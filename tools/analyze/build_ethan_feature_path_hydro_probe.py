#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import (
    ROOT,
    csv_dump_rows,
    finite_float,
    load_salt_dashboard_rows,
    normalized_residual,
    require_columns,
    safe_mean,
    write_json,
)

FEATURE_INPUTS_CSV = ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package" / "salt_feature_correlation_inputs.csv"
CURRENT_FEATURE_PROXY_CSV = ROOT / "reports" / "2026-06-19_ethan_salt_feature_hydraulic_hardening" / "feature_hydro_closure_timeseries.csv"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-22_ethan_feature_path_hydro_probe"
DEFAULT_SMOKE_OUTPUT_DIR = ROOT / "tmp" / "2026-06-22_ethan_feature_path_hydro_probe_smoke"
DEFAULT_WINDOW_STATION_COUNT = 3

FEATURE_CLASS_MAP = {
    "corner_lower_left": "bend",
    "corner_lower_right": "bend",
    "corner_upper_left": "bend",
    "corner_upper_right": "bend",
    "test_section_complex": "quartz_transition",
}

TIMESERIES_COLUMNS = [
    "source_id",
    "case_label",
    "case_order",
    "feature_name",
    "feature_class",
    "feature_kind",
    "time_s",
    "adjacent_major_spans",
    "start_patch",
    "end_patch",
    "start_span_name",
    "start_boundary_role",
    "start_boundary_labels",
    "start_window_station_count",
    "start_window_support_fraction",
    "start_window_face_count",
    "start_window_area_m2",
    "start_window_s_min_m",
    "start_window_s_max_m",
    "start_window_p_wall_area_avg_pa",
    "start_window_p_rgh_wall_area_avg_pa",
    "start_window_t_wall_area_avg_k",
    "end_span_name",
    "end_boundary_role",
    "end_boundary_labels",
    "end_window_station_count",
    "end_window_support_fraction",
    "end_window_face_count",
    "end_window_area_m2",
    "end_window_s_min_m",
    "end_window_s_max_m",
    "end_window_p_wall_area_avg_pa",
    "end_window_p_rgh_wall_area_avg_pa",
    "end_window_t_wall_area_avg_k",
    "window_delta_p_pa",
    "window_abs_delta_p_pa",
    "window_delta_p_rgh_pa",
    "window_abs_delta_p_rgh_pa",
    "window_hydro_correction_pa",
    "window_hydro_correction_abs_pa",
    "endpoint_delta_p_pa",
    "endpoint_abs_delta_p_pa",
    "endpoint_delta_p_rgh_pa",
    "endpoint_abs_delta_p_rgh_pa",
    "endpoint_hydro_proxy_pa",
    "endpoint_hydro_proxy_abs_pa",
    "existing_local_boundary_reference_dp_pa",
    "existing_feature_excess_dp_local_pa",
    "reference_major_dp_pa",
    "reference_length_m",
    "hydro_probe_gap_vs_endpoint_fraction",
    "probe_status",
    "probe_reason",
]

CASE_COLUMNS = [
    "source_id",
    "case_label",
    "case_order",
    "feature_name",
    "feature_class",
    "adjacent_major_spans",
    "time_row_count",
    "probe_ready_time_count",
    "partial_probe_time_count",
    "blocked_probe_time_count",
    "probe_ready_fraction",
    "probe_any_coverage_fraction",
    "min_window_support_fraction",
    "mean_window_support_fraction",
    "mean_window_abs_delta_p_pa",
    "mean_window_abs_delta_p_rgh_pa",
    "mean_window_hydro_correction_abs_pa",
    "mean_endpoint_hydro_proxy_abs_pa",
    "mean_existing_feature_excess_dp_local_pa",
    "mean_hydro_probe_gap_vs_endpoint_fraction",
    "status",
    "status_reason",
]

FEATURE_SUMMARY_COLUMNS = [
    "feature_name",
    "feature_class",
    "case_count",
    "probe_ready_case_count",
    "partial_probe_case_count",
    "blocked_case_count",
    "mean_probe_ready_fraction",
    "mean_window_hydro_correction_abs_pa",
    "mean_endpoint_hydro_proxy_abs_pa",
]


@dataclass(frozen=True)
class BoundaryCandidate:
    span_name: str
    boundary_role: str
    boundary_labels: tuple[str, ...]
    boundary_s_m: float


@dataclass(frozen=True)
class WindowProbe:
    span_name: str
    boundary_role: str
    boundary_labels: tuple[str, ...]
    station_count: int
    support_fraction: float
    face_count: int
    area_m2: float
    s_min_m: float
    s_max_m: float
    p_wall_area_avg_pa: float
    p_rgh_wall_area_avg_pa: float
    t_wall_area_avg_k: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an additive Salt retained-time feature-path hydro probe from the "
            "preserved June 15 live case-analysis artifacts without reopening the "
            "shared extractor path."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument("--window-station-count", type=int, default=DEFAULT_WINDOW_STATION_COUNT)
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def feature_class(feature_name: str) -> str:
    return FEATURE_CLASS_MAP.get(feature_name, "unclassified_feature")


def load_feature_inputs(source_ids: set[str] | None = None) -> dict[tuple[str, str], tuple[str, ...]]:
    rows = load_csv_rows(FEATURE_INPUTS_CSV)
    require_columns(rows, ["source_id", "feature_name", "adjacent_major_spans"], FEATURE_INPUTS_CSV.name)
    output: dict[tuple[str, str], tuple[str, ...]] = {}
    for row in rows:
        source_id = row["source_id"]
        if source_ids and source_id not in source_ids:
            continue
        output[(source_id, row["feature_name"])] = tuple(part.strip() for part in row["adjacent_major_spans"].split("|") if part.strip())
    return output


def load_existing_proxy_rows(source_ids: set[str] | None = None) -> dict[tuple[str, str, float], dict[str, str]]:
    rows = load_csv_rows(CURRENT_FEATURE_PROXY_CSV)
    require_columns(
        rows,
        [
            "source_id",
            "feature_name",
            "time_s",
            "local_boundary_reference_dp_pa",
            "feature_excess_dp_local_pa",
        ],
        CURRENT_FEATURE_PROXY_CSV.name,
    )
    output: dict[tuple[str, str, float], dict[str, str]] = {}
    for row in rows:
        if source_ids and row["source_id"] not in source_ids:
            continue
        output[(row["source_id"], row["feature_name"], finite_float(row["time_s"]))] = row
    return output


def build_boundary_candidate_lookup(
    geometry_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> dict[str, list[BoundaryCandidate]]:
    by_span: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in geometry_rows:
        by_span[row["span_name"]].append(row)

    summary_by_span = {row["span_name"]: row for row in summary_rows}
    candidate_lookup: dict[str, list[BoundaryCandidate]] = defaultdict(list)
    for span_name, payload in by_span.items():
        if span_name not in summary_by_span:
            continue
        min_s = min(finite_float(row["s_span_m"]) for row in payload)
        max_s = max(finite_float(row["s_span_m"]) for row in payload)
        start_labels = tuple(sorted({row["segment_start_label"] for row in payload if math.isclose(finite_float(row["s_span_m"]), min_s, abs_tol=1e-12)}))
        end_labels = tuple(sorted({row["segment_end_label"] for row in payload if math.isclose(finite_float(row["s_span_m"]), max_s, abs_tol=1e-12)}))
        summary_row = summary_by_span[span_name]
        candidate_lookup[summary_row["start_patch"]].append(
            BoundaryCandidate(
                span_name=span_name,
                boundary_role="start",
                boundary_labels=start_labels,
                boundary_s_m=min_s,
            )
        )
        candidate_lookup[summary_row["end_patch"]].append(
            BoundaryCandidate(
                span_name=span_name,
                boundary_role="end",
                boundary_labels=end_labels,
                boundary_s_m=max_s,
            )
        )
    return candidate_lookup


def pick_nearest_stations(station_values: Iterable[float], boundary_s_m: float, station_count: int) -> list[float]:
    unique_values = sorted({value for value in station_values if math.isfinite(value)})
    ranked = sorted(unique_values, key=lambda value: (abs(value - boundary_s_m), value))
    return ranked[: max(station_count, 1)]


def area_weighted_mean(rows: list[dict[str, str]], value_key: str) -> float:
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        area = finite_float(row.get("area_m2"))
        value = finite_float(row.get(value_key))
        if not math.isfinite(area) or area <= 0.0 or not math.isfinite(value):
            continue
        numerator += area * value
        denominator += area
    if denominator <= 0.0:
        return math.nan
    return numerator / denominator


def build_window_probe(
    sample_rows: list[dict[str, str]],
    candidate: BoundaryCandidate,
    station_count: int,
) -> WindowProbe | None:
    stations = pick_nearest_stations((finite_float(row.get("s_span_m")) for row in sample_rows), candidate.boundary_s_m, station_count)
    selected = [row for row in sample_rows if any(math.isclose(finite_float(row.get("s_span_m")), station, abs_tol=1e-12) for station in stations)]
    if not selected:
        return None
    station_payload = [finite_float(row.get("s_span_m")) for row in selected if math.isfinite(finite_float(row.get("s_span_m")))]
    support_fraction = len(stations) / max(station_count, 1)
    area_values = [finite_float(row.get("area_m2")) for row in selected if math.isfinite(finite_float(row.get("area_m2")))]
    return WindowProbe(
        span_name=candidate.span_name,
        boundary_role=candidate.boundary_role,
        boundary_labels=candidate.boundary_labels,
        station_count=len(stations),
        support_fraction=support_fraction,
        face_count=len(selected),
        area_m2=sum(area_values) if area_values else math.nan,
        s_min_m=min(station_payload) if station_payload else math.nan,
        s_max_m=max(station_payload) if station_payload else math.nan,
        p_wall_area_avg_pa=area_weighted_mean(selected, "p_wall_pa"),
        p_rgh_wall_area_avg_pa=area_weighted_mean(selected, "p_rgh_wall_pa"),
        t_wall_area_avg_k=area_weighted_mean(selected, "t_wall_k"),
    )


def classify_time_row(row: dict[str, Any]) -> tuple[str, str]:
    min_support = min(finite_float(row.get("start_window_support_fraction")), finite_float(row.get("end_window_support_fraction")))
    if not math.isfinite(min_support) or min_support <= 0.0:
        return "blocked", "missing_endpoint_window_support"
    required_values = [
        finite_float(row.get("start_window_p_wall_area_avg_pa")),
        finite_float(row.get("start_window_p_rgh_wall_area_avg_pa")),
        finite_float(row.get("end_window_p_wall_area_avg_pa")),
        finite_float(row.get("end_window_p_rgh_wall_area_avg_pa")),
    ]
    if not all(math.isfinite(value) for value in required_values):
        return "blocked", "missing_finite_wall_window_average"
    if min_support < 1.0:
        return "partial", "incomplete_window_station_support"
    return "probe_ready", "full_window_support"


def classify_case_summary(row: dict[str, Any]) -> tuple[str, str]:
    probe_ready_fraction = finite_float(row.get("probe_ready_fraction"))
    probe_any_fraction = finite_float(row.get("probe_any_coverage_fraction"))
    if math.isfinite(probe_ready_fraction) and math.isclose(probe_ready_fraction, 1.0, abs_tol=1e-12):
        return "probe_ready_for_downstream_review", "all_retained_times_have_full_endpoint_window_support"
    if math.isfinite(probe_any_fraction) and probe_any_fraction > 0.0:
        return "partial_probe_only", "some_retained_times_have_endpoint_window_support_but_not_all"
    return "blocked", "no_retained_time_has_usable_endpoint_window_support"


def assemble_timeseries_rows(
    dashboard_rows: list[dict[str, str]],
    feature_inputs: dict[tuple[str, str], tuple[str, ...]],
    existing_proxy_rows: dict[tuple[str, str, float], dict[str, str]],
    station_count: int,
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for case_order, dashboard_row in enumerate(dashboard_rows):
        source_id = dashboard_row["source_id"]
        case_label = dashboard_row["display_label"]
        package_root = Path(dashboard_row["package_root"])
        summary_rows = load_csv_rows(package_root / "major_loss_summary.csv")
        feature_rows = load_csv_rows(package_root / "feature_minor_loss_timeseries.csv")
        geometry_rows = load_csv_rows(package_root / "raw_extraction" / "leg_wall_face_geometry.csv")
        sample_rows = load_csv_rows(package_root / "raw_extraction" / "leg_wall_face_samples.csv")
        require_columns(summary_rows, ["span_name", "start_patch", "end_patch"], f"{source_id}/major_loss_summary.csv")
        require_columns(
            feature_rows,
            [
                "source_id",
                "time_s",
                "feature_name",
                "feature_kind",
                "start_patch",
                "end_patch",
                "delta_p_pa",
                "delta_p_rgh_pa",
                "abs_delta_p_rgh_pa",
                "reference_length_m",
                "reference_major_dp_pa",
            ],
            f"{source_id}/feature_minor_loss_timeseries.csv",
        )
        require_columns(
            geometry_rows,
            ["span_name", "s_span_m", "segment_start_label", "segment_end_label"],
            f"{source_id}/raw_extraction/leg_wall_face_geometry.csv",
        )
        require_columns(
            sample_rows,
            ["time_s", "span_name", "s_span_m", "area_m2", "p_wall_pa", "p_rgh_wall_pa", "t_wall_k"],
            f"{source_id}/raw_extraction/leg_wall_face_samples.csv",
        )
        boundary_lookup = build_boundary_candidate_lookup(geometry_rows, summary_rows)
        samples_by_time_span: dict[tuple[float, str], list[dict[str, str]]] = defaultdict(list)
        for row in sample_rows:
            samples_by_time_span[(finite_float(row["time_s"]), row["span_name"])].append(row)

        for feature_row in feature_rows:
            feature_name = feature_row["feature_name"]
            adjacent_spans = feature_inputs[(source_id, feature_name)]
            time_s = finite_float(feature_row["time_s"])
            start_candidates = [candidate for candidate in boundary_lookup.get(feature_row["start_patch"], []) if candidate.span_name in adjacent_spans]
            end_candidates = [candidate for candidate in boundary_lookup.get(feature_row["end_patch"], []) if candidate.span_name in adjacent_spans]
            start_probe = build_window_probe(samples_by_time_span.get((time_s, start_candidates[0].span_name), []), start_candidates[0], station_count) if len(start_candidates) == 1 else None
            end_probe = build_window_probe(samples_by_time_span.get((time_s, end_candidates[0].span_name), []), end_candidates[0], station_count) if len(end_candidates) == 1 else None

            start_p = start_probe.p_wall_area_avg_pa if start_probe else math.nan
            end_p = end_probe.p_wall_area_avg_pa if end_probe else math.nan
            start_prgh = start_probe.p_rgh_wall_area_avg_pa if start_probe else math.nan
            end_prgh = end_probe.p_rgh_wall_area_avg_pa if end_probe else math.nan
            window_delta_p_pa = start_p - end_p if math.isfinite(start_p) and math.isfinite(end_p) else math.nan
            window_delta_p_rgh_pa = start_prgh - end_prgh if math.isfinite(start_prgh) and math.isfinite(end_prgh) else math.nan
            window_hydro_correction_pa = window_delta_p_pa - window_delta_p_rgh_pa if math.isfinite(window_delta_p_pa) and math.isfinite(window_delta_p_rgh_pa) else math.nan
            endpoint_delta_p_pa = finite_float(feature_row.get("delta_p_pa"))
            endpoint_delta_p_rgh_pa = finite_float(feature_row.get("delta_p_rgh_pa"))
            endpoint_hydro_proxy_pa = endpoint_delta_p_pa - endpoint_delta_p_rgh_pa if math.isfinite(endpoint_delta_p_pa) and math.isfinite(endpoint_delta_p_rgh_pa) else math.nan
            existing_proxy = existing_proxy_rows.get((source_id, feature_name, time_s), {})
            output_row = {
                "source_id": source_id,
                "case_label": case_label,
                "case_order": case_order,
                "feature_name": feature_name,
                "feature_class": feature_class(feature_name),
                "feature_kind": feature_row["feature_kind"],
                "time_s": time_s,
                "adjacent_major_spans": "|".join(adjacent_spans),
                "start_patch": feature_row["start_patch"],
                "end_patch": feature_row["end_patch"],
                "start_span_name": start_probe.span_name if start_probe else "",
                "start_boundary_role": start_probe.boundary_role if start_probe else "",
                "start_boundary_labels": "|".join(start_probe.boundary_labels) if start_probe else "",
                "start_window_station_count": start_probe.station_count if start_probe else 0,
                "start_window_support_fraction": start_probe.support_fraction if start_probe else 0.0,
                "start_window_face_count": start_probe.face_count if start_probe else 0,
                "start_window_area_m2": start_probe.area_m2 if start_probe else math.nan,
                "start_window_s_min_m": start_probe.s_min_m if start_probe else math.nan,
                "start_window_s_max_m": start_probe.s_max_m if start_probe else math.nan,
                "start_window_p_wall_area_avg_pa": start_p,
                "start_window_p_rgh_wall_area_avg_pa": start_prgh,
                "start_window_t_wall_area_avg_k": start_probe.t_wall_area_avg_k if start_probe else math.nan,
                "end_span_name": end_probe.span_name if end_probe else "",
                "end_boundary_role": end_probe.boundary_role if end_probe else "",
                "end_boundary_labels": "|".join(end_probe.boundary_labels) if end_probe else "",
                "end_window_station_count": end_probe.station_count if end_probe else 0,
                "end_window_support_fraction": end_probe.support_fraction if end_probe else 0.0,
                "end_window_face_count": end_probe.face_count if end_probe else 0,
                "end_window_area_m2": end_probe.area_m2 if end_probe else math.nan,
                "end_window_s_min_m": end_probe.s_min_m if end_probe else math.nan,
                "end_window_s_max_m": end_probe.s_max_m if end_probe else math.nan,
                "end_window_p_wall_area_avg_pa": end_p,
                "end_window_p_rgh_wall_area_avg_pa": end_prgh,
                "end_window_t_wall_area_avg_k": end_probe.t_wall_area_avg_k if end_probe else math.nan,
                "window_delta_p_pa": window_delta_p_pa,
                "window_abs_delta_p_pa": abs(window_delta_p_pa) if math.isfinite(window_delta_p_pa) else math.nan,
                "window_delta_p_rgh_pa": window_delta_p_rgh_pa,
                "window_abs_delta_p_rgh_pa": abs(window_delta_p_rgh_pa) if math.isfinite(window_delta_p_rgh_pa) else math.nan,
                "window_hydro_correction_pa": window_hydro_correction_pa,
                "window_hydro_correction_abs_pa": abs(window_hydro_correction_pa) if math.isfinite(window_hydro_correction_pa) else math.nan,
                "endpoint_delta_p_pa": endpoint_delta_p_pa,
                "endpoint_abs_delta_p_pa": abs(endpoint_delta_p_pa) if math.isfinite(endpoint_delta_p_pa) else math.nan,
                "endpoint_delta_p_rgh_pa": endpoint_delta_p_rgh_pa,
                "endpoint_abs_delta_p_rgh_pa": abs(endpoint_delta_p_rgh_pa) if math.isfinite(endpoint_delta_p_rgh_pa) else math.nan,
                "endpoint_hydro_proxy_pa": endpoint_hydro_proxy_pa,
                "endpoint_hydro_proxy_abs_pa": abs(endpoint_hydro_proxy_pa) if math.isfinite(endpoint_hydro_proxy_pa) else math.nan,
                "existing_local_boundary_reference_dp_pa": finite_float(existing_proxy.get("local_boundary_reference_dp_pa")),
                "existing_feature_excess_dp_local_pa": finite_float(existing_proxy.get("feature_excess_dp_local_pa")),
                "reference_major_dp_pa": finite_float(feature_row.get("reference_major_dp_pa")),
                "reference_length_m": finite_float(feature_row.get("reference_length_m")),
                "hydro_probe_gap_vs_endpoint_fraction": normalized_residual(window_hydro_correction_pa - endpoint_hydro_proxy_pa, window_hydro_correction_pa),
            }
            probe_status, probe_reason = classify_time_row(output_row)
            output_row["probe_status"] = probe_status
            output_row["probe_reason"] = probe_reason
            rows_out.append(output_row)
    return rows_out


def assemble_case_rows(timeseries_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in timeseries_rows:
        grouped[(row["source_id"], row["feature_name"])].append(row)
    case_rows: list[dict[str, Any]] = []
    for (_, _), payload in sorted(grouped.items(), key=lambda item: (int(item[1][0]["case_order"]), item[1][0]["feature_name"])):
        summary = {
            "source_id": payload[0]["source_id"],
            "case_label": payload[0]["case_label"],
            "case_order": payload[0]["case_order"],
            "feature_name": payload[0]["feature_name"],
            "feature_class": payload[0]["feature_class"],
            "adjacent_major_spans": payload[0]["adjacent_major_spans"],
            "time_row_count": len(payload),
            "probe_ready_time_count": sum(1 for row in payload if row["probe_status"] == "probe_ready"),
            "partial_probe_time_count": sum(1 for row in payload if row["probe_status"] == "partial"),
            "blocked_probe_time_count": sum(1 for row in payload if row["probe_status"] == "blocked"),
            "probe_ready_fraction": sum(1 for row in payload if row["probe_status"] == "probe_ready") / max(len(payload), 1),
            "probe_any_coverage_fraction": sum(1 for row in payload if row["probe_status"] != "blocked") / max(len(payload), 1),
            "min_window_support_fraction": min(
                min(finite_float(row["start_window_support_fraction"]), finite_float(row["end_window_support_fraction"])) for row in payload
            ),
            "mean_window_support_fraction": safe_mean(
                min(finite_float(row["start_window_support_fraction"]), finite_float(row["end_window_support_fraction"])) for row in payload
            ),
            "mean_window_abs_delta_p_pa": safe_mean(finite_float(row["window_abs_delta_p_pa"]) for row in payload),
            "mean_window_abs_delta_p_rgh_pa": safe_mean(finite_float(row["window_abs_delta_p_rgh_pa"]) for row in payload),
            "mean_window_hydro_correction_abs_pa": safe_mean(finite_float(row["window_hydro_correction_abs_pa"]) for row in payload),
            "mean_endpoint_hydro_proxy_abs_pa": safe_mean(finite_float(row["endpoint_hydro_proxy_abs_pa"]) for row in payload),
            "mean_existing_feature_excess_dp_local_pa": safe_mean(finite_float(row["existing_feature_excess_dp_local_pa"]) for row in payload),
            "mean_hydro_probe_gap_vs_endpoint_fraction": safe_mean(finite_float(row["hydro_probe_gap_vs_endpoint_fraction"]) for row in payload),
        }
        status, reason = classify_case_summary(summary)
        summary["status"] = status
        summary["status_reason"] = reason
        case_rows.append(summary)
    return case_rows


def assemble_feature_summary_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["feature_name"]].append(row)
    summary_rows: list[dict[str, Any]] = []
    for feature_name, payload in sorted(grouped.items()):
        summary_rows.append(
            {
                "feature_name": feature_name,
                "feature_class": payload[0]["feature_class"],
                "case_count": len(payload),
                "probe_ready_case_count": sum(1 for row in payload if row["status"] == "probe_ready_for_downstream_review"),
                "partial_probe_case_count": sum(1 for row in payload if row["status"] == "partial_probe_only"),
                "blocked_case_count": sum(1 for row in payload if row["status"] == "blocked"),
                "mean_probe_ready_fraction": safe_mean(finite_float(row["probe_ready_fraction"]) for row in payload),
                "mean_window_hydro_correction_abs_pa": safe_mean(finite_float(row["mean_window_hydro_correction_abs_pa"]) for row in payload),
                "mean_endpoint_hydro_proxy_abs_pa": safe_mean(finite_float(row["mean_endpoint_hydro_proxy_abs_pa"]) for row in payload),
            }
        )
    return summary_rows


def write_readme(path: Path, summary: dict[str, Any], station_count: int) -> None:
    content = f"""# Ethan Feature-Path Hydro Probe

Generated: `2026-06-22`

## Purpose

This package builds a fresh additive retained-time probe for the Salt feature
hydraulic blocker. It reconstructs endpoint-adjacent wall `p` and `p_rgh`
windows from the preserved June 15 wall-face samples and reports what those
windows imply for the still-blocked hydro term.

The package is deliberately scoped as a probe:

- it does **not** edit any shared extractor
- it does **not** claim a defended full feature-path hydro integral
- it does **not** promote feature `K_eff`

## Inputs

- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/salt_feature_correlation_inputs.csv`
- `reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_hydro_closure_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/feature_minor_loss_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/raw_extraction/leg_wall_face_geometry.csv`
- `tmp/2026-06-15_live_case_analysis/**/raw_extraction/leg_wall_face_samples.csv`

## Window rule

- endpoint window size: `{station_count}` nearest unique `s_span_m` stations on each adjacent span side
- endpoint-to-endpoint wall window deltas are area-weighted across the selected face rows
- the hydro candidate reported here is `Delta p_wall - Delta p_rgh_wall` from those endpoint windows

## Output tables

- `feature_path_hydro_probe_timeseries.csv`
  One retained-time row per case-feature with both endpoint windows, wall means,
  and the hydro-correction candidate.
- `feature_path_hydro_probe_case_summary.csv`
  One case-feature summary row with coverage and consistency counts.
- `feature_path_hydro_probe_feature_summary.csv`
  Aggregated feature-family view across the Salt cases.
- `feature_path_hydro_probe_blockers.csv`
  The remaining interpretation boundary and why this probe stops short of a defended fit.

## Counts

- case-feature rows: `{summary["feature_case_row_count"]}`
- retained-time rows: `{summary["feature_time_row_count"]}`
- probe-ready rows: `{summary["probe_ready_time_row_count"]}`
- partial rows: `{summary["partial_time_row_count"]}`
- blocked rows: `{summary["blocked_time_row_count"]}`
"""
    path.write_text(content, encoding="utf-8")


def write_math_companion(path: Path) -> None:
    content = """# Math Companion

For each retained-time feature row:

- choose the nearest wall-face stations to the feature-side boundary on the
  start adjacent span
- choose the nearest wall-face stations to the feature-side boundary on the end
  adjacent span
- compute area-weighted wall means on each side:
  - `p_start,wall`
  - `p_end,wall`
  - `p_rgh,start,wall`
  - `p_rgh,end,wall`
- compute endpoint-window deltas:
  - `Delta p_window = p_start,wall - p_end,wall`
  - `Delta p_rgh_window = p_rgh,start,wall - p_rgh,end,wall`
- compute the retained-time hydro candidate:
  - `Delta p_hydro,candidate = Delta p_window - Delta p_rgh_window`

Interpretation boundary:

- this is an endpoint-adjacent wall-window probe, not a defended path integral
- it is useful for proving whether the remaining blocker is mostly support,
  mostly hydro-correction magnitude, or mostly method mismatch against the
  existing endpoint proxy
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    dashboard_rows = load_salt_dashboard_rows(source_ids)
    feature_inputs = load_feature_inputs(source_ids)
    existing_proxy_rows = load_existing_proxy_rows(source_ids)
    timeseries_rows = assemble_timeseries_rows(dashboard_rows, feature_inputs, existing_proxy_rows, station_count=args.window_station_count)
    case_rows = assemble_case_rows(timeseries_rows)
    feature_summary_rows = assemble_feature_summary_rows(case_rows)
    blocker_rows = [
        {
            "dependency_or_gap": "feature_keff_defense",
            "current_status": "not_defensible_yet",
            "remaining_requirement": "full retained-time feature-path hydro or density integral, not only endpoint-adjacent wall windows",
            "why_probe_still_helps": "it exposes whether the blocker is now coverage, endpoint hydro magnitude, or mismatch versus the current endpoint proxy",
        }
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "feature_path_hydro_probe_timeseries.csv", timeseries_rows, TIMESERIES_COLUMNS)
    csv_dump_rows(output_dir / "feature_path_hydro_probe_case_summary.csv", case_rows, CASE_COLUMNS)
    csv_dump_rows(output_dir / "feature_path_hydro_probe_feature_summary.csv", feature_summary_rows, FEATURE_SUMMARY_COLUMNS)
    csv_dump_rows(output_dir / "feature_path_hydro_probe_blockers.csv", blocker_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "feature_case_row_count": len(case_rows),
        "feature_time_row_count": len(timeseries_rows),
        "probe_ready_time_row_count": sum(1 for row in timeseries_rows if row["probe_status"] == "probe_ready"),
        "partial_time_row_count": sum(1 for row in timeseries_rows if row["probe_status"] == "partial"),
        "blocked_time_row_count": sum(1 for row in timeseries_rows if row["probe_status"] == "blocked"),
        "case_status_counts": dict(Counter(row["status"] for row in case_rows)),
        "feature_status_counts": dict(Counter(row["feature_name"] for row in case_rows)),
        "window_station_count": args.window_station_count,
    }
    write_json(output_dir / "summary.json", summary)
    write_readme(output_dir / "README.md", summary, station_count=args.window_station_count)
    write_math_companion(output_dir / "MATH_COMPANION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
