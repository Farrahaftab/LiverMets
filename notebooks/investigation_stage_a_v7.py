"""Dataset investigation, stage A: stream the two raw workbooks once and build a row-level table.

For every non-blank row we keep: source part and Excel row, a hash of all cells (duplicate detection), identifiers
(STUDY_ID, SUBJECT_ID, COUNTRY_ID, SITE_ID, CENTER, NUMPAT), and the raw staging codes (STADET, STADEN, STADEM).
Output: LIVERMET_WORK_DIR/investigation_rows.parquet (patient-level; kept out of the repository).
"""
import hashlib
import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from python_calamine import CalamineWorkbook

DATA = Path(os.environ['LIVERMET_DATA_DIR'])
WORK = Path(os.environ['LIVERMET_WORK_DIR'])
PARTS = {'Part1': DATA / 'LiverMet_Part1.xlsx', 'Part2': DATA / 'LiverMet_Part2.xlsx'}
ID_COLS = ['STUDY_ID', 'SUBJECT_ID', 'COUNTRY_ID', 'SITE_ID', 'CENTER', 'NUMPAT', 'STADET', 'STADEN', 'STADEM']
# hash covers the 188 analysis columns of the extract plus identifiers (hashing all 13,658 columns is not practical in Python)
HASH_COLS = list(__import__('pyarrow.parquet', fromlist=['x']).read_schema(os.environ['LIVERMET_WORK_DIR'] + '/extract_raw.parquet').names)
HASH_COLS = [c for c in HASH_COLS if c not in ('SOURCE_PART', 'SOURCE_EXCEL_ROW')]


def nonblank(path):
    sh = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for rn, row in enumerate(sh.iter_rows(), start=1):
        if all(v is None or v == '' for v in row):
            continue
        yield rn, row


def cell(v):
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


_, hdr_row = next(nonblank(PARTS['Part1']))
header = [str(v) for v in hdr_row]
pos = {h: j for j, h in enumerate(header)}
missing = [c for c in ID_COLS + HASH_COLS if c not in pos]
assert not missing, missing
print('header columns:', len(header), '| duplicated header names:', len(header) - len(set(header)))

schema = pa.schema([('SOURCE_PART', pa.string()), ('SOURCE_EXCEL_ROW', pa.int32()), ('ROW_HASH', pa.string())]
                   + [(c, pa.string()) for c in ID_COLS] + [('N_NONBLANK_CELLS', pa.int32()), ('N_CELLS', pa.int32())])
writer = pq.ParquetWriter(WORK / 'investigation_rows.parquet', schema, compression='zstd')
buf = {k: [] for k in [f.name for f in schema]}
counts = {}
for part, path in PARTS.items():
    n = 0
    for rn, row in nonblank(path):
        if part == 'Part1' and rn == 2:          # header row of Part 1
            continue
        L = len(row)
        vals = {c: cell(row[pos[c]]) if pos[c] < L else '' for c in ID_COLS + HASH_COLS}
        h = hashlib.sha256('\x1f'.join(vals[c] for c in HASH_COLS).encode('utf-8')).hexdigest()
        buf['SOURCE_PART'].append(part); buf['SOURCE_EXCEL_ROW'].append(rn); buf['ROW_HASH'].append(h)
        for c in ID_COLS:
            v = vals[c]
            buf[c].append(v if v != '' else None)
        buf['N_NONBLANK_CELLS'].append(sum(1 for c in HASH_COLS if vals[c] != ''))
        buf['N_CELLS'].append(len(HASH_COLS))
        n += 1
        if len(buf['ROW_HASH']) >= 2000:
            writer.write_table(pa.table(buf, schema=schema))
            buf = {k: [] for k in buf}
    if buf['ROW_HASH']:
        writer.write_table(pa.table(buf, schema=schema))
        buf = {k: [] for k in buf}
    counts[part] = n
    print(part, 'non-blank patient rows:', n)
writer.close()
print('total', sum(counts.values()))
