"""Methodological comparison: time origin, TNM-only vs expanded survival trees, and three-group classification.

Runs on the combined extract written by the main notebook (both source parts, 29,565 patients).
Development (tree growth, leaf risk scores, tertile cut-points, Cox fitting) uses training-era
patients only (liver metastasis diagnosis year <= 2009). Temporal validation (>= 2010) is used only
to evaluate fixed rules.

Usage:
    LIVERMET_WORK_DIR=... LIVERMET_RESULTS_DIR=... python methods_comparison.py
"""
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test
from lifelines.utils import concordance_index
from sksurv.tree import SurvivalTree
from sksurv.util import Surv

SEED = 42
WORK = Path(os.environ.get('LIVERMET_WORK_DIR', '/content/work'))
RES = Path(os.environ.get('LIVERMET_RESULTS_DIR', '/content/results')) / 'methods_comparison'
RES.mkdir(parents=True, exist_ok=True)
(RES / 'figures').mkdir(exist_ok=True)
DAYS = 365.25
MAXFU = 15.0
MISS = ['ND', 'NA', '']
EP = pd.Timestamp('1899-12-30')
ERA_YEAR = 2009
t_start = time.time()


def log(msg):
    print(f'[{time.time()-t_start:6.0f}s] {msg}', flush=True)


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def xl(s, lo=1, hi=80000):
    v = num(s)
    v = v.where((v >= lo) & (v <= hi))
    return EP + pd.to_timedelta(v, unit='D')


def yn(s):
    return s.map({'Yes': 1.0, 'No': 0.0})


# ---------------------------------------------------------------- derivations (same rules as the notebook)
raw = pd.read_parquet(WORK / 'combined_extract.parquet')
log(f'loaded {len(raw):,} rows: {raw.SOURCE_PART.value_counts().to_dict()}')
d = pd.DataFrame(index=raw.index)
d['SOURCE_PART'] = raw.SOURCE_PART
d['T0'] = xl(raw.LE1DGMETADT)              # liver metastasis diagnosis (primary time zero)
d['REF'] = xl(raw.REFERDT)                 # referral
d['HEP'] = xl(raw.LE1METARESECDT_L1)       # first hepatic resection of metastasis (lesion 1)
d['LAST'] = xl(raw.LASTNDTC)
d['DGK'] = xl(raw.DGKCOLDT)
d['BIRTH'] = xl(raw.BIRTHDT)
d['STATUS'] = raw.PATSTATC.where(raw.PATSTATC.isin(['Alive', 'Deceased', 'Lost to follow-up']))
d['EVENT_DEATH'] = d.STATUS.map({'Deceased': 1.0, 'Alive': 0.0, 'Lost to follow-up': 0.0})
d['SURG'] = yn(raw.LE1HEPATECTYN_F1)

TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def grp(s, m):
    return s.astype(object).map(lambda v: m.get(v, np.nan) if isinstance(v, str) else np.nan)


d['T_GRP'] = grp(raw.STADET, TMAP)
d['N_GRP'] = grp(raw.STADEN, NMAP)
d['M_GRP'] = grp(raw.STADEM, MMAP)
d['TNM'] = d[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)
d['AGE'] = (d.T0 - d.BIRTH).dt.days / DAYS
d.loc[(d.AGE < 18) | (d.AGE > 100), 'AGE'] = np.nan
d['MALE'] = raw.GENDER.map({'Male': 1.0, 'Female': 0.0})
d['SYNC'] = yn(raw.LE1METASYNCYN)
d['METS'] = num(raw.LE1NBMETAHEPNUM)
d.loc[(d.METS < 1) | (d.METS > 50), 'METS'] = np.nan
d['SIZE'] = num(raw.LE1HEPMETASIZENUM)
d.loc[(d.SIZE <= 0) | (d.SIZE > 300), 'SIZE'] = np.nan
d['CEA_LOG'] = np.log1p(num(raw.LE1PREHEPCEA_F1).clip(lower=0))
d['DFI'] = (d.T0 - d.DGK).dt.days / 30.4375
d.loc[d.SYNC == 1, 'DFI'] = 0.0
d.loc[d.DFI < 0, 'DFI'] = np.nan
d['ERA'] = np.where(d.T0.dt.year <= ERA_YEAR, 'train', 'valid')
d.loc[d.T0.isna(), 'ERA'] = None


def os_fields(origin_col, mask_extra=None):
    """OS time from a chosen origin. Event = death; alive and lost are censored at last contact."""
    days = (d.LAST - d[origin_col]).dt.days
    ok = d.TNM & d[origin_col].notna() & d.STATUS.notna() & (days > 0)
    if mask_extra is not None:
        ok &= mask_extra
    t = np.minimum(days / DAYS, MAXFU)
    e = np.where(days / DAYS > MAXFU, 0.0, d.EVENT_DEATH)
    return ok, t, e


# ---------------------------------------------------------------- 1. time origin comparison
log('time origin comparison')
origins = {
    'Liver metastasis diagnosis (LE1DGMETADT)': ('T0', None),
    'Referral date (REFERDT)': ('REF', None),
    'First hepatic resection of metastasis (LE1METARESECDT_L1)': ('HEP', (d.SURG == 1)),
}
orig_rows, orig_km = [], {}
for name, (col, extra) in origins.items():
    ok, t, e = os_fields(col, extra)
    sub = pd.DataFrame({'t': t[ok], 'e': e[ok], 'era': d.ERA[ok], 'part': d.SOURCE_PART[ok]})
    km = KaplanMeierFitter().fit(sub.t, sub.e)
    orig_km[name] = sub
    row = {'origin': name, 'n_eligible': int(ok.sum()), 'deaths': int(sub.e.sum()),
           'train_n': int((sub.era == 'train').sum()), 'valid_n': int((sub.era == 'valid').sum()),
           'median_OS_years': round(float(km.median_survival_time_), 2) if np.isfinite(km.median_survival_time_) else None,
           'S_1y': round(float(km.survival_function_at_times(1).iloc[0]), 3),
           'S_3y': round(float(km.survival_function_at_times(3).iloc[0]), 3),
           'S_5y': round(float(km.survival_function_at_times(5).iloc[0]), 3),
           'median_follow_up_reverse_KM': round(float(KaplanMeierFitter().fit(sub.t, 1 - sub.e).median_survival_time_), 2)}
    orig_rows.append(row)
orig_df = pd.DataFrame(orig_rows)
# valid-date audit for the hepatectomy origin (must follow diagnosis)
hep_ok = d.HEP.notna() & d.T0.notna()
audit = {'hepatectomy_date_present': int(d.HEP.notna().sum()),
         'hepatectomy_before_diagnosis': int((d.HEP < d.T0).sum()),
         'hepatectomy_flag_yes_but_no_date': int(((d.SURG == 1) & d.HEP.isna()).sum()),
         'referral_after_diagnosis': int((d.REF > d.T0).sum()),
         'referral_before_diagnosis': int((d.REF < d.T0).sum())}
orig_df.to_csv(RES / 'M01_time_origin_comparison.csv', index=False)
json.dump(audit, open(RES / 'M01b_origin_date_audit.json', 'w'), indent=1)
print(orig_df.to_string(index=False))
print('origin date audit:', audit)

# ---------------------------------------------------------------- 2. cohort reconciliation with earlier numbers
log('cohort reconciliation')
primary = d.TNM & d.T0.notna() & d.STATUS.notna() & ((d.LAST - d.T0).dt.days > 0)
recon = pd.DataFrame([
    {'stage': 'All patients (both parts)', 'n': len(d)},
    {'stage': 'TNM complete', 'n': int(d.TNM.sum())},
    {'stage': 'TNM complete + liver metastasis diagnosis date', 'n': int((d.TNM & d.T0.notna()).sum())},
    {'stage': 'TNM complete + valid OS (current primary cohort)', 'n': int(primary.sum())},
    {'stage': 'TNM complete + referral date + valid OS (alternative origin)', 'n': int(os_fields('REF')[0].sum())},
    {'stage': 'Published survival-eligible cohort (earlier analysis, not reproducible here)', 'n': 14759},
])
recon.to_csv(RES / 'M02_cohort_reconciliation.csv', index=False)
print(recon.to_string(index=False))

# ---------------------------------------------------------------- primary cohort and training/validation split
ok, T, E = os_fields('T0')
c = d[ok].copy()
c['OS_Y'] = T[ok].values
c['OS_E'] = E[ok]
tr = c[c.ERA == 'train']
va = c[c.ERA == 'valid']
log(f'primary cohort {len(c):,} | train {len(tr):,} (deaths {int(tr.OS_E.sum()):,}) | valid {len(va):,} (deaths {int(va.OS_E.sum()):,})')
assert len(c) == 13285 and len(tr) == 6658 and len(va) == 6627, 'does not match the notebook cohort counts'

# ---------------------------------------------------------------- feature sets
TNM_COLS = []
tnm_dum = pd.get_dummies(c[['T_GRP', 'N_GRP', 'M_GRP']].astype(str), dtype=float)
tnm_dum.columns = [x.replace(' ', '') for x in tnm_dum.columns]
c = pd.concat([c, tnm_dum], axis=1)
TNM_COLS = list(tnm_dum.columns)
EXP_CONT = ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE', 'CEA_LOG']
EXP_MISS = ['METS', 'SIZE', 'CEA_LOG', 'DFI']
c['AGE_NA'] = c.AGE.isna().astype(float)  # kept only for documentation of missingness


def prep(train_idx, all_idx, cols, miss_cols):
    """Fit imputation on the training rows only; apply to all rows."""
    X = c[cols].astype(float).copy()
    med = X.loc[train_idx].median()
    out = X.copy()
    for m in miss_cols:
        if m in X.columns:
            out[m + '_MISSING'] = X[m].isna().astype(float)
    for col in cols:
        out[col] = X[col].fillna(med[col])
    return out.loc[all_idx]


TNM_FEAT = TNM_COLS
EXP_FEAT = TNM_COLS + EXP_CONT


def run_tree(feature_cols, miss_cols, name):
    tr_idx = c.index[c.ERA == 'train']
    all_idx = c.index
    Xall = prep(tr_idx, all_idx, feature_cols, miss_cols)
    y = Surv.from_arrays(event=c.OS_E.astype(bool).values, time=c.OS_Y.values)
    mask = c.index.isin(tr_idx)
    min_leaf = max(200, int(0.02 * mask.sum()))
    tree = SurvivalTree(max_depth=3, min_samples_leaf=min_leaf, random_state=SEED)
    tree.fit(Xall.values.astype(np.float32)[mask], y[mask])
    leaf = tree.apply(Xall.values.astype(np.float32))
    c[f'{name}_LEAF'] = leaf
    # leaf risk = training-only 5-year restricted mean survival (higher = better)
    leaf_rows = []
    rmst5 = {}
    for L in np.unique(leaf):
        mtr = (leaf == L) & mask
        s = c[mtr]
        kmf = KaplanMeierFitter().fit(s.OS_Y, s.OS_E)
        tt = kmf.survival_function_.index.values.astype(float)
        ss = kmf.survival_function_.iloc[:, 0].values.astype(float)
        grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
        idx = np.searchsorted(tt, grid[:-1], side='right') - 1
        rm = float(np.sum(np.where(idx >= 0, ss[np.clip(idx, 0, None)], 1.0) * np.diff(grid)))
        rmst5[L] = rm
        mv = (leaf == L) & (c.ERA == 'valid').values
        vk = KaplanMeierFitter().fit(c.OS_Y[mv], c.OS_E[mv]) if mv.sum() > 0 else None
        med_tr = kmf.median_survival_time_
        leaf_rows.append({
            'tree': name, 'leaf': int(L), 'train_n': int(mtr.sum()), 'train_deaths': int(s.OS_E.sum()),
            'train_median_OS': round(float(med_tr), 2) if np.isfinite(med_tr) else 'not reached',
            'train_S5': round(float(kmf.survival_function_at_times(5).iloc[0]), 3),
            'train_RMST5': round(rm, 3),
            'valid_n': int(mv.sum()), 'valid_deaths': int(c.OS_E[mv].sum()) if mv.sum() else 0,
            'valid_median_OS': (round(float(vk.median_survival_time_), 2) if vk is not None and np.isfinite(vk.median_survival_time_) else ('not reached' if vk is not None else None)),
            'valid_S5': round(float(vk.survival_function_at_times(5).iloc[0]), 3) if vk is not None else None,
        })
    score = c[f'{name}_LEAF'].map(rmst5).astype(float).values  # higher = longer expected survival
    c[f'{name}_RMST5'] = score
    return tree, pd.DataFrame(leaf_rows), score


def cindex_split(score, subset_idx):
    s = c.loc[subset_idx]
    return round(float(concordance_index(s.OS_Y, score[c.index.get_indexer(subset_idx)], s.OS_E)), 4)


def group_logrank(df, col):
    g = df.groupby(col)
    labels = list(g.groups.keys())
    res = multivariate_logrank_test(df.OS_Y, df[col], df.OS_E)
    return float(res.p_value)


log('fitting TNM-only tree (training era only)')
tree_tnm, leaves_tnm, score_tnm = run_tree(TNM_FEAT, [], 'TNM')
log('fitting expanded tree (training era only)')
tree_exp, leaves_exp, score_exp = run_tree(EXP_FEAT, EXP_MISS, 'EXP')

tr_idx = c.index[c.ERA == 'train']
va_idx = c.index[c.ERA == 'valid']
trm = c.index.isin(tr_idx)
vam = c.index.isin(va_idx)
perf = []
for name, sc in [('TNM-only survival tree', score_tnm), ('Expanded survival tree', score_exp)]:
    perf.append({'model': name, 'train_C': round(float(concordance_index(c.OS_Y[trm], sc[trm], c.OS_E[trm])), 4),
                 'valid_C': round(float(concordance_index(c.OS_Y[vam], sc[vam], c.OS_E[vam])), 4),
                 'train_leaves': int(len(np.unique(c.loc[trm, 'TNM_LEAF' if 'TNM' in name else 'EXP_LEAF']))),
                 'min_leaf_n_train': int(leaves_tnm.train_n.min() if 'TNM' in name else leaves_exp.train_n.min())})

# ---------------------------------------------------------------- Cox benchmark on the same expanded feature set
# Cox uses reference-coded stage dummies (T1-2, N0, M0 dropped) to avoid collinearity with the baseline
REF_DUMMIES = ['T_GRP_T1-2', 'N_GRP_N0', 'M_GRP_M0']
COX_FEAT = [x for x in EXP_FEAT if x not in REF_DUMMIES]
prep_all = prep(tr_idx, c.index, COX_FEAT, EXP_MISS)
cox_train = prep_all.loc[tr_idx].copy()
cox_train['OS_Y'] = c.OS_Y[trm].values
cox_train['OS_E'] = c.OS_E[trm].values
cph = CoxPHFitter(penalizer=0.01).fit(cox_train, 'OS_Y', 'OS_E')
cox_score = cph.predict_partial_hazard(prep_all).values.ravel()
cox_score = -cox_score  # higher = longer survival
perf.append({'model': 'Cox (expanded features, benchmark)',
             'train_C': round(float(concordance_index(c.OS_Y[trm], cox_score[trm], c.OS_E[trm])), 4),
             'valid_C': round(float(concordance_index(c.OS_Y[vam], cox_score[vam], c.OS_E[vam])), 4),
             'train_leaves': None, 'min_leaf_n_train': None})
perf_df = pd.DataFrame(perf)
perf_df.to_csv(RES / 'M03_model_C_index.csv', index=False)
print(perf_df.to_string(index=False))

leaves_all = pd.concat([leaves_tnm, leaves_exp])
leaves_all.to_csv(RES / 'M04_terminal_nodes.csv', index=False)
print(leaves_all.to_string(index=False))

# ---------------------------------------------------------------- 4. why TNM-only gives no Favourable group
log('TNM combination survival (training era)')
combo = (c[trm].groupby(['T_GRP', 'N_GRP', 'M_GRP'])
         .apply(lambda s: pd.Series({
             'train_n': len(s), 'train_deaths': int(s.OS_E.sum()),
             'train_median_OS': round(float(KaplanMeierFitter().fit(s.OS_Y, s.OS_E).median_survival_time_), 2)
             if np.isfinite(KaplanMeierFitter().fit(s.OS_Y, s.OS_E).median_survival_time_) else 'not reached',
             'train_S5': round(float(KaplanMeierFitter().fit(s.OS_Y, s.OS_E).survival_function_at_times(5).iloc[0]), 3)}),
         include_groups=False).reset_index())
combo.to_csv(RES / 'M05_TNM_combinations_training.csv', index=False)
print(combo.to_string(index=False))

# ---------------------------------------------------------------- 5. three-group classification from training data only
def tertile_groups(score, name):
    """Cut-points are 1/3 and 2/3 quantiles of the training-patient risk score, then applied unchanged."""
    q1, q2 = np.quantile(score[trm], [1 / 3, 2 / 3])
    grp_all = np.where(score >= q2, 'Favourable', np.where(score >= q1, 'Intermediate', 'Adverse'))
    return grp_all, q1, q2


def group_table(gcol, label):
    rows = []
    for period, mask in [('training', trm), ('validation', vam)]:
        for g in ['Favourable', 'Intermediate', 'Adverse']:
            m = mask & (c[gcol].values == g)
            s = c[m]
            if len(s) == 0:
                rows.append({'classification': label, 'period': period, 'group': g, 'n': 0}); continue
            km = KaplanMeierFitter().fit(s.OS_Y, s.OS_E)
            med = km.median_survival_time_
            rows.append({'classification': label, 'period': period, 'group': g, 'n': len(s),
                         'share_pct': round(100 * len(s) / mask.sum(), 1), 'deaths': int(s.OS_E.sum()),
                         'median_OS': round(float(med), 2) if np.isfinite(med) else 'not reached',
                         'S5': round(float(km.survival_function_at_times(5).iloc[0]), 3)})
    return pd.DataFrame(rows)


class_tables = []
class_stats = []
for name, sc in [('TNM tree RMST tertiles', score_tnm), ('Expanded tree RMST tertiles', score_exp)]:
    gname = name.replace(' ', '_')
    grp_all, q1, q2 = tertile_groups(sc, name)
    c[gname] = grp_all
    t = group_table(gname, name)
    class_tables.append(t)
    tr_p = multivariate_logrank_test(c.OS_Y[trm], c[gname][trm], c.OS_E[trm]).p_value
    va_p = multivariate_logrank_test(c.OS_Y[vam], c[gname][vam], c.OS_E[vam]).p_value
    # pairwise validation log-rank (Bonferroni over three comparisons)
    pair = {}
    for a, b in [('Favourable', 'Intermediate'), ('Intermediate', 'Adverse'), ('Favourable', 'Adverse')]:
        ma = vam & (c[gname].values == a); mb = vam & (c[gname].values == b)
        if ma.sum() and mb.sum():
            p = logrank_test(c.OS_Y[ma], c.OS_Y[mb], c.OS_E[ma], c.OS_E[mb]).p_value
            pair[f'{a} vs {b}'] = round(min(1.0, p * 3), 6)
    # validation C-index of the ordinal group (Favourable=0 best)
    rank = c[gname].map({'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}).values.astype(float)
    class_stats.append({'classification': name, 'cut_q33': round(float(q1), 3), 'cut_q67': round(float(q2), 3),
                        'train_logrank_p': float(tr_p), 'valid_logrank_p': float(va_p),
                        'valid_C_group': round(float(concordance_index(c.OS_Y[vam], rank[vam], c.OS_E[vam])), 4),
                        'valid_pairwise_bonferroni_p': str(pair)})
class_df = pd.concat(class_tables, ignore_index=True)
class_df.to_csv(RES / 'M06_three_group_counts_and_survival.csv', index=False)
pd.DataFrame(class_stats).to_csv(RES / 'M07_three_group_separation.csv', index=False)
print(class_df.to_string(index=False))
print(pd.DataFrame(class_stats).to_string(index=False))

# ---------------------------------------------------------------- 6. calibration (validation, fixed rules)
cal_rows = []
p5 = cph.predict_survival_function(prep_all.loc[va_idx], times=[5.0]).T.values.ravel()
dec = pd.qcut(pd.Series(p5).rank(method='first'), 10, labels=False).values
for q in range(10):
    m = dec == q
    km = KaplanMeierFitter().fit(c.OS_Y[va_idx][m], c.OS_E[va_idx][m])
    cal_rows.append({'decile': q + 1, 'n': int(m.sum()), 'predicted_S5': round(float(p5[m].mean()), 3),
                     'observed_S5_KM': round(float(km.survival_function_at_times(5).iloc[0]), 3)})
cal_df = pd.DataFrame(cal_rows)
cal_df.to_csv(RES / 'M08_calibration_5y_cox_expanded_validation.csv', index=False)
print(cal_df.to_string(index=False))

# ---------------------------------------------------------------- 7. expanded tree, median fill plus not-recorded indicators
# NOTE: the tree never splits on the indicators, so this is the same tree as the imputed expanded tree.
# Median imputation sends unrecorded CEA into the high-CEA branches (see M11). Here each continuous
# variable keeps its own "not recorded" indicator and the filled value is the training median,
# so the tree can separate unrecorded values from measured ones instead of inheriting them.
log('expanded tree with explicit not-recorded indicators')
for col in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE', 'CEA_LOG']:
    c[col + '_NR'] = c[col].isna().astype(float)
    c[col + '_F'] = c[col].fillna(c.loc[trm, col].median())
NR_FEAT = TNM_COLS + ['AGE_F', 'MALE_F', 'SYNC_F', 'DFI_F', 'METS_F', 'SIZE_F', 'CEA_LOG_F',
                      'DFI_NR', 'METS_NR', 'SIZE_NR', 'CEA_LOG_NR']
Xnr = c[NR_FEAT].astype(float).values.astype(np.float32)
y_all = Surv.from_arrays(event=c.OS_E.astype(bool).values, time=c.OS_Y.values)
tree_nr = SurvivalTree(max_depth=3, min_samples_leaf=max(200, int(0.02 * trm.sum())), random_state=SEED)
tree_nr.fit(Xnr[trm], y_all[trm])
leaf_nr = tree_nr.apply(Xnr)
c['NR_LEAF'] = leaf_nr
rm_nr, rows_nr = {}, []
for L in np.unique(leaf_nr):
    m = (leaf_nr == L) & trm
    s_ = c[m]
    k = KaplanMeierFitter().fit(s_.OS_Y, s_.OS_E)
    tt = k.survival_function_.index.values.astype(float)
    ss = k.survival_function_.iloc[:, 0].values.astype(float)
    grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
    idx = np.searchsorted(tt, grid[:-1], side='right') - 1
    rm_nr[L] = float(np.sum(np.where(idx >= 0, ss[np.clip(idx, 0, None)], 1.0) * np.diff(grid)))
    med = k.median_survival_time_
    mv = (leaf_nr == L) & vam
    rows_nr.append({'leaf': int(L), 'train_n': int(m.sum()),
                    'train_median_OS': round(float(med), 2) if np.isfinite(med) else 'not reached',
                    'train_S5': round(float(k.survival_function_at_times(5).iloc[0]), 3),
                    'train_RMST5': round(rm_nr[L], 3), 'valid_n': int(mv.sum()),
                    'CEA_not_recorded_share_train': round(float(c.CEA_LOG_NR[m].mean()), 3)})
nr_leaves = pd.DataFrame(rows_nr)
nr_leaves.to_csv(RES / 'M10_expanded_NR_terminal_nodes.csv', index=False)
score_nr = np.array([rm_nr.get(L, np.nan) for L in leaf_nr])
c['NR_RMST5'] = score_nr
nr_perf = {'model': 'Expanded survival tree, explicit not-recorded categories',
           'train_C': round(float(concordance_index(c.OS_Y[trm], score_nr[trm], c.OS_E[trm])), 4),
           'valid_C': round(float(concordance_index(c.OS_Y[vam], score_nr[vam], c.OS_E[vam])), 4)}
perf_df = pd.concat([perf_df, pd.DataFrame([nr_perf])], ignore_index=True)
perf_df.to_csv(RES / 'M03_model_C_index.csv', index=False)
print(nr_leaves.to_string(index=False))
print(nr_perf)
c['NR_GROUP'] = tertile_groups(score_nr, 'NR')[0]
nr_tab = group_table('NR_GROUP', 'Expanded tree (not-recorded categories) RMST tertiles')
nr_tab.to_csv(RES / 'M06b_three_group_NR_tree.csv', index=False)
print(nr_tab.to_string(index=False))
q1n, q2n = np.quantile(score_nr[trm], [1 / 3, 2 / 3])
rank_nr = c['NR_GROUP'].map({'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}).values.astype(float)
sep_nr = {'classification': 'Expanded tree (not-recorded categories) RMST tertiles',
          'cut_q33': round(float(q1n), 3), 'cut_q67': round(float(q2n), 3),
          'train_logrank_p': float(multivariate_logrank_test(c.OS_Y[trm], c.NR_GROUP[trm], c.OS_E[trm]).p_value),
          'valid_logrank_p': float(multivariate_logrank_test(c.OS_Y[vam], c.NR_GROUP[vam], c.OS_E[vam]).p_value),
          'valid_C_group': round(float(concordance_index(c.OS_Y[vam], rank_nr[vam], c.OS_E[vam])), 4)}
pd.concat([pd.DataFrame(class_stats), pd.DataFrame([sep_nr])], ignore_index=True).to_csv(RES / 'M07_three_group_separation.csv', index=False)

# where unrecorded values fall in the imputed tree (M11) and outcome by recording status
rec = pd.DataFrame({'CEA_recorded': c.CEA_LOG.notna(), 'OS_Y': c.OS_Y, 'OS_E': c.OS_E, 'ERA': c.ERA})
rec_tab = rec.groupby('CEA_recorded').apply(lambda s: pd.Series({
    'n': len(s), 'deaths': int(s.OS_E.sum()),
    'median_OS': round(float(KaplanMeierFitter().fit(s.OS_Y, s.OS_E).median_survival_time_), 2),
    'S5': round(float(KaplanMeierFitter().fit(s.OS_Y, s.OS_E).survival_function_at_times(5).iloc[0]), 3)}),
    include_groups=False).reset_index()
rec_tab.to_csv(RES / 'M11_CEA_recording_and_outcome.csv', index=False)
print(rec_tab.to_string(index=False))

# ---------------------------------------------------------------- 8. expanded tree WITHOUT CEA (candidate primary model)
# CEA is unrecorded for about one third of patients and the result depends on how that is coded
# (median fill, zero fill and complete-case give different trees, see M10/M12). This variant keeps all
# other baseline variables, each with an explicit missing indicator, and drops CEA from the model.
log('expanded tree without CEA')
NOCEA_FEAT = TNM_COLS + ['AGE_F', 'MALE_F', 'SYNC_F', 'DFI_F', 'METS_F', 'SIZE_F',
                         'DFI_NR', 'METS_NR', 'SIZE_NR']
Xnc = c[NOCEA_FEAT].astype(float).values.astype(np.float32)
tree_nc = SurvivalTree(max_depth=3, min_samples_leaf=max(200, int(0.02 * trm.sum())), random_state=SEED)
tree_nc.fit(Xnc[trm], y_all[trm])
leaf_nc = tree_nc.apply(Xnc)
rm_nc, rows_nc = {}, []
for L in np.unique(leaf_nc):
    m = (leaf_nc == L) & trm
    s_ = c[m]
    k = KaplanMeierFitter().fit(s_.OS_Y, s_.OS_E)
    tt = k.survival_function_.index.values.astype(float)
    ss = k.survival_function_.iloc[:, 0].values.astype(float)
    grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
    idx = np.searchsorted(tt, grid[:-1], side='right') - 1
    rm_nc[L] = float(np.sum(np.where(idx >= 0, ss[np.clip(idx, 0, None)], 1.0) * np.diff(grid)))
    med = k.median_survival_time_
    mv = (leaf_nc == L) & vam
    rows_nc.append({'leaf': int(L), 'train_n': int(m.sum()),
                    'train_median_OS': round(float(med), 2) if np.isfinite(med) else 'not reached',
                    'train_S5': round(float(k.survival_function_at_times(5).iloc[0]), 3),
                    'train_RMST5': round(rm_nc[L], 3), 'valid_n': int(mv.sum()),
                    'valid_median_OS': (lambda vk: round(float(vk.median_survival_time_), 2) if np.isfinite(vk.median_survival_time_) else 'not reached')(KaplanMeierFitter().fit(c.OS_Y[mv], c.OS_E[mv])) if mv.sum() else None})
nc_leaves = pd.DataFrame(rows_nc)
nc_leaves.to_csv(RES / 'M12_expanded_noCEA_terminal_nodes.csv', index=False)
score_nc = np.array([rm_nc.get(L, np.nan) for L in leaf_nc])
c['NC_RMST5'] = score_nc
nc_perf = {'model': 'Expanded survival tree without CEA (candidate primary)',
           'train_C': round(float(concordance_index(c.OS_Y[trm], score_nc[trm], c.OS_E[trm])), 4),
           'valid_C': round(float(concordance_index(c.OS_Y[vam], score_nc[vam], c.OS_E[vam])), 4)}
perf_df = pd.concat([perf_df, pd.DataFrame([nc_perf])], ignore_index=True)
perf_df.to_csv(RES / 'M03_model_C_index.csv', index=False)
print(nc_leaves.to_string(index=False)); print(nc_perf)
c['NC_GROUP'] = tertile_groups(score_nc, 'NC')[0]
nc_tab = group_table('NC_GROUP', 'Expanded tree without CEA: RMST tertiles')
nc_tab.to_csv(RES / 'M06c_three_group_noCEA_tree.csv', index=False)
print(nc_tab.to_string(index=False))
q1c, q2c = np.quantile(score_nc[trm], [1 / 3, 2 / 3])
rank_nc = c['NC_GROUP'].map({'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}).values.astype(float)
sep_nc = {'classification': 'Expanded tree without CEA: RMST tertiles',
          'cut_q33': round(float(q1c), 3), 'cut_q67': round(float(q2c), 3),
          'train_logrank_p': float(multivariate_logrank_test(c.OS_Y[trm], c.NC_GROUP[trm], c.OS_E[trm]).p_value),
          'valid_logrank_p': float(multivariate_logrank_test(c.OS_Y[vam], c.NC_GROUP[vam], c.OS_E[vam]).p_value),
          'valid_C_group': round(float(concordance_index(c.OS_Y[vam], rank_nc[vam], c.OS_E[vam])), 4)}
pd.concat([pd.read_csv(RES / 'M07_three_group_separation.csv'), pd.DataFrame([sep_nc])], ignore_index=True).to_csv(RES / 'M07_three_group_separation.csv', index=False)
print(sep_nc)

# ---------------------------------------------------------------- figures
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
for gname, title in [('TNM_tree_RMST_tertiles', 'TNM-only tree: tertile groups (validation era)'),
                     ('Expanded_tree_RMST_tertiles', 'Expanded tree: tertile groups (validation era)')]:
    fig, ax = plt.subplots(figsize=(7, 5))
    for g, col in [('Favourable', '#1B7837'), ('Intermediate', '#E08214'), ('Adverse', '#B2182B')]:
        m = vam & (c[gname].values == g)
        if m.sum():
            KaplanMeierFitter().fit(c.OS_Y[m], c.OS_E[m], label=f'{g} (n={m.sum():,})').plot_survival_function(ax=ax, color=col, ci_show=True, show_censors=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 1.01); ax.grid(alpha=0.25); ax.set_title(title)
    ax.set_xlabel('Years from liver metastasis diagnosis'); ax.set_ylabel('Overall survival')
    fig.savefig(RES / 'figures' / f'{gname}_validation.png', dpi=200, bbox_inches='tight'); plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 5))
ax.plot([0, 1], [0, 1], ls='--', color='grey', lw=0.8)
ax.scatter(cal_df.predicted_S5, cal_df.observed_S5_KM, s=cal_df.n / cal_df.n.max() * 120 + 20)
ax.set_xlabel('Predicted 5-year OS (decile mean)'); ax.set_ylabel('Observed 5-year OS (KM)')
ax.set_title('Expanded Cox benchmark: 5-year calibration (validation)'); ax.grid(alpha=0.25)
fig.savefig(RES / 'figures' / 'M08_calibration_validation.png', dpi=200, bbox_inches='tight'); plt.close(fig)

# training-only tree rule text
def rules(t, names):
    tr = t.tree_
    out = []
    def walk(n, dpt):
        ind = '|   ' * dpt
        if tr.children_left[n] == -1:
            out.append(f'{ind}leaf {n}'); return
        f = names[tr.feature[n]]; th = tr.threshold[n]
        out.append(f'{ind}{f} <= {th:.2f}'); walk(tr.children_left[n], dpt + 1)
        out.append(f'{ind}{f} >  {th:.2f}'); walk(tr.children_right[n], dpt + 1)
    walk(0, 0)
    return '\n'.join(out)

(RES / 'M09_tree_rules_TNM.txt').write_text(rules(tree_tnm, TNM_FEAT) + '\n')
(RES / 'M09_tree_rules_expanded.txt').write_text(rules(tree_exp, EXP_FEAT + [m + '_MISSING' for m in EXP_MISS]) + '\n')
log(f'done; outputs in {RES}')
