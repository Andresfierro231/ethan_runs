#!/usr/bin/env python3
"""Build a PM10 recirculation-aware residual/readiness scorecard.

This package uses the repaired PM10 matched-plane extraction as recirculation
evidence. It does not promote PM10 to ordinary pipe fits, model-selection rows,
or runtime inputs.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


DATE = "2026-07-20"
DEFAULT_PM10_ADMISSION_DIR = (
    ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission"
)
DEFAULT_FEATURE_MATRIX = DEFAULT_PM10_ADMISSION_DIR / "pm10_recirculation_feature_matrix.csv"
DEFAULT_ANCHOR_ADMISSION = DEFAULT_PM10_ADMISSION_DIR / "pm10_recirculation_anchor_admission.csv"
DEFAULT_HYBRID_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract"
    / "hybrid_1d_model_contract.csv"
)
DEFAULT_DIRECT_DRY_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_direct_recirc_model_forms_and_dry_scorers"
    / "upcomer_hybrid_dry_scorecard.csv"
)
DEFAULT_PM10_RESIDUAL_TARGETS = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets"
    / "pm10_same_window_residual_targets.csv"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_recirc_hybrid_residual_scorecard"
)
DEFAULT_RESIDUAL_CANDIDATES = (
    DEFAULT_PM10_RESIDUAL_TARGETS,
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_isolated_relaunch_post_exit_rollup"
    / "pressure_upcomer_admission_rollup.csv",
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_post_3305547_harvest_wrapper"
    / "pressure_upcomer_admission_rollup.csv",
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer"
    / "recirc_residual_scorecard.csv",
)

PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")

FEATURE_SUMMARY_FIELDS = [
    "case_key",
    "plane_rows",
    "representative_time_s",
    "recirculation_lane",
    "max_RAF",
    "max_RMF",
    "max_SVF",
    "max_Ri",
    "min_abs_delta_T_wall_bulk_K",
    "mean_abs_delta_T_wall_bulk_K",
    "mean_wallHeatFlux_W_m2",
    "inlet_severity",
    "mid_severity",
    "outlet_severity",
    "severity_gradient_outlet_minus_inlet",
    "w_recirc_dry",
    "severity_only_score",
    "mixing_penalty_proxy",
    "outlet_loss_proxy",
    "plane_gradient_proxy",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "hybrid_validation_allowed",
    "ordinary_pipe_fit_allowed",
    "runtime_input_allowed_now",
    "source_paths",
]

RESIDUAL_JOIN_FIELDS = [
    "case_key",
    "target_status",
    "residual_source_id",
    "residual_metric",
    "residual_value",
    "residual_abs_value",
    "residual_row_status",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "blockers",
    "source_paths",
]

MODEL_SCORE_FIELDS = [
    "case_key",
    "model_form_id",
    "model_form_label",
    "allowed_label",
    "forbidden_labels",
    "target_status",
    "residual_metric",
    "residual_value",
    "diagnostic_score",
    "residual_weighted_score",
    "score_use",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "blockers",
    "source_paths",
]

BLOCKER_FIELDS = [
    "priority",
    "case_key",
    "blocker_id",
    "status",
    "unblock_action",
    "evidence_required",
    "source_paths",
]

MANIFEST_FIELDS = ["source_id", "path", "exists", "role"]

MODEL_FORMS = [
    {
        "model_form_id": "PM10-RD1",
        "model_form_label": "recirculation severity diagnostic",
        "allowed_label": "regime_diagnostic",
        "proxy_field": "severity_only_score",
    },
    {
        "model_form_id": "PM10-MP1",
        "model_form_label": "wall-bulk mixing penalty proxy",
        "allowed_label": "mixing_penalty",
        "proxy_field": "mixing_penalty_proxy",
    },
    {
        "model_form_id": "PM10-SL1",
        "model_form_label": "outlet section-effective loss proxy",
        "allowed_label": "section_effective_loss",
        "proxy_field": "outlet_loss_proxy",
    },
    {
        "model_form_id": "PM10-PG1",
        "model_form_label": "plane severity gradient proxy",
        "allowed_label": "regime_diagnostic",
        "proxy_field": "plane_gradient_proxy",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, precision: int = 10) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "" if value is None else str(value)
    return f"{parsed:.{precision}g}"


def finite_values(values: Iterable[Any]) -> list[float]:
    return [parsed for value in values if (parsed := parse_float(value)) is not None]


def mean(values: Iterable[Any]) -> float | None:
    finite = finite_values(values)
    if not finite:
        return None
    return sum(finite) / len(finite)


def clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def recirc_weight(raf: float | None, rmf: float | None, ri: float | None, svf: float | None) -> float:
    values = [value for value in (raf, rmf, svf) if value is not None]
    if ri is not None:
        values.append(clamp01(ri))
    return clamp01(max(values, default=0.0))


def unique_join(values: Iterable[str]) -> str:
    seen: list[str] = []
    for value in values:
        for part in str(value).split(";"):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
    return ";".join(seen)


def normalized_case_key(value: str) -> str:
    return (
        value.strip()
        .replace("_jin", "")
        .replace("_kirst", "")
        .replace("_corrected", "")
        .replace("_continuation", "")
    )


def plane_key(plane_location: str) -> str:
    lower = plane_location.lower()
    if "inlet" in lower:
        return "inlet"
    if "mid" in lower or "span" in lower:
        return "mid"
    if "outlet" in lower:
        return "outlet"
    return lower


def rows_by_case(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row.get("case_key", ""), []).append(row)
    return grouped


def case_feature_summaries(
    feature_rows: list[dict[str, str]],
    admission_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped = rows_by_case(feature_rows)
    admission_by_case = {row.get("case_key", ""): row for row in admission_rows}
    summaries: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        rows = grouped.get(case_key, [])
        admission = admission_by_case.get(case_key, {})
        raf_values = finite_values(row.get("reverse_area_fraction") for row in rows)
        rmf_values = finite_values(row.get("reverse_mass_fraction") for row in rows)
        svf_values = finite_values(row.get("secondary_velocity_fraction") for row in rows)
        ri_values = finite_values(row.get("Ri") for row in rows)
        delta_values = finite_values(row.get("delta_T_wall_bulk_K") for row in rows)
        abs_delta_values = [abs(value) for value in delta_values]
        wall_flux_values = finite_values(row.get("wallHeatFlux_W_m2") for row in rows)

        max_raf = max(raf_values, default=None)
        max_rmf = max(rmf_values, default=None)
        max_svf = max(svf_values, default=None)
        max_ri = max(ri_values, default=None)
        min_abs_delta = min(abs_delta_values, default=None)
        mean_abs_delta = mean(abs_delta_values)
        mean_wall_flux = mean(wall_flux_values)
        w_recirc = recirc_weight(max_raf, max_rmf, max_ri, max_svf)

        severity_by_plane: dict[str, float] = {}
        rmf_by_plane: dict[str, float] = {}
        svf_by_plane: dict[str, float] = {}
        for row in rows:
            key = plane_key(row.get("plane_location", ""))
            raf = parse_float(row.get("reverse_area_fraction"))
            rmf = parse_float(row.get("reverse_mass_fraction"))
            ri = parse_float(row.get("Ri"))
            svf = parse_float(row.get("secondary_velocity_fraction"))
            severity_by_plane[key] = recirc_weight(raf, rmf, ri, svf)
            if rmf is not None:
                rmf_by_plane[key] = rmf
            if svf is not None:
                svf_by_plane[key] = svf

        inlet_severity = severity_by_plane.get("inlet")
        mid_severity = severity_by_plane.get("mid")
        outlet_severity = severity_by_plane.get("outlet")
        gradient = (
            outlet_severity - inlet_severity
            if outlet_severity is not None and inlet_severity is not None
            else None
        )
        outlet_loss = None
        if "outlet" in rmf_by_plane and "outlet" in svf_by_plane:
            outlet_loss = rmf_by_plane["outlet"] * svf_by_plane["outlet"]

        source_paths = unique_join(row.get("source_paths", "") for row in rows)
        summaries.append(
            {
                "case_key": case_key,
                "plane_rows": len(rows),
                "representative_time_s": unique_join(row.get("representative_time_s", "") for row in rows),
                "recirculation_lane": "recirculating_upcomer_effective",
                "max_RAF": fmt(max_raf),
                "max_RMF": fmt(max_rmf),
                "max_SVF": fmt(max_svf),
                "max_Ri": fmt(max_ri),
                "min_abs_delta_T_wall_bulk_K": fmt(min_abs_delta),
                "mean_abs_delta_T_wall_bulk_K": fmt(mean_abs_delta),
                "mean_wallHeatFlux_W_m2": fmt(mean_wall_flux),
                "inlet_severity": fmt(inlet_severity),
                "mid_severity": fmt(mid_severity),
                "outlet_severity": fmt(outlet_severity),
                "severity_gradient_outlet_minus_inlet": fmt(gradient),
                "w_recirc_dry": fmt(w_recirc),
                "severity_only_score": fmt(w_recirc),
                "mixing_penalty_proxy": fmt(w_recirc * mean_abs_delta if mean_abs_delta is not None else None),
                "outlet_loss_proxy": fmt(outlet_loss),
                "plane_gradient_proxy": fmt(abs(gradient) if gradient is not None else None),
                "recirculation_anchor_allowed": admission.get("recirculation_anchor_allowed", "no"),
                "recirculation_calibration_allowed": admission.get("recirculation_calibration_allowed", "no"),
                "hybrid_validation_allowed": admission.get("hybrid_validation_allowed", "no"),
                "ordinary_pipe_fit_allowed": admission.get("ordinary_pipe_fit_allowed", "no"),
                "runtime_input_allowed_now": "no",
                "source_paths": source_paths,
            }
        )
    return summaries


def case_matches(row_case_key: str, pm10_case_key: str) -> bool:
    if row_case_key == pm10_case_key:
        return True
    return normalized_case_key(row_case_key) == normalized_case_key(pm10_case_key)


def numeric_residual_metrics(row: dict[str, str]) -> list[tuple[str, float]]:
    declared_metric = row.get("residual_metric", "").strip()
    if declared_metric:
        declared_value = parse_float(row.get(declared_metric))
        if declared_value is not None:
            return [(declared_metric, declared_value)]
    metrics: list[tuple[str, float]] = []
    skip_tokens = ("status", "path", "source", "blocker", "reason", "classification", "features")
    for key, value in row.items():
        lower = key.lower()
        if any(token in lower for token in skip_tokens):
            continue
        if "resid" not in lower and "residual" not in lower and "error" not in lower and "k_eff_recirc" not in lower:
            continue
        parsed = parse_float(value)
        if parsed is not None:
            metrics.append((key, parsed))
    return metrics


def residual_join_rows(
    feature_summaries: list[dict[str, Any]],
    residual_candidate_paths: Iterable[Path],
) -> list[dict[str, Any]]:
    candidate_paths = list(residual_candidate_paths)
    rows: list[dict[str, Any]] = []
    for summary in feature_summaries:
        case_key = str(summary["case_key"])
        matched_without_metric: list[str] = []
        matched_with_metric = False
        for source_path in candidate_paths:
            for source_row in read_csv(source_path):
                row_case_key = source_row.get("case_key") or source_row.get("case_id") or source_row.get("row_id") or ""
                if not case_matches(row_case_key, case_key):
                    continue
                metrics = numeric_residual_metrics(source_row)
                if not metrics:
                    matched_without_metric.append(rel(source_path))
                    continue
                matched_with_metric = True
                residual_status = (
                    source_row.get("Delta_p_resid_status")
                    or source_row.get("target_status")
                    or source_row.get("admission_status")
                    or source_row.get("parse_status")
                    or "residual_metric_present"
                )
                for metric, value in metrics:
                    rows.append(
                        {
                            "case_key": case_key,
                            "target_status": "residual_target_available",
                            "residual_source_id": source_path.stem,
                            "residual_metric": metric,
                            "residual_value": fmt(value),
                            "residual_abs_value": fmt(abs(value)),
                            "residual_row_status": residual_status,
                            "fit_allowed_now": "no",
                            "model_selection_allowed_now": "no",
                            "runtime_input_allowed_now": "no",
                            "blockers": "recirculation_policy_split_score_required;mesh_time_uq_required",
                            "source_paths": unique_join([summary.get("source_paths", ""), rel(source_path)]),
                        }
                    )
        if matched_with_metric:
            continue
        if matched_without_metric:
            rows.append(
                {
                    "case_key": case_key,
                    "target_status": "matched_pm10_source_without_pressure_or_thermal_residual",
                    "residual_source_id": "matched_source_without_metric",
                    "residual_metric": "",
                    "residual_value": "",
                    "residual_abs_value": "",
                    "residual_row_status": "no_numeric_residual_metric_columns",
                    "fit_allowed_now": "no",
                    "model_selection_allowed_now": "no",
                    "runtime_input_allowed_now": "no",
                    "blockers": "same_window_pm10_pressure_or_thermal_residual_missing",
                    "source_paths": unique_join([summary.get("source_paths", ""), *matched_without_metric]),
                }
            )
        else:
            rows.append(
                {
                    "case_key": case_key,
                    "target_status": "missing_pm10_pressure_or_thermal_residual",
                    "residual_source_id": "none",
                    "residual_metric": "",
                    "residual_value": "",
                    "residual_abs_value": "",
                    "residual_row_status": "no_pm10_case_match_in_residual_candidates",
                    "fit_allowed_now": "no",
                    "model_selection_allowed_now": "no",
                    "runtime_input_allowed_now": "no",
                    "blockers": "same_window_pm10_pressure_or_thermal_residual_missing",
                    "source_paths": unique_join([summary.get("source_paths", ""), *(rel(path) for path in candidate_paths)]),
                }
            )
    return rows


def first_residual_by_case(residual_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_case: dict[str, dict[str, Any]] = {}
    for row in residual_rows:
        case_key = str(row.get("case_key", ""))
        if case_key not in by_case or row.get("target_status") == "residual_target_available":
            by_case[case_key] = row
    return by_case


def model_score_rows(
    feature_summaries: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    residual_by_case = first_residual_by_case(residual_rows)
    rows: list[dict[str, Any]] = []
    for summary in feature_summaries:
        residual = residual_by_case.get(str(summary["case_key"]), {})
        target_available = residual.get("target_status") == "residual_target_available"
        residual_abs = parse_float(residual.get("residual_abs_value"))
        for form in MODEL_FORMS:
            diagnostic_score = parse_float(summary.get(form["proxy_field"]))
            weighted = (
                diagnostic_score * residual_abs
                if target_available and diagnostic_score is not None and residual_abs is not None
                else None
            )
            rows.append(
                {
                    "case_key": summary["case_key"],
                    "model_form_id": form["model_form_id"],
                    "model_form_label": form["model_form_label"],
                    "allowed_label": form["allowed_label"],
                    "forbidden_labels": "single_stream_Nu;single_stream_f_D;component_K",
                    "target_status": residual.get("target_status", "missing_pm10_pressure_or_thermal_residual"),
                    "residual_metric": residual.get("residual_metric", ""),
                    "residual_value": residual.get("residual_value", ""),
                    "diagnostic_score": fmt(diagnostic_score),
                    "residual_weighted_score": fmt(weighted),
                    "score_use": (
                        "residual_weighted_candidate_ranking_only"
                        if target_available
                        else "diagnostic_readiness_only_residual_target_missing"
                    ),
                    "fit_allowed_now": "no",
                    "model_selection_allowed_now": "no",
                    "runtime_input_allowed_now": "no",
                    "blockers": (
                        "split_policy_update_and_mesh_time_uq_required"
                        if target_available
                        else "same_window_pm10_pressure_or_thermal_residual_missing;mesh_time_uq_required"
                    ),
                    "source_paths": unique_join([summary.get("source_paths", ""), residual.get("source_paths", "")]),
                }
            )
    return rows


def blocker_rows(
    feature_summaries: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    residual_by_case = first_residual_by_case(residual_rows)
    rows: list[dict[str, Any]] = []
    for summary in feature_summaries:
        case_key = str(summary["case_key"])
        residual = residual_by_case.get(case_key, {})
        if residual.get("target_status") != "residual_target_available":
            rows.append(
                {
                    "priority": 1,
                    "case_key": case_key,
                    "blocker_id": "PM10_RESIDUAL_TARGET",
                    "status": residual.get("target_status", "missing_pm10_pressure_or_thermal_residual"),
                    "unblock_action": "extract same-window pressure/upcomer or thermal closure residual for the PM10 matched-plane time window",
                    "evidence_required": "pressure residual movement or thermal closure residual joined by PM10 case_key",
                    "source_paths": residual.get("source_paths", summary.get("source_paths", "")),
                }
            )
        rows.extend(
            [
                {
                    "priority": 2,
                    "case_key": case_key,
                    "blocker_id": "PM10_MESH_TIME_UQ",
                    "status": "missing",
                    "unblock_action": "attach mesh/time uncertainty for PM10 recirculation metrics and residual targets",
                    "evidence_required": "same-QOI uncertainty bound for RAF/RMF/SVF/Ri and residual target",
                    "source_paths": summary.get("source_paths", ""),
                },
                {
                    "priority": 3,
                    "case_key": case_key,
                    "blocker_id": "PM10_TRANSITION_BRACKET",
                    "status": "not_observed_in_pm10",
                    "unblock_action": "do not infer ordinary/onset behavior from these strong-recirculation rows; use future ordinary/transition anchors",
                    "evidence_required": "nonrecirculating or near-onset rows in the 0.02-0.10 reverse-fraction band",
                    "source_paths": summary.get("source_paths", ""),
                },
                {
                    "priority": 4,
                    "case_key": case_key,
                    "blocker_id": "PM10_RUNTIME_POLICY",
                    "status": "closed",
                    "unblock_action": "write a dated runtime-input policy before any solver/runtime use",
                    "evidence_required": "policy proving no realized wallHeatFlux or post-solve target leakage",
                    "source_paths": summary.get("source_paths", ""),
                },
            ]
        )
    return rows


def source_manifest(
    feature_matrix_path: Path,
    anchor_admission_path: Path,
    hybrid_contract_path: Path,
    direct_dry_scorecard_path: Path,
    residual_candidate_paths: Iterable[Path],
) -> list[dict[str, Any]]:
    sources = [
        ("pm10_recirculation_feature_matrix", feature_matrix_path, "plane-level PM10 recirculation features"),
        ("pm10_recirculation_anchor_admission", anchor_admission_path, "case-level PM10 recirculation admission"),
        ("hybrid_1d_model_contract", hybrid_contract_path, "recirculating_upcomer_effective lane policy"),
        ("upcomer_hybrid_dry_scorecard", direct_dry_scorecard_path, "existing diagnostic dry-score provenance"),
    ]
    sources.extend(
        (
            f"residual_candidate_{index}",
            path,
            (
                "derived PM10 same-window pressure residual targets"
                if path == DEFAULT_PM10_RESIDUAL_TARGETS
                else "candidate pressure/thermal residual target source"
            ),
        )
        for index, path in enumerate(residual_candidate_paths, start=1)
    )
    return [
        {"source_id": source_id, "path": rel(path), "exists": str(path.exists()).lower(), "role": role}
        for source_id, path, role in sources
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {summary["feature_matrix_path"]}
  - {summary["anchor_admission_path"]}
  - {summary["hybrid_contract_path"]}
tags: [pm10, recirculation, upcomer, residual-scorecard, hybrid-model]
date: {DATE}
type: work_product
status: active
---
# PM10 Recirculation Hybrid Residual Scorecard

This package makes the repaired PM10 matched-plane extraction usable as
recirculation-aware evidence. PM10 remains excluded from ordinary pipe `Nu`,
`f_D`, component-`K`, model-selection, and runtime-input use.

## Decision

The current PM10 rows are in the `recirculating_upcomer_effective` lane. They
can support recirculation diagnostics and conditional hybrid-model review, but
fit/model-selection promotion still requires same-window residual targets,
split scoring, and mesh/time uncertainty.

## Outputs

- `pm10_recirc_feature_summary.csv`: {summary["feature_summary_rows"]} case-level feature rows from {summary["plane_feature_rows"]} plane rows.
- `pm10_recirc_residual_join.csv`: residual target join status for each PM10 row.
- `pm10_recirc_model_form_scorecard.csv`: recirculation-aware model-form dry/available scores.
- `pm10_recirc_blocker_queue.csv`: concrete unblocks for residual targets, UQ, transition anchors, and runtime policy.
- `source_manifest.csv`: source paths and availability.
""",
        encoding="utf-8",
    )


def build_package(
    feature_matrix_path: Path = DEFAULT_FEATURE_MATRIX,
    anchor_admission_path: Path = DEFAULT_ANCHOR_ADMISSION,
    hybrid_contract_path: Path = DEFAULT_HYBRID_CONTRACT,
    direct_dry_scorecard_path: Path = DEFAULT_DIRECT_DRY_SCORECARD,
    residual_candidate_paths: Iterable[Path] = DEFAULT_RESIDUAL_CANDIDATES,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    residual_paths = tuple(residual_candidate_paths)
    feature_rows = read_csv(feature_matrix_path)
    admission_rows = read_csv(anchor_admission_path)
    summaries = case_feature_summaries(feature_rows, admission_rows)
    residual_rows = residual_join_rows(summaries, residual_paths)
    score_rows = model_score_rows(summaries, residual_rows)
    blockers = blocker_rows(summaries, residual_rows)
    manifest = source_manifest(
        feature_matrix_path,
        anchor_admission_path,
        hybrid_contract_path,
        direct_dry_scorecard_path,
        residual_paths,
    )

    csv_dump(output_dir / "pm10_recirc_feature_summary.csv", FEATURE_SUMMARY_FIELDS, summaries)
    csv_dump(output_dir / "pm10_recirc_residual_join.csv", RESIDUAL_JOIN_FIELDS, residual_rows)
    csv_dump(output_dir / "pm10_recirc_model_form_scorecard.csv", MODEL_SCORE_FIELDS, score_rows)
    csv_dump(output_dir / "pm10_recirc_blocker_queue.csv", BLOCKER_FIELDS, blockers)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)

    residual_available_cases = {
        row["case_key"] for row in residual_rows if row.get("target_status") == "residual_target_available"
    }
    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(summaries),
        "plane_feature_rows": len(feature_rows),
        "feature_summary_rows": len(summaries),
        "residual_join_rows": len(residual_rows),
        "residual_target_available_cases": len(residual_available_cases),
        "residual_target_missing_cases": len(summaries) - len(residual_available_cases),
        "model_score_rows": len(score_rows),
        "blocker_rows": len(blockers),
        "ordinary_pipe_fit_allowed_rows": 0,
        "fit_allowed_now": 0,
        "model_selection_allowed_now": 0,
        "runtime_input_allowed_now": 0,
        "recirculation_lane": "recirculating_upcomer_effective",
        "feature_matrix_path": rel(feature_matrix_path),
        "anchor_admission_path": rel(anchor_admission_path),
        "hybrid_contract_path": rel(hybrid_contract_path),
        "output_dir": rel(output_dir),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-matrix", type=Path, default=DEFAULT_FEATURE_MATRIX)
    parser.add_argument("--anchor-admission", type=Path, default=DEFAULT_ANCHOR_ADMISSION)
    parser.add_argument("--hybrid-contract", type=Path, default=DEFAULT_HYBRID_CONTRACT)
    parser.add_argument("--direct-dry-scorecard", type=Path, default=DEFAULT_DIRECT_DRY_SCORECARD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--residual-candidate", type=Path, action="append", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    residual_candidates = args.residual_candidate if args.residual_candidate is not None else DEFAULT_RESIDUAL_CANDIDATES
    summary = build_package(
        feature_matrix_path=args.feature_matrix,
        anchor_admission_path=args.anchor_admission,
        hybrid_contract_path=args.hybrid_contract,
        direct_dry_scorecard_path=args.direct_dry_scorecard,
        residual_candidate_paths=residual_candidates,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
