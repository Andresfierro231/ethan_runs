#!/usr/bin/env python3
"""Prepare and harvest the two-tap corner_lower_right raw endpoint sampler.

This is the executable follow-on to the two-tap raw endpoint contract.  It does
not admit a component K and does not fit F6.  The native continuation cases are
read-only; runtime sampling is staged under task-owned tmp space.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import stat
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK = "TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER"
DATE = "2026-07-18"
SLUG = "2026-07-18_two_tap_staged_endpoint_sampler"
OUT_REL = Path("work_products/2026-07/2026-07-18") / SLUG
OUT = ROOT / OUT_REL
TMP_REL = Path("tmp") / SLUG
TMP = ROOT / TMP_REL
PLAN = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan"
ROADMAP = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap"
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"
FUNCTION_OBJECT = "agentCTwoTapRawEndpointSurfaces"
TARGET_STATIONS = ("lower_leg__s04", "right_leg__s00")
TARGET_FEATURE = "corner_lower_right"
REQUIRED_FIELDS = ("p", "p_rgh", "U", "rho", "T")
RAW_FIELDS = [
    "case_id",
    "case_key",
    "source_id",
    "feature",
    "time_s",
    "tap_role",
    "station_label",
    "surface_label",
    "source_case_path",
    "sampled_surface_file",
    "sample_status",
    "face_count",
    "area_m2",
    "normal_x",
    "normal_y",
    "normal_z",
    "expected_positive_normal_policy",
    "p_pa",
    "p_rgh_pa",
    "rho_kg_m3",
    "T_K",
    "U_area_mean_x_m_s",
    "U_area_mean_y_m_s",
    "U_area_mean_z_m_s",
    "U_bulk_m_s",
    "U_bulk_normal_m_s",
    "mass_flux_kg_s",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "ordinary_recirculation_gate",
    "admission_status",
    "guardrail",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> int:
    data = list(rows)
    if fieldnames is None:
        fieldnames = list(data[0].keys()) if data else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(data)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.12g}" if math.isfinite(number) else ""


def vector_norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(part * part for part in vector))


def unit(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    norm = vector_norm(vector)
    if norm <= 0.0:
        return (float("nan"), float("nan"), float("nan"))
    return (vector[0] / norm, vector[1] / norm, vector[2] / norm)


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def load_targets() -> list[dict[str, str]]:
    rows = read_csv(PLAN / "target_feature_taps.csv")
    targets = [row for row in rows if row.get("feature") == TARGET_FEATURE]
    targets.sort(key=lambda row: row["case_id"])
    return targets


def load_contract_rows() -> list[dict[str, str]]:
    rows = read_csv(PLAN / "pressure_surface_sampling_contract.csv")
    return [row for row in rows if row.get("feature") == TARGET_FEATURE]


def validate_contract(targets: list[dict[str, str]], contract_rows: list[dict[str, str]]) -> None:
    if len(targets) != 3:
        raise RuntimeError(f"Expected 3 target rows, found {len(targets)}")
    if len(contract_rows) != 6:
        raise RuntimeError(f"Expected 6 pressure-surface contract rows, found {len(contract_rows)}")
    expected_times = {"salt_2": "7915", "salt_3": "7618", "salt_4": "10000"}
    for row in targets:
        case_id = row["case_id"]
        if row["time_window_s"] != expected_times[case_id]:
            raise RuntimeError(f"Unexpected time for {case_id}: {row['time_window_s']}")
        if row["upstream_station_label"] != "lower_leg__s04" or row["downstream_station_label"] != "right_leg__s00":
            raise RuntimeError(f"Unexpected station labels for {case_id}")
        if row["upstream_patch"] != "ncc_pipeleg_lower_09_fitting_end":
            raise RuntimeError(f"Unexpected upstream patch for {case_id}")
        if row["downstream_patch"] != "ncc_pipeleg_right_01_lower_start":
            raise RuntimeError(f"Unexpected downstream patch for {case_id}")


def load_mesh_stations(source_id: str) -> dict[str, dict[str, Any]]:
    path = MESH_ROOT / source_id / "mesh_stations.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["label"]: row for row in payload.get("stations", [])}


def parse_boundary_patches(path: Path) -> dict[str, dict[str, str]]:
    patches: dict[str, dict[str, str]] = {}
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    index = 0
    while index < len(lines):
        name = lines[index].strip()
        if not name or name.startswith(("/", "{", "}", "(")) or " " in name:
            index += 1
            continue
        if index + 1 >= len(lines) or lines[index + 1].strip() != "{":
            index += 1
            continue
        depth = 0
        meta: dict[str, str] = {}
        index += 1
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "{":
                depth += 1
            elif stripped == "}":
                depth -= 1
                if depth == 0:
                    break
            else:
                parts = stripped.rstrip(";").split()
                if len(parts) >= 2:
                    meta[parts[0]] = parts[1]
            index += 1
        if "type" in meta:
            patches[name] = meta
        index += 1
    return patches


def boundary_nfaces(source_case: Path, patch_name: str) -> int | None:
    boundary = source_case / "processors64/constant/polyMesh/boundary"
    if not boundary.exists():
        boundary = source_case / "constant/polyMesh/boundary"
    if not boundary.exists():
        return None
    meta = parse_boundary_patches(boundary).get(patch_name)
    if meta is None:
        return None
    try:
        return int(meta.get("nFaces", "0"))
    except ValueError:
        return None


def stage_case_dir(row: dict[str, str]) -> Path:
    return TMP / "staged_reconstructed" / row["case_key"]


def expected_vtk_path(row: dict[str, str], station_label: str) -> Path:
    return stage_case_dir(row) / "postProcessing" / FUNCTION_OBJECT / row["time_window_s"] / f"plane_{station_label}.vtk"


def expected_flow_normal(station: dict[str, Any]) -> tuple[tuple[float, float, float], str]:
    mesh_normal = (float(station["nx"]), float(station["ny"]), float(station["nz"]))
    # The July-1 section-mean products showed negative u_along_tangent at both
    # target endpoint labels; use the opposite station tangent as the declared
    # positive feature-flow direction for this corner sampler.
    normal = unit((-mesh_normal[0], -mesh_normal[1], -mesh_normal[2]))
    return normal, "opposite_mesh_station_tangent_for_lower_leg__s04_to_right_leg__s00_feature_flow"


def control_dict_text(source_id: str) -> str:
    stations = load_mesh_stations(source_id)
    blocks = []
    for label in TARGET_STATIONS:
        station = stations[label]
        blocks.append(
            f"""      plane_{label} {{
        type cuttingPlane; planeType pointAndNormal;
        pointAndNormalDict {{ point ({float(station['x']):.12g} {float(station['y']):.12g} {float(station['z']):.12g}); normal ({float(station['nx']):.12g} {float(station['ny']):.12g} {float(station['nz']):.12g}); }}
      }}"""
        )
    surfaces = "\n".join(blocks)
    return f"""FoamFile {{ version 2.0; format ascii; class dictionary; object controlDict; }}
application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;
writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;
writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;
functions {{
  {FUNCTION_OBJECT} {{
    type            surfaces;
    libs            ("libsampling.so");
    writeControl    writeTime;
    surfaceFormat   vtk;
    interpolate     false;
    interpolationScheme cell;
    fields          (U p p_rgh rho T);
    surfaces (
{surfaces}
    );
  }}
}}
"""


def field_paths_present(source_case: Path, time_s: str) -> dict[str, bool]:
    time_dir = source_case / "processors64" / time_s
    return {field: (time_dir / field).exists() for field in REQUIRED_FIELDS}


def case_sampling_plan_rows(targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in targets:
        mesh = load_mesh_stations(row["source_id"])
        for role, station_label, patch_name, surface_label in (
            ("upstream", row["upstream_station_label"], row["upstream_patch"], row["upstream_output_label"]),
            ("downstream", row["downstream_station_label"], row["downstream_patch"], row["downstream_output_label"]),
        ):
            station = mesh[station_label]
            normal, normal_policy = expected_flow_normal(station)
            rows.append(
                {
                    "case_id": row["case_id"],
                    "case_key": row["case_key"],
                    "source_id": row["source_id"],
                    "feature": row["feature"],
                    "time_s": row["time_window_s"],
                    "tap_role": role,
                    "station_label": station_label,
                    "declared_patch": patch_name,
                    "surface_label": surface_label,
                    "sample_method": "mesh_station_cutting_plane_vtk",
                    "cut_plane_x": fmt(station["x"]),
                    "cut_plane_y": fmt(station["y"]),
                    "cut_plane_z": fmt(station["z"]),
                    "cut_plane_normal_x": fmt(station["nx"]),
                    "cut_plane_normal_y": fmt(station["ny"]),
                    "cut_plane_normal_z": fmt(station["nz"]),
                    "expected_positive_normal_x": fmt(normal[0]),
                    "expected_positive_normal_y": fmt(normal[1]),
                    "expected_positive_normal_z": fmt(normal[2]),
                    "expected_positive_normal_policy": normal_policy,
                    "source_case_path": row["source_case_path"],
                    "staged_case_dir": rel(stage_case_dir(row)),
                    "expected_surface_file": rel(expected_vtk_path(row, station_label)),
                }
            )
    return rows


def preflight_rows(targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in targets:
        source_case = ROOT / row["source_case_path"]
        fields = field_paths_present(source_case, row["time_window_s"])
        mesh_path = MESH_ROOT / row["source_id"] / "mesh_stations.json"
        mesh_ok = False
        missing_stations = list(TARGET_STATIONS)
        if mesh_path.exists():
            mesh = load_mesh_stations(row["source_id"])
            missing_stations = [label for label in TARGET_STATIONS if label not in mesh]
            mesh_ok = not missing_stations
        up_faces = boundary_nfaces(source_case, row["upstream_patch"])
        down_faces = boundary_nfaces(source_case, row["downstream_patch"])
        blocking = []
        if not source_case.exists():
            blocking.append("missing_source_case")
        if not (source_case / "processors64" / row["time_window_s"]).exists():
            blocking.append("missing_processor_time")
        for field, present in fields.items():
            if not present:
                blocking.append(f"missing_field_{field}")
        if not mesh_ok:
            blocking.append("missing_mesh_station_labels")
        if not OF_ENV.exists():
            blocking.append("missing_openfoam13_env")
        patch_status = "blocked_empty_ncc_patch_boundary"
        sampling_status = "ready_for_cutting_plane_sampling" if not blocking else "blocked_preflight_failure"
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "source_id": row["source_id"],
                "time_s": row["time_window_s"],
                "source_case_exists": str(source_case.exists()).lower(),
                "processor_time_exists": str((source_case / "processors64" / row["time_window_s"]).exists()).lower(),
                "required_fields_present": ";".join(field for field, present in fields.items() if present),
                "required_fields_missing": ";".join(field for field, present in fields.items() if not present),
                "mesh_stations_exists": str(mesh_path.exists()).lower(),
                "missing_station_labels": ";".join(missing_stations),
                "upstream_patch_boundary_nfaces": "" if up_faces is None else up_faces,
                "downstream_patch_boundary_nfaces": "" if down_faces is None else down_faces,
                "direct_patch_sampling_status": patch_status,
                "sampling_method": "mesh_station_cutting_plane_vtk",
                "sampler_status": sampling_status,
                "blocking_reasons": ";".join(blocking),
                "native_solver_outputs_mutated": "false",
            }
        )
    return rows


def parse_vtk_surface(path: Path, normal: tuple[float, float, float]) -> dict[str, Any]:
    if not path.exists():
        return {"sample_status": "missing_raw_surface_file"}
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    points: list[tuple[float, float, float]] = []
    polygons: list[list[int]] = []
    cell_data: dict[str, list[Any]] = {}
    index = 0
    while index < len(text):
        parts = text[index].strip().split()
        if not parts:
            index += 1
            continue
        if parts[0] == "POINTS" and len(parts) >= 3:
            count = int(parts[1])
            values: list[float] = []
            index += 1
            while len(values) < count * 3 and index < len(text):
                values.extend(float(part) for part in text[index].split())
                index += 1
            points = [tuple(values[i : i + 3]) for i in range(0, count * 3, 3)]  # type: ignore[list-item]
            continue
        if parts[0] == "POLYGONS" and len(parts) >= 3:
            count = int(parts[1])
            value_count = int(parts[2])
            values: list[int] = []
            index += 1
            while len(values) < value_count and index < len(text):
                values.extend(int(part) for part in text[index].split())
                index += 1
            cursor = 0
            for _ in range(count):
                if cursor >= len(values):
                    break
                face_size = values[cursor]
                cursor += 1
                polygons.append(values[cursor : cursor + face_size])
                cursor += face_size
            continue
        if parts[0] == "CELL_DATA":
            cell_count = int(parts[1])
            index += 1
            while index < len(text):
                parts = text[index].strip().split()
                if not parts:
                    index += 1
                    continue
                if parts[0] == "POINT_DATA":
                    break
                if parts[0] == "FIELD" and len(parts) >= 3:
                    field_count = int(parts[2])
                    index += 1
                    for _ in range(field_count):
                        header = text[index].strip().split()
                        if len(header) < 4:
                            index += 1
                            continue
                        name = header[0]
                        components = int(header[1])
                        tuples = int(header[2])
                        total = components * tuples
                        index += 1
                        values: list[float] = []
                        while len(values) < total and index < len(text):
                            values.extend(float(part) for part in text[index].split())
                            index += 1
                        if tuples != cell_count:
                            continue
                        if components == 1:
                            cell_data[name] = values[:cell_count]
                        elif components == 3:
                            cell_data[name] = [
                                (values[i], values[i + 1], values[i + 2])
                                for i in range(0, cell_count * 3, 3)
                            ]
                    continue
                if parts[0] == "VECTORS" and len(parts) >= 2:
                    name = parts[1]
                    index += 1
                    values = []
                    while len(values) < cell_count * 3 and index < len(text):
                        values.extend(float(part) for part in text[index].split())
                        index += 1
                    data = [
                        (values[i], values[i + 1], values[i + 2])
                        for i in range(0, cell_count * 3, 3)
                    ]
                    cell_data[name] = data
                    continue
                if parts[0] == "SCALARS" and len(parts) >= 2:
                    name = parts[1]
                    index += 1
                    if index < len(text) and text[index].strip().startswith("LOOKUP_TABLE"):
                        index += 1
                    data = []
                    while len(data) < cell_count and index < len(text):
                        stripped = text[index].strip()
                        if stripped:
                            data.extend(float(part) for part in stripped.split())
                        index += 1
                    cell_data[name] = data[:cell_count]
                    continue
                index += 1
            continue
        index += 1
    if not points or not polygons:
        return {"sample_status": "empty_or_unreadable_vtk"}
    missing = [field for field in REQUIRED_FIELDS if field not in cell_data]
    if missing:
        return {"sample_status": "missing_vtk_cell_fields", "missing_fields": ";".join(missing)}
    normal = unit(normal)
    area_total = 0.0
    weighted: dict[str, float] = {"p": 0.0, "p_rgh": 0.0, "rho": 0.0, "T": 0.0}
    u_weighted = [0.0, 0.0, 0.0]
    reverse_area = 0.0
    reverse_mass = 0.0
    abs_mass = 0.0
    signed_mass = 0.0
    secondary_weighted = 0.0
    for face_index, face in enumerate(polygons):
        if len(face) < 3:
            continue
        origin = points[face[0]]
        area_vector = (0.0, 0.0, 0.0)
        for i in range(1, len(face) - 1):
            tri = cross(sub(points[face[i]], origin), sub(points[face[i + 1]], origin))
            area_vector = (
                area_vector[0] + 0.5 * tri[0],
                area_vector[1] + 0.5 * tri[1],
                area_vector[2] + 0.5 * tri[2],
            )
        area = vector_norm(area_vector)
        if area <= 0.0:
            continue
        u_vec = cell_data["U"][face_index]
        rho = float(cell_data["rho"][face_index])
        un = dot(u_vec, normal)
        mass = rho * un * area
        area_total += area
        for field in ("p", "p_rgh", "rho", "T"):
            weighted[field] += float(cell_data[field][face_index]) * area
        for i in range(3):
            u_weighted[i] += float(u_vec[i]) * area
        signed_mass += mass
        abs_mass += abs(mass)
        if un < 0.0:
            reverse_area += area
            reverse_mass += abs(mass)
        speed = vector_norm(u_vec)
        if speed > 0.0:
            transverse = math.sqrt(max(speed * speed - un * un, 0.0)) / speed
            secondary_weighted += transverse * area
    if area_total <= 0.0:
        return {"sample_status": "zero_area_vtk"}
    p_mean = weighted["p"] / area_total
    p_rgh_mean = weighted["p_rgh"] / area_total
    rho_mean = weighted["rho"] / area_total
    t_mean = weighted["T"] / area_total
    u_area = tuple(value / area_total for value in u_weighted)
    u_bulk_normal = signed_mass / (rho_mean * area_total) if rho_mean > 0.0 else float("nan")
    return {
        "sample_status": "sampled",
        "face_count": len(polygons),
        "area_m2": area_total,
        "p_pa": p_mean,
        "p_rgh_pa": p_rgh_mean,
        "rho_kg_m3": rho_mean,
        "T_K": t_mean,
        "U_area_mean_x_m_s": u_area[0],
        "U_area_mean_y_m_s": u_area[1],
        "U_area_mean_z_m_s": u_area[2],
        "U_bulk_m_s": vector_norm(u_area),
        "U_bulk_normal_m_s": u_bulk_normal,
        "mass_flux_kg_s": signed_mass,
        "reverse_area_fraction": reverse_area / area_total,
        "reverse_mass_fraction": reverse_mass / abs_mass if abs_mass > 0.0 else float("nan"),
        "secondary_velocity_fraction": secondary_weighted / area_total,
    }


def raw_rows_from_manifest(surface_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in surface_rows:
        normal = (
            float(row["expected_positive_normal_x"]),
            float(row["expected_positive_normal_y"]),
            float(row["expected_positive_normal_z"]),
        )
        parsed = parse_vtk_surface(ROOT / row["expected_surface_file"], normal)
        gate = ""
        if parsed.get("sample_status") == "sampled":
            raf = float(parsed["reverse_area_fraction"])
            rmf = float(parsed["reverse_mass_fraction"])
            gate = "pass" if raf < 0.01 and rmf < 0.01 else "fail_recirculation"
        rows.append(
            {
                **{key: row.get(key, "") for key in ("case_id", "case_key", "source_id", "feature", "time_s", "tap_role", "station_label", "surface_label", "source_case_path")},
                "sampled_surface_file": row["expected_surface_file"],
                "sample_status": parsed.get("sample_status", ""),
                "face_count": parsed.get("face_count", ""),
                "area_m2": fmt(parsed.get("area_m2")),
                "normal_x": row["expected_positive_normal_x"],
                "normal_y": row["expected_positive_normal_y"],
                "normal_z": row["expected_positive_normal_z"],
                "expected_positive_normal_policy": row["expected_positive_normal_policy"],
                "p_pa": fmt(parsed.get("p_pa")),
                "p_rgh_pa": fmt(parsed.get("p_rgh_pa")),
                "rho_kg_m3": fmt(parsed.get("rho_kg_m3")),
                "T_K": fmt(parsed.get("T_K")),
                "U_area_mean_x_m_s": fmt(parsed.get("U_area_mean_x_m_s")),
                "U_area_mean_y_m_s": fmt(parsed.get("U_area_mean_y_m_s")),
                "U_area_mean_z_m_s": fmt(parsed.get("U_area_mean_z_m_s")),
                "U_bulk_m_s": fmt(parsed.get("U_bulk_m_s")),
                "U_bulk_normal_m_s": fmt(parsed.get("U_bulk_normal_m_s")),
                "mass_flux_kg_s": fmt(parsed.get("mass_flux_kg_s")),
                "reverse_area_fraction": fmt(parsed.get("reverse_area_fraction")),
                "reverse_mass_fraction": fmt(parsed.get("reverse_mass_fraction")),
                "secondary_velocity_fraction": fmt(parsed.get("secondary_velocity_fraction")),
                "ordinary_recirculation_gate": gate,
                "admission_status": "raw_sample_only_no_component_k_admission" if parsed.get("sample_status") == "sampled" else "missing_raw_sample_diagnostic_only",
                "guardrail": "do_not_fit_F6_or_admit_component_K_from_this_sampler",
            }
        )
    return rows


def script_rows() -> list[dict[str, str]]:
    scripts = OUT / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "controlDicts").mkdir(parents=True, exist_ok=True)
    targets = load_targets()
    for row in targets:
        (scripts / "controlDicts" / f"{row['case_key']}.controlDict").write_text(control_dict_text(row["source_id"]), encoding="utf-8")
    case_lines = "\n".join(
        f"{row['case_key']}|{row['source_case_path']}|{row['time_window_s']}" for row in targets
    )
    runner = scripts / "run_two_tap_staged_endpoint_sampling.sh"
    runner.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
ROOT={ROOT}
OUT="$ROOT/{OUT_REL}"
TMP="$ROOT/{TMP_REL}"
OF_ENV="$ROOT/{rel(OF_ENV)}"
LOG_DIR="$OUT/logs"
mkdir -p "$LOG_DIR" "$TMP/staged_reconstructed"
cd "$ROOT"
log() {{ printf '[%s] %s\\n' "$(date --iso-8601=seconds)" "$*" >&2; }}
run_one() {{
  local case_key="$1" source_case="$2" time_s="$3"
  local source_abs="$ROOT/$source_case"
  local case_dir="$TMP/staged_reconstructed/$case_key"
  [[ -d "$source_abs/processors64/$time_s" ]] || {{ log "missing time: $source_abs/processors64/$time_s"; exit 1; }}
  [[ -f "$OF_ENV" ]] || {{ log "missing OpenFOAM env: $OF_ENV"; exit 1; }}
  mkdir -p "$case_dir"
  for name in constant 0; do [[ -e "$case_dir/$name" ]] || cp -a "$source_abs/$name" "$case_dir/$name"; done
  if [[ ! -d "$case_dir/system" ]]; then
    cp -a "$source_abs/system" "$case_dir/system"
  else
    cp -an "$source_abs/system/." "$case_dir/system/"
  fi
  ln -sfn "$source_abs/processors64" "$case_dir/processors64"
  if [[ -e "$case_dir/system/functions" || -L "$case_dir/system/functions" ]]; then
    mv "$case_dir/system/functions" "$case_dir/system/functions.two_tap_disabled.$(date +%s)"
  fi
  cp "$OUT/scripts/controlDicts/${{case_key}}.controlDict" "$case_dir/system/controlDict"
  if [[ ! -d "$case_dir/$time_s" ]]; then
    timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$case_dir' -time '$time_s' -fields '(U p p_rgh rho T)'" > "$LOG_DIR/${{case_key}}_reconstructPar.log" 2>&1
  fi
  timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$case_dir' -time '$time_s'" > "$LOG_DIR/${{case_key}}_foamPostProcess.log" 2>&1
}}
while IFS='|' read -r case_key source_case time_s; do
  [[ -n "$case_key" ]] || continue
  log "sampling $case_key at $time_s"
  run_one "$case_key" "$source_case" "$time_s"
done <<'CASES'
{case_lines}
CASES
python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py --harvest --record-job-id "${{SLURM_JOB_ID:-local}}"
log "two-tap staged endpoint sampling complete"
""",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    sbatch = scripts / "submit_two_tap_staged_endpoint_sampling.sbatch"
    sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J two_tap_ep
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 04:00:00
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -o {OUT}/logs/slurm-%j.out
#SBATCH -e {OUT}/logs/slurm-%j.err

set -euo pipefail
cd {ROOT}
{rel(runner)}
""",
        encoding="utf-8",
    )
    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)
    rows = [
        {"script_id": "runner", "path": rel(runner), "purpose": "stage symlinked read-only case views and run foamPostProcess cutting-plane VTK sampler"},
        {"script_id": "sbatch", "path": rel(sbatch), "purpose": "submit the two-tap endpoint sampler to Slurm"},
    ]
    rows.extend(
        {
            "script_id": f"controlDict_{row['case_key']}",
            "path": rel(scripts / "controlDicts" / f"{row['case_key']}.controlDict"),
            "purpose": f"two-plane VTK function object for {row['case_key']}",
        }
        for row in targets
    )
    return rows


def source_manifest_rows(targets: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [
        {"artifact": "raw_endpoint_plan", "path": rel(PLAN), "use": "exact target/tap/field contract"},
        {"artifact": "blocker_roadmap", "path": rel(ROADMAP), "use": "research path and next-step ordering"},
        {"artifact": "mesh_centerlines_root", "path": rel(MESH_ROOT), "use": "station coordinates and cutting-plane normals"},
        {"artifact": "openfoam_env", "path": rel(OF_ENV), "use": "compute-node foamPostProcess runtime"},
    ]
    for row in targets:
        rows.append(
            {
                "artifact": row["case_key"],
                "path": row["source_case_path"],
                "use": f"read-only source fields at time {row['time_window_s']}",
            }
        )
    return rows


def readiness_rows(preflight: list[dict[str, Any]], raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed_count_by_case = {}
    for row in raw_rows:
        parsed_count_by_case.setdefault(row["case_key"], 0)
        if row["sample_status"] == "sampled":
            parsed_count_by_case[row["case_key"]] += 1
    rows = []
    for row in preflight:
        if row["sampler_status"] != "ready_for_cutting_plane_sampling":
            decision = "blocked_preflight"
            next_action = "repair missing source/time/field/mesh prerequisite"
        elif parsed_count_by_case.get(row["case_key"], 0) == 2:
            decision = "raw_endpoint_sampled"
            next_action = "run pressure/velocity basis audit"
        else:
            decision = "ready_to_submit_or_harvest_pending"
            next_action = "submit scripts/submit_two_tap_staged_endpoint_sampling.sbatch on compute node, then harvest"
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "time_s": row["time_s"],
                "direct_patch_sampling_status": row["direct_patch_sampling_status"],
                "cutting_plane_sampling_status": row["sampler_status"],
                "parsed_endpoint_rows": parsed_count_by_case.get(row["case_key"], 0),
                "decision": decision,
                "next_action": next_action,
                "guardrail": "no F6 fit; no component-K admission; no native-output mutation",
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if summary["raw_sampled_rows"] == summary["endpoint_surfaces"] and summary["raw_missing_rows"] == 0:
        evidence_status = (
            "The sampler package is complete and raw endpoint evidence has been harvested "
            f"from staged VTK surfaces. The harvest recorded job `{summary['last_harvest_job_id']}` "
            "when provided. These rows are raw diagnostic evidence only; they do not admit "
            "component K or fit F6."
        )
        how_to_advance = (
            "Open a separate pressure/velocity basis audit task before computing loss terms. "
            "Do not run F6 fitting or component-K admission directly from this sampler package."
        )
    else:
        evidence_status = (
            "The sampler package is complete. Raw endpoint evidence is still pending because "
            "the task-owned VTK surfaces have not all been harvested; missing raw rows remain "
            "diagnostic placeholders until the Slurm script runs and the builder harvests VTK surfaces."
        )
        how_to_advance = (
            "Submit `scripts/submit_two_tap_staged_endpoint_sampling.sbatch` from this "
            "workspace, then run:\n\n"
            "```bash\n"
            "python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py --harvest --record-job-id <job_id>\n"
            "```\n\n"
            "Only after `raw_endpoint_pressure_velocity.csv` has six `sampled` rows should a "
            "separate pressure/velocity basis audit compute loss terms."
        )
    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(PLAN / 'target_feature_taps.csv')}
  - {rel(PLAN / 'pressure_surface_sampling_contract.csv')}
  - {rel(ROADMAP / 'next_step_queue.csv')}
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/status/2026-07-18_{TASK}.md
  - .agent/journal/2026-07-18/two-tap-staged-endpoint-sampler.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Staged Endpoint Sampler

Generated: `{summary['generated_at']}`

## Result

This package implements the first executable research path from the blocker
roadmap: staged raw endpoint sampling for Salt2/Salt3/Salt4
`corner_lower_right`. The declared NCC patch names are preserved as provenance,
but direct patch sampling is blocked because the reconstructed boundary entries
have zero faces. The runnable path is therefore mesh-station cutting planes at
`lower_leg__s04` and `right_leg__s00`, with VTK output so face area, normals,
velocity, pressure, density, temperature, and reverse-flow metrics can be
computed from the same raw surfaces.

{evidence_status}

## Outputs

- `case_sampling_plan.csv`
- `sampler_preflight.csv`
- `endpoint_surface_target_manifest.csv`
- `raw_endpoint_surface_file_manifest.csv`
- `raw_endpoint_pressure_velocity.csv`
- `sampler_readiness_or_failure.csv`
- `scripts_manifest.csv`
- `source_manifest.csv`
- `summary.json`

## Current Counts

- Target cases: `{summary['target_cases']}`
- Endpoint surfaces: `{summary['endpoint_surfaces']}`
- Preflight failures: `{summary['preflight_failures']}`
- Raw sampled rows: `{summary['raw_sampled_rows']}`
- Raw missing rows: `{summary['raw_missing_rows']}`
- Direct NCC patch sampling viable rows: `{summary['direct_patch_sampling_viable_rows']}`
- Scheduler jobs submitted by this package: `{summary['scheduler_jobs_submitted']}`

## How To Advance

{how_to_advance}

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry, admission state, Fluid
source, F6 fit, component-K admission, or generated documentation index was
changed. This package does not infer endpoint pressure from older proxy rows.
""",
        encoding="utf-8",
    )


def build_package(record_job_id: str = "") -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    targets = load_targets()
    contract = load_contract_rows()
    validate_contract(targets, contract)
    surface_rows = case_sampling_plan_rows(targets)
    preflight = preflight_rows(targets)
    scripts = script_rows()
    raw_rows = raw_rows_from_manifest(surface_rows)
    readiness = readiness_rows(preflight, raw_rows)
    write_csv(OUT / "case_sampling_plan.csv", surface_rows)
    write_csv(OUT / "endpoint_surface_target_manifest.csv", surface_rows)
    write_csv(
        OUT / "raw_endpoint_surface_file_manifest.csv",
        [
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "time_s": row["time_s"],
                "station_label": row["station_label"],
                "surface_label": row["surface_label"],
                "expected_surface_file": row["expected_surface_file"],
                "exists": str((ROOT / row["expected_surface_file"]).exists()).lower(),
            }
            for row in surface_rows
        ],
    )
    write_csv(OUT / "sampler_preflight.csv", preflight)
    write_csv(OUT / "raw_endpoint_pressure_velocity.csv", raw_rows, RAW_FIELDS)
    write_csv(OUT / "sampler_readiness_or_failure.csv", readiness)
    write_csv(OUT / "scripts_manifest.csv", scripts)
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(targets))
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "output_dir": rel(OUT),
        "tmp_dir": rel(TMP),
        "target_cases": len(targets),
        "endpoint_surfaces": len(surface_rows),
        "preflight_failures": sum(1 for row in preflight if row["sampler_status"] != "ready_for_cutting_plane_sampling"),
        "raw_sampled_rows": sum(1 for row in raw_rows if row["sample_status"] == "sampled"),
        "raw_missing_rows": sum(1 for row in raw_rows if row["sample_status"] != "sampled"),
        "direct_patch_sampling_viable_rows": sum(
            1
            for row in preflight
            if row["upstream_patch_boundary_nfaces"] not in ("", 0, "0")
            or row["downstream_patch_boundary_nfaces"] not in ("", 0, "0")
        ),
        "scheduler_jobs_submitted": 0,
        "last_harvest_job_id": record_job_id,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "fluid_or_external_repo_mutated": False,
        "f6_fit_performed": False,
        "component_k_admitted": False,
        "generated_docs_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harvest", action="store_true", help="Rebuild outputs and parse any task-owned VTK surfaces that now exist.")
    parser.add_argument("--record-job-id", default="")
    args = parser.parse_args()
    # The default build and harvest path use the same deterministic outputs; if
    # VTK files exist, they are parsed, otherwise missing rows remain explicit.
    summary = build_package(record_job_id=args.record_job_id if args.harvest else "")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
