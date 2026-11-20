---
title: "Independent referee-style assessment: Paper 1 (prognostic survival model, colorectal liver metastases)"
---

**Purpose.** A critical reading of the final draft for supervisor approval, written as a reviewer for *Annals of Surgical Oncology* would read it. It does not change any result. The locked v8 model (M2a) and all numbers are as reported.

## 1. Summary of the submission

A stratified Cox model (strata: sex, synchronous presentation, M-stage; 11 covariates) was developed on 8,463 patients operated before 2010 and validated on 8,799 patients operated from 2010 in an international registry (17,262 eligible patients with complete TNM staging). Predicted 5-year survival was divided into three prognostic groups using training-set tertiles. Validation discrimination was C = 0.622; calibration under-predicted survival in the recent cohort (40.8% predicted versus 46.6% observed at 5 years).

## 2. Overall recommendation

**Major revision** would be the likely outcome at ASO. The study is large, carefully reported and candid about its limits. However, the intended use is undefined, predictor timing is unresolved, validation follow-up is short, discrimination is modest, and there is no external validation. The manuscript presents these limits honestly, so the main task is to decide the intended use and to address the points below, not to rewrite the analysis.

## 3. Strengths

1. Large international cohort with a temporal validation split that tests the model on a later, different era.
2. The selection rule was fixed before validation results were examined (Schoenfeld tests on the simplest candidate; M2a selected).
3. Missing-data handling is explicit (indicators and training-era medians; no imputation), and sensitivity analyses on duplicate records are reported.
4. Comparison with benchmark scores is made on identical patients, and the approximations are declared.
5. Limitations are stated in detail, and the predictor-timing question is raised by the authors themselves.
6. 75 of 75 manuscript numbers were checked against the locked outputs (`Paper1_verification_75_checks.md`).

## 4. Major concerns

1. **Intended use and prediction time (critical).** The paper does not say at what point the model is applied (before chemotherapy, at resection, or at follow-up). Clinicians cannot act on it until this is decided, and the Discussion should state a single intended use.
2. **Predictor measurement time (critical).** The survival time origin is hepatectomy, but the time at which metastasis count, size and TNM stage were recorded is undocumented. Count and size may reflect disease after pre-operative chemotherapy (43.4% of the cohort). If so, the model may use information not available at the stated time origin. This must be confirmed from the registry data dictionary before submission.
3. **Discrimination and benchmarks.** C = 0.622 is modest. The benchmark comparisons use registry approximations of the Fong and Nordlinger scores and do not reproduce GAME or the Tumour Burden Score. The paper does not claim superiority, but a reader will ask what the model adds beyond a clinician's judgement or an established score.
4. **Calibration.** The model under-predicts 5-year survival in the recent cohort (40.8% versus 46.6%) and was not recalibrated. Calibration slope and O/E are reported, but the implication for use is not drawn out.
5. **Follow-up and horizon.** Validation median follow-up is 1.47 years and only 26% of the validation cohort is evaluable at 5 years. Claims about 5-year prediction must be read against that.
6. **Selection.** 33.8% of eligible patients were excluded for incomplete TNM staging, and these patients differed by period, centre, synchrony and size. The analytic population is the population in which TNM-based prediction is valid, not the general resected population.
7. **No external validation and no clustering.** Validation is temporal within one registry. Centre or site clustering is not accounted for in validation or calibration, so between-centre heterogeneity is unknown.
8. **Precision of the bootstrap.** Percentile intervals use 300 resamples. The M2a upper bound is 0.637 in the candidate table and 0.636 in the selected model (Monte Carlo SD about 0.001). The difference is explained in Supplementary Table S4a, but more resamples would be needed for a final analysis. This is new analysis and needs supervisor approval.
9. **Data quality.** 16 probable duplicate pairs remain in the primary analysis; 3,074 deceased patients lack a death flag (the event is defined by `PATSTATC`, so they are still events, with the date from `LASTNDTC`); 1,676 recurrences have no usable date (affecting the secondary RFS analysis only). Each needs registry confirmation.
10. **Clinical utility.** No decision-curve or net-benefit analysis is presented. The statement that the model is "not suitable for pre-treatment decisions" is correct but limits the paper's clinical message; the authors should decide whether a decision-analytic analysis is in scope.

## 5. Minor concerns

1. Registry description: the original text gives 63 countries and 242 centres; the extract has 54 country codes and 288 site codes (259 with eligible patients). The manuscript states this and it must be reconciled before submission.
2. References: the 2026 review's authors, the Breslow citation year and the AJCC edition used by the registry are not verified. The Nordlinger item definitions differ from the published six-item score.
3. Keywords: seven are given; the journal's limit has not been checked against current instructions.
4. Journal requirements (3,500 words; seven display items; 250-word structured abstract; 1–3 sentence synopsis; AMA references) come from secondary sources. The official instructions must be checked before submission. The synopsis is two sentences and 31 words.
5. The title-page label is "Final Draft for Supervisor Approval", and the manuscript must be relabelled once supervisor approval is given.

## 6. Unresolved items that block submission

- **Ethics:** no approval reference or exemption is recorded; the consent-waiver basis and centre-level approvals are unconfirmed. The study must not be described as approved until they are.
- **Authorship and declarations:** R. Adam's contribution is not recorded; individual contributions and approval of the final manuscript are not confirmed; funding and competing-interest statements come from the original draft and need confirmation.
- **Registry:** centre and country counts, and the data-access route, need confirmation.
- **Predictor timing and prediction time:** see Major concerns 1 and 2.
- **Reporting checklists:** TRIPOD+AI item-level wording was not checked against the official checklist; PROBAST+AI has not been completed by the authors; Patient and Public Involvement (item 19) must be stated by the authors.

## 7. Verdict for the supervisor

The analysis appears to be correctly reported against the locked outputs, and the limitations are candid. The manuscript is not ready for submission until the ethics, authorship and registry items are settled and the intended use and predictor timing are decided. None of these requires changing the locked model.
