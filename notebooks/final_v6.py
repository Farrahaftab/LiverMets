"""Final v6 verification (candidate analysis for locking the notebook and manuscript).

Surgery-origin overall survival, TNM-complete modelling cohort (report rules; 15th-of-month convention for partial
operation dates). Development uses training-era patients only (operation year <= 2009); temporal validation
(>= 2010) is used only to evaluate fixed models, cut-points and rules. No model is chosen by C-index.

Pre-specified model-selection rule (applied to training-only PH diagnostics):
  candidates in order of complexity: M1 (stratified by sex x synchronous presentation, M-stage as covariate),
  M2a (strata = sex x synchronous x M-stage, M-stage removed as covariate),
  M2b (as M1, with a time-varying M-stage coefficient split at 2 years).
  Choose the first candidate whose constant-term Schoenfeld tests all have p > 0.05 in training.
"""
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, CoxTimeVaryingFitter, KaplanMeierFitter, NelsonAalenFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test, proportional_hazard_test
from lifelines.utils import concordance_index, median_survival_times, to_episodic_format
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import cohen_kappa_score
from sksurv.metrics import brier_score, cumulative_dynamic_auc, integrated_brier_score

warnings.filterwarnings('ignore')
T0 = time.time()
SEED = 42
RNG = np.random.default_rng(SEED)
W = Path(os.environ['LIVERMET_WORK_DIR'])
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'final_v6'
RES.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
MAXFU = 15.0
TB = np.arange(1.0, 7.5, 0.5)
CUT = 2.0
DAY_PRIMARY = 15
CENSOR = pd.Timestamp('2020-07-04')


def log(msg):
    print(f'[{time.time()-T0:6.0f}s] {msg}', flush=True)


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


def ymd(v2, base, day_fill):
    y = num(v2[base + '_Y']); m = num(v2[base + '_M']); d = num(v2[base + '_D'])
    if day_fill == 'last':
        import calendar
        last = pd.Series([calendar.monthrange(int(a), int(b))[1] if (a == a and b == b) else np.nan for a, b in zip(y, m)], index=y.index)
        dd = d.fillna(last)
    else:
        dd = d.fillna(day_fill)
    return pd.to_datetime(dict(year=y, month=m, day=dd), errors='coerce'), d.isna() & y.notna() & m.notna()


def save(df, name):
    df.to_csv(RES / f'{name}.csv', index=False)
    return df


# ================================================================== load aligned extracts
v1 = pd.read_parquet(W / 'combined_extract.parquet')
v2 = pd.read_parquet(W / 'combined_extract_v2.parquet')
v3 = pd.read_parquet(W / 'combined_extract_v3_ops.parquet')
assert len(v1) == len(v2) == len(v3) == 29565
assert (v1.SOURCE_EXCEL_ROW.values == v2.SOURCE_EXCEL_ROW.values).all() and (v1.SOURCE_EXCEL_ROW.values == v3.SOURCE_EXCEL_ROW.values).all()
log('extracts aligned')
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(s, m):
    return s.astype(object).map(lambda x: m.get(x, np.nan) if isinstance(x, str) else np.nan)


INC = v1.CINCLUSION.eq('Yes')
HEP = v1.LE1HEPATECTYN_F1.eq('Yes')
PST_ANY = v1.PATSTATC.notna()
PST = v1.PATSTATC.isin(['Alive', 'Deceased', 'Lost to follow-up'])
DEATH = v1.PATSTATC.eq('Deceased')
LAST_SER = serial(v2.LASTNDTC)
LAST_FU = pd.concat([serial(v2[f'LASTNDT_F{i}']) for i in range(1, 8)], axis=1).max(axis=1)
TNM = pd.concat([gmap(v1.STADET, TMAP), gmap(v1.STADEN, NMAP), gmap(v1.STADEM, MMAP)], axis=1).notna().all(axis=1)
T_G = gmap(v1.STADET, TMAP); N_G = gmap(v1.STADEN, NMAP); M_G = gmap(v1.STADEM, MMAP)
BIRTH = serial(v2.BIRTHDT)
DGK = serial(v2.DGKCOLDT)
DG = serial(v2.LE1DGMETADT)
MALE = v1.GENDER.map({'Male': 1.0, 'Female': 0.0})
SYNC = v1.LE1METASYNCYN.map({'Yes': 1.0, 'No': 0.0})
METS = num(v1.LE1NBMETAHEPNUM).where(lambda x: (x >= 1) & (x <= 50))
SIZE = num(v1.LE1HEPMETASIZENUM).where(lambda x: (x > 0) & (x <= 300))
CEA = num(v1.LE1PREHEPCEA_F1).where(lambda x: (x >= 0) & (x <= 40000))


def build(day_fill):
    """Report-consistent surgery-origin OS cohort and covariates for one partial-date convention."""
    op_ser = serial(v2.LE1OPERDT_F1)
    op_ym, partial = ymd(v2, 'LE1OPERDT_F1', day_fill)
    op = op_ser.fillna(op_ym)
    s1 = pd.Series(True, index=v1.index)
    s4 = INC & HEP & op_ym.notna()
    s5 = s4 & PST_ANY & LAST_SER.notna()
    s6 = s5 & (LAST_SER >= op)
    fu = (LAST_SER - op).dt.days
    s7 = s6 & ((fu > 0) | DEATH)
    flow = {'1 registry': int(s1.sum()), '2 CINCLUSION=Yes': int((INC).sum()), '3 hepatectomy': int((INC & HEP).sum()),
            '4 operation date (year+month)': int(s4.sum()), '5 status and last-news': int(s5.sum()),
            '6 chronology': int(s6.sum()), '7 positive follow-up or death': int(s7.sum())}
    d = pd.DataFrame(index=v1.index[s7])
    d['T0'] = op[s7]
    d['PARTIAL'] = partial[s7] & op_ser[s7].isna()
    d['LAST'] = LAST_SER[s7]
    d['DEATH'] = DEATH[s7].astype(float)
    d['OS_DAYS'] = (d['LAST'] - d['T0']).dt.days
    d['T_GRP'] = T_G[s7]; d['N_GRP'] = N_G[s7]; d['M_GRP'] = M_G[s7]
    d['TNM'] = d[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)
    d['AGE'] = (d['T0'] - BIRTH[s7]).dt.days / DAYS
    d.loc[(d.AGE < 18) | (d.AGE > 100), 'AGE'] = np.nan
    d['MALE'] = MALE[s7]; d['SYNC'] = SYNC[s7]; d['METS'] = METS[s7]; d['SIZE'] = SIZE[s7]; d['CEA'] = CEA[s7]
    d['DFI'] = (DG[s7] - DGK[s7]).dt.days / 30.4375
    d.loc[d.SYNC == 1, 'DFI'] = 0.0
    d.loc[(d.DFI < 0) | (DG[s7] > d['T0']), 'DFI'] = np.nan      # interval predictor only if known at time zero
    d['ERA'] = np.where(d['T0'].dt.year <= 2009, 'train', 'valid')
    d['T3'] = (d.T_GRP == 'T3').astype(float).where(d.T_GRP.notna())
    d['T4'] = (d.T_GRP == 'T4').astype(float).where(d.T_GRP.notna())
    d['N1'] = (d.N_GRP == 'N1').astype(float).where(d.N_GRP.notna())
    d['N2'] = (d.N_GRP == 'N2').astype(float).where(d.N_GRP.notna())
    d['M1'] = (d.M_GRP == 'M1').astype(float).where(d.M_GRP.notna())
    # deaths on the operation date (report step 7 includes death): time set to half a day so episodes are defined
    d['OS_Y_raw'] = np.where((d.OS_DAYS <= 0) & (d.DEATH == 1), 0.5, d.OS_DAYS) / DAYS
    d['OS_Y'] = np.minimum(d.OS_Y_raw, MAXFU)
    d['OS_E'] = np.where(d.OS_Y_raw > MAXFU, 0.0, d.DEATH)
    d['LAST_FU'] = LAST_FU[s7]
    return d, flow, op_ser[s7].isna() & partial[s7]


# ================================================================== day-convention comparison (cohort level)
flows, cohorts = {}, {}
for lab, df_ in [('first day (1st)', 1), ('mid-month (15th, primary)', DAY_PRIMARY), ('month-end', 'last')]:
    d_, fl, _ = build(df_)
    flows[lab] = fl
    cohorts[lab] = d_
    log(f'{lab}: OS cohort {len(d_):,}, TNM-complete {int(d_.TNM.sum()):,}')
flow_tab = pd.DataFrame(flows).T
flow_report = {'1 registry': 29565, '2 CINCLUSION=Yes': 28979, '3 hepatectomy': 26677, '4 operation date (year+month)': 26592,
               '5 status and last-news': 26271, '6 chronology': 26186, '7 positive follow-up or death': 26094}
flow_tab.loc['report (2026)'] = pd.Series(flow_report)
save(flow_tab.T.reset_index().rename(columns={'index': 'step'}), 'F01_flow_by_day_convention')
print(flow_tab.T.to_string())

D = cohorts['mid-month (15th, primary)']
M = D[D.TNM].copy()
M['SRC'] = M.index
M = M.reset_index(drop=True)
M['ID_'] = np.arange(len(M))
M['ERA_TRAIN'] = (M.ERA == 'train').values
trm = (M.ERA == 'train').values
vam = (M.ERA == 'valid').values
for col in ['DFI', 'METS', 'SIZE']:
    M[col + '_NR'] = M[col].isna().astype(float)
for col in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE']:
    med = M.loc[trm, col].median()
    M[col + '_F'] = M[col].fillna(med)
M['AGE10_F'] = M.AGE_F / 10; M['DFI12_F'] = M.DFI_F / 12; M['SIZE10_F'] = M.SIZE_F / 10
M['MALE_B'] = M.MALE_F.round().astype(int); M['SYNC_B'] = M.SYNC_F.round().astype(int)
M['STRATUM'] = M.MALE_B * 2 + M.SYNC_B
M['STRAT_M'] = M.STRATUM * 2 + M.M1.astype(int)          # sex x synchronous x M-stage (M2a)
M['CEA_LOG'] = np.log1p(M.CEA)
n_tr, n_va = int(trm.sum()), int(vam.sum())
log(f'primary modelling cohort: train {n_tr:,} (deaths {int(M.OS_E[trm].sum()):,}), valid {n_va:,} (deaths {int(M.OS_E[vam].sum()):,})')
Ttr, Etr = M.OS_Y.values[trm], M.OS_E.values[trm]
Tva, Eva = M.OS_Y.values[vam], M.OS_E.values[vam]
CORE_M1 = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
CORE_M2A = [c for c in CORE_M1 if c != 'M1']
PREOP_ONLY = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'DFI_NR']   # excludes metastasis count and size


# ================================================================== piecewise Breslow (handles stratified and time-varying models)
def breslow(T, E, lpe, lpl, st, cut):
    out = {}
    for s in np.unique(st):
        m = st == s
        t, e, le, ll = T[m], E[m], lpe[m], lpl[m]
        o = np.argsort(t, kind='mergesort'); t, e, le, ll = t[o], e[o], le[o], ll[o]
        re_ = np.cumsum(np.exp(le)[::-1])[::-1]; rl_ = np.cumsum(np.exp(ll)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        late = ev >= cut
        dH = dk / np.where(late, rl_[idx], re_[idx])
        out[s] = (ev, np.cumsum(np.where(late, 0.0, dH)), np.cumsum(np.where(late, dH, 0.0)))
    return out


def predict_S(bres, X, st, be, bl, times):
    xe = X @ be; xl = X @ bl
    S = np.ones((len(X), len(times))); H5 = np.zeros(len(X))
    for s in np.unique(st):
        m = st == s
        ev, He, Hl = bres[s]
        ii = np.searchsorted(ev, times, side='right') - 1
        Te = np.where(ii >= 0, He[np.clip(ii, 0, None)], 0.0)
        Tl = np.where(ii >= 0, Hl[np.clip(ii, 0, None)], 0.0)
        H = np.exp(xe[m, None]) * Te[None, :] + np.exp(xl[m, None]) * Tl[None, :]
        S[m] = np.exp(-H)
    return S


TIMES = np.concatenate([[3.0, 5.0], TB])


class Model:
    """Fitted model with a common prediction interface (survival at TIMES for any patient)."""

    def __init__(self, name, cols, strat_col, tv_cols=()):
        self.name, self.cols, self.strat_col, self.tv = name, cols, strat_col, tv_cols
        if tv_cols:
            base = M.loc[trm, ['OS_Y', 'OS_E', 'ID_', strat_col] + cols].copy()
            base['ID_'] = np.arange(len(base))
            base = base.rename(columns={'OS_E': 'E'})
            long = to_episodic_format(base, duration_col='OS_Y', event_col='E', id_col='ID_', time_gaps=CUT)
            for x in tv_cols:
                long[x + '_late'] = long[x] * (long['start'] >= CUT).astype(float)
            feats = cols + [x + '_late' for x in tv_cols]
            self.ctv = CoxTimeVaryingFitter().fit(long[['ID_', 'start', 'stop', 'E'] + feats + [strat_col]],
                                                  id_col='ID_', event_col='E', start_col='start', stop_col='stop', strata=[strat_col])
            sm = self.ctv.summary
            self.be = np.array([sm.loc[x, 'coef'] for x in cols])
            self.bl = self.be.copy()
            for x in tv_cols:
                self.bl[cols.index(x)] = sm.loc[x, 'coef'] + sm.loc[x + '_late', 'coef']
            self.cut = CUT
        else:
            self.cph = CoxPHFitter().fit(M.loc[trm, cols + [strat_col, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[strat_col])
            self.be = self.cph.params_[cols].values
            self.bl = self.be.copy()
            self.cut = 1e9
        X = M[cols].astype(float).values
        st = M[strat_col].values
        self.bres = breslow(Ttr, Etr, X[trm] @ self.be, X[trm] @ self.bl, st[trm], self.cut)
        self.S = predict_S(self.bres, X, st, self.be, self.bl, TIMES)

    def ph_table(self):
        if self.tv:
            return None
        d = M.loc[trm, self.cols + [self.strat_col, 'OS_Y', 'OS_E']]
        res = proportional_hazard_test(self.cph, d, time_transform='rank').summary.reset_index()
        res.columns = ['term'] + list(res.columns[1:])
        return res

    def hr_table(self):
        if self.tv:
            s = self.ctv.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
        else:
            s = self.cph.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
        s.columns = ['term', 'coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
        return s


def metrics_for(model):
    S = model.S
    y_tr = Surv_(Etr, Ttr); y_va = Surv_(Eva, Tva)
    H5 = -np.log(np.clip(S[:, 1], 1e-12, 1))
    out = {'model': model.name,
           'train_C': round(float(concordance_index(Ttr, -H5[trm], Etr)), 4),
           'valid_C': round(float(concordance_index(Tva, -H5[vam], Eva)), 4)}
    C_bs = []
    for _ in range(300):
        b = RNG.integers(0, n_va, n_va)
        C_bs.append(concordance_index(Tva[b], -H5[vam][b], Eva[b]))
    lo, hi = np.percentile(C_bs, [2.5, 97.5])
    out['valid_C_95CI'] = f'{lo:.3f}-{hi:.3f}'
    auc, _ = cumulative_dynamic_auc(y_tr, y_va, H5[vam], np.array([1.0, 3.0, 5.0]))
    for t, a in zip([1, 3, 5], auc):
        out[f'tAUC_{t}y'] = round(float(a), 3)
    _, bs = brier_score(y_tr, y_va, S[vam][:, 2:], TB)
    for t in [1.0, 3.0, 5.0]:
        out[f'Brier_{int(t)}y'] = round(float(bs[list(TB).index(t)]), 4)
    out['IBS_1_7y'] = round(float(integrated_brier_score(y_tr, y_va, S[vam][:, 2:], TB)), 4)
    o5 = float(KaplanMeierFitter().fit(Tva, Eva).survival_function_at_times(5).iloc[0])
    out['valid_observed_S5'] = round(o5, 3)
    out['valid_mean_predicted_S5'] = round(float(S[vam, 1].mean()), 3)
    out['valid_OE_5y'] = round(o5 / float(S[vam, 1].mean()), 3)
    out['valid_calib_slope_5y'] = round(float(CoxPHFitter().fit(pd.DataFrame({'T': Tva, 'E': Eva, 'lp': np.log(-np.log(np.clip(S[vam, 1], 1e-6, 1 - 1e-6)))}), 'T', 'E').params_['lp']), 3)
    return out


def Surv_(E, T):
    from sksurv.util import Surv
    return Surv.from_arrays(E.astype(bool), T)


# ================================================================== M-stage candidates on identical patients
log('fitting M-stage candidates')
models = {}
models['M1'] = Model('M1 stratified sex x synchronous (M-stage covariate)', CORE_M1, 'STRATUM')
models['M2a'] = Model('M2a stratified sex x synchronous x M-stage', CORE_M2A, 'STRAT_M')
models['M2b'] = Model('M2b stratified sex x synchronous, time-varying M-stage (2-year split)', CORE_M1, 'STRATUM', tv_cols=('M1',))
perf = pd.DataFrame([metrics_for(m) for m in models.values()])
save(perf, 'F02_M_stage_candidates_identical_patients')
print(perf.to_string(index=False))

ph_rows = []
for key in ['M1', 'M2a']:
    tab = models[key].ph_table()
    tab.insert(0, 'model', key)
    ph_rows.append(tab)
ph_all = pd.concat(ph_rows)
save(ph_all.round(4), 'F03_PH_tests_training_constant_terms')
print(ph_all.round(4).to_string(index=False))
ctv = models['M2b'].ctv.summary
tv_rows = pd.DataFrame([{'model': 'M2b', 'term': 'M1 early coef', 'coef': round(float(ctv.loc['M1', 'coef']), 4),
                         'HR_early': round(float(np.exp(ctv.loc['M1', 'coef'])), 3)},
                        {'model': 'M2b', 'term': 'M1 change after 2 years', 'coef': round(float(ctv.loc['M1_late', 'coef']), 4),
                         'p_time_variation': float(ctv.loc['M1_late', 'p'])},
                        {'model': 'M2b', 'term': 'M1 late HR', 'coef': round(float(models['M2b'].bl[CORE_M1.index('M1')]), 4),
                         'HR_late': round(float(np.exp(models['M2b'].bl[CORE_M1.index('M1')])), 3)}])
save(tv_rows, 'F04_M2b_time_varying_M_stage')
print(tv_rows.to_string(index=False))

# selection rule (training-only PH tests of constant terms)
def passes(key):
    if key == 'M2b':
        return None   # M-stage is modelled as time-varying; other constant terms tested below
    tab = models[key].ph_table()
    return bool((tab.p > 0.05).all())


ok_m1 = passes('M1'); ok_m2a = passes('M2a')
selected = 'M1' if ok_m1 else ('M2a' if ok_m2a else 'M2b')
sel_rule = pd.DataFrame([{'candidate': 'M1', 'all_constant_PH_p_gt_0.05_training': ok_m1},
                         {'candidate': 'M2a', 'all_constant_PH_p_gt_0.05_training': ok_m2a},
                         {'candidate': 'M2b', 'all_constant_PH_p_gt_0.05_training': 'M-stage time-varying; other constant terms: see F03 for M1 structure'},
                         {'candidate': 'SELECTED (first passing, simplest first)', 'all_constant_PH_p_gt_0.05_training': selected}])
save(sel_rule, 'F05_model_selection_rule')
print(sel_rule.to_string(index=False))
SEL = models[selected]
log(f'selected model: {selected}')

# ================================================================== phenotypes from the selected model's predicted 5-year survival (training-only cut-points)
S5 = SEL.S[:, 1]
q33, q67 = np.quantile(S5[trm], [1 / 3, 2 / 3])
GRP = np.where(S5 >= q67, 'Favourable', np.where(S5 >= q33, 'Intermediate', 'Adverse'))
M['PHENO'] = GRP
M['S5_SEL'] = S5
ph_def = []
ph_tab = []
for lab in ['Favourable', 'Intermediate', 'Adverse']:
    mt = trm & (GRP == lab); mv = vam & (GRP == lab)
    kt = KaplanMeierFitter().fit(M.OS_Y.values[mt], M.OS_E.values[mt])
    kv = KaplanMeierFitter().fit(M.OS_Y.values[mv], M.OS_E.values[mv])
    ci = median_survival_times(kv.confidence_interval_).iloc[0]
    med = kv.median_survival_time_
    ph_tab.append({'phenotype': lab, 'train_n': int(mt.sum()), 'valid_n': int(mv.sum()), 'valid_deaths': int(M.OS_E.values[mv].sum()),
                   'valid_median_OS': round(float(med), 2) if np.isfinite(med) else None,
                   'valid_median_95CI': f'{ci.iloc[0]:.2f}-{ci.iloc[1]:.2f}' if np.isfinite(ci.iloc[1]) else f'{ci.iloc[0]:.2f}-NE',
                   'valid_S5_KM': round(float(kv.survival_function_at_times(5).iloc[0]), 3),
                   'train_median_OS': round(float(kt.median_survival_time_), 2) if np.isfinite(kt.median_survival_time_) else None,
                   'train_S5_KM': round(float(kt.survival_function_at_times(5).iloc[0]), 3),
                   'train_mean_predicted_S5': round(float(S5[mt].mean()), 3),
                   'valid_mean_predicted_S5': round(float(S5[mv].mean()), 3)})
ph_def.append({'phenotype': lab, 'definition': {'Favourable': f'predicted 5-year OS >= {q67:.4f}',
                                                 'Intermediate': f'{q33:.4f} <= predicted 5-year OS < {q67:.4f}',
                                                 'Adverse': f'predicted 5-year OS < {q33:.4f}'}[lab]})
save(pd.DataFrame(ph_tab), 'F06_phenotypes_counts_survival_calibration')
save(pd.DataFrame(ph_def), 'F07_phenotype_definitions')
print(pd.DataFrame(ph_def).to_string(index=False)); print(pd.DataFrame(ph_tab).to_string(index=False))
lr_v = multivariate_logrank_test(M.OS_Y.values[vam], GRP[vam], M.OS_E.values[vam])
lr_t = multivariate_logrank_test(M.OS_Y.values[trm], GRP[trm], M.OS_E.values[trm])
rk = np.array([{'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}[g] for g in GRP], float)
sep = {'valid_logrank_p': float(lr_v.p_value), 'train_logrank_p': float(lr_t.p_value),
       'valid_C_ordinal': round(float(concordance_index(Tva, rk[vam], Eva)), 4)}
save(pd.Series(sep).rename('value').rename_axis('quantity').reset_index(), 'F08_phenotype_separation')
print(sep)

# bootstrap stability: refit selected model on training bootstrap samples; recompute cut-points and assignments
kap = []
tr_idx = np.where(trm)[0]
for _ in range(100):
    pick = RNG.choice(tr_idx, len(tr_idx), replace=True)
    b = M.iloc[pick]
    try:
        if selected == 'M1':
            cb = CoxPHFitter().fit(b[CORE_M1 + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
            be_b = cb.params_[CORE_M1].values; bl_b = be_b; st_col = 'STRATUM'; cols_b = CORE_M1; cut_b = 1e9
        elif selected == 'M2a':
            cb = CoxPHFitter().fit(b[CORE_M2A + ['STRAT_M', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRAT_M'])
            be_b = cb.params_[CORE_M2A].values; bl_b = be_b; st_col = 'STRAT_M'; cols_b = CORE_M2A; cut_b = 1e9
        else:
            bb = b[['OS_Y', 'OS_E', 'ID_', 'STRATUM'] + CORE_M1].copy() if 'ID_' in b else b.copy()
            bb['ID_'] = np.arange(len(bb))
            bb = bb.rename(columns={'OS_E': 'E'})
            long = to_episodic_format(bb[['OS_Y', 'E', 'ID_', 'STRATUM'] + CORE_M1], duration_col='OS_Y', event_col='E', id_col='ID_', time_gaps=CUT)
            long['M1_late'] = long['M1'] * (long['start'] >= CUT).astype(float)
            ct = CoxTimeVaryingFitter().fit(long[['ID_', 'start', 'stop', 'E'] + CORE_M1 + ['M1_late', 'STRATUM']],
                                            id_col='ID_', event_col='E', start_col='start', stop_col='stop', strata=['STRATUM'])
            sm = ct.summary
            be_b = np.array([sm.loc[x, 'coef'] for x in CORE_M1]); bl_b = be_b.copy()
            bl_b[CORE_M1.index('M1')] = sm.loc['M1', 'coef'] + sm.loc['M1_late', 'coef']
            st_col = 'STRATUM'; cols_b = CORE_M1; cut_b = CUT
    except Exception:  # noqa: BLE001
        continue
    Xall = M[cols_b].astype(float).values
    stv = M[st_col].values
    bres_b = breslow(M.OS_Y.values[pick], M.OS_E.values[pick], Xall[pick] @ be_b, Xall[pick] @ bl_b, stv[pick], cut_b)
    S5b = predict_S(bres_b, Xall, stv, be_b, bl_b, np.array([5.0]))[:, 0]
    a1, a2 = np.quantile(S5b[trm], [1 / 3, 2 / 3])
    gb = np.where(S5b >= a2, 'Favourable', np.where(S5b >= a1, 'Intermediate', 'Adverse'))
    kap.append(cohen_kappa_score(GRP[vam], gb[vam]))
stab = pd.DataFrame([{'selected_model': selected, 'bootstrap_resamples': len(kap),
                      'kappa_median': round(float(np.median(kap)), 3),
                      'kappa_2.5pct': round(float(np.percentile(kap, 2.5)), 3),
                      'kappa_97.5pct': round(float(np.percentile(kap, 97.5)), 3)}])
save(stab, 'F09_phenotype_bootstrap_stability')
print(stab.to_string(index=False))

# ================================================================== day-convention sensitivity (same specification)
day_rows = []
for lab, dd in cohorts.items():
    mm = dd[dd.TNM].reset_index(drop=True)
    tr_ = (mm.ERA == 'train').values; va_ = (mm.ERA == 'valid').values
    mm['DFI_NR'] = mm.DFI.isna().astype(float); mm['METS_NR'] = mm.METS.isna().astype(float); mm['SIZE_NR'] = mm.SIZE.isna().astype(float)
    for col in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE']:
        mm[col + '_F'] = mm[col].fillna(mm.loc[tr_, col].median())
    mm['AGE10_F'] = mm.AGE_F / 10; mm['DFI12_F'] = mm.DFI_F / 12; mm['SIZE10_F'] = mm.SIZE_F / 10
    mm['STRATUM'] = mm.MALE_F.round().astype(int) * 2 + mm.SYNC_F.round().astype(int)
    mm['OS_E'] = mm.OS_E.astype(float)
    cph_ = CoxPHFitter().fit(mm.loc[tr_, CORE_M1 + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
    be_ = cph_.params_[CORE_M1].values
    Xm = mm[CORE_M1].astype(float).values
    bres_ = breslow(mm.OS_Y.values[tr_], mm.OS_E.values[tr_], Xm[tr_] @ be_, Xm[tr_] @ be_, mm.STRATUM.values[tr_], 1e9)
    S5_ = predict_S(bres_, Xm, mm.STRATUM.values, be_, be_, np.array([5.0]))[:, 0]
    q1_, q2_ = np.quantile(S5_[tr_], [1 / 3, 2 / 3])
    G_ = np.where(S5_ >= q2_, 'Favourable', np.where(S5_ >= q1_, 'Intermediate', 'Adverse'))
    hr = cph_.summary.loc['M1', 'exp(coef)']
    row = {'convention': lab, 'modelling_cohort_TNM': len(mm), 'train_n': int(tr_.sum()), 'valid_n': int(va_.sum()),
           'M1_valid_C': round(float(concordance_index(mm.OS_Y.values[va_], -(Xm[va_] @ be_), mm.OS_E.values[va_])), 4),
           'M_stage_HR': round(float(hr), 3), 'cut_S5_q33': round(float(q1_), 4), 'cut_S5_q67': round(float(q2_), 4)}
    day_rows.append(row)
    # map back to primary patients by source row for phenotype reassignment comparison
    mm_key = pd.DataFrame({'SRC': mm.index.values, 'G': G_})
    cohorts[lab + '__G'] = mm_key
day_tab = pd.DataFrame(day_rows)
prim_key = pd.DataFrame({'SRC': M.SRC.values, 'G': GRP})
agree = []
for lab in cohorts:
    if lab.endswith('__G'):
        continue
    if lab == 'mid-month (15th, primary)':
        continue
    kk = cohorts[lab + '__G'] if (lab + '__G') in cohorts else None
    if kk is None:
        continue
    j = prim_key.merge(kk, on='SRC', how='inner', suffixes=('_p', '_c'))
    agree.append({'convention': lab, 'patients_in_both': len(j),
                  'phenotype_identical_pct': round(100 * float((j.G_p == j.G_c).mean()), 2)})
day_tab = day_tab.merge(pd.DataFrame(agree), on='convention', how='left')
save(day_tab, 'F10_day_convention_sensitivity')
print(day_tab.to_string(index=False))

# ================================================================== informative censoring: undated recurrences
REC_FIELDS = ([f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
              + [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)] + [f'RECDT_F{i}' for i in range(1, 8)])
REC_FIRST = pd.concat([serial(v2[c]) for c in REC_FIELDS], axis=1).min(axis=1)
CNT = (pd.concat([num(v2[f'LRNBREC_M{i}']) for i in range(1, 6)] + [num(v2[f'EXHNBREC2_M{i}']) for i in range(1, 9)], axis=1).fillna(0) > 0).any(axis=1)
AWD = v1.PATSTATC.notna() & v2.PATSTAT_F1.eq('Alive with disease')
M_ids = D[D.TNM].index                         # index labels of the primary modelling cohort in the source frame
rec = REC_FIRST.loc[M_ids].values
rec_after = (~pd.isna(rec)) & (rec >= M.T0.values) & (rec <= M.LAST.values)
rec_before = (~pd.isna(rec)) & (rec < M.T0.values)
undated = (~rec_after) & (~rec_before) & CNT.loc[M_ids].values
M['UNDATED'] = undated
M['REC_AFTER'] = rec_after
cmp_rows = []
for lab, mask in [('undated recurrence (count > 0, no date)', undated), ('dated recurrence after operation', rec_after),
                  ('neither', ~undated & ~rec_after)]:
    s_ = M[mask & ~rec_before]
    kk = KaplanMeierFitter().fit(s_.OS_Y, s_.OS_E)
    cmp_rows.append({'group': lab, 'n': len(s_), 'median_age': round(float(s_.AGE.median()), 1),
                     'T4_pct': round(100 * float((s_.T_GRP == 'T4').mean()), 1),
                     'N2_pct': round(100 * float((s_.N_GRP == 'N2').mean()), 1),
                     'M1_pct': round(100 * float((s_.M_GRP == 'M1').mean()), 1),
                     'median_size_mm': round(float(s_.SIZE.median()), 1),
                     'median_follow_up_years': round(float(s_.OS_Y.median()), 2),
                     'OS_median_years': round(float(kk.median_survival_time_), 2) if np.isfinite(kk.median_survival_time_) else None,
                     'deaths_pct': round(100 * float(s_.OS_E.mean()), 1),
                     'mean_predicted_5y_survival': round(float(s_.S5_SEL.mean()), 3)})
ic = pd.DataFrame(cmp_rows)
save(ic, 'F11_undated_recurrence_informative_censoring_check')
print(ic.to_string(index=False))

# ================================================================== death and last-contact verification
dk = pd.concat([v2[f'DEATHKYN_F{i}'] for i in range(1, 8)], axis=1)
dk_yes = dk.eq('Yes').any(axis=1)
cons = {
    'deceased (PATSTATC)': int(DEATH.sum()),
    'deceased with any DEATHKYN_F = Yes': int((DEATH & dk_yes).sum()),
    'deceased without any DEATHKYN_F = Yes': int((DEATH & ~dk_yes).sum()),
    'alive/lost but DEATHKYN_F = Yes': int(((~DEATH) & PST_ANY & dk_yes).sum()),
    'last-news (LASTNDTC) present for deceased': int((DEATH & LAST_SER.notna()).sum()),
    'LASTNDTC equals latest follow-up date (all with both)': int((LAST_SER == LAST_FU)[LAST_SER.notna() & LAST_FU.notna()].sum()),
    'LASTNDTC earlier than latest follow-up date': int((LAST_SER < LAST_FU)[LAST_SER.notna() & LAST_FU.notna()].sum()),
    'LASTNDTC later than latest follow-up date': int((LAST_SER > LAST_FU)[LAST_SER.notna() & LAST_FU.notna()].sum()),
    'modelling deaths with time zero (operation) after last contact': int((M.OS_Y_raw <= 0).sum()),
    'modelling deaths after censoring date 2020-07-04': int((M.LAST > CENSOR).sum()),
    'modelling deaths with event time > 15 years (censored)': int((M.OS_Y_raw > MAXFU).sum()),
}
save(pd.Series(cons).rename('n').rename_axis('check').reset_index(), 'F12_death_and_last_contact_verification')
print(pd.Series(cons).to_string())

# ================================================================== CEA sensitivity on the selected model
cc = M[M.CEA.notna()].copy()
cc_tr = (cc.ERA == 'train').values; cc_va = (cc.ERA == 'valid').values
cols_sel = SEL.cols
base_cols = cols_sel
cph_b = CoxPHFitter().fit(cc.loc[cc_tr, base_cols + [SEL.strat_col, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[SEL.strat_col])
cph_c = CoxPHFitter().fit(cc.loc[cc_tr, base_cols + ['CEA_LOG', SEL.strat_col, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[SEL.strat_col])
lp_b = cc[base_cols].astype(float).values @ cph_b.params_[base_cols].values
lp_c = cc[base_cols + ['CEA_LOG']].astype(float).values @ cph_c.params_[base_cols + ['CEA_LOG']].values
cea_rows = [{'analysis': 'complete case', 'train_n': int(cc_tr.sum()), 'valid_n': int(cc_va.sum()),
             'valid_deaths': int(cc.OS_E.values[cc_va].sum()),
             'CEA_HR_per_log_unit': round(float(np.exp(cph_c.params_['CEA_LOG'])), 3),
             'CEA_HR_95CI': f"{cph_c.summary.loc['CEA_LOG', 'exp(coef) lower 95%']:.3f}-{cph_c.summary.loc['CEA_LOG', 'exp(coef) upper 95%']:.3f}",
             'valid_C_without_CEA': round(float(concordance_index(cc.OS_Y.values[cc_va], -lp_b[cc_va], cc.OS_E.values[cc_va])), 4),
             'valid_C_with_CEA': round(float(concordance_index(cc.OS_Y.values[cc_va], -lp_c[cc_va], cc.OS_E.values[cc_va])), 4)}]
na_fit = NelsonAalenFitter().fit(M.OS_Y.values[trm], M.OS_E.values[trm])
H_na = np.interp(M.OS_Y.values, na_fit.cumulative_hazard_.index.values, na_fit.cumulative_hazard_.iloc[:, 0].values)
pred_cols = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F']
Xp = M[pred_cols].astype(float).values
dev = np.column_stack([Xp, M.CEA_LOG.values, H_na, M.OS_E.values])
coefs, varis, hrs, lp_v = [], [], [], []
for draw in range(10):
    imp = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw).fit(dev[trm])
    cea_dev = imp.transform(dev)[:, len(pred_cols)]
    dd = M[base_cols + [SEL.strat_col, 'OS_Y', 'OS_E']].copy(); dd['CEA_IMP'] = cea_dev
    cm = CoxPHFitter().fit(dd.loc[trm, base_cols + ['CEA_IMP', SEL.strat_col, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[SEL.strat_col])
    coefs.append(cm.params_['CEA_IMP']); varis.append(cm.standard_errors_['CEA_IMP'] ** 2); hrs.append(float(np.exp(cm.params_['CEA_IMP'])))
    impv = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw).fit(np.column_stack([Xp, M.CEA_LOG.values])[trm])
    cea_val = impv.transform(np.column_stack([Xp, M.CEA_LOG.values]))[:, len(pred_cols)]
    dv = M[base_cols].copy(); dv['CEA_IMP'] = cea_val
    lp_v.append(cm.predict_log_partial_hazard(dv[base_cols + ['CEA_IMP']]).values.ravel())
bar = float(np.mean(coefs)); Wv = float(np.mean(varis)); Bv = float(np.var(coefs, ddof=1)); se = np.sqrt(Wv + 1.1 * Bv)
lp_avg = np.mean(lp_v, axis=0)
cea_rows.append({'analysis': 'multiple imputation, 10 draws (development outcome-compatible; validation predictors only)',
                 'train_n': n_tr, 'valid_n': n_va, 'valid_deaths': int(Eva.sum()),
                 'CEA_HR_per_log_unit': round(float(np.exp(bar)), 3),
                 'CEA_HR_95CI': f'{np.exp(bar-1.96*se):.3f}-{np.exp(bar+1.96*se):.3f}',
                 'valid_C_without_CEA': round(float(concordance_index(Tva, -(M[base_cols].astype(float).values @ SEL.be)[vam], Eva)), 4),
                 'valid_C_with_CEA': round(float(concordance_index(Tva, -lp_avg[vam], Eva)), 4),
                 'draw_HR_range': f'{min(hrs):.3f}-{max(hrs):.3f}'})
save(pd.DataFrame(cea_rows), 'F13_CEA_sensitivity_final')
print(pd.DataFrame(cea_rows).to_string(index=False))

# ================================================================== pre-operative-only sensitivity (no count or size)
pre = Model('pre-operative-only sensitivity (no metastasis count or size)', PREOP_ONLY, 'STRATUM')
pre_perf = pd.DataFrame([metrics_for(pre)])
save(pre_perf, 'F14_preoperative_only_sensitivity')
print(pre_perf.to_string(index=False))
M['S5_PREOP'] = pre.S[:, 1]
pre_q1, pre_q2 = np.quantile(M.S5_PREOP[trm], [1 / 3, 2 / 3])
GRP_PRE = np.where(M.S5_PREOP >= pre_q2, 'Favourable', np.where(M.S5_PREOP >= pre_q1, 'Intermediate', 'Adverse'))
kp = cohen_kappa_score(GRP[vam], GRP_PRE[vam])
save(pd.DataFrame([{'agreement_with_primary_phenotypes_validation_kappa': round(float(kp), 3),
                    'share_patients_same_group_pct': round(100 * float((GRP == GRP_PRE).mean()), 1)}]),
     'F15_preoperative_only_phenotype_agreement')

# ================================================================== identical-subset comparison and calibration
fong = (M.N_GRP.isin(['N1', 'N2']).astype(float) + (M.DFI < 12).astype(float) + (M.METS > 1).astype(float)
        + (M.SIZE > 50).astype(float) + (M.CEA > 200).astype(float))
fong = fong.where(M.N_GRP.notna() & M.DFI.notna() & M.METS.notna() & M.SIZE.notna() & M.CEA.notna())
nord = ((M.AGE >= 60).astype(float) + (M.T_GRP == 'T4').astype(float) + M.N_GRP.isin(['N1', 'N2']).astype(float) + (M.DFI < 12).astype(float))
nord = nord.where(M.AGE.notna() & M.T_GRP.notna() & M.N_GRP.notna() & M.DFI.notna())
H5 = -np.log(np.clip(SEL.S[:, 1], 1e-12, 1))
subs = [('All TNM-complete validation', vam), ('Fong CRS subset (CEA recorded)', vam & fong.notna().values),
        ('Nordlinger-type subset', vam & nord.notna().values)]
rows_sub = []
for lab, mv in subs:
    row = {'subset': lab, 'valid_n': int(mv.sum()), 'valid_deaths': int(M.OS_E.values[mv].sum()),
           'selected_model_C': round(float(concordance_index(M.OS_Y.values[mv], -H5[mv], M.OS_E.values[mv])), 4)}
    if 'Fong' in lab:
        row['Fong_CRS_C'] = round(float(concordance_index(M.OS_Y.values[mv], -fong.values[mv], M.OS_E.values[mv])), 4)
    if 'Nordlinger' in lab:
        row['Nordlinger_C'] = round(float(concordance_index(M.OS_Y.values[mv], -nord.values[mv], M.OS_E.values[mv])), 4)
    o5 = float(KaplanMeierFitter().fit(M.OS_Y.values[mv], M.OS_E.values[mv]).survival_function_at_times(5).iloc[0])
    row['mean_predicted_S5'] = round(float(SEL.S[mv, 1].mean()), 3)
    row['observed_S5_KM'] = round(o5, 3)
    row['OE_5y'] = round(o5 / float(SEL.S[mv, 1].mean()), 3)
    rows_sub.append(row)
save(pd.DataFrame(rows_sub), 'F16_identical_subset_comparison_calibration')
print(pd.DataFrame(rows_sub).to_string(index=False))

# ================================================================== RFS (secondary) on the selected cohort
rec_days = (pd.Series(rec) - pd.Series(M.T0.values)).dt.days.values.astype(float)
last_days = (pd.Series(M.LAST.values) - pd.Series(M.T0.values)).dt.days.values.astype(float)
rT = np.clip(np.minimum(np.where(rec_after, rec_days, last_days) / DAYS, MAXFU), 1 / DAYS, None)
elig = ~rec_before
rfs_specs = [
    ('PRIMARY: dated recurrence and death events; undated censored', np.where(rec_after | M.OS_E.values.astype(bool), 1.0, 0.0), elig),
    ('undated recurrences events at last contact', np.where(rec_after | M.OS_E.values.astype(bool) | undated, 1.0, 0.0), elig),
    ('undated recurrences events at mid-interval', None, elig),
    ('undated recurrence patients excluded', np.where(rec_after | M.OS_E.values.astype(bool), 1.0, 0.0), elig & ~undated),
]
rfs_rows = []
for lab, E_, mask in rfs_specs:
    T_ = rT.copy()
    if E_ is None:
        T_ = np.where(undated & ~rec_after, last_days / DAYS / 2, rT)
        E_ = np.where(rec_after | M.OS_E.values.astype(bool) | undated, 1.0, 0.0)
    k = KaplanMeierFitter().fit(T_[mask], E_[mask])
    ci = median_survival_times(k.confidence_interval_).iloc[0]
    rfs_rows.append({'RFS_analysis': lab, 'n': int(mask.sum()), 'events': int(E_[mask].sum()),
                     'median_RFS': round(float(k.median_survival_time_), 2) if np.isfinite(k.median_survival_time_) else None,
                     'median_95CI': f'{ci.iloc[0]:.2f}-{ci.iloc[1]:.2f}' if np.isfinite(ci.iloc[1]) else f'{ci.iloc[0]:.2f}-NE',
                     'RFS_3y': round(float(k.survival_function_at_times(3).iloc[0]), 3),
                     'RFS_5y': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
save(pd.DataFrame(rfs_rows), 'F17_RFS_sensitivity_final')
print(pd.DataFrame(rfs_rows).to_string(index=False))

# ================================================================== save headline metrics
head = {'selected_model': selected, 'phenotype_cut_S5_q33': round(float(q33), 4), 'phenotype_cut_S5_q67': round(float(q67), 4),
        'primary_cohort_TNM_complete': len(M), 'primary_train_n': n_tr, 'primary_valid_n': n_va}
save(pd.Series(head).rename('value').rename_axis('quantity').reset_index(), 'F00_headline')
M.to_parquet(W / 'final_v6_modelling_cohort.parquet') if False else None   # patient-level file kept out of results
log(f'done -> {RES}')
