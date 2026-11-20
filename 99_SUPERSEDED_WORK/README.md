# Superseded work (kept for the record; not the final Paper 1)

These items are retained for audit and reproducibility. **They are not the current Paper 1 results.** Files are left in their original locations so that scripts and paths still work; this folder is an index.

## 1. Original binary-CART manuscript (superseded)
An earlier analysis used binary classification trees (CART) on TNM variables, with groups defined by median overall survival, an approximated recurrence-free survival, and a propensity-matched treatment comparison. The cohort was 14,759 patients.
- Results, preserved unchanged: [`results/historical_published/HISTORICAL_RESULTS.md`](../results/historical_published/HISTORICAL_RESULTS.md)
- Earlier analysis scripts: [`scripts/full_analysis_colab.py`](../scripts/full_analysis_colab.py), [`scripts/build_analysis_cohort.py`](../scripts/build_analysis_cohort.py)
- Earlier notebook package: [`notebooks/PACKAGE_README.md`](../notebooks/PACKAGE_README.md) and [`notebooks/LiverMets_PhD_Survival_Analysis.ipynb`](../notebooks/LiverMets_PhD_Survival_Analysis.ipynb)
- Earlier figure summary: [`figures/ASO_REVISIONS_SUMMARY.md`](../figures/ASO_REVISIONS_SUMMARY.md)
- Superseded results register: [`results/final_v7/SUPERSEDED_RESULTS.md`](../results/final_v7/SUPERSEDED_RESULTS.md)

Why superseded: the binary-CART approach and its median-OS groups were replaced by the stratified Cox model (M2a) with prognostic groups defined by predicted 5-year survival. The replacement and its reasons are in [`manuscript_v7/Cover_note.md`](../manuscript_v7/Cover_note.md).

## 2. Intermediate survival manuscript (v7) and earlier Paper 1 drafts
- Revised manuscript v7 (Cox, pre-v8): [`manuscript_v7/`](../manuscript_v7/)
- Earlier Paper 1 drafts and review packs: see [`manuscript_paper1/VERSIONS.md`](../manuscript_paper1/VERSIONS.md)

## 3. Earlier analysis iterations
Folders `results/final_v3` to `results/final_v6`, `results/final_evaluation`, `results/evaluation_v2`, `results/methods_comparison` and `results/audit_origins_recurrence` hold earlier iterations. Their status is described in `results/README.md`.
