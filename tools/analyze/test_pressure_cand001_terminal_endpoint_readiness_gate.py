from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_pressure_cand001_terminal_endpoint_readiness_gate as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PressureCand001TerminalEndpointReadinessGateTests(unittest.TestCase):
    def test_scheduler_rows_keep_job_running_and_nonterminal(self) -> None:
        rows = builder.scheduler_rows("test-time")
        decision_rows = [row for row in rows if row["ready_effect"] == "blocks_endpoint_harvest"]
        self.assertGreaterEqual(len(decision_rows), 2)
        self.assertTrue(all(row["state"] == "RUNNING" for row in decision_rows))
        self.assertTrue(all(row["terminal"] == "false" for row in decision_rows))

    def test_endpoint_gate_blocks_all_required_fields(self) -> None:
        rows = builder.endpoint_gate_rows()
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(row["readiness_now"] == "blocked_job_not_terminal" for row in rows))
        self.assertIn("p", {row["field_name"] for row in rows})
        self.assertIn("U", {row["field_name"] for row in rows})
        self.assertIn("RAF", {row["field_name"] for row in rows})

    def test_ordinary_flow_uq_gate_has_no_admission(self) -> None:
        rows = builder.ordinary_flow_uq_rows()
        by_gate = {row["gate"]: row for row in rows}
        self.assertEqual(by_gate["terminal_success"]["status_now"], "fail_blocked_running")
        self.assertTrue(by_gate["endpoint_fields"]["status_now"].startswith("fail_0"))
        self.assertEqual(by_gate["admission_guard"]["status_now"], "pass_guardrail_no_admission")

    def test_build_outputs_fail_closed_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "package"
            summary = builder.build(out)
            self.assertEqual(
                summary["decision"],
                "cand001_endpoint_readiness_blocked_job_running_no_sampler_no_admission",
            )
            self.assertFalse(summary["active_job_terminal"])
            self.assertFalse(summary["sampler_allowed_now"])
            self.assertFalse(summary["admission_allowed_now"])
            self.assertEqual(summary["endpoint_ready_fields"], 0)
            endpoints = read_rows(out / "endpoint_readiness_gate.csv")
            self.assertTrue(all(row["readiness_now"] == "blocked_job_not_terminal" for row in endpoints))
            self.assertTrue((out / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()
