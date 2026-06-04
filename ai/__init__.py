"""AI integration package — safe execution, prompt building."""

from ai.prompt_builder import build_chat_system_prompt, build_insight_prompt
from ai.safe_executor import ExecResult, execute_safe

__all__ = [
    "ExecResult",
    "build_chat_system_prompt",
    "build_insight_prompt",
    "execute_safe",
]
