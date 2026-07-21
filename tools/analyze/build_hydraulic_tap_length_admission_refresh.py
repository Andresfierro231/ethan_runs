#!/usr/bin/env python3
"""Refresh hydraulic two-tap K admission with mesh-centerline tap lengths."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh"

MINOR_TWO_TAP = REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv"
AGENT338_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_reset_k_admission_contract"
AGENT338_TAP_GAPS = AGENT338_DIR / "tap_length_gap_table.csv"
AGENT338_COMPONENT_K = AGENT338_DIR / "component_cluster_k_admission_table.csv"
MESH_CENTERLINE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"

# Endpoint station choices are explicit because some span station order follows
# patch numbering and some follows the PCA arc direction.
FEATURE_ENDPOINT_STATIONS = {
    "corner_lower_left": ("left_lower_leg__s00", "lower_leg__s00"),
    "corner_lower_right": ("lower_leg__s04", "right_leg__s00"),
    "corner_upper_right": ("right_leg__s04", "upper_leg__s04"),
    "corner_upper_left": ("upper_leg__s00", "left_upper_leg__s04"),
}


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _fnum(value: object, default: float = math.nan) -> float:
    try:
        text = str(value).strip()
        if text == "" or text.lower() in {"nan", "none", "na"}:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _fmt(value: float) -> str:
    return f"{value:.12g}" if math.isfinite(value) else ""


def _station_index(source_id: str) -> Dict[str, Dict[str, object]]:
    path = MESH_CENTERLINE_DIR / source_id / "mesh_stations.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["label"]: row for row in payload.get("stations", [])}


def _distance(a: Mapping[str, object], b: Mapping[str, object]) -> float:
    dx = _fnum(a.get("x")) - _fnum(b.get("x"))
    dy = _fnum(a.get("y")) - _fnum(b.get("y"))
    dz = _fnum(a.get("z")) - _fnum(b.get("z"))
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _length_row(row: Mapping[str, str]) -> Dict[str, object]:
    source_id = row.get("source_id", "")
    feature = row.get("feature", "")
    labels = FEATURE_ENDPOINT_STATIONS.get(feature)
    stations = _station_index(source_id)
    current_proxy = _fnum(row.get("tap_length_proxy_m"))

    if not labels:
        return {
            "join_key": row.get("join_key", ""),
            "source_id": source_id,
            "case_id": row.get("case_id", ""),
            "feature": feature,
            "start_patch": row.get("start_patch", ""),
            "end_patch": row.get("end_patch", ""),
            "downstream_span": row.get("downstream_span", ""),
            "current_tap_length_proxy_m": row.get("tap_length_proxy_m", ""),
            "centerline_tap_length_m": "",
            "length_ratio_vs_proxy": "",
            "start_station_label": "",
            "end_station_label": "",
            "length_basis": "missing_feature_endpoint_mapping",
            "centerline_length_status": "blocked_requires_raw_two_tap_extraction",
            "mesh_stations_source": _rel(MESH_CENTERLINE_DIR / source_id / "mesh_stations.json"),
            "quality_flags": row.get("quality_flags", ""),
        }

    start_label, end_label = labels
    start = stations.get(start_label)
    end = stations.get(end_label)
    if start is None or end is None:
        return {
            "join_key": row.get("join_key", ""),
            "source_id": source_id,
            "case_id": row.get("case_id", ""),
            "feature": feature,
            "start_patch": row.get("start_patch", ""),
            "end_patch": row.get("end_patch", ""),
            "downstream_span": row.get("downstream_span", ""),
            "current_tap_length_proxy_m": row.get("tap_length_proxy_m", ""),
            "centerline_tap_length_m": "",
            "length_ratio_vs_proxy": "",
            "start_station_label": start_label,
            "end_station_label": end_label,
            "length_basis": "mesh_centerline_endpoint_stations",
            "centerline_length_status": "blocked_missing_mesh_station",
            "mesh_stations_source": _rel(MESH_CENTERLINE_DIR / source_id / "mesh_stations.json"),
            "quality_flags": row.get("quality_flags", ""),
        }

    centerline_length = _distance(start, end)
    ratio = centerline_length / current_proxy if math.isfinite(current_proxy) and current_proxy > 0 else math.nan
    return {
        "join_key": row.get("join_key", ""),
        "source_id": source_id,
        "case_id": row.get("case_id", ""),
        "feature": feature,
        "start_patch": row.get("start_patch", ""),
        "end_patch": row.get("end_patch", ""),
        "downstream_span": row.get("downstream_span", ""),
        "current_tap_length_proxy_m": row.get("tap_length_proxy_m", ""),
        "centerline_tap_length_m": _fmt(centerline_length),
        "length_ratio_vs_proxy": _fmt(ratio),
        "start_station_label": start_label,
        "end_station_label": end_label,
        "length_basis": "mesh_centerline_endpoint_chord_between_fitting_end_stations",
        "centerline_length_status": "resolved_from_existing_mesh_centerline",
        "mesh_stations_source": _rel(MESH_CENTERLINE_DIR / source_id / "mesh_stations.json"),
        "quality_flags": row.get("quality_flags", ""),
    }


def _admission_status(row: Mapping[str, str], length_status: str) -> str:
    flags = row.get("quality_flags", "")
    if "recirculation" in flags or row.get("recirculation_adjacent_spans", ""):
        return "diagnostic_only_recirculation_adjacent"
    if length_status != "resolved_from_existing_mesh_centerline":
        return "blocked_missing_centerline_tap_length"
    if "coarse_no_gci" in flags:
        return "blocked_mesh_gci_after_tap_refresh"
    if row.get("fit_eligible", "").strip().lower() == "yes":
        return "candidate_fit_admissible"
    if row.get("validation_eligible", "").strip().lower() == "yes":
        return "validation_only_not_fit"
    return "blocked_not_fit_or_validation_eligible"


def _admission_action(status: str) -> str:
    if status == "blocked_mesh_gci_after_tap_refresh":
        return "Carry centerline-length K as diagnostic; require mesh-family/GCI pressure evidence before fit admission."
    if status == "diagnostic_only_recirculation_adjacent":
        return "Exclude from universal component K fitting; preserve as recirculation/branch diagnostic."
    if status == "blocked_missing_centerline_tap_length":
        return "Run raw two-tap extraction or add endpoint mapping before recomputing K."
    if status == "candidate_fit_admissible":
        return "May enter bounded H1 fit only with train/validation/holdout split and no thermal fitting."
    if status == "validation_only_not_fit":
        return "Use for no-refit validation diagnostics only."
    return "Audit row before use."


def _recomputed_k_row(row: Mapping[str, str], length: Mapping[str, object]) -> Dict[str, object]:
    length_status = str(length.get("centerline_length_status", ""))
    centerline_length = _fnum(length.get("centerline_tap_length_m"))
    feature_loss = _fnum(row.get("feature_total_pressure_loss_pa"))
    gradient = _fnum(row.get("straight_loss_gradient_pa_m"), 0.0)
    q_ref = _fnum(row.get("q_ref_local_pa"))
    old_local = _fnum(row.get("K_local"))
    new_straight = gradient * centerline_length if math.isfinite(centerline_length) else math.nan
    new_local_loss = feature_loss - new_straight if math.isfinite(new_straight) else math.nan
    new_k = new_local_loss / q_ref if math.isfinite(new_local_loss) and math.isfinite(q_ref) and q_ref != 0.0 else math.nan
    status = _admission_status(row, length_status)

    return {
        "join_key": row.get("join_key", ""),
        "source_id": row.get("source_id", ""),
        "case_id": row.get("case_id", ""),
        "feature": row.get("feature", ""),
        "feature_type": row.get("feature_type", ""),
        "downstream_span": row.get("downstream_span", ""),
        "adjacent_spans": row.get("adjacent_spans", ""),
        "K_apparent": row.get("K_apparent", ""),
        "K_local_old_dz_proxy": row.get("K_local", ""),
        "K_local_centerline": _fmt(new_k),
        "delta_K_local_centerline_minus_proxy": _fmt(new_k - old_local) if math.isfinite(new_k) and math.isfinite(old_local) else "",
        "feature_total_pressure_loss_pa": row.get("feature_total_pressure_loss_pa", ""),
        "old_adjacent_straight_loss_subtracted_pa": row.get("adjacent_straight_loss_subtracted_pa", ""),
        "centerline_adjacent_straight_loss_subtracted_pa": _fmt(new_straight),
        "q_ref_local_pa": row.get("q_ref_local_pa", ""),
        "tap_length_proxy_m": row.get("tap_length_proxy_m", ""),
        "centerline_tap_length_m": length.get("centerline_tap_length_m", ""),
        "centerline_length_status": length_status,
        "fit_eligible": row.get("fit_eligible", ""),
        "validation_eligible": row.get("validation_eligible", ""),
        "admission_status": status,
        "coefficient_name_allowed": "yes_component_K_candidate" if status == "candidate_fit_admissible" else "no_universal_K_yet",
        "required_next_action": _admission_action(status),
        "quality_flags": row.get("quality_flags", ""),
        "source_bend_minor_loss_csv": row.get("source_bend_minor_loss_csv", ""),
    }


def _readme_text(summary: Mapping[str, object]) -> str:
    return f"""# Hydraulic Tap-Length Admission Refresh

Date: 2026-07-14

## Decision

This package implements the HYD-TAP slice from the hydraulic plan. Existing mesh-centerline station artifacts replace the `abs(dz)` tap-length proxy for preserved corner rows where endpoint stations are available. This is a diagnostic/admission refresh only: it does not mutate CFD outputs, edit external Fluid code, fit thermal terms, or introduce a global hydraulic multiplier.

## Result

- Rows with centerline length resolved: {summary['centerline_resolved_rows']}
- Rows still missing centerline/raw two-tap evidence: {summary['centerline_blocked_rows']}
- Component/cluster K rows recomputed: {summary['component_k_rows']}
- Fit-admissible component/cluster K rows: {summary['component_fit_admissible_rows']}
- Rows still blocked by mesh/GCI after tap refresh: {summary['blocked_mesh_gci_after_tap_refresh_rows']}
- Recirculation diagnostic rows: {summary['recirculation_diagnostic_rows']}

## Recommended Next Work

1. Use this package as the H1 local-K evidence refresh, but do not fit component/cluster K yet because no row is fit-admissible.
2. Run raw two-tap extraction for `test_section_complex` rows if those connector losses are still needed.
3. Move to the Fluid reset/development API row next; H1 remains blocked until reset/development terms and admitted pressure evidence are first-class.
"""


def build_package(output_dir: Path = OUTPUT_DIR) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    minor_rows = _read_csv(MINOR_TWO_TAP)
    length_rows = [_length_row(row) for row in minor_rows]
    lengths_by_key = {str(row["join_key"]): row for row in length_rows}
    recomputed_rows = [_recomputed_k_row(row, lengths_by_key.get(row["join_key"], {})) for row in minor_rows]

    readiness_rows = [
        {
            "gate_id": "H1_component_cluster_K",
            "current_status": "blocked",
            "evidence_count": len(recomputed_rows),
            "admitted_count": sum(1 for row in recomputed_rows if row["admission_status"] == "candidate_fit_admissible"),
            "blocking_gap": "no fit-admissible component/cluster K rows after tap-length refresh",
            "next_action": "Require mesh-family/GCI pressure evidence and keep recirculation rows diagnostic.",
        },
        {
            "gate_id": "H1_reset_development",
            "current_status": "blocked",
            "evidence_count": "see AGENT-338 reset contract",
            "admitted_count": 0,
            "blocking_gap": "first-class reset/development Fluid API is not implemented in this repo-local slice",
            "next_action": "Claim external Fluid reset/development API row before any H1 faithful rerun.",
        },
        {
            "gate_id": "H1_faithful_rerun",
            "current_status": "not_launchable",
            "evidence_count": len(recomputed_rows),
            "admitted_count": 0,
            "blocking_gap": "local K and reset/development terms are not admitted",
            "next_action": "Do not launch H1; produce blocked gate until HYD-RESET-API and mesh/GCI admission exist.",
        },
    ]

    status_counts = Counter(str(row["admission_status"]) for row in recomputed_rows)
    length_counts = Counter(str(row["centerline_length_status"]) for row in length_rows)
    source_rows = [
        {"source_id": "minor_two_tap", "path": _rel(MINOR_TWO_TAP), "role": "original two-tap K rows with dz proxy"},
        {"source_id": "agent338_tap_gaps", "path": _rel(AGENT338_TAP_GAPS), "role": "tap-gap priorities and blockers"},
        {"source_id": "agent338_component_k", "path": _rel(AGENT338_COMPONENT_K), "role": "prior component/cluster K admission status"},
        {"source_id": "mesh_centerlines", "path": _rel(MESH_CENTERLINE_DIR), "role": "existing mesh-centerline station artifacts"},
    ]

    _write_csv(
        output_dir / "tap_centerline_length_table.csv",
        [
            "join_key",
            "source_id",
            "case_id",
            "feature",
            "start_patch",
            "end_patch",
            "downstream_span",
            "current_tap_length_proxy_m",
            "centerline_tap_length_m",
            "length_ratio_vs_proxy",
            "start_station_label",
            "end_station_label",
            "length_basis",
            "centerline_length_status",
            "mesh_stations_source",
            "quality_flags",
        ],
        length_rows,
    )
    _write_csv(
        output_dir / "component_cluster_k_recomputed_admission_table.csv",
        [
            "join_key",
            "source_id",
            "case_id",
            "feature",
            "feature_type",
            "downstream_span",
            "adjacent_spans",
            "K_apparent",
            "K_local_old_dz_proxy",
            "K_local_centerline",
            "delta_K_local_centerline_minus_proxy",
            "feature_total_pressure_loss_pa",
            "old_adjacent_straight_loss_subtracted_pa",
            "centerline_adjacent_straight_loss_subtracted_pa",
            "q_ref_local_pa",
            "tap_length_proxy_m",
            "centerline_tap_length_m",
            "centerline_length_status",
            "fit_eligible",
            "validation_eligible",
            "admission_status",
            "coefficient_name_allowed",
            "required_next_action",
            "quality_flags",
            "source_bend_minor_loss_csv",
        ],
        recomputed_rows,
    )
    _write_csv(
        output_dir / "h1_faithful_readiness_after_tap_refresh.csv",
        ["gate_id", "current_status", "evidence_count", "admitted_count", "blocking_gap", "next_action"],
        readiness_rows,
    )
    _write_csv(output_dir / "source_manifest.csv", ["source_id", "path", "role"], source_rows)

    summary: Dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "centerline_resolved_rows": int(length_counts["resolved_from_existing_mesh_centerline"]),
        "centerline_blocked_rows": len(length_rows) - int(length_counts["resolved_from_existing_mesh_centerline"]),
        "centerline_length_status_counts": dict(length_counts),
        "component_k_rows": len(recomputed_rows),
        "component_fit_admissible_rows": int(status_counts["candidate_fit_admissible"]),
        "blocked_mesh_gci_after_tap_refresh_rows": int(status_counts["blocked_mesh_gci_after_tap_refresh"]),
        "recirculation_diagnostic_rows": int(status_counts["diagnostic_only_recirculation_adjacent"]),
        "component_k_status_counts": dict(status_counts),
        "h1_faithful_launchable": False,
        "native_solver_outputs_mutated": False,
        "thermal_fit_used": False,
        "global_multiplier_exported": False,
        "external_fluid_code_edited": False,
        "recommendation": "do_not_fit_component_k_yet; proceed_to_reset_development_api_and_mesh_gci_admission",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(_readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build_package(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
