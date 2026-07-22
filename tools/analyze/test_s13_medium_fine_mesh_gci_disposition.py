import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_s13_medium_fine_mesh_gci_disposition as builder


class S13MediumFineMeshGciDispositionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "mesh_gci_disposition"
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

    def test_summary_fails_closed_without_coarse_triplets(self):
        self.assertEqual(
            self.summary["decision"],
            "medium_fine_mesh_disposition_complete_formal_gci_fail_closed_no_admission",
        )
        self.assertEqual(self.summary["case_qoi_spread_rows"], 12)
        self.assertEqual(self.summary["qoi_summary_rows"], 4)
        self.assertTrue(self.summary["same_label_medium_fine_rows_exist"])
        self.assertFalse(self.summary["same_label_coarse_rows_exist"])
        self.assertFalse(self.summary["formal_gci_run"])
        self.assertFalse(self.summary["production_harvest_allowed"])
        self.assertFalse(self.summary["admission_allowed"])

    def test_case_spread_has_all_cases_qois_and_blocks_admission(self):
        rows = self.read_rows("case_qoi_medium_fine_spread.csv")
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["qoi_label"] for row in rows}, set(builder.QOI_LABELS))
        self.assertEqual({row["formal_gci_status"] for row in rows}, {"blocked_missing_same_label_coarse_member"})
        self.assertEqual({row["same_label_coarse_row_exists"] for row in rows}, {"False"})
        self.assertEqual({row["admission_allowed"] for row in rows}, {"False"})

    def test_qwall_is_low_spread_but_proxies_remain_large(self):
        rows = {row["qoi_label"]: row for row in self.read_rows("qoi_mesh_disposition_summary.csv")}
        self.assertLess(float(rows["Q_wall_W"]["max_medium_fine_relative_percent_vs_fine"]), 1.0)
        self.assertEqual(
            rows["Q_wall_W"]["diagnostic_disposition"],
            "medium_fine_spread_low_diagnostic_only_formal_gci_blocked",
        )
        self.assertGreater(
            float(rows["mdot_exchange_positive_outward_proxy_kg_s"]["max_medium_fine_relative_percent_vs_fine"]),
            50.0,
        )
        self.assertGreater(
            float(rows["wall_core_bulk_temperature_contrast_K"]["max_medium_fine_relative_percent_vs_fine"]),
            40.0,
        )
        self.assertEqual({row["admission_allowed"] for row in rows.values()}, {"False"})

    def test_production_gate_and_blockers_are_fail_closed(self):
        gates = {row["gate"]: row for row in self.read_rows("production_admission_gate.csv")}
        self.assertEqual(gates["split_rerun_exact_label_rows"]["status"], "pass")
        self.assertEqual(gates["same_label_three_grid_gci"]["status"], "fail_closed_missing_coarse")
        self.assertEqual(gates["production_harvest_or_admission"]["status"], "do_not_run")

        blockers = {row["blocker"]: row for row in self.read_rows("formal_gci_blocker_table.csv")}
        self.assertEqual(blockers["formal_three_grid_gci"]["status"], "blocked")
        self.assertIn("same-label coarse", blockers["formal_three_grid_gci"]["evidence"])

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
