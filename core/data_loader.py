"""
core/data_loader.py
Responsible for ONE thing: loading a file into a validated DataFrame.
All error handling lives here so callers never deal with raw exceptions.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

from config.settings import CONFIG

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LoadError(Exception):
    """Raised when a file cannot be loaded or fails validation."""


class FileFormat(str, Enum):  # noqa: UP042, RUF100
    CSV = "csv"
    EXCEL = "excel"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LoadResult:
    """Immutable result returned by load_dataframe()."""

    df: pd.DataFrame
    file_format: FileFormat
    original_rows: int
    original_columns: int
    file_name: str

    @property
    def shape_summary(self) -> str:
        return f"{self.original_rows:,} rows × {self.original_columns} columns"  # noqa: RUF001


def detect_format(file_name: str) -> FileFormat:
    """Detect file format from extension."""
    name = file_name.lower()
    if name.endswith(".csv"):
        return FileFormat.CSV
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        return FileFormat.EXCEL
    return FileFormat.UNKNOWN


def _read_csv(content: bytes) -> pd.DataFrame:
    """Try multiple encodings — real-world CSVs are messy."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return pd.read_csv(
                io.BytesIO(content),
                encoding=encoding,
                low_memory=False,
            )
        except UnicodeDecodeError:
            continue
    raise LoadError("Could not decode CSV. Try saving as UTF-8 from Excel.")


def _read_excel(content: bytes) -> pd.DataFrame:
    try:
        return pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise LoadError(f"Failed to read Excel file: {exc}") from exc


def _validate(df: pd.DataFrame, file_name: str) -> None:
    """Hard validation — raises LoadError on any violation."""
    limits = CONFIG.data

    if df.empty:
        raise LoadError("File is empty — no data to analyse.")

    if len(df) > limits.max_rows:
        raise LoadError(
            f"File has {len(df):,} rows but the limit is "
            f"{limits.max_rows:,}. Please filter or sample the data."
        )

    if len(df.columns) > limits.max_columns:
        raise LoadError(
            f"File has {len(df.columns)} columns but the limit is {limits.max_columns}."
        )

    # Duplicate column names break almost everything downstream
    if df.columns.duplicated().any():
        dupes = df.columns[df.columns.duplicated()].tolist()
        raise LoadError(
            f"Duplicate column names found: {dupes}. Rename them before uploading."
        )


def _detect_duplicate_headers(content: bytes, fmt: FileFormat) -> list[str]:
    """Inspect the first line or row of the raw file to find exact duplicate column headers."""
    if fmt == FileFormat.CSV:
        # Try different encodings as done in _read_csv
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                # Find the end of the first line
                first_line_end = content.find(b"\n")
                if first_line_end == -1:
                    first_line = content
                else:
                    first_line = content[:first_line_end]

                decoded = first_line.decode(encoding)
                import csv

                reader = csv.reader([decoded])
                header = next(reader, None)
                if header:
                    seen = set()
                    dupes = []
                    for col in header:
                        if col in seen:
                            if col not in dupes:
                                dupes.append(col)
                        seen.add(col)
                    return dupes
                break
            except Exception:  # noqa: S112 # nosec B112
                continue
    elif fmt == FileFormat.EXCEL:
        try:
            import openpyxl

            wb = openpyxl.load_workbook(
                io.BytesIO(content), read_only=True, data_only=True
            )
            ws = wb.active
            if ws:
                first_row = next(ws.iter_rows(max_row=1, values_only=True), None)
                if first_row:
                    seen = set()
                    dupes = []
                    for val in first_row:
                        if val is not None:
                            val_str = str(val).strip()
                            if val_str in seen:
                                if val_str not in dupes:
                                    dupes.append(val_str)
                            seen.add(val_str)
                    return dupes
        except Exception as e:
            logger.warning("Excel duplicate column detection failed: %s", e)
    return []


def load_dataframe(file_bytes: bytes, file_name: str) -> LoadResult:
    """
    Public API — load, validate, and return a LoadResult.

    Parameters
    ----------
    file_bytes:
        Raw bytes of the uploaded file.
    file_name:
        Original filename (used for format detection and error messages).

    Returns
    -------
    LoadResult

    Raises
    ------
    LoadError
        If the file cannot be parsed, is empty, or violates size limits.
    """
    fmt = detect_format(file_name)

    if fmt == FileFormat.UNKNOWN:
        raise LoadError(
            f"Unsupported file type: '{file_name}'. Please upload a .csv or .xlsx file."
        )

    logger.info("Loading %s (%s)", file_name, fmt.value)

    # Detect duplicate headers BEFORE loading with Pandas
    dupes = _detect_duplicate_headers(file_bytes, fmt)
    if dupes:
        raise LoadError(
            f"Duplicate column names found: {dupes}. Rename them before uploading."
        )

    if fmt == FileFormat.CSV:
        df = _read_csv(file_bytes)
    else:
        df = _read_excel(file_bytes)

    _validate(df, file_name)

    logger.info("Loaded %s: %d rows × %d columns", file_name, len(df), len(df.columns))  # noqa: RUF001

    return LoadResult(
        df=df,
        file_format=fmt,
        original_rows=len(df),
        original_columns=len(df.columns),
        file_name=file_name,
    )
