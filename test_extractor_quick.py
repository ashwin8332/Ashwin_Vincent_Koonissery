import sys
sys.path.insert(0, '.')
from src.aahar_extractor import _detect_format, _parse_format1, _parse_format2
import pdfplumber

p = 'data/Aahar 2025 Fair Guide.pdf'
with pdfplumber.open(p) as pdf:
    # Test Format-1 pages (index 20, 21)
    for i in [20, 21, 22]:
        text = pdf.pages[i].extract_text() or ''
        lines = [l.rstrip() for l in text.splitlines()]
        fmt = _detect_format(lines)
        print(f'PAGE {i+1} - Detected format: {fmt}')
        if fmt == 1:
            result = _parse_format1(lines, i+1)
        elif fmt == 2:
            result = _parse_format2(lines, i+1)
        else:
            result = []
        for ex in result:
            name = ex.get('company_name', '')
            email = ex.get('email', '')
            tel = ex.get('tel_mobile', '')
            print(f'  -> Company: {name}')
            print(f'     Email:   {email}')
            print(f'     Tel:     {tel}')
        print()

    # Test Format-2 pages (index 120, 121)
    for i in [120, 121, 149]:
        text = pdf.pages[i].extract_text() or ''
        lines = [l.rstrip() for l in text.splitlines()]
        fmt = _detect_format(lines)
        print(f'PAGE {i+1} - Detected format: {fmt}')
        if fmt == 2:
            result = _parse_format2(lines, i+1)
        elif fmt == 1:
            result = _parse_format1(lines, i+1)
        else:
            result = []
        for ex in result:
            name = ex.get('company_name', '')
            email = ex.get('email', '')
            print(f'  -> Company: {name}')
            print(f'     Email:   {email}')
        print()
