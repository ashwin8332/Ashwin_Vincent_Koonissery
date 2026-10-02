import sys
sys.path.insert(0, '.')
from src.aahar_extractor import extract_exhibitors
from src.aahar_exporter import export_to_excel
from pathlib import Path

print("Extracting a quick sample (first 5 pages only for speed)...")

import pdfplumber
exhibitors = []
with pdfplumber.open(r'data\Aahar 2025 Fair Guide.pdf') as pdf:
    from src.aahar_extractor import _detect_format, _parse_format1, _parse_format2, _should_skip, _has_exhibitor_fields
    cnt = 0
    for i, page in enumerate(pdf.pages):
        if cnt >= 20:
            break
        text = page.extract_text() or ''
        if not text.strip():
            continue
        lower = text.lower()
        if _should_skip(lower, text):
            continue
        if not _has_exhibitor_fields(text):
            continue
        lines = [l.rstrip() for l in text.splitlines()]
        fmt = _detect_format(lines)
        if fmt == 2:
            result = _parse_format2(lines, i+1)
            exhibitors.extend(result)
            cnt += len(result)
            print(f'Page {i+1}: found {len(result)} exhibitors ({cnt} total)')

print(f'\nTotal exhibitors found: {len(exhibitors)}')

out_path = Path('output/test_output.xlsx')
out_path.parent.mkdir(exist_ok=True)
print(f'Exporting to {out_path}...')
try:
    result = export_to_excel(exhibitors, output_path=out_path)
    print(f'Export result: {result}')
    print(f'File exists: {out_path.exists()}')
    print(f'File size: {out_path.stat().st_size if out_path.exists() else "N/A"}')
except Exception as e:
    import traceback
    traceback.print_exc()
