#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    safe_float,
)
from tools.case_analysis_profiles import get_case_analysis_profile, resolve_case_paths  # noqa: E402
from tools.hydraulic_budget_defs import DEFAULT_SOURCE_ID, select_stable_processor_times  # noqa: E402

OF_ENV_SCRIPT = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-02_runtime_recovery" / "scripts" / "of13-env.sh"
EXTRA_LD_LIBRARY = "/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data"
TEMP_ROOT = WORKSPACE_ROOT / "tmp_extract" / "ethan_legwise_hydraulic_budget"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_legwise_hydraulic_budget_package" / "raw_extraction"
DEFERRED_NOTE = (
    "profile_dp_pa and wall_dp_pa are deferred in this first extractor; "
    "minor_residual_dp_pa and minor_k_reference therefore remain NaN."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract retained-time start/end patch pressure reductions for the Salt 2 "
            "feature-based minor-loss framework. The helper reconstructs only the "
            "needed root pressure fields into a temp case and samples area-averaged "
            "p and p_rgh on the shared FEATURE_BUDGETS patches."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--analysis-manifest", help="Path to a shared case-analysis manifest JSON.")
    parser.add_argument("--last-n-times", type=int, default=5)
    parser.add_argument("--time-selector", help="Explicit OpenFOAM time selector override.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--extract-key",
        help=(
            "Optional deterministic temp-case key override. By default the extractor derives "
            "a keyed temp workspace from the runtime root, selected times, and required fields."
        ),
    )
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Reuse any existing reconstructed fields and patch reductions if they already exist.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_manifest(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_symlink(link_path: Path, target: Path) -> None:
    if link_path.is_symlink() or link_path.exists():
        if link_path.is_symlink() and link_path.resolve() == target.resolve():
            return
        if link_path.is_dir() and not link_path.is_symlink():
            return
        link_path.unlink()
    link_path.symlink_to(target)


def processor_roots(runtime_root: Path) -> list[Path]:
    return sorted(path for path in runtime_root.iterdir() if path.is_dir() and path.name.startswith("processors"))


def ensure_extract_case(source_id: str, runtime_root: Path, extract_key: str | None = None) -> Path:
    if extract_key:
        safe_key = hashlib.sha1(extract_key.encode("utf-8")).hexdigest()[:16]
        case_dir = ensure_dir(TEMP_ROOT / source_id / safe_key)
    else:
        case_dir = ensure_dir(TEMP_ROOT / source_id)
    ensure_symlink(case_dir / "0", runtime_root / "0")
    ensure_symlink(case_dir / "constant", runtime_root / "constant")
    if (runtime_root / "dynamicCode").exists():
        ensure_symlink(case_dir / "dynamicCode", runtime_root / "dynamicCode")
    for processors_dir in processor_roots(runtime_root):
        ensure_symlink(case_dir / processors_dir.name, processors_dir)
    shutil.copytree(runtime_root / "system", case_dir / "system", dirs_exist_ok=True)
    if (runtime_root / "case_config.yaml").exists():
        shutil.copy2(runtime_root / "case_config.yaml", case_dir / "case_config.yaml")
    return case_dir


def build_extract_key(
    source_id: str,
    profile_name: str,
    runtime_root: Path,
    selected_times: list[str],
    pressure_fields: tuple[str, ...],
) -> str:
    payload = {
        "source_id": source_id,
        "profile_name": profile_name,
        "runtime_root": str(runtime_root),
        "selected_times": [canonical_time_label(value) for value in selected_times],
        "pressure_fields": list(pressure_fields),
    }
    return json.dumps(payload, sort_keys=True)


def shell_run(case_dir: Path, command: str) -> None:
    env_cmd = (
        f"source {shlex.quote(str(OF_ENV_SCRIPT))} && "
        f"export LD_LIBRARY_PATH={shlex.quote(EXTRA_LD_LIBRARY)}:${{LD_LIBRARY_PATH:-}} && "
        f"{command}"
    )
    subprocess.run(["bash", "-lc", env_cmd], cwd=str(case_dir), check=True)


def latest_processor_times(runtime_root: Path) -> list[str]:
    labels_by_value: dict[float, str] = {}
    for processors_root in processor_roots(runtime_root):
        for item in processors_root.iterdir():
            if not item.is_dir():
                continue
            value = safe_float(item.name)
            if value is None:
                continue
            labels_by_value.setdefault(value, item.name)
    return [labels_by_value[value] for value in sorted(labels_by_value)]


def select_times(runtime_root: Path, last_n_times: int, time_selector: str | None) -> list[str]:
    if time_selector:
        return [part.strip() for part in time_selector.split(",") if part.strip()]
    times = latest_processor_times(runtime_root)
    if last_n_times <= 0:
        return times
    return times[-last_n_times:]


def normalize_requested_times(requested_times: list[str], available_times: list[str]) -> tuple[list[str], list[str]]:
    available_set = {canonical_time_label(value) for value in available_times}
    usable_times: list[str] = []
    missing_times: list[str] = []
    for value in requested_times:
        label = canonical_time_label(value)
        if label in available_set:
            usable_times.append(label)
        else:
            missing_times.append(label)
    return usable_times, missing_times


def canonical_time_label(value: Any) -> str:
    numeric = safe_float(value)
    if numeric is not None:
        return f"{numeric:g}"
    return str(value).strip()


def unique_feature_patches(feature_budgets: dict[str, dict[str, Any]]) -> list[str]:
    patches = {definition["start_patch"] for definition in feature_budgets.values()}
    patches.update(definition["end_patch"] for definition in feature_budgets.values())
    return sorted(patches)


def write_surface_functions_dict(path: Path, patch_names: list[str]) -> dict[str, dict[str, str]]:
    object_meta: dict[str, dict[str, str]] = {}
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
        object_meta[object_name] = {"target_type": "patch", "target_name": patch_name}
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
    path.write_text("\n".join(lines), encoding="utf-8")
    return object_meta


def reconstructed_fields_ready(case_dir: Path, selected_times: list[str]) -> bool:
    for time_name in selected_times:
        time_dir = case_dir / canonical_time_label(time_name)
        if not time_dir.exists():
            return False
        for field_name in ("p", "p_rgh"):
            if not (time_dir / field_name).exists():
                return False
    return True


def clear_reconstructed_numeric_times(case_dir: Path) -> None:
    for time_dir in case_dir.iterdir():
        if not time_dir.is_dir() or time_dir.is_symlink():
            continue
        if safe_float(time_dir.name) is None:
            continue
        if time_dir.name == "0":
            continue
        shutil.rmtree(time_dir)


def available_reconstructed_times(case_dir: Path, selected_times: list[str]) -> list[str]:
    available: list[str] = []
    for time_name in selected_times:
        time_dir = case_dir / canonical_time_label(time_name)
        if (time_dir / "p").exists() and (time_dir / "p_rgh").exists():
            available.append(canonical_time_label(time_name))
    return available


def reductions_ready(case_dir: Path, object_names: list[str], selected_times: list[str]) -> bool:
    selected_time_set = {canonical_time_label(time_name) for time_name in selected_times}
    for object_name in object_names:
        output_root = case_dir / "postProcessing" / object_name
        if not output_root.exists():
            return False
        available = {
            canonical_time_label(time_dir.name)
            for time_dir in output_root.iterdir()
            if time_dir.is_dir() and (time_dir / "surfaceFieldValue.dat").exists()
        }
        if not selected_time_set.issubset(available):
            return False
    return True


def parse_surface_field_value(path: Path) -> tuple[dict[str, str], list[dict[str, Any]]]:
    header = {"selection": "", "faces": "", "area": ""}
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# Selection"):
                header["selection"] = stripped.split(":", 1)[1].strip()
                continue
            if stripped.startswith("# Faces"):
                header["faces"] = stripped.split(":", 1)[1].strip()
                continue
            if stripped.startswith("# Area"):
                header["area"] = stripped.split(":", 1)[1].strip()
                continue
            if stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 3:
                continue
            time_value = safe_float(parts[0])
            p_value = safe_float(parts[1])
            p_rgh_value = safe_float(parts[2])
            if time_value is None:
                continue
            rows.append(
                {
                    "time_s": time_value,
                    "areaAverage_p": p_value,
                    "areaAverage_p_rgh": p_rgh_value,
                }
            )
    return header, rows


def collect_pressure_rows(
    case_dir: Path,
    object_meta: dict[str, dict[str, str]],
    selected_times: list[str],
    source_id: str,
    runtime_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    selected_time_set = {canonical_time_label(time_name) for time_name in selected_times}
    for object_name, meta in sorted(object_meta.items()):
        output_root = case_dir / "postProcessing" / object_name
        if not output_root.exists():
            continue
        for time_dir in sorted(output_root.iterdir(), key=lambda item: safe_float(item.name, -1.0) or -1.0):
            if not time_dir.is_dir() or canonical_time_label(time_dir.name) not in selected_time_set:
                continue
            path = time_dir / "surfaceFieldValue.dat"
            if not path.exists():
                continue
            header, payload_rows = parse_surface_field_value(path)
            for payload in payload_rows:
                rows.append(
                    {
                        "source_id": source_id,
                        "runtime_root": str(runtime_root),
                        "extract_case_root": str(case_dir),
                        "object_name": object_name,
                        "patch_name": meta["target_name"],
                        "selection": header["selection"],
                        "faces": header["faces"],
                        "area": header["area"],
                        **payload,
                    }
                )
    return rows


def build_patch_time_map(pressure_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    by_patch: dict[str, dict[str, dict[str, Any]]] = {}
    for row in pressure_rows:
        patch_name = str(row["patch_name"])
        time_value = safe_float(row.get("time_s"))
        if time_value is None:
            continue
        time_label = canonical_time_label(time_value)
        by_patch.setdefault(patch_name, {})[time_label] = row
    return by_patch


def sign_token(value: float, tolerance: float = 1.0) -> int:
    if math.isnan(value) or abs(value) <= tolerance:
        return 0
    return 1 if value > 0.0 else -1


def has_sign_inconsistency(delta_p: float, delta_p_rgh: float) -> bool:
    sign_p = sign_token(delta_p)
    sign_rgh = sign_token(delta_p_rgh)
    return sign_p != 0 and sign_rgh != 0 and sign_p != sign_rgh


def build_feature_patch_pressure_rows(
    source_id: str,
    selected_times: list[str],
    pressure_rows: list[dict[str, Any]],
    feature_budgets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    patch_time_map = build_patch_time_map(pressure_rows)
    rows: list[dict[str, Any]] = []
    for feature_name, definition in feature_budgets.items():
        adjacent_major_spans = "|".join(definition.get("adjacent_major_spans", []))
        for time_name in selected_times:
            time_value = safe_float(time_name)
            if time_value is None:
                continue
            time_label = canonical_time_label(time_name)
            for patch_role, patch_key in (("start", "start_patch"), ("end", "end_patch")):
                patch_name = str(definition[patch_key])
                peer_patch_name = str(definition["end_patch"] if patch_role == "start" else definition["start_patch"])
                payload = patch_time_map.get(patch_name, {}).get(time_label)
                missing = payload is None
                rows.append(
                    {
                        "source_id": source_id,
                        "time_s": time_value,
                        "feature_name": feature_name,
                        "feature_kind": definition["kind"],
                        "patch_role": patch_role,
                        "patch_name": patch_name,
                        "paired_patch": peer_patch_name,
                        "adjacent_major_spans": adjacent_major_spans,
                        "selection": "" if payload is None else payload.get("selection", ""),
                        "faces": "" if payload is None else payload.get("faces", ""),
                        "area": "" if payload is None else payload.get("area", ""),
                        "p_pa": math.nan if payload is None else safe_float(payload.get("areaAverage_p"), math.nan),
                        "p_rgh_pa": math.nan if payload is None else safe_float(payload.get("areaAverage_p_rgh"), math.nan),
                        "missing_flag": int(missing),
                        "warning_flag": int(missing),
                        "note": "" if not missing else "Missing selected retained-time patch pressure reduction.",
                    }
                )
    return rows


def build_feature_minor_loss_rows(
    source_id: str,
    selected_times: list[str],
    pressure_rows: list[dict[str, Any]],
    feature_budgets: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    patch_time_map = build_patch_time_map(pressure_rows)
    rows: list[dict[str, Any]] = []
    missing_events: list[dict[str, Any]] = []
    for feature_name, definition in feature_budgets.items():
        start_patch = str(definition["start_patch"])
        end_patch = str(definition["end_patch"])
        for time_name in selected_times:
            time_value = safe_float(time_name)
            if time_value is None:
                continue
            time_label = canonical_time_label(time_name)
            start_row = patch_time_map.get(start_patch, {}).get(time_label)
            end_row = patch_time_map.get(end_patch, {}).get(time_label)
            note_parts = [
                "delta columns use end minus start in the FEATURE_BUDGETS geometric patch order.",
                DEFERRED_NOTE,
            ]
            warning = False
            if start_row is None or end_row is None:
                warning = True
                missing_events.append(
                    {
                        "feature_name": feature_name,
                        "time_s": time_value,
                        "missing_start_patch": int(start_row is None),
                        "missing_end_patch": int(end_row is None),
                    }
                )
                if start_row is None and end_row is None:
                    note_parts.append("Missing both start and end patch reductions for this retained time.")
                elif start_row is None:
                    note_parts.append("Missing start patch reduction for this retained time.")
                else:
                    note_parts.append("Missing end patch reduction for this retained time.")
                start_p = math.nan
                end_p = math.nan
                start_p_rgh = math.nan
                end_p_rgh = math.nan
                delta_p = math.nan
                delta_p_rgh = math.nan
                abs_delta_p_rgh = math.nan
            else:
                start_p = safe_float(start_row.get("areaAverage_p"), math.nan)
                end_p = safe_float(end_row.get("areaAverage_p"), math.nan)
                start_p_rgh = safe_float(start_row.get("areaAverage_p_rgh"), math.nan)
                end_p_rgh = safe_float(end_row.get("areaAverage_p_rgh"), math.nan)
                delta_p = end_p - start_p
                delta_p_rgh = end_p_rgh - start_p_rgh
                abs_delta_p_rgh = abs(delta_p_rgh)
                if has_sign_inconsistency(delta_p, delta_p_rgh):
                    warning = True
                    note_parts.append("delta_p_pa and delta_p_rgh_pa have inconsistent nonzero signs.")
            rows.append(
                {
                    "source_id": source_id,
                    "time_s": time_value,
                    "feature_name": feature_name,
                    "feature_kind": definition["kind"],
                    "start_patch": start_patch,
                    "end_patch": end_patch,
                    "start_p_pa": start_p,
                    "end_p_pa": end_p,
                    "delta_p_pa": delta_p,
                    "start_p_rgh_pa": start_p_rgh,
                    "end_p_rgh_pa": end_p_rgh,
                    "delta_p_rgh_pa": delta_p_rgh,
                    "abs_delta_p_rgh_pa": abs_delta_p_rgh,
                    "profile_dp_pa": math.nan,
                    "wall_dp_pa": math.nan,
                    "minor_residual_dp_pa": math.nan,
                    "minor_k_reference": math.nan,
                    "warning_flag": int(warning),
                    "note": " ".join(note_parts),
                }
            )
    return rows, missing_events


def summarize_warnings(feature_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in feature_rows:
        if int(row.get("warning_flag", 0)):
            feature_name = str(row["feature_name"])
            counts[feature_name] = counts.get(feature_name, 0) + 1
    return counts


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.analysis_manifest)
    source_id = str(manifest.get("source_id", args.source_id))
    profile = get_case_analysis_profile(source_id)
    frozen_runtime = manifest.get("frozen_runtime_root")
    if frozen_runtime:
        runtime_root = Path(str(frozen_runtime)).resolve()
    else:
        _, runtime_root, _ = resolve_case_paths(source_id)
    output_dir = ensure_dir(Path(args.output_dir))
    manifest_times = [str(value) for value in manifest.get("requested_times", [])]
    if manifest_times:
        runtime_available_times = latest_processor_times(runtime_root)
        selected_times, missing_manifest_times = normalize_requested_times(manifest_times, runtime_available_times)
        if not selected_times:
            raise RuntimeError(
                "No manifest-requested retained pressure-field times were present under "
                f"{runtime_root / 'processors64'}. Requested: {', '.join(manifest_times)}. "
                f"Available: {', '.join(runtime_available_times) if runtime_available_times else 'none'}. "
                "The frozen runtime snapshot referenced by the manifest appears to have drifted from the "
                "requested retained window."
            )
    elif args.time_selector:
        selected_times = select_times(runtime_root, args.last_n_times, args.time_selector)
    else:
        selected_times = select_stable_processor_times(runtime_root, args.last_n_times, required_fields=profile.pressure_fields)
    if not selected_times:
        raise RuntimeError(f"No stable retained processor times with pressure fields found under {runtime_root / 'processors64'}")
    extract_key = args.extract_key or build_extract_key(
        source_id,
        profile.profile_name,
        runtime_root,
        selected_times,
        profile.pressure_fields,
    )
    case_dir = ensure_extract_case(source_id, runtime_root, extract_key)
    patch_names = unique_feature_patches(profile.feature_budgets)
    functions_path = case_dir / "system" / "feature_minor_loss_surface_functions"
    object_meta = write_surface_functions_dict(functions_path, patch_names)
    object_names = list(object_meta)

    if not args.skip_extraction or not reconstructed_fields_ready(case_dir, selected_times):
        clear_reconstructed_numeric_times(case_dir)
        for time_name in selected_times:
            try:
                shell_run(
                    case_dir,
                    "reconstructPar "
                    f"-case {shlex.quote(str(case_dir))} "
                    f"-time {shlex.quote(time_name)} "
                    "-fields '(p p_rgh)'",
                )
            except subprocess.CalledProcessError:
                continue
    usable_times = available_reconstructed_times(case_dir, selected_times)
    if not usable_times:
        raise RuntimeError(f"No reconstructed retained pressure-field times were available under {case_dir}")
    time_selector = ",".join(usable_times)
    if not args.skip_extraction or not reductions_ready(case_dir, object_names, usable_times):
        shell_run(
            case_dir,
            "foamPostProcess "
            f"-case {shlex.quote(str(case_dir))} "
            f"-dict {shlex.quote(str(functions_path))} "
            f"-time {shlex.quote(time_selector)}",
        )

    pressure_rows = collect_pressure_rows(case_dir, object_meta, usable_times, source_id, runtime_root)
    patch_rows = build_feature_patch_pressure_rows(source_id, usable_times, pressure_rows, profile.feature_budgets)
    feature_rows, missing_events = build_feature_minor_loss_rows(
        source_id,
        usable_times,
        pressure_rows,
        profile.feature_budgets,
    )

    patch_csv = output_dir / "feature_patch_pressure_timeseries.csv"
    feature_csv = output_dir / "feature_minor_loss_timeseries.csv"
    csv_dump(
        patch_csv,
        [
            "source_id",
            "time_s",
            "feature_name",
            "feature_kind",
            "patch_role",
            "patch_name",
            "paired_patch",
            "adjacent_major_spans",
            "selection",
            "faces",
            "area",
            "p_pa",
            "p_rgh_pa",
            "missing_flag",
            "warning_flag",
            "note",
        ],
        patch_rows,
    )
    csv_dump(
        feature_csv,
        [
            "source_id",
            "time_s",
            "feature_name",
            "feature_kind",
            "start_patch",
            "end_patch",
            "start_p_pa",
            "end_p_pa",
            "delta_p_pa",
            "start_p_rgh_pa",
            "end_p_rgh_pa",
            "delta_p_rgh_pa",
            "abs_delta_p_rgh_pa",
            "profile_dp_pa",
            "wall_dp_pa",
            "minor_residual_dp_pa",
            "minor_k_reference",
            "warning_flag",
            "note",
        ],
        feature_rows,
    )

    summary = {
        "generated_at": iso_timestamp(),
        "profile_name": profile.profile_name,
        "source_id": source_id,
        "runtime_root": str(runtime_root),
        "extract_case_root": str(case_dir),
        "extract_case_key": extract_key,
        "requested_times": [float(time_name) for time_name in selected_times],
        "available_times": [float(time_name) for time_name in usable_times],
        "feature_names": sorted(profile.feature_budgets),
        "feature_patch_count": len(patch_names),
        "raw_pressure_row_count": len(pressure_rows),
        "feature_patch_pressure_row_count": len(patch_rows),
        "feature_minor_loss_row_count": len(feature_rows),
        "warning_counts_by_feature": summarize_warnings(feature_rows),
        "missing_reduction_events": missing_events,
        "feature_patch_pressure_timeseries_csv": str(patch_csv),
        "feature_minor_loss_timeseries_csv": str(feature_csv),
        "assumptions": [
            "delta columns use end minus start in FEATURE_BUDGETS order.",
            DEFERRED_NOTE,
            "minor_k_reference remains NaN until a shared reference density/velocity convention is supplied by the integrator.",
        ],
    }
    json_dump(output_dir / "feature_minor_loss_extraction_summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
