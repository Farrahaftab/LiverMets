"""Evaluation v2: no-CEA Cox model, head-to-head comparison, three-group derivation, CEA missingness sensitivity.

All model fitting, cut-point derivation and tuning use training-era patients only (liver metastasis
diagnosis year <= 2009). Temporal validation (>= 2010) is used only to evaluate fixed models and rules.
Nothing here selects a threshold or model on validation outcomes; validation results are reported for all
candidates alongside each other.

Usage:
    LIVERMET_WORK_DIR=... LIVERMET_RESULTS_DIR=... python evaluation_v2.py
"""
import json
import os
import runpy
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test, logrank_test, proportional_hazard_test
from lifelines.utils import concordance_index, median_survival_times
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import cohen_kappa_score
from sksurv.metrics import brier_score, cumulative_dynamic_auc, integrated_brier_score
from sksurv.tree import SurvivalTree
from sksurv.util import Surv

warnings.filterwarnings('ignore')
T0 = time.time()
SEED = 42
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'evaluation_v2'
(RES / 'figures').mkdir(parents=True, exist_ok=True)
TIMES = np.array([1.0, 3.0, 5.0])
TIMES_BRIER = np.arange(1.0, 7.5, 0.5)
RNG = np.random.default_rng(SEED)


def log(msg):
    print(f'[{time.time()-T0:6.0f}s] {msg}', flush=True)


# ------------------------------------------------------------------ cohort (rebuilt by the primary methods script)
g = runpy.run_path('/home/user/LiverMets/notebooks/methods_comparison.py', run_name='methods')
c = g['c'].copy()
raw = g['raw']
trm = np.asarray(g['trm'], dtype=bool)
vam = np.asarray(g['vam'], dtype=bool)
assert len(c) == 13285 and trm.sum() == 6658 and vam.sum() == 6627
log(f'primary cohort {len(c):,}: train {trm.sum():,}, valid {vam.sum():,}')

# ------------------------------------------------------------------ covariates
c['AGE10'] = c.AGE / 10
c['DFI12'] = c.DFI / 12
c['SIZE10'] = c.SIZE / 10
for col in ['DFI', 'METS', 'SIZE', 'CEA_LOG']:
    c[col + '_NR'] = c[col].isna().astype(float)
for col in ['AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10', 'CEA_LOG']:
    c[col + '_F'] = c[col].fillna(c.loc[trm, col].median())   # median from training rows only

STAGE = ['T_GRP_T3', 'T_GRP_T4', 'N_GRP_N1', 'N_GRP_N2', 'M_GRP_M1']       # reference: T1-2, N0, M0
TNM_ALL = list(g['TNM_COLS'])                                             # full one-hot (trees only)
COX_NOCEA = STAGE + ['AGE10_F', 'MALE_F', 'SYNC_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
COX_CEA = COX_NOCEA + ['CEA_LOG_F', 'CEA_LOG_NR']
TREE_NOCEA = TNM_ALL + ['AGE10_F', 'MALE_F', 'SYNC_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
TREE_CEA = TREE_NOCEA + ['CEA_LOG_F', 'CEA_LOG_NR']
c['OS_Y'] = c.OS_Y.astype(float)
y_all = Surv.from_arrays(event=c.OS_E.astype(bool).values, time=c.OS_Y.values)
CEA_OBS = c.CEA_LOG.notna().values


# ------------------------------------------------------------------ helpers
def nonconstant(df, cols):
    return [x for x in cols if df[x].nunique() > 1]


def fit_cox(mask_tr, feats, pen=0.0):
    d = c.loc[mask_tr, feats + ['OS_Y', 'OS_E']]
    feats = nonconstant(d, feats)
    cph = CoxPHFitter(penalizer=pen).fit(d[feats + ['OS_Y', 'OS_E']], 'OS_Y', 'OS_E')
    return cph, feats


def cox_score(cph, feats, mask):
    """Higher = longer expected survival (negative log partial hazard)."""
    X = c.loc[mask, feats]
    return -cph.predict_log_partial_hazard(X).values.ravel()


def cox_surv(cph, feats, mask, times):
    X = c.loc[mask, feats]
    return cph.predict_survival_function(X, times=times).T.values


def tree_fit(mask_tr, feats, depth=3):
    X = c[feats].astype(float).values.astype(np.float32)
    tree = SurvivalTree(max_depth=depth, min_samples_leaf=max(200, int(0.02 * mask_tr.sum())), random_state=SEED)
    tree.fit(X[mask_tr], y_all[mask_tr])
    return tree, X


def tree_model(mask_tr, feats, depth=3):
    """Leaf-level training KM: score = 5-year RMST, survival matrix = leaf KM at TIMES."""
    tree, X = tree_fit(mask_tr, feats, depth)
    leaf_all = tree.apply(X)
    rows, rmst, surv_leaf = [], {}, {}
    for L in np.unique(leaf_all):
        m = (leaf_all == L) & mask_tr
        s = c[m]
        k = KaplanMeierFitter().fit(s.OS_Y, s.OS_E)
        tt = k.survival_function_.index.values.astype(float)
        ss = k.survival_function_.iloc[:, 0].values.astype(float)
        grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
        idx = np.searchsorted(tt, grid[:-1], side='right') - 1
        rmst[L] = float(np.sum(np.where(idx >= 0, ss[np.clip(idx, 0, None)], 1.0) * np.diff(grid)))
        surv_leaf[L] = np.array([float(k.survival_function_at_times(t).iloc[0]) for t in TIMES])
        med = k.median_survival_time_
        rows.append({'leaf': int(L), 'train_n': int(m.sum()), 'train_deaths': int(s.OS_E.sum()),
                     'train_median_OS': round(float(med), 2) if np.isfinite(med) else None,
                     'train_RMST5': round(rmst[L], 3)})
    score = np.array([rmst[L] for L in leaf_all])
    surv = np.array([surv_leaf[L] for L in leaf_all])
    # tie fraction in the validation set: share of comparable pairs with identical score
    return score, surv, pd.DataFrame(rows), tree, feats


def km_median_ci(s):
    k = KaplanMeierFitter().fit(s.OS_Y, s.OS_E)
    med = k.median_survival_time_
    ci = median_survival_times(k.confidence_interval_)
    lo, hi = ci.iloc[0, 0], ci.iloc[0, 1]
    f = lambda v: round(float(v), 2) if np.isfinite(v) else None   # noqa: E731
    return f(med), f(lo), f(hi), round(float(k.survival_function_at_times(5).iloc[0]), 3)


def metrics(name, s_tr, s_va_score, S_va, mva, mtr):
    """s_va_score: higher = better. S_va: survival probabilities at TIMES for validation rows."""
    y_tr = Surv.from_arrays(c.OS_E[mtr].astype(bool).values, c.OS_Y[mtr].values)
    y_va = Surv.from_arrays(c.OS_E[mva].astype(bool).values, c.OS_Y[mva].values)
    tt = c.OS_Y[mva].values
    ee = c.OS_E[mva].values
    cidx_tr = concordance_index(c.OS_Y[mtr], s_tr, c.OS_E[mtr])
    cidx_va = concordance_index(tt, s_va_score, ee)
    boots = []
    for _ in range(300):
        b = RNG.integers(0, len(tt), len(tt))
        boots.append(concordance_index(tt[b], s_va_score[b], ee[b]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    out = {'model': name, 'train_C': round(float(cidx_tr), 4), 'valid_C': round(float(cidx_va), 4),
           'valid_C_95CI': f'{lo:.3f}-{hi:.3f}'}
    try:
        auc, _ = cumulative_dynamic_auc(y_tr, y_va, -s_va_score, TIMES)  # risk = -score
        for t, a in zip(TIMES, auc):
            out[f'tAUC_{int(t)}y'] = round(float(a), 3)
    except Exception as ex:  # noqa: BLE001
        out['tAUC_note'] = str(ex)[:80]
    return out, y_tr, y_va


def brier_block(y_tr, y_va, S_va):
    out = {}
    try:
        _, bs = brier_score(y_tr, y_va, S_va, TIMES)
        for t, b in zip(TIMES, bs):
            out[f'Brier_{int(t)}y'] = round(float(b), 4)
    except Exception as ex:  # noqa: BLE001
        out['Brier_note'] = str(ex)[:80]
    return out


def calib_block(score_va, S5_va, mva, label):
    """Decile calibration at 5 years, calibration slope (Cox on validation), observed/expected ratio."""
    dec = pd.qcut(pd.Series(S5_va).rank(method='first'), 10, labels=False).values
    rows = []
    t_va = c.OS_Y[mva].values
    e_va = c.OS_E[mva].values
    for q in range(10):
        m = dec == q
        k = KaplanMeierFitter().fit(t_va[m], e_va[m])
        rows.append({'model': label, 'decile': q + 1, 'n': int(m.sum()), 'predicted_S5': round(float(S5_va[m].mean()), 3),
                     'observed_S5': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    obs = KaplanMeierFitter().fit(t_va, e_va).survival_function_at_times(5).iloc[0]
    slope_df = pd.DataFrame({'T': t_va, 'E': e_va, 'risk': -score_va})
    slope = CoxPHFitter().fit(slope_df, 'T', 'E')
    summary = {'model': label, 'calib_slope': round(float(slope.params_['risk']), 3),
               'OE_ratio_5y': round(float(obs / S5_va.mean()), 3),
               'mean_pred_S5': round(float(S5_va.mean()), 3), 'observed_S5_KM': round(float(obs), 3)}
    return pd.DataFrame(rows), summary


# ================================================================== A. Cox no-CEA model: fit, metrics, PH diagnostics
log('A. no-CEA Cox model')
cph_nc, feats_nc = fit_cox(trm, COX_NOCEA)
hr = cph_nc.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
hr.columns = ['term', 'coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
hr.round(4).to_csv(RES / 'E01_Cox_noCEA_hazard_ratios.csv', index=False)
print(hr.round(3).to_string(index=False))

d_tr = c.loc[trm, feats_nc + ['OS_Y', 'OS_E']]
ph = proportional_hazard_test(cph_nc, d_tr, time_transform='rank').summary.reset_index()
ph.columns = ['term'] + list(ph.columns[1:])
ph.round(4).to_csv(RES / 'E02_Cox_noCEA_PH_test.csv', index=False)
print(ph.round(4).to_string(index=False))

s_cox_tr = cox_score(cph_nc, feats_nc, trm)
s_cox_va = cox_score(cph_nc, feats_nc, vam)
S_cox_va = cox_surv(cph_nc, feats_nc, vam, TIMES)
m_cox, y_tr_full, y_va_full = metrics('Cox no-CEA (full cohort)', s_cox_tr, s_cox_va, S_cox_va, vam, trm)
m_cox.update(brier_block(y_tr_full, y_va_full, S_cox_va))
try:
    m_cox['IBS_1_to_7y'] = round(float(integrated_brier_score(y_tr_full, y_va_full, cox_surv(cph_nc, feats_nc, vam, TIMES_BRIER), TIMES_BRIER)), 4)
except Exception as ex:  # noqa: BLE001
    m_cox['IBS_note'] = str(ex)[:80]
cal_cox, cal_cox_s = calib_block(s_cox_va, S_cox_va[:, 2], vam, 'Cox no-CEA (full cohort)')
cal_cox.to_csv(RES / 'E03_calibration_deciles_Cox_noCEA.csv', index=False)
print(m_cox); print(cal_cox_s)

# ================================================================== B. head-to-head on identical CEA-observed patients
log('B. head-to-head on CEA-observed patients')
mtr_b = trm & CEA_OBS
mva_b = vam & CEA_OBS
rows_b, cal_b, cal_b_sum = [], [], []
S_by_model = {}
# Cox no-CEA on the same patients
cph_b_nc, f_b_nc = fit_cox(mtr_b, COX_NOCEA)
sc_tr = cox_score(cph_b_nc, f_b_nc, mtr_b)
sc_va = cox_score(cph_b_nc, f_b_nc, mva_b)
S_va = cox_surv(cph_b_nc, f_b_nc, mva_b, TIMES)
mm, ytr, yva = metrics('Cox no-CEA', sc_tr, sc_va, S_va, mva_b, mtr_b)
mm.update(brier_block(ytr, yva, S_va)); rows_b.append(mm)
cb, cs = calib_block(sc_va, S_va[:, 2], mva_b, 'Cox no-CEA'); cal_b.append(cb); cal_b_sum.append(cs)
# Cox with CEA (complete case)
cph_b_c, f_b_c = fit_cox(mtr_b, COX_NOCEA + ['CEA_LOG'])
sc_tr = cox_score(cph_b_c, f_b_c, mtr_b)
sc_va = cox_score(cph_b_c, f_b_c, mva_b)
S_va = cox_surv(cph_b_c, f_b_c, mva_b, TIMES)
mm, ytr, yva = metrics('Cox with CEA (complete case)', sc_tr, sc_va, S_va, mva_b, mtr_b)
mm.update(brier_block(ytr, yva, S_va)); rows_b.append(mm)
cb, cs = calib_block(sc_va, S_va[:, 2], mva_b, 'Cox with CEA (complete case)'); cal_b.append(cb); cal_b_sum.append(cs)
cea_hr_cc = cph_b_c.summary.loc['CEA_LOG', ['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].to_dict()
# Trees on the same patients
for name, feats, depth in [('TNM-only survival tree', TNM_ALL, 3), ('Expanded survival tree (no CEA)', TREE_NOCEA, 3),
                           ('Expanded survival tree (with CEA)', TREE_CEA, 3)]:
    mtr_t = mtr_b
    score_all, surv_all, leaves_tbl, tree_obj, _ = tree_model(mtr_t, feats, depth)
    sc_tr = score_all[mtr_t]
    sc_va = score_all[mva_b]
    S_va = surv_all[mva_b]
    mm, ytr, yva = metrics(name, sc_tr, sc_va, S_va, mva_b, mtr_t)
    mm.update(brier_block(ytr, yva, S_va)); rows_b.append(mm)
    cb, cs = calib_block(sc_va, S_va[:, 2], mva_b, name); cal_b.append(cb); cal_b_sum.append(cs)
    leaves_tbl.to_csv(RES / f'E04_leaves_{name.split()[0]}_{"noCEA" if "no CEA" in name else ("CEA" if "with CEA" in name else "TNM")}_identicalCEAcohort.csv', index=False)
    # ties: share of validation pairs with identical predicted score
    _, cnt = np.unique(sc_va, return_counts=True)
    n = len(sc_va)
    rows_b[-1]['valid_tied_pair_share'] = round(float((cnt * (cnt - 1) / 2).sum() / (n * (n - 1) / 2)), 4)
    rows_b[-1]['n_leaves'] = int(len(leaves_tbl))
b_df = pd.DataFrame(rows_b)
b_df.to_csv(RES / 'E05_head_to_head_identical_CEA_cohort.csv', index=False)
pd.concat(cal_b).to_csv(RES / 'E06_calibration_deciles_identical_cohort.csv', index=False)
pd.DataFrame(cal_b_sum).to_csv(RES / 'E06b_calibration_summary_identical_cohort.csv', index=False)
print(b_df.to_string(index=False))
print(pd.DataFrame(cal_b_sum).to_string(index=False))
print('Cox with CEA, CEA_LOG hazard ratio (complete case):', {k: round(float(v), 3) for k, v in cea_hr_cc.items()})

# ------------------------------------------------------------------ same comparison on the full cohort for no-CEA models
rows_full = [m_cox]
for name, feats in [('TNM-only survival tree', TNM_ALL), ('Expanded survival tree (no CEA)', TREE_NOCEA)]:
    score_all, surv_all, leaves_tbl, _, _ = tree_model(trm, feats, 3)
    mm, ytr, yva = metrics(name + ' (full cohort)', score_all[trm], score_all[vam], surv_all[vam], vam, trm)
    mm.update(brier_block(ytr, yva, surv_all[vam])); mm['n_leaves'] = int(len(leaves_tbl))
    rows_full.append(mm)
    leaves_tbl.to_csv(RES / f'E07_leaves_{name.split()[0]}_fullcohort.csv', index=False)
pd.DataFrame(rows_full).to_csv(RES / 'E08_full_cohort_models.csv', index=False)
print(pd.DataFrame(rows_full).to_string(index=False))

# ================================================================== C. survival-tree C-index: limits, depth, ties
log('C. survival tree diagnostics')
diag = []
for depth in [2, 3, 4]:
    for name, feats in [('TNM-only', TNM_ALL), ('no CEA', TREE_NOCEA)]:
        sc, _, lt, _, _ = tree_model(trm, feats, depth)
        diag.append({'tree': name, 'max_depth': depth, 'n_leaves': int(len(lt)),
                     'train_C': round(float(concordance_index(c.OS_Y[trm], sc[trm], c.OS_E[trm])), 4),
                     'valid_C': round(float(concordance_index(c.OS_Y[vam], sc[vam], c.OS_E[vam])), 4)})
diag_df = pd.DataFrame(diag)
diag_df.to_csv(RES / 'E09_tree_depth_diagnostic.csv', index=False)
print(diag_df.to_string(index=False))
# identical predictors: Cox vs tree (full cohort, no CEA)
cox_same = cph_nc.concordance_index_
print('Cox and tree share predictors (no CEA): Cox train C', round(float(cox_same), 4),
      '| Cox valid C', m_cox['valid_C'])

# ================================================================== D. CEA missingness sensitivity
log('D. CEA missingness sensitivity')
sens = []
# 1 complete case (already in B): record HR from B
sens.append({'strategy': 'Complete case (CEA recorded only)', 'n_train': int(mtr_b.sum()), 'n_valid': int(mva_b.sum()),
             'CEA_HR_per_log_unit': round(float(cea_hr_cc['exp(coef)']), 3),
             'CEA_HR_95CI': f"{cea_hr_cc['exp(coef) lower 95%']:.3f}-{cea_hr_cc['exp(coef) upper 95%']:.3f}",
             'valid_C': rows_b[1]['valid_C']})
# 2 median fill + not-recorded indicator (full cohort)
cph_med, f_med = fit_cox(trm, COX_CEA)
sc_va = cox_score(cph_med, f_med, vam)
sens.append({'strategy': 'Median fill + not-recorded indicator (full cohort)', 'n_train': int(trm.sum()),
             'n_valid': int(vam.sum()),
             'CEA_HR_per_log_unit': round(float(cph_med.summary.loc['CEA_LOG_F', 'exp(coef)']), 3),
             'CEA_HR_95CI': f"{cph_med.summary.loc['CEA_LOG_F', 'exp(coef) lower 95%']:.3f}-{cph_med.summary.loc['CEA_LOG_F', 'exp(coef) upper 95%']:.3f}",
             'valid_C': round(float(concordance_index(c.OS_Y[vam], sc_va, c.OS_E[vam])), 4)})
# 3 zero fill + not-recorded indicator (full cohort): shown only to demonstrate coding sensitivity
c['CEA_ZERO'] = c.CEA_LOG.fillna(0.0)
c['CEA_ZERO_NR'] = c.CEA_LOG.isna().astype(float)
cph_z, f_z = fit_cox(trm, STAGE + ['AGE10_F', 'MALE_F', 'SYNC_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR', 'CEA_ZERO', 'CEA_ZERO_NR'])
sc_va = cox_score(cph_z, f_z, vam)
sens.append({'strategy': 'Zero fill + not-recorded indicator (full cohort, coding check only)', 'n_train': int(trm.sum()),
             'n_valid': int(vam.sum()), 'CEA_HR_per_log_unit': round(float(cph_z.summary.loc['CEA_ZERO', 'exp(coef)']), 3),
             'CEA_HR_95CI': f"{cph_z.summary.loc['CEA_ZERO', 'exp(coef) lower 95%']:.3f}-{cph_z.summary.loc['CEA_ZERO', 'exp(coef) upper 95%']:.3f}",
             'valid_C': round(float(concordance_index(c.OS_Y[vam], sc_va, c.OS_E[vam])), 4)})
# 4 multiple imputation (predictors only, 5 draws), Cox pooled by averaging coefficients
mi_cols = ['T_GRP_T3', 'T_GRP_T4', 'N_GRP_N1', 'N_GRP_N2', 'M_GRP_M1', 'AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10', 'CEA_LOG']
mi_X = c[mi_cols].astype(float).values
coefs, hrs, cvals = [], [], []
for draw in range(5):
    imp = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw)
    imp.fit(mi_X[trm])                                      # imputation model fitted on training rows
    Xi = imp.transform(mi_X)
    dfi = pd.DataFrame(Xi, columns=mi_cols, index=c.index)
    dfi['OS_Y'] = c.OS_Y.values; dfi['OS_E'] = c.OS_E.values
    cols = STAGE + ['AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10', 'CEA_LOG']
    cph_i = CoxPHFitter().fit(dfi.loc[trm, cols + ['OS_Y', 'OS_E']], 'OS_Y', 'OS_E')
    coefs.append(cph_i.params_['CEA_LOG']); hrs.append(float(np.exp(cph_i.params_['CEA_LOG'])))
    sc_va = -cph_i.predict_log_partial_hazard(dfi.loc[vam, cols]).values.ravel()
    cvals.append(concordance_index(c.OS_Y[vam], sc_va, c.OS_E[vam]))
pooled = float(np.mean(coefs))
sens.append({'strategy': 'Multiple imputation, 5 draws (predictors only; outcome not in imputation model)',
             'n_train': int(trm.sum()), 'n_valid': int(vam.sum()),
             'CEA_HR_per_log_unit': round(float(np.exp(pooled)), 3),
             'CEA_HR_95CI': f'draw range {min(hrs):.3f}-{max(hrs):.3f}',
             'valid_C': round(float(np.mean(cvals)), 4)})
sens_df = pd.DataFrame(sens)
sens_df.to_csv(RES / 'E10_CEA_missingness_sensitivity.csv', index=False)
print(sens_df.to_string(index=False))

# outcome by CEA recording (identical cohort)
rec = c.assign(rec=c.CEA_LOG.notna())
rec_rows = []
for k_, s in rec.groupby('rec'):
    med, lo, hi, s5 = km_median_ci(s)
    rec_rows.append({'CEA_recorded': bool(k_), 'n': len(s), 'deaths': int(s.OS_E.sum()), 'median_OS': med,
                     'median_95CI': f'{lo}-{hi}', 'S5': s5})
rec_df = pd.DataFrame(rec_rows)
rec_df.to_csv(RES / 'E11_CEA_recording_outcome.csv', index=False)
print(rec_df.to_string(index=False))

# ================================================================== E. three-group derivation (training only)
log('E. three-group derivation')
lp_tr = cph_nc.predict_log_partial_hazard(c.loc[trm, feats_nc]).values.ravel()
lp_all = cph_nc.predict_log_partial_hazard(c[feats_nc]).values.ravel()


def cut_groups(lp_all_, k, lp_train):
    qs = np.quantile(lp_train, np.linspace(0, 1, k + 1)[1:-1])
    return np.searchsorted(qs, lp_all_, side='right'), qs     # 0 = lowest risk


def group_names(k):
    return {3: ['Favourable', 'Intermediate', 'Adverse'], 2: ['Favourable', 'Adverse'],
            4: ['Favourable', 'Intermediate', 'Adverse', 'High-risk']}[k]


grp_rows = []
for k in [2, 3, 4]:
    gi, qs = cut_groups(lp_all, k, lp_tr)
    labels = group_names(k)
    c[f'G{k}'] = np.array(labels)[gi]
    tr_p = multivariate_logrank_test(c.OS_Y[trm], gi[trm], c.OS_E[trm]).p_value
    va_p = multivariate_logrank_test(c.OS_Y[vam], gi[vam], c.OS_E[vam]).p_value
    grp_rows.append({'n_groups': k, 'cut_points_LP': np.round(qs, 3).tolist(),
                     'train_logrank_p': float(tr_p), 'valid_logrank_p': float(va_p),
                     'valid_C_group': round(float(concordance_index(c.OS_Y[vam], -gi[vam], c.OS_E[vam])), 4)})
pd.DataFrame(grp_rows).to_csv(RES / 'E12_group_number_comparison_training_criteria.csv', index=False)
print(pd.DataFrame(grp_rows).to_string(index=False))

# Three-group table with CI, median OS, 5-year OS, both periods
gi3, qs3 = cut_groups(lp_all, 3, lp_tr)
c['G3'] = np.array(group_names(3))[gi3]
tab = []
for period, mask in [('training', trm), ('validation', vam)]:
    for lab in group_names(3):
        s = c[mask & (c.G3.values == lab)]
        med, lo, hi, s5 = km_median_ci(s)
        tab.append({'period': period, 'group': lab, 'n': len(s), 'share_pct': round(100 * len(s) / mask.sum(), 1),
                    'deaths': int(s.OS_E.sum()), 'median_OS': med, 'median_95CI': f'{lo}-{hi}', 'S5': s5})
tab_df = pd.DataFrame(tab)
tab_df.to_csv(RES / 'E13_three_group_cohort_table.csv', index=False)
print(tab_df.to_string(index=False))

# separation: pairwise validation log-rank, Bonferroni 3
pair = []
for a, b_ in [('Favourable', 'Intermediate'), ('Intermediate', 'Adverse'), ('Favourable', 'Adverse')]:
    ma = vam & (c.G3.values == a); mb = vam & (c.G3.values == b_)
    p = logrank_test(c.OS_Y[ma], c.OS_Y[mb], c.OS_E[ma], c.OS_E[mb]).p_value
    pair.append({'comparison': f'{a} vs {b_}', 'valid_logrank_p_bonferroni': min(1.0, 3 * p)})
pd.DataFrame(pair).to_csv(RES / 'E14_three_group_pairwise_validation.csv', index=False)
print(pd.DataFrame(pair).to_string(index=False))

# temporal stability: validation sub-periods
sub_rows = []
for lab, mask in [('2010-2014', vam & (c.T0.dt.year.values <= 2014)), ('2015 onwards', vam & (c.T0.dt.year.values >= 2015))]:
    gg = c.G3.values
    p = multivariate_logrank_test(c.OS_Y[mask], gg[mask], c.OS_E[mask]).p_value
    row = {'validation_subperiod': lab, 'n': int(mask.sum()), 'logrank_p': float(p)}
    for lab2 in group_names(3):
        s = c[mask & (gg == lab2)]
        row[f'{lab2}_n'] = len(s)
        row[f'{lab2}_median'] = km_median_ci(s)[0]
    sub_rows.append(row)
pd.DataFrame(sub_rows).to_csv(RES / 'E15_validation_subperiod_stability.csv', index=False)
print(pd.DataFrame(sub_rows).to_string(index=False))

# bootstrap stability of training-derived cut-points and group assignment (training resamples only)
kappas, cuts = [], []
base_assign = gi3[vam]
tr_ids = np.where(trm)[0]
for b in range(200):
    pick = RNG.choice(tr_ids, size=len(tr_ids), replace=True)
    d_b = c.iloc[pick][feats_nc + ['OS_Y', 'OS_E']]
    try:
        cph_b = CoxPHFitter().fit(d_b, 'OS_Y', 'OS_E')
    except Exception:  # noqa: BLE001
        continue
    lp_b_tr = cph_b.predict_log_partial_hazard(c.iloc[pick][feats_nc]).values.ravel()
    lp_b_va = cph_b.predict_log_partial_hazard(c.loc[vam, feats_nc]).values.ravel()
    qs_b = np.quantile(lp_b_tr, [1 / 3, 2 / 3])
    cuts.append(qs_b)
    gb = np.searchsorted(qs_b, lp_b_va, side='right')
    kappas.append(cohen_kappa_score(base_assign, gb))
stab = {'bootstrap_resamples': len(kappas), 'cut1_median': round(float(np.median([x[0] for x in cuts])), 3),
        'cut1_95pct_range': f"{np.percentile([x[0] for x in cuts], 2.5):.3f}-{np.percentile([x[0] for x in cuts], 97.5):.3f}",
        'cut2_median': round(float(np.median([x[1] for x in cuts])), 3),
        'cut2_95pct_range': f"{np.percentile([x[1] for x in cuts], 2.5):.3f}-{np.percentile([x[1] for x in cuts], 97.5):.3f}",
        'kappa_vs_main_median': round(float(np.median(kappas)), 3),
        'kappa_vs_main_2.5pct': round(float(np.percentile(kappas, 2.5)), 3)}
pd.DataFrame([stab]).to_csv(RES / 'E16_bootstrap_stability_cutpoints.csv', index=False)
print(stab)

# Survival-tree three groups (merged leaves by training RMST), for comparison with the Cox-based groups
score_nc_tree, _, leaves_nc, _, _ = tree_model(trm, TREE_NOCEA, 3)
gtree, qs_tree = cut_groups(-score_nc_tree, 3, -score_nc_tree[trm])
tree_tab = []
for lab_i, lab in enumerate(group_names(3)):
    pass
print('tree tertile cut-points (RMST):', np.round(np.quantile(score_nc_tree[trm], [1 / 3, 2 / 3]), 3).tolist(),
      '| training patients per RMST tertile are tied at leaf level (see E04/E07)')

# ================================================================== F. figures
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 5))
for lab, col in [('Favourable', '#1B7837'), ('Intermediate', '#E08214'), ('Adverse', '#B2182B')]:
    m = vam & (c.G3.values == lab)
    KaplanMeierFitter().fit(c.OS_Y[m], c.OS_E[m], label=f'{lab} (n={m.sum():,})').plot_survival_function(ax=ax, color=col, ci_show=True, show_censors=False)
ax.set_xlim(0, 10); ax.set_ylim(0, 1.01); ax.grid(alpha=0.25)
ax.set_title('Cox no-CEA risk tertiles (validation era, cut-points from training)')
ax.set_xlabel('Years from liver metastasis diagnosis'); ax.set_ylabel('Overall survival')
fig.savefig(RES / 'figures' / 'E_three_group_validation_KM.png', dpi=200, bbox_inches='tight'); plt.close(fig)
log(f'done -> {RES}')
