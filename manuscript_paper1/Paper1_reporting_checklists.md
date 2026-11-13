# Reporting checklist: Paper 1 (TRIPOD+AI, STROBE, PROBAST+AI)

**Page references** refer to the combined review PDF (`Paper1_Full_Manuscript_Supervisor_Review.pdf`). The main manuscript occupies pages 1–13 and the supplementary material pages 14–25.

## 1. TRIPOD+AI (Collins et al., BMJ 2024;385:e078378): primary checklist

**Verification status.** The checklist structure was confirmed by search: item 1 (title), item 2 (abstract), items 3–4 (introduction), items 5–17 (methods), item 18 (open science), item 19 (patient and public involvement), items 20–24 (results), items 25–27 (discussion). The item-by-item wording could not be checked in this session, because the source PMC article is not reachable. **Individual sub-item numbers and wording must be entered from the official checklist before submission.** The mapping below is by domain and item range only.

| Item range | Domain | Manuscript location (PDF page) | Status |
|---|---|---|---|
| 1 | Title identifies the study as development and temporal validation of a prediction model | Title (p. 1) | Done |
| 2 | Abstract (structured, with design, data, performance and conclusions) | Abstract (pp. 1–2) | Done. Abstract checklist to be completed |
| 3–4 | Background, rationale and objectives | Introduction (p. 2) | Done. Intended clinical use is not defined (supervisor decision) |
| 5–17 | Methods: data sources and participants (p. 2); outcome (p. 3); predictors and their timing (p. 3); missing data and indicators (p. 3); sample size (p. 4); model development and selection rule (p. 4); risk groups (p. 4); validation design (p. 4); performance, calibration and censoring (p. 4); comparison with established scores (p. 4); software (p. 5) | pp. 2–5 | Done in substance. Predictor timing: unconfirmed (p. 3; confirmation note, section 4). Sub-item numbers to be entered |
| 18 | Open science: code, data and access | Software and code link (p. 5); Data Availability (p. 13) | Partly done. Registry access route to be confirmed (confirmation note, R3) |
| 19 | Patient and public involvement | **Not reported in the source documents.** Authors to state whether involvement occurred, or that none did | Authors to state (confirmation note, section 2) |
| 20–24 | Results: participants and flow (Figure 1, p. 7; Table 1, p. 8); model specification (Table 2, p. 8); performance and calibration (Table 4, p. 10; Figure 3, p. 10); risk groups (Table 3, p. 9; Figure 2, p. 9); supplementary analyses (p. 11) | pp. 5–11 | Done. Sub-item numbers to be entered |
| 25–27 | Discussion: interpretation, limitations, usefulness | Discussion (p. 12); Limitations (pp. 12–13); Conclusions (p. 13) | Done. Clinical usefulness is not demonstrated and is stated as such |

**Items specific to machine learning** (data partitioning for hyperparameter tuning, algorithm details, fairness, explainability) are **not applicable** to the stratified Cox model. Hazard ratios are reported in Table 2 and Supplementary Figure S2; baseline survival by stratum is in the coefficient outputs (Supplementary Material, p. 25).

## 2. STROBE (von Elm et al., Lancet 2007;370:1453–1457)

| Item | Manuscript location | Status |
|---|---|---|
| 1 Title and abstract | pp. 1–2 | Done |
| 2 Background and rationale | p. 2 | Done. Incidence statement removed pending a verified source (see confirmation note) |
| 3 Objectives | p. 2 | Done |
| 4 Study design | p. 2 | Done |
| 5 Setting | p. 2 | Partly done. Registry counts to be reconciled (confirmation note, R1) |
| 6 Participants | p. 2; Figure 1 (p. 7) | Done |
| 7 Variables | p. 3 | Done |
| 8 Data sources and measurement | p. 3 | Partly done. Data dictionary not available (confirmation note, R2) |
| 9 Bias | pp. 3, 12–13 | Done |
| 10 Study size | p. 4 | Done |
| 11 Quantitative variables | p. 3 | Done |
| 12 Statistical methods | p. 4 | Done |
| 13 Participants | Figure 1 (p. 7) | Done |
| 14 Descriptive data | Table 1 (p. 8) | Done |
| 15 Outcome data | Table 3 (p. 9) | Done |
| 16 Main results | pp. 5–11 | Done |
| 17 Other analyses | Supplementary Tables S3–S5 | Done |
| 18 Key results | p. 12 | Done |
| 19 Limitations | pp. 12–13 | Done |
| 20 Interpretation | p. 12 | Done |
| 21 Generalisability | pp. 12–13 (Limitation 12) | Done |
| 22 Funding | p. 13 | Done |

## 3. PROBAST+AI (Moons et al., BMJ 2025;388:e082505)

**Open.** The risk-of-bias judgements for the four domains (participants, predictors, outcome, analysis) have not been completed by the authors. Concerns to address explicitly: short validation follow-up (median 1.47 years); exclusion of 33.8% for incomplete staging; uncertain predictor timing; no external validation; proportional hazards not tested in validation.
