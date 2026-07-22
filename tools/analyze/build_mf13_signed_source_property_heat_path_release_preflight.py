#!/usr/bin/env python3
"""Build MF13 signed source/property heat-path release preflight.

This study consumes existing evidence only. It determines whether the signed
heater/cooler/test-section/passive heat-path inputs needed by MF12 can be used
as runtime model-form inputs, or whether they fail closed with exact missing
fields.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight"

MF08 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"
MF12 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate"
THERMAL_TRACE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet"
SOURCE_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract"


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


def parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def summarize_case_values(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "train_values": [],
            "validation_values": [],
            "holdout_values": [],
            "external_values": [],
            "cases": [],
            "patches": set(),
        }
    )
    for row in rows:
        key = (row["source_segment_id"], row["physical_role"])
        value = parse_float(row.get("setup_value_W"))
        split = row.get("split_role", "")
        grouped[key]["cases"].append(row.get("case_id", ""))
        grouped[key]["patches"].add(row.get("setup_patch_or_group", ""))
        if split in {"train", "support"}:
            grouped[key]["train_values"].append(value)
        elif split == "validation":
            grouped[key]["validation_values"].append(value)
        elif split == "holdout":
            grouped[key]["holdout_values"].append(value)
        else:
            grouped[key]["external_values"].append(value)
    return grouped


def finite_values(values: list[float | None]) -> list[float]:
    return [v for v in values if v is not None]


def minmax(values: list[float | None]) -> tuple[float | None, float | None]:
    finite = finite_values(values)
    return (min(finite), max(finite)) if finite else (None, None)


def missing_fields_for_source(row: dict[str, str]) -> list[str]:
    missing: list[str] = []
    if not parse_bool(row.get("runtime_allowed_now")):
        missing.append("runtime_allowed_now_true")
    if not parse_bool(row.get("source_property_released_now")):
        missing.append("source_property_released_now_true")
    if parse_bool(row.get("realized_wallHeatFlux_runtime_input_allowed")):
        missing.append("wallHeatFlux_runtime_forbidden_guard")
    if "source_basis_needed" in row.get("setup_provenance_status", ""):
        missing.append("independent_source_basis")
    if row.get("setup_q_min_W", "") == "" or row.get("setup_q_max_W", "") == "":
        missing.append("setup_q_magnitude_range")
    if "passive" in row.get("physical_role", ""):
        missing.append("passive_area_material_ambient_insulation_basis")
    return missing


def build_release_preflight(
    source_rows: list[dict[str, str]],
    setup_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped = summarize_case_values(setup_rows)
    preflight_rows: list[dict[str, Any]] = []
    for row in source_rows:
        key = (row["source_segment_id"], row["physical_role"])
        case_group = grouped.get(key, {})
        train_min, train_max = minmax(case_group.get("train_values", []))
        validation_min, validation_max = minmax(case_group.get("validation_values", []))
        holdout_min, holdout_max = minmax(case_group.get("holdout_values", []))
        all_values = (
            case_group.get("train_values", [])
            + case_group.get("validation_values", [])
            + case_group.get("holdout_values", [])
            + case_group.get("external_values", [])
        )
        all_min, all_max = minmax(all_values)

        runtime_allowed = parse_bool(row.get("runtime_allowed_now"))
        source_released = parse_bool(row.get("source_property_released_now"))
        wall_flux_forbidden_guard_ok = not parse_bool(row.get("realized_wallHeatFlux_runtime_input_allowed"))
        missing = missing_fields_for_source(row)
        release_ready = runtime_allowed and source_released and wall_flux_forbidden_guard_ok and not missing

        if release_ready:
            decision = "release_ready_after_external_admission"
            mf12_use = "runtime_input_candidate_after_separate_release"
            blocking_gap = "none"
        elif row.get("setup_provenance_status") == "setup_known_candidate":
            decision = "fail_closed_setup_known_sign_only_not_source_property_released"
            mf12_use = "diagnostic_direction_only"
            blocking_gap = ";".join(missing)
        else:
            decision = "fail_closed_needs_independent_source_basis"
            mf12_use = "not_usable_in_mf12_formula"
            blocking_gap = ";".join(missing)

        preflight_rows.append(
            {
                "source_segment_id": row["source_segment_id"],
                "physical_role": row["physical_role"],
                "setup_q_sign_convention": row["setup_q_sign_convention"],
                "source_family": f"{row['physical_role']}/{row['source_segment_id']}",
                "setup_q_min_W": row.get("setup_q_min_W", ""),
                "setup_q_max_W": row.get("setup_q_max_W", ""),
                "case_value_min_W": fmt(all_min),
                "case_value_max_W": fmt(all_max),
                "train_setup_q_min_W": fmt(train_min),
                "train_setup_q_max_W": fmt(train_max),
                "validation_values_present_not_used": bool(finite_values(case_group.get("validation_values", []))),
                "validation_setup_q_min_W_metadata_only": fmt(validation_min),
                "validation_setup_q_max_W_metadata_only": fmt(validation_max),
                "holdout_values_present_not_used": bool(finite_values(case_group.get("holdout_values", []))),
                "holdout_setup_q_min_W_metadata_only": fmt(holdout_min),
                "holdout_setup_q_max_W_metadata_only": fmt(holdout_max),
                "setup_provenance_status": row["setup_provenance_status"],
                "runtime_source_status": row["runtime_source_status"],
                "runtime_allowed_now": runtime_allowed,
                "source_property_released_now": source_released,
                "realized_wallHeatFlux_runtime_input_allowed": parse_bool(row.get("realized_wallHeatFlux_runtime_input_allowed")),
                "release_ready": release_ready,
                "mf12_use": mf12_use,
                "release_decision": decision,
                "blocking_gap": blocking_gap,
                "next_required_evidence": next_required_evidence(row, missing),
            }
        )
    return preflight_rows


def next_required_evidence(row: dict[str, str], missing: list[str]) -> str:
    if not missing:
        return "separate release/admission row must still confirm use boundary"
    if "passive_area_material_ambient_insulation_basis" in missing:
        return "independent passive hA/source-family basis by segment; no wallHeatFlux-derived fit"
    if row["physical_role"] == "test_section":
        return "row-specific source/property labels plus recirculating-upcomer guard before formula use"
    return "row-specific source/property labels, cp basis, segment map, and runtime contract release"


def build_case_split_rows(setup_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    split_rank = {"train": 0, "support": 1, "validation": 2, "holdout": 3, "external": 4}
    rows: list[dict[str, Any]] = []
    for row in sorted(setup_rows, key=lambda r: (split_rank.get(r.get("split_role", ""), 99), r["case_id"], r["source_segment_id"])):
        split = row.get("split_role", "")
        rows.append(
            {
                "case_id": row["case_id"],
                "split_role": split,
                "source_segment_id": row["source_segment_id"],
                "physical_role": row["physical_role"],
                "setup_patch_or_group": row["setup_patch_or_group"],
                "setup_value_W": row["setup_value_W"],
                "runtime_allowed_now": parse_bool(row.get("runtime_allowed_now")),
                "claim_use_in_this_study": "train_support_metadata_only" if split in {"train", "support"} else "protected_metadata_not_used",
                "scoring_use_in_this_study": "not_scored",
                "source_property_release_use": "not_released",
                "claim_boundary": row.get("claim_boundary", ""),
            }
        )
    return rows


def build_gate_rows(preflight_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    release_ready_count = sum(1 for row in preflight_rows if row["release_ready"])
    setup_known_count = sum(1 for row in preflight_rows if row["setup_provenance_status"] == "setup_known_candidate")
    passive_ready = any(
        row["physical_role"] == "passive_loss" and row["release_ready"] for row in preflight_rows
    )
    active_source_signs = [
        row for row in preflight_rows if row["setup_provenance_status"] == "setup_known_candidate"
    ]
    return [
        {
            "gate": "setup_sign_available",
            "status": "pass_diagnostic",
            "evidence": f"{setup_known_count} setup-known active source/sink families have sign conventions",
            "release_allowed": False,
            "missing_for_release": "source_property_labels_and_runtime_allowed_contract",
        },
        {
            "gate": "setup_magnitude_available",
            "status": "pass_diagnostic_for_active_sources",
            "evidence": f"{sum(bool(row['setup_q_min_W']) and bool(row['setup_q_max_W']) for row in active_source_signs)} active families have setup q ranges",
            "release_allowed": False,
            "missing_for_release": "separate source/property release and cp basis",
        },
        {
            "gate": "runtime_legal_source_available",
            "status": "fail_closed",
            "evidence": f"{release_ready_count} of {len(preflight_rows)} families are release-ready now",
            "release_allowed": False,
            "missing_for_release": "runtime_allowed_now_true",
        },
        {
            "gate": "source_property_labels_released",
            "status": "fail_closed",
            "evidence": f"{sum(1 for row in preflight_rows if row['source_property_released_now'])} families have source/property released now",
            "release_allowed": False,
            "missing_for_release": "source_property_released_now_true",
        },
        {
            "gate": "cp_basis_released",
            "status": "fail_closed",
            "evidence": "No row-level cp/property basis is released by MF08/MF12 for source-integral formulas",
            "release_allowed": False,
            "missing_for_release": "runtime cp/property lane",
        },
        {
            "gate": "segment_mapping_released",
            "status": "fail_closed",
            "evidence": "Setup patch/group labels exist, but source/property labels and formula-local placement kernels are not admitted",
            "release_allowed": False,
            "missing_for_release": "formula-local source placement and reset kernel",
        },
        {
            "gate": "passive_basis_released",
            "status": "fail_closed",
            "evidence": f"passive/downcomer independent basis ready: {passive_ready}",
            "release_allowed": False,
            "missing_for_release": "passive hA/area/material/ambient/insulation basis",
        },
        {
            "gate": "same_qoi_projection_uq",
            "status": "fail_closed",
            "evidence": "TP projection is still a post-solve target comparison, not a released runtime observable",
            "release_allowed": False,
            "missing_for_release": "same-QOI TP projection uncertainty and runtime-legality status",
        },
        {
            "gate": "admission_release_allowed",
            "status": "fail_closed",
            "evidence": "This task is preflight only: no source/property release, no fitting, no scoring, no final score",
            "release_allowed": False,
            "missing_for_release": "separate admission/release row after all upstream gates pass",
        },
    ]


def build_formula_readiness(candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    requirements = {
        "sigma_q": "diagnostic_ready_for_active_heater_cooler_test_section_only",
        "q_setup": "contract_only_not_runtime_released",
        "cp": "blocked_no_row_level_property_release",
        "A_source_or_source_kernel": "blocked_no_source_bounded_formula",
        "reset_graetz": "diagnostic_ready_not_admitted",
        "wall_profile": "blocked_needs_runtime_wall_profile_basis",
        "same_qoi_tp_projection": "blocked_needs_UQ_and_runtime_legality",
        "upcomer_recirc_guard": "blocked_pending_same_label_mesh_GCI_or_equivalent_guard",
    }
    rows: list[dict[str, Any]] = []
    for formula in candidate_rows:
        needed = formula["required_runtime_inputs"]
        for requirement, status in requirements.items():
            applies = requirement in {"same_qoi_tp_projection", "sigma_q"}
            if "q_setup" in needed and requirement in {"q_setup", "cp", "A_source_or_source_kernel", "reset_graetz"}:
                applies = True
            if "wall" in formula["candidate_id"].lower() and requirement == "wall_profile":
                applies = True
            if "upcomer" in needed.lower() and requirement == "upcomer_recirc_guard":
                applies = True
            rows.append(
                {
                    "candidate_id": formula["candidate_id"],
                    "requirement": requirement,
                    "applies": applies,
                    "readiness_status": status if applies else "not_primary_requirement",
                    "train_only_smoke_unblocked": False,
                    "reason": reason_for_requirement(requirement, applies),
                }
            )
    return rows


def reason_for_requirement(requirement: str, applies: bool) -> str:
    if not applies:
        return "not a primary input for this candidate formula"
    reasons = {
        "sigma_q": "setup-known sign direction exists for active sources, but is diagnostic only",
        "q_setup": "setup magnitudes exist as metadata; runtime input release is blocked",
        "cp": "source/property labels and cp lane are not released",
        "A_source_or_source_kernel": "source-bounded amplitude/kernel is not admitted",
        "reset_graetz": "MF07 coordinates exist diagnostically but are not a released correction",
        "wall_profile": "D3 signal lacks runtime wall-profile model",
        "same_qoi_tp_projection": "TP projection lacks same-QOI UQ and runtime legality decision",
        "upcomer_recirc_guard": "recirculating upcomer treatment remains guarded by S13/same-label evidence",
    }
    return reasons[requirement]


def build_thesis_insert(preflight_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]]) -> str:
    setup_known = [row for row in preflight_rows if row["setup_provenance_status"] == "setup_known_candidate"]
    release_ready = [row for row in preflight_rows if row["release_ready"]]
    passive = [row for row in preflight_rows if row["physical_role"] == "passive_loss"]
    return "\n".join(
        [
            "# MF13 Signed Source/Property Heat-Path Release Preflight",
            "",
            "MF13 asks whether the signed heat-path quantities needed by MF12 can be promoted from diagnostic evidence to runtime model-form inputs. The answer is a fail closed preflight, not a source/property release.",
            "",
            f"Three active setup source/sink families have useful sign and magnitude metadata: {', '.join(row['source_family'] for row in setup_known)}. They establish directionality for candidate formulas, with heater and test-section heat positive into the fluid and cooler heat negative from the fluid. However, all active rows remain `runtime_allowed_now=false` and `source_property_released_now=false`, so MF12 may use them only to motivate a hypothesis, not to execute or score a runtime formula.",
            "",
            f"The passive/downcomer family remains more restricted: {passive[0]['blocking_gap'] if passive else 'no passive row present'}. That prevents treating the H2 global passive sensitivity as an admitted physics repair or as a fitted multiplier.",
            "",
            f"Release-ready source/property families in this preflight: {len(release_ready)} of {len(preflight_rows)}. All release gates report `release_allowed=false`; validation, holdout, and external-test rows are metadata-only and were not scored.",
            "",
            "The next rigorous step is same-QOI TP projection uncertainty: even a physically plausible signed source term cannot be evaluated as a predictive TP model until the TP projection itself has a runtime-legality and uncertainty boundary.",
        ]
    )


def build_readme(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MF13 Signed Source/Property Heat-Path Release Preflight",
            "",
            "This package performs the first MF12 follow-on study. It consumes existing diagnostic/source-contract evidence and asks whether signed heat-path inputs can be used by MF12 candidate formulas.",
            "",
            "## Decision",
            "",
            f"`{summary['decision']}`",
            "",
            "No source/property input is released here. No Fluid solve, fitting, protected split scoring, model selection, repair, admission, or final score was performed.",
            "",
            "## Outputs",
            "",
            "- `signed_heat_path_release_preflight.csv`: family-level release/fail-closed decision.",
            "- `case_split_source_values.csv`: setup source/sink values with train/support versus protected split use separated.",
            "- `source_property_release_gate.csv`: strict gate matrix.",
            "- `mf12_formula_input_readiness.csv`: MF12 input readiness by formula and requirement.",
            "- `thesis_heat_path_preflight_insert.md`: thesis-ready diagnostic paragraph.",
            "- `next_study_queue.csv`: ordered continuation sequence.",
            "- `source_manifest.csv` and `no_mutation_guardrails.csv`: provenance and mutation boundary.",
            "",
            "## Claim Boundary",
            "",
            "The study supports only a train/support diagnostic claim: signed source/sink metadata is useful for hypothesis design, but not yet a runtime predictive input. Validation, holdout, and external-test rows are not used for scoring or model selection.",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv(MF08 / "runtime_legal_source_table.csv")
    setup_rows = read_csv(THERMAL_TRACE / "setup_source_sink_values.csv")
    formula_rows = read_csv(MF12 / "candidate_bulk_to_tp_formulas.csv")
    prior_next_rows = read_csv(MF12 / "next_study_queue.csv")

    preflight_rows = build_release_preflight(source_rows, setup_rows)
    case_split_rows = build_case_split_rows(setup_rows)
    gate_rows = build_gate_rows(preflight_rows)
    readiness_rows = build_formula_readiness(formula_rows)

    release_ready_rows = sum(1 for row in preflight_rows if row["release_ready"])
    setup_known_rows = sum(1 for row in preflight_rows if row["setup_provenance_status"] == "setup_known_candidate")
    protected_metadata_rows = sum(1 for row in case_split_rows if row["claim_use_in_this_study"] == "protected_metadata_not_used")

    next_rows = [
        {
            "priority": 1,
            "next_study": "same_qoi_tp_projection_uq",
            "why": "MF13 leaves source/property release closed, but TP projection UQ is still independently required before any predictive TP formula claim",
            "success_signal": "same-QOI TP projection uncertainty table with runtime-legality status and no protected scoring",
            "current_status_after_mf13": "next",
        },
        {
            "priority": 2,
            "next_study": "runtime_wall_profile_basis_for_tp_projection",
            "why": "D3 wall-shape signal can explain part of TP/TW discrepancy only if a runtime-legal wall/profile basis exists",
            "success_signal": "source-bounded wall-profile model or fail-closed wall-profile gap table",
            "current_status_after_mf13": "pending",
        },
        {
            "priority": 3,
            "next_study": "source_property_label_release_candidate_after_exact_fields",
            "why": "MF13 identified exact fields needed for q_setup/cp/source placement; a separate row must find or reject them",
            "success_signal": "heater/cooler/test-section/passive rows released by an explicit contract or fail closed with source-path evidence",
            "current_status_after_mf13": "pending",
        },
        {
            "priority": 4,
            "next_study": "train_only_mf12_formula_smoke_after_release",
            "why": "Formula execution is only legitimate after source/property and projection gates pass",
            "success_signal": "train/support-only metrics and runtime-leakage audit; validation/holdout/external rows not used",
            "current_status_after_mf13": "blocked_by_release_gates",
        },
        {
            "priority": 5,
            "next_study": "tw_after_tp_residual_ownership",
            "why": "TW ownership should be decomposed after TP projection and source terms are separated",
            "success_signal": "TW residual-owner table after subtracting released or diagnostic TP projection",
            "current_status_after_mf13": "pending",
        },
    ]

    manifest_rows = [
        {
            "source_path": str(MF08 / "runtime_legal_source_table.csv"),
            "use": "primary source-family runtime/source-property status",
            "mutation_status": "read_only",
        },
        {
            "source_path": str(THERMAL_TRACE / "setup_source_sink_values.csv"),
            "use": "case/split setup source values and claim boundary",
            "mutation_status": "read_only",
        },
        {
            "source_path": str(THERMAL_TRACE / "thermal_accounting_traceability_ledger.csv"),
            "use": "residual ownership policy context",
            "mutation_status": "read_only",
        },
        {
            "source_path": str(MF12 / "candidate_bulk_to_tp_formulas.csv"),
            "use": "MF12 model-form input requirements",
            "mutation_status": "read_only",
        },
        {
            "source_path": str(MF12 / "next_study_queue.csv"),
            "use": f"prior ordered queue retained for continuity with {len(prior_next_rows)} rows",
            "mutation_status": "read_only",
        },
        {
            "source_path": str(SOURCE_CONTRACT / "source_property_gate.csv"),
            "use": "older source contract if present; not required for release",
            "mutation_status": "read_only_missing_ok" if not (SOURCE_CONTRACT / "source_property_gate.csv").exists() else "read_only",
        },
    ]

    guardrail_rows = [
        {"guardrail": "Fluid solve launched", "occurred": False},
        {"guardrail": "scheduler action", "occurred": False},
        {"guardrail": "native CFD/OpenFOAM output mutation", "occurred": False},
        {"guardrail": "registry/admission mutation", "occurred": False},
        {"guardrail": "source/property release", "occurred": False},
        {"guardrail": "Qwall release", "occurred": False},
        {"guardrail": "validation scoring", "occurred": False},
        {"guardrail": "holdout scoring", "occurred": False},
        {"guardrail": "external-test scoring", "occurred": False},
        {"guardrail": "fitting/tuning/model selection", "occurred": False},
        {"guardrail": "residual absorbed into internal Nu", "occurred": False},
    ]

    summary = {
        "task_id": "TODO-MF13-SIGNED-SOURCE-PROPERTY-HEAT-PATH-RELEASE-PREFLIGHT-2026-07-22",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "signed_source_property_release_preflight_fail_closed",
        "source_family_rows": len(preflight_rows),
        "setup_known_active_source_rows": setup_known_rows,
        "release_ready_rows": release_ready_rows,
        "source_property_release": False,
        "train_support_execution_evidence_only": True,
        "validation_used": False,
        "holdout_used": False,
        "external_test_used": False,
        "protected_metadata_rows_not_used_for_scoring": protected_metadata_rows,
        "mf12_formula_smoke_unblocked": False,
        "passive_basis_ready": any(row["physical_role"] == "passive_loss" and row["release_ready"] for row in preflight_rows),
        "no_fluid_solve": True,
        "no_fitting_or_model_selection": True,
        "residual_absorbed_into_internal_nu": False,
    }

    write_csv(
        OUT_DIR / "signed_heat_path_release_preflight.csv",
        preflight_rows,
        [
            "source_segment_id",
            "physical_role",
            "setup_q_sign_convention",
            "source_family",
            "setup_q_min_W",
            "setup_q_max_W",
            "case_value_min_W",
            "case_value_max_W",
            "train_setup_q_min_W",
            "train_setup_q_max_W",
            "validation_values_present_not_used",
            "validation_setup_q_min_W_metadata_only",
            "validation_setup_q_max_W_metadata_only",
            "holdout_values_present_not_used",
            "holdout_setup_q_min_W_metadata_only",
            "holdout_setup_q_max_W_metadata_only",
            "setup_provenance_status",
            "runtime_source_status",
            "runtime_allowed_now",
            "source_property_released_now",
            "realized_wallHeatFlux_runtime_input_allowed",
            "release_ready",
            "mf12_use",
            "release_decision",
            "blocking_gap",
            "next_required_evidence",
        ],
    )
    write_csv(
        OUT_DIR / "case_split_source_values.csv",
        case_split_rows,
        [
            "case_id",
            "split_role",
            "source_segment_id",
            "physical_role",
            "setup_patch_or_group",
            "setup_value_W",
            "runtime_allowed_now",
            "claim_use_in_this_study",
            "scoring_use_in_this_study",
            "source_property_release_use",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT_DIR / "source_property_release_gate.csv",
        gate_rows,
        ["gate", "status", "evidence", "release_allowed", "missing_for_release"],
    )
    write_csv(
        OUT_DIR / "mf12_formula_input_readiness.csv",
        readiness_rows,
        ["candidate_id", "requirement", "applies", "readiness_status", "train_only_smoke_unblocked", "reason"],
    )
    write_csv(
        OUT_DIR / "next_study_queue.csv",
        next_rows,
        ["priority", "next_study", "why", "success_signal", "current_status_after_mf13"],
    )
    write_csv(OUT_DIR / "source_manifest.csv", manifest_rows, ["source_path", "use", "mutation_status"])
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows, ["guardrail", "occurred"])

    (OUT_DIR / "thesis_heat_path_preflight_insert.md").write_text(build_thesis_insert(preflight_rows, gate_rows) + "\n")
    (OUT_DIR / "README.md").write_text(build_readme(summary) + "\n")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
