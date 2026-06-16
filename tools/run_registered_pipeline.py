#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, read_registry_rows  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Ethan intake workflow for one or all registered cases.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-id", help="Single registered source identifier.")
    group.add_argument("--all-registered", action="store_true", help="Run the workflow for every registered case.")
    parser.add_argument("--skip-render", action="store_true", help="Skip render preparation and render attempts.")
    parser.add_argument("--dry-run-publish", action="store_true", help="Run publish in dry-run mode.")
    return parser.parse_args()


def run_step(script: str, source_id: str, *extra: str) -> None:
    command = [sys.executable, str(WORKSPACE_ROOT / script), "--source-id", source_id, *extra]
    subprocess.run(command, cwd=str(WORKSPACE_ROOT), check=True)


def main() -> int:
    args = parse_args()
    if args.all_registered:
        source_ids = [row["source_id"] for row in read_registry_rows(WORKSPACE_ROOT / "registry" / "case_registry.csv")]
    else:
        source_ids = [args.source_id]

    for source_id in source_ids:
        run_step("tools/intake/build_import_manifest.py", source_id)
        run_step("tools/extract/extract_case_inventory.py", source_id)
        if not args.skip_render:
            run_step("tools/extract/prepare_render_input.py", source_id, "--format", "auto")
            run_step("tools/extract/render_field_figures.py", source_id, "--backend", "auto")
            run_step("tools/extract/write_render_job.py", source_id)
        run_step("tools/extract/extract_qoi_table.py", source_id)
        run_step("tools/publish/build_cross_model_join.py", source_id)
        publish_extra = ["--dry-run"] if args.dry_run_publish else []
        run_step("tools/publish/publish_cross_model_campaign.py", source_id, *publish_extra)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
