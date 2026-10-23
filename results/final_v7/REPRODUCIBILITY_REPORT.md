# CRLM survival: final reproducibility report (v7)

Notebook: `notebooks/LiverMets_final_reproducible.ipynb` (source `notebooks/LiverMets_final_reproducible.py`).
Input: `LiverMet_Part1.xlsx` and `LiverMet_Part2.xlsx`, read directly from the raw workbooks (streaming, `python-calamine`).
Outputs: `results/final_v7/` (tables `F*.csv`, figures `figures/COX_*.png`, manifest `F24_run_manifest.json`).
Manuscript: not modified.

## 1. Execution

| Check | Result |
|---|---|
| Cells | 24 total: 12 markdown, 12 code |
| Code cells executed | 12 of 12, 0 errors (executed copy used for this report) |
| Runtime | about 7.5 minutes on the build machine (manifest: 433 s for the analysis run) |
| Input SHA-256 | Part 1 `7eed0ab9…a976` and Part 2 `a1839daa…a161049`: both match the recorded values |
| Rows | Part 1: 14,782 patients (header row excluded); Part 2: 14,783; combined 29,565 |
| Packages | pandas 2.3.3, numpy 2.5.3, lifelines 0.30.3, scikit-survival 0.28.0, scikit-learn 1.9.1, pyarrow 26.0.0, python-calamine 0.8.3; Python 3.13.16 |

Two defects were found during execution and fixed before the final run. A calibration cell indexed the selected model as an attribute instead of a dictionary key. The first-run calibration figure title was also corrected. Neither changed any reported number.

## 2. Reproduction of the validated v6 analysis

All ten reference checks pass (`F25_reproduction_check_against_v6.csv`):

| Quantity | v7 | v6 |
|---|---|---|
| Selected model | M2a | M2a |
| Phenotype cut-points (predicted 5-year survival) | 0.3793 / 0.4756 | 0.3793 / 0.4756 |
| Primary cohort (TNM-complete) | 17,262 | 17,262 |
| M2a validation C-index | 0.6216 | 0.6216 |
| Pre-operative-only validation C-index (M1 structure) | 0.5913 | 0.5913 |
| Fong-subset C-index | 0.6394 | 0.6394 |
| Nordlinger-type subset C-index | 0.6303 | 0.6303 |
| RFS primary median (years) | 2.03 | 2.03 |
| CEA complete-case HR per log unit | 1.159 | 1.159 |

One difference was found and is recorded in section 9: the day-convention rows of v6 `F19` (first-day and month-end) were computed by a separate routine and are superseded by v7 `F10`.

## 3. Cohort and definitions

* **Flow** (`F01`): 29,565 registry → 28,979 CINCLUSION = Yes → 26,677 hepatectomy → 26,592 operation date → 26,271 status and last-news → 26,186 chronology → 26,094 positive follow-up or death (matches the report). Modelling cohort after TNM completeness: **17,262**.
* **Time origin**: first hepatectomy. **Event**: death (`PATSTATC = Deceased`). **Censoring**: last-news date, capped at 15 years, and no deaths after 4 July 2020.
* **Partial operation dates**: 15th of the month (primary); 1st and last-day rules are sensitivity analyses.
* **Same-day deaths** (operation date = last-news date, status Deceased): half-day time (primary).
* **Split**: training = operated 2009 or earlier (n = 8,463; 4,675 deaths); validation = operated 2010 or later (n = 8,799; 1,916 deaths). Validation was used only to evaluate fixed models and cut-points.

## 4. Selected model

Pre-specified selection rule (training-only PH tests): M1 fails (M-stage constant term p = 0.031); M2a passes all constant terms, so **M2a** is selected. M2b (time-varying M-stage) shows no significant change after 2 years (p = 0.21).

| Model | Validation C (95% CI) | Validation 5-y O/E | Calibration slope (5-y) |
|---|---|---|---|
| M1 (M-stage covariate) | 0.6218 (0.606–0.636) | 1.141 | 1.091 |
| **M2a (M-stage in strata)** | **0.6216 (0.608–0.637)** | **1.142** | **1.074** |
| M2b (time-varying M-stage) | 0.6219 (0.609–0.637) | 1.140 | 1.091 |

The three candidates give essentially identical discrimination and calibration on identical patients. The choice is driven by the PH rule, not by C-index.

## 5. Prognostic groups (M2a, training-only cut-points)

Groups are tertiles of predicted 5-year survival. Cut-points are fixed in training and applied unchanged to validation.

| Group | Definition | Validation n | Deaths | Median OS, years (95% CI) | 5-y OS (KM) | Mean predicted 5-y S (validation) |
|---|---|---|---|---|---|---|
| Favourable | predicted 5-y ≥ 0.4756 | 2,662 | 383 | 7.38 (6.14–NE) | 0.629 | 0.532 |
| Intermediate | 0.3793 ≤ predicted < 0.4756 | 2,824 | 598 | 4.44 (4.14–4.88) | 0.454 | 0.428 |
| Adverse | predicted < 0.3793 | 3,313 | 935 | 3.18 (2.97–3.38) | 0.343 | 0.291 |

* All three groups are present in training and validation; the three-group log-rank test is p = 2 × 10⁻⁵² in validation (training p = 1 × 10⁻⁷⁷); ordinal C = 0.603.
* Bootstrap stability (100 resamples): κ = 0.832 (95% range 0.778–0.894).
* Figures: `figures/COX_01_OS_by_M2a_group_validation.png` shows all three groups with validation counts 2,662 / 2,824 / 3,313 (verified by eye). `figures/COX_02_RFS_by_M2a_group_validation.png` shows RFS for 2,590 / 2,738 / 3,172.

## 6. Model performance (validation)

| Measure | Value |
|---|---|
| Harrell C (selected M2a) | 0.6216 (0.608–0.637) |
| Time-dependent AUC 1 / 3 / 5 years | 0.639 / 0.653 / 0.675 |
| Brier 1 / 3 / 5 years | 0.060 / 0.101 / 0.065 |
| Integrated Brier score 1–7 years | 0.075 |

## 7. Same-day deaths: verification and sensitivity

**Scope.** 19 patients in the registry have operation date = last-news date with status Deceased. 13 are in the modelling cohort, and 6 lack TNM staging.

**Verification (`F18`, `F18b`).**
* All 19 have a complete operation date and exactly one follow-up form.
* 8 carry death flag `DEATHKYN_F = Yes`; 11 have no flag (10 "No", 1 "ND"). In the modelling cohort the split is 6 flagged and 7 unflagged.
* The missing-flag pattern is not specific to same-day deaths. Among deceased modelling-cohort patients, the flag reads Yes for 46% of same-day deaths, 50% at 1–30 days, 73% at 31–365 days, 82% at 1–5 years and 70% after 5 years (`F18b`). Missing or "No" death flags therefore occur at every time point.
* Interpretation: the 7 unflagged same-day deaths are supported by status and last-news date but not by an explicit death flag. They cannot be confirmed independently.

**Sensitivity (`F19`).**

| Analysis | Modelling n | Same-day deaths | Validation C | Cut-points (0.33 / 0.67) | Phenotype agreement with primary | κ |
|---|---|---|---|---|---|---|
| Primary: half-day, all kept | 17,262 | 13 | 0.6216 | 0.3793 / 0.4756 | 100% | 1.00 |
| **Exclude the 7 unflagged same-day deaths** | **17,255** | 6 | **0.6226** | 0.3797 / 0.4760 | 99.63% | 0.994 |
| Unflagged same-day deaths censored at half-day | 17,262 | 13 | 0.6226 | 0.3796 / 0.4759 | 99.63% | 0.994 |

Excluding or censoring the seven unflagged deaths changes the C-index by 0.001 and reclassifies about 0.4% of patients. The primary result does not depend on these deaths.

## 8. Pre-operative-only model

Metastasis count and size are removed. Two structures are reported:

| Model | Validation C (95% CI) | Validation 5-y O/E | Calibration slope | Phenotype agreement (validation κ) |
|---|---|---|---|---|
| Pre-operative, M1 structure (`F14`) | 0.5913 (0.573–0.606) | 1.126 | 1.358 | 70.4% (0.554) |
| Pre-operative, selected M2a structure (`F23`) | 0.5905 (0.575–0.604) | 1.128 | 1.307 | 71.9% (0.577) |
| Full selected model (M2a) | 0.6216 | 1.142 | 1.074 | — |

Interpretation: the operative metastasis count and size add about 0.03 to the C-index (0.59 → 0.62). Pre-operative variables alone classify about 70% of validation patients into the same group as the full model, and the calibration slope is steeper than 1 (predictions are too compressed). The pre-operative-only model is a sensitivity analysis and is not recommended for clinical use.

## 9. Calibration

**Validation by decile of predicted 5-year survival (`F20`).** Predictions under-estimate survival in almost every decile. Observed minus predicted is positive in 9 of 10 deciles, reaching +0.18 in the top decile (observed 0.758 vs predicted 0.580). The first seven deciles have fewer than 50 patients with 5 years of follow-up (14–45), so their observed values are flagged as sparse (`reliable_5y_estimate = False`).

**Validation by operation period (`F21`).**

| Period | n | Predicted 5-y | Observed 5-y (KM) | O/E | Patients with 5-y follow-up |
|---|---|---|---|---|---|
| 1990–2004 | 2,462 | 0.434 | 0.415 | 0.955 | 822 |
| 2005–2009 (training) | 5,967 | 0.416 | 0.427 | 1.025 | 1,272 |
| 2010–2012 (validation) | 4,315 | 0.411 | 0.447 | 1.088 | 332 |
| 2013–2015 (validation) | 3,084 | 0.406 | 0.500 | 1.234 | 109 |
| 2016+ (validation) | 1,400 | 0.403 | not estimable | — | 0 |

Interpretation: calibration is good in the training era (O/E ≈ 1.0) and drifts upward in validation-era periods. The 2013–2015 estimate rests on 109 patients with 5 years of follow-up and is imprecise. The 2016+ period cannot be assessed at 5 years.

**Recalibration sensitivity (`F22`).** Re-estimating the baseline hazard from 2005–2009 only, with coefficients unchanged, reduces validation O/E from 1.142 to 1.115 (C 0.6197). Phenotype agreement with the primary groups is 92.2% (κ 0.883). This does not explain the calibration gap, and the primary analysis does **not** recalibrate.

**Figures.** `COX_03_calibration_by_decile_validation.png` (sparse deciles open) and `COX_04_O_over_E_by_period.png` (2016+ omitted, with 5-year counts).

## 10. Recurrence-free survival (secondary)

| RFS definition | n | Median RFS, years (95% CI) | 3-y | 5-y |
|---|---|---|---|---|
| **Primary:** dated recurrence or death; undated recurrences censored | 16,677 | 2.03 (1.98–2.09) | 0.393 | 0.276 |
| Undated recurrences as events at last contact | 16,677 | 1.93 (1.88–1.98) | 0.369 | 0.244 |
| Undated recurrences as events at mid-interval | 16,677 | 1.69 (1.65–1.74) | 0.329 | 0.228 |
| Undated recurrence patients excluded | 15,001 | 1.84 (1.78–1.90) | 0.368 | 0.268 |

Undated recurrences (1,676 patients) have different follow-up and death rates from dated and recurrence-free patients, but similar predicted 5-year survival (0.414 vs 0.407 vs 0.420; `F11`). RFS is reported as secondary.

## 11. Clinical benchmarks (validation subsets, identical patients)

| Subset | n | Deaths | Selected model C | Comparator C | O/E (5-y) |
|---|---|---|---|---|---|
| All TNM-complete | 8,799 | 1,916 | 0.6216 | — | 1.142 |
| Fong CRS subset (CEA recorded) | 3,642 | 914 | 0.6394 | Fong 0.5912 | 1.188 |
| Nordlinger-type subset | 6,137 | 1,396 | 0.6303 | Nordlinger 0.583 | 1.155 |

The comparator scores were implemented from their published components, and the Nordlinger-type score is an approximation built from the variables available in this registry (age ≥ 60, T4, N1–2, DFI < 12 months). They are not the original published models. State this in the manuscript.

CEA (`F13`): complete-case HR 1.159 per log unit (95% CI 1.132–1.186); C 0.6276 → 0.6480. Multiple imputation (10 draws): HR 1.153 (1.127–1.180); C 0.6224 → 0.6366. CEA is missing for about one-third of patients.

## 12. Figures: Cox M2a versus survival-tree figures

* **Cox M2a figures (this package, `results/final_v7/figures/`, prefix `COX_`):**
  * `COX_01_OS_by_M2a_group_validation.png`: OS by M2a group, all three groups.
  * `COX_02_RFS_by_M2a_group_validation.png`: RFS by M2a group, all three groups.
  * `COX_03_calibration_by_decile_validation.png`: calibration by decile.
  * `COX_04_O_over_E_by_period.png`: O/E by operation period.
* **Survival-tree figures (earlier analysis, `results/figures/F01–F09`, not part of v7):** these use the tree-leaf phenotypes from the main notebook. They are not the Cox groups.
* **Matched-treatment figure (`results/figures/F08_KM_matched_treatment_by_phenotype.png`):** it shows only Intermediate and Adverse. The Favourable group has zero patients in the treatment comparison pool, so the code skips it (`results/tables/T18_PSM_outcomes_by_phenotype.csv`). It uses the tree phenotypes, so it is superseded and must not be used for the Cox groups.

## 13. Results verified and assumptions

| Result | Status | Basis |
|---|---|---|
| Flow to 26,094; modelling cohort 17,262 | Verified | Recomputed from raw workbooks; matches report |
| Input files unchanged | Verified | SHA-256 match |
| M2a selected by PH rule; M1 fails | Verified | Training PH tests (`F03`, `F05`) |
| Cut-points 0.3793 / 0.4756 and three groups | Verified | Recomputed; matches v6 |
| Group separation (log-rank p, C) | Verified | `F08` |
| Same-day death sensitivity: no material effect | Verified | `F19` |
| Death flag verification | Partly verified | Status and last-news consistent; 7 modelling-cohort same-day deaths lack a flag |
| Metastasis count and size known at operation | **Assumption** | Operative counts agree with pre-operative counts for only 13,130 of 20,553 patients; not verifiable |
| Pre-operative model performance | Verified (as a sensitivity) | `F14`, `F23` |
| Calibration: over-prediction in validation | Verified | `F20`, `F16` (O/E 1.14) |
| Calibration over time (temporal drift) | **Partly verified** | Limited 5-year follow-up in later periods (`F21`) |
| RFS result | Verified as secondary | `F17`; depends on undated-recurrence handling |
| CEA effect | Verified (complete case and MI agree) | `F13`; CEA missing for about one-third |
| Benchmark scores (Fong, Nordlinger) | **Approximate** | Implemented from published components; Nordlinger-type is approximated |

## 14. Remaining limitations

1. **Calibration.** Survival is under-predicted in validation (O/E 1.14; top decile observed 0.76 vs predicted 0.58). Recalibration from recent data does not close the gap. The phenotype cut-points therefore give absolute 5-year survival estimates that are too low for 2010+ patients. The groups remain valid for ranking patients, but absolute survival should not be quoted from the model.
2. **Limited late follow-up.** Patients operated 2013 onward have few 5-year observations (109 for 2013–2015; none for 2016+). Calibration claims for these periods are provisional.
3. **Unverified predictors.** Metastasis count and size are assumed to be known at the time of operation. The pre-operative-only model shows how much discrimination depends on these variables (C 0.59 vs 0.62).
4. **Death dates.** 3,074 deceased patients have no death flag, and only last-news dates support their survival times. Same-day deaths and their flag status are reported in section 7.
5. **Undated recurrences.** 1,676 recurrences have no date. RFS is therefore secondary and its primary definition is one of four sensitivities.
6. **Benchmarks.** The Fong and Nordlinger comparisons use reconstructed scores on subsets. They are indicative only.
7. **Main-notebook figures and tables.** The earlier survival-tree figures and the matched-treatment figure use tree-leaf phenotypes, not the M2a groups, and the matched-treatment figure omits Favourable. These must be regenerated or clearly labelled before use with the Cox groups.
8. **Single-centre registry and temporal split.** Validation is temporal within one registry; no external validation was performed.

## 15. Files

* `notebooks/LiverMets_final_reproducible.ipynb`: executed notebook (12 code cells, 0 errors).
* `results/final_v7/*.csv`: tables F00–F25 (see section 16).
* `results/final_v7/figures/COX_01–04*.png`: Cox M2a figures.
* `results/final_v7/F24_run_manifest.json`: checksums, row counts, package versions.
* `results/final_v7/SUPERSEDED_RESULTS.md`: superseded register.

## 16. Table index

| File | Content |
|---|---|
| F00 | Headline: selected model and cut-points |
| F00a | Extract row counts |
| F01 | Flow by day convention |
| F02 / F02b | Candidate models; selected model performance |
| F03 / F04 / F05 | PH tests; M2b time-varying M-stage; selection rule |
| F06 / F07 / F08 / F09 | Group counts and survival; definitions; separation; bootstrap |
| F10 | Day and same-day conventions (replaces v6 F19 day-convention rows) |
| F11 | Undated recurrences and informative censoring |
| F12 | Death and last-contact checks |
| F13 | CEA sensitivity |
| F14 / F15 / F23 | Pre-operative-only models and agreement |
| F16 | Benchmark subsets and calibration |
| F17 | RFS sensitivity |
| F18 / F18b | Same-day death verification and death-flag rates by time |
| F19 | Unflagged same-day death sensitivity |
| F20 / F21 / F22 | Calibration by decile, period, and recalibration |
| F24 | Run manifest |
| F25 | Reproduction check against v6 |
