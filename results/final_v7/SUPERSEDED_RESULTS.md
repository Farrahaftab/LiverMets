# Superseded results register (v7)

These earlier results are retained for audit only. Do not cite them in the manuscript. The current results are in `results/final_v7/` and `notebooks/LiverMets_final_reproducible.ipynb`.

| Earlier result | Where | Why superseded | Replacement (v7) |
|---|---|---|---|
| Matched-treatment KM figure (Intermediate and Adverse only; Favourable omitted) | `results/figures/F08_KM_matched_treatment_by_phenotype.png` (main notebook) | Uses tree-leaf phenotypes, not the M2a Cox groups. Favourable has zero patients in the treatment pool, so it is skipped | Not regenerated in v7. Any treatment comparison by Cox group must be re-run and labelled. Do not cite the current figure |
| Survival-tree phenotype figures | `results/figures/F01–F09` (main notebook) | Tree-based phenotypes from the earlier analysis, not the M2a Cox groups | Cox M2a figures `results/final_v7/figures/COX_01–04` |
| Reproducibility report generated 16 October 2026 (13,285 survival-eligible; older flow) | `results/reproducibility_report.md` | Written from an earlier run; flow and survival counts do not match the final cohort | `results/final_v7/REPRODUCIBILITY_REPORT.md` |
| v6 day-convention sensitivity (first-day and month-end agreement 99.64% and 99.95%; primary cut-points 0.3794 / 0.4755) | `results/final_v6/F19_sensitivity_same_day_and_date_conventions.csv` (`notebooks/sensitivity_v6.py`) | Used a separate inline baseline-hazard routine, so its primary row (cut-points 0.3794 / 0.4755) does not match the primary analysis (0.3793 / 0.4756) | v7 `F10_day_and_same_day_conventions.csv`: first-day agreement 99.71%, month-end 99.98%, one routine for all rows |
| v6 F10 phenotype-agreement table (33% agreement) | `results/final_v6/F10` (deleted) | Compared groups built from different models (invalid) | v7 `F10` |
| v6 calibration and phenotype figures | none saved in v6 | Not produced | v7 `COX_03`, `COX_04` |
| "Calibration by period shows temporal drift" (v7 F21 period O/E 1.23 for 2013–2015) | `results/final_v7/F21` | Rests on 109 patients with 5-year follow-up. Kept as a provisional observation, not an established finding | Stated as provisional in the report, section 9 |
| Observed 5-year survival for 2016+ period | early v7 run, `F21` | Not estimable: no patient has 5-year follow-up. Earlier output repeated the last KM value | Suppressed (NaN) in the final run; period 2016+ omitted from the figure |
| Pre-operative-only C 0.591 described as "poor" with calibration slope 1.36 | `results/final_v6/F14` | Correct values, but the M1 structure was used. The like-for-like M2a-structure model gives C 0.5905, slope 1.31 | Both reported in v7 `F14` and `F23` |
| Same-day death sensitivity as "11 uncertain deaths" in the modelling cohort | v6 notes | 11 is the count across all 19 same-day deaths. In the modelling cohort it is 7 unflagged of 13 same-day deaths | v7 `F18`, `F19` |
| Cohort 18,158 (surgery origin, superseded) | `results/final_v3` | Included patients without hepatectomy and outside inclusion criteria | 17,262 TNM-complete (v7) |
| M1 validation C 0.625 on 18,158 cohort | `results/final_v3` | Superseded cohort | 0.6216 (M2a, n = 8,799) |
| "M1 passes the PH rule" | `results/final_v3`, `final_v4` | M-stage PH test fails (p = 0.031) | M2a selected (v7 `F03`, `F05`) |
| Interval predictor for patients whose liver metastasis was diagnosed after operation | `results/final_v4` | Not known at time zero | Set missing (v7 build) |
| RFS median 1.76 (count-based events) | `results/final_v4` | Counted alive-with-disease as events | RFS 2.03 (primary, v7 `F17`) |
| Operation-date rule = 1st of month for all partial dates | `results/final_v4` | Does not reproduce report counts at steps 6–7 | 15th-of-month rule (v7 `F01`) |
| Modelling cohort 17,265 (day-1 rule) | `results/final_v4` notes | Day-1 rule; 17,265 is the first-day sensitivity | 17,262 primary (v7) |
