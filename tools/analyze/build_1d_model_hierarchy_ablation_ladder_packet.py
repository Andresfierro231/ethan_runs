#!/usr/bin/env python3
"""Build a thesis-facing 1D model hierarchy and ablation ladder packet."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-1D-MODEL-HIERARCHY-ABLATION-LADDER-PACKET-2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_model_hierarchy_ablation_ladder_packet")

SOURCES = {
    "master_scoreboard": Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/summary.json"),
    "setup_only_uq": Path("work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/summary.json"),
    "s12_thermal": Path("work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/summary.json"),
    "pressure_basis": Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/summary.json"),
    "recirc_onset": Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/summary.json"),
    "pm10_terminal": Path("work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/summary.json"),
    "sensor_projection": Path("work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/summary.json"),
    "amx1_handoff": Path("work_products/2026-07/2026-07-22/2026-07-22_1d_amx1_axial_mixing_fluid_api_handoff/summary.json"),
}


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_text(value: object) -> str:
    return "true" if bool(value) else "false"


def build(outdir: Path = OUTDIR) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    src = {name: read_json(path) for name, path in SOURCES.items()}

    ladder = [
        {
            "level": "L0",
            "model_or_gate": "setup-only runtime input contract",
            "adds": "geometry, setup BCs, property mode declarations, protected split guardrails",
            "evidence_state": src["setup_only_uq"].get("decision", "missing"),
            "admission_state": "contract_ready_not_scored",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "defines legal runtime envelope before any model-form claims",
            "next_gate": "train-only runtime execution/smoke under protected split",
            "source_key": "setup_only_uq",
        },
        {
            "level": "L1",
            "model_or_gate": "pressure/mdot root coupling",
            "adds": "pressure basis ladder, mdot coupling, F3/F6 comparison boundary",
            "evidence_state": src["pressure_basis"].get("decision", "missing"),
            "admission_state": "thesis_evidence_only_no_f6_admission",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "negative pressure residuals motivate basis separation and low-recirculation anchors",
            "next_gate": "low-recirculation pressure anchors with same-QOI UQ before F6 admission",
            "source_key": "pressure_basis",
        },
        {
            "level": "L2",
            "model_or_gate": "thermal residual ownership",
            "adds": "passive wall, test-section source, empirical correction, junction/stub disposition",
            "evidence_state": src["s12_thermal"].get("decision", "missing"),
            "admission_state": "s12_attempted_no_freeze",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "shows why no S12 freeze is allowed despite useful residual-owner evidence",
            "next_gate": "independent source/property release plus same-window pressure/thermal/energy residuals",
            "source_key": "s12_thermal",
        },
        {
            "level": "L3",
            "model_or_gate": "recirculation/exchange/onset lane",
            "adds": "reverse-flow proxies, PM10 terminal diagnostics, exchange/tau boundary",
            "evidence_state": src["recirc_onset"].get("decision", "missing"),
            "admission_state": "diagnostic_only_no_exchange_cell_coefficients",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "turns ordinary upcomer closure failure into model-form evidence",
            "next_gate": "same-window V_recirc, mdot_exchange, tau_recirc, Ri, Qwall, pressure residual, mesh/GCI",
            "source_key": "recirc_onset",
        },
        {
            "level": "L4",
            "model_or_gate": "TP/TW projection and thermal-development path",
            "adds": "score-only projection from 1D bulk/wall state to TP/TW observations",
            "evidence_state": src["sensor_projection"].get("decision", "missing"),
            "admission_state": "measurement_operator_defined_no_temperature_release",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "supports TP-first thermal-development investigation before TW correction",
            "next_gate": "physical/source-bounded bulk-to-TP offset proof",
            "source_key": "sensor_projection",
        },
        {
            "level": "L5",
            "model_or_gate": "axial mixing / AMX1 candidate lane",
            "adds": "Fluid API handoff review and smoke-based root ledger status",
            "evidence_state": src["amx1_handoff"].get("decision", "missing"),
            "admission_state": "no_new_amx1_expansion_no_freeze",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "documents why multiplier-style AMX1 tuning is not the next rigorous move",
            "next_gate": "signed local exchange direction and source-bounded exchange envelope",
            "source_key": "amx1_handoff",
        },
        {
            "level": "L6",
            "model_or_gate": "future blind holdout evidence",
            "adds": "PM10 Salt2/Salt4 +/-10Q terminal evidence with protected-use locks",
            "evidence_state": src["pm10_terminal"].get("disposition", "missing"),
            "admission_state": "terminal_evidence_only_score_after_independent_freeze",
            "train_fit_allowed": "no",
            "validation_holdout_external_score_allowed_now": "no",
            "final_predictive_score_values": 0,
            "thesis_use": "shows protected path status without leaking holdout evidence into development",
            "next_gate": "independently frozen candidate, then protected PM10 score",
            "source_key": "pm10_terminal",
        },
    ]
    write_csv(outdir / "model_hierarchy_ladder.csv", ladder)

    ablation = [
        {
            "ablation_id": "A0",
            "axis": "runtime legality",
            "negative_or_positive_result": "positive_contract",
            "finding": "setup-only UQ/source rows exist, but are screening priors not publication intervals",
            "scientific_interpretation": "model evaluation must start from legal inputs before adding physics",
            "candidate_freeze_allowed": "no",
            "source_key": "setup_only_uq",
        },
        {
            "ablation_id": "A1",
            "axis": "pressure",
            "negative_or_positive_result": "negative_admission",
            "finding": "F6/component-K rows remain unadmitted; low-recirculation anchors exist only as evidence needs",
            "scientific_interpretation": "pressure basis error is real, but not yet a fit-safe correction",
            "candidate_freeze_allowed": "no",
            "source_key": "pressure_basis",
        },
        {
            "ablation_id": "A2",
            "axis": "thermal residual ownership",
            "negative_or_positive_result": "negative_freeze",
            "finding": "S12-HIAX1, passive wall, test-section source, empirical correction, and junction/stub lanes do not freeze",
            "scientific_interpretation": "residual ownership is thesis-strength evidence because it prevents overclaiming",
            "candidate_freeze_allowed": "no",
            "source_key": "s12_thermal",
        },
        {
            "ablation_id": "A3",
            "axis": "recirculation exchange",
            "negative_or_positive_result": "diagnostic_positive_admission_negative",
            "finding": "recirculation proxies and PM10 terminal rows exist; exact closed recirculation fraction and mesh/GCI remain blocked",
            "scientific_interpretation": "ordinary pipe closure is disabled, but exchange-cell coefficients are not admitted",
            "candidate_freeze_allowed": "no",
            "source_key": "recirc_onset;pm10_terminal",
        },
        {
            "ablation_id": "A4",
            "axis": "temperature projection",
            "negative_or_positive_result": "promising_diagnostic",
            "finding": "TP projection path improves diagnostic context, but bulk-to-TP correction is not released",
            "scientific_interpretation": "pursue TP-first thermal development before TW correction",
            "candidate_freeze_allowed": "no",
            "source_key": "sensor_projection",
        },
        {
            "ablation_id": "A5",
            "axis": "axial mixing",
            "negative_or_positive_result": "negative_expansion",
            "finding": "AMX1 reviewed rows pass smoke/root ledgers, but zero forms are ready for Salt1-Salt4 expansion or freeze",
            "scientific_interpretation": "need source-bounded exchange evidence rather than multiplier-only tuning",
            "candidate_freeze_allowed": "no",
            "source_key": "amx1_handoff",
        },
    ]
    write_csv(outdir / "ablation_evidence_matrix.csv", ablation)

    prerequisites = [
        {
            "gate": "train_only_full_solve",
            "current_state": "not_performed_in_this_packet",
            "required_before_freeze": "run setup-only/legal candidate on train rows only",
            "release_allowed_now": "no",
        },
        {
            "gate": "attribution",
            "current_state": "partial_diagnostic_attribution_only",
            "required_before_freeze": "attribute mdot/TP/TW/all-probe/residual errors to legal model terms",
            "release_allowed_now": "no",
        },
        {
            "gate": "source_property_release",
            "current_state": "blocked",
            "required_before_freeze": "independent source/property/Qwall release with conservation and same-QOI UQ",
            "release_allowed_now": "no",
        },
        {
            "gate": "same_qoi_uq",
            "current_state": "partial_temporal_support_only",
            "required_before_freeze": "same-label mesh/GCI and same-window target-minus/target/target-plus QOIs",
            "release_allowed_now": "no",
        },
        {
            "gate": "freeze",
            "current_state": "no_candidate_frozen",
            "required_before_freeze": "complete train-only solve, attribution, runtime legality, and UQ gates",
            "release_allowed_now": "no",
        },
        {
            "gate": "validation_holdout_external_test",
            "current_state": "protected",
            "required_before_freeze": "only after independent freeze",
            "release_allowed_now": "no",
        },
    ]
    write_csv(outdir / "freeze_prerequisite_gate_table.csv", prerequisites)

    final_score = [
        {
            "score_surface": "train_final_candidate_score",
            "score_values_reported": 0,
            "allowed_now": "no",
            "reason": "no frozen predictive candidate exists",
        },
        {
            "score_surface": "validation_score",
            "score_values_reported": 0,
            "allowed_now": "no",
            "reason": "validation is protected until candidate freeze",
        },
        {
            "score_surface": "holdout_score",
            "score_values_reported": 0,
            "allowed_now": "no",
            "reason": "PM10 and PM5 rows remain protected future/blind evidence",
        },
        {
            "score_surface": "external_test_score",
            "score_values_reported": 0,
            "allowed_now": "no",
            "reason": "external-test scoring follows freeze only",
        },
    ]
    write_csv(outdir / "final_score_guardrail_table.csv", final_score)

    figures = [
        {
            "target_id": "FIG-HIER-01",
            "artifact": "model_hierarchy_ladder.csv",
            "caption_safe_claim": "The 1D model-form work now has a staged hierarchy from legal setup inputs through pressure, thermal, recirculation, projection, and protected holdout gates.",
            "required_caveat": "No row is a frozen predictive model or final score.",
        },
        {
            "target_id": "TAB-HIER-01",
            "artifact": "ablation_evidence_matrix.csv",
            "caption_safe_claim": "Negative ablations are scientific evidence: they identify which physical ownership paths are not yet legally admissible.",
            "required_caveat": "Diagnostic results must not be promoted to runtime inputs.",
        },
        {
            "target_id": "TAB-HIER-02",
            "artifact": "freeze_prerequisite_gate_table.csv",
            "caption_safe_claim": "The rigorous path remains train-only full solve, attribution, freeze, validation, holdout, external-test.",
            "required_caveat": "Protected rows stay untouched until freeze.",
        },
    ]
    write_csv(outdir / "figure_caption_targets.csv", figures)

    sources = [
        {"source_key": key, "path": str(path), "exists": bool_text(path.exists()), "read_only": "yes"}
        for key, path in SOURCES.items()
    ]
    write_csv(outdir / "source_manifest.csv", sources)

    guardrails = [
        {"guardrail": "native_output_mutation", "status": "none"},
        {"guardrail": "registry_or_admission_mutation", "status": "none"},
        {"guardrail": "scheduler_solver_sampler_harvest_uq_launch", "status": "none"},
        {"guardrail": "fit_or_model_selection", "status": "none"},
        {"guardrail": "validation_holdout_external_scoring", "status": "none"},
        {"guardrail": "source_property_release", "status": "none"},
        {"guardrail": "candidate_freeze", "status": "none"},
        {"guardrail": "fluid_or_external_edit", "status": "none"},
        {"guardrail": "latex_or_thesis_current_edit", "status": "none"},
        {"guardrail": "residual_absorbed_into_internal_nu", "status": "none"},
    ]
    write_csv(outdir / "no_mutation_guardrails.csv", guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "hierarchy_ablation_ladder_ready_no_freeze_no_score",
        "hierarchy_rows": len(ladder),
        "ablation_rows": len(ablation),
        "freeze_gate_rows": len(prerequisites),
        "figure_caption_target_rows": len(figures),
        "source_manifest_rows": len(sources),
        "final_predictive_score_values": sum(int(row["score_values_reported"]) for row in final_score),
        "candidate_freeze_allowed": False,
        "fit_or_model_selection": False,
        "validation_holdout_external_scoring": False,
        "source_property_release": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "residual_absorbed_into_internal_nu": False,
        "recommended_next_executable_unlock": "pressure_ladder_streamwise_maps_or_physical_bulk_to_TP_offset_proof_after_exact_row_claim",
    }
    write_json(outdir / "summary.json", summary)

    readme = f"""# 1D Model Hierarchy And Ablation Ladder Packet

Decision: `{summary['decision']}`.

This package assembles the current 1D thesis evidence into a staged hierarchy.
It reports no final predictive score values and freezes no candidate.

## Main Result

The defensible model-development path is still:

`train-only full solve -> attribution -> freeze -> validation -> holdout -> external-test`.

Current evidence is strong enough for thesis structure: setup-only runtime
legality, pressure-basis negative evidence, S12 thermal residual ownership,
recirculation/onset diagnostic evidence, TP/TW projection mapping, AMX1 handoff
boundaries, and PM10 future-holdout status. It is not strong enough to release
a source/property correction, ordinary upcomer closure, exchange-cell
coefficient, or final predictive score.

## Outputs

- `model_hierarchy_ladder.csv`
- `ablation_evidence_matrix.csv`
- `freeze_prerequisite_gate_table.csv`
- `final_score_guardrail_table.csv`
- `figure_caption_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
"""
    (outdir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args = parser.parse_args(argv)
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
