# final_v6 verification notes

Scripts: notebooks/final_v6.py (F00–F17), notebooks/sensitivity_v6.py (F18–F20).
Both ran to completion with exit code 0. Input SHA-256 values match results/logs/input_hashes.json (F20), so the source workbooks were not altered.

## 1. Cohort and survival definitions
- Primary: mid-month (15th) day rule for partial operation dates; reproduces report flow steps 1–7 (29,565 → 26,094).
- Modelling cohort: 17,262 TNM-complete patients (training 8,463 with operation ≤ 2009; validation 8,799 with operation ≥ 2010).
- Same-day deaths (operation date = last-news date, status Deceased; n = 19) set to 0.5 day.
- Time origin: first hepatectomy. Event: death from any cause; censoring at 2020-07-04.

## 2. M-stage PH corrections (identical patients, F02–F05)
| Model | Valid C | Valid 5-y O/E | Calibration slope | Training PH |
|---|---|---|---|---|
| M1 (M-stage covariate) | 0.6218 | 1.141 | 1.091 | fails (M1 p = 0.031) |
| M2a (stratum: sex × synchrony × M-stage) | 0.6216 | 1.142 | 1.074 | all constant terms pass |
| M2b (M-stage time-varying, 2-y split) | 0.6219 | 1.140 | 1.091 | time variation p = 0.21 |
Selected by prespecified rule: M2a (first passing, simplest). C is not used to choose the model.

## 3. Phenotypes (M2a, cut-points from training: 0.3793 and 0.4756)
| Phenotype | Validation n | Deaths | Median OS (y, 95% CI) | 5-y KM survival |
|---|---|---|---|---|
| Favourable | 2,662 | 383 | 7.38 (6.14–NE) | 0.629 |
| Intermediate | 2,824 | 598 | 4.44 (4.14–4.88) | 0.454 |
| Adverse | 3,313 | 935 | 3.18 (2.97–3.38) | 0.343 |
Log-rank p = 2.0 × 10⁻⁵² (validation); ordinal C 0.603. Bootstrap κ 0.832 (0.778–0.894; 100 resamples).

## 4. Date-imputation and predictor-timing sensitivity
- Day convention (F19): first day gives 17,265 patients; cut-points 0.3793/0.4752; 99.64% phenotype agreement with primary (κ 0.995). Month-end: 99.95% (κ 0.999).
- Same-day deaths (F19): half, one and quarter day give identical phenotypes at reported precision (100%). Excluding the 19 patients gives 99.63% agreement and cut-points 0.3800/0.4760. The convention does not change the results.
- Pre-operative-only model (no metastasis count or size, F14–F15): validation C 0.591; calibration slope 1.36; 70.6% phenotype agreement (κ 0.554). Predictors recorded after surgery are a material assumption.
- CEA (F13): complete case HR 1.159 per log unit, C 0.628 → 0.648; multiple imputation HR 1.153, C 0.622 → 0.637.

## 5. Death-date verification and RFS (F12, F17, F18)
- Same-day deaths (n = 19): operation date present for all, equal to last-news date for all; LASTNDTC maximum equals last news for all. DEATHKYN_F = Yes for 8 of 19; 11 lack an explicit death flag. Six have TNM missing in the registry and are outside the modelling cohort. The 13 with complete TNM are in the modelling cohort. Consistent with recorded death on the operation date, but not independently confirmed.
- Deceased 11,594; with DEATHKYN_F = Yes 8,520; deceased without any Yes 3,074; alive or lost with Yes 2. LASTNDTC earlier than latest follow-up 9; later 1. No modelling death occurs after time zero's last contact or after the censoring date.
- RFS (primary, dated recurrence and death; undated recurrences censored): median 2.03 y (1.98–2.09), 5-y 0.276. Sensitivity: undated recurrences as events at last contact 1.93 y; at mid-interval 1.69 y; undated patients excluded 1.84 y.
- Informative censoring (F11): undated recurrences differ in follow-up and death rate from dated and no-recurrence patients, but predicted 5-y survival is similar (0.414 / 0.407 / 0.420). RFS remains secondary.

## 6. Performance, calibration and clinical-score comparisons (F16)
| Subset | n (valid) | Model C | Mean predicted 5-y S | Observed 5-y S | O/E | Comparator C |
|---|---|---|---|---|---|---|
| All TNM-complete | 8,799 | 0.6216 | 0.408 | 0.466 | 1.142 | — |
| Fong CRS (CEA recorded) | 3,642 | 0.6394 | 0.399 | 0.474 | 1.188 | Fong 0.5912 |
| Nordlinger-type | 6,137 | 0.6303 | 0.399 | 0.461 | 1.155 | Nordlinger 0.583 |
The model is well discriminating but over-predicts survival (O/E > 1; observed survival higher than predicted), and the validation set is not recalibrated in the primary report.

## 7. Remaining limitations
1. Metastasis count and size are assumed to be known at operation; operative-form counts agree with pre-operative counts for 13,130 of 20,553 patients only, and the resected count exceeds the pre-op count in 3,179.
2. 3,074 deceased patients lack any DEATHKYN_F = Yes; death dates rely on LASTNDTC.
3. Calibration: O/E 1.14 in validation; model is not recalibrated for the primary report.
4. M-stage PH violation addressed by stratification (M2a), not by a hazard-ratio-only model.
5. Undated recurrences (1,676) cannot be placed in time; RFS is secondary.
6. The 19 same-day deaths are internally consistent but not independently verified.
7. Only 2 patients alive with a death flag; 69 deaths beyond 15 years are censored at 15 years.

## Deleted
results/final_v6/F10_day_convention_sensitivity.csv was removed: it compared groups from different models (33% agreement, invalid). Replaced by F19.
