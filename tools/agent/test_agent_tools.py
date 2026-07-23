#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from tools.agent.background_compute_helper import infer_host_kind, recommend
from tools.agent.board_archive import archive_task, build_outputs
from tools.agent.board_slice import filter_entries as filter_slice_entries
from tools.agent.board_summary import filter_entries, parse_section_rows
from tools.agent.case_schema_lint import _hits
from tools.agent.closeout_stub import build_stubs
from tools.agent.common import active_conflicts, find_task, parse_board
from tools.agent.finish_task import (
    _doc_declares_task,
    _source_property_gate_warnings,
    _validate_journal_doc,
    _validate_manifest,
    _validate_status_doc,
)
from tools.agent.gate_snapshot import summarize_package
from tools.agent.guardrail_summary import summarize as summarize_guardrail_lines
from tools.agent.live_blockers import parse_open_blockers
from tools.agent.package_brief import summarize_path
from tools.agent.runtime_input_lint import SAFE_CONTEXT_RE
from tools.agent.scope_conflict_audit import audit_rows, is_broad_edit_path
from tools.agent.source_property_gate import audit_paths
from tools.agent.split_policy_lint import line_allowed
from tools.agent.task_context import instruction_paths
from tools.agent.board_row import main as board_row_main
from tools.agent.board_slice import main as board_slice_main
from tools.agent.claim_task import main as claim_task_main
from tools.agent.closeout_bundle import main as closeout_bundle_main
from tools.agent.closeout_stub import main as closeout_stub_main
from tools.agent.package_digest import main as package_digest_main
from tools.agent.preview_csv import main as preview_csv_main
from tools.agent.read_csv_brief import main as read_csv_brief_main
from tools.docs.state_brief import blocker_open_table, extract_sections
from tools.git.diff_summary import top_dirs as git_diff_top_dirs


def test_parse_board_and_conflict_detection(tmp_path: Path):
    board = tmp_path / "BOARD.md"
    board.write_text(
        "\n".join(
            [
                "| Task ID | Role | Owner | Scope | Goal |",
                "| --- | --- | --- | --- | --- |",
                "| AGENT-1 | Implementer | codex | `tools/agent/**`, `.agent/BOARD.md` (own row only). READ-ONLY: `reports/**` | STATUS: ACTIVE 2026-07-17. |",
                "| AGENT-2 | Implementer | codex | `tools/agent/preflight_task.py`, `.agent/BOARD.md` (own row only). | STATUS: ACTIVE 2026-07-17. |",
                "| AGENT-3 | Writer | codex | `reports/example.md` | STATUS: COMPLETE 2026-07-17. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = parse_board(board)
    row = find_task("AGENT-1", rows)
    assert row is not None
    assert row.status == "active"
    assert "tools/agent/**" in row.edit_paths
    conflicts = active_conflicts(row, rows)
    assert conflicts == [
        {
            "task_id": "AGENT-2",
            "mine": "tools/agent/**",
            "theirs": "tools/agent/preflight_task.py",
            "status": "active",
        }
    ]


def test_board_archive_moves_archived_sections():
    board_text = "\n".join(
        [
            "## Active",
            "| Task ID | Role | Owner | Scope | Goal |",
            "| --- | --- | --- | --- | --- |",
            "| AGENT-1 | Writer | codex | `.agent/BOARD.md` | STATUS: ACTIVE 2026-07-22. |",
            "## Archived Complete - Example",
            "| Task ID | Role | Owner | Scope | Goal |",
            "| --- | --- | --- | --- | --- |",
            "| AGENT-2 | Writer | codex | `.agent/BOARD.md` | STATUS: COMPLETE 2026-07-22. |",
            "## Planned / Unclaimed",
            "| Task ID | Role | Owner | Scope | Goal |",
            "| --- | --- | --- | --- | --- |",
            "| TODO-OPEN | Writer | open | `.agent/BOARD.md` | do it. |",
            "## Board Rules",
            "- keep it tidy",
        ]
    )
    new_board, new_archive, moved = build_outputs(board_text, "")
    assert moved == 1
    assert "## Archived Complete - Example" not in new_board
    assert "AGENT-2" not in new_board
    assert "AGENT-2" in new_archive
    assert "Historical archived board rows live" in new_board


def test_board_archive_archives_one_completed_task():
    board_text = "\n".join(
        [
            "## Active",
            "| Task ID | Role | Owner | Scope | Goal |",
            "| --- | --- | --- | --- | --- |",
            "| TODO-DONE | Writer | codex | `.agent/BOARD.md` | STATUS: COMPLETE 2026-07-22. |",
            "| TODO-OPEN | Writer | codex | `.agent/BOARD.md` | STATUS: ACTIVE 2026-07-22. |",
        ]
    )
    new_board, new_archive = archive_task(board_text, "", "TODO-DONE")
    assert "TODO-DONE" not in new_board
    assert "TODO-OPEN" in new_board
    assert "TODO-DONE" in new_archive


def test_board_summary_keeps_section_context(tmp_path: Path):
    board = tmp_path / "BOARD.md"
    board.write_text(
        "\n".join(
            [
                "## Active",
                "| Task ID | Role | Owner | Scope | Goal |",
                "| --- | --- | --- | --- | --- |",
                "| AGENT-1 | Writer | codex | `.agent/BOARD.md` | STATUS: ACTIVE 2026-07-22. |",
                "## Planned / Unclaimed",
                "| Task ID | Role | Owner | Scope | Goal |",
                "| --- | --- | --- | --- | --- |",
                "| TODO-OPEN | Writer | open | `.agent/BOARD.md` | wait. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = parse_section_rows(board)
    assert [item["section"] for item in rows] == ["Active", "Planned / Unclaimed"]
    filtered = filter_entries(rows, task_filter="open", active_only=False)
    assert len(filtered) == 1
    assert filtered[0]["row"].task_id == "TODO-OPEN"
    assert filter_entries(rows, status_filter="active", active_only=True)[0]["row"].task_id == "AGENT-1"


def test_board_slice_filters_exact_task_and_open_rows(tmp_path: Path):
    board = tmp_path / "BOARD.md"
    board.write_text(
        "\n".join(
            [
                "## Active",
                "| Task ID | Role | Owner | Scope | Goal |",
                "| --- | --- | --- | --- | --- |",
                "| TODO-ONE | Writer | codex | `.agent/BOARD.md` | STATUS: ACTIVE 2026-07-22. |",
                "| TODO-TWO | Writer | codex | `.agent/BOARD.md` | STATUS: COMPLETE 2026-07-22. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = parse_section_rows(board)
    assert [item["row"].task_id for item in filter_slice_entries(rows, open_only=True)] == ["TODO-ONE"]
    assert [item["row"].task_id for item in filter_slice_entries(rows, task_id="TODO-TWO")] == ["TODO-TWO"]


def test_token_efficiency_aliases_delegate_to_existing_mains():
    assert board_row_main is board_slice_main
    assert package_digest_main is summarize_path.__globals__["main"]
    assert read_csv_brief_main is preview_csv_main
    assert claim_task_main.__module__ == "tools.agent.new_task"
    assert closeout_bundle_main is closeout_stub_main


def test_task_context_instruction_paths_for_tools_scope():
    paths = instruction_paths(["tools/agent/example.py", ".agent/BOARD.md"])
    assert "AGENTS.md" in paths
    assert ".agent/BOARD.md" in paths
    assert "tools/README.md" in paths or "tools/AGENTS.override.md" in paths


def test_package_brief_summarizes_json_and_csv(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "summary.json").write_text('{"decision":"fail_closed","rows":[1,2,3],"ready":false}\n', encoding="utf-8")
    (package / "evidence.csv").write_text("case_id,status\nS13,blocked\nS14,ready\n", encoding="utf-8")
    (package / "README.md").write_text("# Package Title\n\n## Evidence\n\nText.\n", encoding="utf-8")
    result = summarize_path(package, rows=1, csv_limit=4)
    assert result["file_count"] == 3
    assert result["summary_json"]["summary"]["decision"] == "fail_closed"
    assert result["csvs"][0]["row_count"] == 2
    assert result["csvs"][0]["sample_rows"] == [{"case_id": "S13", "status": "blocked"}]


def test_gate_snapshot_summarizes_summary_and_action_csv(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "summary.json").write_text(
        json.dumps(
            {
                "task_id": "TODO-EXAMPLE-2026-07-22",
                "decision": "fail_closed_no_freeze",
                "working_prototype_exists_now": True,
                "source_property_release_ready_rows": 0,
                "freeze_ready_candidates": 0,
                "final_score_values": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (package / "next_action_queue.csv").write_text(
        "priority,action,done_when\n1,recover Salt1 source basis,source-ready rows nonzero\n",
        encoding="utf-8",
    )
    result = summarize_package(package, limit=4)
    assert result["task_id"] == "TODO-EXAMPLE-2026-07-22"
    assert "working_prototype_exists_now=True" in result["pass_signals"]
    assert "source_property_release_ready_rows=0" in result["blocker_signals"]
    assert result["actions"][0]["rows"][0]["action"] == "recover Salt1 source basis"


def test_closeout_stub_dry_run_paths_and_manifest():
    result = build_stubs(
        "TODO-EXAMPLE-2026-07-22",
        title="Example Closeout",
        changed_files=["tools/agent/example.py"],
        read_only=[".agent/BOARD.md"],
        today="2026-07-22",
    )
    assert result["paths"]["status"] == ".agent/status/2026-07-22_TODO-EXAMPLE-2026-07-22.md"
    manifest = json.loads(result["contents"]["manifest"])
    assert manifest["task"] == "TODO-EXAMPLE-2026-07-22"
    assert manifest["task_id"] == "TODO-EXAMPLE-2026-07-22"
    assert manifest["no_scorecard_outputs"] is True


def test_state_brief_extracts_named_sections():
    text = "\n".join(
        [
            "# State",
            "## Active Board Tasks",
            "- TODO-ONE",
            "## Other",
            "- hidden",
            "## Open Blockers",
            "- blocker",
        ]
    )
    sections = extract_sections(text, {"Active Board Tasks", "Open Blockers"})
    assert sections["Active Board Tasks"] == ["- TODO-ONE"]
    assert sections["Open Blockers"] == ["- blocker"]


def test_state_brief_blocker_table_stops_before_notes():
    text = "\n".join(
        [
            "# BLOCKERS",
            "## Open (1)",
            "| id | severity |",
            "| --- | --- |",
            "| b1 | high |",
            "## Notes",
            "- long notes",
        ]
    )
    assert blocker_open_table(text) == ["## Open (1)", "| id | severity |", "| --- | --- |", "| b1 | high |"]


def test_live_blockers_parses_open_table_only():
    text = "\n".join(
        [
            "# BLOCKERS",
            "## Open (1)",
            "| id | severity | blocks | evidence | last reviewed |",
            "| --- | --- | --- | --- | --- |",
            "| `b1` | high | T1 | `work_products/x/README.md` | 2026-07-22 |",
            "## Resolved / superseded",
            "| `old` | resolved |",
        ]
    )
    rows = parse_open_blockers(text)
    assert rows == [
        {
            "id": "b1",
            "severity": "high",
            "blocks": "T1",
            "evidence": "work_products/x/README.md",
            "last reviewed": "2026-07-22",
        }
    ]


def test_scope_conflict_audit_flags_broad_open_claims(tmp_path: Path):
    board = tmp_path / "BOARD.md"
    board.write_text(
        "\n".join(
            [
                "| Task ID | Role | Owner | Scope | Goal |",
                "| --- | --- | --- | --- | --- |",
                "| TODO-BROAD | Writer | codex | `tools/analyze/`, `.agent/BOARD.md` (own row only) | STATUS: ACTIVE 2026-07-22. |",
                "| TODO-NARROW | Writer | codex | `tools/analyze/example.py`, `.agent/BOARD.md` (own row only) | STATUS: ACTIVE 2026-07-22. |",
                "| TODO-DONE | Writer | codex | `tools/agent/**` | STATUS: COMPLETE 2026-07-22. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = parse_board(board)
    result = audit_rows(rows)
    assert is_broad_edit_path("tools/analyze/")
    assert is_broad_edit_path("reports/**")
    assert is_broad_edit_path("work_products/<date>_example/**")
    assert not is_broad_edit_path(".agent/status/<date>_TODO-EXAMPLE.md")
    assert not is_broad_edit_path(".agent/journal/<date>/example.md")
    assert not is_broad_edit_path("imports/<date>_example.json")
    assert not is_broad_edit_path("tools/analyze/example.py")
    assert not is_broad_edit_path("work_products/2026-07/2026-07-22/2026-07-22_example/**")
    assert result["broad_scope_rows_total"] == 1
    assert result["conflict_rows_total"] == 2


def test_background_compute_recommendations():
    assert infer_host_kind("login3") == "login"
    assert infer_host_kind("c318-008") == "compute"
    assert recommend("login", "overnight", openfoam=True, persistent=True) == "sbatch"
    assert recommend("compute", "short", openfoam=True, persistent=False) == "srun"


def test_git_diff_summary_top_dirs_is_bounded():
    paths = [
        "tools/agent/a.py",
        "tools/agent/b.py",
        "tools/git/c.py",
        "reports/example.md",
    ]
    assert git_diff_top_dirs(paths, depth=2)[:2] == [("tools/agent", 2), ("tools/git", 1)]


def test_guardrail_summary_prefers_pass_fail_lines():
    lines = [
        "long setup line",
        "== CSEM guardrail check ==",
        "PASS: no TODO[source] markers found.",
        "ordinary diagnostic line",
        "NOTE: review claim-boundary hits.",
    ]
    assert summarize_guardrail_lines(lines, limit=3) == [
        "== CSEM guardrail check ==",
        "PASS: no TODO[source] markers found.",
        "NOTE: review claim-boundary hits.",
    ]


def test_split_policy_historical_allowance():
    assert line_allowed("The older Salt2 train / Salt3 validation / Salt4 holdout split is superseded.")
    assert not line_allowed("Use Salt2 train / Salt3 validation / Salt4 holdout.")


def test_case_schema_lint_detects_contract(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "README.md").write_text(
        """
BC source role table and material geometry rows.
Patch heat ledger, pressure ladder, thermal score, sensor target.
Runtime input audit, PM5 F6 internal Nu, admission table.
""",
        encoding="utf-8",
    )
    assert _hits(package) == {
        "bc_source_roles",
        "material_geometry",
        "patchwise_heat_ledger",
        "pressure_ladder",
        "thermal_score_rows",
        "sensor_targets",
        "runtime_input_audit",
        "pm5_f6_internal_nu",
        "admission_table",
    }


def test_runtime_input_lint_allows_guardrail_language():
    assert SAFE_CONTEXT_RE.search("Predictive artifacts must not use CFD mdot as runtime inputs.")


def test_finish_task_documentation_validators(tmp_path: Path):
    status = tmp_path / "status.md"
    status.write_text(
        """
# Status

## Changes Made

changed files

## Validation

tests passed

## Guardrails

no native mutation
""",
        encoding="utf-8",
    )
    journal = tmp_path / "journal.md"
    journal.write_text(
        """
# Journal
Task AGENT-999

Observed facts.
Interpretation.
Caveats.
Next actions.
Validation notes.
""",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
{
  "changed_files": ["AGENTS.md"],
  "read_only_context": [".agent/BOARD.md"],
  "native_solver_outputs_mutated": false,
  "registry_mutated": false,
  "scheduler_action": false,
  "external_fluid_edit": false
}
""",
        encoding="utf-8",
    )
    assert _validate_status_doc(status) == []
    assert _validate_journal_doc(journal, "AGENT-999") == []
    assert _validate_manifest(manifest) == []


def test_finish_task_rejects_incomplete_manifest(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"changed_files": []}\n', encoding="utf-8")
    errors = _validate_manifest(manifest)
    assert any("read_only_context" in err for err in errors)
    assert any("changed_files must not be empty" in err for err in errors)


def test_finish_task_artifact_matching_requires_declared_task(tmp_path: Path):
    declared = tmp_path / "declared.md"
    declared.write_text("---\ntask: AGENT-999\n---\nMentions AGENT-123.\n", encoding="utf-8")
    incidental = tmp_path / "incidental.md"
    incidental.write_text("This mentions AGENT-999 but belongs elsewhere.\n", encoding="utf-8")
    assert _doc_declares_task(declared, "AGENT-999")
    assert not _doc_declares_task(incidental, "AGENT-999")


def test_source_property_gate_passes_complete_labeled_candidate(tmp_path: Path):
    scorecard = tmp_path / "candidate_scorecard.csv"
    scorecard.write_text(
        "\n".join(
            [
                "fit_allowed,property_mode,property_sensitivity_label,source_validity_envelope_status,source_use_category,provenance_author_title,source_property_gate_status",
                "yes,P1,nominal,inside_source_envelope,fit_evidence,Author Title,pass_source_property_labels_available",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = audit_paths([scorecard])
    assert result["fit_or_admission_candidate_rows"] == 1
    assert result["rows_with_source_property_findings"] == 0
    assert result["allowed_candidate_rows"] == 1


def test_source_property_gate_reports_unlabeled_candidate_failure_modes(tmp_path: Path):
    scorecard = tmp_path / "admission_scorecard.csv"
    scorecard.write_text("admission_status\nadmitted\n", encoding="utf-8")
    result = audit_paths([scorecard])
    assert result["fit_or_admission_candidate_rows"] == 1
    assert result["rows_with_source_property_findings"] == 1
    modes = result["findings"][0]["failure_modes"]
    assert "missing_required_label_column" in modes
    assert "source_property_gate_status_missing" in modes
    assert "candidate_allowed_but_source_property_blocked" in modes


def test_source_property_gate_reports_blocked_label_content(tmp_path: Path):
    scorecard = tmp_path / "fit_decision.csv"
    scorecard.write_text(
        "\n".join(
            [
                "fit_status,property_mode,property_sensitivity_label,source_validity_envelope_status,source_use_category,provenance_author_title,source_property_gate_status",
                "fit,P1,source_property_refresh_required,mixed_or_outside_envelope_label_required,diagnostic_gate,Author Title,pass_source_property_labels_available",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = audit_paths([scorecard])
    modes = result["findings"][0]["failure_modes"]
    assert "refresh_required_label_content" in modes
    assert "outside_or_mixed_source_envelope" in modes
    assert "diagnostic_or_no_fit_source_use" in modes


def test_finish_task_warns_for_manifest_scorecard_findings(tmp_path: Path):
    scorecard = tmp_path / "admission_scorecard.csv"
    scorecard.write_text("fit_allowed\nyes\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "changed_files": [str(scorecard)],
                "read_only_context": [],
                "native_solver_outputs_mutated": False,
                "registry_mutated": False,
                "scheduler_action": False,
                "external_fluid_edit": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    warnings = _source_property_gate_warnings(manifest)
    assert warnings
    assert "SOURCE_PROPERTY_GATE_WARNING" in warnings[0]
    assert "missing_required_label_column" in warnings[0]


def test_finish_task_no_scorecard_outputs_suppresses_source_property_warning(tmp_path: Path):
    scorecard = tmp_path / "admission_scorecard.csv"
    scorecard.write_text("fit_allowed\nyes\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "changed_files": [str(scorecard)],
                "read_only_context": [],
                "native_solver_outputs_mutated": False,
                "registry_mutated": False,
                "scheduler_action": False,
                "external_fluid_edit": False,
                "no_scorecard_outputs": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert _source_property_gate_warnings(manifest) == []
