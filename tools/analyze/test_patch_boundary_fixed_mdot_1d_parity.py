from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import run_patch_boundary_fixed_mdot_1d_parity as parity


class PatchBoundaryFixedMdotParityTests(unittest.TestCase):
    def build_plan_only_package(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "parity"
        args = parity.parse_args(["--output-dir", str(out), "--plan-only", "--strict"])
        metadata = parity.build_package(args)
        self.assertEqual(15, metadata["parity_contract_rows"])
        self.assertEqual(24, metadata["section_heat_balance_rows"])
        self.assertEqual(15, metadata["run_plan_rows"])
        self.assertEqual(0, metadata["result_rows"])
        return out

    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_parity_contract_maps_segments_to_fluid_parents(self) -> None:
        out = self.build_plan_only_package()
        rows = self.rows(out / "parity_input_contract.csv")
        parents = {(row["one_d_segment"], row["fluid_parent_segment"]) for row in rows}

        self.assertIn(("lower_leg", "heated_incline"), parents)
        self.assertIn(("cooling_branch", "cooled_incline_hx_active"), parents)
        self.assertIn(("upcomer", "left_upper_vertical"), parents)
        self.assertIn(("downcomer", "right_vertical"), parents)
        self.assertIn(("junction", "top_horizontal_exit"), parents)

    def test_heat_sign_convention_is_preserved(self) -> None:
        out = self.build_plan_only_package()
        rows = self.rows(out / "parity_input_contract.csv")
        salt2_lower = next(row for row in rows if row["case_id"] == "salt_2" and row["one_d_segment"] == "lower_leg")
        salt2_cooler = next(row for row in rows if row["case_id"] == "salt_2" and row["one_d_segment"] == "cooling_branch")

        self.assertGreater(float(salt2_lower["realized_source_W"]), 0.0)
        self.assertEqual(0.0, float(salt2_lower["realized_loss_W"]))
        self.assertGreater(float(salt2_cooler["realized_loss_W"]), 0.0)
        self.assertEqual(0.0, float(salt2_cooler["realized_source_W"]))

    def test_radiation_policy_marks_inseparable_and_no_extra_radiation(self) -> None:
        out = self.build_plan_only_package()
        contract_rows = self.rows(out / "parity_input_contract.csv")
        decision_rows = self.rows(out / "parity_decision_table.csv")

        self.assertEqual({"inseparable"}, {row["radiation_parity_mode"] for row in contract_rows})
        no_separate = next(row for row in decision_rows if row["decision_id"] == "separable_radiation_output_available")
        self.assertEqual("no", no_separate["value"])
        self.assertIn("do_not_add_separate_radiation", no_separate["parity_instruction"])

    def test_run_plan_has_four_executable_modes_and_one_contract_gap(self) -> None:
        out = self.build_plan_only_package()
        rows = self.rows(out / "run_plan.csv")

        by_path = {}
        for row in rows:
            by_path.setdefault(row["path_id"], set()).add(row["executable_with_current_fluid_api"])

        self.assertEqual({"yes"}, by_path["B0_current_fluid_baseline"])
        self.assertEqual({"yes"}, by_path["B1_legacy_cfd_cooler_duty"])
        self.assertEqual({"yes"}, by_path["B2_realized_wallflux_roles"])
        self.assertEqual({"yes"}, by_path["B3_imposed_setup_roles"])
        self.assertEqual({"no"}, by_path["B4_external_bc_equivalent_contract"])

    def test_section_heat_balance_keeps_imposed_and_realized_terms_separate(self) -> None:
        out = self.build_plan_only_package()
        rows = self.rows(out / "section_heat_balance.csv")
        salt2_heater = next(row for row in rows if row["case_id"] == "salt_2" and row["role"] == "heater")

        self.assertAlmostEqual(243.519101, float(salt2_heater["realized_wallHeatFlux_W"]), places=5)
        self.assertAlmostEqual(265.7, float(salt2_heater["imposed_Q_W"]), places=5)


if __name__ == "__main__":
    unittest.main()
