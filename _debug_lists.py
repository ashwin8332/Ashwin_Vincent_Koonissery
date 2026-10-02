"""
Analyse the 59 participant-list pages (S.No. tables) to see:
1. Total entries
2. Whether they already appear in profile pages
3. What data is available (name + stall only vs full profile)
"""
import sys
sys.path.insert(0, '.')
import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# List pages identified: 59-111 and 619-624
LIST_RE  = re.compile(r'S\.?No\.?\s+', re.IGNORECASE)
ENTRY_RE = re.compile(r'^\d+\s+(.+?)\s{2,}(\S[\S ]+)', re.IGNORECASE)

# Also check FHSAI pages 619-624
check_pages = list(range(59, 112)) + list(range(619, 625))

all_list_entries = []
max_sno = 0

for pg in check_pages:
    raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if not LIST_RE.search(raw):
        continue
    lines = [l.strip() for ln in raw.splitlines() if (l := ln.strip())]
    section = ''
    for l in lines[:5]:
        if 'PARTICIPANTS' in l.upper() or 'EXHIBITOR' in l.upper():
            section = l
    
    for l in lines:
        m = re.match(r'^(\d+)\s+(.+)', l)
        if m:
            sno = int(m.group(1))
            rest = m.group(2).strip()
            if sno > max_sno:
                max_sno = sno
            all_list_entries.append((pg, sno, rest, section))

print(f'Total list entries found: {len(all_list_entries)}')
print(f'Max S.No: {max_sno}')
print()
print('First 10 entries:')
for pg, sno, rest, sec in all_list_entries[:10]:
    print(f'  pg{pg} #{sno}: {rest[:70]}')
print()
print('Last 10 entries:')
for pg, sno, rest, sec in all_list_entries[-10:]:
    print(f'  pg{pg} #{sno}: {rest[:70]}')

# Check FHSAI list specifically
print()
print('=== FHSAI list entries ===')
for pg, sno, rest, sec in all_list_entries:
    if pg >= 619:
        print(f'  pg{pg} #{sno}: {rest[:70]}')

pdf.close()
