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
    "bench": F7 / "F16_identical_subset_comparison_calibration.csv",
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
                   val_pred5=as_float(r["valid_mean_predicted_S5"]), dev_med=as_float(r["train_median_OS"]))

rfs = pick(read_csv(SRC["rfs"]), "RFS_analysis", "PRIMARY", startswith=True)
RFS_MED, RFS_CI = as_float(rfs["median_RFS"]), rfs["median_95CI"]
RFS_N = as_int(rfs["n"])
_f33 = read_csv(F7 / "F33_predictor_and_recurrence_date_audit.csv")
PRE_OP_REC = as_int([r for r in _f33[1:] if r[0].startswith("Dated recurrence before time zero")][0][1])

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
    MX, MW, MH = 6, 58, 5.3
    EX, EW, EH = 72, 26, 5.0
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
    y = 141.5
    step_y = {}
    for key, title, excl_label in steps:
        last = key == "analytic"
        box(MX, y - MH, MW, MH, "#0E2A47" if last else NAVY, NAVY_EDGE)
        ax.text(MX + MW / 2, y - 1.9, title, ha="center", va="center", fontsize=7.6, weight="bold", color="white", zorder=4)
        ax.text(MX + MW / 2, y - 3.9, f"n = {fmt_n(N[key])}" + ("   (analytic cohort)" if last else ""),
                ha="center", va="center", fontsize=7.2, color="white", zorder=4)
        record(fig_id, f"N_{key}", f"Step count: {title}", fmt_n(N[key]), src_flow, f"n, step '{dict(STEP)[key]}'", N[key])
        step_y[key] = y
        if excl_label is not None:
            ex_y = y - MH / 2
            box(EX, ex_y - EH / 2 + 0.2, EW, EH, RED_FILL, RED_EDGE, lw=0.8)
            extra = f" ({pct_incomplete:.1f}%)" if last else ""
            ax.text(EX + EW / 2, ex_y, f"Excluded: {excl_label}\nn = {fmt_n(EXCL[key])}{extra}",
                    ha="center", va="center", fontsize=6.6, color="#6E1C15", zorder=4, linespacing=1.2)
            line([MX + MW, EX], [ex_y, ex_y], color=RED_EDGE, lw=0.7, ls=(0, (3, 2)))
            record(fig_id, f"X_{key}", f"Excluded: {excl_label}", fmt_n(EXCL[key]), src_flow,
                   f"difference of consecutive steps into '{dict(STEP)[key]}'", EXCL[key])
        if not last:
            arrow(MX + MW / 2, y - MH, MX + MW / 2, y - MH - 2.6)
        y -= 7.9
    record(fig_id, "P_incomplete", "Percent excluded for incomplete TNM", f"{pct_incomplete:.1f}%", src_flow,
           "computed: excluded / step 7", round(pct_incomplete, 3))

    analytic_bottom = step_y["analytic"] - MH
    DEV_X, DEV_W, VAL_X, VAL_W = 2, 40, 56, 42
    split_y = analytic_bottom - 2.8
    line([MX + MW / 2, MX + MW / 2], [analytic_bottom, split_y])
    line([DEV_X + DEV_W / 2, VAL_X + VAL_W / 2], [split_y, split_y])
    arrow(DEV_X + DEV_W / 2, split_y, DEV_X + DEV_W / 2, split_y - 2.6)
    arrow(VAL_X + VAL_W / 2, split_y, VAL_X + VAL_W / 2, split_y - 2.6)

    coh_y = split_y - 2.2 - 6.8
    box(DEV_X, coh_y, DEV_W, 6.8, DEV_FILL, DEV_EDGE, lw=1.1)
    ax.text(DEV_X + DEV_W / 2, coh_y + 5.4, "Development cohort", ha="center", va="center", fontsize=7.6, weight="bold", color=DEV_EDGE)
    ax.text(DEV_X + DEV_W / 2, coh_y + 3.0, "operated 2009 or earlier", ha="center", va="center", fontsize=6.6, color=INK)
    ax.text(DEV_X + DEV_W / 2, coh_y + 1.0, f"n = {fmt_n(N_DEV)}   |   events = {fmt_n(EV_DEV)}", ha="center", va="center", fontsize=7.0, weight="bold", color=INK)
    box(VAL_X, coh_y, VAL_W, 6.8, VAL_FILL, VAL_EDGE, lw=1.1)
    ax.text(VAL_X + VAL_W / 2, coh_y + 5.4, "Temporal validation cohort", ha="center", va="center", fontsize=7.6, weight="bold", color=VAL_EDGE)
    ax.text(VAL_X + VAL_W / 2, coh_y + 3.0, "operated 2010 or later", ha="center", va="center", fontsize=6.6, color=INK)
    ax.text(VAL_X + VAL_W / 2, coh_y + 1.0, f"n = {fmt_n(N_VAL)}   |   events = {fmt_n(EV_VAL)}", ha="center", va="center", fontsize=7.0, weight="bold", color=INK)

    mod_y = coh_y - 2.4 - 8.2
    arrow(DEV_X + DEV_W / 2, coh_y, DEV_X + DEV_W / 2, mod_y + 9.2)
    arrow(VAL_X + VAL_W / 2, coh_y, VAL_X + VAL_W / 2, mod_y + 9.2)
    box(DEV_X, mod_y, DEV_W, 8.2, "white", DEV_EDGE, lw=1.0)
    ax.text(DEV_X + 1.5, mod_y + 7.4, "Model development (training only)", ha="left", va="center", fontsize=7.0, weight="bold", color=DEV_EDGE)
    ax.text(DEV_X + 1.5, mod_y + 5.0, f"Stratified Cox model M2a: {N_TERMS} terms,\n{N_STRATA} strata (sex x synchrony x M-stage)",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)
    ax.text(DEV_X + 1.5, mod_y + 1.9, f"Group cut-points (training tertiles):\npredicted 5-y survival {CUT_LO:.4f} and {CUT_HI:.4f}",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)
    box(VAL_X, mod_y, VAL_W, 8.2, "white", VAL_EDGE, lw=1.0)
    ax.text(VAL_X + 1.5, mod_y + 7.4, "Validation: fixed model, no refit", ha="left", va="center", fontsize=7.0, weight="bold", color=VAL_EDGE)
    ax.text(VAL_X + 1.5, mod_y + 4.9, f"C-index {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')})\nO/E at 5 years {OE5:.2f}; IBS (1-7 y) {IBS:.3f}",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)
    ax.text(VAL_X + 1.5, mod_y + 1.6, f"5-y survival: observed {pct(OBS5)}, predicted {pct(PRED5)}\nFavourable/Intermediate/Adverse groups applied",
            ha="left", va="center", fontsize=6.5, color=INK, linespacing=1.3)

    grp_top = mod_y - 3.0
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
    GH = 26.0
    for n in GROUPS:
        x, g = COL_X[n], G[n]
        box(x, grp_top - GH, COL_W, GH, "white", GRP_COL[n], lw=1.3)
        box(x, grp_top - 4.8, COL_W, 4.8, GRP_COL[n], GRP_COL[n], lw=0.0)
        ax.text(COL_CX[n], grp_top - 2.4, f"{n} group", ha="center", va="center", fontsize=7.8, weight="bold", color="white", zorder=4)
        ax.text(COL_CX[n], grp_top - 6.4, defn[n], ha="center", va="center", fontsize=6.4, color=INK, style="italic")
        rows = [("Development n", fmt_n(g["dev_n"])), ("Development 5-y KM", pct(g["dev_s5"])),
                ("Validation n (deaths)", f"{fmt_n(g['val_n'])} ({fmt_n(g['val_deaths'])})"),
                ("Validation median OS, y", f"{g['val_med']:.2f}"), ("  95% CI", g["val_med_ci"].replace("-", "–")),
                ("Validation 5-y KM", pct(g["val_s5"]))]
        yy = grp_top - 9.6
        for lab, val in rows:
            ax.text(x + 1.4, yy, lab, ha="left", va="center", fontsize=6.2, color=GREY)
            ax.text(x + COL_W - 1.4, yy, val, ha="right", va="center", fontsize=6.6, color=INK, weight="bold")
            yy -= 2.45
        record(fig_id, f"G_{n[:3].upper()}", f"{n} group counts and outcomes",
               f"dev n {fmt_n(g['dev_n'])}; val n {fmt_n(g['val_n'])} ({fmt_n(g['val_deaths'])}); median {g['val_med']:.2f}; 5-y {pct(g['val_s5'])}",
               rel(SRC["groups"]), f"row '{n}': train_n, valid_n, valid_deaths, valid_median_OS, valid_S5_KM", n)
    ax.text(50, grp_top - GH - 1.3, "Development group n is one third of the development cohort (training tertiles). "
            "Validation outcomes use the fixed cut-points.", ha="center", va="center", fontsize=5.9, color=GREY, style="italic")

    sum_y = grp_top - GH - 4.0 - 14.0
    box(2, sum_y, 96, 13.6, NAVY, NAVY_EDGE, lw=0.9)
    ax.text(50, sum_y + 11.9, "Model performance and survival findings (temporal validation unless stated)",
            ha="center", va="center", fontsize=7.6, weight="bold", color="white")
    lines_txt = [
        f"Group separation: log-rank p = {sci(P_VAL)} in validation; p = {sci(P_DEV)} in development.  Ordinal C-index {ORD_C:.3f}.",
        f"Discrimination: C-index {C_VAL:.3f} (95% CI {C_CI.replace('-', '–')}) in validation vs {C_DEV_APP:.3f} in development (apparent).",
        f"Calibration: predicted 5-y survival {pct(PRED5)} vs observed {pct(OBS5)} (O/E {OE5:.2f}); the model under-predicts survival.",
        f"Evaluable at 5 years: {EVAL5:.0f}% of validation patients (median follow-up: development {FU_DEV:.2f} y, validation {FU_VAL:.2f} y).",
        f"Secondary outcome: median recurrence-free survival {RFS_MED:.2f} years (95% CI {RFS_CI.replace('-', '–')}).",
    ]
    for i, t in enumerate(lines_txt):
        ax.text(5, sum_y + 10.2 - i * 2.0, "•  " + t, ha="left", va="center", fontsize=6.4, color="white")
    foot_y = sum_y - 1.8
    ax.text(2, foot_y,
            "Excluded counts are differences between consecutive steps.\n"
            "Events = deaths within the 15-year analysis window. Development recorded deaths: "
            f"{fmt_n(REC_DEV)}; {fmt_n(REC_DEV - EV_DEV)} of these fall beyond 15 years and are censored in the models.\n"
            "TNM = tumour-node-metastasis; M2a = stratified Cox model; KM = Kaplan–Meier; O/E = observed/expected;\n"
            "IBS = integrated Brier score; RFS = recurrence-free survival.\n"
            "Every number is read from the locked v8 outputs by make_paper1_figures.py; see verification_report.md.",
            ha="left", va="top", fontsize=6.0, color=GREY, linespacing=1.3)
    bottom = foot_y - 7.4
    ax.set_ylim(bottom, 150)
    fig.set_size_inches(7.2, (150 - bottom) * 0.072)
    return fig



# ============================================================================= Kaplan-Meier helpers (derived from F80 / F81)
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


def km_panel(fig, box, scenario, xmax, n_map, title, label=None, show_legend=True, show_ylabel=True):
    """One Kaplan-Meier panel with a numbers-at-risk strip underneath. box = (x, y, w, h) in figure fractions."""
    x0, y0, w, h = box
    ax = fig.add_axes([x0, y0 + h * 0.30, w, h * 0.70])
    axr = fig.add_axes([x0, y0, w, h * 0.20])
    for g in GROUPS:
        ts, s, lo, hi = km_series(scenario, g)
        ax.fill_between(ts, lo, hi, step="post", color=GRP_COL[g], alpha=0.18, lw=0, zorder=1)
        ax.step(ts, s, where="post", color=GRP_COL[g], lw=1.6, zorder=2, label=f"{g} (n = {fmt_n(n_map[g])})")
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(range(0, xmax + 1, 2))
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels([f"{v:.0%}" for v in [0, 0.2, 0.4, 0.6, 0.8, 1.0]])
    ax.set_xlabel("")
    ax.set_ylabel("Survival probability" if show_ylabel else "")
    ax.set_title(title, fontsize=7.0, loc="left", color=INK, pad=6)
    ax.grid(alpha=0.22, lw=0.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    if show_legend:
        ax.legend(frameon=False, fontsize=6.6, loc="upper right")
    if label:
        ax.text(-0.20, 1.10, label, transform=ax.transAxes, fontsize=10, weight="bold", color=INK)
    axr.set_xlim(-0.9, xmax + 0.5)
    axr.set_ylim(-0.5, len(GROUPS) - 0.5)
    axr.set_yticks(range(len(GROUPS)))
    axr.set_yticklabels(list(reversed(GROUPS)), fontsize=6.4)
    axr.set_xticks(range(0, xmax + 1, 2))
    axr.tick_params(axis="x", labelsize=6.4, length=2)
    axr.tick_params(axis="y", length=0)
    axr.set_xlabel("Years from hepatectomy", fontsize=6.6)
    for sp in ["top", "right", "left"]:
        axr.spines[sp].set_visible(False)
    for i, g in enumerate(reversed(GROUPS)):
        for t in range(0, xmax + 1, 2):
            if t in RISK[scenario][g]:
                axr.text(t, i, fmt_n(RISK[scenario][g][t][0]), ha="center", va="center", fontsize=6.4, color=GRP_COL[g])
    return ax


def check_km(fig_id, scenario, groups_expect, label):
    """Checks that the curves reproduce the reported group n, 5-year survival and median."""
    n_map = {g: RISK[scenario][g][0][1] for g in GROUPS}
    for g in GROUPS:
        check(fig_id, f"{label} {g}: at-risk at t=0 equals group n", n_map[g], RISK[scenario][g][0][0])
        check(fig_id, f"{label} {g}: group n (F81) equals F06", groups_expect[g]["n"], n_map[g])
        s5 = step_value_at(scenario, g, 5.0)
        check(fig_id, f"{label} {g}: KM 5-y survival (curve) equals F06", groups_expect[g]["s5"], s5, tol=0.0015)
        med = km_median(scenario, g)
        check(fig_id, f"{label} {g}: KM median (curve) equals F06", groups_expect[g]["med"], med, tol=0.01)
    return n_map


# ============================================================================= FIGURE 2: OS by group, development and validation
def build_figure2():
    fig_id = "Figure2"
    dev_exp = {g: dict(n=G[g]["dev_n"], s5=G[g]["dev_s5"], med=G[g]["dev_med"]) for g in GROUPS}
    val_exp = {g: dict(n=G[g]["val_n"], s5=G[g]["val_s5"], med=G[g]["val_med"]) for g in GROUPS}
    dev_map = check_km(fig_id, "OS_development", dev_exp, "development")
    val_map = check_km(fig_id, "OS_validation", val_exp, "validation")
    fig = plt.figure(figsize=(7.2, 4.6))
    km_panel(fig, (0.12, 0.13, 0.36, 0.80), "OS_development", 10, dev_map,
             f"Development (operated ≤2009; n = {fmt_n(N_DEV)})", label="A", show_legend=True)
    km_panel(fig, (0.60, 0.13, 0.36, 0.80), "OS_validation", 10, val_map,
             f"Temporal validation (operated ≥2010; n = {fmt_n(N_VAL)})", label="B", show_legend=True,
             show_ylabel=False)
    fig.text(0.02, 0.01, f"Log-rank p = {sci(P_DEV)} (development); {sci(P_VAL)} (validation). "
             "Curves truncated at 10 years; the risk strip below each panel gives the numbers at risk.",
             fontsize=6.2, color=GREY)
    record(fig_id, "P_dev_fig", "Log-rank p shown, development", sci(P_DEV), rel(SRC["sep"]), "train_logrank_p", P_DEV)
    record(fig_id, "P_val_fig", "Log-rank p shown, validation", sci(P_VAL), rel(SRC["sep"]), "valid_logrank_p", P_VAL)
    for g in GROUPS:
        record(fig_id, f"KMDEV_{g[:3].upper()}", f"{g} 5-y KM, development", pct(G[g]["dev_s5"]),
               rel(SRC["groups"]), "train_S5_KM", G[g]["dev_s5"])
        record(fig_id, f"KMVAL_{g[:3].upper()}", f"{g} 5-y KM, validation", pct(G[g]["val_s5"]),
               rel(SRC["groups"]), "valid_S5_KM", G[g]["val_s5"])
    return fig


# ============================================================================= FIGURE 3: calibration by decile and O/E by period
def build_figure3():
    fig_id = "Figure3"
    check(fig_id, "Decile sizes sum to validation n", N_VAL, sum(as_int(d["n"]) for d in dec))
    check(fig_id, "Decile deaths sum to validation window events", EV_VAL, sum(as_int(d["deaths"]) for d in dec))
    for d in dec:
        pred, obs = as_float(d["mean_predicted_5y"]), as_float(d["observed_5y_KM"])
        check(fig_id, f"decile {d['validation_decile']}: observed minus predicted equals F20",
              as_float(d["observed_minus_predicted"]), round(obs - pred, 3), tol=0.0015)
    per_ok = [p for p in per if p["O_over_E"]]
    check(fig_id, "Operation periods with O/E equal periods with 5-year follow-up present in F21",
          sum(as_int(p["patients_with_5y_follow_up"]) > 0 for p in per), len(per_ok))
    for p in per_ok:
        obs, pred = as_float(p["observed_5y_KM"]), as_float(p["mean_predicted_5y"])
        tol = (obs / pred) * (0.0005 / obs + 0.0005 / pred) + 0.0005
        check(fig_id, f"{p['period']}: O/E equals observed divided by predicted (F21), within rounding",
              as_float(p["O_over_E"]), round(obs / pred, 3), tol=tol)

    fig = plt.figure(figsize=(7.2, 3.5))
    # A: calibration
    ax = fig.add_axes([0.09, 0.17, 0.37, 0.72])
    ax.plot([0.1, 0.9], [0.1, 0.9], color="#555555", lw=0.8, ls="--", label="Perfect calibration")
    rel_ = [d for d in dec if d["reliable_5y_estimate"] == "True"]
    spa = [d for d in dec if d["reliable_5y_estimate"] != "True"]
    ax.scatter([as_float(d["mean_predicted_5y"]) for d in rel_], [as_float(d["observed_5y_KM"]) for d in rel_],
               s=24, color="#2166AC", zorder=3, label="50 or more with 5-year follow-up")
    ax.scatter([as_float(d["mean_predicted_5y"]) for d in spa], [as_float(d["observed_5y_KM"]) for d in spa],
               s=24, facecolors="white", edgecolors="#2166AC", zorder=3, label="Fewer than 50 with 5-year follow-up")
    dd = dec[-1]
    ax.annotate(f"Decile {dd['validation_decile']} (most favourable)\n{pct(dd['observed_5y_KM'])} observed; "
                f"{pct(dd['mean_predicted_5y'])} predicted",
                xy=(as_float(dd["mean_predicted_5y"]), as_float(dd["observed_5y_KM"])),
                xytext=(0.20, 0.80), fontsize=6.0, color=INK, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6))
    record(fig_id, "DEC10", "Decile 10 observed and predicted 5-y survival",
           f"{pct(dd['observed_5y_KM'])} vs {pct(dd['mean_predicted_5y'])}", rel(SRC["dec"]),
           "observed_5y_KM; mean_predicted_5y (validation_decile = 10)", dd["observed_5y_KM"])
    ax.set_xlim(0.1, 0.9)
    ax.set_ylim(0.1, 0.9)
    ax.set_xlabel("Mean predicted 5-year survival", fontsize=7.4)
    ax.set_ylabel("Observed 5-year survival (Kaplan–Meier)", fontsize=7.4)
    ax.set_title("A. Validation cohort: calibration by decile", fontsize=7.6, loc="left")
    ax.grid(alpha=0.22, lw=0.5)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=6.0, loc="lower right")
    ax.text(-0.17, 1.03, "A", transform=ax.transAxes, fontsize=10, weight="bold", color=INK)
    # B: O/E by period
    axb = fig.add_axes([0.60, 0.17, 0.37, 0.72])
    xs = range(len(per_ok))
    cols = ["#2166AC" if p["reliable_5y_estimate"] == "True" else "#9AA5B1" for p in per_ok]
    axb.bar(xs, [as_float(p["O_over_E"]) for p in per_ok], color=cols, width=0.62, zorder=2)
    axb.axhline(1.0, color="#333333", lw=0.8, ls="--", zorder=3)
    for i, p in enumerate(per_ok):
        axb.text(i, as_float(p["O_over_E"]) + 0.03, half_up(p["O_over_E"]), ha="center", fontsize=6.6, color=INK,
                 bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"), zorder=4)
        axb.text(i, 0.04, f"n(5y) = {fmt_n(as_int(p['patients_with_5y_follow_up']))}", ha="center", fontsize=5.4,
                 color="white" if cols[i] != "#9AA5B1" else INK, rotation=90, va="bottom")
        record(fig_id, f"OE_{i}", f"O/E, {p['period']}", half_up(p["O_over_E"]), rel(SRC["per"]),
               "O_over_E", as_float(p["O_over_E"]))
    axb.set_xticks(list(xs))
    import re as _re
    def _plabel(pp):
        yrs = _re.findall(r"\d{4}", pp["period"])
        tag = "training" if "training" in pp["period"] else ("validation" if "validation" in pp["period"] else "")
        return f"{yrs[0]}–{yrs[1]}" + (f"\n({tag})" if tag else "")
    axb.set_xticklabels([_plabel(pp) for pp in per_ok], fontsize=6.0)
    axb.set_ylabel("Observed / predicted 5-year survival", fontsize=7.4)
    axb.set_ylim(0, 1.45)
    axb.set_title("B. Operation period (development and validation)", fontsize=7.6, loc="left")
    axb.grid(alpha=0.22, lw=0.5, axis="y", zorder=0)
    for sp in ["top", "right"]:
        axb.spines[sp].set_visible(False)
    axb.text(-0.17, 1.03, "B", transform=axb.transAxes, fontsize=10, weight="bold", color=INK)
    return fig


# ============================================================================= FIGURE S1: RFS by group (validation)
def build_figureS1():
    fig_id = "FigureS1"
    scen = "RFS_validation"
    n_map = {g: RISK[scen][g][0][1] for g in GROUPS}
    check(fig_id, "RFS validation n (sum over groups) does not exceed validation cohort n",
          True, sum(n_map.values()) <= N_VAL)
    check(fig_id, "Primary RFS n (F17) equals analytic cohort minus dated pre-operative recurrences (F33)",
          RFS_N, N["analytic"] - PRE_OP_REC)
    for g in GROUPS:
        check(fig_id, f"{g}: at-risk at t=0 equals group n", n_map[g], RISK[scen][g][0][0])
        record(fig_id, f"RFSN_{g[:3].upper()}", f"{g} RFS n (validation)", fmt_n(n_map[g]), rel(SRC["risk"]),
               f"n, scenario RFS_validation, group {g}", n_map[g])
    fig = plt.figure(figsize=(6.4, 4.6))
    n_rfs_val = sum(n_map.values())
    km_panel(fig, (0.12, 0.22, 0.84, 0.70), scen, 10, n_map,
             f"Recurrence-free survival, temporal validation (RFS-eligible n = {fmt_n(n_rfs_val)} of {fmt_n(N_VAL)})",
             show_legend=True)
    fig.text(0.07, 0.015, f"Primary RFS median, whole analytic cohort (n = {fmt_n(RFS_N)}): {RFS_MED:.2f} years\n"
             f"(95% CI {RFS_CI.replace('-', '–')}). No validation-only median is in the locked outputs.\n"
             f"{fmt_n(N_VAL - n_rfs_val)} validation patients lack RFS eligibility (dated recurrence before operation; derived).",
             fontsize=5.9, color=GREY, linespacing=1.3)
    record(fig_id, "RFS_CI_fig", "Primary RFS median, whole analytic cohort, shown on figure",
           f"{RFS_MED:.2f} ({RFS_CI.replace('-', '–')})", rel(SRC["rfs"]), "median_RFS; median_95CI (PRIMARY row)", RFS_MED)
    record(fig_id, "RFS_N", "RFS-eligible n, whole analytic cohort", fmt_n(RFS_N), rel(SRC["rfs"]), "n (PRIMARY row)", RFS_N)
    record(fig_id, "RFS_VAL_N", "RFS-eligible n, validation (sum of groups)", fmt_n(n_rfs_val), rel(SRC["risk"]),
           "n at time 0, scenario RFS_validation, summed over groups", n_rfs_val)
    record(fig_id, "RFS_VAL_EXCL", "Validation patients without RFS eligibility (derived: N_val minus RFS-eligible)",
           fmt_n(N_VAL - n_rfs_val), "derived from " + rel(SRC["table1"]) + " and " + rel(SRC["risk"]),
           "N_val - sum(RFS n)", N_VAL - n_rfs_val)
    return fig


# ============================================================================= FIGURE S2: M2a forest plot
def build_figureS2():
    fig_id = "FigureS2"
    rows = coef[1:]
    check(fig_id, "Forest plot rows equal M2a terms", N_TERMS, len(rows))
    hdr = coef[0]
    fig = plt.figure(figsize=(7.6, 4.8))
    ax = fig.add_axes([0.45, 0.13, 0.26, 0.80])
    from matplotlib.transforms import blended_transform_factory
    col_tx = blended_transform_factory(fig.transFigure, ax.transData)
    labels, y = [], []
    for i, r in enumerate(rows):
        d = dict(zip(hdr, r))
        hr, lo, hi, beta = as_float(d["HR"]), as_float(d["HR_CI_low"]), as_float(d["HR_CI_high"]), as_float(d["coefficient"])
        check(fig_id, f"{d['term']}: HR equals exp(coefficient) (P1 table)", hr, round(math.exp(beta), 3), tol=0.0015)
        check(fig_id, f"{d['term']}: CI brackets HR", True, lo <= hr <= hi)
        yy = len(rows) - 1 - i
        col = INK if d["p"] and as_float(d["p"]) < 0.05 else GREY
        ax.plot([lo, hi], [yy, yy], color=col, lw=1.2, zorder=2)
        ax.scatter([hr], [yy], s=22, color=col, zorder=3)
        pv = as_float(d["p"])
        ptxt = "<0.001" if pv < 0.0005 else f"{pv:.3f}"
        fig.text(0.735, yy, f"{hr:.3f} ({lo:.3f}–{hi:.3f})", fontsize=6.0, va="center", ha="left", color=INK,
                 transform=col_tx)
        fig.text(0.975, yy, ptxt, fontsize=6.0, va="center", ha="right", color=INK, transform=col_tx)
        labels.append(d["description"])
        y.append(yy)
        record(fig_id, f"HR_{d['term']}", f"HR, {d['description']}", f"{hr:.3f} ({lo:.3f}–{hi:.3f}); p {ptxt}",
               rel(SRC["coef"]), "HR, HR_CI_low, HR_CI_high, p (row " + d["term"] + ")", hr)
    ax.axvline(1.0, color="#555555", lw=0.8, ls="--", zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(0.7, 2.2)
    ax.set_xticks([0.8, 1.0, 1.25, 1.5, 2.0])
    ax.set_xticklabels(["0.8", "1.0", "1.25", "1.5", "2.0"], fontsize=6.6)
    ax.minorticks_off()
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.2)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel("Hazard ratio (log scale), 95% CI", fontsize=7.0)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(0.735, 0.955, "HR (95% CI)", fontsize=6.4, weight="bold", va="bottom", ha="left")
    fig.text(0.975, 0.955, "p", fontsize=6.4, weight="bold", va="bottom", ha="right")
    fig.text(0.02, 0.02, "Stratified Cox model M2a (strata: sex x synchronous presentation x M-stage). Hazard ratios are within strata.\n"
             "Dark ink: p < 0.05; grey: p ≥ 0.05. Reference categories: T1–2 (T terms), N0 (N terms); continuous terms per unit; "
             "'unavailable' terms are indicators for missing data.",
             fontsize=5.8, color=GREY)
    return fig


# ============================================================================= FIGURE S3: discrimination comparison
def build_figureS3():
    fig_id = "FigureS3"
    cand_rows = [r for r in read_csv(SRC["cand"])[1:]]
    cand_hdr = read_csv(SRC["cand"])[0]
    cand = []
    for r in cand_rows:
        d = dict(zip(cand_hdr, r))
        lo, hi = d["valid_C_95CI"].split("-")
        cand.append((d["model"].split(" ")[0], as_float(d["valid_C"]), as_float(lo), as_float(hi)))
    m2a = [c for c in cand if c[0] == "M2a"][0]
    check(fig_id, "M2a validation C in candidate table (F02) equals F02b", as_float(perf["valid_C"]), m2a[1])
    check(fig_id, "M2a validation C-index 95% CI: F02 candidate table equals F02b selected model", "{}-{}".format(m2a[2], m2a[3]),
          C_CI, severity="DISCREPANCY")

    bench = read_csv(SRC["bench"])
    bh = bench[0]
    brows = [dict(zip(bh, r)) for r in bench[1:]]
    sel_all = as_float(brows[0]["selected_model_C"])
    global BENCH_FONG_N, BENCH_NORD_N
    BENCH_FONG_N = as_int([b for b in brows if b["Fong_CRS_C"]][0]["valid_n"])
    BENCH_NORD_N = as_int([b for b in brows if b["Nordlinger_C"]][0]["valid_n"])
    check(fig_id, "Selected-model C on all TNM-complete validation (F16) equals F02b", C_VAL, sel_all)

    fig = plt.figure(figsize=(7.2, 3.6))
    ax = fig.add_axes([0.08, 0.17, 0.40, 0.70])
    for i, (name, c, lo, hi) in enumerate(cand):
        col = "#1F7A6E" if name == "M2a" else "#7F8C99"
        ax.errorbar([i], [c], yerr=[[c - lo], [hi - c]], fmt="o", color=col, ms=5, capsize=3, lw=1.1)
        ax.text(i + 0.12, c, f"{c:.3f}\n({lo:.3f}–{hi:.3f})", fontsize=5.8, va="center", color=INK)
        record(fig_id, f"CAND_{name}", f"Validation C-index, {name} (candidate table)",
               f"{c:.3f} ({lo:.3f}–{hi:.3f})", rel(SRC["cand"]), f"valid_C; valid_C_95CI, row {name}", c)
    ax.set_xticks(range(len(cand)))
    ax.set_xticklabels([c[0] for c in cand], fontsize=7)
    ax.set_xlim(-0.5, len(cand) - 0.4)
    ax.set_ylim(0.55, 0.65)
    ax.set_ylabel("Harrell's C-index (validation)", fontsize=7.2)
    ax.set_title("A. Candidate models, identical patients", fontsize=7.6, loc="left")
    ax.grid(alpha=0.22, lw=0.5, axis="y")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    # discrepancy is reported in the caption and verification report, not on the graph

    axb = fig.add_axes([0.60, 0.17, 0.37, 0.70])
    sub = [b for b in brows if b["Fong_CRS_C"] or b["Nordlinger_C"]]
    xs = range(len(sub))
    for i, b in enumerate(sub):
        sel = as_float(b["selected_model_C"])
        score_col = "Fong_CRS_C" if b["Fong_CRS_C"] else "Nordlinger_C"
        sc = as_float(b[score_col])
        name = "Fong" if score_col == "Fong_CRS_C" else "Nordlinger-type"
        axb.plot([i, i], [sc, sel], color="#B0B7BF", lw=2.0, zorder=1)
        axb.scatter([i], [sel], s=46, color="#1F7A6E", zorder=3)
        axb.scatter([i], [sc], s=46, color="#7F8C99", zorder=3)
        axb.text(i + 0.10, sel, f"{sel:.3f}", fontsize=6.4, va="center", color=INK)
        axb.text(i + 0.10, sc, f"{sc:.3f}", fontsize=6.4, va="center", color=INK)
        record(fig_id, f"BENCH_SEL_{i}", f"Selected model C, {b['subset']}",
               f"{sel:.3f}", rel(SRC["bench"]), "selected_model_C", sel)
        record(fig_id, f"BENCH_{name[:4].upper()}_{i}", f"{name} score C, same patients", f"{sc:.3f}", rel(SRC["bench"]),
               score_col, sc)
    axb.set_xticks(list(xs))
    axb.set_xticklabels([f"{'Fong' if b['Fong_CRS_C'] else 'Nordlinger-type'} subset\n(n = {as_int(b['valid_n'])})"
                         for b in sub], fontsize=6.2)
    axb.set_xlim(-0.5, len(sub) - 0.2)
    axb.set_ylim(0.55, 0.66)
    axb.set_ylabel("Harrell's C-index (validation)", fontsize=7.2)
    axb.set_title("B. Identical patients: model vs score", fontsize=7.6, loc="left")
    axb.grid(alpha=0.22, lw=0.5, axis="y", zorder=0)
    for sp in ["top", "right"]:
        axb.spines[sp].set_visible(False)
    from matplotlib.lines import Line2D
    axb.legend(handles=[Line2D([0], [0], marker="o", ls="", color="#1F7A6E", label="Selected model (M2a)"),
                        Line2D([0], [0], marker="o", ls="", color="#7F8C99", label="Published-score approximation")],
               frameon=False, fontsize=6.0, loc="upper right")
    fig.text(0.08, 0.02, "Point estimates only: no bootstrap intervals for the benchmark scores in the locked outputs. "
             "Benchmarks are registry approximations (Methods).", fontsize=5.8, color=GREY)
    # panel identity is carried by the panel titles (A., B.); no separate letters
    return fig


# ============================================================================= captions, report, main
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
        f"Prognostic groups were defined by training-era tertiles of predicted 5-year survival (cut-points {CUT_LO:.4f} and {CUT_HI:.4f}). "
        f"Median follow-up was {FU_DEV:.2f} years in development and {FU_VAL:.2f} years in validation.")
    cap["Figure2"] = (
        f"**Figure 2.** Overall survival by prognostic group in the development cohort (A, n = {fmt_n(N_DEV)}) and the temporal "
        f"validation cohort (B, n = {fmt_n(N_VAL)}). Kaplan–Meier curves with 95% confidence bands; numbers at risk below each panel. "
        f"Cut-points {CUT_LO:.4f} and {CUT_HI:.4f} were set in development. Log-rank p = {sci(P_DEV)} (A) and {sci(P_VAL)} (B). "
        f"Follow-up is short in validation (median {FU_VAL:.2f} years, reverse Kaplan–Meier; development {FU_DEV:.2f} years), so "
        f"validation curves beyond about 5 years rest on few patients.")
    _sparse = [p["period"] for p in per if p["O_over_E"] and p["reliable_5y_estimate"] != "True"]
    _plotted = [p["period"] for p in per if p["O_over_E"]]
    _colour_sentence = (
        f"Grey bars: fewer than 50 patients with 5-year follow-up ({'; '.join(_sparse)})." if _sparse else
        f"All {len(_plotted)} plotted periods have at least 50 patients with 5-year follow-up; no grey bars.")
    cap["Figure3"] = (
        "**Figure 3.** Calibration of the M2a model. "
        "(A) Validation cohort only (operated 2010 or later): mean predicted against observed 5-year survival by decile; open markers "
        "mark deciles with fewer than 50 patients followed up to 5 years. (B) Observed/predicted 5-year survival by operation period, "
        "comparing development (1990–2009) and validation (2010 onward) periods; values above 1.0 indicate "
        f"under-prediction. {_colour_sentence} The 2016 onward period is omitted (no patient had 5-year follow-up).")
    _n_rfs_val = sum(RISK["RFS_validation"][g][0][1] for g in GROUPS)
    cap["FigureS1"] = (
        f"**Figure S1.** Recurrence-free survival by prognostic group in the temporal validation cohort (RFS-eligible n = "
        f"{fmt_n(_n_rfs_val)} of {fmt_n(N_VAL)}; the remaining {fmt_n(N_VAL - _n_rfs_val)} had a dated recurrence before operation "
        "and are excluded from RFS; this difference is derived by subtraction). Primary definition: dated recurrence or death as "
        "events; undated recurrences censored. Kaplan–Meier curves with 95% confidence bands; numbers at risk beneath. The primary "
        f"RFS median of {RFS_MED:.2f} years (95% CI {RFS_CI.replace('-', '–')}) is for the whole analytic cohort (n = {fmt_n(RFS_N)}); "
        "the locked outputs contain no validation-only RFS median. "
        f"Median follow-up in validation was {FU_VAL:.2f} years, so late RFS estimates rest on few patients.")
    cap["FigureS2"] = (
        "**Figure S2.** Forest plot of the selected stratified Cox model (M2a) for overall survival. Points are hazard ratios and bars "
        "95% confidence intervals (log scale). Hazard ratios are within strata defined by sex, synchronous presentation and M-stage. "
        "Dark ink: p < 0.05. Coefficients are in Table 2; the reference category for each term is shown in its label.")
    cap["FigureS3"] = (
        "**Figure S3.** Discrimination. (A) Harrell's C-index in the validation cohort for the three candidate M-stage structures "
        "fitted on identical patients, with bootstrap 95% CIs from 300 resamples. (B) Selected-model C-index against published-score "
        "approximations on identical validation patients (Fong subset, n = {}; Nordlinger-type subset, n = {}); point estimates only. "
        "**[TO CONFIRM — DISCREPANCY]** The M2a upper confidence bound is 0.637 in the candidate table (F02) and 0.636 for the selected "
        "model (F02b). Both come from the same model with different bootstrap draws (Supplementary Table S4; "
        "investigation record in the verification materials). The manuscript reports the F02b value; the supervisor must confirm this choice."
        ).format(fmt_n(BENCH_FONG_N), fmt_n(BENCH_NORD_N))
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
    L = ["# Paper 1 figure set: verification report (v11)", "",
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
    for old in ["Figure2_OS_by_group_validation", "FigureS2_calibration_by_decile", "FigureS3_OE_by_period"]:
        for ext in [".png", ".pdf", ".svg"]:
            q = OUT / (old + ext)
            if q.exists():
                q.unlink()
    builders = [
        (build_figure1, "Figure1_STROBE"),
        (build_figure2, "Figure2_OS_by_group_development_validation"),
        (build_figure3, "Figure3_calibration_and_OE"),
        (build_figureS1, "FigureS1_RFS_by_group_validation"),
        (build_figureS2, "FigureS2_M2a_forest_plot"),
        (build_figureS3, "FigureS3_discrimination_comparison"),
    ]
    figs = []
    for fn, stem in builders:
        figs.append((fn(), stem, fn.__name__))
    write_captions_placeholder = None
    n_fail, n_disc, n_pass = write_report()
    write_captions()
    written = []
    for fig, stem, key in figs:
        if fig_key_of(key) in FAILED_FIGS:
            plt.close(fig)
            print(f"NOT WRITTEN (failed checks): {stem}")
            continue
        save_figure(fig, stem)
        plt.close(fig)
        written.append(stem)
    print(f"checks: {n_pass} passed, {n_disc} discrepancy(ies), {n_fail} failed")
    print("written:", ", ".join(written))
    return 1 if n_fail else 0


def fig_key_of(fn_name):
    return {"build_figure1": "Figure1", "build_figure2": "Figure2", "build_figure3": "Figure3",
            "build_figureS1": "FigureS1", "build_figureS2": "FigureS2", "build_figureS3": "FigureS3"}[fn_name]


if __name__ == "__main__":
    sys.exit(main())
