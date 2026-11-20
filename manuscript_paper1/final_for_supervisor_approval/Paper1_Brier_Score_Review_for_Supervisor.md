# Brier scores (1, 3 and 5 years): review for supervisor

**Status:** locked values unchanged (Table 4; `results/final_v7/F02b_selected_model_performance.csv`): 0.0604 at 1 year, 0.101 at 3 years, 0.0651 at 5 years. No calculation error has been demonstrated, and non-monotonic values are not treated as an error here.

## What was calculated (from `notebooks/LiverMets_final_reproducible.py`, lines 41, 380–421)
- Function: `sksurv.metrics.brier_score(y_tr, y_va, S[va][:, 2:], TB)`, where `TB` = 1.0, 1.5, ..., 7.0 years, and `S` is the predicted survival of the fixed M2a model at each time.
- Censoring: inverse-probability-of-censoring weights (IPCW; Graf et al., 1999). The censoring distribution is estimated from the **training** cohort only. Validation patients censored before a time point receive weight 1/G(t), and events before the time point receive weight 1/G(T−).
- Time points: the 1, 3 and 5-year values are the entries for 1.0, 3.0 and 5.0 in the same grid, so the time alignment is correct.
- Integrated Brier score (1–7 years) uses the same grid and weights (0.0752 in the locked output).

## Why the pattern deserves a check (not a finding of error)
- Approximate null (no-information) Brier scores, using the observed validation Kaplan–Meier survival p(1−p): about 0.082 at 1 year, 0.229 at 3 years and 0.249 at 5 years.
- Relative reduction versus null: about 27% at 1 year, 56% at 3 years and 74% at 5 years.
- A 74% reduction at 5 years is larger than the time-dependent AUC (0.675) and the C-index (0.622) would suggest, and it is out of line with the 1 and 3-year values.
- A plausible contributor is IPCW instability at 5 years: only 26% of validation patients (2,289) are evaluable at 5 years, and their censoring weights are large. This is a hypothesis, not a demonstrated error.

## What could not be checked here
- Patient-level data are not in the repository, and the raw workbooks are not in this environment. The Brier values therefore cannot be recomputed. The notebook also does not write per-patient predictions.
- The null-model reference above is approximate: it ignores censoring and uses Kaplan–Meier survival, not an IPCW null.

## Recommended action for the authors (before the Brier values are quoted outside the manuscript)
1. Re-run the existing notebook cell on the raw workbooks (no change to the model), and confirm that the 0.0604, 0.101 and 0.0651 values reproduce.
2. Report the range of IPCW weights at 1, 3 and 5 years in the validation cohort.
3. Report the IPCW-null Brier score at each horizon, so that the reader can judge skill.
4. If the 5-year value remains low after these checks, either report it with the 26% evaluable caveat (as in Table 4) or drop it in favour of the 1 and 3-year values. Any change would be a presentation decision for you and your supervisor.
