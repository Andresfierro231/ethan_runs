#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "registry" / "case_registry.csv"
DEFAULT_STATUS_PATH = ROOT / "staging" / "render_inputs" / "latest_time_reconstruction_status.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage reconstructed latest-time T fields for registered cases.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Specific registered source_id to reconstruct. Repeat to select multiple cases.",
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


def stage_case_mirror(source_root: Path, source_id: str) -> tuple[Path, Path]:
    mirror_root = ensure_dir(ROOT / "staging" / "render_inputs" / source_id / "reconstructed_case")
    for item in source_root.iterdir():
        target = mirror_root / item.name
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


def reconstruct_latest_time(source_root: Path, source_id: str) -> dict[str, object]:
    latest_time = discover_last_time(source_root)
    mirror_root, foam_path = stage_case_mirror(source_root, source_id)
    command = [
        "reconstructPar",
        "-case",
        str(mirror_root),
        "-latestTime",
        "-fields",
        "(T)",
        "-fileHandler",
        "collated",
        "-newTimes",
    ]
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
    latest_dir = mirror_root / f"{latest_time:g}"
    reconstructed_t_path = latest_dir / "T"
    status = {
        "source_id": source_id,
        "source_root": str(source_root),
        "mirror_root": str(mirror_root),
        "foam_path": str(foam_path),
        "latest_time": latest_time,
        "reconstructed_t_path": str(reconstructed_t_path),
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "status": "ready" if result.returncode == 0 and reconstructed_t_path.exists() else "failed",
    }
    return status


def main() -> int:
    args = parse_args()
    status_path = Path(args.status_path).resolve()
    selected_ids = set(args.source_ids)
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
            result = reconstruct_latest_time(source_root, row["source_id"])
        except Exception as exc:
            result = {
                "source_id": row["source_id"],
                "source_root": str(source_root),
                "status": "failed",
                "error": str(exc),
            }
        results.append(result)
        print(json.dumps(result, indent=2))

    payload = {
        "generated_at": iso_timestamp(),
        "case_count": len(results),
        "ready_count": sum(1 for item in results if item.get("status") == "ready"),
        "failed_count": sum(1 for item in results if item.get("status") == "failed"),
        "results": results,
    }
    json_dump(status_path, payload)
    return 0 if payload["failed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
