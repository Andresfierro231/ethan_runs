#!/usr/bin/env python3
"""Tests for AGENT-308 H1 proxy runner."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import run_predictive_h1_proxy_rerun as h1


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PredictiveH1ProxyRerunTests(unittest.TestCase):
    def test_k_source_uses_only_salt2_finite_fit_targets(self) -> None:
        rows = h1.k_source_rows()
        included = [row for row in rows if row["included_in_proxy"] == "yes"]
        self.assertGreater(len(included), 0)
        self.assertTrue(all(row["case_id"] == "salt_2" for row in included))
        self.assertTrue(all(row["fit_use_status"] == "fit_target" for row in included))
        self.assertGreater(h1.proxy_k_total(rows), 0.0)

    def test_run_package_is_screen_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "h1"
            summary = h1.run_package(out_dir)
            self.assertEqual(summary["overall_status"], "h1_proxy_screen_complete_not_publication_closure")
            self.assertFalse(summary["thermal_fit_used"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertFalse(summary["publication_closure_allowed"])
            self.assertGreater(summary["n_result_rows"], 0)
            results = read_csv(out_dir / "h1_proxy_results.csv")
            self.assertTrue(all(row["h1_proxy_label"] == "screen_only_not_publication_closure" for row in results))
            self.assertTrue(all(row["thermal_fit_used"] == "false" for row in results))
            self.assertTrue((out_dir / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
