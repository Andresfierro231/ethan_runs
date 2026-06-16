#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure

REPORT_SLUG = '2026-06-05_ethan_continuation_diagnosis'
REPORT_ROOT = WORKSPACE_ROOT / 'reports' / REPORT_SLUG
METADATA_CSV = WORKSPACE_ROOT / 'reports' / '2026-06-04_ethan_case_metadata_index' / 'ethan_case_metadata_index.csv'

JOBS = [
    {
        'job_id': '3202708',
        'case_label': 'Salt 2 validation continuation',
        'source_id': 'val_salt_test_2_coarse_mesh_laminar',
        'variant_label': 'validation',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt2' / '2026-06-01_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt2' / '2026-06-01_continuation_candidate' / 'slurm-3202708.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt2' / '2026-06-01_continuation_candidate' / 'slurm-3202708.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt2' / '2026-06-01_continuation_candidate' / 'case_stage' / 'val_salt_test_2_coarse_mesh_laminar_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3208600',
        'case_label': 'Salt 4 Jin continuation retry 1',
        'source_id': 'viscosity_screening_salt_test_4_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208600.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208600.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_4_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3208837',
        'case_label': 'Salt 4 Jin continuation retry 2',
        'source_id': 'viscosity_screening_salt_test_4_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208837.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208837.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_4_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3208905',
        'case_label': 'Salt 4 Jin continuation retry 3',
        'source_id': 'viscosity_screening_salt_test_4_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208905.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208905.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_4_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3208956',
        'case_label': 'Salt 1 Jin continuation retry 1',
        'source_id': 'viscosity_screening_salt_test_1_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208956.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3208956.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_1_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },    {
        'job_id': '3210231',
        'case_label': 'Salt 4 Jin continuation retry 4',
        'source_id': 'viscosity_screening_salt_test_4_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3210231.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'slurm-3210231.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt4' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_4_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3210268',
        'case_label': 'Salt 1 Jin continuation retry 2',
        'source_id': 'viscosity_screening_salt_test_1_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3210268.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3210268.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_1_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3210760',
        'case_label': 'Salt 1 Kirst continuation retry 1',
        'source_id': 'viscosity_screening_salt_test_1_kirst_coarse_mesh',
        'variant_label': 'kirst',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate' / 'slurm-3210760.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate' / 'slurm-3210760.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_1_kirst_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3210761',
        'case_label': 'Salt 1 Jin continuation retry 3',
        'source_id': 'viscosity_screening_salt_test_1_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3210761.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3210761.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_1_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3211197',
        'case_label': 'Salt 1 Jin continuation retry 4',
        'source_id': 'viscosity_screening_salt_test_1_jin_coarse_mesh',
        'variant_label': 'jin',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3211197.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'slurm-3211197.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-04_jin_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_1_jin_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
    {
        'job_id': '3211199',
        'case_label': 'Salt 1 Kirst continuation retry 2',
        'source_id': 'viscosity_screening_salt_test_1_kirst_coarse_mesh',
        'variant_label': 'kirst',
        'job_root': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate',
        'slurm_out': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate' / 'slurm-3211199.out',
        'slurm_err': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate' / 'slurm-3211199.err',
        'case_log': WORKSPACE_ROOT / 'jadyn_runs' / 'salt1' / '2026-06-05_targeted_campaign' / 'kirst_continuation_candidate' / 'case_stage' / 'viscosity_screening_salt_test_1_kirst_coarse_mesh_continuation' / 'logs' / 'log.foamRun_continuation',
    },
]


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8', errors='replace')


def parse_sacct(job_ids: list[str]) -> dict[str, dict[str, str]]:
    cmd = [
        'sacct', '-j', ','.join(job_ids),
        '--format=JobID,JobName%24,State,ExitCode,Elapsed', '-P'
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except Exception:
        return {}
    rows = list(csv.DictReader(result.stdout.splitlines(), delimiter='|'))
    summary: dict[str, dict[str, str]] = {}
    for row in rows:
        job_id = row.get('JobID', '')
        if '.' in job_id:
            continue
        summary[job_id] = row
    return summary


def extract_env_value(text: str, key: str) -> str:
    match = re.search(rf'^{re.escape(key)}:\s*(.+)$', text, re.M)
    return match.group(1).strip() if match else ''


def classify_failure(stdout: str, stderr: str, case_log: str, sacct_state: str) -> tuple[str, str]:
    combo = '\n'.join([stdout, stderr, case_log])
    if sacct_state == 'RUNNING':
        return 'running_successfully', 'Live continuation is advancing timesteps under Slurm.'
    if sacct_state == 'COMPLETED':
        return 'completed_runtime', 'Continuation completed cleanly under the repaired runtime path.'
    if sacct_state == 'TIMEOUT':
        return 'timed_out', 'Continuation advanced successfully but hit the allocated walltime limit.'
    if 'cannot find file for object T' in combo:
        return 'missing_reconstructed_T', 'Continuation reached startup, but the staged restart tree was missing a readable reconstructed/root-level T field.'
    if '--showme:link' in combo:
        return 'bashrc_mpi_bootstrap_failure', 'OpenFOAM bootstrap queried an OpenMPI-style compiler flag path that LS6 gcc does not support in this environment.'
    if 'dummy Pstream' in combo:
        return 'dummy_pstream_parallel_failure', 'The solver entered OpenFOAM startup with a serial/dummy parallel library selection instead of an MPI-enabled Pstream build.'
    if 'GLIBCXX_3.4.32' in combo:
        return 'glibcxx_runtime_mismatch', 'The runtime reached the launcher but failed on a libstdc++ symbol mismatch before solver startup.'
    if 'foamRun: command not found' in combo:
        return 'foamrun_path_failure', 'The launcher reached srun without a compute-visible foamRun binary on the ranks.'
    return 'unclassified_failure', 'Failure signature did not match the currently catalogued continuation bootstrap issues.'


def latest_time_from_case_log(text: str) -> str:
    matches = re.findall(r'Time =\s*([0-9.]+)s', text)
    return matches[-1] if matches else ''


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    metadata_rows = {row['source_id']: row for row in load_csv_rows(METADATA_CSV)}
    sacct_rows = parse_sacct([job['job_id'] for job in JOBS])
    continuation_rows: list[dict[str, str]] = []
    property_rows: list[dict[str, str]] = []
    property_ids = [
        'val_salt_test_2_coarse_mesh_laminar',
        'viscosity_screening_salt_test_1_jin_coarse_mesh',
        'viscosity_screening_salt_test_4_jin_coarse_mesh',
        'viscosity_screening_salt_test_4_kirst_coarse_mesh',
    ]
    for source_id in property_ids:
        row = metadata_rows[source_id]
        property_rows.append({
            'source_id': source_id,
            'case_id': row.get('case_id', ''),
            'variant_label': row.get('variant_label', ''),
            'cp_model_summary': row.get('cp_model_summary', ''),
            'mu_coeff_summary': row.get('mu_coeff_summary', ''),
            'kappa_coeff_summary': row.get('kappa_coeff_summary', ''),
            'rho_model_summary': row.get('rho_model_summary', ''),
            'three_d_loss_bc_summary': row.get('three_d_loss_bc_summary', ''),
            'friction_treatment_summary': row.get('friction_treatment_summary', ''),
        })
    for job in JOBS:
        stdout = read_text(job['slurm_out'])
        stderr = read_text(job['slurm_err'])
        case_log = read_text(job['case_log'])
        acct = sacct_rows.get(job['job_id'], {})
        stage, detail = classify_failure(stdout, stderr, case_log, acct.get('State', ''))
        continuation_rows.append({
            'job_id': job['job_id'],
            'case_label': job['case_label'],
            'source_id': job['source_id'],
            'variant_label': job['variant_label'],
            'slurm_state': acct.get('State', ''),
            'exit_code': acct.get('ExitCode', ''),
            'elapsed': acct.get('Elapsed', ''),
            'restart_time_reported': extract_env_value(stdout, 'Restarting from latest processor time'),
            'mpi_root': extract_env_value(stdout, 'Using MPI_ROOT'),
            'i_mpi_pmi_library': extract_env_value(stdout, 'Using I_MPI_PMI_LIBRARY'),
            'foamrun_path': extract_env_value(stdout, 'Using foamRun'),
            'runtime_stage': stage,
            'diagnosis_detail': detail,
            'latest_solver_time_seen_s': latest_time_from_case_log(case_log),
        })
    return continuation_rows, property_rows


def build_plot(rows: list[dict[str, str]]) -> None:
    ensure_dir(REPORT_ROOT)
    state_order = {
        'bashrc_mpi_bootstrap_failure': 0,
        'dummy_pstream_parallel_failure': 1,
        'missing_reconstructed_T': 2,
        'completed_runtime': 3,
        'timed_out': 3,
        'running_successfully': 4,
        'glibcxx_runtime_mismatch': 0,
        'foamrun_path_failure': 0,
        'unclassified_failure': 0,
    }
    colors = {
        'bashrc_mpi_bootstrap_failure': '#b23a48',
        'dummy_pstream_parallel_failure': '#d77a28',
        'missing_reconstructed_T': '#6c757d',
        'completed_runtime': '#2f855a',
        'timed_out': '#577590',
        'running_successfully': '#2a9d4b',
        'glibcxx_runtime_mismatch': '#7f3c8d',
        'foamrun_path_failure': '#8a5a44',
        'unclassified_failure': '#555555',
    }
    labels = []
    ys = []
    cs = []
    for row in rows:
        labels.append(f"{row['job_id']}\n{row['case_label'].replace(' continuation', '')}")
        ys.append(state_order.get(row['runtime_stage'], 0))
        cs.append(colors.get(row['runtime_stage'], '#555555'))
    fig, ax = plt.subplots(figsize=(12, 4.8))
    xs = list(range(len(rows)))
    ax.scatter(xs, ys, s=220, c=cs)
    for x, y, row in zip(xs, ys, rows):
        note = row['latest_solver_time_seen_s'] or row['slurm_state']
        ax.annotate(note, (x, y), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=15, ha='right')
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(['bootstrap failure', 'parallel library failure', 'restart tree failure', 'completed/timeout', 'advancing'])
    ax.set_ylabel('Continuation state')
    ax.set_title('Salt continuation runtime sequence on June 4-7, 2026')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    fig.tight_layout()
    save_matplotlib_figure(fig, REPORT_ROOT, 'continuation_job_sequence', dpi=220)
    plt.close(fig)


def build_readme(continuation_rows: list[dict[str, str]], property_rows: list[dict[str, str]]) -> str:
    salt4_jin = next(row for row in property_rows if row['source_id'] == 'viscosity_screening_salt_test_4_jin_coarse_mesh')
    by_job = {row['job_id']: row for row in continuation_rows}
    salt2 = by_job['3202708']
    salt4_live = by_job['3210231']
    salt1_jin_completed = [by_job[job_id] for job_id in ('3210268', '3210761', '3211197') if job_id in by_job]
    lines = [
        '# Ethan Continuation Diagnosis',
        '',
        f'Generated: `{iso_timestamp()}`',
        '',
        '## Current status',
        '',
        f"- `3202708` for Salt 2 timed out on June 7 after advancing through about `{salt2['latest_solver_time_seen_s']} s`.",
        f"- Salt 4 Jin repaired retry `3210231` is still running and the local continuation log has advanced through about `{salt4_live['latest_solver_time_seen_s']} s`.",
        f"- Salt 1 Jin repaired retries `{', '.join(row['job_id'] for row in salt1_jin_completed)}` all completed successfully under the repaired bootstrap path.",
        '- Salt 1 Kirst retry `3210760` completed successfully, but follow-on retry `3211199` failed immediately with a missing root-level `T` restart file.',
        '- Salt 4 Jin failed in two distinct environment phases before the repaired retry succeeded:',
        '  1. `3208600` and `3208837` failed during OpenFOAM bootstrap with `gcc --showme:link`.',
        '  2. `3208905` got past that bootstrap issue and then failed at solver startup with the dummy Pstream library in parallel mode.',
        '- Salt 1 Jin `3208956` matches the latest Salt 4 Jin failure signature: dummy Pstream in parallel mode.',
        '',
        '## What Salt 4 Jin is using for Cp',
        '',
        f"- Current Salt 4 Jin property model: `{salt4_jin['cp_model_summary']}`.",
        f"- Current viscosity branch: `{salt4_jin['mu_coeff_summary']}`.",
        f"- Current conductivity branch: `{salt4_jin['kappa_coeff_summary']}`.",
        f"- Current density branch: `{salt4_jin['rho_model_summary']}`.",
        '',
        '## Interpreted runtime cause',
        '',
        '- The validated compute probe and the working Salt 2 continuation both depended on sourcing `etc/bashrc` with `WM_MPLIB=INTELMPI` in the bootstrap path.',
        '- The shared env wrapper exported `WM_MPLIB` before sourcing bashrc, but did not pass it as the bashrc source argument. That was the critical difference behind the earlier Salt 1/Salt 4 failures.',
        '- The repaired bootstrap path is now validated for Salt 1 Jin and Salt 1 Kirst. The remaining live question is scientific/runtime usefulness, not MPI bootstrap correctness.',
        '',
        '## Interactive-node guidance',
        '',
        '- You do not need an interactive compute node to explain the old dummy-Pstream failures anymore.',
        '- An interactive node becomes useful only if Salt 4 `3210231` fails after substantial runtime or if a new staged restart tree needs rank-by-rank library inspection.',
        '',
        '## Recommended next steps',
        '',
        '- Keep Salt 4 Jin `3210231` running unless a new runtime fault appears, because it is the only live repaired continuation left today.',
        '- Treat Salt 2 as a defensible timeout rather than an environment failure, then decide whether the extra runtime is still worth another extension.',
        '- Repair the Salt 1 Kirst staged restart tree before any further retry, because `3211199` failed on missing root-level `T`, not on the MPI bootstrap path.',
        '- Refresh convergence, continuation, and wall-loss interpretation packages now that Salt 1 Jin and Salt 1 Kirst each have successful repaired-bootstrap runtime history.',
        '',
        '## Key files',
        '',
        '- `continuation_job_diagnosis.csv`: scheduler and failure signature table.',
        '- `salt_property_reference.csv`: current Salt 1/2/4 property-model reference table.',
        '- `figures/png/continuation_job_sequence.png`: runtime-failure sequence visualization.',
        '',
    ]
    return '\n'.join(lines) + '\n'


def main() -> int:
    ensure_dir(REPORT_ROOT)
    continuation_rows, property_rows = build_rows()
    csv_dump(
        REPORT_ROOT / 'continuation_job_diagnosis.csv',
        list(continuation_rows[0].keys()),
        continuation_rows,
    )
    csv_dump(
        REPORT_ROOT / 'salt_property_reference.csv',
        list(property_rows[0].keys()),
        property_rows,
    )
    build_plot(continuation_rows)
    json_dump(
        REPORT_ROOT / 'summary.json',
        {
            'generated_at': iso_timestamp(),
            'jobs': continuation_rows,
            'property_rows': property_rows,
        },
    )
    (REPORT_ROOT / 'README.md').write_text(build_readme(continuation_rows, property_rows), encoding='utf-8')
    print(json.dumps({'report_root': str(REPORT_ROOT), 'job_count': len(continuation_rows)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
