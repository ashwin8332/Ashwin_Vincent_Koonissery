import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import _should_skip, _has_enough_fields, _detect_format
import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
total = len(pdf.pages)

HALL_RE  = re.compile(r'HALL\s*:',   re.IGNORECASE)
FIELD_RE = re.compile(r'(Address|Contact\s+Person|Tel\./|E-?mail|Products?\s+on\s+Display)\s*[:\-]', re.IGNORECASE)
LIST_RE  = re.compile(r'S\.?No\.?\s+', re.IGNORECASE)

categories = {
    'participant_list': [],   # has S.No. table  — name+stall only
    'section_divider':  [],   # 1-line ORGANISER pages
    'ad_or_message':    [],   # front-matter / ads
    'has_data_but_skip': [],  # skipped yet contains HALL: or field labels
    'blank':            [],
    'other':            [],
}

skipped_pages = []

for i, page in enumerate(pdf.pages):
    pg = i + 1
    raw = page.extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]

    if not lines:
        categories['blank'].append(pg)
        continue

    if _should_skip(raw):
        skipped_pages.append(pg)

for pg in skipped_pages:
    raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]
    has_hall  = bool(HALL_RE.search(raw))
    has_field = bool(FIELD_RE.search(raw))
    is_list   = bool(LIST_RE.search(raw))
    enough    = _has_enough_fields(raw)

    if has_hall or has_field:
        categories['has_data_but_skip'].append(pg)
    elif is_list:
        categories['participant_list'].append(pg)
    elif len(lines) <= 4:
        categories['section_divider'].append(pg)
    else:
        categories['other'].append(pg)

# Pages that are NOT skipped but also not profile pages (the 'other 75' from before)
not_skipped_not_profile = []
for i, page in enumerate(pdf.pages):
    pg = i + 1
    raw = page.extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]
    if not lines:
        continue
    if _should_skip(raw):
        continue
    has_hall  = bool(HALL_RE.search(raw))
    has_field = bool(FIELD_RE.search(raw))
    if not has_hall and not has_field:
        not_skipped_not_profile.append(pg)

print(f'Total pages: {total}')
print(f'Total skipped by _should_skip: {len(skipped_pages)}')
print(f'  -> has HALL:/field labels but still skipped: {len(categories["has_data_but_skip"])}  pages: {categories["has_data_but_skip"]}')
print(f'  -> participant list (S.No table):             {len(categories["participant_list"])}  first5: {categories["participant_list"][:5]}')
print(f'  -> section dividers:                          {len(categories["section_divider"])}  pages: {categories["section_divider"][:20]}')
print(f'  -> other skipped:                             {len(categories["other"])}  pages: {categories["other"][:20]}')
print()
print(f'Not-skipped but no HALL/field: {len(not_skipped_not_profile)}  first20: {not_skipped_not_profile[:20]}')

# Show content of has_data_but_skip pages
if categories['has_data_but_skip']:
    print()
    print('=== Pages with data that are being skipped ===')
    for pg in categories['has_data_but_skip']:
        raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
        lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]
        print(f'  Page {pg}:')
        for l in lines[:6]:
            print(f'    {repr(l)}')

# Sample a few 'other' skipped pages
if categories['other']:
    print()
    print('=== Sample of "other" skipped pages ===')
    for pg in categories['other'][:5]:
        raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
        lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]
        print(f'  Page {pg}:')
        for l in lines[:5]:
            print(f'    {repr(l)}')

pdf.close()
