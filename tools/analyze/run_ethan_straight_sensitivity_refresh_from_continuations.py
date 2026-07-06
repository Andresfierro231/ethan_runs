#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-22_ethan_salt_straight_hydraulic_sensitivity_refresh"
DEFAULT_PACKAGE_ROOT = ROOT / "tmp" / "2026-06-22_salt_continuation_case_analysis_refresh"
REQUIRED_FILES = (
    "major_loss_cumulative_timeseries.csv",
    "leg_centerline_station_definitions.csv",
)
SOURCE_IDS = (
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Wait for the continuation-frozen Salt 2/3/4 case-analysis refresh packages "
            "to finish, then rebuild the scoped straight hydraulic sensitivity package."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--package-root", default=str(DEFAULT_PACKAGE_ROOT))
    parser.add_argument("--poll-s", type=float, default=60.0)
    parser.add_argument("--timeout-s", type=float, default=6.0 * 3600.0)
    parser.add_argument("--python", default=sys.executable)
    return parser


def package_dir(package_root: Path, source_id: str) -> Path:
    return package_root / source_id


def missing_requirements(package_root: Path) -> list[str]:
    missing: list[str] = []
    for source_id in SOURCE_IDS:
        root = package_dir(package_root, source_id)
        for name in REQUIRED_FILES:
            if not (root / name).exists():
                missing.append(f"{source_id}:{name}")
    return missing


def build_refresh_command(python_exe: str, package_root: Path, output_dir: Path) -> list[str]:
    command = [
        python_exe,
        "-m",
        "tools.analyze.build_ethan_salt_straight_hydraulic_sensitivity",
        "--output-dir",
        str(output_dir),
    ]
    for source_id in SOURCE_IDS:
        command.extend(["--source-id", source_id])
    for source_id in SOURCE_IDS:
        command.extend(
            [
                "--package-root-override",
                f"{source_id}={package_dir(package_root, source_id)}",
            ]
        )
    return command


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    deadline = time.monotonic() + max(args.timeout_s, 0.0)

    while True:
        missing = missing_requirements(package_root)
        if not missing:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError(
                "Timed out waiting for continuation refresh packages: " + ", ".join(missing)
            )
        print("waiting_for_packages", ",".join(missing), flush=True)
        time.sleep(max(args.poll_s, 1.0))

    command = build_refresh_command(args.python, package_root, output_dir)
    print("running_refresh", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    print("refresh_complete", output_dir, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
