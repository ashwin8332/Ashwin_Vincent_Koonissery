"""
Inspect the exact raw lines for the 7 missing entries to understand the parsing failure.
"""
import pdfplumber, re

ENTRY_RE = re.compile(r'^(\d+)\s+(.+)', re.IGNORECASE)
CONT_RE  = re.compile(r'^[A-Z]', re.IGNORECASE)   # continuation line starts with letter

target_snos = {286, 339, 518, 914, 1253, 1375, 1438}

pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')

for i in range(58, 112):   # pages 59-111
    raw = pdf.pages[i].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    for j, line in enumerate(lines):
        m = ENTRY_RE.match(line)
        if m and int(m.group(1)) in target_snos:
            sno = int(m.group(1))
            print(f"pg {i+1}  S.No {sno}:")
            print(f"  line {j}: {repr(line)}")
            # Show 2 lines before and 3 lines after for context
            for k in range(max(0, j-1), min(len(lines), j+4)):
                print(f"  line {k}: {repr(lines[k])}")
            print()

pdf.close()
