#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
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
    get_registry_row,
    iso_timestamp,
    safe_float,
)

OF_ENV_SCRIPT = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-02_runtime_recovery" / "scripts" / "of13-env.sh"
EXTRA_LD_LIBRARY = "/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data"
METADATA_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
TEMP_ROOT = WORKSPACE_ROOT / "tmp_extract" / "ethan_streamwise_friction"
DEFAULT_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_streamwise_friction_package" / "raw_extraction"

MAIN_LOOP_PATCHES = [
    "pipeleg_lower_01_fitting",
    "pipeleg_lower_02_straight",
    "pipeleg_lower_03_bend",
    "pipeleg_lower_04_straight",
    "pipeleg_lower_05_straight",
    "pipeleg_lower_06_straight",
    "pipeleg_lower_07_bend",
    "pipeleg_lower_08_straight",
    "pipeleg_lower_09_fitting",
    "pipeleg_right_01_lower",
    "pipeleg_right_02_middle",
    "pipeleg_right_03_upper",
    "pipeleg_left_07_lower",
    "pipeleg_left_06_connector",
    "pipeleg_left_02_connector",
    "pipeleg_left_01_upper",
    "pipeleg_upper_09_straight",
    "pipeleg_upper_08_bend",
    "pipeleg_upper_07_straight",
    "pipeleg_upper_06_reducer",
    "pipeleg_upper_05_cooler",
    "pipeleg_upper_04_reducer",
    "pipeleg_upper_03_straight",
    "pipeleg_upper_02_bend",
    "pipeleg_upper_01_straight",
]

BRANCH_PATCHES = [
    "pipeleg_left_03_fitting",
    "pipeleg_left_04_test_section",
    "pipeleg_left_05_fitting",
]

FACE_ZONES = [
    "mdot_pipeleg_lower_05_straight",
    "mdot_pipeleg_right_02_middle",
    "mdot_pipeleg_upper_05_cooler",
    "mdot_pipeleg_left_04_test_section",
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract retained latest-time patch reductions for streamwise friction "
            "reporting. The helper reconstructs only the needed root fields into "
            "a temp case and then runs surfaceFieldValue reductions on wall patches "
            "and mdot face zones."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--last-n-times", type=int, default=5)
    parser.add_argument("--time-selector", help="Explicit OpenFOAM time selector override.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Reuse any existing sampled outputs if the expected reduction files already exist.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_runtime_root(source_id: str) -> Path:
    metadata_rows = {row["source_id"]: row for row in load_csv_rows(METADATA_CSV) if row.get("source_id")}
    meta_row = metadata_rows.get(source_id, {})
    runtime_value = meta_row.get("active_runtime_root") or meta_row.get("source_root")
    if runtime_value:
        return Path(runtime_value).resolve()
    registry_row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", source_id)
    return Path(registry_row["source_root"]).resolve()


def ensure_symlink(link_path: Path, target: Path) -> None:
    if link_path.is_symlink() or link_path.exists():
        if link_path.is_symlink() and link_path.resolve() == target.resolve():
            return
        if link_path.is_dir() and not link_path.is_symlink():
            return
        link_path.unlink()
    link_path.symlink_to(target)


def ensure_extract_case(source_id: str, runtime_root: Path, extract_key: str | None = None) -> Path:
    if extract_key:
        safe_key = hashlib.sha1(extract_key.encode("utf-8")).hexdigest()[:16]
        case_dir = ensure_dir(TEMP_ROOT / source_id / safe_key)
    else:
        case_dir = ensure_dir(TEMP_ROOT / source_id)
    ensure_symlink(case_dir / "0", runtime_root / "0")
    ensure_symlink(case_dir / "constant", runtime_root / "constant")
    ensure_symlink(case_dir / "processors64", runtime_root / "processors64")
    if (runtime_root / "dynamicCode").exists():
        ensure_symlink(case_dir / "dynamicCode", runtime_root / "dynamicCode")
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


def latest_processor_times(runtime_root: Path) -> list[str]:
    processors_root = runtime_root / "processors64"
    values: list[float] = []
    for item in processors_root.iterdir():
        if not item.is_dir():
            continue
        try:
            values.append(float(item.name))
        except ValueError:
            continue
    return [f"{value:g}" for value in sorted(values)]


def select_times(runtime_root: Path, last_n_times: int, time_selector: str | None) -> list[str]:
    if time_selector:
        return [part.strip() for part in time_selector.split(",") if part.strip()]
    times = latest_processor_times(runtime_root)
    if last_n_times <= 0:
        return times
    return times[-last_n_times:]


def write_surface_functions_dict(path: Path) -> dict[str, dict[str, str]]:
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

    def add_patch_object(patch_name: str, field_name: str, operation: str) -> None:
        object_name = f"{field_name}_{operation}_{patch_name}"
        object_meta[object_name] = {
            "target_type": "patch",
            "target_name": patch_name,
            "field_name": field_name,
            "operation": operation,
        }
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
                f"    operation       {operation};",
                f"    fields          ({field_name});",
                "}",
                "",
            ]
        )

    for patch_name in MAIN_LOOP_PATCHES + BRANCH_PATCHES:
        for operation in ("areaAverage", "min", "max"):
            add_patch_object(patch_name, "wallShearStress", operation)
        for operation in ("areaAverage", "max"):
            add_patch_object(patch_name, "yPlus", operation)

    path.write_text("\n".join(lines), encoding="utf-8")
    return object_meta


def reconstructed_fields_ready(case_dir: Path, selected_times: list[str]) -> bool:
    for time_name in selected_times:
        time_dir = case_dir / time_name
        if not time_dir.exists():
            return False
        for field_name in ("wallShearStress", "yPlus"):
            if not (time_dir / field_name).exists():
                return False
    return True


def reductions_ready(case_dir: Path, object_names: list[str], selected_times: list[str]) -> bool:
    for object_name in object_names:
        for time_name in selected_times:
            if not (case_dir / "postProcessing" / object_name / time_name / "surfaceFieldValue.dat").exists():
                return False
    return True


def parse_value_token(raw_value: str) -> tuple[str, float | None, float | None, float | None, float | None]:
    value = raw_value.strip()
    if value.startswith("(") and value.endswith(")"):
        parts = [safe_float(part) for part in value[1:-1].split()]
        if len(parts) == 3 and all(part is not None for part in parts):
            return "vector", parts[0], parts[1], parts[2], None
    scalar = safe_float(value)
    if scalar is not None:
        return "scalar", None, None, None, scalar
    return "raw", None, None, None, None


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
            time_token, _, value_token = stripped.partition("\t")
            if not value_token:
                parts = stripped.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                time_token, value_token = parts
            time_value = safe_float(time_token)
            if time_value is None:
                continue
            value_kind, x_value, y_value, z_value, scalar_value = parse_value_token(value_token)
            rows.append(
                {
                    "time_s": time_value,
                    "value_kind": value_kind,
                    "x": x_value,
                    "y": y_value,
                    "z": z_value,
                    "scalar": scalar_value,
                    "raw_value": value_token.strip(),
                }
            )
    return header, rows


def collect_rows(case_dir: Path, object_meta: dict[str, dict[str, str]], selected_times: list[str], source_id: str, runtime_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    selected_time_set = {time_name for time_name in selected_times}
    for object_name, meta in sorted(object_meta.items()):
        output_root = case_dir / "postProcessing" / object_name
        if not output_root.exists():
            continue
        for time_dir in sorted(output_root.iterdir(), key=lambda item: safe_float(item.name, -1.0) or -1.0):
            if not time_dir.is_dir():
                continue
            if time_dir.name not in selected_time_set:
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
                        "target_type": meta["target_type"],
                        "target_name": meta["target_name"],
                        "field_name": meta["field_name"],
                        "operation": meta["operation"],
                        "selection": header["selection"],
                        "faces": header["faces"],
                        "area": header["area"],
                        **payload,
                    }
                )
    return rows


def json_dump(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    source_id = args.source_id
    runtime_root = load_runtime_root(source_id)
    case_dir = ensure_extract_case(source_id, runtime_root)
    output_dir = ensure_dir(Path(args.output_dir))
    selected_times = select_times(runtime_root, args.last_n_times, args.time_selector)
    if not selected_times:
        raise RuntimeError(f"No processor times found under {runtime_root / 'processors64'}")
    time_selector = ",".join(selected_times)
    functions_path = case_dir / "system" / "streamwise_friction_surface_functions"
    object_meta = write_surface_functions_dict(functions_path)
    object_names = list(object_meta)

    if not args.skip_extraction or not reconstructed_fields_ready(case_dir, selected_times):
        shell_run(
            case_dir,
            "reconstructPar "
            f"-case {shlex.quote(str(case_dir))} "
            f"-time {shlex.quote(time_selector)} "
            "-fields '(wallShearStress yPlus)'",
        )
    if not args.skip_extraction or not reductions_ready(case_dir, object_names, selected_times):
        shell_run(
            case_dir,
            "foamPostProcess "
            f"-case {shlex.quote(str(case_dir))} "
            f"-dict {shlex.quote(str(functions_path))} "
            f"-time {shlex.quote(time_selector)}",
        )

    rows = collect_rows(case_dir, object_meta, selected_times, source_id, runtime_root)
    csv_path = output_dir / "surface_reductions.csv"
    csv_dump(
        csv_path,
        [
            "source_id",
            "runtime_root",
            "extract_case_root",
            "object_name",
            "target_type",
            "target_name",
            "field_name",
            "operation",
            "selection",
            "faces",
            "area",
            "time_s",
            "value_kind",
            "x",
            "y",
            "z",
            "scalar",
            "raw_value",
        ],
        rows,
    )
    summary = {
        "generated_at": iso_timestamp(),
        "source_id": source_id,
        "runtime_root": str(runtime_root),
        "extract_case_root": str(case_dir),
        "selected_times": selected_times,
        "surface_reductions_csv": str(csv_path),
    }
    json_dump(output_dir / "surface_reductions_summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
