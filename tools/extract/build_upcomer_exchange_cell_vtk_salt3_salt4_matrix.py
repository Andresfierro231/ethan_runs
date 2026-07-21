#!/usr/bin/env python3
"""Build the Salt3/Salt4 whole-mesh cell VTK matrix package."""

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
from tools.extract.build_upcomer_exchange_cell_vtk_salt2_smoke import inspect_legacy_vtk

TASK_ID = "TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix"
TMP_DIR = ROOT / "tmp/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix"
SOURCE_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit"
GEOMETRY_RELEASE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release"
INPUT_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
SALT2_SMOKE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke"
CASE_IDS = ("salt_3", "salt_4")
REQUIRED_FIELDS = ("U", "T", "rho")

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
    "expected_outputs",
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
NONFINITE_TOKENS = {"-nan", "nan", "NaN", "NAN", "inf", "+inf", "-inf", "Inf", "+Inf", "-Inf", "INF", "+INF", "-INF"}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sh_quote(text: str) -> str:
    return "'" + text.replace("'", "'\"'\"'") + "'"


def source_rows() -> dict[str, dict[str, str]]:
    rows = read_csv(SOURCE_AUDIT / "case_window_source_audit.csv")
    selected = {row["case_id"]: row for row in rows if row["case_id"] in CASE_IDS}
    missing = sorted(set(CASE_IDS) - set(selected))
    if missing:
        raise ValueError(f"Missing source rows: {missing}")
    return selected


def cell_contracts() -> dict[str, dict[str, str]]:
    rows = read_csv(GEOMETRY_RELEASE / "cell_vtk_contract.csv")
    selected = {row["case_id"]: row for row in rows if row["case_id"] in CASE_IDS}
    missing = sorted(set(CASE_IDS) - set(selected))
    if missing:
        raise ValueError(f"Missing cell VTK contracts: {missing}")
    return selected


def expected_vtk_path(case_id: str, output_dir: Path = PACKAGE_DIR) -> Path:
    return output_dir / "vtk" / f"{case_id}_cell_fields.vtk"


def stage_case_name(case_id: str) -> str:
    return f"{case_id}_case_stage"


def staged_internal_vtk_path(case_id: str) -> Path:
    source = source_rows()[case_id]
    return TMP_DIR / stage_case_name(case_id) / "VTK" / f"{stage_case_name(case_id)}_{source['time_window_s']}.vtk"


def harvest_existing_vtks(output_dir: Path = PACKAGE_DIR) -> None:
    for case_id in CASE_IDS:
        source = staged_internal_vtk_path(case_id)
        if not source.exists():
            continue
        target = expected_vtk_path(case_id, output_dir)
        ensure_dir(target.parent)
        shutil.copy2(source, target)


def sanitize_boundary_nonfinite_tokens(path: Path) -> dict[str, Any]:
    """Replace non-finite boundary tokens in a staged volScalarField.

    The internal field is the evidence lane for this task; if any internal
    token is non-finite, fail closed. Boundary-field non-finites can keep
    foamToVTK from reading the file even when only the internal VTK is used, so
    this task-local repair replaces only boundary tokens after the internal
    list terminator.
    """
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    list_header = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("internalField") and "nonuniform" in line:
            list_header = idx
            break
    if list_header is None:
        raise ValueError(f"{path} does not contain a nonuniform internalField.")
    count_idx = list_header + 1
    while count_idx < len(lines) and not lines[count_idx].strip():
        count_idx += 1
    n_values = int(lines[count_idx].strip())
    open_idx = count_idx + 1
    while open_idx < len(lines) and lines[open_idx].strip() != "(":
        open_idx += 1
    if open_idx >= len(lines):
        raise ValueError(f"{path} internalField list opener not found.")
    internal_start = open_idx + 1
    internal_end = internal_start + n_values
    if internal_end >= len(lines):
        raise ValueError(f"{path} internalField list shorter than declared.")
    internal_nonfinite = []
    for offset, line in enumerate(lines[internal_start:internal_end], start=internal_start + 1):
        token = line.strip()
        if token in NONFINITE_TOKENS:
            internal_nonfinite.append(offset)
    if internal_nonfinite:
        raise ValueError(f"{path} has non-finite internal values at lines {internal_nonfinite[:10]}.")
    replacements = 0
    for idx in range(internal_end, len(lines)):
        pieces = lines[idx].split()
        if not pieces:
            continue
        changed = False
        for piece_idx, piece in enumerate(pieces):
            if piece in NONFINITE_TOKENS:
                pieces[piece_idx] = "0"
                replacements += 1
                changed = True
        if changed:
            lines[idx] = " ".join(pieces)
    if replacements:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "path": rel(path),
        "declared_internal_values": n_values,
        "internal_nonfinite_count": len(internal_nonfinite),
        "boundary_nonfinite_replacements": replacements,
    }


def preflight_rows() -> list[dict[str, Any]]:
    sources = source_rows()
    contracts = cell_contracts()
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        source = sources[case_id]
        contract = contracts[case_id]
        case_dir = ROOT / source["case_dir"]
        proc_time = case_dir / "processors64" / source["time_window_s"]
        volume_csv = ROOT / contract["volume_csv"]
        summary_path = volume_csv.with_name(f"{case_id}_cell_volumes_summary.json")
        volume_n = load_json(summary_path).get("n_cells", "") if summary_path.exists() else ""
        blockers = []
        if contract["release_status"] != "released_for_scheduler_cell_vtk_extraction":
            blockers.append("cell_vtk_not_released")
        for label, path in (
            ("case_dir", case_dir),
            ("processors64_time_dir", proc_time),
            ("volume_csv", volume_csv),
            ("volume_summary", summary_path),
            ("of13_env", ROOT / "tools/ofenv/of13_env.sh"),
        ):
            if not path.exists():
                blockers.append(f"missing_{label}")
        rows.append(
            {
                "case_id": case_id,
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
        )
    return rows


def validation_rows(output_dir: Path = PACKAGE_DIR) -> list[dict[str, Any]]:
    contracts = cell_contracts()
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        contract = contracts[case_id]
        vtk = expected_vtk_path(case_id, output_dir)
        if vtk.exists():
            observed_cells, fields = inspect_legacy_vtk(vtk)
            expected = str(contract["volume_n_cells"])
            missing = [field for field in REQUIRED_FIELDS if field not in fields]
            status = "pass" if str(observed_cells) == expected and not missing else "failed"
            reason = "" if status == "pass" else f"cell_count_or_field_mismatch missing={';'.join(missing)}"
        else:
            observed_cells = ""
            fields = []
            status = "pending_not_produced"
            reason = "cell VTK not present yet"
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": contract["time_window_s"],
                "cell_vtk": rel(vtk),
                "expected_cells": contract["volume_n_cells"],
                "observed_cells": observed_cells,
                "required_fields": ";".join(REQUIRED_FIELDS),
                "observed_fields": ";".join(fields),
                "validation_status": status,
                "blocking_reason": reason,
            }
        )
    return rows


def submission_rows(output_dir: Path, submission_id: str = "", submit_command: str = "") -> list[dict[str, Any]]:
    script = output_dir / "scripts/submit_salt3_salt4_cell_vtk_matrix.sbatch"
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
            "expected_outputs": ";".join(rel(expected_vtk_path(case_id, output_dir)) for case_id in CASE_IDS),
            "terminal_condition": "Both VTKs produced and validation_report.csv passes, or Slurm terminal failure with logs",
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
    pass_count = sum(1 for row in validation if row["validation_status"] == "pass")
    artifact_status = "pass" if pass_count == len(CASE_IDS) else f"partial_or_pending_{pass_count}_of_{len(CASE_IDS)}"
    interpretation = "Scheduler terminal state recorded." if scheduler_state else ""
    return [
        {
            "job_id": submission_id,
            "job_name": "upx_s34_cellvtk" if submission_id else "",
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
        {"guard_id": "scope", "status": "salt3_salt4_cell_vtk_only", "policy": "no Salt2 rewrite, interface VTK, wall VTK, Q_wall, or sampler harvest"},
        {"guard_id": "admission", "status": "blocked", "policy": "no fit, score, model selection, exchange-cell admission, Phase 4B/5/S6 trigger"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "no residual absorption into internal Nu"},
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    sources = source_rows()
    paths = [
        Path("tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py"),
        Path("tools/extract/test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py"),
        SALT2_SMOKE,
        GEOMETRY_RELEASE,
        INPUT_GENERATION,
        SOURCE_AUDIT,
        output_dir,
        TMP_DIR,
    ] + [ROOT / sources[case_id]["case_dir"] for case_id in CASE_IDS]
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        relative_path = rel(full)
        task_output = (
            full in {output_dir, TMP_DIR}
            or relative_path.startswith("tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix")
            or relative_path.startswith("tools/extract/test_build_upcomer_exchange_cell_vtk_salt3_salt4_matrix")
        )
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
    sources = source_rows()
    scripts = ensure_dir(output_dir / "scripts")
    ensure_dir(output_dir / "logs")
    ensure_dir(output_dir / "vtk")
    ensure_dir(TMP_DIR)
    runner = scripts / "run_salt3_salt4_cell_vtk_matrix.sh"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"ROOT={sh_quote(str(ROOT))}",
        f"OUT={sh_quote(str(output_dir))}",
        f"TMP_DIR={sh_quote(str(TMP_DIR))}",
        'cd "$ROOT"',
        "PREFLIGHT_ONLY=false",
        'if [[ "${1:-}" == "--preflight-only" ]]; then PREFLIGHT_ONLY=true; fi',
        'mkdir -p "$OUT/logs" "$OUT/vtk" "$TMP_DIR"',
        "set +eu",
        'source "$ROOT/tools/ofenv/of13_env.sh"',
        "source_status=$?",
        "set -euo pipefail",
        'if [[ "$source_status" -ne 0 ]]; then echo "failed to source OF13 env" >&2; exit "$source_status"; fi',
        "of13_assert_ready",
        'command -v reconstructPar >/dev/null',
        'command -v foamToVTK >/dev/null',
    ]
    for case_id in CASE_IDS:
        source = sources[case_id]
        case_dir = ROOT / source["case_dir"]
        time_val = source["time_window_s"]
        stage_case = TMP_DIR / stage_case_name(case_id)
        vtk_out = expected_vtk_path(case_id, output_dir)
        lines.extend(
            [
                f"test -d {sh_quote(str(case_dir / 'processors64' / time_val))}",
                f"test -f {sh_quote(str(ROOT / f'work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/cell_volumes/{case_id}_cell_volumes.csv'))}",
                f"STAGE_{case_id.upper()}={sh_quote(str(stage_case))}",
                f"CASE_{case_id.upper()}={sh_quote(str(case_dir))}",
                f"TIME_{case_id.upper()}={sh_quote(time_val)}",
                f"VTK_OUT_{case_id.upper()}={sh_quote(str(vtk_out))}",
            ]
        )
    lines.extend(
        [
            'if [[ "$PREFLIGHT_ONLY" == true ]]; then echo "preflight OK"; exit 0; fi',
        ]
    )
    for case_id in CASE_IDS:
        upper = case_id.upper()
        time_val = sources[case_id]["time_window_s"]
        stage_name = stage_case_name(case_id)
        lines.extend(
            [
                f'echo "extracting {case_id}"',
                f'STAGE_CASE="$STAGE_{upper}"',
                f'CASE_DIR="$CASE_{upper}"',
                f'TIME_VAL="$TIME_{upper}"',
                f'VTK_OUT="$VTK_OUT_{upper}"',
                'mkdir -p "$STAGE_CASE"',
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
                f'  reconstructPar -case "$STAGE_CASE" -time "$TIME_VAL" -fields "(U T rho)" -fileHandler collated -noFunctionObjects -newTimes > "$OUT/logs/reconstructPar_{case_id}_t{time_val}.log" 2>&1',
                "fi",
                'python3.11 tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py --sanitize-boundary-field "$STAGE_CASE/$TIME_VAL/T" >> "$OUT/logs/stage_field_sanitization.log"',
                f'foamToVTK -case "$STAGE_CASE" -time "$TIME_VAL" -fields "(U T rho)" -ascii -useTimeName -noFaceZones -noPointValues -excludePatches \'(".*")\' -noFunctionObjects > "$OUT/logs/foamToVTK_{case_id}_t{time_val}.log" 2>&1',
                f'vtk_found="$STAGE_CASE/VTK/{stage_name}_{time_val}.vtk"',
                'if [[ ! -f "$vtk_found" ]]; then echo "missing expected internal VTK $vtk_found" >&2; exit 2; fi',
                'cp -a "$vtk_found" "$VTK_OUT"',
            ]
        )
    lines.extend(
        [
            f"python3.11 {sh_quote(str(scripts / 'validate_salt3_salt4_cell_vtk.py'))} {sh_quote(str(output_dir))}",
            f"python3.11 tools/extract/build_upcomer_exchange_cell_vtk_salt3_salt4_matrix.py --harvest --submission-id \"${{SLURM_JOB_ID:-local}}\"",
        ]
    )
    runner.write_text("\n".join(lines) + "\n", encoding="utf-8")
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)

    validator = scripts / "validate_salt3_salt4_cell_vtk.py"
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
                "from tools.extract.build_upcomer_exchange_cell_vtk_salt3_salt4_matrix import validation_rows",
                "out = Path(sys.argv[1])",
                "rows = validation_rows(out)",
                "failed = [row for row in rows if row['validation_status'] != 'pass']",
                "if failed:",
                "    raise SystemExit(f'VTK validation failed: {failed}')",
                "print('VTK validation OK: ' + '; '.join(f\"{row['case_id']} cells={row['observed_cells']} fields={row['observed_fields']}\" for row in rows))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    validator.chmod(validator.stat().st_mode | stat.S_IXUSR)

    sbatch = scripts / "submit_salt3_salt4_cell_vtk_matrix.sbatch"
    sbatch.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "#SBATCH -J upx_s34_cellvtk",
                "#SBATCH -N 1",
                "#SBATCH -n 1",
                "#SBATCH -t 02:00:00",
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
tags: [upcomer, exchange-cell, cell-vtk, salt3, salt4, no-admission]
related:
  - {rel(SALT2_SMOKE)}
  - {rel(GEOMETRY_RELEASE)}
  - {rel(INPUT_GENERATION)}
---
# Salt3/Salt4 Upcomer Exchange Cell VTK Matrix

This package extends the validated Salt2 whole-mesh cell VTK path to Salt3 and
Salt4. It stages local task-owned reconstructed cases under `tmp/` and writes
cell-field VTK artifacts only under this work-product package.

## Decision

- cases: Salt3 `7618`, Salt4 `10000`
- required fields: `U;T;rho`
- expected cells per case: `2166996`
- passed cases: `{summary["vtk_validation_pass_count"]}/{summary["case_count"]}`
- submission state: `{summary["submission_state"]}`
- native output mutation: `false`
- interface/wall/Q_wall/sampler launch: `false`
- fit/score/admission allowed now: `false`

## Outputs

- `preflight.csv`
- `validation_report.csv`
- `submission_record.csv`
- `scheduler_terminal_status.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `scripts/run_salt3_salt4_cell_vtk_matrix.sh`
- `scripts/submit_salt3_salt4_cell_vtk_matrix.sbatch`
- `scripts/validate_salt3_salt4_cell_vtk.py`

## Guardrails

Do not write VTK or reconstructed fields into native Salt3/Salt4 cases. Do not
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
        harvest_existing_vtks(output_dir)
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
    pass_count = sum(1 for row in validation if row["validation_status"] == "pass")
    if pass_count == len(CASE_IDS):
        status = "complete"
    elif submission_id:
        status = "submitted_or_pending"
    else:
        status = "ready_to_submit"
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": status,
        "case_ids": list(CASE_IDS),
        "case_count": len(CASE_IDS),
        "vtk_validation_pass_count": pass_count,
        "submission_state": submission[0]["scheduler_action"],
        "submission_id": submission_id,
        "scheduler_terminal_state": scheduler_state,
        "scheduler_exit_code": exit_code,
        "scheduler_elapsed": elapsed,
        "scheduler_node_list": node_list,
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
            f"# Salt3/Salt4 Cell VTK Matrix Scheduler Handoff\n\nTask: `{TASK_ID}`\n\nJob: `{submission_id}`\n\nState: `{scheduler_state or 'unknown_or_running'}`\n\nExit code: `{exit_code or 'unknown'}`\n\nCommand: `{submit_command}`\n\nExpected outputs: `{submission[0]['expected_outputs']}`\n\nArtifact status: `{scheduler_terminal[0]['artifact_status']}`\n\nTerminal condition: both validation rows pass or Slurm logs record failure. Killing the job is safe for native outputs because all writes are task-local.\n",
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
    parser.add_argument("--sanitize-boundary-field", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sanitize_boundary_field:
        print(json.dumps(sanitize_boundary_nonfinite_tokens(Path(args.sanitize_boundary_field)), sort_keys=True))
        return 0
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
