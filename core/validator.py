"""
core/validator.py
Fixes:
- Pandas 3.x: numeric columns stored as 'str' dtype with mixed values
- Auto-convert string columns that contain numbers
- infer_datetime_format removed (pandas 2.0+)
- match/case replaced with if/elif (Python 3.9 compat)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

logger = logging.getLogger(__name__)


class SemanticType(str, Enum):
    NUMERIC_CONTINUOUS = "numeric_continuous"
    NUMERIC_DISCRETE = "numeric_discrete"
    CATEGORICAL = "categorical"
    DATE_TIME = "datetime"
    ID_COLUMN = "id"
    BOOLEAN = "boolean"
    TEXT_FREE = "text_free"
    UNKNOWN = "unknown"


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    semantic_type: SemanticType
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    skewness: float | None = None
    top_values: list[tuple[str, int]] = field(default_factory=list)
    is_high_missing: bool = False
    is_constant: bool = False
    is_id_like: bool = False


@dataclass
class DataProfile:
    total_rows: int
    total_columns: int
    total_missing: int
    total_missing_pct: float
    memory_mb: float
    columns: dict[str, ColumnProfile]
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]
    id_columns: list[str]
    high_missing_columns: list[str]
    constant_columns: list[str]
    duplicate_row_count: int
    quality_score: float

    @property
    def has_numeric(self) -> bool:
        return len(self.numeric_columns) > 0

    @property
    def has_categorical(self) -> bool:
        return len(self.categorical_columns) > 0

    @property
    def has_datetime(self) -> bool:
        return len(self.datetime_columns) > 0


def _looks_like_datetime(sample: pd.Series) -> bool:
    """Return plain Python bool."""
    if len(sample) == 0:
        return False
    try:
        parsed = pd.to_datetime(sample.head(10), format="mixed", errors="coerce")
        return bool(parsed.notna().mean() > 0.7)
    except Exception:
        try:
            parsed = pd.to_datetime(sample.head(10), errors="coerce")
            return bool(parsed.notna().mean() > 0.7)
        except Exception:
            return False


def _is_numeric_string_col(series: pd.Series) -> bool:
    """
    Check if a string/object column actually contains numbers.
    Pandas 3.x sometimes reads numeric CSVs as 'str' dtype.
    """
    try:
        sample = series.dropna().head(50)
        if len(sample) == 0:
            return False
        converted = pd.to_numeric(sample, errors="coerce")
        # If > 80% of values convert to numbers, treat as numeric
        return bool(converted.notna().mean() > 0.8)
    except Exception:
        return False


def _infer_semantic_type(series: pd.Series, dtype: str) -> SemanticType:
    n = len(series)
    n_unique = series.nunique()
    pct_unique = n_unique / n if n > 0 else 0

    # Boolean
    if dtype == "bool":
        return SemanticType.BOOLEAN
    non_null = series.dropna().unique()
    if len(non_null) <= 2 and set(non_null).issubset(  # noqa: SIM102
        {0, 1, True, False, "0", "1", "true", "false", "True", "False"}
    ):
        if len(non_null) <= 2:
            return SemanticType.BOOLEAN

    # Datetime dtype
    if "datetime" in dtype:
        return SemanticType.DATE_TIME

    # Numeric dtypes
    if "int" in dtype or "float" in dtype:
        if pct_unique > 0.95 and n_unique > 100:
            return SemanticType.ID_COLUMN
        if "int" in dtype and n_unique <= 20:
            return SemanticType.NUMERIC_DISCRETE
        return SemanticType.NUMERIC_CONTINUOUS

    # Object / str dtype (pandas 3.x uses "str" for string columns)
    if dtype in ("object", "str") or "string" in dtype:
        sample = series.dropna().head(50)

        # KEY FIX: check if string col contains numbers
        if _is_numeric_string_col(series):
            if n_unique <= 20:
                return SemanticType.NUMERIC_DISCRETE
            return SemanticType.NUMERIC_CONTINUOUS

        if _looks_like_datetime(sample):
            return SemanticType.DATE_TIME
        if pct_unique > 0.95 and n_unique > 100:
            return SemanticType.ID_COLUMN
        avg_len = float(sample.astype(str).str.len().mean()) if len(sample) > 0 else 0
        if avg_len > 80:
            return SemanticType.TEXT_FREE
        return SemanticType.CATEGORICAL

    return SemanticType.UNKNOWN


def _profile_column(series: pd.Series) -> ColumnProfile:
    n = len(series)
    dtype = str(series.dtype)
    null_count = int(series.isna().sum())
    null_pct = round(null_count / n * 100, 2) if n > 0 else 0.0
    unique_count = int(series.nunique())
    unique_pct = round(unique_count / n * 100, 2) if n > 0 else 0.0
    sem_type = _infer_semantic_type(series, dtype)

    col = ColumnProfile(
        name=str(series.name),
        dtype=dtype,
        semantic_type=sem_type,
        null_count=null_count,
        null_pct=null_pct,
        unique_count=unique_count,
        unique_pct=unique_pct,
        is_high_missing=null_pct > 50,
        is_constant=unique_count <= 1,
        is_id_like=sem_type == SemanticType.ID_COLUMN,
    )

    if sem_type in (SemanticType.NUMERIC_CONTINUOUS, SemanticType.NUMERIC_DISCRETE):
        num = pd.to_numeric(series, errors="coerce").dropna()
        if len(num) > 0:
            col.mean = round(float(num.mean()), 4)
            col.median = round(float(num.median()), 4)
            col.std = round(float(num.std()), 4)
            col.min_val = round(float(num.min()), 4)
            col.max_val = round(float(num.max()), 4)
            col.skewness = round(float(num.skew()), 4)

    if sem_type == SemanticType.CATEGORICAL:
        top = series.value_counts().head(5)
        col.top_values = [(str(k), int(v)) for k, v in top.items()]

    return col


def _compute_quality_score(profile: DataProfile) -> float:
    completeness = max(0, 40 * (1 - profile.total_missing_pct / 100))
    uniqueness = 20 * (1 - profile.duplicate_row_count / max(profile.total_rows, 1))
    consistency = 20 * (
        1 - len(profile.constant_columns) / max(profile.total_columns, 1)
    )
    structure = 20 if (profile.has_numeric and profile.has_categorical) else 10
    return round(min(100, completeness + uniqueness + consistency + structure), 1)


def profile_dataframe(df: pd.DataFrame) -> DataProfile:
    """Full profile. Auto-converts numeric string columns."""
    logger.info("Profiling: %d rows x %d cols", len(df), len(df.columns))

    # Auto-convert string columns that contain numbers
    df = df.copy()
    for col in df.columns:
        if str(df[col].dtype) in ("object", "str") or "string" in str(df[col].dtype):
            if _is_numeric_string_col(df[col]):
                df[col] = pd.to_numeric(df[col], errors="coerce")
                logger.info("Auto-converted '%s' to numeric", col)

    col_profiles: dict[str, ColumnProfile] = {}
    numeric_cols: list[str] = []
    cat_cols: list[str] = []
    dt_cols: list[str] = []
    id_cols: list[str] = []
    high_missing: list[str] = []
    constant: list[str] = []

    for col_name in df.columns:
        cp = _profile_column(df[col_name])
        col_profiles[col_name] = cp

        if cp.semantic_type in (
            SemanticType.NUMERIC_CONTINUOUS,
            SemanticType.NUMERIC_DISCRETE,
        ):
            numeric_cols.append(col_name)
        elif cp.semantic_type in (SemanticType.CATEGORICAL, SemanticType.BOOLEAN):
            cat_cols.append(col_name)
        elif cp.semantic_type == SemanticType.DATE_TIME:
            dt_cols.append(col_name)
        elif cp.semantic_type == SemanticType.ID_COLUMN:
            id_cols.append(col_name)

        if cp.is_high_missing:
            high_missing.append(col_name)
        if cp.is_constant:
            constant.append(col_name)

    total_cells = len(df) * len(df.columns)
    total_missing = int(df.isna().sum().sum())
    missing_pct = round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0.0
    dup_count = int(df.duplicated().sum())

    partial = DataProfile(
        total_rows=len(df),
        total_columns=len(df.columns),
        total_missing=total_missing,
        total_missing_pct=missing_pct,
        memory_mb=round(df.memory_usage(deep=True).sum() / 1e6, 2),
        columns=col_profiles,
        numeric_columns=numeric_cols,
        categorical_columns=cat_cols,
        datetime_columns=dt_cols,
        id_columns=id_cols,
        high_missing_columns=high_missing,
        constant_columns=constant,
        duplicate_row_count=dup_count,
        quality_score=0.0,
    )
    partial.quality_score = _compute_quality_score(partial)
    logger.info(
        "Profile done: %d numeric, %d categorical, quality=%.1f",
        len(numeric_cols),
        len(cat_cols),
        partial.quality_score,
    )
    return partial
