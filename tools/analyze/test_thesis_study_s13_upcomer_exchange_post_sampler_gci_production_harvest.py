import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_thesis_study_s13_upcomer_exchange_post_sampler_gci_production_harvest as builder


class S13PostSamplerGciProductionHarvestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "post_sampler_gate"
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

    def test_summary_is_fail_closed_after_sampler(self):
        self.assertEqual(
            self.summary["decision"],
            "post_sampler_fail_closed_no_terminal_qoi_no_mesh_gci_no_production_harvest",
        )
        self.assertEqual(self.summary["geometry_rows"], 6)
        self.assertEqual(self.summary["terminal_window_reduction_rows"], 0)
        self.assertEqual(self.summary["exact_label_qoi_rows"], 0)
        self.assertEqual(self.summary["sampling_error_rows"], 6)
        self.assertFalse(self.summary["production_harvest_allowed"])
        self.assertFalse(self.summary["admission_allowed"])
        self.assertFalse(self.summary["s11_s12_s13_s15_s6_trigger"])

    def test_qoi_readiness_preserves_temporal_uq_but_blocks_mesh_gci(self):
        rows = self.read_rows("post_sampler_qoi_mesh_gci_readiness.csv")
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["same_qoi_temporal_uq_status"] for row in rows}, {"executed"})
        self.assertEqual({row["post_sampler_exact_label_qoi_rows"] for row in rows}, {"0"})
        self.assertEqual({row["post_sampler_same_label_mesh_gci_ready"] for row in rows}, {"False"})
        self.assertEqual({row["production_harvest_allowed_now"] for row in rows}, {"False"})

    def test_sampler_disposition_records_missing_face_vectors(self):
        rows = self.read_rows("post_sampler_disposition.csv")
        causes = [row for row in rows if row["artifact"] == "sampling_error_cause"]
        self.assertEqual(len(causes), 6)
        self.assertTrue(all("missing" in row["reason"] for row in causes))
        self.assertEqual({row["usable_for_terminal_qoi"] for row in causes}, {"False"})

    def test_go_no_go_closes_production_and_downstream(self):
        gates = {row["gate"]: row for row in self.read_rows("production_go_no_go_gate.csv")}
        self.assertEqual(gates["sampler_terminal_execution"]["status"], "fail_closed")
        self.assertEqual(gates["same_label_mesh_gci"]["status"], "blocked_no_post_sampler_rows")
        self.assertEqual(gates["production_harvest"]["status"], "do_not_run")

        downstream = {row["downstream_gate"]: row for row in self.read_rows("s11_s15_consequence_table.csv")}
        self.assertEqual(downstream["S11 candidate source/property refresh"]["status"], "closed")
        self.assertEqual(downstream["S15 freeze and S6 final score"]["status"], "closed")

    def test_guardrails_are_false_for_mutating_actions(self):
        with (self.out / "summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        for key in [
            "source_property_release",
            "Qwall_release",
            "ordinary_upcomer_Nu_fD_K_admitted",
            "exchange_cell_coefficient_admitted",
            "scheduler_action",
            "native_solver_outputs_mutated",
            "registry_or_admission_mutated",
            "solver_postprocess_sampler_harvest_uq_launched",
            "validation_holdout_external_scoring",
            "proxy_substitution",
            "residual_absorbed_into_internal_Nu",
        ]:
            self.assertFalse(summary[key], key)


if __name__ == "__main__":
    unittest.main()
