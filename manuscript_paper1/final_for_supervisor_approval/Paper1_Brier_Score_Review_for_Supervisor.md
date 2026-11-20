# Brier scores (1, 3 and 5 years): verification review for supervisor

**Status:** locked values unchanged (Table 4; `results/final_v7/F02b_selected_model_performance.csv`): 0.0604 at 1 year, 0.101 at 3 years and 0.0651 at 5 years. **No calculation error has been demonstrated.** The non-monotonic pattern alone is not treated as an error.

## 1. Calculation as coded (`notebooks/LiverMets_final_reproducible.py`, lines 41, 380–421)
- Call: `brier_score(y_tr, y_va, S[va][:, 2:], TB)` with `TB` = 1.0, 1.5, ..., 7.0 years.
- `y_tr` / `y_va`: training and validation survival objects (event indicator and follow-up time, capped at 15 years).
- `S[va][:, 2:]`: predicted survival of the fixed M2a model for validation patients at each `TB` time. The columns are aligned: `TIMES = [3, 5, TB...]`, so index 2 onward is `TB`. The 1, 3 and 5-year values are read from the 1.0, 3.0 and 5.0 entries.
- The model was fitted on training patients only (Breslow baseline, training data), and the validation data were not used to fit it.

## 2. IPCW censoring adjustment (verified against the installed library)
- The notebook uses scikit-survival (sksurv) 0.28.0. The implementation was installed and read to confirm its behaviour (`sksurv.metrics.brier_score`).
- Censoring distribution G is a Kaplan–Meier estimate fitted to the **training** data with the event indicator reversed, so it is estimated without validation outcomes.
- For each horizon t, the score is the mean of:
  - events with time ≤ t: (predicted survival)² / G(event time), where the prediction target is 0;
  - patients still at risk at t (time > t): (1 − predicted survival)² / G(t).
- Patients censored before t contribute nothing, which is the standard IPCW correction (Graf et al., 1999).
- Integrated Brier score (1–7 years) uses the same grid and weights (0.0752 in the locked output).

## 3. Limits of independent verification
- The patient-level validation data and the per-patient predicted survival are not stored in the repository, and the raw workbooks are not in this environment. The 0.0604, 0.101 and 0.0651 values therefore **cannot be recomputed here**.
- The notebook does not write per-patient predictions, so the inputs to the Brier function cannot be inspected from the outputs.
- sksurv requires every horizon to lie inside the follow-up range of the test set. The notebook meets this (validation follow-up extends to 15 years), so no error was raised.

## 4. Why the 5-year value is worth a check (not a demonstrated error)
- Approximate no-information Brier scores, using the observed validation Kaplan–Meier survival p(1 − p): about 0.082 (1 year), 0.229 (3 years) and 0.249 (5 years). Relative reduction: about 27%, 56% and 74%.
- A 74% reduction at 5 years is large compared with the time-dependent AUC of 0.675 and the C-index of 0.622.
- Only 26% of validation patients (2,289) have 5-year follow-up, so IPCW weights at 5 years are large and few patients drive the estimate.

## 5. Illustration: a non-monotonic IPCW pattern can occur without error
A simulation (not the locked data) used the same sksurv function with the **true** survival function, heavy censoring in validation, and 14.5% of validation patients followed to 5 years. The Brier scores were 0.145 (1 year), 0.192 (3 years) and 0.143 (5 years): the 5-year value is lower than the 3-year value even though the predictions were exact. This shows that non-monotonicity can arise from the IPCW estimator under heavy censoring alone.

## 6. Recommended checks for the authors (before the values are quoted outside the manuscript)
1. Re-run the existing notebook cell on the raw workbooks, without changing the model, and confirm the three values reproduce.
2. Report the range of IPCW weights, 1/G(t), at 1, 3 and 5 years in the validation cohort.
3. Report the IPCW no-information Brier score at each horizon, so the reader can judge skill.
4. Keep the current caution in Table 4 for the 5-year value. Any change to the reported values would need your decision and a demonstrated calculation error.
