# Audit of the v7 analysis: duplicates, follow-up window, TNM and selection

**Status.** This audit is separate from the locked v7 notebook and manuscript. Nothing here changes the primary results. The audit script is `notebooks/audit_checks_v7.py`. It reproduces the primary validation C-index exactly (0.6216), which validates its cohort construction and model.

**Corrections to earlier outputs.** The investigation stage C reported 0.6214 for the duplicate-removed model and 0.5982 for the no-TNM model on all validation patients. Those values used covariate medians computed across all development patients rather than TNM-complete patients. The corrected values are 0.6216 (duplicates removed, cohort-level) and 0.5972 (no-TNM, all validation patients; unchanged). The earlier value of 0.6214 is superseded (see the register).

## 1. Duplicate records: identification and assessment

**How they were identified.** Each row was hashed over the 188 analysis columns of the extract. Rows with identical hashes are "identical-content pairs". A second, broader screen looked for records sharing birth date, operation date and sex, with different content ("near-duplicates").

**Identical-content pairs (A00, A01).** 23 pairs (46 rows).
* 16 pairs link records at Bulgaria site 385 and Brazil site 387. Every pair has identical birth date, operation date, last-news date, status and staging.
* 6 pairs are within Irish centre 566. These records have only 5 non-blank analysis fields.
* 1 pair is within Spanish centre 27.

**Decision rule.** A pair is a *probable duplicate* if (a) all non-blank analysis fields are identical, (b) birth and operation dates match, and (c) at least 20 analysis fields are filled. Sixteen pairs meet this rule (15 cross-country, 1 within centre 27). The six Irish pairs have too few fields to be assessed, and they are not in the analytic cohort.

**Same patient or not?** The cross-country pairs are very unlikely to be coincidence. Two different sites holding identical birth, operation, follow-up and staging data for every field is an import or copy error, most probably a batch duplicated between two sites. This is an inference from the data, and the registry coordinators should confirm it. The file alone cannot prove that the records describe the same person, because there is no patient identifier.

**Across training and validation (A00).** No identical pair spans development and validation. Both copies of each pair share an operation date, so they fall in the same era. Six pairs have both copies in the analytic cohort (2 development, 4 validation).

**Near-duplicates (A02, A13).** 55 groups share birth date, operation date and sex but have different content. 43 are at the same site. Only 16 agree on both last-news date and status, so most are not clean duplicates. Of the 55 groups, 31 have both copies in the analytic cohort and 11 have one copy in it. Whether these are the same patients cannot be determined from the file.

**Treatment of duplicates.** The primary analysis keeps all records, as locked. The identical pairs satisfy a clear rule and are removed in one sensitivity analysis. The near-duplicates do not satisfy a defensible identification rule, so they are removed only in a broader sensitivity analysis, to show their effect.

## 2. Duplicate sensitivity (A03)

| Analysis | Analytic n | Dev n | Val n | Val C | Val 5-y KM | Val O/E (5-y) | Cut-points (q33 / q67) | Patients in same group as primary | Reassigned |
|---|---|---|---|---|---|---|---|---|---|
| Primary (locked) | 17,262 | 8,463 | 8,799 | 0.6216 | 46.6% | 1.143 | 0.3793 / 0.4756 | — | — |
| Identical-content pairs: second copy of each pair removed (all 6 in the cohort meet the probable-duplicate rule) | 17,256 | 8,461 | 8,795 | 0.6216 | 46.6% | 1.142 | 0.3794 / 0.4756 | 99.8% (κ 0.997) | 33 |
| Exact or near duplicates, later record removed | 17,225 | 8,444 | 8,781 | 0.6216 | 46.7% | 1.146 | 0.3785 / 0.4753 | 99.2% (κ 0.988) | 138 |

Group sizes (validation): primary 2,662 / 2,824 / 3,313; identical-pair removal 2,660 / 2,825 / 3,310; broad removal 2,656 / 2,833 / 3,292.

**Interpretation.** Removing duplicates changes the cohort by 6 to 37 patients (0.03% to 0.2%). The C-index, 5-year survival and median OS are essentially unchanged. Calibration moves by less than 0.01 in O/E. Between 33 and 138 patients change group, depending on how far the removal goes. The prognostic groups and their conclusions are therefore robust to duplicates. Nonetheless, the identical cross-country pairs are a data-quality problem that should be fixed in the registry, and the primary analysis should be re-run with those pairs removed once the registry has confirmed them.

## 3. Deaths and follow-up beyond 15 years (A04)

| Quantity | n | Meaning |
|---|---|---|
| Deaths recorded (PATSTATC = Deceased), analytic cohort | **6,601** | All recorded deaths |
| Deaths inside the 15-year analysis window (OS_E = 1) | **6,591** | Events used in the models |
| Deaths beyond 15 years, censored at 15 years | 10 | Recorded deaths not counted as events |
| Patients with follow-up beyond 15 years | 69 | **A patient count, not a death count** |
| — of whom died | 10 | The deaths above |
| — of whom alive or lost to follow-up | 59 | Censored at 15 years |

The development cohort has 4,685 recorded deaths, of which 4,675 are inside the window. The validation cohort has 1,916 recorded deaths, all inside the window.

**Label correction.** The notebook output F12 row "modelling deaths with event time > 15 years (censored)" counts patients, not deaths. The label is wrong, and the value 69 must be described as patients, of whom 10 died. The corrected statement is in this audit. The notebook label should be corrected in the next authorised re-run, because a change to the notebook requires re-execution.

## 4. TNM-complete model versus no-TNM model on the same patients (A05)

| Model | Development | Validation population | n | C-index | Paired difference (95% CI) |
|---|---|---|---|---|---|
| TNM M2a (primary) | 8,463 TNM-complete | TNM-complete validation | 8,799 | **0.6216** | — |
| No-TNM model | 8,463 TNM-complete | TNM-complete validation (same patients) | 8,799 | 0.5994 | TNM − no-TNM = **0.022 (0.011 to 0.034)** |
| No-TNM model | 14,127 all development | TNM-complete validation (same patients) | 8,799 | 0.5982 | — |
| No-TNM model | 14,127 all development | All validation patients | 11,967 | 0.5972 | not comparable (different patients) |

On identical patients, TNM adds about 0.02 to the C-index, and the 95% interval excludes zero. The broad no-TNM model is slightly worse on the same patients, which confirms that the broader development set does not add discrimination.

## 5. The 8,832 incomplete-TNM patients (A06–A11)

**Operation year (A06).** Exclusion falls steadily with time: 69.7% of 1990–1999 operations, 45.3% of 2000–2004, 28.3% of 2005–2009, 27.1% of 2010–2014 and 24.4% of 2015–2020.

**Centre and country (A07).** Among 259 sites, 57 have no incomplete TNM, 11 have only incomplete TNM and 34 have 50% or more. The ten sites with the most exclusions account for 54% of all exclusions. Among 52 countries, 3 have no exclusions, 1 has only exclusions, and the ten largest contributors account for 82%. Missingness is therefore concentrated in specific centres.

**Clinical characteristics (A08).** Included and excluded patients differ most on synchronous presentation (58.7% vs 44.8%, SMD 0.28), operation year (median 2010 vs 2007, SMD 0.58) and metastasis size (30 vs 35 mm, SMD −0.19). Age, sex, metastasis count and CEA differ little. Among metachronous patients, the interval is unavailable for 55.9% of included and 66.2% of excluded patients. The logistic model (A11) confirms that TNM completeness is associated with operation year (OR 1.75 for 2010 onward), synchronous presentation (OR 1.94), and smaller metastases.

**Outcomes (A09).** The direction of the difference depends on the era:

| Group | Included 5-y KM | Excluded 5-y KM |
|---|---|---|
| Development (≤2009) | 42.3% | 39.1% (worse) |
| Validation (≥2010) | 46.6% | 50.5% (better) |

**Informative-selection test (A10).** The no-TNM model fitted on development predicts 5-year survival for both groups. Observed/expected ratios: included 1.03 (development) and 1.16 (validation); excluded 0.96 (development) and 1.27 (validation). If exclusion were unrelated to outcome given the measured covariates, these ratios would be similar across groups. They are not. The excluded patients do better than predicted in the validation era and slightly worse in the development era.

**Potential selection bias.** The excluded patients differ from the analytic cohort in period, synchrony, metastasis size and recording practice. Their outcomes differ from what the measured covariates predict, and the direction changes between eras. Excluding them therefore cannot be assumed to be random: the analytic cohort is a selected population, especially for the earlier period. The estimates apply to patients who had complete staging recorded, which is more common in recent years and in certain centres. Complete-case analysis is valid only if missingness depends on the measured covariates alone. The data show that it does not, so this assumption cannot be verified. The effect on the hazard ratios of T, N and M cannot be quantified without outcome-informed imputation, which would itself rest on untestable assumptions.

## 6. Recommendation

**Keep the 17,262-patient TNM-complete cohort as the primary analysis.**

1. **TNM is the core predictor of the model.** The model cannot be estimated for the 8,832 excluded patients without assuming how their staging would have looked. The imputation tested earlier attenuated the TNM effects and could not be validated, so it cannot support the primary claims.
2. **The excluded patients are not missing at random.** Exclusion depends on period, synchrony, metastasis size, and centre, and the direction of the outcome difference changes between eras. A complete-case analysis is therefore the most transparent option, provided its limits are stated.
3. **The duplicate problem does not change the primary conclusions.** Removing the identical pairs or the broader set changes the C-index by 0.0000 and the 5-year survival by at most 0.1 percentage points. The groups are robust, but the registry data should be corrected.
4. **Report the no-TNM model as a complementary analysis** on all 11,967 validation patients (C 0.597), and state clearly that it discriminates less well (0.598 on the same 8,799 patients) and that it answers a different question: prediction when staging is unknown.
5. **Describe the selection explicitly.** Supplementary material should give the characteristics and outcomes of the excluded patients by era (A06–A10), and the limitations section should state that the analytic cohort over-represents recent operations and synchronous presentation.
6. **Do not publish the imputation results as primary.** At most they can appear as a sensitivity analysis, flagged as unvalidated.
7. **Before submission, ask the registry coordinators** to confirm the identical cross-country pairs and the 31 near-duplicate groups inside the cohort, and to explain the "ND" versus blank coding.

This recommendation keeps the smaller cohort because it is the population for which the model is valid and for which the primary claims can be verified. A larger cohort would only be defensible with outcome-informed imputation that the data cannot test. Reviewers of a surgical oncology prognostic study are likely to ask how selection was handled, so the primary analysis should be transparent about selection and should not rest on untestable imputation assumptions.

## Files

| File | Content |
|---|---|
| A00 | Duplicate summary |
| A01 | Identical-content pairs and the probable-duplicate rule |
| A02, A13 | Near-duplicate groups and field agreement |
| A03 | Duplicate sensitivity (cohort, survival, calibration, groups) |
| A04 | Deaths and the 15-year window |
| A05 | TNM model versus no-TNM model on the same patients |
| A06–A07 | Incomplete TNM by operation year, centre and country |
| A08 | Clinical characteristics, included versus excluded |
| A09 | Outcomes by era |
| A10 | Informative-selection test |
| A11 | Logistic model for TNM completeness |
| A12 | Summary |
