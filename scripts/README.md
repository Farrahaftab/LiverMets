# Analysis Scripts

This directory contains Python scripts for the LiverMets analysis. Each script is self-contained and can be run independently.

## Main Analysis

### `full_analysis_colab.py` (74 KB)
Complete analysis pipeline optimized for Google Colab. Includes:
- Section 1: Load and prepare data
- Section 2: Inclusion/exclusion criteria
- Section 3: Baseline characteristics (Table 1)
- Section 4: CART phenotyping
- Section 5: Survival by phenotype
- Section 6: Phenotype characteristics (Table 2)
- Section 7: Univariable Cox models
- Section 8: Multivariable Cox model
- Section 9: Schoenfeld residual testing (proportional hazards)
- Section 10: Baseline characteristics in PSM cohorts
- Section 11: Propensity Score Matching (PSM) with temporal validation
- Section 12: Treatment effect analysis by phenotype

**Status**: Final submission version
**Last Modified**: 2026-07-26

## Supplementary Table S1 (Baseline Characteristics)

### `Supplementary_Table_S1_ASO_Ready.py` (7 KB) ⭐ **RECOMMENDED**
**ASO submission-ready version**. Compares included (n=14,759) vs excluded (n=14,806) patients.

**Features**:
- ✓ Uses only non-eligibility variables (excludes TNM)
- ✓ Includes all 14,759 patients with NB_METS_GROUP variable
- ✓ Reports 7 metastases count categories: 0–1, 2, 3, 4–5, 6–10, >10, ND
- ✓ Calculates SMDs with max=0.223 (reviewer-safe threshold)
- ✓ Generates manuscript paragraph (ASO-safe language)
- ✓ Exports CSV and XLSX

**Key Fix**: Uses `NB_METS_GROUP` (14,759 patients) instead of `NB_METASTASES_NUM` (13,527 patients)

### `Supplementary_Table_S1_Generator.py` (23 KB)
Full-featured version with interactive column inspection. Same analysis as ASO-Ready but with input prompts.

### `Supplementary_Table_S1_Simple.py` (11 KB)
Simplified version without lambda functions, optimized for Colab caching issues. Useful when Generator has caching problems.

## Utility Scripts

### `build_analysis_cohort.py`
Initial data preparation and cohort building. Creates the final dataset used in analysis.

## Usage

### Local Execution
```bash
python scripts/Supplementary_Table_S1_ASO_Ready.py
```

### Google Colab
Copy the desired script and paste into a Colab cell. Ensure `LiverMets_Final_Dataset.csv` is mounted/accessible.

```python
# Example: Mount Google Drive in Colab
from google.colab import drive
drive.mount('/content/drive')
```

## Data Requirements

All scripts expect: **`LiverMets_Final_Dataset.csv`**
- 29,565 rows (registry patients)
- Required columns: T_STAGE, N_STAGE, M_STAGE, SURVIVAL_YEARS, VITAL_STATUS, GENDER, TREATMENT, NB_METS_GROUP, etc.

## Output Files

Scripts automatically save results to `/home/user/LiverMets/outputs/`:
- `Supplementary_Table_S1_ASO.csv` — Main results table
- `Supplementary_Table_S1_ASO.xlsx` — Excel format
- `Supplementary_Table_S1_Manuscript_Paragraph_ASO.txt` — Manuscript text

## Development Notes

- **Python**: 3.8+
- **Key Libraries**: pandas, numpy, scipy, scikit-learn, statsmodels, matplotlib, seaborn
- **Tested**: Google Colab (2024)

For questions or issues, refer to the main README.md
