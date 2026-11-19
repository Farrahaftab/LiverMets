# Paper 1: Supervisor Confirmation Note

**Status:** draft for supervisor review. Not for journal submission. The manuscript itself contains no open-question markers. Every item below is unresolved unless marked as verified, and none has been assumed to be correct.

## 1. Changes made to the manuscript in this version

| Change | Reason |
|---|---|
| Removed all bracketed markers (TO CONFIRM, TO VERIFY, CITATION NEEDED) from the text and references | Clean presentation; the open items are listed here instead |
| Removed the statement "GAME: 5-year survival 11% vs 73%" from the Introduction | Not verified from the full article |
| Removed the incidence sentence with a missing citation | No verified source |
| Ethics statement reworded: approval, reference number and consent basis are described as not confirmed | Must not imply approval |
| Author contributions reworded: "as recorded in the original draft; to be confirmed by all authors"; R. Adam's contribution not recorded; approval by all authors not confirmed | Must not imply approval or assign contributions without confirmation |
| C-index confidence interval: the manuscript states 0.608–0.636 and explains that the candidate-model table gives 0.608–0.637 because its bootstrap resamples were drawn separately (Supplementary Table S4a) | Discrepancy kept visible in the supplement and the verification record |
| Limitations: "only 26% of validation patients evaluable at 5 years" added to item 3; closing paragraph states the findings do not establish external validity, strong discrimination, good calibration or readiness for clinical use | Scientific caution |
| AJCC: the 7th edition reference removed; the 8th edition is cited | The 7th edition could not be verified |
| References: unverified details removed from the list; verification status recorded in section 9 below | Do not present unverified details as verified |
| Figure S3 caption: internal references to the supervisor and the investigation file removed; wording otherwise unchanged | Figure content and numbers unchanged |
| Title page: discreet "Draft for Supervisor Review" label | Requested label |

Figures, tables, numerical results, supplementary tables and the locked analysis are unchanged.

## 2. Ethics and governance (must be resolved before any submission)

| # | Question | Current position | Needed |
|---|---|---|---|
| E1 | Ethics approval reference, or exemption | Not confirmed; no reference recorded | Approval reference, or exemption wording and the body that issued it |
| E2 | Basis for waiving individual consent | Not confirmed | Regulatory basis under UEL and the source-centre rules |
| E3 | Centre-level approvals or data-sharing agreements | Not stated | Confirm, per centre |
| E4 | Data-governance arrangements for the LiverMetSurvey registry | Described only as "governed by the LiverMetSurvey collaboration" | Written description and the access route |

The manuscript does not state that ethics approval was obtained. It must not be described as approved until E1–E4 are confirmed.

## 3. Authorship and declarations

| # | Question | Current position | Needed |
|---|---|---|---|
| A1 | R. Adam's contribution | Not recorded | He confirms his contribution, or is removed from authorship |
| A2 | Individual contributions of F.A., M.A.G. and M.B. | Taken from the original draft; not re-confirmed | Each author confirms |
| A3 | Approval of the final manuscript by all authors | Not confirmed | Each author confirms |
| A4 | Funding and competing interests | "No specific funding"; "no competing interests" | All authors confirm |

## 4. Registry definitions and counts

| # | Question | Current position | Needed |
|---|---|---|---|
| R1 | Number of countries and centres | Original text: 63 countries, 242 centres. Extract: 54 country codes, 288 site codes (259 sites with eligible patients) | Registry coordinators reconcile; define "centre" and "site" |
| R2 | Data dictionary or case-report form | Not available in the workbook, repository or uploads | Obtain from the registry |
| R3 | Data-access route for other researchers | Via the collaboration | Confirm the route and any conditions |
| R4 | Duplicate records | 16 probable duplicate pairs; 6 second copies in the cohort | Registry confirmation (sensitivity analyses show no change to conclusions) |

## 5. Predictor timing (gating question)

**Evidence check (this session).**
- *Verified from the repository (locked notebook, column inventory, treatment outputs and the predictor-timing audit):* the model's count is `LE1NBMETAHEPNUM` and its size is `LE1HEPMETASIZENUM`; no timing filter is applied; no data dictionary is present; column names contain no timing word for either field; pre-operative liver chemotherapy is recorded for 7,485 patients (43.4%); 4,259 of 4,320 dated pre-operative starts (98.6%) precede operation; both counts are recorded for 14,189 patients, with equal counts in 62.4% (Supplementary Tables S2f, S5d; audit report in `results/final_v10/predictor_timing_audit/`).
- *Not verifiable:* the raw LiverMetSurvey workbooks were not available in this session, and no computer folder was attached. Headers, metadata and patient-level dates were therefore not checked directly. Any statement about the workbooks is an assumption until they are checked.
- *Inference (not proven):* the count is probably recorded on the hepatectomy form, since its sibling `LE1NBMRESECNUM_F1` is a resection count.

**Three distinct questions (as stated in the manuscript).**

1. **Survival time origin: hepatectomy (operation date).** Confirmed as the origin of survival time. This does not show that any predictor was measured at hepatectomy.
2. **Predictor measurement time: not confirmed.** For metastasis count and size, no documentation states when they were measured relative to preoperative chemotherapy or pathology. The source of TNM stage (clinical or pathological) is also unconfirmed. The dataset does not show that count and size were available at hepatectomy.
3. **Intended clinical prediction time: not yet fully established.** Preoperative, hepatectomy and postoperative timing are unresolved. The model should not be used for pre-treatment decisions.

**Needed from the registry coordinators (cannot be obtained from the dataset):**
1. What `LE1NBMETAHEPNUM`, `LE1HEPMETASIZENUM` and their `_V` variants measure, and the date on which each was recorded.
2. Whether the count and size were recorded before or after preoperative liver chemotherapy.
3. Whether size is radiological, clinical or pathological.
4. Whether TNM stage (`STADET`, `STADEN`, `STADEM`) is clinical or pathological, and when it was assigned.
5. The meaning of ND compared with blank for these fields.

**Decision for the supervisor:** whether the intended clinical prediction time can be stated before the registry answers questions 1–5 below, or whether the manuscript should describe the prediction time as unresolved (as it does now).

## 6. Exclusion of 33.8% for incomplete TNM staging

- 8,832 of 26,094 eligible patients (33.8%) were excluded. They differed in synchrony, metastasis size and operation year. Missing-at-random cannot be verified.
- Their outcomes differed from a no-TNM model in opposite directions across the two eras (Supplementary Table S2e). The direction of selection bias cannot be determined from the registry.
- **Decision:** whether to move this to the abstract as a principal limitation. It is currently in the Results, Limitations and Discussion.

## 7. Follow-up and validation limits (stated in the manuscript)

- Validation median follow-up 1.47 years (development 5.89). Only 26% of validation patients are evaluable at 5 years.
- No external validation. Temporal validation within one registry.
- Calibration for operations in 2016 or later cannot be assessed (no 5-year follow-up).
- The model under-predicts 5-year survival in validation (predicted 40.8%, observed 46.6%) and has not been recalibrated.

## 8. Other data-quality items

- 3,074 patients recorded as deceased in the full extract lack an explicit death flag; survival for them rests on the last-news date.
- 1,676 recurrences lack a usable date; RFS is secondary.
- Thirteen same-day deaths in the cohort; seven lack an explicit death flag (group assignment changed for about 0.4% in the sensitivity analysis).

## 9. Reference verification status

| Ref | Reference | Status | Action |
|---|---|---|---|
| 1 | Fong et al., *Ann Surg* 1999 | Verified by search (authors, title, year, volume, first page); pages 309–318 per PubMed | Confirm against the article |
| 2 | Margonis et al., *Br J Surg* 2018 (GAME) | Journal, volume, pages, DOI and first three authors verified. Survival figures not verified and removed from the text | Confirm the cited claim before reinstating any figure |
| 3 | 2026 systematic review, *Cancers* 18(4):625 | Title, journal and article number verified from a mirror abstract. **No authors listed; author list not verified** | Add the authors from the article |
| 4 | Bolhuis et al., *Cancers* 2022 | Authors, journal, volume, article number and DOI verified; C-indices from the abstract | Confirm against the article |
| 5 | Collins et al., TRIPOD+AI, *BMJ* 2024 | First four authors and citation verified; remaining authors shown as "et al." | Complete the author list |
| 6 | Moons et al., PROBAST+AI, *BMJ* 2025 | First three authors and citation verified | Complete the author list |
| 7 | von Elm et al., STROBE, *Lancet* 2007 | Six authors, pages and DOI verified | None |
| 8 | Amin et al., AJCC Cancer Staging Manual, 8th ed., 2017 | Publisher, year and ISBN verified. **The registry's TNM edition is not confirmed** | Confirm which edition the registry's TNM codes follow |
| 9 | Schoenfeld, *Biometrika* 1982 | Verified | None |
| 10 | Breslow, *Biometrics* 1974 | Paper verified. **Confirm this is the intended citation** for the piecewise Breslow baseline-hazard estimator (a 1972 discussion paper may be intended) | Supervisor decision |
| 11 | Harrell et al., *JAMA* 1982 | Verified. Confirm whether a later Harrell reference is also wanted | Supervisor decision |
| 12 | Graf et al., *Stat Med* 1999 | Verified | None |
| 13 | Nordlinger et al., *Cancer* 1996 | Verified (authors, title, journal, volume, pages). **The published score has six items; the registry approximation uses four different items and is not the published score**; item definitions to be checked | Check the item definitions against the article |

**Removed earlier:** the 7th-edition AJCC reference (not verified).

## 10. Analysis and presentation decisions for the supervisor

| # | Question | Position |
|---|---|---|
| D1 | M2a validation CI upper bound: 0.637 (candidate table, F02) or 0.636 (selected-model output, F02b) | The manuscript uses 0.636. The difference arises from separate bootstrap resamples (verified by rerunning the locked notebook). The candidate-table value is shown in Supplementary Table S4a. **Supervisor to confirm the choice** |
| D2 | Headline horizon: 5 years (current) or 3 years | Pre-specification decision. Not changed after validation results were seen |
| D3 | Add clinician-defined decision thresholds | Not added; requires a named clinical decision |
| D4 | Was a protocol or statistical analysis plan dated before validation results were seen? | Not stated. **To confirm** |
| D5 | Is the M2b time-variation p-value (0.207) presented correctly? | Rounded to three decimals in Table S4c; the text says 0.21 (two decimals) |

## 11. Reporting checklists

- **TRIPOD+AI (primary):** the structure of the checklist (items 1–27 by domain) was confirmed by search. Individual sub-item numbers and wording were **not** verified because the checklist text could not be accessed. The checklist file gives domain ranges and manuscript page locations only. Item 19 (patient and public involvement) is not reported in the source documents and must be stated by the authors.
- **STROBE:** all 22 items are mapped to manuscript locations; items 2, 5 and 8 are partly complete pending E1–E4 and R1–R2.
- **PROBAST+AI:** the risk-of-bias judgements have not been completed. This must be done by the authors.

## 12. Journal requirements (Annals of Surgical Oncology)

| Requirement | Status |
|---|---|
| Original article text limit: 3,500 words, excluding title page, abstract and references | Taken from a search summary of the Society of Surgical Oncology instructions. **Not verified against the live page** (surgonc.org could not be reached) |
| Figures and tables combined: maximum 7 | Same source; **not verified**. Manuscript has 3 figures and 4 tables |
| Abstract limit | Not verified. Current abstract: 220 words |
| Reference limit and reference style | **Not verified** |
| Word count used here | 3,472 words, from the Introduction to the Conclusions, including figure and table captions and excluding tables, declarations and references. Conservative, because captions are included |
| Synopsis | 31 words (limit 40, as requested) |

**Action:** check the live instructions and the reference style before submission.
