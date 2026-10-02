"""
Fast single-pass audit. Opens PDF once, categorises every page, prints summary.
"""
import sys, re
sys.path.insert(0, '.')
from src.exhibitor_extractor import (
    _should_skip, _detect_format, _LIST_PAGE_RE,
)
import pdfplumber

HALL_RE  = re.compile(r'HALL\s*:', re.IGNORECASE)
FIELD_RE = re.compile(r'(Address|Contact\s+Person|Tel\./|E-?mail|Products?\s+on\s+Display)\s*[:\-]', re.IGNORECASE)
STALL_RE = re.compile(r'STALL\s*:', re.IGNORECASE)

cats = {
    'blank': [], 'profile_b': [], 'profile_a': [],
    'list_page': [], 'skip_no_data': [], 'skip_keyword': [],
    'fixable': [],          # has HALL/field/stall but gets no format assigned
    'unclassified': [],
}

fixable_details  = []
keyword_details  = []
no_data_details  = []

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
total = len(pdf.pages)

for i, page in enumerate(pdf.pages):
    pg = i + 1
    raw = page.extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    if not lines:
        cats['blank'].append(pg); continue

    if _LIST_PAGE_RE.search(raw):
        cats['list_page'].append(pg); continue

    has_hall  = bool(HALL_RE.search(raw))
    has_field = bool(FIELD_RE.search(raw))
    has_stall = bool(STALL_RE.search(raw))
    has_data  = has_hall or has_field or has_stall

    skipped = _should_skip(raw)

    if skipped:
        if has_data:
            cats['unclassified'].append(pg)
            fixable_details.append((pg, lines[:6], len(HALL_RE.findall(raw)), len(FIELD_RE.findall(raw))))
        else:
            cats['skip_keyword'].append(pg)
            keyword_details.append((pg, lines[:4]))
        continue

    fmt = _detect_format(lines)
    if fmt == 'B':
        cats['profile_b'].append(pg)
    elif fmt == 'A':
        cats['profile_a'].append(pg)
    else:
        if has_data:
            cats['fixable'].append(pg)
            fixable_details.append((pg, lines[:6], len(HALL_RE.findall(raw)), len(FIELD_RE.findall(raw))))
        else:
            cats['skip_no_data'].append(pg)
            no_data_details.append((pg, lines[:3]))

pdf.close()

print(f'Total pages: {total}')
print()
print(f'  Profile-B  (extracted ok):         {len(cats["profile_b"]):4d}')
print(f'  Profile-A  (extracted ok):         {len(cats["profile_a"]):4d}')
print(f'  List pages (extracted ok):         {len(cats["list_page"]):4d}')
print(f'  Blank:                             {len(cats["blank"]):4d}')
print(f'  Skip – no exhibitor data:          {len(cats["skip_no_data"]):4d}')
print(f'  Skip – keyword filter:             {len(cats["skip_keyword"]):4d}')
print(f'  FIXABLE (has data, fmt=empty):     {len(cats["fixable"]):4d}  ← needs fixing')
print(f'  FIXABLE (has data, skip=True):     {len(cats["unclassified"]):4d}  ← needs fixing')
total_fixable = len(cats["fixable"]) + len(cats["unclassified"])
print(f'  Total fixable pages:               {total_fixable:4d}')
print()

if fixable_details:
    print(f'=== ALL {len(fixable_details)} FIXABLE PAGES ===')
    for pg, sample_lines, h_cnt, f_cnt in fixable_details:
        print(f'\n  pg {pg:3d}  halls={h_cnt} fields={f_cnt}')
        for l in sample_lines:
            print(f'    {repr(l[:80])}')

if keyword_details:
    print()
    print(f'=== KEYWORD-SKIPPED pages (sample 10) ===')
    for pg, sample_lines in keyword_details[:10]:
        print(f'\n  pg {pg:3d}')
        for l in sample_lines:
            print(f'    {repr(l[:70])}')
