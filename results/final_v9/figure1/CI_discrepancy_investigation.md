# Investigation: validation C-index 95% CI, F02 (M2a row) vs F02b (selected model)

## Result

| File | Row | Validation C | 95% CI (bootstrap, percentile) |
|---|---|---|---|
| `F02_M_stage_candidates_identical_patients.csv` | M2a | 0.6216 | 0.608–**0.637** |
| `F02b_selected_model_performance.csv` | selected model (= M2a) | 0.6216 | 0.608–**0.636** |

A scratch rerun of the locked notebook (`notebooks/LiverMets_final_reproducible.py`, unmodified, outputs to a scratch folder) reproduced both values exactly.

## Why they differ

1. **Same model.** `SEL = FIT[SELECTED]` with `SELECTED = 'M2a'`, so F02b is the same fitted object as the F02 M2a row. Point estimates, time-dependent AUC, Brier and O/E are identical in both files.
2. **Same method.** Both rows call the same `performance()` function: 300 bootstrap resamples of the validation cohort, C-index recomputed in each, and 2.5th and 97.5th percentiles, formatted to three decimals.
3. **Different random draws.** All resamples come from one generator, `RNG = np.random.default_rng(42)`. The F02 M2a row is computed after the M1 bootstrap has consumed the stream; F02b is computed much later, after many other draws. The two rows therefore use different resamples.
4. **Rounding is not the cause.** Both values are rounded from the raw percentiles to three decimals. The raw percentiles differ by a small amount, which is enough to change the third decimal in one case.

## Size of the effect

Taking the interval width as about 3.92 standard errors gives a bootstrap SE of about 0.0074 for C. The density of C at the 97.5th percentile is about 7.9 per unit (normal approximation). The Monte Carlo SD of the 97.5th percentile from 300 resamples is therefore about 0.0011. The observed gap of 0.001 is within one such SD. Both values are valid estimates of the same interval; neither is a computational error.

## Which estimate to report

- For the selected model, use the `F02b` interval (0.608–0.636). That file is the designated performance output for the selected model. The manuscript text, the abstract and Figure 1 now use it.
- The F02 M2a interval (0.608–0.637) belongs to a candidate-comparison row. It is reported in Supplementary Table S4 with a note that explains the difference.
- Neither value should be presented as more precise than two decimals. Bootstrap percentile bounds from 300 resamples have Monte Carlo error of about ±0.001.

## Options that would remove the discrepancy (not applied)

These would change locked outputs and need explicit supervisor approval:
1. Use the same bootstrap draws for every model (for example, one seed per model) so that the M2a row and F02b agree.
2. Increase the number of resamples (for example, 1,000 or more) and report the interval to two decimals.

No locked value was changed to make the tables agree.
