"""
Find all cases where list-only entries have company names that look wrong
(too short, contain stall tokens, have duplicates).
"""
import sys, re
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors, _normalise_for_dedup

exhibitors = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')

# Separate full profiles vs list-only stubs
full = [e for e in exhibitors if e.get('contact_person') or e.get('email') or e.get('tel_mobile')]
stubs = [e for e in exhibitors if not e.get('contact_person') and not e.get('email') and not e.get('tel_mobile')]

print(f'Full profiles:  {len(full)}')
print(f'List-only stubs: {len(stubs)}')
print()

# Find stubs whose name is suspiciously short (< 5 chars) or contains stall-like tokens
STALL_IN_NAME = re.compile(r'\b(H\d[A-Z0-9\-]+|\d+[A-Z]?--\d|\bHANGAR\b)', re.IGNORECASE)

bad_stubs = []
for e in stubs:
    name = e['company_name']
    if len(name) < 5:
        bad_stubs.append(('TOO_SHORT', e))
    elif STALL_IN_NAME.search(name):
        bad_stubs.append(('STALL_IN_NAME', e))

print(f'Suspicious stub entries: {len(bad_stubs)}')
for reason, e in bad_stubs:
    print(f'  [{reason}] {repr(e["company_name"][:60])} | addr: {e["address"][:40]}')

print()
# Also find duplicate-ish stubs (same normalised prefix)
seen = {}
dups = []
for e in stubs:
    norm = _normalise_for_dedup(e['company_name'])[:20]
    if norm in seen:
        dups.append((norm, seen[norm], e))
    else:
        seen[norm] = e

print(f'Near-duplicate stubs: {len(dups)}')
for norm, e1, e2 in dups[:10]:
    print(f'  key={repr(norm)}')
    print(f'    1: {repr(e1["company_name"][:55])}')
    print(f'    2: {repr(e2["company_name"][:55])}')
