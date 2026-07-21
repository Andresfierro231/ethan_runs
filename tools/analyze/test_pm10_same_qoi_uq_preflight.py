#!/usr/bin/env python3
"""Tests for PM10 same-QOI UQ preflight."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_pm10_same_qoi_uq_preflight as mod


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class Pm10SameQoiUqPreflightTests(unittest.TestCase):
    def test_synthetic_mesh_and_time_members_pass_gate_without_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            targets = root / "targets.csv"
            planes = root / "planes.csv"
            drift = root / "drift.csv"
            target_rows = []
            plane_rows = []
            for case_key in mod.PM10_CASES:
                for level, value in [("coarse", "-21.0"), ("medium", "-20.0"), ("fine", "-19.5")]:
                    target_rows.append(
                        {
                            "case_key": case_key,
                            "residual_metric": "pm10_pressure_partial_residual_pa",
                            "pm10_pressure_partial_residual_pa": value,
                            "mesh_level": level,
                            "source_paths": "fixture",
                        }
                    )
                for time_s in ["10", "11"]:
                    plane_rows.append({"case_key": case_key, "representative_time_s": time_s, "source_paths": "fixture"})
            write_csv(targets, target_rows)
            write_csv(planes, plane_rows)
            write_csv(drift, [{"case_key": case_key, "plateau_like": "True", "strict_log_status": "pass"} for case_key in mod.PM10_CASES])

            summary = mod.build_package(targets, planes, drift, root / "out")

            self.assertEqual(summary["same_qoi_uq_pass_cases"], 4)
            with (root / "out/pm10_uq_gate.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["same_qoi_uq_gate"] for row in rows}, {"same_qoi_uq_pass"})
            self.assertEqual({row["runtime_input_allowed_now"] for row in rows}, {"no"})

    def test_current_default_blocks_same_qoi_uq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = mod.build_package(output_dir=Path(tmp) / "out")

            self.assertEqual(summary["case_count"], 4)
            self.assertEqual(summary["same_qoi_uq_pass_cases"], 0)
            self.assertEqual(summary["same_qoi_uq_blocked_cases"], 4)


if __name__ == "__main__":
    unittest.main()
