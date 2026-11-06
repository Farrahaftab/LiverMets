"""Reports the locked v8 M2a model for TRIPOD model presentation.

Refits the identical specification (stratified Cox, strata sex x synchrony x M-stage; covariates as in the notebook) on the
training era only, and reproduces the validation C-index 0.6216 and the cut-points 0.3793 / 0.4756 before reporting.
No specification is changed. Outputs: P1_model_coefficients.csv, P1_baseline_survival_by_stratum.csv,
P1_group_summary.csv (to LIVERMET_OUT_DIR).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v9/paper1'))
OUT.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25

X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
D = pd.read_parquet(WORK / 'investigation_step7.parquet')


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


src = D.SRC.values
dgk = serial(X.DGKCOLDT).values[src]; dg = serial(X.LE1DGMETADT).values[src]
F = pd.DataFrame({'SRC': src, 'ERA': D.ERA.values, 'DEV': D.ERA.eq('development').values, 'TNM': D.TNM.values,
                  'OS_Y': D.OS_Y.values, 'OS_E': D.OS_E.values, 'DEATH': D.DEATH.values, 'T0': D.T0.values,
                  'AGE': D.AGE.values, 'MALE': D.MALE.values, 'SYNC': D.SYNC.values, 'METS': D.METS.values,
                  'SIZE': D.SIZE.values, 'T_RAW': D.T_RAW.values, 'N_RAW': D.N_RAW.values, 'M_RAW': D.M_RAW.values})
F['DFI'] = (pd.to_datetime(dg) - pd.to_datetime(dgk)).days / 30.4375
F.loc[F.SYNC == 1, 'DFI'] = 0.0
F.loc[(F.DFI < 0) | (pd.to_datetime(dg) > pd.to_datetime(F['T0'])), 'DFI'] = np.nan
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(vals, mp):
    return pd.Series(vals).astype(object).map(lambda x: mp.get(x, np.nan) if isinstance(x, str) else np.nan).values


F['T_ORD'] = pd.Series(gmap(F.T_RAW.values, TMAP)).map({'T1-2': 0, 'T3': 1, 'T4': 2}).values
F['N_ORD'] = pd.Series(gmap(F.N_RAW.values, NMAP)).map({'N0': 0, 'N1': 1, 'N2': 2}).values
F['M_ORD'] = pd.Series(gmap(F.M_RAW.values, MMAP)).map({'M0': 0, 'M1': 1}).values
C = F[F.TNM].reset_index(drop=True)
dev = C.DEV.values
for c in ['DFI', 'METS', 'SIZE']:
    C[c + '_NR'] = C[c].isna().astype(float)
for c in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE']:
    C[c + '_F'] = C[c].fillna(C.loc[dev, c].median())
C['AGE10_F'] = C.AGE_F / 10; C['DFI12_F'] = C.DFI_F / 12; C['SIZE10_F'] = C.SIZE_F / 10
C['T3'] = (C.T_ORD == 1).astype(float); C['T4'] = (C.T_ORD == 2).astype(float)
C['N1'] = (C.N_ORD == 1).astype(float); C['N2'] = (C.N_ORD == 2).astype(float)
C['M1'] = (C.M_ORD == 1).astype(float)
C['MALE_F_B'] = C.MALE_F.round().astype(int); C['SYNC_F_B'] = C.SYNC_F.round().astype(int)
C['STRATUM'] = C.MALE_F_B * 2 + C.SYNC_F_B
C['STRAT_M'] = C.STRATUM * 2 + C.M1.astype(int)
M2A = ['T3', 'T4', 'N1', 'N2', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
LABEL = {'T3': 'T3 vs T1-2', 'T4': 'T4 vs T1-2', 'N1': 'N1 vs N0', 'N2': 'N2 vs N0', 'AGE10_F': 'Age, per 10 years',
         'DFI12_F': 'Interval primary to liver metastasis, per 12 months (0 if synchronous)',
         'METS_F': 'Number of liver metastases, per additional lesion', 'SIZE10_F': 'Largest metastasis, per 10 mm',
         'DFI_NR': 'Interval unavailable (indicator)', 'METS_NR': 'Metastasis count unavailable (indicator)',
         'SIZE_NR': 'Metastasis size unavailable (indicator)'}

cph = CoxPHFitter().fit(C.loc[dev, M2A + ['STRAT_M', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRAT_M'])
be = cph.params_[M2A].values
Xm = C[M2A].astype(float).values
lp = Xm @ be
st = C.STRAT_M.values
bres = {}
for s in np.unique(st):
    m = (st == s) & dev
    t, e, le = C.OS_Y.values[m], C.OS_E.values[m], lp[m]
    o = np.argsort(t, kind='mergesort'); t, e, le = t[o], e[o], le[o]
    re_ = np.cumsum(np.exp(le)[::-1])[::-1]
    ev = np.unique(t[e == 1]); idx = np.searchsorted(t, ev, side='left')
    dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
    bres[s] = (ev, np.cumsum(dk / re_[idx]))


def S_at(tt):
    out = np.ones(len(C))
    for s in np.unique(st):
        ev, H = bres[s]
        ii = np.searchsorted(ev, tt, side='right') - 1
        He = H[ii] if ii >= 0 else 0.0
        m = st == s
        out[m] = np.exp(-np.exp(lp[m]) * He)
    return out


S5 = S_at(5.0)
q33, q67 = np.quantile(S5[dev], [1 / 3, 2 / 3])
assert round(float(q33), 4) == 0.3793 and round(float(q67), 4) == 0.4756
H5 = -np.log(np.clip(S5, 1e-12, 1))
c_val = float(concordance_index(C.OS_Y.values[~dev], -H5[~dev], C.OS_E.values[~dev]))
print('reproduced validation C:', round(c_val, 4), '| cut-points', round(float(q33), 4), round(float(q67), 4))
assert round(c_val, 4) == 0.6216

coef = pd.DataFrame({'term': M2A, 'description': [LABEL[t] for t in M2A],
                     'coefficient': np.round(be, 4), 'HR': np.round(np.exp(be), 3),
                     'HR_CI_low': np.round(np.exp(cph.confidence_intervals_.loc[M2A].iloc[:, 0].values), 3),
                     'HR_CI_high': np.round(np.exp(cph.confidence_intervals_.loc[M2A].iloc[:, 1].values), 3),
                     'p': cph.summary.loc[M2A, 'p'].values.round(4)})
coef.to_csv(OUT / 'P1_model_coefficients.csv', index=False)
print(coef.to_string(index=False))

base = []
for s in sorted(np.unique(st)):
    ev, H = bres[s]
    ii = np.searchsorted(ev, [1.0, 3.0, 5.0], side='right') - 1
    row = {'stratum_sex_synchrony_Mstage': int(s)}
    for tt, ix in zip([1, 3, 5], ii):
        row[f'baseline_survival_{tt}y_at_reference_covariates'] = round(float(np.exp(-H[ix])) if ix >= 0 else 1.0, 4)
    base.append(row)
pd.DataFrame(base).to_csv(OUT / 'P1_baseline_survival_by_stratum.csv', index=False)

grp = np.where(S5 >= q67, 'Favourable', np.where(S5 >= q33, 'Intermediate', 'Adverse'))
va = ~dev
rows = []
for g in ['Favourable', 'Intermediate', 'Adverse']:
    m = va & (grp == g)
    mt = dev & (grp == g)
    rows.append({'group': g, 'development_n': int(mt.sum()), 'validation_n': int(m.sum()),
                 'predicted_5y_survival_range_validation': f"{S5[m].min():.3f}-{S5[m].max():.3f}",
                 'mean_predicted_5y_validation': round(float(S5[m].mean()), 3)})
pd.DataFrame(rows).to_csv(OUT / 'P1_group_summary.csv', index=False)
print(pd.DataFrame(rows).to_string(index=False))
print('model coefficients written ->', OUT)
