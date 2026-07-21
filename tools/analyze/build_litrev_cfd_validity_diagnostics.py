#!/usr/bin/env python3
"""Build CFD single-stream validity diagnostics for closure coefficient naming."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from statistics import pstdev
from typing import Any

from litrev_common import (
    CLOSURE_OBSERVATIONS,
    DATE_DIR,
    PRESSURE_LEDGER,
    THERMAL_BOUNDARY,
    ensure_inputs,
    num,
    read_csv,
    rel,
    summary_payload,
    write_csv,
    write_json,
    write_readme,
)


TASK_ID = "TODO-LITREV-CFD-VALIDITY-DIAGNOSTICS"
OUT_DIR = DATE_DIR / "2026-07-13_litrev_cfd_validity_diagnostics"

VALIDITY_FIELDS = [
    "source_id",
    "case_id",
    "section",
    "section_type",
    "reverse_flow_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "recirculation_zone_flag",
    "recirculation_zone_count",
    "wall_heat_flux_skew",
    "single_stream_validity",
    "coefficient_naming_limit",
    "fit_use_status",
    "provenance_author_title",
    "source_path",
    "quality_flags",
]

LIMIT_FIELDS = [
    "source_id",
    "case_id",
    "section",
    "coefficient_family",
    "allowed_name",
    "rejected_names",
    "naming_status",
    "reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def recirc_lookup() -> dict[tuple[str, str], float]:
    lookup: dict[tuple[str, str], float] = {}
    if not CLOSURE_OBSERVATIONS.exists():
        return lookup
    for row in read_csv(CLOSURE_OBSERVATIONS):
        span = row.get("span") or row.get("segment_1d") or row.get("control_volume")
        value = num(row.get("max_interface_recirc_ratio"))
        backflow = num(row.get("backflow_fraction"))
        metric = max([v for v in [value, backflow] if v is not None], default=None)
        if span and metric is not None:
            lookup[(row["source_id"], span)] = max(lookup.get((row["source_id"], span), 0.0), metric)
    return lookup


def heat_skew_lookup() -> dict[tuple[str, str], float]:
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    if not THERMAL_BOUNDARY.exists():
        return {}
    for row in read_csv(THERMAL_BOUNDARY):
        q = num(row.get("realized_wallHeatFlux_mean_W_m2"))
        seg = row.get("one_d_segment") or row.get("parent_span")
        if q is not None and seg:
            values[(row["source_id"], seg)].append(q)
    out: dict[tuple[str, str], float] = {}
    for key, vals in values.items():
        mean_abs = sum(abs(v) for v in vals) / len(vals)
        out[key] = pstdev(vals) / mean_abs if len(vals) > 1 and mean_abs else 0.0
    return out


def classify(reverse: float | None, recirc_flag: bool, skew: float | None) -> tuple[str, str, str]:
    reverse = reverse or 0.0
    skew = skew or 0.0
    if recirc_flag or reverse >= 0.20:
        return (
            "invalid_single_stream",
            "section_effective_only",
            "reverse/recirculation metric exceeds material threshold or source pressure ledger flags recirculation",
        )
    if reverse >= 0.05 or skew >= 1.0:
        return (
            "marginal_single_stream",
            "diagnostic_or_section_effective_pending_plane_isolation",
            "moderate reverse-flow proxy or wall-heat-flux skew",
        )
    return ("single_stream_plausible", "transferable_candidate_pending_mesh_source_envelope", "no material reverse-flow proxy found in existing artifacts")


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_inputs([PRESSURE_LEDGER, THERMAL_BOUNDARY])
    recirc = recirc_lookup()
    skew = heat_skew_lookup()
    rows: list[dict[str, Any]] = []
    limits: list[dict[str, Any]] = []
    for prow in read_csv(PRESSURE_LEDGER):
        section = prow["span"]
        reverse = recirc.get((prow["source_id"], section))
        heat_skew = skew.get((prow["source_id"], section))
        recirc_flag = str(prow.get("recirculation_flag", "")).lower() == "true"
        validity, naming, reason = classify(reverse, recirc_flag, heat_skew)
        rows.append(
            {
                "source_id": prow["source_id"],
                "case_id": prow["case_id"],
                "section": section,
                "section_type": "pressure_span",
                "reverse_flow_area_fraction": reverse,
                "reverse_mass_fraction": reverse,
                "secondary_velocity_fraction": "",
                "recirculation_zone_flag": "yes" if recirc_flag or (reverse or 0.0) > 0 else "no",
                "recirculation_zone_count": 1 if recirc_flag or (reverse or 0.0) > 0 else 0,
                "wall_heat_flux_skew": heat_skew,
                "single_stream_validity": validity,
                "coefficient_naming_limit": naming,
                "fit_use_status": prow.get("fit_use_status", ""),
                "provenance_author_title": "Patino-Jaramillo et al., Laminar Flow and Pressure Loss in Planar Tee Joints: Numerical Simulations and Flow Analysis; Podila et al., Modelling of Heat Transfer in a Molten Salt Loop Using Computational Fluid Dynamics",
                "source_path": rel(PRESSURE_LEDGER),
                "quality_flags": ";".join(
                    filter(
                        None,
                        [
                            prow.get("quality_flags", ""),
                            "reverse_metric_from_existing_observation_proxy" if reverse is not None else "reverse_metric_missing_needs_plane_extraction",
                            "secondary_velocity_not_available_needs_vector_plane_extraction",
                        ],
                    )
                ),
            }
        )
        for family in ["f_D", "K", "Nu"]:
            if naming == "section_effective_only":
                allowed = f"{family}_section_effective_{section}"
                rejected = f"universal_{family}; transferable_{family}"
                status = "reject_universal_name"
            elif naming.startswith("diagnostic"):
                allowed = f"{family}_diagnostic_{section}"
                rejected = f"universal_{family}"
                status = "diagnostic_only"
            else:
                allowed = f"{family}_candidate_{section}"
                rejected = ""
                status = "candidate_pending_other_gates"
            limits.append(
                {
                    "source_id": prow["source_id"],
                    "case_id": prow["case_id"],
                    "section": section,
                    "coefficient_family": family,
                    "allowed_name": allowed,
                    "rejected_names": rejected,
                    "naming_status": status,
                    "reason": reason,
                }
            )
    return rows, limits


def main() -> None:
    args = parse_args()
    rows, limits = build_rows()
    write_csv(args.output_dir / "cfd_single_stream_validity.csv", rows, VALIDITY_FIELDS)
    write_csv(args.output_dir / "coefficient_naming_limits.csv", limits, LIMIT_FIELDS)
    validation = {
        "validity_rows": len(rows),
        "naming_rows": len(limits),
        "input_paths": [rel(PRESSURE_LEDGER), rel(THERMAL_BOUNDARY), rel(CLOSURE_OBSERVATIONS)],
        "new_openfoam_extraction_performed": False,
        "missing_metric_policy": "secondary_velocity_fraction and exact reverse-flow area/mass require future plane-vector extraction when unavailable",
    }
    write_json(args.output_dir / "validation_report.json", validation)
    write_json(
        args.output_dir / "summary.json",
        summary_payload(
            TASK_ID,
            args.output_dir,
            len(rows),
            ["cfd_single_stream_validity.csv", "coefficient_naming_limits.csv", "validation_report.json"],
            ["Existing artifact proxies were used; no new OpenFOAM extraction was needed for this first validity gate."],
        ),
    )
    write_readme(
        args.output_dir / "README.md",
        "Lit-Rev CFD Validity Diagnostics",
        TASK_ID,
        {
            "Observed Output": f"Built {len(rows)} pressure-section validity rows and {len(limits)} coefficient naming rows.",
            "Inferred Interpretation": "Sections with recirculation or material reverse-flow proxies must be named as section-effective or diagnostic coefficients, not universal `f_D`, `K`, or `Nu` closures.",
            "Blockers": "Secondary velocity fraction and exact reverse-flow area/mass fractions are unavailable in existing package form for some sections; those rows are marked for bounded plane-vector extraction if needed.",
            "Recommended Next Action": "Feed `coefficient_naming_limits.csv` into the reset/named-loss package and reject universal coefficient names wherever the validity gate is section-effective only.",
        },
    )


if __name__ == "__main__":
    main()

