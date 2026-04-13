import xml.etree.ElementTree as ET
import pandas as pd
import os
import glob

NS = 'http://www.irs.gov/efile'
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
# Batch runner — parses all XML folders under ../data/ and writes one CSV
# per folder into ../data/data_csv/
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    base_dir    = os.path.join(os.path.dirname(__file__), '..', 'data')
    output_dir  = os.path.join(base_dir, 'data_csv')
    os.makedirs(output_dir, exist_ok=True)

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
            xml_files   = glob.glob(os.path.join(folder_path, '*.xml'))

            if not xml_files:
                print(f"  [{folder_name}] No XML files found, skipping.")
                continue

            print(f"[{folder_name}] Parsing {len(xml_files)} files…")
            records = [r for r in (parse_990(f) for f in xml_files) if r]

            if not records:
                print(f"  [{folder_name}] No valid records extracted, skipping.")
                continue

            df  = pd.DataFrame(records)
            out = os.path.join(output_dir, f'{folder_name}.csv')
            df.to_csv(out, index=False)
            print(f"  [{folder_name}] {len(df)} orgs, {len(df.columns)} fields → {out}")

    print("\nDone.")
