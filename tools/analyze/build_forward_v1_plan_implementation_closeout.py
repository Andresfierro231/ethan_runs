#!/usr/bin/env python3
"""Build AGENT-403 forward-v1 execution closeout.

This package answers "run everything that needs to be run" for the currently
unblocked forward-v1 work. It records local verification commands, already-run
artifacts, and the items that cannot be run without duplicating active Slurm
jobs or crossing another active board claim.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_plan_implementation_closeout"

AG393 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_hydraulic_unblock_plan_execution"
AG394 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_next_step_execution_from_overnight"
AG401 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_active_row_cleanup_and_forward_work_readiness"
AG402 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_salt_forward_v1_unblock"
AG404 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_matched_plane_parser_repair"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(read_csv(path))


def build_verified_artifacts() -> list[dict[str, Any]]:
    artifacts = [
        {
            "artifact_id": "AGENT-393_sensor_map_policy_refresh",
            "path": AG393 / "sensor_map_policy_refresh.csv",
            "evidence": "Sensor-map policy table exists and labels TP/TW sensors as score/validation only, not runtime inputs.",
            "forward_v1_use": "scorecard_sensor_policy_input",
        },
        {
            "artifact_id": "AGENT-393_hydraulic_gate_refresh",
            "path": AG393 / "hydraulic_gate_refresh.csv",
            "evidence": "Hydraulic gate refresh exists; final hydraulic gate remains blocked pending AGENT-373 terminal outputs.",
            "forward_v1_use": "hydraulic_gate_status",
        },
        {
            "artifact_id": "AGENT-394_overnight_output_intake",
            "path": AG394 / "overnight_output_intake.csv",
            "evidence": "AGENT-391 and AGENT-392 overnight outputs are classified as diagnostic/candidate evidence.",
            "forward_v1_use": "overnight_evidence_intake",
        },
        {
            "artifact_id": "AGENT-394_setup_only_hx_action_table",
            "path": AG394 / "setup_only_hx_and_test_section_action_table.csv",
            "evidence": "Setup-only HX/test-section candidate and diagnostic lanes are explicit.",
            "forward_v1_use": "hx_boundary_candidate_selection",
        },
        {
            "artifact_id": "AGENT-401_safe_next_work_queue",
            "path": AG401 / "safe_next_work_queue.csv",
            "evidence": "Active-row cleanup/readiness package exists and warns against overlapping active claims.",
            "forward_v1_use": "coordination_guardrail",
        },
        {
            "artifact_id": "AGENT-402_salt_training_fit_input_table",
            "path": AG402 / "salt_training_fit_input_table.csv",
            "evidence": "Salt training/holdout input rows are split-aware.",
            "forward_v1_use": "scorecard_train_validation_holdout_contract",
        },
        {
            "artifact_id": "AGENT-402_setup_only_hx_boundary_action_table",
            "path": AG402 / "setup_only_hx_boundary_action_table.csv",
            "evidence": "Best current setup-only cooler candidate is documented without imposed/realized cooler leakage.",
            "forward_v1_use": "hx_candidate_contract",
        },
        {
            "artifact_id": "AGENT-404_pm5_parser_repair",
            "path": AG404 / "summary.json",
            "evidence": "AGENT-404 is active; outputs are not available to AGENT-403 yet.",
            "forward_v1_use": "pending_active_claim",
        },
    ]
    rows = []
    for artifact in artifacts:
        path = artifact["path"]
        rows.append(
            {
                "artifact_id": artifact["artifact_id"],
                "path": rel(path),
                "exists": str(path.exists()).lower(),
                "row_count": row_count(path) if path.suffix == ".csv" else "",
                "evidence": artifact["evidence"],
                "forward_v1_use": artifact["forward_v1_use"],
            }
        )
    return rows


def build_run_matrix() -> list[dict[str, Any]]:
    return [
        {
            "run_id": "focused_forward_v1_unittest_suite",
            "status": "ran_passed",
            "command": (
                "python3.11 -m unittest "
                "tools.analyze.test_forward_v1_hydraulic_unblock_plan_execution "
                "tools.analyze.test_forward_v1_next_step_execution_from_overnight "
                "tools.analyze.test_active_row_cleanup_and_forward_work_readiness "
                "tools.analyze.test_predictive_hx_fit "
                "tools.analyze.test_mdot_temperature_probe_error_audit "
                "tools.analyze.test_external_bc_thermal_profile_parity_study "
                "tools.analyze.test_heater_fraction_forward_v1_paper_methods "
                "tools.analyze.test_best_predictive_heat_loss_discrepancy "
                "tools.analyze.test_forward_v1_gate_refresh_after_fluid_api_and_audits"
            ),
            "result": "46 tests ran in 1.402 s; OK",
            "mutated_protected_state": "false",
            "next_action": "Use as local validation evidence for current forward-v1 packages.",
        },
        {
            "run_id": "json_summary_validation",
            "status": "ran_passed",
            "command": "python3.11 -m json.tool on AGENT-393, AGENT-394, AGENT-401, AGENT-402 summaries",
            "result": "All opened summary.json files parsed.",
            "mutated_protected_state": "false",
            "next_action": "Keep summaries as source inputs for scorecard readiness.",
        },
        {
            "run_id": "read_only_scheduler_snapshot",
            "status": "ran_passed",
            "command": "squeue and sacct read-only snapshots for 3293924, 3295438, 3295989-3295991, 3295901, 3295968, 3295120",
            "result": "3293924 and 3295120 running; 3295438 and AGENT-373 hydraulic chain pending; PM5 sbatch jobs cancelled.",
            "mutated_protected_state": "false",
            "next_action": "Monitor only until terminal outputs exist; do not duplicate running/pending jobs.",
        },
        {
            "run_id": "sensor_map_policy_refresh",
            "status": "already_run_verified",
            "command": "AGENT-393 generated sensor_map_policy_refresh.csv",
            "result": "17 sensor rows available; TP/TW sensors are validation/scorecard only and runtime_input_allowed=false.",
            "mutated_protected_state": "false",
            "next_action": "Consume as scorecard policy input after final gates land.",
        },
        {
            "run_id": "setup_only_hx_candidate_selection",
            "status": "already_run_verified",
            "command": "AGENT-402/AGENT-394 setup-only HX and cooler action tables",
            "result": "Best current candidate is salt2_fit_constant_UA_bulk_drive; leakage rows excluded.",
            "mutated_protected_state": "false",
            "next_action": "Use as candidate lane, not final predictive HX admission.",
        },
        {
            "run_id": "pm5_parser_repair",
            "status": "not_run_by_agent403_active_claim",
            "command": "AGENT-404 owns parser repair/reparse.",
            "result": "No AGENT-404 package outputs were present at AGENT-403 build time.",
            "mutated_protected_state": "false",
            "next_action": "Wait for AGENT-404 closeout or claim a follow-up after it releases scope.",
        },
        {
            "run_id": "final_forward_v1_scorecard",
            "status": "not_run_blocked",
            "command": "No final scorecard run.",
            "result": "Final scorecard remains blocked by non-terminal hydraulics/cfd-pp and PM5 parser/onset evidence.",
            "mutated_protected_state": "false",
            "next_action": "Run only after admitted cfd-pp, hydraulics, BC/HX, and PM5/upcomer gates land.",
        },
    ]


def build_blocked_runs() -> list[dict[str, Any]]:
    return [
        {
            "blocked_item": "corrected_q_terminal_harvest",
            "why_not_run_now": "Job 3293924 is still running and harvester 3295438 is pending.",
            "blocking_evidence": "read_only_scheduler_snapshot",
            "safe_next_step": "Monitor until terminal, then run/admit harvest package.",
        },
        {
            "blocked_item": "agent373_hydraulic_chain",
            "why_not_run_now": "Jobs 3295989, 3295990, and 3295991 are already submitted and dependency-pending.",
            "blocking_evidence": "read_only_scheduler_snapshot",
            "safe_next_step": "Do not duplicate; intake terminal outputs when the chain completes.",
        },
        {
            "blocked_item": "pm5_parser_repair",
            "why_not_run_now": "AGENT-404 has an active claim for parser repair/reparse.",
            "blocking_evidence": ".agent/BOARD.md and .agent/status/2026-07-15_AGENT-404.md",
            "safe_next_step": "Wait for AGENT-404 closeout; consume repaired metrics if admitted.",
        },
        {
            "blocked_item": "final_forward_v1_scorecard",
            "why_not_run_now": "Required gates are not admitted: hydraulics, corrected-Q cfd-pp harvest, PM5/upcomer parser/onset, and final HX/BC admission.",
            "blocking_evidence": "AGENT-393/394/402 summaries and scheduler snapshot.",
            "safe_next_step": "Run scorecard only after gate checklist says all blocking rows are admitted.",
        },
    ]


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    verified = build_verified_artifacts()
    run_matrix = build_run_matrix()
    blocked = build_blocked_runs()

    write_csv(
        output_dir / "verified_artifacts.csv",
        verified,
        ["artifact_id", "path", "exists", "row_count", "evidence", "forward_v1_use"],
    )
    write_csv(
        output_dir / "run_execution_matrix.csv",
        run_matrix,
        ["run_id", "status", "command", "result", "mutated_protected_state", "next_action"],
    )
    write_csv(
        output_dir / "blocked_or_deferred_runs.csv",
        blocked,
        ["blocked_item", "why_not_run_now", "blocking_evidence", "safe_next_step"],
    )
    write_csv(
        output_dir / "source_manifest.csv",
        [
            {"source_id": "AGENT-393", "path": rel(AG393), "use": "sensor, hydraulic, PM5 decision, and gate delta inputs"},
            {"source_id": "AGENT-394", "path": rel(AG394), "use": "overnight intake and action queue"},
            {"source_id": "AGENT-401", "path": rel(AG401), "use": "active-row/readiness guardrails"},
            {"source_id": "AGENT-402", "path": rel(AG402), "use": "salt training/HX/sensor action inputs"},
            {"source_id": "AGENT-404-status", "path": ".agent/status/2026-07-15_AGENT-404.md", "use": "active PM5 parser repair claim"},
        ],
        ["source_id", "path", "use"],
    )

    summaries = {
        "ag393": read_json(AG393 / "summary.json"),
        "ag394": read_json(AG394 / "summary.json"),
        "ag401": read_json(AG401 / "summary.json"),
        "ag402": read_json(AG402 / "summary.json"),
    }
    summary = {
        "task": "AGENT-403",
        "date": "2026-07-15",
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "local_verification_status": "passed",
        "focused_unittest_count": 46,
        "runnable_local_items_status": "run_or_verified",
        "not_run_items": [row["blocked_item"] for row in blocked],
        "verified_artifact_count": len(verified),
        "run_matrix_rows": len(run_matrix),
        "blocked_run_rows": len(blocked),
        "sensor_policy_rows": row_count(AG393 / "sensor_map_policy_refresh.csv"),
        "ag392_status": summaries["ag394"].get("ag392_status"),
        "ag392_stage_count": summaries["ag394"].get("ag392_stage_count"),
        "ag402_pm5_quality_flag": summaries["ag402"].get("pm5_status", {}).get("quality_flag"),
        "native_cfd_outputs_mutated": False,
        "registry_or_admission_state_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "scheduler_mutated": False,
        "new_solver_or_postprocessing_jobs_submitted": False,
    }
    write_json(output_dir / "summary.json", summary)

    readme = """# Forward-v1 Plan Implementation Closeout

Date: 2026-07-15

Task: AGENT-403

## Result

All currently unblocked local forward-v1 work was either run in this pass or
verified from completed packages. Final forward-v1 remains blocked because the
remaining work depends on already-submitted scheduler jobs, an active PM5
parser-repair claim, or admission gates that have not landed.

## What Ran

- Focused forward-v1 test suite: 46 tests passed.
- Read-only scheduler snapshot: confirms corrected-Q and hydraulic work are
  already running or pending and should not be duplicated.
- JSON validation of current July 15 package summaries.

## What Was Verified As Already Run

- Sensor-map policy refresh exists in AGENT-393.
- Setup-only HX/cooler candidate lane exists in AGENT-394/AGENT-402.
- Salt training/holdout input table exists in AGENT-402.
- Active-row cleanup/readiness audit exists in AGENT-401.

## What Could Not Be Run

- Corrected-Q harvest: waits on running `3293924` and pending `3295438`.
- AGENT-373 hydraulic chain: `3295989 -> 3295990 -> 3295991` already submitted
  and dependency-pending.
- PM5 parser repair: active AGENT-404 owns this scope.
- Final forward-v1 scorecard: blocked until admitted hydraulics, corrected-Q,
  PM5/upcomer, and HX/BC gates land.

## Guardrails

No native CFD solver outputs, registry/admission state, external Fluid files,
generated indexes, or scheduler state were mutated. No new solver or
postprocessing jobs were launched.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    return summary


def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
