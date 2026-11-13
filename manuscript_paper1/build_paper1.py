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
    """Pipe table whose separator dashes are proportional to content width, so Word (via pandoc) gives
    wide text columns room and keeps narrow numeric columns narrow. Cell text is unchanged."""
    ncol = len(header)
    weights = []
    for j in range(ncol):
        longest_cell = max([len(str(r[j])) for r in body] + [1])
        longest_word = max(len(w) for w in str(header[j]).split()) if str(header[j]).split() else 1
        weights.append(max(8, min(60, max(longest_cell, longest_word) + 2)))
    total = sum(weights)
    dashes = ['-' * max(3, round(60 * w / total)) for w in weights]
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(dashes) + '|']
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

REFS = """1. Fong Y, Fortner J, Sun RL, Brennan MF, Blumgart LH. Clinical score for predicting recurrence after hepatic resection for metastatic colorectal cancer: analysis of 1001 consecutive cases. *Ann Surg*. 1999;230(3):309–318. [Authors, title, year, volume and first page verified by search; page range per PubMed. Confirm against the article.]
2. Margonis GA, Sasaki K, Gholami S, et al. Genetic And Morphological Evaluation (GAME) score for patients with colorectal liver metastases. *Br J Surg*. 2018;105(9):1210–1220. doi:10.1002/bjs.10838. [Journal, volume, pages, DOI and first three authors verified by search. **Survival figures in the Introduction NOT verified** (search gave only a secondary summary); TO VERIFY from the full text.]
3. Prognostic scores for liver resection in colorectal metastases: performance, limitations, and methodological pitfalls—a systematic review and meta-analysis. *Cancers*. 2026;18(4):625. [Title, journal, volume and article number verified by search from a mirror abstract. **Author list NOT verified.** The 48-score count is from that abstract; TO VERIFY from the article.]
4. Bolhuis K, Wensink GE, Elferink MAG, et al. External validation of two established clinical risk scores predicting outcome after local treatment of colorectal liver metastases in a nationwide cohort. *Cancers*. 2022;14(10):2356. doi:10.3390/cancers14102356. [Authors, journal, volume, article number and DOI verified by search. C-indices (Fong 0.577; GAME 0.596) from the abstract; full text not checked.]
5. Collins GS, Moons KGM, Dhiman P, Riley RD, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. *BMJ*. 2024;385:e078378. [First four authors, journal, volume and article number verified by search; remaining authors not listed here. **Item-level checklist NOT verified** (see the checklist sheet).]
6. Moons KGM, Damen JAA, Kaul T, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. *BMJ*. 2025;388:e082505. [First three authors, journal, volume and article number verified by search.]
7. von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP; STROBE Initiative. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. *Lancet*. 2007;370(9596):1453–1457. doi:10.1016/S0140-6736(07)61602-X. [Authors, journal, volume, pages and DOI verified by search.]
8. Edge SB, Byrd DR, Compton CC, et al., eds. *AJCC Cancer Staging Manual*. 7th ed. New York: Springer; 2010. [**NOT verified** (7th edition not found by search). Confirm the edition and details, and which edition the registry's TNM codes follow.]
9. Amin MB, Edge SB, Greene FL, et al., eds. *AJCC Cancer Staging Manual*. 8th ed. Cham: Springer; 2017. [Editors, publisher and year verified by search (ISBN 978-3-319-40617-6); full editor list to be checked.]
10. Schoenfeld D. Partial residuals for the proportional hazards regression model. *Biometrika*. 1982;69(1):239–241. doi:10.1093/biomet/69.1.239. [Verified by search.]
11. Breslow NE. Covariance analysis of censored survival data. *Biometrics*. 1974;30(1):89–99. doi:10.2307/2529620. [Paper verified by search; one source gives pages 89–100. **Confirm that this is the intended citation** for the piecewise Breslow baseline-hazard estimator; the 1972 discussion paper may be the one intended.]
12. Harrell FE Jr, Califf RM, Pryor DB, Lee KL, Rosati RA. Evaluating the yield of medical tests. *JAMA*. 1982;247(18):2543–2546. [Verified by search. Confirm whether Harrell's later (1996) C-index reference is also wanted.]
13. Graf E, Schmoor C, Sauerbrei W, Schumacher M. Assessment and comparison of prognostic classification schemes for survival data. *Stat Med*. 1999;18(17–18):2529–2545. [Title, journal, volume and pages verified by search (source of the time-dependent Brier score).]
14. Nordlinger B, Guiguet M, Vaillant JC, et al. Surgical resection of colorectal carcinoma metastases to the liver: a prognostic scoring system to improve case selection, based on 1568 patients. *Cancer*. 1996;77(7):1254–1262. [Authors, title, journal, volume and pages verified by search. A search summary lists six factors (age, size or CEA, primary tumour stage, disease-free interval, number of nodules, resection margin); **the registry approximation uses four different items and is not the published score**. Confirm the item definitions from the article.]
"""

# Figure 1 is the v9 generator output; its caption is generated from the same verified values
V10 = ROOT / 'results/final_v10/paper1_figures'
FIG1_CAPTION = (V10 / 'Figure1_caption.md').read_text(encoding='utf-8').strip()
FIG2_CAPTION = (V10 / 'Figure2_caption.md').read_text(encoding='utf-8').strip()
FIG3_CAPTION = (V10 / 'Figure3_caption.md').read_text(encoding='utf-8').strip()
fill = {
 '{{FIG1}}': '![](figures/Figure1_STROBE.png){width=6.2in}',
 '{{FIG2}}': '![](figures/Figure2_OS_by_group_development_validation.png){width=6.5in}',
 '{{FIG2_CAPTION}}': FIG2_CAPTION,
 '{{FIG3}}': '![](figures/Figure3_calibration_and_OE.png){width=6.5in}',
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
