"""
Header normalization and cell-level cleaning for extracted PDF table DataFrames.
"""

import re
import pandas as pd


_CURRENCY_RE = re.compile(r"[\$,]")
_PERCENT_RE  = re.compile(r"%$")
_WHITESPACE  = re.compile(r"\s+")


def clean_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names:
    - strip surrounding whitespace
    - collapse internal whitespace to single space
    - convert to snake_case
    - remove non-alphanumeric characters (except underscores)
    """
    df = df.copy()
    new_cols = []
    for col in df.columns:
        c = str(col).strip()
        c = _WHITESPACE.sub("_", c)
        c = re.sub(r"[^\w]", "", c)
        c = c.lower()
        c = c or f"col_{len(new_cols)}"
        new_cols.append(c)
    df.columns = _dedup_columns(new_cols)
    return df


def strip_cells(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all string cells."""
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(lambda v: str(v).strip() if v is not None else "")
    return df


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempt to coerce columns to numeric where the majority of values look numeric.
    Currency ($1,234.56) and percentages (12.5%) are handled.
    Original string values are preserved when coercion fails for a cell.
    """
    df = df.copy()
    for col in df.columns:
        series = df[col].copy()
        cleaned = series.apply(_parse_cell)
        n_numeric = cleaned.apply(lambda v: isinstance(v, float)).sum()
        if n_numeric / max(len(cleaned), 1) >= 0.6:
            df[col] = cleaned
    return df


def remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where all values are empty strings or whitespace."""
    df = df.copy()
    mask = df.apply(lambda r: any(str(v).strip() for v in r), axis=1)
    return df[mask].reset_index(drop=True)


def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows, keeping the first occurrence."""
    return df.drop_duplicates().reset_index(drop=True)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full cleaning pipeline in order."""
    df = strip_cells(df)
    df = remove_empty_rows(df)
    df = remove_duplicate_rows(df)
    df = clean_headers(df)
    df = coerce_numeric_columns(df)
    return df


# ── Helpers ────────────────────────────────────────────────────────────────────

def _dedup_columns(cols: list[str]) -> list[str]:
    """Make duplicate column names unique by appending _1, _2, etc."""
    seen: dict[str, int] = {}
    result = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            result.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            result.append(c)
    return result


def _parse_cell(value: str) -> float | str:
    """Try to parse a cell value as a float (handles $, commas, %)."""
    v = str(value).strip()
    if not v or v in ("N/A", "None", "nan", "-", "—"):
        return v
    is_currency = v.startswith("$")
    is_percent  = v.endswith("%")
    cleaned = _CURRENCY_RE.sub("", v)
    cleaned = _PERCENT_RE.sub("", cleaned)
    try:
        num = float(cleaned.replace(",", ""))
        if is_percent:
            return num   # keep as-is; caller decides whether to /100
        return num
    except ValueError:
        return value
