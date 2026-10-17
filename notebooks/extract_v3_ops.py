"""Extract operative-form counts and lesion sizes to test whether the pre-operative metastasis count and size
fields could have been recorded from the resection itself. Writes combined_extract_v3_ops.parquet."""
import os
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from python_calamine import CalamineWorkbook

IN = Path(os.environ['LIVERMET_DATA_DIR']); WORK = Path(os.environ['LIVERMET_WORK_DIR'])
PARTS = {'Part1': IN / 'LiverMet_Part1.xlsx', 'Part2': IN / 'LiverMet_Part2.xlsx'}
WANT = ['LE1NBMRESECNUM_F1', 'LE1NBMRESECNUM_F2', 'LE1HEPATECTNO_F1_CNUM', 'LE1HEPATECTNO_F1_CSIZ',
        'LE1METASIZE_L1', 'LE1METASIZE_L1_V', 'LE1NBMETAHEPNUM_V', 'LE1HEPMETASIZENUM_V']


def rows(path):
    sh = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for i, r in enumerate(sh.iter_rows()):
        yield i + 1, r


def conv(v):
    if v is None or v == '':
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


hdr = None
for rn, r in rows(PARTS['Part1']):
    if any(v not in (None, '') for v in r):
        hdr = [str(v) for v in r]; break
pos = {h: j for j, h in enumerate(hdr)}
idx = [pos[c] for c in WANT]
schema = pa.schema([(c, pa.string()) for c in WANT] + [('SOURCE_PART', pa.string()), ('SOURCE_EXCEL_ROW', pa.int32())])
w = pq.ParquetWriter(WORK / 'combined_extract_v3_ops.parquet', schema, compression='zstd')
n = 0
for part, path in PARTS.items():
    buf = {c: [] for c in WANT}; src = []; rr = []
    for rn, r in rows(path):
        if all(v in (None, '') for v in r) or (part == 'Part1' and rn == 2):
            continue
        L = len(r)
        for c, j in zip(WANT, idx):
            buf[c].append(conv(r[j]) if j < L else None)
        src.append(part); rr.append(rn); n += 1
    w.write_table(pa.table({**{c: pa.array(buf[c], pa.string()) for c in WANT},
                            'SOURCE_PART': src, 'SOURCE_EXCEL_ROW': pa.array(rr, pa.int32())}, schema=schema))
w.close()
assert n == 29565
print('done', n)
