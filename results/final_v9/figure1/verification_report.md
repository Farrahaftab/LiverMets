# Figure 1 verification report (STROBE, Cox M2a)

Automated checks: 28 run, 28 passed, 0 failed.

## Displayed statistics and their sources

| ID | Label | Displayed | Source file | Field | Raw |
|---|---|---|---|---|---|
| N_registry | Step count: 1 registry | 29,565 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '1 registry' | 29565 |
| N_eligible | Step count: 2 CINCLUSION=Yes | 28,979 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '2 CINCLUSION=Yes' | 28979 |
| N_hepatectomy | Step count: 3 hepatectomy | 26,677 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '3 hepatectomy' | 26677 |
| N_opdate | Step count: 4 operation date (year+month) | 26,592 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '4 operation date (year+month)' | 26592 |
| N_status | Step count: 5 status and last-news | 26,271 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '5 status and last-news' | 26271 |
| N_chronology | Step count: 6 chronology | 26,186 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '6 chronology' | 26186 |
| N_followup | Step count: 7 positive follow-up or death | 26,094 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '7 positive follow-up or death' | 26094 |
| N_analytic | Step count: 8 complete TNM (analytic cohort) | 17,262 | `results/final_v7/F30_flow_counts_for_figure1.csv` | n where step = '8 complete TNM (analytic cohort)' | 17262 |
| X_eligible | Exclusion at step 'eligible' (difference of consecutive counts) | 586 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 1 registry - 2 CINCLUSION=Yes | 586 |
| X_hepatectomy | Exclusion at step 'hepatectomy' (difference of consecutive counts) | 2,302 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 2 CINCLUSION=Yes - 3 hepatectomy | 2302 |
| X_opdate | Exclusion at step 'opdate' (difference of consecutive counts) | 85 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 3 hepatectomy - 4 operation date (year+month) | 85 |
| X_status | Exclusion at step 'status' (difference of consecutive counts) | 321 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 4 operation date (year+month) - 5 status and last-news | 321 |
| X_chronology | Exclusion at step 'chronology' (difference of consecutive counts) | 85 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 5 status and last-news - 6 chronology | 85 |
| X_followup | Exclusion at step 'followup' (difference of consecutive counts) | 92 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 6 chronology - 7 positive follow-up or death | 92 |
| X_analytic | Exclusion at step 'analytic' (difference of consecutive counts) | 8,832 | `results/final_v7/F30_flow_counts_for_figure1.csv` | difference 7 positive follow-up or death - 8 complete TNM (analytic cohort) | 8832 |
| P_incomplete | Percent excluded for incomplete TNM of those meeting criteria | 33.8% | `results/final_v7/F30_flow_counts_for_figure1.csv` | computed: excluded / step 7 count | 33.847 |
| N_dev | Development cohort n | 8,463 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Patients', column Development | 8463 |
| N_val | Validation cohort n | 8,799 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Patients', column Validation | 8799 |
| EV_dev | Development events inside 15-year window | 4,675 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Deaths inside the 15-year analysis window (events)', column Development | 4675 |
| EV_val | Validation events inside 15-year window | 1,916 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Deaths inside the 15-year analysis window (events)', column Validation | 1916 |
| REC_dev | Development deaths recorded (PATSTATC) - reported in notes only | 4,685 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Deaths recorded (PATSTATC = Deceased)', column Development | 4685 |
| BEYOND_dev | Development deaths beyond 15 years (recorded minus window events), footnote | 10 | `results/final_v7/F31_table1_baseline_characteristics.csv` | Deaths recorded minus Deaths inside window, Development | 10 |
| N_terms | Number of terms in M2a | 11 | `results/final_v9/paper1/P1_model_coefficients.csv` | number of data rows | 11 |
| N_strata | Number of strata (sex x synchrony x M-stage) | 8 | `results/final_v9/paper1/P1_baseline_survival_by_stratum.csv` | number of data rows | 8 |
| CUT_lo | Cut-point, lower tertile of predicted 5-y survival | 0.3793 | `results/final_v7/F00_headline.csv` | phenotype_cut_S5_q33 | 0.3793 |
| CUT_hi | Cut-point, upper tertile of predicted 5-y survival | 0.4756 | `results/final_v7/F00_headline.csv` | phenotype_cut_S5_q67 | 0.4756 |
| C_dev | C-index, development (apparent) | 0.595 | `results/final_v7/F02b_selected_model_performance.csv` | train_C | 0.5952 |
| C_val | C-index, validation | 0.622 | `results/final_v7/F02b_selected_model_performance.csv` | valid_C | 0.6216 |
| C_ci | C-index validation 95% CI | 0.608–0.636 | `results/final_v7/F02b_selected_model_performance.csv` | valid_C_95CI | 0.608-0.636 |
| OE5 | Observed/expected 5-y survival, validation | 1.14 | `results/final_v7/F02b_selected_model_performance.csv` | valid_OE_5y | 1.142 |
| OBS5 | Observed 5-y survival (KM), validation | 46.6% | `results/final_v7/F02b_selected_model_performance.csv` | valid_observed_S5 | 0.466 |
| PRED5 | Mean predicted 5-y survival, validation | 40.8% | `results/final_v7/F02b_selected_model_performance.csv` | valid_mean_predicted_S5 | 0.408 |
| IBS | Integrated Brier score 1-7 y, validation | 0.075 | `results/final_v7/F02b_selected_model_performance.csv` | IBS_1_7y | 0.0752 |
| EVAL5 | Validation patients evaluable at 5 years (%) | 26% | `results/final_v7/feasibility/G01_horizon_feasibility_validation.csv` | pct_evaluable, horizon 5 | 26.0 |
| ORD_C | Ordinal C-index of the three groups, validation | 0.603 | `results/final_v7/F08_phenotype_separation.csv` | valid_C_ordinal | 0.6032 |
| P_val | Log-rank p, validation (group separation) | 2.0e-52 | `results/final_v7/F08_phenotype_separation.csv` | valid_logrank_p | 1.960688139201623e-52 |
| P_dev | Log-rank p, development (group separation) | 1.4e-77 | `results/final_v7/F08_phenotype_separation.csv` | train_logrank_p | 1.3516744662754814e-77 |
| RFS_med | Median RFS, years (primary, secondary outcome) | 2.03 | `results/final_v7/F17_RFS_sensitivity_final.csv` | median_RFS (PRIMARY row) | 2.03 |
| RFS_ci | Median RFS 95% CI | 1.98–2.09 | `results/final_v7/F17_RFS_sensitivity_final.csv` | median_95CI (PRIMARY row) | 1.98-2.09 |
| FU_dev | Median follow-up, development (reverse KM), years | 5.89 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Median follow-up', column Development | 5.89 |
| FU_val | Median follow-up, validation (reverse KM), years | 1.47 | `results/final_v7/F31_table1_baseline_characteristics.csv` | row 'Median follow-up', column Validation | 1.47 |
| C_ci_F02 | C-index validation 95% CI in F02 (reported in text) | 0.608–0.637 | `results/final_v7/F02_M_stage_candidates_identical_patients.csv` | valid_C_95CI, row M2a | 0.608-0.637 |
| FAV_dev_n | Favourable: development n | 2,821 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column dev_n | 2821 |
| FAV_val_n | Favourable: validation n | 2,662 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column val_n | 2662 |
| FAV_val_deaths | Favourable: validation deaths | 383 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column val_deaths | 383 |
| FAV_val_med | Favourable: validation median OS (years) | 7.38 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column val_med | 7.38 |
| FAV_val_s5 | Favourable: validation 5-y KM survival | 62.9% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column val_s5 | 0.629 |
| FAV_dev_s5 | Favourable: development 5-y KM survival | 54.1% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column dev_s5 | 0.541 |
| FAV_med_ci | Favourable: validation median OS 95% CI | 6.14–NE | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column valid_median_95CI | 6.14-NE |
| FAV_pred5 | Favourable: validation mean predicted 5-y (for reference) | 53.2% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Favourable', column valid_mean_predicted_S5 | 0.532 |
| INT_dev_n | Intermediate: development n | 2,821 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column dev_n | 2821 |
| INT_val_n | Intermediate: validation n | 2,824 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column val_n | 2824 |
| INT_val_deaths | Intermediate: validation deaths | 598 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column val_deaths | 598 |
| INT_val_med | Intermediate: validation median OS (years) | 4.44 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column val_med | 4.44 |
| INT_val_s5 | Intermediate: validation 5-y KM survival | 45.4% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column val_s5 | 0.454 |
| INT_dev_s5 | Intermediate: development 5-y KM survival | 41.9% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column dev_s5 | 0.419 |
| INT_med_ci | Intermediate: validation median OS 95% CI | 4.14–4.88 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column valid_median_95CI | 4.14-4.88 |
| INT_pred5 | Intermediate: validation mean predicted 5-y (for reference) | 42.8% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Intermediate', column valid_mean_predicted_S5 | 0.428 |
| ADV_dev_n | Adverse: development n | 2,821 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column dev_n | 2821 |
| ADV_val_n | Adverse: validation n | 3,313 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column val_n | 3313 |
| ADV_val_deaths | Adverse: validation deaths | 935 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column val_deaths | 935 |
| ADV_val_med | Adverse: validation median OS (years) | 3.18 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column val_med | 3.18 |
| ADV_val_s5 | Adverse: validation 5-y KM survival | 34.3% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column val_s5 | 0.343 |
| ADV_dev_s5 | Adverse: development 5-y KM survival | 30.7% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column dev_s5 | 0.307 |
| ADV_med_ci | Adverse: validation median OS 95% CI | 2.97–3.38 | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column valid_median_95CI | 2.97-3.38 |
| ADV_pred5 | Adverse: validation mean predicted 5-y (for reference) | 29.1% | `results/final_v7/F06_phenotypes_counts_survival_calibration.csv` | row 'Adverse', column valid_mean_predicted_S5 | 0.291 |

## Consistency checks

| Check | Expected | Observed | Status |
|---|---|---|---|
| F01 mid-month equals F30 at step '1 registry' | 29565 | 29565 | **PASS** |
| F01 mid-month equals F30 at step '2 CINCLUSION=Yes' | 28979 | 28979 | **PASS** |
| F01 mid-month equals F30 at step '3 hepatectomy' | 26677 | 26677 | **PASS** |
| F01 mid-month equals F30 at step '4 operation date (year+month)' | 26592 | 26592 | **PASS** |
| F01 mid-month equals F30 at step '5 status and last-news' | 26271 | 26271 | **PASS** |
| F01 mid-month equals F30 at step '6 chronology' | 26186 | 26186 | **PASS** |
| F01 mid-month equals F30 at step '7 positive follow-up or death' | 26094 | 26094 | **PASS** |
| Excluded count: F30 difference equals F32 'Excluded' n | 8832 | 8832 | **PASS** |
| Analytic count: F30 equals F32 'Analytic cohort' n | 17262 | 17262 | **PASS** |
| Development + validation equals analytic cohort (F30 step 8) | 17262 | 17262 | **PASS** |
| Development + validation equals F31 total | 17262 | 17262 | **PASS** |
| Window events (dev + val) equal F12 modelling cohort window events | 6591 | 6591 | **PASS** |
| Recorded deaths (dev + val) equal F12 modelling-cohort recorded deaths | 6601 | 6601 | **PASS** |
| Recorded minus window events (dev + val) equal F12 deaths beyond 15 years | 10 | 10 | **PASS** |
| Strata count equals 2 x 2 x 2 = 8 | 8 | 8 | **PASS** |
| 5-y observed KM survival: F02b equals G01 | 0.466 | 0.466 | **PASS** |
| 5-y predicted survival: F02b equals G01 | 0.408 | 0.408 | **PASS** |
| 5-y O/E: F02b equals G01 | 1.142 | 1.142 | **PASS** |
| Validation C-index 95% CI: F02 (candidate table) equals F02b (selected model) | 0.608-0.637 | 0.608-0.636 | **DISCREPANCY** |
| Group development n sum equals development cohort n | 8463 | 8463 | **PASS** |
| Group validation n sum equals validation cohort n | 8799 | 8799 | **PASS** |
| Group validation deaths sum equals validation window events | 1916 | 1916 | **PASS** |
| Development groups are equal thirds (each = dev n / 3) | 2821.0 | 2821 | **PASS** |
| Development group sizes are identical across the three groups | True | True | **PASS** |
| Validation 5-y KM ordering: Favourable > Intermediate > Adverse | True | True | **PASS** |
| Validation 5-y KM (overall) equals G01 observed survival | 0.466 | 0.466 | **PASS** |
| F07 definition for Favourable references the upper cut-point (from F00) | True | True | **PASS** |
| F07 definition for Adverse references the lower cut-point (from F00) | True | True | **PASS** |

## Discrepancies between locked outputs (reported, NOT corrected; figure shows the F02b value)

- Validation C-index 95% CI: F02 (candidate table) equals F02b (selected model): F02 = 0.608-0.637, F02b = 0.608-0.636
