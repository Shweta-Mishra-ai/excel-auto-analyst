"""
tests/test_cleaner.py
Unit tests for core/cleaner.py
The cleaner is the most business-critical module — most thorough tests here.
"""

from __future__ import annotations

import pandas as pd
import pytest

from core.cleaner import (
    CleanResult,
    _impute_categorical,
    _impute_numeric,
    clean_dataframe,
)
from core.validator import profile_dataframe

# ─── _impute_numeric ──────────────────────────────────────────────


class TestImputeNumeric:
    def test_median_strategy(self):
        s = pd.Series([1.0, 2.0, None, 4.0, 5.0], name="x")
        result, label = _impute_numeric(s, "median")
        assert result.isna().sum() == 0
        assert "median" in label

    def test_mean_strategy(self):
        s = pd.Series([1.0, 2.0, None, 4.0, 5.0], name="x")
        result, label = _impute_numeric(s, "mean")
        assert result.isna().sum() == 0
        assert "mean" in label

    def test_zero_strategy_explicit(self):
        s = pd.Series([1.0, None, 3.0], name="x")
        result, label = _impute_numeric(s, "zero")
        assert result.iloc[1] == 0.0
        assert "zero" in label

    def test_no_nulls_returns_no_action(self):
        s = pd.Series([1.0, 2.0, 3.0], name="x")
        _, label = _impute_numeric(s, "median")
        assert label == "no_action"

    def test_median_is_not_zero_for_positive_data(self):
        """THE KEY TEST: ensure we never silently fill with 0."""
        s = pd.Series([100.0, 200.0, None, 400.0, 500.0], name="revenue")
        result, _ = _impute_numeric(s, "median")
        # Filled value must be the median (300.0), NOT 0
        assert result.iloc[2] == pytest.approx(300.0)
        assert result.iloc[2] != 0.0

    def test_ffill_strategy(self):
        s = pd.Series([1.0, None, None, 4.0], name="x")
        result, label = _impute_numeric(s, "ffill")
        assert result.isna().sum() == 0
        assert "forward_fill" in label


# ─── _impute_categorical ──────────────────────────────────────────


class TestImputeCategorical:
    def test_mode_strategy(self):
        s = pd.Series(["A", "A", "B", None, "A"], name="cat")
        result, label = _impute_categorical(s, "mode")
        assert result.isna().sum() == 0
        assert result.iloc[3] == "A"  # mode = "A"
        assert "mode" in label

    def test_unknown_strategy(self):
        s = pd.Series(["X", None, "Y"], name="cat")
        result, _ = _impute_categorical(s, "unknown")
        assert result.iloc[1] == "Unknown"

    def test_no_nulls_returns_no_action(self):
        s = pd.Series(["A", "B", "C"], name="cat")
        _, label = _impute_categorical(s, "mode")
        assert label == "no_action"


# ─── clean_dataframe ──────────────────────────────────────────────


class TestCleanDataframe:
    def test_returns_clean_result(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        result = clean_dataframe(dirty_df, profile)
        assert isinstance(result, CleanResult)

    def test_duplicates_removed(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        before_dups = dirty_df.duplicated().sum()
        result = clean_dataframe(dirty_df, profile)
        assert result.duplicates_removed == before_dups
        assert result.df.duplicated().sum() == 0

    def test_no_missing_values_after_cleaning(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        result = clean_dataframe(dirty_df, profile, numeric_strategy="median")
        # After cleaning, numeric nulls should be gone
        for col in profile.numeric_columns:
            if col in result.df.columns:
                assert result.df[col].isna().sum() == 0

    def test_audit_trail_not_empty(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        result = clean_dataframe(dirty_df, profile)
        assert len(result.audit_trail) > 0

    def test_audit_trail_records_imputation(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        result = clean_dataframe(dirty_df, profile)
        ops = [step.operation for step in result.audit_trail]
        assert "impute_numeric" in ops or "impute_categorical" in ops

    def test_clean_df_warns_high_missing_column(self, all_null_col_df):
        profile = profile_dataframe(all_null_col_df)
        result = clean_dataframe(all_null_col_df, profile)
        assert any("all_null" in w for w in result.warnings)

    def test_clean_df_does_not_modify_original(self, dirty_df):
        original_shape = dirty_df.shape
        original_nulls = dirty_df.isna().sum().sum()
        profile = profile_dataframe(dirty_df)
        clean_dataframe(dirty_df, profile)
        # Original must be untouched
        assert dirty_df.shape == original_shape
        assert dirty_df.isna().sum().sum() == original_nulls

    def test_already_clean_data(self, clean_df):
        profile = profile_dataframe(clean_df)
        result = clean_dataframe(clean_df, profile)
        # Should succeed without errors
        assert isinstance(result, CleanResult)

    def test_summary_is_string(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        result = clean_dataframe(dirty_df, profile)
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0

    def test_drop_constant_columns(self):
        df = pd.DataFrame(
            {
                "sales": [1.0, 2.0, 3.0],
                "constant": ["X", "X", "X"],
                "region": ["A", "B", "C"],
            }
        )
        profile = profile_dataframe(df)
        result = clean_dataframe(df, profile, drop_constant_columns=True)
        assert "constant" not in result.df.columns
        assert "constant" in result.columns_dropped

    def test_numeric_strategy_override(self, dirty_df):
        profile = profile_dataframe(dirty_df)
        result = clean_dataframe(dirty_df, profile, numeric_strategy="mean")
        for col in result.columns_imputed:
            if col in profile.numeric_columns:
                assert "mean" in result.columns_imputed[col]
