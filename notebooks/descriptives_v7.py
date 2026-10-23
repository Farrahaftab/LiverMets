"""Descriptive outputs for the revised manuscript, from the v7 cohort definition (same rules as
LiverMets_final_reproducible.py, section 2). Writes Table 1, Supplementary Table S1, the flow counts used for
Figure 1, and a predictor-timing audit. Every count is checked against the executed notebook outputs.

Inputs: LIVERMET_WORK_DIR/extract_raw.parquet (written by the notebook) and the two raw workbooks in
LIVERMET_DATA_DIR (only for operative-form fields that the notebook does not extract).
Outputs: LIVERMET_OUT_DIR (default results/final_v7), files F30-F35.
"""
import calendar
import os
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from python_calamine import CalamineWorkbook

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
DATA = Path(os.environ['LIVERMET_DATA_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v7'))
OUT.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
MAXFU = 15.0

X = pd.read_parquet(WORK / 'extract_raw.parquet')
assert len(X) == 29565


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
    return s.astype(object).map(lambda v: mapping.get(v, np.nan) if isinstance(v, str) else np.nan)


TMAP = {'T0': 'T1-2', 'T1': 'T1-2', 'T2': 'T1-2', 'T3': 'T3', 'T4': 'T4', 'T4a': 'T4', 'T4b': 'T4'}
NMAP = {'N0': 'N0', 'N1': 'N1', 'N1a': 'N1', 'N1b': 'N1', 'N1c': 'N1', 'N2': 'N2', 'N2a': 'N2', 'N2b': 'N2'}
MMAP = {'M0': 'M0', 'M1': 'M1', 'M1a': 'M1', 'M1b': 'M1', 'M1c': 'M1'}
INC = X.CINCLUSION.eq('Yes')
HEP = X.LE1HEPATECTYN_F1.eq('Yes')
PST_ANY = X.PATSTATC.notna()
DEATH = X.PATSTATC.eq('Deceased')
LAST_SER = serial(X.LASTNDTC)
T_G = gmap(X.STADET, TMAP); N_G = gmap(X.STADEN, NMAP); M_G = gmap(X.STADEM, MMAP)
TNM = pd.concat([T_G, N_G, M_G], axis=1).notna().all(axis=1)
BIRTH = serial(X.BIRTHDT); DGK = serial(X.DGKCOLDT); DG = serial(X.LE1DGMETADT)
MALE = X.GENDER.map({'Male': 1.0, 'Female': 0.0})
SYNC = X.LE1METASYNCYN.map({'Yes': 1.0, 'No': 0.0})
METS = num(X.LE1NBMETAHEPNUM).where(lambda v: (v >= 1) & (v <= 50))
SIZE = num(X.LE1HEPMETASIZENUM).where(lambda v: (v > 0) & (v <= 300))
CEA = num(X.LE1PREHEPCEA_F1).where(lambda v: (v >= 0) & (v <= 40000))
REC_FIELDS = ([f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
              + [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)] + [f'RECDT_F{i}' for i in range(1, 8)])
REC_FIRST = pd.concat([serial(X[c]) for c in REC_FIELDS], axis=1).min(axis=1)
CNT_REC = (pd.concat([num(X[f'LRNBREC_M{i}']) for i in range(1, 6)] + [num(X[f'EXHNBREC2_M{i}']) for i in range(1, 9)],
                     axis=1).fillna(0) > 0).any(axis=1)

# ---------- cohort (day 15 primary; same rules as the notebook)
op_ser = serial(X.LE1OPERDT_F1)
op_ym = ymd('LE1OPERDT_F1', 15)
op = op_ser.fillna(op_ym)
s4 = INC & HEP & op_ym.notna()
s5 = s4 & PST_ANY & LAST_SER.notna()
s6 = s5 & (LAST_SER >= op)
fu = (LAST_SER - op).dt.days
s7 = s6 & ((fu > 0) | DEATH)
flow = pd.Series({'1 registry': len(X), '2 CINCLUSION=Yes': int(INC.sum()), '3 hepatectomy': int((INC & HEP).sum()),
                  '4 operation date (year+month)': int(s4.sum()), '5 status and last-news': int(s5.sum()),
                  '6 chronology': int(s6.sum()), '7 positive follow-up or death': int(s7.sum()),
                  '8 complete TNM (analytic cohort)': int((s7 & TNM).sum())})
flow.rename('n').rename_axis('step').reset_index().to_csv(OUT / 'F30_flow_counts_for_figure1.csv', index=False)
print(flow.to_string())

d = pd.DataFrame(index=X.index[s7])
d['T0'] = op[s7]; d['PARTIAL'] = op_ser[s7].isna() & op_ym[s7].notna()
d['LAST'] = LAST_SER[s7]; d['DEATH'] = DEATH[s7].astype(float)
d['OS_DAYS'] = (d['LAST'] - d['T0']).dt.days
d['TNM'] = TNM[s7]; d['T_GRP'] = T_G[s7]; d['N_GRP'] = N_G[s7]; d['M_GRP'] = M_G[s7]
d['AGE'] = (d['T0'] - BIRTH[s7]).dt.days / DAYS
d.loc[(d.AGE < 18) | (d.AGE > 100), 'AGE'] = np.nan
d['MALE'] = MALE[s7]; d['SYNC'] = SYNC[s7]; d['METS'] = METS[s7]; d['SIZE'] = SIZE[s7]; d['CEA'] = CEA[s7]
d['DFI_RAW'] = (DG[s7] - DGK[s7]).dt.days / 30.4375
d['DG_AFTER_OP'] = (DG[s7] > d['T0']) & d.SYNC.eq(0)
d['DG_MISSING'] = DG[s7].isna() & d.SYNC.eq(0)
d['DGK_MISSING'] = DGK[s7].isna() & d.SYNC.eq(0)
d['DFI_NEG'] = (d.DFI_RAW < 0) & d.SYNC.eq(0)
d['DFI_REASON'] = np.select([d.SYNC.eq(1), d.SYNC.isna(), d.DGK_MISSING, d.DG_MISSING, d.DFI_NEG, d.DG_AFTER_OP],
                            ['synchronous', 'synchrony unknown', 'primary date missing', 'metastasis date missing',
                             'negative interval', 'after operation'], default='available')
d['DFI'] = d.DFI_RAW.copy()
d.loc[d.SYNC == 1, 'DFI'] = 0.0
d.loc[(d.DFI < 0) | d.DG_AFTER_OP, 'DFI'] = np.nan
d['ERA'] = np.where(d['T0'].dt.year <= 2009, 'Development (<=2009)', 'Validation (>=2010)')
d['OS_Y'] = np.minimum(np.where((d.OS_DAYS <= 0) & (d.DEATH == 1), 0.5, d.OS_DAYS) / DAYS, MAXFU)
d['OS_E'] = np.where(np.where((d.OS_DAYS <= 0) & (d.DEATH == 1), 0.5, d.OS_DAYS) / DAYS > MAXFU, 0.0, d.DEATH)
d['MET_CAT'] = pd.cut(d.METS, [0, 1, 3, np.inf], labels=['1', '2-3', '>=4']).astype(object)
d.loc[d.METS.isna(), 'MET_CAT'] = 'Unknown'
d['CEA_AVAIL'] = d.CEA.notna()
A = d[d.TNM].copy()
assert len(A) == 17262, len(A)
A_TR = A[A.ERA.str.startswith('Dev')]
A_VA = A[A.ERA.str.startswith('Val')]
assert (len(A_TR), len(A_VA)) == (8463, 8799), (len(A_TR), len(A_VA))
assert int(A.OS_E.sum()) == 4675 + 1916


def fmt_n(mask_or_n, total):
    return f'{int(mask_or_n):,} ({100 * int(mask_or_n) / total:.1f})'


def median_iqr(s):
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    return f'{med:.1f} ({q1:.1f}-{q3:.1f})'


def km_median(T, E):
    k = KaplanMeierFitter().fit(T, E)
    return k.median_survival_time_


def rev_km_median(T, E):
    k = KaplanMeierFitter().fit(T, 1 - E)
    return k.median_survival_time_


def table1_block(frame):
    n = len(frame)
    rows = []
    rows.append(('Patients', f'{n:,}'))
    rows.append(('Age at operation, years, median (IQR)', median_iqr(frame.AGE.dropna())))
    rows.append(('Male sex, n (%)', fmt_n(frame.MALE.sum(), n)))
    for lab, col, cats in [('T stage', 'T_GRP', ['T1-2', 'T3', 'T4']), ('N stage', 'N_GRP', ['N0', 'N1', 'N2']),
                           ('M stage', 'M_GRP', ['M0', 'M1'])]:
        rows.append((lab + ', n (%)', ''))
        for c in cats:
            rows.append(('   ' + c, fmt_n((frame[col] == c).sum(), n)))
    rows.append(('Synchronous presentation, n (%)', fmt_n(frame.SYNC.sum(), n)))
    rows.append(('Synchrony not recorded, n (%)', fmt_n(frame.SYNC.isna().sum(), n)))
    meta = frame[frame.SYNC == 0]
    rows.append(('Metachronous presentation, n (%)', fmt_n((frame.SYNC == 0).sum(), n)))
    rows.append(('Interval primary to liver metastasis, months, median (IQR; metachronous only)', median_iqr(meta.DFI.dropna())))
    rows.append(('Metachronous, interval unavailable (metastasis date unknown or after operation), n (%)', fmt_n(meta.DFI.isna().sum(), len(meta)) if len(meta) else '0'))
    rows.append(('Number of liver metastases, n (%)', ''))
    for c in ['1', '2-3', '>=4', 'Unknown']:
        rows.append(('   ' + c, fmt_n((frame.MET_CAT == c).sum(), n)))
    rows.append(('Largest recorded metastasis, mm, median (IQR)', median_iqr(frame.SIZE.dropna())))
    rows.append(('Size missing, n (%)', fmt_n(frame.SIZE.isna().sum(), n)))
    rows.append(('Pre-operative CEA recorded, n (%)', fmt_n(frame.CEA_AVAIL.sum(), n)))
    rows.append(('Deaths, n (%)', fmt_n(frame.OS_E.sum(), n)))
    rows.append(('Median follow-up, years (reverse Kaplan-Meier)', f'{rev_km_median(frame.OS_Y.values, frame.OS_E.values):.2f}'))
    rows.append(('Median overall survival, years (KM, 95% CI not shown)', f'{km_median(frame.OS_Y.values, frame.OS_E.values):.2f}'))
    return rows


t1 = pd.DataFrame(table1_block(A), columns=['characteristic', 'Total (n=17,262)'])
t1_tr = pd.DataFrame(table1_block(A_TR), columns=['characteristic', 'Development (<=2009; n=8,463)'])
t1_va = pd.DataFrame(table1_block(A_VA), columns=['characteristic', 'Validation (>=2010; n=8,799)'])
table1 = t1_tr.merge(t1_va, on='characteristic').merge(t1, on='characteristic', how='left')
table1 = table1[['characteristic', 'Total (n=17,262)', 'Development (<=2009; n=8,463)', 'Validation (>=2010; n=8,799)']]
table1.to_csv(OUT / 'F31_table1_baseline_characteristics.csv', index=False)
print(table1.to_string(index=False))

# ---------- Supplementary Table S1: analytic cohort vs patients meeting steps 1-7 but with incomplete TNM
E = d[~d.TNM]
def s1_block(frame):
    n = len(frame)
    out = [('Patients', f'{n:,}'), ('Age at operation, years, median (IQR)', median_iqr(frame.AGE.dropna())),
           ('Male sex, n (%)', fmt_n(frame.MALE.sum(), n)), ('Synchronous presentation, n (%)', fmt_n(frame.SYNC.sum(), n)),
           ('Number of liver metastases known, n (%)', fmt_n(frame.METS.notna().sum(), n)),
           ('Largest recorded metastasis known, n (%)', fmt_n(frame.SIZE.notna().sum(), n)),
           ('Pre-operative CEA recorded, n (%)', fmt_n(frame.CEA_AVAIL.sum(), n)),
           ('Deaths, n (%)', fmt_n(frame.OS_E.sum(), n)),
           ('Median overall survival, years (KM)', f'{km_median(frame.OS_Y.values, frame.OS_E.values):.2f}')]
    return out
s1 = pd.DataFrame(s1_block(A), columns=['characteristic', 'Analytic cohort (TNM complete, n=17,262)'])
s1e = pd.DataFrame(s1_block(E), columns=['characteristic', f'Excluded, incomplete TNM (n={len(E):,})'])
supp = s1.merge(s1e, on='characteristic')
supp['note'] = ''
supp.loc[supp.characteristic.str.startswith('Patients'), 'note'] = 'Both groups met registry steps 1-7'
supp.to_csv(OUT / 'F32_supp_S1_included_vs_excluded.csv', index=False)
print(supp.to_string(index=False))

# ---------- predictor-timing audit
# (a) metastasis diagnosis after operation (interval predictor set missing)
dg_after = int(d.DG_AFTER_OP.sum())
dg_after_tnm = int((d.DG_AFTER_OP & d.TNM).sum())
# (b) recurrence dates: how many of the analytic cohort have a dated recurrence before time zero
rec_all = REC_FIRST[A.index]
rec_before = int(((rec_all < A.T0) & rec_all.notna()).sum())
rec_after = int(((rec_all >= A.T0) & (rec_all <= A['LAST']) & rec_all.notna()).sum())
rec_after_last = int(((rec_all > A['LAST']) & rec_all.notna()).sum())
# undated as defined in the notebook: count > 0 and neither a dated recurrence after operation nor a dated pre-operative one
undated = int((CNT_REC[A.index] & ~((rec_all >= A.T0) & (rec_all <= A['LAST'])) & ~(rec_all < A.T0)).sum())
audit = pd.DataFrame([
    {'item': 'Analytic cohort (TNM complete)', 'n': len(A)},
    {'item': 'Liver metastasis diagnosed after operation (interval set missing), analytic cohort',
     'n': int(A.DG_AFTER_OP.sum())},
    {'item': 'Metachronous, interval unavailable: primary diagnosis date missing (first reason in order)', 'n': int((A.DFI_REASON == 'primary date missing').sum())},
    {'item': 'Metachronous, interval unavailable: liver metastasis date missing', 'n': int((A.DFI_REASON == 'metastasis date missing').sum())},
    {'item': 'Metachronous, interval unavailable: metastasis diagnosed before primary (negative)', 'n': int((A.DFI_REASON == 'negative interval').sum())},
    {'item': 'Metachronous, interval unavailable: metastasis diagnosed after operation', 'n': int((A.DFI_REASON == 'after operation').sum())},
    {'item': 'Metachronous, interval available', 'n': int((A.DFI_REASON == 'available').sum())},
    {'item': 'Synchrony not recorded (not classed as either)', 'n': int((A.DFI_REASON == 'synchrony unknown').sum())},
    {'item': 'Liver metastasis diagnosed after operation, all patients meeting steps 1-7', 'n': dg_after},
    {'item': 'Dated recurrence before time zero (excluded from RFS), analytic cohort', 'n': rec_before},
    {'item': 'Dated recurrence after operation and before last contact, analytic cohort', 'n': rec_after},
    {'item': 'Recurrence recorded with a date after last contact (notebook counts these as undated), analytic cohort', 'n': rec_after_last},
    {'item': 'Recurrence recorded without usable date (count > 0; notebook definition), analytic cohort', 'n': undated},
])
audit.to_csv(OUT / 'F33_predictor_and_recurrence_date_audit.csv', index=False)
print(audit.to_string(index=False))

# ---------- operative-form audit: resected metastasis count vs pre-operative count (analytic cohort)
WANT = ['LE1NBMRESECNUM_F1', 'LE1NBMRESECNUM_F2']


def conv(v):
    if v is None or v == '':
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def rows(path):
    sh = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for i, r in enumerate(sh.iter_rows(), start=1):
        if all(v in (None, '') for v in r):
            continue
        yield i, r


op_vals = {}
_, hdr1 = next(rows(DATA / 'LiverMet_Part1.xlsx'))
pos = {str(h): j for j, h in enumerate(hdr1)}
for part, fn in [('Part1', 'LiverMet_Part1.xlsx'), ('Part2', 'LiverMet_Part2.xlsx')]:
    for rn, r in rows(DATA / fn):
        if part == 'Part1' and rn == 2:
            continue
        op_vals[(part, rn)] = [conv(r[pos[c]]) if pos[c] < len(r) else None for c in WANT]
# align with the extract order (SOURCE_PART, SOURCE_EXCEL_ROW)
keys = list(zip(X.SOURCE_PART, X.SOURCE_EXCEL_ROW))
opdf = pd.DataFrame([op_vals.get((p, int(r)), [None, None]) for p, r in keys], columns=WANT, index=X.index)
res1 = num(opdf['LE1NBMRESECNUM_F1']).loc[A.index]
pre = METS.loc[A.index]
both = res1.notna() & pre.notna()
audit2 = pd.DataFrame([
    {'item': 'Analytic cohort with both pre-operative and resected metastasis counts', 'n': int(both.sum())},
    {'item': 'Resected count equals pre-operative count', 'n': int((res1 == pre)[both].sum())},
    {'item': 'Resected count greater than pre-operative count', 'n': int((res1 > pre)[both].sum())},
    {'item': 'Resected count less than pre-operative count', 'n': int((res1 < pre)[both].sum())},
])
audit2.to_csv(OUT / 'F34_operative_vs_preoperative_metastasis_count.csv', index=False)
print(audit2.to_string(index=False))
print('descriptives done ->', OUT)
