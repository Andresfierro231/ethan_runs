import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_s13_candidate_coarse_medium_fine_reconciliation as builder


class S13CandidateCoarseMediumFineReconciliationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "reconciliation"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tmp.cleanup()

    def read_rows(self, name):
        with (self.out / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_summary_fails_closed_on_nonadmitted_coarse_equivalence(self):
        self.assertEqual(
            self.summary["decision"],
            "candidate_triplets_quantified_formal_gci_fail_closed_coarse_equivalence_not_admitted",
        )
        self.assertEqual(self.summary["candidate_triplet_rows"], 12)
        self.assertEqual(self.summary["qoi_summary_rows"], 4)
        self.assertEqual(self.summary["coarse_equivalence_admitted_rows"], 0)
        self.assertFalse(self.summary["formal_gci_run"])
        self.assertFalse(self.summary["production_harvest_allowed"])
        self.assertFalse(self.summary["admission_allowed"])

    def test_triplet_rows_have_all_cases_and_qois(self):
        rows = self.read_rows("candidate_triplet_reconciliation.csv")
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["qoi_label"] for row in rows}, set(builder.QOI_LABELS))
        self.assertEqual({row["coarse_equivalence_admitted"] for row in rows}, {"False"})
        self.assertEqual({row["formal_gci_status"] for row in rows}, {"not_run_coarse_equivalence_not_admitted"})
        self.assertEqual({row["production_use_allowed"] for row in rows}, {"False"})

    def test_qwall_is_diagnostic_only_even_with_low_medium_fine_spread(self):
        summaries = {row["qoi_label"]: row for row in self.read_rows("qoi_reconciliation_summary.csv")}
        self.assertLess(float(summaries["Q_wall_W"]["max_medium_fine_relative_percent_vs_fine"]), 1.0)
        self.assertGreater(float(summaries["Q_wall_W"]["max_coarse_fine_relative_percent_vs_fine"]), 0.0)
        self.assertEqual(
            summaries["Q_wall_W"]["diagnostic_disposition"],
            "qwall_low_medium_fine_spread_but_coarse_not_admitted",
        )
        self.assertEqual({row["admission_allowed"] for row in summaries.values()}, {"False"})

    def test_gate_blocks_formal_gci_and_admission(self):
        gates = {row["gate"]: row for row in self.read_rows("production_admission_gate.csv")}
        self.assertEqual(gates["canonical_medium_fine_exact_label_rows"]["status"], "pass")
        self.assertEqual(gates["current_coarse_candidate_rows"]["status"], "diagnostic_pass")
        self.assertEqual(gates["coarse_equivalence_contract"]["status"], "fail_closed_not_admitted")
        self.assertEqual(gates["formal_gci"]["status"], "not_run")

    def test_guardrails_are_false(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        for key in [
            "source_property_release",
            "Qwall_release",
            "scheduler_action",
            "native_solver_outputs_mutated",
            "registry_or_admission_mutated",
            "validation_holdout_external_scoring",
            "proxy_substitution",
            "coefficient_admission",
            "s11_s12_s13_s15_s6_trigger",
        ]:
            self.assertFalse(summary[key], key)


if __name__ == "__main__":
    unittest.main()
