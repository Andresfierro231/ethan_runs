#!/usr/bin/env python3
"""Review AGENT-457 pressure maps and junction/corner evidence state."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


TASK = "AGENT-460"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state")
OUT = ROOT / OUT_REL

PRESSURE_BRANCH = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/"
    "all_branch_average_pressure_map.csv"
)
PRESSURE_STATION = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/"
    "all_streamwise_pressure_1d_map.csv"
)
CASE_PROVENANCE = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/"
    "case_provenance_manifest.csv"
)
PRESSURE_ADMISSION = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/"
    "branch_orientation_straight_loss_recirc_admission.csv"
)
PRESSURE_ADMISSION_SUMMARY = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/summary.json"
)
HEAT_ROLE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_role.csv"
HEAT_SEGMENT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_segment.csv"
MINOR_LOSS = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv"
MINOR_LOSS_SEPARATION = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_separation/minor_loss_separation.csv"
MINOR_LOSS_SUMMARY = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_separation/minor_loss_separation_summary.json"
GEOMETRY_REFERENCE = ROOT / "reference/geometry_reference.md"

BRANCH_ORDER = ["lower_leg", "left_lower_leg", "test_section_span", "left_upper_leg", "upper_leg", "right_leg"]
CORNER_ORDER = ["corner_lower_left", "corner_lower_right", "corner_upper_right", "corner_upper_left"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def f(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    return float(value)


def sign(value: float, tol: float = 1e-9) -> str:
    if value > tol:
        return "positive"
    if value < -tol:
        return "negative"
    return "zero"


def build_pressure_branch_review(
    branch_rows: list[dict[str, str]], admission_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    admission_by_key = {(row["case_key"], row["branch"]): row for row in admission_rows}
    review: list[dict[str, Any]] = []
    for row in branch_rows:
        adm = admission_by_key.get((row["case_key"], row["cfd_span"]), {})
        static_delta = f(row, "flow_end_minus_start_p_Pa")
        prgh_delta = f(row, "flow_end_minus_start_p_rgh_Pa")
        static_prgh_relation = "same_sign" if sign(static_delta) == sign(prgh_delta) else "different_sign"
        review.append(
            {
                "case_key": row["case_key"],
                "split_role": row["split_role"],
                "cfd_span": row["cfd_span"],
                "physical_location_label": row["physical_location_label"],
                "one_d_component_segments": row["one_d_component_segments"],
                "flow_start_station_label": row["flow_start_station_label"],
                "flow_end_station_label": row["flow_end_station_label"],
                "arithmetic_mean_p_Pa": row["arithmetic_mean_p_Pa"],
                "arithmetic_mean_p_rgh_Pa": row["arithmetic_mean_p_rgh_Pa"],
                "flow_end_minus_start_p_Pa": static_delta,
                "flow_end_minus_start_p_rgh_Pa": prgh_delta,
                "static_delta_sign": sign(static_delta),
                "p_rgh_delta_sign": sign(prgh_delta),
                "static_prgh_delta_relation": static_prgh_relation,
                "max_reverse_area_fraction_proxy": row["max_reverse_area_fraction_proxy"],
                "mean_reverse_area_fraction_proxy": row["mean_reverse_area_fraction_proxy"],
                "admission_table_status": adm.get("admission_status", "missing_from_admission_table"),
                "recirculation_mask_status": adm.get("recirculation_mask_status", ""),
                "pressure_definition_status": adm.get("pressure_definition_status", ""),
                "orientation_status": adm.get("orientation_status", ""),
                "straight_loss_subtraction_status": adm.get("straight_loss_subtraction_status", ""),
                "true_f_D_or_K_fit_admitted": adm.get("true_f_D_or_K_fit_admitted", "no"),
                "scientific_use": classify_pressure_row(row, adm, static_prgh_relation),
                "critique": pressure_row_critique(row, adm, static_prgh_relation),
                "source_path": row["source_path"],
            }
        )
    return review


def classify_pressure_row(row: dict[str, str], adm: dict[str, str], static_prgh_relation: str) -> str:
    if adm.get("true_f_D_or_K_fit_admitted") == "yes":
        return "fit_admitted"
    if adm.get("recirculation_mask_status") == "blocked_material_recirculation_mask":
        return "diagnostic_location_pressure_map_only"
    if static_prgh_relation == "different_sign":
        return "diagnostic_pressure_definition_sensitive"
    return "diagnostic_screen_only"


def pressure_row_critique(row: dict[str, str], adm: dict[str, str], static_prgh_relation: str) -> str:
    parts = [
        "location_mapping_ok",
        "mean_pressure_values_available",
        "not_distance_normalized",
        "not_straight_loss_subtracted",
    ]
    if static_prgh_relation == "different_sign":
        parts.append("static_vs_p_rgh_branch_delta_sign_differs")
    if adm.get("recirculation_mask_status") == "blocked_material_recirculation_mask":
        parts.append("recirculation_mask_blocks_single_stream_loss_fit")
    if row["cfd_span"] in {"left_lower_leg", "test_section_span", "left_upper_leg"}:
        parts.append("upcomer_or_test_section_hybrid_lane")
    return ";".join(parts)


def build_pressure_case_review(
    branch_review: list[dict[str, Any]], station_rows: list[dict[str, str]], provenance_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    prov = {row["case_key"]: row for row in provenance_rows}
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    station_by_case: Counter[str] = Counter()
    for row in branch_review:
        by_case[row["case_key"]].append(row)
    for row in station_rows:
        station_by_case[row["case_key"]] += 1

    rows: list[dict[str, Any]] = []
    for case_key in sorted(by_case):
        branches = by_case[case_key]
        p_means = [f(row, "arithmetic_mean_p_Pa") for row in branches]
        prgh_means = [f(row, "arithmetic_mean_p_rgh_Pa") for row in branches]
        reverse_max = max(f(row, "max_reverse_area_fraction_proxy") for row in branches)
        blocked_count = sum(row["recirculation_mask_status"] == "blocked_material_recirculation_mask" for row in branches)
        sign_diff_count = sum(row["static_prgh_delta_relation"] == "different_sign" for row in branches)
        admitted_count = sum(row["true_f_D_or_K_fit_admitted"] == "yes" for row in branches)
        rows.append(
            {
                "case_key": case_key,
                "case_id": prov[case_key]["case_id"],
                "split_role": prov[case_key]["split_role"],
                "time_s": prov[case_key]["time_s"],
                "harvest_job_id": prov[case_key]["harvest_job_id"],
                "station_rows": station_by_case[case_key],
                "branch_rows": len(branches),
                "static_branch_mean_range_Pa": max(p_means) - min(p_means),
                "p_rgh_branch_mean_range_Pa": max(prgh_means) - min(prgh_means),
                "max_reverse_area_fraction_proxy": reverse_max,
                "recirculation_blocked_branch_count": blocked_count,
                "static_vs_p_rgh_branch_delta_sign_diff_count": sign_diff_count,
                "fit_admitted_branch_count": admitted_count,
                "overall_scientific_status": "diagnostic_location_pressure_map_only" if admitted_count == 0 else "has_fit_admitted_rows",
                "main_critique": case_critique(station_by_case[case_key], len(branches), blocked_count, sign_diff_count),
                "native_case_path": prov[case_key]["native_case_path"],
            }
        )
    return rows


def case_critique(station_count: int, branch_count: int, blocked_count: int, sign_diff_count: int) -> str:
    parts = []
    if station_count == 30 and branch_count == 6:
        parts.append("complete_station_and_branch_coverage")
    if blocked_count:
        parts.append(f"{blocked_count}_branches_blocked_by_recirc_mask")
    if sign_diff_count:
        parts.append(f"{sign_diff_count}_branches_static_vs_p_rgh_delta_sign_diff")
    parts.append("absolute_static_pressure_not_cross_case_closure_metric")
    return ";".join(parts)


def build_junction_heat_review(role_rows: list[dict[str, str]], segment_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in role_rows:
        if row["path_id"] == "cfd_role_summary" and row["role_or_lane"] in {
            "junction_other",
            "ambient_wall",
            "test_section",
            "cooler",
            "heater",
        }:
            realized = f(row, "cfd_realized_W")
            rows.append(
                {
                    "case_id": row["case_id"],
                    "source_id": row["source_id"],
                    "role_or_lane": row["role_or_lane"],
                    "role_group": row["role_group"],
                    "cfd_imposed_W": row["cfd_imposed_W"],
                    "cfd_realized_W": realized,
                    "heat_direction": "to_fluid" if realized > 0 else "from_fluid" if realized < 0 else "zero",
                    "evidence_class": row["evidence_class"],
                    "scientific_use": "diagnostic_role_accounting_not_predictive_closure",
                    "critique": heat_role_critique(row),
                    "source_paths": row["source_paths"],
                }
            )

    # Add segment-level junction row from realized-wallflux diagnostic, if present.
    for row in segment_rows:
        if row["path_id"] == "B2_realized_wallflux_roles" and row["one_d_segment"] == "junction":
            realized_net = f(row, "cfd_realized_net_to_fluid_W")
            rows.append(
                {
                    "case_id": row["case_id"],
                    "source_id": row["source_id"],
                    "role_or_lane": "junction_segment_realized_wallflux",
                    "role_group": "diagnostic_segment_alignment",
                    "cfd_imposed_W": row["cfd_imposed_net_to_fluid_W"],
                    "cfd_realized_W": realized_net,
                    "heat_direction": "to_fluid" if realized_net > 0 else "from_fluid" if realized_net < 0 else "zero",
                    "evidence_class": row["evidence_class"],
                    "scientific_use": "diagnostic_segment_alignment_not_predictive_closure",
                    "critique": "same_path_present_but_realized_wallHeatFlux_is_forbidden_runtime_input;not_per_junction_resolved",
                    "source_paths": row["source_paths"],
                }
            )
    return sorted(rows, key=lambda r: (r["case_id"], r["role_or_lane"]))


def heat_role_critique(row: dict[str, str]) -> str:
    if row["role_or_lane"] == "junction_other":
        return "junction_or_stub_loss_is_observed_as_aggregate;not_split_by_four_junctions;radiation_included_in_total_wallHeatFlux"
    if row["role_or_lane"] == "ambient_wall":
        return "ambient_wall_loss_observed_but_not_specific_to_junctions"
    if row["role_or_lane"] == "test_section":
        return "test_section_realizes_as_net_sink_despite_imposed_source"
    return "role_level_heat_accounting_observed"


def build_corner_review(minor_rows: list[dict[str, str]], separation_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    sep_by_case_span = {(row["case_id"], row["span"]): row for row in separation_rows}
    rows: list[dict[str, Any]] = []
    for row in minor_rows:
        if row["feature_type"] != "bend/junction_corner":
            continue
        sep = sep_by_case_span.get((row["case_id"], row["downstream_span"]), {})
        rows.append(
            {
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "feature": row["feature"],
                "downstream_span": row["downstream_span"],
                "adjacent_spans": row["adjacent_spans"],
                "feature_total_pressure_loss_pa": row["feature_total_pressure_loss_pa"],
                "adjacent_straight_loss_subtracted_pa": row["adjacent_straight_loss_subtracted_pa"],
                "local_minor_loss_pa": row["local_minor_loss_pa"],
                "K_apparent": row["K_apparent"],
                "K_local_upper_bound": row["K_local"],
                "minor_fraction_pct_if_span_attributed": sep.get("minor_fraction_pct", ""),
                "phi_original": sep.get("phi_original", ""),
                "phi_pipe_only": sep.get("phi_pipe_only", ""),
                "fit_eligible": row["fit_eligible"],
                "validation_eligible": row["validation_eligible"],
                "quality_flags": row["quality_flags"],
                "scientific_use": corner_scientific_use(row),
                "critique": corner_critique(row),
                "source_bend_minor_loss_csv": row["source_bend_minor_loss_csv"],
            }
        )
    return rows


def corner_scientific_use(row: dict[str, str]) -> str:
    flags = row["quality_flags"]
    if "coarse_no_gci" in flags or "K_local_still_upper_bound" in flags:
        return "diagnostic_upper_bound_not_fit_admitted"
    if row["fit_eligible"] == "yes":
        return "candidate_fit_row"
    return "diagnostic_only"


def corner_critique(row: dict[str, str]) -> str:
    parts = ["feature_loss_computed_from_preserved_two_tap_rows"]
    if "tap_length_proxy_abs_dz_not_centerline_length" in row["quality_flags"]:
        parts.append("straight_loss_subtraction_uses_minimum_dz_proxy")
    if "K_local_still_upper_bound" in row["quality_flags"]:
        parts.append("K_local_is_upper_bound")
    if "coarse_no_gci" in row["quality_flags"]:
        parts.append("coarse_mesh_no_gci")
    if "recirculation_adjacent" in row["quality_flags"]:
        parts.append("recirculation_adjacent_limits_single_stream_fit")
    return ";".join(parts)


def aggregate_corner_summary(corner_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_feature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in corner_rows:
        by_feature[row["feature"]].append(row)
    rows: list[dict[str, Any]] = []
    for feature in CORNER_ORDER:
        values = by_feature.get(feature, [])
        if not values:
            continue
        rows.append(
            {
                "feature": feature,
                "case_count": len(values),
                "mean_K_apparent": mean(f(row, "K_apparent") for row in values),
                "min_K_apparent": min(f(row, "K_apparent") for row in values),
                "max_K_apparent": max(f(row, "K_apparent") for row in values),
                "mean_K_local_upper_bound": mean(f(row, "K_local_upper_bound") for row in values),
                "min_K_local_upper_bound": min(f(row, "K_local_upper_bound") for row in values),
                "max_K_local_upper_bound": max(f(row, "K_local_upper_bound") for row in values),
                "fit_admitted_count": sum(row["scientific_use"] == "candidate_fit_row" for row in values),
                "scientific_status": "diagnostic_upper_bound_not_fit_admitted",
            }
        )
    return rows


def write_review_md(
    pressure_case_rows: list[dict[str, Any]],
    pressure_branch_rows: list[dict[str, Any]],
    junction_rows: list[dict[str, Any]],
    corner_summary_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    lines = [
        "# Pressure Map Scientific Review and Junction/Corner State",
        "",
        "## Bottom Line",
        "",
        "The AGENT-457 pressure-map outputs make sense as complete, provenance-rich station and branch pressure maps. They do not make sense as admitted hydraulic closure evidence. Every branch remains diagnostic because the current harvest still lacks accepted distance normalization, straight-loss subtraction, low-recirculation masks, and mesh/GCI admission.",
        "",
        "The junction heat-loss evidence is real at role/accounting level for Salt2-4, but it is aggregate `junction_or_stub` heat transfer, not per-junction closure. Corner pressure-drop evidence exists and is directionally useful, but current K values are diagnostic upper bounds, not admitted component-K coefficients.",
        "",
        "## Pressure Map Review",
        "",
        f"- Cases reviewed: `{summary['pressure_case_count']}`",
        f"- Branch rows reviewed: `{summary['pressure_branch_rows']}`",
        f"- Station rows reviewed: `{summary['pressure_station_rows']}`",
        f"- Branch rows blocked by recirculation mask: `{summary['recirculation_blocked_branch_rows']}`",
        f"- Fit-admitted pressure rows: `{summary['fit_admitted_pressure_rows']}`",
        f"- Static-vs-p_rgh branch delta sign differences in AGENT-457 rows: `{summary['static_prgh_delta_sign_diff_rows']}`",
        "",
        "| case | branch rows | blocked | static/p_rgh sign diff | max reverse proxy | status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in pressure_case_rows:
        lines.append(
            f"| `{row['case_key']}` | {row['branch_rows']} | {row['recirculation_blocked_branch_count']} | "
            f"{row['static_vs_p_rgh_branch_delta_sign_diff_count']} | {float(row['max_reverse_area_fraction_proxy']):.3f} | "
            f"{row['overall_scientific_status']} |"
        )
    lines.extend(
        [
            "",
            "## What Looks Physically Coherent",
            "",
            "- Coverage is complete: every case has 30 stations and 6 branch rows.",
            "- The branch labels map to the correct physical loop locations: `lower_leg` is heater, `right_leg` is downcomer, `upper_leg` is cooled top leg.",
            "- Mainline Salt2/Salt3/Salt4 static branch means vary smoothly across the family rather than jumping randomly.",
            "- Salt2 +/-5Q and `val_salt2` sit near `salt2_mainline`, which is a useful consistency check for the postprocessing path.",
            "",
            "## What Does Not Support Closure Fitting Yet",
            "",
            "- Absolute static pressure is gauge/reference sensitive and hydrostatic dominated; it is not a cross-case closure metric by itself.",
            "- `p_rgh` deltas are the better hydraulic diagnostic, but the branch-level maps show static/p_rgh sign disagreements in several rows.",
            "- The AGENT-449 admission table reports 66/66 branches blocked by material recirculation mask and 0 true `f_D` or component-`K` rows admitted.",
            "- Upcomer/test-section branches are hybrid/recirculating lanes, not ordinary single-stream pipe-loss evidence.",
            "",
            "## Junction Heat Loss",
            "",
            "| case | role | realized W | direction | critique |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in junction_rows:
        if row["role_or_lane"] in {"junction_other", "junction_segment_realized_wallflux"}:
            lines.append(
                f"| `{row['case_id']}` | `{row['role_or_lane']}` | {float(row['cfd_realized_W']):.3f} | "
                f"{row['heat_direction']} | {row['critique']} |"
            )
    lines.extend(
        [
            "",
            "Interpretation: we understand that junction/stub surfaces remove nontrivial heat from the fluid in the realized CFD accounting. We do not yet understand it as a predictive per-junction closure because the evidence is aggregate, includes radiation in total `wallHeatFlux`, and is documented as diagnostic/non-predictive.",
            "",
            "## Corner Pressure Drops",
            "",
            "| corner | cases | mean K apparent | mean K local upper bound | status |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in corner_summary_rows:
        lines.append(
            f"| `{row['feature']}` | {row['case_count']} | {float(row['mean_K_apparent']):.3f} | "
            f"{float(row['mean_K_local_upper_bound']):.3f} | {row['scientific_status']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: corner pressure drops are identified and roughly quantified from preserved two-tap rows. The evidence supports the statement that corners contribute materially but do not dominate the hydraulic discrepancy: prior separation reduced phi by about 9-10% in heater/downcomer/cooler and about 21% on average in upcomer lanes. However, K values remain upper-bound diagnostics because the straight-loss subtraction uses an `abs(dz)` tap-length proxy, rows are coarse/no-GCI, and recirculation affects adjacent upcomer spans.",
            "",
            "## Next Scientific Gates",
            "",
            "1. For pressure closure: extract centerline-distance-normalized tap pairs, subtract straight losses with accepted geometry, use low-recirculation masks, and repeat on admitted mesh/GCI rows.",
            "2. For junction heat: split `junction_other` into the four junction/stub surfaces, preserve radiation/convective components or explicitly document inseparability, and build setup-only predictive parameters without realized `wallHeatFlux` as runtime input.",
            "3. For corner K: rerun two-tap corner extraction with full tap centerline lengths and mesh-refinement/GCI before admitting any component-K coefficients.",
        ]
    )
    (OUT / "scientific_review.md").write_text("\n".join(lines) + "\n")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    branch_rows = read_csv(PRESSURE_BRANCH)
    station_rows = read_csv(PRESSURE_STATION)
    provenance_rows = read_csv(CASE_PROVENANCE)
    admission_rows = read_csv(PRESSURE_ADMISSION)
    role_rows = read_csv(HEAT_ROLE)
    segment_rows = read_csv(HEAT_SEGMENT)
    minor_rows = read_csv(MINOR_LOSS)
    separation_rows = read_csv(MINOR_LOSS_SEPARATION)

    pressure_branch_review = build_pressure_branch_review(branch_rows, admission_rows)
    pressure_case_review = build_pressure_case_review(pressure_branch_review, station_rows, provenance_rows)
    junction_heat_review = build_junction_heat_review(role_rows, segment_rows)
    corner_review = build_corner_review(minor_rows, separation_rows)
    corner_summary = aggregate_corner_summary(corner_review)

    write_csv(OUT / "pressure_branch_scientific_review.csv", pressure_branch_review)
    write_csv(OUT / "pressure_case_scientific_review.csv", pressure_case_review)
    write_csv(OUT / "junction_heat_loss_evidence_state.csv", junction_heat_review)
    write_csv(OUT / "corner_pressure_drop_evidence_state.csv", corner_review)
    write_csv(OUT / "corner_pressure_drop_summary.csv", corner_summary)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_type": "pressure_branch_map", "path": rel(PRESSURE_BRANCH), "use": "AGENT-457 branch pressure map reviewed"},
            {"source_type": "pressure_station_map", "path": rel(PRESSURE_STATION), "use": "AGENT-457 station pressure map reviewed"},
            {"source_type": "pressure_admission", "path": rel(PRESSURE_ADMISSION), "use": "AGENT-449 admission/recirculation/straight-loss state"},
            {"source_type": "heat_loss_role", "path": rel(HEAT_ROLE), "use": "Salt2-4 heat-loss role accounting including junction_other"},
            {"source_type": "heat_loss_segment", "path": rel(HEAT_SEGMENT), "use": "Salt2 segment-level realized-wallflux junction evidence"},
            {"source_type": "corner_minor_loss", "path": rel(MINOR_LOSS), "use": "two-tap corner pressure drop/K evidence"},
            {"source_type": "minor_loss_separation", "path": rel(MINOR_LOSS_SEPARATION), "use": "minor-loss contribution to phi by span"},
            {"source_type": "geometry_reference", "path": rel(GEOMETRY_REFERENCE), "use": "authoritative span naming and flow directions"},
        ],
        ["source_type", "path", "use"],
    )

    admission_summary = read_json(PRESSURE_ADMISSION_SUMMARY)
    minor_loss_summary = read_json(MINOR_LOSS_SUMMARY)
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "pressure_case_count": len(pressure_case_review),
        "pressure_station_rows": len(station_rows),
        "pressure_branch_rows": len(pressure_branch_review),
        "recirculation_blocked_branch_rows": sum(
            row["recirculation_mask_status"] == "blocked_material_recirculation_mask" for row in pressure_branch_review
        ),
        "fit_admitted_pressure_rows": sum(row["true_f_D_or_K_fit_admitted"] == "yes" for row in pressure_branch_review),
        "static_prgh_delta_sign_diff_rows": sum(
            row["static_prgh_delta_relation"] == "different_sign" for row in pressure_branch_review
        ),
        "agent449_pressure_definition_conflict_branch_rows": admission_summary["pressure_definition_conflict_branch_rows"],
        "junction_heat_rows": len(junction_heat_review),
        "junction_other_case_rows": sum(row["role_or_lane"] == "junction_other" for row in junction_heat_review),
        "corner_rows": len(corner_review),
        "corner_summary_rows": len(corner_summary),
        "minor_loss_separation_leg_class_summary": minor_loss_summary["leg_class_summary"],
        "bottom_line": "pressure_maps_are_location/provenance_diagnostic;no_hydraulic_fit_admission;aggregate_junction_heat_loss_understood_diagnostic;corner_K_understood_as_diagnostic_upper_bound",
        "outputs": {
            "pressure_case_review": rel(OUT / "pressure_case_scientific_review.csv"),
            "pressure_branch_review": rel(OUT / "pressure_branch_scientific_review.csv"),
            "junction_heat_loss_evidence_state": rel(OUT / "junction_heat_loss_evidence_state.csv"),
            "corner_pressure_drop_evidence_state": rel(OUT / "corner_pressure_drop_evidence_state.csv"),
            "scientific_review": rel(OUT / "scientific_review.md"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_review_md(pressure_case_review, pressure_branch_review, junction_heat_review, corner_summary, summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
