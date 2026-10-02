"""
Cross-reference participant list entries against already-extracted profiles
to find truly new entries that only exist in list pages (no full profile).
"""
import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors
import pdfplumber
import re

# Step 1: Get all already-extracted exhibitors
print('Extracting full profiles...')
profiles = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
print(f'Profiles extracted: {len(profiles)}')

# Build a set of normalised company names from profiles
def normalise(name: str) -> str:
    name = name.upper().strip()
    # remove common suffixes noise
    for suffix in ['PVT LTD', 'PVT. LTD.', 'PVT.LTD.', 'PRIVATE LIMITED',
                   'PRIVATE LTD', 'LTD.', 'LTD', 'LLP', 'CO.', '& CO', 'INC.',
                   'CORPORATION', 'CORP.', 'INDIA', '(INDIA)']:
        name = name.replace(suffix, '')
    # collapse spaces and punctuation
    name = re.sub(r'[^A-Z0-9 ]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

profile_names = {normalise(p['company_name']): p for p in profiles}

print(f'Unique normalised profile names: {len(profile_names)}')

# Step 2: Parse ALL list entries
LIST_RE  = re.compile(r'S\.?No\.?\s+', re.IGNORECASE)
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# Parse entry from list line: "4  5 AM FARMS LLP  H2F-01-L  2 FF" 
# Format: NUMBER  COMPANY_NAME  STALL_NO  HALL_INFO
ENTRY_RE = re.compile(r'^(\d+)\s+(.+)', re.IGNORECASE)
STALL_RE = re.compile(
    r'^(.+?)\s{2,}(\S[\S-]*(?:-\S+)*)\s{2,}(.+)$'  # name  stall  hall
)

check_pages = list(range(59, 112)) + list(range(619, 625))
list_entries = []

for pg in check_pages:
    raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if not LIST_RE.search(raw):
        continue
    lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]
    prev_sno = None
    prev_name = None
    for line in lines:
        m = ENTRY_RE.match(line)
        if m:
            sno = int(m.group(1))
            rest = m.group(2).strip()
            # Try to split name from stall: last token after 2+ spaces OR alphanum-dash token
            parts = re.split(r'\s{2,}', rest)
            company = parts[0].strip() if parts else rest
            stall   = parts[1].strip() if len(parts) > 1 else ''
            hall    = ' '.join(parts[2:]).strip() if len(parts) > 2 else ''
            list_entries.append({'sno': sno, 'company_name': company, 'stall': stall, 'hall': hall, 'page': pg})
        elif prev_name:
            # continuation line — append to previous company name
            if list_entries and list_entries[-1]['sno'] == prev_sno:
                list_entries[-1]['company_name'] += ' ' + line
        if m:
            prev_sno = int(m.group(1))
            prev_name = True
        elif not m:
            prev_name = False

pdf.close()
print(f'Total list entries parsed: {len(list_entries)}')

# Step 3: Find list entries NOT in profiles
new_entries = []
matched = 0
for entry in list_entries:
    norm = normalise(entry['company_name'])
    found = False
    # exact
    if norm in profile_names:
        found = True
    else:
        # partial match — any profile name starts with/contains this norm
        for pname in profile_names:
            if len(norm) >= 8 and (norm in pname or pname in norm):
                found = True
                break
    if found:
        matched += 1
    else:
        new_entries.append(entry)

print(f'List entries matched to existing profiles: {matched}')
print(f'List entries with NO full profile (new): {len(new_entries)}')
print()
print('First 30 new entries (name + stall):')
for e in new_entries[:30]:
    print(f"  #{e['sno']:4d}  {e['company_name']:<55} {e['stall']}")
