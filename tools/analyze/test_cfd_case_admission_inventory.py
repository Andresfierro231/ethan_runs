from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_cfd_case_admission_inventory import build_cfd_case_admission_inventory


class CFDCaseAdmissionInventoryTests(unittest.TestCase):
    def test_split_and_corrected_q_admission_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cfd-case-admission-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_cfd_case_admission_inventory(out_dir)

            self.assertEqual(summary["training_rows_now"], ["salt_2"])
            self.assertEqual(summary["validation_rows_now"], ["salt_3"])
            self.assertEqual(summary["holdout_rows_now"], ["salt_4"])
            self.assertEqual(summary["corrected_q_rows_admitted"], 0)

            rows = self._rows_by_case(out_dir / "cfd_case_admission_inventory.csv")
            self.assertEqual(len(rows), summary["case_rows"])
            self.assertEqual(rows["salt_2"]["training_eligible_now"], "yes")
            self.assertEqual(rows["salt_3"]["validation_eligible_now"], "yes")
            self.assertEqual(rows["salt_4"]["holdout_eligible_now"], "yes")
            self.assertEqual(rows["salt2_lo10q"]["evidence_use_class"], "blocked_pending_terminal_gate")
            self.assertEqual(rows["salt3_hi10q"]["case_classification"], "failed")
            self.assertEqual(rows["salt1_kirst_continuation_candidate"]["case_classification"], "historical/Kirst")

    def test_boundary_rows_preserve_radiation_semantics(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cfd-case-admission-") as tmpdir:
            out_dir = Path(tmpdir)
            build_cfd_case_admission_inventory(out_dir)

            with (out_dir / "boundary_condition_role_table.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            mainline_rc_rows = [
                row
                for row in rows
                if row["case_id"] == "salt_2" and row["role"] == "heater"
            ]
            self.assertEqual(len(mainline_rc_rows), 1)
            self.assertEqual(mainline_rc_rows[0]["emissivity_values"], "0.95")
            self.assertIn("folded into total wallHeatFlux", mainline_rc_rows[0]["radiation_semantics"])

            corrected_rows = [row for row in rows if row["case_id"] == "salt2_lo10q"]
            self.assertTrue(corrected_rows)
            self.assertTrue(all(row["admission_use"] == "not_admitted_until_terminal_gate" for row in corrected_rows))

    def test_source_manifest_paths_exist_for_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cfd-case-admission-") as tmpdir:
            out_dir = Path(tmpdir)
            build_cfd_case_admission_inventory(out_dir)

            with (out_dir / "source_manifest.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            read_only_inputs = [row for row in rows if row["read_or_generated"] == "read_only_input"]
            self.assertTrue(read_only_inputs)
            self.assertTrue(all(row["exists"] == "True" for row in read_only_inputs))

    @staticmethod
    def _rows_by_case(path: Path) -> dict[str, dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["case_id"]: row for row in csv.DictReader(handle)}


if __name__ == "__main__":
    unittest.main()
