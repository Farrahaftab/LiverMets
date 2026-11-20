# Paper 1: final verification report (round 2)

**Status: Final Draft for Supervisor Approval. Not ready to submit.**

## 1. Numbers
- 75 of 75 headline checks pass against the locked outputs (`scripts/final_submission_verification.py`, re-run this round).
- All numbers in the two-column PDF match the repository manuscript (word-level number comparison: identical multiset, except image-width codes).
- Figure 1 panel values: development apparent C-index 0.595 (F02 train_C 0.5952), IBS 0.075 (F02b 0.0752), O/E 1.14, slope 1.07, calibration values all match locked files. Flow arithmetic checked at each exclusion step.
- Table 2 coefficients match `final_v9/paper1/P1_model_coefficients.csv`; Table 3 predicted survival matches `P1_group_summary.csv`; Figure 2 numbers at risk match `final_v9/paper1/F81_numbers_at_risk_by_group.csv`.

## 2. Brier scores (1, 3, 5 years): investigation
- **Definition and code.** Brier scores come from `sksurv.metrics.brier_score(y_tr, y_va, S[va][:, 2:], TB)` with TB = 1.0, 1.5, ..., 7.0 years. Censoring is handled by inverse-probability-of-censoring weights (Graf et al., 1999), with the censoring distribution estimated from the training cohort only. The S columns align with the TB grid (TIMES = [3, 5, TB...]), so the 1, 3 and 5-year columns are picked correctly.
- **Values (locked, F02b):** 0.0604 (1 y), 0.101 (3 y), 0.0651 (5 y).
- **Concern.** The 5-year value implies a large skill relative to a null model (null Brier about p(1−p) = 0.466 × 0.534 ≈ 0.25, so about 74% reduction), which is larger than at 1 year (about 27%) and 3 years (about 56%), and hard to reconcile with a time-dependent AUC of 0.675. A plausible cause is unstable IPCW weighting at 5 years, where only about 26% of validation patients are evaluable. This is a hypothesis, not a demonstrated error.
- **Limit of this check.** Patient-level data are not in the repository and the raw workbooks are not in this container, so the Brier values cannot be recomputed here. Non-monotonicity alone is not evidence of error.
- **Action.** The 5-year Brier is flagged in Table 4 and should be recomputed by the authors from the raw workbooks (notebook re-run) before the figure is quoted. No locked value was changed.

## 3. Missing data
- Confirmed against the notebook (see change log item 1). The wording in Methods and Limitation 5 now matches the code.

## 4. Reference 3
- The Cancers record exists: "Prognostic Scores for Liver Resection in Colorectal Metastases: Performance, Limitations, and Methodological Pitfalls—A Systematic Review and Meta-Analysis", Cancers 2026, 18(4), 625, published online 14 February 2026 (confirmed by search result).
- **Authors and DOI not confirmed.** mdpi.com and doi.org are blocked from this environment, so the publisher record could not be read. The author list in the earlier uploaded PDF is not verified and has been removed from the manuscript pending confirmation.

## 5. Layout
- Two-column design rebuilt from the corrected source. The original source file is not in the repository, so pagination differs: 10 pages here, against 12 in your uploaded PDF.
- Table 1 caption now sits above its table. Gaps arise where full-width figures do not fit at the end of a page.
- Editable Word file (`Paper1_ASO_Main_Manuscript_FINAL_DRAFT.docx`) uses two-column sections with full-width tables and figures. In the LibreOffice render, Tables 3 and 4 are still cramped and need checking in Microsoft Word before use. Do not treat the Word layout as final.

## 6. Ethics, authorship, predictor timing, registry (unresolved)
- Ethics approval, consent-waiver basis and centre-level approvals: not confirmed.
- R. Adam's contribution not recorded; individual contributions and final approval by all authors not confirmed.
- Funding and competing-interest statements come from the original draft.
- Predictor measurement time and intended prediction time: not confirmed.
- Registry counts: 63 countries and 242 centres in the original text; 54 country codes and 288 site codes in the extract (259 with eligible patients). To be reconciled.

## 7. Word count
- Main text: 3,615 words (Introduction to Conclusions). The secondary-source limit is 3,500. Not reduced without instruction.
