# Cover note: revised manuscript (v7) for supervisor review

## What changed
The earlier manuscript reported a binary-CART TNM phenotype analysis (14,759 patients, median-OS thresholds, approximated RFS, propensity-matched treatment comparison). That analysis is superseded. The revised manuscript reports the final v7 analysis: a stratified Cox model (M2a) with three prognostic groups fixed by training-only tertile cut-points, 17,262 TNM-complete patients, temporal validation (2010+), calibration, sensitivity analyses and RFS.

| Item | Earlier manuscript | Revised (v7) |
|---|---|---|
| Analytic cohort | 14,759 | 17,262 (TNM-complete; from 26,094 with valid follow-up) |
| Phenotype method | Binary CART, groups by KM median OS | Cox M2a, tertiles of predicted 5-y survival |
| Validation C-index | 0.609 (multivariable Cox, complete case) | 0.622 (0.608–0.637) |
| Group median OS (validation) | 7.76 / 5.50 / 4.22 y | 7.38 / 4.44 / 3.18 y |
| RFS | Approximated from PATSTAT_F1 | Dated recurrences from the registry (5,324 dated; 1,676 undated, handled by four rules) |
| Median RFS | Not stated as a headline | 2.03 y (1.98–2.09) primary |
| Calibration | Not assessed | O/E 1.14: survival under-predicted in validation |
| Treatment comparison | PSM, surgery ± chemotherapy | Removed (not re-analysed in v7) |

Every number in the revised text was checked against the v7 outputs in `results/final_v7/`. Superseded results are listed in `results/final_v7/SUPERSEDED_RESULTS.md`.

## Decisions needed from you
1. **Treatment comparison.** The propensity-matched treatment analysis was removed because it has not been re-run on the v7 cohort. Re-running it is an analysis change. Keep it out, or approve a re-run before reinstating it.
2. **Title and framing.** The title no longer says "TNM-based", because the model also uses age, sex, synchronous presentation, interval, and metastasis number and size.
3. **Recurrence dates.** The earlier draft said exact recurrence dates were unavailable. The v7 analysis uses dated recurrences in the registry extract. Please confirm this with the registry team before submission.
4. **Calibration and absolute survival.** The revised paper states that the model under-predicts survival in validation and advises against quoting absolute survival until recalibrated. Please confirm this framing.

## Items still to produce or check
- **Figure 1 (STROBE flow)** must be redrawn from `results/final_v7/F01_flow_by_day_convention.csv`. The earlier diagram shows the superseded flow and must not be reused.
- **Table 1 (baseline characteristics)** and **Supplementary Table S1 (included vs excluded)** have not been generated from the v7 cohort.
- **Operative-field counts** (13,130 of 20,553 agreeing; 3,179 exceeding pre-operative counts) come from an earlier audit, not from the v7 notebook. They should be regenerated or verified.
- **References.** The earlier 41-item list has been reduced to 11 references cited in the revised text. The 41 earlier references supported the superseded CART, treatment and adjuvant-chemotherapy discussion. Three statements are marked [CITATION NEEDED]. All citation details must be verified against the originals.
- **Author contributions and ethics** statements are carried over from the earlier draft and must be confirmed. The earlier draft's contribution statement for R.A. was not present in the original and has not been added.
- **Discussion of treatment and adjuvant chemotherapy** has been removed with the treatment analysis.

## Files
* `Revised_manuscript_v7.docx`: editable Word version for review.
* `Revised_manuscript_v7.md`: Markdown source.
* `figures/COX_01–04*.png`: Figures 2–5.
