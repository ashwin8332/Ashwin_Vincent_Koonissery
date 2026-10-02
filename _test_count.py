import sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors

exhibitors = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
print(f'Total extracted: {len(exhibitors)}')
# Show first 5 and last 5
for ex in exhibitors[:5]:
    print(ex['company_name'][:60])
print('...')
for ex in exhibitors[-5:]:
    print(ex['company_name'][:60])
