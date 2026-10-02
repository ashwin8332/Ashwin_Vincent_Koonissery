import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors, _parse_format_c
import pdfplumber

# Test the parser directly on a few list pages
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

print('=== Testing Format-C on page 59 ===')
raw = pdf.pages[58].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
entries = _parse_format_c(raw, 59)
for e in entries[:15]:
    print(f"  Name: {e['company_name']:<50}  Addr: {e['address']}")

print()
print('=== Testing Format-C on page 619 (FHSAI) ===')
raw = pdf.pages[618].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
entries = _parse_format_c(raw, 619)
for e in entries[:15]:
    print(f"  Name: {e['company_name']:<50}  Addr: {e['address']}")

pdf.close()
