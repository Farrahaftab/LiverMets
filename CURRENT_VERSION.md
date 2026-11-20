# Current version record

**Version date:** 2026-11-20
**Status:** Paper 1 is a **Final Draft for Supervisor Approval**. It is not published and not ready for journal submission.

## Definitive Paper 1 files
All in [`01_PAPER_1_FINAL/`](01_PAPER_1_FINAL/):

| Document | Filename | Last changed in commit |
|---|---|---|
| Main manuscript (PDF, 11 pages) | `Paper1_ASO_Main_Manuscript_FINAL_DRAFT.pdf` | `c69a8ac` |
| Main manuscript (Word) | `Paper1_ASO_Main_Manuscript_FINAL_DRAFT.docx` | `c69a8ac` |
| Supplementary (PDF, 10 pages) | `Paper1_ASO_Supplementary_FINAL_DRAFT.pdf` | `c69a8ac` |
| Supplementary (Word) | `Paper1_ASO_Supplementary_FINAL_DRAFT.docx` | `c69a8ac` |
| Reporting checklists | `Paper1_Reporting_Checklists_FINAL.md` / `.docx` | `7d7ba27` (page note added in the folder copy) |
| Outstanding issues | `Paper1_Outstanding_Issues_for_Supervisor.md` | `4a82170` |

Main text: **3,498 words** (Introduction to Conclusions; excludes abstract, tables, legends, declarations and references). Limit 3,500. ASO's official counting rule has not been verified.

Source files: [`manuscript_paper1/final_for_supervisor_approval/`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/manuscript_paper1/final_for_supervisor_approval) (design HTML in `design_source/`) and [`manuscript_paper1/template_paper1_v2.md`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/manuscript_paper1/template_paper1_v2.md) with `build_paper1.py`.

## Locked analysis version
- **Model:** M2a stratified Cox model (strata: sex × synchrony × M-stage), 11 terms, fitted on the development cohort (operated 2009 or earlier). Validation: operated 2010 or later.
- **Code:** [`notebooks/LiverMets_final_reproducible.py`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/notebooks/LiverMets_final_reproducible.py) (the v8 notebook). Executed copy: [`notebooks/LiverMets_final_reproducible_v8_executed.ipynb`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/notebooks/LiverMets_final_reproducible_v8_executed.ipynb).
- **Locked outputs:** [`results/final_v7/`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/results/final_v7). Derived Paper 1 outputs: [`results/final_v9/paper1/`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/results/final_v9/paper1).
- **Verification:** [`results/final_v10/final_submission_check/verification.md`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/results/final_v10/final_submission_check/verification.md): 75 of 75 headline numbers match the locked outputs.
- **Cohort:** 17,262 patients (8,463 development; 8,799 validation).

No analysis has been refitted or changed in this organisation step.

## Remaining scientific issues (awaiting supervisor confirmation)
1. **Ethics:** approval reference or exemption, consent-waiver basis and centre-level approvals are not confirmed.
2. **Authorship:** R. Adam's contribution is not recorded; individual contributions and final approval by all authors are not confirmed.
3. **Funding and competing interests:** carried from the original draft; to be confirmed.
4. **Registry definitions:** 63 countries and 242 centres in the original text; 54 country codes and 288 site codes in the extract (259 sites with eligible patients).
5. **Predictor timing:** measurement time of metastasis count, size and TNM stage is undocumented; the intended clinical prediction time is not established.
6. **Brier score at 5 years (Table 4):** locked values are unchanged. The 5-year value cannot be recomputed from this repository (raw workbooks are not included). See `01_PAPER_1_FINAL/` documents and [`manuscript_paper1/final_for_supervisor_approval/Paper1_Brier_Score_Review_for_Supervisor.md`](https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/manuscript_paper1/final_for_supervisor_approval/Paper1_Brier_Score_Review_for_Supervisor.md).
7. **Journal requirements:** ASO word limit, display limit and reference style are unverified against the official instructions.

## Links to the latest files (branch `claude/livermetsurvey-phd-notebook-rz184z`)
- Main manuscript PDF: https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/01_PAPER_1_FINAL/Paper1_ASO_Main_Manuscript_FINAL_DRAFT.pdf
- Supplementary PDF: https://github.com/Farrahaftab/LiverMets/blob/claude/livermetsurvey-phd-notebook-rz184z/01_PAPER_1_FINAL/Paper1_ASO_Supplementary_FINAL_DRAFT.pdf

Note: the repository's default branch (`main`) does not yet contain these files. Use the links above, or ask for approval to merge.
