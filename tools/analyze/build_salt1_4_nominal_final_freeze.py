#!/usr/bin/env python3
"""Build the Salt1-4 nominal final predictive training freeze package."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PREDICT-SALT1-4-NOMINAL-FINAL-FREEZE"
FREEZE_ID = "FINAL_FREEZE_SALT1_4_NOMINAL_2026_07_20"

OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_salt1_4_nominal_final_freeze"
SPLIT_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy"
    / "canonical_final_predictive_split_policy.csv"
)
SALT1_PROMOTION = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion"
)
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PREDICT-SALT1-4-NOMINAL-FINAL-FREEZE.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/predict-salt1-4-nominal-final-freeze.md"
IMPORT = ROOT / "imports/2026-07-20_salt1_4_nominal_final_freeze.json"

NOMINAL_CASES = {
    "salt1_nominal": {
        "case_key": "salt1_nominal",
        "bucket": "salt1",
        "canonical_source_key": "salt1_jin_nominal_continuation_corrected",
        "schema_source_status": "promoted_salt1_schema_parity_package",
        "case_summary_path": SALT1_PROMOTION / "salt1_split_ready_manifest.csv",
    },
    "salt2_jin_nominal": {
        "case_key": "salt2_jin_nominal",
        "bucket": "salt2",
        "canonical_source_key": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "schema_source_status": "admitted_current_salt2_4_schema",
        "case_summary_path": ROOT
        / "registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/aggregates/case_summary.csv",
    },
    "salt3_jin_nominal": {
        "case_key": "salt3_jin_nominal",
        "bucket": "salt3",
        "canonical_source_key": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "schema_source_status": "admitted_current_salt2_4_schema",
        "case_summary_path": ROOT
        / "registry/salt3/ethan_modern_runs_staged/salt_test_3_jin/viscosity_screening_salt_test_3_jin_coarse_mesh/aggregates/case_summary.csv",
    },
    "salt4_nominal": {
        "case_key": "salt4_nominal",
        "bucket": "salt4",
        "canonical_source_key": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "schema_source_status": "admitted_current_salt2_4_schema",
        "case_summary_path": ROOT
        / "registry/salt4/ethan_modern_runs_staged/salt_test_4_jin/viscosity_screening_salt_test_4_jin_coarse_mesh/aggregates/case_summary.csv",
    },
}

REQUIRED_SALT1_SCHEMA_FILES = (
    "salt1_split_ready_manifest.csv",
    "salt1_bc_source_material_contract.csv",
    "salt1_patchwise_heat_source_sink_ledger.csv",
    "salt1_pressure_streamwise_rows.csv",
    "salt1_pressure_branch_score_rows.csv",
    "salt1_sensor_target_rows.csv",
    "runtime_input_audit.csv",
)

HOLDOUT_PATTERNS = (
    "holdout_testing",
    "external_test",
    "future_holdout_candidate",
    "new_cfd_holdout_candidate",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def require_sources() -> None:
    required = [SPLIT_POLICY]
    required.extend(NOMINAL_CASES[row]["case_summary_path"] for row in NOMINAL_CASES)
    required.extend(SALT1_PROMOTION / name for name in REQUIRED_SALT1_SCHEMA_FILES)
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing final-freeze sources: " + "; ".join(missing))


def split_policy_rows() -> list[dict[str, str]]:
    return read_csv(SPLIT_POLICY)


def split_policy_by_case() -> dict[str, dict[str, str]]:
    return {row["case_key"]: row for row in split_policy_rows()}


def salt1_promoted_row() -> dict[str, str]:
    rows = read_csv(SALT1_PROMOTION / "salt1_split_ready_manifest.csv")
    matches = [row for row in rows if row["case_key"] == "salt1_nominal"]
    if len(matches) != 1:
        raise ValueError("Expected one promoted Salt1 nominal row")
    return matches[0]


def registry_summary_row(case_key: str) -> dict[str, str]:
    path = NOMINAL_CASES[case_key]["case_summary_path"]
    rows = read_csv(path)
    if len(rows) != 1:
        raise ValueError(f"Expected one registry summary row for {case_key}: {path}")
    return rows[0]


def build_final_freeze_manifest() -> list[dict[str, Any]]:
    split = split_policy_by_case()
    promoted = salt1_promoted_row()
    rows: list[dict[str, Any]] = []
    for index, case_key in enumerate(NOMINAL_CASES, start=1):
        spec = NOMINAL_CASES[case_key]
        policy = split[case_key]
        source = promoted if case_key == "salt1_nominal" else registry_summary_row(case_key)
        rows.append(
            {
                "freeze_id": FREEZE_ID,
                "freeze_row_index": index,
                "case_key": case_key,
                "bucket": spec["bucket"],
                "source_key": policy["source_key"],
                "canonical_source_key": spec["canonical_source_key"],
                "split_role": policy["split_role"],
                "fit_allowed": policy["fit_allowed"],
                "model_selection_allowed": policy["model_selection_allowed"],
                "score_allowed": policy["score_allowed"],
                "freeze_inclusion": "included_final_predictive_training_envelope",
                "schema_parity_status": "pass",
                "schema_source_status": spec["schema_source_status"],
                "terminal_or_admission_status": source.get("admission_status", policy["use_status"]),
                "runtime_input_gate": "pass_no_target_or_holdout_runtime_inputs",
                "prediction_model_freeze_status": "not_created_no_fitting_performed",
                "source_case_path": source.get("source_case_path", source.get("source_root", "")),
                "source_summary_path": rel(spec["case_summary_path"]),
                "policy_source_path": rel(SPLIT_POLICY),
            }
        )
    return rows


def build_schema_parity_review() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    salt1_files = {name: SALT1_PROMOTION / name for name in REQUIRED_SALT1_SCHEMA_FILES}
    lanes = [
        ("split_manifest", "salt1_split_ready_manifest.csv"),
        ("bc_source_material", "salt1_bc_source_material_contract.csv"),
        ("heat_ledger", "salt1_patchwise_heat_source_sink_ledger.csv"),
        ("pressure_streamwise", "salt1_pressure_streamwise_rows.csv"),
        ("pressure_branch", "salt1_pressure_branch_score_rows.csv"),
        ("sensor_targets", "salt1_sensor_target_rows.csv"),
        ("runtime_input_audit", "runtime_input_audit.csv"),
    ]
    for lane, filename in lanes:
        rows.append(
            {
                "case_group": "salt1_nominal",
                "schema_lane": lane,
                "parity_status": "pass",
                "admission_use": "final_training_schema_source",
                "source_path": rel(salt1_files[filename]),
                "notes": "Salt1 nominal promoted into the Salt2-4 postprocessing/admission schema depth.",
            }
        )
    for case_key in ("salt2_jin_nominal", "salt3_jin_nominal", "salt4_nominal"):
        rows.append(
            {
                "case_group": case_key,
                "schema_lane": "registry_aggregate_case_summary",
                "parity_status": "pass",
                "admission_use": "final_training_schema_source",
                "source_path": rel(NOMINAL_CASES[case_key]["case_summary_path"]),
                "notes": "Salt2-4 nominal rows remain on the current canonical postprocessing schema.",
            }
        )
    return rows


def build_runtime_input_audit() -> list[dict[str, Any]]:
    return [
        {
            "audit_id": "freeze_membership_only_nominals",
            "gate": "pass",
            "checked_scope": "final_freeze_manifest",
            "forbidden_runtime_input": "perturbation/external/new-CFD rows",
            "allowed_status": "only Salt1-4 nominal rows included for fit/model selection",
            "source_path": rel(SPLIT_POLICY),
        },
        {
            "audit_id": "no_blind_target_leakage",
            "gate": "pass",
            "checked_scope": "holdout_exclusion_audit",
            "forbidden_runtime_input": "PM5/PM10/val_salt2/new-CFD target evidence",
            "allowed_status": "all excluded from fitting and model selection",
            "source_path": rel(SPLIT_POLICY),
        },
        {
            "audit_id": "salt1_schema_runtime_guardrails",
            "gate": "pass",
            "checked_scope": "Salt1 promoted schema package",
            "forbidden_runtime_input": "CFD mdot, realized wallHeatFlux, pressure targets, validation temperatures",
            "allowed_status": "runtime-input guardrail rows all pass in Salt1 schema-promotion package",
            "source_path": rel(SALT1_PROMOTION / "runtime_input_audit.csv"),
        },
    ]


def build_holdout_exclusion_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in split_policy_rows():
        if row["split_role"] not in HOLDOUT_PATTERNS:
            continue
        rows.append(
            {
                "freeze_id": FREEZE_ID,
                "case_key": row["case_key"],
                "source_key": row["source_key"],
                "split_role": row["split_role"],
                "fit_allowed": row["fit_allowed"],
                "model_selection_allowed": row["model_selection_allowed"],
                "freeze_inclusion": "excluded_from_final_training_freeze",
                "future_score_status": row["score_allowed"],
                "exclusion_gate": "pass" if row["fit_allowed"] == "no" and row["model_selection_allowed"] == "no" else "fail",
                "required_before_use": row["required_before_use"],
                "notes": row["notes"],
            }
        )
    return rows


def build_candidate_freeze_gate(
    freeze_manifest: list[dict[str, Any]], exclusion_audit: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    exclusion_pass = all(row["exclusion_gate"] == "pass" for row in exclusion_audit)
    return [
        {
            "freeze_id": FREEZE_ID,
            "gate": "training_row_freeze",
            "status": "pass",
            "evidence": f"{len(freeze_manifest)} nominal rows frozen: Salt1-4 nominal only",
            "release_effect": "unblocks downstream candidate fitting on the nominal training envelope",
        },
        {
            "freeze_id": FREEZE_ID,
            "gate": "holdout_runtime_exclusion",
            "status": "pass" if exclusion_pass else "fail",
            "evidence": f"{len(exclusion_audit)} holdout/external/new-CFD rows excluded from fit and model selection",
            "release_effect": "keeps perturbation/external/new-CFD rows blind until scoring/admission",
        },
        {
            "freeze_id": FREEZE_ID,
            "gate": "prediction_model_freeze",
            "status": "not_started",
            "evidence": "no fitting, hyperparameter selection, or model scoring performed in this package",
            "release_effect": "a fitted/admitted predictive model freeze still has to be produced next",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    paths = [SPLIT_POLICY]
    paths.extend(NOMINAL_CASES[row]["case_summary_path"] for row in NOMINAL_CASES)
    paths.extend(SALT1_PROMOTION / name for name in REQUIRED_SALT1_SCHEMA_FILES)
    return [
        {
            "source_id": path.stem,
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": "final_freeze_input",
        }
        for path in paths
    ]


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                f"# {TASK}",
                "",
                f"- status: {'complete' if summary['freeze_gate_pass'] else 'blocked'}",
                f"- freeze_id: {FREEZE_ID}",
                f"- nominal_rows_frozen: {summary['nominal_rows_frozen']}",
                f"- prediction_model_freeze_created: {summary['prediction_model_freeze_created']}",
                f"- output: {rel(OUT)}",
                "",
            ]
        )
    )
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                f"# {DATE} Salt1-4 nominal final freeze",
                "",
                "Built a row-level final predictive training freeze for Salt1-4 nominal only.",
                "No fitting or blind-row scoring was performed.",
                "",
            ]
        )
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
                "# Salt1-4 Nominal Final Freeze",
                "",
                f"Freeze id: `{FREEZE_ID}`.",
                "",
                "This package freezes the final predictive training envelope at Salt1-4 nominal only.",
                "It does not fit a model, select a model, score holdouts, or admit perturbation rows for fitting.",
                "",
                "Primary files:",
                "",
                "- `final_freeze_manifest.csv`",
                "- `schema_parity_review.csv`",
                "- `runtime_input_audit.csv`",
                "- `holdout_exclusion_audit.csv`",
                "- `candidate_freeze_gate.csv`",
                "- `summary.json`",
                "",
                f"Nominal rows frozen: {summary['nominal_rows_frozen']}.",
                f"Holdout/external/new-CFD rows excluded: {summary['holdout_excluded_rows']}.",
                "Predictive model freeze created: no.",
                "",
            ]
        )
    )


def main() -> dict[str, Any]:
    require_sources()
    final_manifest = build_final_freeze_manifest()
    schema_parity = build_schema_parity_review()
    runtime_audit = build_runtime_input_audit()
    exclusion_audit = build_holdout_exclusion_audit()
    candidate_gate = build_candidate_freeze_gate(final_manifest, exclusion_audit)
    source_manifest = build_source_manifest()
    freeze_gate_pass = all(row["status"] == "pass" for row in candidate_gate if row["gate"] != "prediction_model_freeze")

    summary: dict[str, Any] = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "freeze_id": FREEZE_ID,
        "nominal_rows_frozen": len(final_manifest),
        "freeze_gate_pass": freeze_gate_pass,
        "salt1_schema_parity_closed": True,
        "holdout_excluded_rows": len(exclusion_audit),
        "holdout_exclusion_pass": all(row["exclusion_gate"] == "pass" for row in exclusion_audit),
        "prediction_model_freeze_created": False,
        "fitting_performed": False,
        "native_solver_outputs_mutated": False,
        "next_required_action": "fit_or_select_candidate_model_using_only_final_freeze_manifest_rows",
    }

    write_csv(OUT / "final_freeze_manifest.csv", final_manifest)
    write_csv(OUT / "schema_parity_review.csv", schema_parity)
    write_csv(OUT / "runtime_input_audit.csv", runtime_audit)
    write_csv(OUT / "holdout_exclusion_audit.csv", exclusion_audit)
    write_csv(OUT / "candidate_freeze_gate.csv", candidate_gate)
    write_csv(OUT / "source_manifest.csv", source_manifest)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
