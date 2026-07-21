from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_submitted_cfd_run_compact_lineage_table import (
    build_compact_lineage_table,
    lineage_group_for,
)


class SubmittedCFDRunCompactLineageTableTests(unittest.TestCase):
    def test_lineage_group_keeps_changed_q_separate(self) -> None:
        nominal = {"run_key": "salt1_jin_basecont", "variant": "nominal_or_continuation", "fluid_family": "salt1"}
        lo10 = {"run_key": "salt1_jin_lo10q_corrected", "variant": "lo10q", "fluid_family": "salt1"}
        hiq = {"run_key": "salt1_jin_hiq_balq", "variant": "legacy_perturbation", "fluid_family": "salt1"}
        self.assertEqual(lineage_group_for(nominal), ("salt1_jin::nominal", "nominal"))
        self.assertEqual(lineage_group_for(lo10), ("salt1_jin::lo10q::mainline", "lo10q"))
        self.assertEqual(lineage_group_for(hiq), ("salt1_jin::hiq::balq", "hiq"))

    def test_compact_table_collapses_nominal_salt1_lineage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="submitted-cfd-compact-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_compact_lineage_table(out_dir)
            self.assertLess(summary["compact_row_count"], summary["input_row_count"])

            rows = self._rows_by_group(out_dir / "submitted_cfd_run_compact_lineage_table.csv")
            salt1_nominal = rows["salt1_jin::nominal"]
            self.assertEqual(salt1_nominal["latest_run_key"], "salt1_jin_nominal_continuation_corrected")
            self.assertIn("salt1_jin", salt1_nominal["collapsed_from_run_keys"])
            self.assertIn("salt1_jin_basecont", salt1_nominal["collapsed_from_run_keys"])

            self.assertIn("salt1_jin::lo10q::mainline", rows)
            self.assertIn("salt1_jin::hi10q::mainline", rows)
            self.assertNotEqual(
                rows["salt1_jin::lo10q::mainline"]["latest_run_key"],
                rows["salt1_jin::nominal"]["latest_run_key"],
            )

    @staticmethod
    def _rows_by_group(path: Path) -> dict[str, dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["lineage_group"]: row for row in csv.DictReader(handle)}


if __name__ == "__main__":
    unittest.main()
