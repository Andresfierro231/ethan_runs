#!/usr/bin/env python3
"""Build the AGENT-407 forward-v1 row-admission ledger.

The ledger is a guardrail artifact: it separates setup-legal predictive
candidate rows from diagnostic replays, diagnostic upper bounds, and blocked
fit families. It does not mutate admission state and does not promote any row
to final forward-v1 use.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger"

AG391 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run"
AG392 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/results"
AG403 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_plan_implementation_closeout"
AG404 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_matched_plane_parser_repair"

COOLER_SCORES = AG391 / "setup_only_cooler_closure_bakeoff/cooler_model_scores.csv"
COOLER_SUMMARY = AG391 / "setup_only_cooler_closure_bakeoff/cooler_rmse_summary_with_leakage_policy.csv"
TEST_SECTION_LEDGER = AG391 / "test_section_boundary_form_bakeoff/test_section_model_result_ledger.csv"
HX_PRIMARY = AG392 / "predictive_hx_fit_setup_only_refresh/hx_primary_forward_scores.csv"
HX_DUTY = AG392 / "predictive_hx_fit_setup_only_refresh/hx_duty_scores.csv"
HX_VIOLATIONS = AG392 / "predictive_hx_fit_setup_only_refresh/violations.csv"
EXT_ADMISSION = AG392 / "external_bc_thermal_profile_parity_refresh/admission_decision_table.csv"
EXT_SECTION_HEAT = AG392 / "external_bc_thermal_profile_parity_refresh/section_heat_loss_comparison.csv"
BEST_LEG_HEAT = AG392 / "best_predictive_heat_loss_discrepancy_refresh/best_predictive_leg_heat_loss_discrepancy.csv"
AG319_JOURNAL = ROOT / ".agent/journal/2026-07-14/thermal-admission-internal-nu-final-gate.md"
AG330_JOURNAL = ROOT / ".agent/journal/2026-07-14/upcomer-recirculation-internal-nu-admissibility.md"
AG404_SUMMARY = AG404 / "summary.json"

LEDGER_FIELDS = [
    "row_family",
    "case_id",
    "split_role",
    "model_form",
    "runtime_inputs_allowed",
    "fit_source",
    "score_source",
    "admission_class",
    "forward_v1_use",
    "blocker",
    "source_path",
]

ALLOWED_CLASSES = {
    "predictive_candidate",
    "diagnostic_replay",
    "diagnostic_upper_bound",
    "blocked_empty_fit_set",
    "not_admitted",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: str | float | int | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def case_split(case_id: str) -> str:
    return {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}.get(case_id, "")


def build_hx_closure_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(COOLER_SCORES):
        if row.get("model_form") != "salt2_fit_constant_UA_bulk_drive":
            continue
        rows.append(
            {
                "candidate_id": "salt2_fit_constant_UA_bulk_drive",
                "case_id": row["case_id"],
                "split_role": row["split"],
                "model_form": row["model_form"],
                "predicted_qhx_W": row.get("q_pred_W", ""),
                "target_qhx_W": row.get("q_cfd_W", ""),
                "abs_error_W": row.get("abs_error_W", ""),
                "runtime_input_violation_count": "0",
                "admission_class": "predictive_candidate",
                "forward_v1_use": "preferred_setup_legal_hx_candidate_pending_terminal_scorecard",
                "source_path": rel(COOLER_SCORES),
            }
        )

    for row in read_csv(HX_PRIMARY):
        if row.get("split_id") != "declared_train_salt2_validate_salt3_holdout_salt4":
            continue
        if row.get("variant_id") != "F1_heater_only":
            continue
        if row.get("model_form_id") != "HX1_global_qhx_multiplier_on_fluid_airside":
            continue
        abs_error = abs(fnum(row.get("qhx_error_W")) or 0.0)
        rows.append(
            {
                "candidate_id": "F1_heater_only_plus_HX1_global_qhx_multiplier_on_fluid_airside",
                "case_id": row["case_id"],
                "split_role": row["fit_role"],
                "model_form": "F1_heater_only + HX1_global_qhx_multiplier_on_fluid_airside",
                "predicted_qhx_W": row.get("predicted_qhx_total_W", ""),
                "target_qhx_W": row.get("target_cooler_removed_W", ""),
                "abs_error_W": fmt(abs_error),
                "runtime_input_violation_count": str(len(read_csv(HX_VIOLATIONS))),
                "admission_class": "predictive_candidate",
                "forward_v1_use": "secondary_reconciliation_candidate_not_promoted",
                "source_path": rel(HX_PRIMARY),
            }
        )
    return rows


def build_hx_reconciliation_rows(hx_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted({row["candidate_id"] for row in hx_rows}):
        candidate_rows = [row for row in hx_rows if row["candidate_id"] == candidate_id]
        by_split = {row["split_role"]: fnum(row.get("abs_error_W")) for row in candidate_rows}
        errors = [value for value in by_split.values() if value is not None]
        rmse = math.sqrt(sum(value * value for value in errors) / len(errors)) if errors else None
        mae = sum(errors) / len(errors) if errors else None
        decision = (
            "preferred_current_candidate"
            if candidate_id == "salt2_fit_constant_UA_bulk_drive"
            else "keep_as_secondary_reconciliation_candidate"
        )
        rows.append(
            {
                "candidate_id": candidate_id,
                "train_abs_error_W": fmt(by_split.get("train")),
                "validation_abs_error_W": fmt(by_split.get("validation")),
                "holdout_abs_error_W": fmt(by_split.get("holdout")),
                "all_non_salt1_rmse_W": fmt(rmse),
                "all_non_salt1_mae_W": fmt(mae),
                "runtime_input_violation_count": str(len(read_csv(HX_VIOLATIONS))),
                "decision": decision,
                "source_path": ";".join(sorted({row["source_path"] for row in candidate_rows})),
            }
        )
    return rows


def build_internal_nu_rows() -> list[dict[str, Any]]:
    pm5 = read_json(AG404_SUMMARY)
    return [
        {
            "fit_row_id": "internal_nu_fit_admitted_rows",
            "case_family": "salt_2_to_salt_4",
            "admitted_row_count": "0",
            "admission_class": "blocked_empty_fit_set",
            "blocker": "AGENT-319 reports 0 fit-eligible rows; AGENT-330 reports all current upcomer evidence is recirculating and missing wall-bulk/Gz/onset anchors.",
            "unlock_dependency": "finish matched upcomer plane extraction, recover wallHeatFlux, add non-recirculating or transition anchors, and pass mesh/time uncertainty gates",
            "wallHeatFlux_rows": str(pm5.get("wallHeatFlux_rows", "unknown")),
            "pm5_internal_nu_wallHeatFlux_blocked": str(pm5.get("internal_nu_wallHeatFlux_blocked", "unknown")).lower(),
            "source_path": ";".join([rel(AG319_JOURNAL), rel(AG330_JOURNAL), rel(AG404_SUMMARY)]),
        }
    ]


def build_realized_wall_heat_flux_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(BEST_LEG_HEAT):
        rows.append(
            {
                "case_id": row["case_id"],
                "split_role": case_split(row["case_id"]),
                "leg": row["leg"],
                "model_form": row["best_model_variant"],
                "model_total_loss_W": row.get("model_total_loss_W", ""),
                "cfd_realized_loss_W": row.get("cfd_realized_loss_W", ""),
                "model_minus_cfd_realized_loss_W": row.get("model_minus_cfd_realized_loss_W", ""),
                "admission_class": "diagnostic_replay",
                "forward_v1_use": "residual_localization_and_sign_policy_only",
                "blocker": "realized_wallHeatFlux_is_CFD_output_and_radiation_is_inseparable_inside_total_flux",
                "source_path": rel(BEST_LEG_HEAT),
            }
        )
    return rows


def build_imposed_cooler_rows() -> list[dict[str, Any]]:
    wanted = {"imposed_cfd_cooler_upper_bound", "salt2_fit_cooler_imposed_ratio"}
    rows = []
    for row in read_csv(COOLER_SCORES):
        if row.get("model_form") not in wanted:
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "split_role": row["split"],
                "model_form": row["model_form"],
                "predicted_qhx_W": row.get("q_pred_W", ""),
                "target_qhx_W": row.get("q_cfd_W", ""),
                "abs_error_W": row.get("abs_error_W", ""),
                "admission_class": "diagnostic_upper_bound",
                "forward_v1_use": "leakage_warning_or_best_possible_cooler_bound_only",
                "blocker": "uses CFD imposed/realized cooler evidence; never report as predictive HX closure",
                "source_path": rel(COOLER_SCORES),
            }
        )
    return rows


def build_test_section_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(TEST_SECTION_LEDGER):
        if row.get("mode_id") != "negative_source_compatibility":
            continue
        rows.append(
            {
                "case_id": row["case_id"],
                "split_role": row["split"],
                "model_form": row["mode_id"],
                "mdot_error_pct": row.get("mdot_error_pct", ""),
                "Tmean_error_K": row.get("Tmean_error_K", ""),
                "admission_class": "diagnostic_replay",
                "forward_v1_use": "boundary_form_screen_and_residual_localization_only",
                "blocker": "compatibility check is not physical boundary-condition proof and not a predictive source model",
                "source_path": rel(TEST_SECTION_LEDGER),
            }
        )
    return rows


def ledger_row(
    row_family: str,
    case_id: str,
    split_role: str,
    model_form: str,
    runtime_inputs_allowed: str,
    fit_source: str,
    score_source: str,
    admission_class: str,
    forward_v1_use: str,
    blocker: str,
    source_path: str,
) -> dict[str, Any]:
    if admission_class not in ALLOWED_CLASSES:
        raise ValueError(f"unexpected admission class: {admission_class}")
    return {
        "row_family": row_family,
        "case_id": case_id,
        "split_role": split_role,
        "model_form": model_form,
        "runtime_inputs_allowed": runtime_inputs_allowed,
        "fit_source": fit_source,
        "score_source": score_source,
        "admission_class": admission_class,
        "forward_v1_use": forward_v1_use,
        "blocker": blocker,
        "source_path": source_path,
    }


def build_ledger(
    hx_rows: list[dict[str, Any]],
    internal_rows: list[dict[str, Any]],
    realized_rows: list[dict[str, Any]],
    imposed_rows: list[dict[str, Any]],
    test_section_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in hx_rows:
        rows.append(
            ledger_row(
                "predictive_hx_closure",
                row["case_id"],
                row["split_role"],
                row["model_form"],
                "setup geometry, fit scalar, and model-predicted bulk/external drive only; no validation target or realized CFD cooler duty at runtime",
                "Salt2-only fit",
                "Salt3 validation and Salt4 holdout without refit",
                "predictive_candidate",
                row["forward_v1_use"],
                "terminal hydraulic/cfd-pp/internal gates still block final forward-v1 promotion",
                row["source_path"],
            )
        )
    for row in internal_rows:
        rows.append(
            ledger_row(
                "fitted_internal_nu",
                row["case_family"],
                "not_applicable",
                "fitted_internal_Nu_rows",
                "none",
                "no fit set admitted",
                "no predictive score",
                "blocked_empty_fit_set",
                "blocked_from_forward_v1_closure_fit",
                row["blocker"],
                row["source_path"],
            )
        )
    for row in realized_rows:
        rows.append(
            ledger_row(
                "realized_wallHeatFlux_replay",
                row["case_id"],
                row["split_role"],
                f"{row['model_form']}:{row['leg']}",
                "diagnostic consumption of CFD realized wallHeatFlux only",
                "not_fit",
                "section heat-loss comparison",
                "diagnostic_replay",
                row["forward_v1_use"],
                row["blocker"],
                row["source_path"],
            )
        )
    for row in imposed_rows:
        rows.append(
            ledger_row(
                "imposed_cooler_duty",
                row["case_id"],
                row["split_role"],
                row["model_form"],
                "CFD cooler duty consumed; predictive runtime not allowed",
                "Salt2 or direct CFD-duty construction",
                "Salt3/Salt4 leakage benchmark",
                "diagnostic_upper_bound",
                row["forward_v1_use"],
                row["blocker"],
                row["source_path"],
            )
        )
    for row in test_section_rows:
        rows.append(
            ledger_row(
                "test_section_negative_source",
                row["case_id"],
                row["split_role"],
                row["model_form"],
                "diagnostic source-form replay only",
                "not_fit",
                "compatibility screen",
                "diagnostic_replay",
                row["forward_v1_use"],
                row["blocker"],
                row["source_path"],
            )
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        ("AGENT-391 cooler scores", COOLER_SCORES, "setup-only cooler closure and imposed-cooler diagnostic rows"),
        ("AGENT-391 cooler summary", COOLER_SUMMARY, "candidate leakage policy and RMSE/MAE cross-check"),
        ("AGENT-391 test-section ledger", TEST_SECTION_LEDGER, "negative-source compatibility diagnostic rows"),
        ("AGENT-392 HX primary scores", HX_PRIMARY, "F1+HX1 setup-only HX candidate scores"),
        ("AGENT-392 HX violations", HX_VIOLATIONS, "runtime-input audit violation count"),
        ("AGENT-392 external parity decisions", EXT_ADMISSION, "realized wallHeatFlux replay and radiation policy"),
        ("AGENT-392 heat-loss discrepancy", BEST_LEG_HEAT, "leg-by-leg realized heat-loss diagnostic rows"),
        ("AGENT-319 internal-Nu gate", AG319_JOURNAL, "zero fit-admissible thermal/internal-Nu rows"),
        ("AGENT-330 upcomer admissibility", AG330_JOURNAL, "recirculation/onset blockers and coefficient guardrails"),
        ("AGENT-404 PM5 parser summary", AG404_SUMMARY, "wallHeatFlux still missing for internal-Nu/F6"),
        ("AGENT-403 plan closeout", AG403 / "README.md", "final forward-v1 still blocked; candidate lanes only"),
    ]
    return [
        {"source_id": source_id, "path": rel(path), "exists": str(path.exists()).lower(), "use": use}
        for source_id, path, use in sources
    ]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""# Forward-v1 Row Admission Ledger

Task: AGENT-407  
Generated: 2026-07-15

## Result

This package creates one canonical row-admission ledger for forward-v1 thermal
and HX evidence. It does not admit final forward-v1. The only predictive lane
kept open is a setup-legal HX/cooler candidate lane; realized wallHeatFlux,
imposed cooler duty, and negative test-section source rows are diagnostic only.
Fitted internal Nu has zero admitted rows.

## Current Classification

- Predictive candidate rows: {summary["admission_class_counts"].get("predictive_candidate", 0)}
- Diagnostic replay rows: {summary["admission_class_counts"].get("diagnostic_replay", 0)}
- Diagnostic upper-bound rows: {summary["admission_class_counts"].get("diagnostic_upper_bound", 0)}
- Blocked empty-fit rows: {summary["admission_class_counts"].get("blocked_empty_fit_set", 0)}
- Not-admitted rows: {summary["admission_class_counts"].get("not_admitted", 0)}

Preferred setup-legal HX candidate:
`{summary["preferred_setup_legal_hx_candidate"]}`.

## Method

1. Read AGENT-391 cooler/test-section outputs and AGENT-392 HX/external-BC
   outputs without rerunning Fluid, OpenFOAM, or scheduler jobs.
2. Classify each row using the allowed classes:
   `predictive_candidate`, `diagnostic_replay`, `diagnostic_upper_bound`,
   `blocked_empty_fit_set`, or `not_admitted`.
3. Require predictive HX rows to fit on Salt2 and score Salt3/Salt4 without
   refit or runtime use of realized/imposed CFD cooler duty.
4. Keep realized wallHeatFlux rows as diagnostic replay only because CFD
   `rcExternalTemperature` radiation is inseparable in total wall flux.
5. Keep internal Nu blocked because AGENT-319 reports zero fit-eligible rows,
   AGENT-330 reports recirculating/missing-anchor evidence, and AGENT-404 still
   has `wallHeatFlux_rows=0`.

## Files

- `row_admission_ledger.csv`: canonical row family table requested by the user.
- `final_predictive_hx_closure_rows.csv`: Salt2/Salt3/Salt4 HX candidate rows.
- `hx_candidate_reconciliation.csv`: side-by-side candidate decision table.
- `internal_nu_fit_rows.csv`: explicit zero-admitted internal-Nu blocker row.
- `realized_wallHeatFlux_replay_rows.csv`: leg heat-loss replay diagnostics.
- `imposed_cooler_diagnostic_rows.csv`: upper-bound/leakage rows.
- `test_section_negative_source_rows.csv`: compatibility-screen rows.
- `source_manifest.csv`: exact provenance paths.

## Guardrails

No native CFD solver outputs, scheduler state, registry/admission state, or
external `../cfd-modeling-tools` files were mutated. Repair-smoke, replay, and
leakage rows remain separate from closure admission.
"""


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    hx_rows = build_hx_closure_rows()
    hx_reconciliation = build_hx_reconciliation_rows(hx_rows)
    internal_rows = build_internal_nu_rows()
    realized_rows = build_realized_wall_heat_flux_rows()
    imposed_rows = build_imposed_cooler_rows()
    test_section_rows = build_test_section_rows()
    ledger = build_ledger(hx_rows, internal_rows, realized_rows, imposed_rows, test_section_rows)
    sources = build_source_manifest()

    class_counts = {class_name: 0 for class_name in sorted(ALLOWED_CLASSES)}
    for row in ledger:
        class_counts[row["admission_class"]] += 1

    summary = {
        "task": "AGENT-407",
        "date": "2026-07-15",
        "ledger_rows": len(ledger),
        "admission_class_counts": class_counts,
        "preferred_setup_legal_hx_candidate": "salt2_fit_constant_UA_bulk_drive",
        "hx_candidate_rows": len(hx_rows),
        "internal_nu_admitted_rows": 0,
        "internal_nu_status": "blocked_empty_fit_set",
        "wallHeatFlux_replay_status": "diagnostic_only_not_predictive_runtime",
        "imposed_cooler_status": "diagnostic_upper_bound_not_predictive",
        "test_section_negative_source_status": "diagnostic_replay_not_physical_bc_proof",
        "runtime_input_audit_violations": len(read_csv(HX_VIOLATIONS)),
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "native_cfd_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "scheduler_mutated": False,
        "registry_or_admission_state_mutated": False,
        "source_count": len(sources),
    }

    write_csv(output_dir / "row_admission_ledger.csv", ledger, LEDGER_FIELDS)
    write_csv(
        output_dir / "final_predictive_hx_closure_rows.csv",
        hx_rows,
        [
            "candidate_id",
            "case_id",
            "split_role",
            "model_form",
            "predicted_qhx_W",
            "target_qhx_W",
            "abs_error_W",
            "runtime_input_violation_count",
            "admission_class",
            "forward_v1_use",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "hx_candidate_reconciliation.csv",
        hx_reconciliation,
        [
            "candidate_id",
            "train_abs_error_W",
            "validation_abs_error_W",
            "holdout_abs_error_W",
            "all_non_salt1_rmse_W",
            "all_non_salt1_mae_W",
            "runtime_input_violation_count",
            "decision",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "internal_nu_fit_rows.csv",
        internal_rows,
        [
            "fit_row_id",
            "case_family",
            "admitted_row_count",
            "admission_class",
            "blocker",
            "unlock_dependency",
            "wallHeatFlux_rows",
            "pm5_internal_nu_wallHeatFlux_blocked",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "realized_wallHeatFlux_replay_rows.csv",
        realized_rows,
        [
            "case_id",
            "split_role",
            "leg",
            "model_form",
            "model_total_loss_W",
            "cfd_realized_loss_W",
            "model_minus_cfd_realized_loss_W",
            "admission_class",
            "forward_v1_use",
            "blocker",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "imposed_cooler_diagnostic_rows.csv",
        imposed_rows,
        [
            "case_id",
            "split_role",
            "model_form",
            "predicted_qhx_W",
            "target_qhx_W",
            "abs_error_W",
            "admission_class",
            "forward_v1_use",
            "blocker",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "test_section_negative_source_rows.csv",
        test_section_rows,
        [
            "case_id",
            "split_role",
            "model_form",
            "mdot_error_pct",
            "Tmean_error_K",
            "admission_class",
            "forward_v1_use",
            "blocker",
            "source_path",
        ],
    )
    write_csv(output_dir / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(build_readme(summary), encoding="utf-8")

    return summary


def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
