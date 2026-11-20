# Paper 1: change log (round 4)

Scope: label corrections, the Brier-score review and the final package. No change to the locked v8 Cox model (M2a), the 17,262-patient cohort, any numerical result, figure, table or conclusion, or the 12 limitations. No analysis was rerun.

## Corrections made
1. **Supplementary Table S2f** (page 2): the unsupported "pre-operative metastasis count" label is replaced by "first recorded metastasis count", with the registry variable names given in the title (LE1NBMETAHEPNUM and LE1NBMRESECNUM_F1). The row labels read "first recorded" and "resected" counts. Values are unchanged (14,189; 8,847 equal, 62.4%; 2,244 greater, 15.8%; 3,098 less, 21.8%).
2. **Supplementary Table S7** (page 7): the row "pre-operative (M1 structure) validation C" now reads "model without metastasis count and size (M1 structure), validation C". The value (0.5913) and PASS status are unchanged.
3. **Main text, Participants paragraph:** "Pre-operative and resected counts agreed for 62%..." now reads "First recorded and resected counts agreed for 62%...", so that the main text matches S2f. Word count rises by one word (3,498; limit 3,500).
4. **Outdated labels:** a search of the rebuilt main and supplementary PDF and Word text found no "pre-operative-only", "pre-operative metastasis count", "pre-operative (M1", "Draft for Supervisor Review", "TO CONFIRM", "TO VERIFY" or "CITATION NEEDED".

## Brier scores (Main Table 4): reviewed, values unchanged
- The calculation was checked against the notebook call and against the installed library (scikit-survival 0.28.0). The IPCW censoring distribution is estimated on the training cohort only, and the prediction inputs are the fixed M2a predictions at the same time grid.
- No calculation error was demonstrated. The 5-year value is documented for supervisor review in `Paper1_Brier_Score_Review_for_Supervisor.md`, together with the limits of independent verification (patient-level data are not in the repository).

## Checked and consistent
- Supplementary tables and figures match the main manuscript's numbers (75 of 75 headline checks pass: `scripts/final_submission_verification.py`).

## Formatting
- Main manuscript (11 pages) and supplementary (10 pages PDF; 9 pages Word) keep the round-3 typography and layout. The two changed supplementary pages (2 and 7) were checked visually.

## Not changed (deliberately)
- Ethics, consent, authorship, predictor timing and registry definitions remain marked as awaiting confirmation (see `Paper1_Outstanding_Issues_for_Supervisor.md`).
