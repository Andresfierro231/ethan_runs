from __future__ import annotations

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/analyze/build_recirculation_cfd_anchor_study_design.py"
OUT = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"


class RecirculationCfdAnchorStudyDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3.11", str(SCRIPT)], check=True, cwd=ROOT)

    def read_csv(self, name: str) -> list[dict[str, str]]:
        with (OUT / name).open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_run_matrix_counts_and_targets(self) -> None:
        rows = self.read_csv("proposed_cfd_run_matrix.csv")
        self.assertEqual(len(rows), 11)
        keys = {row["case_key"] for row in rows}
        self.assertIn("salt3_jin_q1500w_hiins_onset_anchor", keys)
        self.assertIn("salt3_jin_q0150w_loins_onset_anchor", keys)
        self.assertEqual(
            sum(row["study_group"] == "small_q_x_insulation_matrix" for row in rows),
            9,
        )

    def test_required_outputs_include_user_list(self) -> None:
        rows = self.read_csv("required_output_contract.csv")
        required = {row["required_output"] for row in rows}
        for name in [
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
            self.assertIn(name, required)

    def test_insulation_mutation_guardrail_present(self) -> None:
        rows = self.read_csv("mesh_time_uncertainty_plan.csv")
        self.assertTrue(any(row["uncertainty_axis"] == "insulation_mutation" for row in rows))
        matrix = self.read_csv("small_q_insulation_matrix.csv")
        self.assertEqual({row["insulation_mode"] for row in matrix}, {"hiins", "baseline", "loins"})

    def test_summary_json(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["proposed_rows"], 11)
        self.assertTrue(summary["no_scheduler_action"])


if __name__ == "__main__":
    unittest.main()
