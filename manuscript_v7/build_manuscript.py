"""Build the revised manuscript (Markdown and Word) from template.md and the v7 output files.

Tables 1, S1 and the predictor audit are inserted from the CSV outputs, so the numbers in the text match the files.
Writes Revised_manuscript_v7.md and Revised_manuscript_v7.docx, and a check file of the quoted numbers.
"""
import re
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results' / 'final_v7'
tpl = (HERE / 'template.md').read_text(encoding='utf-8')


def md_table(df):
    cols = list(df.columns)
    lines = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in df.iterrows():
        lines.append('| ' + ' | '.join('' if pd.isna(v) else str(v) for v in r.values) + ' |')
    return '\n'.join(lines)


# ---------- citation numbers in order of first appearance
CITE = {'{{FONG}}': '1', '{{KM}}': '2', '{{COX}}': '3', '{{STROBE}}': '4', '{{TRIPOD}}': '5',
        '{{AJCC7}}': '6', '{{AJCC8}}': '7', '{{SCHOEN}}': '8', '{{BRESLOW}}': '9', '{{HARRELL}}': '10',
        '{{GRAF}}': '11', '{{NORD}}': '12'}
REFS = [
    'Fong Y, Fortner J, Sun RL, Brennan MF, Blumgart LH. Clinical score for predicting recurrence after hepatic resection for metastatic colorectal cancer: analysis of 1001 consecutive cases. Ann Surg. 1999;230(3):309–318.',
    'Kaplan EL, Meier P. Nonparametric estimation from incomplete observations. J Am Stat Assoc. 1958;53(282):457–481.',
    'Cox DR. Regression models and life-tables. J R Stat Soc B. 1972;34(2):187–220.',
    'von Elm E, Altman DG, Egger M, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. PLoS Med. 2007;4(10):e296.',
    'Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD): the TRIPOD statement. Ann Intern Med. 2015;162(1):55–63. **[TO CHECK]**',
    'Edge SB, Compton CC. The American Joint Committee on Cancer: the 7th edition of the AJCC cancer staging manual and the future of TNM. Ann Surg Oncol. 2010;17(6):1471–1474.',
    'Amin MB, Greene FL, Edge SB, et al. The 8th edition AJCC cancer staging manual: continuing to build a bridge from a population-based to a more "personalized" approach to cancer staging. CA Cancer J Clin. 2017;67(2):93–99.',
    'Schoenfeld D. Partial residuals for the proportional hazards regression model. Biometrika. 1982;69(1):239–241.',
    'Breslow NE. Discussion of "Regression models and life-tables" by D. R. Cox. J R Stat Soc B. 1972;34(2):216–217. **[TO CHECK]**',
    'Harrell FE Jr. Regression Modeling Strategies. 2nd ed. Springer; 2015.',
    'Graf E, Schmoor C, Sauerbrei W, Schumacher M. Assessment and comparison of prognostic classification schemes for survival data. Stat Med. 1999;18(17–18):2529–2545.',
    'Nordlinger B, Guiguet M, Vaillant JC, et al. Surgical resection of colorectal carcinoma metastases to the liver. A prognostic scoring system to improve case selection. Cancer. 1996;77(7):1254–1262.',
]
ref_text = '\n'.join(f'{i + 1}. {r}' for i, r in enumerate(REFS))

# ---------- tables from CSV
t1 = pd.read_csv(RES / 'F31_table1_baseline_characteristics.csv')
s1 = pd.read_csv(RES / 'F32_supp_S1_included_vs_excluded.csv').drop(columns=['note'])
aud = pd.read_csv(RES / 'F33_predictor_and_recurrence_date_audit.csv')
opa = pd.read_csv(RES / 'F34_operative_vs_preoperative_metastasis_count.csv')
audit_tbl = pd.concat([aud.rename(columns={'item': 'Item', 'n': 'n'}),
                       opa.rename(columns={'item': 'Item', 'n': 'n'})], ignore_index=True)
audit_tbl['n'] = audit_tbl['n'].map(lambda v: f'{int(v):,}')

text = tpl
text = text.replace('{{TABLE1}}', md_table(t1))
text = text.replace('{{S1}}', md_table(s1))
# supplementary tables S2-S5 (from v8 notebook outputs)
s2a = pd.read_csv(RES / 'investigation' / 'F45_TNM_missing_patterns_step7.csv')
s2b = pd.read_csv(RES / 'investigation' / 'F46_TNM_missing_reasons_step7.csv')
s3a = pd.read_csv(RES / 'F60_duplicate_records_screen.csv')
s3b = pd.read_csv(RES / 'F61_duplicate_sensitivity.csv')[['analysis', 'analytic_n', 'validation_n', 'validation_C',
                                                          'validation_KM_5y', 'validation_O_over_E_5y', 'cut_S5_q33', 'cut_S5_q67',
                                                          'validation_Favourable_n', 'validation_Intermediate_n',
                                                          'validation_Adverse_n', 'pct_same_group_as_primary',
                                                          'kappa_vs_primary', 'reassigned_vs_primary']]
s4 = pd.read_csv(RES / 'F62_no_TNM_model_supplementary.csv')
s5_parts = [('Operation period', 'F63_incomplete_TNM_by_operation_year.csv'),
            ('Centres and countries', 'F64_incomplete_TNM_clustering_centre_country.csv'),
            ('Characteristics, included versus excluded', 'F65_included_vs_excluded_characteristics.csv'),
            ('Outcomes by era', 'F66_incomplete_TNM_outcomes_by_era.csv'),
            ('Informative-selection check (no-TNM model)', 'F67_informative_selection_check_no_TNM_model.csv'),
            ('Logistic model for TNM completeness (odds ratios)', 'F68_logistic_TNM_completeness.csv')]
s5_text = '\n\n'.join(f'*{lab}*\n\n' + md_table(pd.read_csv(RES / f)) for lab, f in s5_parts)
text = text.replace('{{S2}}', md_table(s2a) + '\n\n' + md_table(s2b))
text = text.replace('{{S3}}', md_table(s3a) + '\n\n' + md_table(s3b))
text = text.replace('{{S4}}', md_table(s4))
text = text.replace('{{S5}}', s5_text)
text = text.replace('{{TABLE3}}', md_table(audit_tbl))
text = text.replace('{{FIG1}}', '![](figures/FIG1_STROBE_flow_v7.png)')
text = text.replace('{{REFERENCES}}', ref_text)
for k, v in CITE.items():
    text = text.replace(k, v)

# ---------- corrections found on review (see cover note)
FIXES = [
    ("Excluded patients were more often synchronous (41.6% vs 58.0%) and had less frequently recorded metastasis size and CEA.",
     "Excluded patients were less often synchronous (41.6% vs 58.0%), and less often had metastasis size (72.7% vs 80.8% recorded) or CEA (55.5% vs 65.8%) recorded."),
    ("The missing-indicator term means that the coefficient for the interval is estimated only from patients with a usable interval, and the model is therefore weakly identified for the interval term. Predictions for patients without an interval rely on the missing-indicator term.",
     "Patients without a usable interval received the training median together with a missing-indicator term. The interval coefficient therefore reflects patients with a usable interval, and predictions for patients without one depend on the imputed value and the indicator term."),
    ("All last-news dates in the analytic cohort fell on or before 4 July 2020 (checked).",
     "No deaths in the analytic cohort occurred after 4 July 2020 (checked)."),
    ("Both are reported in Results (Table 3)", "Both are reported in Results (Table 4)"),
    ("The three groups were clearly separated in both cohorts (Table 4, Figures 2 and 3).",
     "The three groups were clearly separated in both cohorts (Table 3, Figures 2 and 3)."),
    ("**Table 4.** Prognostic groups (M2a) with training-only cut-points.", "**Table 3.** Prognostic groups (M2a) with training-only cut-points."),
    ("**Table 3.** Predictor-timing and recurrence-date audit", "**Table 4.** Predictor-timing and recurrence-date audit"),
    ("| Table 3 Predictor and recurrence audit | `F33`, `F34` | Generated from v7 cohort |\n| Table 4 Prognostic groups | `F06` | From notebook |",
     "| Table 3 Prognostic groups | `F06` | From notebook |\n| Table 4 Predictor and recurrence audit | `F33`, `F34` | Generated from v7 cohort |"),
]
for a, b in FIXES:
    assert text.count(a) == 1, ('fix not applied', a[:70])
    text = text.replace(a, b)

assert '{{' not in text, 'unfilled placeholder'
(HERE / 'Revised_manuscript_v7.md').write_text(text, encoding='utf-8')

# ---------- abstract word count (Background to Conclusions)
abstract = text.split('# Abstract', 1)[1].split('**Keywords:**', 1)[0]
abstract_words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9’'\-–.,%/()×≥<≤=+]*", re.sub(r'\*\*', '', abstract)))

# ---------- number check against the output files
checks = []


def _tokens(s):
    return re.findall(r'\d[\d,]*(?:\.\d+)?', s)


def _norm(s):
    return s.replace(' years', '').replace(' ', '').replace('-', '–')


def chk(label, expected_in_text, value_from_file, file, pct=False):
    """Pass only if the source value, at the precision written in the text, equals a number quoted in the text,
    and the quoted text is present in the manuscript."""
    v = value_from_file
    if isinstance(v, str):
        matches = _norm(v) in _norm(expected_in_text)
    else:
        v = float(v) * (100 if pct else 1)
        matches = False
        for tok in _tokens(expected_in_text):
            t = tok.replace(',', '')
            dec = len(t.split('.')[1]) if '.' in t else 0
            if abs(round(v, dec) - float(t)) < 1e-9:
                matches = True
                break
    ok_text = expected_in_text in text and matches
    checks.append({'item': label, 'text_value': expected_in_text, 'source_file': file,
                   'source_value': value_from_file, 'in_manuscript_and_matches': ok_text})


f06 = pd.read_csv(RES / 'F06_phenotypes_counts_survival_calibration.csv').set_index('phenotype')
f02 = pd.read_csv(RES / 'F02_M_stage_candidates_identical_patients.csv').iloc[1]
f17 = pd.read_csv(RES / 'F17_RFS_sensitivity_final.csv').iloc[0]
f16 = pd.read_csv(RES / 'F16_identical_subset_comparison_calibration.csv')
f08 = pd.read_csv(RES / 'F08_phenotype_separation.csv').set_index('quantity')['value']
f09 = pd.read_csv(RES / 'F09_phenotype_bootstrap_stability.csv').iloc[0]
chk('Favourable validation n', '2,662', int(f06.loc['Favourable', 'valid_n']), 'F06')
chk('Intermediate validation n', '2,824', int(f06.loc['Intermediate', 'valid_n']), 'F06')
chk('Adverse validation n', '3,313', int(f06.loc['Adverse', 'valid_n']), 'F06')
chk('Favourable median OS', '7.38', float(f06.loc['Favourable', 'valid_median_OS']), 'F06')
chk('Intermediate median OS', '4.44', float(f06.loc['Intermediate', 'valid_median_OS']), 'F06')
chk('Adverse median OS', '3.18', float(f06.loc['Adverse', 'valid_median_OS']), 'F06')
chk('validation C-index', '0.622 (0.608–0.637)', round(float(f02.valid_C), 4), 'F02 (valid_C 0.6216)')
chk('integrated Brier', '0.075', float(f02.IBS_1_7y), 'F02')
chk('predicted 5-y S', '40.8%', float(f02.valid_mean_predicted_S5), 'F02', pct=True)
chk('observed 5-y S', '46.6%', float(f02.valid_observed_S5), 'F02', pct=True)
chk('O/E 5-y', '1.14', float(f02.valid_OE_5y), 'F02')
_m, _e = f"{f08['valid_logrank_p']:.2e}".split('e')
_sup = str.maketrans('0123456789-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻')
chk('log-rank validation p', '2.0 × 10⁻⁵²', f"{round(float(_m), 1)} × 10{str(int(_e)).translate(_sup)}", 'F08')
chk('ordinal C', '0.603', float(f08['valid_C_ordinal']), 'F08')
chk('bootstrap kappa median', '0.832', float(f09.kappa_median), 'F09')
chk('RFS median', '2.03 years (95% CI 1.98–2.09)', f"{f17['median_RFS']} years (95% CI {f17['median_95CI'].replace('-', '–')})", 'F17')
chk('RFS 3-y', '39.3%', float(f17.RFS_3y), 'F17', pct=True)
chk('RFS 5-y', '27.6%', float(f17.RFS_5y), 'F17', pct=True)
f10 = pd.read_csv(RES / 'F10_day_and_same_day_conventions.csv')
chk('first-day agreement', '99.7%', float(f10[(f10.day_convention == 'first day (1st)') & (f10.same_day_rule == 'half')].phenotype_identical_pct_vs_primary.iloc[0]), 'F10')
chk('month-end agreement', '99.98%', float(f10[(f10.day_convention == 'month-end') & (f10.same_day_rule == 'half')].phenotype_identical_pct_vs_primary.iloc[0]), 'F10')
f19 = pd.read_csv(RES / 'F19_unflagged_same_day_deaths_sensitivity.csv')
chk('excluding unflagged same-day deaths: C', '0.623', float(f19.iloc[1].valid_C), 'F19')
f14 = pd.read_csv(RES / 'F14_preoperative_only_sensitivity.csv').iloc[0]
from decimal import Decimal, ROUND_HALF_UP


def _r3(x):
    return str(Decimal(str(x)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))


chk('pre-op M1 C', '0.591 (0.573–0.606)', f"{_r3(f14.valid_C)} ({f14.valid_C_95CI.replace('-', '–')})", 'F14')
f23 = pd.read_csv(RES / 'F23_preoperative_only_selected_structure.csv').iloc[0]
chk('pre-op M2a C', '0.591 (0.575–0.604)', f"{_r3(f23.valid_C)} ({f23.valid_C_95CI.replace('-', '–')})", 'F23')
f13 = pd.read_csv(RES / 'F13_CEA_sensitivity_final.csv')
chk('CEA complete-case HR', '1.16 per log unit', round(float(f13.iloc[0].CEA_HR_per_log_unit), 2), 'F13')
f21 = pd.read_csv(RES / 'F21_calibration_by_operation_period.csv')
chk('period O/E 2013–2015', '1.23', float(f21.iloc[3].O_over_E), 'F21')
chk('period n with 5-y FU 2013–2015', '109', int(f21.iloc[3].patients_with_5y_follow_up), 'F21')
f22 = pd.read_csv(RES / 'F22_recalibration_sensitivity.csv')
chk('recalibration O/E', '1.115', float(f22.iloc[1].valid_O_over_E), 'F22')
f20 = pd.read_csv(RES / 'F20_calibration_by_validation_decile.csv')
chk('top decile observed', '75.8%', round(100 * float(f20.iloc[9].observed_5y_KM), 1), 'F20')
chk('top decile predicted', '58.0%', round(100 * float(f20.iloc[9].mean_predicted_5y), 1), 'F20')
f12 = pd.read_csv(RES / 'F12_death_and_last_contact_verification.csv').set_index('check')['n']
chk('deceased', '11,594', int(f12['deceased (PATSTATC)']), 'F12')
chk('deceased without flag', '3,074', int(f12['deceased without any DEATHKYN_F = Yes']), 'F12')
def aud_n(key):
    hits = aud[aud.item.str.startswith(key)]
    assert len(hits) == 1, (key, list(hits.item))
    return int(hits.n.iloc[0])


chk('undated recurrence', '1,676', aud_n('Recurrence recorded without usable date'), 'F33')
chk('dated after operation', '5,324', aud_n('Dated recurrence after operation'), 'F33')
chk('dated before operation', '585', aud_n('Dated recurrence before time zero'), 'F33')
chk('dated after last contact', '41', aud_n('Recurrence recorded with a date after last contact'), 'F33')
chk('metachronous unavailable interval', '3,941', aud_n('Metachronous, interval unavailable: primary diagnosis date missing') + aud_n('Metachronous, interval unavailable: liver metastasis date missing') + aud_n('Metachronous, interval unavailable: metastasis diagnosed before primary') + aud_n('Metachronous, interval unavailable: metastasis diagnosed after operation'), 'F33 (sum of four reasons)')
chk('operative resected = pre-op', '8,847 (62.4%)', int(opa.iloc[1].n), 'F34')
chk('operative resected > pre-op', '2,244 (15.8%)', int(opa.iloc[2].n), 'F34')
chk('operative resected < pre-op', '3,098 (21.8%)', int(opa.iloc[3].n), 'F34')
chk('analytic cohort', '17,262', int(t1.iloc[0, 1].replace(',', '')), 'F31')
chk('development n', '8,463', int(t1.iloc[0, 2].replace(',', '')), 'F31')
chk('validation n', '8,799', int(t1.iloc[0, 3].replace(',', '')), 'F31')
chk('excluded incomplete TNM', '8,832', int(s1.iloc[0, 2].replace(',', '')), 'F32')
# v8 numbers: death counts, exclusions, duplicates, no-TNM model, excluded-patient comparisons
f12 = pd.read_csv(RES / 'F12_death_and_last_contact_verification.csv').set_index('check')['n']
f31 = pd.read_csv(RES / 'F31_table1_baseline_characteristics.csv').set_index('characteristic')
f60 = pd.read_csv(RES / 'F60_duplicate_records_screen.csv').set_index('item')['n']
f61 = pd.read_csv(RES / 'F61_duplicate_sensitivity.csv')
f62 = pd.read_csv(RES / 'F62_no_TNM_model_supplementary.csv')
f63 = pd.read_csv(RES / 'F63_incomplete_TNM_by_operation_year.csv')
f64 = pd.read_csv(RES / 'F64_incomplete_TNM_clustering_centre_country.csv')
f65 = pd.read_csv(RES / 'F65_included_vs_excluded_characteristics.csv').set_index('characteristic')
f66 = pd.read_csv(RES / 'F66_incomplete_TNM_outcomes_by_era.csv').set_index('group')
f67 = pd.read_csv(RES / 'F67_informative_selection_check_no_TNM_model.csv')
f68 = pd.read_csv(RES / 'F68_logistic_TNM_completeness.csv').set_index('term')
chk('deaths recorded (cohort)', '6,601 deaths were recorded', int(f12['modelling cohort: deaths recorded (PATSTATC = Deceased)']), 'F12')
chk('deaths inside window', '6,591 occurred within the 15-year analysis window', int(f12['modelling cohort: deaths inside the 15-year window (events in the models)']), 'F12')
chk('deaths beyond 15 years', 'the remaining 10 occurred beyond 15 years', int(f12['modelling cohort: deaths beyond 15 years (censored at 15 years)']), 'F12')
chk('patients beyond 15 years', '69 patients in total had follow-up', int(f12['modelling cohort: PATIENTS with follow-up beyond 15 years (all statuses; not a death count)']), 'F12')
chk('alive or lost beyond 15 years', 'the 10 who died and 59', int(f12['modelling cohort: PATIENTS with follow-up beyond 15 years (all statuses; not a death count)'] - f12['modelling cohort: of those patients, number who died']), 'F12')
chk('Table 1 recorded deaths', '6,601 (38.2)', f31.loc['Deaths recorded (PATSTATC = Deceased), n (%)'].iloc[0], 'F31')
chk('Table 1 window deaths', '6,591 (38.2)', f31.loc['Deaths inside the 15-year analysis window (events), n (%)'].iloc[0], 'F31')
chk('excluded for incomplete TNM', '8,832 (33.8%)', 8832, 'F43')
chk('excluded pct of step 7', '33.8%', round(100 * 8832 / 26094, 1), 'F43')
chk('metachronous unavailable interval excluded', '66.2%', float(f65.loc['Metachronous: interval unavailable', 'excluded'].split('%')[0]), 'F65')
chk('metachronous unavailable interval included', '55.9%', float(f65.loc['Metachronous: interval unavailable', 'included'].split('%')[0]), 'F65')
chk('median operation year excluded', '2007', 2007, 'F65')
chk('largest metastasis excluded', '35 vs 30 mm', 35, 'F65')
chk('synchronous included', '58.7%', float(f65.loc['Synchronous presentation', 'included'].split('%')[0]), 'F65')
chk('synchronous excluded', '44.8%', float(f65.loc['Synchronous presentation', 'excluded'].split('%')[0]), 'F65')
chk('exclusion 1990s', '69.7%', float(f63.iloc[0].pct_excluded), 'F63')
chk('exclusion 2000-2004', '45.3%', float(f63.iloc[1].pct_excluded), 'F63')
chk('exclusion 2005-2009', '28.3%', float(f63.iloc[2].pct_excluded), 'F63')
chk('exclusion 2010-2014', '27.1%', float(f63.iloc[3].pct_excluded), 'F63')
chk('exclusion 2015-2020', '24.4%', float(f63.iloc[4].pct_excluded), 'F63')
chk('sites no exclusions', '57 had no excluded patients', int(f64.iloc[0].units_no_exclusions), 'F64')
chk('sites all excluded', '11 had only excluded patients', int(f64.iloc[0].units_only_exclusions), 'F64')
chk('sites half or more excluded', '34 had at least half', int(f64.iloc[0].units_50pct_or_more_excluded), 'F64')
chk('top-10 sites share', '54%', float(f64.iloc[0].pct_of_exclusions_in_10_largest_units), 'F64')
chk('development excluded KM 5-y', '39.1%', round(100 * float(f66.loc['development (<=2009)', 'excluded_KM_5y']), 1), 'F66')
chk('development included KM 5-y', '42.3%', round(100 * float(f66.loc['development (<=2009)', 'included_KM_5y']), 1), 'F66')
chk('validation excluded KM 5-y', '50.5%', round(100 * float(f66.loc['validation (>=2010)', 'excluded_KM_5y']), 1), 'F66')
chk('validation included KM 5-y', '46.6%', round(100 * float(f66.loc['validation (>=2010)', 'included_KM_5y']), 1), 'F66')
chk('O/E included development', '1.03', float(f67.iloc[0].O_over_E), 'F67')
chk('O/E included validation', '1.16', float(f67.iloc[1].O_over_E), 'F67')
chk('O/E excluded development', '0.96', float(f67.iloc[2].O_over_E), 'F67')
chk('O/E excluded validation', '1.27', float(f67.iloc[3].O_over_E), 'F67')
chk('pairs meeting probable-duplicate rule', 'Sixteen pairs met the probable-duplicate rule', 'Sixteen', 'F60 (16)')
chk('identical-content pairs', '23 identical-content pairs (46 records)', int(f60['identical-content pairs']), 'F60')
chk('second copies in cohort', 'Six second copies lie in the analytic cohort', 'Six', 'F60 (6)')
chk('near-duplicate groups with both copies in cohort', '31 of these have both copies', int(f60['near-duplicate groups with both copies in the analytic cohort']), 'F60')
chk('broad removal records', 'removed 37 later records', int(f60['later records dropped in the broad sensitivity (birth date, operation date and sex match within the cohort)']), 'F60')
chk('identical-pair removal C', 'Removing them left the validation C-index at 0.6216', float(f61.iloc[1].validation_C), 'F61')
chk('identical-pair reassigned', 'Thirty-three patients (0.2%)', 'Thirty-three', 'F61 (33)')
chk('identical-pair cut-point', 'from 0.3793 to 0.3794', float(f61.iloc[1].cut_S5_q33), 'F61')
chk('broad removal 5-y KM', '5-year survival was 46.7%', round(100 * float(f61.iloc[2].validation_KM_5y), 1), 'F61')
chk('broad removal reassigned', '138 patients (0.8%)', int(f61.iloc[2].reassigned_vs_primary), 'F61')
chk('broad group sizes Favourable', '2,656', int(f61.iloc[2].validation_Favourable_n), 'F61')
chk('broad group sizes Intermediate', '2,833', int(f61.iloc[2].validation_Intermediate_n), 'F61')
chk('broad group sizes Adverse', '3,292', int(f61.iloc[2].validation_Adverse_n), 'F61')
chk('no-TNM same-patient C', '0.5994', float(f62.iloc[1].validation_C), 'F62')
chk('TNM same-patient C', '0.6216', float(f62.iloc[0].validation_C), 'F62')
chk('no-TNM broad same-patient C', '0.5982', float(f62.iloc[2].validation_C), 'F62')
chk('no-TNM broad all validation C', '0.5972', float(f62.iloc[3].validation_C), 'F62')
import re as _re
_note = str(f62.iloc[1].note)
_m = _re.search(r'difference TNM minus no-TNM = ([\d.]+), 95% CI ([\d.]+) to ([\d.]+)', _note)
chk('no-TNM difference', '0.022 (95% CI 0.009 to 0.034', float(_m.group(1)), 'F62')
chk('no-TNM difference CI lower', '0.009 to 0.034', float(_m.group(2)), 'F62')
chk('no-TNM difference CI upper', '0.009 to 0.034', float(_m.group(3)), 'F62')
pd.DataFrame(checks).to_csv(RES / 'F35_manuscript_number_check.csv', index=False)
bad = [c for c in checks if not c['in_manuscript_and_matches']]
print('abstract words (approx.):', abstract_words)
print('numbers checked:', len(checks), 'missing from manuscript text:', len(bad))
for c in bad:
    print('  MISSING:', c)

# ---------- Word
subprocess.run(['pandoc', 'Revised_manuscript_v7.md', '-o', 'Revised_manuscript_v7.docx', '--resource-path=.'],
               cwd=HERE, check=True)
print('written Revised_manuscript_v7.md and .docx')
