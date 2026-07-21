#!/usr/bin/env python3
"""Build the forward-model readiness note after H1 proxy evidence.

This is an evidence integrator, not a fitted model. It records what is now
admitted for forward-model scoring, what remains diagnostic, and why the
current precursor is still not a final forward-v1 score.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DATE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14"
OUT_DIR = DATE_DIR / "2026-07-14_forward_model_readiness_after_h1_proxy"

INPUT_CONTRACT = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract"
VALIDATION_SPLIT = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split"
FORWARD_V0 = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler"
SOLVE_CASE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation"
)
HX_BOUNDARY = (
    REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave"
)
H1_PROXY = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun"
SENSOR_MAP = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract"
THERMAL_GATE = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate"
SCORECARD_PRECURSOR = (
    REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor"
)

LITREV_GATES = {
    "source_envelope_gate": REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/source_overlap_flags.csv",
    "property_mode_lane": REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv",
    "named_loss_table": REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv",
    "heat_loss_admission_table": REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/heat_closure_admission.csv",
    "cfd_coefficient_naming_limits": REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv",
}

LANE_COLUMNS = [
    "lane_id",
    "readiness_status",
    "score_permission",
    "admitted_evidence",
    "current_blocker",
    "next_gate",
    "source_artifact",
]
SPLIT_COLUMNS = [
    "case_id",
    "split_role",
    "fit_allowed",
    "score_allowed",
    "holdout_allowed_now",
    "discipline_rule",
    "source_artifact",
]
RESIDUAL_COLUMNS = [
    "case_id",
    "split_role",
    "variant_id",
    "score_status",
    "mdot_error_vs_cfd_kg_s",
    "mdot_error_vs_cfd_pct",
    "mdot_residual_attribution",
    "abs_qhx_error_W",
    "hx_residual_attribution",
    "Tmean_error_vs_cfd_K",
    "thermal_state_attribution",
    "sensor_attribution",
    "source_artifact",
]
GATE_COLUMNS = [
    "gate_id",
    "gate_status",
    "admitted_or_current_evidence",
    "blocks_final_forward_v1",
    "source_artifact",
]
BLOCKER_COLUMNS = [
    "blocker_id",
    "severity",
    "blocks_final_forward_v1",
    "why_it_blocks",
    "next_required_evidence",
    "source_artifact",
]
MANIFEST_COLUMNS = ["artifact", "role", "mutation_status", "path"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def by_key(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row.get(key, "") for key in keys): row for row in rows}


def split_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(VALIDATION_SPLIT / "admission_split_table.csv"):
        if row["row_id"] not in {"salt_2", "salt_3", "salt_4"}:
            continue
        role = row["current_assignment"]
        rows.append(
            {
                "case_id": row["row_id"],
                "split_role": role,
                "fit_allowed": "yes" if role == "train" else "no",
                "score_allowed": "yes",
                "holdout_allowed_now": "yes_after_model_freeze" if role == "holdout" else "not_holdout",
                "discipline_rule": row["fit_response_use"] if role == "train" else row["score_response_use"],
                "source_artifact": rel(VALIDATION_SPLIT / "admission_split_table.csv"),
            }
        )
    return rows


def residual_rows() -> list[dict[str, Any]]:
    hx_rows = read_csv(HX_BOUNDARY / "hx_validation_guardrail_scorecard.csv")
    h1_rows = by_key(read_csv(H1_PROXY / "h1_proxy_results.csv"), "case_id", "variant_id")
    sensor_summary = read_json(SENSOR_MAP / "summary.json")
    blocked_sensors = ", ".join(sensor_summary["blocked_sensor_scores"])
    rows: list[dict[str, Any]] = []
    for hx in hx_rows:
        h1_variant = f"{hx['variant_id']}_H1_proxy"
        h1 = h1_rows.get((hx["case_id"], h1_variant), {})
        mdot_error = fnum(h1.get("mdot_error_vs_cfd_kg_s"))
        cfd_mdot = fnum(h1.get("cfd_mdot_kg_s"))
        mdot_pct = (mdot_error / cfd_mdot * 100.0) if cfd_mdot else 0.0
        rows.append(
            {
                "case_id": hx["case_id"],
                "split_role": hx["fit_role"],
                "variant_id": h1_variant,
                "score_status": "h1_proxy_screen_only_not_final_forward_v1",
                "mdot_error_vs_cfd_kg_s": mdot_error,
                "mdot_error_vs_cfd_pct": mdot_pct,
                "mdot_residual_attribution": (
                    "H1 aggregate fixed-K proxy reduces mdot error relative to forward-v0, "
                    "but every Salt row still overpredicts CFD mdot and the implementation is not localized."
                ),
                "abs_qhx_error_W": fnum(hx["abs_qhx_error_W"]),
                "hx_residual_attribution": (
                    "HX1 split-aware cooler score remains guardrailed; imposed or one-scalar cooler evidence "
                    "is not a fully predictive HX boundary."
                ),
                "Tmean_error_vs_cfd_K": fnum(h1.get("Tmean_error_vs_cfd_K")),
                "thermal_state_attribution": (
                    "Thermal state residual is diagnostic while hydraulic H1 is screen-only and thermal mesh "
                    "admission has zero fit-admissible rows."
                ),
                "sensor_attribution": (
                    f"{sensor_summary['n_provisional_diagnostic_score_allowed']} provisional diagnostic sensors "
                    f"may be joined after solve; {blocked_sensors} remain excluded."
                ),
                "source_artifact": rel(H1_PROXY / "h1_proxy_results.csv"),
            }
        )
    return rows


def gate_rows() -> list[dict[str, Any]]:
    input_summary = read_json(INPUT_CONTRACT / "summary.json")
    solve_summary = read_json(SOLVE_CASE / "comparison_summary.json")
    h1_summary = read_json(H1_PROXY / "summary.json")
    sensor_summary = read_json(SENSOR_MAP / "summary.json")
    thermal_summary = read_json(THERMAL_GATE / "summary.json")
    rows: list[dict[str, Any]] = [
        {
            "gate_id": "predictive_input_contract",
            "gate_status": f"pass_{input_summary['n_violations']}_violations",
            "admitted_or_current_evidence": (
                f"{input_summary['n_runtime_fields']} runtime fields, "
                f"{input_summary['n_case_runtime_rows']} case rows, "
                f"{input_summary['n_validation_targets']} validation targets."
            ),
            "blocks_final_forward_v1": "no",
            "source_artifact": rel(INPUT_CONTRACT / "summary.json"),
        },
        {
            "gate_id": "train_validation_holdout_split",
            "gate_status": "locked",
            "admitted_or_current_evidence": "salt_2=train; salt_3=validation; salt_4=holdout.",
            "blocks_final_forward_v1": "no",
            "source_artifact": rel(VALIDATION_SPLIT / "admission_split_table.csv"),
        },
        {
            "gate_id": "solve_case_confirmation",
            "gate_status": solve_summary["overall_status"],
            "admitted_or_current_evidence": (
                f"{solve_summary['n_pass_rows']}/{solve_summary['n_comparison_rows']} solve_case-vs-fast_scan rows pass; "
                "solve_case rows are authoritative for forward-v0."
            ),
            "blocks_final_forward_v1": "no_for_forward_v0_confirmation_yes_for_unrun_h1_solve_case",
            "source_artifact": rel(SOLVE_CASE / "comparison_summary.json"),
        },
        {
            "gate_id": "hydraulic_h1_proxy",
            "gate_status": h1_summary["overall_status"],
            "admitted_or_current_evidence": (
                f"Aggregate Salt2 K sum {h1_summary['minor_loss_total_fixed_K']:.4f}; "
                f"F1 mean mdot error {h1_summary['variant_summary'][1]['mean_mdot_error_vs_cfd_kg_s']:.6f} kg/s."
            ),
            "blocks_final_forward_v1": "yes_until_localized_h1_and_no_overprediction_gate_pass",
            "source_artifact": rel(H1_PROXY / "summary.json"),
        },
        {
            "gate_id": "hx_and_external_boundary",
            "gate_status": "guardrailed_proxy_and_fluid_api_pending",
            "admitted_or_current_evidence": "Split-aware HX/boundary scorecard exists; external-boundary dictionaries are repo-local evidence only.",
            "blocks_final_forward_v1": "yes",
            "source_artifact": rel(HX_BOUNDARY / "hx_validation_guardrail_scorecard.csv"),
        },
        {
            "gate_id": "thermal_mesh_gate",
            "gate_status": thermal_summary["thermal_mesh_gate_status"],
            "admitted_or_current_evidence": (
                f"{thermal_summary['fit_admissible_count']} fit-admissible rows; "
                f"{thermal_summary['publication_ready_thermal_gci_count']} publication-ready thermal GCI rows."
            ),
            "blocks_final_forward_v1": "yes_for_thermal_closure_fits",
            "source_artifact": rel(THERMAL_GATE / "summary.json"),
        },
        {
            "gate_id": "sensor_map",
            "gate_status": sensor_summary["sensor_temperature_score_claim"],
            "admitted_or_current_evidence": (
                f"{sensor_summary['n_sensors']} labels mapped; "
                f"{sensor_summary['n_provisional_diagnostic_score_allowed']} diagnostic-scoreable; "
                f"{sensor_summary['n_currently_blocked_sensor_scores']} blocked."
            ),
            "blocks_final_forward_v1": "yes_for_complete_sensor_claim_no_for_partial_diagnostic_join",
            "source_artifact": rel(SENSOR_MAP / "summary.json"),
        },
    ]
    for gate_id, path in LITREV_GATES.items():
        rows.append(
            {
                "gate_id": f"litrev_{gate_id}",
                "gate_status": "present_referenced_by_input_contract" if path.exists() else "missing",
                "admitted_or_current_evidence": "Required pre-score literature gate reference.",
                "blocks_final_forward_v1": "yes_if_missing",
                "source_artifact": rel(path),
            }
        )
    return rows


def readiness_lanes(gates: list[dict[str, Any]], residuals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    h1_f1 = [row for row in residuals if row["variant_id"] == "F1_heater_only_H1_proxy"]
    mean_h1_f1 = sum(fnum(row["mdot_error_vs_cfd_kg_s"]) for row in h1_f1) / len(h1_f1)
    return [
        {
            "lane_id": "input_contract_and_litrev_gates",
            "readiness_status": "current_pass",
            "score_permission": "score_after_solve_join_only",
            "admitted_evidence": "Strict contract has zero violations and all five lit-rev gates are referenced.",
            "current_blocker": "None for current guardrail scoring; new fitted models must keep this contract current.",
            "next_gate": "Reject any runtime use of CFD mdot, realized wallHeatFlux, or TP/TW targets.",
            "source_artifact": rel(INPUT_CONTRACT / "summary.json"),
        },
        {
            "lane_id": "hydraulic_h1_proxy",
            "readiness_status": "directional_screen_improved_but_blocked",
            "score_permission": "diagnostic_screen_only",
            "admitted_evidence": f"F1 H1 proxy mean mdot error is {mean_h1_f1:.6f} kg/s vs CFD.",
            "current_blocker": "Aggregate fixed-K proxy is not faithful localized H1 and still overpredicts every Salt row.",
            "next_gate": "Finish AGENT-310-style hydraulic scorecard, then implement localized Fluid support and rerun.",
            "source_artifact": rel(H1_PROXY / "h1_proxy_variant_summary.csv"),
        },
        {
            "lane_id": "solve_case_forward_v0",
            "readiness_status": "admitted_for_forward_v0_confirmation",
            "score_permission": "admitted_confirmation_not_h1",
            "admitted_evidence": "Full solve_case comparison passed 6/6 rows; fast_scan remains proxy where documented.",
            "current_blocker": "H1 proxy has not been rerun through full solve_case.",
            "next_gate": "Use solve_case for any final forward mode after hydraulic implementation exists.",
            "source_artifact": rel(SOLVE_CASE / "comparison_summary.json"),
        },
        {
            "lane_id": "hx_boundary",
            "readiness_status": "guardrailed_proxy",
            "score_permission": "proxy_only_under_locked_split",
            "admitted_evidence": "HX1 split-aware scores exist for train/validation/holdout.",
            "current_blocker": "Cooler removal is still imposed/proxy; external Fluid API does not consume first-class boundary dictionaries.",
            "next_gate": "Replace imposed cooler duty with UA/epsilon-NTU after hydraulic gate is credible.",
            "source_artifact": rel(HX_BOUNDARY / "hx_validation_guardrail_scorecard.csv"),
        },
        {
            "lane_id": "thermal_gate",
            "readiness_status": "blocked",
            "score_permission": "no_thermal_fit",
            "admitted_evidence": "Thermal gate currently has zero fit-admissible rows and zero publication-ready thermal GCI rows.",
            "current_blocker": "Sign review, heat-balance/admission, downcomer policy, and mesh-GCI readiness.",
            "next_gate": "Wait for the active AGENT-309 thermal refresh/admission result.",
            "source_artifact": rel(THERMAL_GATE / "summary.json"),
        },
        {
            "lane_id": "sensor_map",
            "readiness_status": "partial_diagnostic",
            "score_permission": "post_solve_join_only",
            "admitted_evidence": "15 of 17 labels are provisionally diagnostic-scoreable; TP2 and TW10 are excluded.",
            "current_blocker": "No survey-grade coordinates and two blocked labels.",
            "next_gate": "Keep TP/TW as validation targets only and add explicit exclusion policy in score tables.",
            "source_artifact": rel(SENSOR_MAP / "summary.json"),
        },
    ]


def blockers() -> list[dict[str, Any]]:
    return [
        {
            "blocker_id": "localized_h1_not_implemented",
            "severity": "high",
            "blocks_final_forward_v1": "yes",
            "why_it_blocks": "Current H1 rerun is an aggregate fixed-K proxy, not the ranked localized named-loss/reset bundle.",
            "next_required_evidence": "Fluid-side localized loss/reset support plus forward rerun showing mdot guardrail passes without thermal fitting.",
            "source_artifact": rel(H1_PROXY / "README.md"),
        },
        {
            "blocker_id": "h1_proxy_mdot_still_overpredicts",
            "severity": "high",
            "blocks_final_forward_v1": "yes",
            "why_it_blocks": "Every Salt2/3/4 H1 proxy row still overpredicts CFD mdot, even though the error is smaller.",
            "next_required_evidence": "Hydraulic scorecard acceptance threshold and residual attribution showing no systematic overprediction.",
            "source_artifact": rel(H1_PROXY / "h1_proxy_results.csv"),
        },
        {
            "blocker_id": "thermal_mesh_not_admitted",
            "severity": "high",
            "blocks_final_forward_v1": "yes_for_thermal_closure_claims",
            "why_it_blocks": "Thermal gate reports zero fit-admissible rows and zero publication-ready thermal GCI rows.",
            "next_required_evidence": "Admission gate that admits thermal rows after sign, heat-balance, downcomer, and mesh checks.",
            "source_artifact": rel(THERMAL_GATE / "summary.json"),
        },
        {
            "blocker_id": "predictive_hx_boundary_not_final",
            "severity": "high",
            "blocks_final_forward_v1": "yes",
            "why_it_blocks": "Imposed cooler/HX1 proxy scores do not yet replace cooler duty with a fully predictive UA or epsilon-NTU boundary.",
            "next_required_evidence": "Frozen HX form trained only on allowed rows and scored on validation/holdout after hydraulic gate passes.",
            "source_artifact": rel(HX_BOUNDARY / "hx_validation_guardrail_scorecard.csv"),
        },
        {
            "blocker_id": "sensor_map_partial",
            "severity": "medium",
            "blocks_final_forward_v1": "yes_for_complete_sensor_claim",
            "why_it_blocks": "TP2 and TW10 are blocked and the remaining coordinates are provisional diagnostics.",
            "next_required_evidence": "Survey-grade or explicit score-exclusion policy for blocked sensor labels.",
            "source_artifact": rel(SENSOR_MAP / "summary.json"),
        },
    ]


def manifest() -> list[dict[str, str]]:
    inputs = [
        INPUT_CONTRACT / "summary.json",
        VALIDATION_SPLIT / "admission_split_table.csv",
        FORWARD_V0 / "forward_v0_variant_summary.csv",
        SOLVE_CASE / "comparison_summary.json",
        HX_BOUNDARY / "hx_validation_guardrail_scorecard.csv",
        H1_PROXY / "summary.json",
        H1_PROXY / "h1_proxy_results.csv",
        SENSOR_MAP / "summary.json",
        THERMAL_GATE / "summary.json",
        SCORECARD_PRECURSOR / "README.md",
    ]
    rows = [
        {
            "artifact": path.name,
            "role": "input_evidence",
            "mutation_status": "read_only",
            "path": rel(path),
        }
        for path in inputs
    ]
    rows.extend(
        {
            "artifact": name,
            "role": "generated_output",
            "mutation_status": "created_by_AGENT_315",
            "path": rel(OUT_DIR / name),
        }
        for name in [
            "README.md",
            "readiness_lanes_after_h1_proxy.csv",
            "train_validation_holdout_guardrail.csv",
            "residual_attribution_after_h1_proxy.csv",
            "input_contract_gate_readiness.csv",
            "blockers_to_final_forward_v1.csv",
            "source_manifest.csv",
            "summary.json",
        ]
    )
    return rows


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(H1_PROXY / 'summary.json')}
  - {rel(SOLVE_CASE / 'comparison_summary.json')}
  - {rel(INPUT_CONTRACT / 'summary.json')}
  - {rel(VALIDATION_SPLIT / 'admission_split_table.csv')}
  - {rel(HX_BOUNDARY / 'hx_validation_guardrail_scorecard.csv')}
  - {rel(THERMAL_GATE / 'summary.json')}
  - {rel(SENSOR_MAP / 'summary.json')}
tags: [forward-model, predictive-1d, scorecard, validation-split, h1-proxy]
related:
  - {rel(SCORECARD_PRECURSOR / 'README.md')}
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-315
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Forward-Model Readiness After H1 Proxy

This is a readiness note and residual-attribution refresh. It is not a final
forward-v1 score, does not fit a new model, does not edit native CFD outputs,
and does not edit external Fluid source.

## Current Decision

Final forward-v1 remains blocked. Evidence improved in two ways: full
`solve_case` confirmation for forward-v0 passed `{summary['solve_case_pass_rows']}/{summary['solve_case_comparison_rows']}`
comparison rows, and the H1 aggregate proxy reduced the F1 mean mdot error to
`{summary['h1_f1_mean_mdot_error_vs_cfd_kg_s']:.6f} kg/s`. That H1 result is
still screen-only because it is an aggregate fixed-K proxy, not localized H1,
and every Salt row still overpredicts CFD mdot.

## Evidence Now Admitted

- Strict predictive input contract: `{summary['input_contract_violations']}` violations, with the five lit-rev gates present.
- Split discipline: `salt_2=train`, `salt_3=validation`, `salt_4=holdout`.
- Full forward-v0 `solve_case` confirmation: pass; solve_case rows are authoritative for forward-v0.
- H1 proxy: directionality evidence only; no thermal fitting and no publication closure.
- Sensor map: `{summary['sensor_scoreable']}` provisional diagnostic labels, with `TP2` and `TW10` blocked.

## Blocks Final Forward-v1

- Faithful localized H1 named-loss/reset implementation has not been run.
- H1 proxy still has systematic positive mdot error versus CFD on Salt2/3/4.
- Thermal gate still has `{summary['thermal_fit_admissible_rows']}` fit-admissible rows and `{summary['thermal_publication_gci_rows']}` publication-ready thermal GCI rows.
- HX/cooler remains guardrailed proxy evidence, not a fully predictive UA or epsilon-NTU boundary.
- Sensor scoring remains partial and post-solve only.

## Files

- `readiness_lanes_after_h1_proxy.csv`
- `train_validation_holdout_guardrail.csv`
- `residual_attribution_after_h1_proxy.csv`
- `input_contract_gate_readiness.csv`
- `blockers_to_final_forward_v1.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = split_rows()
    residuals = residual_rows()
    gates = gate_rows()
    lanes = readiness_lanes(gates, residuals)
    blocker_rows = blockers()
    manifest_rows = manifest()

    h1_f1 = [row for row in residuals if row["variant_id"] == "F1_heater_only_H1_proxy"]
    solve_summary = read_json(SOLVE_CASE / "comparison_summary.json")
    input_summary = read_json(INPUT_CONTRACT / "summary.json")
    thermal_summary = read_json(THERMAL_GATE / "summary.json")
    sensor_summary = read_json(SENSOR_MAP / "summary.json")
    summary = {
        "task_id": "AGENT-315",
        "generated_utc": utc_now(),
        "final_forward_v1_status": "blocked_not_final",
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "n_readiness_lanes": len(lanes),
        "n_split_rows": len(splits),
        "n_residual_rows": len(residuals),
        "n_gate_rows": len(gates),
        "n_blockers": len(blocker_rows),
        "input_contract_violations": input_summary["n_violations"],
        "solve_case_status": solve_summary["overall_status"],
        "solve_case_pass_rows": solve_summary["n_pass_rows"],
        "solve_case_comparison_rows": solve_summary["n_comparison_rows"],
        "h1_f1_mean_mdot_error_vs_cfd_kg_s": sum(fnum(row["mdot_error_vs_cfd_kg_s"]) for row in h1_f1)
        / len(h1_f1),
        "h1_proxy_score_status": "screen_only_not_final_forward_v1",
        "thermal_fit_admissible_rows": thermal_summary["fit_admissible_count"],
        "thermal_publication_gci_rows": thermal_summary["publication_ready_thermal_gci_count"],
        "sensor_scoreable": sensor_summary["n_provisional_diagnostic_score_allowed"],
        "blocked_sensors": sensor_summary["blocked_sensor_scores"],
        "outputs": [
            "README.md",
            "readiness_lanes_after_h1_proxy.csv",
            "train_validation_holdout_guardrail.csv",
            "residual_attribution_after_h1_proxy.csv",
            "input_contract_gate_readiness.csv",
            "blockers_to_final_forward_v1.csv",
            "source_manifest.csv",
            "summary.json",
        ],
    }

    write_csv(out_dir / "readiness_lanes_after_h1_proxy.csv", lanes, LANE_COLUMNS)
    write_csv(out_dir / "train_validation_holdout_guardrail.csv", splits, SPLIT_COLUMNS)
    write_csv(out_dir / "residual_attribution_after_h1_proxy.csv", residuals, RESIDUAL_COLUMNS)
    write_csv(out_dir / "input_contract_gate_readiness.csv", gates, GATE_COLUMNS)
    write_csv(out_dir / "blockers_to_final_forward_v1.csv", blocker_rows, BLOCKER_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", manifest_rows, MANIFEST_COLUMNS)
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = build_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
