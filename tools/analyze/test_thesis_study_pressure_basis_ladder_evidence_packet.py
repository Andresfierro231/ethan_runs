import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze import build_thesis_study_pressure_basis_ladder_evidence_packet as builder


class ThesisStudyPressureBasisLadderEvidencePacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tempdir.name) / "pressure_packet"
        cls.patch = mock.patch.object(builder, "OUT", cls.out)
        cls.patch.start()
        cls.summary = builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.tempdir.cleanup()

    def read_rows(self, name):
        with (self.out / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    def test_section_effective_values_are_negative_and_not_admitted(self):
        rows = self.read_rows("section_effective_residual_values.csv")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(float(row["available_signed_residual_pa"]) < 0 for row in rows))
        self.assertEqual({row["final_label"] for row in rows}, {"section_effective"})
        self.assertEqual({row["admission_status"] for row in rows}, {"not_admitted_for_component_K_or_F6"})

    def test_basis_ladder_names_hybrid_section_residual(self):
        rows = self.read_rows("pressure_basis_ladder.csv")
        steps = {row["basis_step"]: row for row in rows}
        self.assertIn("section_effective_residual", steps)
        self.assertIn("Delta_p_recirc_section", steps["section_effective_residual"]["formula_or_extraction"])
        self.assertIn("component K", steps["section_effective_residual"]["forbidden_use"])

    def test_gate_matrix_blocks_f6_and_source_release(self):
        rows = self.read_rows("pressure_non_admission_gate_matrix.csv")
        gates = {row["gate"]: row for row in rows}
        self.assertEqual(gates["ordinary_flow"]["status"], "fail")
        self.assertEqual(gates["same_qoi_mesh_time_uq"]["status"], "fail")
        self.assertEqual(gates["source_property_nominal_train_release"]["status"], "fail")

    def test_f3_f6_comparison_is_not_numeric(self):
        rows = self.read_rows("f3_f6_and_hybrid_comparison_status.csv")
        f3 = next(row for row in rows if row["comparison"] == "F3-VS-S14-F6")
        self.assertEqual(f3["status"], "not_evaluated_no_admitted_or_ordinary_candidate")
        self.assertEqual(f3["numeric_score_released"], "False")

    def test_summary_guardrails(self):
        with (self.out / "summary.json").open() as handle:
            summary = json.load(handle)
        self.assertEqual(summary["section_effective_rows"], 3)
        self.assertEqual(summary["negative_signed_residual_rows"], 3)
        self.assertEqual(summary["component_k_admitted_rows"], 0)
        self.assertFalse(summary["f3_f6_numeric_comparison_released"])
        self.assertFalse(summary["validation_holdout_external_scoring"])
        self.assertFalse(summary["fitting_or_model_selection_performed"])


if __name__ == "__main__":
    unittest.main()
