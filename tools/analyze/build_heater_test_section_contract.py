#!/usr/bin/env python3
"""Build a heater/test-section source contract from existing forward-v0 evidence.

This is a synthesis package, not a new Fluid solve. It compares the current
37 W test-section source assumption with heater-only and low-dimensional
calibration interpretations while keeping realized CFD wallHeatFlux evidence
diagnostic-only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract"
FORWARD_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler"
FORWARD_RESULTS = FORWARD_DIR / "forward_v0_results.csv"
FORWARD_VARIANT_SUMMARY = FORWARD_DIR / "forward_v0_variant_summary.csv"
SECTION_HEAT_BALANCE = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv"
)

CASE_HEAT_LEDGER_COLUMNS = [
    "case_id",
    "source_id",
    "heater_setup_power_W",
    "heater_realized_wallHeatFlux_source_W",
    "heater_realized_efficiency_diagnostic",
    "test_section_setup_power_W",
    "test_section_realized_wallHeatFlux_source_W",
    "test_section_realized_external_loss_W",
    "cooler_imposed_or_realized_loss_W",
    "passive_external_realized_loss_W",
    "passive_external_roles",
    "wallHeatFlux_runtime_use",
]

CASE_INTERPRETATION_COLUMNS = [
    "case_id",
    "source_id",
    "heater_setup_power_W",
    "test_section_setup_power_W",
    "model_Tmean_F0_current_37W_K",
    "model_Tmean_F1_heater_only_K",
    "cfd_Tmean_K",
    "F0_Tmean_error_vs_cfd_K",
    "F1_Tmean_error_vs_cfd_K",
    "test_source_sensitivity_K_per_W",
    "equivalent_delta_Q_needed_vs_heater_only_W",
    "equivalent_eta_heater_fit",
    "equivalent_test_section_fluid_fraction_fit",
    "equivalent_test_section_external_loss_fit_W",
    "fit_note",
]

CANDIDATE_COLUMNS = [
    "candidate_id",
    "description",
    "eta_heater",
    "test_section_fluid_fraction",
    "test_section_external_loss_W",
    "parameter_basis",
    "runtime_class",
    "calibration_status",
    "training_rows",
    "heldout_rows",
    "mean_abs_Tmean_error_vs_cfd_K",
    "mean_mdot_error_vs_cfd_kg_s",
    "mean_equivalent_delta_Q_vs_heater_only_W",
    "mean_equivalent_eta_heater",
    "mean_equivalent_test_section_external_loss_W",
    "admissibility",
    "wallHeatFlux_runtime_use",
    "recommendation_status",
    "notes",
]

RECOMMENDATION_COLUMNS = [
    "decision_id",
    "recommendation",
    "basis",
    "next_model_contract",
    "thermal_closure_claim_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def fnum(value: Any, default: float = 0.0) -> float:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def span_text(values: list[float], digits: int = 3) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return f"{values[0]:.{digits}f}"
    return f"mean {mean(values):.{digits}f}; range {min(values):.{digits}f}..{max(values):.{digits}f}"


def heat_ledger_rows(section_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in section_rows:
        grouped.setdefault((row["case_id"], row["source_id"]), []).append(row)

    rows: list[dict[str, Any]] = []
    for (case_id, source_id), case_rows in sorted(grouped.items()):
        by_role = {row["role"]: row for row in case_rows}
        heater = by_role.get("heater", {})
        test_section = by_role.get("test_section", {})
        cooler = by_role.get("cooler", {})
        passive_rows = [
            row
            for row in case_rows
            if row.get("role") not in {"heater", "test_section", "cooler"}
        ]
        heater_setup = fnum(heater.get("imposed_source_W"))
        heater_realized = fnum(heater.get("realized_source_W"))
        test_setup = fnum(test_section.get("imposed_source_W"))
        test_realized_source = fnum(test_section.get("realized_source_W"))
        test_realized_loss = fnum(test_section.get("realized_loss_W"))
        rows.append(
            {
                "case_id": case_id,
                "source_id": source_id,
                "heater_setup_power_W": heater_setup,
                "heater_realized_wallHeatFlux_source_W": heater_realized,
                "heater_realized_efficiency_diagnostic": heater_realized / heater_setup if heater_setup else "",
                "test_section_setup_power_W": test_setup,
                "test_section_realized_wallHeatFlux_source_W": test_realized_source,
                "test_section_realized_external_loss_W": test_realized_loss,
                "cooler_imposed_or_realized_loss_W": fnum(cooler.get("realized_loss_W")),
                "passive_external_realized_loss_W": sum(fnum(row.get("realized_loss_W")) for row in passive_rows),
                "passive_external_roles": ";".join(sorted({row.get("role", "") for row in passive_rows if row.get("role")})),
                "wallHeatFlux_runtime_use": "diagnostic_only_not_forward_runtime_input",
            }
        )
    return rows


def forward_pairs(forward_rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    pairs: dict[str, dict[str, dict[str, str]]] = {}
    for row in forward_rows:
        pairs.setdefault(row["case_id"], {})[row["variant_id"]] = row
    return pairs


def interpretation_rows(
    forward_rows: list[dict[str, str]],
    ledger_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ledger_by_case = {row["case_id"]: row for row in ledger_rows}
    rows: list[dict[str, Any]] = []
    for case_id, variants in sorted(forward_pairs(forward_rows).items()):
        f0 = variants.get("F0_current_fluid_sources")
        f1 = variants.get("F1_heater_only")
        ledger = ledger_by_case.get(case_id, {})
        if not f0 or not f1 or not ledger:
            continue
        heater_power = fnum(ledger.get("heater_setup_power_W"))
        test_power = fnum(ledger.get("test_section_setup_power_W"))
        model_f0 = fnum(f0.get("model_Tmean_proxy_K"))
        model_f1 = fnum(f1.get("model_Tmean_proxy_K"))
        cfd_tmean = fnum(f1.get("cfd_Tmean_K"))
        sensitivity = (model_f0 - model_f1) / test_power if test_power else float("nan")
        equivalent_delta_q = (cfd_tmean - model_f1) / sensitivity if sensitivity else float("nan")
        eta_fit = 1.0 + equivalent_delta_q / heater_power if heater_power else float("nan")
        fraction_fit = equivalent_delta_q / test_power if test_power else float("nan")
        external_loss_fit = max(0.0, -equivalent_delta_q)
        rows.append(
            {
                "case_id": case_id,
                "source_id": ledger["source_id"],
                "heater_setup_power_W": heater_power,
                "test_section_setup_power_W": test_power,
                "model_Tmean_F0_current_37W_K": model_f0,
                "model_Tmean_F1_heater_only_K": model_f1,
                "cfd_Tmean_K": cfd_tmean,
                "F0_Tmean_error_vs_cfd_K": fnum(f0.get("Tmean_error_vs_cfd_K")),
                "F1_Tmean_error_vs_cfd_K": fnum(f1.get("Tmean_error_vs_cfd_K")),
                "test_source_sensitivity_K_per_W": sensitivity,
                "equivalent_delta_Q_needed_vs_heater_only_W": equivalent_delta_q,
                "equivalent_eta_heater_fit": eta_fit,
                "equivalent_test_section_fluid_fraction_fit": fraction_fit,
                "equivalent_test_section_external_loss_fit_W": external_loss_fit,
                "fit_note": "linearized from F0-F1 forward-v0 contrast; calibration candidate only, not a held-out score",
            }
        )
    return rows


def variant_summary_by_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["variant_id"]: row for row in rows}


def candidate_rows(
    variant_summary_rows: list[dict[str, str]],
    interpretation: list[dict[str, Any]],
    ledger: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = variant_summary_by_id(variant_summary_rows)
    f0 = summary.get("F0_current_fluid_sources", {})
    f1 = summary.get("F1_heater_only", {})
    delta_q_values = [fnum(row["equivalent_delta_Q_needed_vs_heater_only_W"]) for row in interpretation]
    eta_fit_values = [fnum(row["equivalent_eta_heater_fit"]) for row in interpretation]
    loss_fit_values = [fnum(row["equivalent_test_section_external_loss_fit_W"]) for row in interpretation]
    realized_eta_values = [fnum(row["heater_realized_efficiency_diagnostic"]) for row in ledger]
    realized_test_losses = [fnum(row["test_section_realized_external_loss_W"]) for row in ledger]

    return [
        {
            "candidate_id": "C0_current_37W_test_source",
            "description": "Current Fluid contract: full heater setup power plus full 37 W test-section fluid source.",
            "eta_heater": "1.0",
            "test_section_fluid_fraction": "1.0",
            "test_section_external_loss_W": "0.0",
            "parameter_basis": "predictive setup values currently encoded in Fluid",
            "runtime_class": "predictive_setup_assumption",
            "calibration_status": "not_calibrated",
            "training_rows": "none",
            "heldout_rows": "none",
            "mean_abs_Tmean_error_vs_cfd_K": f0.get("mean_abs_Tmean_error_vs_cfd_K", ""),
            "mean_mdot_error_vs_cfd_kg_s": f0.get("mean_mdot_error_vs_cfd_kg_s", ""),
            "mean_equivalent_delta_Q_vs_heater_only_W": "",
            "mean_equivalent_eta_heater": "",
            "mean_equivalent_test_section_external_loss_W": "",
            "admissibility": "not_recommended_current_evidence_overheats_forward_v0",
            "wallHeatFlux_runtime_use": "none",
            "recommendation_status": "reject_as_default_next_model",
            "notes": "F0 mean abs CFD Tmean error is far larger than heater-only in the fast scan.",
        },
        {
            "candidate_id": "C1_heater_only_predictive_setup",
            "description": "Use heater setup power only; omit the 37 W test-section source until a train/heldout split admits it.",
            "eta_heater": "1.0",
            "test_section_fluid_fraction": "0.0",
            "test_section_external_loss_W": "0.0",
            "parameter_basis": "predictive setup with no fitted thermal correction",
            "runtime_class": "predictive_setup_assumption",
            "calibration_status": "not_calibrated",
            "training_rows": "none",
            "heldout_rows": "Salt 2/Salt 3/Salt 4 are validation evidence only in this package",
            "mean_abs_Tmean_error_vs_cfd_K": f1.get("mean_abs_Tmean_error_vs_cfd_K", ""),
            "mean_mdot_error_vs_cfd_kg_s": f1.get("mean_mdot_error_vs_cfd_kg_s", ""),
            "mean_equivalent_delta_Q_vs_heater_only_W": "",
            "mean_equivalent_eta_heater": "",
            "mean_equivalent_test_section_external_loss_W": "",
            "admissibility": "recommended_next_unfitted_forward_v0_source_contract",
            "wallHeatFlux_runtime_use": "none",
            "recommendation_status": "recommend_next_admissible_model",
            "notes": "Keeps cooler and passive external losses separate and avoids fitting validation targets.",
        },
        {
            "candidate_id": "C2_calibrated_eta_heater_equivalent",
            "description": "Represent the remaining heater-only overtemperature as a fitted heater transfer efficiency.",
            "eta_heater": span_text(eta_fit_values, digits=4),
            "test_section_fluid_fraction": "0.0",
            "test_section_external_loss_W": "0.0",
            "parameter_basis": "linearized per-case fit to CFD Tmean after comparing F0 and F1",
            "runtime_class": "calibrated_parameter_candidate",
            "calibration_status": "requires_train_heldout_split_before_runtime_use",
            "training_rows": "undefined",
            "heldout_rows": "undefined",
            "mean_abs_Tmean_error_vs_cfd_K": "0 by construction on fitted rows",
            "mean_mdot_error_vs_cfd_kg_s": f1.get("mean_mdot_error_vs_cfd_kg_s", ""),
            "mean_equivalent_delta_Q_vs_heater_only_W": mean(delta_q_values),
            "mean_equivalent_eta_heater": mean(eta_fit_values),
            "mean_equivalent_test_section_external_loss_W": "",
            "admissibility": "not_admissible_for_validation_scoring_until_split",
            "wallHeatFlux_runtime_use": "none",
            "recommendation_status": "defer_to_TODO-PRED-VALIDATION-SPLIT",
            "notes": "Useful one-parameter form if independent heater efficiency evidence or training rows are provided.",
        },
        {
            "candidate_id": "C3_calibrated_test_section_external_loss",
            "description": "Keep heater fully transferred and fit a small test-section external loss.",
            "eta_heater": "1.0",
            "test_section_fluid_fraction": "0.0",
            "test_section_external_loss_W": span_text(loss_fit_values, digits=3),
            "parameter_basis": "linearized per-case fit to CFD Tmean after comparing F0 and F1",
            "runtime_class": "calibrated_parameter_candidate",
            "calibration_status": "requires_train_heldout_split_before_runtime_use",
            "training_rows": "undefined",
            "heldout_rows": "undefined",
            "mean_abs_Tmean_error_vs_cfd_K": "0 by construction on fitted rows",
            "mean_mdot_error_vs_cfd_kg_s": f1.get("mean_mdot_error_vs_cfd_kg_s", ""),
            "mean_equivalent_delta_Q_vs_heater_only_W": mean(delta_q_values),
            "mean_equivalent_eta_heater": "",
            "mean_equivalent_test_section_external_loss_W": mean(loss_fit_values),
            "admissibility": "not_admissible_for_validation_scoring_until_split",
            "wallHeatFlux_runtime_use": "none",
            "recommendation_status": "defer_to_TODO-PRED-VALIDATION-SPLIT",
            "notes": "This form matches the sign of diagnostic CFD test-section wall flux without using that flux as a runtime input.",
        },
        {
            "candidate_id": "C4_test_section_fluid_fraction_fit",
            "description": "Fit the 37 W test-section power as a direct positive fluid-source fraction.",
            "eta_heater": "1.0",
            "test_section_fluid_fraction": span_text([fnum(row["equivalent_test_section_fluid_fraction_fit"]) for row in interpretation], digits=4),
            "test_section_external_loss_W": "0.0",
            "parameter_basis": "linearized per-case fit to CFD Tmean after comparing F0 and F1",
            "runtime_class": "calibrated_parameter_candidate",
            "calibration_status": "invalid_sign_on_current_rows",
            "training_rows": "undefined",
            "heldout_rows": "undefined",
            "mean_abs_Tmean_error_vs_cfd_K": "",
            "mean_mdot_error_vs_cfd_kg_s": f1.get("mean_mdot_error_vs_cfd_kg_s", ""),
            "mean_equivalent_delta_Q_vs_heater_only_W": mean(delta_q_values),
            "mean_equivalent_eta_heater": "",
            "mean_equivalent_test_section_external_loss_W": "",
            "admissibility": "reject_current_rows_need_negative_added_heat",
            "wallHeatFlux_runtime_use": "none",
            "recommendation_status": "reject_as_low_dimensional_source_only_form",
            "notes": "Heater-only is already warmer than CFD Tmean on all three rows, so a positive test-section source cannot repair the bias.",
        },
        {
            "candidate_id": "C5_realized_wallHeatFlux_partition_diagnostic",
            "description": "Diagnostic CFD partition: heater realized transfer efficiency and test-section net external wall loss.",
            "eta_heater": span_text(realized_eta_values, digits=4),
            "test_section_fluid_fraction": "0.0",
            "test_section_external_loss_W": span_text(realized_test_losses, digits=3),
            "parameter_basis": "derived from realized CFD wallHeatFlux section ledger",
            "runtime_class": "diagnostic_only_cfd_evidence",
            "calibration_status": "not_fit_safe_runtime_input",
            "training_rows": "none",
            "heldout_rows": "none",
            "mean_abs_Tmean_error_vs_cfd_K": "",
            "mean_mdot_error_vs_cfd_kg_s": "",
            "mean_equivalent_delta_Q_vs_heater_only_W": "",
            "mean_equivalent_eta_heater": mean(realized_eta_values),
            "mean_equivalent_test_section_external_loss_W": mean(realized_test_losses),
            "admissibility": "not_admissible_as_forward_runtime_input",
            "wallHeatFlux_runtime_use": "diagnostic_only_not_forward_runtime_input",
            "recommendation_status": "use_only_as_sign_and_magnitude_evidence",
            "notes": "Confirms the 37 W test-section fluid-source assumption is suspect, but cannot be consumed by predictive runtime.",
        },
    ]


def recommendation_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "R1_next_admissible_model",
            "recommendation": "Use C1 heater-only as the next unfitted imposed-cooler forward-v0 source contract.",
            "basis": "F1 heater-only reduces mean abs CFD Tmean error from 34.374 K to 4.609 K without adding a fitted parameter.",
            "next_model_contract": "Q_heater_to_fluid = heater_power_W; test_section_fluid_fraction = 0; test_section_external_loss_W = 0 until train/heldout calibration admits a correction; keep cooler duty and passive external losses separate.",
            "thermal_closure_claim_status": "provisional_not_thesis_strength",
        },
        {
            "decision_id": "R2_next_calibration_gate",
            "recommendation": "After a validation split, test either one global eta_heater or one global test_section_external_loss, not both on the same small training set.",
            "basis": "The current three rows need negative added heat relative to heater-only; source-only test-section fraction is the wrong sign.",
            "next_model_contract": "Declare eta_heater or test_section_external_loss as calibrated_parameter with training rows, held-out rows, and uncertainty; do not tune passive external hA to absorb this source-contract error.",
            "thermal_closure_claim_status": "calibration_candidate_only",
        },
    ]


def write_readme(
    out_dir: Path,
    candidates: list[dict[str, Any]],
    interpretations: list[dict[str, Any]],
) -> None:
    c0 = next(row for row in candidates if row["candidate_id"] == "C0_current_37W_test_source")
    c1 = next(row for row in candidates if row["candidate_id"] == "C1_heater_only_predictive_setup")
    delta_q = [fnum(row["equivalent_delta_Q_needed_vs_heater_only_W"]) for row in interpretations]
    readme = f"""# Heater/Test-Section Source Contract

Generated: `{utc_now()}`

Task: `TODO-PRED-HEATER-TEST-CONTRACT`

## Purpose

This package turns the forward-v0 imposed-cooler finding into a small source
contract for the TAMU loop. It compares:

- current 37 W test-section source,
- heater-only setup source,
- heater transfer-efficiency calibration,
- test-section source/external-loss calibration,
- diagnostic realized CFD wallHeatFlux partitioning.

The contract equation is:

```text
Q_to_fluid = eta_heater * P_heater_setup
           + test_section_fluid_fraction * P_test_section_setup
           - test_section_external_loss
           - Q_cooler
           - Q_passive_external
```

`Q_cooler` and `Q_passive_external` stay separate. Realized CFD
`wallHeatFlux` is used only as diagnostic evidence and is not a forward runtime
input.

## Key Result

- `C0_current_37W_test_source`: mean abs CFD Tmean error `{c0["mean_abs_Tmean_error_vs_cfd_K"]} K`.
- `C1_heater_only_predictive_setup`: mean abs CFD Tmean error `{c1["mean_abs_Tmean_error_vs_cfd_K"]} K`.
- Linearized fitted rows require `{span_text(delta_q, digits=3)} W` relative to
  heater-only, i.e. negative added test-section heat on all current rows.

## Recommendation

Use `C1_heater_only_predictive_setup` as the next admissible unfitted model:
`eta_heater = 1`, `test_section_fluid_fraction = 0`, and
`test_section_external_loss_W = 0` until a validation split admits a calibrated
correction.

After `TODO-PRED-VALIDATION-SPLIT`, test either one global `eta_heater` or one
global `test_section_external_loss`, not both on the same small training set.
Do not use realized CFD `wallHeatFlux` as a runtime input, and do not hide this
source-contract issue inside passive external hA.

## Files

- `case_heat_ledger.csv`: heater, test-section, cooler, and passive external
  realized heat ledgers from the fixed-mdot diagnostic package.
- `case_contract_interpretation.csv`: per-case linearized source-contract
  interpretation from the F0/F1 forward-v0 contrast.
- `candidate_parameters.csv`: fit/validation-safe candidate parameter table.
- `recommended_model.csv`: next model and calibration-gate recommendation.
- `summary.json`: machine-readable summary.

## Evidence Boundary

Thermal closure claims remain provisional. The package uses existing
forward-v0 fast-scan outputs and diagnostic section heat balance outputs; it
does not rerun Fluid and does not stage or mutate native CFD solver outputs.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    forward_rows = read_csv(FORWARD_RESULTS)
    variant_summary_rows = read_csv(FORWARD_VARIANT_SUMMARY)
    section_rows = read_csv(SECTION_HEAT_BALANCE)

    ledger = heat_ledger_rows(section_rows)
    interpretations = interpretation_rows(forward_rows, ledger)
    candidates = candidate_rows(variant_summary_rows, interpretations, ledger)
    recommendations = recommendation_rows()

    write_csv(out_dir / "case_heat_ledger.csv", ledger, CASE_HEAT_LEDGER_COLUMNS)
    write_csv(out_dir / "case_contract_interpretation.csv", interpretations, CASE_INTERPRETATION_COLUMNS)
    write_csv(out_dir / "candidate_parameters.csv", candidates, CANDIDATE_COLUMNS)
    write_csv(out_dir / "recommended_model.csv", recommendations, RECOMMENDATION_COLUMNS)

    recommended = next(row for row in candidates if row["recommendation_status"] == "recommend_next_admissible_model")
    f0 = next(row for row in candidates if row["candidate_id"] == "C0_current_37W_test_source")
    diagnostic = next(row for row in candidates if row["candidate_id"] == "C5_realized_wallHeatFlux_partition_diagnostic")
    summary = {
        "generated_at": utc_now(),
        "task_id": "TODO-PRED-HEATER-TEST-CONTRACT",
        "source_paths": {
            "forward_results": rel(FORWARD_RESULTS),
            "forward_variant_summary": rel(FORWARD_VARIANT_SUMMARY),
            "section_heat_balance": rel(SECTION_HEAT_BALANCE),
        },
        "n_cases": len(interpretations),
        "n_candidates": len(candidates),
        "current_37W_mean_abs_Tmean_error_vs_cfd_K": fnum(f0["mean_abs_Tmean_error_vs_cfd_K"]),
        "heater_only_mean_abs_Tmean_error_vs_cfd_K": fnum(recommended["mean_abs_Tmean_error_vs_cfd_K"]),
        "recommended_candidate_id": recommended["candidate_id"],
        "recommended_contract": {
            "eta_heater": recommended["eta_heater"],
            "test_section_fluid_fraction": recommended["test_section_fluid_fraction"],
            "test_section_external_loss_W": recommended["test_section_external_loss_W"],
        },
        "diagnostic_realized_wallHeatFlux_mean_eta_heater": fnum(diagnostic["mean_equivalent_eta_heater"]),
        "diagnostic_realized_wallHeatFlux_mean_test_section_external_loss_W": fnum(
            diagnostic["mean_equivalent_test_section_external_loss_W"]
        ),
        "wallHeatFlux_runtime_policy": "diagnostic_only_not_forward_runtime_input",
        "thermal_closure_claim_status": "provisional",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, candidates, interpretations)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = build_package(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
