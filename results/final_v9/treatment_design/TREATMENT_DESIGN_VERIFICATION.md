# Treatment-effect design verification: pre-operative liver chemotherapy versus none

**Status.** Design verification only. No treatment-effect model has been fitted, the locked v8 Cox model and its three prognostic groups (Favourable, Intermediate, Adverse) are unchanged, and the manuscript has not been updated. The prognostic groups were recomputed from the v8 specification and reproduce the locked cut-points (0.3793 and 0.4756) exactly. They are used here only to check whether they could serve as effect modifiers.

Outputs: tables J01–J05 in this folder (aggregate). Scripts: `notebooks/treatment_design_v9.py` and `notebooks/treatment_feasibility_v9.py`. Patient-level working files are outside the repository.

## Summary of findings

1. The locked model and groups are unchanged, and the proposed comparison is defined among patients who reached hepatectomy.
2. The proposed primary comparison is feasible in size: 16,371 patients with known status (7,485 treated; 8,886 untreated).
3. **The data dictionary is not available** in the workbook (one sheet, "Data"), the repository or the uploads. The timing of the metastasis count and size therefore cannot be confirmed from documentation.
4. An indirect test gives no clear evidence that chemotherapy changed recorded counts, but it cannot rule it out. The locked risk groups therefore **cannot yet be validly used** as effect modifiers.
5. Identifiability of a causal treatment effect is doubtful from these fields. The target-trial framing does not remove confounding by indication, which is severe.
6. Overlap is adequate in the overall population but weak in parts of the Adverse group. Matching or weighting should target the treated population.
7. **Recommendation:** keep the treatment question out of the current prognostic paper's primary aims. Pursue it as a separate, carefully scoped analysis once the data dictionary and richer covariates are available.

## 1. Locked analysis and risk groups

The risk groups were rebuilt with the v8 specification and reproduce the locked cut-points exactly (0.3793, 0.4756). Group sizes among patients with known pre-operative status: Favourable 5,193; Intermediate 5,359; Adverse 5,819 (J03). Nothing about the model, the groups or their thresholds has been changed.

## 2. Proposed primary comparison

**Question.** Among patients who underwent hepatectomy, is pre-operative systemic chemotherapy for liver metastases associated with overall survival compared with no pre-operative chemotherapy?

**Population.** Patients in the v8 analytic cohort (17,262) with recorded pre-operative status (Yes or No): **16,371**. Excluded: 759 ND and 132 blank (891; 5.2%), reported as a separate group in any sensitivity analysis (J05).

**Why this comparison and not "surgery alone".** The fields do not identify a "surgery alone" group. "No pre-operative chemotherapy" includes patients who received chemotherapy only after surgery (post-operative only: 4,096 in the cohort) and those with no recorded chemotherapy. The comparator must be named accordingly.

## 3. Timing of the risk-group predictors

**Data dictionary.** Not available in any file provided. Field meanings such as "LE1NBMETAHEPNUM" (pre-operative count), "LE1NBMRESECNUM_F1" (count resected), "LE1HEPMETASIZENUM" (size), and their "_V" variants are inferred from names and coding only. Their recording time (at diagnosis imaging, at restaging after chemotherapy, or at the operation) is **not confirmed**.

**Indirect test (J01).** If the pre-operative count had been recorded after chemotherapy had reduced disease, treated patients would more often show fewer resected lesions than counted before surgery. Across patients with both counts (14,199):

| Pre-operative chemotherapy | n | Resected lower than pre-operative count | Mean pre-operative count |
|---|---|---|---|
| No | 7,625 | 12.3% | 1.79 |
| Yes | 6,213 | 22.5% | 2.51 |

The treated group had more lesions before surgery. Within each pre-operative count stratum the gap is small and not consistent in direction:

| Pre-operative count | No: resected lower | Yes: resected lower |
|---|---|---|
| 1 | 0.4% | 0.7% |
| 2 | 20.3% | 22.9% |
| 3 | 30.2% | 36.9% |
| 4 or more | 38.1% | 36.3% |

**Interpretation.** The crude difference is largely explained by lesion count, which is itself a risk factor for both chemotherapy use and survival. Within strata there is at most a modest excess among treated patients (for example, 30% vs 37% at count 3). This is compatible both with chemotherapy shrinking lesions before the count was recorded and with imaging over-counting in patients who already had more disease. The test cannot separate these explanations.

**Operative size.** An operative size field exists (LE1HEPATECTNO_F1_CSIZ) but is recorded for only 354 records, and the other size fields are sparse, so size timing cannot be checked at all.

**Conclusion on timing.** Unresolved. The timing must be confirmed from the registry data dictionary or the case-report form before any analysis uses metastasis count or size as a confounder or effect modifier.

## 4. Can the three risk groups be used for effect modification?

**Not validly, at present.**

* The groups are built from TNM, age, sex, synchrony, interval, pre-operative count and pre-operative size (plus era terms in the model). Count and size are the two variables whose timing is unconfirmed (section 3).
* If count or size were recorded after pre-operative chemotherapy, the groups are partly post-treatment and would be inappropriate as effect modifiers. Adjusting for them would bias the treatment estimate.
* Even if timing is confirmed as pre-treatment, the groups are a **prognostic** classification, validated for prognosis. Prognostic strata do not automatically define the treatment-effect heterogeneity of interest. Treatment is strongly associated with group membership (section 5), so within-group comparisons still need the same confounding control.

**What a valid alternative would require.** A baseline-only risk classification would need:
1. **Only variables recorded before any treatment**: primary TNM, age, sex, synchrony, interval, and pre-operative CEA if its timing is confirmed. No metastasis count or size unless timing is verified.
2. **A new model**, developed on the development era and evaluated on the validation era, with its own cut-points. This is new modelling and would require your approval.
3. **Pre-specification** as an effect-modifier analysis before any treatment model is fitted.
4. **Its own name and validation.** It cannot be presented as the three validated Favourable, Intermediate and Adverse groups, which remain prognostic.

## 5. Eligibility, time zero, confounders, missing data and selection

**Eligibility.** Hepatectomy recorded; TNM complete; pre-operative status recorded (Yes or No). Analysis population 16,371.

**Time zero.** The hepatectomy date (LE1OPERDT_F1; partial dates as in v8, 15th of the month). Pre-operative chemotherapy is fixed before time zero: 4,259 of 4,320 dated pre-operative starts (98.6%) precede the operation. Exposure is therefore defined at time zero, and this avoids immortal-time bias for the pre-operative exposure. Post-operative chemotherapy would not be fixed at time zero and is excluded from the primary comparison.

**Candidate confounders (recorded before treatment).**
* Age, sex, primary T, N and M stage.
* Synchronous presentation; interval from primary diagnosis to liver metastasis, with a missing indicator.
* Pre-operative CEA (65.8% recorded), with a missing indicator, if its timing is confirmed.
* Era (operated 2010 or later).
* **Primary-tumour pre-operative chemotherapy (PRECOLCHIYN, 93% recorded) and radiotherapy (PRECOLRADYN, 92% recorded).** These precede surgery and are candidate confounders that the earlier plan did not include.
* Metastasis count and size, **only if** their timing is confirmed as pre-treatment.

**Excluded as confounders (post-treatment or post-operative).** Post-operative liver chemotherapy; post-operative primary-tumour chemotherapy (its start is mostly before the liver operation, so its timing is mixed); resection margin (60% recorded, post-operative); lymph-node count from the primary; response and toxicity fields; regimen details (recorded for 35–39%, and only for patients given the drug).

**Missing treatment data.** 891 patients (5.2%) have ND or blank pre-operative status. Their exclusion from the primary analysis is not random: they are concentrated in some centres (8 of 248 centres have half or more unknown status; v9 feasibility H08) and in the development era (14.1% vs 12.2% unknown). A sensitivity analysis treating ND as "no pre-operative chemotherapy" gives an upper bound on misclassification.

**Consequences of selecting only patients who reached surgery.**
* The cohort conditions on being resected. Patients whose disease progressed during chemotherapy, or who were judged inoperable, are absent.
* The comparison therefore estimates a contrast among resected patients, not the effect of offering chemotherapy to all resectable patients.
* Chemotherapy may change who reaches surgery. If unmeasured factors affect both treatment choice and the chance of resection, selection on surgery introduces bias that adjustment cannot remove.
* The registry contains no non-resected patients, so this selection cannot be quantified.

## 6. Positivity and overlap

**Propensity model (diagnostic only).** Logistic regression of pre-operative chemotherapy on the candidate confounders available in every patient (age, sex, synchrony, interval, count and size with missing indicators, pre-operative CEA, T4, N1, N2, M1 and era). This is a positivity check, not an effect estimate.

| Diagnostic | Value (J02) |
|---|---|
| Treated / untreated | 7,485 / 8,886 |
| C-statistic for treatment | **0.711** (strong separation, i.e. substantial confounding by indication) |
| Median propensity, treated / untreated | 0.52 / 0.37 |
| Propensity range | 0.10 to 0.999 |
| Treated outside untreated range | 0.08% |
| Untreated outside treated range | 0.03% |
| Effective sample size, average-treatment-effect weights (treated / untreated) | 6,393 / **1,646** |
| Maximum average-treatment-effect weight | 311 |
| Weights above 10 | 0.2% |

**Interpretation.**
* Common support is adequate overall: almost every patient has comparators.
* Average-treatment-effect weights are unstable for the untreated group (effective sample size 1,646 of 8,886) because a few untreated patients with high propensity receive large weights.
* **An average-treatment-effect estimand is therefore unattractive.** An estimand for the treated population (average treatment effect on the treated, weights of 1 for treated and propensity odds for untreated) has effective sample sizes that are more stable and matches the clinical question "what did treatment do for patients like those who received it".

**Within risk groups (J03).** Positivity is weaker within groups:

| Group | Treated | Untreated | Lowest propensity among treated | Highest propensity among untreated | Within-group C-statistic |
|---|---|---|---|---|---|
| Favourable | 1,969 | 3,224 | 0.118 | 0.804 | 0.692 |
| Intermediate | 2,328 | 3,031 | 0.141 | 0.858 | 0.699 |
| Adverse | 3,188 | 2,631 | 0.134 | **0.997** | 0.700 |

Within each group, treatment is still strongly predictable from covariates, so within-group comparisons are confounded in the same way. In the Adverse group some untreated patients have a propensity near 1, which indicates an almost deterministic exclusion from treatment in part of the group. Those patients provide no comparison.

**Empirical cells (J04).** Of 49 cells defined by T, N, M and synchrony, 2 have no treated or no untreated patients (5 patients). Cells with at least 20 patients and both arms contain 16,221 of the 16,371 patients, so positivity over the full cross-classification is largely satisfied.

**Recommendation on method.** Use weighting for the treated population (average treatment effect on the treated) or 1:1 matching to the treated, with trimming and overlap diagnostics reported. Do not use the average-treatment-effect estimand as primary. Within-group estimates should be presented only with the reduced overlap in the Adverse group stated.

## 7. Is a target-trial emulation identifiable?

A target-trial design clarifies eligibility, time zero and the estimand. It does **not** remove confounding and does not make an effect identifiable by itself. The emulation would be: among resectable patients at the decision point, randomise to pre-operative chemotherapy or immediate surgery; follow overall survival from randomisation. The registry fails each identifiability requirement to a different degree:

| Requirement | Status in this registry |
|---|---|
| **Eligibility at the decision point** | Not met. The registry includes only patients who were resected, and has no records of the decision point or of patients judged unresectable. |
| **Time zero** | Met for the pre-operative exposure (hepatectomy), but this conditions on surviving and remaining resectable until surgery. |
| **Exchangeability given measured covariates** | Not met. Treatment is strongly associated with disease extent (C = 0.71). The main determinants of treatment in practice, performance status, liver function, comorbidity, KRAS and response to first-line therapy, are absent or sparse (comorbidity 4.9%, KRAS 2.3%). |
| **Positivity** | Largely met overall; weak within the Adverse group. |
| **Consistency (a well-defined treatment)** | Not met. Regimens, doses, cycles and sequencing are heterogeneous, partly recorded, and differ across centres. |
| **Measurement of covariates before treatment** | Unconfirmed for the count and size; resolvable only with the data dictionary. |

**Conclusion.** The causal estimand cannot be identified from these fields. What the data can support is a **conditional association** between pre-operative chemotherapy and survival among resected patients, adjusted for recorded baseline factors, with the residual confounding stated. That is not a treatment effect and should not be described as one.

## 8. Should this analysis be in the current ASO paper?

**Recommendation: no, not as a treatment-effect analysis in the current prognostic paper.**

1. **The primary aims are prognostic.** The validated groups, their calibration limits and the selection findings are the paper's contribution. A treatment analysis would change the paper's question.
2. **The design is not yet verified.** The timing of the predictors, the data dictionary and the regimen definitions are unresolved. Presenting treatment associations now would overstate what the data show.
3. **Causal language would be hard to avoid.** Reviewers at a surgical oncology journal will ask for causal interpretation of a treatment comparison; the registry cannot support it, and an observational association in a selected resected population invites over-reading.
4. **The selection and confounding limits are substantial**, so a treatment comparison in the same paper would dilute the prognostic message.

**Permitted in the current paper.** Descriptive patterns of treatment by prognostic group (counts only, with an explicit statement that no treatment effect is estimated), and a limitation paragraph stating that treatment effects were not evaluated.

**Separate publication, if pursued.** After (a) confirmation of the data dictionary and predictor timing, (b) an explicitly defined pre-operative comparison with ND handling pre-specified, (c) a pre-registered analysis plan using the treated-population estimand, and (d) ideally richer covariates (performance status, liver function, KRAS, regimen) from a source that records them. The analysis would then be reported under TARGET (2025) as an observational emulation with its identifiability limits stated.

## 9. Decisions and information needed

1. **Data dictionary and form timing.** The most important item. Obtain from the registry coordinators: what LE1NBMETAHEPNUM, LE1HEPMETASIZENUM and their "_V" variants measure, and when they were recorded relative to any liver chemotherapy.
2. **Pre-operative primary chemotherapy and radiotherapy.** Confirm they are pre-treatment; if so, they should enter the confounder set.
3. **Regimen and response data.** Whether they are available beyond the partial pre-operative fields.
4. **Interaction stratifier.** The locked groups are not validly usable until item 1 is resolved. If they are not usable, a baseline-only classification requires your approval as new modelling.
5. **Paper structure.** Confirm that the treatment question is excluded from the current prognostic paper, and approve a separate analysis plan only after items 1–3.

## Files in this folder

| File | Content |
|---|---|
| J01a | Count discordance by pre-operative chemotherapy (overall) |
| J01b | Count discordance within pre-operative count strata |
| J02 | Propensity overlap diagnostics (positivity check only) |
| J02b | Propensity deciles and treated proportion |
| J03 | Positivity by locked risk group |
| J04 | Empirical positivity over covariate cells |
| J05 | Eligibility and missing-treatment accounting |
