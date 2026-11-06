"""Builds Paper1_supplementary.md and .docx. Tables are read from source CSVs; wide tables are
reshaped so each metric is a row and each analysis a column."""
import csv, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
F7 = ROOT / 'results/final_v7'; P1 = ROOT / 'results/final_v9/paper1'; HERE = Path(__file__).resolve().parent

def rows(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

def md(header, body):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in body]
    return '\n'.join(out)

def select(p, cols, names=None):
    r = rows(p); h = r[0]; idx = [h.index(c) for c in cols]
    return md(names or cols, [[row[i] for i in idx] for row in r[1:]])

def transpose_table(title_cols, data):
    """data: list of (metric, [values per analysis])"""
    return md(title_cols, [[m] + v for m, v in data])

S = []
S.append("# Supplementary Material — Paper 1\n\nAll tables are generated from the locked v8 outputs (`results/final_v7`) and the Paper 1 coefficient outputs (`results/final_v9/paper1`). No model was re-estimated.")

S.append("## Table S1. Included versus excluded patients\n\nSources: `F32` (characteristics) and `F65` (standardised mean differences).\n\n" +
         select(F7/'F32_supp_S1_included_vs_excluded.csv', ['characteristic','Analytic cohort (TNM complete, n=17,262)','Excluded, incomplete TNM (n=8,832)'],
                ['Characteristic','Included (n = 17,262)','Excluded (n = 8,832)']) +
         "\n\n" + select(F7/'F65_included_vs_excluded_characteristics.csv', ['characteristic','included','excluded','SMD'],
                ['Characteristic','Included','Excluded','Standardised mean difference']))

t = rows(F7/'investigation/F45_TNM_missing_patterns_step7.csv')
S.append("## Table S2. Missing TNM components and exclusion patterns\n\n**S2a. Missing components among the 26,094 patients meeting criteria** (`investigation/F45`).\n\n" +
         md(['Missing components','n','% of 26,094'], [[r[0], r[1], f"{float(r[2]):.1f}"] for r in t[1:]]) +
         "\n\n**S2b. Exclusion by operation period** (`F63`).\n\n" + select(F7/'F63_incomplete_TNM_by_operation_year.csv', ['operation_years','analytic_n','excluded_n','pct_excluded'], ['Operation years','Included','Excluded','% excluded']) +
         "\n\n**S2c. Exclusion clustering by site and country** (`F64`; a site is a registry site code).\n\n" + select(F7/'F64_incomplete_TNM_clustering_centre_country.csv', ['level','units','units_no_exclusions','units_only_exclusions','units_50pct_or_more_excluded','median_patients_per_unit','pct_of_exclusions_in_10_largest_units'], ['Level','Units','No exclusions','Only exclusions','≥50% excluded','Median patients per unit','% of exclusions in 10 largest']) +
         "\n\n**S2d. Outcomes of included and excluded patients by era** (`F66`).\n\n" + select(F7/'F66_incomplete_TNM_outcomes_by_era.csv', ['group','included_n','excluded_n','included_KM_5y','excluded_KM_5y','included_KM_median_y','excluded_KM_median_y'], ['Era','Included n','Excluded n','Included 5-y KM','Excluded 5-y KM','Included median OS (y)','Excluded median OS (y)']) +
         "\n\n**S2e. Observed/expected survival relative to a no-TNM model** (`F67`). Interpret with caution: this is a selection check, not a validation.\n\n" + select(F7/'F67_informative_selection_check_no_TNM_model.csv', ['group','period','n','predicted_5y_no_TNM','observed_5y_KM','O_over_E'], ['Group','Period','n','Predicted 5-y (no TNM)','Observed 5-y KM','O/E']))

S.append("## Table S3. Duplicate-record screen and sensitivity analyses\n\n**S3a. Screen** (`F60`).\n\n" + select(F7/'F60_duplicate_records_screen.csv', ['item','n'], ['Item','n']) +
         "\n\n**S3b. Effect on validation results** (`F61`). Columns are the primary analysis and two sensitivity analyses. C-index and survival are for the validation cohort.\n\n")
f61 = {r[0]: r for r in rows(F7/'F61_duplicate_sensitivity.csv')[1:]}
a, b, c = [f61[k] for k in ['primary (locked)', 'identical-pair second copies removed', 'later copies of birth/operation/sex matches removed (broad)']]
def cells(vals): return vals
metrics = [
 ('Analytic cohort (n)', [a[1], b[1], c[1]]),
 ('Development (n)', [a[2], b[2], c[2]]),
 ('Validation (n)', [a[3], b[3], c[3]]),
 ('Validation C-index', [a[4], b[4], c[4]]),
 ('Validation 5-y Kaplan–Meier survival', [f"{float(x)*100:.1f}%" for x in (a[5], b[5], c[5])]),
 ('Validation O/E at 5 years', [f"{float(x):.3f}" for x in (a[6], b[6], c[6])]),
 ('Cut-point, lower tertile (predicted 5-y survival)', [a[7], b[7], c[7]]),
 ('Cut-point, upper tertile (predicted 5-y survival)', [a[8], b[8], c[8]]),
 ('Validation Favourable / Intermediate / Adverse (n)', [f"{a[9]} / {a[10]} / {a[11]}", f"{b[9]} / {b[10]} / {b[11]}", f"{c[9]} / {c[10]} / {c[11]}"]),
 ('Patients in the same group as primary (%)', ['—', b[13], c[13]]),
 ('Agreement with primary grouping (κ)', ['—', f"{float(b[14]):.3f}", f"{float(c[14]):.3f}"]),
 ('Patients reassigned to a different group', ['—', f"{float(b[15]):.0f}", f"{float(c[15]):.0f}"]),
]
S[-1] = S[-1] + transpose_table(['Metric', 'Primary (locked)', 'Identical-pair second copies removed (6 in cohort)', 'Broad rule: later copies removed (37)'], metrics)

S.append("## Table S4. Candidate models and proportional-hazards tests\n\n**S4a. Candidate models on identical patients** (`F02`). Validation n = 8,799; 5-y observed survival 46.6%. Each row's bootstrap CI comes from its own 300 resamples drawn at a different point in the random stream, so the M2a upper bound here (0.637) can differ by 0.001 from the selected-model value (0.636, `F02b`, used in the text and Figure 1). See `results/final_v9/figure1/CI_discrepancy_investigation.md`.\n\n" +
         select(F7/'F02_M_stage_candidates_identical_patients.csv', ['model','train_C','valid_C','valid_C_95CI','tAUC_5y','Brier_5y','valid_mean_predicted_S5','valid_OE_5y','valid_calib_slope_5y'],
                ['Model','Training C','Validation C','95% CI','5-y AUC','5-y Brier','Mean predicted 5-y','O/E 5 y','Calibration slope']) +
         "\n\n**S4b. Schoenfeld tests, training cohort, constant terms** (`F03`); M-stage is the term of interest.\n\n" +
         select(F7/'F03_PH_tests_training_constant_terms.csv', ['model','term','test_statistic','p'], ['Model','Term','Test statistic','p']) +
         "\n\n**S4c. Time-varying M-stage (M2b)** (`F04`).\n\n" + select(F7/'F04_M2b_time_varying_M_stage.csv', ['term','coef','HR_early','p_time_variation','HR_late'], ['Term','Coefficient','HR early','p (time variation)','HR late']) +
         "\n\n**S4d. Selection rule** (`F05`): choose the simplest candidate whose constant-term tests all have p > 0.05 in training data. Selected: M2a.")

S.append("## Table S5. Sensitivity analyses\n\n**S5a. Date conventions and same-day deaths** (`F10`, validation cohort; primary = 15th of month, half-day rule).\n\n" +
         select(F7/'F10_day_and_same_day_conventions.csv', ['day_convention','same_day_rule','modelling_cohort_TNM','valid_C','cut_S5_q33','cut_S5_q67','phenotype_identical_pct_vs_primary','kappa_vs_primary'],
                ['Date convention','Same-day rule','Analytic n','Validation C','Cut-point 1','Cut-point 2','Same groups (%)','κ']) +
         "\n\n**S5b. Same-day deaths without death flag** (`F19`).\n\n" + select(F7/'F19_unflagged_same_day_deaths_sensitivity.csv', ['analysis','modelling_cohort_TNM','valid_C','phenotype_identical_pct_vs_primary','kappa_vs_primary'], ['Analysis','Analytic n','Validation C','Same groups (%)','κ']) +
         "\n\n**S5c. Carcinoembryonic antigen** (`F13`).\n\n" + select(F7/'F13_CEA_sensitivity_final.csv', ['analysis','valid_n','CEA_HR_per_log_unit','CEA_HR_95CI','valid_C_without_CEA','valid_C_with_CEA'], ['Analysis','Validation n','CEA HR per log unit','95% CI','C without CEA','C with CEA']) +
         "\n\n**S5d. Pre-operative-only models (no count or size)** (`F14`, `F23`).\n\n" + select(F7/'F14_preoperative_only_sensitivity.csv', ['model','valid_C','valid_C_95CI','valid_OE_5y','valid_calib_slope_5y'], ['Model','Validation C','95% CI','O/E 5 y','Calibration slope']) + "\n\n" + select(F7/'F23_preoperative_only_selected_structure.csv', ['model','valid_C','valid_C_95CI','valid_OE_5y','valid_calib_slope_5y'], ['Model','Validation C','95% CI','O/E 5 y','Calibration slope']) +
         "\n\n**S5e. Recalibration from 2005–2009 baseline** (`F22`; coefficients fixed).\n\n" + select(F7/'F22_recalibration_sensitivity.csv', ['analysis','valid_mean_predicted_5y','valid_O_over_E','valid_C','agreement_validation_kappa','agreement_pct_validation'], ['Analysis','Mean predicted 5-y','O/E 5 y','Validation C','κ vs primary','% same group']) +
         "\n\n**S5f. No-TNM model on the same patients** (`F62`). The TNM model is 0.6216 on the same 8,799 patients.\n\n" + select(F7/'F62_no_TNM_model_supplementary.csv', ['analysis','development_n','validation_n','validation_C','note'], ['Analysis','Development n','Validation n','Validation C','Note']))

S.append("## Table S6. Death flags and the 15-year window\n\n**S6a.** Sources: `F12`. The first block covers the full extract; the last rows cover the analytic cohort.\n\n" + select(F7/'F12_death_and_last_contact_verification.csv', ['check','n'], ['Check','n']) +
         "\n\n**S6b. Death-flag rate by time from operation** (`F18b`).\n\n" + select(F7/'F18b_death_flag_rate_by_time_from_operation.csv', ['time_from_operation','n','flag_yes','flag_yes_pct'], ['Time from operation','Deaths','Flag = yes','% flagged']))

S.append("## Table S7. Reproduction check\n\nSource: `F25`. Each quantity was reproduced from the notebook against the previously validated values.\n\n" + select(F7/'F25_reproduction_check_against_v6.csv', ['check','this_run','v6_reference','result'], ['Check','This run','Previously validated','Result']))

S.append("## Table S8. Horizon feasibility, group events and recurrence-free survival\n\n**S8a. Group events by horizon** (`G02`, validation).\n\n" + select(F7/'feasibility/G02_group_events_by_horizon_validation.csv', ['group','horizon_years','n','deaths_before_horizon','at_risk_at_horizon'], ['Group','Horizon (y)','n','Deaths before horizon','At risk at horizon']) +
         "\n\n**S8b. Centre-held-out feasibility** (`G04`). Descriptive only; no centre-held-out model was fitted for this manuscript.\n\n" + select(F7/'feasibility/G04_centre_held_out_feasibility.csv', ['threshold_TNM_complete_patients_per_unit','sites_meeting_threshold','sites_with_validation_events_20plus','patients_in_qualifying_sites_pct','countries_meeting_threshold'], ['Minimum patients per site','Sites meeting threshold','Sites with ≥20 validation events','% of patients in qualifying sites','Countries meeting threshold']) +
         "\n\n**S8c. Recurrence-free survival handling rules** (`F17`).\n\n" + select(F7/'F17_RFS_sensitivity_final.csv', ['RFS_analysis','n','events','median_RFS','median_95CI','RFS_3y','RFS_5y'], ['Rule','n','Events','Median (y)','95% CI','3-y RFS','5-y RFS']) +
         "\n\n**S8d. Undated recurrence check** (`F11`).\n\n" + select(F7/'F11_undated_recurrence_informative_censoring_check.csv', ['group','n','median_age','T4_pct','N2_pct','M1_pct','OS_median_years','deaths_pct'], ['Group','n','Median age','T4 %','N2 %','M1 %','Median OS (y)','Deaths %']))

S.append("## Table S9. Reporting checklists\n\nSee `Paper1_reporting_checklists.docx` (TRIPOD+AI primary; STROBE; PROBAST+AI status).")

V10 = ROOT / 'results/final_v10/paper1_figures'
S1_CAP = (V10 / 'FigureS1_caption.md').read_text(encoding='utf-8').strip()
S2_CAP = (V10 / 'FigureS2_caption.md').read_text(encoding='utf-8').strip()
S3_CAP = (V10 / 'FigureS3_caption.md').read_text(encoding='utf-8').strip()
S.append("## Supplementary figures\n\n" + S1_CAP + "\n\n![](figures/FigureS1_RFS_by_group_validation.png)\n\n" +
         S2_CAP + "\n\n![](figures/FigureS2_calibration_by_decile.png)\n\n" +
         S3_CAP + "\n\n![](figures/FigureS3_OE_by_period.png)")

S.append("## Coefficient outputs\n\nBaseline survival by stratum (`P1_baseline_survival_by_stratum.csv`) and group summary (`P1_group_summary.csv`) are in `results/final_v9/paper1/`.\n\n" +
         select(P1/'P1_baseline_survival_by_stratum.csv', list(rows(P1/'P1_baseline_survival_by_stratum.csv')[0]), None) +
         "\n\n" + select(P1/'P1_group_summary.csv', list(rows(P1/'P1_group_summary.csv')[0]), None))

out = '\n\n'.join(S) + '\n'
(HERE/'Paper1_supplementary.md').write_text(out, encoding='utf-8')
subprocess.run(['pandoc', 'Paper1_supplementary.md', '-f', 'markdown', '-t', 'docx', '-o', 'Paper1_supplementary.docx',
                '--resource-path', str(HERE)], cwd=HERE, check=True)
print('supplementary built', len(out.split()), 'words')
