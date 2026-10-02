"""
Find exactly where the ~200 gap between extracted (1561) and claimed (1700+) comes from.
Cross-reference the alphabetical participant list (1465 entries) vs extracted profiles.
"""
import sys, re
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors, _normalise_for_dedup, _parse_format_c, _LIST_PAGE_RE
import pdfplumber

# --- Step 1: extract all profiles + list stubs ---
print("Extracting all exhibitors...")
all_ex = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
print(f"Total extracted: {len(all_ex)}")

# --- Step 2: parse alphabetical list to get the OFFICIAL 1465 entries ---
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# Raw list parse — preserve original line for inspection
LIST_HEADER = re.compile(r'S\.?NO\.?\s+COMPANY\s+NAME', re.IGNORECASE)
ENTRY_RE    = re.compile(r'^(\d+)\s+(.+)', re.IGNORECASE)

official_list = []   # (sno, raw_rest, page)
for i in range(58, 112):   # pages 59-111 = alphabetical list
    raw = pdf.pages[i].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if not LIST_HEADER.search(raw):
        continue
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    for line in lines:
        m = ENTRY_RE.match(line)
        if m:
            sno  = int(m.group(1))
            rest = m.group(2).strip()
            # First word-blob before 2+ spaces is company name
            parts = re.split(r'\s{2,}', rest)
            name = parts[0].strip()
            official_list.append((sno, name, i+1))

pdf.close()
print(f"\nOfficial alphabetical list entries: {len(official_list)}")
print(f"Max S.No: {max(s for s,_,_ in official_list)}")

# --- Step 3: find which official entries are missing from extracted ---
extracted_norms = {_normalise_for_dedup(e['company_name']) for e in all_ex}

missing = []
for sno, name, pg in official_list:
    norm = _normalise_for_dedup(name)
    if not norm:
        continue
    # exact
    if norm in extracted_norms:
        continue
    # substring
    found = any(len(norm) >= 6 and (norm in en or en in norm) for en in extracted_norms)
    if not found:
        missing.append((sno, name, pg))

print(f"\nEntries in official list NOT in extracted output: {len(missing)}")
print()
print("First 40 missing:")
for sno, name, pg in missing[:40]:
    print(f"  #{sno:4d}  {name[:65]}  (list-pg {pg})")

print()
print(f"Last 20 missing:")
for sno, name, pg in missing[-20:]:
    print(f"  #{sno:4d}  {name[:65]}  (list-pg {pg})")
