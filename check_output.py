import sys
sys.path.insert(0, '.')
import pandas as pd

df = pd.read_excel(
    r'output\Aahar_2025_Exhibitors.xlsx',
    sheet_name='Exhibitor Data',
    skiprows=3,
    header=0
)

print(f'Total rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print()

# Check for "STALL" in company names
stall_in_name = df[df['Company Name'].str.contains('STALL', case=False, na=False)]
print(f'Records with STALL in Company Name: {len(stall_in_name)}')
for _, row in stall_in_name.head(5).iterrows():
    print(f'  -> {row["Company Name"]}')
print()

# Show first 10 records
print('First 10 records:')
for i, row in df.head(10).iterrows():
    cname = str(row['Company Name'])
    addr  = str(row['Address'])[:60]
    tel   = str(row['Tel./Mobile'])
    email = str(row['E-mail'])
    print(f'  [{i+1}] {cname}')
    print(f'       Addr: {addr}')
    print(f'       Tel:  {tel} | Email: {email}')
    print()
