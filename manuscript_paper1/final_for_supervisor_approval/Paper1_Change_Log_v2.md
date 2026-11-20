# Paper 1: change log (round 2, QC corrections)

Scope: formatting and wording corrections only. The locked v8 model, cohort, numerical results, figures, tables, conclusions and all 12 limitations are unchanged.

## Changes made
1. **Missing-data wording (approved).** Methods and Limitation 5 now state the same handling, confirmed in the notebook (`notebooks/LiverMets_final_reproducible.py`, lines 308–310 and 1017–1019): for interval, count and size, a missingness indicator is added and the value is replaced by the development-cohort median (single median imputation). Age, sex and synchrony, if missing, get the same median without an indicator. Multiple imputation (IterativeImputer, 10 draws) is used only in the CEA sensitivity analysis (notebook lines 690–723).
2. **Brier and AUC methods disclosed.** Methods now states that Brier scores are inverse-probability-of-censoring weighted with the censoring distribution from training patients (`brier_score(y_tr, y_va, ...)`, notebook line 418), and that the time-dependent AUC at each horizon uses the 5-year cumulative hazard as the risk score (line 415). These describe code already used; no value changed.
3. **Table 4 caution added** on the 5-year Brier score (based on the 26% of validation patients with 5-year follow-up).
4. **Reference 3.** Title, journal, year and article number kept. Authors and DOI are marked as "to be confirmed against the publisher record" because the publisher site could not be reached from this environment (see verification report). The author list in the earlier PDF was not used.
5. **Layout.** Two-column design rebuilt as HTML from the corrected source (`final_for_supervisor_approval/design_source/`), with the Table 1 caption moved above its table, full-width tables and figures, and the running header and "Page x of y" footer. Output is 10 pages, not 12 (see verification report, item 5).

## Not changed (deliberately)
- No refit, recalibration or reanalysis.
- Cohort (17,262; 8,463 / 8,799), all 75 verified numbers, and the three groups.
- Limitations 1–12, including predictor timing, calibration, missing data and short validation follow-up.

## Open items
- Word length: the main text is now 3,615 words, above the 3,500-word limit cited from secondary sources. Content was not cut without your instruction.
