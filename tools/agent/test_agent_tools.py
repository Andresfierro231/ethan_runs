#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from tools.agent.background_compute_helper import infer_host_kind, recommend
from tools.agent.case_schema_lint import _hits
from tools.agent.common import active_conflicts, find_task, parse_board
from tools.agent.finish_task import (
    _doc_declares_task,
    _source_property_gate_warnings,
    _validate_journal_doc,
    _validate_manifest,
    _validate_status_doc,
)
from tools.agent.runtime_input_lint import SAFE_CONTEXT_RE
from tools.agent.source_property_gate import audit_paths
from tools.agent.split_policy_lint import line_allowed


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


def test_background_compute_recommendations():
    assert infer_host_kind("login3") == "login"
    assert infer_host_kind("c318-008") == "compute"
    assert recommend("login", "overnight", openfoam=True, persistent=True) == "sbatch"
    assert recommend("compute", "short", openfoam=True, persistent=False) == "srun"


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
