"""Dataset investigation, stage C: can more patients be included?

Compares, on the same step-7 population (26,094 patients):
  (a) complete-case M2a (primary specification; reproduces the v7 result as a check);
  (b) multiple imputation of incomplete T, N and M (10 draws), using covariates only (no outcome), with the
      development-era imputation model applied to validation patients; M2a fitted per draw and pooled (Rubin);
  (c) a model without TNM that uses only variables recorded for more patients;
  (d) the primary model after removing the second copy of each identical-content record pair.
Validation uses operation year >= 2010 and is used only to evaluate fixed models.
Writes F50-F53 to LIVERMET_OUT_DIR/investigation.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v7/investigation'))
OUT.mkdir(parents=True, exist_ok=True)
DAYS = 365.25
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
SEED = 42
TIMES = np.array([5.0])
M_DRAWS = 10

D = pd.read_parquet(WORK / 'investigation_step7.parquet')
X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
R = pd.read_parquet(WORK / 'investigation_rows.parquet').reset_index(drop=True)
assert len(D) == 26094


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


# ---------- covariates for every step-7 patient (rows of D are indexed by the extract row index)
src = D.SRC.values
dgk = serial(X.DGKCOLDT).values[src]; dg = serial(X.LE1DGMETADT).values[src]
DF = pd.DataFrame({'SRC': src, 'ERA': D.ERA.values, 'OS_Y': D.OS_Y.values, 'OS_E': D.OS_E.values,
                   'DEATH': D.DEATH.values, 'T0': D.T0.values, 'TNM': D.TNM.values,
                   'AGE': D.AGE.values, 'MALE': D.MALE.values, 'SYNC': D.SYNC.values,
                   'METS': D.METS.values, 'SIZE': D.SIZE.values, 'CEA': D.CEA.values, 'YEAR': D.YEAR.values})
DF['DFI'] = (pd.to_datetime(dg) - pd.to_datetime(dgk)).days / 30.4375
DF.loc[DF.SYNC == 1, 'DFI'] = 0.0
DF.loc[(DF.DFI < 0) | (pd.to_datetime(dg) > pd.to_datetime(DF['T0'])), 'DFI'] = np.nan
DF['CEA_LOG'] = np.log1p(DF.CEA)
DF['DEV'] = DF.ERA.eq('development')
tmap = {'T1-2': 0, 'T3': 1, 'T4': 2}
nmap = {'N0': 0, 'N1': 1, 'N2': 2}
mmap = {'M0': 0, 'M1': 1}
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def mapped(raw, mp, codes):
    v = pd.Series(raw).astype(object).map(lambda x: mp.get(x, np.nan) if isinstance(x, str) else np.nan)
    return v.map(codes).astype(float).values


DF['T_OBS'] = mapped(X.STADET.values[src], TMAP, tmap)
DF['N_OBS'] = mapped(X.STADEN.values[src], NMAP, nmap)
DF['M_OBS'] = mapped(X.STADEM.values[src], MMAP, mmap)
# second and later copies of an identical-content record, within the step-7 population
hash_src = R.ROW_HASH.values[src]
DF['DUP2'] = pd.Series(hash_src).duplicated(keep='first').values
assert DF.TNM.eq(DF[['T_OBS', 'N_OBS', 'M_OBS']].notna().all(axis=1)).all()


def breslow(T, E, lpe, lpl, st):
    out = {}
    for s in np.unique(st):
        m = st == s
        t, e, le = T[m], E[m], lpe[m]
        o = np.argsort(t, kind='mergesort'); t, e, le = t[o], e[o], le[o]
        re_ = np.cumsum(np.exp(le)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        out[s] = (ev, np.cumsum(dk / re_[idx]))
    return out


def predict_S5(bres, Xm, st, be):
    xe = Xm @ be
    S = np.ones(len(Xm))
    for s in np.unique(st):
        m = st == s
        ev, H = bres[s]
        ii = np.searchsorted(ev, TIMES, side='right') - 1
        He = np.where(ii >= 0, H[np.clip(ii, 0, None)], 0.0)
        S[m] = np.exp(-np.exp(xe[m]) * He[0])
    return S


def add_covariates(F, tnm_t, tnm_n, tnm_m):
    """F: frame with DEV, DFI, METS, SIZE, AGE, MALE, SYNC; TNM given as ordinal arrays (nan = unknown)."""
    G = F.copy()
    G['T_ORD'] = tnm_t; G['N_ORD'] = tnm_n; G['M_ORD'] = tnm_m
    dev = G.DEV.values
    for c in ['DFI', 'METS', 'SIZE']:
        G[c + '_NR'] = G[c].isna().astype(float)
    for c in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE']:
        G[c + '_F'] = G[c].fillna(G.loc[dev, c].median())
    G['AGE10_F'] = G.AGE_F / 10; G['DFI12_F'] = G.DFI_F / 12; G['SIZE10_F'] = G.SIZE_F / 10
    G['T3'] = (G.T_ORD == 1).astype(float); G['T4'] = (G.T_ORD == 2).astype(float)
    G['N1'] = (G.N_ORD == 1).astype(float); G['N2'] = (G.N_ORD == 2).astype(float)
    G['M1'] = (G.M_ORD == 1).astype(float)
    G['STRATUM'] = G.MALE_F.round().astype(int) * 2 + G.SYNC_F.round().astype(int)
    G['STRAT_M'] = G.STRATUM * 2 + G.M1.astype(int)
    return G


M2A = ['T3', 'T4', 'N1', 'N2', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
NOTNM = ['AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']


def fit_pred(G, cols, strat, train):
    cph = CoxPHFitter().fit(G.loc[train, cols + [strat, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[strat])
    be = cph.params_[cols].values; se = cph.standard_errors_[cols].values
    Xm = G[cols].astype(float).values; st = G[strat].values
    bres = breslow(G.OS_Y.values[train], G.OS_E.values[train], Xm[train] @ be, Xm[train] @ be, st[train])
    S5 = predict_S5(bres, Xm, st, be)
    return be, se, S5


def cstat(G, risk, mask):
    m = mask
    return round(float(concordance_index(G.OS_Y.values[m], -risk[m], G.OS_E.values[m])), 4)


def rubin(bs, ses):
    bs = np.array(bs); ses = np.array(ses)
    qbar = bs.mean(axis=0); W = (ses ** 2).mean(axis=0); B = bs.var(axis=0, ddof=1)
    T = W + (1 + 1 / len(bs)) * B
    return qbar, np.sqrt(T)


# ---------- (a) complete-case M2a (check against v7: validation C 0.6216 on TNM-complete validation)
# covariate medians come from TNM-complete development patients, as in the primary model
cc_src = DF[DF.TNM].reset_index(drop=True)
cc = add_covariates(cc_src, cc_src.T_OBS.values, cc_src.N_OBS.values, cc_src.M_OBS.values)
train_cc = cc.DEV.values
be_cc, se_cc, S5_cc = fit_pred(cc, M2A, 'STRAT_M', train_cc)
C_cc = cstat(cc, -np.log(np.clip(S5_cc, 1e-12, 1)), ~train_cc)
print('complete-case M2a validation C (should be 0.6216):', C_cc, '| n valid', int((~train_cc).sum()))

# ---------- (b) multiple imputation of T, N, M using covariates only (development-era imputation model)
imp_cols = ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE', 'CEA_LOG', 'YEAR', 'T_OBS', 'N_OBS', 'M_OBS']
DF['CEA_LOG'] = np.log1p(DF.CEA)
Z = DF[imp_cols].astype(float).values
fit_rows = DF.DEV.values
draw_be, draw_se, draw_S5_all, draw_T, draw_N, draw_M = [], [], [], [], [], []
draw_C_all, draw_C_tnm = [], []
dev = DF.DEV.values
for m in range(M_DRAWS):
    imp = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + m)
    imp.fit(Z[fit_rows])
    Zi = imp.transform(Z)
    Tm = np.where(DF.T_OBS.notna(), DF.T_OBS, np.clip(np.round(Zi[:, imp_cols.index('T_OBS')]), 0, 2))
    Nm = np.where(DF.N_OBS.notna(), DF.N_OBS, np.clip(np.round(Zi[:, imp_cols.index('N_OBS')]), 0, 2))
    Mm = np.where(DF.M_OBS.notna(), DF.M_OBS, np.clip(np.round(Zi[:, imp_cols.index('M_OBS')]), 0, 1))
    G = add_covariates(DF, Tm, Nm, Mm)
    be, se, S5 = fit_pred(G, M2A, 'STRAT_M', G.DEV.values)
    draw_be.append(be); draw_se.append(se)
    risk = -np.log(np.clip(S5, 1e-12, 1))
    draw_C_all.append(cstat(G, risk, ~G.DEV.values))
    draw_C_tnm.append(cstat(G, risk, (~G.DEV.values) & G.TNM.values))
    draw_T.append(Tm); draw_N.append(Nm); draw_M.append(Mm)
pooled_b, pooled_se = rubin(draw_be, draw_se)
mi_rows = []
for j, term in enumerate(M2A):
    if term in ['T3', 'T4', 'N1', 'N2']:
        hr = np.exp(pooled_b[j]); lo = np.exp(pooled_b[j] - 1.96 * pooled_se[j]); hi = np.exp(pooled_b[j] + 1.96 * pooled_se[j])
        mi_rows.append({'term': term, 'HR_multiple_imputation': round(hr, 3), 'CI_low': round(lo, 3), 'CI_high': round(hi, 3)})
hr_mi = pd.DataFrame(mi_rows)
hr_cc = pd.DataFrame([{'term': t, 'HR_complete_case': round(float(np.exp(be_cc[M2A.index(t)])), 3)} for t in ['T3', 'T4', 'N1', 'N2']])
hr_tab = hr_cc.merge(hr_mi, on='term')
hr_tab.to_csv(OUT / 'F50_TNM_hazard_ratios_complete_case_vs_imputed.csv', index=False)
print(hr_tab.to_string(index=False))

# ---------- (c) model without TNM (variables recorded for all patients)
G_all = add_covariates(DF, DF.T_OBS.values, DF.N_OBS.values, DF.M_OBS.values)
be_nt, se_nt, S5_nt = fit_pred(G_all, NOTNM, 'STRATUM', G_all.DEV.values)
risk_nt = -np.log(np.clip(S5_nt, 1e-12, 1))
C_nt_all = cstat(G_all, risk_nt, ~G_all.DEV.values)
C_nt_tnm = cstat(G_all, risk_nt, (~G_all.DEV.values) & G_all.TNM.values)

# ---------- (d) duplicates removed (second copy of each identical pair dropped)
dd = DF[~DF.DUP2].reset_index(drop=True)
dd = dd[dd.TNM].reset_index(drop=True)
Gd = add_covariates(dd, dd.T_OBS.values, dd.N_OBS.values, dd.M_OBS.values)
be_d, se_d, S5_d = fit_pred(Gd, M2A, 'STRAT_M', Gd.DEV.values)
C_d = cstat(Gd, -np.log(np.clip(S5_d, 1e-12, 1)), ~Gd.DEV.values)
n_dup_tnm = int((DF.DUP2 & DF.TNM).sum())
n_dup_dev_tnm = int((DF.DUP2 & DF.TNM & DF.DEV).sum())

# ---------- summary
tnm_all_valid = DF[(~DF.DEV)]
summary = pd.DataFrame([
    {'analysis': '(a) complete-case M2a, TNM-complete validation patients (v7 primary check)',
     'development_n': int(train_cc.sum()), 'validation_n': int((~train_cc).sum()),
     'validation_C': C_cc, 'note': 'reproduces v7 F02 (0.6216)'},
    {'analysis': '(b) M2a with multiple imputation of T, N, M (10 draws, covariates only), all validation patients',
     'development_n': int(G_all.DEV.sum()), 'validation_n': int((~G_all.DEV).sum()),
     'validation_C': round(float(np.mean(draw_C_all)), 4),
     'note': f'range over draws {min(draw_C_all):.4f}-{max(draw_C_all):.4f}; imputed TNM cannot be validated'},
    {'analysis': '(b) M2a with multiple imputation, TNM-complete validation patients only',
     'development_n': int(G_all.DEV.sum()), 'validation_n': int(((~G_all.DEV) & G_all.TNM).sum()),
     'validation_C': round(float(np.mean(draw_C_tnm)), 4),
     'note': f'range over draws {min(draw_C_tnm):.4f}-{max(draw_C_tnm):.4f}'},
    {'analysis': '(c) model without TNM (age, sex, synchrony, interval, metastasis count and size), all validation patients',
     'development_n': int(G_all.DEV.sum()), 'validation_n': int((~G_all.DEV).sum()),
     'validation_C': C_nt_all, 'note': 'uses variables recorded for all patients'},
    {'analysis': '(c) model without TNM, TNM-complete validation patients (identical patients to (a))',
     'development_n': int(G_all.DEV.sum()), 'validation_n': int(((~G_all.DEV) & G_all.TNM).sum()),
     'validation_C': C_nt_tnm, 'note': 'same patients as (a)'},
    {'analysis': '(d) complete-case M2a after removing second copies of identical records',
     'development_n': int(Gd.DEV.sum()), 'validation_n': int((~Gd.DEV).sum()), 'validation_C': C_d,
     'note': f'{n_dup_tnm} duplicate second copies in the TNM-complete cohort ({n_dup_dev_tnm} development)'},
])
summary.to_csv(OUT / 'F51_model_comparison_including_more_patients.csv', index=False)
print(summary.to_string(index=False))

# imputed-TNM distribution vs observed (validation and development), first draw
first_draw = pd.DataFrame({'group': np.where(DF.TNM, 'observed (TNM complete)', 'imputed (TNM incomplete)'),
                           'T3_or_more_pct': 100 * (np.where(DF.TNM, DF.T_OBS, draw_T[0]) >= 1).astype(float),
                           'T4_pct': 100 * (np.where(DF.TNM, DF.T_OBS, draw_T[0]) == 2).astype(float),
                           'N_positive_pct': 100 * (np.where(DF.TNM, DF.N_OBS, draw_N[0]) >= 1).astype(float),
                           'M1_pct': 100 * (np.where(DF.TNM, DF.M_OBS, draw_M[0]) == 1).astype(float)})
first_draw.groupby('group').mean(numeric_only=True).round(1).reset_index().to_csv(OUT / 'F52_imputed_vs_observed_TNM_distribution.csv', index=False)
print(first_draw.groupby('group').mean(numeric_only=True).round(1).to_string())
print('stage C done ->', OUT)
