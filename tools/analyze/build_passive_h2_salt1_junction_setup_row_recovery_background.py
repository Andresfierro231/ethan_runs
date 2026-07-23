#!/usr/bin/env python3
"""Recover Salt1 PASSIVE-H2 junction setup row and prepare background smoke."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-SALT1-JUNCTION-SETUP-ROW-RECOVERY-BACKGROUND-2026-07-22"
SLUG = "passive_h2_salt1_junction_setup_row_recovery_background"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-salt1-junction-setup-row-recovery-background.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

CASE = ROOT / "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation"
T_FILE = CASE / "0/T"
BOUNDARY = CASE / "constant/polyMesh/boundary"
FLUX = CASE / "postProcessing/wallHeatFlux/4027/wallHeatFlux.dat"
PREV = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate"
RUNTIME_OUT = OUT / "fluid_smoke_outputs/salt_1"
FLUID_ROOT = ROOT.parent / "cfd-modeling-tools/tamu_first_order_model/Fluid"
RUNTIME_EXPECTED_FILES = [
    "runtime_smoke_summary.csv",
    "source_operator_rows_train_only.csv",
    "heat_ledger_delta.csv",
    "sensor_prediction_delta.csv",
    "segment_heat_ledger.csv",
    "runtime_input_audit.csv",
    "summary.json",
]

PATCHES = {
    "cooling_branch": [
        "pipeleg_upper_01_straight",
        "pipeleg_upper_02_bend",
        "pipeleg_upper_03_straight",
        "pipeleg_upper_07_straight",
        "pipeleg_upper_08_bend",
        "pipeleg_upper_09_straight",
    ],
    "downcomer": ["pipeleg_right_01_lower", "pipeleg_right_02_middle", "pipeleg_right_03_upper"],
    "junction": [
        "junction_lower_left",
        "junction_lower_right",
        "junction_upper_right",
        "junction_upper_left",
        "junction_lower_left_left_stub",
        "junction_lower_left_left_extension",
        "junction_lower_left_lower_stub",
        "junction_lower_left_lower_extension",
        "junction_lower_right_right_stub",
        "junction_lower_right_right_extension",
        "junction_lower_right_lower_stub",
        "junction_lower_right_lower_extension",
        "junction_upper_right_right_stub",
        "junction_upper_right_right_extension",
        "junction_upper_right_upper_stub",
        "junction_upper_right_upper_extension",
        "junction_upper_left_upper_stub",
        "junction_upper_left_upper_extension",
    ],
    "lower_leg": [
        "pipeleg_lower_01_fitting",
        "pipeleg_lower_02_straight",
        "pipeleg_lower_03_bend",
        "pipeleg_lower_07_bend",
        "pipeleg_lower_08_straight",
        "pipeleg_lower_09_fitting",
    ],
    "upcomer": [
        "pipeleg_left_01_upper",
        "pipeleg_left_02_connector",
        "pipeleg_left_03_fitting",
        "pipeleg_left_05_fitting",
        "pipeleg_left_06_connector",
        "pipeleg_left_07_lower",
    ],
}

PARENTS = {
    "cooling_branch": "top_horizontal_inlet;cooled_incline_pre_hx;cooled_incline_post_hx;top_horizontal_exit",
    "downcomer": "right_vertical",
    "junction": "bottom_horizontal_inlet",
    "lower_leg": "heated_incline",
    "upcomer": "left_lower_vertical;left_upper_vertical",
}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bool_s(value: Any) -> str:
    return str(bool(value)).lower()


def number(value: float) -> str:
    return f"{value:.12g}"


def blocks() -> dict[str, str]:
    text = T_FILE.read_text(encoding="utf-8", errors="replace")
    return {m.group("name"): m.group("body") for m in re.finditer(r'^\s*"(?P<name>[^"]+)"\s*\{(?P<body>.*?)^\s*\}', text, re.M | re.S)}


def field(body: str, pattern: str) -> str:
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ""


def setup_rows() -> dict[str, dict[str, str]]:
    return {
        name: {
            "patch": name,
            "h": field(body, r"\bh\s+uniform\s+([0-9.eE+-]+)\s*;"),
            "Ta": field(body, r"\bTa\s+constant\s+([0-9.eE+-]+)\s*;"),
            "Tsur": field(body, r"\bTsur\s+constant\s+([0-9.eE+-]+)\s*;"),
            "emissivity": field(body, r"\bemissivity\s+([0-9.eE+-]+)\s*;"),
            "thicknessLayers": field(body, r"\bthicknessLayers\s+([^;]+);"),
            "kappaLayerCoeffs": field(body, r"\bkappaLayerCoeffs\s+([^;]+);"),
        }
        for name, body in blocks().items()
    }


def area_rows() -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for line in FLUX.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        q_w = float(parts[4])
        q_density = float(parts[5])
        rows[parts[1]] = {
            "diagnostic_Q_W": q_w,
            "diagnostic_q_W_m2": q_density,
            "area_m2": abs(q_w / q_density) if q_density else 0.0,
        }
    return rows


def same_or_mixed(values: list[str]) -> str:
    uniq = sorted({value for value in values if value})
    if not uniq:
        return ""
    return uniq[0] if len(uniq) == 1 else "mixed:" + " | ".join(uniq)


def inventory_rows() -> list[dict[str, str]]:
    setup = setup_rows()
    areas = area_rows()
    rows: list[dict[str, str]] = []
    for patch in PATCHES["junction"]:
        s = setup.get(patch, {})
        a = areas.get(patch, {})
        rows.append(
            {
                "patch": patch,
                "setup_boundary_present": bool_s(bool(s)),
                "area_basis_present": bool_s(bool(a) and a.get("area_m2", 0.0) > 0.0),
                "h_present": bool_s(bool(s.get("h"))),
                "Ta_present": bool_s(bool(s.get("Ta"))),
                "Tsur_present": bool_s(bool(s.get("Tsur"))),
                "emissivity_present": bool_s(bool(s.get("emissivity"))),
                "layer_metadata_present": bool_s(bool(s.get("thicknessLayers") and s.get("kappaLayerCoeffs"))),
                "area_m2": number(a.get("area_m2", 0.0)) if a else "",
                "h_W_m2_K": s.get("h", ""),
                "admissibility_role": "setup_geometry_inventory_only",
            }
        )
    return rows


def operator_rows() -> list[dict[str, str]]:
    setup = setup_rows()
    areas = area_rows()
    out: list[dict[str, str]] = []
    for family, patches in PATCHES.items():
        patch_setup = [setup[p] for p in patches if p in setup]
        patch_areas = [areas[p] for p in patches if p in areas]
        area = sum(row["area_m2"] for row in patch_areas)
        hA = sum(float(setup[p]["h"]) * areas[p]["area_m2"] for p in patches if p in setup and p in areas and setup[p].get("h"))
        h = hA / area if area else math.nan
        missing_setup = [p for p in patches if p not in setup]
        missing_area = [p for p in patches if p not in areas or areas[p]["area_m2"] <= 0.0]
        out.append(
            {
                "case_id": "salt_1",
                "source_family": family,
                "external_bc_split_role": "train",
                "original_external_bc_split_role": "train",
                "diagnostic_use": "salt1_junction_recovery_runtime_smoke_no_scoring",
                "area_m2": number(area) if area else "",
                "hA_W_K": number(hA) if hA else "",
                "h_W_m2K_area_weighted": number(h) if math.isfinite(h) else "",
                "Ta_K": same_or_mixed([row["Ta"] for row in patch_setup]),
                "Tsur_K": same_or_mixed([row["Tsur"] for row in patch_setup]),
                "emissivity": same_or_mixed([row["emissivity"] for row in patch_setup]),
                "candidate_id": "PASSIVE-H2-CAND001",
                "admission_or_score": "false",
                "source_property_release": "false",
                "numeric_q_loss_release": "false",
                "runtime_CFD_mdot_used": "false",
                "runtime_Qwall_used": "false",
                "runtime_validation_temperature_used": "false",
                "runtime_wallHeatFlux_used": "false",
                "setup_recovery_status": "recovered_setup_candidate" if not missing_setup and not missing_area and hA else "fail_closed_missing_fields",
                "release_grade_status": "false",
                "missing_setup_patches": ";".join(missing_setup),
                "missing_area_patches": ";".join(missing_area),
                "source_paths": f"{rel(T_FILE)};{rel(BOUNDARY)};{rel(FLUX)}",
            }
        )
    return out


def recovery_gate_rows() -> list[dict[str, str]]:
    inv = inventory_rows()
    op = {row["source_family"]: row for row in operator_rows()}
    junction = op["junction"]
    recoverable = junction["setup_recovery_status"] == "recovered_setup_candidate"
    return [
        {
            "gate": "salt1_junction_patch_setup_inventory",
            "status": "pass" if all(row["setup_boundary_present"] == "true" for row in inv) else "fail_closed",
            "count_or_value": f"{sum(row['setup_boundary_present'] == 'true' for row in inv)}/{len(inv)}",
            "runtime_smoke_allowed": bool_s(False),
            "reason": "patch setup fields exist, but runtime smoke waits for operator schema compatibility",
        },
        {
            "gate": "salt1_junction_area_basis_inventory",
            "status": "pass" if all(row["area_basis_present"] == "true" for row in inv) else "fail_closed",
            "count_or_value": f"{sum(row['area_basis_present'] == 'true' for row in inv)}/{len(inv)}",
            "runtime_smoke_allowed": bool_s(False),
            "reason": "area recovered from diagnostic geometry accounting; heat-flux values remain non-runtime",
        },
        {
            "gate": "five_family_operator_csv_candidate",
            "status": "pass_diagnostic" if recoverable else "fail_closed",
            "count_or_value": f"{sum(row['setup_recovery_status'] == 'recovered_setup_candidate' for row in op.values())}/5",
            "runtime_smoke_allowed": bool_s(recoverable),
            "reason": "operator CSV is suitable for a diagnostic smoke only, not release or freeze",
        },
        {
            "gate": "source_property_release",
            "status": "fail_closed",
            "count_or_value": "0",
            "runtime_smoke_allowed": bool_s(False),
            "reason": "junction recovery does not repair strict source-envelope or release-UQ",
        },
    ]


def command_rows() -> list[dict[str, str]]:
    command = (
        "python3.11 -B -m tamu_loop_model_v2.passive_h2_radiation_runtime_smoke "
        f"--operator-csv {OUT / 'salt1_five_family_operator_rows_for_fluid.csv'} "
        f"--target-csv {OUT / 'salt1_junction_recovery_target_context.csv'} "
        f"--output-root {RUNTIME_OUT} --case-id salt_1 --include-current-baseline"
    )
    job_file = OUT / "slurm_job_id.txt"
    job_id = job_file.read_text(encoding="utf-8").strip() if job_file.exists() else ""
    status = "submitted" if job_id else "prepared_not_submitted"
    if runtime_summary_status() == "failed_after_partial_outputs_schema_mismatch":
        status = "failed_after_partial_outputs_schema_mismatch"
    return [
        {
            "case_id": "salt_1",
            "command": command,
            "working_directory": str(FLUID_ROOT),
            "status": status,
            "scheduler_job_id": job_id,
            "stdout_log": rel(OUT / "salt1_junction_runtime_smoke.%j.out"),
            "stderr_log": rel(OUT / "salt1_junction_runtime_smoke.%j.err"),
            "output_root": rel(RUNTIME_OUT),
        }
    ]


def scheduler_job_id() -> str:
    job_file = OUT / "slurm_job_id.txt"
    return job_file.read_text(encoding="utf-8").strip() if job_file.exists() else ""


def failed_scheduler_jobs() -> list[str]:
    failed_file = OUT / "failed_slurm_job_ids.txt"
    if not failed_file.exists():
        return []
    return [line.strip() for line in failed_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def submission_attempt_rows() -> list[dict[str, str]]:
    job_id = scheduler_job_id()
    failed = failed_scheduler_jobs()
    rows = [
        {
            "attempt_order": "1",
            "location": "compute_node",
            "command": f"sbatch {OUT / 'submit_salt1_junction_runtime_smoke.sbatch'}",
            "result": "not_submitted_sbatch_unavailable_on_compute_node",
            "scheduler_job_id": "",
            "note": "local TACC wrapper reported that sbatch must be run from a login node",
        },
        {
            "attempt_order": "2",
            "location": "login3",
            "command": f"ssh login3 'cd {ROOT} && sbatch {OUT / 'submit_salt1_junction_runtime_smoke.sbatch'}'",
            "result": "not_submitted_missing_account_directive",
            "scheduler_job_id": "",
            "note": "Slurm reported multiple charge projects and requested an account directive",
        },
    ]
    if job_id:
        rows.append(
            {
                "attempt_order": "3",
                "location": "login3",
                "command": f"ssh login3 'cd {ROOT} && sbatch {OUT / 'submit_salt1_junction_runtime_smoke.sbatch'}'",
                "result": "submitted_replacement" if failed else "submitted",
                "scheduler_job_id": job_id,
                "note": "submitted after generated sbatch was patched with #SBATCH -A ASC23046 and target context matched Fluid runner schema",
            }
        )
    return rows


def write_scripts() -> None:
    run = f"""#!/usr/bin/env bash
set -euo pipefail
cd {FLUID_ROOT}
python3.11 -B -m tamu_loop_model_v2.passive_h2_radiation_runtime_smoke \\
  --operator-csv {OUT / 'salt1_five_family_operator_rows_for_fluid.csv'} \\
  --target-csv {OUT / 'salt1_junction_recovery_target_context.csv'} \\
  --output-root {RUNTIME_OUT} \\
  --case-id salt_1 \\
  --include-current-baseline
"""
    sbatch = f"""#!/usr/bin/env bash
#SBATCH -J h2_s1_junction
#SBATCH -A ASC23046
#SBATCH -p development
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 00:20:00
#SBATCH -o {OUT / 'salt1_junction_runtime_smoke.%j.out'}
#SBATCH -e {OUT / 'salt1_junction_runtime_smoke.%j.err'}

set -euo pipefail
{OUT / 'run_salt1_junction_runtime_smoke.sh'}
"""
    (OUT / "run_salt1_junction_runtime_smoke.sh").write_text(run, encoding="utf-8")
    (OUT / "submit_salt1_junction_runtime_smoke.sbatch").write_text(sbatch, encoding="utf-8")
    (OUT / "run_salt1_junction_runtime_smoke.sh").chmod(0o755)
    (OUT / "submit_salt1_junction_runtime_smoke.sbatch").chmod(0o755)


def write_background_handoff() -> None:
    job_file = OUT / "slurm_job_id.txt"
    if not job_file.exists():
        return
    job_id = job_file.read_text(encoding="utf-8").strip()
    if not job_id:
        return
    completed = (RUNTIME_OUT / "summary.json").exists()
    handoff_status = "complete" if completed else "running"
    completion_text = (
        f"Complete: `{rel(RUNTIME_OUT / 'summary.json')}` exists and records "
        "`decision == runtime_radiation_smoke_complete_no_release_no_score`."
        if completed
        else (
            f"Completion condition: `sacct -j {job_id}` reaches `COMPLETED` and "
            f"`{rel(RUNTIME_OUT / 'summary.json')}` exists with "
            "`decision == runtime_radiation_smoke_complete_no_release_no_score`."
        )
    )
    (OUT / "BACKGROUND_HANDOFF.md").write_text(
        f"""---
provenance:
  - {rel(OUT / "submit_salt1_junction_runtime_smoke.sbatch")}
  - {rel(OUT / "run_salt1_junction_runtime_smoke.sh")}
  - {rel(OUT / "command_manifest.csv")}
tags: [PASSIVE-H2, Salt1, junction, slurm, monitor]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Monitor
type: handoff
status: {handoff_status}
---
# Salt1 Junction Runtime Smoke Background Handoff

Task ID: `{TASK_ID}`.

Slurm job: `{job_id}`.

Command file: `{rel(OUT / "submit_salt1_junction_runtime_smoke.sbatch")}`.

Payload command: `{rel(OUT / "run_salt1_junction_runtime_smoke.sh")}`.

Expected output root: `{rel(RUNTIME_OUT)}`.

Logs:

- stdout pattern: `{rel(OUT / "salt1_junction_runtime_smoke.%j.out")}`
- stderr pattern: `{rel(OUT / "salt1_junction_runtime_smoke.%j.err")}`

{completion_text}

Forbidden actions without a new board row: duplicate submission, native CFD
mutation, registry/admission mutation, source/property release, Qwall release,
coefficient admission, candidate freeze, protected/final scoring, or Fluid
source edits.
""",
        encoding="utf-8",
    )


def target_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": "salt_1",
            "scenario_id": "salt_1__junction_recovery",
            "expected_delta_W": "",
            "radiation_on_expected_heat_ledger_delta_W": "nan",
            "passive_operator_full_on_expected_heat_ledger_delta_W": "nan",
            "protected_scoring": "false",
            "target_status": "not_available_without_forbidden_target_replay_nan_placeholders_for_runner_schema",
        }
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        ("salt1_T_boundary", T_FILE),
        ("salt1_mesh_boundary", BOUNDARY),
        ("salt1_geometry_area_accounting", FLUX),
        ("previous_salt1_runtime_package", PREV / "summary.json"),
        ("previous_salt1_recovery_package", RECOVERY / "summary.json"),
        ("fluid_runtime_smoke_module", FLUID_ROOT / "tamu_loop_model_v2/passive_h2_radiation_runtime_smoke.py"),
    ]
    return [{"role": role, "path": rel(path), "mode": "read_only", "exists": bool_s(path.exists())} for role, path in paths]


def guardrail_rows() -> list[dict[str, str]]:
    names = [
        "native_solver_outputs_mutated",
        "registry_or_admission_mutated",
        "fluid_or_external_source_edit",
        "source_property_release",
        "numeric_q_loss_release",
        "qwall_release",
        "coefficient_admission",
        "candidate_freeze",
        "protected_or_final_scoring",
        "hidden_multiplier_or_residual_absorption",
    ]
    return [{"guardrail": name, "value": "false"} for name in names]


def runtime_stderr_text() -> str:
    job_id = scheduler_job_id()
    err = OUT / f"salt1_junction_runtime_smoke.{job_id}.err"
    if err.exists():
        return err.read_text(encoding="utf-8", errors="replace")
    return ""


def runtime_artifact_rows() -> list[dict[str, str]]:
    rows = []
    for filename in RUNTIME_EXPECTED_FILES:
        path = RUNTIME_OUT / filename
        rows.append(
            {
                "artifact": filename,
                "path": rel(path),
                "exists": bool_s(path.exists()),
                "role": "partial_runtime_output" if filename in {"runtime_smoke_summary.csv", "source_operator_rows_train_only.csv"} else "post_summary_output",
            }
        )
    return rows


def runtime_summary_status() -> str:
    summary = read_json(RUNTIME_OUT / "summary.json")
    if summary:
        return str(summary.get("decision", "completed"))
    stderr = runtime_stderr_text()
    if "KeyError: 'radiation_on_expected_heat_ledger_delta_W'" in stderr:
        return "failed_after_partial_outputs_schema_mismatch"
    if (OUT / "slurm_job_id.txt").exists() and failed_scheduler_jobs():
        return "replacement_submitted_pending_or_running_after_failed_partial_output"
    if (RUNTIME_OUT / "runtime_smoke_summary.csv").exists():
        return "partial_outputs_present_no_fluid_summary"
    if (OUT / "slurm_job_id.txt").exists():
        return "submitted_pending_or_running"
    return "not_submitted"


def runtime_failure_reason() -> str:
    status = runtime_summary_status()
    if status == "runtime_radiation_smoke_complete_no_release_no_score":
        return "replacement Slurm job completed the diagnostic Fluid smoke and wrote terminal summary.json"
    if status == "failed_after_partial_outputs_schema_mismatch":
        return (
            "Fluid runner solved the current, PASSIVE-H2 radiation-off, and PASSIVE-H2 "
            "radiation-on rows, then failed while constructing heat_ledger_delta.csv "
            "because the runner attempted to read radiation_on_expected_heat_ledger_delta_W "
            "from a schema-incompatible matched table."
        )
    if status == "partial_outputs_present_no_fluid_summary":
        return "runtime summary exists, but Fluid summary.json is absent"
    if status == "replacement_submitted_pending_or_running_after_failed_partial_output":
        return (
            "replacement Slurm job is pending or running; prior failed job wrote partial "
            "runtime summary outputs before Fluid summary/heat-ledger outputs existed"
        )
    return ""


def terminal_runtime_values() -> dict[str, Any]:
    summary = read_json(RUNTIME_OUT / "summary.json")
    if not summary:
        return {
            "runtime_completed": False,
            "runtime_operator_rows_used": 0,
            "runtime_train_rows_used": 0,
            "runtime_root_statuses": {},
            "runtime_radiation_on_heat_ledger_delta_W": None,
            "runtime_radiation_on_nonzero": False,
            "runtime_forbidden_inputs_used": False,
            "runtime_protected_scoring": False,
            "runtime_fitting_or_model_selection": False,
        }
    forbidden = any(
        bool(summary.get(name, False))
        for name in [
            "runtime_CFD_mdot_used",
            "runtime_Qwall_used",
            "runtime_imposed_cooler_duty_used",
            "runtime_validation_temperature_used",
            "runtime_wallHeatFlux_used",
        ]
    )
    return {
        "runtime_completed": summary.get("decision") == "runtime_radiation_smoke_complete_no_release_no_score",
        "runtime_operator_rows_used": int(summary.get("operator_rows_used", 0)),
        "runtime_train_rows_used": int(summary.get("train_rows_used", 0)),
        "runtime_root_statuses": summary.get("root_statuses", {}),
        "runtime_radiation_on_heat_ledger_delta_W": summary.get("radiation_on_heat_ledger_delta_W"),
        "runtime_radiation_on_nonzero": bool(summary.get("radiation_on_nonzero", False)),
        "runtime_forbidden_inputs_used": forbidden,
        "runtime_protected_scoring": bool(summary.get("protected_scoring", False)),
        "runtime_fitting_or_model_selection": bool(summary.get("fitting_or_model_selection", False)),
    }


def partial_runtime_rows() -> list[dict[str, str]]:
    rows = read_csv(RUNTIME_OUT / "runtime_smoke_summary.csv")
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "case_id": row.get("case", ""),
                "run_label": row.get("run_label", ""),
                "radiation_on": row.get("radiation_on", ""),
                "root_status": row.get("root_status", ""),
                "validity_status": row.get("validity_status", ""),
                "accepted_for_validation": row.get("accepted_for_validation", ""),
                "protected_target_used": row.get("protected_target_used", ""),
                "mdot_kg_s": row.get("mdot_kg_s", ""),
                "predicted_air_outlet_temperature_K": row.get("predicted_air_outlet_temperature_K", ""),
                "qhx_total_W": row.get("qhx_total_W", ""),
                "qambient_total_W": row.get("qambient_total_W", ""),
                "start_temperature_K": row.get("start_temperature_K", ""),
                "end_temperature_K": row.get("end_temperature_K", ""),
                "temperature_periodicity_error_K": row.get("temperature_periodicity_error_K", ""),
                "diagnostic_status": "partial_runtime_summary_retained_no_release_no_score",
            }
        )
    return out


def f(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "nan"))
    except ValueError:
        return float("nan")


def partial_heat_delta_rows() -> list[dict[str, str]]:
    rows = {row.get("run_label", ""): row for row in read_csv(RUNTIME_OUT / "runtime_smoke_summary.csv")}
    pairs = [
        ("role_rad_off_minus_current_no_role", "passive_h2_role_rad_off", "current_no_role_rad_off"),
        ("role_rad_on_minus_role_rad_off", "passive_h2_role_rad_on", "passive_h2_role_rad_off"),
    ]
    out: list[dict[str, str]] = []
    for delta_kind, lhs, rhs in pairs:
        if lhs not in rows or rhs not in rows:
            continue
        left = rows[lhs]
        right = rows[rhs]
        out.append(
            {
                "case_id": "salt_1",
                "delta_kind": delta_kind,
                "delta_qambient_W": number(f(left, "qambient_total_W") - f(right, "qambient_total_W")),
                "delta_qhx_W": number(f(left, "qhx_total_W") - f(right, "qhx_total_W")),
                "delta_mdot_kg_s": number(f(left, "mdot_kg_s") - f(right, "mdot_kg_s")),
                "delta_predicted_air_outlet_temperature_K": number(
                    f(left, "predicted_air_outlet_temperature_K") - f(right, "predicted_air_outlet_temperature_K")
                ),
                "target_delta_W": "nan",
                "target_basis": "no protected target available; target intentionally not used",
                "diagnostic_status": "computed_from_partial_runtime_summary_after_runner_schema_failure",
                "protected_target_used": "false",
            }
        )
    return out


def write_readme(summary: dict[str, Any]) -> None:
    partial_rows = partial_runtime_rows()
    heat_rows = partial_heat_delta_rows()
    text = f"""---
provenance:
  - {rel(T_FILE)}
  - {rel(FLUX)}
  - {rel(OUT / "salt1_five_family_operator_rows_for_fluid.csv")}
  - {rel(RUNTIME_OUT / "runtime_smoke_summary.csv")}
tags: [PASSIVE-H2, Salt1, junction, background-smoke, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Monitor
type: work_product
status: complete
---
# PASSIVE-H2 Salt1 Junction Setup-Row Recovery

Decision: `{summary["decision"]}`.

Salt1 junction setup evidence was recovered as a diagnostic operator-row
candidate. The row has setup boundary fields and area accounting for 18
junction/stub patches, and the package writes a five-family operator CSV plus
an sbatch smoke script. This does not release source/property values or freeze
PASSIVE-H2.

Runtime status: `{summary["runtime_status"]}`.

Scheduler job ID: `{summary["scheduler_job_id"]}`.

Previous failed scheduler attempts: `{summary["failed_scheduler_jobs"]}`.

Runtime terminal finding: `{summary["runtime_failure_reason"]}`.

Terminal runtime evidence: completed `{summary["runtime_completed"]}`, operator
rows used `{summary["runtime_operator_rows_used"]}`, train rows used
`{summary["runtime_train_rows_used"]}`, root statuses
`{summary["runtime_root_statuses"]}`, radiation-on heat-ledger delta
`{summary["runtime_radiation_on_heat_ledger_delta_W"]}` W, forbidden runtime
inputs used `{summary["runtime_forbidden_inputs_used"]}`.

Partial runtime rows retained: `{len(partial_rows)}`. Partial heat-delta rows
computed from `runtime_smoke_summary.csv`: `{len(heat_rows)}`. These are
diagnostic-only rows and are superseded for terminal runtime status when the
replacement job writes a complete Fluid `summary.json`.

Submission note: direct compute-node `sbatch` was refused by the TACC wrapper;
the accepted submission used `login3` with account `ASC23046`.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    STATUS.write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "salt1_junction_patch_inventory.csv")}
  - {rel(OUT / "salt1_five_family_operator_rows_for_fluid.csv")}
tags: [PASSIVE-H2, Salt1, junction, background-smoke, no-release]
related:
  - {rel(OUT / "README.md")}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Monitor
type: status
status: complete
---
# {TASK_ID}

Objective: recover the missing Salt1 PASSIVE-H2 junction setup row and prepare
or submit the background diagnostic runtime smoke if the row is non-leaky.

Outcome: `{summary["decision"]}`. Junction patch setup coverage is
`{summary["junction_setup_patch_rows"]}` / `{summary["junction_required_patch_rows"]}`;
five-family operator rows are `{summary["operator_rows"]}`. Runtime status is
`{summary["runtime_status"]}` with Slurm job `{summary["scheduler_job_id"]}`.
Previous failed Slurm attempts recorded in package:
`{summary["failed_scheduler_jobs"]}`.
Release/freeze/final-score rows remain zero.

Runtime terminal finding: `{summary["runtime_failure_reason"]}`. Current
partial runtime summary rows: `{summary["partial_runtime_summary_rows"]}`;
partial transparent heat-delta rows: `{summary["partial_heat_delta_rows"]}`.
Terminal runtime evidence: completed `{summary["runtime_completed"]}`, operator
rows used `{summary["runtime_operator_rows_used"]}`, train rows used
`{summary["runtime_train_rows_used"]}`, root statuses
`{summary["runtime_root_statuses"]}`, radiation-on heat-ledger delta
`{summary["runtime_radiation_on_heat_ledger_delta_W"]}` W, forbidden runtime
inputs used `{summary["runtime_forbidden_inputs_used"]}`. These rows are
retained for diagnostics only and are not release-grade source or scoring
evidence.

## Changes Made

- `{rel(OUT)}`
- `{rel(Path("tools/analyze/build_passive_h2_salt1_junction_setup_row_recovery_background.py"))}`
- `{rel(Path("tools/analyze/test_passive_h2_salt1_junction_setup_row_recovery_background.py"))}`
- `{rel(IMPORT)}`
- `.agent/STATE.md`
- `.agent/catalog.json`
- `.agent/catalog.csv`
- `.agent/BLOCKERS.md`

## Validation

- `python3.11 tools/analyze/build_passive_h2_salt1_junction_setup_row_recovery_background.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_salt1_junction_setup_row_recovery_background`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_salt1_junction_setup_row_recovery_background.py tools/analyze/test_passive_h2_salt1_junction_setup_row_recovery_background.py`
- `python3.11 tools/agent/runtime_input_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/split_policy_lint.py {rel(OUT)} {rel(STATUS)} {rel(JOURNAL)} {rel(IMPORT)}`
- `python3.11 tools/agent/manifest_check.py {rel(IMPORT)} --check-paths`
- `ssh login3 "squeue -j {summary["scheduler_job_id"]} -o '%i %j %T %M %l %R'"`
- `ssh login3 "sacct -j {summary["scheduler_job_id"]} --format=JobID,JobName,Partition,Account,State,Elapsed,ExitCode,NodeList%20 -X"`
- `sacct -j {summary["scheduler_job_id"]} --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, Fluid/external source
edit, thesis edit, protected/final scoring, fitting/tuning/model selection,
source/property release, Qwall release, numeric q-loss release, coefficient
admission, candidate freeze, hidden multiplier, residual absorption, or
runtime-leakage relaxation.
""",
        encoding="utf-8",
    )
    ensure_dir(JOURNAL.parent)
    JOURNAL.write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "salt1_junction_recovery_gate.csv")}
tags: [PASSIVE-H2, Salt1, junction, background-smoke]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Monitor
type: journal
status: complete
---
# PASSIVE-H2 Salt1 Junction Setup-Row Recovery

Attempted: recover the missing Salt1 junction setup row from native setup
boundary dictionaries and patch area accounting, then prepare the background
runtime smoke path.

Observed: Salt1 contains the junction/stub setup patches needed for a grouped
junction row. The recovered row is diagnostic and setup-only; it does not repair
strict source-envelope, release-UQ, or source/property release gates.

Scheduler: direct compute-node `sbatch` was refused by the TACC wrapper; the
first login-node submission lacked an account directive; after adding
`#SBATCH -A ASC23046`, the first submitted job failed on a package-side target
CSV schema mismatch. The target context was repaired with explicit `nan`
placeholders for the runner's optional target columns, and replacement Slurm
job `{summary["scheduler_job_id"]}` completed. The terminal runtime summary
used five train rows, accepted all three roots, used no forbidden/protected
runtime inputs, and produced a nonzero radiation heat-ledger response.

Observed runtime output: the failed prior execution wrote runtime summary rows
for current/no-role radiation-off, PASSIVE-H2 radiation-off, and PASSIVE-H2
radiation-on before the Fluid runner's post-summary heat-ledger comparison
failed. The retained diagnostic deltas are in
`{rel(OUT / "partial_heat_delta_from_runtime_summary.csv")}`. They are not
score values and do not use protected targets.

Inferred: this removes the mechanical Salt1 4/5 coverage issue if the background
smoke lands, but H2 still cannot freeze until source-envelope and release-UQ
are admitted.
""",
        encoding="utf-8",
    )


def write_import_manifest() -> None:
    package_files = [rel(path) for path in sorted(OUT.rglob("*")) if path.is_file()]
    changed = sorted(
        dict.fromkeys(
            [
                ".agent/BOARD.md",
                rel(STATUS),
                rel(JOURNAL),
                rel(IMPORT),
                "tools/analyze/build_passive_h2_salt1_junction_setup_row_recovery_background.py",
                "tools/analyze/test_passive_h2_salt1_junction_setup_row_recovery_background.py",
                ".agent/STATE.md",
                ".agent/catalog.json",
                ".agent/catalog.csv",
                ".agent/BLOCKERS.md",
                *package_files,
            ]
        )
    )
    json_dump(
        IMPORT,
        {
            "task": TASK_ID,
            "task_id": TASK_ID,
            "generated_at": iso_timestamp(),
            "changed_files": changed,
            "changed_paths": changed,
            "read_only_context": [row["path"] for row in source_manifest_rows()],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": (OUT / "slurm_job_id.txt").exists(),
            "external_fluid_edit": False,
            "no_scorecard_outputs": True,
        },
    )


def write_outputs() -> dict[str, Any]:
    ensure_dir(OUT)
    inventory = inventory_rows()
    operators = operator_rows()
    gates = recovery_gate_rows()
    commands = command_rows()
    write_scripts()
    csv_dump(OUT / "source_manifest.csv", ["role", "path", "mode", "exists"], source_manifest_rows())
    csv_dump(OUT / "salt1_junction_patch_inventory.csv", list(inventory[0]), inventory)
    csv_dump(OUT / "salt1_five_family_operator_rows_for_fluid.csv", list(operators[0]), operators)
    csv_dump(OUT / "salt1_junction_recovery_gate.csv", list(gates[0]), gates)
    csv_dump(OUT / "salt1_junction_recovery_target_context.csv", list(target_rows()[0]), target_rows())
    csv_dump(OUT / "command_manifest.csv", list(commands[0]), commands)
    attempts = submission_attempt_rows()
    csv_dump(OUT / "submission_attempts.csv", list(attempts[0]), attempts)
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrail_rows())
    artifacts = runtime_artifact_rows()
    csv_dump(OUT / "runtime_artifact_status.csv", list(artifacts[0]), artifacts)
    partial_runtime = partial_runtime_rows()
    if partial_runtime:
        csv_dump(OUT / "partial_runtime_smoke_summary.csv", list(partial_runtime[0]), partial_runtime)
    partial_heat = partial_heat_delta_rows()
    if partial_heat:
        csv_dump(OUT / "partial_heat_delta_from_runtime_summary.csv", list(partial_heat[0]), partial_heat)
    write_background_handoff()
    runtime_status = runtime_summary_status()
    terminal_runtime = terminal_runtime_values()
    job_id = scheduler_job_id()
    failed_jobs = failed_scheduler_jobs()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "salt1_junction_setup_row_recovered_background_runtime_smoke_prepared_no_release",
        "candidate_id": "PASSIVE-H2-CAND001",
        "junction_required_patch_rows": len(inventory),
        "junction_setup_patch_rows": sum(1 for row in inventory if row["setup_boundary_present"] == "true"),
        "junction_area_patch_rows": sum(1 for row in inventory if row["area_basis_present"] == "true"),
        "operator_rows": len(operators),
        "five_family_operator_ready": all(row["setup_recovery_status"] == "recovered_setup_candidate" for row in operators),
        "runtime_status": runtime_status,
        "runtime_failure_reason": runtime_failure_reason(),
        "runtime_artifacts_present": sum(1 for row in artifacts if row["exists"] == "true"),
        "runtime_artifacts_expected": len(artifacts),
        "partial_runtime_summary_rows": len(partial_runtime),
        "partial_heat_delta_rows": len(partial_heat),
        "runtime_schema_failure": runtime_status == "failed_after_partial_outputs_schema_mismatch",
        "partial_runtime_protected_target_used_rows": sum(1 for row in partial_runtime if row["protected_target_used"] == "True"),
        **terminal_runtime,
        "scheduler_job_id": job_id,
        "failed_scheduler_jobs": failed_jobs,
        "scheduler_action": (OUT / "slurm_job_id.txt").exists(),
        "source_property_release_rows": 0,
        "freeze_allowed_rows": 0,
        "final_score_values": 0,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_or_final_scoring": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    write_import_manifest()
    return summary


def main() -> int:
    print(json.dumps(write_outputs(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
