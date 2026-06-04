"""
core/cleaner.py
Professional data cleaning with:
- Strategy-based imputation (never blindly fill with 0)
- Full audit trail of every transformation
- Reversible operations
- Returns both cleaned df and what changed
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from config.settings import CONFIG
from core.validator import DataProfile

logger = logging.getLogger(__name__)


@dataclass
class TransformStep:
    """One logged step in the cleaning audit trail."""

    operation: str
    column: str | None
    before: str
    after: str
    rows_affected: int


@dataclass
class CleanResult:
    """Everything the cleaner produces."""

    df: pd.DataFrame
    audit_trail: list[TransformStep]
    duplicates_removed: int
    columns_imputed: dict[str, str]  # col → strategy used
    columns_dropped: list[str]  # constant/ID columns optionally dropped
    warnings: list[str]  # human-readable warnings

    @property
    def summary(self) -> str:
        lines = [
            f"Removed {self.duplicates_removed} duplicate rows.",
            f"Imputed {len(self.columns_imputed)} columns.",
        ]
        if self.warnings:
            lines += [f"⚠ {w}" for w in self.warnings]
        return "\n".join(lines)


# ─── Imputation strategies ────────────────────────────────────────


def _impute_numeric(
    series: pd.Series,
    strategy: str,
) -> tuple[pd.Series, str]:
    """
    Impute a numeric series. Never uses 0 as default.

    Strategies
    ----------
    median   → robust to outliers (default)
    mean     → only for symmetric distributions
    ffill    → forward-fill (good for time-ordered data)
    drop     → drop rows with nulls (use with caution)
    """
    null_count = series.isna().sum()
    if null_count == 0:
        return series, "no_action"

    if strategy == "median":
        fill_val = series.median()
        return series.fillna(fill_val), f"median={fill_val:.4g}"
    if strategy == "mean":
        fill_val = series.mean()
        return series.fillna(fill_val), f"mean={fill_val:.4g}"
    if strategy == "ffill":
        return series.ffill().bfill(), "forward_fill"
    if strategy == "zero":
        # Allowed explicitly, but NEVER the silent default
        return series.fillna(0), "zero (explicit)"
    if strategy == "drop":
        return series, "drop_rows"  # handled at df level
    # Fallback safe default
    fill_val = series.median()
    return series.fillna(fill_val), f"median={fill_val:.4g} (fallback)"


def _impute_categorical(
    series: pd.Series,
    strategy: str,
) -> tuple[pd.Series, str]:
    """Impute a categorical/object series."""
    null_count = series.isna().sum()
    if null_count == 0:
        return series, "no_action"

    if strategy == "mode":
        mode_vals = series.mode()
        if len(mode_vals) == 0:
            return series.fillna("Unknown"), "unknown (no mode)"
        fill_val = mode_vals.iloc[0]
        return series.fillna(fill_val), f"mode='{fill_val}'"
    if strategy == "unknown":
        return series.fillna("Unknown"), "unknown"
    if strategy == "drop":
        return series, "drop_rows"
    # Fallback
    return series.fillna("Unknown"), "unknown (fallback)"


# ─── Public API ──────────────────────────────────────────────────


def clean_dataframe(
    df: pd.DataFrame,
    profile: DataProfile,
    numeric_strategy: str | None = None,
    categorical_strategy: str | None = None,
    drop_constant_columns: bool = False,
    drop_id_columns: bool = False,
) -> CleanResult:
    """
    Clean a DataFrame using the profile as guidance.

    Parameters
    ----------
    df : Raw DataFrame from load_dataframe()
    profile : DataProfile from profile_dataframe()
    numeric_strategy : Override CONFIG default
    categorical_strategy : Override CONFIG default
    drop_constant_columns : Remove columns that have only 1 unique value
    drop_id_columns : Remove detected ID-like columns

    Returns
    -------
    CleanResult with cleaned df and full audit trail
    """
    cfg = CONFIG.cleaning
    num_strat = numeric_strategy or cfg.numeric_strategy
    cat_strat = categorical_strategy or cfg.categorical_strategy

    df_out = df.copy()
    audit: list[TransformStep] = []
    imputed: dict[str, str] = {}
    dropped_cols: list[str] = []
    warnings: list[str] = []

    # ── 1. Duplicate rows ────────────────────────────────────────
    before_rows = len(df_out)
    df_out = df_out.drop_duplicates()
    dups_removed = before_rows - len(df_out)
    if dups_removed > 0:
        audit.append(
            TransformStep(
                operation="drop_duplicates",
                column=None,
                before=f"{before_rows} rows",
                after=f"{len(df_out)} rows",
                rows_affected=dups_removed,
            )
        )
        logger.info("Removed %d duplicate rows", dups_removed)

    # ── 2. Drop constant columns (optional) ─────────────────────
    if drop_constant_columns and profile.constant_columns:
        df_out = df_out.drop(columns=profile.constant_columns, errors="ignore")
        dropped_cols.extend(profile.constant_columns)
        audit.append(
            TransformStep(
                operation="drop_constant_columns",
                column=str(profile.constant_columns),
                before="present",
                after="dropped",
                rows_affected=0,
            )
        )

    # ── 3. Drop ID columns (optional) ───────────────────────────
    if drop_id_columns and profile.id_columns:
        df_out = df_out.drop(columns=profile.id_columns, errors="ignore")
        dropped_cols.extend(profile.id_columns)

    # ── 4. Warn about high-missing columns ──────────────────────
    for col in profile.high_missing_columns:
        if col in df_out.columns:
            pct = profile.columns[col].null_pct
            warnings.append(
                f"Column '{col}' is {pct:.1f}% missing. "
                "Consider dropping it instead of imputing."
            )

    # ── 5. Numeric imputation ────────────────────────────────────
    for col in profile.numeric_columns:
        if col not in df_out.columns:
            continue
        null_before = int(df_out[col].isna().sum())
        if null_before == 0:
            continue

        imputed_series, strategy_used = _impute_numeric(df_out[col], num_strat)

        if num_strat == "drop":
            df_out = df_out.dropna(subset=[col])
            rows_affected = null_before
        else:
            df_out[col] = imputed_series
            rows_affected = null_before

        imputed[col] = strategy_used
        audit.append(
            TransformStep(
                operation="impute_numeric",
                column=col,
                before=f"{null_before} nulls",
                after=f"0 nulls ({strategy_used})",
                rows_affected=rows_affected,
            )
        )

    # ── 6. Categorical imputation ────────────────────────────────
    for col in profile.categorical_columns:
        if col not in df_out.columns:
            continue
        null_before = int(df_out[col].isna().sum())
        if null_before == 0:
            continue

        imputed_series, strategy_used = _impute_categorical(df_out[col], cat_strat)

        if cat_strat == "drop":
            df_out = df_out.dropna(subset=[col])
            rows_affected = null_before
        else:
            df_out[col] = imputed_series
            rows_affected = null_before

        imputed[col] = strategy_used
        audit.append(
            TransformStep(
                operation="impute_categorical",
                column=col,
                before=f"{null_before} nulls",
                after=f"0 nulls ({strategy_used})",
                rows_affected=rows_affected,
            )
        )

    logger.info(
        "Cleaning complete: %d cols imputed, %d dups removed",
        len(imputed),
        dups_removed,
    )

    return CleanResult(
        df=df_out,
        audit_trail=audit,
        duplicates_removed=dups_removed,
        columns_imputed=imputed,
        columns_dropped=dropped_cols,
        warnings=warnings,
    )
