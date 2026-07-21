from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_thermal_boundary_contract as builder


class ThermalBoundaryContractTests(unittest.TestCase):
    def build_temp_package(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "contract"
        args = builder.parse_args(["--output-dir", str(out)])
        summary = builder.build_package(args)
        self.assertEqual([], summary["validation_errors"])
        return out

    def read_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_contract_preserves_all_patch_roles_and_radiation_caveat(self) -> None:
        out = self.build_temp_package()
        rows = self.read_rows(out / "cfd_thermal_boundary_contract.csv")

        self.assertEqual(24, len(rows))
        self.assertEqual(
            {"ambient_wall", "cooler", "heater", "junction_other", "test_section"},
            {row["patch_group"] for row in rows},
        )
        self.assertTrue(all(row["radiation_present"] == "False" for row in rows))
        self.assertTrue(all(row["radiation_caveat"] for row in rows))
        self.assertTrue(
            all(
                row["thermal_contract_label"]
                == "cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field"
                for row in rows
            )
        )

    def test_targets_capture_large_existing_thermal_mismatch(self) -> None:
        out = self.build_temp_package()
        rows = self.read_rows(out / "case_thermal_targets.csv")

        self.assertEqual(3, len(rows))
        for row in rows:
            self.assertGreater(float(row["prior_1d_Tmean_error_K"]), 60.0)
            self.assertLess(float(row["prior_1d_loop_delta_T_error_K"]), -3.0)
            self.assertEqual("2.0", row["mean_T_abs_gate_K"])
            self.assertEqual("1.0", row["loop_delta_T_abs_gate_K"])

    def test_solver_audit_marks_frozen_hydraulics_as_required_gap(self) -> None:
        out = self.build_temp_package()
        rows = self.read_rows(out / "fluid_solver_state_audit.csv")
        by_capability = {row["capability"]: row for row in rows}

        self.assertEqual(
            "requires_solver_extension_or_wrapper",
            by_capability["frozen_mdot_or_frozen_hydraulics"]["paper_replay_status"],
        )
        self.assertEqual(
            "supported_after_normalized_contract",
            by_capability["three_d_source_profile"]["paper_replay_status"],
        )
        self.assertEqual(
            "supported_after_normalized_contract",
            by_capability["three_d_segment_losses"]["paper_replay_status"],
        )

    def test_bakeoff_is_blocked_until_thermal_gate(self) -> None:
        out = self.build_temp_package()
        rows = self.read_rows(out / "frozen_hydraulics_replay_plan.csv")

        bakeoff = [row for row in rows if row["stage_id"] == "replay_05_model_form_bakeoff"]
        self.assertEqual(1, len(bakeoff))
        self.assertEqual("yes_after_gate", bakeoff[0]["bakeoff_allowed"])
        for row in rows:
            if int(row["sequence"]) < 5:
                self.assertEqual("no", row["bakeoff_allowed"])
        self.assertIn("abs(Tmean error) <= 2 K", rows[4]["exit_gate"])
        self.assertIn("abs(loop delta T error) <= 1 K", rows[4]["exit_gate"])

    def test_span_residual_rows_keep_caveated_enthalpy_status(self) -> None:
        out = self.build_temp_package()
        rows = self.read_rows(out / "span_heat_residuals.csv")

        self.assertEqual(15, len(rows))
        statuses = {row["enthalpy_change_status"] for row in rows}
        self.assertIn("not_bracketed_by_endpoint_temperature_segment", statuses)
        self.assertIn("computed_diagnostic_only_high_recirculation", statuses)
        self.assertTrue(any("high_recirculation_endpoint_temperature" in row["quality_flags"] for row in rows))


if __name__ == "__main__":
    unittest.main()
