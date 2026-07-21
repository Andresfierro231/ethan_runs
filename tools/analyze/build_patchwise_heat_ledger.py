#!/usr/bin/env python3
"""Build the formal patchwise heat ledger for admitted Salt 2/3/4 rows.

This is the thermal companion to the pressure-term ledger. It reuses the
AGENT-194 wallHeatFlux parser/classifier, but emits a stricter fit/validation
contract with source windows, sign convention, physical role, radiation caveat,
and explicit enthalpy/residual status fields.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from build_heat_source_sink_ledger import (
    CASES,
    CP_JIN_JKGK,
    build_case_ledger,
    compute_aggregate_check,
    find_latest_wallheatflux_dat,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07-08_patchwise_heat_ledger"
SOURCE_CONTRACT = ROOT / "work_products/2026-06-29_ethan_reduction_contract_audit/source_contract_map.csv"
SCENARIO_CONTRACT = ROOT / "work_products/2026-07-08_cfd_scenario_contract/scenario_contract.csv"
OBSERVATION_SCHEMA = ROOT / "work_products/2026-07-08_closure_observation_table/closure_observation_schema.csv"
SPAN_ENDPOINTS = ROOT / "work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv"

RECONSTRUCTED_T_BY_SOURCE = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": ROOT
    / "tmp/2026-06-30_claude_action_items/recon_salt2_of13/7915/T",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": ROOT
    / "tmp/2026-06-30_claude_action_items/recon_salt3_of13/7618/T",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": ROOT
    / "tmp/2026-06-30_claude_action_items/recon_salt4_of13/10000/T",
}

SEGMENT_ENDPOINT_SPANS = {
    "lower_leg": ["lower_leg"],
    "cooling_branch": ["upper_leg"],
    "downcomer": ["right_leg"],
    "upcomer": ["left_lower_leg", "test_section_span", "left_upper_leg"],
}

ADMITTED_SOURCES = set(CASES.keys())

FIELDS = [
    "source_id",
    "case_id",
    "run_class",
    "mesh_level",
    "mesh_status",
    "source_case_root",
    "source_window_start_s",
    "source_window_end_s",
    "source_window_count",
    "wallheatflux_source_path",
    "wallheatflux_sample_time_s",
    "time_window_source",
    "closure_observation_schema",
    "patch_group",
    "physical_role",
    "span",
    "patch_names",
    "bc_type",
    "bc_sign_convention",
    "wall_flux_sign_convention",
    "wallHeatFlux_integral_W",
    "wallHeatFlux_mean_W_m2",
    "heat_to_fluid_W",
    "heater_imposed_duty_W",
    "cooler_removed_duty_W",
    "passive_wall_heat_leak_gain_W",
    "junction_loss_W",
    "imposed_Q_sum_W",
    "imposed_Q_minus_wallHeatFlux_W",
    "T_bulk_inlet_K",
    "T_bulk_outlet_K",
    "T_bulk_span_K",
    "mdot_kg_s",
    "cp_jkgk",
    "enthalpy_change_W",
    "enthalpy_change_status",
    "segment_wallHeatFlux_sum_W",
    "segment_enthalpy_source",
    "wallHeatFlux_vs_enthalpy_residual_W",
    "residual_fraction",
    "residual_assignment",
    "patch_area_m2",
    "wall_temperature_source",
    "wall_temperature_sample_time_s",
    "wall_T_mean_K",
    "boundary_ambient_T_K",
    "boundary_h_W_m2K",
    "internal_convection_delta_T_K",
    "internal_convection_htc_W_m2K",
    "internal_convection_resistance_m2K_W",
    "wall_conduction_resistance_m2K_W",
    "external_convection_resistance_m2K_W",
    "external_radiation_resistance_m2K_W",
    "total_boundary_resistance_m2K_W",
    "network_terms_resolved",
    "radiation_output_term",
    "radiation_present",
    "radiation_caveat",
    "fit_eligible",
    "validation_eligible",
    "fit_use_status",
    "validation_use_status",
    "quality_flags",
    "notes",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def case_id(source_id: str) -> str:
    match = re.search(r"salt_test_(\d+)_jin", source_id)
    return f"salt_{match.group(1)}" if match else ""


def source_contracts() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in read_csv(SOURCE_CONTRACT)}


def scenario_contracts() -> dict[str, dict[str, str]]:
    return {
        row["source_id"]: row
        for row in read_csv(SCENARIO_CONTRACT)
        if row.get("run_class") == "mainline_jin_continuation"
    }


def physical_role(patch_group: str) -> str:
    return {
        "heater": "intended_heater_input",
        "test_section": "intended_test_section_input_actual_net_sink_possible",
        "cooler": "intended_cooler_removal",
        "ambient_wall": "passive_ambient_loss_or_gain",
        "junction_other": "junction_other_loss_or_gain",
    }.get(patch_group, "unknown")


def heat_to_fluid(row: dict[str, Any]) -> float | str:
    value = row.get("wallHeatFlux_integral_W", "")
    if value == "":
        return ""
    return float(value)


def source_time(source_id: str) -> tuple[str, str]:
    dat, time_dir = find_latest_wallheatflux_dat(CASES[source_id]["run_dir"])
    if dat is None:
        return "", ""
    return rel(dat), time_dir


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "nan", "NaN", "None"}:
        return None
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def fmt(value: Any, digits: int = 6) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def brace_blocks(content: str) -> dict[str, str]:
    """Return OpenFOAM boundary blocks keyed by quoted or bare patch name."""
    blocks: dict[str, str] = {}
    pattern = re.compile(r'(?m)^\s*(?:"([^"]+)"|([A-Za-z0-9_]+))\s*\{')
    for match in pattern.finditer(content):
        name = match.group(1) or match.group(2)
        start = content.find("{", match.start())
        depth = 0
        end = None
        for pos in range(start, len(content)):
            char = content[pos]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = pos
                    break
        if end is not None:
            blocks[name] = content[start + 1 : end]
    return blocks


def block_scalar(block: str, keyword: str) -> float | None:
    pattern = re.compile(
        rf"\b{re.escape(keyword)}\s+(?:uniform\s+|constant\s+)?"
        r"([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*;"
    )
    match = pattern.search(block)
    return safe_float(match.group(1)) if match else None


def block_type(block: str) -> str:
    match = re.search(r"\btype\s+([A-Za-z0-9_]+)\s*;", block)
    return match.group(1) if match else "unknown"


def block_number_list(block: str, keyword: str) -> list[float]:
    match = re.search(rf"\b{re.escape(keyword)}\s*\(([^;]+?)\)\s*;", block, re.DOTALL)
    if not match:
        return []
    return [
        float(token)
        for token in re.findall(r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?", match.group(1))
    ]


def block_coeff_lists(block: str, keyword: str) -> list[list[float]]:
    match = re.search(rf"\b{re.escape(keyword)}\s*\((.*?)\)\s*;", block, re.DOTALL)
    if not match:
        return []
    coeffs: list[list[float]] = []
    for group in re.finditer(r"\(([^()]*)\)", match.group(1)):
        coeffs.append(
            [
                float(token)
                for token in re.findall(
                    r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?", group.group(1)
                )
            ]
        )
    return coeffs


def eval_poly(coeffs: list[float], temperature_k: float) -> float | None:
    if not coeffs:
        return None
    value = sum(coef * (temperature_k**power) for power, coef in enumerate(coeffs))
    return value if value > 0 else None


def parse_bc_metadata(t_file: Path) -> dict[str, dict[str, Any]]:
    if not t_file.exists():
        return {}
    content = t_file.read_text(encoding="utf-8", errors="replace")
    metadata: dict[str, dict[str, Any]] = {}
    for patch, block in brace_blocks(content).items():
        metadata[patch] = {
            "type": block_type(block),
            "Q": block_scalar(block, "Q"),
            "h": block_scalar(block, "h"),
            "Ta": block_scalar(block, "Ta"),
            "Tsur": block_scalar(block, "Tsur"),
            "emissivity": block_scalar(block, "emissivity"),
            "thicknessLayers": block_number_list(block, "thicknessLayers"),
            "kappaLayerCoeffs": block_coeff_lists(block, "kappaLayerCoeffs"),
        }
    return metadata


def parse_wallheatflux_detail(dat_file: Path) -> tuple[dict[str, dict[str, float]], float | None]:
    by_time: dict[float, dict[str, dict[str, float]]] = defaultdict(dict)
    if not dat_file.exists():
        return {}, None
    with dat_file.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            try:
                time_s = float(parts[0])
                q_integral = float(parts[4])
                q_mean = float(parts[5])
            except ValueError:
                continue
            by_time[time_s][parts[1]] = {"Q_W": q_integral, "q_W_m2": q_mean}
    if not by_time:
        return {}, None
    latest = max(by_time)
    return by_time[latest], latest


def parse_wall_temperature_means(t_file: Path) -> dict[str, float]:
    if not t_file.exists():
        return {}
    content = t_file.read_text(encoding="utf-8", errors="replace")
    means: dict[str, float] = {}
    for patch, block in brace_blocks(content).items():
        uniform = re.search(
            r"\bvalue\s+uniform\s+([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*;",
            block,
        )
        if uniform:
            parsed = safe_float(uniform.group(1))
            if parsed is not None:
                means[patch] = parsed
            continue
        nonuniform = re.search(
            r"\bvalue\s+nonuniform\s+List<scalar>\s+\d+\s*\((.*?)\)\s*;",
            block,
            re.DOTALL,
        )
        if not nonuniform:
            continue
        values = [
            float(token)
            for token in re.findall(
                r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?", nonuniform.group(1)
            )
        ]
        if values:
            means[patch] = sum(values) / len(values)
    return means


def patch_area(detail: dict[str, float]) -> float:
    q_integral = detail.get("Q_W")
    q_mean = detail.get("q_W_m2")
    if q_integral is None or q_mean in {None, 0.0}:
        return 0.0
    return abs(q_integral / q_mean)


def layer_resistance(meta: dict[str, Any], wall_t_k: float | None) -> float | None:
    thicknesses = meta.get("thicknessLayers") or []
    coeffs = meta.get("kappaLayerCoeffs") or []
    if not thicknesses or not coeffs or wall_t_k is None:
        return None
    total = 0.0
    for thickness, layer_coeffs in zip(thicknesses, coeffs):
        kappa = eval_poly(layer_coeffs, wall_t_k)
        if kappa is None:
            return None
        total += thickness / kappa
    return total


def area_weighted(patches: list[str], values: dict[str, float | None], areas: dict[str, float]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for patch in patches:
        value = values.get(patch)
        area = areas.get(patch, 0.0)
        if value is None or area <= 0:
            continue
        numerator += value * area
        denominator += area
    if denominator <= 0:
        return None
    return numerator / denominator


def radiation_output_term(run_dir: Path) -> tuple[bool, str]:
    for child in run_dir.iterdir():
        if child.is_dir() and child.name.replace(".", "", 1).isdigit():
            if (child / "qr").exists():
                return True, rel(child / "qr")
    for candidate in (run_dir / "0" / "qr", run_dir / "postProcessing" / "qr"):
        if candidate.exists():
            return True, rel(candidate)
    return False, ""


def load_endpoint_segments(mdot_by_source: dict[str, float]) -> dict[tuple[str, str], dict[str, Any]]:
    endpoint_rows = read_csv(SPAN_ENDPOINTS)
    by_source_span = {
        (row.get("source_id", ""), row.get("span", "")): row for row in endpoint_rows
    }
    segments: dict[tuple[str, str], dict[str, Any]] = {}
    for source_id, mdot in mdot_by_source.items():
        for segment, spans in SEGMENT_ENDPOINT_SPANS.items():
            selected = [by_source_span.get((source_id, span)) for span in spans]
            selected = [row for row in selected if row]
            if len(selected) != len(spans):
                continue
            deltas = [safe_float(row.get("delta_T_flow_dir_k")) for row in selected]
            if any(delta is None for delta in deltas):
                continue
            t_in = safe_float(selected[0].get("T_in_bulk_k"))
            t_out = safe_float(selected[-1].get("T_out_bulk_k"))
            recirc_values = []
            for row in selected:
                for key in ("T_s00_recirc_ratio", "T_s04_recirc_ratio"):
                    value = safe_float(row.get(key))
                    if value is not None:
                        recirc_values.append(value)
            delta_sum = sum(delta for delta in deltas if delta is not None)
            segments[(source_id, segment)] = {
                "T_in_bulk_K": t_in,
                "T_out_bulk_K": t_out,
                "delta_T_K": delta_sum,
                "enthalpy_change_W": mdot * CP_JIN_JKGK * delta_sum,
                "source": rel(SPAN_ENDPOINTS) + ":" + "+".join(spans),
                "max_recirc_ratio": max(recirc_values) if recirc_values else None,
                "status": ",".join(sorted({row.get("status_s00", "") for row in selected} | {row.get("status_s04", "") for row in selected})),
            }
    return segments


def build_rows() -> list[dict[str, Any]]:
    sources = source_contracts()
    scenarios = scenario_contracts()
    mdot_by_source: dict[str, float] = {}
    raw_by_source: dict[str, list[dict[str, Any]]] = {}
    for source_id, cfg in CASES.items():
        raw_rows = build_case_ledger(source_id, cfg)
        raw_by_source[source_id] = raw_rows
        mdot = next((safe_float(row.get("mdot_kg_s")) for row in raw_rows if safe_float(row.get("mdot_kg_s")) is not None), None)
        if mdot is not None:
            mdot_by_source[source_id] = mdot
    endpoint_segments = load_endpoint_segments(mdot_by_source)
    output: list[dict[str, Any]] = []
    for source_id, cfg in CASES.items():
        raw_rows = raw_by_source[source_id]
        whf_path, whf_time = source_time(source_id)
        whf_detail: dict[str, dict[str, float]] = {}
        if whf_path:
            whf_detail, _ = parse_wallheatflux_detail(ROOT / whf_path)
        bc_meta = parse_bc_metadata(cfg["run_dir"] / "0" / "T")
        wall_t_path = RECONSTRUCTED_T_BY_SOURCE.get(source_id)
        wall_t = parse_wall_temperature_means(wall_t_path) if wall_t_path else {}
        radiation_present, radiation_term = radiation_output_term(cfg["run_dir"])
        segment_wall_flux = defaultdict(float)
        for row in raw_rows:
            segment_wall_flux[row["span"]] += safe_float(row.get("wallHeatFlux_integral_W")) or 0.0
        source_contract = sources[source_id]
        scenario = scenarios.get(source_id, {})
        for row in raw_rows:
            patches = [patch.strip() for patch in row["patch_names"].split(",") if patch.strip()]
            patch_areas = {patch: patch_area(whf_detail.get(patch, {})) for patch in patches}
            total_area = sum(patch_areas.values())
            imposed_values = [bc_meta.get(patch, {}).get("Q") for patch in patches]
            imposed_present = any(value is not None for value in imposed_values)
            imposed_q = sum(value for value in imposed_values if value is not None)
            wall_flux = safe_float(row.get("wallHeatFlux_integral_W")) or 0.0
            wall_flux_mean = wall_flux / total_area if total_area > 0 else None
            wall_t_values = {patch: wall_t.get(patch) for patch in patches}
            h_values = {patch: bc_meta.get(patch, {}).get("h") for patch in patches}
            ambient_values = {
                patch: bc_meta.get(patch, {}).get("Ta") or bc_meta.get(patch, {}).get("Tsur")
                for patch in patches
            }
            conduction_values = {
                patch: layer_resistance(bc_meta.get(patch, {}), wall_t_values.get(patch))
                for patch in patches
            }
            convection_values = {
                patch: (1.0 / h_values[patch] if h_values.get(patch) else None)
                for patch in patches
            }
            wall_t_mean = area_weighted(patches, wall_t_values, patch_areas)
            h_mean = area_weighted(patches, h_values, patch_areas)
            ambient_t = area_weighted(patches, ambient_values, patch_areas)
            wall_conduction_r = area_weighted(patches, conduction_values, patch_areas)
            external_convection_r = area_weighted(patches, convection_values, patch_areas)
            total_boundary_r = None
            if wall_conduction_r is not None or external_convection_r is not None:
                total_boundary_r = (wall_conduction_r or 0.0) + (external_convection_r or 0.0)
            endpoint = endpoint_segments.get((source_id, row["span"]))
            t_in = endpoint.get("T_in_bulk_K") if endpoint else None
            t_out = endpoint.get("T_out_bulk_K") if endpoint else None
            enthalpy = endpoint.get("enthalpy_change_W") if endpoint else None
            segment_q = segment_wall_flux[row["span"]]
            residual = segment_q - enthalpy if enthalpy is not None else None
            residual_fraction = residual / abs(enthalpy) if enthalpy not in {None, 0.0} else None
            t_bulk_span = safe_float(row.get("T_bulk_span_K"))
            if t_bulk_span is None and t_in is not None and t_out is not None:
                t_bulk_span = 0.5 * (t_in + t_out)
            internal_delta_t = wall_t_mean - t_bulk_span if wall_t_mean is not None and t_bulk_span is not None else None
            internal_htc = None
            internal_r = None
            if internal_delta_t not in {None, 0.0} and wall_flux_mean is not None:
                internal_htc = wall_flux_mean / internal_delta_t
                internal_r = 1.0 / internal_htc if internal_htc != 0 else None
            flags = ["coarse_no_gci"]
            if row["patch_group"] == "test_section" and float(row["wallHeatFlux_integral_W"]) < 0:
                flags.append("intended_input_actual_net_sink")
            if row["patch_group"] == "junction_other":
                flags.append("junction_grouped_mixed_bc")
            if endpoint and safe_float(endpoint.get("max_recirc_ratio")) and float(endpoint["max_recirc_ratio"]) > 0.5:
                flags.append("high_recirculation_endpoint_temperature")
            if not radiation_present:
                flags.append("no_qr_radiation_output")
            enthalpy_status = "computed_from_span_endpoint_temperatures"
            residual_assignment = "segment_wall_flux_minus_segment_enthalpy_change"
            if row["span"] == "cooling_branch":
                enthalpy_status = "computed_but_cooler_cut_planes_only_partially_bracket_sink"
            elif row["span"] == "upcomer":
                enthalpy_status = "computed_diagnostic_only_high_recirculation"
                residual_assignment = "diagnostic_only_upcomer_recirculation_cell"
            elif row["span"] == "junction":
                enthalpy_status = "not_bracketed_by_endpoint_temperature_segment"
                residual_assignment = "junction_loss_reported_as_wall_flux_not_segment_enthalpy"
            elif enthalpy is None:
                enthalpy_status = "missing_endpoint_temperature_segment"
                residual_assignment = "not_computable_until_endpoint_temperature_available"
            network_terms = [
                "wallHeatFlux_interface",
                "effective_internal_convection_from_wall_T_minus_bulk_T",
                "wall_conduction_from_bc_thickness_kappa_layers",
                "external_convection_from_bc_h",
                "junction_losses_grouped_by_junction_other",
            ]
            if radiation_present:
                network_terms.append("radiation_from_qr_output")
            else:
                network_terms.append("radiation_absent_no_qr_output")
            out = {
                "source_id": source_id,
                "case_id": case_id(source_id),
                "run_class": "mainline_jin_continuation",
                "mesh_level": "coarse",
                "mesh_status": "coarse_no_gci",
                "source_case_root": scenario.get("case_root", str(cfg["run_dir"].relative_to(ROOT))),
                "source_window_start_s": source_contract.get("requested_time_start_s", ""),
                "source_window_end_s": source_contract.get("requested_time_end_s", ""),
                "source_window_count": source_contract.get("requested_time_count", ""),
                "wallheatflux_source_path": whf_path,
                "wallheatflux_sample_time_s": whf_time,
                "time_window_source": rel(SOURCE_CONTRACT),
                "closure_observation_schema": rel(OBSERVATION_SCHEMA),
                "patch_group": row["patch_group"],
                "physical_role": physical_role(row["patch_group"]),
                "span": row["span"],
                "patch_names": row["patch_names"],
                "bc_type": row["bc_type"],
                "bc_sign_convention": row["bc_sign_convention"],
                "wall_flux_sign_convention": "positive_into_fluid_negative_out_of_fluid",
                "wallHeatFlux_integral_W": row["wallHeatFlux_integral_W"],
                "wallHeatFlux_mean_W_m2": fmt(wall_flux_mean),
                "heat_to_fluid_W": heat_to_fluid(row),
                "heater_imposed_duty_W": fmt(imposed_q) if row["patch_group"] == "heater" else "",
                "cooler_removed_duty_W": fmt(-wall_flux) if row["patch_group"] == "cooler" else "",
                "passive_wall_heat_leak_gain_W": fmt(wall_flux) if row["patch_group"] == "ambient_wall" else "",
                "junction_loss_W": fmt(wall_flux) if row["patch_group"] == "junction_other" else "",
                "imposed_Q_sum_W": fmt(imposed_q) if imposed_present else "",
                "imposed_Q_minus_wallHeatFlux_W": fmt(imposed_q - wall_flux) if imposed_present else "",
                "T_bulk_inlet_K": fmt(t_in),
                "T_bulk_outlet_K": fmt(t_out),
                "T_bulk_span_K": fmt(t_bulk_span),
                "mdot_kg_s": row["mdot_kg_s"],
                "cp_jkgk": CP_JIN_JKGK,
                "enthalpy_change_W": fmt(enthalpy),
                "enthalpy_change_status": enthalpy_status,
                "segment_wallHeatFlux_sum_W": fmt(segment_q),
                "segment_enthalpy_source": endpoint.get("source", "") if endpoint else "",
                "wallHeatFlux_vs_enthalpy_residual_W": fmt(residual),
                "residual_fraction": fmt(residual_fraction),
                "residual_assignment": residual_assignment,
                "patch_area_m2": fmt(total_area),
                "wall_temperature_source": rel(wall_t_path) if wall_t_path else "",
                "wall_temperature_sample_time_s": wall_t_path.parent.name if wall_t_path else "",
                "wall_T_mean_K": fmt(wall_t_mean),
                "boundary_ambient_T_K": fmt(ambient_t),
                "boundary_h_W_m2K": fmt(h_mean),
                "internal_convection_delta_T_K": fmt(internal_delta_t),
                "internal_convection_htc_W_m2K": fmt(internal_htc),
                "internal_convection_resistance_m2K_W": fmt(internal_r),
                "wall_conduction_resistance_m2K_W": fmt(wall_conduction_r),
                "external_convection_resistance_m2K_W": fmt(external_convection_r),
                "external_radiation_resistance_m2K_W": "" if radiation_present else "absent_no_qr_output",
                "total_boundary_resistance_m2K_W": fmt(total_boundary_r),
                "network_terms_resolved": ";".join(network_terms),
                "radiation_output_term": radiation_term,
                "radiation_present": radiation_present,
                "radiation_caveat": (
                    "qr_output_present"
                    if radiation_present
                    else "surface_emissivity_bc_metadata_present_but_no_qr_radiation_output"
                ),
                "fit_eligible": "no",
                "validation_eligible": "yes",
                "fit_use_status": "validation_only_thermal_residual_not_fit_target",
                "validation_use_status": "thermal_validation_diagnostic",
                "quality_flags": ";".join(flags),
                "notes": row["note"],
            }
            output.append(out)
    output.sort(key=lambda r: (r["source_id"], r["span"], r["patch_group"]))
    return output


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    required = [
        "source_id",
        "case_id",
        "run_class",
        "source_case_root",
        "source_window_start_s",
        "source_window_end_s",
        "wallheatflux_source_path",
        "wallheatflux_sample_time_s",
        "patch_group",
        "physical_role",
        "span",
        "bc_type",
        "bc_sign_convention",
        "wallHeatFlux_integral_W",
        "heat_to_fluid_W",
        "enthalpy_change_status",
        "residual_assignment",
        "patch_area_m2",
        "network_terms_resolved",
        "radiation_caveat",
        "fit_eligible",
        "validation_eligible",
    ]
    for index, row in enumerate(rows, start=2):
        row_id = f"{row.get('source_id')}:{row.get('span')}:{row.get('patch_group')}"
        for field in required:
            if str(row.get(field, "")).strip() == "":
                errors.append(f"{row_id}: missing {field}")
        if row.get("source_id") not in ADMITTED_SOURCES:
            errors.append(f"{row_id}: non-admitted source")
        try:
            float(row["wallHeatFlux_integral_W"])
        except (TypeError, ValueError):
            errors.append(f"{row_id}: nonnumeric wallHeatFlux_integral_W")
        if row.get("fit_eligible") != "no":
            errors.append(f"{row_id}: heat rows must remain validation-only")
        if row.get("validation_eligible") != "yes":
            errors.append(f"{row_id}: validation_eligible must be yes")
        if row.get("span") != "junction":
            if safe_float(row.get("enthalpy_change_W")) is None:
                errors.append(f"{row_id}: missing enthalpy_change_W")
            if safe_float(row.get("wallHeatFlux_vs_enthalpy_residual_W")) is None:
                errors.append(f"{row_id}: missing wallHeatFlux_vs_enthalpy_residual_W")
            if str(row.get("segment_enthalpy_source", "")).strip() == "":
                errors.append(f"{row_id}: missing segment_enthalpy_source")
        if row.get("patch_group") in {"heater", "cooler", "test_section"} and safe_float(row.get("imposed_Q_sum_W")) is None:
            errors.append(f"{row_id}: missing imposed_Q_sum_W for active thermal BC")
        if safe_float(row.get("patch_area_m2")) is None:
            errors.append(f"{row_id}: missing patch_area_m2")
        if "radiation_absent_no_qr_output" not in row.get("network_terms_resolved", "") and not row.get("radiation_output_term"):
            errors.append(f"{row_id}: missing radiation absence note")
        if not (ROOT / str(row.get("wallheatflux_source_path", ""))).exists():
            errors.append(f"{row_id}: wallheatflux_source_path missing on disk")
        wall_temp_source = row.get("wall_temperature_source", "")
        if wall_temp_source and not (ROOT / str(wall_temp_source)).exists():
            errors.append(f"{row_id}: wall_temperature_source missing on disk")
    return errors


def aggregate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    net_by_source: dict[str, float] = defaultdict(float)
    heater_by_source: dict[str, float] = defaultdict(float)
    heater_imposed_by_source: dict[str, float] = defaultdict(float)
    cooler_by_source: dict[str, float] = defaultdict(float)
    cooler_imposed_by_source: dict[str, float] = defaultdict(float)
    test_section_by_source: dict[str, float] = defaultdict(float)
    nonjunction_residuals: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        q = float(row["wallHeatFlux_integral_W"])
        net_by_source[row["source_id"]] += q
        if row["patch_group"] == "heater":
            heater_by_source[row["source_id"]] += q
            heater_imposed_by_source[row["source_id"]] += safe_float(row.get("heater_imposed_duty_W")) or 0.0
        if row["patch_group"] == "cooler":
            cooler_by_source[row["source_id"]] += q
            cooler_imposed_by_source[row["source_id"]] += safe_float(row.get("imposed_Q_sum_W")) or 0.0
        if row["patch_group"] == "test_section":
            test_section_by_source[row["source_id"]] += q
        residual = safe_float(row.get("wallHeatFlux_vs_enthalpy_residual_W"))
        if row.get("span") != "junction" and residual is not None:
            nonjunction_residuals[row["source_id"]].append(residual)
    return {
        sid: {
            "heater_imposed_duty_W": round(heater_imposed_by_source[sid], 3),
            "heater_input_W": round(heater_by_source[sid], 3),
            "heater_imposed_minus_wallHeatFlux_W": round(heater_imposed_by_source[sid] - heater_by_source[sid], 3),
            "cooler_imposed_duty_W": round(cooler_imposed_by_source[sid], 3),
            "cooler_removal_W": round(cooler_by_source[sid], 3),
            "test_section_wallHeatFlux_W": round(test_section_by_source[sid], 3),
            "net_wallHeatFlux_W": round(net_by_source[sid], 3),
            "net_fraction_of_heater": round(net_by_source[sid] / abs(heater_by_source[sid]), 6),
            "max_abs_segment_enthalpy_residual_W": round(
                max(abs(value) for value in nonjunction_residuals[sid]), 3
            ),
        }
        for sid in sorted(net_by_source)
    }


def write_readme(rows: list[dict[str, Any]], errors: list[str]) -> None:
    summary = aggregate_summary(rows)
    text = f"""# Patchwise Heat Ledger

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

Formal patchwise heat-source/sink ledger for admitted Salt 2/3/4 Jin mainline
continuations. This is the thermal companion to the July 8 pressure-term ledger.
It is read-only with respect to native solver outputs.

## Contract

- `wallHeatFlux_integral_W` and `heat_to_fluid_W` use the OpenFOAM convention:
  positive is heat into the fluid, negative is heat out of the fluid.
- Rows are grouped by physical role: heater input, cooler removal, passive
  ambient exchange, test-section exchange, and junction/other exchange.
- `heater_imposed_duty_W`, `cooler_removed_duty_W`,
  `passive_wall_heat_leak_gain_W`, and `junction_loss_W` provide the role-level
  heat-source/sink terms requested for closure audits.
- `enthalpy_change_W` is computed from
  `{rel(SPAN_ENDPOINTS)}` using the Jin salt cp and the mdot already admitted by
  the source heat ledger. Junction rows remain unbracketed.
- `wallHeatFlux_vs_enthalpy_residual_W` is a segment residual:
  segment wallHeatFlux sum minus segment enthalpy-flow change. It is repeated on
  rows in the same segment so each patch group is fit-ready without extra joins.
- The resistance network is resolved from available OpenFOAM outputs as:
  effective internal convection from wall T minus bulk T, BC wall/layer
  conduction from `thicknessLayers` and `kappaLayerCoeffs`, external convection
  from BC `h`, grouped junction losses, and radiation only if a `qr` output
  field exists.
- `radiation_present=False` means no OpenFOAM `qr` output term was found. Surface
  emissivity metadata alone is not treated as a radiation heat ledger term.
- All rows are validation diagnostics, not fit targets.

## Outputs

- `patchwise_heat_ledger.csv`
- `patchwise_heat_ledger.json`
- `summary.json`
- `README.md`

## Counts

- Rows: `{len(rows)}`
- Source ids: `{len({row['source_id'] for row in rows})}`
- Patch groups: `{dict(sorted(Counter(row['patch_group'] for row in rows).items()))}`
- Validation errors: `{len(errors)}`

## Aggregate Wall-Flux Sums

```json
{json.dumps(summary, indent=2)}
```

## Interpretation Notes

- Cooler specified duty matches `wallHeatFlux` closely for these rows; heater
  specified duty exceeds realized interface `wallHeatFlux`, so heater residuals
  should be interpreted as boundary/solid/storage or staging mismatch until a
  same-time solid-energy audit is available.
- Upcomer rows are diagnostic only because the endpoint-temperature source shows
  high recirculation fractions; treat those residuals as recirculation-cell
  evidence, not pipe-friction closure evidence.
- Specified-Q boundary rows without layer/h metadata still carry imposed duty,
  wall flux, wall temperature, and segment residuals, but their external
  resistance sub-stack is intentionally blank.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_outputs(rows: list[dict[str, Any]], errors: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "patchwise_heat_ledger.csv", rows, FIELDS)
    (OUT / "patchwise_heat_ledger.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "TODO-PATCHWISE-HEAT-LEDGER",
        "rows": len(rows),
        "source_ids": sorted({row["source_id"] for row in rows}),
        "patch_groups": dict(sorted(Counter(row["patch_group"] for row in rows).items())),
        "aggregate_wall_flux": aggregate_summary(rows),
        "validation_errors": errors,
        "validation_passed": not errors,
        "limitations": [
            "junction rows are not bracketed by endpoint enthalpy segments",
            "upcomer enthalpy residuals are diagnostic only because endpoint recirculation fractions are high",
            "specified-Q boundary rows without layer/h metadata do not expose a complete external resistance sub-stack",
            "surface emissivity boundary metadata exists, but radiation is absent unless OpenFOAM exposes a qr output term",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(rows, errors)


def main() -> int:
    rows = build_rows()
    errors = validate_rows(rows)
    write_outputs(rows, errors)
    print(f"patchwise_heat_rows={len(rows)}")
    print(f"validation_errors={len(errors)}")
    if errors:
        for error in errors[:20]:
            print(f"ERROR: {error}")
        return 1
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
