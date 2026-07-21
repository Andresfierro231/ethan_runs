#!/usr/bin/env python3
"""Build AGENT-299 predictive parallel execution integration package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DATE_DIR = ROOT / "work_products/2026-07/2026-07-13"
OUT_DIR = DATE_DIR / "2026-07-13_predictive_parallel_execution_coordination"

SOLVE_DIR = DATE_DIR / "2026-07-13_predictive_forward_v0_solve_case_confirmation"
HYD_DIR = DATE_DIR / "2026-07-13_predictive_hydraulic_correction_candidates"
SENSOR_DIR = DATE_DIR / "2026-07-13_predictive_sensor_map_contract"
SCORECARD_DIR = DATE_DIR / "2026-07-13_predictive_endtoend_scorecard_precursor"
EXTERNAL_BC_DIR = DATE_DIR / "2026-07-13_predictive_external_bc_implementation_wave"
THERMAL_GATE_DIR = DATE_DIR / "2026-07-13_thermal_mesh_gate"


INTEGRATION_COLUMNS = [
    "lane_id",
    "phase",
    "status",
    "admitted_use_now",
    "key_result",
    "blocks",
    "next_action",
    "source_artifact",
]
H1_COLUMNS = [
    "case_id",
    "variant_id",
    "row_status",
    "mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_ratio_model_to_cfd",
    "required_resistance_multiplier",
    "equivalent_added_loss_at_model_root_Pa",
    "thermal_fit_used",
    "h1_candidate_id",
    "h1_corrected_mdot_kg_s",
    "h1_corrected_mdot_error_vs_cfd_kg_s",
    "interpretation",
]
SENSOR_COLUMNS = [
    "case_id",
    "variant_id",
    "sensor_source",
    "sensor",
    "kind",
    "score_status_current",
    "score_included_current",
    "predicted_K",
    "target_K",
    "error_K",
    "prediction_source_segment",
    "prediction_source_fraction",
    "blocker_or_caveat",
]
DECISION_COLUMNS = [
    "decision_id",
    "claim_level",
    "decision",
    "evidence",
    "next_gate",
]
H1_FEASIBILITY_COLUMNS = [
    "item",
    "status",
    "implementation_path",
    "scientific_label",
    "guardrail",
]
QUEUE_COLUMNS = [
    "task_id",
    "priority",
    "parallel_group",
    "owner_role",
    "write_scope",
    "objective",
    "acceptance_signal",
    "blocked_by",
]
MANIFEST_COLUMNS = ["artifact_id", "path", "status", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finite_text(value: str) -> bool:
    return num(value) is not None


def integration_rows() -> list[dict[str, Any]]:
    solve_summary = read_json(SOLVE_DIR / "comparison_summary.json")
    solve_full_summary = read_json(SOLVE_DIR / "solve_case_full/summary.json")
    hyd_summary = read_json(HYD_DIR / "decision_summary.json")
    sensor_summary = read_json(SENSOR_DIR / "summary.json")
    score_summary = read_json(SCORECARD_DIR / "summary.json")
    external_summary = read_json(EXTERNAL_BC_DIR / "summary.json")
    thermal_summary = read_json(THERMAL_GATE_DIR / "summary.json")

    solve_status = solve_summary.get("overall_status", "missing")
    hyd_best = hyd_summary.get("best_candidate_id", "missing")
    sensor_claim = sensor_summary.get("sensor_temperature_score_claim", "missing")
    score_status = score_summary.get("overall_status", "missing")
    external_rows = (external_summary.get("row_counts") or {}).get("external_boundary_rows", "missing")
    thermal_fit = thermal_summary.get("fit_admissible_count", "0")

    return [
        {
            "lane_id": "solve_case_confirmation",
            "phase": "phase_1_harvest",
            "status": f"complete_{solve_status}",
            "admitted_use_now": "authoritative_forward_v0_confirmation",
            "key_result": (
                f"{solve_summary.get('n_pass_rows', 0)}/{solve_summary.get('n_comparison_rows', 0)} rows pass; "
                f"max mdot delta {solve_summary.get('max_abs_mdot_delta_kg_s', '')} kg/s; "
                f"solve_case F1 mean mdot error {variant_metric(solve_full_summary, 'F1_heater_only', 'mean_mdot_error_vs_cfd_kg_s')} kg/s"
            ),
            "blocks": "does_not_block_fast_scan_screening_but_solve_case_is_authoritative",
            "next_action": "use solve_case rows for claims; fast_scan remains screening proxy inside documented bands",
            "source_artifact": rel(SOLVE_DIR / "solve_case_vs_fast_scan_comparison.csv"),
        },
        {
            "lane_id": "hydraulic_correction_candidates",
            "phase": "phase_1_harvest",
            "status": "complete_candidate_ranked",
            "admitted_use_now": "rerun_candidate_only_no_closure_claim",
            "key_result": f"best={hyd_best}; mean required resistance multiplier={hyd_summary.get('mean_required_resistance_multiplier', '')}",
            "blocks": "blocks_end_to_end_claim_until_corrected_rerun_improves_mdot",
            "next_action": "run H1 localized named-loss/reset bundle in a bounded forward rerun",
            "source_artifact": rel(HYD_DIR / "candidate_rankings.csv"),
        },
        {
            "lane_id": "sensor_map_contract",
            "phase": "phase_1_harvest",
            "status": "artifact_present_closeout_missing",
            "admitted_use_now": "secondary_provisional_sensor_scores_only",
            "key_result": (
                f"{sensor_summary.get('n_provisional_diagnostic_score_allowed', '')} sensors provisionally allowed; "
                f"blocked={','.join(sensor_summary.get('blocked_sensor_scores', []))}"
            ),
            "blocks": "blocks_thesis_grade_exact_sensor_claims",
            "next_action": "complete worker closeout; score only provisional finite post-solve rows",
            "source_artifact": rel(SENSOR_DIR / "sensor_map_contract.csv"),
        },
        {
            "lane_id": "scorecard_precursor",
            "phase": "phase_1_refresh",
            "status": "stale_requires_refresh",
            "admitted_use_now": "historical_precursor_only",
            "key_result": f"previous overall_status={score_status}; predates AGENT-300 completion and solve_case harvest",
            "blocks": "blocks_final_forward_v1_scorecard",
            "next_action": "regenerate after H1 rerun or publish refreshed precursor from this AGENT-299 package",
            "source_artifact": rel(SCORECARD_DIR / "summary.json"),
        },
        {
            "lane_id": "external_boundary_api",
            "phase": "phase_2_parallel",
            "status": "contract_ready_source_not_modified",
            "admitted_use_now": "setup_dictionary_and_radiation_policy",
            "key_result": f"{external_rows} external boundary rows ready; Fluid API still pending",
            "blocks": "blocks_external_boundary_table_runtime_mode",
            "next_action": "claim writable Fluid row or produce patch package only",
            "source_artifact": rel(EXTERNAL_BC_DIR / "fluid_external_boundary_patch_plan.md"),
        },
        {
            "lane_id": "thermal_mesh_gate",
            "phase": "phase_2_guardrail",
            "status": "blocked_no_thermal_fit",
            "admitted_use_now": "blocker_and_diagnostic_context",
            "key_result": f"fit_admissible_count={thermal_fit}; no UA/HTC/Nu closure admitted",
            "blocks": "blocks_thermal_closure_fit",
            "next_action": "resolve sign, heat-balance, downcomer, and mesh-family gates before thermal fitting",
            "source_artifact": rel(THERMAL_GATE_DIR / "summary.json"),
        },
    ]


def variant_metric(summary: dict[str, Any], variant_id: str, metric: str) -> Any:
    for row in summary.get("variant_summary", []):
        if row.get("variant_id") == variant_id:
            return row.get(metric, "")
    return ""


def h1_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(HYD_DIR / "mdot_resistance_scaling.csv"):
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "variant_id": row.get("variant_id", ""),
                "row_status": "screening_input_ready_h1_not_rerun",
                "mdot_kg_s": row.get("mdot_kg_s", ""),
                "cfd_mdot_kg_s": row.get("cfd_mdot_kg_s", ""),
                "mdot_ratio_model_to_cfd": row.get("mdot_ratio_model_to_cfd", ""),
                "required_resistance_multiplier": row.get("required_resistance_multiplier", ""),
                "equivalent_added_loss_at_model_root_Pa": row.get("equivalent_added_loss_at_model_root_Pa", ""),
                "thermal_fit_used": "no",
                "h1_candidate_id": "H1_localized_named_loss_and_reset_bundle",
                "h1_corrected_mdot_kg_s": "",
                "h1_corrected_mdot_error_vs_cfd_kg_s": "",
                "interpretation": "candidate identified but no corrected forward rerun exists yet",
            }
        )
    return rows


def sensor_score_rows() -> list[dict[str, Any]]:
    contract = {row.get("sensor", ""): row for row in read_csv(SENSOR_DIR / "sensor_map_contract.csv")}
    prediction_paths = [
        SOLVE_DIR / "solve_case_full/forward_v0_sensor_predictions_experimental.csv",
        SOLVE_DIR / "solve_case_full/forward_v0_sensor_predictions_cfd.csv",
    ]
    rows: list[dict[str, Any]] = []
    for path in prediction_paths:
        for row in read_csv(path):
            sensor = row.get("sensor", "")
            mapped = contract.get(sensor, {})
            score_status = mapped.get("score_status_current", "missing_sensor_contract")
            included = (
                score_status == "provisional_diagnostic_score_allowed"
                and finite_text(row.get("predicted_K", ""))
                and finite_text(row.get("target_K", ""))
            )
            rows.append(
                {
                    "case_id": row.get("case_id", ""),
                    "variant_id": row.get("variant_id", ""),
                    "sensor_source": row.get("sensor_source", ""),
                    "sensor": sensor,
                    "kind": row.get("kind", ""),
                    "score_status_current": score_status,
                    "score_included_current": "yes" if included else "no",
                    "predicted_K": row.get("predicted_K", ""),
                    "target_K": row.get("target_K", ""),
                    "error_K": row.get("error_K", ""),
                    "prediction_source_segment": row.get("prediction_source_segment", ""),
                    "prediction_source_fraction": row.get("prediction_source_fraction", ""),
                    "blocker_or_caveat": mapped.get("current_blocker_or_caveat", ""),
                }
            )
    return rows


def decision_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "D1_solve_case_confirmation",
            "claim_level": "authoritative_forward_v0_confirmation",
            "decision": "Use solve_case rows for forward-v0 claims; fast_scan may remain a screening proxy because all six comparison rows pass.",
            "evidence": rel(SOLVE_DIR / "comparison_summary.json"),
            "next_gate": "Use solve_case or documented proxy bands for forward-v1 refresh.",
        },
        {
            "decision_id": "D2_hydraulic_first",
            "claim_level": "screening_rerun_required",
            "decision": "Advance H1 localized named-loss/reset bundle before any thermal closure fit; faithful localized H1 requires Fluid-side API work, while an ethan_runs-only run is a downgraded fixed-K proxy screen.",
            "evidence": rel(HYD_DIR / "decision_summary.json"),
            "next_gate": "Run H1 and require mdot improvement on Salt2/Salt3/Salt4 without thermal fitting.",
        },
        {
            "decision_id": "D3_sensor_scores",
            "claim_level": "secondary_provisional_only",
            "decision": "Score only provisional finite TP/TW rows; exclude TP2 and TW10 from current totals.",
            "evidence": rel(SENSOR_DIR / "summary.json"),
            "next_gate": "Complete exact sensor coordinate/aggregation policy before thesis-grade sensor claims.",
        },
        {
            "decision_id": "D4_external_bc",
            "claim_level": "implementation_pending",
            "decision": "Do not emulate external-boundary physics by fixed wallHeatFlux replay; implement external_boundary_table when Fluid is writable.",
            "evidence": rel(EXTERNAL_BC_DIR / "fluid_external_boundary_patch_plan.md"),
            "next_gate": "Writable Fluid row or patch package with tests for emissivity/Tsur and no double-counting.",
        },
        {
            "decision_id": "D5_thermal_fit",
            "claim_level": "blocked",
            "decision": "No thermal UA/HTC/Nu fitting is admitted in the next wave.",
            "evidence": rel(THERMAL_GATE_DIR / "summary.json"),
            "next_gate": "Thermal sign, heat-balance, downcomer, and mesh-family gates must pass first.",
        },
    ]


def h1_feasibility_rows() -> list[dict[str, str]]:
    return [
        {
            "item": "faithful_localized_H1",
            "status": "requires_external_fluid_implementation",
            "implementation_path": "../cfd-modeling-tools Fluid solver/config support for named localized hydraulic loss and reset metadata",
            "scientific_label": "candidate_physics_rerun_not_yet_available",
            "guardrail": "do not collapse named component/cluster/branch losses into a publication closure without explicit Fluid support",
        },
        {
            "item": "ethan_runs_only_H1_proxy",
            "status": "possible_but_downgraded_screen",
            "implementation_path": "new task-scoped runner could pass aggregate MinorLosses/fixed-K values into existing Fluid APIs",
            "scientific_label": "screen_only_not_publication_closure",
            "guardrail": "label as directionality test; preserve named-loss ledger separately; no thermal fitting",
        },
        {
            "item": "global_loop_multiplier",
            "status": "rejected_except_math_baseline",
            "implementation_path": "do not export as model correction",
            "scientific_label": "diagnostic_baseline_only",
            "guardrail": "would hide localized pressure recovery, reset, feature loss, and recirculation invalidity",
        },
    ]


def queue_rows() -> list[dict[str, str]]:
    return [
        {
            "task_id": "NEXT-H1-HYDRAULIC-RERUN",
            "priority": "high",
            "parallel_group": "phase_2A",
            "owner_role": "Implementer/Tester/Writer",
            "write_scope": "new task-scoped work_product plus focused runner/test; external Fluid required for faithful localized H1",
            "objective": "Run H1 localized named-loss/reset hydraulic correction, or explicitly run a downgraded fixed-K proxy if Fluid remains read-only.",
            "acceptance_signal": "Salt2/Salt3/Salt4 mdot errors reported under locked split; thermal_fit_used=false; output labels faithful-H1 versus proxy.",
            "blocked_by": "true localized H1 requires Fluid API support for named/localized hydraulic losses and reset metadata",
        },
        {
            "task_id": "NEXT-EXTERNAL-BOUNDARY-FLUID-API",
            "priority": "high",
            "parallel_group": "phase_2A",
            "owner_role": "Implementer/Tester",
            "write_scope": "../cfd-modeling-tools Fluid if writable, otherwise ethan_runs patch package only",
            "objective": "Implement ambient_loss_model=external_boundary_table from AGENT-297 dictionary.",
            "acceptance_signal": "Tests show emissivity/Tsur affect setup mode and realized wallHeatFlux replay does not add radiation.",
            "blocked_by": "workspace write permissions outside ethan_runs",
        },
        {
            "task_id": "NEXT-SENSOR-SCORE-REFRESH",
            "priority": "medium",
            "parallel_group": "phase_2B",
            "owner_role": "Implementer/Writer",
            "write_scope": "new scorecard refresh package",
            "objective": "Summarize provisional solve_case sensor scores using AGENT-302 contract.",
            "acceptance_signal": "TP2/TW10 excluded; all scored rows are post-solve validation joins, not runtime inputs.",
            "blocked_by": "exact survey-grade sensor locations for final thesis claims",
        },
        {
            "task_id": "NEXT-FORWARD-V1-SCORECARD",
            "priority": "medium",
            "parallel_group": "phase_2C",
            "owner_role": "Coordinator/Writer",
            "write_scope": "new forward-v1 scorecard package",
            "objective": "Regenerate scorecard after H1 rerun and external/sensor decisions are current.",
            "acceptance_signal": "Train/validation/holdout table separates passed scores from blockers and uses solve_case-authoritative rows.",
            "blocked_by": "H1 rerun not executed; external BC runtime mode pending",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    artifacts = [
        ("solve_case_comparison", SOLVE_DIR / "solve_case_vs_fast_scan_comparison.csv", "present", "authoritative comparison"),
        ("solve_case_summary", SOLVE_DIR / "comparison_summary.json", "present", "authoritative comparison summary"),
        ("hydraulic_candidates", HYD_DIR / "decision_summary.json", "present", "phase 2 hydraulic candidate"),
        ("sensor_contract", SENSOR_DIR / "summary.json", "present", "sensor scoring contract"),
        ("scorecard_precursor", SCORECARD_DIR / "summary.json", "present_stale", "historical precursor"),
        ("external_bc_bridge", EXTERNAL_BC_DIR / "summary.json", "present", "external boundary bridge"),
        ("thermal_mesh_gate", THERMAL_GATE_DIR / "summary.json", "present", "thermal fit blocker"),
    ]
    return [
        {"artifact_id": artifact_id, "path": rel(path), "status": status, "role": role}
        for artifact_id, path, status, role in artifacts
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(SOLVE_DIR / 'comparison_summary.json')}
  - {rel(HYD_DIR / 'decision_summary.json')}
  - {rel(SENSOR_DIR / 'summary.json')}
tags: [forward-model, predictive-1d, coordination, solve-case, hydraulics]
related:
  - .agent/status/2026-07-13_AGENT-299.md
  - .agent/journal/2026-07-13/predictive-parallel-execution-coordination.md
task: AGENT-299
date: 2026-07-13
role: Coordinator/Integrator/Tester/Writer
type: work_product
status: complete
---
# Predictive Parallel Execution Coordination

Generated: `{summary['generated_utc']}`

This package integrates the next two predictive phases without mutating native
CFD outputs or editing external Fluid source. It supersedes the earlier
coordination stub by harvesting the completed full `solve_case` confirmation
and AGENT-300 hydraulic-candidate package.

## Main Result

- Full `solve_case` confirmation passed: `{summary['solve_case_pass_rows']}` of
  `{summary['solve_case_comparison_rows']}` rows pass.
- Fast scan remains a screening proxy, but `solve_case` rows are authoritative.
- H1 localized named-loss/reset is the next hydraulic rerun candidate; it has
  not been rerun yet.
- Faithful localized H1 requires Fluid-side API work; an `ethan_runs`-only
  implementation would be a downgraded fixed-K proxy screen.
- Sensor scoring is provisional only; TP2 and TW10 remain excluded.
- External boundary table implementation is still pending writable Fluid source.
- Thermal UA/HTC/Nu fitting remains blocked.

## Outputs

- `forward_v1_integration_summary.csv`
- `solve_case_vs_fast_scan.csv`
- `hydraulic_H1_screening_scores.csv`
- `h1_feasibility_notes.csv`
- `sensor_score_provisional.csv`
- `forward_v1_decision_table.csv`
- `next_phase_task_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

- Do not claim end-to-end forward-v1 readiness before an H1 rerun improves mdot.
- Do not use TP/TW measurements as runtime inputs.
- Do not add separate radiation to realized CFD `wallHeatFlux` replay.
- Do not fit thermal UA/HTC/Nu while the thermal mesh/sign gate is blocked.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    solve_comparison = SOLVE_DIR / "solve_case_vs_fast_scan_comparison.csv"
    if solve_comparison.exists():
        shutil.copyfile(solve_comparison, out_dir / "solve_case_vs_fast_scan.csv")
    else:
        write_csv(out_dir / "solve_case_vs_fast_scan.csv", [], [])

    integration = integration_rows()
    h1 = h1_rows()
    h1_feasibility = h1_feasibility_rows()
    sensors = sensor_score_rows()
    decisions = decision_rows()
    queue = queue_rows()
    manifest = source_manifest_rows()

    write_csv(out_dir / "forward_v1_integration_summary.csv", integration, INTEGRATION_COLUMNS)
    write_csv(out_dir / "hydraulic_H1_screening_scores.csv", h1, H1_COLUMNS)
    write_csv(out_dir / "h1_feasibility_notes.csv", h1_feasibility, H1_FEASIBILITY_COLUMNS)
    write_csv(out_dir / "sensor_score_provisional.csv", sensors, SENSOR_COLUMNS)
    write_csv(out_dir / "forward_v1_decision_table.csv", decisions, DECISION_COLUMNS)
    write_csv(out_dir / "next_phase_task_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    solve_summary = read_json(SOLVE_DIR / "comparison_summary.json")
    sensor_included = sum(1 for row in sensors if row["score_included_current"] == "yes")
    summary = {
        "task_id": "AGENT-299",
        "generated_utc": utc_now(),
        "package": rel(out_dir),
        "overall_status": "phase_1_integrated_phase_2_ready_with_blockers",
        "solve_case_status": solve_summary.get("overall_status", "missing"),
        "solve_case_pass_rows": solve_summary.get("n_pass_rows", 0),
        "solve_case_comparison_rows": solve_summary.get("n_comparison_rows", 0),
        "h1_rerun_status": "not_executed_candidate_ready",
        "sensor_rows_total": len(sensors),
        "sensor_rows_included_current": sensor_included,
        "thermal_fit_admitted": False,
        "external_fluid_modified": False,
        "native_solver_outputs_mutated": False,
        "row_counts": {
            "integration_rows": len(integration),
            "h1_screening_rows": len(h1),
            "h1_feasibility_rows": len(h1_feasibility),
            "sensor_score_rows": len(sensors),
            "decision_rows": len(decisions),
            "queue_rows": len(queue),
            "manifest_rows": len(manifest),
        },
        "outputs": [
            "README.md",
            "forward_v1_integration_summary.csv",
            "solve_case_vs_fast_scan.csv",
            "hydraulic_H1_screening_scores.csv",
            "h1_feasibility_notes.csv",
            "sensor_score_provisional.csv",
            "forward_v1_decision_table.csv",
            "next_phase_task_queue.csv",
            "source_manifest.csv",
            "summary.json",
        ],
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = build_package(args.output_dir)
    print(json.dumps(summary["row_counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
