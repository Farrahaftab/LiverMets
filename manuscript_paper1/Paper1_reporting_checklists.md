# Reporting checklists — Paper 1 (revision 2)

**Primary checklist: TRIPOD+AI (Collins et al., BMJ 2024;385:e078378).** TRIPOD+AI supersedes TRIPOD 2015 and applies to regression models as well as machine-learning models, so it applies to the stratified Cox model. TRIPOD 2015 should no longer be used. An earlier draft of this checklist described TRIPOD+AI as machine-learning-only; that was wrong and has been corrected here.

**Item numbers.** The 27-item TRIPOD+AI checklist and its 13-item abstract checklist were identified by search, but the item-by-item text was not accessed from this session. The mapping below is by TRIPOD+AI domain. Item numbers must be entered from the official expanded checklist before submission. **[TO CONFIRM]**

Status key: **Done** = reported in the manuscript; **Partial** = reported with a stated limitation; **Open** = requires action before submission; **N/A** = not applicable to this model.

## 1. TRIPOD+AI, main checklist (by domain)

| Domain | Requirement (summary) | Where in manuscript | Status |
|---|---|---|---|
| Title and abstract | Identify as development and validation of a prediction model; report design, data, performance and conclusions | Title; Abstract (220 words) | Done. Confirm abstract checklist (13 items) before submission |
| Introduction | Rationale; intended use and population; objectives | Introduction, paragraphs 1–3 | Partial: intended clinical use is described only as stratification; no decision context named (see unresolved issues) |
| Methods: source of data | Describe data source, design and dates | Methods, Study design; Participants | Done |
| Methods: participants | Eligibility, setting, treatment and follow-up | Methods, Participants; Figure 1 | Done. Setting counts to reconcile (63/242 vs 54/288) **[TO CONFIRM]** |
| Methods: outcome | Define outcome, timing and ascertainment | Methods, Outcomes | Done. Death flag gap noted (Limitations 6) |
| Methods: predictors | Define predictors, measurement and timing | Methods, Outcomes and predictors | Partial. Predictor timing for metastasis count and size **unconfirmed** **[TO CONFIRM]** |
| Methods: sample size | Justify size | Methods, Model development | Done (4,675 development deaths; 11 candidate terms) |
| Methods: missing data | Describe missingness and handling | Methods, Participants; Predictors | Partial. Indicators and training medians; no multiple imputation for primary model; complete-case and MI shown for CEA only |
| Methods: statistical analysis | Model type, selection, estimation, validation approach | Methods, Model development to Performance | Done. Selection rule fixed before validation |
| Methods: risk groups | Describe how groups were derived and applied | Methods, Prognostic groups | Done |
| Methods: validation | Temporal split, data partition, evaluation | Methods, Model development | Done (temporal; no external validation) |
| Results: participants | Flow and characteristics | Results; Figure 1; Table 1; Tables S1–S2 | Done |
| Results: model | Full model specification and coefficients | Table 2 | Done (M2a, with baseline survival by stratum in S-output) |
| Results: performance | Discrimination and calibration with uncertainty | Table 4; Results, Model and discrimination; Calibration | Done. Bootstrap intervals for C and O/E; no decision-curve analysis |
| Results: risk groups | Group performance and separation | Table 3; Figure 2 | Done |
| Discussion: interpretation | Context, limitations, usefulness | Discussion; Limitations | Done |
| Discussion: usefulness | Clinical use, decision thresholds | Discussion | Partial. No clinician-defined thresholds; decision curve not produced; use is not recommended before recalibration |
| Other: supplementary | Code, data, supplementary material | Supplementary Material S1–S9; repository link | Done. Registry data access route to be confirmed |
| Other: funding and conflicts | Report | Declarations | Done |
| Other: registration or protocol | Report whether a protocol exists | None | **Open**: state whether a protocol or SAP was dated before validation results were seen |

## 2. TRIPOD+AI items specific to AI or machine learning

| Item group | Status |
|---|---|
| Data partitioning for machine-learning hyperparameter tuning | N/A (no tuning; the model was fixed by a pre-stated rule) |
| Algorithm and software details beyond regression | N/A (regression); software versions are reported |
| Fairness and subgroup performance | Partial. Performance is reported by period, decile and benchmark subset; not by sex or age group. **Open** if required by the journal |
| Explainability | Partial. Hazard ratios and baseline survival by stratum are reported |

## 3. STROBE (observational cohort, 22 items)

| Item | Where | Status |
|---|---|---|
| 1 Title and abstract | Title; Abstract | Done |
| 2 Background and rationale | Introduction | Done. One citation placeholder remains (incidence) **[CITATION NEEDED]** |
| 3 Objectives | Introduction, final paragraph | Done |
| 4 Study design | Methods, Study design | Done |
| 5 Setting | Methods, Participants | Partial (registry description to reconcile) |
| 6 Participants | Methods; Figure 1 | Done |
| 7 Variables | Methods, Outcomes and predictors | Done |
| 8 Data sources and measurement | Methods | Partial (no data dictionary; predictor timing unconfirmed) |
| 9 Bias | Methods, sensitivity analyses; Limitations | Done |
| 10 Study size | Methods, Model development | Done |
| 11 Quantitative variables | Methods, Predictors | Done |
| 12 Statistical methods | Methods | Done |
| 13 Participants | Figure 1; Results | Done |
| 14 Descriptive data | Table 1; Tables S1–S2 | Done |
| 15 Outcome data | Results; Table 3 | Done |
| 16 Main results | Results; Tables 2–5 | Done |
| 17 Other analyses | Supplementary Tables S3–S8 | Done |
| 18 Key results | Discussion | Done |
| 19 Limitations | Limitations | Done |
| 20 Interpretation | Discussion | Done |
| 21 Generalisability | Limitations 5 and 12 | Done |
| 22 Funding | Declarations | Done |

## 4. PROBAST+AI (risk of bias; Moons et al., BMJ 2025;388:e082505)

**Open.** The authors must complete the domain judgements for model development and evaluation (participants, predictors, outcome, analysis). Expected concerns to state explicitly: temporal validation with short follow-up in validation (median 1.47 years); exclusion of 33.8% for incomplete staging; uncertain predictor timing for count and size; no external validation; proportional hazards not tested in validation.
