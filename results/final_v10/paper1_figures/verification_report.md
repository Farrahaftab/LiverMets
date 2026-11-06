# Paper 1 figure set: verification report (v11)

Automated checks: 91 run; 89 passed; 2 discrepancy(ies) reported; 0 failed.

## Discrepancies between locked outputs (reported, not corrected)

- [common] Validation C-index 95% CI: F02 (candidate table, M2a row) equals F02b (selected model): expected 0.608-0.637, observed 0.608-0.636
- [FigureS3] M2a validation C-index 95% CI: F02 candidate table equals F02b selected model: expected 0.608-0.637, observed 0.608-0.636

## Failed checks (figure not drawn)

None.

## Every displayed value and its source

| Figure | ID | Label | Displayed | Source file | Field | Raw |
|---|---|---|---|---|---|---|
| common | C_ci_F02 | C-index 95% CI, M2a row of candidate table (Supplementary S4) | 0.608–0.637 | `results/final_v7/F02_M_stage_candidates_identical_patients.csv` | valid_C_95CI, row M2a | 0.608-0.637 |
| common | N_registry | Registry records | 29,565 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '1 registry' | 29565 |
| common | N_analytic | Analytic cohort | 17,262 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '8 complete TNM' | 17262 |
| common | N_dev | Development n | 8,463 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Patients / Development | 8463 |
| common | N_val | Validation n | 8,799 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Patients / Validation | 8799 |
| common | EV_dev | Development events in window | 4,675 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Deaths inside the 15-year window / Development | 4675 |
| common | EV_val | Validation events in window | 1,916 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Deaths inside the 15-year window / Validation | 1916 |
| common | CUT_lo | Cut-point, lower tertile | 0.3793 | `results/final_v7/F00_headline.csv` | phenotype_cut_S5_q33 | 0.3793 |
| common | CUT_hi | Cut-point, upper tertile | 0.4756 | `results/final_v7/F00_headline.csv` | phenotype_cut_S5_q67 | 0.4756 |
| common | C_val | Validation C-index | 0.622 | `results/final_v7/F02b_selected_model_performance.csv` | valid_C | 0.6216 |
| common | C_ci | Validation C-index 95% CI (F02b, selected model) | 0.608–0.636 | `results/final_v7/F02b_selected_model_performance.csv` | valid_C_95CI | 0.608-0.636 |
| common | OE5 | Observed/expected 5-y | 1.14 | `results/final_v7/F02b_selected_model_performance.csv` | valid_OE_5y | 1.142 |
| common | OBS5 | Observed 5-y survival (KM) | 46.6% | `results/final_v7/F02b_selected_model_performance.csv` | valid_observed_S5 | 0.466 |
| common | PRED5 | Predicted 5-y survival (mean) | 40.8% | `results/final_v7/F02b_selected_model_performance.csv` | valid_mean_predicted_S5 | 0.408 |
| common | P_val | Log-rank p, validation | 2.0 × 10⁻⁵² | `results/final_v7/F08_phenotype_separation.csv` | valid_logrank_p | 1.960688139201623e-52 |
| common | P_dev | Log-rank p, development | 1.4 × 10⁻⁷⁷ | `results/final_v7/F08_phenotype_separation.csv` | train_logrank_p | 1.3516744662754814e-77 |
| common | RFS_med | Median RFS, years (primary) | 2.03 | `results/final_v7/F17_RFS_sensitivity_final.csv` | median_RFS (PRIMARY row) | 2.03 |
| common | EVAL5 | Validation evaluable at 5 years | 26% | `results/final_v7/feasibility/G01_horizon_feasibility_validation.csv` | pct_evaluable, horizon 5 | 26.0 |
| common | FU_dev | Median follow-up, development (years) | 5.89 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Median follow-up / Development | 5.89 |
| common | FU_val | Median follow-up, validation (years) | 1.47 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Median follow-up / Validation | 1.47 |
| common | N_terms | M2a terms | 11 | `results/final_v9/paper1/P1_model_coefficients.csv` | number of rows | 11 |
| common | N_strata | M2a strata | 8 | `results/final_v9/paper1/P1_baseline_survival_by_stratum.csv` | number of rows | 8 |
| Figure1 | N_registry | Step count: LiverMetSurvey registry | 29,565 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '1 registry' | 29565 |
| Figure1 | N_eligible | Step count: Recorded as eligible (CINCLUSION = Yes) | 28,979 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '2 CINCLUSION=Yes' | 28979 |
| Figure1 | X_eligible | Excluded: not recorded as eligible | 586 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '2 CINCLUSION=Yes' | 586 |
| Figure1 | N_hepatectomy | Step count: Hepatectomy recorded | 26,677 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '3 hepatectomy' | 26677 |
| Figure1 | X_hepatectomy | Excluded: no hepatectomy recorded | 2,302 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '3 hepatectomy' | 2302 |
| Figure1 | N_opdate | Step count: Operation date recorded (year and month) | 26,592 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '4 operation date (year+month)' | 26592 |
| Figure1 | X_opdate | Excluded: no operation date | 85 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '4 operation date (year+month)' | 85 |
| Figure1 | N_status | Step count: Vital status and last-news date recorded | 26,271 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '5 status and last-news' | 26271 |
| Figure1 | X_status | Excluded: missing status or last-news | 321 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '5 status and last-news' | 321 |
| Figure1 | N_chronology | Step count: Chronology consistent | 26,186 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '6 chronology' | 26186 |
| Figure1 | X_chronology | Excluded: inconsistent dates | 85 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '6 chronology' | 85 |
| Figure1 | N_followup | Step count: Positive follow-up or death | 26,094 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '7 positive follow-up or death' | 26094 |
| Figure1 | X_followup | Excluded: no follow-up and not dead | 92 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '7 positive follow-up or death' | 92 |
| Figure1 | N_analytic | Step count: Complete TNM staging: analytic cohort | 17,262 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n, step '8 complete TNM (analytic cohort)' | 17262 |
| Figure1 | X_analytic | Excluded: incomplete TNM staging | 8,832 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference of consecutive steps into '8 complete TNM (analytic cohort)' | 8832 |
| Figure1 | P_incomplete | Percent excluded for incomplete TNM | 33.8% | `results/final_v7/F30_flow_counts_for_figure1.csv` | computed: excluded / step 7 | 33.847 |
| Figure1 | G_FAV | Favourable group counts and outcomes | dev n 2,821; val n 2,662 (383); median 7.38; 5-y 62.9% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable': train_n, valid_n, valid_deaths, valid_median_OS, valid_S5_KM | Favourable |
| Figure1 | G_INT | Intermediate group counts and outcomes | dev n 2,821; val n 2,824 (598); median 4.44; 5-y 45.4% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate': train_n, valid_n, valid_deaths, valid_median_OS, valid_S5_KM | Intermediate |
| Figure1 | G_ADV | Adverse group counts and outcomes | dev n 2,821; val n 3,313 (935); median 3.18; 5-y 34.3% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse': train_n, valid_n, valid_deaths, valid_median_OS, valid_S5_KM | Adverse |
| Figure2 | P_dev_fig | Log-rank p shown, development | 1.4 × 10⁻⁷⁷ | `results/final_v7/F08_phenotype_separation.csv` | train_logrank_p | 1.3516744662754814e-77 |
| Figure2 | P_val_fig | Log-rank p shown, validation | 2.0 × 10⁻⁵² | `results/final_v7/F08_phenotype_separation.csv` | valid_logrank_p | 1.960688139201623e-52 |
| Figure2 | KMDEV_FAV | Favourable 5-y KM, development | 54.1% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | train_S5_KM | 0.541 |
| Figure2 | KMVAL_FAV | Favourable 5-y KM, validation | 62.9% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | valid_S5_KM | 0.629 |
| Figure2 | KMDEV_INT | Intermediate 5-y KM, development | 41.9% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | train_S5_KM | 0.419 |
| Figure2 | KMVAL_INT | Intermediate 5-y KM, validation | 45.4% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | valid_S5_KM | 0.454 |
| Figure2 | KMDEV_ADV | Adverse 5-y KM, development | 30.7% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | train_S5_KM | 0.307 |
| Figure2 | KMVAL_ADV | Adverse 5-y KM, validation | 34.3% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | valid_S5_KM | 0.343 |
| Figure3 | DEC10 | Decile 10 observed and predicted 5-y survival | 75.8% vs 58.0% | `results/final_v7/F20_calibration_by_validation_decile.csv` | observed_5y_KM; mean_predicted_5y (validation_decile = 10) | 0.758 |
| Figure3 | OE_0 | O/E, operation 1990-2004 | 0.96 | `results/final_v7/F21_calibration_by_operation_period.csv` | O_over_E | 0.955 |
| Figure3 | OE_1 | O/E, operation 2005-2009 (training) | 1.03 | `results/final_v7/F21_calibration_by_operation_period.csv` | O_over_E | 1.025 |
| Figure3 | OE_2 | O/E, operation 2010-2012 (validation) | 1.09 | `results/final_v7/F21_calibration_by_operation_period.csv` | O_over_E | 1.088 |
| Figure3 | OE_3 | O/E, operation 2013-2015 (validation) | 1.23 | `results/final_v7/F21_calibration_by_operation_period.csv` | O_over_E | 1.234 |
| FigureS1 | RFSN_FAV | Favourable RFS n (validation) | 2,590 | `results/final_v9/paper1/F81_numbers_at_risk_by_group.csv` | n, scenario RFS_validation, group Favourable | 2590 |
| FigureS1 | RFSN_INT | Intermediate RFS n (validation) | 2,738 | `results/final_v9/paper1/F81_numbers_at_risk_by_group.csv` | n, scenario RFS_validation, group Intermediate | 2738 |
| FigureS1 | RFSN_ADV | Adverse RFS n (validation) | 3,172 | `results/final_v9/paper1/F81_numbers_at_risk_by_group.csv` | n, scenario RFS_validation, group Adverse | 3172 |
| FigureS1 | RFS_CI_fig | Overall median RFS shown on figure | 2.03 (1.98–2.09) | `results/final_v7/F17_RFS_sensitivity_final.csv` | median_RFS; median_95CI (PRIMARY row) | 2.03 |
| FigureS2 | HR_T3 | HR, T3 vs T1-2 | 1.124 (0.908–1.393); p 0.283 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row T3) | 1.124 |
| FigureS2 | HR_T4 | HR, T4 vs T1-2 | 1.364 (1.093–1.701); p 0.006 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row T4) | 1.364 |
| FigureS2 | HR_N1 | HR, N1 vs N0 | 1.282 (1.195–1.376); p <0.001 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row N1) | 1.282 |
| FigureS2 | HR_N2 | HR, N2 vs N0 | 1.625 (1.505–1.755); p <0.001 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row N2) | 1.625 |
| FigureS2 | HR_AGE10_F | HR, Age, per 10 years | 1.131 (1.098–1.166); p <0.001 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row AGE10_F) | 1.131 |
| FigureS2 | HR_DFI12_F | HR, Interval primary to liver metastasis, per 12 months (0 if synchronous) | 0.982 (0.939–1.027); p 0.420 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row DFI12_F) | 0.982 |
| FigureS2 | HR_METS_F | HR, Number of liver metastases, per additional lesion | 1.064 (1.054–1.075); p <0.001 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row METS_F) | 1.064 |
| FigureS2 | HR_SIZE10_F | HR, Largest metastasis, per 10 mm | 1.032 (1.022–1.042); p <0.001 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row SIZE10_F) | 1.032 |
| FigureS2 | HR_DFI_NR | HR, Interval unavailable (indicator) | 0.932 (0.827–1.050); p 0.245 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row DFI_NR) | 0.932 |
| FigureS2 | HR_METS_NR | HR, Metastasis count unavailable (indicator) | 1.213 (1.079–1.363); p 0.001 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row METS_NR) | 1.213 |
| FigureS2 | HR_SIZE_NR | HR, Metastasis size unavailable (indicator) | 0.984 (0.904–1.070); p 0.703 | `results/final_v9/paper1/P1_model_coefficients.csv` | HR, HR_CI_low, HR_CI_high, p (row SIZE_NR) | 0.984 |
| FigureS3 | CAND_M1 | Validation C-index, M1 (candidate table) | 0.622 (0.606–0.636) | `results/final_v7/F02_M_stage_candidates_identical_patients.csv` | valid_C; valid_C_95CI, row M1 | 0.6218 |
| FigureS3 | CAND_M2a | Validation C-index, M2a (candidate table) | 0.622 (0.608–0.637) | `results/final_v7/F02_M_stage_candidates_identical_patients.csv` | valid_C; valid_C_95CI, row M2a | 0.6216 |
| FigureS3 | CAND_M2b | Validation C-index, M2b (candidate table) | 0.622 (0.609–0.637) | `results/final_v7/F02_M_stage_candidates_identical_patients.csv` | valid_C; valid_C_95CI, row M2b | 0.6219 |
| FigureS3 | BENCH_SEL_0 | Selected model C, Fong CRS subset (CEA recorded) | 0.639 | `results/final_v7/F16_identical_subset_comparison_calibration.csv` | selected_model_C | 0.6394 |
| FigureS3 | BENCH_FONG_0 | Fong score C, same patients | 0.591 | `results/final_v7/F16_identical_subset_comparison_calibration.csv` | Fong_CRS_C | 0.5912 |
| FigureS3 | BENCH_SEL_1 | Selected model C, Nordlinger-type subset | 0.630 | `results/final_v7/F16_identical_subset_comparison_calibration.csv` | selected_model_C | 0.6303 |
| FigureS3 | BENCH_NORD_1 | Nordlinger-type score C, same patients | 0.583 | `results/final_v7/F16_identical_subset_comparison_calibration.csv` | Nordlinger_C | 0.583 |

## All automated checks

| Figure | Check | Expected | Observed | Status |
|---|---|---|---|---|
| common | F01 mid-month equals F30 at '1 registry' | 29565 | 29565 | **PASS** |
| common | F01 mid-month equals F30 at '2 CINCLUSION=Yes' | 28979 | 28979 | **PASS** |
| common | F01 mid-month equals F30 at '3 hepatectomy' | 26677 | 26677 | **PASS** |
| common | F01 mid-month equals F30 at '4 operation date (year+month)' | 26592 | 26592 | **PASS** |
| common | F01 mid-month equals F30 at '5 status and last-news' | 26271 | 26271 | **PASS** |
| common | F01 mid-month equals F30 at '6 chronology' | 26186 | 26186 | **PASS** |
| common | F01 mid-month equals F30 at '7 positive follow-up or death' | 26094 | 26094 | **PASS** |
| common | Excluded n: F30 difference equals F32 'Excluded' n | 8832 | 8832 | **PASS** |
| common | Analytic n: F30 equals F32 'Analytic cohort' n | 17262 | 17262 | **PASS** |
| common | Development + validation equals analytic cohort | 17262 | 17262 | **PASS** |
| common | Window events (dev + val) equal F12 | 6591 | 6591 | **PASS** |
| common | Recorded minus window events equal F12 deaths beyond 15 years | 10 | 10 | **PASS** |
| common | Group development n sum equals development cohort | 8463 | 8463 | **PASS** |
| common | Group validation n sum equals validation cohort | 8799 | 8799 | **PASS** |
| common | Group validation deaths sum equals validation window events | 1916 | 1916 | **PASS** |
| common | Validation C-index 95% CI: F02 (candidate table, M2a row) equals F02b (selected model) | 0.608-0.637 | 0.608-0.636 | **DISCREPANCY** |
| common | Validation 5-y observed survival: F02b equals G01 | 0.466 | 0.466 | **PASS** |
| common | Validation 5-y predicted survival: F02b equals G01 | 0.408 | 0.408 | **PASS** |
| common | Validation 5-y O/E: F02b equals G01 | 1.142 | 1.142 | **PASS** |
| common | M2a strata count equals 2 x 2 x 2 | 8 | 8 | **PASS** |
| Figure2 | development Favourable: at-risk at t=0 equals group n | 2821 | 2821 | **PASS** |
| Figure2 | development Favourable: group n (F81) equals F06 | 2821 | 2821 | **PASS** |
| Figure2 | development Favourable: KM 5-y survival (curve) equals F06 | 0.541 | 0.541045 | **PASS** |
| Figure2 | development Favourable: KM median (curve) equals F06 | 5.5 | 5.4976 | **PASS** |
| Figure2 | development Intermediate: at-risk at t=0 equals group n | 2821 | 2821 | **PASS** |
| Figure2 | development Intermediate: group n (F81) equals F06 | 2821 | 2821 | **PASS** |
| Figure2 | development Intermediate: KM 5-y survival (curve) equals F06 | 0.419 | 0.419261 | **PASS** |
| Figure2 | development Intermediate: KM median (curve) equals F06 | 3.89 | 3.885 | **PASS** |
| Figure2 | development Adverse: at-risk at t=0 equals group n | 2821 | 2821 | **PASS** |
| Figure2 | development Adverse: group n (F81) equals F06 | 2821 | 2821 | **PASS** |
| Figure2 | development Adverse: KM 5-y survival (curve) equals F06 | 0.307 | 0.306703 | **PASS** |
| Figure2 | development Adverse: KM median (curve) equals F06 | 2.97 | 2.9678 | **PASS** |
| Figure2 | validation Favourable: at-risk at t=0 equals group n | 2662 | 2662 | **PASS** |
| Figure2 | validation Favourable: group n (F81) equals F06 | 2662 | 2662 | **PASS** |
| Figure2 | validation Favourable: KM 5-y survival (curve) equals F06 | 0.629 | 0.628974 | **PASS** |
| Figure2 | validation Favourable: KM median (curve) equals F06 | 7.38 | 7.3785 | **PASS** |
| Figure2 | validation Intermediate: at-risk at t=0 equals group n | 2824 | 2824 | **PASS** |
| Figure2 | validation Intermediate: group n (F81) equals F06 | 2824 | 2824 | **PASS** |
| Figure2 | validation Intermediate: KM 5-y survival (curve) equals F06 | 0.454 | 0.45403 | **PASS** |
| Figure2 | validation Intermediate: KM median (curve) equals F06 | 4.44 | 4.4353 | **PASS** |
| Figure2 | validation Adverse: at-risk at t=0 equals group n | 3313 | 3313 | **PASS** |
| Figure2 | validation Adverse: group n (F81) equals F06 | 3313 | 3313 | **PASS** |
| Figure2 | validation Adverse: KM 5-y survival (curve) equals F06 | 0.343 | 0.342834 | **PASS** |
| Figure2 | validation Adverse: KM median (curve) equals F06 | 3.18 | 3.1841 | **PASS** |
| Figure3 | Decile sizes sum to validation n | 8799 | 8799 | **PASS** |
| Figure3 | Decile deaths sum to validation window events | 1916 | 1916 | **PASS** |
| Figure3 | decile 1: observed minus predicted equals F20 | 0.032 | 0.031 | **PASS** |
| Figure3 | decile 2: observed minus predicted equals F20 | 0.053 | 0.054 | **PASS** |
| Figure3 | decile 3: observed minus predicted equals F20 | 0.035 | 0.035 | **PASS** |
| Figure3 | decile 4: observed minus predicted equals F20 | 0.074 | 0.074 | **PASS** |
| Figure3 | decile 5: observed minus predicted equals F20 | -0.016 | -0.016 | **PASS** |
| Figure3 | decile 6: observed minus predicted equals F20 | 0.021 | 0.021 | **PASS** |
| Figure3 | decile 7: observed minus predicted equals F20 | 0.067 | 0.067 | **PASS** |
| Figure3 | decile 8: observed minus predicted equals F20 | 0.071 | 0.071 | **PASS** |
| Figure3 | decile 9: observed minus predicted equals F20 | 0.025 | 0.025 | **PASS** |
| Figure3 | decile 10: observed minus predicted equals F20 | 0.178 | 0.178 | **PASS** |
| Figure3 | Operation periods with O/E equal periods with 5-year follow-up present in F21 | 4 | 4 | **PASS** |
| Figure3 | operation 1990-2004: O/E equals observed divided by predicted (F21), within rounding | 0.955 | 0.956 | **PASS** |
| Figure3 | operation 2005-2009 (training): O/E equals observed divided by predicted (F21), within rounding | 1.025 | 1.026 | **PASS** |
| Figure3 | operation 2010-2012 (validation): O/E equals observed divided by predicted (F21), within rounding | 1.088 | 1.088 | **PASS** |
| Figure3 | operation 2013-2015 (validation): O/E equals observed divided by predicted (F21), within rounding | 1.234 | 1.232 | **PASS** |
| FigureS1 | RFS validation n (sum over groups) does not exceed validation cohort n | True | True | **PASS** |
| FigureS1 | Favourable: at-risk at t=0 equals group n | 2590 | 2590 | **PASS** |
| FigureS1 | Intermediate: at-risk at t=0 equals group n | 2738 | 2738 | **PASS** |
| FigureS1 | Adverse: at-risk at t=0 equals group n | 3172 | 3172 | **PASS** |
| FigureS2 | Forest plot rows equal M2a terms | 11 | 11 | **PASS** |
| FigureS2 | T3: HR equals exp(coefficient) (P1 table) | 1.124 | 1.124 | **PASS** |
| FigureS2 | T3: CI brackets HR | True | True | **PASS** |
| FigureS2 | T4: HR equals exp(coefficient) (P1 table) | 1.364 | 1.364 | **PASS** |
| FigureS2 | T4: CI brackets HR | True | True | **PASS** |
| FigureS2 | N1: HR equals exp(coefficient) (P1 table) | 1.282 | 1.282 | **PASS** |
| FigureS2 | N1: CI brackets HR | True | True | **PASS** |
| FigureS2 | N2: HR equals exp(coefficient) (P1 table) | 1.625 | 1.625 | **PASS** |
| FigureS2 | N2: CI brackets HR | True | True | **PASS** |
| FigureS2 | AGE10_F: HR equals exp(coefficient) (P1 table) | 1.131 | 1.131 | **PASS** |
| FigureS2 | AGE10_F: CI brackets HR | True | True | **PASS** |
| FigureS2 | DFI12_F: HR equals exp(coefficient) (P1 table) | 0.982 | 0.982 | **PASS** |
| FigureS2 | DFI12_F: CI brackets HR | True | True | **PASS** |
| FigureS2 | METS_F: HR equals exp(coefficient) (P1 table) | 1.064 | 1.064 | **PASS** |
| FigureS2 | METS_F: CI brackets HR | True | True | **PASS** |
| FigureS2 | SIZE10_F: HR equals exp(coefficient) (P1 table) | 1.032 | 1.032 | **PASS** |
| FigureS2 | SIZE10_F: CI brackets HR | True | True | **PASS** |
| FigureS2 | DFI_NR: HR equals exp(coefficient) (P1 table) | 0.932 | 0.932 | **PASS** |
| FigureS2 | DFI_NR: CI brackets HR | True | True | **PASS** |
| FigureS2 | METS_NR: HR equals exp(coefficient) (P1 table) | 1.213 | 1.213 | **PASS** |
| FigureS2 | METS_NR: CI brackets HR | True | True | **PASS** |
| FigureS2 | SIZE_NR: HR equals exp(coefficient) (P1 table) | 0.984 | 0.984 | **PASS** |
| FigureS2 | SIZE_NR: CI brackets HR | True | True | **PASS** |
| FigureS3 | M2a validation C in candidate table (F02) equals F02b | 0.6216 | 0.6216 | **PASS** |
| FigureS3 | M2a validation C-index 95% CI: F02 candidate table equals F02b selected model | 0.608-0.637 | 0.608-0.636 | **DISCREPANCY** |
| FigureS3 | Selected-model C on all TNM-complete validation (F16) equals F02b | 0.6216 | 0.6216 | **PASS** |
