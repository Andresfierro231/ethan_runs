#!/usr/bin/env python3
"""Build the S12 thermal residual candidate disposition thesis package."""

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

TASK_ID = "TODO-S12-THERMAL-RESIDUAL-CANDIDATE-DISPOSITION-AND-THESIS-PANELS-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels"
)
S12_SCORE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score"
)
S12_OWNER = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s8_s12_thermal_residual_ownership_gate"
)
S12_SHAPE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate"
)
N3 = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_n3_thermal_residual_owner_train_ablation"
)


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_rows_by_family() -> dict[str, dict[str, str]]:
    return {row["metric_family"]: row for row in read_csv(S12_SCORE / "finite_train_metric_table.csv")}


def candidate_disposition_rows() -> list[dict[str, str]]:
    metrics = metric_rows_by_family()
    all_probe = metrics["all_probe"]
    tp = metrics["TP"]
    tw = metrics["TW"]
    mdot = metrics["mdot"]
    pressure = metrics["pressure_root"]
    return [
        {
            "candidate_or_lane": "S12-HIAX1",
            "disposition": "not_frozen",
            "evidence_role": "plausible_owner_but_not_candidate_release",
            "train_metric_context": (
                f"all_probe_RMSE_K={all_probe['rmse_K']}; TP_RMSE_K={tp['rmse_K']}; "
                f"TW_RMSE_K={tw['rmse_K']}; mdot_residual_kg_s={mdot['residual_mdot_kg_s']}; "
                f"pressure_residual_Pa={pressure['pressure_residual_Pa']}"
            ),
            "why_not_frozen": (
                "finite train precursor metrics exist, but exchange-state, same-QOI UQ, "
                "source/property release, and attribution-freeze gates fail"
            ),
            "runtime_legality": "contract_only_not_released",
            "source_property_release": "false",
            "validation_holdout_external_scored": "false",
            "final_score_released": "false",
            "s11_s15_s6_trigger": "false",
            "thesis_use": "lead S12 negative-result candidate row",
        },
        {
            "candidate_or_lane": "passive_wall",
            "disposition": "evidence_only",
            "evidence_role": "plausible_needs_source_basis",
            "train_metric_context": "global_tw5_improvement_K=51.6337 from N3 ablation context",
            "why_not_frozen": "passive source families remain unreleased; source basis is not sufficient for admission",
            "runtime_legality": "not_released",
            "source_property_release": "false",
            "validation_holdout_external_scored": "false",
            "final_score_released": "false",
            "s11_s15_s6_trigger": "false",
            "thesis_use": "explain why another passive wall selector is not the next S12 repair",
        },
        {
            "candidate_or_lane": "test_section_source",
            "disposition": "evidence_only",
            "evidence_role": "partial_local_response",
            "train_metric_context": "all_mae_delta_K=0.06910055550108041; TP/TW response is mixed",
            "why_not_frozen": "partial improvement and worsening are both observed; no released physical model form",
            "runtime_legality": "not_released",
            "source_property_release": "false",
            "validation_holdout_external_scored": "false",
            "final_score_released": "false",
            "s11_s15_s6_trigger": "false",
            "thesis_use": "support thermal residual ownership caveat",
        },
        {
            "candidate_or_lane": "empirical_correction",
            "disposition": "diagnostic_only",
            "evidence_role": "diagnostic_residual_layer",
            "train_metric_context": "empirical_train_MAE_K=7.2809; transfer_MAE_K=13.3245",
            "why_not_frozen": "fit is not physical closure admission and was not used for model selection",
            "runtime_legality": "not_released",
            "source_property_release": "false",
            "validation_holdout_external_scored": "false",
            "final_score_released": "false",
            "s11_s15_s6_trigger": "false",
            "thesis_use": "show residual reducibility without claiming physics",
        },
        {
            "candidate_or_lane": "junction_stub",
            "disposition": "blocked",
            "evidence_role": "unresolved_owner",
            "train_metric_context": "no independent source/property basis",
            "why_not_frozen": "unowned residual/stub lane lacks independent basis and runtime release",
            "runtime_legality": "not_released",
            "source_property_release": "false",
            "validation_holdout_external_scored": "false",
            "final_score_released": "false",
            "s11_s15_s6_trigger": "false",
            "thesis_use": "name remaining blocker without hiding it in internal Nu",
        },
    ]


def residual_owner_waterfall_rows() -> list[dict[str, str]]:
    residuals = read_csv(S12_SHAPE / "residual_quantification.csv")
    owner = {row["candidate_id"]: row for row in read_csv(S12_OWNER / "residual_owner_matrix.csv")}
    rows: list[dict[str, str]] = []
    for row in residuals:
        rows.append(
            {
                "waterfall_step": row["residual_id"],
                "sensor": row["sensor"],
                "segment": row["segment"],
                "mean_m3_abs_error_K": row["mean_m3_abs_error_K"],
                "mean_prior_candidate_abs_error_K": row["mean_prior_candidate_abs_error_K"],
                "mean_prior_candidate_excess_vs_m3_K": row["mean_prior_candidate_excess_vs_m3_K"],
                "prior_candidate_families_failed": row["prior_candidate_families_failed"],
                "fail_fraction": row["fail_fraction"],
                "owner_inference": "heated_incline_upcomer_exchange_shape",
                "required_physics": row["required_physics"],
                "admission_status": "not_admitted",
            }
        )
    for candidate_id in ("PASSIVE-H2-CAND001", "SETUP-KNOWN-HEATER-SOURCE", "EMPIRICAL-LEG-BIAS"):
        source = owner[candidate_id]
        rows.append(
            {
                "waterfall_step": candidate_id,
                "sensor": "TW5/TW6",
                "segment": source["owner_family"],
                "mean_m3_abs_error_K": "",
                "mean_prior_candidate_abs_error_K": "",
                "mean_prior_candidate_excess_vs_m3_K": "",
                "prior_candidate_families_failed": "",
                "fail_fraction": "",
                "owner_inference": source["positive_evidence"],
                "required_physics": source["blocking_evidence"],
                "admission_status": source["gate_status"],
            }
        )
    return rows


def runtime_legality_rows() -> list[dict[str, str]]:
    n3_rows = {row["lane"]: row for row in read_csv(N3 / "runtime_legality_matrix.csv")}
    disposition_map = {row["candidate_or_lane"]: row for row in candidate_disposition_rows()}
    map_lanes = {
        "S12-HIAX1": "external_boundary",
        "passive_wall": "passive_wall",
        "test_section_source": "test_section_source",
        "empirical_correction": "empirical_diagnostic",
        "junction_stub": "junction_stub",
    }
    rows: list[dict[str, str]] = []
    for candidate, lane in map_lanes.items():
        n3 = n3_rows[lane]
        disp = disposition_map[candidate]
        rows.append(
            {
                "candidate_or_lane": candidate,
                "runtime_legal": n3["runtime_legal"],
                "source_property_released": n3["source_property_released"],
                "admission_allowed": n3["admission_allowed"],
                "validation_holdout_external_scored": disp["validation_holdout_external_scored"],
                "final_score_released": disp["final_score_released"],
                "residual_absorbed_into_internal_Nu": "false",
                "reason": n3["reason"],
            }
        )
    return rows


def train_metric_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(S12_SCORE / "finite_train_metric_table.csv"):
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "split_role": row["split_role"],
                "metric_family": row["metric_family"],
                "target_count": row["target_count"],
                "finite_count": row["finite_count"],
                "mae_K": row["mae_K"],
                "rmse_K": row["rmse_K"],
                "mean_bias_K": row["mean_bias_K"],
                "max_abs_K": row["max_abs_K"],
                "predicted_mdot_kg_s": row["predicted_mdot_kg_s"],
                "reference_mdot_kg_s": row["reference_mdot_kg_s"],
                "residual_mdot_kg_s": row["residual_mdot_kg_s"],
                "pressure_residual_Pa": row["pressure_residual_Pa"],
                "metric_use": "train_only_context_not_freeze_or_final_score",
            }
        )
    return rows


def no_freeze_rationale_rows() -> list[dict[str, str]]:
    phasef = read_csv(S12_SCORE / "s12_hiax1_train_score_gate.csv")
    thermal = read_csv(S12_OWNER / "candidate_gate_decision.csv")
    rows: list[dict[str, str]] = []
    for row in phasef:
        rows.append(
            {
                "source": "S12-HIAX1_train_score_gate",
                "gate": row["gate"],
                "status": row["status"],
                "blocks_freeze": "true" if row["status"] == "fail" else "false",
                "evidence": row["evidence"],
            }
        )
    for row in thermal:
        rows.append(
            {
                "source": "thermal_residual_ownership_gate",
                "gate": row["gate"],
                "status": row["status"],
                "blocks_freeze": "true" if row["status"] in {"fail", "needs_more_physical_basis"} else "false",
                "evidence": row["evidence"],
            }
        )
    return rows


def claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "S12-C1",
            "claim": "S12-HIAX1 remains the best named physical residual-owner hypothesis for TW5/TW6.",
            "allowed": "true",
            "basis": rel(S12_SHAPE / "candidate_contract.csv"),
        },
        {
            "claim_id": "S12-C2",
            "claim": "Finite train-only precursor metrics exist for S12-HIAX1.",
            "allowed": "true",
            "basis": rel(S12_SCORE / "finite_train_metric_table.csv"),
        },
        {
            "claim_id": "S12-C3",
            "claim": "No S12 candidate can be frozen or admitted from the current evidence.",
            "allowed": "true",
            "basis": rel(N3 / "summary.json"),
        },
        {
            "claim_id": "S12-X1",
            "claim": "S12-HIAX1 is an implemented frozen candidate or final predictive score.",
            "allowed": "false",
            "basis": rel(S12_SCORE / "freeze_decision.csv"),
        },
        {
            "claim_id": "S12-X2",
            "claim": "Empirical correction coefficients are physical thermal closures.",
            "allowed": "false",
            "basis": rel(N3 / "thermal_residual_ablation_table.csv"),
        },
        {
            "claim_id": "S12-X3",
            "claim": "The remaining S12 residual can be hidden inside internal Nu.",
            "allowed": "false",
            "basis": rel(S12_OWNER / "runtime_leakage_audit.csv"),
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read completed packages only"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "fluid_solve_or_external_edit", "changed": "false", "policy": "no Fluid solve or external edit"},
        {"guard_id": "validation_holdout_external_scoring", "changed": "false", "policy": "no protected scoring"},
        {"guard_id": "fitting_or_model_selection", "changed": "false", "policy": "no fit or model selection"},
        {"guard_id": "source_property_release", "changed": "false", "policy": "no source/property release"},
        {"guard_id": "final_score_or_freeze", "changed": "false", "policy": "no final score or candidate freeze"},
        {"guard_id": "downstream_trigger", "changed": "false", "policy": "no S11/S12/S13/S15/S6 trigger"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "forbidden"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (S12_SCORE / "finite_train_metric_table.csv", "S12-HIAX1 train-only finite metrics"),
        (S12_SCORE / "s12_hiax1_train_score_gate.csv", "S12-HIAX1 freeze gate blockers"),
        (S12_OWNER / "residual_owner_matrix.csv", "thermal residual ownership families"),
        (S12_OWNER / "candidate_gate_decision.csv", "overall thermal candidate gate"),
        (S12_SHAPE / "residual_quantification.csv", "TW5/TW6 residual quantification"),
        (S12_SHAPE / "admission_gate_matrix.csv", "S12-HIAX1 admission blockers"),
        (N3 / "thermal_residual_ablation_table.csv", "train-only ablation lane disposition"),
        (N3 / "runtime_legality_matrix.csv", "runtime legality and admission matrix"),
        (N3 / "summary.json", "N3 zero candidate-release decision"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_waterfall_svg(out: Path, rows: list[dict[str, str]]) -> str:
    svg_dir = ensure_dir(out / "figures" / "svg")
    path = svg_dir / "s12_residual_owner_waterfall.svg"
    chart_rows = [row for row in rows if row["mean_prior_candidate_excess_vs_m3_K"]]
    max_value = max(float(row["mean_prior_candidate_excess_vs_m3_K"]) for row in chart_rows)
    width = 760
    height = 260
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="30" y="30" font-family="Arial, sans-serif" font-size="18" font-weight="700">S12 residual-owner waterfall</text>',
    ]
    y = 70
    for row in chart_rows:
        value = float(row["mean_prior_candidate_excess_vs_m3_K"])
        bar_w = 500 * value / max_value
        parts.append(f'<text x="30" y="{y + 16}" font-family="Arial, sans-serif" font-size="13">{row["sensor"]}</text>')
        parts.append(f'<rect x="120" y="{y}" width="{bar_w:.1f}" height="24" fill="#b0413e"/>')
        parts.append(
            f'<text x="{130 + bar_w:.1f}" y="{y + 16}" font-family="Arial, sans-serif" font-size="12">{value:.2f} K excess vs M3</text>'
        )
        y += 45
    parts.append('<text x="30" y="190" font-family="Arial, sans-serif" font-size="12">Both dominant residuals point to heated-incline/upcomer exchange shape; no S12 candidate is frozen.</text>')
    parts.append('<text x="30" y="212" font-family="Arial, sans-serif" font-size="12">Use as thesis evidence only: no source/property release, no protected scoring, no internal Nu absorption.</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return rel(path)


def write_readme(out: Path, summary: dict[str, Any], svg_path: str) -> None:
    text = f"""---
provenance:
  - {rel(S12_SCORE / "finite_train_metric_table.csv")}
  - {rel(S12_OWNER / "residual_owner_matrix.csv")}
  - {rel(S12_SHAPE / "residual_quantification.csv")}
  - {rel(N3 / "thermal_residual_ablation_table.csv")}
tags: [s12, thermal-residual, thesis-panels, no-freeze]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - operational_notes/07-26/22/2026-07-22_S12_THERMAL_RESIDUAL_CANDIDATE_DISPOSITION_AND_THESIS_PANELS.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Figures / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S12 Thermal Residual Candidate Disposition And Thesis Panels

Decision: `{summary["decision"]}`.

This package turns the S12 thermal residual-owner work into thesis-strength
negative evidence. It does not freeze or admit a candidate.

- candidate disposition rows: `{summary["candidate_disposition_rows"]}`
- train-only metric rows: `{summary["train_metric_rows"]}`
- no-freeze blocker rows: `{summary["no_freeze_blocker_rows"]}`
- candidate-reviewable rows: `{summary["candidate_reviewable_rows"]}`
- validation/holdout/external scored rows: `{summary["validation_holdout_external_rows_scored"]}`
- final score values: `{summary["final_score_values"]}`
- figure: `{svg_path}`

Use `thesis_panel_handoff.md` for chapter-facing table, figure, and caption
instructions.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_thesis_handoff(out: Path, svg_path: str) -> None:
    text = f"""---
provenance:
  - {rel(out / "candidate_disposition_table.csv")}
  - {rel(out / "residual_owner_waterfall_table.csv")}
  - {rel(out / "runtime_legality_matrix.csv")}
  - {rel(out / "no_freeze_rationale.csv")}
tags: [s12, thesis-panel, thermal-residual, no-freeze]
related:
  - {rel(out / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Writer / Reviewer
type: report
status: complete
---
# Thesis Panel Handoff: S12 Thermal Residual Candidate Disposition

## Use In Thesis

Use this package to state that S12 was attempted rigorously and produced a
negative candidate-release result.

## Tables

- `candidate_disposition_table.csv`: S12-HIAX1 not frozen; passive wall and
  test-section source evidence-only; empirical correction diagnostic-only;
  junction/stub blocked.
- `residual_owner_waterfall_table.csv`: TW5/TW6 residual-owner evidence.
- `runtime_legality_matrix.csv`: all lanes remain not released for runtime use.
- `train_only_metric_context.csv`: finite train-only context for S12-HIAX1.
- `no_freeze_rationale.csv`: exact gates that block freeze/admission.

## Figure

Figure source: `{svg_path}`.

Caption: S12 thermal residual-owner disposition. The dominant TW5/TW6 residuals
identify a heated-incline/upcomer exchange-shape hypothesis, and finite
train-only S12-HIAX1 precursor metrics exist. However, exchange-state,
same-QOI UQ, source/property release, and attribution-freeze gates remain
closed, so no S12 candidate is frozen or admitted.

## Forbidden Claims

Do not claim validation, holdout, or external-test scoring. Do not claim
source/property release, final score, candidate freeze, closure admission, or
residual absorption into internal Nu.
"""
    (out / "thesis_panel_handoff.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    disposition = candidate_disposition_rows()
    waterfall = residual_owner_waterfall_rows()
    runtime = runtime_legality_rows()
    train = train_metric_context_rows()
    no_freeze = no_freeze_rationale_rows()
    claims = claim_boundary_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()
    svg_path = write_waterfall_svg(out, waterfall)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "s12_attempted_rigorously_no_candidate_freeze_allowed",
        "candidate_disposition_rows": len(disposition),
        "train_metric_rows": len(train),
        "residual_waterfall_rows": len(waterfall),
        "runtime_legality_rows": len(runtime),
        "no_freeze_blocker_rows": sum(1 for row in no_freeze if row["blocks_freeze"] == "true"),
        "candidate_reviewable_rows": sum(1 for row in disposition if row["disposition"] == "candidate_reviewable"),
        "validation_holdout_external_rows_scored": 0,
        "source_property_release_rows": 0,
        "final_score_values": 0,
        "candidate_freeze_allowed": False,
        "coefficient_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_repo_mutation": False,
        "fitting_or_model_selection": False,
        "residual_absorbed_into_internal_nu": False,
        "figure_svg": svg_path,
    }
    csv_dump(out / "candidate_disposition_table.csv", list(disposition[0]), disposition)
    csv_dump(out / "residual_owner_waterfall_table.csv", list(waterfall[0]), waterfall)
    csv_dump(out / "runtime_legality_matrix.csv", list(runtime[0]), runtime)
    csv_dump(out / "train_only_metric_context.csv", list(train[0]), train)
    csv_dump(out / "no_freeze_rationale.csv", list(no_freeze[0]), no_freeze)
    csv_dump(out / "s12_thesis_claim_boundary.csv", list(claims[0]), claims)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary, svg_path)
    write_thesis_handoff(out, svg_path)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
