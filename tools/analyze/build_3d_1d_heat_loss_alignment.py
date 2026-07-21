#!/usr/bin/env python3
"""Build a diagnostic 3D-vs-1D heat-loss alignment package.

This package compares where Ethan CFD adds/removes heat against where existing
fixed-mdot 1D replay modes add/remove heat. It is a diagnostic parity product,
not a predictive score: realized CFD wallHeatFlux and CFD mdot are evidence
used to locate heat-path mismatches, not forward-model runtime inputs.
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
TASK_ID = "AGENT-350"

DEFAULT_OUTPUT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment"
)

PATCHWISE_ENTHALPY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/patchwise_heat_ledger_enthalpy_interfaces.csv"
)
PATCH_ROLE_SUMMARY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
)
SECTION_HEAT_BALANCE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv"
)
PARITY_RESULTS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/fixed_mdot_parity_results.csv"
)
PARITY_DECISIONS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/parity_decision_table.csv"
)
NO_RAD_SECTION = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/section_heat_loss_comparison.csv"
)
NO_RAD_DISCREPANCY = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/discrepancy_attribution.csv"
)
NO_RAD_CONTRACT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/cfd_boundary_condition_contract_no_radiation.csv"
)
RUNTIME_INPUTS = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/case_runtime_inputs_forward_v0.csv"
)
HEATER_LEDGER = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_heat_ledger.csv"
)
BOUNDARY_DECISION = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md"
)

SOURCE_PATHS = [
    PATCHWISE_ENTHALPY,
    PATCH_ROLE_SUMMARY,
    SECTION_HEAT_BALANCE,
    PARITY_RESULTS,
    PARITY_DECISIONS,
    NO_RAD_SECTION,
    NO_RAD_DISCREPANCY,
    NO_RAD_CONTRACT,
    RUNTIME_INPUTS,
    HEATER_LEDGER,
    BOUNDARY_DECISION,
]

PARENT_TO_SEGMENT = {
    "heated_incline": "lower_leg",
    "left_upper_vertical": "upcomer",
    "right_vertical": "downcomer",
    "cooled_incline_hx_active": "cooling_branch",
    "top_horizontal_exit": "junction",
    "test_section": "upcomer",
}

SEGMENT_ORDER = {
    "lower_leg": 0,
    "upcomer": 1,
    "cooling_branch": 2,
    "downcomer": 3,
    "junction": 4,
}

SEGMENT_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "path_family",
    "one_d_segment",
    "fluid_parent_segment",
    "model_source_W",
    "model_cooler_loss_W",
    "model_external_loss_W",
    "model_total_loss_W",
    "model_net_to_fluid_W",
    "cfd_imposed_source_W",
    "cfd_imposed_loss_W",
    "cfd_imposed_net_to_fluid_W",
    "cfd_realized_source_W",
    "cfd_realized_loss_W",
    "cfd_realized_net_to_fluid_W",
    "model_minus_cfd_realized_net_W",
    "model_minus_cfd_imposed_net_W",
    "realized_residual_fraction_of_heater",
    "imposed_residual_fraction_of_heater",
    "sign_match_vs_realized",
    "sign_match_vs_imposed",
    "location_match_status",
    "magnitude_status_vs_realized",
    "evidence_class",
    "admissibility_status",
    "source_paths",
    "notes",
]

ASSUMPTION_COLUMNS = [
    "case_id",
    "assumption_id",
    "ethan_3d_assumption",
    "one_d_assumption",
    "match_status",
    "evidence_class",
    "source_paths",
    "notes",
]

ROLE_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "role_or_lane",
    "role_group",
    "model_W",
    "cfd_imposed_W",
    "cfd_realized_W",
    "model_minus_cfd_realized_W",
    "evidence_class",
    "source_paths",
    "interpretation",
]

CASE_COLUMNS = [
    "case_id",
    "source_id",
    "path_id",
    "path_family",
    "heater_power_W",
    "model_net_to_fluid_W",
    "cfd_imposed_net_to_fluid_W",
    "cfd_realized_net_to_fluid_W",
    "model_minus_cfd_realized_net_W",
    "model_minus_cfd_imposed_net_W",
    "abs_realized_residual_fraction_of_heater",
    "largest_segment_residual",
    "segments_with_sign_match_vs_realized",
    "segments_total",
    "study_status",
    "thesis_use_status",
    "notes",
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


def split_signed_heat(value: float) -> tuple[float, float]:
    """Return source, loss magnitudes for signed heat into fluid."""
    if value >= 0.0:
        return value, 0.0
    return 0.0, abs(value)


def sign_label(value: float, tolerance: float = 1e-9) -> str:
    if value > tolerance:
        return "source_to_fluid"
    if value < -tolerance:
        return "loss_from_fluid"
    return "near_zero"


def sign_match(model: float, reference: float) -> str:
    model_sign = sign_label(model)
    ref_sign = sign_label(reference)
    if model_sign == ref_sign:
        return "match"
    if "near_zero" in {model_sign, ref_sign}:
        return "zero_mismatch"
    return "opposite_sign"


def parse_json_map(text: str) -> dict[str, float]:
    if not text or text == "{}":
        return {}
    parsed = json.loads(text)
    return {str(key): fnum(value) for key, value in parsed.items()}


def source_join(*paths: Path) -> str:
    return ";".join(rel(path) for path in paths)


def heater_power_by_case() -> dict[str, float]:
    return {row["case_id"]: fnum(row["heater_power_W"]) for row in read_csv(RUNTIME_INPUTS)}


def base_segment_rows() -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_csv(SECTION_HEAT_BALANCE):
        key = (row["case_id"], row["one_d_segment"])
        item = grouped.setdefault(
            key,
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "one_d_segment": row["one_d_segment"],
                "fluid_parent_segment": row["fluid_parent_segment"],
                "cfd_imposed_source_W": 0.0,
                "cfd_imposed_loss_W": 0.0,
                "cfd_realized_source_W": 0.0,
                "cfd_realized_loss_W": 0.0,
            },
        )
        item["cfd_imposed_source_W"] += fnum(row.get("imposed_source_W"))
        item["cfd_imposed_loss_W"] += fnum(row.get("imposed_loss_W"))
        item["cfd_realized_source_W"] += fnum(row.get("realized_source_W"))
        item["cfd_realized_loss_W"] += fnum(row.get("realized_loss_W"))

    for item in grouped.values():
        item["cfd_imposed_net_to_fluid_W"] = item["cfd_imposed_source_W"] - item["cfd_imposed_loss_W"]
        item["cfd_realized_net_to_fluid_W"] = item["cfd_realized_source_W"] - item["cfd_realized_loss_W"]
    return grouped


def classify_location(model_net: float, imposed_net: float, realized_net: float) -> str:
    model_zero = abs(model_net) <= 1e-9
    reference_zero = abs(imposed_net) <= 1e-9 and abs(realized_net) <= 1e-9
    if model_zero and reference_zero:
        return "both_zero"
    if model_zero and not reference_zero:
        return "model_missing_heat_path"
    if not model_zero and reference_zero:
        return "model_extra_heat_path"
    return "same_segment_heat_path_present"


def magnitude_status(residual: float, heater_power: float) -> str:
    threshold = max(10.0, 0.05 * heater_power)
    if abs(residual) <= threshold:
        return "within_screen_threshold"
    return "mismatched_magnitude"


def segment_output_row(
    *,
    base: dict[str, Any],
    path_id: str,
    path_family: str,
    model_source: float,
    model_cooler_loss: float,
    model_external_loss: float,
    evidence_class: str,
    admissibility_status: str,
    source_paths: str,
    heater_power: float,
    notes: str,
) -> dict[str, Any]:
    model_total_loss = model_cooler_loss + model_external_loss
    model_net = model_source - model_total_loss
    realized_net = fnum(base["cfd_realized_net_to_fluid_W"])
    imposed_net = fnum(base["cfd_imposed_net_to_fluid_W"])
    realized_residual = model_net - realized_net
    imposed_residual = model_net - imposed_net
    return {
        "case_id": base["case_id"],
        "source_id": base["source_id"],
        "path_id": path_id,
        "path_family": path_family,
        "one_d_segment": base["one_d_segment"],
        "fluid_parent_segment": base["fluid_parent_segment"],
        "model_source_W": model_source,
        "model_cooler_loss_W": model_cooler_loss,
        "model_external_loss_W": model_external_loss,
        "model_total_loss_W": model_total_loss,
        "model_net_to_fluid_W": model_net,
        "cfd_imposed_source_W": base["cfd_imposed_source_W"],
        "cfd_imposed_loss_W": base["cfd_imposed_loss_W"],
        "cfd_imposed_net_to_fluid_W": imposed_net,
        "cfd_realized_source_W": base["cfd_realized_source_W"],
        "cfd_realized_loss_W": base["cfd_realized_loss_W"],
        "cfd_realized_net_to_fluid_W": realized_net,
        "model_minus_cfd_realized_net_W": realized_residual,
        "model_minus_cfd_imposed_net_W": imposed_residual,
        "realized_residual_fraction_of_heater": realized_residual / heater_power if heater_power else "",
        "imposed_residual_fraction_of_heater": imposed_residual / heater_power if heater_power else "",
        "sign_match_vs_realized": sign_match(model_net, realized_net),
        "sign_match_vs_imposed": sign_match(model_net, imposed_net),
        "location_match_status": classify_location(model_net, imposed_net, realized_net),
        "magnitude_status_vs_realized": magnitude_status(realized_residual, heater_power),
        "evidence_class": evidence_class,
        "admissibility_status": admissibility_status,
        "source_paths": source_paths,
        "notes": notes,
    }


def fixed_q_segment_rows(
    base_rows: dict[tuple[str, str], dict[str, Any]],
    heater_power: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in read_csv(PARITY_RESULTS):
        path_id = result["path_id"]
        if path_id not in {"B2_realized_wallflux_roles", "B3_imposed_setup_roles"}:
            continue
        case_id = result["case_id"]
        source_map = parse_json_map(result.get("source_map_json", ""))
        loss_map = parse_json_map(result.get("loss_map_json", ""))
        source_by_segment: dict[str, float] = defaultdict(float)
        loss_by_segment: dict[str, float] = defaultdict(float)
        for parent, value in source_map.items():
            source_by_segment[PARENT_TO_SEGMENT.get(parent, parent)] += value
        for parent, value in loss_map.items():
            loss_by_segment[PARENT_TO_SEGMENT.get(parent, parent)] += value

        evidence_class = (
            "diagnostic_realized_wallflux"
            if path_id == "B2_realized_wallflux_roles"
            else "fixed_mdot_setup_diagnostic"
        )
        notes = (
            "Fixed-Q diagnostic from realized CFD wallHeatFlux; not a predictive runtime input."
            if path_id == "B2_realized_wallflux_roles"
            else "Fixed-Q replay using imposed setup heat terms; exposes setup-vs-realized discrepancy."
        )
        for key, base in sorted(base_rows.items(), key=lambda item: SEGMENT_ORDER.get(item[0][1], 99)):
            if key[0] != case_id:
                continue
            segment = key[1]
            loss = loss_by_segment.get(segment, 0.0)
            rows.append(
                segment_output_row(
                    base=base,
                    path_id=path_id,
                    path_family="patch_boundary_fixed_mdot",
                    model_source=source_by_segment.get(segment, 0.0),
                    model_cooler_loss=loss if segment == "cooling_branch" else 0.0,
                    model_external_loss=0.0 if segment == "cooling_branch" else loss,
                    evidence_class=evidence_class,
                    admissibility_status="diagnostic_only_not_predictive",
                    source_paths=source_join(PARITY_RESULTS, SECTION_HEAT_BALANCE, PARITY_DECISIONS),
                    heater_power=heater_power.get(case_id, 0.0),
                    notes=notes,
                )
            )
    return rows


def no_radiation_segment_rows(heater_power: dict[str, float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(NO_RAD_SECTION):
        case_id = row["case_id"]
        base = {
            "case_id": case_id,
            "source_id": row["source_id"],
            "one_d_segment": row["one_d_segment"],
            "fluid_parent_segment": "",
            "cfd_imposed_source_W": fnum(row["cfd_imposed_source_W"]),
            "cfd_imposed_loss_W": fnum(row["cfd_imposed_loss_W"]),
            "cfd_imposed_net_to_fluid_W": fnum(row["cfd_imposed_net_to_fluid_W"]),
            "cfd_realized_source_W": fnum(row["cfd_realized_source_W"]),
            "cfd_realized_loss_W": fnum(row["cfd_realized_loss_W"]),
            "cfd_realized_net_to_fluid_W": fnum(row["cfd_realized_net_to_fluid_W"]),
        }
        rows.append(
            segment_output_row(
                base=base,
                path_id=row["path_id"],
                path_family="radiation_off_sensitivity",
                model_source=fnum(row["model_source_W"]),
                model_cooler_loss=fnum(row["model_cooler_loss_W"]),
                model_external_loss=fnum(row["model_external_loss_W"]),
                evidence_class="radiation_off_sensitivity_not_cfd_parity",
                admissibility_status="diagnostic_sensitivity_only",
                source_paths=source_join(NO_RAD_SECTION, NO_RAD_CONTRACT),
                heater_power=heater_power.get(case_id, 0.0),
                notes="Radiation is forced off in this 1D sensitivity; after AGENT-277/287 it is not Ethan-CFD parity.",
            )
        )
    return rows


def build_assumption_matrix(heater_power: dict[str, float]) -> list[dict[str, Any]]:
    runtime = {row["case_id"]: row for row in read_csv(RUNTIME_INPUTS)}
    heater = {row["case_id"]: row for row in read_csv(HEATER_LEDGER)}
    rows: list[dict[str, Any]] = []
    for case_id in sorted(heater_power):
        r = runtime[case_id]
        h = heater[case_id]
        rows.extend(
            [
                {
                    "case_id": case_id,
                    "assumption_id": "fixed_mdot_policy",
                    "ethan_3d_assumption": "CFD mdot is an observed diagnostic target.",
                    "one_d_assumption": "Fixed-mdot replay holds mdot at CFD value only for diagnostic parity.",
                    "match_status": "matched_for_diagnostic_replay_not_predictive",
                    "evidence_class": "diagnostic_parity",
                    "source_paths": source_join(PARITY_RESULTS, RUNTIME_INPUTS),
                    "notes": "Forward predictive modes must not use CFD mdot at runtime.",
                },
                {
                    "case_id": case_id,
                    "assumption_id": "heater_setup_location_and_power",
                    "ethan_3d_assumption": f"heater setup power {r['heater_power_W']} W on heater/lower-leg patches.",
                    "one_d_assumption": f"heater source applied to heated_incline/lower_leg with {r['heater_power_W']} W in setup replay.",
                    "match_status": "matched_setup_location_and_power",
                    "evidence_class": "setup_input",
                    "source_paths": source_join(RUNTIME_INPUTS, SECTION_HEAT_BALANCE),
                    "notes": f"Realized heater wallHeatFlux efficiency is diagnostic ({h['heater_realized_efficiency_diagnostic']}).",
                },
                {
                    "case_id": case_id,
                    "assumption_id": "test_section_source_policy",
                    "ethan_3d_assumption": f"test-section setup source {r['test_section_power_W']} W exists, but realized CFD wallHeatFlux can be net sink.",
                    "one_d_assumption": "Current source variants include full test-section source and heater-only sensitivity.",
                    "match_status": "variant_dependent_diagnostic",
                    "evidence_class": "source_contract_candidate",
                    "source_paths": source_join(RUNTIME_INPUTS, HEATER_LEDGER),
                    "notes": "Do not tune passive external loss to hide test-section source-contract error.",
                },
                {
                    "case_id": case_id,
                    "assumption_id": "cooler_removal_location_and_duty",
                    "ethan_3d_assumption": f"cooler imposed removal {r['imposed_cooler_duty_W']} W on cooling-branch cooler patches.",
                    "one_d_assumption": "Fixed-mdot diagnostic replay can impose the same cooler duty on cooled_incline_hx_active.",
                    "match_status": "matched_for_imposed_cooler_replay",
                    "evidence_class": "setup_input_diagnostic_replay",
                    "source_paths": source_join(RUNTIME_INPUTS, SECTION_HEAT_BALANCE),
                    "notes": "Predictive HX must replace imposed cooler duty with UA/epsilon-NTU or equivalent setup-only model.",
                },
                {
                    "case_id": case_id,
                    "assumption_id": "passive_wall_external_boundary",
                    "ethan_3d_assumption": "rcExternalTemperature patches carry h, Ta, Tsur, emissivity, and layer metadata.",
                    "one_d_assumption": "Current repo-local Fluid API accepts fixed sources/losses, not patch-level external boundary dictionaries.",
                    "match_status": "blocked_external_bc_api",
                    "evidence_class": "model_form_blocker",
                    "source_paths": source_join(SECTION_HEAT_BALANCE, PARITY_DECISIONS),
                    "notes": "This is the main place where same-assumption setup parity is contract-only rather than executable.",
                },
                {
                    "case_id": case_id,
                    "assumption_id": "radiation_handling",
                    "ethan_3d_assumption": "rcExternalTemperature includes emissivity/Tsur effects in total wallHeatFlux; no separate qr ledger is available.",
                    "one_d_assumption": "Do not add a separate radiation term on top of realized CFD wallHeatFlux replay.",
                    "match_status": "matched_no_double_count_for_realized_wallflux_replay",
                    "evidence_class": "radiation_inseparable",
                    "source_paths": source_join(PARITY_DECISIONS, BOUNDARY_DECISION),
                    "notes": "Radiation-off rows remain sensitivity-only and must not be called Ethan-CFD parity.",
                },
                {
                    "case_id": case_id,
                    "assumption_id": "wallheatflux_runtime_use",
                    "ethan_3d_assumption": "Realized wallHeatFlux is diagnostic heat accounting evidence.",
                    "one_d_assumption": "Realized wallHeatFlux may be prescribed only in diagnostic fixed-Q replay.",
                    "match_status": "diagnostic_only",
                    "evidence_class": "not_admissible_predictive_runtime",
                    "source_paths": source_join(HEATER_LEDGER, PARITY_RESULTS),
                    "notes": "Using realized wallHeatFlux in forward prediction would leak validation target information.",
                },
            ]
        )
    return rows


def build_role_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(PATCH_ROLE_SUMMARY):
        if row.get("role") == "zero_gradient_ncc_connector":
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "path_id": "cfd_role_summary",
                "role_or_lane": row["role"],
                "role_group": row["role_group"],
                "model_W": "",
                "cfd_imposed_W": fnum(row["imposed_Q_W"]),
                "cfd_realized_W": fnum(row["realized_wallHeatFlux_W"]),
                "model_minus_cfd_realized_W": "",
                "evidence_class": "cfd_heat_path_accounting",
                "source_paths": source_join(PATCH_ROLE_SUMMARY),
                "interpretation": "CFD role-level imposed and realized heat accounting; positive heats fluid, negative removes heat.",
            }
        )
    for row in read_csv(NO_RAD_DISCREPANCY):
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": "",
                "path_id": row["path_id"],
                "role_or_lane": row["lane"],
                "role_group": "one_d_radiation_off_sensitivity_lane",
                "model_W": fnum(row["model_W"]),
                "cfd_imposed_W": fnum(row["cfd_imposed_W"]),
                "cfd_realized_W": fnum(row["cfd_realized_W"]),
                "model_minus_cfd_realized_W": fnum(row["model_minus_cfd_realized_W"]),
                "evidence_class": "radiation_off_sensitivity_not_cfd_parity",
                "source_paths": source_join(NO_RAD_DISCREPANCY),
                "interpretation": row["interpretation"],
            }
        )
    return sorted(rows, key=lambda item: (item["case_id"], item["path_id"], item["role_or_lane"]))


def build_case_summary(segment_rows: list[dict[str, Any]], heater_power: dict[str, float]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in segment_rows:
        grouped[(row["case_id"], row["path_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for (case_id, path_id), items in sorted(grouped.items()):
        model_net = sum(fnum(row["model_net_to_fluid_W"]) for row in items)
        imposed_net = sum(fnum(row["cfd_imposed_net_to_fluid_W"]) for row in items)
        realized_net = sum(fnum(row["cfd_realized_net_to_fluid_W"]) for row in items)
        realized_residual = model_net - realized_net
        imposed_residual = model_net - imposed_net
        largest = max(items, key=lambda row: abs(fnum(row["model_minus_cfd_realized_net_W"])))
        match_count = sum(1 for row in items if row["sign_match_vs_realized"] == "match")
        path_family = items[0]["path_family"]
        if path_family == "radiation_off_sensitivity":
            study_status = "diagnostic_sensitivity_only_not_cfd_parity"
        elif path_id == "B2_realized_wallflux_roles":
            study_status = "diagnostic_realized_wallflux_replay"
        else:
            study_status = "diagnostic_setup_parity_replay"
        rows.append(
            {
                "case_id": case_id,
                "source_id": items[0]["source_id"],
                "path_id": path_id,
                "path_family": path_family,
                "heater_power_W": heater_power.get(case_id, ""),
                "model_net_to_fluid_W": model_net,
                "cfd_imposed_net_to_fluid_W": imposed_net,
                "cfd_realized_net_to_fluid_W": realized_net,
                "model_minus_cfd_realized_net_W": realized_residual,
                "model_minus_cfd_imposed_net_W": imposed_residual,
                "abs_realized_residual_fraction_of_heater": (
                    abs(realized_residual) / heater_power[case_id] if heater_power.get(case_id) else ""
                ),
                "largest_segment_residual": (
                    f"{largest['one_d_segment']}:{largest['model_minus_cfd_realized_net_W']}"
                ),
                "segments_with_sign_match_vs_realized": match_count,
                "segments_total": len(items),
                "study_status": study_status,
                "thesis_use_status": "use_for_heat_path_diagnosis_not_predictive_claim",
                "notes": "Compare section residuals before interpreting aggregate temperature error.",
            }
        )
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_source_manifest() -> list[dict[str, Any]]:
    roles = {
        PATCHWISE_ENTHALPY: "CFD patch wallHeatFlux and physical-interface enthalpy context",
        PATCH_ROLE_SUMMARY: "CFD role-level heat accounting",
        SECTION_HEAT_BALANCE: "CFD segment-level imposed and realized heat accounting",
        PARITY_RESULTS: "Fixed-mdot B2/B3 1D replay maps",
        PARITY_DECISIONS: "Radiation and external-boundary parity guardrails",
        NO_RAD_SECTION: "Radiation-off section sensitivity rows",
        NO_RAD_DISCREPANCY: "Radiation-off role/lane discrepancy rows",
        NO_RAD_CONTRACT: "Radiation-off boundary-contract sensitivity context",
        RUNTIME_INPUTS: "Setup input contract and heater/cooler values",
        HEATER_LEDGER: "Heater/test-section realized diagnostic context",
        BOUNDARY_DECISION: "Boundary/HX/wall/radiation decision prose",
    }
    rows: list[dict[str, Any]] = []
    for path in SOURCE_PATHS:
        row_count = ""
        if path.suffix == ".csv":
            row_count = len(read_csv(path))
        rows.append(
            {
                "source_path": rel(path),
                "exists": path.exists(),
                "row_count": row_count,
                "sha256": sha256(path) if path.exists() else "",
                "role": roles[path],
                "notes": "Read-only input; native CFD solver outputs were not modified.",
            }
        )
    return rows


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(SECTION_HEAT_BALANCE)}
  - {rel(PARITY_RESULTS)}
  - {rel(NO_RAD_SECTION)}
  - {rel(RUNTIME_INPUTS)}
tags: [thermal-parity, heat-loss, cfd-to-1d, thesis-source, methodology]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/README.md
task: {TASK_ID}
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# 3D vs 1D Heat-Loss Alignment

## Decision

This package starts the requested heat-loss study. It compares where Ethan's
3D CFD model adds/removes heat against where current fixed-mdot 1D replay modes
add/remove heat for Salt2-4 mainline rows.

The result is **diagnostic parity evidence**, not a predictive closure. The
study uses CFD mdot and realized `wallHeatFlux` only to locate heat-path
mismatches. Those quantities remain forbidden runtime inputs for setup-only
forward prediction.

## Headline

- Cases: `{summary["case_count"]}`
- Segment alignment rows: `{summary["segment_alignment_rows"]}`
- Role/lane rows: `{summary["role_alignment_rows"]}`
- Assumption rows: `{summary["assumption_rows"]}`
- Publication-ready predictive heat-loss rows: `0`

The package confirms the study has started and gives thesis-ready tables for
same-assumption heat-path bookkeeping. It also keeps the key caveat explicit:
`rcExternalTemperature` radiation is embedded in total CFD `wallHeatFlux`, so
there is no separate radiation heat term to add during realized-wallFlux replay.

## Files

- `assumption_match_matrix.csv`
- `heat_loss_alignment_by_segment.csv`
- `heat_loss_alignment_by_role.csv`
- `case_heat_loss_summary.csv`
- `source_manifest.csv`
- `methodology_and_assumptions.md`
- `thesis_presentation_notes.md`
- `summary.json`
"""
    (out / "README.md").write_text(readme, encoding="utf-8")


def write_methodology(out: Path) -> None:
    text = f"""# Methodology and Assumptions

## Objective

Track where heat enters and leaves the loop in Ethan's 3D CFD evidence and in
the current 1D fixed-mdot replay evidence, starting from the same setup
assumptions: same heater input places, same cooler removal place, and explicit
handling of passive wall/junction/radiation paths.

## Sign convention

All heat terms use the OpenFOAM/ledger convention used by the source packages:
positive heat enters the fluid and negative heat leaves the fluid. The output
tables split signed heat into source magnitude, loss magnitude, and net heat to
fluid so the sign cannot be hidden.

## Evidence lanes

`B3_imposed_setup_roles` is the closest current same-setup fixed-Q replay: it
maps imposed heater/test-section/cooler setup terms onto 1D segments.

`B2_realized_wallflux_roles` prescribes realized CFD wall flux by segment. It is
useful for locating where CFD actually transfers heat, but it is not a
predictive runtime model.

`N0`-`N3` radiation-off rows are retained as sensitivities only. They are useful
for role/lane diagnosis, but AGENT-277/287 showed that Ethan CFD
`rcExternalTemperature` includes emissivity/Tsur effects inside total
`wallHeatFlux`.

## Rigor gates

- Do not mutate native CFD outputs.
- Do not run heavy OpenFOAM from this package.
- Do not call radiation-off rows Ethan-CFD parity.
- Do not add separate 1D radiation on top of realized CFD `wallHeatFlux`.
- Do not use CFD mdot, realized CFD `wallHeatFlux`, or validation temperatures
  as setup-only forward-model runtime inputs.
- Report source paths for every table row.
- Report model-form/API blockers instead of fitting around them.

## Thesis use

This package supports a thesis/presentation section on heat-path attribution:
what the 3D model was asked to do, what heat it actually transferred at walls,
what the 1D replay can currently express, and which residuals belong to
heater, cooler/HX, passive wall, junction/storage, radiation metadata, or API
limitations.
"""
    (out / "methodology_and_assumptions.md").write_text(text, encoding="utf-8")


def write_thesis_notes(out: Path, case_rows: list[dict[str, Any]]) -> None:
    b3 = [row for row in case_rows if row["path_id"] == "B3_imposed_setup_roles"]
    worst = max(b3, key=lambda row: fnum(row["abs_realized_residual_fraction_of_heater"])) if b3 else None
    worst_text = (
        f"The largest setup-vs-realized case residual in B3 is {worst['case_id']} "
        f"at {float(worst['abs_realized_residual_fraction_of_heater']):.3f} of heater power."
        if worst
        else "No B3 rows were available."
    )
    text = f"""# Thesis and Presentation Notes

## Suggested slide claim

The 3D and 1D models can now be compared by heat path rather than only by mean
temperature error. The same-assumption ledger shows which sections receive
heater/test-section input, which section removes cooler duty, and where passive
wall/junction losses and realized wall-flux residuals sit.

## Caveated result wording

Use: "A fixed-mdot diagnostic alignment was built for Salt2-4. It separates
imposed setup heat, realized CFD wall heat, and current 1D replay heat by
section. It identifies heat-path mismatches without promoting CFD wallHeatFlux
or CFD mdot to predictive runtime inputs."

Avoid: "The 1D thermal model is validated" or "radiation-off replay matches
Ethan CFD."

## Current key observation

{worst_text}

The package should be read by segment first, then by case total. Case totals can
hide wrong-location heat transfer.

## Figures to make later

- Stacked signed heat bars by case and segment: CFD imposed, CFD realized, B3
  setup replay, and B2 realized-wallFlux replay.
- Role/lane bars: heater, test section, cooler, passive wall, junction.
- One residual waterfall per Salt case normalized by heater power.
"""
    (out / "thesis_presentation_notes.md").write_text(text, encoding="utf-8")


def build_package(out: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    heater_power = heater_power_by_case()
    base = base_segment_rows()
    segment_rows = fixed_q_segment_rows(base, heater_power) + no_radiation_segment_rows(heater_power)
    segment_rows = sorted(
        segment_rows,
        key=lambda row: (
            row["case_id"],
            row["path_family"],
            row["path_id"],
            SEGMENT_ORDER.get(row["one_d_segment"], 99),
        ),
    )
    assumption_rows = build_assumption_matrix(heater_power)
    role_rows = build_role_rows()
    case_rows = build_case_summary(segment_rows, heater_power)
    source_rows = build_source_manifest()

    write_csv(out / "assumption_match_matrix.csv", assumption_rows, ASSUMPTION_COLUMNS)
    write_csv(out / "heat_loss_alignment_by_segment.csv", segment_rows, SEGMENT_COLUMNS)
    write_csv(out / "heat_loss_alignment_by_role.csv", role_rows, ROLE_COLUMNS)
    write_csv(out / "case_heat_loss_summary.csv", case_rows, CASE_COLUMNS)
    write_csv(
        out / "source_manifest.csv",
        source_rows,
        ["source_path", "exists", "row_count", "sha256", "role", "notes"],
    )

    summary = {
        "task": TASK_ID,
        "generated_utc": utc_now(),
        "host": socket.gethostname(),
        "case_count": len(heater_power),
        "cases": sorted(heater_power),
        "segment_alignment_rows": len(segment_rows),
        "role_alignment_rows": len(role_rows),
        "case_summary_rows": len(case_rows),
        "assumption_rows": len(assumption_rows),
        "source_manifest_rows": len(source_rows),
        "study_mode": "fixed_mdot_diagnostic_heat_path_alignment",
        "predictive_rows_admitted": 0,
        "native_solver_outputs_mutated": False,
        "heavy_openfoam_run": False,
        "radiation_policy": "rcExternalTemperature_radiation_inseparable_in_total_wallHeatFlux_no_separate_qr",
        "runtime_guardrail": "CFD_mdot_and_realized_wallHeatFlux_are_diagnostic_not_predictive_runtime_inputs",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(out, summary)
    write_methodology(out)
    write_thesis_notes(out, case_rows)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_package(args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
