#!/usr/bin/env python3
"""Build and submit-ready input generation package for upcomer exchange sampling."""

from __future__ import annotations

import argparse
import csv
import json
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
PARSER_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser"
EXPORT_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_export_sbatch"
COMPUTE_GATE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution"
SAMPLER_IMPLEMENTATION = (
    ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation"
)
MESH_READY = PARSER_PACKAGE / "mesh_volume_parser_readiness.csv"

INPUT_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "input_name",
    "path",
    "status",
    "basis",
    "command_or_release_path",
    "blocking_for_sampler_execution",
    "native_solver_output_mutated",
    "admission_use",
]
COMMAND_FIELDS = [
    "case_id",
    "time_window_s",
    "poly_mesh",
    "output_csv",
    "summary_json",
    "stdout_log",
    "stderr_log",
    "command",
    "expected_runtime_policy",
]
BLOCKER_FIELDS = ["case_id", "time_window_s", "blocked_input", "blocker", "next_action", "fit_allowed_now", "score_allowed_now"]
VALIDATION_FIELDS = [
    "case_id",
    "time_window_s",
    "cell_volume_csv",
    "summary_json",
    "status",
    "n_cells",
    "negative_volume_cells",
    "zero_or_negative_volume_cells",
    "sum_raw_volume_m3",
    "basis",
]
SUBMISSION_FIELDS = ["submission_id", "submitted", "scheduler_action", "submit_command", "script", "stdout_log", "stderr_log", "expected_outputs", "terminal_condition"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
HANDOFF_FIELDS = ["sequence", "work_package", "objective", "entry_condition", "forbidden_action"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sh_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


def mesh_rows() -> list[dict[str, str]]:
    return read_csv(MESH_READY)


def case_volume_paths(output_dir: Path, row: dict[str, str]) -> dict[str, Path]:
    root = output_dir / "cell_volumes"
    case_id = row["case_id"]
    return {
        "csv": root / f"{case_id}_cell_volumes.csv",
        "summary": root / f"{case_id}_cell_volumes_summary.json",
        "stdout": output_dir / "logs" / f"{case_id}_cell_volume_export.stdout",
        "stderr": output_dir / "logs" / f"{case_id}_cell_volume_export.stderr",
    }


def external_volume_paths(row: dict[str, str]) -> dict[str, Path]:
    root = EXPORT_PACKAGE / "cell_volumes"
    case_id = row["case_id"]
    return {
        "csv": root / f"{case_id}_cell_volumes.csv",
        "summary": root / f"{case_id}_cell_volumes_summary.json",
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def external_volume_ready(row: dict[str, str]) -> bool:
    paths = external_volume_paths(row)
    return volume_paths_ready(paths)


def task_volume_ready(output_dir: Path, row: dict[str, str]) -> bool:
    paths = case_volume_paths(output_dir, row)
    return volume_paths_ready(paths)


def volume_paths_ready(paths: dict[str, Path]) -> bool:
    summary = load_json(paths["summary"])
    return (
        paths["csv"].exists()
        and paths["summary"].exists()
        and int(summary.get("n_cells", 0)) > 0
        and int(summary.get("negative_volume_cells", 1)) == 0
        and int(summary.get("zero_or_negative_volume_cells", 1)) == 0
    )


def input_rows(output_dir: Path, volume_export_status: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in mesh_rows():
        paths = case_volume_paths(output_dir, case)
        external_paths = external_volume_paths(case)
        if task_volume_ready(output_dir, case):
            volume_path = paths["csv"]
            volume_status = "present_task_owned_cell_volume_export_sbatch"
            volume_basis = "completed TODO-UPCOMER-EXCHANGE-INPUT-GENERATION-2026-07-21 job output"
            volume_release = rel(output_dir / "RUNNING.md")
            volume_blocking = "false"
        elif external_volume_ready(case):
            volume_path = external_paths["csv"]
            volume_status = "present_external_cell_volume_export_sbatch"
            volume_basis = "completed TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21 output"
            volume_release = rel(EXPORT_PACKAGE / "RUNNING.md")
            volume_blocking = "false"
        else:
            volume_path = paths["csv"]
            volume_status = "present_generated" if paths["csv"].exists() else volume_export_status
            volume_basis = "tools/extract/openfoam_cell_volumes.py ASCII polyMesh parser"
            volume_release = rel(output_dir / "scripts/run_cell_volume_exports.sh")
            volume_blocking = str(not paths["csv"].exists()).lower()
        rows.append(
            {
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "time_window_s": case["time_window_s"],
                "input_name": "cell_volume_csv",
                "path": rel(volume_path),
                "status": volume_status,
                "basis": volume_basis,
                "command_or_release_path": volume_release,
                "blocking_for_sampler_execution": volume_blocking,
                "native_solver_output_mutated": "false",
                "admission_use": "diagnostic_only_no_fit_no_exchange_cell_admission",
            }
        )
        for input_name, status, basis, release_path in [
            (
                "recirc_mask",
                "derivable_after_cell_vtk_exists",
                "sample_upcomer_exchange_cell.py fallback U_dot_throughflow_normal_lt_zero",
                "run diagnostic sampler after cell_vtk exists",
            ),
            (
                "cell_vtk",
                "blocked_requires_scheduler_surface_or_cell_sample_dict",
                "same-window U/T/rho plus cellId or same-order cellVolume basis",
                "claim separate OpenFOAM sampling row",
            ),
            (
                "exchange_interface_vtk",
                "blocked_requires_named_exchange_interface_definition",
                "same-window interface U/rho/area with fixed normal sign",
                "claim separate OpenFOAM surface-generation row",
            ),
            (
                "wall_vtk",
                "blocked_requires_wall_core_surface_definition",
                "same-window wall T and optional wallHeatFlux diagnostic",
                "claim separate OpenFOAM surface-generation row",
            ),
            (
                "source_sink_ledger",
                "blocked_requires_same_window_source_sink_extractor",
                "Q_source_W/Q_sink_W with sign convention and source path",
                "claim source/sink ledger extraction row",
            ),
        ]:
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "input_name": input_name,
                    "path": "",
                    "status": status,
                    "basis": basis,
                    "command_or_release_path": release_path,
                    "blocking_for_sampler_execution": "true" if input_name != "recirc_mask" else "false",
                    "native_solver_output_mutated": "false",
                    "admission_use": "diagnostic_only_no_fit_no_exchange_cell_admission",
                }
            )
    return rows


def volume_validation_rows(output_dir: Path = PACKAGE_DIR) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in mesh_rows():
        if task_volume_ready(output_dir, case):
            paths = case_volume_paths(output_dir, case)
            pass_status = "pass_task_owned_volume_export_ready"
            fail_status = "blocked_task_owned_volume_export_missing_or_invalid"
            basis = "completed task-owned cell-volume export summary JSON; line counts validated in row closeout"
        else:
            paths = external_volume_paths(case)
            pass_status = "pass_external_volume_export_ready"
            fail_status = "blocked_external_volume_export_missing_or_invalid"
            basis = "completed external cell-volume export package summary JSON; line counts validated in row closeout"
        summary = load_json(paths["summary"])
        ready = volume_paths_ready(paths)
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "cell_volume_csv": rel(paths["csv"]),
                "summary_json": rel(paths["summary"]),
                "status": pass_status if ready else fail_status,
                "n_cells": summary.get("n_cells", ""),
                "negative_volume_cells": summary.get("negative_volume_cells", ""),
                "zero_or_negative_volume_cells": summary.get("zero_or_negative_volume_cells", ""),
                "sum_raw_volume_m3": summary.get("sum_raw_volume_m3", ""),
                "basis": basis,
            }
        )
    return rows


def volume_command_rows(output_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in mesh_rows():
        paths = case_volume_paths(output_dir, case)
        poly_mesh = ROOT / case["poly_mesh"]
        command = " ".join(
            [
                "python3.11",
                sh_quote(str(ROOT / "tools/extract/openfoam_cell_volumes.py")),
                "--poly-mesh",
                sh_quote(str(poly_mesh)),
                "--output-csv",
                sh_quote(str(paths["csv"])),
                "--summary-json",
                sh_quote(str(paths["summary"])),
            ]
        )
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "poly_mesh": rel(poly_mesh),
                "output_csv": rel(paths["csv"]),
                "summary_json": rel(paths["summary"]),
                "stdout_log": rel(paths["stdout"]),
                "stderr_log": rel(paths["stderr"]),
                "command": command,
                "expected_runtime_policy": "submit_via_sbatch_not_foreground_if_over_5_minutes",
            }
        )
    return rows


def blocker_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    blockers = [
        ("cell_vtk", "requires same-window cell sample with U/T/rho and cellId or same-order volume basis"),
        ("exchange_interface_vtk", "requires named exchange interface geometry and normal sign convention"),
        ("wall_vtk", "requires wall/core surface definition for wall-core Delta T and wall heat diagnostic"),
        ("source_sink_ledger", "requires same-window Q_source/Q_sink extraction and sign convention"),
    ]
    for case in mesh_rows():
        for input_name, blocker in blockers:
            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "blocked_input": input_name,
                    "blocker": blocker,
                    "next_action": "claim_separate_generation_or_extraction_row_before_sampler_execution",
                    "fit_allowed_now": "false",
                    "score_allowed_now": "false",
                }
            )
    return rows


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "pass_no_mutation", "policy": "read native polyMesh only; write generated outputs under task work_product"},
        {"guard_id": "scheduler", "status": "allowed_cell_volume_sbatch_only", "policy": "only task-owned cell-volume export sbatch may be submitted"},
        {"guard_id": "openfoam", "status": "blocked", "policy": "no OpenFOAM solver, reconstructPar, foamPostProcess, or surface sampling in this row"},
        {"guard_id": "admission", "status": "blocked", "policy": "no fit, score, model selection, exchange-cell admission, or Phase 4B/5/S6 trigger"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "pressure and energy residuals stay explicit and are not hidden in internal Nu"},
    ]


def handoff_rows() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "work_package": "monitor_cell_volume_export",
            "objective": "check sbatch terminal state and produced cell volume CSV/summary files",
            "entry_condition": "submission_record.csv has a scheduler job id",
            "forbidden_action": "do not resubmit duplicate volume jobs without a new board row",
        },
        {
            "sequence": 2,
            "work_package": "surface_and_ledger_generation",
            "objective": "generate cell/interface/wall VTKs and source/sink ledgers with exact geometry basis",
            "entry_condition": "cell-volume CSVs exist or terminal export failure is recorded",
            "forbidden_action": "do not run OpenFOAM surface sampling outside a scheduler-authorized row",
        },
        {
            "sequence": 3,
            "work_package": "diagnostic_sampler_execution",
            "objective": "run exchange sampler against ready inputs and emit finite or fail-closed rows",
            "entry_condition": "cell volume, cell VTK, interface VTK, and source ledger statuses are explicit",
            "forbidden_action": "do not fit or score exchange-cell rows",
        },
    ]


def source_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_upcomer_exchange_input_generation.py"),
        Path("tools/extract/test_build_upcomer_exchange_input_generation.py"),
        Path("tools/extract/openfoam_cell_volumes.py"),
        Path("tools/extract/sample_upcomer_exchange_cell.py"),
        PARSER_PACKAGE,
        EXPORT_PACKAGE,
        COMPUTE_GATE,
        SAMPLER_IMPLEMENTATION,
        output_dir,
    ]
    paths.extend(Path(row["poly_mesh"]) for row in mesh_rows())
    out: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        task_output = (
            full == output_dir
            or str(path).startswith("tools/extract/build_upcomer_exchange_input_generation")
            or str(path).startswith("tools/extract/test_build_upcomer_exchange_input_generation")
        )
        native = str(path).startswith("jadyn_runs/")
        out.append(
            {
                "path": rel(full),
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return out


def submission_rows(output_dir: Path, submission_id: str, submit_command: str) -> list[dict[str, Any]]:
    submitted = bool(submission_id)
    script = output_dir / "scripts/submit_cell_volume_exports.sbatch"
    expected_outputs = ";".join(row["output_csv"] for row in volume_command_rows(output_dir))
    terminal_condition = "all task-owned cell_volumes/*_cell_volumes.csv and *_summary.json exist or job terminal failure is recorded"
    if not submitted and all(external_volume_ready(row) for row in mesh_rows()):
        submit_command = "not_submitted_by_this_row_existing_job_3308290_completed"
        expected_outputs = ";".join(rel(external_volume_paths(row)["csv"]) for row in mesh_rows())
        terminal_condition = "external job 3308290 completed and all external cell-volume CSV/summary files validated"
    return [
        {
            "submission_id": submission_id,
            "submitted": str(submitted).lower(),
            "scheduler_action": str(submitted).lower(),
            "submit_command": submit_command,
            "script": rel(script),
            "stdout_log": rel(output_dir / "logs/slurm-%j.out"),
            "stderr_log": rel(output_dir / "logs/slurm-%j.err"),
            "expected_outputs": expected_outputs,
            "terminal_condition": terminal_condition,
        }
    ]


def write_runner(output_dir: Path) -> None:
    scripts = ensure_dir(output_dir / "scripts")
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"ROOT={sh_quote(str(ROOT))}",
        f"OUT={sh_quote(str(output_dir))}",
        'mkdir -p "$OUT/cell_volumes" "$OUT/logs"',
        'echo "upcomer exchange cell-volume export start $(date -Is)"',
    ]
    for row in volume_command_rows(output_dir):
        case_id = row["case_id"]
        lines.extend(
            [
                f'echo "exporting {case_id} cell volumes"',
                f"{row['command']} > {sh_quote(str(output_dir / 'logs' / f'{case_id}_cell_volume_export.stdout'))} "
                f"2> {sh_quote(str(output_dir / 'logs' / f'{case_id}_cell_volume_export.stderr'))}",
            ]
        )
    lines.extend(
        [
            'python3.11 "$ROOT/tools/extract/build_upcomer_exchange_input_generation.py" '
            '--output-dir "$OUT" --volume-export-status completed_from_sbatch '
            '--submission-id "${SLURM_JOB_ID:-manual}" '
            f"--submit-command {sh_quote('postrun_refresh_from_run_cell_volume_exports.sh')} "
            '> "$OUT/logs/postrun_package_refresh.stdout" 2> "$OUT/logs/postrun_package_refresh.stderr"',
            'echo "upcomer exchange cell-volume export end $(date -Is)"',
        ]
    )
    runner = scripts / "run_cell_volume_exports.sh"
    runner.write_text("\n".join(lines) + "\n", encoding="utf-8")
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)

    sbatch = scripts / "submit_cell_volume_exports.sbatch"
    sbatch.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "#SBATCH -J upx_volumes",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 02:00:00",
                "#SBATCH -p NuclearEnergy",
                "#SBATCH -A ASC23046",
                f"#SBATCH -o {output_dir}/logs/slurm-%j.out",
                f"#SBATCH -e {output_dir}/logs/slurm-%j.err",
                "",
                "set -euo pipefail",
                f"{runner}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, input-generation, cell-volume, scheduler]
related:
  - {rel(PARSER_PACKAGE)}
  - {rel(EXPORT_PACKAGE)}
  - {rel(COMPUTE_GATE)}
---
# Upcomer Exchange Input Generation

This package bridges the next input-generation state after the cell-volume
parser and export sbatch. It records the completed Salt2 `7915`, Salt3 `7618`,
and Salt4 `10000` cell-volume CSVs from the dedicated export package, prepares
task-owned export scripts, records the completed task-owned validation export,
and records why the other production sampler inputs remain blocked.

## Decision

- case windows: `{summary["case_rows"]}`
- input ledger rows: `{summary["input_rows"]}`
- task-owned cell-volume CSVs ready: `{summary["task_owned_cell_volume_ready_rows"]}/3`
- external corroborating cell-volume CSVs ready: `{summary["external_cell_volume_ready_rows"]}/3`
- cell-volume export submitted by this row: `{str(summary["cell_volume_export_submitted"]).lower()}`
- scheduler action: `{str(summary["scheduler_action"]).lower()}`
- OpenFOAM surface/postprocessing launch: `false`
- fit/admission/score allowed now: `false`

Cell-volume export was completed under this row and matches the earlier
`TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21` outputs. The
task-owned CSVs are the primary ready inputs for the next row. Cell/interface/
wall VTK generation and source/sink ledger extraction remain explicit blockers
for a later row.

## Outputs

- `input_generation_ledger.csv`: per-case input status.
- `cell_volume_export_validation.csv`: external volume output readiness.
- `cell_volume_export_commands.csv`: exact parser commands and output paths.
- `surface_and_ledger_blockers.csv`: blockers for VTK and source/sink inputs.
- `submission_record.csv`: scheduler submission state.
- `scripts/`: runner and sbatch wrapper for cell-volume export.
- `RUNNING.md`: written when a scheduler job id is recorded.
- `source_manifest.csv`: provenance and mutation flags.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, Fluid source, external
repository, blocker register, generated docs index, fit, model selection,
exchange-cell admission, Phase 4B rescore, Phase 5/S6 trigger, or internal-Nu
residual absorption is changed by this package.
"""


def running_note(output_dir: Path, submission_id: str, submit_command: str) -> str:
    expected = "\n".join(f"- `{row['output_csv']}`" for row in volume_command_rows(output_dir))
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Writer
type: operational_note
status: active
tags: [upcomer, exchange-cell, cell-volume, scheduler]
provenance:
  - {rel(output_dir / "submission_record.csv")}
related:
  - {rel(output_dir / "README.md")}
---
# Running Cell-Volume Export

- task ID: `{TASK_ID}`
- job ID: `{submission_id}`
- submitted from node: unknown from package; check `squeue -j {submission_id}` while queued/running
- exact submit command: `{submit_command}`
- runner: `{rel(output_dir / "scripts/run_cell_volume_exports.sh")}`
- sbatch script: `{rel(output_dir / "scripts/submit_cell_volume_exports.sbatch")}`
- stdout log pattern: `{rel(output_dir / "logs/slurm-%j.out")}`
- stderr log pattern: `{rel(output_dir / "logs/slurm-%j.err")}`

Expected outputs:

{expected}

Terminal condition: all expected CSV and summary JSON files exist, or Slurm
reports a terminal failure. Killing/cancelling the job is safe for native CFD
outputs because it writes only under this work-product package, but do not
resubmit without a new board row or explicit operator decision.
"""


def build_package(
    output_dir: Path = PACKAGE_DIR,
    volume_export_status: str = "ready_for_sbatch_generation",
    submission_id: str = "",
    submit_command: str = "",
) -> dict[str, Any]:
    ensure_dir(output_dir)
    ensure_dir(output_dir / "logs")
    ensure_dir(output_dir / "cell_volumes")
    write_runner(output_dir)

    inputs = input_rows(output_dir, volume_export_status)
    commands = volume_command_rows(output_dir)
    volume_checks = volume_validation_rows(output_dir)
    blockers = blocker_rows()
    submissions = submission_rows(output_dir, submission_id, submit_command)
    guards = guard_rows()
    handoff = handoff_rows()
    manifest = source_manifest(output_dir)
    csv_dump(output_dir / "input_generation_ledger.csv", INPUT_FIELDS, inputs)
    csv_dump(output_dir / "cell_volume_export_validation.csv", VALIDATION_FIELDS, volume_checks)
    csv_dump(output_dir / "cell_volume_export_commands.csv", COMMAND_FIELDS, commands)
    csv_dump(output_dir / "surface_and_ledger_blockers.csv", BLOCKER_FIELDS, blockers)
    csv_dump(output_dir / "submission_record.csv", SUBMISSION_FIELDS, submissions)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "next_agent_handoff.csv", HANDOFF_FIELDS, handoff)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)

    case_rows = len(mesh_rows())
    present_volume = sum(
        1
        for row in inputs
        if row["input_name"] == "cell_volume_csv" and str(row["status"]).startswith("present")
    )
    task_ready = sum(1 for row in mesh_rows() if task_volume_ready(output_dir, row))
    external_ready = sum(1 for row in mesh_rows() if external_volume_ready(row))
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "case_rows": case_rows,
        "input_rows": len(inputs),
        "volume_command_rows": len(commands),
        "volume_validation_rows": len(volume_checks),
        "blocker_rows": len(blockers),
        "guardrail_rows": len(guards),
        "handoff_rows": len(handoff),
        "present_cell_volume_csv_rows": present_volume,
        "task_owned_cell_volume_ready_rows": task_ready,
        "external_cell_volume_ready_rows": external_ready,
        "external_cell_volume_export_package": rel(EXPORT_PACKAGE),
        "cell_volume_export_submitted": bool(submission_id),
        "submission_id": submission_id,
        "scheduler_action": bool(submission_id),
        "openfoam_surface_or_postprocessing_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "phase4b_rescore_run": False,
        "phase5_or_s6_trigger": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    if submission_id:
        (output_dir / "RUNNING.md").write_text(running_note(output_dir, submission_id, submit_command), encoding="utf-8")
    return {"summary": summary, "inputs": inputs, "commands": commands, "blockers": blockers}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    parser.add_argument("--volume-export-status", default="ready_for_sbatch_generation")
    parser.add_argument("--submission-id", default="")
    parser.add_argument("--submit-command", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(
        Path(args.output_dir),
        volume_export_status=args.volume_export_status,
        submission_id=args.submission_id,
        submit_command=args.submit_command,
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
