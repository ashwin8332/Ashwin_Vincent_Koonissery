# Engineering Decisions — PDF Table Extractor

---

## ED-1: Line-based pdfplumber detection — not text/word-spacing strategy

**Decision:** `extract_tables_from_pdf()` uses `vertical_strategy="lines"` and `horizontal_strategy="lines"` with `snap_tolerance=5`, `join_tolerance=3`, and `edge_min_length=10`. These settings detect tables using the visible grid lines drawn in the PDF.

**Alternative considered:** Use pdfplumber's text/word-spacing strategy, which infers table boundaries from the spatial clustering of text characters.

**Why line-based detection was chosen:** Text-strategy detection produces false positives on multi-column prose layouts where text is evenly spaced but no table is intended. A formatted financial report with two text columns and no grid will trigger text-strategy detection; line-based detection will not. For documents with explicit table borders — the primary use case — line-based detection is deterministic and produces zero false positives. The trade-off (borderless tables and image-rendered tables are not detected) is documented in ARCHITECTURE.md and acceptable for the government procurement document use case, where table borders are standard.

---

## ED-2: BytesIO-first export — both exporters default to in-memory buffers

**Decision:** `export_to_csv()` and `export_to_excel()` return a `BytesIO` buffer when `output_path=None` (the default). They redirect to disk only when a path is explicitly supplied.

**Alternative considered:** Always write to a temporary file path, then return the path or its contents.

**Why BytesIO-first was chosen:** Streamlit's `st.download_button` requires an in-memory buffer object, not a file path. If the exporter wrote to disk by default, the Streamlit UI would need to open the file, read its bytes, close it, and clean up the temp file. The BytesIO-first design makes the UI integration code trivial — the download button receives the buffer directly. For non-Streamlit batch use, callers supply `output_path` and the exporter writes to disk as expected. The API is additive: the common path (Streamlit) requires no extra arguments.

---

## ED-3: Five-step cleaning pipeline in fixed order — pure functions, no mutation

**Decision:** `clean_dataframe()` applies five steps in order: `strip_cells()` → `remove_empty_rows()` → `remove_duplicate_rows()` → `clean_headers()` → `coerce_numeric_columns()`. Each step is a pure function that returns a new DataFrame; no step mutates its input.

**Alternative considered:** Apply cleaning steps in arbitrary order, or combine steps into a single monolithic function.

**Why fixed-order pure functions were chosen:** The order matters for correctness: stripping cells before deduplication ensures that rows differing only by padding whitespace are recognized as duplicates. Cleaning headers after validation ensures validation sees the original column names that the user sees in the PDF, not the normalized forms. Pure functions (returning `df.copy()` results rather than modifying in place) make each step independently testable — a test for `coerce_numeric_columns` can pass any DataFrame without worrying about prior cleaning state. The fixed-order design is documented in ARCHITECTURE.md; if the order is changed, the architecture documentation flags the dependency.

---

## ED-4: Header deduplication with `_N` suffix — no silent data loss

**Decision:** When `_table_to_dataframe()` detects repeated column names in an extracted table, it deduplicates by appending `_1`, `_2`, etc. (`Amount`, `Amount_1`, `Amount_2`). Duplicate names are not overwritten, and no error is raised.

**Alternative considered:** Raise an exception when duplicate headers are detected, or silently overwrite the duplicate columns.

**Why `_N` suffix was chosen:** Overwriting duplicate columns would silently discard data — if a financial table has three "Amount" columns representing different periods, overwriting would leave only one. Raising an exception would fail on a legitimate class of real-world PDFs, making the tool unusable for documents with repeating headers (common in quarterly financial reports). Appending `_N` preserves all columns and makes the deduplication visible to the user in the downloaded CSV, who can rename the columns manually with full knowledge of what was extracted.

---

## ED-5: 60% numeric threshold for column coercion in `coerce_numeric_columns()`

**Decision:** A column is coerced to float only if ≥ 60% of its non-empty values parse as numeric (after stripping `$`, commas, and `%`). Columns below this threshold are left as strings.

**Alternative considered:** Use a 50% threshold (majority-numeric), a 90% threshold (near-pure numeric), or inspect column headers for numeric keywords.

**Why 60% was chosen:** A 50% threshold risks coercing columns that are mostly categorical text with a minority of numeric-looking cells (e.g., invoice status codes like "A1", "B2"). A 90% threshold risks leaving legitimately numeric columns uncleaned when a small number of cells contain annotation strings like "N/A", "TBD", or footnote markers. The 60% threshold is a calibrated middle ground that handles the common case (a dollar-amount column with a few blank or annotated cells) while protecting against false coercion on mixed-content columns. The threshold is a named constant (`NUMERIC_THRESHOLD = 0.60`) accessible in the public API.

---

## ED-6: Sample PDF committed to the repository — CI runs integration tests without setup steps

**Decision:** `data/sample_report.pdf` is committed to the repository. The integration test class `TestExtractSamplePdf` in `tests/test_extractor.py` depends on this file being present at test time.

**Alternative considered:** Generate the sample PDF at test setup time using a fixture, or skip PDF integration tests in CI and run them only locally.

**Why the PDF is committed:** A generated fixture adds `reportlab` as a CI test dependency and adds a setup step that must succeed before any test can run. If the generation script fails (dependency update, Python version mismatch), the entire test suite becomes unrunnable. Committing the PDF eliminates that dependency chain: `git clone` followed by `pytest` runs all 79 tests immediately. The PDF is deterministic (generated once, committed, never regenerated unless the sample data schema changes), small (~10 KB), and binary — it will not produce confusing diffs.

---

*This document is a repository artifact and may be committed to the published repository.*
