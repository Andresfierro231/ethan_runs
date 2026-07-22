import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.analyze import build_s13_throughflow_enthalpy_endpoint_preflight as builder


class S13ThroughflowEnthalpyEndpointPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "s13_throughflow_preflight"
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

    def test_summary_is_fail_closed(self):
        self.assertEqual(
            self.summary["decision"],
            "s13_throughflow_endpoint_preflight_complete_fail_closed_no_residual_value",
        )
        self.assertEqual(self.summary["case_endpoint_contract_rows"], 3)
        self.assertEqual(self.summary["harvest_ready_cases"], 0)
        self.assertEqual(self.summary["residual_value_released_rows"], 0)
        for key in [
            "source_property_release",
            "Qwall_release",
            "coefficient_admission",
            "candidate_freeze",
            "validation_holdout_external_scoring",
            "solver_postprocessing_sampler_harvest_uq_launched",
            "endpoint_proxy_substitution",
        ]:
            self.assertFalse(self.summary[key], key)

    def test_endpoint_contract_defines_composite_upcomer(self):
        rows = self.read_rows("endpoint_definition_contract.csv")
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        for row in rows:
            self.assertEqual(row["throughflow_cv"], "composite_upcomer_open_cv")
            self.assertEqual(row["inlet_endpoint"], "left_lower_leg:s00")
            self.assertEqual(row["outlet_endpoint"], "left_upper_leg:s04")
            self.assertEqual(row["same_basis_harvest_ready"], "False")
            self.assertIn("true throughflow mdot", row["blocking_reason"])

    def test_required_inputs_include_all_blockers(self):
        rows = self.read_rows("required_input_status_matrix.csv")
        self.assertEqual(len(rows), 27)
        labels = {row["required_label"] for row in rows}
        self.assertIn("T_in_bulk_K", labels)
        self.assertIn("T_out_bulk_K", labels)
        self.assertIn("mdot_throughflow_kg_s", labels)
        self.assertIn("cp_J_kg_K", labels)
        self.assertIn("Q_storage_W", labels)
        self.assertIn("Q_other_named_losses_W", labels)
        self.assertEqual({row["release_or_harvest_ready"] for row in rows}, {"False"})

    def test_postprocessing_is_diagnostic_only(self):
        rows = self.read_rows("postprocessing_support_summary.csv")
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["admissibility_role"], "diagnostic_drift_and_error_support_only")
            self.assertGreater(int(row["mdot_window_stat_rows"]), 0)
            self.assertGreater(int(row["temperature_window_stat_rows"]), 0)
            self.assertIn("forbidden as predictive runtime inputs", row["why_not_residual_input"])

    def test_command_contract_does_not_run_now(self):
        rows = self.read_rows("sampling_command_contract.csv")
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["run_now"] for row in rows}, {"False"})
        labels = {row["command_label"] for row in rows}
        self.assertIn("stage_read_only_case_copy", labels)
        self.assertIn("run_openfoam_sampling_on_compute", labels)

    def test_readme_and_methodology_exist(self):
        self.assertTrue((self.out / "README.md").exists())
        self.assertTrue((self.out / "methodology_and_assumptions.md").exists())
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["hidden_multiplier_or_internal_Nu_absorption"])


if __name__ == "__main__":
    unittest.main()
