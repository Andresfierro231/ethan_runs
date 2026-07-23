from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_role_subspan_mapping_recovery as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2RoleSubspanMappingRecoveryTests(unittest.TestCase):
    def test_patch_subspan_coverage_recovers_all_case_family_rows(self) -> None:
        rows = builder.patch_subspan_coverage_rows()
        self.assertEqual(len(rows), 15)
        self.assertEqual(sum(row["setup_subspan_support_ready"] == "true" for row in rows), 15)
        self.assertEqual({row["source_family"] for row in rows}, set(builder.FAMILIES))
        self.assertTrue(all(row["release_grade_subspan_ready_now"] == "false" for row in rows))

    def test_salt34_runtime_smoke_is_diagnostic_only(self) -> None:
        coverage = builder.patch_subspan_coverage_rows()
        rows = builder.salt34_runtime_smoke_eligibility_rows(coverage)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["runtime_smoke_eligible_next_row"] == "true" for row in rows))
        self.assertTrue(all(row["protected_scoring_eligible"] == "false" for row in rows))
        self.assertEqual({row["decision"] for row in rows}, {"eligible_for_diagnostic_runtime_smoke_only"})

    def test_setup_uq_computes_finite_same_qoi_rows_without_release(self) -> None:
        rows = builder.setup_uq_rows()
        self.assertGreaterEqual(len(rows), len(builder.UQ_QOIS))
        computed = [row for row in rows if row["setup_only_uq_computed"] == "true"]
        self.assertGreaterEqual(len(computed), 20)
        self.assertFalse(any(row["admission_release_ready"] == "true" for row in rows))
        readiness = builder.qoi_readiness_rows(rows)
        self.assertEqual(len(readiness), len(builder.UQ_QOIS))
        self.assertTrue(all(row["same_qoi_setup_only_uq_available"] == "true" for row in readiness))

    def test_build_summary_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_role_subspan_mapping_recovered_diagnostic_uq_done_no_release_no_freeze",
            )
            self.assertEqual(summary["setup_subspan_support_ready_rows"], 15)
            self.assertEqual(summary["salt34_runtime_smoke_eligible_rows"], 2)
            self.assertEqual(summary["source_property_release_ready_rows"], 0)
            self.assertFalse(summary["candidate_freeze"])
            gates = read_rows(out / "release_gate_matrix.csv")
            self.assertTrue(any(row["gate"] == "same_qoi_setup_only_uq_computed" for row in gates))
            self.assertTrue(any(row["gate"] == "candidate_freeze" and row["ready_now"] == "false" for row in gates))


if __name__ == "__main__":
    unittest.main()
