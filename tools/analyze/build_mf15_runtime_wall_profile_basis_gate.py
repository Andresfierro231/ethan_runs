#!/usr/bin/env python3
"""Build MF15 runtime wall/profile basis gate from D3 evidence."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate"

D3 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
MF14 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate"
MF13 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight"
N4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"


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


def build_family_rows(candidate_rows: list[dict[str, str]], crosswalk_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    blocks = "; ".join(f"{row['evidence_family']}={row['status']}" for row in crosswalk_rows if parse_bool(row["blocks_candidate"]))
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row["candidate_id"] == "D3-WALL-CORE-EXCHANGE-SHAPE":
            required = "predicted T_wall_inner; predicted T_bulk; wall_core_bulk_temperature_contrast_K UQ; source/property conservation; wall/segment map; no fitted coefficient"
            runtime_basis = "missing_runtime_wall_core_exchange_operator"
        elif row["candidate_id"] == "D3-AXIAL-MIXING-SHAPE":
            required = "source-bounded axial mixing coefficient; exchange/recirculation QOI UQ; conservation test; segment map; no residual-trained shape coefficient"
            runtime_basis = "missing_independent_axial_mixing_operator"
        else:
            required = "sensor projection UQ; runtime temperature legality; wall-state projection operator; no closure repair"
            runtime_basis = "supporting_uncertainty_only_not_closure"
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "mechanism": row["mechanism"],
                "positive_evidence": row["positive_evidence"],
                "blocking_evidence": row["blocking_evidence"],
                "required_runtime_inputs": required,
                "runtime_basis_status": runtime_basis,
                "runtime_legal_source_bounded_study_defined": parse_bool(row["runtime_legal_source_bounded_study_defined"]),
                "same_qoi_or_source_property_blockers": blocks,
                "candidate_ready": parse_bool(row["candidate_ready"]),
                "wall_profile_correction_release_ready": False,
                "gate_status": row["gate_status"],
                "claim_allowed_now": "diagnostic_mechanism_priority_only" if "fail_closed" in row["gate_status"] else "supporting_uncertainty_only",
            }
        )
    return rows


def build_requirement_rows(family_rows: list[dict[str, Any]], same_qoi_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    triplet_ready = {row["qoi_label"]: parse_bool(row["triplet_ready"]) for row in same_qoi_rows}
    uq_executed = {row["qoi_label"]: row["same_qoi_uq_execution_status"] == "executed" for row in same_qoi_rows}
    requirements = [
        ("predicted_T_wall_inner", "blocked", "1D wall state exists as a model output concept but no runtime wall/profile correction operator is released"),
        ("predicted_T_bulk", "diagnostic_available", "Bulk/fluid projection exists only as post-solve score-target projection"),
        ("wall_core_bulk_temperature_contrast_K", "triplet_ready_uq_not_executed" if triplet_ready.get("wall_core_bulk_temperature_contrast_K") else "blocked", "S13/D3 says triplets are ready but UQ and production use are not executed"),
        ("Q_wall_W", "triplet_ready_uq_not_executed" if triplet_ready.get("Q_wall_W") else "blocked", "Qwall supports wall/core exchange only after same-QOI UQ and production gate"),
        ("mdot_exchange_positive_outward_proxy_kg_s", "triplet_ready_uq_not_executed" if triplet_ready.get("mdot_exchange_positive_outward_proxy_kg_s") else "blocked", "exchange proxy supports axial/wall-core mechanism only after UQ"),
        ("tau_recirc_proxy_s", "triplet_ready_uq_not_executed" if triplet_ready.get("tau_recirc_proxy_s") else "blocked", "recirculation proxy supports axial mixing only after UQ"),
        ("source_property_conservation", "fail_closed", "D3 crosswalk reports source/property conservation release failed"),
        ("runtime_temperature_release", "fail_closed", "N4/MF14 runtime temperature allowed rows are zero"),
        ("independent_coefficient_basis", "fail_closed", "D3 wall-index shape is residual-trained and has no independent coefficient basis"),
    ]
    rows: list[dict[str, Any]] = []
    for family in family_rows:
        for requirement, status, evidence in requirements:
            applies = True
            if family["candidate_id"] == "D3-SENSOR-PROJECTION-SHAPE" and requirement in {
                "Q_wall_W",
                "mdot_exchange_positive_outward_proxy_kg_s",
                "tau_recirc_proxy_s",
                "source_property_conservation",
                "independent_coefficient_basis",
            }:
                applies = False
            rows.append(
                {
                    "candidate_id": family["candidate_id"],
                    "requirement": requirement,
                    "applies": applies,
                    "status": status if applies else "not_primary_requirement",
                    "uq_executed": uq_executed.get(requirement, False),
                    "release_allowed": False,
                    "evidence": evidence if applies else "not a primary requirement for this family",
                }
            )
    return rows


def build_case_rows(case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows:
        rows.append(
            {
                "case_id": row["case_id"],
                "split_group": row["split_group"],
                "tw_rows": row["tw_rows"],
                "m3_tw_rmse_K": row["m3_tw_rmse_K"],
                "d3_tw_rmse_K": row["d3_tw_rmse_K"],
                "d3_minus_m3_tw_rmse_K": row["d3_minus_m3_tw_rmse_K"],
                "m3_error_slope_K_per_sensor_index": row["m3_error_slope_K_per_sensor_index"],
                "d3_error_slope_K_per_sensor_index": row["d3_error_slope_K_per_sensor_index"],
                "existing_metric_reused_read_only": True,
                "new_scoring_performed": False,
                "claim_boundary": "train diagnostic" if row["split_group"] == "train" else "existing transfer metric read-only; not used for model selection",
            }
        )
    return rows


def build_gate_rows(family_rows: list[dict[str, Any]], requirement_rows: list[dict[str, Any]], d3_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate": "wall_shape_signal_present",
            "status": "pass_diagnostic",
            "evidence": f"D3 transfer RMSE reduction {d3_summary['d3_transfer_rmse_reduction_pct']} pct",
            "release_allowed": False,
            "missing_for_release": "runtime wall/profile operator and independent basis",
        },
        {
            "gate": "candidate_reviewable_now",
            "status": "fail_closed",
            "evidence": f"{sum(row['candidate_ready'] for row in family_rows)} of {len(family_rows)} D3 candidate rows ready",
            "release_allowed": False,
            "missing_for_release": "same-QOI UQ, source/property conservation, runtime basis",
        },
        {
            "gate": "same_qoi_uq_executed",
            "status": "fail_closed",
            "evidence": f"{sum(row['uq_executed'] for row in requirement_rows)} executed UQ requirement rows",
            "release_allowed": False,
            "missing_for_release": "execute separate same-QOI UQ/production gate",
        },
        {
            "gate": "runtime_temperature_release",
            "status": "fail_closed",
            "evidence": "N4/MF14 runtime temperature allowed rows are zero",
            "release_allowed": False,
            "missing_for_release": "runtime wall and bulk state use boundary",
        },
        {
            "gate": "source_property_conservation",
            "status": "fail_closed",
            "evidence": "D3 crosswalk reports source/property conservation release failed",
            "release_allowed": False,
            "missing_for_release": "source/property conservation release",
        },
        {
            "gate": "wall_profile_correction_release",
            "status": "fail_closed",
            "evidence": "No D3 runtime coefficient or correction may enter the model",
            "release_allowed": False,
            "missing_for_release": "source-bounded wall/profile correction proof and admission",
        },
    ]


def build_thesis_insert(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MF15 Runtime Wall/Profile Basis Gate",
            "",
            "MF15 evaluates whether the D3 wall-shape signal can be promoted to a runtime wall/profile model. The signal is strong diagnostically: D3 reduces transfer RMSE by about 52% and reduces wall-index error shape. However, no wall/profile correction is released.",
            "",
            "The missing pieces are not another empirical shape coefficient. They are a source-bounded wall/core or axial-mixing operator, same-QOI UQ for wall-core/exchange/recirculation quantities, source/property conservation release, and a runtime temperature-use boundary.",
            "",
            f"Candidate-ready wall/profile rows: {summary['candidate_ready_rows']} of {summary['candidate_rows']}. Release-ready wall/profile rows: {summary['wall_profile_correction_release_ready_rows']} of {summary['candidate_rows']}. The next rigorous study should target source/property label release using the exact missing fields from MF13 and MF15.",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    d3_summary = json.loads((D3 / "summary.json").read_text())
    candidate_rows = read_csv(D3 / "candidate_gate.csv")
    crosswalk_rows = read_csv(D3 / "s12_s13_evidence_crosswalk.csv")
    same_qoi_rows = read_csv(D3 / "same_qoi_uq_requirement_table.csv")
    case_rows = read_csv(D3 / "wall_shape_case_summary.csv")
    mf14_summary = json.loads((MF14 / "summary.json").read_text())

    family_rows = build_family_rows(candidate_rows, crosswalk_rows)
    requirement_rows = build_requirement_rows(family_rows, same_qoi_rows)
    case_summary_rows = build_case_rows(case_rows)
    gate_rows = build_gate_rows(family_rows, requirement_rows, d3_summary)
    next_rows = [
        {
            "priority": 1,
            "next_study": "source_property_label_release_candidate_after_exact_fields",
            "why": "MF13 and MF15 both block on source/property conservation and row-level source/property labels",
            "success_signal": "explicit release/fail-closed matrix for q_setup, cp/property, segment/source placement, wall/profile conservation, and runtime use",
            "current_status_after_mf15": "next",
        },
        {
            "priority": 2,
            "next_study": "same_qoi_wall_core_exchange_uq_execution",
            "why": "D3 says Qwall/exchange/recirculation/wall-core triplets are ready but UQ not executed",
            "success_signal": "same-QOI UQ rows for four D3 support QOIs, still no coefficient admission",
            "current_status_after_mf15": "parallel_after_source_contract_or_separate_scheduler_row",
        },
        {
            "priority": 3,
            "next_study": "train_only_mf12_formula_smoke_after_release",
            "why": "Formula smoke remains blocked until source/property, projection, and wall/profile gates pass",
            "success_signal": "train/support-only metrics and runtime-leakage audit",
            "current_status_after_mf15": "blocked_by_release_gates",
        },
        {
            "priority": 4,
            "next_study": "tw_after_tp_residual_ownership",
            "why": "TW residual ownership should follow source/property and wall/profile UQ separation",
            "success_signal": "TW residual-owner table with D3 mechanisms separated from TP projection residual",
            "current_status_after_mf15": "pending",
        },
    ]
    manifest_rows = [
        {"source_path": str(D3 / "summary.json"), "use": "D3 diagnostic decision and metrics", "mutation_status": "read_only"},
        {"source_path": str(D3 / "candidate_gate.csv"), "use": "candidate mechanism rows and gate status", "mutation_status": "read_only"},
        {"source_path": str(D3 / "same_qoi_uq_requirement_table.csv"), "use": "same-QOI triplet/UQ readiness", "mutation_status": "read_only"},
        {"source_path": str(D3 / "s12_s13_evidence_crosswalk.csv"), "use": "S12/S13 blockers and support", "mutation_status": "read_only"},
        {"source_path": str(D3 / "wall_shape_case_summary.csv"), "use": "existing case metrics reused read-only", "mutation_status": "read_only"},
        {"source_path": str(MF14 / "summary.json"), "use": f"TP projection gate context: {mf14_summary['decision']}", "mutation_status": "read_only"},
        {"source_path": str(N4 / "summary.json"), "use": "runtime temperature release context", "mutation_status": "read_only"},
        {"source_path": str(MF13 / "summary.json"), "use": "source/property release context", "mutation_status": "read_only"},
    ]
    guardrail_rows = [
        {"guardrail": "new validation scoring", "occurred": False},
        {"guardrail": "new holdout scoring", "occurred": False},
        {"guardrail": "external-test scoring", "occurred": False},
        {"guardrail": "fitting/tuning/model selection", "occurred": False},
        {"guardrail": "runtime temperature input release", "occurred": False},
        {"guardrail": "wall-profile correction release", "occurred": False},
        {"guardrail": "source/property release", "occurred": False},
        {"guardrail": "coefficient admission", "occurred": False},
        {"guardrail": "Fluid solve or scheduler action", "occurred": False},
        {"guardrail": "native output or registry mutation", "occurred": False},
        {"guardrail": "residual absorbed into internal Nu", "occurred": False},
    ]
    summary = {
        "task_id": "TODO-MF15-RUNTIME-WALL-PROFILE-BASIS-GATE-2026-07-22",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "runtime_wall_profile_basis_fail_closed_diagnostic_signal_only",
        "candidate_rows": len(family_rows),
        "candidate_ready_rows": sum(row["candidate_ready"] for row in family_rows),
        "wall_profile_correction_release_ready_rows": sum(row["wall_profile_correction_release_ready"] for row in family_rows),
        "same_qoi_triplet_ready_qois": d3_summary["same_qoi_triplet_ready_qois"],
        "same_qoi_uq_executed": d3_summary["same_qoi_uq_executed"],
        "d3_transfer_rmse_reduction_pct": d3_summary["d3_transfer_rmse_reduction_pct"],
        "new_validation_holdout_external_scoring": False,
        "runtime_temperature_input_release": False,
        "source_property_release": False,
        "wall_profile_correction_release": False,
        "coefficient_admission": False,
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(OUT_DIR / "wall_profile_family_basis_gate.csv", family_rows, ["candidate_id", "mechanism", "positive_evidence", "blocking_evidence", "required_runtime_inputs", "runtime_basis_status", "runtime_legal_source_bounded_study_defined", "same_qoi_or_source_property_blockers", "candidate_ready", "wall_profile_correction_release_ready", "gate_status", "claim_allowed_now"])
    write_csv(OUT_DIR / "runtime_operator_requirement_matrix.csv", requirement_rows, ["candidate_id", "requirement", "applies", "status", "uq_executed", "release_allowed", "evidence"])
    write_csv(OUT_DIR / "wall_shape_case_metric_reuse_boundary.csv", case_summary_rows, ["case_id", "split_group", "tw_rows", "m3_tw_rmse_K", "d3_tw_rmse_K", "d3_minus_m3_tw_rmse_K", "m3_error_slope_K_per_sensor_index", "d3_error_slope_K_per_sensor_index", "existing_metric_reused_read_only", "new_scoring_performed", "claim_boundary"])
    write_csv(OUT_DIR / "wall_profile_release_gate.csv", gate_rows, ["gate", "status", "evidence", "release_allowed", "missing_for_release"])
    write_csv(OUT_DIR / "next_study_queue.csv", next_rows, ["priority", "next_study", "why", "success_signal", "current_status_after_mf15"])
    write_csv(OUT_DIR / "source_manifest.csv", manifest_rows, ["source_path", "use", "mutation_status"])
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows, ["guardrail", "occurred"])

    (OUT_DIR / "thesis_wall_profile_basis_insert.md").write_text(build_thesis_insert(summary) + "\n")
    (OUT_DIR / "README.md").write_text(
        "# MF15 Runtime Wall/Profile Basis Gate\n\n"
        f"Decision: `{summary['decision']}`.\n\n"
        "D3 wall-shape evidence is diagnostic and promising, but no runtime wall/profile correction is released. "
        "Outputs identify missing same-QOI UQ, source/property conservation, runtime temperature release, and independent coefficient/source-bounded basis.\n"
    )
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
