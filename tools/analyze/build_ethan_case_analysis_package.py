#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_ethan_case_heat_summary import build_case_heat_summary  # noqa: E402
from tools.case_analysis_profiles import (  # noqa: E402
    DEFAULT_SOURCE_ID,
    DEFAULT_TARGET_DS_M,
    build_flow_direction_hint_metadata,
    get_case_analysis_profile,
    resolve_case_paths,
)
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, safe_float, save_matplotlib_figure  # noqa: E402
from tools import hydraulic_budget_defs as defs  # noqa: E402

MAJOR_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_leg_centerline_major_loss.py"
FEATURE_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_feature_minor_loss_budget.py"
BOUNDARY_LAYER_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_boundary_layer_landmarks.py"
AZIMUTHAL_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_azimuthal_transport.py"
PATCH_BUILDER_PATH = ROOT / "tools" / "analyze" / "build_ethan_streamwise_friction_package.py"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-10_ethan_salt2_case_analysis_package"
REUSED_HEAT_CSV_FILENAMES = (
    "heat_loss_summary.csv",
    "heat_loss_timeseries.csv",
    "heat_loss_window_summary.csv",
)
HEAT_FIGURE_EXTENSIONS = ("png", "svg", "pdf")

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


patch_builder = load_module("build_ethan_streamwise_friction_package", PATCH_BUILDER_PATH)


def build_parser(default_output_dir: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a reusable per-case analysis package by integrating legwise major-loss, "
            "feature minor-loss pressure budgets, and case-scoped heat accounting."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--last-n-times", type=int, default=5)
    parser.add_argument("--time-selector", help="Explicit comma-separated OpenFOAM time selector override.")
    parser.add_argument("--target-ds-m", type=float, default=DEFAULT_TARGET_DS_M)
    parser.add_argument("--skip-extraction", action="store_true")
    parser.add_argument("--output-dir", default=str(default_output_dir))
    parser.add_argument(
        "--raw-extraction-dir",
        help="Reuse an existing raw extraction directory instead of calling the hydraulic extractors.",
    )
    return parser


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def numeric_or_nan(value: object) -> float:
    parsed = safe_float(value)
    return float(parsed) if parsed is not None and math.isfinite(parsed) else math.nan


def normalize_warning_flag(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    token = str(value).strip().lower()
    if token in {"1", "true", "yes", "y"}:
        return "yes"
    if token in {"0", "false", "no", "n", ""}:
        return "no"
    return "yes"


def canonical_time_labels(values: list[str]) -> list[str]:
    labels: list[str] = []
    for value in values:
        numeric = safe_float(value)
        labels.append(f"{numeric:g}" if numeric is not None else value.strip())
    return labels


def build_snapshot_request_key(
    source_id: str,
    live_runtime_root: Path,
    selected_times: list[str],
    profile_name: str,
) -> str:
    payload = {
        "source_id": source_id,
        "live_runtime_root": str(live_runtime_root),
        "selected_times": canonical_time_labels(selected_times),
        "profile_name": profile_name,
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def create_frozen_runtime_snapshot(
    source_id: str,
    live_runtime_root: Path,
    selected_times: list[str],
    profile_name: str,
) -> tuple[Path, list[str], list[str]]:
    snapshot_key = build_snapshot_request_key(
        source_id,
        live_runtime_root,
        selected_times,
        profile_name,
    )
    snapshot_root = ensure_dir(
        ROOT / "tmp_extract" / "ethan_case_analysis_snapshots" / source_id / profile_name / snapshot_key
    )
    processors_root = ensure_dir(snapshot_root / "processors64")
    missing_times: list[str] = []
    copied_times: list[str] = []
    snapshot_request = {
        "generated_at": iso_timestamp(),
        "source_id": source_id,
        "live_runtime_root": str(live_runtime_root),
        "selected_times": canonical_time_labels(selected_times),
        "profile_name": profile_name,
        "snapshot_key": snapshot_key,
    }
    json_dump(snapshot_root / "snapshot_request.json", snapshot_request)

    for name in ("0", "constant", "dynamicCode", "postProcessing", "system", "case_config.yaml"):
        source_path = live_runtime_root / name
        target_path = snapshot_root / name
        if not source_path.exists():
            continue
        if target_path.is_symlink() or target_path.exists():
            if target_path.is_dir() and not target_path.is_symlink():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
        if source_path.is_dir():
            target_path.symlink_to(source_path)
        else:
            target_path.symlink_to(source_path)

    source_processors_root = live_runtime_root / "processors64"
    constant_path = source_processors_root / "constant"
    target_constant = processors_root / "constant"
    for existing in processors_root.iterdir():
        if existing.name == "constant":
            continue
        if existing.is_dir():
            shutil.rmtree(existing)
        else:
            existing.unlink()
    if target_constant.is_symlink() or target_constant.exists():
        if target_constant.is_dir() and not target_constant.is_symlink():
            shutil.rmtree(target_constant)
        else:
            target_constant.unlink()
    if constant_path.exists():
        shutil.copytree(constant_path, target_constant, dirs_exist_ok=True)

    for time_name in selected_times:
        source_time_dir = source_processors_root / time_name
        target_time_dir = processors_root / time_name
        if target_time_dir.exists():
            shutil.rmtree(target_time_dir)
        if not source_time_dir.exists():
            missing_times.append(time_name)
            continue
        shutil.copytree(source_time_dir, target_time_dir)
        copied_times.append(time_name)
    return snapshot_root, copied_times, missing_times


def build_analysis_manifest(
    source_id: str,
    selected_times: list[str],
    target_ds_m: float,
    live_runtime_root: Path,
    frozen_runtime_root: Path,
    missing_times: list[str],
) -> dict[str, Any]:
    profile = get_case_analysis_profile(source_id)
    source_root, _, _ = resolve_case_paths(source_id)
    flow_direction_metadata = build_flow_direction_hint_metadata(profile)
    return {
        "generated_at": iso_timestamp(),
        "profile_name": profile.profile_name,
        "source_id": source_id,
        "source_root": str(source_root),
        "runtime_root": str(frozen_runtime_root),
        "live_runtime_root": str(live_runtime_root),
        "frozen_runtime_root": str(frozen_runtime_root),
        "requested_times": canonical_time_labels(selected_times),
        "missing_snapshot_times": canonical_time_labels(missing_times),
        "target_ds_m": float(target_ds_m),
        "required_fields": list(profile.analysis_required_fields),
        "wall_fields": list(profile.wall_fields),
        "pressure_fields": list(profile.pressure_fields),
        "flow_direction_hints": flow_direction_metadata,
        "sign_conventions": {
            "feature_pressure_delta": "end_minus_start",
            "major_dp_gradient": "positive magnitude from Darcy-f estimate",
            "major_direct_pressure_drop_gradient": "minus d(area_avg(p_rgh))/ds so positive means pressure drop along local streamwise coordinate",
        },
        "deferred_terms": [
            "profile_dp_pa remains unsampled in the first feature-budget implementation",
            "feature wall_dp_pa is inferred from adjacent major-span gradients",
        ],
    }


def run_extractor(
    path: Path,
    source_id: str,
    manifest_path: Path,
    target_ds_m: float,
    output_dir: Path,
    skip_extraction: bool,
) -> None:
    cmd = [
        sys.executable,
        str(path),
        "--source-id",
        source_id,
        "--analysis-manifest",
        str(manifest_path),
        "--output-dir",
        str(output_dir / "raw_extraction"),
    ]
    if path == MAJOR_EXTRACTOR_PATH:
        cmd.extend(["--target-ds-m", str(target_ds_m)])
    if skip_extraction:
        cmd.append("--skip-extraction")
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def copy_raw_extraction_tree(source_dir: Path, target_dir: Path) -> None:
    if source_dir.resolve() == target_dir.resolve():
        return
    ensure_dir(target_dir)
    for item in source_dir.iterdir():
        destination = target_dir / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            if destination.exists() and item.resolve() == destination.resolve():
                continue
            shutil.copy2(item, destination)


def copy_file(source_path: Path, destination_path: Path) -> None:
    ensure_dir(destination_path.parent)
    shutil.copy2(source_path, destination_path)


def canonical_time_labels_from_meta(metadata: dict[str, Any], key: str) -> list[str]:
    values = metadata.get(key, [])
    return canonical_time_labels([str(value) for value in values])


def first_nonempty_str(*values: object) -> str:
    for value in values:
        token = str(value).strip()
        if token:
            return token
    return ""


def validate_raw_extraction_metadata(
    requested_source_id: str,
    profile_name: str,
    major_summary_meta: dict[str, Any],
    feature_summary_meta: dict[str, Any],
    boundary_summary_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    major_source_id = first_nonempty_str(major_summary_meta.get("source_id"))
    feature_source_id = first_nonempty_str(feature_summary_meta.get("source_id"))
    if major_source_id != requested_source_id or feature_source_id != requested_source_id:
        raise RuntimeError(
            "Raw extraction summary source_id mismatch: "
            f"requested `{requested_source_id}`, "
            f"major `{major_source_id or '<missing>'}`, "
            f"feature `{feature_source_id or '<missing>'}`"
        )

    major_profile_name = first_nonempty_str(major_summary_meta.get("profile_name"))
    feature_profile_name = first_nonempty_str(feature_summary_meta.get("profile_name"))
    if major_profile_name != profile_name or feature_profile_name != profile_name:
        raise RuntimeError(
            "Raw extraction summary profile_name mismatch: "
            f"expected `{profile_name}`, "
            f"major `{major_profile_name or '<missing>'}`, "
            f"feature `{feature_profile_name or '<missing>'}`"
        )

    major_requested = canonical_time_labels_from_meta(major_summary_meta, "requested_times")
    feature_requested = canonical_time_labels_from_meta(feature_summary_meta, "requested_times")
    if not major_requested or not feature_requested:
        raise RuntimeError("Raw extraction summaries must both report non-empty `requested_times`")
    if major_requested != feature_requested:
        raise RuntimeError(
            "Raw extraction summary requested_times mismatch: "
            f"major {major_requested} vs feature {feature_requested}"
        )

    major_available = canonical_time_labels_from_meta(major_summary_meta, "available_times")
    feature_available = canonical_time_labels_from_meta(feature_summary_meta, "available_times")
    if not major_available or not feature_available:
        raise RuntimeError("Raw extraction summaries must both report non-empty `available_times`")
    if major_available != feature_available:
        raise RuntimeError(
            "Raw extraction summary available_times mismatch: "
            f"major {major_available} vs feature {feature_available}"
        )

    major_runtime_root = first_nonempty_str(major_summary_meta.get("runtime_root"))
    feature_runtime_root = first_nonempty_str(feature_summary_meta.get("runtime_root"))
    if not major_runtime_root or not feature_runtime_root:
        raise RuntimeError("Raw extraction summaries must both report `runtime_root`")
    if major_runtime_root != feature_runtime_root:
        raise RuntimeError(
            "Raw extraction summary runtime_root mismatch: "
            f"major `{major_runtime_root}` vs feature `{feature_runtime_root}`"
        )

    if boundary_summary_meta:
        boundary_source_id = first_nonempty_str(boundary_summary_meta.get("source_id"))
        boundary_profile_name = first_nonempty_str(boundary_summary_meta.get("profile_name"))
        boundary_requested = canonical_time_labels_from_meta(boundary_summary_meta, "requested_times")
        boundary_available = canonical_time_labels_from_meta(boundary_summary_meta, "available_times")
        boundary_runtime_root = first_nonempty_str(boundary_summary_meta.get("runtime_root"))
        boundary_major_geometry_csv = first_nonempty_str(boundary_summary_meta.get("major_wall_face_geometry_csv"))
        major_geometry_csv = first_nonempty_str(major_summary_meta.get("wall_face_geometry_csv"))
        if boundary_source_id != requested_source_id:
            raise RuntimeError(
                "Boundary-layer raw extraction source_id mismatch: "
                f"expected `{requested_source_id}`, found `{boundary_source_id or '<missing>'}`"
            )
        if boundary_profile_name != profile_name:
            raise RuntimeError(
                "Boundary-layer raw extraction profile_name mismatch: "
                f"expected `{profile_name}`, found `{boundary_profile_name or '<missing>'}`"
            )
        if boundary_requested and boundary_requested != major_requested:
            raise RuntimeError(
                "Boundary-layer raw extraction requested_times mismatch: "
                f"boundary {boundary_requested} vs major {major_requested}"
            )
        if boundary_available and boundary_available != major_available:
            raise RuntimeError(
                "Boundary-layer raw extraction available_times mismatch: "
                f"boundary {boundary_available} vs major {major_available}"
            )
        same_major_geometry = False
        if boundary_major_geometry_csv and major_geometry_csv:
            try:
                same_major_geometry = Path(boundary_major_geometry_csv).resolve() == Path(major_geometry_csv).resolve()
            except OSError:
                same_major_geometry = False
        if boundary_runtime_root and boundary_runtime_root != major_runtime_root and not same_major_geometry:
            # The boundary-layer helper may run from its own reconstructed scratch
            # case, so runtime-root equality is too strict by itself. What must
            # stay fixed is the major-loss geometry contract; if both summaries
            # reference the same validated wall-face geometry CSV, the package can
            # safely treat the boundary landmarks as aligned to the same bins.
            raise RuntimeError(
                "Boundary-layer raw extraction runtime_root mismatch: "
                f"boundary `{boundary_runtime_root}` vs major `{major_runtime_root}`"
            )

    return {
        "validation_status": "validated",
        "requested_source_id": requested_source_id,
        "requested_profile_name": profile_name,
        "major_raw_schema_version": first_nonempty_str(major_summary_meta.get("raw_schema_version")),
        "major_summary_source_id": major_source_id,
        "feature_summary_source_id": feature_source_id,
        "major_summary_profile_name": major_profile_name,
        "feature_summary_profile_name": feature_profile_name,
        "requested_times": major_requested,
        "available_times": major_available,
        "runtime_root": major_runtime_root,
    }


def build_manifest_from_raw_extraction(
    source_id: str,
    profile_name: str,
    live_runtime_root: Path,
    raw_dir: Path,
    target_ds_m: float,
) -> dict[str, Any]:
    major_summary_meta = load_json(raw_dir / "leg_major_loss_extraction_summary.json")
    feature_summary_meta = load_json(raw_dir / "feature_minor_loss_extraction_summary.json")
    boundary_summary_meta = (
        load_json(raw_dir / "boundary_layer_landmark_summary.json")
        if (raw_dir / "boundary_layer_landmark_summary.json").exists()
        else None
    )
    raw_provenance = validate_raw_extraction_metadata(
        source_id,
        profile_name,
        major_summary_meta,
        feature_summary_meta,
        boundary_summary_meta,
    )
    major_geometry_csv = Path(
        first_nonempty_str(major_summary_meta.get("wall_face_geometry_csv"))
        or raw_dir / "leg_wall_face_geometry.csv"
    )
    major_wall_samples_csv = Path(
        first_nonempty_str(major_summary_meta.get("wall_face_samples_csv"))
        or raw_dir / "leg_wall_face_samples.csv"
    )
    if raw_provenance["major_raw_schema_version"] == "salt_family_major_loss_v2" and not major_geometry_csv.exists():
        raise RuntimeError(
            "Raw extraction summary advertises `salt_family_major_loss_v2`, but the wall-face geometry CSV is missing: "
            f"{major_geometry_csv}"
        )
    raw_provenance["major_wall_face_geometry_csv"] = str(major_geometry_csv)
    raw_provenance["major_wall_face_samples_csv"] = str(major_wall_samples_csv)
    requested_labels = list(raw_provenance["requested_times"])
    available_labels = set(raw_provenance["available_times"])
    missing_times = [value for value in requested_labels if value not in available_labels]
    effective_target_ds_m = float(major_summary_meta.get("target_ds_m", target_ds_m))
    effective_runtime_root = Path(str(raw_provenance["runtime_root"] or live_runtime_root))
    manifest = build_analysis_manifest(
        source_id,
        requested_labels,
        effective_target_ds_m,
        live_runtime_root,
        effective_runtime_root,
        missing_times,
    )
    manifest["generated_at"] = iso_timestamp()
    manifest["raw_extraction_provenance"] = raw_provenance
    return manifest


def reuse_heat_artifacts_from_package(
    raw_extraction_source_dir: Path,
    output_dir: Path,
    source_id: str,
    profile_name: str,
) -> dict[str, Any]:
    package_dir = raw_extraction_source_dir.resolve().parent
    summary_path = package_dir / "heat_loss_summary.json"
    missing_files = [name for name in REUSED_HEAT_CSV_FILENAMES if not (package_dir / name).exists()]
    if not summary_path.exists() or missing_files:
        missing_labels = ["heat_loss_summary.json" if not summary_path.exists() else ""]
        missing_labels.extend(missing_files)
        missing_labels = [label for label in missing_labels if label]
        raise RuntimeError(
            "Raw-reuse heat decoupling requires frozen package heat artifacts adjacent to the raw extraction directory; "
            f"missing {', '.join(missing_labels)} under {package_dir}"
        )

    heat_summary = load_json(summary_path)
    summary_source_id = first_nonempty_str(heat_summary.get("source_id"))
    summary_profile_name = first_nonempty_str(heat_summary.get("profile_name"))
    if summary_source_id != source_id or summary_profile_name != profile_name:
        raise RuntimeError(
            "Package heat summary identity mismatch for raw reuse: "
            f"expected source/profile `{source_id}` / `{profile_name}`, "
            f"found `{summary_source_id or '<missing>'}` / `{summary_profile_name or '<missing>'}`"
        )

    for filename in REUSED_HEAT_CSV_FILENAMES:
        copy_file(package_dir / filename, output_dir / filename)

    figure_paths: dict[str, str] = {}
    for extension in HEAT_FIGURE_EXTENSIONS:
        source_figure = Path(str(heat_summary.get("figure_paths", {}).get(extension, "")).strip())
        if not source_figure.exists():
            raise RuntimeError(
                "Raw-reuse heat decoupling requires the frozen package heat figure referenced by the heat summary; "
                f"missing `{source_figure}`"
            )
        destination_figure = output_dir / "figures" / extension / f"case_heat_loss_summary.{extension}"
        copy_file(source_figure, destination_figure)
        figure_paths[extension] = str(destination_figure)

    reused_summary = dict(heat_summary)
    validation_reference = reused_summary.get("validation_reference", {})
    validation_final_time_s = safe_float(validation_reference.get("final_time"))
    latest_heat_time_s = safe_float(reused_summary.get("latest_heat_time_s"))
    derived_validation_status = (
        "available"
        if isinstance(validation_reference, dict) and validation_reference
        else "missing"
    )
    derived_validation_source = str(
        reused_summary.get(
            "validation_reference_source",
            "reused_package_heat_summary_without_recorded_validation_source",
        )
    )
    derived_validation_lag_s: float | str = ""
    if latest_heat_time_s is not None and validation_final_time_s is not None:
        derived_validation_lag_s = float(latest_heat_time_s - validation_final_time_s)

    reused_summary.setdefault("validation_reference_status", derived_validation_status)
    reused_summary.setdefault("validation_reference_source", derived_validation_source)
    reused_summary.setdefault("validation_reference_lag_s", derived_validation_lag_s)
    if isinstance(reused_summary.get("latest_summary"), dict):
        reused_summary["latest_summary"].setdefault("validation_reference_status", reused_summary["validation_reference_status"])
        reused_summary["latest_summary"].setdefault("validation_reference_source", reused_summary["validation_reference_source"])
        reused_summary["latest_summary"].setdefault("validation_reference_lag_s", reused_summary["validation_reference_lag_s"])
    reused_summary["figure_paths"] = figure_paths
    reused_summary["reuse_status"] = "reused_package_heat_artifacts"
    reused_summary["reused_from_package_dir"] = str(package_dir)
    reused_summary["reused_at"] = iso_timestamp()
    json_dump(output_dir / "heat_loss_summary.json", reused_summary)
    return reused_summary


def load_major_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "bin_index": int(row["bin_index"]),
                "s_start_m": float(row["s_start_m"]),
                "s_end_m": float(row["s_end_m"]),
                "s_mid_m": float(row["s_mid_m"]),
                "wall_face_count": int(row["wall_face_count"]),
                "wall_area_m2": float(row["wall_area_m2"]),
                "local_wetted_perimeter_m": float(row["local_wetted_perimeter_m"]),
                "hydraulic_diameter_geom_m": float(row["hydraulic_diameter_geom_m"]),
                "flow_area_geom_m2": float(row["flow_area_geom_m2"]),
                "rho_bulk_kg_m3": float(row["rho_bulk_kg_m3"]),
                "mdot_mean_abs_kg_s": float(row["mdot_mean_abs_kg_s"]),
                "bulk_velocity_m_s": float(row["bulk_velocity_m_s"]),
                "tauw_streamwise_mean_signed_pa": float(row["tauw_streamwise_mean_signed_pa"]),
                "tauw_streamwise_mean_abs_pa": float(row["tauw_streamwise_mean_abs_pa"]),
                "tauw_streamwise_std_abs_pa": float(row["tauw_streamwise_std_abs_pa"]),
                "tauw_streamwise_max_rel_dev": float(row["tauw_streamwise_max_rel_dev"]),
                "darcy_f": float(row["darcy_f"]),
                "p_wall_area_avg_pa": numeric_or_nan(row.get("p_wall_area_avg_pa")),
                "p_rgh_wall_area_avg_pa": numeric_or_nan(row.get("p_rgh_wall_area_avg_pa")),
                "t_wall_area_avg_k": numeric_or_nan(row.get("t_wall_area_avg_k")),
                "bulk_temp_fluid_area_avg_k": numeric_or_nan(row.get("bulk_temp_fluid_area_avg_k")),
                "bulk_temp_area_weighted_k": numeric_or_nan(row.get("bulk_temp_area_weighted_k")),
                "bulk_temp_union_area_avg_k": numeric_or_nan(row.get("bulk_temp_union_area_avg_k")),
                "bulk_cross_section_face_count": numeric_or_nan(row.get("bulk_cross_section_face_count")),
                "bulk_cross_section_area_m2": numeric_or_nan(row.get("bulk_cross_section_area_m2")),
                "bulk_cross_section_total_face_count": numeric_or_nan(
                    row.get("bulk_cross_section_total_face_count")
                ),
                "bulk_cross_section_total_area_m2": numeric_or_nan(
                    row.get("bulk_cross_section_total_area_m2")
                ),
                "bulk_cross_section_region_count": numeric_or_nan(
                    row.get("bulk_cross_section_region_count")
                ),
                "bulk_cross_section_reference_area_m2": numeric_or_nan(
                    row.get("bulk_cross_section_reference_area_m2")
                ),
                "bulk_cross_section_area_ratio_to_geom": numeric_or_nan(row.get("bulk_cross_section_area_ratio_to_geom")),
                "bulk_cross_section_chosen_region_area_ratio_to_reference": numeric_or_nan(
                    row.get("bulk_cross_section_chosen_region_area_ratio_to_reference")
                ),
                "bulk_cross_section_chosen_region_signed_mass_flux_kg_s": numeric_or_nan(
                    row.get("bulk_cross_section_chosen_region_signed_mass_flux_kg_s")
                ),
                "bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s": numeric_or_nan(
                    row.get("bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s")
                ),
                "bulk_cross_section_chosen_region_positive_mass_flux_kg_s": numeric_or_nan(
                    row.get("bulk_cross_section_chosen_region_positive_mass_flux_kg_s")
                ),
                "bulk_cross_section_region_selection_status": str(
                    row.get("bulk_cross_section_region_selection_status", "")
                ),
                "bulk_temp_tp_endpoint_proxy_k": numeric_or_nan(
                    row.get("bulk_temp_tp_endpoint_proxy_k", row.get("bulk_temp_proxy_k"))
                ),
                "bulk_minus_wall_tp_endpoint_proxy_k": numeric_or_nan(
                    row.get("bulk_minus_wall_tp_endpoint_proxy_k", row.get("bulk_minus_wall_temp_k"))
                ),
                "effective_htc_tp_endpoint_proxy_w_m2_k": numeric_or_nan(
                    row.get("effective_htc_tp_endpoint_proxy_w_m2_k", row.get("effective_htc_w_m2_k"))
                ),
                "effective_ua_per_m_tp_endpoint_proxy_w_m_k": numeric_or_nan(
                    row.get("effective_ua_per_m_tp_endpoint_proxy_w_m_k", row.get("effective_ua_per_m_w_m_k"))
                ),
                "effective_thermal_resistance_tp_endpoint_proxy_k_m_w": numeric_or_nan(
                    row.get(
                        "effective_thermal_resistance_tp_endpoint_proxy_k_m_w",
                        row.get("effective_thermal_resistance_k_m_w"),
                    )
                ),
                "bulk_minus_wall_temp_k": numeric_or_nan(row.get("bulk_minus_wall_temp_k")),
                "wall_heatflux_area_avg_w_m2": numeric_or_nan(row.get("wall_heatflux_area_avg_w_m2")),
                "wall_heat_per_length_w_m": numeric_or_nan(row.get("wall_heat_per_length_w_m")),
                "effective_htc_w_m2_k": numeric_or_nan(row.get("effective_htc_w_m2_k")),
                "effective_ua_per_m_w_m_k": numeric_or_nan(row.get("effective_ua_per_m_w_m_k")),
                "effective_thermal_resistance_k_m_w": numeric_or_nan(
                    row.get("effective_thermal_resistance_k_m_w")
                ),
                "fanning_cf_shear": numeric_or_nan(row.get("fanning_cf_shear")),
                "fanning_cf_pressure_drop_prgh": numeric_or_nan(row.get("fanning_cf_pressure_drop_prgh")),
                "dp_major_gradient_pa_per_m": numeric_or_nan(row.get("dp_major_gradient_pa_per_m")),
                "dp_major_gradient_direct_prgh_pa_per_m": numeric_or_nan(
                    row.get("dp_major_gradient_direct_prgh_pa_per_m")
                ),
                "dp_major_gradient_direct_p_pa_per_m": numeric_or_nan(
                    row.get("dp_major_gradient_direct_p_pa_per_m")
                ),
                "flow_alignment_sign": numeric_or_nan(row.get("flow_alignment_sign")),
                "darcy_f_pressure_drop_prgh": numeric_or_nan(row.get("darcy_f_pressure_drop_prgh")),
                "momentum_resistance_estimated_pa_s_kg_m": numeric_or_nan(
                    row.get("momentum_resistance_estimated_pa_s_kg_m")
                ),
                "momentum_resistance_direct_prgh_pa_s_kg_m": numeric_or_nan(
                    row.get("momentum_resistance_direct_prgh_pa_s_kg_m")
                ),
                "thermal_support_status": str(row.get("thermal_support_status", "")),
                "thermal_support_warning_flag": normalize_warning_flag(
                    row.get("thermal_support_warning_flag", "")
                ),
                "yplus_area_avg": float(row["yplus_area_avg"]),
                "yplus_max": float(row["yplus_max"]),
                "warning_flag": normalize_warning_flag(row.get("warning_flag", "")),
            }
        )
    return rows


def load_feature_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "start_p_pa": numeric_or_nan(row["start_p_pa"]),
                "end_p_pa": numeric_or_nan(row["end_p_pa"]),
                "delta_p_pa": numeric_or_nan(row["delta_p_pa"]),
                "start_p_rgh_pa": numeric_or_nan(row["start_p_rgh_pa"]),
                "end_p_rgh_pa": numeric_or_nan(row["end_p_rgh_pa"]),
                "delta_p_rgh_pa": numeric_or_nan(row["delta_p_rgh_pa"]),
                "abs_delta_p_rgh_pa": numeric_or_nan(row["abs_delta_p_rgh_pa"]),
                "profile_dp_pa": numeric_or_nan(row["profile_dp_pa"]),
                "wall_dp_pa": numeric_or_nan(row["wall_dp_pa"]),
                "minor_residual_dp_pa": numeric_or_nan(row["minor_residual_dp_pa"]),
                "minor_k_reference": numeric_or_nan(row["minor_k_reference"]),
                "warning_flag": normalize_warning_flag(row.get("warning_flag", "")),
            }
        )
    return rows


def load_wall_face_sample_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "distance_to_centerline_m": float(row["distance_to_centerline_m"]),
                "area_m2": float(row["area_m2"]),
            }
        )
    return rows


def load_station_definitions(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        sample_token = row.get("sample_index", row.get("bin_index", "0"))
        s_mid_token = row.get("s_m", row.get("s_mid_m", "0"))
        rows.append(
            {
                **row,
                "sample_index": int(sample_token),
                "bin_index": int(row.get("bin_index", sample_token)),
                "s_m": float(s_mid_token),
                "x_m": float(row["x_m"]),
                "y_m": float(row["y_m"]),
                "z_m": float(row["z_m"]),
                "target_ds_m": float(row["target_ds_m"]),
            }
        )
    return rows


def load_boundary_layer_summary_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "span_name": str(row["span_name"]),
                "span_kind": str(row["span_kind"]),
                "landmark_name": str(row["landmark_name"]),
                "landmark_label": str(row["landmark_label"]),
                "landmark_role": str(row["landmark_role"]),
                "s_landmark_m": numeric_or_nan(row.get("s_landmark_m")),
                "line_length_m": numeric_or_nan(row.get("line_length_m")),
                "nearest_bin_index": int(row["nearest_bin_index"]),
                "nearest_bin_s_mid_m": numeric_or_nan(row.get("nearest_bin_s_mid_m")),
                "sample_count": int(row["sample_count"]),
                "valid_sample_count": int(row["valid_sample_count"]),
                "u_core_streamwise_abs_m_s": numeric_or_nan(row.get("u_core_streamwise_abs_m_s")),
                "t_core_k": numeric_or_nan(row.get("t_core_k")),
                "t_wall_area_avg_k": numeric_or_nan(row.get("t_wall_area_avg_k")),
                "bulk_temp_fluid_area_avg_k": numeric_or_nan(row.get("bulk_temp_fluid_area_avg_k")),
                "rho_bulk_kg_m3": numeric_or_nan(row.get("rho_bulk_kg_m3")),
                "tauw_streamwise_mean_abs_pa": numeric_or_nan(row.get("tauw_streamwise_mean_abs_pa")),
                "u_tau_m_s": numeric_or_nan(row.get("u_tau_m_s")),
                "darcy_f_shear": numeric_or_nan(row.get("darcy_f_shear")),
                "fanning_cf_shear": numeric_or_nan(row.get("fanning_cf_shear")),
                "effective_htc_w_m2_k": numeric_or_nan(row.get("effective_htc_w_m2_k")),
                "effective_ua_per_m_w_m_k": numeric_or_nan(row.get("effective_ua_per_m_w_m_k")),
                "effective_thermal_resistance_k_m_w": numeric_or_nan(
                    row.get("effective_thermal_resistance_k_m_w")
                ),
                "momentum_resistance_direct_prgh_pa_s_kg_m": numeric_or_nan(
                    row.get("momentum_resistance_direct_prgh_pa_s_kg_m")
                ),
                "wall_heatflux_area_avg_w_m2": numeric_or_nan(row.get("wall_heatflux_area_avg_w_m2")),
                "delta99_u_m": numeric_or_nan(row.get("delta99_u_m")),
                "delta_star_u_m": numeric_or_nan(row.get("delta_star_u_m")),
                "theta_u_m": numeric_or_nan(row.get("theta_u_m")),
                "shape_factor_u": numeric_or_nan(row.get("shape_factor_u")),
                "delta99_t_m": numeric_or_nan(row.get("delta99_t_m")),
                "velocity_profile_status": str(row.get("velocity_profile_status", "")),
                "thermal_profile_status": str(row.get("thermal_profile_status", "")),
                "profile_status": str(row.get("profile_status", "")),
                "status_note": str(row.get("status_note", "")),
            }
        )
    return rows


def load_azimuthal_summary_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "span_name": str(row["span_name"]),
                "thermal_role": str(row.get("thermal_role", "")),
                "thermal_role_group": str(row.get("thermal_role_group", "")),
                "streamwise_bin_index": int(row["streamwise_bin_index"]),
                "streamwise_bin_center_local_m": numeric_or_nan(row.get("streamwise_bin_center_local_m")),
                "streamwise_bin_center_global_m": numeric_or_nan(row.get("streamwise_bin_center_global_m")),
                "theta_bin_index": int(row["theta_bin_index"]),
                "theta_bin_center_rad": numeric_or_nan(row.get("theta_bin_center_rad")),
                "theta_bin_center_deg": numeric_or_nan(row.get("theta_bin_center_deg")),
                "area_m2": numeric_or_nan(row.get("area_m2")),
                "face_count": int(row["face_count"]),
                "mean_s_m": numeric_or_nan(row.get("mean_s_m")),
                "mean_theta_deg": numeric_or_nan(row.get("mean_theta_deg")),
                "mean_radial_distance_m": numeric_or_nan(row.get("mean_radial_distance_m")),
                "mean_yplus": numeric_or_nan(row.get("mean_yplus")),
                "mean_p_pa": numeric_or_nan(row.get("mean_p_pa")),
                "mean_p_rgh_pa": numeric_or_nan(row.get("mean_p_rgh_pa")),
                "mean_t_wall_k": numeric_or_nan(row.get("mean_t_wall_k")),
                "mean_wall_shear_streamwise_pa": numeric_or_nan(row.get("mean_wall_shear_streamwise_pa")),
                "mean_wall_shear_streamwise_abs_pa": numeric_or_nan(row.get("mean_wall_shear_streamwise_abs_pa")),
                "mean_wall_shear_magnitude_pa": numeric_or_nan(row.get("mean_wall_shear_magnitude_pa")),
                "mean_wall_heat_flux_w_m2": numeric_or_nan(row.get("mean_wall_heat_flux_w_m2")),
                "total_wall_heat_w": numeric_or_nan(row.get("total_wall_heat_w")),
            }
        )
    return rows


def span_dp_gradient(row: dict[str, Any]) -> float:
    rho = float(row["rho_bulk_kg_m3"])
    bulk_u = float(row["bulk_velocity_m_s"])
    darcy_f = float(row["darcy_f"])
    dh = float(row["hydraulic_diameter_geom_m"])
    if not math.isfinite(darcy_f) or not math.isfinite(dh) or dh <= defs.EPS:
        return math.nan
    return float(darcy_f * rho * bulk_u * bulk_u / max(2.0 * dh, defs.EPS))


def finite_difference_pressure_drop_gradient(
    s_values: list[float],
    pressure_values: list[float],
) -> list[float]:
    gradients: list[float] = [math.nan] * len(s_values)
    if len(s_values) < 2:
        return gradients
    for index in range(len(s_values)):
        p_here = pressure_values[index]
        if not math.isfinite(p_here):
            continue
        if index == 0:
            if not math.isfinite(pressure_values[index + 1]):
                continue
            ds = s_values[index + 1] - s_values[index]
            if abs(ds) <= defs.EPS:
                continue
            gradients[index] = -float((pressure_values[index + 1] - p_here) / ds)
        elif index == len(s_values) - 1:
            if not math.isfinite(pressure_values[index - 1]):
                continue
            ds = s_values[index] - s_values[index - 1]
            if abs(ds) <= defs.EPS:
                continue
            gradients[index] = -float((p_here - pressure_values[index - 1]) / ds)
        else:
            p_prev = pressure_values[index - 1]
            p_next = pressure_values[index + 1]
            if not math.isfinite(p_prev) or not math.isfinite(p_next):
                continue
            ds = s_values[index + 1] - s_values[index - 1]
            if abs(ds) <= defs.EPS:
                continue
            gradients[index] = -float((p_next - p_prev) / ds)
    return gradients


def pressure_drop_based_darcy_f(row: dict[str, Any], dp_gradient: float) -> float:
    rho = float(row["rho_bulk_kg_m3"])
    bulk_u = float(row["bulk_velocity_m_s"])
    dh = float(row["hydraulic_diameter_geom_m"])
    if not math.isfinite(dp_gradient) or not math.isfinite(rho) or not math.isfinite(bulk_u) or not math.isfinite(dh):
        return math.nan
    if dh <= defs.EPS or bulk_u <= defs.EPS:
        return math.nan
    return float(2.0 * dh * dp_gradient / max(rho * bulk_u * bulk_u, defs.EPS))


def summarize_major_rows(rows: list[dict[str, Any]], span_order: list[str], major_spans: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_span: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_span[str(row["span_name"])].append(row)

    cumulative_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for span_name in span_order:
        payload = sorted(by_span.get(span_name, []), key=lambda row: (float(row["time_s"]), int(row["bin_index"])))
        grouped_by_time: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for row in payload:
            grouped_by_time[float(row["time_s"])].append(row)

        span_meta = major_spans[span_name]
        mean_values: list[float] = []
        pressure_f_values: list[float] = []
        max_values: list[float] = []
        grad_values_estimated: list[float] = []
        grad_values_direct_prgh: list[float] = []
        grad_values_direct_p: list[float] = []
        fanning_cf_values: list[float] = []
        fanning_cf_pressure_values: list[float] = []
        momentum_resistance_estimated_values: list[float] = []
        momentum_resistance_direct_values: list[float] = []
        dp_values_estimated: list[float] = []
        dp_values_direct_prgh: list[float] = []
        wall_temp_values: list[float] = []
        bulk_temp_values: list[float] = []
        bulk_temp_tp_proxy_values: list[float] = []
        delta_t_values: list[float] = []
        delta_t_tp_proxy_values: list[float] = []
        wall_heatflux_values: list[float] = []
        htc_values: list[float] = []
        htc_tp_proxy_values: list[float] = []
        ua_per_m_values: list[float] = []
        ua_per_m_tp_proxy_values: list[float] = []
        thermal_resistance_values: list[float] = []
        thermal_resistance_tp_proxy_values: list[float] = []
        cross_section_area_values: list[float] = []
        cross_section_area_ratio_values: list[float] = []
        cross_section_area_ratio_reference_values: list[float] = []
        cross_section_positive_flux_values: list[float] = []
        thermal_valid_rows = 0
        thermal_warning_rows = 0
        valid_bins = 0
        direct_prgh_valid_bins = 0
        total_rows = 0
        empty_rows = 0
        warned_rows = 0
        flow_alignment_sign_summary = math.nan

        for time_value, rows_at_time in sorted(grouped_by_time.items()):
            rows_at_time.sort(key=lambda row: int(row["bin_index"]))
            s_mid_values = [float(row["s_mid_m"]) for row in rows_at_time]
            p_wall_values = [float(row["p_wall_area_avg_pa"]) for row in rows_at_time]
            p_rgh_values = [float(row["p_rgh_wall_area_avg_pa"]) for row in rows_at_time]
            raw_direct_prgh_gradients = finite_difference_pressure_drop_gradient(s_mid_values, p_rgh_values)
            raw_direct_p_gradients = finite_difference_pressure_drop_gradient(s_mid_values, p_wall_values)
            first_valid_prgh = next((value for value in p_rgh_values if math.isfinite(value)), math.nan)
            last_valid_prgh = next((value for value in reversed(p_rgh_values) if math.isfinite(value)), math.nan)
            if math.isfinite(first_valid_prgh) and math.isfinite(last_valid_prgh) and (first_valid_prgh - last_valid_prgh) < 0.0:
                flow_alignment_sign = -1.0
            else:
                flow_alignment_sign = 1.0
            flow_alignment_sign_summary = flow_alignment_sign
            direct_prgh_gradients = [
                float(flow_alignment_sign * value) if math.isfinite(value) else math.nan
                for value in raw_direct_prgh_gradients
            ]
            direct_p_gradients = [
                float(flow_alignment_sign * value) if math.isfinite(value) else math.nan
                for value in raw_direct_p_gradients
            ]
            cumulative_dp_estimated = 0.0
            cumulative_dp_direct_prgh = 0.0
            for index, row in enumerate(rows_at_time):
                total_rows += 1
                if int(row["wall_face_count"]) <= 0:
                    empty_rows += 1
                if normalize_warning_flag(row.get("warning_flag", "")) == "yes":
                    warned_rows += 1
                dp_gradient_estimated = span_dp_gradient(row)
                dp_gradient_direct_prgh = direct_prgh_gradients[index]
                dp_gradient_direct_p = direct_p_gradients[index]
                darcy_f_pressure_drop = pressure_drop_based_darcy_f(row, dp_gradient_direct_prgh)
                fanning_cf_value = safe_float(row.get("fanning_cf_shear"))
                fanning_cf_pressure_value = safe_float(row.get("fanning_cf_pressure_drop_prgh"))
                momentum_resistance_estimated_value = safe_float(
                    row.get("momentum_resistance_estimated_pa_s_kg_m")
                )
                momentum_resistance_direct_value = safe_float(
                    row.get("momentum_resistance_direct_prgh_pa_s_kg_m")
                )
                ds_value = float(row["s_end_m"] - row["s_start_m"])
                if math.isfinite(dp_gradient_estimated):
                    delta_dp_estimated = dp_gradient_estimated * ds_value
                    cumulative_dp_estimated += delta_dp_estimated
                    mean_values.append(float(row["darcy_f"]))
                    grad_values_estimated.append(dp_gradient_estimated)
                    max_values.append(float(row["yplus_max"]))
                    valid_bins += 1
                else:
                    delta_dp_estimated = math.nan
                if math.isfinite(dp_gradient_direct_prgh):
                    grad_values_direct_prgh.append(dp_gradient_direct_prgh)
                if math.isfinite(dp_gradient_direct_p):
                    grad_values_direct_p.append(dp_gradient_direct_p)
                if math.isfinite(darcy_f_pressure_drop):
                    pressure_f_values.append(darcy_f_pressure_drop)
                if fanning_cf_value is not None and math.isfinite(fanning_cf_value):
                    fanning_cf_values.append(float(fanning_cf_value))
                if fanning_cf_pressure_value is not None and math.isfinite(fanning_cf_pressure_value):
                    fanning_cf_pressure_values.append(float(fanning_cf_pressure_value))
                if (
                    momentum_resistance_estimated_value is not None
                    and math.isfinite(momentum_resistance_estimated_value)
                ):
                    momentum_resistance_estimated_values.append(float(momentum_resistance_estimated_value))
                if (
                    momentum_resistance_direct_value is not None
                    and math.isfinite(momentum_resistance_direct_value)
                ):
                    momentum_resistance_direct_values.append(float(momentum_resistance_direct_value))
                wall_temp_value = safe_float(row.get("t_wall_area_avg_k"))
                bulk_temp_value = safe_float(row.get("bulk_temp_fluid_area_avg_k"))
                bulk_temp_tp_proxy_value = safe_float(row.get("bulk_temp_tp_endpoint_proxy_k"))
                delta_t_value = safe_float(row.get("bulk_minus_wall_temp_k"))
                delta_t_tp_proxy_value = safe_float(row.get("bulk_minus_wall_tp_endpoint_proxy_k"))
                wall_heatflux_value = safe_float(row.get("wall_heatflux_area_avg_w_m2"))
                htc_value = safe_float(row.get("effective_htc_w_m2_k"))
                htc_tp_proxy_value = safe_float(row.get("effective_htc_tp_endpoint_proxy_w_m2_k"))
                ua_per_m_value = safe_float(row.get("effective_ua_per_m_w_m_k"))
                ua_per_m_tp_proxy_value = safe_float(row.get("effective_ua_per_m_tp_endpoint_proxy_w_m_k"))
                thermal_resistance_value = safe_float(row.get("effective_thermal_resistance_k_m_w"))
                thermal_resistance_tp_proxy_value = safe_float(
                    row.get("effective_thermal_resistance_tp_endpoint_proxy_k_m_w")
                )
                cross_section_area_value = safe_float(row.get("bulk_cross_section_area_m2"))
                cross_section_area_ratio_value = safe_float(row.get("bulk_cross_section_area_ratio_to_geom"))
                cross_section_area_ratio_reference_value = safe_float(
                    row.get("bulk_cross_section_chosen_region_area_ratio_to_reference")
                )
                cross_section_positive_flux_value = safe_float(
                    row.get("bulk_cross_section_chosen_region_positive_mass_flux_kg_s")
                )
                thermal_support_warning_flag = normalize_warning_flag(
                    row.get("thermal_support_warning_flag", "")
                )
                if wall_temp_value is not None and math.isfinite(wall_temp_value):
                    wall_temp_values.append(float(wall_temp_value))
                if bulk_temp_value is not None and math.isfinite(bulk_temp_value):
                    bulk_temp_values.append(float(bulk_temp_value))
                if bulk_temp_tp_proxy_value is not None and math.isfinite(bulk_temp_tp_proxy_value):
                    bulk_temp_tp_proxy_values.append(float(bulk_temp_tp_proxy_value))
                if delta_t_value is not None and math.isfinite(delta_t_value):
                    delta_t_values.append(float(delta_t_value))
                if delta_t_tp_proxy_value is not None and math.isfinite(delta_t_tp_proxy_value):
                    delta_t_tp_proxy_values.append(float(delta_t_tp_proxy_value))
                if wall_heatflux_value is not None and math.isfinite(wall_heatflux_value):
                    wall_heatflux_values.append(float(wall_heatflux_value))
                if htc_value is not None and math.isfinite(htc_value):
                    htc_values.append(float(htc_value))
                if htc_tp_proxy_value is not None and math.isfinite(htc_tp_proxy_value):
                    htc_tp_proxy_values.append(float(htc_tp_proxy_value))
                if ua_per_m_value is not None and math.isfinite(ua_per_m_value):
                    ua_per_m_values.append(float(ua_per_m_value))
                if ua_per_m_tp_proxy_value is not None and math.isfinite(ua_per_m_tp_proxy_value):
                    ua_per_m_tp_proxy_values.append(float(ua_per_m_tp_proxy_value))
                if thermal_resistance_value is not None and math.isfinite(thermal_resistance_value):
                    thermal_resistance_values.append(float(thermal_resistance_value))
                if (
                    thermal_resistance_tp_proxy_value is not None
                    and math.isfinite(thermal_resistance_tp_proxy_value)
                ):
                    thermal_resistance_tp_proxy_values.append(float(thermal_resistance_tp_proxy_value))
                if cross_section_area_value is not None and math.isfinite(cross_section_area_value):
                    cross_section_area_values.append(float(cross_section_area_value))
                if cross_section_area_ratio_value is not None and math.isfinite(cross_section_area_ratio_value):
                    cross_section_area_ratio_values.append(float(cross_section_area_ratio_value))
                if (
                    cross_section_area_ratio_reference_value is not None
                    and math.isfinite(cross_section_area_ratio_reference_value)
                ):
                    cross_section_area_ratio_reference_values.append(
                        float(cross_section_area_ratio_reference_value)
                    )
                if cross_section_positive_flux_value is not None and math.isfinite(cross_section_positive_flux_value):
                    cross_section_positive_flux_values.append(float(cross_section_positive_flux_value))
                if thermal_support_warning_flag == "yes":
                    thermal_warning_rows += 1
                else:
                    thermal_valid_rows += 1
                p_rgh_value = p_rgh_values[index]
                if math.isfinite(first_valid_prgh) and math.isfinite(p_rgh_value):
                    cumulative_dp_direct_prgh = float(flow_alignment_sign * (first_valid_prgh - p_rgh_value))
                else:
                    cumulative_dp_direct_prgh = math.nan
                if math.isfinite(dp_gradient_direct_prgh):
                    delta_dp_direct_prgh = dp_gradient_direct_prgh * ds_value
                    direct_prgh_valid_bins += 1
                else:
                    delta_dp_direct_prgh = math.nan
                cumulative_rows.append(
                    {
                        "source_id": row["source_id"],
                        "time_s": time_value,
                        "span_name": span_name,
                        "span_kind": span_meta["kind"],
                        "bin_index": row["bin_index"],
                        "s_start_m": row["s_start_m"],
                        "s_end_m": row["s_end_m"],
                        "s_mid_m": row["s_mid_m"],
                        "dp_major_gradient_pa_per_m": dp_gradient_estimated,
                        "dp_major_gradient_estimated_pa_per_m": dp_gradient_estimated,
                        "dp_major_gradient_direct_prgh_pa_per_m": dp_gradient_direct_prgh,
                        "dp_major_gradient_direct_p_pa_per_m": dp_gradient_direct_p,
                        "delta_dp_major_pa": delta_dp_estimated,
                        "delta_dp_major_estimated_pa": delta_dp_estimated,
                        "delta_dp_major_direct_prgh_pa": delta_dp_direct_prgh,
                        "cumulative_dp_major_pa": cumulative_dp_estimated,
                        "cumulative_dp_major_estimated_pa": cumulative_dp_estimated,
                        "cumulative_dp_major_direct_prgh_pa": cumulative_dp_direct_prgh,
                        "flow_alignment_sign": flow_alignment_sign,
                        "darcy_f": row["darcy_f"],
                        "darcy_f_shear": row["darcy_f"],
                        "darcy_f_pressure_drop_prgh": darcy_f_pressure_drop,
                        "fanning_cf_shear": row["fanning_cf_shear"],
                        "fanning_cf_pressure_drop_prgh": row["fanning_cf_pressure_drop_prgh"],
                        "momentum_resistance_estimated_pa_s_kg_m": row[
                            "momentum_resistance_estimated_pa_s_kg_m"
                        ],
                        "momentum_resistance_direct_prgh_pa_s_kg_m": row[
                            "momentum_resistance_direct_prgh_pa_s_kg_m"
                        ],
                        "p_wall_area_avg_pa": row["p_wall_area_avg_pa"],
                        "p_rgh_wall_area_avg_pa": row["p_rgh_wall_area_avg_pa"],
                        "t_wall_area_avg_k": row["t_wall_area_avg_k"],
                        "bulk_temp_fluid_area_avg_k": row["bulk_temp_fluid_area_avg_k"],
                        "bulk_temp_area_weighted_k": row["bulk_temp_area_weighted_k"],
                        "bulk_temp_union_area_avg_k": row["bulk_temp_union_area_avg_k"],
                        "bulk_cross_section_face_count": row["bulk_cross_section_face_count"],
                        "bulk_cross_section_area_m2": row["bulk_cross_section_area_m2"],
                        "bulk_cross_section_total_face_count": row["bulk_cross_section_total_face_count"],
                        "bulk_cross_section_total_area_m2": row["bulk_cross_section_total_area_m2"],
                        "bulk_cross_section_region_count": row["bulk_cross_section_region_count"],
                        "bulk_cross_section_reference_area_m2": row["bulk_cross_section_reference_area_m2"],
                        "bulk_cross_section_area_ratio_to_geom": row["bulk_cross_section_area_ratio_to_geom"],
                        "bulk_cross_section_chosen_region_area_ratio_to_reference": row[
                            "bulk_cross_section_chosen_region_area_ratio_to_reference"
                        ],
                        "bulk_cross_section_chosen_region_signed_mass_flux_kg_s": row[
                            "bulk_cross_section_chosen_region_signed_mass_flux_kg_s"
                        ],
                        "bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s": row[
                            "bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s"
                        ],
                        "bulk_cross_section_chosen_region_positive_mass_flux_kg_s": row[
                            "bulk_cross_section_chosen_region_positive_mass_flux_kg_s"
                        ],
                        "bulk_cross_section_region_selection_status": row[
                            "bulk_cross_section_region_selection_status"
                        ],
                        "bulk_temp_tp_endpoint_proxy_k": row["bulk_temp_tp_endpoint_proxy_k"],
                        "bulk_minus_wall_tp_endpoint_proxy_k": row["bulk_minus_wall_tp_endpoint_proxy_k"],
                        "effective_htc_tp_endpoint_proxy_w_m2_k": row["effective_htc_tp_endpoint_proxy_w_m2_k"],
                        "effective_ua_per_m_tp_endpoint_proxy_w_m_k": row["effective_ua_per_m_tp_endpoint_proxy_w_m_k"],
                        "effective_thermal_resistance_tp_endpoint_proxy_k_m_w": row[
                            "effective_thermal_resistance_tp_endpoint_proxy_k_m_w"
                        ],
                        "bulk_minus_wall_temp_k": row["bulk_minus_wall_temp_k"],
                        "wall_heatflux_area_avg_w_m2": row["wall_heatflux_area_avg_w_m2"],
                        "wall_heat_per_length_w_m": row["wall_heat_per_length_w_m"],
                        "effective_htc_w_m2_k": row["effective_htc_w_m2_k"],
                        "effective_ua_per_m_w_m_k": row["effective_ua_per_m_w_m_k"],
                        "effective_thermal_resistance_k_m_w": row["effective_thermal_resistance_k_m_w"],
                        "thermal_support_status": row["thermal_support_status"],
                        "thermal_support_warning_flag": row["thermal_support_warning_flag"],
                        "hydraulic_diameter_geom_m": row["hydraulic_diameter_geom_m"],
                        "bulk_velocity_m_s": row["bulk_velocity_m_s"],
                        "rho_bulk_kg_m3": row["rho_bulk_kg_m3"],
                        "warning_flag": normalize_warning_flag(row.get("warning_flag", "")),
                    }
                )
            if rows_at_time:
                dp_values_estimated.append(cumulative_dp_estimated)
                dp_values_direct_prgh.append(cumulative_dp_direct_prgh)

        summary_rows.append(
            {
                "span_name": span_name,
                "span_kind": span_meta["kind"],
                "start_patch": span_meta["start_patch"],
                "end_patch": span_meta["end_patch"],
                "mean_darcy_f": defs.safe_nanmean(mean_values),
                "mean_darcy_f_pressure_drop_prgh": defs.safe_nanmean(pressure_f_values),
                "mean_fanning_cf_shear": defs.safe_nanmean(fanning_cf_values),
                "mean_fanning_cf_pressure_drop_prgh": defs.safe_nanmean(fanning_cf_pressure_values),
                "mean_dp_major_gradient_pa_per_m": defs.safe_nanmean(grad_values_estimated),
                "mean_dp_major_gradient_direct_prgh_pa_per_m": defs.safe_nanmean(grad_values_direct_prgh),
                "mean_dp_major_gradient_direct_p_pa_per_m": defs.safe_nanmean(grad_values_direct_p),
                "mean_momentum_resistance_estimated_pa_s_kg_m": defs.safe_nanmean(
                    momentum_resistance_estimated_values
                ),
                "mean_momentum_resistance_direct_prgh_pa_s_kg_m": defs.safe_nanmean(
                    momentum_resistance_direct_values
                ),
                "mean_terminal_dp_major_pa": defs.safe_nanmean(dp_values_estimated),
                "mean_terminal_dp_major_direct_prgh_pa": defs.safe_nanmean(dp_values_direct_prgh),
                "flow_alignment_sign": flow_alignment_sign_summary,
                "mean_t_wall_area_avg_k": defs.safe_nanmean(wall_temp_values),
                "mean_bulk_temp_fluid_area_avg_k": defs.safe_nanmean(bulk_temp_values),
                "mean_bulk_temp_tp_endpoint_proxy_k": defs.safe_nanmean(bulk_temp_tp_proxy_values),
                "mean_bulk_minus_wall_temp_k": defs.safe_nanmean(delta_t_values),
                "mean_bulk_minus_wall_tp_endpoint_proxy_k": defs.safe_nanmean(delta_t_tp_proxy_values),
                "mean_wall_heatflux_area_avg_w_m2": defs.safe_nanmean(wall_heatflux_values),
                "mean_effective_htc_w_m2_k": defs.safe_nanmean(htc_values),
                "mean_effective_htc_tp_endpoint_proxy_w_m2_k": defs.safe_nanmean(htc_tp_proxy_values),
                "mean_effective_ua_per_m_w_m_k": defs.safe_nanmean(ua_per_m_values),
                "mean_effective_ua_per_m_tp_endpoint_proxy_w_m_k": defs.safe_nanmean(ua_per_m_tp_proxy_values),
                "mean_effective_thermal_resistance_k_m_w": defs.safe_nanmean(thermal_resistance_values),
                "mean_effective_thermal_resistance_tp_endpoint_proxy_k_m_w": defs.safe_nanmean(
                    thermal_resistance_tp_proxy_values
                ),
                "mean_bulk_cross_section_area_m2": defs.safe_nanmean(cross_section_area_values),
                "mean_bulk_cross_section_area_ratio_to_geom": defs.safe_nanmean(cross_section_area_ratio_values),
                "mean_bulk_cross_section_area_ratio_to_reference": defs.safe_nanmean(
                    cross_section_area_ratio_reference_values
                ),
                "mean_bulk_cross_section_positive_mass_flux_kg_s": defs.safe_nanmean(
                    cross_section_positive_flux_values
                ),
                "max_yplus": max(max_values) if max_values else math.nan,
                "time_sample_count": len(grouped_by_time),
                "valid_bin_count": valid_bins,
                "direct_prgh_valid_bin_count": direct_prgh_valid_bins,
                "thermal_valid_bin_count": thermal_valid_rows,
                "total_bin_row_count": total_rows,
                "warning_fraction": float(warned_rows / max(total_rows, 1)),
                "thermal_warning_fraction": float(thermal_warning_rows / max(total_rows, 1)),
                "empty_bin_fraction": float(empty_rows / max(total_rows, 1)),
            }
        )
    return cumulative_rows, summary_rows


def aggregate_boundary_layer_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["span_name"]), str(row["landmark_name"]))].append(row)

    output_rows: list[dict[str, Any]] = []
    for (span_name, landmark_name), payload in sorted(grouped.items()):
        first = payload[0]
        output_rows.append(
            {
                "span_name": span_name,
                "span_kind": str(first["span_kind"]),
                "landmark_name": landmark_name,
                "landmark_label": str(first["landmark_label"]),
                "landmark_role": str(first["landmark_role"]),
                "s_landmark_m": numeric_or_nan(first.get("s_landmark_m")),
                "line_length_m": defs.safe_nanmean([numeric_or_nan(row.get("line_length_m")) for row in payload]),
                "time_sample_count": len(payload),
                "usable_profile_count": sum(1 for row in payload if row["profile_status"] == "usable"),
                "mean_delta99_u_m": defs.safe_nanmean([numeric_or_nan(row.get("delta99_u_m")) for row in payload]),
                "mean_delta_star_u_m": defs.safe_nanmean([numeric_or_nan(row.get("delta_star_u_m")) for row in payload]),
                "mean_theta_u_m": defs.safe_nanmean([numeric_or_nan(row.get("theta_u_m")) for row in payload]),
                "mean_shape_factor_u": defs.safe_nanmean([numeric_or_nan(row.get("shape_factor_u")) for row in payload]),
                "mean_delta99_t_m": defs.safe_nanmean([numeric_or_nan(row.get("delta99_t_m")) for row in payload]),
                "mean_u_tau_m_s": defs.safe_nanmean([numeric_or_nan(row.get("u_tau_m_s")) for row in payload]),
                "mean_fanning_cf_shear": defs.safe_nanmean(
                    [numeric_or_nan(row.get("fanning_cf_shear")) for row in payload]
                ),
                "mean_effective_thermal_resistance_k_m_w": defs.safe_nanmean(
                    [numeric_or_nan(row.get("effective_thermal_resistance_k_m_w")) for row in payload]
                ),
                "mean_momentum_resistance_direct_prgh_pa_s_kg_m": defs.safe_nanmean(
                    [numeric_or_nan(row.get("momentum_resistance_direct_prgh_pa_s_kg_m")) for row in payload]
                ),
                "profile_statuses": ", ".join(sorted({str(row["profile_status"]) for row in payload})),
            }
        )
    return output_rows


def feature_reference_length_m(feature_name: str, station_centers: dict[str, tuple[float, float, float]]) -> float:
    if feature_name == "corner_lower_left":
        return 0.5 * (
            defs.distance(station_centers["TP3"], station_centers["TW6"])
            + defs.distance(station_centers["TP3"], station_centers["TW7"])
        )
    if feature_name == "corner_lower_right":
        return 0.5 * (
            defs.distance(station_centers["TP2"], station_centers["TW3"])
            + defs.distance(station_centers["TP2"], station_centers["TW4"])
        )
    if feature_name == "corner_upper_right":
        return 0.5 * (
            defs.distance(station_centers["TP1"], station_centers["TW1"])
            + defs.distance(station_centers["TP1"], station_centers["TW9"])
        )
    if feature_name == "corner_upper_left":
        return 0.5 * (
            defs.distance(station_centers["TP6"], station_centers["TW8"])
            + defs.distance(station_centers["TP6"], station_centers["TW11"])
        )
    if feature_name == "test_section_complex":
        return defs.distance(station_centers["TP4"], station_centers["TP5"])
    return math.nan


def merge_feature_budget(
    feature_rows: list[dict[str, Any]],
    cumulative_major_rows: list[dict[str, Any]],
    source_id: str,
    feature_budgets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    station_centers = defs.load_station_centers(source_id)
    gradients_by_span_time: dict[tuple[str, float], list[float]] = defaultdict(list)
    rho_by_span_time: dict[tuple[str, float], list[float]] = defaultdict(list)
    u_by_span_time: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in cumulative_major_rows:
        key = (str(row["span_name"]), float(row["time_s"]))
        gradient_value = safe_float(row["dp_major_gradient_pa_per_m"], math.nan)
        if gradient_value is not None and math.isfinite(gradient_value):
            gradients_by_span_time[key].append(float(gradient_value))
            rho_by_span_time[key].append(float(row["rho_bulk_kg_m3"]))
            u_by_span_time[key].append(float(row["bulk_velocity_m_s"]))

    output_rows: list[dict[str, Any]] = []
    for row in feature_rows:
        feature_name = str(row["feature_name"])
        feature_def = feature_budgets[feature_name]
        adjacent = feature_def["adjacent_major_spans"]
        time_value = float(row["time_s"])
        gradient_candidates = [
            defs.safe_nanmean(gradients_by_span_time.get((span_name, time_value), []))
            for span_name in adjacent
        ]
        rho_candidates = [
            defs.safe_nanmean(rho_by_span_time.get((span_name, time_value), []))
            for span_name in adjacent
        ]
        u_candidates = [
            defs.safe_nanmean(u_by_span_time.get((span_name, time_value), []))
            for span_name in adjacent
        ]
        reference_gradient = defs.safe_nanmean(gradient_candidates)
        rho_reference = defs.safe_nanmean(rho_candidates)
        u_reference = defs.safe_nanmean(u_candidates)
        reference_length = feature_reference_length_m(feature_name, station_centers)
        wall_dp_pa = (
            float(reference_gradient * reference_length)
            if math.isfinite(reference_gradient) and math.isfinite(reference_length)
            else math.nan
        )
        profile_dp_pa = float(row["profile_dp_pa"]) if math.isfinite(float(row["profile_dp_pa"])) else math.nan
        minor_residual = (
            float(abs(float(row["abs_delta_p_rgh_pa"])) - (wall_dp_pa if math.isfinite(wall_dp_pa) else 0.0))
            if math.isfinite(float(row["abs_delta_p_rgh_pa"]))
            else math.nan
        )
        minor_k = (
            float(2.0 * minor_residual / max(rho_reference * u_reference * u_reference, defs.EPS))
            if math.isfinite(minor_residual) and math.isfinite(rho_reference) and math.isfinite(u_reference)
            else math.nan
        )
        warning_sources: list[str] = []
        if normalize_warning_flag(row.get("warning_flag", "")) == "yes":
            warning_sources.append("raw_feature_warning")
        if not math.isfinite(wall_dp_pa):
            warning_sources.append("missing_wall_reference")
        if not math.isfinite(minor_residual):
            warning_sources.append("missing_minor_residual")
        if math.isfinite(minor_residual) and minor_residual < -defs.EPS:
            warning_sources.append("negative_minor_residual")
        warning_flag = "yes" if warning_sources else "no"
        note = "profile correction not yet sampled; wall reference inferred from adjacent major-span mean gradients"
        if warning_sources:
            note += f". warning_sources={','.join(warning_sources)}."
        output_rows.append(
            {
                **row,
                "reference_length_m": reference_length,
                "reference_major_dp_pa": wall_dp_pa,
                "profile_dp_pa": profile_dp_pa,
                "wall_dp_pa": wall_dp_pa,
                "minor_residual_dp_pa": minor_residual,
                "minor_k_reference": minor_k,
                "warning_flag": warning_flag,
                "note": note,
            }
        )
    return output_rows


def summarize_feature_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["feature_name"])].append(row)
    summary_rows: list[dict[str, Any]] = []
    for feature_name, payload in grouped.items():
        summary_rows.append(
            {
                "feature_name": feature_name,
                "feature_kind": payload[0]["feature_kind"],
                "start_patch": payload[0]["start_patch"],
                "end_patch": payload[0]["end_patch"],
                "reference_length_m": defs.safe_nanmean([float(row["reference_length_m"]) for row in payload]),
                "mean_abs_delta_p_rgh_pa": defs.safe_nanmean([float(row["abs_delta_p_rgh_pa"]) for row in payload]),
                "mean_reference_major_dp_pa": defs.safe_nanmean([float(row["reference_major_dp_pa"]) for row in payload]),
                "mean_minor_residual_dp_pa": defs.safe_nanmean([float(row["minor_residual_dp_pa"]) for row in payload]),
                "mean_minor_k_reference": defs.safe_nanmean([float(row["minor_k_reference"]) for row in payload]),
                "warning_fraction": float(
                    sum(1 for row in payload if normalize_warning_flag(row.get("warning_flag", "")) == "yes") / max(len(payload), 1)
                ),
                "time_sample_count": len(payload),
            }
        )
    return sorted(summary_rows, key=lambda row: row["feature_name"])


def enrich_major_summary_rows(
    summary_rows: list[dict[str, Any]],
    wall_face_rows: list[dict[str, Any]],
    mdot_monitor_area_m2_by_span: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    distances_by_span: dict[str, list[float]] = defaultdict(list)
    for row in wall_face_rows:
        distances_by_span[str(row["span_name"])].append(float(row["distance_to_centerline_m"]))

    enriched_rows: list[dict[str, Any]] = []
    quarantined_spans: list[str] = []
    for row in summary_rows:
        span_name = str(row["span_name"])
        distances = sorted(distances_by_span.get(span_name, []))
        monitor_area = safe_float(mdot_monitor_area_m2_by_span.get(span_name))
        reference_radius = math.sqrt(max(monitor_area, defs.EPS) / math.pi) if monitor_area is not None else math.nan
        projection_threshold = max(0.05, 3.0 * reference_radius) if math.isfinite(reference_radius) else 0.05
        median_distance = distances[len(distances) // 2] if distances else math.nan
        p95_distance = distances[int(0.95 * (len(distances) - 1))] if distances else math.nan
        summary_status = "usable"
        status_note = ""
        if math.isfinite(median_distance) and median_distance > projection_threshold:
            summary_status = "quarantined_projection_misregistration"
            status_note = "median projected face distance exceeds the span reference threshold"
            quarantined_spans.append(span_name)
        elif float(row["warning_fraction"]) >= 0.5:
            summary_status = "warning_heavy"
            status_note = "more than half of retained bin rows are warning-flagged"
        enriched_rows.append(
            {
                **row,
                "median_face_distance_to_centerline_m": float(median_distance),
                "p95_face_distance_to_centerline_m": float(p95_distance),
                "projection_distance_reference_m": float(projection_threshold),
                "summary_status": summary_status,
                "status_note": status_note,
            }
        )
    return enriched_rows, quarantined_spans


def mean_profile_by_span(rows: list[dict[str, Any]], value_key: str) -> dict[str, tuple[list[float], list[float]]]:
    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    s_mid_map: dict[str, dict[int, float]] = defaultdict(dict)
    for row in rows:
        value = safe_float(row.get(value_key))
        if value is None or not math.isfinite(value):
            continue
        span_name = str(row["span_name"])
        bin_index = int(row["bin_index"])
        grouped[span_name][bin_index].append(float(value))
        s_mid_map[span_name][bin_index] = float(row["s_mid_m"])
    profile_map: dict[str, tuple[list[float], list[float]]] = {}
    for span_name, by_bin in grouped.items():
        indices = sorted(by_bin)
        s_values = [s_mid_map[span_name][index] for index in indices]
        mean_values = [defs.safe_nanmean(by_bin[index]) for index in indices]
        profile_map[span_name] = (s_values, mean_values)
    return profile_map


def span_lengths_from_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    lengths: dict[str, float] = {}
    for row in rows:
        span_name = str(row["span_name"])
        lengths[span_name] = max(lengths.get(span_name, 0.0), float(row["s_end_m"]))
    return lengths


def build_loop_offsets(span_order: list[str], span_lengths: dict[str, float]) -> dict[str, float]:
    offsets: dict[str, float] = {}
    running_length = 0.0
    for span_name in span_order:
        offsets[span_name] = running_length
        running_length += float(span_lengths.get(span_name, 0.0))
    return offsets


def merge_azimuthal_transport_rows(
    rows: list[dict[str, Any]],
    major_rows: list[dict[str, Any]],
    span_order: list[str],
) -> tuple[list[dict[str, Any]], float]:
    span_lengths = span_lengths_from_rows(major_rows)
    offsets = build_loop_offsets(span_order, span_lengths)
    total_length = sum(float(span_lengths.get(span_name, 0.0)) for span_name in span_order)
    major_lookup = {
        (float(row["time_s"]), str(row["span_name"]), int(row["bin_index"])): row
        for row in major_rows
    }

    merged_rows: list[dict[str, Any]] = []
    for row in rows:
        key = (float(row["time_s"]), str(row["span_name"]), int(row["streamwise_bin_index"]))
        major_row = major_lookup.get(key)
        if major_row is None:
            merged_rows.append(
                {
                    **row,
                    "loop_s_mid_m": math.nan,
                    "loop_s_fraction": math.nan,
                    "streamwise_bin_length_m": math.nan,
                    "rho_bulk_kg_m3": math.nan,
                    "bulk_velocity_m_s": math.nan,
                    "fanning_cf_shear": math.nan,
                    "darcy_f_shear": math.nan,
                    "wall_heat_per_length_w_m": math.nan,
                    "wall_heat_abs_per_length_w_m": math.nan,
                    "merge_status": "missing_major_bin",
                }
            )
            continue

        ds_m = max(float(major_row["s_end_m"]) - float(major_row["s_start_m"]), defs.EPS)
        rho_bulk = float(major_row["rho_bulk_kg_m3"])
        bulk_velocity = float(major_row["bulk_velocity_m_s"])
        dynamic_pressure = 0.5 * rho_bulk * bulk_velocity * bulk_velocity
        wall_shear_abs = numeric_or_nan(row.get("mean_wall_shear_streamwise_abs_pa"))
        fanning_cf = (
            float(wall_shear_abs / max(dynamic_pressure, defs.EPS))
            if math.isfinite(wall_shear_abs)
            and math.isfinite(dynamic_pressure)
            and dynamic_pressure > defs.EPS
            else math.nan
        )
        loop_s_mid_m = float(offsets.get(str(row["span_name"]), 0.0) + float(major_row["s_mid_m"]))
        total_wall_heat_w = numeric_or_nan(row.get("total_wall_heat_w"))
        merged_rows.append(
            {
                **row,
                "loop_s_mid_m": loop_s_mid_m,
                "loop_s_fraction": float(loop_s_mid_m / max(total_length, defs.EPS)),
                "streamwise_bin_length_m": float(ds_m),
                "rho_bulk_kg_m3": float(rho_bulk),
                "bulk_velocity_m_s": float(bulk_velocity),
                "fanning_cf_shear": float(fanning_cf),
                "darcy_f_shear": float(4.0 * fanning_cf) if math.isfinite(fanning_cf) else math.nan,
                "wall_heat_per_length_w_m": (
                    float(total_wall_heat_w / ds_m) if math.isfinite(total_wall_heat_w) else math.nan
                ),
                "wall_heat_abs_per_length_w_m": (
                    float(abs(total_wall_heat_w) / ds_m) if math.isfinite(total_wall_heat_w) else math.nan
                ),
                "merge_status": "matched",
            }
        )
    return merged_rows, float(total_length)


def aggregate_azimuthal_transport_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("merge_status", "")) != "matched":
            continue
        grouped[
            (
                str(row["span_name"]),
                int(row["streamwise_bin_index"]),
                int(row["theta_bin_index"]),
                str(row["thermal_role"]),
                str(row["thermal_role_group"]),
            )
        ].append(row)

    mean_rows: list[dict[str, Any]] = []
    for key, payload in sorted(grouped.items()):
        span_name, streamwise_bin_index, theta_bin_index, thermal_role, thermal_role_group = key
        first = payload[0]
        mean_rows.append(
            {
                "source_id": str(first["source_id"]),
                "span_name": span_name,
                "streamwise_bin_index": int(streamwise_bin_index),
                "theta_bin_index": int(theta_bin_index),
                "thermal_role": thermal_role,
                "thermal_role_group": thermal_role_group,
                "time_sample_count": len(payload),
                "loop_s_mid_m": defs.safe_nanmean([float(row["loop_s_mid_m"]) for row in payload]),
                "loop_s_fraction": defs.safe_nanmean([float(row["loop_s_fraction"]) for row in payload]),
                "streamwise_bin_length_m": defs.safe_nanmean([float(row["streamwise_bin_length_m"]) for row in payload]),
                "streamwise_bin_center_local_m": defs.safe_nanmean(
                    [numeric_or_nan(row.get("streamwise_bin_center_local_m")) for row in payload]
                ),
                "streamwise_bin_center_global_m": defs.safe_nanmean(
                    [numeric_or_nan(row.get("streamwise_bin_center_global_m")) for row in payload]
                ),
                "theta_bin_center_deg": defs.safe_nanmean(
                    [numeric_or_nan(row.get("theta_bin_center_deg")) for row in payload]
                ),
                "mean_area_m2": defs.safe_nanmean([numeric_or_nan(row.get("area_m2")) for row in payload]),
                "mean_face_count": defs.safe_nanmean([float(row["face_count"]) for row in payload]),
                "mean_radial_distance_m": defs.safe_nanmean(
                    [numeric_or_nan(row.get("mean_radial_distance_m")) for row in payload]
                ),
                "mean_yplus": defs.safe_nanmean([numeric_or_nan(row.get("mean_yplus")) for row in payload]),
                "mean_p_rgh_pa": defs.safe_nanmean([numeric_or_nan(row.get("mean_p_rgh_pa")) for row in payload]),
                "mean_t_wall_k": defs.safe_nanmean([numeric_or_nan(row.get("mean_t_wall_k")) for row in payload]),
                "mean_wall_shear_streamwise_abs_pa": defs.safe_nanmean(
                    [numeric_or_nan(row.get("mean_wall_shear_streamwise_abs_pa")) for row in payload]
                ),
                "mean_wall_heat_flux_w_m2": defs.safe_nanmean(
                    [numeric_or_nan(row.get("mean_wall_heat_flux_w_m2")) for row in payload]
                ),
                "mean_wall_heat_w": defs.safe_nanmean([numeric_or_nan(row.get("total_wall_heat_w")) for row in payload]),
                "mean_wall_heat_per_length_w_m": defs.safe_nanmean(
                    [numeric_or_nan(row.get("wall_heat_per_length_w_m")) for row in payload]
                ),
                "mean_wall_heat_abs_per_length_w_m": defs.safe_nanmean(
                    [numeric_or_nan(row.get("wall_heat_abs_per_length_w_m")) for row in payload]
                ),
                "mean_fanning_cf_shear": defs.safe_nanmean(
                    [numeric_or_nan(row.get("fanning_cf_shear")) for row in payload]
                ),
                "mean_darcy_f_shear": defs.safe_nanmean(
                    [numeric_or_nan(row.get("darcy_f_shear")) for row in payload]
                ),
            }
        )
    return mean_rows


def summarize_streamwise_heat_loss_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matched_rows = [row for row in rows if str(row.get("merge_status", "")) == "matched"]

    def build_time_rows(group_field: str | None = None) -> list[dict[str, Any]]:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in matched_rows:
            key: tuple[Any, ...]
            if group_field is None:
                key = (float(row["time_s"]), str(row["span_name"]), int(row["streamwise_bin_index"]))
            else:
                key = (
                    float(row["time_s"]),
                    str(row["span_name"]),
                    int(row["streamwise_bin_index"]),
                    str(row.get(group_field, "")),
                )
            grouped[key].append(row)

        time_rows: list[dict[str, Any]] = []
        for key, payload in grouped.items():
            first = payload[0]
            row = {
                "source_id": str(first["source_id"]),
                "time_s": float(first["time_s"]),
                "span_name": str(first["span_name"]),
                "streamwise_bin_index": int(first["streamwise_bin_index"]),
                "loop_s_mid_m": defs.safe_nanmean([float(item["loop_s_mid_m"]) for item in payload]),
                "loop_s_fraction": defs.safe_nanmean([float(item["loop_s_fraction"]) for item in payload]),
                "streamwise_bin_length_m": defs.safe_nanmean(
                    [float(item["streamwise_bin_length_m"]) for item in payload]
                ),
                "mean_wall_heat_w": float(
                    sum(
                        numeric_or_nan(item.get("total_wall_heat_w"))
                        for item in payload
                        if math.isfinite(numeric_or_nan(item.get("total_wall_heat_w")))
                    )
                ),
                "mean_wall_heat_abs_w": float(
                    sum(
                        abs(numeric_or_nan(item.get("total_wall_heat_w")))
                        for item in payload
                        if math.isfinite(numeric_or_nan(item.get("total_wall_heat_w")))
                    )
                ),
            }
            ds_m = max(float(row["streamwise_bin_length_m"]), defs.EPS)
            row["mean_wall_heat_per_length_w_m"] = float(row["mean_wall_heat_w"] / ds_m)
            row["mean_wall_heat_abs_per_length_w_m"] = float(row["mean_wall_heat_abs_w"] / ds_m)
            if group_field is not None:
                row[group_field] = str(first.get(group_field, ""))
            time_rows.append(row)

        if group_field is None:
            cumulative_groups = {"total": sorted(time_rows, key=lambda item: float(item["loop_s_mid_m"]))}
        else:
            cumulative_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in time_rows:
                cumulative_groups[str(row[group_field])].append(row)
            for group_name in list(cumulative_groups):
                cumulative_groups[group_name] = sorted(
                    cumulative_groups[group_name],
                    key=lambda item: (float(item["time_s"]), float(item["loop_s_mid_m"])),
                )

        output: list[dict[str, Any]] = []
        if group_field is None:
            by_time: dict[float, list[dict[str, Any]]] = defaultdict(list)
            for row in time_rows:
                by_time[float(row["time_s"])].append(row)
            for _, payload in by_time.items():
                running_signed = 0.0
                running_abs = 0.0
                for row in sorted(payload, key=lambda item: float(item["loop_s_mid_m"])):
                    running_signed += float(row["mean_wall_heat_w"])
                    running_abs += float(row["mean_wall_heat_abs_w"])
                    output.append(
                        {
                            **row,
                            "cumulative_wall_heat_w": float(running_signed),
                            "cumulative_wall_heat_abs_w": float(running_abs),
                        }
                    )
        else:
            by_time_group: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
            for row in time_rows:
                by_time_group[(float(row["time_s"]), str(row[group_field]))].append(row)
            for _, payload in by_time_group.items():
                running_signed = 0.0
                running_abs = 0.0
                for row in sorted(payload, key=lambda item: float(item["loop_s_mid_m"])):
                    running_signed += float(row["mean_wall_heat_w"])
                    running_abs += float(row["mean_wall_heat_abs_w"])
                    output.append(
                        {
                            **row,
                            "cumulative_wall_heat_w": float(running_signed),
                            "cumulative_wall_heat_abs_w": float(running_abs),
                        }
                    )
        return output

    def aggregate_time_rows(
        rows_to_aggregate: list[dict[str, Any]],
        group_field: str | None = None,
    ) -> list[dict[str, Any]]:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows_to_aggregate:
            if group_field is None:
                key = (str(row["span_name"]), int(row["streamwise_bin_index"]))
            else:
                key = (str(row[group_field]), str(row["span_name"]), int(row["streamwise_bin_index"]))
            grouped[key].append(row)
        summary_rows: list[dict[str, Any]] = []
        for key, payload in sorted(grouped.items(), key=lambda item: defs.safe_nanmean([float(row["loop_s_mid_m"]) for row in item[1]])):
            first = payload[0]
            row = {
                "source_id": str(first["source_id"]),
                "span_name": str(first["span_name"]),
                "streamwise_bin_index": int(first["streamwise_bin_index"]),
                "time_sample_count": len(payload),
                "loop_s_mid_m": defs.safe_nanmean([float(item["loop_s_mid_m"]) for item in payload]),
                "loop_s_fraction": defs.safe_nanmean([float(item["loop_s_fraction"]) for item in payload]),
                "streamwise_bin_length_m": defs.safe_nanmean(
                    [float(item["streamwise_bin_length_m"]) for item in payload]
                ),
                "mean_wall_heat_w": defs.safe_nanmean([float(item["mean_wall_heat_w"]) for item in payload]),
                "mean_wall_heat_abs_w": defs.safe_nanmean([float(item["mean_wall_heat_abs_w"]) for item in payload]),
                "mean_wall_heat_per_length_w_m": defs.safe_nanmean(
                    [float(item["mean_wall_heat_per_length_w_m"]) for item in payload]
                ),
                "mean_wall_heat_abs_per_length_w_m": defs.safe_nanmean(
                    [float(item["mean_wall_heat_abs_per_length_w_m"]) for item in payload]
                ),
                "mean_cumulative_wall_heat_w": defs.safe_nanmean(
                    [float(item["cumulative_wall_heat_w"]) for item in payload]
                ),
                "mean_cumulative_wall_heat_abs_w": defs.safe_nanmean(
                    [float(item["cumulative_wall_heat_abs_w"]) for item in payload]
                ),
            }
            if group_field is not None:
                row[group_field] = str(first[group_field])
            summary_rows.append(row)
        return sorted(summary_rows, key=lambda row: (float(row["loop_s_mid_m"]), str(row.get(group_field, ""))))

    total_time_rows = build_time_rows()
    grouped_time_rows = build_time_rows("thermal_role_group")
    return (
        aggregate_time_rows(total_time_rows),
        aggregate_time_rows(grouped_time_rows, "thermal_role_group"),
    )


def annotate_span_landmarks(
    ax: Any,
    span_order: list[str],
    offsets: dict[str, float],
    span_lengths: dict[str, float],
) -> None:
    ymin, ymax = ax.get_ylim()
    y_text = ymax - 0.04 * (ymax - ymin)
    for index, span_name in enumerate(span_order):
        start = offsets[span_name]
        end = start + float(span_lengths.get(span_name, 0.0))
        ax.axvline(start, color="#9ca3af", linewidth=0.8, alpha=0.7)
        if index == len(span_order) - 1:
            ax.axvline(end, color="#9ca3af", linewidth=0.8, alpha=0.7)
        ax.text(
            start + 0.5 * (end - start),
            y_text,
            span_name.replace("_", " "),
            ha="center",
            va="top",
            fontsize=8,
            color="#374151",
        )


def plot_legwise_friction(
    output_dir: Path,
    cumulative_rows: list[dict[str, Any]],
    span_order: list[str],
    quarantined_spans: set[str],
) -> dict[str, str]:
    shear_profiles = mean_profile_by_span(cumulative_rows, "darcy_f_shear")
    pressure_profiles = mean_profile_by_span(cumulative_rows, "darcy_f_pressure_drop_prgh")
    fig, axes = plt.subplots(3, 2, figsize=(13, 11), sharex=False)
    axes_list = list(axes.flat)
    for axis, span_name in zip(axes_list, span_order):
        shear_profile = shear_profiles.get(span_name)
        pressure_profile = pressure_profiles.get(span_name)
        if not shear_profile and not pressure_profile:
            axis.set_visible(False)
            continue
        if shear_profile:
            axis.plot(shear_profile[0], shear_profile[1], color="#0b3954", linewidth=1.8, label="shear-based f")
        if pressure_profile:
            axis.plot(pressure_profile[0], pressure_profile[1], color="#ff7f11", linewidth=1.4, label="pressure-drop f")
        title = span_name.replace("_", " ")
        if span_name in quarantined_spans:
            title += " (quarantined)"
        axis.set_title(title)
        axis.set_xlabel("Local s [m]")
        axis.set_ylabel("Darcy f")
        axis.legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "case_major_friction_profiles_comparison", dpi=220)
    plt.close(fig)
    return paths


def plot_legwise_pressure_gradient(
    output_dir: Path,
    cumulative_rows: list[dict[str, Any]],
    span_order: list[str],
    quarantined_spans: set[str],
) -> dict[str, str]:
    estimated_profiles = mean_profile_by_span(cumulative_rows, "dp_major_gradient_estimated_pa_per_m")
    direct_profiles = mean_profile_by_span(cumulative_rows, "dp_major_gradient_direct_prgh_pa_per_m")
    fig, axes = plt.subplots(3, 2, figsize=(13, 11), sharex=False)
    axes_list = list(axes.flat)
    for axis, span_name in zip(axes_list, span_order):
        estimated_profile = estimated_profiles.get(span_name)
        direct_profile = direct_profiles.get(span_name)
        if not estimated_profile and not direct_profile:
            axis.set_visible(False)
            continue
        if estimated_profile:
            axis.plot(estimated_profile[0], estimated_profile[1], color="#7c3aed", linewidth=1.8, label="estimated from shear")
        if direct_profile:
            axis.plot(direct_profile[0], direct_profile[1], color="#059669", linewidth=1.4, label="direct from wall p_rgh")
        title = span_name.replace("_", " ")
        if span_name in quarantined_spans:
            title += " (quarantined)"
        axis.set_title(title)
        axis.set_xlabel("Local s [m]")
        axis.set_ylabel("Pressure-drop gradient [Pa/m]")
        axis.legend(loc="best", fontsize=8)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "case_major_pressure_gradient_profiles_comparison", dpi=220)
    plt.close(fig)
    return paths


def plot_loopwise_hydraulic_comparisons(
    output_dir: Path,
    cumulative_rows: list[dict[str, Any]],
    span_order: list[str],
) -> dict[str, str]:
    span_lengths = span_lengths_from_rows(cumulative_rows)
    offsets = build_loop_offsets(span_order, span_lengths)
    friction_shear = mean_profile_by_span(cumulative_rows, "darcy_f_shear")
    friction_pressure = mean_profile_by_span(cumulative_rows, "darcy_f_pressure_drop_prgh")
    gradient_estimated = mean_profile_by_span(cumulative_rows, "dp_major_gradient_estimated_pa_per_m")
    gradient_direct = mean_profile_by_span(cumulative_rows, "dp_major_gradient_direct_prgh_pa_per_m")

    fig_f, ax_f = plt.subplots(figsize=(14, 5.4))
    for span_name in span_order:
        if span_name in friction_shear:
            s_values, values = friction_shear[span_name]
            ax_f.plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#0b3954",
                linewidth=1.8,
            )
        if span_name in friction_pressure:
            s_values, values = friction_pressure[span_name]
            ax_f.plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#ff7f11",
                linewidth=1.4,
            )
    ax_f.plot([], [], color="#0b3954", linewidth=1.8, label="shear-based f")
    ax_f.plot([], [], color="#ff7f11", linewidth=1.4, label="pressure-drop f from wall p_rgh")
    ax_f.set_title("Loopwise Darcy friction comparison")
    ax_f.set_xlabel("Distance along loop [m]")
    ax_f.set_ylabel("Darcy f")
    ax_f.legend(loc="best")
    annotate_span_landmarks(ax_f, span_order, offsets, span_lengths)
    fig_f.tight_layout()
    friction_paths = save_matplotlib_figure(fig_f, output_dir, "case_loopwise_friction_comparison", dpi=220)
    plt.close(fig_f)

    fig_g, ax_g = plt.subplots(figsize=(14, 5.4))
    for span_name in span_order:
        if span_name in gradient_estimated:
            s_values, values = gradient_estimated[span_name]
            ax_g.plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#7c3aed",
                linewidth=1.8,
            )
        if span_name in gradient_direct:
            s_values, values = gradient_direct[span_name]
            ax_g.plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#059669",
                linewidth=1.4,
            )
    ax_g.plot([], [], color="#7c3aed", linewidth=1.8, label="estimated from shear")
    ax_g.plot([], [], color="#059669", linewidth=1.4, label="direct from wall p_rgh")
    ax_g.set_title("Loopwise pressure-gradient comparison")
    ax_g.set_xlabel("Distance along loop [m]")
    ax_g.set_ylabel("Pressure-drop gradient [Pa/m]")
    ax_g.legend(loc="best")
    annotate_span_landmarks(ax_g, span_order, offsets, span_lengths)
    fig_g.tight_layout()
    gradient_paths = save_matplotlib_figure(fig_g, output_dir, "case_loopwise_pressure_gradient_comparison", dpi=220)
    plt.close(fig_g)

    return {
        "friction": friction_paths,
        "pressure_gradient": gradient_paths,
    }


def plot_loopwise_thermal_profiles(
    output_dir: Path,
    cumulative_rows: list[dict[str, Any]],
    span_order: list[str],
) -> dict[str, str]:
    span_lengths = span_lengths_from_rows(cumulative_rows)
    offsets = build_loop_offsets(span_order, span_lengths)
    wall_heatflux_profiles = mean_profile_by_span(cumulative_rows, "wall_heatflux_area_avg_w_m2")
    wall_temp_profiles = mean_profile_by_span(cumulative_rows, "t_wall_area_avg_k")
    bulk_temp_profiles = mean_profile_by_span(cumulative_rows, "bulk_temp_fluid_area_avg_k")
    bulk_temp_tp_proxy_profiles = mean_profile_by_span(cumulative_rows, "bulk_temp_tp_endpoint_proxy_k")
    delta_t_profiles = mean_profile_by_span(cumulative_rows, "bulk_minus_wall_temp_k")
    delta_t_tp_proxy_profiles = mean_profile_by_span(cumulative_rows, "bulk_minus_wall_tp_endpoint_proxy_k")
    htc_profiles = mean_profile_by_span(cumulative_rows, "effective_htc_w_m2_k")
    htc_tp_proxy_profiles = mean_profile_by_span(cumulative_rows, "effective_htc_tp_endpoint_proxy_w_m2_k")
    ua_per_m_profiles = mean_profile_by_span(cumulative_rows, "effective_ua_per_m_w_m_k")
    ua_per_m_tp_proxy_profiles = mean_profile_by_span(cumulative_rows, "effective_ua_per_m_tp_endpoint_proxy_w_m_k")

    fig, axes = plt.subplots(4, 1, figsize=(14, 13), sharex=True)
    panel_specs = [
        (axes[0], wall_heatflux_profiles, "#bc3908", "Wall heat flux [W/m^2]", "Wall heat-flux profile"),
        (axes[2], delta_t_profiles, "#6d597a", "T_bulk - T_wall [K]", "Bulk-minus-wall temperature"),
        (axes[3], htc_profiles, "#0b3954", "Effective HTC [W/m^2/K]", "Effective HTC profile"),
    ]
    for axis, profile_map, color, ylabel, title in panel_specs:
        for span_name in span_order:
            if span_name not in profile_map:
                continue
            s_values, values = profile_map[span_name]
            axis.plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color=color,
                linewidth=1.8,
            )
        axis.set_ylabel(ylabel)
        axis.set_title(title)
    for span_name in span_order:
        if span_name in delta_t_tp_proxy_profiles:
            s_values, values = delta_t_tp_proxy_profiles[span_name]
            axes[2].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#9ca3af",
                linewidth=1.1,
                linestyle="--",
            )
        if span_name in htc_tp_proxy_profiles:
            s_values, values = htc_tp_proxy_profiles[span_name]
            axes[3].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#94a1b2",
                linewidth=1.1,
                linestyle="--",
            )
    for span_name in span_order:
        if span_name in wall_temp_profiles:
            s_values, values = wall_temp_profiles[span_name]
            axes[1].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#e07a5f",
                linewidth=1.8,
            )
        if span_name in bulk_temp_profiles:
            s_values, values = bulk_temp_profiles[span_name]
            axes[1].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#3d405b",
                linewidth=1.4,
            )
        if span_name in bulk_temp_tp_proxy_profiles:
            s_values, values = bulk_temp_tp_proxy_profiles[span_name]
            axes[1].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#9ca3af",
                linewidth=1.1,
                linestyle="--",
            )
    axes[1].plot([], [], color="#e07a5f", linewidth=1.8, label="wall T")
    axes[1].plot([], [], color="#3d405b", linewidth=1.4, label="bulk T from cutPlane (mass-flux-weighted)")
    axes[1].plot([], [], color="#9ca3af", linewidth=1.1, linestyle="--", label="TP-endpoint proxy")
    axes[1].set_ylabel("Temperature [K]")
    axes[1].set_title("Wall and bulk-fluid temperature profiles")
    axes[1].legend(loc="best")
    axes[2].plot([], [], color="#6d597a", linewidth=1.8, label="cutPlane bulk - wall")
    axes[2].plot([], [], color="#9ca3af", linewidth=1.1, linestyle="--", label="TP-endpoint proxy - wall")
    axes[2].legend(loc="best")
    axes[3].plot([], [], color="#0b3954", linewidth=1.8, label="effective HTC from mass-flux-weighted bulk")
    axes[3].plot([], [], color="#94a1b2", linewidth=1.1, linestyle="--", label="effective HTC from TP proxy")
    axes[3].legend(loc="best")
    axes[3].set_xlabel("Distance along loop [m]")
    for axis in axes:
        annotate_span_landmarks(axis, span_order, offsets, span_lengths)
    fig.tight_layout()
    thermal_paths = save_matplotlib_figure(fig, output_dir, "case_loopwise_thermal_profiles", dpi=220)
    plt.close(fig)

    fig_ua, ax_ua = plt.subplots(figsize=(14, 5.4))
    for span_name in span_order:
        if span_name not in ua_per_m_profiles:
            continue
        s_values, values = ua_per_m_profiles[span_name]
        ax_ua.plot(
            [offsets[span_name] + value for value in s_values],
            values,
            color="#2a9d8f",
            linewidth=1.8,
        )
        if span_name in ua_per_m_tp_proxy_profiles:
            s_values_proxy, values_proxy = ua_per_m_tp_proxy_profiles[span_name]
            ax_ua.plot(
                [offsets[span_name] + value for value in s_values_proxy],
                values_proxy,
                color="#94a1b2",
                linewidth=1.1,
                linestyle="--",
            )
    ax_ua.set_title("Loopwise effective UA per unit length")
    ax_ua.set_xlabel("Distance along loop [m]")
    ax_ua.set_ylabel("Effective UA' [W/m/K]")
    ax_ua.plot([], [], color="#2a9d8f", linewidth=1.8, label="effective UA' from mass-flux-weighted bulk")
    ax_ua.plot([], [], color="#94a1b2", linewidth=1.1, linestyle="--", label="effective UA' from TP proxy")
    ax_ua.legend(loc="best")
    annotate_span_landmarks(ax_ua, span_order, offsets, span_lengths)
    fig_ua.tight_layout()
    ua_paths = save_matplotlib_figure(fig_ua, output_dir, "case_loopwise_effective_ua_per_m", dpi=220)
    plt.close(fig_ua)

    thermal_resistance_profiles = mean_profile_by_span(cumulative_rows, "effective_thermal_resistance_k_m_w")
    thermal_resistance_tp_profiles = mean_profile_by_span(
        cumulative_rows,
        "effective_thermal_resistance_tp_endpoint_proxy_k_m_w",
    )
    fig_r, ax_r = plt.subplots(figsize=(14, 5.4))
    for span_name in span_order:
        if span_name not in thermal_resistance_profiles:
            continue
        s_values, values = thermal_resistance_profiles[span_name]
        ax_r.plot(
            [offsets[span_name] + value for value in s_values],
            values,
            color="#3d405b",
            linewidth=1.8,
        )
        if span_name in thermal_resistance_tp_profiles:
            s_values_proxy, values_proxy = thermal_resistance_tp_profiles[span_name]
            ax_r.plot(
                [offsets[span_name] + value for value in s_values_proxy],
                values_proxy,
                color="#94a1b2",
                linewidth=1.1,
                linestyle="--",
            )
    ax_r.set_title("Loopwise effective thermal resistance per unit length")
    ax_r.set_xlabel("Distance along loop [m]")
    ax_r.set_ylabel("Effective R_th' [K m / W]")
    ax_r.plot([], [], color="#3d405b", linewidth=1.8, label="1 / UA' from mass-flux-weighted bulk")
    ax_r.plot([], [], color="#94a1b2", linewidth=1.1, linestyle="--", label="1 / UA' from TP proxy")
    ax_r.legend(loc="best")
    annotate_span_landmarks(ax_r, span_order, offsets, span_lengths)
    fig_r.tight_layout()
    thermal_resistance_paths = save_matplotlib_figure(
        fig_r,
        output_dir,
        "case_loopwise_effective_thermal_resistance",
        dpi=220,
    )
    plt.close(fig_r)

    return {
        "thermal_profiles": thermal_paths,
        "effective_ua_per_m": ua_paths,
        "effective_thermal_resistance": thermal_resistance_paths,
    }


def plot_loopwise_thermal_qc(
    output_dir: Path,
    cumulative_rows: list[dict[str, Any]],
    span_order: list[str],
) -> dict[str, str]:
    span_lengths = span_lengths_from_rows(cumulative_rows)
    offsets = build_loop_offsets(span_order, span_lengths)
    area_ratio_profiles = mean_profile_by_span(
        cumulative_rows,
        "bulk_cross_section_chosen_region_area_ratio_to_reference",
    )
    positive_flux_profiles = mean_profile_by_span(
        cumulative_rows,
        "bulk_cross_section_chosen_region_positive_mass_flux_kg_s",
    )
    flagged_rows = [
        row
        for row in cumulative_rows
        if normalize_warning_flag(row.get("thermal_support_warning_flag", "")) == "yes"
    ]

    fig, axes = plt.subplots(2, 1, figsize=(14, 8.5), sharex=True)
    for span_name in span_order:
        if span_name in area_ratio_profiles:
            s_values, values = area_ratio_profiles[span_name]
            axes[0].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#7c3aed",
                linewidth=1.8,
            )
        if span_name in positive_flux_profiles:
            s_values, values = positive_flux_profiles[span_name]
            axes[1].plot(
                [offsets[span_name] + value for value in s_values],
                values,
                color="#0b3954",
                linewidth=1.8,
            )
    flagged_x = [
        offsets[str(row["span_name"])] + float(row["s_mid_m"])
        for row in flagged_rows
        if str(row["span_name"]) in offsets
    ]
    flagged_area_ratio_y = [
        float(row["bulk_cross_section_chosen_region_area_ratio_to_reference"])
        for row in flagged_rows
    ]
    flagged_flux_y = [
        float(row["bulk_cross_section_chosen_region_positive_mass_flux_kg_s"])
        for row in flagged_rows
    ]
    axes[0].scatter(flagged_x, flagged_area_ratio_y, color="#bc3908", s=14, alpha=0.85, label="flagged bins")
    axes[1].scatter(flagged_x, flagged_flux_y, color="#bc3908", s=14, alpha=0.85, label="flagged bins")
    axes[0].axhline(0.5, color="#9ca3af", linestyle="--", linewidth=1.0)
    axes[0].axhline(2.0, color="#9ca3af", linestyle="--", linewidth=1.0)
    axes[0].set_ylabel("Chosen area / ref area")
    axes[0].set_title("Loopwise thermal support QC: chosen-region area ratio")
    axes[0].legend(loc="best")
    axes[1].set_ylabel("Aligned +mass flux [kg/s]")
    axes[1].set_title("Loopwise thermal support QC: chosen-region aligned positive mass flux")
    axes[1].legend(loc="best")
    axes[1].set_xlabel("Distance along loop [m]")
    for axis in axes:
        annotate_span_landmarks(axis, span_order, offsets, span_lengths)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "case_loopwise_thermal_support_qc", dpi=220)
    plt.close(fig)
    return paths


def plot_feature_bars(output_dir: Path, feature_summary_rows: list[dict[str, Any]]) -> dict[str, str]:
    labels = [row["feature_name"].replace("_", "\n") for row in feature_summary_rows]
    total = [float(row["mean_abs_delta_p_rgh_pa"]) for row in feature_summary_rows]
    reference = [float(row["mean_reference_major_dp_pa"]) for row in feature_summary_rows]
    residual = [float(row["mean_minor_residual_dp_pa"]) for row in feature_summary_rows]
    x = np.arange(len(labels), dtype=float)
    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.bar(x - 0.22, total, width=0.22, label="|Δp_rgh| total", color="#0b3954")
    ax.bar(x, reference, width=0.22, label="Reference wall major", color="#ff7f11")
    ax.bar(x + 0.22, residual, width=0.22, label="Minor residual", color="#7a306c")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Pressure budget [Pa]")
    ax.set_title("Feature pressure budgets over retained late window")
    ax.legend()
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "case_feature_pressure_budgets", dpi=220)
    plt.close(fig)
    return paths


def plot_streamwise_heat_loss(
    output_dir: Path,
    total_rows: list[dict[str, Any]],
    grouped_rows: list[dict[str, Any]],
) -> dict[str, str]:
    total_payload = sorted(total_rows, key=lambda row: float(row["loop_s_mid_m"]))
    grouped_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in grouped_rows:
        grouped_by_role[str(row["thermal_role_group"])].append(row)
    for role_name in list(grouped_by_role):
        grouped_by_role[role_name] = sorted(grouped_by_role[role_name], key=lambda row: float(row["loop_s_mid_m"]))

    fig, axes = plt.subplots(2, 1, figsize=(14, 8.5), sharex=True)
    x_total = [float(row["loop_s_mid_m"]) for row in total_payload]
    axes[0].plot(
        x_total,
        [float(row["mean_wall_heat_per_length_w_m"]) for row in total_payload],
        color="#111827",
        linewidth=2.0,
        label="total",
    )
    axes[1].plot(
        x_total,
        [float(row["mean_cumulative_wall_heat_w"]) for row in total_payload],
        color="#111827",
        linewidth=2.0,
        label="total",
    )
    role_style = {
        "intended_transfer": ("#0b6e4f", "intended"),
        "parasitic_loss": ("#bc3908", "parasitic"),
    }
    for role_name, payload in sorted(grouped_by_role.items()):
        color, label = role_style.get(role_name, ("#6b7280", role_name))
        x = [float(row["loop_s_mid_m"]) for row in payload]
        axes[0].plot(
            x,
            [float(row["mean_wall_heat_per_length_w_m"]) for row in payload],
            color=color,
            linewidth=1.7,
            linestyle="--",
            label=label,
        )
        axes[1].plot(
            x,
            [float(row["mean_cumulative_wall_heat_w"]) for row in payload],
            color=color,
            linewidth=1.7,
            linestyle="--",
            label=label,
        )
    axes[0].axhline(0.0, color="#9ca3af", linewidth=0.9)
    axes[1].axhline(0.0, color="#9ca3af", linewidth=0.9)
    axes[0].set_ylabel("q' [W/m]")
    axes[1].set_ylabel("Cumulative Q [W]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[0].set_title("Streamwise wall heat-loss summary")
    axes[1].set_title("Cumulative wall heat-loss summary")
    axes[0].legend(loc="best")
    axes[1].legend(loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "case_streamwise_heat_loss", dpi=220)
    plt.close(fig)
    return paths


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    quarantined_spans = summary["major_loss"].get("quarantined_spans", [])
    negative_features = summary["feature_minor_loss"].get("negative_residual_feature_names", [])
    validation_final_time = safe_float(summary["heat_loss"].get("validation_reference", {}).get("final_time"))
    thermal_times = summary.get("streamwise_thermal", {}).get("available_times_s", [])
    thermal_nan_replacements = summary.get("streamwise_thermal", {}).get("thermal_nan_token_replacements_by_time", {})
    boundary_layer_available = bool(summary.get("boundary_layer", {}).get("available"))
    boundary_landmark_count = int(summary.get("boundary_layer", {}).get("landmark_count", 0))
    azimuthal_available = bool(summary.get("azimuthal_transport", {}).get("available"))
    theta_bin_count = int(summary.get("azimuthal_transport", {}).get("theta_bin_count", 0))
    lines = [
        "# Ethan Case Analysis Package",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Observed Outputs",
        "",
        f"- Source case: `{summary['source_id']}` under profile `{summary['profile_name']}`.",
        f"- Requested retained field times: `{', '.join(f'{value:g}' for value in summary['requested_times_s'])}` s.",
        f"- Major-loss times present: `{', '.join(f'{value:g}' for value in summary['major_retained_times_s'])}` s.",
        f"- Feature-budget times present: `{', '.join(f'{value:g}' for value in summary['feature_retained_times_s'])}` s.",
        (
            f"- Matched streamwise thermal times present: `{', '.join(f'{value:g}' for value in thermal_times)}` s."
            if thermal_times
            else "- Matched streamwise thermal times present: none."
        ),
        (
            f"- Boundary-layer landmark rows were reduced for `{boundary_landmark_count}` representative landmarks."
            if boundary_layer_available
            else "- Boundary-layer landmark rows are not available in this package build."
        ),
        (
            f"- Azimuthal wall transport was reduced on `{theta_bin_count}` theta bins per retained streamwise station."
            if azimuthal_available
            else "- Azimuthal wall transport rows are not available in this package build."
        ),
        f"- Heat tail ends at `{summary['heat_latest_time_s']:g}` s.",
        f"- Hydraulic raw extraction source: `{summary['raw_extraction_source_dir']}`.",
        "",
        "## Inferred Interpretation",
        "",
        "- The package uses one shared manifest so the hydraulic streams operate from one frozen late-time window rather than self-selecting different retained times.",
        "- Major losses are reported legwise with centerline bins, while corner and connector effects remain in the feature-based minor-loss budget.",
        "- The hydraulic package now carries two parallel major-loss reductions on the same repaired bins: a shear-based estimate and a direct wall-pressure-drop view from area-averaged `p_rgh`.",
        "- The streamwise thermal extension now reports wall temperature, matched cross-sectional fluid temperature from OpenFOAM cut planes using connected-region, mass-flux-weighted support selection, the legacy TP-endpoint bulk estimate for comparison, wall heat flux, effective HTC, and effective `UA'` on the same repaired loop coordinate.",
        (
            "- The azimuthal transport extension now publishes theta-binned wall shear and wall heat-transfer summaries on the same repaired streamwise bins, plus streamwise total and grouped wall-heat-loss reductions."
            if azimuthal_available
            else "- Azimuthal transport is not published here, so circumferential asymmetry and grouped parasitic-loss language should remain deferred."
        ),
        (
            "- First-pass boundary-layer landmarks are sampled on wall-to-centerline lines at representative span anchors so the package can report `delta99`, momentum-thickness, and resistance-linked near-wall context without claiming a full cross-sectional closure model."
            if boundary_layer_available
            else "- Boundary-layer landmark sampling is not present here, so near-wall interpretation should stay on the effective transport proxies only."
        ),
        "- Heat accounting follows the existing wallHeatFlux section semantics so the hydraulic and thermal products can sit in one per-case report package.",
        "",
        "## Contradictions And Caveats",
        "",
        "- `profile_dp_pa` remains deferred; feature `wall_dp_pa` is still inferred from adjacent major-span gradients.",
        "- Hydraulic diameter and flow area remain geometry estimates from wall area per unit length using a circular-perimeter approximation.",
        "- The direct hydraulic comparison uses wall-area-averaged `p_rgh`, not a volume-centerline probe, so it is best interpreted as a wall-registered pressure-drop diagnostic on the repaired span coordinate.",
        (
            "- Azimuthal friction factors are normalized with the matched streamwise-bin bulk density and bulk velocity, so they should be interpreted as circumferential distribution relative to the same bulk transport state used by the streamwise major-loss package."
            if azimuthal_available
            else "- No azimuthal friction-factor reduction is present in this package build."
        ),
        "- The local thermal extension now uses OpenFOAM sampled cut-plane `T` and `U`, selects one connected support region per bin, and mass-flux-weights `T` over aligned positive flux on that chosen region. The older TP-endpoint interpolation is retained as a comparison diagnostic.",
        "- Effective HTC and `UA'` are masked whenever the chosen support region fails the current quality gates: wrong-sign/fallback support, chosen-area ratio outside `[0.5, 2.0]` relative to the monitor reference area, or `|T_bulk - T_wall| < 0.25 K`.",
        (
            f"- Reconstructed retained `T` files required local sanitization of invalid `-nan` tokens before OpenFOAM could read the field on cut planes: `{', '.join(f'{time_name}: {count}' for time_name, count in thermal_nan_replacements.items())}` replacements."
            if thermal_nan_replacements
            else "- No invalid retained `T` scalar tokens required local sanitization before streamwise thermal postprocessing."
        ),
        (
            f"- Quarantined major-loss spans: `{', '.join(quarantined_spans)}` because projected wall-face distances are inconsistent with the intended centerline."
            if quarantined_spans
            else "- No major-loss spans were quarantined by the current projection-distance diagnostic."
        ),
        (
            f"- Features with negative minor residuals over the retained window: `{', '.join(negative_features)}`. Treat these as reference-budget caveats, not as settled negative-loss physics."
            if negative_features
            else "- No retained feature objects reported negative minor residuals."
        ),
        (
            f"- Heat validation metrics still depend on the older June 4 direct-validation package; the live heat tail is `{summary['heat_latest_time_s']:g}` s while the reused validation reference ends at `{validation_final_time:g}` s."
            if validation_final_time is not None
            else "- Heat validation metrics still depend on the older June 4 direct-validation package when no refreshed validation package exists."
        ),
        "",
        "## Next Actions",
        "",
        (
            "- Review the now-unquarantined major-loss spans against the raw centerline-distance and warning diagnostics before tightening any hydraulic interpretation."
            if not quarantined_spans
            else "- Repair or redefine the quarantined major-loss spans before using them in any coupled hydraulic interpretation."
        ),
        "- Split `test_section_complex` into smaller feature objects if a connector-level minor-loss narrative is needed.",
        "- Review the thermal support-QC figure and any masked gaps before using local HTC / `UA'` language in the report text.",
        (
            "- Review the grouped streamwise heat-loss table before calling any transport-region loss 'parasitic'; the current grouping distinguishes intended-transfer versus transport-wall channels only."
            if azimuthal_available
            else "- Rebuild with azimuthal transport enabled before attempting grouped parasitic heat-loss interpretation."
        ),
        (
            "- Review the boundary-layer landmark QC rows before using `delta99` or shape-factor language beyond first-pass comparative context."
            if boundary_layer_available
            else "- Add the boundary-layer landmark extractor to the next rebuild if first-pass near-wall profile metrics are needed."
        ),
        "- Add the next case profile under `tools/case_analysis_profiles.py` only after this Salt 2 package is review-clean on both provenance and interpretation.",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None, default_output_dir: Path = DEFAULT_OUTPUT_DIR) -> int:
    parser = build_parser(default_output_dir)
    args = parser.parse_args(argv)

    profile = get_case_analysis_profile(args.source_id)
    flow_direction_metadata = build_flow_direction_hint_metadata(profile)
    output_dir = ensure_dir(Path(args.output_dir))
    manifest_path = output_dir / "analysis_manifest.json"
    raw_dir = output_dir / "raw_extraction"
    raw_reuse_heat_summary: dict[str, Any] | None = None

    _, runtime_root, _ = resolve_case_paths(args.source_id)
    if args.raw_extraction_dir:
        raw_extraction_source_dir = Path(args.raw_extraction_dir).resolve()
        copy_raw_extraction_tree(raw_extraction_source_dir, raw_dir)
        manifest = build_manifest_from_raw_extraction(
            args.source_id,
            profile.profile_name,
            runtime_root,
            raw_dir,
            args.target_ds_m,
        )
        raw_source_package_dir = raw_extraction_source_dir.parent.resolve()
        if raw_source_package_dir != output_dir.resolve():
            # Reusing raw extraction from an older finished package can safely
            # copy the already-frozen heat accounting products. When rebuilding
            # from the same package root we must not require those frozen heat
            # artifacts to pre-exist, because the current run is the one that is
            # regenerating them after the raw-only compatibility fixes.
            raw_reuse_heat_summary = reuse_heat_artifacts_from_package(
                raw_extraction_source_dir,
                output_dir,
                args.source_id,
                profile.profile_name,
            )
        json_dump(manifest_path, manifest)
    else:
        selected_times = (
            [part.strip() for part in args.time_selector.split(",") if part.strip()]
            if args.time_selector
            else defs.select_stable_processor_times(
                runtime_root,
                args.last_n_times,
                required_fields=profile.analysis_required_fields,
            )
        )
        if not selected_times:
            raise RuntimeError(
                f"No stable retained processor times with required fields found under {runtime_root / 'processors64'}"
            )
        frozen_runtime_root, frozen_times, missing_times = create_frozen_runtime_snapshot(
            args.source_id,
            runtime_root,
            selected_times,
            profile.profile_name,
        )
        if not frozen_times:
            raise RuntimeError(
                f"No retained processor times could be copied into a frozen snapshot from {runtime_root / 'processors64'}"
            )
        manifest = build_analysis_manifest(
            args.source_id,
            frozen_times,
            args.target_ds_m,
            runtime_root,
            frozen_runtime_root,
            missing_times,
        )
        json_dump(manifest_path, manifest)
        run_extractor(MAJOR_EXTRACTOR_PATH, args.source_id, manifest_path, args.target_ds_m, output_dir, args.skip_extraction)
        run_extractor(
            BOUNDARY_LAYER_EXTRACTOR_PATH,
            args.source_id,
            manifest_path,
            args.target_ds_m,
            output_dir,
            args.skip_extraction,
        )
        run_extractor(
            AZIMUTHAL_EXTRACTOR_PATH,
            args.source_id,
            manifest_path,
            args.target_ds_m,
            output_dir,
            args.skip_extraction,
        )
        run_extractor(FEATURE_EXTRACTOR_PATH, args.source_id, manifest_path, args.target_ds_m, output_dir, args.skip_extraction)

    station_rows = load_station_definitions(raw_dir / "leg_centerline_station_definitions.csv")
    major_rows = load_major_rows(raw_dir / "leg_major_loss_timeseries.csv")
    feature_rows = load_feature_rows(raw_dir / "feature_minor_loss_timeseries.csv")
    boundary_layer_rows = (
        load_boundary_layer_summary_rows(raw_dir / "boundary_layer_landmark_summary.csv")
        if (raw_dir / "boundary_layer_landmark_summary.csv").exists()
        else []
    )
    azimuthal_summary_rows = (
        load_azimuthal_summary_rows(raw_dir / "azimuthal_wall_transport_summary.csv")
        if (raw_dir / "azimuthal_wall_transport_summary.csv").exists()
        else []
    )
    wall_face_rows = load_wall_face_sample_rows(raw_dir / "leg_wall_face_samples.csv")
    if not station_rows or not major_rows or not feature_rows:
        raise RuntimeError(f"Raw extraction is incomplete under {raw_dir}")

    cumulative_rows, major_summary_rows = summarize_major_rows(
        major_rows,
        profile.major_span_order,
        profile.major_spans,
    )
    integrated_feature_rows = merge_feature_budget(
        feature_rows,
        cumulative_rows,
        args.source_id,
        profile.feature_budgets,
    )
    feature_summary_rows = summarize_feature_rows(integrated_feature_rows)
    heat_summary = raw_reuse_heat_summary or build_case_heat_summary(args.source_id, output_dir, profile.heat_window_count)
    major_summary_meta = load_json(raw_dir / "leg_major_loss_extraction_summary.json")
    thermal_sanitization_summary = (
        load_json(raw_dir / "thermal_sanitization_summary.json")
        if (raw_dir / "thermal_sanitization_summary.json").exists()
        else {}
    )
    major_summary_rows, quarantined_spans = enrich_major_summary_rows(
        major_summary_rows,
        wall_face_rows,
        major_summary_meta.get("mdot_monitor_area_m2_by_span", {}),
    )
    boundary_layer_mean_rows = aggregate_boundary_layer_summary_rows(boundary_layer_rows) if boundary_layer_rows else []
    azimuthal_transport_rows, azimuthal_total_length = (
        merge_azimuthal_transport_rows(azimuthal_summary_rows, major_rows, profile.loop_span_order)
        if azimuthal_summary_rows
        else ([], math.nan)
    )
    azimuthal_transport_mean_rows = (
        aggregate_azimuthal_transport_rows(azimuthal_transport_rows) if azimuthal_transport_rows else []
    )
    streamwise_heat_loss_rows, parasitic_heat_loss_rows = (
        summarize_streamwise_heat_loss_rows(azimuthal_transport_rows) if azimuthal_transport_rows else ([], [])
    )
    negative_residual_features = sorted(
        {
            str(row["feature_name"])
            for row in feature_summary_rows
            if safe_float(row.get("mean_minor_residual_dp_pa")) is not None
            and float(row["mean_minor_residual_dp_pa"]) < -defs.EPS
        }
    )

    csv_dump(output_dir / "leg_centerline_station_definitions.csv", list(station_rows[0].keys()), station_rows)
    csv_dump(output_dir / "major_loss_summary.csv", list(major_summary_rows[0].keys()), major_summary_rows)
    csv_dump(output_dir / "thermal_streamwise_summary.csv", list(major_summary_rows[0].keys()), major_summary_rows)
    csv_dump(
        output_dir / "major_loss_cumulative_timeseries.csv",
        list(cumulative_rows[0].keys()),
        cumulative_rows,
    )
    csv_dump(
        output_dir / "feature_minor_loss_timeseries.csv",
        list(integrated_feature_rows[0].keys()),
        integrated_feature_rows,
    )
    csv_dump(
        output_dir / "feature_minor_loss_summary.csv",
        list(feature_summary_rows[0].keys()),
        feature_summary_rows,
    )
    if (raw_dir / "leg_wall_face_geometry.csv").exists():
        copy_file(
            raw_dir / "leg_wall_face_geometry.csv",
            output_dir / "leg_wall_face_geometry.csv",
        )
    if boundary_layer_rows:
        copy_file(
            raw_dir / "boundary_layer_landmark_profiles.csv",
            output_dir / "boundary_layer_landmark_profiles.csv",
        )
        csv_dump(
            output_dir / "boundary_layer_landmark_summary.csv",
            list(boundary_layer_rows[0].keys()),
            boundary_layer_rows,
        )
    if boundary_layer_mean_rows:
        csv_dump(
            output_dir / "boundary_layer_landmark_mean_summary.csv",
            list(boundary_layer_mean_rows[0].keys()),
            boundary_layer_mean_rows,
        )
    if azimuthal_summary_rows:
        copy_file(
            raw_dir / "azimuthal_wall_transport_geometry.csv",
            output_dir / "azimuthal_wall_transport_geometry.csv",
        )
        csv_dump(
            output_dir / "azimuthal_wall_transport_summary.csv",
            list(azimuthal_summary_rows[0].keys()),
            azimuthal_summary_rows,
        )
    if azimuthal_transport_mean_rows:
        csv_dump(
            output_dir / "azimuthal_transport_mean_summary.csv",
            list(azimuthal_transport_mean_rows[0].keys()),
            azimuthal_transport_mean_rows,
        )
    if streamwise_heat_loss_rows:
        csv_dump(
            output_dir / "streamwise_heat_loss_summary.csv",
            list(streamwise_heat_loss_rows[0].keys()),
            streamwise_heat_loss_rows,
        )
    if parasitic_heat_loss_rows:
        csv_dump(
            output_dir / "parasitic_heat_loss_summary.csv",
            list(parasitic_heat_loss_rows[0].keys()),
            parasitic_heat_loss_rows,
        )

    friction_paths = plot_legwise_friction(output_dir, cumulative_rows, profile.major_span_order, set(quarantined_spans))
    gradient_paths = plot_legwise_pressure_gradient(output_dir, cumulative_rows, profile.major_span_order, set(quarantined_spans))
    loopwise_paths = plot_loopwise_hydraulic_comparisons(output_dir, cumulative_rows, profile.loop_span_order)
    thermal_paths = plot_loopwise_thermal_profiles(output_dir, cumulative_rows, profile.loop_span_order)
    thermal_qc_paths = plot_loopwise_thermal_qc(output_dir, cumulative_rows, profile.loop_span_order)
    feature_paths = plot_feature_bars(output_dir, feature_summary_rows)
    streamwise_heat_loss_paths = (
        plot_streamwise_heat_loss(output_dir, streamwise_heat_loss_rows, parasitic_heat_loss_rows)
        if streamwise_heat_loss_rows
        else {}
    )

    mdot_rows, _ = patch_builder.build_mdot_series(runtime_root)
    feature_summary_meta = load_json(raw_dir / "feature_minor_loss_extraction_summary.json")
    effective_requested_times = major_summary_meta.get("requested_times", manifest["requested_times"])
    if not effective_requested_times:
        effective_requested_times = feature_summary_meta.get("requested_times", manifest["requested_times"])
    effective_requested_times = canonical_time_labels([str(value) for value in effective_requested_times])
    summary = {
        "generated_at": iso_timestamp(),
        "profile_name": profile.profile_name,
        "source_id": args.source_id,
        "requested_times_s": [float(value) for value in effective_requested_times],
        "major_retained_times_s": sorted({float(row["time_s"]) for row in major_rows}),
        "feature_retained_times_s": sorted({float(row["time_s"]) for row in integrated_feature_rows}),
        "heat_latest_time_s": float(heat_summary.get("latest_heat_time_s", math.nan)),
        "history_time_end_s": max(float(row["time_s"]) for row in mdot_rows),
        "major_loss": {
            "span_count": len(profile.major_span_order),
            "loop_span_order": profile.loop_span_order,
            "requested_times_s": major_summary_meta.get("requested_times", []),
            "available_times_s": major_summary_meta.get("available_times", []),
            "quarantined_spans": quarantined_spans,
            "summary_csv": str(output_dir / "major_loss_summary.csv"),
            "cumulative_timeseries_csv": str(output_dir / "major_loss_cumulative_timeseries.csv"),
        },
        "streamwise_thermal": {
            "summary_csv": str(output_dir / "thermal_streamwise_summary.csv"),
            "timeseries_csv": str(output_dir / "major_loss_cumulative_timeseries.csv"),
            "available_times_s": major_summary_meta.get("cross_section_temperature_available_times", []),
            "thermal_nan_token_replacements_by_time": thermal_sanitization_summary.get(
                "replacements_by_time",
                major_summary_meta.get("thermal_nan_token_replacements_by_time", {}),
            ),
            "sanitization_summary_json": str(raw_dir / "thermal_sanitization_summary.json"),
            "thermal_bulk_method": major_summary_meta.get("cross_section_temperature_method", ""),
            "thermal_support_flagged_bin_count": sum(
                1
                for row in cumulative_rows
                if normalize_warning_flag(row.get("thermal_support_warning_flag", "")) == "yes"
            ),
        },
        "boundary_layer": {
            "available": bool(boundary_layer_rows),
            "profile_csv": str(output_dir / "boundary_layer_landmark_profiles.csv"),
            "summary_csv": str(output_dir / "boundary_layer_landmark_summary.csv"),
            "mean_summary_csv": str(output_dir / "boundary_layer_landmark_mean_summary.csv"),
            "available_times_s": sorted({float(row["time_s"]) for row in boundary_layer_rows}),
            "landmark_count": len({str(row["landmark_name"]) for row in boundary_layer_rows}),
            "usable_profile_count": sum(1 for row in boundary_layer_rows if row["profile_status"] == "usable"),
            "nonusable_profile_count": sum(1 for row in boundary_layer_rows if row["profile_status"] != "usable"),
        },
        "azimuthal_transport": {
            "available": bool(azimuthal_summary_rows),
            "geometry_csv": str(output_dir / "azimuthal_wall_transport_geometry.csv"),
            "summary_csv": str(output_dir / "azimuthal_wall_transport_summary.csv"),
            "mean_summary_csv": str(output_dir / "azimuthal_transport_mean_summary.csv"),
            "streamwise_heat_loss_summary_csv": str(output_dir / "streamwise_heat_loss_summary.csv"),
            "parasitic_heat_loss_summary_csv": str(output_dir / "parasitic_heat_loss_summary.csv"),
            "available_times_s": sorted({float(row["time_s"]) for row in azimuthal_summary_rows}),
            "theta_bin_count": len({int(row["theta_bin_index"]) for row in azimuthal_summary_rows}),
            "streamwise_bin_count": len(
                {(str(row["span_name"]), int(row["streamwise_bin_index"])) for row in azimuthal_summary_rows}
            ),
            "matched_transport_row_count": sum(
                1 for row in azimuthal_transport_rows if str(row.get("merge_status", "")) == "matched"
            ),
            "total_loop_length_m": float(azimuthal_total_length) if math.isfinite(azimuthal_total_length) else math.nan,
        },
        "feature_minor_loss": {
            "feature_count": len(profile.feature_budgets),
            "requested_times_s": feature_summary_meta.get("requested_times", []),
            "available_times_s": feature_summary_meta.get("available_times", []),
            "negative_residual_feature_names": negative_residual_features,
            "summary_csv": str(output_dir / "feature_minor_loss_summary.csv"),
        },
        "heat_loss": heat_summary,
        "figure_paths": {
            "major_friction": friction_paths,
            "major_pressure_gradient": gradient_paths,
            "loopwise_hydraulics": loopwise_paths,
            "loopwise_thermal": thermal_paths,
            "loopwise_thermal_qc": thermal_qc_paths,
            "feature_budgets": feature_paths,
            "streamwise_heat_loss": streamwise_heat_loss_paths,
            "heat_loss": heat_summary.get("figure_paths", {}),
        },
        "limitations": {
            "profile_dp_pa": "not yet sampled directly; remains NaN in this first package",
            "feature_wall_dp_pa": "inferred from adjacent major-span mean gradients",
            "geometry_assumption": "local D_h and area inferred from wall area per unit length with a circular-perimeter assumption",
            "direct_pressure_gradient_method": "wall-area-averaged p_rgh reduced on the same repaired bins, then differentiated along local span arclength",
            "streamwise_bulk_temperature_method": "bulk temperature is computed from OpenFOAM cutPlane sampled T and U on repaired major-span bins, selecting one connected region by aligned positive mass-flux support and reference-area agreement, then mass-flux-weighting T over that chosen region",
            "streamwise_bulk_temperature_weighting": "HTC and UA' are only reported where chosen-region support passes the current area-ratio, aligned-flux, and minimum-|Delta T| gates",
            "boundary_layer_landmarks": "wall-to-centerline sampled-set landmarks provide first-pass local profile metrics only; they are not a full circumferential or full-span boundary-layer reconstruction",
            "azimuthal_transport": "theta-binned wall transport uses registered wall-face projection onto the repaired streamwise coordinate and local cross-plane azimuth bins; local friction factors are normalized with the matched streamwise-bin bulk rho and bulk velocity rather than a wall-local velocity scale",
            "flow_direction_sign_hint": flow_direction_metadata["meaning"],
        },
        "flow_direction_hints": flow_direction_metadata,
        "raw_extraction_provenance": manifest.get(
            "raw_extraction_provenance",
            {
                "validation_status": "live_extraction",
                "requested_source_id": args.source_id,
                "requested_profile_name": profile.profile_name,
            },
        ),
        "raw_extraction_reused": bool(args.raw_extraction_dir),
        "raw_extraction_source_dir": str(Path(args.raw_extraction_dir).resolve()) if args.raw_extraction_dir else str(raw_dir.resolve()),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
