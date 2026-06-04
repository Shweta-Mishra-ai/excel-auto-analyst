"""
analytics/stats_engine.py
Senior-level statistical analysis engine.
Fixes:
  - correlation: correct check for < 2 numeric columns (was using wrong threshold)
  - Windows: SIGALRM fallback handled in safe_executor
  - All functions pure — no side effects
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from config.settings import CONFIG
from core.validator import DataProfile

logger = logging.getLogger(__name__)


@dataclass
class DescriptiveStats:
    column: str
    count: int
    mean: float
    median: float
    mode: float | None
    min_val: float
    max_val: float
    std: float
    variance: float
    skewness: float
    kurtosis: float
    p5: float
    p25: float
    p75: float
    p95: float
    iqr: float
    cv: float
    is_normal: bool
    shapiro_p: float


@dataclass
class OutlierResult:
    column: str
    method: str
    outlier_count: int
    outlier_pct: float
    lower_bound: float | None
    upper_bound: float | None
    outlier_indices: list[int]


@dataclass
class CorrelationResult:
    method: str
    matrix: pd.DataFrame
    strong_pairs: list[tuple[str, str, float]]


@dataclass
class KPIResult:
    column: str
    total: float
    mean: float
    median: float
    std: float
    max_val: float
    min_val: float
    range_val: float
    mom_change_pct: float | None
    cv_pct: float


# ── Descriptive Stats ─────────────────────────────────────────────


def compute_descriptive_stats(series: pd.Series) -> DescriptiveStats:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) < 3:
        raise ValueError(f"Column '{series.name}' has too few non-null values.")

    sample = clean if len(clean) <= 5000 else clean.sample(5000, random_state=42)
    _, shapiro_p = scipy_stats.shapiro(sample)

    mode_result = scipy_stats.mode(clean, keepdims=True)
    mode_val = float(mode_result.mode[0]) if len(mode_result.mode) > 0 else None

    std = float(clean.std())
    mean = float(clean.mean())
    cv = abs(std / mean) if mean != 0 else float("inf")

    return DescriptiveStats(
        column=str(series.name),
        count=len(clean),
        mean=round(mean, 4),
        median=round(float(clean.median()), 4),
        mode=round(mode_val, 4) if mode_val is not None else None,
        min_val=round(float(clean.min()), 4),
        max_val=round(float(clean.max()), 4),
        std=round(std, 4),
        variance=round(float(clean.var()), 4),
        skewness=round(float(clean.skew()), 4),
        kurtosis=round(float(clean.kurtosis()), 4),
        p5=round(float(clean.quantile(0.05)), 4),
        p25=round(float(clean.quantile(0.25)), 4),
        p75=round(float(clean.quantile(0.75)), 4),
        p95=round(float(clean.quantile(0.95)), 4),
        iqr=round(float(clean.quantile(0.75) - clean.quantile(0.25)), 4),
        cv=round(cv, 4),
        is_normal=bool(shapiro_p > CONFIG.stats.significance_level),
        shapiro_p=round(float(shapiro_p), 6),
    )


def compute_all_descriptive_stats(
    df: pd.DataFrame, profile: DataProfile
) -> dict[str, DescriptiveStats]:
    results: dict[str, DescriptiveStats] = {}
    for col in profile.numeric_columns:
        if col not in df.columns:
            continue
        try:
            results[col] = compute_descriptive_stats(df[col])
        except ValueError as e:
            logger.warning("Skipping stats for '%s': %s", col, e)
    return results


# ── Outlier Detection ─────────────────────────────────────────────


def detect_outliers_iqr(
    series: pd.Series,
    multiplier: float | None = None,
) -> OutlierResult:
    k = multiplier or CONFIG.cleaning.iqr_multiplier
    clean = pd.to_numeric(series, errors="coerce").dropna()
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    lower = float(q1 - k * iqr)
    upper = float(q3 + k * iqr)
    mask = (clean < lower) | (clean > upper)
    return OutlierResult(
        column=str(series.name),
        method="IQR",
        outlier_count=int(mask.sum()),
        outlier_pct=round(float(mask.mean() * 100), 2),
        lower_bound=round(lower, 4),
        upper_bound=round(upper, 4),
        outlier_indices=list(clean[mask].index),
    )


def detect_outliers_zscore(
    series: pd.Series,
    threshold: float | None = None,
) -> OutlierResult:
    z_thresh = threshold or CONFIG.cleaning.zscore_threshold
    clean = pd.to_numeric(series, errors="coerce").dropna()
    z_scores = np.abs(scipy_stats.zscore(clean))
    mask = z_scores > z_thresh
    return OutlierResult(
        column=str(series.name),
        method="Z-Score",
        outlier_count=int(mask.sum()),
        outlier_pct=round(float(mask.mean() * 100), 2),
        lower_bound=None,
        upper_bound=None,
        outlier_indices=list(clean[mask].index),
    )


def detect_all_outliers(
    df: pd.DataFrame, profile: DataProfile
) -> dict[str, OutlierResult]:
    results: dict[str, OutlierResult] = {}
    method = CONFIG.cleaning.outlier_method
    for col in profile.numeric_columns:
        if col not in df.columns:
            continue
        try:
            if method == "zscore":
                results[col] = detect_outliers_zscore(df[col])
            else:
                results[col] = detect_outliers_iqr(df[col])
        except Exception as e:
            logger.warning("Outlier detection failed for '%s': %s", col, e)
    return results


# ── Correlation ───────────────────────────────────────────────────


def compute_correlation(
    df: pd.DataFrame,
    profile: DataProfile,
    method: str = "pearson",
    min_corr: float = 0.5,
) -> CorrelationResult | None:
    """
    Returns None if fewer than 2 numeric columns.
    Fix: was checking < correlation_min_rows // 10 (= 1),
         now correctly checks < 2.
    """
    num_cols = [c for c in profile.numeric_columns if c in df.columns]

    # FIXED: must have at least 2 numeric columns for correlation
    if len(num_cols) < 2:
        return None

    if len(df) < CONFIG.stats.correlation_min_rows:
        logger.warning("Too few rows for reliable correlation.")

    matrix = df[num_cols].corr(method=method)

    strong_pairs: list[tuple[str, str, float]] = []
    for i, col_a in enumerate(matrix.columns):
        for col_b in matrix.columns[i + 1 :]:
            val = matrix.loc[col_a, col_b]
            if abs(val) >= min_corr:
                strong_pairs.append((col_a, col_b, round(float(val), 4)))

    strong_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    return CorrelationResult(
        method=method,
        matrix=matrix,
        strong_pairs=strong_pairs,
    )


# ── KPIs ──────────────────────────────────────────────────────────


def compute_kpis(
    df: pd.DataFrame,
    metric_col: str,
    date_col: str | None = None,
) -> KPIResult:
    series = pd.to_numeric(df[metric_col], errors="coerce").dropna()
    if len(series) == 0:
        raise ValueError(f"No numeric data in column '{metric_col}'")

    mean = float(series.mean())
    std = float(series.std())
    cv_pct = round(abs(std / mean) * 100, 2) if mean != 0 else 0.0

    mom_change = None
    if date_col and date_col in df.columns:
        try:
            df_temp = df[[date_col, metric_col]].copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
            df_temp = df_temp.dropna()
            df_temp["month"] = df_temp[date_col].dt.to_period("M")
            monthly = df_temp.groupby("month")[metric_col].sum().sort_index()
            if len(monthly) >= 2:
                prev = float(monthly.iloc[-2])
                curr = float(monthly.iloc[-1])
                mom_change = (
                    round((curr - prev) / abs(prev) * 100, 2) if prev != 0 else None
                )
        except Exception as e:
            logger.warning("MoM calculation failed: %s", e)

    return KPIResult(
        column=metric_col,
        total=round(float(series.sum()), 4),
        mean=round(mean, 4),
        median=round(float(series.median()), 4),
        std=round(std, 4),
        max_val=round(float(series.max()), 4),
        min_val=round(float(series.min()), 4),
        range_val=round(float(series.max() - series.min()), 4),
        mom_change_pct=mom_change,
        cv_pct=cv_pct,
    )
