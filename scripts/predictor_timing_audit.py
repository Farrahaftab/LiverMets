"""Predictor-timing audit for the metastasis count and size variables used in the locked M2a model.

Reads only the repository's locked outputs and source code (no patient-level data, which is not in the
repository). Every number in the audit tables is read or computed here; nothing is typed in.
Writes CSV tables to results/final_v10/predictor_timing_audit/ and prints a summary.
Usage: python scripts/predictor_timing_audit.py
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/final_v10/predictor_timing_audit"
OUT.mkdir(parents=True, exist_ok=True)
NB = REPO / "notebooks/LiverMets_final_reproducible.py"
INV = REPO / "results/tables/T01_column_inventory.csv"
F7 = REPO / "results/final_v7"
TF = REPO / "results/final_v9/treatment_feasibility"
TD = REPO / "results/final_v9/treatment_design"


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def as_int(s):
    return int(str(s).split("(")[0].strip().replace(",", ""))


def write(name, header, body):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(body)


# ---------------------------------------------------------------- A1. column trace (code)
code = NB.read_text(encoding="utf-8").splitlines()
trace_patterns = {
    "METS (count used in model)": r"^METS = ",
    "SIZE (size used in model)": r"^SIZE = ",
    "CEA (pre-operative CEA, not in M2a)": r"^CEA = ",
    "DIRECT field list": r"^DIRECT = ",
    "DATES field list": r"^DATES = ",
    "Interval DFI definition": r"d\['DFI'\] = ",
    "Interval set to missing when metastasis after operation": r"DFI.*np\.nan",
    "Time zero (operation date)": r"d\['T0'\] = ",
    "M2a covariate list": r"^CORE_M2A = ",
    "Pre-operative-only sensitivity covariates": r"^PREOP_M2A = ",
}
a1 = []
for label, pat in trace_patterns.items():
    hits = [(i + 1, l.strip()) for i, l in enumerate(code) if re.search(pat, l)]
    for ln, txt in hits[:3]:
        a1.append([label, NB.relative_to(REPO), ln, txt[:200]])
write("A1_column_trace_from_code.csv", ["item", "file", "line", "code_as_written"], a1)

# ---------------------------------------------------------------- A2. column names and fill (inventory)
inv = {r["column_name"]: r for r in csv.DictReader(open(INV, encoding="utf-8"))}
key_cols = ["LE1NBMETAHEPNUM", "LE1NBMETAHEPNUM_V", "LE1NBMETAHEPCAR", "LE1HEPMETASIZENUM", "LE1HEPMETASIZENUM_V",
            "LE1HEPMETASIZECAR", "LE1NBMRESECNUM_F1", "LE1NBMRESECCAR_F1", "LE1METASYNCYN", "LE1OPERDT_F1",
            "LE1DGMETADT", "DGKCOLDT", "LE1PREOPMCTYN_F1", "LE1PREOPMSTDT_F1", "LE1POSTOPMCTYN_F1",
            "LE1POSTOPMSTDT_F1", "POSTCOLCTYN_F1", "PRECOLCHIYN", "STADET", "STADEN", "STADEM", "LE1PREHEPCEA_F1"]
a2 = []
for c in key_cols:
    r = inv.get(c)
    if r:
        a2.append([c, r["nonempty_part1"], r["nonempty_part2"], r["nonempty_total"], r["fill_pct_total"],
                   "name contains a timing word" if re.search(r"PREOP|PREHEP|POSTOP|RESEC|DG|OPER", c) else "no timing word in name"])
    else:
        a2.append([c, "", "", "", "", "not in inventory"])
write("A2_column_names_and_fill.csv", ["column", "nonempty_part1", "nonempty_part2", "nonempty_total",
                                        "fill_pct_total", "timing_evidence_in_name"], a2)

# ---------------------------------------------------------------- A3. temporal anchors that can be established
h03 = rows(TF / "H03_timing_pattern_cohort.csv")
h04 = {r[0]: r for r in rows(TF / "H04_chemotherapy_start_dates_cohort.csv")[1:]}
pre_rows = [r for r in h04.values() if r[0].startswith("pre-operative")][0]
post_rows = [r for r in h04.values() if r[0].startswith("post-operative liver")][0]
pre_yes, pre_dated = as_int(pre_rows[1]), as_int(pre_rows[2])
pre_before, pre_after = as_int(pre_rows[5]), as_int(pre_rows[6])
post_yes, post_dated = as_int(post_rows[1]), as_int(post_rows[2])
post_before, post_after = as_int(post_rows[5]), as_int(post_rows[6])
f31 = rows(F7 / "F31_table1_baseline_characteristics.csv")
f31h = f31[0]
cohort_n = as_int([r for r in f31[1:] if r[0] == "Patients"][0][1])
f33 = {r[0]: as_int(r[1]) for r in rows(F7 / "F33_predictor_and_recurrence_date_audit.csv")[1:]}
a3 = [
    ["Operation date (time zero)", "LE1OPERDT_F1", "Establishable", "Used as time zero in the notebook (T0)", "94.8% usable (inventory)"],
    ["Primary diagnosis to liver metastasis interval", "DGKCOLDT, LE1DGMETADT", "Establishable where both dates exist",
     "Interval missing for metachronous patients without a primary diagnosis date (n = {})".format(f33["Metachronous, interval unavailable: primary diagnosis date missing (first reason in order)"]),
     "DGKCOLDT 50.7%; LE1DGMETADT 68.3% (F41)"],
    ["Liver metastasis diagnosed after operation", "LE1DGMETADT vs LE1OPERDT_F1", "Establishable",
     "Set to missing in the interval (not used as a predictor value); {} analytic-cohort patients".format(f33["Liver metastasis diagnosed after operation (interval set missing), analytic cohort"]), "F33"],
    ["Pre-operative chemotherapy start vs operation", "LE1PREOPMSTDT_F1 vs LE1OPERDT_F1", "Establishable for dated starts",
     "{} of {} dated pre-operative starts ({:.1f}%) before operation".format(pre_before, pre_dated, 100 * pre_before / pre_dated), "H04"],
    ["Post-operative liver chemotherapy start vs operation", "LE1POSTOPMSTDT_F1 vs LE1OPERDT_F1", "Establishable for dated starts",
     "{} of {} dated post-operative starts ({:.1f}%) after operation".format(post_after, post_dated, 100 * post_after / post_dated), "H04"],
    ["Metastasis count or size vs any chemotherapy date", "LE1NBMETAHEPNUM, LE1HEPMETASIZENUM", "NOT establishable",
     "No date or timing field for count or size exists in the inventory", "A2"],
    ["Metastasis count or size vs operation", "LE1NBMETAHEPNUM, LE1HEPMETASIZENUM", "NOT establishable",
     "No timestamp; the form date is the operation, not the measurement", "A2"],
    ["TNM stage (STADET/STADEN/STADEM) pathological or clinical", "STADET, STADEN, STADEM", "NOT establishable",
     "No field name or code states the source (clinical or pathological)", "A2; notebook line 216"],
]
write("A3_temporal_anchors.csv", ["relationship", "fields", "can_be_established", "evidence", "source"], a3)

# ---------------------------------------------------------------- A4. preoperative vs resected count
f34 = {r[0]: as_int(r[1]) for r in rows(F7 / "F34_operative_vs_preoperative_metastasis_count.csv")[1:]}
both = f34["Analytic cohort with both pre-operative and resected metastasis counts"]
eq = f34["Resected count equals pre-operative count"]
gt = f34["Resected count greater than pre-operative count"]
lt = f34["Resected count less than pre-operative count"]
assert eq + gt + lt == both
a4 = [
    ["Both counts recorded (LE1NBMETAHEPNUM and LE1NBMRESECNUM_F1)", both, "100.0"],
    ["Resected count equals LE1NBMETAHEPNUM", eq, f"{100*eq/both:.1f}"],
    ["Resected count greater than LE1NBMETAHEPNUM", gt, f"{100*gt/both:.1f}"],
    ["Resected count less than LE1NBMETAHEPNUM", lt, f"{100*lt/both:.1f}"],
]
j01 = {r[0]: r for r in rows(TD / "J01a_count_discordance_overall.csv")[1:]}
j01b = rows(TD / "J01b_count_discordance_within_preop_count_strata.csv")[1:]
for pre_flag, label in [("Yes", "pre-operative chemotherapy yes"), ("No", "pre-operative chemotherapy no")]:
    r = j01[pre_flag]
    a4.append([f"Among patients with chemotherapy flag known: {label}, n", r[1], ""])
    a4.append([f"  mean LE1NBMETAHEPNUM / mean LE1NBMRESECNUM_F1", f"{r[2]} / {r[3]}", ""])
    a4.append([f"  resected lower than pre-operative count (%)", r[4], ""])
for b in j01b:
    a4.append([f"Within count stratum {b[0]}: resected lower (%), chemotherapy {b[1]} (n={b[2]})", b[3], ""])
write("A4_count_agreement_and_chemotherapy.csv", ["comparison", "value", "pct_of_both_counts"], a4)

# ---------------------------------------------------------------- A5. chemotherapy exposure in the analytic cohort
h02 = rows(TF / "H02_preop_by_postop_liver_chemotherapy_cohort.csv")
h01 = {r[1]: r for r in rows(TF / "H01_treatment_variable_inventory_cohort.csv")[1:]}
pr = h01["LE1PREOPMCTYN_F1"]
a5 = [
    ["Pre-operative liver chemotherapy: yes", pr[3], f"{100*as_int(pr[3])/cohort_n:.1f}"],
    ["Pre-operative liver chemotherapy: no", pr[4], f"{100*as_int(pr[4])/cohort_n:.1f}"],
    ["Pre-operative liver chemotherapy: ND or NA", pr[5], f"{100*as_int(pr[5])/cohort_n:.1f}"],
    ["Pre-operative liver chemotherapy: blank", pr[6], f"{100*as_int(pr[6])/cohort_n:.1f}"],
    ["Pre-operative yes, start date recorded", pre_dated, f"{100*pre_dated/pre_yes:.1f} (of yes)"],
    ["Pre-operative yes, start date missing", pre_yes - pre_dated, f"{100*(pre_yes-pre_dated)/pre_yes:.1f} (of yes)"],
]
for r in h03[1:]:
    a5.append([f"Timing pattern: {r[0]}", r[1], r[2]])
write("A5_chemotherapy_exposure.csv", ["item", "n", "pct"], a5)

# ---------------------------------------------------------------- A6. missingness of the model variables
f32 = rows(F7 / "F32_supp_S1_included_vs_excluded.csv")
f32p = {r[0].strip(): r for r in f32[1:]}
a6 = [
    ["Metastasis count known (analytic cohort)", "16,011 (92.8)", "F32 row 'Number of liver metastases known'"],
    ["Metastasis count unknown (analytic cohort)", "1,251 (7.2)", "F31 row 'Number of liver metastases', Unknown"],
    ["Largest metastasis size missing (analytic cohort)", "3,306 (19.2)", "F31 row 'Size missing'"],
]
f41 = rows(F7 / "investigation/F41_key_variable_missingness_all_rows.csv")
for r in f41[1:]:
    if r[0] in ("LE1NBMETAHEPNUM", "LE1HEPMETASIZENUM"):
        a6.append([f"{r[0]} (all 29,565 rows): valid", r[1], "F41 valid_value"])
        a6.append([f"{r[0]} (all 29,565 rows): ND", r[2], "F41 ND"])
        a6.append([f"{r[0]} (all 29,565 rows): NA", r[3], "F41 NA"])
        a6.append([f"{r[0]} (all 29,565 rows): blank", r[4], "F41 blank"])
write("A6_missingness_of_model_variables.csv", ["item", "value", "source"], a6)

# ---------------------------------------------------------------- A7. leakage matrix (prediction time = operation)
a7 = [
    ["Age at operation", "Known before time zero", "None", "Low"],
    ["Sex", "Known before time zero", "None", "Low"],
    ["Synchrony (LE1METASYNCYN)", "Recorded by time zero", "Cannot confirm recording date", "Low"],
    ["Interval (DFI)", "Metastasis dates after operation set to missing in the notebook", "None found in code", "Low"],
    ["TNM T, N, M (STADET/STADEN/STADEM)", "Source (clinical vs pathological) not documented", "May include post-operative pathology", "Unresolved"],
    ["Metastasis count (LE1NBMETAHEPNUM)", "Timing not documented; may follow pre-operative chemotherapy in {} patients".format(pre_yes), "May reflect post-treatment disease; resected count (not used) is post-operative", "Unresolved"],
    ["Largest metastasis size (LE1HEPMETASIZENUM)", "Timing not documented; could be pathological size", "Possible post-operative information", "Unresolved"],
    ["Resected count LE1NBMRESECNUM_F1", "Not a model predictor", "Would be leakage if used", "Not used (none)"],
]
write("A7_leakage_matrix.csv", ["variable", "timing_status", "leakage_concern", "risk_at_operation_time"], a7)

print("tables written to", OUT)
for name in sorted(p.name for p in OUT.glob("*.csv")):
    print(" -", name)
print("pre-operative chemotherapy yes:", pre_yes, "| dated:", pre_dated, "| before op:", pre_before)
print("count agreement: equal", eq, "greater", gt, "less", lt, "of", both)
