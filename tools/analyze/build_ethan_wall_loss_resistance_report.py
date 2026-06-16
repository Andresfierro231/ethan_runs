#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure

REPORT_SLUG = '2026-06-05_ethan_wall_loss_resistance_coupling'
REPORT_ROOT = WORKSPACE_ROOT / 'reports' / REPORT_SLUG
VALIDATION_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_direct_validation' / 'ethan_direct_validation_metrics.csv'
METADATA_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_case_metadata_index' / 'ethan_case_metadata_index.csv'
SECTION_PRESSURE_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_section_transport_package' / 'section_pressure_drops.csv'
REP_SECTION_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_section_transport_package' / 'representative_section_summary.csv'
STEADY_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_essential_steadiness_audit' / 'salt_case_essential_steadiness.csv'

SECTION_ORDER = ['lower_leg', 'right_leg', 'upper_leg', 'left_leg', 'test_section_branch']


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def f(value: str) -> float:
    return float(value) if value not in ('', None) else float('nan')


def build_tables() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    validation_rows = [row for row in load_csv_rows(VALIDATION_CSV) if row['exp_case_name'].startswith('Salt')]
    metadata_rows = {row['source_id']: row for row in load_csv_rows(METADATA_CSV)}
    steady_rows = {row['source_id']: row for row in load_csv_rows(STEADY_CSV)}
    pressure_rows = load_csv_rows(SECTION_PRESSURE_CSV)

    assumption_rows = []
    coupling_rows = []
    pressure_wide: dict[str, dict[str, str]] = {}

    for row in validation_rows:
        source_id = row['source_id']
        meta = metadata_rows[source_id]
        steady = steady_rows.get(source_id, {})
        assumption_rows.append({
            'source_id': source_id,
            'case_id': meta.get('case_id', ''),
            'variant_label': meta.get('variant_label', ''),
            'cp_model_summary': meta.get('cp_model_summary', ''),
            'mu_coeff_summary': meta.get('mu_coeff_summary', ''),
            'three_d_loss_bc_summary': meta.get('three_d_loss_bc_summary', ''),
            'cooler_h_W_m2K': meta.get('cooler_h_W_m2K', ''),
            'three_d_outer_insulation_thickness_in': meta.get('three_d_outer_insulation_thickness_in', ''),
            'friction_treatment_summary': meta.get('friction_treatment_summary', ''),
        })
        coupling_rows.append({
            'source_id': source_id,
            'exp_case_name': row['exp_case_name'],
            'variant_label': meta.get('variant_label', ''),
            'essential_steadiness_class': steady.get('essential_steadiness_class', ''),
            'exp_all_temp_rmse_k': row['exp_all_temp_rmse_k'],
            'exp_mdot_abs_error_pct': row['exp_mdot_abs_error_pct'],
            'exp_q_external_loss_abs_error_pct': row['exp_q_external_loss_abs_error_pct'],
            'sim_ambient_proxy_w': row['sim_ambient_proxy_w'],
            'sim_cooling_branch_total_removal_w': row['sim_cooling_branch_total_removal_w'],
            'sim_section_test_section_net_q_w': row['sim_section_test_section_net_q_w'],
        })
        pressure_wide[source_id] = {
            'source_id': source_id,
            'exp_case_name': row['exp_case_name'],
            'variant_label': meta.get('variant_label', ''),
        }
    for row in pressure_rows:
        source_id = row['source_id']
        if source_id not in pressure_wide:
            continue
        pressure_wide[source_id][f"{row['section_name']}_abs_delta_p_rgh_pa"] = row['abs_delta_p_rgh_pa']
    hydraulic_rows = list(pressure_wide.values())
    hydraulic_rows.sort(key=lambda item: item['source_id'])
    return assumption_rows, coupling_rows, hydraulic_rows


def build_scatter(coupling_rows: list[dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 6.2))
    for row in coupling_rows:
        x = f(row['exp_q_external_loss_abs_error_pct'])
        y = f(row['exp_mdot_abs_error_pct'])
        color = '#1f77b4' if row['variant_label'] == 'jin' else '#e07a1f' if row['variant_label'] == 'kirst' else '#2a9d4b'
        ax.scatter(x, y, s=90, color=color)
        label = row['source_id'].replace('viscosity_screening_', '').replace('_coarse_mesh', '').replace('val_', '')
        ax.annotate(label, (x, y), xytext=(6, 5), textcoords='offset points', fontsize=8)
    ax.set_xlabel('Ambient-loss proxy absolute error [%]')
    ax.set_ylabel('Mass-flow absolute error [%]')
    ax.set_title('Salt cases: mass-flow mismatch versus ambient-loss mismatch')
    ax.grid(True, linestyle='--', alpha=0.3)
    fig.tight_layout()
    save_matplotlib_figure(fig, REPORT_ROOT, 'salt_mdot_vs_ambient_loss_error', dpi=220)
    plt.close(fig)


def build_heatmap(hydraulic_rows: list[dict[str, str]]) -> None:
    labels = []
    matrix = []
    for row in hydraulic_rows:
        labels.append(row['source_id'].replace('viscosity_screening_', '').replace('_coarse_mesh', '').replace('val_', ''))
        matrix.append([f(row.get(f'{section}_abs_delta_p_rgh_pa', 'nan')) for section in SECTION_ORDER])
    arr = np.array(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(10.6, 5.8))
    im = ax.imshow(arr, aspect='auto', cmap='YlOrRd')
    ax.set_xticks(range(len(SECTION_ORDER)))
    ax.set_xticklabels([name.replace('_', '\n') for name in SECTION_ORDER])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_title('Section |Δp_rgh| ranking across salt cases [Pa]')
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, f'{arr[i, j]:.1f}', ha='center', va='center', fontsize=7)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('|Δp_rgh| [Pa]')
    fig.tight_layout()
    save_matplotlib_figure(fig, REPORT_ROOT, 'salt_section_pressure_drop_heatmap', dpi=220)
    plt.close(fig)


def build_hypothesis_rows(coupling_rows: list[dict[str, str]], hydraulic_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            'hypothesis': 'Shared wall-loss boundary underpredicts ambient exchange',
            'evidence_for': 'Ambient-loss proxy error stays clustered near 17-21% for Salt 2-4 and near 27% for Salt 1 while Jin/Kirst changes do not remove the bias.',
            'evidence_against': 'Ambient-loss error alone does not explain the large mdot spread across Jin/Kirst and Salt 1-4.',
            'low_cost_test': 'Recompute report metrics after a wall-loss sensitivity centered on Salt 2 validation and Salt 4 Jin.',
            'worth_doing_now': 'yes',
        },
        {
            'hypothesis': 'Hydraulic resistance is too high in the upper-left loop path',
            'evidence_for': 'Upper-leg |Δp_rgh| dominates every salt row, and Jin usually lowers upper-leg/left-leg loss together with better mdot agreement.',
            'evidence_against': 'Pressure data are latest-time only in the current package; full transient pressure-history confirmation is still pending.',
            'low_cost_test': 'Build transient p_rgh history extraction for the upper leg, left leg, and test-section branch before changing geometry.',
            'worth_doing_now': 'yes',
        },
        {
            'hypothesis': 'Constant Cp is not the leading-order cause of the mdot mismatch',
            'evidence_for': 'All salt rows share effectively constant Cp=1423.47, yet mdot changes materially between Jin and Kirst while ambient-loss bias remains clustered.',
            'evidence_against': 'Cp still affects buoyancy through enthalpy-temperature conversion and should not be ruled out permanently without a focused sensitivity.',
            'low_cost_test': 'Defer Cp sensitivity until after wall-loss and resistance-coupling checks, because those levers have stronger evidence today.',
            'worth_doing_now': 'no',
        },
        {
            'hypothesis': 'Salt 1 is a coupled low-power regime problem, not just missing runtime',
            'evidence_for': 'Salt 1 remains about 4% off in net heat balance even when flat in time, and both temperature and mdot errors are much worse than Salt 2-4.',
            'evidence_against': 'The Salt 1 continuations have not yet been extended successfully after the new runtime path was introduced.',
            'low_cost_test': 'Continue both Salt 1 Jin and Salt 1 Kirst with the repaired bootstrap before proposing lower-power wall-loss or cooler-h sensitivities.',
            'worth_doing_now': 'yes',
        },
    ]


def build_readme(coupling_rows: list[dict[str, str]], hydraulic_rows: list[dict[str, str]], hypothesis_rows: list[dict[str, str]]) -> str:
    lines = [
        '# Ethan Wall-Loss And Resistance Coupling',
        '',
        f'Generated: `{iso_timestamp()}`',
        '',
        '## What the plots mean',
        '',
        '- `figures/png/salt_mdot_vs_ambient_loss_error.png`: each point is one salt case. The x-axis is the CFD absolute error against the Ethan-linked ambient-loss proxy. The y-axis is the CFD absolute mass-flow error. If wall-loss were the only major problem, cases would move mostly left-right with little change in mdot. They do not.',
        '- `figures/png/salt_section_pressure_drop_heatmap.png`: latest-time patch-averaged `|Δp_rgh|` by major branch. Larger values indicate where the hydrostatic-pressure-reduced loop resistance is concentrated. The absolute columns should be used for ranking.',
        '',
        '## Scientific interpretation',
        '',
        '- The salt cases do not support a single-cause story in which wall loss alone explains the mdot shortfall.',
        '- Salt 2-4 cluster fairly tightly on ambient-loss proxy error, but mdot still changes materially between Jin and Kirst. That is stronger evidence for a coupled resistance problem than for a pure wall-loss problem.',
        '- The upper leg is the dominant pressure-loss section in every salt row. The left leg is consistently the next major branch loss. The test-section branch is much smaller in absolute loss, but it still changes enough between Jin and Kirst to affect loop balance.',
        '- Salt 1 is different from Salt 2-4. It is not just less converged. It sits on a much higher residual floor and much worse validation error simultaneously, which means runtime extension alone may not fully rescue it.',
        '',
        '## How to bring the mass-flow error down',
        '',
        '- First priority: fix the continuation/bootstrap path and extend Salt 4 Jin and Salt 1 so the pressure and heat-balance tails are no longer ambiguous.',
        '- Second priority: build transient `p_rgh` histories for the upper leg, left leg, and test-section branch. That is the cheapest way to confirm whether the current hydraulic ranking is stable in time.',
        '- Third priority: run a wall-loss sensitivity on the current representative Salt 2 validation row and Salt 4 Jin. Use that to test whether improved ambient exchange reduces temperature bias without worsening mdot further.',
        '- Do not prioritize insulation thickening first. The existing data already show a shared ambient-loss bias, but the mdot spread is too variant-sensitive for insulation thickness to be the first explanatory lever.',
        '- Cp sensitivity is lower priority than wall-loss and resistance-coupling checks because all salt rows currently share the same effectively constant Cp model.',
        '',
        '## Recommended clarification work',
        '',
    ]
    for row in hypothesis_rows:
        lines.append(f"- `{row['hypothesis']}`: {row['low_cost_test']} Worth doing now: `{row['worth_doing_now']}`.")
    lines.extend([
        '',
        '## Output files',
        '',
        '- `salt_model_assumption_summary.csv`: current 3D property and wall-loss assumption table.',
        '- `salt_coupling_summary.csv`: validation and coupling summary for all salt rows.',
        '- `salt_hydraulic_summary.csv`: section-wise pressure-loss summary in wide format.',
        '- `hypothesis_matrix.csv`: modeling-hypothesis and next-test matrix.',
        '',
    ])
    return '\n'.join(lines) + '\n'


def main() -> int:
    ensure_dir(REPORT_ROOT)
    assumption_rows, coupling_rows, hydraulic_rows = build_tables()
    hypothesis_rows = build_hypothesis_rows(coupling_rows, hydraulic_rows)
    csv_dump(REPORT_ROOT / 'salt_model_assumption_summary.csv', list(assumption_rows[0].keys()), assumption_rows)
    csv_dump(REPORT_ROOT / 'salt_coupling_summary.csv', list(coupling_rows[0].keys()), coupling_rows)
    csv_dump(REPORT_ROOT / 'salt_hydraulic_summary.csv', list(hydraulic_rows[0].keys()), hydraulic_rows)
    csv_dump(REPORT_ROOT / 'hypothesis_matrix.csv', list(hypothesis_rows[0].keys()), hypothesis_rows)
    build_scatter(coupling_rows)
    build_heatmap(hydraulic_rows)
    json_dump(REPORT_ROOT / 'summary.json', {
        'generated_at': iso_timestamp(),
        'coupling_rows': coupling_rows,
        'hypothesis_rows': hypothesis_rows,
    })
    (REPORT_ROOT / 'README.md').write_text(build_readme(coupling_rows, hydraulic_rows, hypothesis_rows), encoding='utf-8')
    print(json.dumps({'report_root': str(REPORT_ROOT), 'salt_case_count': len(coupling_rows)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
