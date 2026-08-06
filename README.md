# LiverMets: Interpretable Machine Learning for Colorectal Liver Metastases

Research code supporting my PhD work in **AI for Healthcare**, focusing on interpretable machine learning, survival analysis and explainable AI for patients with colorectal liver metastases (CRLM).

## 🔬 Research Overview

This project investigates whether clinically interpretable machine learning approaches can support risk stratification and outcome analysis in colorectal liver metastases.

The work combines traditional survival analysis with machine learning and explainability techniques to identify clinically meaningful patient subgroups and prognostic factors.

## 🧠 Methods

The analytical workflow includes:

- Cohort preparation and data quality assessment
- Decision-tree-based patient stratification
- Kaplan–Meier survival estimation
- Log-rank testing
- Multivariable Cox proportional hazards modelling
- Proportional hazards assumption assessment
- Propensity score matching
- Treatment-effect analysis
- Temporal validation
- Explainable AI (XAI)
- SHAP-based model interpretation

## 📂 Repository Structure

```text
LiverMets/
├── notebooks/
│   ├── 01_cohort_preparation.ipynb
│   ├── 02_cart_phenotyping.ipynb
│   ├── 03_survival_analysis.ipynb
│   ├── 04_multivariable_cox.ipynb
│   ├── 05_treatment_analysis.ipynb
│   └── 06_temporal_validation.ipynb
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── analysis.py
│   └── visualization.py
├── scripts/
├── figures/
├── requirements.txt
├── .gitignore
└── README.md