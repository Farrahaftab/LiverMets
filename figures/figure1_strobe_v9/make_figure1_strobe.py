#!/usr/bin/env python3
"""
STROBE patient-flow diagram for Paper 1 (Figure 1), generated entirely from the locked v8 outputs.

Nothing on the figure is typed in by hand. Every displayed number is read from a source CSV
(see the field map in the verification report). Before drawing, the script runs automated
consistency checks across the source files. If any check fails, the script writes the
verification report with the discrepancy and DOES NOT draw the figure, so that a disagreement
is reported rather than silently corrected.

Inputs (repository-relative, or set LIVERMET_REPO):
  results/final_v7/F00a_extract_row_counts.csv
  results/final_v7/F01_flow_by_day_convention.csv
  results/final_v7/F02b_selected_model_performance.csv
  results/final_v7/F06_phenotypes_counts_survival_calibration.csv
  results/final_v7/F07_phenotype_definitions.csv
  results/final_v7/F08_phenotype_separation.csv
  results/final_v7/F12_death_and_last_contact_verification.csv
  results/final_v7/F17_RFS_sensitivity_final.csv
  results/final_v7/F30_flow_counts_for_figure1.csv
  results/final_v7/F31_table1_baseline_characteristics.csv
  results/final_v7/F32_supp_S1_included_vs_excluded.csv
  results/final_v7/feasibility/G01_horizon_feasibility_validation.csv
  results/final_v9/paper1/P1_model_coefficients.csv
  results/final_v9/paper1/P1_baseline_survival_by_stratum.csv

Outputs (results/final_v9/figure1/):
  Figure1_STROBE_Cox.png (600 dpi), Figure1_STROBE_Cox.pdf (vector), Figure1_STROBE_Cox.svg (vector),
  verification_report.csv, verification_report.md

Usage:
  python make_figure1_strobe.py                # from a repository checkout
  LIVERMET_REPO=/path/to/LiverMets python make_figure1_strobe.py
"""
import csv
import math
import os
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("LIVERMET_REPO", HERE.parents[1]))
F7 = REPO / "results/final_v7"
P1 = REPO / "results/final_v9/paper1"
OUT = REPO / "results/final_v9/figure1"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------- helpers
RECORDS = []   # every displayed statistic: id, label, displayed, source, field, raw
CHECKS = []    # automated consistency checks: name, expected, observed, status


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def as_int(s):
    """'8,463' or '4,675 (55.2)' -> 8463 / 4675"""
    return int(str(s).split("(")[0].strip().replace(",", ""))


def as_float(s):
    return float(str(s).strip())


def record(rid, label, displayed, source, field, raw):
    RECORDS.append(dict(id=rid, label=label, displayed=displayed, source=source, field=field, raw=raw))


def check(name, expected, observed, tol=0.0, severity="FAIL"):
    """severity FAIL blocks drawing; DISCREPANCY is reported but the source value is still drawn."""
    ok = (abs(float(expected) - float(observed)) <= tol) if isinstance(expected, (int, float)) and isinstance(observed, (int, float)) else (expected == observed)
    status = "PASS" if ok else severity
    CHECKS.append(dict(check=name, expected=expected, observed=observed, status=status))
    return ok


def lookup_row(rows, key_col, key_value):
    header = rows[0]
    k = header.index(key_col)
    for r in rows[1:]:
        if r[k].strip() == key_value:
            return dict(zip(header, r))
    raise KeyError(f"{key_value} not found in column {key_col}")


# ----------------------------------------------------------------------------- 1. patient selection
flow_rows = read_csv(F7 / "F30_flow_counts_for_figure1.csv")
flow = {r[0]: as_int(r[1]) for r in flow_rows[1:]}
src_flow = "results/final_v7/F30_flow_counts_for_figure1.csv"
STEP = {
    "registry": "1 registry",
    "eligible": "2 CINCLUSION=Yes",
    "hepatectomy": "3 hepatectomy",
    "opdate": "4 operation date (year+month)",
    "status": "5 status and last-news",
    "chronology": "6 chronology",
    "followup": "7 positive follow-up or death",
    "analytic": "8 complete TNM (analytic cohort)",
}
N = {k: flow[v] for k, v in STEP.items()}
for k, v in STEP.items():
    record(f"N_{k}", f"Step count: {v}", f"{N[k]:,}", src_flow, f"n where step = '{v}'", flow[v])

# Day-convention table (independent file): mid-month column must equal F30 at every step
conv = read_csv(F7 / "F01_flow_by_day_convention.csv")
conv_hdr = conv[0]
mid_col = conv_hdr.index("mid-month (15th, primary)")
for r in conv[1:]:
    step = r[0].strip()
    if step in flow:
        check(f"F01 mid-month equals F30 at step '{step}'", flow[step], as_int(r[mid_col]))

# Exclusions are differences between consecutive steps
order = ["registry", "eligible", "hepatectomy", "opdate", "status", "chronology", "followup", "analytic"]
EXCL = {}
for a, b in zip(order[:-1], order[1:]):
    EXCL[b] = N[a] - N[b]
    record(f"X_{b}", f"Exclusion at step '{b}' (difference of consecutive counts)", f"{EXCL[b]:,}",
           src_flow, f"difference {STEP[a]} - {STEP[b]}", EXCL[b])
pct_incomplete = 100.0 * EXCL["analytic"] / N["followup"]
record("P_incomplete", "Percent excluded for incomplete TNM of those meeting criteria",
       f"{pct_incomplete:.1f}%", src_flow, "computed: excluded / step 7 count", round(pct_incomplete, 3))

# Cross-check the excluded count against the supplementary characteristics file (independent)
s1 = read_csv(F7 / "F32_supp_S1_included_vs_excluded.csv")
s1_hdr = s1[0]
s1_patients = [r for r in s1[1:] if r[0].strip() == "Patients"][0]
excl_s1 = as_int(s1_patients[s1_hdr.index("Excluded, incomplete TNM (n=8,832)")])
incl_s1 = as_int(s1_patients[s1_hdr.index("Analytic cohort (TNM complete, n=17,262)")])
check("Excluded count: F30 difference equals F32 'Excluded' n", EXCL["analytic"], excl_s1)
check("Analytic count: F30 equals F32 'Analytic cohort' n", N["analytic"], incl_s1)

# ----------------------------------------------------------------------------- 2. development and validation cohorts
t1 = read_csv(F7 / "F31_table1_baseline_characteristics.csv")
t1_hdr = t1[0]
col_total = t1_hdr.index('Total (n=17,262)')
col_dev = t1_hdr.index("Development (<=2009; n=8,463)")
col_val = t1_hdr.index("Validation (>=2010; n=8,799)")
pat = [r for r in t1[1:] if r[0].strip() == "Patients"][0]
N_DEV = as_int(pat[col_dev])
N_VAL = as_int(pat[col_val])
N_TOT = as_int(pat[col_total])
src_t1 = "results/final_v7/F31_table1_baseline_characteristics.csv"
record("N_dev", "Development cohort n", f"{N_DEV:,}", src_t1, "row 'Patients', column Development", N_DEV)
record("N_val", "Validation cohort n", f"{N_VAL:,}", src_t1, "row 'Patients', column Validation", N_VAL)

ev_row = [r for r in t1[1:] if r[0].startswith("Deaths inside the 15-year")][0]
rec_row = [r for r in t1[1:] if r[0].startswith("Deaths recorded")][0]
EV_DEV = as_int(ev_row[col_dev])
EV_VAL = as_int(ev_row[col_val])
REC_DEV = as_int(rec_row[col_dev])
REC_VAL = as_int(rec_row[col_val])
record("EV_dev", "Development events inside 15-year window", f"{EV_DEV:,}", src_t1,
       "row 'Deaths inside the 15-year analysis window (events)', column Development", EV_DEV)
record("EV_val", "Validation events inside 15-year window", f"{EV_VAL:,}", src_t1,
       "row 'Deaths inside the 15-year analysis window (events)', column Validation", EV_VAL)
record("REC_dev", "Development deaths recorded (PATSTATC) - reported in notes only", f"{REC_DEV:,}", src_t1,
       "row 'Deaths recorded (PATSTATC = Deceased)', column Development", REC_DEV)

check("Development + validation equals analytic cohort (F30 step 8)", N["analytic"], N_DEV + N_VAL)
record("BEYOND_dev", "Development deaths beyond 15 years (recorded minus window events), footnote", f"{REC_DEV - EV_DEV}",
       "results/final_v7/F31_table1_baseline_characteristics.csv", "Deaths recorded minus Deaths inside window, Development", REC_DEV - EV_DEV)
check("Development + validation equals F31 total", N_TOT, N_DEV + N_VAL)
f12 = read_csv(F7 / "F12_death_and_last_contact_verification.csv")
f12_win = [r for r in f12[1:] if r[0].startswith("modelling cohort: deaths inside the 15-year window")][0]
F12_WIN = as_int(f12_win[1])
check("Window events (dev + val) equal F12 modelling cohort window events", F12_WIN, EV_DEV + EV_VAL)
f12_rec = [r for r in f12[1:] if r[0].startswith("modelling cohort: deaths recorded")][0]
check("Recorded deaths (dev + val) equal F12 modelling-cohort recorded deaths", as_int(f12_rec[1]), REC_DEV + REC_VAL)
f12_beyond = [r for r in f12[1:] if r[0].startswith("modelling cohort: deaths beyond 15 years")][0]
check("Recorded minus window events (dev + val) equal F12 deaths beyond 15 years",
      as_int(f12_beyond[1]), (REC_DEV + REC_VAL) - (EV_DEV + EV_VAL))

# ----------------------------------------------------------------------------- 3. model information
coef = read_csv(P1 / "P1_model_coefficients.csv")
N_TERMS = len(coef) - 1
strata = read_csv(P1 / "P1_baseline_survival_by_stratum.csv")
N_STRATA = len(strata) - 1
record("N_terms", "Number of terms in M2a", f"{N_TERMS}", "results/final_v9/paper1/P1_model_coefficients.csv",
       "number of data rows", N_TERMS)
record("N_strata", "Number of strata (sex x synchrony x M-stage)", f"{N_STRATA}",
       "results/final_v9/paper1/P1_baseline_survival_by_stratum.csv", "number of data rows", N_STRATA)
check("Strata count equals 2 x 2 x 2 = 8", 8, N_STRATA)

# cut-points and definitions
defs = read_csv(F7 / "F07_phenotype_definitions.csv")
hdr = read_csv(F7 / "F00_headline.csv")
head = {r[0]: r[1] for r in hdr[1:]}
CUT_LO = as_float(head["phenotype_cut_S5_q33"])
CUT_HI = as_float(head["phenotype_cut_S5_q67"])
record("CUT_lo", "Cut-point, lower tertile of predicted 5-y survival", f"{CUT_LO:.4f}",
       "results/final_v7/F00_headline.csv", "phenotype_cut_S5_q33", CUT_LO)
record("CUT_hi", "Cut-point, upper tertile of predicted 5-y survival", f"{CUT_HI:.4f}",
       "results/final_v7/F00_headline.csv", "phenotype_cut_S5_q67", CUT_HI)

# ----------------------------------------------------------------------------- 4. performance (validation)
perf_rows = read_csv(F7 / "F02b_selected_model_performance.csv")
perf = dict(zip(perf_rows[0], perf_rows[1]))
src_perf = "results/final_v7/F02b_selected_model_performance.csv"
C_DEV = as_float(perf["train_C"])
C_VAL = as_float(perf["valid_C"])
C_CI = perf["valid_C_95CI"]
OE5 = as_float(perf["valid_OE_5y"])
OBS5 = as_float(perf["valid_observed_S5"])
PRED5 = as_float(perf["valid_mean_predicted_S5"])
IBS = as_float(perf["IBS_1_7y"])
record("C_dev", "C-index, development (apparent)", f"{C_DEV:.3f}", src_perf, "train_C", C_DEV)
record("C_val", "C-index, validation", f"{C_VAL:.3f}", src_perf, "valid_C", C_VAL)
record("C_ci", "C-index validation 95% CI", C_CI.replace("-", "–"), src_perf, "valid_C_95CI", C_CI)
record("OE5", "Observed/expected 5-y survival, validation", f"{OE5:.2f}", src_perf, "valid_OE_5y", OE5)
record("OBS5", "Observed 5-y survival (KM), validation", f"{OBS5*100:.1f}%", src_perf, "valid_observed_S5", OBS5)
record("PRED5", "Mean predicted 5-y survival, validation", f"{PRED5*100:.1f}%", src_perf, "valid_mean_predicted_S5", PRED5)
record("IBS", "Integrated Brier score 1-7 y, validation", f"{IBS:.3f}", src_perf, "IBS_1_7y", IBS)

g1 = read_csv(F7 / "feasibility/G01_horizon_feasibility_validation.csv")
g5 = lookup_row(g1, "horizon_years", "5")
src_g1 = "results/final_v7/feasibility/G01_horizon_feasibility_validation.csv"
check("5-y observed KM survival: F02b equals G01", OBS5, as_float(g5["observed_KM_survival"]), tol=0.0005)
check("5-y predicted survival: F02b equals G01", PRED5, as_float(g5["mean_predicted_survival"]), tol=0.0005)
check("5-y O/E: F02b equals G01", OE5, as_float(g5["O_over_E"]), tol=0.0005)
record("EVAL5", "Validation patients evaluable at 5 years (%)", f"{as_float(g5['pct_evaluable']):.0f}%",
       src_g1, "pct_evaluable, horizon 5", as_float(g5["pct_evaluable"]))

f8 = read_csv(F7 / "F08_phenotype_separation.csv")
f8d = {r[0]: r[1] for r in f8[1:]}
record("ORD_C", "Ordinal C-index of the three groups, validation", "", "results/final_v7/F08_phenotype_separation.csv", "valid_C_ordinal", float(f8d["valid_C_ordinal"]))
P_VAL = float(f8d["valid_logrank_p"])
P_DEV = float(f8d["train_logrank_p"])
ORD_C = float(f8d["valid_C_ordinal"])
RECORDS[-1]["displayed"] = f"{ORD_C:.3f}"
record("P_val", "Log-rank p, validation (group separation)", f"{P_VAL:.1e}", "results/final_v7/F08_phenotype_separation.csv",
       "valid_logrank_p", P_VAL)
record("P_dev", "Log-rank p, development (group separation)", f"{P_DEV:.1e}", "results/final_v7/F08_phenotype_separation.csv",
       "train_logrank_p", P_DEV)

f17 = read_csv(F7 / "F17_RFS_sensitivity_final.csv")
rfs = [r for r in f17[1:] if r[0].startswith("PRIMARY")][0]
f17h = dict(zip(f17[0], rfs))
RFS_MED = as_float(f17h["median_RFS"])
record("RFS_med", "Median RFS, years (primary, secondary outcome)", f"{RFS_MED:.2f}",
       "results/final_v7/F17_RFS_sensitivity_final.csv", "median_RFS (PRIMARY row)", RFS_MED)
record("RFS_ci", "Median RFS 95% CI", f17h["median_95CI"].replace("-", "–"),
       "results/final_v7/F17_RFS_sensitivity_final.csv", "median_95CI (PRIMARY row)", f17h["median_95CI"])

# follow-up
t1_fu = [r for r in t1[1:] if r[0].startswith("Median follow-up")][0]
FU_DEV = as_float(t1_fu[col_dev])
FU_VAL = as_float(t1_fu[col_val])
record("FU_dev", "Median follow-up, development (reverse KM), years", f"{FU_DEV:.2f}", src_t1,
       "row 'Median follow-up', column Development", FU_DEV)
record("FU_val", "Median follow-up, validation (reverse KM), years", f"{FU_VAL:.2f}", src_t1,
       "row 'Median follow-up', column Validation", FU_VAL)

# C-index CI: F02 (candidate-model table) and F02b (selected-model table) are both locked outputs
f02 = read_csv(F7 / "F02_M_stage_candidates_identical_patients.csv")
f02_m2a = [r for r in f02[1:] if r[0].startswith("M2a")][0]
f02_ci = f02_m2a[f02[0].index("valid_C_95CI")]
check("Validation C-index 95% CI: F02 (candidate table) equals F02b (selected model)", f02_ci, C_CI,
      severity="DISCREPANCY")
record("C_ci_F02", "C-index validation 95% CI in F02 (reported in text)", f02_ci.replace("-", "–"),
       "results/final_v7/F02_M_stage_candidates_identical_patients.csv", "valid_C_95CI, row M2a", f02_ci)

# ----------------------------------------------------------------------------- 5. three prognostic groups
f6 = read_csv(F7 / "F06_phenotypes_counts_survival_calibration.csv")
src_f6 = "results/final_v7/F06_phenotypes_counts_survival_calibration.csv"
GROUPS = ["Favourable", "Intermediate", "Adverse"]
G = {}
for name in GROUPS:
    r = lookup_row(f6, "phenotype", name)
    G[name] = dict(
        dev_n=as_int(r["train_n"]), val_n=as_int(r["valid_n"]), val_deaths=as_int(r["valid_deaths"]),
        val_med=as_float(r["valid_median_OS"]), val_med_ci=r["valid_median_95CI"],
        val_s5=as_float(r["valid_S5_KM"]), dev_s5=as_float(r["train_S5_KM"]),
        val_pred5=as_float(r["valid_mean_predicted_S5"]),
    )
    g = G[name]
    for key, lab, val, fmt in [
        ("dev_n", "development n", g["dev_n"], "{:,}"),
        ("val_n", "validation n", g["val_n"], "{:,}"),
        ("val_deaths", "validation deaths", g["val_deaths"], "{:,}"),
        ("val_med", "validation median OS (years)", g["val_med"], "{:.2f}"),
        ("val_s5", "validation 5-y KM survival", g["val_s5"], "{:.3f}"),
        ("dev_s5", "development 5-y KM survival", g["dev_s5"], "{:.3f}"),
    ]:
        disp = fmt.format(val) if key != "val_s5" and key != "dev_s5" else f"{val*100:.1f}%"
        record(f"{name[:3].upper()}_{key}", f"{name}: {lab}", disp, src_f6, f"row '{name}', column {key}", val)
    record(f"{name[:3].upper()}_med_ci", f"{name}: validation median OS 95% CI", g["val_med_ci"].replace("-", "–"),
           src_f6, f"row '{name}', column valid_median_95CI", g["val_med_ci"])
    record(f"{name[:3].upper()}_pred5", f"{name}: validation mean predicted 5-y (for reference)", f"{g['val_pred5']*100:.1f}%",
           src_f6, f"row '{name}', column valid_mean_predicted_S5", g["val_pred5"])

check("Group development n sum equals development cohort n", N_DEV, sum(G[n]["dev_n"] for n in GROUPS))
check("Group validation n sum equals validation cohort n", N_VAL, sum(G[n]["val_n"] for n in GROUPS))
check("Group validation deaths sum equals validation window events", EV_VAL, sum(G[n]["val_deaths"] for n in GROUPS))
check("Development groups are equal thirds (each = dev n / 3)", N_DEV / 3, G["Favourable"]["dev_n"], tol=0.5)
check("Development group sizes are identical across the three groups",
      True, all(G[n]["dev_n"] == G["Favourable"]["dev_n"] for n in GROUPS))
check("Validation 5-y KM ordering: Favourable > Intermediate > Adverse",
      True, G["Favourable"]["val_s5"] > G["Intermediate"]["val_s5"] > G["Adverse"]["val_s5"])
check("Validation 5-y KM (overall) equals G01 observed survival",
      OBS5, as_float(g5["observed_KM_survival"]), tol=0.0005)

# group-level assignment rule: predicted-survival definition text in F07
defn = {r[0]: r[1] for r in defs[1:]}
check("F07 definition for Favourable references the upper cut-point (from F00)",
      True, f"{CUT_HI:.4f}" in defn["Favourable"])
check("F07 definition for Adverse references the lower cut-point (from F00)",
      True, f"{CUT_LO:.4f}" in defn["Adverse"])

# ----------------------------------------------------------------------------- report and gating
fails = [c for c in CHECKS if c["status"] == "FAIL"]
discrepancies = [c for c in CHECKS if c["status"] == "DISCREPANCY"]


def write_report():
    with open(OUT / "verification_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section", "id", "label", "displayed_on_figure", "source_file", "source_field", "raw_value"])
        for r in RECORDS:
            w.writerow(["statistic", r["id"], r["label"], r["displayed"], r["source"], r["field"], r["raw"]])
        for c in CHECKS:
            w.writerow(["check", c["check"], c["status"], f"expected={c['expected']}", f"observed={c['observed']}", "", ""])
    lines = ["# Figure 1 verification report (STROBE, Cox M2a)", "",
             f"Automated checks: {len(CHECKS)} run, {len(CHECKS)-len(fails)} passed, {len(fails)} failed.", "",
             "## Displayed statistics and their sources", "",
             "| ID | Label | Displayed | Source file | Field | Raw |", "|---|---|---|---|---|---|"]
    for r in RECORDS:
        lines.append(f"| {r['id']} | {r['label']} | {r['displayed']} | `{r['source']}` | {r['field']} | {r['raw']} |")
    lines += ["", "## Consistency checks", "", "| Check | Expected | Observed | Status |", "|---|---|---|---|"]
    for c in CHECKS:
        lines.append(f"| {c['check']} | {c['expected']} | {c['observed']} | **{c['status']}** |")
    if discrepancies:
        lines += ["", "## Discrepancies between locked outputs (reported, NOT corrected; figure shows the F02b value)", ""]
        lines += [f"- {c['check']}: F02 = {c['expected']}, F02b = {c['observed']}" for c in discrepancies]
    if fails:
        lines += ["", "## Failed checks (figure NOT drawn)", ""]
        lines += [f"- {c['check']}: expected {c['expected']}, observed {c['observed']}" for c in fails]
    (OUT / "verification_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


write_report()
if fails:
    print(f"{len(fails)} check(s) FAILED. Figure not drawn. See {OUT/'verification_report.md'}")
    sys.exit(1)
print(f"{len(CHECKS)-len(fails)-len(discrepancies)} checks passed, {len(discrepancies)} discrepancy(ies) reported. Writing figure to {OUT}")
for c in discrepancies:
    print(f"DISCREPANCY: {c['check']}: F02 = {c['expected']}, F02b = {c['observed']}")

# ----------------------------------------------------------------------------- 6. drawing
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "pdf.fonttype": 42, "svg.fonttype": "none",
})

NAVY = "#1B3A5C"
NAVY_EDGE = "#0F2540"
RED_FILL = "#FBE3E0"
RED_EDGE = "#A93226"
DEV_FILL = "#E3F1E4"
DEV_EDGE = "#1E7B3C"
VAL_FILL = "#FDEBD6"
VAL_EDGE = "#C66A12"
GRP_COL = {"Favourable": "#1F7A6E", "Intermediate": "#C98A12", "Adverse": "#A93226"}
GREY = "#3D4B5A"

fig = plt.figure(figsize=(7.2, 12.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 150)
ax.axis("off")


def box(x, y, w, h, fc, ec, lw=0.9, radius=0.9):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                       fc=fc, ec=ec, lw=lw, zorder=2)
    ax.add_patch(p)


def arrow(x1, y1, x2, y2, color=GREY, lw=0.9, style="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=0), zorder=3)


def line(xs, ys, color=GREY, lw=0.9, ls="-"):
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=1, solid_capstyle="butt")


def fmt_n(n):
    return f"{n:,}"


SUPER = {"-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}


def sci(p):
    """1.96e-52 -> '2.0 × 10⁻⁵²' (one decimal in the mantissa)"""
    exp = int(math.floor(math.log10(p)))
    mant = p / 10 ** exp
    if round(mant, 1) >= 10:
        mant, exp = mant / 10, exp + 1
    return f"{mant:.1f} × 10" + "".join(SUPER[c] for c in str(exp))


# title
ax.text(50, 148.2, "Figure 1. STROBE patient flow: selection, development and temporal validation",
        ha="center", va="center", fontsize=8.6, weight="bold", color="#1A1A1A")

# --- selection column (navy flow boxes, red exclusion boxes)
MX, MW, MH = 6, 58, 6.2          # main box x, width, height
EX, EW, EH = 72, 26, 5.4          # exclusion box x, width, height
top = 141.0
step_y = {}
steps = [
    ("registry", "LiverMetSurvey registry", None),
    ("eligible", "Recorded as eligible (CINCLUSION = Yes)", "not recorded as eligible"),
    ("hepatectomy", "Hepatectomy recorded", "no hepatectomy recorded"),
    ("opdate", "Operation date recorded (year and month)", "no operation date"),
    ("status", "Vital status and last-news date recorded", "missing status or last-news"),
    ("chronology", "Chronology consistent", "inconsistent dates"),
    ("followup", "Positive follow-up or death", "no follow-up and not dead"),
    ("analytic", "Complete TNM staging: analytic cohort", "incomplete TNM staging"),
]
y = top
for i, (key, title, excl_label) in enumerate(steps):
    last = key == "analytic"
    fc = NAVY if not last else "#0E2A47"
    box(MX, y - MH, MW, MH, fc, NAVY_EDGE)
    count_txt = f"n = {fmt_n(N[key])}" if not last else f"n = {fmt_n(N[key])}   (analytic cohort)"
    ax.text(MX + MW / 2, y - 2.1, title, ha="center", va="center", fontsize=7.4, weight="bold", color="white", zorder=4)
    ax.text(MX + MW / 2, y - 4.6, count_txt, ha="center", va="center", fontsize=7.0, color="white", zorder=4)
    step_y[key] = y
    if excl_label is not None:
        ex_n = EXCL[key]
        ex_y = y - 5.0 - EH / 2 + 2.8
        box(EX, ex_y - EH / 2 + 0.2, EW, EH, RED_FILL, RED_EDGE, lw=0.8)
        extra = f"\n{pct_incomplete:.1f}% of patients meeting criteria" if key == "analytic" else ""
        ax.text(EX + EW / 2, ex_y + 0.3,
                f"Excluded: {excl_label}\nn = {fmt_n(ex_n)}{extra}",
                ha="center", va="center", fontsize=6.3, color="#6E1C15", zorder=4, linespacing=1.25)
        line([MX + MW, EX], [ex_y, ex_y], color=RED_EDGE, lw=0.7, ls=(0, (3, 2)))
    if not last:
        arrow(MX + MW / 2, y - MH, MX + MW / 2, y - MH - 3.0)
    y -= 9.6

analytic_bottom = step_y["analytic"] - MH
# split arrows to development and validation
DEV_X, DEV_W = 2, 40
VAL_X, VAL_W = 56, 42
split_y = analytic_bottom - 3.4
line([MX + MW / 2, MX + MW / 2], [analytic_bottom, split_y], color=GREY)
line([DEV_X + DEV_W / 2, VAL_X + VAL_W / 2], [split_y, split_y], color=GREY)
arrow(DEV_X + DEV_W / 2, split_y, DEV_X + DEV_W / 2, split_y - 2.6)
arrow(VAL_X + VAL_W / 2, split_y, VAL_X + VAL_W / 2, split_y - 2.6)

# --- development and validation cohorts (green = development, orange = validation)
coh_y = split_y - 2.6 - 7.4
box(DEV_X, coh_y, DEV_W, 7.4, DEV_FILL, DEV_EDGE, lw=1.1)
ax.text(DEV_X + DEV_W / 2, coh_y + 5.4, "Development cohort", ha="center", va="center", fontsize=7.6, weight="bold", color=DEV_EDGE)
ax.text(DEV_X + DEV_W / 2, coh_y + 3.0, "operated 2009 or earlier", ha="center", va="center", fontsize=6.6, color="#1A1A1A")
ax.text(DEV_X + DEV_W / 2, coh_y + 1.0, f"n = {fmt_n(N_DEV)}   |   events = {fmt_n(EV_DEV)}", ha="center", va="center", fontsize=7.0, weight="bold", color="#1A1A1A")
box(VAL_X, coh_y, VAL_W, 7.4, VAL_FILL, VAL_EDGE, lw=1.1)
ax.text(VAL_X + VAL_W / 2, coh_y + 5.4, "Temporal validation cohort", ha="center", va="center", fontsize=7.6, weight="bold", color=VAL_EDGE)
ax.text(VAL_X + VAL_W / 2, coh_y + 3.0, "operated 2010 or later", ha="center", va="center", fontsize=6.6, color="#1A1A1A")
ax.text(VAL_X + VAL_W / 2, coh_y + 1.0, f"n = {fmt_n(N_VAL)}   |   events = {fmt_n(EV_VAL)}", ha="center", va="center", fontsize=7.0, weight="bold", color="#1A1A1A")

# --- model development (green) and validation (orange)
mod_y = coh_y - 3.0 - 9.0
arrow(DEV_X + DEV_W / 2, coh_y, DEV_X + DEV_W / 2, mod_y + 9.0 + 0.2)
arrow(VAL_X + VAL_W / 2, coh_y, VAL_X + VAL_W / 2, mod_y + 9.0 + 0.2)
box(DEV_X, mod_y, DEV_W, 9.0, "white", DEV_EDGE, lw=1.0)
ax.text(DEV_X + 1.5, mod_y + 7.4, "Model development (training only)", ha="left", va="center", fontsize=7.0, weight="bold", color=DEV_EDGE)
ax.text(DEV_X + 1.5, mod_y + 5.0,
        f"Stratified Cox model M2a: {N_TERMS} terms,\n{N_STRATA} strata (sex x synchrony x M-stage)",
        ha="left", va="center", fontsize=6.5, color="#1A1A1A", linespacing=1.3)
ax.text(DEV_X + 1.5, mod_y + 1.9,
        f"Group cut-points (training tertiles):\npredicted 5-y survival {CUT_LO:.4f} and {CUT_HI:.4f}",
        ha="left", va="center", fontsize=6.5, color="#1A1A1A", linespacing=1.3)

box(VAL_X, mod_y, VAL_W, 9.0, "white", VAL_EDGE, lw=1.0)
ax.text(VAL_X + 1.5, mod_y + 7.4, "Validation: fixed model, no refit", ha="left", va="center", fontsize=7.0, weight="bold", color=VAL_EDGE)
ax.text(VAL_X + 1.5, mod_y + 4.9,
        f"C-index {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')})\nO/E at 5 years {OE5:.2f}; IBS (1-7 y) {IBS:.3f}",
        ha="left", va="center", fontsize=6.5, color="#1A1A1A", linespacing=1.3)
ax.text(VAL_X + 1.5, mod_y + 1.6,
        f"5-y survival: observed {OBS5*100:.1f}%, predicted {PRED5*100:.1f}%\nFavourable/Intermediate/Adverse groups applied",
        ha="left", va="center", fontsize=6.5, color="#1A1A1A", linespacing=1.3)

# --- three prognostic groups
grp_top = mod_y - 4.0
bus_y = grp_top + 1.8
line([DEV_X + DEV_W / 2, DEV_X + DEV_W / 2], [mod_y, bus_y], color=GREY)
line([VAL_X + VAL_W / 2, VAL_X + VAL_W / 2], [mod_y, bus_y], color=GREY)
COL_W = 30.6
COL_X = {"Favourable": 1.5, "Intermediate": 34.7, "Adverse": 67.9}
COL_CX = {n: COL_X[n] + COL_W / 2 for n in GROUPS}
line([COL_CX["Favourable"], COL_CX["Adverse"]], [bus_y, bus_y], color=GREY)
line([DEV_X + DEV_W / 2, VAL_X + VAL_W / 2], [bus_y, bus_y], color=GREY)
for n in GROUPS:
    arrow(COL_CX[n], bus_y, COL_CX[n], grp_top + 0.2)

defn_txt = {"Favourable": f"predicted 5-y ≥ {CUT_HI:.4f}", "Intermediate": f"{CUT_LO:.4f} to < {CUT_HI:.4f}", "Adverse": f"predicted 5-y < {CUT_LO:.4f}"}
GH = 31.0
for n in GROUPS:
    x = COL_X[n]
    g = G[n]
    box(x, grp_top - GH, COL_W, GH, "white", GRP_COL[n], lw=1.3)
    box(x, grp_top - 4.8, COL_W, 4.8, GRP_COL[n], GRP_COL[n], lw=0.0)
    ax.text(COL_CX[n], grp_top - 2.4, f"{n} group", ha="center", va="center", fontsize=7.8, weight="bold", color="white", zorder=4)
    ax.text(COL_CX[n], grp_top - 7.2, defn_txt[n], ha="center", va="center", fontsize=6.3, color="#1A1A1A", style="italic")
    rows = [
        ("Development n", f"{fmt_n(g['dev_n'])}"),
        ("Development 5-y KM", f"{g['dev_s5']*100:.1f}%"),
        ("Validation n (deaths)", f"{fmt_n(g['val_n'])} ({fmt_n(g['val_deaths'])})"),
        ("Validation median OS, y", f"{g['val_med']:.2f}"),
        ("  95% CI", f"{g['val_med_ci'].replace('-', '–')}"),
        ("Validation 5-y KM", f"{g['val_s5']*100:.1f}%"),
    ]
    yy = grp_top - 11.0
    for lab, val in rows:
        ax.text(x + 1.4, yy, lab, ha="left", va="center", fontsize=6.2, color=GREY)
        ax.text(x + COL_W - 1.4, yy, val, ha="right", va="center", fontsize=6.6, color="#1A1A1A", weight="bold")
        yy -= 2.9
ax.text(50, grp_top - GH - 1.6,
        "Development group n is one third of the development cohort (training tertiles). Validation outcomes use the fixed cut-points.",
        ha="center", va="center", fontsize=5.9, color=GREY, style="italic")

# --- performance and survival summary box
sum_y = grp_top - GH - 4.6 - 16.0
box(2, sum_y, 96, 15.6, NAVY, NAVY_EDGE, lw=0.9)
ax.text(50, sum_y + 13.2, "Model performance and survival findings (temporal validation unless stated)",
        ha="center", va="center", fontsize=7.6, weight="bold", color="white")
lines_txt = [
    f"Group separation: log-rank p = {sci(P_VAL)} in validation; p = {sci(P_DEV)} in development.  Ordinal C-index {ORD_C:.3f}.",
    f"Discrimination: C-index {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')}) in validation vs {C_DEV:.3f} in development (apparent).",
    f"Calibration: predicted 5-y survival {PRED5*100:.1f}% vs observed {OBS5*100:.1f}% (O/E {OE5:.2f}); the model under-predicts survival.",
    f"Evaluable at 5 years: {as_float(g5['pct_evaluable']):.0f}% of validation patients (median follow-up: development {FU_DEV:.2f} y, validation {FU_VAL:.2f} y).",
    f"Secondary outcome: median recurrence-free survival {RFS_MED:.2f} years (95% CI {f17h['median_95CI'].replace('-', '–')}).",
]
for i, t in enumerate(lines_txt):
    ax.text(5, sum_y + 10.4 - i * 2.1, "•  " + t, ha="left", va="center", fontsize=6.2, color="white")
FOOT_Y = sum_y - 2.2

# footnote
ax.text(2, FOOT_Y,
        "Excluded counts are differences between consecutive steps.\n"
        "Events = deaths within the 15-year analysis window. Development recorded deaths: "
        f"{fmt_n(REC_DEV)}; {fmt_n(REC_DEV - EV_DEV)} of these fall beyond 15 years and are censored in the models.\n"
        "TNM = tumour-node-metastasis; CRLM = colorectal liver metastases; M2a = stratified Cox model;\n"
        "KM = Kaplan–Meier; O/E = observed/expected; IBS = integrated Brier score; RFS = recurrence-free survival.\n"
        "Source: locked v8 analysis (results/final_v7) and Paper 1 model outputs (results/final_v9/paper1).\n"
        "Every number is generated by make_figure1_strobe.py; see verification_report.md.",
        ha="left", va="top", fontsize=5.4, color=GREY, linespacing=1.35)

bottom = FOOT_Y - 10.0
ax.set_ylim(bottom, 150)
fig.set_size_inches(7.2, (150 - bottom) * 0.072)
png = OUT / "Figure1_STROBE_Cox.png"
pdf = OUT / "Figure1_STROBE_Cox.pdf"
svg = OUT / "Figure1_STROBE_Cox.svg"
fig.savefig(png, dpi=600, facecolor="white")
fig.savefig(pdf, facecolor="white")
fig.savefig(svg, facecolor="white")
print("written:", png.name, pdf.name, svg.name)

# ----------------------------------------------------------------------------- 7. manuscript caption (generated from the same values)
caption = (
    f"**Figure 1.** STROBE patient flow for the development and temporal validation of the prognostic model. "
    f"Of {fmt_n(N['registry'])} registry records, {fmt_n(N['eligible'])} were recorded as eligible and "
    f"{fmt_n(N['analytic'])} patients met all eligibility criteria and had complete TNM staging; "
    f"{fmt_n(EXCL['analytic'])} ({pct_incomplete:.1f}% of the {fmt_n(N['followup'])} patients meeting criteria) were excluded for incomplete staging. "
    f"Patients operated in 2009 or earlier formed the development cohort (n = {fmt_n(N_DEV)}; {fmt_n(EV_DEV)} events within 15 years) and "
    f"those operated in 2010 or later the temporal validation cohort (n = {fmt_n(N_VAL)}; {fmt_n(EV_VAL)} events). "
    f"The stratified Cox model (M2a; {N_TERMS} terms; {N_STRATA} strata) was fitted in development only and applied unchanged to validation. "
    f"Three prognostic groups were defined by training-era tertiles of predicted 5-year survival (cut-points {CUT_LO:.4f} and {CUT_HI:.4f}). "
    f"In validation, the C-index was {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')}; see verification report for an F02 discrepancy), predicted 5-year survival was {PRED5*100:.1f}% against "
    f"{OBS5*100:.1f}% observed, and the groups separated overall survival (log-rank p = {sci(P_VAL)}). "
    f"Recurrence-free survival (secondary) had a median of {RFS_MED:.2f} years. "
    f"Counts are generated from the locked v8 outputs; excluded counts are differences between consecutive steps."
)
(OUT / "Figure1_caption.md").write_text(caption + "\n", encoding="utf-8")
print("caption written")
