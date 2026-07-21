#!/usr/bin/env python3
"""Build a patch-level CFD thermal boundary role table for Salt 2/3/4.

This is the AGENT-263 patch-grain companion to the grouped July 8 patchwise
heat ledger.  It reads OpenFOAM dictionaries and existing wallHeatFlux outputs
only; it does not reconstruct fields or mutate solver outputs.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_heat_source_sink_ledger import CASES, PATCH_MAP, find_latest_wallheatflux_dat
from tools.case_analysis_profiles import get_case_analysis_profile

OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table"
JULY8_GROUPED_LEDGER = (
    ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv"
)
INTERFACE_REGISTRY = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/interface_registry.csv"
)

PATCH_FIELDS = [
    "source_id",
    "case_id",
    "run_class",
    "case_root",
    "patch_name",
    "role",
    "role_group",
    "bc_type",
    "parent_span",
    "one_d_segment",
    "one_d_segment_mapping_status",
    "area_m2",
    "h_W_m2K",
    "Ta_K",
    "Tsur_K",
    "emissivity",
    "thicknessLayers",
    "thickness_total_m",
    "kappaLayerCoeffs",
    "wall_layer_metadata_status",
    "imposed_Q_W",
    "realized_wallHeatFlux_W",
    "realized_wallHeatFlux_mean_W_m2",
    "wallHeatFlux_source_path",
    "wallHeatFlux_sample_time_s",
    "boundary_dictionary_path",
    "radiation_metadata_status",
    "fit_use_status",
    "notes",
]

SUMMARY_FIELDS = [
    "source_id",
    "case_id",
    "role",
    "role_group",
    "patch_count",
    "area_m2",
    "imposed_Q_W",
    "realized_wallHeatFlux_W",
    "rcExternalTemperature_count",
    "externalTemperature_count",
    "zeroGradient_count",
]

SEGMENT_FIELDS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "component_parent_spans",
    "patch_count",
    "area_m2",
    "realized_wallHeatFlux_W",
    "imposed_Q_W",
    "area_weighted_h_W_m2K",
    "area_weighted_Ta_K",
    "area_weighted_Tsur_K",
    "area_weighted_emissivity",
    "mapping_status",
    "interface_registry_status",
]

ROLE_GROUPS = {
    "heater": "intended_heater_input",
    "cooler": "intended_cooler_removal",
    "test_section": "intended_test_section_exchange",
    "ambient_wall": "passive_ambient_wall_exchange",
    "junction_other": "junction_or_stub_diagnostic",
    "zero_gradient_ncc_connector": "zero_gradient_connector",
    "other": "unclassified_or_nonthermal",
}

SPAN_TO_SEGMENT = {
    "lower_leg": "lower_leg",
    "right_leg": "downcomer",
    "upper_leg": "cooling_branch",
    "left_lower_leg": "upcomer",
    "test_section_span": "upcomer",
    "left_upper_leg": "upcomer",
    "junction": "junction",
}


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
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, digits: int = 9) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def extract_named_block(text: str, token: str, start_pos: int = 0) -> tuple[str, int] | None:
    match = re.search(rf"\b{re.escape(token)}\b\s*\{{", text[start_pos:])
    if not match:
        return None
    brace = start_pos + match.end() - 1
    depth = 1
    pos = brace + 1
    while pos < len(text) and depth:
        char = text[pos]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        pos += 1
    if depth:
        return None
    return text[brace + 1 : pos - 1], pos


def iter_boundary_fields(text: str) -> list[str]:
    blocks: list[str] = []
    pos = 0
    while True:
        found = extract_named_block(text, "boundaryField", pos)
        if not found:
            break
        block, pos = found
        blocks.append(block)
    return blocks


def parse_patch_blocks(boundary_text: str) -> dict[str, str]:
    patches: dict[str, str] = {}
    pattern = re.compile(r'(?m)^\s*"?([A-Za-z0-9_.*|()]+)"?\s*\n\s*\{')
    for match in pattern.finditer(boundary_text):
        name = match.group(1)
        brace = match.end() - 1
        depth = 1
        pos = brace + 1
        while pos < len(boundary_text) and depth:
            char = boundary_text[pos]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            pos += 1
        if not depth:
            patches[name] = boundary_text[brace + 1 : pos - 1]
    return patches


def value_for(block: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s+([^;\{{\n][^;]*);", block)
    return " ".join(match.group(1).split()) if match else ""


def scalar_for(block: str, key: str) -> str:
    nested = re.search(rf"(?ms)^\s*{re.escape(key)}\s*\{{(?P<body>.*?)^\s*\}}", block)
    if nested:
        nested_value = value_for(nested.group("body"), "value")
        if nested_value:
            match = re.search(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", nested_value)
            return match.group(0) if match else nested_value
    raw = value_for(block, key)
    if not raw:
        return ""
    match = re.search(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", raw)
    return match.group(0) if match else raw


def list_for(block: str, key: str) -> str:
    match = re.search(rf"(?ms)^\s*{re.escape(key)}\s*(\([^;]*\))\s*;", block)
    return " ".join(match.group(1).split()) if match else ""


def parse_t_boundary(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    parsed: dict[str, dict[str, str]] = {}
    for boundary in iter_boundary_fields(text):
        for patch, block in parse_patch_blocks(boundary).items():
            parsed[patch] = {
                "type": value_for(block, "type"),
                "Q": scalar_for(block, "Q"),
                "h": scalar_for(block, "h"),
                "Ta": scalar_for(block, "Ta"),
                "Tsur": scalar_for(block, "Tsur"),
                "emissivity": scalar_for(block, "emissivity"),
                "thicknessLayers": list_for(block, "thicknessLayers"),
                "kappaLayerCoeffs": list_for(block, "kappaLayerCoeffs"),
            }
    return parsed


def parse_wallheatflux_detail(path: Path) -> tuple[dict[str, dict[str, float]], float | None]:
    by_time: dict[float, dict[str, dict[str, float]]] = defaultdict(dict)
    if not path.exists():
        return {}, None
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.strip()
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


def numbers(text: str) -> list[float]:
    return [
        float(item)
        for item in re.findall(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", text)
    ]


def case_id(source_id: str) -> str:
    match = re.search(r"salt_test_(\d+)_jin", source_id)
    return f"salt_{match.group(1)}" if match else ""


def span_by_patch(source_id: str) -> dict[str, str]:
    profile = get_case_analysis_profile(source_id)
    out: dict[str, str] = {}
    for span_name, definition in profile.major_spans.items():
        for patch in definition.get("wall_patches", []):
            out[str(patch)] = str(span_name)
    return out


def classify_patch(patch: str, span_lookup: dict[str, str]) -> tuple[str, str, str]:
    if patch in PATCH_MAP:
        role, legacy_span = PATCH_MAP[patch]
        parent_span = span_lookup.get(patch, legacy_span)
        return role, parent_span, SPAN_TO_SEGMENT.get(parent_span, legacy_span)
    if patch.startswith("junction_") or patch.startswith("ncc_junction_"):
        return "junction_other", "junction", "junction"
    if patch.startswith("ncc_"):
        return "zero_gradient_ncc_connector", "", ""
    return "other", span_lookup.get(patch, ""), SPAN_TO_SEGMENT.get(span_lookup.get(patch, ""), "")


def area_from_wallheatflux(detail: dict[str, float]) -> float | None:
    q = detail.get("Q_W")
    q_mean = detail.get("q_W_m2")
    if q is None or q_mean in {None, 0.0}:
        return None
    return abs(q / q_mean)


def metadata_status(meta: dict[str, str]) -> str:
    has_h = bool(meta.get("h"))
    has_layers = bool(meta.get("thicknessLayers"))
    if has_h and has_layers:
        return "h_and_layers_present"
    if has_h:
        return "h_only"
    if has_layers:
        return "layers_only"
    return "no_wall_layer_metadata"


def radiation_status(meta: dict[str, str]) -> str:
    if meta.get("emissivity") and meta.get("Tsur"):
        return "emissivity_and_Tsur_metadata_present"
    if meta.get("emissivity"):
        return "emissivity_metadata_present_no_Tsur"
    return "no_emissivity_metadata"


def build_patch_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, cfg in CASES.items():
        run_dir = cfg["run_dir"]
        t_path = run_dir / "0" / "T"
        bc_rows = parse_t_boundary(t_path)
        whf_path, whf_time_dir = find_latest_wallheatflux_dat(run_dir)
        whf_detail, whf_sample_time = parse_wallheatflux_detail(whf_path) if whf_path else ({}, None)
        spans = span_by_patch(source_id)
        for patch_name, meta in sorted(bc_rows.items()):
            role, parent_span, one_d_segment = classify_patch(patch_name, spans)
            detail = whf_detail.get(patch_name, {})
            area = area_from_wallheatflux(detail)
            thicknesses = numbers(meta.get("thicknessLayers", ""))
            mapping_status = "mapped_to_1d_segment" if one_d_segment else "connector_or_unmapped"
            if role == "junction_other":
                mapping_status = "mapped_to_grouped_junction_diagnostic"
            fit_status = "validation_diagnostic"
            if role in {"zero_gradient_ncc_connector", "other"}:
                fit_status = "not_fit_boundary_connector_or_unclassified"
            rows.append(
                {
                    "source_id": source_id,
                    "case_id": case_id(source_id),
                    "run_class": "mainline_jin_continuation",
                    "case_root": rel(run_dir),
                    "patch_name": patch_name,
                    "role": role,
                    "role_group": ROLE_GROUPS.get(role, "unclassified_or_nonthermal"),
                    "bc_type": meta.get("type", ""),
                    "parent_span": parent_span,
                    "one_d_segment": one_d_segment,
                    "one_d_segment_mapping_status": mapping_status,
                    "area_m2": fmt(area),
                    "h_W_m2K": meta.get("h", ""),
                    "Ta_K": meta.get("Ta", ""),
                    "Tsur_K": meta.get("Tsur", ""),
                    "emissivity": meta.get("emissivity", ""),
                    "thicknessLayers": meta.get("thicknessLayers", ""),
                    "thickness_total_m": fmt(sum(thicknesses)) if thicknesses else "",
                    "kappaLayerCoeffs": meta.get("kappaLayerCoeffs", ""),
                    "wall_layer_metadata_status": metadata_status(meta),
                    "imposed_Q_W": meta.get("Q", ""),
                    "realized_wallHeatFlux_W": fmt(detail.get("Q_W")),
                    "realized_wallHeatFlux_mean_W_m2": fmt(detail.get("q_W_m2")),
                    "wallHeatFlux_source_path": rel(whf_path) if whf_path else "",
                    "wallHeatFlux_sample_time_s": fmt(whf_sample_time if whf_sample_time is not None else whf_time_dir),
                    "boundary_dictionary_path": rel(t_path),
                    "radiation_metadata_status": radiation_status(meta),
                    "fit_use_status": fit_status,
                    "notes": "native_solver_outputs_read_only",
                }
            )
    return rows


def grouped_ledger_totals() -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in read_csv(JULY8_GROUPED_LEDGER):
        value = safe_float(row.get("wallHeatFlux_integral_W"))
        if value is not None:
            totals[row["source_id"]] += value
    return totals


def summarize_by_role(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["source_id"], row["case_id"], row["role"])].append(row)
    out: list[dict[str, Any]] = []
    for (source_id, cid, role), payload in sorted(grouped.items()):
        type_counts = Counter(row["bc_type"] for row in payload)
        out.append(
            {
                "source_id": source_id,
                "case_id": cid,
                "role": role,
                "role_group": ROLE_GROUPS.get(role, ""),
                "patch_count": len(payload),
                "area_m2": fmt(sum(safe_float(row["area_m2"]) or 0.0 for row in payload)),
                "imposed_Q_W": fmt(sum(safe_float(row["imposed_Q_W"]) or 0.0 for row in payload)),
                "realized_wallHeatFlux_W": fmt(
                    sum(safe_float(row["realized_wallHeatFlux_W"]) or 0.0 for row in payload)
                ),
                "rcExternalTemperature_count": type_counts.get("rcExternalTemperature", 0),
                "externalTemperature_count": type_counts.get("externalTemperature", 0),
                "zeroGradient_count": type_counts.get("zeroGradient", 0),
            }
        )
    return out


def weighted_mean(rows: list[dict[str, Any]], field: str) -> str:
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        area = safe_float(row.get("area_m2"))
        value = safe_float(row.get(field))
        if area is None or value is None or area <= 0:
            continue
        numerator += area * value
        denominator += area
    return fmt(numerator / denominator) if denominator > 0 else ""


def interface_status_by_source_segment() -> set[tuple[str, str]]:
    rows = read_csv(INTERFACE_REGISTRY)
    return {
        (row.get("source_id", ""), row.get("physical_segment", ""))
        for row in rows
        if row.get("source_id") and row.get("physical_segment")
    }


def segment_reduction_inputs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_segment: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        segment = row.get("one_d_segment", "")
        if not segment:
            continue
        by_segment[(row["source_id"], row["case_id"], segment)].append(row)
    registered = interface_status_by_source_segment()
    out: list[dict[str, Any]] = []
    for (source_id, cid, segment), payload in sorted(by_segment.items()):
        spans = sorted({row["parent_span"] for row in payload if row.get("parent_span")})
        out.append(
            {
                "source_id": source_id,
                "case_id": cid,
                "one_d_segment": segment,
                "component_parent_spans": "+".join(spans),
                "patch_count": len(payload),
                "area_m2": fmt(sum(safe_float(row["area_m2"]) or 0.0 for row in payload)),
                "realized_wallHeatFlux_W": fmt(
                    sum(safe_float(row["realized_wallHeatFlux_W"]) or 0.0 for row in payload)
                ),
                "imposed_Q_W": fmt(sum(safe_float(row["imposed_Q_W"]) or 0.0 for row in payload)),
                "area_weighted_h_W_m2K": weighted_mean(payload, "h_W_m2K"),
                "area_weighted_Ta_K": weighted_mean(payload, "Ta_K"),
                "area_weighted_Tsur_K": weighted_mean(payload, "Tsur_K"),
                "area_weighted_emissivity": weighted_mean(payload, "emissivity"),
                "mapping_status": "patches_collapsed_to_segment_equivalent_inputs",
                "interface_registry_status": (
                    "present_in_interface_registry"
                    if (source_id, segment) in registered
                    else "not_present_or_connector_only"
                ),
            }
        )
    return out


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row["source_id"]].append(row)
        for field in ("source_id", "case_id", "case_root", "patch_name", "role", "bc_type", "boundary_dictionary_path"):
            if not str(row.get(field, "")).strip():
                errors.append(f"{row.get('source_id')}:{row.get('patch_name')}: missing {field}")
        if row["role"] not in ROLE_GROUPS:
            errors.append(f"{row['source_id']}:{row['patch_name']}: unknown role {row['role']}")
        if row["bc_type"] != "zeroGradient" and safe_float(row.get("area_m2")) is None:
            errors.append(f"{row['source_id']}:{row['patch_name']}: non-zeroGradient row missing area")
    for source_id, payload in by_source.items():
        if len(payload) != 69:
            errors.append(f"{source_id}: expected 69 T boundary patches, found {len(payload)}")
        type_counts = Counter(row["bc_type"] for row in payload)
        expected_counts = {"externalTemperature": 10, "rcExternalTemperature": 36, "zeroGradient": 23}
        if dict(type_counts) != expected_counts:
            errors.append(f"{source_id}: unexpected bc type counts {dict(type_counts)}")
        if sum(1 for row in payload if row["role"] == "heater") != 3:
            errors.append(f"{source_id}: expected 3 heater patches")
        if sum(1 for row in payload if row["role"] == "cooler") != 3:
            errors.append(f"{source_id}: expected 3 cooler patches")
        if sum(1 for row in payload if row["role"] == "test_section") != 1:
            errors.append(f"{source_id}: expected 1 test-section patch")
    ledger_totals = grouped_ledger_totals()
    for source_id, expected in ledger_totals.items():
        actual = sum(safe_float(row.get("realized_wallHeatFlux_W")) or 0.0 for row in by_source.get(source_id, []))
        if abs(actual - expected) > 5e-4:
            errors.append(f"{source_id}: patch sum {actual:.9g} != July 8 grouped sum {expected:.9g}")
    return errors


def write_readme(rows: list[dict[str, Any]], errors: list[str]) -> None:
    text = f"""# Thermal Boundary Patch-Role Table

Generated: `{datetime.now().isoformat(timespec='seconds')}`
Task: `AGENT-263`

## Scope

Patch-level CFD thermal boundary table for admitted Salt 2/3/4 Jin mainline
continuations. The package reads OpenFOAM `0/T` dictionaries and existing
`wallHeatFlux.dat` postProcessing outputs only. Native solver outputs are not
modified.

## Outputs

- `thermal_boundary_patch_role_table.csv`
- `thermal_boundary_patch_role_table.json`
- `patch_role_area_heat_summary.csv`
- `segment_reduction_inputs.csv`
- `validation_report.json`
- `summary.json`

## Contract

Positive `realized_wallHeatFlux_W` means heat enters the fluid; negative means
heat leaves the fluid. Patch rows preserve imposed `Q`, realized wall flux,
boundary `h`, `Ta`, `Tsur`, emissivity, and wall/layer metadata separately.

Rows with `zero_gradient_ncc_connector` are connector/support patches and are
not 1D fit targets. Junction rows are grouped diagnostics. Segment reduction
rows provide area-weighted external inputs for a future 1D parity mode, not a
new 1D run.

## Counts

- Patch rows: `{len(rows)}`
- Sources: `{sorted({row['source_id'] for row in rows})}`
- Roles: `{dict(sorted(Counter(row['role'] for row in rows).items()))}`
- Validation errors: `{len(errors)}`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_outputs(rows: list[dict[str, Any]], errors: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    role_rows = summarize_by_role(rows)
    segment_rows = segment_reduction_inputs(rows)
    write_csv(OUT / "thermal_boundary_patch_role_table.csv", rows, PATCH_FIELDS)
    (OUT / "thermal_boundary_patch_role_table.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    write_csv(OUT / "patch_role_area_heat_summary.csv", role_rows, SUMMARY_FIELDS)
    write_csv(OUT / "segment_reduction_inputs.csv", segment_rows, SEGMENT_FIELDS)
    validation = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "validation_passed": not errors,
        "validation_errors": errors,
    }
    (OUT / "validation_report.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    summary = {
        "generated_at": validation["generated_at"],
        "task": "AGENT-263",
        "patch_rows": len(rows),
        "source_ids": sorted({row["source_id"] for row in rows}),
        "role_counts": dict(sorted(Counter(row["role"] for row in rows).items())),
        "bc_type_counts": dict(sorted(Counter(row["bc_type"] for row in rows).items())),
        "validation_passed": not errors,
        "validation_errors": errors,
        "outputs": {
            "patch_table": rel(OUT / "thermal_boundary_patch_role_table.csv"),
            "role_summary": rel(OUT / "patch_role_area_heat_summary.csv"),
            "segment_reduction_inputs": rel(OUT / "segment_reduction_inputs.csv"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(rows, errors)


def main() -> int:
    rows = build_patch_rows()
    errors = validate_rows(rows)
    write_outputs(rows, errors)
    print(f"patch_rows={len(rows)}")
    print(f"validation_errors={len(errors)}")
    print(f"wrote {rel(OUT)}")
    if errors:
        for error in errors[:20]:
            print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
