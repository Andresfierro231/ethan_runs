#!/usr/bin/env python3
"""Build the daily and gate-triggered table update contract.

This package implements the documentation cadence from the July 14 execution
plan. It does not change blocker state or scientific admissions; it defines the
tables that must be refreshed when other agents land gate-moving results.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "AGENT-325"
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_table_update_cadence_contract"
BOARD = ROOT / ".agent/BOARD.md"
BLOCKERS = ROOT / ".agent/BLOCKERS.md"


TABLE_CONTRACTS = [
    {
        "table_id": "T01",
        "table_name": "blocker_register_and_generated_blockers",
        "primary_files": ".agent/blockers.yml;.agent/BLOCKERS.md",
        "owner_lane": "coordinator",
        "cadence": "daily_check_plus_gate_trigger",
        "gate_triggers": "blocker_added;blocker_resolved;blocker_superseded;blocker_narrowed",
        "required_update": "Edit blocker register when scoped, regenerate index files, and cite evidence path plus review date.",
        "max_lag": "same_day_for_gate;daily_no_gate_note_allowed",
        "overclaim_guard": "Do not re-open superseded blockers or resolve blockers from smoke evidence alone.",
    },
    {
        "table_id": "T02",
        "table_name": "thermal_admission_and_mesh_gci_tables",
        "primary_files": "thermal_admission_table.csv;thermal_mesh_gate_qois.csv;mesh map",
        "owner_lane": "internal-Nu / therm-reconstr",
        "cadence": "gate_triggered_plus_daily_check",
        "gate_triggers": "thermal_sign_review;heat_balance_review;lower_leg_nu_policy;downcomer_policy;gci_rerun",
        "required_update": "Record fit-admissible, validation-only, diagnostic-only, or blocked status for every QOI row.",
        "max_lag": "same_day_for_gate",
        "overclaim_guard": "No GCI for two-level, source-blocked, non-monotone, oscillatory, divergent, or invalid-order rows.",
    },
    {
        "table_id": "T03",
        "table_name": "forward_model_scorecards",
        "primary_files": "forward_v1_scorecard.csv;residual_attribution.csv;summary.json",
        "owner_lane": "forward-pred",
        "cadence": "gate_triggered_plus_daily_check",
        "gate_triggers": "hydraulic_model_changed;boundary_model_changed;sensor_policy_changed;split_changed",
        "required_update": "Report train, validation, and holdout rows with residual lanes separated.",
        "max_lag": "same_day_for_gate",
        "overclaim_guard": "No runtime CFD mdot, realized CFD wallHeatFlux, or validation temperatures in predictive rows.",
    },
    {
        "table_id": "T04",
        "table_name": "boundary_hx_wall_radiation_decision_tables",
        "primary_files": "boundary_model_decision_table.csv;setup_only_boundary_scorecard.csv",
        "owner_lane": "BC-modeling",
        "cadence": "gate_triggered_plus_daily_check",
        "gate_triggers": "heater_model_candidate;cooler_model_candidate;wall_layer_api;external_bc_api;radiation_semantics_change",
        "required_update": "State setup inputs, fitted parameters, validation status, and residual attribution.",
        "max_lag": "same_day_for_gate",
        "overclaim_guard": "Do not double-count radiation already embedded in CFD wallHeatFlux.",
    },
    {
        "table_id": "T05",
        "table_name": "hydraulic_closure_and_friction_tables",
        "primary_files": "h1_scorecard.csv;f6_screen.csv;pressure_momentum_map",
        "owner_lane": "hydraulics",
        "cadence": "gate_triggered_plus_daily_check",
        "gate_triggers": "localized_h1_result;f6_screen_result;pressure_fit_policy;recirculation_policy",
        "required_update": "Separate straight friction, component-K, cluster-K, branch-apparent, reset, and recirculation terms.",
        "max_lag": "same_day_for_gate",
        "overclaim_guard": "Do not hide named losses or reset/development inside a global friction multiplier.",
    },
    {
        "table_id": "T06",
        "table_name": "case_run_admission_inventory",
        "primary_files": "corrected_salt_q_admission_inventory.csv;cfd_runs_and_admission_map",
        "owner_lane": "cfd-pp",
        "cadence": "daily_check_plus_terminal_gate",
        "gate_triggers": "slurm_terminal;post_exit_harvest;steadiness_gate;bc_label_complete",
        "required_update": "Admit no rows from Slurm completion alone; require terminal solver evidence, steadiness, BC labels, and provenance.",
        "max_lag": "same_day_after_terminal_harvest",
        "overclaim_guard": "Perturbation rows remain sensitivity/correlation-support unless explicitly admitted.",
    },
    {
        "table_id": "T07",
        "table_name": "math_theory_assumptions_results_register",
        "primary_files": "equation_register.csv;assumption_register.csv;result_intake_contract.csv",
        "owner_lane": "methodology / thesis-pres-docs",
        "cadence": "daily_check_plus_gate_trigger",
        "gate_triggers": "new_equation;assumption_changed;result_contract_changed;new_negative_evidence",
        "required_update": "Every gate-moving package cites equation IDs, assumptions, units, split role, and evidence class.",
        "max_lag": "same_day_for_gate",
        "overclaim_guard": "Diagnostic, calibrated, predictive, reference-only, rejected, and blocked evidence must not be mixed.",
    },
    {
        "table_id": "T08",
        "table_name": "thesis_presentation_claim_ledger",
        "primary_files": "reports/thesis_dossier;presentation update notes",
        "owner_lane": "thesis-pres-docs",
        "cadence": "daily_check_plus_story_change",
        "gate_triggers": "blocker_state_changed;scorecard_changed;admission_changed;weekly_meeting_story_changed",
        "required_update": "State what changed, what is trustworthy, what remains blocked, and what to show next meeting.",
        "max_lag": "same_day_for_story_change",
        "overclaim_guard": "Resolved blockers stay out of the narrative.",
    },
]


GATE_MATRIX = [
    {
        "gate_event": "daily_no_gate_refresh",
        "detector": "calendar day or session closeout",
        "tables_to_check": "T01;T02;T03;T04;T05;T06;T07;T08",
        "required_action": "Record no-gate-change status if no blocker, admission, scorecard, or story state changed.",
        "closeout_required": "status_or_journal_note",
    },
    {
        "gate_event": "blocker_state_changed",
        "detector": "blocker register diff or package decision",
        "tables_to_check": "T01;T08",
        "required_action": "Update blocker register, generated blocker table when scoped, and thesis claim wording.",
        "closeout_required": "status;journal;import;index_refresh_if_scoped",
    },
    {
        "gate_event": "admission_class_changed",
        "detector": "fit/validation/diagnostic/blocked status differs from prior package",
        "tables_to_check": "T02;T06;T08",
        "required_action": "Update admission inventory and state source evidence for each changed row.",
        "closeout_required": "package_readme;status;journal;import",
    },
    {
        "gate_event": "scorecard_changed",
        "detector": "new train/validation/holdout scores or residual attribution",
        "tables_to_check": "T03;T05;T08",
        "required_action": "Refresh scorecard and state whether rows are predictive, proxy, diagnostic, or blocked.",
        "closeout_required": "package_readme;status;journal;import",
    },
    {
        "gate_event": "boundary_model_changed",
        "detector": "heater, cooler, wall-layer, external-BC, or radiation model decision/result",
        "tables_to_check": "T03;T04;T07;T08",
        "required_action": "Record setup inputs, assumptions, equations, residual lanes, and predictive admissibility.",
        "closeout_required": "package_readme;status;journal;import",
    },
    {
        "gate_event": "terminal_cfd_harvest",
        "detector": "Slurm terminal state plus post-exit evidence package",
        "tables_to_check": "T06;T02;T05;T08",
        "required_action": "Run admission gate before downstream fit, validation, or sensitivity use.",
        "closeout_required": "admission_package;status;journal;import",
    },
]


DAILY_CHECKLIST = [
    {
        "step": 1,
        "check": "Read board active rows and status closeouts",
        "pass_condition": "Every in-flight gate-moving row has an owner, scope, and latest status or is flagged stale.",
    },
    {
        "step": 2,
        "check": "Read blocker register",
        "pass_condition": "Open blockers and resolved/superseded blockers match current evidence.",
    },
    {
        "step": 3,
        "check": "Scan latest package summaries",
        "pass_condition": "Any package with changed admission, scorecard, blocker, API, or thesis state is queued for table refresh.",
    },
    {
        "step": 4,
        "check": "Refresh scoped tables",
        "pass_condition": "Only claimed files are edited; active-agent scopes are not touched.",
    },
    {
        "step": 5,
        "check": "Close out",
        "pass_condition": "Status, journal, import manifest, README, and index refresh are complete when scoped.",
    },
]


def write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_board_rows(board_text: str) -> list[dict[str, str]]:
    """Parse markdown task rows from the Active section."""
    rows: list[dict[str, str]] = []
    has_active_heading = "## Active" in board_text
    in_active = not has_active_heading
    for line in board_text.splitlines():
        if line.strip() == "## Active":
            in_active = True
            continue
        if has_active_heading and in_active and line.startswith("## ") and line.strip() != "## Active":
            break
        if not in_active:
            continue
        if not line.startswith("| AGENT-"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 5:
            continue
        task_id, role, owner, scope, goal = parts[:5]
        status_match = re.search(r"STATUS:\s*([^.|]+(?:\.[^|]*)?)", goal)
        status = status_match.group(1).strip() if status_match else "unknown"
        rows.append(
            {
                "task_id": task_id,
                "role": role,
                "owner": owner,
                "status": status,
                "watch_tables": infer_watch_tables(scope + " " + goal),
                "gate_update_reason": infer_gate_reason(status, scope + " " + goal),
            }
        )
    return rows


def infer_watch_tables(text: str) -> str:
    lowered = text.lower()
    tables: list[str] = []
    if any(token in lowered for token in ("blocker", "generated index", "blockers.yml")):
        tables.append("T01")
    if any(token in lowered for token in ("thermal", "nu", "mesh", "gci", "admission")):
        tables.append("T02")
    if any(token in lowered for token in ("scorecard", "forward-v1", "forward model", "h1")):
        tables.append("T03")
    if any(token in lowered for token in ("boundary", "hx", "cooler", "heater", "radiation", "wall-layer")):
        tables.append("T04")
    if any(token in lowered for token in ("hydraulic", "friction", "f6", "localized", "named-loss")):
        tables.append("T05")
    if any(token in lowered for token in ("corrected", "salt-q", "terminal", "slurm")):
        tables.append("T06")
    if any(token in lowered for token in ("math", "theory", "assumption", "equation")):
        tables.append("T07")
    if any(token in lowered for token in ("thesis", "presentation", "mission")):
        tables.append("T08")
    return ";".join(dict.fromkeys(tables)) or "review_required"


def infer_gate_reason(status: str, text: str) -> str:
    status_lower = status.lower()
    lowered = text.lower()
    if status_lower.startswith("complete") and any(token in lowered for token in ("scorecard", "admission", "blocker", "gate")):
        return "completed_gate_candidate_check_outputs"
    if "running" in status_lower:
        return "watch_for_future_gate_result"
    return "daily_watch"


def read_text_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def is_current_watch_row(row: dict[str, str]) -> bool:
    status = row["status"].lower()
    return not status.startswith("complete") or "2026-07-14" in status


def build_summary(out_dir: Path, watch_rows: list[dict[str, str]]) -> dict[str, object]:
    return {
        "task_id": TASK_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "cadence_policy": "daily_plus_gate_triggered",
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "registry_or_admission_state_modified": False,
        "generated_index_refreshed": False,
        "n_table_contracts": len(TABLE_CONTRACTS),
        "n_gate_events": len(GATE_MATRIX),
        "n_daily_steps": len(DAILY_CHECKLIST),
        "n_watch_rows": len(watch_rows),
        "outputs": sorted(path.name for path in out_dir.iterdir() if path.is_file()),
    }


def write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    readme = f"""---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_math_theory_assumptions_results_register/README.md
tags: [table-cadence, coordination, blocker-register, admission, scorecard, thesis-source]
related:
  - .agent/journal/2026-07-14/table-update-cadence-contract.md
  - imports/2026-07-14_table_update_cadence_contract.json
task: {TASK_ID}
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Table Update Cadence Contract

This package implements the daily plus gate-triggered update cadence requested
for the CFD-to-1D closure workflow. It is infrastructure, not a scientific
result: it tells each active lane which tables to refresh when results arrive.

## Cadence

- Daily: run the checklist and record either updates or a no-gate-change note.
- Gate-triggered: update same day when blocker state, admission class,
  scorecard, boundary/API model, terminal CFD harvest, or thesis story changes.

## Outputs

- `table_update_contract.csv`: {summary["n_table_contracts"]} table contracts.
- `gate_trigger_matrix.csv`: {summary["n_gate_events"]} trigger events.
- `daily_refresh_checklist.csv`: {summary["n_daily_steps"]} daily steps.
- `active_result_watchlist.csv`: {summary["n_watch_rows"]} board-derived watch rows.
- `summary.json`: machine-readable metadata.

## Guardrails

- Do not edit active-agent scopes to refresh tables.
- Do not resolve blockers from smoke or diagnostic evidence alone.
- Do not mix predictive, calibrated, diagnostic, reference-only, rejected, and
  blocked evidence in one result row.
- Do not regenerate generated index files unless the board row explicitly claims
  them.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def run_package(out_dir: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    board_text = read_text_or_empty(BOARD)
    watch_rows = [row for row in parse_board_rows(board_text) if is_current_watch_row(row)]
    write_csv(out_dir / "table_update_contract.csv", TABLE_CONTRACTS)
    write_csv(out_dir / "gate_trigger_matrix.csv", GATE_MATRIX)
    write_csv(out_dir / "daily_refresh_checklist.csv", DAILY_CHECKLIST)
    if watch_rows:
        write_csv(out_dir / "active_result_watchlist.csv", watch_rows)
    else:
        write_csv(
            out_dir / "active_result_watchlist.csv",
            [
                {
                    "task_id": "none_found",
                    "role": "",
                    "owner": "",
                    "status": "",
                    "watch_tables": "review_required",
                    "gate_update_reason": "board_parse_empty",
                }
            ],
        )
    summary = build_summary(out_dir, watch_rows)
    write_readme(out_dir, summary)
    summary = build_summary(out_dir, watch_rows)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_package(args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
