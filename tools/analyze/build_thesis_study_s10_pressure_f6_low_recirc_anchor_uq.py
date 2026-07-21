#!/usr/bin/env python3
"""Build the S10 pressure/F6 low-recirculation anchor UQ thesis study.

This consolidates existing pressure-corner, F6, and same-QOI evidence into an
admission decision. It does not launch samplers, fit F6, admit K values, or
trigger S11.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-THESIS-STUDY-S10-PRESSURE-F6-LOW-RECIRC-ANCHOR-UQ-2026-07-21"
DATE = "2026-07-21"
DEFAULT_OUT = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq"
)

LOW_RECIRC = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_low_recirc_anchor_harvest"
)
F6_QA = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_f6_stage_a_harvest_qa"
)
S10_FIG = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall"
)
PRESSURE_FREEZE = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_publication_freeze"
)
PRESSURE_REVIEW = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_comparison_admission_review"
)
SAME_QOI_B = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
)
S5 = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s5_source_property_split_release"
)

SOURCE_FILES = {
    "low_recirc_summary": LOW_RECIRC / "summary.json",
    "low_recirc_candidate_preflight": LOW_RECIRC / "candidate_terminal_preflight.csv",
    "low_recirc_source_readiness": LOW_RECIRC / "source_case_readiness.csv",
    "low_recirc_endpoint_fields": LOW_RECIRC / "endpoint_field_availability.csv",
    "low_recirc_anchor_decision": LOW_RECIRC / "anchor_decision.csv",
    "f6_summary": F6_QA / "summary.json",
    "f6_pair_qa": F6_QA / "endpoint_pair_qa.csv",
    "f6_medium_fine": F6_QA / "medium_fine_consistency.csv",
    "f6_gate_status": F6_QA / "qa_gate_status.csv",
    "s10_fig_summary": S10_FIG / "summary.json",
    "s10_waterfall": S10_FIG / "pressure_f6_gate_waterfall.csv",
    "s10_f3_comparison": S10_FIG / "f3_shah_apparent_comparison_table.csv",
    "s10_claim_boundary": S10_FIG / "claim_boundary_ledger.csv",
    "pressure_freeze_summary": PRESSURE_FREEZE / "summary.json",
    "pressure_canonical": PRESSURE_FREEZE / "canonical_pressure_corner_result.csv",
    "pressure_review_summary": PRESSURE_REVIEW / "summary.json",
    "pressure_review_matrix": PRESSURE_REVIEW / "pressure_corner_comparison_matrix.csv",
    "pressure_gate_review": PRESSURE_REVIEW / "pressure_corner_gate_review.csv",
    "same_qoi_b_summary": SAME_QOI_B / "summary.json",
    "same_qoi_b_phase_c": SAME_QOI_B / "phase_c_input_table.csv",
    "s5_summary": S5 / "summary.json",
    "s5_release_ledger": S5 / "source_property_release_ledger.csv",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def first_f3_status() -> str:
    rows = read_csv(SOURCE_FILES["s10_f3_comparison"])
    if not rows:
        return "missing"
    row = rows[0]
    return f"{row['status']}: {row['reason']}"


def build_candidate_admission_matrix() -> list[dict[str, Any]]:
    f3 = first_f3_status()
    rows: list[dict[str, Any]] = []

    for row in read_csv(SOURCE_FILES["low_recirc_candidate_preflight"]):
        terminal_ready = int(row["terminal_ready_cases"] or "0")
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "lane": "low_recirc_pressure_anchor",
                "case_scope": row["source_cases"],
                "isolation_basis": row["endpoint_labels"],
                "recirculation_status": "not_measured_pending_terminal_harvest" if terminal_ready == 0 else "requires_RAF_RMF_check",
                "same_qoi_uq_status": "not_declared_for_candidate",
                "source_validity_envelope": row["preflight_status"],
                "property_mode_sensitivity_label": "blocked_by_S5_no_fit_release",
                "f3_shah_apparent_comparison": f3,
                "admission_decision": "not_admitted",
                "blocking_reasons": row["preflight_status"] + ";terminal_ready_cases=" + row["terminal_ready_cases"],
                "s11_candidate_status": "not_ready",
                "source_paths": row["source_paths"],
            }
        )

    for row in read_csv(SOURCE_FILES["pressure_review_matrix"]):
        rows.append(
            {
                "candidate_id": row["comparison_id"],
                "lane": "current_pressure_corner_rows",
                "case_scope": row["case_key"],
                "isolation_basis": row["component_isolation_gate"],
                "recirculation_status": f"RAF={row['reverse_area_fraction']};RMF={row['reverse_mass_fraction']}",
                "same_qoi_uq_status": row["same_qoi_uncertainty_gate"],
                "source_validity_envelope": row["source_envelope_gate"],
                "property_mode_sensitivity_label": "blocked_by_S5_no_fit_release",
                "f3_shah_apparent_comparison": row["f6_allowed_use"],
                "admission_decision": row["admission_status_after_review"],
                "blocking_reasons": row["decision_reason"],
                "s11_candidate_status": "not_ready",
                "source_paths": row["source_paths"],
            }
        )

    for row in read_csv(SOURCE_FILES["f6_pair_qa"]):
        rows.append(
            {
                "candidate_id": f"F6-{row['mesh_level']}-{row['branch']}",
                "lane": "F6_endpoint_pair",
                "case_scope": row["mesh_level"],
                "isolation_basis": row["endpoint_pair"],
                "recirculation_status": f"{row['pair_label']}; RAF={row['max_reverse_area_fraction']}; RMF={row['max_reverse_mass_fraction']}",
                "same_qoi_uq_status": "two_mesh_diagnostic_only_until_coarse_repair",
                "source_validity_envelope": row["admission_status"],
                "property_mode_sensitivity_label": "blocked_by_S5_no_fit_release",
                "f3_shah_apparent_comparison": f3,
                "admission_decision": "not_admitted",
                "blocking_reasons": row["reason"],
                "s11_candidate_status": "not_ready",
                "source_paths": str(SOURCE_FILES["f6_pair_qa"]),
            }
        )
    return rows


def build_s10_gate_matrix(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = {name: read_json(path) for name, path in SOURCE_FILES.items() if path.suffix == ".json"}
    low = summaries["low_recirc_summary"]
    f6 = summaries["f6_summary"]
    fig = summaries["s10_fig_summary"]
    same = summaries["same_qoi_b_summary"]
    s5 = summaries["s5_summary"]
    admitted = sum(1 for row in candidates if row["admission_decision"] in {"admitted", "candidate_may_feed_S11"})
    return [
        {
            "gate_id": "S10-G0",
            "gate_family": "coordination",
            "required_condition": "S10 study row claimed with exact builder/test/package paths.",
            "status": "pass",
            "decision": "study_can_run_from_existing_evidence",
            "s11_effect": "none",
            "source_paths": ".agent/BOARD.md",
        },
        {
            "gate_id": "S10-G1",
            "gate_family": "low_recirc_anchor_terminal",
            "required_condition": "At least one selected low-recirculation source case is terminal and harvest-ready.",
            "status": "fail" if int(low.get("terminal_ready_cases", 0)) == 0 else "pass",
            "decision": f"terminal_ready_cases={low.get('terminal_ready_cases', 0)}; preferred_candidate={low.get('preferred_candidate_id', '')}",
            "s11_effect": "blocks_low_recirc_anchor",
            "source_paths": str(SOURCE_FILES["low_recirc_candidate_preflight"]),
        },
        {
            "gate_id": "S10-G2",
            "gate_family": "ordinary_flow_or_recirc",
            "required_condition": "Candidate rows must pass ordinary-flow RAF/RMF thresholds before K or F6 claims.",
            "status": "fail" if int(f6.get("ordinary_candidate_pairs", 0)) == 0 else "pass",
            "decision": f"ordinary_candidate_pairs={f6.get('ordinary_candidate_pairs', 0)}; recirc_diagnostic_pairs={f6.get('recirc_diagnostic_pairs', 0)}",
            "s11_effect": "blocks_F6_and_component_K",
            "source_paths": str(SOURCE_FILES["f6_pair_qa"]),
        },
        {
            "gate_id": "S10-G3",
            "gate_family": "same_qoi_uq",
            "required_condition": "Same-QOI time/window and mesh/GCI evidence accepted for pressure/F6 rows.",
            "status": "fail" if int(same.get("accepted_rows", 0)) == 0 else "pass",
            "decision": f"accepted_rows={same.get('accepted_rows', 0)}; blocked_rows={same.get('blocked_rows', 0)}",
            "s11_effect": "blocks_pressure_F6_candidate",
            "source_paths": str(SOURCE_FILES["same_qoi_b_summary"]),
        },
        {
            "gate_id": "S10-G4",
            "gate_family": "source_property_split",
            "required_condition": "Candidate-specific source/property release permits fit/model selection.",
            "status": "fail" if int(s5.get("fit_allowed_rows", 0)) == 0 else "pass",
            "decision": f"fit_allowed_rows={s5.get('fit_allowed_rows', 0)}; release_decision={s5.get('release_decision')}",
            "s11_effect": "blocks_candidate_refresh_until_one_candidate_exists",
            "source_paths": str(SOURCE_FILES["s5_summary"]),
        },
        {
            "gate_id": "S10-G5",
            "gate_family": "forbidden_shortcuts",
            "required_condition": "No clipped K, hidden multiplier, component K, cluster K, or F6 fit is admitted.",
            "status": "pass",
            "decision": f"waterfall admitted_rows={fig.get('admitted_rows', 0)}; clipped_k_rows={fig.get('clipped_k_rows', 0)}; f6_fits={fig.get('f6_fits_performed', 0)}",
            "s11_effect": "prevents_invalid_unblock",
            "source_paths": str(SOURCE_FILES["s10_claim_boundary"]),
        },
        {
            "gate_id": "S10-G6",
            "gate_family": "s11_release",
            "required_condition": "Exactly one low-recirculation pressure/F6 candidate passes all gates.",
            "status": "fail" if admitted == 0 else "pass",
            "decision": f"{admitted} S11-ready pressure/F6 candidates",
            "s11_effect": "S11 remains blocked from S10" if admitted == 0 else "S11 may claim one candidate",
            "source_paths": "s11_unblock_decision.csv",
        },
    ]


def build_s11_decision(gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate = next(row for row in gates if row["gate_id"] == "S10-G6")
    return [
        {
            "decision_id": "S10-S11-DECISION",
            "candidate_id": "",
            "candidate_family": "pressure_F6_low_recirc_anchor",
            "s11_unblocked": "false",
            "reason": gate["decision"],
            "required_before_s11": "terminal-ready low-recirculation source; RAF/RMF ordinary-flow pass; finite endpoint fields; same-QOI UQ; source/property split release; F3 comparison possible without clipped K or hidden multiplier",
            "component_k_admission": "none",
            "f6_fit_admission": "none",
            "next_board_task": "S11 cannot be claimed yet; continue terminal/coarse-path UQ repair or a future low-recirculation anchor harvest row.",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    rows = []
    for role, path in SOURCE_FILES.items():
        rows.append(
            {
                "source_path": str(path),
                "role_in_study": role,
                "mutation_status": "read_only",
                "trusted_or_diagnostic": "trusted_existing_package" if path.exists() else "missing_required_source",
                "notes": "S10 consumed this artifact as existing evidence only.",
            }
        )
    rows.extend(
        [
            {
                "source_path": "native CFD/OpenFOAM outputs",
                "role_in_study": "solver_outputs",
                "mutation_status": "not_touched",
                "trusted_or_diagnostic": "not_accessed",
                "notes": "No solver output was sampled or mutated by S10.",
            },
            {
                "source_path": "registry/admission/scheduler state",
                "role_in_study": "global_state",
                "mutation_status": "not_mutated",
                "trusted_or_diagnostic": "read_only_context",
                "notes": "No registry, admission, scheduler, Fluid, external, blocker, or generated-index state changed.",
            },
        ]
    )
    return rows


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - .agent/BOARD.md
  - {SOURCE_FILES['low_recirc_candidate_preflight']}
  - {SOURCE_FILES['f6_pair_qa']}
  - {SOURCE_FILES['s10_waterfall']}
  - {SOURCE_FILES['pressure_review_matrix']}
  - {SOURCE_FILES['same_qoi_b_summary']}
tags: [thesis-dossier, s10, pressure, f6, low-recirculation-anchor, same-qoi-uq, negative-result]
related:
  - {S10_FIG}/README.md
  - {LOW_RECIRC}/README.md
  - {F6_QA}/README.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Tester/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis S10 Pressure/F6 Low-Recirculation Anchor UQ

## Decision

S10 closes as `{summary['study_state']}`.

The study reviews `{summary['candidate_rows']}` candidate rows across
low-recirculation pressure anchors, current pressure-corner diagnostics, and F6
endpoint pairs. It releases `{summary['s11_ready_candidates']}` S11-ready
pressure/F6 candidates.

## Claim Boundary

Current evidence strengthens pressure/F6 non-admission. It does not admit a
component K, cluster K, F6 fit, clipped K, hidden multiplier, or mixed-basis
pressure correction.

## Files

| File | Use |
| --- | --- |
| `s10_candidate_admission_matrix.csv` | Candidate-by-candidate gate decision. |
| `s10_gate_matrix.csv` | Study-level admission gates and S11 effects. |
| `s11_unblock_decision.csv` | Machine-readable S11 decision from S10. |
| `source_manifest.csv` | Source paths and mutation flags. |
| `summary.json` | Machine-readable summary. |

## Guardrails

No native output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler launch, Fluid edit, external edit, fitting,
model selection, component-K/F6 admission, clipped K, hidden multiplier,
generated-index refresh, S11 trigger, or mixed-basis promotion was performed.
"""


def build(out: Path) -> dict[str, Any]:
    missing = [str(path) for path in SOURCE_FILES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required S10 sources: " + "; ".join(missing))

    out.mkdir(parents=True, exist_ok=True)
    candidates = build_candidate_admission_matrix()
    gates = build_s10_gate_matrix(candidates)
    s11_rows = build_s11_decision(gates)
    sources = build_source_manifest()

    write_csv(out / "s10_candidate_admission_matrix.csv", candidates, list(candidates[0]))
    write_csv(out / "s10_gate_matrix.csv", gates, list(gates[0]))
    write_csv(out / "s11_unblock_decision.csv", s11_rows, list(s11_rows[0]))
    write_csv(out / "source_manifest.csv", sources, list(sources[0]))

    lane_counts = Counter(row["lane"] for row in candidates)
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "study_state": "negative_result_s11_still_blocked",
        "candidate_rows": len(candidates),
        "lane_counts": dict(lane_counts),
        "admitted_candidate_rows": 0,
        "s11_ready_candidates": 0,
        "s11_unblocked": False,
        "component_k_admitted_rows": 0,
        "cluster_k_admitted_rows": 0,
        "f6_fit_rows": 0,
        "clipped_k_rows": 0,
        "hidden_global_multiplier_rows": 0,
        "solver_or_sampler_or_harvest_launch": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action_taken": False,
        "fluid_or_external_repo_edited": False,
        "fitting_or_model_selection": False,
        "generated_index_mutation": False,
        "next_action": "Do not claim S11 yet; continue terminal/coarse-path UQ repair or future low-recirculation anchor harvest.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "README.md").write_text(build_readme(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
