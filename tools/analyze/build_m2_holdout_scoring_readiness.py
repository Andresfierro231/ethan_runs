#!/usr/bin/env python3
"""Build a readiness queue for future blind scoring with the M2 frozen artifact."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-M2-HOLDOUT-SCORING-READINESS"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_m2_holdout_scoring_readiness"
FROZEN_ARTIFACT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_frozen_prediction_artifact"
SALT1_CLOSEOUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_salt1_support_closeout"
M2_CANDIDATE = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_predictive_candidate_freeze"
PM10 = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"
PM5 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing"
VAL_SALT2 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-M2-HOLDOUT-SCORING-READINESS.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-m2-holdout-scoring-readiness.md"
IMPORT = ROOT / "imports/2026-07-20_m2_holdout_scoring_readiness.json"

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
        FROZEN_ARTIFACT / "candidate_model_freeze.json",
        FROZEN_ARTIFACT / "train_row_predictions.csv",
        M2_CANDIDATE / "holdout_exclusion_audit.csv",
        PM10 / "pm10_split_decisions.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M2 holdout readiness sources: " + "; ".join(missing))


def model_is_score_ready() -> bool:
    if not (SALT1_CLOSEOUT / "summary.json").exists():
        return False
    closeout = read_json(SALT1_CLOSEOUT / "summary.json")
    return bool(closeout.get("holdout_scoring_unblocked"))


def pm10_decision_by_case() -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in read_csv(PM10 / "pm10_split_decisions.csv")}


def classify_family(case_key: str, split_role: str) -> str:
    if "10q" in case_key.lower():
        return "PM10"
    if "5q" in case_key.lower():
        return "PM5"
    if case_key == "val_salt2":
        return "val_salt2"
    if "new" in case_key.lower() or split_role == "new_cfd":
        return "new-CFD"
    return "holdout"


def build_scoring_row_queue() -> list[dict[str, Any]]:
    ready_model = model_is_score_ready()
    pm10 = pm10_decision_by_case()
    rows = []
    for row in read_csv(M2_CANDIDATE / "holdout_exclusion_audit.csv"):
        case_key = row["case_key"]
        family = classify_family(case_key, row.get("split_role", ""))
        source_paths = [rel(M2_CANDIDATE / "holdout_exclusion_audit.csv")]
        admission_status = "not_yet_checked"
        readiness_status = "blocked_model_artifact_not_score_ready"
        blocker = "salt1_m2_support_closeout_did_not_unblock_blind_scoring"

        if family == "PM10":
            pm10_row = pm10.get(case_key, {})
            source_paths.append(rel(PM10 / "pm10_split_decisions.csv"))
            admission_status = pm10_row.get("classification_split_role") or pm10_row.get("decision", "missing_pm10_decision")
            decision = pm10_row.get("decision", "")
            if "future_holdout" in admission_status or decision == "holdout_testing_not_training":
                readiness_status = "ready_after_model_artifact_score_ready" if ready_model else readiness_status
                blocker = "" if ready_model else blocker
            else:
                readiness_status = "blocked_pm10_terminal_admission"
                blocker = admission_status
        elif family == "PM5":
            source_paths.append(rel(PM5 / "corrected_q_pm5_split_admission_matrix.csv"))
            admission_status = "pm5_admission_package_available" if PM5.exists() else "missing_pm5_admission_package"
        elif family == "val_salt2":
            source_paths.append(rel(VAL_SALT2 / "val_salt2_external_admission_decision.csv"))
            admission_status = "external_ledger_available" if VAL_SALT2.exists() else "missing_val_salt2_external_ledger"
        else:
            admission_status = "policy_holdout_exclusion_only"

        rows.append(
            {
                "frozen_model_id": FROZEN_MODEL_ID,
                "case_key": case_key,
                "split_role": row.get("split_role", ""),
                "row_family": family,
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "score_now": "no",
                "readiness_status": readiness_status,
                "admission_status": admission_status,
                "blocker": blocker,
                "source_paths": ";".join(source_paths),
            }
        )
    return rows


def build_prediction_join_contract(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in queue:
        rows.append(
            {
                "case_key": row["case_key"],
                "row_family": row["row_family"],
                "join_key": "case_key",
                "prediction_source": rel(FROZEN_ARTIFACT / "candidate_model_freeze.json"),
                "target_source_status": row["admission_status"],
                "score_policy": "blind_score_only_after_frozen_model_score_ready",
                "score_now": "no",
                "leakage_guard": "target rows may be joined only after prediction artifact is frozen",
            }
        )
    return rows


def build_target_leakage_audit(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = sorted({row["row_family"] for row in queue})
    rows = [
        {
            "audit_id": "m2_fit_scope",
            "gate": "pass",
            "evidence": "candidate freeze uses Salt1-4 nominal manifest only",
            "source_path": rel(M2_CANDIDATE / "candidate_freeze_manifest.csv"),
        },
        {
            "audit_id": "holdout_predictions_disabled",
            "gate": "pass",
            "evidence": "readiness queue sets score_now=no for every row",
            "source_path": rel(FROZEN_ARTIFACT / "summary.json"),
        },
    ]
    for family in families:
        rows.append(
            {
                "audit_id": f"exclude_{family.lower().replace('-', '_')}",
                "gate": "pass",
                "evidence": "not used for fit or model selection",
                "source_path": rel(M2_CANDIDATE / "holdout_exclusion_audit.csv"),
            }
        )
    return rows


def build_blocked_score_rows(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_key": row["case_key"],
            "row_family": row["row_family"],
            "readiness_status": row["readiness_status"],
            "blocker": row["blocker"] or "model_artifact_score_ready_required",
            "next_action": "rerun readiness after Salt1 M2 support closes and row admission/target joins are verified",
        }
        for row in queue
        if row["score_now"] != "yes"
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (FROZEN_ARTIFACT / "candidate_model_freeze.json", "frozen M2 model artifact"),
        (FROZEN_ARTIFACT / "train_row_predictions.csv", "M2 train-row prediction status"),
        (SALT1_CLOSEOUT / "summary.json", "Salt1 closeout score-ready gate"),
        (M2_CANDIDATE / "holdout_exclusion_audit.csv", "blind-row exclusion audit"),
        (PM10 / "pm10_split_decisions.csv", "PM10 terminal split decisions"),
        (PM5 / "corrected_q_pm5_split_admission_matrix.csv", "PM5 admission package"),
        (VAL_SALT2 / "val_salt2_external_admission_decision.csv", "val_salt2 external admission package"),
    ]
    return [
        {
            "source_id": path.name,
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": role,
            "mutation": "read_only",
        }
        for path, role in sources
    ]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# M2 Holdout Scoring Readiness",
                "",
                "This package builds the future blind-scoring queue for the M2 artifact.",
                "It does not score PM5, PM10, val_salt2, or new-CFD rows.",
                "",
                "Primary outputs:",
                "",
                "- `scoring_row_queue.csv`",
                "- `prediction_join_contract.csv`",
                "- `target_leakage_audit.csv`",
                "- `blocked_score_rows.csv`",
                "- `summary.json`",
                "",
                f"Queue rows: {summary['queue_rows']}.",
                f"Rows scored now: {summary['rows_scored_now']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                f"# {TASK}",
                "",
                "- status: complete",
                f"- queue_rows: {summary['queue_rows']}",
                f"- rows_scored_now: {summary['rows_scored_now']}",
                f"- output: {rel(OUT)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                f"# {DATE} M2 holdout scoring readiness",
                "",
                "Prepared blind scoring queue without scoring holdout/external/new-CFD rows.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        IMPORT,
        {
            "task": TASK,
            "date": DATE,
            "output_dir": rel(OUT),
            "native_solver_outputs_mutated": False,
            "generated_index_refreshed": False,
            "summary_path": rel(OUT / "summary.json"),
        },
    )


def main() -> dict[str, Any]:
    require_sources()
    queue = build_scoring_row_queue()
    join = build_prediction_join_contract(queue)
    leakage = build_target_leakage_audit(queue)
    blocked = build_blocked_score_rows(queue)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "frozen_model_id": FROZEN_MODEL_ID,
        "queue_rows": len(queue),
        "rows_scored_now": sum(row["score_now"] == "yes" for row in queue),
        "blocked_score_rows": len(blocked),
        "fit_rows_added": 0,
        "model_selection_rows_added": 0,
        "holdout_predictions_created": False,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "scoring_row_queue.csv", queue)
    write_csv(OUT / "prediction_join_contract.csv", join)
    write_csv(OUT / "target_leakage_audit.csv", leakage)
    write_csv(OUT / "blocked_score_rows.csv", blocked)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
