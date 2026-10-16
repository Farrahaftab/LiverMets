# Reproducibility report: LiverMets CRLM survival analysis

Generated 2026-10-16 13:45 by running the notebook top to bottom. Every number below is read from files written by the notebook.

## 1. Input data and combination

* Input files: `LiverMet_Part1.xlsx` and `LiverMet_Part2.xlsx` (SHA-256 in `logs/input_hashes.json`).
* Part 1: 14,782 patient rows, header at Excel row 2 (row 1 blank).
* Part 2: 14,783 patient rows, **no header** (row 1 blank), aligned to the Part 1 column template.
* Combined: **29,565 patients** (expected 29,565). The header row is not a patient; if it were counted the total would read 29,566.
* Column names: 13,658 in the header, all unique. Full inventory: `tables/T01_column_inventory.csv`.
* Analysis extract: 106 columns, written to Parquet in batches of 2,000 rows (streamed; the full sheet is never held in memory).

## 2. Dates

Clinical dates are stored twice: the original Excel serial (`*_RAW`) and the calendar date (`*_DATE`). The day, month and year component columns agree with the serial value in every case (`tables/T02_date_preservation_check.csv`).

## 3. Cohort

```
                                               step     n  excluded_from_previous
                   All patients in combined extract 29565                       0
TNM complete (T, N and M stage recorded, not ND/NA) 19465                   10100
   ...and liver metastasis diagnosis date available 13588                    5877
   ...and valid OS (known status, date > time zero) 13285                     303
```

The TNM-complete count reproduces the earlier published flow (19,465 retained, 10,100 excluded). The survival-eligible count does not reproduce the earlier 14,759. The earlier value came from a derived dataset (SURVIVAL_YEARS, VITAL_STATUS) that is not in this repository, so it cannot be reproduced exactly. This notebook derives follow-up from dates (see section 4).

## 4. Variable definitions (all derived in the notebook)

* **Time zero:** date of first liver metastasis diagnosis (`LE1DGMETADT`).
* **OS:** days from time zero to last contact (`LASTNDTC`); event = `PATSTATC` = Deceased; Alive and Lost to follow-up are censored. Truncated at 15 years.
* **RFS:** recurrence date (earliest of `RECDT_F1`-`RECDT_F7`) if recorded; otherwise death or last contact. `alive_with_disease_no_date` (status from `PATSTAT_F1`) is an event at last contact, which is a known approximation.
* **TNM groups:** T1-2 (incl. T0), T3, T4 (incl. T4a/b); N0, N1 (incl. a/b/c), N2; M0, M1 (incl. a/b/c).
* **Phenotypes:** survival tree on TNM groups, training era only; terminal nodes labelled from KM median OS with the earlier thresholds (6 and 5 years).
* **Phenotype note:** no patients were assigned to Favourable under the pre-specified thresholds (highest training-node median OS = 5.83 years). Analyses use the observed groups only; thresholds were not changed to create a group.
* **Treatment:** hepatectomy (`LE1HEPATECTYN_F1`) and peri-operative systemic chemotherapy (`LE1PREOPMCTYN_F1` or `LE1POSTOPMCTYN_F1`).
* **Metastases count:** values outside 1-50 set to missing; **size:** outside 1-300 mm set to missing; **CEA:** `LE1PREHEPCEA_F1` in ng/mL.
* `TIMELAST` is not used. It does not equal any date difference in the export and has negative values (`tables/T03_timelast_qc.csv`).

## 5. Results

### Phenotypes and survival

```
       group      n  events  median_years  S_1y  S_3y  S_5y    logrank_p
  Favourable    NaN     NaN           NaN   NaN   NaN   NaN 2.389080e-36
Intermediate 3580.0  1097.0          6.09 0.957 0.768 0.578 2.389080e-36
     Adverse 9705.0  3824.0          4.08 0.940 0.638 0.423 2.389080e-36
```

### Cox model (treatment)

```
        term                                                    model    n  events   coef    HR  HR_lower95  HR_upper95     p  c_index_apparent
      PH_ADV Multivariable OS: phenotype + treatment (complete cases) 9569    3567  0.418 1.519       1.404       1.645 0.000             0.609
TX_SURGCHEMO Multivariable OS: phenotype + treatment (complete cases) 9569    3567 -0.284 0.753       0.692       0.819 0.000             0.609
TX_CHEMOONLY Multivariable OS: phenotype + treatment (complete cases) 9569    3567  0.483 1.622       1.398       1.881 0.000             0.609
  TX_NOTREAT Multivariable OS: phenotype + treatment (complete cases) 9569    3567  0.702 2.018       1.610       2.529 0.000             0.609
      AGE_10 Multivariable OS: phenotype + treatment (complete cases) 9569    3567  0.106 1.112       1.076       1.148 0.000             0.609
        MALE Multivariable OS: phenotype + treatment (complete cases) 9569    3567 -0.002 0.998       0.933       1.069 0.964             0.609
        METS Multivariable OS: phenotype + treatment (complete cases) 9569    3567  0.044 1.045       1.036       1.055 0.000             0.609
```

### Model performance (C-index, time-dependent AUC, Brier)

```
                                                                    model  C_index  tAUC_1y  tAUC_3y  tAUC_5y  Brier_1y  Brier_5y  IBS_1_to_7y
                                 Phenotype rank [Internal (random 70/30)]   0.5488   0.5364   0.5696   0.5763       NaN       NaN          NaN
                               Cox (prognostic) [Internal (random 70/30)]   0.6277   0.6763   0.6560   0.6569    0.0487    0.2347       0.1968
                         Random survival forest [Internal (random 70/30)]   0.6315   0.6800   0.6598   0.6545    0.0480    0.2352       0.1970
                      Gradient-boosted survival [Internal (random 70/30)]   0.6271   0.6673   0.6552   0.6523    0.0490    0.2367       0.1977
                              Fong CRS (subset) [Internal (random 70/30)]   0.5804   0.5752   0.6023   0.5867       NaN       NaN          NaN
            Nordlinger-type unweighted (subset) [Internal (random 70/30)]   0.5637   0.5721   0.5801   0.5860       NaN       NaN          NaN
                     Phenotype rank [Temporal (<=2009 train, >2009 test)]   0.5496   0.5208   0.5619   0.5981       NaN       NaN          NaN
                   Cox (prognostic) [Temporal (<=2009 train, >2009 test)]   0.6540   0.6886   0.6819   0.7082    0.0345    0.0682       0.0722
             Random survival forest [Temporal (<=2009 train, >2009 test)]   0.6499   0.6850   0.6786   0.7032    0.0341    0.0692       0.0728
          Gradient-boosted survival [Temporal (<=2009 train, >2009 test)]   0.6583   0.7009   0.6868   0.7089    0.0345    0.0686       0.0724
                  Fong CRS (subset) [Temporal (<=2009 train, >2009 test)]   0.5841   0.5598   0.6171   0.5974       NaN       NaN          NaN
Nordlinger-type unweighted (subset) [Temporal (<=2009 train, >2009 test)]   0.5794   0.5867   0.5865   0.6108       NaN       NaN          NaN
```

### Propensity-score matched treatment comparison

```
   phenotype                        note  n_treated  n_control  n_treated_pool  n_control_pool  matched_pairs  caliper_logit  HR_SurgChemo_vs_SurgOnly  HR_lower95  HR_upper95  HR_p_robust    logrank_p  RMST_5y_SurgChemo  RMST_5y_SurgOnly  RMST_diff_5y  RMST_diff_5y_boot_lo  RMST_diff_5y_boot_hi
  Favourable too few patients in one arm        0.0        0.0             NaN             NaN            NaN            NaN                       NaN         NaN         NaN          NaN          NaN                NaN               NaN           NaN                   NaN                   NaN
Intermediate                         NaN        NaN        NaN          2194.0           707.0          629.0         0.1938                     0.808       0.665       0.981 3.120652e-02 3.393907e-02              4.166             3.942         0.224                 0.035                 0.409
     Adverse                         NaN        NaN        NaN          6090.0          1706.0         1561.0         0.1891                     0.695       0.621       0.778 2.712906e-10 3.248362e-10              3.865             3.460         0.405                 0.278                 0.523
```

### Sensitivity analyses

```
                                                 analysis     n  events  HR_PH_ADV     p_PH_ADV  HR_TX_SURGCHEMO  p_TX_SURGCHEMO
Primary analysis (time zero = liver metastasis diagnosis)  9569    3567      1.519 4.171729e-25            0.753    4.326338e-11
                      Time zero = referral date (REFERDT)  8477    3026      1.517 2.698110e-21            0.766    1.680607e-08
                             Metachronous metastases only  3880    1412      1.534 2.434295e-13            0.791    1.295478e-04
                          Follow-up truncated at 10 years  9569    3540      1.530 1.301386e-25            0.751    3.476288e-11
                               Training era only (<=2009)  5025    2595      1.445 2.805001e-15            0.792    2.167036e-06
                              Validation era only (>2009)  4544     972      1.770 2.407623e-12            0.667    6.135835e-06
                           Recurrence-free survival (RFS)  9569    5403      1.476 1.160943e-32            0.844    2.622876e-06
    Chemotherapy includes post-colectomy adjuvant therapy 10243    3837      1.520 1.014271e-26            0.729    2.676033e-08
```

## 6. Limitations and deviations from the earlier analysis

* Earlier published derived variables (SURVIVAL_YEARS, VITAL_STATUS, TREATMENT, NB_METASTASES_NUM) were not available. Their definitions are replaced by the date-based definitions above, so results will not match the earlier numbers exactly.
* The earlier RFS used overall-survival time and an F1-only status mapping. This notebook uses recurrence dates where recorded.
* The earlier phenotypes came from a binary CART with the outcome in the same data. Here the survival tree is grown on the training era and then applied to the validation era.
* Basingstoke Predictive Index is not computed (tumour differentiation grade not in the export). The Nordlinger score is reported only as a Nordlinger-type unweighted count.
* Counts from `ND`/`NA` are treated as missing; no imputation is used for the cohort or the treatment comparison. Machine-learning models use training-set median imputation with missing indicators.
* Treatment is determined after time zero; the treatment comparison is therefore observational and is checked with a 6-month landmark analysis, which does not remove all bias.
* Patient-level working data are in `WORK_DIR` and are not part of the results package.

## 7. Environment and reproducibility

```json
{
  "python": "3.13.16",
  "platform": "Linux-6.18.44-fc-v139-x86_64-with-glibc2.39",
  "pandas": "2.3.3",
  "numpy": "2.5.3",
  "lifelines": "0.30.3",
  "scikit-survival": "0.28.0",
  "scikit-learn": "1.9.1",
  "matplotlib": "3.11.2",
  "seed": 42
}
```
