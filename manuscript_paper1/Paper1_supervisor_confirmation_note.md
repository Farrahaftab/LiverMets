# Paper 1: supervisor confirmation note

**Purpose.** This note lists facts that the manuscript cannot settle from the locked analysis, and the references and journal requirements that could not be verified in this session. Nothing here is treated as fact until it has been confirmed. Items marked **[TO CONFIRM]** appear in the manuscript.

## 1. Ethics and governance (must be resolved before submission)

| # | Question | Current statement in manuscript | Action needed |
|---|---|---|---|
| E1 | Is there an ethics approval reference, or an exemption? | None recorded. The manuscript says institutional review followed UEL governance (Declarations, p. 13) | Supply the approval reference, or the exemption wording and the body that issued it |
| E2 | On what basis was consent waived? | "Where permitted by applicable regulation" (p. 13) | Confirm the regulatory basis under UEL and the source-centre rules |
| E3 | Do the source centres each have approval? | Not stated | Confirm centre-level approvals or data-sharing agreements |

## 2. Authorship and declarations

| # | Question | Current statement | Action needed |
|---|---|---|---|
| A1 | R. Adam's contribution | None recorded; flagged in the Author Contributions statement | R. Adam to confirm his contribution, or be removed from authorship |
| A2 | Individual contributions of F.A., M.A.G. and M.B. | Taken from the original statement; not re-confirmed | All authors to confirm |
| A3 | Funding and competing interests | "No specific funding"; "no competing interests" | Confirm with all authors |

## 3. Registry definitions and counts

| # | Question | Current statement | Action needed |
|---|---|---|---|
| R1 | Number of countries and centres | Original text: 63 countries, 242 centres. Extract: 54 country codes, 288 site codes; 259 sites with eligible patients | Registry coordinators to reconcile; define "centre" and "site" |
| R2 | Data dictionary and case-report form | Not available in the workbook, repository or uploads | Obtain from the registry |
| R3 | Access route for others to request the data | Stated as via the collaboration (Data Availability) | Confirm the route and any conditions |
| R4 | Registry data-quality checks | Duplicate screen only | Confirm the duplicate pairs (16 probable pairs; 6 second copies in the cohort) |

## 4. Predictor timing (scientific gating question)

- **Question:** were metastasis count and size recorded before or after any preoperative treatment?
- **Current statement:** the model assumes both are known at operation. The timing is unconfirmed (Methods p. 3; Limitation 4, p. 12). Pre-operative and resected counts agreed for 62% of 14,189 patients with both recorded (Supplementary Table S2f). This shows agreement, not timing.
- **Action needed:** registry confirmation. If the counts were recorded after preoperative treatment, the model's inputs would not be available at the time it is meant to be used, and the interpretation would change.

## 5. Exclusion of 33.8% for incomplete TNM staging

- 8,832 of 26,094 eligible patients (33.8%) were excluded. Excluded patients differed (synchrony, metastasis size, operation year), and missingness at random cannot be verified.
- Their outcomes departed from a no-TNM model in opposite directions in the two eras (Supplementary Table S2e). Directions of bias cannot be determined from the registry.
- **Decision needed:** whether to present this as a principal limitation in the abstract, or only in the Results and Limitations as now.

## 6. Follow-up and validation limitations (stated, not resolved)

- Median follow-up is 1.47 years in validation (5.89 years in development). Only 26% of validation patients can be evaluated at 5 years.
- No external validation. Temporal validation within one registry only.
- Calibration in patients operated in 2016 or later cannot be assessed (no 5-year follow-up).
- The model under-predicts 5-year survival in validation (predicted 40.8%; observed 46.6%). It has not been recalibrated; recalibration on contemporary data is needed before absolute estimates are used.
- These limitations are stated in the Results, Discussion and Limitations. The manuscript does not claim external validation, strong discrimination, good calibration or clinical readiness.

## 7. Data quality

- 16 probable duplicate pairs and near-duplicate groups await registry confirmation. Sensitivity analyses show no change to the conclusions.
- 3,074 patients recorded as deceased in the full extract lack an explicit death flag. Their survival times rest on the last-news date.
- 1,676 recurrences lack a usable date; RFS is therefore secondary.
- Thirteen same-day deaths in the cohort: seven lack an explicit death flag (sensitivity analysis: group assignment changed for about 0.4%).

## 8. Analysis decisions for the supervisor

| # | Question | Status |
|---|---|---|
| D1 | Headline horizon: 5 years (current) or 3 years | Pre-specification decision; not changed after validation results were seen |
| D2 | Add clinician-defined decision thresholds | Not added. Requires a named clinical decision |
| D3 | M2a validation CI upper bound: 0.637 (candidate table, F02) or 0.636 (selected-model output, F02b) | Discrepancy documented; the manuscript uses 0.636 (selected-model output); the supervisor must confirm this choice. Documented in Supplementary Table S4a and Figure S3 caption |
| D4 | Was a protocol or statistical analysis plan dated before validation results were seen? | Not stated. **[TO CONFIRM]** |

## 9. Journal requirements (Annals of Surgical Oncology)

| Requirement | Verification status |
|---|---|
| Original article text limit: 3,500 words, excluding title page, abstract and references | Taken from a search summary of the Society of Surgical Oncology instructions. **Not verified against the live page** (surgonc.org could not be reached from this session) |
| Figures and tables combined: maximum 7 | Same source; **not verified** |
| Abstract limit | Not verified. One source mentions 250 words for an article type, unclear which. Current abstract: 220 words |
| Reference limit and reference style (AMA stated by one source) | **Not verified** |
| Word count method used here | Introduction to Conclusions, including figure and table captions, excluding tables, declarations and references: 3,472 words. Conservative: the count includes captions |
| Current display items | Three figures (Figure 1: STROBE flow; Figure 2: overall survival by group, two panels; Figure 3: calibration and observed/expected, two panels) and four tables (Tables 1–4). Total seven display items |

**Action:** check the live instructions page and the reference style before submission.

## 10. Reference verification

| Ref | Reference | Status |
|---|---|---|
| 1 | Fong et al., *Ann Surg* 1999 | Verified by search (authors, title, year, volume, first page). Page range 309–318 per PubMed |
| 2 | Margonis et al., *Br J Surg* 2018;105:1210–1220 | Journal, volume, pages, DOI and first authors verified. **GAME survival figures (11% vs 73%) NOT verified** |
| 3 | 2026 systematic review, *Cancers* 18(4):625 | Title and article number verified from a mirror abstract. **Author list not verified** |
| 4 | Bolhuis et al., *Cancers* 2022;14(10):2356 | Authors, journal, volume, article number and DOI verified. C-indices from the abstract |
| 5 | Collins et al., TRIPOD+AI, *BMJ* 2024;385:e078378 | First four authors and citation verified. **Item-level checklist not verified** |
| 6 | Moons et al., PROBAST+AI, *BMJ* 2025;388:e082505 | First three authors and citation verified |
| 7 | von Elm et al., STROBE, *Lancet* 2007;370:1453–1457 | Authors (six plus group), pages and DOI verified |
| 8 | AJCC Cancer Staging Manual, 7th edition (Edge 2010) | **NOT verified.** Not found by search. Confirm the edition, and which edition the registry's TNM codes follow |
| 9 | AJCC Cancer Staging Manual, 8th edition (Amin 2017) | Publisher, year and ISBN verified; editor list to check |
| 10 | Schoenfeld, *Biometrika* 1982;69:239–241 | Verified |
| 11 | Breslow, *Biometrics* 1974;30:89–99 | Verified as a paper. **Confirm it is the intended citation** for the piecewise Breslow baseline-hazard estimator; the 1972 discussion may be intended |
| 12 | Harrell et al., *JAMA* 1982;247:2543–2546 | Verified. Confirm whether a later Harrell reference is also wanted |
| 13 | Graf et al., *Stat Med* 1999;18:2529–2545 | Verified |
| 14 | Nordlinger et al., *Cancer* 1996;77:1254–1262 | Verified (authors, title, journal, volume, pages). **The published score has six items; the registry approximation uses four different items and is not the published score.** Item definitions to be checked against the article |

## 11. Scientific limitations retained

The Limitations section (pp. 12–13) states: modest discrimination (C-index 0.622); under-prediction of 5-year survival; temporal validation within one registry with short follow-up and no external validation; uncertain predictor timing; one-third exclusion for incomplete staging; missing death flags and undated recurrences; duplicates awaiting confirmation; approximate benchmarks; missing covariates; registry description to reconcile; and over-representation of recent and synchronous operations.
