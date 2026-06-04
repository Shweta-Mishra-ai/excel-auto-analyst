"""
config/settings.py
Central configuration — all constants, limits, and env vars live here.
No magic numbers scattered across the codebase.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent


# ─── Data Limits ─────────────────────────────────────────────────
@dataclass(frozen=True)
class DataLimits:
    max_file_size_mb: int = 50
    max_rows: int = 500_000
    max_columns: int = 500
    preview_rows: int = 5
    sample_rows_for_ai: int = 3


# ─── Cleaning Strategy ───────────────────────────────────────────
@dataclass(frozen=True)
class CleaningConfig:
    # Numeric: "median" | "mean" | "zero" | "drop"
    numeric_strategy: str = "median"
    # Categorical: "mode" | "unknown" | "drop"
    categorical_strategy: str = "mode"
    # Flag columns where missing > this threshold
    high_missing_threshold: float = 0.5
    # Outlier detection: "iqr" | "zscore" | "both"
    outlier_method: str = "iqr"
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0


# ─── AI / LLM ────────────────────────────────────────────────────
@dataclass(frozen=True)
class AIConfig:
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.0
    max_tokens: int = 1024
    # Safe execution limits
    exec_timeout_seconds: int = 10
    exec_memory_limit_mb: int = 256
    # Allowed modules in sandboxed exec
    allowed_modules: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "pandas",
                "numpy",
                "scipy",
                "math",
                "statistics",
                "datetime",
                "re",
            }
        )
    )


# ─── Statistics ──────────────────────────────────────────────────
@dataclass(frozen=True)
class StatsConfig:
    correlation_min_rows: int = 10
    significance_level: float = 0.05
    min_category_count: int = 2
    max_categories_for_chart: int = 30


# ─── Report / PPT ────────────────────────────────────────────────
@dataclass(frozen=True)
class ReportConfig:
    max_charts_per_report: int = 8
    ppt_theme: str = "dark_teal"  # "dark_teal" | "light_blue" | "corporate"
    include_raw_stats: bool = True
    include_ai_narrative: bool = True


# ─── App ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class AppConfig:
    title: str = "Excel Auto-Analyst"
    version: str = "2.0.0"
    page_icon: str = "📊"
    layout: str = "wide"
    data: DataLimits = field(default_factory=DataLimits)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    stats: StatsConfig = field(default_factory=StatsConfig)
    report: ReportConfig = field(default_factory=ReportConfig)


# ─── Environment ─────────────────────────────────────────────────
def get_groq_api_key() -> str | None:
    """Resolve API key: Streamlit secrets → env var → None."""
    # Try Streamlit secrets (production)
    try:
        import streamlit as st

        return st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    # Fallback: environment variable (local dev with .env)
    return os.getenv("GROQ_API_KEY")


# ─── Singleton ───────────────────────────────────────────────────
CONFIG = AppConfig()
