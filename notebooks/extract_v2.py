"""Second streaming extract: index-operation dates, liver and extrahepatic recurrence episodes and
follow-up status fields. Writes combined_extract_v2.parquet (both parts, original row order), leaving the
v1 extract used by the main analysis unchanged."""
import json
import os
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from python_calamine import CalamineWorkbook

IN = Path(os.environ.get('LIVERMET_DATA_DIR', '/content'))
WORK = Path(os.environ.get('LIVERMET_WORK_DIR', '/content/work'))
PARTS = {'Part1': IN / 'LiverMet_Part1.xlsx', 'Part2': IN / 'LiverMet_Part2.xlsx'}
T0 = time.time()

EXTRA = (['LE1OPERDT_F1', 'LE1OPERDT_F2', 'LE1OPERDT_F3', 'LE1DGMETA2DT', 'DGKCOLDT', 'REFERDT', 'BIRTHDT']
         + [f'LRDGMETADT_M{i}' for i in range(1, 6)] + [f'LRDGMETA2DT_M{i}' for i in range(1, 6)]
         + [f'EXHEXTRAHEPDGDT_M{i}' for i in range(1, 9)]
         + [f'LRNBREC_M{i}' for i in range(1, 6)] + [f'EXHNBREC2_M{i}' for i in range(1, 9)]
         + [f'LROPERDT_M{i}_F1' for i in range(1, 5)]
         + [f'RECDT_F{i}' for i in range(1, 8)] + [f'PATSTAT_F{i}' for i in range(1, 8)]
         + [f'DEATHKYN_F{i}' for i in range(1, 8)] + [f'LASTNDT_F{i}' for i in range(1, 8)]
         + ['PATSTATC', 'LASTNDTC', 'LE1DGMETADT', 'LE1METARESECDT_L1', 'LE1HEPATECTYN_F1', 'STADET', 'STADEN', 'STADEM',
            'GENDER', 'LE1METASYNCYN', 'LE1NBMETAHEPNUM', 'LE1HEPMETASIZENUM', 'LE1PREHEPCEA_F1'])
EXTRA = list(dict.fromkeys(EXTRA))


def comps(name):
    return [name, name + '_D', name + '_M', name + '_Y']


def iter_rows(path):
    sh = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for i, row in enumerate(sh.iter_rows()):
        yield i + 1, row


def blank(row):
    return all(v is None or v == '' for v in row)


def conv(v):
    if v is None or v == '':
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# header from Part 1 (row 2)
hdr = None
for rn, row in iter_rows(PARTS['Part1']):
    if blank(row):
        continue
    hdr = [str(v) for v in row]
    break
pos = {h: j for j, h in enumerate(hdr)}
cols = []
for name in EXTRA:
    for c in comps(name):
        if c in pos and c not in cols:
            cols.append(c)
missing = [n for n in EXTRA if n not in pos]
assert not missing, f'missing from header: {missing}'
idx = [pos[c] for c in cols]
print(f'v2 columns: {len(cols)}', flush=True)
schema = pa.schema([(c, pa.string()) for c in cols] + [('SOURCE_PART', pa.string()), ('SOURCE_EXCEL_ROW', pa.int32())])
writer = pq.ParquetWriter(WORK / 'combined_extract_v2.parquet', schema, compression='zstd')
total = 0
for part, path in PARTS.items():
    buf = {c: [] for c in cols}
    src, rows = [], []
    for rn, row in iter_rows(path):
        if blank(row) or (part == 'Part1' and rn == 2):
            continue
        L = len(row)
        for c, j in zip(cols, idx):
            buf[c].append(conv(row[j]) if j < L else None)
        src.append(part); rows.append(rn); total += 1
        if len(src) >= 2000:
            writer.write_table(pa.table({**{c: pa.array(buf[c], pa.string()) for c in cols},
                                         'SOURCE_PART': src, 'SOURCE_EXCEL_ROW': pa.array(rows, pa.int32())}, schema=schema))
            buf = {c: [] for c in cols}; src, rows = [], []
    if src:
        writer.write_table(pa.table({**{c: pa.array(buf[c], pa.string()) for c in cols},
                                     'SOURCE_PART': src, 'SOURCE_EXCEL_ROW': pa.array(rows, pa.int32())}, schema=schema))
    print(f'{part} done ({time.time()-T0:.0f}s)', flush=True)
writer.close()
print(f'TOTAL patient rows written: {total}', flush=True)
assert total == 29565
print('extract v2 done', flush=True)
