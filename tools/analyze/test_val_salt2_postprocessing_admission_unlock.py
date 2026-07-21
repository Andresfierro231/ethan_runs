import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_val_salt2_postprocessing_admission_unlock import build_package


class ValSalt2PostprocessingAdmissionUnlockTest(unittest.TestCase):
    def test_build_package_unlocks_external_test_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["case_key"], "salt2_native_val")
            self.assertEqual(summary["steady_state_label"], "steady")
            self.assertEqual(summary["admission_decision"], "external_test_validation_candidate_unlocked")
            self.assertFalse(summary["native_cfd_outputs_mutated"])

            with (out / "val_salt2_split_admission_refresh.csv").open(newline="") as fh:
                split = list(csv.DictReader(fh))
            self.assertEqual(len(split), 1)
            self.assertEqual(split[0]["split_role"], "external_test_or_validation_candidate")
            self.assertEqual(split[0]["usable_now"], "yes_external_test_validation")

            with (out / "val_salt2_section_heat_loss_ledger.csv").open(newline="") as fh:
                ledger = list(csv.DictReader(fh))
            section_keys = {row["section_key"] for row in ledger}
            for required in ["heater", "cooling_branch", "upcomer", "downcomer", "junctions"]:
                self.assertIn(required, section_keys)

            with (out / "refreshed_terminal_steady_state_gate.csv").open(newline="") as fh:
                steady_rows = list(csv.DictReader(fh))
            self.assertTrue(steady_rows)
            self.assertTrue(all(row["verdict"] == "steady" for row in steady_rows))

            with (out / "val_salt2_bc_source_material_contract.csv").open(newline="") as fh:
                bc_rows = list(csv.DictReader(fh))
            self.assertGreaterEqual(len(bc_rows), 30)

            readme = (out / "README.md").read_text()
            self.assertIn("no longer blocked by a missing section", readme)

            summary_json = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary_json["usable_now"], "yes_external_test_validation")


if __name__ == "__main__":
    unittest.main()
