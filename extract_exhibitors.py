#!/usr/bin/env python3
"""
PDF Exhibitor Data Extractor — Universal Runner
================================================
Author  : Ashwin
GitHub  : https://github.com/ashwin8332
Version : 3.0.0

Extracts structured exhibitor/contact data from any PDF that uses
the field-label format:

    Company Name : ...
    Address      : ...
    Contact Person : ...
    Tel./Mobile  : ...
    E-mail       : ...
    Products on Display : ...

Works with:
  - Fair/trade-show guide PDFs (e.g. Aahar 2025)
  - Exhibitor directories
  - Any PDF whose pages contain the above key:value fields

Usage
-----
    # Default (looks for PDF in data/ folder):
    python extract_exhibitors.py

    # Specify your own PDF and output path:
    python extract_exhibitors.py --pdf "path/to/your.pdf" --out "results/output.xlsx"

    # Show more preview rows:
    python extract_exhibitors.py --preview 20
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

# Auto-detect first PDF in data/ as default, else require --pdf argument
_pdfs_in_data = sorted(DATA_DIR.glob("*.pdf")) if DATA_DIR.exists() else []
DEFAULT_PDF  = _pdfs_in_data[0] if _pdfs_in_data else DATA_DIR / "input.pdf"
DEFAULT_XLSX = OUTPUT_DIR / "extracted_exhibitors.xlsx"

sys.path.insert(0, str(ROOT_DIR))
from src.exhibitor_extractor import extract_exhibitors
from src.exhibitor_exporter  import export_to_excel, COLUMN_MAP


# ── CLI ────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_exhibitors",
        description=(
            "Extract exhibitor contact data from any PDF that uses key:value "
            "field labels (Company Name, Address, Contact Person, Tel./Mobile, "
            "E-mail, Products on Display)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_exhibitors.py
  python extract_exhibitors.py --pdf "data/Aahar 2025 Fair Guide.pdf"
  python extract_exhibitors.py --pdf "data/my_guide.pdf" --out "output/result.xlsx"
  python extract_exhibitors.py --preview 20
        """,
    )
    parser.add_argument(
        "--pdf", "-p",
        type=Path,
        default=DEFAULT_PDF,
        metavar="PDF_PATH",
        help=f"Path to the input PDF (default: first PDF found in data/)",
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
        help="Number of rows to preview in terminal (default: 10, 0 to skip)",
    )
    return parser


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    args = _build_parser().parse_args()

    pdf_path  = args.pdf.resolve()
    xlsx_path = args.out.resolve()

    _banner()

    if not pdf_path.exists():
        print(f"\n[ERROR] PDF not found: {pdf_path}")
        print("  -->  Please check the --pdf argument or place the PDF in data/")
        print(f"  -->  Available PDFs in data/: {[p.name for p in _pdfs_in_data]}")
        return 1

    xlsx_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'-'*62}")
    print(f"  Input  : {pdf_path.name}")
    print(f"  Output : {xlsx_path}")
    print(f"{'-'*62}\n")

    # ── Extract ────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    exhibitors = extract_exhibitors(pdf_path)
    extract_time = time.perf_counter() - t0

    if not exhibitors:
        print("\n[WARNING] No exhibitor records were extracted.")
        print("  Possible reasons:")
        print("  - PDF uses image-based pages (scanned) — OCR not supported")
        print("  - PDF does not contain 'Field : Value' exhibitor profiles")
        print("  - All pages were skipped as non-exhibitor content")
        return 2

    # ── Build DataFrame for display ────────────────────────────────────────────
    df = pd.DataFrame([
        {display: ex.get(internal, "")
         for internal, display in COLUMN_MAP.items()}
        for ex in exhibitors
    ])

    # ── Export ─────────────────────────────────────────────────────────────────
    t1 = time.perf_counter()
    try:
        export_to_excel(
            exhibitors,
            output_path=xlsx_path,
            pdf_filename=pdf_path.name,
        )
        export_time = time.perf_counter() - t1
    except PermissionError:
        export_time = time.perf_counter() - t1
        print(f"\n[ERROR] Cannot write to: {xlsx_path}")
        print("  The file may be open in Excel. Close it and retry.")
        return 3

    # ── Summary & preview ──────────────────────────────────────────────────────
    _print_summary(df, extract_time, export_time, xlsx_path)

    if args.preview > 0:
        _print_preview(df, args.preview)

    print(f"\n[DONE]  Output saved to: {xlsx_path}\n")
    return 0


# ── Print helpers ──────────────────────────────────────────────────────────────

def _banner() -> None:
    print("""
+--------------------------------------------------------------+
|   PDF Exhibitor Data Extractor                               |
|   Author : Ashwin                                            |
|   GitHub : https://github.com/ashwin8332                     |
|   Works with any PDF containing Field : Value profiles       |
+--------------------------------------------------------------+
""")


def _print_summary(
    df: pd.DataFrame,
    extract_time: float,
    export_time: float,
    xlsx_path: Path,
) -> None:
    print(f"\n{'='*62}")
    print("  EXTRACTION SUMMARY")
    print(f"{'='*62}")
    print(f"  Total exhibitors extracted : {len(df)}")
    print(f"  Extraction time            : {extract_time:.1f}s")
    print(f"  Export time                : {export_time:.1f}s")
    if xlsx_path.exists():
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
    print(f"{'='*62}")


def _print_preview(df: pd.DataFrame, n: int) -> None:
    print(f"\n  Preview -- first {min(n, len(df))} records:\n")
    preview = df.head(n).copy()
    for col in ["Address", "Products on Display"]:
        if col in preview.columns:
            preview[col] = preview[col].apply(
                lambda v: (v[:55] + "...") if len(v) > 55 else v
            )
    try:
        print(preview.to_string(index=False, max_colwidth=38))
    except Exception:
        print(preview.to_string(index=False))
    print()


if __name__ == "__main__":
    sys.exit(main())
