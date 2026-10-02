"""
PDF Exhibitor Data & Table Extractor — Streamlit Web Application
================================================================
Author  : Ashwin
GitHub  : https://github.com/ashwin8332
Version : 3.0.0

Run:
    streamlit run app/main.py
"""

import sys
from io import BytesIO
from pathlib import Path

# Add project root to sys.path so `src` is importable
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from src.exhibitor_extractor import extract_exhibitors
from src.exhibitor_exporter  import export_to_excel as export_exhibitors_to_excel, COLUMN_MAP
from src.extractor          import extract_tables_from_bytes, extract_tables_from_path
from src.validator          import validate_table, summarize_issues
from src.cleaner            import clean_dataframe
from src.exporter           import export_to_csv, export_to_excel as export_grid_to_excel, build_export_label

AAHAR_PDF  = ROOT_DIR / "data" / "Aahar 2025 Fair Guide.pdf"
SAMPLE_PDF = ROOT_DIR / "data" / "sample_report.pdf"

# ── Streamlit Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="PDF Extractor — Ashwin",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F3864;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Cached Extraction Helpers ──────────────────────────────────────────────────

@st.cache_data(show_spinner="Parsing PDF exhibitor profiles... Please wait.")
def cached_extract_from_bytes(pdf_bytes: bytes, filename: str) -> list[dict]:
    temp_dir = ROOT_DIR / "output" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / filename
    temp_path.write_bytes(pdf_bytes)
    return extract_exhibitors(temp_path)


@st.cache_data(show_spinner="Parsing PDF exhibitor profiles... Please wait.")
def cached_extract_from_path(pdf_path_str: str) -> list[dict]:
    return extract_exhibitors(Path(pdf_path_str))


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/PDF%20Extractor-v3.0.0-1F3864?style=for-the-badge", use_container_width=True)
    st.markdown("### Navigation & Modes")
    mode = st.radio(
        "Choose Mode:",
        ["🏆 Exhibitor Directory Extractor", "📊 Generic Grid Table Extractor"],
        index=0,
    )

    st.markdown("---")
    st.markdown("**Author:** Ashwin")
    st.markdown("[GitHub Repository](https://github.com/ashwin8332)")
    st.markdown("---")
    st.caption("Powered by `pdfplumber`, `pandas` & `openpyxl`")


# ══════════════════════════════════════════════════════════════════════════════
# MODE 1: EXHIBITOR DIRECTORY EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════════

if mode == "🏆 Exhibitor Directory Extractor":
    st.markdown("<div class='main-header'>🏆 PDF Exhibitor Directory Extractor</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Extract targeted exhibitor details (Company Name, Address, Contact Person, "
        "Tel./Mobile, E-mail, Products on Display) from any PDF guide or trade directory.</div>",
        unsafe_allow_html=True,
    )

    # Input controls
    c1, c2 = st.columns([1, 2])

    with c1:
        use_aahar = st.toggle("Use Aahar 2025 Fair Guide PDF", value=AAHAR_PDF.exists())

    with c2:
        if use_aahar:
            if AAHAR_PDF.exists():
                st.info(f"Using default sample PDF: `{AAHAR_PDF.name}` ({AAHAR_PDF.stat().st_size / (1024*1024):.1f} MB)")
                pdf_bytes_input = AAHAR_PDF.read_bytes()
                pdf_filename_input = AAHAR_PDF.name
            else:
                st.error("Aahar 2025 PDF not found in data/ folder.")
                pdf_bytes_input = None
                pdf_filename_input = None
        else:
            uploaded_pdf = st.file_uploader(
                "Upload any Exhibitor Directory PDF",
                type=["pdf"],
                help="Upload any PDF containing Field : Value exhibitor records."
            )
            if uploaded_pdf is not None:
                pdf_bytes_input = uploaded_pdf.read()
                pdf_filename_input = uploaded_pdf.name
            else:
                pdf_bytes_input = None
                pdf_filename_input = None

    if not pdf_bytes_input:
        st.info("👈 Upload a PDF or toggle 'Use Aahar 2025 Fair Guide PDF' to extract exhibitor data.")
        st.stop()

    # Extract automatically with caching
    exhibitors = cached_extract_from_bytes(pdf_bytes_input, pdf_filename_input)

    if not exhibitors:
        st.error("No exhibitor records were extracted from this PDF. Make sure the PDF contains selectable text and Field : Value profile entries.")
        st.stop()

    # Convert to DataFrame
    rows = [
        {display: ex.get(internal, "") for internal, display in COLUMN_MAP.items()}
        for ex in exhibitors
    ]
    df = pd.DataFrame(rows, columns=list(COLUMN_MAP.values()))

    # Summary Metrics
    st.markdown("---")
    st.subheader("📊 Extraction Summary & Metrics")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Exhibitors Extracted", f"{len(df):,}")
    m2.metric("Company Names Filled", f"{df['Company Name'].apply(lambda x: bool(str(x).strip())).sum():,} / {len(df):,}")
    m3.metric("E-mails Filled", f"{df['E-mail'].apply(lambda x: bool(str(x).strip())).sum():,} / {len(df):,}")
    m4.metric("Products Filled", f"{df['Products on Display'].apply(lambda x: bool(str(x).strip())).sum():,} / {len(df):,}")

    # Field Completeness Progress
    st.markdown("##### Field Completeness Breakdown")
    fc1, fc2 = st.columns(2)

    for idx, col in enumerate(df.columns):
        filled = df[col].apply(lambda v: bool(str(v).strip())).sum()
        pct = filled / len(df) if len(df) else 0.0
        target_col = fc1 if idx % 2 == 0 else fc2
        with target_col:
            st.write(f"**{col}**: {filled:,} / {len(df):,} ({pct * 100:.1f}%)")
            st.progress(pct)

    # Search & Filter
    st.markdown("---")
    st.subheader("🔍 Search & Filter Exhibitor Records")

    search_term = st.text_input(
        "Search exhibitors by name, email, address, or products:",
        placeholder="Type company name, product, city, or contact name...",
    )

    if search_term.strip():
        term = search_term.strip().lower()
        filtered_df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(term).any(), axis=1)]
        st.caption(f"Found **{len(filtered_df):,}** matching exhibitors out of {len(df):,}")
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True, height=450)

    # Export Buttons
    st.markdown("---")
    st.subheader("📥 Export Options")

    e1, e2 = st.columns(2)

    with e1:
        # Styled Excel Workbook
        excel_buf = export_exhibitors_to_excel(exhibitors, pdf_filename=pdf_filename_input)
        if isinstance(excel_buf, str):
            excel_bytes = Path(excel_buf).read_bytes()
        else:
            excel_bytes = excel_buf.getvalue()

        st.download_button(
            label="📗 Download Polished Excel Workbook (.xlsx)",
            data=excel_bytes,
            file_name=f"{Path(pdf_filename_input).stem}_Exhibitors.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with e2:
        # CSV Export
        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Download CSV Data (.csv)",
            data=csv_bytes,
            file_name=f"{Path(pdf_filename_input).stem}_Exhibitors.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# MODE 2: GENERIC GRID TABLE EXTRACTOR & VALIDATOR
# ══════════════════════════════════════════════════════════════════════════════

else:
    st.markdown("<div class='main-header'>📊 Generic Grid Table Extractor & Validator</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Extract grid tables from any PDF, run automated quality validation checks, "
        "apply header cleaning, and export to CSV or multi-sheet Excel.</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        use_sample_grid = st.toggle("Use Sample PDF", value=SAMPLE_PDF.exists())
    with c2:
        if use_sample_grid:
            if SAMPLE_PDF.exists():
                st.info(f"Using sample PDF: `{SAMPLE_PDF.name}`")
                grid_pdf_bytes = SAMPLE_PDF.read_bytes()
            else:
                st.error("Sample PDF not found in data/ folder.")
                grid_pdf_bytes = None
        else:
            uploaded_grid = st.file_uploader("Upload a Grid Table PDF", type=["pdf"])
            grid_pdf_bytes = uploaded_grid.read() if uploaded_grid else None

    auto_clean = st.checkbox("Auto-clean headers & coerce numerics", value=True)

    if not grid_pdf_bytes:
        st.warning("Please upload a PDF or toggle 'Use Sample PDF' to proceed.")
        st.stop()

    tables = extract_tables_from_bytes(grid_pdf_bytes)

    if not tables:
        st.warning("No grid tables detected in this PDF.")
        st.stop()

    pages_seen = len({t["page_number"] for t in tables})
    total_rows = sum(t["row_count"] for t in tables)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Tables Found", len(tables))
    mc2.metric("Pages with Tables", pages_seen)
    mc3.metric("Total Rows", total_rows)

    st.markdown("---")
    export_items: list[dict] = []

    for i, tbl in enumerate(tables):
        label      = build_export_label(tbl["page_number"], tbl["table_index"])
        df_raw     = tbl["dataframe"]
        df_display = clean_dataframe(df_raw) if auto_clean else df_raw

        issues  = validate_table(df_display, table_label=label)
        summary = summarize_issues(issues)

        with st.expander(
            f"**{label}** — {tbl['row_count']} rows × {tbl['col_count']} cols (Page {tbl['page_number']})",
            expanded=(i == 0),
        ):
            q1, q2, q3 = st.columns(3)
            q1.metric("Errors", summary["errors"])
            q2.metric("Warnings", summary["warnings"])
            status_text = "PASSED" if summary["passed"] else ("ERRORS" if summary["errors"] else "WARNINGS")
            q3.metric("Status", status_text)

            if issues:
                st.markdown("**Validation Issues:**")
                for issue in issues:
                    sev = issue["severity"]
                    if sev == "ERROR":
                        st.error(f"**ERROR**: {issue['message']}")
                    elif sev == "WARNING":
                        st.warning(f"**WARNING**: {issue['message']}")
                    else:
                        st.info(f"**INFO**: {issue['message']}")
            else:
                st.success("All validation checks passed.")

            st.dataframe(df_display, use_container_width=True)

            csv_buf = export_to_csv(df_display)
            st.download_button(
                label=f"Download {label}.csv",
                data=csv_buf,
                file_name=f"{label}.csv",
                mime="text/csv",
                key=f"grid_csv_{i}",
            )

            export_items.append({"dataframe": df_display, "label": label})

    st.markdown("---")
    st.subheader("Bulk Export")
    if export_items:
        xlsx_buf = export_grid_to_excel(export_items)
        st.download_button(
            label="Download All Tables (.xlsx)",
            data=xlsx_buf,
            file_name="extracted_tables.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="grid_xlsx_all",
        )
