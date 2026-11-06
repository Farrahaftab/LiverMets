# Paper 1: revision 2 review pack

## 1. What changed in this revision

| Request | Change | Where |
|---|---|---|
| 1. Journal limits | Main text reduced from 4,889 to 3,274 words (Introduction to Conclusions, excluding tables, legends and declarations). Abstract 220 words. Display items reduced from 12 to 7 (2 figures, 5 tables). Method detail moved to supplementary tables S1–S9. Journal limits taken from a search result (3,500 words; 7 figures and tables combined, excluding title page, abstract and references). The live instructions page could not be opened from this session. **[TO CONFIRM against surgonc.org before submission]** | Manuscript; Supplementary |
| 2. TRIPOD+AI primary | Checklist rebuilt on TRIPOD+AI (BMJ 2024;385:e078378), which covers regression. Earlier claim that TRIPOD+AI was machine-learning-only was an error and is corrected. TRIPOD 2015 is no longer cited. Item numbers must be entered from the expanded checklist; the 27-item text was not accessed. | Reporting checklist |
| 3. Predictor timing | "All predictors recorded before or at operation" removed. The text now says the model assumes count and size are known at operation, that timing is unconfirmed, and that this is a limitation. Pre-operative vs resected count agreement (62%) is reported as data, not as proof of timing. | Methods, Predictor timing; Limitation 4 |
| 4. References | Verified by search: Fong 1999; GAME as *Br J Surg* 2018;105(9):1210–1220 (DOI 10.1002/bjs.10838); Bolhuis et al., *Cancers* 2022 (nationwide validation, Fong C 0.577, GAME 0.596); the 2026 *Cancers* systematic review (18(4):625); TRIPOD+AI; PROBAST+AI (BMJ 2025;388:e082505); Harrell 1982. Not verified: STROBE, AJCC editions, Schoenfeld, Breslow, Graf, Nordlinger. Earlier draft errors corrected: GAME was wrongly cited as *Ann Surg*; the TRIPOD+AI and PROBAST+AI author lists were not fully checked. | Reference list |
| 5. Supplementary formatting | S3b (duplicate sensitivity) reshaped: one row per metric, three columns (primary, identical-pair removal, broad rule), O/E and κ rounded. S2, S4, S5, S6 and S8 split into labelled sub-tables with plain column names. Figures S1–S3 added (RFS, decile calibration, period O/E). | Supplementary Material |
| 6. Preserve locked results | No model, coefficient, cut-point, group, C-index or survival value changed. Every table cell is generated from the source CSVs by the build script. | Build scripts |
| 7. Flags kept | Ethics reference, R. Adam's contribution, registry counts, predictor timing and the 2026 review author list remain flagged. | Declarations; Introduction; Reference list |
| 8. Feedback check | See section 2 below. | — |

## 2. Doctors' feedback: how each point is now handled

| Feedback | Current handling | Residual weakness |
|---|---|---|
| Weak discrimination | Reported honestly (C 0.622, 95% CI 0.608–0.637); framed as stratification with calibrated survival; no superiority claimed | Modest C is a real limit for individual decisions; no decision-analytic benefit has been shown |
| Benchmarks (Fong, GAME, TBS, Nordlinger) | Fong and Nordlinger-type compared on identical patients as approximations; GAME and TBS not reproduced | The Nordlinger-type approximation is not the published score, and its original citation is not confirmed. GAME cannot be reproduced without KRAS, which is recorded for 2.3% |
| Censoring and short validation follow-up | Reverse-KM follow-up given; evaluable proportions reported (61%, 35%, 26% at 1, 3, 5 years) | 5-year metrics rest on 26% of validation patients and on the earlier-cohort tail |
| Validation design | Temporal split with fixed model and cut-points | No external validation; calibration in 2016+ patients cannot be assessed |
| Proportional hazards | Tests in training only, stated in Limitation 8 | Validation-cohort PH and time-varying effects for all covariates were not tested |
| Calibration | Under-prediction at 5 years (40.8% vs 46.6%); recalibration sensitivity reported; primary model not recalibrated | Absolute survival estimates should not be used clinically without recalibration on contemporary data |
| Selection | 33.8% excluded for incomplete staging; excluded patients differ; directions of selection bias unknown | The most important unresolved validity threat. Missingness at random cannot be checked |
| Predictor timing | Flagged as unconfirmed | If count and size were recorded after treatment, the model's inputs are not known at the intended time of use |
| Clinical utility | Thresholds not defined; no decision curve | Paper does not show that the groups change decisions |

## 3. Unresolved issues requiring supervisor or registry action

1. **Journal instructions.** Confirm the current word limit, the display-item limit and the reference style on the live *Annals of Surgical Oncology* page. The figures used here came from a search result, and the live page could not be opened.
2. **TRIPOD+AI item numbers.** Enter the item numbers from the official 27-item checklist and the 13-item abstract checklist. The mapping here is by domain, not by number.
3. **Predictor timing (registry).** Data dictionary or case-report form stating when metastasis count and size were recorded relative to any preoperative treatment. This decides whether the model is usable at the intended time point.
4. **Registry description.** 63 countries and 242 centres in the original text, against 54 country codes and 288 site codes (259 with eligible patients). Which is correct, and what is a centre?
5. **Ethics approval reference or exemption wording.** None is recorded. Do not submit until resolved.
6. **R. Adam's contribution.** Not in the original statement. No contribution added on his behalf.
7. **Authors' names and references:** full author lists to check for refs 2–6 (see reference list notes); Nordlinger original citation not found; AJCC edition; Breslow and Graf citations to confirm.
8. **Introduction survival figures.** The GAME figures (11% vs 73%) are confirmed only by a search snippet of the abstract; check against the article.
9. **Horizon and thresholds.** Confirm the headline horizon and whether clinician-defined thresholds are added. Both are pre-specification decisions and cannot be chosen after the validation results.
10. **Protocol or SAP.** State whether a protocol was dated before validation results were seen.
11. **Duplicates.** Registry confirmation of 16 probable duplicate pairs and near-duplicate groups.
12. **Death flags.** 3,074 patients recorded as deceased in the full extract lack an explicit flag; confirm whether the registry can resolve them.

## 4. Major scientific weaknesses that remain

These are not fixed by rewording. They limit what Paper 1 can claim.

1. **Selection into the analytic cohort.** One third of eligible patients are excluded, and the excluded group differs (synchrony, metastasis size, operation year). The model is valid only in the population with complete staging.
2. **Modest discrimination and under-prediction.** The model separates groups but does not predict individual outcomes well, and its absolute survival estimates are too high for recent patients.
3. **No external validation and short validation follow-up.** The temporal split is within one registry, and the 5-year results rest on 26% of validation patients.
4. **Unresolved predictor timing.** The inputs may not be available at the moment the model is meant to be used.
5. **No demonstrated clinical utility.** No decision threshold or decision-curve analysis is reported.
6. **Benchmark comparisons are approximate.** Relative performance against published scores is not established on this registry.

## 5. Files

| File | Purpose |
|---|---|
| `Paper1_manuscript.docx` | Revised manuscript (2 figures, 5 tables) |
| `Paper1_supplementary.docx` | Supplementary Tables S1–S9 and Figures S1–S3 |
| `Paper1_reporting_checklists.docx` | TRIPOD+AI (primary), STROBE and PROBAST+AI status |
| `Paper1_review_pack.docx` | This document |
| `build_paper1.py`, `build_supplementary.py` | Regenerate all tables from source CSVs |
