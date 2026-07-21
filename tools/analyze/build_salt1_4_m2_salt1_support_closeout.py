#!/usr/bin/env python3
"""Close out Salt1 support status for the Salt1-4 M2 frozen prediction artifact."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-SALT1-4-M2-SALT1-SUPPORT-CLOSEOUT"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_salt1_support_closeout"
FROZEN_ARTIFACT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_frozen_prediction_artifact"
FINAL_FREEZE = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_nominal_final_freeze"
SALT1_SCHEMA = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion"
HEATER_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/heater_scorecard.csv"
)
COOLER_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/cooler_hx_scorecard.csv"
)
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-SALT1-4-M2-SALT1-SUPPORT-CLOSEOUT.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-salt1-4-m2-salt1-support-closeout.md"
IMPORT = ROOT / "imports/2026-07-20_salt1_4_m2_salt1_support_closeout.json"

FROZEN_MODEL_ID = "M2_FROZEN_PREDICTION_ARTIFACT_SALT1_4_NOMINAL_2026_07_20"
SALT1_CASE_KEY = "salt1_nominal"
SALT1_CASE_ID = "salt_1"


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
        FROZEN_ARTIFACT / "train_row_predictions.csv",
        FROZEN_ARTIFACT / "candidate_model_freeze.json",
        FINAL_FREEZE / "final_freeze_manifest.csv",
        HEATER_SCORECARD,
        COOLER_SCORECARD,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Salt1 M2 closeout sources: " + "; ".join(missing))


def first(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    matches = [row for row in rows if row.get(key) == value]
    if not matches:
        raise ValueError(f"Expected row with {key}={value}")
    return matches[0]


def admitted_heater_scalar() -> str:
    rows = [row for row in read_csv(HEATER_SCORECARD) if row.get("admission_decision") == "admitted_predictive_boundary_submodel"]
    scalars = {row.get("fitted_scalar", "") for row in rows if row.get("fitted_scalar", "")}
    if len(scalars) != 1:
        return ""
    return next(iter(scalars))


def cooler_salt1_row() -> dict[str, str] | None:
    for row in read_csv(COOLER_SCORECARD):
        if row.get("case_id") == SALT1_CASE_ID or row.get("case_key") == SALT1_CASE_KEY:
            return row
    return None


def build_salt1_m2_support_audit() -> list[dict[str, Any]]:
    train = first(read_csv(FROZEN_ARTIFACT / "train_row_predictions.csv"), "case_key", SALT1_CASE_KEY)
    freeze = first(read_csv(FINAL_FREEZE / "final_freeze_manifest.csv"), "case_key", SALT1_CASE_KEY)
    heater_scalar = admitted_heater_scalar()
    cooler_row = cooler_salt1_row()
    schema_sources = sorted(SALT1_SCHEMA.glob("*.csv"))

    return [
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "check_id": "salt1_training_freeze_membership",
            "status": "pass" if freeze.get("freeze_inclusion") == "included_final_predictive_training_envelope" else "fail",
            "evidence": freeze.get("schema_source_status", ""),
            "source_path": rel(FINAL_FREEZE / "final_freeze_manifest.csv"),
        },
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "check_id": "salt1_schema_parity",
            "status": "pass" if freeze.get("schema_parity_status") == "pass" else "fail",
            "evidence": ";".join(rel(path) for path in schema_sources) if schema_sources else "schema_promotion_directory_missing_csvs",
            "source_path": rel(freeze_path_from_row(freeze)),
        },
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "check_id": "heater_boundary_projection",
            "status": "supported" if heater_scalar else "blocked",
            "evidence": "admitted_global_heater_scalar_available" if heater_scalar else "missing_single_admitted_heater_scalar",
            "source_path": rel(HEATER_SCORECARD),
        },
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "check_id": "cooler_hx_boundary_projection",
            "status": "supported" if cooler_row else "blocked",
            "evidence": (
                "salt1_cooler_hx_scorecard_row_available"
                if cooler_row
                else "missing_salt1_cooler_hx_scorecard_row_no_projection_fabricated"
            ),
            "source_path": rel(COOLER_SCORECARD),
        },
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "check_id": "current_m2_train_prediction",
            "status": train.get("admitted_boundary_prediction_status", ""),
            "evidence": (
                "current frozen artifact leaves Salt1 unsupported; closeout must not overwrite it without cooler/HX support"
            ),
            "source_path": rel(FROZEN_ARTIFACT / "train_row_predictions.csv"),
        },
    ]


def freeze_path_from_row(row: dict[str, str]) -> Path:
    source = row.get("source_summary_path") or row.get("source_path") or ""
    return ROOT / source if source and not source.startswith("/") else Path(source) if source else FINAL_FREEZE


def build_salt1_boundary_projection_candidate() -> list[dict[str, Any]]:
    heater_scalar = admitted_heater_scalar()
    cooler_row = cooler_salt1_row()
    full_support = bool(heater_scalar and cooler_row)
    return [
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "term_id": "heater",
            "projection_status": "supported" if heater_scalar else "blocked",
            "candidate_value": heater_scalar,
            "model_form": "salt2_fit_constant_heater_efficiency",
            "admission_use": "candidate_train_row_update_only_if_all_m2_boundary_terms_supported",
            "source_path": rel(HEATER_SCORECARD),
        },
        {
            "case_key": SALT1_CASE_KEY,
            "case_id": SALT1_CASE_ID,
            "term_id": "cooler_hx",
            "projection_status": "supported" if cooler_row else "blocked_missing_supported_scorecard_row",
            "candidate_value": cooler_row.get("predicted_qhx_W", "") if cooler_row else "",
            "model_form": "salt2_fit_constant_UA_bulk_drive",
            "admission_use": (
                "candidate_train_row_update_allowed" if full_support else "do_not_update_no_fabricated_cooler_projection"
            ),
            "source_path": rel(COOLER_SCORECARD),
        },
    ]


def build_m2_artifact_update_decision() -> list[dict[str, Any]]:
    candidates = build_salt1_boundary_projection_candidate()
    full_support = all(row["projection_status"] == "supported" for row in candidates)
    decision = "update_artifact_supported" if full_support else "no_update_salt1_cooler_hx_support_missing"
    return [
        {
            "frozen_model_id": FROZEN_MODEL_ID,
            "case_key": SALT1_CASE_KEY,
            "decision": decision,
            "salt1_gap_status": "closed_supported" if full_support else "closed_blocked_nonfabricated",
            "current_artifact_action": "emit_follow_on_4_row_artifact" if full_support else "leave_current_artifact_unchanged",
            "reason": (
                "heater and cooler/HX boundary projections are both supported"
                if full_support
                else "heater scalar is available but Salt1 cooler/HX scorecard row is missing"
            ),
            "holdout_scoring_unblocked": str(full_support).lower(),
            "fit_or_model_selection_changed": "false",
            "native_solver_outputs_mutated": "false",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (FROZEN_ARTIFACT / "train_row_predictions.csv", "current M2 train-row predictions"),
        (FROZEN_ARTIFACT / "candidate_model_freeze.json", "current frozen model artifact"),
        (FINAL_FREEZE / "final_freeze_manifest.csv", "Salt1-4 nominal final training freeze"),
        (HEATER_SCORECARD, "admitted heater scalar"),
        (COOLER_SCORECARD, "cooler/HX scorecard"),
        (SALT1_SCHEMA, "Salt1 schema promotion package"),
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
                "# Salt1 M2 Support Closeout",
                "",
                "This package closes the Salt1 support question for the M2 frozen prediction artifact.",
                "It does not overwrite the frozen model artifact and does not score blind rows.",
                "",
                "Primary outputs:",
                "",
                "- `salt1_m2_support_audit.csv`",
                "- `salt1_boundary_projection_candidate.csv`",
                "- `m2_artifact_update_decision.csv`",
                "- `summary.json`",
                "",
                f"Salt1 gap status: {summary['salt1_gap_status']}.",
                f"Follow-on artifact emitted: {summary['follow_on_artifact_emitted']}.",
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
                f"- salt1_gap_status: {summary['salt1_gap_status']}",
                f"- follow_on_artifact_emitted: {summary['follow_on_artifact_emitted']}",
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
                f"# {DATE} Salt1 M2 support closeout",
                "",
                "Audited Salt1 support for admitted heater/cooler M2 boundary predictions.",
                "No blind scoring, fitting, or solver mutation was performed.",
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
    audit = build_salt1_m2_support_audit()
    candidate = build_salt1_boundary_projection_candidate()
    decision = build_m2_artifact_update_decision()
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "frozen_model_id": FROZEN_MODEL_ID,
        "salt1_gap_status": decision[0]["salt1_gap_status"],
        "salt1_heater_projection_status": candidate[0]["projection_status"],
        "salt1_cooler_hx_projection_status": candidate[1]["projection_status"],
        "follow_on_artifact_emitted": decision[0]["current_artifact_action"] == "emit_follow_on_4_row_artifact",
        "holdout_scoring_unblocked": decision[0]["holdout_scoring_unblocked"] == "true",
        "fit_or_model_selection_changed": False,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "salt1_m2_support_audit.csv", audit)
    write_csv(OUT / "salt1_boundary_projection_candidate.csv", candidate)
    write_csv(OUT / "m2_artifact_update_decision.csv", decision)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
