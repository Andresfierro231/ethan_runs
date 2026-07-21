from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_submitted_cfd_run_steady_state_table import build_submitted_cfd_run_steady_state_table


class SubmittedCFDRunSteadyStateTableTests(unittest.TestCase):
    def test_core_rows_and_labels(self) -> None:
        with tempfile.TemporaryDirectory(prefix="submitted-cfd-steady-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_submitted_cfd_run_steady_state_table(out_dir, query_scheduler=False)
            self.assertGreater(summary["row_count"], 20)

            rows = self._rows_by_key(out_dir / "submitted_cfd_run_steady_state_table.csv")
            self.assertEqual(rows["salt1_jin_nominal_continuation_corrected"]["steady_or_needs_continuation"], "steady")
            self.assertEqual(rows["salt4_jin_hi10q_corrected"]["steady_or_needs_continuation"], "needs continuation")
            self.assertEqual(rows["salt4_jin_hi10q_corrected"]["steady_detection_run"], "no_current_terminal_window")
            self.assertEqual(rows["salt4_jin"]["steady_or_needs_continuation"], "steady")
            self.assertEqual(rows["salt2_jin"]["steady_or_needs_continuation"], "needs continuation")

    def test_manifest_inputs_exist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="submitted-cfd-steady-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_submitted_cfd_run_steady_state_table(out_dir, query_scheduler=False)
            for filename in summary["required_outputs"]:
                self.assertTrue((out_dir / filename).exists(), filename)
            with (out_dir / "source_manifest.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            inputs = [row for row in rows if row["role"] == "read_only_input"]
            self.assertTrue(inputs)
            self.assertTrue(all(row["exists"] == "True" for row in inputs))

    @staticmethod
    def _rows_by_key(path: Path) -> dict[str, dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["run_key"]: row for row in csv.DictReader(handle)}


if __name__ == "__main__":
    unittest.main()
