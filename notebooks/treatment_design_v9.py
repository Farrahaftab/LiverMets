"""Treatment workstream, design verification (no treatment-effect model is fitted).

Diagnostics only:
  J01  timing check: discordance between the pre-operative metastasis count and the resected count, by pre-operative
       liver chemotherapy, overall and within lesion-count strata.
  J02  propensity-score diagnostics for pre-operative liver chemotherapy vs none: overlap, common support,
       effective sample size, and extreme weights. The propensity model is a positivity check, not an effect estimate.
  J03  positivity by locked risk group.
  J04  empirical positivity: covariate cells with no treated or no untreated patients.
  J05  eligibility and missing-treatment accounting.
Inputs: investigation_step7.parquet, extract_raw.parquet, treatment_rows.parquet, combined_extract_v3_ops.parquet (WORK).
Outputs: LIVERMET_OUT_DIR (default results/final_v9/treatment_design).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines.utils import concordance_index
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
TREAT = Path(os.environ.get('LIVERMET_TREAT_DIR', str(WORK)))
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v9/treatment_design'))
OUT.mkdir(parents=True, exist_ok=True)
DAYS = 365.25
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']

X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
T = pd.read_parquet(TREAT / 'treatment_rows.parquet').reset_index(drop=True)
V = pd.read_parquet(Path(os.environ.get('LIVERMET_OPS_DIR', str(WORK))) / 'combined_extract_v3_ops.parquet').reset_index(drop=True)
D = pd.read_parquet(WORK / 'investigation_step7.parquet')
assert (X.SOURCE_EXCEL_ROW.values == T.SOURCE_EXCEL_ROW.values).all() and (V.SOURCE_EXCEL_ROW.values == X.SOURCE_EXCEL_ROW.values).all()


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


A = D[D.TNM].reset_index(drop=True)
src = A.SRC.values
pre = T.LE1PREOPMCTYN_F1.values[src]
op = serial(X.LE1OPERDT_F1).values[src]
dgk = serial(X.DGKCOLDT).values[src]; dg = serial(X.LE1DGMETADT).values[src]
A['PRE'] = pre
A['PRE_STATUS'] = pd.Series(pre).replace({None: 'blank'}).fillna('blank').values
A['EXPO'] = np.where(A.PRE == 'Yes', 1.0, np.where(A.PRE == 'No', 0.0, np.nan))
A['PRE_CNT'] = pd.to_numeric(X.LE1NBMETAHEPNUM.values[src], errors='coerce')
A['RES_CNT'] = pd.to_numeric(V.LE1NBMRESECNUM_F1.values[src].astype(object), errors='coerce')
A['SIZE_RAW'] = A.SIZE
A['YEAR_GE2010'] = (A.YEAR >= 2010).astype(float)
A['DFI'] = (pd.to_datetime(dg) - pd.to_datetime(dgk)).days / 30.4375
A.loc[A.SYNC == 1, 'DFI'] = 0.0
A.loc[(A.DFI < 0) | (pd.to_datetime(dg) > pd.to_datetime(op)), 'DFI'] = np.nan
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def mapped(raw, mp):
    return pd.Series(raw).astype(object).map(lambda x: mp.get(x, np.nan) if isinstance(x, str) else np.nan).values


A['T_G'] = mapped(A.T_RAW.values, TMAP); A['N_G'] = mapped(A.N_RAW.values, NMAP); A['M_G'] = mapped(A.M_RAW.values, MMAP)

# ================================================================ J01: timing check (pre-op count vs resected count)
both = A[A.PRE.isin(['Yes', 'No']) & A.PRE_CNT.notna() & A.RES_CNT.notna()].copy()
both['pc'] = np.minimum(both.PRE_CNT, 4); both['rc'] = np.minimum(both.RES_CNT, 4)
both['resected_lower'] = (both.rc < both.pc).astype(int)
both['resected_higher'] = (both.rc > both.pc).astype(int)
j1a = both.groupby('PRE').agg(n=('pc', 'size'), mean_preop_count=('pc', 'mean'), mean_resected_count=('rc', 'mean'),
                              resected_lower_pct=('resected_lower', lambda s: round(100 * s.mean(), 1)),
                              resected_higher_pct=('resected_higher', lambda s: round(100 * s.mean(), 1))).reset_index()
j1a.round(2).to_csv(OUT / 'J01a_count_discordance_overall.csv', index=False)
both['bin'] = pd.cut(both.pc, [0, 1, 2, 3, 4], labels=['1', '2', '3', '4 or more'])
j1b = both.groupby(['bin', 'PRE'], observed=True).agg(n=('pc', 'size'),
                                                     resected_lower_pct=('resected_lower', lambda s: round(100 * s.mean(), 1))).reset_index()
j1b.to_csv(OUT / 'J01b_count_discordance_within_preop_count_strata.csv', index=False)
print(j1a.round(2).to_string(index=False)); print(j1b.to_string(index=False))

# ================================================================ J02: propensity diagnostics (positivity check only)
K = A[A.EXPO.notna()].reset_index(drop=True)
COV = pd.DataFrame({'age': K.AGE.fillna(K.AGE.median()), 'male': K.MALE.fillna(0), 'synchronous': K.SYNC.fillna(0),
                    'interval_missing': K.DFI.isna().astype(float), 'interval_months': K.DFI.fillna(0) / 12,
                    'metastasis_count': K.METS.fillna(K.METS.median()), 'count_missing': K.METS.isna().astype(float),
                    'size_mm': K.SIZE.fillna(K.SIZE.median()), 'size_missing': K.SIZE.isna().astype(float),
                    'cea_log': np.log1p(K.CEA.fillna(K.CEA.median())), 'cea_missing': K.CEA.isna().astype(float),
                    'T4': (K.T_G == 'T4').astype(float), 'N1': (K.N_G == 'N1').astype(float),
                    'N2': (K.N_G == 'N2').astype(float), 'M1': (K.M_G == 'M1').astype(float),
                    'operated_2010_or_later': K.YEAR_GE2010})
ps_model = LogisticRegression(max_iter=2000, C=1e6).fit(COV.values, K.EXPO.values)
ps = ps_model.predict_proba(COV.values)[:, 1]
K['PS'] = ps
treated = K.EXPO.values == 1
w_ate = np.where(treated, 1 / ps, 1 / (1 - ps))
w_att = np.where(treated, 1.0, ps / (1 - ps))
ess = lambda w: (w.sum() ** 2) / (w ** 2).sum()  # noqa: E731
rows2 = []
rows2.append({'population': 'all with known pre-operative status', 'treated_n': int(treated.sum()), 'untreated_n': int((~treated).sum()),
              'C_statistic_for_treatment': round(float(roc_auc_score(K.EXPO.values, ps)), 3),
              'PS_median_treated': round(float(np.median(ps[treated])), 3), 'PS_median_untreated': round(float(np.median(ps[~treated])), 3),
              'PS_min': round(float(ps.min()), 4), 'PS_max': round(float(ps.max()), 4),
              'pct_PS_below_0.05': round(100 * float((ps < 0.05).mean()), 1), 'pct_PS_above_0.95': round(100 * float((ps > 0.95).mean()), 1),
              'treated_outside_untreated_range_pct': round(100 * float((treated & ((ps < ps[~treated].min()) | (ps > ps[~treated].max()))).sum() / treated.sum()), 2),
              'untreated_outside_treated_range_pct': round(100 * float((~treated & ((ps < ps[treated].min()) | (ps > ps[treated].max()))).sum() / (~treated).sum()), 2),
              'ESS_ATE_treated': round(float(ess(w_ate[treated])), 0), 'ESS_ATE_untreated': round(float(ess(w_ate[~treated])), 0),
              'max_ATE_weight': round(float(w_ate.max()), 1), 'pct_weights_above_10': round(100 * float((w_ate > 10).mean()), 2)})
j2 = pd.DataFrame(rows2)
j2.to_csv(OUT / 'J02_propensity_overlap_diagnostics.csv', index=False)
print(j2.T.to_string())
# overlap by decile of propensity
K['PS_DEC'] = pd.qcut(K.PS, 10, labels=False, duplicates='drop') + 1
j2b = K.groupby('PS_DEC').agg(n=('EXPO', 'size'), treated=('EXPO', 'sum'), mean_PS=('PS', 'mean')).reset_index()
j2b['treated_pct'] = (100 * j2b.treated / j2b.n).round(1)
j2b.round(3).to_csv(OUT / 'J02b_propensity_deciles.csv', index=False)
print(j2b.round(3).to_string(index=False))

# ================================================================ J03: positivity by locked risk group
# risk groups are the locked M2a groups, recomputed from the v8 specification (same assertion as the treatment feasibility script)
GROUP = pd.read_csv(WORK / 'groups_v8.csv').set_index('SRC')['GROUP']   # written by treatment_feasibility_v9.py (locked M2a groups)
if True:
    K['GROUP'] = K.SRC.map(GROUP).values
    rows3 = []
    for g in ['Favourable', 'Intermediate', 'Adverse']:
        k = K[K.GROUP == g]
        rows3.append({'group': g, 'n': len(k), 'treated': int(k.EXPO.sum()), 'untreated': int((1 - k.EXPO).sum()),
                      'PS_min_treated': round(float(k.PS[k.EXPO == 1].min()), 3), 'PS_max_untreated': round(float(k.PS[k.EXPO == 0].max()), 3),
                      'C_statistic_within_group': round(float(roc_auc_score(k.EXPO, k.PS)), 3)})
    pd.DataFrame(rows3).to_csv(OUT / 'J03_positivity_by_locked_group.csv', index=False)
    print(pd.DataFrame(rows3).to_string(index=False))

# ================================================================ J04: empirical positivity over covariate cells
cells = K.assign(T=K.T_G.fillna('NA'), N=K.N_G.fillna('NA'), M=K.M_G.fillna('NA'), S=K.SYNC.fillna(-1).astype(int).astype(str))
cell = cells.groupby(['T', 'N', 'M', 'S']).agg(n=('EXPO', 'size'), treated=('EXPO', 'sum')).reset_index()
cell['untreated'] = cell.n - cell.treated
cell['empty_arm'] = (cell.treated == 0) | (cell.untreated == 0)
j4 = pd.DataFrame([{'cells_total': len(cell), 'cells_with_n_at_least_20': int((cell.n >= 20).sum()),
                    'cells_with_empty_arm': int(cell.empty_arm.sum()),
                    'patients_in_empty_arm_cells': int(cell.loc[cell.empty_arm, 'n'].sum()),
                    'patients_in_cells_with_n_ge_20_and_both_arms': int(cell.loc[(cell.n >= 20) & ~cell.empty_arm, 'n'].sum())}])
j4.to_csv(OUT / 'J04_empirical_positivity_cells.csv', index=False)
print(j4.to_string(index=False))

# ================================================================ J05: eligibility and missing-treatment accounting
acc = pd.DataFrame([
    {'step': 'analytic cohort (v8, TNM complete, hepatectomy)', 'n': len(A)},
    {'step': 'pre-operative liver chemotherapy recorded Yes', 'n': int((A.PRE == 'Yes').sum())},
    {'step': 'pre-operative liver chemotherapy recorded No', 'n': int((A.PRE == 'No').sum())},
    {'step': 'pre-operative status ND', 'n': int((A.PRE == 'ND').sum())},
    {'step': 'pre-operative status NA', 'n': int((A.PRE == 'NA').sum())},
    {'step': 'pre-operative status blank', 'n': int((A.PRE_STATUS == 'blank').sum())},
    {'step': 'analysis population for the proposed primary comparison (Yes or No)', 'n': int(A.EXPO.notna().sum())},
    {'step': 'pre-operative Yes with a start date', 'n': int(((A.PRE == 'Yes') & pd.Series(serial(T.LE1PREOPMSTDT_F1).values[src]).notna().values).sum())},
])
acc.to_csv(OUT / 'J05_eligibility_and_missing_treatment_accounting.csv', index=False)
print(acc.to_string(index=False))
print('design diagnostics written ->', OUT)
