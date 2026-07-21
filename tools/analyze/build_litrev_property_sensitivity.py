#!/usr/bin/env python3
"""Build property-mode sensitivity tables for lit-review closure gating."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from litrev_common import (
    DATE_DIR,
    PREDICTIVE_THERMAL,
    PRESSURE_LEDGER,
    PROPERTY_MODES,
    TIME_UNCERTAINTY,
    ensure_inputs,
    num,
    prandtl,
    property_mode,
    read_csv,
    rel,
    reynolds,
    safe_div,
    summary_payload,
    write_csv,
    write_json,
    write_readme,
)


TASK_ID = "TODO-LITREV-PROPERTY-SENSITIVITY"
OUT_DIR = DATE_DIR / "2026-07-13_litrev_property_sensitivity"

FIELDS = [
    "source_id",
    "case_id",
    "span",
    "property_mode",
    "T_basis_K",
    "rho_kg_m3",
    "mu_pa_s",
    "cp_jkgk",
    "k_w_mk",
    "Re",
    "Re_ratio_to_replication",
    "Pr",
    "Pr_ratio_to_replication",
    "Gz",
    "Gz_ratio_to_replication",
    "buoyancy_head_proxy_pa",
    "buoyancy_head_ratio_to_replication",
    "pressure_residual_proxy_pa",
    "pressure_residual_ratio_to_replication",
    "heat_residual_W",
    "heat_residual_ratio_to_replication",
    "model_form_admission_flag",
    "source_status",
    "provenance_author_title",
    "quality_flags",
]

SUMMARY_FIELDS = [
    "case_id",
    "property_mode",
    "mean_Re_ratio_to_replication",
    "mean_Pr_ratio_to_replication",
    "mean_Gz_ratio_to_replication",
    "mean_abs_heat_residual_W",
    "max_abs_pressure_residual_proxy_pa",
    "admission_summary",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def thermal_lookup() -> dict[tuple[str, str], dict[str, str]]:
    mapping: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_csv(PREDICTIVE_THERMAL):
        spans = [x.strip() for x in row.get("component_parent_spans", "").replace(";", ",").split(",") if x.strip()]
        if not spans:
            spans = [row.get("one_d_segment", "")]
        for span in spans:
            if span:
                mapping[(row["source_id"], span)] = row
    return mapping


def build_rows() -> list[dict[str, Any]]:
    ensure_inputs([PRESSURE_LEDGER, PREDICTIVE_THERMAL])
    thermal = thermal_lookup()
    rows: list[dict[str, Any]] = []
    replication_by_span: dict[tuple[str, str], dict[str, Any]] = {}
    for prow in read_csv(PRESSURE_LEDGER):
        trow = thermal.get((prow["source_id"], prow["span"]))
        T = (
            num(trow.get("T_bulk_for_htc_K") if trow else None)
            or num(trow.get("T_bulk_inlet_K") if trow else None)
            or 450.0
        )
        D = num(prow.get("D_h_m"), 0.0) or 0.0
        L = num(prow.get("L_m"), 0.0) or 0.0
        u = num(prow.get("u_bulk_m_s"), 0.0) or 0.0
        heat_residual = num(trow.get("wallHeatFlux_vs_enthalpy_residual_W") if trow else None)
        pressure_residual = num(prow.get("residual_pa"), 0.0) or 0.0
        buoyancy = num(prow.get("buoyancy_contribution_pa"), 0.0) or 0.0
        span_rows: list[dict[str, Any]] = []
        for mode in PROPERTY_MODES:
            props = property_mode(mode, T)
            Re = reynolds(props["rho_kg_m3"], u, D, props["mu_pa_s"]) if D else None
            Pr = prandtl(props["mu_pa_s"], props["cp_jkgk"], props["k_w_mk"])
            Gz = Re * Pr * D / L if Re is not None and L else None
            row = {
                "source_id": prow["source_id"],
                "case_id": prow["case_id"],
                "span": prow["span"],
                "property_mode": mode,
                "T_basis_K": T,
                "rho_kg_m3": props["rho_kg_m3"],
                "mu_pa_s": props["mu_pa_s"],
                "cp_jkgk": props["cp_jkgk"],
                "k_w_mk": props["k_w_mk"],
                "Re": Re,
                "Pr": Pr,
                "Gz": Gz,
                "buoyancy_head_proxy_pa": buoyancy,
                "pressure_residual_proxy_pa": pressure_residual,
                "heat_residual_W": heat_residual,
                "source_status": props["source_status"],
                "provenance_author_title": props["provenance_author_title"],
                "quality_flags": "first_order_property_reduction_no_full_1d_rerun;thermal_residual_from_existing_package" if trow else "first_order_property_reduction_no_full_1d_rerun;no_thermal_segment_match",
            }
            span_rows.append(row)
            if mode == "replication_reis_jadyn":
                replication_by_span[(prow["source_id"], prow["span"])] = row
        base = replication_by_span[(prow["source_id"], prow["span"])]
        for row in span_rows:
            row["Re_ratio_to_replication"] = safe_div(num(row["Re"]), num(base["Re"]))
            row["Pr_ratio_to_replication"] = safe_div(num(row["Pr"]), num(base["Pr"]))
            row["Gz_ratio_to_replication"] = safe_div(num(row["Gz"]), num(base["Gz"]))
            row["buoyancy_head_ratio_to_replication"] = 1.0
            row["pressure_residual_ratio_to_replication"] = safe_div(num(row["pressure_residual_proxy_pa"]), num(base["pressure_residual_proxy_pa"]))
            row["heat_residual_ratio_to_replication"] = safe_div(num(row["heat_residual_W"]), num(base["heat_residual_W"]))
            max_move = max(
                abs((num(row.get("Re_ratio_to_replication"), 1.0) or 1.0) - 1.0),
                abs((num(row.get("Pr_ratio_to_replication"), 1.0) or 1.0) - 1.0),
                abs((num(row.get("Gz_ratio_to_replication"), 1.0) or 1.0) - 1.0),
            )
            row["model_form_admission_flag"] = (
                "property_sensitivity_material_closure_fit_blocked"
                if row["property_mode"] != "replication_reis_jadyn" and max_move > 0.10
                else "property_mode_reported_no_closure_fit"
            )
            rows.append(row)
    return rows


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    keys = sorted({(r["case_id"], r["property_mode"]) for r in rows})
    for case_id, mode in keys:
        subset = [r for r in rows if r["case_id"] == case_id and r["property_mode"] == mode]
        material = any(r["model_form_admission_flag"] == "property_sensitivity_material_closure_fit_blocked" for r in subset)
        out.append(
            {
                "case_id": case_id,
                "property_mode": mode,
                "mean_Re_ratio_to_replication": mean([num(r.get("Re_ratio_to_replication")) for r in subset]),
                "mean_Pr_ratio_to_replication": mean([num(r.get("Pr_ratio_to_replication")) for r in subset]),
                "mean_Gz_ratio_to_replication": mean([num(r.get("Gz_ratio_to_replication")) for r in subset]),
                "mean_abs_heat_residual_W": mean([abs(num(r.get("heat_residual_W"), 0.0) or 0.0) for r in subset]),
                "max_abs_pressure_residual_proxy_pa": max(abs(num(r.get("pressure_residual_proxy_pa"), 0.0) or 0.0) for r in subset),
                "admission_summary": "do_not_fit_closure_before_property_choice" if material else "reported_reference_mode",
            }
        )
    return out


def main() -> None:
    args = parse_args()
    rows = build_rows()
    summaries = summary_rows(rows)
    write_csv(args.output_dir / "property_mode_matrix.csv", rows, FIELDS)
    write_csv(args.output_dir / "property_sensitivity_summary.csv", summaries, SUMMARY_FIELDS)
    validation = {
        "rows": len(rows),
        "summary_rows": len(summaries),
        "property_modes": PROPERTY_MODES,
        "input_paths": [rel(PRESSURE_LEDGER), rel(PREDICTIVE_THERMAL)],
        "full_1d_rerun_performed": False,
    }
    write_json(args.output_dir / "validation_report.json", validation)
    write_json(
        args.output_dir / "summary.json",
        summary_payload(
            TASK_ID,
            args.output_dir,
            len(rows),
            ["property_mode_matrix.csv", "property_sensitivity_summary.csv", "validation_report.json"],
            ["This is a first-order postprocessing sensitivity, not a full pressure-rooted 1D rerun."],
        ),
    )
    write_readme(
        args.output_dir / "README.md",
        "Lit-Rev Property Sensitivity",
        TASK_ID,
        {
            "Observed Output": f"Built {len(rows)} property-mode branch rows and {len(summaries)} case/mode summary rows.",
            "Inferred Interpretation": "Property choices move Re, Pr, and Gz enough that pressure or heat residuals should not be fitted until the property mode is declared.",
            "Blockers": "This pass does not rerun Fluid or recompute pressure-rooted mdot. It quantifies first-order nondimensional and residual sensitivity from existing CFD/postprocessing artifacts.",
            "Recommended Next Action": "Use `property_sensitivity_summary.csv` to choose replication versus updated-property lanes before fitting friction, heat-loss, or Nu residuals.",
        },
    )


if __name__ == "__main__":
    main()

