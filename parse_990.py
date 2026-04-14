import xml.etree.ElementTree as ET
import pandas as pd
import os
import glob
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed

NS = 'http://www.irs.gov/efile'
MAX_CSV_BYTES = 50 * 1024 * 1024  # 50 MB
def ns(tag): return f'{{{NS}}}{tag}'

def get_text(el, *path):
    """Navigate a path of tags from an element, return text or None."""
    cur = el
    for tag in path:
        if cur is None: return None
        cur = cur.find(ns(tag))
    return cur.text if cur is not None else None

def to_float(val):
    try: return float(val)
    except: return None

def parse_990(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"Failed: {filepath}: {e}")
        return None

    header = root.find(ns('ReturnHeader'))
    filer  = header.find(ns('Filer')) if header else None
    addr   = filer.find(ns('USAddress')) if filer else None
    irs990 = root.find(f'.//{ns("IRS990")}')

    def h(tag):  return get_text(header, tag)
    def f(tag):  return get_text(filer, tag)  if filer  else None
    def a(tag):  return get_text(addr, tag)   if addr   else None
    def g(tag):  # search anywhere in IRS990 section
        if irs990 is None: return None
        el = irs990.find(f'.//{ns(tag)}')
        return el.text if el is not None else None

    record = {}

    # --- Identity ---
    record['EIN']         = f('EIN')
    record['OrgName']     = get_text(filer, 'BusinessName', 'BusinessNameLine1Txt') if filer else None
    record['State']       = a('StateAbbreviationCd')
    record['City']        = a('CityNm')
    record['ZIP']         = a('ZIPCd')
    record['TaxYear']     = h('TaxYr')
    record['TaxPeriodEnd']= h('TaxPeriodEndDt')
    record['FormType']    = h('ReturnTypeCd')
    record['FormationYr'] = g('FormationYr')
    record['Mission']     = g('ActivityOrMissionDesc')
    record['Employees']   = to_float(g('TotalEmployeeCnt'))
    record['Volunteers']  = to_float(g('TotalVolunteersCnt'))

    # --- Revenue ---
    record['GrossReceipts']         = to_float(g('GrossReceiptsAmt'))
    record['TotalRevenueCY']        = to_float(g('CYTotalRevenueAmt'))
    record['TotalRevenuePY']        = to_float(g('PYTotalRevenueAmt'))
    record['ContributionsGrantsCY'] = to_float(g('CYContributionsGrantsAmt'))
    record['ContributionsGrantsPY'] = to_float(g('PYContributionsGrantsAmt'))
    record['ProgramServiceRevCY']   = to_float(g('CYProgramServiceRevenueAmt'))
    record['ProgramServiceRevPY']   = to_float(g('PYProgramServiceRevenueAmt'))
    record['InvestmentIncomeCY']    = to_float(g('CYInvestmentIncomeAmt'))
    record['OtherRevenueCY']        = to_float(g('CYOtherRevenueAmt'))
    record['GovernmentGrantsAmt']   = to_float(g('GovernmentGrantsAmt'))

    # --- Expenses ---
    record['TotalExpensesCY']    = to_float(g('CYTotalExpensesAmt'))
    record['TotalExpensesPY']    = to_float(g('PYTotalExpensesAmt'))
    record['SalariesCY']         = to_float(g('CYSalariesCompEmpBnftPaidAmt'))
    record['FundraisingExpCY']   = to_float(g('CYTotalFundraisingExpenseAmt'))
    record['ProgramSvcExpenses'] = to_float(g('TotalProgramServiceExpensesAmt'))

    # --- Net ---
    record['NetRevenueCY'] = to_float(g('CYRevenuesLessExpensesAmt'))
    record['NetRevenuePY'] = to_float(g('PYRevenuesLessExpensesAmt'))

    # --- Balance Sheet ---
    record['TotalAssetsEOY']      = to_float(g('TotalAssetsEOYAmt'))
    record['TotalAssetsBOY']      = to_float(g('TotalAssetsBOYAmt'))
    record['TotalLiabilitiesEOY'] = to_float(g('TotalLiabilitiesEOYAmt'))
    record['TotalLiabilitiesBOY'] = to_float(g('TotalLiabilitiesBOYAmt'))
    record['NetAssetsEOY']        = to_float(g('NetAssetsOrFundBalancesEOYAmt'))
    record['NetAssetsBOY']        = to_float(g('NetAssetsOrFundBalancesBOYAmt'))

    # --- Derived Metrics ---
    # Commented out — computed separately in a downstream enrichment step.

    # cy_rev  = record['TotalRevenueCY']
    # cy_exp  = record['TotalExpensesCY']
    # py_rev  = record['TotalRevenuePY']
    # grants  = record['ContributionsGrantsCY'] or 0
    # prog_rev= record['ProgramServiceRevCY'] or 0
    # invest  = record['InvestmentIncomeCY'] or 0
    # other   = record['OtherRevenueCY'] or 0
    # total   = grants + prog_rev + invest + other

    # record['RevenueGrowthPct'] = (cy_rev - py_rev) / abs(py_rev) if (cy_rev and py_rev and py_rev != 0) else None

    # prog_exp = record['ProgramSvcExpenses']
    # record['ProgramExpenseRatio'] = prog_exp / cy_exp if (prog_exp and cy_exp and cy_exp != 0) else None

    # if total > 0:
    #     record['GrantDependencyPct']   = grants / total
    #     record['ProgramRevenuePct']    = prog_rev / total
    #     record['InvestmentRevenuePct'] = invest / total
    # else:
    #     record['GrantDependencyPct'] = record['ProgramRevenuePct'] = record['InvestmentRevenuePct'] = None

    # net_assets = record['NetAssetsEOY']
    # record['OperatingReserveMonths'] = (net_assets / cy_exp * 12) if (net_assets and cy_exp and cy_exp > 0) else None

    # assets = record['TotalAssetsEOY']
    # liab   = record['TotalLiabilitiesEOY']
    # record['DebtRatio']     = liab / assets if (assets and liab and assets > 0) else None
    # record['SurplusMargin'] = (record['NetRevenueCY'] or 0) / cy_rev if (cy_rev and cy_rev > 0) else None

    # try:
    #     record['OrgAge'] = int(record['TaxYear']) - int(record['FormationYr'])
    # except:
    #     record['OrgAge'] = None

    # # Shock simulation: 30% grant loss
    # shock = grants * 0.30
    # post_shock_net = (record['NetRevenueCY'] or 0) - shock
    # record['Shock30PctGrantLoss']  = -shock
    # record['PostShockNetRevenue']  = post_shock_net
    # record['PostShockSurplus']     = 'Surplus' if post_shock_net >= 0 else 'Deficit'

    # # Resilience score (0-100 composite)
    # score = 0
    # if record['OperatingReserveMonths']:
    #     score += min(record['OperatingReserveMonths'] / 12 * 30, 30)  # max 30pts
    # if record['GrantDependencyPct'] is not None:
    #     score += (1 - record['GrantDependencyPct']) * 20              # max 20pts
    # if record['ProgramExpenseRatio']:
    #     score += record['ProgramExpenseRatio'] * 20                   # max 20pts
    # if record['SurplusMargin'] is not None:
    #     score += max(min(record['SurplusMargin'] * 100, 15), 0)       # max 15pts
    # if record['DebtRatio'] is not None:
    #     score += max((1 - record['DebtRatio']) * 15, 0)               # max 15pts
    # record['ResilienceScore'] = round(score, 1)

    record['SourceFile'] = os.path.basename(filepath)
    return record


# ---------------------------------------------------------------------------
# NTEE enrichment helpers
# ---------------------------------------------------------------------------

def load_teos_lookup(base_dir):
    """Load TEOS NTEE_CD data for EIN lookups. Returns None if unavailable."""
    teos_dir = os.path.join(base_dir, 'TEOS IRS Data')
    if not os.path.isdir(teos_dir):
        print("[NTEE] TEOS IRS Data folder not found — skipping NTEE enrichment.")
        return None
    teos_csvs = [
        os.path.join(teos_dir, f)
        for f in os.listdir(teos_dir)
        if f.endswith('.csv') and os.path.isfile(os.path.join(teos_dir, f))
    ]
    if not teos_csvs:
        print("[NTEE] No TEOS CSV files found — skipping NTEE enrichment.")
        return None
    teos_df = pd.concat(
        [pd.read_csv(f, usecols=['EIN', 'NTEE_CD'], dtype=str) for f in teos_csvs],
        ignore_index=True,
    ).drop_duplicates(subset='EIN')
    teos_df['EIN'] = teos_df['EIN'].str.strip()
    print(f"[NTEE] Loaded {len(teos_df)} orgs from TEOS")
    return teos_df


def enrich_ntee(df, teos_df):
    """Left-join NTEE_CD onto df via EIN. No-op if teos_df is None."""
    if teos_df is None:
        return df
    df['_EIN_key'] = df['EIN'].str.replace('-', '', regex=False).str.strip()
    df = df.merge(
        teos_df.rename(columns={'EIN': '_EIN_key'}),
        on='_EIN_key', how='left',
    )
    df.drop(columns=['_EIN_key'], inplace=True)
    matched = df['NTEE_CD'].notna().sum()
    print(f"    NTEE: {matched}/{len(df)} orgs matched")
    return df


# ---------------------------------------------------------------------------
# CSV writer — splits into ≤50 MB chunks when needed
# ---------------------------------------------------------------------------

def write_csv_split(df, output_dir, base_name, max_bytes=MAX_CSV_BYTES):
    """Write df to output_dir/base_name.csv, splitting if the file exceeds max_bytes."""
    # Write to a temp file to get the real on-disk size before committing
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.csv', dir=output_dir)
    os.close(tmp_fd)
    df.to_csv(tmp_path, index=False)
    total_size = os.path.getsize(tmp_path)

    if total_size <= max_bytes:
        out = os.path.join(output_dir, f'{base_name}.csv')
        os.replace(tmp_path, out)
        print(f"  -> {base_name}.csv ({total_size / 1024 / 1024:.1f} MB, {len(df)} rows)")
    else:
        os.unlink(tmp_path)
        total_rows = len(df)
        rows_per_chunk = max(1, int(total_rows * max_bytes / total_size))
        chunk_num = 1
        start = 0
        while start < total_rows:
            chunk = df.iloc[start:start + rows_per_chunk]
            out = os.path.join(output_dir, f'{base_name}_{chunk_num}.csv')
            chunk.to_csv(out, index=False)
            actual_size = os.path.getsize(out)
            print(f"  -> {base_name}_{chunk_num}.csv ({actual_size / 1024 / 1024:.1f} MB, {len(chunk)} rows)")
            start += rows_per_chunk
            chunk_num += 1


# ---------------------------------------------------------------------------
# Batch runner — parses all XML folders under data/ and writes CSV(s)
# per folder into data/data_csv/, with NTEE_CD merged in and auto-splitting
# at 50 MB.
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    base_dir   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    output_dir = os.path.join(base_dir, 'data_csv')
    os.makedirs(output_dir, exist_ok=True)

    teos_df = load_teos_lookup(base_dir)

    # Find every sub-folder that contains XML files (e.g. 2019_990, 2020_990 …)
    xml_folders = sorted([
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d != 'data_csv'
    ])

    if not xml_folders:
        print("No XML folders found under data/. Nothing to do.")
    else:
        for folder_name in xml_folders:
            folder_path = os.path.join(base_dir, folder_name)
            xml_files   = glob.glob(os.path.join(folder_path, '**', '*.xml'), recursive=True)

            if not xml_files:
                print(f"  [{folder_name}] No XML files found, skipping.")
                continue

            workers = min(os.cpu_count() or 4, 8)
            print(f"\n[{folder_name}] Parsing {len(xml_files)} files using {workers} workers…")
            records = []
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(parse_990, f): f for f in xml_files}
                for i, future in enumerate(as_completed(futures), 1):
                    result = future.result()
                    if result:
                        records.append(result)
                    if i % 1000 == 0:
                        print(f"    [{folder_name}] {i}/{len(xml_files)} files processed…")

            if not records:
                print(f"  [{folder_name}] No valid records extracted, skipping.")
                continue

            df = pd.DataFrame(records)
            df = enrich_ntee(df, teos_df)
            write_csv_split(df, output_dir, folder_name)

    print("\nDone.")
