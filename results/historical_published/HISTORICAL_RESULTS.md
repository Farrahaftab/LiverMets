# Historical published results (earlier analysis, preserved unchanged)

These values come from `figures/ASO_REVISIONS_SUMMARY.md` and the earlier Colab pipeline
(`scripts/full_analysis_colab.py`, `scripts/build_analysis_cohort.py`). They were produced from a
derived dataset (`LiverMets_Final_Dataset.csv`, with SURVIVAL_YEARS and VITAL_STATUS) that is not in this
repository, so they cannot be regenerated here. They are kept for the record and are **not** the results of
the current analysis.

## Cohort flow (earlier)
- Registry: 29,565 patients
- TNM-complete: 19,465 (10,100 excluded)
- Survival-eligible: 14,759 (4,706 excluded)

## Phenotypes (binary CART on TNM, terminal-node median OS, earlier thresholds 6 and 5 years)
| Phenotype | n | % | Median OS (years) | OS events | RFS events |
|---|---|---|---|---|---|
| Favourable | 3,953 | 26.8 | 6.49 | 1,077 | 1,741 |
| Intermediate | 2,666 | 18.1 | 5.55 | 862 | 1,315 |
| Adverse | 8,140 | 55.2 | 4.06 | 2,958 | 4,784 |

- Global log-rank OS chi2(2) = 224.89; RFS chi2(2) = 371.66 (both p < 0.001)
- Temporal validation: training (<=2009) n = 6,502, chi2 = 86.74; validation (>2009) n = 8,217, chi2 = 159.51

## Multivariable Cox (earlier, n = 13,481)
- Adverse HR = 1.616 (p < 0.001); Surgery+Chemo HR = 0.931 (p = 0.030)
- C-index = 0.607

## Propensity-score matching (earlier, 4,636 pairs, caliper 0.05)
- Favourable p = 0.701; Intermediate p = 0.696; Adverse p = 0.045 (described as exploratory)

## Known issues in the earlier analysis (documented in the current review)
- The CART phenotype was grown with the binary VITAL_STATUS outcome on the full cohort (not a survival tree, and not validated out of sample).
- The earlier RFS used the overall-survival time with an F1-only status mapping.
- The survival origin of SURVIVAL_YEARS could not be verified from the repository.
- The 6-year phenotype threshold was fixed in advance rather than derived from training data.
