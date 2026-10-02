import pdfplumber
import re

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
for pg in [52, 53]:
    text = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for ln in text.splitlines() if (l := ln.strip())]
    print(f'--- Page {pg} ---')
    for l in lines:
        print(repr(l))
    print()
pdf.close()
