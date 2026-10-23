"""Audit of the v7 analysis (separate from the locked notebook; nothing here changes the primary results).

  1. Duplicate records: identification, same-patient assessment, and era of each copy.
  2. Duplicate sensitivity: cohort, survival, calibration, C-index and prognostic groups with and without second copies.
  3. Deaths and follow-up beyond 15 years: recorded deaths versus deaths inside the analysis window.
  4. TNM-complete model versus no-TNM model on exactly the same validation patients (and the broader cohort).
  5. Incomplete-TNM patients: differences by centre, operation year, outcome and clinical characteristics;
     informative-selection test using the no-TNM model.
  6. Summary numbers for the recommendation.

Inputs (from the investigation stages): LIVERMET_WORK_DIR/extract_raw.parquet, investigation_rows.parquet,
investigation_step7.parquet. Outputs: LIVERMET_OUT_DIR/audit (default results/final_v7/audit).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.utils import concordance_index
from sklearn.metrics import cohen_kappa_score

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v7/audit'))
OUT.mkdir(parents=True, exist_ok=True)
DAYS = 365.25
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
MAXFU = 15.0
rng = np.random.default_rng(42)

X = pd.read_parquet(WORK / 'extract_raw.parquet').reset_index(drop=True)
R = pd.read_parquet(WORK / 'investigation_rows.parquet').reset_index(drop=True)
D = pd.read_parquet(WORK / 'investigation_step7.parquet')
assert len(X) == len(R) == 29565 and len(D) == 26094


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


def save(df, name):
    df.to_csv(OUT / f'{name}.csv', index=False)
    print(f'--- {name}')
    print(df.to_string(index=False))
    return df


# =============================================================== 1. duplicate records
op_all = serial(X.LE1OPERDT_F1)
bd_all = serial(X.BIRTHDT)
nonblank_fields = R.N_NONBLANK_CELLS.values
pairs_mask = R.ROW_HASH.duplicated(keep=False).values
pairs = R[pairs_mask].copy()
pairs['ROW'] = pairs.index
pairs['GROUP'] = pairs.ROW_HASH
step7_rows = set(D.SRC.values)
cohort = D[D.TNM].set_index('SRC')
pairs['IN_STEP7'] = pairs.ROW.isin(step7_rows)
pairs['IN_COHORT'] = pairs.ROW.isin(set(cohort.index))
pairs['ERA'] = pairs.ROW.map(lambda r: cohort.ERA.get(r, 'not in cohort'))
pairs['BIRTH'] = bd_all.values[pairs.ROW]
pairs['OPER'] = op_all.values[pairs.ROW]

rows_pairs = []
for h, g in pairs.groupby('GROUP'):
    g = g.sort_values('ROW')
    a, b = g.iloc[0], g.iloc[1]
    same_bd = (a.BIRTH == b.BIRTH) or (pd.isna(a.BIRTH) and pd.isna(b.BIRTH))
    same_op = (a.OPER == b.OPER) or (pd.isna(a.OPER) and pd.isna(b.OPER))
    sites = f'{R.COUNTRY_ID[a.ROW]}-{R.SITE_ID[a.ROW]}  /  {R.COUNTRY_ID[b.ROW]}-{R.SITE_ID[b.ROW]}'
    cross_country = R.COUNTRY_ID[a.ROW] != R.COUNTRY_ID[b.ROW]
    rows_pairs.append({
        'pair_id': len(rows_pairs) + 1,
        'centres_country_site': sites,
        'cross_country': bool(cross_country),
        'same_patient_number_in_centre': bool(R.NUMPAT[a.ROW] == R.NUMPAT[b.ROW]),
        'nonblank_analysis_fields': int(a.N_NONBLANK_CELLS),
        'identical_on_all_fields_hash': True,
        'same_birth_date': bool(same_bd),
        'same_operation_date': bool(same_op),
        'in_step7_population': f'{int(a.IN_STEP7)}/{int(b.IN_STEP7)}',
        'in_analytic_cohort': f'{int(a.IN_COHORT)}/{int(b.IN_COHORT)}',
        'era_of_copies': '/'.join(sorted(set(g.ERA))),
    })
pair_tbl = pd.DataFrame(rows_pairs)
# decision rule: probable duplicate = identical on every non-blank analysis field AND same birth date AND same
# operation date AND at least 20 non-blank analysis fields. Pairs failing the rule are reported, not removed.
pair_tbl['probable_duplicate_rule'] = (pair_tbl.identical_on_all_fields_hash & pair_tbl.same_birth_date
                                       & pair_tbl.same_operation_date & (pair_tbl.nonblank_analysis_fields >= 20))
pair_tbl['probable_duplicate_rule'] = pair_tbl.probable_duplicate_rule.map(lambda v: bool(v))
save(pair_tbl, 'A01_duplicate_pairs_identification')

# near-duplicate screen: same birth date, operation date and sex, but not identical content
key_df = pd.DataFrame({'BIRTH': bd_all.values, 'OPER': op_all.values, 'SEX': X.GENDER.values,
                       'COUNTRY': R.COUNTRY_ID.values, 'HASH': R.ROW_HASH.values, 'ROW': np.arange(len(R))})
key_df = key_df.dropna(subset=['BIRTH', 'OPER'])
grp = key_df.groupby(['BIRTH', 'OPER', 'SEX']).filter(lambda g: len(g) > 1)
near = []
for _, g in grp.groupby(['BIRTH', 'OPER', 'SEX']):
    if g.HASH.nunique() == 1:
        continue  # identical pairs already listed
    near.append({'rows_in_group': len(g), 'distinct_contents': g.HASH.nunique(),
                 'countries': '/'.join(sorted(set(g.COUNTRY.astype(str)))), 'in_step7': int(g.ROW.isin(step7_rows).sum())})
near_tbl = pd.DataFrame(near)
summary_dup = pd.DataFrame([
    {'item': 'rows in identical-content pairs', 'n': int(pairs_mask.sum())},
    {'item': 'identical-content pairs', 'n': int(pair_tbl.shape[0])},
    {'item': 'pairs meeting the probable-duplicate rule', 'n': int(pair_tbl.probable_duplicate_rule.sum())},
    {'item': 'pairs with cross-country copies', 'n': int(pair_tbl.cross_country.sum())},
    {'item': 'pairs with both copies in step 7', 'n': int((pair_tbl.in_step7_population == '1/1').sum())},
    {'item': 'pairs with both copies in the analytic cohort', 'n': int((pair_tbl.in_analytic_cohort == '1/1').sum())},
    {'item': 'pairs with one copy in the analytic cohort', 'n': int(pair_tbl.in_analytic_cohort.isin(['1/0', '0/1']).sum())},
    {'item': 'copies in the same era (both in cohort)', 'n': int(((pair_tbl.in_analytic_cohort == '1/1') & (pair_tbl.era_of_copies.str.count('/') == 0)).sum())},
    {'item': 'pairs spanning development and validation', 'n': int((pair_tbl.era_of_copies.str.contains('development') & pair_tbl.era_of_copies.str.contains('validation')).sum())},
    {'item': 'near-duplicate groups (same birth date, operation date and sex; different content)', 'n': int(len(near_tbl))},
])
save(summary_dup, 'A00_duplicate_summary')
if len(near_tbl):
    save(near_tbl, 'A02_near_duplicate_groups')

# =============================================================== build the analysis frame (same rules as the notebook)
dgk = serial(X.DGKCOLDT).values[D.SRC.values]; dg = serial(X.LE1DGMETADT).values[D.SRC.values]
F = pd.DataFrame({'SRC': D.SRC.values, 'ERA': D.ERA.values, 'DEV': D.ERA.eq('development').values,
                  'TNM': D.TNM.values, 'OS_Y': D.OS_Y.values, 'OS_E': D.OS_E.values, 'DEATH': D.DEATH.values,
                  'OS_DAYS': D.OS_DAYS.values, 'T0': D.T0.values, 'AGE': D.AGE.values, 'MALE': D.MALE.values,
                  'SYNC': D.SYNC.values, 'METS': D.METS.values, 'SIZE': D.SIZE.values, 'CEA': D.CEA.values,
                  'YEAR': D.YEAR.values, 'COUNTRY': D.COUNTRY.values, 'SITE': D.SITE.values})
F['DFI'] = (pd.to_datetime(dg) - pd.to_datetime(dgk)).days / 30.4375
F.loc[F.SYNC == 1, 'DFI'] = 0.0
F.loc[(F.DFI < 0) | (pd.to_datetime(dg) > pd.to_datetime(F['T0'])), 'DFI'] = np.nan
T_MAP = {'T1-2': 0, 'T3': 1, 'T4': 2}; N_MAP = {'N0': 0, 'N1': 1, 'N2': 2}; M_MAP = {'M0': 0, 'M1': 1}
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(vals, mp):
    return pd.Series(vals).astype(object).map(lambda x: mp.get(x, np.nan) if isinstance(x, str) else np.nan).values


F['T_ORD'] = pd.Series(gmap(D.T_RAW.values, TMAP)).map(T_MAP).values
F['N_ORD'] = pd.Series(gmap(D.N_RAW.values, NMAP)).map(N_MAP).values
F['M_ORD'] = pd.Series(gmap(D.M_RAW.values, MMAP)).map(M_MAP).values
F['CEA_LOG'] = np.log1p(F.CEA)
assert (F.TNM == F[['T_ORD', 'N_ORD', 'M_ORD']].notna().all(axis=1)).all()
hash_src = R.ROW_HASH.values[F.SRC.values]


def covariates(G, ref):
    """Covariates with medians from the development rows of the frame G (ref = G itself, subsetted by caller)."""
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
NOTNM = ['AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']


def breslow(T, E, lp, st):
    out = {}
    for s in np.unique(st):
        m = st == s
        t, e, le = T[m], E[m], lp[m]
        o = np.argsort(t, kind='mergesort'); t, e, le = t[o], e[o], le[o]
        re_ = np.cumsum(np.exp(le)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        idx = np.searchsorted(t, ev, side='left')
        dk = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        out[s] = (ev, np.cumsum(dk / re_[idx]))
    return out


def fit(G, cols, strat, train):
    """Fit a stratified Cox model on the training rows of G; return coefficients and 5-year predicted survival."""
    cph = CoxPHFitter().fit(G.loc[train, cols + [strat, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[strat])
    be = cph.params_[cols].values
    Xm = G[cols].astype(float).values; st = G[strat].values
    bres = breslow(G.OS_Y.values[train], G.OS_E.values[train], Xm[train] @ be, st[train])
    S5 = np.ones(len(G))
    xe = Xm @ be
    for s in np.unique(st):
        m = st == s
        ev, H = bres[s]
        ii = np.searchsorted(ev, 5.0, side='right') - 1
        He = H[ii] if ii >= 0 else 0.0
        S5[m] = np.exp(-np.exp(xe[m]) * He)
    return be, S5, cph


def cidx(T, risk, E):
    return round(float(concordance_index(T, -risk, E)), 4)


def km5(T, E):
    if len(T) == 0 or (T >= 5).sum() == 0:
        return np.nan
    return float(KaplanMeierFitter().fit(T, E).survival_function_at_times(5).iloc[0])


def groups(S5, train):
    q1, q2 = np.quantile(S5[train], [1 / 3, 2 / 3])
    return np.where(S5 >= q2, 'Favourable', np.where(S5 >= q1, 'Intermediate', 'Adverse')), q1, q2


# =============================================================== 2. duplicate sensitivity (primary vs second copies removed)
PRIM = covariates(F[F.TNM].reset_index(drop=True), None)
# second copies are identified within the TNM-complete cohort, so a valid record is never dropped because its twin lacks TNM
PRIM['DUP2'] = pd.Series(R.ROW_HASH.values[PRIM.SRC.values]).duplicated(keep='first').values
be_p, S5_p, _ = fit(PRIM, M2A, 'STRAT_M', PRIM.DEV.values)
val_p = ~PRIM.DEV.values
risk_p = -np.log(np.clip(S5_p, 1e-12, 1))
C_p = round(float(concordance_index(PRIM.OS_Y.values[val_p], -risk_p[val_p], PRIM.OS_E.values[val_p])), 4)
G_p, q1p, q2p = groups(S5_p, PRIM.DEV.values)

DEDUP = covariates(PRIM[~PRIM.DUP2].reset_index(drop=True), None)
be_d, S5_d, _ = fit(DEDUP, M2A, 'STRAT_M', DEDUP.DEV.values)
val_d = ~DEDUP.DEV.values
risk_d = -np.log(np.clip(S5_d, 1e-12, 1))
C_d = round(float(concordance_index(DEDUP.OS_Y.values[val_d], -risk_d[val_d], DEDUP.OS_E.values[val_d])), 4)
G_d, q1d, q2d = groups(S5_d, DEDUP.DEV.values)

# patient-level comparison on patients present in both
common = np.intersect1d(PRIM.SRC.values, DEDUP.SRC.values)
gp = pd.Series(G_p, index=PRIM.SRC.values).loc[common].values
gd = pd.Series(G_d, index=DEDUP.SRC.values).loc[common].values
dup_rows = []


def arm(name, G, S5, G_group, q1, q2):
    dev, val = G.DEV.values, ~G.DEV.values
    km_val = KaplanMeierFitter().fit(G.OS_Y.values[val], G.OS_E.values[val])
    row = {'analysis': name, 'analytic_n': len(G), 'development_n': int(dev.sum()), 'validation_n': int(val.sum()),
           'validation_deaths': int(G.OS_E.values[val].sum()),
           'validation_C': cidx(G.OS_Y.values[val], -np.log(np.clip(S5, 1e-12, 1))[val], G.OS_E.values[val]),
           'validation_KM_5y': round(km5(G.OS_Y.values[val], G.OS_E.values[val]), 4),
           'validation_mean_predicted_5y': round(float(S5[val].mean()), 4),
           'validation_O_over_E_5y': round(km5(G.OS_Y.values[val], G.OS_E.values[val]) / float(S5[val].mean()), 4),
           'validation_median_OS_years': round(float(km_val.median_survival_time_), 3),
           'cut_S5_q33': round(float(q1), 4), 'cut_S5_q67': round(float(q2), 4)}
    for g in ['Favourable', 'Intermediate', 'Adverse']:
        m = val & (G_group == g)
        row[f'{g}_validation_n'] = int(m.sum())
    return row


# broader sensitivity: drop the later record of any pair sharing birth date, operation date and sex (exact or near duplicates)
key_src = pd.DataFrame({'SRC': PRIM.SRC.values, 'BD': bd_all.values[PRIM.SRC.values], 'OP': op_all.values[PRIM.SRC.values],
                        'SEX': X.GENDER.values[PRIM.SRC.values]}).dropna(subset=['BD', 'OP'])
key_src = key_src.sort_values('SRC')
later = key_src.duplicated(['BD', 'OP', 'SEX'], keep='first')
drop_src = set(key_src.SRC[later].values)
NEAR = covariates(PRIM[~PRIM.SRC.isin(drop_src)].reset_index(drop=True), None)
be_n2, S5_n2, _ = fit(NEAR, M2A, 'STRAT_M', NEAR.DEV.values)
G_n2, q1n, q2n = groups(S5_n2, NEAR.DEV.values)
print('exact-or-near duplicates (later copy dropped):', int(later.sum()), '| in development:', int(PRIM[PRIM.SRC.isin(drop_src)].DEV.sum()))
common_n = np.intersect1d(PRIM.SRC.values, NEAR.SRC.values)
gn = pd.Series(G_n2, index=NEAR.SRC.values).loc[common_n].values
gpn = pd.Series(G_p, index=PRIM.SRC.values).loc[common_n].values
dup_rows.append(arm('primary (all TNM-complete records)', PRIM, S5_p, G_p, q1p, q2p))
dup_rows.append(arm('second copies of identical records removed', DEDUP, S5_d, G_d, q1d, q2d))
dup_rows.append(arm('exact or near duplicates removed (later record of birth date, operation date and sex match)', NEAR, S5_n2, G_n2, q1n, q2n))
dup_tbl = pd.DataFrame(dup_rows)
dup_tbl['kappa_vs_primary_common_patients'] = [None, round(float(cohen_kappa_score(gp, gd)), 4), round(float(cohen_kappa_score(gpn, gn)), 4)]
dup_tbl['pct_same_group_common_patients'] = [None, round(100 * float((gp == gd).mean()), 2), round(100 * float((gpn == gn).mean()), 2)]
dup_tbl['patients_reassigned'] = [None, int((gp != gd).sum()), int((gpn != gn).sum())]
save(dup_tbl, 'A03_duplicate_sensitivity')
print('reproduction check: primary validation C (v7 F02 = 0.6216):', C_p)

# =============================================================== 3. deaths and follow-up beyond 15 years
an = F[F.TNM]
beyond = an.OS_DAYS / DAYS > MAXFU
deaths_tbl = pd.DataFrame([
    {'quantity': 'deaths recorded (PATSTATC = Deceased), analytic cohort', 'n': int(an.DEATH.sum()), 'note': 'all recorded deaths'},
    {'quantity': 'deaths inside the 15-year analysis window (OS_E = 1), analytic cohort', 'n': int(an.OS_E.sum()),
     'note': 'used in the models'},
    {'quantity': 'deaths beyond 15 years, censored at 15 years', 'n': int(an.DEATH.sum() - an.OS_E.sum()),
     'note': 'recorded deaths not counted as events'},
    {'quantity': 'patients with follow-up beyond 15 years (the notebook F12 row, labelled "deaths")', 'n': int(beyond.sum()),
     'note': 'this is a patient count, not a death count'},
    {'quantity': '  of whom died', 'n': int((beyond & (an.DEATH == 1)).sum()), 'note': 'the deaths counted above'},
    {'quantity': '  of whom alive or lost to follow-up', 'n': int((beyond & (an.DEATH == 0)).sum()), 'note': 'censored at 15 years'},
    {'quantity': 'development: deaths recorded / inside window', 'n': f'{int(an[an.DEV].DEATH.sum()):,} / {int(an[an.DEV].OS_E.sum()):,}', 'note': ''},
    {'quantity': 'validation: deaths recorded / inside window', 'n': f'{int(an[~an.DEV].DEATH.sum()):,} / {int(an[~an.DEV].OS_E.sum()):,}', 'note': ''},
])
save(deaths_tbl, 'A04_deaths_and_15_year_window')

# =============================================================== 4. TNM model vs no-TNM model on identical patients
cohort = F[F.TNM].reset_index(drop=True)
COH = covariates(cohort, None)                       # TNM-complete analytic cohort, medians from TNM-complete development
be_t, S5_t, _ = fit(COH, M2A, 'STRAT_M', COH.DEV.values)
be_n, S5_n, _ = fit(COH, NOTNM, 'STRATUM', COH.DEV.values)
val8799 = ~COH.DEV.values
r_t = -np.log(np.clip(S5_t, 1e-12, 1)); r_n = -np.log(np.clip(S5_n, 1e-12, 1))
C_t = cidx(COH.OS_Y.values[val8799], r_t[val8799], COH.OS_E.values[val8799])
C_n = cidx(COH.OS_Y.values[val8799], r_n[val8799], COH.OS_E.values[val8799])
idx = np.where(val8799)[0]
diffs = []
for _ in range(300):
    b = rng.choice(idx, len(idx), replace=True)
    ct = concordance_index(COH.OS_Y.values[b], -r_t[b], COH.OS_E.values[b])
    cn = concordance_index(COH.OS_Y.values[b], -r_n[b], COH.OS_E.values[b])
    diffs.append(ct - cn)
diffs = np.array(diffs)
# no-TNM model fitted on all development patients (broader), evaluated on the same 8,799 and on all validation patients
ALL = covariates(F.reset_index(drop=True), None)
be_nb, S5_nb, _ = fit(ALL, NOTNM, 'STRATUM', ALL.DEV.values)
r_nb = -np.log(np.clip(S5_nb, 1e-12, 1))
src_coh = COH.SRC.values
pos_all = pd.Series(np.arange(len(ALL)), index=ALL.SRC.values)
ii = pos_all.loc[src_coh].values
C_nb_same = cidx(COH.OS_Y.values[val8799], r_nb[ii][val8799], COH.OS_E.values[val8799])
val_all = ~ALL.DEV.values
C_nb_all = cidx(ALL.OS_Y.values[val_all], r_nb[val_all], ALL.OS_E.values[val_all])
cmp_tbl = pd.DataFrame([
    {'model': 'TNM M2a (complete-case development, 8,463)', 'validation_population': 'TNM-complete validation (8,799)', 'validation_n': 8799,
     'C_index': C_t, 'C_95CI_paired_diff_vs_no_TNM': ''},
    {'model': 'no-TNM model (complete-case development, 8,463)', 'validation_population': 'TNM-complete validation (8,799)', 'validation_n': 8799,
     'C_index': C_n, 'C_95CI_paired_diff_vs_no_TNM': f'difference TNM - no-TNM = {C_t - C_n:.4f} (95% CI {np.percentile(diffs, 2.5):.4f} to {np.percentile(diffs, 97.5):.4f})'},
    {'model': 'no-TNM model (broad development, 14,127)', 'validation_population': 'TNM-complete validation (8,799)', 'validation_n': 8799,
     'C_index': C_nb_same, 'C_95CI_paired_diff_vs_no_TNM': ''},
    {'model': 'no-TNM model (broad development, 14,127)', 'validation_population': 'all validation patients incl. TNM-incomplete', 'validation_n': int(val_all.sum()),
     'C_index': C_nb_all, 'C_95CI_paired_diff_vs_no_TNM': 'not comparable with TNM model (different patients)'},
])
save(cmp_tbl, 'A05_TNM_vs_no_TNM_same_patients')

# =============================================================== 5. incomplete-TNM patients
E5 = F[~F.TNM].copy()
A5 = F[F.TNM].copy()
E5['YEARBAND'] = pd.cut(E5.YEAR, [1989, 1999, 2004, 2009, 2014, 2020], labels=['1990-1999', '2000-2004', '2005-2009', '2010-2014', '2015-2020'])
A5['YEARBAND'] = pd.cut(A5.YEAR, [1989, 1999, 2004, 2009, 2014, 2020], labels=['1990-1999', '2000-2004', '2005-2009', '2010-2014', '2015-2020'])
rows_band = []
for b in ['1990-1999', '2000-2004', '2005-2009', '2010-2014', '2015-2020']:
    a = A5[A5.YEARBAND == b]; e = E5[E5.YEARBAND == b]
    rows_band.append({'operation_years': b, 'analytic_n': len(a), 'excluded_n': len(e),
                      'pct_excluded': round(100 * len(e) / max(len(a) + len(e), 1), 1)})
band_tbl = pd.DataFrame(rows_band)
save(band_tbl, 'A06_incomplete_TNM_by_operation_year')

# site and country distribution of incompleteness
site = F.groupby('SITE').agg(n=('TNM', 'size'), excluded=('TNM', lambda s: int((~s).sum())))
site['pct_excluded'] = 100 * site.excluded / site.n
country = F.groupby('COUNTRY').agg(n=('TNM', 'size'), excluded=('TNM', lambda s: int((~s).sum())))
country['pct_excluded'] = 100 * country.excluded / country.n
site_tbl = pd.DataFrame([{
    'level': 'sites', 'units': len(site), 'units_0pct_excluded': int((site.pct_excluded == 0).sum()),
    'units_100pct_excluded': int((site.pct_excluded == 100).sum()),
    'units_50pct_or_more_excluded': int((site.pct_excluded >= 50).sum()),
    'median_patients_per_unit': int(site.n.median()),
    'share_of_excluded_in_top_10_sites_pct': round(100 * site.excluded.nlargest(10).sum() / site.excluded.sum(), 1)},
    {'level': 'countries', 'units': len(country), 'units_0pct_excluded': int((country.pct_excluded == 0).sum()),
     'units_100pct_excluded': int((country.pct_excluded == 100).sum()),
     'units_50pct_or_more_excluded': int((country.pct_excluded >= 50).sum()),
     'median_patients_per_unit': int(country.n.median()),
     'share_of_excluded_in_top_10_sites_pct': round(100 * country.excluded.nlargest(10).sum() / country.excluded.sum(), 1)}])
save(site_tbl, 'A07_incomplete_TNM_clustering_by_centre_and_country')

# clinical characteristics and outcomes, included vs excluded (complete data only where noted)
def desc(col, lab, kind='cont'):
    a = A5[col].dropna(); e = E5[col].dropna()
    if kind == 'cont':
        sd = np.sqrt((a.var() + e.var()) / 2)
        return {'characteristic': lab, 'included': f'{a.median():.1f} (IQR {a.quantile(.25):.1f}-{a.quantile(.75):.1f}), n={len(a):,}',
                'excluded': f'{e.median():.1f} (IQR {e.quantile(.25):.1f}-{e.quantile(.75):.1f}), n={len(e):,}',
                'SMD': round(float((a.mean() - e.mean()) / sd), 3)}
    pa, pe = a.mean(), e.mean()
    sd = np.sqrt((pa * (1 - pa) + pe * (1 - pe)) / 2)
    return {'characteristic': lab, 'included': f'{100 * pa:.1f}%, n={len(a):,}', 'excluded': f'{100 * pe:.1f}%, n={len(e):,}',
            'SMD': round(float((pa - pe) / sd), 3)}


def desc_meta(col, lab):
    a = A5[(A5.SYNC == 0) & A5[col].notna()][col]
    e = E5[(E5.SYNC == 0) & E5[col].notna()][col]
    sd = np.sqrt((a.var() + e.var()) / 2)
    return {'characteristic': lab, 'included': f'{a.median():.1f} (IQR {a.quantile(.25):.1f}-{a.quantile(.75):.1f}), n={len(a):,}',
            'excluded': f'{e.median():.1f} (IQR {e.quantile(.25):.1f}-{e.quantile(.75):.1f}), n={len(e):,}',
            'SMD': round(float((a.mean() - e.mean()) / sd), 3)}


rows_c = [desc('AGE', 'Age, years', 'cont'), desc('MALE', 'Male sex', 'bin'), desc('SYNC', 'Synchronous presentation', 'bin'),
          desc_meta('DFI', 'Interval primary to liver metastasis, months (metachronous with interval known)'),
          desc('METS', 'Number of liver metastases (known)', 'cont'), desc('SIZE', 'Largest metastasis, mm (known)', 'cont'),
          desc('CEA', 'Pre-operative CEA, ng/mL (known)', 'cont'), desc('YEAR', 'Operation year', 'cont')]
_mi = A5[A5.SYNC == 0]; _me = E5[E5.SYNC == 0]
rows_c.append({'characteristic': 'Metachronous: interval unavailable (date missing, negative or after operation)',
               'included': f'{100 * _mi.DFI.isna().mean():.1f}%, n={len(_mi):,}', 'excluded': f'{100 * _me.DFI.isna().mean():.1f}%, n={len(_me):,}', 'SMD': None})
char_tbl = pd.DataFrame(rows_c)
save(char_tbl, 'A08_incomplete_TNM_characteristics')

# outcomes by period, included vs excluded
rows_o = []
for lab, a, e in [('all', A5, E5), ('development (<=2009)', A5[A5.DEV], E5[E5.DEV]), ('validation (>=2010)', A5[~A5.DEV], E5[~E5.DEV])]:
    rows_o.append({'group': lab, 'included_n': len(a), 'excluded_n': len(e),
                   'included_deaths_pct': round(100 * a.DEATH.mean(), 1), 'excluded_deaths_pct': round(100 * e.DEATH.mean(), 1),
                   'included_KM_5y': round(km5(a.OS_Y.values, a.OS_E.values), 3), 'excluded_KM_5y': round(km5(e.OS_Y.values, e.OS_E.values), 3),
                   'included_KM_median_y': round(float(KaplanMeierFitter().fit(a.OS_Y.values, a.OS_E.values).median_survival_time_), 2),
                   'excluded_KM_median_y': round(float(KaplanMeierFitter().fit(e.OS_Y.values, e.OS_E.values).median_survival_time_), 2)})
out_tbl = pd.DataFrame(rows_o)
save(out_tbl, 'A09_incomplete_TNM_outcomes')

# informative-selection test: does the no-TNM model (fitted on development, all patients) predict outcomes of excluded
# patients as well as those of included patients? observed/expected 5-year survival in each group, by period.
rows_sel = []
for lab, mask in [('included (TNM complete)', F.TNM.values), ('excluded (TNM incomplete)', ~F.TNM.values)]:
    for per, pm in [('development', ALL.DEV.values), ('validation', ~ALL.DEV.values)]:
        m = mask & pm
        pred5 = S5_nb[m].mean()
        obs5 = km5(ALL.OS_Y.values[m], ALL.OS_E.values[m])
        rows_sel.append({'group': lab, 'period': per, 'n': int(m.sum()), 'predicted_5y_no_TNM': round(float(pred5), 3),
                         'observed_5y_KM': round(obs5, 3), 'O_over_E': round(obs5 / pred5, 3)})
sel_tbl = pd.DataFrame(rows_sel)
save(sel_tbl, 'A10_informative_selection_test_no_TNM_model')

# logistic model for TNM completeness (who is excluded?), with covariates recorded for everyone
try:
    import statsmodels.api as sm
    Xl = pd.DataFrame({'const': 1.0, 'valid_era': (ALL.YEAR.values >= 2010).astype(float),
                       'synchronous': ALL.SYNC.fillna(0).values,
                       'age_per10': (ALL.AGE.fillna(ALL.AGE.median()).values / 10),
                       'male': ALL.MALE.fillna(0).values,
                       'size_per10mm': (ALL.SIZE.fillna(ALL.SIZE.median()).values / 10),
                       'metastases_per_1': ALL.METS.fillna(ALL.METS.median()).values})
    lm = sm.Logit((ALL.TNM.astype(float)).values, Xl).fit(disp=0)
    lo = pd.DataFrame({'term': lm.params.index, 'OR_complete_TNM': np.exp(lm.params.values),
                       'CI_low': np.exp(lm.conf_int()[0].values), 'CI_high': np.exp(lm.conf_int()[1].values),
                       'p': lm.pvalues.values}).round(4)
    save(lo, 'A11_logistic_TNM_completeness')
except Exception as exc:  # noqa: BLE001
    print('logistic model skipped:', exc)

# =============================================================== 6. summary for the recommendation
summary = pd.DataFrame([
    {'quantity': 'analytic cohort (TNM complete)', 'value': len(COH)},
    {'quantity': 'excluded for incomplete TNM', 'value': len(E5)},
    {'quantity': 'primary validation C (reproduction)', 'value': C_p},
    {'quantity': 'duplicate-removed validation C', 'value': C_d},
    {'quantity': 'TNM vs no-TNM C on the same 8,799 validation patients', 'value': f'{C_t:.4f} vs {C_n:.4f}'},
    {'quantity': 'no-TNM C on all validation patients (broad model)', 'value': C_nb_all},
])
save(summary, 'A12_summary')
print('audit done ->', OUT)
