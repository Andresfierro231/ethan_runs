#!/usr/bin/env python3
"""Build AGENT-459 branch-local Internal-Nu unblock package.

This package is the implementation pass after AGENT-455. It does not try to
make new CFD measurements. It restricts the current closure-QOI/GCI ledger to
rows that could actually enter final non-upcomer fits, checks the branch-local
Internal-Nu gates, and emits a precise unblock queue.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-459"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock")
OUT = ROOT / OUT_REL

AGENT455 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution"
CANDIDATES = AGENT455 / "leg_specific_internal_nu_candidate_rows.csv"
MESH_GCI = AGENT455 / "mesh_gci_gate_for_admitted_candidates.csv"
MODEL_FORMS = AGENT455 / "leg_specific_nu_model_form_matrix.csv"
GEOMETRY = AGENT455 / "geometry_taxonomy_correction.csv"
BLOCKER_DECISION_455 = AGENT455 / "blocker_unblock_decision.csv"
THERMAL_PARITY = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/README.md"
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-closures-and-internal-nu.md"
MESH_MAP = ROOT / "operational_notes/maps/mesh-gci-and-uncertainty.md"

SOURCE_PATHS = {
    "agent455_candidates": CANDIDATES,
    "agent455_mesh_gci": MESH_GCI,
    "agent455_model_forms": MODEL_FORMS,
    "agent455_geometry": GEOMETRY,
    "agent455_blocker_decision": BLOCKER_DECISION_455,
    "thermal_parity": THERMAL_PARITY,
    "thermal_map": THERMAL_MAP,
    "mesh_map": MESH_MAP,
}

BRANCH_COLUMNS = [
    "canonical_leg_id",
    "leg_role",
    "candidate_rows",
    "nu_candidate_rows",
    "residual_owner_pass_rows",
    "sign_heat_balance_pass_rows",
    "recirculation_pass_rows",
    "mesh_gci_pass_rows",
    "fit_admissible_internal_nu_rows",
    "branch_local_decision",
    "primary_blockers",
    "next_action",
    "source_path",
]
FINAL_USE_COLUMNS = [
    "qoi_id",
    "canonical_leg_id",
    "reported_span_or_segment",
    "qoi_family",
    "quantity",
    "intended_final_fit_lane",
    "current_publication_ready",
    "current_fit_admissible",
    "complete_triplet",
    "gci_status",
    "final_use_decision",
    "resolution_action",
    "source_paths",
]
FIT_COLUMNS = [
    "candidate_id",
    "canonical_leg_id",
    "case_id",
    "reported_segment_or_span",
    "qoi",
    "fit_admissible",
    "gate_vector",
    "failure_reasons",
    "source_path",
]
QUEUE_COLUMNS = [
    "queue_id",
    "canonical_leg_id",
    "gate_family",
    "blocked_rows",
    "current_status",
    "required_next_artifact",
    "acceptance_signal",
    "source_path",
]
DECISION_COLUMNS = [
    "blocker_id",
    "decision",
    "can_update_blocker_register",
    "resolved_by",
    "resolved_on",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
    "next_unlock_sequence",
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
            writer.writerow({column: format_value(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass"}


def is_upcomer(row: dict[str, str]) -> bool:
    return row.get("canonical_leg_id") == "upcomer_left_vertical" or yes(row.get("upcomer_member", ""))


def internal_nu_qoi(row: dict[str, str]) -> bool:
    qoi = row.get("qoi", "").strip()
    return qoi == "Nu"


def gate_vector(row: dict[str, str]) -> dict[str, bool]:
    return {
        "qoi": internal_nu_qoi(row),
        "non_upcomer": not is_upcomer(row),
        "source_allows_fit": yes(row.get("internal_nu_fit_allowed_now", "")),
        "residual_owner": row.get("residual_owner_gate") == "pass",
        "sign_heat_balance": row.get("sign_heat_balance_gate") == "pass",
        "recirculation": row.get("recirculation_gate") == "pass",
        "mesh_gci": row.get("mesh_gci_gate") == "pass",
    }


def fit_admissible(row: dict[str, str]) -> bool:
    vector = gate_vector(row)
    return all(vector.values())


def failure_reasons(row: dict[str, str]) -> str:
    vector = gate_vector(row)
    missing = [key for key, value in vector.items() if not value]
    row_reason = row.get("reason", "")
    return ";".join(missing + ([row_reason] if row_reason else []))


def final_use_rows(mesh_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in mesh_rows:
        leg = row.get("canonical_leg_id", "")
        if leg == "upcomer_left_vertical":
            continue
        decision = row.get("final_use_decision", "")
        intended = decision in {
            "admitted_final_use",
            "blocked_pending_downcomer_policy",
            "blocked_pending_same_qoi_triplet_reconciliation",
            "blocked_pending_sign_heat_balance_source_admission",
            "not_publication_gci_current_triplet_exclude_or_reextract",
        }
        out.append(
            {
                "qoi_id": row.get("qoi_id", ""),
                "canonical_leg_id": leg,
                "reported_span_or_segment": row.get("reported_span_or_segment", ""),
                "qoi_family": row.get("qoi_family", ""),
                "quantity": row.get("quantity", ""),
                "intended_final_fit_lane": intended,
                "current_publication_ready": row.get("current_publication_ready", ""),
                "current_fit_admissible": row.get("current_fit_admissible", ""),
                "complete_triplet": row.get("complete_triplet", ""),
                "gci_status": row.get("gci_status", ""),
                "final_use_decision": decision,
                "resolution_action": row.get("resolution_action", ""),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return out


def fit_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in candidate_rows:
        if not internal_nu_qoi(row):
            continue
        vector = gate_vector(row)
        out.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "canonical_leg_id": row.get("canonical_leg_id", ""),
                "case_id": row.get("case_id", ""),
                "reported_segment_or_span": row.get("reported_segment_or_span", ""),
                "qoi": row.get("qoi", ""),
                "fit_admissible": fit_admissible(row),
                "gate_vector": ";".join(f"{key}={format_value(value)}" for key, value in vector.items()),
                "failure_reasons": "" if all(vector.values()) else failure_reasons(row),
                "source_path": row.get("source_path", ""),
            }
        )
    return out


def branch_decision(
    leg: str,
    model: dict[str, str],
    candidates: list[dict[str, str]],
    final_rows: list[dict[str, Any]],
    fit_count: int,
) -> tuple[str, str, str]:
    reasons = " ".join(row.get("reason", "") for row in candidates)
    mesh_decisions = {row.get("final_use_decision", "") for row in final_rows}
    if fit_count > 0:
        return ("fit_admissible_rows_present", "none", "fit only the rows admitted in internal_nu_fit_admissible_rows.csv")
    if leg == "upcomer_left_vertical":
        return (
            "hybrid_onset_diagnostic_not_single_stream",
            "upcomer/test-section recirculation lane",
            "classify onset as observed/bracketed/extrapolated or build explicit hybrid model; do not fit single-stream Nu",
        )
    if leg == "heater_lower_leg":
        return (
            "blocked_source_sign_heat_balance_mesh",
            "source ownership, sign/heat-balance, and mesh/GCI still block fit",
            "publish branch-local heater source/enthalpy/sign admission, then same-QOI Nu or HTC/UA mesh-GCI",
        )
    if leg == "downcomer_right_vertical":
        return (
            "blocked_downcomer_policy_and_mesh",
            "downcomer policy; sign/heat-balance; no admitted same-QOI GCI",
            "write downcomer thermal policy and admit low-recirculation branch-local thermal rows before GCI",
        )
    if leg == "cooler_hx_branch":
        return (
            "boundary_hx_lane_not_internal_nu_fit",
            "HX/boundary residual not separable as internal Nu",
            "keep setup-only UA/effectiveness model; fit cooler internal Nu only after HX removal and shell/boundary residual separation",
        )
    if "not_publication_gci_current_triplet_exclude_or_reextract" in mesh_decisions:
        return (
            "blocked_current_triplet_not_publication_gci",
            "current same-QOI triplet is non-publication GCI",
            "exclude from final closure set or rerun same-plane/same-window extraction on a better mesh/source contract",
        )
    if "waiting_on_branch_rows" in reasons or model.get("current_evidence_status") == "waiting_on_branch_rows":
        return (
            "waiting_on_branch_local_rows",
            "no branch-local admitted rows",
            "extract/admit branch-local low-recirculation rows with residual-owner and heat-balance gates",
        )
    return ("not_fit_target_or_manual_review", "no current admitted fit path", "manual review if this leg is intended for a future fit")


def branch_rows(
    models: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    final_rows: list[dict[str, Any]],
    fit_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_leg: dict[str, list[dict[str, str]]] = defaultdict(list)
    final_by_leg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fit_by_leg: Counter[str] = Counter()
    for row in candidate_rows:
        candidates_by_leg[row.get("canonical_leg_id", "")].append(row)
    for row in final_rows:
        final_by_leg[str(row.get("canonical_leg_id", ""))].append(row)
    for row in fit_table:
        if yes(row.get("fit_admissible", "")):
            fit_by_leg[str(row.get("canonical_leg_id", ""))] += 1
    rows: list[dict[str, Any]] = []
    for model in models:
        leg = model.get("canonical_leg_id", "")
        leg_candidates = candidates_by_leg.get(leg, [])
        leg_final = final_by_leg.get(leg, [])
        fit_count = fit_by_leg[leg]
        decision, blockers, action = branch_decision(leg, model, leg_candidates, leg_final, fit_count)
        rows.append(
            {
                "canonical_leg_id": leg,
                "leg_role": model.get("leg_role", ""),
                "candidate_rows": len(leg_candidates),
                "nu_candidate_rows": sum(1 for row in leg_candidates if internal_nu_qoi(row)),
                "residual_owner_pass_rows": sum(1 for row in leg_candidates if row.get("residual_owner_gate") == "pass"),
                "sign_heat_balance_pass_rows": sum(1 for row in leg_candidates if row.get("sign_heat_balance_gate") == "pass"),
                "recirculation_pass_rows": sum(1 for row in leg_candidates if row.get("recirculation_gate") == "pass"),
                "mesh_gci_pass_rows": sum(1 for row in leg_candidates if row.get("mesh_gci_gate") == "pass"),
                "fit_admissible_internal_nu_rows": fit_count,
                "branch_local_decision": decision,
                "primary_blockers": blockers,
                "next_action": action,
                "source_path": rel(MODEL_FORMS),
            }
        )
    return rows


def queue_rows(branch_table: list[dict[str, Any]], final_rows_table: list[dict[str, Any]], fit_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    branch_by_leg = {row["canonical_leg_id"]: row for row in branch_table}
    unresolved_final = [row for row in final_rows_table if row["final_use_decision"] != "admitted_final_use"]
    for leg in ["heater_lower_leg", "downcomer_right_vertical", "cooler_hx_branch", "upcomer_left_vertical"]:
        branch = branch_by_leg.get(leg, {})
        blocked_rows = sum(1 for row in fit_table if row.get("canonical_leg_id") == leg and not yes(row.get("fit_admissible")))
        if leg == "heater_lower_leg":
            gate = "source_sign_heat_balance_and_mesh_gci"
            artifact = "heater branch-local source/enthalpy/sign admission table plus same-QOI Nu or HTC/UA GCI triplet"
            signal = ">=1 heater Nu-equivalent row with residual_owner/sign/recirculation/mesh gates passing"
        elif leg == "downcomer_right_vertical":
            gate = "downcomer_policy_low_recirculation_and_mesh_gci"
            artifact = "downcomer thermal policy memo plus admitted low-recirculation branch-local thermal rows"
            signal = "downcomer policy pass and >=1 same-QOI publication-ready GCI row"
        elif leg == "cooler_hx_branch":
            gate = "hx_boundary_residual_separation"
            artifact = "cooler/HX shell-boundary residual separation package"
            signal = "HX removal separated from internal convection without realized wallHeatFlux or imposed cooler duty"
        else:
            gate = "upcomer_hybrid_onset"
            artifact = "upcomer onset classification or explicit hybrid recirculation model"
            signal = "onset observed/bracketed/extrapolated decision without single-stream coefficient promotion"
        queue.append(
            {
                "queue_id": f"{leg}:{gate}",
                "canonical_leg_id": leg,
                "gate_family": gate,
                "blocked_rows": blocked_rows,
                "current_status": branch.get("branch_local_decision", ""),
                "required_next_artifact": artifact,
                "acceptance_signal": signal,
                "source_path": rel(OUT / "branch_local_thermal_admission.csv"),
            }
        )
    queue.append(
        {
            "queue_id": "global:final_use_same_qoi_mesh_gci",
            "canonical_leg_id": "global_non_upcomer",
            "gate_family": "same_qoi_mesh_gci",
            "blocked_rows": len(unresolved_final),
            "current_status": "0_current_publication_ready_final_use_gci_rows",
            "required_next_artifact": "same-QOI mesh/GCI rerun or exclusion decision only for admitted final-use rows",
            "acceptance_signal": "all final-use rows are either publication-ready or explicitly excluded before blocker closeout",
            "source_path": rel(OUT / "final_use_closure_qoi_gci.csv"),
        }
    )
    return queue


def blocker_decision(
    branch_table: list[dict[str, Any]],
    final_rows_table: list[dict[str, Any]],
    fit_table: list[dict[str, Any]],
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fit_count = sum(1 for row in fit_table if yes(row.get("fit_admissible", "")))
    publication_ready = sum(
        1
        for row in final_rows_table
        if yes(row.get("current_publication_ready", "")) and yes(row.get("current_fit_admissible", ""))
    )
    unresolved_final = sum(1 for row in final_rows_table if row.get("final_use_decision") != "admitted_final_use")
    resolved = fit_count > 0 and publication_ready > 0 and unresolved_final == 0
    passed = [
        "test_section_span_kept_in_upcomer_lane",
        "final_use_gci_restricted_to_non_upcomer_fit_lanes",
        "branch_local_queue_generated",
        "residual_owner_guardrail_preserved",
    ]
    failed = []
    if fit_count == 0:
        failed.append("0_fit_admissible_internal_Nu_rows")
    if publication_ready == 0:
        failed.append("0_publication_ready_final_use_GCI_rows")
    if unresolved_final:
        failed.append(f"{unresolved_final}_unresolved_final_use_GCI_rows")
    if queue and not resolved:
        failed.append(f"{len(queue)}_targeted_unblock_queue_rows")
    return [
        {
            "blocker_id": "closure-qoi-mesh-gci",
            "decision": "resolved" if resolved else "not_resolved",
            "can_update_blocker_register": "yes",
            "resolved_by": rel(OUT) if resolved else "",
            "resolved_on": DATE if resolved else "",
            "criteria_passed": ";".join(passed),
            "criteria_failed": ";".join(failed),
            "scientific_interpretation": (
                "Branch-local Internal-Nu fitting is admissible on current evidence."
                if resolved
                else "Branch-local gates are now decision-complete, but current evidence still has no fit-admissible Internal-Nu rows and no publication-ready final-use GCI rows."
            ),
            "next_unlock_sequence": " -> ".join(row["queue_id"] for row in queue),
        }
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "agent455_candidates": "row-level leg-specific Internal-Nu candidate gate",
        "agent455_mesh_gci": "Closure-QOI/GCI final-use candidate decisions",
        "agent455_model_forms": "distinct leg model-form lanes",
        "agent455_geometry": "test-section/upcomer taxonomy",
        "agent455_blocker_decision": "previous blocker decision input",
        "thermal_parity": "residual-owner and no-Nu-absorption guardrail",
        "thermal_map": "thermal/Internal-Nu topic hub",
        "mesh_map": "mesh/GCI topic hub",
    }
    return [
        {"source_id": key, "path": rel(path), "exists": path.exists(), "role": roles[key]}
        for key, path in SOURCE_PATHS.items()
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CANDIDATES)}
  - {rel(MESH_GCI)}
  - {rel(MODEL_FORMS)}
  - {rel(BLOCKER_DECISION_455)}
tags: [internal-nu, closure-qoi, mesh-gci, branch-local-admission, blocker-narrowing]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: {TASK}
date: {DATE}
role: Coordinator/cfd-pp/Mesh-GCI/Internal-Nu/Implementer/Tester/Writer
type: work_product
status: complete
---
# Branch-Local Internal-Nu Unblock

Generated: `{summary["generated_at"]}`

## Decision

`closure-qoi-mesh-gci`: `{summary["blocker_decision"]}`.

This package implements the branch-local unblock plan after AGENT-455. It
restricts final-use GCI review to non-upcomer fit lanes, keeps the test section
inside the upcomer hybrid/onset lane, and evaluates whether any current row can
fit a leg-specific Internal-Nu correlation.

## Results

- Branches reviewed: `{summary["branch_count"]}`.
- Final-use non-upcomer GCI rows reviewed: `{summary["final_use_gci_rows"]}`.
- Publication-ready final-use GCI rows: `{summary["publication_ready_final_use_gci_rows"]}`.
- Internal-Nu candidate rows reviewed: `{summary["internal_nu_candidate_rows"]}`.
- Fit-admissible Internal-Nu rows: `{summary["fit_admissible_internal_nu_rows"]}`.
- Targeted unblock queue rows: `{summary["targeted_queue_rows"]}`.

## Interpretation

The current blocker cannot be closed today. The taxonomy and branch lanes are
decision-complete, but the evidence still lacks both an admitted Internal-Nu fit
row and a publication-ready final-use Closure-QOI/GCI row. The next work is
branch-local admission, not global Nu tuning.

## Outputs

- `branch_local_thermal_admission.csv`
- `final_use_closure_qoi_gci.csv`
- `internal_nu_fit_admissible_rows.csv`
- `targeted_extraction_admission_queue.csv`
- `blocker_resolution_decision.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    candidates = read_csv(CANDIDATES)
    mesh = read_csv(MESH_GCI)
    models = read_csv(MODEL_FORMS)

    final_table = final_use_rows(mesh)
    fit_table = fit_rows(candidates)
    branch_table = branch_rows(models, candidates, final_table, fit_table)
    queue = queue_rows(branch_table, final_table, fit_table)
    decisions = blocker_decision(branch_table, final_table, fit_table, queue)
    manifest = source_manifest_rows()

    write_csv(out / "branch_local_thermal_admission.csv", branch_table, BRANCH_COLUMNS)
    write_csv(out / "final_use_closure_qoi_gci.csv", final_table, FINAL_USE_COLUMNS)
    write_csv(out / "internal_nu_fit_admissible_rows.csv", fit_table, FIT_COLUMNS)
    write_csv(out / "targeted_extraction_admission_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out / "blocker_resolution_decision.csv", decisions, DECISION_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    fit_count = sum(1 for row in fit_table if yes(row.get("fit_admissible", "")))
    publication_ready = sum(
        1
        for row in final_table
        if yes(row.get("current_publication_ready", "")) and yes(row.get("current_fit_admissible", ""))
    )
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "blocker_decision": decisions[0]["decision"],
        "branch_count": len(branch_table),
        "branch_decision_counts": dict(Counter(row["branch_local_decision"] for row in branch_table)),
        "final_use_gci_rows": len(final_table),
        "publication_ready_final_use_gci_rows": publication_ready,
        "internal_nu_candidate_rows": len(fit_table),
        "fit_admissible_internal_nu_rows": fit_count,
        "targeted_queue_rows": len(queue),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
