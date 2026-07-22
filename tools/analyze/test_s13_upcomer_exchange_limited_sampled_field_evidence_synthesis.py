from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13LimitedSampledFieldEvidenceSynthesisTests(unittest.TestCase):
    def test_exchange_rows_are_finite_and_diagnostic_only(self) -> None:
        rows = builder.exchange_trend_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["finite_required_metrics"] == "true" for row in rows))
        self.assertTrue(all(row["production_harvest_allowed"] == "false" for row in rows))
        self.assertTrue(all(row["coefficient_admission_allowed"] == "false" for row in rows))

    def test_gate_matrix_keeps_production_blocked(self) -> None:
        rows = builder.sampled_field_gate_rows()
        self.assertEqual(len(rows), 30)
        by_gate = {(row["case_id"], row["gate"]): row for row in rows}
        for case_id in ("salt_2", "salt_3", "salt_4"):
            self.assertEqual(by_gate[(case_id, "interface_U")]["diagnostic_ready"], "true")
            self.assertEqual(by_gate[(case_id, "wall_T")]["diagnostic_ready"], "true")
            self.assertEqual(by_gate[(case_id, "Q_wall_W")]["blocks_production"], "true")
            self.assertEqual(by_gate[(case_id, "pressure")]["blocks_production"], "true")
            self.assertEqual(by_gate[(case_id, "same_qoi_uq")]["production_ready"], "false")

    def test_predictive_path_status_includes_required_thesis_topics(self) -> None:
        steps = {row["path_step"] for row in builder.predictive_path_status_rows()}
        self.assertIn("runtime_input_contract", steps)
        self.assertIn("train_validation_holdout_external_test_separation", steps)
        self.assertIn("pressure_gate", steps)
        self.assertIn("thermal_gate", steps)
        self.assertIn("recirculation_exchange_gate", steps)
        self.assertIn("negative_results_as_scientific_evidence", steps)

    def test_build_outputs_insert_ready_package_without_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["decision"], "diagnostic_only_thesis_ready_production_harvest_blocked")
            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["finite_exchange_rows"], 3)
            self.assertEqual(summary["production_ready_gate_rows"], 0)
            self.assertEqual(summary["production_harvest_allowed_rows"], 0)
            self.assertFalse(summary["thesis_current_file_edit"])
            self.assertTrue((out / "thesis_insert_package.md").exists())
            self.assertTrue((out / "figures" / "svg" / "s13_predictive_path_status.svg").exists())
            gates = read_rows(out / "s13_sampled_field_gate_matrix.csv")
            self.assertEqual(sum(1 for row in gates if row["blocks_production"] == "true"), 15)


if __name__ == "__main__":
    unittest.main()
