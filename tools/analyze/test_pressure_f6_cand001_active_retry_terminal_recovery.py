#!/usr/bin/env python3.11
"""Validation for the CAND001 active retry terminal recovery package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery"
TASK_ID = "TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True)
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))

    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "continue_existing_cand001_retry_monitor_only_no_duplicate_submit"
    assert summary["candidate_id"] == "CAND-001"
    assert summary["active_retry_job_id"] == "3308712"
    assert summary["active_retry_case_rows"] == 4
    assert summary["prior_timeout_jobs"] == 2
    assert summary["worth_continuing"] is True
    assert summary["terminal_source_recovery_only"] is True
    assert summary["new_scheduler_submission"] is False
    assert summary["duplicate_submit_allowed"] is False
    assert summary["f6_scoring_allowed_now"] is False
    assert summary["component_k_admitted"] is False
    assert summary["cluster_k_admitted"] is False
    assert summary["clipped_k"] is False
    assert summary["hidden_global_multiplier"] is False
    assert summary["f6_fit_performed"] is False
    assert summary["s11_s15_s6_trigger"] is False
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False

    source_rows = read_csv(OUT_DIR / "active_retry_source_contract.csv")
    assert len(source_rows) == 4
    assert {row["active_retry_job_id"] for row in source_rows} == {"3308712"}
    assert {row["allowed_use"] for row in source_rows} == {"terminal_source_recovery_only_not_F6_scoring"}
    assert all(row["endpoint_labels"] == "lower_leg__s04;right_leg__s00" for row in source_rows)

    duplicate_rows = read_csv(OUT_DIR / "duplicate_launch_guard.csv")
    assert len(duplicate_rows) == 1
    assert duplicate_rows[0]["new_submit_allowed"] == "False"
    assert duplicate_rows[0]["cancel_or_requeue_allowed"] == "False"
    assert duplicate_rows[0]["monitor_allowed"] == "True"

    guardrails = {row["guardrail"]: row for row in read_csv(OUT_DIR / "no_scoring_guardrails.csv")}
    for key in (
        "new_scheduler_submission_in_this_task",
        "F6_scoring_now",
        "component_K_or_cluster_K_admission",
        "clipped_K_or_global_multiplier",
        "native_output_mutation",
        "registry_or_admission_mutation",
    ):
        assert guardrails[key]["allowed"] == "False"

    decision_tree = read_csv(OUT_DIR / "post_terminal_decision_tree.csv")
    assert len(decision_tree) == 5
    assert any(row["event"] == "3308712_success_and_cases_terminal" for row in decision_tree)
    assert any("F6 scoring" in row["forbidden_action"] for row in decision_tree)

    assert (OUT_DIR / "README.md").exists()
    assert (OUT_DIR / "scientific_worth_assessment.md").exists()
    assert (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").exists()
    assert (ROOT / ".agent/journal/2026-07-22/pressure-f6-cand001-active-retry-terminal-recovery.md").exists()
    assert (ROOT / "imports/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery.json").exists()

    print("pressure F6 CAND001 active retry terminal recovery package passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
