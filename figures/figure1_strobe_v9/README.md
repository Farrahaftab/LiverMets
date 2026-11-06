# Figure 1 (STROBE flow, Paper 1): reproducible generator

`make_figure1_strobe.py` draws the Paper 1 patient-flow figure. Every displayed number is read from the locked v8 output files. Nothing is typed in by hand. The script also writes a verification report that names the source file and field for each displayed statistic.

## What it reads (repository-relative)

| File | Used for |
|---|---|
| `results/final_v7/F30_flow_counts_for_figure1.csv` | Step counts and exclusions (differences between steps) |
| `results/final_v7/F01_flow_by_day_convention.csv` | Independent check of the step counts |
| `results/final_v7/F31_table1_baseline_characteristics.csv` | Development and validation n, events in window, recorded deaths, follow-up |
| `results/final_v7/F32_supp_S1_included_vs_excluded.csv` | Independent check of the analytic and excluded counts |
| `results/final_v7/F00_headline.csv` | Cut-points 0.3793 and 0.4756 |
| `results/final_v7/F02b_selected_model_performance.csv` | C-index, O/E, observed and predicted 5-y survival, IBS |
| `results/final_v7/F02_M_stage_candidates_identical_patients.csv` | Cross-check of the C-index CI |
| `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | Group sizes, deaths, median OS, 5-y KM |
| `results/final_v7/F07_phenotype_definitions.csv` | Group definitions (cut-point text check) |
| `results/final_v7/F08_phenotype_separation.csv` | Log-rank p-values and ordinal C-index |
| `results/final_v7/F12_death_and_last_contact_verification.csv` | Deaths recorded, deaths beyond 15 years |
| `results/final_v7/F17_RFS_sensitivity_final.csv` | Median RFS (primary row) |
| `results/final_v7/feasibility/G01_horizon_feasibility_validation.csv` | 5-y evaluable %, observed, predicted, O/E |
| `results/final_v9/paper1/P1_model_coefficients.csv` | Number of M2a terms |
| `results/final_v9/paper1/P1_baseline_survival_by_stratum.csv` | Number of strata |

## What it writes (`results/final_v9/figure1/`)

* `Figure1_STROBE_Cox.png` (600 dpi raster)
* `Figure1_STROBE_Cox.pdf` (vector, editable text, TrueType fonts)
* `Figure1_STROBE_Cox.svg` (vector)
* `Figure1_caption.md` (manuscript caption, generated from the same values)
* `verification_report.csv` and `verification_report.md` (every displayed statistic with its source file and field, and every automated check)

## Checks and what happens when one fails

* **FAIL** (for example, step counts that do not agree between files, or group sizes that do not sum to the cohort): the report is written, the figure is **not** drawn, and the script exits with status 1.
* **DISCREPANCY** (two locked outputs disagree): the report records both values, the script prints a warning, and the figure is drawn with the value from the file named in the figure logic. The discrepancy is **not** corrected silently.

The current run passes 27 checks and reports 1 discrepancy: the validation C-index 95% CI upper bound is 0.637 in `F02` and 0.636 in `F02b`. The figure shows the `F02b` value, and the caption refers to the discrepancy. The Results text uses 0.637. The team must decide which value is correct. The locked outputs have not been changed.

## Run locally

```bash
python figures/figure1_strobe_v9/make_figure1_strobe.py
```

Requires Python 3.9 or later and matplotlib. No other packages are needed. See `COLAB.md` for a Google Colab run.

## Relation to the earlier v7 script

`notebooks/figure1_flow_v7.py` and `figures/generate_publication_outputs.py` predate this generator. The v7 script contains typed-in values (for example, the death counts 4,675 and 1,916 and the v7 title), so it is not used for Paper 1. It has not been modified.

## Scope

This generator does not fit or refit any model. It does not include the superseded CART results or the treatment-comparison analyses.
