"""
Final breakdown: where does 1636 come from vs the 1700+ claim?
Check all section participant lists vs extracted.
"""
import sys, re
sys.path.insert(0, '.')
from src.exhibitor_extractor import extract_exhibitors, _normalise_for_dedup, _LIST_PAGE_RE
import pdfplumber

all_ex = extract_exhibitors('data/Aahar 2025 Fair Guide.pdf')
print(f"Total extracted: {len(all_ex)}")
full_profile = [e for e in all_ex if e.get('contact_person') or e.get('tel_mobile') or e.get('email')]
list_only    = [e for e in all_ex if not e.get('contact_person') and not e.get('tel_mobile') and not e.get('email')]
print(f"  Full profiles (with contact/email): {len(full_profile)}")
print(f"  List-only stubs (name+stall only):  {len(list_only)}")
print()

# Count entries per section participant list
pdf = pdfplumber.open('data/Aahar 2025 Fair Guide.pdf')
ENTRY_RE = re.compile(r'^(\d+)\s+.+', re.IGNORECASE)

sections = {
    'Alphabetical (main)': range(59, 112),
    'FHSAI':               range(619, 625),
}

total_list_entries = 0
for name, page_range in sections.items():
    count = 0
    max_sno = 0
    for i in page_range:
        if i >= len(pdf.pages): break
        raw = pdf.pages[i].extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
        if not _LIST_PAGE_RE.search(raw): continue
        for line in raw.splitlines():
            m = ENTRY_RE.match(line.strip())
            if m:
                count += 1
                max_sno = max(max_sno, int(m.group(1)))
    total_list_entries += count
    print(f"  {name}: {count} rows (max S.No={max_sno})")

print(f"  Total list entries: {total_list_entries}")
print()

# The 1700+ claim: check what sections don't have full profiles
# (FHSAI 130 + overseas + sub-associations all feed into one pool)
# Key question: how many UNIQUE companies total across all sources?
print("Unique companies in extracted output:", len({_normalise_for_dedup(e['company_name']) for e in all_ex}))

# Also check: are there profile pages that produce 0 exhibitors?
from src.exhibitor_extractor import _parse_format_b, _detect_format, _should_skip
zero_output_pages = []
for i, page in enumerate(pdf.pages):
    pg = i + 1
    raw = page.extract_text(x_tolerance=3, y_tolerance=3, layout=False) or ''
    if not raw.strip() or _should_skip(raw) or _LIST_PAGE_RE.search(raw):
        continue
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    fmt = _detect_format(lines)
    if fmt == 'B':
        results = _parse_format_b(lines, pg)
        import re as _re
        expected = len(_re.compile(r'HALL\s*:', _re.IGNORECASE).findall(raw))
        if len(results) < expected:
            zero_output_pages.append((pg, expected, len(results)))

print(f"\nProfile-B pages where extracted < expected HALL: count: {len(zero_output_pages)}")
for pg, exp, got in zero_output_pages[:10]:
    print(f"  pg {pg}: expected={exp} got={got}")

pdf.close()
