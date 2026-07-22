#!/usr/bin/env python3
"""Build MF16 source/property exact-fields release candidate gate."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate"

NOMINAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
MF13 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight"
MF15 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate"


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


def build_exact_field_matrix(
    nominal_rows: list[dict[str, str]],
    mf13_rows: list[dict[str, str]],
    mf15_requirements: list[dict[str, str]],
) -> list[dict[str, Any]]:
    labels_complete = sum(parse_bool(row["labels_complete"]) for row in nominal_rows)
    release_ready = sum(parse_bool(row["release_ready"]) for row in nominal_rows)
    setup_active_rows = [row for row in mf13_rows if row["setup_provenance_status"] == "setup_known_candidate"]
    source_conservation_rows = [
        row for row in mf15_requirements
        if row["requirement"] == "source_property_conservation" and row["applies"] == "True"
    ]
    runtime_temp_rows = [
        row for row in mf15_requirements
        if row["requirement"] == "runtime_temperature_release" and row["applies"] == "True"
    ]
    return [
        {
            "exact_field": "q_setup_sign_and_magnitude",
            "current_evidence": f"{len(setup_active_rows)} MF13 active source/sink rows have setup sign and magnitude metadata",
            "field_presence_status": "present_as_setup_metadata",
            "release_blocker": "runtime_allowed_now false and source_property_released_now false in MF13",
            "release_ready": False,
            "claim_allowed": "diagnostic directionality only",
            "next_required_evidence": "row-specific runtime source contract with no realized wallHeatFlux, no validation temperatures, and no residual fill",
        },
        {
            "exact_field": "cp_property_basis",
            "current_evidence": f"{labels_complete} nominal rows have nonblank property labels, but property sensitivity remains material-closure-fit-blocked",
            "field_presence_status": "partial_label_presence",
            "release_blocker": "property sensitivity and material closure not released for predictive formula use",
            "release_ready": False,
            "claim_allowed": "property family provenance only",
            "next_required_evidence": "candidate-specific cp/property sensitivity table using setup-known property basis only",
        },
        {
            "exact_field": "segment_source_placement_kernel",
            "current_evidence": "setup patch/group labels exist; nominal release preflight says source envelope is not strict row-specific",
            "field_presence_status": "labels_present_but_source_envelope_not_strict",
            "release_blocker": "Salt1 lacks row-specific branch envelope; Salt2/Salt3/Salt4 remain mixed/outside/unknown",
            "release_ready": False,
            "claim_allowed": "source placement gap can be named, not consumed",
            "next_required_evidence": "strict row-specific source-envelope pass for each train row and candidate source family",
        },
        {
            "exact_field": "wall_profile_source_property_conservation",
            "current_evidence": f"{len(source_conservation_rows)} MF15 source/property conservation requirement rows fail closed",
            "field_presence_status": "failed_conservation_release",
            "release_blocker": "D3/MF15 source/property conservation release failed",
            "release_ready": False,
            "claim_allowed": "diagnostic wall/profile mechanism only",
            "next_required_evidence": "same-mask energy residual and conservation ledger for wall/core exchange control volume",
        },
        {
            "exact_field": "runtime_temperature_and_wall_state_use",
            "current_evidence": f"{len(runtime_temp_rows)} MF15 runtime-temperature requirement rows fail closed",
            "field_presence_status": "runtime_temperature_release_false",
            "release_blocker": "N4/MF14 runtime temperature allowed rows are zero",
            "release_ready": False,
            "claim_allowed": "post-solve score target only",
            "next_required_evidence": "runtime wall/bulk state use boundary that excludes TP/TW validation temperatures",
        },
        {
            "exact_field": "release_candidate_gate",
            "current_evidence": f"{release_ready} nominal rows release-ready; protected rows released = 0",
            "field_presence_status": "no_release_candidate",
            "release_blocker": "source-envelope strict pass and candidate-specific physical gate both fail",
            "release_ready": False,
            "claim_allowed": "fail-closed release decision",
            "next_required_evidence": "one physical candidate with strict source/property, split, runtime, and UQ gates",
        },
    ]


def build_row_candidate_matrix(nominal_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in nominal_rows:
        rows.append(
            {
                "case_key": row["case_key"],
                "normalized_case_id": row["normalized_case_id"],
                "final_scorecard_partition": row["final_scorecard_partition"],
                "labels_complete": parse_bool(row["labels_complete"]),
                "property_mode": row["property_mode"],
                "source_validity_envelope_status": row["source_validity_envelope_status"],
                "source_use_category": row["source_use_category"],
                "source_property_gate_status": row["source_property_gate_status"],
                "final_fit_allowed": row["final_fit_allowed"],
                "final_model_selection_allowed": row["final_model_selection_allowed"],
                "release_ready": parse_bool(row["release_ready"]),
                "release_decision": row["release_decision"],
                "primary_blocker": row["primary_blocker"],
                "next_action": row["next_action"],
                "protected_row_release": parse_bool(row["protected_row_release"]),
            }
        )
    return rows


def build_release_gate_rows(blocker_rows: list[dict[str, str]], field_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "gate": row["gate"],
            "status": row["status"],
            "evidence": row["evidence"],
            "release_allowed": False,
            "candidate_freeze_allowed": False,
            "next_action": row["s11_s15_action"],
        }
        for row in blocker_rows
    ]
    rows.append(
        {
            "gate": "exact_field_matrix_all_release_ready",
            "status": "fail",
            "evidence": f"{sum(row['release_ready'] for row in field_rows)} of {len(field_rows)} exact-field gates release-ready",
            "release_allowed": False,
            "candidate_freeze_allowed": False,
            "next_action": "do not open S11/S15/S6",
        }
    )
    return rows


def build_readme(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MF16 Source/Property Exact-Fields Release Candidate",
            "",
            f"Decision: `{summary['decision']}`.",
            "",
            "This package checks exact missing fields after MF13/MF15. It does not release source/property rows and does not open S11/S15/S6.",
            "",
            "Core result: labels exist on nominal rows, but strict row-specific source-envelope evidence, candidate-specific property sensitivity, wall/profile conservation, and runtime-use permissions are still missing.",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nominal_rows = read_csv(NOMINAL / "nominal_train_release_audit.csv")
    blocker_rows = read_csv(NOMINAL / "s11_s15_blocker_matrix.csv")
    family_rollup = read_csv(NOMINAL / "source_family_blocker_rollup.csv")
    lane_rows = read_csv(NOMINAL / "candidate_lane_consequences.csv")
    mf13_rows = read_csv(MF13 / "signed_heat_path_release_preflight.csv")
    mf15_requirements = read_csv(MF15 / "runtime_operator_requirement_matrix.csv")
    nominal_summary = json.loads((NOMINAL / "summary.json").read_text())
    mf13_summary = json.loads((MF13 / "summary.json").read_text())
    mf15_summary = json.loads((MF15 / "summary.json").read_text())

    field_rows = build_exact_field_matrix(nominal_rows, mf13_rows, mf15_requirements)
    row_matrix = build_row_candidate_matrix(nominal_rows)
    release_gate_rows = build_release_gate_rows(blocker_rows, field_rows)
    next_rows = [
        {
            "priority": 1,
            "next_study": "strict_row_specific_source_envelope_recovery",
            "why": "MF16 blocks primarily on row-specific strict-pass source-envelope evidence",
            "success_signal": "Salt1/Salt2 train rows have strict source-envelope pass without protected-row leakage",
            "status_after_mf16": "next_serial",
        },
        {
            "priority": 2,
            "next_study": "same_qoi_wall_core_exchange_uq_execution",
            "why": "MF15 says triplets exist and MF17 can preserve temporal UQ evidence for wall/core mechanism",
            "success_signal": "Qwall/exchange/recirc/wall-core temporal UQ summarized with no admission",
            "status_after_mf16": "parallel_ready",
        },
        {
            "priority": 3,
            "next_study": "candidate_specific_cp_property_sensitivity_gate",
            "why": "property labels exist but sensitivity remains material-closure-fit-blocked",
            "success_signal": "cp/property uncertainty envelope for exactly one physical candidate",
            "status_after_mf16": "pending",
        },
    ]
    manifest_rows = [
        {"source_path": str(NOMINAL / "nominal_train_release_audit.csv"), "use": "nominal row source/property release status", "mutation_status": "read_only"},
        {"source_path": str(NOMINAL / "s11_s15_blocker_matrix.csv"), "use": "release and freeze blockers", "mutation_status": "read_only"},
        {"source_path": str(NOMINAL / "candidate_lane_consequences.csv"), "use": "candidate-lane consequences", "mutation_status": "read_only"},
        {"source_path": str(MF13 / "signed_heat_path_release_preflight.csv"), "use": "q_setup sign/magnitude and runtime source status", "mutation_status": "read_only"},
        {"source_path": str(MF15 / "runtime_operator_requirement_matrix.csv"), "use": "wall/profile conservation and runtime-use requirements", "mutation_status": "read_only"},
    ]
    guardrail_rows = [
        {"guardrail": "source/property release", "occurred": False},
        {"guardrail": "candidate freeze", "occurred": False},
        {"guardrail": "S11/S12/S13/S15/S6 trigger", "occurred": False},
        {"guardrail": "validation/holdout/external scoring", "occurred": False},
        {"guardrail": "fitting/tuning/model selection", "occurred": False},
        {"guardrail": "Fluid solve or scheduler action", "occurred": False},
        {"guardrail": "native output or registry mutation", "occurred": False},
        {"guardrail": "residual absorbed into internal Nu", "occurred": False},
    ]
    summary = {
        "task_id": "TODO-MF16-SOURCE-PROPERTY-EXACT-FIELDS-RELEASE-CANDIDATE-2026-07-22",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "source_property_exact_fields_release_candidate_fail_closed_no_release",
        "nominal_rows": len(nominal_rows),
        "labels_complete_rows": nominal_summary["labels_complete_rows"],
        "nominal_release_ready_rows": nominal_summary["release_ready_rows"],
        "mf13_release_ready_rows": mf13_summary["release_ready_rows"],
        "mf15_wall_profile_release_ready_rows": mf15_summary["wall_profile_correction_release_ready_rows"],
        "exact_field_rows": len(field_rows),
        "exact_field_release_ready_rows": sum(row["release_ready"] for row in field_rows),
        "protected_rows_released": nominal_summary["protected_rows_released"],
        "candidate_freeze": False,
        "source_property_release": False,
        "s11_s15_s6_opened": False,
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection": False,
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(OUT_DIR / "exact_field_release_matrix.csv", field_rows, ["exact_field", "current_evidence", "field_presence_status", "release_blocker", "release_ready", "claim_allowed", "next_required_evidence"])
    write_csv(OUT_DIR / "row_level_release_candidate_matrix.csv", row_matrix, ["case_key", "normalized_case_id", "final_scorecard_partition", "labels_complete", "property_mode", "source_validity_envelope_status", "source_use_category", "source_property_gate_status", "final_fit_allowed", "final_model_selection_allowed", "release_ready", "release_decision", "primary_blocker", "next_action", "protected_row_release"])
    write_csv(OUT_DIR / "source_family_blocker_rollup.csv", family_rollup, list(family_rollup[0].keys()))
    write_csv(OUT_DIR / "candidate_lane_consequences.csv", lane_rows, list(lane_rows[0].keys()))
    write_csv(OUT_DIR / "release_candidate_gate.csv", release_gate_rows, ["gate", "status", "evidence", "release_allowed", "candidate_freeze_allowed", "next_action"])
    write_csv(OUT_DIR / "next_study_queue.csv", next_rows, ["priority", "next_study", "why", "success_signal", "status_after_mf16"])
    write_csv(OUT_DIR / "source_manifest.csv", manifest_rows, ["source_path", "use", "mutation_status"])
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows, ["guardrail", "occurred"])
    (OUT_DIR / "README.md").write_text(build_readme(summary) + "\n")
    (OUT_DIR / "thesis_source_property_exact_fields_insert.md").write_text(
        "# MF16 Source/Property Exact-Fields Release Candidate\n\n"
        "MF16 finds no releasable source/property candidate. The useful result is the exact blocker set: q_setup is setup metadata only, cp/property labels are partial and sensitivity-blocked, source placement lacks strict row-specific source envelopes, wall/profile conservation failed, and runtime temperature/wall-state use is not released.\n\n"
        "This supports a rigorous no-freeze thesis claim while preserving the path to a future strict source-envelope recovery study.\n"
    )
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
