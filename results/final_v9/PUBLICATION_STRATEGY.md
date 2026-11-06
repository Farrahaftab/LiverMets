# Publication strategy: prognostic model and chemotherapy-associated outcomes (decision document)

**Status.** Strategy only. No new treatment model has been run and the locked v8 Cox M2a model and its Favourable, Intermediate and Adverse groups (cut-points 0.3793 and 0.4756) are unchanged. Evidence cited is the project's own outputs (v7, v8, audit, feasibility, treatment design).

## 1. Recommendation

**Option B: two separate papers within the PhD.**

* **Study 1 (submit to Annals of Surgical Oncology now, after the pre-submission checks in section 5):** development and temporal validation of the postoperative survival model and its three prognostic groups.
* **Study 2 (not yet submittable):** chemotherapy-associated survival, overall and by prognostic group. It proceeds only after the clinical data questions in section 4 are resolved, and it should be framed as an observational association study, reported under TARGET (2025) and STROBE.

The reason is that the two components have different evidential status. Study 1 is verified and bounded. Study 2 depends on unresolved predictor timing, treatment definitions and confounders. Combining them would make the weaker component define the stronger one.

## 2. Comparison of the options

| Criterion | A. One combined manuscript | B. Two papers (recommended) |
|---|---|---|
| **Clinical novelty** | Diluted. The prognostic contribution (validated, transparent groups with an honest calibration gap) becomes secondary to a treatment claim that readers will read causally. | Each paper has a clear question. Study 1 is a standalone prognostic contribution; Study 2 is a distinct clinical question. |
| **Methodological validity** | Weak. The treatment component cannot be identified from current fields (design verification, sections 3–7). Its confounding and selection problems would contaminate the validated model's narrative. | Study 1 stands on its own validity. Study 2 is evaluated only when its design is justified. |
| **Statistical limitations** | Two sets of limitations in one paper; reviewers would apply the strictest standard to both. Multiple-comparison and interaction questions multiply. | Each paper states its limitations once. Study 1 has no treatment-effect inference to defend. |
| **Interaction with risk groups** | The groups would be used as treatment modifiers before their timing is confirmed (see section 4). That is a validity problem. | Study 1 reports the groups as prognostic only, which is what they were validated for. Study 2 decides later whether they can modify treatment effects. |
| **Journal scope** | Annals of Surgical Oncology publishes both prognostic and comparative clinical studies, but a combined paper must meet TRIPOD and TARGET/STROBE at once, which lengthens the reporting burden. | Study 1 fits surgical oncology prognostic research; reporting is TRIPOD (regression model, not AI). Study 2 targets the same or a suitable surgical or oncology journal once its design is defensible. |
| **Reporting requirements** | TRIPOD for the model; TARGET and STROBE for the treatment comparison; PROBAST for risk of bias of the model. One combined checklist is awkward and invites inconsistency. | TRIPOD + PROBAST for Study 1; STROBE and TARGET for Study 2. Each checklist matches its design. |
| **Risk to credibility** | High. A reviewer who finds the treatment comparison confounded will question the prognostic results too. | Low. Study 1 can be assessed on its own terms. |
| **Time to submission** | Blocked by the treatment questions. | Study 1 can go forward once the checks below are done. |

**Note on journal policy.** Current author guidelines, word limits and the handling of prediction-model and comparative-effectiveness papers should be checked on the journal's site before submission. I have not verified them from here.

## 3. Study 1: what is ready and what must be done first

**Study 1 contribution.** A stratified Cox model using TNM, age, sex, synchrony, interval, metastasis count and size produces three prognostic groups. Temporal validation (operated 2010 or later) gives a C-index of 0.622, log-rank separation p = 2 × 10⁻⁵², a stable group assignment (κ 0.83), and a calibration gap that is reported openly (observed 5-year survival 46.6% vs predicted 40.8%). Its clinical value is transparency, a published baseline risk stratification, and a calibration limitation that other models in this field may not report.

**Modest novelty to say honestly.** Discrimination is modest and the benchmark comparisons use approximations of the published scores. The paper should not claim superiority over GAME, TBS or the other scores, which cannot be reconstructed from registry variables.

**Checks before submission (none changes the locked model):**

1. **Horizon decision.** Decide whether 3 years becomes the primary decision horizon or 5 years remains the headline. This is a pre-specification decision and must be declared, not chosen after seeing validation results.
2. **Option B.** Decide whether to add clinician-defined thresholds. Without a named clinical decision they should not be added (feasibility report, section 3).
3. **Duplicate records.** Registry confirmation of the 16 probable duplicate pairs and the 31 near-duplicates inside the cohort. Sensitivity analyses already show no change to conclusions.
4. **Death-count and exclusion wording.** Already corrected in v8 (6,601 recorded; 6,591 inside the window; 33.8% excluded).
5. **Reporting.** TRIPOD checklist; PROBAST risk-of-bias assessment; flow diagram; the excluded-patient comparison (v8 Supplementary Table S5).
6. **Authorship and approvals.** Confirm R. Adam's contribution and the ethics approval reference (both marked [TO CONFIRM]).
7. **Citations.** Three [CITATION NEEDED] items and two [TO CHECK] references.

**Study 1 limitations to state:** single registry and temporal validation only (no external validation); modest discrimination; calibration gap; selection to resected patients with complete staging (33.8% excluded); unverified timing of metastasis count and size; missing death flags for 3,074 deceased patients; undated recurrences for RFS.

## 4. Study 2: what must be established before a treatment comparison is defensible

The design verification found that a treatment-effect estimate cannot be identified from current fields. Minimum evidence required, in order of priority:

**Priority 1: predictor timing (gating item).**
* A data dictionary, or the case-report form, stating when metastasis count and size were recorded relative to any liver chemotherapy. Without it, the three prognostic groups cannot be used as effect modifiers, because they include these two variables.
* Confirmation of when the pre-operative count and size were recorded for patients who had pre-operative chemotherapy.

**Priority 2: treatment definitions.**
* A definition of "pre-operative liver chemotherapy" (flag, start date, number of cycles, regimen) and of "no pre-operative chemotherapy" (is it "surgery alone", or "post-operative only"?).
* Clarity on the meaning of the primary-tumour chemotherapy and radiotherapy fields and their timing relative to liver surgery.
* Start dates for the 42% of exposed patients where they are missing, or a clear statement that they cannot be recovered.
* Handling of ND (not determined) and blank: whether these are "not given" or "unknown".

**Priority 3: missing clinical confounders.**
* Performance status (ECOG), ASA grade, liver function (for example Child-Pugh or bilirubin), and comorbidity. Comorbidity is currently recorded for 4.9% of records and KRAS for 2.3%; these are the most important gaps.
* Pre-operative CEA (recorded for 65.8%) with its timing confirmed.
* Regimen detail for pre-operative chemotherapy (recorded for 35–39%) and response to it.

**Priority 4: sample and selection.**
* Information on patients who were not resected after chemotherapy, or whose disease was judged unresectable, if the registry holds it. Without it, the comparison is confined to resected patients and cannot estimate the effect of offering chemotherapy.

**What would make the comparison defensible.** Items 1–3 resolved; a pre-specified analysis plan (treated-population estimand, weighting or matching, overlap reported, ND handled in pre-specified sensitivity analyses); and reporting under TARGET with the identifiability limits stated. Even then the result is an observational association, not a treatment effect.

**What would not be defensible even then:** a claim that chemotherapy improves or worsens survival, or that the groups predict chemotherapy benefit, without an explicit effect-modification design that the data can support.

## 5. Decisions needed

1. Approve Option B (two papers), with Study 1 as the first submission.
2. Decide the horizon and whether Option B thresholds are added to Study 1 (both pre-specification decisions).
3. Request the data dictionary and form timing from the registry coordinators (Priority 1). This is the single action that unblocks Study 2.
4. Decide whether to request the missing clinical covariates (Priority 3) from the source centres, which is a larger undertaking.
5. Confirm the R. Adam contribution and the ethics reference before any submission.

## 6. Summary

Study 1 is ready for a careful submission after the checks above, and its contribution is honest and useful. Study 2 is a legitimate and clinically important question, but the current registry cannot yet answer it causally, and presenting it alongside Study 1 would weaken both. Two papers is the stronger strategy: it protects the validated prognostic work from a treatment comparison that the data cannot support, and it leaves Study 2 open until its design is justified.
