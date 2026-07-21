#!/usr/bin/env python3
"""Build val_salt2 heat-readiness and corner-K unlock ledgers from existing evidence."""

from __future__ import annotations

import csv
import json
import math
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-483"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock")
OUT = ROOT / OUT_REL

VAL_AGG = ROOT / "registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates"
VAL_SQLITE = VAL_AGG / "postprocessing.sqlite"
VAL_SECTION_LEDGER = ROOT / (
    "work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/"
    "val_salt2_section_heat_loss_ledger.csv"
)
VAL_BC_SUMMARY = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/"
    "boundary_condition_summary.csv"
)
AGENT473_JUNCTION_SPLIT = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/"
    "junction_split_heat_ledger.csv"
)
PRESSURE_BRANCH_ADMISSION = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/"
    "branch_orientation_straight_loss_recirc_admission.csv"
)
PRESSURE_STATIONS = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/"
    "all_streamwise_pressure_1d_map.csv"
)
CORNER_EVIDENCE = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/"
    "corner_pressure_drop_evidence_state.csv"
)
CORNER_RECOMPUTED = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/"
    "component_cluster_k_recomputed_admission_table.csv"
)
TAP_LENGTHS = ROOT / (
    "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/"
    "tap_centerline_length_table.csv"
)

VAL_CASE_KEY = "val_salt2"
VAL_CASE_ID = "val_salt_2"
VAL_DISPLAY = "val_salt_test_2_coarse_mesh"
VAL_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
TERMINAL_START_S = 8302.0
TERMINAL_END_S = 8602.0
PHYSICAL_SECTION_KEYS = {
    "heater",
    "test_section",
    "cooling_branch",
    "downcomer",
    "upcomer",
    "upper_transport",
    "lower_transport",
    "junctions",
    "other",
}

JUNCTION_BUCKET_LABELS = {
    "lower_left": "lower-left junction/stub group",
    "lower_right": "lower-right junction/stub group",
    "upper_left": "upper-left junction/stub group",
    "upper_right": "upper-right junction/stub group",
}
CORNER_ORDER = ["corner_lower_left", "corner_lower_right", "corner_upper_right", "corner_upper_left"]
CASE_KEY_BY_CASE_ID = {"salt_2": "salt2_mainline", "salt_3": "salt3_mainline", "salt_4": "salt4_mainline"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def fmt(value: float | str | None, digits: int = 12) -> str:
    if value in ("", None):
        return ""
    number = fnum(value)
    return f"{number:.{digits}g}"


def section_for_patch(name: str) -> tuple[str, str, str]:
    if name.startswith("junction_"):
        return ("junctions", "junction and stub surfaces", "junction_or_stub")
    if name.startswith("ncc_"):
        return ("zero_gradient_ncc_connector", "non-conformal connector zero-gradient patches", "zero_gradient_ncc_connector")
    if name in {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}:
        return ("heater", "lower-leg heater patches", "heater/source")
    if name == "pipeleg_left_04_test_section":
        return ("test_section", "powered test-section patch", "test-section/source-or-loss")
    if name in {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}:
        return ("cooling_branch", "upper reducer/cooler branch", "cooler/HX/removal")
    if name.startswith("pipeleg_right_"):
        return ("downcomer", "right downcomer", "passive wall loss")
    if name.startswith("pipeleg_left_"):
        return ("upcomer", "left upcomer excluding test section", "passive wall loss")
    if name.startswith("pipeleg_upper_"):
        return ("upper_transport", "upper transport outside cooler", "passive wall loss")
    if name.startswith("pipeleg_lower_"):
        return ("lower_transport", "lower transport outside heater", "passive wall loss")
    return ("other", "unmapped wallHeatFlux entity", "unmapped")


def junction_bucket(name: str) -> str:
    for bucket in JUNCTION_BUCKET_LABELS:
        if name.startswith(f"junction_{bucket}"):
            return bucket
    return ""


def patch_subrole(name: str) -> str:
    if name.endswith("_stub"):
        return "stub"
    if name.endswith("_step"):
        return "step"
    if "_extension" in name:
        return "extension"
    if name.startswith("junction_"):
        return "corner_body"
    if name.startswith("ncc_"):
        return "ncc_interface"
    return "section_wall"


def load_wall_heat_rows(sqlite_path: Path = VAL_SQLITE) -> list[dict[str, Any]]:
    con = sqlite3.connect(sqlite_path)
    latest_time = con.execute(
        "select max(time_s) from postprocessing_case_long where dataset='wall_heat_flux'"
    ).fetchone()[0]
    latest = {
        (row[0], row[1]): row[2]
        for row in con.execute(
            """
            select entity_name, value_name, value
            from postprocessing_case_long
            where dataset='wall_heat_flux' and time_s=?
            """,
            (latest_time,),
        )
    }
    stats = {
        row[0]: {
            "terminal_mean_q_net_w": row[1],
            "terminal_min_q_net_w": row[2],
            "terminal_max_q_net_w": row[3],
            "terminal_sample_count": row[4],
        }
        for row in con.execute(
            """
            select entity_name, avg(value), min(value), max(value), count(*)
            from postprocessing_case_long
            where dataset='wall_heat_flux'
              and value_name='q_net_w'
              and time_s between ? and ?
            group by entity_name
            """,
            (TERMINAL_START_S, TERMINAL_END_S),
        )
    }
    first_time = con.execute(
        """
        select min(time_s) from postprocessing_case_long
        where dataset='wall_heat_flux' and value_name='q_net_w' and time_s between ? and ?
        """,
        (TERMINAL_START_S, TERMINAL_END_S),
    ).fetchone()[0]
    first = {
        row[0]: row[1]
        for row in con.execute(
            """
            select entity_name, value
            from postprocessing_case_long
            where dataset='wall_heat_flux' and value_name='q_net_w' and time_s=?
            """,
            (first_time,),
        )
    }
    entities = sorted({key[0] for key in latest})
    rows: list[dict[str, Any]] = []
    for entity in entities:
        section_key, section_label, role = section_for_patch(entity)
        q_latest = latest.get((entity, "q_net_w"), 0.0)
        q_first = first.get(entity, q_latest)
        rows.append(
            {
                "case_key": VAL_CASE_KEY,
                "case_id": VAL_CASE_ID,
                "display_label": VAL_DISPLAY,
                "source_id": VAL_SOURCE_ID,
                "entity_name": entity,
                "section_key": section_key,
                "section_label": section_label,
                "thermal_role": role,
                "physical_junction_bucket": junction_bucket(entity),
                "physical_junction_label": JUNCTION_BUCKET_LABELS.get(junction_bucket(entity), ""),
                "patch_subrole": patch_subrole(entity),
                "latest_time_s": latest_time,
                "latest_q_net_w": q_latest,
                "latest_q_avg_w_m2": latest.get((entity, "q_avg_w_m2"), ""),
                "latest_min_w_m2": latest.get((entity, "min_w_m2"), ""),
                "latest_max_w_m2": latest.get((entity, "max_w_m2"), ""),
                "terminal_window_start_s": TERMINAL_START_S,
                "terminal_window_end_s": TERMINAL_END_S,
                "terminal_mean_q_net_w": stats.get(entity, {}).get("terminal_mean_q_net_w", ""),
                "terminal_min_q_net_w": stats.get(entity, {}).get("terminal_min_q_net_w", ""),
                "terminal_max_q_net_w": stats.get(entity, {}).get("terminal_max_q_net_w", ""),
                "terminal_sample_count": stats.get(entity, {}).get("terminal_sample_count", 0),
                "terminal_first_to_latest_drift_w": q_latest - q_first,
                "external_loss_positive_w": max(-q_latest, 0.0),
                "source_component_w": max(q_latest, 0.0),
                "removal_component_w": max(-q_latest, 0.0),
                "sign_convention": "positive is net heat into fluid; negative is heat removed from fluid",
                "source_path": rel(sqlite_path),
            }
        )
    return rows


def build_section_reconciliation(patch_rows: list[dict[str, Any]], ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    patch_by_section: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    patch_counts: Counter[str] = Counter()
    for row in patch_rows:
        section = row["section_key"]
        patch_counts[section] += 1
        patch_by_section[section]["latest"] += fnum(row["latest_q_net_w"])
        patch_by_section[section]["mean"] += fnum(row["terminal_mean_q_net_w"])

    rows: list[dict[str, Any]] = []
    ledger_sections = {row["section_key"]: row for row in ledger_rows if row["section_key"] in PHYSICAL_SECTION_KEYS}
    for section, ledger in ledger_sections.items():
        latest_patch = patch_by_section[section]["latest"]
        mean_patch = patch_by_section[section]["mean"]
        latest_ledger = fnum(ledger.get("latest_cfd_realized_net_to_fluid_W"))
        mean_ledger = fnum(ledger.get("terminal_window_mean_net_to_fluid_W"))
        rows.append(
            {
                "case_key": VAL_CASE_KEY,
                "section_key": section,
                "section_label": ledger.get("section_label", ""),
                "thermal_role": ledger.get("thermal_role", ""),
                "patch_count": patch_counts[section],
                "latest_patch_sum_q_net_w": latest_patch,
                "latest_section_ledger_q_net_w": latest_ledger,
                "latest_residual_patch_minus_ledger_w": latest_patch - latest_ledger,
                "terminal_mean_patch_sum_q_net_w": mean_patch,
                "terminal_mean_section_ledger_q_net_w": mean_ledger,
                "terminal_mean_residual_patch_minus_ledger_w": mean_patch - mean_ledger,
                "reconciliation_status": "pass" if abs(latest_patch - latest_ledger) < 1e-6 else "review",
                "source_paths": f"{rel(VAL_SQLITE)};{rel(VAL_SECTION_LEDGER)}",
            }
        )
    total_latest = sum(fnum(row["latest_q_net_w"]) for row in patch_rows)
    total_mean = sum(fnum(row["terminal_mean_q_net_w"]) for row in patch_rows)
    ledger_total_row = next(row for row in ledger_rows if row["section_key"] == "total_Q_postProc")
    ledger_latest = fnum(ledger_total_row.get("latest_cfd_realized_net_to_fluid_W"))
    ledger_mean = fnum(ledger_total_row.get("terminal_window_mean_net_to_fluid_W"))
    rows.append(
        {
            "case_key": VAL_CASE_KEY,
            "section_key": "case_total_check",
            "section_label": "all wallHeatFlux patch entities",
            "thermal_role": "closure_check",
            "patch_count": len(patch_rows),
            "latest_patch_sum_q_net_w": total_latest,
            "latest_section_ledger_q_net_w": ledger_latest,
            "latest_residual_patch_minus_ledger_w": total_latest - ledger_latest,
            "terminal_mean_patch_sum_q_net_w": total_mean,
            "terminal_mean_section_ledger_q_net_w": ledger_mean,
            "terminal_mean_residual_patch_minus_ledger_w": total_mean - ledger_mean,
            "reconciliation_status": "pass" if abs(total_latest - ledger_latest) < 1e-6 else "review",
            "source_paths": f"{rel(VAL_SQLITE)};{rel(VAL_SECTION_LEDGER)}",
        }
    )
    return rows


def build_junction_split(patch_rows: list[dict[str, Any]], ledger_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    junction_latest = -fnum(next(row["latest_cfd_realized_net_to_fluid_W"] for row in ledger_rows if row["section_key"] == "junctions"))
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in patch_rows:
        if row["section_key"] == "junctions":
            by_bucket[row["physical_junction_bucket"]].append(row)
    rows: list[dict[str, Any]] = []
    for bucket in JUNCTION_BUCKET_LABELS:
        group = by_bucket[bucket]
        latest_q = sum(fnum(row["latest_q_net_w"]) for row in group)
        mean_q = sum(fnum(row["terminal_mean_q_net_w"]) for row in group)
        loss = max(-latest_q, 0.0)
        rows.append(
            {
                "case_key": VAL_CASE_KEY,
                "case_id": VAL_CASE_ID,
                "source_id": VAL_SOURCE_ID,
                "physical_junction_bucket": bucket,
                "physical_junction_label": JUNCTION_BUCKET_LABELS[bucket],
                "patch_count": len(group),
                "stub_patch_count": sum(row["patch_subrole"] == "stub" for row in group),
                "extension_patch_count": sum(row["patch_subrole"] == "extension" for row in group),
                "step_patch_count": sum(row["patch_subrole"] == "step" for row in group),
                "realized_wallHeatFlux_W": latest_q,
                "terminal_mean_wallHeatFlux_W": mean_q,
                "realized_external_loss_positive_W": loss,
                "source_aggregate_junction_loss_positive_W": junction_latest,
                "fraction_of_case_junction_loss": loss / junction_latest if junction_latest else "",
                "model_use": "external_test_target_only_not_runtime_input",
                "source_path": rel(VAL_SQLITE),
            }
        )
    split_total = sum(fnum(row["realized_external_loss_positive_W"]) for row in rows)
    rows.append(
        {
            "case_key": VAL_CASE_KEY,
            "case_id": VAL_CASE_ID,
            "source_id": VAL_SOURCE_ID,
            "physical_junction_bucket": "case_total_check",
            "physical_junction_label": "sum of four val_salt2 junction/stub buckets",
            "patch_count": sum(fnum(row["patch_count"]) for row in rows),
            "stub_patch_count": sum(fnum(row["stub_patch_count"]) for row in rows),
            "extension_patch_count": sum(fnum(row["extension_patch_count"]) for row in rows),
            "step_patch_count": sum(fnum(row["step_patch_count"]) for row in rows),
            "realized_wallHeatFlux_W": -split_total,
            "terminal_mean_wallHeatFlux_W": "",
            "realized_external_loss_positive_W": split_total,
            "source_aggregate_junction_loss_positive_W": junction_latest,
            "fraction_of_case_junction_loss": split_total / junction_latest if junction_latest else "",
            "model_use": "closure_check",
            "source_path": rel(VAL_SQLITE),
        }
    )
    return rows


def build_val_training_gate(
    patch_rows: list[dict[str, Any]],
    section_rows: list[dict[str, Any]],
    junction_rows: list[dict[str, Any]],
    bc_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    max_section_residual = max(abs(fnum(row["latest_residual_patch_minus_ledger_w"])) for row in section_rows)
    junction_total = next(row for row in junction_rows if row["physical_junction_bucket"] == "case_total_check")
    junction_residual = fnum(junction_total["realized_external_loss_positive_W"]) - fnum(
        junction_total["source_aggregate_junction_loss_positive_W"]
    )
    rows = [
        {
            "gate": "patch_level_wall_heat_flux_available",
            "status": "pass" if len(patch_rows) == 69 else "review",
            "observed_value": len(patch_rows),
            "criterion": "69 wall_heat_flux entities, including wall and zero-gradient connector patches",
            "consequence": "val_salt2 can now be audited below aggregate section level",
        },
        {
            "gate": "section_reconciliation_to_july15_ledger",
            "status": "pass" if max_section_residual < 1e-6 else "review",
            "observed_value": max_section_residual,
            "criterion": "maximum absolute latest patch-minus-section residual < 1e-6 W",
            "consequence": "patch extraction is consistent with the accepted section ledger",
        },
        {
            "gate": "junction_split_closes_to_section_junction_loss",
            "status": "pass" if abs(junction_residual) < 1e-6 else "review",
            "observed_value": junction_residual,
            "criterion": "four-bucket junction split sums to July 15 aggregate junction loss",
            "consequence": "val_salt2 junction/stub heat is now comparable to Salt2-4 split ledgers",
        },
        {
            "gate": "bc_source_material_contract_available",
            "status": "pass" if len(bc_rows) >= 9 else "review",
            "observed_value": len(bc_rows),
            "criterion": "val_salt2 BC/source/material rows from AGENT-422/July 14 documentation",
            "consequence": "thermal roles and runtime-input guardrails are documented",
        },
        {
            "gate": "external_test_policy_locked",
            "status": "pass_guardrail",
            "observed_value": "AGENT-481 external-test-only",
            "criterion": "do not fit or tune on val_salt2 unless explicitly reclassified later",
            "consequence": "training-quality postprocessing exists, but blind validation is preserved",
        },
        {
            "gate": "training_use_without_reclassification",
            "status": "fail_policy",
            "observed_value": "not allowed by current split policy",
            "criterion": "explicit future decision must spend the external-test row before training",
            "consequence": "usable as main external evidence now; not admitted as training evidence now",
        },
    ]
    return rows


def build_corner_k_rows(
    corner_rows: list[dict[str, str]],
    recomputed_rows: list[dict[str, str]],
    tap_rows: list[dict[str, str]],
    branch_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    recomputed = {row["join_key"]: row for row in recomputed_rows}
    taps = {row["join_key"]: row for row in tap_rows}
    branch_by_case = defaultdict(list)
    for row in branch_rows:
        branch_by_case[row["case_key"]].append(row)
    out: list[dict[str, Any]] = []
    for row in corner_rows:
        if not row["feature"].startswith("corner_"):
            continue
        join_key = f"{row['source_id']}:{row['feature']}:{row['downstream_span']}"
        rec = recomputed.get(join_key, {})
        tap = taps.get(join_key, {})
        case_key = CASE_KEY_BY_CASE_ID.get(row["case_id"], row["case_id"])
        branches = branch_by_case.get(case_key, [])
        recirc_blocked = sum(b.get("recirculation_mask_status") == "blocked_material_recirculation_mask" for b in branches)
        pressure_conflicts = sum("conflict" in b.get("pressure_definition_status", "") for b in branches)
        centerline_k = rec.get("K_local_centerline", "")
        centerline_status = "over_subtracted_negative_local_K" if centerline_k != "" and fnum(centerline_k) < 0 else "nonnegative"
        blockers = [
            "recirculation_mask" if recirc_blocked else "",
            "pressure_definition_conflict" if pressure_conflicts else "",
            "coarse_only_no_mesh_gci" if "coarse_no_gci" in row.get("quality_flags", "") else "",
            "straight_loss_reference_over_subtracts" if centerline_status == "over_subtracted_negative_local_K" else "",
            "component_K_not_isolated",
        ]
        blockers = [item for item in blockers if item]
        out.append(
            {
                "case_key": case_key,
                "case_id": row["case_id"],
                "source_id": row["source_id"],
                "feature": row["feature"],
                "downstream_span": row["downstream_span"],
                "adjacent_spans": rec.get("adjacent_spans", row.get("adjacent_spans", "")),
                "K_apparent": row["K_apparent"],
                "K_local_old_dz_proxy": row["K_local_upper_bound"],
                "K_local_centerline": centerline_k,
                "centerline_tap_length_m": tap.get("centerline_tap_length_m", rec.get("centerline_tap_length_m", "")),
                "tap_length_proxy_m": tap.get("current_tap_length_proxy_m", rec.get("tap_length_proxy_m", "")),
                "centerline_length_status": tap.get("centerline_length_status", rec.get("centerline_length_status", "")),
                "feature_total_pressure_loss_pa": rec.get("feature_total_pressure_loss_pa", row["feature_total_pressure_loss_pa"]),
                "old_adjacent_straight_loss_subtracted_pa": rec.get(
                    "old_adjacent_straight_loss_subtracted_pa", row["adjacent_straight_loss_subtracted_pa"]
                ),
                "centerline_adjacent_straight_loss_subtracted_pa": rec.get("centerline_adjacent_straight_loss_subtracted_pa", ""),
                "recirculation_blocked_branch_count": recirc_blocked,
                "pressure_definition_conflict_branch_count": pressure_conflicts,
                "fit_admitted": "no",
                "admission_status": "not_admitted_diagnostic_only",
                "why_diagnostic": ";".join(blockers),
                "unlock_needed": (
                    "new or repaired corner extraction with non-recirculating tap placement, admitted pressure definition, "
                    "physically local straight-loss reference, and mesh/GCI for the same corner-loss QoI"
                ),
                "source_paths": f"{rel(CORNER_EVIDENCE)};{rel(CORNER_RECOMPUTED)};{rel(TAP_LENGTHS)};{rel(PRESSURE_BRANCH_ADMISSION)}",
            }
        )
    out.sort(key=lambda r: (r["case_id"], CORNER_ORDER.index(r["feature"]) if r["feature"] in CORNER_ORDER else 99))
    return out


def build_corner_unlock_queue(corner_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in corner_rows:
        grouped[row["feature"]].append(row)
    out = []
    for feature in CORNER_ORDER:
        rows = grouped[feature]
        admitted = sum(row["fit_admitted"] == "yes" for row in rows)
        negative_centerline = sum(fnum(row["K_local_centerline"], 1.0) < 0 for row in rows)
        recirc = sum(fnum(row["recirculation_blocked_branch_count"]) > 0 for row in rows)
        conflicts = sum(fnum(row["pressure_definition_conflict_branch_count"]) > 0 for row in rows)
        out.append(
            {
                "feature": feature,
                "case_count": len(rows),
                "fit_admitted_count": admitted,
                "negative_centerline_K_count": negative_centerline,
                "recirculation_blocked_case_count": recirc,
                "pressure_definition_conflict_case_count": conflicts,
                "current_status": "diagnostic_only",
                "minimum_unlock_sequence": (
                    "1 choose pressure basis and resolve p/p_rgh conflicts; "
                    "2 place taps outside recirculation and not inside hybrid upcomer lanes; "
                    "3 recompute local straight-gradient over a physically comparable straight span; "
                    "4 repeat on mesh family/GCI before fitting K"
                ),
            }
        )
    return out


def build_val_pressure_map(station_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = [row for row in station_rows if row["case_key"] == VAL_CASE_KEY]
    return [
        {
            "case_key": row["case_key"],
            "loop_order_index": row["loop_order_index"],
            "cfd_span": row["cfd_span"],
            "station_label": row["station_label"],
            "physical_location_label": row["physical_location_label"],
            "one_d_component_segments": row["one_d_component_segments"],
            "relative_p_from_case_loop_start_Pa": row["relative_p_from_case_loop_start_Pa"],
            "relative_p_rgh_from_case_loop_start_Pa": row["relative_p_rgh_from_case_loop_start_Pa"],
            "reverse_area_fraction_proxy": row["reverse_area_fraction_proxy"],
            "mapping_status": row["mapping_status"],
            "source_path": row["source_path"],
        }
        for row in sorted(rows, key=lambda r: fnum(r["loop_order_index"]))
    ]


def svg_bar(path: Path, rows: list[dict[str, Any]], label_key: str, value_key: str, title: str) -> None:
    width, height = 900, 420
    margin_l, margin_b, margin_t = 90, 70, 50
    values = [fnum(row[value_key]) for row in rows]
    max_value = max(values) if values else 1.0
    bar_w = (width - margin_l - 40) / max(len(rows), 1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{title}</text>')
    parts.append(f'<line x1="{margin_l}" y1="{height-margin_b}" x2="{width-30}" y2="{height-margin_b}" stroke="#333"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{height-margin_b}" stroke="#333"/>')
    for i, row in enumerate(rows):
        value = fnum(row[value_key])
        x = margin_l + i * bar_w + 8
        h = (height - margin_b - margin_t) * value / max_value if max_value else 0
        y = height - margin_b - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-16:.1f}" height="{h:.1f}" fill="#4477aa"/>')
        parts.append(f'<text x="{x + (bar_w-16)/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="Arial" font-size="11">{value:.2f}</text>')
        label = str(row[label_key]).replace("corner_", "").replace("_", " ")
        parts.append(f'<text x="{x + (bar_w-16)/2:.1f}" y="{height-45}" text-anchor="middle" font-family="Arial" font-size="11">{label}</text>')
    parts.append(f'<text x="22" y="{height/2}" transform="rotate(-90 22 {height/2})" text-anchor="middle" font-family="Arial" font-size="12">{value_key}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def svg_pressure_map(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 940, 440
    margin_l, margin_b, margin_t = 85, 80, 55
    vals = [fnum(row["relative_p_rgh_from_case_loop_start_Pa"]) for row in rows]
    min_v, max_v = (min(vals), max(vals)) if vals else (0.0, 1.0)
    span = max(max_v - min_v, 1e-9)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">val_salt2 loop pressure map, p_rgh relative to loop start</text>')
    points = []
    for i, row in enumerate(rows):
        x = margin_l + i * (width - margin_l - 50) / max(len(rows) - 1, 1)
        y = margin_t + (max_v - fnum(row["relative_p_rgh_from_case_loop_start_Pa"])) * (height - margin_t - margin_b) / span
        points.append((x, y, row))
    parts.append(f'<line x1="{margin_l}" y1="{height-margin_b}" x2="{width-35}" y2="{height-margin_b}" stroke="#333"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{height-margin_b}" stroke="#333"/>')
    parts.append('<polyline fill="none" stroke="#aa3377" stroke-width="2" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points) + '"/>')
    for x, y, row in points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#aa3377"/>')
        label = row["station_label"].replace("__", " ")
        parts.append(f'<text x="{x:.1f}" y="{height-55}" transform="rotate(60 {x:.1f} {height-55})" font-family="Arial" font-size="9">{label}</text>')
    parts.append(f'<text x="20" y="{height/2}" transform="rotate(-90 20 {height/2})" text-anchor="middle" font-family="Arial" font-size="12">relative p_rgh (Pa)</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(VAL_SQLITE)}
  - {rel(VAL_SECTION_LEDGER)}
  - {rel(CORNER_EVIDENCE)}
  - {rel(CORNER_RECOMPUTED)}
  - {rel(PRESSURE_BRANCH_ADMISSION)}
tags: [val-salt2, external-test, heat-ledger, pressure-k, admission]
related:
  - .agent/status/2026-07-17_AGENT-483.md
  - .agent/journal/2026-07-17/val-salt2-training-readiness-and-corner-k-unlock.md
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 Training Readiness and Corner-K Unlock

## Main Conclusions

- `val_salt2` now has a patch-level wallHeatFlux ledger from the existing registry aggregate database. The patch ledger has `{summary['val_patch_rows']}` entities and reconciles to the July 15 section ledger with maximum latest residual `{summary['max_section_latest_residual_W']:.3e} W`.
- The `val_salt2` junction/stub split closes to the aggregate junction loss: `{summary['val_junction_loss_positive_W']:.6f} W` across four physical buckets.
- This makes `val_salt2` training-quality as an evidence artifact, but it is **not admitted as training input** under the AGENT-481 split policy. It remains external-test/blind-validation evidence unless explicitly reclassified later.
- Pressure corner K remains diagnostic. Current rows have `{summary['corner_fit_admitted_rows']}` fit-admitted entries. True centerline straight-loss subtraction over-subtracts the preserved corner rows, all current pressure-map branch rows are recirculation-blocked, and the evidence is coarse/no-GCI.

## Files

- `val_salt2_patch_heat_ledger.csv`: patch-level wallHeatFlux latest and terminal-window values.
- `val_salt2_section_reconciliation.csv`: patch sums compared with the July 15 section ledger.
- `val_salt2_junction_split_heat_ledger.csv`: four-bucket junction/stub split.
- `val_salt2_training_admission_gate.csv`: explicit external-test/training guardrail.
- `pressure_corner_k_admission_table.csv`: joined K, tap-length, recirculation, and pressure-definition admission status.
- `pressure_corner_k_unlock_queue.csv`: minimum evidence needed to turn diagnostic K into admitted component K.
- `val_salt2_pressure_map.csv`: streamwise pressure-map rows used by `pressure_loop_map_val_salt2.svg`.
- `heat_loss_junction_split_by_case.svg`, `corner_k_diagnostic_by_case.svg`, `pressure_loop_map_val_salt2.svg`: quick-look plots.

## Scientific Critique

The heat ledger is now strong enough for external validation scoring because it uses realized `wallHeatFlux` targets only and preserves BC/source/material provenance. It is not a runtime input contract for a predictive model.

The corner-K evidence is internally useful but not a closure coefficient. With mesh-centerline tap distances, the adjacent straight-loss subtraction exceeds the preserved total feature pressure loss, producing negative local centerline K for the preserved corner rows. That is a diagnostic warning about the current tap/straight-reference construction, not evidence that physical corner K is negative.

## Do Not Do

- Do not fit or tune on `val_salt2` while it is labeled external-test only.
- Do not submit duplicate pressure ladder jobs from this package.
- Do not promote corner K into the 1D model until the unlock queue gates pass.
"""
    (OUT / "README.md").write_text(readme)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    patch_rows = load_wall_heat_rows()
    section_rows = build_section_reconciliation(patch_rows, read_csv(VAL_SECTION_LEDGER))
    junction_rows = build_junction_split(patch_rows, read_csv(VAL_SECTION_LEDGER))
    gate_rows = build_val_training_gate(patch_rows, section_rows, junction_rows, read_csv(VAL_BC_SUMMARY))
    corner_rows = build_corner_k_rows(
        read_csv(CORNER_EVIDENCE),
        read_csv(CORNER_RECOMPUTED),
        read_csv(TAP_LENGTHS),
        read_csv(PRESSURE_BRANCH_ADMISSION),
    )
    unlock_rows = build_corner_unlock_queue(corner_rows)
    pressure_rows = build_val_pressure_map(read_csv(PRESSURE_STATIONS))

    write_csv(OUT / "val_salt2_patch_heat_ledger.csv", patch_rows)
    write_csv(OUT / "val_salt2_section_reconciliation.csv", section_rows)
    write_csv(OUT / "val_salt2_junction_split_heat_ledger.csv", junction_rows)
    write_csv(OUT / "val_salt2_training_admission_gate.csv", gate_rows)
    write_csv(OUT / "pressure_corner_k_admission_table.csv", corner_rows)
    write_csv(OUT / "pressure_corner_k_unlock_queue.csv", unlock_rows)
    write_csv(OUT / "val_salt2_pressure_map.csv", pressure_rows)

    svg_bar(
        OUT / "heat_loss_junction_split_by_case.svg",
        [row for row in junction_rows if row["physical_junction_bucket"] != "case_total_check"],
        "physical_junction_bucket",
        "realized_external_loss_positive_W",
        "val_salt2 junction/stub heat loss by physical bucket",
    )
    svg_bar(
        OUT / "corner_k_diagnostic_by_case.svg",
        [row for row in corner_rows if row["case_id"] == "salt_2"],
        "feature",
        "K_apparent",
        "Salt2 preserved corner apparent K, diagnostic only",
    )
    svg_pressure_map(OUT / "pressure_loop_map_val_salt2.svg", pressure_rows)

    source_manifest = [
        {"artifact": "val_salt2_registry_sqlite", "path": rel(VAL_SQLITE), "use": "patch-level wallHeatFlux extraction"},
        {"artifact": "val_salt2_section_ledger", "path": rel(VAL_SECTION_LEDGER), "use": "section reconciliation"},
        {"artifact": "val_salt2_bc_summary", "path": rel(VAL_BC_SUMMARY), "use": "BC/source/material guardrails"},
        {"artifact": "agent473_junction_split", "path": rel(AGENT473_JUNCTION_SPLIT), "use": "comparison schema/provenance"},
        {"artifact": "corner_evidence", "path": rel(CORNER_EVIDENCE), "use": "diagnostic corner K input"},
        {"artifact": "corner_recomputed", "path": rel(CORNER_RECOMPUTED), "use": "centerline tap-length K recomputation"},
        {"artifact": "pressure_branch_admission", "path": rel(PRESSURE_BRANCH_ADMISSION), "use": "recirculation and pressure-definition gates"},
        {"artifact": "pressure_stations", "path": rel(PRESSURE_STATIONS), "use": "val_salt2 streamwise pressure map"},
    ]
    write_csv(OUT / "source_manifest.csv", source_manifest)

    max_residual = max(abs(fnum(row["latest_residual_patch_minus_ledger_w"])) for row in section_rows)
    junction_total = next(row for row in junction_rows if row["physical_junction_bucket"] == "case_total_check")
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "val_patch_rows": len(patch_rows),
        "val_junction_patch_rows": sum(1 for row in patch_rows if row["section_key"] == "junctions"),
        "val_junction_loss_positive_W": fnum(junction_total["realized_external_loss_positive_W"]),
        "max_section_latest_residual_W": max_residual,
        "val_training_policy": "external_test_only_training_quality_artifact_not_training_input",
        "corner_rows": len(corner_rows),
        "corner_fit_admitted_rows": sum(row["fit_admitted"] == "yes" for row in corner_rows),
        "corner_centerline_negative_k_rows": sum(fnum(row["K_local_centerline"], 1.0) < 0 for row in corner_rows),
        "pressure_ladder_duplicate_jobs_submitted": "no",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
