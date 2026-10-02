import pdfplumber
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
raw = pdf.pages[361].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
print('=== Page 362 ===')
for line in raw.splitlines():
    print(repr(line))
pdf.close()
