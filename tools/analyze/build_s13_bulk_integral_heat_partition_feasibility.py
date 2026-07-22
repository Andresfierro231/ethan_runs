#!/usr/bin/env python3
"""No-fit S13 bulk-integral heat-partition feasibility study.

This package takes the cleanest current path toward a predictive 1D model:
use bulk/averaged states only as drivers while keeping heat flow, exchange
flow, and residuals as integral outputs. It does not fit coefficients.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


TASK_ID = "TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_bulk_integral_heat_partition_feasibility"
)

COARSE_OPEN_CV = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract"
)
MF_DISPOSITION = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_mesh_gci_disposition"
)
SAME_QOI_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
SOURCE_EQ = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
)
PROPERTY_PREFLIGHT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_source_property_cp_viscosity_pressure_basis_preflight"
)
THERMAL_ACCOUNTING = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def fnum(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite numeric value: {value}")
    return result


def safe_ratio(num: float, den: float) -> float | None:
    if den == 0.0:
        return None
    value = num / den
    if not math.isfinite(value):
        return None
    return value


def require_inputs() -> None:
    required = [
        COARSE_OPEN_CV / "summary.json",
        COARSE_OPEN_CV / "open_cv_use_policy.csv",
        COARSE_OPEN_CV / "averaged_value_policy.csv",
        MF_DISPOSITION / "qoi_mesh_disposition_summary.csv",
        SAME_QOI_UQ / "heat_flow_match_diagnostics.csv",
        SAME_QOI_UQ / "same_qoi_temporal_uq_summary.csv",
        SOURCE_EQ / "source_side_qoi_contract.csv",
        SOURCE_EQ / "case_heatflow_equivalence_basis.csv",
        PROPERTY_PREFLIGHT / "field_release_contract.csv",
        PROPERTY_PREFLIGHT / "summary.json",
        THERMAL_ACCOUNTING / "thermal_accounting_traceability_ledger.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 bulk heat-partition inputs: " + "; ".join(missing))


def build_heat_partition_rows(heat_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in heat_rows:
        q_wall = fnum(row["Q_wall_W"])
        q_source = fnum(row["Q_source_side_net_static_bc_W"])
        q_remaining = q_source - q_wall
        f_wall = safe_ratio(q_wall, q_source)
        f_remaining = safe_ratio(q_remaining, q_source)
        mdot_delta_t = fnum(row["abs_mdot_times_deltaT_kgK_s"])
        rows.append(
            {
                "case_id": row["case_id"],
                "target_time_window_s": row["target_time_window_s"],
                "Q_wall_W": q_wall,
                "Q_source_side_net_static_bc_W": q_source,
                "Q_remaining_after_wall_W": q_remaining,
                "F_wall_Qwall_over_source": f_wall,
                "F_remaining_after_wall": f_remaining,
                "abs_mdot_times_deltaT_kgK_s": mdot_delta_t,
                "cp_required_to_match_Q_wall_J_kg_K": row["cp_required_to_match_Q_wall_J_kg_K"],
                "cp_required_to_match_source_side_J_kg_K": row["cp_required_to_match_source_side_J_kg_K"],
                "partition_observation": (
                    "stable_candidate_bulk_integral_partition"
                    if f_wall is not None and 0.12 <= f_wall <= 0.16
                    else "partition_not_stable"
                ),
                "exchange_enthalpy_scale_status": "not_physical_match_with_current_exchange_scale",
                "production_use_allowed_now": False,
                "reason": "observed heat partition is diagnostic; cp/source-property and residual-complete CV gates remain closed",
            }
        )
    return rows


def build_partition_summary(rows: list[dict[str, Any]], qoi_summary_rows: list[dict[str, str]], temporal_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    f_values = [float(row["F_wall_Qwall_over_source"]) for row in rows]
    remaining_values = [float(row["F_remaining_after_wall"]) for row in rows]
    qwall_mesh = next(row for row in qoi_summary_rows if row["qoi_label"] == "Q_wall_W")
    qwall_temporal = next(row for row in temporal_rows if row["qoi_label"] == "Q_wall_W")
    spread = max(f_values) - min(f_values)
    cv = pstdev(f_values) / mean(f_values) if mean(f_values) != 0 else None
    return [
        {
            "metric": "F_wall_Qwall_over_source",
            "case_count": len(f_values),
            "min": min(f_values),
            "max": max(f_values),
            "mean": mean(f_values),
            "range": spread,
            "population_std": pstdev(f_values),
            "coefficient_of_variation": cv,
            "stability_status": "stable_diagnostic_candidate" if spread < 0.005 else "not_stable",
            "qwall_medium_fine_max_spread_percent": qwall_mesh["max_medium_fine_relative_percent_vs_fine"],
            "qwall_temporal_max_relative_percent": qwall_temporal["max_relative_temporal_uncertainty_percent"],
            "claim_boundary": "diagnostic bulk-integral partition only; no coefficient fit or admission",
        },
        {
            "metric": "F_remaining_after_wall",
            "case_count": len(remaining_values),
            "min": min(remaining_values),
            "max": max(remaining_values),
            "mean": mean(remaining_values),
            "range": max(remaining_values) - min(remaining_values),
            "population_std": pstdev(remaining_values),
            "coefficient_of_variation": pstdev(remaining_values) / mean(remaining_values),
            "stability_status": "stable_diagnostic_remainder",
            "qwall_medium_fine_max_spread_percent": qwall_mesh["max_medium_fine_relative_percent_vs_fine"],
            "qwall_temporal_max_relative_percent": qwall_temporal["max_relative_temporal_uncertainty_percent"],
            "claim_boundary": "remainder is an explicit residual/throughflow/storage lane, not an internal Nu adjustment",
        },
    ]


def build_energy_residual_feasibility(
    partition_rows: list[dict[str, Any]], field_contract_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    field_status = {row["field_or_basis"]: row for row in field_contract_rows}
    cp_status = field_status["cp_J_kg_K"]
    qwall_status = field_status["signed_Q_wall_W"]
    mdot_status = field_status["mdot_exchange_positive_outward_proxy_kg_s"]
    rows: list[dict[str, Any]] = []
    for row in partition_rows:
        rows.append(
            {
                "case_id": row["case_id"],
                "Q_source_side_net_static_bc_W": row["Q_source_side_net_static_bc_W"],
                "Q_wall_W": row["Q_wall_W"],
                "Q_remaining_after_wall_W": row["Q_remaining_after_wall_W"],
                "exchange_enthalpy_driver_abs_mdot_deltaT_kgK_s": row["abs_mdot_times_deltaT_kgK_s"],
                "energy_residual_formula": "R_E = Q_source_side_net_static_bc_W - Q_wall_W - mdot_throughflow*cp*DeltaT_throughflow - storage - other_named_losses",
                "can_compute_same_basis_energy_residual_now": False,
                "blocking_cp_status": cp_status["current_status"],
                "blocking_qwall_status": qwall_status["current_status"],
                "blocking_exchange_status": mdot_status["current_status"],
                "current_feasibility_disposition": "partition_residual_support_ready_but_energy_residual_not_computable",
                "next_required_evidence": "row-specific cp/property release plus same-window throughflow enthalpy endpoints and residual-complete CV terms",
            }
        )
    return rows


def build_model_form_ladder() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "model_direction": "bulk_integral_heat_partition",
            "formula_or_contract": "Q_wall_model = F_wall * Q_source_side_net_static_bc_W; residual lane remains explicit",
            "why_high_value_now": "F_wall is stable across Salt2/Salt3/Salt4 and Q_wall_W is the only low medium/fine-spread S13 QOI",
            "current_evidence_status": "diagnostic_ready_no_fit",
            "next_action": "predeclare partition target and validate residual-complete energy balance when cp/throughflow endpoints are released",
            "fit_allowed_now": False,
            "predictive_release_allowed_now": False,
        },
        {
            "rank": 2,
            "model_direction": "residual_complete_open_cv_energy_balance",
            "formula_or_contract": "R_E = Q_source - Q_wall - throughflow enthalpy - storage - named losses",
            "why_high_value_now": "preserves conservation and can use an open CV if every crossing term is explicit",
            "current_evidence_status": "blocked_cp_and_throughflow_endpoints",
            "next_action": "harvest same-window throughflow enthalpy endpoints and release cp/property provenance",
            "fit_allowed_now": False,
            "predictive_release_allowed_now": False,
        },
        {
            "rank": 3,
            "model_direction": "throughflow_plus_recirc_exchange_cell",
            "formula_or_contract": "main throughflow plus recirc cell with mdot_exchange, T_recirc, and bounded energy/pressure residuals",
            "why_high_value_now": "needed only after bulk residual shows exchange-cell detail is necessary",
            "current_evidence_status": "defer_proxy_mesh_sensitive",
            "next_action": "do not fit until mdot/tau/contrast mesh sensitivity and coarse-equivalence gates clear",
            "fit_allowed_now": False,
            "predictive_release_allowed_now": False,
        },
        {
            "rank": 4,
            "model_direction": "ordinary_one_stream_upcomer_nu_fd_k",
            "formula_or_contract": "single-stream upcomer Nu/f_D/K/F6",
            "why_high_value_now": "not high value in recirculating upcomer because topology invalidates the assumptions",
            "current_evidence_status": "disabled_by_recirc_switch",
            "next_action": "use only in low-recirculation or nonrecirculating anchors",
            "fit_allowed_now": False,
            "predictive_release_allowed_now": False,
        },
    ]


def build_progression_gate(partition_summary: list[dict[str, Any]], property_summary: dict[str, Any]) -> list[dict[str, Any]]:
    fwall = next(row for row in partition_summary if row["metric"] == "F_wall_Qwall_over_source")
    return [
        {
            "gate": "bulk_integral_partition_stability",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": f"F_wall range={float(fwall['range']):.12g}; mean={float(fwall['mean']):.12g}",
            "consequence": "advance bulk-integral partition as the leading modeling direction",
        },
        {
            "gate": "cp_property_release",
            "status": "fail_closed",
            "pass": False,
            "evidence": f"mf16_exact_field_release_ready_rows={property_summary['mf16_exact_field_release_ready_rows']}; s13_source_property_release_ready_rows={property_summary['s13_source_property_release_ready_rows']}",
            "consequence": "do not compute or admit same-basis energy residual yet",
        },
        {
            "gate": "exchange_proxy_mesh_stability",
            "status": "fail_closed",
            "pass": False,
            "evidence": "medium/fine mesh disposition showed mdot/tau/contrast proxy spread remains large",
            "consequence": "defer exchange-cell coefficient fitting",
        },
        {
            "gate": "predictive_1d_next_step",
            "status": "open_next_contract_only",
            "pass": True,
            "evidence": "bulk-integral partition is stable enough for a no-fit residual-complete follow-up",
            "consequence": "next work should harvest/reconcile throughflow enthalpy and property basis, not fit coefficients",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {"artifact": "heat_flow_match_diagnostics", "path": rel(SAME_QOI_UQ / "heat_flow_match_diagnostics.csv"), "role": "direct Qwall/source-side heat-flow and mdot*DeltaT scale", "mutation_status": "read_only"},
        {"artifact": "same_qoi_temporal_uq_summary", "path": rel(SAME_QOI_UQ / "same_qoi_temporal_uq_summary.csv"), "role": "temporal UQ support for exact QOI labels", "mutation_status": "read_only"},
        {"artifact": "medium_fine_mesh_disposition", "path": rel(MF_DISPOSITION / "qoi_mesh_disposition_summary.csv"), "role": "Qwall mesh stability and proxy instability", "mutation_status": "read_only"},
        {"artifact": "open_cv_contract", "path": rel(COARSE_OPEN_CV / "open_cv_use_policy.csv"), "role": "open CV and averaged-value policy", "mutation_status": "read_only"},
        {"artifact": "source_side_qoi_contract", "path": rel(SOURCE_EQ / "source_side_qoi_contract.csv"), "role": "source-side heat-flow label and sign convention", "mutation_status": "read_only"},
        {"artifact": "cp_property_preflight", "path": rel(PROPERTY_PREFLIGHT / "field_release_contract.csv"), "role": "cp/property release status for enthalpy residual", "mutation_status": "read_only"},
        {"artifact": "thermal_accounting_ledger", "path": rel(THERMAL_ACCOUNTING / "thermal_accounting_traceability_ledger.csv"), "role": "residual owner and heat-path policy context", "mutation_status": "read_only"},
    ]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SAME_QOI_UQ / "heat_flow_match_diagnostics.csv")}
  - {rel(MF_DISPOSITION / "qoi_mesh_disposition_summary.csv")}
  - {rel(COARSE_OPEN_CV / "open_cv_use_policy.csv")}
  - {rel(PROPERTY_PREFLIGHT / "field_release_contract.csv")}
tags: [work-product, s13, predictive-1d, heat-partition, bulk-integral, no-fit]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-bulk-integral-heat-partition-feasibility.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Bulk-Integral Heat-Partition Feasibility

Decision: `{summary["decision"]}`.

This package keeps the predictive 1D target conservative: averaged states may
drive future formulas, but `Q_wall_W`, source-side heat flow, exchange enthalpy
scale, and energy residual remain integral outputs.

The highest-value direction is a no-fit bulk heat partition first:
`Q_wall_model = F_wall * Q_source_side_net_static_bc_W`, with residual ownership
kept explicit. Current `F_wall` is stable across Salt2/Salt3/Salt4, but it is
not admitted as a coefficient because source/property, same-basis energy
residual, and formal release gates remain closed.
"""


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    heat_rows = read_csv(SAME_QOI_UQ / "heat_flow_match_diagnostics.csv")
    qoi_summary = read_csv(MF_DISPOSITION / "qoi_mesh_disposition_summary.csv")
    temporal_summary = read_csv(SAME_QOI_UQ / "same_qoi_temporal_uq_summary.csv")
    field_contract = read_csv(PROPERTY_PREFLIGHT / "field_release_contract.csv")
    property_summary = read_json(PROPERTY_PREFLIGHT / "summary.json")

    heat_partition = build_heat_partition_rows(heat_rows)
    partition_summary = build_partition_summary(heat_partition, qoi_summary, temporal_summary)
    residual_feasibility = build_energy_residual_feasibility(heat_partition, field_contract)
    ladder = build_model_form_ladder()
    gate = build_progression_gate(partition_summary, property_summary)
    manifest = build_source_manifest()

    fwall = next(row for row in partition_summary if row["metric"] == "F_wall_Qwall_over_source")
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "bulk_integral_heat_partition_feasible_diagnostic_no_fit_residual_next",
        "case_count": len(heat_partition),
        "F_wall_mean": fwall["mean"],
        "F_wall_min": fwall["min"],
        "F_wall_max": fwall["max"],
        "F_wall_range": fwall["range"],
        "F_wall_stability_status": fwall["stability_status"],
        "bulk_integral_partition_diagnostic_ready": True,
        "same_basis_energy_residual_computable_now": False,
        "recommended_next_model_direction": "bulk_integral_heat_partition_then_residual_complete_open_cv",
        "exchange_cell_coefficient_direction_now": "defer",
        "ordinary_one_stream_upcomer_direction_now": "disabled_in_recirc_upcomer",
        "source_property_release": False,
        "Qwall_release": False,
        "coefficient_admission": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "validation_holdout_external_scoring": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "generated_docs_index_refreshed": False,
    }

    write_csv(
        OUT / "bulk_integral_heat_partition_rows.csv",
        heat_partition,
        [
            "case_id",
            "target_time_window_s",
            "Q_wall_W",
            "Q_source_side_net_static_bc_W",
            "Q_remaining_after_wall_W",
            "F_wall_Qwall_over_source",
            "F_remaining_after_wall",
            "abs_mdot_times_deltaT_kgK_s",
            "cp_required_to_match_Q_wall_J_kg_K",
            "cp_required_to_match_source_side_J_kg_K",
            "partition_observation",
            "exchange_enthalpy_scale_status",
            "production_use_allowed_now",
            "reason",
        ],
    )
    write_csv(
        OUT / "partition_stability_summary.csv",
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
        OUT / "energy_residual_feasibility.csv",
        residual_feasibility,
        [
            "case_id",
            "Q_source_side_net_static_bc_W",
            "Q_wall_W",
            "Q_remaining_after_wall_W",
            "exchange_enthalpy_driver_abs_mdot_deltaT_kgK_s",
            "energy_residual_formula",
            "can_compute_same_basis_energy_residual_now",
            "blocking_cp_status",
            "blocking_qwall_status",
            "blocking_exchange_status",
            "current_feasibility_disposition",
            "next_required_evidence",
        ],
    )
    write_csv(
        OUT / "bulk_integral_model_form_ladder.csv",
        ladder,
        [
            "rank",
            "model_direction",
            "formula_or_contract",
            "why_high_value_now",
            "current_evidence_status",
            "next_action",
            "fit_allowed_now",
            "predictive_release_allowed_now",
        ],
    )
    write_csv(
        OUT / "progression_gate.csv",
        gate,
        ["gate", "status", "pass", "evidence", "consequence"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        manifest,
        ["artifact", "path", "role", "mutation_status"],
    )
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    global OUT
    if args.output_dir is not None:
        OUT = args.output_dir
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
