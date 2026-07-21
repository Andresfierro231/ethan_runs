#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, finite_float, load_csv_rows, write_json  # noqa: E402
from tools.common import ensure_dir, iso_timestamp, relative_to_workspace  # noqa: E402

DEFAULT_REPORT_DAY_DIR = ROOT / "reports" / "2026-06" / "2026-06-29"
DEFAULT_OUTPUT_DIR = DEFAULT_REPORT_DAY_DIR / "2026-06-29_ethan_reduction_contract_audit"
DEFAULT_WORK_PRODUCT_DIR = ROOT / "work_products" / "2026-06-29_ethan_reduction_contract_audit"
DEFAULT_IMPORT_MANIFEST_PATH = ROOT / "imports" / "2026-06-29_ethan_reduction_contract_audit.json"
DEFAULT_PAPER_CASE_INVENTORY_CSV = (
    ROOT / "work_products" / "2026-06-29_ethan_paper_case_inventory" / "paper_case_inventory.csv"
)
DEFAULT_CLOSURE_BRANCH_POLICY_CSV = (
    ROOT
    / "reports"
    / "2026-06"
    / "2026-06-23"
    / "2026-06-23_ethan_frozen_state_1d_validation"
    / "closure_branch_policy.csv"
)
DEFAULT_SALT1_PACKAGE_ROOT = ROOT / "tmp" / "2026-06-23_ethan_latest_window_case_analysis_refresh" / "salt1_jin"
DEFAULT_SALT2_PACKAGE_ROOT = (
    ROOT
    / "tmp"
    / "2026-06-15_live_case_analysis"
    / "contract_fix_salt2"
    / "viscosity_screening_salt_test_2_jin_coarse_mesh"
)
DEFAULT_SALT3_PACKAGE_ROOT = (
    ROOT
    / "tmp"
    / "2026-06-15_live_case_analysis"
    / "contract_fix_salt_family"
    / "viscosity_screening_salt_test_3_jin_coarse_mesh"
)
DEFAULT_SALT4_PACKAGE_ROOT = (
    ROOT
    / "tmp"
    / "2026-06-15_live_case_analysis"
    / "contract_fix_salt_family"
    / "viscosity_screening_salt_test_4_jin_coarse_mesh"
)

SOURCE_ID_ORDER = (
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
)

PACKAGE_ROOT_DEFAULTS = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": DEFAULT_SALT1_PACKAGE_ROOT,
    "viscosity_screening_salt_test_2_jin_coarse_mesh": DEFAULT_SALT2_PACKAGE_ROOT,
    "viscosity_screening_salt_test_3_jin_coarse_mesh": DEFAULT_SALT3_PACKAGE_ROOT,
    "viscosity_screening_salt_test_4_jin_coarse_mesh": DEFAULT_SALT4_PACKAGE_ROOT,
}

STATION_SIGNATURE_FIELDS = (
    "span_name",
    "span_kind",
    "bin_index",
    "target_ds_m",
    "s_start_m",
    "s_end_m",
    "s_mid_m",
    "segment_start_label",
    "segment_end_label",
    "sample_index",
    "s_m",
)

BRANCH_GEOMETRY_FIELDS = (
    "branch_type",
    "component_spans",
    "component_span_count",
)

CASE_FILE_NAMES = {
    "analysis_manifest": "analysis_manifest.json",
    "summary": "summary.json",
    "station_map": "leg_centerline_station_definitions.csv",
    "branch_summary": "branch_thermal_summary.csv",
    "major_loss": "major_loss_summary.csv",
    "streamwise_heat_loss": "streamwise_heat_loss_summary.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a dated 3D-to-1D reduction-contract audit for the frozen "
            "June 29 paper-grade Salt subset."
        )
    )
    parser.add_argument("--paper-case-inventory-csv", default=str(DEFAULT_PAPER_CASE_INVENTORY_CSV))
    parser.add_argument("--closure-branch-policy-csv", default=str(DEFAULT_CLOSURE_BRANCH_POLICY_CSV))
    parser.add_argument("--salt1-package-root", default=str(DEFAULT_SALT1_PACKAGE_ROOT))
    parser.add_argument("--salt2-package-root", default=str(DEFAULT_SALT2_PACKAGE_ROOT))
    parser.add_argument("--salt3-package-root", default=str(DEFAULT_SALT3_PACKAGE_ROOT))
    parser.add_argument("--salt4-package-root", default=str(DEFAULT_SALT4_PACKAGE_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--work-product-dir", default=str(DEFAULT_WORK_PRODUCT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_MANIFEST_PATH))
    return parser.parse_args()


def source_sort_key(source_id: str) -> int:
    try:
        return SOURCE_ID_ORDER.index(source_id)
    except ValueError:
        return len(SOURCE_ID_ORDER)


def join_tokens(values: list[str]) -> str:
    payload = [str(value).strip() for value in values if str(value).strip()]
    return "|".join(payload)


def json_token(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def time_bounds(values: list[Any]) -> tuple[float, float]:
    payload = [finite_float(value) for value in values]
    payload = [value for value in payload if math.isfinite(value)]
    if not payload:
        return (math.nan, math.nan)
    return (min(payload), max(payload))


def required_case_package_paths(package_root: Path) -> dict[str, Path]:
    paths = {label: package_root / filename for label, filename in CASE_FILE_NAMES.items()}
    missing = [label for label, path in paths.items() if not path.exists()]
    if missing:
        raise RuntimeError(f"package root missing required files {missing}: {package_root}")
    return paths


def select_paper_grade_inventory_rows(inventory_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [row for row in inventory_rows if row.get("paper_class") == "paper-grade"]
    rows.sort(key=lambda row: source_sort_key(str(row.get("source_id", ""))))
    source_ids = [row.get("source_id", "") for row in rows]
    missing = [source_id for source_id in SOURCE_ID_ORDER if source_id not in source_ids]
    if missing:
        raise RuntimeError(f"paper-grade inventory missing expected nominal Salt Jin cases: {missing}")
    return rows


def package_roots_from_args(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "viscosity_screening_salt_test_1_jin_coarse_mesh": Path(args.salt1_package_root),
        "viscosity_screening_salt_test_2_jin_coarse_mesh": Path(args.salt2_package_root),
        "viscosity_screening_salt_test_3_jin_coarse_mesh": Path(args.salt3_package_root),
        "viscosity_screening_salt_test_4_jin_coarse_mesh": Path(args.salt4_package_root),
    }


def load_case_context(inventory_row: dict[str, str], package_root: Path) -> dict[str, Any]:
    paths = required_case_package_paths(package_root)
    analysis_manifest = json.loads(paths["analysis_manifest"].read_text(encoding="utf-8"))
    package_summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    station_rows = load_csv_rows(paths["station_map"])
    branch_rows = load_csv_rows(paths["branch_summary"])
    major_rows = load_csv_rows(paths["major_loss"])
    streamwise_rows = load_csv_rows(paths["streamwise_heat_loss"])
    requested_times = list(analysis_manifest.get("requested_times", []))
    requested_start_s, requested_end_s = time_bounds(requested_times)
    return {
        "inventory": inventory_row,
        "package_root": package_root,
        "paths": paths,
        "analysis_manifest": analysis_manifest,
        "package_summary": package_summary,
        "station_rows": station_rows,
        "branch_rows": branch_rows,
        "major_rows": major_rows,
        "streamwise_rows": streamwise_rows,
        "source_id": inventory_row["source_id"],
        "case_label": inventory_row["case_label"],
        "paper_class": inventory_row["paper_class"],
        "requested_times": requested_times,
        "requested_time_count": len(requested_times),
        "requested_time_start_s": requested_start_s,
        "requested_time_end_s": requested_end_s,
    }


def station_row_signature(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")).strip() for field in STATION_SIGNATURE_FIELDS)


def branch_geometry_signature(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")).strip() for field in BRANCH_GEOMETRY_FIELDS)


def branch_summary_support_fraction(row: dict[str, str]) -> float:
    direct_value = finite_float(row.get("mean_support_fraction"))
    if math.isfinite(direct_value):
        return direct_value
    usable_count = finite_float(row.get("usable_row_count"))
    total_count = finite_float(row.get("total_row_count"))
    if not math.isfinite(usable_count) or not math.isfinite(total_count) or total_count == 0.0:
        return math.nan
    return usable_count / total_count


def build_station_map_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reference = case_contexts[0]
    reference_rows = reference["station_rows"]
    signatures_by_case = {
        context["source_id"]: [station_row_signature(row) for row in context["station_rows"]]
        for context in case_contexts
    }
    rows_out: list[dict[str, Any]] = []
    for index, row in enumerate(reference_rows):
        matching_source_ids = [
            context["source_id"]
            for context in case_contexts
            if len(signatures_by_case[context["source_id"]]) > index
            and signatures_by_case[context["source_id"]][index] == signatures_by_case[reference["source_id"]][index]
        ]
        rows_out.append(
            {
                "reference_source_id": reference["source_id"],
                "source_case_count": len(case_contexts),
                "matching_source_case_count": len(matching_source_ids),
                "matching_source_ids": join_tokens(matching_source_ids),
                "span_name": row["span_name"],
                "span_kind": row["span_kind"],
                "bin_index": int(row["bin_index"]),
                "target_ds_m": finite_float(row.get("target_ds_m")),
                "s_start_m": finite_float(row.get("s_start_m")),
                "s_end_m": finite_float(row.get("s_end_m")),
                "s_mid_m": finite_float(row.get("s_mid_m")),
                "segment_start_label": row.get("segment_start_label", ""),
                "segment_end_label": row.get("segment_end_label", ""),
                "sample_index": int(row["sample_index"]),
                "s_m": finite_float(row.get("s_m")),
            }
        )
    return rows_out


def build_branch_map_rows(
    case_contexts: list[dict[str, Any]],
    policy_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    policy_by_branch = {row["branch_name"]: row for row in policy_rows}
    reference = case_contexts[0]
    reference_by_branch = {row["branch_name"]: row for row in reference["branch_rows"]}
    rows_out: list[dict[str, Any]] = []
    for branch_name in sorted(reference_by_branch):
        reference_row = reference_by_branch[branch_name]
        branch_rows = [
            next((row for row in context["branch_rows"] if row.get("branch_name") == branch_name), None)
            for context in case_contexts
        ]
        present_rows = [row for row in branch_rows if row is not None]
        matching_geometry_source_ids = [
            context["source_id"]
            for context, row in zip(case_contexts, branch_rows)
            if row is not None and branch_geometry_signature(row) == branch_geometry_signature(reference_row)
        ]
        policy_row = policy_by_branch.get(branch_name, {})
        rows_out.append(
            {
                "branch_name": branch_name,
                "reference_source_id": reference["source_id"],
                "present_case_count": len(present_rows),
                "matching_geometry_case_count": len(matching_geometry_source_ids),
                "matching_geometry_source_ids": join_tokens(matching_geometry_source_ids),
                "branch_type": reference_row.get("branch_type", ""),
                "component_spans": reference_row.get("component_spans", ""),
                "component_span_count": int(reference_row.get("component_span_count", "0") or 0),
                "mean_branch_total_length_m": sum(
                    finite_float(row.get("branch_total_length_m")) for row in present_rows
                )
                / len(present_rows),
                "min_branch_total_length_m": min(finite_float(row.get("branch_total_length_m")) for row in present_rows),
                "max_branch_total_length_m": max(finite_float(row.get("branch_total_length_m")) for row in present_rows),
                "mean_support_fraction": sum(branch_summary_support_fraction(row) for row in present_rows) / len(present_rows),
                "mean_abs_bulk_minus_wall_temp_k": sum(
                    finite_float(row.get("mean_abs_bulk_minus_wall_temp_k")) for row in present_rows
                )
                / len(present_rows),
                "policy_mean_residual_fraction_of_wall_heat": finite_float(
                    policy_row.get("mean_residual_fraction_of_wall_heat")
                ),
                "branch_role": policy_row.get("branch_role", ""),
                "primary_model_mode": policy_row.get("primary_model_mode", ""),
                "direct_nu_allowed": policy_row.get("direct_nu_allowed", ""),
                "direct_nu_status": policy_row.get("direct_nu_status", ""),
                "primary_ua_allowed": policy_row.get("primary_ua_allowed", ""),
                "secondary_htc_allowed": policy_row.get("secondary_htc_allowed", ""),
                "dominant_fit_status": policy_row.get("dominant_fit_status", ""),
                "domain_note": policy_row.get("domain_note", ""),
                "modeling_note": policy_row.get("modeling_note", ""),
            }
        )
    return rows_out


def build_source_contract_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        manifest = context["analysis_manifest"]
        summary = context["package_summary"]
        inventory = context["inventory"]
        rows_out.append(
            {
                "source_id": context["source_id"],
                "case_label": context["case_label"],
                "paper_class": context["paper_class"],
                "checkpoint_case_key": inventory.get("checkpoint_case_key", ""),
                "checkpoint_lane": inventory.get("checkpoint_lane", ""),
                "retained_window_status": inventory.get("retained_window_status", ""),
                "checkpoint_representative_time_count": int(
                    inventory.get("checkpoint_representative_time_count", "0") or 0
                ),
                "checkpoint_latest_retained_time_s": finite_float(inventory.get("checkpoint_latest_retained_time_s")),
                "package_root": relative_to_workspace(context["package_root"]),
                "analysis_manifest_generated_at": manifest.get("generated_at", ""),
                "package_summary_generated_at": summary.get("generated_at", ""),
                "profile_name": manifest.get("profile_name", ""),
                "source_case_path": inventory.get("source_case_path", ""),
                "source_root": manifest.get("source_root", ""),
                "runtime_root": manifest.get("runtime_root", ""),
                "live_runtime_root": manifest.get("live_runtime_root", ""),
                "frozen_runtime_root": manifest.get("frozen_runtime_root", ""),
                "requested_time_count": context["requested_time_count"],
                "requested_time_start_s": context["requested_time_start_s"],
                "requested_time_end_s": context["requested_time_end_s"],
                "target_ds_m": finite_float(manifest.get("target_ds_m")),
                "required_fields": join_tokens(list(manifest.get("required_fields", []))),
                "pressure_fields": join_tokens(list(manifest.get("pressure_fields", []))),
                "wall_fields": join_tokens(list(manifest.get("wall_fields", []))),
                "major_span_order": join_tokens(list(summary.get("major_loss", {}).get("loop_span_order", []))),
                "branch_order": join_tokens(list(summary.get("branch_thermal", {}).get("branch_order", []))),
                "derived_branch_names": join_tokens(list(summary.get("branch_thermal", {}).get("derived_branch_names", []))),
            }
        )
    return rows_out


def build_reduction_choice_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        manifest = context["analysis_manifest"]
        summary = context["package_summary"]
        manifest_rel = relative_to_workspace(context["paths"]["analysis_manifest"])
        streamwise = summary.get("streamwise_thermal", {})
        branch_thermal = summary.get("branch_thermal", {})
        azimuthal = summary.get("azimuthal_transport", {})
        rows_out.extend(
            [
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "time_window",
                    "choice_key": "requested_times",
                    "choice_value": join_tokens([str(value) for value in context["requested_times"]]),
                    "evidence_source": manifest_rel,
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "geometry",
                    "choice_key": "target_ds_m",
                    "choice_value": str(manifest.get("target_ds_m", "")),
                    "evidence_source": manifest_rel,
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "fields",
                    "choice_key": "required_fields",
                    "choice_value": join_tokens(list(manifest.get("required_fields", []))),
                    "evidence_source": manifest_rel,
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "fields",
                    "choice_key": "pressure_fields",
                    "choice_value": join_tokens(list(manifest.get("pressure_fields", []))),
                    "evidence_source": manifest_rel,
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "fields",
                    "choice_key": "wall_fields",
                    "choice_value": join_tokens(list(manifest.get("wall_fields", []))),
                    "evidence_source": manifest_rel,
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "averaging",
                    "choice_key": "thermal_bulk_method",
                    "choice_value": str(streamwise.get("thermal_bulk_method", "")),
                    "evidence_source": relative_to_workspace(context["paths"]["summary"]),
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "support_gate",
                    "choice_key": "thermal_support_flagged_bin_count",
                    "choice_value": str(streamwise.get("thermal_support_flagged_bin_count", "")),
                    "evidence_source": relative_to_workspace(context["paths"]["summary"]),
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "coordinate_contract",
                    "choice_key": "loop_span_order",
                    "choice_value": join_tokens(list(summary.get("major_loss", {}).get("loop_span_order", []))),
                    "evidence_source": relative_to_workspace(context["paths"]["summary"]),
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "coordinate_contract",
                    "choice_key": "branch_order",
                    "choice_value": join_tokens(list(branch_thermal.get("branch_order", []))),
                    "evidence_source": relative_to_workspace(context["paths"]["summary"]),
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "coordinate_contract",
                    "choice_key": "derived_branch_names",
                    "choice_value": join_tokens(list(branch_thermal.get("derived_branch_names", []))),
                    "evidence_source": relative_to_workspace(context["paths"]["summary"]),
                },
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "transport_support",
                    "choice_key": "matched_transport_row_count",
                    "choice_value": str(azimuthal.get("matched_transport_row_count", "")),
                    "evidence_source": relative_to_workspace(context["paths"]["summary"]),
                },
            ]
        )
        for sign_key, sign_value in sorted(dict(manifest.get("sign_conventions", {})).items()):
            rows_out.append(
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "sign_convention",
                    "choice_key": sign_key,
                    "choice_value": str(sign_value),
                    "evidence_source": manifest_rel,
                }
            )
        flow_direction_hints = dict(manifest.get("flow_direction_hints", {}))
        for flow_key in ("status", "meaning"):
            if flow_key in flow_direction_hints:
                rows_out.append(
                    {
                        "source_id": context["source_id"],
                        "case_label": context["case_label"],
                        "choice_group": "flow_direction",
                        "choice_key": flow_key,
                        "choice_value": str(flow_direction_hints[flow_key]),
                        "evidence_source": manifest_rel,
                    }
                )
        if "hints_by_span" in flow_direction_hints:
            rows_out.append(
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "flow_direction",
                    "choice_key": "hints_by_span_json",
                    "choice_value": json_token(flow_direction_hints["hints_by_span"]),
                    "evidence_source": manifest_rel,
                }
            )
        for index, deferred_term in enumerate(list(manifest.get("deferred_terms", [])), start=1):
            rows_out.append(
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "deferred_term",
                    "choice_key": f"deferred_term_{index}",
                    "choice_value": str(deferred_term),
                    "evidence_source": manifest_rel,
                }
            )
        if "raw_extraction_provenance" in manifest:
            rows_out.append(
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "choice_group": "provenance",
                    "choice_key": "raw_extraction_provenance_json",
                    "choice_value": json_token(manifest["raw_extraction_provenance"]),
                    "evidence_source": manifest_rel,
                }
            )
    return rows_out


def append_case_metadata(
    rows: list[dict[str, str]],
    context: dict[str, Any],
    extra_fields: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    base = {
        "source_id": context["source_id"],
        "case_label": context["case_label"],
        "paper_class": context["paper_class"],
        "checkpoint_case_key": context["inventory"].get("checkpoint_case_key", ""),
        "checkpoint_lane": context["inventory"].get("checkpoint_lane", ""),
        "retained_window_status": context["inventory"].get("retained_window_status", ""),
        "package_root": relative_to_workspace(context["package_root"]),
    }
    if extra_fields:
        base.update(extra_fields)
    for row in rows:
        payload.append({**base, **row})
    return payload


def build_reduced_branch_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        rows_out.extend(append_case_metadata(context["branch_rows"], context))
    return rows_out


def build_reduced_major_loss_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        rows_out.extend(append_case_metadata(context["major_rows"], context))
    return rows_out


def build_reduced_streamwise_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        rows_out.extend(
            append_case_metadata(
                context["streamwise_rows"],
                context,
                extra_fields={"requested_time_count": context["requested_time_count"]},
            )
        )
    return rows_out


def build_readme(
    *,
    case_contexts: list[dict[str, Any]],
    station_map_rows: list[dict[str, Any]],
    branch_map_rows: list[dict[str, Any]],
    reduction_choice_rows: list[dict[str, Any]],
) -> str:
    source_rows = [
        f"- `{context['case_label']}` -> `{relative_to_workspace(context['package_root'])}`"
        for context in case_contexts
    ]
    all_station_match = all(
        int(row["matching_source_case_count"]) == len(case_contexts) for row in station_map_rows
    )
    all_branch_match = all(
        int(row["matching_geometry_case_count"]) == len(case_contexts) for row in branch_map_rows
    )
    salt1_note = (
        "Salt 1 Jin currently points at the latest-window refresh root that AGENT-121 is rebuilding; "
        "this audit records the latest readable package snapshot rather than waiting for the full republish chain."
    )
    return f"""# Ethan Reduction-Contract Audit

Generated: `{iso_timestamp()}`

## Scope

- Paper-grade Salt subset only: `Salt 1 Jin`, `Salt 2 Jin`, `Salt 3 Jin`, `Salt 4 Jin`.
- This package is additive and provenance-first: it reuses existing reduced package roots instead of reopening the older June 10-26 builders.
- Source package roots:
{chr(10).join(source_rows)}

## Main findings

- Station contract shared across all paper-grade cases: `{all_station_match}`.
- Branch geometry contract shared across all paper-grade cases: `{all_branch_match}`.
- Branch map rows published: `{len(branch_map_rows)}`.
- Reduction-choice audit rows published: `{len(reduction_choice_rows)}`.
- {salt1_note}

## Boundaries

- Salt 2-4 currently reuse the June 15 reduced package roots; this audit makes that mixed provenance explicit rather than pretending every case already passed through the live June 29 rerun.
- Flow direction remains a manual profile assumption encoded in the per-case analysis manifests.
- Deferred terms still include the unsampled profile-level `dp` term and inferred feature wall `dp` term where the manifest says so.
"""


def write_import_manifest(
    *,
    inventory_csv: Path,
    closure_branch_policy_csv: Path,
    package_roots: dict[str, Path],
    output_dir: Path,
    work_product_dir: Path,
    import_manifest_path: Path,
) -> None:
    payload = {
        "generated_at": iso_timestamp(),
        "package": "2026-06-29_ethan_reduction_contract_audit",
        "inputs": {
            "paper_case_inventory_csv": str(inventory_csv.resolve()),
            "closure_branch_policy_csv": str(closure_branch_policy_csv.resolve()),
            "package_roots": {source_id: str(path.resolve()) for source_id, path in package_roots.items()},
        },
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "work_product_dir": str(work_product_dir.resolve()),
            "station_map_csv": str((work_product_dir / "station_map.csv").resolve()),
            "branch_map_csv": str((work_product_dir / "branch_map.csv").resolve()),
            "source_contract_map_csv": str((work_product_dir / "source_contract_map.csv").resolve()),
            "reduction_choice_audit_csv": str((work_product_dir / "reduction_choice_audit.csv").resolve()),
            "paper_reduced_branch_summary_csv": str((work_product_dir / "paper_reduced_branch_summary.csv").resolve()),
            "paper_reduced_major_loss_summary_csv": str((work_product_dir / "paper_reduced_major_loss_summary.csv").resolve()),
            "paper_reduced_streamwise_heat_loss_summary_csv": str(
                (work_product_dir / "paper_reduced_streamwise_heat_loss_summary.csv").resolve()
            ),
        },
    }
    write_json(import_manifest_path, payload)


def main() -> int:
    args = parse_args()
    inventory_csv = Path(args.paper_case_inventory_csv)
    closure_branch_policy_csv = Path(args.closure_branch_policy_csv)
    output_dir = ensure_dir(Path(args.output_dir))
    work_product_dir = ensure_dir(Path(args.work_product_dir))
    import_manifest_path = Path(args.import_manifest_path)
    package_roots = package_roots_from_args(args)

    inventory_rows = load_csv_rows(inventory_csv)
    paper_grade_rows = select_paper_grade_inventory_rows(inventory_rows)
    policy_rows = load_csv_rows(closure_branch_policy_csv)
    case_contexts = [load_case_context(row, package_roots[row["source_id"]]) for row in paper_grade_rows]

    station_map_rows = build_station_map_rows(case_contexts)
    branch_map_rows = build_branch_map_rows(case_contexts, policy_rows)
    source_contract_rows = build_source_contract_rows(case_contexts)
    reduction_choice_rows = build_reduction_choice_rows(case_contexts)
    reduced_branch_rows = build_reduced_branch_rows(case_contexts)
    reduced_major_loss_rows = build_reduced_major_loss_rows(case_contexts)
    reduced_streamwise_rows = build_reduced_streamwise_rows(case_contexts)

    csv_dump_rows(work_product_dir / "station_map.csv", station_map_rows)
    csv_dump_rows(work_product_dir / "branch_map.csv", branch_map_rows)
    csv_dump_rows(work_product_dir / "source_contract_map.csv", source_contract_rows)
    csv_dump_rows(work_product_dir / "reduction_choice_audit.csv", reduction_choice_rows)
    csv_dump_rows(work_product_dir / "paper_reduced_branch_summary.csv", reduced_branch_rows)
    csv_dump_rows(work_product_dir / "paper_reduced_major_loss_summary.csv", reduced_major_loss_rows)
    csv_dump_rows(work_product_dir / "paper_reduced_streamwise_heat_loss_summary.csv", reduced_streamwise_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "paper_grade_case_count": len(case_contexts),
        "station_row_count": len(station_map_rows),
        "branch_count": len(branch_map_rows),
        "reduction_choice_count": len(reduction_choice_rows),
        "all_cases_match_station_contract": all(
            int(row["matching_source_case_count"]) == len(case_contexts) for row in station_map_rows
        ),
        "all_cases_match_branch_geometry": all(
            int(row["matching_geometry_case_count"]) == len(case_contexts) for row in branch_map_rows
        ),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        build_readme(
            case_contexts=case_contexts,
            station_map_rows=station_map_rows,
            branch_map_rows=branch_map_rows,
            reduction_choice_rows=reduction_choice_rows,
        ),
        encoding="utf-8",
    )
    write_import_manifest(
        inventory_csv=inventory_csv,
        closure_branch_policy_csv=closure_branch_policy_csv,
        package_roots=package_roots,
        output_dir=output_dir,
        work_product_dir=work_product_dir,
        import_manifest_path=import_manifest_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
