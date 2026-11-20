# Paper 1: change log for the final draft for supervisor approval

**Version:** final draft built from `manuscript_paper1/template_paper1_v2.md` at commit `c359969` and the commits that follow it. The locked v8 analysis, all results, figures and conclusions are unchanged.

## A. Changes made in this final round

| # | Location | Change | Reason | Effect on results |
|---|---|---|---|---|
| 1 | Title page | Label changed from "Draft for Supervisor Review" to "Final Draft for Supervisor Approval" | Status requested | None |
| 2 | Tables 1–4 and supplementary tables | Thousands separators in counts (for example 2821 → 2,821) and en dashes in numeric ranges (for example 6.14-NE → 6.14–NE) | Consistent typesetting with the text | None. Values checked by script |
| 3 | Supplementary Table S5d | Labels describe the removed variables ("model without metastasis count and size") | Remove unsupported "pre-operative-only" label | None |
| 4 | Verification | Added `scripts/final_submission_verification.py`: 75 checks of manuscript and supplementary numbers against the locked CSVs | Verify every reported result | None (checks only) |

## B. Changes made in earlier rounds (retained, verified present)

| Area | Change | Commit |
|---|---|---|
| Predictor timing | Survival time origin, measurement time and intended prediction time separated | `c02e404`, `b6b153e` |
| Predictor timing audit | Reproducible audit script and outputs | `f101094` |
| Missing data | Indicator and training-era median wording; no imputation | `b6b153e` |
| Limitations | Follow-up limits, external validity and calibration limits stated | `4624932` |
| Ethics and authorship | Approval, consent waiver and contributions described as unconfirmed | `4624932` |
| References | Reference list of 13 entries (details still to be verified; see section D) | `4624932`, `8b2703d` |
| C-index interval | Selected-model interval 0.608–0.636; candidate-table upper bound 0.637 explained in Supplementary Table S4a | `eb954f0` |
| Figures | Figure 3 panel titles and Figure S1 embedding | `e5ca3b2`, `2674433`, `6415442` |
| Tables | Column widths and table text size | `61e391f` |

## C. Items checked and found consistent (no change needed)

- No occurrences of "pre-operative-only", "TO CONFIRM", "TO VERIFY", "CITATION NEEDED" in the manuscript or supplementary text.
- No treatment-comparison findings or CART results in the paper. Treatment analysis is mentioned only as future work.
- Cross-references: every cited table and figure exists (Tables 1–4, S1–S10 including S2f and S4a; Figures 1–3 and S1–S3).
- Synopsis: 31 words, two sentences.
- Main text: 3,498 words (Introduction to Conclusions, excluding tables, legends, declarations and references).
- Display items: 3 figures and 4 tables (7).
- Abstract: 220 words, structured.

## D. Issues found but not changed (need supervisor or registry decision)

1. **Predictor measurement time** of metastasis count, size and TNM stage is undocumented. Not resolved by any dataset check.
2. **Intended clinical prediction time** is not yet fully established.
3. **Ethics approval, consent-waiver basis and centre-level approvals** are unconfirmed.
4. **Authorship:** R. Adam's contribution not recorded; all authors' approval not confirmed; individual contributions to be confirmed.
5. **Declarations:** funding and competing-interest statements are from the original draft and need confirmation by all authors.
6. **Registry description:** 63 countries and 242 centres (original text) against 54 country codes and 288 site codes (extract; 259 with eligible patients).
7. **Death date for deceased patients:** the event is defined by `PATSTATC`, so the 3,074 deceased patients without a death flag are still events; their death date is taken from `LASTNDTC`. The registry should confirm that `LASTNDTC` is the date of death for these patients.
8. **Bootstrap precision:** percentile intervals use 300 resamples, with Monte Carlo error of about ±0.001 in the bounds (this is the source of the 0.636/0.637 difference). More resamples would be needed for a final analysis; this was not done, because it would be new analysis.
9. **Centre clustering:** validation and calibration do not account for clustering by centre or site. This is not stated in the manuscript.
10. **References not verified:** the 2026 review's authors; the AJCC 7th edition (removed); the Breslow citation (confirm it is the intended one); the Nordlinger item definitions (the published score has six items, and the registry approximation uses four).
11. **Journal requirements:** the official ASO instructions page could not be checked directly from this session. Secondary sources give 3,500 words, 7 display items, a 250-word structured abstract and a 1–3 sentence synopsis. The reference style (AMA according to one source) and submission-file requirements are unverified.
12. **Keywords:** seven keywords; the journal's keyword limit is unverified.

## E. Verification results

`results/final_v10/final_submission_check/verification.md`: 75 of 75 checks pass. The checks compare numbers in the manuscript and supplementary text with the locked output files (cohort sizes, C-indices and CIs, group results, calibration, benchmarks, sensitivity analyses, duplicate-record results, model hazard ratios, proportional-hazards p-values and missing-data counts).
