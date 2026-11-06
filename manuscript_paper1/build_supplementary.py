"""Builds Paper1_supplementary.md (+docx) from the source CSVs."""
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

def table_from(p, skip_header=False):
    r = rows(p)
    return md(r[0], r[1:])

S = []
S.append('# Supplementary Material — Paper 1\n\n**Draft for supervisor review.** All tables below are generated from the locked v8 outputs (`results/final_v7`) and the Paper 1 coefficient outputs (`results/final_v9/paper1`). Nothing has been re-estimated.\n')

S.append('## Table S1. Included (TNM complete) versus excluded (TNM incomplete) patients\nSource: `F32_supp_S1_included_vs_excluded.csv`; standardised differences from `F65`.\n\n' + table_from(F7/'F32_supp_S1_included_vs_excluded.csv') + '\n\n' + table_from(F7/'F65_included_vs_excluded_characteristics.csv'))

t2 = rows(F7/'investigation/F45_TNM_missing_patterns_step7.csv')
S.append('## Table S2. Missing TNM components among the 26,094 patients meeting criteria\nSource: `investigation/F45_TNM_missing_patterns_step7.csv`; reasons (ND vs blank) in `investigation/F46_TNM_missing_reasons_step7.csv`.\n\n' + md(t2[0], t2[1:]))

S.append('## Table S3. Duplicate-record screen and sensitivity\nSources: `F60`, `F61`.\n\n' + table_from(F7/'F60_duplicate_records_screen.csv') + '\n\n' + table_from(F7/'F61_duplicate_sensitivity.csv'))

S.append('## Table S4. Model without TNM staging and pre-operative-only models\nSources: `F62`, `F14`, `F23`.\n\n' + table_from(F7/'F62_no_TNM_model_supplementary.csv') + '\n\n' + table_from(F7/'F14_preoperative_only_sensitivity.csv') + '\n\n' + table_from(F7/'F23_preoperative_only_selected_structure.csv'))

S.append('## Table S5. Excluded patients: period, centre and outcomes\nSources: `F63`, `F64` (sites and countries), `F66`, `F67`.\n\n' + table_from(F7/'F63_incomplete_TNM_by_operation_year.csv') + '\n\n' + table_from(F7/'F64_incomplete_TNM_clustering_centre_country.csv') + '\n\n' + table_from(F7/'F66_incomplete_TNM_outcomes_by_era.csv') + '\n\n' + table_from(F7/'F67_informative_selection_check_no_TNM_model.csv'))

S.append('## Table S6. Death flags and the 15-year window\nSources: `F12`, `F18b`. Among the 11,594 patients recorded as deceased in the full extract, 3,074 lack an explicit death flag. The analytic cohort contains 6,601 recorded deaths, 6,591 inside the window.\n\n' + table_from(F7/'F12_death_and_last_contact_verification.csv') + '\n\n' + table_from(F7/'F18b_death_flag_rate_by_time_from_operation.csv'))

S.append('## Table S7. Reproduction check against the previously validated analysis\nSource: `F25_reproduction_check_against_v6.csv`.\n\n' + table_from(F7/'F25_reproduction_check_against_v6.csv'))

S.append('## Table S8. Horizon feasibility and group events by horizon\nSources: `feasibility/G01`, `G02`, `G04` (centre-held-out feasibility, not a validation result).\n\n' + table_from(F7/'feasibility/G01_horizon_feasibility_validation.csv') + '\n\n' + table_from(F7/'feasibility/G02_group_events_by_horizon_validation.csv') + '\n\n' + table_from(F7/'feasibility/G04_centre_held_out_feasibility.csv'))

S.append('## Table S9. Reporting checklists\nSee `Paper1_reporting_checklists.md` (STROBE and TRIPOD items mapped to manuscript sections, with open items).')

S.append('## Coefficient outputs\nBaseline survival by stratum (`P1_baseline_survival_by_stratum.csv`) and group summary (`P1_group_summary.csv`) are in `results/final_v9/paper1/`.\n\n' + table_from(P1/'P1_baseline_survival_by_stratum.csv') + '\n\n' + table_from(P1/'P1_group_summary.csv'))

out = '\n\n'.join(S) + '\n'
(HERE/'Paper1_supplementary.md').write_text(out, encoding='utf-8')
subprocess.run(['pandoc','Paper1_supplementary.md','-f','markdown','-t','docx','-o','Paper1_supplementary.docx'], cwd=HERE, check=True)
print('supplementary built', len(out.split()), 'words')
