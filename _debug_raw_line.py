import pdfplumber, re
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# Check page 59 for the problematic entries
raw = pdf.pages[58].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
lines = [l.strip() for l in raw.splitlines() if l.strip()]
for l in lines:
    if 'GOURMET' in l.upper() or 'A.K.' in l.upper():
        print(repr(l))

print()
# Also check ASHOK HOTELWARE
raw2 = pdf.pages[618].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
lines2 = [l.strip() for l in raw2.splitlines() if l.strip()]
for l in lines2:
    if 'ASHOK' in l.upper() or 'ZION' in l.upper():
        print(repr(l))

# Also check the raw extract with layout=True for comparison
raw3 = pdf.pages[58].extract_text(x_tolerance=3, y_tolerance=3, layout=True) or ''
print("\n--- Page 59 with layout=True (first 20 lines) ---")
for l in raw3.splitlines()[:20]:
    print(repr(l))

pdf.close()
