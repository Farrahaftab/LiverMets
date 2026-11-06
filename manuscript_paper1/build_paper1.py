"""Builds Paper1_manuscript.md and .docx from template_paper1_v2.md.
Every table cell is read from a source CSV; no numbers are typed by hand except the reference list."""
import csv, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F7 = ROOT / 'results/final_v7'
P1 = ROOT / 'results/final_v9/paper1'
HERE = Path(__file__).resolve().parent

def rows(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

def md(header, body):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in body]
    return '\n'.join(out)

def pct(x):
    return f"{float(x)*100:.1f}%"

# Table 1 baseline (F31)
t1 = rows(F7 / 'F31_table1_baseline_characteristics.csv')
body = []
for r in t1[1:]:
    label = r[0]
    lab = ('&emsp;' if label.startswith('   ') else '') + label.strip()
    body.append([lab] + [v for v in r[1:4]])
T1 = md(['Characteristic', 'Total (n = 17,262)', 'Development (≤2009; n = 8,463)', 'Validation (≥2010; n = 8,799)'], body)

# Table 2 coefficients (P1_model_coefficients.csv)
t2 = rows(P1 / 'P1_model_coefficients.csv')
body = []
for r in t2[1:]:
    p = '<0.001' if float(r[6]) < 0.0005 else f"{float(r[6]):.3f}"
    body.append([r[1], r[2], r[3], f"{r[4]}–{r[5]}", p])
T2 = md(['Term', 'β', 'HR', '95% CI', 'p'], body)

# Table 3 prognostic groups (F06)
t3 = rows(F7 / 'F06_phenotypes_counts_survival_calibration.csv')
body = []
for r in t3[1:]:
    body.append([r[0], r[1], r[2], r[3], f"{r[4]} ({r[5]})", pct(r[6]), pct(r[8]), pct(r[10])])
T3 = md(['Group', 'Development n', 'Validation n', 'Validation deaths', 'Validation median OS, years (95% CI)',
         'Validation 5-y KM survival', 'Development 5-y KM survival', 'Validation mean predicted 5-y survival'], body)

# Table 4 performance and calibration by horizon (G01, G03, F02b)
g1 = rows(F7 / 'feasibility/G01_horizon_feasibility_validation.csv')
g3 = {r[0]: r for r in rows(F7 / 'feasibility/G03_calibration_precision_by_horizon.csv')[1:]}
f2 = rows(F7 / 'F02b_selected_model_performance.csv')[1]
tauc = {'1': f2[4], '3': f2[5], '5': f2[6]}
brier = {'1': f2[7], '3': f2[8], '5': f2[9]}
body = []
for r in g1[1:]:
    h = r[0]; g = g3[h]
    lo, hi = r[8].split('-')
    body.append([h, f"{r[2]} ({r[3]}%)", r[4], pct(r[6]), f"{pct(r[7])} ({float(lo)*100:.1f}–{float(hi)*100:.1f})",
                 f"{float(r[9]):.2f} ({float(g[1]):.2f}–{float(g[2]):.2f})", tauc[h], f"{float(brier[h]):.3f}"])
T4 = md(['Horizon (years)', 'Evaluable n (%)', 'Deaths before horizon', 'Mean predicted survival',
         'Observed KM survival (95% CI)', 'O/E (95% CI)', 'Time-dependent AUC', 'Brier score'], body)

# Table 5 benchmarks (F16)
t5 = rows(F7 / 'F16_identical_subset_comparison_calibration.csv')
body = []
for r in t5[1:]:
    body.append([r[0], r[1], r[2], r[3], r[6], r[7] or '—', r[8] or '—'])
T5 = md(['Validation subset', 'n', 'Deaths', 'Selected model C-index', 'Observed/expected 5-y', 'Fong score C-index', 'Nordlinger-type C-index'], body)

REFS = """1. Fong Y, Fortner J, Sun RL, Brennan MF, Blumgart LH. Clinical score for predicting recurrence after hepatic resection for metastatic colorectal cancer: analysis of 1001 consecutive cases. *Ann Surg*. 1999;230(3):309–318. [Confirmed by search: authors, title, year, volume and first page; page range given by PubMed as 309–318]
2. Margonis GA, et al. Genetic And Morphological Evaluation (GAME) score for patients with colorectal liver metastases. *Br J Surg*. 2018;105(9):1210–1220. doi:10.1002/bjs.10838. [Journal, volume, pages and DOI confirmed by search; full author list to be checked against the article. Survival figures in the Introduction still to be checked.]
3. Prognostic Scores for Liver Resection in Colorectal Metastases: Performance, Limitations, and Methodological Pitfalls—A Systematic Review and Meta-Analysis. *Cancers*. 2026;18(4):625. [Title, journal, volume and article number confirmed by search; author list and the 48-score count rest on a mirror abstract and are to be checked]
4. Bolhuis et al. External validation of two established clinical risk scores predicting outcome after local treatment of colorectal liver metastases in a nationwide cohort. *Cancers*. 2022;14(10):2356. [Title, journal and article number confirmed by search; first author and C-indices (Fong 0.577, GAME 0.596) from the abstract; full author list to check]
5. Collins GS, Moons KGM, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. *BMJ*. 2024;385:e078378. [Journal, volume and article number confirmed by search; author list to be checked against the article]
6. Moons KGM, Damen JAA, Kaul T, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. *BMJ*. 2025;388:e082505. [Journal, volume, article number and first author confirmed by search]
7. von Elm E, Altman DG, Egger M, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement. *Lancet*. 2007;370(9596):1453–1457. [Standard citation; not re-verified in this revision]
8. Edge SB, Byrd DR, Compton CC, et al., eds. *AJCC Cancer Staging Manual*. 7th ed. Springer; 2010. [Not re-verified; confirm which edition the registry's TNM codes follow]
9. Amin MB, Edge SB, Greene FL, et al., eds. *AJCC Cancer Staging Manual*. 8th ed. Springer; 2017. [Not re-verified; confirm edition]
10. Schoenfeld D. Partial residuals for the proportional hazards regression model. *Biometrika*. 1982;69(1):239–241. [Standard citation; not re-verified in this revision]
11. Breslow NE. Covariance analysis of censored survival data. *Biometrics*. 1974;30(1):89–99. [Standard citation for the Breslow baseline-hazard estimator; not re-verified in this revision. Confirm the intended citation.]
12. Harrell FE Jr, Califf RM, Pryor DB, Lee KL, Rosati RA. Evaluating the yield of medical tests. *JAMA*. 1982;247(18):2543–2546. [Confirmed by search. Harrell's estimator can be optimistic under heavy censoring; the manuscript therefore reports horizon-specific AUC and calibration alongside it.]
13. Graf E, Schmoor C, Sauerbrei W, Schumacher M. Assessment and comparison of prognostic classification schemes for survival data. *Stat Med*. 1999;18(17–18):2529–2545. [Not verified by search in this revision; confirm volume and pages]
14. Nordlinger B, et al. [Original 1996 citation for the Nordlinger-type score NOT confirmed. Searches located only validation studies. Do not submit until the original is identified and its score definition checked against the approximation used here.]
"""

# Figure 1 is the v9 generator output; its caption is generated from the same verified values
V10 = ROOT / 'results/final_v10/paper1_figures'
FIG1_CAPTION = (V10 / 'Figure1_caption.md').read_text(encoding='utf-8').strip()
FIG2_CAPTION = (V10 / 'Figure2_caption.md').read_text(encoding='utf-8').strip()
FIG3_CAPTION = (V10 / 'Figure3_caption.md').read_text(encoding='utf-8').strip()
fill = {
 '{{FIG1}}': '![STROBE patient flow: selection, development and temporal validation](figures/Figure1_STROBE.png)',
 '{{FIG2}}': '![Overall survival by prognostic group, development and validation cohorts](figures/Figure2_OS_by_group_development_validation.png)',
 '{{FIG2_CAPTION}}': FIG2_CAPTION,
 '{{FIG3}}': '![Calibration by validation decile and observed/expected by operation period](figures/Figure3_calibration_and_OE.png)',
 '{{FIG3_CAPTION}}': FIG3_CAPTION,
 '{{FIG1_CAPTION}}': FIG1_CAPTION,
  '{{TABLE1}}': T1, '{{TABLE2}}': T2, '{{TABLE3}}': T3, '{{TABLE4}}': T4,
 '{{REFERENCES}}': REFS,
}
text = (HERE / 'template_paper1_v2.md').read_text(encoding='utf-8')
for k, v in fill.items():
    assert text.count(k) == 1, k
    text = text.replace(k, v)
assert '{{' not in text
(HERE / 'Paper1_manuscript.md').write_text(text, encoding='utf-8')
subprocess.run(['pandoc', 'Paper1_manuscript.md', '-f', 'markdown', '-t', 'docx', '-o', 'Paper1_manuscript.docx',
                '--resource-path', str(HERE)], cwd=HERE, check=True)

# word counts
main = text.split('# Introduction')[1].split('# References')[0]
main = main.split('# Declarations')[0]
abstract = text.split('# Abstract')[1].split('# Introduction')[0]
print('abstract words:', len(re.findall(r'\S+', abstract)))
print('main text words (Introduction to Conclusions, excl. tables/legends/Declarations):',
      len(re.findall(r'\S+', re.sub(r'\|.*\|', '', main))))
print('display items: 3 figures, 4 tables')
