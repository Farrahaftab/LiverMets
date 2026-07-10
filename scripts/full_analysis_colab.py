"""
LiverMets CRLM Analysis — full pipeline, consolidated and bug-fixed.

Paste into Colab as a single notebook: each "# @title Section N : ..." block
below is meant to become its own cell (copy/paste one block at a time, in
order). Every section after Section 5 reads from the single `surv_df`
dataframe produced in Section 4/5 — nothing re-derives cleaning locally, which
is what caused several sections of the original notebook to silently disagree
with each other (see review notes inline at the fixed spots, marked FIX:).

Sections covered: 1 (libraries), 2 (upload), 3 (EDA), 4+5 (preprocessing +
CART phenotype derivation), 5-viz (tree plots), 6 (OS KM), 7 (RFS KM),
8 (unadjusted Cox), 9 (multivariable Cox + forest plot), 10 (treatment KM by
phenotype), 11 (propensity score matching + diagnostics).
"""

# ============================================================================
# @title Section 1 : Install & Import Libraries
# ============================================================================
get_ipython().system('pip install -qq lifelines')  # remove this line if running outside Colab

import warnings; warnings.filterwarnings('ignore')
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test
from lifelines.utils import concordance_index
from google.colab import files

plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.titlesize': 13,
                      'axes.labelsize': 12, 'legend.fontsize': 10, 'figure.dpi': 150})

PHENOTYPE_COLORS = {'Favourable': '#1565C0', 'Intermediate': '#E65100', 'Adverse': '#B71C1C'}
PHENOTYPES = ['Favourable', 'Intermediate', 'Adverse']
MAX_FOLLOW_UP = 15  # truncate at 15 years

print("Section 1 Complete — Libraries loaded.")

# ============================================================================
# @title Section 2 : Upload Dataset
# ============================================================================
uploaded = files.upload()
filename = next(iter(uploaded))
df = pd.read_csv(io.BytesIO(uploaded[filename]))
print(f"Section 2 Complete — {filename} | {len(df):,} patients x {df.shape[1]} variables")

# ============================================================================
# @title Section 3 : EDA — Data Overview
# ============================================================================
print("=" * 60); print("SECTION 3 — EDA"); print("=" * 60)

print("\n— Missing Values —")
missing = df.isnull().sum(); missing = missing[missing > 0].sort_values(ascending=False)
for col, n in missing.items():
    print(f"  {col:<30}: {n:>6,} ({n/len(df)*100:.1f}%)")

print("\n— TNM Distributions —")
for stage in ['T_STAGE', 'N_STAGE', 'M_STAGE']:
    if stage in df.columns:
        print(f"\n {stage}:")
        for val, n in df[stage].value_counts().items():
            print(f"   {str(val):<8}: {n:>7,} ({n/len(df)*100:.1f}%)")

print("\n— Vital Status —")
if 'VITAL_STATUS' in df.columns:
    vs = df['VITAL_STATUS'].value_counts()
    print(f"  Alive(0): {vs.get(0.0, 0):,} | Deceased(1): {vs.get(1.0, 0):,} | Missing: {df['VITAL_STATUS'].isna().sum():,}")

print("\n— Survival Years —")
if 'SURVIVAL_YEARS' in df.columns:
    sv = df['SURVIVAL_YEARS'].dropna()
    print(f"  Count:{len(sv):,} Mean:{sv.mean():.2f} Median:{sv.median():.2f} Min:{sv.min():.2f} Max:{sv.max():.2f}")

print("\n— Treatment Distribution —")
if 'TREATMENT' in df.columns:
    for t, n in df['TREATMENT'].value_counts().items():
        print(f"  {str(t):<25}: {n:>7,} ({n/len(df)*100:.1f}%)")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
if 'GENDER' in df.columns:
    gc = df['GENDER'].value_counts()
    axes[0].bar(gc.index, gc.values, color=['#1565C0', '#E53935'], edgecolor='white')
    axes[0].set_title('Gender', fontweight='bold'); axes[0].set_ylabel('Patients')
    for i, v in enumerate(gc.values): axes[0].text(i, v + 50, f'{v:,}', ha='center', fontsize=10)
if 'T_STAGE' in df.columns:
    tc = df['T_STAGE'].value_counts()
    axes[1].bar(tc.index.astype(str), tc.values, color='#1565C0', edgecolor='white')
    axes[1].set_title('T Stage', fontweight='bold'); axes[1].tick_params(axis='x', rotation=30)
if 'TREATMENT' in df.columns:
    tr = df['TREATMENT'].value_counts()
    axes[2].bar(range(len(tr)), tr.values, color='#2E7D32', edgecolor='white')
    axes[2].set_xticks(range(len(tr))); axes[2].set_xticklabels(tr.index, rotation=30, ha='right', fontsize=9)
    axes[2].set_title('Treatment', fontweight='bold')
plt.suptitle('EDA — LiverMetSurvey', fontsize=13, fontweight='bold')
plt.tight_layout(); plt.savefig('EDA_Overview.png', dpi=150, bbox_inches='tight'); plt.show()
print("Section 3 Complete — Saved: EDA_Overview.png")

# ============================================================================
# @title Section 4+5 : Preprocessing + CART Phenotype Derivation (consolidated)
# ============================================================================
# FIX: this replaces the notebook's Sections 4/5/9/11/R4/R7/PSM cleaning blocks,
# which each re-derived AGE_CLEAN/NB_METS_CLEAN/TNM dummies slightly differently
# (e.g. Section 11 dropped NB_METASTASES_NUM>50, R4/R7 clipped it instead) —
# that drift is what produced different patient counts for the "same" model.
# Every later section in this file reads surv_df; nothing re-derives cleaning.

def assign_phenotype(median_os):
    if median_os is None or (isinstance(median_os, float) and np.isnan(median_os)):
        return 'Adverse'
    if median_os >= 6.0:
        return 'Favourable'
    if median_os >= 5.0:
        return 'Intermediate'
    return 'Adverse'


def rfs_event(status):
    if pd.isna(status):
        return np.nan
    s = str(status).strip()
    if s in ['Deceased', 'Alive with disease']:
        return 1
    if s in ['Alive without disease', 'Alive (without precision)', 'Lost to follow-up']:
        return 0
    return np.nan


def build_analysis_cohort(raw_df: pd.DataFrame):
    print("=" * 60); print("SECTION 4 — PREPROCESSING"); print("=" * 60)
    print(f"Raw registry: {len(raw_df):,} patients x {raw_df.shape[1]} variables")

    tnm_cols = ['T_STAGE', 'N_STAGE', 'M_STAGE']
    mask_tnm = raw_df[tnm_cols].notna().all(axis=1) & (raw_df[tnm_cols] != 'ND').all(axis=1)
    cohort = raw_df[mask_tnm].copy().reset_index(drop=True)
    print(f"Excluded (missing/ND TNM): {len(raw_df) - len(cohort):,}")
    print(f"Complete TNM cohort: {len(cohort):,}")

    cohort['SURVIVAL_YEARS'] = pd.to_numeric(cohort['SURVIVAL_YEARS'], errors='coerce')
    cohort['VITAL_STATUS'] = pd.to_numeric(cohort['VITAL_STATUS'], errors='coerce')
    n_before = len(cohort)
    cohort = cohort.dropna(subset=['SURVIVAL_YEARS', 'VITAL_STATUS'])
    cohort = cohort[cohort['SURVIVAL_YEARS'] > 0].reset_index(drop=True)
    print(f"Excluded (missing survival/vital status): {n_before - len(cohort):,}")
    print(f"Final analysis cohort: {len(cohort):,}")

    cohort['SURVIVAL_TRUNC'] = cohort['SURVIVAL_YEARS'].clip(upper=MAX_FOLLOW_UP)
    cohort['EVENT_TRUNC'] = np.where(cohort['SURVIVAL_YEARS'] > MAX_FOLLOW_UP, 0,
                                      cohort['VITAL_STATUS'].astype(int))

    # FIX: cohort and tnm_dum share the same fresh 0..n-1 index, so this concat
    # is safe (the original notebook's Model-2 TNM-Cox benchmark mixed a reset
    # and an un-reset index here, silently dropping ~40% of rows via dropna()).
    tnm_dum = pd.get_dummies(cohort[tnm_cols], prefix=['T', 'N', 'M'])
    cohort = pd.concat([cohort, tnm_dum], axis=1)
    tnm_feat_cols = list(tnm_dum.columns)

    print("=" * 60); print("SECTION 5 — CART PHENOTYPE DERIVATION"); print("=" * 60)
    print("NOTE: CART used for phenotype derivation only — NOT for survival prediction")
    cart_model = DecisionTreeClassifier(
        criterion='gini', max_depth=4, min_samples_split=200,
        min_samples_leaf=100, class_weight='balanced', random_state=42)
    cart_model.fit(cohort[tnm_feat_cols], cohort['VITAL_STATUS'].astype(int))
    cohort['TERMINAL_NODE'] = cart_model.apply(cohort[tnm_feat_cols])
    print(f"\nTree depth: {cart_model.get_depth()} | Terminal nodes: {cart_model.get_n_leaves()}")
    print("\n— Decision Rules —")
    print(export_text(cart_model, feature_names=tnm_feat_cols))

    node_results = []
    for nid in sorted(cohort['TERMINAL_NODE'].unique()):
        nd = cohort[(cohort['TERMINAL_NODE'] == nid) & (cohort['SURVIVAL_TRUNC'] > 0)]
        if len(nd) < 50:
            continue
        kmf = KaplanMeierFitter()
        kmf.fit(nd['SURVIVAL_TRUNC'].astype(float), nd['EVENT_TRUNC'].astype(int))
        med = kmf.median_survival_time_
        node_results.append({'Node': nid, 'N': len(nd), 'Events': int(nd['EVENT_TRUNC'].sum()),
                              'Median_OS': round(float(med), 2) if med and not np.isinf(med) else None})
    node_df = pd.DataFrame(node_results).dropna(subset=['Median_OS'])
    node_df = node_df.sort_values('Median_OS', ascending=False).reset_index(drop=True)
    node_df['Phenotype'] = node_df['Median_OS'].apply(assign_phenotype)
    node_map = dict(zip(node_df['Node'], node_df['Phenotype']))
    cohort['PHENOTYPE'] = cohort['TERMINAL_NODE'].map(node_map).fillna('Adverse')

    print("\n— Terminal Node Median OS —")
    print(f"{'Node':>6} {'N':>7} {'Events':>7} {'Median OS':>12}")
    for _, row in node_df.iterrows():
        print(f"{int(row['Node']):>6} {int(row['N']):>7,} {int(row['Events']):>7,} {row['Median_OS']:>10.2f} yrs")

    print("\n— Phenotype Distribution —")
    for p in PHENOTYPES:
        n = int((cohort['PHENOTYPE'] == p).sum())
        print(f"  {p:<14}: {n:>7,} ({n/len(cohort)*100:.1f}%)")

    cohort['AGE_CLEAN'] = pd.to_numeric(cohort['AGE_AT_REFERRAL'], errors='coerce')
    cohort.loc[(cohort['AGE_CLEAN'] < 18) | (cohort['AGE_CLEAN'] > 100), 'AGE_CLEAN'] = np.nan
    cohort['AGE_10YR'] = cohort['AGE_CLEAN'] / 10

    cohort['NB_METS_CLEAN'] = pd.to_numeric(cohort['NB_METASTASES_NUM'], errors='coerce')
    cohort.loc[cohort['NB_METS_CLEAN'] > 50, 'NB_METS_CLEAN'] = np.nan

    cohort['MALE'] = (cohort['GENDER'] == 'Male').astype(float)

    if 'TREATMENT' in cohort.columns:
        cohort['Tx_SurgChemo'] = (cohort['TREATMENT'] == 'Surgery+Chemo').astype(int)
        cohort['Tx_ChemoOnly'] = (cohort['TREATMENT'] == 'Chemo_Only').astype(int)
        cohort['Tx_NoTreat'] = (cohort['TREATMENT'] == 'No_Treatment').astype(int)

    cohort['RFS_EVENT'] = cohort['PATSTAT_F1'].apply(rfs_event)
    cohort['RFS_TRUNC'] = cohort['SURVIVAL_YEARS'].clip(upper=MAX_FOLLOW_UP)
    cohort['RFS_EVENT_TRUNC'] = np.where(cohort['SURVIVAL_YEARS'] > MAX_FOLLOW_UP, 0, cohort['RFS_EVENT'])

    print(f"\nSection 4+5 Complete — final dataset: {len(cohort):,} patients x {cohort.shape[1]} variables")
    return cohort, cart_model, tnm_feat_cols, node_df


surv_df, cart_model, tnm_feat_cols, node_df = build_analysis_cohort(df)

# ============================================================================
# @title Section 5 (viz) : CART Tree Visualizations
# ============================================================================
# FIX: the original notebook's "Option 2" custom tree was hand-drawn with
# hardcoded box labels (e.g. claimed the N0/N1 branch splits by M-stage, when
# the fitted tree actually splits it by N-stage). This version walks
# cart_model.tree_ directly, so it can never disagree with Option 1/3.

# --- Option 1: sklearn plot_tree (ground truth, matches Option 3 exactly) ---
fig, ax = plt.subplots(figsize=(28, 12))
plot_tree(cart_model, feature_names=tnm_feat_cols, class_names=['Alive', 'Deceased'],
          filled=True, rounded=True, fontsize=9, ax=ax, impurity=False, proportion=False)
plt.title('CART Decision Tree: TNM-Based Phenotyping of Colorectal Liver Metastases\n'
          f'n = {len(surv_df):,} | Tree Depth = {cart_model.get_depth()} | Terminal Nodes = {cart_model.get_n_leaves()}',
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout(); plt.savefig('CART_Tree_sklearn.png', dpi=310, bbox_inches='tight', facecolor='white'); plt.show()
print("Saved: CART_Tree_sklearn.png")

# --- Option 2: custom tree, colored by derived phenotype — built programmatically ---
tree = cart_model.tree_
node_median = dict(zip(node_df['Node'], node_df['Median_OS']))
node_pheno = dict(zip(node_df['Node'], node_df['Phenotype']))

positions = {}
_leaf_x = [0]

def _assign_xy(node_id, depth):
    left, right = tree.children_left[node_id], tree.children_right[node_id]
    if left == -1:
        x = _leaf_x[0]; _leaf_x[0] += 1
        positions[node_id] = (x, -depth)
        return x
    xl = _assign_xy(left, depth + 1)
    xr = _assign_xy(right, depth + 1)
    x = (xl + xr) / 2
    positions[node_id] = (x, -depth)
    return x

_assign_xy(0, 0)

fig, ax = plt.subplots(figsize=(24, 10))

def _draw(node_id):
    x, y = positions[node_id]
    left, right = tree.children_left[node_id], tree.children_right[node_id]
    if left != -1:
        for child in (left, right):
            xc, yc = positions[child]
            ax.plot([x, xc], [y - 0.08, yc + 0.08], color='#999999', lw=1.5, zorder=1)
            _draw(child)
        feat = tnm_feat_cols[tree.feature[node_id]]
        ax.text(x, y, f"{feat}?", ha='center', va='center', fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.35', facecolor='#EEEEEE', edgecolor='#555555'), zorder=3)
    else:
        n = int(tree.n_node_samples[node_id])
        pheno = node_pheno.get(node_id, 'Adverse')
        med = node_median.get(node_id)
        color = PHENOTYPE_COLORS[pheno]
        os_str = f"{med:.2f}y" if med is not None else "NR"
        label = f"{pheno}\nn={n:,}\nMedian OS={os_str}"
        ax.text(x, y, label, ha='center', va='center', fontsize=8, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.45', facecolor=color, edgecolor='black', alpha=0.92), zorder=3)

_draw(0)
ax.axis('off')
ax.set_title(f'CART Decision Tree — Colored by Derived Phenotype\n'
             f'n = {len(surv_df):,} | Tree Depth = {cart_model.get_depth()} | Terminal Nodes = {cart_model.get_n_leaves()}',
             fontsize=14, fontweight='bold', pad=20)
handles = [mpatches.Patch(color=PHENOTYPE_COLORS[p], label=p) for p in PHENOTYPES]
ax.legend(handles=handles, loc='upper right', fontsize=11, framealpha=0.95)
plt.tight_layout(); plt.savefig('CART_Tree_Phenotype_Custom.png', dpi=310, bbox_inches='tight', facecolor='white'); plt.show()
print("Saved: CART_Tree_Phenotype_Custom.png")

# --- Option 3: text export (for Methods section) ---
tree_rules = export_text(cart_model, feature_names=tnm_feat_cols)
print("\n" + tree_rules)
with open('CART_Tree_Rules.txt', 'w') as f:
    f.write("CART Decision Rules\n" + "=" * 70 + "\n\n" + tree_rules)
print("Saved: CART_Tree_Rules.txt")
print("Section 5 (viz) Complete")

# ============================================================================
# @title Section 6 : Overall Survival — KM by Phenotype
# ============================================================================
print("=" * 60); print("SECTION 6 — OVERALL SURVIVAL BY PHENOTYPE"); print("=" * 60)

fig, ax = plt.subplots(figsize=(13, 8))
os_summary = {}
for pheno in PHENOTYPES:
    pdata = surv_df[surv_df['PHENOTYPE'] == pheno]
    if len(pdata) < 10: continue
    T = pdata['SURVIVAL_TRUNC'].astype(float).values; E = pdata['EVENT_TRUNC'].astype(int).values
    kmf = KaplanMeierFitter()
    kmf.fit(T, E, label=f"{pheno} (n={len(pdata):,})")
    kmf.plot_survival_function(ax=ax, color=PHENOTYPE_COLORS[pheno], linewidth=2.5, ci_show=True, ci_alpha=0.12)
    med = kmf.median_survival_time_
    os_summary[pheno] = {'n': len(pdata), 'events': int(E.sum()),
                          'median': round(float(med), 2) if med and not np.isinf(med) else None}

times = [0, 2, 5, 10, 15]
at_risk_text = "At risk:\n"
for pheno in PHENOTYPES:
    pdata = surv_df[(surv_df['PHENOTYPE'] == pheno) & (surv_df['SURVIVAL_TRUNC'] > 0)]
    counts = [(pdata['SURVIVAL_TRUNC'] >= t).sum() for t in times]
    at_risk_text += f"{pheno:14} " + " | ".join([f"{n:5,}" for n in counts]) + "\n"

lr_all = multivariate_logrank_test(surv_df['SURVIVAL_TRUNC'].astype(float),
                                    surv_df['PHENOTYPE'], event_col=surv_df['EVENT_TRUNC'].astype(int))
p_all = lr_all.p_value; p_str = '< 0.001' if p_all < 0.001 else f'= {p_all:.4f}'

ax.set_xlabel('Time (Years)', fontsize=13); ax.set_ylabel('Overall Survival Probability', fontsize=13)
ax.set_title(f'Kaplan-Meier Overall Survival by CART Phenotype\nLog-rank p {p_str} | {MAX_FOLLOW_UP}-year follow-up',
             fontsize=12, fontweight='bold', pad=12)
ax.set_xlim(0, MAX_FOLLOW_UP); ax.set_ylim(0, 1.05)
ax.axhline(y=0.5, color='grey', linestyle='--', alpha=0.4); ax.legend(loc='upper right', frameon=True, fontsize=11)
ax.grid(axis='y', alpha=0.3)
fig.text(0.5, 0.07, at_risk_text, ha='center', fontsize=10, family='monospace',
          bbox=dict(boxstyle='round,pad=0.8', facecolor='wheat', alpha=0.6, edgecolor='black'))
fig.text(0.5, 0.03, f'Time (years): {" | ".join([f"{t:5}" for t in times])}',
          ha='center', fontsize=9, family='monospace', style='italic', color='gray')
plt.tight_layout(rect=[0, 0.18, 1, 1])
plt.savefig('KM_OS_by_Phenotype.png', dpi=310, bbox_inches='tight'); plt.show()

print("\n— OS Summary —")
for pheno, res in os_summary.items():
    med_str = f"{res['median']:.2f} yrs" if res['median'] else "NR"
    print(f"{pheno:<14} {res['n']:>7,} {res['events']:>7,} {med_str:>12}")
print(f"\nOverall log-rank p {p_str}")

print("\n— Pairwise Log-Rank Tests —")
pairs = [('Favourable', 'Intermediate'), ('Favourable', 'Adverse'), ('Intermediate', 'Adverse')]
for a, b in pairs:
    da = surv_df[surv_df['PHENOTYPE'] == a]; db = surv_df[surv_df['PHENOTYPE'] == b]
    lr = logrank_test(da['SURVIVAL_TRUNC'].astype(float), db['SURVIVAL_TRUNC'].astype(float),
                       da['EVENT_TRUNC'].astype(int), db['EVENT_TRUNC'].astype(int))
    ps = '< 0.001' if lr.p_value < 0.001 else f'= {lr.p_value:.4f}'
    print(f"  {a} vs {b}: p {ps}")
print("Section 6 Complete — Saved: KM_OS_by_Phenotype.png")

# ============================================================================
# @title Section 7 : Recurrence-Free Survival — KM by Phenotype
# ============================================================================
print("=" * 60); print("SECTION 7 — RECURRENCE-FREE SURVIVAL"); print("=" * 60)
print("RFS event = Deceased OR Alive with disease (from PATSTAT_F1)")
print("RFS time = SURVIVAL_YEARS (last follow-up) — approximation, acknowledged as limitation")

rfs_df = surv_df.dropna(subset=['RFS_TRUNC', 'RFS_EVENT_TRUNC', 'PHENOTYPE']).copy()
rfs_df = rfs_df[rfs_df['RFS_TRUNC'] > 0].copy()
rfs_df['RFS_EVENT_TRUNC'] = rfs_df['RFS_EVENT_TRUNC'].astype(int)
print(f"\nRFS cohort: {len(rfs_df):,} | Events: {int(rfs_df['RFS_EVENT_TRUNC'].sum()):,}")

fig, ax = plt.subplots(figsize=(13, 8))
rfs_summary = {}
for pheno in PHENOTYPES:
    pdata = rfs_df[rfs_df['PHENOTYPE'] == pheno]
    if len(pdata) < 10: continue
    T = pdata['RFS_TRUNC'].astype(float).values; E = pdata['RFS_EVENT_TRUNC'].astype(int).values
    kmf = KaplanMeierFitter()
    kmf.fit(T, E, label=f"{pheno} (n={len(pdata):,})")
    kmf.plot_survival_function(ax=ax, color=PHENOTYPE_COLORS[pheno], linewidth=2.5, ci_show=True, ci_alpha=0.12)
    med = kmf.median_survival_time_
    rfs_summary[pheno] = {'n': len(pdata), 'events': int(E.sum()),
                           'median': round(float(med), 2) if med and not np.isinf(med) else None}

at_risk_text = "At risk:\n"
for pheno in PHENOTYPES:
    pdata = rfs_df[rfs_df['PHENOTYPE'] == pheno]
    counts = [(pdata['RFS_TRUNC'] >= t).sum() for t in times]
    at_risk_text += f"{pheno:14} " + " | ".join([f"{n:5,}" for n in counts]) + "\n"

lr_rfs = multivariate_logrank_test(rfs_df['RFS_TRUNC'].astype(float), rfs_df['PHENOTYPE'],
                                    event_col=rfs_df['RFS_EVENT_TRUNC'].astype(int))
p_rfs = lr_rfs.p_value; p_rfs_str = '< 0.001' if p_rfs < 0.001 else f'= {p_rfs:.4f}'

ax.set_xlabel('Time (Years)', fontsize=13); ax.set_ylabel('RFS Probability', fontsize=13)
ax.set_title(f'Kaplan-Meier Recurrence-Free Survival by CART Phenotype\nLog-rank p {p_rfs_str}',
             fontsize=12, fontweight='bold', pad=12)
ax.set_xlim(0, MAX_FOLLOW_UP); ax.set_ylim(0, 1.05)
ax.axhline(y=0.5, color='grey', linestyle='--', alpha=0.4); ax.legend(loc='upper right', frameon=True, fontsize=11)
ax.grid(axis='y', alpha=0.3)
fig.text(0.5, 0.07, at_risk_text, ha='center', fontsize=10, family='monospace',
          bbox=dict(boxstyle='round,pad=0.8', facecolor='wheat', alpha=0.6, edgecolor='black'))
fig.text(0.5, 0.03, f'Time (years): {" | ".join([f"{t:5}" for t in times])}',
          ha='center', fontsize=9, family='monospace', style='italic', color='gray')
plt.tight_layout(rect=[0, 0.18, 1, 1])
plt.savefig('KM_RFS_by_Phenotype.png', dpi=310, bbox_inches='tight'); plt.show()

print("\n— RFS Summary —")
for pheno, res in rfs_summary.items():
    med_str = f"{res['median']:.2f} yrs" if res['median'] else "NR"
    print(f"  {pheno:<14}: n={res['n']:,} Median RFS={med_str} Events={res['events']:,}")
print(f"\nOverall log-rank p {p_rfs_str}")

print("\n— Pairwise Log-Rank (RFS) —")
for a, b in pairs:
    da = rfs_df[rfs_df['PHENOTYPE'] == a]; db = rfs_df[rfs_df['PHENOTYPE'] == b]
    lr = logrank_test(da['RFS_TRUNC'].astype(float), db['RFS_TRUNC'].astype(float),
                       da['RFS_EVENT_TRUNC'].astype(int), db['RFS_EVENT_TRUNC'].astype(int))
    ps = '< 0.001' if lr.p_value < 0.001 else f'= {lr.p_value:.4f}'
    print(f"  {a} vs {b}: p {ps}")
print("Section 7 Complete — Saved: KM_RFS_by_Phenotype.png")

# ============================================================================
# @title Section 8 : Simple Cox Regression (Unadjusted)
# ============================================================================
print("=" * 60); print("SECTION 8 — SIMPLE COX (UNADJUSTED)"); print("=" * 60)
print("Reference: Favourable phenotype | Surgery Only")

cox_s_base = surv_df[surv_df['TREATMENT'].isin(['Surgery_Only', 'Surgery+Chemo'])].copy()
cox_s_base['Phenotype_Intermediate'] = (cox_s_base['PHENOTYPE'] == 'Intermediate').astype(int)
cox_s_base['Phenotype_Adverse'] = (cox_s_base['PHENOTYPE'] == 'Adverse').astype(int)
feats_s = ['Phenotype_Intermediate', 'Phenotype_Adverse', 'Tx_SurgChemo']
idx_labels = ['Intermediate vs Favourable', 'Adverse vs Favourable', 'Surgery+Chemo vs Surgery Only']

cox_s_df = cox_s_base[feats_s + ['SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()
cox_s_df = cox_s_df[cox_s_df['SURVIVAL_TRUNC'] > 0]
cph_s = CoxPHFitter(); cph_s.fit(cox_s_df, duration_col='SURVIVAL_TRUNC', event_col='EVENT_TRUNC')
hr_s = cph_s.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].copy()
hr_s.columns = ['HR', 'CI_lower', 'CI_upper', 'p_value']; hr_s = hr_s.round(3); hr_s.index = idx_labels

print(f"\nPatients: {len(cox_s_df):,}")
print(f"\n{'Variable':<40} {'HR':>6} {'95% CI':>20} {'p':>10}")
for idx, row in hr_s.iterrows():
    p_d = '< 0.001' if row['p_value'] < 0.001 else f'{row["p_value"]:.3f}'
    ci = f"({row['CI_lower']:.2f}-{row['CI_upper']:.2f})"
    sig = '***' if row['p_value'] < 0.001 else ('**' if row['p_value'] < 0.01 else ('*' if row['p_value'] < 0.05 else 'ns'))
    print(f"{idx:<40} {row['HR']:>6.3f} {ci:>20} {p_d:>10} {sig}")
print("Section 8 Complete")

# ============================================================================
# @title Section 9 : Multivariable Cox + C-index + Forest Plot
# ============================================================================
print("=" * 60); print("SECTION 9 — MULTIVARIABLE COX"); print("=" * 60)

mv_df = surv_df.copy()
mv_df['Phenotype_Intermediate'] = (mv_df['PHENOTYPE'] == 'Intermediate').astype(int)
mv_df['Phenotype_Adverse'] = (mv_df['PHENOTYPE'] == 'Adverse').astype(int)

all_feats = ['Phenotype_Intermediate', 'Phenotype_Adverse',
             'Tx_SurgChemo', 'Tx_ChemoOnly', 'Tx_NoTreat',
             'AGE_10YR', 'MALE', 'NB_METS_CLEAN']
cox_feats_mv = [f for f in all_feats if f in mv_df.columns]
cox_mv = mv_df[cox_feats_mv + ['SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()
cox_mv = cox_mv[cox_mv['SURVIVAL_TRUNC'] > 0]

cph_mv = CoxPHFitter(); cph_mv.fit(cox_mv, duration_col='SURVIVAL_TRUNC', event_col='EVENT_TRUNC')
hr_mv = cph_mv.summary[['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']].copy()
hr_mv.columns = ['HR', 'CI_lower', 'CI_upper', 'p_value']; hr_mv = hr_mv.round(3)
label_map = {'Phenotype_Intermediate': 'Intermediate vs Favourable', 'Phenotype_Adverse': 'Adverse vs Favourable',
             'Tx_SurgChemo': 'Surgery+Chemo vs Surgery Only', 'Tx_ChemoOnly': 'Chemo Only vs Surgery Only',
             'Tx_NoTreat': 'No Treatment vs Surgery Only', 'AGE_10YR': 'Age (per 10 years)',
             'MALE': 'Male vs Female', 'NB_METS_CLEAN': 'N Metastases (per additional)'}
hr_mv.index = [label_map.get(i, i) for i in hr_mv.index]

ci_score = concordance_index(cox_mv['SURVIVAL_TRUNC'], -cph_mv.predict_partial_hazard(cox_mv), cox_mv['EVENT_TRUNC'])
print(f"\nPatients: {len(cox_mv):,} | Events: {int(cox_mv['EVENT_TRUNC'].sum()):,} | C-index: {ci_score:.3f}")
print(f"\n{'Variable':<40} {'HR':>6} {'95% CI':>20} {'p':>10}")
for idx, row in hr_mv.iterrows():
    p_d = '< 0.001' if row['p_value'] < 0.001 else f'{row["p_value"]:.3f}'
    ci = f"({row['CI_lower']:.2f}-{row['CI_upper']:.2f})"
    sig = '***' if row['p_value'] < 0.001 else ('**' if row['p_value'] < 0.01 else ('*' if row['p_value'] < 0.05 else 'ns'))
    print(f"{idx:<40} {row['HR']:>6.3f} {ci:>20} {p_d:>10} {sig}")

fig, ax = plt.subplots(figsize=(13, 8))
cmap = {'Intermediate vs Favourable': '#1565C0', 'Adverse vs Favourable': '#1565C0',
        'Surgery+Chemo vs Surgery Only': '#2E7D32', 'Chemo Only vs Surgery Only': '#E53935',
        'No Treatment vs Surgery Only': '#E53935', 'Age (per 10 years)': '#6A1B9A',
        'Male vs Female': '#6A1B9A', 'N Metastases (per additional)': '#6A1B9A'}
y_pos = list(range(len(hr_mv)))[::-1]
for i, (idx, row) in enumerate(hr_mv.iterrows()):
    yp = y_pos[i]; col = cmap.get(idx, '#555555')
    ax.plot([row['CI_lower'], row['CI_upper']], [yp, yp], color=col, linewidth=2.5, solid_capstyle='round')
    ax.plot(row['HR'], yp, 'o', color=col, markersize=10, zorder=5)
    p_d = '< 0.001' if row['p_value'] < 0.001 else f'{row["p_value"]:.3f}'
    ax.text(hr_mv['CI_upper'].max() + 0.05, yp,
            f"HR={row['HR']:.2f} ({row['CI_lower']:.2f}-{row['CI_upper']:.2f}) p {p_d}", va='center', fontsize=9.5, color=col)
ax.axvline(x=1.0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
ax.set_yticks(y_pos); ax.set_yticklabels(hr_mv.index, fontsize=11)
ax.set_xlabel('Hazard Ratio (HR) — 95% CI', fontsize=12)
ax.set_title(f'Multivariable Cox — Forest Plot\nC-index={ci_score:.3f} | n={len(cox_mv):,}', fontsize=12, fontweight='bold', pad=15)
ax.set_xlim(0.3, hr_mv['CI_upper'].max() + 2.5); ax.grid(axis='x', alpha=0.3)
plt.tight_layout(); plt.savefig('Cox_Multivariable_Forest_Plot.png', dpi=310, bbox_inches='tight'); plt.show()
hr_mv.to_csv('Cox_Multivariable_Results.csv')
print("Section 9 Complete — Saved: Cox_Multivariable_Forest_Plot.png, Cox_Multivariable_Results.csv")

# ============================================================================
# @title Section 10 : Treatment KM by Phenotype
# ============================================================================
print("=" * 60); print("SECTION 10 : TREATMENT BY PHENOTYPE"); print("=" * 60)

tx_rows = []; tx_pvals = {}
tx_surv = surv_df[surv_df['TREATMENT'].isin(['Surgery_Only', 'Surgery+Chemo'])].copy()
fig, axes = plt.subplots(1, 3, figsize=(21, 7), sharey=True)
fig.suptitle('KM OS by Treatment — Stratified by CART Phenotype (Unadjusted)', fontsize=13, fontweight='bold', y=1.02)

for ax, pheno in zip(axes, PHENOTYPES):
    pdata = tx_surv[tx_surv['PHENOTYPE'] == pheno]
    so_d = pdata[pdata['TREATMENT'] == 'Surgery_Only']; sc_d = pdata[pdata['TREATMENT'] == 'Surgery+Chemo']
    for treat, label, col in [('Surgery_Only', 'Surgery Only', '#1B5E20'), ('Surgery+Chemo', 'Surgery+Chemo', '#43A047')]:
        tdata = pdata[pdata['TREATMENT'] == treat]
        if len(tdata) < 20: continue
        kmf = KaplanMeierFitter()
        kmf.fit(tdata['SURVIVAL_TRUNC'].astype(float), tdata['EVENT_TRUNC'].astype(int), label=f"{label} (n={len(tdata):,})")
        kmf.plot_survival_function(ax=ax, color=col, linewidth=2.5, ci_show=True, ci_alpha=0.15)
        med = kmf.median_survival_time_
        tx_rows.append({'Phenotype': pheno, 'Treatment': label, 'N': len(tdata),
                         'Events': int(tdata['EVENT_TRUNC'].sum()),
                         'Median_OS': round(float(med), 2) if med and not np.isinf(med) else None})
    if len(so_d) >= 20 and len(sc_d) >= 20:
        lr_tx = logrank_test(so_d['SURVIVAL_TRUNC'].astype(float), sc_d['SURVIVAL_TRUNC'].astype(float),
                              so_d['EVENT_TRUNC'].astype(int), sc_d['EVENT_TRUNC'].astype(int))
        tx_pvals[pheno] = lr_tx.p_value
        ps_tx = '< 0.001' if lr_tx.p_value < 0.001 else f'= {lr_tx.p_value:.4f}'
    else:
        ps_tx = 'N/A'
    ax.set_title(f'{pheno}\n(SO vs SC p {ps_tx})', fontsize=12, fontweight='bold', color=PHENOTYPE_COLORS[pheno])
    ax.set_xlabel('Time (Years)', fontsize=12); ax.set_xlim(0, MAX_FOLLOW_UP); ax.set_ylim(0, 1.05)
    ax.axhline(y=0.5, color='grey', linestyle='--', alpha=0.35); ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(axis='y', alpha=0.3)
axes[0].set_ylabel('Overall Survival Probability', fontsize=12)
plt.tight_layout(); plt.savefig('KM_Treatment_by_Phenotype.png', dpi=310, bbox_inches='tight'); plt.show()

print("\n— Treatment Comparison (Unadjusted) —")
print(f"{'Phenotype':<14} {'Treatment':<22} {'N':>6} {'Median OS':>12}")
for row in tx_rows:
    med_str = f"{row['Median_OS']:.2f} yrs" if row['Median_OS'] else "NR"
    print(f"{row['Phenotype']:<14} {row['Treatment']:<22} {row['N']:>6,} {med_str:>12}")
print("\n— SO vs SC p-values —")
for pheno, p in tx_pvals.items():
    ps = '< 0.001' if p < 0.001 else f'= {p:.4f}'
    sig = ' significant' if p < 0.05 else ' (not significant)'
    print(f"  {pheno}: p {ps}{sig}")
pd.DataFrame(tx_rows).to_csv('Treatment_by_Phenotype_Unadjusted.csv', index=False)
print("Section 10 Complete — Saved: KM_Treatment_by_Phenotype.png")

# ============================================================================
# @title Section 11 : Propensity Score Matching (with integrated diagnostics)
# ============================================================================
# FIX: the original notebook re-derived AGE_CLEAN/NB_METS_CLEAN separately in
# this section, in "REVISION R4/R7" (which clipped instead of dropped
# NB_METASTASES_NUM>50), and again in a final "balance plot" cell (which
# skipped outlier cleaning entirely) — three different cohorts for what was
# presented as one PSM analysis. Here everything reads AGE_CLEAN/NB_METS_CLEAN
# from surv_df (built once, in Section 4+5), so matching, the propensity
# C-statistic, and the balance table are all guaranteed to describe the same
# patients.
print("=" * 60); print("SECTION 11 — PROPENSITY SCORE MATCHING"); print("=" * 60)

psm_base = surv_df[surv_df['TREATMENT'].isin(['Surgery_Only', 'Surgery+Chemo'])].copy()
psm_base['TREATED'] = (psm_base['TREATMENT'] == 'Surgery+Chemo').astype(int)
ps_feats = ['AGE_CLEAN', 'NB_METS_CLEAN', 'MALE'] + [c for c in ['T_T3', 'T_T4', 'N_N1', 'N_N2', 'M_M1'] if c in psm_base.columns]
psm_df2 = psm_base.dropna(subset=ps_feats + ['SURVIVAL_TRUNC', 'EVENT_TRUNC']).copy()
psm_df2 = psm_df2[psm_df2['SURVIVAL_TRUNC'] > 0].reset_index(drop=True)
print(f"\nSO: {(psm_df2['TREATED']==0).sum():,} | SC: {(psm_df2['TREATED']==1).sum():,} | Total: {len(psm_df2):,}")

X_ps = psm_df2[ps_feats].fillna(0); y_ps = psm_df2['TREATED']
scaler = StandardScaler(); X_sc = scaler.fit_transform(X_ps)
lr_ps = LogisticRegression(random_state=42, max_iter=1000); lr_ps.fit(X_sc, y_ps)
psm_df2['PROPENSITY'] = lr_ps.predict_proba(X_sc)[:, 1]

np.random.seed(42)
treated_pool = psm_df2[psm_df2['TREATED'] == 1].copy()
untreated_pool = psm_df2[psm_df2['TREATED'] == 0].copy()
CALIPER = 0.05; mt_rows = []; mc_rows = []; used_ctrl = set()
for idx, row in treated_pool.iterrows():
    prop = row['PROPENSITY']
    cands = untreated_pool[(abs(untreated_pool['PROPENSITY'] - prop) < CALIPER) & (~untreated_pool.index.isin(used_ctrl))]
    if len(cands) > 0:
        best_idx = (cands['PROPENSITY'] - prop).abs().idxmin()
        mt_rows.append(row); mc_rows.append(untreated_pool.loc[best_idx]); used_ctrl.add(best_idx)

matched_t = pd.DataFrame(mt_rows).reset_index(drop=True)
matched_c = pd.DataFrame(mc_rows).reset_index(drop=True)
matched_df = pd.concat([matched_t, matched_c]).reset_index(drop=True)
print(f"Matched pairs: {len(matched_t):,} | Total matched: {len(matched_df):,}")

fig, ax = plt.subplots(figsize=(12, 7))
psm_results = {}
for tv, label, col in [(0, 'Surgery Only', '#1B5E20'), (1, 'Surgery+Chemo', '#43A047')]:
    tdata = matched_df[matched_df['TREATED'] == tv]
    T = tdata['SURVIVAL_TRUNC'].astype(float).values; E = tdata['EVENT_TRUNC'].astype(int).values
    kmf = KaplanMeierFitter(); kmf.fit(T, E, label=f"{label} (n={len(tdata):,})")
    kmf.plot_survival_function(ax=ax, color=col, linewidth=2.5, ci_show=True, ci_alpha=0.15)
    med = kmf.median_survival_time_
    psm_results[label] = {'n': len(tdata), 'median': round(float(med), 2) if med and not np.isinf(med) else None}
so_m = matched_df[matched_df['TREATED'] == 0]; sc_m = matched_df[matched_df['TREATED'] == 1]
lr_psm = logrank_test(so_m['SURVIVAL_TRUNC'].astype(float), sc_m['SURVIVAL_TRUNC'].astype(float),
                       so_m['EVENT_TRUNC'].astype(int), sc_m['EVENT_TRUNC'].astype(int))
p_psm = lr_psm.p_value; ps_psm = '< 0.001' if p_psm < 0.001 else f'= {p_psm:.4f}'
ax.set_xlabel('Time (Years)', fontsize=13); ax.set_ylabel('Overall Survival Probability', fontsize=13)
ax.set_title(f'PSM: Surgery Only vs Surgery+Chemo\n{len(matched_t):,} matched pairs | Log-rank p {ps_psm}', fontsize=12, fontweight='bold', pad=12)
ax.set_xlim(0, MAX_FOLLOW_UP); ax.set_ylim(0, 1.05); ax.axhline(y=0.5, color='grey', linestyle='--', alpha=0.4)
ax.legend(loc='upper right', frameon=True, fontsize=12); ax.grid(axis='y', alpha=0.3)
plt.tight_layout(); plt.savefig('PSM_KM_Overall.png', dpi=310, bbox_inches='tight'); plt.show()

print("\n— PSM Results Summary —")
so_str = f"{psm_results.get('Surgery Only', {}).get('median', 'NR')}"
sc_str = f"{psm_results.get('Surgery+Chemo', {}).get('median', 'NR')}"
print(f"{'Overall':<20} {so_str:>10} {sc_str:>10} {ps_psm:>12}")

psm_pheno_rows = []
fig, axes = plt.subplots(1, 3, figsize=(21, 7), sharey=True)
fig.suptitle('PSM Survival — SO vs SC by Phenotype', fontsize=13, fontweight='bold', y=1.02)
for ax, pheno in zip(axes, PHENOTYPES):
    pdata = matched_df[matched_df['PHENOTYPE'] == pheno]
    if len(pdata) < 40:
        ax.text(0.5, 0.5, f'Insufficient matched data\nn={len(pdata)}', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'{pheno}', fontsize=12, fontweight='bold', color=PHENOTYPE_COLORS[pheno])
        continue
    ph_so = pdata[pdata['TREATED'] == 0]; ph_sc = pdata[pdata['TREATED'] == 1]; ph_meds = {}
    for tv, label, col in [(0, 'Surgery Only', '#1B5E20'), (1, 'Surgery+Chemo', '#43A047')]:
        tdata = pdata[pdata['TREATED'] == tv]
        if len(tdata) < 10: continue
        kmf = KaplanMeierFitter()
        kmf.fit(tdata['SURVIVAL_TRUNC'].astype(float), tdata['EVENT_TRUNC'].astype(int), label=f"{label} (n={len(tdata):,})")
        kmf.plot_survival_function(ax=ax, color=col, linewidth=2.5, ci_show=True, ci_alpha=0.15)
        med = kmf.median_survival_time_
        ph_meds[label] = round(float(med), 2) if med and not np.isinf(med) else None
    if len(ph_so) >= 10 and len(ph_sc) >= 10:
        lr_ph = logrank_test(ph_so['SURVIVAL_TRUNC'].astype(float), ph_sc['SURVIVAL_TRUNC'].astype(float),
                              ph_so['EVENT_TRUNC'].astype(int), ph_sc['EVENT_TRUNC'].astype(int))
        p_ph = lr_ph.p_value; ps_ph = '< 0.001' if p_ph < 0.001 else f'= {p_ph:.4f}'
    else:
        p_ph = 1.0; ps_ph = 'N/A'
    psm_pheno_rows.append({'Phenotype': pheno, 'SO_median': ph_meds.get('Surgery Only'),
                            'SC_median': ph_meds.get('Surgery+Chemo'), 'p_value': round(p_ph, 4),
                            'n_SO': len(ph_so), 'n_SC': len(ph_sc)})
    ax.set_title(f'{pheno}\n(SO vs SC p {ps_ph})', fontsize=12, fontweight='bold', color=PHENOTYPE_COLORS[pheno])
    ax.set_xlabel('Time (Years)', fontsize=12); ax.set_xlim(0, MAX_FOLLOW_UP); ax.set_ylim(0, 1.05)
    ax.axhline(y=0.5, color='grey', linestyle='--', alpha=0.35); ax.legend(loc='upper right', frameon=True, fontsize=10)
    ax.grid(axis='y', alpha=0.3)
axes[0].set_ylabel('Overall Survival Probability', fontsize=12)
plt.tight_layout(); plt.savefig('PSM_KM_by_Phenotype.png', dpi=310, bbox_inches='tight'); plt.show()
pd.DataFrame(psm_pheno_rows).to_csv('PSM_Results_by_Phenotype.csv', index=False)

# --- Integrated diagnostics: propensity C-statistic + before/after overlap ---
# FIX: reuses lr_ps/scaler/psm_df2/matched_df from above directly instead of
# rebuilding the propensity model from a re-cleaned cohort (which is what
# caused the original notebook's "R4" diagnostics to report a slightly
# different N than the matching step it was supposedly diagnosing).
from sklearn.metrics import roc_auc_score
auc = roc_auc_score(y_ps, psm_df2['PROPENSITY'])
print(f"\n— Propensity Model Diagnostics —")
print(f"Propensity model C-statistic (AUC): {auc:.3f}")
print(f"Covariates: {ps_feats}")
print(f"N: {len(psm_df2):,} Treated: {int(y_ps.sum()):,} Untreated: {int((1-y_ps).sum()):,}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for treated, label, col in [(1, 'Surgery+Chemo', '#2E7D32'), (0, 'Surgery Only', '#1565C0')]:
    grp = psm_df2[psm_df2['TREATED'] == treated]['PROPENSITY']
    axes[0].hist(grp, bins=40, alpha=0.5, color=col, label=label, density=True)
axes[0].set_xlabel('Propensity Score'); axes[0].set_ylabel('Density')
axes[0].set_title('Before Matching'); axes[0].legend(); axes[0].grid(alpha=0.3)
for treated, label, col in [(1, 'Surgery+Chemo', '#2E7D32'), (0, 'Surgery Only', '#1565C0')]:
    grp = matched_df[matched_df['TREATED'] == treated]['PROPENSITY']
    axes[1].hist(grp, bins=40, alpha=0.5, color=col, label=label, density=True)
axes[1].set_xlabel('Propensity Score'); axes[1].set_ylabel('Density')
axes[1].set_title('After Matching'); axes[1].legend(); axes[1].grid(alpha=0.3)
plt.suptitle('Propensity Score Overlap', fontweight='bold')
plt.tight_layout(); plt.savefig('PSM_Overlap_Histogram.png', dpi=310, bbox_inches='tight'); plt.show()

# --- SMD balance table (before vs after matching, same cohort throughout) ---
def calc_smd(d, treat_col, covariate):
    a = d[d[treat_col] == 1][covariate].dropna(); b = d[d[treat_col] == 0][covariate].dropna()
    if len(a) == 0 or len(b) == 0: return np.nan
    pooled_sd = np.sqrt((a.var() + b.var()) / 2)
    return np.nan if pooled_sd == 0 else abs(a.mean() - b.mean()) / pooled_sd

balance_rows = []
for cov in ps_feats:
    smd_before = calc_smd(psm_df2, 'TREATED', cov)
    smd_after = calc_smd(matched_df, 'TREATED', cov)
    balance_rows.append({'Covariate': cov, 'SMD_before': round(smd_before, 3), 'SMD_after': round(smd_after, 3)})
balance_df = pd.DataFrame(balance_rows)
print("\n— Covariate Balance (SMD) —")
print(balance_df.to_string(index=False))
balance_df.to_csv('PSM_Balance_Table.csv', index=False)

print("Section 11 Complete — Saved: PSM_KM_Overall.png, PSM_KM_by_Phenotype.png, "
      "PSM_Overlap_Histogram.png, PSM_Balance_Table.csv")

# ============================================================================
# @title Section 12 : Model Benchmark — CART vs Full TNM Cox vs Multivariable Cox
# ============================================================================
# FIX (two bugs from the original notebook's benchmarking cells):
#   1. Entry year was computed on cart_df (19,465 rows) then assigned onto
#      bench_df/surv_df (14,759 rows) via `.values` — a raw positional copy
#      between differently-sized, differently-ordered frames. Here ENTRY_YEAR
#      is computed directly on surv_df's own columns, so alignment is
#      guaranteed by construction instead of by accident.
#   2. The "Full TNM Cox" model previously re-ran pd.get_dummies on a
#      non-reset train_df/test_df index and concatenated it against a
#      reset-index survival-column slice — most rows failed to align and were
#      silently dropped by dropna(), corrupting ~40% of the training set and
#      producing an implausible near-random C-index. Here it reuses surv_df's
#      own T_T0..M_M1 dummy columns (already aligned, built once in
#      Section 4+5) instead of re-deriving and re-concatenating them.
print("=" * 70); print("SECTION 12 — MODEL BENCHMARK: CART vs TRADITIONAL COX REGRESSION"); print("=" * 70)

bench_df = surv_df.copy()
print(f"\nStarting cohort: {len(bench_df):,} patients")
print(f"Events (deaths): {int(bench_df['EVENT_TRUNC'].sum()):,}")

# --- Approximate registry entry year, computed directly on surv_df ---
bench_df['LASTNDT_parsed'] = pd.to_datetime(bench_df['LASTNDT_F1'], errors='coerce')
bench_df['APPROX_ENTRY_YEAR'] = bench_df['LASTNDT_parsed'].dt.year - bench_df['SURVIVAL_YEARS']
bench_df['APPROX_ENTRY_YEAR'] = pd.to_numeric(bench_df['APPROX_ENTRY_YEAR'], errors='coerce')
bench_df.loc[(bench_df['APPROX_ENTRY_YEAR'] < 1990) | (bench_df['APPROX_ENTRY_YEAR'] > 2023), 'APPROX_ENTRY_YEAR'] = np.nan

valid_yrs = bench_df['APPROX_ENTRY_YEAR'].dropna()
temporal_split_available = len(valid_yrs) > 100
if temporal_split_available:
    SPLIT_YEAR = int(valid_yrs.median())
    train_df = bench_df[bench_df['APPROX_ENTRY_YEAR'] <= SPLIT_YEAR].copy()
    test_df = bench_df[bench_df['APPROX_ENTRY_YEAR'] > SPLIT_YEAR].copy()
    print(f"\nTemporal split (approx. registry entry year, median={SPLIT_YEAR}):")
    print(f"  Training (<={SPLIT_YEAR}): {len(train_df):,} patients")
    print(f"  Validation (>{SPLIT_YEAR}): {len(test_df):,} patients")
else:
    print("\nNot enough valid entry-year data for temporal split — Section 12 skipped")

pheno_map = {'Favourable': 0, 'Intermediate': 1, 'Adverse': 2}

if temporal_split_available:
    # ---- Model 1: CART phenotype score only ----
    print("\n" + "-" * 70); print("MODEL 1: CART PHENOTYPE SCORE (ordinal 0/1/2)"); print("-" * 70)
    train_cart = train_df[['PHENOTYPE', 'SURVIVAL_TRUNC', 'EVENT_TRUNC']].copy()
    train_cart['PHENOTYPE_SCORE'] = train_cart['PHENOTYPE'].map(pheno_map)
    train_cart = train_cart[['PHENOTYPE_SCORE', 'SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()
    test_cart = test_df[['PHENOTYPE', 'SURVIVAL_TRUNC', 'EVENT_TRUNC']].copy()
    test_cart['PHENOTYPE_SCORE'] = test_cart['PHENOTYPE'].map(pheno_map)
    test_cart = test_cart[['PHENOTYPE_SCORE', 'SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()

    cph_cart = CoxPHFitter()
    cph_cart.fit(train_cart, duration_col='SURVIVAL_TRUNC', event_col='EVENT_TRUNC')
    ci_cart_tr = concordance_index(train_cart['SURVIVAL_TRUNC'], -cph_cart.predict_partial_hazard(train_cart), train_cart['EVENT_TRUNC'])
    ci_cart_val = concordance_index(test_cart['SURVIVAL_TRUNC'], -cph_cart.predict_partial_hazard(test_cart), test_cart['EVENT_TRUNC'])
    print(f"  Training n: {len(train_cart):,} | Validation n: {len(test_cart):,}")
    print(f"  Training C-index:   {ci_cart_tr:.3f}")
    print(f"  Validation C-index: {ci_cart_val:.3f}")

    # ---- Model 2: Full TNM Cox (uses surv_df's own aligned dummy columns) ----
    print("\n" + "-" * 70); print("MODEL 2: FULL TNM COX REGRESSION (All Staging Variables)"); print("-" * 70)
    train_tnm = train_df[tnm_feat_cols + ['SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()
    test_tnm = test_df[tnm_feat_cols + ['SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()

    cph_tnm = CoxPHFitter(penalizer=0.1)
    cph_tnm.fit(train_tnm, duration_col='SURVIVAL_TRUNC', event_col='EVENT_TRUNC')
    ci_tnm_tr = concordance_index(train_tnm['SURVIVAL_TRUNC'], -cph_tnm.predict_partial_hazard(train_tnm), train_tnm['EVENT_TRUNC'])
    ci_tnm_val = concordance_index(test_tnm['SURVIVAL_TRUNC'], -cph_tnm.predict_partial_hazard(test_tnm), test_tnm['EVENT_TRUNC'])
    print(f"  Training n: {len(train_tnm):,} | Validation n: {len(test_tnm):,}")
    print(f"  Training C-index:   {ci_tnm_tr:.3f}")
    print(f"  Validation C-index: {ci_tnm_val:.3f}")
    print(f"  Features: all binary TNM dummies ({len(tnm_feat_cols)} variables)")

    # ---- Model 3: Multivariable Cox (Phenotype + Age + Metastases + Sex) ----
    print("\n" + "-" * 70); print("MODEL 3: MULTIVARIABLE COX (Phenotype + Age + Metastases + Sex)"); print("-" * 70)
    mv_cols = ['PHENOTYPE', 'AGE_AT_REFERRAL', 'NB_METASTASES_NUM', 'GENDER', 'SURVIVAL_TRUNC', 'EVENT_TRUNC']

    def _prep_mv(d):
        out = d[mv_cols].copy()
        out['PHENOTYPE_SCORE'] = out['PHENOTYPE'].map(pheno_map)
        out['AGE_10YR'] = pd.to_numeric(out['AGE_AT_REFERRAL'], errors='coerce') / 10
        out['NB_METS'] = pd.to_numeric(out['NB_METASTASES_NUM'], errors='coerce')
        out['MALE'] = (out['GENDER'] == 'Male').astype(int)
        return out[['PHENOTYPE_SCORE', 'AGE_10YR', 'NB_METS', 'MALE', 'SURVIVAL_TRUNC', 'EVENT_TRUNC']].dropna()

    train_mv3 = _prep_mv(train_df); test_mv3 = _prep_mv(test_df)
    cph_mv3 = CoxPHFitter()
    cph_mv3.fit(train_mv3, duration_col='SURVIVAL_TRUNC', event_col='EVENT_TRUNC')
    ci_mv_tr = concordance_index(train_mv3['SURVIVAL_TRUNC'], -cph_mv3.predict_partial_hazard(train_mv3), train_mv3['EVENT_TRUNC'])
    ci_mv_val = concordance_index(test_mv3['SURVIVAL_TRUNC'], -cph_mv3.predict_partial_hazard(test_mv3), test_mv3['EVENT_TRUNC'])
    print(f"  Training n: {len(train_mv3):,} | Validation n: {len(test_mv3):,}")
    print(f"  Training C-index:   {ci_mv_tr:.3f}")
    print(f"  Validation C-index: {ci_mv_val:.3f}")
    print(f"  Features: Phenotype + Age + N Metastases + Sex")

    # ---- Summary table + plot ----
    print("\n" + "=" * 80); print("BENCHMARK SUMMARY — VALIDATION C-INDEX COMPARISON"); print("=" * 80)
    results = [("CART Phenotyping (Current Study)", ci_cart_tr, ci_cart_val),
               ("Full TNM Cox Regression", ci_tnm_tr, ci_tnm_val),
               ("Multivariable Cox (Phenotype + Clinical)", ci_mv_tr, ci_mv_val)]
    print(f"\n{'Model':<42} {'Train C':>10} {'Val C':>10}")
    for name, tr, val in results:
        print(f"{name:<42} {tr:>10.3f} {val:>10.3f}")
    print(f"\nDifference (Full TNM - CART):        {ci_tnm_val - ci_cart_val:+.3f}")
    print(f"Difference (Multivariable - CART):   {ci_mv_val - ci_cart_val:+.3f}")

    fig, ax = plt.subplots(figsize=(11, 7))
    model_names = ["CART Phenotyping\n(Current Study)", "Full TNM Cox", "Multivariable Cox"]
    val_scores = [ci_cart_val, ci_tnm_val, ci_mv_val]; train_scores = [ci_cart_tr, ci_tnm_tr, ci_mv_tr]
    colors = ['#1565C0', '#F57C00', '#6A1B9A']
    x = np.arange(len(model_names)); width = 0.35
    bars1 = ax.bar(x - width/2, train_scores, width, label='Training', color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, val_scores, width, label='Validation', color=colors, alpha=1.0, edgecolor='black', linewidth=2)
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.4, linewidth=2, label='Random (C=0.5)')
    ax.set_ylabel('Concordance Index (C-index)', fontsize=12, fontweight='bold')
    ax.set_title(f'Model Performance Comparison: CART vs Traditional Cox Regression\n'
                 f'Temporal Validation (Training <={SPLIT_YEAR}, Validation >{SPLIT_YEAR})', fontsize=13, fontweight='bold', pad=20)
    ax.set_xticks(x); ax.set_xticklabels(model_names, fontsize=11)
    ax.set_ylim(0.45, 0.75); ax.legend(fontsize=11, loc='lower right', framealpha=0.95)
    ax.grid(axis='y', alpha=0.3, linestyle=':', linewidth=0.8)
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01, f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout(); plt.savefig('Model_Benchmark_Comparison.png', dpi=310, bbox_inches='tight'); plt.show()

    pd.DataFrame(results, columns=['Model', 'Train_Cindex', 'Val_Cindex']).to_csv('Model_Benchmark_Results.csv', index=False)
    print("Section 12 Complete — Saved: Model_Benchmark_Comparison.png, Model_Benchmark_Results.csv")
