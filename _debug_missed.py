import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import _should_skip, _detect_format, _parse_format_b, _parse_format_a
import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
HALL_RE = re.compile(r'HALL\s*:', re.IGNORECASE)

for pg in [13, 21, 22, 52, 53]:
    text = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for ln in text.splitlines() if (l := ln.strip())]
    print(f'--- Page {pg} ---')
    print(f'HALL count: {len(HALL_RE.findall(text))}')
    print(f'Should skip: {_should_skip(text)}')
    fmt = _detect_format(lines)
    print(f'Format: {fmt}')
    # show lines with HALL
    for l in lines:
        if 'HALL' in l.upper():
            print(f'  HALL line: {repr(l)}')
    print()

pdf.close()
