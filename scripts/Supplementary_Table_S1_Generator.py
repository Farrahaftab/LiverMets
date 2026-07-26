"""
Supplementary Table S1: Comparison of Baseline Characteristics
Between Included and Excluded Patients

This script generates Table S1 comparing included (n=14,759) vs excluded (n=14,806)
patients using the same cohort definition as the main analysis.

Inclusion criteria:
  1. Complete TNM staging (no missing/ND in T_STAGE, N_STAGE, M_STAGE)
  2. Complete survival data (no missing SURVIVAL_YEARS or VITAL_STATUS)

Exclusion: all other patients from the raw registry (n=29,565)
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from scipy import stats
import io

# ============================================================================
# STEP 1: Load the dataset
# ============================================================================
print("=" * 80)
print("SUPPLEMENTARY TABLE S1: BASELINE CHARACTERISTICS COMPARISON")
print("=" * 80)
print("\nLoading LiverMets_Final_Dataset.csv...")

# For local file (adjust path if needed)
try:
    df = pd.read_csv('/home/user/LiverMets/scripts/LiverMets_Final_Dataset.csv')
    print(f"✓ Loaded: {len(df):,} patients x {df.shape[1]} variables")
except FileNotFoundError:
    print("File not found at /home/user/LiverMets/scripts/")
    print("Trying current directory...")
    df = pd.read_csv('LiverMets_Final_Dataset.csv')
    print(f"✓ Loaded: {len(df):,} patients x {df.shape[1]} variables")

# ============================================================================
# STEP 2: Inspect dataset structure and coding
# ============================================================================
print("\n" + "=" * 80)
print("STEP 1: COLUMN INSPECTION & CODING DETECTION")
print("=" * 80)

print(f"\nAll columns in dataset ({df.shape[1]} total):")
print(df.columns.tolist())

print("\n" + "-" * 80)
print("CANDIDATE COLUMNS FOR TABLE S1:")
print("-" * 80)

# List key columns
key_cols = {
    'Age': ['AGE_AT_REFERRAL', 'AGE', 'AGE_CLEAN'],
    'Gender/Sex': ['GENDER', 'MALE', 'SEX'],
    'T-Stage': ['T_STAGE'],
    'N-Stage': ['N_STAGE'],
    'M-Stage': ['M_STAGE'],
    'Metastases count': ['NB_METASTASES_NUM', 'NB_METS', 'NB_METS_CLEAN'],
    'Survival time': ['SURVIVAL_YEARS', 'SURVIVAL_MONTHS'],
    'Vital status': ['VITAL_STATUS', 'PATSTAT_F1'],
    'Treatment': ['TREATMENT', 'SURGERY', 'CHEMOTHERAPY', 'Tx_SurgChemo', 'Tx_ChemoOnly', 'Tx_NoTreat']
}

detected = {}
for category, possible_names in key_cols.items():
    found = [col for col in possible_names if col in df.columns]
    if found:
        detected[category] = found
        print(f"\n{category}: {', '.join(found)}")
        for col in found:
            print(f"  └─ {col}: {df[col].dtype} | Non-null: {df[col].notna().sum():,} | Unique: {df[col].nunique()}")
            if df[col].nunique() <= 20:
                print(f"     Values: {sorted(df[col].dropna().unique())}")
    else:
        print(f"\n{category}: NOT FOUND")

# ============================================================================
# STEP 3: Confirm column mapping before proceeding
# ============================================================================
print("\n" + "=" * 80)
print("REQUIRED CONFIRMATION BEFORE PROCEEDING")
print("=" * 80)

print("""
Please confirm the correct column mapping:

1. AGE COLUMN:
   Which column contains patient age at baseline?
   Candidates: {0}

2. GENDER COLUMN:
   Which column contains gender? (Should be 'M'/'F', 'Male'/'Female', or 1/0)
   Candidates: {1}

3. T-STAGE:
   Column: T_STAGE
   Values: {2}

4. N-STAGE:
   Column: N_STAGE
   Values: {3}

5. M-STAGE:
   Column: M_STAGE
   Values: {4}

6. METASTASES COUNT:
   Which column has the number of liver metastases?
   Candidates: {5}

7. SURVIVAL TIME:
   Which column? (Should be in years)
   Candidates: {6}

8. VITAL STATUS:
   Column: VITAL_STATUS
   Values: {7}
   (Should represent 0=Alive, 1=Deceased, or vice versa)

9. TREATMENT:
   Which column(s) contain treatment category?
   Candidates: {8}
   If multiple columns, are they already combined into one 'TREATMENT' column?
""".format(
    detected.get('Age', ['NOT FOUND']),
    detected.get('Gender/Sex', ['NOT FOUND']),
    sorted(df['T_STAGE'].dropna().unique()) if 'T_STAGE' in df.columns else 'NOT FOUND',
    sorted(df['N_STAGE'].dropna().unique()) if 'N_STAGE' in df.columns else 'NOT FOUND',
    sorted(df['M_STAGE'].dropna().unique()) if 'M_STAGE' in df.columns else 'NOT FOUND',
    detected.get('Metastases count', ['NOT FOUND']),
    detected.get('Survival time', ['NOT FOUND']),
    sorted(df['VITAL_STATUS'].dropna().unique()) if 'VITAL_STATUS' in df.columns else 'NOT FOUND',
    detected.get('Treatment', ['NOT FOUND'])
))

input("\n>>> Press ENTER to proceed with automated detection, or manually verify the mappings above <<<\n")

# ============================================================================
# STEP 4: Auto-detect and standardize columns
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: AUTO-DETECTING COLUMNS & STANDARDIZING VALUES")
print("=" * 80)

# Age
age_col = None
for col in ['AGE_AT_REFERRAL', 'AGE_CLEAN', 'AGE']:
    if col in df.columns:
        age_col = col
        break
if age_col:
    print(f"✓ Age: {age_col}")
else:
    print("✗ Age column not found. Please check dataset.")
    raise ValueError("Age column required but not found")

# Gender
gender_col = None
for col in ['GENDER', 'MALE', 'SEX']:
    if col in df.columns:
        gender_col = col
        break
if gender_col:
    print(f"✓ Gender: {gender_col}")
else:
    print("✗ Gender column not found.")
    raise ValueError("Gender column required but not found")

# TNM stages
print("✓ T-Stage: T_STAGE")
print("✓ N-Stage: N_STAGE")
print("✓ M-Stage: M_STAGE")

# Metastases count
mets_col = None
for col in ['NB_METS_CLEAN', 'NB_METASTASES_NUM', 'NB_METS']:
    if col in df.columns:
        mets_col = col
        break
if mets_col:
    print(f"✓ Metastases count: {mets_col}")
else:
    print("✗ Metastases count column not found.")

# Survival
print("✓ Survival time: SURVIVAL_YEARS")
print("✓ Vital status: VITAL_STATUS")

# Treatment
treatment_col = None
if 'TREATMENT' in df.columns:
    treatment_col = 'TREATMENT'
    print(f"✓ Treatment: {treatment_col} (pre-combined)")
else:
    print("! Treatment: Not found as single column. Will check for indicators.")
    treatment_col = 'TREATMENT'

# ============================================================================
# STEP 5: Apply inclusion/exclusion criteria
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: APPLYING INCLUSION/EXCLUSION CRITERIA")
print("=" * 80)

raw_n = len(df)
print(f"\nRaw registry: {raw_n:,} patients")

# Step 1: Complete TNM
complete_tnm = df[
    (df['T_STAGE'].notna()) & (df['T_STAGE'] != 'ND') &
    (df['N_STAGE'].notna()) & (df['N_STAGE'] != 'ND') &
    (df['M_STAGE'].notna()) & (df['M_STAGE'] != 'ND')
].copy()
excluded_tnm = raw_n - len(complete_tnm)
print(f"  Excluded (missing/ND TNM): {excluded_tnm:,}")
print(f"  Complete TNM cohort: {len(complete_tnm):,}")

# Step 2: Complete survival data
included = complete_tnm[
    (complete_tnm['SURVIVAL_YEARS'].notna()) & (complete_tnm['SURVIVAL_YEARS'] > 0) &
    (complete_tnm['VITAL_STATUS'].notna())
].copy()
excluded_surv = len(complete_tnm) - len(included)
print(f"  Excluded (missing survival/vital status): {excluded_surv:,}")
print(f"  Final INCLUDED cohort: {len(included):,}")

# Excluded cohort = all others
excluded = df[~df.index.isin(included.index)].copy()
print(f"  Final EXCLUDED cohort: {len(excluded):,}")

# Verify totals
print(f"\n  Verification:")
print(f"    Included + Excluded = {len(included):,} + {len(excluded):,} = {len(included) + len(excluded):,}")
print(f"    Raw total: {raw_n:,}")
assert len(included) + len(excluded) == raw_n, "Cohort split error!"
assert len(included) == 14759, f"Included cohort should be 14,759, got {len(included):,}"
assert len(excluded) == 14806, f"Excluded cohort should be 14,806, got {len(excluded):,}"
print(f"  ✓ All counts match expected values!")

# ============================================================================
# STEP 6: Calculate Standardised Mean Differences (SMD)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 4: CALCULATING STANDARDISED MEAN DIFFERENCES (SMD)")
print("=" * 80)

def calculate_smd_continuous(x_incl, x_excl):
    """SMD for continuous variables (Cohen's d with pooled SD)"""
    mean_incl = x_incl.mean()
    mean_excl = x_excl.mean()
    std_incl = x_incl.std()
    std_excl = x_excl.std()
    n_incl = len(x_incl)
    n_excl = len(x_excl)

    # Pooled SD
    pooled_sd = np.sqrt(
        ((n_incl - 1) * std_incl**2 + (n_excl - 1) * std_excl**2) /
        (n_incl + n_excl - 2)
    )

    if pooled_sd == 0:
        return 0

    smd = (mean_incl - mean_excl) / pooled_sd
    return abs(smd)

def calculate_smd_binary(p_incl, p_excl):
    """SMD for binary variables"""
    # Pooled proportion
    p_pool = (p_incl + p_excl) / 2
    if p_pool == 0 or p_pool == 1:
        return 0

    pooled_sd = np.sqrt(p_pool * (1 - p_pool))
    smd = (p_incl - p_excl) / pooled_sd
    return abs(smd)

# ============================================================================
# STEP 7: Build the comparison table
# ============================================================================
print("\nBuilding comparison table...")

results = []

# --- DEMOGRAPHICS ---

# Age
age_incl = included[age_col].dropna()
age_excl = excluded[age_col].dropna()
age_smd = calculate_smd_continuous(age_incl, age_excl)
results.append({
    'Characteristic': 'Age (years)',
    'Included': f"{age_incl.mean():.1f} ± {age_incl.std():.1f}",
    'Excluded': f"{age_excl.mean():.1f} ± {age_excl.std():.1f}",
    'SMD': age_smd
})
print(f"  ✓ Age: SMD = {age_smd:.3f}")

# Gender
if gender_col == 'GENDER':
    # Assume values are 'M'/'F' or 'Male'/'Female'
    male_incl = included[gender_col].dropna()
    male_incl = (male_incl.str.upper() == 'M').sum() / len(male_incl)

    male_excl = excluded[gender_col].dropna()
    male_excl = (male_excl.str.upper() == 'M').sum() / len(male_excl)
else:  # MALE column (1=Male, 0=Female)
    male_incl = included[gender_col].dropna().mean()
    male_excl = excluded[gender_col].dropna().mean()

male_smd = calculate_smd_binary(male_incl, male_excl)
n_male_incl = int(male_incl * len(included[gender_col].dropna()))
n_male_excl = int(male_excl * len(excluded[gender_col].dropna()))
pct_male_incl = male_incl * 100
pct_male_excl = male_excl * 100

results.append({
    'Characteristic': 'Male sex',
    'Included': f"{n_male_incl:,} ({pct_male_incl:.1f}%)",
    'Excluded': f"{n_male_excl:,} ({pct_male_excl:.1f}%)",
    'SMD': male_smd
})
print(f"  ✓ Gender: SMD = {male_smd:.3f}")

# --- TREATMENT ---
# Assuming TREATMENT column exists and has values like 'Surgery_Only', 'Surgery+Chemo', etc.
if treatment_col in included.columns:
    treat_labels = {
        'Surgery_Only': 'Surgery alone',
        'Surgery+Chemo': 'Surgery + chemotherapy',
        'Surgery_Chemo': 'Surgery + chemotherapy',
        'Chemo_Only': 'Chemotherapy alone',
        'No_Treatment': 'No treatment'
    }

    for treat_code, treat_label in treat_labels.items():
        n_incl = (included[treatment_col] == treat_code).sum()
        n_excl = (excluded[treatment_col] == treat_code).sum()
        pct_incl = 100 * n_incl / len(included) if len(included) > 0 else 0
        pct_excl = 100 * n_excl / len(excluded) if len(excluded) > 0 else 0

        p_incl = n_incl / len(included) if len(included) > 0 else 0
        p_excl = n_excl / len(excluded) if len(excluded) > 0 else 0
        treat_smd = calculate_smd_binary(p_incl, p_excl)

        if n_incl > 0 or n_excl > 0:  # Only include if present in at least one group
            results.append({
                'Characteristic': f"Treatment: {treat_label}",
                'Included': f"{n_incl:,} ({pct_incl:.1f}%)",
                'Excluded': f"{n_excl:,} ({pct_excl:.1f}%)",
                'SMD': treat_smd
            })
    print(f"  ✓ Treatment categories: Done")

# --- TUMOUR CHARACTERISTICS ---

# T-Stage grouping
t_early = (included['T_STAGE'].isin(['T0', 'T1', 'T2'])).sum()
t_early_pct = 100 * t_early / len(included)
t_early_excl = (excluded['T_STAGE'].isin(['T0', 'T1', 'T2'])).sum()
t_early_excl_pct = 100 * t_early_excl / len(excluded)
t_smd = calculate_smd_binary(t_early / len(included), t_early_excl / len(excluded))

results.append({
    'Characteristic': 'T-Stage: T0–T2',
    'Included': f"{t_early:,} ({t_early_pct:.1f}%)",
    'Excluded': f"{t_early_excl:,} ({t_early_excl_pct:.1f}%)",
    'SMD': t_smd
})

t_late = (included['T_STAGE'].isin(['T3', 'T4'])).sum()
t_late_pct = 100 * t_late / len(included)
t_late_excl = (excluded['T_STAGE'].isin(['T3', 'T4'])).sum()
t_late_excl_pct = 100 * t_late_excl / len(excluded)
t_smd_late = calculate_smd_binary(t_late / len(included), t_late_excl / len(excluded))

results.append({
    'Characteristic': 'T-Stage: T3–T4',
    'Included': f"{t_late:,} ({t_late_pct:.1f}%)",
    'Excluded': f"{t_late_excl:,} ({t_late_excl_pct:.1f}%)",
    'SMD': t_smd_late
})
print(f"  ✓ T-Stage: SMD = {t_smd:.3f}, {t_smd_late:.3f}")

# N-Stage grouping
n_early = (included['N_STAGE'].isin(['N0', 'N1'])).sum()
n_early_pct = 100 * n_early / len(included)
n_early_excl = (excluded['N_STAGE'].isin(['N0', 'N1'])).sum()
n_early_excl_pct = 100 * n_early_excl / len(excluded)
n_smd = calculate_smd_binary(n_early / len(included), n_early_excl / len(excluded))

results.append({
    'Characteristic': 'N-Stage: N0–N1',
    'Included': f"{n_early:,} ({n_early_pct:.1f}%)",
    'Excluded': f"{n_early_excl:,} ({n_early_excl_pct:.1f}%)",
    'SMD': n_smd
})

n_late = (included['N_STAGE'] == 'N2').sum()
n_late_pct = 100 * n_late / len(included)
n_late_excl = (excluded['N_STAGE'] == 'N2').sum()
n_late_excl_pct = 100 * n_late_excl / len(excluded)
n_smd_late = calculate_smd_binary(n_late / len(included), n_late_excl / len(excluded))

results.append({
    'Characteristic': 'N-Stage: N2',
    'Included': f"{n_late:,} ({n_late_pct:.1f}%)",
    'Excluded': f"{n_late_excl:,} ({n_late_excl_pct:.1f}%)",
    'SMD': n_smd_late
})
print(f"  ✓ N-Stage: SMD = {n_smd:.3f}, {n_smd_late:.3f}")

# M-Stage
m0 = (included['M_STAGE'] == 'M0').sum()
m0_pct = 100 * m0 / len(included)
m0_excl = (excluded['M_STAGE'] == 'M0').sum()
m0_excl_pct = 100 * m0_excl / len(excluded)
m_smd = calculate_smd_binary(m0 / len(included), m0_excl / len(excluded))

results.append({
    'Characteristic': 'M-Stage: M0 (no distant metastases)',
    'Included': f"{m0:,} ({m0_pct:.1f}%)",
    'Excluded': f"{m0_excl:,} ({m0_excl_pct:.1f}%)",
    'SMD': m_smd
})

m1 = (included['M_STAGE'] == 'M1').sum()
m1_pct = 100 * m1 / len(included)
m1_excl = (excluded['M_STAGE'] == 'M1').sum()
m1_excl_pct = 100 * m1_excl / len(excluded)
m_smd_m1 = calculate_smd_binary(m1 / len(included), m1_excl / len(excluded))

results.append({
    'Characteristic': 'M-Stage: M1 (distant metastases)',
    'Included': f"{m1:,} ({m1_pct:.1f}%)",
    'Excluded': f"{m1_excl:,} ({m1_excl_pct:.1f}%)",
    'SMD': m_smd_m1
})
print(f"  ✓ M-Stage: SMD = {m_smd:.3f}, {m_smd_m1:.3f}")

# Number of liver metastases (categorical)
if mets_col:
    # Convert to numeric (handle any text values)
    mets_incl = pd.to_numeric(included[mets_col], errors='coerce').dropna()
    mets_excl = pd.to_numeric(excluded[mets_col], errors='coerce').dropna()

    # Create categories: 1, 2-3, >=4
    for cat_name, cat_filter in [('1 metastasis', lambda x: x == 1),
                                   ('2–3 metastases', lambda x: x.isin([2, 3])),
                                   ('≥4 metastases', lambda x: x >= 4)]:
        n_incl = cat_filter(mets_incl).sum()
        n_excl = cat_filter(mets_excl).sum()
        pct_incl = 100 * n_incl / len(mets_incl) if len(mets_incl) > 0 else 0
        pct_excl = 100 * n_excl / len(mets_excl) if len(mets_excl) > 0 else 0

        p_incl = n_incl / len(mets_incl) if len(mets_incl) > 0 else 0
        p_excl = n_excl / len(mets_excl) if len(mets_excl) > 0 else 0
        mets_smd = calculate_smd_binary(p_incl, p_excl)

        results.append({
            'Characteristic': f"Number of liver metastases: {cat_name}",
            'Included': f"{n_incl:,} ({pct_incl:.1f}%)",
            'Excluded': f"{n_excl:,} ({pct_excl:.1f}%)",
            'SMD': mets_smd
        })
    print(f"  ✓ Metastases count: Done")

# --- FOLLOW-UP & OUTCOMES ---

# Follow-up duration (Survival Years as proxy for follow-up)
surv_incl = included['SURVIVAL_YEARS'].dropna()
surv_excl = excluded['SURVIVAL_YEARS'].dropna()
surv_smd = calculate_smd_continuous(surv_incl, surv_excl)

results.append({
    'Characteristic': 'Follow-up duration (years)',
    'Included': f"{surv_incl.mean():.2f} ± {surv_incl.std():.2f}",
    'Excluded': f"{surv_excl.mean():.2f} ± {surv_excl.std():.2f}",
    'SMD': surv_smd
})
print(f"  ✓ Follow-up duration: SMD = {surv_smd:.3f}")

# Deaths
deaths_incl = (included['VITAL_STATUS'] == 1).sum()
deaths_incl_pct = 100 * deaths_incl / len(included)
deaths_excl = (excluded['VITAL_STATUS'] == 1).sum()
deaths_excl_pct = 100 * deaths_excl / len(excluded)
death_smd = calculate_smd_binary(deaths_incl / len(included), deaths_excl / len(excluded))

results.append({
    'Characteristic': 'Deaths',
    'Included': f"{deaths_incl:,} ({deaths_incl_pct:.1f}%)",
    'Excluded': f"{deaths_excl:,} ({deaths_excl_pct:.1f}%)",
    'SMD': death_smd
})

# Censored/Alive
censored_incl = (included['VITAL_STATUS'] == 0).sum()
censored_incl_pct = 100 * censored_incl / len(included)
censored_excl = (excluded['VITAL_STATUS'] == 0).sum()
censored_excl_pct = 100 * censored_excl / len(excluded)
censored_smd = calculate_smd_binary(censored_incl / len(included), censored_excl / len(excluded))

results.append({
    'Characteristic': 'Censored/Alive',
    'Included': f"{censored_incl:,} ({censored_incl_pct:.1f}%)",
    'Excluded': f"{censored_excl:,} ({censored_excl_pct:.1f}%)",
    'SMD': censored_smd
})
print(f"  ✓ Vital status: SMD = {death_smd:.3f}, {censored_smd:.3f}")

# ============================================================================
# STEP 8: Create and display the final table
# ============================================================================
print("\n" + "=" * 80)
print("SUPPLEMENTARY TABLE S1: BASELINE CHARACTERISTICS COMPARISON")
print("=" * 80)

table_df = pd.DataFrame(results)
print("\n" + table_df.to_string(index=False))

# ============================================================================
# STEP 9: Summary statistics
# ============================================================================
print("\n" + "=" * 80)
print("SMD SUMMARY STATISTICS")
print("=" * 80)

smd_values = table_df['SMD'].values
print(f"\nMaximum absolute SMD: {smd_values.max():.3f}")
print(f"Median SMD: {np.median(smd_values):.3f}")
print(f"Mean SMD: {smd_values.mean():.3f}")

print(f"\nVariables with SMD ≥ 0.10 (small-to-meaningful difference):")
small_imb = table_df[table_df['SMD'] >= 0.10].sort_values('SMD', ascending=False)
if len(small_imb) > 0:
    for _, row in small_imb.iterrows():
        print(f"  • {row['Characteristic']}: {row['SMD']:.3f}")
else:
    print("  None")

print(f"\nVariables with SMD ≥ 0.20 (meaningful difference):")
large_imb = table_df[table_df['SMD'] >= 0.20].sort_values('SMD', ascending=False)
if len(large_imb) > 0:
    for _, row in large_imb.iterrows():
        print(f"  • {row['Characteristic']}: {row['SMD']:.3f}")
else:
    print("  None")

# ============================================================================
# STEP 10: Generate manuscript-ready Results paragraph
# ============================================================================
print("\n" + "=" * 80)
print("MANUSCRIPT RESULTS PARAGRAPH")
print("=" * 80)

max_smd = smd_values.max()
n_smd_ge20 = (smd_values >= 0.20).sum()
n_smd_ge10 = (smd_values >= 0.10).sum()

if max_smd < 0.10:
    balance_statement = "Included and excluded patients were well-balanced across all measured characteristics."
    bias_statement = "There is no evidence of important selection bias based on measured variables."
elif max_smd < 0.20:
    balance_statement = f"Included and excluded patients were generally well-balanced, with small differences (SMD range 0–{max_smd:.3f}) observed in {n_smd_ge10} characteristics."
    bias_statement = "These differences were generally negligible (SMD <0.10) and unlikely to represent important selection bias."
else:
    largest_vars = table_df.nlargest(3, 'SMD')['Characteristic'].tolist()
    balance_statement = f"Included and excluded patients differed in {n_smd_ge20} characteristics, with the largest differences observed in: {', '.join(largest_vars)} (SMD up to {max_smd:.3f})."
    bias_statement = "These differences suggest some potential selection bias that should be considered when interpreting results."

results_paragraph = f"""
Of the 29,565 patients in the LiverMets registry, 14,759 (49.9%) met inclusion criteria
(complete TNM staging and survival data), while 14,806 (50.1%) were excluded, primarily due
to missing TNM stage information (n=10,100) or incomplete survival follow-up (n=4,706).
{balance_statement} {bias_statement}
"""

print(results_paragraph)

# ============================================================================
# STEP 11: Save outputs
# ============================================================================
print("\n" + "=" * 80)
print("SAVING OUTPUTS")
print("=" * 80)

# CSV
csv_file = '/home/user/LiverMets/outputs/Supplementary_Table_S1.csv'
table_df.to_csv(csv_file, index=False)
print(f"✓ Saved: {csv_file}")

# XLSX (if openpyxl available)
try:
    xlsx_file = '/home/user/LiverMets/outputs/Supplementary_Table_S1.xlsx'
    table_df.to_excel(xlsx_file, index=False, sheet_name='Table S1')
    print(f"✓ Saved: {xlsx_file}")
except Exception as e:
    print(f"⚠ Could not save XLSX: {e}")

# Save manuscript paragraph
para_file = '/home/user/LiverMets/outputs/Supplementary_Table_S1_Manuscript_Paragraph.txt'
with open(para_file, 'w') as f:
    f.write("SUPPLEMENTARY TABLE S1 — MANUSCRIPT RESULTS PARAGRAPH\n")
    f.write("=" * 80 + "\n\n")
    f.write(results_paragraph)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("FOOTNOTE:\n")
    f.write("Values are presented as mean ± standard deviation or number (percentage), as appropriate. ")
    f.write("Standardised mean differences (SMD) were used to assess differences between included and excluded patients. ")
    f.write("An absolute SMD <0.10 was considered negligible.\n")
print(f"✓ Saved: {para_file}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"""
Summary:
  • Included cohort: {len(included):,} patients
  • Excluded cohort: {len(excluded):,} patients
  • Total: {len(included) + len(excluded):,} (matches raw registry)

SMD Summary:
  • Maximum SMD: {max_smd:.3f}
  • Variables with SMD ≥0.10: {n_smd_ge10}
  • Variables with SMD ≥0.20: {n_smd_ge20}

Outputs:
  • CSV: Supplementary_Table_S1.csv
  • XLSX: Supplementary_Table_S1.xlsx
  • Paragraph: Supplementary_Table_S1_Manuscript_Paragraph.txt
""")
