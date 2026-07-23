from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_source_mapping_split_uq_preflight as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2SourceMappingSplitUqPreflightTests(unittest.TestCase):
    def test_mapping_support_is_not_release(self) -> None:
        rows = builder.mapping_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["source_backed_parent_mapping"] == "true" for row in rows))
        self.assertTrue(all(row["release_status"] != "release_ready" for row in rows))

    def test_split_conflicts_keep_salt3_salt4_diagnostic(self) -> None:
        rows = builder.split_rows()
        by_case = {row["case_id"]: row for row in rows}
        self.assertEqual(by_case["salt_2"]["disposition"], "train_context_only")
        self.assertEqual(by_case["salt_3"]["split_conflict"], "true")
        self.assertEqual(by_case["salt_4"]["split_conflict"], "true")
        self.assertTrue(all(row["protected_scoring_allowed"] == "false" for row in rows))

    def test_same_qoi_uq_blocks_release(self) -> None:
        rows = builder.same_qoi_uq_rows()
        self.assertTrue(any(row["status"] == "diagnostic_ready_train_context" for row in rows))
        self.assertTrue(any(row["release_effect"] == "blocks_candidate_freeze" for row in rows))
        self.assertFalse(any(row["release_effect"] == "release_ready" for row in rows))

    def test_build_fail_closed_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "passive_h2_source_mapping_split_uq_preflight_fail_closed_no_release_no_freeze",
            )
            self.assertEqual(summary["source_mapping_release_ready_rows"], 0)
            self.assertEqual(summary["split_conflict_rows"], 2)
            self.assertEqual(summary["same_qoi_release_ready_rows"], 0)
            self.assertFalse(summary["candidate_freeze"])
            rows = read_rows(out / "release_admission_readiness.csv")
            self.assertTrue(any(row["gate"] == "runtime_smoke" and row["ready_now"] == "true" for row in rows))


if __name__ == "__main__":
    unittest.main()
