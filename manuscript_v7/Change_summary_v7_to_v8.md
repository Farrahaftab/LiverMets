# Summary of changes: v7 to v8

## Primary analysis: unchanged
* Model: stratified Cox M2a, selected by the pre-specified PH rule. Not refitted or re-specified.
* Cohort: 17,262 TNM-complete patients (8,463 development; 8,799 validation).
* Validation C-index: 0.6216. Training-only cut-points 0.3793 and 0.4756.
* Groups (validation): Favourable 2,662; Intermediate 2,824; Adverse 3,313.
* Verified: the primary outputs F00–F23 are byte-identical to the v7 freeze. The reproduction check passes 10 of 10 (F25).

## Notebook (`notebooks/LiverMets_final_reproducible.py`, executed copy `LiverMets_final_reproducible_v8_executed.ipynb`)
* 30 cells: 15 code cells, all executed with no errors.
* Extraction: four identifier columns (`COUNTRY_ID`, `SITE_ID`, `CENTER`, `NUMPAT`) added. They are excluded from the duplicate hash and do not enter any model.
* Cohort frame: country and site carried through (no change to values).
* Death labels corrected (F12): the row counting 69 "deaths" now reads as patients, and separate rows give 6,601 recorded deaths, 6,591 events inside the window, 10 deaths beyond 15 years, and 69 patients beyond 15 years (10 died, 59 alive or lost).
* New section 11: duplicate-record screen and sensitivity (F60, F61).
* New section 12: no-TNM model on the same patients and the broader cohort (F62).
* New section 13: incomplete-TNM patients by period, centre, country, characteristics, outcomes and informative-selection check (F63–F68).
* Figures and reproduction check renumbered as section 14. The reproduction check is unchanged.

## Corrections made during v8
1. **Death count.** The 69-patient label was misleading; corrected in the notebook and manuscript. Table 1 now reports 6,601 recorded deaths and 6,591 window events separately (F31, F32).
2. **Exclusion percentage.** 8,832 of 26,094 is 33.8%, not 33.9% as previously written. Corrected throughout.
3. **Duplicate rule.** The notebook's first v8 run used the raw operation date, which is blank for one Spanish pair, so that pair failed the rule and the count was 15. The rule now uses the year-and-month-filled date, matching the audit: 16 probable pairs.
4. **Investigation stage C.** Its complete-case reference used medians from all development patients. Corrected to TNM-complete medians. The complete-case hazard ratios were unchanged; the duplicate-removed C-index moved from 0.6214 to 0.6216.

## Supplementary material (new)
* S2: missing T/N/M components and reasons (F45, F46).
* S3: duplicate-record screen and sensitivity (F60, F61).
* S4: no-TNM model (F62). On the same 8,799 validation patients, C 0.6216 (TNM) vs 0.5994 (no-TNM), difference 0.022 (95% CI 0.009–0.034). Broader no-TNM model: 0.5982 on the same patients; 0.5972 on all 11,967 validation patients (not directly comparable).
* S5: incomplete-TNM patients (F63–F68).

## Manuscript (Word file regenerated)
* Methods: exclusion steps; death and follow-up window definitions; duplicate handling; no-TNM model design.
* Results: new section on patients excluded for incomplete staging; new section on duplicates and the no-TNM model; Table 1 death rows.
* Discussion: selection-bias paragraph, worded as raising concern rather than establishing non-random missingness.
* Limitations: death-flag pattern; selection and missing staging; possible duplicates. Numbering runs 1–12.
* Abstract: 249 words; adds the no-TNM C-index and the selection concern.
* Build checks: 94 quoted numbers verified against their source files (F35).

## Not changed
* No new model, cut-off, horizon or prognostic group was introduced.
* Option B, GAME, TBS and the feasibility recommendations are not implemented; they remain proposals (see the feasibility report).
