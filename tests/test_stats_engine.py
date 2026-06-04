"""tests/test_stats_engine.py — Fixed correlation single-col test"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analytics.stats_engine import (
    compute_all_descriptive_stats,
    compute_correlation,
    compute_descriptive_stats,
    compute_kpis,
    detect_all_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
)
from core.validator import profile_dataframe


class TestDescriptiveStats:
    def test_basic_stats_correct(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], name="x")
        r = compute_descriptive_stats(s)
        assert r.mean == pytest.approx(3.0)
        assert r.median == pytest.approx(3.0)
        assert r.min_val == pytest.approx(1.0)
        assert r.max_val == pytest.approx(5.0)

    def test_iqr_correct(self):
        s = pd.Series(range(1, 101), dtype=float, name="x")
        r = compute_descriptive_stats(s)
        assert r.iqr == pytest.approx(49.5, rel=0.1)

    def test_skewness_right_skewed(self):
        np.random.seed(0)
        s = pd.Series(np.random.exponential(1, 500), name="x")
        assert compute_descriptive_stats(s).skewness > 0.5

    def test_too_few_values_raises(self):
        with pytest.raises(ValueError, match="too few"):
            compute_descriptive_stats(pd.Series([1.0, 2.0], name="x"))

    def test_percentiles_ordered(self, clean_df):
        r = compute_descriptive_stats(clean_df["sales"])
        assert r.p5 <= r.p25 <= r.median <= r.p75 <= r.p95

    def test_all_columns_returns_dict(self, clean_df):
        profile = profile_dataframe(clean_df)
        results = compute_all_descriptive_stats(clean_df, profile)
        assert "sales" in results
        assert "region" not in results  # categorical excluded

    def test_is_normal_is_python_bool(self, clean_df):
        r = compute_descriptive_stats(clean_df["sales"])
        assert type(r.is_normal) is bool


class TestOutlierDetection:
    def test_iqr_detects_obvious_outlier(self):
        s = pd.Series([1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 1000.0], name="x")
        r = detect_outliers_iqr(s)
        assert r.outlier_count >= 1

    def test_iqr_no_outliers_uniform(self):
        s = pd.Series(range(1, 51), dtype=float, name="x")
        assert detect_outliers_iqr(s).outlier_pct < 5.0

    def test_zscore_detects_outlier(self):
        np.random.seed(0)
        s = pd.Series([*np.random.normal(0, 1, 200).tolist(), 50.0], name="x")
        assert detect_outliers_zscore(s).outlier_count >= 1

    def test_iqr_bounds_set(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], name="x")
        r = detect_outliers_iqr(s)
        assert r.lower_bound is not None
        assert r.upper_bound is not None
        assert r.lower_bound < r.upper_bound

    def test_all_outliers_catches_injected(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        results = detect_all_outliers(dirty_df, profile)
        assert "revenue" in results
        assert results["revenue"].outlier_count >= 1


class TestCorrelation:
    def test_perfect_correlation(self):
        df = pd.DataFrame(
            {
                "x": [1.0, 2.0, 3.0, 4.0, 5.0] * 5,
                "y": [2.0, 4.0, 6.0, 8.0, 10.0] * 5,
            }
        )
        profile = profile_dataframe(df)
        result = compute_correlation(df, profile)
        assert result is not None
        assert abs(result.matrix.loc["x", "y"]) == pytest.approx(1.0, abs=1e-6)

    def test_single_numeric_column_returns_none(self):
        """FIXED: was checking wrong threshold (< 1 instead of < 2)."""
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0] * 10, "label": ["a", "b", "c"] * 10})
        profile = profile_dataframe(df)
        assert len(profile.numeric_columns) == 1
        result = compute_correlation(df, profile)
        assert result is None  # must be None with only 1 numeric col

    def test_two_columns_returns_result(self, clean_df):
        profile = profile_dataframe(clean_df)
        result = compute_correlation(clean_df, profile, min_corr=0.01)
        assert result is not None
        assert isinstance(result.strong_pairs, list)

    def test_spearman_method(self, clean_df):
        profile = profile_dataframe(clean_df)
        result = compute_correlation(clean_df, profile, method="spearman")
        assert result is not None
        assert result.method == "spearman"


class TestKPIs:
    def test_basic_kpis(self, clean_df):
        r = compute_kpis(clean_df, "sales")
        assert r.total == pytest.approx(clean_df["sales"].sum(), rel=1e-4)
        assert r.mean == pytest.approx(clean_df["sales"].mean(), rel=1e-4)

    def test_range_is_max_minus_min(self, clean_df):
        r = compute_kpis(clean_df, "sales")
        expected = clean_df["sales"].max() - clean_df["sales"].min()
        assert r.range_val == pytest.approx(expected, rel=1e-4)

    def test_empty_column_raises(self):
        df = pd.DataFrame({"sales": [None, None, None]})
        with pytest.raises(ValueError, match="No numeric data"):
            compute_kpis(df, "sales")

    def test_mom_without_dates_is_none(self, clean_df):
        assert compute_kpis(clean_df, "sales").mom_change_pct is None

    def test_mom_with_dates(self, clean_df):
        r = compute_kpis(clean_df, "sales", date_col="date")
        assert isinstance(r.mom_change_pct, float | type(None))
