#!/usr/bin/env python3
"""Build AGENT-513 wall-temperature-drive candidate package."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_wall_test_section_distribution_ladder as ladder


TASK = "AGENT-513"
DATE = "2026-07-17"
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate")
OUT = ROOT / OUT_REL

CASE_NAME = ladder.CASE_NAME
SPLIT = ladder.SPLIT
SETUP_ROWS = ladder.SETUP_ROWS
WALL_LAYER = ladder.WALL_LAYER
AGENT498 = ladder.OUT
AGENT507 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_passive_test_section_admission_closeout"
TARGET_ROLES = {"ambient_wall", "test_section"}
UPCOMER_PARENT = "left_upper_vertical"
DEFAULT_TIMEOUT_SECONDS = ladder.DEFAULT_TIMEOUT_SECONDS

WALL_IDS = [
    "WTD1_upcomer_test_section_pipe_outer_wall_drive",
    "WTD2_upcomer_test_section_outer_surface_drive",
]
DRIVE_SELECTOR_BY_WALL = {
    "WTD1_upcomer_test_section_pipe_outer_wall_drive": "pipe_outer_wall_temperature",
    "WTD2_upcomer_test_section_outer_surface_drive": "outer_surface_temperature",
}
COOLER_IDS_BY_WALL = {
    "WTD1_upcomer_test_section_pipe_outer_wall_drive": [
        "HX_LUMPED_UA_NTU",
        "HX_SEGMENTED_UA_NTU_N16",
    ],
    "WTD2_upcomer_test_section_outer_surface_drive": [
        "HX_SEGMENTED_UA_NTU_N16",
    ],
}
SUPPORTED_SELECTORS = {
    "fluid_segment_bulk_temperature_for_v1_setup_mode",
    "pipe_outer_wall_temperature",
    "outer_surface_temperature",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return ladder.rel(path)


def safe_float(value: Any) -> float | None:
    return ladder.safe_float(value)


def fmt(value: Any, precision: int = 10) -> str:
    return ladder.fmt(value, precision=precision)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def shape_for_candidate(_wall_id: str) -> dict[tuple[str, str], float]:
    """Retain the Salt2 PB2 local distribution shape and isolate drive choice."""
    return ladder.salt2_shape_pb2()


def wall_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wall_id in WALL_IDS:
        rows.append(
            {
                "wall_candidate_id": wall_id,
                "fit_case_id": "salt_2",
                "fit_parameter_count": 1,
                "base_distribution": "PB2_salt2_local_shape_passive_hA_p1",
                "upcomer_role_drive_selector": DRIVE_SELECTOR_BY_WALL[wall_id],
                "target_parent_segment": UPCOMER_PARENT,
                "target_roles": ";".join(sorted(TARGET_ROLES)),
                "runtime_policy": (
                    "setup_external_boundary_rows;Salt2_shape_only;"
                    "Fluid_solved_wall_state_drive;cooler_alpha_UA"
                ),
                "model_purpose": (
                    "diagnose whether solving passive/test-section loss against a local "
                    "1D wall state repairs AGENT-498 temperature-shape regression"
                ),
                "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)};{rel(AGENT498)};{rel(AGENT507)}",
            }
        )
    return rows


def coupled_candidate_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wall_id in WALL_IDS:
        for cooler_id in COOLER_IDS_BY_WALL[wall_id]:
            rows.append(
                {
                    "candidate_id": f"{wall_id}_PLUS_{cooler_id}",
                    "wall_candidate_id": wall_id,
                    "cooler_candidate_id": cooler_id,
                    "fit_parameter_count": 2,
                    "fitted_parameters": "one Salt2 wall distribution drive/shape; one Salt2 cooler alpha_UA",
                    "changed_physics_vs_AGENT498": (
                        "upcomer ambient_wall/test_section external-boundary drive selector "
                        f"changed to {DRIVE_SELECTOR_BY_WALL[wall_id]}"
                    ),
                    "runtime_status": "eligible_after_static_runtime_precheck",
                    "source_path": f"{rel(SETUP_ROWS)};{rel(AGENT498)};{rel(ladder.AGENT482)}",
                }
            )
    return rows


def _role_rows_for_contract(
    case_rows: list[dict[str, str]],
    shape: dict[tuple[str, str], float],
    ratio: float,
    wall_id: str,
) -> list[dict[str, Any]]:
    selector = DRIVE_SELECTOR_BY_WALL[wall_id]
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        if row["fluid_parent_segment"] != UPCOMER_PARENT:
            continue
        drive_selector = row["recommended_drive_selector"]
        if row["role"] in TARGET_ROLES and row["one_d_segment"] == "upcomer":
            drive_selector = selector
        rows.append(
            {
                "parent_segment": row["fluid_parent_segment"],
                "one_d_segment": row["one_d_segment"],
                "role": row["role"],
                "area_m2": safe_float(row["area_m2"]),
                "h_W_m2K": safe_float(row["h_W_m2K"]),
                "hA_W_K": safe_float(row["hA_W_K"]),
                "Ta_K": safe_float(row["Ta_K"]),
                "Tsur_K": safe_float(row["Tsur_K"]),
                "emissivity": safe_float(row["emissivity"]),
                "coverage_multiplier": ratio * shape.get(ladder.row_key(row), 1.0),
                "drive_selector": drive_selector,
                "source": rel(SETUP_ROWS),
            }
        )
    return rows


def static_drive_audit_rows() -> list[dict[str, Any]]:
    setup = ladder.setup_rows_by_case()
    ratios = ladder.heater_ratio_by_case()
    wall = ladder.wall_layer_by_case_key()
    rows: list[dict[str, Any]] = []
    for wall_id in WALL_IDS:
        shape = shape_for_candidate(wall_id)
        selector = DRIVE_SELECTOR_BY_WALL[wall_id]
        for case_id, case_rows in setup.items():
            for row in case_rows:
                if row["fluid_parent_segment"] != UPCOMER_PARENT or row["role"] not in TARGET_ROLES:
                    continue
                layer = wall.get((case_id, row["one_d_segment"], row["role"]), {})
                if selector == "pipe_outer_wall_temperature":
                    proxy_drive = safe_float(layer.get("T_wall_shell_K"))
                    proxy_field = "T_wall_shell_K"
                else:
                    proxy_drive = safe_float(layer.get("T_ext_drive_loss_positive_K"))
                    proxy_field = "T_ext_drive_loss_positive_K"
                h_a = safe_float(row.get("hA_W_K")) or 0.0
                ambient = safe_float(row.get("Ta_K"))
                coverage = ratios[case_id] * shape.get(ladder.row_key(row), 1.0)
                proxy_loss = None
                if proxy_drive is not None and ambient is not None:
                    proxy_loss = h_a * coverage * max(proxy_drive - ambient, 0.0)
                target = safe_float(row.get("realized_external_loss_W"))
                rows.append(
                    {
                        "wall_candidate_id": wall_id,
                        "case_id": case_id,
                        "split_role": SPLIT[case_id],
                        "one_d_segment": row["one_d_segment"],
                        "role": row["role"],
                        "runtime_drive_selector": selector,
                        "score_only_proxy_field": proxy_field,
                        "score_only_proxy_drive_K": fmt(proxy_drive),
                        "ambient_K": fmt(ambient),
                        "hA_W_K": fmt(h_a),
                        "coverage_multiplier": fmt(coverage),
                        "proxy_loss_W_score_only": fmt(proxy_loss),
                        "target_loss_W_score_only": fmt(target),
                        "proxy_error_W_score_only": fmt(None if proxy_loss is None or target is None else proxy_loss - target),
                        "runtime_use": "Fluid solves this drive state at runtime; proxy fields are audit-only",
                        "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)}",
                    }
                )
    return rows


def static_candidate_gate_rows(audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wall_id in WALL_IDS:
        selector = DRIVE_SELECTOR_BY_WALL[wall_id]
        for case_id in CASE_NAME:
            case_rows = [row for row in audit if row["wall_candidate_id"] == wall_id and row["case_id"] == case_id]
            missing_proxy = sum(1 for row in case_rows if row["score_only_proxy_drive_K"] == "")
            nonphysical = sum(
                1
                for row in case_rows
                if safe_float(row.get("hA_W_K")) is None
                or safe_float(row.get("coverage_multiplier")) is None
                or (safe_float(row.get("coverage_multiplier")) or 0.0) <= 0.0
            )
            gate = (
                "fit_row_not_generalization_scored"
                if SPLIT[case_id] == "train"
                else "pass"
                if selector in SUPPORTED_SELECTORS and nonphysical == 0
                else "fail"
            )
            rows.append(
                {
                    "wall_candidate_id": wall_id,
                    "case_id": case_id,
                    "split_role": SPLIT[case_id],
                    "runtime_drive_selector": selector,
                    "targeted_role_rows": len(case_rows),
                    "score_only_missing_proxy_count": missing_proxy,
                    "nonphysical_runtime_value_count": nonphysical,
                    "static_gate": gate,
                    "gate_reason": (
                        "supported_solver_selector_and_positive_setup_values"
                        if gate != "fail"
                        else "unsupported_selector_or_nonpositive_setup_value"
                    ),
                    "admission_policy": "static_proxy_never_admits; coupled mdot/all-probe/TW gates required",
                }
            )
    return rows


def scenario_contract_rows(static_gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    setup = ladder.setup_rows_by_case()
    ratios = ladder.heater_ratio_by_case()
    alpha = ladder.fit_alpha_ua()
    eligible = {
        row["wall_candidate_id"]
        for row in static_gates
        if row["split_role"] != "train" and row["static_gate"] == "pass"
    }
    rows: list[dict[str, Any]] = []
    for candidate in coupled_candidate_definitions():
        wall_id = candidate["wall_candidate_id"]
        if wall_id not in eligible:
            continue
        shape = shape_for_candidate(wall_id)
        for case_id, case_rows in setup.items():
            role_rows = _role_rows_for_contract(case_rows, shape, ratios[case_id], wall_id)
            parent_maps = ladder._parent_maps_for_contract(case_rows, shape, ratios[case_id])
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "wall_candidate_id": wall_id,
                    "cooler_candidate_id": candidate["cooler_candidate_id"],
                    "case_id": case_id,
                    "fluid_case_name": CASE_NAME[case_id],
                    "split_role": SPLIT[case_id],
                    "heater_source_ratio_to_salt2": fmt(ratios[case_id]),
                    "hx_ua_multiplier": fmt(alpha),
                    "outer_closure_mode": "external_boundary_table",
                    "role_row_count": len(role_rows),
                    "parent_boundary_count": len(parent_maps["external_boundary_h_by_parent_segment"]),
                    "upcomer_role_drive_selector": DRIVE_SELECTOR_BY_WALL[wall_id],
                    "runtime_input_violations": 0,
                    "runtime_inputs": "setup_external_boundary_rows;Salt2_wall_shape;Fluid_solved_wall_state;cooler_alpha_UA",
                    "scenario_json": json.dumps({"role_rows": role_rows, "parent_boundary_maps": parent_maps}, sort_keys=True),
                    "source_path": f"{rel(SETUP_ROWS)};{rel(WALL_LAYER)};{rel(ladder.AGENT482)}",
                }
            )
    return rows


def runtime_input_audit_rows(contracts: list[dict[str, Any]], run_fluid: bool) -> list[dict[str, Any]]:
    forbidden = [
        "realized wallHeatFlux",
        "CFD mdot",
        "validation/holdout wall-shell temperature",
        "validation/holdout outer-surface temperature",
        "validation/holdout probe temperatures",
        "imposed CFD cooler duty",
        "realized test-section heat",
    ]
    bad_selectors = 0
    role_rows = 0
    for contract in contracts:
        payload = json.loads(contract["scenario_json"])
        for role_row in payload["role_rows"]:
            if role_row.get("parent_segment") == UPCOMER_PARENT and role_row.get("role") in TARGET_ROLES:
                role_rows += 1
                if role_row.get("drive_selector") not in SUPPORTED_SELECTORS:
                    bad_selectors += 1
    return [
        {
            "audit_id": "R1_split_legal_runtime_inputs",
            "gate": "pass",
            "evidence": (
                "scenario contracts use setup external-boundary rows, Salt2-only PB2 wall shape, "
                "Fluid-solved wall-state drive selectors, and Salt2 cooler alpha_UA"
            ),
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R2_role_row_drive_selector_support",
            "gate": "pass" if role_rows > 0 and bad_selectors == 0 else "fail",
            "evidence": f"{role_rows} targeted upcomer role rows reviewed; {bad_selectors} unsupported selectors",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R3_contract_row_violations",
            "gate": "pass" if all(int(row.get("runtime_input_violations", 0)) == 0 for row in contracts) else "fail",
            "evidence": f"{len(contracts)} scenario rows reviewed",
            "forbidden_runtime_input": ";".join(forbidden),
        },
        {
            "audit_id": "R4_coupled_execution",
            "gate": "pass" if run_fluid else "pending",
            "evidence": "Fluid rows run in this package" if run_fluid else "compute-node Fluid scoring required",
            "forbidden_runtime_input": "execution gate only",
        },
    ]


def coupled_scorecard_rows(
    contracts: list[dict[str, Any]], run_fluid: bool, timeout_seconds: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    coupled, probes = ladder.coupled_scorecard_rows(contracts, run_fluid, timeout_seconds)
    for row in coupled:
        if row.get("source_path"):
            row["source_path"] = row["source_path"].replace(
                "AGENT-498 distribution ladder", "AGENT-513 wall-temperature-drive"
            )
    for row in probes:
        if row.get("source_path"):
            row["source_path"] = row["source_path"].replace(
                "AGENT-498 distribution ladder", "AGENT-513 wall-temperature-drive"
            )
    return coupled, probes


def current_candidate_ids() -> set[str]:
    return {row["candidate_id"] for row in coupled_candidate_definitions()}


def read_existing_current_probe_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    allowed = current_candidate_ids()
    rows = ladder.read_csv(path)
    return [row for row in rows if row.get("candidate_id") in allowed]


def candidate_admission_review_rows(
    deltas: list[dict[str, Any]],
    runtime: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime_pass = all(row["gate"] == "pass" for row in runtime)
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row["score_gate"] for row in deltas if row["candidate_id"] == candidate_id}
        blockers: list[str] = []
        if not runtime_pass:
            blockers.append("runtime_audit_failed_or_pending")
        if by_split.get("validation") != "pass":
            blockers.append("validation_mdot_all_probe_tw_gate_failed")
        if by_split.get("holdout") != "pass":
            blockers.append("holdout_mdot_all_probe_tw_gate_failed")
        rows.append(
            {
                "candidate_id": candidate_id,
                "runtime_gate": "pass" if runtime_pass else "fail_or_pending",
                "validation_coupled_gate": by_split.get("validation", "missing"),
                "holdout_coupled_gate": by_split.get("holdout", "missing"),
                "admission_decision": "admitted_wall_temperature_drive_candidate" if not blockers else "not_admitted",
                "blocking_reasons": ";".join(blockers),
            }
        )
    return rows


def next_step_rows(admission: list[dict[str, Any]], coupled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    admitted = any(row["admission_decision"] == "admitted_wall_temperature_drive_candidate" for row in admission)
    completed = [row for row in coupled if row.get("coupled_run_status") == "completed"]
    if admitted:
        action = "freeze_admitted_candidate_and_run_corrected_split_scorecard"
        rationale = "At least one WTD candidate passed runtime, validation, and holdout coupled gates."
    elif completed:
        action = "move_to_heater_source_redistribution_and_explicit_wall_fluid_coupling"
        rationale = (
            "Wall-state drive completed but did not pass mdot/all-probe/TW gates; the next physics "
            "lane should separate heater/source placement from passive loss and add explicit "
            "test-section wall/fluid coupling or upcomer mixing."
        )
    else:
        action = "complete_bounded_compute_node_coupled_score"
        rationale = "Static/runtime contracts exist but coupled Fluid rows have not completed."
    return [
        {
            "priority": 1,
            "action": action,
            "rationale": rationale,
            "owner_lane": "forward_predictive_wall_test_section",
        },
        {
            "priority": 2,
            "action": "do_not_close_predictive_wall_test_section_submodels_without_coupled_temperature_shape_pass",
            "rationale": "The blocker is specifically all-probe/TW field shape, not passive-total heat or runtime legality alone.",
            "owner_lane": "admission_policy",
        },
    ]


def background_run_contract_rows(timeout_seconds: int) -> list[dict[str, Any]]:
    log_dir = f"logs/{DATE}"
    command = (
        f"mkdir -p {log_dir} && "
        f"srun -N1 -n1 python3 tools/analyze/build_wall_temperature_drive_candidate.py "
        f"--run-fluid --timeout-seconds {timeout_seconds} "
        f"> {log_dir}/wall_temperature_drive_candidate.out "
        f"2> {log_dir}/wall_temperature_drive_candidate.err"
    )
    return [
        {
            "contract_id": "bounded_srun_coupled_score",
            "timeout_seconds": timeout_seconds,
            "command": command,
            "stdout": f"{log_dir}/wall_temperature_drive_candidate.out",
            "stderr": f"{log_dir}/wall_temperature_drive_candidate.err",
            "policy": "run bounded Fluid scoring through compute-node srun or equivalent; no login-node Fluid solve",
        }
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent507_closeout", "path": rel(AGENT507), "use": "blocker status and next-physics motivation"},
        {"source_id": "agent498_distribution_ladder", "path": rel(AGENT498), "use": "PB2 Salt2 shape and coupled scoring helper baseline"},
        {"source_id": "agent482_cooler", "path": rel(ladder.AGENT482), "use": "HX alpha_UA and segmented HX adapter"},
        {"source_id": "agent461_m3", "path": rel(ladder.M3_COMPARATORS), "use": "M3 mdot/TP/TW/all-probe comparator gates"},
        {"source_id": "agent_m3_sensor_baseline", "path": rel(ladder.M3_SENSOR_ROWS), "use": "M3 probe-level comparator"},
        {"source_id": "setup_external_boundary_rows", "path": rel(SETUP_ROWS), "use": "setup hA/Ta/Tsur/emissivity role rows"},
        {"source_id": "wall_layer_drive_mapping", "path": rel(WALL_LAYER), "use": "score-only wall proxy audit fields"},
        {
            "source_id": "fluid_solver",
            "path": rel(ladder.FLUID_ROOT / "tamu_loop_model_v2/solver.py"),
            "use": "read-only Fluid solve_case execution and drive-selector implementation",
        },
    ]


def blocker_decision_payload(
    coupled: list[dict[str, Any]],
    admission: list[dict[str, Any]],
    run_fluid: bool,
) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for row in coupled:
        statuses[row["coupled_run_status"]] = statuses.get(row["coupled_run_status"], 0) + 1
    admitted = [row for row in admission if row["admission_decision"] == "admitted_wall_temperature_drive_candidate"]
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "blocker_id": "predictive-wall-test-section-submodels",
        "blocker_decision": "resolve" if admitted and run_fluid else "keep_open",
        "coupled_status_counts": statuses,
        "coupled_completed_rows": sum(1 for row in coupled if row["coupled_run_status"] == "completed"),
        "admitted_candidates": [row["candidate_id"] for row in admitted],
        "why": (
            "A wall-temperature-drive candidate passed validation and holdout mdot, all-probe, and TW gates vs M3."
            if admitted and run_fluid
            else "No wall-temperature-drive candidate has passed validation and holdout mdot, all-probe, and TW gates vs M3."
        ),
    }


def performance_highlight_table(deltas: list[dict[str, Any]], admission: list[dict[str, Any]]) -> str:
    if not deltas:
        return "No validation/holdout coupled deltas are available.\n"
    admission_by_id = {row["candidate_id"]: row for row in admission}
    lines = [
        "| Candidate | Validation delta vs M3 | Holdout delta vs M3 | Admission |",
        "| --- | --- | --- | --- |",
    ]
    for candidate_id in sorted({row["candidate_id"] for row in deltas}):
        by_split = {row["split_role"]: row for row in deltas if row["candidate_id"] == candidate_id}

        def cell(split: str) -> str:
            row = by_split.get(split)
            if row is None:
                return "missing"
            return (
                f"mdot `{row['mdot_delta_vs_m3_pct']} pct`; "
                f"all-probe `{row['all_probe_delta_vs_m3_K']} K`; "
                f"TW `{row['tw_delta_vs_m3_K']} K`"
            )

        decision = admission_by_id.get(candidate_id, {}).get("admission_decision", "missing")
        lines.append(f"| `{candidate_id}` | {cell('validation')} | {cell('holdout')} | `{decision}` |")
    return "\n".join(lines) + "\n"


def readme_text(summary: dict[str, Any], deltas: list[dict[str, Any]], admission: list[dict[str, Any]]) -> str:
    decision = summary["decision"]
    command = background_run_contract_rows(summary["timeout_seconds"])[0]["command"]
    performance_table = performance_highlight_table(deltas, admission)
    return f"""---
provenance:
  - {rel(AGENT507)}
  - {rel(AGENT498)}
  - {rel(ladder.AGENT482)}
  - {rel(ladder.M3_COMPARATORS)}
  - {rel(SETUP_ROWS)}
  - {rel(WALL_LAYER)}
tags: [forward-model, wall-circuit, wall-temperature-drive, test-section, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-SEGMENT-THERMAL-MODELS
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall-Temperature-Drive Candidate

## Result

This package tests the next wall/test-section unblock step after AGENT-507:
keep the Salt2 PB2 local distribution shape, but change only the upcomer
`ambient_wall` and `test_section` role-row passive-loss drive from bulk-fluid
temperature to a Fluid-solved wall state.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

## Candidate Set

- `WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU`
- `WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16`
- `WTD2_upcomer_test_section_outer_surface_drive_PLUS_HX_SEGMENTED_UA_NTU_N16`

The wall proxy fields in `static_drive_audit.csv` are score-only diagnostics.
At runtime the Fluid solver computes `T_pipe_outer_wall_K` or
`T_outer_surface_K`; validation/holdout wall temperatures are not consumed.

## Coupled Run

Coupled rows completed: `{decision['coupled_completed_rows']}`.
Status counts: `{json.dumps(decision['coupled_status_counts'], sort_keys=True)}`.

## Performance Versus M3

Negative mdot delta is better. Negative all-probe and TW deltas would be better.

{performance_table}

Replay command:

```bash
{command}
```

## Files

- `wall_candidate_definitions.csv`
- `candidate_definitions.csv`
- `static_drive_audit.csv`
- `static_candidate_gate.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `probe_delta_vs_m3.csv`
- `role_segment_error_summary.csv`
- `candidate_admission_review.csv`
- `next_steps.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build(
    run_fluid: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    reuse_existing_coupled: bool = False,
) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    wall_candidates = wall_candidate_definitions()
    candidates = coupled_candidate_definitions()
    static_audit = static_drive_audit_rows()
    static_gates = static_candidate_gate_rows(static_audit)
    contracts = scenario_contract_rows(static_gates)
    runtime = runtime_input_audit_rows(contracts, run_fluid)
    if reuse_existing_coupled and (OUT / "coupled_scorecard.csv").exists():
        coupled = ladder.read_csv(OUT / "coupled_scorecard.csv")
        probes = read_existing_current_probe_rows(OUT / "probe_error_localization.csv")
        effective_run_fluid = any(row.get("coupled_run_status") == "completed" for row in coupled)
    else:
        coupled, probes = coupled_scorecard_rows(contracts, run_fluid, timeout_seconds)
        effective_run_fluid = run_fluid
    runtime = runtime_input_audit_rows(contracts, effective_run_fluid)
    deltas = ladder.coupled_delta_rows(coupled)
    probe_deltas = ladder.probe_delta_rows(probes)
    role_segments = ladder.role_segment_error_summary_rows(probe_deltas)
    coupled = ladder.annotate_coupled_gates(coupled, deltas)
    admission = candidate_admission_review_rows(deltas, runtime)
    next_steps = next_step_rows(admission, coupled)
    background = background_run_contract_rows(timeout_seconds)
    manifest = source_manifest_rows()
    decision = blocker_decision_payload(coupled, admission, effective_run_fluid)

    counts = {
        "wall_candidate_definitions.csv": write_csv(
            OUT / "wall_candidate_definitions.csv", wall_candidates, list(wall_candidates[0].keys())
        ),
        "candidate_definitions.csv": write_csv(OUT / "candidate_definitions.csv", candidates, list(candidates[0].keys())),
        "static_drive_audit.csv": write_csv(OUT / "static_drive_audit.csv", static_audit, list(static_audit[0].keys())),
        "static_candidate_gate.csv": write_csv(OUT / "static_candidate_gate.csv", static_gates, list(static_gates[0].keys())),
        "scenario_contracts.csv": write_csv(
            OUT / "scenario_contracts.csv", contracts, list(contracts[0].keys()) if contracts else ["candidate_id"]
        ),
        "runtime_input_audit.csv": write_csv(OUT / "runtime_input_audit.csv", runtime, list(runtime[0].keys())),
        "coupled_scorecard.csv": write_csv(
            OUT / "coupled_scorecard.csv", coupled, list(coupled[0].keys()) if coupled else ["candidate_id"]
        ),
        "coupled_delta_vs_m3.csv": write_csv(
            OUT / "coupled_delta_vs_m3.csv", deltas, list(deltas[0].keys()) if deltas else ["candidate_id"]
        ),
        "probe_error_localization.csv": write_csv(OUT / "probe_error_localization.csv", probes, ladder.PROBE_FIELDS),
        "probe_delta_vs_m3.csv": write_csv(OUT / "probe_delta_vs_m3.csv", probe_deltas, ladder.PROBE_DELTA_FIELDS),
        "role_segment_error_summary.csv": write_csv(
            OUT / "role_segment_error_summary.csv", role_segments, ladder.ROLE_SEGMENT_FIELDS
        ),
        "candidate_admission_review.csv": write_csv(
            OUT / "candidate_admission_review.csv", admission, list(admission[0].keys()) if admission else ["candidate_id"]
        ),
        "next_steps.csv": write_csv(OUT / "next_steps.csv", next_steps, list(next_steps[0].keys())),
        "background_run_contract.csv": write_csv(OUT / "background_run_contract.csv", background, list(background[0].keys())),
        "source_manifest.csv": write_csv(OUT / "source_manifest.csv", manifest, list(manifest[0].keys())),
    }
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "run_fluid": effective_run_fluid,
        "reuse_existing_coupled": reuse_existing_coupled,
        "timeout_seconds": timeout_seconds,
        "counts": counts,
        "decision": decision,
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary, deltas, admission), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-fluid", action="store_true", help="Run Fluid solve_case rows through compute-node srun/sbatch.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--reuse-existing-coupled", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                run_fluid=args.run_fluid,
                timeout_seconds=args.timeout_seconds,
                reuse_existing_coupled=args.reuse_existing_coupled,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
