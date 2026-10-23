# Change summary for supervisor: revised manuscript (v7)

**Files:** `Revised_manuscript_v7.docx` (editable), `Revised_manuscript_v7.md` (source), `figures/` (Figures 1–5), `build_manuscript.py` (rebuilds the document and checks every quoted number against the v7 output files).

## What the revision does
* **New title:** "Survival Modelling and Prognostic Groups for Colorectal Liver Metastases: Temporal Validation in an International Registry". The model uses clinical and operative variables as well as TNM, so "TNM-based" was removed.
* **Analysis:** the locked v7 analysis (stratified Cox M2a, training-only tertile cut-points, temporal validation). No analysis was changed. The v7 notebook ran end to end on the raw workbooks: 24 cells, 12 code cells, 0 errors. Ten reproduction checks against the validated analysis pass.
* **Treatment comparison:** removed, as agreed, because it has not been reproduced in v7. It is listed as a limitation.
* **Calibration:** reported transparently. Survival is under-predicted in validation (predicted 40.8% vs observed 46.6% at 5 years). Recalibration from recent data reduced but did not remove the gap, and no patient operated in 2016 or later has 5-year follow-up.
* **Figure 1 (STROBE flow):** generated from the v7 counts. Exclusions at each step are differences between consecutive counts.
* **Table 1 and Supplementary Table S1:** generated from the v7 cohort (17,262 analytic; 8,832 excluded for incomplete TNM).
* **Uncertainty documented:** recurrence dates and predictor timing have their own subsection and Table 4. The interval predictor is unavailable for 3,941 of 7,049 metachronous patients (55.9%). Pre-operative and resected metastasis counts agreed for 62.4% of patients with both recorded.
* **Verification:** 42 quoted numbers are checked against the output files at the precision written in the text. All 42 match (`results/final_v7/F35_manuscript_number_check.csv`).
* **Reporting:** STROBE and TRIPOD are cited; the structured abstract is 232 words (approximate count). Citations are numbered in order of first appearance.

## Decisions and items for you
1. **Checklists.** The STROBE and TRIPOD checklists must be completed and supplied with the submission.
2. **Author contributions.** The original statement records contributions for F.A., M.A.G. and M.B., but not for R. Adam. I have not added one. Please confirm each author's contribution.
3. **Ethics.** The original statement has no approval reference number. Please add one, or state that it does not apply.
4. **Citations.** Three statements are marked [CITATION NEEDED]. References 5 (TRIPOD) and 9 (Breslow discussion) are marked [TO CHECK] and should be verified against the originals. The reference list was rebuilt; the earlier 41 references were removed because they supported the superseded text.
5. **Journal rules.** Word limits, the structured-abstract format and figure requirements should be checked against the current Annals of Surgical Oncology author guidelines. I could not access them from here.
6. **Recurrence dates.** Confirm with the registry team that the dated recurrence fields are accurate. The earlier draft said they were unavailable. 41 recurrences are dated after the last contact and are classed as undated.

## Corrections made during this revision
* The earlier draft's operative-count figures (13,130 of 20,553; 3,179) could not be reproduced and are superseded by the analytic-cohort audit (`F34`).
* The earlier 34-patient interval figure is superseded by the audit (`F33`).
* Supplementary Table S1 was first drafted with the excluded group's direction reversed for synchronous presentation. This is corrected to 41.6% (excluded) vs 58.0% (analytic).
* Table numbering was corrected to run in order of appearance.
* The author-contribution statement for R. Adam was not in the original and has not been added.
