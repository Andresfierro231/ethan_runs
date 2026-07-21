"""Tests for thermal sign/enthalpy review."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_thermal_sign_enthalpy_review import build_review


class ThermalSignEnthalpyReviewTests(unittest.TestCase):
    def write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_blocks_sign_conflict_and_large_residual(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            qois = root / "qois.csv"
            enthalpy = root / "enthalpy.csv"
            out = root / "out"
            self.write_csv(
                qois,
                [
                    {
                        "case_id": "salt_2",
                        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                        "segment": "lower_leg",
                        "quantity": "HTC",
                        "medium_q_sign": "positive_out_of_fluid_cooled",
                        "fine_q_sign": "positive_out_of_fluid_cooled",
                        "medium_wall_duty_Q_w": "237",
                        "fine_wall_duty_Q_w": "238",
                        "admission_decision": "blocked_sign_review",
                    }
                ],
            )
            self.write_csv(
                enthalpy,
                [
                    {
                        "case_id": "salt_2",
                        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                        "physical_segment": "lower_leg",
                        "delta_T_K": "15",
                        "enthalpy_change_W": "288",
                        "segment_wallHeatFlux_sum_W": "237",
                        "wallHeatFlux_vs_enthalpy_residual_W": "-51",
                        "residual_fraction": "-0.18",
                        "enthalpy_change_status": "computed_from_physical_segment_interfaces",
                        "max_interface_recirc_ratio": "0.2",
                        "quality_flags": "",
                    }
                ],
            )

            summary = build_review(qois, enthalpy, out)

            self.assertEqual(summary["fit_admissible_count"], 0)
            text = (out / "thermal_sign_enthalpy_blockers.csv").read_text(encoding="utf-8")
            self.assertIn("repaired_q_sign_label_conflict", text)
            self.assertIn("thermal_mesh_gate_not_admitted", text)

    def test_high_recirculation_blocks_upcomer(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            qois = root / "qois.csv"
            enthalpy = root / "enthalpy.csv"
            out = root / "out"
            self.write_csv(
                qois,
                [
                    {
                        "case_id": "salt_2",
                        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                        "segment": "upcomer",
                        "quantity": "Nu",
                        "medium_q_sign": "negative_into_fluid_heated",
                        "fine_q_sign": "negative_into_fluid_heated",
                        "medium_wall_duty_Q_w": "-25",
                        "fine_wall_duty_Q_w": "-25",
                        "admission_decision": "blocked_sign_review",
                    }
                ],
            )
            self.write_csv(
                enthalpy,
                [
                    {
                        "case_id": "salt_2",
                        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
                        "physical_segment": "upcomer",
                        "delta_T_K": "7",
                        "enthalpy_change_W": "136",
                        "segment_wallHeatFlux_sum_W": "-25",
                        "wallHeatFlux_vs_enthalpy_residual_W": "-162",
                        "residual_fraction": "-1.18",
                        "enthalpy_change_status": "computed_diagnostic_only_high_recirculation_interfaces",
                        "max_interface_recirc_ratio": "0.98",
                        "quality_flags": "high_recirculation_interface_temperature",
                    }
                ],
            )

            build_review(qois, enthalpy, out)

            text = (out / "thermal_sign_enthalpy_blockers.csv").read_text(encoding="utf-8")
            self.assertIn("high_recirculation_interface", text)
            self.assertIn("large_wall_enthalpy_residual", text)


if __name__ == "__main__":
    unittest.main()
