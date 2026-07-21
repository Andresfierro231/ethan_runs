from __future__ import annotations

import csv
import unittest
from pathlib import Path

from tools.analyze.build_upcomer_onset_blocker_resolution import OUT, build


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class UpcomerOnsetBlockerResolutionTests(unittest.TestCase):
    def test_builds_expected_outputs(self) -> None:
        summary = build()
        self.assertEqual(summary["task"], "AGENT-324")
        self.assertEqual(summary["blocker_decision"], "remains_open")
        for name in summary["outputs"]:
            self.assertTrue((OUT / name).exists(), name)

    def test_current_evidence_does_not_calibrate_onset(self) -> None:
        summary = build()
        self.assertEqual(summary["n_points"], 3)
        self.assertEqual(summary["recirculating_points"], 3)
        self.assertEqual(summary["non_recirculating_points"], 0)
        self.assertGreater(summary["route_A_mid_Re"], summary["re_max"])
        self.assertGreater(summary["route_B_mid_Re"], summary["re_max"])

    def test_evidence_rows_are_diagnostic_not_fit_admitted(self) -> None:
        build()
        rows = read_csv(OUT / "upcomer_onset_evidence_status.csv")
        self.assertEqual({row["regime_class"] for row in rows}, {"recirculation_cell_observed"})
        self.assertEqual({row["admission_for_closure"] for row in rows}, {"not_fit_single_stream_pipe_closure"})
        self.assertTrue(all("calibrated_regime_switch" in row["excluded_use"] for row in rows))

    def test_next_evidence_requirements_are_decision_complete(self) -> None:
        build()
        rows = read_csv(OUT / "next_evidence_requirements.csv")
        needed = {row["needed_evidence"] for row in rows}
        self.assertIn("terminal corrected Salt-Q points near onset", needed)
        self.assertIn("non-recirculating or transition anchor", needed)
        self.assertIn("mesh/time uncertainty for onset metrics", needed)
        self.assertIn("wall-core or wall-bulk Delta T extraction", needed)


if __name__ == "__main__":
    unittest.main()
