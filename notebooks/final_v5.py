"""Final v4: surgery-origin OS cohort rebuilt to the 2026 reproducibility report's patient flow, then the
stratified Cox M1 model, phenotypes, validation, decision curves, RFS and benchmarks on identical subsets.

Inputs: combined_extract.parquet (v1 analysis columns, used for CINCLUSION, hepatectomy flag, status, staging)
        combined_extract_v2.parquet (operation dates, recurrence episodes, follow-up fields).
Both are in identical row order (checked below).

Rules (taken from the report's flow; no rule was chosen to match a model result):
  1 registry: all rows (29,565)
  2 inclusion: CINCLUSION == 'Yes'
  3 hepatectomy at first liver procedure: LE1HEPATECTYN_F1 == 'Yes'
  4 index operation date available: LE1OPERDT_F1 with year and month present (day may be missing)
  5 vital status and last-news date available: PATSTATC non-blank and LASTNDTC present
  6 valid chronology: last-news date >= index operation date
  7 positive follow-up or death: follow-up > 0 days or PATSTATC = Deceased
Partial operation dates (day missing) are set to the 1st of the month; a sensitivity analysis restricts to
complete dates. Training era: operation year <= 2009. Validation: operation year >= 2010.
"""
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter, NelsonAalenFitter
from lifelines.statistics import multivariate_logrank_test, proportional_hazard_test
from lifelines.utils import concordance_index, median_survival_times
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import cohen_kappa_score
from sksurv.metrics import brier_score, integrated_brier_score
from sksurv.tree import SurvivalTree
from sksurv.util import Surv

warnings.filterwarnings('ignore')
T0 = time.time()
SEED = 42
RNG = np.random.default_rng(SEED)
W = Path(os.environ['LIVERMET_WORK_DIR'])
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'final_v4'
RES.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
TB = np.arange(1.0, 7.5, 0.5)
PT = np.round(np.arange(0.10, 0.61, 0.05), 2)
MAXFU = 15.0
DAY_FILL = 15   # missing operation day set to mid-month (reproduces report steps 6-7; month-end gives identical counts)
CENSOR = pd.Timestamp('2020-07-04')


def log(msg):
    print(f'[{time.time()-T0:6.0f}s] {msg}', flush=True)


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s, lo=1, hi=80000):
    v = num(s)
    v = v.where((v >= lo) & (v <= hi))
    return EP + pd.to_timedelta(v, unit='D')


def ym(df, base):
    """Date from year/month/day components; a missing day is set to DAY_FILL (partial date)."""
    y = num(df[base + '_Y']); m = num(df[base + '_M']); d = num(df[base + '_D'])
    return pd.to_datetime(dict(year=y, month=m, day=d.fillna(DAY_FILL)), errors='coerce'), d.isna() & y.notna() & m.notna()


def save(df, name):
    df.to_csv(RES / f'{name}.csv', index=False)
    return df


# ================================================================== load and align the two extracts
v1 = pd.read_parquet(W / 'combined_extract.parquet')
v2 = pd.read_parquet(W / 'combined_extract_v2.parquet')
assert len(v1) == len(v2) == 29565
assert (v1.SOURCE_EXCEL_ROW.values == v2.SOURCE_EXCEL_ROW.values).all()
assert (v1.SOURCE_PART.values == v2.SOURCE_PART.values).all()
log('extracts aligned by source part and Excel row')

# ================================================================== patient flow (exact rules, report order)
INC = v1.CINCLUSION.eq('Yes')
HEP = v1.LE1HEPATECTYN_F1.eq('Yes')
OPD_ser = serial(v2.LE1OPERDT_F1)
OPD_ym, OPD_partial = ym(v2, 'LE1OPERDT_F1')
OPD = OPD_ser.fillna(OPD_ym)
OPD_hasym = OPD_ym.notna()
LAST_ser = serial(v2.LASTNDTC)
PST = v1.PATSTATC.isin(['Alive', 'Deceased', 'Lost to follow-up'])
PST_any = v1.PATSTATC.notna()
DEATH = v1.PATSTATC.eq('Deceased')
FU = (LAST_ser - OPD).dt.days
s1 = pd.Series(True, index=v1.index)
s2 = s1 & INC
s3 = s2 & HEP
s4 = s3 & OPD_hasym
s5 = s4 & PST_any & LAST_ser.notna()
s6 = s5 & (LAST_ser >= OPD)
s7 = s6 & ((FU > 0) | DEATH)
flow = pd.DataFrame([
    {'step': 1, 'rule': 'Original registry (all rows)', 'n': int(s1.sum()), 'report': 29565},
    {'step': 2, 'rule': 'Registry inclusion: CINCLUSION = Yes', 'n': int(s2.sum()), 'report': 28979},
    {'step': 3, 'rule': 'Hepatectomy at first liver procedure: LE1HEPATECTYN_F1 = Yes', 'n': int(s3.sum()), 'report': 26677},
    {'step': 4, 'rule': 'Index operation date available (LE1OPERDT_F1 year and month present)', 'n': int(s4.sum()), 'report': 26592},
    {'step': 5, 'rule': 'Vital status (PATSTATC) and last-news date (LASTNDTC) available', 'n': int(s5.sum()), 'report': 26271},
    {'step': 6, 'rule': 'Valid chronology: last-news date >= index operation date', 'n': int(s6.sum()), 'report': 26186},
    {'step': 7, 'rule': 'Positive follow-up or death', 'n': int(s7.sum()), 'report': 26094},
])
flow['difference_from_report'] = flow.n - flow.report
save(flow, 'F01_patient_flow_report_rules')
print(flow.to_string(index=False))
diagnostic = {
    'index operation: complete serial date at step 4': int((s4 & OPD_ser.notna()).sum()),
    'index operation: partial (day missing, set to 1st)': int((s4 & OPD_ser.isna()).sum()),
    'last-news after administrative censoring date 2020-07-04': int((s7 & (LAST_ser > CENSOR)).sum()),
    'operation after censoring date': int((s7 & (OPD > CENSOR)).sum()),
}
save(pd.Series(diagnostic).rename('n').rename_axis('check').reset_index(), 'F02_flow_diagnostics')
print(diagnostic)

# ================================================================== analysis cohort = step 7 (OS) and its TNM-complete subset
B = pd.DataFrame(index=v1.index)
B['T0'] = OPD
B['PARTIAL_OP_DAY'] = OPD_partial & OPD_ser.isna()
B['LAST'] = LAST_ser.fillna(pd.concat([serial(v2[f'LASTNDT_F{i}']) for i in range(1, 8)], axis=1).max(axis=1))
B['OS_E'] = np.where(DEATH, 1.0, 0.0)
B['OS_DAYS'] = (B.LAST - B.T0).dt.days
B['BIRTH'] = serial(v2.BIRTHDT)
B['DGK'] = serial(v2.DGKCOLDT)
B['DG'] = serial(v2.LE1DGMETADT)
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(s, m):
    return s.astype(object).map(lambda v: m.get(v, np.nan) if isinstance(v, str) else np.nan)


B['T_GRP'] = gmap(v1.STADET, TMAP)
B['N_GRP'] = gmap(v1.STADEN, NMAP)
B['M_GRP'] = gmap(v1.STADEM, MMAP)
B['TNM'] = B[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)
B['T3'] = (B.T_GRP == 'T3').astype(float).where(B.T_GRP.notna())
B['T4'] = (B.T_GRP == 'T4').astype(float).where(B.T_GRP.notna())
B['N1'] = (B.N_GRP == 'N1').astype(float).where(B.N_GRP.notna())
B['N2'] = (B.N_GRP == 'N2').astype(float).where(B.N_GRP.notna())
B['M1'] = (B.M_GRP == 'M1').astype(float).where(B.M_GRP.notna())
B['AGE'] = (B.T0 - B.BIRTH).dt.days / DAYS
B.loc[(B.AGE < 18) | (B.AGE > 100), 'AGE'] = np.nan
B['MALE'] = v1.GENDER.map({'Male': 1.0, 'Female': 0.0})
B['SYNC'] = v1.LE1METASYNCYN.map({'Yes': 1.0, 'No': 0.0})
B['METS'] = num(v1.LE1NBMETAHEPNUM)
B.loc[(B.METS < 1) | (B.METS > 50), 'METS'] = np.nan
B['SIZE'] = num(v1.LE1HEPMETASIZENUM)
B.loc[(B.SIZE <= 0) | (B.SIZE > 300), 'SIZE'] = np.nan
B['CEA'] = num(v1.LE1PREHEPCEA_F1)
B.loc[(B.CEA < 0) | (B.CEA > 40000), 'CEA'] = np.nan
# DFI: primary diagnosis to liver metastasis diagnosis, known before surgery; synchronous = 0
B['DFI'] = (B.DG - B.DGK).dt.days / 30.4375
B.loc[B.SYNC == 1, 'DFI'] = 0.0
B.loc[B.DFI < 0, 'DFI'] = np.nan
B['AGE10'] = B.AGE / 10
B['DFI12'] = B.DFI / 12
B['SIZE10'] = B.SIZE / 10
B['ERA'] = np.where(B.T0.dt.year <= 2009, 'train', 'valid')

os_mask = s7.values
tnm_mask = B.TNM.values
COH = B[os_mask].copy()
COH['DEFINITION_OS_STEP7'] = True
M = COH[COH.TNM].copy()        # modelling cohort: OS cohort with TNM complete
log(f'OS cohort (report rules, step 7) {len(COH):,}; TNM-complete modelling cohort {len(M):,}')
trm = (M.ERA == 'train').values
vam = (M.ERA == 'valid').values
for col in ['DFI', 'METS', 'SIZE']:
    M[col + '_NR'] = M[col].isna().astype(float)
for col in ['AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10']:
    M[col + '_F'] = M[col].fillna(M.loc[trm, col].median())
M['MALE_B'] = M.MALE_F.round().astype(int)
M['SYNC_B'] = M.SYNC_F.round().astype(int)
M['STRATUM'] = M.MALE_B * 2 + M.SYNC_B
CORE = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
M['OS_Y'] = np.minimum(M.OS_DAYS / DAYS, MAXFU)
M['OS_E'] = np.where(M.OS_DAYS / DAYS > MAXFU, 0.0, M.OS_E)
Ttr, Etr = M.OS_Y.values[trm], M.OS_E.values[trm]
Tva, Eva = M.OS_Y.values[vam], M.OS_E.values[vam]
log(f'modelling cohort: train {trm.sum():,} (deaths {int(Etr.sum()):,}), valid {vam.sum():,} (deaths {int(Eva.sum()):,})')

# ================================================================== M1 model and metrics
cph = CoxPHFitter().fit(M.loc[trm, CORE + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
be = cph.params_[CORE].values
hr = cph.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
hr.columns = ['term', 'HR', 'HR_lower95', 'HR_upper95', 'p']
save(hr.round(4), 'F03_M1_hazard_ratios')
ph = proportional_hazard_test(cph, M.loc[trm, CORE + ['OS_Y', 'OS_E', 'STRATUM']], time_transform='rank').summary.reset_index()
ph.columns = ['term'] + list(ph.columns[1:])
save(ph.round(4), 'F04_M1_PH_test_training')
X = M[CORE].astype(float).values
lp = X @ be
strat = M.STRATUM.values


def breslow(T, E, lpv, st):
    out = {}
    for s in np.unique(st):
        m = st == s
        t, e, l_ = T[m], E[m], lpv[m]
        o = np.argsort(t, kind='mergesort'); t, e, l_ = t[o], e[o], l_[o]
        risk = np.cumsum(np.exp(l_)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        out[s] = (ev, np.cumsum(dk / risk[idx]))
    return out


bres = breslow(Ttr, Etr, lp[trm], strat[trm])


def surv(times):
    S = np.ones((len(M), len(times)))
    for s in np.unique(strat):
        m = strat == s
        ev, H = bres[s]
        ii = np.searchsorted(ev, times, side='right') - 1
        Hs = np.where(ii >= 0, H[np.clip(ii, 0, None)], 0.0)
        S[m] = np.exp(-np.exp(lp[m, None]) * Hs[None, :])
    return S


TIMES = np.concatenate([[3.0, 5.0], TB])
S = surv(TIMES)
S3, S5 = S[:, 0], S[:, 1]
ytr = Surv.from_arrays(Etr.astype(bool), Ttr)
yva = Surv.from_arrays(Eva.astype(bool), Tva)
metrics = {'M1_train_C': round(float(concordance_index(Ttr, -lp[trm], Etr)), 4),
           'M1_valid_C': round(float(concordance_index(Tva, -lp[vam], Eva)), 4)}
_, bs = brier_score(ytr, yva, S[vam][:, 2:], TB)
for t in [1.0, 3.0, 5.0]:
    metrics[f'M1_Brier_{int(t)}y'] = round(float(bs[list(TB).index(t)]), 4)
metrics['M1_IBS_1_7y'] = round(float(integrated_brier_score(ytr, yva, S[vam][:, 2:], TB)), 4)
obs5 = float(KaplanMeierFitter().fit(Tva, Eva).survival_function_at_times(5).iloc[0])
metrics['M1_mean_pred_S5'] = round(float(S5[vam].mean()), 3)
metrics['M1_observed_S5'] = round(obs5, 3)
metrics['M1_OE_5y'] = round(obs5 / float(S5[vam].mean()), 3)
dec = pd.qcut(pd.Series(S5[vam]).rank(method='first'), 10, labels=False).values
cal = []
for q in range(10):
    m = dec == q
    k = KaplanMeierFitter().fit(Tva[m], Eva[m])
    cal.append({'decile': q + 1, 'n': int(m.sum()), 'predicted_S5': round(float(S5[vam][m].mean()), 3),
                'observed_S5_KM': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
save(pd.DataFrame(cal), 'F05_calibration_5y_deciles_validation')
slope = CoxPHFitter().fit(pd.DataFrame({'T': Tva, 'E': Eva, 'lp': np.log(-np.log(np.clip(S5[vam], 1e-6, 1 - 1e-6)))}), 'T', 'E').params_['lp']
metrics['M1_calib_slope_5y'] = round(float(slope), 3)

# identical-subset comparison of M1, survival tree and published scores
fong = (M.N_GRP.isin(['N1', 'N2']).astype(float) + (M.DFI < 12).astype(float) + (M.METS > 1).astype(float)
        + (M.SIZE > 50).astype(float) + (M.CEA > 200).astype(float))
fong = fong.where(M.N_GRP.notna() & M.DFI.notna() & M.METS.notna() & M.SIZE.notna() & M.CEA.notna())
nord = ((M.AGE >= 60).astype(float) + (M.T_GRP == 'T4').astype(float) + M.N_GRP.isin(['N1', 'N2']).astype(float)
        + (M.DFI < 12).astype(float))
nord = nord.where(M.AGE.notna() & M.T_GRP.notna() & M.N_GRP.notna() & M.DFI.notna())

# survival tree (no CEA; training only), leaves merged to three groups by training RMST5
TREE_F = CORE + ['MALE_F', 'SYNC_F']
Xt = M[TREE_F].astype(float).values.astype(np.float32)
tree = SurvivalTree(max_depth=3, min_samples_leaf=max(200, int(0.02 * trm.sum())), random_state=SEED)
yall = Surv.from_arrays(M.OS_E.astype(bool).values, M.OS_Y.values)
tree.fit(Xt[trm], yall[trm])
leaf = tree.apply(Xt)
lrows = []
for L in np.unique(leaf):
    m = (leaf == L) & trm
    k = KaplanMeierFitter().fit(M.OS_Y[m], M.OS_E[m])
    tt = k.survival_function_.index.values.astype(float); ss = k.survival_function_.iloc[:, 0].values.astype(float)
    grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
    ix = np.searchsorted(tt, grid[:-1], side='right') - 1
    rm = float(np.sum(np.where(ix >= 0, ss[np.clip(ix, 0, None)], 1.0) * np.diff(grid)))
    lrows.append((L, int(m.sum()), rm))
order = sorted(lrows, key=lambda r: -r[2])
tot = sum(r[1] for r in order); cum = 0.0; mp = {}
for L, n, rm in order:
    b = cum / tot; cum += n; mid = (b + cum / tot) / 2
    mp[L] = 'Favourable' if mid < 1 / 3 else ('Intermediate' if mid < 2 / 3 else 'Adverse')
rank_map = {'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}
tree_grp = np.array([mp[L] for L in leaf])
tree_rank = np.array([rank_map[g_] for g_ in tree_grp], float)
save(pd.DataFrame([{'leaf': int(L), 'train_n': n, 'train_RMST5': round(rm, 3), 'merged_group': mp[L]} for L, n, rm in lrows]),
     'F06_survival_tree_leaves')

rows = []
for lab, sc in [('All TNM-complete validation patients', None), ('Fong CRS subset (CEA recorded, all criteria)', fong),
                ('Nordlinger-type subset (age, T, N, DFI recorded)', nord)]:
    mv = vam & (np.ones(len(M), bool) if sc is None else sc.notna().values)
    mt = trm & (np.ones(len(M), bool) if sc is None else sc.notna().values)
    r = {'subset': lab, 'train_n': int(mt.sum()), 'valid_n': int(mv.sum()),
         'valid_deaths': int(M.OS_E.values[mv].sum())}
    r['M1_valid_C'] = round(float(concordance_index(M.OS_Y.values[mv], -lp[mv], M.OS_E.values[mv])), 4)
    r['tree_valid_C'] = round(float(concordance_index(M.OS_Y.values[mv], tree_rank[mv], M.OS_E.values[mv])), 4)
    if sc is not None:
        r['published_score_valid_C'] = round(float(concordance_index(M.OS_Y.values[mv], -sc.values[mv], M.OS_E.values[mv])), 4)
        r['published_score'] = 'Fong CRS' if 'Fong' in lab else 'Nordlinger-type (unweighted)'
    rows.append(r)
cmp_df = save(pd.DataFrame(rows), 'F07_identical_subset_comparison')
print(cmp_df.to_string(index=False))

# three groups: training tertiles of the M1 linear predictor (fixed rule)
q1, q2 = np.quantile(lp[trm], [1 / 3, 2 / 3])
grp = np.where(lp >= q2, 'Adverse', np.where(lp >= q1, 'Intermediate', 'Favourable'))
M['GROUP'] = grp
metrics['tertile_cut_LP_q33'] = round(float(q1), 4)
metrics['tertile_cut_LP_q67'] = round(float(q2), 4)
gt = []
for period, mask in [('training', trm), ('validation', vam)]:
    for lab in ['Favourable', 'Intermediate', 'Adverse']:
        m = mask & (grp == lab)
        k = KaplanMeierFitter().fit(M.OS_Y[m], M.OS_E[m])
        ci = median_survival_times(k.confidence_interval_).iloc[0]
        med = k.median_survival_time_
        gt.append({'period': period, 'group': lab, 'n': int(m.sum()), 'share_pct': round(100 * m.sum() / mask.sum(), 1),
                   'deaths': int(M.OS_E[m].sum()),
                   'median_OS': round(float(med), 2) if np.isfinite(med) else None,
                   'median_95CI_lo': round(float(ci.iloc[0]), 2),
                   'median_95CI_hi': round(float(ci.iloc[1]), 2) if np.isfinite(ci.iloc[1]) else None,
                   'S5': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
save(pd.DataFrame(gt), 'F08_three_group_table')
rank = np.array([rank_map[g_] for g_ in grp], float)
metrics['tertile_valid_C'] = round(float(concordance_index(Tva, rank[vam], Eva)), 4)
metrics['tertile_valid_logrank_p'] = float(multivariate_logrank_test(Tva, grp[vam], Eva).p_value)
metrics['tertile_train_logrank_p'] = float(multivariate_logrank_test(Ttr, grp[trm], Etr).p_value)
gcal = []
for lab in ['Favourable', 'Intermediate', 'Adverse']:
    kt = KaplanMeierFitter().fit(M.OS_Y[trm & (grp == lab)], M.OS_E[trm & (grp == lab)])
    kv = KaplanMeierFitter().fit(M.OS_Y[vam & (grp == lab)], M.OS_E[vam & (grp == lab)])
    gcal.append({'group': lab, 'predicted_S5_training': round(float(kt.survival_function_at_times(5).iloc[0]), 3),
                 'observed_S5_validation': round(float(kv.survival_function_at_times(5).iloc[0]), 3)})
save(pd.DataFrame(gcal), 'F09_group_calibration_5y')
kap = []
tr_idx = np.where(trm)[0]
for _ in range(100):
    pick = RNG.choice(tr_idx, len(tr_idx), replace=True)
    try:
        cb = CoxPHFitter().fit(M.iloc[pick][CORE + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
    except Exception:  # noqa: BLE001
        continue
    lpb = X @ cb.params_[CORE].values
    a1, a2 = np.quantile(lpb[trm], [1 / 3, 2 / 3])
    gb = np.where(lpb >= a2, 'Adverse', np.where(lpb >= a1, 'Intermediate', 'Favourable'))
    kap.append(cohen_kappa_score(grp[vam], gb[vam]))
metrics['bootstrap_kappa_median'] = round(float(np.median(kap)), 3)
metrics['bootstrap_kappa_2.5pct'] = round(float(np.percentile(kap, 2.5)), 3)
metrics['bootstrap_resamples'] = len(kap)
pair = []
for a, b_ in [('Favourable', 'Intermediate'), ('Intermediate', 'Adverse'), ('Favourable', 'Adverse')]:
    from lifelines.statistics import logrank_test
    ma = vam & (grp == a); mb = vam & (grp == b_)
    p = logrank_test(M.OS_Y[ma], M.OS_Y[mb], M.OS_E[ma], M.OS_E[mb]).p_value
    pair.append({'comparison': f'{a} vs {b_}', 'valid_logrank_p_bonferroni': min(1.0, 3 * p)})
save(pd.DataFrame(pair), 'F10_pairwise_validation')

# decision curves (IPCW; censoring distribution from training)
ct = KaplanMeierFitter().fit(Ttr, 1 - Etr).survival_function_
cts, csv_ = ct.index.values.astype(float), ct.iloc[:, 0].values.astype(float)


def G(x):
    ii = np.searchsorted(cts, x, side='right') - 1
    return np.where(ii >= 0, csv_[np.clip(ii, 0, None)], 1.0)


def nb_curve(T, E, h, decide):
    Y = (T <= h) & (E == 1)
    known = Y | (T > h)
    w = np.zeros(len(T))
    w[known] = 1.0 / np.clip(G(np.minimum(T[known], h)), 1e-6, None)
    Nn = len(T)
    out = []
    for p in PT:
        d = decide(p).astype(float)
        odds = p / (1 - p)
        out.append(np.sum(w * (Y.astype(float) * d - (~Y).astype(float) * known.astype(float) * odds * d)) / Nn)
    return np.array(out)


dcrows = []
for h, j in [(3.0, 0), (5.0, 1)]:
    rv = 1 - S[vam, j]
    nb_m = nb_curve(Tva, Eva, h, lambda p: rv >= p)
    nb_a = nb_curve(Tva, Eva, h, lambda p: np.ones(len(Tva), bool))
    gv = grp[vam]
    nb_g = nb_curve(Tva, Eva, h, lambda p: gv == 'Adverse')
    for i, p in enumerate(PT):
        dcrows.append({'horizon_years': h, 'threshold': p, 'NB_M1_continuous': round(float(nb_m[i]), 4),
                       'NB_treat_adverse_group': round(float(nb_g[i]), 4), 'NB_treat_all': round(float(nb_a[i]), 4),
                       'NB_treat_none': 0.0})
save(pd.DataFrame(dcrows), 'F11_decision_curves_IPCW')

# ================================================================== RFS (post-operative), undated recurrences handled separately
REC_FIELDS = ([f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
              + [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)] + [f'RECDT_F{i}' for i in range(1, 8)])
REC_ALL = pd.concat([serial(v2[c]) for c in REC_FIELDS], axis=1)     # dated recurrence fields (serial dates)
REC_FIRST = REC_ALL.min(axis=1)
REC_CNT_POS = (pd.concat([num(v2[f'LRNBREC_M{i}']) for i in range(1, 6)] + [num(v2[f'EXHNBREC2_M{i}']) for i in range(1, 9)],
                         axis=1).fillna(0) > 0).any(axis=1)
AWD1 = v1.PATSTATC.notna() & v2.PATSTAT_F1.eq('Alive with disease')
rf = pd.DataFrame(index=M.index)
rf['rec'] = REC_FIRST.loc[M.index]
rf['T0'] = M.T0
rf['LAST'] = M.LAST
rf['DEATH'] = M.OS_E.astype(bool)
rf['cnt'] = REC_CNT_POS.loc[M.index]
rf['awd'] = AWD1.loc[M.index]
rec_before = rf.rec.notna() & (rf.rec < rf.T0)
rec_after = rf.rec.notna() & (rf.rec >= rf.T0) & (rf.rec <= rf.LAST)
undated = (~rec_after) & (~rec_before) & rf.cnt             # recurrence recorded (count > 0) without a usable date
elig = ~rec_before.values
dated_days = (rf.rec - rf.T0).dt.days.astype(float)
last_days = (rf.LAST - rf.T0).dt.days.astype(float)
rT_base = np.where(rec_after, dated_days, last_days) / DAYS
mid_days = last_days / 2.0
rfs_specs = [
    ('PRIMARY: dated recurrence and death are events; undated recurrences censored at last contact (not assigned)',
     np.where(rec_after | rf.DEATH, 1.0, 0.0), np.where(rec_after, dated_days, last_days) / DAYS, elig),
    ('Undated recurrences assigned as events at last contact (conservative early)',
     np.where(rec_after | rf.DEATH | undated, 1.0, 0.0), np.where(rec_after, dated_days, last_days) / DAYS, elig),
    ('Undated recurrences assigned as events at mid-interval (operation to last contact)',
     np.where(rec_after | rf.DEATH | undated, 1.0, 0.0),
     np.where(rec_after, dated_days, np.where(undated, mid_days, last_days)) / DAYS, elig),
    ('Patients with undated recurrences excluded',
     np.where(rec_after | rf.DEATH, 1.0, 0.0), np.where(rec_after, dated_days, last_days) / DAYS, elig & ~undated.values),
    ('Earlier rule (reference only): all alive-with-disease events',
     np.where(rec_after | rf.DEATH | rf.awd, 1.0, 0.0), np.where(rec_after, dated_days, last_days) / DAYS, elig),
]
rfs_rows = []
for lab, E_, T_, mask in rfs_specs:
    Tt = np.clip(np.minimum(T_, MAXFU), 1 / DAYS, None)
    k = KaplanMeierFitter().fit(Tt[mask], E_[mask])
    ci = median_survival_times(k.confidence_interval_).iloc[0]
    rfs_rows.append({'RFS_analysis': lab, 'n': int(mask.sum()), 'events': int(E_[mask].sum()),
                     'dated_recurrence_after_operation': int(rec_after.values[mask].sum()),
                     'undated_recurrence_count_in_analysis': int(undated.values[mask].sum()),
                     'median_RFS': round(float(k.median_survival_time_), 2) if np.isfinite(k.median_survival_time_) else None,
                     'median_95CI_lo': round(float(ci.iloc[0]), 2),
                     'median_95CI_hi': round(float(ci.iloc[1]), 2) if np.isfinite(ci.iloc[1]) else None,
                     'RFS_3y': round(float(k.survival_function_at_times(3).iloc[0]), 3),
                     'RFS_5y': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
rfs_rows.append({'RFS_analysis': 'excluded: recurrence dated before operation', 'n': int(rec_before.sum())})
save(pd.DataFrame(rfs_rows), 'F12_RFS_sensitivity')
print(pd.DataFrame(rfs_rows).to_string(index=False))
src = pd.Series(np.select([rec_after.values, rf.DEATH.values, undated.values, rf.awd.values],
                          ['dated recurrence after operation', 'death', 'undated recurrence (count > 0)',
                           'alive with disease, no date, no count'], 'censored at last contact')).value_counts()
save(src.rename_axis('source').reset_index(name='n'), 'F13_RFS_event_sources')

# ================================================================== sensitivity: complete operation dates only
cc = M[~M.T0.isna() & ~M.PARTIAL_OP_DAY]
cc_tr = (cc.ERA == 'train').values; cc_va = (cc.ERA == 'valid').values
cph_cc = CoxPHFitter().fit(cc.loc[cc_tr, CORE + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
sens = {'complete operation dates only: n train / valid': f'{int(cc_tr.sum())} / {int(cc_va.sum())}',
        'complete-date M1 valid C': round(float(concordance_index(cc.OS_Y.values[cc_va], -(cc[CORE].astype(float).values @ cph_cc.params_[CORE].values)[cc_va], cc.OS_E.values[cc_va])), 4)}
metrics.update({'sensitivity_' + k.replace(' ', '_').replace(':', ''): v for k, v in sens.items()})

# ================================================================== phenotype methodology under stratification
STRAT_LAB = {0: 'female, asynchronous', 1: 'female, synchronous', 2: 'male, asynchronous', 3: 'male, synchronous'}
q33s, q67s = np.quantile(S5[trm], [1 / 3, 2 / 3])
grp_abs = np.where(S5 >= q67s, 'Favourable', np.where(S5 >= q33s, 'Intermediate', 'Adverse'))
M['GROUP_ABS5'] = grp_abs
strat_rows = []
for sv in sorted(STRAT_LAB):
    for period, mask in [('training', trm), ('validation', vam)]:
        ms = mask & (strat == sv)
        row = {'stratum': STRAT_LAB[sv], 'period': period, 'n': int(ms.sum()), 'deaths': int(M.OS_E.values[ms].sum())}
        for lab in ['Favourable', 'Intermediate', 'Adverse']:
            row[f'LP_tertile_{lab}_n'] = int((ms & (grp == lab)).sum())
            row[f'abs5_{lab}_n'] = int((ms & (grp_abs == lab)).sum())
        row['mean_predicted_S5'] = round(float(S5[ms].mean()), 3)
        row['observed_S5_KM'] = round(float(KaplanMeierFitter().fit(M.OS_Y.values[ms], M.OS_E.values[ms]).survival_function_at_times(5).iloc[0]), 3) if ms.sum() > 20 else None
        strat_rows.append(row)
save(pd.DataFrame(strat_rows), 'F14_stratum_composition_and_absolute_risk')
print(pd.DataFrame(strat_rows).to_string(index=False))

def group_block(gvec, label):
    out = []
    for lab in ['Favourable', 'Intermediate', 'Adverse']:
        mt = trm & (gvec == lab); mv = vam & (gvec == lab)
        kv = KaplanMeierFitter().fit(M.OS_Y.values[mv], M.OS_E.values[mv])
        kt = KaplanMeierFitter().fit(M.OS_Y.values[mt], M.OS_E.values[mt])
        med = kv.median_survival_time_
        out.append({'grouping': label, 'group': lab, 'train_n': int(mt.sum()), 'valid_n': int(mv.sum()),
                    'valid_deaths': int(M.OS_E.values[mv].sum()),
                    'valid_median_OS': round(float(med), 2) if np.isfinite(med) else None,
                    'valid_S5_KM': round(float(kv.survival_function_at_times(5).iloc[0]), 3),
                    'train_mean_predicted_S5': round(float(S5[mt].mean()), 3),
                    'train_observed_S5_KM': round(float(kt.survival_function_at_times(5).iloc[0]), 3),
                    'valid_mean_predicted_S5': round(float(S5[mv].mean()), 3)})
    return out
pheno_cmp = group_block(grp, 'pooled linear-predictor tertiles') + group_block(grp_abs, 'fixed-horizon 5-year predicted survival tertiles')
save(pd.DataFrame(pheno_cmp), 'F15_phenotype_LP_vs_absolute_risk')
print(pd.DataFrame(pheno_cmp).to_string(index=False))
sep = []
for label, gvec in [('pooled linear-predictor tertiles', grp), ('fixed-horizon 5-year risk tertiles', grp_abs)]:
    rk = np.array([rank_map[x] for x in gvec], float)
    row = {'grouping': label,
           'valid_C_group_ordinal': round(float(concordance_index(M.OS_Y.values[vam], rk[vam], M.OS_E.values[vam])), 4),
           'valid_logrank_p': float(multivariate_logrank_test(M.OS_Y.values[vam], gvec[vam], M.OS_E.values[vam]).p_value),
           'train_logrank_p': float(multivariate_logrank_test(M.OS_Y.values[trm], gvec[trm], M.OS_E.values[trm]).p_value)}
    for sv in sorted(STRAT_LAB):
        ms = vam & (strat == sv)
        row[f'valid_logrank_p_{STRAT_LAB[sv].replace(", ", "_").replace(" ", "_")}'] = float(multivariate_logrank_test(M.OS_Y.values[ms], gvec[ms], M.OS_E.values[ms]).p_value)
    sep.append(row)
save(pd.DataFrame(sep), 'F16_phenotype_separation_within_strata')
print(pd.DataFrame(sep).to_string(index=False))
# bootstrap kappa for the two groupings (refit M1 on each resample; S5 recomputed with that resample's baseline)
kap_lp, kap_abs = [], []
for _ in range(100):
    pick = RNG.choice(tr_idx, len(tr_idx), replace=True)
    try:
        cb = CoxPHFitter().fit(M.iloc[pick][CORE + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
    except Exception:  # noqa: BLE001
        continue
    lpb = X @ cb.params_[CORE].values
    a1, a2 = np.quantile(lpb[trm], [1 / 3, 2 / 3])
    gb = np.where(lpb >= a2, 'Adverse', np.where(lpb >= a1, 'Intermediate', 'Favourable'))
    kap_lp.append(cohen_kappa_score(grp[vam], gb[vam]))
    bb = breslow(M.OS_Y.values[pick], M.OS_E.values[pick], lpb[pick], strat[pick])
    ev_b = {sv: bb[sv] for sv in bb}
    S5b = np.ones(len(M))
    for sv in np.unique(strat):
        mm = strat == sv
        ev, H = ev_b[sv]
        ii = np.searchsorted(ev, 5.0, side='right') - 1
        Hs = H[ii] if ii >= 0 else 0.0
        S5b[mm] = np.exp(-np.exp(lpb[mm]) * Hs)
    q1b, q2b = np.quantile(S5b[trm], [1 / 3, 2 / 3])
    ga = np.where(S5b >= q2b, 'Favourable', np.where(S5b >= q1b, 'Intermediate', 'Adverse'))
    kap_abs.append(cohen_kappa_score(grp_abs[vam], ga[vam]))
stab_rows = [{'grouping': 'pooled LP tertiles', 'kappa_median': round(float(np.median(kap_lp)), 3),
              'kappa_2.5pct': round(float(np.percentile(kap_lp, 2.5)), 3), 'resamples': len(kap_lp)},
             {'grouping': 'absolute 5-year tertiles', 'kappa_median': round(float(np.median(kap_abs)), 3),
              'kappa_2.5pct': round(float(np.percentile(kap_abs, 2.5)), 3), 'resamples': len(kap_abs)}]
save(pd.DataFrame(stab_rows), 'F17_phenotype_bootstrap_stability')
print(pd.DataFrame(stab_rows).to_string(index=False))
kappa_main = round(float(cohen_kappa_score(grp[vam], grp_abs[vam])), 3)
metrics['kappa_pooledLP_vs_absolute_validation'] = kappa_main
metrics['absolute5_cut_S5_q33'] = round(float(q33s), 4)
metrics['absolute5_cut_S5_q67'] = round(float(q67s), 4)

# ================================================================== CEA sensitivity on the corrected cohort
M['CEA_LOG'] = np.log1p(M.CEA)
cc = M[M.CEA.notna()].copy()
cc_tr = (cc.ERA == 'train').values; cc_va = (cc.ERA == 'valid').values
cea_rows = []
cph_base_cc = CoxPHFitter().fit(cc.loc[cc_tr, CORE + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
cph_cea_cc = CoxPHFitter().fit(cc.loc[cc_tr, CORE + ['CEA_LOG', 'STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
lp_b = cc[CORE].astype(float).values @ cph_base_cc.params_[CORE].values
lp_c = cc[CORE + ['CEA_LOG']].astype(float).values @ cph_cea_cc.params_[CORE + ['CEA_LOG']].values
cea_rows.append({'analysis': 'Complete case (CEA recorded)', 'train_n': int(cc_tr.sum()), 'valid_n': int(cc_va.sum()),
                 'valid_deaths': int(cc.OS_E.values[cc_va].sum()),
                 'CEA_HR_per_log_unit': round(float(np.exp(cph_cea_cc.params_['CEA_LOG'])), 3),
                 'CEA_HR_95CI': f"{cph_cea_cc.summary.loc['CEA_LOG', 'exp(coef) lower 95%']:.3f}-{cph_cea_cc.summary.loc['CEA_LOG', 'exp(coef) upper 95%']:.3f}",
                 'valid_C_M1_without_CEA': round(float(concordance_index(cc.OS_Y.values[cc_va], -lp_b[cc_va], cc.OS_E.values[cc_va])), 4),
                 'valid_C_M1_with_CEA': round(float(concordance_index(cc.OS_Y.values[cc_va], -lp_c[cc_va], cc.OS_E.values[cc_va])), 4)})
# multiple imputation: development imputation uses the outcome (Nelson-Aalen and event); validation uses predictors only
pred_cols = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10']
na_fit = NelsonAalenFitter().fit(M.OS_Y.values[trm], M.OS_E.values[trm])
H_na = np.interp(M.OS_Y.values, na_fit.cumulative_hazard_.index.values, na_fit.cumulative_hazard_.iloc[:, 0].values)
Xp = M[pred_cols].astype(float).values
dev = np.column_stack([Xp, M.CEA_LOG.values, H_na, M.OS_E.values])
MI_COLS = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'MALE_F', 'SYNC_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
coefs, varis, lp_v, hrs = [], [], [], []
for draw in range(10):
    imp = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw).fit(dev[trm])
    cea_dev = imp.transform(dev)[:, len(pred_cols)]
    dd = M[MI_COLS + ['STRATUM', 'OS_Y', 'OS_E']].copy()
    dd['CEA_IMP'] = cea_dev
    cm = CoxPHFitter().fit(dd.loc[trm, MI_COLS + ['CEA_IMP', 'STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
    coefs.append(cm.params_['CEA_IMP']); varis.append(cm.standard_errors_['CEA_IMP'] ** 2); hrs.append(float(np.exp(cm.params_['CEA_IMP'])))
    impv = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw).fit(np.column_stack([Xp, M.CEA_LOG.values])[trm])
    cea_val = impv.transform(np.column_stack([Xp, M.CEA_LOG.values]))[:, len(pred_cols)]
    dv = M[MI_COLS].copy(); dv['CEA_IMP'] = cea_val
    lp_v.append(cm.predict_log_partial_hazard(dv[MI_COLS + ['CEA_IMP']]).values.ravel())
bar = float(np.mean(coefs)); W_ = float(np.mean(varis)); B_ = float(np.var(coefs, ddof=1)); Tv = W_ + (1 + 1 / 10) * B_
se = np.sqrt(Tv)
lp_avg = np.mean(lp_v, axis=0)
cea_rows.append({'analysis': 'Multiple imputation, 10 draws (development: outcome-compatible; validation: predictors only)',
                 'train_n': int(trm.sum()), 'valid_n': int(vam.sum()), 'valid_deaths': int(Eva.sum()),
                 'CEA_HR_per_log_unit': round(float(np.exp(bar)), 3),
                 'CEA_HR_95CI': f'{np.exp(bar-1.96*se):.3f}-{np.exp(bar+1.96*se):.3f}',
                 'valid_C_M1_without_CEA': metrics['M1_valid_C'],
                 'valid_C_M1_with_CEA': round(float(concordance_index(Tva, -lp_avg[vam], Eva)), 4),
                 'draw_HR_range': f'{min(hrs):.3f}-{max(hrs):.3f}'})
save(pd.DataFrame(cea_rows), 'F18_CEA_sensitivity_corrected_cohort')
print(pd.DataFrame(cea_rows).to_string(index=False))

# ================================================================== predictor availability at prediction time
def cov(x):
    return round(100 * float(x.notna().mean()), 1)
dg_before = (M.DG <= M.T0)
avail = pd.DataFrame([
    {'predictor': 'Age at operation', 'source': 'BIRTHDT (date) and LE1OPERDT_F1 (date)', 'basis': 'confirmed date fields',
     'timing': 'before time zero', 'coverage_pct': cov(M.AGE), 'status': 'confirmed'},
    {'predictor': 'Sex', 'source': 'GENDER', 'basis': 'no date field', 'timing': 'baseline characteristic',
     'coverage_pct': cov(M.MALE), 'status': 'assumed static'},
    {'predictor': 'T, N, M stage', 'source': 'STADET, STADEN, STADEM', 'basis': 'no date field',
     'timing': 'at primary staging (before liver metastasis diagnosis)', 'coverage_pct': 100.0, 'status': 'assumed (stage date not in export)'},
    {'predictor': 'Diagnosis-to-metastasis interval', 'source': 'DGKCOLDT and LE1DGMETADT (dates)', 'basis': 'confirmed date fields',
     'timing': f'before time zero for {100*float(dg_before[M.DFI.notna()].mean()):.1f}% with both dates', 'coverage_pct': cov(M.DFI), 'status': 'confirmed (dates); DG after operation excluded by NR rule'},
    {'predictor': 'Synchronous presentation', 'source': 'LE1METASYNCYN', 'basis': 'no date field',
     'timing': 'at liver metastasis diagnosis', 'coverage_pct': cov(M.SYNC), 'status': 'assumed'},
    {'predictor': 'Number of liver metastases (episode 1)', 'source': 'LE1NBMETAHEPNUM', 'basis': 'no measurement date',
     'timing': 'episode 1 (assumed pre-operative)', 'coverage_pct': cov(M.METS), 'status': 'assumed'},
    {'predictor': 'Largest metastasis size (episode 1)', 'source': 'LE1HEPMETASIZENUM', 'basis': 'no measurement date',
     'timing': 'episode 1 (assumed pre-operative)', 'coverage_pct': cov(M.SIZE), 'status': 'assumed'},
    {'predictor': 'CEA (sensitivity only)', 'source': 'LE1PREHEPCEA_F1', 'basis': 'field name: pre-hepatectomy, no date',
     'timing': 'pre-hepatectomy (assumed)', 'coverage_pct': cov(M.CEA), 'status': 'assumed; not in primary model'},
])
save(avail, 'F19_predictor_availability')
print(avail.to_string(index=False))

# ================================================================== calibration and benchmarks on identical validation subsets
subs = [('All TNM-complete validation', vam), ('Fong CRS subset (CEA recorded)', vam & fong.notna().values),
        ('Nordlinger-type subset', vam & nord.notna().values)]
cal_rows = []
for lab, mv in subs:
    row = {'subset': lab, 'valid_n': int(mv.sum()), 'valid_deaths': int(M.OS_E.values[mv].sum())}
    row['M1_C'] = round(float(concordance_index(M.OS_Y.values[mv], -lp[mv], M.OS_E.values[mv])), 4)
    row['tree_C'] = round(float(concordance_index(M.OS_Y.values[mv], tree_rank[mv], M.OS_E.values[mv])), 4)
    if 'Fong' in lab:
        row['Fong_CRS_C'] = round(float(concordance_index(M.OS_Y.values[mv], -fong.values[mv], M.OS_E.values[mv])), 4)
    if 'Nordlinger' in lab:
        row['Nordlinger_C'] = round(float(concordance_index(M.OS_Y.values[mv], -nord.values[mv], M.OS_E.values[mv])), 4)
    o5 = float(KaplanMeierFitter().fit(M.OS_Y.values[mv], M.OS_E.values[mv]).survival_function_at_times(5).iloc[0])
    row['M1_mean_predicted_S5'] = round(float(S5[mv].mean()), 3)
    row['observed_S5_KM'] = round(o5, 3)
    row['M1_OE_5y'] = round(o5 / float(S5[mv].mean()), 3)
    row['M1_calib_slope_5y'] = round(float(CoxPHFitter().fit(pd.DataFrame({'T': M.OS_Y.values[mv], 'E': M.OS_E.values[mv],
                                                                         'lp': np.log(-np.log(np.clip(S5[mv], 1e-6, 1 - 1e-6)))}), 'T', 'E').params_['lp']), 3)
    cal_rows.append(row)
save(pd.DataFrame(cal_rows), 'F20_calibration_and_benchmarks_identical_subsets')
print(pd.DataFrame(cal_rows).to_string(index=False))

# ================================================================== save all headline numbers
save(pd.Series(metrics).rename('value').rename_axis('quantity').reset_index(), 'F00_headline_metrics')
print(pd.Series(metrics).to_string())
log(f'done -> {RES}')
