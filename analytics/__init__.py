"""Analytics package — statistics, KPIs, outliers, correlations."""

from analytics.stats_engine import (
    CorrelationResult,
    DescriptiveStats,
    KPIResult,
    OutlierResult,
    compute_all_descriptive_stats,
    compute_correlation,
    compute_descriptive_stats,
    compute_kpis,
    detect_all_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
)

__all__ = [
    "CorrelationResult",
    "DescriptiveStats",
    "KPIResult",
    "OutlierResult",
    "compute_all_descriptive_stats",
    "compute_correlation",
    "compute_descriptive_stats",
    "compute_kpis",
    "detect_all_outliers",
    "detect_outliers_iqr",
    "detect_outliers_zscore",
]
