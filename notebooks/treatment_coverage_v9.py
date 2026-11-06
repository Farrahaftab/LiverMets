"""Treatment workstream: coverage of candidate confounders and effect modifiers (stage 2 of the feasibility audit).

Streams the raw workbooks for the fields listed below and writes H10_candidate_covariate_coverage.csv
(aggregate counts over all 29,565 records). Nothing here changes the locked analysis.
"""
import os
from collections import Counter
from pathlib import Path

import pandas as pd
from python_calamine import CalamineWorkbook

DATA = Path(os.environ['LIVERMET_DATA_DIR'])
OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v9/treatment_feasibility'))
OUT.mkdir(parents=True, exist_ok=True)
FIELDS = [('COMORBYN', 'comorbidity recorded (baseline)'), ('KPKRASMUTYN', 'KRAS mutation (baseline, primary tumour)'),
          ('LE1MKRASMUTYN', 'KRAS mutation (metastasis)'), ('KPBRAFMUTYN', 'BRAF mutation'), ('KPMSSMSI', 'MSI/MSS status'),
          ('LE1PREOPMOXALIYN_F1', 'pre-operative oxaliplatin (liver chemotherapy)'),
          ('LE1PREOPMLV5FUYN_F1', 'pre-operative leucovorin/5-FU (liver chemotherapy)'),
          ('LE1PREOPMIRIYN_F1', 'pre-operative irinotecan (liver chemotherapy)'),
          ('LE1PREOPMTARGTHEYN_F1', 'pre-operative targeted therapy (liver chemotherapy)'),
          ('LE1PREOPMCAPEYN_F1', 'pre-operative capecitabine (liver chemotherapy)'),
          ('LE1MINMARGNUM_F1', 'resection margin, post-operative (not baseline)'),
          ('CINCLUSION', 'registry inclusion'), ('LE1HEPATECTYN_F1', 'hepatectomy recorded')]
rows_out = {f: Counter() for f, _ in FIELDS}
n_rows = 0
for part, fn in [('Part1', 'LiverMet_Part1.xlsx'), ('Part2', 'LiverMet_Part2.xlsx')]:
    sh = CalamineWorkbook.from_path(str(DATA / fn)).get_sheet_by_name('Data')
    it = sh.iter_rows()
    if part == 'Part1':
        next(it); hdr = [str(v) for v in next(it)]
        pos = {h: j for j, h in enumerate(hdr)}
        idx = {f: pos[f] for f, _ in FIELDS}
        rn0 = 2
    for rn, row in enumerate(it, start=(3 if part == 'Part1' else 1)):
        if all(v in (None, '') for v in row):
            continue
        n_rows += 1
        for f, _ in FIELDS:
            j = idx[f]
            v = row[j] if j < len(row) else None
            rows_out[f]['blank' if v in (None, '') else str(v)] += 1
recs = []
for f, lab in FIELDS:
    c = rows_out[f]
    usable = sum(n for k, n in c.items() if k not in ('blank', 'ND', 'NA', 'Unknown'))
    recs.append({'field': f, 'meaning': lab, 'usable_yes_no_or_value': usable,
                 'pct_of_records': round(100 * usable / n_rows, 1),
                 'top_values': '; '.join(f'{k}={v}' for k, v in c.most_common(6))})
tbl = pd.DataFrame(recs)
tbl.to_csv(OUT / 'H10_candidate_covariate_coverage.csv', index=False)
print('records:', n_rows)
print(tbl.to_string(index=False))
