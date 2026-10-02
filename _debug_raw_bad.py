import pdfplumber, re

targets = ['ANI GLASS', 'ATALMAL', 'DECORAIDS', 'INDIGO METALWARE',
           'PUSHPA INTERNATIONAL', 'SAI SHAKTI', 'SHERALIKHAN', 'TELMAT',
           'THE TEA PLANET', 'VISHAAL NATURAL', 'MOULD INJECTION']

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# Check all list pages with layout=True
for pg in list(range(59, 112)) + list(range(619, 625)):
    raw_layout = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=True) or ''
    raw_nolay  = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''

    for t in targets:
        for line in raw_layout.splitlines():
            if t.upper() in line.upper():
                print(f'pg {pg} layout=True:  {repr(line.rstrip()[:90])}')
        for line in raw_nolay.splitlines():
            if t.upper() in line.upper():
                print(f'pg {pg} layout=False: {repr(line.strip()[:90])}')

pdf.close()
