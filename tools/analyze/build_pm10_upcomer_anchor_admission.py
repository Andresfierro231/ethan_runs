#!/usr/bin/env python3
"""Classify PM10 matched-plane upcomer anchor usefulness.

The terminal drift gate can make PM10 rows ready for extraction, but it does not
make them fit/model-selection rows. This package reads matched-plane extraction
CSV outputs when present and emits a policy-safe admission table.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
DEFAULT_PARSED_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/parsed"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_upcomer_anchor_admission"
)
TERMINAL_DRIFT = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"
    / "pm10_terminal_drift.csv"
)
EXTRACTION_PACKAGE = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package"
)

CLASSIFICATION_FIELDS = [
    "case_key",
    "extraction_status",
    "plane_rows_available",
    "parsed_plane_rows",
    "representative_time_s",
    "max_reverse_area_fraction",
    "max_reverse_mass_fraction",
    "max_secondary_velocity_fraction",
    "max_Ri",
    "min_abs_delta_T_wall_bulk_K",
    "missing_required_fields",
    "missing_preferred_fields",
    "upcomer_admission_classification",
    "recirculation_severity_class",
    "ordinary_anchor_allowed",
    "onset_transition_anchor_allowed",
    "recirculation_diagnostic_allowed",
    "ordinary_pipe_fit_allowed",
    "ordinary_pipe_model_selection_allowed",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "recirculation_model_selection_allowed",
    "hybrid_validation_allowed",
    "candidate_for_policy_update",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "policy_package_required",
    "allowed_use_now",
    "blockers",
    "source_paths",
]

GATE_FIELDS = [
    "case_key",
    "ordinary_pipe_fit_allowed",
    "ordinary_pipe_model_selection_allowed",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "recirculation_model_selection_allowed",
    "hybrid_validation_allowed",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "candidate_for_policy_update",
    "policy_package_required",
    "required_evidence_to_promote",
    "current_gate_reason",
]

RECIRCULATION_ANCHOR_FIELDS = [
    "case_key",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "recirculation_model_selection_allowed",
    "hybrid_validation_allowed",
    "ordinary_pipe_fit_allowed",
    "recirculation_severity_class",
    "max_reverse_area_fraction",
    "max_reverse_mass_fraction",
    "max_secondary_velocity_fraction",
    "max_Ri",
    "min_abs_delta_T_wall_bulk_K",
    "allowed_use_now",
    "use_condition",
    "source_paths",
]

RECIRCULATION_FEATURE_FIELDS = [
    "case_key",
    "plane_location",
    "representative_time_s",
    "recirculation_severity_class",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "Ri",
    "bulk_T_K",
    "wall_T_K",
    "wallHeatFlux_W_m2",
    "delta_T_wall_bulk_K",
    "Re",
    "Pr",
    "Gz",
    "recirculation_anchor_allowed",
    "recirculation_calibration_allowed",
    "hybrid_validation_allowed",
    "source_paths",
]

REQUIRED_FIELDS = (
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "Ri",
    "bulk_T_K",
    "wall_T_K",
    "wallHeatFlux_W_m2",
    "representative_time_s",
)
PREFERRED_FIELDS = ("Re", "Pr", "Gz")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def fmt(value: Any, precision: int = 10) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return ""
    return f"{number:.{precision}g}"


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def parsed_file(parsed_dir: Path, case_key: str) -> Path:
    return parsed_dir / f"matched_plane_metrics_{case_key}.csv"


def terminal_source_for_case(case_key: str) -> str:
    rows = {row.get("case_key", ""): row for row in read_csv(TERMINAL_DRIFT)}
    row = rows.get(case_key)
    if not row:
        return rel(TERMINAL_DRIFT)
    return ";".join(path for path in [rel(TERMINAL_DRIFT), row.get("harvest_log_path", "")] if path)


def field_missing(row: dict[str, str], field: str) -> bool:
    if field == "representative_time_s":
        return not row.get(field, "").strip()
    if field == "Gz" and row.get(field, "") == "not_applicable_zero_entry_length":
        return False
    return safe_float(row.get(field)) is None


def unique_join(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return ";".join(seen)


def recirculation_severity_class(
    reverse_area: float | None,
    reverse_mass: float | None,
    ri: float | None,
) -> str:
    if (
        (reverse_area is not None and reverse_area > 0.10)
        or (reverse_mass is not None and reverse_mass > 0.10)
        or (ri is not None and ri >= 1.0)
    ):
        return "strong_recirculation"
    if (
        (reverse_area is not None and reverse_area >= 0.02)
        or (reverse_mass is not None and reverse_mass >= 0.02)
        or (ri is not None and ri >= 0.30)
    ):
        return "transition_or_mixed_convection"
    if reverse_area is None or reverse_mass is None or ri is None:
        return "unknown"
    return "ordinary_low_reverse"


def recirculation_use_condition(enabled: bool) -> str:
    if not enabled:
        return "not_admitted_for_recirculation_use"
    return "recirculation_aware_or_hybrid_models_only;ordinary_pipe_fit_excluded;runtime_input_policy_required"


def classify_case(case_key: str, parsed_dir: Path) -> dict[str, str]:
    path = parsed_file(parsed_dir, case_key)
    rows = read_csv(path)
    if not rows:
        return {
            "case_key": case_key,
            "extraction_status": "blocked_missing_extraction",
            "plane_rows_available": "0",
            "parsed_plane_rows": "0",
            "representative_time_s": "",
            "max_reverse_area_fraction": "",
            "max_reverse_mass_fraction": "",
            "max_secondary_velocity_fraction": "",
            "max_Ri": "",
            "min_abs_delta_T_wall_bulk_K": "",
            "missing_required_fields": "matched_plane_metrics_csv",
            "missing_preferred_fields": "",
            "upcomer_admission_classification": "blocked_missing_extraction",
            "recirculation_severity_class": "unknown",
            "ordinary_anchor_allowed": "no",
            "onset_transition_anchor_allowed": "no",
            "recirculation_diagnostic_allowed": "no",
            "ordinary_pipe_fit_allowed": "no",
            "ordinary_pipe_model_selection_allowed": "no",
            "recirculation_anchor_allowed": "no",
            "recirculation_calibration_allowed": "no",
            "recirculation_model_selection_allowed": "no",
            "hybrid_validation_allowed": "no",
            "candidate_for_policy_update": "no",
            "fit_allowed_now": "no",
            "model_selection_allowed_now": "no",
            "runtime_input_allowed_now": "no",
            "policy_package_required": "no",
            "allowed_use_now": "terminal_holdout_only_pending_matched_plane_extraction",
            "blockers": "pm10_matched_plane_metrics_absent",
            "source_paths": unique_join([rel(path), terminal_source_for_case(case_key), rel(EXTRACTION_PACKAGE)]),
        }

    missing_required: list[str] = []
    missing_preferred: list[str] = []
    parsed_count = sum(1 for row in rows if row.get("metric_status", "").startswith("parsed"))
    for row in rows:
        for field in REQUIRED_FIELDS:
            if field_missing(row, field):
                missing_required.append(f"{row.get('plane_location', 'unknown')}:{field}")
        for field in PREFERRED_FIELDS:
            if field_missing(row, field):
                missing_preferred.append(f"{row.get('plane_location', 'unknown')}:{field}")

    reverse_area_values = [safe_float(row.get("reverse_area_fraction")) for row in rows]
    reverse_mass_values = [safe_float(row.get("reverse_mass_fraction")) for row in rows]
    secondary_values = [safe_float(row.get("secondary_velocity_fraction")) for row in rows]
    ri_values = [safe_float(row.get("Ri")) for row in rows]
    delta_values: list[float] = []
    for row in rows:
        delta = safe_float(row.get("delta_T_wall_bulk_K"))
        if delta is None:
            wall = safe_float(row.get("wall_T_K"))
            bulk = safe_float(row.get("bulk_T_K"))
            if wall is not None and bulk is not None:
                delta = wall - bulk
        if delta is not None:
            delta_values.append(abs(delta))

    max_reverse_area = max((value for value in reverse_area_values if value is not None), default=None)
    max_reverse_mass = max((value for value in reverse_mass_values if value is not None), default=None)
    max_secondary = max((value for value in secondary_values if value is not None), default=None)
    max_ri = max((value for value in ri_values if value is not None), default=None)
    min_delta = min(delta_values, default=None)
    times = [row.get("representative_time_s", "") for row in rows if row.get("representative_time_s", "")]

    blockers: list[str] = []
    classification = "blocked_missing_fields"
    ordinary_allowed = "no"
    onset_allowed = "no"
    recirc_allowed = "no"
    recirc_anchor_allowed = "no"
    recirc_calibration_allowed = "no"
    recirc_model_selection_allowed = "no"
    hybrid_validation_allowed = "no"
    candidate_for_policy_update = "no"
    policy_package_required = "no"
    allowed_use_now = "terminal_holdout_only_pending_matched_plane_admission"
    severity_class = recirculation_severity_class(max_reverse_area, max_reverse_mass, max_ri)

    strong_reversal = (
        (max_reverse_area is not None and max_reverse_area > 0.10)
        or (max_reverse_mass is not None and max_reverse_mass > 0.10)
        or (max_ri is not None and max_ri >= 1.0)
    )
    if strong_reversal:
        classification = "recirculation_diagnostic"
        recirc_allowed = "yes"
        if missing_required:
            allowed_use_now = "terminal_holdout_only_pending_complete_matched_plane_fields"
            blockers.append("strong_recirculation_detected_with_incomplete_same_window_fields")
        else:
            recirc_anchor_allowed = "yes"
            recirc_calibration_allowed = "conditional"
            recirc_model_selection_allowed = "conditional"
            hybrid_validation_allowed = "yes"
            allowed_use_now = "recirculation_aware_calibration_and_hybrid_validation"
    elif missing_required:
        classification = "blocked_missing_fields"
        blockers.append("same_window_required_fields_missing")
    elif min_delta is not None and min_delta < 0.5:
        classification = "diagnostic_small_wall_bulk_deltaT"
        blockers.append("wall_bulk_deltaT_below_0p5K")
    elif max_secondary is not None and max_secondary >= 0.20:
        classification = "diagnostic_secondary_flow"
        blockers.append("secondary_velocity_fraction_ge_0p20")
    elif max_ri is not None and max_ri >= 0.30:
        classification = "diagnostic_mixed_convection"
        blockers.append("Ri_ge_0p30")
    elif (
        max_reverse_area is not None
        and max_reverse_mass is not None
        and max_reverse_area < 0.02
        and max_reverse_mass < 0.02
    ):
        classification = "ordinary_anchor_candidate"
        ordinary_allowed = "yes"
        candidate_for_policy_update = "yes"
        policy_package_required = "yes"
        allowed_use_now = "candidate_for_dated_split_policy_update"
    elif (
        (max_reverse_area is not None and 0.02 <= max_reverse_area <= 0.10)
        or (max_reverse_mass is not None and 0.02 <= max_reverse_mass <= 0.10)
    ):
        classification = "onset_transition_candidate"
        onset_allowed = "yes"
        candidate_for_policy_update = "yes"
        policy_package_required = "yes"
        allowed_use_now = "candidate_for_dated_split_policy_update"
    else:
        classification = "diagnostic_indeterminate_reverse_fraction"
        blockers.append("reverse_fraction_not_classifiable")

    if missing_preferred:
        blockers.append("preferred_nondimensional_fields_missing")

    return {
        "case_key": case_key,
        "extraction_status": "matched_plane_rows_present",
        "plane_rows_available": str(len(rows)),
        "parsed_plane_rows": str(parsed_count),
        "representative_time_s": unique_join(times),
        "max_reverse_area_fraction": fmt(max_reverse_area),
        "max_reverse_mass_fraction": fmt(max_reverse_mass),
        "max_secondary_velocity_fraction": fmt(max_secondary),
        "max_Ri": fmt(max_ri),
        "min_abs_delta_T_wall_bulk_K": fmt(min_delta),
        "missing_required_fields": unique_join(missing_required),
        "missing_preferred_fields": unique_join(missing_preferred),
        "upcomer_admission_classification": classification,
        "recirculation_severity_class": severity_class,
        "ordinary_anchor_allowed": ordinary_allowed,
        "onset_transition_anchor_allowed": onset_allowed,
        "recirculation_diagnostic_allowed": recirc_allowed,
        "ordinary_pipe_fit_allowed": "no",
        "ordinary_pipe_model_selection_allowed": "no",
        "recirculation_anchor_allowed": recirc_anchor_allowed,
        "recirculation_calibration_allowed": recirc_calibration_allowed,
        "recirculation_model_selection_allowed": recirc_model_selection_allowed,
        "hybrid_validation_allowed": hybrid_validation_allowed,
        "candidate_for_policy_update": candidate_for_policy_update,
        "fit_allowed_now": "no",
        "model_selection_allowed_now": "no",
        "runtime_input_allowed_now": "no",
        "policy_package_required": policy_package_required,
        "allowed_use_now": allowed_use_now,
        "blockers": unique_join(blockers),
        "source_paths": unique_join([rel(path), terminal_source_for_case(case_key), rel(EXTRACTION_PACKAGE)]),
    }


def gate_rows(classification_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in classification_rows:
        candidate = row["candidate_for_policy_update"] == "yes"
        recirc_enabled = row["recirculation_anchor_allowed"] == "yes"
        rows.append(
            {
                "case_key": row["case_key"],
                "ordinary_pipe_fit_allowed": row["ordinary_pipe_fit_allowed"],
                "ordinary_pipe_model_selection_allowed": row["ordinary_pipe_model_selection_allowed"],
                "recirculation_anchor_allowed": row["recirculation_anchor_allowed"],
                "recirculation_calibration_allowed": row["recirculation_calibration_allowed"],
                "recirculation_model_selection_allowed": row["recirculation_model_selection_allowed"],
                "hybrid_validation_allowed": row["hybrid_validation_allowed"],
                "fit_allowed_now": "no",
                "model_selection_allowed_now": "no",
                "runtime_input_allowed_now": "no",
                "candidate_for_policy_update": row["candidate_for_policy_update"],
                "policy_package_required": row["policy_package_required"],
                "required_evidence_to_promote": (
                    "dated_split_policy_update_after_matched_plane_admission_and_residual_gate"
                    if candidate
                    else (
                        "recirculation_aware_model_form_and_runtime_policy_for_broader_use"
                        if recirc_enabled
                        else "complete_matched_plane_extraction_then_reclassify"
                    )
                ),
                "current_gate_reason": (
                    "current_pm10_split_is_future_holdout_scoring_only"
                    if candidate
                    else (
                        "ordinary_pipe_closed_recirc_aware_conditional"
                        if recirc_enabled
                        else row["upcomer_admission_classification"]
                    )
                ),
            }
        )
    return rows


def recirculation_anchor_rows(classification_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in classification_rows:
        enabled = row["recirculation_anchor_allowed"] == "yes"
        rows.append(
            {
                "case_key": row["case_key"],
                "recirculation_anchor_allowed": row["recirculation_anchor_allowed"],
                "recirculation_calibration_allowed": row["recirculation_calibration_allowed"],
                "recirculation_model_selection_allowed": row["recirculation_model_selection_allowed"],
                "hybrid_validation_allowed": row["hybrid_validation_allowed"],
                "ordinary_pipe_fit_allowed": row["ordinary_pipe_fit_allowed"],
                "recirculation_severity_class": row["recirculation_severity_class"],
                "max_reverse_area_fraction": row["max_reverse_area_fraction"],
                "max_reverse_mass_fraction": row["max_reverse_mass_fraction"],
                "max_secondary_velocity_fraction": row["max_secondary_velocity_fraction"],
                "max_Ri": row["max_Ri"],
                "min_abs_delta_T_wall_bulk_K": row["min_abs_delta_T_wall_bulk_K"],
                "allowed_use_now": row["allowed_use_now"],
                "use_condition": recirculation_use_condition(enabled),
                "source_paths": row["source_paths"],
            }
        )
    return rows


def recirculation_feature_rows(parsed_dir: Path, classification_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_case = {row["case_key"]: row for row in classification_rows}
    rows: list[dict[str, str]] = []
    for case_key in PM10_CASES:
        case_row = by_case[case_key]
        for plane in read_csv(parsed_file(parsed_dir, case_key)):
            rows.append(
                {
                    "case_key": case_key,
                    "plane_location": plane.get("plane_location", ""),
                    "representative_time_s": plane.get("representative_time_s", ""),
                    "recirculation_severity_class": case_row["recirculation_severity_class"],
                    "reverse_area_fraction": plane.get("reverse_area_fraction", ""),
                    "reverse_mass_fraction": plane.get("reverse_mass_fraction", ""),
                    "secondary_velocity_fraction": plane.get("secondary_velocity_fraction", ""),
                    "Ri": plane.get("Ri", ""),
                    "bulk_T_K": plane.get("bulk_T_K", ""),
                    "wall_T_K": plane.get("wall_T_K", ""),
                    "wallHeatFlux_W_m2": plane.get("wallHeatFlux_W_m2", ""),
                    "delta_T_wall_bulk_K": plane.get("delta_T_wall_bulk_K", ""),
                    "Re": plane.get("Re", ""),
                    "Pr": plane.get("Pr", ""),
                    "Gz": plane.get("Gz", ""),
                    "recirculation_anchor_allowed": case_row["recirculation_anchor_allowed"],
                    "recirculation_calibration_allowed": case_row["recirculation_calibration_allowed"],
                    "hybrid_validation_allowed": case_row["hybrid_validation_allowed"],
                    "source_paths": plane.get("source_paths", case_row["source_paths"]),
                }
            )
    return rows


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {rel(TERMINAL_DRIFT)}
  - {rel(EXTRACTION_PACKAGE)}
tags: [pm10, upcomer, matched-plane, admission]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Upcomer Anchor Admission

This package classifies the four completed PM10 rows after matched-plane
extraction. It separates ordinary-pipe gates from recirculation-aware use:
recirculation can be usable evidence while ordinary single-stream pipe fitting
remains closed.

## Outputs

- `pm10_upcomer_anchor_classification.csv`: {summary["case_count"]} case-level
  PM10 classifications.
- `pm10_fit_model_selection_gate.csv`: explicit split-policy gate for fit and
  model-selection use.
- `pm10_model_use_gate.csv`: lane-specific ordinary-pipe versus
  recirculation-aware use gate.
- `pm10_recirculation_anchor_admission.csv`: recirculation calibration,
  model-selection, and hybrid-validation eligibility.
- `pm10_recirculation_feature_matrix.csv`: plane-level recirculation features
  for recirculation-aware scoring.
- `summary.json`: counts and source paths.

## Current Policy

PM10 rows remain excluded from ordinary-pipe Nu/friction/component-K fitting.
Strong-recirculation rows are admitted as recirculation-regime evidence for
conditional recirculation-aware calibration, conditional recirculation-aware
model selection, and hybrid validation. Runtime-input use still requires a dated
policy update.
""",
        encoding="utf-8",
    )


def build_package(parsed_dir: Path = DEFAULT_PARSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    rows = [classify_case(case_key, parsed_dir) for case_key in PM10_CASES]
    gates = gate_rows(rows)
    recirc_rows = recirculation_anchor_rows(rows)
    feature_rows = recirculation_feature_rows(parsed_dir, rows)
    csv_dump(output_dir / "pm10_upcomer_anchor_classification.csv", CLASSIFICATION_FIELDS, rows)
    csv_dump(output_dir / "pm10_fit_model_selection_gate.csv", GATE_FIELDS, gates)
    csv_dump(output_dir / "pm10_model_use_gate.csv", GATE_FIELDS, gates)
    csv_dump(output_dir / "pm10_recirculation_anchor_admission.csv", RECIRCULATION_ANCHOR_FIELDS, recirc_rows)
    csv_dump(output_dir / "pm10_recirculation_feature_matrix.csv", RECIRCULATION_FEATURE_FIELDS, feature_rows)
    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(rows),
        "ordinary_anchor_candidates": sum(row["upcomer_admission_classification"] == "ordinary_anchor_candidate" for row in rows),
        "onset_transition_candidates": sum(row["upcomer_admission_classification"] == "onset_transition_candidate" for row in rows),
        "recirculation_diagnostics": sum(row["upcomer_admission_classification"] == "recirculation_diagnostic" for row in rows),
        "blocked_missing_extraction": sum(row["upcomer_admission_classification"] == "blocked_missing_extraction" for row in rows),
        "blocked_missing_fields": sum(row["upcomer_admission_classification"] == "blocked_missing_fields" for row in rows),
        "recirculation_anchor_allowed_rows": sum(row["recirculation_anchor_allowed"] == "yes" for row in rows),
        "recirculation_calibration_conditional_rows": sum(row["recirculation_calibration_allowed"] == "conditional" for row in rows),
        "recirculation_model_selection_conditional_rows": sum(row["recirculation_model_selection_allowed"] == "conditional" for row in rows),
        "hybrid_validation_allowed_rows": sum(row["hybrid_validation_allowed"] == "yes" for row in rows),
        "ordinary_pipe_fit_allowed_rows": sum(row["ordinary_pipe_fit_allowed"] == "yes" for row in rows),
        "recirculation_feature_rows": len(feature_rows),
        "fit_allowed_now": 0,
        "model_selection_allowed_now": 0,
        "runtime_input_allowed_now": 0,
        "parsed_dir": rel(parsed_dir),
        "output_dir": rel(output_dir),
        "source_paths": [rel(TERMINAL_DRIFT), rel(EXTRACTION_PACKAGE)],
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parsed-dir", type=Path, default=DEFAULT_PARSED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_package(args.parsed_dir, args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
