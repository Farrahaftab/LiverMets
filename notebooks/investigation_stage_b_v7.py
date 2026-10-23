"""Dataset investigation, stage B: verification, exclusions, TNM missingness, and included-vs-excluded comparison.

Uses LIVERMET_WORK_DIR/extract_raw.parquet and investigation_rows.parquet (stage A). Writes F40-F49 to LIVERMET_OUT_DIR.
Cohort definitions are the v7 rules (notebook section 2). Patient-level data are not written to the repository.
"""
import calendar
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v7/investigation'))
OUT.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
MAXFU = 15.0

X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
R = pd.read_parquet(WORK / 'investigation_rows.parquet').reset_index(drop=True)
assert len(X) == len(R) == 29565
assert (X.SOURCE_EXCEL_ROW.values == R.SOURCE_EXCEL_ROW.values).all()
X['COUNTRY_ID'] = R.COUNTRY_ID.values; X['SITE_ID'] = R.SITE_ID.values; X['NUMPAT'] = R.NUMPAT.values
X['ROW_HASH'] = R.ROW_HASH.values


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


def ymd(base, day_fill):
    y = num(X[base + '_Y']); m = num(X[base + '_M']); d = num(X[base + '_D'])
    if day_fill == 'last':
        last = pd.Series([calendar.monthrange(int(a), int(b))[1] if (a == a and b == b) else np.nan
                          for a, b in zip(y, m)], index=y.index)
        dd = d.fillna(last)
    else:
        dd = d.fillna(day_fill)
    return pd.to_datetime(dict(year=y, month=m, day=dd), errors='coerce')


TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(s, mapping):
    return s.astype(object).map(lambda v: mapping.get(v, np.nan) if isinstance(v, str) else np.nan)


def save(df, name):
    df.to_csv(OUT / f'{name}.csv', index=False)
    return df


# ===================================================== 1. dataset verification
ver = []
ver.append(('rows read, Part 1 (non-blank, header excluded)', int((X.SOURCE_PART == 'Part1').sum())))
ver.append(('rows read, Part 2 (non-blank)', int((X.SOURCE_PART == 'Part2').sum())))
ver.append(('rows combined', len(X)))
ver.append(('rows expected (report)', 29565))
ver.append(('distinct Excel row sources (part, row) duplicated', int(X.duplicated(['SOURCE_PART', 'SOURCE_EXCEL_ROW']).sum())))
ver.append(('STUDY_ID distinct values (constant "LIVERMET" = no patient-level ID)', int(R.STUDY_ID.nunique())))
ver.append(('SUBJECT_ID blank rows', int(R.SUBJECT_ID.isna().sum())))
key = R.COUNTRY_ID.astype(str) + '|' + R.SITE_ID.astype(str) + '|' + R.CENTER.astype(str) + '|' + R.NUMPAT.astype(str)
ver.append(('distinct country|site|centre|NUMPAT keys', int(key.nunique())))
ver.append(('rows sharing a country|site|centre|NUMPAT key with another row', int(key.duplicated(keep=False).sum())))
ver.append(('keys shared by two rows with different content (ID collisions)', int(((key.duplicated(keep=False)) & (~X.ROW_HASH.duplicated(keep=False))).sum())))
dup_mask = X.ROW_HASH.duplicated(keep=False)
ver.append(('rows whose analysis content is identical to another row (in pairs)', int(dup_mask.sum())))
ver.append(('extra copies (second record of an identical pair)', int(X.ROW_HASH.duplicated().sum())))
ver.append(('countries', int(R.COUNTRY_ID.nunique())))
ver.append(('sites', int(R.SITE_ID.nunique())))
ver.append(('header column names (unique)', 13658))
save(pd.DataFrame(ver, columns=['check', 'value']), 'F40_dataset_verification')
print(pd.DataFrame(ver, columns=['check', 'value']).to_string(index=False))

# key variable missingness, all 29,565 rows (raw codes)
MISS_VARS = ['STADET', 'STADEN', 'STADEM', 'GENDER', 'LE1METASYNCYN', 'LE1NBMETAHEPNUM', 'LE1HEPMETASIZENUM',
             'LE1PREHEPCEA_F1', 'LE1OPERDT_F1_Y', 'LE1OPERDT_F1_M', 'BIRTHDT', 'DGKCOLDT', 'LE1DGMETADT', 'LASTNDTC',
             'PATSTATC', 'CINCLUSION', 'LE1HEPATECTYN_F1']
rows_m = []
for v in MISS_VARS:
    s = X[v]
    rows_m.append({'variable': v, 'valid_value': int((~s.isna() & ~s.isin(MISS)).sum()),
                   'ND': int((s == 'ND').sum()), 'NA': int((s == 'NA').sum()), 'blank': int(s.isna().sum()),
                   'pct_usable': round(100 * float((~s.isna() & ~s.isin(MISS)).mean()), 1)})
save(pd.DataFrame(rows_m), 'F41_key_variable_missingness_all_rows')
print(pd.DataFrame(rows_m).to_string(index=False))

# TNM raw codes
codes = []
for v, nm in [('STADET', 'T'), ('STADEN', 'N'), ('STADEM', 'M')]:
    for code, n in X[v].fillna('(blank)').value_counts().items():
        codes.append({'component': nm, 'raw_code': code, 'n': int(n)})
save(pd.DataFrame(codes), 'F42_tnm_raw_codes')

# ===================================================== 2. exclusions
op_ser = serial(X.LE1OPERDT_F1)
op_ym = ymd('LE1OPERDT_F1', 15)
op = op_ser.fillna(op_ym)
INC = X.CINCLUSION.eq('Yes'); HEP = X.LE1HEPATECTYN_F1.eq('Yes')
PST_ANY = X.PATSTATC.notna(); DEATH = X.PATSTATC.eq('Deceased')
LAST = serial(X.LASTNDTC)
T_G = gmap(X.STADET, TMAP); N_G = gmap(X.STADEN, NMAP); M_G = gmap(X.STADEM, MMAP)
TNM = pd.concat([T_G, N_G, M_G], axis=1).notna().all(axis=1)
s4 = INC & HEP & op_ym.notna()
s5 = s4 & PST_ANY & LAST.notna()
s6 = s5 & (LAST >= op)
fu = (LAST - op).dt.days
s7 = s6 & ((fu > 0) | DEATH)
steps = [('1 registry (all rows)', pd.Series(True, index=X.index)),
         ('2 CINCLUSION = Yes', INC),
         ('3 hepatectomy recorded', INC & HEP),
         ('4 operation date (year and month)', s4),
         ('5 vital status and last-news recorded', s5),
         ('6 chronology consistent', s6),
         ('7 positive follow-up or death', s7),
         ('8 complete TNM (analytic cohort)', s7 & TNM)]
flow = []
prev = None
for lab, m in steps:
    n = int(m.sum())
    flow.append({'step': lab, 'n_remaining': n, 'excluded_at_step': None if prev is None else prev - n})
    prev = n
flow = pd.DataFrame(flow)
save(flow, 'F43_exclusion_steps_sequential')
print(flow.to_string(index=False))

# each criterion alone (applied to all 29,565 rows), to show overlap
alone = pd.DataFrame([
    {'criterion': 'CINCLUSION not Yes', 'n_failing': int((~INC).sum())},
    {'criterion': 'no hepatectomy recorded', 'n_failing': int((~HEP).sum())},
    {'criterion': 'no operation year and month', 'n_failing': int((~op_ym.notna()).sum())},
    {'criterion': 'no vital status', 'n_failing': int((~PST_ANY).sum())},
    {'criterion': 'no last-news date', 'n_failing': int((~LAST.notna()).sum())},
    {'criterion': 'TNM incomplete (any of T, N, M missing or unmapped)', 'n_failing': int((~TNM).sum())},
])
save(alone, 'F44_each_criterion_alone_all_rows')
print(alone.to_string(index=False))

# ===================================================== 3. TNM-incomplete patients (step 7 but not TNM complete)
D = pd.DataFrame(index=X.index[s7])
D['T_RAW'] = X.STADET[s7].fillna('blank').values
D['N_RAW'] = X.STADEN[s7].fillna('blank').values
D['M_RAW'] = X.STADEM[s7].fillna('blank').values
D['T_OK'] = T_G[s7].notna().values; D['N_OK'] = N_G[s7].notna().values; D['M_OK'] = M_G[s7].notna().values
D['TNM'] = TNM[s7].values
D['T0'] = op[s7].values; D['LAST'] = LAST[s7].values
D['DEATH'] = DEATH[s7].astype(float).values
D['OS_DAYS'] = (D['LAST'] - D['T0']).dt.days.values
D['OS_Y'] = np.minimum(np.where((D.OS_DAYS <= 0) & (D.DEATH == 1), 0.5, D.OS_DAYS) / DAYS, MAXFU)
D['OS_E'] = np.where(np.where((D.OS_DAYS <= 0) & (D.DEATH == 1), 0.5, D.OS_DAYS) / DAYS > MAXFU, 0.0, D.DEATH)
D['ERA'] = np.where(D['T0'].dt.year <= 2009, 'development', 'validation')
D['COUNTRY'] = X.COUNTRY_ID[s7].values
D['SITE'] = X.SITE_ID[s7].values
D['SRC'] = D.index
D['MALE'] = X.GENDER[s7].map({'Male': 1.0, 'Female': 0.0}).values
D['SYNC'] = X.LE1METASYNCYN[s7].map({'Yes': 1.0, 'No': 0.0}).values
D['METS'] = num(X.LE1NBMETAHEPNUM[s7]).where(lambda v: (v >= 1) & (v <= 50)).values
D['SIZE'] = num(X.LE1HEPMETASIZENUM[s7]).where(lambda v: (v > 0) & (v <= 300)).values
D['CEA'] = num(X.LE1PREHEPCEA_F1[s7]).where(lambda v: (v >= 0) & (v <= 40000)).values
D['AGE'] = ((D['T0'] - serial(X.BIRTHDT[s7])).dt.days / DAYS).values
D.loc[(D.AGE < 18) | (D.AGE > 100), 'AGE'] = np.nan
D['YEAR'] = D['T0'].dt.year.values

pat = pd.crosstab(D.T_OK.map({True: 'T ok', False: 'T missing'}),
                  [D.N_OK.map({True: 'N ok', False: 'N missing'}), D.M_OK.map({True: 'M ok', False: 'M missing'}).rename('M')])
inc_pat = []
for (t, n_, m_), g in D.groupby(['T_OK', 'N_OK', 'M_OK']):
    missing = [name for name, ok in [('T', t), ('N', n_), ('M', m_)] if not ok]
    inc_pat.append({'missing_components': ' + '.join(missing) if missing else 'none (complete)', 'n': len(g),
                    'pct_of_step7': round(100 * len(g) / len(D), 2)})
inc_pat = pd.DataFrame(inc_pat).sort_values('n', ascending=False)
save(inc_pat, 'F45_TNM_missing_patterns_step7')
print(inc_pat.to_string(index=False))

# why each component is missing: blank, ND (not determined), NA (not applicable), unmapped code
reasons = []
for comp, col, ok in [('T', 'T_RAW', 'T_OK'), ('N', 'N_RAW', 'N_OK'), ('M', 'M_RAW', 'M_OK')]:
    bad = D[~D[ok]]
    for code, n in bad[col].value_counts().items():
        kind = 'blank' if code == 'blank' else ('ND' if code == 'ND' else ('NA' if code == 'NA' else 'unmapped code'))
        reasons.append({'component': comp, 'raw': code, 'reason': kind, 'n': int(n)})
reasons = pd.DataFrame(reasons)
save(reasons, 'F46_TNM_missing_reasons_step7')
print(reasons.to_string(index=False))

# ===================================================== 4. included vs excluded
A = D[D.TNM]; E = D[~D.TNM]
assert len(A) == 17262 and len(E) == 8832


def smd_cont(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)


def smd_bin(a, b):
    pa, pb = a.mean(), b.mean()
    return (pa - pb) / np.sqrt((pa * (1 - pa) + pb * (1 - pb)) / 2)


def km5(T, Ev):
    k = KaplanMeierFitter().fit(T, Ev)
    return float(k.survival_function_at_times(5).iloc[0]), float(k.median_survival_time_)


rows_cmp = []
for lab, col in [('Age at operation (years)', 'AGE'), ('Metastasis count (known)', 'METS'), ('Largest metastasis mm (known)', 'SIZE'),
                 ('Pre-operative CEA (known)', 'CEA')]:
    a = A[col].dropna(); b = E[col].dropna()
    rows_cmp.append({'characteristic': lab, 'included_n': len(a), 'included': f'{a.median():.1f} (IQR {a.quantile(.25):.1f}-{a.quantile(.75):.1f})',
                     'excluded_n': len(b), 'excluded': f'{b.median():.1f} (IQR {b.quantile(.25):.1f}-{b.quantile(.75):.1f})',
                     'SMD': round(smd_cont(a, b), 3)})
for lab, col in [('Male sex', 'MALE'), ('Synchronous presentation', 'SYNC'), ('Death recorded', 'DEATH')]:
    a = A[col].dropna(); b = E[col].dropna()
    rows_cmp.append({'characteristic': lab, 'included_n': len(a), 'included': f'{100 * a.mean():.1f}%',
                     'excluded_n': len(b), 'excluded': f'{100 * b.mean():.1f}%', 'SMD': round(smd_bin(a, b), 3)})
rows_cmp.append({'characteristic': 'Operation year, median', 'included_n': len(A), 'included': f'{A.YEAR.median():.0f}',
                 'excluded_n': len(E), 'excluded': f'{E.YEAR.median():.0f}', 'SMD': round(smd_cont(A.YEAR, E.YEAR), 3)})
rows_cmp.append({'characteristic': 'Operated 2010 or later', 'included_n': len(A), 'included': f'{100 * (A.YEAR >= 2010).mean():.1f}%',
                 'excluded_n': len(E), 'excluded': f'{100 * (E.YEAR >= 2010).mean():.1f}%',
                 'SMD': round(smd_bin((A.YEAR >= 2010).astype(float), (E.YEAR >= 2010).astype(float)), 3)})
ka5, kmed = km5(A.OS_Y.values, A.OS_E.values); ke5, kmede = km5(E.OS_Y.values, E.OS_E.values)
rows_cmp.append({'characteristic': 'Overall survival: KM median, years', 'included_n': len(A), 'included': f'{kmed:.2f}',
                 'excluded_n': len(E), 'excluded': f'{kmede:.2f}', 'SMD': None})
rows_cmp.append({'characteristic': 'Overall survival: KM 5-year', 'included_n': len(A), 'included': f'{100 * ka5:.1f}%',
                 'excluded_n': len(E), 'excluded': f'{100 * ke5:.1f}%', 'SMD': None})
rows_cmp.append({'characteristic': 'Death recorded (deaths / n)', 'included_n': len(A), 'included': f'{int(A.DEATH.sum()):,}',
                 'excluded_n': len(E), 'excluded': f'{int(E.DEATH.sum()):,}', 'SMD': None})
cmp_tbl = pd.DataFrame(rows_cmp)
save(cmp_tbl, 'F47_included_vs_excluded_comparison')
print(cmp_tbl.to_string(index=False))

# TNM missingness by period and by country (is it clustered?)
by_era = D.groupby('ERA').agg(n=('TNM', 'size'), tnm_incomplete=('TNM', lambda s: int((~s).sum())))
by_era['pct_incomplete'] = (100 * by_era.tnm_incomplete / by_era.n).round(1)
by_era.reset_index().to_csv(OUT / 'F48a_TNM_incomplete_by_period.csv', index=False)
by_year = D.groupby('YEAR').agg(n=('TNM', 'size'), incomplete=('TNM', lambda s: int((~s).sum())))
by_year['pct_incomplete'] = (100 * by_year.incomplete / by_year.n).round(1)
by_year.reset_index().to_csv(OUT / 'F48b_TNM_incomplete_by_operation_year.csv', index=False)
by_c = D.groupby('COUNTRY').agg(n=('TNM', 'size'), incomplete=('TNM', lambda s: int((~s).sum())))
by_c['pct_incomplete'] = (100 * by_c.incomplete / by_c.n).round(1)
by_c = by_c.sort_values('n', ascending=False)
by_c.reset_index().to_csv(OUT / 'F48c_TNM_incomplete_by_country.csv', index=False)
site_pct = by_c.pct_incomplete
print('countries:', len(by_c), '| countries with 0% incomplete:', int((site_pct == 0).sum()),
      '| with 100%:', int((site_pct == 100).sum()))
sites = D.groupby('SITE').agg(n=('TNM', 'size'), incomplete=('TNM', lambda s: int((~s).sum())))
sites['pct'] = 100 * sites.incomplete / sites.n
print('sites:', len(sites), '| sites with 0% incomplete:', int((sites.pct == 0).sum()),
      '| sites with >=50% incomplete:', int((sites.pct >= 50).sum()), '| median patients per site:', int(sites.n.median()))
site_summary = pd.DataFrame([{'sites': len(sites), 'sites_zero_incomplete': int((sites.pct == 0).sum()),
                              'sites_all_incomplete': int((sites.pct == 100).sum()),
                              'sites_50pct_or_more_incomplete': int((sites.pct >= 50).sum()),
                              'median_patients_per_site': int(sites.n.median())}])
save(site_summary, 'F48d_TNM_incomplete_site_clustering')

D.to_parquet(WORK / 'investigation_step7.parquet')
print('stage B done ->', OUT)
