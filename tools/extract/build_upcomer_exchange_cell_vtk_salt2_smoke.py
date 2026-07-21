#!/usr/bin/env python3
"""Build the Salt2 whole-mesh cell VTK smoke package."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke"
TMP_DIR = ROOT / "tmp/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke"
SOURCE_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit"
GEOMETRY_RELEASE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release"
INPUT_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"

PREFLIGHT_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "case_dir",
    "processors64_time_dir",
    "volume_csv",
    "volume_n_cells",
    "release_status",
    "preflight_status",
    "blocking_reason",
]
VALIDATION_FIELDS = [
    "case_id",
    "time_window_s",
    "cell_vtk",
    "expected_cells",
    "observed_cells",
    "required_fields",
    "observed_fields",
    "validation_status",
    "blocking_reason",
]
SUBMISSION_FIELDS = [
    "submitted",
    "scheduler_action",
    "submission_id",
    "submit_command",
    "script",
    "stdout_log",
    "stderr_log",
    "expected_output",
    "terminal_condition",
]
SCHEDULER_TERMINAL_FIELDS = [
    "job_id",
    "job_name",
    "state",
    "exit_code",
    "elapsed",
    "node_list",
    "artifact_status",
    "interpretation",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sh_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


def salt2_source_row() -> dict[str, str]:
    rows = read_csv(SOURCE_AUDIT / "case_window_source_audit.csv")
    for row in rows:
        if row["case_id"] == "salt_2":
            return row
    raise ValueError("Salt2 source row not found.")


def salt2_cell_contract() -> dict[str, str]:
    rows = read_csv(GEOMETRY_RELEASE / "cell_vtk_contract.csv")
    for row in rows:
        if row["case_id"] == "salt_2":
            return row
    raise ValueError("Salt2 cell VTK contract not found.")


def expected_vtk_path(output_dir: Path = PACKAGE_DIR) -> Path:
    return output_dir / "vtk" / "salt_2_cell_fields.vtk"


def staged_internal_vtk_path() -> Path:
    return TMP_DIR / "salt_2_case_stage" / "VTK" / "salt_2_case_stage_7915.vtk"


def harvest_existing_vtk(output_dir: Path = PACKAGE_DIR) -> None:
    source = staged_internal_vtk_path()
    if not source.exists():
        return
    target = expected_vtk_path(output_dir)
    ensure_dir(target.parent)
    shutil.copy2(source, target)


def preflight_rows() -> list[dict[str, Any]]:
    source = salt2_source_row()
    contract = salt2_cell_contract()
    case_dir = ROOT / source["case_dir"]
    proc_time = case_dir / "processors64" / source["time_window_s"]
    volume_csv = ROOT / contract["volume_csv"]
    volume_summary = volume_csv.with_name("salt_2_cell_volumes_summary.json")
    volume_n = load_json(volume_summary).get("n_cells", "")
    blockers = []
    if contract["release_status"] != "released_for_scheduler_cell_vtk_extraction":
        blockers.append("cell_vtk_not_released")
    for label, path in (
        ("case_dir", case_dir),
        ("processors64_time_dir", proc_time),
        ("volume_csv", volume_csv),
        ("volume_summary", volume_summary),
        ("of13_env", ROOT / "tools/ofenv/of13_env.sh"),
    ):
        if not path.exists():
            blockers.append(f"missing_{label}")
    return [
        {
            "case_id": "salt_2",
            "case_key": source["case_key"],
            "time_window_s": source["time_window_s"],
            "case_dir": rel(case_dir),
            "processors64_time_dir": rel(proc_time),
            "volume_csv": rel(volume_csv),
            "volume_n_cells": volume_n,
            "release_status": contract["release_status"],
            "preflight_status": "ready_for_sbatch_preflight" if not blockers else "blocked",
            "blocking_reason": ";".join(blockers),
        }
    ]


def validation_rows(output_dir: Path = PACKAGE_DIR) -> list[dict[str, Any]]:
    contract = salt2_cell_contract()
    vtk = expected_vtk_path(output_dir)
    if vtk.exists():
        observed_cells, fields = inspect_legacy_vtk(vtk)
        expected = str(contract["volume_n_cells"])
        required = ["U", "T", "rho"]
        missing = [field for field in required if field not in fields]
        status = "pass" if str(observed_cells) == expected and not missing else "failed"
        reason = "" if status == "pass" else f"cell_count_or_field_mismatch missing={';'.join(missing)}"
    else:
        observed_cells = ""
        fields = []
        status = "pending_not_produced"
        reason = "cell VTK not present yet"
    return [
        {
            "case_id": "salt_2",
            "time_window_s": contract["time_window_s"],
            "cell_vtk": rel(vtk),
            "expected_cells": contract["volume_n_cells"],
            "observed_cells": observed_cells,
            "required_fields": "U;T;rho",
            "observed_fields": ";".join(fields),
            "validation_status": status,
            "blocking_reason": reason,
        }
    ]


def inspect_legacy_vtk(path: Path) -> tuple[int | str, list[str]]:
    cell_count: int | str = ""
    fields: list[str] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = 0
    in_cell_data = False
    while idx < len(lines):
        parts = lines[idx].strip().split()
        if not parts:
            idx += 1
            continue
        if len(parts) == 2 and parts[0] == "CELL_DATA":
            cell_count = int(parts[1])
            in_cell_data = True
            idx += 1
            continue
        if parts[0] in {"POINT_DATA", "POINTS", "CELLS", "POLYGONS"}:
            in_cell_data = False
        if in_cell_data and len(parts) >= 2 and parts[0] in {"SCALARS", "VECTORS", "TENSORS"}:
            fields.append(parts[1])
        if in_cell_data and len(parts) >= 3 and parts[0] == "FIELD":
            n_arrays = int(parts[2])
            idx += 1
            for _ in range(n_arrays):
                while idx < len(lines) and not lines[idx].strip():
                    idx += 1
                if idx >= len(lines):
                    break
                header = lines[idx].split()
                if len(header) < 4:
                    break
                fields.append(header[0])
                n_values = int(header[1]) * int(header[2])
                idx += 1
                consumed = 0
                while idx < len(lines) and consumed < n_values:
                    consumed += len(lines[idx].split())
                    idx += 1
            continue
        idx += 1
    return cell_count, sorted(set(fields))


def submission_rows(output_dir: Path, submission_id: str = "", submit_command: str = "") -> list[dict[str, Any]]:
    script = output_dir / "scripts/submit_salt2_cell_vtk_smoke.sbatch"
    submitted = bool(submission_id)
    return [
        {
            "submitted": str(submitted).lower(),
            "scheduler_action": "submitted" if submitted else "not_submitted",
            "submission_id": submission_id,
            "submit_command": submit_command,
            "script": rel(script),
            "stdout_log": rel(output_dir / "logs/slurm-%j.out"),
            "stderr_log": rel(output_dir / "logs/slurm-%j.err"),
            "expected_output": rel(expected_vtk_path(output_dir)),
            "terminal_condition": "VTK produced and validation_report.csv passes, or Slurm terminal failure with logs",
        }
    ]


def scheduler_terminal_rows(
    validation: list[dict[str, Any]],
    *,
    submission_id: str = "",
    scheduler_state: str = "",
    exit_code: str = "",
    elapsed: str = "",
    node_list: str = "",
) -> list[dict[str, Any]]:
    artifact_status = validation[0]["validation_status"]
    interpretation = ""
    if scheduler_state == "FAILED" and artifact_status == "pass":
        interpretation = "Slurm wrapper failed after producing/copying a valid VTK because the generated validator lacked repo-root import setup; validator repaired and rerun post-job."
    elif scheduler_state:
        interpretation = "Scheduler terminal state recorded."
    return [
        {
            "job_id": submission_id,
            "job_name": "upx_s2_cellvtk" if submission_id else "",
            "state": scheduler_state,
            "exit_code": exit_code,
            "elapsed": elapsed,
            "node_list": node_list,
            "artifact_status": artifact_status,
            "interpretation": interpretation,
        }
    ]


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "pass_task_local_stage_only", "policy": "copy/link into tmp and write VTK under work product only"},
        {"guard_id": "scope", "status": "salt2_cell_vtk_only", "policy": "no Salt3/Salt4, interface VTK, wall VTK, Q_wall, or sampler harvest"},
        {"guard_id": "admission", "status": "blocked", "policy": "no fit, score, model selection, exchange-cell admission, Phase 4B/5/S6 trigger"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "no residual absorption into internal Nu"},
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    source = salt2_source_row()
    paths = [
        Path("tools/extract/build_upcomer_exchange_cell_vtk_salt2_smoke.py"),
        Path("tools/extract/test_build_upcomer_exchange_cell_vtk_salt2_smoke.py"),
        GEOMETRY_RELEASE,
        INPUT_GENERATION,
        SOURCE_AUDIT,
        ROOT / source["case_dir"],
        output_dir,
        TMP_DIR,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        relative_path = rel(full)
        task_output = full in {output_dir, TMP_DIR} or relative_path.startswith("tools/extract/build_upcomer_exchange_cell_vtk_salt2_smoke") or relative_path.startswith("tools/extract/test_build_upcomer_exchange_cell_vtk_salt2_smoke")
        native = relative_path.startswith("jadyn_runs/")
        rows.append(
            {
                "path": relative_path,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output).lower(),
            }
        )
    return rows


def write_scripts(output_dir: Path) -> None:
    source = salt2_source_row()
    scripts = ensure_dir(output_dir / "scripts")
    ensure_dir(output_dir / "logs")
    ensure_dir(output_dir / "vtk")
    ensure_dir(TMP_DIR)
    runner = scripts / "run_salt2_cell_vtk_smoke.sh"
    stage_case = TMP_DIR / "salt_2_case_stage"
    vtk_out = expected_vtk_path(output_dir)
    runner.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"ROOT={sh_quote(str(ROOT))}",
                f"CASE_DIR={sh_quote(str(ROOT / source['case_dir']))}",
                f"STAGE_CASE={sh_quote(str(stage_case))}",
                f"TIME_VAL={sh_quote(source['time_window_s'])}",
                f"OUT={sh_quote(str(output_dir))}",
                f"VTK_OUT={sh_quote(str(vtk_out))}",
                'cd "$ROOT"',
                "PREFLIGHT_ONLY=false",
                'if [[ "${1:-}" == "--preflight-only" ]]; then PREFLIGHT_ONLY=true; fi',
                'mkdir -p "$OUT/logs" "$OUT/vtk" "$STAGE_CASE"',
                "set +eu",
                'source "$ROOT/tools/ofenv/of13_env.sh"',
                "source_status=$?",
                "set -euo pipefail",
                'if [[ "$source_status" -ne 0 ]]; then echo "failed to source OF13 env" >&2; exit "$source_status"; fi',
                "of13_assert_ready",
                'command -v reconstructPar >/dev/null',
                'command -v foamToVTK >/dev/null',
                'test -d "$CASE_DIR/processors64/$TIME_VAL"',
                'test -f "$ROOT/work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/cell_volumes/salt_2_cell_volumes.csv"',
                'if [[ "$PREFLIGHT_ONLY" == true ]]; then echo "preflight OK"; exit 0; fi',
                'if [[ ! -d "$STAGE_CASE/constant" ]]; then',
                '  cp -a "$CASE_DIR/constant" "$STAGE_CASE/constant"',
                '  cp -a "$CASE_DIR/system" "$STAGE_CASE/system"',
                '  cp -a "$CASE_DIR/0" "$STAGE_CASE/0"',
                "fi",
                'ln -sfn "$CASE_DIR/processors64" "$STAGE_CASE/processors64"',
                'if [[ -e "$STAGE_CASE/system/functions" || -L "$STAGE_CASE/system/functions" ]]; then',
                '  mv "$STAGE_CASE/system/functions" "$STAGE_CASE/system/functions.cell_vtk_original.$(date +%s)"',
                "fi",
                'if [[ ! -e "$STAGE_CASE/system/functions" ]]; then',
                '  printf "// task-local empty functions include for cell VTK extraction\\n" > "$STAGE_CASE/system/functions"',
                "fi",
                'if [[ ! -d "$STAGE_CASE/$TIME_VAL" ]]; then',
                '  reconstructPar -case "$STAGE_CASE" -time "$TIME_VAL" -fields "(U T rho)" -fileHandler collated -noFunctionObjects -newTimes > "$OUT/logs/reconstructPar_salt2_t${TIME_VAL}.log" 2>&1',
                "fi",
                'foamToVTK -case "$STAGE_CASE" -time "$TIME_VAL" -fields "(U T rho)" -ascii -useTimeName -noFaceZones -noFunctionObjects > "$OUT/logs/foamToVTK_salt2_t${TIME_VAL}.log" 2>&1',
                'mapfile -t vtk_candidates < <(find "$STAGE_CASE/VTK" -maxdepth 1 -type f -name "*.vtk" | sort)',
                'vtk_found="${vtk_candidates[0]:-}"',
                'if [[ -z "$vtk_found" ]]; then echo "no VTK file produced" >&2; exit 2; fi',
                'cp -a "$vtk_found" "$VTK_OUT"',
                f"python3.11 {sh_quote(str(output_dir / 'scripts/validate_salt2_cell_vtk.py'))} {sh_quote(str(vtk_out))} 2166996 U T rho",
                f"python3.11 tools/extract/build_upcomer_exchange_cell_vtk_salt2_smoke.py --harvest --submission-id \"${{SLURM_JOB_ID:-local}}\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    validator = scripts / "validate_salt2_cell_vtk.py"
    validator.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import sys",
                "from pathlib import Path",
                f"ROOT = Path({str(ROOT)!r})",
                "if str(ROOT) not in sys.path:",
                "    sys.path.insert(0, str(ROOT))",
                "from tools.extract.build_upcomer_exchange_cell_vtk_salt2_smoke import inspect_legacy_vtk",
                "path = Path(sys.argv[1])",
                "expected = int(sys.argv[2])",
                "required = set(sys.argv[3:])",
                "observed, fields = inspect_legacy_vtk(path)",
                "missing = sorted(required - set(fields))",
                "if observed != expected or missing:",
                "    raise SystemExit(f'VTK validation failed: observed_cells={observed} expected={expected} missing={missing} fields={fields}')",
                "print(f'VTK validation OK: cells={observed} fields={fields}')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    validator.chmod(validator.stat().st_mode | stat.S_IXUSR)
    sbatch = scripts / "submit_salt2_cell_vtk_smoke.sbatch"
    sbatch.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "#SBATCH -J upx_s2_cellvtk",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 01:00:00",
                "#SBATCH -p NuclearEnergy",
                "#SBATCH -A ASC23046",
                f"#SBATCH -o {output_dir}/logs/slurm-%j.out",
                f"#SBATCH -e {output_dir}/logs/slurm-%j.err",
                "",
                "set -euo pipefail",
                str(runner),
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
status: {summary["status"]}
tags: [upcomer, exchange-cell, cell-vtk, scheduler-smoke, no-admission]
related:
  - {rel(GEOMETRY_RELEASE)}
  - {rel(INPUT_GENERATION)}
  - {rel(SOURCE_AUDIT)}
---
# Salt2 Upcomer Exchange Cell VTK Smoke

This package implements the first executable step after geometry release: a
Salt2-only whole-mesh cell VTK export for `U`, `T`, and `rho`. It stages a
task-local reconstructed case under `tmp/` and writes VTK outputs only under
this work-product package.

## Decision

- case: Salt2 `7915`
- expected cells: `2166996`
- submission state: `{summary["submission_state"]}`
- VTK validation state: `{summary["vtk_validation_state"]}`
- native output mutation: `false`
- interface/wall/Q_wall/sampler launch: `false`
- fit/score/admission allowed now: `false`

## Outputs

- `preflight.csv`
- `validation_report.csv`
- `submission_record.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `scripts/run_salt2_cell_vtk_smoke.sh`
- `scripts/submit_salt2_cell_vtk_smoke.sbatch`
- `scripts/validate_salt2_cell_vtk.py`

## Guardrails

Do not write VTK or reconstructed fields into the native Salt2 case. Do not
generate exchange-interface or wall/core VTKs here. Do not run the exchange-cell
sampler, fit, score, admit, rescore Phase 4B, trigger Phase 5/S6, or absorb any
residual into internal `Nu`.
"""


def build_package(
    output_dir: Path = PACKAGE_DIR,
    *,
    submission_id: str = "",
    submit_command: str = "",
    harvest: bool = False,
    scheduler_state: str = "",
    exit_code: str = "",
    elapsed: str = "",
    node_list: str = "",
) -> dict[str, Any]:
    ensure_dir(output_dir)
    if harvest:
        harvest_existing_vtk(output_dir)
    write_scripts(output_dir)
    preflight = preflight_rows()
    validation = validation_rows(output_dir)
    submission = submission_rows(output_dir, submission_id=submission_id, submit_command=submit_command)
    scheduler_terminal = scheduler_terminal_rows(
        validation,
        submission_id=submission_id,
        scheduler_state=scheduler_state,
        exit_code=exit_code,
        elapsed=elapsed,
        node_list=node_list,
    )
    guards = guard_rows()
    manifest = manifest_rows(output_dir)
    csv_dump(output_dir / "preflight.csv", PREFLIGHT_FIELDS, preflight)
    csv_dump(output_dir / "validation_report.csv", VALIDATION_FIELDS, validation)
    csv_dump(output_dir / "submission_record.csv", SUBMISSION_FIELDS, submission)
    csv_dump(output_dir / "scheduler_terminal_status.csv", SCHEDULER_TERMINAL_FIELDS, scheduler_terminal)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete" if validation[0]["validation_status"] == "pass" else "submitted_or_pending" if submission_id else "ready_to_submit",
        "case_id": "salt_2",
        "time_window_s": preflight[0]["time_window_s"],
        "expected_cells": preflight[0]["volume_n_cells"],
        "submission_state": submission[0]["scheduler_action"],
        "submission_id": submission_id,
        "scheduler_terminal_state": scheduler_state,
        "scheduler_exit_code": exit_code,
        "scheduler_elapsed": elapsed,
        "scheduler_node_list": node_list,
        "vtk_validation_state": validation[0]["validation_status"],
        "native_output_mutation": False,
        "scheduler_action": bool(submission_id),
        "openfoam_postprocessing_launch": bool(submission_id),
        "interface_wall_qwall_or_sampler_launch": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "exchange_cell_admission": False,
        "phase4b_rescore_run": False,
        "phase5_or_s6_trigger": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    if submission_id:
        (output_dir / "RUNNING.md").write_text(
            f"# Salt2 Cell VTK Smoke Scheduler Handoff\n\nTask: `{TASK_ID}`\n\nJob: `{submission_id}`\n\nState: `{scheduler_state or 'unknown_or_running'}`\n\nExit code: `{exit_code or 'unknown'}`\n\nCommand: `{submit_command}`\n\nExpected output: `{rel(expected_vtk_path(output_dir))}`\n\nArtifact validation: `{validation[0]['validation_status']}`\n\nTerminal condition: validation report passes or Slurm logs record failure. Killing the job is safe for native outputs because all writes are task-local.\n",
            encoding="utf-8",
        )
    return {"summary": summary, "preflight": preflight, "validation": validation}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    parser.add_argument("--submission-id", default="")
    parser.add_argument("--submit-command", default="")
    parser.add_argument("--harvest", action="store_true")
    parser.add_argument("--scheduler-state", default="")
    parser.add_argument("--exit-code", default="")
    parser.add_argument("--elapsed", default="")
    parser.add_argument("--node-list", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(
        Path(args.output_dir),
        submission_id=args.submission_id,
        submit_command=args.submit_command,
        harvest=args.harvest,
        scheduler_state=args.scheduler_state,
        exit_code=args.exit_code,
        elapsed=args.elapsed,
        node_list=args.node_list,
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
