import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors

exhibitors = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
# Show list-only entries (those with address like "Hall: ...")
list_only = [e for e in exhibitors if e['address'].startswith('Hall:') and not e['contact_person']]
full_profile = [e for e in exhibitors if not e['address'].startswith('Hall:') or e['contact_person']]

print(f'Total: {len(exhibitors)}')
print(f'Full profiles: {len(full_profile)}')
print(f'List-only (partial data): {len(list_only)}')
print()
print('Sample list-only entries:')
for e in list_only[:15]:
    print(f"  Company: {e['company_name'][:55]}")
    print(f"  Address: {e['address']}")
    print()
