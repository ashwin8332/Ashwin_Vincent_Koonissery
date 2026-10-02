"""
Check whether any of the 7 missing entries DO exist in the profiles under a different name form.
Also check what the continuation lines produce after fixing.
"""
import sys, re
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors, _normalise_for_dedup
import pdfplumber

all_ex = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
print(f"Total: {len(all_ex)}")

# search for partial matches on the 7 missing
queries = [
    "CROWN COFFEE",
    "DREAMSPAN",
    "GULAB OIL",
    "NUTRIVATIVE",
    "SRI PANCHMUKHI",
    "US HIGHBUSH",
    "WHITE WARBLER",
]

for q in queries:
    matches = [e for e in all_ex if q.upper() in e['company_name'].upper()]
    if matches:
        for e in matches:
            print(f"  FOUND '{q}' as: {e['company_name']}")
    else:
        print(f"  MISSING: '{q}'")

# Also check what _split_list_row produces for these raw lines
print()
from src.exhibitor_extractor import _split_list_row
test_rows = [
    "286 CROWN COFFEE MACHINE & HH7-A-07-A HH7A",
    "339 DREAMSPAN VENTURES PVT. LTD. 06-43-A 6",
    "518 GULAB OIL AND FOOD 4F-08/A 4 FF",
    "914 NUTRIVATIVE FOODS PVT. LTD. 5F-19 G 5 FF",
    "1253 SRI PANCHMUKHI ENTERPRISES 5F-19 B1 5 FF",
    "1375 US HIGHBUSH BLUEBERRY COUNCIL 1G-10 E 1 GF",
    "1438 WHITE WARBLER 5F-37-C 5 FF",
]
print("_split_list_row results:")
for row in test_rows:
    rest = re.match(r'^\d+\s+(.+)', row).group(1)
    c, s, h = _split_list_row(rest)
    print(f"  row: {row[:55]}")
    print(f"    -> company={repr(c)} | stall={repr(s)} | hall={repr(h)}")
    print()
