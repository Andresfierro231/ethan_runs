#!/usr/bin/env python3
"""Regression checks for thesis N4 sensor/QOI projection uncertainty table."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, "tools/analyze/build_thesis_n4_sensor_qoi_projection_uncertainty_table.py"], cwd=ROOT, check=True)
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "sensor_projection_uncertainty_table_complete_no_runtime_temperature_release"
    assert summary["sensor_rows"] == 17
    assert summary["runtime_temperature_allowed_rows"] == 0
    assert summary["runtime_temperature_input_release"] is False
    projection = rows("sensor_qoi_projection_table.csv")
    assert len(projection) == 17
    assert all(row["runtime_temperature_allowed"] == "false" for row in projection)
    assert any(row["sensor"] == "TW10" and row["acceptance_class"] == "excluded" for row in projection)
    print("thesis N4 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
