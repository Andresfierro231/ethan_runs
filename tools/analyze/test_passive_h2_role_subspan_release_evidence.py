from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_passive_h2_role_subspan_release_evidence as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2RoleSubspanReleaseEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.main()

    def test_summary_remains_fail_closed(self) -> None:
        summary = json.loads((builder.OUT_DIR / "summary.json").read_text())
        self.assertEqual(
            summary["decision"],
            "passive_h2_role_subspan_release_evidence_fail_closed_setup_only",
        )
        self.assertEqual(summary["family_rows"], 5)
        self.assertEqual(summary["release_grade_rows"], 0)
        self.assertFalse(summary["source_property_release"])

    def test_release_matrix_has_no_release_grade_family(self) -> None:
        rows = read_csv(builder.OUT_DIR / "release_grade_subspan_evidence_matrix.csv")
        self.assertEqual(len(rows), 5)
        self.assertEqual({row["release_grade_now"] for row in rows}, {"False"})
        self.assertTrue(all("exact_same_qoi_uq" in row["missing_release_fields"] for row in rows))

    def test_runtime_legality_keeps_forbidden_inputs_closed(self) -> None:
        rows = read_csv(builder.OUT_DIR / "runtime_legality_matrix.csv")
        by_item = {row["runtime_item"]: row for row in rows}
        self.assertEqual(by_item["realized CFD wallHeatFlux/Qwall"]["legal_runtime_input"], "False")
        self.assertEqual(by_item["validation/holdout temperatures"]["legal_runtime_input"], "False")


if __name__ == "__main__":
    unittest.main()
