#!/usr/bin/env python3
"""Build a setup/BC/model-form/error synthesis report from existing evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-15"
    / "2026-07-15_setup_bc_model_error_synthesis_report"
)

AUDIT_DIR = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-14"
    / "2026-07-14_mdot_temperature_probe_error_audit"
)
AGENT420_DIR = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-15"
    / "2026-07-15_mdot_temperature_error_report_and_presentation"
)
ROW_LEDGER_DIR = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-15"
    / "2026-07-15_forward_v1_row_admission_ledger"
)
FLUID_VARIANT_DIR = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-15"
    / "2026-07-15_setup_predictive_heat_loss_fluid_variant"
)
HEAT_REPLAY_DIR = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-15"
    / "2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def float_or_none(value: str) -> float | None:
    if value == "" or value is None:
        return None
    return float(value)


def fmt(value: str | float | int | None, digits: int = 3) -> str:
    if value is None or value == "":
        return ""
    number = float(value)
    if abs(number) >= 1000 or (0 < abs(number) < 0.001):
        return f"{number:.3e}"
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def markdown_table(rows: list[dict[str, object]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return "\n".join([header, sep, *body])


def build_setup_case_summary() -> list[dict[str, object]]:
    source = AUDIT_DIR / "model_config_appendix" / "resolved_case_inputs_salt1_to_salt4.csv"
    rows = []
    for row in read_csv(source):
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "split": row["split"],
                "fit_use": row["fit_use"],
                "cfd_mdot_kg_s": fmt(row["cfd_mdot_kg_s"], 5),
                "cfd_Tmean_K": fmt(row["cfd_Tmean_K"], 2),
                "cfd_loop_delta_T_K": fmt(row["cfd_loop_delta_T_K"], 2),
                "heater_power_W": fmt(row["heater_power_W"], 1),
                "test_section_power_W": fmt(row["test_section_power_W"], 1),
                "boundary_ambient_Ta_K": fmt(row["boundary_ambient_Ta_K"], 2),
                "patch_heat_ledger": row["has_patch_heat_ledger"],
                "notes": row["notes"],
                "source_path": rel(source),
            }
        )
    return rows


def build_mode_matrix() -> list[dict[str, object]]:
    source = AUDIT_DIR / "model_mode_matrix.csv"
    rows = []
    for row in read_csv(source):
        rows.append(
            {
                "mode_id": row["mode_id"],
                "part": row["part"],
                "description": row["description"],
                "solver_policy": row["solver_policy"],
                "predictivity_class": row["predictivity_class"],
                "uses_cfd_mdot_runtime": row["uses_cfd_mdot_runtime"],
                "uses_realized_cfd_wallHeatFlux_runtime": row[
                    "uses_realized_cfd_wallHeatFlux_runtime"
                ],
                "closure_terms": row["closure_terms"],
                "runtime_input_policy": row["runtime_input_policy"],
                "source_path": rel(source),
            }
        )
    return rows


def build_error_by_case() -> list[dict[str, object]]:
    source = AGENT420_DIR / "case_mode_error_table.csv"
    rows = []
    for row in read_csv(source):
        rows.append(
            {
                "case_id": row["case_id"],
                "split": row["split"],
                "mode_id": row["mode_id"],
                "mdot_pred_kg_s": fmt(row["mdot_pred_kg_s"], 5),
                "cfd_mdot_kg_s": fmt(row["cfd_mdot_kg_s"], 5),
                "mdot_error_pct": fmt(row["mdot_error_pct"], 3),
                "all_probe_rmse_K": fmt(row["all_probe_rmse_K"], 3),
                "tp_rmse_K": fmt(row["tp_rmse_K"], 3),
                "tw_rmse_K": fmt(row["tw_rmse_K"], 3),
                "Tmean_error_K": fmt(row["Tmean_error_K"], 3),
                "loop_delta_error_K": fmt(row["loop_delta_error_K"], 3),
                "admission_use_class": row["admission_use_class"],
                "source_path": rel(source),
            }
        )
    return rows


def build_performance_summary() -> list[dict[str, object]]:
    source = AGENT420_DIR / "boundary_mode_performance_summary.csv"
    rows = []
    for row in read_csv(source):
        rows.append(
            {
                "mode_id": row["mode_id"],
                "part": row["part"],
                "label": row["label"],
                "predictivity_class": row["predictivity_class"],
                "mean_abs_mdot_error_pct": fmt(row["mean_abs_mdot_error_pct"], 3),
                "mean_abs_mdot_error_kg_s": fmt(row["mean_abs_mdot_error_kg_s"], 5),
                "mean_all_probe_rmse_K": fmt(row["mean_all_probe_rmse_K"], 3),
                "runtime_input_policy": row["runtime_input_policy"],
                "admission_note": row["admission_note"],
                "source_path": rel(source),
            }
        )
    return rows


def build_heater_cooler_summary() -> list[dict[str, object]]:
    rows = []
    for source in [
        AUDIT_DIR / "part4_cooling_rmse_summary.csv",
        AUDIT_DIR / "part5_heating_rmse_summary.csv",
    ]:
        for row in read_csv(source):
            if row["scope"] != "all_non_salt1":
                continue
            rows.append(
                {
                    "part": row["part"],
                    "leg": row["leg"],
                    "model_form": row["model_form"],
                    "scope": row["scope"],
                    "n_rows": row["n_rows"],
                    "rmse_W": fmt(row["rmse_W"], 3),
                    "mae_W": fmt(row["mae_W"], 3),
                    "mean_error_W": fmt(row["mean_error_W"], 3),
                    "fit_policy": row["fit_policy"],
                    "interpretation": row["interpretation"],
                    "source_path": rel(source),
                }
            )
    return rows


def build_predictive_variant_status() -> list[dict[str, object]]:
    source = FLUID_VARIANT_DIR / "fluid_variant_contract.csv"
    rows = []
    for row in read_csv(source):
        rows.append(
            {
                "field": row["field"],
                "status": row["status"],
                "accepted_values": row["accepted_values"],
                "purpose": row["purpose"],
                "runtime_leakage_risk": row["runtime_leakage_risk"],
                "source_path": rel(source),
            }
        )
    return rows


def build_assumptions() -> list[dict[str, object]]:
    source = AUDIT_DIR / "study_assumption_register.csv"
    return [
        {
            "assumption_id": row["assumption_id"],
            "topic": row["topic"],
            "statement": row["statement"],
            "applies_to_modes": row["applies_to_modes"],
            "risk_or_consequence": row["risk_or_consequence"],
            "source_path": row["source_path"],
        }
        for row in read_csv(source)
    ]


def write_report(
    setup_rows: list[dict[str, object]],
    mode_rows: list[dict[str, object]],
    error_rows: list[dict[str, object]],
    perf_rows: list[dict[str, object]],
    heater_cooler_rows: list[dict[str, object]],
    variant_rows: list[dict[str, object]],
    assumption_rows: list[dict[str, object]],
) -> None:
    perf_lookup = {row["mode_id"]: row for row in perf_rows}
    m1 = perf_lookup["M1_full_cfd_segment_heat_flux_pressure_root"]
    m2 = perf_lookup["M2_cfd_heater_test_section_cooler_pressure_root"]
    m3 = perf_lookup["M3_cfd_heater_cooler_pressure_root"]

    exact_replay_path = HEAT_REPLAY_DIR / "diagnostic_forced_replay_case_summary.csv"
    exact_replay_note = (
        "The exact section-placement replay exists as diagnostic-only evidence; "
        "it forces CFD-realized wallHeatFlux locations and therefore admits zero "
        "predictive rows."
    )
    if exact_replay_path.exists():
        replay_rows = read_csv(exact_replay_path)
        residual_column = next(
            (
                name
                for name in [
                    "max_abs_segment_net_residual_W",
                    "max_abs_residual_W",
                    "model_minus_cfd_realized_net_sum_W",
                ]
                if replay_rows and name in replay_rows[0]
            ),
            None,
        )
        if residual_column:
            max_residual = max(abs(float(row[residual_column])) for row in replay_rows)
            exact_replay_note += f" Its maximum forced residual is {fmt(max_residual)} W."

    report = f"""# Setup, Boundary-Condition, Model-Form, and Error Synthesis

Generated: 2026-07-15

## Executive Answer

The clearest current result is that matching where heat is placed with
CFD-realized values is useful diagnostically, but it is not yet a predictive
model. The pressure-root diagnostic ladder gives these averaged Salt2/Salt3/Salt4
errors:

- M1 full CFD segment heat ledger: mdot mean absolute error
  {m1['mean_abs_mdot_error_pct']} pct and all-probe RMSE
  {m1['mean_all_probe_rmse_K']} K.
- M2 CFD heater + test-section net + cooler: mdot mean absolute error
  {m2['mean_abs_mdot_error_pct']} pct and all-probe RMSE
  {m2['mean_all_probe_rmse_K']} K.
- M3 CFD heater + cooler only: mdot mean absolute error
  {m3['mean_abs_mdot_error_pct']} pct and all-probe RMSE
  {m3['mean_all_probe_rmse_K']} K.

M2 is the best current combined mdot/temperature diagnostic mode. M3 has lower
temperature-probe RMSE, but a worse mdot error, which means the test-section
term is changing buoyancy and hydraulic state rather than being negligible.
M1 is the strongest warning: even full realized segment heat placement leaves a
large thermal-state error in the current 1D state representation.

{exact_replay_note}

## Case Setup

{markdown_table(setup_rows, [
        ('case_id', 'case'),
        ('split', 'split'),
        ('fit_use', 'fit?'),
        ('cfd_mdot_kg_s', 'CFD mdot kg/s'),
        ('cfd_Tmean_K', 'CFD Tmean K'),
        ('cfd_loop_delta_T_K', 'CFD loop dT K'),
        ('heater_power_W', 'heater W'),
        ('test_section_power_W', 'test-section W'),
        ('boundary_ambient_Ta_K', 'Ta K'),
        ('patch_heat_ledger', 'patch heat ledger'),
    ])}

Salt2 is the declared training row, Salt3 is validation, and Salt4 is holdout.
Salt1 is context only in this audit because the consumed source set lacks a
current admitted Salt1 patch heat ledger.

## Boundary Conditions And Model Forms

{markdown_table(mode_rows, [
        ('mode_id', 'mode'),
        ('description', 'description'),
        ('solver_policy', 'solver policy'),
        ('predictivity_class', 'class'),
        ('uses_cfd_mdot_runtime', 'uses CFD mdot'),
        ('uses_realized_cfd_wallHeatFlux_runtime', 'uses realized wallHeatFlux'),
        ('closure_terms', 'model/closure terms'),
    ])}

Interpretation:

- M1 and M1b consume the realized CFD heat ledger and are diagnostic upper-bound
  or isolation studies, not setup-only predictions.
- M2 and M3 solve mdot from pressure balance, but still consume CFD-realized
  heater/cooler/test-section thermal terms. They are diagnostic boundary-form
  comparisons.
- Fixed-mdot rows isolate thermal behavior only and should not be presented as
  hydraulic predictions.

## Resulting Errors

{markdown_table(perf_rows, [
        ('mode_id', 'mode'),
        ('mean_abs_mdot_error_pct', 'mean abs mdot %'),
        ('mean_abs_mdot_error_kg_s', 'mean abs mdot kg/s'),
        ('mean_all_probe_rmse_K', 'mean all-probe RMSE K'),
        ('predictivity_class', 'class'),
    ])}

### Per-Case Error Matrix

{markdown_table(error_rows, [
        ('case_id', 'case'),
        ('split', 'split'),
        ('mode_id', 'mode'),
        ('mdot_pred_kg_s', '1D mdot kg/s'),
        ('cfd_mdot_kg_s', 'CFD mdot kg/s'),
        ('mdot_error_pct', 'mdot error %'),
        ('all_probe_rmse_K', 'all-probe RMSE K'),
        ('tp_rmse_K', 'TP RMSE K'),
        ('tw_rmse_K', 'TW RMSE K'),
        ('Tmean_error_K', 'Tmean error K'),
        ('loop_delta_error_K', 'loop dT error K'),
    ])}

## Heater And Cooler Model-Form Error

{markdown_table(heater_cooler_rows, [
        ('leg', 'leg'),
        ('model_form', 'model form'),
        ('scope', 'scope'),
        ('rmse_W', 'RMSE W'),
        ('mae_W', 'MAE W'),
        ('mean_error_W', 'mean error W'),
        ('fit_policy', 'fit policy'),
    ])}

The cooler model is the strongest immediate boundary-model lever. The current
fixed-mdot airside-HX representation under-removes heat by about 102 W MAE over
Salt2/Salt3/Salt4, while a Salt2-fit constant-UA bulk-drive diagnostic reduces
the all-non-Salt1 RMSE to about 4.64 W. The heater mismatch is smaller but still
important: electrical 1:1 heater power has about 24.63 W RMSE, while a Salt2-fit
heater-efficiency diagnostic transfers to Salt3/Salt4 with about 0.68 W RMSE.

## Setup-Predictive Variant Status

The implemented setup-predictive variant now has the Fluid hooks needed to
replace realized CFD heat-loss replay with setup-only inputs:

{markdown_table(variant_rows, [
        ('field', 'field'),
        ('status', 'status'),
        ('accepted_values', 'accepted values'),
        ('purpose', 'purpose'),
        ('runtime_leakage_risk', 'leakage guardrail'),
    ])}

This is an implementation unlock, not a final admitted predictive score. It
still needs a declared split, fit on training rows only, and validation/holdout
scoring without realized CFD wallHeatFlux, CFD mdot, imposed CFD cooler duty, or
validation temperatures at runtime.

## Assumptions And Guardrails

{markdown_table(assumption_rows, [
        ('assumption_id', 'ID'),
        ('topic', 'topic'),
        ('statement', 'assumption'),
        ('risk_or_consequence', 'risk if violated'),
    ])}

## Presentation-Ready Takeaways

1. The current best combined diagnostic boundary mode is M2, not because it is
   predictive, but because it balances mdot and temperature errors better than
   the other realized-CFD boundary modes.
2. M3 has the best temperature-probe RMSE, but worsens mdot. That tradeoff is
   the evidence that heat placement changes buoyancy and flow, not just sensor
   offsets.
3. Full CFD heat-ledger replay does not solve the 1D state error by itself.
   The model still needs better reference-temperature, wall/shell-drive, and
   thermal-development treatment.
4. Cooler/HX closure is the largest near-term setup-only model improvement.
5. Heater closure is tractable as a scalar efficiency or thermal-resistance
   model, but it must be setup-only before predictive admission.

## Source Paths

- `{rel(AUDIT_DIR)}`
- `{rel(AGENT420_DIR)}`
- `{rel(ROW_LEDGER_DIR)}`
- `{rel(FLUID_VARIANT_DIR)}`
- `{rel(HEAT_REPLAY_DIR)}`
"""
    (OUT_DIR / "report.md").write_text(report, encoding="utf-8")

    readme = f"""# Setup/BC/Model-Form Error Synthesis Report

Task: AGENT-424
Generated: 2026-07-15

This package summarizes the different 1D setup variants, boundary conditions,
modeling assumptions/forms, and resulting mass-flow and TP/TW temperature
errors from existing evidence only. It does not launch OpenFOAM, mutate native
CFD outputs, mutate registry/admission state, or edit external Fluid files.

Open `report.md` first.

## Files

- `report.md`: report-ready synthesis.
- `case_setup_summary.csv`: Salt case setup and split table.
- `boundary_model_matrix.csv`: boundary/mode assumptions and predictivity class.
- `mode_error_summary.csv`: mean mdot and all-probe error by mode.
- `case_mode_error_matrix.csv`: per-case mdot/TP/TW/Tmean/loop-dT errors.
- `heater_cooler_model_form_errors.csv`: heat-added/removed model-form errors.
- `setup_predictive_variant_status.csv`: implemented setup-only Fluid hooks.
- `assumptions_and_guardrails.csv`: assumption register with risks.
- `source_manifest.csv`: exact source paths.
- `summary.json`: machine-readable summary.

## Headline Numbers

- M1 full CFD segment heat ledger: {m1['mean_abs_mdot_error_pct']} pct mean
  absolute mdot error, {m1['mean_all_probe_rmse_K']} K all-probe RMSE.
- M2 CFD heater + test-section net + cooler: {m2['mean_abs_mdot_error_pct']}
  pct mean absolute mdot error, {m2['mean_all_probe_rmse_K']} K all-probe RMSE.
- M3 CFD heater + cooler only: {m3['mean_abs_mdot_error_pct']} pct mean
  absolute mdot error, {m3['mean_all_probe_rmse_K']} K all-probe RMSE.

## Guardrail

Rows that consume realized CFD wallHeatFlux, imposed CFD cooler duty, or CFD
mdot at runtime are diagnostic. They are not final setup-only predictive model
results.
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def write_source_manifest() -> list[dict[str, object]]:
    rows = [
        {
            "label": "primary_mdot_temperature_audit",
            "path": rel(AUDIT_DIR),
            "role": "source audit for case setup, mode matrix, assumptions, and heat model scores",
        },
        {
            "label": "report_ready_mdot_temperature_package",
            "path": rel(AGENT420_DIR),
            "role": "source for presentation-ready mode and per-case error tables",
        },
        {
            "label": "row_admission_ledger",
            "path": rel(ROW_LEDGER_DIR),
            "role": "predictive/diagnostic/admission class guardrails",
        },
        {
            "label": "setup_predictive_heat_loss_variant",
            "path": rel(FLUID_VARIANT_DIR),
            "role": "implemented setup-only Fluid hooks for future predictive variant",
        },
        {
            "label": "diagnostic_forced_heat_loss_replay",
            "path": rel(HEAT_REPLAY_DIR),
            "role": "diagnostic exact CFD-realized section placement replay status",
        },
    ]
    write_csv(OUT_DIR / "source_manifest.csv", rows, ["label", "path", "role"])
    return rows


def build(out_dir: Path = OUT_DIR) -> None:
    global OUT_DIR
    OUT_DIR = out_dir
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    setup_rows = build_setup_case_summary()
    mode_rows = build_mode_matrix()
    error_rows = build_error_by_case()
    perf_rows = build_performance_summary()
    heater_cooler_rows = build_heater_cooler_summary()
    variant_rows = build_predictive_variant_status()
    assumption_rows = build_assumptions()

    write_csv(
        OUT_DIR / "case_setup_summary.csv",
        setup_rows,
        [
            "case_id",
            "source_id",
            "split",
            "fit_use",
            "cfd_mdot_kg_s",
            "cfd_Tmean_K",
            "cfd_loop_delta_T_K",
            "heater_power_W",
            "test_section_power_W",
            "boundary_ambient_Ta_K",
            "patch_heat_ledger",
            "notes",
            "source_path",
        ],
    )
    write_csv(
        OUT_DIR / "boundary_model_matrix.csv",
        mode_rows,
        [
            "mode_id",
            "part",
            "description",
            "solver_policy",
            "predictivity_class",
            "uses_cfd_mdot_runtime",
            "uses_realized_cfd_wallHeatFlux_runtime",
            "closure_terms",
            "runtime_input_policy",
            "source_path",
        ],
    )
    write_csv(
        OUT_DIR / "case_mode_error_matrix.csv",
        error_rows,
        [
            "case_id",
            "split",
            "mode_id",
            "mdot_pred_kg_s",
            "cfd_mdot_kg_s",
            "mdot_error_pct",
            "all_probe_rmse_K",
            "tp_rmse_K",
            "tw_rmse_K",
            "Tmean_error_K",
            "loop_delta_error_K",
            "admission_use_class",
            "source_path",
        ],
    )
    write_csv(
        OUT_DIR / "mode_error_summary.csv",
        perf_rows,
        [
            "mode_id",
            "part",
            "label",
            "predictivity_class",
            "mean_abs_mdot_error_pct",
            "mean_abs_mdot_error_kg_s",
            "mean_all_probe_rmse_K",
            "runtime_input_policy",
            "admission_note",
            "source_path",
        ],
    )
    write_csv(
        OUT_DIR / "heater_cooler_model_form_errors.csv",
        heater_cooler_rows,
        [
            "part",
            "leg",
            "model_form",
            "scope",
            "n_rows",
            "rmse_W",
            "mae_W",
            "mean_error_W",
            "fit_policy",
            "interpretation",
            "source_path",
        ],
    )
    write_csv(
        OUT_DIR / "setup_predictive_variant_status.csv",
        variant_rows,
        [
            "field",
            "status",
            "accepted_values",
            "purpose",
            "runtime_leakage_risk",
            "source_path",
        ],
    )
    write_csv(
        OUT_DIR / "assumptions_and_guardrails.csv",
        assumption_rows,
        [
            "assumption_id",
            "topic",
            "statement",
            "applies_to_modes",
            "risk_or_consequence",
            "source_path",
        ],
    )
    source_rows = write_source_manifest()

    write_report(
        setup_rows,
        mode_rows,
        error_rows,
        perf_rows,
        heater_cooler_rows,
        variant_rows,
        assumption_rows,
    )

    summary = {
        "task": "AGENT-424",
        "generated": "2026-07-15",
        "case_rows": len(setup_rows),
        "mode_rows": len(mode_rows),
        "case_mode_error_rows": len(error_rows),
        "heater_cooler_model_form_rows": len(heater_cooler_rows),
        "source_rows": len(source_rows),
        "headline": {
            "best_combined_diagnostic_mode": "M2_cfd_heater_test_section_cooler_pressure_root",
            "lowest_temperature_rmse_mode": "M3_cfd_heater_cooler_pressure_root",
            "full_heat_ledger_mode_warning": "M1 remains high-error despite realized segment heat ledger",
        },
        "guardrail": (
            "CFD-realized wallHeatFlux, imposed CFD cooler duty, and CFD mdot "
            "runtime consumption are diagnostic, not final setup-only prediction."
        ),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    build()


if __name__ == "__main__":
    main()
