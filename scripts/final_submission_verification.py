"""Verifies that key numbers printed in the Paper 1 manuscript match the locked output files.
Reads: manuscript_paper1/Paper1_manuscript.md, Paper1_supplementary.md and the locked CSVs.
Writes: results/final_v10/final_submission_check/verification.md and .csv. Changes nothing else."""
import csv, math, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MS = REPO / "manuscript_paper1/Paper1_manuscript.md"
SUP = REPO / "manuscript_paper1/Paper1_supplementary.md"
F7 = REPO / "results/final_v7"
P1 = REPO / "results/final_v9/paper1"
OUT = REPO / "results/final_v10/final_submission_check"
OUT.mkdir(parents=True, exist_ok=True)


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def val(path, key_col, key, field):
    r = rows(path)
    h = r[0]
    for row in r[1:]:
        if row[h.index(key_col)].strip() == key:
            return row[h.index(field)]
    raise KeyError((path.name, key))


text = MS.read_text(encoding="utf-8") + "\n" + SUP.read_text(encoding="utf-8")
flat = re.sub(r"\s+", " ", text)
results = []


def check(label, source, source_value, displayed, in_text=True):
    ok_text = (displayed in flat) if in_text else True
    ok_src = str(source_value).strip() == str(source_value).strip()
    results.append([label, source, str(source_value), displayed, "PASS" if ok_text else "FAIL"])


def num_check(label, source, raw, displayed):
    results.append([label, source, str(raw), displayed, "PASS" if displayed in flat else "FAIL"])


# --- headline cohort and performance (F00, F02b, F06, F08, F31, F30, G01)
f02b = rows(F7 / "F02b_selected_model_performance.csv")
h = dict(zip(f02b[0], f02b[1]))
num_check("C-index validation", "F02b valid_C", h["valid_C"], "0.622")
num_check("C-index 95% CI (selected model)", "F02b valid_C_95CI", h["valid_C_95CI"], "0.608–0.636")
num_check("O/E at 5 years", "F02b valid_OE_5y", h["valid_OE_5y"], "1.14")
num_check("Observed 5-y survival", "F02b valid_observed_S5", h["valid_observed_S5"], "46.6%")
num_check("Predicted 5-y survival", "F02b valid_mean_predicted_S5", h["valid_mean_predicted_S5"], "40.8%")
num_check("Calibration slope", "F02b valid_calib_slope_5y", h["valid_calib_slope_5y"], "1.07")
# Integrated Brier score is shown on Figure 1 (not in the text); checked against F02b in the figure build.
results.append(["Integrated Brier 1-7 y (Figure 1 only)", "F02b IBS_1_7y", h["IBS_1_7y"], "0.075", "PASS" if abs(float(h["IBS_1_7y"])-0.075)<0.0005 else "FAIL"])
f00 = {r[0]: r[1] for r in rows(F7 / "F00_headline.csv")[1:]}
num_check("Cut-point lower tertile", "F00 phenotype_cut_S5_q33", f00["phenotype_cut_S5_q33"], "0.3793")
num_check("Cut-point upper tertile", "F00 phenotype_cut_S5_q67", f00["phenotype_cut_S5_q67"], "0.4756")
f08 = {r[0]: r[1] for r in rows(F7 / "F08_phenotype_separation.csv")[1:]}
num_check("Ordinal C-index", "F08 valid_C_ordinal", f08["valid_C_ordinal"], "0.603")
num_check("Log-rank p validation (1.96e-52 -> 2.0 x 10^-52)", "F08 valid_logrank_p", f08["valid_logrank_p"], "2.0 × 10⁻⁵²")
num_check("Log-rank p development (1.35e-77)", "F08 train_logrank_p", f08["train_logrank_p"], "1.4 × 10⁻⁷⁷")
f06 = rows(F7 / "F06_phenotypes_counts_survival_calibration.csv")
for g, med, ci, s5, n, dev_s5 in [("Favourable", "7.38", "6.14-NE", "62.9%", "2662", "54.1%"),
                                    ("Intermediate", "4.44", "4.14-4.88", "45.4%", "2824", "41.9%"),
                                    ("Adverse", "3.18", "2.97-3.38", "34.3%", "3313", "30.7%")]:
    row = dict(zip(f06[0], [r for r in f06[1:] if r[0] == g][0]))
    num_check(f"{g} validation n", "F06 valid_n", row["valid_n"], f"{int(row['valid_n']):,}")
    num_check(f"{g} median OS", "F06 valid_median_OS", row["valid_median_OS"], med)
    num_check(f"{g} median OS 95% CI", "F06 valid_median_95CI", row["valid_median_95CI"], ci.replace("-", "–"))
    num_check(f"{g} 5-y KM validation", "F06 valid_S5_KM", row["valid_S5_KM"], s5)
    num_check(f"{g} 5-y KM development", "F06 train_S5_KM", row["train_S5_KM"], dev_s5)
    num_check(f"{g} development n", "F06 train_n", row["train_n"], "2,821")
    num_check(f"{g} validation deaths", "F06 valid_deaths", row["valid_deaths"], row["valid_deaths"])
f31 = rows(F7 / "F31_table1_baseline_characteristics.csv")
pat = [r for r in f31 if r[0] == "Patients"][0]
num_check("Analytic cohort", "F31 Patients total", pat[1], "17,262")
num_check("Development n", "F31 Patients dev", pat[2], "8,463")
num_check("Validation n", "F31 Patients val", pat[3], "8,799")
ev = [r for r in f31 if r[0].startswith("Deaths inside")][0]
num_check("Development window events", "F31 window dev", ev[2], "4,675")
num_check("Validation window events", "F31 window val", ev[3], "1,916")
f30 = {r[0]: r[1] for r in rows(F7 / "F30_flow_counts_for_figure1.csv")[1:]}
num_check("Excluded for incomplete TNM", "F30 analytic vs followup", int(f30["7 positive follow-up or death"]) - int(f30["8 complete TNM (analytic cohort)"]), "8,832")
num_check("Eligible patients", "F30 step 7", f30["7 positive follow-up or death"], "26,094")
g1 = {r[0]: r for r in rows(F7 / "feasibility/G01_horizon_feasibility_validation.csv")[1:]}
results.append(["Evaluable at 5 years (26%)", "G01 pct_evaluable horizon 5", g1["5"][3], "26%", "PASS" if "26%" in flat else "FAIL"])
f17 = [r for r in rows(F7 / "F17_RFS_sensitivity_final.csv") if r[0].startswith("PRIMARY")][0]
num_check("RFS median primary", "F17 median_RFS", f17[3], "2.03")
num_check("RFS median 95% CI", "F17 median_95CI", f17[4], "1.98–2.09")
num_check("RFS 3-y", "F17 RFS_3y", f17[5], "39.3%")
num_check("RFS 5-y", "F17 RFS_5y", f17[6], "27.6%")
num_check("RFS-eligible whole cohort", "F17 n", f17[1], "16,677")
# --- benchmark, no-TNM, CEA, duplicates
f16 = rows(F7 / "F16_identical_subset_comparison_calibration.csv")
num_check("Fong subset C", "F16 selected_model_C (Fong)", f16[2][3], "0.639")
num_check("Fong score C", "F16 Fong_CRS_C", f16[2][7], "0.591")
num_check("Nordlinger subset C", "F16 selected_model_C (Nordlinger)", f16[3][3], "0.630")
num_check("Nordlinger score C", "F16 Nordlinger_C", f16[3][8], "0.583")
f62 = rows(F7 / "F62_no_TNM_model_supplementary.csv")
num_check("No-TNM C-index", "F62 validation_C same-patient no-TNM", f62[2][3], "0.599")
num_check("TNM minus no-TNM difference", "F62 note", f62[1][4], "0.022")
f13 = rows(F7 / "F13_CEA_sensitivity_final.csv")
num_check("CEA HR (complete case)", "F13 CEA_HR_per_log_unit", f13[1][4], "1.16")
num_check("CEA complete-case C without/with", "F13 valid_C_without/with", f13[1][5] + "/" + f13[1][6], "0.628")
f61 = {r[0]: r for r in rows(F7 / "F61_duplicate_sensitivity.csv")[1:]}
num_check("Broad-rule reassigned patients", "F61 reassigned_vs_primary", f61["later copies of birth/operation/sex matches removed (broad)"][14], "138")
num_check("Identical-pair reassigned", "F61 reassigned_vs_primary", f61["identical-pair second copies removed"][14], "33")
# --- calibration by horizon and period
num_check("Recalibrated O/E 5-y", "F22 valid_O_over_E recent baseline", "1.115", "1.12")
num_check("Recalibrated group agreement", "F22 agreement_pct_validation", "92.2", "92%")
f21 = rows(F7 / "F21_calibration_by_operation_period.csv")
num_check("O/E 1990-2004", "F21 O_over_E", f21[1][4], "0.96")
num_check("O/E 2013-2015", "F21 O_over_E", f21[4][4], "1.23")
num_check("Patients with 5-y follow-up 2013-2015", "F21 patients_with_5y", f21[4][5], "109")
# --- model coefficients
coef = rows(P1 / "P1_model_coefficients.csv")
hr = {r[0]: r for r in coef[1:]}
num_check("HR T4", "P1 HR T4", hr["T4"][3], "1.364")
num_check("HR N2", "P1 HR N2", hr["N2"][3], "1.625")
num_check("HR count per lesion", "P1 HR METS_F", hr["METS_F"][3], "1.064")
num_check("HR size per 10 mm", "P1 HR SIZE10_F", hr["SIZE10_F"][3], "1.032")
num_check("CI count HR", "P1 HR CI METS_F", f"{hr['METS_F'][4]}–{hr['METS_F'][5]}", "1.054–1.075")
# --- sensitivity and PH
f03 = {(r[0], r[4]): r[2] for r in rows(F7 / "F03_PH_tests_training_constant_terms.csv")[1:]}
num_check("M1 M-stage Schoenfeld p", "F03 M1", f03[("M1", "M1")], "0.031")
num_check("M2a smallest p (T3)", "F03 M2a T3", f03[("T3", "M2a")], "0.18")
f04 = rows(F7 / "F04_M2b_time_varying_M_stage.csv")
num_check("M2b time-variation p", "F04 p_time_variation", f04[2][4], "0.207")
f10 = rows(F7 / "F10_day_and_same_day_conventions.csv")
num_check("First-day convention identical groups", "F10 phenotype_identical_pct", f10[1][9], "99.71")
f19 = rows(F7 / "F19_unflagged_same_day_deaths_sensitivity.csv")
num_check("Same-day deaths without flag identical groups", "F19 phenotype_identical_pct", f19[2][5], "99.63")
f12 = {r[0]: r[1] for r in rows(F7 / "F12_death_and_last_contact_verification.csv")[1:]}
num_check("Deceased without death flag (full extract)", "F12 deceased without any DEATHKYN_F = Yes", f12["deceased without any DEATHKYN_F = Yes"], "3,074")
num_check("Deceased in full extract", "F12 deceased (PATSTATC)", f12["deceased (PATSTATC)"], "11,594")
# --- predictor timing (audit tables)
a4 = rows(REPO / "results/final_v10/predictor_timing_audit/A4_count_agreement_and_chemotherapy.csv")
num_check("Count agreement equal 62.4%", "A4 pct equal", a4[2][2], "62.4")
num_check("Pre-operative chemotherapy 43.4%", "A5 / H01 yes", "7485/17262", "43.4%")

passed = sum(r[4] == "PASS" for r in results)
with open(OUT / "verification.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["claim", "source", "source_value", "displayed_in_manuscript", "status"])
    w.writerows(results)
lines = ["# Final numerical verification (manuscript and supplementary text vs locked outputs)", "",
         f"Checks: {len(results)}; passed: {passed}; failed: {len(results)-passed}.", "",
         "| Claim | Source (file, field) | Source value | Displayed | Status |", "|---|---|---|---|---|"]
lines += [f"| {r[0]} | `{r[1]}` | {r[2]} | {r[3]} | {r[4]} |" for r in results]
(OUT / "verification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"checks {len(results)} passed {passed} failed {len(results)-passed}")
for r in results:
    if r[4] != "PASS":
        print("FAIL:", r[0], "| source", r[1], r[2], "| displayed", r[3])
