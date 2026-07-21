#!/usr/bin/env python3
"""Build the AGENT-452 thermal parity resolution gate package.

The gate resolves the broad thermal CFD-to-1D parity blocker only when current
evidence proves predictive thermal work can continue without fitting internal
Nu to boundary, source, storage, radiation, or recirculation residuals.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-452"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate")
OUT = ROOT / OUT_REL

RESIDUAL_GUARDRAILS = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails"
    / "thermal_residual_ownership_guardrails.csv"
)
THERMAL_REVIEW = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation"
    / "thermal_internal_nu_admission_review.csv"
)
HX_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock"
    / "hx_candidate_gate_decision.csv"
)
HX_RUNTIME_AUDIT = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock"
    / "hx_runtime_input_legality_audit.csv"
)
INTERNAL_NU_FIT_ROWS = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger"
    / "internal_nu_fit_rows.csv"
)
LITREV_LESSONS = (
    ROOT / "reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md"
)
LITREV_MAP = ROOT / "operational_notes/maps/literature-synthesis-and-gates.md"
BOUNDARY_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision"
    / "README.md"
)
BLOCKER_WAVE = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation"
    / "README.md"
)

PREFERRED_HX = "salt2_fit_constant_UA_bulk_drive"
REQUIRED_RESIDUALS = {
    "heater_realized_fraction",
    "cooler_hx_removal",
    "wall_layer_external_convection",
    "radiation_metadata",
    "wall_storage_transient",
    "branch_mixing_recirculation",
    "internal_convection_development",
}

RESIDUAL_COLUMNS = [
    "residual_id",
    "residual_owner_present",
    "internal_nu_guardrail_present",
    "excluded_internal_nu_use_present",
    "runtime_setup_inputs_present",
    "source_evidence_present",
    "resolution_gate",
    "reason",
    "residual_owner",
    "boundary_model_form_or_ledger",
    "primary_runtime_setup_inputs",
    "excluded_internal_nu_use",
    "source_evidence",
]

THERMAL_COLUMNS = [
    "case_id",
    "segment",
    "qoi",
    "review_admission_class",
    "internal_nu_fit_allowed",
    "residual_owner_gate",
    "parity_resolution_use",
    "blockers",
    "guardrail",
    "next_action",
    "source_paths",
]

LITREV_COLUMNS = [
    "method_rule",
    "litrev_gate",
    "implementation_in_resolution_gate",
    "allowed_use_after_resolution",
    "excluded_use",
    "source_path",
]

CONTINUATION_COLUMNS = [
    "continuation_item",
    "status",
    "gate",
    "evidence",
    "runtime_forbidden_inputs",
    "source_path",
]

BLOCKER_COLUMNS = [
    "blocker_id",
    "decision",
    "can_update_blocker_register",
    "resolved_by",
    "resolved_on",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
    "remaining_open_blockers",
]

MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: row.get(column, "") for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1"}


def gate(value: bool) -> str:
    return "pass" if value else "fail"


def evaluate_residual_owners(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = {row.get("residual_id", "") for row in rows}
    for row in rows:
        residual_id = row.get("residual_id", "")
        owner_present = bool(row.get("residual_owner", "").strip())
        guardrail_text = " ".join(
            [
                row.get("internal_nu_guardrail", ""),
                row.get("excluded_internal_nu_use", ""),
            ]
        ).lower()
        guardrail_present = "nu" in guardrail_text and (
            "do not" in guardrail_text
            or "closed" in guardrail_text
            or "0 fit-admissible" in guardrail_text
            or "keep rows out" in guardrail_text
        )
        excluded_present = bool(row.get("excluded_internal_nu_use", "").strip())
        runtime_inputs_present = bool(row.get("primary_runtime_setup_inputs", "").strip())
        source_present = bool(row.get("source_evidence", "").strip())
        required_present = residual_id in REQUIRED_RESIDUALS
        passed = all(
            [
                required_present,
                owner_present,
                guardrail_present,
                excluded_present,
                runtime_inputs_present,
                source_present,
            ]
        )
        reasons = []
        if not required_present:
            reasons.append("not_in_required_residual_set")
        if not owner_present:
            reasons.append("missing_owner")
        if not guardrail_present:
            reasons.append("missing_no_internal_nu_guardrail")
        if not excluded_present:
            reasons.append("missing_excluded_internal_nu_use")
        if not runtime_inputs_present:
            reasons.append("missing_runtime_setup_inputs")
        if not source_present:
            reasons.append("missing_source_evidence")
        out.append(
            {
                "residual_id": residual_id,
                "residual_owner_present": gate(owner_present),
                "internal_nu_guardrail_present": gate(guardrail_present),
                "excluded_internal_nu_use_present": gate(excluded_present),
                "runtime_setup_inputs_present": gate(runtime_inputs_present),
                "source_evidence_present": gate(source_present),
                "resolution_gate": gate(passed),
                "reason": "all_required_fields_present" if passed else ";".join(reasons),
                "residual_owner": row.get("residual_owner", ""),
                "boundary_model_form_or_ledger": row.get("boundary_model_form_or_ledger", ""),
                "primary_runtime_setup_inputs": row.get("primary_runtime_setup_inputs", ""),
                "excluded_internal_nu_use": row.get("excluded_internal_nu_use", ""),
                "source_evidence": row.get("source_evidence", ""),
            }
        )
    for missing in sorted(REQUIRED_RESIDUALS - seen):
        out.append(
            {
                "residual_id": missing,
                "residual_owner_present": "fail",
                "internal_nu_guardrail_present": "fail",
                "excluded_internal_nu_use_present": "fail",
                "runtime_setup_inputs_present": "fail",
                "source_evidence_present": "fail",
                "resolution_gate": "fail",
                "reason": "missing_required_residual_row",
            }
        )
    return out


def evaluate_thermal_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    allowed_classes = {"validation_only", "diagnostic_only", "blocked", "fit_admissible"}
    for row in rows:
        admission_class = row.get("review_admission_class", "")
        internal_nu_allowed = truthy(row.get("internal_nu_fit_allowed", ""))
        guardrail = row.get("guardrail", "")
        owner_gate = (
            admission_class in allowed_classes
            and (not internal_nu_allowed)
            and "do_not_fit_boundary_or_storage_residual_into_internal_Nu" in guardrail
        )
        out.append(
            {
                "case_id": row.get("case_id", ""),
                "segment": row.get("segment", ""),
                "qoi": row.get("qoi", ""),
                "review_admission_class": admission_class,
                "internal_nu_fit_allowed": row.get("internal_nu_fit_allowed", ""),
                "residual_owner_gate": gate(owner_gate),
                "parity_resolution_use": (
                    "supports_resolution_no_internal_nu_absorption"
                    if owner_gate
                    else "does_not_support_resolution"
                ),
                "blockers": row.get("blockers", ""),
                "guardrail": guardrail,
                "next_action": row.get("next_action", ""),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return out


def litrev_crosswalk_rows() -> list[dict[str, str]]:
    return [
        {
            "method_rule": "Branchwise closure ledger",
            "litrev_gate": "architecture",
            "implementation_in_resolution_gate": "Every residual is assigned to a physical owner before any coefficient fitting.",
            "allowed_use_after_resolution": "Continue predictive thermal work with branch/section residual owners.",
            "excluded_use": "Do not report one global Nu, UA, or friction cleanup multiplier.",
            "source_path": rel(LITREV_LESSONS),
        },
        {
            "method_rule": "Heat-loss network separation",
            "litrev_gate": "heat-loss-calibration",
            "implementation_in_resolution_gate": "Cooler/HX, passive wall loss, radiation metadata, heater/source, storage, and residual are separate lanes.",
            "allowed_use_after_resolution": "Use setup-only HX/cooler candidate as a final-scorecard input.",
            "excluded_use": "Do not hide active cooler or passive loss error in internal Nu.",
            "source_path": rel(LITREV_MAP),
        },
        {
            "method_rule": "Invalid-single-stream diagnostics",
            "litrev_gate": "CFD-validity-diagnostics",
            "implementation_in_resolution_gate": "Recirculating rows remain section-effective or diagnostic; true Nu/f_D/K labels stay closed.",
            "allowed_use_after_resolution": "Proceed with upcomer recirculation/onset lane separately.",
            "excluded_use": "Do not fit recirculating upcomer rows as transferable single-stream Nu.",
            "source_path": rel(LITREV_MAP),
        },
        {
            "method_rule": "Property and source-envelope discipline",
            "litrev_gate": "source-envelope + property-sensitivity",
            "implementation_in_resolution_gate": "Resolution does not promote new Nu correlations; default/literature Nu remains reference until source and property gates pass.",
            "allowed_use_after_resolution": "Carry Nu as baseline/reference while residual owners advance.",
            "excluded_use": "Do not activate Chen or other source-bounded Nu without overlap and property-lane gates.",
            "source_path": rel(LITREV_LESSONS),
        },
        {
            "method_rule": "Radiation double-count guardrail",
            "litrev_gate": "boundary/HX/wall/radiation decision",
            "implementation_in_resolution_gate": "CFD rcExternalTemperature wallHeatFlux replay is treated as total embedded radiation metadata.",
            "allowed_use_after_resolution": "Use explicit radiation only in predictive boundary mode, not realized wallHeatFlux replay.",
            "excluded_use": "Do not add separate qr on top of realized wallHeatFlux or fit it into Nu.",
            "source_path": rel(BOUNDARY_DECISION),
        },
    ]


def evaluate_continuation(
    hx_rows: list[dict[str, str]], runtime_rows: list[dict[str, str]], fit_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    preferred = next((row for row in hx_rows if row.get("candidate_id") == PREFERRED_HX), {})
    hx_pass = (
        preferred.get("validation_gate") == "pass"
        and preferred.get("holdout_gate") == "pass"
        and preferred.get("runtime_gate") == "pass"
        and preferred.get("runtime_input_violation_count") in {"0", 0}
    )
    runtime_failures = [row for row in runtime_rows if not row.get("gate", "").startswith("pass")]
    fit_row = next((row for row in fit_rows if row.get("fit_row_id") == "internal_nu_fit_admitted_rows"), {})
    admitted_count = fit_row.get("admitted_row_count", "0")
    return [
        {
            "continuation_item": "setup_only_hx_cooler",
            "status": "admitted_candidate_input" if hx_pass else "blocked",
            "gate": gate(hx_pass),
            "evidence": (
                f"{PREFERRED_HX}: validation {preferred.get('validation_abs_error_W', '')} W, "
                f"holdout {preferred.get('holdout_abs_error_W', '')} W, runtime violations "
                f"{preferred.get('runtime_input_violation_count', '')}"
            ),
            "runtime_forbidden_inputs": "imposed CFD cooler duty; realized wallHeatFlux; CFD mdot; validation temperature",
            "source_path": rel(HX_DECISION),
        },
        {
            "continuation_item": "runtime_input_legality",
            "status": "legal" if not runtime_failures else "blocked",
            "gate": gate(not runtime_failures),
            "evidence": f"{len(runtime_rows)} runtime audit rows; {len(runtime_failures)} failures",
            "runtime_forbidden_inputs": "; ".join(row.get("forbidden_runtime_inputs", "") for row in runtime_rows),
            "source_path": rel(HX_RUNTIME_AUDIT),
        },
        {
            "continuation_item": "internal_nu_fit_rows",
            "status": "closed_to_fit_reference_only" if admitted_count == "0" else "fit_rows_present_review_required",
            "gate": "pass" if admitted_count == "0" else "fail",
            "evidence": f"admitted internal Nu fit rows = {admitted_count}",
            "runtime_forbidden_inputs": "boundary/source/storage/radiation/recirculation residuals may not be absorbed by Nu",
            "source_path": rel(INTERNAL_NU_FIT_ROWS),
        },
    ]


def blocker_decision_rows(
    residual_rows: list[dict[str, Any]],
    thermal_rows: list[dict[str, Any]],
    continuation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failed = []
    if any(row["resolution_gate"] != "pass" for row in residual_rows):
        failed.append("residual_ownership")
    if any(row["residual_owner_gate"] != "pass" for row in thermal_rows):
        failed.append("thermal_row_guardrails")
    if any(row["gate"] != "pass" for row in continuation_rows):
        failed.append("predictive_continuation")
    passed = not failed
    criteria = [
        "residual ownership separated",
        "internal Nu not fit to boundary/source/storage residuals",
        "setup-only HX/cooler continuation input legal",
        "LitRev branchwise heat-loss methodology applied",
    ]
    return [
        {
            "blocker_id": "thermal-cfd-1d-parity",
            "decision": "resolved" if passed else "not_resolved",
            "can_update_blocker_register": "yes" if passed else "no",
            "resolved_by": rel(OUT),
            "resolved_on": DATE if passed else "",
            "criteria_passed": "; ".join(criteria if passed else [item for item in criteria if item not in failed]),
            "criteria_failed": "" if passed else "; ".join(failed),
            "scientific_interpretation": (
                "Resolved as a blocker to predictive thermal continuation: parity residuals have physical owners and internal Nu remains reference-only, not tuned."
                if passed
                else "Broad parity blocker remains open because at least one required residual-ownership or continuation gate failed."
            ),
            "remaining_open_blockers": (
                "closure-qoi-mesh-gci; predictive-heater-cooler-wall-submodels; upcomer-onset-data-sparsity; f6-friction-re-correction"
            ),
        }
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    sources = [
        ("residual_guardrails", RESIDUAL_GUARDRAILS, "residual owner and no-Nu-absorption contract"),
        ("thermal_review", THERMAL_REVIEW, "current thermal/Internal-Nu admission review"),
        ("hx_decision", HX_DECISION, "setup-only HX/cooler candidate decision"),
        ("hx_runtime_audit", HX_RUNTIME_AUDIT, "runtime input legality audit"),
        ("internal_nu_fit_rows", INTERNAL_NU_FIT_ROWS, "explicit zero admitted internal-Nu fit rows"),
        ("litrev_lessons", LITREV_LESSONS, "LitRev methodology and model-form guardrails"),
        ("litrev_map", LITREV_MAP, "LitRev gate discipline map"),
        ("boundary_decision", BOUNDARY_DECISION, "boundary/HX/wall/radiation model-form decision"),
        ("blocker_wave", BLOCKER_WAVE, "prior blocker state"),
    ]
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": path.exists(),
            "role": role,
        }
        for source_id, path, role in sources
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    decision = summary["blocker_decision"]
    text = f"""---
provenance:
  - {rel(RESIDUAL_GUARDRAILS)}
  - {rel(THERMAL_REVIEW)}
  - {rel(HX_DECISION)}
  - {rel(LITREV_LESSONS)}
tags: [thermal-parity, blocker-resolution, internal-nu, forward-v1, litrev-synthesis]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/forward-predictive-model.md
task: {TASK}
date: {DATE}
role: Coordinator/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Thermal Parity Resolution Gate

## Decision

`thermal-cfd-1d-parity`: `{decision}`.

This resolves the blocker only in the scientifically narrow sense that
predictive thermal work can continue without tuning internal Nu to absorb
boundary, source, storage, radiation, or recirculation residuals. It does **not**
admit internal-Nu fitting.

## Gate Results

- Residual owner rows: `{summary["residual_owner_rows"]}`.
- Residual owner gate failures: `{summary["residual_owner_failures"]}`.
- Thermal/Internal-Nu rows reviewed: `{summary["thermal_rows_reviewed"]}`.
- Internal-Nu fit-admissible rows after this gate: `{summary["internal_nu_fit_allowed_rows"]}`.
- Setup-only HX/cooler continuation gate: `{summary["setup_only_hx_gate"]}`.
- Runtime input legality gate: `{summary["runtime_legality_gate"]}`.

## Interpretation

The LitRev theory is used as methodology: branchwise ledgers, heat-loss network
separation, property/source-envelope discipline, reset/development awareness,
and invalid-single-stream diagnostics. Current internal Nu remains
reference/baseline or diagnostic-only until a later gate admits true rows.

## Files

- `residual_owner_resolution_gate.csv`
- `thermal_row_admission_gate.csv`
- `litrev_methodology_crosswalk.csv`
- `predictive_thermal_continuation_decision.csv`
- `blocker_resolution_decision.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD solver outputs, registry/admission state, scheduler state, or
external `../cfd-modeling-tools/**` files were mutated.
"""
    out.joinpath("README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    residual_gate_rows = evaluate_residual_owners(read_csv(RESIDUAL_GUARDRAILS))
    thermal_gate_rows = evaluate_thermal_rows(read_csv(THERMAL_REVIEW))
    litrev_rows = litrev_crosswalk_rows()
    continuation_rows = evaluate_continuation(read_csv(HX_DECISION), read_csv(HX_RUNTIME_AUDIT), read_csv(INTERNAL_NU_FIT_ROWS))
    blocker_rows = blocker_decision_rows(residual_gate_rows, thermal_gate_rows, continuation_rows)
    manifest = source_manifest_rows()

    write_csv(out / "residual_owner_resolution_gate.csv", residual_gate_rows, RESIDUAL_COLUMNS)
    write_csv(out / "thermal_row_admission_gate.csv", thermal_gate_rows, THERMAL_COLUMNS)
    write_csv(out / "litrev_methodology_crosswalk.csv", litrev_rows, LITREV_COLUMNS)
    write_csv(out / "predictive_thermal_continuation_decision.csv", continuation_rows, CONTINUATION_COLUMNS)
    write_csv(out / "blocker_resolution_decision.csv", blocker_rows, BLOCKER_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    class_counts = Counter(row["review_admission_class"] for row in thermal_gate_rows)
    internal_nu_fit_allowed = sum(1 for row in thermal_gate_rows if truthy(str(row.get("internal_nu_fit_allowed", ""))))
    setup_only_gate = next(row for row in continuation_rows if row["continuation_item"] == "setup_only_hx_cooler")["gate"]
    runtime_gate = next(row for row in continuation_rows if row["continuation_item"] == "runtime_input_legality")["gate"]
    decision = blocker_rows[0]["decision"]
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "blocker_decision": decision,
        "can_update_blocker_register": blocker_rows[0]["can_update_blocker_register"] == "yes",
        "residual_owner_rows": len(residual_gate_rows),
        "residual_owner_failures": sum(1 for row in residual_gate_rows if row["resolution_gate"] != "pass"),
        "thermal_rows_reviewed": len(thermal_gate_rows),
        "thermal_review_class_counts": dict(class_counts),
        "internal_nu_fit_allowed_rows": internal_nu_fit_allowed,
        "setup_only_hx_gate": setup_only_gate,
        "runtime_legality_gate": runtime_gate,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_modified": False,
        "outputs": [
            rel(out / "README.md"),
            rel(out / "residual_owner_resolution_gate.csv"),
            rel(out / "thermal_row_admission_gate.csv"),
            rel(out / "litrev_methodology_crosswalk.csv"),
            rel(out / "predictive_thermal_continuation_decision.csv"),
            rel(out / "blocker_resolution_decision.csv"),
            rel(out / "source_manifest.csv"),
            rel(out / "summary.json"),
        ],
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args(argv)
    summary = build_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
