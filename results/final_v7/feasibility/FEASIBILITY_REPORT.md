# Methodological feasibility assessment: prediction horizon, prognostic groups, clinical thresholds, calibration, centre-level validation and reconstructable scores

**Scope.** This assessment uses the locked v7 analysis (stratified Cox M2a; training-only tertile cut-points; TNM-complete cohort of 17,262). No model was refitted, no cut-off was changed, and no existing output was overwritten. The feasibility computations (`notebooks/feasibility_v7.py`, outputs `G01–G05`) reproduce the locked validation C-index (0.6216) before evaluating horizons. Validation outcomes were used only to describe the fixed model.

**Three categories of evidence are kept separate below.**
* **[V7]** Completed v7 findings, already in the locked outputs.
* **[FEAS]** Feasibility computations on the locked model, new in this assessment, not used to change any result.
* **[PROPOSAL]** Recommendations that need new data, clinician input or a pre-specified decision before analysis.

**Literature and reporting references used.** The 2026 systematic review and meta-analysis in *Cancers* (48 scores, 48 studies, 33,602 patients, published February 2026) was located through a search; I have only the search summary, not the full text, so its pooled estimates are not reported here. I could not locate the April 2026 *Annals of Surgical Oncology* comparison of 11 scores. The closest match is a 2024 abstract comparing 11 scores (Fong, Nordlinger, Nagashima, Konopke, BPI, TBS, RSI, Kulik, RAS-mutation score, mTBS and GAME) ([Z Gastroenterol 2024 abstract](https://www.thieme-connect.de/products/ejournals/html/10.1055/s-0043-1777515)). **Please send the 2026 ASO paper if it is a different study.** The reporting guidance is TRIPOD (for regression models) and TRIPOD+AI for machine-learning models ([EQUATOR, TRIPOD](https://resources.equator-network.org/reporting-guidelines/tripod-statement/); [TRIPOD+AI and PROBAST+AI protocol, 2021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8273461/)). I could not confirm the 2025 PROBAST+AI publication itself from a primary source.

---

## 1. Prediction horizon: 1, 3 or 5 years?

### Evidence

| Horizon | Evaluable validation patients [FEAS] | Deaths before horizon [FEAS] | Predicted S [FEAS] | Observed KM S (95% CI) [FEAS] | O/E (bootstrap 95% CI) [FEAS] | Group-level at-risk, Favourable / Intermediate / Adverse [FEAS] |
|---|---|---|---|---|---|---|
| 1 year | 5,335 (60.6%) | 581 | 0.897 | 0.910 (0.903–0.917) | 1.015 (1.006–1.023) | 1,470 / 1,583 / 1,701 |
| 3 years | 3,118 (35.4%) | 1,544 | 0.592 | 0.645 (0.630–0.661) | 1.091 (1.065–1.116) | 568 / 534 / 472 |
| 5 years | 2,289 (26.0%) | 1,848 | 0.408 | 0.466 (0.444–0.487) | 1.142 (1.087–1.198) | 194 / 129 / 118 |

Discrimination at each horizon (time-dependent AUC, [V7], F02): 0.639 (1 year), 0.653 (3 years), 0.675 (5 years).

### Assessment

* **Follow-up and censoring.** The validation cohort has a median follow-up of 1.47 years ([V7] descriptive table). Only 26% of validation patients can be evaluated at 5 years, and the at-risk group at 5 years is 441. The 5-year estimate therefore depends on a minority of patients and on the tail of a Kaplan–Meier curve.
* **Event counts.** Events are adequate at 1 and 3 years (581 and 1,544). At 5 years there are 1,848 deaths, but the events fall mostly in patients who are censored early, so the effective sample for 5-year calibration is small.
* **Calibration precision.** Calibration is best at 1 year (O/E 1.015, interval 1.006–1.023). Under-prediction of survival grows with horizon, from 1.015 at 1 year to 1.142 at 5 years. The intervals at 3 and 5 years do not include 1.00. The gap is therefore a property of the model over time, not a sampling artefact.
* **Group-level evaluation.** At 5 years there are 118–194 patients at risk per group, which is too few for reliable group-specific survival estimates. At 3 years the counts (472–568) are workable.
* **Clinical relevance.** Five-year overall survival is the standard reporting horizon in CRLM studies and in the scores being compared. A 1-year horizon has limited relevance for surgical decisions, which are made for longer horizons.

### Recommendation

* **[PROPOSAL]** Report all three horizons, with a pre-specified **3-year horizon as the primary decision horizon**, because it combines adequate evaluability (35%, 1,544 events) with clinical relevance. Report **5-year** survival as the comparator needed for published benchmarks, with its evaluability and wide intervals stated explicitly. Report 1-year survival as a calibration reference.
* **Caution.** Choosing the horizon after seeing validation evaluability is a validation-informed decision, even though no cut-off is being tuned. It should be declared as a change from the locked analysis and justified in the manuscript, or it should be fixed prospectively for a future study.

---

## 2. Are the Cox-based tertiles appropriate as descriptive groups?

### Assessment

* **[V7]** The three groups are defined by training-only tertiles of predicted 5-year survival (cut-points 0.3793 and 0.4756). They separate outcomes in validation (log-rank p = 2.0 × 10⁻⁵²; ordinal C 0.603) and are stable across bootstrap refits (κ 0.832).
* **Strengths.** Tertiles are transparent, fixed in training, and stable. They describe the population in relative terms.
* **Limitations.**
  * Tertiles are sample-driven: each group contains a third of the training population by construction, regardless of clinical meaning.
  * The groups are relative rankings, so their absolute survival estimates are affected by the miscalibration described in section 4.
  * Tertile membership depends on the period of the training data.

### Recommendation

* **[PROPOSAL]** Keep the Cox-based tertiles as **descriptive, relative prognostic groups** in the primary manuscript, labelled as such. Do not describe them as clinical risk categories or cut-offs that should guide treatment without a separate clinical justification (section 3).

---

## 3. Would a clinician-defined risk stratification (Option B) add clinical value?

### Assessment

* A clinician-defined stratification would have clinical value only if its thresholds correspond to a **specific decision** that changes management, for example:
  * eligibility for a trial of perioperative or adjuvant systemic therapy;
  * intensity of post-operative surveillance;
  * whether to offer resection versus systemic therapy first;
  * selection for a neoadjuvant strategy.
* The decision determines the threshold. Without a decision, a threshold is arbitrary, and its performance cannot be judged.
* Option B could use the same variables as the current model, but its thresholds would be set by clinical judgement rather than by the data. This is a legitimate approach, but it needs documented clinical input before any analysis.

### Recommendation

* **[PROPOSAL, requires clinical input]** Option B is worth pursuing only if the research question is tied to one named decision. The clinical panel must specify (a) the decision, (b) the risk threshold that would change it, and (c) what outcome difference would justify the change. The thresholds would then be evaluated in the existing data as a pre-specified, descriptive comparison, with no adjustment to the current model.
* **[V7]** Without this input, Option B should not be added to the primary paper.

---

## 4. Can calibration be improved using development-era data without leaking validation outcomes?

### What has been done (no validation leakage) [V7]

* A recalibrated baseline hazard from 2005–2009 training patients, with the coefficients unchanged, reduced validation O/E from 1.142 to 1.115 and kept 92% of patients in their primary group (κ 0.883). The gap was reduced but not removed.

### Options that do not use validation outcomes

* **Bootstrap optimism correction within development** [PROPOSAL]. Estimate the optimism of calibration slope and C-index by bootstrapping the development cohort alone, then apply the correction to the model. This quantifies overfitting within development, but it does not address the temporal drift, because the development data are older than the validation data.
* **Recent-era recalibration of the baseline** [FEAS, tested above]. Uses 2005–2009 patients only. It is the most defensible option within the data, but its effect (O/E 1.115) indicates that the drift is not captured by a single recent baseline.
* **Time-varying baseline or period covariate** [PROPOSAL, new modelling]. Would model the period effect explicitly. It is a new model, so it requires a separate pre-specified development, and it cannot be validated on the same temporal split without a further holdout.

### Assessment

* Calibration can be improved in development without leakage, but the validation drift is a temporal change that development data cannot fully describe. Any recalibration would need a prospective or external validation to show that it generalises to later patients.

### Recommendation

* **[PROPOSAL]** Keep the locked model for the primary paper and report the calibration gap explicitly, as now. Use bootstrap optimism correction within development only as a supplementary check if the authors wish to report it. Do not recalibrate the primary model on validation data.

---

## 5. Is a centre-held-out validation strategy feasible?

### Evidence [FEAS, G04–G05]

| Threshold: TNM-complete patients per centre | Centres meeting threshold | Centres with ≥20 validation events | Share of cohort in qualifying centres | Countries meeting threshold |
|---|---|---|---|---|
| ≥20 | 122 | 32 | 95.5% | 37 |
| ≥50 | 78 | 32 | 87.0% | 27 |
| ≥100 | 51 | 29 | 76.0% | 22 |

* 248 centres have TNM-complete patients; the median is 18 per centre.
* 133 centres contribute to both development and validation eras.

### Assessment

* **Feasible, with constraints.** Grouped validation by centre is possible for the 78 centres with at least 50 TNM-complete patients (87% of the cohort). Only 32 of them have at least 20 validation events, so centre-specific estimates would be imprecise.
* **Site-level missingness.** 57 centres have no incomplete TNM, but 34 have 50% or more. Centre-held-out validation would therefore test centres with systematically different recording practice. This is informative, but it also means that the held-out centres differ in data quality, not only in patient mix.
* **Possible duplicates.** Identical cross-country records (Bulgaria–Brazil) mean that centre-held-out splits could place a patient and its duplicate on opposite sides of a split, which would leak outcomes. Duplicates must be resolved, or grouped by the duplicate cluster, before any centre split.
* **Method.** Leave-one-centre-out validation is too unstable at this sample size. Grouped (site-level) cross-validation, with repeated splits and reporting of centre-level heterogeneity, is the feasible design.

### Recommendation

* **[PROPOSAL]** Centre-level validation is feasible as a **secondary analysis** after the duplicate records are resolved: grouped cross-validation across the 78 centres with at least 50 TNM-complete patients, with random-effects summaries of C-index and O/E. It should not replace the temporal validation, and it should not be framed as external validation, because it uses the same registry.

---

## 6. Can GAME, TBS, Fong and other scores be reconstructed faithfully?

### Assessment score by score

| Score | Components [source] | Available in registry? | Faithful reconstruction? |
|---|---|---|---|
| **Fong Clinical Risk Score** | Node-positive, interval < 12 months, > 1 metastasis, size > 50 mm, CEA > 200 ng/mL [our earlier implementation; original definitions to be checked against the Fong 1999 paper (Ann Surg) and the external validation study [PMC9139295](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9139295/)] | All five items are present; CEA is recorded for 66% of the cohort | **Largely faithful** for patients with CEA recorded (n = 3,642 in the validation Fong subset). The score is incomplete for the remaining third. Thresholds must be verified against the original paper. |
| **GAME score** | KRAS mutation, CEA ≥ 20 ng/mL, primary-tumour nodal involvement, Tumour Burden Score, extrahepatic disease [MSKCC record](https://synapse.mskcc.org/synapse/works/127627) | **No**: KRAS status is not in the registry. Extrahepatic disease at operation is not clearly recorded. | **Not faithful.** A version without KRAS would not be GAME. The sources also disagree on risk-group cut-offs (a 4-point high-risk group in one, ≥ 6 points in another), so the authors would need to confirm the original definition. |
| **Tumour Burden Score (TBS)** | (maximum diameter in cm)² + (number of lesions)² [Sasaki 2016](https://iris.univr.it/bitstream/11562/957734/1/2016%20Sasaki%20K%20-%20The%20Tumor%20Burden%20Score%20-%20A%20New%20Metro-ticket%20prognostic%20tool%20for%20CRLM%20based%20on%20tumor%20size%20and%20number%20of%20tumors.pdf)] | Size (mm) and metastasis count are present; the count is coded in bands in some extracts, and the size is the largest recorded value | **Approximately reconstructable.** Cut-offs vary between studies, and the registry's size is the largest recorded value, not necessarily the maximum diameter, so the result must be called an approximation. |
| **Nordlinger-type score** | Age, T, N, interval (our four-item approximation) | Yes | **Not faithful** to the original score. It is an approximation and should be presented as such, or replaced once the original definition is checked. |
| Nagashima, Konopke, BPI, RSI, Kulik, RAS-mutation score, mTBS | Require variables that are not recorded in the registry, such as histology grade, RAS status and perioperative therapy details; I could not verify their definitions from primary sources here | Mostly **no** | **Not feasible** without the original definitions and the missing variables. |

### Recommendation

* **[PROPOSAL]** Include only the **Fong score**, implemented faithfully for patients with CEA recorded, as a benchmark, with its missingness reported. Describe the Nordlinger-type comparison as an approximation or remove it. Do not present GAME or TBS as reconstructed unless the original definitions are confirmed and the variables are complete. Do not claim a comparison with GAME.

---

## Overall recommendation

1. **Keep the locked v7 model and the 17,262 TNM-complete primary cohort.** The validation results are internally consistent, the duplicate issues do not change them, and the cohort is the population for which TNM-based prediction is valid.
2. **Horizon.** Report 1, 3 and 5 years. Declare 3 years as the primary decision horizon, with 5 years as the benchmark comparator, and state evaluability and calibration precision at each horizon. Declare the change from the locked analysis explicitly.
3. **Groups.** Keep the tertiles as descriptive, relative groups.
4. **Clinical stratification.** Do not add Option B unless a named clinical decision and threshold are supplied by clinicians before analysis.
5. **Calibration.** Report the gap openly. Do not recalibrate the primary model on validation data. Any improvement must be developed and validated prospectively or externally.
6. **Centre-level validation.** Pursue as a secondary grouped analysis after duplicates are resolved and restricted to centres with at least 50 TNM-complete patients.
7. **Benchmarks.** Use the Fong score, faithfully implemented for patients with CEA recorded. Present the Nordlinger-type comparison as an approximation. Do not reconstruct GAME or the other scores without their original definitions and variables.

**Publication implications.** The stronger paper is a TNM-based survival model with transparent limits, reporting its horizons, its selection and its missingness, and reporting its calibration gap honestly. A paper claiming superiority over GAME, TBS or other scores is not supported by the available data. The TRIPOD statement applies to this regression model; TRIPOD+AI would apply only if machine-learning methods were used. PROBAST (or PROBAST+AI for AI-based models) should be used to assess risk of bias, and the main risks are the missing TNM data, the possible duplicates and the temporal drift.

**Required from you:** (1) the 2026 ASO paper, if it is different from the one above; (2) a named clinical decision for any Option B thresholds; (3) confirmation that the horizon change in recommendation 2 should be declared in the manuscript.

## Files

| File | Content |
|---|---|
| G01 | Horizon feasibility, validation (1, 3, 5 years) |
| G02 | Group-level events and at-risk counts by horizon |
| G03 | Bootstrap calibration precision by horizon |
| G04 | Centre-held-out feasibility by threshold |
| G05 | Site structure of TNM-complete patients |
