#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, parse_probe_series, parse_scalar_series, safe_float, save_matplotlib_figure

REPORT_SLUG = '2026-06-05_ethan_convergence_and_salt1_campaign'
REPORT_ROOT = WORKSPACE_ROOT / 'reports' / REPORT_SLUG
VALIDATION_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_direct_validation' / 'ethan_direct_validation_metrics.csv'
METADATA_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_case_metadata_index' / 'ethan_case_metadata_index.csv'
SALT_STEADY_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_essential_steadiness_audit' / 'salt_case_essential_steadiness.csv'
WINDOW_COUNT = 50

REP_SALT = {
    'Salt 1': ('viscosity_screening_salt_test_1_kirst_coarse_mesh', 'Reached coded convergence and is the strongest documented Salt 1 restart candidate, but still not steady enough.'),
    'Salt 2': ('val_salt_test_2_coarse_mesh_laminar', 'Current manuscript representative and active continuation target.'),
    'Salt 3': ('viscosity_screening_salt_test_3_jin_coarse_mesh', 'Best current Salt 3 mdot agreement with practical steadiness.'),
    'Salt 4': ('viscosity_screening_salt_test_4_jin_coarse_mesh', 'User-priority case; practically usable but still the most borderline of Salt 2-4.'),
}
WATER_CASES = ['Water 1', 'Water 2', 'Water 3', 'Water 4']


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def pick_case_root(meta: dict[str, str]) -> Path:
    active = meta.get('active_runtime_root', '')
    source = meta.get('source_root', '')
    return Path(active or source)


def parse_mdot_summary(case_root: Path) -> tuple[float | None, float | None]:
    mdot_paths = sorted((case_root / 'postProcessing').glob('mdot_*/0/surfaceFieldValue.dat'))
    finals = []
    starts = []
    for path in mdot_paths:
        rows = parse_scalar_series(path)
        if not rows:
            continue
        finals.append(abs(rows[-1]['value']))
        start_row = rows[-WINDOW_COUNT] if len(rows) >= WINDOW_COUNT else rows[0]
        starts.append(abs(start_row['value']))
    if not finals:
        return None, None
    final_mean = sum(finals) / len(finals)
    start_mean = sum(starts) / len(starts)
    drift_pct = abs(final_mean - start_mean) / final_mean * 100.0 if final_mean else None
    return final_mean, drift_pct


def parse_total_q_summary(case_root: Path) -> tuple[float | None, float | None]:
    rows = parse_scalar_series(case_root / 'postProcessing' / 'total_Q.dat')
    if not rows:
        return None, None
    final_abs = abs(rows[-1]['value'])
    return rows[-1]['value'], final_abs


def probe_drift(case_root: Path) -> float | None:
    candidates = [
        case_root / 'postProcessing' / 'temperature_probes' / '0' / 'T',
        case_root / 'postProcessing' / 'wall_temperature_probes' / '0' / 'T',
    ]
    drifts = []
    for path in candidates:
        payload = parse_probe_series(path)
        rows = payload['rows']
        if not rows:
            continue
        start_row = rows[-WINDOW_COUNT] if len(rows) >= WINDOW_COUNT else rows[0]
        final_row = rows[-1]
        diffs = [abs(float(a) - float(b)) for a, b in zip(final_row['values'], start_row['values'])]
        if diffs:
            drifts.append(max(diffs))
    return max(drifts) if drifts else None


def classify_case(net_q_pct: float | None, mdot_drift_pct: float | None, probe_drift_k: float | None) -> tuple[str, str]:
    if net_q_pct is None:
        return 'insufficient_runtime_evidence', 'Missing total_Q history prevents a convergence claim.'
    if net_q_pct > 1.0:
        return 'not_steady_enough', 'Net heat-balance residual remains above 1% of heater power.'
    if (mdot_drift_pct is not None and mdot_drift_pct > 0.25) or (probe_drift_k is not None and probe_drift_k > 0.10):
        return 'borderline_but_usable', 'Residual is small, but late-window drift is still noticeable.'
    return 'essentially_steady', 'Residual and late-window drifts are small enough for practical steady-state use.'


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validation_rows_by_source = {row['source_id']: row for row in load_csv_rows(VALIDATION_CSV)}
    metadata_rows = {row['source_id']: row for row in load_csv_rows(METADATA_CSV)}
    salt_steady_rows = {row['source_id']: row for row in load_csv_rows(SALT_STEADY_CSV)}
    summary_rows = []

    for case_name, (source_id, rationale) in REP_SALT.items():
        v = validation_rows_by_source[source_id]
        s = salt_steady_rows[source_id]
        summary_rows.append({
            'study_case': case_name,
            'fluid': 'salt',
            'representative_source_id': source_id,
            'selection_rationale': rationale,
            'run_status': v['run_status'],
            'convergence_reached': v['convergence_reached'],
            'final_time_s': v['final_time'],
            'final_net_total_q_pct_of_heater': s['final_net_total_q_pct_of_heater'],
            'late_window_mdot_drift_pct': s['late_window_mdot_drift_pct'],
            'late_window_probe_drift_k': s['late_window_probe_drift_k'],
            'steady_state_class': s['essential_steadiness_class'],
            'exp_all_temp_rmse_k': v['exp_all_temp_rmse_k'],
            'exp_mdot_abs_error_pct': v['exp_mdot_abs_error_pct'],
            'exp_q_external_loss_abs_error_pct': v['exp_q_external_loss_abs_error_pct'],
            'determination': s['reason'],
        })

    for index, case_name in enumerate(WATER_CASES, start=1):
        source_id = f'val_water_test_{index}_coarse_mesh_laminar'
        v = validation_rows_by_source[source_id]
        meta = metadata_rows[source_id]
        case_root = pick_case_root(meta)
        _, mdot_drift_pct = parse_mdot_summary(case_root)
        _, total_q_abs = parse_total_q_summary(case_root)
        heater_power = safe_float(meta.get('heater_power_W'))
        net_q_pct = (total_q_abs / heater_power * 100.0) if total_q_abs is not None and heater_power else None
        probe_drift_k = probe_drift(case_root)
        steady_class, determination = classify_case(net_q_pct, mdot_drift_pct, probe_drift_k)
        summary_rows.append({
            'study_case': case_name,
            'fluid': 'water',
            'representative_source_id': source_id,
            'selection_rationale': 'Direct laminar validation row for the water test.',
            'run_status': v['run_status'],
            'convergence_reached': v['convergence_reached'],
            'final_time_s': v['final_time'],
            'final_net_total_q_pct_of_heater': f'{net_q_pct:.6f}' if net_q_pct is not None else '',
            'late_window_mdot_drift_pct': f'{mdot_drift_pct:.6f}' if mdot_drift_pct is not None else '',
            'late_window_probe_drift_k': f'{probe_drift_k:.6f}' if probe_drift_k is not None else '',
            'steady_state_class': steady_class,
            'exp_all_temp_rmse_k': v['exp_all_temp_rmse_k'],
            'exp_mdot_abs_error_pct': v['exp_mdot_abs_error_pct'],
            'exp_q_external_loss_abs_error_pct': v['exp_q_external_loss_abs_error_pct'],
            'determination': determination,
        })

    hypothesis_rows = [
        {
            'hypothesis': 'Salt 1 primarily needs a longer continuation with the repaired MPI bootstrap.',
            'why_it_matters': 'Both Salt 1 rows are flat in time, but neither has been extended under the repaired post-June-2 continuation path.',
            'test_to_run': 'Continue Salt 1 Jin from 3229 s and Salt 1 Kirst from 3279.163522013 s with the corrected OpenFOAM bootstrap.',
            'expected_signal': 'If the 4% net-Q floor is mostly a runtime issue, the residual should fall materially without a large setup change.',
        },
        {
            'hypothesis': 'Salt 1 is a low-power modeling problem, not only a runtime problem.',
            'why_it_matters': 'Salt 1 remains much worse than Salt 2-4 on temperature, mdot, and ambient-loss metrics simultaneously.',
            'test_to_run': 'Only after the continuation retries finish, test a targeted Salt 1 loss-model or cooler-h sensitivity rather than a blanket property sweep.',
            'expected_signal': 'If the residual floor survives the new continuation, the setup itself is the next lever, not more runtime alone.',
        },
    ]
    return summary_rows, hypothesis_rows


def build_plot(summary_rows: list[dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 6.4))
    for row in summary_rows:
        x = float(row['final_net_total_q_pct_of_heater']) if row['final_net_total_q_pct_of_heater'] else float('nan')
        y = float(row['late_window_mdot_drift_pct']) if row['late_window_mdot_drift_pct'] else float('nan')
        color = '#d77a28' if row['fluid'] == 'salt' else '#1f77b4'
        marker = 's' if row['fluid'] == 'salt' else 'o'
        ax.scatter(x, y, s=90, c=color, marker=marker)
        ax.annotate(row['study_case'], (x, y), xytext=(5, 5), textcoords='offset points', fontsize=8)
    ax.axvline(1.0, color='#555555', linestyle='--', linewidth=1.0, label='1% residual threshold')
    ax.axhline(0.25, color='#888888', linestyle=':', linewidth=1.0, label='0.25% mdot drift threshold')
    ax.set_xlabel('Final |total_Q| as % of heater power')
    ax.set_ylabel('Late-window mdot drift [%]')
    ax.set_title('Eight-case convergence dashboard')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper right')
    fig.tight_layout()
    save_matplotlib_figure(fig, REPORT_ROOT, 'eight_case_convergence_dashboard', dpi=220)
    plt.close(fig)


def build_readme(summary_rows: list[dict[str, str]], hypothesis_rows: list[dict[str, str]]) -> str:
    lines = [
        '# Ethan Eight-Case Convergence And Salt 1 Campaign',
        '',
        f'Generated: `{iso_timestamp()}`',
        '',
        '## Method',
        '',
        '- Salt representatives use the current best-supported row for each physical salt test, not both Jin and Kirst simultaneously, so the report stays at the requested eight study cases.',
        '- Water cases are reclassified with the same practical-steadiness ingredients used for the salt audit: final `|total_Q|` relative to heater power, late-window mdot drift, and late-window probe drift.',
        '- Interpretation rule used here:',
        '  - `essentially_steady`: final `|total_Q|/heater < 1%` and no noticeable late-window drift.',
        '  - `borderline_but_usable`: residual is small, but mdot or probe drift is still noticeable.',
        '  - `not_steady_enough`: residual remains too large for a clean steady-state claim.',
        '',
        '## Eight-case determination',
        '',
    ]
    for row in summary_rows:
        lines.append(f"- `{row['study_case']}` (`{row['representative_source_id']}`): `{row['steady_state_class']}`. {row['determination']}")
    lines.extend([
        '',
        '## Salt 1 targeted campaign hypotheses',
        '',
    ])
    for row in hypothesis_rows:
        lines.append(f"- `{row['hypothesis']}`: {row['test_to_run']} Expected signal: {row['expected_signal']}")
    lines.extend([
        '',
        '## Recommended Salt 1 tries',
        '',
        '- Try 1: Salt 1 Jin continuation retry with the repaired OpenFOAM MPI bootstrap.',
        '- Try 2: Salt 1 Kirst continuation retry with the same repaired bootstrap, because it already reached the coded convergence monitor but still has an unacceptably large residual floor.',
        '',
        '## Output files',
        '',
        '- `eight_case_convergence_summary.csv`: main determination table.',
        '- `salt1_hypothesis_matrix.csv`: Salt 1 targeted hypothesis table.',
        '- `figures/png/eight_case_convergence_dashboard.png`: residual-versus-mdot-drift convergence dashboard.',
        '',
    ])
    return '\n'.join(lines) + '\n'


def main() -> int:
    ensure_dir(REPORT_ROOT)
    summary_rows, hypothesis_rows = build_rows()
    csv_dump(REPORT_ROOT / 'eight_case_convergence_summary.csv', list(summary_rows[0].keys()), summary_rows)
    csv_dump(REPORT_ROOT / 'salt1_hypothesis_matrix.csv', list(hypothesis_rows[0].keys()), hypothesis_rows)
    build_plot(summary_rows)
    json_dump(REPORT_ROOT / 'summary.json', {
        'generated_at': iso_timestamp(),
        'summary_rows': summary_rows,
        'hypothesis_rows': hypothesis_rows,
    })
    (REPORT_ROOT / 'README.md').write_text(build_readme(summary_rows, hypothesis_rows), encoding='utf-8')
    print(json.dumps({'report_root': str(REPORT_ROOT), 'study_case_count': len(summary_rows)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
