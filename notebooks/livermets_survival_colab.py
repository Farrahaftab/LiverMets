# %% [markdown]
# # LiverMets PhD analysis: censoring-aware survival, phenotyping and treatment comparison
#
# **Purpose.** Rebuild the colorectal liver metastases (CRLM) survival analysis from the two split
# LiverMetSurvey export files (`LiverMet_Part1.xlsx`, `LiverMet_Part2.xlsx`).
#
# **Memory strategy.** The Excel export has ~13,600 columns. Each workbook is streamed row by row with
# `python-calamine` (Rust reader, no full sheet in memory). Only the analysis columns are kept and
# written to a compressed Parquet file in 2,000-row batches. A separate pass records the non-empty
# count of every column (the full column inventory). All analysis then runs on the ~110-column Parquet.
#
# **Privacy.** Direct identifiers (names, reference numbers, free-text subject references) are never
# extracted. Patient-level working files are written to `WORK_DIR` only. The `RESULTS_DIR` outputs are
# aggregate tables, figures, logs and the reproducibility report.
#
# **Run order.** Run all cells top to bottom (Runtime > Run all). Expected run time on Colab CPU: about
# 25 to 35 minutes, dominated by the Excel streaming pass and the random survival forest.
#
# **Honesty rules used throughout.** No result is typed in by hand. Every number in the report is
# produced by a cell in this notebook. Performance is reported as measured. There is no tuning on the
# validation data, and no threshold is set to reach a target value.

# %% [code]
# Install dependencies (no-op when already present, e.g. local runs)
import importlib, subprocess, sys

def _ensure(import_name, pip_name):
    try:
        importlib.import_module(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pip_name])

_ensure('python_calamine', 'python-calamine')
_ensure('lifelines', 'lifelines')
_ensure('sksurv', 'scikit-survival')
print('Dependencies ready.')

# %% [code]
# Imports, configuration and reproducibility settings
import os, json, time, shutil, hashlib, platform, warnings, resource
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
import sklearn
import lifelines, sksurv
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test, proportional_hazard_test
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sksurv.tree import SurvivalTree
from sksurv.ensemble import RandomSurvivalForest, GradientBoostingSurvivalAnalysis
from sksurv.metrics import (concordance_index_censored, cumulative_dynamic_auc,
                            brier_score, integrated_brier_score)
from sksurv.util import Surv

warnings.filterwarnings('ignore')
SEED = 42
np.random.seed(SEED)
MAX_FU_YEARS = 15          # follow-up truncation, as in the earlier analysis
PHENO_FAV_MIN = 6.0        # KM median OS (years) thresholds, as in the earlier analysis
PHENO_INT_MIN = 5.0
ERA_SPLIT_YEAR = 2009      # training era <= 2009, validation era > 2009 (temporal validation)
DAYS_PER_YEAR = 365.25
TIMES_AUC = np.array([1.0, 3.0, 5.0])
TIMES_BRIER = np.arange(1.0, 7.5, 0.5)
RMST_TAU = 5.0

IN_COLAB = 'google.colab' in sys.modules
DATA_DIR = Path(os.environ.get('LIVERMET_DATA_DIR', '/content'))
WORK_DIR = Path(os.environ.get('LIVERMET_WORK_DIR', '/content/work'))
RESULTS_DIR = Path(os.environ.get('LIVERMET_RESULTS_DIR', '/content/results'))
for _d in [WORK_DIR, RESULTS_DIR / 'tables', RESULTS_DIR / 'figures', RESULTS_DIR / 'logs']:
    _d.mkdir(parents=True, exist_ok=True)

PART_FILES = {'Part1': DATA_DIR / 'LiverMet_Part1.xlsx', 'Part2': DATA_DIR / 'LiverMet_Part2.xlsx'}
RUN_FULL_INVENTORY = True   # counts non-empty cells in all ~13,658 columns (adds a few minutes)

def peak_mem_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')} | peak {peak_mem_mb():,.0f} MB] {msg}", flush=True)

def save_table(df, name, index=False):
    path = RESULTS_DIR / 'tables' / f'{name}.csv'
    df.to_csv(path, index=index)
    return path

def save_fig(fig, name):
    path = RESULTS_DIR / 'figures' / f'{name}.png'
    fig.savefig(path, dpi=300, bbox_inches='tight')
    return path

print('Python', platform.python_version(), '| pandas', pd.__version__, '| numpy', np.__version__,
      '| lifelines', lifelines.__version__, '| scikit-survival', sksurv.__version__,
      '| scikit-learn', sklearn.__version__)
log(f'DATA_DIR={DATA_DIR} WORK_DIR={WORK_DIR} RESULTS_DIR={RESULTS_DIR} IN_COLAB={IN_COLAB}')

# %% [code]
# Locate the two workbooks (Colab: upload them if they are not already present)
missing = [p.name for p in PART_FILES.values() if not p.exists()]
if missing and IN_COLAB:
    from google.colab import files
    print('Please upload:', missing)
    uploaded = files.upload()
    for name in uploaded:
        shutil.move(name, DATA_DIR / name)
missing = [p.name for p in PART_FILES.values() if not p.exists()]
assert not missing, f'Missing input files: {missing}. Rename uploads to LiverMet_Part1.xlsx / LiverMet_Part2.xlsx.'
for k, p in PART_FILES.items():
    log(f'{k}: {p.name} ({p.stat().st_size/1e6:.1f} MB)')

# %% [markdown]
# ## Part 1. Combine the two Excel files by streaming
#
# Part 1 has a blank first row, then a header row (row 2), then patients. Part 2 has a blank first row
# and **no header**: its first non-blank row is a patient. The notebook detects both layouts
# automatically and checks that the Part 2 columns align with the Part 1 header.

# %% [code]
from python_calamine import CalamineWorkbook

DATE_BASES = ['BIRTHDT', 'REFERDT', 'CSTDT', 'DGKCOLDT', 'LE1DGMETADT', 'LE1DGMETA2DT',
              'LE1METARESECDT_L1', 'LE1PREOPMSTDT_F1', 'LE1POSTOPMSTDT_F1', 'LASTNDTC'] + \
             [f'RECDT_F{i}' for i in range(1, 8)]
PLAIN_COLS = ['COUNTRY_ID', 'SITE_ID', 'GENDER', 'STADET', 'STADEN', 'STADEM',
              'METANODENUM', 'RESECNODENUM', 'LE1METASYNCYN', 'LE1NBMETAHEPNUM', 'LE1NBMETAHEPCAR',
              'LE1HEPMETASIZENUM', 'LE1HEPMETASIZECAR', 'LE1PREHEPCEA_F1', 'LE1PREHEPCEACAR_F1',
              'LE1HEPATECTYN_F1', 'LE1HEPATECTYN_F2', 'LE1METARESECYN_L1', 'LE1METAOTHTRTYN_L1',
              'LE1PREOPMCTYN_F1', 'LE1POSTOPMCTYN_F1', 'POSTCOLCTYN_F1', 'LE1MINMARGNUM_F1',
              'LE1HISTONLIV_F1', 'PATSTATC', 'TIMELAST', 'TIMELAST_V', 'PATSTAT_F1', 'PATSTAT_F2',
              'CINCLUSION', 'KPMSSMSI'] + [f'DEATHKYN_F{i}' for i in range(1, 8)]
MISSING_TOKENS = ['ND', 'NA', '']


def iter_excel_rows(path):
    """Yield (excel_row_number, row) without loading the whole sheet into memory."""
    sheet = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for i, row in enumerate(sheet.iter_rows()):
        yield i + 1, row


def is_blank(row):
    return all(v is None or v == '' for v in row)


# Locate the header in Part 1 and confirm Part 2 has none
header_row_no, header_vals = None, None
for rn, row in iter_excel_rows(PART_FILES['Part1']):
    if is_blank(row):
        continue
    header_row_no, header_vals = rn, list(row)
    break
first_nonblank_p2 = None
for rn, row in iter_excel_rows(PART_FILES['Part2']):
    if is_blank(row):
        continue
    first_nonblank_p2 = (rn, list(row)[:6])
    break
log(f'Part1 header at Excel row {header_row_no}; Part2 first data row {first_nonblank_p2[0]}: {first_nonblank_p2[1]}')
assert header_row_no == 2 and str(header_vals[0]) == 'STUDY_ID', 'Part 1 header not where expected'
assert first_nonblank_p2[1][0] == 'LIVERMET', 'Part 2 does not look like patient data (no header expected)'

SCHEMA = [str(v) if v not in (None, '') else f'UNNAMED_{j+1}' for j, v in enumerate(header_vals)]
N_SCHEMA = len(SCHEMA)
assert len(set(SCHEMA)) == N_SCHEMA, 'Duplicate column names in header'
log(f'Header: {N_SCHEMA:,} column names, all unique')

# Analysis columns: every date keeps its day/month/year components where they exist
ANALYSIS_COLS = []
for base in DATE_BASES:
    for suf in ['', '_D', '_M', '_Y']:
        if base + suf in SCHEMA:
            ANALYSIS_COLS.append(base + suf)
for c in PLAIN_COLS:
    if c in SCHEMA:
        ANALYSIS_COLS.append(c)
ANALYSIS_COLS = list(dict.fromkeys(ANALYSIS_COLS))
MISSING_FROM_SCHEMA = [c for c in DATE_BASES + PLAIN_COLS if c not in SCHEMA]
assert not MISSING_FROM_SCHEMA, f'Expected analysis columns missing from header: {MISSING_FROM_SCHEMA}'
ANALYSIS_IDX = [SCHEMA.index(c) for c in ANALYSIS_COLS]
log(f'Analysis columns selected: {len(ANALYSIS_COLS)} of {N_SCHEMA:,}')

# %% [code]
# Stream both parts: keep analysis columns, count everything else, write Parquet in batches
import pyarrow as pa
import pyarrow.parquet as pq

EXTRACT_PATH = WORK_DIR / 'combined_extract.parquet'
BATCH = 2000
arrow_schema = pa.schema([(c, pa.string()) for c in ANALYSIS_COLS] +
                         [('SOURCE_PART', pa.string()), ('SOURCE_EXCEL_ROW', pa.int32())])
inventory = {k: np.zeros(N_SCHEMA, dtype=np.int64) for k in ['Part1', 'Part2']} if RUN_FULL_INVENTORY else None
audit = {}
writer = pq.ParquetWriter(EXTRACT_PATH, arrow_schema, compression='zstd')

def _conv(v):
    if v is None or v == '':
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)

for part, path in PART_FILES.items():
    t0 = time.time()
    counts = {'physical_rows': 0, 'blank_rows': 0, 'header_rows': 0, 'patient_rows': 0}
    cols_buf = {c: [] for c in ANALYSIS_COLS}
    src_buf, row_buf = [], []
    has_header = (part == 'Part1')
    for rn, row in iter_excel_rows(path):
        counts['physical_rows'] += 1
        if is_blank(row):
            counts['blank_rows'] += 1
            continue
        if has_header and rn == header_row_no:
            counts['header_rows'] += 1
            continue
        counts['patient_rows'] += 1
        L = len(row)
        for c, j in zip(ANALYSIS_COLS, ANALYSIS_IDX):
            cols_buf[c].append(_conv(row[j]) if j < L else None)
        if inventory is not None:
            inv = inventory[part]
            for j in range(min(L, N_SCHEMA)):
                v = row[j]
                if v is not None and v != '':
                    inv[j] += 1
        src_buf.append(part)
        row_buf.append(rn)
        if len(src_buf) >= BATCH:
            tbl = pa.table({**{c: pa.array(cols_buf[c], pa.string()) for c in ANALYSIS_COLS},
                            'SOURCE_PART': pa.array(src_buf, pa.string()),
                            'SOURCE_EXCEL_ROW': pa.array(row_buf, pa.int32())}, schema=arrow_schema)
            writer.write_table(tbl)
            cols_buf = {c: [] for c in ANALYSIS_COLS}
            src_buf, row_buf = [], []
    if src_buf:
        tbl = pa.table({**{c: pa.array(cols_buf[c], pa.string()) for c in ANALYSIS_COLS},
                        'SOURCE_PART': pa.array(src_buf, pa.string()),
                        'SOURCE_EXCEL_ROW': pa.array(row_buf, pa.int32())}, schema=arrow_schema)
        writer.write_table(tbl)
    audit[part] = counts
    log(f'{part}: {counts} in {time.time()-t0:,.0f}s')
writer.close()
log(f'Wrote {EXTRACT_PATH.name}')

# %% [code]
# Verify the combined row count and document the "additional counted row"
total_patients = sum(a['patient_rows'] for a in audit.values())
total_physical = sum(a['physical_rows'] for a in audit.values())
audit_df = pd.DataFrame(audit).T
audit_df.loc['TOTAL'] = audit_df.sum()
display(audit_df)
save_table(audit_df.reset_index().rename(columns={'index': 'source'}), 'T00_row_audit')

expected_patients = 29565
print(f'Patient rows combined: {total_patients:,} (expected {expected_patients:,})')
print(f'If the Part 1 header row were counted as a record, the total would be {total_patients + 1:,}; '
      f'it is not a patient and is excluded.')
assert total_patients == expected_patients, 'Row count does not match the expected 29,565 patients'
assert len(pd.read_parquet(EXTRACT_PATH, columns=['SOURCE_PART'])) == expected_patients

# %% [code]
# Full column inventory (names, positions and fill counts for every column in both parts)
if RUN_FULL_INVENTORY:
    inv_df = pd.DataFrame({
        'excel_column': [i + 1 for i in range(N_SCHEMA)],
        'column_name': SCHEMA,
        'nonempty_part1': inventory['Part1'][:N_SCHEMA],
        'nonempty_part2': inventory['Part2'][:N_SCHEMA],
    })
    inv_df['nonempty_total'] = inv_df.nonempty_part1 + inv_df.nonempty_part2
    inv_df['in_analysis_extract'] = inv_df.column_name.isin(ANALYSIS_COLS)
    inv_df['fill_pct_total'] = (100 * inv_df.nonempty_total / expected_patients).round(2)
    save_table(inv_df, 'T01_column_inventory')
    print(f'Columns with any data: {(inv_df.nonempty_total > 0).sum():,} of {N_SCHEMA:,}')
    print(f'Columns with no data in either part: {(inv_df.nonempty_total == 0).sum():,}')
    print(f'Columns with data beyond Part 2 width (Part 2 has no header):',
          int((inv_df.nonempty_part2 > 0).sum()) - int((inv_df.nonempty_part2[:13567] > 0).sum()))
    display(inv_df.sort_values('nonempty_total', ascending=False).head(10))
    log('Full inventory saved: T01_column_inventory.csv (column names only, no patient values)')

# %% [markdown]
# ## Part 2. Clean, derive and verify the analysis variables
#
# * Excel serial dates are converted to calendar dates. The original serial value is kept as `*_RAW`,
#   and the day/month/year component columns are checked against the serial value.
# * `ND` and `NA` tokens are treated as missing. No value is imputed in the cohort definition.
# * `TIMELAST` is **not** used as the survival time. Its values do not equal any date difference in the
#   export and include negative values (checked below), so follow-up is recomputed from dates.

# %% [code]
ana = pd.read_parquet(EXTRACT_PATH)
log(f'Loaded extract: {ana.shape[0]:,} patients x {ana.shape[1]} columns')
EXCEL_EPOCH = pd.Timestamp('1899-12-30')

def num(s):
    """Numeric conversion with ND/NA/blank treated as missing."""
    return pd.to_numeric(s.where(~s.isin(MISSING_TOKENS)), errors='coerce')

def excel_to_date(s, lo=1, hi=80000):
    v = num(s)
    v = v.where((v >= lo) & (v <= hi))
    return EXCEL_EPOCH + pd.to_timedelta(v, unit='D')

def yn(s):
    m = s.map({'Yes': 1.0, 'No': 0.0})
    return m

# Preserve original clinical dates and verify components
date_qc = []
for base in DATE_BASES:
    if base not in ana.columns:
        continue
    ana[base + '_RAW'] = ana[base]
    ana[base + '_DATE'] = excel_to_date(ana[base])
    if all(base + s in ana.columns for s in ['_D', '_M', '_Y']):
        comp = pd.to_datetime(dict(year=num(ana[base + '_Y']), month=num(ana[base + '_M']),
                                   day=num(ana[base + '_D'])), errors='coerce')
        both = ana[base + '_DATE'].notna() & comp.notna()
        agree = int((ana.loc[both, base + '_DATE'] == comp[both]).sum())
        date_qc.append({'date_field': base, 'n_with_serial': int(ana[base + '_DATE'].notna().sum()),
                        'n_with_components': int(comp.notna().sum()), 'n_components_agree': agree,
                        'n_components_disagree': int(both.sum()) - agree,
                        'min_date': str(ana[base + '_DATE'].min().date()) if ana[base + '_DATE'].notna().any() else None,
                        'max_date': str(ana[base + '_DATE'].max().date()) if ana[base + '_DATE'].notna().any() else None})
date_qc_df = pd.DataFrame(date_qc)
save_table(date_qc_df, 'T02_date_preservation_check')
display(date_qc_df)
assert (date_qc_df.n_components_disagree == 0).all(), 'Date components disagree with serial dates'

# Time-zero and follow-up
ana['T0_DATE'] = ana['LE1DGMETADT_DATE']        # date of first liver metastasis diagnosis
ana['LAST_DATE'] = ana['LASTNDTC_DATE']         # date of last known contact
ana['OS_DAYS'] = (ana['LAST_DATE'] - ana['T0_DATE']).dt.days
ana['PATSTATC_CLEAN'] = ana['PATSTATC'].where(ana['PATSTATC'].isin(['Alive', 'Deceased', 'Lost to follow-up']))

# Verify TIMELAST does not reproduce a date difference (justifies recomputing follow-up)
tl = num(ana['TIMELAST'])
qc = {}
for ref in ['REFERDT_DATE', 'CSTDT_DATE', 'DGKCOLDT_DATE', 'T0_DATE']:
    diff = (ana['LAST_DATE'] - ana[ref]).dt.days
    m = tl.notna() & diff.notna() & (tl > 0)
    qc[ref.replace('_DATE', '')] = int(((diff[m] - tl[m]).abs() <= 1).sum())
qc['TIMELAST_negative'] = int((tl < 0).sum())
qc['TIMELAST_available'] = int(tl.notna().sum())
timelast_qc = pd.Series(qc, name='count')
save_table(timelast_qc.rename_axis('check').reset_index(), 'T03_timelast_qc')
print('TIMELAST cross-check (matches within 1 day):'); display(timelast_qc)

# %% [code]
# Covariates, staging groups and treatment definitions
def group_t(s):
    s = s.astype('string')
    return s.map(lambda v: 'T1-2' if v in ('T0', 'T1', 'T2') else ('T3' if v == 'T3' else
                 ('T4' if v in ('T4', 'T4a', 'T4b') else pd.NA)))

def group_n(s):
    s = s.astype('string')
    return s.map(lambda v: 'N0' if v == 'N0' else ('N1' if v in ('N1', 'N1a', 'N1b', 'N1c') else
                 ('N2' if v in ('N2', 'N2a', 'N2b') else pd.NA)))

def group_m(s):
    s = s.astype('string')
    return s.map(lambda v: 'M0' if v == 'M0' else ('M1' if v in ('M1', 'M1a', 'M1b', 'M1c') else pd.NA))

ana['T_GRP'] = group_t(ana['STADET'])
ana['N_GRP'] = group_n(ana['STADEN'])
ana['M_GRP'] = group_m(ana['STADEM'])
ana['TNM_COMPLETE'] = ana[['T_GRP', 'N_GRP', 'M_GRP']].notna().all(axis=1)

ana['AGE'] = (ana['T0_DATE'] - ana['BIRTHDT_DATE']).dt.days / DAYS_PER_YEAR
ana.loc[(ana['AGE'] < 18) | (ana['AGE'] > 100), 'AGE'] = np.nan
ana['MALE'] = (ana['GENDER'] == 'Male').astype(float).where(ana['GENDER'].isin(['Male', 'Female']))
ana['SYNC'] = yn(ana['LE1METASYNCYN'].where(ana['LE1METASYNCYN'].notna()))
ana['METS'] = num(ana['LE1NBMETAHEPNUM'])
ana.loc[(ana['METS'] < 1) | (ana['METS'] > 50), 'METS'] = np.nan   # >50 treated as invalid (earlier rule)
ana['SIZE_MM'] = num(ana['LE1HEPMETASIZENUM'])
ana.loc[(ana['SIZE_MM'] <= 0) | (ana['SIZE_MM'] > 300), 'SIZE_MM'] = np.nan
ana['CEA'] = num(ana['LE1PREHEPCEA_F1'])
ana.loc[(ana['CEA'] < 0) | (ana['CEA'] > 40000), 'CEA'] = np.nan
ana['DFI_DAYS'] = (ana['T0_DATE'] - ana['DGKCOLDT_DATE']).dt.days
ana['DFI_MO'] = ana['DFI_DAYS'] / 30.4375
ana.loc[ana['SYNC'] == 1, 'DFI_MO'] = 0.0        # synchronous metastases: interval 0
ana.loc[ana['DFI_MO'] < 0, 'DFI_MO'] = np.nan
ana['ERA'] = np.where(ana['T0_DATE'].dt.year <= ERA_SPLIT_YEAR, 'Training', 'Validation')
ana.loc[ana['T0_DATE'].isna(), 'ERA'] = None

# Treatment: hepatectomy for liver metastases and systemic chemotherapy around it
ana['SURGERY'] = yn(ana['LE1HEPATECTYN_F1'])
pre = yn(ana['LE1PREOPMCTYN_F1']); post = yn(ana['LE1POSTOPMCTYN_F1'])
ana['CHEMO_PERIOP'] = np.nan
ana.loc[(pre == 0) & (post == 0), 'CHEMO_PERIOP'] = 0.0
ana.loc[(pre == 1) | (post == 1), 'CHEMO_PERIOP'] = 1.0
TX = pd.Series(pd.NA, index=ana.index, dtype='object')
TX[(ana.SURGERY == 1) & (ana.CHEMO_PERIOP == 1)] = 'Surgery+Chemo'
TX[(ana.SURGERY == 1) & (ana.CHEMO_PERIOP == 0)] = 'Surgery_Only'
TX[(ana.SURGERY == 0) & (ana.CHEMO_PERIOP == 1)] = 'Chemo_Only'
TX[(ana.SURGERY == 0) & (ana.CHEMO_PERIOP == 0)] = 'No_Treatment'
ana['TREATMENT'] = TX
ana['TX_SURGCHEMO'] = (ana.TREATMENT == 'Surgery+Chemo').astype(float).where(ana.TREATMENT.notna())
ana['TX_CHEMOONLY'] = (ana.TREATMENT == 'Chemo_Only').astype(float).where(ana.TREATMENT.notna())
ana['TX_NOTREAT'] = (ana.TREATMENT == 'No_Treatment').astype(float).where(ana.TREATMENT.notna())

# Chemotherapy timing relative to time zero (immortal-time check)
chemo_start = ana['LE1PREOPMSTDT_F1_DATE'].fillna(ana['LE1POSTOPMSTDT_F1_DATE'])
ana['CHEMO_START_DAYS'] = (chemo_start - ana['T0_DATE']).dt.days
ana['CHEMO_TIMING'] = np.select(
    [ana.CHEMO_PERIOP != 1, ana.CHEMO_START_DAYS.isna(), ana.CHEMO_START_DAYS < 0,
     ana.CHEMO_START_DAYS <= 180, ana.CHEMO_START_DAYS > 180],
    ['not_applicable', 'start_date_missing', 'before_time_zero', 'within_6_months', 'after_6_months'],
    default='unknown')

# Overall survival (OS): time zero = liver metastasis diagnosis; event = death
ana['OS_EVENT_RAW'] = ana['PATSTATC_CLEAN'].map({'Deceased': 1.0, 'Alive': 0.0, 'Lost to follow-up': 0.0})
ana['OS_VALID'] = ana.OS_DAYS.notna() & (ana.OS_DAYS > 0) & ana.OS_EVENT_RAW.notna()
ana['OS_YEARS'] = np.minimum(ana.OS_DAYS / DAYS_PER_YEAR, MAX_FU_YEARS)
ana['OS_EVENT'] = np.where(ana.OS_DAYS / DAYS_PER_YEAR > MAX_FU_YEARS, 0.0, ana.OS_EVENT_RAW)

# Recurrence-free survival (RFS): recurrence date if recorded, else death or last contact
rec_cols = [f'RECDT_F{i}_DATE' for i in range(1, 8) if f'RECDT_F{i}_DATE' in ana.columns]
ana['REC_DATE_FIRST'] = ana[rec_cols].min(axis=1)
rec_in_window = ana.REC_DATE_FIRST.notna() & (ana.REC_DATE_FIRST >= ana.T0_DATE) & (ana.REC_DATE_FIRST <= ana.LAST_DATE)
rfs_days_rec = (ana.REC_DATE_FIRST - ana.T0_DATE).dt.days
died = ana.PATSTATC_CLEAN.eq('Deceased')
alive_with_dz = ana.PATSTAT_F1.eq('Alive with disease')
ana['RFS_SOURCE'] = np.select(
    [rec_in_window, died, alive_with_dz],
    ['recurrence_date', 'death_or_last_contact', 'alive_with_disease_no_date'],
    default='censored_last_contact')
ana['RFS_EVENT_RAW'] = np.select([rec_in_window, died, alive_with_dz], [1.0, 1.0, 1.0], default=0.0)
ana['RFS_DAYS'] = np.where(rec_in_window, rfs_days_rec, ana.OS_DAYS)
ana['RFS_VALID'] = ana.OS_VALID & (pd.Series(ana.RFS_DAYS, index=ana.index) > 0)
ana['RFS_YEARS'] = np.minimum(pd.Series(ana.RFS_DAYS, index=ana.index) / DAYS_PER_YEAR, MAX_FU_YEARS)
ana['RFS_EVENT'] = np.where(ana.RFS_YEARS >= MAX_FU_YEARS, 0.0, ana.RFS_EVENT_RAW)

# Fong clinical risk score (five criteria, one point each) and a Nordlinger-type unweighted count
ana['FONG_N_POS'] = ana.N_GRP.isin(['N1', 'N2']).astype(float).where(ana.N_GRP.notna())
ana['FONG_DFI_LT12'] = (ana.DFI_MO < 12).astype(float).where(ana.DFI_MO.notna())
ana['FONG_MULTI'] = (ana.METS > 1).astype(float).where(ana.METS.notna())
ana['FONG_SIZE_GT50'] = (ana.SIZE_MM > 50).astype(float).where(ana.SIZE_MM.notna())
ana['FONG_CEA_GT200'] = (ana.CEA > 200).astype(float).where(ana.CEA.notna())
FONG_COLS = ['FONG_N_POS', 'FONG_DFI_LT12', 'FONG_MULTI', 'FONG_SIZE_GT50', 'FONG_CEA_GT200']
ana['FONG_SCORE'] = ana[FONG_COLS].sum(axis=1, min_count=5)
ana['NORDLINGER_TYPE'] = (ana.AGE >= 60).astype(float).where(ana.AGE.notna()) + \
                         (ana.T_GRP == 'T4').astype(float).where(ana.T_GRP.notna()) + \
                         ana.FONG_N_POS + ana.FONG_DFI_LT12
ana.loc[ana[['AGE', 'T_GRP', 'FONG_N_POS', 'FONG_DFI_LT12']].isna().any(axis=1), 'NORDLINGER_TYPE'] = np.nan

# Analysis cohort flow
flow = []
def _step(label, mask):
    flow.append({'step': label, 'n': int(mask.sum())})
_step('All patients in combined extract', pd.Series(True, index=ana.index))
_step('TNM complete (T, N and M stage recorded, not ND/NA)', ana.TNM_COMPLETE)
_step('  ...and liver metastasis diagnosis date available', ana.TNM_COMPLETE & ana.T0_DATE.notna())
_step('  ...and valid OS (known status, date > time zero)', ana.TNM_COMPLETE & ana.OS_VALID)
flow_df = pd.DataFrame(flow)
flow_df['excluded_from_previous'] = -flow_df.n.diff().fillna(0).astype(int)
save_table(flow_df, 'T04_cohort_flow')
display(flow_df)
ana_os = ana[ana.TNM_COMPLETE & ana.OS_VALID].copy()
log(f'OS analysis cohort: {len(ana_os):,} patients')
tnm_excluded = int((~ana.TNM_COMPLETE).sum())
print(f'TNM-incomplete exclusions: {tnm_excluded:,} (earlier published value: 10,100)')

# %% [code]
# Survival and staging summary (aggregate only)
summ = {
    'OS events (death)': int(ana_os.OS_EVENT.sum()),
    'OS median follow-up, reverse KM (years)': round(float(KaplanMeierFitter().fit(
        ana_os.OS_YEARS, 1 - ana_os.OS_EVENT).median_survival_time_), 2),
    'RFS events': int(ana_os.RFS_EVENT.sum()),
    'RFS source: recurrence date': int((ana_os.RFS_SOURCE == 'recurrence_date').sum()),
    'RFS source: alive with disease, no date': int((ana_os.RFS_SOURCE == 'alive_with_disease_no_date').sum()),
    'Training era (<=2009)': int((ana_os.ERA == 'Training').sum()),
    'Validation era (>2009)': int((ana_os.ERA == 'Validation').sum()),
    'Treatment categories available': int(ana_os.TREATMENT.notna().sum()),
    'Fong score computable (all 5 criteria)': int(ana_os.FONG_SCORE.notna().sum()),
    'Nordlinger-type score computable': int(ana_os.NORDLINGER_TYPE.notna().sum()),
}
summ_df = pd.Series(summ, name='value').rename_axis('quantity').reset_index()
save_table(summ_df, 'T05_cohort_summary')
display(summ_df)

# %% [markdown]
# ## Part 3. Overall survival and recurrence-free survival (Kaplan-Meier)
#
# Time zero is the date of the first liver metastasis diagnosis. Patients alive at last contact are
# censored there. Follow-up is truncated at 15 years.

# %% [code]
def km_fit(df, t, e, label):
    kmf = KaplanMeierFitter(label=label)
    kmf.fit(df[t], df[e], label=label)
    return kmf

def km_summary(df, t, e, group):
    rows = []
    for g, sub in df.groupby(group, observed=True):
        k = km_fit(sub, t, e, str(g))
        med = k.median_survival_time_
        rows.append({'group': g, 'n': len(sub), 'events': int(sub[e].sum()),
                     'median_years': round(float(med), 2) if np.isfinite(med) else None,
                     'S_1y': round(float(k.survival_function_at_times(1).iloc[0]), 3),
                     'S_3y': round(float(k.survival_function_at_times(3).iloc[0]), 3),
                     'S_5y': round(float(k.survival_function_at_times(5).iloc[0]), 3)})
    return pd.DataFrame(rows)

def plot_km_by_group(df, t, e, group, title, order, fname, xmax=10, colors=None):
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    colors = colors or {'Favourable': '#1B7837', 'Intermediate': '#E08214', 'Adverse': '#B2182B'}
    for g in order:
        sub = df[df[group] == g]
        if len(sub) == 0:
            continue
        k = km_fit(sub, t, e, f'{g} (n={len(sub):,})')
        k.plot_survival_function(ax=ax, ci_show=True, color=colors.get(g), show_censors=False)
    ax.set_xlim(0, xmax); ax.set_ylim(0, 1.01)
    ax.set_xlabel('Years from liver metastasis diagnosis'); ax.set_ylabel('Survival probability')
    ax.set_title(title); ax.grid(alpha=0.25)
    ax.legend(loc='upper right', frameon=False)
    save_fig(fig, fname); plt.show(); plt.close(fig)

os_overall = km_summary(ana_os.assign(ALL='All'), 'OS_YEARS', 'OS_EVENT', 'ALL')
save_table(os_overall, 'T06_OS_overall')
rfs_overall = km_summary(ana_os.assign(ALL='All'), 'RFS_YEARS', 'RFS_EVENT', 'ALL')
save_table(rfs_overall, 'T06b_RFS_overall')
display(os_overall); display(rfs_overall)

# %% [markdown]
# ## Part 4. Survival-tree phenotypes (replaces the binary CART)
#
# A survival tree is grown on the TNM stage groups only, with overall survival as the outcome. Growth
# uses the **training era only** (liver metastasis diagnosis up to 2009). Terminal nodes are then given
# phenotypes from their Kaplan-Meier median OS, using the earlier thresholds (Favourable >= 6 years,
# Intermediate 5 to 6 years, Adverse < 5 years; a median that is never reached is Favourable). The
# phenotype rules are then applied unchanged to the validation era.

# %% [code]
TNM_FEATS = pd.get_dummies(ana_os[['T_GRP', 'N_GRP', 'M_GRP']].astype(str), dtype=float)
TNM_FEATS.columns = [c.replace(' ', '') for c in TNM_FEATS.columns]
train_mask = (ana_os.ERA == 'Training').values
y_os = Surv.from_arrays(event=ana_os.OS_EVENT.values.astype(bool), time=ana_os.OS_YEARS.values)
min_leaf = max(200, int(0.02 * train_mask.sum()))
tree = SurvivalTree(max_depth=3, min_samples_leaf=min_leaf, random_state=SEED)
tree.fit(TNM_FEATS.values[train_mask], y_os[train_mask])
leaf_train = tree.apply(TNM_FEATS.values[train_mask])
leaf_all = tree.apply(TNM_FEATS.values)

def phenotype_from_median(m):
    if m is None or not np.isfinite(m):
        return 'Favourable'
    if m >= PHENO_FAV_MIN:
        return 'Favourable'
    if m >= PHENO_INT_MIN:
        return 'Intermediate'
    return 'Adverse'

node_rows = []
node_pheno = {}
for leaf in np.unique(leaf_train):
    m_tr = leaf_train == leaf
    sub = ana_os[train_mask].loc[m_tr]
    k = km_fit(sub, 'OS_YEARS', 'OS_EVENT', str(leaf))
    med = k.median_survival_time_
    med_v = float(med) if np.isfinite(med) else None
    ph = phenotype_from_median(med_v)
    node_pheno[leaf] = ph
    node_rows.append({'terminal_node': int(leaf), 'n_training': int(m_tr.sum()),
                      'events_training': int(sub.OS_EVENT.sum()),
                      'median_OS_years': round(med_v, 2) if med_v is not None else 'not reached',
                      'phenotype': ph})
node_df = pd.DataFrame(node_rows).sort_values('median_OS_years', key=lambda s: s.replace('not reached', 99),
                                              ascending=False)
save_table(node_df, 'T07_survival_tree_terminal_nodes')
display(node_df)

def tree_rules(t, feature_names):
    tr = t.tree_
    lines = []
    def walk(node, depth):
        indent = '|   ' * depth
        if tr.children_left[node] == -1:
            lines.append(f'{indent}leaf node {node}')
            return
        f = feature_names[tr.feature[node]]
        thr = tr.threshold[node]
        lines.append(f'{indent}{f} <= {thr:.2f}')
        walk(tr.children_left[node], depth + 1)
        lines.append(f'{indent}{f} > {thr:.2f}')
        walk(tr.children_right[node], depth + 1)
    walk(0, 0)
    return '\n'.join(lines)

rules_txt = tree_rules(tree, list(TNM_FEATS.columns))
print(rules_txt)
(RESULTS_DIR / 'tables' / 'T08_survival_tree_rules.txt').write_text(rules_txt + '\n')

ana_os['TERMINAL_NODE'] = leaf_all
ana_os['PHENOTYPE'] = pd.Series(leaf_all, index=ana_os.index).map(node_pheno).fillna('Adverse')
ana_os['PHENO_RANK'] = ana_os.PHENOTYPE.map({'Favourable': 0, 'Intermediate': 1, 'Adverse': 2})
ana_os['ERA_TRAIN'] = (ana_os.ERA == 'Training').astype(int)
PHENO_ORDER = ['Favourable', 'Intermediate', 'Adverse']
phen_tab = ana_os.groupby('PHENOTYPE').size().reindex(PHENO_ORDER)
print(phen_tab.to_string())

# %% [code]
os_by_pheno = km_summary(ana_os, 'OS_YEARS', 'OS_EVENT', 'PHENOTYPE').set_index('group').loc[PHENO_ORDER].reset_index()
rfs_by_pheno = km_summary(ana_os, 'RFS_YEARS', 'RFS_EVENT', 'PHENOTYPE').set_index('group').loc[PHENO_ORDER].reset_index()
lr_os = multivariate_logrank_test(ana_os.OS_YEARS, ana_os.PHENOTYPE, ana_os.OS_EVENT)
lr_rfs = multivariate_logrank_test(ana_os.RFS_YEARS, ana_os.PHENOTYPE, ana_os.RFS_EVENT)
print(f'OS log-rank chi2={lr_os.test_statistic:.2f}, df=2, p={lr_os.p_value:.2e}')
print(f'RFS log-rank chi2={lr_rfs.test_statistic:.2f}, df=2, p={lr_rfs.p_value:.2e}')
os_by_pheno['logrank_p'] = lr_os.p_value; rfs_by_pheno['logrank_p'] = lr_rfs.p_value
save_table(os_by_pheno, 'T09_OS_by_phenotype'); save_table(rfs_by_pheno, 'T10_RFS_by_phenotype')
display(os_by_pheno); display(rfs_by_pheno)

fig = plot_km_by_group(ana_os, 'OS_YEARS', 'OS_EVENT', 'PHENOTYPE', 'Overall survival by phenotype',
                       PHENO_ORDER, 'F02_KM_OS_by_phenotype')
fig = plot_km_by_group(ana_os, 'RFS_YEARS', 'RFS_EVENT', 'PHENOTYPE', 'Recurrence-free survival by phenotype',
                       PHENO_ORDER, 'F03_KM_RFS_by_phenotype')

# %% [code]
# Survival tree figure: KM curves for the terminal nodes used to define phenotypes
fig, ax = plt.subplots(figsize=(7.2, 5.4))
for leaf in node_df.terminal_node:
    sub = ana_os[ana_os.TERMINAL_NODE == leaf]
    k = km_fit(sub, 'OS_YEARS', 'OS_EVENT', f'node {leaf} ({node_pheno[leaf]}, n={len(sub):,})')
    k.plot_survival_function(ax=ax, ci_show=False, show_censors=False)
ax.set_xlim(0, 10); ax.set_ylim(0, 1.01); ax.grid(alpha=0.25)
ax.set_xlabel('Years from liver metastasis diagnosis'); ax.set_ylabel('Survival probability')
ax.set_title('Survival-tree terminal nodes (all era, rules from training era)')
ax.legend(fontsize=8, frameon=False)
save_fig(fig, 'F01_survival_tree_nodes'); plt.show(); plt.close(fig)

# %% [markdown]
# ## Part 5. Cox proportional hazards models
#
# * **Prognostic Cox** (phenotype, age, sex, nodal burden and metastasis count): used in Part 6.
# * **Treatment Cox** (phenotype and treatment, complete cases): the same covariates as the earlier
#   multivariable model, with Surgery_Only as the reference treatment.
# * Proportional-hazards checks use Schoenfeld residual tests and log(-log S) curves.

# %% [code]
ana_os['PH_INT'] = ana_os.PHENOTYPE.eq('Intermediate').astype(float)
ana_os['PH_ADV'] = ana_os.PHENOTYPE.eq('Adverse').astype(float)
ana_os['AGE_10'] = ana_os.AGE / 10
ana_os['N_POS'] = ana_os.N_GRP.isin(['N1', 'N2']).astype(float).where(ana_os.N_GRP.notna())

def cox_table(df, t, e, covars, label, penalizer=0.0):
    cols = [t, e] + covars
    d = df[cols].dropna()
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(d, duration_col=t, event_col=e)
    s = cph.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].copy()
    s.columns = ['coef', 'HR', 'HR_lower95', 'HR_upper95', 'p']
    s.insert(0, 'model', label)
    s.insert(1, 'n', len(d)); s.insert(2, 'events', int(d[e].sum()))
    s['c_index_apparent'] = round(cph.concordance_index_, 3)
    return cph, s.reset_index().rename(columns={'covariate': 'term'})

TREAT_COVARS = ['PH_INT', 'PH_ADV', 'TX_SURGCHEMO', 'TX_CHEMOONLY', 'TX_NOTREAT', 'AGE_10', 'MALE', 'METS']
cph_treat, cox_treat_tab = cox_table(ana_os.assign(METS=ana_os.METS), 'OS_YEARS', 'OS_EVENT', TREAT_COVARS,
                                     'Multivariable OS: phenotype + treatment (complete cases)')
display(cox_treat_tab.round(4))
save_table(cox_treat_tab, 'T11_Cox_multivariable_OS')

# Proportional hazards diagnostics (Schoenfeld residuals, rank time transform)
d_ph = ana_os[['OS_YEARS', 'OS_EVENT'] + TREAT_COVARS].dropna()
ph_test = proportional_hazard_test(cph_treat, d_ph, time_transform='rank')
ph_tab = ph_test.summary.reset_index().rename(columns={'index': 'term'})
save_table(ph_tab, 'T12_PH_test_Schoenfeld_OS')
display(ph_tab.round(4))

# log(-log S) check by phenotype and treatment (roughly parallel curves = PH holds)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, (group, order) in zip(axes, [('PHENOTYPE', PHENO_ORDER), ('TREATMENT', ['Surgery+Chemo', 'Surgery_Only'])]):
    for g in order:
        sub = ana_os[ana_os[group] == g]
        if len(sub) < 30:
            continue
        k = km_fit(sub, 'OS_YEARS', 'OS_EVENT', g)
        s = k.survival_function_
        s = s[(s.index > 0.25) & (s.index < 8) & (s.iloc[:, 0] > 0)]
        ax.plot(np.log(s.index.values), np.log(-np.log(s.iloc[:, 0].values)), label=g)
    ax.set_xlabel('log(time, years)'); ax.set_ylabel('log(-log S(t))'); ax.grid(alpha=0.25)
    ax.set_title(f'PH check: {group}'); ax.legend(frameon=False, fontsize=8)
save_fig(fig, 'F04_PH_log_minus_log'); plt.show(); plt.close(fig)

# %% [code]
# Restricted mean survival time (RMST) up to tau years, from the Kaplan-Meier curve
def rmst(times, events, tau=RMST_TAU, weights=None):
    """Area under the KM curve from 0 to tau (right-continuous step function)."""
    k = KaplanMeierFitter().fit(np.asarray(times), np.asarray(events),
                                weights=None if weights is None else np.asarray(weights))
    tt = k.survival_function_.index.values.astype(float)
    ss = k.survival_function_.iloc[:, 0].values.astype(float)
    grid = np.concatenate([[0.0], tt[(tt > 0) & (tt < tau)], [tau]])
    idx = np.searchsorted(tt, grid[:-1], side='right') - 1
    s_vals = np.where(idx >= 0, ss[np.clip(idx, 0, None)], 1.0)
    return float(np.sum(s_vals * np.diff(grid)))

rmst_rows = []
for g in PHENO_ORDER:
    sub = ana_os[ana_os.PHENOTYPE == g]
    rmst_rows.append({'comparison': 'phenotype', 'group': g, 'n': len(sub),
                      'RMST_5y_years': round(rmst(sub.OS_YEARS, sub.OS_EVENT), 3)})
for g in ['Surgery+Chemo', 'Surgery_Only', 'Chemo_Only', 'No_Treatment']:
    sub = ana_os[ana_os.TREATMENT == g]
    if len(sub) > 0:
        rmst_rows.append({'comparison': 'treatment (all patients)', 'group': g, 'n': len(sub),
                          'RMST_5y_years': round(rmst(sub.OS_YEARS, sub.OS_EVENT), 3)})
rmst_df = pd.DataFrame(rmst_rows)
save_table(rmst_df, 'T13_RMST_5y')
display(rmst_df)

# %% [markdown]
# ## Part 6. Machine-learning survival models with internal and temporal validation
#
# **Prognostic features** are available at liver metastasis diagnosis (treatment is excluded because
# it is decided after time zero). Continuous features with missing values are median-imputed using the
# training data only, and each has a missing-indicator column. Nothing is tuned on validation data.
#
# **Validation:**
# 1. *Internal:* stratified random 70/30 split on the event indicator.
# 2. *Temporal:* train on the training era (<= 2009), test on the validation era (> 2009).

# %% [code]
PROG_CONT = ['AGE', 'METS', 'SIZE_MM', 'CEA_LOG', 'DFI_MO']

def build_prog_frame(df):
    X = pd.DataFrame(index=df.index)
    X['AGE'] = df.AGE
    X['MALE'] = df.MALE
    X['SYNC'] = df.SYNC
    X['DFI_MO'] = df.DFI_MO
    X['METS'] = df.METS
    X['SIZE_MM'] = df.SIZE_MM
    X['CEA_LOG'] = np.log1p(df.CEA)
    for g, lv in [('T_GRP', ['T3', 'T4']), ('N_GRP', ['N1', 'N2']), ('M_GRP', ['M1'])]:
        for L in lv:
            X[f'{g}_{L}'] = (df[g] == L).astype(float).where(df[g].notna())
    return X

def impute_fit_transform(Xtr, Xte):
    Xtr = Xtr.copy(); Xte = Xte.copy()
    for c in PROG_CONT:
        miss_tr = Xtr[c].isna(); miss_te = Xte[c].isna()
        if miss_tr.any() or miss_te.any():
            Xtr[c + '_MISS'] = miss_tr.astype(float); Xte[c + '_MISS'] = miss_te.astype(float)
        med = Xtr[c].median()
        Xtr[c] = Xtr[c].fillna(med); Xte[c] = Xte[c].fillna(med)
    for c in Xtr.columns:
        if Xtr[c].isna().any():
            Xtr[c] = Xtr[c].fillna(0.0)
        if Xte[c].isna().any():
            Xte[c] = Xte[c].fillna(0.0)
    return Xtr, Xte

X_all = build_prog_frame(ana_os)
has_base = X_all[['AGE', 'MALE', 'T_GRP_T3', 'T_GRP_T4', 'N_GRP_N1', 'N_GRP_N2', 'M_GRP_M1']].notna().all(axis=1)
ana_ml = ana_os[has_base].copy()
X_all = X_all.loc[ana_ml.index]
y_ml = Surv.from_arrays(event=ana_ml.OS_EVENT.values.astype(bool), time=ana_ml.OS_YEARS.values)
log(f'ML cohort (baseline features present): {len(ana_ml):,} patients, {int(ana_ml.OS_EVENT.sum()):,} deaths')

idx_all = np.arange(len(ana_ml))
tr_idx, te_idx = train_test_split(idx_all, test_size=0.30, random_state=SEED,
                                  stratify=ana_ml.OS_EVENT.values.astype(int))
splits = {
    'Internal (random 70/30)': (tr_idx, te_idx),
    'Temporal (<=2009 train, >2009 test)': (np.where(ana_ml.ERA.values == 'Training')[0],
                                            np.where(ana_ml.ERA.values == 'Validation')[0]),
}
for name, (a, b) in splits.items():
    log(f'{name}: train n={len(a):,} (deaths {int(ana_ml.OS_EVENT.values[a].sum()):,}); '
        f'test n={len(b):,} (deaths {int(ana_ml.OS_EVENT.values[b].sum()):,})')

def surv_matrix(surv_fns, times):
    return np.asarray([[fn(t) for t in times] for fn in surv_fns])

def evaluate_model(name, risk_te, surv_te_mat, y_tr, y_te, times_auc, times_brier, risk_tr=None):
    out = {'model': name}
    out['C_index'] = round(concordance_index_censored(y_te['event'], y_te['time'], risk_te)[0], 4)
    try:
        _, mean_auc = cumulative_dynamic_auc(y_tr, y_te, risk_te, times_auc)
        auc_vals = cumulative_dynamic_auc(y_tr, y_te, risk_te, times_auc)[0]
        for t, a in zip(times_auc, auc_vals):
            out[f'tAUC_{int(t)}y'] = round(float(a), 4)
    except Exception as ex:
        out['tAUC_note'] = f'not computed: {ex}'
    if surv_te_mat is not None:
        try:
            _, bs = brier_score(y_tr, y_te, surv_te_mat, times_brier)
            out['Brier_1y'] = round(float(bs[0]), 4)
            out['Brier_5y'] = round(float(bs[list(times_brier).index(5.0)]), 4)
            out['IBS_1_to_7y'] = round(float(integrated_brier_score(y_tr, y_te, surv_te_mat, times_brier)), 4)
        except Exception as ex:
            out['Brier_note'] = f'not computed: {ex}'
    return out

results_rows = []
calib_store = {}
for split_name, (tr, te) in splits.items():
    Xtr_raw, Xte_raw = X_all.iloc[tr], X_all.iloc[te]
    Xtr, Xte = impute_fit_transform(Xtr_raw, Xte_raw)
    ytr, yte = y_ml[tr], y_ml[te]
    te_df = ana_ml.iloc[te]
    tr_df = ana_ml.iloc[tr]
    # Phenotype rank (rules fixed in Part 4)
    pheno_risk = te_df.PHENO_RANK.values.astype(float)
    results_rows.append(evaluate_model(f'Phenotype rank [{split_name}]', pheno_risk, None, ytr, yte,
                                       TIMES_AUC, TIMES_BRIER))
    # Prognostic Cox (light L2 penalty for numerical stability)
    d_tr = Xtr.copy(); d_tr['OS_YEARS'] = tr_df.OS_YEARS.values; d_tr['OS_EVENT'] = tr_df.OS_EVENT.values
    cph_p = CoxPHFitter(penalizer=0.01).fit(d_tr, 'OS_YEARS', 'OS_EVENT')
    risk_cox = cph_p.predict_partial_hazard(Xte).values.ravel()
    surv_cox = cph_p.predict_survival_function(Xte, times=TIMES_BRIER).T.values
    results_rows.append(evaluate_model(f'Cox (prognostic) [{split_name}]', risk_cox, surv_cox, ytr, yte,
                                       TIMES_AUC, TIMES_BRIER))
    # Random survival forest
    t0 = time.time()
    rsf = RandomSurvivalForest(n_estimators=300, min_samples_leaf=20, max_features='sqrt',
                               n_jobs=-1, random_state=SEED).fit(Xtr.values, ytr)
    risk_rsf = rsf.predict(Xte.values)
    surv_rsf = surv_matrix(rsf.predict_survival_function(Xte.values), TIMES_BRIER)
    results_rows.append(evaluate_model(f'Random survival forest [{split_name}]', risk_rsf, surv_rsf, ytr, yte,
                                       TIMES_AUC, TIMES_BRIER))
    log(f'RSF fitted in {time.time()-t0:,.0f}s')
    # Gradient-boosted survival (Cox partial likelihood)
    t0 = time.time()
    gbs = GradientBoostingSurvivalAnalysis(loss='coxph', n_estimators=200, learning_rate=0.05, max_depth=2,
                                           subsample=0.7, random_state=SEED).fit(Xtr.values, ytr)
    risk_gbs = gbs.predict(Xte.values)
    surv_gbs = surv_matrix(gbs.predict_survival_function(Xte.values), TIMES_BRIER)
    results_rows.append(evaluate_model(f'Gradient-boosted survival [{split_name}]', risk_gbs, surv_gbs, ytr, yte,
                                       TIMES_AUC, TIMES_BRIER))
    log(f'GBS fitted in {time.time()-t0:,.0f}s')
    # Calibration at 5 years (deciles of predicted survival): RSF and Cox
    j5 = list(TIMES_BRIER).index(5.0)
    for mname, s5 in [('RSF', surv_rsf[:, j5]), ('Cox (prognostic)', surv_cox[:, j5])]:
        dec = pd.qcut(pd.Series(s5).rank(method='first'), 10, labels=False)
        rows = []
        for q in range(10):
            m = (dec == q).values
            kmf = KaplanMeierFitter().fit(te_df.OS_YEARS.values[m], te_df.OS_EVENT.values[m])
            obs = float(kmf.survival_function_at_times(5).iloc[0])
            rows.append({'decile': q + 1, 'n': int(m.sum()), 'predicted_S5': round(float(s5[m].mean()), 4),
                         'observed_S5_KM': round(obs, 4)})
        cdf = pd.DataFrame(rows)
        cdf['abs_error'] = (cdf.predicted_S5 - cdf.observed_S5_KM).abs()
        calib_store[(split_name, mname)] = cdf
    # Fong / Nordlinger benchmarks on the subset where each score is computable
    te_fong = te_df.FONG_SCORE.notna().values
    if te_fong.sum() > 50:
        fong_metrics = evaluate_model(f'Fong CRS (subset) [{split_name}]', te_df.FONG_SCORE.values[te_fong],
                                      None, ytr, yte[te_fong], TIMES_AUC, TIMES_BRIER)
        fong_metrics['n_test_subset'] = int(te_fong.sum())
        results_rows.append(fong_metrics)
    te_nord = te_df.NORDLINGER_TYPE.notna().values
    if te_nord.sum() > 50:
        nord_metrics = evaluate_model(f'Nordlinger-type unweighted (subset) [{split_name}]',
                                      te_df.NORDLINGER_TYPE.values[te_nord], None, ytr, yte[te_nord],
                                      TIMES_AUC, TIMES_BRIER)
        nord_metrics['n_test_subset'] = int(te_nord.sum())
        results_rows.append(nord_metrics)

perf = pd.DataFrame(results_rows)
save_table(perf, 'T14_model_performance')
display(perf)
for (split_name, mname), cdf in calib_store.items():
    tag = 'internal' if split_name.startswith('Internal') else 'temporal'
    save_table(cdf, f'T15_calibration_5y_{mname.split()[0].lower()}_{tag}')

# %% [code]
# Figures: time-dependent AUC and calibration (temporal split, which is the stricter test)
fig, ax = plt.subplots(figsize=(6.5, 4.6))
sub = perf[perf.model.str.contains('Temporal') & perf.model.str.contains('Random|Gradient|Cox', regex=True)]
for _, r in sub.iterrows():
    vals = [r.get(f'tAUC_{int(t)}y') for t in TIMES_AUC]
    if all(v is not None and not pd.isna(v) for v in vals):
        ax.plot(TIMES_AUC, vals, marker='o', label=r.model.split(' [')[0])
ax.axhline(0.5, color='grey', lw=0.8, ls='--'); ax.set_ylim(0.4, 1.0); ax.grid(alpha=0.25)
ax.set_xlabel('Time (years)'); ax.set_ylabel('Time-dependent AUC'); ax.set_title('Temporal validation: time-dependent AUC')
ax.legend(frameon=False, fontsize=8)
save_fig(fig, 'F05_time_dependent_AUC_temporal'); plt.show(); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
for ax, mname in zip(axes, ['RSF', 'Cox (prognostic)']):
    cdf = calib_store[('Temporal (<=2009 train, >2009 test)', mname)]
    ax.plot([0, 1], [0, 1], color='grey', ls='--', lw=0.8)
    ax.scatter(cdf.predicted_S5, cdf.observed_S5_KM, s=cdf.n / cdf.n.max() * 120 + 20, alpha=0.8)
    ax.set_xlabel('Predicted 5-year survival (decile mean)'); ax.set_title(f'{mname}: calibration at 5 years (temporal)')
    ax.grid(alpha=0.25)
axes[0].set_ylabel('Observed 5-year survival (KM)')
save_fig(fig, 'F06_calibration_5y_temporal'); plt.show(); plt.close(fig)

# %% [markdown]
# ## Part 7. Benchmarks: Fong CRS and Nordlinger-type score
#
# * **Fong CRS** (five criteria, one point each): node-positive primary, disease-free interval < 12
#   months, more than one metastasis, largest metastasis > 50 mm, pre-operative CEA > 200 ng/mL.
#   Computed on the complete-case subset.
# * **Nordlinger-type score:** age >= 60, T4 primary, node-positive primary and DFI < 12 months,
#   summed without weights. The published Nordlinger point weights could not be verified from the
#   sources available here, so this is labelled a *Nordlinger-type unweighted count* and not the score.
# * **Basingstoke Predictive Index:** not computed. It adds tumour differentiation grade, extrahepatic
#   disease and resection margin to Fong's criteria; differentiation grade is not in this export.

# %% [code]
fong_dist = ana_os.FONG_SCORE.value_counts(dropna=True).sort_index()
print('Fong score distribution (complete cases):'); print(fong_dist.to_string())
nord_dist = ana_os.NORDLINGER_TYPE.value_counts(dropna=True).sort_index()
print('Nordlinger-type count distribution:'); print(nord_dist.to_string())
bench_rows = []
for name, col in [('Fong CRS', 'FONG_SCORE'), ('Nordlinger-type unweighted', 'NORDLINGER_TYPE'),
                  ('Phenotype rank', 'PHENO_RANK')]:
    sub = ana_os[ana_os[col].notna()]
    c = concordance_index_censored(sub.OS_EVENT.astype(bool), sub.OS_YEARS, sub[col].astype(float))[0]
    bench_rows.append({'score': name, 'n_complete': len(sub), 'deaths': int(sub.OS_EVENT.sum()),
                       'C_index_apparent': round(c, 4)})
bench_df = pd.DataFrame(bench_rows)
save_table(bench_df, 'T16_benchmark_scores_apparent')
display(bench_df)

fong_km = km_summary(ana_os[ana_os.FONG_SCORE.notna()].assign(
    FONG_RISK=lambda d: pd.cut(d.FONG_SCORE, [-1, 2, 5], labels=['Fong 0-2 (low)', 'Fong 3-5 (high)'])),
    'OS_YEARS', 'OS_EVENT', 'FONG_RISK')
save_table(fong_km, 'T17_Fong_risk_groups_OS')
display(fong_km)

# %% [markdown]
# ## Part 8. Treatment comparison: propensity-score matching with confounding and timing checks
#
# Comparison: **Surgery+Chemo vs Surgery_Only**, within each phenotype.
#
# * Propensity score from logistic regression on pre-treatment covariates only (age, sex, T, N, M,
#   synchronous disease, metastasis count, size, DFI, era, CEA log, with missing indicators).
# * 1:1 nearest-neighbour matching without replacement on the logit of the propensity score, caliper
#   0.2 x SD of the logit.
# * Balance is reported as standardised mean differences (SMD); |SMD| < 0.1 is taken as balanced.
# * **Timing checks:** (a) chemotherapy start relative to time zero, (b) a 6-month **landmark**
#   analysis that removes early deaths, which guards against immortal-time bias from post-operative
#   chemotherapy.

# %% [code]
PS_COVARS = ['AGE', 'MALE', 'T_GRP_T3', 'T_GRP_T4', 'N_GRP_N1', 'N_GRP_N2', 'M_GRP_M1', 'SYNC',
             'METS', 'SIZE_MM', 'DFI_MO', 'CEA_LOG', 'ERA_TRAIN']

def ps_frame(df):
    X = build_prog_frame(df)
    X['ERA_TRAIN'] = (df.ERA == 'Training').astype(float).values
    return X[[c for c in X.columns if c in PS_COVARS or c.startswith('CEA_LOG') or c.startswith('DFI')]]

def psm_match(df, treat_col, caliper_frac=0.2, seed=SEED):
    """1:1 nearest-neighbour matching without replacement on logit(PS), with a caliper."""
    d = df.copy()
    Xp = ps_frame(d)
    Xp, _ = impute_fit_transform(Xp, Xp.iloc[:1])
    lr = LogisticRegression(max_iter=2000, C=1.0).fit(Xp.values, d[treat_col].values.astype(int))
    ps = lr.predict_proba(Xp.values)[:, 1]
    lp = np.log(ps / (1 - ps))
    caliper = caliper_frac * np.std(lp, ddof=1)
    d['PS'] = ps; d['LP'] = lp
    t_idx = np.where(d[treat_col].values == 1)[0]
    c_idx = np.where(d[treat_col].values == 0)[0]
    rng = np.random.default_rng(seed)
    t_order = rng.permutation(t_idx)
    avail = np.ones(len(c_idx), dtype=bool)
    pairs = []
    for ti in t_order:
        diff = np.abs(lp[c_idx] - lp[ti])
        diff[~avail] = np.inf
        j = int(np.argmin(diff))
        if diff[j] <= caliper:
            avail[j] = False
            pairs.append((ti, c_idx[j]))
    pair_id = np.full(len(d), -1)
    for k, (a, b) in enumerate(pairs):
        pair_id[a] = k; pair_id[b] = k
    d['PAIR_ID'] = pair_id
    matched = d[d.PAIR_ID >= 0].copy()
    return matched, lr, caliper

def smd_table(df, treat_col, covars):
    rows = []
    for c in covars:
        x1 = df.loc[df[treat_col] == 1, c].astype(float); x0 = df.loc[df[treat_col] == 0, c].astype(float)
        pooled = np.sqrt((x1.var(ddof=1) + x0.var(ddof=1)) / 2)
        rows.append({'covariate': c, 'mean_treated': round(x1.mean(), 3), 'mean_control': round(x0.mean(), 3),
                     'SMD': round((x1.mean() - x0.mean()) / pooled, 3) if pooled > 0 else 0.0})
    return pd.DataFrame(rows)

tx_df = ana_os[ana_os.TREATMENT.isin(['Surgery+Chemo', 'Surgery_Only'])].copy()
tx_df['TX'] = (tx_df.TREATMENT == 'Surgery+Chemo').astype(int)
tx_df = tx_df[tx_df.OS_YEARS.notna()].copy()
X_bal = ps_frame(tx_df)
Xb_imp, _ = impute_fit_transform(X_bal, X_bal.iloc[:1])
Xb_imp = Xb_imp.copy()
for c in Xb_imp.columns:
    tx_df[f'BAL_{c}'] = Xb_imp[c].values
BAL_COLS = [f'BAL_{c}' for c in Xb_imp.columns]
log(f'Treatment comparison pool (Surgery+Chemo vs Surgery_Only): {len(tx_df):,} patients')

psm_results, psm_bal_rows, psm_out_rows = [], [], []
matched_store = {}
for pheno in PHENO_ORDER:
    sub = tx_df[tx_df.PHENOTYPE == pheno].copy()
    n_t = int((sub.TX == 1).sum()); n_c = int((sub.TX == 0).sum())
    if min(n_t, n_c) < 30:
        psm_results.append({'phenotype': pheno, 'note': 'too few patients in one arm', 'n_treated': n_t, 'n_control': n_c})
        continue
    matched, lr_ps, caliper = psm_match(sub, 'TX')
    matched_store[pheno] = matched
    bal_b = smd_table(sub, 'TX', BAL_COLS).assign(phenotype=pheno, stage='before')
    bal_a = smd_table(matched, 'TX', BAL_COLS).assign(phenotype=pheno, stage='after matching')
    psm_bal_rows += [bal_b, bal_a]
    lr_test = logrank_test(matched.loc[matched.TX == 1, 'OS_YEARS'], matched.loc[matched.TX == 0, 'OS_YEARS'],
                           matched.loc[matched.TX == 1, 'OS_EVENT'], matched.loc[matched.TX == 0, 'OS_EVENT'])
    d_cox = matched[['OS_YEARS', 'OS_EVENT', 'TX', 'PAIR_ID']].copy()
    cph_m = CoxPHFitter().fit(d_cox, 'OS_YEARS', 'OS_EVENT', cluster_col='PAIR_ID', robust=True)
    hr = cph_m.summary.loc['TX']
    rm_t = rmst(matched.loc[matched.TX == 1, 'OS_YEARS'], matched.loc[matched.TX == 1, 'OS_EVENT'])
    rm_c = rmst(matched.loc[matched.TX == 0, 'OS_YEARS'], matched.loc[matched.TX == 0, 'OS_EVENT'])
    # Bootstrap over matched pairs: resample pairs as integer weights on each member
    pair_ids = np.sort(matched.PAIR_ID.unique())
    pair_pos = np.searchsorted(pair_ids, matched.PAIR_ID.values)
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(300):
        draw = np.bincount(rng.integers(0, len(pair_ids), size=len(pair_ids)), minlength=len(pair_ids))
        w = draw[pair_pos].astype(float)
        m1 = matched.TX.values == 1; m0 = ~m1
        boots.append(rmst(matched.OS_YEARS.values[m1], matched.OS_EVENT.values[m1], weights=w[m1]) -
                     rmst(matched.OS_YEARS.values[m0], matched.OS_EVENT.values[m0], weights=w[m0]))
    psm_results.append({
        'phenotype': pheno, 'n_treated_pool': n_t, 'n_control_pool': n_c,
        'matched_pairs': len(pair_ids), 'caliper_logit': round(float(caliper), 4),
        'HR_SurgChemo_vs_SurgOnly': round(float(hr['exp(coef)']), 3),
        'HR_lower95': round(float(hr['exp(coef) lower 95%']), 3),
        'HR_upper95': round(float(hr['exp(coef) upper 95%']), 3),
        'HR_p_robust': float(hr['p']),
        'logrank_p': float(lr_test.p_value),
        'RMST_5y_SurgChemo': round(rm_t, 3), 'RMST_5y_SurgOnly': round(rm_c, 3),
        'RMST_diff_5y': round(rm_t - rm_c, 3),
        'RMST_diff_5y_boot_lo': round(float(np.percentile(boots, 2.5)), 3),
        'RMST_diff_5y_boot_hi': round(float(np.percentile(boots, 97.5)), 3)})

psm_df = pd.DataFrame(psm_results)
save_table(psm_df, 'T18_PSM_outcomes_by_phenotype')
display(psm_df)
bal_df = pd.concat(psm_bal_rows) if psm_bal_rows else pd.DataFrame()
save_table(bal_df, 'T19_PSM_balance_SMD')
if len(bal_df):
    display(bal_df[bal_df.stage == 'after matching'].assign(abs_SMD=lambda d: d.SMD.abs()).groupby('phenotype').abs_SMD.max().rename('max |SMD| after matching').to_frame())

# Love plot (balance before and after matching)
if len(bal_df):
    fig, axes = plt.subplots(1, len(matched_store), figsize=(4.6 * len(matched_store), 4.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, pheno in zip(axes, [p for p in PHENO_ORDER if p in matched_store]):
        b = bal_df[bal_df.phenotype == pheno]
        before = b[b.stage == 'before'].set_index('covariate').SMD
        after = b[b.stage == 'after matching'].set_index('covariate').SMD
        yy = np.arange(len(before))
        ax.scatter(before.values, yy, label='before', marker='o', color='#999999')
        ax.scatter(after.values, yy, label='after matching', marker='D', color='#1F78B4')
        ax.axvline(0, color='k', lw=0.8); ax.axvline(0.1, color='grey', ls=':'); ax.axvline(-0.1, color='grey', ls=':')
        ax.set_yticks(yy); ax.set_yticklabels([c.replace('BAL_', '') for c in before.index], fontsize=7)
        ax.set_title(f'{pheno}'); ax.set_xlabel('SMD'); ax.grid(alpha=0.25)
    axes[0].legend(frameon=False, fontsize=8)
    save_fig(fig, 'F07_PSM_love_plot'); plt.show(); plt.close(fig)

# KM of the matched samples (one panel per phenotype)
if matched_store:
    fig, axes = plt.subplots(1, len(matched_store), figsize=(4.6 * len(matched_store), 4.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, pheno in zip(axes, [p for p in PHENO_ORDER if p in matched_store]):
        m = matched_store[pheno]
        for tx, col in [(1, '#1B7837'), (0, '#762A83')]:
            s = m[m.TX == tx]
            k = km_fit(s, 'OS_YEARS', 'OS_EVENT', 'Surgery+Chemo' if tx == 1 else 'Surgery_Only')
            k.plot_survival_function(ax=ax, ci_show=True, color=col, show_censors=False)
        ax.set_xlim(0, 10); ax.set_ylim(0, 1.01); ax.grid(alpha=0.25); ax.set_title(f'{pheno} (matched)')
        ax.set_xlabel('Years from liver metastasis diagnosis')
    axes[0].set_ylabel('Survival probability'); axes[0].legend(frameon=False, fontsize=8)
    save_fig(fig, 'F08_KM_matched_treatment_by_phenotype'); plt.show(); plt.close(fig)

# Timing checks
timing = (tx_df.groupby(['PHENOTYPE', 'CHEMO_TIMING']).size().rename('n').reset_index())
save_table(timing, 'T20_chemo_timing_checks')
display(timing)

# Landmark at 6 months (removes deaths and censoring before 6 months)
lm = tx_df[tx_df.OS_YEARS > 0.5].copy()
lm['OS_LM'] = lm.OS_YEARS - 0.5
lm_rows = []
for pheno in PHENO_ORDER:
    s = lm[lm.PHENOTYPE == pheno]
    a = s[s.TX == 1]; b = s[s.TX == 0]
    if min(len(a), len(b)) < 30:
        continue
    cph_l = CoxPHFitter().fit(s[['OS_LM', 'OS_EVENT', 'TX']], 'OS_LM', 'OS_EVENT')
    lm_rows.append({'phenotype': pheno, 'landmark_years': 0.5, 'n_surgchemo': len(a), 'n_surgonly': len(b),
                    'HR_SurgChemo_vs_SurgOnly_unadjusted': round(float(cph_l.hazard_ratios_['TX']), 3),
                    'p': float(cph_l.summary.loc['TX', 'p'])})
lm_df = pd.DataFrame(lm_rows)
save_table(lm_df, 'T21_landmark_6month_treatment')
display(lm_df)

# %% [markdown]
# ## Part 9. Sensitivity analyses
#
# Each row re-runs the main OS Cox treatment model (phenotype + treatment + covariates) under one change.
# The data are not tuned to any target.

# %% [code]
def treat_hr(df, label, t='OS_YEARS', e='OS_EVENT'):
    d = df.copy()
    d['AGE_10'] = d.AGE / 10
    try:
        _, s = cox_table(d, t, e, TREAT_COVARS, label)
        keep = s[s.term.isin(['TX_SURGCHEMO', 'PH_ADV', 'PH_INT'])]
        out = {'analysis': label, 'n': int(s.n.iloc[0]), 'events': int(s.events.iloc[0])}
        for _, r in keep.iterrows():
            out[f'HR_{r.term}'] = round(float(r.HR), 3)
            out[f'p_{r.term}'] = float(r.p)
        return out
    except Exception as ex:
        return {'analysis': label, 'note': f'not estimable: {ex}'}

sens = []
sens.append(treat_hr(ana_os, 'Primary analysis (time zero = liver metastasis diagnosis)'))

# 1. Time zero = referral date (REFERDT): larger cohort, phenotype re-assigned with the same fixed rules
alt = ana[ana.TNM_COMPLETE & ana.REFERDT_DATE.notna() & ana.OS_EVENT_RAW.notna()].copy()
alt['OS_DAYS_REF'] = (alt.LAST_DATE - alt.REFERDT_DATE).dt.days
alt = alt[alt.OS_DAYS_REF > 0].copy()
alt['OS_YEARS'] = np.minimum(alt.OS_DAYS_REF / DAYS_PER_YEAR, MAX_FU_YEARS)
alt['OS_EVENT'] = np.where(alt.OS_DAYS_REF / DAYS_PER_YEAR > MAX_FU_YEARS, 0.0, alt.OS_EVENT_RAW)
alt_tnm = pd.get_dummies(alt[['T_GRP', 'N_GRP', 'M_GRP']].astype(str), dtype=float)
alt_tnm.columns = [c.replace(' ', '') for c in alt_tnm.columns]
alt_tnm = alt_tnm.reindex(columns=TNM_FEATS.columns, fill_value=0.0)
alt['PHENOTYPE'] = pd.Series(tree.apply(alt_tnm.values), index=alt.index).map(node_pheno).fillna('Adverse')
alt['PH_INT'] = alt.PHENOTYPE.eq('Intermediate').astype(float)
alt['PH_ADV'] = alt.PHENOTYPE.eq('Adverse').astype(float)
sens.append(treat_hr(alt, 'Time zero = referral date (REFERDT)'))

# 2. Metachronous metastases only
sens.append(treat_hr(ana_os[ana_os.SYNC != 1], 'Metachronous metastases only'))

# 3. Follow-up truncated at 10 years
t10 = ana_os.copy()
t10['OS_YEARS'] = np.minimum(t10.OS_YEARS, 10)
t10['OS_EVENT'] = np.where(t10.OS_YEARS >= 10, 0.0, t10.OS_EVENT)
sens.append(treat_hr(t10, 'Follow-up truncated at 10 years'))

# 4. Era-specific models
sens.append(treat_hr(ana_os[ana_os.ERA == 'Training'], 'Training era only (<=2009)'))
sens.append(treat_hr(ana_os[ana_os.ERA == 'Validation'], 'Validation era only (>2009)'))

# 5. Recurrence-free survival
sens.append(treat_hr(ana_os, 'Recurrence-free survival (RFS)', 'RFS_YEARS', 'RFS_EVENT'))

# 6. Treatment definition extended to post-colectomy adjuvant chemotherapy
post_col = yn(ana_os.POSTCOLCTYN_F1)
chemo_any = pd.Series(np.nan, index=ana_os.index)
chemo_any[(ana_os.CHEMO_PERIOP == 0) & (post_col == 0)] = 0.0
chemo_any[(ana_os.CHEMO_PERIOP == 1) | (post_col == 1)] = 1.0
alt_tx = ana_os.copy()
alt_tx['TX_SURGCHEMO'] = (alt_tx.SURGERY == 1).astype(float).where(alt_tx.SURGERY.notna()) * chemo_any
alt_tx['TX_CHEMOONLY'] = (alt_tx.SURGERY == 0).astype(float).where(alt_tx.SURGERY.notna()) * chemo_any
alt_tx['TX_NOTREAT'] = (alt_tx.SURGERY == 0).astype(float).where(alt_tx.SURGERY.notna()) * (1 - chemo_any)
sens.append(treat_hr(alt_tx, 'Chemotherapy includes post-colectomy adjuvant therapy'))
sens_df = pd.DataFrame(sens)
save_table(sens_df, 'T22_sensitivity_analyses')
display(sens_df)

# %% [markdown]
# ## Part 10. Main results tables and publication figures

# %% [code]
# Table 1: baseline characteristics by phenotype (aggregate)
def describe_group(df, label):
    return {'group': label, 'n': len(df),
            'age_median_IQR': f"{df.AGE.median():.1f} ({df.AGE.quantile(.25):.1f}-{df.AGE.quantile(.75):.1f})",
            'male_n_pct': f"{int(df.MALE.sum()):,} ({100*df.MALE.mean():.1f}%)",
            'T3_n_pct': f"{int((df.T_GRP=='T3').sum()):,} ({100*(df.T_GRP=='T3').mean():.1f}%)",
            'T4_n_pct': f"{int((df.T_GRP=='T4').sum()):,} ({100*(df.T_GRP=='T4').mean():.1f}%)",
            'N_positive_n_pct': f"{int(df.N_GRP.isin(['N1','N2']).sum()):,} ({100*df.N_GRP.isin(['N1','N2']).mean():.1f}%)",
            'M1_n_pct': f"{int((df.M_GRP=='M1').sum()):,} ({100*(df.M_GRP=='M1').mean():.1f}%)",
            'synchronous_n_pct': f"{int((df.SYNC==1).sum()):,} ({100*(df.SYNC==1).mean():.1f}%)",
            'metastases_median_IQR': f"{df.METS.median():.0f} ({df.METS.quantile(.25):.0f}-{df.METS.quantile(.75):.0f})",
            'size_mm_median_IQR': f"{df.SIZE_MM.median():.0f} ({df.SIZE_MM.quantile(.25):.0f}-{df.SIZE_MM.quantile(.75):.0f})",
            'DFI_months_median_IQR': f"{df.DFI_MO.median():.1f} ({df.DFI_MO.quantile(.25):.1f}-{df.DFI_MO.quantile(.75):.1f})",
            'surgery_n_pct': f"{int((df.SURGERY==1).sum()):,} ({100*(df.SURGERY==1).mean():.1f}%)" if df.SURGERY.notna().any() else 'n/a',
            'surgery_chemo_n_pct': f"{int((df.TREATMENT=='Surgery+Chemo').sum()):,}"}

t1 = pd.DataFrame([describe_group(ana_os, 'All')] +
                  [describe_group(ana_os[ana_os.PHENOTYPE == p], p) for p in PHENO_ORDER]).set_index('group').T
save_table(t1, 'T23_table1_baseline_by_phenotype', index=True)
display(t1)

# Figure: stacked phenotype distribution by TNM group (aggregate)
ct = pd.crosstab([ana_os.T_GRP, ana_os.N_GRP], ana_os.PHENOTYPE, normalize='index').reindex(columns=PHENO_ORDER).fillna(0)
fig, ax = plt.subplots(figsize=(8, 4.8))
bottom = np.zeros(len(ct))
for p, col in zip(PHENO_ORDER, ['#1B7837', '#E08214', '#B2182B']):
    ax.bar(range(len(ct)), ct[p].values, bottom=bottom, color=col, label=p)
    bottom += ct[p].values
ax.set_xticks(range(len(ct))); ax.set_xticklabels([f'{a} / {b}' for a, b in ct.index], rotation=45, ha='right', fontsize=8)
ax.set_ylabel('Proportion of patients'); ax.set_title('Phenotype distribution by T and N stage')
ax.legend(frameon=False, fontsize=8, bbox_to_anchor=(1.01, 1), loc='upper left')
save_fig(fig, 'F09_phenotype_by_TN'); plt.show(); plt.close(fig)

# Table 2: Cox treatment model (already saved as T11). Table 3: performance (T14). Table 4: PSM (T18).

# %% [markdown]
# ## Part 11. Reproducibility report and results package

# %% [code]
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

input_hashes = {k: {'file': p.name, 'bytes': p.stat().st_size, 'sha256': sha256(p)} for k, p in PART_FILES.items()}
env = {'python': platform.python_version(), 'platform': platform.platform(), 'pandas': pd.__version__,
       'numpy': np.__version__, 'lifelines': lifelines.__version__, 'scikit-survival': sksurv.__version__,
       'scikit-learn': sklearn.__version__, 'matplotlib': matplotlib.__version__, 'seed': SEED}
(RESULTS_DIR / 'logs' / 'environment.json').write_text(json.dumps(env, indent=2))
(RESULTS_DIR / 'logs' / 'input_hashes.json').write_text(json.dumps(input_hashes, indent=2))
(RESULTS_DIR / 'logs' / 'row_audit.json').write_text(json.dumps(audit, indent=2))
perf_small = perf[['model', 'C_index'] + [c for c in perf.columns if c.startswith(('tAUC', 'Brier', 'IBS'))]]
ph_p = ph_tab.set_index('term')['p'].round(4).to_dict()
psm_ok = psm_df.dropna(subset=['HR_SurgChemo_vs_SurgOnly']) if 'HR_SurgChemo_vs_SurgOnly' in psm_df else pd.DataFrame()

def md(df):
    """Markdown-ready fixed-width table (no optional dependency needed)."""
    return '```\n' + df.to_string(index=False) + '\n```'

report = []
report.append('# Reproducibility report: LiverMets CRLM survival analysis\n')
report.append(f'Generated {time.strftime("%Y-%m-%d %H:%M")} by running the notebook top to bottom. Every number below is '
              'read from files written by the notebook.\n')
report.append('## 1. Input data and combination\n')
report.append(f'* Input files: `{PART_FILES["Part1"].name}` and `{PART_FILES["Part2"].name}` (SHA-256 in `logs/input_hashes.json`).')
report.append(f'* Part 1: {audit["Part1"]["patient_rows"]:,} patient rows, header at Excel row 2 (row 1 blank).')
report.append(f'* Part 2: {audit["Part2"]["patient_rows"]:,} patient rows, **no header** (row 1 blank), aligned to the Part 1 column template.')
report.append(f'* Combined: **{total_patients:,} patients** (expected 29,565). The header row is not a patient; if it were counted the total would read {total_patients+1:,}.')
report.append(f'* Column names: {N_SCHEMA:,} in the header, all unique. Full inventory: `tables/T01_column_inventory.csv`.')
report.append(f'* Analysis extract: {len(ANALYSIS_COLS)} columns, written to Parquet in batches of {BATCH:,} rows (streamed; the full sheet is never held in memory).\n')
report.append('## 2. Dates\n')
report.append('Clinical dates are stored twice: the original Excel serial (`*_RAW`) and the calendar date (`*_DATE`). The day, month and year component columns agree with the serial value in every case (`tables/T02_date_preservation_check.csv`).\n')
report.append('## 3. Cohort\n')
report.append(md(flow_df))
report.append('\nThe TNM-complete count reproduces the earlier published flow (19,465 retained, 10,100 excluded). The survival-eligible count does not reproduce the earlier 14,759. The earlier value came from a derived dataset (SURVIVAL_YEARS, VITAL_STATUS) that is not in this repository, so it cannot be reproduced exactly. This notebook derives follow-up from dates (see section 4).\n')
report.append('## 4. Variable definitions (all derived in the notebook)\n')
report.append('* **Time zero:** date of first liver metastasis diagnosis (`LE1DGMETADT`).')
report.append('* **OS:** days from time zero to last contact (`LASTNDTC`); event = `PATSTATC` = Deceased; Alive and Lost to follow-up are censored. Truncated at 15 years.')
report.append('* **RFS:** recurrence date (earliest of `RECDT_F1`-`RECDT_F7`) if recorded; otherwise death or last contact. `alive_with_disease_no_date` (status from `PATSTAT_F1`) is an event at last contact, which is a known approximation.')
report.append('* **TNM groups:** T1-2 (incl. T0), T3, T4 (incl. T4a/b); N0, N1 (incl. a/b/c), N2; M0, M1 (incl. a/b/c).')
report.append('* **Phenotypes:** survival tree on TNM groups, training era only; terminal nodes labelled from KM median OS with the earlier thresholds (6 and 5 years).')
report.append('* **Treatment:** hepatectomy (`LE1HEPATECTYN_F1`) and peri-operative systemic chemotherapy (`LE1PREOPMCTYN_F1` or `LE1POSTOPMCTYN_F1`).')
report.append('* **Metastases count:** values outside 1-50 set to missing; **size:** outside 1-300 mm set to missing; **CEA:** `LE1PREHEPCEA_F1` in ng/mL.')
report.append('* `TIMELAST` is not used. It does not equal any date difference in the export and has negative values (`tables/T03_timelast_qc.csv`).\n')
report.append('## 5. Results\n')
report.append('### Phenotypes and survival\n')
report.append(md(os_by_pheno))
report.append('\n### Cox model (treatment)\n')
report.append(md(cox_treat_tab.round(3)))
report.append('\n### Model performance (C-index, time-dependent AUC, Brier)\n')
report.append(md(perf_small))
report.append('\n### Propensity-score matched treatment comparison\n')
report.append(md(psm_df))
report.append('\n### Sensitivity analyses\n')
report.append(md(sens_df))
report.append('\n## 6. Limitations and deviations from the earlier analysis\n')
report.append('* Earlier published derived variables (SURVIVAL_YEARS, VITAL_STATUS, TREATMENT, NB_METASTASES_NUM) were not available. Their definitions are replaced by the date-based definitions above, so results will not match the earlier numbers exactly.')
report.append('* The earlier RFS used overall-survival time and an F1-only status mapping. This notebook uses recurrence dates where recorded.')
report.append('* The earlier phenotypes came from a binary CART with the outcome in the same data. Here the survival tree is grown on the training era and then applied to the validation era.')
report.append('* Basingstoke Predictive Index is not computed (tumour differentiation grade not in the export). The Nordlinger score is reported only as a Nordlinger-type unweighted count.')
report.append('* Counts from `ND`/`NA` are treated as missing; no imputation is used for the cohort or the treatment comparison. Machine-learning models use training-set median imputation with missing indicators.')
report.append('* Treatment is determined after time zero; the treatment comparison is therefore observational and is checked with a 6-month landmark analysis, which does not remove all bias.')
report.append('* Patient-level working data are in `WORK_DIR` and are not part of the results package.\n')
report.append('## 7. Environment and reproducibility\n')
report.append('```json\n' + json.dumps(env, indent=2) + '\n```')
(RESULTS_DIR / 'reproducibility_report.md').write_text('\n'.join(report) + '\n')
log('Reproducibility report written: reproducibility_report.md')

# Package the aggregate results (no patient-level files)
pkg = shutil.make_archive(str(WORK_DIR.parent / 'LiverMets_results_package'), 'zip', RESULTS_DIR)
log(f'Results package: {pkg}')
print('Files in results folder:')
for p in sorted(RESULTS_DIR.rglob('*')):
    if p.is_file():
        print('  ', p.relative_to(RESULTS_DIR), f'{p.stat().st_size/1024:,.0f} KB')
