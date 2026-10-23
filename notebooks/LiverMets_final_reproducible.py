# %% [markdown]
# # CRLM survival: final reproducible analysis from the raw workbooks
#
# This notebook starts from the two raw LiverMetSurvey Excel files (`LiverMet_Part1.xlsx`, `LiverMet_Part2.xlsx`),
# streams them into a compact extract, and reproduces the final analysis (v6 pipeline) together with the checks
# completed afterwards: the uncertain same-day deaths, the pre-operative-only sensitivity model, and calibration.
#
# **Design rules**
# * Development uses training-era patients only (operation year <= 2009). Temporal validation (>= 2010) is used only to
#   evaluate fixed models, cut-points and rules. No model is chosen by C-index.
# * Model selection follows the pre-specified PH rule (first candidate whose training Schoenfeld tests all pass).
# * Partial operation dates use the mid-month (15th) rule; the first-day and month-end rules are sensitivity analyses.
# * Same-day deaths (operation date = last-news date) are set to half a day; alternatives are reported.
# * Undated recurrences are censored for RFS in the primary analysis; alternatives are reported.
#
# **To run:** set `LIVERMET_DATA_DIR` to the folder holding the two raw workbooks (in Colab, upload them to `/content`).
# Outputs are written to `LIVERMET_OUT_DIR`. If an earlier results folder with `final_v6/` is present at `LIVERMET_REF_DIR`,
# the last section checks that the key numbers reproduce.

# %% [code]
import calendar
import hashlib
import json
import os
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from lifelines import CoxPHFitter, CoxTimeVaryingFitter, KaplanMeierFitter, NelsonAalenFitter
from lifelines.statistics import multivariate_logrank_test, proportional_hazard_test
from lifelines.utils import concordance_index, median_survival_times, to_episodic_format
from python_calamine import CalamineWorkbook
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import cohen_kappa_score
from sksurv.metrics import brier_score, cumulative_dynamic_auc, integrated_brier_score
from sksurv.util import Surv

warnings.filterwarnings('ignore')
T_START = time.time()
DATA_DIR = Path(os.environ.get('LIVERMET_DATA_DIR', '/content'))
WORK_DIR = Path(os.environ.get('LIVERMET_WORK_DIR', '/content/work'))
OUT_DIR = Path(os.environ.get('LIVERMET_OUT_DIR', '/content/results_final'))
REF_DIR = Path(os.environ.get('LIVERMET_REF_DIR', '/content/none'))
WORK_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)
SEED = 42
RNG = np.random.default_rng(SEED)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
MAXFU = 15.0
CUT = 2.0
TB = np.arange(1.0, 7.5, 0.5)
TIMES = np.concatenate([[3.0, 5.0], TB])
CENSOR = pd.Timestamp('2020-07-04')
INPUT_SHA256 = {
    'LiverMet_Part1.xlsx': '7eed0ab953a3b09da616e71b03664ea1dcacd5ad3c6a4b47e70d57bfc393a976',
    'LiverMet_Part2.xlsx': 'a1839daaded4b5e4619154e247428a8f2e15fcdc53066a8d67a819b53a161049',
}
EXPECTED_ROWS = {'Part1': 14782, 'Part2': 14783}


def log(msg):
    print(f'[{time.time() - T_START:6.0f}s] {msg}', flush=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(df, name):
    df.to_csv(OUT_DIR / f'{name}.csv', index=False)
    return df


log(f'data: {DATA_DIR}  work: {WORK_DIR}  output: {OUT_DIR}')

# %% [markdown]
# ## 1. Stream the raw workbooks into a compact extract
#
# Each workbook is read row by row (`python-calamine`), so the full sheet is never held in memory. Only the fields used
# by the analysis are kept. Part 1 has a header on Excel row 2; Part 2 has no header and is aligned to the same columns.
# Blank rows are skipped. Row counts are checked against the expected totals (14,782 + 14,783 = 29,565).

# %% [code]
DIRECT = ['CINCLUSION', 'LE1HEPATECTYN_F1', 'PATSTATC', 'STADET', 'STADEN', 'STADEM', 'GENDER', 'LE1METASYNCYN',
          'LE1NBMETAHEPNUM', 'LE1HEPMETASIZENUM', 'LE1PREHEPCEA_F1']
DATES = (['LE1OPERDT_F1', 'LASTNDTC', 'BIRTHDT', 'DGKCOLDT', 'LE1DGMETADT']
         + [f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
         + [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)] + [f'RECDT_F{i}' for i in range(1, 8)]
         + [f'LASTNDT_F{i}' for i in range(1, 8)])
STATUS = [f'DEATHKYN_F{i}' for i in range(1, 8)] + [f'PATSTAT_F{i}' for i in range(1, 8)]
COUNTS = [f'LRNBREC_M{i}' for i in range(1, 6)] + [f'EXHNBREC2_M{i}' for i in range(1, 9)]
BASES = DIRECT + DATES + STATUS + COUNTS
PARTS = {'Part1': DATA_DIR / 'LiverMet_Part1.xlsx', 'Part2': DATA_DIR / 'LiverMet_Part2.xlsx'}
EXTRACT = WORK_DIR / 'extract_raw.parquet'


def nonblank_rows(path):
    sheet = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for rn, row in enumerate(sheet.iter_rows(), start=1):
        if all(v is None or v == '' for v in row):
            continue
        yield rn, row


def conv(v):
    if v is None or v == '':
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# header: first non-blank row of Part 1
header_rn, header = next(nonblank_rows(PARTS['Part1']))
header = [str(v) for v in header]
pos = {h: j for j, h in enumerate(header)}
missing = [b for b in BASES if b not in pos]
assert not missing, f'columns missing from the workbook: {missing}'
cols = []
for b in BASES:
    for c in [b, b + '_D', b + '_M', b + '_Y']:
        if c in pos and c not in cols:
            cols.append(c)
idx = [pos[c] for c in cols]
log(f'header: {len(header)} columns; extracting {len(cols)}')

schema = pa.schema([(c, pa.string()) for c in cols] + [('SOURCE_PART', pa.string()), ('SOURCE_EXCEL_ROW', pa.int32())])
writer = pq.ParquetWriter(EXTRACT, schema, compression='zstd')
row_counts = {}
for part, path in PARTS.items():
    buf = {c: [] for c in cols}
    src, rows = [], []
    n = 0
    for rn, row in nonblank_rows(path):
        if part == 'Part1' and rn == header_rn:
            continue
        L = len(row)
        for c, j in zip(cols, idx):
            buf[c].append(conv(row[j]) if j < L else None)
        src.append(part); rows.append(rn); n += 1
        if len(src) >= 2000:
            tbl = pa.table({**{c: pa.array(buf[c], pa.string()) for c in cols},
                            'SOURCE_PART': src, 'SOURCE_EXCEL_ROW': pa.array(rows, pa.int32())}, schema=schema)
            writer.write_table(tbl)
            buf = {c: [] for c in cols}; src, rows = [], []
    if src:
        tbl = pa.table({**{c: pa.array(buf[c], pa.string()) for c in cols},
                        'SOURCE_PART': src, 'SOURCE_EXCEL_ROW': pa.array(rows, pa.int32())}, schema=schema)
        writer.write_table(tbl)
    row_counts[part] = n
    log(f'{part}: {n:,} patient rows')
writer.close()
assert row_counts == EXPECTED_ROWS, f'unexpected row counts {row_counts}'
X = pd.read_parquet(EXTRACT)
assert len(X) == 29565
flow_rows = pd.DataFrame([{'check': 'Part1 patient rows (header excluded)', 'n': row_counts['Part1']},
                          {'check': 'Part2 patient rows (no header)', 'n': row_counts['Part2']},
                          {'check': 'combined rows', 'n': len(X)}])
save(flow_rows, 'F00a_extract_row_counts')
manifest_inputs = {f: {'sha256': sha256(DATA_DIR / f), 'matches_recorded': sha256(DATA_DIR / f) == h}
                   for f, h in INPUT_SHA256.items()}
print(flow_rows.to_string(index=False))
print(json.dumps(manifest_inputs, indent=1))

# %% [markdown]
# ## 2. Definitions, cohort and survival variables
#
# Dates are Excel serial numbers (origin 1899-12-30). Component columns (`_D`, `_M`, `_Y`) fill partial operation dates
# with the 15th (primary), the 1st, or the last day of the month. Time origin is the first hepatectomy. Death is
# `PATSTATC = Deceased`; censoring is at the last-news date (`LASTNDTC`), capped at 15 years.

# %% [code]
def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def serial(s):
    v = num(s)
    v = v.where((v >= 1) & (v <= 80000))
    return EP + pd.to_timedelta(v, unit='D')


def ymd(base, day_fill):
    y = num(X[base + '_Y']); m = num(X[base + '_M']); d = num(X[base + '_D'])
    if day_fill == 'last':
        last = pd.Series([calendar.monthrange(int(a), int(b))[1] if (a == a and b == b) else np.nan
                          for a, b in zip(y, m)], index=y.index)
        dd = d.fillna(last)
    else:
        dd = d.fillna(day_fill)
    return pd.to_datetime(dict(year=y, month=m, day=dd), errors='coerce')


def gmap(s, mapping):
    return s.astype(object).map(lambda x: mapping.get(x, np.nan) if isinstance(x, str) else np.nan)


TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}
INC = X.CINCLUSION.eq('Yes')
HEP = X.LE1HEPATECTYN_F1.eq('Yes')
PST_ANY = X.PATSTATC.notna()
DEATH = X.PATSTATC.eq('Deceased')
LAST_SER = serial(X.LASTNDTC)
LAST_FU = pd.concat([serial(X[f'LASTNDT_F{i}']) for i in range(1, 8)], axis=1).max(axis=1)
T_G = gmap(X.STADET, TMAP); N_G = gmap(X.STADEN, NMAP); M_G = gmap(X.STADEM, MMAP)
TNM = pd.concat([T_G, N_G, M_G], axis=1).notna().all(axis=1)
BIRTH = serial(X.BIRTHDT); DGK = serial(X.DGKCOLDT); DG = serial(X.LE1DGMETADT)
MALE = X.GENDER.map({'Male': 1.0, 'Female': 0.0})
SYNC = X.LE1METASYNCYN.map({'Yes': 1.0, 'No': 0.0})
METS = num(X.LE1NBMETAHEPNUM).where(lambda x: (x >= 1) & (x <= 50))
SIZE = num(X.LE1HEPMETASIZENUM).where(lambda x: (x > 0) & (x <= 300))
CEA = num(X.LE1PREHEPCEA_F1).where(lambda x: (x >= 0) & (x <= 40000))
DK_ANY_YES = pd.concat([X[f'DEATHKYN_F{i}'] for i in range(1, 8)], axis=1).eq('Yes').any(axis=1)
REC_FIELDS = ([f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
              + [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)] + [f'RECDT_F{i}' for i in range(1, 8)])
REC_FIRST = pd.concat([serial(X[c]) for c in REC_FIELDS], axis=1).min(axis=1)
CNT_REC = (pd.concat([num(X[f'LRNBREC_M{i}']) for i in range(1, 6)] + [num(X[f'EXHNBREC2_M{i}']) for i in range(1, 9)],
                     axis=1).fillna(0) > 0).any(axis=1)


def build_cohort(day_fill):
    """Report-consistent surgery-origin cohort (flow steps 1-7) for one partial-date convention."""
    op_ser = serial(X.LE1OPERDT_F1)
    op_ym = ymd('LE1OPERDT_F1', day_fill)
    op = op_ser.fillna(op_ym)
    s4 = INC & HEP & op_ym.notna()
    s5 = s4 & PST_ANY & LAST_SER.notna()
    s6 = s5 & (LAST_SER >= op)
    fu = (LAST_SER - op).dt.days
    s7 = s6 & ((fu > 0) | DEATH)
    flow = {'1 registry': len(X), '2 CINCLUSION=Yes': int(INC.sum()), '3 hepatectomy': int((INC & HEP).sum()),
            '4 operation date (year+month)': int(s4.sum()), '5 status and last-news': int(s5.sum()),
            '6 chronology': int(s6.sum()), '7 positive follow-up or death': int(s7.sum())}
    d = pd.DataFrame(index=X.index[s7])
    d['SRC'] = d.index
    d['T0'] = op[s7]
    d['PARTIAL'] = (op_ser[s7].isna() & op_ym[s7].notna())
    d['LAST'] = LAST_SER[s7]
    d['DEATH'] = DEATH[s7].astype(float)
    d['OS_DAYS'] = (d['LAST'] - d['T0']).dt.days
    d['DK_YES'] = DK_ANY_YES[s7]
    d['T_GRP'] = T_G[s7]; d['N_GRP'] = N_G[s7]; d['M_GRP'] = M_G[s7]
    d['TNM'] = d[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)
    d['AGE'] = (d['T0'] - BIRTH[s7]).dt.days / DAYS
    d.loc[(d.AGE < 18) | (d.AGE > 100), 'AGE'] = np.nan
    d['MALE'] = MALE[s7]; d['SYNC'] = SYNC[s7]; d['METS'] = METS[s7]; d['SIZE'] = SIZE[s7]; d['CEA'] = CEA[s7]
    d['DFI'] = (DG[s7] - DGK[s7]).dt.days / 30.4375
    d.loc[d.SYNC == 1, 'DFI'] = 0.0
    d.loc[(d.DFI < 0) | (DG[s7] > d['T0']), 'DFI'] = np.nan   # interval only if known at time zero
    d['ERA'] = np.where(d['T0'].dt.year <= 2009, 'train', 'valid')
    d['T3'] = (d.T_GRP == 'T3').astype(float).where(d.T_GRP.notna())
    d['T4'] = (d.T_GRP == 'T4').astype(float).where(d.T_GRP.notna())
    d['N1'] = (d.N_GRP == 'N1').astype(float).where(d.N_GRP.notna())
    d['N2'] = (d.N_GRP == 'N2').astype(float).where(d.N_GRP.notna())
    d['M1'] = (d.M_GRP == 'M1').astype(float).where(d.M_GRP.notna())
    d['LAST_FU'] = LAST_FU[s7]
    return d, flow


COHORTS, FLOWS = {}, {}
for label, day in [('first day (1st)', 1), ('mid-month (15th, primary)', 15), ('month-end', 'last')]:
    COHORTS[label], FLOWS[label] = build_cohort(day)
    log(f'{label}: step-7 cohort {len(COHORTS[label]):,}; TNM-complete {int(COHORTS[label].TNM.sum()):,}')
flow_tab = pd.DataFrame(FLOWS).T
flow_tab.loc['report (2026)'] = pd.Series({'1 registry': 29565, '2 CINCLUSION=Yes': 28979, '3 hepatectomy': 26677,
                                           '4 operation date (year+month)': 26592, '5 status and last-news': 26271,
                                           '6 chronology': 26186, '7 positive follow-up or death': 26094})
save(flow_tab.T.reset_index().rename(columns={'index': 'step'}), 'F01_flow_by_day_convention')
print(flow_tab.T.to_string())

SAME_DAY_TIME = {'half': 0.5, 'one': 1.0, 'quarter': 0.25, 'exclude_all': 0.5,
                 'exclude_unflagged': 0.5, 'censor_unflagged': 0.5}


def model_frame(D, same_day='half'):
    """TNM-complete modelling frame with covariates (training-era medians) and strata for one same-day rule."""
    F = D[D.TNM].copy()
    sd = (F.DEATH == 1) & (F.OS_DAYS <= 0)
    unflagged = sd & ~F.DK_YES
    if same_day == 'exclude_all':
        F = F[~sd]
    elif same_day == 'exclude_unflagged':
        F = F[~unflagged]
    F = F.copy()
    sd = (F.DEATH == 1) & (F.OS_DAYS <= 0)
    unflagged = sd & ~F.DK_YES
    event = F.DEATH.copy()
    if same_day == 'censor_unflagged':
        event[unflagged] = 0.0
    F['OS_Y_raw'] = np.where(sd, SAME_DAY_TIME[same_day], F.OS_DAYS) / DAYS
    F['OS_Y'] = np.minimum(F.OS_Y_raw, MAXFU)
    F['OS_E'] = np.where(F.OS_Y_raw > MAXFU, 0.0, event)
    train = F.ERA.eq('train')
    for col in ['DFI', 'METS', 'SIZE']:
        F[col + '_NR'] = F[col].isna().astype(float)
    for col in ['AGE', 'MALE', 'SYNC', 'DFI', 'METS', 'SIZE']:
        F[col + '_F'] = F[col].fillna(F.loc[train, col].median())
    F['AGE10_F'] = F.AGE_F / 10; F['DFI12_F'] = F.DFI_F / 12; F['SIZE10_F'] = F.SIZE_F / 10
    F['MALE_B'] = F.MALE_F.round().astype(int); F['SYNC_B'] = F.SYNC_F.round().astype(int)
    F['STRATUM'] = F.MALE_B * 2 + F.SYNC_B                      # sex x synchronous presentation
    F['STRAT_M'] = F.STRATUM * 2 + F.M1.astype(int)             # sex x synchronous x M-stage (M2a)
    F['CEA_LOG'] = np.log1p(F.CEA)
    return F.reset_index(drop=True)


PRIMARY = model_frame(COHORTS['mid-month (15th, primary)'], 'half')
trm = PRIMARY.ERA.eq('train').values
vam = ~trm
log(f'primary modelling cohort: {len(PRIMARY):,}; train {int(trm.sum()):,} (deaths {int(PRIMARY.OS_E[trm].sum()):,}); '
    f'validation {int(vam.sum()):,} (deaths {int(PRIMARY.OS_E[vam].sum()):,})')

CORE_M1 = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F', 'DFI_NR', 'METS_NR', 'SIZE_NR']
CORE_M2A = [c for c in CORE_M1 if c != 'M1']
PREOP_M1 = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'DFI_NR']
PREOP_M2A = ['T3', 'T4', 'N1', 'N2', 'AGE10_F', 'DFI12_F', 'DFI_NR']

# %% [markdown]
# ## 3. Survival models
#
# Cox models are stratified (sex x synchronous presentation; M2a adds M-stage to the strata). Baseline hazards are
# piecewise Breslow estimates from training patients only, so predicted survival is available at any horizon. The
# M2b variant allows a time-varying M-stage effect split at 2 years.

# %% [code]
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


def predict_S(bres, X_, st, be, bl, times):
    xe = X_ @ be; xl = X_ @ bl
    S = np.ones((len(X_), len(times)))
    for s in np.unique(st):
        m = st == s
        ev, He, Hl = bres[s]
        ii = np.searchsorted(ev, times, side='right') - 1
        Te = np.where(ii >= 0, He[np.clip(ii, 0, None)], 0.0)
        Tl = np.where(ii >= 0, Hl[np.clip(ii, 0, None)], 0.0)
        H = np.exp(xe[m, None]) * Te[None, :] + np.exp(xl[m, None]) * Tl[None, :]
        S[m] = np.exp(-H)
    return S


def fit_cox(F, cols, strat, tv=()):
    train = F.ERA.eq('train').values
    if not tv:
        cph = CoxPHFitter().fit(F.loc[train, cols + [strat, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[strat])
        be = cph.params_[cols].values; bl = be.copy(); cut = 1e9; ctv = None
    else:
        base = F.loc[train, ['OS_Y', 'OS_E', strat] + cols].reset_index(drop=True)
        base['ID_'] = np.arange(len(base))
        long = to_episodic_format(base.rename(columns={'OS_E': 'E'}), duration_col='OS_Y', event_col='E',
                                  id_col='ID_', time_gaps=CUT)
        for x in tv:
            long[x + '_late'] = long[x] * (long['start'] >= CUT).astype(float)
        feats = cols + [x + '_late' for x in tv]
        ctv = CoxTimeVaryingFitter().fit(long[['ID_', 'start', 'stop', 'E'] + feats + [strat]], id_col='ID_',
                                         event_col='E', start_col='start', stop_col='stop', strata=[strat])
        sm = ctv.summary
        be = np.array([sm.loc[x, 'coef'] for x in cols]); bl = be.copy()
        for x in tv:
            bl[cols.index(x)] = sm.loc[x, 'coef'] + sm.loc[x + '_late', 'coef']
        cut = CUT; cph = None
    X_ = F[cols].astype(float).values; st = F[strat].values
    bres = breslow(F.OS_Y.values[train], F.OS_E.values[train], X_[train] @ be, X_[train] @ bl, st[train], cut)
    S = predict_S(bres, X_, st, be, bl, TIMES)
    return {'cols': cols, 'strat': strat, 'cph': cph, 'ctv': ctv, 'be': be, 'bl': bl, 'cut': cut,
            'S': S, 'train': train}


def valid_C(F, risk, mask=None):
    m = vam if mask is None else mask
    return round(float(concordance_index(F.OS_Y.values[m], -risk[m], F.OS_E.values[m])), 4)


def performance(name, fit, F):
    S = fit['S']
    tr, va = F.ERA.eq('train').values, F.ERA.eq('valid').values
    Ttr, Etr = F.OS_Y.values[tr], F.OS_E.values[tr]
    Tva, Eva = F.OS_Y.values[va], F.OS_E.values[va]
    H5 = -np.log(np.clip(S[:, 1], 1e-12, 1))
    out = {'model': name, 'train_C': round(float(concordance_index(Ttr, -H5[tr], Etr)), 4),
           'valid_C': round(float(concordance_index(Tva, -H5[va], Eva)), 4)}
    C_bs = []
    for _ in range(300):
        b = RNG.integers(0, int(va.sum()), int(va.sum()))
        C_bs.append(concordance_index(Tva[b], -H5[va][b], Eva[b]))
    lo, hi = np.percentile(C_bs, [2.5, 97.5])
    out['valid_C_95CI'] = f'{lo:.3f}-{hi:.3f}'
    y_tr = Surv.from_arrays(Etr.astype(bool), Ttr); y_va = Surv.from_arrays(Eva.astype(bool), Tva)
    auc, _ = cumulative_dynamic_auc(y_tr, y_va, H5[va], np.array([1.0, 3.0, 5.0]))
    for t, a in zip([1, 3, 5], auc):
        out[f'tAUC_{t}y'] = round(float(a), 3)
    _, bs = brier_score(y_tr, y_va, S[va][:, 2:], TB)
    for t in [1.0, 3.0, 5.0]:
        out[f'Brier_{int(t)}y'] = round(float(bs[list(TB).index(t)]), 4)
    out['IBS_1_7y'] = round(float(integrated_brier_score(y_tr, y_va, S[va][:, 2:], TB)), 4)
    o5 = float(KaplanMeierFitter().fit(Tva, Eva).survival_function_at_times(5).iloc[0])
    out['valid_observed_S5'] = round(o5, 3)
    out['valid_mean_predicted_S5'] = round(float(S[va, 1].mean()), 3)
    out['valid_OE_5y'] = round(o5 / float(S[va, 1].mean()), 3)
    lp = np.log(-np.log(np.clip(S[va, 1], 1e-6, 1 - 1e-6)))
    slope = CoxPHFitter().fit(pd.DataFrame({'T': Tva, 'E': Eva, 'lp': lp}), 'T', 'E').params_['lp']
    out['valid_calib_slope_5y'] = round(float(slope), 3)
    return out


def ph_table(fit, F):
    d = F.loc[fit['train'], fit['cols'] + [fit['strat'], 'OS_Y', 'OS_E']]
    res = proportional_hazard_test(fit['cph'], d, time_transform='rank').summary.reset_index()
    res.columns = ['term'] + list(res.columns[1:])
    return res


# ---- M-stage candidates on identical patients (training-only PH tests drive the selection)
log('fitting M-stage candidates')
FIT = {'M1': fit_cox(PRIMARY, CORE_M1, 'STRATUM'),
       'M2a': fit_cox(PRIMARY, CORE_M2A, 'STRAT_M'),
       'M2b': fit_cox(PRIMARY, CORE_M1, 'STRATUM', tv=('M1',))}
perf = pd.DataFrame([performance('M1 stratified sex x synchronous (M-stage covariate)', FIT['M1'], PRIMARY),
                     performance('M2a stratified sex x synchronous x M-stage', FIT['M2a'], PRIMARY),
                     performance('M2b stratified sex x synchronous, time-varying M-stage (2-year split)', FIT['M2b'], PRIMARY)])
save(perf, 'F02_M_stage_candidates_identical_patients')
print(perf.to_string(index=False))

ph_all = pd.concat([ph_table(FIT['M1'], PRIMARY).assign(model='M1'), ph_table(FIT['M2a'], PRIMARY).assign(model='M2a')])
save(ph_all.round(4), 'F03_PH_tests_training_constant_terms')
print(ph_all.round(4).to_string(index=False))
ctv = FIT['M2b']['ctv'].summary
tv_tab = pd.DataFrame([{'model': 'M2b', 'term': 'M1 early coef', 'coef': round(float(ctv.loc['M1', 'coef']), 4),
                        'HR_early': round(float(np.exp(ctv.loc['M1', 'coef'])), 3)},
                       {'model': 'M2b', 'term': 'M1 change after 2 years', 'coef': round(float(ctv.loc['M1_late', 'coef']), 4),
                        'p_time_variation': float(ctv.loc['M1_late', 'p'])},
                       {'model': 'M2b', 'term': 'M1 late HR', 'coef': round(float(FIT['M2b']['bl'][CORE_M1.index('M1')]), 4),
                        'HR_late': round(float(np.exp(FIT['M2b']['bl'][CORE_M1.index('M1')])), 3)}])
save(tv_tab, 'F04_M2b_time_varying_M_stage')
print(tv_tab.to_string(index=False))

ok_m1 = bool((ph_table(FIT['M1'], PRIMARY).p > 0.05).all())
ok_m2a = bool((ph_table(FIT['M2a'], PRIMARY).p > 0.05).all())
SELECTED = 'M1' if ok_m1 else ('M2a' if ok_m2a else 'M2b')
sel_rule = pd.DataFrame([{'candidate': 'M1', 'all_constant_PH_p_gt_0.05_training': ok_m1},
                         {'candidate': 'M2a', 'all_constant_PH_p_gt_0.05_training': ok_m2a},
                         {'candidate': 'M2b', 'all_constant_PH_p_gt_0.05_training': 'M-stage time-varying (see F04)'},
                         {'candidate': 'SELECTED (first passing, simplest first)', 'all_constant_PH_p_gt_0.05_training': SELECTED}])
save(sel_rule, 'F05_model_selection_rule')
print(sel_rule.to_string(index=False))
SEL = FIT[SELECTED]
SEL_COLS = CORE_M2A if SELECTED == 'M2a' else CORE_M1
SEL_STRAT = 'STRAT_M' if SELECTED == 'M2a' else 'STRATUM'
log(f'selected model: {SELECTED}')

# %% [markdown]
# ## 4. Three prognostic groups
#
# Groups are defined by the selected model's predicted 5-year overall survival. Cut-points are the tertiles in
# **training** patients only and are then applied unchanged to validation patients.

# %% [code]
def phenotype_groups(fit, F):
    S5 = fit['S'][:, 1]
    tr = fit['train']
    q33, q67 = np.quantile(S5[tr], [1 / 3, 2 / 3])
    G = np.where(S5 >= q67, 'Favourable', np.where(S5 >= q33, 'Intermediate', 'Adverse'))
    return G, S5, q33, q67


GRP, S5_SEL, Q33, Q67 = phenotype_groups(SEL, PRIMARY)
PRIMARY['PHENO'] = GRP
PRIMARY['S5_SEL'] = S5_SEL
rows_ph, rows_def = [], []
for lab in ['Favourable', 'Intermediate', 'Adverse']:
    mt = trm & (GRP == lab); mv = vam & (GRP == lab)
    kt = KaplanMeierFitter().fit(PRIMARY.OS_Y.values[mt], PRIMARY.OS_E.values[mt])
    kv = KaplanMeierFitter().fit(PRIMARY.OS_Y.values[mv], PRIMARY.OS_E.values[mv])
    med = kv.median_survival_time_
    ci = median_survival_times(kv.confidence_interval_).iloc[0]
    rows_ph.append({'phenotype': lab, 'train_n': int(mt.sum()), 'valid_n': int(mv.sum()),
                    'valid_deaths': int(PRIMARY.OS_E.values[mv].sum()),
                    'valid_median_OS': round(float(med), 2) if np.isfinite(med) else None,
                    'valid_median_95CI': f'{ci.iloc[0]:.2f}-{ci.iloc[1]:.2f}' if np.isfinite(ci.iloc[1]) else f'{ci.iloc[0]:.2f}-NE',
                    'valid_S5_KM': round(float(kv.survival_function_at_times(5).iloc[0]), 3),
                    'train_median_OS': round(float(kt.median_survival_time_), 2) if np.isfinite(kt.median_survival_time_) else None,
                    'train_S5_KM': round(float(kt.survival_function_at_times(5).iloc[0]), 3),
                    'train_mean_predicted_S5': round(float(S5_SEL[mt].mean()), 3),
                    'valid_mean_predicted_S5': round(float(S5_SEL[mv].mean()), 3)})
rows_def = [{'phenotype': 'Favourable', 'definition': f'predicted 5-year OS >= {Q67:.4f}'},
            {'phenotype': 'Intermediate', 'definition': f'{Q33:.4f} <= predicted 5-year OS < {Q67:.4f}'},
            {'phenotype': 'Adverse', 'definition': f'predicted 5-year OS < {Q33:.4f}'}]
save(pd.DataFrame(rows_ph), 'F06_phenotypes_counts_survival_calibration')
save(pd.DataFrame(rows_def), 'F07_phenotype_definitions')
print(pd.DataFrame(rows_def).to_string(index=False)); print(pd.DataFrame(rows_ph).to_string(index=False))

lr_v = multivariate_logrank_test(PRIMARY.OS_Y.values[vam], GRP[vam], PRIMARY.OS_E.values[vam])
lr_t = multivariate_logrank_test(PRIMARY.OS_Y.values[trm], GRP[trm], PRIMARY.OS_E.values[trm])
rank = np.array([{'Favourable': 2, 'Intermediate': 1, 'Adverse': 0}[g] for g in GRP], float)
sep = {'valid_logrank_p': float(lr_v.p_value), 'train_logrank_p': float(lr_t.p_value),
       'valid_C_ordinal': round(float(concordance_index(PRIMARY.OS_Y.values[vam], rank[vam], PRIMARY.OS_E.values[vam])), 4)}
save(pd.Series(sep).rename('value').rename_axis('quantity').reset_index(), 'F08_phenotype_separation')
print(sep)

# bootstrap stability of the phenotype assignment (refit and recut on training bootstrap samples)
kappas = []
tr_idx = np.where(trm)[0]
for _ in range(100):
    pick = RNG.choice(tr_idx, len(tr_idx), replace=True)
    b = PRIMARY.iloc[pick]
    try:
        if SELECTED == 'M2a':
            cb = CoxPHFitter().fit(b[CORE_M2A + ['STRAT_M', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRAT_M'])
            be_b = cb.params_[CORE_M2A].values; bl_b = be_b; cols_b = CORE_M2A; st_col = 'STRAT_M'; cut_b = 1e9
        else:
            cb = CoxPHFitter().fit(b[CORE_M1 + ['STRATUM', 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=['STRATUM'])
            be_b = cb.params_[CORE_M1].values; bl_b = be_b; cols_b = CORE_M1; st_col = 'STRATUM'; cut_b = 1e9
    except Exception:  # noqa: BLE001
        continue
    Xall = PRIMARY[cols_b].astype(float).values; stv = PRIMARY[st_col].values
    bres_b = breslow(PRIMARY.OS_Y.values[pick], PRIMARY.OS_E.values[pick], Xall[pick] @ be_b, Xall[pick] @ bl_b, stv[pick], cut_b)
    S5b = predict_S(bres_b, Xall, stv, be_b, bl_b, np.array([5.0]))[:, 0]
    a1, a2 = np.quantile(S5b[trm], [1 / 3, 2 / 3])
    gb = np.where(S5b >= a2, 'Favourable', np.where(S5b >= a1, 'Intermediate', 'Adverse'))
    kappas.append(cohen_kappa_score(GRP[vam], gb[vam]))
save(pd.DataFrame([{'selected_model': SELECTED, 'bootstrap_resamples': len(kappas),
                    'kappa_median': round(float(np.median(kappas)), 3),
                    'kappa_2.5pct': round(float(np.percentile(kappas, 2.5)), 3),
                    'kappa_97.5pct': round(float(np.percentile(kappas, 97.5)), 3)}]), 'F09_phenotype_bootstrap_stability')

head = {'selected_model': SELECTED, 'phenotype_cut_S5_q33': round(float(Q33), 4), 'phenotype_cut_S5_q67': round(float(Q67), 4),
        'primary_cohort_TNM_complete': len(PRIMARY), 'primary_train_n': int(trm.sum()), 'primary_valid_n': int(vam.sum())}
save(pd.Series(head).rename('value').rename_axis('quantity').reset_index(), 'F00_headline')
print(head)

# %% [markdown]
# ## 5. Verification of the same-day deaths
#
# A same-day death is a patient whose operation date equals the last-news date with status *Deceased*. These carry a
# half-day time convention. Because the death flag (`DEATHKYN_F`) is the only explicit death confirmation, the table
# below tests whether these deaths are supported by other fields, and whether lack of a death flag is specific to them.

# %% [code]
D15 = COHORTS['mid-month (15th, primary)']
sd_all = D15[(D15.DEATH == 1) & (D15.OS_DAYS <= 0)].copy()
sd_all['FORMS_WITH_LASTNEWS'] = pd.concat([serial(X.loc[sd_all.index, f'LASTNDT_F{i}']).notna() for i in range(1, 8)],
                                          axis=1).sum(axis=1)
sd_all['PATSTAT_F1_DECEASED'] = X.loc[sd_all.index, 'PATSTAT_F1'].eq('Deceased')
sd_all['DEATHKYN_RAW'] = X.loc[sd_all.index, 'DEATHKYN_F1'].fillna('blank')
sd_all['IN_MODEL_COHORT'] = sd_all.TNM
sd_all['GROUP'] = np.where(sd_all.DK_YES, 'death flag = Yes', 'death flag absent (No / ND)')
verif = (sd_all.groupby('GROUP')
         .agg(n=('SRC', 'size'), in_model_cohort=('IN_MODEL_COHORT', 'sum'),
              operation_date_complete=('PARTIAL', lambda s: int((~s).sum())),
              forms_with_last_news_median=('FORMS_WITH_LASTNEWS', 'median'),
              patstat_F1_deceased=('PATSTAT_F1_DECEASED', 'sum'))
         .reset_index())
save(verif, 'F18_same_day_deaths_verification')
print(verif.to_string(index=False))
print(sd_all.DEATHKYN_RAW.value_counts().to_string())

# is a missing death flag specific to same-day deaths? death-flag rate by time from operation (modelling cohort)
dec = PRIMARY[PRIMARY.DEATH == 1].copy()
bands = pd.cut(dec.OS_DAYS, [-1, 0, 30, 365, 1826, 1e6], labels=['same day', '1-30 days', '31-365 days', '1-5 years', '>5 years'])
flag_rate = (dec.groupby(bands, observed=False).agg(n=('DK_YES', 'size'), flag_yes=('DK_YES', 'sum')).reset_index())
flag_rate['flag_yes_pct'] = (100 * flag_rate.flag_yes / flag_rate.n).round(1)
flag_rate = flag_rate.rename(columns={'OS_DAYS': 'time_from_operation'})
save(flag_rate, 'F18b_death_flag_rate_by_time_from_operation')
print(flag_rate.to_string(index=False))

# %% [markdown]
# ## 6. Sensitivity analyses: partial dates, same-day deaths, and handling of unflagged same-day deaths
#
# Each variant rebuilds the cohort and refits the selected specification. Phenotype agreement is computed on the same
# patients as the primary analysis.

# %% [code]
def run_variant(day, same_day):
    D_ = COHORTS[{1: 'first day (1st)', 15: 'mid-month (15th, primary)', 'last': 'month-end'}[day]]
    F = model_frame(D_, same_day)
    fit = fit_cox(F, SEL_COLS, SEL_STRAT)
    G, S5, a, b = phenotype_groups(fit, F)
    va = F.ERA.eq('valid').values
    H5 = -np.log(np.clip(fit['S'][:, 1], 1e-12, 1))
    return {'F': F, 'G': G, 'C': valid_C(F, H5, va), 'cut33': a, 'cut67': b,
            'train_n': int(fit['train'].sum()), 'valid_n': int(va.sum())}


def agreement(F_v, G_v, F_p=PRIMARY, G_p=GRP):
    common = np.intersect1d(F_v.SRC.values, F_p.SRC.values)
    a = pd.Series(G_v, index=F_v.SRC.values).loc[common].values
    b = pd.Series(G_p, index=F_p.SRC.values).loc[common].values
    return len(common), round(100 * float((a == b).mean()), 2), round(float(cohen_kappa_score(a, b)), 3)


conv_rows = []
for label, day in [('first day (1st)', 1), ('mid-month (15th, primary)', 15), ('month-end', 'last')]:
    for sd in ['half', 'one', 'quarter', 'exclude_all']:
        r = run_variant(day, sd)
        n_common, pct, kap = agreement(r['F'], r['G'])
        conv_rows.append({'day_convention': label, 'same_day_rule': sd, 'modelling_cohort_TNM': len(r['F']),
                          'train_n': r['train_n'], 'valid_n': r['valid_n'], 'valid_C': r['C'],
                          'cut_S5_q33': round(float(r['cut33']), 4), 'cut_S5_q67': round(float(r['cut67']), 4),
                          'patients_in_common_with_primary': n_common,
                          'phenotype_identical_pct_vs_primary': pct, 'kappa_vs_primary': kap})
save(pd.DataFrame(conv_rows), 'F10_day_and_same_day_conventions')
print(pd.DataFrame(conv_rows).to_string(index=False))

unflag_rows = []
for sd, lab in [('half', 'primary: half-day, all same-day deaths kept'),
                ('exclude_unflagged', 'exclude same-day deaths without death flag'),
                ('censor_unflagged', 'same-day deaths without flag treated as censored at half-day')]:
    r = run_variant(15, sd)
    n_common, pct, kap = agreement(r['F'], r['G'])
    unflag_rows.append({'analysis': lab, 'modelling_cohort_TNM': len(r['F']),
                        'same_day_deaths_in_cohort': int(((r['F'].DEATH == 1) & (r['F'].OS_DAYS <= 0)).sum()),
                        'valid_C': r['C'], 'cut_S5_q33': round(float(r['cut33']), 4), 'cut_S5_q67': round(float(r['cut67']), 4),
                        'phenotype_identical_pct_vs_primary': pct, 'kappa_vs_primary': kap})
save(pd.DataFrame(unflag_rows), 'F19_unflagged_same_day_deaths_sensitivity')
print(pd.DataFrame(unflag_rows).to_string(index=False))

# %% [markdown]
# ## 7. Undated recurrences, death verification and CEA sensitivity

# %% [code]
PRIMARY['REC_FIRST'] = REC_FIRST.loc[PRIMARY.SRC].values
PRIMARY['CNT_REC'] = CNT_REC.loc[PRIMARY.SRC].values
rec_days_raw = PRIMARY.REC_FIRST
rec_after = (~rec_days_raw.isna()) & (rec_days_raw >= PRIMARY.T0) & (rec_days_raw <= PRIMARY['LAST'])
rec_before = (~rec_days_raw.isna()) & (rec_days_raw < PRIMARY.T0)
undated = (~rec_after) & (~rec_before) & PRIMARY.CNT_REC
PRIMARY['UNDATED'] = undated; PRIMARY['REC_AFTER'] = rec_after; PRIMARY['REC_BEFORE'] = rec_before
ic_rows = []
for lab, mask in [('undated recurrence (count > 0, no date)', undated), ('dated recurrence after operation', rec_after),
                  ('neither', ~undated & ~rec_after)]:
    s_ = PRIMARY[mask & ~rec_before]
    kk = KaplanMeierFitter().fit(s_.OS_Y, s_.OS_E)
    ic_rows.append({'group': lab, 'n': len(s_), 'median_age': round(float(s_.AGE.median()), 1),
                    'T4_pct': round(100 * float((s_.T_GRP == 'T4').mean()), 1),
                    'N2_pct': round(100 * float((s_.N_GRP == 'N2').mean()), 1),
                    'M1_pct': round(100 * float((s_.M_GRP == 'M1').mean()), 1),
                    'median_size_mm': round(float(s_.SIZE.median()), 1),
                    'median_follow_up_years': round(float(s_.OS_Y.median()), 2),
                    'OS_median_years': round(float(kk.median_survival_time_), 2) if np.isfinite(kk.median_survival_time_) else None,
                    'deaths_pct': round(100 * float(s_.OS_E.mean()), 1),
                    'mean_predicted_5y_survival': round(float(s_.S5_SEL.mean()), 3)})
save(pd.DataFrame(ic_rows), 'F11_undated_recurrence_informative_censoring_check')
print(pd.DataFrame(ic_rows).to_string(index=False))

dk_yes_all = DK_ANY_YES
cons = {
    'deceased (PATSTATC)': int(DEATH.sum()),
    'deceased with any DEATHKYN_F = Yes': int((DEATH & dk_yes_all).sum()),
    'deceased without any DEATHKYN_F = Yes': int((DEATH & ~dk_yes_all).sum()),
    'alive/lost but DEATHKYN_F = Yes': int(((~DEATH) & PST_ANY & dk_yes_all).sum()),
    'LASTNDTC earlier than latest follow-up date': int((LAST_SER < LAST_FU)[LAST_SER.notna() & LAST_FU.notna()].sum()),
    'LASTNDTC later than latest follow-up date': int((LAST_SER > LAST_FU)[LAST_SER.notna() & LAST_FU.notna()].sum()),
    'modelling cohort with last contact before time zero': int((PRIMARY.OS_DAYS < 0).sum()),
    'modelling deaths after censoring date 2020-07-04': int((PRIMARY['LAST'] > CENSOR).sum()),
    'modelling deaths with event time > 15 years (censored)': int((PRIMARY.OS_Y_raw > MAXFU).sum()),
}
save(pd.Series(cons).rename('n').rename_axis('check').reset_index(), 'F12_death_and_last_contact_verification')
print(pd.Series(cons).to_string())

# CEA sensitivity on the selected model (complete case and multiple imputation)
cc = PRIMARY[PRIMARY.CEA.notna()].copy().reset_index(drop=True)
cc_tr = cc.ERA.eq('train').values; cc_va = ~cc_tr
cph_b = CoxPHFitter().fit(cc.loc[cc_tr, SEL_COLS + [SEL_STRAT, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[SEL_STRAT])
cph_c = CoxPHFitter().fit(cc.loc[cc_tr, SEL_COLS + ['CEA_LOG', SEL_STRAT, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[SEL_STRAT])
lp_b = cc[SEL_COLS].astype(float).values @ cph_b.params_[SEL_COLS].values
lp_c = cc[SEL_COLS + ['CEA_LOG']].astype(float).values @ cph_c.params_[SEL_COLS + ['CEA_LOG']].values
cea_rows = [{'analysis': 'complete case', 'train_n': int(cc_tr.sum()), 'valid_n': int(cc_va.sum()),
             'valid_deaths': int(cc.OS_E.values[cc_va].sum()),
             'CEA_HR_per_log_unit': round(float(np.exp(cph_c.params_['CEA_LOG'])), 3),
             'CEA_HR_95CI': f"{cph_c.summary.loc['CEA_LOG', 'exp(coef) lower 95%']:.3f}-{cph_c.summary.loc['CEA_LOG', 'exp(coef) upper 95%']:.3f}",
             'valid_C_without_CEA': valid_C(cc, lp_b, cc_va),
             'valid_C_with_CEA': valid_C(cc, lp_c, cc_va)}]
na_fit = NelsonAalenFitter().fit(PRIMARY.OS_Y.values[trm], PRIMARY.OS_E.values[trm])
H_na = np.interp(PRIMARY.OS_Y.values, na_fit.cumulative_hazard_.index.values, na_fit.cumulative_hazard_.iloc[:, 0].values)
pred_cols = ['T3', 'T4', 'N1', 'N2', 'M1', 'AGE10_F', 'DFI12_F', 'METS_F', 'SIZE10_F']
Xp = PRIMARY[pred_cols].astype(float).values
dev = np.column_stack([Xp, PRIMARY.CEA_LOG.values, H_na, PRIMARY.OS_E.values])
coefs, varis, hrs, lp_v = [], [], [], []
for draw in range(10):
    imp = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw).fit(dev[trm])
    cea_dev = imp.transform(dev)[:, len(pred_cols)]
    dd = PRIMARY[SEL_COLS + [SEL_STRAT, 'OS_Y', 'OS_E']].copy(); dd['CEA_IMP'] = cea_dev
    cm = CoxPHFitter().fit(dd.loc[trm, SEL_COLS + ['CEA_IMP', SEL_STRAT, 'OS_Y', 'OS_E']], 'OS_Y', 'OS_E', strata=[SEL_STRAT])
    coefs.append(cm.params_['CEA_IMP']); varis.append(cm.standard_errors_['CEA_IMP'] ** 2)
    hrs.append(float(np.exp(cm.params_['CEA_IMP'])))
    impv = IterativeImputer(max_iter=10, sample_posterior=True, random_state=SEED + draw).fit(np.column_stack([Xp, PRIMARY.CEA_LOG.values])[trm])
    cea_val = impv.transform(np.column_stack([Xp, PRIMARY.CEA_LOG.values]))[:, len(pred_cols)]
    dv = PRIMARY[SEL_COLS].copy(); dv['CEA_IMP'] = cea_val
    lp_v.append(cm.predict_log_partial_hazard(dv[SEL_COLS + ['CEA_IMP']]).values.ravel())
bar = float(np.mean(coefs)); Wv = float(np.mean(varis)); Bv = float(np.var(coefs, ddof=1))
se = np.sqrt(Wv + 1.1 * Bv)
lp_avg = np.mean(lp_v, axis=0)
cea_rows.append({'analysis': 'multiple imputation, 10 draws (development outcome-compatible; validation predictors only)',
                 'train_n': int(trm.sum()), 'valid_n': int(vam.sum()), 'valid_deaths': int(PRIMARY.OS_E.values[vam].sum()),
                 'CEA_HR_per_log_unit': round(float(np.exp(bar)), 3),
                 'CEA_HR_95CI': f'{np.exp(bar - 1.96 * se):.3f}-{np.exp(bar + 1.96 * se):.3f}',
                 'valid_C_without_CEA': valid_C(PRIMARY, PRIMARY[SEL_COLS].astype(float).values @ SEL['be'], vam),
                 'valid_C_with_CEA': valid_C(PRIMARY, lp_avg, vam),
                 'draw_HR_range': f'{min(hrs):.3f}-{max(hrs):.3f}'})
save(pd.DataFrame(cea_rows), 'F13_CEA_sensitivity_final')
print(pd.DataFrame(cea_rows).to_string(index=False))

# %% [markdown]
# ## 8. Pre-operative-only sensitivity model
#
# Two versions are reported. **F14/F15** keep the M1 structure used in the earlier report. **F23** uses the selected
# M2a structure (M-stage in the strata) without metastasis count or size, which is the like-for-like comparison with the
# selected model.

# %% [code]
pre_m1 = fit_cox(PRIMARY, PREOP_M1, 'STRATUM')
pre_m2a = fit_cox(PRIMARY, PREOP_M2A, 'STRAT_M')
pre_perf = pd.DataFrame([performance('pre-operative-only, M1 structure (no count or size)', pre_m1, PRIMARY),
                         performance('pre-operative-only, selected M2a structure (no count or size)', pre_m2a, PRIMARY)])
save(pre_perf.iloc[[0]], 'F14_preoperative_only_sensitivity')
save(pre_perf.iloc[[1]].assign(note='like-for-like with selected model'), 'F23_preoperative_only_selected_structure')
print(pre_perf.to_string(index=False))

agree_rows = []
for lab, fit_ in [('M1 structure', pre_m1), ('selected M2a structure', pre_m2a)]:
    G_pre, S5_pre, pq1, pq2 = phenotype_groups(fit_, PRIMARY)
    agree_rows.append({'pre_op_structure': lab,
                       'validation_kappa_vs_primary': round(float(cohen_kappa_score(GRP[vam], G_pre[vam])), 3),
                       'share_same_group_pct_all_patients': round(100 * float((GRP == G_pre).mean()), 1),
                       'share_same_group_pct_validation': round(100 * float((GRP[vam] == G_pre[vam]).mean()), 1)})
save(pd.DataFrame(agree_rows), 'F15_preoperative_only_phenotype_agreement')
print(pd.DataFrame(agree_rows).to_string(index=False))

# %% [markdown]
# ## 9. Calibration
#
# Calibration is assessed by observed (Kaplan-Meier) against mean predicted 5-year survival. Validation groups are
# formed on predicted risk and by operation period, which shows whether any miscalibration is temporal. A sensitivity
# analysis re-estimates only the baseline hazard from the most recent training years (2005-2009); coefficients and
# cut-points are re-derived from that window and used nowhere else.

# %% [code]
def km_s5(T, E):
    if len(T) == 0:
        return np.nan, 0
    k = KaplanMeierFitter().fit(T, E)
    return float(k.survival_function_at_times(5).iloc[0]), int((T >= 5).sum())


S5v = SEL["S"][:, 1]
va_idx = np.where(vam)[0]
dec_q = pd.qcut(S5v[vam], 10, labels=False, duplicates='drop')
rows_dec = []
for g in sorted(np.unique(dec_q)):
    ii = va_idx[dec_q == g]
    obs, n5 = km_s5(PRIMARY.OS_Y.values[ii], PRIMARY.OS_E.values[ii])
    rows_dec.append({'validation_decile': int(g) + 1, 'n': len(ii), 'deaths': int(PRIMARY.OS_E.values[ii].sum()),
                     'mean_predicted_5y': round(float(S5v[ii].mean()), 3), 'observed_5y_KM': round(obs, 3),
                     'observed_minus_predicted': round(obs - float(S5v[ii].mean()), 3),
                     'at_risk_5y': n5})
save(pd.DataFrame(rows_dec), 'F20_calibration_by_validation_decile')
print(pd.DataFrame(rows_dec).to_string(index=False))

era_bins = [(1990, 2004, 'operation 1990-2004'), (2005, 2009, 'operation 2005-2009 (training)'),
            (2010, 2012, 'operation 2010-2012 (validation)'), (2013, 2015, 'operation 2013-2015 (validation)'),
            (2016, 2030, 'operation 2016+ (validation)')]
rows_era = []
yr = PRIMARY.T0.dt.year.values
for lo, hi, lab in era_bins:
    ii = np.where((yr >= lo) & (yr <= hi))[0]
    if len(ii) == 0:
        continue
    obs, n5 = km_s5(PRIMARY.OS_Y.values[ii], PRIMARY.OS_E.values[ii])
    pred = float(S5v[ii].mean())
    rows_era.append({'period': lab, 'n': len(ii), 'mean_predicted_5y': round(pred, 3),
                     'observed_5y_KM': round(obs, 3), 'O_over_E': round(obs / pred, 3),
                     'patients_with_5y_follow_up': n5})
save(pd.DataFrame(rows_era), 'F21_calibration_by_operation_period')
print(pd.DataFrame(rows_era).to_string(index=False))

# recalibration sensitivity: baseline from the most recent training years only; coefficients unchanged
recent = trm & (PRIMARY.T0.dt.year.values >= 2005)
X_sel = PRIMARY[SEL_COLS].astype(float).values
st_sel = PRIMARY[SEL_STRAT].values
bres_recent = breslow(PRIMARY.OS_Y.values[recent], PRIMARY.OS_E.values[recent], X_sel[recent] @ SEL['be'],
                      X_sel[recent] @ SEL['bl'], st_sel[recent], SEL['cut'])
S_recent = predict_S(bres_recent, X_sel, st_sel, SEL['be'], SEL['bl'], TIMES)
G_rec, S5_rec, rq1, rq2 = phenotype_groups({'S': S_recent, 'train': recent}, PRIMARY)
o5_base = km_s5(PRIMARY.OS_Y.values[vam], PRIMARY.OS_E.values[vam])[0]
rec_rows = []
for lab, S5_ in [('primary (baseline from all training years)', S5v), ('recent-baseline sensitivity (2005-2009)', S_recent[:, 1])]:
    pred = float(S5_[vam].mean())
    rec_rows.append({'analysis': lab, 'valid_mean_predicted_5y': round(pred, 3),
                     'valid_observed_5y_KM': round(o5_base, 3), 'valid_O_over_E': round(o5_base / pred, 3),
                     'valid_C': valid_C(PRIMARY, -np.log(np.clip(S5_, 1e-12, 1)))})
rec_rows.append({'analysis': 'phenotype agreement of recent-baseline groups with primary',
                 'valid_mean_predicted_5y': None, 'valid_observed_5y_KM': None, 'valid_O_over_E': None,
                 'valid_C': None,
                 'agreement_validation_kappa': round(float(cohen_kappa_score(GRP[vam], G_rec[vam])), 3),
                 'agreement_pct_validation': round(100 * float((GRP[vam] == G_rec[vam]).mean()), 2)})
save(pd.DataFrame(rec_rows), 'F22_recalibration_sensitivity')
print(pd.DataFrame(rec_rows).to_string(index=False))

# %% [markdown]
# ## 10. Model performance, clinical benchmarks and RFS

# %% [code]
perf_final = performance('selected model', SEL, PRIMARY)
save(pd.DataFrame([perf_final]), 'F02b_selected_model_performance')
print(pd.DataFrame([perf_final]).to_string(index=False))

fong = (PRIMARY.N_GRP.isin(['N1', 'N2']).astype(float) + (PRIMARY.DFI < 12).astype(float)
        + (PRIMARY.METS > 1).astype(float) + (PRIMARY.SIZE > 50).astype(float) + (PRIMARY.CEA > 200).astype(float))
fong = fong.where(PRIMARY.N_GRP.notna() & PRIMARY.DFI.notna() & PRIMARY.METS.notna() & PRIMARY.SIZE.notna() & PRIMARY.CEA.notna())
nord = ((PRIMARY.AGE >= 60).astype(float) + (PRIMARY.T_GRP == 'T4').astype(float)
        + PRIMARY.N_GRP.isin(['N1', 'N2']).astype(float) + (PRIMARY.DFI < 12).astype(float))
nord = nord.where(PRIMARY.AGE.notna() & PRIMARY.T_GRP.notna() & PRIMARY.N_GRP.notna() & PRIMARY.DFI.notna())
H5 = -np.log(np.clip(SEL['S'][:, 1], 1e-12, 1))
subsets = [('All TNM-complete validation', vam), ('Fong CRS subset (CEA recorded)', vam & fong.notna().values),
           ('Nordlinger-type subset', vam & nord.notna().values)]
rows_sub = []
for lab, mv in subsets:
    row = {'subset': lab, 'valid_n': int(mv.sum()), 'valid_deaths': int(PRIMARY.OS_E.values[mv].sum()),
           'selected_model_C': valid_C(PRIMARY, H5, mv)}
    if 'Fong' in lab:
        row['Fong_CRS_C'] = valid_C(PRIMARY, fong.fillna(0).values, mv)
    if 'Nordlinger' in lab:
        row['Nordlinger_C'] = valid_C(PRIMARY, nord.fillna(0).values, mv)
    o5 = float(KaplanMeierFitter().fit(PRIMARY.OS_Y.values[mv], PRIMARY.OS_E.values[mv]).survival_function_at_times(5).iloc[0])
    row['mean_predicted_S5'] = round(float(SEL['S'][mv, 1].mean()), 3)
    row['observed_S5_KM'] = round(o5, 3)
    row['OE_5y'] = round(o5 / float(SEL['S'][mv, 1].mean()), 3)
    rows_sub.append(row)
save(pd.DataFrame(rows_sub), 'F16_identical_subset_comparison_calibration')
print(pd.DataFrame(rows_sub).to_string(index=False))

# RFS (secondary): dated recurrence or death; undated recurrences handled by the alternatives below
rec_ser = PRIMARY.REC_FIRST
rec_days = (rec_ser - PRIMARY.T0).dt.days.values.astype(float)
last_days = (PRIMARY['LAST'] - PRIMARY.T0).dt.days.values.astype(float)
rT = np.clip(np.minimum(np.where(rec_after.values, rec_days, last_days) / DAYS, MAXFU), 1 / DAYS, None)
elig = ~rec_before.values
und = undated.values; rafter = rec_after.values; dead = PRIMARY.OS_E.values.astype(bool)
rfs_specs = [
    ('PRIMARY: dated recurrence and death events; undated censored', rT, np.where(rafter | dead, 1.0, 0.0), elig),
    ('undated recurrences events at last contact', rT, np.where(rafter | dead | und, 1.0, 0.0), elig),
    ('undated recurrences events at mid-interval',
     np.where(und & ~rafter, last_days / DAYS / 2, rT), np.where(rafter | dead | und, 1.0, 0.0), elig),
    ('undated recurrence patients excluded', rT, np.where(rafter | dead, 1.0, 0.0), elig & ~und),
]
rfs_rows = []
for lab, T_, E_, mask in rfs_specs:
    k = KaplanMeierFitter().fit(T_[mask], E_[mask])
    ci = median_survival_times(k.confidence_interval_).iloc[0]
    rfs_rows.append({'RFS_analysis': lab, 'n': int(mask.sum()), 'events': int(E_[mask].sum()),
                     'median_RFS': round(float(k.median_survival_time_), 2) if np.isfinite(k.median_survival_time_) else None,
                     'median_95CI': f'{ci.iloc[0]:.2f}-{ci.iloc[1]:.2f}' if np.isfinite(ci.iloc[1]) else f'{ci.iloc[0]:.2f}-NE',
                     'RFS_3y': round(float(k.survival_function_at_times(3).iloc[0]), 3),
                     'RFS_5y': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
save(pd.DataFrame(rfs_rows), 'F17_RFS_sensitivity_final')
print(pd.DataFrame(rfs_rows).to_string(index=False))

# %% [markdown]
# ## 11. Manifest and reproduction check
#
# The manifest records input checksums, row counts and package versions. If earlier v6 results are available, the key
# numbers are compared; the notebook reports PASS or FAIL for each.

# %% [code]
import importlib.metadata as md
versions = {p: md.version(p) for p in ['pandas', 'numpy', 'lifelines', 'scikit-survival', 'scikit-learn', 'pyarrow', 'python-calamine']}
manifest = {'inputs': manifest_inputs, 'row_counts': row_counts, 'platform': platform.platform(),
            'python': platform.python_version(), 'packages': versions, 'selected_model': SELECTED,
            'runtime_seconds': round(time.time() - T_START)}
(OUT_DIR / 'F24_run_manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))

ref = REF_DIR / 'final_v6'
if ref.exists():
    checks = []
    def chk(name, got, want, tol=0.0):
        ok = (abs(float(got) - float(want)) <= tol) if tol else (str(got) == str(want))
        checks.append({'check': name, 'this_run': got, 'v6_reference': want, 'result': 'PASS' if ok else 'FAIL'})
    ref_head = pd.read_csv(ref / 'F00_headline.csv').set_index('quantity')['value']
    chk('selected model', SELECTED, ref_head['selected_model'])
    chk('cut-point q33', round(Q33, 4), ref_head['phenotype_cut_S5_q33'], 1e-4)
    chk('cut-point q67', round(Q67, 4), ref_head['phenotype_cut_S5_q67'], 1e-4)
    chk('primary cohort', len(PRIMARY), ref_head['primary_cohort_TNM_complete'])
    ref_perf = pd.read_csv(ref / 'F02_M_stage_candidates_identical_patients.csv')
    chk('M2a validation C', perf.iloc[1]['valid_C'], ref_perf.iloc[1]['valid_C'], 1e-4)
    ref_rfs = pd.read_csv(ref / 'F17_RFS_sensitivity_final.csv')
    chk('RFS primary median', rfs_rows[0]['median_RFS'], ref_rfs.iloc[0]['median_RFS'], 1e-2)
    ref_pre = pd.read_csv(ref / 'F14_preoperative_only_sensitivity.csv')
    chk('pre-operative (M1 structure) validation C', pre_perf.iloc[0]['valid_C'], ref_pre.iloc[0]['valid_C'], 1e-4)
    ref_sub = pd.read_csv(ref / 'F16_identical_subset_comparison_calibration.csv')
    chk('Fong subset C', rows_sub[1]['selected_model_C'], ref_sub.iloc[1]['selected_model_C'], 1e-4)
    chk('Nordlinger subset C', rows_sub[2]['selected_model_C'], ref_sub.iloc[2]['selected_model_C'], 1e-4)
    chk('CEA complete-case HR', cea_rows[0]['CEA_HR_per_log_unit'], pd.read_csv(ref / 'F13_CEA_sensitivity_final.csv').iloc[0]['CEA_HR_per_log_unit'], 1e-3)
    rep = pd.DataFrame(checks)
    save(rep, 'F25_reproduction_check_against_v6')
    print(rep.to_string(index=False))
    print('ALL PASS' if (rep.result == 'PASS').all() else 'SOME CHECKS DIFFER: see F25_reproduction_check_against_v6.csv')
else:
    print(f'No v6 reference found at {ref}; reproduction check skipped.')
log(f'done -> {OUT_DIR}')
