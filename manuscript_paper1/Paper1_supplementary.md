# Supplementary Material — Paper 1

**Draft for supervisor review.** All tables below are generated from the locked v8 outputs (`results/final_v7`) and the Paper 1 coefficient outputs (`results/final_v9/paper1`). Nothing has been re-estimated.


## Table S1. Included (TNM complete) versus excluded (TNM incomplete) patients
Source: `F32_supp_S1_included_vs_excluded.csv`; standardised differences from `F65`.

| characteristic | Analytic cohort (TNM complete, n=17,262) | Excluded, incomplete TNM (n=8,832) | note |
|---|---|---|---|
| Patients | 17,262 | 8,832 | Both groups met registry steps 1-7 |
| Age at operation, years, median (IQR) | 63.4 (55.7-70.6) | 63.0 (55.3-69.9) |  |
| Male sex, n (%) | 10,676 (61.8) | 5,333 (60.4) |  |
| Synchronous presentation, n (%) | 10,015 (58.0) | 3,674 (41.6) |  |
| Number of liver metastases known, n (%) | 16,011 (92.8) | 7,068 (80.0) |  |
| Largest recorded metastasis known, n (%) | 13,956 (80.8) | 6,425 (72.7) |  |
| Pre-operative CEA recorded, n (%) | 11,364 (65.8) | 4,898 (55.5) |  |
| Deaths recorded, n (%) | 6,601 (38.2) | 3,705 (41.9) |  |
| Deaths inside the 15-year window (events), n (%) | 6,591 (38.2) | 3,696 (41.8) |  |
| Median overall survival, years (KM) | 4.15 | 3.84 |  |

| characteristic | included | excluded | SMD |
|---|---|---|---|
| Age at operation, years | 63.4 (IQR 55.7-70.6; n=15,271) | 63.0 (IQR 55.3-69.9; n=7,416) | 0.051 |
| Male sex | 61.9% (n=17,246) | 60.4% (n=8,827) | 0.031 |
| Synchronous presentation | 58.7% (n=17,064) | 44.8% (n=8,210) | 0.282 |
| Number of liver metastases (known) | 2.0 (IQR 1.0-3.0; n=16,011) | 2.0 (IQR 1.0-3.0; n=7,068) | 0.017 |
| Largest metastasis, mm (known) | 30.0 (IQR 20.0-45.0; n=13,956) | 35.0 (IQR 20.0-50.0; n=6,425) | -0.186 |
| Pre-operative CEA, ng/mL (known) | 7.2 (IQR 2.8-25.0; n=11,364) | 9.7 (IQR 3.2-41.0; n=4,898) | -0.029 |
| Operation year | 2010.0 (IQR 2007.0-2013.0; n=17,262) | 2007.0 (IQR 2001.0-2011.0; n=8,832) | 0.584 |
| Metachronous: interval unavailable | 55.9% (n=7,049) | 66.2% (n=4,536) |  |

## Table S2. Missing TNM components among the 26,094 patients meeting criteria
Source: `investigation/F45_TNM_missing_patterns_step7.csv`; reasons (ND vs blank) in `investigation/F46_TNM_missing_reasons_step7.csv`.

| missing_components | n | pct_of_step7 |
|---|---|---|
| none (complete) | 17262 | 66.15 |
| T + N + M | 3041 | 11.65 |
| T | 2324 | 8.91 |
| M | 1358 | 5.2 |
| T + N | 1220 | 4.68 |
| T + M | 418 | 1.6 |
| N | 402 | 1.54 |
| N + M | 69 | 0.26 |

## Table S3. Duplicate-record screen and sensitivity
Sources: `F60`, `F61`.

| item | n |
|---|---|
| records in identical-content pairs | 46 |
| identical-content pairs | 23 |
| pairs meeting the probable-duplicate rule | 16 |
| pairs with copies at different countries | 16 |
| second copies of identical pairs inside the analytic cohort | 6 |
| near-duplicate groups (birth date, operation date, sex match; different content) | 55 |
| near-duplicate groups with both copies in the analytic cohort | 31 |
| near-duplicate groups with one copy in the analytic cohort | 11 |
| later records dropped in the broad sensitivity (birth date, operation date and sex match within the cohort) | 37 |

| analysis | analytic_n | development_n | validation_n | validation_C | validation_KM_5y | validation_O_over_E_5y | cut_S5_q33 | cut_S5_q67 | validation_Favourable_n | validation_Intermediate_n | validation_Adverse_n | patients_in_common_with_primary | pct_same_group_as_primary | kappa_vs_primary | reassigned_vs_primary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary (locked) | 17262 | 8463 | 8799 | 0.6216 | 0.4659 | 1.1425 | 0.3793 | 0.4756 | 2662 | 2824 | 3313 |  |  |  |  |
| identical-pair second copies removed | 17256 | 8461 | 8795 | 0.6216 | 0.4659 | 1.1424 | 0.3794 | 0.4756 | 2660 | 2825 | 3310 | 17256.0 | 99.81 | 0.9971 | 33.0 |
| later copies of birth/operation/sex matches removed (broad) | 17225 | 8444 | 8781 | 0.6216 | 0.4668 | 1.1455 | 0.3785 | 0.4753 | 2656 | 2833 | 3292 | 17225.0 | 99.2 | 0.988 | 138.0 |

## Table S4. Model without TNM staging and pre-operative-only models
Sources: `F62`, `F14`, `F23`.

| analysis | development_n | validation_n | validation_C | note |
|---|---|---|---|---|
| same patients: TNM M2a (primary) | 8463 | 8799 | 0.6216 | reference |
| same patients: no-TNM model (complete-case development) | 8463 | 8799 | 0.5994 | difference TNM minus no-TNM = 0.0222, 95% CI 0.0094 to 0.0335 (paired bootstrap, 300 resamples) |
| broader: no-TNM model (all development patients), same 8,799 validation patients | 14127 | 8799 | 0.5982 | same patients as the primary validation set |
| broader: no-TNM model (all development patients), all validation patients | 14127 | 11967 | 0.5972 | includes patients with incomplete TNM; not comparable with the TNM model |

| model | train_C | valid_C | valid_C_95CI | tAUC_1y | tAUC_3y | tAUC_5y | Brier_1y | Brier_3y | Brier_5y | IBS_1_7y | valid_observed_S5 | valid_mean_predicted_S5 | valid_OE_5y | valid_calib_slope_5y |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pre-operative-only, M1 structure (no count or size) | 0.57 | 0.5913 | 0.573-0.606 | 0.594 | 0.623 | 0.638 | 0.0611 | 0.1036 | 0.0676 | 0.0773 | 0.466 | 0.414 | 1.126 | 1.358 |

| model | train_C | valid_C | valid_C_95CI | tAUC_1y | tAUC_3y | tAUC_5y | Brier_1y | Brier_3y | Brier_5y | IBS_1_7y | valid_observed_S5 | valid_mean_predicted_S5 | valid_OE_5y | valid_calib_slope_5y | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pre-operative-only, selected M2a structure (no count or size) | 0.5706 | 0.5905 | 0.575-0.604 | 0.593 | 0.624 | 0.64 | 0.0611 | 0.1035 | 0.0676 | 0.0773 | 0.466 | 0.413 | 1.128 | 1.307 | like-for-like with selected model |

## Table S5. Excluded patients: period, centre and outcomes
Sources: `F63`, `F64` (sites and countries), `F66`, `F67`.

| operation_years | analytic_n | excluded_n | pct_excluded |
|---|---|---|---|
| 1990-1999 | 637 | 1466 | 69.7 |
| 2000-2004 | 1825 | 1514 | 45.3 |
| 2005-2009 | 5967 | 2353 | 28.3 |
| 2010-2014 | 6637 | 2472 | 27.1 |
| 2015-2020 | 2162 | 696 | 24.4 |

| level | units | units_no_exclusions | units_only_exclusions | units_50pct_or_more_excluded | median_patients_per_unit | pct_of_exclusions_in_10_largest_units |
|---|---|---|---|---|---|---|
| sites | 259 | 57 | 11 | 34 | 22 | 54.0 |
| countries | 52 | 3 | 1 | 7 | 89 | 81.6 |

| group | included_n | excluded_n | included_deaths_pct | excluded_deaths_pct | included_KM_5y | excluded_KM_5y | included_KM_median_y | excluded_KM_median_y |
|---|---|---|---|---|---|---|---|---|
| all | 17262 | 8832 | 38.2 | 41.9 | 0.436 | 0.407 | 4.15 | 3.84 |
| development (<=2009) | 8463 | 5664 | 55.4 | 55.0 | 0.423 | 0.391 | 3.97 | 3.67 |
| validation (>=2010) | 8799 | 3168 | 21.8 | 18.5 | 0.466 | 0.505 | 4.5 | 5.25 |

| group | period | n | predicted_5y_no_TNM | observed_5y_KM | O_over_E |
|---|---|---|---|---|---|
| included (TNM complete) | development | 8463 | 0.411 | 0.423 | 1.028 |
| included (TNM complete) | validation | 8799 | 0.401 | 0.466 | 1.161 |
| excluded (TNM incomplete) | development | 5664 | 0.406 | 0.391 | 0.963 |
| excluded (TNM incomplete) | validation | 3168 | 0.399 | 0.505 | 1.266 |

## Table S6. Death flags and the 15-year window
Sources: `F12`, `F18b`. Among the 11,594 patients recorded as deceased in the full extract, 3,074 lack an explicit death flag. The analytic cohort contains 6,601 recorded deaths, 6,591 inside the window.

| check | n |
|---|---|
| deceased (PATSTATC) | 11594 |
| deceased with any DEATHKYN_F = Yes | 8520 |
| deceased without any DEATHKYN_F = Yes | 3074 |
| alive/lost but DEATHKYN_F = Yes | 2 |
| LASTNDTC earlier than latest follow-up date | 9 |
| LASTNDTC later than latest follow-up date | 1 |
| modelling cohort with last contact before time zero | 0 |
| modelling deaths after censoring date 2020-07-04 | 0 |
| modelling cohort: deaths recorded (PATSTATC = Deceased) | 6601 |
| modelling cohort: deaths inside the 15-year window (events in the models) | 6591 |
| modelling cohort: deaths beyond 15 years (censored at 15 years) | 10 |
| modelling cohort: PATIENTS with follow-up beyond 15 years (all statuses; not a death count) | 69 |
| modelling cohort: of those patients, number who died | 10 |

| time_from_operation | n | flag_yes | flag_yes_pct |
|---|---|---|---|
| same day | 13 | 6 | 46.2 |
| 1-30 days | 197 | 99 | 50.3 |
| 31-365 days | 1163 | 843 | 72.5 |
| 1-5 years | 4470 | 3648 | 81.6 |
| >5 years | 758 | 533 | 70.3 |

## Table S7. Reproduction check against the previously validated analysis
Source: `F25_reproduction_check_against_v6.csv`.

| check | this_run | v6_reference | result |
|---|---|---|---|
| selected model | M2a | M2a | PASS |
| cut-point q33 | 0.3793 | 0.3793 | PASS |
| cut-point q67 | 0.4756 | 0.4756 | PASS |
| primary cohort | 17262 | 17262 | PASS |
| M2a validation C | 0.6216 | 0.6216 | PASS |
| RFS primary median | 2.03 | 2.03 | PASS |
| pre-operative (M1 structure) validation C | 0.5913 | 0.5913 | PASS |
| Fong subset C | 0.6394 | 0.6394 | PASS |
| Nordlinger subset C | 0.6303 | 0.6303 | PASS |
| CEA complete-case HR | 1.159 | 1.159 | PASS |

## Table S8. Horizon feasibility and group events by horizon
Sources: `feasibility/G01`, `G02`, `G04` (centre-held-out feasibility, not a validation result).

| horizon_years | validation_n | evaluable_n | pct_evaluable | deaths_before_horizon | at_risk_at_horizon | mean_predicted_survival | observed_KM_survival | observed_KM_95CI | O_over_E | sparse_flag_under_50_at_risk |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8799 | 5335 | 60.6 | 581 | 4754 | 0.897 | 0.91 | 0.903-0.917 | 1.015 | False |
| 3 | 8799 | 3118 | 35.4 | 1544 | 1574 | 0.592 | 0.645 | 0.630-0.661 | 1.091 | False |
| 5 | 8799 | 2289 | 26.0 | 1848 | 441 | 0.408 | 0.466 | 0.444-0.487 | 1.142 | False |

| group | horizon_years | n | deaths_before_horizon | at_risk_at_horizon |
|---|---|---|---|---|
| Favourable | 1 | 2662 | 98 | 1470 |
| Favourable | 3 | 2662 | 275 | 568 |
| Favourable | 5 | 2662 | 355 | 194 |
| Intermediate | 1 | 2824 | 151 | 1583 |
| Intermediate | 3 | 2824 | 469 | 534 |
| Intermediate | 5 | 2824 | 581 | 129 |
| Adverse | 1 | 3313 | 332 | 1701 |
| Adverse | 3 | 3313 | 800 | 472 |
| Adverse | 5 | 3313 | 912 | 118 |

| threshold_TNM_complete_patients_per_unit | sites_meeting_threshold | sites_with_validation_events_20plus | patients_in_qualifying_sites_pct | countries_meeting_threshold |
|---|---|---|---|---|
| 20 | 122 | 32 | 95.5 | 37 |
| 50 | 78 | 32 | 87.0 | 27 |
| 100 | 51 | 29 | 76.0 | 22 |

## Table S9. Reporting checklists
See `Paper1_reporting_checklists.md` (STROBE and TRIPOD items mapped to manuscript sections, with open items).

## Coefficient outputs
Baseline survival by stratum (`P1_baseline_survival_by_stratum.csv`) and group summary (`P1_group_summary.csv`) are in `results/final_v9/paper1/`.

| stratum_sex_synchrony_Mstage | baseline_survival_1y_at_reference_covariates | baseline_survival_3y_at_reference_covariates | baseline_survival_5y_at_reference_covariates |
|---|---|---|---|
| 0 | 0.9762 | 0.8781 | 0.809 |
| 1 | 0.965 | 0.854 | 0.7572 |
| 2 | 0.9747 | 0.8698 | 0.802 |
| 3 | 0.9742 | 0.8852 | 0.8147 |
| 4 | 0.9765 | 0.8887 | 0.8082 |
| 5 | 0.967 | 0.8403 | 0.751 |
| 6 | 0.9771 | 0.8878 | 0.8008 |
| 7 | 0.9776 | 0.8919 | 0.8134 |

| group | development_n | validation_n | predicted_5y_survival_range_validation | mean_predicted_5y_validation |
|---|---|---|---|---|
| Favourable | 2821 | 2662 | 0.476-0.711 | 0.532 |
| Intermediate | 2821 | 2824 | 0.379-0.476 | 0.428 |
| Adverse | 2821 | 3313 | 0.000-0.379 | 0.291 |
