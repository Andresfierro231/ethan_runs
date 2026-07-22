#!/usr/bin/env python3
"""Build MF14 same-QOI TP projection UQ gate.

This study separates TP sensor/projection bookkeeping from runtime-admissible
bulk-to-TP correction. It consumes existing D2/N4/projection-operator evidence
and does not perform new scoring.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate"

N4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"
D2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
PROJECTION_OP = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk"
MF13 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight"


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


def index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def uq_class(row: dict[str, str]) -> str:
    if row["acceptance_class"] == "mapped":
        return "mapped_projection_without_quantitative_same_qoi_uq"
    if row["acceptance_class"] == "bounded":
        return "bounded_location_without_quantitative_same_qoi_uq"
    return "excluded_or_unsupported"


def build_tp_rows(
    n4_rows: list[dict[str, str]],
    op_rows: list[dict[str, str]],
    d2_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    op_by_sensor = index(op_rows, "sensor")
    d2_by_sensor = index(d2_rows, "sensor")
    rows: list[dict[str, Any]] = []
    for n4 in n4_rows:
        if n4["kind"] != "TP":
            continue
        op = op_by_sensor[n4["sensor"]]
        d2 = d2_by_sensor[n4["sensor"]]
        runtime_allowed = parse_bool(n4["runtime_temperature_allowed"]) or parse_bool(op["runtime_temperature_allowed"])
        fit_allowed = parse_bool(n4["fit_allowed"]) or parse_bool(op["fit_allowed"])
        model_selection_allowed = parse_bool(n4["model_selection_allowed"]) or parse_bool(op["model_selection_allowed"])
        same_qoi_label_present = n4["score_target_use"] == "post_solve_score_target_only" and op["projection_operator"] == "bulk_fluid_projection"
        quantitative_uq_ready = False
        release_ready = (
            same_qoi_label_present
            and quantitative_uq_ready
            and runtime_allowed
            and not fit_allowed
            and not model_selection_allowed
            and d2["admission_readiness"].startswith("ready")
        )
        rows.append(
            {
                "sensor": n4["sensor"],
                "kind": n4["kind"],
                "acceptance_class": n4["acceptance_class"],
                "one_d_segment_or_state": n4["one_d_segment_or_state"],
                "one_d_fraction_or_marker": n4["one_d_fraction_or_marker"],
                "projection_operator": op["projection_operator"],
                "projection_equation": op["projection_equation"],
                "mapped_developing_span": d2["mapped_developing_span"],
                "current_projection": d2["current_projection"],
                "thermal_development_evidence": d2["thermal_development_evidence"],
                "litrev_allowed_rows": d2["litrev_allowed_rows"],
                "litrev_uq_blocked_rows": d2["litrev_uq_blocked_rows"],
                "example_x_from_reset_m": d2["example_x_from_reset_m"],
                "example_L_over_D_from_reset": d2["example_L_over_D_from_reset"],
                "thermal_reset_status": d2["thermal_reset_status"],
                "same_qoi_label_present": same_qoi_label_present,
                "quantitative_same_qoi_uq_ready": quantitative_uq_ready,
                "runtime_temperature_allowed": runtime_allowed,
                "fit_allowed": fit_allowed,
                "model_selection_allowed": model_selection_allowed,
                "bulk_to_tp_correction_released": False,
                "same_qoi_projection_release_ready": release_ready,
                "uq_status": uq_class(n4),
                "uncertainty_caveat": n4["uncertainty_caveat"],
                "claim_allowed_now": "post_solve_score_target_projection_only",
                "blocking_gap": "quantitative_same_qoi_projection_uq;runtime_temperature_release;source_bounded_bulk_to_tp_offset",
            }
        )
    return rows


def build_gate_rows(tp_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "gate": "tp_same_qoi_labels_present",
            "status": "pass_diagnostic",
            "evidence": f"{sum(row['same_qoi_label_present'] for row in tp_rows)} of {len(tp_rows)} TP rows have bulk-fluid projection labels",
            "release_allowed": False,
            "missing_for_release": "quantitative_same_qoi_uq_and_runtime_temperature_release",
        },
        {
            "gate": "sensor_projection_acceptance_class_documented",
            "status": "pass_diagnostic",
            "evidence": "TP rows carry bounded/mapped acceptance classes and caveats from N4",
            "release_allowed": False,
            "missing_for_release": "exact measurement provenance or quantitative projection uncertainty",
        },
        {
            "gate": "thermal_development_evidence_present",
            "status": "pass_diagnostic",
            "evidence": "D2 provides promising thermal-development/projection evidence for TP1-TP6",
            "release_allowed": False,
            "missing_for_release": "source-bounded correction formula and UQ",
        },
        {
            "gate": "quantitative_same_qoi_uq_ready",
            "status": "fail_closed",
            "evidence": f"{sum(row['quantitative_same_qoi_uq_ready'] for row in tp_rows)} of {len(tp_rows)} TP rows have quantitative same-QOI UQ",
            "release_allowed": False,
            "missing_for_release": "uncertainty propagation for projection operator and probe placement",
        },
        {
            "gate": "runtime_temperature_release",
            "status": "fail_closed",
            "evidence": f"{sum(row['runtime_temperature_allowed'] for row in tp_rows)} of {len(tp_rows)} TP rows allow runtime temperature use",
            "release_allowed": False,
            "missing_for_release": "runtime_temperature_allowed_true",
        },
        {
            "gate": "bulk_to_tp_correction_release",
            "status": "fail_closed",
            "evidence": f"{sum(row['bulk_to_tp_correction_released'] for row in tp_rows)} released correction rows",
            "release_allowed": False,
            "missing_for_release": "source-bounded thermal-development offset proof",
        },
        {
            "gate": "protected_scoring_or_model_selection",
            "status": "pass_guardrail",
            "evidence": "MF14 performs no new validation/holdout/external scoring and no model selection",
            "release_allowed": False,
            "missing_for_release": "separate freeze/admission row after upstream gates",
        },
    ]


def build_d2_boundary(d2_summary: dict[str, Any], score_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in score_rows:
        rows.append(
            {
                "evidence_item": row["comparison"],
                "observed_signal": row["interpretation"],
                "existing_metric_reused_read_only": True,
                "new_scoring_performed": False,
                "runtime_use_allowed": False,
                "admission_allowed": False,
                "claim_boundary": row["status"],
            }
        )
    rows.append(
        {
            "evidence_item": "D2_summary_decision",
            "observed_signal": d2_summary["decision"],
            "existing_metric_reused_read_only": True,
            "new_scoring_performed": False,
            "runtime_use_allowed": False,
            "admission_allowed": False,
            "claim_boundary": "D2 is evidence for study priority, not a released correction",
        }
    )
    return rows


def build_split_rows() -> list[dict[str, Any]]:
    return [
        {
            "split_or_claim": "train/support",
            "mf14_use": "existing diagnostic evidence and sensor-map bookkeeping only",
            "new_scoring": False,
            "model_selection": False,
            "release_or_admission": False,
        },
        {
            "split_or_claim": "validation",
            "mf14_use": "not used; any existing D2 transfer values are read-only prior package context",
            "new_scoring": False,
            "model_selection": False,
            "release_or_admission": False,
        },
        {
            "split_or_claim": "holdout",
            "mf14_use": "not used",
            "new_scoring": False,
            "model_selection": False,
            "release_or_admission": False,
        },
        {
            "split_or_claim": "external-test",
            "mf14_use": "not used",
            "new_scoring": False,
            "model_selection": False,
            "release_or_admission": False,
        },
    ]


def build_thesis_insert(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MF14 Same-QOI TP Projection UQ Gate",
            "",
            "MF14 separates sensor/QOI bookkeeping from a predictive bulk-to-TP correction. TP1-TP6 have documented 1D projection operators and bounded or mapped acceptance classes, so TP comparison can be described as a post-solve bulk-fluid projection target.",
            "",
            "The same evidence does not release a runtime TP correction. Quantitative same-QOI projection uncertainty is absent, runtime temperature input use remains false, and the D2 TP improvement is reused only as diagnostic context. No new validation, holdout, or external-test scoring was performed.",
            "",
            f"Release-ready TP projection rows: {summary['same_qoi_projection_release_ready_rows']} of {summary['tp_rows']}. The next rigorous step is a runtime wall/profile basis gate, because the D3 wall-shape signal cannot become a predictive correction until it has a source-bounded wall/profile operator and UQ boundary.",
        ]
    )


def build_readme(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MF14 Same-QOI TP Projection UQ Gate",
            "",
            "This package is the second queued MF13/MF12 follow-on study. It asks whether TP projection evidence is ready for predictive runtime use.",
            "",
            "## Decision",
            "",
            f"`{summary['decision']}`",
            "",
            "Same-QOI TP labels and projection operators exist diagnostically, but quantitative projection UQ and runtime temperature release do not.",
            "",
            "## Outputs",
            "",
            "- `tp_same_qoi_projection_uq.csv`: TP1-TP6 projection/UQ/runtime status.",
            "- `projection_release_gate.csv`: fail-closed release matrix.",
            "- `d2_reuse_boundary.csv`: how D2 evidence may be cited without new scoring or admission.",
            "- `split_claim_matrix.csv`: train/protected/external-test claim boundaries.",
            "- `thesis_tp_projection_uq_insert.md`: thesis-ready interpretation.",
            "- `next_study_queue.csv`: continuation sequence.",
            "",
            "## Claim Boundary",
            "",
            "No protected scoring, model selection, runtime-temperature release, bulk-to-TP correction release, source/property release, or coefficient admission is made here.",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n4_rows = read_csv(N4 / "sensor_qoi_projection_table.csv")
    op_rows = read_csv(PROJECTION_OP / "sensor_projection_operator_table.csv")
    d2_rows = read_csv(D2 / "tp_projection_thermal_development_evidence.csv")
    d2_score_rows = read_csv(D2 / "d2_score_improvement_summary.csv")
    d2_summary = json.loads((D2 / "summary.json").read_text())
    n4_summary = json.loads((N4 / "summary.json").read_text())
    op_summary = json.loads((PROJECTION_OP / "summary.json").read_text())

    tp_rows = build_tp_rows(n4_rows, op_rows, d2_rows)
    gate_rows = build_gate_rows(tp_rows)
    d2_boundary_rows = build_d2_boundary(d2_summary, d2_score_rows)
    split_rows = build_split_rows()
    next_rows = [
        {
            "priority": 1,
            "next_study": "runtime_wall_profile_basis_for_tp_projection",
            "why": "MF14 leaves TP correction release closed; D3 wall-shape evidence needs a runtime-legal wall/profile basis before TW/TP corrections can be admitted",
            "success_signal": "source-bounded wall/profile operator or fail-closed gap table with no protected scoring",
            "current_status_after_mf14": "next",
        },
        {
            "priority": 2,
            "next_study": "source_property_label_release_candidate_after_exact_fields",
            "why": "MF13 identified source/property gaps and MF14 identified projection-UQ gaps; source labels remain required before MF12 formulas",
            "success_signal": "explicit release/fail-closed table for q_setup, cp, segment map, and placement kernel",
            "current_status_after_mf14": "pending",
        },
        {
            "priority": 3,
            "next_study": "train_only_mf12_formula_smoke_after_release",
            "why": "Only after source/property, TP projection UQ, and wall/profile gates pass should formula execution occur",
            "success_signal": "train/support-only metrics and runtime-leakage audit",
            "current_status_after_mf14": "blocked_by_release_gates",
        },
        {
            "priority": 4,
            "next_study": "tw_after_tp_residual_ownership",
            "why": "TW residual ownership should wait until TP projection and wall/profile layers are separated",
            "success_signal": "TW residual-owner table after released or diagnostic TP projection subtraction",
            "current_status_after_mf14": "pending",
        },
    ]
    manifest_rows = [
        {"source_path": str(N4 / "sensor_qoi_projection_table.csv"), "use": "sensor acceptance class and runtime input audit", "mutation_status": "read_only"},
        {"source_path": str(PROJECTION_OP / "sensor_projection_operator_table.csv"), "use": "1D TP projection operators", "mutation_status": "read_only"},
        {"source_path": str(D2 / "tp_projection_thermal_development_evidence.csv"), "use": "TP thermal-development/projection diagnostic evidence", "mutation_status": "read_only"},
        {"source_path": str(D2 / "d2_score_improvement_summary.csv"), "use": "existing D2 diagnostic metric boundary, no new scoring", "mutation_status": "read_only"},
        {"source_path": str(MF13 / "next_study_queue.csv"), "use": "prior queue order", "mutation_status": "read_only"},
    ]
    guardrail_rows = [
        {"guardrail": "new validation scoring", "occurred": False},
        {"guardrail": "new holdout scoring", "occurred": False},
        {"guardrail": "external-test scoring", "occurred": False},
        {"guardrail": "fitting/tuning/model selection", "occurred": False},
        {"guardrail": "runtime temperature input release", "occurred": False},
        {"guardrail": "bulk-to-TP correction release", "occurred": False},
        {"guardrail": "source/property release", "occurred": False},
        {"guardrail": "coefficient admission", "occurred": False},
        {"guardrail": "Fluid solve or scheduler action", "occurred": False},
        {"guardrail": "native output or registry mutation", "occurred": False},
        {"guardrail": "residual absorbed into internal Nu", "occurred": False},
    ]
    summary = {
        "task_id": "TODO-MF14-SAME-QOI-TP-PROJECTION-UQ-GATE-2026-07-22",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "same_qoi_tp_projection_uq_fail_closed_no_runtime_temperature_release",
        "tp_rows": len(tp_rows),
        "same_qoi_label_rows": sum(row["same_qoi_label_present"] for row in tp_rows),
        "quantitative_same_qoi_uq_ready_rows": sum(row["quantitative_same_qoi_uq_ready"] for row in tp_rows),
        "runtime_temperature_allowed_rows": sum(row["runtime_temperature_allowed"] for row in tp_rows),
        "same_qoi_projection_release_ready_rows": sum(row["same_qoi_projection_release_ready"] for row in tp_rows),
        "d2_transfer_tp_rmse_K_read_only": d2_summary["d2_transfer_tp_rmse_K"],
        "m3_transfer_tp_rmse_K_read_only": d2_summary["m3_transfer_tp_rmse_K"],
        "n4_runtime_temperature_allowed_rows": n4_summary["runtime_temperature_allowed_rows"],
        "projection_operator_bulk_to_tp_released": op_summary["bulk_to_tp_correction_released"],
        "new_validation_holdout_external_scoring": False,
        "runtime_temperature_input_release": False,
        "source_property_release": False,
        "bulk_to_tp_correction_release": False,
        "coefficient_admission": False,
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(
        OUT_DIR / "tp_same_qoi_projection_uq.csv",
        tp_rows,
        [
            "sensor",
            "kind",
            "acceptance_class",
            "one_d_segment_or_state",
            "one_d_fraction_or_marker",
            "projection_operator",
            "projection_equation",
            "mapped_developing_span",
            "current_projection",
            "thermal_development_evidence",
            "litrev_allowed_rows",
            "litrev_uq_blocked_rows",
            "example_x_from_reset_m",
            "example_L_over_D_from_reset",
            "thermal_reset_status",
            "same_qoi_label_present",
            "quantitative_same_qoi_uq_ready",
            "runtime_temperature_allowed",
            "fit_allowed",
            "model_selection_allowed",
            "bulk_to_tp_correction_released",
            "same_qoi_projection_release_ready",
            "uq_status",
            "uncertainty_caveat",
            "claim_allowed_now",
            "blocking_gap",
        ],
    )
    write_csv(OUT_DIR / "projection_release_gate.csv", gate_rows, ["gate", "status", "evidence", "release_allowed", "missing_for_release"])
    write_csv(OUT_DIR / "d2_reuse_boundary.csv", d2_boundary_rows, ["evidence_item", "observed_signal", "existing_metric_reused_read_only", "new_scoring_performed", "runtime_use_allowed", "admission_allowed", "claim_boundary"])
    write_csv(OUT_DIR / "split_claim_matrix.csv", split_rows, ["split_or_claim", "mf14_use", "new_scoring", "model_selection", "release_or_admission"])
    write_csv(OUT_DIR / "next_study_queue.csv", next_rows, ["priority", "next_study", "why", "success_signal", "current_status_after_mf14"])
    write_csv(OUT_DIR / "source_manifest.csv", manifest_rows, ["source_path", "use", "mutation_status"])
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows, ["guardrail", "occurred"])

    (OUT_DIR / "thesis_tp_projection_uq_insert.md").write_text(build_thesis_insert(summary) + "\n")
    (OUT_DIR / "README.md").write_text(build_readme(summary) + "\n")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
