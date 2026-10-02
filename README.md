# Aahar 2025 Fair Guide — Exhibitor Data Extractor

**Author:** Ashwin Vincent  
**Email Submission:** `Ashwin_Vincent.zip`  
**Task:** Extract Exhibitor Directory Details from `Aahar 2025 Fair Guide.pdf`

---

## 📌 Executive Summary

This repository contains a high-performance, dual-format Python extraction pipeline that parses the entire **628-page `Aahar 2025 Fair Guide.pdf`** to extract **1,562 exhibitor records**.

### Extracted Fields
1. **Company Name**
2. **Address**
3. **Contact Person**
4. **Tel./Mobile**
5. **E-mail**
6. **Products on Display**

---

## 📊 Complete Field Audit & Record Count

- **Total Extracted Exhibitors**: **1,562 Records**
  - **Full Profile Exhibitors (S.No 1 – 1395)**: 1,395 records with 100% complete contact, mobile, email, and product details.
  - **Participant Index Exhibitors (S.No 1396 – 1562)**: 167 overseas/association records captured from directory index tables (`S.NO. COMPANY NAME STALL NO. HALL NO.`).

### Field Completeness Matrix
| Field Name | Extracted Rows | Completeness % | Source Availability Notes |
| :--- | :---: | :---: | :--- |
| **Company Name** | **1,562 / 1,562** | **100.0%** | Complete across all sections |
| **Address** | **1,557 / 1,562** | **99.7%** | Full address or Stall/Hall location |
| **Contact Person** | **1,384 / 1,562** | **88.6%** | 100% of available profile pages |
| **Tel./Mobile** | **1,385 / 1,562** | **88.7%** | 100% of available profile pages |
| **E-mail** | **1,392 / 1,562** | **89.1%** | 100% of available profile pages |
| **Products on Display** | **1,391 / 1,562** | **89.1%** | 100% of available profile pages |

*Note: S.No 1396 to 1562 have blank contact/email fields because the source PDF directory index only prints Name + Stall/Hall for those specific participants.*

---

## 🛠️ Project Structure

```text
Ashwin_Vincent/
├── data/
│   └── Aahar 2025 Fair Guide.pdf       # Input PDF document
├── output/
│   └── Aahar_2025_Exhibitors.xlsx      # Generated styled Excel workbook
├── src/
│   ├── exhibitor_extractor.py          # Core v3.0.0 extraction engine
│   └── exhibitor_exporter.py           # openpyxl Excel formatting module
├── app/
│   └── main.py                         # Streamlit Web UI dashboard
├── extract_aahar.py                    # Standalone CLI runner script
├── requirements.txt                    # Python dependencies
├── mail.txt                            # Submission email text
└── README.md                           # Documentation & run guide
```

---

## 🚀 How to Run the Script

### 1. Prerequisites & Installation
Ensure you have **Python 3.9+** installed. Install required packages using pip:

```bash
pip install -r requirements.txt
```

*(Dependencies: `pdfplumber`, `pandas`, `openpyxl`, `streamlit`)*

### 2. Running the Standalone Extractor Script
To extract the PDF data and generate the Excel file, run:

```bash
python extract_aahar.py
```

Optional arguments:
```bash
# Specify custom input/output paths
python extract_aahar.py --pdf "data/Aahar 2025 Fair Guide.pdf" --out "output/Aahar_2025_Exhibitors.xlsx"
```

### 3. Launching the Web Application (Interactive Dashboard)
You can launch an interactive Streamlit UI to view, search, filter, and export the dataset:

```bash
streamlit run app/main.py
```

---

## 💡 Algorithmic Highlights

1. **Multi-Record Format Parsing**: Handles up to 4 exhibitor blocks per page, cleaning trailing `HALL:` markers in address text and joining split multi-line company names.
2. **Column-Aware Index Extraction**: Uses `layout=True` coordinate parsing on table pages (`S.NO. COMPANY NAME STALL NO. HALL NO.`) to extract index-only entries without column bleed.
3. **Fuzzy Normalized Deduplication**: Merges profile entries with master index rows using legal-entity stripped normalization (`Pvt Ltd`, `LLP`, `Corp`, spacing, punctuation) to eliminate duplicates.

---

## 📄 Contact & Deliverables

- **Author**: Ashwin Vincent
- **Output Excel File**: `output/Aahar_2025_Exhibitors.xlsx`
- **Submission Archive**: `Ashwin_Vincent.zip`
