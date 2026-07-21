import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_sensor_policy_gate_opening_and_hydraulic_node_run import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class SensorPolicyGateOpeningHydraulicNodeRunTests(unittest.TestCase):
    def test_package_records_landed_node_outputs_and_blocked_admission(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["task"], "AGENT-405")
            self.assertEqual(summary["raw_two_tap_admission"], "blocked_preflight_only")
            self.assertEqual(summary["f6_gate_admission"], "blocked_not_admitted")
            self.assertEqual(
                summary["reset_k_admission"],
                "diagnostic_admitted_component_separation_only",
            )
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["local_openfoam_postprocessing_launched_by_agent405"])

    def test_admission_decisions_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["gate_item"]: row for row in read_csv(out / "hydraulic_admission_decisions.csv")}

            self.assertEqual(rows["test_section_complex_raw_two_tap"]["admission_status"], "blocked_not_admitted")
            self.assertEqual(
                rows["fluid_reset_k_diagnostic_sweep"]["admission_status"],
                "diagnostic_admitted_component_separation_only",
            )
            self.assertIn("partial", rows["pm5_matched_pressure_upcomer"]["admission_status"])

    def test_residual_attribution_stays_provisional(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            residuals = {row["residual_component"]: row for row in read_csv(out / "final_hydraulic_residual_attribution.csv")}

            self.assertEqual(summary["final_hydraulic_residual_attribution"], "provisional_not_final")
            self.assertEqual(residuals["final_hydraulic_residual"]["current_attribution"], "not_final")
            self.assertEqual(residuals["f6_re_variation_hydraulic_closure"]["current_attribution"], "blocked")


if __name__ == "__main__":
    unittest.main()
