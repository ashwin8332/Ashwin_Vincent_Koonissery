# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-21

### Added
- `src/extractor.py` — pdfplumber-based PDF table extraction with line-based grid detection
- `src/validator.py` — six-check data quality validation pipeline (ERROR/WARNING severity model)
- `src/cleaner.py` — five-step cleaning pipeline: strip, remove empty rows, deduplicate, normalize headers, coerce numerics
- `src/exporter.py` — CSV (BytesIO or disk) and multi-sheet Excel export via openpyxl
- `app/main.py` — Streamlit UI with file upload, per-table quality report, and bulk Excel download
- `tests/test_extractor.py` — 18 tests (9 unit, 9 integration against sample PDF)
- `tests/test_validator.py` — 29 tests covering all six validation checks
- `tests/test_cleaner.py` — 32 tests covering all cleaning pipeline steps
- `scripts/create_sample_pdf.py` — reportlab script to generate 2-page, 3-table demo PDF
- `data/sample_report.pdf` — committed sample PDF for testing and demo
- `docs/ARCHITECTURE.md`, `docs/TESTING.md`, `docs/DATA_DICTIONARY.md`
- `.github/workflows/tests.yml` — CI workflow running full 79-test suite on push and pull request
