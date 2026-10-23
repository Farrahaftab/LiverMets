"""Feasibility assessment (no new modelling, no change to locked v7 outputs).

Uses the locked M2a specification and training-only tertile cut-points, reproduced exactly (validation C 0.6216)
by the audit code. Reports, for the validation cohort only as evaluation:
  (1) evaluable patients, events, at-risk counts and observed vs predicted survival at 1, 3 and 5 years;
  (2) centre- and country-level structure for centre-held-out validation feasibility;
  (3) group-level event counts at each horizon.
Writes to LIVERMET_OUT_DIR/feasibility (default results/final_v7/feasibility). Validation outcomes are used only to
describe performance of the fixed model; nothing is tuned on them.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v7/feasibility'))
OUT.mkdir(parents=True, exist_ok=True)
DAYS = 365.25
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
MAXFU = 15.0
HORIZONS = [1.0, 3.0, 5.0]
TB_TIMES = np.concatenate([[1.0, 3.0, 5.0], np.arange(1.5, 7.5, 0.5)])

X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
R = pd.read_parquet(WORK / 'investigation_rows.parquet').reset_index(drop=True)
D = pd.read_parquet(WORK / 'investigation_step7.parquet')
assert len(D) == 26094


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


src = D.SRC.values
dgk = serial(X.DGKCOLDT).values[src]; dg = serial(X.LE1DGMETADT).values[src]
F = pd.DataFrame({'SRC': src, 'ERA': D.ERA.values, 'DEV': D.ERA.eq('development').values, 'TNM': D.TNM.values,
                  'OS_Y': D.OS_Y.values, 'OS_E': D.OS_E.values, 'DEATH': D.DEATH.values, 'OS_DAYS': D.OS_DAYS.values,
                  'T0': D.T0.values, 'AGE': D.AGE.values, 'MALE': D.MALE.values, 'SYNC': D.SYNC.values,
                  'METS': D.METS.values, 'SIZE': D.SIZE.values, 'CEA': D.CEA.values, 'COUNTRY': D.COUNTRY.values,
                  'SITE': D.SITE.values})
F['DFI'] = (pd.to_datetime(dg) - pd.to_datetime(dgk)).days / 30.4375
F.loc[F.SYNC == 1, 'DFI'] = 0.0
F.loc[(F.DFI < 0) | (pd.to_datetime(dg) > pd.to_datetime(F['T0'])), 'DFI'] = np.nan
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}
T_MAP = {'T1-2': 0, 'T3': 1, 'T4': 2}; N_MAP = {'N0': 0, 'N1': 1, 'N2': 2}; M_MAP = {'M0': 0, 'M1': 1}


def gmap(vals, mp):
    return pd.Series(vals).astype(object).map(lambda x: mp.get(x, np.nan) if isinstance(x, str) else np.nan).values


F['T_ORD'] = pd.Series(gmap(D.T_RAW.values, TMAP)).map(T_MAP).values
F['N_ORD'] = pd.Series(gmap(D.N_RAW.values, NMAP)).map(N_MAP).values
F['M_ORD'] = pd.Series(gmap(D.M_RAW.values, MMAP)).map(M_MAP).values


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
VAL = ~TRN
cph = CoxPHFitter().fit(COH.loc[TRN, M2A + ['STRAT_M', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRAT_M'])
be = cph.params_[M2A].values
Xm = COH[M2A].astype(float).values
st = COH.STRAT_M.values
lp = Xm @ be


def breslow_at(T, E, lpv, stv, times):
    """Stratified Breslow baseline (training only), returns S(t) for every patient at the requested times."""
    out = np.ones((len(lpv), len(times)))
    for s in np.unique(stv):
        mt = (stv == s) & TRN
        t, e, le = T[mt], E[mt], lpv[mt]
        o = np.argsort(t, kind='mergesort'); t, e, le = t[o], e[o], le[o]
        re_ = np.cumsum(np.exp(le)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        H = np.cumsum(dk / re_[idx])
        ii = np.searchsorted(ev, times, side='right') - 1
        He = np.where(ii >= 0, H[np.clip(ii, 0, None)], 0.0)
        ms = stv == s
        out[ms] = np.exp(-np.exp(lpv[ms, None]) * He[None, :])
    return out


S_t = breslow_at(COH.OS_Y.values, COH.OS_E.values, lp, st, np.array(TB_TIMES))
S5 = S_t[:, list(TB_TIMES).index(5.0)]
H5 = -np.log(np.clip(S5, 1e-12, 1))
from lifelines.utils import concordance_index  # noqa: E402
C_val = round(float(concordance_index(COH.OS_Y.values[VAL], -H5[VAL], COH.OS_E.values[VAL])), 4)
print('reproduced validation C (locked v7 = 0.6216):', C_val)
q33, q67 = np.quantile(S5[TRN], [1 / 3, 2 / 3])
GRP = np.where(S5 >= q67, 'Favourable', np.where(S5 >= q33, 'Intermediate', 'Adverse'))
assert round(float(q33), 4) == 0.3793 and round(float(q67), 4) == 0.4756

# ------------------------------------------------------------- (1) horizon feasibility, validation cohort
T = COH.OS_Y.values[VAL]; E = COH.OS_E.values[VAL]
rows = []
for h in HORIZONS:
    k = KaplanMeierFitter().fit(T, E)
    evaluable = (T >= h) | ((E == 1) & (T < h))
    km_h = float(k.survival_function_at_times(h).iloc[0])
    ci = k.confidence_interval_survival_function_
    lo = float(ci.iloc[np.searchsorted(ci.index.values, h, side='right') - 1, 0])
    hi = float(ci.iloc[np.searchsorted(ci.index.values, h, side='right') - 1, 1])
    pred = float(S_t[VAL, list(TB_TIMES).index(h)].mean())
    rows.append({'horizon_years': int(h), 'validation_n': int(VAL.sum()),
                 'evaluable_n': int(evaluable.sum()), 'pct_evaluable': round(100 * evaluable.mean(), 1),
                 'deaths_before_horizon': int(((T < h) & (E == 1)).sum()),
                 'at_risk_at_horizon': int((T >= h).sum()),
                 'mean_predicted_survival': round(pred, 3), 'observed_KM_survival': round(km_h, 3),
                 'observed_KM_95CI': f'{lo:.3f}-{hi:.3f}', 'O_over_E': round(km_h / pred, 3),
                 'sparse_flag_under_50_at_risk': bool((T >= h).sum() < 50)})
hz = pd.DataFrame(rows)
hz.to_csv(OUT / 'G01_horizon_feasibility_validation.csv', index=False)
print(hz.to_string(index=False))

# group-level events by horizon (validation), using the locked groups
grp_rows = []
for g in ['Favourable', 'Intermediate', 'Adverse']:
    m = GRP[VAL] == g
    for h in HORIZONS:
        grp_rows.append({'group': g, 'horizon_years': int(h), 'n': int(m.sum()),
                         'deaths_before_horizon': int(((T[m] < h) & (E[m] == 1)).sum()),
                         'at_risk_at_horizon': int((T[m] >= h).sum())})
pd.DataFrame(grp_rows).to_csv(OUT / 'G02_group_events_by_horizon_validation.csv', index=False)
print(pd.DataFrame(grp_rows).to_string(index=False))

# calibration precision at each horizon: bootstrap of O/E (evaluation only; no refit)
rng = np.random.default_rng(42)
cal_rows = []
for h in HORIZONS:
    idx_v = np.where(VAL)[0]
    ratios = []
    for _ in range(300):
        b = rng.choice(idx_v, len(idx_v), replace=True)
        kb = KaplanMeierFitter().fit(COH.OS_Y.values[b], COH.OS_E.values[b])
        ob = float(kb.survival_function_at_times(h).iloc[0])
        pb = float(S_t[b, list(TB_TIMES).index(h)].mean())
        ratios.append(ob / pb)
    cal_rows.append({'horizon_years': int(h), 'O_over_E_bootstrap_2.5pct': round(float(np.percentile(ratios, 2.5)), 3),
                     'O_over_E_bootstrap_97.5pct': round(float(np.percentile(ratios, 97.5)), 3)})
pd.DataFrame(cal_rows).to_csv(OUT / 'G03_calibration_precision_by_horizon.csv', index=False)
print(pd.DataFrame(cal_rows).to_string(index=False))

# ------------------------------------------------------------- (2) centre and country structure
site_t = COH.assign(EVENT=COH.OS_E, VALID=VAL).groupby('SITE').agg(
    n_tnm=('TNM', 'size'), dev_n=('DEV', lambda s: int(s.sum())), val_n=('DEV', lambda s: int((~s).sum())),
    )
ev_val = COH[VAL].groupby('SITE').OS_E.sum()
site_t['val_events'] = ev_val.reindex(site_t.index).fillna(0).astype(int)
site_t['both_eras'] = (site_t.dev_n > 0) & (site_t.val_n > 0)
cty_t = COH.groupby('COUNTRY').agg(n_tnm=('TNM', 'size'))
rows_s = []
for thr in [20, 50, 100]:
    rows_s.append({'threshold_TNM_complete_patients_per_unit': thr,
                   'sites_meeting_threshold': int((site_t.n_tnm >= thr).sum()),
                   'sites_with_validation_events_20plus': int(((site_t.n_tnm >= thr) & (site_t.val_events >= 20)).sum()),
                   'patients_in_qualifying_sites_pct': round(100 * site_t.n_tnm[site_t.n_tnm >= thr].sum() / site_t.n_tnm.sum(), 1),
                   'countries_meeting_threshold': int((cty_t.n_tnm >= thr).sum())})
pd.DataFrame(rows_s).to_csv(OUT / 'G04_centre_held_out_feasibility.csv', index=False)
print(pd.DataFrame(rows_s).to_string(index=False))
site_t.reset_index().to_csv(OUT / 'G05_site_structure_tnm_complete.csv', index=False)
print('sites with TNM-complete patients:', len(site_t), '| median per site:', int(site_t.n_tnm.median()),
      '| sites in both eras:', int(site_t.both_eras.sum()))
print('feasibility done ->', OUT)
