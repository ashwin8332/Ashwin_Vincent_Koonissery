import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import _should_skip, _detect_format, _parse_format_b, _parse_format_a
import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
HALL_RE = re.compile(r'HALL\s*:', re.IGNORECASE)
FIELD_RE = re.compile(r'(Address|Contact\s+Person|Tel\./|E-?mail|Products?\s+on\s+Display)\s*[:\-]', re.IGNORECASE)

total_expected = 0
total_got = 0
under_pages = []

for i in range(len(pdf.pages)):
    text = pdf.pages[i].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if not text.strip() or _should_skip(text):
        continue

    has_hall = bool(HALL_RE.search(text))
    has_field = bool(FIELD_RE.search(text))
    if not has_hall and not has_field:
        continue

    lines = [l.strip() for ln in text.splitlines() if (l := ln.strip())]
    fmt = _detect_format(lines)
    expected = len(HALL_RE.findall(text))
    if expected == 0 and has_field:
        expected = 1

    total_expected += expected

    if fmt == 'B':
        got = len(_parse_format_b(lines, i+1))
    elif fmt == 'A':
        got = len(_parse_format_a(lines, i+1))
    else:
        got = 0

    total_got += got
    if got < expected:
        diff = expected - got
        under_pages.append((i+1, expected, got, diff, fmt))

print(f'Total expected: {total_expected}')
print(f'Total extracted: {total_got}')
print(f'Total missed: {total_expected - total_got}')
print()
print(f'Pages under-extracting: {len(under_pages)}')
for pg, exp, got, diff, fmt in under_pages[:30]:
    print(f'  pg{pg:4d} fmt={fmt} expected={exp} got={got} missed={diff}')

pdf.close()
