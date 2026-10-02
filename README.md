# PDF Exhibitor Directory Extractor

Extract exhibitor contact and directory details from trade-show PDF guides and export them to a clean, formatted Excel workbook. Built and tested on the **Aahar 2025 Fair Guide** (628 pages, 1,562 exhibitors), and designed to work with other digital exhibitor guides too.

**Version:** 3.0.0 · **Author:** Ashwin Vincent · [GitHub](https://github.com/ashwin8332) · **License:** MIT

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [How to Run](#how-to-run)
- [Command-Line Options](#command-line-options)
- [Output](#output)
- [Results & Field Completeness](#results--field-completeness)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [License](#license)

---

## Features

Extracts six fields for every exhibitor:

| # | Field | Description |
|---|-------|-------------|
| 1 | Company Name | Name of the exhibiting company |
| 2 | Address | Full address, or Stall/Hall location where no address is printed |
| 3 | Contact Person | Representative listed in the guide |
| 4 | Tel./Mobile | Phone / mobile number(s) |
| 5 | E-mail | Contact e-mail address |
| 6 | Products on Display | Products or categories being exhibited |

- **Any page count:** handles PDFs from a single page to 600+ pages.
- **Auto-detects two layouts:**
  - **Format A:** single-block exhibitor profiles
  - **Format B:** multi-exhibitor pages with inline HALL/STALL headers
- **Polished Excel output:** auto-filters, custom styling, frozen header row, and a completeness summary sheet.
- **Two ways to run:** command-line scripts or an interactive Streamlit dashboard.

---

## Screenshots

### Dashboard: extraction summary and field completeness

![Dashboard showing extraction summary and field completeness](screenshot/Screenshot%202026-10-02%20143608.png)

### Searchable exhibitor table (company, address, contact, phone)

![Searchable exhibitor table, left columns](screenshot/Screenshot%202026-10-02%20144000.png)

### Searchable exhibitor table (phone, e-mail, products) and export options

![Searchable exhibitor table, right columns, with export buttons](screenshot/Screenshot%202026-10-02%20144044.png)

---

## Requirements

- **Python 3.9+**
- **pip**
- A **digital PDF with selectable text** (scanned image PDFs need OCR first, see the [FAQ](#troubleshooting--faq))
- For the Aahar demo: `Aahar 2025 Fair Guide.pdf` in the `data/` folder

| Package | Purpose |
|---------|---------|
| `pdfplumber` | Reads and parses the PDF |
| `pandas` | Builds the dataset and completeness report |
| `openpyxl` | Writes the formatted Excel file |
| `streamlit` | Optional web dashboard |
| `reportlab` | Optional, used by the sample-PDF helper script |
| `pytest` | Optional, for running tests |

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ashwin8332/upgraded-octo-waffle.git
cd upgraded-octo-waffle

# 2. (Recommended) create and activate a virtual environment
python -m venv venv

#    macOS / Linux
source venv/bin/activate
#    Windows (PowerShell)
venv\Scripts\Activate.ps1
#    Windows (Command Prompt)
venv\Scripts\activate.bat

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the extractor
python extract_exhibitors.py
```

If you only need the core packages, install them manually instead:

```bash
pip install pdfplumber pandas openpyxl
```

---

## How to Run

Run all commands from the repository root.

### Option A: Web dashboard (Streamlit)

```bash
streamlit run app/main.py
```

Open the local URL Streamlit prints (usually <http://localhost:8501>). The sidebar offers two modes:

- **Exhibitor Directory Extractor:** the main mode shown in the screenshots above
- **Generic Grid Table Extractor:** a general-purpose table extraction mode

From the dashboard you can search by company name, product, city or contact, then download the data as **Excel (.xlsx)** or **CSV (.csv)**.

### Option B: CLI on the default PDF

Uses the first PDF found in `data/`:

```bash
python extract_exhibitors.py
```

### Option C: CLI on a specific PDF

```bash
python extract_exhibitors.py --pdf "data/Aahar 2025 Fair Guide.pdf" --out "output/Aahar_2025_Exhibitors.xlsx"
```

### Option D: CLI on a PDF anywhere on your disk

```bash
# macOS / Linux
python extract_exhibitors.py --pdf "/path/to/your_guide.pdf" --out "/path/to/result.xlsx"

# Windows
python extract_exhibitors.py --pdf "C:\path\to\your_guide.pdf" --out "C:\path\to\result.xlsx"
```

### Option E: Aahar-specific runner

```bash
python extract_aahar.py
```

### Option F: Run the test suite

```bash
pytest tests/ -v
```

> **Tip:** Wrap any path that contains spaces in quotes.

---

## Command-Line Options

Both `extract_exhibitors.py` and `extract_aahar.py` accept:

| Option | Short | Description |
|--------|-------|-------------|
| `--pdf PDF_PATH` | `-p` | Path to the input PDF |
| `--out XLSX_PATH` | `-o` | Path for the generated Excel file (missing folders are created automatically) |
| `--preview N` | `-n` | Number of rows to print in the console preview (default `10`, `0` to skip) |

**Defaults**

| Script | Default input | Default output |
|--------|---------------|----------------|
| `extract_exhibitors.py` | First PDF in `data/` | `output/extracted_exhibitors.xlsx` |
| `extract_aahar.py` | `data/Aahar 2025 Fair Guide.pdf` | `output/Aahar_2025_Exhibitors.xlsx` |

Examples:

```bash
python extract_exhibitors.py --preview 20
python extract_exhibitors.py --pdf "data/Aahar 2025 Fair Guide.pdf"
python extract_aahar.py --help
```

**Exit codes for `extract_aahar.py`:** `0` success · `1` PDF not found · `2` PDF opened but no exhibitors extracted.

---

## Output

The command-line scripts print a banner, an **extraction summary** (total exhibitors, timings, file size), a per-field **completeness report**, and a **preview table** of the first records.

The Excel workbook includes:

- Auto-filters on every column
- A frozen header row
- Custom styling
- A statistical completeness summary sheet

---

## Results & Field Completeness

Running on the full 628-page Aahar 2025 guide yields **1,562 exhibitor records**:

- **S.No 1 – 1395:** full-profile exhibitors with contact details, e-mail and products
- **S.No 1396 – 1562:** 167 overseas / association participants taken from the directory index tables (`S.NO. · COMPANY NAME · STALL NO. · HALL NO.`)

| Field | Rows Filled | Completeness |
|-------|-------------|--------------|
| Company Name | 1,562 / 1,562 | 100.0% |
| Address | 1,557 / 1,562 | 99.7% |
| Contact Person | 1,384 / 1,562 | 88.6% |
| Tel./Mobile | 1,385 / 1,562 | 88.7% |
| E-mail | 1,392 / 1,562 | 89.1% |
| Products on Display | 1,391 / 1,562 | 89.1% |

> Records 1396–1562 have no contact, e-mail or product data because the source PDF only prints the company name plus Stall/Hall number for these participants.

---

## Project Structure

```
upgraded-octo-waffle/
├── extract_exhibitors.py        # Main generalized runner (works on any exhibitor PDF)
├── extract_aahar.py             # Aahar-specific runner
├── requirements.txt             # Python dependencies
├── RUN_PROJECT.txt              # Plain-text setup and run guide
├── app/
│   └── main.py                  # Streamlit dashboard
├── src/
│   ├── exhibitor_extractor.py   # Universal PDF text and field parsing engine
│   ├── exhibitor_exporter.py    # Excel workbook generation and styling
│   ├── aahar_extractor.py       # Backward-compatible Aahar extractor
│   ├── aahar_exporter.py        # Backward-compatible Aahar exporter
│   ├── extractor.py             # Generic table extraction engine
│   ├── cleaner.py               # DataFrame cleaning pipeline
│   ├── exporter.py              # Generic exporter
│   └── validator.py             # Data quality validation
├── tests/
│   ├── test_exhibitor_extractor.py
│   ├── test_extractor.py
│   ├── test_cleaner.py
│   └── test_validator.py
├── scripts/
│   └── create_sample_pdf.py     # Generates sample test PDFs
├── data/                        # Input PDFs (Aahar 2025 Fair Guide, sample_report.pdf)
├── output/                      # Generated Excel files (created automatically)
├── screenshot/                  # Dashboard screenshots used in this README
├── docs/                        # Additional documentation
├── .streamlit/                  # Streamlit configuration
├── .env.example
├── CHANGELOG.md
├── LICENSE
└── README.md
```

The underscore-prefixed scripts in the repo root (`_debug_*.py`, `_check_*.py`, etc.) are development helpers used while auditing the extraction. They are **not** needed to run the project.

---

## How It Works

1. **Layout auto-detection:** identifies single-block profiles (Format A) and multi-exhibitor pages with inline HALL/STALL headers (Format B).
2. **Multi-record page parsing:** handles up to four exhibitor blocks per page, strips trailing `HALL:` markers from addresses, and re-joins company names that wrap across lines.
3. **Column-aware index extraction:** uses `pdfplumber`'s `layout=True` coordinate parsing on the index table pages so columns don't bleed into each other.
4. **Normalized deduplication:** merges profile entries with index rows after stripping legal suffixes (`Pvt Ltd`, `LLP`, `Corp`), spacing and punctuation, so each company appears once.
5. **Excel export:** writes a styled workbook with filters, a frozen header and a completeness summary sheet.

---

## Troubleshooting & FAQ

| Problem | Fix |
|---------|-----|
| `PermissionError` when writing the output file | Close the Excel file if it is open, then re-run. |
| `ModuleNotFoundError: No module named 'pdfplumber'` (or `pandas`, `openpyxl`) | Activate your virtual environment and run `pip install -r requirements.txt`. |
| `ModuleNotFoundError: No module named 'src'` | Run the script from the repository root. |
| `[ERROR] PDF not found` | Put the PDF in `data/`, or pass its location with `--pdf`. |
| `[WARNING] No exhibitors were extracted` | Check that the PDF is a valid exhibitor guide and not corrupted or password-protected. |
| `streamlit: command not found` | Use `python -m streamlit run app/main.py`. |

**Does it work on PDFs with more or fewer pages than Aahar 2025?**
Yes. The engine iterates over all pages dynamically, so it works on 1-page, 10-page or 1000-page PDFs.

**Are scanned PDFs supported?**
No. The extractor needs digital PDFs with selectable text. For scanned image PDFs, run an OCR tool such as `ocrmypdf` first.

---

## License

This project is released under the [MIT License](LICENSE).
