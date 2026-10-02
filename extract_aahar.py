#!/usr/bin/env python3
"""
Aahar 2025 Fair Guide — Main Extraction Runner
================================================
Author  : Ashwin
GitHub  : https://github.com/ashwin8332
Version : 2.1.0

Usage
-----
    python extract_aahar.py

    # Custom paths
    python extract_aahar.py --pdf "path/to/file.pdf" --out "path/to/output.xlsx"

The script:
    1. Opens the Aahar 2025 Fair Guide PDF using pdfplumber.
    2. Extracts exhibitor fields (Company Name, Address, Contact Person,
       Tel./Mobile, E-mail, Products on Display) using dual-format parsing.
    3. Exports the cleaned data to a structured Excel workbook.
    4. Prints a summary table and per-field completeness report.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

# ── Path setup ─────────────────────────────────────────────────────────────────
ROOT_DIR     = Path(__file__).parent
DATA_DIR     = ROOT_DIR / "data"
OUTPUT_DIR   = ROOT_DIR / "output"
DEFAULT_PDF  = DATA_DIR / "Aahar 2025 Fair Guide.pdf"
DEFAULT_XLSX = OUTPUT_DIR / "Aahar_2025_Exhibitors.xlsx"

# Make src importable when running from project root
sys.path.insert(0, str(ROOT_DIR))
from src.aahar_extractor import extract_exhibitors
from src.aahar_exporter  import export_to_excel, COLUMN_MAP


# ── CLI argument parser ────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_aahar",
        description="Extract exhibitor data from the Aahar 2025 Fair Guide PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_aahar.py
  python extract_aahar.py --pdf data/Aahar\\ 2025\\ Fair\\ Guide.pdf
  python extract_aahar.py --pdf data/guide.pdf --out results/exhibitors.xlsx
        """,
    )
    parser.add_argument(
        "--pdf", "-p",
        type=Path,
        default=DEFAULT_PDF,
        metavar="PDF_PATH",
        help=f"Path to the input PDF (default: {DEFAULT_PDF})",
    )
    parser.add_argument(
        "--out", "-o",
        type=Path,
        default=DEFAULT_XLSX,
        metavar="XLSX_PATH",
        help=f"Path for the output Excel file (default: {DEFAULT_XLSX})",
    )
    parser.add_argument(
        "--preview", "-n",
        type=int,
        default=10,
        metavar="N",
        help="Number of rows to print in the preview table (default: 10, 0 to skip)",
    )
    return parser


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    args = _build_parser().parse_args()

    pdf_path  = args.pdf.resolve()
    xlsx_path = args.out.resolve()

    _banner()

    # ── Validate input ─────────────────────────────────────────────────────────
    if not pdf_path.exists():
        print(f"\n[ERROR] PDF not found: {pdf_path}")
        print("  -->  Please check the --pdf argument or place the file in data/")
        return 1

    xlsx_path.parent.mkdir(parents=True, exist_ok=True)

    # -- Extract -------------------------------------------------------------------
    print(f"\n{'-'*60}")
    print(f"  Input  : {pdf_path}")
    print(f"  Output : {xlsx_path}")
    print(f"{'-'*60}\n")

    t0 = time.perf_counter()
    exhibitors = extract_exhibitors(pdf_path)
    extract_time = time.perf_counter() - t0

    if not exhibitors:
        print("\n[WARNING] No exhibitors were extracted.")
        print("  Please verify the PDF is the correct Aahar 2025 Fair Guide.")
        return 2

    # ── Build DataFrame for preview / stats ───────────────────────────────────
    df = pd.DataFrame([
        {display: ex.get(internal, "") for internal, display in COLUMN_MAP.items()}
        for ex in exhibitors
    ])

    # ── Export ─────────────────────────────────────────────────────────────────
    t1 = time.perf_counter()
    export_to_excel(exhibitors, output_path=xlsx_path, pdf_filename=pdf_path.name)
    export_time = time.perf_counter() - t1

    # ── Summary ────────────────────────────────────────────────────────────────
    _print_summary(df, extract_time, export_time, xlsx_path)

    # ── Preview ────────────────────────────────────────────────────────────────
    if args.preview > 0:
        _print_preview(df, args.preview)

    print(f"\n[DONE]  Output saved to: {xlsx_path}\n")
    return 0


# ── Print helpers ──────────────────────────────────────────────────────────────

def _banner() -> None:
    print("""
+----------------------------------------------------------+
|    AAHAR 2025 FAIR GUIDE - Exhibitor Extractor           |
|    Author : Ashwin                                               |
|    GitHub : https://github.com/ashwin8332               |
+----------------------------------------------------------+
""")


def _print_summary(
    df: pd.DataFrame,
    extract_time: float,
    export_time: float,
    xlsx_path: Path,
) -> None:
    print(f"\n{'='*60}")
    print("  EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"  Total exhibitors extracted : {len(df)}")
    print(f"  Extraction time            : {extract_time:.1f}s")
    print(f"  Export time                : {export_time:.1f}s")
    print(f"  Output file size           : {xlsx_path.stat().st_size / 1024:.1f} KB")
    print()
    print("  Field Completeness:")
    print(f"  {'Field':<28}  {'Filled':>7}  {'%':>7}")
    print(f"  {'-'*28}  {'-'*7}  {'-'*7}")
    for col in df.columns:
        filled = df[col].apply(lambda v: bool(str(v).strip())).sum()
        pct    = filled / len(df) * 100 if len(df) else 0
        bar    = "#" * int(pct / 10) + "." * (10 - int(pct / 10))
        print(f"  {col:<28}  {filled:>7}  {pct:>6.1f}%  {bar}")
    print(f"{'='*60}")


def _print_preview(df: pd.DataFrame, n: int) -> None:
    print(f"\n  Preview — first {min(n, len(df))} records:\n")
    preview = df.head(n).copy()
    # Truncate long fields for display
    for col in ["Address", "Products on Display"]:
        if col in preview.columns:
            preview[col] = preview[col].apply(
                lambda v: (v[:60] + "…") if len(v) > 60 else v
            )
    try:
        print(preview.to_string(index=False, max_colwidth=40))
    except Exception:
        print(preview.to_string(index=False))
    print()


if __name__ == "__main__":
    sys.exit(main())
