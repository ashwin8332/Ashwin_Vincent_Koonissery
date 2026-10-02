"""
Export extracted (and optionally cleaned) tables to CSV or multi-sheet Excel.
"""

from io import BytesIO
from pathlib import Path

import pandas as pd


def export_to_csv(df: pd.DataFrame, output_path: str | Path | None = None) -> str | BytesIO:
    """
    Export a single DataFrame to CSV.
    - If output_path is given, writes to disk and returns the path string.
    - Otherwise returns a BytesIO buffer (for Streamlit download_button).
    """
    if output_path is not None:
        df.to_csv(str(output_path), index=False)
        return str(output_path)
    buf = BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


def export_to_excel(
    tables: list[dict],
    output_path: str | Path | None = None,
    sheet_name_key: str = "label",
) -> str | BytesIO:
    """
    Export multiple tables to a single multi-sheet Excel workbook.

    Each item in `tables` must have:
      - "dataframe": pd.DataFrame
      - "label" (or the value of sheet_name_key): str used as the sheet name

    Returns a file path string if output_path is provided, else a BytesIO buffer.
    """
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for i, item in enumerate(tables):
            df    = item.get("dataframe", pd.DataFrame())
            label = item.get(sheet_name_key, f"Table_{i + 1}")
            # Excel sheet names: max 31 chars, no special chars
            sheet = _safe_sheet_name(label, i)
            df.to_excel(writer, sheet_name=sheet, index=False)
    buf.seek(0)

    if output_path is not None:
        Path(output_path).write_bytes(buf.read())
        return str(output_path)

    buf.seek(0)
    return buf


def build_export_label(page_number: int, table_index: int) -> str:
    """Return a human-readable label for a table extracted from a PDF."""
    return f"Page{page_number}_Table{table_index + 1}"


def _safe_sheet_name(name: str, index: int) -> str:
    """Truncate and sanitize an Excel sheet name."""
    invalid = r'\/?*[]:'
    safe = name
    for ch in invalid:
        safe = safe.replace(ch, "_")
    safe = safe[:31]
    return safe or f"Sheet_{index + 1}"
