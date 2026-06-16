#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_case_metadata,
)

OF_ENV_SCRIPT = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-02_runtime_recovery" / "scripts" / "of13-env.sh"
EXTRA_LD_LIBRARY = "/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data"
OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_section_transport_package"
TEMP_ROOT = WORKSPACE_ROOT / "tmp_extract" / "ethan_section_transport"
METADATA_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
VALIDATION_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
REPRESENTATIVE_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "representative_case_selection.csv"
ALL_SALT_STATUS_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "all_salt_case_status.csv"

MAJOR_SECTION_PATCH_PAIRS = {
    "lower_leg": ("ncc_pipeleg_lower_01_fitting_start", "ncc_pipeleg_lower_09_fitting_end"),
    "right_leg": ("ncc_pipeleg_right_01_lower_start", "ncc_pipeleg_right_03_upper_end"),
    "upper_leg": ("ncc_pipeleg_upper_01_straight_start", "ncc_pipeleg_upper_09_straight_end"),
    "left_leg": ("ncc_pipeleg_left_01_upper_start", "ncc_pipeleg_left_07_lower_end"),
    "test_section_branch": ("ncc_pipeleg_left_03_fitting_start", "ncc_pipeleg_left_05_fitting_end"),
    "connector_span": ("ncc_pipeleg_left_02_connector_end", "ncc_pipeleg_left_06_connector_start"),
}
FACE_ZONES: list[str] = []
HEAT_KEYS = [
    "ambient_proxy_w",
    "ambient_noncooling_proxy_w",
    "cooling_branch_total_removal_w",
    "cooling_branch_excess_w",
    "net_total_q_w",
    "section_downcomer_net_q_w",
    "section_heater_net_q_w",
    "section_upcomer_net_q_w",
    "section_test_section_net_q_w",
    "section_cooling_branch_net_q_w",
    "section_upper_transport_net_q_w",
    "section_lower_transport_net_q_w",
    "section_junctions_net_q_w",
    "section_other_net_q_w",
]
HEAT_LABELS = {
    "ambient_proxy_w": "Derived ambient-loss proxy",
    "ambient_noncooling_proxy_w": "Ambient-loss proxy excluding cooling branch excess",
    "cooling_branch_total_removal_w": "Cooling branch total heat removal",
    "cooling_branch_excess_w": "Cooling branch excess over operating cooling duty",
    "net_total_q_w": "Net total wall heat",
    "section_downcomer_net_q_w": "Downcomer net wall heat",
    "section_heater_net_q_w": "Heater net wall heat",
    "section_upcomer_net_q_w": "Upcomer net wall heat",
    "section_test_section_net_q_w": "Test-section net wall heat",
    "section_cooling_branch_net_q_w": "Cooling branch net wall heat",
    "section_upper_transport_net_q_w": "Upper transport net wall heat",
    "section_lower_transport_net_q_w": "Lower transport net wall heat",
    "section_junctions_net_q_w": "Junction-region net wall heat",
    "section_other_net_q_w": "Other net wall heat",
}


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


s2 = load_module("build_salt2_behavior_package", ROOT / "tools" / "analyze" / "build_salt2_behavior_package.py")
rep = load_module("build_ethan_report_package", ROOT / "tools" / "analyze" / "build_ethan_report_package.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a reusable section-transport package for Ethan salt cases. "
            "This performs non-destructive pressure extraction from interface patches "
            "and combines it with existing wall-heat time histories."
        )
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Repeat to override the default salt-case source set.",
    )
    parser.add_argument(
        "--skip-pressure-extraction",
        action="store_true",
        help="Reuse any existing pressure outputs in the temp extraction roots instead of rerunning OpenFOAM postprocessing.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def default_source_ids() -> list[str]:
    rows = load_csv_rows(METADATA_CSV)
    return [row["source_id"] for row in rows if "salt" in row.get("source_id", "")]


def load_runtime_context(source_id: str) -> tuple[Path, Path, dict[str, Any], dict[str, str], dict[str, str]]:
    metadata_map = {row["source_id"]: row for row in load_csv_rows(METADATA_CSV) if row.get("source_id")}
    validation_map = {row["source_id"]: row for row in load_csv_rows(VALIDATION_CSV) if row.get("source_id")}
    meta_row = metadata_map.get(source_id, {})
    runtime_root = Path(meta_row.get("active_runtime_root") or meta_row.get("source_root") or get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)["source_root"]).resolve()
    source_root = Path(meta_row.get("source_root") or runtime_root).resolve()
    metadata = load_case_metadata(runtime_root) or load_case_metadata(source_root) or {}
    return source_root, runtime_root, metadata, meta_row, validation_map.get(source_id, {})


def latest_processor_time(source_root: Path) -> str:
    candidate_roots = sorted(path for path in source_root.iterdir() if path.is_dir() and path.name.startswith("processors"))
    latest_value: float | None = None
    latest_label = ""
    for root in candidate_roots:
        times = sorted(
            child.name
            for child in root.iterdir()
            if child.is_dir() and child.name.replace(".", "", 1).isdigit()
        )
        if not times:
            continue
        current_value = float(times[-1])
        if latest_value is None or current_value > latest_value:
            latest_value = current_value
            latest_label = times[-1]
    return latest_label


def ensure_symlink(link_path: Path, target: Path) -> None:
    if link_path.is_symlink() or link_path.exists():
        if link_path.is_symlink() and link_path.resolve() == target.resolve():
            return
        if link_path.is_dir() and not link_path.is_symlink():
            return
        link_path.unlink()
    link_path.symlink_to(target)


def ensure_extract_case(source_id: str, runtime_root: Path) -> Path:
    case_dir = ensure_dir(TEMP_ROOT / source_id)
    ensure_symlink(case_dir / "0", runtime_root / "0")
    ensure_symlink(case_dir / "constant", runtime_root / "constant")
    if (runtime_root / "dynamicCode").exists():
        ensure_symlink(case_dir / "dynamicCode", runtime_root / "dynamicCode")
    for processors_dir in runtime_root.glob("processors*"):
        ensure_symlink(case_dir / processors_dir.name, processors_dir)
    shutil.copytree(runtime_root / "system", case_dir / "system", dirs_exist_ok=True)
    if (runtime_root / "case_config.yaml").exists():
        shutil.copy2(runtime_root / "case_config.yaml", case_dir / "case_config.yaml")
    return case_dir


def shell_run(case_dir: Path, command: str) -> None:
    env_cmd = (
        f"source {shlex.quote(str(OF_ENV_SCRIPT))} && "
        f"export LD_LIBRARY_PATH={shlex.quote(EXTRA_LD_LIBRARY)}:${{LD_LIBRARY_PATH:-}} && "
        f"{command}"
    )
    subprocess.run(["bash", "-lc", env_cmd], cwd=str(case_dir), check=True)


def write_pressure_dict(path: Path, patch_names: list[str], face_zones: list[str]) -> list[str]:
    object_names: list[str] = []
    lines = [
        "FoamFile",
        "{",
        "    format      ascii;",
        "    class       dictionary;",
        "    location    \"system\";",
        "    object      functions;",
        "}",
        "",
    ]
    for patch_name in patch_names:
        object_name = f"patch_{patch_name}"
        object_names.append(object_name)
        lines.extend(
            [
                f"{object_name}",
                "{",
                "    type            surfaceFieldValue;",
                "    libs            (\"libfieldFunctionObjects.so\");",
                "    writeControl    timeStep;",
                "    writeInterval   1;",
                "    surfaceFormat   none;",
                "    writeFields     false;",
                "    writeToFile     true;",
                "    log             false;",
                f"    patch           {patch_name};",
                "    operation       areaAverage;",
                "    fields          (p p_rgh);",
                "}",
                "",
            ]
        )
    for face_zone in face_zones:
        object_name = f"faceZone_{face_zone}"
        object_names.append(object_name)
        lines.extend(
            [
                f"{object_name}",
                "{",
                "    type            surfaceFieldValue;",
                "    libs            (\"libfieldFunctionObjects.so\");",
                "    writeControl    timeStep;",
                "    writeInterval   1;",
                "    surfaceFormat   none;",
                "    writeFields     false;",
                "    writeToFile     true;",
                "    log             false;",
                f"    faceZone        {face_zone};",
                "    operation       areaAverage;",
                "    fields          (p p_rgh);",
                "}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return object_names


def parse_surface_field_value(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "selection": "",
        "faces": "",
        "area": "",
        "time": "",
        "areaAverage_p": "",
        "areaAverage_p_rgh": "",
    }
    with path.open("r", encoding="utf-8") as handle:
        rows = [line.rstrip("\n") for line in handle if line.strip()]
    for line in rows:
        if line.startswith("# Selection"):
            payload["selection"] = line.split(":", 1)[1].strip()
        elif line.startswith("# Faces"):
            payload["faces"] = line.split(":", 1)[1].strip()
        elif line.startswith("# Area"):
            payload["area"] = line.split(":", 1)[1].strip()
        elif line.startswith("# Time"):
            continue
        elif not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 3:
                payload["time"] = parts[0]
                payload["areaAverage_p"] = parts[1]
                payload["areaAverage_p_rgh"] = parts[2]
    return payload


def pressure_outputs_ready(case_dir: Path, object_names: list[str], latest_time: str) -> bool:
    for object_name in object_names:
        path = case_dir / "postProcessing" / object_name / latest_time / "surfaceFieldValue.dat"
        if not path.exists():
            return False
    return True


def extract_pressure_rows(source_id: str, runtime_root: Path, skip_pressure_extraction: bool) -> list[dict[str, Any]]:
    case_dir = ensure_extract_case(source_id, runtime_root)
    latest_time = latest_processor_time(runtime_root)
    if not latest_time:
        return []
    patch_names = sorted({name for pair in MAJOR_SECTION_PATCH_PAIRS.values() for name in pair})
    functions_path = case_dir / "system" / "functions"
    object_names = write_pressure_dict(functions_path, patch_names, FACE_ZONES)
    root_time_dir = case_dir / latest_time
    if not skip_pressure_extraction or not root_time_dir.exists():
        if not root_time_dir.exists():
            shell_run(case_dir, f"reconstructPar -case {shlex.quote(str(case_dir))} -time {latest_time} -fields '(p p_rgh)'")
        elif not (root_time_dir / "p").exists() or not (root_time_dir / "p_rgh").exists():
            shell_run(case_dir, f"reconstructPar -case {shlex.quote(str(case_dir))} -time {latest_time} -fields '(p p_rgh)'")
        if not skip_pressure_extraction or not pressure_outputs_ready(case_dir, object_names, latest_time):
            shell_run(case_dir, f"foamPostProcess -case {shlex.quote(str(case_dir))} -dict {shlex.quote(str(functions_path))} -time {latest_time}")
    rows: list[dict[str, Any]] = []
    for object_name in object_names:
        path = case_dir / "postProcessing" / object_name / latest_time / "surfaceFieldValue.dat"
        if not path.exists():
            continue
        payload = parse_surface_field_value(path)
        kind = "patch" if object_name.startswith("patch_") else "faceZone"
        target_name = object_name.split("_", 1)[1]
        rows.append(
            {
                "source_id": source_id,
                "runtime_root": str(runtime_root),
                "extract_case_root": str(case_dir),
                "latest_time": latest_time,
                "kind": kind,
                "target_name": target_name,
                **payload,
            }
        )
    return rows


def build_pressure_drop_rows(pressure_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in pressure_rows:
        if row["kind"] != "patch":
            continue
        grouped.setdefault(str(row["source_id"]), {})[str(row["target_name"])] = row
    section_rows: list[dict[str, Any]] = []
    for source_id, patch_map in sorted(grouped.items()):
        for section_name, (start_patch, end_patch) in MAJOR_SECTION_PATCH_PAIRS.items():
            start_row = patch_map.get(start_patch)
            end_row = patch_map.get(end_patch)
            if not start_row or not end_row:
                continue
            start_p = float(start_row["areaAverage_p"])
            end_p = float(end_row["areaAverage_p"])
            start_p_rgh = float(start_row["areaAverage_p_rgh"])
            end_p_rgh = float(end_row["areaAverage_p_rgh"])
            section_rows.append(
                {
                    "source_id": source_id,
                    "section_name": section_name,
                    "start_patch": start_patch,
                    "end_patch": end_patch,
                    "latest_time": start_row["latest_time"],
                    "start_p_pa": start_p,
                    "end_p_pa": end_p,
                    "delta_p_pa": end_p - start_p,
                    "abs_delta_p_pa": abs(end_p - start_p),
                    "start_p_rgh_pa": start_p_rgh,
                    "end_p_rgh_pa": end_p_rgh,
                    "delta_p_rgh_pa": end_p_rgh - start_p_rgh,
                    "abs_delta_p_rgh_pa": abs(end_p_rgh - start_p_rgh),
                    "sign_convention": "end minus start in geometric patch order; use the absolute columns for section-loss ranking.",
                }
            )
    return section_rows


def compute_heat_rows(source_id: str, runtime_root: Path, metadata: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    heat_rows = s2.parse_wall_heatflux_section_series(runtime_root, metadata)
    heat_time, heat_series = s2.rows_to_series(heat_rows, HEAT_KEYS)
    drift_rows: list[dict[str, Any]] = []
    latest_rows: list[dict[str, Any]] = []
    latest = heat_rows[-1] if heat_rows else {}
    for key in HEAT_KEYS:
        stats = s2.compute_last_window_stats(source_id, key, heat_time, heat_series.get(key, np.array([])), s2.LAST_WINDOW_COUNT)
        mean_value = stats.get("mean")
        slope_value = stats.get("slope_per_s")
        normalized = ""
        if mean_value not in ("", 0, 0.0) and slope_value not in ("", None):
            normalized = abs(float(slope_value)) / max(abs(float(mean_value)), 1.0)
        drift_rows.append(
            {
                "source_id": source_id,
                "metric": key,
                "metric_label": HEAT_LABELS.get(key, key),
                "window_count": stats.get("window_count", ""),
                "time_start_s": stats.get("time_start", ""),
                "time_end_s": stats.get("time_end", ""),
                "mean_w": stats.get("mean", ""),
                "std_w": stats.get("std", ""),
                "min_w": stats.get("min", ""),
                "max_w": stats.get("max", ""),
                "slope_per_s": stats.get("slope_per_s", ""),
                "end_minus_start_w": stats.get("end_minus_start", ""),
                "abs_slope_over_mean_per_s": normalized,
            }
        )
        latest_rows.append(
            {
                "source_id": source_id,
                "metric": key,
                "metric_label": HEAT_LABELS.get(key, key),
                "latest_time_s": latest.get("time", ""),
                "latest_value_w": latest.get(key, ""),
            }
        )
    return drift_rows, latest_rows


def build_manuscript_rows(
    representative_rows: list[dict[str, str]],
    pressure_drop_rows: list[dict[str, Any]],
    heat_latest_rows: list[dict[str, Any]],
    case_status_map: dict[str, dict[str, str]],
    validation_map: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rep_sources = {
        row["primary_manuscript_representative"]
        for row in representative_rows
        if row.get("primary_manuscript_representative")
    }
    pressure_by_source: dict[str, dict[str, dict[str, Any]]] = {}
    for row in pressure_drop_rows:
        pressure_by_source.setdefault(str(row["source_id"]), {})[str(row["section_name"])] = row
    heat_by_source: dict[str, dict[str, dict[str, Any]]] = {}
    for row in heat_latest_rows:
        heat_by_source.setdefault(str(row["source_id"]), {})[str(row["metric"])] = row
    manuscript_rows: list[dict[str, Any]] = []
    for source_id in sorted(rep_sources):
        pressure = pressure_by_source.get(source_id, {})
        heat = heat_by_source.get(source_id, {})
        status = case_status_map.get(source_id, {})
        validation = validation_map.get(source_id, {})
        manuscript_rows.append(
            {
                "source_id": source_id,
                "base_case_id": status.get("base_case_id", ""),
                "variant_label": status.get("variant_label", ""),
                "run_status": status.get("run_status", ""),
                "essential_steadiness_class": status.get("essential_steadiness_class", ""),
                "exp_tp_rmse_k": validation.get("exp_tp_rmse_k", ""),
                "exp_tw_rmse_k_excluding_tw10": validation.get("exp_tw_rmse_k", ""),
                "exp_mdot_abs_error_pct": validation.get("exp_mdot_abs_error_pct", ""),
                "exp_q_external_loss_abs_error_pct": validation.get("exp_q_external_loss_abs_error_pct", ""),
                "ambient_proxy_w": heat.get("ambient_proxy_w", {}).get("latest_value_w", ""),
                "cooling_branch_total_removal_w": heat.get("cooling_branch_total_removal_w", {}).get("latest_value_w", ""),
                "section_heater_net_q_w": heat.get("section_heater_net_q_w", {}).get("latest_value_w", ""),
                "section_test_section_net_q_w": heat.get("section_test_section_net_q_w", {}).get("latest_value_w", ""),
                "section_cooling_branch_net_q_w": heat.get("section_cooling_branch_net_q_w", {}).get("latest_value_w", ""),
                "section_downcomer_net_q_w": heat.get("section_downcomer_net_q_w", {}).get("latest_value_w", ""),
                "section_upcomer_net_q_w": heat.get("section_upcomer_net_q_w", {}).get("latest_value_w", ""),
                "lower_leg_abs_delta_p_rgh_pa": pressure.get("lower_leg", {}).get("abs_delta_p_rgh_pa", ""),
                "right_leg_abs_delta_p_rgh_pa": pressure.get("right_leg", {}).get("abs_delta_p_rgh_pa", ""),
                "upper_leg_abs_delta_p_rgh_pa": pressure.get("upper_leg", {}).get("abs_delta_p_rgh_pa", ""),
                "left_leg_abs_delta_p_rgh_pa": pressure.get("left_leg", {}).get("abs_delta_p_rgh_pa", ""),
                "test_section_branch_abs_delta_p_rgh_pa": pressure.get("test_section_branch", {}).get("abs_delta_p_rgh_pa", ""),
            }
        )
    return manuscript_rows


def write_readme(
    source_ids: list[str],
    pressure_drop_rows: list[dict[str, Any]],
    manuscript_rows: list[dict[str, Any]],
    case_status_map: dict[str, dict[str, str]],
) -> None:
    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for row in pressure_drop_rows:
        rows_by_source.setdefault(str(row["source_id"]), []).append(row)
    lines = [
        "# Ethan Section Transport Package",
        "",
        "This package adds a reusable section-transport layer on top of the June 4 Ethan reporting stack.",
        "",
        "## Scope",
        "",
        "- Extract latest-time section pressure information from non-destructively reconstructed `p` and `p_rgh` fields.",
        "- Reuse the existing `wallHeatFlux.dat` reductions to rank section-wise heat-transfer drift over the last analysis window.",
        "- Provide manuscript-facing summary rows for the current representative salt cases.",
        "",
        "## Important limitations",
        "",
        "- Pressure extraction is latest-time only in this first pass. It is meant to support section ranking and loop-resistance interpretation, not a full transient hydraulic history yet.",
        "- Pressure-drop signs follow the geometric `start -> end` patch ordering from the mesh naming. Use the absolute pressure-drop columns for loss ranking.",
        "- The current axial `h(x)` / `Nu(x)` analysis is not included here because the reconstructed root-level `T` field is not reliable enough for generic surface sampling in this workflow. The section heat and pressure products remain valid because they use `wallHeatFlux.dat`, existing probe outputs, and patch-averaged pressure fields only.",
        "- `TW10` remains excluded from manuscript RMSE scorecards elsewhere. This package does not change that rule.",
        "",
        "## Cases processed",
        "",
    ]
    for source_id in source_ids:
        status = case_status_map.get(source_id, {})
        lines.append(
            f"- `{source_id}`: `run_status={status.get('run_status', '')}`, `essential_steadiness_class={status.get('essential_steadiness_class', '')}`"
        )
    lines.extend(
        [
            "",
            "## Pressure sections",
            "",
            "The major section pressure drops are extracted between these non-conformal interface patches:",
            "",
        ]
    )
    for section_name, (start_patch, end_patch) in MAJOR_SECTION_PATCH_PAIRS.items():
        lines.append(f"- `{section_name}`: `{start_patch}` -> `{end_patch}`")
    lines.extend(
        [
            "",
            "## Current scientific use",
            "",
            "- The pressure-drop columns are suitable for first-pass loop-resistance comparisons across Jin, Kirst, and validation-style runs.",
            "- The section-heat drift rows are suitable for checking whether the net heat-balance tail is still moving materially in any section, even when the solver convergence monitor did not declare convergence.",
            "- The representative summary table is the manuscript-ready bridge product for the next write-up pass.",
            "",
            "## Representative snapshot",
            "",
        ]
    )
    for row in manuscript_rows:
        lines.append(
            "- "
            + f"`{row['source_id']}`: ambient proxy `{row['ambient_proxy_w']}` W, cooling branch `{row['cooling_branch_total_removal_w']}` W, "
            + f"test-section branch `|Δp_rgh|={row['test_section_branch_abs_delta_p_rgh_pa']}` Pa"
        )
    lines.append("")
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_scientific_notes(
    manuscript_rows: list[dict[str, Any]],
    representative_rows: list[dict[str, str]],
) -> None:
    rep_map = {row["primary_manuscript_representative"]: row for row in representative_rows if row.get("primary_manuscript_representative")}
    lines = [
        "# Scientific Write-up Notes",
        "",
        "## Observed outputs",
        "",
        "- Latest-time section pressure drops are now available for all processed salt rows using non-destructive OpenFOAM postprocessing on reconstructed `p` and `p_rgh` fields.",
        "- Section heat-transfer drift statistics are now available from the existing `wallHeatFlux.dat` time histories for every processed salt row.",
        "- The representative summary table joins these section-transport quantities to the previously generated validation metrics and usability classifications.",
        "",
        "## Interpretation",
        "",
        "- The section-pressure products are the first direct 3D basis for discussing loop resistance by branch instead of only using global mdot mismatch.",
        "- The section-heat drift products make it possible to separate cases that are globally flat from cases that still show a meaningful late-time drift in a specific branch or loss channel.",
        "- Because the reconstructed `T` field is not yet clean enough for generic surface sampling, the current package should be used for branch-scale resistance and heat accounting, not yet for definitive axial `h(x)` or `Nu(x)` claims.",
        "",
        "## Representative rows",
        "",
    ]
    for row in manuscript_rows:
        rep_meta = rep_map.get(str(row["source_id"]), {})
        lines.append(
            "- "
            + f"`{row['source_id']}` for `{rep_meta.get('base_case_id', row.get('base_case_id', ''))}`: "
            + f"TP RMSE `{row['exp_tp_rmse_k']}` K, TW RMSE excluding TW10 `{row['exp_tw_rmse_k_excluding_tw10']}` K, "
            + f"mdot error `{row['exp_mdot_abs_error_pct']}` %, external-loss error `{row['exp_q_external_loss_abs_error_pct']}` %."
        )
    lines.extend(
        [
            "",
            "## Next analytical step",
            "",
            "- Add a compute-node postprocessing path for clean transient `p_rgh` histories and axial surface sampling so the manuscript can move from branch-wise section metrics to true distance-resolved transport coefficients.",
            "",
        ]
    )
    (OUTPUT_DIR / "scientific_writeup_notes.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_ids = args.source_ids or default_source_ids()
    case_status_map = {row["source_id"]: row for row in load_csv_rows(ALL_SALT_STATUS_CSV) if row.get("source_id")}
    validation_map = {row["source_id"]: row for row in load_csv_rows(VALIDATION_CSV) if row.get("source_id")}
    representative_rows = load_csv_rows(REPRESENTATIVE_CSV)

    pressure_rows: list[dict[str, Any]] = []
    heat_drift_rows: list[dict[str, Any]] = []
    heat_latest_rows: list[dict[str, Any]] = []
    case_context_rows: list[dict[str, Any]] = []

    for source_id in source_ids:
        source_root, runtime_root, metadata, meta_row, validation_row = load_runtime_context(source_id)
        pressure_rows.extend(extract_pressure_rows(source_id, runtime_root, args.skip_pressure_extraction))
        drift_rows, latest_rows = compute_heat_rows(source_id, runtime_root, metadata)
        heat_drift_rows.extend(drift_rows)
        heat_latest_rows.extend(latest_rows)
        case_context_rows.append(
            {
                "source_id": source_id,
                "source_root": str(source_root),
                "runtime_root": str(runtime_root),
                "base_case_id": meta_row.get("base_case_id", ""),
                "variant_label": meta_row.get("variant_label", ""),
                "run_status": meta_row.get("run_status", ""),
                "essential_steadiness_class": case_status_map.get(source_id, {}).get("essential_steadiness_class", ""),
                "exp_tp_rmse_k": validation_row.get("exp_tp_rmse_k", ""),
                "exp_tw_rmse_k": validation_row.get("exp_tw_rmse_k", ""),
                "exp_mdot_abs_error_pct": validation_row.get("exp_mdot_abs_error_pct", ""),
                "exp_q_external_loss_abs_error_pct": validation_row.get("exp_q_external_loss_abs_error_pct", ""),
            }
        )

    pressure_drop_rows = build_pressure_drop_rows(pressure_rows)
    manuscript_rows = build_manuscript_rows(representative_rows, pressure_drop_rows, heat_latest_rows, case_status_map, validation_map)

    ensure_dir(OUTPUT_DIR)
    csv_dump(
        OUTPUT_DIR / "case_context.csv",
        list(case_context_rows[0].keys()) if case_context_rows else ["source_id"],
        case_context_rows,
    )
    csv_dump(
        OUTPUT_DIR / "pressure_surface_values.csv",
        list(pressure_rows[0].keys()) if pressure_rows else ["source_id", "target_name"],
        pressure_rows,
    )
    csv_dump(
        OUTPUT_DIR / "section_pressure_drops.csv",
        list(pressure_drop_rows[0].keys()) if pressure_drop_rows else ["source_id", "section_name"],
        pressure_drop_rows,
    )
    csv_dump(
        OUTPUT_DIR / "section_heat_drift.csv",
        list(heat_drift_rows[0].keys()) if heat_drift_rows else ["source_id", "metric"],
        heat_drift_rows,
    )
    csv_dump(
        OUTPUT_DIR / "section_heat_latest.csv",
        list(heat_latest_rows[0].keys()) if heat_latest_rows else ["source_id", "metric"],
        heat_latest_rows,
    )
    csv_dump(
        OUTPUT_DIR / "representative_section_summary.csv",
        list(manuscript_rows[0].keys()) if manuscript_rows else ["source_id"],
        manuscript_rows,
    )
    summary = {
        "generated_at": iso_timestamp(),
        "source_ids": source_ids,
        "pressure_row_count": len(pressure_rows),
        "pressure_drop_row_count": len(pressure_drop_rows),
        "heat_drift_row_count": len(heat_drift_rows),
        "heat_latest_row_count": len(heat_latest_rows),
        "representative_row_count": len(manuscript_rows),
        "notes": [
            "Pressure drops use latest-time patch-averaged p and p_rgh from reconstructed fields.",
            "Section heat drift uses the existing wallHeatFlux time-history reductions.",
            "Axial h(x) and Nu(x) are intentionally deferred until a cleaner T-field postprocessing path is in place.",
        ],
    }
    json_dump(OUTPUT_DIR / "summary.json", summary)
    write_readme(source_ids, pressure_drop_rows, manuscript_rows, case_status_map)
    write_scientific_notes(manuscript_rows, representative_rows)


if __name__ == "__main__":
    main()
