import pdfplumber, re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
print(f'Total pages: {len(pdf.pages)}')

table_pages = []
for i, page in enumerate(pdf.pages):
    text = page.extract_text() or ''
    if re.search(r'\b(S\.?NO\.?|STALL|HALL)\b', text, re.IGNORECASE):
        table_pages.append(i+1)

print(f'Total pages with STALL/HALL/S.NO: {len(table_pages)}')
print('Pages:', table_pages)
pdf.close()
