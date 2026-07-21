#!/usr/bin/env python3
"""Build the upcomer exchange-cell compute-execution gate package.

This is a readiness/execution-handoff task. It inventories the queued source
windows and writes a future compute-node scaffold, but it deliberately does not
submit jobs or mutate CFD/native OpenFOAM directories.
"""

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

TASK_ID = "TODO-UPCOMER-EXCHANGE-SAMPLER-COMPUTE-EXECUTION-2026-07-21"
PACKAGE_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution"
)
CONTRACT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_upcomer_exchange_evidence_extraction"
)
DESIGN_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design"
)
CASE_QUEUE = CONTRACT_DIR / "case_time_window_queue.csv"
SCHEMA = DESIGN_DIR / "exchange_sampler_required_schema.csv"

PRIMARY_FIELDS = ("U", "T", "rho", "p_rgh", "Re", "Pr", "Ri", "Gr", "Ra")
DERIVED_DIAGNOSTICS = ("cellVolume", "recircMask_or_U_fallback", "mu", "wallHeatFlux")
BLOCKING_DIAGNOSTICS = ("cellVolume",)

CASE_SOURCES: dict[str, dict[str, str]] = {
    "salt2_jin_nominal_continuation": {
        "source_case_path": (
            "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
            "runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation"
        ),
        "existing_recon_case_path": "tmp/2026-06-30_claude_action_items/recon_salt2_of13",
    },
    "salt3_jin_nominal_continuation": {
        "source_case_path": (
            "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
            "runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation"
        ),
        "existing_recon_case_path": "tmp/2026-06-30_claude_action_items/recon_salt3_of13",
    },
    "salt4_jin_nominal_continuation": {
        "source_case_path": (
            "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/"
            "runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation"
        ),
        "existing_recon_case_path": "tmp/2026-06-30_claude_action_items/recon_salt4_of13",
    },
}

READINESS_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "source_case_path",
    "existing_recon_case_path",
    "source_case_exists",
    "existing_recon_time_dir_exists",
    "processor_time_dir_exists",
    "present_primary_fields",
    "missing_primary_fields",
    "available_diagnostics",
    "derivable_diagnostics",
    "missing_or_untrusted_diagnostics",
    "blocking_missing_diagnostics",
    "execution_status",
    "launch_decision",
    "notes",
]
GAP_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "field_or_diagnostic",
    "needed_for_outputs",
    "current_status",
    "release_path",
    "blocking_for_compute_sample",
    "admission_policy",
]
DECISION_FIELDS = [
    "decision_id",
    "status",
    "submitted",
    "scheduler_action",
    "reason",
    "release_condition",
    "next_task",
]
SCRIPT_FIELDS = ["script_path", "role", "submit_status", "guardrail", "expected_outputs"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
HANDOFF_FIELDS = ["sequence", "task", "objective", "entry_condition", "forbidden_action"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_path(text: str) -> Path:
    candidate = Path(text)
    return candidate if candidate.is_absolute() else ROOT / candidate


def queued_cases() -> list[dict[str, str]]:
    return read_csv(CASE_QUEUE)


def list_time_fields(time_dir: Path) -> set[str]:
    if not time_dir.is_dir():
        return set()
    return {path.name for path in time_dir.iterdir() if path.is_file()}


def readiness_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in queued_cases():
        case_key = row["case_key"]
        sources = CASE_SOURCES[case_key]
        source_case = source_path(sources["source_case_path"])
        recon_case = source_path(sources["existing_recon_case_path"])
        time_s = row["time_window_s"]
        recon_time = recon_case / time_s
        processor_time = source_case / "processors64" / time_s
        fields = list_time_fields(recon_time)
        present_primary = [field for field in PRIMARY_FIELDS if field in fields]
        missing_primary = [field for field in PRIMARY_FIELDS if field not in fields]
        available_diag = [field for field in ("mu", "wallHeatFlux", "cellVolume", "recircMask") if field in fields]
        derivable = ["recircMask_or_U_fallback"] if "U" in fields else []
        if processor_time.is_dir() or recon_time.is_dir():
            derivable.append("wallHeatFlux_via_staged_compute_diagnostic")
        missing_diag = []
        if "cellVolume" not in fields:
            missing_diag.append("cellVolume")
        if "mu" not in fields:
            missing_diag.append("mu_optional_R_mu_unavailable")
        if "wallHeatFlux" not in fields:
            missing_diag.append("wallHeatFlux_not_in_reconstructed_time_dir")
        blocking = [name for name in BLOCKING_DIAGNOSTICS if name in missing_diag]
        launch = "not_submitted"
        status = "blocked_missing_cell_volume_export"
        if missing_primary:
            status = "blocked_missing_primary_fields"
        elif not blocking:
            status = "ready_for_compute_node_submission_from_future_row"
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": case_key,
                "time_window_s": time_s,
                "source_case_path": rel(source_case),
                "existing_recon_case_path": rel(recon_case),
                "source_case_exists": str(source_case.is_dir()).lower(),
                "existing_recon_time_dir_exists": str(recon_time.is_dir()).lower(),
                "processor_time_dir_exists": str(processor_time.is_dir()).lower(),
                "present_primary_fields": ";".join(present_primary),
                "missing_primary_fields": ";".join(missing_primary),
                "available_diagnostics": ";".join(available_diag),
                "derivable_diagnostics": ";".join(derivable),
                "missing_or_untrusted_diagnostics": ";".join(missing_diag),
                "blocking_missing_diagnostics": ";".join(blocking),
                "execution_status": status,
                "launch_decision": launch,
                "notes": (
                    "primary fields exist; compute execution needs a trusted cell-volume "
                    "export before the exchange-cell sampler can assemble V_recirc"
                    if not missing_primary
                    else "primary field repair required before any sampler launch"
                ),
            }
        )
    return rows


def gap_rows(readiness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    needed = {
        "U": "recircMask fallback; mdot_exchange",
        "T": "T_main; T_recirc; wall_core_delta_T",
        "rho": "R_rho; mdot_exchange; tau_recirc",
        "p_rgh": "pressure residual support",
        "Re": "onset/support classification",
        "Pr": "onset/support classification",
        "Ri": "one-stream versus recirculating-flow gate",
        "Gr": "buoyancy support classification",
        "Ra": "buoyancy support classification",
        "cellVolume": "V_recirc; tau_recirc; T_main/T_recirc volume weighting",
        "recircMask_or_U_fallback": "recirculation-cell partition",
        "mu": "R_mu",
        "wallHeatFlux": "wall_core_delta_T support; energy residual diagnostic source term",
    }
    for row in readiness:
        present = set(str(row["present_primary_fields"]).split(";")) if row["present_primary_fields"] else set()
        available = set(str(row["available_diagnostics"]).split(";")) if row["available_diagnostics"] else set()
        derivable = set(str(row["derivable_diagnostics"]).split(";")) if row["derivable_diagnostics"] else set()
        for field in (*PRIMARY_FIELDS, *DERIVED_DIAGNOSTICS):
            if field in present or field in available:
                status = "present_in_reconstructed_time_dir"
                release = "none"
                blocking = "false"
            elif field == "recircMask_or_U_fallback" and field in derivable:
                status = "derivable_from_U_dot_throughflow_normal"
                release = "use dry parser fallback and record recirc_mask_basis"
                blocking = "false"
            elif field == "wallHeatFlux" and "wallHeatFlux_via_staged_compute_diagnostic" in derivable:
                status = "derivable_in_task_owned_staged_case"
                release = "run field-function-object in a scheduler-authorized row"
                blocking = "false"
            elif field == "mu":
                status = "optional_missing"
                release = "emit R_mu_status=not_available_with_reason:missing_mu"
                blocking = "false"
            else:
                status = "missing"
                release = "add trusted cell-volume export or mesh-volume parser before launch"
                blocking = str(field in BLOCKING_DIAGNOSTICS).lower()
            rows.append(
                {
                    "case_id": row["case_id"],
                    "case_key": row["case_key"],
                    "time_window_s": row["time_window_s"],
                    "field_or_diagnostic": field,
                    "needed_for_outputs": needed[field],
                    "current_status": status,
                    "release_path": release,
                    "blocking_for_compute_sample": blocking,
                    "admission_policy": "diagnostic_only_no_fit_no_exchange_cell_admission",
                }
            )
    return rows


def decision_rows(readiness: list[dict[str, Any]]) -> list[dict[str, str]]:
    blocking = sorted({row["blocking_missing_diagnostics"] for row in readiness if row["blocking_missing_diagnostics"]})
    ready = all(row["execution_status"].startswith("ready") for row in readiness)
    return [
        {
            "decision_id": "upcomer_exchange_sampler_submission",
            "status": "not_submitted_blocked" if not ready else "ready_but_not_submitted_by_this_gate",
            "submitted": "false",
            "scheduler_action": "false",
            "reason": (
                "missing trusted cellVolume export for all queued windows"
                if blocking
                else "board row is a gate/package; submission must be a separate scheduler-authorized action"
            ),
            "release_condition": (
                "cellVolume exists in same cell VTK as U/T/rho or parser computes tested mesh cell volumes; "
                "wall heat-flux diagnostic generation remains scheduler-only and scoring/support-only"
            ),
            "next_task": "implement_cell_volume_export_then_submit_exchange_sampler",
        }
    ]


def write_scripts(output_dir: Path, readiness: list[dict[str, Any]]) -> list[dict[str, str]]:
    script_dir = ensure_dir(output_dir / "scripts")
    run_script = script_dir / "run_upcomer_exchange_sampler_compute.sh"
    sbatch = script_dir / "submit_upcomer_exchange_sampler_compute.sbatch"
    case_lines = "\n".join(
        "|".join(
            [
                str(row["case_id"]),
                str(row["case_key"]),
                str(row["time_window_s"]),
                str(row["source_case_path"]),
                str(row["existing_recon_case_path"]),
            ]
        )
        for row in readiness
    )
    run_script.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={ROOT}
OUT="$ROOT/{rel(output_dir)}"
LOG_DIR="$OUT/logs"
mkdir -p "$LOG_DIR"
cd "$ROOT"

log() {{ printf '[%s] %s\\n' "$(date --iso-8601=seconds)" "$*" >&2; }}

cat <<'CASES' > "$OUT/queued_cases.for_future_execution.txt"
{case_lines}
CASES

log "Preflight-only scaffold for {TASK_ID}"
log "No sampler is launched here because cellVolume export is not yet implemented in the exchange-cell VTK path."
log "After the cell-volume exporter is implemented, run the staged OpenFOAM sampling on a compute node only."
exit 2
""",
        encoding="utf-8",
    )
    sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J upx_cell_gate
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 02:00:00
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -o {output_dir}/logs/slurm-%j.out
#SBATCH -e {output_dir}/logs/slurm-%j.err

set -euo pipefail
cd {ROOT}
{run_script}
""",
        encoding="utf-8",
    )
    for path in (run_script, sbatch):
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return [
        {
            "script_path": rel(run_script),
            "role": "preflight_only_future_compute_scaffold",
            "submit_status": "not_submitted",
            "guardrail": "exits before OpenFOAM until cellVolume export is implemented",
            "expected_outputs": "queued_cases.for_future_execution.txt",
        },
        {
            "script_path": rel(sbatch),
            "role": "future_scheduler_submission_template",
            "submit_status": "not_submitted",
            "guardrail": "do not submit until a new board row authorizes scheduler action",
            "expected_outputs": "logs/slurm-<jobid>.out; logs/slurm-<jobid>.err",
        },
    ]


def guard_rows() -> list[dict[str, str]]:
    return [
        {
            "guard_id": "native_outputs",
            "status": "pass_no_mutation",
            "policy": "source and reconstructed OpenFOAM directories are read-only evidence for this gate",
        },
        {
            "guard_id": "scheduler",
            "status": "pass_no_action",
            "policy": "no sbatch, srun, cancel, requeue, or monitor action was performed",
        },
        {
            "guard_id": "login_node",
            "status": "pass_no_openfoam",
            "policy": "no reconstructPar, foamPostProcess, sampler, or solver was run on the login node",
        },
        {
            "guard_id": "diagnostic_heat_flux",
            "status": "pass_scoring_only",
            "policy": "wallHeatFlux is diagnostic/support evidence only and never fit as a predictive parameter",
        },
        {
            "guard_id": "admission",
            "status": "pass_no_admission",
            "policy": "no exchange-cell closure, pressure model, energy residual, Nu, K, or scorecard admission changed",
        },
    ]


def handoff_rows() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "task": "cell_volume_export",
            "objective": "add a trusted same-cell VTK cellVolume source or tested mesh-volume parser",
            "entry_condition": "dry exchange-cell schema and current readiness package are open",
            "forbidden_action": "do not infer V_recirc from planar reverse fractions",
        },
        {
            "sequence": 2,
            "task": "scheduler_authorized_sampler_launch",
            "objective": "stage scratch cases and generate cell/interface/wall VTK rows for the three queued windows",
            "entry_condition": "cellVolume export exists and scripts are updated to call the real sampler",
            "forbidden_action": "do not run OpenFOAM or sampling on the login node",
        },
        {
            "sequence": 3,
            "task": "exchange_residual_harvest",
            "objective": "assemble R_mu, R_rho, V_recirc, mdot_exchange, T_recirc, pressure residual, and energy residual rows",
            "entry_condition": "VTK outputs exist or terminal source-field failures are recorded",
            "forbidden_action": "do not fit coefficients or admit ordinary upcomer closures",
        },
        {
            "sequence": 4,
            "task": "same_qoi_uq_then_claim_review",
            "objective": "pair exchange-cell QOIs with same-window/time/mesh uncertainty before any scoring claim",
            "entry_condition": "sample rows exist and QOI formulas are frozen",
            "forbidden_action": "do not trigger Phase 4B/5/S6 scorecard updates without UQ status",
        },
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/build_upcomer_exchange_sampler_compute_execution.py"),
        Path("tools/extract/test_build_upcomer_exchange_sampler_compute_execution.py"),
        CASE_QUEUE,
        SCHEMA,
        Path("tools/extract/sample_upcomer_exchange_cell.py"),
        Path("tools/extract/sample_upcomer_matched_plane_metrics.py"),
        Path("tmp/2026-06-30_claude_action_items/recon_salt2_of13/7915"),
        Path("tmp/2026-06-30_claude_action_items/recon_salt3_of13/7618"),
        Path("tmp/2026-06-30_claude_action_items/recon_salt4_of13/10000"),
        output_dir,
    ]
    rows = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        task_output = full == output_dir or str(path).startswith("tools/extract/build_upcomer") or str(path).startswith("tools/extract/test_build_upcomer")
        native = str(path).startswith("tmp/2026-06-30")
        rows.append(
            {
                "path": rel(full),
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, sampler, compute-gate]
related:
  - {rel(CONTRACT_DIR)}
  - {rel(DESIGN_DIR)}
---
# Upcomer Exchange-Cell Compute-Execution Gate

This package implements the next rigorous gate after the dry exchange-cell
sampler design. It inventories the queued Salt2/Salt3/Salt4 source windows,
checks field readiness, writes a future compute-node scaffold, and records why
the sampler was not submitted by this row.

## Decision

- queued windows: `{summary["case_rows"]}`
- primary-field-ready windows: `{summary["primary_ready_rows"]}`
- blocking diagnostic gap: `{summary["blocking_gap"]}`
- scheduler action: `false`
- sampler/postprocessing launched: `false`
- fit/admission changed: `false`

The primary reconstructed fields are present for all queued windows, but the
exchange-cell row cannot be assembled with the current VTK path because
`cellVolume` is absent. `mu` remains optional and should emit an unavailable
status for `R_mu`; the recirculation mask can fall back to `U dot n`; wall
heat-flux evidence is diagnostic/support-only and must be generated only in a
task-owned staged case on a compute node.

## Outputs

- `source_case_readiness.csv`: Salt2/Salt3/Salt4 field and diagnostic readiness.
- `required_field_gap.csv`: per-case source/derived field gaps tied to output QOIs.
- `compute_submission_decision.csv`: explicit no-submit decision and release condition.
- `execution_script_plan.csv`: generated script inventory.
- `scripts/`: future no-submit scaffold that exits before OpenFOAM work.
- `next_agent_handoff.csv`: ordered continuation tasks.
- `no_mutation_guardrails.csv`: side-effect and admission guardrails.
- `source_manifest.csv`: read-only context and changed artifacts.

## Guardrails

No native CFD/OpenFOAM output, staged source case, registry/admission state,
scheduler state, Fluid source, external repository, blocker register, or
generated docs index was mutated. No solver, OpenFOAM postprocessor, sampler,
fitting, model selection, ordinary upcomer closure admission, component-K
admission, pressure residual absorption, energy residual absorption, Phase 4B
rescore, Phase 5, or S6 trigger was run.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    readiness = readiness_rows()
    gaps = gap_rows(readiness)
    decisions = decision_rows(readiness)
    scripts = write_scripts(output_dir, readiness)
    guards = guard_rows()
    handoff = handoff_rows()
    manifest = manifest_rows(output_dir)
    csv_dump(output_dir / "source_case_readiness.csv", READINESS_FIELDS, readiness)
    csv_dump(output_dir / "required_field_gap.csv", GAP_FIELDS, gaps)
    csv_dump(output_dir / "compute_submission_decision.csv", DECISION_FIELDS, decisions)
    csv_dump(output_dir / "execution_script_plan.csv", SCRIPT_FIELDS, scripts)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "next_agent_handoff.csv", HANDOFF_FIELDS, handoff)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "case_rows": len(readiness),
        "primary_ready_rows": sum(1 for row in readiness if not row["missing_primary_fields"]),
        "blocking_gap": sorted({row["blocking_missing_diagnostics"] for row in readiness if row["blocking_missing_diagnostics"]}),
        "field_gap_rows": len(gaps),
        "decision_status": decisions[0]["status"],
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "readiness": readiness, "gaps": gaps, "decisions": decisions}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(Path(args.output_dir))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
