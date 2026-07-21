#!/usr/bin/env python3
"""Build Salt2 +/-5Q and val_salt2 fluid+walls readiness ledgers.

This builder intentionally consumes existing postprocessed evidence only. It
does not launch OpenFOAM, submit scheduler jobs, mutate native CFD outputs, or
change scientific admission state.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-484"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger")
OUT = ROOT / OUT_REL

ALLOWED_STATUSES = {"admitted", "diagnostic", "partial", "missing"}
STATUS_FIELDS = [
    "geometry_status",
    "material_stack_status",
    "pressure_model_status",
    "thermal_circuit_status",
    "source_sink_role_status",
    "boundary_layer_state_status",
    "recirculation_flags_status",
    "uncertainty_status",
]

CASES = ["salt2_lo5q", "salt2_hi5q", "val_salt2"]
SALT2_PM5_CASES = {"salt2_lo5q", "salt2_hi5q"}

INPUTS = {
    "canonical_split_policy": Path(
        "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/"
        "canonical_final_predictive_split_policy.csv"
    ),
    "fluid_walls_model_form": Path("operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md"),
    "geometry_reference": Path("reference/geometry_reference.md"),
    "salt2_pm5_metrics": Path(
        "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/"
        "resampled_pm5_matched_plane_metrics.csv"
    ),
    "salt2_pm5_scorecard": Path(
        "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/"
        "pm5_f6_internal_nu_unlock_scorecard.csv"
    ),
    "salt2_heat_role_reduction": Path(
        "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/"
        "corrected_q_pm5_heat_role_reduction.csv"
    ),
    "pressure_branch_admission": Path(
        "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/"
        "branch_orientation_straight_loss_recirc_admission.csv"
    ),
    "pressure_branch_map": Path(
        "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/"
        "all_branch_average_pressure_map.csv"
    ),
    "val_section_heat_ledger": Path(
        "work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/"
        "val_salt2_section_heat_loss_ledger.csv"
    ),
    "val_patch_heat_ledger": Path(
        "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/"
        "val_salt2_patch_heat_ledger.csv"
    ),
    "val_junction_split_ledger": Path(
        "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/"
        "val_salt2_junction_split_heat_ledger.csv"
    ),
    "val_training_gate": Path(
        "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/"
        "val_salt2_training_admission_gate.csv"
    ),
}

SEGMENTS = [
    {
        "segment_or_branch": "lower_leg",
        "one_d_segment": "heated_incline",
        "row_type": "heater_lower_leg",
        "model_role": "heater/source lower leg",
        "material_basis": "steel/insulated lower leg role is known but needs one final wall-stack runtime contract",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "boundary_layer_state_status": "diagnostic",
    },
    {
        "segment_or_branch": "left_lower_leg",
        "one_d_segment": "left_lower_vertical",
        "row_type": "upcomer_inlet",
        "model_role": "lower upcomer before test section",
        "material_basis": "upcomer wall stack exists in prior geometry/BC evidence but is not finalized here",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "boundary_layer_state_status": "diagnostic",
    },
    {
        "segment_or_branch": "test_section_span",
        "one_d_segment": "test_section",
        "row_type": "test_section",
        "model_role": "bare-quartz electrically heated upcomer span",
        "material_basis": "bare-quartz test-section material and geometry are explicitly identified in the model-form note",
        "geometry_status": "admitted",
        "material_stack_status": "admitted",
        "boundary_layer_state_status": "diagnostic",
    },
    {
        "segment_or_branch": "left_upper_leg",
        "one_d_segment": "left_upper_vertical",
        "row_type": "upcomer_outlet",
        "model_role": "upper upcomer after test section",
        "material_basis": "upcomer wall stack exists in prior geometry/BC evidence but is not finalized here",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "boundary_layer_state_status": "diagnostic",
    },
    {
        "segment_or_branch": "upper_leg",
        "one_d_segment": "upper_horizontal_cooler",
        "row_type": "cooler_hx_upper_branch",
        "model_role": "cooler/HX and upper transport sink region",
        "material_basis": "cooler/HX role is known; segment-local wall/HX material stack remains partial",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "boundary_layer_state_status": "diagnostic",
    },
    {
        "segment_or_branch": "right_leg",
        "one_d_segment": "right_vertical",
        "row_type": "downcomer",
        "model_role": "right-leg downcomer/passive wall loss",
        "material_basis": "downcomer wall stack exists in geometry/BC evidence but is not finalized here",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "boundary_layer_state_status": "diagnostic",
    },
    {
        "segment_or_branch": "junctions",
        "one_d_segment": "junction_stub_connector_group",
        "row_type": "junction_stub_connector_group",
        "model_role": "junction, stub, step, and connector losses",
        "material_basis": "junction/stub local geometry and material ownership remain incomplete",
        "geometry_status": "partial",
        "material_stack_status": "partial",
        "boundary_layer_state_status": "missing",
    },
]

SECTION_BY_SEGMENT = {
    "lower_leg": "heater",
    "left_lower_leg": "upcomer",
    "test_section_span": "test_section",
    "left_upper_leg": "upcomer",
    "upper_leg": "cooling_branch",
    "right_leg": "downcomer",
    "junctions": "junctions",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def rel(path: Path | str) -> str:
    resolved = resolve(path)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def read_csv(path: Path | str) -> list[dict[str, str]]:
    with resolve(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def semi_join(parts: list[str]) -> str:
    return ";".join(part for part in parts if part)


def input_path(name: str) -> str:
    return rel(INPUTS[name])


def load_inputs() -> dict[str, Any]:
    missing = [rel(path) for path in INPUTS.values() if not resolve(path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required input files: {missing}")

    split_rows = {row["case_key"]: row for row in read_csv(INPUTS["canonical_split_policy"])}
    pm5_rows = [row for row in read_csv(INPUTS["salt2_pm5_metrics"]) if row["case_key"] in SALT2_PM5_CASES]
    heat_rows = [row for row in read_csv(INPUTS["salt2_heat_role_reduction"]) if row["case_key"] in SALT2_PM5_CASES]
    pressure_rows = [row for row in read_csv(INPUTS["pressure_branch_admission"]) if row["case_key"] in CASES]
    pressure_map_rows = [row for row in read_csv(INPUTS["pressure_branch_map"]) if row["case_key"] in CASES]
    val_section_rows = read_csv(INPUTS["val_section_heat_ledger"])
    val_patch_rows = read_csv(INPUTS["val_patch_heat_ledger"])
    val_junction_rows = read_csv(INPUTS["val_junction_split_ledger"])
    val_gate_rows = read_csv(INPUTS["val_training_gate"])
    pm5_scorecard_rows = read_csv(INPUTS["salt2_pm5_scorecard"])

    return {
        "split_rows": split_rows,
        "pm5_rows": pm5_rows,
        "heat_rows": heat_rows,
        "pressure_rows": pressure_rows,
        "pressure_map_rows": pressure_map_rows,
        "val_section_rows": val_section_rows,
        "val_patch_rows": val_patch_rows,
        "val_junction_rows": val_junction_rows,
        "val_gate_rows": val_gate_rows,
        "pm5_scorecard_rows": pm5_scorecard_rows,
    }


def case_inventory(data: dict[str, Any]) -> list[dict[str, Any]]:
    heat_by_case = {row["case_key"]: row for row in data["heat_rows"]}
    pm5_times: dict[str, set[str]] = defaultdict(set)
    for row in data["pm5_rows"]:
        pm5_times[row["case_key"]].add(row["representative_time_s"])
    pressure_by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in data["pressure_rows"]:
        pressure_by_case[row["case_key"]].append(row)

    val_latest_time = ""
    val_window = ""
    if data["val_section_rows"]:
        val_latest_time = data["val_section_rows"][0].get("latest_time_s", "")
        start = "8302"
        end = data["val_section_rows"][0].get("latest_time_s", "8602")
        val_window = f"{start}-{end}"

    rows: list[dict[str, Any]] = []
    for case_key in CASES:
        split = data["split_rows"].get(case_key, {})
        heat = heat_by_case.get(case_key, {})
        pressure = pressure_by_case.get(case_key, [])
        if case_key in SALT2_PM5_CASES:
            representative_time_s = sorted(pm5_times.get(case_key, []))[0] if pm5_times.get(case_key) else ""
            terminal_window_s = f"{heat.get('final_window_start_s', '')}-{heat.get('final_window_end_s', '')}"
            source_key = heat.get("source_case_key", split.get("source_key", ""))
            evidence = "Salt2 +/-5Q PM5 repaired; pressure and heat ledgers available; holdout/testing only."
            current_status = "holdout_pm5_pressure_heat_evidence_available_fit_forbidden"
        else:
            representative_time_s = val_latest_time
            terminal_window_s = val_window
            source_key = split.get("source_key", "val_salt_test_2_coarse_mesh_laminar")
            evidence = "val_salt2 heat and pressure ledgers available; PM5/upcomer matched-plane extraction not in current evidence set."
            current_status = "external_test_heat_pressure_ledger_available_pm5_missing"
        rows.append(
            {
                "case_key": case_key,
                "source_key": source_key,
                "split_role": split.get("split_role", pressure[0].get("split_role", "") if pressure else ""),
                "fit_allowed": split.get("fit_allowed", "no"),
                "model_selection_allowed": split.get("model_selection_allowed", "no"),
                "score_allowed": split.get("score_allowed", "yes"),
                "split_policy_use_status": split.get("use_status", ""),
                "current_postprocessing_status": current_status,
                "legal_use": legal_use(case_key),
                "representative_time_s": representative_time_s,
                "terminal_window_s": terminal_window_s,
                "pressure_branch_rows": len(pressure),
                "pm5_rows": sum(1 for row in data["pm5_rows"] if row["case_key"] == case_key),
                "thermal_rows": thermal_row_count(case_key, data),
                "evidence_summary": evidence,
                "primary_source_paths": sources_for_case(case_key),
            }
        )
    return rows


def legal_use(case_key: str) -> str:
    if case_key in SALT2_PM5_CASES:
        return "holdout_testing_only_no_fit_no_tune"
    return "external_test_only_no_fit_no_tune"


def thermal_row_count(case_key: str, data: dict[str, Any]) -> int:
    if case_key in SALT2_PM5_CASES:
        return sum(1 for row in data["heat_rows"] if row["case_key"] == case_key)
    return len(data["val_section_rows"]) + len(data["val_patch_rows"]) + len(data["val_junction_rows"])


def sources_for_case(case_key: str) -> str:
    parts = ["canonical_split_policy", "pressure_branch_admission", "pressure_branch_map", "fluid_walls_model_form"]
    if case_key in SALT2_PM5_CASES:
        parts += ["salt2_pm5_metrics", "salt2_pm5_scorecard", "salt2_heat_role_reduction"]
    else:
        parts += ["val_section_heat_ledger", "val_patch_heat_ledger", "val_junction_split_ledger", "val_training_gate"]
    return semi_join([input_path(part) for part in parts])


def pressure_by_case_branch(data: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_key"], row["branch"]): row for row in data["pressure_rows"]}


def pressure_map_by_case_branch(data: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_key"], row["cfd_span"]): row for row in data["pressure_map_rows"]}


def salt2_heat_by_case(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in data["heat_rows"]}


def val_section_by_key(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in data["val_section_rows"]:
        out[row["section_key"]] = row
    return out


def pm5_by_case_span(data: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, str]]]:
    out: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in data["pm5_rows"]:
        out[(row["case_key"], row["span"])].append(row)
    return out


def build_readiness_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    pressure_lookup = pressure_by_case_branch(data)
    pressure_map_lookup = pressure_map_by_case_branch(data)
    heat_lookup = salt2_heat_by_case(data)
    val_heat_lookup = val_section_by_key(data)
    pm5_lookup = pm5_by_case_span(data)
    split_rows = data["split_rows"]

    rows: list[dict[str, Any]] = []
    for case_key in CASES:
        split = split_rows.get(case_key, {})
        for segment in SEGMENTS:
            branch = segment["segment_or_branch"]
            section = SECTION_BY_SEGMENT[branch]
            pressure = pressure_lookup.get((case_key, branch), {})
            pressure_map = pressure_map_lookup.get((case_key, branch), {})
            pm5_rows = pm5_lookup.get((case_key, branch), [])
            heat_evidence = thermal_evidence(case_key, section, heat_lookup, val_heat_lookup)
            pm5_status, pm5_evidence, pm5_next = classify_pm5(case_key, branch, pm5_rows)
            source_sink_status, source_sink_evidence = classify_source_sink(case_key, section, heat_evidence)
            pressure_status, pressure_evidence = classify_pressure(pressure)
            recirc_status, recirc_evidence = classify_recirc(case_key, branch, pressure, pm5_rows)
            uncertainty_status, uncertainty_evidence = classify_uncertainty(case_key, pressure, heat_evidence, pm5_rows)
            thermal_status, thermal_evidence_summary = classify_thermal_circuit(case_key, section, heat_evidence, pm5_rows)

            admission_decision = "diagnostic_or_target_evidence_only"
            if case_key == "val_salt2" and source_sink_status != "missing":
                admission_decision = "external_test_target_ready_no_fit"
            if case_key in SALT2_PM5_CASES and pm5_rows:
                admission_decision = "holdout_diagnostic_ready_no_fit"

            rows.append(
                {
                    "case_key": case_key,
                    "split_role": split.get("split_role", pressure.get("split_role", "")),
                    "legal_use": legal_use(case_key),
                    "row_type": segment["row_type"],
                    "segment_or_branch": branch,
                    "one_d_segment": pressure_map.get("one_d_parent_segment", segment["one_d_segment"]),
                    "model_role": segment["model_role"],
                    "representative_time_s": representative_time(case_key, data),
                    "terminal_window_s": terminal_window(case_key, data),
                    "geometry_status": segment["geometry_status"],
                    "geometry_evidence": f"{branch} mapped to {segment['one_d_segment']}; reference geometry/model-form note is source of truth",
                    "material_stack_status": segment["material_stack_status"],
                    "material_stack_evidence": segment["material_basis"],
                    "pressure_model_status": pressure_status,
                    "pressure_model_evidence": pressure_evidence,
                    "thermal_circuit_status": thermal_status,
                    "thermal_circuit_evidence": thermal_evidence_summary,
                    "source_sink_role_status": source_sink_status,
                    "source_sink_role_evidence": source_sink_evidence,
                    "boundary_layer_state_status": segment["boundary_layer_state_status"],
                    "boundary_layer_state_evidence": boundary_layer_evidence(branch),
                    "recirculation_flags_status": recirc_status,
                    "recirculation_flags_evidence": recirc_evidence,
                    "uncertainty_status": uncertainty_status,
                    "uncertainty_evidence": uncertainty_evidence,
                    "pm5_internal_nu_gate_status": pm5_status,
                    "pm5_internal_nu_gate_evidence": pm5_evidence,
                    "admission_decision": admission_decision,
                    "do_not_use_for": do_not_use_for(case_key, pressure, pm5_rows),
                    "next_action": next_action(case_key, branch, pressure, pm5_next, source_sink_status),
                    "primary_source_paths": row_sources(case_key, branch, section, pressure, pm5_rows, heat_evidence),
                }
            )
    return rows


def representative_time(case_key: str, data: dict[str, Any]) -> str:
    if case_key in SALT2_PM5_CASES:
        times = sorted({row["representative_time_s"] for row in data["pm5_rows"] if row["case_key"] == case_key})
        return times[0] if times else ""
    if data["val_section_rows"]:
        return data["val_section_rows"][0].get("latest_time_s", "8602.0")
    return "8602.0"


def terminal_window(case_key: str, data: dict[str, Any]) -> str:
    if case_key in SALT2_PM5_CASES:
        heat = salt2_heat_by_case(data).get(case_key, {})
        return f"{heat.get('final_window_start_s', '')}-{heat.get('final_window_end_s', '')}"
    return "8302-8602"


def thermal_evidence(
    case_key: str,
    section: str,
    salt2_heat_lookup: dict[str, dict[str, str]],
    val_heat_lookup: dict[str, dict[str, str]],
) -> dict[str, Any]:
    if case_key in SALT2_PM5_CASES:
        heat = salt2_heat_lookup.get(case_key, {})
        column = f"section_{section}_net_q_mean_W"
        if section == "cooling_branch":
            column = "section_cooling_branch_net_q_mean_W"
        if column in heat:
            return {
                "available": True,
                "q_net_w": heat.get(column, ""),
                "role": section,
                "source_path": heat.get("source_wall_heat_flux_grouped_csv", input_path("salt2_heat_role_reduction")),
                "runtime_guardrail": heat.get("runtime_use_guardrail", ""),
                "radiation_semantics": heat.get("radiation_semantics", ""),
            }
        return {"available": False}
    heat = val_heat_lookup.get(section, {})
    if heat:
        return {
            "available": True,
            "q_net_w": heat.get("latest_cfd_realized_net_to_fluid_W", ""),
            "role": heat.get("thermal_role", section),
            "source_path": heat.get("source_path", input_path("val_section_heat_ledger")),
            "runtime_guardrail": "external-test target only; not a predictive runtime input",
            "radiation_semantics": "rcExternalTemperature radiation embedded in wallHeatFlux where applicable",
        }
    return {"available": False}


def classify_pm5(case_key: str, branch: str, rows: list[dict[str, str]]) -> tuple[str, str, str]:
    if case_key == "val_salt2":
        return (
            "missing",
            "No val_salt2 PM5/upcomer matched-plane evidence is present in the current source set.",
            "Queue val_salt2 PM5/upcomer extraction only if final external scoring needs matched-plane recirculation fields.",
        )
    if branch in {"left_lower_leg", "test_section_span", "left_upper_leg"} and rows:
        max_raf = max(fnum(row.get("reverse_area_fraction")) for row in rows)
        max_rmf = max(fnum(row.get("reverse_mass_fraction")) for row in rows)
        return (
            "diagnostic",
            f"AGENT-406 repaired PM5 fields; {len(rows)} row(s), max RAF={max_raf:.3g}, max RMF={max_rmf:.3g}; not admitted for fitting.",
            "Run bounded F6/internal-Nu review only as diagnostic holdout evidence; keep fit forbidden.",
        )
    if branch in {"left_lower_leg", "test_section_span", "left_upper_leg"}:
        return (
            "missing",
            "Expected Salt2 PM5 upcomer row is not present in repaired PM5 metrics.",
            "Repair or rerun PM5 extraction on staged copies before any upcomer diagnostic claim.",
        )
    return (
        "missing",
        "PM5 matched-plane metrics are scoped to upcomer inlet/mid/outlet, not this segment.",
        "No PM5 action required unless a future segment-local extraction is requested.",
    )


def classify_source_sink(case_key: str, section: str, heat: dict[str, Any]) -> tuple[str, str]:
    if not heat.get("available"):
        return "missing", "No section heat/source/sink row found in current evidence."
    q = fnum(heat.get("q_net_w"))
    if case_key == "val_salt2":
        return (
            "diagnostic",
            f"val_salt2 section heat target exists for {section}: q_net={q:.6g} W; external-test target only.",
        )
    return (
        "diagnostic",
        f"Salt2 +/-5Q section heat target exists for {section}: q_net={q:.6g} W; holdout/scoring target only.",
    )


def classify_pressure(pressure: dict[str, str]) -> tuple[str, str]:
    if not pressure:
        return "missing", "No pressure branch-admission row found."
    admitted = pressure.get("true_f_D_or_K_fit_admitted", "no")
    blockers = pressure.get("blockers", "")
    if admitted == "yes":
        return "admitted", "Pressure branch row is marked true f_D/K fit admitted."
    return (
        "diagnostic",
        f"{pressure.get('admission_status', 'not_admitted')}; blockers={blockers}; no duplicate pressure ladder job needed.",
    )


def classify_recirc(
    case_key: str,
    branch: str,
    pressure: dict[str, str],
    pm5_rows: list[dict[str, str]],
) -> tuple[str, str]:
    evidence: list[str] = []
    if pressure:
        evidence.append(
            f"pressure recirc={pressure.get('recirculation_mask_status', '')}, max_pair_RAF={pressure.get('max_pair_reverse_area_fraction_proxy', '')}"
        )
    if pm5_rows:
        evidence.append(
            "PM5 "
            + ",".join(
                f"{row.get('plane_location')} RAF={fnum(row.get('reverse_area_fraction')):.3g} RMF={fnum(row.get('reverse_mass_fraction')):.3g}"
                for row in pm5_rows
            )
        )
    if case_key == "val_salt2" and branch in {"left_lower_leg", "test_section_span", "left_upper_leg"}:
        return (
            "partial",
            semi_join(evidence)
            + "; val_salt2 has pressure recirculation flags but lacks matching PM5 reverse-mass plane metrics.",
        )
    if evidence:
        return "diagnostic", semi_join(evidence)
    return "missing", "No recirculation evidence found."


def classify_uncertainty(
    case_key: str,
    pressure: dict[str, str],
    heat: dict[str, Any],
    pm5_rows: list[dict[str, str]],
) -> tuple[str, str]:
    notes: list[str] = []
    status = "partial"
    if pressure:
        notes.append("pressure rows are coarse-only/no mesh-GCI and diagnostic")
    else:
        notes.append("pressure uncertainty missing")
        status = "missing"
    if heat.get("available"):
        notes.append("terminal heat window exists but realized wallHeatFlux is scoring-only")
    else:
        notes.append("thermal/source uncertainty missing")
        status = "missing"
    if case_key in SALT2_PM5_CASES:
        if pm5_rows:
            notes.append("PM5 fields are repaired but F6/internal-Nu admission is not complete")
        else:
            notes.append("PM5 uncertainty missing for non-upcomer segment")
    else:
        notes.append("val_salt2 PM5 uncertainty missing/queued")
    return status, "; ".join(notes)


def classify_thermal_circuit(case_key: str, section: str, heat: dict[str, Any], pm5_rows: list[dict[str, str]]) -> tuple[str, str]:
    if not heat.get("available"):
        return "missing", "No thermal heat/source row found for this section."
    q = fnum(heat.get("q_net_w"))
    direction = "adds heat to fluid" if q > 0 else "removes heat from fluid" if q < 0 else "near zero net heat"
    base = (
        f"section role={section}, q_net={q:.6g} W ({direction}); "
        f"{heat.get('runtime_guardrail', 'realized wallHeatFlux is diagnostic only')}"
    )
    if section in {"upcomer", "test_section"} and pm5_rows:
        return "partial", base + "; PM5 wall/core fields exist but internal Nu/HTC remains gated."
    return "partial", base + "; final predictive wall/material resistance circuit is not admitted here."


def boundary_layer_evidence(branch: str) -> str:
    if branch in {"left_lower_leg", "test_section_span", "left_upper_leg"}:
        return "upcomer belongs to hybrid recirculation/onset lane; ordinary single-stream boundary-layer fitting is rejected."
    if branch == "junctions":
        return "junction/stub reset and local development state not yet parameterized."
    return "development/reset state is diagnostic/planned; not admitted as fitted segment coefficient."


def do_not_use_for(case_key: str, pressure: dict[str, str], pm5_rows: list[dict[str, str]]) -> str:
    forbidden = ["training_fit", "model_tuning"]
    if pressure and pressure.get("true_f_D_or_K_fit_admitted", "no") != "yes":
        forbidden.append("pressure_f_D_or_K_fit")
    if pm5_rows or case_key == "val_salt2":
        forbidden.append("ordinary_upcomer_single_stream_fit")
    return ";".join(forbidden)


def next_action(
    case_key: str,
    branch: str,
    pressure: dict[str, str],
    pm5_next: str,
    source_sink_status: str,
) -> str:
    if case_key == "val_salt2" and branch in {"left_lower_leg", "test_section_span", "left_upper_leg"}:
        return "Keep external-test heat/pressure evidence; queue PM5 extraction only if final external scoring needs matched-plane recirculation metrics."
    if case_key in SALT2_PM5_CASES and branch in {"left_lower_leg", "test_section_span", "left_upper_leg"}:
        return pm5_next
    if pressure and pressure.get("true_f_D_or_K_fit_admitted", "no") != "yes":
        return "Use pressure row diagnostically; admit pressure definition, recirculation, straight-loss, geometry, component isolation, and mesh/GCI before coefficients."
    if source_sink_status == "missing":
        return "Add section heat/source-sink evidence before model scoring."
    return "Keep as diagnostic/scoring evidence until final fluid+walls runtime circuit is admitted."


def row_sources(
    case_key: str,
    branch: str,
    section: str,
    pressure: dict[str, str],
    pm5_rows: list[dict[str, str]],
    heat: dict[str, Any],
) -> str:
    sources = [input_path("canonical_split_policy"), input_path("fluid_walls_model_form"), input_path("geometry_reference")]
    if pressure:
        sources += [input_path("pressure_branch_admission"), input_path("pressure_branch_map")]
    if case_key in SALT2_PM5_CASES:
        sources.append(input_path("salt2_heat_role_reduction"))
        if pm5_rows:
            sources += [input_path("salt2_pm5_metrics"), input_path("salt2_pm5_scorecard")]
    else:
        sources += [input_path("val_section_heat_ledger"), input_path("val_patch_heat_ledger"), input_path("val_junction_split_ledger"), input_path("val_training_gate")]
    if heat.get("source_path"):
        sources.append(str(heat["source_path"]))
    return semi_join(sources)


def build_pressure_ledger(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    map_lookup = pressure_map_by_case_branch(data)
    for row in data["pressure_rows"]:
        mapped = map_lookup.get((row["case_key"], row["branch"]), {})
        status, evidence = classify_pressure(row)
        rows.append(
            {
                "case_key": row["case_key"],
                "split_role": row.get("split_role", ""),
                "branch": row["branch"],
                "one_d_segment": mapped.get("one_d_parent_segment", ""),
                "pressure_model_status": status,
                "admission_status": row.get("admission_status", ""),
                "true_f_D_or_K_fit_admitted": row.get("true_f_D_or_K_fit_admitted", ""),
                "pressure_definition_status": row.get("pressure_definition_status", ""),
                "orientation_status": row.get("orientation_status", ""),
                "straight_loss_subtraction_status": row.get("straight_loss_subtraction_status", ""),
                "recirculation_mask_status": row.get("recirculation_mask_status", ""),
                "max_pair_reverse_area_fraction_proxy": row.get("max_pair_reverse_area_fraction_proxy", ""),
                "blockers": row.get("blockers", ""),
                "next_use": row.get("next_use", ""),
                "evidence_summary": evidence,
                "source_paths": semi_join([input_path("pressure_branch_admission"), input_path("pressure_branch_map"), row.get("source_paths", "")]),
            }
        )
    return rows


def build_pm5_ledger(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in data["pm5_rows"]:
        rows.append(
            {
                "case_key": row["case_key"],
                "split_role": "holdout_testing_only_no_fit_no_tune",
                "span": row["span"],
                "plane_location": row["plane_location"],
                "representative_time_s": row["representative_time_s"],
                "metric_status": row["metric_status"],
                "pm5_internal_nu_gate_status": "diagnostic",
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_velocity_fraction": row["secondary_velocity_fraction"],
                "Re": row["Re"],
                "Pr": row["Pr"],
                "Ri": row["Ri"],
                "Gr": row["Gr"],
                "Ra": row["Ra"],
                "Gz": row["Gz"],
                "wallHeatFlux_available": row["wallHeatFlux_available"],
                "admission_status": row["admission_status"],
                "do_not_use_for": "training_fit;model_tuning;ordinary_upcomer_single_stream_fit",
                "next_action": "Use for bounded F6/internal-Nu diagnostic review only; do not fit or tune on holdout rows.",
                "source_paths": semi_join([input_path("salt2_pm5_metrics"), input_path("salt2_pm5_scorecard"), row.get("source_paths", "")]),
            }
        )
    rows.append(
        {
            "case_key": "val_salt2",
            "split_role": "external_test_only_no_fit_no_tune",
            "span": "left_lower_leg;test_section_span;left_upper_leg",
            "plane_location": "upcomer_inlet;upcomer_mid;upcomer_outlet",
            "representative_time_s": "8602",
            "metric_status": "missing_in_current_evidence_set",
            "pm5_internal_nu_gate_status": "missing",
            "reverse_area_fraction": "",
            "reverse_mass_fraction": "",
            "secondary_velocity_fraction": "",
            "Re": "",
            "Pr": "",
            "Ri": "",
            "Gr": "",
            "Ra": "",
            "Gz": "",
            "wallHeatFlux_available": "not_extracted_as_pm5_wall_band",
            "admission_status": "queued_if_external_score_requires_upcomer_matched_plane_features",
            "do_not_use_for": "training_fit;model_tuning;ordinary_upcomer_single_stream_fit",
            "next_action": "Optional follow-on: run val_salt2 PM5/upcomer extraction on staged copies if final external scoring requires matched-plane recirculation metrics.",
            "source_paths": semi_join([input_path("val_section_heat_ledger"), input_path("val_training_gate")]),
        }
    )
    return rows


def build_thermal_ledger(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for heat in data["heat_rows"]:
        for section in ["heater", "test_section", "cooling_branch", "downcomer", "upcomer", "junctions"]:
            key = f"section_{section}_net_q_mean_W"
            if key not in heat:
                continue
            q = fnum(heat[key])
            rows.append(
                {
                    "case_key": heat["case_key"],
                    "section_key": section,
                    "source_sink_role_status": "diagnostic",
                    "terminal_window_s": f"{heat.get('final_window_start_s', '')}-{heat.get('final_window_end_s', '')}",
                    "q_net_to_fluid_W": q,
                    "source_component_W": max(q, 0.0),
                    "removal_component_W": max(-q, 0.0),
                    "sign_convention": "positive is net heat into fluid; negative is heat removed from fluid",
                    "runtime_use_guardrail": heat.get("runtime_use_guardrail", ""),
                    "radiation_semantics": heat.get("radiation_semantics", ""),
                    "source_paths": semi_join([input_path("salt2_heat_role_reduction"), heat.get("source_wall_heat_flux_grouped_csv", "")]),
                }
            )
    for heat in data["val_section_rows"]:
        q = fnum(heat.get("latest_cfd_realized_net_to_fluid_W"))
        rows.append(
            {
                "case_key": "val_salt2",
                "section_key": heat.get("section_key", ""),
                "source_sink_role_status": "diagnostic",
                "terminal_window_s": "8302-8602",
                "q_net_to_fluid_W": q,
                "source_component_W": max(q, 0.0),
                "removal_component_W": max(-q, 0.0),
                "sign_convention": heat.get("sign_convention", "positive is net heat into fluid; negative is heat removed from fluid"),
                "runtime_use_guardrail": "external-test target only; not a predictive runtime input",
                "radiation_semantics": "rcExternalTemperature radiation embedded in wallHeatFlux where applicable",
                "source_paths": semi_join([input_path("val_section_heat_ledger"), heat.get("source_path", "")]),
            }
        )
    return rows


def build_uncertainty_rows(readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in readiness_rows:
        blockers: list[str] = []
        if row["pressure_model_status"] != "admitted":
            blockers.append("pressure coefficient not admitted")
        if row["uncertainty_status"] != "admitted":
            blockers.append("mesh/GCI or matched-field uncertainty incomplete")
        if row["recirculation_flags_status"] in {"diagnostic", "partial"}:
            blockers.append("recirculation blocks ordinary single-stream coefficients")
        if row["thermal_circuit_status"] != "admitted":
            blockers.append("predictive wall/material thermal circuit not admitted")
        rows.append(
            {
                "case_key": row["case_key"],
                "segment_or_branch": row["segment_or_branch"],
                "uncertainty_status": row["uncertainty_status"],
                "uncertainty_evidence": row["uncertainty_evidence"],
                "primary_uncertainty_blockers": semi_join(blockers),
                "fit_or_score_implication": row["legal_use"],
                "source_paths": row["primary_source_paths"],
            }
        )
    return rows


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": resolve(path).exists(),
            "use": source_use(source_id),
        }
        for source_id, path in INPUTS.items()
    ]


def source_use(source_id: str) -> str:
    uses = {
        "canonical_split_policy": "Split/legal-use source of truth.",
        "fluid_walls_model_form": "Readiness dimensions and steady-state fluid+walls contract.",
        "geometry_reference": "Segment and geometry reference.",
        "salt2_pm5_metrics": "Salt2 +/-5Q repaired PM5/upcomer field metrics.",
        "salt2_pm5_scorecard": "PM5 field availability and F6/internal-Nu gate status.",
        "salt2_heat_role_reduction": "Salt2 +/-5Q section heat/source/sink evidence.",
        "pressure_branch_admission": "Pressure coefficient admission and blocker evidence.",
        "pressure_branch_map": "Branch-to-1D mapping and pressure map provenance.",
        "val_section_heat_ledger": "val_salt2 section heat/source/sink ledger.",
        "val_patch_heat_ledger": "val_salt2 patch-level wallHeatFlux ledger.",
        "val_junction_split_ledger": "val_salt2 junction/stub split heat ledger.",
        "val_training_gate": "val_salt2 external-test/training guardrail gates.",
    }
    return uses[source_id]


def validate_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        for field in STATUS_FIELDS:
            value = row[field]
            if value not in ALLOWED_STATUSES:
                raise ValueError(f"{row['case_key']} {row['segment_or_branch']} invalid {field}={value}")
        if not row["primary_source_paths"]:
            raise ValueError(f"{row['case_key']} {row['segment_or_branch']} missing source paths")
        if row["admission_decision"] != "admitted" and not row["next_action"]:
            raise ValueError(f"{row['case_key']} {row['segment_or_branch']} missing next action")


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {input_path('canonical_split_policy')}
  - {input_path('salt2_pm5_metrics')}
  - {input_path('pressure_branch_admission')}
  - {input_path('val_section_heat_ledger')}
  - {input_path('val_patch_heat_ledger')}
tags: [fluid-walls, readiness-ledger, salt2-pm5q, val-salt2, external-test]
related:
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/README.md
  - .agent/status/2026-07-17_AGENT-484.md
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt2 +/-5Q and val_salt2 fluid+walls Readiness Ledger

## Start Here

Open `fluid_walls_readiness_ledger.csv` first. It is the row-by-row ledger for
`salt2_lo5q`, `salt2_hi5q`, and `val_salt2` across the steady-state
`fluid+walls` dimensions: geometry, material stack, pressure model, thermal
circuit, source/sink role, boundary-layer state, recirculation flags, and
uncertainty.

This package is existing-evidence-only. It did not submit jobs, repair native
case trees, edit registry state, or change scientific admission. It assembles
the current evidence into one comparable status contract for tomorrow's model
work.

## Main Result

- Cases reviewed: `{summary['case_rows']}`.
- Readiness rows: `{summary['readiness_rows']}`.
- Pressure rows: `{summary['pressure_rows']}`.
- PM5/upcomer rows: `{summary['pm5_rows']}`.
- Thermal source/sink rows: `{summary['thermal_rows']}`.
- Fit-admitted pressure coefficient rows: `{summary['fit_admitted_pressure_rows']}`.
- Rows with admitted pressure model status: `{summary['status_counts']['pressure_model_status'].get('admitted', 0)}`.

Salt2 +/-5Q rows are holdout/testing-only. `val_salt2` is external-test-only.
None of these rows may be used for fitting, tuning, or model selection under
the AGENT-481 split policy.

## Files

- `case_inventory.csv`: case-level split role, legal use, representative time,
  terminal window, and evidence coverage.
- `fluid_walls_readiness_ledger.csv`: the main segment/branch readiness table.
- `thermal_source_sink_ledger.csv`: section heat/source/sink roles and sign
  convention.
- `pressure_readiness_ledger.csv`: pressure branch rows and admission blockers.
- `pm5_recirc_readiness_ledger.csv`: Salt2 +/-5Q PM5 repaired-field rows plus
  the explicit missing/queued `val_salt2` PM5 row.
- `uncertainty_and_admission_status.csv`: uncertainty blockers and fit/score
  implications.
- `source_manifest.csv`: all consumed source paths.
- `summary.json`: machine-readable counts and guardrail booleans.

## Interpretation

Geometry is mostly admitted because the segment map and model-form contract are
established. Material stack is still partial except for the bare-quartz test
section. Pressure is diagnostic for the 18 mapped branch rows: the harvested
ladders exist, but current pressure tables still admit zero true `f_D` or
component `K` fit rows. The three junction/stub rows are marked missing for
segment-local pressure because this package did not consume a junction-local
pressure/K artifact.

Thermal source/sink roles are present as realized CFD targets, not runtime model
inputs. Salt2 +/-5Q has section heat reduction and repaired PM5 wall-band fields.
`val_salt2` has a strong section/patch/junction heat ledger for external-test
scoring, but it does not yet have the same PM5/upcomer matched-plane evidence in
this source set.

## Do Not Do

- Do not fit or tune on `salt2_lo5q`, `salt2_hi5q`, or `val_salt2`.
- Do not promote diagnostic pressure rows into `f_D` or `K` coefficients.
- Do not treat realized `wallHeatFlux` or cooler duty as predictive runtime
  inputs.
- Do not infer `val_salt2` PM5/upcomer recirculation metrics from Salt2 +/-5Q.
- Do not submit duplicate pressure ladder jobs for these rows.

## Next Work

The shortest next step is a bounded F6/internal-Nu review for Salt2 +/-5Q using
the AGENT-406 repaired PM5 metrics, preserving holdout labels. A separate
optional follow-on can extract `val_salt2` PM5/upcomer fields on staged copies
if final external scoring requires matched-plane recirculation metrics.
"""
    (out / "README.md").write_text(readme)


def build(out: Path = OUT) -> dict[str, Any]:
    data = load_inputs()
    out.mkdir(parents=True, exist_ok=True)

    case_rows = case_inventory(data)
    readiness_rows = build_readiness_rows(data)
    validate_rows(readiness_rows)
    pressure_rows = build_pressure_ledger(data)
    pm5_rows = build_pm5_ledger(data)
    thermal_rows = build_thermal_ledger(data)
    uncertainty_rows = build_uncertainty_rows(readiness_rows)
    manifest_rows = source_manifest_rows()

    write_csv(out / "case_inventory.csv", case_rows)
    write_csv(out / "fluid_walls_readiness_ledger.csv", readiness_rows)
    write_csv(out / "pressure_readiness_ledger.csv", pressure_rows)
    write_csv(out / "pm5_recirc_readiness_ledger.csv", pm5_rows)
    write_csv(out / "thermal_source_sink_ledger.csv", thermal_rows)
    write_csv(out / "uncertainty_and_admission_status.csv", uncertainty_rows)
    write_csv(out / "source_manifest.csv", manifest_rows)

    status_counts = {field: dict(Counter(str(row[field]) for row in readiness_rows)) for field in STATUS_FIELDS}
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "case_rows": len(case_rows),
        "readiness_rows": len(readiness_rows),
        "pressure_rows": len(pressure_rows),
        "pm5_rows": len(pm5_rows),
        "thermal_rows": len(thermal_rows),
        "uncertainty_rows": len(uncertainty_rows),
        "fit_admitted_pressure_rows": sum(1 for row in pressure_rows if row["true_f_D_or_K_fit_admitted"] == "yes"),
        "status_counts": status_counts,
        "guardrails": {
            "native_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
            "duplicate_pressure_or_pm5_jobs": False,
            "scientific_admission_changed": False,
            "salt2_pm5q_fit_or_tune_allowed": False,
            "val_salt2_training_input_allowed": False,
        },
        "outputs": [
            "case_inventory.csv",
            "fluid_walls_readiness_ledger.csv",
            "pressure_readiness_ledger.csv",
            "pm5_recirc_readiness_ledger.csv",
            "thermal_source_sink_ledger.csv",
            "uncertainty_and_admission_status.csv",
            "source_manifest.csv",
            "README.md",
            "summary.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT, help="Output directory")
    args = parser.parse_args()
    summary = build(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
