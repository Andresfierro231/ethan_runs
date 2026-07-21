#!/usr/bin/env python3
"""Build the repo-local predictive external-boundary implementation wave.

This package is the handoff between the CFD-derived external boundary evidence
and the reduced-order Fluid implementation.  It intentionally keeps external
Fluid source read-only in this workspace and emits Fluid-ready contracts plus
scorecards from existing artifacts.
"""

from __future__ import annotations

import csv
import json
import math
import platform
import socket
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "AGENT-297"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave"

PATCH_TABLE = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
PATCH_PARITY_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/parity_input_contract.csv"
)
WALL_LAYER_DRIVE = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv"
)
WALL_LAYER_PARITY = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/section_heat_parity.csv"
)
VALIDATION_SPLIT = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv"
)
HX_FORWARD_SCORES = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/hx_primary_forward_scores.csv"
)
HX_FIT_PARAMETERS = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/hx_fit_parameters.csv"
)
HX_VALIDATION_SPLITS = (
    ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/hx_validation_splits.csv"
)
HYDRAULIC_RESIDUALS = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv"
)

EXTERNAL_BC_COLUMNS = [
    "case_id",
    "source_id",
    "fluid_parent_segment",
    "one_d_segment",
    "role",
    "patch_count",
    "area_m2",
    "hA_W_K",
    "h_W_m2K",
    "Ta_K",
    "Tsur_K",
    "emissivity",
    "thicknessLayers",
    "thickness_total_m",
    "kappaLayerCoeffs",
    "wall_layer_metadata_status",
    "realized_wallHeatFlux_W",
    "realized_external_loss_W",
    "imposed_Q_W",
    "recommended_runtime_mode",
    "recommended_drive_selector",
    "setup_radiation_policy",
    "realized_flux_replay_policy",
    "validation_split_role",
    "support_status",
    "source_paths",
]

BOUNDARY_SCORE_COLUMNS = [
    "case_id",
    "validation_split_role",
    "role",
    "mode",
    "n_rows",
    "realized_external_loss_W",
    "mode_external_loss_W",
    "loss_residual_mode_minus_cfd_W",
    "mean_abs_loss_residual_W",
    "max_abs_loss_residual_W",
    "interpretation",
]

HX_SCORE_COLUMNS = [
    "split_id",
    "case_id",
    "fit_role",
    "variant_id",
    "predicted_qhx_total_W",
    "target_cooler_removed_W",
    "qhx_error_W",
    "abs_qhx_error_W",
    "Tmean_error_vs_cfd_K",
    "loop_delta_error_vs_cfd_K",
    "mdot_error_vs_cfd_kg_s",
    "mdot_error_vs_cfd_pct",
    "hydraulic_interpretation",
    "score_role",
    "guardrail_status",
    "package_caveat",
]

HYDRAULIC_SUMMARY_COLUMNS = [
    "variant_id",
    "n_cases",
    "mean_mdot_error_vs_cfd_kg_s",
    "mean_mdot_error_vs_cfd_pct",
    "max_abs_mdot_error_vs_cfd_kg_s",
    "guardrail_status",
    "interpretation",
]

DECISION_COLUMNS = [
    "decision_id",
    "status",
    "implementation_action",
    "scientific_guardrail",
    "next_owner",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fnum(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if text in {"", "nan", "NaN", "None"}:
        return default
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.9f}".rstrip("0").rstrip(".")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def git_rev() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def load_validation_roles() -> dict[str, str]:
    return {
        row["row_id"]: row["current_assignment"]
        for row in read_csv(VALIDATION_SPLIT)
        if row.get("row_family") == "mainline_salt"
    }


def aggregate_patch_metadata() -> dict[tuple[str, str, str], dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(PATCH_TABLE):
        key = (row["case_id"], row["one_d_segment"], row["role"])
        grouped[key].append(row)

    out: dict[tuple[str, str, str], dict[str, str]] = {}
    for key, rows in grouped.items():
        out[key] = {
            "thicknessLayers": unique_or_mixed(rows, "thicknessLayers"),
            "thickness_total_m": unique_or_mixed(rows, "thickness_total_m"),
            "kappaLayerCoeffs": unique_or_mixed(rows, "kappaLayerCoeffs"),
            "wall_layer_metadata_status": unique_or_mixed(rows, "wall_layer_metadata_status"),
        }
    return out


def unique_or_mixed(rows: list[dict[str, str]], key: str) -> str:
    values = sorted({row.get(key, "").strip() for row in rows if row.get(key, "").strip()})
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return "mixed:" + " | ".join(values)


def load_parent_segments() -> dict[tuple[str, str], str]:
    out = {}
    for row in read_csv(PATCH_PARITY_CONTRACT):
        out[(row["case_id"], row["one_d_segment"])] = row.get("fluid_parent_segment", "")
    return out


def build_external_bc_dictionary() -> list[dict[str, Any]]:
    validation_roles = load_validation_roles()
    parent_segments = load_parent_segments()
    patch_meta = aggregate_patch_metadata()
    rows = []
    for row in read_csv(WALL_LAYER_DRIVE):
        key = (row["case_id"], row["one_d_segment"], row["role"])
        h = fnum(row.get("area_weighted_h_W_m2K"))
        ta = fnum(row.get("Ta_K"))
        tsur = fnum(row.get("Tsur_K"))
        eps = fnum(row.get("emissivity"))
        role = row["role"]
        has_setup_bc = h is not None and ta is not None and tsur is not None and eps is not None
        if role in {"ambient_wall", "junction_other"} and has_setup_bc:
            runtime_mode = "external_boundary_table_setup_candidate"
            support = "ready_for_fluid_api_consumption"
        elif role in {"heater", "cooler", "test_section"}:
            runtime_mode = "source_sink_documentation_not_passive_hA_fit"
            support = "document_only_keep_out_of_passive_external_fit"
        else:
            runtime_mode = "blocked_external_hA_inputs_incomplete"
            support = "blocked_missing_h_Ta_Tsur_or_emissivity"

        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "fluid_parent_segment": parent_segments.get((row["case_id"], row["one_d_segment"]), ""),
                "one_d_segment": row["one_d_segment"],
                "role": role,
                "patch_count": row.get("patch_count", ""),
                "area_m2": fnum(row.get("area_m2")),
                "hA_W_K": fnum(row.get("hA_W_K")),
                "h_W_m2K": h,
                "Ta_K": ta,
                "Tsur_K": tsur,
                "emissivity": eps,
                "thicknessLayers": patch_meta.get(key, {}).get("thicknessLayers", ""),
                "thickness_total_m": patch_meta.get(key, {}).get("thickness_total_m", ""),
                "kappaLayerCoeffs": patch_meta.get(key, {}).get("kappaLayerCoeffs", ""),
                "wall_layer_metadata_status": patch_meta.get(key, {}).get("wall_layer_metadata_status", ""),
                "realized_wallHeatFlux_W": fnum(row.get("realized_wallHeatFlux_W")),
                "realized_external_loss_W": fnum(row.get("external_loss_realized_W")),
                "imposed_Q_W": fnum(row.get("imposed_Q_W")),
                "recommended_runtime_mode": runtime_mode,
                "recommended_drive_selector": "fluid_segment_bulk_temperature_for_v1_setup_mode",
                "setup_radiation_policy": "include_rcExternalTemperature_equivalent_radiation_from_emissivity_Tsur",
                "realized_flux_replay_policy": "do_not_add_radiation_to_realized_CFD_wallHeatFlux",
                "validation_split_role": validation_roles.get(row["case_id"], "not_in_split"),
                "support_status": support,
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def build_boundary_scorecard() -> list[dict[str, Any]]:
    validation_roles = load_validation_roles()
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(WALL_LAYER_PARITY):
        grouped[(row["case_id"], row["role"], row["mode"])].append(row)

    out = []
    for (case_id, role, mode), rows in sorted(grouped.items()):
        realized = sum(fnum(row.get("realized_external_loss_W"), 0.0) or 0.0 for row in rows)
        modeled = sum(fnum(row.get("mode_external_loss_W"), 0.0) or 0.0 for row in rows)
        residual = modeled - realized
        abs_vals = [fnum(row.get("absolute_loss_residual_W"), 0.0) or 0.0 for row in rows]
        interpretation = "diagnostic_only"
        if role == "ambient_wall" and mode in {"E1_wall_shell", "E2_low_dimensional_blend"}:
            interpretation = "executable_but_does_not_close_passive_heat_loss_gap"
        elif role in {"heater", "test_section"}:
            interpretation = "source_role_not_passive_external_fit"
        out.append(
            {
                "case_id": case_id,
                "validation_split_role": validation_roles.get(case_id, "not_in_split"),
                "role": role,
                "mode": mode,
                "n_rows": len(rows),
                "realized_external_loss_W": realized,
                "mode_external_loss_W": modeled,
                "loss_residual_mode_minus_cfd_W": residual,
                "mean_abs_loss_residual_W": sum(abs_vals) / len(abs_vals) if abs_vals else None,
                "max_abs_loss_residual_W": max(abs_vals) if abs_vals else None,
                "interpretation": interpretation,
            }
        )
    return out


def build_hx_scorecard() -> list[dict[str, Any]]:
    hydraulic = {
        (row["case_id"], row["variant_id"]): row for row in read_csv(HYDRAULIC_RESIDUALS)
    }
    out = []
    for row in read_csv(HX_FORWARD_SCORES):
        key = (row["case_id"], row["variant_id"])
        hrow = hydraulic.get(key, {})
        mdot_error = fnum(row.get("mdot_error_vs_cfd_kg_s"))
        fit_role = row["fit_role"]
        if fit_role == "train":
            score_role = "fit_row_not_model_selection_score"
        elif fit_role == "validation":
            score_role = "model_selection_score"
        elif fit_role == "holdout":
            score_role = "final_heldout_score_after_model_freeze"
        else:
            score_role = "diagnostic"
        guardrail = "hydraulic_guardrail_failed_mdot_overprediction"
        if mdot_error is not None and abs(mdot_error) <= 0.002:
            guardrail = "hydraulic_guardrail_passed"
        out.append(
            {
                "split_id": row.get("split_id", ""),
                "case_id": row["case_id"],
                "fit_role": fit_role,
                "variant_id": row["variant_id"],
                "predicted_qhx_total_W": fnum(row.get("predicted_qhx_total_W")),
                "target_cooler_removed_W": fnum(row.get("target_cooler_removed_W")),
                "qhx_error_W": fnum(row.get("qhx_error_W")),
                "abs_qhx_error_W": abs(fnum(row.get("qhx_error_W"), 0.0) or 0.0),
                "Tmean_error_vs_cfd_K": fnum(row.get("Tmean_error_vs_cfd_K")),
                "loop_delta_error_vs_cfd_K": fnum(row.get("loop_delta_error_vs_cfd_K")),
                "mdot_error_vs_cfd_kg_s": mdot_error,
                "mdot_error_vs_cfd_pct": fnum(hrow.get("mdot_error_vs_cfd_pct")),
                "hydraulic_interpretation": hrow.get("hydraulic_interpretation", ""),
                "score_role": score_role,
                "guardrail_status": guardrail,
                "package_caveat": "use_split_aware_hx_scores_ignore_stale_missing_split_protocol_files",
            }
        )
    return out


def build_hydraulic_summary() -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(HYDRAULIC_RESIDUALS):
        grouped[row["variant_id"]].append(row)
    out = []
    for variant, rows in sorted(grouped.items()):
        errors = [fnum(row.get("mdot_error_vs_cfd_kg_s"), 0.0) or 0.0 for row in rows]
        pcts = [fnum(row.get("mdot_error_vs_cfd_pct"), 0.0) or 0.0 for row in rows]
        out.append(
            {
                "variant_id": variant,
                "n_cases": len(rows),
                "mean_mdot_error_vs_cfd_kg_s": sum(errors) / len(errors),
                "mean_mdot_error_vs_cfd_pct": sum(pcts) / len(pcts),
                "max_abs_mdot_error_vs_cfd_kg_s": max(abs(value) for value in errors),
                "guardrail_status": "failed_all_rows_overpredict_mdot",
                "interpretation": "do_not_use_thermal_fit_to_hide_hydraulic_bias",
            }
        )
    return out


def build_decision_table() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "D1_external_boundary_table_contract",
            "status": "repo_local_contract_ready_fluid_source_read_only_here",
            "implementation_action": "add Fluid external_boundary_table mode consuming generated cfd_external_boundary_dictionary.csv",
            "scientific_guardrail": "setup parity includes radiation via emissivity/Tsur; realized wallHeatFlux replay does not add radiation",
            "next_owner": "Fluid implementer with writable cfd-modeling-tools scope",
        },
        {
            "decision_id": "D2_wall_shell_E1_E2",
            "status": "diagnostic_not_validated_closure",
            "implementation_action": "keep E1/E2 in evidence package but do not promote beta or owner-cell shell proxy into predictive model",
            "scientific_guardrail": "owner-cell T_wall_shell did not close passive heat-loss gap and E2 beta saturates at bounds",
            "next_owner": "boundary evidence writer",
        },
        {
            "decision_id": "D3_hx_scalar_fit",
            "status": "validation_split_available_but_hydraulic_guardrail_fails",
            "implementation_action": "score HX1 train/validation/holdout rows; do not claim end-to-end prediction until mdot bias is addressed",
            "scientific_guardrail": "Salt2 train, Salt3 validation, Salt4 holdout; no refit on validation or holdout",
            "next_owner": "HX scorer plus hydraulic guardrail reviewer",
        },
        {
            "decision_id": "D4_thermal_mesh_gate",
            "status": "parallel_follow_on_required",
            "implementation_action": "classify repaired thermal QOIs before any UA/HTC/Nu closure admission",
            "scientific_guardrail": "no thermal closure target without sign, heat-balance, downcomer, and mesh-family gates",
            "next_owner": "TODO-PRED-THERMAL-MESH-GATE implementer",
        },
    ]


def write_readme(summary: dict[str, Any]) -> None:
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(OUT / "summary.json")}
  - {rel(OUT / "cfd_external_boundary_dictionary.csv")}
  - {rel(OUT / "hx_validation_guardrail_scorecard.csv")}
tags: [forward-model, predictive-1d, external-boundary, radiation, hydraulic-guardrail]
related:
  - .agent/status/2026-07-13_AGENT-297.md
  - .agent/journal/2026-07-13/predictive-external-bc-implementation-wave.md
task: AGENT-297
date: 2026-07-13
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Predictive External BC Implementation Wave

Generated: `{summary['generated_at']}`  
Task: `{TASK_ID}`

This package implements the repo-local bridge for the next CFD-to-1D parity
phase. It does not mutate native CFD solver outputs and does not edit external
Fluid source in this sandbox.

## Outputs

- `cfd_external_boundary_dictionary.csv`: Fluid-ready segment/role external
  boundary rows from AGENT-263 plus wall-layer metadata.
- `boundary_mode_scorecard.csv`: E0/E1/E2 wall-layer residuals with validation
  split roles.
- `hx_validation_guardrail_scorecard.csv`: Salt2 train, Salt3 validation, Salt4
  holdout HX score rows with hydraulic guardrails.
- `hydraulic_guardrail_summary.csv`: mdot-bias summary by forward-v0 variant.
- `implementation_decision_table.csv`: decisions and next owners.
- `fluid_external_boundary_patch_plan.md`: exact downstream Fluid edit plan.

## Main Result

The external boundary dictionary is ready for Fluid API implementation, but the
current workspace keeps `../cfd-modeling-tools/**` read-only. Radiation policy is
fixed: setup-level external-boundary parity must include emissivity/Tsur
radiation; realized CFD `wallHeatFlux` replay must not add a separate radiation
term.

The validation split is now usable for one-scalar HX scoring, but hydraulic
guardrails still fail: forward-v0 Salt rows overpredict mdot, so thermal
improvements cannot be interpreted as end-to-end prediction yet.

HX package caveat: `fit_protocol_status.csv` and
`validation_split_requirements.csv` still contain stale missing-split language.
Use the later split-aware `hx_validation_splits.csv`, `hx_fit_parameters.csv`,
and `hx_primary_forward_scores.csv` artifacts for this scorecard.

## Row Counts

- external boundary rows: `{summary['row_counts']['external_boundary_rows']}`
- boundary score rows: `{summary['row_counts']['boundary_score_rows']}`
- HX score rows: `{summary['row_counts']['hx_score_rows']}`
- hydraulic summary rows: `{summary['row_counts']['hydraulic_summary_rows']}`
""",
        encoding="utf-8",
    )


def write_fluid_patch_plan() -> None:
    (OUT / "fluid_external_boundary_patch_plan.md").write_text(
        """---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
tags: [forward-model, predictive-1d, external-boundary, fluid]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md
task: AGENT-297
date: 2026-07-13
role: Implementer/Writer
type: work_product
status: complete
---
# Fluid External Boundary Patch Plan

## Goal

Add an `external_boundary_table` outer-boundary mode to
`../cfd-modeling-tools/tamu_first_order_model/Fluid` that consumes
`cfd_external_boundary_dictionary.csv`.

## Current Fluid Implementation Map

- `tamu_loop_model_v2/solver.py`: `ScenarioConfig` carries `radiation_on`,
  `ambient_loss_model`, `outer_closure_mode`, and per-parent outer multipliers.
- `tamu_loop_model_v2/config_loader.py`: `_scenario_from_mapping()` parses
  scenario fields; `CampaignPlan` already has the pattern for external tables.
- `tamu_loop_model_v2/ethan_coupling.py`: current fixed external-loss replay
  loader for `external_prescribed_segment_loss`.
- `tamu_loop_model_v2/solver.py`: `wall_and_insulation_resistances_per_length()`
  computes internal HTC, wall/insulation/external convection, optional
  linearized radiation, and wall/surface temperatures.
- `tamu_loop_model_v2/solver.py`: `ambient_loss_for_segment()` dispatches
  adiabatic, fixed prescribed loss, HX-zero ambient, or internal resistance
  network losses.
- `tamu_loop_model_v2/solver.py`: `_outer_closure_multipliers_for_segment()`
  currently supports only `baseline` and `per_parent_multiplier`.
- `tamu_loop_model_v2/solver.py` and `reporting.py`: `SegmentState`,
  `_segment_dataframe()`, and `write_case_report()` emit segment-state
  diagnostics.

## Minimal Edit Points

1. Add `ambient_loss_model: external_boundary_table` and do not overload
   `external_prescribed_segment_loss`, which is fixed realized-loss replay.
2. Extend the Fluid scenario/config object with:
   - `outer_closure_mode: external_boundary_table`
   - `external_boundary_table_path`
   - `external_boundary_drive_selector`
3. Add a small loader, preferably `external_boundary.py`, keyed by case plus
   segment/parent/role.
4. Extend `solve_case()`, `pressure_residual()`,
   `solve_temperature_periodicity()`, `march_temperatures()`, and
   `ambient_loss_for_segment()` to pass an optional boundary table alongside
   existing `prescribed_segment_losses_W`.
5. Refactor `wall_and_insulation_resistances_per_length()` to accept optional
   boundary overrides: `h`, `Ta`, `Tsur`, emissivity, added layer resistance,
   and drive-temperature selector.
6. For setup parity, compute passive external loss from `area`, `h`, `Ta`,
   `Tsur`, emissivity, and wall/layer metadata.
7. For realized-flux replay, consume realized `wallHeatFlux` as total heat
   transfer and do not add radiation again.
8. Write segment-state diagnostics that separate convective external loss,
   radiative external loss, imposed source/sink duty, realized replay duty, and
   residual; include `external_Ta_K`, `external_Tsur_K`,
   `external_emissivity`, `table_h_ext_W_m2K`, and boundary source/mode.

## Required Tests

- emissivity `0` removes radiative heat loss;
- changing `Tsur` changes radiative heat loss;
- realized-flux replay does not add radiation;
- missing provenance/path/unit fields fail closed;
- existing `internal_model` and `external_prescribed_segment_loss` modes remain
  unchanged.

## Current Constraint

This `ethan_runs` sandbox has write permission only in `ethan_runs` and `/tmp`,
so this package stops at a Fluid-ready contract and exact patch plan.
""",
        encoding="utf-8",
    )


def write_metadata(summary: dict[str, Any]) -> None:
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    external_rows = build_external_bc_dictionary()
    boundary_scores = build_boundary_scorecard()
    hx_scores = build_hx_scorecard()
    hydraulic_summary = build_hydraulic_summary()
    decisions = build_decision_table()

    write_csv(OUT / "cfd_external_boundary_dictionary.csv", external_rows, EXTERNAL_BC_COLUMNS)
    write_csv(OUT / "boundary_mode_scorecard.csv", boundary_scores, BOUNDARY_SCORE_COLUMNS)
    write_csv(OUT / "hx_validation_guardrail_scorecard.csv", hx_scores, HX_SCORE_COLUMNS)
    write_csv(OUT / "hydraulic_guardrail_summary.csv", hydraulic_summary, HYDRAULIC_SUMMARY_COLUMNS)
    write_csv(OUT / "implementation_decision_table.csv", decisions, DECISION_COLUMNS)

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "git_rev": git_rev(),
        "source_paths": {
            "patch_table": rel(PATCH_TABLE),
            "patch_parity_contract": rel(PATCH_PARITY_CONTRACT),
            "wall_layer_drive": rel(WALL_LAYER_DRIVE),
            "wall_layer_parity": rel(WALL_LAYER_PARITY),
            "validation_split": rel(VALIDATION_SPLIT),
            "hx_forward_scores": rel(HX_FORWARD_SCORES),
            "hx_fit_parameters": rel(HX_FIT_PARAMETERS),
            "hx_validation_splits": rel(HX_VALIDATION_SPLITS),
            "hydraulic_residuals": rel(HYDRAULIC_RESIDUALS),
        },
        "row_counts": {
            "external_boundary_rows": len(external_rows),
            "boundary_score_rows": len(boundary_scores),
            "hx_score_rows": len(hx_scores),
            "hydraulic_summary_rows": len(hydraulic_summary),
            "decision_rows": len(decisions),
        },
        "fluid_source_modified": False,
        "native_solver_outputs_modified": False,
        "hx_package_caveat": "fit_protocol_status.csv and validation_split_requirements.csv are stale; use hx_validation_splits.csv, hx_fit_parameters.csv, and hx_primary_forward_scores.csv",
        "radiation_policy": "setup parity includes emissivity/Tsur radiation; realized wallHeatFlux replay does not add separate radiation",
    }

    write_readme(summary)
    write_fluid_patch_plan()
    write_metadata(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary["row_counts"], indent=2))


if __name__ == "__main__":
    main()
