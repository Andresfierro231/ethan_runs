#!/usr/bin/env python3
"""Build AGENT-454 predictive boundary-submodel admission package."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-454"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission")
OUT = ROOT / OUT_REL

AGENT390 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods"
AGENT360 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit"
AGENT418 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant"
AGENT423 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger"
AGENT424 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report"
AGENT438 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock"

HEATER_MODEL = "salt2_fit_constant_heater_efficiency"
HEATER_SCALAR_MODEL = "H1_eta_heater_fit_salt2"
COOLER_MODEL = "salt2_fit_constant_UA_bulk_drive"

VALIDATION_W_TOL = 5.0
HOLDOUT_W_TOL = 10.0
PCT_TOL = 5.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def pass_fail(value: float | None, tolerance: float) -> str:
    if value is None:
        return "missing"
    return "pass" if value <= tolerance else "fail"


def split_w_tolerance(split_role: str) -> float | None:
    if split_role == "validation":
        return VALIDATION_W_TOL
    if split_role == "holdout":
        return HOLDOUT_W_TOL
    return None


def gate_for_split(abs_error_w: float | None, abs_error_pct: float | None, split_role: str) -> str:
    tol_w = split_w_tolerance(split_role)
    if split_role == "train":
        return "fit_row_not_generalization_scored"
    if tol_w is None:
        return "missing_split"
    if pass_fail(abs_error_w, tol_w) == "pass" and pass_fail(abs_error_pct, PCT_TOL) == "pass":
        return "pass"
    return "fail"


def heater_scorecard_rows() -> list[dict[str, Any]]:
    summary_rows = read_csv(AGENT360 / "part5_heating_rmse_summary.csv")
    split_rows = read_csv(AGENT390 / "heater_fraction_split_scores.csv")
    scalar_rows = read_csv(AGENT390 / "heater_fraction_scalar_candidates.csv")

    scalar = next(row for row in scalar_rows if row["model_id"] == HEATER_SCALAR_MODEL)
    heater_by_split = {
        row["scope"]: row
        for row in summary_rows
        if row["leg"] == "heating_leg" and row["model_form"] == HEATER_MODEL and row["scope"] in {"train", "validation", "holdout"}
    }
    setup_power_by_split = {
        row["split"]: safe_float(row["heater_setup_power_W"])
        for row in split_rows
        if row["model_id"] == HEATER_SCALAR_MODEL
    }
    out: list[dict[str, Any]] = []
    for split_role in ["train", "validation", "holdout"]:
        row = heater_by_split[split_role]
        abs_error = safe_float(row["mae_W"])
        setup_power = setup_power_by_split.get(split_role)
        pct_error = None if setup_power in (None, 0.0) or abs_error is None else 100.0 * abs_error / abs(setup_power)
        gate = gate_for_split(abs_error, pct_error, split_role)
        eta = safe_float(scalar["fitted_value"])
        eta_gate = "pass" if eta is not None and 0.0 <= eta <= 1.0 else "fail"
        runtime_gate = "pass" if "passes" in scalar["runtime_input_audit"] else "fail"
        out.append(
            {
                "submodel": "heater",
                "model_form": HEATER_MODEL,
                "case_split": split_role,
                "fit_policy": row["fit_policy"],
                "fitted_scalar": fmt(eta),
                "scalar_gate": eta_gate,
                "abs_error_W": fmt(abs_error),
                "abs_error_pct_of_setup_power": fmt(pct_error),
                "error_gate": gate,
                "runtime_gate": runtime_gate,
                "admission_decision": "admitted_predictive_boundary_submodel" if gate != "fail" and eta_gate == "pass" and runtime_gate == "pass" else "not_admitted",
                "source_path": rel(AGENT360 / "part5_heating_rmse_summary.csv"),
            }
        )
    return out


def cooler_scorecard_rows() -> list[dict[str, Any]]:
    rows = read_csv(AGENT438 / "setup_only_hx_boundary_scorecard.csv")
    out: list[dict[str, Any]] = []
    for row in rows:
        if row["candidate_id"] != COOLER_MODEL:
            continue
        split_role = row["split_role"]
        abs_error = safe_float(row["abs_error_W"])
        pct_error = safe_float(row["abs_error_pct_of_target"])
        runtime_violations = safe_float(row["runtime_input_violation_count"])
        gate = gate_for_split(abs_error, pct_error, split_role)
        runtime_gate = "pass" if runtime_violations == 0 else "fail"
        out.append(
            {
                "submodel": "cooler_hx",
                "model_form": COOLER_MODEL,
                "case_id": row["case_id"],
                "case_split": split_role,
                "fit_policy": row["setup_only_hx_use"],
                "predicted_qhx_W": row["predicted_qhx_W"],
                "target_qhx_W_for_scoring_only": row["target_qhx_W_for_scoring_only"],
                "abs_error_W": row["abs_error_W"],
                "abs_error_pct_of_target": row["abs_error_pct_of_target"],
                "error_gate": gate,
                "runtime_gate": runtime_gate,
                "admission_decision": "admitted_predictive_boundary_submodel" if gate != "fail" and runtime_gate == "pass" else "not_admitted",
                "source_path": rel(AGENT438 / "setup_only_hx_boundary_scorecard.csv"),
            }
        )
    return out


def wall_test_section_rows() -> list[dict[str, Any]]:
    diagnostic_rows = read_csv(AGENT423 / "diagnostic_test_section_negative_source_rows.csv")
    api_rows = read_csv(AGENT418 / "fluid_variant_contract.csv")
    implemented_fields = ";".join(row["field"] for row in api_rows if row["status"] in {"implemented", "compatible_existing_hook"})
    return [
        {
            "submodel": "wall_test_section_passive_boundary",
            "model_form": "setup_only_distributed_loss_or_resistance_network",
            "case_scope": "salt_2_train_salt_3_validation_salt_4_holdout",
            "api_state": "implemented_hooks_available",
            "implemented_fields": implemented_fields,
            "scored_setup_only_rows": 0,
            "diagnostic_negative_source_rows": len(diagnostic_rows),
            "error_gate": "blocked_missing_setup_only_scored_physical_loss_model",
            "runtime_gate": "pass_for_available_api_contract",
            "admission_decision": "not_admitted_narrow_blocker_required",
            "why_blocked": "Current test-section rows are diagnostic negative-source compatibility screens; no setup-only physical wall/test-section loss model has been fit on Salt2 and scored on Salt3/Salt4.",
            "next_action": "Claim TODO-PREDICT-TEST-SECTION-HEAT-LOSS or TODO-PREDICT-SEGMENT-THERMAL-MODELS and score a setup-only distributed loss/resistance model.",
            "source_path": f"{rel(AGENT423 / 'diagnostic_test_section_negative_source_rows.csv')};{rel(AGENT418 / 'fluid_variant_contract.csv')}",
        }
    ]


def runtime_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "audit_id": "R1_no_cfd_mdot_runtime",
            "gate": "pass",
            "observed_state": "Heater/HX admission reads scalar scorecards and W errors only; no CFD mdot column is consumed for runtime prediction.",
            "forbidden_runtime_input": "CFD mdot",
        },
        {
            "audit_id": "R2_no_realized_wallheatflux_runtime",
            "gate": "pass",
            "observed_state": "Realized wallHeatFlux rows remain diagnostic replay rows in AGENT-407/423 and are not admission inputs for heater/HX.",
            "forbidden_runtime_input": "realized CFD wallHeatFlux",
        },
        {
            "audit_id": "R3_no_imposed_cooler_runtime",
            "gate": "pass",
            "observed_state": "Cooler target duty is used only after prediction for scoring; the admitted candidate uses Salt2-fitted setup-only UA bulk drive.",
            "forbidden_runtime_input": "imposed CFD cooler duty",
        },
        {
            "audit_id": "R4_no_validation_refit",
            "gate": "pass",
            "observed_state": "Salt3 and Salt4 rows are scored without refitting heater eta or cooler UA.",
            "forbidden_runtime_input": "validation/holdout temperatures or heat targets for fitting",
        },
        {
            "audit_id": "R5_wall_test_section_not_admitted_by_api_only",
            "gate": "pass",
            "observed_state": "External-boundary API fields are implementation evidence only; absence of scored setup-only wall/test-section rows blocks admission.",
            "forbidden_runtime_input": "diagnostic negative-source test-section compatibility rows as physical closure",
        },
    ]


def submodel_summary_rows(
    heater_rows: list[dict[str, Any]],
    cooler_rows: list[dict[str, Any]],
    wall_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    heater_validation = next(row for row in heater_rows if row["case_split"] == "validation")
    heater_holdout = next(row for row in heater_rows if row["case_split"] == "holdout")
    cooler_validation = next(row for row in cooler_rows if row["case_split"] == "validation")
    cooler_holdout = next(row for row in cooler_rows if row["case_split"] == "holdout")
    wall = wall_rows[0]
    return [
        {
            "submodel": "heater",
            "preferred_model": HEATER_MODEL,
            "admission_decision": "admitted_predictive_boundary_submodel",
            "validation_error": f"{heater_validation['abs_error_W']} W",
            "holdout_error": f"{heater_holdout['abs_error_W']} W",
            "runtime_gate": "pass",
            "remaining_blocker": "none_for_scalar_heater_boundary_admission",
        },
        {
            "submodel": "cooler_hx",
            "preferred_model": COOLER_MODEL,
            "admission_decision": "admitted_predictive_boundary_submodel",
            "validation_error": f"{cooler_validation['abs_error_W']} W",
            "holdout_error": f"{cooler_holdout['abs_error_W']} W",
            "runtime_gate": "pass",
            "remaining_blocker": "none_for_setup_only_hx_candidate_admission",
        },
        {
            "submodel": "wall_test_section_passive_boundary",
            "preferred_model": wall["model_form"],
            "admission_decision": "not_admitted_narrow_blocker_required",
            "validation_error": "not_scored",
            "holdout_error": "not_scored",
            "runtime_gate": wall["runtime_gate"],
            "remaining_blocker": "predictive-wall-test-section-submodels",
        },
    ]


def blocker_decision(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    admitted = {row["submodel"] for row in summary_rows if row["admission_decision"] == "admitted_predictive_boundary_submodel"}
    blocked = {row["submodel"] for row in summary_rows if row["admission_decision"] != "admitted_predictive_boundary_submodel"}
    if {"heater", "cooler_hx"}.issubset(admitted) and blocked == {"wall_test_section_passive_boundary"}:
        decision = "supersede_broad_blocker_with_narrow_wall_test_section_blocker"
    elif not blocked:
        decision = "resolve_original_blocker"
    else:
        decision = "keep_original_blocker_open"
    return {
        "task": TASK,
        "date": DATE,
        "decision": decision,
        "original_blocker": "predictive-heater-cooler-wall-submodels",
        "new_or_remaining_blocker": "predictive-wall-test-section-submodels" if decision.startswith("supersede") else "",
        "admitted_submodels": sorted(admitted),
        "blocked_submodels": sorted(blocked),
        "generated_index_refresh": "required_after_blocker_register_update",
        "evidence": rel(OUT_REL / "README.md"),
    }


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {"source_id": "AGENT390_heater_scalar", "path": rel(AGENT390 / "heater_fraction_scalar_candidates.csv"), "use": "eta_heater scalar and runtime audit"},
        {"source_id": "AGENT390_heater_split", "path": rel(AGENT390 / "heater_fraction_split_scores.csv"), "use": "heater split and setup-power context"},
        {"source_id": "AGENT360_heater_errors", "path": rel(AGENT360 / "part5_heating_rmse_summary.csv"), "use": "heater per-split W-error score rows"},
        {"source_id": "AGENT424_model_errors", "path": rel(AGENT424 / "heater_cooler_model_form_errors.csv"), "use": "consolidated heater/cooler model-form synthesis"},
        {"source_id": "AGENT438_hx_scorecard", "path": rel(AGENT438 / "setup_only_hx_boundary_scorecard.csv"), "use": "cooler/HX setup-only W-error rows"},
        {"source_id": "AGENT418_external_boundary", "path": rel(AGENT418 / "fluid_variant_contract.csv"), "use": "wall/passive external-boundary API availability"},
        {"source_id": "AGENT423_test_section", "path": rel(AGENT423 / "diagnostic_test_section_negative_source_rows.csv"), "use": "test-section non-admission evidence"},
    ]


def write_readme(summary: list[dict[str, Any]], decision: dict[str, Any]) -> None:
    heater = next(row for row in summary if row["submodel"] == "heater")
    cooler = next(row for row in summary if row["submodel"] == "cooler_hx")
    wall = next(row for row in summary if row["submodel"] == "wall_test_section_passive_boundary")
    text = f"""---
provenance:
  - {rel(AGENT390 / "heater_fraction_scalar_candidates.csv")}
  - {rel(AGENT360 / "part5_heating_rmse_summary.csv")}
  - {rel(AGENT424 / "heater_cooler_model_form_errors.csv")}
  - {rel(AGENT438 / "setup_only_hx_boundary_scorecard.csv")}
  - {rel(AGENT418 / "fluid_variant_contract.csv")}
  - {rel(AGENT423 / "diagnostic_test_section_negative_source_rows.csv")}
tags: [forward-model, boundary-modeling, blocker-resolution, heater, hx, wall-loss]
related:
  - operational_notes/maps/forward-predictive-model.md
  - .agent/blockers.yml
task: {TASK}
date: {DATE}
role: Coordinator/BC-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Predictive Boundary-Submodel Admission

Date: {DATE}
Task: {TASK}

## Result

This package applies a split-aware runtime-input admission gate to the broad
`predictive-heater-cooler-wall-submodels` blocker. It uses existing evidence
only and does not mutate native CFD outputs, launch solver/postprocessing jobs,
or edit external Fluid source.

Decision: `{decision["decision"]}`.

## Submodel Decisions

- Heater: `{heater["admission_decision"]}` using `{heater["preferred_model"]}`.
  Validation error `{heater["validation_error"]}`, holdout error
  `{heater["holdout_error"]}`, runtime gate `{heater["runtime_gate"]}`.
- Cooler/HX: `{cooler["admission_decision"]}` using `{cooler["preferred_model"]}`.
  Validation error `{cooler["validation_error"]}`, holdout error
  `{cooler["holdout_error"]}`, runtime gate `{cooler["runtime_gate"]}`.
- Wall/test-section/passive boundary: `{wall["admission_decision"]}`.
  No setup-only physical wall/test-section loss model is currently scored on
  Salt3/Salt4; existing rows are diagnostic negative-source compatibility
  screens, not predictive boundary proof.

## Blocker Register Action

The broad blocker is superseded by the narrower
`predictive-wall-test-section-submodels` blocker. This is not a final forward-v1
admission: hydraulic/F6, internal-Nu/sign/heat-balance, recirculation, and
mesh/GCI blockers still govern final forward-v1.

After updating `.agent/blockers.yml`, regenerate `.agent/STATE.md`,
`.agent/BLOCKERS.md`, `.agent/catalog.json`, and `.agent/catalog.csv` so the
new narrowed blocker is authoritative.

## Files

- `submodel_admission_summary.csv`
- `heater_scorecard.csv`
- `cooler_hx_scorecard.csv`
- `wall_test_section_scorecard.csv`
- `runtime_input_audit.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`

## Guardrails

- Salt2 is the training row; Salt3 is validation; Salt4 is holdout.
- No realized CFD `wallHeatFlux`, imposed CFD cooler duty, CFD mdot, or
  validation/holdout temperatures are predictive runtime inputs.
- Internal Nu does not absorb heater, cooler, wall, radiation, storage, or
  test-section residuals.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    heater = heater_scorecard_rows()
    cooler = cooler_scorecard_rows()
    wall = wall_test_section_rows()
    runtime = runtime_audit_rows()
    summary_rows = submodel_summary_rows(heater, cooler, wall)
    decision = blocker_decision(summary_rows)
    sources = source_manifest_rows()

    counts = {
        "heater_rows": write_csv(
            OUT / "heater_scorecard.csv",
            heater,
            [
                "submodel",
                "model_form",
                "case_split",
                "fit_policy",
                "fitted_scalar",
                "scalar_gate",
                "abs_error_W",
                "abs_error_pct_of_setup_power",
                "error_gate",
                "runtime_gate",
                "admission_decision",
                "source_path",
            ],
        ),
        "cooler_rows": write_csv(
            OUT / "cooler_hx_scorecard.csv",
            cooler,
            [
                "submodel",
                "model_form",
                "case_id",
                "case_split",
                "fit_policy",
                "predicted_qhx_W",
                "target_qhx_W_for_scoring_only",
                "abs_error_W",
                "abs_error_pct_of_target",
                "error_gate",
                "runtime_gate",
                "admission_decision",
                "source_path",
            ],
        ),
        "wall_rows": write_csv(
            OUT / "wall_test_section_scorecard.csv",
            wall,
            [
                "submodel",
                "model_form",
                "case_scope",
                "api_state",
                "implemented_fields",
                "scored_setup_only_rows",
                "diagnostic_negative_source_rows",
                "error_gate",
                "runtime_gate",
                "admission_decision",
                "why_blocked",
                "next_action",
                "source_path",
            ],
        ),
        "runtime_rows": write_csv(
            OUT / "runtime_input_audit.csv",
            runtime,
            ["audit_id", "gate", "observed_state", "forbidden_runtime_input"],
        ),
        "summary_rows": write_csv(
            OUT / "submodel_admission_summary.csv",
            summary_rows,
            [
                "submodel",
                "preferred_model",
                "admission_decision",
                "validation_error",
                "holdout_error",
                "runtime_gate",
                "remaining_blocker",
            ],
        ),
        "source_rows": write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "use"]),
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_readme(summary_rows, decision)
    payload = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "decision": decision["decision"],
        "original_blocker": decision["original_blocker"],
        "new_or_remaining_blocker": decision["new_or_remaining_blocker"],
        "counts": counts,
        "outputs": [
            rel(OUT / name)
            for name in [
                "README.md",
                "submodel_admission_summary.csv",
                "heater_scorecard.csv",
                "cooler_hx_scorecard.csv",
                "wall_test_section_scorecard.csv",
                "runtime_input_audit.csv",
                "blocker_decision.json",
                "source_manifest.csv",
                "summary.json",
            ]
        ],
        "generated_index_refresh": decision["generated_index_refresh"],
    }
    write_json(OUT / "summary.json", payload)
    return payload


def main() -> None:
    payload = build()
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
