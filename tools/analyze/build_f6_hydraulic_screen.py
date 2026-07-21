#!/usr/bin/env python3
"""Build a bounded F6 hydraulic-readiness screen.

This script does not refit thermal parameters and does not mutate CFD outputs.
It summarizes whether the already-implemented Fluid ``F6_phi_re`` closure is
ready to close the open friction-Re blocker, using the current hydraulic gate
and H1 mdot scorecard as source evidence.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_f6_hydraulic_screen"
HYDRAULIC_GATE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate"
CORRECTION_CANDIDATE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates"
H1_SCORECARD_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard"
FRICTION_CLOSURE_PATH = (
    REPO_ROOT.parent
    / "cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py"
)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    row_list = list(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in row_list:
            writer.writerow(row)


def _h1_f1_summary(rows: List[Dict[str, str]]) -> Dict[str, float]:
    selected = [row for row in rows if row["base_variant_id"] == "F1_heater_only"]
    if not selected:
        return {
            "mean_baseline_error_kg_s": 0.0,
            "mean_h1_error_kg_s": 0.0,
            "mean_error_reduction_pct": 0.0,
            "n_rows": 0.0,
        }
    baseline = [float(row["baseline_mdot_error_vs_cfd_kg_s"]) for row in selected]
    h1 = [float(row["h1_mdot_error_vs_cfd_kg_s"]) for row in selected]
    reduction = [float(row["mdot_error_reduction_pct"]) for row in selected]
    return {
        "mean_baseline_error_kg_s": sum(baseline) / len(baseline),
        "mean_h1_error_kg_s": sum(h1) / len(h1),
        "mean_error_reduction_pct": sum(reduction) / len(reduction),
        "n_rows": float(len(selected)),
    }


def _count_gate_rows(rows: List[Dict[str, str]], gate_prefix: str) -> int:
    return sum(1 for row in rows if row.get("gate_decision", "").startswith(gate_prefix))


def build_f6_hydraulic_screen(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        output_label = str(output_dir.relative_to(REPO_ROOT))
    except ValueError:
        output_label = str(output_dir)

    gate_rows = _read_csv(HYDRAULIC_GATE_DIR / "hydraulic_fit_safety_gate.csv")
    candidate_rows = _read_csv(CORRECTION_CANDIDATE_DIR / "candidate_rankings.csv")
    h1_rows = _read_csv(H1_SCORECARD_DIR / "h1_hydraulic_scorecard.csv")
    h1_summary = _h1_f1_summary(h1_rows)

    friction_text = FRICTION_CLOSURE_PATH.read_text(encoding="utf-8") if FRICTION_CLOSURE_PATH.exists() else ""
    f6_code_available = "def dp_F6_phi_re" in friction_text and '"F6_phi_re"' in friction_text

    raw_fit_safe_count = _count_gate_rows(gate_rows, "fit_safe_but")
    diagnostic_momentum_count = _count_gate_rows(gate_rows, "fit_safe_momentum_corrected")
    publication_ready_count = sum(1 for row in gate_rows if row.get("gci_publication_ready", "").lower() == "yes")

    evidence_rows = [
        {
            "evidence_id": "raw_fit_safe_pressure_gradient",
            "evidence_class": "training_guardrail",
            "row_count": raw_fit_safe_count,
            "allowed_use": "may_screen_or_calibrate_hydraulic_terms_with_mesh_caveat",
            "limitation": "GCI publication readiness is false; only two raw spans are fit-safe.",
        },
        {
            "evidence_id": "momentum_corrected_friction",
            "evidence_class": "diagnostic_only",
            "row_count": diagnostic_momentum_count,
            "allowed_use": "may_inform_debuoyed_friction_or_profile_terms_not_raw_pressure_gradient_fit",
            "limitation": "Debuoyed/profile evidence is not raw pressure-gradient fitting evidence.",
        },
        {
            "evidence_id": "h1_mdot_screen_f1_heater_only",
            "evidence_class": "forward_v1_diagnostic_unblocker",
            "row_count": int(h1_summary["n_rows"]),
            "allowed_use": "hydraulic-only mdot movement scorecard; no thermal fitting",
            "limitation": "H1 is an aggregate localized-loss proxy until Fluid localized-loss metadata is used in a full solve_case campaign.",
        },
        {
            "evidence_id": "corrected_q_admission",
            "evidence_class": "blocked_validation_expansion",
            "row_count": 0,
            "allowed_use": "none_for_f6_refit_yet",
            "limitation": "Corrected-Q rows are not admitted for F6 coefficient revision in the current gate state.",
        },
    ]

    f6_decision = (
        "screen_only_keep_blocker_open"
        if f6_code_available and publication_ready_count == 0
        else "not_available_or_unassessed"
    )
    scorecard_rows = [
        {
            "candidate_id": "F6_phi_re",
            "candidate_class": "friction_re_multiplier",
            "uses_global_friction_multiplier": "false",
            "uses_thermal_fit": "false",
            "code_available": str(f6_code_available).lower(),
            "raw_fit_safe_training_rows": raw_fit_safe_count,
            "diagnostic_momentum_rows": diagnostic_momentum_count,
            "publication_ready_gci_rows": publication_ready_count,
            "corrected_q_admitted_rows": 0,
            "mdot_forward_score_available": "false",
            "decision": f6_decision,
            "blocker_status_after_screen": "open",
            "reason": "F6 exists in Fluid, but current evidence lacks corrected-Q/held-out admission and publication-ready GCI support.",
        },
        {
            "candidate_id": "H1_localized_named_loss_and_reset_bundle",
            "candidate_class": "localized_named_loss_reset_proxy",
            "uses_global_friction_multiplier": "false",
            "uses_thermal_fit": "false",
            "code_available": "bridge_now_supported_by_localized_fixed_k_config",
            "raw_fit_safe_training_rows": raw_fit_safe_count,
            "diagnostic_momentum_rows": diagnostic_momentum_count,
            "publication_ready_gci_rows": publication_ready_count,
            "corrected_q_admitted_rows": 0,
            "mdot_forward_score_available": "true",
            "decision": "unblocks_forward_v1_diagnostic_scorecard_only",
            "blocker_status_after_screen": "partially_moved_not_closed",
            "reason": (
                "F1 heater-only H1 proxy reduces mean mdot error from "
                f"{h1_summary['mean_baseline_error_kg_s']:.7f} to {h1_summary['mean_h1_error_kg_s']:.7f} kg/s "
                f"({h1_summary['mean_error_reduction_pct']:.2f}% mean reduction) without thermal fitting."
            ),
        },
    ]

    source_rows = [
        {
            "source_id": "hydraulic_fit_safety_gate",
            "path": str(HYDRAULIC_GATE_DIR / "hydraulic_fit_safety_gate.csv"),
            "role": "fit-safe and diagnostic hydraulic evidence boundaries",
        },
        {
            "source_id": "candidate_rankings",
            "path": str(CORRECTION_CANDIDATE_DIR / "candidate_rankings.csv"),
            "role": "H1/H2/H3/H4 candidate separation and global multiplier rejection",
        },
        {
            "source_id": "h1_hydraulic_scorecard",
            "path": str(H1_SCORECARD_DIR / "h1_hydraulic_scorecard.csv"),
            "role": "hydraulic-only mdot movement without thermal fitting",
        },
        {
            "source_id": "fluid_friction_closures",
            "path": str(FRICTION_CLOSURE_PATH),
            "role": "checks whether F6_phi_re implementation exists",
        },
    ]

    _write_csv(
        output_dir / "f6_evidence_rows.csv",
        ["evidence_id", "evidence_class", "row_count", "allowed_use", "limitation"],
        evidence_rows,
    )
    _write_csv(
        output_dir / "f6_hydraulic_scorecard.csv",
        [
            "candidate_id",
            "candidate_class",
            "uses_global_friction_multiplier",
            "uses_thermal_fit",
            "code_available",
            "raw_fit_safe_training_rows",
            "diagnostic_momentum_rows",
            "publication_ready_gci_rows",
            "corrected_q_admitted_rows",
            "mdot_forward_score_available",
            "decision",
            "blocker_status_after_screen",
            "reason",
        ],
        scorecard_rows,
    )
    _write_csv(output_dir / "source_manifest.csv", ["source_id", "path", "role"], source_rows)

    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    summary = {
        "task_id": "AGENT-318",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": output_label,
        "native_solver_outputs_mutated": False,
        "thermal_fit_used": False,
        "global_friction_multiplier_exported": False,
        "f6_code_available": f6_code_available,
        "f6_decision": f6_decision,
        "f6_blocker_status": "open",
        "h1_decision": scorecard_rows[1]["decision"],
        "h1_mean_baseline_mdot_error_kg_s": h1_summary["mean_baseline_error_kg_s"],
        "h1_mean_mdot_error_kg_s": h1_summary["mean_h1_error_kg_s"],
        "h1_mean_error_reduction_pct": h1_summary["mean_error_reduction_pct"],
        "raw_fit_safe_training_rows": raw_fit_safe_count,
        "diagnostic_momentum_rows": diagnostic_momentum_count,
        "publication_ready_gci_rows": publication_ready_count,
        "best_existing_candidate": candidate_by_id.get("H1_localized_named_loss_and_reset_bundle", {}).get("candidate_name", ""),
        "outputs": [
            "f6_evidence_rows.csv",
            "f6_hydraulic_scorecard.csv",
            "source_manifest.csv",
            "summary.json",
            "README.md",
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = f"""---
provenance:
  - {HYDRAULIC_GATE_DIR.relative_to(REPO_ROOT)}/hydraulic_fit_safety_gate.csv
  - {CORRECTION_CANDIDATE_DIR.relative_to(REPO_ROOT)}/candidate_rankings.csv
  - {H1_SCORECARD_DIR.relative_to(REPO_ROOT)}/h1_hydraulic_scorecard.csv
tags: [hydraulics, friction, f6, mdot, forward-v1]
task: AGENT-318
date: 2026-07-14
role: Implementer/Tester/Writer
status: complete
---
# F6 Hydraulic Screen

## Decision

`F6_phi_re` remains a candidate screen, not a blocker-closing validated
hydraulic closure. The implementation exists in Fluid, but the current evidence
still lacks corrected-Q/held-out admission and has zero publication-ready GCI
rows for the hydraulic fit gate.

H1 localized named-loss/reset remains the hydraulic path that improves mdot
without thermal fitting. For the `F1_heater_only` rows, mean mdot error drops
from `{h1_summary['mean_baseline_error_kg_s']:.7f}` to
`{h1_summary['mean_h1_error_kg_s']:.7f}` kg/s, a
`{h1_summary['mean_error_reduction_pct']:.2f}%` mean reduction. This is enough
to unblock forward-v1 diagnostic scorecard refresh, but not enough to publish a
final localized closure.

## Boundaries

- No native CFD solver outputs were mutated.
- No thermal parameter fitting was used.
- No one global friction multiplier was exported as a model correction.
- Raw pressure-gradient fit-safe rows, component/localized K, cluster/reset
  effects, branch-apparent loss, and recirculation limitations remain separate.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    return summary


def main() -> None:
    summary = build_f6_hydraulic_screen()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
