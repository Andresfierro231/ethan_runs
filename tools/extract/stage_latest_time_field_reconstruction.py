#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "registry" / "case_registry.csv"
DEFAULT_STATUS_PATH = ROOT / "staging" / "render_inputs" / "latest_time_field_reconstruction_status.json"
LOCAL_MIRROR_DIRS = {"constant", "system"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage reconstructed latest-time fields for registered cases.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Specific registered source_id to reconstruct. Repeat to select multiple cases.",
    )
    parser.add_argument(
        "--field",
        action="append",
        dest="fields",
        default=[],
        help="Field to reconstruct. Repeat to select multiple fields. Defaults to T if omitted.",
    )
    parser.add_argument(
        "--all-times",
        action="store_true",
        help="Reconstruct all available numeric times instead of only the latest time.",
    )
    parser.add_argument(
        "--new-times-only",
        action="store_true",
        help="Pass `-newTimes` to reconstructPar. Leave unset to allow backfilling new fields into an existing latest-time mirror.",
    )
    parser.add_argument(
        "--status-path",
        default=str(DEFAULT_STATUS_PATH),
        help="Machine-readable run status JSON path.",
    )
    return parser.parse_args()


def iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def json_dump(path: Path, payload: object) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def read_registry_rows() -> list[dict[str, str]]:
    with REGISTRY_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def numeric_dir_values(root: Path) -> list[float]:
    values: list[float] = []
    if not root.exists():
        return values
    for item in root.iterdir():
        if not item.is_dir():
            continue
        try:
            values.append(float(item.name))
        except ValueError:
            continue
    return values


def discover_last_time(source_root: Path) -> float:
    candidates = numeric_dir_values(source_root)
    candidates.extend(numeric_dir_values(source_root / "processors64"))
    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))
    if not candidates:
        raise RuntimeError(f"No numeric timestep directories found under {source_root}.")
    return max(candidates)


def discover_case_times(source_root: Path) -> list[float]:
    candidates = numeric_dir_values(source_root)
    candidates.extend(numeric_dir_values(source_root / "processors64"))
    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))
    times = sorted(set(candidates))
    if not times:
        raise RuntimeError(f"No numeric timestep directories found under {source_root}.")
    return times


def candidate_source_roots(source_root: Path, source_id: str) -> list[Path]:
    candidates = [source_root.resolve()]
    patterns = (
        f"{source_id}_continuation",
        source_id,
    )
    for pattern in patterns:
        for candidate in sorted(ROOT.glob(f"jadyn_runs/*/*/case_stage/{pattern}")):
            resolved = candidate.resolve()
            if resolved not in candidates:
                candidates.append(resolved)
    return candidates


def resolve_reconstruction_source_root(source_root: Path, source_id: str) -> tuple[Path, list[dict[str, object]]]:
    candidate_payloads: list[dict[str, object]] = []
    best_root = source_root.resolve()
    best_time_count = -1
    best_last_time = float("-inf")
    for candidate in candidate_source_roots(source_root, source_id):
        try:
            candidate_times = discover_case_times(candidate)
            payload = {
                "source_root": str(candidate),
                "time_count": len(candidate_times),
                "first_time": candidate_times[0],
                "last_time": candidate_times[-1],
            }
            candidate_payloads.append(payload)
            if (len(candidate_times), candidate_times[-1]) > (best_time_count, best_last_time):
                best_root = candidate
                best_time_count = len(candidate_times)
                best_last_time = candidate_times[-1]
        except Exception as exc:
            candidate_payloads.append({"source_root": str(candidate), "error": str(exc)})
    return best_root, candidate_payloads


def stage_case_mirror(source_root: Path, source_id: str) -> tuple[Path, Path]:
    mirror_root = ensure_dir(ROOT / "staging" / "render_inputs" / source_id / "reconstructed_case")
    for item in source_root.iterdir():
        target = mirror_root / item.name
        if item.name in LOCAL_MIRROR_DIRS:
            if target.is_symlink():
                target.unlink()
            if not target.exists():
                shutil.copytree(item, target, symlinks=True)
            continue
        if target.is_symlink():
            if target.resolve() == item.resolve():
                continue
            target.unlink()
        elif target.exists():
            continue
        target.symlink_to(item, target_is_directory=item.is_dir())
    foam_path = mirror_root / f"{source_id}.foam"
    if not foam_path.exists():
        foam_path.write_text("\n", encoding="utf-8")
    return mirror_root, foam_path


def reconstruct_field_times(
    source_root: Path,
    source_id: str,
    fields: list[str],
    *,
    all_times: bool,
    new_times_only: bool,
) -> dict[str, object]:
    resolved_source_root, source_root_candidates = resolve_reconstruction_source_root(source_root, source_id)
    source_times = discover_case_times(resolved_source_root)
    latest_time = source_times[-1]
    mirror_root, foam_path = stage_case_mirror(resolved_source_root, source_id)
    field_expr = "(" + " ".join(fields) + ")"
    command = [
        "reconstructPar",
        "-case",
        str(mirror_root),
        "-fields",
        field_expr,
        "-fileHandler",
        "collated",
    ]
    if not all_times:
        command.insert(3, "-latestTime")
    if new_times_only:
        command.append("-newTimes")
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
    latest_dir = mirror_root / f"{latest_time:g}"
    mirrored_times = sorted(numeric_dir_values(mirror_root))
    reconstructed_paths = {field_name: str(latest_dir / field_name) for field_name in fields}
    status = {
        "source_id": source_id,
        "source_root": str(source_root),
        "resolved_source_root": str(resolved_source_root),
        "source_root_candidates": source_root_candidates,
        "mirror_root": str(mirror_root),
        "foam_path": str(foam_path),
        "source_times": source_times,
        "mirrored_times": mirrored_times,
        "latest_time": latest_time,
        "fields": fields,
        "all_times": all_times,
        "new_times_only": new_times_only,
        "reconstructed_paths": reconstructed_paths,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "status": (
            "ready"
            if result.returncode == 0
            and all((latest_dir / field_name).exists() for field_name in fields)
            and (len(mirrored_times) > 1 if all_times else True)
            else "failed"
        ),
    }
    return status


def main() -> int:
    args = parse_args()
    status_path = Path(args.status_path).resolve()
    selected_ids = set(args.source_ids)
    fields = args.fields or ["T"]
    rows = [
        row
        for row in read_registry_rows()
        if row.get("status") == "registered"
        and row.get("source_id")
        and (not selected_ids or row["source_id"] in selected_ids)
    ]

    results = []
    for row in rows:
        source_root = Path(row["source_root"]).resolve()
        try:
            result = reconstruct_field_times(
                source_root,
                row["source_id"],
                fields,
                all_times=args.all_times,
                new_times_only=args.new_times_only,
            )
        except Exception as exc:
            result = {
                "source_id": row["source_id"],
                "source_root": str(source_root),
                "fields": fields,
                "all_times": args.all_times,
                "new_times_only": args.new_times_only,
                "status": "failed",
                "error": str(exc),
            }
        results.append(result)
        print(json.dumps(result, indent=2))

    payload = {
        "generated_at": iso_timestamp(),
        "fields": fields,
        "all_times": args.all_times,
        "new_times_only": args.new_times_only,
        "case_count": len(results),
        "ready_count": sum(1 for item in results if item.get("status") == "ready"),
        "failed_count": sum(1 for item in results if item.get("status") == "failed"),
        "results": results,
    }
    json_dump(status_path, payload)
    return 0 if payload["failed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
