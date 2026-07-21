#!/usr/bin/env python3
"""Build reset-distance and named-loss tables for lit-review closure rigor."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from litrev_common import (
    DATE_DIR,
    MINOR_LOSS_TWO_TAP,
    PRESSURE_LEDGER,
    THERMAL_BOUNDARY,
    classify_orientation,
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


TASK_ID = "TODO-LITREV-RESET-NAMED-LOSSES"
OUT_DIR = DATE_DIR / "2026-07-13_litrev_reset_named_losses"
DEFAULT_VALIDITY = DATE_DIR / "2026-07-13_litrev_cfd_validity_diagnostics" / "coefficient_naming_limits.csv"

RESET_FIELDS = [
    "source_id",
    "case_id",
    "feature_or_span",
    "reset_type",
    "downstream_span",
    "orientation",
    "x_from_reset_m",
    "L_over_D_from_reset",
    "thermal_reset_status",
    "hydraulic_reset_status",
    "provenance_author_title",
    "source_path",
    "quality_flags",
]

LOSS_FIELDS = [
    "source_id",
    "case_id",
    "name",
    "loss_class",
    "span_or_feature",
    "pressure_basis",
    "velocity_basis",
    "plane_or_tap_span",
    "included_fittings",
    "delta_p_basis_pa",
    "straight_loss_correction_pa",
    "K_local",
    "K_apparent",
    "f_D_delta_p",
    "fit_use_status",
    "coefficient_naming_status",
    "source_status",
    "provenance_author_title",
    "source_path",
    "quality_flags",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--validity-csv", type=Path, default=DEFAULT_VALIDITY)
    return parser.parse_args()


def validity_lookup(path: Path) -> dict[tuple[str, str, str], str]:
    if not path.exists():
        return {}
    out: dict[tuple[str, str, str], str] = {}
    for row in read_csv(path):
        out[(row["source_id"], row["section"], row["coefficient_family"])] = row["naming_status"]
    return out


def reset_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pressure = read_csv(PRESSURE_LEDGER)
    for row in pressure:
        L = num(row.get("L_m"), 0.0) or 0.0
        D = num(row.get("D_h_m"), 0.0) or 0.0
        flow_reset = str(row.get("flow_reset_flag", "")).lower() == "true"
        rows.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "feature_or_span": row["span"],
                "reset_type": "section_endpoint_or_recent_feature" if flow_reset else "no_local_reset_flag_in_pressure_ledger",
                "downstream_span": row["span"],
                "orientation": classify_orientation(row["span"]),
                "x_from_reset_m": L,
                "L_over_D_from_reset": safe_div(L, D),
                "thermal_reset_status": "unknown_until_wall_material_or_heat_path_reset_mapped",
                "hydraulic_reset_status": "reset_flagged" if flow_reset else "not_flagged_in_pressure_ledger",
                "provenance_author_title": "Shah, A Correlation for Laminar Hydrodynamic Entry Length Solutions for Circular and Noncircular Ducts; Muzychka and Yovanovich, Pressure Drop in Laminar Developing Flow in Noncircular Ducts: A Scaling and Modeling Approach",
                "source_path": rel(PRESSURE_LEDGER),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    for row in read_csv(MINOR_LOSS_TWO_TAP):
        rows.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "feature_or_span": row["feature"],
                "reset_type": row.get("feature_type", "feature"),
                "downstream_span": row.get("downstream_span", ""),
                "orientation": classify_orientation(row.get("downstream_span", "")),
                "x_from_reset_m": 0.0,
                "L_over_D_from_reset": 0.0,
                "thermal_reset_status": "possible_thermal_reset_if_wall_bc_or_geometry_changes",
                "hydraulic_reset_status": "feature_reset_assumed_for_downstream_development_sensitivity",
                "provenance_author_title": "Lin et al., State-of-the-Art Review on Measurement of Pressure Losses of Fluid Flow Through Pipe Fittings; Patino-Jaramillo et al., Laminar Flow and Pressure Loss in Planar Tee Joints: Pressure Loss Coefficients",
                "source_path": rel(MINOR_LOSS_TWO_TAP),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    return rows


def pressure_loss_rows(validity: dict[tuple[str, str, str], str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in read_csv(PRESSURE_LEDGER):
        span = row["span"]
        recirc = str(row.get("recirculation_flag", "")).lower() == "true"
        loss_class = "straight_section" if not recirc and row.get("feature_mask") == "straight_span_only" else "branch_apparent"
        naming = validity.get((row["source_id"], span, "f_D"), "candidate_pending_validity_gate")
        out.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "name": f"{loss_class}:{span}",
                "loss_class": loss_class,
                "span_or_feature": span,
                "pressure_basis": "debuoyed_total_pressure_proxy_from_pressure_term_ledger",
                "velocity_basis": "q_ref_pa_from_pressure_ledger",
                "plane_or_tap_span": f"{row.get('station_start_label','')}->{row.get('station_end_label','')}",
                "included_fittings": row.get("feature_mask", ""),
                "delta_p_basis_pa": row.get("distributed_friction_pa", ""),
                "straight_loss_correction_pa": row.get("distributed_friction_pa", ""),
                "K_local": row.get("minor_loss_K", ""),
                "K_apparent": row.get("minor_loss_K", ""),
                "f_D_delta_p": row.get("f_debuoyed", ""),
                "fit_use_status": row.get("fit_use_status", ""),
                "coefficient_naming_status": naming,
                "source_status": "pressure_ledger_reduction",
                "provenance_author_title": "Lin et al., Measurement Methods and Techniques for Pressure Losses in Pipe Fittings; Muzychka and Yovanovich, Pressure Drop in Laminar Developing Flow in Noncircular Ducts: A Scaling and Modeling Approach",
                "source_path": rel(PRESSURE_LEDGER),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    for row in read_csv(MINOR_LOSS_TWO_TAP):
        feature = row["feature"]
        adjacent = row.get("adjacent_spans", "")
        loss_class = "cluster_K" if ";" in adjacent else "component_K"
        naming = validity.get((row["source_id"], row.get("downstream_span", ""), "K"), "candidate_pending_validity_gate")
        out.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "name": f"{loss_class}:{feature}",
                "loss_class": loss_class,
                "span_or_feature": feature,
                "pressure_basis": "two_tap_total_pressure_feature_loss_minus_buoyancy_dynamic_and_straight_proxy",
                "velocity_basis": row.get("q_ref_basis", ""),
                "plane_or_tap_span": f"{row.get('start_patch','')}->{row.get('end_patch','')}",
                "included_fittings": adjacent,
                "delta_p_basis_pa": row.get("feature_total_pressure_loss_pa", ""),
                "straight_loss_correction_pa": row.get("adjacent_straight_loss_subtracted_pa", ""),
                "K_local": row.get("K_local", ""),
                "K_apparent": row.get("K_apparent", ""),
                "f_D_delta_p": "",
                "fit_use_status": row.get("fit_use_status", ""),
                "coefficient_naming_status": naming,
                "source_status": row.get("status", ""),
                "provenance_author_title": "Lin et al., State-of-the-Art Review on Measurement of Pressure Losses of Fluid Flow Through Pipe Fittings; Salehi et al., Experimental Determination and Computational Fluid Dynamics Predictions of Pressure Loss in Close-Coupled Elbows (RP-1682)",
                "source_path": rel(MINOR_LOSS_TWO_TAP),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    return out


def main() -> None:
    args = parse_args()
    ensure_inputs([PRESSURE_LEDGER, MINOR_LOSS_TWO_TAP])
    validity = validity_lookup(args.validity_csv)
    resets = reset_rows()
    losses = pressure_loss_rows(validity)
    write_csv(args.output_dir / "reset_distance_map.csv", resets, RESET_FIELDS)
    write_csv(args.output_dir / "named_pressure_loss_table.csv", losses, LOSS_FIELDS)
    validation = {
        "reset_rows": len(resets),
        "named_loss_rows": len(losses),
        "input_paths": [rel(PRESSURE_LEDGER), rel(MINOR_LOSS_TWO_TAP), rel(args.validity_csv)],
        "validity_rows_consumed": len(validity),
        "global_friction_multiplier_recommended": False,
    }
    write_json(args.output_dir / "validation_report.json", validation)
    write_json(
        args.output_dir / "summary.json",
        summary_payload(
            TASK_ID,
            args.output_dir,
            len(losses),
            ["reset_distance_map.csv", "named_pressure_loss_table.csv", "validation_report.json"],
            ["No global friction multiplier is recommended; localized resets and named losses remain explicit."],
        ),
    )
    write_readme(
        args.output_dir / "README.md",
        "Lit-Rev Reset Map And Named Losses",
        TASK_ID,
        {
            "Observed Output": f"Built {len(resets)} reset rows and {len(losses)} named pressure-loss rows from the pressure ledger and two-tap minor-loss package.",
            "Inferred Interpretation": "Pressure residuals near bends, clusters, or recirculating sections should be carried as named component/cluster/branch-apparent rows, not hidden in one loop friction multiplier.",
            "Blockers": "Some tap lengths remain proxy lengths from preserved reductions. Thermal reset status is conservative until wall material and heat-path reset locations are explicitly mapped.",
            "Recommended Next Action": "Use `named_pressure_loss_table.csv` with CFD validity naming limits before any section coefficient is exported to the 1D model.",
        },
    )


if __name__ == "__main__":
    main()

