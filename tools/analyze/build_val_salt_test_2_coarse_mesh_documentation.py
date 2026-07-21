#!/usr/bin/env python3
"""Build the val_salt_test_2_coarse_mesh documentation package.

This is a read-only documentation builder. It inspects existing case files,
registry aggregates, and prior documentation packages, then writes a compact
lineage, boundary-condition, material-property, and Salt2 Jin comparison
package for AGENT-354.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-354"
DATE = "2026-07-14"
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation"

VAL_CASE = ROOT / "jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation"
JIN_CASE = ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation"

VAL_IMPORT = ROOT / "imports/2026-05-29_val_salt_test_2_coarse_mesh_laminar_import.json"
JIN_IMPORT = ROOT / "imports/2026-06-02_viscosity_screening_salt_test_2_jin_coarse_mesh_import.json"
CASE_REGISTRY = ROOT / "registry/case_registry.csv"
VAL_AGG_MANIFEST = ROOT / "registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregation_manifest.json"
JIN_AGG_MANIFEST = ROOT / "registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/aggregation_manifest.json"
VAL_CASE_SUMMARY = ROOT / "registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates/case_summary.csv"
JIN_CASE_SUMMARY = ROOT / "registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/aggregates/case_summary.csv"
VAL_WALL_HEAT = ROOT / "registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates/wall_heat_flux_grouped.csv"
JIN_WALL_HEAT = ROOT / "registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/aggregates/wall_heat_flux_grouped.csv"
DIRECT_VALIDATION = ROOT / "reports/2026-06/2026-06-04/2026-06-04_ethan_direct_validation/ethan_direct_validation_metrics.csv"
PAPER_CASE_INVENTORY = ROOT / "reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/paper_case_inventory.csv"
SUBMITTED_STEADY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv"
COMPACT_STEADY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_compact_lineage_table.csv"
FLOW_BC_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv"
FLOW_BC_SEMANTICS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/bc_semantics_and_assumptions.csv"
FLOW_PATCH_ROLES = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/patch_role_bc_summary.csv"
TRIAGE_COMPARISON = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/salt2_jin_vs_val_comparison.csv"
THERMAL_BOUNDARY_MAP = ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"
VAL_CAMPAIGN_README = ROOT / "jadyn_runs/salt2/2026-06-01_continuation_candidate/README.md"
JIN_CAMPAIGN_README = ROOT / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/README.md"


CASE_SPECS = [
    {
        "case_label": "val_salt_test_2_coarse_mesh",
        "canonical_display_label": "val_salt_test_2_coarse_mesh",
        "legacy_source_id": "val_salt_test_2_coarse_mesh_laminar",
        "runtime_display_label": "val_salt_test_2_coarse_mesh_laminar_continuation",
        "root": VAL_CASE,
        "import_manifest": VAL_IMPORT,
        "agg_manifest": VAL_AGG_MANIFEST,
        "case_summary": VAL_CASE_SUMMARY,
        "wall_heat": VAL_WALL_HEAT,
    },
    {
        "case_label": "salt2_jin",
        "canonical_display_label": "salt2_jin",
        "legacy_source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "runtime_display_label": "viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "root": JIN_CASE,
        "import_manifest": JIN_IMPORT,
        "agg_manifest": JIN_AGG_MANIFEST,
        "case_summary": JIN_CASE_SUMMARY,
        "wall_heat": JIN_WALL_HEAT,
    },
]


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "nan", "NaN", "None"}:
        return None
    try:
        parsed = float(text.replace("+", ""))
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, digits: int = 6) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "" if value is None else str(value)
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def first_row(path: Path, source_id: str | None = None) -> dict[str, str]:
    for row in read_csv(path):
        if source_id is None or row.get("source_id") == source_id or row.get("run_key") == source_id:
            return row
    return {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_section(text: str, path: list[str]) -> str:
    lines = text.splitlines()
    start = 0
    indent = -1
    body = lines
    for key in path:
        found = False
        for i, line in enumerate(body[start:], start=start):
            match = re.match(r"^(\s*)" + re.escape(key) + r":\s*$", line)
            if match:
                indent = len(match.group(1))
                start = i + 1
                found = True
                break
        if not found:
            return ""
        end = len(body)
        for j in range(start, len(body)):
            if body[j].strip() and (len(body[j]) - len(body[j].lstrip(" "))) <= indent:
                end = j
                break
        body = body[start:end]
        start = 0
    return "\n".join(body)


def yaml_scalar(text: str, key: str) -> str:
    match = re.search(r"^\s*" + re.escape(key) + r":\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip("'\"") if match else ""


def yaml_list_after(text: str, key: str) -> str:
    lines = text.splitlines()
    values: list[str] = []
    for i, line in enumerate(lines):
        if re.match(r"^\s*" + re.escape(key) + r":\s*$", line):
            indent = len(line) - len(line.lstrip(" "))
            for nxt in lines[i + 1 :]:
                stripped = nxt.strip()
                if stripped.startswith("- "):
                    values.append(stripped[2:])
                elif stripped and (len(nxt) - len(nxt.lstrip(" "))) <= indent:
                    break
            break
    return " ".join(values)


def parse_case_config(path: Path) -> dict[str, str]:
    text = read_text(path)
    op = extract_section(text, ["operating_point"])
    heater = extract_section(text, ["bc_params", "heater"])
    cooler = extract_section(text, ["bc_params", "cooler"])
    test_section = extract_section(text, ["bc_params", "test_section"])
    insulated = extract_section(text, ["bc_params", "insulated"])
    fluid_props = extract_section(text, ["fluid_properties"])
    mu = extract_section(fluid_props, ["mu_spec"])
    kappa = extract_section(fluid_props, ["kappa_spec"])
    return {
        "fluid": yaml_scalar(text, "fluid"),
        "turbulence_model": yaml_scalar(text, "turbulence_model"),
        "case_id": yaml_scalar(op, "case_id"),
        "heater_power_W": yaml_scalar(op, "heater_power_W"),
        "cooling_power_W": yaml_scalar(op, "cooling_power_W"),
        "T_init_K": yaml_scalar(op, "T_init_K"),
        "heater_Q_W": yaml_scalar(heater, "Q"),
        "heater_h_metadata": yaml_scalar(heater, "h"),
        "heater_Ta_metadata_K": yaml_scalar(heater, "Ta"),
        "heater_emissivity_metadata": yaml_scalar(heater, "emissivity"),
        "cooler_h_metadata": yaml_scalar(cooler, "h"),
        "cooler_Ta_metadata_K": yaml_scalar(cooler, "Ta"),
        "test_section_h_metadata": yaml_scalar(test_section, "h"),
        "test_section_Ta_metadata_K": yaml_scalar(test_section, "Ta"),
        "insulated_h_metadata": yaml_scalar(insulated, "h"),
        "insulated_Ta_metadata_K": yaml_scalar(insulated, "Ta"),
        "mu_model": yaml_scalar(mu, "type"),
        "mu_coeffs": yaml_list_after(mu, "coeffs"),
        "kappa_model": yaml_scalar(kappa, "type"),
        "kappa_coeffs": yaml_list_after(kappa, "coeffs"),
        "Cp_coeffs": yaml_list_after(fluid_props, "Cp_coeffs"),
        "rho_coeffs": yaml_list_after(fluid_props, "rho_coeffs"),
        "mesh_group_id": yaml_scalar(text, "mesh_group_id"),
        "nprocs": yaml_scalar(text, "nprocs"),
        "scale_to_meters": yaml_scalar(text, "scale_to_meters"),
    }


def extract_foam_value(block: str, key: str) -> str:
    match = re.search(r"\b" + re.escape(key) + r"\s+(?:uniform|constant)?\s*([^;\n]+)", block)
    return match.group(1).strip() if match else ""


def parse_boundary_blocks(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    matches = list(re.finditer(r'^\s*"([^"]+)"\s*\n\s*\{', text, flags=re.MULTILINE))
    blocks: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else text.rfind("}")
        block = text[start:end]
        blocks.append(
            {
                "patch": match.group(1),
                "type": extract_foam_value(block, "type"),
                "Q_W": extract_foam_value(block, "Q"),
                "h_W_m2K": extract_foam_value(block, "h"),
                "Ta_K": extract_foam_value(block, "Ta"),
                "Tsur_K": extract_foam_value(block, "Tsur"),
                "emissivity": extract_foam_value(block, "emissivity"),
                "internalRadius_m": extract_foam_value(block, "internalRadius"),
                "thicknessLayers_m": extract_foam_value(block, "thicknessLayers").strip("()"),
                "powerLayer": extract_foam_value(block, "powerLayer"),
            }
        )
    return blocks


def classify_patch(patch: str, patch_type: str) -> str:
    if patch.startswith("ncc_"):
        return "zero_gradient_ncc_connector"
    if patch in {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}:
        return "heater"
    if patch in {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}:
        return "cooler"
    if patch == "pipeleg_left_04_test_section":
        return "test_section"
    if patch.startswith("junction_") or "stub" in patch:
        return "junction_or_stub"
    if patch_type == "externalTemperature":
        return "fixed_external_temperature_passive_or_stub"
    return "passive_ambient_wall"


def summarize_temperature_boundaries(spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = parse_boundary_blocks(spec["root"] / "0/T")
    detail_rows: list[dict[str, str]] = []
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        role = classify_patch(row["patch"], row["type"])
        grouped[role].append(row)
        detail_rows.append(
            {
                "case_label": spec["case_label"],
                "source_id": spec["legacy_source_id"],
                "field": "T",
                "patch": row["patch"],
                "role": role,
                "patch_type": row["type"],
                "Q_W": row["Q_W"],
                "h_W_m2K": row["h_W_m2K"],
                "Ta_K": row["Ta_K"],
                "Tsur_K": row["Tsur_K"],
                "emissivity": row["emissivity"],
                "thicknessLayers_m": row["thicknessLayers_m"],
                "semantics": boundary_semantics(row["type"], row["Q_W"], row["Tsur_K"], row["emissivity"]),
                "evidence_path": rel(spec["root"] / "0/T"),
            }
        )

    summary_rows: list[dict[str, Any]] = []
    for role, role_rows in sorted(grouped.items()):
        q_sum = sum(as_float(r["Q_W"]) or 0.0 for r in role_rows)
        h_vals = [as_float(r["h_W_m2K"]) for r in role_rows if as_float(r["h_W_m2K"]) is not None]
        types = sorted({r["type"] for r in role_rows if r["type"]})
        tas = sorted({r["Ta_K"] for r in role_rows if r["Ta_K"]})
        tsurs = sorted({r["Tsur_K"] for r in role_rows if r["Tsur_K"]})
        emiss = sorted({r["emissivity"] for r in role_rows if r["emissivity"]})
        thicknesses = sorted({r["thicknessLayers_m"] for r in role_rows if r["thicknessLayers_m"]})
        summary_rows.append(
            {
                "case_label": spec["case_label"],
                "source_id": spec["legacy_source_id"],
                "field": "T",
                "role": role,
                "patch_count": len(role_rows),
                "patch_types": ";".join(types),
                "imposed_Q_W_sum": fmt(q_sum),
                "h_min_W_m2K": fmt(min(h_vals)) if h_vals else "",
                "h_max_W_m2K": fmt(max(h_vals)) if h_vals else "",
                "Ta_K_values": ";".join(tas),
                "Tsur_K_values": ";".join(tsurs),
                "emissivity_values": ";".join(emiss),
                "thicknessLayers_m_values": " | ".join(thicknesses[:8]) + (" | ..." if len(thicknesses) > 8 else ""),
                "semantics": role_semantics(role, types),
                "evidence_path": rel(spec["root"] / "0/T"),
            }
        )
    return summary_rows, detail_rows


def boundary_semantics(patch_type: str, q_w: str, tsur: str, emissivity: str) -> str:
    if patch_type == "zeroGradient":
        return "thermal connector; no explicit external heat exchange"
    if patch_type == "externalTemperature" and q_w:
        return "fixed imposed Q boundary; cooler/removal sign is negative in these cases"
    if patch_type == "rcExternalTemperature":
        suffix = " with emissivity/Tsur radiation folded into total wallHeatFlux" if tsur or emissivity else ""
        return "resistance/capacitance external wall model" + suffix
    if patch_type == "externalTemperature":
        return "external temperature style passive/stub boundary"
    return patch_type


def role_semantics(role: str, types: list[str]) -> str:
    if role == "heater":
        return "Three lower-leg heater patches impose 88.5666667 W each through rcExternalTemperature powerLayer 1; emissivity/Tsur radiation is folded into total wallHeatFlux."
    if role == "cooler":
        return "Upper reducer/cooler/reducer patches impose fixed negative Q; metadata cooler h is not the live OpenFOAM knob."
    if role == "test_section":
        return "Powered test-section patch imposes 37 W separately from case-level heater_power_W."
    if role == "passive_ambient_wall":
        return "Passive loop wall heat exchange through rcExternalTemperature with Ta/Tsur/emissivity and wall layers."
    if role == "junction_or_stub":
        return "Junction and stub patches mix rcExternalTemperature and externalTemperature wall-loss treatments."
    if role == "zero_gradient_ncc_connector":
        return "Non-conformal connector thermal patches use zeroGradient; they are not inlets/outlets."
    return "Boundary role inferred from patch name and type: " + ";".join(types)


def motion_boundary_rows(spec: dict[str, Any]) -> list[dict[str, Any]]:
    u_text = read_text(spec["root"] / "0/U")
    p_text = read_text(spec["root"] / "0/p_rgh")
    slip_match = re.search(r'"\(([^"]+)\)"\s*\{\s*type\s+slip;', u_text, flags=re.S)
    slip_count = len(slip_match.group(1).split("|")) if slip_match else 0
    return [
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "field": "U",
            "role": "closed_loop_wall_default",
            "patch_count": "all unmatched patches",
            "patch_types": "noSlip",
            "imposed_Q_W_sum": "",
            "h_min_W_m2K": "",
            "h_max_W_m2K": "",
            "Ta_K_values": "",
            "Tsur_K_values": "",
            "emissivity_values": "",
            "thicknessLayers_m_values": "",
            "semantics": "No named inlet/outlet velocity boundary is present; default velocity boundary is noSlip.",
            "evidence_path": rel(spec["root"] / "0/U"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "field": "U",
            "role": "ncc_neighbor_velocity_connector",
            "patch_count": slip_count,
            "patch_types": "slip",
            "imposed_Q_W_sum": "",
            "h_min_W_m2K": "",
            "h_max_W_m2K": "",
            "Ta_K_values": "",
            "Tsur_K_values": "",
            "emissivity_values": "",
            "thicknessLayers_m_values": "",
            "semantics": "NCC neighbour patches use slip velocity coupling; these are internal closed-loop connectors, not inlet/outlet boundaries.",
            "evidence_path": rel(spec["root"] / "0/U"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "field": "p_rgh",
            "role": "closed_loop_pressure_default",
            "patch_count": "all patches",
            "patch_types": "fixedFluxPressure",
            "imposed_Q_W_sum": "",
            "h_min_W_m2K": "",
            "h_max_W_m2K": "",
            "Ta_K_values": "",
            "Tsur_K_values": "",
            "emissivity_values": "",
            "thicknessLayers_m_values": "",
            "semantics": "No inlet/outlet pressure boundary is present; all patches use fixedFluxPressure.",
            "evidence_path": rel(spec["root"] / "0/p_rgh"),
        },
    ]


def build_lineage_rows() -> list[dict[str, Any]]:
    val_import = load_json(VAL_IMPORT)
    jin_import = load_json(JIN_IMPORT)
    val_agg = load_json(VAL_AGG_MANIFEST)
    jin_agg = load_json(JIN_AGG_MANIFEST)
    registry = read_csv(CASE_REGISTRY)
    val_reg = next((r for r in registry if r.get("source_id") == "val_salt_test_2_coarse_mesh_laminar"), {})
    jin_reg = next((r for r in registry if r.get("source_id") == "viscosity_screening_salt_test_2_jin_coarse_mesh"), {})
    return [
        {
            "lineage_item": "canonical_display_label",
            "current_or_legacy_label": "val_salt_test_2_coarse_mesh",
            "path_or_value": "Use this display label in new human-facing documentation.",
            "migration_action": "Add display alias only. Do not rename historical directories or registry source_id.",
            "provenance_preservation": "Historical source_id remains val_salt_test_2_coarse_mesh_laminar; runtime folder remains val_salt_test_2_coarse_mesh_laminar_continuation.",
            "evidence_path": rel(VAL_IMPORT),
        },
        {
            "lineage_item": "original_external_source",
            "current_or_legacy_label": val_import.get("source_id", ""),
            "path_or_value": val_import.get("source_root", ""),
            "migration_action": "Preserve as source provenance.",
            "provenance_preservation": "This is the native external source path recorded at intake.",
            "evidence_path": rel(VAL_IMPORT),
        },
        {
            "lineage_item": "registered_case_registry_row",
            "current_or_legacy_label": val_reg.get("source_id", ""),
            "path_or_value": val_reg.get("source_root", ""),
            "migration_action": "Do not edit registry in this documentation task.",
            "provenance_preservation": "Registry records source_owner native_2d_cfd_external and registered timestamp.",
            "evidence_path": rel(CASE_REGISTRY),
        },
        {
            "lineage_item": "staged_continuation_runtime",
            "current_or_legacy_label": "val_salt_test_2_coarse_mesh_laminar_continuation",
            "path_or_value": str(VAL_CASE),
            "migration_action": "Display as val_salt_test_2_coarse_mesh when context is clear; cite full path when discussing solver provenance.",
            "provenance_preservation": "Continuation is a staged writable copy; source import remains read-only.",
            "evidence_path": rel(VAL_CAMPAIGN_README),
        },
        {
            "lineage_item": "registry_aggregate_runtime",
            "current_or_legacy_label": val_agg.get("source_id", ""),
            "path_or_value": val_agg.get("runtime_root", ""),
            "migration_action": "Keep aggregate path keyed by historical source_id.",
            "provenance_preservation": "Aggregation rows are not admission; they document available postprocessing.",
            "evidence_path": rel(VAL_AGG_MANIFEST),
        },
        {
            "lineage_item": "salt2_jin_comparator_source",
            "current_or_legacy_label": jin_import.get("source_id", ""),
            "path_or_value": jin_import.get("source_root", ""),
            "migration_action": "Keep separate from val display alias.",
            "provenance_preservation": "Salt2 Jin is a distinct modern Jin lineage.",
            "evidence_path": rel(JIN_IMPORT),
        },
        {
            "lineage_item": "salt2_jin_current_runtime",
            "current_or_legacy_label": "salt2_jin",
            "path_or_value": str(JIN_CASE),
            "migration_action": "Use as current mainline Salt2 Jin continuation evidence, not as a parent of val.",
            "provenance_preservation": "Jin continuation belongs to June 18 convergence/Jin envelope wave.",
            "evidence_path": rel(JIN_CAMPAIGN_README),
        },
        {
            "lineage_item": "salt2_jin_registry_row",
            "current_or_legacy_label": jin_reg.get("source_id", ""),
            "path_or_value": jin_reg.get("source_root", ""),
            "migration_action": "Do not collapse with val registry row.",
            "provenance_preservation": "Both rows share mesh group but differ in source family and fluid label.",
            "evidence_path": rel(CASE_REGISTRY),
        },
    ]


def material_rows_for(spec: dict[str, Any], cfg: dict[str, str]) -> list[dict[str, Any]]:
    physical = read_text(spec["root"] / "constant/physicalProperties")
    momentum = read_text(spec["root"] / "constant/momentumTransport")
    transport = read_text(spec["root"] / "constant/thermophysicalTransport")
    cp_match = re.search(r"CpCoeffs<8>\s+\(([^)]+)\)", physical)
    rho_match = re.search(r"rhoCoeffs<8>\s+\(([^)]+)\)", physical)
    thermo_match = re.search(r"thermoType\s*\{(.*?)\n\}", physical, flags=re.S)
    rows = [
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "case_config",
            "property_group": "fluid_label",
            "value": cfg.get("fluid", ""),
            "semantics": "Readable case-level fluid family label.",
            "evidence_path": rel(spec["root"] / "case_config.yaml"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "case_config",
            "property_group": "temperature_initial_condition",
            "value": cfg.get("T_init_K", ""),
            "semantics": "Initial internal field temperature used by the case setup.",
            "evidence_path": rel(spec["root"] / "case_config.yaml"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "thermoType",
            "value": compact_ws(thermo_match.group(1)) if thermo_match else "",
            "semantics": "OpenFOAM thermophysical model selection.",
            "evidence_path": rel(spec["root"] / "constant/physicalProperties"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "CpCoeffs",
            "value": cp_match.group(1) if cp_match else cfg.get("Cp_coeffs", ""),
            "semantics": "Constant sensible-enthalpy heat capacity polynomial; first coefficient is Cp.",
            "evidence_path": rel(spec["root"] / "constant/physicalProperties"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "rhoCoeffs",
            "value": rho_match.group(1) if rho_match else cfg.get("rho_coeffs", ""),
            "semantics": "Polynomial density relation; available coefficients support rho = 2293.6 - 0.7497*T.",
            "evidence_path": rel(spec["root"] / "constant/physicalProperties"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "mu",
            "value": f"{cfg.get('mu_model', '')}: {cfg.get('mu_coeffs', '')}",
            "semantics": "Case config records expInvT source coefficients; OpenFOAM uses the generated icoTabulated table.",
            "evidence_path": rel(spec["root"] / "case_config.yaml") + ";" + rel(spec["root"] / "constant/physicalProperties"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "kappa",
            "value": f"{cfg.get('kappa_model', '')}: {cfg.get('kappa_coeffs', '')}",
            "semantics": "Case config records polynomial conductivity source coefficients; OpenFOAM uses the generated icoTabulated table.",
            "evidence_path": rel(spec["root"] / "case_config.yaml") + ";" + rel(spec["root"] / "constant/physicalProperties"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "momentum_transport",
            "value": "laminar" if "simulationType  laminar" in momentum else "",
            "semantics": "No turbulence closure is active.",
            "evidence_path": rel(spec["root"] / "constant/momentumTransport"),
        },
        {
            "case_label": spec["case_label"],
            "source_id": spec["legacy_source_id"],
            "evidence_class": "OpenFOAM_dictionary",
            "property_group": "thermophysical_transport",
            "value": "Fourier" if "model           Fourier" in transport else "",
            "semantics": "Laminar conductive heat transport model.",
            "evidence_path": rel(spec["root"] / "constant/thermophysicalTransport"),
        },
    ]
    return rows


def compact_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def wall_heat_latest(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[-1] if rows else {}


def comparison_rows(configs: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    val_summary = first_row(VAL_CASE_SUMMARY)
    jin_summary = first_row(JIN_CASE_SUMMARY)
    val_direct = first_row(DIRECT_VALIDATION, "val_salt_test_2_coarse_mesh_laminar")
    jin_direct = first_row(DIRECT_VALIDATION, "viscosity_screening_salt_test_2_jin_coarse_mesh")
    val_paper = first_row(PAPER_CASE_INVENTORY, "val_salt_test_2_coarse_mesh_laminar")
    jin_paper = first_row(PAPER_CASE_INVENTORY, "viscosity_screening_salt_test_2_jin_coarse_mesh")
    steady = first_row(SUBMITTED_STEADY, "salt2_jin")
    flow_val = find_flow_row("salt2")
    flow_jin = find_flow_row("salt2_jin")
    triage = {r["comparison_axis"]: r for r in read_csv(TRIAGE_COMPARISON) if r.get("comparison_axis")}
    return [
        comp_row("canonical_display_label", "salt2_jin", "val_salt_test_2_coarse_mesh", "Use user-requested val display label in new reports; preserve val_salt_test_2_coarse_mesh_laminar source_id and continuation path."),
        comp_row("lineage", triage.get("lineage", {}).get("salt2_jin", "Modern Jin Salt2 continuation."), triage.get("lineage", {}).get("salt2_val", "Continuation of older external/native val_salt_test_2_coarse_mesh_laminar source."), "Distinct lineages; do not collapse val into salt2_jin."),
        comp_row("source_owner", "ethan_modern_runs_staged", "native_2d_cfd_external", "Different intake families and owners in registry/import manifests."),
        comp_row("fluid_label", configs["salt2_jin"].get("fluid", ""), configs["val_salt_test_2_coarse_mesh"].get("fluid", ""), "Jin uses hitec_salt_jin; val uses hitec_salt with otherwise similar coefficient evidence."),
        comp_row("T_init_K", configs["salt2_jin"].get("T_init_K", ""), configs["val_salt_test_2_coarse_mesh"].get("T_init_K", ""), "Val starts 4.5 K warmer in case_config."),
        comp_row("mesh_group_id", configs["salt2_jin"].get("mesh_group_id", ""), configs["val_salt_test_2_coarse_mesh"].get("mesh_group_id", ""), "Same mesh group id; mesh sameness does not imply lineage sameness."),
        comp_row("heater_and_test_section_inputs_W", "heater 265.7 plus test-section 37", "heater 265.7 plus test-section 37", "Both use three 88.5666667 W heater patches and one 37 W test-section patch."),
        comp_row("cooler_fixed_Q_W", "-136.350740 total across upper reducer/cooler/reducer", "-136.350740 total across upper reducer/cooler/reducer", "Both impose the same fixed cooler branch Q in 0/T; metadata cooler h differs and is not the live cooler Q knob."),
        comp_row("insulation_layer_difference", "0.03556 m outer insulation layer on many Jin ambient walls", "0.04191 m outer insulation layer on many val ambient walls", "Boundary dictionaries show different insulation thicknesses; this is a physical BC difference."),
        comp_row("metadata_cooler_h_W_m2K", configs["salt2_jin"].get("cooler_h_metadata", ""), configs["val_salt_test_2_coarse_mesh"].get("cooler_h_metadata", ""), "Recorded metadata differs, but 0/T cooler patches are fixed-Q externalTemperature."),
        comp_row("mdot_consensus_kg_s_registry", jin_summary.get("mdot_consensus_kg_s", ""), val_summary.get("mdot_consensus_kg_s", ""), "Registry aggregate mdot values show val has the higher available mdot."),
        comp_row("latest_total_Q_postProc_W_registry", jin_summary.get("latest_total_Q_postProc_w", ""), val_summary.get("latest_total_Q_postProc_w", ""), "Both aggregates have small residual total_Q values; this is diagnostic, not admission by itself."),
        comp_row("direct_validation_run_status", jin_direct.get("run_status", ""), val_direct.get("run_status", ""), "June 4 direct validation saw Jin terminated and val running; later docs still treat val as diagnostic/context."),
        comp_row("current_steady_status", steady.get("steady_state_detection_status", ""), flow_val.get("steady_state_detection_status", ""), "Salt2 Jin is hydraulic-stationary with thermal heat-drift caveat in the current steady table. Val appears as diagnostic context with mixed drift/steady evidence in the flow/BC study."),
        comp_row("admission_or_use", steady.get("admission_overlay", ""), val_paper.get("paper_class", "blocked"), "Salt2 Jin is current mainline nominal evidence; val is blocked/diagnostic until re-admitted."),
        comp_row("possible_uses", "current Salt2 mainline comparison/training anchor with thermal drift caveat", "historical/diagnostic validation-coarse-mesh context, BC/property comparison, migration-label target; not training without admission", "Use val to document provenance and compare setup, not to silently expand fit data."),
        comp_row("paper_inventory_class", jin_paper.get("paper_class", ""), val_paper.get("paper_class", ""), "June 29 inventory classifies Salt2 Jin as paper-grade and Salt2 Val as blocked."),
        comp_row("registry_postprocessing_paths", rel(JIN_CASE_SUMMARY), rel(VAL_CASE_SUMMARY), "Both have registry aggregates; aggregation is not admission."),
    ]


def comp_row(axis: str, jin: Any, val: Any, interpretation: str) -> dict[str, Any]:
    return {
        "comparison_axis": axis,
        "salt2_jin": jin,
        "val_salt_test_2_coarse_mesh": val,
        "interpretation": interpretation,
    }


def find_flow_row(key: str) -> dict[str, str]:
    for row in read_csv(FLOW_BC_MATRIX):
        if row.get("case_key") == key:
            return row
    return {}


def source_manifest_rows(outputs: list[str]) -> list[dict[str, Any]]:
    inputs = [
        (VAL_IMPORT, "input", "Val original intake manifest."),
        (VAL_CAMPAIGN_README, "input", "Val continuation rationale and source path."),
        (VAL_CASE / "case_config.yaml", "input", "Val setup metadata."),
        (VAL_CASE / "0/T", "input", "Val thermal boundary dictionary."),
        (VAL_CASE / "0/U", "input", "Val velocity boundary dictionary."),
        (VAL_CASE / "0/p_rgh", "input", "Val pressure boundary dictionary."),
        (VAL_CASE / "constant/physicalProperties", "input", "Val material model dictionary."),
        (VAL_CASE_SUMMARY, "input", "Val registry case aggregate."),
        (VAL_WALL_HEAT, "input", "Val registry wall heat aggregate."),
        (JIN_IMPORT, "input", "Salt2 Jin intake manifest."),
        (JIN_CAMPAIGN_README, "input", "Salt2 Jin continuation wave context."),
        (JIN_CASE / "case_config.yaml", "input", "Salt2 Jin setup metadata."),
        (JIN_CASE / "0/T", "input", "Salt2 Jin thermal boundary dictionary."),
        (JIN_CASE / "0/U", "input", "Salt2 Jin velocity boundary dictionary."),
        (JIN_CASE / "0/p_rgh", "input", "Salt2 Jin pressure boundary dictionary."),
        (JIN_CASE / "constant/physicalProperties", "input", "Salt2 Jin material model dictionary."),
        (JIN_CASE_SUMMARY, "input", "Salt2 Jin registry case aggregate."),
        (JIN_WALL_HEAT, "input", "Salt2 Jin registry wall heat aggregate."),
        (CASE_REGISTRY, "input", "Global case registration state, read only."),
        (DIRECT_VALIDATION, "input", "June 4 direct validation metrics."),
        (PAPER_CASE_INVENTORY, "input", "June 29 paper/admission inventory."),
        (SUBMITTED_STEADY, "input", "July 14 steady/admission table."),
        (FLOW_BC_MATRIX, "input", "July 14 flow/BC response rows."),
        (FLOW_BC_SEMANTICS, "input", "Radiation and BC semantics."),
        (FLOW_PATCH_ROLES, "input", "Patch role reductions for Salt2 Jin."),
        (TRIAGE_COMPARISON, "input", "Existing Salt2 Jin versus val comparison."),
        (THERMAL_BOUNDARY_MAP, "input", "Current radiation/rcExternalTemperature map."),
    ]
    rows = []
    for path, kind, note in inputs:
        rows.append(
            {
                "path": rel(path),
                "kind": kind,
                "exists": "yes" if path.exists() else "no",
                "read_or_write": "read-only",
                "notes": note,
            }
        )
    for output in outputs:
        rows.append(
            {
                "path": output,
                "kind": "output",
                "exists": "yes",
                "read_or_write": "written_by_builder",
                "notes": "AGENT-354 documentation artifact.",
            }
        )
    return rows


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(VAL_IMPORT)}
  - {rel(VAL_CAMPAIGN_README)}
  - {rel(VAL_CASE / 'case_config.yaml')}
  - {rel(VAL_CASE / '0/T')}
  - {rel(JIN_CASE / 'case_config.yaml')}
  - {rel(JIN_CASE / '0/T')}
  - {rel(SUBMITTED_STEADY)}
  - {rel(FLOW_BC_MATRIX)}
tags: [cfd-pp, salt2, boundary-conditions, provenance, rcExternalTemperature]
related:
  - {rel(THERMAL_BOUNDARY_MAP)}
  - {rel(TRIAGE_COMPARISON)}
task: {TASK}
date: {DATE}
role: Writer/Implementer
type: work_product
status: complete
---
# val_salt_test_2_coarse_mesh Documentation Package

## Purpose

This package documents `val_salt_test_2_coarse_mesh`, the requested canonical
display label for the existing `2026-06-01_continuation_candidate` /
`val_salt_test_2_coarse_mesh_laminar` lineage. It does not rename directories,
edit registry state, mutate native CFD outputs, or write external
`../cfd-modeling-tools` files.

## Main Findings

- Display migration: use `val_salt_test_2_coarse_mesh` in new prose and tables,
  while preserving `val_salt_test_2_coarse_mesh_laminar` as the historical
  `source_id` and
  `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation`
  as the continuation provenance path.
- The val lineage is distinct from `salt2_jin`; it is not a mislabeled Jin
  continuation. Salt2 Jin remains the current mainline Salt2 comparison row.
- Both cases are closed-loop OpenFOAM cases: no inlet/outlet patch was found in
  `0/U` or `0/p_rgh`; velocity is default `noSlip` with NCC connector `slip`,
  and pressure is `fixedFluxPressure`.
- Thermal BCs use lower-leg heater patches, a separate powered test-section
  patch, fixed-Q upper cooler/reducer patches, and passive wall/stub exchange.
- `rcExternalTemperature` carries `Ta`, `Tsur`, `emissivity`, wall-layer
  coefficients, and optional `Q`. Current repo guidance says radiation is folded
  into total `wallHeatFlux`; no separate exported `qr` term is available.
- Material evidence is available from `case_config.yaml` and
  `constant/physicalProperties`: laminar Hitec salt family, `heRhoThermo`,
  `icoTabulated` transport, `hPolynomial` Cp, `icoPolynomial` density,
  `momentumTransport` laminar, and Fourier laminar thermal transport.
- Salt2 Jin is current mainline nominal evidence with hydraulic-stationary /
  heat-drifting caveat. Val is historical/diagnostic or blocked context unless a
  future row explicitly re-admits it.

## Files

- `lineage_migration_plan.csv`: display-label migration and provenance path plan.
- `boundary_condition_summary.csv`: grouped thermal, velocity, pressure, and
  inlet/outlet boundary facts.
- `boundary_condition_patch_detail.csv`: patch-level thermal BC extraction from
  `0/T`.
- `material_property_evidence.csv`: fluid, property, transport, and material
  evidence.
- `salt2_jin_comparison.csv`: comparison report versus current Salt2 Jin.
- `source_manifest.csv`: exact read-only inputs and generated outputs.
- `summary.json`: machine-readable package summary.

## Counts

- Boundary summary rows: `{summary["boundary_summary_rows"]}`
- Patch detail rows: `{summary["boundary_patch_detail_rows"]}`
- Material/property rows: `{summary["material_property_rows"]}`
- Comparison rows: `{summary["comparison_rows"]}`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)

    configs = {spec["case_label"]: parse_case_config(spec["root"] / "case_config.yaml") for spec in CASE_SPECS}

    boundary_summary: list[dict[str, Any]] = []
    patch_detail: list[dict[str, str]] = []
    materials: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        thermal_summary, thermal_detail = summarize_temperature_boundaries(spec)
        boundary_summary.extend(thermal_summary)
        boundary_summary.extend(motion_boundary_rows(spec))
        patch_detail.extend(thermal_detail)
        materials.extend(material_rows_for(spec, configs[spec["case_label"]]))

    lineage = build_lineage_rows()
    comparison = comparison_rows(configs)

    outputs = [
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/lineage_migration_plan.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/boundary_condition_summary.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/boundary_condition_patch_detail.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/material_property_evidence.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/salt2_jin_comparison.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/source_manifest.csv",
        "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/summary.json",
    ]

    write_csv(
        out / "lineage_migration_plan.csv",
        lineage,
        ["lineage_item", "current_or_legacy_label", "path_or_value", "migration_action", "provenance_preservation", "evidence_path"],
    )
    write_csv(
        out / "boundary_condition_summary.csv",
        boundary_summary,
        [
            "case_label",
            "source_id",
            "field",
            "role",
            "patch_count",
            "patch_types",
            "imposed_Q_W_sum",
            "h_min_W_m2K",
            "h_max_W_m2K",
            "Ta_K_values",
            "Tsur_K_values",
            "emissivity_values",
            "thicknessLayers_m_values",
            "semantics",
            "evidence_path",
        ],
    )
    write_csv(
        out / "boundary_condition_patch_detail.csv",
        patch_detail,
        [
            "case_label",
            "source_id",
            "field",
            "patch",
            "role",
            "patch_type",
            "Q_W",
            "h_W_m2K",
            "Ta_K",
            "Tsur_K",
            "emissivity",
            "thicknessLayers_m",
            "semantics",
            "evidence_path",
        ],
    )
    write_csv(
        out / "material_property_evidence.csv",
        materials,
        ["case_label", "source_id", "evidence_class", "property_group", "value", "semantics", "evidence_path"],
    )
    write_csv(
        out / "salt2_jin_comparison.csv",
        comparison,
        ["comparison_axis", "salt2_jin", "val_salt_test_2_coarse_mesh", "interpretation"],
    )
    write_csv(
        out / "source_manifest.csv",
        source_manifest_rows(outputs),
        ["path", "kind", "exists", "read_or_write", "notes"],
    )

    summary = {
        "task": TASK,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "canonical_display_label": "val_salt_test_2_coarse_mesh",
        "legacy_source_id": "val_salt_test_2_coarse_mesh_laminar",
        "runtime_lineage": rel(VAL_CASE),
        "salt2_jin_comparator": rel(JIN_CASE),
        "boundary_summary_rows": len(boundary_summary),
        "boundary_patch_detail_rows": len(patch_detail),
        "material_property_rows": len(materials),
        "comparison_rows": len(comparison),
        "native_cfd_outputs_mutated": False,
        "registry_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "admission_conclusion": "val_salt_test_2_coarse_mesh is historical/diagnostic until explicitly re-admitted; salt2_jin remains current mainline nominal evidence with thermal-drift caveat.",
        "outputs": outputs,
    }
    write_json(out / "summary.json", summary)
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
