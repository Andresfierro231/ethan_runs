#!/usr/bin/env python3
"""Advance Salt mesh-UQ blockers without mutating solver data.

This package does three concrete read-only checks after AGENT-231:

1. Compare mainline coarse continuation monitor values against the external
   coarse mesh-family monitor values.
2. Inventory whether Salt 2/4 medium/fine cases have the inputs required for
   pressure/thermal closure-QoI extraction.
3. Review Salt 4 medium/fine admission evidence from logs and full-history
   monitors.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_salt_mesh_full_history_monitor_reduction import build_monitor_rows  # noqa: E402
from tools.analyze.compute_gci import compute_gci  # noqa: E402
from tools.common import WORKSPACE_ROOT, ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_CATALOG = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_case_catalog.csv"
)
DEFAULT_QUALITY = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_quality_gate.csv"
)
DEFAULT_SCENARIO = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv"
)
DEFAULT_FOLLOWON = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_followon_readiness"
)
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_blocker_resolution_progress"
)

ENDPOINT_CASES = ("salt_test_2_jin", "salt_test_4_jin")
SOURCE_ID_TO_CASE = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt_test_2_jin",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt_test_4_jin",
}
MONITOR_QUANTITIES = [
    "mdot_abs_mean_kg_s",
    "wall_gross_duty_w",
    "wall_heat_in_w",
    "wall_heat_out_w",
    "wall_net_q_w",
    "yplus_global_max",
    "yplus_patch_average_mean",
    "temperature_probe_mean_K",
    "wall_temperature_probe_mean_K",
]
ALIGN_TOLERANCES = {
    "mdot_abs_mean_kg_s": ("relative", 0.01),
    "wall_gross_duty_w": ("relative", 0.01),
    "wall_heat_in_w": ("relative", 0.01),
    "wall_heat_out_w": ("relative", 0.01),
    "wall_net_q_w": ("absolute", 5.0),
    "yplus_global_max": ("relative", 0.25),
    "yplus_patch_average_mean": ("relative", 0.25),
    "temperature_probe_mean_K": ("absolute", 2.0),
    "wall_temperature_probe_mean_K": ("absolute", 2.0),
}
CORE_ALIGNMENT_QUANTITIES = {
    "mdot_abs_mean_kg_s",
    "wall_gross_duty_w",
    "wall_heat_in_w",
    "wall_heat_out_w",
    "temperature_probe_mean_K",
    "wall_temperature_probe_mean_K",
}

ALIGN_FIELDS = [
    "case_id",
    "quantity",
    "units",
    "external_coarse_value",
    "mainline_coarse_value",
    "abs_delta",
    "rel_delta",
    "tolerance_type",
    "tolerance_value",
    "alignment_status",
    "external_series_verdict",
    "mainline_series_verdict",
    "mainline_source_path",
    "external_source_note",
]

CASE_DECISION_FIELDS = [
    "case_id",
    "core_quantity_count",
    "core_aligned_count",
    "core_blocked_count",
    "baseline_decision",
    "recommended_next_action",
]

INVENTORY_FIELDS = [
    "case_id",
    "mesh_level",
    "source_id",
    "source_path",
    "source_exists",
    "processor_dir",
    "processor_dir_exists",
    "latest_solver_time_s",
    "required_fields_present",
    "postprocessing_families_present",
    "existing_closure_products",
    "pressure_qoi_status",
    "thermal_qoi_status",
    "recommended_execution",
    "notes",
]

SALT4_FIELDS = [
    "case_id",
    "mesh_level",
    "gate_verdict",
    "foamrun_terminal_state",
    "tail_signal15",
    "tail_convergence_monitor",
    "monitor_rows",
    "stationary_or_quasi_rows",
    "problem_rows",
    "admission_review",
    "recommended_next_action",
]

MAINLINE_GCI_FIELDS = [
    "case_id",
    "quantity",
    "units",
    "coarse_source",
    "coarse_value",
    "medium_value",
    "fine_value",
    "r21",
    "r32",
    "medium_gate_verdict",
    "fine_gate_verdict",
    "verdict",
    "order_status",
    "observed_order_p",
    "f_exact_richardson",
    "gci_fine_pct",
    "gci_coarse_pct",
    "asymptotic_range_ratio",
    "gci_trustworthy",
    "endpoint_monitor_gci_status",
    "publication_ready",
    "note",
]

PROTOCOL_TARGETS = {
    "mdot_abs_mean_kg_s": 2.0,
    "wall_gross_duty_w": 5.0,
    "wall_heat_in_w": 5.0,
    "wall_heat_out_w": 5.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--quality", default=str(DEFAULT_QUALITY))
    parser.add_argument("--scenario-contract", default=str(DEFAULT_SCENARIO))
    parser.add_argument("--followon-dir", default=str(DEFAULT_FOLLOWON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def numeric(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def numeric_dirs(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    pairs: list[tuple[float, Path]] = []
    for child in path.iterdir():
        value = numeric(child.name)
        if child.is_dir() and value is not None:
            pairs.append((value, child))
    return [item[1] for item in sorted(pairs, key=lambda item: item[0])]


def mainline_rows(scenario: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in scenario:
        case_id = SOURCE_ID_TO_CASE.get(row.get("source_id", ""))
        if not case_id or row.get("run_class") != "mainline_jin_continuation":
            continue
        root = WORKSPACE_ROOT / row["case_root"]
        rows.append(
            {
                "source_id": f"{row['source_id']}_mainline_continuation",
                "case_id": case_id,
                "mesh_level": "coarse",
                "fluid_variant": "jin",
                "source_path": str(root),
            }
        )
    return rows


def value_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["case_id"], row["quantity"]): row for row in rows if row.get("mesh_level") == "coarse"}


def compare_status(quantity: str, external: float | None, mainline: float | None) -> tuple[str, str, float | None, float | None, float | None]:
    tolerance_type, tolerance = ALIGN_TOLERANCES[quantity]
    if external is None or mainline is None:
        return "missing_value", tolerance_type, tolerance, None, None
    abs_delta = abs(mainline - external)
    scale = max(abs(external), abs(mainline), 1.0e-20)
    rel_delta = abs_delta / scale
    metric = rel_delta if tolerance_type == "relative" else abs_delta
    status = "aligned" if metric <= tolerance else "different"
    return status, tolerance_type, tolerance, abs_delta, rel_delta


def build_mainline_alignment(
    scenario: list[dict[str, str]],
    external_monitor_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    mainline_catalog = mainline_rows(scenario)
    mainline_monitor_rows, _coverage = build_monitor_rows(mainline_catalog)
    mainline_values = value_map(mainline_monitor_rows)
    external_values = value_map(external_monitor_rows)
    alignment: list[dict[str, Any]] = []
    for case_id in ENDPOINT_CASES:
        source_path = next((row["source_path"] for row in mainline_catalog if row["case_id"] == case_id), "")
        for quantity in MONITOR_QUANTITIES:
            ext = external_values.get((case_id, quantity), {})
            main = mainline_values.get((case_id, quantity), {})
            ext_value = numeric(ext.get("mean_value"))
            main_value = numeric(main.get("mean_value"))
            status, tol_type, tol_value, abs_delta, rel_delta = compare_status(quantity, ext_value, main_value)
            alignment.append(
                {
                    "case_id": case_id,
                    "quantity": quantity,
                    "units": ext.get("units") or main.get("units", ""),
                    "external_coarse_value": "" if ext_value is None else ext_value,
                    "mainline_coarse_value": "" if main_value is None else main_value,
                    "abs_delta": "" if abs_delta is None else abs_delta,
                    "rel_delta": "" if rel_delta is None else rel_delta,
                    "tolerance_type": tol_type,
                    "tolerance_value": tol_value,
                    "alignment_status": status,
                    "external_series_verdict": ext.get("series_verdict", "missing"),
                    "mainline_series_verdict": main.get("series_verdict", "missing"),
                    "mainline_source_path": source_path,
                    "external_source_note": "external coarse mesh-family summary from AGENT-231",
                }
            )
    decisions: list[dict[str, Any]] = []
    for case_id in ENDPOINT_CASES:
        core = [row for row in alignment if row["case_id"] == case_id and row["quantity"] in CORE_ALIGNMENT_QUANTITIES]
        aligned = [row for row in core if row["alignment_status"] == "aligned"]
        blocked = [row for row in core if row["alignment_status"] != "aligned"]
        if not blocked:
            decision = "mainline_coarse_can_replace_external_for_endpoint_monitor_gci"
            action = "recompute endpoint monitor GCI using mainline coarse and external medium/fine"
        else:
            decision = "blocked_mainline_external_coarse_values_differ"
            action = "inspect differing monitor histories before selecting a coarse baseline"
        decisions.append(
            {
                "case_id": case_id,
                "core_quantity_count": len(core),
                "core_aligned_count": len(aligned),
                "core_blocked_count": len(blocked),
                "baseline_decision": decision,
                "recommended_next_action": action,
            }
        )
    return alignment, decisions, mainline_monitor_rows


def field_presence(case_root: Path, proc_dir: str) -> tuple[str, str]:
    proc = case_root / proc_dir
    times = numeric_dirs(proc)
    latest = times[-1] if times else None
    required = ["U", "p_rgh", "T"]
    if latest is None:
        return "", "no_processor_times"
    present = [name for name in required if (latest / name).exists()]
    status = "yes" if len(present) == len(required) else f"partial:{','.join(present)}"
    return latest.name, status


def postprocessing_families(case_root: Path) -> set[str]:
    pp = case_root / "postProcessing"
    if not pp.is_dir():
        return set()
    return {child.name for child in pp.iterdir()}


def build_closure_qoi_inventory(catalog: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in catalog:
        if row.get("case_id") not in ENDPOINT_CASES or row.get("mesh_level") not in {"medium", "fine"} or row.get("fluid_variant") != "jin":
            continue
        root = Path(row["source_path"])
        proc_dir = row.get("proc_dir") or ("processors128" if row["mesh_level"] == "fine" else "processors64")
        latest_time, fields_status = field_presence(root, proc_dir)
        families = postprocessing_families(root)
        closure_products = [
            name
            for name in families
            if any(token in name.lower() for token in ["section_mean", "pressure", "secmean", "htc", "interface"])
        ]
        processor_exists = (root / proc_dir).is_dir()
        pressure_status = (
            "field_data_present_sampling_required"
            if processor_exists and fields_status == "yes"
            else "blocked_missing_required_fields"
        )
        thermal_inputs = {"wallHeatFlux", "wall_temperature_probes", "temperature_probes"}.issubset(families)
        thermal_status = (
            "monitor_inputs_present_sampling_required"
            if thermal_inputs and processor_exists
            else "blocked_missing_thermal_inputs"
        )
        rows.append(
            {
                "case_id": row["case_id"],
                "mesh_level": row["mesh_level"],
                "source_id": row["source_id"],
                "source_path": row["source_path"],
                "source_exists": "yes" if root.is_dir() else "no",
                "processor_dir": proc_dir,
                "processor_dir_exists": "yes" if processor_exists else "no",
                "latest_solver_time_s": latest_time,
                "required_fields_present": fields_status,
                "postprocessing_families_present": ";".join(sorted(families)),
                "existing_closure_products": ";".join(sorted(closure_products)) if closure_products else "none",
                "pressure_qoi_status": pressure_status,
                "thermal_qoi_status": thermal_status,
                "recommended_execution": "compute_node_sampling_job_no_login_node_extraction",
                "notes": "No existing section-mean pressure or physical-interface closure products found in postProcessing.",
            }
        )
    return rows


def monitor_value_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {(row["case_id"], row["mesh_level"], row["quantity"]): row for row in rows}


def catalog_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_id"], row["mesh_level"]): row for row in rows}


def mesh_ratios(catalog: dict[tuple[str, str], dict[str, str]], case_id: str) -> tuple[float, float]:
    fine = numeric(catalog[(case_id, "fine")].get("bulk_cell_size"))
    medium = numeric(catalog[(case_id, "medium")].get("bulk_cell_size"))
    coarse = numeric(catalog[(case_id, "coarse")].get("bulk_cell_size"))
    if fine is None or medium is None or coarse is None or fine <= 0.0 or medium <= 0.0:
        return 1.5, 1.5
    return medium / fine, coarse / medium


def gate_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    return {(row["case_id"], row["mesh_level"]): row.get("gate_verdict", "") for row in rows}


def mainline_coarse_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["case_id"], row["quantity"]): row for row in rows if row.get("mesh_level") == "coarse"}


def build_mainline_endpoint_gci(
    catalog_rows: list[dict[str, str]],
    quality_rows: list[dict[str, str]],
    external_monitor_rows: list[dict[str, str]],
    mainline_monitor_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    catalog = catalog_map(catalog_rows)
    gates = gate_map(quality_rows)
    external = monitor_value_map(external_monitor_rows)
    mainline = mainline_coarse_map(mainline_monitor_rows)
    decision_map = {row["case_id"]: row["baseline_decision"] for row in decisions}
    rows: list[dict[str, Any]] = []
    for case_id in ENDPOINT_CASES:
        r21, r32 = mesh_ratios(catalog, case_id)
        for quantity in MONITOR_QUANTITIES:
            coarse_row = mainline.get((case_id, quantity), {})
            medium_row = external.get((case_id, "medium", quantity), {})
            fine_row = external.get((case_id, "fine", quantity), {})
            values = [numeric(coarse_row.get("mean_value")), numeric(medium_row.get("mean_value")), numeric(fine_row.get("mean_value"))]
            if any(value is None for value in values):
                continue
            gci = compute_gci(values[0], values[1], values[2], r21, r32)
            medium_gate = gates.get((case_id, "medium"), "missing")
            fine_gate = gates.get((case_id, "fine"), "missing")
            target = PROTOCOL_TARGETS.get(quantity)
            if decision_map.get(case_id) != "mainline_coarse_can_replace_external_for_endpoint_monitor_gci":
                status = "blocked_coarse_not_aligned"
            elif medium_gate != "admitted_for_gci_input" or fine_gate != "admitted_for_gci_input":
                status = "blocked_medium_or_fine_not_admitted"
            elif gci.get("gci_trustworthy") is not True:
                status = "blocked_gci_not_trustworthy"
            elif target is not None and numeric(gci.get("gci_fine_pct")) is not None and gci["gci_fine_pct"] > target:
                status = "blocked_gci_exceeds_protocol_target"
            elif target is None:
                status = "diagnostic_gci_computed"
            else:
                status = "endpoint_monitor_gci_ready"
            rows.append(
                {
                    "case_id": case_id,
                    "quantity": quantity,
                    "units": coarse_row.get("units", ""),
                    "coarse_source": "mainline_continuation",
                    "coarse_value": values[0],
                    "medium_value": values[1],
                    "fine_value": values[2],
                    "r21": r21,
                    "r32": r32,
                    "medium_gate_verdict": medium_gate,
                    "fine_gate_verdict": fine_gate,
                    "verdict": gci["verdict"],
                    "order_status": gci["order_status"],
                    "observed_order_p": gci["observed_order_p"],
                    "f_exact_richardson": gci["f_exact_richardson"],
                    "gci_fine_pct": gci["gci_fine_pct"],
                    "gci_coarse_pct": gci["gci_coarse_pct"],
                    "asymptotic_range_ratio": gci["asymptotic_range_ratio"],
                    "gci_trustworthy": gci["gci_trustworthy"],
                    "endpoint_monitor_gci_status": status,
                    "publication_ready": "yes" if status == "endpoint_monitor_gci_ready" else "no",
                    "note": gci["gci_note"],
                }
            )
    return rows


def quality_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_id"], row["mesh_level"]): row for row in rows}


def build_salt4_admission_review(
    quality_rows: list[dict[str, str]],
    monitor_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    qmap = quality_map(quality_rows)
    rows: list[dict[str, Any]] = []
    for level in ("medium", "fine"):
        q = qmap.get(("salt_test_4_jin", level), {})
        monitors = [
            row
            for row in monitor_rows
            if row.get("case_id") == "salt_test_4_jin"
            and row.get("mesh_level") == level
            and row.get("series_verdict") != "derived_composite"
        ]
        stationary = [
            row for row in monitors if row.get("series_verdict") in {"stationary", "quasi_stationary"}
        ]
        problem = [
            row
            for row in monitors
            if row.get("series_verdict") in {"drifting_or_oscillatory", "short_or_partial", "missing_monitor"}
        ]
        if q.get("gate_verdict") != "admitted_for_gci_input":
            admission = "not_admitted_log_gate_failed"
            action = "prepare continuation_or_stronger_admission_review_before_publication_gci"
        elif problem:
            admission = "not_admitted_monitor_problem"
            action = "resolve nonstationary monitor rows before gci"
        else:
            admission = "candidate_admitted_by_monitors"
            action = "combine with coarse-alignment decision for GCI"
        rows.append(
            {
                "case_id": "salt_test_4_jin",
                "mesh_level": level,
                "gate_verdict": q.get("gate_verdict", ""),
                "foamrun_terminal_state": q.get("foamrun_terminal_state", ""),
                "tail_signal15": q.get("tail_signal15", ""),
                "tail_convergence_monitor": q.get("tail_convergence_monitor", ""),
                "monitor_rows": len(monitors),
                "stationary_or_quasi_rows": len(stationary),
                "problem_rows": len(problem),
                "admission_review": admission,
                "recommended_next_action": action,
            }
        )
    return rows


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Salt Mesh Blocker Resolution Progress

Generated: `{summary['generated_at']}`

## Summary

This read-only package makes concrete progress on the blockers identified by
AGENT-231. It compares mainline coarse endpoint monitor values with external
coarse mesh-family values, inventories medium/fine closure-QOI extraction
readiness, and reviews Salt 4 medium/fine admission evidence.

## Observed Facts

- Mainline/external coarse alignment decisions: `{summary['baseline_decision_counts']}`.
- Mainline-coarse endpoint monitor GCI status: `{summary['endpoint_monitor_gci_status_counts']}`.
- Medium/fine closure-QOI inventory rows: `{summary['closure_inventory_count']}`.
- Salt 4 admission review rows: `{summary['salt4_review_count']}`.

## Interpretation

If a case is `mainline_coarse_can_replace_external_for_endpoint_monitor_gci`,
the existing mainline continuation can be used as the coarse endpoint for monitor
GCI after regenerating the GCI table with that baseline. This does not solve
debuoyed friction or Nu/HTC GCI: those still need medium/fine compute-node
sampling because section-mean pressure and physical-interface closure products
are not already present.
"""
    path.write_text(text, encoding="utf-8")


def write_next_actions(path: Path, decisions: list[dict[str, Any]], inventory: list[dict[str, Any]], salt4: list[dict[str, Any]]) -> None:
    ready_cases = [row["case_id"] for row in decisions if row["baseline_decision"] == "mainline_coarse_can_replace_external_for_endpoint_monitor_gci"]
    text = f"""# Next Actions

## Do Now

1. Use `endpoint_monitor_gci_mainline_coarse.csv` as the current endpoint-monitor
   GCI screen for cases with aligned mainline coarse baselines: `{';'.join(ready_cases) if ready_cases else 'none'}`.
2. Stage a compute-node sampling task for medium/fine pressure and thermal closure QoIs.
3. Keep `closure_observations.csv` unchanged until admitted closure-QOI mesh-UQ
   rows exist.

## Sampling Targets

- pressure: section-mean or centerline-derived `p_rgh`, `U`, `T/rho` reductions for lower leg and test-section spans;
- thermal: physical-interface bulk temperatures, wallHeatFlux, wall/wall-adjacent temperature, Nu/HTC or UA-prime metrics;
- provenance: exact source case root, mesh level, time window, processor layout, and sampling dictionary.

## Salt 4

Salt 4 medium/fine still require a log/admission decision before publication GCI.
Full-history monitors are useful screening evidence, but signal-15/no convergence
monitor evidence remains the controlling blocker unless a later task explicitly
admits the runs.
"""
    path.write_text(text, encoding="utf-8")


def run(
    catalog_path: Path,
    quality_path: Path,
    scenario_path: Path,
    followon_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    out = ensure_dir(output_dir)
    catalog = read_csv(catalog_path)
    quality = read_csv(quality_path)
    scenario = read_csv(scenario_path)
    external_monitor_rows = read_csv(followon_dir / "endpoint_full_history_monitor_summary.csv")

    alignment_rows, decision_rows, mainline_monitor_rows = build_mainline_alignment(scenario, external_monitor_rows)
    inventory_rows = build_closure_qoi_inventory(catalog)
    salt4_rows = build_salt4_admission_review(quality, external_monitor_rows)
    mainline_gci_rows = build_mainline_endpoint_gci(
        catalog,
        quality,
        external_monitor_rows,
        mainline_monitor_rows,
        decision_rows,
    )

    write_csv(out / "mainline_coarse_alignment.csv", alignment_rows, ALIGN_FIELDS)
    write_csv(out / "mainline_coarse_baseline_decisions.csv", decision_rows, CASE_DECISION_FIELDS)
    write_csv(out / "mainline_coarse_full_history_monitor_summary.csv", mainline_monitor_rows, list(mainline_monitor_rows[0].keys()))
    write_csv(out / "endpoint_monitor_gci_mainline_coarse.csv", mainline_gci_rows, MAINLINE_GCI_FIELDS)
    write_csv(out / "medium_fine_closure_qoi_inventory.csv", inventory_rows, INVENTORY_FIELDS)
    write_csv(out / "salt4_admission_review.csv", salt4_rows, SALT4_FIELDS)

    decision_counts: dict[str, int] = {}
    for row in decision_rows:
        decision_counts[row["baseline_decision"]] = decision_counts.get(row["baseline_decision"], 0) + 1
    gci_status_counts: dict[str, int] = {}
    for row in mainline_gci_rows:
        gci_status_counts[row["endpoint_monitor_gci_status"]] = gci_status_counts.get(row["endpoint_monitor_gci_status"], 0) + 1
    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-235",
        "output_dir": rel(out),
        "alignment_row_count": len(alignment_rows),
        "baseline_decision_counts": dict(sorted(decision_counts.items())),
        "endpoint_monitor_gci_row_count": len(mainline_gci_rows),
        "endpoint_monitor_gci_status_counts": dict(sorted(gci_status_counts.items())),
        "closure_inventory_count": len(inventory_rows),
        "salt4_review_count": len(salt4_rows),
        "source_tree_read_only": True,
        "registry_updated": False,
        "staging_updated": False,
        "closure_observations_updated": False,
        "continuation_jobs_submitted": False,
        "generated_files": [
            rel(out / "mainline_coarse_alignment.csv"),
            rel(out / "mainline_coarse_baseline_decisions.csv"),
            rel(out / "mainline_coarse_full_history_monitor_summary.csv"),
            rel(out / "endpoint_monitor_gci_mainline_coarse.csv"),
            rel(out / "medium_fine_closure_qoi_inventory.csv"),
            rel(out / "salt4_admission_review.csv"),
            rel(out / "next_actions.md"),
            rel(out / "README.md"),
            rel(out / "summary.json"),
        ],
    }
    write_next_actions(out / "next_actions.md", decision_rows, inventory_rows, salt4_rows)
    write_json(out / "summary.json", summary)
    write_readme(out / "README.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(
        Path(args.catalog),
        Path(args.quality),
        Path(args.scenario_contract),
        Path(args.followon_dir),
        Path(args.output_dir),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
