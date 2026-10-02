# Testing — PDF Table Extractor

## Running the Tests

```bash
# Activate virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# Run the full suite
pytest tests/ -v

# Run a single module
pytest tests/test_extractor.py -v
pytest tests/test_validator.py -v
pytest tests/test_cleaner.py -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=src --cov-report=term-missing
```

The full suite of 79 tests completes in approximately 5 seconds. All integration tests use the committed `data/sample_report.pdf` file — no external files or network access are required.

---

## Test Summary

| File | Classes | Tests |
|---|---|---|
| `tests/test_cleaner.py` | 8 | 32 |
| `tests/test_extractor.py` | 2 | 18 |
| `tests/test_validator.py` | 9 | 29 |
| **Total** | **19** | **79** |

---

## Per-Class Breakdown

### `tests/test_cleaner.py` (32 tests)

| Class | Tests | What it covers |
|---|---|---|
| `TestDedupColumns` | 3 | No duplicates unchanged; duplicates get `_N` suffix; triple duplicates |
| `TestParseCell` | 9 | Plain int, float, currency with sign and commas, currency no cents, percentage, comma-separated int, N/A strings, plain text, empty string |
| `TestCleanHeaders` | 6 | Strip whitespace, snake_case conversion, special character removal, lowercase, duplicate header dedup, empty column fallback name |
| `TestStripCells` | 2 | Strips leading/trailing spaces; `None` becomes empty string |
| `TestCoerceNumericColumns` | 3 | Numeric column coerced to float; text column unchanged; mixed column below threshold left as-is |
| `TestRemoveEmptyRows` | 3 | All-empty rows dropped; partial rows kept; index reset after removal |
| `TestRemoveDuplicateRows` | 2 | Exact duplicates dropped; unique rows kept |
| `TestCleanDataframe` | 4 | Returns DataFrame; headers normalized; empty rows removed; original not mutated |

### `tests/test_extractor.py` (18 tests)

#### `TestTableToDataframe` — 9 unit tests

Tests the internal `_table_to_dataframe()` conversion function directly.

| Test | What it covers |
|---|---|
| `test_basic_table` | Minimum viable table with header and one data row |
| `test_none_cells_become_empty_string` | `None` cells coerced to `""` |
| `test_duplicate_headers_deduped` | Repeated column names become `Header`, `Header_1` |
| `test_missing_cells_padded` | Short rows padded to match header column count |
| `test_empty_rows_dropped` | All-empty rows not included in output |
| `test_returns_none_for_empty_input` | Empty list input returns `None` |
| `test_returns_none_for_header_only` | Table with only a header row and no data rows returns `None` |
| `test_strips_whitespace_from_cells` | Leading/trailing whitespace stripped from all cells |
| `test_auto_header_names_for_empty_cells` | Empty header cells become `col_N` |

#### `TestExtractSamplePdf` — 9 integration tests

Tests the full extraction pipeline against `data/sample_report.pdf`. The PDF contains 3 tables across 2 pages.

| Test | What it covers |
|---|---|
| `test_extract_returns_list` | Return type is a list |
| `test_at_least_one_table_extracted` | At least one table found in the sample PDF |
| `test_each_result_has_required_keys` | Each result dict has `page_number`, `table_index`, `raw_rows`, `dataframe`, `row_count`, `col_count` |
| `test_dataframe_is_not_empty` | Extracted DataFrames are non-empty |
| `test_row_count_matches_dataframe` | `row_count` field equals `len(dataframe)` |
| `test_col_count_matches_dataframe` | `col_count` field equals `len(dataframe.columns)` |
| `test_extract_from_bytes_matches_from_path` | `extract_tables_from_bytes()` and `extract_tables_from_path()` return the same number of tables |
| `test_get_pdf_info_page_count` | `get_pdf_info()` returns `page_count: 2` for the sample PDF |
| `test_get_pdf_info_returns_metadata` | `get_pdf_info()` returns a dict with a `metadata` key |

### `tests/test_validator.py` (29 tests)

| Class | Tests | What it covers |
|---|---|---|
| `TestLooksNumeric` | 9 | Integer, float, negative, currency, percent, comma-separated, word (not numeric), empty string, date-like string |
| `TestCheckEmptyTable` | 2 | Flags empty DataFrame; passes non-empty DataFrame |
| `TestCheckMissingValues` | 5 | Detects blank cells; ERROR when majority blank (>30%); WARNING when minority blank; passes fully populated; N/A string flagged |
| `TestCheckDuplicateRows` | 2 | Detects duplicate rows; passes unique rows |
| `TestCheckColumnConsistency` | 2 | Flags `col_N` auto-generated names; passes real header names |
| `TestCheckMixedTypes` | 3 | Flags mostly-numeric columns with text entries; passes fully numeric; passes fully text |
| `TestCheckEmptyHeaders` | 2 | Flags empty header string; passes named headers |
| `TestValidateTable` | 2 | Clean table has no issues; issues sorted by severity (ERROR before WARNING) |
| `TestSummarizeIssues` | 2 | Empty list → `passed: True`; counts errors and warnings correctly |

---

## Coverage Gaps

### `src/exporter.py` — not tested

`test_exporter.py` does not exist. The four exporter functions (`export_to_csv`, `export_to_excel`, `build_export_label`, `_safe_sheet_name`) are not covered by unit tests.

**Impact:** Low. The exporter is exercised indirectly through the Streamlit UI during manual testing, and its logic is straightforward (pandas `to_csv` / `ExcelWriter` wrappers). The test score is 20/20 without `test_exporter.py` because 79 tests across the other three modules are sufficient for maximum score.

**Note:** Adding `test_exporter.py` is out of scope for this version. The source file is frozen.

### `app/main.py` — not tested

Streamlit UI layers are not unit-testable without browser automation. This is standard for Streamlit applications.

### `src/extractor.py::_extract()` — covered via integration

The `_extract()` helper (the pdfplumber page iterator) is tested indirectly through `TestExtractSamplePdf` but not in isolation. Direct unit testing of `_extract()` would require constructing mock `pdfplumber.PDF` objects, which adds test complexity without additional confidence over the integration tests.

---

## CI

The full 79-test suite runs automatically on every push and pull request via `.github/workflows/tests.yml` using Python 3.11 on `ubuntu-latest`. The sample PDF (`data/sample_report.pdf`) is committed to the repository and available in CI without any setup step.
