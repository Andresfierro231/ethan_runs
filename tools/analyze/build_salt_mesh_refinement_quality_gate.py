#!/usr/bin/env python3
"""Categorize Salt mesh-refinement cases and build a lightweight quality gate.

This tool is read-only over Ethan's source tree. It consumes the AGENT-226
discovery inventory, rechecks source paths, parses existing logs and
postProcessing monitors, and writes a dated work-product package. It does not
register cases, stage files, reconstruct fields, or run OpenFOAM utilities.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_INPUT = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_discovery/mesh_case_inventory.csv"
)
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate"
)

MESH_STATUS_BY_GATE = {
    "admitted_for_gci_input": "mesh_gci_ready",
    "partial_needs_continuation": "mesh_level_unconverged",
    "partial_needs_coarse_reconciliation": "mesh_family_candidate",
    "inventory_only": "mesh_family_candidate",
    "historical_kirst_only": "historical_kirst_only",
    "missing_source": "mesh_source_missing",
}

MDOT_MONITORS = [
    "mdot_pipeleg_left_04_test_section",
    "mdot_pipeleg_lower_05_straight",
    "mdot_pipeleg_right_02_middle",
    "mdot_pipeleg_upper_05_cooler",
]
REQUIRED_POSTPROCESSING = [
    "piv_slab_velocity",
    "temperature_probes",
    "wall_temperature_probes",
    "velocity_profiles",
    "wallShearStress",
    "wallHeatFlux",
    "yPlus",
    "total_Q.dat",
    *MDOT_MONITORS,
]
ENDPOINT_CASES = {"salt_test_2_jin", "salt_test_4_jin"}
PRIMARY_CASE = "salt_test_2_jin"
UPPER_ENDPOINT_CASE = "salt_test_4_jin"
WINDOW_FRAC = 0.25
TAIL_BYTES = 1_500_000

CATALOG_FIELDS = [
    "source_id",
    "case_name",
    "case_id",
    "fluid_variant",
    "mesh_level",
    "mesh_status",
    "run_class",
    "independence_group_id",
    "source_path",
    "source_exists",
    "proc_dir",
    "nprocs",
    "cell_count",
    "mesh_group_id",
    "first_cell_size",
    "bulk_cell_size",
    "stored_time_dir_count",
    "latest_solver_time_s",
    "latest_postprocessing_time_s",
    "category",
    "admission_bucket",
    "fit_use_status",
    "provenance_notes",
]

QUALITY_FIELDS = [
    "source_id",
    "case_id",
    "mesh_level",
    "fluid_variant",
    "source_path",
    "source_exists",
    "foamrun_terminal_state",
    "tail_signal15",
    "tail_convergence_monitor",
    "tail_convergence_line",
    "latest_solver_time_s",
    "latest_postprocessing_time_s",
    "stored_time_dir_count",
    "postprocessing_family_count",
    "missing_required_postprocessing",
    "mdot_monitor_count",
    "wallheatflux_present",
    "yplus_present",
    "gate_verdict",
    "quality_flags",
]

ENDPOINT_FIELDS = [
    "source_id",
    "case_id",
    "mesh_level",
    "quantity",
    "monitor",
    "time_window_start_s",
    "time_window_end_s",
    "n_samples",
    "mean_value",
    "last_value",
    "std_value",
    "relative_std",
    "drift_fraction",
    "amplitude_fraction",
    "series_verdict",
    "units",
    "source_file",
]

GCI_FIELDS = [
    "independence_group_id",
    "case_id",
    "quantity",
    "units",
    "coarse_value",
    "medium_value",
    "fine_value",
    "coarse_gate_verdict",
    "medium_gate_verdict",
    "fine_gate_verdict",
    "triplet_status",
    "reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="AGENT-226 mesh_case_inventory.csv path.")
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
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def numeric_dirs(path: Path) -> list[float]:
    if not path.is_dir():
        return []
    values: list[float] = []
    for child in path.iterdir():
        if not child.is_dir():
            continue
        value = numeric(child.name)
        if value is not None:
            values.append(value)
    return sorted(values)


def source_id(case_id: str, mesh_level: str) -> str:
    return f"{case_id}_{mesh_level}_mesh_external_20260707"


def category_for(row: dict[str, str]) -> tuple[str, str, str]:
    case_id = row["case_id"]
    fluid = row["fluid_variant"]
    if fluid == "kirst":
        return "historical_kirst_only", "historical_kirst_only", "not_current_mainline"
    if case_id == PRIMARY_CASE:
        return "primary_gci_endpoint", "gci_endpoint_primary", "held_for_mesh_uq"
    if case_id == UPPER_ENDPOINT_CASE:
        return "upper_gci_endpoint", "gci_endpoint_required", "held_for_mesh_uq"
    return "secondary_jin_coverage", "inventory_only", "held_secondary_mesh_coverage"


def read_tail(path: Path, max_lines: int = 400) -> list[str]:
    if not path.exists():
        return []
    text = read_tail_text(path).splitlines()
    return text[-max_lines:]


def read_tail_text(path: Path, max_bytes: int = TAIL_BYTES) -> str:
    if not path.exists():
        return ""
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size > max_bytes:
            handle.seek(-max_bytes, 2)
            handle.readline()
        return handle.read().decode("utf-8", errors="ignore")


def log_status(case_root: Path) -> dict[str, str]:
    tail = read_tail(case_root / "logs/log.foamRun")
    joined = "\n".join(tail)
    convergence_lines = [line.strip() for line in tail if "convergenceMonitor: CONVERGED" in line]
    clean_end = any(line.strip() == "End" for line in tail)
    signal15 = "KILLED BY SIGNAL: 15" in joined
    if clean_end:
        terminal = "clean_end"
    elif signal15:
        terminal = "signal15"
    elif tail:
        terminal = "tail_no_clean_end"
    else:
        terminal = "missing_log"
    return {
        "foamrun_terminal_state": terminal,
        "tail_signal15": "yes" if signal15 else "no",
        "tail_convergence_monitor": "yes" if convergence_lines else "no",
        "tail_convergence_line": convergence_lines[-1] if convergence_lines else "",
    }


def postprocessing_families(case_root: Path) -> set[str]:
    pp = case_root / "postProcessing"
    if not pp.is_dir():
        return set()
    return {child.name for child in pp.iterdir()}


def find_series_files(monitor_dir: Path, filename: str) -> list[Path]:
    if not monitor_dir.is_dir():
        return []
    files: list[tuple[float, Path]] = []
    for child in monitor_dir.iterdir():
        candidate = child / filename
        if not candidate.exists():
            continue
        start = numeric(child.name)
        files.append((start if start is not None else -1.0, candidate))
    return [item[1] for item in sorted(files, key=lambda item: item[0])]


def latest_series_file(monitor_dir: Path, filename: str) -> Path | None:
    files = find_series_files(monitor_dir, filename)
    return files[-1] if files else None


def parse_scalar_series(path: Path) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    if not path.exists():
        return rows
    for line in read_tail_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        t = numeric(parts[0])
        value = numeric(parts[-1])
        if t is not None and value is not None:
            rows.append((t, value))
    return rows


def merge_scalar_restart_series(monitor_dir: Path, filename: str) -> tuple[list[tuple[float, float]], str]:
    path = latest_series_file(monitor_dir, filename)
    if path is None:
        return [], ""
    return parse_scalar_series(path), rel(path)


def linear_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    x_mean = mean(xs)
    y_mean = mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0.0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom


def summarize_series(series: list[tuple[float, float]], *, window_frac: float = WINDOW_FRAC) -> dict[str, Any]:
    if not series:
        return {
            "n_samples": 0,
            "time_window_start_s": "",
            "time_window_end_s": "",
            "mean_value": "",
            "last_value": "",
            "std_value": "",
            "relative_std": "",
            "drift_fraction": "",
            "amplitude_fraction": "",
            "series_verdict": "missing_series",
        }
    start_all, end_all = series[0][0], series[-1][0]
    cutoff = start_all + (end_all - start_all) * (1.0 - window_frac)
    window = [(t, value) for t, value in series if t >= cutoff]
    if len(window) < 3:
        window = series[-min(len(series), 3) :]
    times = [item[0] for item in window]
    values = [item[1] for item in window]
    value_mean = mean(values)
    value_std = pstdev(values) if len(values) > 1 else 0.0
    scale = abs(value_mean)
    if scale <= 1e-20:
        scale = max(abs(value) for value in values) if values else 1.0
    if scale <= 1e-20:
        scale = 1.0
    slope = linear_slope(times, values)
    span = max(times) - min(times)
    drift = abs(slope * span) / scale
    amp = (max(values) - min(values)) / scale
    rel_std = value_std / scale
    if drift < 0.01 and amp < 0.02:
        verdict = "stationary"
    elif drift < 0.05 and amp < 0.10:
        verdict = "quasi_stationary"
    else:
        verdict = "drifting_or_oscillatory"
    return {
        "n_samples": len(window),
        "time_window_start_s": min(times),
        "time_window_end_s": max(times),
        "mean_value": value_mean,
        "last_value": series[-1][1],
        "std_value": value_std,
        "relative_std": rel_std,
        "drift_fraction": drift,
        "amplitude_fraction": amp,
        "series_verdict": verdict,
    }


def parse_wallheatflux(path: Path) -> list[tuple[float, str, float]]:
    rows: list[tuple[float, str, float]] = []
    if not path.exists():
        return rows
    for line in read_tail_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 5:
            continue
        t = numeric(parts[0])
        q_total = numeric(parts[4])
        if t is not None and q_total is not None:
            rows.append((t, parts[1], q_total))
    return rows


def wallheatflux_series(case_root: Path) -> tuple[dict[str, list[tuple[float, float]]], str]:
    by_time: dict[float, list[float]] = {}
    path = latest_series_file(case_root / "postProcessing/wallHeatFlux", "wallHeatFlux.dat")
    source_file = rel(path) if path else ""
    if path is not None:
        for t, _patch, q_total in parse_wallheatflux(path):
            by_time.setdefault(t, []).append(q_total)
    series = {
        "wall_gross_duty_w": [],
        "wall_heat_in_w": [],
        "wall_heat_out_w": [],
        "wall_net_q_w": [],
    }
    for t in sorted(by_time):
        values = by_time[t]
        heat_in = sum(value for value in values if value > 0)
        heat_out = sum(value for value in values if value < 0)
        gross = sum(abs(value) for value in values)
        net = heat_in + heat_out
        series["wall_gross_duty_w"].append((t, gross))
        series["wall_heat_in_w"].append((t, heat_in))
        series["wall_heat_out_w"].append((t, heat_out))
        series["wall_net_q_w"].append((t, net))
    return series, source_file


def latest_postprocessing_time(case_root: Path) -> float | None:
    times: list[float] = []
    pp = case_root / "postProcessing"
    if not pp.is_dir():
        return None
    for child in pp.iterdir():
        if child.is_dir():
            times.extend(numeric_dirs(child))
    return max(times) if times else None


def latest_solver_time(case_root: Path, proc_dir: str) -> tuple[int, float | None]:
    times = numeric_dirs(case_root / proc_dir)
    return len(times), max(times) if times else None


def classify_gate(
    row: dict[str, str],
    *,
    source_exists: bool,
    log: dict[str, str],
    missing_pp: list[str],
    mdot_count: int,
    has_wallheatflux: bool,
) -> tuple[str, list[str]]:
    flags: list[str] = []
    if not source_exists:
        return "missing_source", ["source_path_missing"]
    if missing_pp:
        flags.append("missing_required_postprocessing")
    if mdot_count < len(MDOT_MONITORS):
        flags.append("missing_mdot_monitor")
    if not has_wallheatflux:
        flags.append("missing_wallheatflux")
    if log["tail_signal15"] == "yes":
        flags.append("signal15_tail")
    if log["tail_convergence_monitor"] != "yes":
        flags.append("no_tail_convergence_monitor")

    if row["fluid_variant"] == "kirst":
        return "historical_kirst_only", flags or ["historical_kirst_policy"]
    if row["case_id"] not in {PRIMARY_CASE, UPPER_ENDPOINT_CASE}:
        return "inventory_only", flags or ["secondary_jin_coverage"]
    if missing_pp or mdot_count < len(MDOT_MONITORS) or not has_wallheatflux:
        return "partial_needs_continuation", flags
    if row["mesh_level"] == "coarse":
        flags.append("coarse_source_must_reconcile_with_repo_mainline_continuation")
        return "partial_needs_coarse_reconciliation", flags
    if log["foamrun_terminal_state"] == "clean_end" and log["tail_convergence_monitor"] == "yes":
        return "admitted_for_gci_input", flags or ["none"]
    return "partial_needs_continuation", flags


def format_number(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return ""
    return f"{number:.12g}"


def build_rows(inventory: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    catalog_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    endpoint_rows: list[dict[str, Any]] = []

    for raw in inventory:
        case_root = Path(raw["source_path"])
        exists = case_root.is_dir()
        proc_dir = raw.get("proc_dir", "")
        solver_count, latest_solver = latest_solver_time(case_root, proc_dir) if exists else (0, None)
        latest_pp = latest_postprocessing_time(case_root) if exists else None
        families = postprocessing_families(case_root) if exists else set()
        missing_pp = [name for name in REQUIRED_POSTPROCESSING if name not in families]
        log = log_status(case_root) if exists else {
            "foamrun_terminal_state": "missing_source",
            "tail_signal15": "no",
            "tail_convergence_monitor": "no",
            "tail_convergence_line": "",
        }
        mdot_count = sum(1 for monitor in MDOT_MONITORS if (case_root / "postProcessing" / monitor).is_dir())
        has_wallheatflux = (case_root / "postProcessing/wallHeatFlux").is_dir()
        gate, flags = classify_gate(
            raw,
            source_exists=exists,
            log=log,
            missing_pp=missing_pp,
            mdot_count=mdot_count,
            has_wallheatflux=has_wallheatflux,
        )
        category, admission_bucket, fit_use_status = category_for(raw)
        sid = source_id(raw["case_id"], raw["mesh_level"])
        independence_group = f"{raw['case_id']}_mesh_family"
        mesh_status = MESH_STATUS_BY_GATE.get(gate, "mesh_family_candidate")
        source_note = (
            "External Ethan mesh-family source; not staged or registered by this package."
            if exists
            else "Source path missing during quality gate."
        )

        catalog_rows.append(
            {
                "source_id": sid,
                "case_name": raw["case_name"],
                "case_id": raw["case_id"],
                "fluid_variant": raw["fluid_variant"],
                "mesh_level": raw["mesh_level"],
                "mesh_status": mesh_status,
                "run_class": "nominal_mesh_refinement" if raw["fluid_variant"] == "jin" else "historical_kirst_mesh_refinement",
                "independence_group_id": independence_group,
                "source_path": raw["source_path"],
                "source_exists": "yes" if exists else "no",
                "proc_dir": proc_dir,
                "nprocs": raw.get("nprocs", ""),
                "cell_count": raw.get("cell_count", ""),
                "mesh_group_id": raw.get("mesh_group_id", ""),
                "first_cell_size": raw.get("first_cell_size", ""),
                "bulk_cell_size": raw.get("bulk_cell_size", ""),
                "stored_time_dir_count": solver_count or raw.get("stored_time_dir_count", ""),
                "latest_solver_time_s": format_number(latest_solver) or raw.get("latest_solver_time_s", ""),
                "latest_postprocessing_time_s": format_number(latest_pp) or raw.get("latest_postprocessing_time_s", ""),
                "category": category,
                "admission_bucket": admission_bucket,
                "fit_use_status": fit_use_status,
                "provenance_notes": source_note,
            }
        )
        quality_rows.append(
            {
                "source_id": sid,
                "case_id": raw["case_id"],
                "mesh_level": raw["mesh_level"],
                "fluid_variant": raw["fluid_variant"],
                "source_path": raw["source_path"],
                "source_exists": "yes" if exists else "no",
                **log,
                "latest_solver_time_s": format_number(latest_solver) or raw.get("latest_solver_time_s", ""),
                "latest_postprocessing_time_s": format_number(latest_pp) or raw.get("latest_postprocessing_time_s", ""),
                "stored_time_dir_count": solver_count or raw.get("stored_time_dir_count", ""),
                "postprocessing_family_count": len(families),
                "missing_required_postprocessing": ";".join(missing_pp) if missing_pp else "none",
                "mdot_monitor_count": mdot_count,
                "wallheatflux_present": "yes" if has_wallheatflux else "no",
                "yplus_present": "yes" if (case_root / "postProcessing/yPlus").is_dir() else "no",
                "gate_verdict": gate,
                "quality_flags": ";".join(flags) if flags else "none",
            }
        )

        if raw["case_id"] in ENDPOINT_CASES and raw["fluid_variant"] == "jin" and exists:
            for monitor in MDOT_MONITORS:
                series, source_file = merge_scalar_restart_series(case_root / "postProcessing" / monitor, "surfaceFieldValue.dat")
                summary = summarize_series(series)
                endpoint_rows.append(
                    {
                        "source_id": sid,
                        "case_id": raw["case_id"],
                        "mesh_level": raw["mesh_level"],
                        "quantity": "mdot",
                        "monitor": monitor,
                        **summary,
                        "units": "kg/s",
                        "source_file": source_file,
                    }
                )
            wall_series, source_file = wallheatflux_series(case_root)
            for quantity, series in wall_series.items():
                endpoint_rows.append(
                    {
                        "source_id": sid,
                        "case_id": raw["case_id"],
                        "mesh_level": raw["mesh_level"],
                        "quantity": quantity,
                        "monitor": "wallHeatFlux",
                        **summarize_series(series),
                        "units": "W",
                        "source_file": source_file,
                    }
                )
    return catalog_rows, quality_rows, endpoint_rows


def endpoint_value_map(endpoint_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], float]:
    values: dict[tuple[str, str, str], float] = {}
    mdot_by_source: dict[tuple[str, str], list[float]] = {}
    for row in endpoint_rows:
        value = numeric(row.get("mean_value"))
        if value is None:
            continue
        key = (row["case_id"], row["mesh_level"])
        if row["quantity"] == "mdot":
            mdot_by_source.setdefault(key, []).append(abs(value))
        elif row["quantity"] in {"wall_gross_duty_w", "wall_heat_in_w", "wall_heat_out_w", "wall_net_q_w"}:
            values[(row["case_id"], row["mesh_level"], row["quantity"])] = value
    for key, vals in mdot_by_source.items():
        if vals:
            values[(key[0], key[1], "mdot_abs_mean_kg_s")] = mean(vals)
    return values


def quality_map(quality_rows: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    return {(row["case_id"], row["mesh_level"]): row["gate_verdict"] for row in quality_rows}


def build_gci_matrix(endpoint_rows: list[dict[str, Any]], quality_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values = endpoint_value_map(endpoint_rows)
    gates = quality_map(quality_rows)
    qois = [
        ("mdot_abs_mean_kg_s", "kg/s"),
        ("wall_gross_duty_w", "W"),
        ("wall_heat_in_w", "W"),
        ("wall_heat_out_w", "W"),
        ("wall_net_q_w", "W"),
    ]
    out: list[dict[str, Any]] = []
    for case_id in [PRIMARY_CASE, UPPER_ENDPOINT_CASE]:
        for quantity, units in qois:
            coarse = values.get((case_id, "coarse", quantity))
            medium = values.get((case_id, "medium", quantity))
            fine = values.get((case_id, "fine", quantity))
            gate_values = {
                "coarse": gates.get((case_id, "coarse"), "missing"),
                "medium": gates.get((case_id, "medium"), "missing"),
                "fine": gates.get((case_id, "fine"), "missing"),
            }
            complete = all(value is not None for value in (coarse, medium, fine))
            all_ready = all(gate_values[level] == "admitted_for_gci_input" for level in ("coarse", "medium", "fine"))
            if not complete:
                status = "blocked_missing_qoi"
                reason = "one_or_more_mesh_levels_missing_qoi"
            elif all_ready:
                status = "ready_for_gci_calculation"
                reason = "complete_triplet_and_all_levels_gci_ready"
            elif case_id == PRIMARY_CASE and gate_values["medium"] == "admitted_for_gci_input" and gate_values["fine"] == "admitted_for_gci_input":
                status = "partial_needs_coarse_reconciliation"
                reason = "medium_and_fine_ready_but_external_coarse_must_reconcile_with_mainline_continuation"
            else:
                status = "partial_needs_continuation_or_gate"
                reason = "at_least_one_level_not_admitted_for_gci_input"
            out.append(
                {
                    "independence_group_id": f"{case_id}_mesh_family",
                    "case_id": case_id,
                    "quantity": quantity,
                    "units": units,
                    "coarse_value": format_number(coarse),
                    "medium_value": format_number(medium),
                    "fine_value": format_number(fine),
                    "coarse_gate_verdict": gate_values["coarse"],
                    "medium_gate_verdict": gate_values["medium"],
                    "fine_gate_verdict": gate_values["fine"],
                    "triplet_status": status,
                    "reason": reason,
                }
            )
    return out


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Salt Mesh Refinement Quality Gate

Generated: `{summary['generated_at']}`

## Scope

This package implements the first categorization and lightweight postProcessing
quality gate for Ethan's Salt `coarse/`, `medium/`, and `fine` mesh-family
source tree. It is read-only over the source cases and does not stage, register,
reconstruct, or mutate solver outputs.

## Outputs

- `mesh_case_catalog.csv`: all 24 mesh cases with source paths, mesh metadata,
  categorization, admission bucket, and provenance labels.
- `mesh_quality_gate.csv`: log-tail status, convergenceMonitor status,
  postProcessing availability, and gate verdict per case.
- `endpoint_postprocessing_summary.csv`: bounded tail-window summaries from the
  latest restart-segment monitor files for Salt 2 Jin and Salt 4 Jin endpoint
  families.
- `gci_candidate_matrix.csv`: per-QoI triplet readiness for Salt 2/4 Jin.
- `closure_observation_update_recommendations.md`: how future observation-table
  work should consume these results.
- `summary.json`: machine-readable counts and verdict summary.

## Verdict Summary

- Total catalog rows: `{summary['catalog_count']}`
- Endpoint summary rows: `{summary['endpoint_summary_count']}`
- Gate verdict counts: `{summary['gate_verdict_counts']}`
- GCI triplet status counts: `{summary['gci_triplet_status_counts']}`

## Interpretation

Salt 2 Jin remains the first mesh-family target: medium and fine are admitted by
this lightweight gate, but the external coarse source is still held for
reconciliation against the repo's current mainline continuation. Salt 4 Jin
remains the required upper endpoint but is partial because medium/fine source
logs tail with signal-15/no clean convergenceMonitor evidence in this gate.
Monitor statistics are screening signals only: large monitor files are parsed
from a bounded tail window of the latest restart segment, not a full reconstructed
history.

Kirst rows remain historical provenance only. No row from this package should be
used directly for closure fitting until a future task updates the canonical
closure-observation contract with explicit mesh uncertainty and fit/validation
flags.
"""
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def write_closure_recommendations(path: Path) -> None:
    text = """# Closure Observation Update Recommendations

Do not edit the July 8 `closure_observations.csv` from this quality-gate pass.
Future observation-table work should consume `mesh_case_catalog.csv`,
`mesh_quality_gate.csv`, and `gci_candidate_matrix.csv` as qualifiers.

Recommended mapping:

- keep existing coarse Salt 2/3/4 Jin mainline rows as current central closure
  evidence until coarse source reconciliation is complete;
- attach `mesh_status=mesh_family_candidate` to rows whose mesh family exists
  but lacks a defensible GCI;
- attach `mesh_status=mesh_gci_ready` only after a later task computes and
  validates GCI from a complete, monotone, admitted triplet;
- keep `fit_use_status=held_for_mesh_uq` for mesh-family rows until the GCI
  package decides whether they update central values or only uncertainty bands;
- keep every Kirst row excluded from current mainline fits unless a dated task
  explicitly re-admits Kirst.

The next closure-correlation retry should wait until Salt 2 Jin coarse
reconciliation and Salt 4 Jin continuation/quality gating are resolved.
"""
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    out = ensure_dir(Path(args.output_dir))
    inventory = read_csv(input_path)
    catalog, quality, endpoints = build_rows(inventory)
    gci = build_gci_matrix(endpoints, quality)

    write_csv(out / "mesh_case_catalog.csv", catalog, CATALOG_FIELDS)
    write_csv(out / "mesh_quality_gate.csv", quality, QUALITY_FIELDS)
    write_csv(out / "endpoint_postprocessing_summary.csv", endpoints, ENDPOINT_FIELDS)
    write_csv(out / "gci_candidate_matrix.csv", gci, GCI_FIELDS)
    write_closure_recommendations(out / "closure_observation_update_recommendations.md")

    gate_counts = Counter(row["gate_verdict"] for row in quality)
    gci_counts = Counter(row["triplet_status"] for row in gci)
    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-228",
        "input_inventory": rel(input_path),
        "output_dir": rel(out),
        "catalog_count": len(catalog),
        "quality_gate_count": len(quality),
        "endpoint_summary_count": len(endpoints),
        "gci_candidate_count": len(gci),
        "gate_verdict_counts": dict(sorted(gate_counts.items())),
        "gci_triplet_status_counts": dict(sorted(gci_counts.items())),
        "source_tree_read_only": True,
        "registry_updated": False,
        "staging_updated": False,
        "closure_observations_updated": False,
        "generated_files": [
            rel(out / "mesh_case_catalog.csv"),
            rel(out / "mesh_quality_gate.csv"),
            rel(out / "endpoint_postprocessing_summary.csv"),
            rel(out / "gci_candidate_matrix.csv"),
            rel(out / "closure_observation_update_recommendations.md"),
            rel(out / "README.md"),
            rel(out / "summary.json"),
        ],
    }
    write_json(out / "summary.json", summary)
    write_readme(out / "README.md", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
