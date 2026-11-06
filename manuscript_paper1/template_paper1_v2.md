---
title: "Prognostic Survival Prediction and Risk Stratification in Colorectal Liver Metastases: Development and Temporal Validation in an International Registry"
author:
  - Farrah Aftab, MSc^1,*^; Mustansar Ali Ghazanfar, PhD^1^; Mudassar Ali Ghazanfar, MBChB^2^; Mohamed Bekheit, MD^3^; René Adam^4^
---

^1^School of Architecture, Computing and Engineering, University of East London, London E16 2RD, United Kingdom. ^2^NHS Grampian, Department of General Surgery, Aberdeen Royal Infirmary, Aberdeen AB25 2ZA, United Kingdom. ^3^East Lancashire Hospitals NHS Trust, Department of Hepatopancreaticobiliary Surgery, Burnley, Lancashire, United Kingdom. ^4^Centre Hépato-Biliaire, AP-HP Hôpital Universitaire Paul Brousse, Université Paris-Saclay, Villejuif, France.

\*Corresponding author: Farrah Aftab, MSc — f.aftab@uel.ac.uk

> **Draft for supervisor review.** Items marked **[TO CONFIRM]**, **[TO VERIFY]** or **[CITATION NEEDED]** are unresolved and are listed separately in the supervisor-confirmation note.

# Abstract

**Background:** Colorectal liver metastases (CRLM) are a major cause of colorectal cancer death. Established prognostic scores were mostly derived from older, single-centre cohorts, and their performance in contemporary practice is uncertain.

**Methods:** Retrospective analysis of the LiverMetSurvey registry. The analytic cohort comprised 17,262 patients undergoing hepatectomy with complete TNM staging, divided by operation year into a development cohort (≤2009; n = 8,463) and a temporal validation cohort (≥2010; n = 8,799). A stratified Cox model (strata: sex, synchronous presentation and M-stage) used TNM stage, age, interval to liver metastasis, and number and size of metastases. Three prognostic groups were defined by training-era tertiles of predicted 5-year survival and applied unchanged to validation patients.

**Results:** Validation median overall survival was 7.38, 4.44 and 3.18 years in the Favourable (n = 2,662), Intermediate (n = 2,824) and Adverse (n = 3,313) groups (log-rank p = 2 × 10⁻⁵²). The C-index was 0.622 (95% CI 0.608–0.636). Predicted 5-year survival was 40.8% against 46.6% observed. Without TNM stage the C-index was 0.599 in the same patients.

**Conclusions:** A stratified Cox model using routinely recorded variables separated three prognostic groups that remained distinct in temporal validation. Discrimination was modest and survival was under-predicted in recent patients, so absolute predictions need recalibration before clinical use.

**Keywords:** colorectal liver metastases; prognostic model; survival analysis; temporal validation; calibration

# Introduction

Hepatic resection is the main opportunity for long-term survival in patients with colorectal liver metastases, yet outcomes vary widely and are hard to predict for an individual patient [CITATION NEEDED: incidence of liver metastases]. Prognostic information informs patient selection, follow-up and trial design.

The Fong Clinical Risk Score, derived from 1,001 consecutive resections at a single centre, is the most widely used benchmark [1]. It counts five preoperative criteria and predates contemporary systemic therapy. The GAME score adds KRAS status to clinicopathological variables and separated patients with 5-year overall survival of 11% from 73% in its derivation cohort [2] [TO VERIFY: survival figures against the original article]. A 2026 systematic review and meta-analysis of liver-resection prognostic scores reported limited performance and heterogeneous reporting [3]. In a nationwide Dutch cohort, the Fong score had a C-index of 0.577 and GAME 0.596 [4].

Two gaps remain. Many models report discrimination without calibration, so absolute predictions cannot be checked. Few have been validated in a later cohort using a model fixed before validation. We therefore aimed to (1) develop a stratified Cox survival model from routinely recorded variables; (2) derive three prognostic groups from training-era predicted 5-year survival and apply them unchanged to later patients; (3) assess discrimination, calibration and separation in temporal validation; and (4) test the findings against date conventions, duplicate records, the omission of metastasis count and size, and a model without TNM stage. We report the model under the TRIPOD+AI statement [5], which applies to regression as well as machine-learning models, and assess risk of bias with PROBAST+AI [6]. Treatment-associated survival is not analysed here.

# Methods

## Study design and reporting

This was a retrospective cohort study of the LiverMetSurvey registry, a prospectively maintained web-based database of patients with colorectal liver metastases. The study followed STROBE [7] and TRIPOD+AI [5]. The completed checklist is provided in Supplementary Material S9. Source workbooks were checksummed (SHA-256) before analysis, and the analysis was run end to end from a single scripted notebook.

## Participants

Eligibility required a recorded hepatectomy, an operation year and month, a vital status with a last-news date on or after operation, and either positive follow-up or death. Of 29,565 registry records, 26,094 met these criteria. Of these, 8,832 (33.8%) had incomplete TNM staging and were excluded, leaving 17,262 patients (Figure 1). Missing components were recorded as "not determined" (ND) or blank; their patterns and the characteristics of excluded patients are in Supplementary Tables S1–S2.

Operation dates recorded to year and month only were set to the 15th of the month; the first and last day of the month were used as sensitivity analyses.

**Registry description [TO CONFIRM].** The original manuscript described the registry as spanning 63 countries and 242 contributing centres. The analysis extract contains 54 country codes and 288 site codes, of which 259 sites contain eligible patients. The reconciliation with the registry coordinators is outstanding; the figures reported here are the extract's.

## Outcomes and predictors

The primary outcome was overall survival from hepatectomy to death from any cause or to the last-news date, with follow-up capped at 15 years. No deaths in the analytic cohort occurred after 4 July 2020. Recurrence-free survival (RFS) was a secondary outcome: time to the earliest dated recurrence after operation, or to death. Undated recurrences were censored in the primary analysis and handled by three alternative rules.

Candidate predictors were TNM stage (T1–2, T3, T4; N0, N1, N2; M0, M1; AJCC categories [8,9] with subcategories collapsed), age at operation (per 10 years), sex, synchronous presentation, interval from primary diagnosis to liver metastasis (per 12 months; 0 for synchronous; missing when the date was unknown, negative or after operation), number of liver metastases (per additional lesion) and largest recorded metastasis (per 10 mm). Missing interval, count and size were handled with indicator variables and training-era medians; no multiple imputation was used for the primary model.

**Predictor timing [TO CONFIRM].** The model assumes that count and size are known at operation. The registry data dictionary was not available, and the time at which count and size were recorded relative to any preoperative treatment cannot be confirmed from the data. Pre-operative and resected counts agreed for 62% of the 14,189 patients with both recorded (Supplementary Table S2). The clinical implications are discussed in the Limitations.

## Data quality, duplicate records and sensitivity analyses

The registry has no patient-level identifier. Records were screened for duplicates on all analysis columns together with country, site and patient number. Twenty-three identical-content pairs (46 records) were found, of which 16 met a probable-duplicate rule (shared birth and operation dates, at least 20 non-blank fields). All records were retained in the primary analysis. Probable duplicates and a broader rule (later records sharing birth date, operation date and sex) were removed only in sensitivity analyses (Supplementary Table S3). Nothing was permanently removed, pending registry confirmation.

Other sensitivity analyses are listed in Table S5: date conventions; same-day deaths assigned half a day, one day or a quarter day, or excluded, with and without the death flag; a pre-operative-only model without count and size; complete-case and multiple-imputation analyses of carcinoembryonic antigen (CEA); RFS handling rules; and a baseline hazard re-estimated from 2005–2009 patients with coefficients fixed.

## Model development

Patients operated in 2009 or earlier formed the development cohort, and those operated in 2010 or later the temporal validation cohort. Validation data were used only to evaluate fixed models, cut-points and rules. No model was selected on the basis of its validation C-index.

Three candidate models were compared on identical patients (Supplementary Table S4): M1, stratified by sex and synchrony with M-stage as a covariate; M2a, stratified by sex, synchrony and M-stage; and M2b, as M1 with a time-varying M-stage effect split at 2 years. Before validation results were used, a rule was fixed: choose the simplest candidate whose Schoenfeld tests [10] for all constant terms give p > 0.05. M1 failed for M-stage (p = 0.031). M2a passed for all terms (smallest p = 0.18) and was selected. The time-varying M-stage effect in M2b was not significant (p = 0.21). The baseline hazard was estimated by a piecewise Breslow method [11] from training patients only.

The development cohort contains 4,675 deaths, which is ample for the 11 candidate terms in the selected model.

## Prognostic groups

Groups were defined by predicted 5-year survival, with cut-points at the training tertiles and applied unchanged to validation: Favourable ≥0.4756; Intermediate 0.3793 to <0.4756; Adverse <0.3793. Each group contains one third of the development cohort (n = 2,821). Separation was assessed by log-rank test. Stability of assignment was assessed by 100 bootstrap refits, comparing assignments with Cohen's κ.

## Performance, calibration and censoring

Harrell's C-index [12] was computed in each cohort, with 300-resample bootstrap intervals in validation. Time-dependent AUC and Brier scores were computed at 1, 3 and 5 years, and the integrated Brier score over 1–7 years [13]. Calibration was assessed by comparing mean predicted survival with Kaplan–Meier survival at each horizon (observed/expected ratio with bootstrap intervals), by a calibration slope, by validation decile and by operation period. Estimates with fewer than 50 patients followed up to 5 years were flagged as sparse.

Survival was estimated by Kaplan–Meier and Cox methods, which account for patients alive at last contact. Median follow-up by reverse Kaplan–Meier was 5.89 years (development) and 1.47 years (validation). Because validation follow-up is short, the number of patients evaluable at each horizon falls, and this is reported (Table 4).

## Comparison with established scores

The Fong score [1] and a Nordlinger-type score [14] were computed on identical patients. The Fong subset had CEA recorded; the Nordlinger-type subset had age, T, N and interval data. The Fong score was computed from its five published criteria (node-positive, disease-free interval <12 months, more than one tumour, CEA >200 ng/mL, largest tumour >5 cm). The Nordlinger-type score is an approximation built from four registry variables (age ≥60, T4, node-positive, interval <12 months) and is not the published model. GAME [2] was not reproduced because KRAS status is recorded for 2.3% of patients. The Tumour Burden Score was not reproduced because its published cut-offs differ between studies and the registry's size variable is the largest recorded lesion rather than a validated maximum diameter.

## Software

Analyses used pandas 2.3.3, NumPy 2.5.3, lifelines 0.30.3, scikit-survival 0.28.0, scikit-learn 1.9.1, pyarrow 26.0.0 and python-calamine 0.8.3 on Python 3.13.16, with random seed 42. All 15 code cells ran without errors. The primary outputs reproduce the previously validated analysis on all ten checked quantities (Supplementary S7). Analysis code is available at https://github.com/FarrahAftab/LiverMets.

# Results

## Study population

Of 29,565 registry records, 17,262 patients had eligible operations and complete TNM staging (Figure 1). The development cohort contained 8,463 patients (4,675 deaths) and the validation cohort 8,799 (1,916 deaths). Median age was 63.4 years (IQR 55.7–70.6), 61.8% were male and 57.8% had M1 disease. The validation cohort had more M1 disease and more patients with four or more metastases, and shorter follow-up (Table 1).

{{FIG1}}

{{FIG1_CAPTION}}

{{TABLE1}}

**Table 1.** Baseline characteristics of the analytic cohort by development (operated ≤2009) and temporal validation (operated ≥2010) periods. Deaths are shown as recorded and as events inside the 15-year window.

## Excluded patients

Exclusion for incomplete staging fell from 69.7% of operations in 1990–1999 to 24.4% in 2015–2020. Excluded patients were less often synchronous, had larger recorded metastases (median 35 vs 30 mm) and were operated earlier (median year 2007 vs 2010) (Supplementary Tables S1 and S2). Their 5-year survival was lower in the development era and higher in validation (Supplementary Table S2). The excluded group's pattern is hard to reconcile with missingness that depends only on recorded covariates; the direction of any selection bias cannot be determined from the registry.

## Model and discrimination

The selected model's coefficients are in Table 2. In validation the C-index was 0.622 (95% CI 0.608–0.636), against 0.622 for M1 and 0.622 for M2b. Time-dependent AUC was 0.639, 0.653 and 0.675 at 1, 3 and 5 years (Table 4). Discrimination is therefore modest. The model's contribution lies mainly in stratification and calibrated survival estimates.

{{TABLE2}}

**Table 2.** Coefficients of the selected model (M2a), fitted on the development cohort. Hazard ratios are within strata defined by sex, synchrony and M-stage. Source: `P1_model_coefficients.csv`.

## Proportional hazards

In M1 the M-stage term violated proportional hazards (p = 0.031). In M2a, which stratifies on M-stage, all constant terms satisfied the test (smallest p = 0.18). The time-varying M-stage model showed no significant change after 2 years (p = 0.21). The test was applied in the training cohort only; validation-cohort tests were not performed (Limitations).

## Prognostic groups

The groups separated overall survival clearly in both cohorts (Table 3; Figure 2). In validation, median overall survival was 7.38 years (95% CI 6.14 to not estimable) in the Favourable group, 4.44 years (4.14–4.88) in the Intermediate group and 3.18 years (2.97–3.38) in the Adverse group. Five-year Kaplan–Meier survival was 62.9%, 45.4% and 34.3%. The log-rank p-value was 2 × 10⁻⁵² in validation and 1.4 × 10⁻⁷⁷ in development. The ordinal C-index in validation was 0.603, and bootstrap κ for assignment stability was 0.83 (95% range 0.78–0.89).

{{TABLE3}}

**Table 3.** Prognostic groups (M2a) with training-only cut-points and validation outcomes. Source: `F06_phenotypes_counts_survival_calibration.csv`.

{{FIG2}}

**Figure 2.** Overall survival by prognostic group in the validation cohort (operated ≥2010). Cut-points were derived in the development cohort.

## Calibration

Predicted 5-year survival was 40.8% against 46.6% observed (observed/expected 1.14, bootstrap interval 1.09–1.20; calibration slope 1.07). Under-prediction was small at 1 year (O/E 1.01) and grew at 3 years (1.09, interval 1.06–1.12) and 5 years (Table 4). Under-prediction was present in nine of ten validation deciles, most markedly in the most favourable decile, the highest predicted survival (observed 75.8% against 58.0% predicted; Supplementary Figure S2). By operation period, O/E was 0.96 for 1990–2004, 1.03 for 2005–2009 (training), 1.09 for 2010–2012 and 1.23 for 2013–2015 (Supplementary Figure S3). The 2013–2015 estimate rests on 109 patients with 5 years of follow-up; calibration cannot be assessed for patients operated in 2016 or later.

Re-estimating the baseline hazard from 2005–2009 patients, with coefficients fixed, reduced the 5-year O/E to 1.12 and kept 92% of patients in their primary group (κ 0.88). The gap was reduced but not removed, so the primary model was not recalibrated.

{{TABLE4}}

**Table 4.** Performance and calibration by horizon in the validation cohort (n = 8,799). Evaluable patients are those with follow-up to the horizon or an event before it. Sources: `G01_horizon_feasibility_validation.csv`, `G03_calibration_precision_by_horizon.csv`, `F02b_selected_model_performance.csv`.

## Recurrence-free survival

Median RFS was 2.03 years (95% CI 1.98–2.09) in the primary analysis, with 39.3% and 27.6% recurrence-free at 3 and 5 years (Supplementary Figure S1). Alternative handling of undated recurrences gave medians of 1.93 years (undated recurrences treated as events at last contact), 1.69 years (mid-interval) and 1.84 years (undated recurrences excluded). In the cohort, 5,324 patients had a dated recurrence after operation, 585 had a recurrence dated before operation (excluded), and 1,676 had a recurrence recorded without a usable date; 41 recurrences dated after last contact were treated as undated.

## Sensitivity analyses

Across all sensitivity analyses (Supplementary Table S5), the validation C-index remained between 0.621 and 0.623 for the date-convention, same-day-death and duplicate analyses. The first-day convention changed 0.3% of group assignments, and assigning same-day deaths half a day, one day or a quarter day gave identical groups. Of the 13 same-day deaths in the cohort, seven lacked an explicit death flag; excluding or censoring them changed group assignment for about 0.4% of patients. Removing probable duplicates left the C-index at 0.622 and reassigned 33 patients (0.2%); the broader removal reassigned 138 (0.8%) and gave 5-year survival of 46.7% (Supplementary Table S3). Recalibration from 2005–2009 is reported in Results, Calibration.

## Comparison with established scores and a model without TNM

On identical validation patients, the selected model had a C-index of 0.639 in the Fong subset (n = 3,642; 914 deaths), against 0.591 for the Fong score, and 0.630 in the Nordlinger-type subset (n = 6,137; 1,396 deaths), against 0.583 for the Nordlinger-type approximation (Table 5). These approximations indicate relative performance on this registry; they do not establish the published models' performance.

{{TABLE5}}

**Table 5.** Validation C-index on identical patients in benchmark subsets. Source: `F16_identical_subset_comparison_calibration.csv`.

Without metastasis count and size (pre-operative-only model), the C-index fell to 0.591 (95% CI 0.573–0.606) in the M1 structure and 0.591 (0.575–0.604) in M2a (Supplementary Table S5). A model without TNM stage, using age, sex, synchrony, interval, count and size, gave 0.599 on the same 8,799 validation patients, a difference of 0.022 (95% CI 0.009–0.034) from the TNM model.

## Carcinoembryonic antigen

Among the 5,847 validation patients with CEA recorded, CEA was associated with mortality (hazard ratio 1.16 per log unit, 95% CI 1.13–1.19). Adding it raised the C-index from 0.628 to 0.648 (complete case) and from 0.622 to 0.637 (multiple imputation, 10 draws). CEA was missing for about one third of patients, so it was not in the primary model.

# Discussion

In this international registry, a stratified Cox model using TNM stage, age, interval to liver metastasis, and metastasis number and size separated three prognostic groups that remained distinct in temporal validation. Five-year survival was 62.9%, 45.4% and 34.3% in the Favourable, Intermediate and Adverse groups. Groups were fixed in training and assignment was stable on bootstrap refitting (κ 0.83).

Discrimination was modest (C-index 0.622). This should be read against the literature: a 2026 systematic review reported limited performance and heterogeneous reporting for liver-resection scores [3], and the nationwide Dutch validation found limited preoperative discrimination for the Fong score and GAME [4]. Our benchmark comparisons suggest better discrimination than registry approximations of the Fong and Nordlinger-type scores, but these are approximations and we do not claim superiority over published scores. GAME adds KRAS status and extrahepatic disease, which this registry does not record for most patients, so the two cannot be compared directly here. The model's contribution is therefore stratification with predicted survival at 1, 3 and 5 years, from routinely recorded variables, fixed before validation, with its calibration limits reported.

The model under-predicted survival in validation, most clearly at 5 years. This suggests the baseline hazard does not fully capture the longer-term outcomes of recent patients. Recalibration on contemporary data is needed before absolute estimates are quoted. Only 26% of validation patients could be evaluated at 5 years, so 1- and 3-year results are reported alongside.

Patients with incomplete staging (33.8% of eligible patients) differed in period, centre, synchrony and metastasis size, and their outcomes departed from a no-TNM model in opposite directions in the two eras. The analytic cohort is therefore the population in which TNM-based prediction is valid, not a representative sample of all resected patients.

An earlier analysis of this registry used binary classification and classification trees; the present survival model replaces it because it retains the timing and censoring of outcomes. A treatment-associated survival analysis is planned separately, because pre-operative chemotherapy must be defined by timing, the timing of metastasis count and size must be confirmed, and performance status, liver function and KRAS status must be available before any treatment comparison can be interpreted.

# Limitations

1. **Discrimination.** The C-index of 0.622 is modest; the groups rank patients but do not identify individual outcomes precisely.
2. **Calibration.** The model under-predicts survival in validation, most clearly at 5 years. The primary model was not recalibrated.
3. **Validation and follow-up.** Validation is temporal within one registry, with median follow-up of 1.47 years. No external validation was performed, and long-term calibration in recent patients cannot be assessed.
4. **Predictor timing [TO CONFIRM].** Count and size are assumed to be known at operation. Whether they were recorded before or after any preoperative treatment cannot be confirmed without the data dictionary. The timing question could change the interpretation of the model if these variables were recorded after treatment.
5. **Selection and missing data.** One third of the eligible population was excluded for incomplete staging, and excluded patients differ systematically. Missing-at-random cannot be verified. Interval, count and size are missing for many patients and handled by indicators, not imputation.
6. **Death and recurrence data.** In the full registry extract, 11,594 patients are recorded as deceased, of whom 3,074 lack an explicit death flag, so their survival times rest on the last-news date. The analytic cohort contains 6,601 recorded deaths. Recurrence dates are missing for 1,676 recurrences, so RFS is secondary.
7. **Duplicates.** Sixteen probable duplicate pairs and near-duplicate groups in the cohort await registry confirmation. Sensitivity analyses show no change to conclusions.
8. **Proportional hazards.** The tests were applied in the training cohort only. Validation-cohort tests and tests of time-varying effects for all covariates were not performed.
9. **Benchmarks.** The Fong and Nordlinger-type comparisons use registry approximations. GAME and the Tumour Burden Score could not be reproduced from registry variables.
10. **Missing covariates.** Performance status, comorbidity, liver function and KRAS status are not available for most patients, so the model cannot adjust for them.
11. **Registry description [TO CONFIRM].** The country and centre counts in the original manuscript must be reconciled with the extract.
12. **Generalisability.** The analytic cohort over-represents recent and synchronous operations (Supplementary Table S1).

# Conclusions

In an international registry, a stratified Cox model using routinely recorded TNM, clinical and operative variables produced three prognostic groups with clearly different survival. The groups were fixed in training and remained distinct in temporal validation, with modest discrimination and a calibration gap that increases with horizon. The model's value lies in transparent, survival-based stratification and explicit reporting of its limits. Absolute predictions require recalibration on contemporary data, and external validation is needed before clinical use.

# Declarations

**Funding:** No specific funding was received for this study.

**Conflicts of Interest:** The authors declare that they have no competing interests relevant to this work.

**Author Contributions:** F.A. conceived and designed the study, performed the statistical analyses, interpreted the data, and drafted the manuscript. M.A.G. supervised the study, contributed to the study design and interpretation of the findings, and critically revised the manuscript. M.B. provided clinical expertise, contributed to the interpretation of the clinical findings, and critically reviewed the manuscript. All authors read and approved the final manuscript. **[TO CONFIRM]** The original statement does not record a contribution for R. Adam. The authors must confirm each author's contribution before submission; no contribution has been added on their behalf.

**Data Availability:** The data were obtained from the LiverMetSurvey international registry. Access is governed by the LiverMetSurvey collaboration and is subject to institutional approval, data-sharing agreements and applicable ethical requirements. Requests should be directed to the registry coordinating centre. The analysis code is available at https://github.com/FarrahAftab/LiverMets.

**Ethics Approval:** The study followed the principles of the Declaration of Helsinki and used anonymised secondary registry data. Individual consent was waived where permitted by applicable regulation. Institutional review followed University of East London research governance. **[TO CONFIRM]** No approval reference number is recorded and it is not clear whether a formal approval or exemption was issued for this analysis. The reference or exemption wording must be supplied before submission. Do not submit until this is resolved.

# References

{{REFERENCES}}
