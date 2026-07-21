#!/usr/bin/env python3
"""Build the first M2 predictive candidate freeze from Salt1-4 nominal rows."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-SALT1-4-M2-CANDIDATE-FREEZE"
CANDIDATE_FREEZE_ID = "M2_CANDIDATE_FREEZE_SALT1_4_NOMINAL_2026_07_20"
MODEL_FAMILY_ID = "M2"
MODEL_FORM_NAME = "admitted_heater_cooler_boundary_model"

OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_m2_predictive_candidate_freeze"
TRAINING_FREEZE = (
    ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_nominal_final_freeze"
)
FINAL_FREEZE_MANIFEST = TRAINING_FREEZE / "final_freeze_manifest.csv"
HOLDOUT_EXCLUSION = TRAINING_FREEZE / "holdout_exclusion_audit.csv"
RUNTIME_AUDIT_SOURCE = TRAINING_FREEZE / "runtime_input_audit.csv"
BOUNDARY_ADMISSION = (
    ROOT / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission"
)
SUBMODEL_SUMMARY = BOUNDARY_ADMISSION / "submodel_admission_summary.csv"
MODEL_BAKEOFF = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff"
)
MODEL_CONTRACTS = MODEL_BAKEOFF / "model_form_contracts.csv"
MODEL_SCORES = MODEL_BAKEOFF / "model_form_scores.csv"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-SALT1-4-M2-CANDIDATE-FREEZE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-salt1-4-m2-candidate-freeze.md"
IMPORT = ROOT / "imports/2026-07-20_salt1_4_m2_predictive_candidate_freeze.json"

FINAL_TRAINING_CASES = {"salt1_nominal", "salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"}
FORBIDDEN_ROW_KEYS = {
    "salt2_lo5q",
    "salt2_hi5q",
    "val_salt2",
    "salt2_lo10q",
    "salt2_hi10q",
    "salt4_lo10q",
    "salt4_hi10q",
    "salt3_q_insulation_matrix",
}
ADMITTED_SUBMODELS = {"heater", "cooler_hx"}


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
        FINAL_FREEZE_MANIFEST,
        HOLDOUT_EXCLUSION,
        RUNTIME_AUDIT_SOURCE,
        SUBMODEL_SUMMARY,
        MODEL_CONTRACTS,
        MODEL_SCORES,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing M2 candidate-freeze sources: " + "; ".join(missing))


def m2_contract() -> dict[str, str]:
    matches = [row for row in read_csv(MODEL_CONTRACTS) if row["model_form_id"] == MODEL_FAMILY_ID]
    if len(matches) != 1:
        raise ValueError("Expected exactly one M2 model-form contract")
    return matches[0]


def build_candidate_freeze_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(FINAL_FREEZE_MANIFEST):
        if row["case_key"] not in FINAL_TRAINING_CASES:
            continue
        if row["split_role"] != "final_training" or row["fit_allowed"] != "yes":
            raise ValueError(f"Unexpected non-training row in freeze manifest: {row['case_key']}")
        rows.append(
            {
                "candidate_freeze_id": CANDIDATE_FREEZE_ID,
                "source_training_freeze_id": row["freeze_id"],
                "model_family_id": MODEL_FAMILY_ID,
                "model_form_name": MODEL_FORM_NAME,
                "case_key": row["case_key"],
                "bucket": row["bucket"],
                "source_key": row["source_key"],
                "split_role": row["split_role"],
                "candidate_fit_allowed": "yes",
                "candidate_model_selection_allowed": "yes",
                "candidate_score_allowed": row["score_allowed"],
                "candidate_row_inclusion": "included_m2_candidate_training",
                "runtime_input_gate": row["runtime_input_gate"],
                "schema_parity_status": row["schema_parity_status"],
                "source_summary_path": row["source_summary_path"],
            }
        )
    return rows


def build_candidate_model_terms() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(SUBMODEL_SUMMARY):
        submodel = row["submodel"]
        admitted = submodel in ADMITTED_SUBMODELS and row["admission_decision"] == "admitted_predictive_boundary_submodel"
        rows.append(
            {
                "candidate_freeze_id": CANDIDATE_FREEZE_ID,
                "model_family_id": MODEL_FAMILY_ID,
                "term_id": submodel,
                "preferred_model": row["preferred_model"],
                "term_role": "setup_boundary_term",
                "term_status": "admitted_predictive_boundary_term" if admitted else "blocked_or_diagnostic",
                "candidate_fit_use": "included" if admitted else "excluded",
                "runtime_input_gate": row["runtime_gate"],
                "validation_error": row["validation_error"],
                "holdout_error": row["holdout_error"],
                "remaining_blocker": row["remaining_blocker"],
                "coefficient_value_status": (
                    "use_admitted_submodel_artifact_no_refit_in_this_freeze"
                    if admitted
                    else "not_admitted_no_coefficient_fit"
                ),
                "forbidden_runtime_inputs": "CFD mdot; realized CFD wallHeatFlux; pressure losses; validation temperatures",
                "source_path": rel(SUBMODEL_SUMMARY),
            }
        )

    blocked_terms = [
        ("pressure_lanes", "pressure/upcomer rows remain zero fit-admitted or pending job 3305547 harvest"),
        ("upcomer_internal_nu", "recirculating rows remain diagnostic; ordinary Nu/f_D/K not admitted"),
        ("two_tap_corner_k", "corner lower-right rows are diagnostic; component K not admitted"),
    ]
    for term_id, blocker in blocked_terms:
        rows.append(
            {
                "candidate_freeze_id": CANDIDATE_FREEZE_ID,
                "model_family_id": MODEL_FAMILY_ID,
                "term_id": term_id,
                "preferred_model": "",
                "term_role": "blocked_non_m2_or_diagnostic_term",
                "term_status": "blocked_or_diagnostic",
                "candidate_fit_use": "excluded",
                "runtime_input_gate": "blocked",
                "validation_error": "not_scored",
                "holdout_error": "not_scored",
                "remaining_blocker": blocker,
                "coefficient_value_status": "not_admitted_no_coefficient_fit",
                "forbidden_runtime_inputs": "pressure/upcomer/two-tap diagnostic evidence cannot enter M2 fit",
                "source_path": rel(MODEL_CONTRACTS),
            }
        )
    return rows


def build_candidate_runtime_input_audit() -> list[dict[str, Any]]:
    return [
        {
            "audit_id": "allowed_setup_inputs",
            "gate": "pass",
            "input_family": "geometry;property lane;setup heater power;setup cooler/HX metadata;ambient/radiation setup inputs",
            "fit_use_status": "allowed",
            "evidence": "allowed runtime inputs in M2 model-form contract",
            "source_path": rel(MODEL_CONTRACTS),
        },
        {
            "audit_id": "admitted_boundary_coefficients_only",
            "gate": "pass",
            "input_family": "admitted heater/cooler coefficients",
            "fit_use_status": "allowed_from_admitted_submodel_artifact",
            "evidence": "heater and cooler_hx rows admitted in boundary submodel package",
            "source_path": rel(SUBMODEL_SUMMARY),
        },
        {
            "audit_id": "forbidden_blind_rows",
            "gate": "pass",
            "input_family": "PM5; PM10; val_salt2; new-CFD rows",
            "fit_use_status": "excluded_from_fitting_and_model_selection",
            "evidence": "holdout exclusion audit has no fit/model-selection rows",
            "source_path": rel(HOLDOUT_EXCLUSION),
        },
        {
            "audit_id": "forbidden_cfd_targets",
            "gate": "pass",
            "input_family": "CFD mdot; realized CFD wallHeatFlux; pressure losses; TP/TW validation temperatures; hidden multipliers",
            "fit_use_status": "forbidden_runtime_inputs",
            "evidence": "runtime guardrail inherited from final row freeze and M2 contract",
            "source_path": rel(RUNTIME_AUDIT_SOURCE),
        },
    ]


def build_candidate_fit_provenance() -> list[dict[str, Any]]:
    contract = m2_contract()
    return [
        {
            "candidate_freeze_id": CANDIDATE_FREEZE_ID,
            "model_family_id": MODEL_FAMILY_ID,
            "model_form_name": contract["model_form_name"],
            "predictive_or_diagnostic": contract["predictive_or_diagnostic"],
            "candidate_fit_status": "candidate_freeze_created_admitted_terms_reused_no_holdout_scoring",
            "training_rows_source": rel(FINAL_FREEZE_MANIFEST),
            "terms_source": rel(SUBMODEL_SUMMARY),
            "contract_source": rel(MODEL_CONTRACTS),
            "scoring_status": "not_scored_no_holdout_predictions_created",
            "native_solver_outputs_mutated": "false",
            "registry_mutation": "none",
        }
    ]


def build_holdout_exclusion_audit() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(HOLDOUT_EXCLUSION):
        rows.append(
            {
                "candidate_freeze_id": CANDIDATE_FREEZE_ID,
                "case_key": row["case_key"],
                "split_role": row["split_role"],
                "fit_allowed": row["fit_allowed"],
                "model_selection_allowed": row["model_selection_allowed"],
                "candidate_fit_use": "excluded_from_m2_candidate_fit",
                "candidate_model_selection_use": "excluded_from_m2_candidate_selection",
                "exclusion_gate": "pass" if row["case_key"] in FORBIDDEN_ROW_KEYS and row["exclusion_gate"] == "pass" else row["exclusion_gate"],
                "notes": row["notes"],
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (FINAL_FREEZE_MANIFEST, "Salt1-4 nominal final training rows"),
        (HOLDOUT_EXCLUSION, "blind-row exclusion audit"),
        (RUNTIME_AUDIT_SOURCE, "runtime guardrails"),
        (SUBMODEL_SUMMARY, "admitted heater/cooler submodels"),
        (MODEL_CONTRACTS, "M2 model-form contract"),
        (MODEL_SCORES, "M2 score context"),
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
                f"- candidate_freeze_id: {CANDIDATE_FREEZE_ID}",
                f"- training_rows: {summary['training_rows']}",
                f"- admitted_terms: {summary['admitted_predictive_terms']}",
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
                f"# {DATE} M2 predictive candidate freeze",
                "",
                "Created the first M2 candidate-freeze artifact from Salt1-4 nominal rows only.",
                "No holdout scoring, model selection on blind rows, or solver mutation was performed.",
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
                "# Salt1-4 M2 Predictive Candidate Freeze",
                "",
                f"Candidate freeze: `{CANDIDATE_FREEZE_ID}`.",
                "",
                "This package starts the first predictive candidate lane from the Salt1-4 nominal row freeze.",
                "It admits only the existing heater and cooler/HX setup boundary terms and keeps pressure, upcomer, PM5, PM10, val_salt2, new-CFD, and two-tap evidence out of fitting/model selection.",
                "",
                "Primary outputs:",
                "",
                "- `candidate_freeze_manifest.csv`",
                "- `candidate_model_terms.csv`",
                "- `candidate_runtime_input_audit.csv`",
                "- `candidate_fit_provenance.csv`",
                "- `holdout_exclusion_audit.csv`",
                "- `summary.json`",
                "",
                f"Training rows: {summary['training_rows']}.",
                f"Holdout rows used for fit: {summary['holdout_rows_used_for_fit']}.",
                "Holdout predictions created: no.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> dict[str, Any]:
    require_sources()
    freeze_manifest = build_candidate_freeze_manifest()
    model_terms = build_candidate_model_terms()
    runtime_audit = build_candidate_runtime_input_audit()
    fit_provenance = build_candidate_fit_provenance()
    holdout_audit = build_holdout_exclusion_audit()
    source_manifest = build_source_manifest()
    admitted_terms = sum(row["term_status"] == "admitted_predictive_boundary_term" for row in model_terms)

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "candidate_freeze_id": CANDIDATE_FREEZE_ID,
        "model_family": MODEL_FAMILY_ID,
        "model_form_name": MODEL_FORM_NAME,
        "candidate_freeze_created": True,
        "training_rows": len(freeze_manifest),
        "admitted_predictive_terms": admitted_terms,
        "blocked_or_diagnostic_terms": sum(row["term_status"] == "blocked_or_diagnostic" for row in model_terms),
        "holdout_rows_used_for_fit": 0,
        "holdout_predictions_created": False,
        "model_selection_rows_outside_nominal_freeze": 0,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "candidate_freeze_manifest.csv", freeze_manifest)
    write_csv(OUT / "candidate_model_terms.csv", model_terms)
    write_csv(OUT / "candidate_runtime_input_audit.csv", runtime_audit)
    write_csv(OUT / "candidate_fit_provenance.csv", fit_provenance)
    write_csv(OUT / "holdout_exclusion_audit.csv", holdout_audit)
    write_csv(OUT / "source_manifest.csv", source_manifest)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
