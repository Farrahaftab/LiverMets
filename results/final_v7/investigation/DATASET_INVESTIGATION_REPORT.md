# Dataset investigation: 29,565 registry records to the 17,262 analytic cohort

Scope: the two raw LiverMetSurvey workbooks, the v7 cohort rules (`notebooks/LiverMets_final_reproducible.py`, section 2), and the investigation scripts `notebooks/investigation_stage_a_v7.py`, `investigation_stage_b_v7.py` and `investigation_stage_c_v7.py`. All tables in this folder are aggregate. Patient-level working files stay outside the repository.

No change was made to the locked v7 analysis. The sensitivity analyses below are reported alongside it.

## 1. Dataset verification

| Check | Result | Table |
|---|---|---|
| Rows read from Part 1 (non-blank, header excluded) | 14,782 | F40 |
| Rows read from Part 2 (non-blank) | 14,783 | F40 |
| Rows combined | 29,565 (matches the report; no rows lost or added) | F40 |
| Duplicate Excel row sources | 0 | F40 |
| Column headers | 13,658, all unique | F40 |
| Patient-level identifier | **None usable.** `STUDY_ID` is the constant "LIVERMET" for all rows; `SUBJECT_ID` is blank for all rows | F40 |
| Identifier used for matching | Country, site, centre and patient number (`COUNTRY_ID`, `SITE_ID`, `CENTER`, `NUMPAT`): 29,562 distinct keys | F40 |
| Identical-content record pairs | **23 pairs (46 rows), 23 extra copies** | F40 |
| Identifier collisions (same key, different content) | 3 pairs (centre 59, patient numbers 1028–1030), one row in each part | F40 |

**Duplicate records.** The identical-content check covered the 188 analysis columns and the identifiers. It did not cover all 13,658 columns; hashing every column was not practical. The 23 pairs are not random:
* 16 pairs link Bulgaria site 385 with Brazil site 387, with identical birth date, operation date, last-news date, status, staging and metastasis data. Two different countries and sites holding identical clinical records is unlikely to be chance. A batch copy or import error is the likely explanation, but this must be confirmed with the registry coordinators.
* 6 pairs are within Irish centre 566, and 1 pair is within Spanish centre 27. Several of the Irish pairs have no operation data.
* **Six second copies are in the analytic cohort**: 2 in development and 4 in validation. Removing them changes the validation C-index from 0.6215 to 0.6214 under the same re-implementation (F51, row d), so the duplicates do not change the conclusions. They should still be removed in the final data.

**Missing values and data quality** (all 29,565 rows; F41). Usable (valid) values:

| Variable | Usable | Missing: blank | Missing: ND | Missing: NA |
|---|---|---|---|---|
| GENDER | 99.8% | 48 | 0 | 0 |
| T stage (STADET) | 72.6% | 3,884 | 4,215 | 9 |
| N stage (STADEN) | 80.7% | 1,439 | 4,243 | 10 |
| M stage (STADEM) | 80.9% | 1,870 | 3,756 | 9 |
| Synchronous presentation | 95.0% | 1,052 | 416 | 0 |
| Metastasis count | 85.6% | 2,014 | 2,256 | 0 |
| Metastasis size | 75.0% | 2,870 | 4,535 | 0 |
| Pre-operative CEA | 58.7% | 2,661 | 9,549 | 9 |
| Primary diagnosis date | 50.7% | 14,583 | 0 | 0 |
| Liver-metastasis diagnosis date | 68.3% | 9,372 | 0 | 0 |
| Operation year and month | 96.2–96.4% | 939 | 130–177 | 4 |

**Blank and ND are different in meaning.** A blank cell means the field was not entered. "ND" (not determined) is an explicit entry meaning the stage was not assessed. The analysis treats both as missing, but they may carry different information (see section 3).

**Raw codes.** The T, N and M codes are all in the expected set (T0–T4b, N0–N2c, M0–M1c). Every non-missing code was mapped, so no valid code was lost to the mapping (F42).

## 2. Patient exclusions: step by step

Sequential flow (F43). Each step is applied to the patients who passed the previous steps.

| Step | Remaining | Excluded at this step | Reason |
|---|---|---|---|
| 1. Registry | 29,565 | — | — |
| 2. CINCLUSION = Yes | 28,979 | **586** | Recorded as not eligible for the registry |
| 3. Hepatectomy recorded | 26,677 | **2,302** | No hepatectomy recorded for the patient |
| 4. Operation year and month | 26,592 | **85** | No operation date |
| 5. Vital status and last-news date | 26,271 | **321** | Status or last-news date missing |
| 6. Chronology consistent | 26,186 | **85** | Last-news date before the operation |
| 7. Positive follow-up or death | 26,094 | **92** | No follow-up time and no death |
| 8. Complete TNM staging | **17,262** | **8,832** | T, N or M missing or not determined |

Total excluded: 3,471 before TNM and 8,832 for TNM, leaving 17,262. Each criterion on its own (F44) fails for: 586 not eligible, 2,751 with no hepatectomy, 1,120 with no operation date, 921 with no vital status, 909 with no last-news date, and 10,100 with incomplete TNM across all 29,565 rows. The 10,100 matches the earlier published TNM-complete count (19,465 complete), so the TNM count is consistent with the earlier report.

## 3. The 8,832 patients excluded for incomplete TNM

**Pattern of missing components** (F45; among the 26,094 patients meeting steps 1–7):

| Missing components | n | % of 26,094 |
|---|---|---|
| T, N and M | 3,041 | 11.7 |
| T only | 2,324 | 8.9 |
| M only | 1,358 | 5.2 |
| T and N | 1,220 | 4.7 |
| T and M | 418 | 1.6 |
| N only | 402 | 1.5 |
| N and M | 69 | 0.3 |
| **Total excluded** | **8,832** | **33.9** |

**Why each component is missing** (F46):
* T: not determined (ND) for 3,617 patients, blank for 3,379, not applicable (NA) for 7.
* N: ND for 3,599, blank for 1,125, NA for 8.
* M: ND for 3,320, blank for 1,559, NA for 7.
* No non-missing code was unmapped.

In other words, 5,337 of the 8,832 excluded patients (60%) have an explicit "not determined" entry for at least one component, and 3,870 (44%) have a blank entry for at least one. Many exclusions therefore reflect a recorded decision that staging was not determined, not a gap in the file.

**Included versus excluded** (F47; SMD = standardised mean difference, values above 0.1 indicate imbalance):

| Characteristic | Analytic cohort (17,262) | Excluded (8,832) | SMD |
|---|---|---|---|
| Synchronous presentation | 58.7% | 44.8% | 0.28 |
| Operated 2010 or later | 51.0% | 35.9% | 0.31 |
| Operation year, median | 2010 | 2007 | 0.58 |
| Largest metastasis, mm (median) | 30 | 35 | −0.19 |
| Age (years, median) | 63.4 | 63.0 | 0.05 |
| Male sex | 61.9% | 60.4% | 0.03 |
| Pre-operative CEA, median (ng/mL) | 7.2 | 9.7 | −0.03 |
| Kaplan–Meier median survival (years) | 4.15 | 3.84 | — |
| Kaplan–Meier 5-year survival | 43.6% | 40.7% | — |

The excluded patients differ systematically on time period, synchrony and metastasis size. Their survival is somewhat worse.

**Clustering by period and site** (F48a–d): TNM incompleteness is 40.1% in the development-era patients (14,127) and 26.5% in validation-era patients (11,967). It is strongly clustered by site. Of 259 sites among the 26,094 patients, 57 have no incomplete TNM at all, 11 have only incomplete TNM, and 34 have 50% or more incomplete. The median site contributes 22 patients. Missingness therefore reflects local recording practice, not random loss.

## 4. Can more patients be included?

Three approaches were tested on the same 26,094 patients (F50–F52). Validation uses operation year 2010 or later; the imputation model uses covariates only, so validation outcomes are not used.

**(a) Multiple imputation of T, N and M** (10 draws; development-era imputation model; ordinal coding).

| Term | HR, complete case (17,262) | HR, multiple imputation (26,094) | 95% CI (imputed) |
|---|---|---|---|
| T3 vs T1–2 | 1.124 | 1.013 | 0.875–1.174 |
| T4 vs T1–2 | 1.364 | 1.158 | 0.988–1.358 |
| N1 vs N0 | 1.282 | 1.264 | 1.191–1.342 |
| N2 vs N0 | 1.625 | 1.497 | 1.396–1.606 |

The imputed hazard ratios are closer to 1, so the TNM effects are attenuated. The imputed patients also have fewer M1 tumours: 45.7% against 57.8% among the observed. Because the imputation model uses no outcome, it cannot reflect the fact that patients with missing staging may have more or less advanced disease. The imputation is therefore not validated, and it would be wrong to present it as a reliable estimate for the excluded patients. Imputation is most credible when the missingness is plausibly random given the covariates. Here the site clustering and the unexplained "not determined" entries argue against that.

**(b) A model without TNM** that uses only variables recorded for almost all patients: age, sex, synchrony, interval from primary diagnosis, metastasis count and size, and period.

| Validation set | n | C-index |
|---|---|---|
| Primary model with TNM (complete-case, same patients) | 8,799 | 0.622 |
| Model without TNM, same 8,799 patients | 8,799 | 0.598 |
| Model without TNM, all validation patients | 11,967 | 0.597 |

TNM adds about 0.02 to the C-index. A model without TNM is scientifically defensible as a separate, clinically usable model for a broader population. It would answer a different question, though: "what can be predicted when staging is unknown?". It should be presented as a complement to the TNM model, not as a replacement, and its results should be reported in its own right.

**(c) Duplicates removed.** Removing the 6 second copies changes the C-index from 0.6215 to 0.6214 under the same re-implementation, and the cohort from 17,262 to 17,256 (2 development, 4 validation; F51, row d).

**Reproduction check.** The complete-case model in this investigation gives validation C = 0.6215, against 0.6216 in the v7 notebook. The 0.0001 difference comes from the re-implementation in the investigation script, not from the cohort or the data. The v7 notebook remains the reference.

## 5. Scientific impact

**Would including more patients improve reliability?** Partly. The primary cohort (17,262) excludes 34% of hepatectomy patients with valid follow-up. Including them would strengthen precision, especially for the development era (only 8,463 development patients with TNM). But imputed staging would introduce error that is not testable in this registry. The sensible gain is the no-TNM model, which uses 26,094 patients and avoids the imputation problem.

**Would it improve generalisability?** Not with the current data. The analytic cohort over-represents recent operations (51% from 2010 onward against 36% of excluded patients) and synchronous presentations. The excluded patients are older, more often metachronous, and have larger metastases. So the TNM-based model describes a more recent, more synchronous population than the registry as a whole. This must be stated as a limitation. The no-TNM model is closer to the full population.

**Recommendations for the manuscript (no analysis changed):**
1. Keep the 17,262 TNM-complete cohort as the primary analysis, and state the exclusion counts in the flow diagram (done).
2. Describe the excluded patients (Supplementary Table S1 already does this) and state that they differ on period, synchrony and size.
3. Report the no-TNM model (C 0.597 on all validation patients) as a complementary sensitivity analysis.
4. Do not present multiple imputation of TNM as a result. Report it only, if at all, as an unvalidated sensitivity analysis showing attenuated TNM effects.
5. Ask the registry coordinators about the 16 Bulgaria–Brazil identical-record pairs and the within-centre pairs, and about the meaning of "ND" versus blank.

## 6. Corrections found during this investigation

* **Deaths beyond 15 years.** The notebook output (F12, row "modelling deaths with event time > 15 years") counts all patients with follow-up beyond 15 years, not deaths. The correct count is **69 patients, of whom 10 died**. The reproducibility report does not quote this figure. The notebook label should be corrected in a future re-run.
* **Table 1 deaths.** Table 1 reports 6,591 deaths (events within 15 years). The total deaths are 6,601; the 10 deaths beyond 15 years are censored in the analysis. Table 1 should say so.
* **Synchronous percentages.** Table 1 gives 58.0% (denominator including unknown synchrony); this table gives 58.7% (denominator excluding unknown). Both are correct for their denominators.

## 7. Limitations of this investigation

* The registry has no patient-level identifier, so duplicates were identified from content and from the centre-number key. Some true duplicates may differ in content and be missed.
* The row-content check covered 188 analysis columns and the identifiers, not all 13,658 columns.
* Imputation used covariates only. An imputation model that uses the outcome would require the outcome for validation patients and is not appropriate for the validation design.
* The no-TNM model uses the same modelling choices as the primary model, except for TNM; it has not been tuned.

## Files in this folder

| File | Content |
|---|---|
| F40 | Dataset verification and duplicate checks |
| F41 | Missingness of key variables, all rows |
| F42 | Raw T, N, M codes |
| F43 | Sequential exclusion steps |
| F44 | Each criterion on its own |
| F45 | Missing-component patterns (step 7) |
| F46 | Reasons for missing components (ND, blank, NA) |
| F47 | Included versus excluded comparison |
| F48a–d | Incomplete TNM by period, operation year, country and site |
| F50 | Hazard ratios: complete case versus multiple imputation |
| F51 | Model comparison (complete case, imputed, no-TNM, duplicates removed) |
| F52 | Distribution of imputed versus observed staging |
