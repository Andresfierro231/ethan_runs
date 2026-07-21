import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_forward_v1_plan_implementation_closeout import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ForwardV1PlanImplementationCloseoutTests(unittest.TestCase):
    def test_package_records_run_and_blocked_items(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = build_package(out)

            self.assertEqual(summary["task"], "AGENT-403")
            self.assertEqual(
                summary["final_forward_v1_status"],
                "blocked_no_go_final_forward_v1_not_admitted",
            )
            self.assertEqual(summary["local_verification_status"], "passed")
            self.assertFalse(summary["scheduler_mutated"])
            self.assertFalse(summary["new_solver_or_postprocessing_jobs_submitted"])

            runs = {row["run_id"]: row for row in read_csv(out / "run_execution_matrix.csv")}
            self.assertEqual(runs["focused_forward_v1_unittest_suite"]["status"], "ran_passed")
            self.assertEqual(runs["final_forward_v1_scorecard"]["status"], "not_run_blocked")

            blocked = {row["blocked_item"]: row for row in read_csv(out / "blocked_or_deferred_runs.csv")}
            self.assertIn("agent373_hydraulic_chain", blocked)
            self.assertIn("pm5_parser_repair", blocked)

    def test_verified_artifacts_include_sensor_and_hx_inputs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            artifacts = {row["artifact_id"]: row for row in read_csv(out / "verified_artifacts.csv")}

            self.assertEqual(artifacts["AGENT-393_sensor_map_policy_refresh"]["exists"], "true")
            self.assertEqual(artifacts["AGENT-394_setup_only_hx_action_table"]["exists"], "true")
            self.assertEqual(
                artifacts["AGENT-404_pm5_parser_repair"]["forward_v1_use"],
                "pending_active_claim",
            )

    def test_summary_json_is_written(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            build_package(out)
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))

            self.assertEqual(parsed["focused_unittest_count"], 46)
            self.assertGreaterEqual(parsed["sensor_policy_rows"], 1)
            self.assertIn("final_forward_v1_scorecard", parsed["not_run_items"])


if __name__ == "__main__":
    unittest.main()
