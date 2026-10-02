# Architecture — PDF Table Extractor

## Overview

PDF Table Extractor is a Type D (ETL/Pipeline) application. It extracts structured tables from unstructured PDF documents, validates data quality, applies a cleaning pipeline, and exports results to CSV or Excel. All processing is local; no external APIs or cloud services are used.

---

## Module Map

| Module | Responsibility |
|---|---|
| `app/main.py` | Streamlit UI — file upload, per-table quality report, cleaning controls, download buttons |
| `src/extractor.py` | PDF page iteration; line-based table detection; raw-to-DataFrame conversion |
| `src/validator.py` | Six-check data quality validation pipeline; severity-sorted issue list |
| `src/cleaner.py` | Five-step cleaning pipeline: strip, remove empty rows, deduplicate, normalize headers, coerce numerics |
| `src/exporter.py` | CSV export (BytesIO or disk) and multi-sheet Excel export via openpyxl |
| `src/__init__.py` | Public API surface — eleven exported names from the four source modules |
| `scripts/create_sample_pdf.py` | reportlab utility to generate `data/sample_report.pdf` for testing and demo |

---

## Data Flow

```
PDF file (path or bytes)
        │
        ▼
  src/extractor.py
  ─────────────────
  pdfplumber opens PDF
  Iterates every page
  page.extract_tables() with line-based settings
  _table_to_dataframe(): first non-empty row → header
                         deduplicate column names
                         pad/truncate rows to column width
                         drop all-empty rows
        │
        ▼  list[dict]
        │  { page_number, table_index, raw_rows,
        │    dataframe, row_count, col_count }
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
  src/validator.py                     src/cleaner.py
  ─────────────────                    ──────────────────
  _check_empty_table()                 strip_cells()
  _check_missing_values()              remove_empty_rows()
  _check_duplicate_rows()              remove_duplicate_rows()
  _check_column_consistency()          clean_headers()
  _check_mixed_types()                 coerce_numeric_columns()
  _check_empty_headers()
  sorted by SEVERITY_ORDER             Returns cleaned DataFrame
  Returns list[dict] issues
        │                                      │
        └────────────────┬─────────────────────┘
                         ▼
                   src/exporter.py
                   ─────────────────
                   export_to_csv()     → BytesIO or disk CSV
                   export_to_excel()   → BytesIO or disk .xlsx
                                         (one sheet per table)
```

---

## pdfplumber Detection Settings

P09 uses pdfplumber's **line-based** table detection, not the text/word-spacing strategy. This is a deliberate choice: line-based detection is deterministic and produces zero false positives on tables with visible grid lines. The trade-off is that borderless or image-based tables are not detected.

```python
table_settings = {
    "vertical_strategy":   "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance":       5,    # px — snap nearby line endpoints
    "join_tolerance":       3,    # px — join broken line segments
    "edge_min_length":     10,    # px — ignore very short edges (noise)
}
```

`snap_tolerance=5` and `join_tolerance=3` handle the common case where PDF rendering software draws table borders as slightly misaligned segments rather than perfectly connected lines. Setting these too high causes false positives; too low causes missed tables.

---

## Validation Check Reference

| Check | Severity | Threshold / Trigger |
|---|---|---|
| `empty_table` | ERROR | DataFrame has zero rows |
| `empty_headers` | ERROR | One or more column names are blank strings |
| `missing_values` | ERROR | Blank / N/A / null values in a column exceed 30% of rows |
| `missing_values` | WARNING | Blank / N/A / null values present but ≤ 30% of rows |
| `duplicate_rows` | WARNING | Exact duplicate rows detected |
| `auto_column_names` | WARNING | Column names match `col_N` pattern — header row likely not detected |
| `mixed_types` | WARNING | Column is 50–95% numeric; remaining cells contain non-numeric text |

Issues are sorted by `SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}` before being returned.

`summarize_issues()` returns `passed: True` only when there are zero errors **and** zero warnings.

---

## Cleaning Pipeline

`clean_dataframe()` applies five steps in order. Each step is a pure function that returns a new DataFrame; the original is never mutated.

| Step | Function | Action |
|---|---|---|
| 1 | `strip_cells()` | Strip leading/trailing whitespace from all string cells; `None` → `""` |
| 2 | `remove_empty_rows()` | Drop rows where every cell is empty or whitespace-only |
| 3 | `remove_duplicate_rows()` | Drop exact duplicate rows; keep first occurrence |
| 4 | `clean_headers()` | Normalize column names: strip whitespace → collapse spaces to `_` → remove non-alphanumeric → lowercase → deduplicate |
| 5 | `coerce_numeric_columns()` | Columns with ≥ 60% numeric-looking values are coerced to float; handles `$`, commas, `%` |

**Why this order matters:** Stripping cells first ensures the duplicate-row check and numeric coercion see clean values, not values that differ only by padding whitespace. Cleaning headers last means header normalization does not interfere with validation, which runs on the pre-cleaned version when used independently.

---

## BytesIO-First Export Design

Both `export_to_csv()` and `export_to_excel()` default to returning a `BytesIO` buffer when `output_path=None`. This design was chosen for Streamlit compatibility: `st.download_button` requires an in-memory buffer, not a file path. Passing `output_path` redirects output to disk for batch or non-Streamlit use cases.

---

## Key Design Decisions

### Line-based detection over text strategy
Text-strategy detection (where pdfplumber infers table structure from character spacing) produces false positives on multi-column text layouts that have no table intent. Line-based detection is safe for documents with explicit borders and fails silently for documents without them.

### Header deduplication with `_N` suffix
When a PDF table has repeated column headers (common in financial tables with repeated "Amount" columns), `_table_to_dataframe()` deduplicates with a `_N` suffix (`Amount`, `Amount_1`, `Amount_2`) rather than raising an error or overwriting. This preserves all data without silent data loss.

### 60% numeric threshold for coercion
Columns where fewer than 60% of values look numeric are left as strings. A lower threshold risks coercing columns that are mostly text with a few numeric-looking strings. A higher threshold risks leaving genuinely numeric columns uncleaned when a small number of cells contain notes or flags.

### Validation runs on cleaned data
In the Streamlit UI, validation runs on the cleaned DataFrame, not the raw extracted version. This reflects what the user will actually download. A user who checks "Auto-clean" and downloads a CSV should see quality results that match the file they receive.

### `data/sample_report.pdf` committed to repository
The integration tests in `test_extractor.py` (`TestExtractSamplePdf`) require the sample PDF to be present. Committing it eliminates a setup step in CI and makes the test suite runnable immediately after `git clone` without needing to run the generation script. The PDF is deterministic and small (~10 KB).
