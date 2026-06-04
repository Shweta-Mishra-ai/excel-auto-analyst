"""
tests/test_data_loader.py
Unit tests for core/data_loader.py
"""

from __future__ import annotations

import io

import pytest

from core.data_loader import (
    FileFormat,
    LoadError,
    detect_format,
    load_dataframe,
)

# ─── detect_format ────────────────────────────────────────────────


class TestDetectFormat:
    def test_csv_lowercase(self):
        assert detect_format("data.csv") == FileFormat.CSV

    def test_csv_uppercase(self):
        assert detect_format("DATA.CSV") == FileFormat.CSV

    def test_xlsx(self):
        assert detect_format("report.xlsx") == FileFormat.EXCEL

    def test_xls(self):
        assert detect_format("old.xls") == FileFormat.EXCEL

    def test_xlsm(self):
        assert detect_format("macro.xlsm") == FileFormat.EXCEL

    def test_unknown_returns_unknown(self):
        assert detect_format("notes.txt") == FileFormat.UNKNOWN

    def test_no_extension(self):
        assert detect_format("nodotfile") == FileFormat.UNKNOWN


# ─── load_dataframe ───────────────────────────────────────────────


class TestLoadDataframe:
    def test_load_valid_csv(self, csv_bytes):
        result = load_dataframe(csv_bytes, "data.csv")
        assert result.file_format == FileFormat.CSV
        assert result.original_rows == 100
        assert result.original_columns == 6
        assert "sales" in result.df.columns

    def test_load_valid_excel(self, excel_bytes):
        result = load_dataframe(excel_bytes, "data.xlsx")
        assert result.file_format == FileFormat.EXCEL
        assert result.original_rows == 100

    def test_load_returns_load_result(self, csv_bytes):
        from core.data_loader import LoadResult

        result = load_dataframe(csv_bytes, "data.csv")
        assert isinstance(result, LoadResult)

    def test_shape_summary_format(self, csv_bytes):
        result = load_dataframe(csv_bytes, "data.csv")
        assert "rows" in result.shape_summary
        assert "×" in result.shape_summary  # noqa: RUF001

    def test_unsupported_extension_raises(self):
        with pytest.raises(LoadError, match="Unsupported"):
            load_dataframe(b"some data", "notes.txt")

    def test_empty_csv_raises(self):
        empty_csv = b"col1,col2\n"  # header only, no rows
        with pytest.raises(LoadError, match="empty"):
            load_dataframe(empty_csv, "empty.csv")

    def test_duplicate_columns_raises(self, duplicate_col_df):
        buf = io.BytesIO()
        duplicate_col_df.to_csv(buf, index=False)
        with pytest.raises(LoadError, match="Duplicate"):
            load_dataframe(buf.getvalue(), "dupes.csv")

    def test_file_name_stored_in_result(self, csv_bytes):
        result = load_dataframe(csv_bytes, "my_data.csv")
        assert result.file_name == "my_data.csv"

    def test_corrupted_bytes_raises(self):
        with pytest.raises(LoadError):
            load_dataframe(b"this is not valid excel", "bad.xlsx")

    def test_latin1_csv_loads(self):
        # CSV with latin-1 encoded special characters
        latin_csv = "name,value\nCafé,100\nnaïve,200\n".encode("latin-1")
        result = load_dataframe(latin_csv, "latin.csv")
        assert len(result.df) == 2
