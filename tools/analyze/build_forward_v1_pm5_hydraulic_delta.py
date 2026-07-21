#!/usr/bin/env python3
"""Integrate completed +/-5Q and hydraulic tap-refresh evidence for forward-v1."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta"

PM5_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/summary.json"
PM5_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv"
PM5_HEAT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_heat_role_reduction.csv"
PM5_QUEUE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_forward_gate_queue.csv"
HYD_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/summary.json"
HYD_K_TABLE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv"
HYD_H1 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/h1_faithful_readiness_after_tap_refresh.csv"
FORWARD_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/summary.json"
FORWARD_DASHBOARD = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/summary.json"

DELTA_COLUMNS = [
    "delta_id",
    "lane",
    "evidence_landed",
    "forward_v1_effect",
    "admitted_now",
    "still_blocked_by",
    "next_required_artifact",
    "do_not_claim",
    "source_artifact",
]
THESIS_COLUMNS = [
    "table_id",
    "claim",
    "status",
    "numbers_to_cite",
    "interpretation",
    "limits",
    "source_artifact",
]
ACTION_COLUMNS = [
    "priority",
    "action_id",
    "owner_lane",
    "trigger",
    "required_inputs",
    "output",
    "acceptance",
]
MANIFEST_COLUMNS = ["artifact", "role", "path"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def min_max(rows: list[dict[str, str]], column: str) -> tuple[float, float]:
    values = [float(row[column]) for row in rows if row.get(column) not in {"", None}]
    return min(values), max(values)


def build_delta_rows() -> list[dict[str, Any]]:
    pm5_summary = read_json(PM5_SUMMARY)
    hyd_summary = read_json(HYD_SUMMARY)
    forward_summary = read_json(FORWARD_SUMMARY)
    return [
        {
            "delta_id": "pm5_terminal_harvest",
            "lane": "cfd_admission",
            "evidence_landed": f"{pm5_summary['harvest_rows']} +/-5Q rows terminal-harvested; {pm5_summary['closure_fit_admissible_terminal_gate_rows']} closure-fit-admissible terminal-gate rows",
            "forward_v1_effect": "Improves perturbation-family evidence but does not expand independent train/validation/holdout rows.",
            "admitted_now": "train-family or holdout-family sensitivity/admission evidence only",
            "still_blocked_by": "dated perturbation split policy plus BC-role and operating-point admission refresh",
            "next_required_artifact": "perturbation_split_policy_update.csv",
            "do_not_claim": "Do not add +/-5Q rows as independent training rows.",
            "source_artifact": rel(PM5_SUMMARY),
        },
        {
            "delta_id": "pm5_boundary_heat_targets",
            "lane": "boundary_hx",
            "evidence_landed": "Final-window heat-role reductions landed for four +/-5Q rows.",
            "forward_v1_effect": "Provides score targets for later setup-only boundary/HX scoring.",
            "admitted_now": "diagnostic/score targets only",
            "still_blocked_by": "Fluid setup-only boundary/HX outputs and runtime-input audit",
            "next_required_artifact": "setup_only_boundary_hx_outputs.csv",
            "do_not_claim": "Do not use CFD cooler duty or realized wallHeatFlux as predictive runtime inputs.",
            "source_artifact": rel(PM5_HEAT),
        },
        {
            "delta_id": "pm5_f6_onset_candidates",
            "lane": "hydraulic_or_upcomer_onset",
            "evidence_landed": "+/-5Q rows can become Re-variation/onset candidates after metric extraction.",
            "forward_v1_effect": "Potential future input for F6 and upcomer onset, not current closure evidence.",
            "admitted_now": "candidate evidence pending pressure/upcomer metric extraction",
            "still_blocked_by": "matched pressure/upcomer metrics and admission gate",
            "next_required_artifact": "pm5_corrected_q_matched_pressure_upcomer_metrics.csv",
            "do_not_claim": "Do not infer F6 or onset from terminal harvest alone.",
            "source_artifact": rel(PM5_QUEUE),
        },
        {
            "delta_id": "hyd_tap_centerline_refresh",
            "lane": "hydraulics",
            "evidence_landed": f"{hyd_summary['centerline_resolved_rows']} tap rows resolved from existing mesh centerlines; {hyd_summary['centerline_blocked_rows']} still blocked",
            "forward_v1_effect": "Removes dz-proxy ambiguity for preserved rows but does not admit component/cluster K.",
            "admitted_now": "diagnostic/admission refresh only",
            "still_blocked_by": "mesh/GCI, raw two-tap extraction for connector rows, reset/development API, admitted pressure evidence",
            "next_required_artifact": "f6_phi_re_hydraulic_scorecard.csv or reset_development_pressure_scorecard.csv",
            "do_not_claim": "Do not fit component/cluster K or launch faithful H1 yet.",
            "source_artifact": rel(HYD_SUMMARY),
        },
        {
            "delta_id": "forward_v1_status_after_delta",
            "lane": "forward_v1",
            "evidence_landed": "Completed +/-5Q terminal-harvest delta and hydraulic tap-length delta integrated.",
            "forward_v1_effect": forward_summary["final_forward_v1_status"],
            "admitted_now": "current Salt2/Salt3/Salt4 split plus diagnostic/proxy/perturbation-family evidence",
            "still_blocked_by": f"{forward_summary['blocking_gate_count']} forward-v1 blocking gates remain",
            "next_required_artifact": "forward_v1_residual_attribution_scorecard.csv after upstream gates land",
            "do_not_claim": "Do not call final forward-v1 admitted.",
            "source_artifact": rel(FORWARD_SUMMARY),
        },
    ]


def build_thesis_rows() -> list[dict[str, Any]]:
    pm5_rows = read_csv(PM5_MATRIX)
    heat_rows = read_csv(PM5_HEAT)
    hyd_summary = read_json(HYD_SUMMARY)
    q_ratios = sorted({row["q_ratio"] for row in pm5_rows})
    cooler_min, cooler_max = min_max(heat_rows, "cooling_branch_total_removal_mean_W")
    return [
        {
            "table_id": "pm5_terminal_harvest",
            "claim": "+/-5Q corrected-Q rows are terminal-harvested perturbation evidence.",
            "status": "landed_but_not_training_expansion",
            "numbers_to_cite": f"rows={len(pm5_rows)}; q_ratios={','.join(q_ratios)}; independent_training_expansion_rows=0",
            "interpretation": "The perturbation family can support sensitivity/admission discussion without leaking extra training rows.",
            "limits": "Needs dated perturbation split policy before independent train/validation/holdout expansion.",
            "source_artifact": rel(PM5_MATRIX),
        },
        {
            "table_id": "pm5_heat_targets",
            "claim": "+/-5Q heat-role reductions provide boundary/HX score targets.",
            "status": "diagnostic_score_targets",
            "numbers_to_cite": f"cooling_branch_total_removal_mean_W_range={cooler_min:.3f}..{cooler_max:.3f}",
            "interpretation": "Useful for later setup-only HX/BC scoring once runtime-input guardrails pass.",
            "limits": "WallHeatFlux/cooler duty are not runtime predictive inputs.",
            "source_artifact": rel(PM5_HEAT),
        },
        {
            "table_id": "tap_length_refresh",
            "claim": "Existing mesh-centerline station artifacts improved hydraulic tap-length evidence.",
            "status": "diagnostic_admission_refresh",
            "numbers_to_cite": (
                f"centerline_resolved_rows={hyd_summary['centerline_resolved_rows']}; "
                f"centerline_blocked_rows={hyd_summary['centerline_blocked_rows']}; "
                f"component_fit_admissible_rows={hyd_summary['component_fit_admissible_rows']}"
            ),
            "interpretation": "Hydraulic evidence is cleaner, but H1 component/cluster K remains unfit.",
            "limits": "No component/cluster K fit and no global multiplier.",
            "source_artifact": rel(HYD_SUMMARY),
        },
    ]


def build_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "priority": "P1",
            "action_id": "pm5_matched_pressure_upcomer_metrics",
            "owner_lane": "therm-reconstr / hydraulics",
            "trigger": "AGENT-357 +/-5Q matched-plane/pressure job lands",
            "required_inputs": "matched pressure/upcomer metrics for salt2/salt4 +/-5Q terminal-harvest rows",
            "output": "pm5_corrected_q_matched_pressure_upcomer_metrics.csv",
            "acceptance": "Rows have source paths, time windows, metric admission status, and no runtime predictive leakage.",
        },
        {
            "priority": "P2",
            "action_id": "perturbation_split_policy",
            "owner_lane": "cfd-pp / forward-pred",
            "trigger": "terminal +/-5Q rows and metric extraction are available",
            "required_inputs": "PM5 split matrix, BC-role reductions, metric admission status",
            "output": "perturbation_split_policy_update.csv",
            "acceptance": "Defines whether perturbation-family evidence is train-family sensitivity, validation-only, holdout-family, or excluded.",
        },
        {
            "priority": "P3",
            "action_id": "f6_score_after_admitted_re_variation",
            "owner_lane": "hydraulics",
            "trigger": "admitted pressure/Re-variation rows exist",
            "required_inputs": "admitted +/-5Q or +/-10Q pressure-loss rows, current split policy",
            "output": "f6_phi_re_hydraulic_scorecard.csv",
            "acceptance": "Pressure-loss primary score and mdot guardrail; no thermal fitting.",
        },
        {
            "priority": "P4",
            "action_id": "boundary_hx_score_targets",
            "owner_lane": "BC-modeling / forward-pred",
            "trigger": "Fluid setup-only boundary/HX API outputs land",
            "required_inputs": "PM5 heat-role targets and setup-only modeled boundary/HX outputs",
            "output": "setup_only_boundary_hx_outputs.csv",
            "acceptance": "Scores heat residuals without realized wallHeatFlux or cooler duty runtime inputs.",
        },
        {
            "priority": "P5",
            "action_id": "forward_v1_delta_refresh",
            "owner_lane": "forward-pred",
            "trigger": "one upstream gate-moving action above lands",
            "required_inputs": "result-intake-compatible cfd/hydraulic/boundary/thermal rows",
            "output": "forward_v1_residual_attribution_scorecard.csv",
            "acceptance": "Keeps final no-go unless all blocking gates pass.",
        },
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PM5_SUMMARY)}
  - {rel(HYD_SUMMARY)}
  - {rel(FORWARD_SUMMARY)}
tags: [forward-model, forward-v1, corrected-q, hydraulics, thesis-table]
related:
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-362
date: 2026-07-14
role: Forward-pred/Scientific-closure/Implementer/Tester/Writer
type: work_product
status: complete
---
# Forward-v1 +/-5Q / Hydraulic Delta

## Decision

This package integrates two completed gate-moving evidence slices into the
forward-v1 ledger. The +/-5Q corrected-Q harvest adds terminal perturbation
evidence and heat-role score targets. The hydraulic tap refresh resolves many
tap lengths. Neither slice admits final forward-v1 or independent new training
rows today.

Final forward-v1 remains `{summary['final_forward_v1_status']}`.

## Main Results

- +/-5Q terminal harvested rows: `{summary['pm5_harvest_rows']}`.
- +/-5Q independent training expansion rows: `{summary['independent_training_expansion_rows']}`.
- Hydraulic centerline rows resolved: `{summary['centerline_resolved_rows']}`.
- Fit-admissible component/cluster K rows: `{summary['component_fit_admissible_rows']}`.

## Guardrails

Do not add +/-5Q rows as independent training rows before a dated perturbation
split policy. Do not use CFD cooler duty or realized wallHeatFlux as predictive
runtime inputs. Do not fit component/cluster K, F6, or internal Nu from these
delta rows until the required metric/admission gates land.

## Files

- `forward_v1_gate_delta_after_pm5_hydraulic.csv`
- `thesis_pm5_hydraulic_progress_table.csv`
- `next_gate_actions_after_pm5_hydraulic.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pm5 = read_json(PM5_SUMMARY)
    hyd = read_json(HYD_SUMMARY)
    forward = read_json(FORWARD_SUMMARY)
    deltas = build_delta_rows()
    thesis = build_thesis_rows()
    actions = build_action_rows()
    write_csv(output_dir / "forward_v1_gate_delta_after_pm5_hydraulic.csv", deltas, DELTA_COLUMNS)
    write_csv(output_dir / "thesis_pm5_hydraulic_progress_table.csv", thesis, THESIS_COLUMNS)
    write_csv(output_dir / "next_gate_actions_after_pm5_hydraulic.csv", actions, ACTION_COLUMNS)
    write_csv(
        output_dir / "source_manifest.csv",
        [
            {"artifact": "pm5_summary", "role": "source", "path": rel(PM5_SUMMARY)},
            {"artifact": "pm5_split_matrix", "role": "source", "path": rel(PM5_MATRIX)},
            {"artifact": "pm5_heat_role_reduction", "role": "source", "path": rel(PM5_HEAT)},
            {"artifact": "pm5_forward_queue", "role": "source", "path": rel(PM5_QUEUE)},
            {"artifact": "hydraulic_tap_summary", "role": "source", "path": rel(HYD_SUMMARY)},
            {"artifact": "hydraulic_k_table", "role": "source", "path": rel(HYD_K_TABLE)},
            {"artifact": "hydraulic_h1_readiness", "role": "source", "path": rel(HYD_H1)},
            {"artifact": "forward_summary", "role": "source", "path": rel(FORWARD_SUMMARY)},
            {"artifact": "forward_dashboard_summary", "role": "source", "path": rel(FORWARD_DASHBOARD)},
        ],
        MANIFEST_COLUMNS,
    )
    summary = {
        "task": "AGENT-362",
        "generated_at_utc": utc_now(),
        "final_forward_v1_status": forward["final_forward_v1_status"],
        "pm5_harvest_rows": int(pm5["harvest_rows"]),
        "pm5_closure_fit_admissible_terminal_gate_rows": int(pm5["closure_fit_admissible_terminal_gate_rows"]),
        "independent_training_expansion_rows": int(pm5["independent_training_expansion_rows"]),
        "centerline_resolved_rows": int(hyd["centerline_resolved_rows"]),
        "centerline_blocked_rows": int(hyd["centerline_blocked_rows"]),
        "component_fit_admissible_rows": int(hyd["component_fit_admissible_rows"]),
        "h1_faithful_launchable": bool(hyd["h1_faithful_launchable"]),
        "forward_v1_admitted": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "external_fluid_modified": False,
        "scheduler_action_taken": False,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
