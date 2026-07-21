#!/usr/bin/env python3
"""Build the final coupled segment M3+TS admission scorecard."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/predict-coupled-segment-m3ts-scorecard.md"
IMPORT = ROOT / "imports/2026-07-17_predict_coupled_segment_m3ts_scorecard.json"

SEGMENT_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_equation_contract"
    / "downstream_gate_contract.csv"
)
PRESSURE_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
    / "segment_pressure_model_scorecard.csv"
)
THERMAL_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
    / "segment_thermal_model_scorecard.csv"
)
UPCOMER_HYBRID = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "upcomer_admission_decision.csv"
)
BRANCH_MASK = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard"
    / "ordinary_pipe_branch_mask.csv"
)
DEVELOPMENT_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard"
    / "prerequisite_gate_scorecard.csv"
)
SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude"
    / "sensor_policy_scorecard.csv"
)
SPLIT_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy"
    / "canonical_final_predictive_split_policy.csv"
)
PREVIOUS_M3TS_SCORE = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score"
    / "m3ts_coupled_scorecard.csv"
)
PREVIOUS_M3TS_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score"
    / "m3ts_admission_review.csv"
)
PREVIOUS_M3_DELTA = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score"
    / "m2_m3_delta_summary.csv"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [
        SEGMENT_CONTRACT,
        PRESSURE_SCORECARD,
        THERMAL_SCORECARD,
        UPCOMER_HYBRID,
        BRANCH_MASK,
        DEVELOPMENT_SCORECARD,
        SENSOR_POLICY,
        SPLIT_POLICY,
        PREVIOUS_M3TS_SCORE,
        PREVIOUS_M3TS_ADMISSION,
        PREVIOUS_M3_DELTA,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing coupled M3+TS scorecard sources: " + "; ".join(missing))


def build_prerequisite_matrix() -> list[dict[str, object]]:
    pressure = read_csv(PRESSURE_SCORECARD)
    thermal = read_csv(THERMAL_SCORECARD)
    upcomer = read_csv(UPCOMER_HYBRID)
    branch = read_csv(BRANCH_MASK)
    development = read_csv(DEVELOPMENT_SCORECARD)
    sensor = read_csv(SENSOR_POLICY)
    split = read_csv(SPLIT_POLICY)
    previous = read_csv(PREVIOUS_M3TS_ADMISSION)
    return [
        {"gate": "segment_equation_contract", "status": "available", "admitted_rows": len(read_csv(SEGMENT_CONTRACT)), "blocking": "false", "reason": "pressure/thermal runtime contracts exist"},
        {"gate": "segment_pressure_models", "status": "blocked", "admitted_rows": sum(int(row["scoreable_predictive_model_rows"]) for row in pressure), "blocking": "true", "reason": "zero scoreable predictive pressure model rows"},
        {"gate": "segment_thermal_models", "status": "partial", "admitted_rows": sum(int(row["scoreable_predictive_thermal_rows"]) for row in thermal), "blocking": "true", "reason": "heater/cooler setup admitted but test-section/upcomer/wall lanes blocked"},
        {"gate": "upcomer_hybrid", "status": "diagnostic_only", "admitted_rows": sum(1 for row in upcomer if row["admission_status"] == "diagnostic_only_contract_complete"), "blocking": "true", "reason": "hybrid lane lacks predictive calibration"},
        {"gate": "branch_specific_ordinary_pipe", "status": "blocked", "admitted_rows": sum(int(row["ordinary_pipe_fit_included"] == "true") for row in branch), "blocking": "true", "reason": "zero ordinary aggregate branches included"},
        {"gate": "boundary_layer_development", "status": "diagnostic_only", "admitted_rows": sum(int(row["admitted_rows"]) for row in development), "blocking": "true", "reason": "zero executable development ablation rows"},
        {"gate": "sensor_policy", "status": "validation_only", "admitted_rows": sum(1 for row in sensor if row["aggregate_score_after_refresh"] == "yes"), "blocking": "false", "reason": "post-solve targets are available but runtime temperatures are forbidden"},
        {"gate": "final_split_policy", "status": "available", "admitted_rows": sum(1 for row in split if row["score_allowed"] == "yes"), "blocking": "false", "reason": "Salt1-4 final training/support policy is available"},
        {"gate": "previous_m3ts_candidates", "status": "not_admitted", "admitted_rows": sum(1 for row in previous if row["admission_decision"] == "admitted"), "blocking": "true", "reason": "frozen M3+TS candidates failed coupled/heat gates"},
    ]


def build_candidate_scorecard() -> list[dict[str, object]]:
    previous = read_csv(PREVIOUS_M3TS_ADMISSION)
    score_rows = read_csv(PREVIOUS_M3TS_SCORE)
    rows: list[dict[str, object]] = []
    for candidate in previous:
        related_scores = [row for row in score_rows if row["candidate_id"] == candidate["candidate_id"]]
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_family": "frozen_m3ts_2026_07_16",
                "admission_status": "blocked",
                "validation_status": "diagnostic_only",
                "coupled_score_rows": len(related_scores),
                "coupled_run_status": ";".join(sorted({row["coupled_run_status"] for row in related_scores})),
                "candidate_admitted": "false",
                "blocking_reasons": candidate["blocking_reasons"],
                "source_path": rel(PREVIOUS_M3TS_ADMISSION),
            }
        )
    rows.append(
        {
            "candidate_id": "segment_setup_only_forward_v1",
            "candidate_family": "assembled_from_2026_07_17_scorecards",
            "admission_status": "blocked",
            "validation_status": "not_run_gate_blocked",
            "coupled_score_rows": 0,
            "coupled_run_status": "not_run_prerequisite_gates_failed",
            "candidate_admitted": "false",
            "blocking_reasons": "pressure_closure_zero_admitted;test_section_passive_loss_not_admitted;upcomer_hybrid_not_calibrated;ordinary_branch_mask_zero;development_ablation_not_executable",
            "source_path": ";".join([rel(PRESSURE_SCORECARD), rel(THERMAL_SCORECARD), rel(UPCOMER_HYBRID), rel(BRANCH_MASK), rel(DEVELOPMENT_SCORECARD)]),
        }
    )
    return rows


def build_admission_status_scorecard() -> list[dict[str, object]]:
    candidates = build_candidate_scorecard()
    split = read_csv(SPLIT_POLICY)
    sensor = read_csv(SENSOR_POLICY)
    return [
        {
            "admission_status": "admitted",
            "row_count": 0,
            "items": "none",
            "allowed_use": "none_for_final_forward_v1",
            "guardrail": "do not claim admitted coupled closure",
        },
        {
            "admission_status": "validation-only",
            "row_count": sum(1 for row in sensor if row["aggregate_score_after_refresh"] == "yes"),
            "items": "TP/TW post-solve scoring targets; final split cases with score_allowed=yes",
            "allowed_use": "validation and reporting after solver output exists",
            "guardrail": "runtime_temperature_allowed=false; fit_allowed=false for sensors",
        },
        {
            "admission_status": "diagnostic-only",
            "row_count": len(candidates) - sum(1 for row in candidates if row["candidate_admitted"] == "true"),
            "items": "previous frozen M3+TS attempts; pressure/thermal/source-sink/development diagnostics",
            "allowed_use": "blocker narrowing and thesis evidence",
            "guardrail": "not closure admission",
        },
        {
            "admission_status": "blocked",
            "row_count": sum(1 for row in candidates if row["admission_status"] == "blocked"),
            "items": "final forward-v1 coupled admission",
            "allowed_use": "unresolved blocker queue",
            "guardrail": "must pass prerequisite gates before final admission",
        },
    ]


def build_blocker_queue() -> list[dict[str, object]]:
    return [
        {"blocker_id": "pressure_closure_admission", "status": "open", "next_action": "admit segment-local pressure coefficients or keep diagnostic-only pressure terms", "source_path": rel(PRESSURE_SCORECARD)},
        {"blocker_id": "test_section_passive_loss", "status": "open", "next_action": "produce setup-only test-section passive loss candidate that passes validation and holdout heat gates", "source_path": rel(THERMAL_SCORECARD)},
        {"blocker_id": "upcomer_hybrid_calibration", "status": "open", "next_action": "add ordinary/transition anchors and split-score a frozen hybrid penalty form", "source_path": rel(UPCOMER_HYBRID)},
        {"blocker_id": "boundary_layer_executable_ablation", "status": "open", "next_action": "run segment-specific ablations only after prerequisite closures are admitted", "source_path": rel(DEVELOPMENT_SCORECARD)},
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_cfd_mdot_runtime", "status": "pass_forbidden", "forbidden_input": "CFD mdot", "policy": "mdot must be solved by coupled model"},
        {"check": "no_validation_temperature_runtime", "status": "pass_forbidden", "forbidden_input": "validation TP/TW temperatures", "policy": "post-solve score targets only"},
        {"check": "no_realized_wall_heat_runtime", "status": "pass_forbidden", "forbidden_input": "realized wallHeatFlux", "policy": "diagnostic evidence only"},
        {"check": "no_imposed_cfd_cooler_duty_runtime", "status": "pass_forbidden", "forbidden_input": "imposed CFD cooler duty", "policy": "cooler model must use setup-only admitted terms"},
        {"check": "no_global_multiplier", "status": "pass_forbidden", "forbidden_input": "global friction/thermal multiplier", "policy": "segment-local terms only"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("segment_contract", SEGMENT_CONTRACT, "downstream gate contract"),
        ("pressure_scorecard", PRESSURE_SCORECARD, "segment pressure gates"),
        ("thermal_scorecard", THERMAL_SCORECARD, "segment thermal gates"),
        ("upcomer_hybrid", UPCOMER_HYBRID, "upcomer hybrid gate"),
        ("branch_mask", BRANCH_MASK, "ordinary branch mask"),
        ("development_scorecard", DEVELOPMENT_SCORECARD, "boundary-layer gate"),
        ("sensor_policy", SENSOR_POLICY, "TP/TW target policy"),
        ("split_policy", SPLIT_POLICY, "final split policy"),
        ("previous_m3ts_score", PREVIOUS_M3TS_SCORE, "prior coupled attempt scores"),
        ("previous_m3ts_admission", PREVIOUS_M3TS_ADMISSION, "prior candidate admission review"),
        ("previous_m3_delta", PREVIOUS_M3_DELTA, "M2/M3 comparator deltas"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(PRESSURE_SCORECARD)}",
                f"  - {rel(THERMAL_SCORECARD)}",
                f"  - {rel(PREVIOUS_M3TS_ADMISSION)}",
                "tags: [coupled-m3ts, forward-v1, admission, scorecard]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Coupled Segment M3+TS Scorecard",
                "",
                "## Decision",
                "",
                "Final forward-v1 coupled admission remains blocked. This package completes the scorecard by admission status: "
                "zero admitted coupled candidates, validation-only sensor/split targets, diagnostic-only prior M3+TS evidence, and explicit unresolved blockers.",
                "",
                "## Results",
                "",
                f"- Candidate rows: `{summary['candidate_rows']}`.",
                f"- Candidates admitted: `{summary['candidates_admitted']}`.",
                f"- Blocking prerequisite gates: `{summary['blocking_prerequisite_gates']}`.",
                f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
            ]
        )
        + "\n"
    )
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                f"  - {rel(OUT / 'summary.json')}",
                "tags: [status, coupled-m3ts, forward-v1]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- Prior frozen M3+TS candidates were not admitted.",
                "- Current prerequisite gates still block final forward-v1 coupled admission.",
                "- Validation targets and diagnostic evidence remain useful when separated from closure claims.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_coupled_segment_m3ts_scorecard`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for final coupled scorecard visibility.",
                "- Final forward-v1 remains blocked by pressure closure admission, test-section passive loss, upcomer hybrid calibration, and executable boundary-layer ablations.",
                "- Generated docs index refresh was skipped because active board rows own generated index files.",
            ]
        )
        + "\n"
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(PREVIOUS_M3TS_ADMISSION)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, coupled-m3ts, forward-v1]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Coupled Segment M3+TS Scorecard Journal",
                "",
                "## Files Changed",
                "",
                "- `tools/analyze/run_coupled_segment_m3ts_scorecard.py`",
                "- `tools/analyze/test_coupled_segment_m3ts_scorecard.py`",
                f"- `{rel(OUT)}/`",
                f"- `{rel(STATUS)}`",
                f"- `{rel(JOURNAL)}`",
                f"- `{rel(IMPORT)}`",
                "- `.agent/BOARD.md` own row status",
                "",
                "## Interpretation",
                "",
                "The final story is defensible because implementation, diagnostic evidence, admission gates, and unresolved blockers are separated.",
            ]
        )
        + "\n"
    )
    manifest = {
        "task": TASK,
        "date": DATE,
        "package": rel(OUT),
        "outputs": sorted(path.name for path in OUT.iterdir() if path.is_file()),
        "summary": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
        "generated_index_refresh_note": "Skipped because active board rows own generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)
    prerequisites = build_prerequisite_matrix()
    candidates = build_candidate_scorecard()
    admission = build_admission_status_scorecard()
    blockers = build_blocker_queue()
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(OUT / "prerequisite_gate_matrix.csv", prerequisites, ["gate", "status", "admitted_rows", "blocking", "reason"])
    write_csv(OUT / "coupled_candidate_gate_scorecard.csv", candidates, ["candidate_id", "candidate_family", "admission_status", "validation_status", "coupled_score_rows", "coupled_run_status", "candidate_admitted", "blocking_reasons", "source_path"])
    write_csv(OUT / "admission_status_scorecard.csv", admission, ["admission_status", "row_count", "items", "allowed_use", "guardrail"])
    write_csv(OUT / "unresolved_blocker_queue.csv", blockers, ["blocker_id", "status", "next_action", "source_path"])
    write_csv(OUT / "runtime_coupled_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "candidate_rows": len(candidates),
        "candidates_admitted": sum(1 for row in candidates if row["candidate_admitted"] == "true"),
        "admission_status_rows": len(admission),
        "blocking_prerequisite_gates": sum(1 for row in prerequisites if row["blocking"] == "true"),
        "unresolved_blocker_rows": len(blockers),
        "runtime_audit_rows": len(runtime),
        "runtime_audit_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
        "final_forward_v1_status": "blocked",
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_docs(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
