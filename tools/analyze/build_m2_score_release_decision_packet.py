#!/usr/bin/env python3
"""Build an explicit M2 score release decision packet."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-M2-SCORE-RELEASE-DECISION-PACKET"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_score_release_decision_packet"
RESOLUTION = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_salt1_cooler_hx_resolution_package"
READINESS = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_holdout_scoring_readiness"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-M2-SCORE-RELEASE-DECISION-PACKET.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-m2-score-release-decision-packet.md"
IMPORT = ROOT / "imports/2026-07-20_m2_score_release_decision_packet.json"


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
    required = [RESOLUTION / "summary.json", RESOLUTION / "optional_3row_exception_memo.csv", READINESS / "scoring_row_queue.csv"]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M2 score release packet sources: " + "; ".join(missing))


def build_score_release_options() -> list[dict[str, Any]]:
    resolution = read_json(RESOLUTION / "summary.json")
    return [
        {
            "option_id": "default_4row_supported",
            "status": "available" if resolution.get("salt1_cooler_hx_supported") else "blocked",
            "release_condition": "numeric Salt1 cooler/HX projection exists",
            "holdout_score_release": str(bool(resolution.get("salt1_cooler_hx_supported"))).lower(),
            "selected_now": str(bool(resolution.get("salt1_cooler_hx_supported"))).lower(),
        },
        {
            "option_id": "M2_CORE_3ROW_SUPPORTED_SCORE_READY",
            "status": "policy_option_not_granted",
            "release_condition": "explicit approval that Salt1 unsupported context does not block holdout scoring",
            "holdout_score_release": "false",
            "selected_now": "false",
        },
    ]


def build_default_blocked_decision() -> list[dict[str, Any]]:
    resolution = read_json(RESOLUTION / "summary.json")
    supported = bool(resolution.get("salt1_cooler_hx_supported"))
    return [
        {
            "decision_id": "m2_default_score_release",
            "decision": "release_4row_score_ready" if supported else "blocked_missing_salt1_cooler_hx",
            "holdout_rows_scored_now": 0,
            "fit_rows_added": 0,
            "model_selection_rows_added": 0,
            "reason": "Salt1 cooler/HX support found" if supported else "No numeric Salt1 cooler/HX projection exists",
        }
    ]


def build_three_row_exception_requirements() -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": "explicit_policy_approval",
            "status": "missing",
            "required_before_release": "yes",
            "detail": "Approve M2_CORE_3ROW_SUPPORTED_SCORE_READY in writing before blind scoring.",
        },
        {
            "requirement_id": "salt1_unsupported_context_disclosure",
            "status": "prepared_not_approved",
            "required_before_release": "yes",
            "detail": "Scorecard must state Salt1 train-row cooler/HX remains unsupported.",
        },
        {
            "requirement_id": "no_fit_or_selection_change",
            "status": "pass",
            "required_before_release": "yes",
            "detail": "Exception may score only; it must not alter fitting or candidate selection.",
        },
    ]


def build_holdout_rows_still_blocked() -> list[dict[str, Any]]:
    return [
        {
            "case_key": row["case_key"],
            "row_family": row["row_family"],
            "score_now": "no",
            "blocker": "m2_score_release_not_granted",
            "source_status": row["readiness_status"],
        }
        for row in read_csv(READINESS / "scoring_row_queue.csv")
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [(RESOLUTION / "summary.json", "Salt1 cooler/HX resolution"), (READINESS / "scoring_row_queue.csv", "holdout readiness queue")]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# M2 Score Release Decision Packet\n\nDecision: {summary['decision']}. Holdout rows scored now: {summary['holdout_rows_scored_now']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- decision: {summary['decision']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} M2 score release decision packet\n\nPrepared score release options without scoring holdout rows.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    options = build_score_release_options()
    decision = build_default_blocked_decision()
    requirements = build_three_row_exception_requirements()
    blocked = build_holdout_rows_still_blocked()
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "decision": decision[0]["decision"],
        "three_row_exception_granted": False,
        "holdout_rows_blocked": len(blocked),
        "holdout_rows_scored_now": 0,
        "fit_rows_added": 0,
        "model_selection_rows_added": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "score_release_options.csv", options)
    write_csv(OUT / "default_blocked_decision.csv", decision)
    write_csv(OUT / "three_row_exception_requirements.csv", requirements)
    write_csv(OUT / "holdout_rows_still_blocked.csv", blocked)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
