"""v6 sensitivity checks, read-only on the source extracts.

(a) Verification of the 19 same-day deaths (operation date = last-news date, status Deceased).
(b) Same-day convention: half-day (primary), one day, quarter day, and exclusion of the 19 patients.
(c) Day convention for partial operation dates (1st, 15th = primary, month-end), with the selected model
    specification (M2a: stratified sex x synchronous x M-stage). Phenotype agreement is computed on the same
    patients with the same model, so differences reflect only the date convention.
(d) Input-file integrity: SHA-256 of both workbooks compared with the hashes recorded in the first run.

Development uses training-era patients only (operation year <= 2009). Validation is used only to report.
"""
import calendar
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from sklearn.metrics import cohen_kappa_score

W = Path(os.environ['LIVERMET_WORK_DIR'])
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'final_v6'
IN = Path(os.environ['LIVERMET_DATA_DIR'])
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
MAXFU = 15.0
CORE_M2A = ['T3', 'T4', 'N1', 'N2', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


def ymd(v2, base, day):
    y = num(v2[base + '_Y']); m = num(v2[base + '_M']); d = num(v2[base + '_D'])
    if day == 'last':
        last = pd.Series([calendar.monthrange(int(a), int(b))[1] if (a == a and b == b) else np.nan for a, b in zip(y, m)], index=y.index)
        dd = d.fillna(last)
    else:
        dd = d.fillna(day)
    return pd.to_datetime(dict(year=y, month=m, day=dd), errors='coerce')


v1 = pd.read_parquet(W / 'combined_extract.parquet')
v2 = pd.read_parquet(W / 'combined_extract_v2.parquet')
TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}


def gmap(s, m):
    return s.astype(object).map(lambda x: m.get(x, np.nan) if isinstance(x, str) else np.nan)


INC = v1.CINCLUSION.eq('Yes'); HEP = v1.LE1HEPATECTYN_F1.eq('Yes')
LAST = serial(v2.LASTNDTC)
DEATH = v1.PATSTATC.eq('Deceased')
T_G = gmap(v1.STADET, TMAP); N_G = gmap(v1.STADEN, NMAP); M_G = gmap(v1.STADEM, MMAP)
TNM = pd.concat([T_G, N_G, M_G], axis=1).notna().all(axis=1)
BIRTH = serial(v2.BIRTHDT); DGK = serial(v2.DGKCOLDT); DG = serial(v2.LE1DGMETADT)
MALE = v1.GENDER.map({'Male': 1.0, 'Female': 0.0}); SYNC = v1.LE1METASYNCYN.map({'Yes': 1.0, 'No': 0.0})
METS = num(v1.LE1NBMETAHEPNUM).where(lambda x: (x >= 1) & (x <= 50))
SIZE = num(v1.LE1HEPMETASIZENUM).where(lambda x: (x > 0) & (x <= 300))
OP_SER = serial(v2.LE1OPERDT_F1)
OP_YM = {d: ymd(v2, 'LE1OPERDT_F1', d) for d in [1, 15, 'last']}
PST_ANY = v1.PATSTATC.notna()

# ---------------- (a) verification of the 19 same-day deaths
op15 = OP_SER.fillna(OP_YM[15])
fu15 = (LAST - op15).dt.days
base_mask = INC & HEP & OP_YM[15].notna() & PST_ANY & LAST.notna() & (LAST >= op15)
sameday = base_mask & DEATH & (fu15 == 0)
dk = pd.concat([v2[f'DEATHKYN_F{i}'] for i in range(1, 8)], axis=1)
ver = pd.DataFrame({
    'source_part': v1.SOURCE_PART[sameday].values,
    'excel_row': v1.SOURCE_EXCEL_ROW[sameday].values,
    'operation_date_serial_available': OP_SER[sameday].notna().values,
    'last_news_equals_operation_date': (LAST[sameday] == op15[sameday]).values,
    'deathkyn_any_yes': dk[sameday].eq('Yes').any(axis=1).values,
    'lastnd_f_max_equals_last_news': (pd.concat([serial(v2[f'LASTNDT_F{i}']) for i in range(1, 8)], axis=1).max(axis=1)[sameday] == LAST[sameday]).values,
    'tnm_complete': TNM[sameday].values,
    'stage_at_risk_of_tnm_missing': (~TNM[sameday]).values,
})
ver.to_csv(RES / 'F18_same_day_deaths_verification.csv', index=False)
print('same-day deaths (report step 7 rule):', len(ver))
print(ver.drop(columns=['excel_row']).sum(numeric_only=True).to_string())
print('same-day deaths with TNM complete (in modelling cohort):', int(ver.tnm_complete.sum()))

# ---------------- cohort builder for a given date convention and same-day convention
def cohort(day, same_day):
    op = OP_SER.fillna(OP_YM[day])
    partial = OP_SER.isna() & OP_YM[day].notna()
    fu = (LAST - op).dt.days
    s7 = INC & HEP & OP_YM[day].notna() & PST_ANY & LAST.notna() & (LAST >= op) & ((fu > 0) | DEATH)
    if same_day == 'exclude':
        s7 &= ~(DEATH & (fu == 0))
    d = pd.DataFrame({'SRC': v1.index[s7], 'T0': op[s7].values, 'LAST': LAST[s7].values, 'DEATH': DEATH[s7].astype(float).values,
                      'T_GRP': T_G[s7].values, 'N_GRP': N_G[s7].values, 'M_GRP': M_G[s7].values,
                      'MALE': MALE[s7].values, 'SYNC': SYNC[s7].values, 'METS': METS[s7].values, 'SIZE': SIZE[s7].values,
                      'DG': DG[s7].values, 'DGK': DGK[s7].values, 'BIRTH': BIRTH[s7].values, 'PARTIAL': partial[s7].values})
    d = d[d[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)].copy()
    d['T0'] = pd.to_datetime(d.T0); d['LAST'] = pd.to_datetime(d.LAST)
    days = (d['LAST'] - d['T0']).dt.days.astype(float)
    small = {'half': 0.5, 'one': 1.0, 'quarter': 0.25, 'exclude': 0.5}[same_day]
    time_days = np.where((days <= 0) & (d.DEATH == 1), small, days)
    d['OS_Y'] = np.minimum(time_days / DAYS, MAXFU)
    d['OS_E'] = np.where(time_days / DAYS > MAXFU, 0.0, d.DEATH)
    d['AGE'] = (d['T0'] - pd.to_datetime(d.BIRTH)).dt.days / DAYS
    d['DFI'] = (pd.to_datetime(d.DG) - pd.to_datetime(d.DGK)).dt.days / 30.4375
    d.loc[d.SYNC == 1, 'DFI'] = 0.0
    d.loc[(d.DFI < 0) | (pd.to_datetime(d.DG) > d['T0']), 'DFI'] = np.nan
    d['ERA'] = np.where(d['T0'].dt.year <= 2009, 'train', 'valid')
    d['T3'] = (d.T_GRP == 'T3').astype(float); d['T4'] = (d.T_GRP == 'T4').astype(float)
    d['N1'] = (d.N_GRP == 'N1').astype(float); d['N2'] = (d.N_GRP == 'N2').astype(float)
    d['M1'] = (d.M_GRP == 'M1').astype(float)
    d['PARTIAL'] = d.PARTIAL.astype(bool)
    return d.reset_index(drop=True)


def model_s5(d):
    trm = (d.ERA == 'train').values; vam = (d.ERA == 'valid').values
    d = d.copy()
    for c in ['DFI', 'METS', 'SIZE']:
        d[c + '_NR'] = d[c].isna().astype(float)
    for c in ['AGE', 'DFI', 'METS', 'SIZE']:
        d[c + '_F'] = d[c].fillna(d.loc[trm, c].median())
    d['AGE10_F'] = d.AGE_F / 10; d['DFI12_F'] = d.DFI_F / 12; d['SIZE10_F'] = d.SIZE_F / 10
    d['MALE_F'] = d.MALE.fillna(d.loc[trm, 'MALE'].median()); d['SYNC_F'] = d.SYNC.fillna(d.loc[trm, 'SYNC'].median())
    d['STRATUM'] = d.MALE_F.round().astype(int) * 2 + d.SYNC_F.round().astype(int)
    d['STRAT_M'] = d.STRATUM * 2 + d.M1.astype(int)
    cph = CoxPHFitter().fit(d.loc[trm, CORE_M2A + ['STRAT_M', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRAT_M'])
    be = cph.params_[CORE_M2A].values
    X = d[CORE_M2A].astype(float).values
    lp = X @ be
    st = d.STRAT_M.values
    S5 = np.ones(len(d))
    for s in np.unique(st):
        m = trm & (st == s)
        t, e, l_ = d.OS_Y.values[m], d.OS_E.values[m], lp[m]
        o = np.argsort(t, kind='mergesort'); t, e, l_ = t[o], e[o], l_[o]
        risk = np.cumsum(np.exp(l_)[::-1])[::-1]
        ev = np.unique(t[e == 1])
        idx = np.searchsorted(t, ev, side='left')
        dk_ = np.bincount(np.searchsorted(ev, t[e == 1]), minlength=len(ev)).astype(float)
        H = np.cumsum(dk_ / risk[idx])
        ii = np.searchsorted(ev, 5.0, side='right') - 1
        H5 = H[ii] if ii >= 0 else 0.0
        mm = st == s
        S5[mm] = np.exp(-np.exp(lp[mm]) * H5)
    return d, S5, cph, trm, vam


out = []
prim = cohort(15, 'half')
prim, S_prim, cph_p, trm_p, vam_p = model_s5(prim)
q33, q67 = np.quantile(S_prim[trm_p], [1 / 3, 2 / 3])
G_prim = np.where(S_prim >= q67, 'Favourable', np.where(S_prim >= q33, 'Intermediate', 'Adverse'))
prim_map = pd.DataFrame({'SRC': prim.SRC.values, 'G': G_prim})


def summarise(label, day, same_day):
    d = cohort(day, same_day)
    d, S5, cph, trm, vam = model_s5(d)
    a, b = np.quantile(S5[trm], [1 / 3, 2 / 3])
    G = np.where(S5 >= b, 'Favourable', np.where(S5 >= a, 'Intermediate', 'Adverse'))
    j = prim_map.merge(pd.DataFrame({'SRC': d.SRC.values, 'G': G}), on='SRC', how='inner', suffixes=('_p', '_c'))
    H5 = None
    row = {'analysis': label, 'modelling_TNM_n': len(d), 'train_n': int(trm.sum()), 'valid_n': int(vam.sum()),
           'train_deaths': int(d.OS_E.values[trm].sum()), 'cut_S5_q33': round(float(a), 4), 'cut_S5_q67': round(float(b), 4),
           'valid_C': round(float(concordance_index(d.OS_Y.values[vam], S5[vam], d.OS_E.values[vam])), 4),
           'STRATUM_M1_HR_male': round(float(cph.params_.get('MALE_F', np.nan)), 3) if 'MALE_F' in cph.params_ else None,
           'M_stage_in_model': 'stratum',
           'patients_in_common_with_primary': len(j),
           'phenotype_identical_pct_vs_primary': round(100 * float((j.G_p == j.G_c).mean()), 2),
           'kappa_vs_primary': round(float(cohen_kappa_score(j.G_p, j.G_c)), 3)}
    return row


rows = [
    summarise('primary: mid-month day, same-day deaths at half day', 15, 'half'),
    summarise('day convention: first day of month', 1, 'half'),
    summarise('day convention: month-end', 'last', 'half'),
    summarise('same-day deaths: one day', 15, 'one'),
    summarise('same-day deaths: quarter day', 15, 'quarter'),
    summarise('same-day deaths: excluded (19 patients)', 15, 'exclude'),
]
tab = pd.DataFrame(rows)
tab.to_csv(RES / 'F19_sensitivity_same_day_and_date_conventions.csv', index=False)
print(tab.to_string(index=False))

# ---------------- (d) input integrity
recorded = json.load(open(Path(os.environ['LIVERMET_RESULTS_DIR']) / 'logs' / 'input_hashes.json'))
hashes = {}
for k, fn in [('Part1', 'LiverMet_Part1.xlsx'), ('Part2', 'LiverMet_Part2.xlsx')]:
    h = hashlib.sha256((IN / fn).read_bytes()).hexdigest()
    hashes[k] = {'file': fn, 'sha256_now': h, 'sha256_recorded': recorded[k]['sha256'],
                 'unchanged': h == recorded[k]['sha256']}
json.dump(hashes, open(RES / 'F20_input_integrity.json', 'w'), indent=2)
print(json.dumps(hashes, indent=2))
print('sensitivity done')
