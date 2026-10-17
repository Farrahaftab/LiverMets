"""Final analysis v3, both time origins, from combined_extract_v2.parquet.

Model: stratified Cox (M1: stratified by sex and synchronous presentation) with no-CEA prespecified covariates,
all measured at or before time zero. Three prognostic groups are tertiles of the training linear predictor.
Training era: time zero <= 2009. Temporal validation: time zero >= 2010. Nothing is fitted or chosen on
validation outcomes. Censoring weights for decision curves are estimated on training data.
"""
import itertools  # noqa: F401 (kept for reproducibility of reconciliation searches)
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test, proportional_hazard_test
from lifelines.utils import concordance_index, median_survival_times
from sklearn.metrics import cohen_kappa_score
from sksurv.metrics import brier_score, cumulative_dynamic_auc, integrated_brier_score
from sksurv.tree import SurvivalTree
from sksurv.util import Surv

warnings.filterwarnings('ignore')
T0 = time.time()
SEED = 42
RNG = np.random.default_rng(SEED)
W = Path(os.environ['LIVERMET_WORK_DIR'])
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'final_v3'
RES.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
TB = np.arange(1.0, 7.5, 0.5)
HOR = [3.0, 5.0]
PT = np.round(np.arange(0.10, 0.61, 0.05), 2)
MAXFU = 15.0


def log(msg):
    print(f'[{time.time()-T0:6.0f}s] {msg}', flush=True)


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def xl(s, lo=1, hi=80000):
    v = num(s)
    v = v.where((v >= lo) & (v <= hi))
    return EP + pd.to_timedelta(v, unit='D')


def save(df, name):
    df.to_csv(RES / f'{name}.csv', index=False)
    return df


# ================================================================== base variables (time-independent, from raw)
raw = pd.read_parquet(W / 'combined_extract_v2.parquet')
log(f'loaded {len(raw):,} patients')
B = pd.DataFrame(index=raw.index)
B['PART'] = raw.SOURCE_PART
B['ROW'] = raw.SOURCE_EXCEL_ROW
B['BIRTH'] = xl(raw.BIRTHDT)
B['DGK'] = xl(raw.DGKCOLDT)
B['DG'] = xl(raw.LE1DGMETADT)                 # liver metastasis diagnosis
B['OP'] = xl(raw.LE1OPERDT_F1)                # index operation (surgery origin)
B['LAST_C'] = xl(raw.LASTNDTC)
fup = pd.concat([xl(raw[f'LASTNDT_F{i}']) for i in range(1, 8)], axis=1)
B['LAST'] = B.LAST_C.fillna(fup.max(axis=1))
B['STATUS'] = raw.PATSTATC.where(raw.PATSTATC.isin(['Alive', 'Deceased', 'Lost to follow-up']))
B['DEATH'] = B.STATUS.eq('Deceased').astype(float).where(B.STATUS.notna())
B['AWD1'] = raw.PATSTAT_F1.eq('Alive with disease')
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(s, m):
    return s.astype(object).map(lambda v: m.get(v, np.nan) if isinstance(v, str) else np.nan)


B['T_GRP'] = gmap(raw.STADET, TMAP)
B['N_GRP'] = gmap(raw.STADEN, NMAP)
B['M_GRP'] = gmap(raw.STADEM, MMAP)
B['TNM'] = B[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)
B['MALE'] = raw.GENDER.map({'Male': 1.0, 'Female': 0.0})
B['SYNC'] = raw.LE1METASYNCYN.map({'Yes': 1.0, 'No': 0.0})
B['METS'] = num(raw.LE1NBMETAHEPNUM)
B['METS'] = B.METS.where((B.METS >= 1) & (B.METS <= 50))
B['SIZE'] = num(raw.LE1HEPMETASIZENUM)
B['SIZE'] = B.SIZE.where((B.SIZE > 0) & (B.SIZE <= 300))
B['SURG'] = raw.LE1HEPATECTYN_F1.map({'Yes': 1.0, 'No': 0.0})
B['CEA'] = num(raw.LE1PREHEPCEA_F1)

# recurrence evidence (episode dates after time zero are used below)
LIVER_DATES = [f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
EXH_DATES = [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)]
RECDT = [f'RECDT_F{i}' for i in range(1, 8)]
ALLREC = pd.concat([xl(raw[c]) for c in LIVER_DATES + EXH_DATES + RECDT], axis=1)
B['REC_FIRST'] = ALLREC.min(axis=1)
REC_CNT = pd.concat([num(raw[f'LRNBREC_M{i}']) for i in range(1, 6)] + [num(raw[f'EXHNBREC2_M{i}']) for i in range(1, 9)], axis=1)
B['REC_COUNT_POS'] = (REC_CNT.fillna(0) > 0).any(axis=1)
B['REC_DATE_ANY'] = B.REC_FIRST.notna()
log('base variables built')


# ================================================================== origin-specific cohorts and covariates
def build(origin):
    """origin in {'diagnosis', 'surgery'}. Returns frame of eligible patients with time zero and covariates."""
    t0 = B.DG if origin == 'diagnosis' else B.OP
    ok = t0.notna() & B.TNM & B.STATUS.notna() & B.LAST.notna() & ((B.LAST - t0).dt.days > 0)
    d = B[ok].copy()
    d['T0'] = t0[ok]
    d['OS_Y'] = np.minimum((d.LAST - d.T0).dt.days / DAYS, MAXFU)
    d['OS_E'] = np.where((d.LAST - d.T0).dt.days / DAYS > MAXFU, 0.0, d.DEATH)
    d['AGE'] = (d.T0 - d.BIRTH).dt.days / DAYS
    d.loc[(d.AGE < 18) | (d.AGE > 100), 'AGE'] = np.nan
    # predictors are fixed at liver metastasis diagnosis (before any surgery): DFI measured to DG
    d['DFI'] = (d.DG - d.DGK).dt.days / 30.4375
    d.loc[d.SYNC == 1, 'DFI'] = 0.0
    d.loc[d.DFI < 0, 'DFI'] = np.nan
    d['ERA'] = np.where(d.T0.dt.year <= 2009, 'train', 'valid')
    d['T3'] = (d.T_GRP == 'T3').astype(float).where(d.T_GRP.notna())
    d['T4'] = (d.T_GRP == 'T4').astype(float).where(d.T_GRP.notna())
    d['N1'] = (d.N_GRP == 'N1').astype(float).where(d.N_GRP.notna())
    d['N2'] = (d.N_GRP == 'N2').astype(float).where(d.N_GRP.notna())
    d['M1'] = (d.M_GRP == 'M1').astype(float).where(d.M_GRP.notna())
    d['AGE10'] = d.AGE / 10
    d['DFI12'] = d.DFI / 12
    d['SIZE10'] = d.SIZE / 10
    return d


def add_fills(d, trm):
    for col in ['DFI', 'METS', 'SIZE']:
        d[col + '_NR'] = d[col].isna().astype(float)
    for col in ['AGE10', 'MALE', 'SYNC', 'DFI12', 'METS', 'SIZE10']:
        d[col + '_F'] = d[col].fillna(d.loc[trm, col].median())
    d['MALE_B'] = d.MALE_F.round().astype(int)
    d['SYNC_B'] = d.SYNC_F.round().astype(int)
    d['STRATUM'] = d.MALE_B * 2 + d.SYNC_B
    return d


CORE = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']


# ================================================================== stratified Breslow and prediction
def breslow(T, E, X, be, strat):
    lp = X @ be
    out = {}
    for s in np.unique(strat):
        m = strat == s
        t, e, l_ = T[m], E[m], lp[m]
        o = np.argsort(t, kind='mergesort')
        t, e, l_ = t[o], e[o], l_[o]
        risk = np.cumsum(np.exp(l_)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        if len(ev) == 0:
            out[s] = (np.array([0.0]), np.array([0.0])); continue
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        out[s] = (ev, np.cumsum(dk / risk[idx]))
    return out


def surv_at(bres, X, strat, be, times):
    lp = X @ be
    S = np.ones((len(X), len(times)))
    for s in np.unique(strat):
        m = strat == s
        ev, H = bres[s]
        ii = np.searchsorted(ev, times, side='right') - 1
        Hs = np.where(ii >= 0, H[np.clip(ii, 0, None)], 0.0)
        S[m] = np.exp(-np.exp(lp[m, None]) * Hs[None, :])
    return S


# ================================================================== IPCW decision curve
def censor_km(T, E):
    """Kaplan-Meier of the censoring distribution (training data)."""
    k = KaplanMeierFitter().fit(T, 1 - E)
    return k.survival_function_.index.values.astype(float), k.survival_function_.iloc[:, 0].values.astype(float)


def G_at(ct, cs, x):
    ii = np.searchsorted(ct, x, side='right') - 1
    return np.where(ii >= 0, cs[np.clip(ii, 0, None)], 1.0)


def net_benefit(T, E, decision_by_pt, t, G, pts):
    """IPCW net benefit at horizon t. decision_by_pt(pt) -> boolean array (True = treat)."""
    Y = (T <= t) & (E == 1)
    known = Y | (T > t)
    w = np.zeros(len(T))
    ct, cs = G
    w[known] = 1.0 / np.clip(G_at(ct, cs, np.minimum(T[known], t)), 1e-6, None)
    N = len(T)
    out = []
    for pt in pts:
        d = decision_by_pt(pt)
        odds = pt / (1 - pt)
        Yf, df_ = Y.astype(float), d.astype(float)
        nb = np.sum(w * (Yf * df_ - (~Y).astype(float) * known.astype(float) * odds * df_)) / N
        out.append(nb)
    return np.array(out)


# ================================================================== main analysis for one origin
def analyse(origin):
    tag = origin
    d = build(origin)
    d = add_fills(d, (d.ERA == 'train').values)
    trm = (d.ERA == 'train').values
    vam = (d.ERA == 'valid').values
    log(f'[{origin}] eligible {len(d):,} | train {trm.sum():,} (deaths {int(d.OS_E[trm].sum()):,}) | '
        f'valid {vam.sum():,} (deaths {int(d.OS_E[vam].sum()):,})')
    Ttr, Etr = d.OS_Y.values[trm], d.OS_E.values[trm]
    Tva, Eva = d.OS_Y.values[vam], d.OS_E.values[vam]
    rep = {'origin': origin, 'eligible': len(d), 'train_n': int(trm.sum()), 'valid_n': int(vam.sum()),
           'train_deaths': int(Etr.sum()), 'valid_deaths': int(Eva.sum())}

    # --- M1 stratified Cox, prespecified no-CEA covariates
    cph = CoxPHFitter().fit(d.loc[trm, CORE + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
    be = cph.params_[CORE].values
    hr = cph.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].reset_index()
    hr.columns = ['term', 'HR', 'HR_lower95', 'HR_upper95', 'p']
    save(hr.round(4), f'{tag}_M1_hazard_ratios')
    ph = proportional_hazard_test(cph, d.loc[trm, CORE + ['OS_Y', 'OS_E', 'STRATUM']], time_transform='rank').summary
    ph = ph.reset_index(); ph.columns = ['term'] + list(ph.columns[1:])
    save(ph.round(4), f'{tag}_M1_PH_test_training')
    X = d[CORE].astype(float).values
    strat = d.STRATUM.values
    bres = breslow(Ttr, Etr, X[trm], be, strat[trm])
    times = np.concatenate([[3.0, 5.0], TB])
    S = surv_at(bres, X, strat, be, times)
    lp_all = X @ be
    rep['M1_train_C'] = round(float(concordance_index(Ttr, -lp_all[trm], Etr)), 4)
    rep['M1_valid_C'] = round(float(concordance_index(Tva, -lp_all[vam], Eva)), 4)

    # --- Brier / tAUC / calibration on validation, M1 continuous risk
    Sva = S[vam]
    ysv = Surv.from_arrays(Eva.astype(bool), Tva)
    ytr = Surv.from_arrays(Etr.astype(bool), Ttr)
    try:
        _, bs = brier_score(ytr, ysv, Sva[:, 2:], TB)
        for t in [1.0, 3.0, 5.0]:
            rep[f'M1_Brier_{int(t)}y'] = round(float(bs[list(TB).index(t)]), 4)
        rep['M1_IBS'] = round(float(integrated_brier_score(ytr, ysv, Sva[:, 2:], TB)), 4)
    except Exception as ex:  # noqa: BLE001
        rep['M1_brier_note'] = str(ex)[:80]
    S3 = S[:, 0]; S5 = S[:, 1]
    dec = pd.qcut(pd.Series(S5[vam]).rank(method='first'), 10, labels=False).values
    cal = []
    for q in range(10):
        m = dec == q
        k = KaplanMeierFitter().fit(Tva[m], Eva[m])
        cal.append({'origin': origin, 'decile': q + 1, 'n': int(m.sum()), 'predicted_S5': round(float(S5[vam][m].mean()), 3),
                    'observed_S5_KM': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    cal = pd.DataFrame(cal)
    save(cal, f'{tag}_M1_calibration_5y_deciles')
    obs5 = float(KaplanMeierFitter().fit(Tva, Eva).survival_function_at_times(5).iloc[0])
    rep['M1_mean_pred_S5'] = round(float(S5[vam].mean()), 3)
    rep['M1_observed_S5'] = round(obs5, 3)
    rep['M1_OE_5y'] = round(obs5 / float(S5[vam].mean()), 3)
    slope = CoxPHFitter().fit(pd.DataFrame({'T': Tva, 'E': Eva, 'lp': np.log(-np.log(np.clip(S5[vam], 1e-6, 1 - 1e-6)))}), 'T', 'E').params_['lp']
    rep['M1_calib_slope_5y'] = round(float(slope), 3)

    # --- three prognostic groups: training tertiles of the training linear predictor (fixed rule)
    q1, q2 = np.quantile(lp_all[trm], [1 / 3, 2 / 3])
    grp = np.where(lp_all >= q2, 'Adverse', np.where(lp_all >= q1, 'Intermediate', 'Favourable'))
    d['GROUP'] = grp
    rep['tertile_cut_LP_q33'] = round(float(q1), 4); rep['tertile_cut_LP_q67'] = round(float(q2), 4)
    gt = []
    for period, mask in [('training', trm), ('validation', vam)]:
        for lab in ['Favourable', 'Intermediate', 'Adverse']:
            m = mask & (grp == lab)
            k = KaplanMeierFitter().fit(d.OS_Y[m], d.OS_E[m])
            ci = median_survival_times(k.confidence_interval_).iloc[0]
            med = k.median_survival_time_
            gt.append({'origin': origin, 'period': period, 'group': lab, 'n': int(m.sum()),
                       'share_pct': round(100 * m.sum() / mask.sum(), 1), 'deaths': int(d.OS_E[m].sum()),
                       'median_OS': round(float(med), 2) if np.isfinite(med) else None,
                       'median_95CI_lo': round(float(ci.iloc[0]), 2),
                       'median_95CI_hi': round(float(ci.iloc[1]), 2) if np.isfinite(ci.iloc[1]) else None,
                       'S5': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    gt = pd.DataFrame(gt)
    save(gt, f'{tag}_three_group_table')
    rank = d.GROUP.map({'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}).values.astype(float)
    rep['tertile_valid_C'] = round(float(concordance_index(Tva, rank[vam], Eva)), 4)
    rep['continuous_valid_C'] = rep['M1_valid_C']
    rep['tertile_valid_logrank_p'] = float(multivariate_logrank_test(Tva, grp[vam], Eva).p_value)
    rep['tertile_train_logrank_p'] = float(multivariate_logrank_test(Ttr, grp[trm], Etr).p_value)
    # group calibration at 5 years: training KM predicted vs validation KM observed
    gcal = []
    for lab in ['Favourable', 'Intermediate', 'Adverse']:
        kt = KaplanMeierFitter().fit(d.OS_Y[trm & (grp == lab)], d.OS_E[trm & (grp == lab)])
        kv = KaplanMeierFitter().fit(d.OS_Y[vam & (grp == lab)], d.OS_E[vam & (grp == lab)])
        gcal.append({'origin': origin, 'group': lab, 'predicted_S5_training': round(float(kt.survival_function_at_times(5).iloc[0]), 3),
                     'observed_S5_validation': round(float(kv.survival_function_at_times(5).iloc[0]), 3)})
    save(pd.DataFrame(gcal), f'{tag}_group_calibration_5y')

    # --- stability: bootstrap refits of M1 on training data; kappa vs main assignment on validation
    kap = []
    tr_idx = np.where(trm)[0]
    for _ in range(100):
        pick = RNG.choice(tr_idx, len(tr_idx), replace=True)
        db = d.iloc[pick][CORE + ['STRATUM', 'OS_Y', 'OS_E']]
        try:
            cb = CoxPHFitter().fit(db, 'OS_Y', 'OS_E', strata=['STRATUM'])
        except Exception:  # noqa: BLE001
            continue
        lpb = X @ cb.params_[CORE].values
        q1b, q2b = np.quantile(lpb[trm], [1 / 3, 2 / 3])
        gb = np.where(lpb >= q2b, 'Adverse', np.where(lpb >= q1b, 'Intermediate', 'Favourable'))
        kap.append(cohen_kappa_score(grp[vam], gb[vam]))
    rep['bootstrap_kappa_median'] = round(float(np.median(kap)), 3)
    rep['bootstrap_kappa_2.5pct'] = round(float(np.percentile(kap, 2.5)), 3)
    rep['bootstrap_resamples'] = len(kap)

    # --- decision curves at 3 and 5 years (IPCW, censoring KM from training)
    G = censor_km(Ttr, Etr)
    dcrows = []
    for h in HOR:
        j = 0 if h == 3.0 else 1
        risk_model = 1 - S[:, j]
        # model-based: treat when predicted risk >= threshold (validation patients)
        Tv, Ev = Tva, Eva
        rv = risk_model[vam]
        nb_model = net_benefit(Tv, Ev, lambda p: rv >= p, h, G, PT)
        nb_all = net_benefit(Tv, Ev, lambda p: np.ones(len(Tv), bool), h, G, PT)
        nb_none = np.zeros(len(PT))
        gv = grp[vam]
        nb_adv = net_benefit(Tv, Ev, lambda p: gv == 'Adverse', h, G, PT)
        for i, p in enumerate(PT):
            dcrows.append({'origin': origin, 'horizon_years': h, 'threshold': p,
                           'NB_model_continuous_risk': round(float(nb_model[i]), 4),
                           'NB_treat_adverse_group': round(float(nb_adv[i]), 4),
                           'NB_treat_all': round(float(nb_all[i]), 4), 'NB_treat_none': 0.0})
    save(pd.DataFrame(dcrows), f'{tag}_decision_curves_IPCW')

    # --- survival tree (no CEA; same covariates), training only; leaves merged to three groups by training RMST5
    Xt = d[CORE + ['MALE_F', 'SYNC_F']].astype(float).values.astype(np.float32)
    tr = SurvivalTree(max_depth=3, min_samples_leaf=max(200, int(0.02 * trm.sum())), random_state=SEED)
    y_all = Surv.from_arrays(event=d.OS_E.astype(bool).values, time=d.OS_Y.values)
    tr.fit(Xt[trm], y_all[trm])
    leaf = tr.apply(Xt)
    lrows = []
    for L in np.unique(leaf):
        m = (leaf == L) & trm
        k = KaplanMeierFitter().fit(d.OS_Y[m], d.OS_E[m])
        tt = k.survival_function_.index.values.astype(float); ss = k.survival_function_.iloc[:, 0].values.astype(float)
        grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < 5)], [5.0]])
        ix = np.searchsorted(tt, grid[:-1], side='right') - 1
        rm = float(np.sum(np.where(ix >= 0, ss[np.clip(ix, 0, None)], 1.0) * np.diff(grid)))
        lrows.append((L, int(m.sum()), rm, float(np.nan_to_num(k.median_survival_time_, nan=-1))))
    order = sorted(lrows, key=lambda r: -r[2])
    tot = sum(r[1] for r in order); cum = 0.0; mp = {}
    for L, n, rm, med in order:
        b = cum / tot; cum += n; mid = (b + cum / tot) / 2
        mp[L] = 'Favourable' if mid < 1 / 3 else ('Intermediate' if mid < 2 / 3 else 'Adverse')
    tree_grp = np.array([mp[L] for L in leaf])
    rank_t = np.array([{'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}[x] for x in tree_grp], float)
    rep['tree_valid_C'] = round(float(concordance_index(Tva, rank_t[vam], Eva)), 4)
    rep['tree_leaves'] = len(lrows)
    tl = []
    for lab in ['Favourable', 'Intermediate', 'Adverse']:
        m = vam & (tree_grp == lab)
        if m.sum() == 0:
            continue
        k = KaplanMeierFitter().fit(d.OS_Y[m], d.OS_E[m])
        tl.append({'origin': origin, 'tree_group': lab, 'valid_n': int(m.sum()),
                   'valid_median_OS': round(float(k.median_survival_time_), 2) if np.isfinite(k.median_survival_time_) else None,
                   'valid_S5': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    save(pd.DataFrame(tl), f'{tag}_tree_groups_validation')

    # --- benchmark comparison on identical patients: Fong (CEA-complete) and Nordlinger-type
    fong = (d.N_GRP.isin(['N1', 'N2']).astype(float) + (d.DFI < 12).astype(float) + (d.METS > 1).astype(float)
            + (d.SIZE > 50).astype(float) + (d.CEA > 200).astype(float))
    fong = fong.where(d.N_GRP.notna() & d.DFI.notna() & d.METS.notna() & d.SIZE.notna() & d.CEA.notna())
    nord = ((d.AGE >= 60).astype(float) + (d.T_GRP == 'T4').astype(float) + d.N_GRP.isin(['N1', 'N2']).astype(float)
            + (d.DFI < 12).astype(float))
    nord = nord.where(d.AGE.notna() & d.T_GRP.notna() & d.N_GRP.notna() & d.DFI.notna())
    bm = []
    for lab, sc in [('Fong CRS (CEA-complete)', fong), ('Nordlinger-type (unweighted)', nord)]:
        mt = trm & sc.notna().values; mv = vam & sc.notna().values
        if mv.sum() < 50:
            bm.append({'origin': origin, 'benchmark': lab, 'valid_n': int(mv.sum()), 'note': 'too few'}); continue
        bm.append({'origin': origin, 'benchmark': lab, 'train_n': int(mt.sum()), 'valid_n': int(mv.sum()),
                   'benchmark_valid_C': round(float(concordance_index(d.OS_Y.values[mv], -sc.values[mv], d.OS_E.values[mv])), 4),
                   'M1_same_patients_valid_C': round(float(concordance_index(d.OS_Y.values[mv], -lp_all[mv], d.OS_E.values[mv])), 4)})
    save(pd.DataFrame(bm), f'{tag}_benchmarks_same_patients')

    # --- RFS with recurrence evidence rule (time zero = origin)
    rec_after = d.REC_FIRST.notna() & (d.REC_FIRST >= d.T0) & (d.REC_FIRST <= d.LAST)
    rec_before = d.REC_FIRST.notna() & (d.REC_FIRST < d.T0)
    days = np.where(rec_after, (d.REC_FIRST - d.T0).dt.days, (d.LAST - d.T0).dt.days).astype(float)
    rT = np.clip(np.minimum(days / DAYS, MAXFU), 1 / DAYS, None)
    evidence = rec_after | d.DEATH.eq(1) | d.REC_COUNT_POS.reindex(d.index).fillna(False).astype(bool)
    rE = np.where(evidence, 1.0, 0.0)
    rE_sens = np.where(rec_after | d.DEATH.eq(1), 1.0, 0.0)                 # alive with disease, no date = censored
    rE_v1 = np.where(rec_after | d.DEATH.eq(1) | d.AWD1.reindex(d.index).fillna(False).astype(bool), 1.0, 0.0)  # earlier rule
    elig = ~rec_before.values
    rr = []
    for lab, E_ in [('evidence rule (primary)', rE), ('sensitivity: no-date recurrence censored', rE_sens),
                    ('earlier rule: all alive-with-disease events', rE_v1)]:
        k = KaplanMeierFitter().fit(rT[elig], E_[elig])
        ci = median_survival_times(k.confidence_interval_).iloc[0]
        rr.append({'origin': origin, 'RFS_definition': lab, 'n': int(elig.sum()), 'events': int(E_[elig].sum()),
                   'dated_recurrence_in_window': int(rec_after[elig].sum()),
                   'median_RFS': round(float(k.median_survival_time_), 2) if np.isfinite(k.median_survival_time_) else None,
                   'median_95CI_lo': round(float(ci.iloc[0]), 2), 'median_95CI_hi': round(float(ci.iloc[1]), 2) if np.isfinite(ci.iloc[1]) else None,
                   'RFS_3y': round(float(k.survival_function_at_times(3).iloc[0]), 3),
                   'RFS_5y': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    rr.append({'origin': origin, 'RFS_definition': 'recurrence before time zero (excluded from RFS)', 'n': int(rec_before.sum())})
    save(pd.DataFrame(rr), f'{tag}_RFS_definitions')
    rec_src = pd.Series(np.select([rec_after.values, d.DEATH.eq(1).values, d.REC_COUNT_POS.values],
                                  ['dated recurrence', 'death', 'recurrence count without date'], 'censored at last contact'))
    save(rec_src.value_counts().rename_axis('source').reset_index(name='n'), f'{tag}_RFS_event_sources')
    return d, rep, S, lp_all, grp


# ================================================================== run both origins
results = {}
for origin in ['diagnosis', 'surgery']:
    results[origin] = analyse(origin)
    log(f'{origin} done')
rep_all = pd.DataFrame([results[o][1] for o in results])
save(rep_all.T.reset_index().rename(columns={'index': 'quantity', 0: 'diagnosis', 1: 'surgery'}), 'SUMMARY_by_origin')
print(rep_all.T.to_string())

# ================================================================== reconciliation of the two origins
rec = []
for o in ['diagnosis', 'surgery']:
    d = results[o][0]
    rec.append({'origin': o, 'eligible': len(d), 'deaths': int(d.OS_E.sum()),
                'unique source rows': int(d[['PART', 'ROW']].drop_duplicates().shape[0])})
rec = pd.DataFrame(rec)
save(rec, 'RECONCILIATION_cohorts')
print(rec.to_string(index=False))
log(f'done -> {RES}')
