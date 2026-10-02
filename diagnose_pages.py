import sys
sys.path.insert(0, '.')
import pdfplumber
import re

FIELD_RE = re.compile(
    r"^(Company\s+Name|Address|Contact\s+Person|Tel\.(?:/Mob(?:ile)?|/Mobile|Mobile)?|"
    r"E-?mail|Products?\s+on\s+Display)\s*[:\-]\s*(.*)$",
    re.IGNORECASE,
)

FORMAT2_COMPANY_RE = re.compile(r"^(.+?)\s+HALL\s*:\s*(.+)$", re.IGNORECASE)

def has_exhibitor_fields(text):
    count = 0
    patterns = [
        r"Address\s*[:\-]",
        r"Contact\s+Person\s*[:\-]",
        r"Tel\./",
        r"E-?mail\s*[:\-]",
        r"Products?\s+on\s+Display\s*[:\-]",
    ]
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            count += 1
    return count >= 2

p = 'data/Aahar 2025 Fair Guide.pdf'
with pdfplumber.open(p) as pdf:
    print(f'Total pages: {len(pdf.pages)}')
    fmt1_pages = []
    fmt2_pages = []
    for i in range(len(pdf.pages)):
        text = pdf.pages[i].extract_text() or ''
        if not text.strip():
            continue
        if not has_exhibitor_fields(text):
            continue
        lines = text.splitlines()
        # Check if any line is Format-2 HALL header
        is_f2 = any(FORMAT2_COMPANY_RE.match(l.strip()) for l in lines)
        if is_f2:
            fmt2_pages.append(i+1)
        else:
            fmt1_pages.append(i+1)
    
    print(f'Format-1 pages: {len(fmt1_pages)}, first few: {fmt1_pages[:10]}')
    print(f'Format-2 pages: {len(fmt2_pages)}, first few: {fmt2_pages[:10]}')
    
    # Show 3 Format-1 page samples
    if fmt1_pages:
        for pg in fmt1_pages[:3]:
            text = pdf.pages[pg-1].extract_text() or ''
            print(f'\nFORMAT-1 Page {pg}:')
            print(repr(text[:300]))
