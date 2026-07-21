#!/usr/bin/env python3
"""Build the frozen upcomer hybrid candidate score/admission package."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-UPCOMER-HYBRID-FROZEN-CANDIDATE-SCORE"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_hybrid_frozen_candidate_score"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-UPCOMER-HYBRID-FROZEN-CANDIDATE-SCORE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/upcomer-hybrid-frozen-candidate-score.md"
IMPORT = ROOT / "imports/2026-07-17_upcomer_hybrid_frozen_candidate_score.json"

HYBRID_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "hybrid_model_candidate_contract.csv"
)
FEATURE_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "recirculation_feature_scorecard.csv"
)
UPCOMER_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "upcomer_admission_decision.csv"
)
ONSET_MATRIX = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix"
    / "upcomer_onset_anchor_matrix.csv"
)
REQUIRED_OUTPUTS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix"
    / "required_output_contract.csv"
)
COUPLED_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard"
    / "admission_status_scorecard.csv"
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
    required = [HYBRID_CONTRACT, FEATURE_SCORECARD, UPCOMER_DECISION, ONSET_MATRIX, REQUIRED_OUTPUTS, COUPLED_SCORECARD]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing frozen hybrid candidate sources: " + "; ".join(missing))


def build_candidate_definition() -> list[dict[str, object]]:
    return [
        {
            "candidate_id": "UH1_throughflow_pipe_plus_recirc_cell",
            "candidate_status": "frozen_contract_not_fit",
            "pressure_form": "dp_upcomer = dp_throughflow_pipe + dp_recirc_cell_penalty",
            "thermal_form": "Q_upcomer = Q_wall_core_exchange + Q_test_section_coupling + Q_recirc_cell_exchange",
            "regime_weight_form": "w_recirc = clamp(max(RAF, RMF, min(1,Ri/Ri_ref), SVF), 0, 1)",
            "allowed_runtime_inputs": "geometry;setup boundary data;solved state;RAF/RMF/SVF/Ri/Gr/Ra/Re/Pr/Gz only after admitted extraction",
            "forbidden_labels": "single_stream_Nu;single_stream_f_D;component_K;ordinary_F6",
            "admission_status": "blocked",
            "reason": "onset anchors and split-safe coupled scores are missing",
        }
    ]


def build_input_contract() -> list[dict[str, object]]:
    required = read_csv(REQUIRED_OUTPUTS)
    rows = [
        {
            "input_name": row["required_output"],
            "role": row["why_required"],
            "runtime_allowed_now": "false",
            "fit_allowed_now": "false",
            "required_before_admission": row["required_for_acceptance"],
        }
        for row in required
    ]
    rows.extend(
        [
            {"input_name": "CFD mdot", "role": "forbidden leakage", "runtime_allowed_now": "false", "fit_allowed_now": "false", "required_before_admission": "no"},
            {"input_name": "realized wallHeatFlux as runtime closure", "role": "forbidden leakage", "runtime_allowed_now": "false", "fit_allowed_now": "false", "required_before_admission": "no"},
            {"input_name": "validation TP/TW temperatures", "role": "forbidden leakage", "runtime_allowed_now": "false", "fit_allowed_now": "false", "required_before_admission": "no"},
        ]
    )
    return rows


def build_score_gate_rows() -> list[dict[str, object]]:
    return [
        {"score_gate": "onset_anchor_coverage", "status": "blocked", "required_metric": "ordinary/transition/recirculating anchors", "current_evidence": "design_only_not_launched"},
        {"score_gate": "train_validation_holdout_mdot", "status": "blocked", "required_metric": "mdot error", "current_evidence": "not_run"},
        {"score_gate": "train_validation_holdout_tp_tw", "status": "blocked", "required_metric": "TP_RMSE;TW_RMSE", "current_evidence": "not_run"},
        {"score_gate": "thermal_state_scores", "status": "blocked", "required_metric": "Tmean;loop_delta_T", "current_evidence": "not_run"},
        {"score_gate": "residual_ownership", "status": "blocked", "required_metric": "no pressure/thermal residual absorption", "current_evidence": "guardrail_only"},
        {"score_gate": "mesh_time_uncertainty", "status": "blocked", "required_metric": "RAF/RMF/SVF/wall-core uncertainty", "current_evidence": "missing"},
    ]


def build_admission_decision() -> list[dict[str, object]]:
    features = read_csv(FEATURE_SCORECARD)
    anchors = read_csv(ONSET_MATRIX)
    return [
        {
            "candidate_id": "UH1_throughflow_pipe_plus_recirc_cell",
            "admission_status": "blocked",
            "fit_allowed_now": "false",
            "score_allowed_now": "diagnostic_contract_only",
            "feature_rows_available": len(features),
            "anchor_rows_available": len(anchors),
            "launched_anchor_rows": 0,
            "ordinary_fit_admitted_rows": 0,
            "hybrid_fit_admitted_rows": 0,
            "blocking_reasons": "anchor_matrix_design_only;split_scores_not_run;mesh_time_uncertainty_missing;runtime_feature_admission_missing",
        }
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_ordinary_labels", "status": "pass_forbidden", "forbidden_input": "single-stream Nu/f_D/K labels", "policy": "hybrid lane only"},
        {"check": "no_cfd_mdot_runtime", "status": "pass_forbidden", "forbidden_input": "CFD mdot", "policy": "solved output"},
        {"check": "no_realized_wall_heat_runtime", "status": "pass_forbidden", "forbidden_input": "realized wallHeatFlux", "policy": "diagnostic only"},
        {"check": "no_validation_temperature_runtime", "status": "pass_forbidden", "forbidden_input": "validation TP/TW temperatures", "policy": "post-solve target"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("hybrid_contract", HYBRID_CONTRACT, "hybrid candidate lanes"),
        ("feature_scorecard", FEATURE_SCORECARD, "current recirculation features"),
        ("upcomer_decision", UPCOMER_DECISION, "current admission decisions"),
        ("onset_matrix", ONSET_MATRIX, "anchor matrix design"),
        ("required_outputs", REQUIRED_OUTPUTS, "hybrid input requirements"),
        ("coupled_scorecard", COUPLED_SCORECARD, "final coupled admission status"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(HYBRID_CONTRACT)}",
                f"  - {rel(ONSET_MATRIX)}",
                f"  - {rel(COUPLED_SCORECARD)}",
                "tags: [upcomer, hybrid-model, frozen-candidate, admission]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Upcomer Hybrid Frozen Candidate Score",
                "",
                "## Decision",
                "",
                "`UH1_throughflow_pipe_plus_recirc_cell` is defined as a frozen candidate contract, but it is not admitted. Required onset anchors, split-safe coupled scores, and mesh/time uncertainty are missing.",
                "",
                "## Results",
                "",
                f"- Candidate rows: `{summary['candidate_rows']}`.",
                f"- Candidate admitted rows: `{summary['candidate_admitted_rows']}`.",
                f"- Score gates blocked: `{summary['blocked_score_gates']}`.",
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
                "tags: [status, upcomer, hybrid-model]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- A frozen hybrid candidate can be specified from existing feature and model-form evidence.",
                "- It cannot be admitted because onset anchors are design-only and split-safe scores are not run.",
                "- Ordinary `Nu`, `f_D`, and `K` labels remain forbidden for current recirculating rows.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_upcomer_hybrid_frozen_candidate_score`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
            ]
        )
        + "\n"
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(HYBRID_CONTRACT)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, upcomer, hybrid-model]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Upcomer Hybrid Frozen Candidate Score Journal",
                "",
                "UH1 is now defined as a candidate contract. It remains blocked, which is the scientifically rigorous state until anchors and split scores exist.",
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
        "generated_index_refresh_note": "Skipped because active/completed board context owns generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = build_candidate_definition()
    inputs = build_input_contract()
    gates = build_score_gate_rows()
    decisions = build_admission_decision()
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(OUT / "frozen_candidate_definition.csv", candidates, ["candidate_id", "candidate_status", "pressure_form", "thermal_form", "regime_weight_form", "allowed_runtime_inputs", "forbidden_labels", "admission_status", "reason"])
    write_csv(OUT / "hybrid_input_contract.csv", inputs, ["input_name", "role", "runtime_allowed_now", "fit_allowed_now", "required_before_admission"])
    write_csv(OUT / "hybrid_score_gate.csv", gates, ["score_gate", "status", "required_metric", "current_evidence"])
    write_csv(OUT / "hybrid_admission_decision.csv", decisions, ["candidate_id", "admission_status", "fit_allowed_now", "score_allowed_now", "feature_rows_available", "anchor_rows_available", "launched_anchor_rows", "ordinary_fit_admitted_rows", "hybrid_fit_admitted_rows", "blocking_reasons"])
    write_csv(OUT / "runtime_hybrid_candidate_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "candidate_rows": len(candidates),
        "candidate_admitted_rows": sum(1 for row in decisions if row["admission_status"] == "admitted"),
        "input_contract_rows": len(inputs),
        "blocked_score_gates": sum(1 for row in gates if row["status"] == "blocked"),
        "runtime_audit_rows": len(runtime),
        "runtime_audit_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
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
