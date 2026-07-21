"""Tests for active-row cleanup and forward-work readiness audit."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_active_row_cleanup_and_forward_work_readiness import (
    build_issue_rows,
    build_package,
    build_status_rows,
    parse_active_rows,
)


SAMPLE_BOARD = """# Task Board

## Active

| Task ID | Role | Owner | Scope | Goal |
| --- | --- | --- | --- | --- |
| AGENT-900 | Writer | codex | `.agent/BOARD.md` | First task. STATUS: ACTIVE 2026-07-15. |
| AGENT-900 | Tester | codex | `.agent/BOARD.md` | Duplicate task. STATUS: COMPLETE 2026-07-15. |
| AGENT-901 | Implementer | codex | `.agent/status/2026-07-15_AGENT-901.md` | Missing status task. STATUS: RUNNING 2026-07-15. |

## Planned
"""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ActiveRowCleanupReadinessTests(unittest.TestCase):
    def test_parse_active_rows_and_status(self) -> None:
        rows = parse_active_rows(SAMPLE_BOARD)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["task_id"], "AGENT-900")
        self.assertEqual(rows[0]["board_status"], "ACTIVE 2026-07-15")
        self.assertEqual(rows[1]["board_status"], "COMPLETE 2026-07-15")

    def test_duplicate_and_missing_status_issues_are_reported(self) -> None:
        active = parse_active_rows(SAMPLE_BOARD)
        status_rows = build_status_rows(active)
        issues = build_issue_rows(status_rows)
        issue_types = {row["issue_type"] for row in issues}

        self.assertIn("duplicate_active_task_id", issue_types)
        self.assertIn("active_row_missing_status", issue_types)
        self.assertIn("board_hygiene", issue_types)

    def test_real_package_writes_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["task"], "AGENT-401")
            self.assertEqual(summary["final_forward_v1_status"], "blocked_no_go_final_forward_v1_not_admitted")
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["scheduler_action_taken"])
            self.assertFalse(summary["generated_indexes_mutated"])

            for name in {
                "README.md",
                "active_row_status_audit.csv",
                "forward_work_claim_matrix.csv",
                "safe_next_work_queue.csv",
                "coordination_issues.csv",
                "source_manifest.csv",
                "summary.json",
            }:
                self.assertTrue((out / name).exists(), name)

            status_rows = read_csv(out / "active_row_status_audit.csv")
            self.assertGreater(len(status_rows), 0)
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["task"], "AGENT-401")

    def test_forward_work_matrix_blocks_claimed_cooler_scope(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            rows = {row["work_area"]: row for row in read_csv(out / "forward_work_claim_matrix.csv")}

            self.assertIn("setup_only_cooler_hx_synthesis", rows)
            self.assertIn(rows["setup_only_cooler_hx_synthesis"]["safe_to_claim_now"], {"no", "yes"})
            if rows["setup_only_cooler_hx_synthesis"]["claimed_by_active_tasks"]:
                self.assertEqual(rows["setup_only_cooler_hx_synthesis"]["safe_to_claim_now"], "no")


if __name__ == "__main__":
    unittest.main()
