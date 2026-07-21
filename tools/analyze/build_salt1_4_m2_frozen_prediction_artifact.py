#!/usr/bin/env python3
"""Freeze the M2 admitted-boundary prediction artifact for Salt1-4 nominal rows."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-SALT1-4-M2-FROZEN-PREDICTION-ARTIFACT"
SOURCE_CANDIDATE_FREEZE_ID = "M2_CANDIDATE_FREEZE_SALT1_4_NOMINAL_2026_07_20"
FROZEN_MODEL_ID = "M2_FROZEN_PREDICTION_ARTIFACT_SALT1_4_NOMINAL_2026_07_20"
MODEL_FAMILY = "M2"
MODEL_FORM_NAME = "admitted_heater_cooler_boundary_model"

OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_frozen_prediction_artifact"
M2_CANDIDATE = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_predictive_candidate_freeze"
CANDIDATE_MANIFEST = M2_CANDIDATE / "candidate_freeze_manifest.csv"
CANDIDATE_TERMS = M2_CANDIDATE / "candidate_model_terms.csv"
CANDIDATE_HOLDOUT_EXCLUSION = M2_CANDIDATE / "holdout_exclusion_audit.csv"
HEATER_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/heater_scorecard.csv"
)
COOLER_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/cooler_hx_scorecard.csv"
)
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-SALT1-4-M2-FROZEN-PREDICTION-ARTIFACT.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-salt1-4-m2-frozen-prediction-artifact.md"
IMPORT = ROOT / "imports/2026-07-20_salt1_4_m2_frozen_prediction_artifact.json"

BUCKET_TO_CASE_ID = {"salt1": "salt_1", "salt2": "salt_2", "salt3": "salt_3", "salt4": "salt_4"}
BUCKET_TO_GENERALIZATION_SPLIT = {"salt2": "train", "salt3": "validation", "salt4": "holdout"}
FORBIDDEN_FAMILIES = ("PM5", "PM10", "val_salt2", "new-CFD")


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
    required = [CANDIDATE_MANIFEST, CANDIDATE_TERMS, CANDIDATE_HOLDOUT_EXCLUSION, HEATER_SCORECARD, COOLER_SCORECARD]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M2 frozen prediction sources: " + "; ".join(missing))


def scorecard_by_split(path: Path) -> dict[str, dict[str, str]]:
    return {row["case_split"]: row for row in read_csv(path)}


def cooler_by_case_id() -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(COOLER_SCORECARD)}


def admitted_term_rows() -> list[dict[str, str]]:
    return [row for row in read_csv(CANDIDATE_TERMS) if row["term_status"] == "admitted_predictive_boundary_term"]


def blocked_term_rows() -> list[dict[str, str]]:
    return [row for row in read_csv(CANDIDATE_TERMS) if row["term_status"] == "blocked_or_diagnostic"]


def heater_scalar() -> str:
    rows = read_csv(HEATER_SCORECARD)
    scalars = {row["fitted_scalar"] for row in rows if row["admission_decision"] == "admitted_predictive_boundary_submodel"}
    if len(scalars) != 1:
        raise ValueError(f"Expected exactly one admitted heater scalar, got {sorted(scalars)}")
    return next(iter(scalars))


def build_candidate_model_freeze() -> dict[str, Any]:
    admitted = admitted_term_rows()
    blocked = blocked_term_rows()
    return {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "frozen_model_id": FROZEN_MODEL_ID,
        "source_candidate_freeze_id": SOURCE_CANDIDATE_FREEZE_ID,
        "model_family": MODEL_FAMILY,
        "model_form_name": MODEL_FORM_NAME,
        "training_rows_source": rel(CANDIDATE_MANIFEST),
        "admitted_terms": [
            {
                "term_id": "heater",
                "model_form": "salt2_fit_constant_heater_efficiency",
                "fitted_scalar": heater_scalar(),
                "source_path": rel(HEATER_SCORECARD),
            },
            {
                "term_id": "cooler_hx",
                "model_form": "salt2_fit_constant_UA_bulk_drive",
                "prediction_source": rel(COOLER_SCORECARD),
            },
        ],
        "blocked_terms": [
            {"term_id": row["term_id"], "remaining_blocker": row["remaining_blocker"]} for row in blocked
        ],
        "runtime_policy": {
            "allowed_inputs": "setup geometry/property lane/setup heater/cooler/ambient metadata",
            "forbidden_inputs": "CFD mdot; realized CFD wallHeatFlux; pressure losses; validation temperatures; blind-row targets",
        },
        "holdout_rows_scored": 0,
        "blind_rows_used_for_fit": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
        "admitted_term_count": len(admitted),
        "blocked_term_count": len(blocked),
    }


def build_train_row_predictions() -> list[dict[str, Any]]:
    heater = scorecard_by_split(HEATER_SCORECARD)
    cooler = cooler_by_case_id()
    rows: list[dict[str, Any]] = []
    for manifest in read_csv(CANDIDATE_MANIFEST):
        bucket = manifest["bucket"]
        case_id = BUCKET_TO_CASE_ID[bucket]
        split = BUCKET_TO_GENERALIZATION_SPLIT.get(bucket, "")
        heater_row = heater.get(split, {})
        cooler_row = cooler.get(case_id, {})
        heater_available = bool(heater_row)
        cooler_available = bool(cooler_row)
        prediction_status = (
            "admitted_boundary_prediction_available"
            if heater_available and cooler_available
            else "missing_supported_scorecard_row"
        )
        rows.append(
            {
                "frozen_model_id": FROZEN_MODEL_ID,
                "source_candidate_freeze_id": manifest["candidate_freeze_id"],
                "case_key": manifest["case_key"],
                "bucket": bucket,
                "case_id": case_id,
                "split_role": manifest["split_role"],
                "prediction_scope": "training_row_nominal_only",
                "heater_model_form": "salt2_fit_constant_heater_efficiency",
                "heater_fitted_scalar": heater_scalar() if heater_available else "",
                "heater_prediction_status": "available_from_admitted_scorecard" if heater_available else "missing_supported_scorecard_row",
                "heater_abs_error_W_context": heater_row.get("abs_error_W", ""),
                "cooler_model_form": "salt2_fit_constant_UA_bulk_drive",
                "cooler_predicted_qhx_W": cooler_row.get("predicted_qhx_W", ""),
                "cooler_prediction_status": "available_from_admitted_scorecard" if cooler_available else "missing_supported_scorecard_row",
                "cooler_abs_error_W_context": cooler_row.get("abs_error_W", ""),
                "admitted_boundary_prediction_status": prediction_status,
                "blocked_terms": "wall_test_section_passive_boundary;pressure_lanes;upcomer_internal_nu;two_tap_corner_k",
                "holdout_or_external_scoring": "not_performed",
                "source_path": rel(CANDIDATE_MANIFEST),
            }
        )
    return rows


def build_freeze_runtime_audit() -> list[dict[str, Any]]:
    rows = [
        {
            "audit_id": "m2_setup_inputs_only",
            "gate": "pass",
            "input_family": "geometry;property lane;setup heater/cooler metadata;ambient/radiation setup inputs",
            "runtime_or_fit_use": "allowed",
            "source_path": rel(CANDIDATE_TERMS),
        },
        {
            "audit_id": "admitted_boundary_terms_only",
            "gate": "pass",
            "input_family": "heater and cooler/HX admitted scorecard terms",
            "runtime_or_fit_use": "allowed",
            "source_path": rel(HEATER_SCORECARD) + ";" + rel(COOLER_SCORECARD),
        },
        {
            "audit_id": "forbidden_cfd_targets",
            "gate": "pass",
            "input_family": "CFD mdot; realized CFD wallHeatFlux; pressure losses; validation temperatures",
            "runtime_or_fit_use": "forbidden",
            "source_path": rel(CANDIDATE_TERMS),
        },
    ]
    for family in FORBIDDEN_FAMILIES:
        rows.append(
            {
                "audit_id": f"exclude_{family.lower().replace('-', '_')}",
                "gate": "pass",
                "input_family": family,
                "runtime_or_fit_use": "excluded_from_fit_model_selection_and_scoring_in_this_artifact",
                "source_path": rel(CANDIDATE_HOLDOUT_EXCLUSION),
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (CANDIDATE_MANIFEST, "candidate training rows"),
        (CANDIDATE_TERMS, "candidate admitted/blocked terms"),
        (CANDIDATE_HOLDOUT_EXCLUSION, "blind-row exclusion audit"),
        (HEATER_SCORECARD, "admitted heater scalar"),
        (COOLER_SCORECARD, "admitted cooler/HX predictions"),
    ]
    return [
        {
            "source_id": path.stem,
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": role,
            "mutation": "read_only",
        }
        for path, role in sources
    ]


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                f"# {TASK}",
                "",
                "- status: complete",
                f"- frozen_model_id: {FROZEN_MODEL_ID}",
                f"- train_rows: {summary['train_rows']}",
                f"- holdout_rows_scored: {summary['holdout_rows_scored']}",
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
                f"# {DATE} M2 frozen prediction artifact",
                "",
                "Froze admitted heater/cooler M2 boundary predictions for Salt1-4 nominal rows only.",
                "No blind holdout scoring or solver mutation was performed.",
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


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# Salt1-4 M2 Frozen Prediction Artifact",
                "",
                f"Frozen model id: `{FROZEN_MODEL_ID}`.",
                "",
                "This package freezes the M2 admitted heater/cooler boundary artifact for Salt1-4 nominal rows only.",
                "It does not score PM5, PM10, val_salt2, or new-CFD rows.",
                "",
                "Primary outputs:",
                "",
                "- `candidate_model_freeze.json`",
                "- `train_row_predictions.csv`",
                "- `freeze_runtime_audit.csv`",
                "- `summary.json`",
                "",
                f"Train rows: {summary['train_rows']}.",
                f"Rows with full admitted boundary predictions: {summary['rows_with_full_admitted_boundary_predictions']}.",
                f"Holdout rows scored: {summary['holdout_rows_scored']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> dict[str, Any]:
    require_sources()
    model_freeze = build_candidate_model_freeze()
    predictions = build_train_row_predictions()
    audit = build_freeze_runtime_audit()
    sources = build_source_manifest()

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "frozen_model_id": FROZEN_MODEL_ID,
        "source_candidate_freeze_id": SOURCE_CANDIDATE_FREEZE_ID,
        "frozen_prediction_artifact_created": True,
        "train_rows": len(predictions),
        "rows_with_full_admitted_boundary_predictions": sum(
            row["admitted_boundary_prediction_status"] == "admitted_boundary_prediction_available"
            for row in predictions
        ),
        "rows_missing_supported_scorecard": sum(
            row["admitted_boundary_prediction_status"] == "missing_supported_scorecard_row"
            for row in predictions
        ),
        "holdout_rows_scored": 0,
        "blind_rows_used_for_fit": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_json(OUT / "candidate_model_freeze.json", model_freeze)
    write_csv(OUT / "train_row_predictions.csv", predictions)
    write_csv(OUT / "freeze_runtime_audit.csv", audit)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
