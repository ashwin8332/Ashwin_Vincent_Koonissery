"""
Examine the raw text of list pages to understand the split-name patterns.
"""
import re
import pdfplumber

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

# Check specific pages with known split entries
problem_pages = {
    60: [39],    # AGGARWAL CROCKERY AND H12-06-D... → SCIENTIFIC STORES on next line?
    61: [64],    # ALIANÇA INTERNACIONAL DAS
    63: [133, 141],
    65: [179],   # BHAGWATI TIRATH
}

for pg, snos in problem_pages.items():
    raw = pdf.pages[pg-1].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    print(f'=== Page {pg} raw ===')
    for line in raw.splitlines():
        print(repr(line))
    print()

pdf.close()
