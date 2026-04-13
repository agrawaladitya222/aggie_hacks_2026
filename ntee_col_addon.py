import os
import pandas as pd

base_dir   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
data_csv   = os.path.join(base_dir, 'data_csv')
teos_dir   = os.path.join(base_dir, 'TEOS IRS Data')

# Load TEOS split CSVs (skip actual/ subfolder)
teos_csvs = [
    os.path.join(teos_dir, f)
    for f in os.listdir(teos_dir)
    if f.endswith('.csv') and os.path.isfile(os.path.join(teos_dir, f))
]

if not teos_csvs:
    raise FileNotFoundError("No TEOS CSV files found in TEOS IRS Data/")

teos_df = pd.concat(
    [pd.read_csv(f, usecols=['EIN', 'NTEE_CD'], dtype=str) for f in teos_csvs],
    ignore_index=True
).drop_duplicates(subset='EIN')
teos_df['EIN'] = teos_df['EIN'].str.strip()
print(f"Loaded TEOS: {len(teos_df)} orgs")

# Add NTEE_CD to each data_csv file
for fname in sorted(os.listdir(data_csv)):
    if not fname.endswith('.csv'):
        continue

    fpath = os.path.join(data_csv, fname)
    df = pd.read_csv(fpath, dtype=str)

    if 'EIN' not in df.columns:
        print(f"  [{fname}] No EIN column, skipping.")
        continue

    df['_EIN_key'] = df['EIN'].str.replace('-', '', regex=False).str.strip()
    df = df.merge(
        teos_df.rename(columns={'EIN': '_EIN_key'}),
        on='_EIN_key', how='left'
    )
    df.drop(columns=['_EIN_key'], inplace=True)

    matched = df['NTEE_CD'].notna().sum()
    df.to_csv(fpath, index=False)
    print(f"  [{fname}] {matched}/{len(df)} orgs matched NTEE_CD")

print("\nDone.")
