# Predictor-timing audit: metastasis count and size in the locked M2a model

**Scope.** The audit asks whether the metastasis count (`LE1NBMETAHEPNUM`) and size (`LE1HEPMETASIZENUM`) used in the locked M2a model were recorded at a time that makes them valid predictors at the intended prediction time (hepatectomy). It uses only the repository's locked outputs, the locked notebook code and the column inventory. It does not re-fit any model or change any reported result.

**Limit of this audit.** The raw workbooks and the patient-level extract were not available in this session (the scratch copy had been cleared), and no computer folder was attached. Header names, data dictionary and patient-level dates therefore could not be checked directly. Each result below states its source. The reproducible script is `scripts/predictor_timing_audit.py`; its tables are in this folder (A1–A7).

## 1. Columns traced through the model (confirmed from code)

| Step | Column | Code (locked notebook) |
|---|---|---|
| Metastasis count (M2a `METS_F`, indicator `METS_NR`) | `LE1NBMETAHEPNUM` | `METS = num(X.LE1NBMETAHEPNUM).where((x>=1)&(x<=50))` (line 221) |
| Largest metastasis size (M2a `SIZE10_F`, indicator `SIZE_NR`) | `LE1HEPMETASIZENUM` | `SIZE = num(X.LE1HEPMETASIZENUM).where((x>0)&(x<=300))` (line 222) |
| Interval (`DFI12_F`, `DFI_NR`) | `DGKCOLDT`, `LE1DGMETADT`, operation date | `DFI` set to missing when metastasis date is after time zero (line 262) |
| Time zero | `LE1OPERDT_F1` | `T0` (line 249) |
| Model covariates | `CORE_M2A` | line 326 |

The notebook applies **no timing filter** to count or size. The pre-operative-only sensitivity model (`PREOP_M2A`, line 328) drops both variables; it does not change when they were recorded.

## 2. Documentation search (what the dataset itself says)

- **No data dictionary** exists in the repository, the notebook or the workbook as described in the treatment-design verification (which records a single sheet named "Data"). Confirmed by repository search for "dictionary" and "codebook".
- **Column names carry no timing word** for count or size. Other fields in the same block do: `LE1PREHEPCEA_F1` (pre-operative CEA), `LE1PREOPMCTYN_F1` (pre-operative metastasis chemotherapy), `LE1NBMRESECNUM_F1` (resected count). The absence of a timing word in `LE1NBMETAHEPNUM` and `LE1HEPMETASIZENUM` is evidence of an undocumented field, not of a pre-operative field.
- The `_V` variants (`LE1NBMETAHEPNUM_V`, `LE1HEPMETASIZENUM_V`) and the `CAR` variants are not documented; their meaning is unknown.
- **TNM fields** `STADET`, `STADEN`, `STADEM` carry no source marker (clinical or pathological).

## 3. Temporal relationships (table A3)

| Relationship | Can be established? | Evidence |
|---|---|---|
| Operation date is time zero | Yes | `LE1OPERDT_F1`, 94.8% usable |
| Liver-metastasis diagnosis after operation | Yes, where dated | 12 analytic-cohort patients (F33) |
| Pre-operative chemotherapy start before operation | Yes, where dated | 4,259 of 4,320 dated starts (98.6%) (H04) |
| Post-operative liver chemotherapy start after operation | Yes, where dated | 4,337 of 4,425 dated starts (98.0%) (H04) |
| **Count or size relative to chemotherapy** | **No** | no date or timing field exists for count or size |
| **Count or size relative to operation** | **No** | no timestamp; the form date is the operation |
| **TNM source (clinical or pathological)** | **No** | no source field |

## 4. Pre-operative versus resected counts (table A4)

- Both counts are recorded for **14,189** analytic-cohort patients (F34). The resected count is `LE1NBMRESECNUM_F1`, which is explicitly a resection count.
- Equal: 8,847 (62.4%). Resected greater: 2,244 (15.8%). Resected lower: 3,098 (21.8%).
- Among patients with the chemotherapy flag known (J01a, n = 13,838): resected lower than `LE1NBMETAHEPNUM` in **22.5%** of those given pre-operative chemotherapy (n = 6,213) and **12.3%** of those not given it (n = 7,625). Mean count 2.51 versus 1.79.
- Within count strata (J01b), the difference is small or inconsistent: 0.7% versus 0.4% at count 1; 22.9% versus 20.3% at count 2; 36.9% versus 30.2% at count 3; 36.3% versus 38.1% at 4 or more.

**Interpretation.** Treated patients had more lesions at the first count, so the higher share of "resected lower" among them is consistent with two explanations that the data cannot separate: (a) the count was recorded before chemotherapy and treated patients had more disease, or (b) the count was recorded after chemotherapy had reduced disease. Agreement in 62% of patients does not show that both counts were recorded at the same time, nor the timing of the first count.

## 5. Chemotherapy exposure (table A5)

- Pre-operative liver chemotherapy yes: **7,485 (43.4%)** of 17,262; no: 8,886 (51.5%); ND or NA: 759 (4.4%); blank: 132 (0.8%) (H01, H02).
- Pre-operative yes with a start date: 4,320 of 7,485 (57.7%).
- Timing pattern (H03): pre-operative only 22.2%; pre- and post-operative 21.2%; post-operative only 23.7%; no liver chemotherapy recorded 19.8%; ND in at least one field 8.9%; unknown 4.2%.

## 6. Leakage assessment (table A7; intended prediction time = hepatectomy)

| Variable | Status | Risk at operation time |
|---|---|---|
| Age, sex | Known before time zero | Low |
| Synchrony | Recorded by time zero (date not documented) | Low |
| Interval | Metastasis dates after operation are set to missing (code, line 262) | Low; no leakage found in code |
| TNM (T, N, M) | Source not documented; pathological stage would be post-operative | **Unresolved** |
| Metastasis count | Timing not documented; may reflect post-chemotherapy disease in up to 7,485 patients (43.4%) | **Unresolved** (treatment-related rather than post-operative) |
| Largest size | Timing not documented; could be pathological size | **Unresolved** (possible post-operative information) |
| Resected count | Not a model predictor | Would be leakage if used; it is not used |

## 7. Missingness (table A6)

- Count: 92.8% known in the analytic cohort (F32); 1,251 (7.2%) unknown (F31). In all 29,565 rows (F41): valid 85.6%, ND 7.6%, blank 6.8%.
- Size: 3,306 (19.2%) missing in the analytic cohort (F31). In all rows (F41): valid 75.0%, ND 15.3%, blank 9.7%.
- ND and blank are both treated as missing in the model. Whether ND means "not measured" or "not applicable" is not documented.

## 8. Findings by status

**Confirmed (from code, outputs or inventory)**
1. The model uses `LE1NBMETAHEPNUM` (count) and `LE1HEPMETASIZENUM` (size), with the filters in section 1.
2. The notebook applies no timing filter to either variable.
3. Time zero is the operation date, and metastases dated after operation are excluded from the interval.
4. No data dictionary is available in the repository or the workbook as described.
5. Pre-operative chemotherapy is recorded for 7,485 patients, and 98.6% of dated pre-operative starts precede operation.
6. Both counts are recorded for 14,189 patients; they agree exactly for 62.4%.

**Reasonable inferences (not proven)**
7. `LE1NBMETAHEPNUM` was probably recorded at the hepatectomy form, because its sibling `LE1NBMRESECNUM_F1` is a resection count. This is an inference from naming.
8. Treated patients may have had counts recorded after chemotherapy. The J01 comparison is consistent with this, but also with more disease at baseline.

**Cannot be established from the dataset**
9. When count and size were recorded relative to chemotherapy and to operation.
10. Whether size is clinical, radiological or pathological.
11. The meaning of the `_V` variants and the `CAR` variants.
12. Whether TNM is clinical or pathological.

## 9. Discrepancies found in the existing outputs

1. **Treatment-design text** gives 14,199 patients with both counts; its own table (J01a) sums to 13,838 with the chemotherapy flag known, and F34 gives 14,189 with both counts. The 14,199 figure should be corrected in the treatment document. The manuscript does not use it.
2. **Labels.** F34 and the manuscript call the count "pre-operative" and the sensitivity model "pre-operative-only". The timing of the count is undocumented, so these labels assert something the dataset does not establish.
3. **Inventory flag.** The column inventory marks `LE1OPERDT_F1` as not in the analysis extract, although the notebook extracts it (DATES list). The inventory flag appears stale.

## 10. Recommended prediction time and wording

**Recommended intended prediction time:** at hepatectomy (time zero), using information recorded before resection, **with the caveat** that the count and size may reflect disease after any pre-operative chemotherapy. The model should not be presented as usable before treatment decisions, because pre-treatment timing of count and size is not established.

**Wording changes for the manuscript (recommended, not made):**
1. Methods, predictor timing: replace "The model assumes that count and size are known at operation" with "Metastasis count and size are taken from the hepatectomy form (LE1NBMETAHEPNUM, LE1HEPMETASIZENUM). Their recording time relative to pre-operative chemotherapy and to pathology is not documented; the model is therefore applicable at hepatectomy, and not before treatment decisions."
2. Replace "pre-operative-only model" (Results, Supplementary Table S5, figure labels) with "model without metastasis count and size", which describes what was removed rather than when it was measured.
3. Supplementary Table S2f and the agreement sentence: describe the variables by field name, and state that agreement does not establish the timing of either count.
4. Limitations (item 4): add that treated patients had more lesions at the first count, and that count may reflect post-chemotherapy disease in 43.4% of the cohort.
5. Add TNM source (clinical or pathological) to the questions for the registry.

## 11. Questions only the registry can answer

1. What do `LE1NBMETAHEPNUM`, `LE1HEPMETASIZENUM` and their `_V` variants measure, and on what date were they recorded?
2. Was the count recorded before pre-operative chemotherapy, or after it?
3. Is the size a radiological, clinical or pathological measure?
4. Is the TNM stage clinical or pathological?
5. What does ND mean for these variables, as distinct from blank?
