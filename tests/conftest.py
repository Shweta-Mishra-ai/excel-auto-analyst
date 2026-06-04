"""
tests/conftest.py
Shared pytest fixtures — one place, used everywhere.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# ─── DataFrames ──────────────────────────────────────────────────


@pytest.fixture
def clean_df() -> pd.DataFrame:
    """A well-formed DataFrame with numeric and categorical columns."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame(
        {
            "sales": np.random.normal(5000, 1200, n).round(2),
            "units": np.random.randint(10, 500, n),
            "profit": np.random.normal(1500, 400, n).round(2),
            "region": np.random.choice(["North", "South", "East", "West"], n),
            "product": np.random.choice(["Widget", "Gadget", "Doohickey"], n),
            "date": pd.date_range("2023-01-01", periods=n, freq="D"),
        }
    )


@pytest.fixture
def dirty_df() -> pd.DataFrame:
    """A DataFrame with missing values, duplicates, and outliers."""
    np.random.seed(99)
    n = 80
    df = pd.DataFrame(
        {
            "revenue": np.random.normal(10000, 2000, n).round(2),
            "cost": np.random.normal(6000, 1500, n).round(2),
            "category": np.random.choice(["A", "B", "C", None], n),
            "country": np.random.choice(["US", "UK", "DE", None], n),
        }
    )
    # Inject missing values
    df.loc[::5, "revenue"] = None
    df.loc[::7, "cost"] = None
    # Inject outlier
    df.loc[0, "revenue"] = 999_999.0
    # Inject duplicate rows
    df = pd.concat([df, df.iloc[:5]], ignore_index=True)
    return df


@pytest.fixture
def tiny_df() -> pd.DataFrame:
    """Minimal 3-row DataFrame for edge case tests."""
    return pd.DataFrame({"value": [1.0, 2.0, 3.0], "label": ["a", "b", "c"]})


@pytest.fixture
def empty_df() -> pd.DataFrame:
    return pd.DataFrame()


@pytest.fixture
def all_null_col_df() -> pd.DataFrame:
    """DataFrame where one column is entirely null."""
    return pd.DataFrame(
        {
            "good": [1.0, 2.0, 3.0, 4.0, 5.0],
            "all_null": [None, None, None, None, None],
            "label": ["a", "b", "c", "d", "e"],
        }
    )


@pytest.fixture
def duplicate_col_df() -> pd.DataFrame:
    """DataFrame with duplicate column names."""
    df = pd.DataFrame([[1, 2, 3]], columns=["a", "b", "a"])
    return df


@pytest.fixture
def csv_bytes(clean_df) -> bytes:
    return clean_df.to_csv(index=False).encode("utf-8")


@pytest.fixture
def excel_bytes(clean_df) -> bytes:
    import io

    buf = io.BytesIO()
    clean_df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()
