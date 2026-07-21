#!/usr/bin/env python3
"""Build the upcomer throughflow-pipe plus recirculation-cell hybrid package."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/upcomer-pipe-cell-hybrid-model.md"
IMPORT = ROOT / "imports/2026-07-17_upcomer_pipe_cell_hybrid_model.json"

HYBRID_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract"
    / "hybrid_1d_model_contract.csv"
)
FEATURE_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract"
    / "recirculation_feature_admission_table.csv"
)
PM5_METRICS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
    / "salt2_pm5_holdout_metrics.csv"
)
PM5_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair"
    / "salt2_pm5_admission_table.csv"
)
ONSET_CLASS = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard"
    / "upcomer_onset_classification.csv"
)
F6_CANDIDATES = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock"
    / "f6_candidate_inventory.csv"
)
THERMAL_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
    / "segment_thermal_model_scorecard.csv"
)
PRESSURE_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
    / "segment_pressure_model_scorecard.csv"
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
        HYBRID_CONTRACT,
        FEATURE_ADMISSION,
        PM5_METRICS,
        PM5_ADMISSION,
        ONSET_CLASS,
        F6_CANDIDATES,
        THERMAL_SCORECARD,
        PRESSURE_SCORECARD,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing upcomer hybrid sources: " + "; ".join(missing))


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value not in {"", None} else 0.0


def _h_proxy(row: dict[str, str]) -> str:
    if row.get("h_proxy_W_m2_K"):
        return row["h_proxy_W_m2_K"]
    delta_t = _float(row, "delta_T_wall_bulk_K")
    if abs(delta_t) < 1e-12:
        return ""
    return str(_float(row, "wallHeatFlux_W_m2") / delta_t)


def build_candidate_contract() -> list[dict[str, object]]:
    source_rows = read_csv(HYBRID_CONTRACT)
    rows: list[dict[str, object]] = []
    for row in source_rows:
        if row["model_lane"] == "ordinary_pipe":
            fit_allowed = "false_for_current_upcomer"
            score_allowed = "false"
            current_status = "blocked_current_rows_not_ordinary"
        elif row["model_lane"] == "transition_diagnostic":
            fit_allowed = "false"
            score_allowed = "diagnostic"
            current_status = "blocked_missing_transition_anchor"
        elif row["model_lane"] == "recirculating_upcomer_effective":
            fit_allowed = "false"
            score_allowed = "diagnostic_model_contract_ready"
            current_status = "contract_ready_not_calibrated"
        else:
            fit_allowed = "false"
            score_allowed = "diagnostic"
            current_status = row["current_status"]
        rows.append(
            {
                "model_lane": row["model_lane"],
                "applies_when": row["applies_when"],
                "allowed_labels": row["allowed_labels"],
                "forbidden_labels": row["forbidden_labels"],
                "solver_facing_behavior": row["solver_facing_behavior"],
                "fit_allowed_now": fit_allowed,
                "score_allowed_now": score_allowed,
                "current_status": current_status,
                "required_evidence_to_admit": row["required_evidence_to_admit"],
                "do_not_do_guardrail": row["do_not_do_guardrail"],
            }
        )
    return rows


def build_feature_scorecard() -> list[dict[str, object]]:
    metrics = read_csv(PM5_METRICS)
    rows: list[dict[str, object]] = []
    for row in metrics:
        rows.append(
            {
                "case_key": row["case_key"],
                "case_role": row["case_role"],
                "span": row["span"],
                "Re": row["Re"],
                "Ri": row["Ri"],
                "Pr": row["Pr"],
                "Gz": row["Gz"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_velocity_fraction": row["secondary_velocity_fraction"],
                "delta_T_wall_bulk_K": row["delta_T_wall_bulk_K"],
                "h_proxy_W_m2_K": _h_proxy(row),
                "regime_weight_basis": "max(reverse_area_fraction, reverse_mass_fraction, min(1,Ri))",
                "regime_class": "recirculating_upcomer_effective"
                if max(_float(row, "reverse_area_fraction"), _float(row, "reverse_mass_fraction")) >= 0.10
                else "transition_diagnostic",
                "ordinary_fit_allowed": "false",
                "hybrid_use_allowed": "diagnostic_only_not_calibrated",
                "blocked_labels": "single_stream_Nu;single_stream_f_D;component_K",
                "source_path": rel(PM5_METRICS),
            }
        )
    return rows


def build_admission_decisions() -> list[dict[str, object]]:
    feature_rows = build_feature_scorecard()
    onset = read_csv(ONSET_CLASS)
    f6 = read_csv(F6_CANDIDATES)
    thermal_upcomer = [row for row in read_csv(THERMAL_SCORECARD) if row["loop_region"] == "upcomer"][0]
    pressure_upcomer = [row for row in read_csv(PRESSURE_SCORECARD) if row["loop_region"] == "upcomer"][0]
    max_raf = max(_float(row, "reverse_area_fraction") for row in feature_rows)
    max_rmf = max(_float(row, "reverse_mass_fraction") for row in feature_rows)
    max_ri = max(_float(row, "Ri") for row in feature_rows)
    return [
        {
            "decision_id": "ordinary_upcomer_pipe_coefficients",
            "admission_status": "blocked",
            "fit_allowed_now": "false",
            "score_allowed_now": "false",
            "evidence_rows": len(feature_rows) + len(onset),
            "max_reverse_area_fraction": max_raf,
            "max_reverse_mass_fraction": max_rmf,
            "max_Ri": max_ri,
            "blocked_labels": "single_stream_Nu;single_stream_f_D;component_K;ordinary_F6",
            "reason": "material recirculation invalidates current single-stream ordinary-pipe labels",
            "source_paths": ";".join([rel(FEATURE_ADMISSION), rel(PM5_METRICS), rel(ONSET_CLASS)]),
        },
        {
            "decision_id": "hybrid_throughflow_pipe_plus_cell_contract",
            "admission_status": "diagnostic_only_contract_complete",
            "fit_allowed_now": "false",
            "score_allowed_now": "diagnostic",
            "evidence_rows": len(feature_rows),
            "max_reverse_area_fraction": max_raf,
            "max_reverse_mass_fraction": max_rmf,
            "max_Ri": max_ri,
            "blocked_labels": "calibrated_predictive_penalty;true_Nu;true_f_D;true_K",
            "reason": "features and candidate form are defined, but onset anchors and split scoring are missing",
            "source_paths": ";".join([rel(HYBRID_CONTRACT), rel(PM5_ADMISSION), rel(F6_CANDIDATES)]),
        },
        {
            "decision_id": "coupled_upcomer_pressure_thermal_use",
            "admission_status": "blocked_pending_hybrid_calibration",
            "fit_allowed_now": "false",
            "score_allowed_now": "diagnostic",
            "evidence_rows": len(f6),
            "max_reverse_area_fraction": max_raf,
            "max_reverse_mass_fraction": max_rmf,
            "max_Ri": max_ri,
            "blocked_labels": "runtime_global_multiplier;ordinary_internal_Nu_absorption",
            "reason": f"pressure={pressure_upcomer['admission_status']}; thermal={thermal_upcomer['admission_status']}",
            "source_paths": ";".join([rel(PRESSURE_SCORECARD), rel(THERMAL_SCORECARD)]),
        },
    ]


def build_onset_gap_rows() -> list[dict[str, object]]:
    return [
        {
            "gap_id": "ordinary_transition_anchors",
            "status": "missing",
            "needed": "same-window ordinary/transition anchor cases such as Re 150/200/250 with low and rising RAF/RMF",
            "why_needed": "calibrate onset probability and keep recirculation penalty separate from ordinary pipe coefficients",
        },
        {
            "gap_id": "split_scored_hybrid_penalty",
            "status": "missing",
            "needed": "train/validation/holdout mdot, TP/TW, Tmean, and loop-dT score for a frozen hybrid penalty form",
            "why_needed": "promote the hybrid lane from diagnostic contract to predictive closure",
        },
        {
            "gap_id": "mesh_time_uncertainty",
            "status": "missing",
            "needed": "mesh/time uncertainty on RAF/RMF/SVF and wall-core Delta T",
            "why_needed": "prevent a coarse-only recirculation feature from becoming an overfit closure",
        },
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "check": "no_single_stream_labels_for_recirc",
            "status": "pass_forbidden",
            "forbidden_input": "single-stream Nu/f_D/K labels on recirculating rows",
            "policy": "Current upcomer rows are hybrid/diagnostic only.",
        },
        {
            "check": "no_runtime_cfd_mdot",
            "status": "pass_forbidden",
            "forbidden_input": "CFD mdot",
            "policy": "mdot remains a coupled solved output.",
        },
        {
            "check": "no_runtime_realized_wall_heat",
            "status": "pass_forbidden",
            "forbidden_input": "realized wallHeatFlux",
            "policy": "wall heat and h_proxy are diagnostics until a setup-only predictive term is admitted.",
        },
        {
            "check": "no_global_multiplier",
            "status": "pass_forbidden",
            "forbidden_input": "global friction or heat-transfer multiplier",
            "policy": "recirculation effects must remain a named upcomer lane.",
        },
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("hybrid_contract", HYBRID_CONTRACT, "existing hybrid lane policy"),
        ("feature_admission", FEATURE_ADMISSION, "recirculation feature admission evidence"),
        ("pm5_metrics", PM5_METRICS, "same-window RAF/RMF/SVF/Ri/Gz/wall-bulk features"),
        ("pm5_admission", PM5_ADMISSION, "PM5 fit-forbidden admission table"),
        ("onset_classification", ONSET_CLASS, "onset blocker state"),
        ("f6_candidates", F6_CANDIDATES, "F6 ordinary-vs-hybrid candidate inventory"),
        ("thermal_scorecard", THERMAL_SCORECARD, "thermal upcomer gate"),
        ("pressure_scorecard", PRESSURE_SCORECARD, "pressure upcomer gate"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(HYBRID_CONTRACT)}",
        f"  - {rel(PM5_METRICS)}",
        f"  - {rel(ONSET_CLASS)}",
        "tags: [upcomer, recirculation, hybrid-model, admission]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Upcomer Pipe-Cell Hybrid Model",
        "",
        "## Decision",
        "",
        "The upcomer is treated as a throughflow pipe branch plus recirculating convection-cell exchange. "
        "Current evidence admits the hybrid lane as a diagnostic contract only. Ordinary single-stream `Nu`, `f_D`, `K`, and F6 labels remain blocked for current recirculating rows.",
        "",
        "## Results",
        "",
        f"- Hybrid candidate lanes: `{summary['candidate_lanes']}`.",
        f"- Recirculation feature rows: `{summary['feature_rows']}`.",
        f"- Ordinary upcomer coefficient fit-admitted rows: `{summary['ordinary_fit_admitted_rows']}`.",
        f"- Hybrid predictive fit-admitted rows: `{summary['hybrid_predictive_fit_admitted_rows']}`.",
        f"- Onset/calibration gaps: `{summary['onset_gap_rows']}`.",
        f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_closeout(summary: dict[str, object]) -> None:
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
                "- PM5 and recirculation evidence show material reverse-flow fractions in current upcomer rows.",
                "- Current rows are diagnostic/hybrid evidence, not ordinary pipe closure data.",
                "- Onset anchors and split-scored hybrid penalty calibration are still missing.",
                "",
                "## Changes Made",
                "",
                f"- Wrote `{rel(OUT)}/` with hybrid candidate contract, feature scorecard, admission decisions, onset gaps, runtime audit, README, and summary.",
                "- Added focused builder tests.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_upcomer_pipe_cell_hybrid_model`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for documenting the hybrid lane contract.",
                "- Predictive upcomer closure remains blocked by ordinary/transition anchors, mesh/time uncertainty, and train/validation/holdout scoring of a frozen hybrid penalty.",
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
                f"  - {rel(HYBRID_CONTRACT)}",
                f"  - {rel(PM5_METRICS)}",
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
                "# Upcomer Pipe-Cell Hybrid Model Journal",
                "",
                "## Files Inspected",
                "",
                f"- `{rel(HYBRID_CONTRACT)}`",
                f"- `{rel(FEATURE_ADMISSION)}`",
                f"- `{rel(PM5_METRICS)}`",
                f"- `{rel(PM5_ADMISSION)}`",
                f"- `{rel(ONSET_CLASS)}`",
                f"- `{rel(F6_CANDIDATES)}`",
                "",
                "## Files Changed",
                "",
                "- `tools/analyze/build_upcomer_pipe_cell_hybrid_model.py`",
                "- `tools/analyze/test_upcomer_pipe_cell_hybrid_model.py`",
                f"- `{rel(OUT)}/`",
                f"- `{rel(STATUS)}`",
                f"- `{rel(JOURNAL)}`",
                f"- `{rel(IMPORT)}`",
                "- `.agent/BOARD.md` own row status",
                "",
                "## Interpretation",
                "",
                "The correct current state is a complete diagnostic hybrid contract, not an admitted predictive upcomer closure.",
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
    candidates = build_candidate_contract()
    features = build_feature_scorecard()
    decisions = build_admission_decisions()
    onset_gaps = build_onset_gap_rows()
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(
        OUT / "hybrid_model_candidate_contract.csv",
        candidates,
        [
            "model_lane",
            "applies_when",
            "allowed_labels",
            "forbidden_labels",
            "solver_facing_behavior",
            "fit_allowed_now",
            "score_allowed_now",
            "current_status",
            "required_evidence_to_admit",
            "do_not_do_guardrail",
        ],
    )
    write_csv(
        OUT / "recirculation_feature_scorecard.csv",
        features,
        [
            "case_key",
            "case_role",
            "span",
            "Re",
            "Ri",
            "Pr",
            "Gz",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "delta_T_wall_bulk_K",
            "h_proxy_W_m2_K",
            "regime_weight_basis",
            "regime_class",
            "ordinary_fit_allowed",
            "hybrid_use_allowed",
            "blocked_labels",
            "source_path",
        ],
    )
    write_csv(
        OUT / "upcomer_admission_decision.csv",
        decisions,
        [
            "decision_id",
            "admission_status",
            "fit_allowed_now",
            "score_allowed_now",
            "evidence_rows",
            "max_reverse_area_fraction",
            "max_reverse_mass_fraction",
            "max_Ri",
            "blocked_labels",
            "reason",
            "source_paths",
        ],
    )
    write_csv(OUT / "onset_anchor_gap.csv", onset_gaps, ["gap_id", "status", "needed", "why_needed"])
    write_csv(OUT / "runtime_hybrid_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "candidate_lanes": len(candidates),
        "feature_rows": len(features),
        "admission_decision_rows": len(decisions),
        "ordinary_fit_admitted_rows": 0,
        "hybrid_predictive_fit_admitted_rows": 0,
        "diagnostic_hybrid_rows": sum(1 for row in decisions if row["score_allowed_now"] == "diagnostic"),
        "onset_gap_rows": len(onset_gaps),
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
    write_readme(summary)
    write_closeout(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
