#!/usr/bin/env python3
"""Build the lit-review source-envelope gate for TAMU branches."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Mapping

from litrev_common import (
    DATE_DIR,
    G,
    PREDICTIVE_THERMAL,
    PRESSURE_LEDGER,
    PROPERTY_MODES,
    ROOT,
    classify_orientation,
    ensure_inputs,
    grashof,
    heating_sign_for_span,
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


TASK_ID = "TODO-LITREV-SOURCE-ENVELOPE"
OUT_DIR = DATE_DIR / "2026-07-13_litrev_source_envelope"

BRANCH_FIELDS = [
    "source_id",
    "case_id",
    "span",
    "property_mode",
    "orientation",
    "heating_cooling_sign",
    "T_basis_K",
    "delta_T_basis_K",
    "rho_kg_m3",
    "mu_pa_s",
    "cp_jkgk",
    "k_w_mk",
    "Re",
    "Pr",
    "Gr",
    "Gr_star",
    "Ri",
    "Ra",
    "Gz",
    "Bo",
    "L_m",
    "D_h_m",
    "L_over_D",
    "reset_distance_m",
    "reset_distance_basis",
    "flow_reset_flag",
    "fit_use_status",
    "quality_flags",
]

SOURCE_FIELDS = [
    "source_id",
    "case_id",
    "span",
    "property_mode",
    "candidate_source",
    "provenance_author_title",
    "source_use_category",
    "overlap_status",
    "source_range_summary",
    "tamu_range_summary",
    "admission_recommendation",
    "reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def thermal_by_span(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    mapping: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        spans = [s.strip() for s in row.get("component_parent_spans", "").split(";") if s.strip()]
        spans.extend([s.strip() for s in row.get("component_parent_spans", "").split(",") if s.strip()])
        if not spans and row.get("one_d_segment"):
            spans = [row["one_d_segment"]]
        for span in spans:
            mapping[(row["source_id"], span)] = row
    return mapping


def branch_rows() -> list[dict[str, Any]]:
    ensure_inputs([PRESSURE_LEDGER, PREDICTIVE_THERMAL])
    pressure = read_csv(PRESSURE_LEDGER)
    thermal = thermal_by_span(read_csv(PREDICTIVE_THERMAL))
    rows: list[dict[str, Any]] = []
    for prow in pressure:
        source_id = prow["source_id"]
        span = prow["span"]
        trow = thermal.get((source_id, span))
        T = (
            num(trow.get("T_bulk_for_htc_K") if trow else None)
            or num(trow.get("T_bulk_inlet_K") if trow else None)
            or 450.0
        )
        dT = abs(num(trow.get("delta_T_K") if trow else None, 1.0) or 1.0)
        L = num(prow.get("L_m"), 0.0) or 0.0
        D = num(prow.get("D_h_m"), 0.0) or 0.0
        u = num(prow.get("u_bulk_m_s"), 0.0) or 0.0
        q_ref = num(prow.get("q_ref_pa"))
        buoy = num(prow.get("buoyancy_contribution_pa"))
        for mode in PROPERTY_MODES:
            props = property_mode(mode, T)
            Re = reynolds(props["rho_kg_m3"], u, D, props["mu_pa_s"]) if D else None
            Pr = prandtl(props["mu_pa_s"], props["cp_jkgk"], props["k_w_mk"])
            Gr = grashof(props["rho_kg_m3"], props["mu_pa_s"], 0.7497 / props["rho_kg_m3"], dT, D) if D else None
            rows.append(
                {
                    "source_id": source_id,
                    "case_id": prow["case_id"],
                    "span": span,
                    "property_mode": mode,
                    "orientation": classify_orientation(span),
                    "heating_cooling_sign": heating_sign_for_span(span, trow),
                    "T_basis_K": T,
                    "delta_T_basis_K": dT,
                    "rho_kg_m3": props["rho_kg_m3"],
                    "mu_pa_s": props["mu_pa_s"],
                    "cp_jkgk": props["cp_jkgk"],
                    "k_w_mk": props["k_w_mk"],
                    "Re": Re,
                    "Pr": Pr,
                    "Gr": Gr,
                    "Gr_star": (Gr * D / L) if Gr is not None and L else None,
                    "Ri": (Gr / (Re * Re)) if Gr is not None and Re else None,
                    "Ra": Gr * Pr if Gr is not None else None,
                    "Gz": Re * Pr * D / L if Re is not None and L else None,
                    "Bo": safe_div(abs(buoy) if buoy is not None else None, q_ref),
                    "L_m": L,
                    "D_h_m": D,
                    "L_over_D": safe_div(L, D),
                    "reset_distance_m": L,
                    "reset_distance_basis": "section_length_since_local_endpoint_only; upstream reset map handled by TODO-LITREV-RESET-NAMED-LOSSES",
                    "flow_reset_flag": prow.get("flow_reset_flag", ""),
                    "fit_use_status": prow.get("fit_use_status", ""),
                    "quality_flags": ";".join(
                        filter(
                            None,
                            [
                                prow.get("quality_flags", ""),
                                "thermal_deltaT_from_segment_when_available" if trow else "thermal_deltaT_default_1K_no_segment_match",
                                props["source_status"],
                            ],
                        )
                    ),
                }
            )
    return rows


def in_range(value: float | None, lo: float, hi: float) -> bool | None:
    if value is None or not math.isfinite(value):
        return None
    return lo <= value <= hi


def source_overlap(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    Re = num(row.get("Re"))
    Pr = num(row.get("Pr"))
    Gr = num(row.get("Gr"))
    Gz = num(row.get("Gz"))
    LD = num(row.get("L_over_D"))
    common = {
        "source_id": row["source_id"],
        "case_id": row["case_id"],
        "span": row["span"],
        "property_mode": row["property_mode"],
        "tamu_range_summary": f"Re={Re:.3g} Pr={Pr:.3g} Gr={Gr:.3g} Gz={Gz:.3g} L/D={LD:.3g}" if all(v is not None for v in [Re, Pr, Gr, Gz, LD]) else "one or more TAMU groups unavailable",
    }
    checks: list[dict[str, Any]] = []
    chen_inside = all(
        x is True
        for x in [
            in_range(Re, 300.0, 2300.0),
            in_range(Pr, 11.0, 27.0),
            in_range(Gr, 8.56e4, 3.95e6),
            in_range(Gz, 150.0, 310.0),
            in_range(LD, 35.0, 95.0),
        ]
    )
    chen_outside = any(
        x is False
        for x in [
            in_range(Re, 300.0, 2300.0),
            in_range(Pr, 11.0, 27.0),
            in_range(Gr, 8.56e4, 3.95e6),
            in_range(Gz, 150.0, 310.0),
            in_range(LD, 35.0, 95.0),
        ]
    )
    checks.append(
        common
        | {
            "candidate_source": "chen_2017_low_re_molten_salt_mixed_convection",
            "provenance_author_title": "Chen et al., Characteristics of the laminar convective heat transfer of molten salt in concentric tube",
            "source_use_category": "source_bounded_active_candidate_only_if_inside",
            "overlap_status": "inside" if chen_inside else ("outside" if chen_outside else "unknown"),
            "source_range_summary": "Re 300-2300; Pr 11-27; Gr 8.56e4-3.95e6; Gz 150-310; 35<L/D<95; concentric-tube molten salt",
            "admission_recommendation": "conditional_candidate" if chen_inside else "do_not_promote",
            "reason": "numeric range overlap checked; geometry still not TAMU-matched" if chen_inside else "one or more TAMU nondimensional groups are outside or unknown",
        }
    )
    tian_outside = Re is not None and Re < 2300.0
    checks.append(
        common
        | {
            "candidate_source": "tian_2024_turbulent_cooled_molten_salt",
            "provenance_author_title": "Tian et al., Numerical analysis of turbulent mixed convection heat transfer of molten salt in horizontal tubes with uniformly cooled heat flux",
            "source_use_category": "reference_or_outside_if_laminar",
            "overlap_status": "outside" if tian_outside else "unknown",
            "source_range_summary": "turbulent mixed convection source; exact audited numeric range not promoted for low-Re TAMU laminar branches",
            "admission_recommendation": "reference_only",
            "reason": "TAMU branch Re is laminar in this ledger" if tian_outside else "requires exact turbulent source envelope extraction before active use",
        }
    )
    muzy_inside = Re is not None and Re < 2300.0 and Pr is not None and Pr > 0.1
    checks.append(
        common
        | {
            "candidate_source": "muzychka_yovanovich_forced_combined_entry",
            "provenance_author_title": "Muzychka and Yovanovich, Laminar Forced Convection Heat Transfer in the Combined Entry Region of Non-Circular Ducts",
            "source_use_category": "method_reference_pending_characteristic_length_conversion",
            "overlap_status": "inside" if muzy_inside else "unknown",
            "source_range_summary": "0.1<Pr<infinity; laminar forced combined entry; characteristic-length conversion required",
            "admission_recommendation": "reference_or_candidate_after_conversion_audit",
            "reason": "Pr/Re model class overlaps but implementation constants and characteristic length must be audited before active closure",
        }
    )
    checks.append(
        common
        | {
            "candidate_source": "everts_meyer_entrance_length_gate",
            "provenance_author_title": "Everts and Meyer, Laminar Hydrodynamic and Thermal Entrance Lengths for Simultaneously Hydrodynamically and Thermally Developing Forced and Mixed Convective Flows in Horizontal Tubes",
            "source_use_category": "diagnostic_gate",
            "overlap_status": "unknown",
            "source_range_summary": "entrance-length and mixed-convection diagnostic source; fluid/geometry/range match not fully established here",
            "admission_recommendation": "use_as_gate_not_active_correlation",
            "reason": "TAMU groups are computed, but exact source envelope and geometry match require separate audit",
        }
    )
    return checks


def main() -> None:
    args = parse_args()
    rows = sorted(branch_rows(), key=lambda r: (r["case_id"], r["span"], r["property_mode"]))
    source_rows = [item for row in rows for item in source_overlap(row)]
    write_csv(args.output_dir / "branch_source_envelope.csv", rows, BRANCH_FIELDS)
    write_csv(args.output_dir / "source_overlap_flags.csv", source_rows, SOURCE_FIELDS)
    validation = {
        "branch_rows": len(rows),
        "source_overlap_rows": len(source_rows),
        "missing_required_fields": [
            field for field in BRANCH_FIELDS if any(str(row.get(field, "")).strip() == "" for row in rows) and field not in {"Bo"}
        ],
        "input_paths": [rel(PRESSURE_LEDGER), rel(PREDICTIVE_THERMAL)],
    }
    write_json(args.output_dir / "validation_report.json", validation)
    write_json(
        args.output_dir / "summary.json",
        summary_payload(
            TASK_ID,
            args.output_dir,
            len(rows),
            ["branch_source_envelope.csv", "source_overlap_flags.csv", "validation_report.json"],
            [
                "Chen 2017 numeric overlap is checked directly from the lit-review audited range.",
                "Tian 2024 is kept reference-only for laminar TAMU rows.",
                "Muzychka/Yovanovich and Everts/Meyer are retained as method/gate sources pending conversion and range audit.",
            ],
        ),
    )
    write_readme(
        args.output_dir / "README.md",
        "Lit-Rev Source Envelope Gate",
        TASK_ID,
        {
            "Observed Output": f"Built {len(rows)} branch/property rows and {len(source_rows)} source-overlap rows from `{rel(PRESSURE_LEDGER)}` and `{rel(PREDICTIVE_THERMAL)}`.",
            "Inferred Interpretation": "The table is a gate, not a closure promotion. It identifies whether source-bounded literature models are inside, outside, or still unknown relative to TAMU branch nondimensional conditions.",
            "Blockers": "Reset distance is section-local until the named-loss/reset package maps upstream hydraulic and thermal resets. Some literature ranges remain method-only because the lit review did not provide implementation-safe numeric bounds.",
            "Recommended Next Action": "Use `source_overlap_flags.csv` before any Nu/f/K model promotion. Treat `outside` and `unknown` rows as reference-only or sensitivity-only until a later audit resolves them.",
        },
    )


if __name__ == "__main__":
    main()

