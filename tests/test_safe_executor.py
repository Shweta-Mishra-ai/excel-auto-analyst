"""tests/test_safe_executor.py — Windows-safe, no SIGALRM dependency"""

from __future__ import annotations

import pandas as pd
import pytest

from ai.safe_executor import ExecResult, _validate_ast, execute_safe


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "sales": [100.0, 200.0, 300.0],
            "region": ["North", "South", "East"],
        }
    )


class TestValidateAST:
    def test_safe_code_passes(self):
        assert _validate_ast("result = df['sales'].mean()\nprint(result)") is None

    def test_os_import_blocked(self):
        assert _validate_ast("import os\nos.system('rm -rf /')") is not None

    def test_sys_import_blocked(self):
        assert _validate_ast("import sys\nsys.exit(1)") is not None

    def test_subprocess_blocked(self):
        assert _validate_ast("import subprocess\nsubprocess.run(['ls'])") is not None

    def test_exec_name_blocked(self):
        assert _validate_ast("exec('import os')") is not None

    def test_eval_name_blocked(self):
        assert _validate_ast("eval('1+1')") is not None

    def test_open_blocked(self):
        assert _validate_ast("f = open('/etc/passwd')") is not None

    def test_dunder_attribute_blocked(self):
        assert _validate_ast("x = df.__class__.__bases__") is not None

    def test_any_import_blocked(self):
        """All imports blocked — modules are pre-injected."""
        assert _validate_ast("import pandas as pd") is not None

    def test_syntax_error_caught(self):
        assert _validate_ast("def broken(:\n    pass") is not None


class TestExecuteSafe:
    def test_simple_print_works(self, sample_df):
        r = execute_safe("print(df['sales'].mean())", sample_df)
        assert r.success is True
        assert "200" in r.output

    def test_returns_exec_result(self, sample_df):
        r = execute_safe("print(len(df))", sample_df)
        assert isinstance(r, ExecResult)

    def test_dangerous_import_blocked(self, sample_df):
        r = execute_safe("import os\nprint(os.getcwd())", sample_df)
        assert r.success is False
        assert r.error is not None

    def test_syntax_error_caught(self, sample_df):
        r = execute_safe("def broken(:\n    pass", sample_df)
        assert r.success is False

    def test_runtime_error_caught(self, sample_df):
        r = execute_safe("print(1/0)", sample_df)
        assert r.success is False
        assert r.error is not None

    def test_nonexistent_column_caught(self, sample_df):
        r = execute_safe("print(df['does_not_exist'].mean())", sample_df)
        assert r.success is False

    def test_markdown_fences_stripped(self, sample_df):
        r = execute_safe("```python\nprint(df.shape)\n```", sample_df)
        assert r.success is True
        assert "(3, 2)" in r.output

    def test_code_executed_stored(self, sample_df):
        r = execute_safe("print(len(df))", sample_df)
        assert "print" in r.code_executed

    def test_large_output_truncated(self, sample_df):
        r = execute_safe("print('x' * 10000)", sample_df)
        assert r.success is True
        assert len(r.output) <= 4500

    def test_no_figure_when_none_created(self, sample_df):
        r = execute_safe("print('hello')", sample_df)
        assert r.figure is None
