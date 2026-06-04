"""
ai/safe_executor.py
Sandboxed code execution for AI-generated Python.
Fixes:
  - Windows: signal.SIGALRM not available → platform-safe timeout
  - plotly lazy import
  - RestrictedPython optional
"""

from __future__ import annotations

import ast
import logging
import platform
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO

import pandas as pd

from config.settings import CONFIG

logger = logging.getLogger(__name__)

try:
    from RestrictedPython import compile_restricted
    from RestrictedPython.Guards import guarded_getattr, guarded_getiter, safe_builtins

    _HAS_RESTRICTED = True
except ImportError:
    logger.warning("RestrictedPython not installed — using AST-only sandbox.")
    _HAS_RESTRICTED = False

MAX_OUTPUT_CHARS = 4_000
_IS_WINDOWS = platform.system() == "Windows"


@dataclass
class ExecResult:
    success: bool
    output: str
    figure: object | None
    error: str | None
    code_executed: str


# ── AST Security ─────────────────────────────────────────────────

_BLOCKED_NAMES = frozenset(
    {
        "__import__",
        "__builtins__",
        "__loader__",
        "__spec__",
        "exec",
        "eval",
        "compile",
        "open",
        "input",
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "importlib",
        "ctypes",
        "pickle",
        "marshal",
    }
)


def _validate_ast(code: str) -> str | None:
    """Return error string if validation fails, else None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"

    allowed_mods = set(CONFIG.ai.allowed_modules) | {"pandas", "plotly", "numpy"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_mod = alias.name.split(".")[0]
                if base_mod not in allowed_mods:
                    return f"Import of '{base_mod}' is not permitted. All allowed libraries are pre-imported."
        elif isinstance(node, ast.ImportFrom):
            base_mod = node.module.split(".")[0] if node.module else ""
            if base_mod not in allowed_mods:
                return f"Import from '{base_mod}' is not permitted. All allowed libraries are pre-imported."

        if isinstance(node, ast.Name) and node.id in _BLOCKED_NAMES:
            return f"Use of '{node.id}' is not permitted."

        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return f"Dunder attribute '{node.attr}' is not permitted."

    return None


# ── Safe scope ────────────────────────────────────────────────────


def _build_safe_scope(df: pd.DataFrame) -> dict:
    import collections
    import datetime
    import itertools
    import json
    import math
    import re
    import statistics
    import time
    import warnings

    import numpy as np

    try:
        import scipy
    except ImportError:
        scipy = None  # type: ignore[assignment]

    try:
        import plotly.express as px
    except ImportError:
        px = None  # type: ignore[assignment]

    scope: dict = {
        "df": df,
        "pd": pd,
        "px": px,
        "np": np,
        "math": math,
        "statistics": statistics,
        "datetime": datetime,
        "re": re,
        "scipy": scipy,
        "warnings": warnings,
        "collections": collections,
        "itertools": itertools,
        "json": json,
        "time": time,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "print": print,
        "round": round,
        "sorted": sorted,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "list": list,
        "dict": dict,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "isinstance": isinstance,
        "type": type,
    }

    if _HAS_RESTRICTED:
        scope.update(
            {
                "_getattr_": guarded_getattr,
                "_getiter_": guarded_getiter,
                "__builtins__": safe_builtins,
            }
        )

    return scope


# ── Timeout (platform-safe) ───────────────────────────────────────


def _exec_with_timeout(byte_code: object, scope: dict, timeout: int) -> None:
    """
    Execute compiled code with timeout.
    Windows: no SIGALRM — use threading timeout instead.
    Linux/Mac: use signal.SIGALRM (more reliable in main thread),
               fall back to threading if not running in the main thread.
    """
    use_thread_fallback = _IS_WINDOWS

    if not _IS_WINDOWS:
        import signal

        def _handler(signum: int, frame: object) -> None:
            raise TimeoutError(f"Code timed out after {timeout}s.")

        try:
            old = signal.signal(signal.SIGALRM, _handler)
            has_signal = True
        except ValueError:
            has_signal = False
            use_thread_fallback = True

        if has_signal:
            signal.alarm(timeout)
            try:
                exec(byte_code, scope)  # noqa: S102 # nosec B102
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)

    if use_thread_fallback:
        import threading

        result = {"error": None}

        def run() -> None:
            try:
                exec(byte_code, scope)  # noqa: S102 # nosec B102
            except Exception as e:
                result["error"] = e

        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(timeout=timeout)
        if t.is_alive():
            raise TimeoutError(f"Code timed out after {timeout}s.")
        if result["error"]:
            raise result["error"]


# ── Public API ────────────────────────────────────────────────────


def execute_safe(code: str, df: pd.DataFrame) -> ExecResult:
    """Safely execute AI-generated Python. Never raises — errors in result.error."""
    # Strip markdown fences
    cleaned = code.strip()
    if "```python" in cleaned:
        cleaned = cleaned.split("```python")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    # AST validation (this also blocks forbidden imports)
    ast_error = _validate_ast(cleaned)
    if ast_error:
        return ExecResult(
            success=False,
            output="",
            figure=None,
            error=f"Security check failed: {ast_error}",
            code_executed=cleaned,
        )

    # Use AST to strip imports securely
    class ImportStripper(ast.NodeTransformer):
        def visit_Import(self, node):  # noqa: N802
            return None

        def visit_ImportFrom(self, node):  # noqa: N802
            return None

    try:
        tree = ast.parse(cleaned)
        tree = ImportStripper().visit(tree)
        ast.fix_missing_locations(tree)
        cleaned = ast.unparse(tree)
    except Exception:  # noqa: S110
        pass

    scope = _build_safe_scope(df)
    buffer = StringIO()

    # Compile
    if _HAS_RESTRICTED:
        try:
            byte_code = compile_restricted(cleaned, filename="<ai_code>", mode="exec")
        except SyntaxError as e:
            return ExecResult(
                success=False,
                output="",
                figure=None,
                error=f"Compilation error: {e}",
                code_executed=cleaned,
            )
    else:
        try:
            byte_code = compile(cleaned, "<ai_code>", "exec")
        except SyntaxError as e:
            return ExecResult(
                success=False,
                output="",
                figure=None,
                error=f"Compilation error: {e}",
                code_executed=cleaned,
            )

    # Execute with timeout
    try:
        with redirect_stdout(buffer):
            _exec_with_timeout(byte_code, scope, CONFIG.ai.exec_timeout_seconds)
    except TimeoutError as e:
        return ExecResult(
            success=False, output="", figure=None, error=str(e), code_executed=cleaned
        )
    except Exception as e:
        return ExecResult(
            success=False,
            output="",
            figure=None,
            error=f"Runtime error: {type(e).__name__}: {e}",
            code_executed=cleaned,
        )

    output = buffer.getvalue()
    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + "\n… (output truncated)"
    if output.strip().startswith("{") and len(output) > 200:
        output = ""

    return ExecResult(
        success=True,
        output=output,
        figure=scope.get("fig"),
        error=None,
        code_executed=cleaned,
    )
