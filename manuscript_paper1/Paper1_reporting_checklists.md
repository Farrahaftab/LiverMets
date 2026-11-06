# Reporting checklists — Paper 1 (draft)

**Scope.** The model is a stratified Cox regression, not a machine-learning model. TRIPOD (2015) is therefore the primary checklist. TRIPOD+AI (2024) is mapped as a secondary check because it updates the general items. PROBAST (and PROBAST+AI for the risk-of-bias judgement) should be completed by the authors. **[TO CONFIRM with supervisor: which TRIPOD version the journal requires.]**

Status key: **Done** = reported in the manuscript; **Partial** = reported with a limitation; **Open** = needs action before submission.

## STROBE (observational cohort)

| Item | Where | Status |
|---|---|---|
| 1 Title/abstract | Title, Abstract | Done |
| 2 Background/rationale | Introduction | Done (one citation placeholder left, see review pack) |
| 3 Objectives | Introduction, last paragraph | Done |
| 4 Study design | Methods, Study design | Done |
| 5 Setting | Methods, Participants; registry description | Partial: country/centre counts to reconcile (63/242 vs 54/288 site codes) |
| 6 Participants (eligibility, follow-up) | Methods, Participants; Figure 1 | Done |
| 7 Variables (outcomes, predictors) | Methods, Outcomes and predictors | Done |
| 8 Data sources and measurement | Methods | Partial: data dictionary not available; predictor timing unconfirmed |
| 9 Bias | Methods, sensitivity analyses; Limitations | Done |
| 10 Study size | Results, Model development; Methods | Done (4,675 deaths in development) |
| 11 Quantitative variables | Methods, Predictors | Done |
| 12 Statistical methods | Methods | Done |
| 13 Participants flow | Figure 1; Results | Done |
| 14 Descriptive data | Table 1; Table S1 | Done |
| 15 Outcome data | Results; Table 4 | Done |
| 16 Main results | Results | Done |
| 17 Other analyses | Sensitivity Table 6; benchmarks Table 7 | Done |
| 18 Key results | Discussion | Done |
| 19 Limitations | Limitations | Done |
| 20 Interpretation | Discussion | Done |
| 21 Generalisability | Limitations 5 and 11 | Done |
| 22 Funding | Declarations | Done (none) |

## TRIPOD (2015), development and validation of a prediction model

| Item | Where | Status |
|---|---|---|
| 1 Title | Title | Done |
| 2 Abstract | Abstract | Done |
| 3 Background and objectives | Introduction | Done |
| 4 Source of data | Methods, Study design | Done |
| 5 Participants | Methods; Figure 1 | Done |
| 6 Outcome | Methods, Outcomes | Done |
| 7 Predictors | Methods, Predictors | Done (timing Partial) |
| 8 Sample size | Methods, Model development | Done |
| 9 Missing data | Methods, Predictors; Table S5 | Partial: indicator method, no multiple imputation for primary model |
| 10 Statistical analysis | Methods, Model development | Done |
| 11 Risk groups | Methods, Prognostic groups | Done |
| 12 Development vs validation | Methods; Results | Done (temporal split) |
| 13 Results of model | Table 3; Results | Done |
| 14 Model performance | Table 2; Results | Done |
| 15 Model updating | Results, calibration; Discussion | Done (recalibration sensitivity; primary not recalibrated) |
| 16 Interpretation | Discussion | Done |
| 17 Limitations | Limitations | Done |
| 18 Supplementary | Supplementary Material | Done |
| 19 Funding | Declarations | Done |
| 20 Registration / protocol | Not registered | **Open**: state whether a protocol exists |

## TRIPOD+AI (2024), general items relevant to a regression model

| Item | Status |
|---|---|
| Machine-learning-specific items (data partition, hyperparameters, fairness) | Not applicable to the locked Cox model; state this explicitly in the submission |
| Code and data availability | Done (repository link); data restricted, **Open**: confirm registry access route |
| Calibration and clinical utility | Partial: no decision-curve analysis; clinician thresholds not defined (see review pack) |

## PROBAST / PROBAST+AI (risk of bias)

**Open.** The authors must complete the PROBAST domain judgements (participants, predictors, outcome, analysis). Expected concerns to address explicitly: temporal validation with short follow-up; 33.8% exclusion for incomplete staging; uncertain predictor timing for count and size; no external validation.
