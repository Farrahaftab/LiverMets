"""
Build ONE canonical analysis-ready dataset from the raw LiverMets registry export.

Consolidates cleaning logic that was previously duplicated (and drifting out of
sync) across Sections 4/9/11/R4/R7/PSM of the notebook:
  - complete-TNM filter + survival/vital-status cleaning (Section 4)
  - CART phenotype derivation (Section 5)
  - age / metastasis-count / sex cleaning used by every Cox / PSM model
    (previously: dropped >50 mets in Section 11, clipped at 50 in R4/R7,
    left uncapped in the final PSM balance cell)
  - recurrence-free survival fields (Section 7)

Every downstream section (KM, Cox, PSM, benchmarking) should load
LiverMets_Analysis_Cohort.csv instead of re-deriving these columns itself.

Usage (Colab):
    uploaded = files.upload()
    df = pd.read_csv(io.BytesIO(uploaded['LiverMets_Final_Dataset.csv']))
    cohort = build_analysis_cohort(df)
    cohort.to_csv('LiverMets_Analysis_Cohort.csv', index=False)

Usage (local):
    python build_analysis_cohort.py LiverMets_Final_Dataset.csv LiverMets_Analysis_Cohort.csv
"""
import sys
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from lifelines import KaplanMeierFitter

MAX_FOLLOW_UP = 15  # years, truncate follow-up here (matches notebook)

PHENOTYPES = ['Favourable', 'Intermediate', 'Adverse']


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


def build_analysis_cohort(df: pd.DataFrame) -> pd.DataFrame:
    print(f"Raw registry: {len(df):,} patients x {df.shape[1]} variables")

    # ---- 1. Complete-TNM filter (Section 4) ----
    tnm_cols = ['T_STAGE', 'N_STAGE', 'M_STAGE']
    mask_tnm = df[tnm_cols].notna().all(axis=1) & (df[tnm_cols] != 'ND').all(axis=1)
    cohort = df[mask_tnm].copy().reset_index(drop=True)
    print(f"Excluded (missing/ND TNM): {len(df) - len(cohort):,}")
    print(f"Complete TNM cohort: {len(cohort):,}")

    # ---- 2. Clean survival / vital status — do NOT impute ----
    cohort['SURVIVAL_YEARS'] = pd.to_numeric(cohort['SURVIVAL_YEARS'], errors='coerce')
    cohort['VITAL_STATUS'] = pd.to_numeric(cohort['VITAL_STATUS'], errors='coerce')
    n_before = len(cohort)
    cohort = cohort.dropna(subset=['SURVIVAL_YEARS', 'VITAL_STATUS'])
    cohort = cohort[cohort['SURVIVAL_YEARS'] > 0].reset_index(drop=True)
    print(f"Excluded (missing survival/vital status): {n_before - len(cohort):,}")
    print(f"Final analysis cohort: {len(cohort):,}")

    # ---- 3. Truncate follow-up at MAX_FOLLOW_UP years ----
    cohort['SURVIVAL_TRUNC'] = cohort['SURVIVAL_YEARS'].clip(upper=MAX_FOLLOW_UP)
    cohort['EVENT_TRUNC'] = np.where(
        cohort['SURVIVAL_YEARS'] > MAX_FOLLOW_UP, 0, cohort['VITAL_STATUS'].astype(int)
    )

    # ---- 4. One-hot TNM dummies ----
    # cohort and tnm_dum share the same fresh 0..n-1 index from reset_index above,
    # so this concat is safe (this is the pattern the notebook's Model-2 benchmark
    # cell got wrong by mixing a reset and an un-reset index).
    tnm_dum = pd.get_dummies(cohort[tnm_cols], prefix=['T', 'N', 'M'])
    cohort = pd.concat([cohort, tnm_dum], axis=1)
    tnm_feat_cols = list(tnm_dum.columns)

    # ---- 5. CART phenotype derivation (Section 5) ----
    cart_model = DecisionTreeClassifier(
        criterion='gini', max_depth=4, min_samples_split=200,
        min_samples_leaf=100, class_weight='balanced', random_state=42
    )
    cart_model.fit(cohort[tnm_feat_cols], cohort['VITAL_STATUS'].astype(int))
    cohort['TERMINAL_NODE'] = cart_model.apply(cohort[tnm_feat_cols])

    node_results = []
    for nid in sorted(cohort['TERMINAL_NODE'].unique()):
        nd = cohort[(cohort['TERMINAL_NODE'] == nid) & (cohort['SURVIVAL_TRUNC'] > 0)]
        if len(nd) < 50:
            continue
        kmf = KaplanMeierFitter()
        kmf.fit(nd['SURVIVAL_TRUNC'].astype(float), nd['EVENT_TRUNC'].astype(int))
        med = kmf.median_survival_time_
        node_results.append({
            'Node': nid,
            'Median_OS': round(float(med), 2) if med and not np.isinf(med) else None,
        })
    node_df = pd.DataFrame(node_results).dropna(subset=['Median_OS'])
    node_df['Phenotype'] = node_df['Median_OS'].apply(assign_phenotype)
    node_map = dict(zip(node_df['Node'], node_df['Phenotype']))
    cohort['PHENOTYPE'] = cohort['TERMINAL_NODE'].map(node_map).fillna('Adverse')

    print("\nPhenotype distribution:")
    for p in PHENOTYPES:
        n = int((cohort['PHENOTYPE'] == p).sum())
        print(f"  {p:<14}: {n:>7,} ({n / len(cohort) * 100:.1f}%)")

    # ---- 6. ONE consistent covariate-cleaning rule set, used by every downstream model ----
    cohort['AGE_CLEAN'] = pd.to_numeric(cohort['AGE_AT_REFERRAL'], errors='coerce')
    cohort.loc[(cohort['AGE_CLEAN'] < 18) | (cohort['AGE_CLEAN'] > 100), 'AGE_CLEAN'] = np.nan
    cohort['AGE_10YR'] = cohort['AGE_CLEAN'] / 10

    cohort['NB_METS_CLEAN'] = pd.to_numeric(cohort['NB_METASTASES_NUM'], errors='coerce')
    cohort.loc[cohort['NB_METS_CLEAN'] > 50, 'NB_METS_CLEAN'] = np.nan  # dropped, not clipped, everywhere

    cohort['MALE'] = (cohort['GENDER'] == 'Male').astype(float)

    # ---- 7. Treatment dummies (reference: Surgery_Only) ----
    if 'TREATMENT' in cohort.columns:
        cohort['Tx_SurgChemo'] = (cohort['TREATMENT'] == 'Surgery+Chemo').astype(int)
        cohort['Tx_ChemoOnly'] = (cohort['TREATMENT'] == 'Chemo_Only').astype(int)
        cohort['Tx_NoTreat'] = (cohort['TREATMENT'] == 'No_Treatment').astype(int)

    # ---- 8. Recurrence-free survival fields (Section 7) ----
    cohort['RFS_EVENT'] = cohort['PATSTAT_F1'].apply(rfs_event)
    cohort['RFS_TRUNC'] = cohort['SURVIVAL_YEARS'].clip(upper=MAX_FOLLOW_UP)
    cohort['RFS_EVENT_TRUNC'] = np.where(
        cohort['SURVIVAL_YEARS'] > MAX_FOLLOW_UP, 0, cohort['RFS_EVENT']
    )

    print(f"\nFinal dataset: {len(cohort):,} patients x {cohort.shape[1]} variables")
    return cohort


if __name__ == '__main__':
    in_path = sys.argv[1] if len(sys.argv) > 1 else 'LiverMets_Final_Dataset.csv'
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'LiverMets_Analysis_Cohort.csv'
    raw = pd.read_csv(in_path)
    result = build_analysis_cohort(raw)
    result.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
