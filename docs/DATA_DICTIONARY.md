# Data Dictionary — PDF Table Extractor

## Inputs

### PDF file

Accepted as either a file path (string or `pathlib.Path`) or raw bytes (`bytes`).

| Parameter | Type | Notes |
|---|---|---|
| `pdf_path` | `str \| Path` | Used by `extract_tables_from_path()` |
| `pdf_bytes` | `bytes` | Used by `extract_tables_from_bytes()`; standard for Streamlit `file_uploader` |

**Requirements:** The PDF must contain tables with explicit border lines (grid lines). Borderless tables and image-based PDFs are not supported.

---

## Extraction Output

`extract_tables_from_path()` and `extract_tables_from_bytes()` return `list[dict]`. Each dict represents one extracted table.

| Field | Type | Description |
|---|---|---|
| `page_number` | `int` | 1-based page number where the table was found |
| `table_index` | `int` | 0-based index of the table on its page (for pages with multiple tables) |
| `raw_rows` | `list[list[str \| None]]` | Raw rows as returned by pdfplumber before any processing |
| `dataframe` | `pd.DataFrame` | Processed DataFrame: first non-empty row used as header; duplicate column names deduplicated; short rows padded; all-empty rows dropped |
| `row_count` | `int` | Number of data rows in `dataframe` (equals `len(dataframe)`) |
| `col_count` | `int` | Number of columns in `dataframe` (equals `len(dataframe.columns)`) |

### `build_export_label(page_number, table_index) → str`

Returns a human-readable label used as the sheet name in Excel export and the filename stem in CSV export.

```
build_export_label(1, 0)  →  "Page1_Table1"
build_export_label(2, 1)  →  "Page2_Table2"
```

---

## `get_pdf_info()` Output

```python
get_pdf_info(pdf_path: str | Path) -> dict
```

| Field | Type | Description |
|---|---|---|
| `page_count` | `int` | Total number of pages in the PDF |
| `metadata` | `dict` | PDF metadata dict from pdfplumber (may be empty `{}` if the PDF has no metadata) |

---

## Validation Issue Schema

`validate_table()` returns `list[dict]`. Each dict is a validation issue.

| Field | Type | Values |
|---|---|---|
| `severity` | `str` | `"ERROR"`, `"WARNING"`, `"INFO"` |
| `check` | `str` | Name of the check that produced the issue (see table below) |
| `message` | `str` | Human-readable description of the issue, including the table label and column name where applicable |
| `rows` | `list[int]` | 0-based row indices of affected rows; empty list `[]` for table-level issues |

Issues are returned sorted by severity: ERROR first, then WARNING, then INFO.

### Validation Checks

| `check` | `severity` | Trigger |
|---|---|---|
| `empty_table` | ERROR | DataFrame has zero rows after extraction |
| `empty_headers` | ERROR | One or more column names are empty strings |
| `missing_values` | ERROR | Blank / `N/A` / null cells exceed 30% of rows in a column |
| `missing_values` | WARNING | Blank / `N/A` / null cells present but ≤ 30% of rows in a column |
| `duplicate_rows` | WARNING | Exact duplicate rows detected (by DataFrame `.duplicated()`) |
| `auto_column_names` | WARNING | Column names match the `col_N` pattern generated when the header row was not detected |
| `mixed_types` | WARNING | Column is 50–95% numeric-looking but remaining cells contain non-numeric text |

---

## `summarize_issues()` Output Schema

```python
summarize_issues(issues: list[dict]) -> dict
```

| Field | Type | Description |
|---|---|---|
| `total` | `int` | Total number of issues (errors + warnings + info) |
| `errors` | `int` | Number of ERROR-severity issues |
| `warnings` | `int` | Number of WARNING-severity issues |
| `passed` | `bool` | `True` only when `total == 0` (zero errors, zero warnings, zero info) |

---

## Cleaning Pipeline Behavior

`clean_dataframe()` applies five steps in order. Each step is a pure function that does not mutate the input DataFrame.

| Step | Function | Input behavior → Output behavior |
|---|---|---|
| 1 | `strip_cells()` | `"  value  "` → `"value"` ; `None` → `""` |
| 2 | `remove_empty_rows()` | Rows where all cells are empty strings or whitespace are dropped; index is reset |
| 3 | `remove_duplicate_rows()` | Exact duplicate rows (by all column values) are dropped; first occurrence is kept; index is reset |
| 4 | `clean_headers()` | Column names: strip whitespace → collapse internal whitespace to `_` → remove non-alphanumeric characters → lowercase → deduplicate with `_N` suffix; empty names become `col_N` |
| 5 | `coerce_numeric_columns()` | Columns where ≥ 60% of values are numeric-looking are coerced to `float`. Handles `$1,234.56` (currency), `12.5%` (percentage), commas, negative signs. Values that fail float conversion are preserved as strings. |

### Numeric detection in `coerce_numeric_columns()`

A value is considered "numeric-looking" if it matches any of:
- `^\$?[\d,]+(\.\d{1,2})?$` — currency amounts
- `^\d+(\.\d+)?%$` — percentages
- `^-?[\d,]+(\.\d+)?$` — plain integers and floats with optional commas

Values matching `N/A`, `None`, `nan`, `-`, `—` are preserved as-is and do not count toward the numeric ratio.

---

## Export Formats

### CSV — `export_to_csv(df, output_path=None)`

Exports a single DataFrame as CSV.

| Parameter | Type | Behavior |
|---|---|---|
| `df` | `pd.DataFrame` | The DataFrame to export |
| `output_path` | `str \| Path \| None` | If `None` (default): returns `BytesIO` for Streamlit download. If a path is provided: writes to disk and returns the path string. |

CSV is produced with `index=False`. Column headers are included as the first row.

### Excel — `export_to_excel(tables, output_path=None, sheet_name_key="label")`

Exports multiple DataFrames to a single multi-sheet `.xlsx` workbook. One sheet per table.

| Parameter | Type | Behavior |
|---|---|---|
| `tables` | `list[dict]` | Each dict must have `"dataframe"` (pd.DataFrame) and a label field |
| `output_path` | `str \| Path \| None` | If `None` (default): returns `BytesIO`. If a path: writes to disk and returns path string. |
| `sheet_name_key` | `str` | Key in each dict to use as the sheet name (default: `"label"`) |

Sheet names are sanitized: characters `\ / ? * [ ] :` are replaced with `_`. Names are truncated to 31 characters per the `.xlsx` format specification.

---

## `src/__init__.py` — Public API

The following names are exported from `src` and constitute the stable public API.

| Name | Module | Description |
|---|---|---|
| `extract_tables_from_path` | extractor | Extract tables from a PDF file on disk |
| `extract_tables_from_bytes` | extractor | Extract tables from PDF bytes |
| `get_pdf_info` | extractor | Return page count and metadata for a PDF |
| `validate_table` | validator | Run all six validation checks; return sorted issue list |
| `summarize_issues` | validator | Summarize an issue list into error/warning counts and pass/fail |
| `clean_dataframe` | cleaner | Apply the full five-step cleaning pipeline |
| `clean_headers` | cleaner | Normalize column names only |
| `coerce_numeric_columns` | cleaner | Apply numeric coercion only |
| `export_to_csv` | exporter | Export a single DataFrame to CSV |
| `export_to_excel` | exporter | Export multiple DataFrames to a multi-sheet Excel workbook |
| `build_export_label` | exporter | Generate a `Page{N}_Table{M}` label string |

Internal helpers (`_extract`, `_table_to_dataframe`, `_check_*` functions, `_looks_numeric`, `_parse_cell`, `_dedup_columns`, `_safe_sheet_name`, regex constants) are not part of the public API and may change without notice.
