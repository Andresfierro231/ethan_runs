#!/usr/bin/env python3
"""Tests for PM10 pressure component isolation."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_pm10_pressure_component_isolation as mod


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


class Pm10PressureComponentIsolationTests(unittest.TestCase):
    def test_synthetic_component_terms_make_isolation_ready_without_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            targets = root / "targets.csv"
            dev = root / "dev.csv"
            terms = root / "terms.csv"
            write_csv(
                targets,
                [
                    {
                        "case_key": case_key,
                        "target_status": "residual_target_available",
                        "pm10_pressure_partial_residual_pa": "-20.0",
                        "source_paths": "fixture",
                    }
                    for case_key in mod.PM10_CASES
                ],
            )
            write_csv(dev, [{"loop_region": "upcomer", "toggle_id": "hydraulic_reset_length", "local_evidence_rows": "2"}])
            write_csv(
                terms,
                [
                    {
                        "case_key": case_key,
                        "straight_development_term_pa": "-3.0",
                        "component_term_status": "same_window_available",
                    }
                    for case_key in mod.PM10_CASES
                ],
            )
            summary = mod.build_package(targets, dev, terms, root / "out")

            self.assertEqual(summary["component_isolation_ready_cases"], 4)
            with (root / "out/pm10_pressure_component_isolation.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["pm10_pressure_isolated_residual_pa"] for row in rows}, {"-17"})
            self.assertEqual({row["component_K_admitted"] for row in rows}, {"false"})
            self.assertEqual({row["fit_allowed_now"] for row in rows}, {"no"})

    def test_current_default_is_partial_not_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = mod.build_package(output_dir=Path(tmp) / "out")

            self.assertEqual(summary["case_count"], 4)
            self.assertEqual(summary["component_isolation_ready_cases"], 0)
            self.assertEqual(summary["component_isolation_partial_cases"], 4)


if __name__ == "__main__":
    unittest.main()
