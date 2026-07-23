#!/usr/bin/env python3
"""Build a candidate-specific source/property gate packet.

This consolidates already-published train/support evidence for a few physical
candidate lanes. It deliberately stays fail-closed: no protected scoring,
source/property release, Qwall release, coefficient admission, or freeze.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-CANDIDATE-SPECIFIC-SOURCE-PROPERTY-GATE-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"

PACKAGES = {
    "passive_h2": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate",
    "passive_h2_runtime": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation",
    "p1d": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_p1d_bulk_cv_h2_train_only_thesis_prototype",
    "cooler": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_cooler_removal_model",
    "source_nominal": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight",
    "source_unblock": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_source_property_release_unblock_study",
    "source_exact": ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14",
}

GUARDRAILS = {
    "native_solver_outputs_mutated": False,
    "registry_or_admission_mutated": False,
    "scheduler_action": False,
    "solver_postprocessing_sampler_harvest_uq_launched": False,
    "fluid_or_external_edit": False,
    "thesis_current_or_latex_edit": False,
    "validation_holdout_external_scoring": False,
    "protected_scoring": False,
    "fitting_or_model_selection": False,
    "source_property_broad_release": False,
    "Qwall_release": False,
    "numeric_q_loss_release": False,
    "coefficient_admission": False,
    "candidate_freeze": False,
    "final_score_claim": False,
    "hidden_multiplier": False,
    "residual_absorbed_into_internal_Nu": False,
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
        PACKAGES["passive_h2"] / "summary.json",
        PACKAGES["passive_h2"] / "decision_gate.csv",
        PACKAGES["passive_h2_runtime"] / "summary.json",
        PACKAGES["passive_h2_runtime"] / "heat_ledger_delta.csv",
        PACKAGES["passive_h2_runtime"] / "runtime_input_audit.csv",
        PACKAGES["p1d"] / "summary.json",
        PACKAGES["p1d"] / "residual_completion_gate.csv",
        PACKAGES["cooler"] / "summary.json",
        PACKAGES["source_nominal"] / "nominal_train_release_audit.csv",
        PACKAGES["source_nominal"] / "candidate_lane_consequences.csv",
        PACKAGES["source_unblock"] / "candidate_release_path_table.csv",
        PACKAGES["source_exact"] / "summary.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing candidate gate inputs: " + "; ".join(missing))


def source_row_counts() -> dict[str, int]:
    nominal = read_csv(PACKAGES["source_nominal"] / "nominal_train_release_audit.csv")
    release_ready = sum(row["release_ready"] == "True" for row in nominal)
    strict_ready = sum(
        row["source_validity_envelope_status"] in {"strict_pass", "source_envelope_strict_pass"}
        for row in nominal
    )
    protected = sum(row["protected_row_release"] == "True" for row in nominal)
    return {
        "nominal_train_rows": len(nominal),
        "release_ready_rows": release_ready,
        "strict_source_envelope_pass_rows": strict_ready,
        "protected_row_release_rows": protected,
    }


def candidate_rows() -> list[dict[str, Any]]:
    passive = read_json(PACKAGES["passive_h2"] / "summary.json")
    passive_runtime = read_json(PACKAGES["passive_h2_runtime"] / "summary.json")
    p1d = read_json(PACKAGES["p1d"] / "summary.json")
    cooler = read_json(PACKAGES["cooler"] / "summary.json")

    common_blocker = (
        "row-specific source/property release-ready rows are 0; Qwall/numeric "
        "q-loss release remains closed; no coupled score/freeze evidence"
    )
    h2_runtime_context = (
        f"runtime_delta_qambient_W={passive_runtime['radiation_on_heat_ledger_delta_W']}; "
        f"target_W={passive_runtime['radiation_target_delta_W']}; "
        f"ratio={passive_runtime['radiation_delta_over_target']}"
    )
    return [
        {
            "candidate_id": passive["candidate_id"],
            "candidate_lane": "passive_outer_insulation_radiation_operator",
            "setup_source_basis": "pass_support_only",
            "runtime_legality": "pass_train_only_runtime_smoke",
            "split_legality": "train_support_only_no_protected_scoring",
            "row_specific_source_property_release": "fail_closed",
            "uq_residual_prerequisites": "fail_closed_missing_same_qoi_uq",
            "fit_or_admission_readiness": "fail_closed_no_freeze",
            "primary_numeric_context": h2_runtime_context,
            "primary_blocker": common_blocker,
            "next_unblock": "source-backed role-to-parent/subspan mapping, Salt3/Salt4 split resolution, and same-QOI UQ",
        },
        {
            "candidate_id": p1d["candidate_id"],
            "candidate_lane": "bulk_cv_passive_h2_open_cv_residual_owner",
            "setup_source_basis": "partial_passive_h2_basis",
            "runtime_legality": "prototype_runs_no_fit",
            "split_legality": "train_context_only_no_protected_scoring",
            "row_specific_source_property_release": "fail_closed",
            "uq_residual_prerequisites": "fail_closed_missing_same_basis_residual_inputs",
            "fit_or_admission_readiness": "fail_closed_scorecard_blocked",
            "primary_numeric_context": p1d["nonzero_passive_h2_rows"],
            "primary_blocker": "same-basis residual-computable cases are 0 and source/property release-ready rows are 0",
            "next_unblock": "recover throughflow enthalpy endpoints, cp basis, storage/named losses, and strict source envelope",
        },
        {
            "candidate_id": cooler["selected_current_candidate"],
            "candidate_lane": "cooler_removal_lumped_ua_ntu",
            "setup_source_basis": "candidate_defined_from_setup_screen",
            "runtime_legality": "pending_solver_coupled_compute_run",
            "split_legality": "train_support_pending_no_protected_scoring",
            "row_specific_source_property_release": "fail_closed",
            "uq_residual_prerequisites": "fail_closed_coupled_rows_not_run",
            "fit_or_admission_readiness": "fail_closed_compute_pending",
            "primary_numeric_context": cooler["coupled_rows"],
            "primary_blocker": "coupled Fluid rows all not_run and " + common_blocker,
            "next_unblock": "run coupled cooler candidate on compute node under a separate row after source/property gate clears",
        },
    ]


def subgate_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gates = [
        "setup_source_basis",
        "runtime_legality",
        "split_legality",
        "row_specific_source_property_release",
        "uq_residual_prerequisites",
        "fit_or_admission_readiness",
    ]
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        for gate in gates:
            status = candidate[gate]
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_lane": candidate["candidate_lane"],
                    "subgate": gate,
                    "status": status,
                    "passes_now": status.startswith("pass"),
                    "release_or_freeze_enabled": False,
                    "blocker": "" if status.startswith("pass") else candidate["primary_blocker"],
                }
            )
    return rows


def guardrail_rows() -> list[dict[str, Any]]:
    return [{"guardrail": key, "occurred": value} for key, value in GUARDRAILS.items()]


def source_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, package in PACKAGES.items():
        rows.append(
            {
                "source_label": label,
                "path": rel(package),
                "exists": package.exists(),
                "read_only": True,
                "role": "candidate_gate_input",
            }
        )
    return rows


def blocker_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "blocker": "row_specific_source_property_release",
            "affected_candidates": ";".join(row["candidate_id"] for row in candidates),
            "next_action": "recover row-specific strict source envelope and cp/mu/k/source labels before S11/S15",
        },
        {
            "blocker": "S13_same_basis_residual",
            "affected_candidates": "P1D-BULK-CV-H2-CAND001",
            "next_action": "recover same-window endpoint fields, Qwall/source heat path, storage/named losses, and same-QOI UQ",
        },
        {
            "blocker": "passive_H2_source_mapping_split_uq",
            "affected_candidates": "PASSIVE-H2-CAND001",
            "next_action": "verify H2 source-family-to-Fluid-parent placement, resolve Salt3/Salt4 split conflicts, then run same-QOI setup-only UQ",
        },
        {
            "blocker": "cooler_coupled_compute_pending",
            "affected_candidates": "HX_LUMPED_UA_NTU",
            "next_action": "run solver-coupled candidate under a separate compute row after source/property gate clears",
        },
    ]


def priority_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    explanations = {
        "PASSIVE-H2-CAND001": (
            "Closest to source-bounded physics: setup/passive exterior heat-path "
            "evidence exists and the runtime smoke path keeps protected runtime-use flags false."
        ),
        "P1D-BULK-CV-H2-CAND001": (
            "Broader physical residual owner for passive-H2 energy balance, but it still "
            "needs same-basis endpoint/source terms before it can support fit or admission."
        ),
        "HX_LUMPED_UA_NTU": (
            "Physically meaningful cooler-removal candidate, but admission depends on "
            "coupled rows that have not been run and on the same source/property release."
        ),
    }
    return [
        {
            "priority_rank": index,
            "candidate_id": candidate["candidate_id"],
            "why_promising": explanations[candidate["candidate_id"]],
            "best_next_action": candidate["next_unblock"],
        }
        for index, candidate in enumerate(candidates, start=1)
    ]


def release_decision_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subgates = subgate_rows(candidates)
    rows: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        candidate_subgates = [row for row in subgates if row["candidate_id"] == candidate["candidate_id"]]
        pass_like = sum(row["passes_now"] for row in candidate_subgates)
        hard_fail = len(candidate_subgates) - pass_like
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "priority_rank": rank,
                "subgate_pass_like_rows": pass_like,
                "hard_fail_closed_rows": hard_fail,
                "candidate_specific_source_property_gate_passed": False,
                "fit_or_admission_allowed_now": False,
                "source_property_release_now": False,
                "candidate_freeze_allowed_now": False,
                "decision": "support_subgates_only_final_gate_fail_closed",
                "why": (
                    "The candidate can be prioritized only for repair work; full source/property "
                    "release requires row-specific labels plus strict source-envelope and same-QOI evidence."
                ),
            }
        )
    return rows


def compatibility_gate_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_paths = {
        "PASSIVE-H2-CAND001": rel(PACKAGES["passive_h2"] / "summary.json"),
        "P1D-BULK-CV-H2-CAND001": rel(PACKAGES["p1d"] / "summary.json"),
        "HX_LUMPED_UA_NTU": rel(PACKAGES["cooler"] / "summary.json"),
    }
    rows: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        for subgate in (
            "setup_source_basis",
            "runtime_legality",
            "split_legality",
            "row_specific_source_property_release",
            "uq_residual_prerequisites",
            "fit_or_admission_readiness",
        ):
            status = candidate[subgate]
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "priority_rank": rank,
                    "subgate": subgate,
                    "status": status,
                    "evidence": candidate["primary_numeric_context"] if subgate == "runtime_legality" else candidate["primary_blocker"],
                    "decision_consequence": (
                        "support-only progress; no release or freeze"
                        if status.startswith("pass")
                        else "fail-closed for fit/admission"
                    ),
                    "source_path": source_paths[candidate["candidate_id"]],
                }
            )
    return rows


def next_unblock_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order": index,
            "task": f"{candidate['candidate_id']} source/property repair",
            "candidate_id": candidate["candidate_id"],
            "instruction": candidate["next_unblock"],
            "done_when": "candidate-specific gate rerun reports source/property release-ready rows > 0 without protected scoring",
        }
        for index, candidate in enumerate(candidates, start=1)
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PACKAGES['passive_h2'] / 'summary.json')}
  - {rel(PACKAGES['passive_h2_runtime'] / 'summary.json')}
  - {rel(PACKAGES['p1d'] / 'summary.json')}
  - {rel(PACKAGES['cooler'] / 'summary.json')}
  - {rel(PACKAGES['source_nominal'] / 'nominal_train_release_audit.csv')}
tags: [work-product, source-property, candidate-gate, train-support, no-release]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/candidate-specific-source-property-gate.md
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Reviewer / Tester / Writer
type: work_product
status: complete
---
# Candidate-Specific Source/Property Gate

Decision: `{summary['decision']}`.

This packet reviews three physical candidate lanes against the source/property
and runtime gates needed before any S11/S15 freeze path. It is a gate packet,
not a scorecard. Candidate-level setup/runtime evidence is separated from
row-specific source/property release, wall/source heat-flow release, same-QOI
residual readiness, and freeze/admission readiness. PASSIVE-H2 now consumes the
train-only Fluid runtime-smoke package, so its next blocker is source mapping,
Salt3/Salt4 split status, and same-QOI UQ rather than runtime implementation.

Current result: `{summary['candidate_rows']}` candidates reviewed, source/property
release-ready rows `{summary['source_property_release_ready_rows']}`, protected
row release rows `{summary['protected_row_release_rows']}`, and freeze-ready
candidates `{summary['freeze_ready_candidates']}`. Missing heat residual remains
outside internal Nu.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = candidate_rows()
    counts = source_row_counts()
    release_ready = sum(row["fit_or_admission_readiness"].startswith("pass") for row in candidates)
    summary = {
        "task_id": TASK_ID,
        "decision": "candidate_specific_source_property_gate_fail_closed_no_release_no_freeze",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate_rows": len(candidates),
        "candidate_ids": [row["candidate_id"] for row in candidates],
        "source_property_release_ready_rows": counts["release_ready_rows"],
        "strict_source_envelope_pass_rows": counts["strict_source_envelope_pass_rows"],
        "protected_row_release_rows": counts["protected_row_release_rows"],
        "freeze_ready_candidates": release_ready,
        "s11_open_ready_candidates": release_ready,
        "residual_absorbed_into_internal_Nu": False,
        **GUARDRAILS,
    }
    write_csv(
        OUT / "candidate_gate_matrix.csv",
        candidates,
        [
            "candidate_id",
            "candidate_lane",
            "setup_source_basis",
            "runtime_legality",
            "split_legality",
            "row_specific_source_property_release",
            "uq_residual_prerequisites",
            "fit_or_admission_readiness",
            "primary_numeric_context",
            "primary_blocker",
            "next_unblock",
        ],
    )
    write_csv(
        OUT / "candidate_priority_ranking.csv",
        priority_rows(candidates),
        ["priority_rank", "candidate_id", "why_promising", "best_next_action"],
    )
    write_csv(
        OUT / "candidate_release_decision.csv",
        release_decision_rows(candidates),
        [
            "candidate_id",
            "priority_rank",
            "subgate_pass_like_rows",
            "hard_fail_closed_rows",
            "candidate_specific_source_property_gate_passed",
            "fit_or_admission_allowed_now",
            "source_property_release_now",
            "candidate_freeze_allowed_now",
            "decision",
            "why",
        ],
    )
    write_csv(
        OUT / "candidate_specific_gate_matrix.csv",
        compatibility_gate_rows(candidates),
        ["candidate_id", "priority_rank", "subgate", "status", "evidence", "decision_consequence", "source_path"],
    )
    write_csv(
        OUT / "candidate_subgate_status.csv",
        subgate_rows(candidates),
        ["candidate_id", "candidate_lane", "subgate", "status", "passes_now", "release_or_freeze_enabled", "blocker"],
    )
    write_csv(
        OUT / "next_unblock_sequence.csv",
        next_unblock_rows(candidates),
        ["order", "task", "candidate_id", "instruction", "done_when"],
    )
    write_csv(OUT / "blocker_to_next_action.csv", blocker_rows(candidates), ["blocker", "affected_candidates", "next_action"])
    write_csv(OUT / "no_mutation_guardrails.csv", guardrail_rows(), ["guardrail", "occurred"])
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_label", "path", "exists", "read_only", "role"])
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    build()


if __name__ == "__main__":
    main()
