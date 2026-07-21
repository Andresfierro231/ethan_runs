#!/usr/bin/env python3
"""Build AGENT-505 F6 anchor-first refinement package."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-505"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement"

F6_RECORRECTION = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_recorrection_resolution_plan"
PM10_READINESS = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness"
HIGH_HEAT_MONITOR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"
ANCHOR_STUDY = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"

F6_GATE = F6_RECORRECTION / "f6_row_gate_matrix.csv"
F6_SCORECARD = F6_RECORRECTION / "f6_resolution_scorecard.csv"
F6_QUEUE = F6_RECORRECTION / "f6_next_action_queue.csv"
F6_SUMMARY = F6_RECORRECTION / "summary.json"
PM10_CASES = PM10_READINESS / "pm10_case_readiness.csv"
PM10_SUMMARY = PM10_READINESS / "summary.json"
HIGH_HEAT_QUEUE = HIGH_HEAT_MONITOR / "harvest_readiness_queue.csv"
ANCHOR_MATRIX = ANCHOR_STUDY / "proposed_cfd_run_matrix.csv"

LOW_REVERSE_LIMIT = 0.01
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"}

SOURCES = {
    "f6_gate_matrix": (F6_GATE, "current PM5 row-level F6 gates"),
    "f6_scorecard": (F6_SCORECARD, "current F6 vs F3 decision scorecard"),
    "f6_next_action_queue": (F6_QUEUE, "current narrowed F6 evidence queue"),
    "f6_summary": (F6_SUMMARY, "current F6 recorrection summary"),
    "pm10_case_readiness": (PM10_CASES, "recorded PM10 terminal readiness"),
    "pm10_summary": (PM10_SUMMARY, "recorded PM10 readiness summary"),
    "high_heat_harvest_queue": (HIGH_HEAT_QUEUE, "recorded high-heat harvest readiness"),
    "recirculation_anchor_matrix": (ANCHOR_MATRIX, "Salt3 Q x insulation onset matrix"),
}

TERMINAL_COLUMNS = [
    "evidence_family",
    "case_key",
    "case_role",
    "source_job_ids",
    "recorded_state",
    "live_state",
    "terminal_status",
    "harvest_readiness",
    "readiness_reason",
    "next_action",
    "source_path",
]

ANCHOR_COLUMNS = [
    "row_id",
    "evidence_family",
    "case_key",
    "lane",
    "RAF",
    "RMF",
    "pressure_evidence",
    "reverse_flow_gate",
    "scoreable_now",
    "promotion_allowed",
    "source_status",
    "primary_blocker",
    "next_action",
    "source_path",
]

LANE_COLUMNS = [
    "lane",
    "current_rows",
    "scoreable_rows",
    "promotion_allowed",
    "production_baseline",
    "status",
    "stop_go_gate",
    "next_action",
]

PRESSURE_COLUMNS = [
    "model_or_evidence",
    "evidence_family",
    "candidate_rows",
    "pressure_residual_status",
    "validation_holdout_status",
    "decision",
    "reason",
]

NEXT_CFD_COLUMNS = [
    "recommended_order",
    "case_key",
    "study_group",
    "target_regime",
    "target_heater_power_W",
    "insulation_mode",
    "launch_decision",
    "precondition",
    "required_outputs",
    "scientific_use",
    "source_path",
]

MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({key: "" if row.get(key) is None else str(row.get(key, "")) for key in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def require_sources() -> None:
    missing = [rel(path) for path, _role in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-505 source files: " + ", ".join(missing))


def run_command(args: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=20)
    except Exception as exc:  # pragma: no cover - depends on scheduler environment
        return 127, f"{type(exc).__name__}: {exc}"
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def query_live_job_states(job_ids: Iterable[str], live_scheduler: bool) -> dict[str, str]:
    unique_ids = sorted({job_id for job_id in job_ids if job_id})
    if not live_scheduler:
        return {job_id: "not_requested" for job_id in unique_ids}

    states: dict[str, str] = {}
    for job_id in unique_ids:
        sacct_code, sacct_out = run_command(["sacct", "-j", job_id, "--format=JobID,State", "-P", "-n"])
        parsed_state = ""
        if sacct_code == 0 and sacct_out:
            for line in sacct_out.splitlines():
                fields = line.split("|")
                if fields and fields[0] == job_id and len(fields) > 1:
                    parsed_state = fields[1].split()[0]
                    break
        if parsed_state:
            states[job_id] = parsed_state
            continue

        squeue_code, squeue_out = run_command(["squeue", "-j", job_id, "-h", "-o", "%T"])
        if squeue_code == 0 and squeue_out:
            states[job_id] = squeue_out.splitlines()[0].strip().split()[0]
        else:
            states[job_id] = f"unknown_or_not_in_queue:sacct={sacct_code};squeue={squeue_code}"
    return states


def live_state_for(job_ids: list[str], live_states: dict[str, str]) -> str:
    return ";".join(f"{job_id}={live_states.get(job_id, 'not_requested')}" for job_id in job_ids if job_id)


def terminal_from_states(job_ids: list[str], live_states: dict[str, str], recorded_nonterminal: bool) -> str:
    states = [live_states.get(job_id, "not_requested") for job_id in job_ids if job_id]
    if not states or all(state == "not_requested" for state in states):
        return "recorded_nonterminal" if recorded_nonterminal else "recorded_ready_or_terminal"
    normalized = [state.split(":")[0] for state in states]
    if all(state in TERMINAL_STATES for state in normalized):
        return "live_terminal_unadmitted"
    if any(state in {"RUNNING", "PENDING", "CONFIGURING", "COMPLETING"} for state in normalized):
        return "live_nonterminal"
    return "live_unknown_check_before_harvest"


def build_terminal_rows(
    pm10_rows: list[dict[str, str]],
    high_heat_rows: list[dict[str, str]],
    live_states: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in pm10_rows:
        job_ids = [row.get("solver_job_id", ""), row.get("harvest_job_id", "")]
        recorded_nonterminal = row.get("readiness_state") != "ready_for_terminal_admission"
        terminal_status = terminal_from_states(job_ids, live_states, recorded_nonterminal)
        rows.append(
            {
                "evidence_family": "PM10",
                "case_key": row.get("case_key", ""),
                "case_role": row.get("split_role", ""),
                "source_job_ids": ";".join(job_id for job_id in job_ids if job_id),
                "recorded_state": f"solver={row.get('solver_state', '')};harvest={row.get('harvest_state', '')}",
                "live_state": live_state_for(job_ids, live_states),
                "terminal_status": terminal_status,
                "harvest_readiness": row.get("readiness_state", ""),
                "readiness_reason": row.get("next_action", ""),
                "next_action": "claim terminal PM10 postprocessing task only after solver/harvest are terminal",
                "source_path": rel(PM10_CASES),
            }
        )

    for row in high_heat_rows:
        job_ids = [row.get("job_id", "")]
        recorded_nonterminal = row.get("harvest_readiness") != "harvest_ready"
        terminal_status = terminal_from_states(job_ids, live_states, recorded_nonterminal)
        rows.append(
            {
                "evidence_family": "high_heat",
                "case_key": row.get("case_key", ""),
                "case_role": "candidate_anchor",
                "source_job_ids": ";".join(job_id for job_id in job_ids if job_id),
                "recorded_state": row.get("scheduler_state", ""),
                "live_state": live_state_for(job_ids, live_states),
                "terminal_status": terminal_status,
                "harvest_readiness": row.get("harvest_readiness", ""),
                "readiness_reason": row.get("note", ""),
                "next_action": "if terminal, claim high-heat harvest task and test RAF/RMF anchor gate",
                "source_path": rel(HIGH_HEAT_QUEUE),
            }
        )
    return rows


def low_reverse_gate(raf: str | None, rmf: str | None) -> bool:
    raf_value = as_float(raf)
    rmf_value = as_float(rmf)
    return (
        raf_value is not None
        and rmf_value is not None
        and raf_value < LOW_REVERSE_LIMIT
        and rmf_value < LOW_REVERSE_LIMIT
    )


def build_anchor_gate_rows(
    pm5_rows: list[dict[str, str]],
    pm10_rows: list[dict[str, str]],
    high_heat_rows: list[dict[str, str]],
    terminal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    terminal_by_case = {row["case_key"]: row for row in terminal_rows}

    for row in pm5_rows:
        passes_low_reverse = low_reverse_gate(row.get("RAF"), row.get("RMF"))
        lane = "ordinary_F6_anchor" if passes_low_reverse else "recirculation_diagnostic"
        rows.append(
            {
                "row_id": row.get("row_id", ""),
                "evidence_family": "PM5",
                "case_key": row.get("case_key", ""),
                "lane": lane,
                "RAF": row.get("RAF", ""),
                "RMF": row.get("RMF", ""),
                "pressure_evidence": row.get("pressure_status", ""),
                "reverse_flow_gate": "pass_low_reverse" if passes_low_reverse else "fail_material_reverse_flow",
                "scoreable_now": "no",
                "promotion_allowed": "no",
                "source_status": row.get("lane_classification", ""),
                "primary_blocker": row.get("primary_blocker", ""),
                "next_action": "do not fit ordinary F6 from PM5; use only as diagnostic/onset evidence",
                "source_path": row.get("source_path", rel(F6_GATE)),
            }
        )

    for row in pm10_rows:
        terminal = terminal_by_case.get(row.get("case_key", ""), {})
        rows.append(
            {
                "row_id": f"pm10:{row.get('case_key', '')}",
                "evidence_family": "PM10",
                "case_key": row.get("case_key", ""),
                "lane": "blocked_pending_terminal",
                "RAF": "",
                "RMF": "",
                "pressure_evidence": "not_postprocessed_in_this_package",
                "reverse_flow_gate": "not_evaluated_pending_terminal_harvest",
                "scoreable_now": "no",
                "promotion_allowed": "no",
                "source_status": terminal.get("terminal_status", row.get("readiness_state", "")),
                "primary_blocker": "terminal_harvest_and_pm5_style_postprocessing_missing",
                "next_action": "wait for terminal then run full output-contract postprocessing",
                "source_path": rel(PM10_CASES),
            }
        )

    for row in high_heat_rows:
        terminal = terminal_by_case.get(row.get("case_key", ""), {})
        rows.append(
            {
                "row_id": f"high_heat:{row.get('case_key', '')}",
                "evidence_family": "high_heat",
                "case_key": row.get("case_key", ""),
                "lane": "blocked_pending_terminal",
                "RAF": "",
                "RMF": "",
                "pressure_evidence": "not_harvested_in_this_package",
                "reverse_flow_gate": "not_evaluated_pending_terminal_harvest",
                "scoreable_now": "no",
                "promotion_allowed": "no",
                "source_status": terminal.get("terminal_status", row.get("harvest_readiness", "")),
                "primary_blocker": "terminal_harvest_missing",
                "next_action": "harvest after terminal and test ordinary anchor gate first",
                "source_path": rel(HIGH_HEAT_QUEUE),
            }
        )
    return rows


def build_lane_decisions(anchor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["lane"] for row in anchor_rows)
    return [
        {
            "lane": "ordinary_F6_anchor",
            "current_rows": counts.get("ordinary_F6_anchor", 0),
            "scoreable_rows": 0,
            "promotion_allowed": "no",
            "production_baseline": "F3_shah_apparent",
            "status": "no_current_low_reverse_pressure_anchor",
            "stop_go_gate": "RAF < 0.01, RMF < 0.01, same-window pressure loss, split-safe score over F3",
            "next_action": "terminal high-heat harvest first; ordinary F6 only if low-reverse gate passes",
        },
        {
            "lane": "transition_anchor",
            "current_rows": 0,
            "scoreable_rows": 0,
            "promotion_allowed": "no",
            "production_baseline": "F3_shah_apparent",
            "status": "not_yet_bracketed",
            "stop_go_gate": "paired low-reverse and material-recirculation rows with same output contract",
            "next_action": "use Salt3 Q x insulation matrix only if terminal high-heat/PM10 evidence remains insufficient",
        },
        {
            "lane": "recirculation_diagnostic",
            "current_rows": counts.get("recirculation_diagnostic", 0),
            "scoreable_rows": 0,
            "promotion_allowed": "no",
            "production_baseline": "F3_shah_apparent",
            "status": "diagnostic_only",
            "stop_go_gate": "named closure plus pressure residual movement, Delta T, Gz, UQ, validation/holdout improvement",
            "next_action": "do not fit ordinary friction; preserve as onset/regime evidence",
        },
        {
            "lane": "blocked_pending_terminal",
            "current_rows": counts.get("blocked_pending_terminal", 0),
            "scoreable_rows": 0,
            "promotion_allowed": "no",
            "production_baseline": "F3_shah_apparent",
            "status": "waiting_for_terminal_or_harvest",
            "stop_go_gate": "terminal jobs plus PM5-style scratch-copy postprocessing",
            "next_action": "monitor/harvest in separately claimed task",
        },
    ]


def build_pressure_scorecard(anchor_rows: list[dict[str, Any]], terminal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["lane"] for row in anchor_rows)
    blocked_or_unknown = sum(
        1
        for row in terminal_rows
        if row.get("terminal_status") not in {"live_terminal_unadmitted", "recorded_ready_or_terminal"}
    )
    return [
        {
            "model_or_evidence": "F3_shah_apparent",
            "evidence_family": "production_baseline",
            "candidate_rows": "",
            "pressure_residual_status": "baseline_to_beat",
            "validation_holdout_status": "current_production",
            "decision": "keep",
            "reason": "No F6 lane has passed admission or shown split-safe residual improvement.",
        },
        {
            "model_or_evidence": "ordinary_F6_single_stream",
            "evidence_family": "PM5/current",
            "candidate_rows": counts.get("ordinary_F6_anchor", 0),
            "pressure_residual_status": "not_scoreable_zero_low_reverse_anchors",
            "validation_holdout_status": "not_scoreable",
            "decision": "do_not_promote",
            "reason": "Ordinary F6 requires non-recirculating pressure anchors; current PM5 rows fail reverse-flow gates.",
        },
        {
            "model_or_evidence": "recirculation_modeled_closure",
            "evidence_family": "PM5/current",
            "candidate_rows": counts.get("recirculation_diagnostic", 0),
            "pressure_residual_status": "missing_explicit_residual_movement",
            "validation_holdout_status": "not_scoreable_missing_features_and_UQ",
            "decision": "do_not_promote",
            "reason": "Material recirculation rows may inform a named closure later, but lack residual, thermal, and uncertainty evidence.",
        },
        {
            "model_or_evidence": "PM10_and_high_heat_follow_on",
            "evidence_family": "future_harvest",
            "candidate_rows": counts.get("blocked_pending_terminal", 0),
            "pressure_residual_status": f"blocked_or_unknown_pending_harvest_rows={blocked_or_unknown}",
            "validation_holdout_status": "not_admitted",
            "decision": "wait",
            "reason": "Terminal harvest and full output-contract postprocessing must precede scoring.",
        },
    ]


def build_next_cfd_rows(anchor_matrix: list[dict[str, str]]) -> list[dict[str, Any]]:
    priority_rank = {"sentinel_cell_off": 10, "sentinel_cell_max": 20, "small_q_x_insulation_matrix": 30}
    rows = []
    for row in sorted(
        anchor_matrix,
        key=lambda item: (
            priority_rank.get(item.get("study_group", ""), 99),
            as_float(item.get("target_heater_power_W")) or 0.0,
            item.get("insulation_mode", ""),
        ),
    ):
        study_group = row.get("study_group", "")
        if study_group.startswith("sentinel"):
            launch_decision = "next_if_current_terminal_evidence_insufficient"
        else:
            launch_decision = "launch_after_sentinel_gap_confirmed"
        rows.append(
            {
                "recommended_order": len(rows) + 1,
                "case_key": row.get("case_key", ""),
                "study_group": study_group,
                "target_regime": row.get("target_regime", ""),
                "target_heater_power_W": row.get("target_heater_power_W", ""),
                "insulation_mode": row.get("insulation_mode", ""),
                "launch_decision": launch_decision,
                "precondition": "after PM10/high-heat terminal harvest or explicit evidence gap",
                "required_outputs": "U;T;wallHeatFlux;Re/Pr/Ri/Gr/Ra/Gz;wall-core DeltaT;RAF/RMF/SVF;secondary velocity;steady-window;mesh/time UQ",
                "scientific_use": row.get("scientific_use", ""),
                "source_path": rel(ANCHOR_MATRIX),
            }
        )
    return rows


def build_manifest() -> list[dict[str, Any]]:
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "role": role,
        }
        for source_id, (path, role) in SOURCES.items()
    ]


def write_readme(path: Path, generated_at: str, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(F6_GATE)}
  - {rel(PM10_CASES)}
  - {rel(HIGH_HEAT_QUEUE)}
  - {rel(ANCHOR_MATRIX)}
tags: [f6, friction, recirculation, anchor-first]
related:
  - .agent/status/2026-07-17_AGENT-505.md
  - .agent/journal/2026-07-17/f6-anchor-first-refinement.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Anchor-First Refinement

Generated: `{generated_at}`

## Decision

This package keeps the F6 avenue open but does not promote a new closure.
The next research move is anchor-first: terminal high-heat and PM10 evidence
must be harvested and gated before ordinary F6 or a named recirculation closure
can be scored.

## Current Counts

- PM5 rows reviewed: `{summary["pm5_rows"]}`.
- PM5 ordinary anchor rows: `{summary["pm5_ordinary_anchor_rows"]}`.
- PM5 recirculation diagnostic rows: `{summary["pm5_recirculation_diagnostic_rows"]}`.
- PM10/high-heat blocked rows: `{summary["blocked_pending_terminal_rows"]}`.
- Recommended Salt3 CFD rows if evidence remains insufficient: `{summary["recommended_next_cfd_rows"]}`.
- Production closure: `{summary["production_closure"]}`.
- Promotion allowed now: `{summary["promotion_allowed"]}`.

## Outputs

- `terminal_status_refresh.csv`
- `anchor_gate_table.csv`
- `f6_lane_decision.csv`
- `pressure_residual_scorecard.csv`
- `recommended_next_cfd_runs.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, blocker register, generated index files, or active-agent scopes
were mutated. Optional live scheduler checks are read-only and do not replace a
separately claimed terminal harvest task.
""",
        encoding="utf-8",
    )


def build_package(out_dir: Path = OUT, live_scheduler: bool = False) -> dict[str, Any]:
    require_sources()
    generated_at = utc_now()
    out_dir.mkdir(parents=True, exist_ok=True)

    pm5_rows = read_csv(F6_GATE)
    pm10_rows = read_csv(PM10_CASES)
    high_heat_rows = read_csv(HIGH_HEAT_QUEUE)
    anchor_matrix = read_csv(ANCHOR_MATRIX)
    f6_summary = read_json(F6_SUMMARY)
    pm10_summary = read_json(PM10_SUMMARY)

    job_ids = []
    for row in pm10_rows:
        job_ids.extend([row.get("solver_job_id", ""), row.get("harvest_job_id", "")])
    for row in high_heat_rows:
        job_ids.append(row.get("job_id", ""))
    live_states = query_live_job_states(job_ids, live_scheduler)

    terminal_rows = build_terminal_rows(pm10_rows, high_heat_rows, live_states)
    anchor_rows = build_anchor_gate_rows(pm5_rows, pm10_rows, high_heat_rows, terminal_rows)
    lane_rows = build_lane_decisions(anchor_rows)
    pressure_rows = build_pressure_scorecard(anchor_rows, terminal_rows)
    next_cfd_rows = build_next_cfd_rows(anchor_matrix)
    manifest_rows = build_manifest()

    write_csv(out_dir / "terminal_status_refresh.csv", terminal_rows, TERMINAL_COLUMNS)
    write_csv(out_dir / "anchor_gate_table.csv", anchor_rows, ANCHOR_COLUMNS)
    write_csv(out_dir / "f6_lane_decision.csv", lane_rows, LANE_COLUMNS)
    write_csv(out_dir / "pressure_residual_scorecard.csv", pressure_rows, PRESSURE_COLUMNS)
    write_csv(out_dir / "recommended_next_cfd_runs.csv", next_cfd_rows, NEXT_CFD_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", manifest_rows, MANIFEST_COLUMNS)

    anchor_counts = Counter(row["lane"] for row in anchor_rows)
    terminal_counts = Counter(row["terminal_status"] for row in terminal_rows)
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": generated_at,
        "output_dir": rel(out_dir),
        "live_scheduler_requested": live_scheduler,
        "live_scheduler_states": live_states,
        "pm5_rows": f6_summary.get("pm5_rows", len(pm5_rows)),
        "pm5_ordinary_anchor_rows": anchor_counts.get("ordinary_F6_anchor", 0),
        "pm5_recirculation_diagnostic_rows": anchor_counts.get("recirculation_diagnostic", 0),
        "blocked_pending_terminal_rows": anchor_counts.get("blocked_pending_terminal", 0),
        "terminal_status_counts": dict(terminal_counts),
        "pm10_ready_cases_recorded": pm10_summary.get("ready_for_terminal_admission_count", 0),
        "recommended_next_cfd_rows": len(next_cfd_rows),
        "production_closure": "F3_shah_apparent",
        "promotion_allowed": "no",
        "ordinary_f6_scoreable_rows": 0,
        "hybrid_scoreable_rows": 0,
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "read_only_status_check" if live_scheduler else "none_recorded_status_only",
        "scientific_admission_change": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir / "README.md", generated_at, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--live-scheduler", action="store_true", help="Add read-only sacct/squeue job state observations.")
    args = parser.parse_args()
    summary = build_package(args.out_dir, live_scheduler=args.live_scheduler)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
