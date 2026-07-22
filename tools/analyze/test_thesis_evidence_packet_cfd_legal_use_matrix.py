import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_thesis_evidence_packet_cfd_legal_use_matrix as builder


class ThesisEvidencePacketCfdLegalUseMatrixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tempdir.name) / "legal-use"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tempdir.cleanup()

    def rows(self, name):
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_runtime_bans_are_explicit(self):
        rows = self.rows("runtime_forbidden_input_bans.csv")
        joined = " ".join(row["forbidden_input"] for row in rows)
        for token in (
            "CFD_mdot",
            "realized_CFD_wallHeatFlux",
            "imposed_CFD_cooler_duty",
            "validation_holdout_external_temperatures",
            "protected_holdout_or_external_residuals",
        ):
            self.assertIn(token, joined)
        self.assertEqual({row["runtime_use_allowed"] for row in rows}, {"no"})

    def test_split_preserves_holdout_and_external_boundaries(self):
        rows = self.rows("case_split_legal_use_table.csv")
        by_key = {row["case_key"]: row for row in rows}
        self.assertEqual(by_key["val_salt2"]["final_fit_allowed"], "no")
        self.assertEqual(by_key["val_salt2"]["final_model_selection_allowed"], "no")
        self.assertEqual(by_key["salt2_lo5q"]["final_fit_allowed"], "no")
        self.assertEqual(by_key["salt2_hi5q"]["final_model_selection_allowed"], "no")

    def test_pm10_terminal_evidence_is_not_current_score(self):
        rows = self.rows("case_split_legal_use_table.csv")
        pm10 = [row for row in rows if row["case_key"] in {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"}]
        self.assertEqual(len(pm10), 4)
        self.assertEqual({row["blind_score_allowed_now"] for row in pm10}, {"no"})
        self.assertTrue(all("do_not_fit" in row["legal_disposition"] for row in pm10))

    def test_summary_guardrails(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertFalse(summary["validation_holdout_external_scoring"])
        self.assertEqual(summary["final_score"], "not_performed")
        self.assertFalse(summary["candidate_freeze"])
        self.assertFalse(summary["runtime_leakage_detected"])
        self.assertFalse(summary["native_output_mutation"])


if __name__ == "__main__":
    unittest.main()
