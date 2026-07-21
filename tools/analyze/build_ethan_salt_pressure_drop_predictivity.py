#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import (
    csv_dump_rows,
    finite_float,
    load_csv_rows,
    write_json,
)
from tools.common import ensure_dir, iso_timestamp

DEFAULT_FROZEN_DIR = ROOT / "reports" / "2026-06" / "2026-06-22" / "2026-06-22_ethan_frozen_state_results"
DEFAULT_HYDRO_PROBE_DIR = ROOT / "reports" / "2026-06" / "2026-06-22" / "2026-06-22_ethan_feature_path_hydro_probe"
DEFAULT_WORK_PRODUCT_DIR = ROOT / "work_products" / "2026-06-29_ethan_salt_pressure_drop_predictivity"
DEFAULT_REPORT_DIR = ROOT / "reports" / "2026-06" / "2026-06-29" / "2026-06-29_ethan_salt_pressure_drop_predictivity"
DEFAULT_IMPORT_MANIFEST_PATH = ROOT / "imports" / "2026-06-29_ethan_salt_pressure_drop_predictivity.json"

SENSOR_PATTERN = re.compile(r"^(TP|TW)(\d+)$")
CASE_FAMILY_PATTERN = re.compile(r"^(Salt \d+)")

LOCAL_REPLAY_ATTEMPTS = (
    ("major_only_baseline", "major_total_resistance_pa_s_kg", "Hydraulic-only replay using major-span CFD resistance only."),
    (
        "major_plus_feature_endpoint_baseline",
        "feature_endpoint_total_resistance_pa_s_kg",
        "Add endpoint-to-endpoint connector losses from the frozen CFD reduction.",
    ),
    (
        "major_plus_feature_probe_baseline",
        "feature_probe_total_resistance_pa_s_kg",
        "Use the best available feature-path hydro probe where available.",
    ),
    (
        "major_plus_feature_probe_external_losses",
        "feature_probe_total_resistance_pa_s_kg",
        "Same hydraulic replay as the probe attempt; thermal corrections enter only in the true 1D lane.",
    ),
    (
        "major_plus_feature_probe_hybrid_external",
        "feature_probe_total_resistance_pa_s_kg",
        "Same hydraulic replay as the probe attempt; hybrid thermal corrections enter only in the true 1D lane.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the additive Salt pressure-drop predictivity package: a 9-case CFD pressure budget, "
            "sensor reference table, and a lightweight hydraulic local replay surface."
        )
    )
    parser.add_argument("--frozen-dir", default=str(DEFAULT_FROZEN_DIR))
    parser.add_argument("--hydro-probe-dir", default=str(DEFAULT_HYDRO_PROBE_DIR))
    parser.add_argument("--work-product-dir", default=str(DEFAULT_WORK_PRODUCT_DIR))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_MANIFEST_PATH))
    return parser.parse_args()


def case_family_from_label(label: str) -> str:
    match = CASE_FAMILY_PATTERN.match(label.strip())
    if not match:
        return label.strip()
    return match.group(1)


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_rmse(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(math.sqrt(sum(value * value for value in payload) / len(payload)))


def sensor_sort_key(label: str) -> tuple[str, int]:
    match = SENSOR_PATTERN.match(label)
    if not match:
        return (label, 0)
    return (match.group(1), int(match.group(2)))


def load_frozen_contract_rows(frozen_dir: Path) -> list[dict[str, str]]:
    rows = load_csv_rows(frozen_dir / "frozen_state_contract.csv")
    return [row for row in rows if row.get("case_label", "").startswith("Salt ")]


def load_probe_lookup(probe_dir: Path) -> dict[tuple[str, str], dict[str, str]]:
    rows = load_csv_rows(probe_dir / "feature_path_hydro_probe_case_summary.csv")
    return {
        (row["source_id"], row["feature_name"]): row
        for row in rows
    }


def build_sensor_reference_rows(
    *,
    source_id: str,
    case_label: str,
    boundary_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in boundary_rows:
        label = str(row.get("landmark_label", "")).strip()
        if not SENSOR_PATTERN.match(label):
            continue
        grouped.setdefault(label, []).append(row)
    sensor_rows: list[dict[str, Any]] = []
    for label in sorted(grouped.keys(), key=sensor_sort_key):
        payload = grouped[label]
        kind = "TP" if label.startswith("TP") else "TW"
        ref_field = "t_core_k" if kind == "TP" else "t_wall_area_avg_k"
        ref_values = [finite_float(row.get(ref_field)) for row in payload]
        sensor_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "case_family": case_family_from_label(case_label),
                "sensor": label,
                "kind": kind,
                "reference_k": safe_mean(ref_values),
                "bulk_proxy_k": safe_mean([finite_float(row.get("bulk_temp_fluid_area_avg_k")) for row in payload]),
                "wall_proxy_k": safe_mean([finite_float(row.get("t_wall_area_avg_k")) for row in payload]),
                "time_sample_count": len(payload),
                "reference_source_field": ref_field,
            }
        )
    return sensor_rows


def frozen_case_mdot(branch_rows: list[dict[str, str]]) -> float:
    preferred = [row for row in branch_rows if row.get("branch_name") == "lower_leg"]
    source_rows = preferred if preferred else branch_rows
    values = [finite_float(row.get("mean_mdot_mean_abs_kg_s")) for row in source_rows]
    return safe_mean(values)


def resistance_from_drop(dp_pa: float, mdot_kg_s: float) -> float:
    if not math.isfinite(dp_pa) or not math.isfinite(mdot_kg_s) or abs(mdot_kg_s) <= 0.0:
        return math.nan
    return float(dp_pa / mdot_kg_s)


def sort_element_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    major_order = [
        "left_lower_leg",
        "corner_lower_left",
        "lower_leg",
        "corner_lower_right",
        "right_leg",
        "corner_upper_right",
        "upper_leg",
        "corner_upper_left",
        "left_upper_leg",
        "test_section_complex",
        "test_section_span",
    ]
    order_lookup = {name: index for index, name in enumerate(major_order)}
    rows.sort(key=lambda row: (order_lookup.get(str(row["element_name"]), 999), str(row["element_name"])))
    for index, row in enumerate(rows):
        row["element_order_index"] = index
    return rows


def union_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames


def build_case_tables(
    contract_row: dict[str, str],
    probe_lookup: dict[tuple[str, str], dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    package_root = Path(contract_row["package_root"])
    source_id = contract_row["source_id"]
    case_label = contract_row["case_label"]
    case_family = case_family_from_label(case_label)

    major_rows = load_csv_rows(package_root / "major_loss_summary.csv")
    feature_rows = load_csv_rows(package_root / "feature_minor_loss_summary.csv")
    branch_rows = load_csv_rows(package_root / "branch_thermal_summary.csv")
    boundary_rows = load_csv_rows(package_root / "boundary_layer_landmark_summary.csv")
    heat_rows = load_csv_rows(package_root / "heat_loss_summary.csv")

    cfd_mdot = frozen_case_mdot(branch_rows)
    heat_row = heat_rows[0] if heat_rows else {}
    element_rows: list[dict[str, Any]] = []

    major_total_dp = 0.0
    major_total_r = 0.0
    for row in major_rows:
        dp_pa = abs(finite_float(row.get("mean_terminal_dp_major_direct_prgh_pa")))
        resistance_pa_s_kg = abs(finite_float(row.get("mean_momentum_resistance_direct_prgh_pa_s_kg_m")))
        major_total_dp += dp_pa if math.isfinite(dp_pa) else 0.0
        major_total_r += resistance_pa_s_kg if math.isfinite(resistance_pa_s_kg) else 0.0
        element_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "case_family": case_family,
                "element_name": row["span_name"],
                "element_kind": "major_span",
                "measurement_kind": "direct_prgh_terminal",
                "dp_pa": dp_pa,
                "resistance_pa_s_kg": resistance_pa_s_kg,
                "reference_length_m": finite_float(row.get("reference_length_m")),
                "start_patch": row.get("start_patch", ""),
                "end_patch": row.get("end_patch", ""),
                "adjacent_major_spans": row.get("span_name", ""),
                "package_root": str(package_root),
            }
        )

    feature_endpoint_total_dp = 0.0
    feature_endpoint_total_r = 0.0
    feature_probe_total_dp = 0.0
    feature_probe_total_r = 0.0
    best_available_feature_dp = 0.0
    best_available_feature_r = 0.0
    for row in feature_rows:
        feature_name = row["feature_name"]
        endpoint_dp = abs(finite_float(row.get("mean_abs_delta_p_rgh_pa")))
        endpoint_r = resistance_from_drop(endpoint_dp, cfd_mdot)
        feature_endpoint_total_dp += endpoint_dp if math.isfinite(endpoint_dp) else 0.0
        feature_endpoint_total_r += endpoint_r if math.isfinite(endpoint_r) else 0.0

        probe_row = probe_lookup.get((source_id, feature_name))
        probe_dp = math.nan
        probe_r = math.nan
        probe_status = "missing_probe"
        if probe_row is not None:
            probe_dp = abs(finite_float(probe_row.get("mean_window_hydro_correction_abs_pa")))
            probe_r = resistance_from_drop(probe_dp, cfd_mdot)
            probe_status = probe_row.get("status", "")
        chosen_dp = probe_dp if math.isfinite(probe_dp) else endpoint_dp
        chosen_r = probe_r if math.isfinite(probe_r) else endpoint_r
        feature_probe_total_dp += (probe_dp if math.isfinite(probe_dp) else 0.0)
        feature_probe_total_r += (probe_r if math.isfinite(probe_r) else 0.0)
        best_available_feature_dp += chosen_dp if math.isfinite(chosen_dp) else 0.0
        best_available_feature_r += chosen_r if math.isfinite(chosen_r) else 0.0
        element_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "case_family": case_family,
                "element_name": feature_name,
                "element_kind": "minor_feature",
                "measurement_kind": "feature_endpoint_or_probe",
                "dp_pa": chosen_dp,
                "resistance_pa_s_kg": chosen_r,
                "reference_length_m": finite_float(row.get("reference_length_m")),
                "start_patch": row.get("start_patch", ""),
                "end_patch": row.get("end_patch", ""),
                "adjacent_major_spans": probe_row.get("adjacent_major_spans", "") if probe_row else "",
                "package_root": str(package_root),
                "feature_endpoint_dp_pa": endpoint_dp,
                "feature_endpoint_resistance_pa_s_kg": endpoint_r,
                "feature_probe_dp_pa": probe_dp,
                "feature_probe_resistance_pa_s_kg": probe_r,
                "feature_probe_status": probe_status,
            }
        )

    sort_element_rows(element_rows)
    summary_row = {
        "source_id": source_id,
        "case_label": case_label,
        "case_family": case_family,
        "fluid_case_name": case_family,
        "run_status": contract_row.get("run_status", ""),
        "comparison_ready": contract_row.get("comparison_ready", ""),
        "package_root": str(package_root),
        "late_window_time_start_s": finite_float(contract_row.get("late_window_time_start_s")),
        "late_window_time_end_s": finite_float(contract_row.get("late_window_time_end_s")),
        "late_window_time_count": finite_float(contract_row.get("late_window_time_count")),
        "cfd_mdot_kg_s": cfd_mdot,
        "cfd_qambient_w": finite_float(heat_row.get("ambient_proxy_w")),
        "cfd_qremoved_w": finite_float(heat_row.get("cooling_branch_total_removal_w")),
        "cfd_qheater_w": finite_float(heat_row.get("section_heater_net_q_w")),
        "major_element_count": sum(1 for row in element_rows if row["element_kind"] == "major_span"),
        "feature_element_count": sum(1 for row in element_rows if row["element_kind"] == "minor_feature"),
        "major_total_dp_pa": major_total_dp,
        "major_total_resistance_pa_s_kg": major_total_r,
        "feature_endpoint_total_dp_pa": feature_endpoint_total_dp,
        "feature_endpoint_total_resistance_pa_s_kg": feature_endpoint_total_r,
        "feature_probe_total_dp_pa": feature_probe_total_dp,
        "feature_probe_total_resistance_pa_s_kg": feature_probe_total_r,
        "best_available_feature_dp_pa": best_available_feature_dp,
        "best_available_feature_resistance_pa_s_kg": best_available_feature_r,
        "best_available_total_dp_pa": major_total_dp + best_available_feature_dp,
        "best_available_total_resistance_pa_s_kg": major_total_r + best_available_feature_r,
        "probe_feature_count": sum(
            1
            for row in element_rows
            if row["element_kind"] == "minor_feature" and math.isfinite(finite_float(row.get("feature_probe_dp_pa")))
        ),
    }
    sensor_rows = build_sensor_reference_rows(source_id=source_id, case_label=case_label, boundary_rows=boundary_rows)
    return element_rows, summary_row, sensor_rows


def local_replay_row(summary_row: dict[str, Any], attempt_name: str, resistance_field: str, note: str) -> dict[str, Any]:
    cfd_drive_pa = finite_float(summary_row.get("best_available_total_dp_pa"))
    cfd_mdot = finite_float(summary_row.get("cfd_mdot_kg_s"))
    total_resistance = finite_float(summary_row.get("major_total_resistance_pa_s_kg")) + finite_float(summary_row.get(resistance_field))
    if resistance_field == "major_total_resistance_pa_s_kg":
        total_resistance = finite_float(summary_row.get("major_total_resistance_pa_s_kg"))
    predicted_mdot = math.nan
    if math.isfinite(cfd_drive_pa) and math.isfinite(total_resistance) and total_resistance > 0.0:
        predicted_mdot = float(cfd_drive_pa / total_resistance)
    error_kg_s = abs(predicted_mdot - cfd_mdot) if math.isfinite(predicted_mdot) and math.isfinite(cfd_mdot) else math.nan
    error_pct = (
        100.0 * (predicted_mdot - cfd_mdot) / cfd_mdot
        if math.isfinite(predicted_mdot) and math.isfinite(cfd_mdot) and cfd_mdot != 0.0
        else math.nan
    )
    return {
        "source_id": summary_row["source_id"],
        "case_label": summary_row["case_label"],
        "case_family": summary_row["case_family"],
        "attempt_name": attempt_name,
        "cfd_drive_pa": cfd_drive_pa,
        "total_resistance_pa_s_kg": total_resistance,
        "predicted_mdot_kg_s": predicted_mdot,
        "cfd_mdot_kg_s": cfd_mdot,
        "mdot_abs_error_kg_s": error_kg_s,
        "mdot_relative_error_pct": error_pct,
        "note": note,
    }


def build_local_replay_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary_row in summary_rows:
        for attempt_name, resistance_field, note in LOCAL_REPLAY_ATTEMPTS:
            rows.append(local_replay_row(summary_row, attempt_name, resistance_field, note))
    return rows


def replay_summary_rows(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in replay_rows:
        grouped.setdefault(row["attempt_name"], []).append(row)
    payload: list[dict[str, Any]] = []
    for attempt_name, rows in grouped.items():
        mdot_errors = [finite_float(row["mdot_abs_error_kg_s"]) for row in rows]
        payload.append(
            {
                "attempt_name": attempt_name,
                "case_count": len(rows),
                "mean_mdot_abs_error_kg_s": safe_mean(mdot_errors),
                "rmse_mdot_abs_error_kg_s": safe_rmse(mdot_errors),
            }
        )
    payload.sort(key=lambda row: (finite_float(row["mean_mdot_abs_error_kg_s"]), row["attempt_name"]))
    return payload


def write_readme(
    path: Path,
    *,
    summary_rows: list[dict[str, Any]],
    replay_summary: list[dict[str, Any]],
) -> None:
    best_attempt = replay_summary[0]["attempt_name"] if replay_summary else "none"
    lines = [
        "# Ethan Salt Pressure-Drop Predictivity",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Scope",
        "",
        "- Salt-only additive package covering all 9 June 22 frozen-state references.",
        "- Publishes a defended 3D pressure-budget summary built from the preserved case-analysis products.",
        "- Publishes a local hydraulic replay table that holds the CFD pressure-drive fixed and asks how much mdot error remains under several reduced pressure-drop contracts.",
        "",
        "## Output tables",
        "",
        "- `cfd_pressure_budget_elements.csv`: one ordered hydraulic element table per frozen Salt reference.",
        "- `cfd_pressure_budget_summary.csv`: one frozen-reference contract row with major/feature totals and reduced hydraulic resistances.",
        "- `cfd_sensor_reference.csv`: CFD TP/TW references for downstream 1D-vs-CFD scoring.",
        "- `local_hydraulic_replay.csv`: local mdot replay rows for the five named attempts.",
        "- `local_hydraulic_replay_summary.csv`: attempt-level mdot replay summary.",
        "",
        "## Notes",
        "",
        f"- Best hydraulic-only local replay by mean |mdot| error: `{best_attempt}`.",
        "- Attempts 4 and 5 intentionally share the same local hydraulic replay as attempt 3; their thermal distinctions only appear in the true 1D study lane.",
        f"- Case count: `{len(summary_rows)}`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    frozen_dir = Path(args.frozen_dir)
    hydro_probe_dir = Path(args.hydro_probe_dir)
    work_product_dir = Path(args.work_product_dir)
    report_dir = Path(args.report_dir)
    import_manifest_path = Path(args.import_manifest_path)

    ensure_dir(work_product_dir)
    ensure_dir(report_dir)
    ensure_dir(import_manifest_path.parent)

    contract_rows = load_frozen_contract_rows(frozen_dir)
    probe_lookup = load_probe_lookup(hydro_probe_dir)

    element_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    sensor_rows: list[dict[str, Any]] = []
    for contract_row in contract_rows:
        case_element_rows, case_summary_row, case_sensor_rows = build_case_tables(contract_row, probe_lookup)
        element_rows.extend(case_element_rows)
        summary_rows.append(case_summary_row)
        sensor_rows.extend(case_sensor_rows)
    summary_rows.sort(key=lambda row: (row["case_family"], row["source_id"]))
    replay_rows = build_local_replay_rows(summary_rows)
    replay_summary = replay_summary_rows(replay_rows)

    element_fieldnames = union_fieldnames(element_rows)
    csv_dump_rows(work_product_dir / "cfd_pressure_budget_elements.csv", element_rows, fieldnames=element_fieldnames)
    csv_dump_rows(work_product_dir / "cfd_pressure_budget_summary.csv", summary_rows)
    csv_dump_rows(work_product_dir / "cfd_sensor_reference.csv", sensor_rows)
    csv_dump_rows(work_product_dir / "local_hydraulic_replay.csv", replay_rows)
    csv_dump_rows(work_product_dir / "local_hydraulic_replay_summary.csv", replay_summary)

    csv_dump_rows(report_dir / "cfd_pressure_budget_elements.csv", element_rows, fieldnames=element_fieldnames)
    csv_dump_rows(report_dir / "cfd_pressure_budget_summary.csv", summary_rows)
    csv_dump_rows(report_dir / "cfd_sensor_reference.csv", sensor_rows)
    csv_dump_rows(report_dir / "local_hydraulic_replay.csv", replay_rows)
    csv_dump_rows(report_dir / "local_hydraulic_replay_summary.csv", replay_summary)
    write_readme(report_dir / "README.md", summary_rows=summary_rows, replay_summary=replay_summary)

    payload = {
        "generated_at": iso_timestamp(),
        "frozen_dir": str(frozen_dir),
        "hydro_probe_dir": str(hydro_probe_dir),
        "summary_row_count": len(summary_rows),
        "element_row_count": len(element_rows),
        "sensor_row_count": len(sensor_rows),
        "replay_row_count": len(replay_rows),
        "best_local_replay_attempt": replay_summary[0]["attempt_name"] if replay_summary else "",
    }
    write_json(report_dir / "summary.json", payload)
    write_json(work_product_dir / "summary.json", payload)
    write_json(
        import_manifest_path,
        {
            "generated_at": iso_timestamp(),
            "script_path": str(Path(__file__).resolve()),
            "inputs": {
                "frozen_dir": str(frozen_dir),
                "hydro_probe_dir": str(hydro_probe_dir),
            },
            "outputs": {
                "work_product_dir": str(work_product_dir),
                "report_dir": str(report_dir),
            },
        },
    )


if __name__ == "__main__":
    main()
