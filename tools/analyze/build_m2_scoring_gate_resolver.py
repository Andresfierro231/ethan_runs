#!/usr/bin/env python3
"""Resolve whether the M2 frozen artifact can be released for blind scoring."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-M2-SCORING-GATE-RESOLVER"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_scoring_gate_resolver"
M2_ARTIFACT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_frozen_prediction_artifact"
SALT1_CLOSEOUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_salt1_support_closeout"
READINESS = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_holdout_scoring_readiness"
FINAL_FREEZE = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_nominal_final_freeze"
COOLER_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/cooler_hx_scorecard.csv"
)
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-M2-SCORING-GATE-RESOLVER.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-m2-scoring-gate-resolver.md"
IMPORT = ROOT / "imports/2026-07-20_m2_scoring_gate_resolver.json"

FROZEN_MODEL_ID = "M2_FROZEN_PREDICTION_ARTIFACT_SALT1_4_NOMINAL_2026_07_20"


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
        M2_ARTIFACT / "candidate_model_freeze.json",
        M2_ARTIFACT / "train_row_predictions.csv",
        SALT1_CLOSEOUT / "summary.json",
        READINESS / "scoring_row_queue.csv",
        FINAL_FREEZE / "final_freeze_manifest.csv",
        COOLER_SCORECARD,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M2 scoring resolver sources: " + "; ".join(missing))


def cooler_scorecard_has_salt1() -> bool:
    for row in read_csv(COOLER_SCORECARD):
        values = {row.get("case_id", ""), row.get("case_key", ""), row.get("bucket", "")}
        if {"salt_1", "salt1", "salt1_nominal"} & values:
            return True
    return False


def build_salt1_cooler_hx_source_search() -> list[dict[str, Any]]:
    closeout = read_json(SALT1_CLOSEOUT / "summary.json")
    candidates = [
        (COOLER_SCORECARD, "admitted cooler/HX scorecard", cooler_scorecard_has_salt1()),
        (SALT1_CLOSEOUT / "salt1_boundary_projection_candidate.csv", "prior Salt1 projection closeout", False),
        (FINAL_FREEZE / "final_freeze_manifest.csv", "Salt1 final freeze membership", False),
    ]
    rows = []
    for path, role, supported in candidates:
        rows.append(
            {
                "case_key": "salt1_nominal",
                "source_path": rel(path),
                "source_role": role,
                "exists": "yes" if path.exists() else "no",
                "salt1_cooler_hx_supported": str(supported).lower(),
                "status": "supported" if supported else "not_supported",
                "evidence": (
                    "salt1 cooler/HX row found"
                    if supported
                    else closeout.get("salt1_cooler_hx_projection_status", "missing_supported_scorecard_row")
                ),
            }
        )
    return rows


def build_m2_score_ready_policy_decision(search_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    has_salt1_cooler = any(row["salt1_cooler_hx_supported"] == "true" for row in search_rows)
    decision = "score_ready" if has_salt1_cooler else "blocked_missing_salt1_cooler_hx"
    return [
        {
            "frozen_model_id": FROZEN_MODEL_ID,
            "decision": decision,
            "score_ready_artifact_id": FROZEN_MODEL_ID if has_salt1_cooler else "",
            "score_ready_exception_id": "",
            "exception_granted": "false",
            "holdout_score_release": str(has_salt1_cooler).lower(),
            "reason": (
                "Salt1 cooler/HX support exists"
                if has_salt1_cooler
                else "Salt1 cooler/HX support is missing and no 3-row score-ready exception is granted"
            ),
            "fit_or_model_selection_changed": "false",
            "native_solver_outputs_mutated": "false",
        }
    ]


def build_score_ready_artifact_candidate(decision: dict[str, Any]) -> dict[str, Any]:
    freeze = read_json(M2_ARTIFACT / "candidate_model_freeze.json")
    return {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "source_frozen_model_id": FROZEN_MODEL_ID,
        "candidate_status": decision["decision"],
        "score_ready": decision["holdout_score_release"] == "true",
        "score_ready_exception_granted": False,
        "model_family": freeze.get("model_family", "M2"),
        "admitted_terms": freeze.get("admitted_terms", []),
        "blocked_reason": "" if decision["holdout_score_release"] == "true" else decision["reason"],
        "holdout_rows_scored": 0,
        "blind_rows_used_for_fit": 0,
        "native_solver_outputs_mutated": False,
    }


def build_holdout_score_release_gate(decision: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(READINESS / "scoring_row_queue.csv"):
        rows.append(
            {
                "case_key": row["case_key"],
                "row_family": row["row_family"],
                "release_status": "release_after_score_ready_artifact" if decision["holdout_score_release"] == "true" else "blocked",
                "score_now": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "blocker": "" if decision["holdout_score_release"] == "true" else "missing_salt1_cooler_hx_or_explicit_exception",
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (M2_ARTIFACT / "candidate_model_freeze.json", "source M2 artifact"),
        (M2_ARTIFACT / "train_row_predictions.csv", "train-row support status"),
        (SALT1_CLOSEOUT / "summary.json", "Salt1 closeout"),
        (READINESS / "scoring_row_queue.csv", "queued blind rows"),
        (COOLER_SCORECARD, "cooler/HX scorecard"),
    ]
    return [
        {"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"}
        for path, role in sources
    ]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# M2 Scoring Gate Resolver",
                "",
                "This package resolves the next M2 blind-scoring gate without scoring holdout rows.",
                "",
                f"Decision: `{summary['score_gate_status']}`.",
                f"Holdout rows released now: {summary['holdout_rows_released_now']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- score_gate_status: {summary['score_gate_status']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} M2 scoring gate resolver\n\nResolved M2 score-ready gate without blind scoring.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    search = build_salt1_cooler_hx_source_search()
    decision = build_m2_score_ready_policy_decision(search)
    artifact = build_score_ready_artifact_candidate(decision[0])
    release = build_holdout_score_release_gate(decision[0])
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "score_gate_status": decision[0]["decision"],
        "salt1_cooler_hx_supported": any(row["salt1_cooler_hx_supported"] == "true" for row in search),
        "score_ready_exception_granted": False,
        "holdout_rows_released_now": 0,
        "holdout_rows_scored": 0,
        "fit_rows_added": 0,
        "model_selection_rows_added": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "salt1_cooler_hx_source_search.csv", search)
    write_csv(OUT / "m2_score_ready_policy_decision.csv", decision)
    write_json(OUT / "m2_score_ready_artifact_candidate.json", artifact)
    write_csv(OUT / "holdout_score_release_gate.csv", release)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
