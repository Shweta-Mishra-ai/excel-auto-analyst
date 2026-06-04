"""tests/test_validator.py — Fixed for pandas 2.x + Python 3.9+"""

from __future__ import annotations

import pandas as pd

from core.validator import (
    DataProfile,
    SemanticType,
    _infer_semantic_type,
    _looks_like_datetime,
    profile_dataframe,
)


class TestLooksLikeDatetime:
    def test_date_strings_detected(self):
        s = pd.Series(["2023-01-01", "2023-02-15", "2023-03-30"])
        assert bool(_looks_like_datetime(s)) is True  # force Python bool compare

    def test_random_strings_not_datetime(self):
        s = pd.Series(["apple", "banana", "cherry"])
        assert bool(_looks_like_datetime(s)) is False

    def test_empty_series_returns_false(self):
        s = pd.Series([], dtype="object")
        assert _looks_like_datetime(s) is False

    def test_returns_python_bool(self):
        """Ensure never returns numpy bool — causes 'is True' failures."""
        s = pd.Series(["2023-01-01", "2023-02-15"])
        result = _looks_like_datetime(s)
        assert type(result) is bool  # strict Python bool


class TestInferSemanticType:
    def test_float_continuous(self):
        s = pd.Series([1.1, 2.5, 3.8, 4.2, 5.9] * 20, name="x")
        assert _infer_semantic_type(s, "float64") == SemanticType.NUMERIC_CONTINUOUS

    def test_low_cardinality_int_is_discrete(self):
        s = pd.Series([1, 2, 3, 1, 2, 3] * 10, name="x")
        assert _infer_semantic_type(s, "int64") == SemanticType.NUMERIC_DISCRETE

    def test_boolean_detection(self):
        s = pd.Series([True, False, True, False], name="flag")
        assert _infer_semantic_type(s, "bool") == SemanticType.BOOLEAN

    def test_high_cardinality_object_is_id(self):
        s = pd.Series([f"ID-{i}" for i in range(200)], name="id")
        assert _infer_semantic_type(s, "object") == SemanticType.ID_COLUMN

    def test_low_cardinality_object_is_categorical(self):
        s = pd.Series(["North", "South", "East", "West"] * 25, name="region")
        assert _infer_semantic_type(s, "object") == SemanticType.CATEGORICAL

    def test_datetime_dtype_detected(self):
        s = pd.Series(pd.date_range("2023-01-01", periods=10), name="date")
        assert _infer_semantic_type(s, "datetime64[ns]") == SemanticType.DATE_TIME


class TestProfileDataframe:
    def test_returns_data_profile(self, clean_df):
        assert isinstance(profile_dataframe(clean_df), DataProfile)

    def test_row_count_correct(self, clean_df):
        assert profile_dataframe(clean_df).total_rows == 100

    def test_column_count_correct(self, clean_df):
        assert profile_dataframe(clean_df).total_columns == 6

    def test_numeric_columns_detected(self, clean_df):
        p = profile_dataframe(clean_df)
        assert "sales" in p.numeric_columns
        assert "units" in p.numeric_columns

    def test_categorical_columns_detected(self, clean_df):
        p = profile_dataframe(clean_df)
        assert "region" in p.categorical_columns

    def test_missing_values_counted(self, dirty_df):
        assert profile_dataframe(dirty_df).total_missing > 0

    def test_duplicate_rows_counted(self, dirty_df):
        assert profile_dataframe(dirty_df).duplicate_row_count >= 5

    def test_quality_score_in_range(self, clean_df):
        qs = profile_dataframe(clean_df).quality_score
        assert 0 <= qs <= 100

    def test_clean_data_high_quality_score(self, clean_df):
        assert profile_dataframe(clean_df).quality_score >= 60

    def test_has_numeric_property(self, clean_df):
        assert profile_dataframe(clean_df).has_numeric is True

    def test_has_categorical_property(self, clean_df):
        assert profile_dataframe(clean_df).has_categorical is True

    def test_column_profile_has_stats(self, clean_df):
        cp = profile_dataframe(clean_df).columns["sales"]
        assert cp.mean is not None
        assert cp.median is not None

    def test_high_missing_column_flagged(self, all_null_col_df):
        assert "all_null" in profile_dataframe(all_null_col_df).high_missing_columns

    def test_memory_mb_positive(self, clean_df):
        assert profile_dataframe(clean_df).memory_mb > 0
