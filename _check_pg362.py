import pdfplumber
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
for pg in [362, 363, 525, 526]:
    raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    print(f'=== Page {pg} ===')
    for line in raw.splitlines():
        print(repr(line))
    print()
pdf.close()
