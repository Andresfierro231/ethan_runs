import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_s13_coarse_equivalence_open_cv_heatflow_contract as builder


class S13CoarseEquivalenceOpenCvHeatflowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "contract"
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

    def test_summary_resolves_coarse_as_reference_only(self):
        self.assertEqual(
            self.summary["decision"],
            "coarse_reference_candidate_only_equivalence_contract_defined_no_gci_no_admission",
        )
        self.assertEqual(self.summary["current_coarse_candidate_rows"], 12)
        self.assertEqual(self.summary["coarse_equivalence_admitted_rows"], 0)
        self.assertFalse(self.summary["formal_gci_unlocked"])
        self.assertFalse(self.summary["production_harvest_allowed"])
        self.assertFalse(self.summary["admission_allowed"])

    def test_coarse_basis_table_blocks_every_qoi(self):
        rows = self.read_rows("coarse_basis_resolution.csv")
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual({row["qoi_label"] for row in rows}, set(builder.QOI_LABELS))
        self.assertEqual({row["current_coarse_candidate_exists"] for row in rows}, {"True"})
        self.assertEqual({row["coarse_equivalence_admitted"] for row in rows}, {"False"})
        self.assertEqual({row["formal_gci_unlocked"] for row in rows}, {"False"})
        self.assertEqual(
            {row["resolution"] for row in rows},
            {"current_coarse_reference_candidate_only_not_equivalent_yet"},
        )

    def test_open_cv_and_averages_policy(self):
        open_cv = {row["use_case"]: row for row in self.read_rows("open_cv_use_policy.csv")}
        self.assertEqual(open_cv["diagnostic_exchange_or_heat_accounting"]["open_cv_allowed"], "True")
        self.assertEqual(open_cv["throughflow_plus_recirc_exchange_cell_admission"]["open_cv_allowed"], "False")
        self.assertEqual(open_cv["throughflow_plus_recirc_exchange_cell_admission"]["closed_cv_required"], "True")

        avg = {row["quantity_type"]: row for row in self.read_rows("averaged_value_policy.csv")}
        self.assertEqual(avg["intensive_state"]["averaged_values_allowed"], "True")
        self.assertEqual(avg["flux_or_integral"]["averaged_values_allowed"], "False")
        self.assertEqual(avg["residual"]["averaged_values_allowed"], "False")

    def test_heatflow_focus_keeps_source_side_distinct(self):
        rows = self.read_rows("source_side_heatflow_focus.csv")
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["heat_flow_match_status"] for row in rows}, {"not_physical_match_with_current_exchange_scale"})
        self.assertTrue(all(float(row["qwall_to_source_side_ratio"]) < 0.15 for row in rows))
        self.assertEqual({row["admission_allowed_now"] for row in rows}, {"False"})

    def test_equivalence_contract_has_required_criteria(self):
        criteria = {row["criterion"]: row for row in self.read_rows("auditable_coarse_equivalence_contract.csv")}
        for key in [
            "qoi_label_formula_sign_units",
            "geometry_mask_provenance",
            "time_window_equivalence",
            "field_source_property_basis",
            "closed_or_residual_accounted_cv",
            "same_qoi_uq_and_mesh_disposition",
        ]:
            self.assertIn(key, criteria)
        self.assertEqual(criteria["closed_or_residual_accounted_cv"]["necessity"], "required_for_admission")

    def test_guardrails_false(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        for key in [
            "source_property_release",
            "Qwall_release",
            "scheduler_action",
            "native_solver_outputs_mutated",
            "registry_or_admission_mutated",
            "validation_holdout_external_scoring",
            "coefficient_admission",
            "s11_s12_s13_s15_s6_trigger",
            "generated_docs_index_refreshed",
        ]:
            self.assertFalse(summary[key], key)


if __name__ == "__main__":
    unittest.main()
