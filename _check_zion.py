import sys, re
sys.path.insert(0, '.')
from src.exhibitor_extractor import _parse_format_c
import pdfplumber

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# Find ZION in list pages
for i in range(58, 112):
    raw = pdf.pages[i].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if 'ZION' in raw.upper() or 'YAN WAL' in raw.upper():
        print(f'=== Page {i+1} ===')
        for line in raw.splitlines():
            if 'ZION' in line.upper() or 'YAN WAL' in line.upper() or 'GROUP' in line.upper():
                print(repr(line))
        print()

pdf.close()

# Also test _parse_format_c directly on a sample
from src.exhibitor_extractor import _split_list_row

# Simulate what the joined row looks like
test_rows = [
    "1461 ZION INTERANTIONAL FOOD H2F-04-B 2 FF INGREDIENTS PVT LTD",
    "1439 YAN WAL YUN CORPORATION 1G-05 A 1 GF GROUP CO., LTD",
    "39 AGGARWAL CROCKERY AND H12-06-D,H12-06-E 12 SCIENTIFIC STORES",
    "179 BHAGWATI TIRATH H5F-14-A 5 FF POLYCONTAINERS INDUSTRIES PVT. LTD.",
    "64 ALIANÇA INTERNACIONAL DAS 1G-06 A 1 GF MULHERES DO CAFÉ",
]

import re as _re
LISTROW_RE = re.compile(r'^(\d+)\s+(.+)', re.IGNORECASE)

for row in test_rows:
    m = LISTROW_RE.match(row)
    rest = m.group(2).strip()
    company, stall, hall = _split_list_row(rest)
    print(f'Input:   {rest[:75]}')
    print(f'Company: {company}')
    print(f'Stall:   {stall}')
    print(f'Hall:    {hall}')
    print()
