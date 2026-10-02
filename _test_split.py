import re, sys
sys.path.insert(0, '.')
from src.exhibitor_extractor import _split_list_row, _STALL_START_RE

tests = [
    'ANI GLASS CORPORATION 12--2-B   12',
    'INDIGO METALWARE LLP 12--02-C   12',
    'PUSHPA INTERNATIONAL 9--03-B    9',
    'DECORAIDS DECORATING H14F-11-D  14 FF',
    'THE TEA PLANET GLOBAL H5G-24-C  5 GF',
    'TELMAT MATERIALS AND H11-19-N   11',
    'VISHAAL NATURAL FOOD H4G-13-C  4 GF',
]

print('=== 2-space split analysis ===')
for t in tests:
    parts = re.split(r'\s{2,}', t.strip())
    print(f'  {t[:55]}')
    print(f'    parts={parts}')
    if len(parts) == 2:
        cand = parts[1].strip()
        tok0 = cand.split()[0] if cand.split() else ''
        print(f'    parts[1] candidate={repr(cand)}, tok0={repr(tok0)}, stall_start={bool(_STALL_START_RE.match(tok0))}')
    print()

print('=== _split_list_row results ===')
for t in tests:
    c, s, h = _split_list_row(t)
    print(f'  IN:  {t[:55]}')
    print(f'  OUT: name={repr(c[:40])} | stall={repr(s)} | hall={repr(h)}')
    print()
