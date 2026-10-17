"""Audit: (1) reproduce the surgery-origin cohort (index operation LE1OPERDT_F1) and (2) audit recurrence
variables. Reads combined_extract_v2.parquet only; writes aggregate tables."""
import os
from pathlib import Path

import numpy as np
import pandas as pd

WORK = Path(os.environ['LIVERMET_WORK_DIR'])
RES = Path(os.environ['LIVERMET_RESULTS_DIR']) / 'audit_origins_recurrence'
RES.mkdir(parents=True, exist_ok=True)
EP = pd.Timestamp('1899-12-30')
MISS = ['ND', 'NA', '']
DAYS = 365.25
df = pd.read_parquet(WORK / 'combined_extract_v2.parquet')
print('rows', len(df), df.SOURCE_PART.value_counts().to_dict())


def num(s):
    return pd.to_numeric(s.where(~s.isin(MISS)), errors='coerce')


def xl(s, lo=1, hi=80000):
    v = num(s)
    v = v.where((v >= lo) & (v <= hi))
    return EP + pd.to_timedelta(v, unit='D')


def tnm(col_t, col_n, col_m):
    ok = pd.Series(True, index=df.index)
    for c in [col_t, col_n, col_m]:
        ok &= df[c].notna() & ~df[c].isin(MISS)
    return ok


TNM = tnm('STADET', 'STADEN', 'STADEM')
OP = xl(df.LE1OPERDT_F1)
DG = xl(df.LE1DGMETADT)
LAST = xl(df.LASTNDTC)
ST = df.PATSTATC.where(df.PATSTATC.isin(['Alive', 'Deceased', 'Lost to follow-up']))
VALID_STATUS = ST.notna()
OS_OP = (LAST - OP).dt.days
OS_DG = (LAST - DG).dt.days

# ---------------- 1. surgery-origin reproduction
rows = []


def add(label, mask):
    rows.append({'definition': label, 'n': int(mask.sum()),
                 'deaths': int((mask & ST.eq('Deceased')).sum())})


add('index operation date present (LE1OPERDT_F1)', OP.notna())
add('  + TNM complete', OP.notna() & TNM)
add('  + valid status and last contact', OP.notna() & VALID_STATUS & LAST.notna())
add('  + OS from operation > 0 days', OP.notna() & VALID_STATUS & LAST.notna() & (OS_OP > 0))
add('  + TNM complete + valid OS from operation', OP.notna() & TNM & VALID_STATUS & LAST.notna() & (OS_OP > 0))
add('  + LE1 surgery flag Yes (LE1HEPATECTYN_F1)', OP.notna() & df.LE1HEPATECTYN_F1.eq('Yes'))
add('  + valid OS from operation, any TNM', OP.notna() & VALID_STATUS & LAST.notna() & (OS_OP > 0))
add('  + operation on/after liver metastasis diagnosis', OP.notna() & DG.notna() & (OP >= DG) & VALID_STATUS & LAST.notna() & (OS_OP > 0))
add('Diagnosis origin, TNM complete, valid OS (primary, for reference)', TNM & DG.notna() & VALID_STATUS & LAST.notna() & (OS_DG > 0))
rep = pd.DataFrame(rows)
rep.to_csv(RES / 'A01_surgery_origin_reproduction.csv', index=False)
print(rep.to_string(index=False))

# operation date audit
op_audit = {
    'operation dates present (LE1OPERDT_F1)': int(OP.notna().sum()),
    'operation date before liver metastasis diagnosis': int((OP < DG).sum()),
    'operation date same day as diagnosis': int((OP == DG).sum()),
    'operation date with no diagnosis date': int((OP.notna() & DG.isna()).sum()),
    'operation date after last contact': int((OP > LAST).sum()),
    'operation date with dataset flag LE1HEPATECTYN_F1 = No': int((OP.notna() & df.LE1HEPATECTYN_F1.eq('No')).sum()),
    'LE1HEPATECTYN_F1 = Yes but no operation date': int((OP.isna() & df.LE1HEPATECTYN_F1.eq('Yes')).sum()),
    'operation date components agree with serial': int(((xl(df.LE1OPERDT_F1_Y).dt.year == OP.dt.year) & (num(df.LE1OPERDT_F1_M) == OP.dt.month) & (num(df.LE1OPERDT_F1_D) == OP.dt.day))[OP.notna()].sum()),
}
pd.Series(op_audit).rename('n').rename_axis('check').reset_index().to_csv(RES / 'A02_operation_date_audit.csv', index=False)
print(pd.Series(op_audit).to_string())

# ---------------- 2. recurrence variables audit
REC_FIELDS = {
    'RECDT_F1..F7 (generic recurrence date, follow-up forms)': [f'RECDT_F{i}' for i in range(1, 8)],
    'LRDGMETADT_M1..M5 (liver recurrence episode date)': [f'LRDGMETADT_M{i}' for i in range(1, 6)],
    'LRDGMETA2DT_M1..M5 (second liver recurrence date)': [f'LRDGMETA2DT_M{i}' for i in range(1, 6)],
    'EXHEXTRAHEPDGDT_M1..M8 (extrahepatic recurrence date)': [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)],
}
rec_rows = []
dates = {}
for label, fields in REC_FIELDS.items():
    per = {f: xl(df[f]) for f in fields}
    dates[label] = per
    any_date = pd.concat(per.values(), axis=1).notna().any(axis=1)
    rec_rows.append({'field group': label, 'patients_with_any_date': int(any_date.sum()),
                     'date_entries': int(sum(v.notna().sum() for v in per.values()))})
cnt = {'LRNBREC_M1..M5 (liver recurrence count, >0)': [f'LRNBREC_M{i}' for i in range(1, 6)],
       'EXHNBREC2_M1..M8 (extrahepatic recurrence count, >0)': [f'EXHNBREC2_M{i}' for i in range(1, 9)]}
for label, fields in cnt.items():
    vals = pd.concat([num(df[f]) for f in fields], axis=1)
    rec_rows.append({'field group': label, 'patients_with_any_date': int((vals > 0).any(axis=1).sum()),
                     'date_entries': int((vals > 0).sum().sum())})
rec_df = pd.DataFrame(rec_rows)
rec_df.to_csv(RES / 'A03_recurrence_fields_coverage.csv', index=False)
print(rec_df.to_string(index=False))

# any dated recurrence (liver or extrahepatic episode date, or RECDT_F*) after diagnosis
all_dates = pd.concat([v for label, per in dates.items() for v in per.values()] +
                      [xl(df[f'RECDT_F{i}']) for i in range(1, 8)], axis=1)
first_rec = all_dates.min(axis=1)
dated = first_rec.notna()
liver_or_ext = pd.concat([v for label, per in dates.items() if 'RECDT' not in label for v in per.values()], axis=1).min(axis=1)
cnt_pos = (pd.concat([num(df[f]) for f in cnt['LRNBREC_M1..M5 (liver recurrence count, >0)']], axis=1).sum(axis=1) > 0) | \
          (pd.concat([num(df[f]) for f in cnt['EXHNBREC2_M1..M8 (extrahepatic recurrence count, >0)']], axis=1).sum(axis=1) > 0)
AWD = df.PATSTAT_F1.eq('Alive with disease')
DEATH = ST.eq('Deceased')
cross = pd.DataFrame({
    'alive with disease at F1': AWD,
    'dated recurrence (any field)': dated,
    'recurrence count >0 (LRNBREC/EXHNBREC2)': cnt_pos,
    'death': DEATH,
})
cross_tab = cross.groupby(['alive with disease at F1', 'dated recurrence (any field)', 'recurrence count >0 (LRNBREC/EXHNBREC2)']).size().rename('n').reset_index()
cross_tab.to_csv(RES / 'A04_alive_with_disease_vs_recurrence_fields.csv', index=False)
print(cross_tab.to_string(index=False))

# relation of recurrence dates to the index operation (surgery-origin) and to diagnosis
rel = pd.DataFrame({'first_dated_recurrence': first_rec, 'op': OP, 'dg': DG})
rel_summary = {
    'patients with any dated recurrence': int(dated.sum()),
    'dated recurrence before index operation': int(((first_rec < OP) & OP.notna()).sum()),
    'dated recurrence after index operation': int(((first_rec >= OP) & OP.notna()).sum()),
    'dated recurrence but no index operation date': int((dated & OP.isna()).sum()),
}
pd.Series(rel_summary).rename('n').rename_axis('check').reset_index().to_csv(RES / 'A05_recurrence_vs_operation_dates.csv', index=False)
print(pd.Series(rel_summary).to_string())
print('done')
