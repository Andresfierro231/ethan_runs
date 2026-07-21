#!/usr/bin/env python3
"""Build the H1 faithful-implementation gap and F6 candidate decision package."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_h1_faithful_gap_and_f6_decision"

H1_SCORECARD_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/summary.json"
H1_SCORECARD_README = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md"
LOCALIZED_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/summary.json"
LOCALIZED_SOURCE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/localized_fixed_k_source.csv"
CORRECTION_README = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/README.md"
NAMED_LOSSES = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv"
RESET_MAP = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv"
F6_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_f6_hydraulic_screen/summary.json"
F6_SCORECARD = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_f6_hydraulic_screen/f6_hydraulic_scorecard.csv"
BLOCKERS = REPO_ROOT / ".agent/BLOCKERS.md"


def _read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _count(rows: Iterable[Dict[str, str]], predicate) -> int:
    return sum(1 for row in rows if predicate(row))


def build_package(output_dir: Path = OUTPUT_DIR) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    h1_summary = _read_json(H1_SCORECARD_SUMMARY)
    h1_f1 = h1_summary["variant_decisions"]["F1_heater_only"]  # type: ignore[index]
    localized_summary = _read_json(LOCALIZED_SUMMARY)
    f6_summary = _read_json(F6_SUMMARY)
    localized_rows = _read_csv(LOCALIZED_SOURCE)
    named_rows = _read_csv(NAMED_LOSSES)
    reset_rows = _read_csv(RESET_MAP)

    localized_included = [row for row in localized_rows if row.get("included_in_localized_score") == "yes"]
    branch_apparent_fit_rows = [
        row for row in named_rows
        if row.get("loss_class") == "branch_apparent" and row.get("fit_use_status") == "fit_target"
    ]
    cluster_rows = [row for row in named_rows if row.get("loss_class") == "cluster_K"]
    reset_flagged_rows = [row for row in reset_rows if row.get("hydraulic_reset_status") == "reset_flagged"]
    reset_feature_rows = [
        row for row in reset_rows
        if "feature_reset_assumed" in row.get("hydraulic_reset_status", "")
    ]

    h1_gap_rows = [
        {
            "gap_id": "H1_PROXY_AGGREGATE_FIXED_K",
            "closure_piece": "aggregate proxy resistance",
            "current_evidence": (
                "AGENT-310 H1 proxy improves F1_heater_only mean mdot error from "
                f"{h1_f1['mean_baseline_abs_mdot_error_kg_s']:.7f} to "
                f"{h1_f1['mean_h1_abs_mdot_error_kg_s']:.7f} kg/s "
                f"({h1_f1['mean_mdot_error_reduction_pct']:.2f}% reduction)."
            ),
            "faithful_requirement": "Replace aggregate proxy with named local loss and reset/development terms only.",
            "gap_type": "model_form",
            "current_status": "proxy_only_retired_for_faithful_closure",
            "blocking_detail": "The aggregate proxy moves mdot but does not identify which physical losses caused the resistance increase.",
            "required_next_action": "Do not use aggregate H1 as final closure; keep only as diagnostic proof that added hydraulic resistance can move mdot.",
            "acceptance_gate": "No aggregate K or global resistance term appears in a forward-v1 candidate.",
        },
        {
            "gap_id": "H1_LOCALIZED_FIXED_K_DIRECTION",
            "closure_piece": "localized fixed K",
            "current_evidence": (
                f"AGENT-328 localized fixed-K score used keys {localized_summary['localized_fixed_k_keys']} "
                f"with total K={localized_summary['localized_fixed_k_total']:.6f}; "
                f"F1 mean mdot error changed to {localized_summary['f1_mean_localized_abs_mdot_error_kg_s']:.7f} kg/s "
                f"({localized_summary['f1_mean_mdot_error_reduction_pct']:.2f}% reduction, negative means worse)."
            ),
            "faithful_requirement": "Localized K must improve train, validation, and holdout direction without thermal fitting.",
            "gap_type": "screen_result",
            "current_status": "failed_directional_screen",
            "blocking_detail": "Localized-only K did not reproduce the aggregate proxy movement; reset/development semantics are missing.",
            "required_next_action": "Retire localized-fixed-K-only H1 as final candidate.",
            "acceptance_gate": "A faithful H1 rerun must beat baseline on Salt2 train and not worsen Salt3/Salt4 no-refit diagnostics.",
        },
        {
            "gap_id": "H1_BRANCH_APPARENT_NOT_COMPONENT_K",
            "closure_piece": "branch-apparent K extraction",
            "current_evidence": f"{len(branch_apparent_fit_rows)} branch-apparent fit-target rows exist; {len(localized_included)} Salt2 rows entered localized fixed-K scoring.",
            "faithful_requirement": "Separate straight friction, component K, cluster K, branch-apparent loss, and residual before assigning a coefficient.",
            "gap_type": "data_reduction",
            "current_status": "not_faithful_as_component_loss",
            "blocking_detail": "Branch-apparent rows include straight, reset/development, cluster, and residual effects and carry coarse/no-GCI flags.",
            "required_next_action": "Use branch-apparent rows only as upper-bound screens unless component/cluster rows can be isolated with centerline tap lengths.",
            "acceptance_gate": "Each local K row has a coefficient class, finite K, centerline length basis, source path, and fit/validation status.",
        },
        {
            "gap_id": "H1_RESET_REDEVELOPMENT_NOT_IMPLEMENTED",
            "closure_piece": "reset/development",
            "current_evidence": f"{len(reset_flagged_rows)} reset-flagged span rows and {len(reset_feature_rows)} feature-reset rows exist in reset_distance_map.csv.",
            "faithful_requirement": "Represent reset/development as a distinct hydraulic term keyed to reset feature, downstream segment, x/D, Re, and entry validity.",
            "gap_type": "code_api",
            "current_status": "missing_first_class_term",
            "blocking_detail": "Fluid has segment-entry friction forms, but no first-class feature-reset object that applies redevelopment after bends/junctions within the closure ledger.",
            "required_next_action": "Add a reset/development input table and diagnostics before any faithful H1 rerun.",
            "acceptance_gate": "Forward run reports fixed component K, cluster K, branch-apparent diagnostic, and reset/development pressure terms separately.",
        },
        {
            "gap_id": "H1_RECIRCULATION_INVALID_SINGLE_COEFFICIENTS",
            "closure_piece": "upcomer/test-section recirculation",
            "current_evidence": f"{_count(named_rows, lambda r: 'recirculation_invalid_single_f' in r.get('quality_flags', ''))} named-loss rows carry recirculation-invalid flags.",
            "faithful_requirement": "Do not fit universal f or K on recirculating regions; keep them diagnostic or use section-effective labels.",
            "gap_type": "physics_admission",
            "current_status": "blocked_for_universal_coefficient",
            "blocking_detail": "Left-lower/left-upper upcomer and test-section-adjacent rows cannot be reduced to a single-stream K/f without a recirculation-aware model.",
            "required_next_action": "Exclude recirculating rows from H1 coefficient fitting; report them as diagnostics only.",
            "acceptance_gate": "No recirculation-invalid row is used as a universal K or f_D fit target.",
        },
        {
            "gap_id": "H1_MESH_TAP_LENGTH_ADMISSION",
            "closure_piece": "mesh/tap-length trust",
            "current_evidence": "Named-loss rows are coarse/no-GCI; cluster K rows include tap_length_proxy_abs_dz_not_centerline_length and K_local upper-bound flags.",
            "faithful_requirement": "Use mesh-qualified rows and true centerline tap-to-tap lengths for component/cluster K.",
            "gap_type": "admission_data",
            "current_status": "blocked_for_publication_closure",
            "blocking_detail": "The current rows may support bounded diagnostics but not a publication-ready local-loss closure.",
            "required_next_action": "Postprocess centerline tap lengths and mesh-family pressure terms before admitting component/cluster K.",
            "acceptance_gate": "At least train rows have centerline tap lengths and mesh/GCI status; validation/holdout rows remain no-refit.",
        },
    ]

    f6_decision_rows = [
        {
            "candidate_id": "F6_phi_re",
            "candidate_type": "friction_re_multiplier_over_F3_shah",
            "current_evidence": (
                f"Fluid code available={str(f6_summary['f6_code_available']).lower()}; "
                f"raw fit-safe rows={f6_summary['raw_fit_safe_training_rows']}; "
                f"diagnostic momentum rows={f6_summary['diagnostic_momentum_rows']}; "
                f"publication-ready GCI rows={f6_summary['publication_ready_gci_rows']}; "
                "corrected-Q admitted rows=0."
            ),
            "decision": "next_bounded_candidate_after_admission_preconditions",
            "why": "H1 faithful path is blocked/retired as current proxy; F6 tests a physically narrower Re-dependent friction multiplier without global K or thermal fitting.",
            "preconditions": "Terminal/admitted corrected-Q or equivalent Re-variation rows; no recirculation-invalid fit rows; no thermal fitting; no global multiplier.",
            "primary_acceptance_metric": "Validation/holdout segment pressure-loss error improves versus F3_shah_apparent on admitted non-recirculating spans.",
            "secondary_mdot_guardrail": "No-refit Salt3/Salt4 mdot error must not worsen, and mean mdot error should improve by >=30% versus baseline for a bounded screen.",
            "rejection_rule": "Reject if improvement comes only from a global multiplier, recirculation-invalid spans, or thermal/boundary tuning.",
            "blocker_effect": "does_not_close_f6_blocker_until_validation_passes",
        },
        {
            "candidate_id": "F3_shah_apparent",
            "candidate_type": "production_baseline",
            "current_evidence": "Current production friction baseline; literature-backed developing-flow apparent friction.",
            "decision": "retain_as_baseline",
            "why": "Provides the comparison baseline for F6; not enough by itself to fix forward mdot.",
            "preconditions": "None.",
            "primary_acceptance_metric": "F6 must beat this on pressure-loss validation, not just mdot.",
            "secondary_mdot_guardrail": "F6 must not degrade mdot relative to this baseline.",
            "rejection_rule": "Do not replace F3 with F6 unless validation improves.",
            "blocker_effect": "baseline_not_blocker_closing",
        },
        {
            "candidate_id": "H1_localized_named_loss_reset",
            "candidate_type": "localized_loss_reset_bundle",
            "current_evidence": "Aggregate H1 improves mdot, but localized fixed-K-only scoring worsens F1 mean mdot error by 6.78%.",
            "decision": "retire_current_h1_as_proxy_only",
            "why": "The faithful path needs reset/development and component/cluster separation that are not implemented/admitted today.",
            "preconditions": "A future H1 revival needs first-class reset terms, centerline tap lengths, component/cluster K separation, and no-refit validation.",
            "primary_acceptance_metric": "Train improves and validation/holdout do not worsen without aggregate K.",
            "secondary_mdot_guardrail": "Must improve mdot direction without imposed thermal fitting.",
            "rejection_rule": "Reject localized-fixed-K-only and branch-apparent-only forms as final closures.",
            "blocker_effect": "proxy_retired_not_forward_v1_admitted",
        },
    ]

    source_rows = [
        {"source_id": "h1_scorecard", "path": str(H1_SCORECARD_README.relative_to(REPO_ROOT)), "role": "aggregate H1 directional screen"},
        {"source_id": "localized_fixed_k", "path": str(LOCALIZED_SUMMARY.relative_to(REPO_ROOT)), "role": "faithful localized fixed-K screen result"},
        {"source_id": "correction_candidates", "path": str(CORRECTION_README.relative_to(REPO_ROOT)), "role": "ranked hydraulic candidate context"},
        {"source_id": "named_losses", "path": str(NAMED_LOSSES.relative_to(REPO_ROOT)), "role": "component/cluster/branch-apparent candidate rows"},
        {"source_id": "reset_map", "path": str(RESET_MAP.relative_to(REPO_ROOT)), "role": "reset/development evidence"},
        {"source_id": "f6_screen", "path": str(F6_SCORECARD.relative_to(REPO_ROOT)), "role": "F6 current blocker state"},
        {"source_id": "blockers", "path": str(BLOCKERS.relative_to(REPO_ROOT)), "role": "open blocker register"},
    ]

    _write_csv(
        output_dir / "h1_faithful_implementation_gap_table.csv",
        [
            "gap_id",
            "closure_piece",
            "current_evidence",
            "faithful_requirement",
            "gap_type",
            "current_status",
            "blocking_detail",
            "required_next_action",
            "acceptance_gate",
        ],
        h1_gap_rows,
    )
    _write_csv(
        output_dir / "f6_candidate_decision_table.csv",
        [
            "candidate_id",
            "candidate_type",
            "current_evidence",
            "decision",
            "why",
            "preconditions",
            "primary_acceptance_metric",
            "secondary_mdot_guardrail",
            "rejection_rule",
            "blocker_effect",
        ],
        f6_decision_rows,
    )
    _write_csv(output_dir / "source_manifest.csv", ["source_id", "path", "role"], source_rows)

    summary = {
        "task_id": "AGENT-333",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "native_solver_outputs_mutated": False,
        "thermal_fit_used": False,
        "global_friction_multiplier_exported": False,
        "h1_decision": "retire_current_h1_as_proxy_only",
        "h1_reason": "aggregate H1 improves mdot but localized fixed-K-only scoring fails and reset/development is not first-class/admitted",
        "next_hydraulic_candidate": "F6_phi_re",
        "f6_decision": "next_bounded_candidate_after_admission_preconditions",
        "recommended_next_run_or_edit": "Do not launch another H1 fixed-K run; implement/admit reset/development before H1 revival, otherwise run a bounded F6 screen only after corrected-Q or equivalent Re-variation rows are admitted.",
        "outputs": [
            "h1_faithful_implementation_gap_table.csv",
            "f6_candidate_decision_table.csv",
            "source_manifest.csv",
            "summary.json",
            "README.md",
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = f"""---
provenance:
  - {H1_SCORECARD_README.relative_to(REPO_ROOT)}
  - {LOCALIZED_SUMMARY.relative_to(REPO_ROOT)}
  - {CORRECTION_README.relative_to(REPO_ROOT)}
  - {F6_SCORECARD.relative_to(REPO_ROOT)}
tags: [hydraulics, h1, f6, friction, pressure-ledger]
task: AGENT-333
date: 2026-07-14
role: Hydraulics / Implementer / Tester / Writer
status: complete
---
# H1 Faithful Gap And F6 Decision

## Decision

Retire the current H1 forms as proxy-only. The aggregate H1 proxy remains useful
diagnostic evidence that added hydraulic resistance can move mdot toward CFD,
but it is not a faithful closure. The localized fixed-K-only follow-up failed
the directional screen, and the missing physics is exactly the part H1 was meant
to represent: reset/redevelopment plus separated component/cluster losses.

The next hydraulic candidate is `F6_phi_re` as a bounded screen, not a validated
closure. It should run only after corrected-Q or equivalent Re-variation rows
are terminal/admitted, with no thermal fitting, no recirculation-invalid fit
rows, and no global multiplier.

## Recommended Next Hydraulic Run/Edit

Do not launch another H1 fixed-K run. The faithful-H1 path first needs a
reset/development input table and diagnostics that keep component K, cluster K,
branch-apparent loss, straight friction, and recirculation diagnostics separate.
If that edit is not being taken immediately, the next hydraulic test should be a
bounded F6/Re screen under the acceptance criteria in
`f6_candidate_decision_table.csv`.

## Outputs

- `h1_faithful_implementation_gap_table.csv`
- `f6_candidate_decision_table.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

- Thermal fitting used: `false`.
- Native CFD outputs mutated: `false`.
- Global friction multiplier exported: `false`.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build_package(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
