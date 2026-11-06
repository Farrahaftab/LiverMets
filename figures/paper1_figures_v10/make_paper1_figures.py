#!/usr/bin/env python3
"""
Paper 1 figure set (clean rebuild, v10). Every figure is generated from the locked v8 outputs.

Figures
  Figure 1  STROBE patient flow, development and temporal validation, three prognostic groups
  Figure 2  Overall survival by prognostic group, temporal validation cohort (Kaplan-Meier, numbers at risk)
  Figure S1 Recurrence-free survival by prognostic group, temporal validation cohort (Kaplan-Meier)
  Figure S2 Calibration by validation decile of predicted 5-year survival
  Figure S3 Observed/expected 5-year survival by operation period

Rules
  * No statistic is typed in. Every number is read from a verified source file and field.
  * Each figure is checked against the locked outputs. A FAIL stops the build of that figure and is
    written to the discrepancy report. A DISCREPANCY (two locked outputs disagree) is reported and the
    value from the file named in the figure logic is drawn; nothing is silently corrected.
  * Outputs per figure: PNG (600 dpi), PDF (vector, editable text), SVG (vector), caption (Markdown),
    plus a shared verification_report.md / .csv listing the source file and field for every displayed value.

Inputs (repository-relative)
  results/final_v7/F00_headline.csv, F06_..., F08_..., F17_..., F20_..., F21_..., F30_..., F31_..., F12_..., F02_..., F02b_...
  results/final_v7/feasibility/G01_horizon_feasibility_validation.csv
  results/final_v7/F01_flow_by_day_convention.csv, F32_supp_S1_included_vs_excluded.csv, F07_phenotype_definitions.csv
  results/final_v9/paper1/P1_model_coefficients.csv, P1_baseline_survival_by_stratum.csv
  results/final_v9/paper1/F80_km_curve_points_by_group.csv and F81_numbers_at_risk_by_group.csv
      (derived Kaplan-Meier curve points and numbers at risk, written by the locked notebook's figure-data
       export block; they contain no model or cohort information beyond the curves themselves)

Outputs: results/final_v10/paper1_figures/
Usage:   python make_paper1_figures.py        (set LIVERMET_REPO to override the repository root)
"""
import csv
import math
import os
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
OUT = REPO / "results/final_v10/paper1_figures"
OUT.mkdir(parents=True, exist_ok=True)

GROUPS = ["Favourable", "Intermediate", "Adverse"]
GRP_COL = {"Favourable": "#1F7A6E", "Intermediate": "#C98A12", "Adverse": "#A93226"}
NAVY, NAVY_EDGE = "#1B3A5C", "#0F2540"
RED_FILL, RED_EDGE = "#FBE3E0", "#A93226"
DEV_FILL, DEV_EDGE = "#E3F1E4", "#1E7B3C"
VAL_FILL, VAL_EDGE = "#FDEBD6", "#C66A12"
GREY, INK = "#3D4B5A", "#1A1A1A"

RECORDS = []   # every displayed value: figure, id, label, displayed, source, field, raw
CHECKS = []    # automated checks: figure, name, expected, observed, status
FAILED_FIGS = set()


# ----------------------------------------------------------------------------- helpers
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def rel(path):
    return str(Path(path).relative_to(REPO)).replace("\\", "/")


def as_int(s):
    return int(str(s).split("(")[0].strip().replace(",", ""))


def as_float(s):
    return float(str(s).strip())


def pick(rows, key_col, key_val, startswith=False):
    h = rows[0]
    k = h.index(key_col)
    for r in rows[1:]:
        v = r[k].strip()
        if (v.startswith(key_val) if startswith else v == key_val):
            return dict(zip(h, r))
    raise KeyError(f"{key_val!r} not found in column {key_col!r} of {rows[0][:3]}")


def record(fig, rid, label, displayed, source, field, raw):
    RECORDS.append(dict(figure=fig, id=rid, label=label, displayed=displayed,
                        source=source, field=field, raw=raw))


def check(fig, name, expected, observed, tol=0.0, severity="FAIL"):
    if isinstance(expected, (int, float)) and isinstance(observed, (int, float)):
        ok = abs(float(expected) - float(observed)) <= tol
    else:
        ok = expected == observed
    status = "PASS" if ok else severity
    CHECKS.append(dict(figure=fig, check=name, expected=expected, observed=observed, status=status))
    if status == "FAIL":
        FAILED_FIGS.add(fig)
    return ok


def sci(p):
    exp = int(math.floor(math.log10(p)))
    mant = p / 10 ** exp
    if round(mant, 1) >= 10:
        mant, exp = mant / 10, exp + 1
    sup = {"-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    return f"{mant:.1f} × 10" + "".join(sup[c] for c in str(exp))


def half_up(x, places=2):
    """Round a source value half-up using its decimal string (0.955 -> 0.96), as the manuscript text does."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(1).scaleb(-places)
    return str(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def fmt_n(n):
    return f"{n:,}"


def pct(x, d=1):
    return f"{float(x) * 100:.{d}f}%"


def save_figure(fig, stem):
    fig.savefig(OUT / f"{stem}.png", dpi=600, facecolor="white")
    fig.savefig(OUT / f"{stem}.pdf", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", facecolor="white")


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "pdf.fonttype": 42,
                     "svg.fonttype": "none", "axes.linewidth": 0.7, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6})

# ----------------------------------------------------------------------------- sources
SRC = {
    "headline": F7 / "F00_headline.csv",
    "flow": F7 / "F30_flow_counts_for_figure1.csv",
    "flow_mid": F7 / "F01_flow_by_day_convention.csv",
    "table1": F7 / "F31_table1_baseline_characteristics.csv",
    "s1": F7 / "F32_supp_S1_included_vs_excluded.csv",
    "death": F7 / "F12_death_and_last_contact_verification.csv",
    "perf": F7 / "F02b_selected_model_performance.csv",
    "cand": F7 / "F02_M_stage_candidates_identical_patients.csv",
    "groups": F7 / "F06_phenotypes_counts_survival_calibration.csv",
    "sep": F7 / "F08_phenotype_separation.csv",
    "rfs": F7 / "F17_RFS_sensitivity_final.csv",
    "dec": F7 / "F20_calibration_by_validation_decile.csv",
    "per": F7 / "F21_calibration_by_operation_period.csv",
    "horizon": F7 / "feasibility/G01_horizon_feasibility_validation.csv",
    "coef": P1 / "P1_model_coefficients.csv",
    "strata": P1 / "P1_baseline_survival_by_stratum.csv",
    "km": P1 / "F80_km_curve_points_by_group.csv",
    "risk": P1 / "F81_numbers_at_risk_by_group.csv",
}
for k, p in SRC.items():
    if not p.exists():
        sys.exit(f"missing source: {rel(p)}")

flow_rows = read_csv(SRC["flow"])
flow = {r[0]: as_int(r[1]) for r in flow_rows[1:]}
STEP = [("registry", "1 registry"), ("eligible", "2 CINCLUSION=Yes"), ("hepatectomy", "3 hepatectomy"),
        ("opdate", "4 operation date (year+month)"), ("status", "5 status and last-news"),
        ("chronology", "6 chronology"), ("followup", "7 positive follow-up or death"),
        ("analytic", "8 complete TNM (analytic cohort)")]
N = {k: flow[v] for k, v in STEP}
EXCL = {}
order = [k for k, _ in STEP]
for a, b in zip(order[:-1], order[1:]):
    EXCL[b] = N[a] - N[b]

t1 = read_csv(SRC["table1"])
t1h = t1[0]
C_TOT, C_DEV, C_VAL = t1h.index("Total (n=17,262)"), t1h.index("Development (<=2009; n=8,463)"), t1h.index("Validation (>=2010; n=8,799)")


def t1row(prefix):
    return [r for r in t1[1:] if r[0].startswith(prefix)][0]


N_DEV = as_int(t1row("Patients")[C_DEV])
N_VAL = as_int(t1row("Patients")[C_VAL])
EV_DEV = as_int(t1row("Deaths inside the 15-year")[C_DEV])
EV_VAL = as_int(t1row("Deaths inside the 15-year")[C_VAL])
REC_DEV = as_int(t1row("Deaths recorded")[C_DEV])
FU_DEV = as_float(t1row("Median follow-up")[C_DEV])
FU_VAL = as_float(t1row("Median follow-up")[C_VAL])

head = {r[0]: r[1] for r in read_csv(SRC["headline"])[1:]}
CUT_LO = as_float(head["phenotype_cut_S5_q33"])
CUT_HI = as_float(head["phenotype_cut_S5_q67"])

coef = read_csv(SRC["coef"])
N_TERMS = len(coef) - 1
N_STRATA = len(read_csv(SRC["strata"])) - 1

perf = dict(zip(read_csv(SRC["perf"])[0], read_csv(SRC["perf"])[1]))
C_DEV_APP = as_float(perf["train_C"])
C_VAL = as_float(perf["valid_C"])
C_CI = perf["valid_C_95CI"]
OE5 = as_float(perf["valid_OE_5y"])
OBS5 = as_float(perf["valid_observed_S5"])
PRED5 = as_float(perf["valid_mean_predicted_S5"])
IBS = as_float(perf["IBS_1_7y"])

sep = {r[0]: r[1] for r in read_csv(SRC["sep"])[1:]}
P_VAL, P_DEV, ORD_C = float(sep["valid_logrank_p"]), float(sep["train_logrank_p"]), float(sep["valid_C_ordinal"])

grp_rows = read_csv(SRC["groups"])
G = {}
for name in GROUPS:
    r = pick(grp_rows, "phenotype", name)
    G[name] = dict(dev_n=as_int(r["train_n"]), val_n=as_int(r["valid_n"]), val_deaths=as_int(r["valid_deaths"]),
                   val_med=as_float(r["valid_median_OS"]), val_med_ci=r["valid_median_95CI"],
                   val_s5=as_float(r["valid_S5_KM"]), dev_s5=as_float(r["train_S5_KM"]),
                   val_pred5=as_float(r["valid_mean_predicted_S5"]))

rfs = pick(read_csv(SRC["rfs"]), "RFS_analysis", "PRIMARY", startswith=True)
RFS_MED, RFS_CI = as_float(rfs["median_RFS"]), rfs["median_95CI"]

g1 = pick(read_csv(SRC["horizon"]), "horizon_years", "5")
EVAL5 = as_float(g1["pct_evaluable"])

dec_rows = read_csv(SRC["dec"])
dec = [dict(zip(dec_rows[0], r)) for r in dec_rows[1:]]
per_rows = read_csv(SRC["per"])
per = [dict(zip(per_rows[0], r)) for r in per_rows[1:]]

km_rows = read_csv(SRC["km"])
KM = {}
for r in km_rows[1:]:
    KM.setdefault(r[0], {}).setdefault(r[1], []).append(
        (as_float(r[2]), as_float(r[3]), as_float(r[4]), as_float(r[5])))
risk_rows = read_csv(SRC["risk"])
RISK = {}
for r in risk_rows[1:]:
    RISK.setdefault(r[0], {}).setdefault(r[1], {})[as_int(r[2])] = (as_int(r[3]), as_int(r[4]))

# ----------------------------------------------------------------------------- shared checks
src_flow = rel(SRC["flow"])
mid_col = read_csv(SRC["flow_mid"])[0].index("mid-month (15th, primary)")
for r in read_csv(SRC["flow_mid"])[1:]:
    step = r[0].strip()
    if step in flow:
        check("common", f"F01 mid-month equals F30 at '{step}'", flow[step], as_int(r[mid_col]))

s1 = read_csv(SRC["s1"])
s1p = [r for r in s1[1:] if r[0].strip() == "Patients"][0]
check("common", "Excluded n: F30 difference equals F32 'Excluded' n", EXCL["analytic"],
      as_int(s1p[s1[0].index("Excluded, incomplete TNM (n=8,832)")]))
check("common", "Analytic n: F30 equals F32 'Analytic cohort' n", N["analytic"],
      as_int(s1p[s1[0].index("Analytic cohort (TNM complete, n=17,262)")]))
check("common", "Development + validation equals analytic cohort", N["analytic"], N_DEV + N_VAL)
death = read_csv(SRC["death"])
win = [r for r in death[1:] if r[0].startswith("modelling cohort: deaths inside the 15-year window")][0]
check("common", "Window events (dev + val) equal F12", as_int(win[1]), EV_DEV + EV_VAL)
rec = [r for r in death[1:] if r[0].startswith("modelling cohort: deaths recorded")][0]
beyond = [r for r in death[1:] if r[0].startswith("modelling cohort: deaths beyond 15 years")][0]
check("common", "Recorded minus window events equal F12 deaths beyond 15 years", as_int(beyond[1]),
      REC_DEV - EV_DEV)
check("common", "Group development n sum equals development cohort", N_DEV, sum(G[g]["dev_n"] for g in GROUPS))
check("common", "Group validation n sum equals validation cohort", N_VAL, sum(G[g]["val_n"] for g in GROUPS))
check("common", "Group validation deaths sum equals validation window events", EV_VAL,
      sum(G[g]["val_deaths"] for g in GROUPS))
_cand = read_csv(SRC["cand"])
_f02_m2a = [r for r in _cand[1:] if r[0].startswith("M2a")][0]
F02_CI = _f02_m2a[_cand[0].index("valid_C_95CI")]
check("common", "Validation C-index 95% CI: F02 (candidate table, M2a row) equals F02b (selected model)",
      F02_CI, C_CI, severity="DISCREPANCY")
record("common", "C_ci_F02", "C-index 95% CI, M2a row of candidate table (Supplementary S4)", F02_CI.replace("-", "–"),
       rel(SRC["cand"]), "valid_C_95CI, row M2a", F02_CI)
check("common", "Validation 5-y observed survival: F02b equals G01", OBS5, as_float(g1["observed_KM_survival"]), tol=0.0005)
check("common", "Validation 5-y predicted survival: F02b equals G01", PRED5, as_float(g1["mean_predicted_survival"]), tol=0.0005)
check("common", "Validation 5-y O/E: F02b equals G01", OE5, as_float(g1["O_over_E"]), tol=0.0005)

record("common", "N_registry", "Registry records", fmt_n(N["registry"]), src_flow, "n, step '1 registry'", N["registry"])
record("common", "N_analytic", "Analytic cohort", fmt_n(N["analytic"]), src_flow, "n, step '8 complete TNM'", N["analytic"])
record("common", "N_dev", "Development n", fmt_n(N_DEV), rel(SRC["table1"]), "Patients / Development", N_DEV)
record("common", "N_val", "Validation n", fmt_n(N_VAL), rel(SRC["table1"]), "Patients / Validation", N_VAL)
record("common", "EV_dev", "Development events in window", fmt_n(EV_DEV), rel(SRC["table1"]),
       "Deaths inside the 15-year window / Development", EV_DEV)
record("common", "EV_val", "Validation events in window", fmt_n(EV_VAL), rel(SRC["table1"]),
       "Deaths inside the 15-year window / Validation", EV_VAL)
record("common", "CUT_lo", "Cut-point, lower tertile", f"{CUT_LO:.4f}", rel(SRC["headline"]), "phenotype_cut_S5_q33", CUT_LO)
record("common", "CUT_hi", "Cut-point, upper tertile", f"{CUT_HI:.4f}", rel(SRC["headline"]), "phenotype_cut_S5_q67", CUT_HI)
record("common", "C_val", "Validation C-index", f"{C_VAL:.3f}", rel(SRC["perf"]), "valid_C", C_VAL)
record("common", "C_ci", "Validation C-index 95% CI (F02b, selected model)", C_CI.replace("-", "–"),
       rel(SRC["perf"]), "valid_C_95CI", C_CI)
record("common", "OE5", "Observed/expected 5-y", f"{OE5:.2f}", rel(SRC["perf"]), "valid_OE_5y", OE5)
record("common", "OBS5", "Observed 5-y survival (KM)", pct(OBS5), rel(SRC["perf"]), "valid_observed_S5", OBS5)
record("common", "PRED5", "Predicted 5-y survival (mean)", pct(PRED5), rel(SRC["perf"]), "valid_mean_predicted_S5", PRED5)
record("common", "P_val", "Log-rank p, validation", sci(P_VAL), rel(SRC["sep"]), "valid_logrank_p", P_VAL)
record("common", "P_dev", "Log-rank p, development", sci(P_DEV), rel(SRC["sep"]), "train_logrank_p", P_DEV)
record("common", "RFS_med", "Median RFS, years (primary)", f"{RFS_MED:.2f}", rel(SRC["rfs"]), "median_RFS (PRIMARY row)", RFS_MED)
record("common", "EVAL5", "Validation evaluable at 5 years", f"{EVAL5:.0f}%", rel(SRC["horizon"]), "pct_evaluable, horizon 5", EVAL5)
record("common", "FU_dev", "Median follow-up, development (years)", f"{FU_DEV:.2f}", rel(SRC["table1"]), "Median follow-up / Development", FU_DEV)
record("common", "FU_val", "Median follow-up, validation (years)", f"{FU_VAL:.2f}", rel(SRC["table1"]), "Median follow-up / Validation", FU_VAL)
record("common", "N_terms", "M2a terms", f"{N_TERMS}", rel(SRC["coef"]), "number of rows", N_TERMS)
record("common", "N_strata", "M2a strata", f"{N_STRATA}", rel(SRC["strata"]), "number of rows", N_STRATA)
check("common", "M2a strata count equals 2 x 2 x 2", 8, N_STRATA)


# ============================================================================= FIGURE 1: STROBE flow
def build_figure1():
    fig_id = "Figure1"
    fig = plt.figure(figsize=(7.2, 12.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 150)
    ax.axis("off")

    def box(x, y, w, h, fc, ec, lw=0.9, radius=0.9):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                                    fc=fc, ec=ec, lw=lw, zorder=2))

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9, shrinkA=0, shrinkB=0), zorder=3)

    def line(xs, ys, color=GREY, lw=0.9, ls="-"):
        ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=1)

    ax.text(50, 148.2, "Figure 1. STROBE patient flow: selection, development and temporal validation",
            ha="center", va="center", fontsize=8.6, weight="bold", color=INK)
    MX, MW, MH = 6, 58, 6.2
    EX, EW, EH = 72, 26, 5.4
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
    pct_incomplete = 100.0 * EXCL["analytic"] / N["followup"]
    y = 141.0
    step_y = {}
    for key, title, excl_label in steps:
        last = key == "analytic"
        box(MX, y - MH, MW, MH, "#0E2A47" if last else NAVY, NAVY_EDGE)
        ax.text(MX + MW / 2, y - 2.1, title, ha="center", va="center", fontsize=7.4, weight="bold", color="white", zorder=4)
        ax.text(MX + MW / 2, y - 4.6, f"n = {fmt_n(N[key])}" + ("   (analytic cohort)" if last else ""),
                ha="center", va="center", fontsize=7.0, color="white", zorder=4)
        record(fig_id, f"N_{key}", f"Step count: {title}", fmt_n(N[key]), src_flow, f"n, step '{dict(STEP)[key]}'", N[key])
        step_y[key] = y
        if excl_label is not None:
            ex_y = y - 5.0 - EH / 2 + 2.8
            box(EX, ex_y - EH / 2 + 0.2, EW, EH, RED_FILL, RED_EDGE, lw=0.8)
            extra = f"\n{pct_incomplete:.1f}% of patients meeting criteria" if last else ""
            ax.text(EX + EW / 2, ex_y + 0.3, f"Excluded: {excl_label}\nn = {fmt_n(EXCL[key])}{extra}",
                    ha="center", va="center", fontsize=6.3, color="#6E1C15", zorder=4, linespacing=1.25)
            line([MX + MW, EX], [ex_y, ex_y], color=RED_EDGE, lw=0.7, ls=(0, (3, 2)))
            record(fig_id, f"X_{key}", f"Excluded: {excl_label}", fmt_n(EXCL[key]), src_flow,
                   f"difference of consecutive steps into '{dict(STEP)[key]}'", EXCL[key])
        if not last:
            arrow(MX + MW / 2, y - MH, MX + MW / 2, y - MH - 3.0)
        y -= 9.6
    record(fig_id, "P_incomplete", "Percent excluded for incomplete TNM", f"{pct_incomplete:.1f}%", src_flow,
           "computed: excluded / step 7", round(pct_incomplete, 3))

    analytic_bottom = step_y["analytic"] - MH
    DEV_X, DEV_W, VAL_X, VAL_W = 2, 40, 56, 42
    split_y = analytic_bottom - 3.4
    line([MX + MW / 2, MX + MW / 2], [analytic_bottom, split_y])
    line([DEV_X + DEV_W / 2, VAL_X + VAL_W / 2], [split_y, split_y])
    arrow(DEV_X + DEV_W / 2, split_y, DEV_X + DEV_W / 2, split_y - 2.6)
    arrow(VAL_X + VAL_W / 2, split_y, VAL_X + VAL_W / 2, split_y - 2.6)

    coh_y = split_y - 2.6 - 7.4
    box(DEV_X, coh_y, DEV_W, 7.4, DEV_FILL, DEV_EDGE, lw=1.1)
    ax.text(DEV_X + DEV_W / 2, coh_y + 5.4, "Development cohort", ha="center", va="center", fontsize=7.6, weight="bold", color=DEV_EDGE)
    ax.text(DEV_X + DEV_W / 2, coh_y + 3.0, "operated 2009 or earlier", ha="center", va="center", fontsize=6.6, color=INK)
    ax.text(DEV_X + DEV_W / 2, coh_y + 1.0, f"n = {fmt_n(N_DEV)}   |   events = {fmt_n(EV_DEV)}", ha="center", va="center", fontsize=7.0, weight="bold", color=INK)
    box(VAL_X, coh_y, VAL_W, 7.4, VAL_FILL, VAL_EDGE, lw=1.1)
    ax.text(VAL_X + VAL_W / 2, coh_y + 5.4, "Temporal validation cohort", ha="center", va="center", fontsize=7.6, weight="bold", color=VAL_EDGE)
    ax.text(VAL_X + VAL_W / 2, coh_y + 3.0, "operated 2010 or later", ha="center", va="center", fontsize=6.6, color=INK)
    ax.text(VAL_X + VAL_W / 2, coh_y + 1.0, f"n = {fmt_n(N_VAL)}   |   events = {fmt_n(EV_VAL)}", ha="center", va="center", fontsize=7.0, weight="bold", color=INK)

    mod_y = coh_y - 3.0 - 9.0
    arrow(DEV_X + DEV_W / 2, coh_y, DEV_X + DEV_W / 2, mod_y + 9.2)
    arrow(VAL_X + VAL_W / 2, coh_y, VAL_X + VAL_W / 2, mod_y + 9.2)
    box(DEV_X, mod_y, DEV_W, 9.0, "white", DEV_EDGE, lw=1.0)
    ax.text(DEV_X + 1.5, mod_y + 7.4, "Model development (training only)", ha="left", va="center", fontsize=7.0, weight="bold", color=DEV_EDGE)
    ax.text(DEV_X + 1.5, mod_y + 5.0, f"Stratified Cox model M2a: {N_TERMS} terms,\n{N_STRATA} strata (sex x synchrony x M-stage)",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)
    ax.text(DEV_X + 1.5, mod_y + 1.9, f"Group cut-points (training tertiles):\npredicted 5-y survival {CUT_LO:.4f} and {CUT_HI:.4f}",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)
    box(VAL_X, mod_y, VAL_W, 9.0, "white", VAL_EDGE, lw=1.0)
    ax.text(VAL_X + 1.5, mod_y + 7.4, "Validation: fixed model, no refit", ha="left", va="center", fontsize=7.0, weight="bold", color=VAL_EDGE)
    ax.text(VAL_X + 1.5, mod_y + 4.9, f"C-index {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')})\nO/E at 5 years {OE5:.2f}; IBS (1-7 y) {IBS:.3f}",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)
    ax.text(VAL_X + 1.5, mod_y + 1.6, f"5-y survival: observed {pct(OBS5)}, predicted {pct(PRED5)}\nFavourable/Intermediate/Adverse groups applied",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)

    grp_top = mod_y - 4.0
    bus_y = grp_top + 1.8
    COL_W = 30.6
    COL_X = {"Favourable": 1.5, "Intermediate": 34.7, "Adverse": 67.9}
    COL_CX = {n: COL_X[n] + COL_W / 2 for n in GROUPS}
    line([DEV_X + DEV_W / 2, DEV_X + DEV_W / 2], [mod_y, bus_y])
    line([VAL_X + VAL_W / 2, VAL_X + VAL_W / 2], [mod_y, bus_y])
    line([COL_CX["Favourable"], COL_CX["Adverse"]], [bus_y, bus_y])
    line([DEV_X + DEV_W / 2, VAL_X + VAL_W / 2], [bus_y, bus_y])
    for n in GROUPS:
        arrow(COL_CX[n], bus_y, COL_CX[n], grp_top + 0.2)
    defn = {"Favourable": f"predicted 5-y ≥ {CUT_HI:.4f}", "Intermediate": f"{CUT_LO:.4f} to < {CUT_HI:.4f}",
            "Adverse": f"predicted 5-y < {CUT_LO:.4f}"}
    GH = 31.0
    for n in GROUPS:
        x, g = COL_X[n], G[n]
        box(x, grp_top - GH, COL_W, GH, "white", GRP_COL[n], lw=1.3)
        box(x, grp_top - 4.8, COL_W, 4.8, GRP_COL[n], GRP_COL[n], lw=0.0)
        ax.text(COL_CX[n], grp_top - 2.4, f"{n} group", ha="center", va="center", fontsize=7.8, weight="bold", color="white", zorder=4)
        ax.text(COL_CX[n], grp_top - 7.2, defn[n], ha="center", va="center", fontsize=6.3, color=INK, style="italic")
        rows = [("Development n", fmt_n(g["dev_n"])), ("Development 5-y KM", pct(g["dev_s5"])),
                ("Validation n (deaths)", f"{fmt_n(g['val_n'])} ({fmt_n(g['val_deaths'])})"),
                ("Validation median OS, y", f"{g['val_med']:.2f}"), ("  95% CI", g["val_med_ci"].replace("-", "–")),
                ("Validation 5-y KM", pct(g["val_s5"]))]
        yy = grp_top - 11.0
        for lab, val in rows:
            ax.text(x + 1.4, yy, lab, ha="left", va="center", fontsize=6.2, color=GREY)
            ax.text(x + COL_W - 1.4, yy, val, ha="right", va="center", fontsize=6.6, color=INK, weight="bold")
            yy -= 2.9
        record(fig_id, f"G_{n[:3].upper()}", f"{n} group counts and outcomes",
               f"dev n {fmt_n(g['dev_n'])}; val n {fmt_n(g['val_n'])} ({fmt_n(g['val_deaths'])}); median {g['val_med']:.2f}; 5-y {pct(g['val_s5'])}",
               rel(SRC["groups"]), f"row '{n}': train_n, valid_n, valid_deaths, valid_median_OS, valid_S5_KM", n)
    ax.text(50, grp_top - GH - 1.6, "Development group n is one third of the development cohort (training tertiles). "
            "Validation outcomes use the fixed cut-points.", ha="center", va="center", fontsize=5.9, color=GREY, style="italic")

    sum_y = grp_top - GH - 4.6 - 16.0
    box(2, sum_y, 96, 15.6, NAVY, NAVY_EDGE, lw=0.9)
    ax.text(50, sum_y + 13.2, "Model performance and survival findings (temporal validation unless stated)",
            ha="center", va="center", fontsize=7.6, weight="bold", color="white")
    lines_txt = [
        f"Group separation: log-rank p = {sci(P_VAL)} in validation; p = {sci(P_DEV)} in development.  Ordinal C-index {ORD_C:.3f}.",
        f"Discrimination: C-index {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')}) in validation vs {C_DEV_APP:.3f} in development (apparent).",
        f"Calibration: predicted 5-y survival {pct(PRED5)} vs observed {pct(OBS5)} (O/E {OE5:.2f}); the model under-predicts survival.",
        f"Evaluable at 5 years: {EVAL5:.0f}% of validation patients (median follow-up: development {FU_DEV:.2f} y, validation {FU_VAL:.2f} y).",
        f"Secondary outcome: median recurrence-free survival {RFS_MED:.2f} years (95% CI {RFS_CI.replace('-', '–')}).",
    ]
    for i, t in enumerate(lines_txt):
        ax.text(5, sum_y + 10.4 - i * 2.1, "•  " + t, ha="left", va="center", fontsize=6.2, color="white")
    foot_y = sum_y - 2.2
    ax.text(2, foot_y,
            "Excluded counts are differences between consecutive steps.\n"
            "Events = deaths within the 15-year analysis window. Development recorded deaths: "
            f"{fmt_n(REC_DEV)}; {fmt_n(REC_DEV - EV_DEV)} of these fall beyond 15 years and are censored in the models.\n"
            "TNM = tumour-node-metastasis; M2a = stratified Cox model; KM = Kaplan–Meier; O/E = observed/expected;\n"
            "IBS = integrated Brier score; RFS = recurrence-free survival.\n"
            "Every number is read from the locked v8 outputs by make_paper1_figures.py; see verification_report.md.",
            ha="left", va="top", fontsize=5.4, color=GREY, linespacing=1.35)
    bottom = foot_y - 10.0
    ax.set_ylim(bottom, 150)
    fig.set_size_inches(7.2, (150 - bottom) * 0.072)
    return fig


# ============================================================================= KM helpers
def km_series(scenario, group):
    pts = KM[scenario][group]
    return ([p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], [p[3] for p in pts])


def step_value_at(scenario, group, t):
    ts, s, _, _ = km_series(scenario, group)
    val = 1.0
    for ti, si in zip(ts, s):
        if ti <= t:
            val = si
        else:
            break
    return val


def km_median(scenario, group):
    ts, s, _, _ = km_series(scenario, group)
    for ti, si in zip(ts, s):
        if si <= 0.5:
            return ti
    return None


def draw_km(scenario, xmax, risk_scenario, n_map, colour_map):
    fig = plt.figure(figsize=(6.6, 5.6))
    ax = fig.add_axes([0.11, 0.33, 0.86, 0.62])
    for g in GROUPS:
        ts, s, lo, hi = km_series(scenario, g)
        ax.fill_between(ts, lo, hi, step="post", color=colour_map[g], alpha=0.18, lw=0, zorder=1)
        ax.step(ts, s, where="post", color=colour_map[g], lw=1.6, zorder=2,
                label=f"{g} (n = {fmt_n(n_map[g])})")
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(range(0, xmax + 1, 2))
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels([f"{v:.0%}" for v in [0, 0.2, 0.4, 0.6, 0.8, 1.0]])
    ax.set_xlabel("Years from hepatectomy")
    ax.set_ylabel("Survival probability")
    ax.grid(alpha=0.22, lw=0.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7.4, loc="upper right")
    # numbers at risk
    axr = fig.add_axes([0.11, 0.08, 0.86, 0.17])
    axr.set_xlim(-0.9, xmax)
    axr.set_ylim(-0.5, len(GROUPS) - 0.5)
    axr.set_yticks(range(len(GROUPS)))
    axr.set_yticklabels(list(reversed(GROUPS)), fontsize=7.2)
    axr.set_xticks(range(0, xmax + 1, 2))
    axr.tick_params(axis="x", labelsize=7)
    axr.set_xlabel("Number at risk", fontsize=7.4)
    for sp in ["top", "right", "left"]:
        axr.spines[sp].set_visible(False)
    axr.tick_params(axis="y", length=0)
    for i, g in enumerate(reversed(GROUPS)):
        for t in range(0, xmax + 1, 2):
            axr.text(t, i, fmt_n(RISK[risk_scenario][g][t][0]) if t in RISK[risk_scenario][g] else "",
                     ha="center", va="center", fontsize=7, color=colour_map[g])
    return fig, ax


def build_figure2():
    fig_id = "Figure2"
    scen = "OS_validation"
    n_map = {g: RISK[scen][g][0][1] for g in GROUPS}
    check(fig_id, "KM group n (F81) equals F06 validation n", {g: G[g]["val_n"] for g in GROUPS},
          {g: n_map[g] for g in GROUPS})
    for g in GROUPS:
        check(fig_id, f"{g}: at-risk at t=0 equals group n", n_map[g], RISK[scen][g][0][0])
        s5 = step_value_at(scen, g, 5.0)
        check(fig_id, f"{g}: KM survival at 5 y (curve) equals F06 valid_S5_KM", G[g]["val_s5"], s5, tol=0.0015)
        med = km_median(scen, g)
        check(fig_id, f"{g}: KM median (curve) equals F06 valid_median_OS", G[g]["val_med"], med, tol=0.01)
        record(fig_id, f"KM5_{g[:3].upper()}", f"{g} 5-y KM survival (validation)", pct(G[g]["val_s5"]),
               rel(SRC["groups"]), "valid_S5_KM", G[g]["val_s5"])
        record(fig_id, f"MED_{g[:3].upper()}", f"{g} median OS (validation), years", f"{G[g]['val_med']:.2f} ({G[g]['val_med_ci'].replace('-', '–')})",
               rel(SRC["groups"]), "valid_median_OS; valid_median_95CI", G[g]["val_med"])
    fig, ax = draw_km(scen, 10, scen, n_map, GRP_COL)
    ax.text(0.98, 0.06, f"log-rank p = {sci(P_VAL)}\nC-index {C_VAL:.3f}", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7.2, color=INK)
    record(fig_id, "P_val_fig", "Log-rank p shown on figure", sci(P_VAL), rel(SRC["sep"]), "valid_logrank_p", P_VAL)
    return fig


def build_figureS1():
    fig_id = "FigureS1"
    scen = "RFS_validation"
    n_map = {g: RISK[scen][g][0][1] for g in GROUPS}
    check(fig_id, "RFS validation n (sum over groups) does not exceed validation cohort n",
          True, sum(n_map.values()) <= N_VAL)
    for g in GROUPS:
        check(fig_id, f"{g}: at-risk at t=0 equals group n", n_map[g], RISK[scen][g][0][0])
        record(fig_id, f"RFSN_{g[:3].upper()}", f"{g} RFS n (validation)", fmt_n(n_map[g]), rel(SRC["risk"]),
               f"n, scenario RFS_validation, group {g}", n_map[g])
    fig, ax = draw_km(scen, 10, scen, n_map, GRP_COL)
    ax.text(0.98, 0.06, f"Overall median RFS {RFS_MED:.2f} y (95% CI {RFS_CI.replace('-', '–')})\n(primary definition, all validation patients)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8, color=INK)
    record(fig_id, "RFS_CI_fig", "Overall median RFS shown on figure", f"{RFS_MED:.2f} ({RFS_CI.replace('-', '–')})",
           rel(SRC["rfs"]), "median_RFS; median_95CI (PRIMARY row)", RFS_MED)
    return fig


def build_figureS2():
    fig_id = "FigureS2"
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    fig.subplots_adjust(left=0.15, right=0.97, bottom=0.14, top=0.95)
    check(fig_id, "Decile sizes sum to validation n", N_VAL, sum(as_int(d["n"]) for d in dec))
    check(fig_id, "Decile deaths sum to validation window events", EV_VAL, sum(as_int(d["deaths"]) for d in dec))
    for d in dec:
        pred, obs = as_float(d["mean_predicted_5y"]), as_float(d["observed_5y_KM"])
        check(fig_id, f"decile {d['validation_decile']}: observed minus predicted equals F20",
              as_float(d["observed_minus_predicted"]), round(obs - pred, 3), tol=0.0015)
    ax.plot([0.1, 0.9], [0.1, 0.9], color="#555555", lw=0.8, ls="--", label="Perfect calibration")
    rel_ = [d for d in dec if d["reliable_5y_estimate"] == "True"]
    spa = [d for d in dec if d["reliable_5y_estimate"] != "True"]
    ax.scatter([as_float(d["mean_predicted_5y"]) for d in rel_], [as_float(d["observed_5y_KM"]) for d in rel_],
               s=26, color="#2166AC", zorder=3, label="50 or more with 5-year follow-up")
    ax.scatter([as_float(d["mean_predicted_5y"]) for d in spa], [as_float(d["observed_5y_KM"]) for d in spa],
               s=26, facecolors="white", edgecolors="#2166AC", zorder=3, label="Fewer than 50 with 5-year follow-up")
    dd = dec[-1]
    ax.annotate(f"Decile {dd['validation_decile']}\n{pct(dd['observed_5y_KM'])} observed\n{pct(dd['mean_predicted_5y'])} predicted",
                xy=(as_float(dd["mean_predicted_5y"]), as_float(dd["observed_5y_KM"])),
                xytext=(0.38, 0.86), fontsize=6.6, color=INK,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6))
    record(fig_id, "DEC10", "Decile 10 observed and predicted 5-y survival", f"{pct(dd['observed_5y_KM'])} vs {pct(dd['mean_predicted_5y'])}",
           rel(SRC["dec"]), "observed_5y_KM; mean_predicted_5y (validation_decile = 10)", dd["observed_5y_KM"])
    ax.set_xlim(0.1, 0.9)
    ax.set_ylim(0.1, 0.9)
    ax.set_xlabel("Mean predicted 5-year survival")
    ax.set_ylabel("Observed 5-year survival (Kaplan–Meier)")
    ax.grid(alpha=0.22, lw=0.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=6.6, loc="lower right")
    return fig


def build_figureS3():
    fig_id = "FigureS3"
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.25, top=0.95)
    rows = [p for p in per if p["O_over_E"]]
    check(fig_id, "Operation periods with O/E equal periods with 5-year follow-up present in F21",
          sum(as_int(p["patients_with_5y_follow_up"]) > 0 for p in per), len(rows))
    for p in rows:
        obs, pred = as_float(p["observed_5y_KM"]), as_float(p["mean_predicted_5y"])
        # tolerance = propagated rounding of the three-decimal inputs plus output rounding
        tol = (obs / pred) * (0.0005 / obs + 0.0005 / pred) + 0.0005
        check(fig_id, f"{p['period']}: O/E equals observed divided by predicted (F21), within rounding",
              as_float(p["O_over_E"]), round(obs / pred, 3), tol=tol)
    xs = range(len(rows))
    cols = ["#2166AC" if p["reliable_5y_estimate"] == "True" else "#9AA5B1" for p in rows]
    ax.bar(xs, [as_float(p["O_over_E"]) for p in rows], color=cols, width=0.62, zorder=2)
    ax.axhline(1.0, color="#333333", lw=0.8, ls="--", zorder=3)
    for i, p in enumerate(rows):
        ax.text(i, as_float(p["O_over_E"]) + 0.03, half_up(p["O_over_E"]), ha="center", fontsize=7.2, color=INK,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"), zorder=4)
        ax.text(i, 0.04, f"n(5y) = {fmt_n(as_int(p['patients_with_5y_follow_up']))}", ha="center", fontsize=5.8,
                color="white" if cols[i] != "#9AA5B1" else INK, rotation=90, va="bottom")
        record(fig_id, f"OE_{i}", f"O/E, {p['period']}", half_up(p["O_over_E"]), rel(SRC["per"]),
               "O_over_E", as_float(p["O_over_E"]))
    labels = [p["period"].replace(" (", "\n(") for p in rows]
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, fontsize=6.6)
    ax.set_ylabel("Observed / predicted 5-year survival")
    ax.set_ylim(0, 1.45)
    ax.grid(alpha=0.22, lw=0.5, axis="y", zorder=0)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    return fig


# ============================================================================= gate, draw, write
def write_captions():
    cap = {}
    cap["Figure1"] = (
        f"**Figure 1.** STROBE patient flow for the development and temporal validation of the prognostic model. "
        f"Of {fmt_n(N['registry'])} registry records, {fmt_n(N['eligible'])} were recorded as eligible and "
        f"{fmt_n(N['analytic'])} patients met all criteria with complete TNM staging; {fmt_n(EXCL['analytic'])} "
        f"({pct_incomplete_text()} of the {fmt_n(N['followup'])} patients meeting criteria) were excluded for incomplete staging. "
        f"Patients operated in 2009 or earlier formed the development cohort (n = {fmt_n(N_DEV)}; {fmt_n(EV_DEV)} events within 15 years) "
        f"and those operated in 2010 or later the temporal validation cohort (n = {fmt_n(N_VAL)}; {fmt_n(EV_VAL)} events). "
        f"The stratified Cox model (M2a; {N_TERMS} terms; {N_STRATA} strata) was fitted in development only and applied unchanged to validation. "
        f"Prognostic groups were defined by training-era tertiles of predicted 5-year survival (cut-points {CUT_LO:.4f} and {CUT_HI:.4f}).")
    cap["Figure2"] = (
        f"**Figure 2.** Overall survival by prognostic group in the temporal validation cohort (operated 2010 or later; n = {fmt_n(N_VAL)}). "
        f"Kaplan–Meier curves with 95% confidence bands (shaded). Groups were defined by training-only cut-points "
        f"({CUT_LO:.4f} and {CUT_HI:.4f}). Numbers at risk are shown below the axis. "
        f"Log-rank p = {sci(P_VAL)}. Median follow-up in validation was {FU_VAL:.2f} years, so few patients were followed beyond 5 years.")
    cap["FigureS1"] = (
        "**Figure S1.** Recurrence-free survival by prognostic group in the temporal validation cohort (primary definition: "
        "dated recurrence or death as events; undated recurrences censored). Kaplan–Meier curves with 95% confidence bands; "
        "numbers at risk below the axis. Overall median RFS "
        f"{RFS_MED:.2f} years (95% CI {RFS_CI.replace('-', '–')}).")
    cap["FigureS2"] = (
        "**Figure S2.** Calibration by validation decile of predicted 5-year survival (validation cohort, n = "
        f"{fmt_n(N_VAL)}). Each point is one decile; the dashed line is perfect calibration. Open markers mark deciles with fewer "
        "than 50 patients followed up to 5 years, whose observed values are imprecise.")
    cap["FigureS3"] = (
        "**Figure S3.** Observed/predicted 5-year survival by operation period. Bars above 1.0 indicate survival under-predicted "
        "by the model. Grey bars: fewer than 50 patients with 5-year follow-up. The 2016 onward period is omitted because no "
        "patient operated in that period had 5-year follow-up.")
    for k, v in cap.items():
        (OUT / f"{k}_caption.md").write_text(v + "\n", encoding="utf-8")
    return cap


def pct_incomplete_text():
    return f"{100.0 * EXCL['analytic'] / N['followup']:.1f}%"


def write_report():
    with open(OUT / "verification_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section", "figure", "id", "label", "displayed", "source_file", "source_field", "raw"])
        for r in RECORDS:
            w.writerow(["value", r["figure"], r["id"], r["label"], r["displayed"], r["source"], r["field"], r["raw"]])
        for c in CHECKS:
            w.writerow(["check", c["figure"], c["check"], "", c["status"], "", f"expected={c['expected']}", f"observed={c['observed']}"])
    n_fail = sum(c["status"] == "FAIL" for c in CHECKS)
    n_disc = sum(c["status"] == "DISCREPANCY" for c in CHECKS)
    n_pass = sum(c["status"] == "PASS" for c in CHECKS)
    L = ["# Paper 1 figure set: verification report (v10)", "",
         f"Automated checks: {len(CHECKS)} run; {n_pass} passed; {n_disc} discrepancy(ies) reported; {n_fail} failed.", ""]
    L += ["## Discrepancies between locked outputs (reported, not corrected)", ""]
    disc = [c for c in CHECKS if c["status"] == "DISCREPANCY"]
    L += [f"- [{c['figure']}] {c['check']}: expected {c['expected']}, observed {c['observed']}" for c in disc] or ["None."]
    L += ["", "## Failed checks (figure not drawn)", ""]
    fails = [c for c in CHECKS if c["status"] == "FAIL"]
    L += [f"- [{c['figure']}] {c['check']}: expected {c['expected']}, observed {c['observed']}" for c in fails] or ["None."]
    L += ["", "## Every displayed value and its source", "", "| Figure | ID | Label | Displayed | Source file | Field | Raw |", "|---|---|---|---|---|---|---|"]
    for r in RECORDS:
        L.append(f"| {r['figure']} | {r['id']} | {r['label']} | {r['displayed']} | `{r['source']}` | {r['field']} | {r['raw']} |")
    L += ["", "## All automated checks", "", "| Figure | Check | Expected | Observed | Status |", "|---|---|---|---|---|"]
    for c in CHECKS:
        L.append(f"| {c['figure']} | {c['check']} | {c['expected']} | {c['observed']} | **{c['status']}** |")
    (OUT / "verification_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return n_fail, n_disc, n_pass


def main():
    builders = {"Figure1": (build_figure1, "Figure1_STROBE"), "Figure2": (build_figure2, "Figure2_OS_by_group_validation"),
                "FigureS1": (build_figureS1, "FigureS1_RFS_by_group_validation"),
                "FigureS2": (build_figureS2, "FigureS2_calibration_by_decile"),
                "FigureS3": (build_figureS3, "FigureS3_OE_by_period")}
    figs = {}
    for key, (fn, stem) in builders.items():
        fig = fn()
        figs[key] = (fig, stem)
    n_fail, n_disc, n_pass = write_report()
    write_captions()
    written = []
    for key, (fig, stem) in figs.items():
        if key in FAILED_FIGS:
            plt.close(fig)
            print(f"NOT WRITTEN (failed checks): {key}")
            continue
        save_figure(fig, stem)
        plt.close(fig)
        written.append(stem)
    print(f"checks: {n_pass} passed, {n_disc} discrepancy(ies), {n_fail} failed")
    print("written:", ", ".join(written))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
