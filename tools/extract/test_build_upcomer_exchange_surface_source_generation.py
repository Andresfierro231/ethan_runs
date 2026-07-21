from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract import build_upcomer_exchange_surface_source_generation as builder


class UpcomerExchangeSurfaceSourceGenerationTests(unittest.TestCase):
    def test_parse_t_boundary_q_finds_sources_and_sinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "T"
            path.write_text(
                '''
boundaryField
{
    "heater_patch"
    {
        type rcExternalTemperature;
        Q constant 10.5;
    }
    "cooler_patch"
    {
        type rcExternalTemperature;
        Q constant -4.25;
    }
}
''',
                encoding="utf-8",
            )
            rows = builder.parse_t_boundary_q(path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["patch"], "heater_patch")
        self.assertEqual(rows[0]["q_lane"], "Q_source_W")
        self.assertEqual(rows[1]["patch"], "cooler_patch")
        self.assertEqual(rows[1]["q_lane"], "Q_sink_W")

    def test_source_sink_summary_keeps_sink_positive_magnitude(self) -> None:
        rows = [
            {"case_id": "salt_x", "case_key": "case", "time_window_s": "1", "q_w": "10", "q_lane": "Q_source_W"},
            {"case_id": "salt_x", "case_key": "case", "time_window_s": "1", "q_w": "-3", "q_lane": "Q_sink_W"},
        ]
        summary = builder.source_sink_summary_rows(rows)
        self.assertEqual(summary[0]["q_source_w"], "10")
        self.assertEqual(summary[0]["q_sink_w"], "3")
        self.assertEqual(summary[0]["q_net_w"], "7")

    def test_build_package_fails_closed_without_scheduler_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            summary = payload["summary"]
            self.assertEqual(summary["case_rows"], 3)
            self.assertFalse(summary["scheduler_action"])
            self.assertFalse(summary["openfoam_launch"])
            self.assertGreater(summary["source_sink_rows"], 0)
            self.assertTrue((out / "surface_extraction_contract.csv").exists())
            self.assertTrue((out / "source_sink_static_ledger.csv").exists())
            self.assertTrue((out / "scripts/run_surface_source_generation.sh").exists())


if __name__ == "__main__":
    unittest.main()
