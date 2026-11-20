# LiverMets: PhD research on prognostic survival in colorectal liver metastases

Research repository for my PhD in AI for Healthcare. The work develops and validates clinically interpretable survival models for patients who undergo liver resection for colorectal liver metastases (CRLM), using an international registry (LiverMetSurvey).

## Latest work: Paper 1

**Status: Final Draft for Supervisor Approval.** Not published. Not ready for journal submission until the items in the outstanding-issues list are confirmed.

**Title:** Prognostic Survival Prediction and Risk Stratification in Colorectal Liver Metastases: Development and Temporal Validation in an International Registry

**Purpose.** To develop a stratified Cox survival model from routinely recorded TNM and clinical variables, to define three prognostic groups from training-era predictions, and to test those groups in a later cohort with calibration reported.

**Main results** (temporal validation, 8,799 patients operated 2010 or later; model developed on 8,463 patients operated 2009 or earlier):
- Cohort: 17,262 patients with complete TNM staging, from 29,565 registry records.
- Discrimination: C-index 0.622 (95% CI 0.608–0.636). Modest.
- Prognostic groups (Favourable, Intermediate, Adverse) remained distinct: 5-year overall survival 62.9%, 45.4% and 34.3%.
- Calibration: predicted 5-year survival 40.8% against 46.6% observed, so the model under-predicts survival in recent patients and needs recalibration before clinical use.
- Limitations: no external validation; median validation follow-up 1.47 years; predictor measurement timing not confirmed.

### Where to find the latest manuscript

| Document | Link |
|---|---|
| **Main manuscript (PDF)** | [`01_PAPER_1_FINAL/Paper1_ASO_Main_Manuscript_FINAL_DRAFT.pdf`](01_PAPER_1_FINAL/Paper1_ASO_Main_Manuscript_FINAL_DRAFT.pdf) |
| Main manuscript (Word) | [`01_PAPER_1_FINAL/Paper1_ASO_Main_Manuscript_FINAL_DRAFT.docx`](01_PAPER_1_FINAL/Paper1_ASO_Main_Manuscript_FINAL_DRAFT.docx) |
| **Supplementary material (PDF)** | [`01_PAPER_1_FINAL/Paper1_ASO_Supplementary_FINAL_DRAFT.pdf`](01_PAPER_1_FINAL/Paper1_ASO_Supplementary_FINAL_DRAFT.pdf) |
| Supplementary material (Word) | [`01_PAPER_1_FINAL/Paper1_ASO_Supplementary_FINAL_DRAFT.docx`](01_PAPER_1_FINAL/Paper1_ASO_Supplementary_FINAL_DRAFT.docx) |
| Reporting checklists | [`01_PAPER_1_FINAL/Paper1_Reporting_Checklists_FINAL.md`](01_PAPER_1_FINAL/Paper1_Reporting_Checklists_FINAL.md) |
| Outstanding issues for supervisor | [`01_PAPER_1_FINAL/Paper1_Outstanding_Issues_for_Supervisor.md`](01_PAPER_1_FINAL/Paper1_Outstanding_Issues_for_Supervisor.md) |
| Current version record | [`CURRENT_VERSION.md`](CURRENT_VERSION.md) |

Branch: `claude/livermetsurvey-phd-notebook-rz184z` (the default branch `main` does not yet contain these files).

## Repository map

| Folder | Contents |
|---|---|
| [`01_PAPER_1_FINAL/`](01_PAPER_1_FINAL/) | **Latest Paper 1 documents** (start here) |
| [`manuscript_paper1/`](manuscript_paper1/) | Paper 1 source, build scripts and the design build (`final_for_supervisor_approval/`). Index of current and superseded files: [`VERSIONS.md`](manuscript_paper1/VERSIONS.md) |
| [`notebooks/`](notebooks/) | Locked v8 analysis notebook and its source (`LiverMets_final_reproducible.py`), earlier notebooks and their package notes |
| [`scripts/`](scripts/) | Analysis, cohort-building and verification scripts (including `final_submission_verification.py`) |
| [`results/`](results/) | Locked numerical outputs, verification reports and earlier iterations. Index: [`results/README.md`](results/README.md) |
| [`figures/`](figures/) | Figure generators and figure notes |
| [`manuscript_v7/`](manuscript_v7/) | Earlier revised survival manuscript (v7), superseded |
| [`99_SUPERSEDED_WORK/`](99_SUPERSEDED_WORK/) | Index of superseded work, including the original binary-CART analysis. Not the final Paper 1 |

## Reproducibility

- Analysis code: `notebooks/LiverMets_final_reproducible.py` (locked v8 analysis).
- Locked outputs: `results/final_v7/` (with derived Paper 1 outputs in `results/final_v9/paper1/`).
- Verification: `scripts/final_submission_verification.py` checks 75 manuscript numbers against the locked outputs (75 of 75 pass).
- The registry workbooks are not included, so the notebook cannot be run end to end from this repository. Access is governed by the LiverMetSurvey collaboration. No patient-level data are stored here.

## Superseded work

The original analysis used binary classification trees (CART) with median-OS groups on 14,759 patients. It has been replaced by the stratified Cox model (M2a). Its results are kept for the record in `results/historical_published/` and indexed in [`99_SUPERSEDED_WORK/README.md`](99_SUPERSEDED_WORK/README.md). It is not the final Paper 1.

## Open items

Ethics approval and consent basis, author contributions, funding and competing interests, registry definitions, predictor timing and the 5-year Brier value are awaiting supervisor confirmation. See the outstanding-issues list linked above.
