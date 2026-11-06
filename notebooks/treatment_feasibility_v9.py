"""Treatment workstream, feasibility audit (separate from the locked v8 analysis; nothing here refits or alters it).

Inputs (working directory, patient-level, not in the repository):
  extract_raw.parquet, investigation_rows.parquet, investigation_step7.parquet (v8 cohort rules),
  treatment_rows.parquet (treatment fields, aligned to the extract by workbook order).
The risk groups are rebuilt with the locked M2a specification; the script asserts that the cut-points are 0.3793 / 0.4756.
Outputs: results/final_v9/treatment_feasibility (aggregate tables only).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v9/treatment_feasibility'))
OUT.mkdir(parents=True, exist_ok=True)
DAYS = 365.25
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']

X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
T = pd.read_parquet(Path(os.environ.get('LIVERMET_TREAT_DIR', str(WORK))) / 'treatment_rows.parquet').reset_index(drop=True)
D = pd.read_parquet(WORK / 'investigation_step7.parquet')
assert len(X) == len(T) == 29565 and (X.SOURCE_EXCEL_ROW.values == T.SOURCE_EXCEL_ROW.values).all()


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


def ymd_serial_or_components(base_serial, y, m, d, fill=15):
    yy = num(y); mm = num(m); dd = num(d).fillna(fill)
    built = pd.to_datetime(dict(year=yy, month=mm, day=dd), errors='coerce')
    return base_serial.fillna(built)


# ---------------------------------------------------------------- v8 cohort (analytic) and locked risk groups
src = D.SRC.values
dgk = serial(X.DGKCOLDT).values[src]; dg = serial(X.LE1DGMETADT).values[src]
F = pd.DataFrame({'SRC': src, 'ERA': D.ERA.values, 'DEV': D.ERA.eq('development').values, 'TNM': D.TNM.values,
                  'OS_Y': D.OS_Y.values, 'OS_E': D.OS_E.values, 'DEATH': D.DEATH.values, 'OS_DAYS': D.OS_DAYS.values,
                  'T0': D.T0.values, 'AGE': D.AGE.values, 'MALE': D.MALE.values, 'SYNC': D.SYNC.values,
                  'METS': D.METS.values, 'SIZE': D.SIZE.values, 'CEA': D.CEA.values, 'YEAR': D.YEAR.values,
                  'COUNTRY': D.COUNTRY.values, 'SITE': D.SITE.values, 'T_RAW': D.T_RAW.values,
                  'N_RAW': D.N_RAW.values, 'M_RAW': D.M_RAW.values})
F['DFI'] = (pd.to_datetime(dg) - pd.to_datetime(dgk)).days / 30.4375
F.loc[F.SYNC == 1, 'DFI'] = 0.0
F.loc[(F.DFI < 0) | (pd.to_datetime(dg) > pd.to_datetime(F['T0'])), 'DFI'] = np.nan
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(vals, mp):
    return pd.Series(vals).astype(object).map(lambda x: mp.get(x, np.nan) if isinstance(x, str) else np.nan).values


T_ORD = pd.Series(gmap(F.T_RAW.values, TMAP)).map({'T1-2': 0, 'T3': 1, 'T4': 2}).values
N_ORD = pd.Series(gmap(F.N_RAW.values, NMAP)).map({'N0': 0, 'N1': 1, 'N2': 2}).values
M_ORD = pd.Series(gmap(F.M_RAW.values, MMAP)).map({'M0': 0, 'M1': 1}).values
F['T_ORD'] = T_ORD; F['N_ORD'] = N_ORD; F['M_ORD'] = M_ORD


def covariates(G):
    H = G.copy()
    dev = H.DEV.values
    for c in ['DFI', 'METS', 'SIZE']:
        H[c + '_NR'] = H[c].isna().astype(float)
    for c in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE']:
        H[c + '_F'] = H[c].fillna(H.loc[dev, c].median())
    H['AGE10_F'] = H.AGE_F / 10; H['DFI12_F'] = H.DFI_F / 12; H['SIZE10_F'] = H.SIZE_F / 10
    H['T3'] = (H.T_ORD == 1).astype(float); H['T4'] = (H.T_ORD == 2).astype(float)
    H['N1'] = (H.N_ORD == 1).astype(float); H['N2'] = (H.N_ORD == 2).astype(float)
    H['M1'] = (H.M_ORD == 1).astype(float)
    H['STRATUM'] = H.MALE_F.round().astype(int) * 2 + H.SYNC_F.round().astype(int)
    H['STRAT_M'] = H.STRATUM * 2 + H.M1.astype(int)
    return H


M2A = ['T3', 'T4', 'N1', 'N2', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
COH = covariates(F[F.TNM].reset_index(drop=True))
TRN = COH.DEV.values
cph = CoxPHFitter().fit(COH.loc[TRN, M2A + ['STRAT_M', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRAT_M'])
be = cph.params_[M2A].values
lp = COH[M2A].astype(float).values @ be
# baseline hazard (training) at 5 years, Breslow
S5 = np.ones(len(COH))
for s in np.unique(COH.STRAT_M.values):
    mt = (COH.STRAT_M.values == s) & TRN
    t, e, le = COH.OS_Y.values[mt], COH.OS_E.values[mt], lp[mt]
    o = np.argsort(t, kind='mergesort'); t, e, le = t[o], e[o], le[o]
    re_ = np.cumsum(np.exp(le)[::-1])[::-1]
    ev = np.unique(t[e == 1])
    idx = np.searchsorted(t, ev, side='left')
    dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
    H = np.cumsum(dk / re_[idx])
    ii = np.searchsorted(ev, 5.0, side='right') - 1
    He = H[ii] if ii >= 0 else 0.0
    ms = COH.STRAT_M.values == s
    S5[ms] = np.exp(-np.exp(lp[ms]) * He)
q33, q67 = np.quantile(S5[TRN], [1 / 3, 2 / 3])
assert round(float(q33), 4) == 0.3793 and round(float(q67), 4) == 0.4756, (q33, q67)
COH['GROUP'] = np.where(S5 >= q67, 'Favourable', np.where(S5 >= q33, 'Intermediate', 'Adverse'))
print('locked cut-points reproduced:', round(float(q33), 4), round(float(q67), 4))
print(COH.GROUP.value_counts().to_string())

# ---------------------------------------------------------------- treatment fields for the cohort
TF = T.loc[COH.SRC.values].reset_index(drop=True)
COH = pd.concat([COH.reset_index(drop=True), TF.drop(columns=['SOURCE_PART', 'SOURCE_EXCEL_ROW'])], axis=1)
op_date = COH['T0']
preop_start = serial(COH.LE1PREOPMSTDT_F1)
postop_start = serial(COH.LE1POSTOPMSTDT_F1)
poscol_start = serial(COH.POSTCOLSTDT_F1)
COH['PREOP_MC'] = COH.LE1PREOPMCTYN_F1.replace({'ND': 'ND', 'NA': 'ND'}).fillna('blank')
COH['POSTOP_MC'] = COH.LE1POSTOPMCTYN_F1.replace({'ND': 'ND', 'NA': 'ND'}).fillna('blank')
COH['POSTCOL_CT'] = COH.POSTCOLCTYN_F1.replace({'NA': 'ND'}).fillna('blank')
COH['PRECOL_CHI'] = COH.PRECOLCHIYN.replace({'NA': 'ND'}).fillna('blank')
COH['SURG'] = 'hepatectomy'   # all cohort members have a recorded hepatectomy (step 3)

# ---------------------------------------------------------------- T01: inventory and coding in the cohort
inv_rows = []
for lab, col, meaning in [
    ('Pre-operative chemotherapy for liver metastases', 'LE1PREOPMCTYN_F1', 'Yes/No; start date LE1PREOPMSTDT_F1'),
    ('Post-operative chemotherapy for liver metastases', 'LE1POSTOPMCTYN_F1', 'Yes/No; start date LE1POSTOPMSTDT_F1'),
    ('Post-operative chemotherapy after primary colorectal surgery', 'POSTCOLCTYN_F1', 'Yes/No; start date POSTCOLSTDT_F1 (components available)'),
    ('Pre-operative chemotherapy for primary colorectal cancer', 'PRECOLCHIYN', 'Yes/No (no date)'),
    ('Pre-operative radiotherapy for primary colorectal cancer', 'PRECOLRADYN', 'Yes/No (no date)'),
    ('Chemotherapy intent after primary surgery', 'POSTCOLINTENT_F1', 'Yes/No (intent; not defined in extract)'),
    ('Targeted therapy after primary surgery', 'POSTCOLTARGTHEYN_F1', 'Yes/No'),
    ('Oxaliplatin after primary surgery', 'POSTCOLOXALIYN_F1', 'Yes/No'),
    ('Local treatment of liver metastases (other than resection)', 'LE1LOCALTRTYN_F1', 'Yes/No'),
    ('Liver metastasis resection (LE1METARESECYN_L1)', 'LE1METARESECYN_L1', 'Yes/No (repeat resection context)'),
    ('KRAS / RAS status proxy (KPEGFRYN)', 'KPEGFRYN', 'Not KRAS; EGFR-related field, mostly blank')]:
    s_ = COH[col]
    inv_rows.append({'variable': lab, 'field': col, 'coding': meaning,
                     'yes_n': int((s_ == 'Yes').sum()), 'no_n': int((s_ == 'No').sum()),
                     'ND_or_NA_n': int(s_.isin(['ND', 'NA']).sum()), 'blank_n': int(s_.isna().sum() + (s_ == 'blank').sum()),
                     'pct_usable': round(100 * float(s_.isin(['Yes', 'No']).mean()), 1)})
inv = pd.DataFrame(inv_rows)
inv.to_csv(OUT / 'H01_treatment_variable_inventory_cohort.csv', index=False)
print(inv.to_string(index=False))

# ---------------------------------------------------------------- T02: timing pattern (before / after surgery / both)
def cat(row_pre, row_post):
    if row_pre == 'Yes' and row_post == 'Yes':
        return 'pre-operative and post-operative (liver metastases)'
    if row_pre == 'Yes':
        return 'pre-operative only'
    if row_post == 'Yes':
        return 'post-operative only'
    if 'No' in (row_pre, row_post) and row_pre in ('No', 'ND') and row_post in ('No', 'ND'):
        return 'no recorded liver-metastasis chemotherapy' if (row_pre == 'No' and row_post == 'No') else 'no recorded chemotherapy, with ND'
    return 'unknown (ND or blank in at least one field)'


COH['TIMING'] = [cat(a, b) for a, b in zip(COH.PREOP_MC, COH.POSTOP_MC)]
comb = pd.crosstab(COH.PREOP_MC, COH.POSTOP_MC, margins=True)
comb.to_csv(OUT / 'H02_preop_by_postop_liver_chemotherapy_cohort.csv')
print(comb.to_string())
timing_tab = COH.groupby('TIMING').agg(n=('SRC', 'size')).reset_index()
timing_tab['pct'] = (100 * timing_tab.n / len(COH)).round(1)
timing_tab.to_csv(OUT / 'H03_timing_pattern_cohort.csv', index=False)
print(timing_tab.to_string(index=False))

# ---------------------------------------------------------------- T03: start dates and missing dates; immortal-time check
dates_rows = []
for lab, yn, start in [('pre-operative liver-metastasis chemotherapy', COH.PREOP_MC, preop_start),
                       ('post-operative liver-metastasis chemotherapy', COH.POSTOP_MC, postop_start),
                       ('post-operative chemotherapy after primary surgery', COH.POSTCOL_CT, poscol_start)]:
    yes = yn.eq('Yes')
    d_days = (start - op_date).dt.days
    dates_rows.append({'exposure': lab, 'recorded_yes': int(yes.sum()), 'yes_with_start_date': int((yes & start.notna()).sum()),
                       'yes_missing_start_date': int((yes & start.isna()).sum()),
                       'pct_yes_with_date': round(100 * float((yes & start.notna()).sum() / max(yes.sum(), 1)), 1),
                       'start_before_operation_n': int((yes & (d_days < 0)).sum()),
                       'start_on_or_after_operation_n': int((yes & (d_days >= 0)).sum()),
                       'median_days_from_operation_start': round(float(np.nanmedian(d_days[yes & start.notna()])), 1)
                       if (yes & start.notna()).sum() else None})
dates_tab = pd.DataFrame(dates_rows)
dates_tab.to_csv(OUT / 'H04_chemotherapy_start_dates_cohort.csv', index=False)
print(dates_tab.to_string(index=False))

# ---------------------------------------------------------------- T04: pretreatment covariates by treatment (confounding by indication)
COH['PRE_OR_POST'] = np.where((COH.PREOP_MC == 'Yes') | (COH.POSTOP_MC == 'Yes'), 'any liver-metastasis chemotherapy',
                              np.where((COH.PREOP_MC == 'No') & (COH.POSTOP_MC == 'No'), 'no recorded liver-metastasis chemotherapy', 'unknown'))
cov_rows = []
known = COH[COH.PRE_OR_POST != 'unknown']
for lab, col in [('Age, years (median)', 'AGE'), ('Metastasis count (median)', 'METS'), ('Largest metastasis, mm (median)', 'SIZE'),
                 ('Pre-operative CEA, ng/mL (median)', 'CEA')]:
    a = known[known.PRE_OR_POST == 'any liver-metastasis chemotherapy'][col].dropna()
    b = known[known.PRE_OR_POST == 'no recorded liver-metastasis chemotherapy'][col].dropna()
    cov_rows.append({'covariate': lab, 'treated_n': len(a), 'treated': round(float(a.median()), 1),
                     'untreated_n': len(b), 'untreated': round(float(b.median()), 1),
                     'SMD': round(float((a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)), 3)})
for lab, cond in [('Synchronous presentation (%)', 'SYNC'), ('Male sex (%)', 'MALE'), ('Operated 2010 or later (%)', 'YEAR>=2010'),
                  ('T4 (%)', 'T4'), ('N2 (%)', 'N2'), ('M1 (%)', 'M1')]:
    if cond == 'YEAR>=2010':
        flag_ = known.YEAR >= 2010
    elif cond in ('T4', 'N2', 'M1'):
        flag_ = known[{'T4': 'T_ORD', 'N2': 'N_ORD', 'M1': 'M_ORD'}[cond]].isin([2] if cond == 'T4' else [2] if cond == 'N2' else [1])
    else:
        flag_ = known[cond] == 1
    a = flag_[known.PRE_OR_POST == 'any liver-metastasis chemotherapy'].astype(float)
    b = flag_[known.PRE_OR_POST == 'no recorded liver-metastasis chemotherapy'].astype(float)
    pa, pb = a.mean(), b.mean()
    cov_rows.append({'covariate': lab, 'treated_n': len(a), 'treated': round(100 * pa, 1), 'untreated_n': len(b),
                     'untreated': round(100 * pb, 1), 'SMD': round(float((pa - pb) / np.sqrt((pa * (1 - pa) + pb * (1 - pb)) / 2)), 3)})
pd.DataFrame(cov_rows).to_csv(OUT / 'H05_pretreatment_covariates_by_treatment_cohort.csv', index=False)
print(pd.DataFrame(cov_rows).to_string(index=False))

# ---------------------------------------------------------------- T05: treatment by locked risk group (prevalence and sizes)
grp_rows = []
for g in ['Favourable', 'Intermediate', 'Adverse']:
    m = COH.GROUP == g
    k = COH[m]
    grp_rows.append({'group': g, 'n': int(m.sum()),
                     'pre_op_liver_chemo_yes': int((k.PREOP_MC == 'Yes').sum()),
                     'post_op_liver_chemo_yes': int((k.POSTOP_MC == 'Yes').sum()),
                     'any_liver_chemo_recorded': int((k.PRE_OR_POST == 'any liver-metastasis chemotherapy').sum()),
                     'no_recorded_liver_chemo': int((k.PRE_OR_POST == 'no recorded liver-metastasis chemotherapy').sum()),
                     'unknown_treatment_status': int((k.PRE_OR_POST == 'unknown').sum()),
                     'deaths': int(k.DEATH.sum())})
pd.DataFrame(grp_rows).to_csv(OUT / 'H06_treatment_counts_by_risk_group.csv', index=False)
print(pd.DataFrame(grp_rows).to_string(index=False))

# ---------------------------------------------------------------- T06: missingness structure by period and site
miss = COH.groupby('ERA').agg(n=('SRC', 'size'), unknown=('PRE_OR_POST', lambda s: int((s == 'unknown').sum())))
miss['pct_unknown'] = (100 * miss.unknown / miss.n).round(1)
miss.reset_index().to_csv(OUT / 'H07_treatment_unknown_by_period.csv', index=False)
print(miss.to_string())
site = COH.groupby('SITE').agg(n=('SRC', 'size'), unknown=('PRE_OR_POST', lambda s: int((s == 'unknown').sum())))
site['pct_unknown'] = 100 * site.unknown / site.n
site_sum = pd.DataFrame([{'sites': len(site), 'sites_all_known': int((site.pct_unknown == 0).sum()),
                          'sites_50pct_or_more_unknown': int((site.pct_unknown >= 50).sum()),
                          'median_patients_per_site': int(site.n.median())}])
site_sum.to_csv(OUT / 'H08_treatment_unknown_site_structure.csv', index=False)
print(site_sum.to_string(index=False))

# ---------------------------------------------------------------- T07: exposure counts for an interaction analysis
exp_rows = []
for g in ['Favourable', 'Intermediate', 'Adverse']:
    k = COH[(COH.GROUP == g) & (COH.PRE_OR_POST != 'unknown')]
    exp_rows.append({'group': g, 'treated_n': int((k.PRE_OR_POST == 'any liver-metastasis chemotherapy').sum()),
                     'untreated_n': int((k.PRE_OR_POST == 'no recorded liver-metastasis chemotherapy').sum()),
                     'treated_deaths': int(k[k.PRE_OR_POST == 'any liver-metastasis chemotherapy'].DEATH.sum()),
                     'untreated_deaths': int(k[k.PRE_OR_POST == 'no recorded liver-metastasis chemotherapy'].DEATH.sum())})
pd.DataFrame(exp_rows).to_csv(OUT / 'H09_exposure_counts_by_group_for_interaction.csv', index=False)
print(pd.DataFrame(exp_rows).to_string(index=False))
print('treatment feasibility tables written ->', OUT)
