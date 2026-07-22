import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_thesis_study_s13_upcomer_exchange_production_harvest_uq as builder


class ThesisStudyS13ProductionHarvestUQTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "s13_closeout"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def read_rows(self, filename):
        with (self.out / filename).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_preserves_finite_current_coarse_qoi_context(self):
        rows = self.read_rows("exchange_qoi_availability_uq_table.csv")
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["current_coarse_case_rows"] for row in rows}, {"3"})
        self.assertEqual({row["finite_current_coarse_values"] for row in rows}, {"3"})
        self.assertEqual({row["same_qoi_temporal_uq_complete"] for row in rows}, {"True"})

    def test_medium_fine_mesh_gap_blocks_production(self):
        rows = self.read_rows("same_label_mesh_gci_blocker_table.csv")
        self.assertEqual(len(rows), 36)
        missing = [
            row for row in rows
            if row["mesh_level"] in {"medium", "fine"} and row["same_label_row_present"] == "False"
        ]
        self.assertEqual(len(missing), 24)
        self.assertEqual({row["production_use_allowed_now"] for row in rows}, {"False"})

    def test_gate_table_keeps_s11_and_harvest_closed(self):
        rows = self.read_rows("production_harvest_readiness_gate.csv")
        gates = {row["gate"]: row for row in rows}
        self.assertEqual(gates["same_label_mesh_gci"]["pass"], "False")
        self.assertEqual(gates["production_harvest"]["status"], "do_not_run")
        self.assertEqual(gates["s11_decision"]["status"], "closed")

    def test_summary_guardrails(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(summary["decision"], "fail_closed_ordinary_upcomer_disabled_no_s11_reviewable_candidate")
        self.assertEqual(summary["missing_medium_fine_same_label_rows"], 24)
        self.assertFalse(summary["production_harvest_allowed"])
        self.assertFalse(summary["s11_reviewable_candidate"])
        self.assertFalse(summary["s15_freeze_allowed"])
        self.assertFalse(summary["validation_holdout_external_scoring"])
        self.assertFalse(summary["source_property_release"])
        self.assertFalse(summary["residual_absorbed_into_internal_nu"])


if __name__ == "__main__":
    unittest.main()
