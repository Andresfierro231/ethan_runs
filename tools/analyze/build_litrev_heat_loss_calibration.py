#!/usr/bin/env python3
"""Build a separated heat-loss calibration ledger from existing artifacts."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from litrev_common import (
    DATE_DIR,
    PREDICTIVE_THERMAL,
    THERMAL_BOUNDARY,
    ensure_inputs,
    num,
    read_csv,
    rel,
    safe_div,
    summary_payload,
    write_csv,
    write_json,
    write_readme,
)


TASK_ID = "TODO-LITREV-HEAT-LOSS-CALIBRATION"
OUT_DIR = DATE_DIR / "2026-07-13_litrev_heat_loss_calibration"

LEDGER_FIELDS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "heat_path",
    "heat_W_positive_to_fluid",
    "absolute_heat_W",
    "term_status",
    "fit_use_status",
    "calibration_admission",
    "provenance_author_title",
    "source_status",
    "source_path",
    "notes",
]

ADMISSION_FIELDS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "Q_jacket_W",
    "Q_passive_convection_W",
    "Q_radiation_bound_W",
    "Q_heater_realized_W",
    "Q_heater_imposed_W",
    "heater_efficiency_realized_over_imposed",
    "Q_wall_storage_W",
    "Q_residual_W",
    "internal_Nu_admission",
    "UA_or_emissivity_admission",
    "quality_flags",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def classify_patch(row: dict[str, str]) -> str:
    role = row.get("role", "").lower()
    segment = row.get("one_d_segment", "").lower()
    if "cool" in role or "cool" in segment:
        return "jacket_or_cooler_removal"
    if "heater" in role or "heated" in segment or "lower_leg" in segment:
        return "heater_or_test_section_input"
    if row.get("bc_type", "") == "rcExternalTemperature":
        return "passive_convection_radiation_inseparable"
    if row.get("bc_type", "") == "externalTemperature":
        return "passive_convection"
    return "junction_or_other_wall_heat"


def build_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_inputs([THERMAL_BOUNDARY, PREDICTIVE_THERMAL])
    ledger: list[dict[str, Any]] = []
    by_segment: dict[tuple[str, str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in read_csv(THERMAL_BOUNDARY):
        key = (row["source_id"], row["case_id"], row.get("one_d_segment", ""))
        path = classify_patch(row)
        q = num(row.get("realized_wallHeatFlux_W"), 0.0) or 0.0
        imposed = num(row.get("imposed_Q_W"))
        by_segment[key][path] += q
        if imposed is not None:
            by_segment[key]["imposed_Q_W"] += imposed
        source_status = (
            "realized_wallHeatFlux_includes_rcExternalTemperature_emissivity_Tsur"
            if row.get("radiation_metadata_status") == "emissivity_and_Tsur_metadata_present"
            else row.get("radiation_metadata_status", "unknown_radiation_metadata")
        )
        ledger.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "one_d_segment": row.get("one_d_segment", ""),
                "heat_path": path,
                "heat_W_positive_to_fluid": q,
                "absolute_heat_W": abs(q),
                "term_status": "observed_realized_wallHeatFlux",
                "fit_use_status": row.get("fit_use_status", "validation_diagnostic"),
                "calibration_admission": "diagnostic_observed_do_not_double_count",
                "provenance_author_title": "VDI Heat Atlas; Reis, Seo, and Hassan, Molten Salt Flow Visualization to Characterize Boundary Layer Behavior and Heat Transfer in a Natural Circulation Loop",
                "source_status": source_status,
                "source_path": rel(THERMAL_BOUNDARY),
                "notes": f"patch={row.get('patch_name','')}; bc_type={row.get('bc_type','')}; role={row.get('role','')}",
            }
        )
    predictive_rows = {(r["source_id"], r["case_id"], r["one_d_segment"]): r for r in read_csv(PREDICTIVE_THERMAL)}
    admission: list[dict[str, Any]] = []
    for key, terms in sorted(by_segment.items()):
        source_id, case_id, segment = key
        pred = predictive_rows.get(key)
        residual = num(pred.get("wallHeatFlux_vs_enthalpy_residual_W") if pred else None)
        jacket = terms.get("jacket_or_cooler_removal", 0.0)
        passive = terms.get("passive_convection", 0.0) + terms.get("passive_convection_radiation_inseparable", 0.0) + terms.get("junction_or_other_wall_heat", 0.0)
        heater = terms.get("heater_or_test_section_input", 0.0)
        imposed = terms.get("imposed_Q_W", 0.0)
        admission.append(
            {
                "source_id": source_id,
                "case_id": case_id,
                "one_d_segment": segment,
                "Q_jacket_W": jacket,
                "Q_passive_convection_W": passive,
                "Q_radiation_bound_W": "inseparable_in_rcExternalTemperature_wallHeatFlux",
                "Q_heater_realized_W": heater,
                "Q_heater_imposed_W": imposed,
                "heater_efficiency_realized_over_imposed": safe_div(heater, imposed),
                "Q_wall_storage_W": "not_observed_steady_window_assumed_small_or_residual",
                "Q_residual_W": residual,
                "internal_Nu_admission": "blocked_from_absorbing_external_heat_loss",
                "UA_or_emissivity_admission": "envelope_labeled_sensitivity_only",
                "quality_flags": "separated_terms_from_existing_wallHeatFlux;no_new_extraction;residual_from_enthalpy_package" if pred else "separated_terms_from_existing_wallHeatFlux;no_enthalpy_residual_match",
            }
        )
    return ledger, admission


def main() -> None:
    args = parse_args()
    ledger, admission = build_ledgers()
    write_csv(args.output_dir / "separated_heat_loss_ledger.csv", ledger, LEDGER_FIELDS)
    write_csv(args.output_dir / "heat_closure_admission.csv", admission, ADMISSION_FIELDS)
    validation = {
        "ledger_rows": len(ledger),
        "admission_rows": len(admission),
        "input_paths": [rel(THERMAL_BOUNDARY), rel(PREDICTIVE_THERMAL)],
        "new_openfoam_extraction_performed": False,
    }
    write_json(args.output_dir / "validation_report.json", validation)
    write_json(
        args.output_dir / "summary.json",
        summary_payload(
            TASK_ID,
            args.output_dir,
            len(ledger),
            ["separated_heat_loss_ledger.csv", "heat_closure_admission.csv", "validation_report.json"],
            ["Radiation is not separated from rcExternalTemperature wallHeatFlux unless a later source/output exposes a distinct qr term."],
        ),
    )
    write_readme(
        args.output_dir / "README.md",
        "Lit-Rev Heat-Loss Calibration Ledger",
        TASK_ID,
        {
            "Observed Output": f"Built {len(ledger)} heat-path rows and {len(admission)} segment admission rows from thermal boundary and predictive heat-loss packages.",
            "Inferred Interpretation": "The ledger keeps cooler/jacket removal, passive losses, heater input, radiation metadata, wall/storage unknowns, and residuals separate. Internal Nu remains blocked from absorbing external heat-loss terms.",
            "Blockers": "The current CFD wallHeatFlux integrates the rcExternalTemperature effect; radiation is metadata-bounded but not a separately observed heat term in this package.",
            "Recommended Next Action": "Use `heat_closure_admission.csv` before any internal HTC/Nu calibration. Add a later radiation-specific row only if a distinct `qr` term or independent surface-radiation estimate is available.",
        },
    )


if __name__ == "__main__":
    main()

