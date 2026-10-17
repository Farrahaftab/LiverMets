"""Final evaluation: stratified and time-varying Cox corrections, recalibration (training data only),
phenotype comparison (censoring-aware survival tree vs Cox risk-score tertiles), CEA missingness
sensitivity (survival-compatible multiple imputation), RFS, and Fong / Nordlinger benchmarks.

Development uses training-era patients only (liver metastasis diagnosis <= 2009). Temporal validation
(>= 2010) is used only to evaluate fixed models and rules. No cut-point, model or recalibration parameter
is estimated from validation outcomes.

Usage:
    LIVERMET_WORK_DIR=... LIVERMET_RESULTS_DIR=... python final_evaluation.py
"""
import os
import runpy
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, CoxTimeVaryingFitter, KaplanMeierFitter, NelsonAalenFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test, proportional_hazard_test
from lifelines.utils import concordance_index, median_survival_times, to_episodic_format
from scipy.stats import chi2, norm
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import cohen_kappa_score
from sksurv.metrics import brier_score, cumulative_dynamic_auc, integrated_brier_score
from sksurv.tree import SurvivalTree
from sksurv.util import Surv

warnings.filterwarnings('ignore')
T0 = time.time()
SEED = 42
RNG = np.random.default_rng(SEED)
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'final_evaluation'
(RES / 'figures').mkdir(parents=True, exist_ok=True)
TIMES = np.array([1.0, 3.0, 5.0])
TB = np.arange(1.0, 7.5, 0.5)
CUT = 2.0          # time-varying coefficients: separate effects before and after 2 years
MAXFU = 15.0
DAYS = 365.25
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']


def log(msg):
    print(f'[{time.time()-T0:6.0f}s] {msg}', flush=True)


def save(df, name):
    df.to_csv(RES / f'{name}.csv', index=False)
    return df


# ================================================================== cohort and covariates
g = runpy.run_path('/home/user/LiverMets/notebooks/methods_comparison.py', run_name='methods')
c = g['c'].copy()
raw = g['raw']
trm = np.asarray(g['trm'], dtype=bool)
vam = np.asarray(g['vam'], dtype=bool)
assert len(c) == 13285 and trm.sum() == 6658 and vam.sum() == 6627
c['OS_Y'] = c.OS_Y.astype(float)
c['OS_E'] = c.OS_E.astype(float)
c['T3'] = c['T_GRP_T3']
c['T4'] = c['T_GRP_T4']
c['N1'] = c['N_GRP_N1']
c['N2'] = c['N_GRP_N2']
c['M1'] = c['M_GRP_M1']
c['AGE10'] = c.AGE / 10
c['DFI12'] = c.DFI / 12
c['SIZE10'] = c.SIZE / 10
for col in ['DFI', 'METS', 'SIZE']:
    c[col + '_NR'] = c[col].isna().astype(float)
for col in ['AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10']:
    c[col + '_F'] = c[col].fillna(c.loc[trm, col].median())          # training medians only
c['MALE_B'] = c.MALE_F.round().astype(int)
c['SYNC_B'] = c.SYNC_F.round().astype(int)
c['STRATUM'] = c.MALE_B * 2 + c.SYNC_B                             # sex x synchronous, 4 strata
ID = np.arange(len(c))
c['ID'] = ID

CORE = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
CORE_NOSTRAT = CORE + ['MALE_F', 'SYNC_F']                      # M0: prespecified no-CEA model
y_os = Surv.from_arrays(event=c.OS_E.astype(bool).values, time=c.OS_Y.values)
log(f'cohort {len(c):,} | train {trm.sum():,} (deaths {int(c.OS_E[trm].sum()):,}) | valid {vam.sum():,} '
    f'(deaths {int(c.OS_E[vam].sum()):,})')


# ================================================================== Breslow baseline with piecewise coefficients
def breslow(T, E, X, be, bl, strat, cut=CUT):
    """Baseline cumulative hazard per stratum; coefficients be before `cut`, bl after `cut`."""
    lpe = X @ be
    lpl = X @ bl
    out = {}
    for s in np.unique(strat):
        m = strat == s
        t, e, le, ll = T[m], E[m], lpe[m], lpl[m]
        o = np.argsort(t, kind='mergesort')
        t, e, le, ll = t[o], e[o], le[o], ll[o]
        re_ = np.cumsum(np.exp(le)[::-1])[::-1]
        rl_ = np.cumsum(np.exp(ll)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        if len(ev) == 0:
            out[s] = (np.array([0.0]), np.array([0.0]), np.array([0.0]))
            continue
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        late = ev >= cut
        denom = np.where(late, rl_[idx], re_[idx])
        dH = dk / denom
        out[s] = (ev, np.cumsum(np.where(late, 0.0, dH)), np.cumsum(np.where(late, dH, 0.0)))
    return out


def predict_S(bres, X, strat, be, bl, times):
    """Survival probabilities S(t|x) at `times`; returns (S, H5) where H5 = cumulative hazard at 5 years."""
    xe = X @ be
    xl = X @ bl
    S = np.ones((len(X), len(times)))
    H = np.zeros((len(X), len(times)))
    for s in np.unique(strat):
        m = strat == s
        ev, He, Hl = bres[s]
        ii = np.searchsorted(ev, times, side='right') - 1
        Te = np.where(ii >= 0, He[np.clip(ii, 0, None)], 0.0)
        Tl = np.where(ii >= 0, Hl[np.clip(ii, 0, None)], 0.0)
        Hm = np.exp(xe[m, None]) * Te[None, :] + np.exp(xl[m, None]) * Tl[None, :]
        H[m] = Hm
        S[m] = np.exp(-Hm)
    return S, H


# ================================================================== model fitting
def fit_static(mask, cols, strata=None):
    d = c.loc[mask, cols + ['OS_Y', 'OS_E'] + ([strata] if strata else [])]
    cph = CoxPHFitter().fit(d, 'OS_Y', 'OS_E', strata=[strata] if strata else None)
    return cph


def fit_tv(mask, cols, tv_cols, strata=None):
    """Piecewise time-varying Cox: tv_cols get a second coefficient for follow-up >= CUT years."""
    base = c.loc[mask, ['ID', 'OS_Y', 'OS_E'] + cols + ([strata] if strata else [])].rename(columns={'OS_E': 'E'})
    long = to_episodic_format(base, duration_col='OS_Y', event_col='E', id_col='ID', time_gaps=CUT)
    for x in tv_cols:
        long[x + '_late'] = long[x] * (long['start'] >= CUT).astype(float)
    feats = cols + [x + '_late' for x in tv_cols]
    ctv = CoxTimeVaryingFitter().fit(long[['ID', 'start', 'stop', 'E'] + feats + ([strata] if strata else [])],
                                     id_col='ID', event_col='E', start_col='start', stop_col='stop',
                                     strata=[strata] if strata else None)
    summ = ctv.summary
    be = np.array([summ.loc[x, 'coef'] for x in cols])
    bl = be.copy()
    for x in tv_cols:
        bl[cols.index(x)] = summ.loc[x, 'coef'] + summ.loc[x + '_late', 'coef']
    return ctv, be, bl


def model_predict(bres, X, strat, be, bl):
    return predict_S(bres, X, strat, be, bl, np.concatenate([TIMES, TB]))


# ================================================================== metrics
def cindex_bootstrap(T, E, risk, reps=300):
    n = len(T)
    base = concordance_index(T, -risk, E)
    boots = []
    for _ in range(reps):
        b = RNG.integers(0, n, n)
        boots.append(concordance_index(T[b], -risk[b], E[b]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return round(float(base), 4), f'{lo:.3f}-{hi:.3f}'


def calibration(S5, T, E, label):
    dec = pd.qcut(pd.Series(S5).rank(method='first'), 10, labels=False).values
    rows = []
    for q in range(10):
        m = dec == q
        k = KaplanMeierFitter().fit(T[m], E[m])
        rows.append({'model': label, 'decile': q + 1, 'n': int(m.sum()),
                     'predicted_S5': round(float(S5[m].mean()), 3),
                     'observed_S5_KM': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    obs = float(KaplanMeierFitter().fit(T, E).survival_function_at_times(5).iloc[0])
    lp = np.log(-np.log(np.clip(S5, 1e-6, 1 - 1e-6)))
    slope = CoxPHFitter().fit(pd.DataFrame({'T': T, 'E': E, 'lp': lp}), 'T', 'E').params_['lp']
    summ = {'model': label, 'mean_pred_S5': round(float(S5.mean()), 3), 'observed_S5_KM': round(obs, 3),
            'OE_ratio_5y': round(obs / float(S5.mean()), 3), 'calib_slope': round(float(slope), 3)}
    return pd.DataFrame(rows), summ


def performance(name, S_tr, H_tr_all, S_va, H_va, mtr, mva, Ttr, Etr, Tva, Eva):
    """S_* and H_* are matrices with columns [TIMES..., TB...]; risk = 5-year cumulative hazard."""
    ntim = len(TIMES)
    risk_tr = H_tr_all[:, 2]
    risk_va = H_va[:, 2]
    y_tr = Surv.from_arrays(Etr.astype(bool), Ttr)
    y_va = Surv.from_arrays(Eva.astype(bool), Tva)
    Cv, Cci = cindex_bootstrap(Tva, Eva, risk_va)
    out = {'model': name, 'train_C': round(float(concordance_index(Ttr, -risk_tr, Etr)), 4),
           'valid_C': Cv, 'valid_C_95CI': Cci}
    try:
        auc, _ = cumulative_dynamic_auc(y_tr, y_va, risk_va, TIMES)
        for t, a in zip(TIMES, auc):
            out[f'tAUC_{int(t)}y'] = round(float(a), 3)
    except Exception as ex:  # noqa: BLE001
        out['tAUC_note'] = str(ex)[:60]
    try:
        _, bs = brier_score(y_tr, y_va, S_va[:, ntim:], TB)
        for t in [1.0, 3.0, 5.0]:
            out[f'Brier_{int(t)}y'] = round(float(bs[list(TB).index(t)]), 4)
        out['IBS_1_to_7y'] = round(float(integrated_brier_score(y_tr, y_va, S_va[:, ntim:], TB)), 4)
    except Exception as ex:  # noqa: BLE001
        out['Brier_note'] = str(ex)[:60]
    return out


# ================================================================== masks and data arrays
Ttr, Etr = c.OS_Y[trm].values, c.OS_E[trm].values
Tva, Eva = c.OS_Y[vam].values, c.OS_E[vam].values

# ================================================================== 1. M0 baseline and four candidate corrections
log('1. fitting M0 (no-CEA Cox, no corrections)')
cph0 = fit_static(trm, CORE_NOSTRAT)
cols0 = CORE_NOSTRAT
be0 = cph0.params_[cols0].values
X_all0 = c[cols0].astype(float).values
bres0 = breslow(Ttr, Etr, X_all0[trm], be0, be0, np.zeros(trm.sum(), int))
S0, H0 = model_predict(bres0, X_all0, np.zeros(len(c), int), be0, be0)

# validate my Breslow implementation against lifelines on the validation set
lf = cph0.predict_survival_function(c.loc[vam, cols0], times=[5.0]).T.values.ravel()
mine = S0[vam][:, list(np.concatenate([TIMES, TB])).index(5.0)]
log(f'breslow check vs lifelines (validation S(5)): max abs diff {np.max(np.abs(lf - mine)):.2e}')
assert np.max(np.abs(lf - mine)) < 1e-3, "Breslow implementation disagrees with lifelines"

hr0 = cph0.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
hr0.columns = ['term', 'coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
save(hr0.round(4), 'F01_M0_hazard_ratios')
ph0 = proportional_hazard_test(cph0, c.loc[trm, cols0 + ['OS_Y', 'OS_E']], time_transform='rank').summary.reset_index()
ph0.columns = ['term'] + list(ph0.columns[1:])
save(ph0.round(4), 'F02_M0_PH_test_training')
print(ph0.round(4).to_string(index=False))

# M1: stratified by sex and synchronous presentation; all other covariates constant
log('1. fitting M1 (stratified)')
cph1 = fit_static(trm, CORE, strata='STRATUM')
cols1 = CORE
be1 = cph1.params_[cols1].values
X_all1 = c[cols1].astype(float).values
bres1 = breslow(Ttr, Etr, X_all1[trm], be1, be1, c.STRATUM.values[trm])
S1, H1 = model_predict(bres1, X_all1, c.STRATUM.values, be1, be1)
hr1 = cph1.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
hr1.columns = ['term', 'coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
save(hr1.round(4), 'F03_M1_stratified_hazard_ratios')
ph1 = proportional_hazard_test(cph1, c.loc[trm, cols1 + ['OS_Y', 'OS_E', 'STRATUM']], time_transform='rank').summary.reset_index()
ph1.columns = ['term'] + list(ph1.columns[1:])
save(ph1.round(4), 'F04_M1_PH_test_training')
print(hr1.round(3).to_string(index=False)); print(ph1.round(4).to_string(index=False))

# M2: piecewise time-varying coefficients for the PH violators; sex and synchronous kept as covariates
TV2 = ['MALE_F', 'SYNC_F', 'N2', 'SIZE10_F', 'METS_NR']
log('1. fitting M2 (time-varying coefficients)')
ctv2, be2, bl2 = fit_tv(trm, CORE_NOSTRAT, TV2)
X_all2 = c[CORE_NOSTRAT].astype(float).values
bres2 = breslow(Ttr, Etr, X_all2[trm], be2, bl2, np.zeros(trm.sum(), int))
S2, H2 = model_predict(bres2, X_all2, np.zeros(len(c), int), be2, bl2)
tv2 = ctv2.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
tv2.columns = ['term', 'coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
save(tv2.round(4), 'F05_M2_timevarying_hazard_ratios')
print(tv2.round(3).to_string(index=False))

# M3: stratified by sex and synchronous presentation + time-varying coefficients for remaining violators
TV3 = ['N2', 'SIZE10_F', 'METS_NR']
log('1. fitting M3 (stratified + time-varying)')
ctv3, be3, bl3 = fit_tv(trm, CORE, TV3, strata='STRATUM')
X_all3 = c[CORE].astype(float).values
bres3 = breslow(Ttr, Etr, X_all3[trm], be3, bl3, c.STRATUM.values[trm])
S3, H3 = model_predict(bres3, X_all3, c.STRATUM.values, be3, bl3)
tv3 = ctv3.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
tv3.columns = ['term', 'coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
save(tv3.round(4), 'F06_M3_stratified_timevarying_hazard_ratios')
print(tv3.round(3).to_string(index=False))

# ------------------------------------------------------------------ performance and calibration, identical patients
perf = []
cal_all = []
summ_all = []
models = {'M0 Cox (original, no corrections)': (S0, H0, H0),
          'M1 Cox stratified (sex x synchronous)': (S1, H1, H1),
          'M2 Cox time-varying (2-year split)': (S2, H2, H2),
          'M3 Cox stratified + time-varying': (S3, H3, H3)}
for name, (S_, H_, _) in models.items():
    perf.append(performance(name, S_[trm], H_[trm], S_[vam], H_[vam], trm, vam, Ttr, Etr, Tva, Eva))
    cal, sm = calibration(S_[vam][:, 2], Tva, Eva, name)
    cal_all.append(cal); summ_all.append(sm)
perf_df = save(pd.DataFrame(perf), 'F07_model_performance_before_after')
save(pd.concat(cal_all), 'F08_calibration_deciles_5y_validation')
save(pd.DataFrame(summ_all), 'F09_calibration_summary_validation')
print(perf_df.to_string(index=False)); print(pd.DataFrame(summ_all).to_string(index=False))

# ------------------------------------------------------------------ PH diagnostics after correction (training)
ph_summary = []
for name, ctv_, be_, bl_, cols_, tvc in [('M2', ctv2, be2, bl2, CORE_NOSTRAT, TV2),
                                         ('M3', ctv3, be3, bl3, CORE, TV3)]:
    for x in tvc:
        s = ctv_.summary.loc[x + '_late']
        ph_summary.append({'model': name, 'term': x, 'early_coef': round(float(ctv_.summary.loc[x, 'coef']), 4),
                           'late_minus_early': round(float(s['coef']), 4), 'p_time_variation': float(s['p']),
                           'note': 'coefficient changes after 2 years (p < 0.05 means the time-varying term is needed)'})
ph_summary = save(pd.DataFrame(ph_summary), 'F10_timevarying_term_tests')
print(ph_summary.round(4).to_string(index=False))

# ================================================================== model selection on TRAINING diagnostics only
# rule: a model is acceptable if every constant covariate passes the training Schoenfeld test (p > 0.05)
def residual_violations(cph_obj, cols_, extra_strata=None):
    d = c.loc[trm, cols_ + ['OS_Y', 'OS_E'] + ([extra_strata] if extra_strata else [])]
    res = proportional_hazard_test(cph_obj, d, time_transform='rank').summary
    return res


res1 = residual_violations(cph1, CORE, 'STRATUM')
v0 = ph0[ph0.p < 0.05].term.tolist()
v1 = res1[res1.p < 0.05].index.tolist()
rule_rows = [
    {'model': 'M0', 'constant_terms_violating_PH_training': ', '.join(v0) or 'none',
     'n_violations': len(v0), 'acceptable_by_training_rule': len(v0) == 0},
    {'model': 'M1', 'constant_terms_violating_PH_training': ', '.join(v1) or 'none',
     'n_violations': len(v1), 'acceptable_by_training_rule': len(v1) == 0},
    {'model': 'M2', 'constant_terms_violating_PH_training': 'time-varying terms modelled; constant terms: ' +
     ', '.join([x for x in CORE_NOSTRAT if x not in TV2]), 'n_violations': None,
     'acceptable_by_training_rule': None},
    {'model': 'M3', 'constant_terms_violating_PH_training': 'time-varying terms modelled; constant terms: ' +
     ', '.join([x for x in CORE if x not in TV3]), 'n_violations': None, 'acceptable_by_training_rule': None},
]
rule_df = save(pd.DataFrame(rule_rows), 'F11_model_selection_training_rule')
print(rule_df.to_string(index=False))

# ================================================================== 2. recalibration using training data only
log('2. recalibration (training data only)')
rec_rows = []
rec_cal = []
for label, (be_, bl_, cols_, X_, strat_, S_v) in {
        'M0': (be0, be0, CORE_NOSTRAT, X_all0, np.zeros(len(c), int), S0),
        'M3': (be3, bl3, CORE, X_all3, c.STRATUM.values, S3)}.items():
    # (a) recent-baseline recalibration: baseline re-estimated on training patients diagnosed in 2005-2009
    recent = trm & (c.T0.dt.year.values >= 2005)
    if label == 'M0':
        bres_r = breslow(c.OS_Y[recent].values, c.OS_E[recent].values, X_[recent], be_, bl_,
                         np.zeros(recent.sum(), int))
        S_r, H_r = model_predict(bres_r, X_, np.zeros(len(c), int), be_, bl_)
    else:
        bres_r = breslow(c.OS_Y[recent].values, c.OS_E[recent].values, X_[recent], be_, bl_,
                         strat_[recent])
        S_r, H_r = model_predict(bres_r, X_, strat_, be_, bl_)
    # (b) shrinkage factor from training-only bootstrap optimism (Harrell), static Cox refits
    lp_tr_full = X_[trm] @ be_
    gamma_app = float(CoxPHFitter().fit(pd.DataFrame({'T': Ttr, 'E': Etr, 'lp': lp_tr_full}), 'T', 'E').params_['lp'])
    optim = []
    tr_ids = np.where(trm)[0]
    cols_s = CORE_NOSTRAT if label == 'M0' else CORE_NOSTRAT
    for _ in range(100):
        bidx = RNG.choice(tr_ids, len(tr_ids), replace=True)
        Xbl = c[cols_s].astype(float).values
        db = pd.DataFrame(Xbl[bidx], columns=cols_s).assign(T=c.OS_Y.values[bidx], E=c.OS_E.values[bidx])
        try:
            cb = CoxPHFitter().fit(db, 'T', 'E')
        except Exception:  # noqa: BLE001
            continue
        bb = cb.params_[cols_s].values
        s_boot = CoxPHFitter().fit(pd.DataFrame({'T': db['T'], 'E': db['E'], 'lp': Xbl[bidx] @ bb}), 'T', 'E').params_['lp']
        s_orig = CoxPHFitter().fit(pd.DataFrame({'T': Ttr, 'E': Etr, 'lp': Xbl[tr_ids] @ bb}), 'T', 'E').params_['lp']
        optim.append(s_boot - s_orig)
    gamma = gamma_app - float(np.mean(optim))
    S_shr = np.power(np.clip(S_v, 1e-9, 1), gamma)
    for variant, S_use in [('original', S_v), ('recent-baseline (train 2005-2009)', S_r),
                           ('shrinkage factor gamma (training optimism)', S_shr)]:
        H_use = -np.log(np.clip(S_use, 1e-12, 1))
        p = performance(f'{label} {variant}', S_use[trm], H_use[trm], S_use[vam], H_use[vam],
                        trm, vam, Ttr, Etr, Tva, Eva)
        p['gamma_apparent'] = round(gamma_app, 3)
        p['gamma_optimism_corrected'] = round(gamma, 3)
        rec_rows.append(p)
        cal, sm = calibration(S_use[vam][:, 2], Tva, Eva, f'{label} {variant}')
        rec_cal.append(sm)
save(pd.DataFrame(rec_rows), 'F12_recalibration_validation')
save(pd.DataFrame(rec_cal), 'F12b_recalibration_calibration_summary')
print(pd.DataFrame(rec_rows).to_string(index=False)); print(pd.DataFrame(rec_cal).to_string(index=False))
log('recalibration done')

# ================================================================== 3. phenotype approaches
log('3. phenotype approaches')
# (a) censoring-aware survival tree (no CEA, depth 3, training only); leaves merged to three groups by training RMST5
TREE_FEAT = TNM = list(g['TNM_COLS']) + ['AGE10_F', 'MALE_F', 'SYNC_F', 'DFI12_F', 'METS_F', 'SIZE10_F',
                                             'DFI_NR', 'METS_NR', 'SIZE_NR']


def tree_fit(mask_tr, depth=3, seed=SEED):
    X = c[TREE_FEAT].astype(float).values.astype(np.float32)
    tr = SurvivalTree(max_depth=depth, min_samples_leaf=max(200, int(0.02 * mask_tr.sum())), random_state=seed)
    tr.fit(X[mask_tr], y_os[mask_tr])
    return tr, X


def leaf_rmst(tr_obj, X, mask_tr):
    leaf = tr_obj.apply(X)
    rm, rows = {}, []
    for L in np.unique(leaf):
        m = (leaf == L) & mask_tr
        k = KaplanMeierFitter().fit(c.OS_Y[m], c.OS_E[m])
        tt = k.survival_function_.index.values.astype(float)
        ss = k.survival_function_.iloc[:, 0].values.astype(float)
        grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
        idx = np.searchsorted(tt, grid[:-1], side='right') - 1
        rm[L] = float(np.sum(np.where(idx >= 0, ss[np.clip(idx, 0, None)], 1.0) * np.diff(grid)))
        rows.append((L, int(m.sum()), rm[L]))
    return leaf, rm, rows


def merge_leaves_to_three(rows):
    """Order leaves from best to worst (training RMST5); a leaf is assigned by the midpoint of its
    cumulative training-patient share: below 1/3 Favourable, below 2/3 Intermediate, otherwise Adverse."""
    rows = sorted(rows, key=lambda r: -r[2])
    total = sum(r[1] for r in rows)
    mapping, cum = {}, 0.0
    for L, n, _ in rows:
        before = cum / total
        cum += n
        mid = (before + cum / total) / 2
        mapping[L] = 'Favourable' if mid < 1 / 3 else ('Intermediate' if mid < 2 / 3 else 'Adverse')
    return mapping


tr_tree, Xtree = tree_fit(trm)
leaf_all, rmst_map, leaf_rows = leaf_rmst(tr_tree, Xtree, trm)
mapping_tree = merge_leaves_to_three(leaf_rows)
leaf_tab = pd.DataFrame([{'leaf': int(L), 'train_n': n, 'train_RMST5': round(r, 3),
                          'merged_group': mapping_tree[L],
                          'train_median_OS': round(float(KaplanMeierFitter().fit(c.OS_Y[(leaf_all == L) & trm],
                                                                             c.OS_E[(leaf_all == L) & trm]).median_survival_time_), 2)}
                         for L, n, r in leaf_rows])
save(leaf_tab, 'F13_survival_tree_leaves_and_merge')
print(leaf_tab.to_string(index=False))
grp_tree = np.array([mapping_tree[L] for L in leaf_all])
risk_tree_score = np.array([rmst_map[L] for L in leaf_all])     # higher = better

# (b) Cox risk-score tertiles (corrected model M3 is primary candidate; M0 for comparison)
def cox_tertiles(lp_all, lp_train):
    q1, q2 = np.quantile(lp_train, [1 / 3, 2 / 3])
    return np.where(lp_all >= q2, 'Adverse', np.where(lp_all >= q1, 'Intermediate', 'Favourable')), (q1, q2)


lp3 = X_all3 @ be3
lp0 = X_all0 @ be0
grp_c3, cut3 = cox_tertiles(lp3, lp3[trm])
grp_c0, cut0 = cox_tertiles(lp0, lp0[trm])


def phenotype_report(label, grp, score_for_c):
    rows = []
    for period, mask in [('training', trm), ('validation', vam)]:
        for lab in ['Favourable', 'Intermediate', 'Adverse']:
            m = mask & (grp == lab)
            if m.sum() == 0:
                rows.append({'phenotype': label, 'period': period, 'group': lab, 'n': 0}); continue
            k = KaplanMeierFitter().fit(c.OS_Y[m], c.OS_E[m])
            med = k.median_survival_time_
            ci = median_survival_times(k.confidence_interval_).iloc[0]
            rows.append({'phenotype': label, 'period': period, 'group': lab, 'n': int(m.sum()),
                         'share_pct': round(100 * m.sum() / mask.sum(), 1), 'deaths': int(c.OS_E[m].sum()),
                         'median_OS': round(float(med), 2) if np.isfinite(med) else None,
                         'median_95CI': f'{ci.iloc[0]:.2f}-{ci.iloc[1]:.2f}' if np.isfinite(ci.iloc[1]) else f'{ci.iloc[0]:.2f}-NE',
                         'S5': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    return pd.DataFrame(rows)


ph_tab = pd.concat([phenotype_report('Survival tree (merged leaves)', grp_tree, None),
                    phenotype_report('Cox M3 risk tertiles', grp_c3, None),
                    phenotype_report('Cox M0 risk tertiles', grp_c0, None)], ignore_index=True)
save(ph_tab, 'F14_phenotype_sizes_median_OS')
print(ph_tab.to_string(index=False))

# separation, C, calibration, Brier, stability, net benefit
sep = []
cal_ph = []
dca = []
rank_map = {'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}
for label, grp in [('Survival tree (merged leaves)', grp_tree), ('Cox M3 risk tertiles', grp_c3),
                   ('Cox M0 risk tertiles', grp_c0)]:
    rank_va = np.array([rank_map[x] for x in grp[vam]], float)
    rank_tr = np.array([rank_map[x] for x in grp[trm]], float)
    row = {'phenotype': label}
    row['train_logrank_p'] = float(multivariate_logrank_test(Ttr, grp[trm], Etr).p_value)
    row['valid_logrank_p'] = float(multivariate_logrank_test(Tva, grp[vam], Eva).p_value)
    pair = []
    for a, b in [('Favourable', 'Intermediate'), ('Intermediate', 'Adverse'), ('Favourable', 'Adverse')]:
        ma = vam & (grp == a); mb = vam & (grp == b)
        if ma.sum() and mb.sum():
            pair.append(min(1.0, 3 * logrank_test(c.OS_Y[ma], c.OS_Y[mb], c.OS_E[ma], c.OS_E[mb]).p_value))
    row['valid_pairwise_bonf_max_p'] = float(max(pair)) if pair else None
    row['valid_C_group_ordinal'] = round(float(concordance_index(Tva, rank_va, Eva)), 4)
    # group-level survival prediction from TRAINING KM, applied to validation patients
    S_grp = np.zeros((len(c), len(TB) + len(TIMES)))
    grid = np.concatenate([TIMES, TB])
    for lab in ['Favourable', 'Intermediate', 'Adverse']:
        mt = trm & (grp == lab)
        k = KaplanMeierFitter().fit(c.OS_Y[mt], c.OS_E[mt])
        sv = np.array([float(k.survival_function_at_times(t).iloc[0]) for t in grid])
        S_grp[grp == lab] = sv
    row.update(performance(label, S_grp[trm], -np.log(np.clip(S_grp[trm], 1e-12, 1)), S_grp[vam],
                           -np.log(np.clip(S_grp[vam], 1e-12, 1)), trm, vam, Ttr, Etr, Tva, Eva))
    for lab in ['Favourable', 'Intermediate', 'Adverse']:
        mv = vam & (grp == lab)
        if mv.sum() == 0:
            continue
        k = KaplanMeierFitter().fit(c.OS_Y[mv], c.OS_E[mv])
        pred5 = float(np.array([KaplanMeierFitter().fit(c.OS_Y[trm & (grp == lab)], c.OS_E[trm & (grp == lab)]).survival_function_at_times(5).iloc[0]])[0])
        cal_ph.append({'phenotype': label, 'group': lab, 'predicted_S5_training': round(pred5, 3),
                       'observed_S5_validation': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    # stability: bootstrap training resamples (tree re-grown; Cox re-fitted), kappa against main assignment
    kap = []
    for b_ in range(100):
        pick = RNG.choice(np.where(trm)[0], trm.sum(), replace=True)
        if label.startswith('Survival'):
            m_b = np.zeros(len(c), bool); m_b[pick] = True
            tb_, Xb_ = tree_fit(m_b, seed=SEED + b_)
            lb_leaf, rb_map, rb_rows = leaf_rmst(tb_, Xb_, m_b)
            mp = merge_leaves_to_three(rb_rows)
            g_b = np.array([mp[L] for L in tb_.apply(Xb_)])
        else:
            cols_b = CORE if label.startswith('Cox M3') else CORE_NOSTRAT
            d_b = c.iloc[pick][cols_b + ['OS_Y', 'OS_E']]
            try:
                cb = CoxPHFitter().fit(d_b, 'OS_Y', 'OS_E')
            except Exception:  # noqa: BLE001
                continue
            lp_b = (c[cols_b].astype(float).values @ cb.params_[cols_b].values)
            q1, q2 = np.quantile(lp_b[trm], [1 / 3, 2 / 3])
            g_b = np.where(lp_b >= q2, 'Adverse', np.where(lp_b >= q1, 'Intermediate', 'Favourable'))
        kap.append(cohen_kappa_score(grp[vam], g_b[vam]))
    row['bootstrap_kappa_median'] = round(float(np.median(kap)), 3)
    row['bootstrap_kappa_2.5pct'] = round(float(np.percentile(kap, 2.5)), 3)
    row['bootstrap_resamples'] = len(kap)
    sep.append(row)
    # clinical usefulness: group-level decision curve, high-risk = Adverse, outcome = 5-year death (validation KM)
    r_all = 1 - float(KaplanMeierFitter().fit(Tva, Eva).survival_function_at_times(5).iloc[0])
    mh = vam & (grp == 'Adverse')
    r_h = 1 - float(KaplanMeierFitter().fit(c.OS_Y[mh], c.OS_E[mh]).survival_function_at_times(5).iloc[0])
    frac_h = mh.sum() / vam.sum()
    for pt in np.arange(0.10, 0.61, 0.05):
        odds = pt / (1 - pt)
        dca.append({'phenotype': label, 'threshold': round(pt, 2),
                    'net_benefit_adverse_group': round(frac_h * (r_h - (1 - r_h) * odds), 4),
                    'net_benefit_treat_all': round(r_all - (1 - r_all) * odds, 4), 'net_benefit_none': 0.0})
sep_df = save(pd.DataFrame(sep), 'F15_phenotype_separation_C_calibration_stability')
save(pd.DataFrame(cal_ph), 'F16_phenotype_group_calibration_5y')
save(pd.DataFrame(dca), 'F17_decision_curve_adverse_group_5y')
print(sep_df.round(4).to_string(index=False)); print(pd.DataFrame(cal_ph).to_string(index=False))

# ------------------------------------------------------------------ 5. do Cox tertiles add information beyond the continuous score?
log('5. tertiles vs continuous score')
lp_tr3 = lp3[trm]
d_lp = pd.DataFrame({'T': Ttr, 'E': Etr, 'lp': lp_tr3})
cont = CoxPHFitter().fit(d_lp, 'T', 'E')
d_t = d_lp.assign(mid=(grp_c3[trm] == 'Intermediate').astype(float), adv=(grp_c3[trm] == 'Adverse').astype(float))
tert = CoxPHFitter().fit(d_t[['T', 'E', 'lp', 'mid', 'adv']], 'T', 'E')
LR = 2 * (tert.log_likelihood_ - cont.log_likelihood_)
p_lr = float(chi2.sf(LR, df=2))
add = pd.DataFrame([{
    'training_LR_chi2_tertiles_beyond_continuous': round(float(LR), 3), 'df': 2, 'p': p_lr,
    'valid_C_continuous': round(float(concordance_index(Tva, -lp3[vam], Eva)), 4),
    'valid_C_tertiles': round(float(concordance_index(Tva, np.array([rank_map[x] for x in grp_c3[vam]], float), Eva)), 4),
    'valid_C_continuous_95CI': cindex_bootstrap(Tva, Eva, lp3[vam])[1],
}])
save(add, 'F18_tertiles_vs_continuous_score')
print(add.to_string(index=False))

# ================================================================== 6. time origin and cohort reconciliation
log('6. cohort reconciliation')
EP_ = EP


def xl(s, lo=1, hi=80000):
    v = pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')
    v = v.where((v >= lo) & (v <= hi))
    return EP_ + pd.to_timedelta(v, unit='D')


SURG = raw.LE1HEPATECTYN_F1.map({'Yes': 1.0, 'No': 0.0})
HEPDT = xl(raw.LE1METARESECDT_L1)
LAST = xl(raw.LASTNDTC)
DG = xl(raw.LE1DGMETADT)
TNM = g['d'].TNM
st = g['d'].STATUS.notna()
cand = [
    ('All patients', pd.Series(True, index=raw.index)),
    ('TNM complete', TNM),
    ('Surgery = Yes (any date)', SURG == 1),
    ('Surgery = Yes and TNM complete', (SURG == 1) & TNM),
    ('Surgery = Yes, TNM complete, valid last contact', (SURG == 1) & TNM & LAST.notna() & st),
    ('Hepatectomy date present (lesion 1), TNM complete', HEPDT.notna() & TNM),
    ('Diagnosis origin, TNM complete, valid OS (primary)', TNM & DG.notna() & LAST.notna() & st & ((LAST - DG).dt.days > 0)),
]
recon = pd.DataFrame([{'definition': a, 'n': int(b.sum())} for a, b in cand])
recon.loc[len(recon)] = {'definition': 'Earlier published survival-eligible cohort (not reproducible from repo)', 'n': 14759}
recon.loc[len(recon)] = {'definition': 'Earlier-cited surgery-origin cohort (no definition found in repo)', 'n': 26094}
save(recon, 'F19_cohort_reconciliation_origins')
print(recon.to_string(index=False))

# ================================================================== 7. CEA missingness: survival-compatible multiple imputation
log('7. CEA missingness sensitivity (MI, outcome-compatible in development)')
M_DRAWS = 10
na = NelsonAalenFitter().fit(c.OS_Y[trm], c.OS_E[trm])
H_na = np.interp(c.OS_Y.values, na.cumulative_hazard_.index.values, na.cumulative_hazard_.iloc[:, 0].values)
pred_cols = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10']
X_pred = c[pred_cols].astype(float).values
X_cea = c[['CEA_LOG']].values
coefs, vars_, lp_val = [], [], []
cox_cols = CORE_NOSTRAT + ['CEA_IMP']
dev_mat = np.column_stack([X_pred, X_cea, H_na, c.OS_E.values])
for draw in range(M_DRAWS):
    imp = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw)
    imp.fit(dev_mat[trm])                                       # development: includes outcome (Nelson-Aalen, event)
    Xd = imp.transform(dev_mat)
    d = c[['OS_Y', 'OS_E'] + [x for x in CORE_NOSTRAT if x not in ('MALE_F', 'SYNC_F')]].copy()
    d['MALE_F'] = c.MALE_F.values; d['SYNC_F'] = c.SYNC_F.values
    d['CEA_IMP'] = Xd[:, len(pred_cols)]
    cph_m = CoxPHFitter().fit(d.loc[trm, cox_cols + ['OS_Y', 'OS_E']], 'OS_Y', 'OS_E')
    coefs.append(cph_m.params_['CEA_IMP']); vars_.append(cph_m.standard_errors_['CEA_IMP'] ** 2)
    # validation: CEA imputed WITHOUT outcome (deployment-like), predictors only
    imp_v = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw)
    imp_v.fit(np.column_stack([X_pred, X_cea])[trm])
    Xv = imp_v.transform(np.column_stack([X_pred, X_cea]))
    dv = d.copy(); dv['CEA_IMP'] = Xv[:, len(pred_cols)]
    lp_val.append(cph_m.predict_log_partial_hazard(dv.loc[vam, cox_cols]).values.ravel())
bar = float(np.mean(coefs))
W = float(np.mean(vars_)); B = float(np.var(coefs, ddof=1)); Tv = W + (1 + 1 / M_DRAWS) * B
se = np.sqrt(Tv)
lp_avg = np.mean(lp_val, axis=0)
mi = pd.DataFrame([{
    'strategy': 'Multiple imputation, 10 draws, outcome-compatible in development (Nelson-Aalen + event), predictor-only at validation',
    'CEA_HR_per_log_unit': round(float(np.exp(bar)), 3),
    'CEA_HR_95CI': f'{np.exp(bar-1.96*se):.3f}-{np.exp(bar+1.96*se):.3f}',
    'valid_C': round(float(concordance_index(Tva, -lp_avg, Eva)), 4),
    'valid_C_draw_range': f'{min(concordance_index(Tva, -x, Eva) for x in lp_val):.4f}-{max(concordance_index(Tva, -x, Eva) for x in lp_val):.4f}',
}])
save(mi, 'F20_CEA_multiple_imputation_sensitivity')
print(mi.to_string(index=False))

# ================================================================== 8. RFS with final definitions
log('8. RFS')
REC = pd.concat([xl(raw[f'RECDT_F{i}']) for i in range(1, 8)], axis=1).min(axis=1).loc[c.index]
T0c = g['d'].T0.loc[c.index]
LASTc = g['d'].LAST.loc[c.index]
DEATH = g['d'].STATUS.loc[c.index].eq('Deceased').values
AWD = raw.PATSTAT_F1.loc[c.index].eq('Alive with disease').values
rec_in = (REC.notna() & (REC >= T0c) & (REC <= LASTc)).values
rfs_days = np.where(rec_in, (REC - T0c).dt.days, (LASTc - T0c).dt.days).astype(float)
rfs_T = np.clip(np.minimum(rfs_days / DAYS, MAXFU), 1 / DAYS, None)
rfs_E = np.where(rec_in | DEATH | AWD, 1.0, 0.0)            # primary: 'alive with disease, no date' is an event
rfs_E_s = np.where(rec_in | DEATH, 1.0, 0.0)                # sensitivity: that group censored at last contact
rfs_source = np.select([rec_in, DEATH, AWD], ['recurrence date', 'death or last contact', 'alive with disease, no date'],
                       default='censored at last contact')
rfs_df = pd.DataFrame({'T': rfs_T, 'E': rfs_E, 'E_sens': rfs_E_s, 'era': c.ERA.values, 'grp_c3': grp_c3,
                       'source': rfs_source})
km_r = KaplanMeierFitter().fit(rfs_df['T'], rfs_df['E'])
ci_r = median_survival_times(km_r.confidence_interval_).iloc[0]
km_s = KaplanMeierFitter().fit(rfs_df['T'], rfs_df['E_sens'])
rfs_rows = [
    {'analysis': 'RFS primary (AWD without date = event at last contact)', 'n': len(rfs_df),
     'events': int(rfs_df.E.sum()), 'median_RFS_years': round(float(km_r.median_survival_time_), 2),
     'median_95CI': f'{ci_r.iloc[0]:.2f}-{ci_r.iloc[1]:.2f}',
     'RFS_1y': round(float(km_r.survival_function_at_times(1).iloc[0]), 3),
     'RFS_3y': round(float(km_r.survival_function_at_times(3).iloc[0]), 3),
     'RFS_5y': round(float(km_r.survival_function_at_times(5).iloc[0]), 3)},
    {'analysis': 'RFS sensitivity (AWD without date censored)', 'n': len(rfs_df),
     'events': int(rfs_df.E_sens.sum()), 'median_RFS_years': round(float(km_s.median_survival_time_), 2),
     'median_95CI': '', 'RFS_1y': round(float(km_s.survival_function_at_times(1).iloc[0]), 3),
     'RFS_3y': round(float(km_s.survival_function_at_times(3).iloc[0]), 3),
     'RFS_5y': round(float(km_s.survival_function_at_times(5).iloc[0]), 3)}]
save(pd.DataFrame(rfs_rows), 'F21_RFS_final_definition')
print(pd.DataFrame(rfs_rows).to_string(index=False))
print(rfs_df.source.value_counts().to_string())
rfs_grp_rows = []
for lab in ['Favourable', 'Intermediate', 'Adverse']:
    mm = (rfs_df.grp_c3 == lab).values
    k = KaplanMeierFitter().fit(rfs_T[mm], rfs_E[mm])
    rfs_grp_rows.append({'Cox M3 group': lab, 'n': int(mm.sum()), 'events': int(rfs_E[mm].sum()),
                         'median_RFS': round(float(k.median_survival_time_), 2) if np.isfinite(k.median_survival_time_) else None,
                         'RFS_5y': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
save(pd.DataFrame(rfs_grp_rows), 'F22_RFS_by_Cox_M3_group')
print(pd.DataFrame(rfs_grp_rows).to_string(index=False))
rfs_fit = CoxPHFitter().fit(pd.DataFrame(c.loc[trm, CORE_NOSTRAT].values, columns=CORE_NOSTRAT).assign(
    T=rfs_T[trm], E=rfs_E[trm]), 'T', 'E')
save(rfs_fit.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].round(4).reset_index(),
     'F23_RFS_Cox_hazard_ratios_training')
print(rfs_fit.summary[['exp(coef)', 'p']].round(4).to_string())

# ================================================================== 9. Fong CRS and Nordlinger-type benchmarks (proxies documented)
log('9. benchmarks')
d_ = g['d'].loc[c.index]
N_POS = d_.N_GRP.isin(['N1', 'N2']).astype(float).where(d_.N_GRP.notna())
DFI_LT12 = (d_.DFI < 12).astype(float).where(d_.DFI.notna())
MULTI = (d_.METS > 1).astype(float).where(d_.METS.notna())
SIZE50 = (d_.SIZE > 50).astype(float).where(d_.SIZE.notna())
CEA200 = (np.expm1(c.CEA_LOG) > 200).astype(float).where(c.CEA_LOG.notna())
FONG = pd.concat([N_POS, DFI_LT12, MULTI, SIZE50, CEA200], axis=1).sum(axis=1, min_count=5)
AGE60 = (d_.AGE >= 60).astype(float).where(d_.AGE.notna())
T4 = (d_.T_GRP == 'T4').astype(float).where(d_.T_GRP.notna())
NORD = pd.concat([AGE60, T4, N_POS, DFI_LT12], axis=1).sum(axis=1, min_count=4)
proxy_doc = pd.DataFrame([
    {'score': 'Fong CRS', 'criterion': 'node-positive primary', 'source': 'STADEN N1/N2', 'proxy': 'clinical N stage at diagnosis (pathological N not available)'},
    {'score': 'Fong CRS', 'criterion': 'disease-free interval < 12 months', 'source': 'DGKCOLDT to LE1DGMETADT (synchronous = 0)', 'proxy': 'interval to liver-metastasis diagnosis'},
    {'score': 'Fong CRS', 'criterion': 'more than one liver tumour', 'source': 'LE1NBMETAHEPNUM > 1', 'proxy': 'count at liver episode 1'},
    {'score': 'Fong CRS', 'criterion': 'largest tumour > 5 cm', 'source': 'LE1HEPMETASIZENUM > 50 mm', 'proxy': 'size field not confirmed as largest lesion'},
    {'score': 'Fong CRS', 'criterion': 'pre-operative CEA > 200 ng/mL', 'source': 'LE1PREHEPCEA_F1 > 200', 'proxy': 'pre-hepatectomy CEA; complete cases only'},
    {'score': 'Nordlinger-type', 'criterion': 'age >= 60; T4; node-positive; DFI < 12 months', 'source': 'as above', 'proxy': 'unweighted count; published Nordlinger weights not verified'},
    {'score': 'Basingstoke', 'criterion': 'differentiation grade, extrahepatic disease, margin', 'source': 'not available', 'proxy': 'not computed'},
])
save(proxy_doc, 'F24_benchmark_proxy_documentation')
bench = []
for label, score, mask_ in [('Fong CRS (CEA complete cases)', FONG, c.CEA_LOG.notna()),
                            ('Nordlinger-type (full cohort)', NORD, pd.Series(True, index=c.index))]:
    mtr_ = trm & mask_.values & score.notna().values
    mva_ = vam & mask_.values & score.notna().values
    bench.append({'benchmark': label, 'train_n': int(mtr_.sum()), 'valid_n': int(mva_.sum()),
                  'train_C': round(float(concordance_index(c.OS_Y[mtr_], -score[mtr_], c.OS_E[mtr_])), 4),
                  'valid_C': round(float(concordance_index(c.OS_Y[mva_], -score[mva_], c.OS_E[mva_])), 4)})
    # comparator on the same validation patients
    bench.append({'benchmark': label + ' | comparator: Cox M3 linear predictor, same patients', 'train_n': int(mtr_.sum()),
                  'valid_n': int(mva_.sum()),
                  'train_C': round(float(concordance_index(c.OS_Y[mtr_], -lp3[mtr_], c.OS_E[mtr_])), 4),
                  'valid_C': round(float(concordance_index(c.OS_Y[mva_], -lp3[mva_], c.OS_E[mva_])), 4)})
bench_df = save(pd.DataFrame(bench), 'F25_benchmark_C_index_same_patients')
print(bench_df.to_string(index=False))
log(f'done -> {RES}')
