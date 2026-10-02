"""
Extract tables from PDF files using pdfplumber.

pdfplumber is used over camelot because it requires no system dependencies
(no Ghostscript/Tkinter) and handles the majority of real-world PDF tables.
"""

from pathlib import Path
from io import BytesIO

import pdfplumber
import pandas as pd


def extract_tables_from_path(pdf_path: str | Path) -> list[dict]:
    """Extract all tables from a PDF file on disk."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        return _extract(pdf)


def extract_tables_from_bytes(pdf_bytes: bytes) -> list[dict]:
    """Extract all tables from PDF bytes (e.g. from an uploaded file)."""
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        return _extract(pdf)


def _extract(pdf: pdfplumber.PDF) -> list[dict]:
    """
    Iterate every page, extract tables, and return a list of result dicts.
    Each dict has: page_number, table_index, raw_rows, dataframe.
    """
    results = []
    for page_num, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables(
            table_settings={
                "vertical_strategy":   "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance":       5,
                "join_tolerance":       3,
                "edge_min_length":     10,
            }
        )
        for t_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue  # skip empty or header-only tables
            df = _table_to_dataframe(table)
            if df is None or df.empty:
                continue
            results.append({
                "page_number":  page_num,
                "table_index":  t_idx,
                "raw_rows":     table,
                "dataframe":    df,
                "row_count":    len(df),
                "col_count":    len(df.columns),
            })
    return results


def _table_to_dataframe(table: list[list]) -> pd.DataFrame | None:
    """
    Convert a raw pdfplumber table (list of lists) to a DataFrame.
    First non-empty row is used as the header.
    """
    if not table:
        return None

    # Find the first row with actual content to use as header
    header_idx = 0
    for i, row in enumerate(table):
        if any(cell and str(cell).strip() for cell in row):
            header_idx = i
            break

    headers = [
        str(cell).strip() if cell else f"col_{j}"
        for j, cell in enumerate(table[header_idx])
    ]
    # Deduplicate header names
    seen: dict[str, int] = {}
    deduped = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            deduped.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            deduped.append(h)

    data_rows = table[header_idx + 1:]
    if not data_rows:
        return None

    # Pad/truncate rows to match header length
    n_cols = len(deduped)
    padded = [
        (list(row) + [""] * n_cols)[:n_cols]
        for row in data_rows
    ]

    df = pd.DataFrame(padded, columns=deduped)
    # Clean cell values
    for col in df.columns:
        df[col] = df[col].apply(lambda x: str(x).strip() if x is not None else "")

    # Drop rows that are entirely empty
    df = df[df.apply(lambda r: any(v.strip() for v in r), axis=1)].reset_index(drop=True)
    return df


def get_pdf_info(pdf_path: str | Path) -> dict:
    """Return basic metadata about the PDF."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        return {
            "page_count": len(pdf.pages),
            "metadata":   pdf.metadata or {},
        }
