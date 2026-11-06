"""Treatment feasibility workstream, stage 1: stream the raw workbooks for treatment fields (patient-level, kept out of the repository).

Writes LIVERMET_WORK_DIR/treatment_rows.parquet with one row per non-blank record in workbook order, plus the
treatment fields listed below and the identifiers needed to align the rows with the v8 cohort.
"""
import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from python_calamine import CalamineWorkbook

DATA = Path(os.environ['LIVERMET_DATA_DIR'])
WORK = Path(os.environ['LIVERMET_WORK_DIR'])
PARTS = {'Part1': DATA / 'LiverMet_Part1.xlsx', 'Part2': DATA / 'LiverMet_Part2.xlsx'}
FIELDS = ['PRECOLCHIYN', 'PRECOLCHIP', 'PRECOLRADYN',
          'POSTCOLCTYN_F1', 'POSTCOLSTDT_F1_D', 'POSTCOLSTDT_F1_M', 'POSTCOLSTDT_F1_Y', 'POSTCOLSTDT_F1',
          'POSTCOLINTENT_F1', 'POSTCOLBESTREP_F1', 'POSTCOLENDT_F1', 'POSTCOLTARGTHEYN_F1',
          'POSTCOLLV5FUYN_F1', 'POSTCOLOXALIYN_F1', 'POSTCOLIRIYN_F1', 'POSTCOLCAPEYN_F1', 'POSTCOLFU5YN_F1',
          'LE1PREOPMCTYN_F1', 'LE1PREOPMSTDT_F1_D', 'LE1PREOPMSTDT_F1_M', 'LE1PREOPMSTDT_F1_Y', 'LE1PREOPMSTDT_F1',
          'LE1POSTOPMCTYN_F1', 'LE1POSTOPMSTDT_F1',
          'LE1METARESECYN_L1', 'LE1METARESECDT_L1', 'LE1METAOTHTRTYN_L1', 'LE1LOCALTRTYN_F1', 'LE1LOCTRTDT_F1',
          'LE1OPERDT_F1_D', 'LE1OPERDT_F1_M', 'LE1OPERDT_F1_Y', 'LE1OPERDT_F1',
          'CINCLUSION', 'LE1HEPATECTYN_F1', 'PATSTATC', 'LASTNDTC', 'KPEGFRYN', 'COUNTRY_ID', 'SITE_ID', 'CENTER', 'NUMPAT']


def nonblank(path):
    sh = CalamineWorkbook.from_path(str(path)).get_sheet_by_name('Data')
    for rn, row in enumerate(sh.iter_rows(), start=1):
        if all(v is None or v == '' for v in row):
            continue
        yield rn, row


def conv(v):
    if v is None or v == '':
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


_, hdr_row = next(nonblank(PARTS['Part1']))
hdr = [str(v) for v in hdr_row]
pos = {h: j for j, h in enumerate(hdr)}
missing = [f for f in FIELDS if f not in pos]
assert not missing, missing
schema = pa.schema([('SOURCE_PART', pa.string()), ('SOURCE_EXCEL_ROW', pa.int32())] + [(f, pa.string()) for f in FIELDS])
writer = pq.ParquetWriter(WORK / 'treatment_rows.parquet', schema, compression='zstd')
n_total = 0
for part, path in PARTS.items():
    buf = {k: [] for k in schema.names}
    for rn, row in nonblank(path):
        if part == 'Part1' and rn == 2:
            continue
        L = len(row)
        buf['SOURCE_PART'].append(part); buf['SOURCE_EXCEL_ROW'].append(rn)
        for f in FIELDS:
            buf[f].append(conv(row[pos[f]]) if pos[f] < L else None)
        n_total += 1
        if len(buf['SOURCE_PART']) >= 2000:
            writer.write_table(pa.table(buf, schema=schema)); buf = {k: [] for k in buf}
    if buf['SOURCE_PART']:
        writer.write_table(pa.table(buf, schema=schema))
writer.close()
print('treatment rows written:', n_total)
