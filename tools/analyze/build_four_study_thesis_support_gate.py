#!/usr/bin/env python3
"""Build the four-study thesis-support gate package from existing artifacts.

This is a coordinator reducer only. It consumes completed packages read-only and
does not launch solvers, harvests, UQ, fitting, admission, or freeze tasks.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-FOUR-STUDY-THESIS-SUPPORT-GATE-2026-07-22"
OUT_DIR = Path(
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_four_study_thesis_support_gate"
)

SOURCES = {
    "passive_physical": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_passive_h2_cand001_physical_basis"
    ),
    "passive_source_enrichment": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment"
    ),
    "source_residual_decomp": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"
    ),
    "s13_unblock": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
    ),
    "s13_source_side_prereq": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"
    ),
    "s13_exact_qwall": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
    ),
    "s13_limited_evidence": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
    ),
    "predictive_final_starter": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_predictive_final_model_starter"
    ),
    "s6_frozen_scorecard": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_thesis_study_s6_frozen_candidate_scorecard"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    name: bool_text(row.get(name, ""))
                    if isinstance(row.get(name, ""), bool)
                    else row.get(name, "")
                    for name in fieldnames
                }
            )


def bool_text(value: Any) -> str:
    return "true" if value is True else "false" if value is False else str(value)


def source_summary(source_id: str, filename: str = "summary.json") -> dict[str, Any]:
    return load_json(SOURCES[source_id] / filename)


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    passive = source_summary("passive_physical")
    passive_enrich = source_summary("passive_source_enrichment")
    source_decomp = source_summary("source_residual_decomp")
    s13_unblock = source_summary("s13_unblock")
    s13_prereq = source_summary("s13_source_side_prereq")
    s13_exact = source_summary("s13_exact_qwall")
    s13_evidence = source_summary("s13_limited_evidence")
    starter = source_summary("predictive_final_starter")
    s6 = source_summary("s6_frozen_scorecard")

    qwall_rows = load_csv(SOURCES["s13_exact_qwall"] / "trusted_wall_Q_wall_summary.csv")
    qwall_values = [
        f"{row['case_id']}:{float(row['Q_wall_W']):.6g} W/{row['release_status']}"
        for row in qwall_rows
    ]
    qwall_released_rows = sum(
        1 for row in qwall_rows if row.get("Q_wall_W_released", "").lower() == "true"
    )

    tw_focus = load_csv(SOURCES["source_residual_decomp"] / "tw4_tw6_focus.csv")
    tw_response = [
        f"{row['sensor']}:{row['response_class']}:{float(row['delta_abs_residual_K']):.6g} K"
        for row in tw_focus
    ]

    sequence_rows: list[dict[str, Any]] = [
        {
            "study_id": "passive_physical_basis",
            "requested_study": "passive physical-basis study",
            "current_state": "complete",
            "key_evidence": (
                f"h_screen={bool_text(passive['all_current_h_inside_engineering_range'])}; "
                f"q_screen={bool_text(passive['all_current_q_inside_engineering_range'])}; "
                f"families={len(passive['families'])}; "
                f"source_enrichment_rows={passive_enrich['source_family_rows']}"
            ),
            "decision": passive_enrich["decision"],
            "admissibility_boundary": (
                "plausible passive heat path, but all current passive rows retain "
                "wallHeatFlux-derived provenance and no source/property release"
            ),
            "next_action": (
                "release an external heat-path source family only after ambient, area, "
                "insulation, and wallHeatFlux provenance gates pass"
            ),
            "s15_eligible_now": False,
        },
        {
            "study_id": "source_sink_residual_decomposition",
            "requested_study": "source/sink residual decomposition",
            "current_state": "complete_train_only",
            "key_evidence": "; ".join(tw_response),
            "decision": source_decomp["decision"],
            "admissibility_boundary": (
                "train-only source lane shows partial/local improvement and cannot "
                "be promoted to validation, holdout, external, freeze, or admission"
            ),
            "next_action": (
                "develop explicit missing source/sink or redistribution physics; do "
                "not absorb the residual into internal Nu"
            ),
            "s15_eligible_now": False,
        },
        {
            "study_id": "s13_sampled_field_qwall_harvest",
            "requested_study": "S13 sampled-field/Qwall harvest",
            "current_state": "exact_pressure_and_qwall_released_but_production_blocked",
            "key_evidence": (
                f"pressure_basis_rows={s13_exact['pressure_basis_released_rows']}; "
                f"Q_wall_release_rows={qwall_released_rows}; "
                f"Q_wall_values={' | '.join(qwall_values)}; "
                f"finite_exchange_rows={s13_evidence['finite_exchange_rows']}"
            ),
            "decision": s13_evidence["decision"],
            "admissibility_boundary": (
                "exact pressure and Q_wall_W inputs are available, but same-QOI "
                "UQ/production harvest are not executed and no candidate is released"
            ),
            "next_action": (
                "complete active source-side conservation/neighbour/UQ gate or a "
                "separate production harvest row before any S13 review"
            ),
            "s15_eligible_now": False,
        },
        {
            "study_id": "candidate_freeze_no_freeze",
            "requested_study": "one candidate freeze/no-freeze study",
            "current_state": "no_freeze",
            "key_evidence": (
                f"starter_freeze_blocking_gate_rows={starter['freeze_blocking_gate_rows']}; "
                f"s6_final_score_values={s6['final_score_values_published']}; "
                f"s6_source_property_release_rows={s6['source_property_release_rows']}"
            ),
            "decision": "no_freeze_no_single_released_candidate",
            "admissibility_boundary": (
                "S15 is trigger-gated after exactly one candidate is released by "
                "S12, S13, or S14; that condition is not met"
            ),
            "next_action": (
                "wait for a source/property-released candidate, then run S15 without "
                "changing split roles or using protected rows for model selection"
            ),
            "s15_eligible_now": False,
        },
    ]

    candidate_rows: list[dict[str, Any]] = [
        {
            "candidate_or_lane": "PASSIVE-H2-CAND001",
            "basis": "external passive heat path",
            "diagnostic_evidence_available": True,
            "source_property_released": passive_enrich["source_property_release"],
            "qwall_or_equivalent_released": False,
            "same_qoi_uq_ready": False,
            "production_or_repair_allowed": passive_enrich["run_one_train_repair"],
            "candidate_released": False,
            "s15_eligible": False,
            "freeze_decision": "no_freeze",
            "blocking_reason": "source basis enriched but no source/property release or repair",
        },
        {
            "candidate_or_lane": "KNOWN-HEATER-SOURCE-RESIDUAL-LANE",
            "basis": "known heater source/sink decomposition",
            "diagnostic_evidence_available": True,
            "source_property_released": source_decomp["source_property_release"],
            "qwall_or_equivalent_released": False,
            "same_qoi_uq_ready": False,
            "production_or_repair_allowed": False,
            "candidate_released": False,
            "s15_eligible": False,
            "freeze_decision": "no_freeze",
            "blocking_reason": "partial train-only improvement; model form still needed",
        },
        {
            "candidate_or_lane": "S13-DIRECT-QWALL",
            "basis": "trusted-wall wallHeatFlux integration",
            "diagnostic_evidence_available": True,
            "source_property_released": False,
            "qwall_or_equivalent_released": qwall_released_rows > 0,
            "same_qoi_uq_ready": s13_exact["same_qoi_uq_ready"],
            "production_or_repair_allowed": s13_exact["production_harvest_allowed_now"],
            "candidate_released": False,
            "s15_eligible": False,
            "freeze_decision": "no_freeze",
            "blocking_reason": "Q_wall_W released, but same-QOI UQ/production harvest remain blocked",
        },
        {
            "candidate_or_lane": "S13-SOURCE-SIDE-EQUIVALENT",
            "basis": "Q_source_side_net_static_bc_W",
            "diagnostic_evidence_available": s13_prereq[
                "Q_source_side_net_static_bc_W_defined"
            ],
            "source_property_released": s13_prereq["source_property_release"],
            "qwall_or_equivalent_released": False,
            "same_qoi_uq_ready": s13_prereq["same_qoi_uq_release_allowed"],
            "production_or_repair_allowed": s13_prereq["production_harvest_allowed"],
            "candidate_released": False,
            "s15_eligible": False,
            "freeze_decision": "no_freeze",
            "blocking_reason": "same-QOI UQ prerequisite not executed; no production release",
        },
    ]

    gate_rows: list[dict[str, Any]] = [
        {
            "gate": "exactly_one_candidate_released",
            "status": "fail",
            "allowed": False,
            "reason": "zero candidate_or_lane rows have candidate_released=true",
        },
        {
            "gate": "source_property_release",
            "status": "fail",
            "allowed": False,
            "reason": "all inspected lanes report source_property_released=false",
        },
        {
            "gate": "same_qoi_uq_or_release_basis",
            "status": "fail",
            "allowed": False,
            "reason": "S13 direct Qwall exists, but same-QOI UQ is not ready/executed and passive/source lanes are unreleased",
        },
        {
            "gate": "protected_split_integrity",
            "status": "pass",
            "allowed": True,
            "reason": "consumed zero validation/holdout/external rows and performed no fit/model selection",
        },
        {
            "gate": "s15_candidate_freeze",
            "status": "blocked_no_freeze",
            "allowed": False,
            "reason": "S15 remains trigger-gated until exactly one released candidate exists",
        },
    ]

    next_rows: list[dict[str, Any]] = [
        {
            "priority": 1,
            "next_action": "Close active S13 source-side conservation/neighbour/UQ gate from existing evidence",
            "allowed_row": "TODO-S13-UPCOMER-EXCHANGE-SOURCE-SIDE-CONSERVATION-NEIGHBOR-UQ-GATE-2026-07-22",
            "blocked_by": "same-QOI UQ/source-property prerequisites",
            "acceptance_signal": "release or fail-close source-side equivalent without relabeling it as Q_wall_W",
        },
        {
            "priority": 2,
            "next_action": "If S13 production prerequisites pass, claim production harvest/UQ row",
            "allowed_row": "TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21",
            "blocked_by": "production_harvest_allowed=false in current packages",
            "acceptance_signal": "same-window harvest and same-QOI UQ table, or explicit fail-closed S13 decision",
        },
        {
            "priority": 3,
            "next_action": "Turn passive physical-basis diagnostics into a source-family release candidate",
            "allowed_row": "new exact passive source release row after enrichment blockers are resolved",
            "blocked_by": "wallHeatFlux provenance and ambient/area/insulation source basis not released",
            "acceptance_signal": "families_released>0 and no global hA multiplier or validation leakage",
        },
        {
            "priority": 4,
            "next_action": "Run S15 only after exactly one S12/S13/S14 candidate is released",
            "allowed_row": "TODO-THESIS-STUDY-S15-CANDIDATE-FREEZE-SOURCE-PROPERTY-SCORE-RELEASE-2026-07-21",
            "blocked_by": "candidate_released_count=0",
            "acceptance_signal": "candidate freeze/no-freeze with protected split roles preserved",
        },
    ]

    manifest_rows = [
        {
            "source_id": source_id,
            "source_path": str(path),
            "consumed_files": "summary.json"
            if source_id != "s13_exact_qwall"
            else "summary.json;trusted_wall_Q_wall_summary.csv",
            "mutation_status": "read_only",
            "provenance_role": "input_evidence",
        }
        for source_id, path in SOURCES.items()
    ]
    manifest_rows.append(
        {
            "source_id": "source_residual_tw4_tw6_focus",
            "source_path": str(SOURCES["source_residual_decomp"] / "tw4_tw6_focus.csv"),
            "consumed_files": "tw4_tw6_focus.csv",
            "mutation_status": "read_only",
            "provenance_role": "local residual response evidence",
        }
    )

    write_csv(
        OUT_DIR / "four_study_sequence_status.csv",
        sequence_rows,
        [
            "study_id",
            "requested_study",
            "current_state",
            "key_evidence",
            "decision",
            "admissibility_boundary",
            "next_action",
            "s15_eligible_now",
        ],
    )
    write_csv(
        OUT_DIR / "candidate_freeze_readiness_matrix.csv",
        candidate_rows,
        [
            "candidate_or_lane",
            "basis",
            "diagnostic_evidence_available",
            "source_property_released",
            "qwall_or_equivalent_released",
            "same_qoi_uq_ready",
            "production_or_repair_allowed",
            "candidate_released",
            "s15_eligible",
            "freeze_decision",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT_DIR / "s15_trigger_gate.csv",
        gate_rows,
        ["gate", "status", "allowed", "reason"],
    )
    write_csv(
        OUT_DIR / "next_action_queue.csv",
        next_rows,
        ["priority", "next_action", "allowed_row", "blocked_by", "acceptance_signal"],
    )
    write_csv(
        OUT_DIR / "source_manifest.csv",
        manifest_rows,
        ["source_id", "source_path", "consumed_files", "mutation_status", "provenance_role"],
    )

    released_count = sum(1 for row in candidate_rows if row["candidate_released"])
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "no_freeze_no_single_released_candidate",
        "study_rows": len(sequence_rows),
        "candidate_rows": len(candidate_rows),
        "candidate_released_count": released_count,
        "s15_trigger_allowed": released_count == 1,
        "passive_physical_basis_status": passive["gate_decision"],
        "passive_source_basis_decision": passive_enrich["decision"],
        "source_sink_residual_decision": source_decomp["decision"],
        "s13_exact_qwall_decision": s13_exact["decision"],
        "s13_Q_wall_W_released_rows": qwall_released_rows,
        "s13_production_harvest_allowed_rows": s13_evidence[
            "production_harvest_allowed_rows"
        ],
        "s13_same_qoi_uq_ready": bool(s13_exact["same_qoi_uq_ready"]),
        "s6_final_score_values_published": s6["final_score_values_published"],
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "thesis_current_file_edit": False,
        "validation_holdout_external_rows_scored": 0,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "coefficient_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    readme = f"""---
provenance:
  - {SOURCES['passive_physical'] / 'summary.json'}
  - {SOURCES['passive_source_enrichment'] / 'summary.json'}
  - {SOURCES['source_residual_decomp'] / 'summary.json'}
  - {SOURCES['source_residual_decomp'] / 'tw4_tw6_focus.csv'}
  - {SOURCES['s13_exact_qwall'] / 'summary.json'}
  - {SOURCES['s13_exact_qwall'] / 'trusted_wall_Q_wall_summary.csv'}
  - {SOURCES['s13_limited_evidence'] / 'summary.json'}
  - {SOURCES['predictive_final_starter'] / 'summary.json'}
  - {SOURCES['s6_frozen_scorecard'] / 'summary.json'}
tags: [thesis, predictive-model, passive-heat-path, source-sink-residual, s13-upcomer-exchange, freeze-gate]
related:
  - .agent/status/2026-07-22_TODO-FOUR-STUDY-THESIS-SUPPORT-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/four-study-thesis-support-gate.md
  - imports/2026-07-22_four_study_thesis_support_gate.json
task: {TASK_ID}
date: 2026-07-22
role: Coordinator/Writer/Tester/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---

# Four-Study Thesis Support Gate

Generated by `{TASK_ID}`.

## Decision

`{summary['decision']}`. The requested studies are thesis-useful as diagnostics,
but none releases exactly one candidate for S15.

## What This Implements

- Passive physical-basis study: completed and enriched, but source/property
  release remains false.
- Source/sink residual decomposition: completed as train-only evidence with
  partial/local response; model-form uncertainty remains.
- S13 sampled-field/Qwall harvest path: exact pressure and `Q_wall_W` inputs
  are released, but production harvest, same-QOI UQ, and candidate release are
  still blocked.
- Candidate freeze/no-freeze study: evaluated as `no_freeze` because no
  released candidate exists.

## Thesis Claim Boundary

The failure is diagnostic, not a dead end. It localizes the next scientific
uncertainty to external heat-path physical basis and missing source/sink or
redistribution physics. A global response cannot be admitted as a fit, and no
thermal residual was absorbed into internal Nu.

## Outputs

- `four_study_sequence_status.csv`
- `candidate_freeze_readiness_matrix.csv`
- `s15_trigger_gate.csv`
- `next_action_queue.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT_DIR / "README.md").write_text(readme)

    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
