"""STROBE patient-flow diagram (Figure 1) drawn from the v7 flow counts (results/final_v7/F30_flow_counts_for_figure1.csv).
Every number on the figure is read from that file; exclusions are differences between consecutive steps."""
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

OUT = Path(os.environ.get('LIVERMET_OUT_DIR', '/home/user/LiverMets/results/final_v7'))
flow = pd.read_csv(OUT / 'F30_flow_counts_for_figure1.csv').set_index('step')['n']
dev = pd.read_csv(OUT / 'F31_table1_baseline_characteristics.csv')
n_dev = int(flow.iloc[-1])
steps = list(flow.index)
N = dict(zip(steps, flow.values))
reg = N['1 registry']
inc = N['2 CINCLUSION=Yes']
hep = N['3 hepatectomy']
opd = N['4 operation date (year+month)']
sta = N['5 status and last-news']
chr_ = N['6 chronology']
fu = N['7 positive follow-up or death']
ana = N['8 complete TNM (analytic cohort)']
assert (reg, inc, hep, opd, sta, chr_, fu, ana) == (29565, 28979, 26677, 26592, 26271, 26186, 26094, 17262)

# development and validation counts from the Table 1 file (same cohort definition)
dev_n = int(dev.loc[dev.characteristic == 'Patients', 'Development (<=2009; n=8,463)'].str.replace(',', '').iloc[0])
val_n = int(dev.loc[dev.characteristic == 'Patients', 'Validation (>=2010; n=8,799)'].str.replace(',', '').iloc[0])
assert (dev_n, val_n) == (8463, 8799) and dev_n + val_n == ana

main_steps = [
    ('LiverMetSurvey registry', f'n = {reg:,}', None),
    ('Recorded as eligible (CINCLUSION = Yes)', f'n = {inc:,}', f'Excluded: not eligible (n = {reg - inc:,})'),
    ('Hepatectomy recorded', f'n = {hep:,}', f'Excluded: no hepatectomy (n = {inc - hep:,})'),
    ('Operation date recorded (year and month)', f'n = {opd:,}', f'Excluded: no operation date (n = {hep - opd:,})'),
    ('Vital status and last-news recorded', f'n = {sta:,}', f'Excluded: missing status/last-news (n = {opd - sta:,})'),
    ('Chronology consistent', f'n = {chr_:,}', f'Excluded: inconsistent dates (n = {sta - chr_:,})'),
    ('Positive follow-up or death', f'n = {fu:,}', f'Excluded: no follow-up or death (n = {chr_ - fu:,})'),
    ('Complete TNM staging (analytic cohort)', f'n = {ana:,}', f'Excluded: incomplete TNM (n = {fu - ana:,})'),
]

fig, ax = plt.subplots(figsize=(8.6, 13.6))
ax.set_xlim(0, 100); ax.set_ylim(-6, 100); ax.axis('off')
BOX = '#E8EEF4'; EDGE = '#2F4B63'; EXC = '#FBEFEF'
y = 96.5
step_h = 9.0
centres = []
for i, (title, count, excl) in enumerate(main_steps):
    ax.add_patch(FancyBboxPatch((9, y - 4.2), 60, 7.4, boxstyle='round,pad=0.3', fc=BOX, ec=EDGE, lw=1))
    ax.text(39, y + 0.6, title, ha='center', va='center', fontsize=9.5, weight='bold', color='#1B2A38')
    ax.text(39, y - 2.1, count, ha='center', va='center', fontsize=9.5, color='#1B2A38')
    centres.append(y)
    if excl:
        ax.add_patch(FancyBboxPatch((71, y - 3.0), 28, 5.6, boxstyle='round,pad=0.3', fc=EXC, ec='#B2182B', lw=0.8))
        ax.text(85, y - 0.2, excl.replace('Excluded: ', ''), ha='center', va='center', fontsize=7.0, color='#7A1020')
        ax.plot([69, 72], [y - 0.2, y - 0.2], color='#7A1020', lw=0.8)
    if i < len(main_steps) - 1:
        ax.annotate('', xy=(39, y - 6.2), xytext=(39, y - 4.6), arrowprops=dict(arrowstyle='->', color=EDGE, lw=1))
    y -= step_h

# split into development and validation
yb = y - 2.0
ax.annotate('', xy=(26, yb + 1.6), xytext=(39, centres[-1] - 4.6), arrowprops=dict(arrowstyle='->', color=EDGE, lw=1))
ax.annotate('', xy=(64, yb + 1.6), xytext=(39, centres[-1] - 4.6), arrowprops=dict(arrowstyle='->', color=EDGE, lw=1))
ax.add_patch(FancyBboxPatch((2, yb - 7.4), 44, 7.8, boxstyle='round,pad=0.3', fc='#DDEBD8', ec='#1B7837', lw=1))
ax.text(24, yb - 2.2, 'Development (operated 2009 or earlier)', ha='center', va='center', fontsize=8.2, weight='bold')
ax.text(24, yb - 5.2, f'n = {dev_n:,}  (deaths 4,675)', ha='center', va='center', fontsize=9)
ax.add_patch(FancyBboxPatch((54, yb - 7.4), 44, 7.8, boxstyle='round,pad=0.3', fc='#FDE7CF', ec='#E08214', lw=1))
ax.text(76, yb - 2.2, 'Temporal validation (operated 2010+)', ha='center', va='center', fontsize=8.2, weight='bold')
ax.text(76, yb - 5.2, f'n = {val_n:,}  (deaths 1,916)', ha='center', va='center', fontsize=9)

yc = yb - 13.0
ax.add_patch(FancyBboxPatch((2, yc - 7.6), 96, 9.6, boxstyle='round,pad=0.3', fc='#F2F2F2', ec='#555555', lw=0.8))
ax.text(50, yc - 1.8, 'Analyses (all from the v7 analytic cohort)', ha='center', va='center', fontsize=9, weight='bold')
ax.text(50, yc - 4.6, 'Stratified Cox model (M2a); three prognostic groups from training-only tertiles; discrimination,\n'
        'calibration (decile and period), Kaplan-Meier separation, recurrence-free survival (secondary),\n'
        'sensitivity analyses (date conventions, same-day deaths, pre-operative-only model, CEA), benchmark subsets',
        ha='center', va='center', fontsize=7.6)
ax.text(2, -4.5, 'TNM = tumour-node-metastasis; CRLM = colorectal liver metastases. Step 4 onward: partial operation dates set to the 15th of the '
        'month (primary rule).\nFlow counts are from the executed notebook (F01, F30).', fontsize=6.8, color='#444444')

fig.savefig(OUT / 'figures' / 'FIG1_STROBE_flow_v7.png', dpi=220, bbox_inches='tight')
print('written', OUT / 'figures' / 'FIG1_STROBE_flow_v7.png')
