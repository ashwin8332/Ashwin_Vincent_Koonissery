import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import _should_skip, _has_enough_fields, _detect_format
import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
HALL_RE = re.compile(r'HALL\s*:', re.IGNORECASE)
FIELD_RE = re.compile(r'(Address|Contact\s+Person|Tel\./|E-?mail|Products?\s+on\s+Display)\s*[:\-]', re.IGNORECASE)

skip_count = 0
no_fmt_count = 0
ok_count = 0

for i in range(114, 630):
    if i >= len(pdf.pages):
        break
    text = pdf.pages[i].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if not text.strip():
        continue
    has_hall = bool(HALL_RE.search(text))
    has_field = bool(FIELD_RE.search(text))
    if not has_hall and not has_field:
        continue

    lines = [l.strip() for ln in text.splitlines() if (l := ln.strip())]
    skipped = _should_skip(text)
    fmt = _detect_format(lines)
    enough = _has_enough_fields(text)
    halls = len(HALL_RE.findall(text))
    first = lines[0][:60] if lines else ''

    if skipped:
        skip_count += 1
        print(f'SKIP  pg{i+1:4d}: halls={halls}, enough={enough}, first={first}')
    elif fmt == '':
        no_fmt_count += 1
        print(f'NOFMT pg{i+1:4d}: halls={halls}, enough={enough}, first={first}')
    else:
        ok_count += 1

print()
print(f'OK={ok_count}, Skipped={skip_count}, NoFormat={no_fmt_count}')
pdf.close()
