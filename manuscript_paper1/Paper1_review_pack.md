# Paper 1 review pack: feedback response, open questions and reference record

## 1. How the feedback is addressed

| Feedback theme (from the original review) | What the revised Paper 1 does | Evidence / location |
|---|---|---|
| **Weak discrimination** | Reported openly: C-index 0.622 (95% CI 0.608–0.637). Framed as the model's modest discrimination; value claimed as stratification and calibrated survival, not high accuracy. Time-dependent AUC reported at 1, 3 and 5 years. | Abstract; Table 2; Discussion, "Discrimination in context" |
| **Benchmarks (Fong, GAME, TBS, Nordlinger)** | Fong and Nordlinger-type compared on identical patients, explicitly labelled as registry approximations. GAME and TBS not reproduced (KRAS recorded for 2.3%; TBS cut-offs differ). No superiority claimed. | Methods, Clinical comparison; Table 7 |
| **Censoring / follow-up** | Kaplan–Meier and Cox used; reverse-KM median follow-up reported (5.89 and 1.47 years); the number evaluable at each horizon is reported (61%, 35%, 26%). 15-year cap and last-news censoring described. | Table 5; Methods, Censoring |
| **Validation strategy** | Temporal validation: development ≤2009, validation ≥2010, with the model and cut-points fixed on training data. No external validation claimed. | Methods, Model development; Limitation 3 |
| **Proportional hazards** | Schoenfeld tests reported. M1 failed (p = 0.031); selected M2a passed (smallest p = 0.18); M2b time-varying effect not significant (p = 0.21). Validation-cohort PH testing not done (stated as limitation). | Results, Proportional hazards; Table S-PH in F03/F04 |
| **Calibration** | Under-prediction at 5 years (40.8% vs 46.6%; O/E 1.14). Shown by horizon, decile and period. Recalibration sensitivity reported (O/E 1.12). Primary model not recalibrated. | Table 5; Results, Calibration; Figures 4–5 |
| **Clinical score comparisons** | Identical-patient subsets; approximations flagged; pre-operative-only and no-TNM models reported. | Table 7; Table S4 |
| **Limitations** | Eleven numbered limitations, including selection (33.8% excluded), predictor timing, death flags, duplicates and missing covariates. | Limitations section |
| **Treatment content** | Removed from Paper 1. Treatment-associated survival is listed as future research (Paper 2). The earlier PSM treatment findings are not reported. | Introduction (final paragraph); Future research |
| **Earlier CART analysis** | Replaced by the stratified Cox model on 17,262 patients. CART results (14,759 patients) are not mixed with the Cox results. | Discussion, "Relation to earlier work" |

## 2. Open questions requiring supervisor or registry confirmation

1. **Registry description.** The original paper reports 63 countries and 242 centres; the analysis extract has 54 country codes and 288 site codes (259 sites contain patients meeting criteria). Which is correct, and what is a "centre" in the registry?
2. **Predictor timing (gating item for Paper 2).** When were metastasis count and size recorded relative to any pre-operative treatment? No data dictionary was found in the workbook, repository or uploads.
3. **Ethics approval reference.** No reference number is recorded. Does a UEL approval exist, or does the study fall under a governance exemption? Supply the reference or the exemption wording.
4. **R. Adam's contribution** to the work is not recorded in the original author-contribution statement. Confirm before submission; nothing has been added on his behalf.
5. **Horizon decision.** Is 5 years or 3 years the headline horizon? This must be declared before submission, not chosen after seeing validation results.
6. **Option B (clinician thresholds).** Are clinically defined decision thresholds to be added? Without a named clinical decision they should not be added.
7. **Duplicate records.** Registry confirmation of the 16 probable duplicate pairs and near-duplicate groups inside the cohort (6 second copies in the cohort; 37 later records in the broad rule).
8. **Death-flag gap.** 3,074 patients recorded as deceased in the full extract lack an explicit death flag. Can the registry confirm their status?
9. **Journal.** Check the journal's current author guidelines and word limits for prediction-model papers. This has not been verified.
10. **Reporting-guideline choice.** Confirm TRIPOD (2015) as primary. TRIPOD+AI applies to ML-style models and is only a secondary check here.
11. **Citations** flagged in the manuscript: the [CITATION NEEDED] items in the Introduction (incidence statements), and the survival figures for GAME (11% vs 73.4%).
12. **Protocol / registration.** Was a protocol or statistical analysis plan dated before validation results were seen?

## 3. Reference verification record

| Ref | Item | Status |
|---|---|---|
| 1 | Fong 1999, *Ann Surg* | Verified in earlier search; confirm pages |
| 2 | Margonis et al., GAME score | Verified in earlier search; **survival figures (11%, 73.4%) to be checked** |
| 3 | 2026 *Cancers* systematic review | Likely match only; title, venue and score count not fully confirmed |
| 4 | Nationwide Fong validation (PMC9139295) | Authors and journal not confirmed |
| 5 | TRIPOD 2015 (Collins et al., *BMJ*) | Standard citation; confirm volume |
| 6 | TRIPOD+AI 2024 | Author list to verify |
| 7 | PROBAST+AI 2025 | Verified in earlier search; confirm author list |
| 8 | STROBE, von Elm 2007 | Standard citation |
| 9–10 | AJCC Edge 2010; Amin 2017 | Edition used by the registry to confirm |
| 11 | Schoenfeld 1982 | Standard citation |
| 12 | Breslow 1972 discussion | Confirm citation |
| 13 | Harrell C-index | Confirm which Harrell paper is intended |
| 14 | Graf et al. 1999 | Standard citation |
| 15 | Nordlinger-type score | Citation and score definition to confirm; approximation is four items |

Reference details marked TO VERIFY must be checked against the original articles before submission. The TARGET 2025 reference (Cashin, Hansford, Hernán) was verified in the earlier search and is used in the Paper 2 plan, not in Paper 1.

## 4. Changes from the template made in this build

* Corrected the log-rank p-value in development to 1.4 × 10⁻⁷⁷ (was rounded to 1 × 10⁻⁷⁷).
* Clarified that the same-day-death sensitivity changed C from 0.6216 to 0.6221 (excluding all 13 same-day deaths).
* Clarified that 11,594 deceased and 3,074 without a death flag refer to the full extract, not the analytic cohort.
* Changed "centres" to "sites" where the counts come from site codes (259).
* Corrected the three-year bootstrap interval in the calibration text to 1.06–1.12 to match Table 5.
* Marked the GAME survival figures and the nationwide Fong validation statement as TO VERIFY.
