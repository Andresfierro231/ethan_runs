#!/usr/bin/env python3
"""Build a physical-interface follow-up to the July 8 patchwise heat ledger."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXTRACT_DIR = ROOT / "tools/extract"
if str(EXTRACT_DIR) not in sys.path:
    sys.path.insert(0, str(EXTRACT_DIR))

import sample_physical_segment_interface_temperatures as interfaces

FOUNDATION_DIR = ROOT / "work_products/2026-07-08_patchwise_heat_ledger"
FOUNDATION_CSV = FOUNDATION_DIR / "patchwise_heat_ledger.csv"
OUT = ROOT / "work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"
CP_JIN_JKGK = 1423.47

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
    "physical_interface_inlet",
    "physical_interface_outlet",
    "physical_interface_bracket_status",
    "interface_temperature_source",
    "interface_temperature_selection_rule",
    "max_interface_recirc_ratio",
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

SEGMENT_FIELDS = [
    "source_id",
    "case_id",
    "physical_segment",
    "component_spans",
    "inlet_interface",
    "outlet_interface",
    "bracket_status",
    "T_bulk_inlet_K",
    "T_bulk_outlet_K",
    "delta_T_K",
    "mdot_kg_s",
    "cp_jkgk",
    "enthalpy_change_W",
    "segment_wallHeatFlux_sum_W",
    "wallHeatFlux_vs_enthalpy_residual_W",
    "residual_fraction",
    "enthalpy_change_status",
    "residual_assignment",
    "max_interface_recirc_ratio",
    "temperature_selection_rule",
    "quality_flags",
    "source_files",
]

NETWORK_FIELDS = [
    "source_id",
    "case_id",
    "patch_group",
    "span",
    "patch_names",
    "wallHeatFlux_integral_W",
    "internal_convection_resistance_m2K_W",
    "wall_conduction_resistance_m2K_W",
    "external_convection_resistance_m2K_W",
    "external_radiation_resistance_m2K_W",
    "total_boundary_resistance_m2K_W",
    "network_terms_resolved",
    "radiation_output_term",
    "radiation_present",
    "radiation_caveat",
    "unresolved_network_terms",
]

SOURCE_FIELDS = [
    "source_id",
    "case_id",
    "foundation_ledger",
    "source_case_root",
    "source_window_start_s",
    "source_window_end_s",
    "wallheatflux_source_path",
    "wallheatflux_sample_time_s",
    "interface_temperature_source",
    "radiation_present",
    "quality_flags",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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
    if not math.isfinite(parsed):
        return None
    return parsed


def fmt(value: Any, digits: int = 6) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def sample_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row["source_id"], row["component_span"], row["interface_role"])


def source_segment_wall_flux(rows: list[dict[str, str]]) -> dict[tuple[str, str], float]:
    sums: dict[tuple[str, str], float] = defaultdict(float)
    for row in rows:
        value = safe_float(row.get("wallHeatFlux_integral_W")) or 0.0
        sums[(row["source_id"], row["span"])] += value
    return sums


def mdot_by_source(rows: list[dict[str, str]]) -> dict[str, float]:
    mdot: dict[str, float] = {}
    for row in rows:
        parsed = safe_float(row.get("mdot_kg_s"))
        if parsed is not None:
            mdot.setdefault(row["source_id"], parsed)
    return mdot


def row_source_paths(*rows: dict[str, str] | None) -> str:
    paths: list[str] = []
    for row in rows:
        if not row:
            continue
        plane = row.get("plane_file", "")
        if plane:
            paths.append(plane)
    return ";".join(paths)


def build_segment_residuals(
    foundation_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
    sample_rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, Any]]:
    samples = {sample_key(row): row for row in sample_rows}
    segment_q = source_segment_wall_flux(foundation_rows)
    mdot_lookup = mdot_by_source(foundation_rows)
    results: dict[tuple[str, str], dict[str, Any]] = {}
    registry_by_segment = {(row["source_id"], row["physical_segment"]): row for row in registry_rows}
    for (source_id, physical_segment), registry in registry_by_segment.items():
        case_id = registry["case_id"]
        mdot = mdot_lookup.get(source_id)
        component_spans = [span for span in registry.get("component_spans", "").split("+") if span]
        segment_wall_q = segment_q.get((source_id, physical_segment), 0.0)
        if physical_segment == "junction":
            results[(source_id, physical_segment)] = {
                **registry,
                "segment_wallHeatFlux_sum_W": fmt(segment_wall_q),
                "mdot_kg_s": fmt(mdot),
                "cp_jkgk": CP_JIN_JKGK,
                "enthalpy_change_status": "not_bracketed_by_physical_segment_interfaces",
                "residual_assignment": "junction_loss_reported_as_wall_flux_not_segment_enthalpy",
                "quality_flags": "junction_grouped_mixed_bc;not_bracketed_by_available_interfaces",
            }
            continue
        deltas: list[float] = []
        recircs: list[float] = []
        source_files: list[str] = []
        status_flags: list[str] = []
        for span in component_spans:
            inlet = samples.get((source_id, span, "raw_span_inlet"))
            outlet = samples.get((source_id, span, "raw_span_outlet"))
            t_in = safe_float(inlet.get("T_used_K") if inlet else None)
            t_out = safe_float(outlet.get("T_used_K") if outlet else None)
            if t_in is None or t_out is None:
                status_flags.append(f"missing_temperature:{span}")
                continue
            deltas.append(t_out - t_in)
            for sample in (inlet, outlet):
                if sample and sample.get("plane_file"):
                    source_files.append(sample["plane_file"])
                recirc = safe_float(sample.get("recirculation_ratio") if sample else None)
                if recirc is not None:
                    recircs.append(recirc)
                qflags = sample.get("quality_flags", "") if sample else ""
                if qflags:
                    status_flags.extend(flag for flag in qflags.split(";") if flag)
        inlet_span, inlet_station = registry["inlet_interface"].split(":")
        outlet_span, outlet_station = registry["outlet_interface"].split(":")
        inlet_row = samples.get((source_id, inlet_span, "raw_span_inlet"))
        if inlet_row is None or inlet_row.get("station_label") != inlet_station:
            inlet_row = samples.get((source_id, physical_segment, "physical_segment_inlet"))
        outlet_row = samples.get((source_id, outlet_span, "raw_span_outlet"))
        if outlet_row is None or outlet_row.get("station_label") != outlet_station:
            outlet_row = samples.get((source_id, physical_segment, "physical_segment_outlet"))
        t_in_segment = safe_float(inlet_row.get("T_used_K") if inlet_row else None)
        t_out_segment = safe_float(outlet_row.get("T_used_K") if outlet_row else None)
        delta_t = sum(deltas) if deltas and len(deltas) == len(component_spans) else None
        enthalpy = mdot * CP_JIN_JKGK * delta_t if mdot is not None and delta_t is not None else None
        residual = segment_wall_q - enthalpy if enthalpy is not None else None
        residual_fraction = residual / abs(enthalpy) if enthalpy not in {None, 0.0} else None
        max_recirc = max(recircs) if recircs else None
        if physical_segment == "cooling_branch":
            enthalpy_status = "computed_from_physical_interfaces_partial_cooler_bracket"
            status_flags.append("cooler_not_fully_bracketed_by_available_surfaces")
        elif physical_segment == "upcomer":
            enthalpy_status = "computed_diagnostic_only_high_recirculation_interfaces"
            status_flags.append("recirculation_cell_diagnostic_only")
        elif max_recirc is not None and max_recirc > 0.5:
            enthalpy_status = "computed_from_physical_interfaces_high_recirculation_flag"
        elif enthalpy is not None:
            enthalpy_status = "computed_from_physical_segment_interfaces"
        else:
            enthalpy_status = "missing_physical_interface_temperature"
        if max_recirc is not None and max_recirc > 0.5:
            status_flags.append("high_recirculation_interface_temperature")
        residual_assignment = (
            "diagnostic_only_upcomer_recirculation_cell"
            if physical_segment == "upcomer"
            else "segment_wall_flux_minus_physical_interface_enthalpy_change"
        )
        results[(source_id, physical_segment)] = {
            **registry,
            "T_bulk_inlet_K": fmt(t_in_segment),
            "T_bulk_outlet_K": fmt(t_out_segment),
            "delta_T_K": fmt(delta_t),
            "mdot_kg_s": fmt(mdot),
            "cp_jkgk": CP_JIN_JKGK,
            "enthalpy_change_W": fmt(enthalpy),
            "segment_wallHeatFlux_sum_W": fmt(segment_wall_q),
            "wallHeatFlux_vs_enthalpy_residual_W": fmt(residual),
            "residual_fraction": fmt(residual_fraction),
            "enthalpy_change_status": enthalpy_status,
            "residual_assignment": residual_assignment,
            "max_interface_recirc_ratio": fmt(max_recirc),
            "temperature_selection_rule": "forward_bulk_when_recirc_gt_0p5_else_mixing_cup",
            "quality_flags": ";".join(sorted(set(status_flags))),
            "source_files": ";".join(sorted(set(source_files))),
        }
    return results


def append_quality(existing: str, *flags: str) -> str:
    values = [flag for flag in existing.split(";") if flag]
    values.extend(flag for flag in flags if flag)
    return ";".join(sorted(set(values)))


def enhance_patchwise_rows(
    foundation_rows: list[dict[str, str]],
    segment_rows: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    enhanced: list[dict[str, Any]] = []
    for row in foundation_rows:
        out: dict[str, Any] = dict(row)
        segment = segment_rows.get((row["source_id"], row["span"]))
        if segment:
            out["T_bulk_inlet_K"] = segment.get("T_bulk_inlet_K", "")
            out["T_bulk_outlet_K"] = segment.get("T_bulk_outlet_K", "")
            if out.get("T_bulk_inlet_K") and out.get("T_bulk_outlet_K"):
                tin = safe_float(out["T_bulk_inlet_K"])
                tout = safe_float(out["T_bulk_outlet_K"])
                out["T_bulk_span_K"] = fmt(0.5 * (tin + tout) if tin is not None and tout is not None else None)
            out["enthalpy_change_W"] = segment.get("enthalpy_change_W", "")
            out["enthalpy_change_status"] = segment.get("enthalpy_change_status", "")
            out["segment_wallHeatFlux_sum_W"] = segment.get("segment_wallHeatFlux_sum_W", "")
            out["segment_enthalpy_source"] = rel(OUT / "segment_enthalpy_residuals.csv")
            out["wallHeatFlux_vs_enthalpy_residual_W"] = segment.get("wallHeatFlux_vs_enthalpy_residual_W", "")
            out["residual_fraction"] = segment.get("residual_fraction", "")
            out["residual_assignment"] = segment.get("residual_assignment", "")
            out["physical_interface_inlet"] = segment.get("inlet_interface", "")
            out["physical_interface_outlet"] = segment.get("outlet_interface", "")
            out["physical_interface_bracket_status"] = segment.get("bracket_status", "")
            out["interface_temperature_source"] = rel(OUT / "interface_temperature_samples.csv")
            out["interface_temperature_selection_rule"] = segment.get("temperature_selection_rule", "")
            out["max_interface_recirc_ratio"] = segment.get("max_interface_recirc_ratio", "")
            out["quality_flags"] = append_quality(
                row.get("quality_flags", ""),
                "physical_interface_enthalpy_followup",
                *[flag for flag in segment.get("quality_flags", "").split(";") if flag],
            )
            if row["span"] == "junction":
                out["segment_enthalpy_source"] = ""
                out["fit_eligible"] = "no"
                out["fit_use_status"] = "not_fit_unbracketed_junction"
        unresolved = []
        if not out.get("internal_convection_resistance_m2K_W"):
            unresolved.append("internal_convection_missing_or_singular")
        if not out.get("wall_conduction_resistance_m2K_W"):
            unresolved.append("wall_conduction_missing")
        if not out.get("external_convection_resistance_m2K_W"):
            unresolved.append("external_convection_missing")
        if out.get("external_radiation_resistance_m2K_W") == "absent_no_qr_output":
            unresolved.append("radiation_absent_no_qr_output")
        out["notes"] = row.get("notes", "")
        if unresolved:
            out["notes"] = (out["notes"] + "; " if out["notes"] else "") + "unresolved_network_terms=" + "|".join(unresolved)
        enhanced.append(out)
    return enhanced


def build_network_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    network_rows: list[dict[str, Any]] = []
    for row in rows:
        unresolved = []
        for field, label in [
            ("internal_convection_resistance_m2K_W", "internal_convection"),
            ("wall_conduction_resistance_m2K_W", "wall_conduction"),
            ("external_convection_resistance_m2K_W", "external_convection"),
        ]:
            if not row.get(field):
                unresolved.append(label)
        if row.get("external_radiation_resistance_m2K_W") == "absent_no_qr_output":
            unresolved.append("radiation_absent_no_qr_output")
        network_rows.append({**row, "unresolved_network_terms": ";".join(unresolved)})
    return network_rows


def build_source_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[str, dict[str, Any]] = {}
    for row in rows:
        by_source.setdefault(
            row["source_id"],
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "foundation_ledger": rel(FOUNDATION_CSV),
                "source_case_root": row["source_case_root"],
                "source_window_start_s": row["source_window_start_s"],
                "source_window_end_s": row["source_window_end_s"],
                "wallheatflux_source_path": row["wallheatflux_source_path"],
                "wallheatflux_sample_time_s": row["wallheatflux_sample_time_s"],
                "interface_temperature_source": rel(OUT / "interface_temperature_samples.csv"),
                "radiation_present": row["radiation_present"],
                "quality_flags": "",
            },
        )
        by_source[row["source_id"]]["quality_flags"] = append_quality(
            by_source[row["source_id"]]["quality_flags"],
            *[flag for flag in row.get("quality_flags", "").split(";") if flag],
        )
    return [by_source[key] for key in sorted(by_source)]


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    required = [
        "source_id",
        "case_id",
        "patch_group",
        "span",
        "wallHeatFlux_integral_W",
        "heat_to_fluid_W",
        "wall_flux_sign_convention",
        "enthalpy_change_status",
        "residual_assignment",
        "radiation_caveat",
        "quality_flags",
    ]
    for row in rows:
        row_id = f"{row.get('source_id')}:{row.get('span')}:{row.get('patch_group')}"
        for field in required:
            if str(row.get(field, "")).strip() == "":
                errors.append(f"{row_id}: missing {field}")
        if row.get("wall_flux_sign_convention") != "positive_into_fluid_negative_out_of_fluid":
            errors.append(f"{row_id}: bad wall flux sign convention")
        if row.get("span") != "junction":
            for field in (
                "T_bulk_inlet_K",
                "T_bulk_outlet_K",
                "enthalpy_change_W",
                "segment_wallHeatFlux_sum_W",
                "wallHeatFlux_vs_enthalpy_residual_W",
                "physical_interface_inlet",
                "physical_interface_outlet",
                "interface_temperature_source",
            ):
                if str(row.get(field, "")).strip() == "":
                    errors.append(f"{row_id}: missing {field}")
        else:
            if str(row.get("enthalpy_change_W", "")).strip() != "":
                errors.append(f"{row_id}: junction enthalpy should stay blank")
        if row.get("radiation_present") in {"False", "false", False}:
            if row.get("external_radiation_resistance_m2K_W") != "absent_no_qr_output":
                errors.append(f"{row_id}: no-qr radiation row missing absence marker")
            if "radiation_absent_no_qr_output" not in row.get("network_terms_resolved", ""):
                errors.append(f"{row_id}: no-qr radiation not recorded in network terms")
    return errors


def write_readme(rows: list[dict[str, Any]], segment_rows: list[dict[str, Any]], errors: list[str]) -> None:
    segments_by_status = Counter(row.get("enthalpy_change_status", "") for row in segment_rows)
    max_residual = max(
        [abs(safe_float(row.get("wallHeatFlux_vs_enthalpy_residual_W")) or 0.0) for row in segment_rows],
        default=0.0,
    )
    text = f"""# Patchwise Heat Ledger With Physical Interface Enthalpy

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

Follow-up package for `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER`. This package keeps
`{rel(FOUNDATION_DIR)}/` read-only and writes a new enthalpy/residual layer based
on explicit physical segment interfaces sampled from existing `secmeanSurfaces`
XY planes.

## Contract

- Positive `wallHeatFlux_integral_W` and `heat_to_fluid_W` mean heat enters the
  fluid; negative values mean heat leaves the fluid.
- `enthalpy_change_W = mdot * cp * (T_out - T_in)` with Jin salt
  `cp = {CP_JIN_JKGK} J/kg/K`.
- Interface temperatures use mixing-cup bulk temperature unless recirculation
  ratio exceeds `0.5`; high-recirculation interfaces use forward-flow bulk
  temperature and are diagnostic only.
- Junction rows remain unbracketed because no single inlet/outlet interface pair
  encloses the grouped junction patches.
- Radiation is a heat-ledger term only when OpenFOAM exposes `qr`. These rows
  retain the July 8 no-`qr` status and do not infer radiation from emissivity
  metadata alone.

## Outputs

- `interface_registry.csv`
- `interface_temperature_samples.csv`
- `segment_enthalpy_residuals.csv`
- `patchwise_heat_ledger_enthalpy_interfaces.csv`
- `patchwise_heat_ledger_enthalpy_interfaces.json`
- `resistance_network_terms.csv`
- `source_inventory.csv`
- `summary.json`
- `README.md`

## Counts

- Patchwise rows: `{len(rows)}`
- Segment residual rows: `{len(segment_rows)}`
- Validation errors: `{len(errors)}`
- Segment statuses: `{dict(segments_by_status)}`
- Max absolute segment residual: `{max_residual:.3f} W`

## Interpretation

This package improves the July 8 foundation by making the control-volume
interfaces explicit. It does not magically make every heat row fit-ready:
cooler rows are still only partially bracketed by available upper-leg cut
planes, upcomer rows remain recirculation-cell diagnostics, and junction rows
remain wall-flux-only until dedicated junction-bracketing surfaces exist.

## Validation Errors

```json
{json.dumps(errors, indent=2)}
```
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    global OUT
    OUT = output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    foundation_hash_before = sha256(FOUNDATION_CSV)
    interface_summary = interfaces.build_package(output_dir=output_dir)
    foundation_rows = read_csv(FOUNDATION_CSV)
    registry_rows = read_csv(output_dir / "interface_registry.csv")
    sample_rows = read_csv(output_dir / "interface_temperature_samples.csv")
    segment_map = build_segment_residuals(foundation_rows, registry_rows, sample_rows)
    segment_rows = [segment_map[key] for key in sorted(segment_map)]
    enhanced_rows = enhance_patchwise_rows(foundation_rows, segment_map)
    network_rows = build_network_rows(enhanced_rows)
    inventory_rows = build_source_inventory(enhanced_rows)
    errors = validate_rows(enhanced_rows)
    write_csv(output_dir / "segment_enthalpy_residuals.csv", segment_rows, SEGMENT_FIELDS)
    write_csv(output_dir / "patchwise_heat_ledger_enthalpy_interfaces.csv", enhanced_rows, FIELDS)
    with (output_dir / "patchwise_heat_ledger_enthalpy_interfaces.json").open("w", encoding="utf-8") as handle:
        json.dump(enhanced_rows, handle, indent=2)
    write_csv(output_dir / "resistance_network_terms.csv", network_rows, NETWORK_FIELDS)
    write_csv(output_dir / "source_inventory.csv", inventory_rows, SOURCE_FIELDS)
    foundation_hash_after = sha256(FOUNDATION_CSV)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "script": rel(Path(__file__)),
        "foundation_ledger": rel(FOUNDATION_CSV),
        "foundation_sha256_before": foundation_hash_before,
        "foundation_sha256_after": foundation_hash_after,
        "foundation_unchanged": foundation_hash_before == foundation_hash_after,
        "interface_summary": interface_summary,
        "counts": {
            "patchwise_rows": len(enhanced_rows),
            "segment_rows": len(segment_rows),
            "network_rows": len(network_rows),
            "source_inventory_rows": len(inventory_rows),
            "validation_errors": len(errors),
        },
        "validation_errors": errors,
        "outputs": {
            "interface_registry": rel(output_dir / "interface_registry.csv"),
            "interface_temperature_samples": rel(output_dir / "interface_temperature_samples.csv"),
            "segment_enthalpy_residuals": rel(output_dir / "segment_enthalpy_residuals.csv"),
            "patchwise_heat_ledger_enthalpy_interfaces": rel(output_dir / "patchwise_heat_ledger_enthalpy_interfaces.csv"),
            "resistance_network_terms": rel(output_dir / "resistance_network_terms.csv"),
            "source_inventory": rel(output_dir / "source_inventory.csv"),
        },
        "limitations": [
            "No native solver output was modified.",
            "No new OpenFOAM sampling was run; existing secmeanSurfaces are reused.",
            "Cooler and heater interiors are not separately bracketed by the available interface planes.",
            "Junction rows are not physically bracketed.",
            "High-recirculation interface temperatures are diagnostic and not fit targets.",
        ],
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    write_readme(enhanced_rows, segment_rows, errors)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(OUT))
    args = parser.parse_args()
    summary = build_package(Path(args.output_dir))
    print(json.dumps(summary["counts"], indent=2))
    if summary["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
