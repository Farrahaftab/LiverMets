"""
Supplementary Table S1 — Simplified version without lambda functions
Compares baseline characteristics: included (n=14,759) vs excluded (n=14,806)
"""

import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np

print("=" * 80)
print("SUPPLEMENTARY TABLE S1: BASELINE CHARACTERISTICS COMPARISON")
print("=" * 80)

# Load dataset
print("\nLoading LiverMets_Final_Dataset.csv...")
try:
    df = pd.read_csv('LiverMets_Final_Dataset.csv')
except:
    df = pd.read_csv('/home/user/LiverMets/scripts/LiverMets_Final_Dataset.csv')
print(f"✓ Loaded: {len(df):,} patients x {df.shape[1]} variables")

# Apply inclusion/exclusion criteria
print("\n" + "=" * 80)
print("APPLYING INCLUSION/EXCLUSION CRITERIA")
print("=" * 80)

raw_n = len(df)
print(f"\nRaw registry: {raw_n:,} patients")

# Complete TNM
complete_tnm = df[
    (df['T_STAGE'].notna()) & (df['T_STAGE'] != 'ND') &
    (df['N_STAGE'].notna()) & (df['N_STAGE'] != 'ND') &
    (df['M_STAGE'].notna()) & (df['M_STAGE'] != 'ND')
].copy()
print(f"  Excluded (missing/ND TNM): {raw_n - len(complete_tnm):,}")
print(f"  Complete TNM cohort: {len(complete_tnm):,}")

# Complete survival
included = complete_tnm[
    (complete_tnm['SURVIVAL_YEARS'].notna()) & (complete_tnm['SURVIVAL_YEARS'] > 0) &
    (complete_tnm['VITAL_STATUS'].notna())
].copy()
print(f"  Excluded (missing survival): {len(complete_tnm) - len(included):,}")
print(f"  Final INCLUDED: {len(included):,}")

# Excluded cohort
excluded = df[~df.index.isin(included.index)].copy()
print(f"  Final EXCLUDED: {len(excluded):,}")
print(f"  ✓ Total: {len(included):,} + {len(excluded):,} = {len(included) + len(excluded):,}")

# SMD function
def smd_continuous(x_incl, x_excl):
    mean_incl = x_incl.mean()
    mean_excl = x_excl.mean()
    pooled_sd = np.sqrt(((len(x_incl)-1)*x_incl.std()**2 + (len(x_excl)-1)*x_excl.std()**2) / (len(x_incl) + len(x_excl) - 2))
    if pooled_sd == 0: return 0
    return abs((mean_incl - mean_excl) / pooled_sd)

def smd_binary(p_incl, p_excl):
    p_pool = (p_incl + p_excl) / 2
    if p_pool == 0 or p_pool == 1: return 0
    pooled_sd = np.sqrt(p_pool * (1 - p_pool))
    return abs((p_incl - p_excl) / pooled_sd)

# Build table
print("\n" + "=" * 80)
print("CALCULATING CHARACTERISTICS")
print("=" * 80)

results = []

# Age
age_incl = included['AGE_AT_REFERRAL'].dropna()
age_excl = excluded['AGE_AT_REFERRAL'].dropna()
results.append({
    'Characteristic': 'Age (years)',
    'Included': f"{age_incl.mean():.1f} ± {age_incl.std():.1f}",
    'Excluded': f"{age_excl.mean():.1f} ± {age_excl.std():.1f}",
    'SMD': smd_continuous(age_incl, age_excl)
})
print(f"✓ Age")

# Gender
male_incl = (included['GENDER'] == 'Male').sum()
male_excl = (excluded['GENDER'] == 'Male').sum()
male_pct_incl = 100 * male_incl / len(included)
male_pct_excl = 100 * male_excl / len(excluded)
results.append({
    'Characteristic': 'Male sex',
    'Included': f"{male_incl:,} ({male_pct_incl:.1f}%)",
    'Excluded': f"{male_excl:,} ({male_pct_excl:.1f}%)",
    'SMD': smd_binary(male_incl/len(included), male_excl/len(excluded))
})
print(f"✓ Gender")

# Treatment
for treat_code, treat_label in [('Surgery_Only', 'Surgery alone'),
                                 ('Surgery+Chemo', 'Surgery + chemotherapy'),
                                 ('Chemo_Only', 'Chemotherapy alone'),
                                 ('No_Treatment', 'No treatment')]:
    n_incl = (included['TREATMENT'] == treat_code).sum()
    n_excl = (excluded['TREATMENT'] == treat_code).sum()
    pct_incl = 100 * n_incl / len(included)
    pct_excl = 100 * n_excl / len(excluded)
    results.append({
        'Characteristic': f"Treatment: {treat_label}",
        'Included': f"{n_incl:,} ({pct_incl:.1f}%)",
        'Excluded': f"{n_excl:,} ({pct_excl:.1f}%)",
        'SMD': smd_binary(n_incl/len(included), n_excl/len(excluded))
    })
print(f"✓ Treatment")

# T-Stage
t_early_incl = included['T_STAGE'].isin(['T0', 'T1', 'T2']).sum()
t_early_excl = excluded['T_STAGE'].isin(['T0', 'T1', 'T2']).sum()
results.append({
    'Characteristic': 'T-Stage: T0–T2',
    'Included': f"{t_early_incl:,} ({100*t_early_incl/len(included):.1f}%)",
    'Excluded': f"{t_early_excl:,} ({100*t_early_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(t_early_incl/len(included), t_early_excl/len(excluded))
})

t_late_incl = included['T_STAGE'].isin(['T3', 'T4']).sum()
t_late_excl = excluded['T_STAGE'].isin(['T3', 'T4']).sum()
results.append({
    'Characteristic': 'T-Stage: T3–T4',
    'Included': f"{t_late_incl:,} ({100*t_late_incl/len(included):.1f}%)",
    'Excluded': f"{t_late_excl:,} ({100*t_late_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(t_late_incl/len(included), t_late_excl/len(excluded))
})
print(f"✓ T-Stage")

# N-Stage
n_early_incl = included['N_STAGE'].isin(['N0', 'N1']).sum()
n_early_excl = excluded['N_STAGE'].isin(['N0', 'N1']).sum()
results.append({
    'Characteristic': 'N-Stage: N0–N1',
    'Included': f"{n_early_incl:,} ({100*n_early_incl/len(included):.1f}%)",
    'Excluded': f"{n_early_excl:,} ({100*n_early_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(n_early_incl/len(included), n_early_excl/len(excluded))
})

n_late_incl = (included['N_STAGE'] == 'N2').sum()
n_late_excl = (excluded['N_STAGE'] == 'N2').sum()
results.append({
    'Characteristic': 'N-Stage: N2',
    'Included': f"{n_late_incl:,} ({100*n_late_incl/len(included):.1f}%)",
    'Excluded': f"{n_late_excl:,} ({100*n_late_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(n_late_incl/len(included), n_late_excl/len(excluded))
})
print(f"✓ N-Stage")

# M-Stage
m0_incl = (included['M_STAGE'] == 'M0').sum()
m0_excl = (excluded['M_STAGE'] == 'M0').sum()
results.append({
    'Characteristic': 'M-Stage: M0 (no distant metastases)',
    'Included': f"{m0_incl:,} ({100*m0_incl/len(included):.1f}%)",
    'Excluded': f"{m0_excl:,} ({100*m0_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(m0_incl/len(included), m0_excl/len(excluded))
})

m1_incl = (included['M_STAGE'] == 'M1').sum()
m1_excl = (excluded['M_STAGE'] == 'M1').sum()
results.append({
    'Characteristic': 'M-Stage: M1 (distant metastases)',
    'Included': f"{m1_incl:,} ({100*m1_incl/len(included):.1f}%)",
    'Excluded': f"{m1_excl:,} ({100*m1_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(m1_incl/len(included), m1_excl/len(excluded))
})
print(f"✓ M-Stage")

# Metastases count (NO lambda functions — direct filtering)
mets_incl = pd.to_numeric(included['NB_METASTASES_NUM'], errors='coerce').dropna()
mets_excl = pd.to_numeric(excluded['NB_METASTASES_NUM'], errors='coerce').dropna()

# 1 metastasis
n_met1_incl = (mets_incl == 1).sum()
n_met1_excl = (mets_excl == 1).sum()
results.append({
    'Characteristic': 'Number of liver metastases: 1',
    'Included': f"{n_met1_incl:,} ({100*n_met1_incl/len(mets_incl):.1f}%)" if len(mets_incl) > 0 else "0",
    'Excluded': f"{n_met1_excl:,} ({100*n_met1_excl/len(mets_excl):.1f}%)" if len(mets_excl) > 0 else "0",
    'SMD': smd_binary(n_met1_incl/len(mets_incl) if len(mets_incl) > 0 else 0,
                      n_met1_excl/len(mets_excl) if len(mets_excl) > 0 else 0)
})

# 2-3 metastases
n_met23_incl = ((mets_incl >= 2) & (mets_incl <= 3)).sum()
n_met23_excl = ((mets_excl >= 2) & (mets_excl <= 3)).sum()
results.append({
    'Characteristic': 'Number of liver metastases: 2–3',
    'Included': f"{n_met23_incl:,} ({100*n_met23_incl/len(mets_incl):.1f}%)" if len(mets_incl) > 0 else "0",
    'Excluded': f"{n_met23_excl:,} ({100*n_met23_excl/len(mets_excl):.1f}%)" if len(mets_excl) > 0 else "0",
    'SMD': smd_binary(n_met23_incl/len(mets_incl) if len(mets_incl) > 0 else 0,
                      n_met23_excl/len(mets_excl) if len(mets_excl) > 0 else 0)
})

# ≥4 metastases
n_met4_incl = (mets_incl >= 4).sum()
n_met4_excl = (mets_excl >= 4).sum()
results.append({
    'Characteristic': 'Number of liver metastases: ≥4',
    'Included': f"{n_met4_incl:,} ({100*n_met4_incl/len(mets_incl):.1f}%)" if len(mets_incl) > 0 else "0",
    'Excluded': f"{n_met4_excl:,} ({100*n_met4_excl/len(mets_excl):.1f}%)" if len(mets_excl) > 0 else "0",
    'SMD': smd_binary(n_met4_incl/len(mets_incl) if len(mets_incl) > 0 else 0,
                      n_met4_excl/len(mets_excl) if len(mets_excl) > 0 else 0)
})
print(f"✓ Metastases count")

# Follow-up duration
surv_incl = included['SURVIVAL_YEARS'].dropna()
surv_excl = excluded['SURVIVAL_YEARS'].dropna()
results.append({
    'Characteristic': 'Follow-up duration (years)',
    'Included': f"{surv_incl.mean():.2f} ± {surv_incl.std():.2f}",
    'Excluded': f"{surv_excl.mean():.2f} ± {surv_excl.std():.2f}",
    'SMD': smd_continuous(surv_incl, surv_excl)
})

# Deaths
deaths_incl = (included['VITAL_STATUS'] == 1).sum()
deaths_excl = (excluded['VITAL_STATUS'] == 1).sum()
results.append({
    'Characteristic': 'Deaths',
    'Included': f"{deaths_incl:,} ({100*deaths_incl/len(included):.1f}%)",
    'Excluded': f"{deaths_excl:,} ({100*deaths_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(deaths_incl/len(included), deaths_excl/len(excluded))
})

# Censored
censored_incl = (included['VITAL_STATUS'] == 0).sum()
censored_excl = (excluded['VITAL_STATUS'] == 0).sum()
results.append({
    'Characteristic': 'Censored/Alive',
    'Included': f"{censored_incl:,} ({100*censored_incl/len(included):.1f}%)",
    'Excluded': f"{censored_excl:,} ({100*censored_excl/len(excluded):.1f}%)",
    'SMD': smd_binary(censored_incl/len(included), censored_excl/len(excluded))
})
print(f"✓ Follow-up/outcomes")

# Create table
print("\n" + "=" * 80)
print("SUPPLEMENTARY TABLE S1")
print("=" * 80)
table_df = pd.DataFrame(results)
print("\n" + table_df.to_string(index=False))

# Summary statistics
print("\n" + "=" * 80)
print("SMD SUMMARY")
print("=" * 80)
smd_vals = table_df['SMD'].values
print(f"\nMaximum SMD: {smd_vals.max():.3f}")
print(f"Median SMD: {np.median(smd_vals):.3f}")

large_imb = table_df[table_df['SMD'] >= 0.20].sort_values('SMD', ascending=False)
if len(large_imb) > 0:
    print(f"\nVariables with SMD ≥ 0.20 (meaningful difference):")
    for _, row in large_imb.iterrows():
        print(f"  • {row['Characteristic']}: {row['SMD']:.3f}")
else:
    print(f"\nNo variables with SMD ≥ 0.20")

# Save
print("\n" + "=" * 80)
print("SAVING OUTPUTS")
print("=" * 80)
try:
    table_df.to_csv('Supplementary_Table_S1.csv', index=False)
    print("✓ Saved: Supplementary_Table_S1.csv")
except:
    table_df.to_csv('/home/user/LiverMets/outputs/Supplementary_Table_S1.csv', index=False)
    print("✓ Saved: /home/user/LiverMets/outputs/Supplementary_Table_S1.csv")

try:
    table_df.to_excel('Supplementary_Table_S1.xlsx', index=False)
    print("✓ Saved: Supplementary_Table_S1.xlsx")
except:
    try:
        table_df.to_excel('/home/user/LiverMets/outputs/Supplementary_Table_S1.xlsx', index=False)
        print("✓ Saved: /home/user/LiverMets/outputs/Supplementary_Table_S1.xlsx")
    except:
        print("⚠ Could not save XLSX (openpyxl not available)")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
