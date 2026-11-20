# Paper 1: final quality-control report on the uploaded 12-page two-column design

Scope: the uploaded PDF `8e140cfb-Research_paper_request.pdf` (12 pages, label "Final Draft for Supervisor Approval") was compared with the repository manuscript (`Paper1_manuscript.md`) and the locked v7/v9 outputs. No analysis, model, cohort, result or conclusion was changed.

## 1. Numerical agreement
- Every numeric token in the uploaded PDF text matches the repository manuscript. Only differences: image-width codes in the markdown (artefacts), and the DOI and author list on reference 3, which exist only in the PDF.
- 75 of 75 headline checks pass (`scripts/final_submission_verification.py`).
- Figure 1 panel values match locked outputs: development apparent C-index 0.595 (F02, M2a train_C 0.5952); IBS 0.075 (F02b 0.0752); O/E 1.14; calibration slope 1.07; group n, deaths, medians and 5-year KM values.
- Figure 2 numbers at risk match F81 (validation Favourable 2,662/916/325/108/30/3, etc.).
- Table 2 coefficients, hazard ratios and CIs match P1_model_coefficients.csv.
- Table 3 mean predicted 5-year survival (53.2/42.8/29.1%) matches P1_group_summary.csv.
- Table 4 Brier scores match F02b (0.0604, 0.101, 0.0651).
- Figure 1 flow arithmetic: each exclusion step subtracts correctly (29,565 → 28,979 → 26,677 → 26,592 → 26,271 → 26,186 → 26,094 → 17,262).
- Not covered by the 75 checks: Fong/Nordlinger subset C-indices, CEA values, excluded-patient percentages (69.7%, 24.4%), RFS medians, and sensitivity figures. Their values appear in the locked result files as text matches only; they are not fully traced to a specific cell.

## 2. Genuine errors and issues found
1. **Missing-data wording is internally inconsistent (corrections needed).** Methods says "no imputation was used". Limitation 5 says missing values "were replaced using development-cohort medians". Median replacement is single imputation. Suggested wording: "missing values were replaced by development-cohort medians with missingness indicators (single imputation); multiple imputation was used only in the CEA sensitivity analysis." Needs your approval before changing.
2. **Layout: Table 1 caption is separated from its table** (caption on page 4, table on page 5), leaving page 4 mostly blank.
3. **Reference 3 author list and DOI** (Viganò L, Risi L, Ragaini E, Ieva F, Desiato E; doi:10.3390/cancers18040625) appear in the PDF but not in the repository manuscript. The article exists (Cancers 2026, 18(4), 625, published 14 February 2026), and its MDPI URL matches the DOI pattern. The author list could not be confirmed from the search result. Confirm against the journal page before submission.
4. **Table 4 Brier score is non-monotonic** (1 y 0.060, 3 y 0.101, 5 y 0.065). This is the locked value. It is not an error in the manuscript, but a reviewer may ask about it. Flag for supervisor.
5. **Design source not in the repository.** The 12-page two-column layout (printed from a browser) has no source file in this container. The repository builds a different 15-page single-column version. Keeping the exact design requires either the original HTML/source or permission to reconstruct it.

## 3. Still needing supervisor or author confirmation (not changed)
- Ethics approval reference or exemption; consent-waiver basis; centre-level approvals.
- Authorship: R. Adam's contribution not recorded; individual contributions and final approval by all authors not confirmed.
- Funding and competing-interest statements (from original draft).
- Registry centre and country counts (63/242 original text vs 54/288 extract; 259 sites with eligible patients).
- Predictor measurement time and intended clinical prediction time.
- Reference 3 authors; reference 8 AJCC edition used by the registry.
- Bootstrap precision: 300 resamples; M2a upper bound 0.637 (candidate table) vs 0.636 (selected model).
- Journal requirements (word limit, display items, abstract, synopsis, reference style) remain unverified against official ASO instructions.

## 4. Limitations
All 12 limitations are present in the uploaded PDF and in the repository manuscript, including predictor timing (4), calibration (2), missing data (5) and short validation follow-up (3).
