# LiverMets: TNM-Based Prognostic Phenotyping of Colorectal Liver Metastases

A comprehensive analysis of colorectal cancer patients with liver metastases using the LiverMetSurvey registry, focusing on TNM-based prognostic phenotyping and treatment outcomes.

## Project Overview

This repository contains reproducible analysis code for a manuscript submitted to *Annals of Surgical Oncology*. The analysis includes:

- **Cohort preparation**: Inclusion/exclusion criteria, data completeness assessment
- **CART phenotyping**: Classification and Regression Tree analysis for TNM-based phenotyping
- **Survival analysis**: Kaplan-Meier curves and log-rank tests by phenotype
- **Multivariable Cox regression**: Risk stratification with Schoenfeld residual testing
- **Propensity score matching**: Treatment effect estimation with temporal validation
- **Temporal validation**: Training (≤2009) and validation (>2009) cohorts

## Repository Structure

```
LiverMets/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── LICENSE                      # License information
├── .gitignore                   # Git ignore rules
│
├── notebooks/                   # Jupyter notebooks for analysis
│   ├── 01_cohort_preparation.ipynb
│   ├── 02_cart_phenotyping.ipynb
│   ├── 03_survival_analysis.ipynb
│   ├── 04_multivariable_cox.ipynb
│   ├── 05_treatment_analysis.ipynb
│   └── 06_temporal_validation.ipynb
│
├── src/                         # Python modules and utilities
│   ├── __init__.py
│   ├── data.py                  # Data loading and preprocessing
│   ├── analysis.py              # Analysis functions
│   └── visualization.py         # Plotting utilities
│
└── outputs/                     # Generated results and figures
    ├── figures/                 # Publication figures
    ├── tables/                  # Supplementary tables (CSV, XLSX)
    └── logs/                    # Analysis logs
```

## Installation

### Prerequisites
- Python 3.8+
- Jupyter Lab or Jupyter Notebook

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/farrahaftab/livermets.git
   cd livermets
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch Jupyter:
   ```bash
   jupyter lab
   ```

## Key Files

### Analysis Scripts
- **`scripts/Supplementary_Table_S1_ASO_Ready.py`**: Generates Table S1 (baseline characteristics comparison)
- **`scripts/full_analysis_colab.py`**: Complete analysis pipeline (optimized for Google Colab)

### Data Requirements
- `LiverMets_Final_Dataset.csv`: De-identified registry data (not included in repository)

## Analysis Overview

### 1. Cohort Preparation
- Registry: 29,565 colorectal cancer patients with liver metastases
- Inclusion: Complete TNM staging + survival data
- **Included**: 14,759 patients (49.9%)
- **Excluded**: 14,806 patients (50.1%) — missing TNM (n=10,100) or survival (n=4,706)

### 2. CART Phenotyping
Binary classification tree based on TNM components produces:
- **Phenotype 1 (Favourable)**: M0, N0–N1 → 4,913 patients
- **Phenotype 2 (Intermediate)**: M0, N2 or M1, N0–N1 → 4,323 patients  
- **Phenotype 3 (Adverse)**: M1, N2 → 5,523 patients

### 3. Statistical Methods
- **Survival**: Kaplan-Meier estimator, log-rank test
- **Cox regression**: Multivariable model with Schoenfeld residual testing for proportional hazards
- **PSM**: One-to-one matching with caliper 0.05 (propensity score scale)
- **Treatment effect**: Interaction between phenotype and treatment modality
- **Temporal validation**: Internal validation in >2009 cohort

## Reproducibility

### ASO Submission Requirements
Table S1 (Supplementary Table S1) uses only **non-eligibility variables**:
- ✓ Age, Sex, Treatment, Metastases count, Follow-up, Mortality
- ✗ Excludes TNM (inherently part of inclusion criteria)

All metastases counts account for the complete cohort (14,759) using `NB_METS_GROUP`:
- Categories: 0–1, 2, 3, 4–5, 6–10, >10, Not determined (ND, n=878)
- Standardised Mean Differences (SMD) ≥0.20 indicate meaningful baseline imbalance

### Citation of Results
If using results or code from this analysis, please cite:

```
[Author names]. [Manuscript title]. *Annals of Surgical Oncology*. [Year]. 
```

## License

This project is licensed under [LICENSE] — see LICENSE file for details.

## Contact

For questions or feedback:
- **Email**: farrahaftab19@gmail.com
- **GitHub**: [farrahaftab](https://github.com/farrahaftab)

## Acknowledgments

This analysis uses data from the LiverMetSurvey registry. We acknowledge all participating centers and patients.

---

**Last Updated**: 2026-08-06
**Status**: Manuscript submitted to ASO
