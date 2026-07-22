#!/usr/bin/env python3
"""Build MF17 same-QOI wall/core exchange UQ execution synthesis."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution"

UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
D3 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
MF15 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate"
MF16 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate"


QOI_MECHANISM = {
    "Q_wall_W": "wall_core_exchange_heat_path",
    "mdot_exchange_positive_outward_proxy_kg_s": "exchange_mass_proxy",
    "tau_recirc_proxy_s": "recirculation_residence_proxy",
    "wall_core_bulk_temperature_contrast_K": "wall_core_temperature_profile",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return value.strip().lower() in {"true", "1", "yes", "y"}


def build_qoi_execution_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in summary_rows:
        rows.append(
            {
                "qoi_label": row["qoi_label"],
                "mechanism_role": QOI_MECHANISM[row["qoi_label"]],
                "case_count": row["case_count"],
                "finite_triplet_rows": row["finite_triplet_rows"],
                "neighbor_window_uq_executed_rows": row["neighbor_window_uq_executed_rows"],
                "max_abs_temporal_uncertainty": row["max_abs_temporal_uncertainty"],
                "mean_abs_temporal_uncertainty": row["mean_abs_temporal_uncertainty"],
                "max_half_range_uncertainty": row["max_half_range_uncertainty"],
                "max_relative_temporal_uncertainty_percent": row["max_relative_temporal_uncertainty_percent"],
                "same_qoi_temporal_uq_status": row["same_qoi_temporal_uq_status"],
                "mesh_gci_gate_input_ready": parse_bool(row["mesh_gci_gate_input_ready"]),
                "production_use_allowed_now": parse_bool(row["production_use_allowed_now"]),
                "admission_allowed_now": parse_bool(row["admission_allowed_now"]),
                "release_boundary": row["release_boundary"],
                "mf17_interpretation": "temporal_uq_executed_supports_mechanism_not_admission",
            }
        )
    return rows


def build_case_rows(case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "mechanism_role": QOI_MECHANISM[row["qoi_label"]],
            "mf17_claim_boundary": "same-QOI neighbor-window temporal UQ only; no mesh/GCI/admission",
        }
        for row in case_rows
    ]


def build_mechanism_rows(qoi_rows: list[dict[str, Any]], heat_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    heat_match_ready = sum(1 for row in heat_rows if row["heat_flow_match_status"] == "physical_match_ready")
    executed = {row["qoi_label"]: row for row in qoi_rows if row["same_qoi_temporal_uq_status"] == "executed"}
    return [
        {
            "mechanism_family": "D3-WALL-CORE-EXCHANGE-SHAPE",
            "required_qois": "Q_wall_W; wall_core_bulk_temperature_contrast_K; mdot_exchange_positive_outward_proxy_kg_s",
            "same_qoi_temporal_uq_executed": all(qoi in executed for qoi in ["Q_wall_W", "wall_core_bulk_temperature_contrast_K", "mdot_exchange_positive_outward_proxy_kg_s"]),
            "heat_flow_match_ready_rows": heat_match_ready,
            "mesh_gci_ready": True,
            "mesh_gci_executed": False,
            "source_property_release_ready": False,
            "production_or_admission_allowed": False,
            "interpretation": "temporal UQ supports mechanism priority, but heat-flow mismatch and source/property/mesh-GCI gates block admission",
        },
        {
            "mechanism_family": "D3-AXIAL-MIXING-SHAPE",
            "required_qois": "mdot_exchange_positive_outward_proxy_kg_s; tau_recirc_proxy_s; wall_core_bulk_temperature_contrast_K",
            "same_qoi_temporal_uq_executed": all(qoi in executed for qoi in ["mdot_exchange_positive_outward_proxy_kg_s", "tau_recirc_proxy_s", "wall_core_bulk_temperature_contrast_K"]),
            "heat_flow_match_ready_rows": heat_match_ready,
            "mesh_gci_ready": True,
            "mesh_gci_executed": False,
            "source_property_release_ready": False,
            "production_or_admission_allowed": False,
            "interpretation": "exchange/recirculation temporal UQ is executed, but no independent axial-mixing coefficient basis is admitted",
        },
    ]


def build_release_gate(uq_summary: dict[str, Any], production_rows: list[dict[str, str]], mf16_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate": "same_qoi_temporal_uq_for_four_qois",
            "status": "pass_executed",
            "evidence": f"{uq_summary['same_qoi_temporal_uq_executed_qois']} of {uq_summary['qoi_label_count']} QOIs executed",
            "release_allowed": False,
            "next_action": "preserve as temporal UQ support",
        },
        {
            "gate": "mesh_gci_uq",
            "status": "ready_not_executed",
            "evidence": "mesh/GCI remains separate; active medium/fine exact-label sampler is not consumed for admission here",
            "release_allowed": False,
            "next_action": "wait for same-label mesh/GCI row",
        },
        {
            "gate": "production_harvest",
            "status": "blocked",
            "evidence": "; ".join(f"{row['gate']}={row['production_harvest_allowed_now']}" for row in production_rows),
            "release_allowed": False,
            "next_action": "do not run production harvest from MF17",
        },
        {
            "gate": "source_property_release",
            "status": "fail_closed",
            "evidence": f"MF16 exact-field release-ready rows {mf16_summary['exact_field_release_ready_rows']}",
            "release_allowed": False,
            "next_action": "strict source envelope recovery remains serial blocker",
        },
        {
            "gate": "wall_core_exchange_coefficient_admission",
            "status": "fail_closed",
            "evidence": "temporal UQ is not a coefficient or closure admission",
            "release_allowed": False,
            "next_action": "require source-bounded coefficient/operator plus mesh/GCI and source/property release",
        },
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    uq_summary_rows = read_csv(UQ / "same_qoi_temporal_uq_summary.csv")
    uq_case_rows = read_csv(UQ / "same_qoi_temporal_uq_case_rows.csv")
    heat_rows = read_csv(UQ / "heat_flow_match_diagnostics.csv")
    production_rows = read_csv(UQ / "production_readiness_gate.csv")
    uq_summary = json.loads((UQ / "summary.json").read_text())
    d3_summary = json.loads((D3 / "summary.json").read_text())
    mf15_summary = json.loads((MF15 / "summary.json").read_text())
    mf16_summary = json.loads((MF16 / "summary.json").read_text())

    qoi_rows = build_qoi_execution_rows(uq_summary_rows)
    case_rows = build_case_rows(uq_case_rows)
    mechanism_rows = build_mechanism_rows(qoi_rows, heat_rows)
    release_gate_rows = build_release_gate(uq_summary, production_rows, mf16_summary)
    next_rows = [
        {
            "priority": 1,
            "next_study": "same_label_mesh_gci_after_medium_fine_sampler",
            "why": "MF17 executes temporal UQ; mesh/GCI is next before production/admission",
            "success_signal": "accepted same-label mesh/GCI rows for the four S13 QOIs",
            "status_after_mf17": "blocked_on_active_sampler",
        },
        {
            "priority": 2,
            "next_study": "strict_row_specific_source_envelope_recovery",
            "why": "MF16 source/property release remains closed",
            "success_signal": "strict source-envelope pass for candidate train rows",
            "status_after_mf17": "serial_blocker",
        },
        {
            "priority": 3,
            "next_study": "same_mask_exchange_control_volume_energy_residual",
            "why": "heat-flow diagnostics show Qwall and source-side heat are different lanes",
            "success_signal": "same-mask enthalpy/source/wall residual ledger with cp/property basis",
            "status_after_mf17": "pending_after_source_property",
        },
    ]
    manifest_rows = [
        {"source_path": str(UQ / "same_qoi_temporal_uq_summary.csv"), "use": "QOI-level executed temporal UQ", "mutation_status": "read_only"},
        {"source_path": str(UQ / "same_qoi_temporal_uq_case_rows.csv"), "use": "case-level target-minus/target/target-plus triplets", "mutation_status": "read_only"},
        {"source_path": str(UQ / "heat_flow_match_diagnostics.csv"), "use": "heat-flow mismatch caveat", "mutation_status": "read_only"},
        {"source_path": str(UQ / "production_readiness_gate.csv"), "use": "production/admission boundary", "mutation_status": "read_only"},
        {"source_path": str(MF16 / "summary.json"), "use": "source/property serial blocker", "mutation_status": "read_only"},
    ]
    guardrail_rows = [
        {"guardrail": "scheduler/solver/sampler/UQ launched", "occurred": False},
        {"guardrail": "active medium/fine sampler mutation", "occurred": False},
        {"guardrail": "Qwall production release", "occurred": False},
        {"guardrail": "source/property release", "occurred": False},
        {"guardrail": "coefficient admission", "occurred": False},
        {"guardrail": "validation/holdout/external scoring", "occurred": False},
        {"guardrail": "fitting/tuning/model selection", "occurred": False},
        {"guardrail": "native output or registry mutation", "occurred": False},
        {"guardrail": "residual absorbed into internal Nu", "occurred": False},
    ]
    summary = {
        "task_id": "TODO-MF17-SAME-QOI-WALL-CORE-EXCHANGE-UQ-EXECUTION-2026-07-22",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "same_qoi_wall_core_exchange_temporal_uq_executed_no_admission",
        "qoi_label_count": len(qoi_rows),
        "case_temporal_uq_rows": len(case_rows),
        "same_qoi_temporal_uq_executed_qois": uq_summary["same_qoi_temporal_uq_executed_qois"],
        "mechanism_rows": len(mechanism_rows),
        "heat_flow_match_ready_rows": uq_summary["heat_flow_match_ready_rows"],
        "mesh_gci_gate_input_ready": uq_summary["mesh_gci_gate_input_ready"],
        "mesh_gci_uq_executed": uq_summary["mesh_gci_uq_executed"],
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "source_property_release": False,
        "qwall_production_release": False,
        "coefficient_admission": False,
        "d3_transfer_rmse_reduction_pct_read_only": d3_summary["d3_transfer_rmse_reduction_pct"],
        "mf15_wall_profile_release_ready_rows": mf15_summary["wall_profile_correction_release_ready_rows"],
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(OUT_DIR / "qoi_temporal_uq_execution_summary.csv", qoi_rows, ["qoi_label", "mechanism_role", "case_count", "finite_triplet_rows", "neighbor_window_uq_executed_rows", "max_abs_temporal_uncertainty", "mean_abs_temporal_uncertainty", "max_half_range_uncertainty", "max_relative_temporal_uncertainty_percent", "same_qoi_temporal_uq_status", "mesh_gci_gate_input_ready", "production_use_allowed_now", "admission_allowed_now", "release_boundary", "mf17_interpretation"])
    write_csv(OUT_DIR / "case_triplet_temporal_uq_rows.csv", case_rows, list(case_rows[0].keys()))
    write_csv(OUT_DIR / "d3_mechanism_uq_impact_table.csv", mechanism_rows, ["mechanism_family", "required_qois", "same_qoi_temporal_uq_executed", "heat_flow_match_ready_rows", "mesh_gci_ready", "mesh_gci_executed", "source_property_release_ready", "production_or_admission_allowed", "interpretation"])
    write_csv(OUT_DIR / "heat_flow_match_caveat.csv", heat_rows, list(heat_rows[0].keys()))
    write_csv(OUT_DIR / "production_admission_boundary.csv", release_gate_rows, ["gate", "status", "evidence", "release_allowed", "next_action"])
    write_csv(OUT_DIR / "next_study_queue.csv", next_rows, ["priority", "next_study", "why", "success_signal", "status_after_mf17"])
    write_csv(OUT_DIR / "source_manifest.csv", manifest_rows, ["source_path", "use", "mutation_status"])
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows, ["guardrail", "occurred"])
    (OUT_DIR / "README.md").write_text(
        "# MF17 Same-QOI Wall/Core Exchange UQ Execution\n\n"
        f"Decision: `{summary['decision']}`.\n\n"
        "Temporal same-QOI UQ is executed for Qwall, exchange mdot proxy, recirculation tau proxy, and wall/core bulk temperature contrast. This supports the D3 wall/core and axial-mixing mechanism discussion, but does not release Qwall, source/property fields, production harvest, mesh/GCI, or a coefficient.\n"
    )
    (OUT_DIR / "thesis_wall_core_exchange_uq_insert.md").write_text(
        "# MF17 Same-QOI Wall/Core Exchange UQ Execution\n\n"
        "MF17 closes the temporal-UQ part of the D3 wall/core exchange evidence path: all four requested QOIs have target-minus/target/target-plus same-QOI temporal UQ executed. The result strengthens the thesis mechanism argument, but remains non-admissive because mesh/GCI, source/property release, and same-mask exchange control-volume energy closure are still open.\n"
    )
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
