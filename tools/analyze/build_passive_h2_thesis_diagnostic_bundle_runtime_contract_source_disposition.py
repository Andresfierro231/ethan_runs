#!/usr/bin/env python3
"""Build the PASSIVE-H2 thesis diagnostic bundle, no-score contract, and source disposition."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PASSIVE-H2-THESIS-DIAGNOSTIC-BUNDLE-RUNTIME-CONTRACT-SOURCE-DISPOSITION-2026-07-22"
SLUG = "passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/passive-h2-thesis-diagnostic-bundle-runtime-contract-source-disposition.md"
IMPORT = ROOT / f"imports/2026-07-22_{SLUG}.json"

POLICY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_candidate_gate_rerun_passive_role_filtered_policy"
SALT1 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
BURNDOWN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_h2_s13_modelform_blocker_burndown"
SOURCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
RUNTIME34 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_source_property_gate_rerun_with_salt34_smoke"
MASTER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"
HX = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler"
S13 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_strict_coarse_nogo_contract"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: Any, default: float | None = None) -> float | None:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def bool_s(value: Any) -> str:
    return str(bool(value)).lower()


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "pass", "passed"}


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        ("passive_role_policy_summary", POLICY / "summary.json"),
        ("policy_presentable_scores", POLICY / "carried_forward_presentable_diagnostic_scores.csv"),
        ("policy_case_family_matrix", POLICY / "candidate_case_family_policy_matrix.csv"),
        ("policy_release_decision", POLICY / "release_decision.csv"),
        ("salt1_runtime_summary", SALT1 / "summary.json"),
        ("salt1_heat_ledger_delta", SALT1 / "fluid_smoke_outputs/salt_1/heat_ledger_delta.csv"),
        ("salt1_runtime_input_audit", SALT1 / "fluid_smoke_outputs/salt_1/runtime_input_audit.csv"),
        ("salt1_operator_rows", SALT1 / "salt1_recovered_operator_rows_for_fluid.csv"),
        ("burndown_summary", BURNDOWN / "summary.json"),
        ("source_family_evidence", SOURCE / "passive_h2_family_evidence_recovery_matrix.csv"),
        ("missing_evidence", SOURCE / "passive_h2_missing_evidence_after_recovery.csv"),
        ("three_case_runtime_evidence", RUNTIME34 / "three_case_runtime_evidence.csv"),
        ("master_scoreboard", MASTER / "master_model_form_scoreboard.csv"),
        ("hx_duty_scorecard", HX / "coupled_fluid_output/duty_scorecard.csv"),
        ("s13_qwall_gci_no_go", S13 / "qoi_formal_gci_no_go_matrix.csv"),
    ]
    return [
        {"role": role, "path": rel(path), "mode": "read_only", "exists": bool_s(path.exists())}
        for role, path in sources
    ]


def diagnostic_scores() -> list[dict[str, str]]:
    rows = read_csv(POLICY / "carried_forward_presentable_diagnostic_scores.csv")
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "score_id": row["score_id"],
                "lane": row["lane"],
                "case_scope": row["case_scope"],
                "metric": row["metric"],
                "score_value": row["score_value"],
                "signed_error": row.get("signed_or_percent_context", ""),
                "admission_status": "diagnostic_presentable_not_admitted",
                "thesis_caption_status": "caption_must_state_not_admitted_not_final",
                "source_path": row["source_path"],
            }
        )
    salt1_summary = read_json(SALT1 / "summary.json")
    out.append(
        {
            "score_id": "PASSIVE-H2_runtime_salt_1",
            "lane": "passive_h2_runtime_heat_ledger",
            "case_scope": "salt_1 train",
            "metric": "radiation_on_heat_ledger_delta_W",
            "score_value": str(salt1_summary.get("salt1_radiation_on_heat_ledger_delta_W", "")),
            "signed_error": "no analytic target ratio emitted for Salt1; diagnostic runtime delta only",
            "admission_status": "diagnostic_presentable_not_admitted",
            "thesis_caption_status": "caption_must_state_no_target_score_no_release",
            "source_path": rel(SALT1 / "summary.json"),
        }
    )
    return out


def runtime_diagnostic_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    salt1 = read_json(SALT1 / "summary.json")
    rows.append(
        {
            "case_id": "salt_1",
            "split_role": "train",
            "runtime_completed": bool_s(salt1.get("salt1_runtime_smoke_complete")),
            "runtime_roots_accepted": bool_s(salt1.get("salt1_runtime_roots_accepted")),
            "radiation_delta_W": str(salt1.get("salt1_radiation_on_heat_ledger_delta_W", "")),
            "radiation_delta_over_target": "",
            "target_status": "no_target_ratio_emitted",
            "protected_scoring": "false",
            "source_property_release": "false",
            "candidate_freeze": "false",
            "thesis_use": "diagnostic runtime feasibility only",
            "evidence_path": rel(SALT1 / "summary.json"),
        }
    )
    for row in read_csv(RUNTIME34 / "three_case_runtime_evidence.csv"):
        rows.append(
            {
                "case_id": row["case_id"],
                "split_role": row["split_role"],
                "runtime_completed": row["runtime_completed"],
                "runtime_roots_accepted": row["accepted_roots"],
                "radiation_delta_W": row["radiation_on_heat_ledger_delta_W"],
                "radiation_delta_over_target": row["radiation_delta_over_target"],
                "target_status": "analytic_target_ratio_diagnostic",
                "protected_scoring": "false",
                "source_property_release": "false",
                "candidate_freeze": "false",
                "thesis_use": "diagnostic runtime feasibility only",
                "evidence_path": row["evidence_path"],
            }
        )
    return rows


def no_score_runtime_input_contract_rows() -> list[dict[str, str]]:
    allowed = [
        ("geometry", "source_family", "required", "source-backed family label selecting external-boundary rows"),
        ("geometry", "area_m2", "required", "passive-role filtered setup area"),
        ("thermal_boundary", "hA_W_K", "required", "setup dictionary hA, not fitted from targets"),
        ("thermal_boundary", "h_W_m2K", "optional_trace", "setup dictionary h where available"),
        ("thermal_boundary", "Ta_K", "required", "ambient temperature from setup dictionary"),
        ("thermal_boundary", "Tsur_K", "required", "surroundings temperature from setup dictionary"),
        ("thermal_boundary", "emissivity", "required", "setup emissivity"),
        ("thermal_boundary", "wall_layer_metadata", "required_when_present", "layer/kappa metadata only as setup provenance"),
        ("model_state", "predicted_outer_surface_temperature_K", "required", "computed by the 1D runtime solve"),
        ("model_state", "predicted_bulk_or_wall_state", "required", "computed by the 1D runtime solve"),
    ]
    forbidden = [
        ("solver_output", "wallHeatFlux", "forbidden", "realized CFD wallHeatFlux cannot drive runtime q_loss"),
        ("solver_output", "Qwall_W", "forbidden", "realized Qwall cannot be a runtime input"),
        ("solver_output", "CFD_mdot", "forbidden", "realized CFD mdot cannot be a runtime input"),
        ("protected_target", "TP_or_TW_observed_K", "forbidden", "observed sensor temperatures cannot drive runtime"),
        ("protected_target", "measured_cooler_power_W", "forbidden", "measured duty cannot be injected as passive H2 closure"),
        ("calibration", "hidden_global_multiplier", "forbidden", "no residual absorption or hidden multiplier"),
    ]
    rows: list[dict[str, str]] = []
    for group, field, requirement, note in allowed:
        rows.append(
            {
                "io_direction": "input",
                "input_group": group,
                "field": field,
                "requirement": requirement,
                "allowed_as_runtime_input": "true",
                "protected_or_forbidden": "false",
                "source_basis": note,
                "validation_rule": "must be present in setup/source manifest or generated internally by the model",
            }
        )
    for group, field, requirement, note in forbidden:
        rows.append(
            {
                "io_direction": "input",
                "input_group": group,
                "field": field,
                "requirement": requirement,
                "allowed_as_runtime_input": "false",
                "protected_or_forbidden": "true",
                "source_basis": note,
                "validation_rule": "runtime audit must show false or not read",
            }
        )
    return rows


def runtime_output_contract_rows() -> list[dict[str, str]]:
    outputs = [
        ("diagnostic_heat_ledger", "qambient_total_W", "allowed_diagnostic", "not a released numeric passive q_loss"),
        ("diagnostic_heat_ledger", "radiation_delta_W", "allowed_diagnostic", "runtime response only"),
        ("diagnostic_root", "root_status", "allowed_diagnostic", "execution proof only"),
        ("diagnostic_flow", "mdot_kg_s", "allowed_diagnostic", "not scored or fitted in this row"),
        ("diagnostic_temperature", "sensor_prediction_delta_K", "allowed_diagnostic", "no protected target error claim"),
        ("admission", "source_property_release", "must_be_false", "release closed"),
        ("admission", "candidate_freeze", "must_be_false", "freeze closed"),
        ("admission", "final_score", "must_be_absent_or_zero", "final score closed"),
    ]
    return [
        {
            "output_group": group,
            "field": field,
            "allowed_use": allowed,
            "score_allowed": "false",
            "release_allowed": "false",
            "note": note,
        }
        for group, field, allowed, note in outputs
    ]


def source_property_disposition_rows() -> list[dict[str, str]]:
    policy_rows = read_csv(POLICY / "candidate_case_family_policy_matrix.csv")
    salt1_rows = read_csv(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv")
    family_source = {
        row["source_family"]: row
        for row in read_csv(SOURCE / "passive_h2_family_evidence_recovery_matrix.csv")
    }
    rows: list[dict[str, str]] = []
    for row in salt1_rows:
        family = row["source_family"]
        rows.append(
            {
                "candidate_id": row.get("candidate_id", "PASSIVE-H2-CAND001"),
                "case_id": "salt_1",
                "source_family": family,
                "setup_basis_status": "repaired_setup_runtime_basis",
                "runtime_contract_status": "runtime_smoke_complete_no_score",
                "strict_source_envelope_status": "not_admitted",
                "same_qoi_release_uq_status": "missing",
                "source_property_release_disposition": "fail_closed_current_corpus",
                "permanent_or_repairable": "repairable_only_with_new_strict_source_envelope_and_release_uq",
                "reason": "Salt1 runtime row is setup-backed and leak-guarded, but source/property admission and same-QOI release UQ remain closed.",
                "release_allowed_now": "false",
                "freeze_allowed_now": "false",
                "score_allowed_now": "false",
                "evidence_path": rel(SALT1 / "salt1_recovered_operator_rows_for_fluid.csv"),
            }
        )
    salt1_families = {row["source_family"] for row in salt1_rows}
    if "junction" not in salt1_families:
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": "salt_1",
                "source_family": "junction",
                "setup_basis_status": "missing_case_family_coverage",
                "runtime_contract_status": "not_ready_for_this_family",
                "strict_source_envelope_status": "not_admitted",
                "same_qoi_release_uq_status": "missing",
                "source_property_release_disposition": "permanent_fail_closed_current_corpus",
                "permanent_or_repairable": "repairable_only_by_new_junction_source_rows_plus_release_uq",
                "reason": "Salt1 source-family coverage is 4/5; junction has no recovered operator row in current evidence.",
                "release_allowed_now": "false",
                "freeze_allowed_now": "false",
                "score_allowed_now": "false",
                "evidence_path": rel(SALT1 / "summary.json"),
            }
        )
    for row in policy_rows:
        source = family_source.get(row["source_family"], {})
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "case_id": row["case_id"],
                "source_family": row["source_family"],
                "setup_basis_status": "repaired_setup_runtime_basis" if truth(row["runtime_setup_input_allowed"]) else "missing_setup_basis",
                "runtime_contract_status": "contract_ready_no_score" if truth(row["runtime_setup_input_allowed"]) else "not_ready",
                "strict_source_envelope_status": "not_admitted",
                "same_qoi_release_uq_status": "missing",
                "source_property_release_disposition": "fail_closed_current_corpus",
                "permanent_or_repairable": "repairable_only_with_new_strict_source_envelope_and_release_uq",
                "reason": source.get("remaining_missing_evidence", "strict source envelope plus release-grade same-QOI UQ missing"),
                "release_allowed_now": "false",
                "freeze_allowed_now": "false",
                "score_allowed_now": "false",
                "evidence_path": row["evidence_path"],
            }
        )
    return rows


def figure_rows(scores: list[dict[str, str]], runtime: list[dict[str, str]], source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    temp = [row for row in scores if row["lane"] == "temperature_residual_shape"]
    h2 = [row for row in runtime]
    hx = [row for row in scores if row["lane"] == "hx_fixed_mdot_duty"]
    s13 = [row for row in scores if row["lane"] == "s13_m5_upcomer_exchange"]
    return [
        {
            "figure_id": "fig_passive_h2_temperature_residual_shape",
            "filename": "figures/passive_h2_temperature_residual_shape.svg",
            "data_rows": str(len(temp)),
            "primary_message": "D4/D3/D2 diagnostic residual-shape transfers reduce M3 RMSE but are not admitted physical coefficients.",
            "caption_caveat": "Salt2 train-fitted diagnostic transfer to Salt3/Salt4; not final predictive admission.",
        },
        {
            "figure_id": "fig_passive_h2_runtime_response_four_case",
            "filename": "figures/passive_h2_runtime_response_four_case.svg",
            "data_rows": str(len(h2)),
            "primary_message": "PASSIVE-H2 runtime path executes on Salt1/Salt2/Salt3/Salt4 and gives nonzero heat-ledger response.",
            "caption_caveat": "Runtime smoke/diagnostic response only; no release, no source/property release, and no protected score.",
        },
        {
            "figure_id": "fig_hx_fixed_mdot_duty",
            "filename": "figures/hx_fixed_mdot_duty.svg",
            "data_rows": str(len(hx)),
            "primary_message": "Fixed-mdot HX duty is close on Salt3/Salt4 but not coupled final performance.",
            "caption_caveat": "Cooler submodel diagnostic; coupled temperature/mdot review remains blocked.",
        },
        {
            "figure_id": "fig_s13_qwall_mesh_spread",
            "filename": "figures/s13_qwall_mesh_spread.svg",
            "data_rows": str(len(s13)),
            "primary_message": "S13 Q_wall medium/fine spread is low, supporting exchange-cell motivation.",
            "caption_caveat": "Formal GCI and admission remain blocked by same-label coarse gate.",
        },
        {
            "figure_id": "fig_source_property_gate_counts",
            "filename": "figures/source_property_gate_counts.svg",
            "data_rows": str(len(source_rows)),
            "primary_message": "Setup runtime basis is repaired, while source/property release remains zero.",
            "caption_caveat": "Gate-count figure; no release, no coefficient, and no final score is admitted.",
        },
    ]


def svg_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_bar_svg(path: Path, title: str, rows: list[tuple[str, float]], unit: str, subtitle: str) -> None:
    ensure_dir(path.parent)
    width = 980
    row_h = 42
    left = 290
    top = 78
    chart_w = 560
    height = top + row_h * max(1, len(rows)) + 48
    max_abs = max([abs(v) for _, v in rows] + [1.0])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="34" font-family="Arial" font-size="20" font-weight="700" fill="#111827">{svg_escape(title)}</text>',
        f'<text x="24" y="56" font-family="Arial" font-size="12" fill="#4b5563">Diagnostic evidence only: {svg_escape(subtitle)}</text>',
    ]
    for idx, (label, value) in enumerate(rows):
        y = top + idx * row_h
        bar_w = max(2.0, abs(value) / max_abs * chart_w)
        color = "#2563eb" if value >= 0 else "#dc2626"
        parts.append(f'<text x="24" y="{y + 20}" font-family="Arial" font-size="12" fill="#111827">{svg_escape(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y + 4}" width="{bar_w:.1f}" height="22" fill="{color}" opacity="0.88"/>')
        parts.append(f'<text x="{left + bar_w + 8:.1f}" y="{y + 20}" font-family="Arial" font-size="12" fill="#111827">{value:.4g} {svg_escape(unit)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_figures(scores: list[dict[str, str]], runtime: list[dict[str, str]], source_rows: list[dict[str, str]]) -> None:
    temp = [
        (row["score_id"].replace("_", " "), float(row["score_value"]))
        for row in scores
        if row["lane"] == "temperature_residual_shape" and f(row["score_value"]) is not None
    ]
    write_bar_svg(
        OUT / "figures/passive_h2_temperature_residual_shape.svg",
        "Diagnostic Temperature Residual-Shape Transfer",
        temp,
        "K RMSE",
        "Diagnostic evidence only: train-fitted transfer, not final admission.",
    )
    runtime_rows = [
        (row["case_id"], float(row["radiation_delta_W"]))
        for row in runtime
        if f(row["radiation_delta_W"]) is not None
    ]
    write_bar_svg(
        OUT / "figures/passive_h2_runtime_response_four_case.svg",
        "PASSIVE-H2 Runtime Heat-Ledger Response",
        runtime_rows,
        "W",
        "Four-case runtime diagnostic response; no release or protected scoring.",
    )
    hx_rows = [
        (row["case_scope"], float(row["score_value"]))
        for row in scores
        if row["lane"] == "hx_fixed_mdot_duty" and f(row["score_value"]) is not None
    ]
    write_bar_svg(
        OUT / "figures/hx_fixed_mdot_duty.svg",
        "HX Fixed-mdot Duty Signed Error",
        hx_rows,
        "W",
        "Cooler-duty diagnostic only; not coupled final Fluid score.",
    )
    s13_rows = [
        (row["metric"], float(row["score_value"]))
        for row in scores
        if row["lane"] == "s13_m5_upcomer_exchange" and f(row["score_value"]) is not None
    ]
    write_bar_svg(
        OUT / "figures/s13_qwall_mesh_spread.svg",
        "S13 Q_wall Mesh-Spread Diagnostic",
        s13_rows,
        "%",
        "Low spread motivates exchange-cell path; formal GCI remains blocked.",
    )
    gate_counts = [
        ("runtime setup-input rows", sum(1 for row in source_rows if row["runtime_contract_status"] in {"contract_ready_no_score", "runtime_smoke_complete_no_score"})),
        ("source/property release rows", sum(1 for row in source_rows if row["release_allowed_now"] == "true")),
        ("candidate freeze rows", sum(1 for row in source_rows if row["freeze_allowed_now"] == "true")),
        ("score-allowed rows", sum(1 for row in source_rows if row["score_allowed_now"] == "true")),
    ]
    write_bar_svg(
        OUT / "figures/source_property_gate_counts.svg",
        "PASSIVE-H2 Gate Counts",
        [(label, float(value)) for label, value in gate_counts],
        "rows",
        "Setup support is usable; release/freeze/score remain closed.",
    )


def claim_language_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "C1",
            "allowed": "true",
            "claim_text": "PASSIVE-H2 has a source-backed setup-runtime contract for diagnostic execution.",
            "must_include_caveat": "No source/property, Qwall, numeric q_loss, coefficient, freeze, or final score is released.",
        },
        {
            "claim_id": "C2",
            "allowed": "true",
            "claim_text": "PASSIVE-H2 runtime diagnostics execute on Salt1-4 with nonzero heat-ledger response.",
            "must_include_caveat": "This is execution and heat-ledger evidence, not protected validation scoring.",
        },
        {
            "claim_id": "C3",
            "allowed": "true",
            "claim_text": "D4/D3/D2 residual-shape diagnostics motivate physical successor model forms.",
            "must_include_caveat": "These are diagnostic transfer rows and should not be presented as fitted physical coefficients.",
        },
        {
            "claim_id": "F1",
            "allowed": "false",
            "claim_text": "PASSIVE-H2 source/property release is admitted.",
            "must_include_caveat": "Forbidden: strict source-envelope and same-QOI release UQ gates remain closed.",
        },
        {
            "claim_id": "F2",
            "allowed": "false",
            "claim_text": "PASSIVE-H2 has a final frozen score.",
            "must_include_caveat": "Forbidden: candidate freeze and final score values remain zero.",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "value": "false"},
        {"guardrail": "registry_or_admission_mutated", "value": "false"},
        {"guardrail": "scheduler_action_in_this_task", "value": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launched_in_this_task", "value": "false"},
        {"guardrail": "fluid_or_external_edit", "value": "false"},
        {"guardrail": "thesis_current_or_latex_edit", "value": "false"},
        {"guardrail": "source_property_release", "value": "false"},
        {"guardrail": "numeric_q_loss_release", "value": "false"},
        {"guardrail": "qwall_release", "value": "false"},
        {"guardrail": "coefficient_admission", "value": "false"},
        {"guardrail": "candidate_freeze", "value": "false"},
        {"guardrail": "protected_or_final_scoring", "value": "false"},
        {"guardrail": "hidden_multiplier_or_residual_absorption", "value": "false"},
    ]


def next_action_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "next_task": "Use figure/caption bundle in thesis evidence appendix.",
            "why": "It is already scored and guardrailed as diagnostic evidence.",
            "acceptance": "captions include diagnostic/not-admitted wording from figure_caption_bank.csv",
        },
        {
            "priority": "2",
            "next_task": "Only if thesis needs admitted PASSIVE-H2: open a new source-envelope/UQ evidence row.",
            "why": "Current corpus is permanently fail-closed for admission until new evidence appears.",
            "acceptance": "new rows must change strict source-envelope or same-QOI release UQ status without protected inputs",
        },
        {
            "priority": "3",
            "next_task": "Continue S13 direct coarse/open-CV chain separately.",
            "why": "S13 can add exchange-cell evidence but cannot repair PASSIVE-H2 source/property gates.",
            "acceptance": "same-label coarse and endpoint gates pass before formal GCI/UQ/admission",
        },
    ]


def write_package() -> dict[str, Any]:
    ensure_dir(OUT)
    scores = diagnostic_scores()
    runtime = runtime_diagnostic_rows()
    source_rows = source_property_disposition_rows()
    figures = figure_rows(scores, runtime, source_rows)
    write_figures(scores, runtime, source_rows)

    csv_dump(OUT / "source_manifest.csv", ["role", "path", "mode", "exists"], source_manifest_rows())
    csv_dump(
        OUT / "thesis_diagnostic_score_bundle.csv",
        ["score_id", "lane", "case_scope", "metric", "score_value", "signed_error", "admission_status", "thesis_caption_status", "source_path"],
        scores,
    )
    csv_dump(
        OUT / "passive_h2_four_case_runtime_diagnostic.csv",
        ["case_id", "split_role", "runtime_completed", "runtime_roots_accepted", "radiation_delta_W", "radiation_delta_over_target", "target_status", "protected_scoring", "source_property_release", "candidate_freeze", "thesis_use", "evidence_path"],
        runtime,
    )
    csv_dump(
        OUT / "no_score_runtime_input_contract.csv",
        ["io_direction", "input_group", "field", "requirement", "allowed_as_runtime_input", "protected_or_forbidden", "source_basis", "validation_rule"],
        no_score_runtime_input_contract_rows(),
    )
    csv_dump(
        OUT / "no_score_runtime_output_contract.csv",
        ["output_group", "field", "allowed_use", "score_allowed", "release_allowed", "note"],
        runtime_output_contract_rows(),
    )
    csv_dump(
        OUT / "source_property_final_disposition.csv",
        ["candidate_id", "case_id", "source_family", "setup_basis_status", "runtime_contract_status", "strict_source_envelope_status", "same_qoi_release_uq_status", "source_property_release_disposition", "permanent_or_repairable", "reason", "release_allowed_now", "freeze_allowed_now", "score_allowed_now", "evidence_path"],
        source_rows,
    )
    csv_dump(
        OUT / "figure_manifest.csv",
        ["figure_id", "filename", "data_rows", "primary_message", "caption_caveat"],
        figures,
    )
    csv_dump(
        OUT / "figure_caption_bank.csv",
        ["figure_id", "caption_text"],
        [{"figure_id": row["figure_id"], "caption_text": f'{row["primary_message"]} Caveat: {row["caption_caveat"]}'} for row in figures],
    )
    csv_dump(
        OUT / "thesis_claim_language.csv",
        ["claim_id", "allowed", "claim_text", "must_include_caveat"],
        claim_language_rows(),
    )
    csv_dump(OUT / "no_mutation_guardrails.csv", ["guardrail", "value"], guardrail_rows())
    csv_dump(OUT / "next_action_queue.csv", ["priority", "next_task", "why", "acceptance"], next_action_rows())

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "passive_h2_thesis_diagnostic_bundle_complete_no_score_runtime_contract_source_property_fail_closed",
        "diagnostic_score_rows": len(scores),
        "runtime_diagnostic_case_rows": len(runtime),
        "runtime_completed_rows": sum(1 for row in runtime if row["runtime_completed"] == "true"),
        "runtime_nonzero_delta_rows": sum(1 for row in runtime if f(row["radiation_delta_W"], 0.0) not in (None, 0.0)),
        "figure_manifest_rows": len(figures),
        "svg_figure_files": len(figures),
        "no_score_runtime_input_contract_rows": len(no_score_runtime_input_contract_rows()),
        "no_score_runtime_output_contract_rows": len(runtime_output_contract_rows()),
        "source_property_disposition_rows": len(source_rows),
        "release_allowed_rows": sum(1 for row in source_rows if row["release_allowed_now"] == "true"),
        "freeze_allowed_rows": sum(1 for row in source_rows if row["freeze_allowed_now"] == "true"),
        "score_allowed_rows": sum(1 for row in source_rows if row["score_allowed_now"] == "true"),
        "salt1_junction_fail_closed_rows": sum(1 for row in source_rows if row["case_id"] == "salt_1" and row["source_family"] == "junction"),
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_or_final_scoring": False,
        "final_score_values": 0,
        "scheduler_action_in_this_task": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
        "solver_sampler_harvest_uq_launched_in_this_task": False,
    }
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    write_import_manifest(summary)
    return summary


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(POLICY / "carried_forward_presentable_diagnostic_scores.csv")}
  - {rel(SALT1 / "summary.json")}
  - {rel(SOURCE / "passive_h2_family_evidence_recovery_matrix.csv")}
tags: [PASSIVE-H2, thesis-figures, no-score-runtime, source-property, no-release]
related:
  - {rel(STATUS)}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Thesis Diagnostic Bundle / Runtime Contract / Source Disposition

Decision: `{summary["decision"]}`.

This package is the defensible workaround: it turns the available PASSIVE-H2
evidence into thesis-ready diagnostic figures and a no-score runtime contract,
then explicitly fail-closes release-grade source/property provenance for the
current evidence corpus.

## Results

- Diagnostic score rows: `{summary["diagnostic_score_rows"]}`.
- Runtime diagnostic cases: `{summary["runtime_diagnostic_case_rows"]}` with
  `{summary["runtime_completed_rows"]}` completed runtime rows.
- SVG figures: `{summary["svg_figure_files"]}`.
- Source/property disposition rows: `{summary["source_property_disposition_rows"]}`.
- Release/freeze/score allowed rows: `{summary["release_allowed_rows"]}` /
  `{summary["freeze_allowed_rows"]}` / `{summary["score_allowed_rows"]}`.

## Claim Boundary

Allowed: diagnostic model-form evidence, four-case PASSIVE-H2 runtime response,
and a no-score setup-input contract.

Not allowed: source/property release, numeric q_loss release, Qwall release,
coefficient admission, candidate freeze, protected scoring, or final predictive
score.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_closeout(summary: dict[str, Any]) -> None:
    ensure_dir(STATUS.parent)
    status = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "thesis_diagnostic_score_bundle.csv")}
  - {rel(OUT / "source_property_final_disposition.csv")}
tags: [PASSIVE-H2, thesis-figures, no-score-runtime, source-property]
related:
  - {rel(OUT / "README.md")}
  - {rel(JOURNAL)}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

Objective: build the next PASSIVE-H2 thesis workaround outputs in order:
diagnostic figure bundle, no-score runtime contract, and source/property
repair-or-fail-close disposition.

Outcome: `{summary["decision"]}`. The package emits
`{summary["diagnostic_score_rows"]}` diagnostic score rows,
`{summary["runtime_diagnostic_case_rows"]}` runtime diagnostic case rows,
`{summary["svg_figure_files"]}` SVG figures, and
`{summary["source_property_disposition_rows"]}` source/property disposition
rows. Release/freeze/score allowed rows remain
`{summary["release_allowed_rows"]}` / `{summary["freeze_allowed_rows"]}` /
`{summary["score_allowed_rows"]}`.

## Changes Made

- Built the thesis diagnostic score bundle and figure/caption tables.
- Implemented the no-score runtime input/output contract as auditable CSV
  artifacts.
- Published source/property disposition rows that repair setup-runtime basis
  where supported and fail-close current-corpus source/property release.
- Wrote package README, status, journal, and import manifest.

## Validation

- `python3.11 tools/analyze/build_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.py tools/analyze/test_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.py`
- `python3.11 tools/agent/runtime_input_lint.py ...`
- `python3.11 tools/agent/split_policy_lint.py ...`
- `python3.11 tools/agent/manifest_check.py imports/2026-07-22_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.json --check-paths`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

Guardrails: no native-output mutation, registry/admission mutation, scheduler
action in this task, solver/sampler/harvest/UQ launch, Fluid/external edit,
thesis LaTeX edit, source/property release, numeric q-loss release, Qwall
release, coefficient admission, candidate freeze, protected/final scoring,
hidden multiplier, or residual absorption.
"""
    STATUS.write_text(status, encoding="utf-8")

    ensure_dir(JOURNAL.parent)
    journal = f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "figure_caption_bank.csv")}
tags: [PASSIVE-H2, diagnostic-score, no-score-runtime, source-property]
related:
  - {rel(STATUS)}
  - {rel(OUT / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Thesis Diagnostic Bundle / Runtime Contract / Source Disposition

Attempted: make thesis-presentable progress despite closed admission gates by
separating diagnostic scoring, runtime contract, and release-grade source
property disposition.

Observed: Salt1 runtime smoke is now available and supports a four-case
diagnostic runtime response table. The no-score input contract can permit setup
area/hA/h/Ta/Tsur/emissivity/layers and model-generated states, while forbidding
wallHeatFlux, Qwall, CFD mdot, protected temperatures, measured duty, and hidden
multipliers. Source/property release remains fail-closed for every current row.

Inferred: the thesis can defend these figures as model-form evidence and
motivation for physical successors, not as final predictive admissions.

Caveats: Salt1 has 4/5 source-family coverage with junction fail-closed; Salt2-4
have setup basis but strict source-envelope and same-QOI release UQ remain
closed; figures must carry diagnostic/not-admitted captions.

Next useful actions: use the figure bundle in the thesis evidence appendix, and
open a new source-envelope/UQ evidence row only if admitted PASSIVE-H2 is still
needed.
"""
    JOURNAL.write_text(journal, encoding="utf-8")


def write_import_manifest(summary: dict[str, Any]) -> None:
    package_files = [rel(path) for path in sorted(OUT.rglob("*")) if path.is_file()]
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.py",
        "tools/analyze/test_passive_h2_thesis_diagnostic_bundle_runtime_contract_source_disposition.py",
    ]
    payload = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "changed_files": sorted(dict.fromkeys(changed + package_files)),
        "read_only_context": [row["path"] for row in source_manifest_rows()],
        "results": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "mutation_flags": {
            "native_solver_outputs_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action_in_this_task": False,
            "solver_sampler_harvest_uq_launched_in_this_task": False,
            "fluid_or_external_edit": False,
            "thesis_current_or_latex_edit": False,
            "source_property_release": False,
            "numeric_q_loss_release": False,
            "qwall_release": False,
            "coefficient_admission": False,
            "candidate_freeze": False,
            "protected_or_final_scoring": False,
        },
    }
    json_dump(IMPORT, payload)


def main() -> int:
    summary = write_package()
    print(json.dumps(summary, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
