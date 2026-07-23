import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_hx_coupled_fluid_evaluation_preflight as preflight


class HxCoupledFluidEvaluationPreflightTests(unittest.TestCase):
    @staticmethod
    def rows(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_preflight_is_diagnostic_not_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with mock.patch.object(preflight, "OUT", out), mock.patch.object(preflight, "COUPLED_OUT", out / "coupled_fluid_output"):
                summary = preflight.build()
            self.assertEqual(summary["preflight_decision"], "diagnostic_coupled_compute_allowed_source_property_fail_closed")
            self.assertFalse(summary["source_property_release"])
            self.assertFalse(summary["candidate_freeze"])
            rows = self.rows(out / "source_property_preflight.csv")
            by_gate = {row["gate"]: row for row in rows}
            self.assertEqual(by_gate["candidate_specific_source_property_release"]["status"], "fail_closed")
            self.assertIn("diagnostic", by_gate["coupled_compute_permission"]["status"])

    def test_launch_contract_targets_run_specific_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            coupled = out / "coupled_fluid_output"
            with mock.patch.object(preflight, "OUT", out), mock.patch.object(preflight, "COUPLED_OUT", coupled):
                preflight.build()
            rows = self.rows(out / "launch_contract.csv")
            command = next(row for row in rows if row["launch_item"] == "scheduler_command")["value"]
            self.assertIn("--run-fluid", command)
            self.assertIn("--timeout-seconds 273", command)
            self.assertIn("--output-dir", command)
            self.assertIn("coupled_fluid_output", command)


if __name__ == "__main__":
    unittest.main()
