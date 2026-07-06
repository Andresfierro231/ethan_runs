#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, load_csv_rows, write_json

STARTER_DIR = ROOT / "reports" / "2026-06-19_ethan_water_phase1_starter_package"
THERMAL_DIR = ROOT / "reports" / "2026-06-19_ethan_water_thermal_closure_readiness"
FEATURE_DIR = ROOT / "reports" / "2026-06-19_ethan_water_feature_hydraulic_readiness"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_water_readiness_handoff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Water readiness handoff.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dependency_rows = load_csv_rows(STARTER_DIR / "water_dependency_readiness.csv")
    thermal_rows = load_csv_rows(THERMAL_DIR / "water_thermal_closure_readiness_rows.csv")
    feature_rows = load_csv_rows(FEATURE_DIR / "water_feature_hydraulic_readiness_rows.csv")

    readiness_rollup = [
        {
            "artifact_family": "water_dependency_readiness",
            "status_counts": Counter(row["current_status"] for row in dependency_rows),
            "note": "starter dependency posture from the bounded phase-1 package",
        },
        {
            "artifact_family": "water_thermal_closure_readiness",
            "status_counts": Counter(row["readiness_status"] for row in thermal_rows),
            "note": "case-span readiness outcomes from the new thermal closure package",
        },
        {
            "artifact_family": "water_feature_hydraulic_readiness",
            "status_counts": Counter(row["readiness_status"] for row in feature_rows),
            "note": "case-feature readiness outcomes from the new hydraulic feature audit",
        },
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "water_readiness_rollup.csv", readiness_rollup)

    summary = {
        "generated_at": iso_timestamp(),
        "dependency_status_counts": Counter(row["current_status"] for row in dependency_rows),
        "thermal_status_counts": Counter(row["readiness_status"] for row in thermal_rows),
        "feature_status_counts": Counter(row["readiness_status"] for row in feature_rows),
    }
    write_json(output_dir / "summary.json", summary)

    handoff = """# Water Readiness Handoff

Generated: `2026-06-19`

## Purpose

This package rolls the Water starter dependency posture together with the new
thermal and feature readiness audits. It still does not claim defended Water
dependencies.

## Next practical order

1. thermal closure rebuild on the strongest direct Water spans
2. feature hydraulic hardening on the proxy-positive Water features
3. only then a closure-gated Water dependency package
"""
    (output_dir / "README.md").write_text(handoff, encoding="utf-8")
    (output_dir / "water_readiness_conclusions.md").write_text(handoff, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
