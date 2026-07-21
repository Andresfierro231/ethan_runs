#!/usr/bin/env python3
"""Build an external-BC and thermal-profile parity study for Salt2-4.

This is a reproducible documentation/analysis package. It does not run
OpenFOAM, does not mutate native CFD outputs, and does not edit external Fluid
source. Realized CFD wallHeatFlux is used only as diagnostic evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import socket
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "AGENT-365"
BEST_VARIANT = "F1_heater_only"

DEFAULT_OUTPUT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study"
)

PATCH_ROLE_TABLE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)
PATCH_ROLE_SUMMARY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
)
EXTERNAL_BC_DICTIONARY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv"
)
WALL_DRIVE_TABLE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv"
)
BEST_DISCREPANCY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv"
)
BEST_CASE_SUMMARY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_case_heat_loss_summary.csv"
)
BEST_MODEL_CHANGES = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/model_change_recommendations.csv"
)
AGENT350_ALIGNMENT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_segment.csv"
)
RADIATION_MAP = REPO_ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"
FORWARD_MAP = REPO_ROOT / "operational_notes/maps/forward-predictive-model.md"
FLUID_BRIDGE_README = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_fluid_api_localized_loss_external_bc_bridge/README.md"
)

SOURCE_PATHS = [
    PATCH_ROLE_TABLE,
    PATCH_ROLE_SUMMARY,
    EXTERNAL_BC_DICTIONARY,
    WALL_DRIVE_TABLE,
    BEST_DISCREPANCY,
    BEST_CASE_SUMMARY,
    BEST_MODEL_CHANGES,
    AGENT350_ALIGNMENT,
    RADIATION_MAP,
    FORWARD_MAP,
    FLUID_BRIDGE_README,
]

LEG_ORDER = {
    "lower_leg": 0,
    "upcomer": 1,
    "cooling_branch": 2,
    "downcomer": 3,
    "junction": 4,
}

VALIDATION_SPLIT = {
    "salt_2": "train",
    "salt_3": "validation",
    "salt_4": "holdout",
}

SOURCE_KIND_BY_ROLE = {
    "heater": "active_source",
    "test_section": "active_source_or_loss",
    "cooler": "active_sink",
    "ambient_wall": "passive_external_loss",
    "junction_other": "passive_external_loss_or_geometry_gap",
}

PATCH_COLUMNS = [
    "case_id",
    "source_id",
    "patch_name",
    "role",
    "role_group",
    "bc_type",
    "one_d_segment",
    "parent_span",
    "area_m2",
    "h_W_m2K",
    "Ta_K",
    "Tsur_K",
    "emissivity",
    "thickness_total_m",
    "wall_layer_metadata_status",
    "imposed_Q_W",
    "realized_wallHeatFlux_W",
    "realized_external_loss_W",
    "source_kind",
    "setup_radiation_policy",
    "realized_flux_replay_policy",
    "predictive_runtime_policy",
    "source_paths",
]

SEGMENT_COLUMNS = [
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
    "thickness_total_m",
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

SOURCE_SINK_COLUMNS = [
    "case_id",
    "source_id",
    "one_d_segment",
    "role",
    "source_kind",
    "patch_count",
    "area_m2",
    "imposed_Q_W",
    "realized_wallHeatFlux_W",
    "realized_external_loss_W",
    "realized_minus_imposed_W",
    "contract_status",
    "runtime_policy",
    "source_paths",
]

HEAT_LOSS_COLUMNS = [
    "case_id",
    "source_id",
    "validation_split_role",
    "best_model_variant",
    "leg",
    "leg_label",
    "model_total_loss_W",
    "model_ambient_loss_W",
    "model_hx_loss_W",
    "cfd_realized_loss_W",
    "cfd_imposed_loss_W",
    "model_minus_cfd_realized_loss_W",
    "loss_discrepancy_fraction_of_heater",
    "heat_loss_bias",
    "likely_root_cause",
    "required_1d_model_change",
    "evidence_class",
    "runtime_status",
    "source_paths",
]

DRIVE_COLUMNS = [
    "case_id",
    "source_id",
    "validation_split_role",
    "one_d_segment",
    "role",
    "area_m2",
    "hA_W_K",
    "Ta_K",
    "Tsur_K",
    "emissivity",
    "cfd_realized_external_loss_W",
    "best_model_total_loss_W",
    "best_model_minus_cfd_realized_loss_W",
    "T_path_bulk_K",
    "T_wall_inner_K",
    "T_wall_shell_K",
    "T_ext_drive_loss_positive_K",
    "wall_shell_minus_path_bulk_K",
    "recirculation_status",
    "drive_diagnosis",
    "recommended_next_model",
    "admission_status",
    "source_paths",
]

CASE_COLUMNS = [
    "case_id",
    "source_id",
    "validation_split_role",
    "best_model_variant",
    "model_total_loss_W",
    "cfd_realized_total_loss_W",
    "model_minus_cfd_realized_total_loss_W",
    "largest_over_loss_leg",
    "largest_under_loss_leg",
    "largest_abs_loss_discrepancy_leg",
    "case_interpretation",
    "admission_status",
]

ADMISSION_COLUMNS = [
    "decision_id",
    "scope",
    "status",
    "decision",
    "basis",
    "source_paths",
]

MANIFEST_COLUMNS = [
    "source_id",
    "path",
    "exists",
    "size_bytes",
    "sha256_16",
    "role",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return round(value, 9)
    return value


def fnum(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def source_join(*paths: Path) -> str:
    return ";".join(rel(path) for path in paths)


def sha16(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def external_loss_from_wallflux(row: dict[str, str]) -> float:
    role = row.get("role", "")
    realized = fnum(row.get("realized_wallHeatFlux_W"))
    if role in {"ambient_wall", "junction_other", "cooler"}:
        return -realized
    return 0.0


def source_kind(role: str) -> str:
    return SOURCE_KIND_BY_ROLE.get(role, "other_boundary_role")


def likely_root_cause(leg: str, bias: str) -> str:
    if leg == "junction":
        return "missing_junction_stub_connector_external_loss_area"
    if leg == "lower_leg":
        return "heater_realization_and_lower_leg_wall_loss_are_coupled"
    if leg == "cooling_branch":
        return "active_hx_sink_and_passive_upper_leg_loss_are_not_separated"
    if leg in {"upcomer", "downcomer"} and bias == "model_over_loses_heat":
        return "bulk_temperature_external_loss_drive_too_hot_for_stratified_wall_adjacent_flow"
    return "leg_level_heat_loss_model_form_mismatch"


def patch_contract_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(PATCH_ROLE_TABLE):
        role = row["role"]
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "patch_name": row["patch_name"],
                "role": role,
                "role_group": row["role_group"],
                "bc_type": row["bc_type"],
                "one_d_segment": row["one_d_segment"],
                "parent_span": row["parent_span"],
                "area_m2": fnum(row.get("area_m2")),
                "h_W_m2K": row.get("h_W_m2K", ""),
                "Ta_K": row.get("Ta_K", ""),
                "Tsur_K": row.get("Tsur_K", ""),
                "emissivity": row.get("emissivity", ""),
                "thickness_total_m": row.get("thickness_total_m", ""),
                "wall_layer_metadata_status": row.get("wall_layer_metadata_status", ""),
                "imposed_Q_W": fnum(row.get("imposed_Q_W")),
                "realized_wallHeatFlux_W": fnum(row.get("realized_wallHeatFlux_W")),
                "realized_external_loss_W": external_loss_from_wallflux(row),
                "source_kind": source_kind(role),
                "setup_radiation_policy": (
                    "include_rcExternalTemperature_emissivity_Tsur_for_setup_prediction"
                    if row.get("bc_type") == "rcExternalTemperature"
                    else "no_separate_radiation_metadata_on_this_patch"
                ),
                "realized_flux_replay_policy": "do_not_add_radiation_to_realized_CFD_wallHeatFlux",
                "predictive_runtime_policy": (
                    "allowed_as_setup_boundary_input_not_validation_target"
                    if role in {"ambient_wall", "junction_other"}
                    else "document_source_sink_separately_not_passive_external_fit"
                ),
                "source_paths": source_join(PATCH_ROLE_TABLE),
            }
        )
    return rows


def segment_equivalent_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(EXTERNAL_BC_DICTIONARY):
        copied = {column: row.get(column, "") for column in SEGMENT_COLUMNS}
        copied["validation_split_role"] = VALIDATION_SPLIT.get(row["case_id"], row.get("validation_split_role", ""))
        copied["source_paths"] = source_join(EXTERNAL_BC_DICTIONARY, PATCH_ROLE_TABLE)
        rows.append(copied)
    rows.sort(key=lambda r: (r["case_id"], LEG_ORDER.get(r["one_d_segment"], 99), r["role"]))
    return rows


def source_sink_contract_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(EXTERNAL_BC_DICTIONARY):
        role = row["role"]
        if role == "ambient_wall":
            continue
        imposed = fnum(row.get("imposed_Q_W"))
        realized = fnum(row.get("realized_wallHeatFlux_W"))
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "one_d_segment": row["one_d_segment"],
                "role": role,
                "source_kind": source_kind(role),
                "patch_count": row.get("patch_count", ""),
                "area_m2": row.get("area_m2", ""),
                "imposed_Q_W": imposed,
                "realized_wallHeatFlux_W": realized,
                "realized_external_loss_W": row.get("realized_external_loss_W", ""),
                "realized_minus_imposed_W": realized - imposed,
                "contract_status": (
                    "diagnostic_realized_flux_available_keep_out_of_runtime_prediction"
                    if role in {"heater", "cooler", "test_section"}
                    else "geometry_external_loss_contract_needed"
                ),
                "runtime_policy": (
                    "setup_input_or_predictive_submodel_required_not_realized_CFD_wallHeatFlux"
                    if role in {"heater", "cooler", "test_section"}
                    else "passive_external_boundary_table_candidate"
                ),
                "source_paths": source_join(EXTERNAL_BC_DICTIONARY, PATCH_ROLE_SUMMARY),
            }
        )
    rows.sort(key=lambda r: (r["case_id"], LEG_ORDER.get(r["one_d_segment"], 99), r["role"]))
    return rows


def heat_loss_comparison_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(BEST_DISCREPANCY):
        leg = row["leg"]
        required_change = row["recommended_model_change"]
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "validation_split_role": VALIDATION_SPLIT.get(row["case_id"], ""),
                "best_model_variant": row["best_model_variant"],
                "leg": leg,
                "leg_label": row["leg_label"],
                "model_total_loss_W": fnum(row["model_total_loss_W"]),
                "model_ambient_loss_W": fnum(row["model_ambient_loss_W"]),
                "model_hx_loss_W": fnum(row["model_hx_loss_W"]),
                "cfd_realized_loss_W": fnum(row["cfd_realized_loss_W"]),
                "cfd_imposed_loss_W": fnum(row["cfd_imposed_loss_W"]),
                "model_minus_cfd_realized_loss_W": fnum(row["model_minus_cfd_realized_loss_W"]),
                "loss_discrepancy_fraction_of_heater": fnum(row["loss_discrepancy_fraction_of_heater"]),
                "heat_loss_bias": row["heat_loss_bias"],
                "likely_root_cause": likely_root_cause(leg, row["heat_loss_bias"]),
                "required_1d_model_change": required_change,
                "evidence_class": "diagnostic_model_form_heat_loss_placement",
                "runtime_status": row["runtime_status"],
                "source_paths": source_join(BEST_DISCREPANCY, EXTERNAL_BC_DICTIONARY, WALL_DRIVE_TABLE),
            }
        )
    rows.sort(key=lambda r: (r["case_id"], LEG_ORDER.get(r["leg"], 99)))
    return rows


def best_discrepancy_by_case_leg() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_id"], row["leg"]): row for row in read_csv(BEST_DISCREPANCY)}


def drive_comparison_rows() -> list[dict[str, Any]]:
    best = best_discrepancy_by_case_leg()
    rows = []
    for row in read_csv(WALL_DRIVE_TABLE):
        role = row["role"]
        if role not in {"ambient_wall", "junction_other"}:
            continue
        case_id = row["case_id"]
        segment = row["one_d_segment"]
        disc = best.get((case_id, segment), {})
        wall_shell = fnum(row.get("T_wall_shell_K"), math.nan)
        bulk = fnum(row.get("T_path_bulk_K"), math.nan)
        wall_minus_bulk = wall_shell - bulk if math.isfinite(wall_shell) and math.isfinite(bulk) else math.nan
        discrepancy = fnum(disc.get("model_minus_cfd_realized_loss_W"))
        if not math.isfinite(wall_minus_bulk):
            diagnosis = "missing_wall_shell_or_bulk_drive"
            next_model = "stage_matched_wall_adjacent_temperature_extraction_or_use_segment_equivalent_contract_only"
            admission = "blocked_missing_drive_temperature"
        elif discrepancy > 0 and wall_minus_bulk < 0:
            diagnosis = "wall_adjacent_proxy_cooler_than_bulk_consistent_with_bulk_drive_over_loss"
            next_model = "test_external_boundary_table_with_wall_shell_or_wall_adjacent_drive"
            admission = "diagnostic_only_train_salt2_then_validate_salt3_holdout_salt4"
        elif discrepancy < 0:
            diagnosis = "model_under_loss_not_fixed_by_cooler_wall_drive_alone"
            next_model = "add_missing_junction_stub_connector_area_or_external_boundary_segments"
            admission = "diagnostic_only_geometry_model_change_required"
        else:
            diagnosis = "drive_temperature_effect_available_but_not_sufficient_alone"
            next_model = "compare bulk_wall_shell_and_mixing_factor_modes_under_split_gate"
            admission = "diagnostic_only"
        rows.append(
            {
                "case_id": case_id,
                "source_id": row["source_id"],
                "validation_split_role": VALIDATION_SPLIT.get(case_id, ""),
                "one_d_segment": segment,
                "role": role,
                "area_m2": row.get("area_m2", ""),
                "hA_W_K": row.get("hA_W_K", ""),
                "Ta_K": row.get("Ta_K", ""),
                "Tsur_K": row.get("Tsur_K", ""),
                "emissivity": row.get("emissivity", ""),
                "cfd_realized_external_loss_W": row.get("external_loss_realized_W", ""),
                "best_model_total_loss_W": disc.get("model_total_loss_W", ""),
                "best_model_minus_cfd_realized_loss_W": discrepancy if disc else "",
                "T_path_bulk_K": row.get("T_path_bulk_K", ""),
                "T_wall_inner_K": row.get("T_wall_inner_K", ""),
                "T_wall_shell_K": row.get("T_wall_shell_K", ""),
                "T_ext_drive_loss_positive_K": row.get("T_ext_drive_loss_positive_K", ""),
                "wall_shell_minus_path_bulk_K": wall_minus_bulk,
                "recirculation_status": row.get("recirculation_status", ""),
                "drive_diagnosis": diagnosis,
                "recommended_next_model": next_model,
                "admission_status": admission,
                "source_paths": source_join(WALL_DRIVE_TABLE, BEST_DISCREPANCY),
            }
        )
    rows.sort(key=lambda r: (r["case_id"], LEG_ORDER.get(r["one_d_segment"], 99), r["role"]))
    return rows


def case_summary_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(BEST_CASE_SUMMARY):
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "validation_split_role": VALIDATION_SPLIT.get(row["case_id"], ""),
                "best_model_variant": row["best_model_variant"],
                "model_total_loss_W": fnum(row["model_total_loss_W"]),
                "cfd_realized_total_loss_W": fnum(row["cfd_realized_total_loss_W"]),
                "model_minus_cfd_realized_total_loss_W": fnum(row["model_minus_cfd_realized_total_loss_W"]),
                "largest_over_loss_leg": row["largest_over_loss_leg"],
                "largest_under_loss_leg": row["largest_under_loss_leg"],
                "largest_abs_loss_discrepancy_leg": row["largest_abs_loss_discrepancy_leg"],
                "case_interpretation": (
                    "Aggregate heat balance is closer than leg placement because pipe-leg over-loss "
                    "partly cancels junction/stub under-loss."
                ),
                "admission_status": "diagnostic_only_best_model_uses_imposed_cooler_duty",
            }
        )
    return rows


def model_change_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(BEST_MODEL_CHANGES):
        copied = dict(row)
        copied["study_linkage"] = "carried_forward_from_best_predictive_heat_loss_discrepancy_and_tied_to_external_bc_drive_contract"
        rows.append(copied)
    return rows


def admission_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "D1",
            "scope": "realized_CFD_wallHeatFlux_replay",
            "status": "allowed_diagnostic_only",
            "decision": "Use realized wallHeatFlux to locate heat-path mismatch, not as predictive runtime input.",
            "basis": "CFD radiation is inseparable inside total wallHeatFlux; adding separate radiation would double-count.",
            "source_paths": source_join(RADIATION_MAP, PATCH_ROLE_TABLE, BEST_DISCREPANCY),
        },
        {
            "decision_id": "D2",
            "scope": "external_boundary_setup_parity",
            "status": "ready_for_setup_contract",
            "decision": "Use h/Ta/Tsur/emissivity/layer metadata from the CFD boundary contract for parity/predictive setup modes.",
            "basis": "AGENT-318 reports Fluid support for external_boundary_table fields; this package does not rerun Fluid.",
            "source_paths": source_join(EXTERNAL_BC_DICTIONARY, FLUID_BRIDGE_README),
        },
        {
            "decision_id": "D3",
            "scope": "radiation_off_runs",
            "status": "sensitivity_only",
            "decision": "Do not call radiation-off 1D runs CFD parity.",
            "basis": "The stale cfd-no-radiation-parity blocker is superseded; rcExternalTemperature includes emissivity/Tsur effects.",
            "source_paths": source_join(RADIATION_MAP),
        },
        {
            "decision_id": "D4",
            "scope": "current_best_predictive_style_model",
            "status": "diagnostic_model_form_evidence",
            "decision": "Use F1_heater_only for heat-loss placement diagnosis but not final predictive-HX validation.",
            "basis": "The model still consumes imposed cooler duty and therefore is not setup-only predictive.",
            "source_paths": source_join(BEST_DISCREPANCY, FORWARD_MAP),
        },
        {
            "decision_id": "D5",
            "scope": "thermal_profile_internal_drive",
            "status": "not_admitted_for_closure_fit",
            "decision": "Treat wall-shell/wall-adjacent drive as a diagnostic next model until Salt2 train, Salt3 validation, Salt4 holdout gates are run.",
            "basis": "Current wall-drive rows explain some over-loss behavior but do not constitute a validated internal Nu or HTC closure.",
            "source_paths": source_join(WALL_DRIVE_TABLE, AGENT350_ALIGNMENT),
        },
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    roles = {
        PATCH_ROLE_TABLE: "patch_level_external_boundary_contract",
        PATCH_ROLE_SUMMARY: "role_level_area_heat_summary",
        EXTERNAL_BC_DICTIONARY: "segment_equivalent_external_boundary_dictionary",
        WALL_DRIVE_TABLE: "thermal_profile_drive_inputs",
        BEST_DISCREPANCY: "best_predictive_leg_heat_loss_discrepancy",
        BEST_CASE_SUMMARY: "best_predictive_case_summary",
        BEST_MODEL_CHANGES: "prior_model_change_recommendations",
        AGENT350_ALIGNMENT: "diagnostic_heat_loss_alignment",
        RADIATION_MAP: "radiation_and_double_counting_policy",
        FORWARD_MAP: "predictive_model_status",
        FLUID_BRIDGE_README: "external_boundary_api_availability",
    }
    rows = []
    for idx, path in enumerate(SOURCE_PATHS, start=1):
        rows.append(
            {
                "source_id": f"SRC-{idx:02d}",
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else "",
                "sha256_16": sha16(path),
                "role": roles[path],
            }
        )
    return rows


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(EXTERNAL_BC_DICTIONARY)}
  - {rel(WALL_DRIVE_TABLE)}
  - {rel(BEST_DISCREPANCY)}
  - {rel(RADIATION_MAP)}
tags: [thermal-parity, external-boundary, radiation, heat-loss, thesis-source]
related:
  - {rel(FORWARD_MAP)}
  - reports/thesis_dossier/README.md
task: {TASK_ID}
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# External-BC and Thermal-Profile Parity Study

## Decision

This package makes the requested 3D-vs-1D heat-release study repeatable and
presentation-ready. It starts from the same heat-path assumptions as Ethan's CFD
setup, then separates external boundary metadata, source/sink contracts,
realized CFD heat fluxes, and the thermal-profile drive problem.

The result is diagnostic/model-form evidence. It does not admit a final
predictive thermal closure because the current best executable model still uses
imposed cooler duty and because wall-adjacent drive corrections have not been
validated under the Salt2/Salt3/Salt4 split.

## Headline

- Cases: `{summary["case_count"]}` (`salt_2`, `salt_3`, `salt_4`).
- Patch contract rows: `{summary["external_bc_patch_contract_rows"]}`.
- Segment-equivalent boundary rows: `{summary["external_bc_segment_equivalent_rows"]}`.
- Heat-loss comparison rows: `{summary["section_heat_loss_comparison_rows"]}`.
- Thermal-profile drive rows: `{summary["thermal_profile_drive_rows"]}`.
- Publication-ready predictive heat-loss rows: `0`.

Main finding: the best current predictive-style model has a near-closed
aggregate heat balance for the wrong reason. It over-loses heat in pipe legs and
under-loses heat in junction/stub connector regions. That points to external
boundary placement, source/sink separation, and wall-adjacent drive as model
changes, not to one global heat-loss multiplier.

## Radiation Policy

The old assumption that CFD has no radiation is superseded. CFD
`rcExternalTemperature` includes emissivity/Tsur effects, and current exported
`wallHeatFlux` is total heat flux with radiation inseparable. Therefore:

- do not add separate 1D radiation on top of realized CFD `wallHeatFlux`;
- do not call radiation-off 1D replay CFD parity;
- setup/predictive parity must carry h, Ta, Tsur, emissivity, and layer metadata.

## Open First

1. `presentation_brief.md`
2. `section_heat_loss_comparison.csv`
3. `thermal_profile_drive_comparison.csv`
4. `external_bc_segment_equivalents.csv`
5. `methodology_and_assumptions.md`
6. `repeatability_and_refinement_guide.md`
7. `thesis_reuse_index.md`

## Files

- `external_bc_patch_contract.csv`
- `external_bc_segment_equivalents.csv`
- `source_sink_parity_contract.csv`
- `section_heat_loss_comparison.csv`
- `thermal_profile_drive_comparison.csv`
- `case_summary.csv`
- `model_change_recommendations.csv`
- `admission_decision_table.csv`
- `source_manifest.csv`
- `methodology_and_assumptions.md`
- `equations_and_sign_conventions.md`
- `presentation_brief.md`
- `repeatability_and_refinement_guide.md`
- `thesis_reuse_index.md`
- `summary.json`
"""


def methodology_text() -> str:
    return f"""# Methodology and Assumptions

## Study Ladder

1. Consolidate the CFD external-boundary and source/sink contract.
2. Preserve patch-level provenance, then form segment-equivalent 1D boundary rows.
3. Compare current best predictive-style 1D heat loss against CFD realized heat
   loss by physical leg.
4. Diagnose whether bulk-temperature external loss drive is plausible using
   existing wall/shell temperature proxies.
5. Classify each result as setup contract, diagnostic-only, blocked, or future
   validation candidate.

## Inputs

- Patch-level CFD boundary table: `{rel(PATCH_ROLE_TABLE)}`.
- Fluid-ready segment-equivalent external boundary table:
  `{rel(EXTERNAL_BC_DICTIONARY)}`.
- Wall-layer drive table: `{rel(WALL_DRIVE_TABLE)}`.
- Best predictive-style heat-loss discrepancy:
  `{rel(BEST_DISCREPANCY)}`.

## Assumptions

- Salt split is fixed: Salt2 trains, Salt3 validates, Salt4 is holdout.
- Realized CFD `wallHeatFlux` can diagnose heat-path placement but cannot be a
  runtime predictive input.
- CFD radiation is embedded in `wallHeatFlux`; it is not separately exported as
  `qr`.
- The current best model is `F1_heater_only`, which still uses imposed cooler
  duty. It is useful for model-form diagnosis, not final predictive-HX scoring.
- Wall-shell temperatures are proxies from existing postprocessing and remain
  diagnostic until a gated forward rerun validates a model form.

## Interpretation Rules

- Pipe-leg over-loss plus junction under-loss means aggregate balance is not an
  adequate success metric.
- Heater, cooler, test section, passive walls, and junction/stub losses must
  remain separate lanes.
- Internal Nu/HTC must not absorb passive external-boundary, radiation, heater,
  cooler, or missing-geometry residuals.
"""


def equations_text() -> str:
    return """# Equations and Sign Conventions

## Heat Loss Sign

This package reports `*_loss_W` as positive when heat leaves the fluid/control
volume. Native OpenFOAM `realized_wallHeatFlux_W` signs are converted only for
diagnostic loss columns:

```text
realized_external_loss_W = -realized_wallHeatFlux_W
```

for passive ambient, junction, and cooler roles. Heater realized heat remains a
source/sink contract quantity and is not treated as passive external loss.

## Leg Discrepancy

```text
model_minus_cfd_realized_loss_W
  = model_total_loss_W - cfd_realized_loss_W
```

Positive means the 1D model loses too much heat in that leg. Negative means it
loses too little heat there.

## External Boundary Contract

The segment-equivalent external boundary preserves the CFD setup fields:

```text
hA = sum_patches(h_patch * A_patch)
Ta = setup ambient temperature
Tsur = setup radiative surroundings temperature
epsilon = setup emissivity
layer metadata = wall/insulation resistance contract
```

Radiation is not added to realized CFD `wallHeatFlux` replay. It belongs in the
setup/predictive external-boundary model.

## Thermal Drive Diagnostic

The wall-profile diagnostic compares bulk/path temperature against existing
wall-shell proxy temperature:

```text
wall_shell_minus_path_bulk_K = T_wall_shell_K - T_path_bulk_K
```

If the 1D model over-loses heat while the wall-shell proxy is cooler than the
bulk/path temperature, that supports testing wall-adjacent or mixed drive
temperatures. It is not, by itself, an admitted internal Nu closure.
"""


def presentation_text() -> str:
    return """# Presentation Brief

## One-Sentence Takeaway

The current best 1D predictive-style model releases about the right total heat
only by cancellation: it loses too much heat in pipe legs and too little in
junction/stub connector regions.

## What This Study Adds

- A patch-level CFD external-boundary/source contract.
- Segment-equivalent h/Ta/Tsur/emissivity/layer rows for 1D setup parity.
- A radiation policy that prevents double-counting.
- A leg-by-leg comparison for Salt2 train, Salt3 validation, and Salt4 holdout.
- A thermal-profile drive diagnosis showing where bulk temperature is likely
  the wrong external-loss driver.

## Slide-Ready Claims

- CFD `rcExternalTemperature` includes radiation; radiation-off replay is only a
  sensitivity.
- Realized CFD `wallHeatFlux` is diagnostic evidence, not a runtime predictive
  input.
- The biggest model-form issue is heat-loss placement, especially missing
  junction/stub loss and over-loss in pipe legs.
- Next 1D refinement should use external-boundary dictionaries and wall-adjacent
  drive tests before fitting internal Nu.

## Figure Suggestions

1. Stacked bar: CFD realized loss vs best 1D loss by leg for Salt2-4.
2. Residual bar: model-minus-CFD heat loss by leg.
3. External boundary circuit schematic: h/Ta/Tsur/emissivity/layers to
   environment, with realized wallHeatFlux kept separate.
4. Thermal drive diagnostic: bulk/path temperature vs wall-shell proxy by leg.
"""


def repeatability_text() -> str:
    return """# Repeatability and Refinement Guide

## Exact Rerun

From repo root:

```bash
python3.11 tools/analyze/build_external_bc_thermal_profile_parity_study.py
python3.11 -m unittest tools.analyze.test_external_bc_thermal_profile_parity_study
```

## Expected Row Counts

- `external_bc_patch_contract.csv`: 207 rows.
- `external_bc_segment_equivalents.csv`: 24 rows.
- `source_sink_parity_contract.csv`: 12 rows.
- `section_heat_loss_comparison.csv`: 15 rows.
- `thermal_profile_drive_comparison.csv`: 15 rows.
- `case_summary.csv`: 3 rows.
- `admission_decision_table.csv`: 5 rows.

## Reuse With a Refined 1D Model

1. Land the new 1D run with per-segment heat source, HX loss, and ambient loss
   columns.
2. Rebuild the leg-level discrepancy table against the same CFD contract.
3. Do not judge success by aggregate heat balance alone.
4. Check whether junction under-loss shrinks and pipe-leg over-loss does not
   grow.
5. If fitting a wall-adjacent or mixing-factor drive, train only on Salt2,
   validate on Salt3, and hold out Salt4.

## Guardrails

- Do not use realized CFD wallHeatFlux, CFD mdot, or validation temperatures as
  runtime predictive inputs.
- Do not add a separate radiation term to realized CFD wallHeatFlux.
- Do not call imposed cooler duty final predictive HX.
- Do not hide heater, cooler, junction, or wall-drive errors in one global
  ambient multiplier.
"""


def thesis_text() -> str:
    return """# Thesis Reuse Index

## Thesis Claim Status

Supported diagnostic claim:

> The best current 1D predictive-style model can appear close in aggregate heat
> balance while losing heat in the wrong physical locations.

Boundary-condition claim:

> CFD and 1D parity must be defined at the external thermal circuit level:
> h, Ta, Tsur, emissivity, wall/layer resistance, and source/sink roles. Current
> CFD realized wallHeatFlux already includes inseparable radiation effects.

Not yet supported:

> A final predictive thermal model, final predictive-HX scoring, or admitted
> internal Nu closure.

Short label: not final predictive-HX scoring.

## Where To Cite This Package

- Methods chapter: external-boundary parity definition and sign conventions.
- Results chapter: leg-level heat-loss placement discrepancy.
- Discussion chapter: why developing/stratified thermal profiles make bulk
  temperature a poor external-loss drive in some legs.
- Future work: setup-only HX model, heater realization model, junction/stub
  heat-loss coverage, and wall-adjacent drive validation.
"""


def build_package(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    patch_rows = patch_contract_rows()
    segment_rows = segment_equivalent_rows()
    source_sink_rows = source_sink_contract_rows()
    heat_rows = heat_loss_comparison_rows()
    drive_rows = drive_comparison_rows()
    case_rows = case_summary_rows()
    changes = model_change_rows()
    admissions = admission_decision_rows()
    manifest = source_manifest_rows()

    write_csv(output_dir / "external_bc_patch_contract.csv", patch_rows, PATCH_COLUMNS)
    write_csv(output_dir / "external_bc_segment_equivalents.csv", segment_rows, SEGMENT_COLUMNS)
    write_csv(output_dir / "source_sink_parity_contract.csv", source_sink_rows, SOURCE_SINK_COLUMNS)
    write_csv(output_dir / "section_heat_loss_comparison.csv", heat_rows, HEAT_LOSS_COLUMNS)
    write_csv(output_dir / "thermal_profile_drive_comparison.csv", drive_rows, DRIVE_COLUMNS)
    write_csv(output_dir / "case_summary.csv", case_rows, CASE_COLUMNS)
    write_csv(
        output_dir / "model_change_recommendations.csv",
        changes,
        list(read_csv(BEST_MODEL_CHANGES)[0].keys()) + ["study_linkage"],
    )
    write_csv(output_dir / "admission_decision_table.csv", admissions, ADMISSION_COLUMNS)
    write_csv(output_dir / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    summary = {
        "task": TASK_ID,
        "generated_utc": utc_now(),
        "host": socket.gethostname(),
        "output_dir": rel(output_dir),
        "case_count": len({row["case_id"] for row in heat_rows}),
        "best_model_variant": BEST_VARIANT,
        "external_bc_patch_contract_rows": len(patch_rows),
        "external_bc_segment_equivalent_rows": len(segment_rows),
        "source_sink_parity_contract_rows": len(source_sink_rows),
        "section_heat_loss_comparison_rows": len(heat_rows),
        "thermal_profile_drive_rows": len(drive_rows),
        "case_summary_rows": len(case_rows),
        "admission_decision_rows": len(admissions),
        "publication_ready_predictive_heat_loss_rows": 0,
        "evidence_class": "diagnostic_model_form_and_setup_contract",
        "predictive_hx_admitted": False,
        "internal_nu_closure_admitted": False,
        "native_solver_outputs_mutated": False,
        "heavy_openfoam_run": False,
        "external_fluid_modified": False,
        "radiation_policy": "CFD wallHeatFlux includes inseparable rcExternalTemperature radiation; do not add separate radiation in realized-flux replay.",
        "primary_finding": "Best current predictive-style model over-loses heat in pipe legs and under-loses heat in junction/stub connector regions.",
    }

    write_text(output_dir / "README.md", readme_text(summary))
    write_text(output_dir / "methodology_and_assumptions.md", methodology_text())
    write_text(output_dir / "equations_and_sign_conventions.md", equations_text())
    write_text(output_dir / "presentation_brief.md", presentation_text())
    write_text(output_dir / "repeatability_and_refinement_guide.md", repeatability_text())
    write_text(output_dir / "thesis_reuse_index.md", thesis_text())
    write_text(output_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = build_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
