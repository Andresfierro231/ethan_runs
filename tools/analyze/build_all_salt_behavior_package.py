#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, ensure_dir, load_case_metadata, parse_scalar_series  # noqa: E402


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


s2 = load_module('build_salt2_behavior_package', ROOT / 'tools' / 'analyze' / 'build_salt2_behavior_package.py')
rep = load_module('build_ethan_report_package', ROOT / 'tools' / 'analyze' / 'build_ethan_report_package.py')

OUTPUT_DIR = WORKSPACE_ROOT / 'reports' / '2026-06-04_all_salt_behavior_package'
WINDOW_COUNT = 50
HEAT_KEYS = [
    'ambient_proxy_w',
    'ambient_noncooling_proxy_w',
    'cooling_branch_total_removal_w',
    'cooling_branch_excess_w',
    'net_total_q_w',
    'section_downcomer_net_q_w',
    'section_heater_net_q_w',
    'section_upcomer_net_q_w',
    'section_test_section_net_q_w',
    'section_cooling_branch_net_q_w',
    'section_upper_transport_net_q_w',
    'section_lower_transport_net_q_w',
    'section_junctions_net_q_w',
    'section_other_net_q_w',
]


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def csv_dump(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_total_q_series(source_root: Path) -> tuple[np.ndarray, np.ndarray]:
    rows = parse_scalar_series(source_root / 'postProcessing' / 'total_Q.dat')
    if not rows:
        return np.array([]), np.array([])
    return np.array([float(row['time']) for row in rows]), np.array([float(row['value']) for row in rows])


def choose_representatives(case_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in case_rows:
        grouped[str(row['base_case_id'])].append(row)
    selections: list[dict[str, object]] = []
    for base_case_id in sorted(grouped):
        rows = grouped[base_case_id]
        by_source = {str(row['source_id']): row for row in rows}
        usable = [row for row in rows if str(row['usable_for_steady_state_now']) in {'yes', 'yes_with_caveat'}]
        usable_sorted = sorted(
            usable,
            key=lambda row: (
                0 if str(row['usable_for_steady_state_now']) == 'yes' else 1,
                float(row['exp_all_temp_rmse_k']) if row['exp_all_temp_rmse_k'] not in ('', None) else 1e9,
                float(row['exp_mdot_abs_error_pct']) if row['exp_mdot_abs_error_pct'] not in ('', None) else 1e9,
            ),
        )
        current_rep = usable_sorted[0]['source_id'] if usable_sorted else ''
        manuscript_rep = current_rep
        continuation_candidate = ''
        rationale = ''
        if base_case_id == 'salt_test_1':
            current_rep = ''
            manuscript_rep = ''
            continuation_candidate = 'viscosity_screening_salt_test_1_jin_coarse_mesh' if 'viscosity_screening_salt_test_1_jin_coarse_mesh' in by_source else ''
            rationale = 'No current Salt 1 row is clean enough for a steady-state representative; Jin is the preferred continuation candidate because it avoids the false-convergence interpretation and has slightly better mass-flow error than Kirst.'
        elif base_case_id == 'salt_test_2':
            manuscript_rep = 'val_salt_test_2_coarse_mesh_laminar' if 'val_salt_test_2_coarse_mesh_laminar' in by_source else current_rep
            continuation_candidate = manuscript_rep
            rationale = 'Use the native val_salt_test_2 continuation as the primary representative; retain staged Jin and Kirst as sensitivity comparisons for viscosity and setup changes.'
        elif base_case_id == 'salt_test_3':
            manuscript_rep = 'viscosity_screening_salt_test_3_jin_coarse_mesh' if 'viscosity_screening_salt_test_3_jin_coarse_mesh' in by_source else current_rep
            rationale = 'Salt 3 Jin is the current preferred representative because it remains practically steady and has the better mass-flow agreement.'
        elif base_case_id == 'salt_test_4':
            current_rep = 'viscosity_screening_salt_test_4_kirst_coarse_mesh' if 'viscosity_screening_salt_test_4_kirst_coarse_mesh' in by_source else current_rep
            manuscript_rep = 'viscosity_screening_salt_test_4_jin_coarse_mesh' if 'viscosity_screening_salt_test_4_jin_coarse_mesh' in by_source else current_rep
            continuation_candidate = manuscript_rep
            rationale = 'Salt 4 Kirst is the steadier current reference, but Salt 4 Jin is the chosen manuscript sensitivity representative and has been extended in the background to improve its steady-state credibility.'
        selections.append({
            'base_case_id': base_case_id,
            'current_steady_representative': current_rep,
            'primary_manuscript_representative': manuscript_rep,
            'continuation_candidate': continuation_candidate,
            'sensitivity_rows': '; '.join(sorted(by_source)),
            'selection_rationale': rationale,
        })
    return selections


def build_case_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    metadata_rows = {row['source_id']: row for row in load_csv_rows(WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_case_metadata_index' / 'ethan_case_metadata_index.csv')}
    validation_rows = {row['source_id']: row for row in load_csv_rows(WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_direct_validation' / 'ethan_direct_validation_metrics.csv')}
    decision_rows = {row['source_id']: row for row in load_csv_rows(WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_runtime_and_hypothesis_matrix' / 'continuation_decisions.csv')}
    steadiness_rows = {row['source_id']: row for row in load_csv_rows(WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_essential_steadiness_audit' / 'salt_case_essential_steadiness.csv')}

    salt_ids = [sid for sid, row in metadata_rows.items() if 'salt' in sid]
    case_status_rows: list[dict[str, object]] = []
    steady_rows: list[dict[str, object]] = []
    ambient_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []

    for source_id in salt_ids:
        meta = metadata_rows[source_id]
        validation = validation_rows.get(source_id, {})
        decision = decision_rows.get(source_id, {})
        steady = steadiness_rows.get(source_id, {})
        runtime_root = Path(meta.get('active_runtime_root') or meta.get('source_root'))
        source_root = Path(meta.get('source_root') or runtime_root)
        metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root) or {}

        mdot_t, mdot_v = s2.parse_mdot_mean_series(runtime_root)
        tp_t, tp_series, tp_mean = s2.parse_temperature_probe_series(runtime_root)
        heat_rows = s2.parse_wall_heatflux_section_series(runtime_root, metadata)
        heat_t, heat_series = s2.rows_to_series(heat_rows, HEAT_KEYS)
        total_q_t, total_q_v = parse_total_q_series(runtime_root)

        metric_map = {
            'mdot_mean_abs_kg_s': (mdot_t, mdot_v),
            'tp_mean_K': (tp_t, tp_mean),
            'total_q_net_w': (total_q_t, total_q_v),
        }
        metric_map.update({key: (heat_t, values) for key, values in heat_series.items()})
        for metric, (times, values) in metric_map.items():
            steady_rows.append(s2.compute_last_window_stats(source_id, metric, times, values, WINDOW_COUNT))

        case_status_rows.append({
            'source_id': source_id,
            'case_id': meta.get('case_id', ''),
            'base_case_id': meta.get('base_case_id', ''),
            'variant_label': meta.get('variant_label', ''),
            'run_status': meta.get('run_status', ''),
            'convergence_reached': meta.get('convergence_reached', ''),
            'essential_steadiness_class': steady.get('essential_steadiness_class', ''),
            'usable_for_steady_state_now': steady.get('usable_for_steady_state_now', ''),
            'decision': decision.get('decision', ''),
            'final_time_s': meta.get('final_time', ''),
            'mdot_mean_abs_kg_s': meta.get('mdot_mean_abs_kg_s', ''),
            'final_total_wall_heat_abs_w': meta.get('final_total_wall_heat_abs_w', ''),
            'sim_total_wall_q_net_w': meta.get('sim_total_wall_q_net_w', ''),
            'sim_ambient_proxy_w': meta.get('sim_ambient_proxy_w', ''),
            'exp_all_temp_rmse_k': validation.get('exp_all_temp_rmse_k', ''),
            'exp_mdot_abs_error_pct': validation.get('exp_mdot_abs_error_pct', ''),
            'exp_q_external_loss_abs_error_pct': validation.get('exp_q_external_loss_abs_error_pct', ''),
            'reason': steady.get('reason', ''),
        })

        ambient_rows.append({
            'source_id': source_id,
            'base_case_id': meta.get('base_case_id', ''),
            'variant_label': meta.get('variant_label', ''),
            'run_status': meta.get('run_status', ''),
            'essential_steadiness_class': steady.get('essential_steadiness_class', ''),
            'T_init_K': meta.get('T_init_K', ''),
            'cooler_h_W_m2K': meta.get('cooler_h_W_m2K', ''),
            'outer_insulation_in': meta.get('three_d_outer_insulation_thickness_in', ''),
            'mu_coeff_summary': meta.get('mu_coeff_summary', ''),
            'sim_ambient_proxy_w': meta.get('sim_ambient_proxy_w', ''),
            'sim_ambient_noncooling_proxy_w': validation.get('sim_ambient_noncooling_proxy_w', ''),
            'sim_cooling_branch_total_removal_w': validation.get('sim_cooling_branch_total_removal_w', ''),
            'sim_cooling_branch_excess_w': validation.get('sim_cooling_branch_excess_over_operating_cooling_w', ''),
            'exp_q_external_loss_reference_w': validation.get('exp_q_external_loss_reference_w', ''),
            'exp_q_external_loss_abs_error_pct': validation.get('exp_q_external_loss_abs_error_pct', ''),
            'exp_mdot_abs_error_pct': validation.get('exp_mdot_abs_error_pct', ''),
            'exp_all_temp_rmse_k': validation.get('exp_all_temp_rmse_k', ''),
            'sim_section_downcomer_net_q_w': validation.get('sim_section_downcomer_net_q_w', ''),
            'sim_section_heater_net_q_w': validation.get('sim_section_heater_net_q_w', ''),
            'sim_section_upcomer_net_q_w': validation.get('sim_section_upcomer_net_q_w', ''),
            'sim_section_test_section_net_q_w': validation.get('sim_section_test_section_net_q_w', ''),
            'sim_section_cooling_branch_net_q_w': validation.get('sim_section_cooling_branch_net_q_w', ''),
            'loss_setup_summary': meta.get('loss_setup_summary', ''),
            'ambient_error_hypothesis': '',
        })

    grouped = defaultdict(dict)
    for row in ambient_rows:
        grouped[str(row['base_case_id'])][str(row['variant_label'] or 'base')] = row
    for base_case_id, group in sorted(grouped.items()):
        jin = group.get('jin')
        kirst = group.get('kirst')
        if jin and kirst:
            def f(row, key):
                try:
                    return float(row[key])
                except Exception:
                    return None
            comparison_rows.append({
                'base_case_id': base_case_id,
                'jin_source_id': jin['source_id'],
                'kirst_source_id': kirst['source_id'],
                'delta_sim_ambient_proxy_w_jin_minus_kirst': '' if f(jin, 'sim_ambient_proxy_w') is None or f(kirst, 'sim_ambient_proxy_w') is None else f(jin, 'sim_ambient_proxy_w') - f(kirst, 'sim_ambient_proxy_w'),
                'delta_exp_q_external_loss_abs_error_pct_jin_minus_kirst': '' if f(jin, 'exp_q_external_loss_abs_error_pct') is None or f(kirst, 'exp_q_external_loss_abs_error_pct') is None else f(jin, 'exp_q_external_loss_abs_error_pct') - f(kirst, 'exp_q_external_loss_abs_error_pct'),
                'delta_exp_mdot_abs_error_pct_jin_minus_kirst': '' if f(jin, 'exp_mdot_abs_error_pct') is None or f(kirst, 'exp_mdot_abs_error_pct') is None else f(jin, 'exp_mdot_abs_error_pct') - f(kirst, 'exp_mdot_abs_error_pct'),
                'delta_exp_all_temp_rmse_k_jin_minus_kirst': '' if f(jin, 'exp_all_temp_rmse_k') is None or f(kirst, 'exp_all_temp_rmse_k') is None else f(jin, 'exp_all_temp_rmse_k') - f(kirst, 'exp_all_temp_rmse_k'),
                'interpretation': 'Jin-vs-Kirst differences alter mass-flow agreement more strongly than ambient-loss agreement.'
            })

    # add hypothesis text after pair comparison context exists
    for row in ambient_rows:
        base_case_id = str(row['base_case_id'])
        if base_case_id == 'salt_test_2':
            row['ambient_error_hypothesis'] = 'Salt 2 ambient proxy stays near 187-188 W across val, Jin, and Kirst despite changes in insulation thickness, cooler h, and viscosity. That points to a shared external-loss model bias rather than a viscosity-only or insulation-only explanation.'
        elif base_case_id == 'salt_test_1':
            row['ambient_error_hypothesis'] = 'Salt 1 ambient-loss interpretation is confounded by the elevated net heat-balance residual floor; more runtime is justified before using it to calibrate wall-loss assumptions.'
        else:
            row['ambient_error_hypothesis'] = 'Ambient-loss underprediction remains systematic but moderate; likely sources include shared external h/Tsur calibration, emissivity/radiation treatment, or unmodeled parasitic conduction/support losses.'

    return case_status_rows, steady_rows, ambient_rows, comparison_rows


def write_readme(case_status_rows: list[dict[str, object]], ambient_rows: list[dict[str, object]], selections: list[dict[str, object]]) -> None:
    by_source = {row['source_id']: row for row in case_status_rows}
    lines = [
        '# All-Salt Behavior Package',
        '',
        'This package extends the Salt 2 behavior work to the full salt campaign and separates coded convergence from practical usability.',
        '',
        '## Main findings',
        '',
        '- Salt Test 2, 3, and most of Salt Test 4 are practically usable now for steady-state analysis, even where the coded convergence monitor never fired.',
        '- Salt Test 1 remains the main exception: both current rows are flat in the tail, but they sit on a materially larger net heat-balance residual floor and should not be treated as clean steady-state representatives.',
        '- Jin versus Kirst changes mass-flow agreement more strongly than it changes the derived ambient-loss proxy. That is evidence that the remaining ambient-loss error is dominated by a shared wall-loss model bias rather than by the viscosity branch alone.',
        '- Salt 2 is the strongest current validation case. The native val_salt_test_2 continuation remains the primary manuscript representative for Salt 2.',
        '- Salt 4 Jin has now been staged and resubmitted for a capped 72-hour continuation to improve the steady-state sensitivity evidence for the user-chosen representative branch.',
        '',
        '## Representative-case policy',
        '',
    ]
    for row in selections:
        lines.append(f"- `{row['base_case_id']}`: steady representative `{row['current_steady_representative'] or 'none yet'}`, manuscript representative `{row['primary_manuscript_representative'] or 'none yet'}`, continuation candidate `{row['continuation_candidate'] or 'none'}`. {row['selection_rationale']}")
    lines.extend([
        '',
        '## Ambient-loss interpretation',
        '',
        '- The current 3D ambient-loss mismatch is systematic but not catastrophic. Most use-ready salt rows underpredict the Ethan-linked ambient-loss proxy by roughly 17--21\%.',
        '- The Salt 2 triad is especially informative: the val row, staged Jin row, and staged Kirst row all land near the same derived ambient-loss magnitude despite differing in insulation thickness, cooler h, runtime, and viscosity branch. That strongly suggests a shared external wall-loss modeling bias.',
        '- The shared bias could come from one or more of the following: external film coefficient calibration, external ambient or surrounding-surface temperature assumptions, emissivity/radiation treatment details, or parasitic conduction paths not represented in the current wall-loss boundary partition.',
        '',
        '## Source files',
        '',
        '- `all_salt_case_status.csv`: cross-case state, usability, and validation summary.',
        '- `all_salt_steady_window_summary.csv`: last-window statistics and drift metrics for mdot, TP mean, total Q, and section heat terms.',
        '- `ambient_loss_audit.csv`: case-by-case ambient-loss accounting and hypothesis notes.',
        '- `jin_vs_kirst_summary.csv`: direct paired comparisons for tests with both viscosity branches.',
        '- `representative_case_selection.csv`: explicit selection rationale for manuscript-facing representative rows.',
    ])
    (OUTPUT_DIR / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    ensure_dir(OUTPUT_DIR)
    case_status_rows, steady_rows, ambient_rows, comparison_rows = build_case_rows()
    selections = choose_representatives(case_status_rows)

    csv_dump(OUTPUT_DIR / 'all_salt_case_status.csv', list(case_status_rows[0].keys()), case_status_rows)
    csv_dump(OUTPUT_DIR / 'all_salt_steady_window_summary.csv', list(steady_rows[0].keys()), steady_rows)
    csv_dump(OUTPUT_DIR / 'ambient_loss_audit.csv', list(ambient_rows[0].keys()), ambient_rows)
    csv_dump(OUTPUT_DIR / 'jin_vs_kirst_summary.csv', list(comparison_rows[0].keys()), comparison_rows)
    csv_dump(OUTPUT_DIR / 'representative_case_selection.csv', list(selections[0].keys()), selections)

    (OUTPUT_DIR / 'summary.json').write_text(json.dumps({
        'case_status_rows': case_status_rows,
        'representative_case_selection': selections,
    }, indent=2) + '\n', encoding='utf-8')
    write_readme(case_status_rows, ambient_rows, selections)
    print(json.dumps({'output_dir': str(OUTPUT_DIR), 'case_count': len(case_status_rows)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
