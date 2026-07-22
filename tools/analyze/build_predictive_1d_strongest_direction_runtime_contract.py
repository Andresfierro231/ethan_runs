#!/usr/bin/env python3
"""Build the strongest-current predictive 1D runtime contract packet.

This is a local implementation scaffold, not an admitted model release.  It
combines the completed bulk heat-partition, open-CV residual-contract, and
PASSIVE-H2 packets into a reproducible reference kernel and execution gate
package.  It does not edit Fluid, launch solvers, fit coefficients, score
protected rows, or release source/property or wall-integral values.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-PREDICTIVE-1D-STRONGEST-DIRECTION-RUNTIME-CONTRACT-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_predictive_1d_strongest_direction_runtime_contract"
)

PACKAGES = {
    "blocker_workthrough": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_1d_blocker_workthrough_progress",
    "bulk_partition": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility",
    "open_cv_contract": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract",
    "passive_h2": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet",
    "source_property_unblock": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_source_property_release_unblock_study",
}

GUARDRAILS = {
    "native_solver_outputs_mutated": False,
    "registry_or_admission_mutated": False,
    "scheduler_action": False,
    "solver_postprocessing_sampler_harvest_uq_launched": False,
    "fluid_or_external_edit": False,
    "thesis_body_or_latex_edit": False,
    "source_property_release": False,
    "wall_integral_release": False,
    "numeric_passive_loss_release": False,
    "validation_holdout_external_scoring": False,
    "fitting_or_model_selection": False,
    "coefficient_admission": False,
    "candidate_freeze": False,
    "final_score_claim": False,
    "s11_s12_s13_s15_s6_trigger": False,
    "runtime_leakage_relaxation": False,
    "hidden_multiplier": False,
    "residual_absorbed_into_internal_Nu": False,
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
        PACKAGES["blocker_workthrough"] / "summary.json",
        PACKAGES["blocker_workthrough"] / "execution_readiness_gates.csv",
        PACKAGES["blocker_workthrough"] / "fluid_runtime_handoff_requirements.csv",
        PACKAGES["bulk_partition"] / "summary.json",
        PACKAGES["bulk_partition"] / "partition_stability_summary.csv",
        PACKAGES["open_cv_contract"] / "summary.json",
        PACKAGES["open_cv_contract"] / "required_input_matrix.csv",
        PACKAGES["open_cv_contract"] / "throughflow_enthalpy_harvest_contract.csv",
        PACKAGES["open_cv_contract"] / "residual_equation_contract.csv",
        PACKAGES["passive_h2"] / "summary.json",
        PACKAGES["passive_h2"] / "implementation_handoff_contract.csv",
        PACKAGES["passive_h2"] / "corrected_operator_family_ledger.csv",
        PACKAGES["passive_h2"] / "runtime_input_audit.csv",
        PACKAGES["source_property_unblock"] / "summary.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing predictive 1D contract inputs: " + "; ".join(missing))


def numeric(value: Any) -> float:
    return float(str(value).strip())


def load_summaries() -> dict[str, dict[str, Any]]:
    return {name: read_json(path / "summary.json") for name, path in PACKAGES.items() if (path / "summary.json").exists()}


def passive_case_totals() -> list[dict[str, Any]]:
    rows = read_csv(PACKAGES["passive_h2"] / "corrected_operator_family_ledger.csv")
    totals: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = row["case_id"]
        bucket = totals.setdefault(
            case_id,
            {
                "case_id": case_id,
                "split_role": row["external_bc_split_role"],
                "component_count": 0,
                "diagnostic_convective_W": 0.0,
                "diagnostic_radiative_W": 0.0,
                "diagnostic_total_W": 0.0,
            },
        )
        bucket["component_count"] += 1
        bucket["diagnostic_convective_W"] += numeric(row["corrected_q_conv_W"])
        bucket["diagnostic_radiative_W"] += numeric(row["corrected_q_rad_W"])
        bucket["diagnostic_total_W"] += numeric(row["corrected_q_total_W"])
    return [
        {
            **bucket,
            "runtime_use": "target_only_until_runtime_operator_moves_heat_ledger",
            "score_use": "forbidden_until_candidate_freeze_and_split_gate",
        }
        for _, bucket in sorted(totals.items())
    ]


def build_runtime_schema() -> list[dict[str, Any]]:
    return [
        {
            "field": "case_id",
            "unit": "label",
            "required": True,
            "runtime_legal": True,
            "source": "case setup",
            "contract": "identifier only; no score label logic",
        },
        {
            "field": "heater_power_setpoint_W",
            "unit": "W",
            "required": True,
            "runtime_legal": True,
            "source": "setup thermal-boundary ledger",
            "contract": "external forcing, not a diagnostic wall integral",
        },
        {
            "field": "passive_segment_area_m2",
            "unit": "m2",
            "required": True,
            "runtime_legal": True,
            "source": "geometry trace",
            "contract": "segment-local passive boundary geometry",
        },
        {
            "field": "passive_segment_emissivity",
            "unit": "1",
            "required": True,
            "runtime_legal": True,
            "source": "material/source-basis table",
            "contract": "predeclared physical property; no fitted multiplier",
        },
        {
            "field": "ambient_temperature_K",
            "unit": "K",
            "required": True,
            "runtime_legal": True,
            "source": "room/surroundings setup source",
            "contract": "independent boundary source, not an observed validation temperature",
        },
        {
            "field": "surroundings_temperature_K",
            "unit": "K",
            "required": True,
            "runtime_legal": True,
            "source": "room/surroundings setup source",
            "contract": "radiation sink temperature from source basis",
        },
        {
            "field": "model_solved_wall_temperature_K",
            "unit": "K",
            "required": True,
            "runtime_legal": True,
            "source": "1D state",
            "contract": "solved state only; forbidden wallHeatFlux and observed temperature inputs remain excluded",
        },
        {
            "field": "throughflow_enthalpy_W",
            "unit": "W",
            "required": False,
            "runtime_legal": False,
            "source": "blocked endpoint/property harvest",
            "contract": "explicit missing lane until same-basis endpoints and cp evidence are released",
        },
        {
            "field": "storage_and_named_losses_W",
            "unit": "W",
            "required": False,
            "runtime_legal": False,
            "source": "blocked owner ledger",
            "contract": "must remain explicit; never hidden in internal Nu",
        },
    ]


def build_candidate_blueprint(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "P1D-BULK-CV-H2-CAND001",
            "candidate_status": "executable_contract_only_not_frozen",
            "model_form": "bulk_integral_heat_partition + residual_complete_open_cv + passive_h2_runtime_boundary",
            "working_piece_now": "reference passive-boundary and open-CV accounting kernel generated in this package",
            "strongest_evidence": (
                f"bulk fraction diagnostic range {summaries['bulk_partition']['F_wall_range']}; "
                f"PASSIVE-H2 corrected total target envelope {summaries['passive_h2']['corrected_total_min_W']}.."
                f"{summaries['passive_h2']['corrected_total_max_W']} W"
            ),
            "blocked_before_train_execution": "runtime heat-ledger movement; source/property release; same-basis throughflow endpoints",
            "blocked_before_freeze": "one predeclared train-only candidate must pass legal-runtime, split, UQ, and no-score gates",
            "forbidden_shortcut": "no global multiplier; no residual absorption; no protected scoring; no wall-integral target as runtime input",
        }
    ]


def build_execution_plan() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "row_to_claim": "TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22",
            "purpose": "implement segment-local outer insulation convection/radiation operator",
            "acceptance": "analytic tests pass and radiation-enabled heat ledger moves on train-context cases",
            "may_run_now_from_this_packet": False,
            "reason": "requires separate external/runtime path claim",
        },
        {
            "order": 2,
            "row_to_claim": "TODO-SOURCE-PROPERTY-ROW-SPECIFIC-RELEASE-REPAIR-2026-07-22",
            "purpose": "repair strict source/property provenance for candidate rows",
            "acceptance": "nonzero release-ready rows without source/property leakage into runtime",
            "may_run_now_from_this_packet": False,
            "reason": "current release-ready count remains zero",
        },
        {
            "order": 3,
            "row_to_claim": "TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-CP-HARVEST-PREFLIGHT-2026-07-22",
            "purpose": "make open-CV residual computable on a same-basis window",
            "acceptance": "endpoint masks, signed flow, bulk temperatures, cp basis, storage/named loss lanes are all explicit",
            "may_run_now_from_this_packet": False,
            "reason": "sampler/harvest launch is outside this row",
        },
        {
            "order": 4,
            "row_to_claim": "TODO-P1D-BULK-CV-H2-TRAIN-ONLY-CANDIDATE-SMOKE-2026-07-22",
            "purpose": "run the first one-candidate train-only smoke after prerequisites pass",
            "acceptance": "same-QOI train-only report with no protected score, no fit, no coefficient admission",
            "may_run_now_from_this_packet": False,
            "reason": "blocked until rows 1-3 pass",
        },
    ]


def build_kernel_text() -> str:
    return '''#!/usr/bin/env python3
"""Reference kernel for the P1D-BULK-CV-H2 candidate contract.

Generated by build_predictive_1d_strongest_direction_runtime_contract.py.
This module is an executable specification.  It contains physical accounting
functions and explicit refusal states; it is not a released or frozen model.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


SIGMA_W_M2_K4 = 5.670374419e-8


@dataclass(frozen=True)
class PassiveSegment:
    name: str
    area_m2: float
    h_external_W_m2_K: float
    emissivity: float
    surface_temperature_K: float
    ambient_temperature_K: float
    surroundings_temperature_K: float


def _finite_nonnegative(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")


def exterior_convection_W(segment: PassiveSegment) -> float:
    _finite_nonnegative("area_m2", segment.area_m2)
    _finite_nonnegative("h_external_W_m2_K", segment.h_external_W_m2_K)
    return segment.area_m2 * segment.h_external_W_m2_K * (
        segment.surface_temperature_K - segment.ambient_temperature_K
    )


def exterior_radiation_W(segment: PassiveSegment) -> float:
    _finite_nonnegative("area_m2", segment.area_m2)
    _finite_nonnegative("emissivity", segment.emissivity)
    if segment.emissivity > 1.0:
        raise ValueError("emissivity must be <= 1")
    return (
        segment.emissivity
        * SIGMA_W_M2_K4
        * segment.area_m2
        * (segment.surface_temperature_K**4 - segment.surroundings_temperature_K**4)
    )


def passive_segment_loss_W(segment: PassiveSegment, radiation_on: bool = True) -> dict[str, float]:
    q_conv = exterior_convection_W(segment)
    q_rad = exterior_radiation_W(segment) if radiation_on else 0.0
    return {"convective_W": q_conv, "radiative_W": q_rad, "total_W": q_conv + q_rad}


def passive_total_loss_W(segments: list[PassiveSegment], radiation_on: bool = True) -> dict[str, float]:
    totals = {"convective_W": 0.0, "radiative_W": 0.0, "total_W": 0.0}
    for segment in segments:
        row = passive_segment_loss_W(segment, radiation_on=radiation_on)
        for key in totals:
            totals[key] += row[key]
    return totals


def open_cv_residual_W(
    heater_power_setpoint_W: float,
    passive_loss_W: float,
    throughflow_enthalpy_W: float | None,
    storage_W: float | None,
    named_losses_W: float | None,
) -> dict[str, object]:
    missing = []
    if throughflow_enthalpy_W is None:
        missing.append("throughflow_enthalpy_W")
    if storage_W is None:
        missing.append("storage_W")
    if named_losses_W is None:
        missing.append("named_losses_W")
    if missing:
        return {"computable": False, "missing": missing, "residual_W": None}
    residual = heater_power_setpoint_W - passive_loss_W - throughflow_enthalpy_W - storage_W - named_losses_W
    return {"computable": True, "missing": [], "residual_W": residual}
'''


def build_source_manifest() -> list[dict[str, Any]]:
    files = [
        PACKAGES["blocker_workthrough"] / "summary.json",
        PACKAGES["blocker_workthrough"] / "execution_readiness_gates.csv",
        PACKAGES["blocker_workthrough"] / "fluid_runtime_handoff_requirements.csv",
        PACKAGES["bulk_partition"] / "summary.json",
        PACKAGES["bulk_partition"] / "partition_stability_summary.csv",
        PACKAGES["open_cv_contract"] / "summary.json",
        PACKAGES["open_cv_contract"] / "required_input_matrix.csv",
        PACKAGES["open_cv_contract"] / "throughflow_enthalpy_harvest_contract.csv",
        PACKAGES["open_cv_contract"] / "residual_equation_contract.csv",
        PACKAGES["passive_h2"] / "summary.json",
        PACKAGES["passive_h2"] / "implementation_handoff_contract.csv",
        PACKAGES["passive_h2"] / "corrected_operator_family_ledger.csv",
        PACKAGES["passive_h2"] / "runtime_input_audit.csv",
        PACKAGES["source_property_unblock"] / "summary.json",
    ]
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "use": "read-only evidence",
            "native_or_external_mutation": False,
        }
        for path in files
    ]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_predictive_1d_blocker_workthrough_progress/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet/summary.json
tags: [work-product, predictive-1d, runtime-contract, passive-h2, open-cv, no-release, no-score]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/predictive-1d-strongest-direction-runtime-contract.md
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: complete
---
# Predictive 1D Strongest Direction Runtime Contract

Decision: `{summary["decision"]}`.

This package makes the strongest current predictive 1D direction concrete
without admitting it. The generated reference kernel can compute segment-local
PASSIVE-H2 exterior convection/radiation and open-CV residual accounting when
legal inputs are supplied. It refuses to compute the residual when throughflow,
storage, or named loss lanes are missing.

Current outcome:

- Strongest candidate: `P1D-BULK-CV-H2-CAND001`.
- Working local piece: executable reference kernel plus input/output schema.
- Immediate executable next row: `TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22`.
- Top blockers remain source/property release and same-basis throughflow/open-CV terms.
- No external runtime edit, score, fit, freeze, coefficient admission, or source/property release occurred.
"""


def main() -> int:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = load_summaries()
    passive_totals = passive_case_totals()
    partition_summary = read_csv(PACKAGES["bulk_partition"] / "partition_stability_summary.csv")
    open_cv_inputs = read_csv(PACKAGES["open_cv_contract"] / "required_input_matrix.csv")
    handoff = read_csv(PACKAGES["blocker_workthrough"] / "fluid_runtime_handoff_requirements.csv")

    runtime_schema = build_runtime_schema()
    candidate_blueprint = build_candidate_blueprint(summaries)
    execution_plan = build_execution_plan()
    source_manifest = build_source_manifest()

    write_csv(
        OUT / "runtime_input_schema.csv",
        runtime_schema,
        ["field", "unit", "required", "runtime_legal", "source", "contract"],
    )
    write_csv(
        OUT / "train_context_passive_h2_targets.csv",
        passive_totals,
        [
            "case_id",
            "split_role",
            "component_count",
            "diagnostic_convective_W",
            "diagnostic_radiative_W",
            "diagnostic_total_W",
            "runtime_use",
            "score_use",
        ],
    )
    write_csv(
        OUT / "candidate_blueprint.csv",
        candidate_blueprint,
        [
            "candidate_id",
            "candidate_status",
            "model_form",
            "working_piece_now",
            "strongest_evidence",
            "blocked_before_train_execution",
            "blocked_before_freeze",
            "forbidden_shortcut",
        ],
    )
    write_csv(
        OUT / "execution_plan.csv",
        execution_plan,
        ["order", "row_to_claim", "purpose", "acceptance", "may_run_now_from_this_packet", "reason"],
    )
    write_csv(
        OUT / "bulk_partition_prior.csv",
        partition_summary,
        [
            "metric",
            "case_count",
            "min",
            "max",
            "mean",
            "range",
            "population_std",
            "coefficient_of_variation",
            "stability_status",
            "qwall_medium_fine_max_spread_percent",
            "qwall_temporal_max_relative_percent",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "open_cv_missing_terms.csv",
        open_cv_inputs,
        ["input_label", "unit", "formula_or_definition", "current_status", "release_ready", "next_required_action"],
    )
    write_csv(
        OUT / "runtime_handoff_gate_status.csv",
        handoff,
        ["handoff_family", "requirement_id", "requirement", "required", "acceptance_signal", "source_path"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        source_manifest,
        ["source_path", "exists", "use", "native_or_external_mutation"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [{"guardrail": key, "pass": value is False, "value": value} for key, value in GUARDRAILS.items()],
        ["guardrail", "pass", "value"],
    )

    kernel_path = OUT / "predictive_1d_reference_kernel.py"
    kernel_path.write_text(build_kernel_text(), encoding="utf-8")

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "strongest_predictive_1d_runtime_contract_working_locally_no_release_no_freeze",
        "candidate_id": "P1D-BULK-CV-H2-CAND001",
        "next_model_direction": summaries["blocker_workthrough"]["next_model_direction"],
        "top_remaining_blocker": summaries["blocker_workthrough"]["top_remaining_blocker"],
        "working_artifact": rel(kernel_path),
        "runtime_schema_rows": len(runtime_schema),
        "train_context_case_rows": len(passive_totals),
        "execution_plan_rows": len(execution_plan),
        "open_cv_required_input_rows": len(open_cv_inputs),
        "handoff_gate_rows": len(handoff),
        "passive_h2_runtime_implementation_worth_launching": summaries["passive_h2"]["runtime_implementation_worth_launching"],
        "bulk_integral_partition_diagnostic_ready": summaries["bulk_partition"]["bulk_integral_partition_diagnostic_ready"],
        "same_basis_residual_computable_rows": summaries["open_cv_contract"]["same_basis_residual_computable_rows"],
        "source_property_release_ready_rows": summaries["source_property_unblock"].get("atlas_release_ready_rows", 0),
        **GUARDRAILS,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
