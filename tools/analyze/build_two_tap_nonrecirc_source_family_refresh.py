#!/usr/bin/env python3
"""Refresh source-family readiness for the two-tap nonrecirculating anchor."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-TWO-TAP-NONRECIRC-SOURCE-FAMILY-REFRESH"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_source_family_refresh"
ANCHOR_PLAN = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan"
STAGING = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_f6_two_tap_nonrecirc_staging"
LAUNCH = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_same_qoi_anchor_launch_package"
HIGH_HEAT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_high_heat_status_refresh"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-TWO-TAP-NONRECIRC-SOURCE-FAMILY-REFRESH.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/two-tap-nonrecirc-source-family-refresh.md"
IMPORT = ROOT / "imports/2026-07-20_two_tap_nonrecirc_source_family_refresh.json"

ENDPOINT_PAIR = "lower_leg__s04->right_leg__s00"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    required = [
        ANCHOR_PLAN / "source_case_selection.csv",
        STAGING / "source_case_selection.csv",
        LAUNCH / "staged_copy_case_request.csv",
        HIGH_HEAT / "updated_live_job_status.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing two-tap source-family refresh sources: " + "; ".join(missing))


def high_heat_running_or_terminal() -> tuple[int, int]:
    rows = read_csv(HIGH_HEAT / "updated_live_job_status.csv")
    running = sum(row["scheduler_state"].startswith("RUNNING") for row in rows)
    terminal = sum(row["scheduler_state"] in {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED"} for row in rows)
    return running, terminal


def build_source_family_readiness() -> list[dict[str, Any]]:
    anchor = {row["candidate_id"]: row for row in read_csv(ANCHOR_PLAN / "source_case_selection.csv")}
    staging = {row["candidate_id"]: row for row in read_csv(STAGING / "source_case_selection.csv")}
    running, terminal = high_heat_running_or_terminal()
    rows = []
    for candidate_id in ("CAND-001", "CAND-002", "CAND-003"):
        anchor_row = anchor[candidate_id]
        staging_row = staging[candidate_id]
        if candidate_id == "CAND-001":
            readiness = "terminal_gated_running" if running else "terminal_review_required"
            source_family = staging_row["source_family"]
        elif candidate_id == "CAND-002":
            readiness = "fallback_hold_until_CAND_001_fails_terminal_review"
            source_family = staging_row["source_family"]
        else:
            readiness = "deferred_no_source_case"
            source_family = staging_row["source_family"]
        rows.append(
            {
                "candidate_id": candidate_id,
                "request_id": anchor_row["request_id"],
                "source_family": source_family,
                "selection_status": anchor_row.get("selection_status", staging_row.get("current_state", "")),
                "readiness_status": readiness,
                "launch_allowed_now": "false",
                "high_heat_running_jobs": running,
                "high_heat_terminal_jobs": terminal,
                "fallback": anchor_row["fallback"],
            }
        )
    return rows


def build_candidate_source_case_gate(readiness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "endpoint_pair": ENDPOINT_PAIR,
            "source_case_gate": "blocked_terminal_gated" if row["candidate_id"] == "CAND-001" else "blocked_fallback_or_deferred",
            "required_before_launch": "terminal_success;low_reverse_RAF_RMF;finite_pressure_velocity;fresh_staged_copy_sampler_row",
            "auto_submit": "false",
        }
        for row in readiness
    ]


def build_same_qoi_sampler_launch_gate(readiness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "same_qoi_sampler_launch",
            "preferred_candidate": "CAND-001",
            "launch_status": "blocked",
            "endpoint_pair": ENDPOINT_PAIR,
            "pressure_basis": "static_p_pa_primary_with_p_rgh_cross_check",
            "same_qoi_requirements": "Delta_p;K_app;RAF;RMF same formula/sign/window;time UQ;mesh UQ where available",
            "no_make_positive_correction": "true",
        }
    ]


def build_fallback_decision(readiness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "two_tap_nonrecirc_fallback",
            "current_preferred": "CAND-001",
            "fallback_now": "none",
            "fallback_condition": "CAND-001 terminal review fails to provide low-reverse same-topology source",
            "component_k_status": "blocked_current_rows_diagnostic_only",
            "current_rows_use": "apparent_cluster_loss_only",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (ANCHOR_PLAN / "source_case_selection.csv", "anchor plan source selection"),
        (STAGING / "source_case_selection.csv", "staging source selection"),
        (LAUNCH / "staged_copy_case_request.csv", "current launch block"),
        (HIGH_HEAT / "updated_live_job_status.csv", "high-heat live status"),
    ]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# Two-Tap Nonrecirculating Source-Family Refresh\n\nPreferred candidate: CAND-001. Launch allowed now: {summary['launch_allowed_now']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- launch_allowed_now: {summary['launch_allowed_now']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} two-tap source-family refresh\n\nMerged source-family readiness for two-tap nonrecirculating anchor.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    readiness = build_source_family_readiness()
    source_gate = build_candidate_source_case_gate(readiness)
    sampler_gate = build_same_qoi_sampler_launch_gate(readiness)
    fallback = build_fallback_decision(readiness)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "preferred_candidate": "CAND-001",
        "launch_allowed_now": False,
        "auto_submit": False,
        "cand_001_status": next(row["readiness_status"] for row in readiness if row["candidate_id"] == "CAND-001"),
        "component_k_current_status": "blocked_current_rows_diagnostic_only",
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "source_family_readiness.csv", readiness)
    write_csv(OUT / "candidate_source_case_gate.csv", source_gate)
    write_csv(OUT / "same_qoi_sampler_launch_gate.csv", sampler_gate)
    write_csv(OUT / "fallback_decision.csv", fallback)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
