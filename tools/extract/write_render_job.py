#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, ensure_dir, get_registry_row  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a Slurm render job for a registered case.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument("--time", default="00:30:00", help="Requested walltime.")
    parser.add_argument("--partition", default="", help="Optional Slurm partition.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    row = get_registry_row(WORKSPACE_ROOT / "registry" / "case_registry.csv", args.source_id)
    job_dir = ensure_dir(WORKSPACE_ROOT / "staging" / "render_jobs")
    job_path = job_dir / f"{args.source_id}_render.sbatch"
    lines = [
        "#!/bin/bash",
        f"#SBATCH -J render_{args.source_id}",
        f"#SBATCH -t {args.time}",
        "#SBATCH -N 1",
        "#SBATCH -n 1",
    ]
    if args.partition:
        lines.append(f"#SBATCH -p {args.partition}")
    lines.extend(
        [
            "",
            "set -euo pipefail",
            "module load gcc/11.2.0 impi/19.0.9 paraview_osmesa/5.13.3",
            "unset TACC_PARAVIEW_BIN",
            f"cd {WORKSPACE_ROOT}",
            f"{sys.executable} tools/extract/prepare_render_input.py --source-id {args.source_id} --format auto",
            f"{sys.executable} tools/extract/render_field_figures.py --source-id {args.source_id} --backend paraview",
            "",
        ]
    )
    job_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"source_id": row["source_id"], "job_path": str(job_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
