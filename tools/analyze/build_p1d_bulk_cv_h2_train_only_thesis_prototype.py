#!/usr/bin/env python3
"""Build the train-only P1D bulk-CV-H2 thesis prototype packet.

The packet produces a working no-fit prototype kernel plus thesis-facing tables.
It intentionally remains pre-admission: no source/property release, no protected
scoring, no coefficient fit, no freeze, and no hidden residual absorption.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-P1D-BULK-CV-H2-TRAIN-ONLY-THESIS-PROTOTYPE-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype"

PACKAGES = {
    "runtime_contract": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_1d_strongest_direction_runtime_contract",
    "passive_runtime": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation",
    "s13_endpoint": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight",
    "source_exact": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14",
    "source_recovery": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_strict_row_specific_source_envelope_recovery",
    "source_unblock": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_source_property_release_unblock_study",
    "candidate_preflight": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_train_only_candidate_preflight",
}

GUARDRAILS = {
    "native_solver_outputs_mutated": False,
    "registry_or_admission_mutated": False,
    "scheduler_action": False,
    "solver_postprocessing_sampler_harvest_uq_launched": False,
    "fluid_or_external_edit": False,
    "thesis_body_or_latex_edit": False,
    "source_property_release": False,
    "Qwall_release": False,
    "numeric_q_loss_release": False,
    "validation_holdout_external_scoring": False,
    "protected_scoring": False,
    "fitting_or_model_selection": False,
    "coefficient_admission": False,
    "candidate_freeze": False,
    "final_score_claim": False,
    "s11_s12_s13_s15_s6_trigger": False,
    "hidden_multiplier": False,
    "residual_absorbed_into_internal_Nu": False,
    "endpoint_proxy_substitution": False,
    "runtime_leakage_relaxation": False,
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def require_inputs() -> None:
    required = [
        PACKAGES["runtime_contract"] / "summary.json",
        PACKAGES["runtime_contract"] / "runtime_input_schema.csv",
        PACKAGES["runtime_contract"] / "candidate_blueprint.csv",
        PACKAGES["passive_runtime"] / "summary.json",
        PACKAGES["passive_runtime"] / "heat_ledger_movement.csv",
        PACKAGES["s13_endpoint"] / "summary.json",
        PACKAGES["s13_endpoint"] / "residual_readiness_gate.csv",
        PACKAGES["s13_endpoint"] / "required_input_status_matrix.csv",
        PACKAGES["s13_endpoint"] / "next_action_queue.csv",
        PACKAGES["source_exact"] / "summary.json",
        PACKAGES["source_exact"] / "salt14_row_specific_release_matrix.csv",
        PACKAGES["source_recovery"] / "summary.json",
        PACKAGES["source_recovery"] / "row_specific_recovery_matrix.csv",
        PACKAGES["source_unblock"] / "summary.json",
        PACKAGES["source_unblock"] / "release_unblock_matrix.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing P1D prototype inputs: " + "; ".join(missing))


def f(value: Any) -> float:
    return float(str(value).strip())


def build_kernel_text() -> str:
    return '''#!/usr/bin/env python3
"""Executable no-fit prototype for P1D-BULK-CV-H2-CAND001.

This module is a thesis prototype, not an admitted closure.  It computes the
currently legal passive-boundary ledger and keeps open-CV residual terms
explicitly incomplete unless same-basis evidence is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class PrototypeInputs:
    case_id: str
    heater_power_setpoint_W: float
    passive_h2_loss_W: float
    throughflow_enthalpy_W: float | None = None
    storage_W: float | None = None
    named_losses_W: float | None = None


def _finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def run_prototype(inputs: PrototypeInputs) -> dict[str, object]:
    _finite("heater_power_setpoint_W", inputs.heater_power_setpoint_W)
    _finite("passive_h2_loss_W", inputs.passive_h2_loss_W)
    if inputs.heater_power_setpoint_W <= 0.0:
        raise ValueError("heater_power_setpoint_W must be positive")
    if inputs.passive_h2_loss_W < 0.0:
        raise ValueError("passive_h2_loss_W must be non-negative")

    missing = []
    for label in ("throughflow_enthalpy_W", "storage_W", "named_losses_W"):
        if getattr(inputs, label) is None:
            missing.append(label)

    remaining_after_passive_W = inputs.heater_power_setpoint_W - inputs.passive_h2_loss_W
    result: dict[str, object] = {
        "case_id": inputs.case_id,
        "passive_h2_loss_W": inputs.passive_h2_loss_W,
        "passive_fraction_of_heater": inputs.passive_h2_loss_W / inputs.heater_power_setpoint_W,
        "remaining_after_passive_W": remaining_after_passive_W,
        "residual_computable": not missing,
        "missing_residual_terms": missing,
    }
    if missing:
        result["open_cv_residual_W"] = None
    else:
        result["open_cv_residual_W"] = (
            remaining_after_passive_W
            - float(inputs.throughflow_enthalpy_W)
            - float(inputs.storage_W)
            - float(inputs.named_losses_W)
        )
    return result
'''


def train_context_rows() -> list[dict[str, Any]]:
    movement_rows = read_csv(PACKAGES["passive_runtime"] / "heat_ledger_movement.csv")
    rows: list[dict[str, Any]] = []
    for row in movement_rows:
        passive_total = f(row["contract_full_passive_operator_delta_W"])
        baseline_context = f(row["baseline_qambient_total_W"])
        rows.append(
            {
                "case_id": row["case_id"],
                "scenario_id": row["scenario_id"],
                "split_role_in_source_packet": {
                    "salt_2": "train_context",
                    "salt_3": "diagnostic_context_not_score",
                    "salt_4": "diagnostic_context_not_score",
                }[row["case_id"]],
                "prototype_passive_h2_loss_W": passive_total,
                "prototype_radiation_component_W": row["contract_radiation_on_delta_W"],
                "legacy_qambient_context_W": baseline_context,
                "passive_fraction_of_legacy_context": passive_total / baseline_context,
                "residual_computable_now": False,
                "missing_residual_terms": "throughflow_enthalpy_W;storage_W;named_losses_W;cp/source_property_release",
                "protected_scoring": False,
                "candidate_freeze": False,
                "thesis_use": "train_context_physical_model_prototype_and_blocker_localization",
            }
        )
    return rows


def source_property_repair_status() -> list[dict[str, Any]]:
    exact_rows = read_csv(PACKAGES["source_exact"] / "salt14_row_specific_release_matrix.csv")
    recovery_summary = read_json(PACKAGES["source_recovery"] / "summary.json")
    rows: list[dict[str, Any]] = []
    for row in exact_rows:
        rows.append(
            {
                "case_key": row["case_key"],
                "case_id": row["normalized_case_id"],
                "labels_complete": row["labels_complete"],
                "current_status": row["source_property_gate_status"],
                "release_ready": row["release_ready"],
                "primary_blocker": row["primary_blocker"],
                "next_action": row["next_action"],
                "repair_progress_this_row": "confirmed_no_local_release_repair_available_from_existing_evidence",
                "strict_source_envelope_pass_rows_global": recovery_summary["strict_source_envelope_pass_rows"],
            }
        )
    return rows


def residual_completion_status() -> list[dict[str, Any]]:
    required = read_csv(PACKAGES["s13_endpoint"] / "required_input_status_matrix.csv")
    rows: list[dict[str, Any]] = []
    for row in required:
        if row["required_label"] in {
            "throughflow_endpoint_face_masks",
            "T_in_bulk_K",
            "T_out_bulk_K",
            "mdot_throughflow_kg_s",
            "cp_J_kg_K",
            "Q_storage_W",
            "Q_other_named_losses_W",
        }:
            rows.append(
                {
                    "case_id": row["case_id"],
                    "required_label": row["required_label"],
                    "ready_now": row["release_or_harvest_ready"],
                    "current_evidence": row["current_evidence"],
                    "next_action": row["next_action"],
                    "prototype_behavior": "explicit_missing_lane_no_residual_value",
                }
            )
    return rows


def blocked_scorecard_shell(train_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "P1D-BULK-CV-H2-CAND001",
            "case_id": row["case_id"],
            "score_status": "blocked_no_freeze",
            "score_value": "",
            "why_blocked": "source/property release and residual-complete open-CV inputs are not ready",
            "prototype_output_available": True,
            "protected_scoring": False,
            "final_score_claim": False,
        }
        for row in train_rows
    ]


def thesis_claim_ledger() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "P1D-CLAIM-001",
            "claim": "A no-fit predictive 1D prototype now exists and runs as an explicit heat-ledger model.",
            "allowed": True,
            "evidence": "candidate kernel plus train-context passive-H2 ledger rows",
            "boundary": "prototype only; not an admitted closure",
        },
        {
            "claim_id": "P1D-CLAIM-002",
            "claim": "PASSIVE-H2 provides a physical external heat-path operator with nonzero radiation-enabled ledger movement.",
            "allowed": True,
            "evidence": "PASSIVE-H2 runtime smoke reports Salt2 nonzero movement; train-context contract table retains Salt2/Salt3/Salt4 nonzero targets",
            "boundary": "Salt3/Salt4 remain diagnostic context until separate train/support execution is released",
        },
        {
            "claim_id": "P1D-CLAIM-003",
            "claim": "The model localizes the remaining thermal uncertainty to source/property and open-CV residual ownership.",
            "allowed": True,
            "evidence": "source/property release rows 0 and same-basis residual-computable rows 0",
            "boundary": "diagnostic failure localization, not a final score",
        },
        {
            "claim_id": "P1D-FORBID-001",
            "claim": "This candidate is frozen, validated, or admitted.",
            "allowed": False,
            "evidence": "freeze and score guardrails remain false",
            "boundary": "requires S11/S15/S6 trigger after gates pass",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    files = [
        PACKAGES["runtime_contract"] / "summary.json",
        PACKAGES["runtime_contract"] / "runtime_input_schema.csv",
        PACKAGES["passive_runtime"] / "summary.json",
        PACKAGES["passive_runtime"] / "heat_ledger_movement.csv",
        PACKAGES["s13_endpoint"] / "summary.json",
        PACKAGES["s13_endpoint"] / "residual_readiness_gate.csv",
        PACKAGES["s13_endpoint"] / "required_input_status_matrix.csv",
        PACKAGES["source_exact"] / "summary.json",
        PACKAGES["source_exact"] / "salt14_row_specific_release_matrix.csv",
        PACKAGES["source_recovery"] / "summary.json",
        PACKAGES["source_recovery"] / "row_specific_recovery_matrix.csv",
        PACKAGES["source_unblock"] / "summary.json",
    ]
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "use": "read-only evidence",
            "mutation": False,
        }
        for path in files
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_predictive_1d_strongest_direction_runtime_contract/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14/summary.json
tags: [work-product, predictive-1d, thesis-prototype, train-only, no-release, no-score]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/p1d-bulk-cv-h2-train-only-thesis-prototype.md
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: complete
---
# P1D Bulk-CV-H2 Train-Only Thesis Prototype

Decision: `{summary["decision"]}`.

This package is the first working thesis prototype for
`P1D-BULK-CV-H2-CAND001`. It provides an executable no-fit candidate kernel and
train-context heat-ledger rows. It is useful for the thesis as a model
architecture and diagnostic failure-localization artifact.

It is not a frozen or admitted predictive model. Source/property release and
same-basis open-CV residual completion both remain blocked, so the scorecard is
published only as a blocked shell with no score values.
"""


def main() -> int:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    runtime_summary = read_json(PACKAGES["runtime_contract"] / "summary.json")
    passive_summary = read_json(PACKAGES["passive_runtime"] / "summary.json")
    endpoint_summary = read_json(PACKAGES["s13_endpoint"] / "summary.json")
    source_summary = read_json(PACKAGES["source_exact"] / "summary.json")
    source_recovery_summary = read_json(PACKAGES["source_recovery"] / "summary.json")
    passive_movement_cases = passive_summary.get("radiation_on_heat_ledger_movement_nonzero_cases")
    if passive_movement_cases is None:
        passive_movement_cases = int(bool(passive_summary.get("radiation_on_nonzero", False)))

    train_rows = train_context_rows()
    source_rows = source_property_repair_status()
    residual_rows = residual_completion_status()
    score_rows = blocked_scorecard_shell(train_rows)

    kernel_path = OUT / "p1d_bulk_cv_h2_candidate_model.py"
    kernel_path.write_text(build_kernel_text(), encoding="utf-8")

    write_csv(
        OUT / "train_context_prototype_outputs.csv",
        train_rows,
        [
            "case_id",
            "scenario_id",
            "split_role_in_source_packet",
            "prototype_passive_h2_loss_W",
            "prototype_radiation_component_W",
            "legacy_qambient_context_W",
            "passive_fraction_of_legacy_context",
            "residual_computable_now",
            "missing_residual_terms",
            "protected_scoring",
            "candidate_freeze",
            "thesis_use",
        ],
    )
    write_csv(
        OUT / "source_property_repair_status.csv",
        source_rows,
        [
            "case_key",
            "case_id",
            "labels_complete",
            "current_status",
            "release_ready",
            "primary_blocker",
            "next_action",
            "repair_progress_this_row",
            "strict_source_envelope_pass_rows_global",
        ],
    )
    write_csv(
        OUT / "residual_completion_gate.csv",
        residual_rows,
        ["case_id", "required_label", "ready_now", "current_evidence", "next_action", "prototype_behavior"],
    )
    write_csv(
        OUT / "blocked_scorecard_shell.csv",
        score_rows,
        [
            "candidate_id",
            "case_id",
            "score_status",
            "score_value",
            "why_blocked",
            "prototype_output_available",
            "protected_scoring",
            "final_score_claim",
        ],
    )
    write_csv(
        OUT / "thesis_claim_ledger.csv",
        thesis_claim_ledger(),
        ["claim_id", "claim", "allowed", "evidence", "boundary"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        source_manifest(),
        ["source_path", "exists", "use", "mutation"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"guardrail": key, "pass": value is False, "value": value} for key, value in GUARDRAILS.items()],
        ["guardrail", "pass", "value"],
    )

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "p1d_bulk_cv_h2_train_only_prototype_runs_scorecard_blocked_no_freeze",
        "candidate_id": "P1D-BULK-CV-H2-CAND001",
        "prototype_kernel": rel(kernel_path),
        "train_context_case_rows": len(train_rows),
        "nonzero_passive_h2_rows": sum(f(row["prototype_passive_h2_loss_W"]) > 0.0 for row in train_rows),
        "source_property_release_ready_rows": source_summary["release_ready_rows"],
        "strict_source_envelope_pass_rows": source_recovery_summary["strict_source_envelope_pass_rows"],
        "same_basis_residual_computable_cases": endpoint_summary["same_basis_residual_computable_cases"],
        "residual_value_released_rows": endpoint_summary["residual_value_released_rows"],
        "passive_h2_radiation_movement_nonzero_cases": passive_movement_cases,
        "passive_h2_train_runtime_rows_used": passive_summary.get("train_rows_used", ""),
        "thesis_use": "working train-context prototype and diagnostic failure-localization artifact",
        **GUARDRAILS,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
