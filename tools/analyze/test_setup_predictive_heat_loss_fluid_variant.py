import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_setup_predictive_heat_loss_fluid_variant import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class SetupPredictiveHeatLossFluidVariantTests(unittest.TestCase):
    def test_contract_exports_required_setup_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertTrue(summary["implemented"])
            rows = {row["field"]: row for row in read_csv(out / "fluid_variant_contract.csv")}
            for field in [
                "outer_closure_mode",
                "external_boundary_h_by_parent_segment",
                "external_boundary_ambient_temperature_by_parent_segment",
                "external_boundary_surroundings_temperature_by_parent_segment",
                "external_boundary_emissivity_by_parent_segment",
                "external_boundary_coverage_multiplier_by_parent_segment",
                "external_boundary_drive_selector_by_parent_segment",
                "hx_ua_multiplier",
            ]:
                self.assertEqual(rows[field]["status"].split("_")[0], "implemented" if field != "hx_ua_multiplier" else "compatible")

    def test_dry_run_demonstrates_coverage_and_drive_effects(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["demo_id"]: row for row in read_csv(out / "dry_run_segment_loss_demonstration.csv")}

            q_bulk = float(rows["heated_bulk_drive"]["q_ambient_W"])
            q_wall = float(rows["heated_pipe_outer_wall_drive"]["q_ambient_W"])
            q_surface = float(rows["heated_outer_surface_drive"]["q_ambient_W"])
            q_junction_unit = float(rows["junction_unit_coverage"]["q_ambient_W"])
            q_junction_double = float(rows["junction_double_coverage"]["q_ambient_W"])
            q_warmer_ambient = float(rows["heated_warmer_ambient"]["q_ambient_W"])

            self.assertGreater(q_bulk, q_wall)
            self.assertGreater(q_wall, q_surface)
            self.assertAlmostEqual(q_junction_double, 2.0 * q_junction_unit)
            self.assertLess(q_warmer_ambient, q_bulk)
            self.assertEqual(rows["junction_double_coverage"]["coverage_multiplier"], "2")

    def test_summary_records_runtime_leakage_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))

            self.assertIn("no_realized_CFD_wallHeatFlux", parsed["runtime_leakage_guardrail"])
            self.assertFalse(parsed["native_cfd_outputs_mutated"])
            self.assertFalse(parsed["scheduler_mutated"])
            self.assertFalse(parsed["registry_or_admission_state_mutated"])


if __name__ == "__main__":
    unittest.main()
