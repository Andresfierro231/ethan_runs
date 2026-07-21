from __future__ import annotations

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_high_heat_harvest_readiness_and_live_monitor.py"
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"


class HighHeatHarvestReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3.11", str(SCRIPT), "--no-scheduler"], cwd=ROOT, check=True)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT / name).open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_indexes_all_high_heat_cases(self) -> None:
        rows = self.read_csv("high_heat_case_index.csv")
        self.assertEqual(len(rows), 4)
        powers = {row["target_heater_power_W"] for row in rows}
        self.assertEqual(powers, {"500", "1000", "1012.8", "1500"})

    def test_jobs_represented(self) -> None:
        rows = self.read_csv("live_job_status.csv")
        self.assertEqual({row["job_id"] for row in rows}, {"3299610", "3299620"})

    def test_qoi_contract_contains_required_outputs(self) -> None:
        rows = self.read_csv("required_qoi_contract.csv")
        outputs = {row["required_output"] for row in rows}
        for required in [
            "U",
            "T",
            "wallHeatFlux",
            "Re",
            "Pr",
            "Ri",
            "Gr",
            "Ra",
            "Gz",
            "wall_core_deltaT",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "steady_window_status",
            "mesh_time_uncertainty",
        ]:
            self.assertIn(required, outputs)

    def test_unknown_scheduler_does_not_mark_harvest_ready(self) -> None:
        rows = self.read_csv("harvest_readiness_queue.csv")
        self.assertTrue(rows)
        self.assertNotIn("terminal_ready_for_harvest", {row["harvest_readiness"] for row in rows})

    def test_summary_json(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["case_count"], 4)
        self.assertEqual(summary["job_count"], 2)
        self.assertEqual(summary["native_output_mutation"], "none")


if __name__ == "__main__":
    unittest.main()
