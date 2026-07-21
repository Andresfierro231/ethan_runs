import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_salt_external_test_and_q_unlock_admission import build_tables


class SaltExternalTestAndQUnlockAdmissionTest(unittest.TestCase):
    def test_build_outputs_and_required_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            counts = build_tables(out)
            self.assertEqual(counts["master"], 18)
            self.assertEqual(counts["split"], 18)
            self.assertGreaterEqual(counts["blocked"], 10)

            with (out / "salt_unlock_master_inventory.csv").open(newline="") as fh:
                master = {row["case_key"]: row for row in csv.DictReader(fh)}

            for key in [
                "salt1_nominal",
                "salt3_jin_nominal",
                "salt2_native_val",
                "salt2_lo5q",
                "salt4_hi5q",
                "salt4_hi10q",
            ]:
                self.assertIn(key, master)

            self.assertEqual(
                master["salt2_native_val"]["final_admission_decision"],
                "external_test_candidate_blocked_heat_loss_ledger",
            )
            self.assertEqual(
                master["salt4_hi10q"]["final_admission_decision"],
                "pending_terminal_harvest",
            )
            self.assertIn("diagnostic", master["salt4_hi5q"]["final_admission_decision"])

            summary = json.loads((out / "summary.json").read_text())
            self.assertFalse(summary["native_cfd_outputs_mutated"])
            self.assertEqual(summary["live_3293924_rows_blocked"], 4)


if __name__ == "__main__":
    unittest.main()
