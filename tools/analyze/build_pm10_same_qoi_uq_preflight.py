#!/usr/bin/env python3
"""Build PM10 same-QOI mesh/time UQ preflight."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
DEFAULT_TARGETS = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets"
    / "pm10_same_window_residual_targets.csv"
)
DEFAULT_PLANE_TARGETS = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets"
    / "pm10_plane_pressure_targets.csv"
)
DEFAULT_TERMINAL_DRIFT = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"
    / "pm10_terminal_drift.csv"
)
DEFAULT_OUTPUT_DIR = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_qoi_uq_preflight"

MESH_FIELDS = [
    "case_key",
    "same_qoi_formula_id",
    "eligible_same_qoi_mesh_members",
    "mesh_levels",
    "residual_span_pa",
    "relative_span_to_reference",
    "mesh_uq_status",
    "admission_use",
    "source_paths",
]
TIME_FIELDS = [
    "case_key",
    "same_qoi_formula_id",
    "available_same_qoi_time_members",
    "representative_times_s",
    "terminal_drift_status",
    "time_window_status",
    "admission_use",
    "source_paths",
]
GATE_FIELDS = [
    "case_key",
    "mesh_uq_status",
    "time_window_status",
    "same_qoi_uq_gate",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "blockers",
]
MANIFEST_FIELDS = ["source_id", "path", "exists", "role"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, precision: int = 10) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "" if value is None else str(value)
    return f"{parsed:.{precision}g}"


def unique_join(values: Iterable[str]) -> str:
    seen: list[str] = []
    for value in values:
        for part in str(value).split(";"):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
    return ";".join(seen)


def by_case(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row.get("case_key", ""), []).append(row)
    return grouped


def residual_value(row: dict[str, str]) -> float | None:
    metric = row.get("residual_metric", "pm10_pressure_partial_residual_pa")
    return parse_float(row.get(metric) or row.get("pm10_pressure_partial_residual_pa"))


def mesh_rows(targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped = by_case(targets)
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        members = grouped.get(case_key, [])
        values = [value for row in members if (value := residual_value(row)) is not None]
        mesh_levels = [row.get("mesh_level", "pm10_corrected_coarse") for row in members]
        source_paths = unique_join(row.get("source_paths", "") for row in members)
        if len(set(mesh_levels)) >= 3 and len(values) >= 3:
            span = max(values) - min(values)
            reference = values[-1]
            rel_span = abs(span / reference) if reference else None
            status = "diagnostic_same_qoi_mesh_spread_available_not_GCI"
            admission = "diagnostic_only_pending_gci_policy"
        else:
            span = None
            rel_span = None
            status = "missing_no_same_qoi_mesh_family"
            admission = "forbidden_until_same_qoi_mesh_family_available"
        rows.append(
            {
                "case_key": case_key,
                "same_qoi_formula_id": "pm10_pressure_partial_residual_v1",
                "eligible_same_qoi_mesh_members": str(len(set(mesh_levels))),
                "mesh_levels": unique_join(mesh_levels),
                "residual_span_pa": fmt(span),
                "relative_span_to_reference": fmt(rel_span),
                "mesh_uq_status": status,
                "admission_use": admission,
                "source_paths": source_paths,
            }
        )
    return rows


def terminal_status(row: dict[str, str] | None) -> str:
    if not row:
        return "missing_terminal_drift_row"
    if row.get("plateau_like") == "True" and row.get("strict_log_status") == "pass":
        return "terminal_drift_pass_not_time_uq"
    return "terminal_drift_not_pass"


def time_rows(plane_targets: list[dict[str, str]], terminal_drift: list[dict[str, str]]) -> list[dict[str, Any]]:
    planes = by_case(plane_targets)
    drift_by_case = {row.get("case_key", ""): row for row in terminal_drift}
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        times = sorted({row.get("representative_time_s", "") for row in planes.get(case_key, []) if row.get("representative_time_s", "")})
        status = terminal_status(drift_by_case.get(case_key))
        if len(times) >= 2:
            window_status = "same_qoi_neighbor_windows_available"
            admission = "diagnostic_time_spread_available"
        else:
            window_status = "missing_no_same_qoi_neighbor_windows"
            admission = "forbidden_until_time_uq_available"
        rows.append(
            {
                "case_key": case_key,
                "same_qoi_formula_id": "pm10_pressure_partial_residual_v1",
                "available_same_qoi_time_members": str(len(times)),
                "representative_times_s": ";".join(times),
                "terminal_drift_status": status,
                "time_window_status": window_status,
                "admission_use": admission,
                "source_paths": unique_join([*(row.get("source_paths", "") for row in planes.get(case_key, [])), rel(DEFAULT_TERMINAL_DRIFT)]),
            }
        )
    return rows


def gate_rows(mesh: list[dict[str, Any]], time: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mesh_by_case = {row["case_key"]: row for row in mesh}
    time_by_case = {row["case_key"]: row for row in time}
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        m = mesh_by_case[case_key]
        t = time_by_case[case_key]
        mesh_ok = not str(m["mesh_uq_status"]).startswith("missing")
        time_ok = not str(t["time_window_status"]).startswith("missing")
        blockers = []
        if not mesh_ok:
            blockers.append("same_qoi_mesh_uq_missing")
        if not time_ok:
            blockers.append("same_qoi_time_uq_missing")
        gate = "same_qoi_uq_pass" if mesh_ok and time_ok else "same_qoi_uq_blocked"
        rows.append(
            {
                "case_key": case_key,
                "mesh_uq_status": m["mesh_uq_status"],
                "time_window_status": t["time_window_status"],
                "same_qoi_uq_gate": gate,
                "fit_allowed_now": "no",
                "model_selection_allowed_now": "no",
                "runtime_input_allowed_now": "no",
                "blockers": unique_join(blockers),
            }
        )
    return rows


def source_manifest(targets_path: Path, plane_targets_path: Path, terminal_drift_path: Path) -> list[dict[str, Any]]:
    return [
        {"source_id": "pm10_same_window_residual_targets", "path": rel(targets_path), "exists": str(targets_path.exists()).lower(), "role": "PM10 same-QOI residual target rows"},
        {"source_id": "pm10_plane_pressure_targets", "path": rel(plane_targets_path), "exists": str(plane_targets_path.exists()).lower(), "role": "PM10 retained-window plane pressure rows"},
        {"source_id": "pm10_terminal_drift", "path": rel(terminal_drift_path), "exists": str(terminal_drift_path.exists()).lower(), "role": "terminal stability evidence, not same-QOI time UQ"},
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {summary["targets_path"]}
tags: [pm10, same-qoi, uq, mesh, time]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Same-QOI UQ Preflight

Terminal drift is recorded as stability evidence, but it is not treated as
same-QOI time-window uncertainty. Current PM10 rows remain blocked on same-QOI
mesh/time UQ unless matching mesh-family and neighbor-window members are present.
""",
        encoding="utf-8",
    )


def build_package(
    targets_path: Path = DEFAULT_TARGETS,
    plane_targets_path: Path = DEFAULT_PLANE_TARGETS,
    terminal_drift_path: Path = DEFAULT_TERMINAL_DRIFT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    mesh = mesh_rows(read_csv(targets_path))
    time = time_rows(read_csv(plane_targets_path), read_csv(terminal_drift_path))
    gates = gate_rows(mesh, time)
    csv_dump(output_dir / "pm10_same_qoi_mesh_uq_status.csv", MESH_FIELDS, mesh)
    csv_dump(output_dir / "pm10_same_qoi_time_uq_status.csv", TIME_FIELDS, time)
    csv_dump(output_dir / "pm10_uq_gate.csv", GATE_FIELDS, gates)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, source_manifest(targets_path, plane_targets_path, terminal_drift_path))
    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(gates),
        "same_qoi_uq_pass_cases": sum(row["same_qoi_uq_gate"] == "same_qoi_uq_pass" for row in gates),
        "same_qoi_uq_blocked_cases": sum(row["same_qoi_uq_gate"] == "same_qoi_uq_blocked" for row in gates),
        "fit_allowed_now": 0,
        "model_selection_allowed_now": 0,
        "runtime_input_allowed_now": 0,
        "targets_path": rel(targets_path),
        "output_dir": rel(output_dir),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--plane-targets", type=Path, default=DEFAULT_PLANE_TARGETS)
    parser.add_argument("--terminal-drift", type=Path, default=DEFAULT_TERMINAL_DRIFT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(build_package(args.targets, args.plane_targets, args.terminal_drift, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
