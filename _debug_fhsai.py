import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
total = len(pdf.pages)

# Check pages 618-628 (FHSAI section - list only, no profiles)
print('=== FHSAI section (pg 617-628) ===')
for pg in range(617, min(629, total+1)):
    text = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for ln in text.splitlines() if (l := ln.strip())]
    print(f'--- Page {pg} ---')
    for l in lines[:8]:
        print(repr(l))
    print()

# Check the overseas section
print('=== OVERSEAS section (pg 365-420) ===')
HALL_RE = re.compile(r'HALL\s*:', re.IGNORECASE)
FIELD_RE = re.compile(r'(Address|Contact\s+Person|Tel\./|E-?mail|Products?\s+on\s+Display)\s*[:\-]', re.IGNORECASE)
for pg in range(365, 420):
    text = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if HALL_RE.search(text) or FIELD_RE.search(text):
        lines = [l.strip() for ln in text.splitlines() if (l := ln.strip())]
        halls = len(HALL_RE.findall(text))
        print(f'Page {pg}: {halls} exhibitors, first_line={lines[0][:60] if lines else ""}')

pdf.close()
