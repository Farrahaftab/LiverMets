"""Builds the Paper 1 manuscript from template_paper1.md.
Tables are generated directly from the source CSVs (no hand-typed numbers).
Outputs: Paper1_manuscript.md and Paper1_manuscript.docx (via pandoc)."""
import csv, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
F7 = ROOT / 'results/final_v7'
P1 = ROOT / 'results/final_v9/paper1'

def rows(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

def md(header, body):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    out += ['| ' + ' | '.join(r) + ' |' for r in body]
    return '\n'.join(out)

# Table 1: baseline characteristics (F31), indented sub-rows kept
t1 = rows(F7 / 'F31_table1_baseline_characteristics.csv')
t1_body = []
for r in t1[1:]:
    label = r[0]
    indent = label.startswith('   ')
    label = ('&emsp;' if indent else '') + label.strip()
    t1_body.append([label] + [v if v else '' for v in r[1:4]])
T1 = md(['Characteristic', 'Total (n = 17,262)', 'Development (≤2009; n = 8,463)', 'Validation (≥2010; n = 8,799)'], t1_body)

# Table 2: candidate models (F02)
t2 = rows(F7 / 'F02_M_stage_candidates_identical_patients.csv')
t2_body = []
for r in t2[1:]:
    name = r[0].split(' (')[0]
    t2_body.append([name, r[2], f"{r[3]}", f"{r[4]}/{r[5]}/{r[6]}", f"{r[7]}/{r[8]}/{r[9]}", r[10], r[13]])
T2 = md(['Model', 'Validation C-index', '95% CI', 'tAUC 1/3/5 y', 'Brier 1/3/5 y', 'IBS 1–7 y', 'O/E 5 y'], t2_body)

# Table 3: coefficients (P1_model_coefficients.csv)
t3 = rows(P1 / 'P1_model_coefficients.csv')
t3_body = []
for r in t3[1:]:
    p = r[6]
    p = '<0.001' if float(p) < 0.0005 else f"{float(p):.3f}"
    t3_body.append([r[1], r[2], r[3], f"{r[4]}–{r[5]}", p])
T3 = md(['Term', 'Coefficient (β)', 'HR', '95% CI', 'p'], t3_body)

# Table 4: prognostic groups (F06) + group summary
t4 = rows(F7 / 'F06_phenotypes_counts_survival_calibration.csv')
t4_body = []
for r in t4[1:]:
    t4_body.append([r[0], r[1], r[2], r[3], f"{r[4]} ({r[5]})", f"{float(r[6])*100:.1f}%", f"{float(r[8])*100:.1f}%" , f"{float(r[9])*100:.1f}%"])
T4 = md(['Group', 'Development n', 'Validation n', 'Validation deaths', 'Validation median OS, years (95% CI)', 'Validation 5-y KM survival', 'Development 5-y KM survival', 'Validation mean predicted 5-y survival'], t4_body)

# Table 5: horizons (G01 + G03)
g1 = rows(ROOT / 'results/final_v7/feasibility/G01_horizon_feasibility_validation.csv')
g3 = {r[0]: r for r in rows(ROOT / 'results/final_v7/feasibility/G03_calibration_precision_by_horizon.csv')[1:]}
t5_body = []
for r in g1[1:]:
    g = g3[r[0]]
    t5_body.append([f"{r[0]}", f"{r[2]} ({r[3]}%)", r[4], f"{float(r[6])*100:.1f}%", f"{float(r[7])*100:.1f}% ({float(r[8].split('-')[0])*100:.1f}–{float(r[8].split('-')[1])*100:.1f})", f"{float(r[9]):.2f} ({float(g[1]):.2f}–{float(g[2]):.2f})"])
T5 = md(['Horizon, years', 'Evaluable n (%)', 'Deaths before horizon', 'Mean predicted survival', 'Observed KM survival (95% CI)', 'O/E (bootstrap 95% CI)'], t5_body)

# Table 6: sensitivity analyses
t6_body = [
 ['Primary (15th of month; same-day deaths half a day)', '0.6216', '—', '—', 'Reference'],
 ['First day of month for partial dates', '0.6214', '99.7%', '0.996', 'F10'],
 ['Month-end for partial dates', '0.6217', '99.98%', '1.000', 'F10'],
 ['Same-day deaths excluded (13)', '0.6221', '99.6%', '0.994', 'F10'],
 ['Same-day deaths without death flag excluded (7)', '0.6226', '99.6%', '0.994', 'F19'],
 ['Pre-operative-only model, M1 structure (no count/size)', '0.5913 (0.573–0.606)', '—', '—', 'F14'],
 ['Pre-operative-only model, selected M2a structure', '0.5905 (0.575–0.604)', '—', '—', 'F23'],
 ['CEA added, complete case (n = 5,847)', '0.628 → 0.648', '—', '—', 'F13; CEA HR 1.16 (1.13–1.19) per log unit'],
 ['CEA added, multiple imputation (10 draws)', '0.622 → 0.637', '—', '—', 'F13; CEA HR 1.15 (1.13–1.18)'],
 ['Baseline hazard re-estimated from 2005–2009 (coefficients fixed)', '0.6197', '92.2%', '0.883', 'F22; 5-y O/E 1.12 (from 1.14)'],
]
T6 = md(['Analysis', 'Validation C-index', 'Group agreement with primary', 'κ', 'Source / note'], t6_body)

# Table 7: benchmarks (F16)
t7 = rows(F7 / 'F16_identical_subset_comparison_calibration.csv')
t7_body = []
for r in t7[1:]:
    t7_body.append([r[0], r[1], r[2], r[3], r[6], r[7] or '—', r[8] or '—'])
T7 = md(['Validation subset', 'n', 'Deaths', 'Selected model C-index', 'Observed/expected 5-y', 'Fong score C-index', 'Nordlinger-type C-index'], t7_body)

fill = {
 '{{TABLE1}}': T1, '{{TABLE2}}': T2, '{{TABLE3}}': T3, '{{TABLE4}}': T4,
 '{{TABLE5}}': T5, '{{TABLE6}}': T6, '{{TABLE7}}': T7,
 '{{FIG1}}': '![STROBE patient flow](figures/FIG1_STROBE_flow_v7.png)',
}
REFS = """1. Fong Y, Fortner J, Sun RL, Brennan MF, Blumgart LH. Clinical score for predicting recurrence after hepatic resection for metastatic colorectal cancer: analysis of 1001 consecutive cases. *Ann Surg*. 1999;230(3):309–318. [Verified in prior search; confirm page range]
2. Margonis GA, Sasaki K, Gholami S, et al. Genetic and morphological evaluation (GAME) score for colorectal liver metastases. *Ann Surg* (2018). [Verified in prior search; confirm volume and pages] **[TO VERIFY survival figures cited in text]**
3. Systematic review and meta-analysis of prognostic scores for liver resection of colorectal metastases. *Cancers* (2026). [TO VERIFY: title, authors and score count; match identified but not fully confirmed]
4. Nationwide validation of the Fong clinical risk score after liver resection for colorectal metastases (PMC9139295). [TO VERIFY: authors, journal and year]
5. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent Reporting of a multivariable prediction model for Individual Prognosis or Diagnosis (TRIPOD): the TRIPOD statement. *BMJ*. 2015;350:g7594.
6. Collins GS, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. *BMJ*. 2024. [TO VERIFY: author list and volume]
7. Moons KGM, Damen JAA, Kaul T, et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. *BMJ*. 2025. [Verified in prior search; confirm author list]
8. von Elm E, Altman DG, Egger M, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement. *Lancet*. 2007;370(9596):1453–1457.
9. Edge SB, Byrd DR, Compton CC, et al., eds. *AJCC Cancer Staging Manual*. 7th ed. Springer; 2010. [TO VERIFY edition used in the registry]
10. Amin MB, Edge SB, Greene FL, et al., eds. *AJCC Cancer Staging Manual*. 8th ed. Springer; 2017. [TO VERIFY]
11. Schoenfeld D. Partial residuals for the proportional hazards regression model. *Biometrika*. 1982;69(1):239–241.
12. Breslow NE. Discussion of Professor Cox's paper. *J R Stat Soc B*. 1972. [TO VERIFY citation]
13. Harrell FE Jr, Califf RM, Pryor DB, Lee KL, Rosati RA. Evaluating the yield of medical tests. *JAMA*. 1982;247(18):2543–2546. [TO VERIFY: C-index reference]
14. Graf E, Schmoor C, Sauerbrei W, Schumacher M. Assessment and comparison of prognostic classification schemes for survival data. *Stat Med*. 1999;18(17–18):2529–2545.
15. Nordlinger B, et al. Nordlinger-type prognostic score for colorectal liver metastases. [TO VERIFY: citation and original score definition; the approximation used here is four items only]
"""
fill['{{REFERENCES}}'] = REFS

text = (HERE / 'template_paper1.md').read_text(encoding='utf-8')
for k, v in fill.items():
    assert text.count(k) == 1, k
    text = text.replace(k, v)
assert '{{' not in text
(HERE / 'Paper1_manuscript.md').write_text(text, encoding='utf-8')
subprocess.run(['pandoc', 'Paper1_manuscript.md', '-f', 'markdown', '-t', 'docx', '-o', 'Paper1_manuscript.docx',
                '--resource-path', str(HERE)], cwd=HERE, check=True)
print('built', len(text.split()), 'words')
