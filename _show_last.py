import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors

exhibitors = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
print(f'Total: {len(exhibitors)}')
print()
print('Last 20 entries (list-only appended at end):')
for e in exhibitors[-20:]:
    name = e['company_name']
    addr = e['address']
    contact = e['contact_person']
    print(f"  Name:    {name[:65]}")
    print(f"  Address: {addr[:65]}")
    print(f"  Contact: {contact[:40]}")
    print()
