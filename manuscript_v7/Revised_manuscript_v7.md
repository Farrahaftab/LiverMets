---
title: "Prognostic Groups for Colorectal Liver Metastases: Survival Analysis in an International Registry with Temporal Validation"
author:
  - Farrah Aftab, MSc^1,*^; Mustansar Ali Ghazanfar, PhD^1^; Mudassar Ali Ghazanfar, MBChB^2^; Mohamed Bekheit, MD^3^; René Adam^4^
---

^1^School of Architecture, Computing and Engineering, University of East London, London E16 2RD, United Kingdom. ^2^NHS Grampian, Department of General Surgery, Aberdeen Royal Infirmary, Aberdeen AB25 2ZA, United Kingdom. ^3^East Lancashire Hospitals NHS Trust, Department of Hepatopancreaticobiliary Surgery, Burnley, Lancashire, United Kingdom. ^4^Centre Hépato-Biliaire, AP-HP Hôpital Universitaire Paul Brousse, Université Paris-Saclay, Villejuif, France.

\*Corresponding author: Farrah Aftab, MSc — f.aftab@uel.ac.uk

> **Draft status for supervisor review.** This version replaces the earlier binary-CART TNM analysis. The Results, Abstract, Discussion and Conclusions are rewritten from the final v7 analysis (notebook `LiverMets_final_reproducible`, outputs in `results/final_v7/`). Items marked **[TO COMPLETE]** need outputs that have not yet been generated. See the cover note for the full list of changes and decisions.

# Abstract

**Background:** Colorectal liver metastases (CRLM) remain a leading cause of colorectal cancer death. Prognostic tools developed in single-centre cohorts may not reflect contemporary practice, and binary classification of survival status discards information about timing. We developed and temporally validated a survival-based prognostic model and three prognostic groups for patients undergoing hepatic resection for CRLM.

**Methods:** Retrospective analysis of the LiverMetSurvey international registry (29,565 patients, 63 countries, 242 centres). The analytic cohort comprised 17,262 patients who underwent hepatectomy with complete TNM staging. Time origin was the first hepatectomy. Development used patients operated in 2009 or earlier (n = 8,463); temporal validation used patients operated in 2010 or later (n = 8,799). A stratified Cox model (strata: sex, synchronous presentation and M-stage) was fitted to TNM stage, age, interval from primary diagnosis to liver-metastasis diagnosis, and number and size of liver metastases. Prognostic groups were the training-era tertiles of predicted 5-year survival. Performance was assessed by Harrell's C-index, time-dependent AUC, Brier score, calibration and Kaplan–Meier separation. Recurrence-free survival (RFS) was a secondary outcome. Fong and Nordlinger-type scores were compared on identical subsets.

**Results:** In the validation cohort, the Favourable (n = 2,662), Intermediate (n = 2,824) and Adverse (n = 3,313) groups had median overall survival of 7.38 years, 4.44 years and 3.18 years (log-rank p = 2 × 10⁻⁵²). The model achieved a validation C-index of 0.622 (95% CI 0.608–0.637), time-dependent AUC of 0.675 at 5 years and integrated Brier score of 0.075 over 1–7 years. Predicted 5-year survival was lower than observed (40.8% vs 46.6%; observed/expected 1.14), indicating under-prediction of survival in the validation era. The C-index was 0.639 in the Fong-score subset and 0.630 in the Nordlinger-type subset, versus 0.591 and 0.583 for the comparator scores. A model without metastasis count and size gave a C-index of 0.591. Median RFS was 2.03 years (95% CI 1.98–2.09), ranging from 1.69 to 2.03 years across handling rules for undated recurrences.

**Conclusions:** A stratified Cox model using routinely recorded TNM, clinical and operative variables separated patients into three prognostic groups that remained distinct in temporal validation. Discrimination was modest, and the model under-predicted survival in more recent patients, so absolute survival estimates should not be quoted without recalibration. Prospective validation in contemporary cohorts is required before clinical use.

**Keywords:** colorectal liver metastases; prognostic groups; Cox regression; survival analysis; temporal validation; calibration; surgical oncology

# Introduction

Colorectal cancer accounts for about 10% of global cancer diagnoses, and hepatic metastases develop in roughly half of affected patients [CITATION NEEDED]. Surgical resection, with or without perioperative chemotherapy, is the principal opportunity for cure, yet long-term outcomes remain hard to predict for an individual patient. Established scores such as the Fong Clinical Risk Score were derived from single-centre or limited multicentre cohorts more than two decades ago [1], and their threshold-based summation may not capture interactions between tumour biology variables [CITATION NEEDED].

Some machine learning approaches for CRLM model a binary outcome, alive or dead, which discards time-to-event information and the censoring of patients with differing follow-up [CITATION NEEDED]. Survival methods that use the full time-to-event structure are better suited to prognostic stratification and to communicating expected survival [4,5].

The LiverMetSurvey registry provides international, internationally standardised data on patients resected for CRLM, with TNM staging and dates available for analysis. In this study we aimed to: (1) define a survival-based prognostic model using routinely recorded variables fixed before validation; (2) derive three prognostic groups from that model using training-era cut-points only; (3) evaluate discrimination, calibration and separation in a later temporal validation cohort; (4) assess recurrence-free survival and the sensitivity of findings to date conventions, death-date handling and omission of metastasis count and size; and (5) compare performance with established scores on identical patients.

# Methods

## Study design and data source

This was a retrospective cohort analysis of the LiverMetSurvey registry, a prospectively maintained, web-based database of patients with colorectal liver metastases established in 2004. The registry comprises 29,565 patients from 63 countries and 242 contributing centres, with standardised data collection and site-level quality assurance. The study followed the STROBE guidelines [9]. Analyses were performed on the raw registry workbooks (Part 1 and Part 2) using a fully scripted pipeline; the workbook checksums were recorded to confirm that the source files were unchanged.

## Study population

Eligibility required: registry inclusion; hepatic resection recorded (`LE1HEPATECTYN_F1 = Yes`); a usable operation year and month; a vital status and a last-news date on or after the operation date; and either a positive follow-up time or death. Of 29,565 patients, 26,094 met these criteria (Table 1 flow in Results). Patients with incomplete T, N or M staging were excluded from the modelling cohort, leaving 17,262 patients.

Operation dates recorded to year and month only were assigned the 15th of the month (primary rule). The first-day and last-day-of-month rules were used as sensitivity analyses.

## Variables and definitions

* **Outcome:** overall survival (OS) from first hepatectomy to death from any cause, or to last-news date. Follow-up was capped at 15 years. All last-news dates in the modelling cohort fell on or before 4 July 2020 (checked).
* **TNM stage:** T1–2, T3, T4; N0, N1, N2; M0, M1, using the AJCC staging categories [10,11] with sub-categories collapsed. T1–2 is the reference for T; N0 for N; M0 for M.
* **Predictors:** age at operation (per 10 years); interval from diagnosis of the primary to diagnosis of liver metastases (per 12 months; set to 0 for synchronous presentation, and missing when the liver metastasis diagnosis followed the operation); number of liver metastases (continuous, 1–50); recorded liver metastasis size in mm (per 10 mm); sex; synchronous presentation. Missing metastasis count and size were handled with missing-indicator variables and training-era medians.
* **Death:** status *Deceased* in the registry. Patients who died on the operation date (same-day deaths) were assigned half a day of follow-up, and this convention was tested as a sensitivity analysis.
* **Recurrence-free survival (RFS):** time from hepatectomy to the earliest dated liver or extrahepatic recurrence after operation, or to death. Undated recurrences (count > 0 with no date) were censored in the primary analysis and handled in sensitivity analyses. Recurrences dated before the operation were excluded.

## Model development

Patients operated in 2009 or earlier formed the development (training) cohort; patients operated in 2010 or later formed the temporal validation cohort. Validation data were used only to evaluate fixed models, cut-points and rules.

Three candidate models were compared on identical patients:

* **M1:** stratified by sex and synchronous presentation; M-stage as a covariate.
* **M2a:** stratified by sex, synchronous presentation and M-stage; M-stage removed as a covariate.
* **M2b:** as M1, with a time-varying M-stage effect split at 2 years.

The selection rule was applied to training-only data: choose the simplest candidate whose Schoenfeld tests [6] for all constant terms have p > 0.05. Model discrimination was not used to select the model. M1 failed the test for M-stage (p = 0.031); M2a passed for all constant terms and was selected. The time-varying M-stage effect in M2b was not significant (p = 0.21).

Baseline hazards were estimated by a piecewise Breslow method [7] from training patients only, so that predicted survival could be obtained at any time. Predicted 5-year survival was the basis for the prognostic groups.

## Prognostic groups

Patients were assigned to groups by their predicted 5-year survival, using tertile cut-points estimated in the training cohort and applied unchanged to the validation cohort:

* Favourable: predicted 5-year survival ≥ 0.4756
* Intermediate: 0.3793 ≤ predicted 5-year survival < 0.4756
* Adverse: predicted 5-year survival < 0.3793

Group separation was tested by log-rank tests and ordinal C-index. Stability of the group assignment was assessed by bootstrap refitting of the model (100 resamples, Cohen's κ against the primary assignment).

## Performance and calibration

Harrell's C-index [3] was calculated in each cohort with a 300-resample bootstrap confidence interval in validation. Time-dependent AUC at 1, 3 and 5 years, Brier scores at 1, 3 and 5 years, and the integrated Brier score over 1–7 years were computed in validation using training-based predictions [8]. Calibration was assessed by comparing mean predicted 5-year survival with Kaplan–Meier 5-year survival [4] (observed/expected ratio), by a calibration slope, by validation decile of predicted survival, and by operation period. Because few patients in later periods have 5 years of follow-up, decile and period estimates were flagged as sparse when fewer than 50 patients had 5-year follow-up.

## Sensitivity analyses

* **Partial operation dates:** first-day and month-end rules.
* **Same-day deaths:** half-day (primary), one day, quarter day, exclusion, and handling of same-day deaths without an explicit death flag (exclusion or censoring at half a day).
* **Pre-operative-only model:** metastasis count and size removed, fitted in the M1 structure and in the selected M2a structure.
* **Carcinoembryonic antigen (CEA):** complete-case analysis and multiple imputation (10 draws, development outcome included, validation predictors only).
* **Undated recurrences:** four RFS analyses (primary; undated as events at last contact; undated as events at mid-interval; undated patients excluded).
* **Recent baseline:** recalibration of the baseline hazard using only 2005–2009 training patients, with coefficients unchanged. This was a sensitivity analysis only and was not used for the primary results.

## Comparison with established scores

The Fong Clinical Risk Score [1] and a Nordlinger-type score [2] were calculated from variables available in the registry and compared with the selected model on identical patients (Fong subset: patients with CEA recorded; Nordlinger-type subset: patients with age, T, N and interval data). The Fong score was computed from its five items (node-positive, interval < 12 months, > 1 metastasis, size > 50 mm, CEA > 200 ng/mL). The Nordlinger-type score is an approximation built from four items available here (age ≥ 60, T4, node-positive, interval < 12 months) and is not the published model. Both are therefore comparisons with approximations of the published scores.

## Data handling, reproducibility and software

All analyses were run in a single Python notebook that reads the raw workbooks, builds the cohort, fits all models and writes every table and figure. Random seed was 42. Software: pandas 2.3.3, NumPy 2.5.3, lifelines 0.30.3, scikit-survival 0.28.0, scikit-learn 1.9.1, pyarrow 26.0.0 and python-calamine 0.8.3, on Python 3.13.16. The notebook was executed end-to-end; the reproduction check reproduced all key values of the previous validated analysis. No patient-level data are published.

The analysis was not optimised for the C-index. The M-stage model was selected by the pre-specified PH rule, and phenotype cut-points were fixed in the training cohort.

# Results

## Study population and flow

Of 29,565 registry patients, 28,979 had CINCLUSION = Yes, 26,677 had a recorded hepatectomy, 26,592 had an operation date (year and month), 26,271 had a recorded status and last-news date, 26,186 had consistent chronology and 26,094 had positive follow-up or death. Of these, 17,262 had complete TNM staging and formed the analytic cohort. Development contained 8,463 patients (4,675 deaths) and validation 8,799 patients (1,916 deaths).

**[TO COMPLETE]** Figure 1 (STROBE flow diagram) must be redrawn from `results/final_v7/F01_flow_by_day_convention.csv`. The earlier diagram shows the superseded 14,759-patient flow and must not be used.

**[TO COMPLETE] Table 1.** Baseline characteristics of the analytic cohort (17,262) by development and validation period. These have not yet been generated from the v7 cohort. The earlier Table 1 (n = 14,759) must not be used.

## Model selection and performance

The M-stage candidates gave near-identical performance on identical patients (Table 2). M1 violated the proportional hazards assumption for M-stage (p = 0.031), so M2a was selected by the pre-specified rule. Time-dependent discrimination in validation was 0.639, 0.653 and 0.675 at 1, 3 and 5 years. Brier scores were 0.060, 0.101 and 0.065 at 1, 3 and 5 years, and the integrated Brier score over 1–7 years was 0.075.

**Table 2. Candidate models, identical patients (validation n = 8,799).**

| Model | Training C | Validation C (95% CI) | 5-y observed S | 5-y mean predicted S | O/E (5-y) | Calibration slope |
|---|---|---|---|---|---|---|
| M1: stratified sex × synchronous; M-stage covariate | 0.595 | 0.622 (0.606–0.636) | 0.466 | 0.409 | 1.141 | 1.091 |
| **M2a: stratified sex × synchronous × M-stage (selected)** | **0.595** | **0.622 (0.608–0.637)** | **0.466** | **0.408** | **1.142** | **1.074** |
| M2b: time-varying M-stage | 0.595 | 0.622 (0.609–0.637) | 0.466 | 0.409 | 1.140 | 1.091 |

## Prognostic groups

The Favourable, Intermediate and Adverse groups were clearly separated in both cohorts (Table 3; Figure 2 and Figure 3). In validation, the log-rank p-value was 2.0 × 10⁻⁵² and the ordinal C-index was 0.603. Bootstrap refitting gave a median κ of 0.832 (95% range 0.778–0.894), indicating stable group assignment.

**Table 3. Prognostic groups (M2a) with training-only cut-points.**

| Group | Predicted 5-y survival | Development n | Validation n | Validation deaths | Median OS, years (95% CI) | 5-y OS (KM) | Mean predicted 5-y S (validation) |
|---|---|---|---|---|---|---|---|
| Favourable | ≥ 0.4756 | 2,821 | 2,662 | 383 | 7.38 (6.14–NE) | 0.629 | 0.532 |
| Intermediate | 0.3793–0.4755 | 2,821 | 2,824 | 598 | 4.44 (4.14–4.88) | 0.454 | 0.428 |
| Adverse | < 0.3793 | 2,821 | 3,313 | 935 | 3.18 (2.97–3.38) | 0.343 | 0.291 |

Note: development n is shown per group from the tertiles of the training cohort; the group counts in the notebook output (`F06`) are the authoritative values.

![](figures/COX_01_OS_by_M2a_group_validation.png)

**Figure 2.** Overall survival by prognostic group in the validation cohort (operated 2010 or later).

![](figures/COX_02_RFS_by_M2a_group_validation.png)

**Figure 3.** Recurrence-free survival by prognostic group in the validation cohort (primary RFS definition).

## Calibration

Predicted 5-year survival was lower than observed in validation (40.8% vs 46.6%; O/E 1.14; calibration slope 1.07). The under-prediction was present in most validation deciles (Figure 4). In the top decile, observed 5-year survival was 75.8% against 58.0% predicted, and this decile had 80 patients with 5 years of follow-up. The lower deciles had fewer than 50 patients with 5-year follow-up, so their observed values are imprecise.

By operation period, the observed/expected ratio was 0.96 for 1990–2004, 1.03 for 2005–2009 (training), 1.09 for 2010–2012 and 1.23 for 2013–2015 (Figure 5). The 2013–2015 estimate rests on 109 patients with 5 years of follow-up. No patient operated in 2016 or later has 5 years of follow-up, so calibration in that period cannot be assessed.

Re-estimating the baseline hazard from 2005–2009 patients only reduced the validation O/E to 1.115 (C-index 0.620). Phenotype agreement with the primary groups was 92%, so this recalibration did not change the groups materially, but it also did not remove the calibration gap. The primary results are therefore not recalibrated.

![](figures/COX_03_calibration_by_decile_validation.png)

**Figure 4.** Calibration by validation decile of predicted 5-year survival. Open markers are deciles with fewer than 50 patients with 5-year follow-up.

![](figures/COX_04_O_over_E_by_period.png)

**Figure 5.** Observed/expected 5-year survival by operation period.

## Sensitivity analyses

**Table 4. Sensitivity analyses (validation unless stated).**

| Analysis | Result |
|---|---|
| Partial date rule: first day of month | Cohort 17,265; C 0.621; phenotype agreement 99.7% (κ 0.996) |
| Partial date rule: month-end | Cohort 17,262; C 0.622; phenotype agreement 99.98% (κ 1.00) |
| Same-day deaths: half day, one day, quarter day (primary) | C 0.622; identical phenotypes at reported precision |
| Same-day deaths: all 13 in the cohort excluded | Cohort 17,249; C 0.622; agreement 99.6% (κ 0.994) |
| Same-day deaths without death flag (7 patients) excluded | Cohort 17,255; C 0.623; agreement 99.6% (κ 0.994) |
| Same-day deaths without death flag censored at half a day | C 0.623; agreement 99.6% (κ 0.994) |
| Pre-operative-only model (no metastasis count or size), M1 structure | C 0.591 (0.573–0.606); O/E 1.13; calibration slope 1.36; agreement 70% (κ 0.55) |
| Pre-operative-only model, selected M2a structure | C 0.591 (0.575–0.604); O/E 1.13; calibration slope 1.31; agreement 72% (κ 0.58) |
| CEA, complete case | HR 1.16 per log unit (95% CI 1.13–1.19); C 0.628 → 0.648 |
| CEA, multiple imputation (10 draws) | HR 1.15 (95% CI 1.13–1.18); C 0.622 → 0.637 |

**Same-day deaths.** Nineteen registry patients died on the day of operation, and 13 of them are in the analytic cohort. Their operation dates are complete, and each has one follow-up form. Six of the 13 carry an explicit death flag (`DEATHKYN_F = Yes`), and seven do not. The death flag was also missing for deaths at other times: among deceased patients in the analytic cohort, it read Yes for 50% at 1–30 days, 73% at 31–365 days, 82% at 1–5 years and 70% beyond 5 years. The seven unflagged same-day deaths are therefore not supported by an explicit flag, but excluding or censoring them changes the C-index by 0.001 and the group assignment for about 0.4% of patients.

**Dates.** Using the first day of the month instead of the 15th changes 0.3% of group assignments. Month-end gives agreement of 99.98%.

## Pre-operative prognostication

Without metastasis count and size, the model discriminated less well (C 0.591 vs 0.622). About 70% of validation patients were assigned to the same group as the full model (κ 0.55–0.58). Operative metastasis count and size therefore add discrimination, but they are recorded at or after the operation, so their use in pre-operative decision-making is limited (see Limitations).

## Recurrence-free survival

Median RFS was 2.03 years (95% CI 1.98–2.09) with 39.3% and 27.6% recurrence-free at 3 and 5 years. Sensitivity analyses gave medians of 1.93 years (undated recurrences as events at last contact), 1.69 years (undated recurrences as events at mid-interval) and 1.84 years (undated recurrences excluded). In the cohort, 5,324 patients had a dated post-operative recurrence and 1,676 had a recurrence recorded without a date. Undated recurrences had different follow-up and death rates from other patients but a similar predicted 5-year survival (0.414 vs 0.407 and 0.420). RFS is a secondary outcome.

## Comparison with established scores

**Table 5. Validation C-index on identical patients.**

| Subset | n | Deaths | Selected model | Comparator | O/E (5-y) |
|---|---|---|---|---|---|
| Fong subset (CEA recorded) | 3,642 | 914 | 0.639 | Fong approximation 0.591 | 1.19 |
| Nordlinger-type subset | 6,137 | 1,396 | 0.630 | Nordlinger-type approximation 0.583 | 1.16 |

The comparator scores are approximations built from registry variables, not the published models. The selected model discriminated better in both subsets, but the comparison should be read as indicative.

## Treatment comparison

**[NOT RE-ANALYSED IN v7]** The earlier propensity-score treatment comparison was not repeated in the final analysis. Treatment-related conclusions have therefore been removed from this version. They must not be reinstated until the matched analysis has been re-run on the v7 cohort and checked for covariate balance, with the matching model and treatment definitions stated.

# Discussion

In this international registry, a stratified Cox model using TNM stage, age, interval from diagnosis to resection, and the number and size of liver metastases separated patients into three prognostic groups whose survival remained distinct in a later temporal validation cohort. The model discriminated modestly (C-index 0.622), and it was comparable with or better than the Fong and Nordlinger-type approximations in their respective subsets.

The model uses a survival framework, so each patient receives a predicted survival curve rather than a binary risk class, and predictions can be stated at 1, 3 and 5 years. Stability of the group assignments was good (κ 0.83), and the groups did not depend on tuning against the validation cohort.

The model under-predicted survival in the validation era, with observed 5-year survival of 46.6% against 40.8% predicted. The gap was largest in the most favourable decile. This is consistent with improving survival in more recent patients, but the evidence is limited: later periods have few patients with 5 years of follow-up, and recalibration from recent data did not close the gap. Absolute survival estimates from the model should therefore not be used in consultation until recalibrated on contemporary data.

Recurrence-free survival was analysed as a secondary outcome. Its median ranged from 1.69 to 2.03 years depending on how undated recurrences were handled, so RFS conclusions depend on that assumption.

Metastasis count and size improved discrimination, but they are recorded with the operation. The pre-operative-only model is a sensitivity analysis and is not a pre-operative tool.

# Limitations

1. **Calibration and absolute survival.** The model under-predicts 5-year survival in the validation era (O/E 1.14). Recalibration using recent data reduced but did not remove the gap. The groups rank patients consistently, but their absolute survival values should be interpreted with caution.
2. **Limited late follow-up.** Patients operated from 2013 onward have few 5-year observations (109 for 2013–2015; none for 2016 onward). Period-specific calibration is provisional.
3. **Predictor timing.** Metastasis count and size are assumed to be known at the operation. Operative-form counts agreed with pre-operative counts for 13,130 of 20,553 patients, but 3,179 resected counts exceeded the pre-operative count. The pre-operative-only model shows how much discrimination depends on these variables.
4. **Death data.** Among 11,594 deceased patients, 3,074 have no death flag, so survival times for these patients rest on the last-news date. Seven unflagged same-day deaths are included in the primary analysis; excluding them made no material difference.
5. **Undated recurrences.** 1,676 recurrences have no date, so RFS is secondary and depends on handling rules.
6. **Comparators.** The Fong and Nordlinger-type scores are approximations built from registry variables. They do not reproduce the published models.
7. **Treatment effects.** Treatment comparisons are not included in this version and have not been re-analysed in the final pipeline.
8. **Missing covariates.** CEA was missing for about one-third of patients. Complete-case and multiple-imputation results were similar, but CEA's contribution is small (C-index increase of about 0.02).
9. **Registry and design.** Validation is temporal within a single registry. No external validation has been performed. Molecular markers (KRAS, BRAF, microsatellite instability) and performance status were not present in the extract analysed.

# Conclusions

In an international registry of patients undergoing hepatic resection for CRLM, a stratified Cox model based on TNM stage, clinical and operative variables produced three prognostic groups with clearly different survival. The groups were stable and remained distinct in temporal validation, with modest discrimination. The model under-predicted survival in more recent patients, so absolute survival estimates require recalibration on contemporary data. Prospective validation is needed before clinical use.

# Declarations

**Funding:** No specific funding was received for this study.

**Conflicts of interest:** The authors declare that they have no competing interests relevant to this work.

**Author contributions:** F.A. conceived and designed the study, performed the statistical analyses, interpreted the data, and drafted the manuscript. M.A.G. supervised the study, contributed to the study design and interpretation of the findings, and critically revised the manuscript. M.B. provided clinical expertise, contributed to the interpretation of the clinical findings, and critically reviewed the manuscript. All authors read and approved the final manuscript. **[TO CONFIRM by authors]** Contribution statements must be checked against the revised work.

**Data availability:** The data analysed in this study were obtained from the LiverMetSurvey international registry. Access is governed by the LiverMetSurvey collaboration and is subject to institutional approval, data-sharing agreements and applicable ethical requirements. Requests should be directed to the registry coordinating centre. The analysis code is available at https://github.com/FarrahAftab/LiverMets.

**Ethics approval:** The study involved secondary analysis of anonymised data from the LiverMetSurvey registry. The registry contains de-identified clinical data collected under local ethical and regulatory approvals at participating centres. Individual informed consent was waived where permitted by applicable regulations. Institutional review was conducted in accordance with University of East London research governance requirements. **[TO CONFIRM]** The ethics statement should be checked against the approvals held for this analysis.

# References

1. Fong Y, Fortner J, Sun RL, Brennan MF, Blumgart LH. Clinical score for predicting recurrence after hepatic resection for metastatic colorectal cancer: analysis of 1001 consecutive cases. Ann Surg. 1999;230(3):309–318.
2. Nordlinger B, Guiguet M, Vaillant JC, et al. Surgical resection of colorectal carcinoma metastases to the liver. A prognostic scoring system to improve case selection. Cancer. 1996;77(7):1254–1262.
3. Harrell FE Jr. Regression Modeling Strategies. 2nd ed. Springer; 2015.
4. Kaplan EL, Meier P. Nonparametric estimation from incomplete observations. J Am Stat Assoc. 1958;53(282):457–481.
5. Cox DR. Regression models and life-tables. J R Stat Soc B. 1972;34(2):187–220.
6. Schoenfeld D. Partial residuals for the proportional hazards regression model. Biometrika. 1982;69(1):239–241.
7. Breslow NE. Discussion of "Regression models and life-tables" by D. R. Cox. J R Stat Soc B. 1972;34(2):216–217.
8. Graf E, Schmoor C, Sauerbrei W, Schumacher M. Assessment and comparison of prognostic classification schemes for survival data. Stat Med. 1999;18(17–18):2529–2545.
9. von Elm E, Altman DG, Egger M, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. PLoS Med. 2007;4(10):e296.
10. Edge SB, Compton CC. The American Joint Committee on Cancer: the 7th edition of the AJCC cancer staging manual and the future of TNM. Ann Surg Oncol. 2010;17(6):1471–1474.
11. Amin MB, Greene FL, Edge SB, et al. The 8th edition AJCC cancer staging manual: continuing to build a bridge from a population-based to a more "personalized" approach to cancer staging. CA Cancer J Clin. 2017;67(2):93–99.

**[TO CHECK]** The reference list was rebuilt for the revised text. Only references cited in the revised manuscript are listed. The 41 references in the earlier draft that supported the superseded CART, treatment and adjuvant-chemotherapy discussion have been removed and should be restored only if those sections are reinstated. Citation details for references 1–11 must be verified against the originals before submission. Three statements are marked [CITATION NEEDED] in the introduction.

# Figure and table index

| Item | Status |
|---|---|
| Figure 1 STROBE flow diagram | **[TO COMPLETE]** redraw from v7 flow (`F01`) |
| Figure 2 OS by group, validation | Available (`COX_01`) |
| Figure 3 RFS by group, validation | Available (`COX_02`) |
| Figure 4 Calibration by decile | Available (`COX_03`) |
| Figure 5 O/E by period | Available (`COX_04`) |
| Table 1 Baseline characteristics | **[TO COMPLETE]** not generated from v7 |
| Table 2 Candidate models | Available (`F02`) |
| Table 3 Prognostic groups | Available (`F06`) |
| Table 4 Sensitivity analyses | Available (`F10`, `F13`, `F14`, `F19`, `F23`) |
| Table 5 Benchmarks | Available (`F16`) |
| Supplementary Table S1 Included vs excluded | **[TO COMPLETE]** not generated from v7 |
| Earlier CART figures (Figures 2, 3, 5–8, tree diagram) and Tables 2, 4–6 | Superseded; removed |
