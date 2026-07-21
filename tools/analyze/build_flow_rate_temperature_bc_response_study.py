#!/usr/bin/env python3
"""Build a flow-rate/temperature/boundary-condition response study."""
from __future__ import annotations

import csv
import html
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-351"
PAPER_TASK = "AGENT-359"
DATE = "2026-07-14"
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study"

CASE_METADATA = ROOT / "reports/2026-06/2026-06-02/2026-06-02_ethan_case_metadata_index/ethan_case_metadata_index.csv"
STEADY_SUMMARY = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv"
TIME_CASE_INVENTORY = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/case_inventory.csv"
PATCH_ROLE_TABLE = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
PATCH_ROLE_SUMMARY = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
SUBMITTED_STEADY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv"
SUBMITTED_COMPACT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_compact_lineage_table.csv"
SALT_INVENTORY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv"
TRIAGE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/steady_candidate_admission_triage.csv"
CORRECTED_HARVEST_3295437 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/corrected_q_harvest_3295437_processing_status.csv"
PM5_SPLIT_ADMISSION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv"
PM5_HEAT_ROLE_REDUCTION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_heat_role_reduction.csv"
PM5_FORWARD_GATE_QUEUE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_forward_gate_queue.csv"
HIINS_LOINS_REVIEW = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/hiins_loins_construction_review.csv"
T2_NOTE = ROOT / ".agent/journal/2026-07-01/T2-truesteady-insulation-runs.md"
T3_NOTE = ROOT / ".agent/journal/2026-07-01/T3-perturbation-requalification.md"
THERMAL_BOUNDARY_MAP = ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"

FIGURES = [
    "mdot_vs_probe_temperature.svg",
    "mdot_vs_initial_temperature.svg",
    "mdot_vs_heater_power.svg",
    "mdot_vs_cooler_power.svg",
    "mdot_vs_area_weighted_external_h.svg",
    "q_perturbation_expected_vs_observed_mdot_move.svg",
    "bc_role_heat_breakdown_by_case.svg",
]

FALSE_STEADY_Q_ROWS = [
    ("salt2_jin_hiq_hiins", "1.10", "-0.011", "3.23", "false_steady"),
    ("salt2_jin_loq_loins", "0.90", "-0.004", "3.45", "false_steady"),
    ("salt3_jin_hiq_hiins", "1.10", "+0.084", "3.23", "false_steady"),
    ("salt3_jin_loq_loins", "0.90", "+0.095", "3.45", "false_steady"),
    ("salt4_jin_hiq_hiins", "1.10", "+0.023", "3.23", "false_steady"),
    ("salt4_jin_loq_loins", "0.90", "+0.086", "3.45", "false_steady"),
    ("salt2_jin_hi5q_balq", "1.05", "+0.098", "1.64", "false_steady"),
    ("salt2_jin_lo5q_balq", "0.95", "+0.097", "1.70", "false_steady"),
    ("salt3_jin_hi5q_balq", "1.05", "+0.200", "1.64", "false_steady"),
    ("salt3_jin_lo5q_balq", "0.95", "+0.182", "1.70", "false_steady"),
    ("salt4_jin_hi5q_balq", "1.05", "+0.035", "1.64", "false_steady"),
    ("salt4_jin_lo5q_balq", "0.95", "+0.070", "1.70", "false_steady"),
    ("salt1_jin_hiq_balq", "1.10", "+0.283", "3.23", "false_steady"),
    ("salt1_jin_loq_balq", "0.90", "+0.283", "3.45", "false_steady"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(path)


def f(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "None", "nan", "NaN", "--"}:
        return None
    try:
        parsed = float(text.replace("+", ""))
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, digits: int = 6) -> str:
    parsed = f(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def mean(values: Iterable[float | None]) -> float | None:
    valid = [v for v in values if v is not None and math.isfinite(v)]
    return sum(valid) / len(valid) if valid else None


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    sx = math.sqrt(sum((x - xbar) ** 2 for x in xs))
    sy = math.sqrt(sum((y - ybar) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / (sx * sy)


def linear_fit(xs: list[float], ys: list[float]) -> dict[str, float | None]:
    if len(xs) < 2 or len(xs) != len(ys):
        return {"slope": None, "intercept": None, "r": None, "r_squared": None}
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    sxx = sum((x - xbar) ** 2 for x in xs)
    if sxx == 0:
        return {"slope": None, "intercept": None, "r": None, "r_squared": None}
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sxx
    intercept = ybar - slope * xbar
    r = pearson(xs, ys)
    return {
        "slope": slope,
        "intercept": intercept,
        "r": r,
        "r_squared": r * r if r is not None else None,
    }


def pm5_tables() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_case = {row["case_key"]: row for row in read_csv(PM5_SPLIT_ADMISSION)}
    by_source = {row["source_case_key"]: row for row in by_case.values() if row.get("source_case_key")}
    heat_by_case = {row["case_key"]: row for row in read_csv(PM5_HEAT_ROLE_REDUCTION)}
    return by_case, by_source, heat_by_case


def slug_parts(slug: str) -> list[str]:
    return slug.split("__")


def source_id_from_slug(slug: str) -> str:
    parts = slug_parts(slug)
    return parts[-1] if parts else slug


def case_key_from_slug(slug: str) -> str:
    parts = slug_parts(slug)
    for part in reversed(parts[:-1]):
        if part.startswith(("salt", "water", "val_")):
            return part
    return source_id_from_slug(slug)


def base_source_from_key(case_key: str) -> str:
    if case_key.startswith("salt") and "_jin" in case_key:
        salt_num = case_key.split("_", 1)[0].replace("salt", "")
        return f"viscosity_screening_salt_test_{salt_num}_jin_coarse_mesh"
    if case_key.startswith("salt") and "_kirst" in case_key:
        salt_num = case_key.split("_", 1)[0].replace("salt", "")
        return f"viscosity_screening_salt_test_{salt_num}_kirst_coarse_mesh"
    return case_key


def aggregate_timeseries() -> dict[str, dict[str, Any]]:
    rows = read_csv(STEADY_SUMMARY)
    by_slug: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_slug[row["case_slug"]].append(row)

    case_inv = {row["slug"]: row for row in read_csv(TIME_CASE_INVENTORY) if not row.get("duplicate_of")}
    out: dict[str, dict[str, Any]] = {}
    for slug, inv in case_inv.items():
        series = by_slug.get(slug, [])
        mdot_rows = [r for r in series if r["group"] == "mdot"]
        temp_rows = [r for r in series if r["group"] == "temperature"]
        wall_rows = [r for r in series if r["group"] == "wall_temperature"]
        heat_rows = [r for r in series if r["group"] == "heat"]
        verdicts = {r["verdict"] for r in mdot_rows + temp_rows + wall_rows + heat_rows if r.get("verdict")}
        key = case_key_from_slug(slug)
        out[key] = {
            "case_slug": slug,
            "case_key": key,
            "source_id": source_id_from_slug(slug),
            "fluid": inv.get("fluid", ""),
            "postprocessing": inv.get("postprocessing", ""),
            "mdot_mean_abs_kg_s": mean(abs(f(r.get("osc_mean")) or 0.0) for r in mdot_rows) if mdot_rows else None,
            "mdot_monitor_count": str(len(mdot_rows)),
            "timeseries_probe_T_avg_K": mean(f(r.get("osc_mean")) for r in temp_rows),
            "timeseries_probe_T_min_K": min([v for v in (f(r.get("osc_mean")) for r in temp_rows) if v is not None], default=None),
            "timeseries_probe_T_max_K": max([v for v in (f(r.get("osc_mean")) for r in temp_rows) if v is not None], default=None),
            "timeseries_wall_T_avg_K": mean(f(r.get("osc_mean")) for r in wall_rows),
            "timeseries_heat_net_W": mean(f(r.get("osc_mean")) for r in heat_rows),
            "timeseries_verdict": "mixed:" + ";".join(sorted(verdicts)) if len(verdicts) > 1 else next(iter(verdicts), ""),
            "timeseries_source": rel(STEADY_SUMMARY),
        }
    return out


def metadata_by_source() -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in read_csv(CASE_METADATA)}


def patch_role_reductions() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    patch_rows = read_csv(PATCH_ROLE_TABLE)
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in patch_rows:
        key = (row["source_id"], row["case_id"], row["role"])
        g = grouped.setdefault(
            key,
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "role": row["role"],
                "role_group": row["role_group"],
                "patch_count": 0,
                "area_m2": 0.0,
                "imposed_Q_W": 0.0,
                "realized_wallHeatFlux_W": 0.0,
                "rcExternalTemperature_count": 0,
                "externalTemperature_count": 0,
                "zeroGradient_count": 0,
                "area_h_num": 0.0,
                "area_Ta_num": 0.0,
                "area_Tsur_num": 0.0,
                "area_emissivity_num": 0.0,
                "area_h_den": 0.0,
                "area_Ta_den": 0.0,
                "area_Tsur_den": 0.0,
                "area_emissivity_den": 0.0,
            },
        )
        area = f(row.get("area_m2")) or 0.0
        g["patch_count"] += 1
        g["area_m2"] += area
        g["imposed_Q_W"] += f(row.get("imposed_Q_W")) or 0.0
        g["realized_wallHeatFlux_W"] += f(row.get("realized_wallHeatFlux_W")) or 0.0
        if row.get("bc_type") == "rcExternalTemperature":
            g["rcExternalTemperature_count"] += 1
        elif row.get("bc_type") == "externalTemperature":
            g["externalTemperature_count"] += 1
        elif row.get("bc_type") == "zeroGradient":
            g["zeroGradient_count"] += 1
        for field, num, den in [
            ("h_W_m2K", "area_h_num", "area_h_den"),
            ("Ta_K", "area_Ta_num", "area_Ta_den"),
            ("Tsur_K", "area_Tsur_num", "area_Tsur_den"),
            ("emissivity", "area_emissivity_num", "area_emissivity_den"),
        ]:
            val = f(row.get(field))
            if val is not None and area > 0:
                g[num] += val * area
                g[den] += area

    role_rows: list[dict[str, Any]] = []
    by_source: dict[str, dict[str, Any]] = defaultdict(dict)
    for g in grouped.values():
        row = {
            "source_id": g["source_id"],
            "case_id": g["case_id"],
            "role": g["role"],
            "role_group": g["role_group"],
            "patch_count": g["patch_count"],
            "area_m2": fmt(g["area_m2"], 9),
            "imposed_Q_W": fmt(g["imposed_Q_W"], 6),
            "realized_wallHeatFlux_W": fmt(g["realized_wallHeatFlux_W"], 6),
            "rcExternalTemperature_count": g["rcExternalTemperature_count"],
            "externalTemperature_count": g["externalTemperature_count"],
            "zeroGradient_count": g["zeroGradient_count"],
            "area_weighted_h_W_m2K": fmt(g["area_h_num"] / g["area_h_den"] if g["area_h_den"] else None, 6),
            "area_weighted_Ta_K": fmt(g["area_Ta_num"] / g["area_Ta_den"] if g["area_Ta_den"] else None, 6),
            "area_weighted_Tsur_K": fmt(g["area_Tsur_num"] / g["area_Tsur_den"] if g["area_Tsur_den"] else None, 6),
            "area_weighted_emissivity": fmt(g["area_emissivity_num"] / g["area_emissivity_den"] if g["area_emissivity_den"] else None, 6),
            "source_table": rel(PATCH_ROLE_TABLE),
        }
        role_rows.append(row)
        by_source[row["source_id"]][row["role"]] = row
    return sorted(role_rows, key=lambda r: (r["source_id"], r["role"])), by_source


def load_status_tables() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    triage = {row["case_key"]: row for row in read_csv(TRIAGE)}
    submitted: dict[str, dict[str, str]] = {}
    for row in read_csv(SUBMITTED_COMPACT) or read_csv(SUBMITTED_STEADY):
        key = row.get("run_key") or row.get("latest_run_key") or row.get("lineage_group", "")
        if key:
            submitted[key] = row
    harvest = {row["case_key"]: row for row in read_csv(CORRECTED_HARVEST_3295437)}
    pm5_by_case, pm5_by_source, pm5_heat_by_case = pm5_tables()
    return triage, submitted, harvest, pm5_by_case, pm5_by_source, pm5_heat_by_case


def classify(
    case_key: str,
    source_id: str,
    triage: dict[str, dict[str, str]],
    harvest: dict[str, dict[str, str]],
    pm5_by_case: dict[str, dict[str, str]] | None = None,
    pm5_by_source: dict[str, dict[str, str]] | None = None,
) -> tuple[str, str, str]:
    pm5_by_case = pm5_by_case or {}
    pm5_by_source = pm5_by_source or {}
    false_keys = {row[0] for row in FALSE_STEADY_Q_ROWS}
    if case_key in false_keys:
        return "invalid_false_steady", "old Q perturbation failed operating-point movement gate", rel(T3_NOTE)
    if case_key in pm5_by_case or source_id in pm5_by_source or case_key in pm5_by_source:
        pm5 = pm5_by_case.get(case_key) or pm5_by_source.get(source_id) or pm5_by_source.get(case_key) or {}
        return "terminal_harvested_split_pending", pm5.get("current_allowed_use", "terminal corrected-Q sensitivity evidence; split-policy pending"), rel(PM5_SPLIT_ADMISSION)
    if case_key in harvest:
        h = harvest[case_key]
        if h.get("closure_fit_admissible_in_terminal_gate") == "yes":
            return "terminal_harvested_split_pending", "terminal corrected-Q harvest passed but split/BC-role refresh is still required", rel(CORRECTED_HARVEST_3295437)
        return "pending_terminal_admission", "corrected-Q terminal/admission evidence incomplete", rel(CORRECTED_HARVEST_3295437)
    if case_key in triage:
        verdict = triage[case_key].get("current_admission_or_split_verdict", "")
        if verdict in {"training", "validation", "holdout"}:
            return "admitted_or_usable", verdict, rel(TRIAGE)
        if verdict == "diagnostic-only":
            return "diagnostic", triage[case_key].get("why_not_admitted_as_training_now", "diagnostic-only"), rel(TRIAGE)
        if verdict in {"not-admissible", "excluded"}:
            return "invalid_or_rejected", triage[case_key].get("why_not_admitted_as_training_now", "not-admissible"), rel(TRIAGE)
        if "pending" in verdict:
            return "pending_terminal_admission", verdict, rel(TRIAGE)
    if case_key in {"salt2_jin", "salt3_jin", "salt4_jin"}:
        split = {"salt2_jin": "training", "salt3_jin": "validation", "salt4_jin": "holdout"}[case_key]
        return "admitted_or_usable", split, "mainline split policy from current inventory"
    if "kirst" in case_key or "kirst" in source_id:
        return "diagnostic", "Kirst rows are historical/context unless explicitly re-admitted", "AGENTS.md repo-specific operating rules"
    if case_key.startswith("salt1"):
        return "diagnostic", "Salt1 remains context-only pending Salt1 policy/admission", rel(TRIAGE)
    if case_key.startswith("water"):
        return "diagnostic", "water rows are outside this salt-focused flow/BC response fit scope", rel(CASE_METADATA)
    return "diagnostic", "context row; not current admitted split evidence", rel(CASE_METADATA)


def role_value(roles: dict[str, Any], role: str, field: str) -> str:
    return str(roles.get(role, {}).get(field, ""))


def weighted_external_h(roles: dict[str, Any]) -> str:
    nums = []
    dens = []
    for role in ["ambient_wall", "heater", "test_section", "junction_other"]:
        r = roles.get(role)
        if not r:
            continue
        h = f(r.get("area_weighted_h_W_m2K"))
        area = f(r.get("area_m2"))
        if h is not None and area is not None:
            nums.append(h * area)
            dens.append(area)
    return fmt(sum(nums) / sum(dens) if dens and sum(dens) else None, 6)


def apply_pm5_overlay(
    matrix: dict[str, dict[str, Any]],
    pm5_by_case: dict[str, dict[str, str]],
    pm5_by_source: dict[str, dict[str, str]],
    pm5_heat_by_case: dict[str, dict[str, str]],
) -> None:
    for canonical_key, pm5 in pm5_by_case.items():
        source_key = pm5.get("source_case_key", "")
        base = dict(matrix.get(source_key) or matrix.get(canonical_key) or {})
        if not base:
            base = {
                "case_key": canonical_key,
                "source_id": source_key or canonical_key,
                "missing_result_reason": "no time-series row available before corrected-Q overlay",
                "evidence_paths": "",
            }
        base["case_key"] = canonical_key
        base["source_case_key"] = source_key
        base["canonical_case_key"] = canonical_key
        base["source_id"] = source_key or base.get("source_id", canonical_key)
        base["evidence_class"] = "terminal_harvested_split_pending"
        base["split_or_use_status"] = pm5.get("current_allowed_use", "")
        base["current_split_family"] = pm5.get("current_split_family", "")
        base["q_ratio"] = pm5.get("q_ratio", "")
        base["terminal_harvest_state"] = pm5.get("terminal_harvest_state", "")
        base["closure_fit_admissible_terminal_gate"] = pm5.get("closure_fit_admissible_terminal_gate", "")
        base["can_expand_training_now"] = pm5.get("can_expand_training_now", "")
        base["can_score_validation_now"] = pm5.get("can_score_validation_now", "")
        base["can_score_holdout_now"] = pm5.get("can_score_holdout_now", "")
        base["blocked_use"] = pm5.get("blocked_use", "")
        base["next_required_gate"] = pm5.get("next_required_gate", "")
        heat = pm5_heat_by_case.get(canonical_key, {})
        for source_field, out_field in [
            ("final_window_start_s", "pm5_final_window_start_s"),
            ("final_window_end_s", "pm5_final_window_end_s"),
            ("final_window_row_count", "pm5_final_window_row_count"),
            ("total_Q_postProc_mean_W", "pm5_total_Q_postProc_mean_W"),
            ("ambient_proxy_mean_W", "pm5_ambient_proxy_mean_W"),
            ("cooling_branch_total_removal_mean_W", "pm5_cooling_branch_total_removal_mean_W"),
            ("section_heater_net_q_mean_W", "pm5_section_heater_net_q_mean_W"),
            ("section_test_section_net_q_mean_W", "pm5_section_test_section_net_q_mean_W"),
            ("section_cooling_branch_net_q_mean_W", "pm5_section_cooling_branch_net_q_mean_W"),
            ("section_downcomer_net_q_mean_W", "pm5_section_downcomer_net_q_mean_W"),
            ("section_upcomer_net_q_mean_W", "pm5_section_upcomer_net_q_mean_W"),
            ("section_junctions_net_q_mean_W", "pm5_section_junctions_net_q_mean_W"),
            ("radiation_semantics", "pm5_radiation_semantics"),
            ("runtime_use_guardrail", "pm5_runtime_use_guardrail"),
        ]:
            base[out_field] = heat.get(source_field, "")
        paths = [p for p in [base.get("evidence_paths", ""), rel(PM5_SPLIT_ADMISSION), rel(PM5_HEAT_ROLE_REDUCTION) if heat else ""] if p]
        base["evidence_paths"] = ";".join(dict.fromkeys(";".join(paths).split(";")))
        if source_key and source_key in matrix:
            del matrix[source_key]
        matrix[canonical_key] = base


def build_case_matrix() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ts = aggregate_timeseries()
    meta = metadata_by_source()
    patch_rows, roles_by_source = patch_role_reductions()
    triage, submitted, harvest, pm5_by_case, pm5_by_source, pm5_heat_by_case = load_status_tables()

    matrix: dict[str, dict[str, Any]] = {}
    for case_key, t in ts.items():
        source_id = base_source_from_key(case_key) if case_key.startswith("salt") and "corrected" not in case_key else t["source_id"]
        source_id = source_id if source_id in meta or source_id in roles_by_source else t["source_id"]
        m = meta.get(source_id, {})
        roles = roles_by_source.get(source_id, {})
        evidence_class, use_status, class_source = classify(case_key, source_id, triage, harvest, pm5_by_case, pm5_by_source)
        row = assemble_case_row(case_key, source_id, m, t, roles, evidence_class, use_status, class_source, submitted)
        matrix[case_key] = row

    for source_id, m in meta.items():
        case_key = m.get("case_id", source_id)
        if source_id.startswith("viscosity_screening_salt_test_") and "_jin" in source_id:
            salt = source_id.split("_test_")[1].split("_", 1)[0]
            case_key = f"salt{salt}_jin"
        if case_key in matrix:
            continue
        roles = roles_by_source.get(source_id, {})
        evidence_class, use_status, class_source = classify(case_key, source_id, triage, harvest, pm5_by_case, pm5_by_source)
        matrix[case_key] = assemble_case_row(case_key, source_id, m, {}, roles, evidence_class, use_status, class_source, submitted)

    for case_key, h in harvest.items():
        if case_key in matrix:
            continue
        case_summary = read_csv(Path(h["case_summary_csv"])) if h.get("case_summary_csv") else []
        summary = case_summary[0] if case_summary else {}
        source_id = h.get("source_case_key", summary.get("source_id", case_key))
        evidence_class, use_status, class_source = classify(case_key, source_id, triage, harvest, pm5_by_case, pm5_by_source)
        matrix[case_key] = assemble_case_row(
            case_key,
            source_id,
            {},
            {
                "fluid": case_key.split("_", 1)[0],
                "mdot_mean_abs_kg_s": f(summary.get("mdot_mean_abs_kg_s")),
                "mdot_monitor_count": summary.get("mdot_monitor_count", ""),
                "timeseries_probe_T_avg_K": f(summary.get("latest_tp_avg_k")),
                "timeseries_heat_net_W": f(summary.get("latest_total_Q_postProc_w")),
                "timeseries_verdict": h.get("terminal_window_status", ""),
                "timeseries_source": rel(Path(h["case_summary_csv"])) if h.get("case_summary_csv") else "",
                "postprocessing": summary.get("runtime_root", ""),
            },
            {},
            evidence_class,
            use_status,
            class_source,
            submitted,
        )

    apply_pm5_overlay(matrix, pm5_by_case, pm5_by_source, pm5_heat_by_case)
    case_rows = sorted(matrix.values(), key=lambda r: (r["evidence_class"], r["case_key"]))
    false_map = {
        case_key: {"q_ratio": q_ratio, "observed_mdot_move_pct": observed, "expected_mdot_move_pct": expected}
        for case_key, q_ratio, observed, expected, _verdict in FALSE_STEADY_Q_ROWS
    }
    invalid_rows = []
    for row in case_rows:
        if row["evidence_class"] != "admitted_or_usable":
            enriched = dict(row)
            enriched.update(false_map.get(row["case_key"], {}))
            invalid_rows.append(enriched)
    semantics = semantics_rows()
    response_summary = response_rows(case_rows)
    return case_rows, patch_rows, response_summary, invalid_rows + false_steady_rows_not_in_matrix(case_rows)


def assemble_case_row(
    case_key: str,
    source_id: str,
    m: dict[str, str],
    t: dict[str, Any],
    roles: dict[str, Any],
    evidence_class: str,
    use_status: str,
    class_source: str,
    submitted: dict[str, dict[str, str]],
) -> dict[str, Any]:
    submitted_row = submitted.get(case_key, {})
    mdot = t.get("mdot_mean_abs_kg_s")
    temp = t.get("timeseries_probe_T_avg_K") or f(m.get("probe_T_avg_K"))
    missing_reason = ""
    if f(mdot) is None:
        missing_reason = "no mdot aggregate available in joined sources"
    if f(temp) is None:
        missing_reason = (missing_reason + "; " if missing_reason else "") + "no probe/temperature aggregate available in joined sources"
    source_paths = ";".join(
        p
        for p in [
            rel(CASE_METADATA) if m else "",
            t.get("timeseries_source", ""),
            rel(PATCH_ROLE_TABLE) if roles else "",
            class_source,
        ]
        if p
    )
    return {
        "case_key": case_key,
        "source_case_key": case_key,
        "canonical_case_key": case_key,
        "source_id": source_id,
        "case_id": m.get("case_id", ""),
        "fluid": t.get("fluid") or m.get("fluid", ""),
        "variant_label": m.get("variant_label", ""),
        "evidence_class": evidence_class,
        "split_or_use_status": use_status,
        "steady_or_needs_continuation": submitted_row.get("steady_or_needs_continuation", ""),
        "steady_state_detection_status": submitted_row.get("steady_state_detection_status", t.get("timeseries_verdict", "")),
        "bc_summary_status": "patch_role_summary_available" if roles else "case_level_only_or_missing",
        "heater_power_W": m.get("heater_power_W", ""),
        "cooling_power_W": m.get("cooling_power_W", ""),
        "T_init_K": m.get("T_init_K", ""),
        "heater_h_W_m2K": m.get("heater_h_W_m2K", ""),
        "heater_Ta_K": m.get("heater_Ta_K", ""),
        "heater_emissivity": m.get("heater_emissivity", role_value(roles, "heater", "area_weighted_emissivity")),
        "cooler_h_W_m2K": m.get("cooler_h_W_m2K", role_value(roles, "cooler", "area_weighted_h_W_m2K")),
        "cooler_Ta_K": m.get("cooler_Ta_K", role_value(roles, "cooler", "area_weighted_Ta_K")),
        "test_section_h_W_m2K": m.get("test_section_h_W_m2K", role_value(roles, "test_section", "area_weighted_h_W_m2K")),
        "test_section_Ta_K": m.get("test_section_Ta_K", role_value(roles, "test_section", "area_weighted_Ta_K")),
        "insulated_h_W_m2K": m.get("insulated_h_W_m2K", ""),
        "insulated_Ta_K": m.get("insulated_Ta_K", ""),
        "two_d_radiation_on": m.get("two_d_radiation_on", ""),
        "mdot_mean_abs_kg_s": fmt(mdot, 9),
        "mdot_monitor_count": t.get("mdot_monitor_count", ""),
        "metadata_probe_T_avg_K": m.get("probe_T_avg_K", ""),
        "timeseries_probe_T_avg_K": fmt(t.get("timeseries_probe_T_avg_K"), 6),
        "timeseries_probe_T_min_K": fmt(t.get("timeseries_probe_T_min_K"), 6),
        "timeseries_probe_T_max_K": fmt(t.get("timeseries_probe_T_max_K"), 6),
        "timeseries_wall_T_avg_K": fmt(t.get("timeseries_wall_T_avg_K"), 6),
        "timeseries_heat_net_W": fmt(t.get("timeseries_heat_net_W"), 6),
        "final_total_wall_heat_abs_W": m.get("final_total_wall_heat_abs_w", ""),
        "heater_realized_wallHeatFlux_W": role_value(roles, "heater", "realized_wallHeatFlux_W"),
        "cooler_realized_wallHeatFlux_W": role_value(roles, "cooler", "realized_wallHeatFlux_W"),
        "ambient_wall_realized_wallHeatFlux_W": role_value(roles, "ambient_wall", "realized_wallHeatFlux_W"),
        "test_section_realized_wallHeatFlux_W": role_value(roles, "test_section", "realized_wallHeatFlux_W"),
        "area_weighted_external_h_W_m2K": weighted_external_h(roles),
        "missing_result_reason": missing_reason,
        "source_root": m.get("source_root", t.get("postprocessing", "")),
        "evidence_paths": source_paths,
    }


def false_steady_rows_not_in_matrix(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = {r["case_key"] for r in case_rows}
    rows = []
    for case_key, q_ratio, observed, expected, verdict in FALSE_STEADY_Q_ROWS:
        if case_key in seen:
            continue
        rows.append(
            {
                "case_key": case_key,
                "source_id": base_source_from_key(case_key),
                "evidence_class": "invalid_false_steady",
                "split_or_use_status": "old Q perturbation failed operating-point movement gate",
                "steady_state_detection_status": verdict,
                "missing_result_reason": "invalid old perturbation row; documented in T3 gate",
                "evidence_paths": rel(T3_NOTE),
                "q_ratio": q_ratio,
                "observed_mdot_move_pct": observed,
                "expected_mdot_move_pct": expected,
            }
        )
    return rows


def semantics_rows() -> list[dict[str, str]]:
    return [
        {
            "rule_id": "radiation_embedded_in_wallheatflux",
            "topic": "radiation",
            "rule": "CFD rcExternalTemperature includes emissivity and Tsur; OpenFOAM wallHeatFlux is total wall heat with radiation folded in.",
            "study_consequence": "There is no separate exported `qr`; do not add or plot a separate radiation term for current CFD rows.",
            "source_path": rel(THERMAL_BOUNDARY_MAP),
        },
        {
            "rule_id": "realized_wallheatflux_is_diagnostic",
            "topic": "runtime input",
            "rule": "Realized CFD wallHeatFlux documents outcomes and parity diagnostics, not forward-model runtime inputs.",
            "study_consequence": "Charts can show realized heat, but rows cannot be used to leak CFD outcomes into predictive setup.",
            "source_path": rel(PATCH_ROLE_TABLE),
        },
        {
            "rule_id": "false_steady_q_rows_invalid",
            "topic": "perturbation admission",
            "rule": "Old Q perturbation rows did not move mdot by the expected Q^(1/3) operating-point response.",
            "study_consequence": "They appear only in invalid/provenance tables and the expected-vs-observed chart.",
            "source_path": rel(T3_NOTE),
        },
        {
            "rule_id": "corrected_q_split_pending",
            "topic": "corrected-Q",
            "rule": "Harvested corrected-Q +/-5 rows can be terminal in their gate while still awaiting BC-role refresh and split-policy labeling.",
            "study_consequence": "They are shown as terminal_harvested_split_pending, not as admitted training rows.",
            "source_path": rel(CORRECTED_HARVEST_3295437),
        },
        {
            "rule_id": "case_and_patch_bc_layers",
            "topic": "boundary documentation",
            "rule": "Use case-level metadata for setup scalars and patch-role reductions for actual OpenFOAM boundary roles.",
            "study_consequence": "The main matrix stays compact while patch_role_bc_summary.csv preserves boundary details.",
            "source_path": rel(CASE_METADATA) + ";" + rel(PATCH_ROLE_TABLE),
        },
    ]


def response_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    variables = [
        ("T_init_K", "setup initial temperature"),
        ("metadata_probe_T_avg_K", "metadata probe average temperature"),
        ("timeseries_probe_T_avg_K", "time-series probe average temperature"),
        ("timeseries_wall_T_avg_K", "time-series wall-temperature average"),
        ("heater_power_W", "heater setup power"),
        ("cooling_power_W", "cooler setup power"),
        ("area_weighted_external_h_W_m2K", "patch-role area-weighted external h"),
        ("final_total_wall_heat_abs_W", "metadata final total wall heat magnitude"),
    ]
    rows: list[dict[str, str]] = []
    for scope_name, scope_rows in [
        ("all_rows_with_mdot", [r for r in case_rows if f(r.get("mdot_mean_abs_kg_s")) is not None]),
        ("admitted_or_usable_with_mdot", [r for r in case_rows if r["evidence_class"] == "admitted_or_usable" and f(r.get("mdot_mean_abs_kg_s")) is not None]),
    ]:
        for variable, label in variables:
            pairs = [(f(r.get(variable)), f(r.get("mdot_mean_abs_kg_s"))) for r in scope_rows]
            pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
            xs = [x for x, _ in pairs]
            ys = [y for _, y in pairs]
            fit = linear_fit(xs, ys)
            x_delta = (max(xs) - min(xs)) if xs else None
            y_delta = (max(ys) - min(ys)) if ys else None
            rows.append(
                {
                    "scope": scope_name,
                    "variable": variable,
                    "label": label,
                    "n": str(len(pairs)),
                    "x_min": fmt(min(xs) if xs else None, 6),
                    "x_max": fmt(max(xs) if xs else None, 6),
                    "mdot_min_kg_s": fmt(min(ys) if ys else None, 9),
                    "mdot_max_kg_s": fmt(max(ys) if ys else None, 9),
                    "pearson_r": fmt(fit["r"], 6),
                    "r_squared": fmt(fit["r_squared"], 6),
                    "slope_kg_s_per_unit": fmt(fit["slope"], 12),
                    "intercept_kg_s": fmt(fit["intercept"], 9),
                    "x_delta_observed_range": fmt(x_delta, 6),
                    "mdot_delta_observed_range_kg_s": fmt(y_delta, 9),
                    "trend_statement": trend_statement_for(variable, len(pairs), fit["r"], fit["slope"], scope_name),
                    "paper_use": paper_use_for(scope_name, variable, len(pairs)),
                    "interpretation": interpretation_for(variable, len(pairs), fit["r"]),
                }
            )
    return rows


def trend_statement_for(variable: str, n: int, r: float | None, slope: float | None, scope: str) -> str:
    if n < 3:
        return "too few rows for a reported trend"
    if r is None or slope is None:
        return "finite trend not available"
    direction = "increases" if slope > 0 else "decreases"
    strength = "strong" if abs(r) >= 0.8 else "moderate" if abs(r) >= 0.5 else "weak"
    caveat = "mainline monotonic ordering" if scope == "admitted_or_usable_with_mdot" else "mixed admitted/diagnostic association"
    return f"mdot {direction} with {variable}; {strength} {caveat}; not a controlled causal fit"


def paper_use_for(scope: str, variable: str, n: int) -> str:
    if n < 3:
        return "do_not_use_for_trend"
    if scope == "admitted_or_usable_with_mdot":
        return "paper_observational_trend_limited_n3"
    if variable in {"heater_power_W", "cooling_power_W", "area_weighted_external_h_W_m2K", "T_init_K"}:
        return "paper_context_only_confounding_by_case_design"
    return "paper_supplement_diagnostic_only"


def interpretation_for(variable: str, n: int, r: float | None) -> str:
    if n < 3:
        return "insufficient rows for trend claim"
    if r is None:
        return "no finite variance for correlation"
    strength = "strong" if abs(r) >= 0.8 else "moderate" if abs(r) >= 0.5 else "weak"
    return f"{strength} observed association only; not a controlled causal fit"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def draw_scatter(path: Path, rows: list[dict[str, Any]], xfield: str, yfield: str, title: str, xlabel: str) -> None:
    pts = [(f(r.get(xfield)), f(r.get(yfield)), r) for r in rows]
    pts = [(x, y, r) for x, y, r in pts if x is not None and y is not None]
    width, height = 780, 480
    left, right, top, bottom = 92, 730, 54, 410
    colors = {
        "admitted_or_usable": "#12664f",
        "diagnostic": "#5e6b73",
        "terminal_harvested_split_pending": "#b26a00",
        "pending_terminal_admission": "#8a5a9e",
        "invalid_false_steady": "#b23838",
        "invalid_or_rejected": "#b23838",
    }
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        if xmin == xmax:
            xmin -= 1
            xmax += 1
        if ymin == ymax:
            ymin -= 0.001
            ymax += 0.001
    else:
        xmin, xmax, ymin, ymax = 0.0, 1.0, 0.0, 1.0

    def sx(x: float) -> float:
        return left + (x - xmin) / (xmax - xmin) * (right - left)

    def sy(y: float) -> float:
        return bottom - (y - ymin) / (ymax - ymin) * (bottom - top)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<!-- generated_by={TASK}; source={rel(path)}; x={xfield}; y={yfield} -->",
        '<rect width="100%" height="100%" fill="#fcfcfb"/>',
        '<style>text{font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:#111}.title{font-size:19px;font-weight:700}.axis{font-size:12px;fill:#444}.tick{font-size:10px;fill:#777}.legend{font-size:11px;fill:#333}</style>',
        f'<text x="{left}" y="28" class="title">{esc(title)}</text>',
        f'<text x="{(left+right)/2}" y="458" text-anchor="middle" class="axis">{esc(xlabel)}</text>',
        '<text x="18" y="235" transform="rotate(-90 18 235)" text-anchor="middle" class="axis">mean |mdot| [kg/s]</text>',
    ]
    for i in range(5):
        x = left + i * (right - left) / 4
        y = top + i * (bottom - top) / 4
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}" stroke="#e5e2da"/>')
        parts.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e5e2da"/>')
        xv = xmin + i * (xmax - xmin) / 4
        yv = ymax - i * (ymax - ymin) / 4
        parts.append(f'<text x="{x:.1f}" y="{bottom+18}" text-anchor="middle" class="tick">{xv:.3g}</text>')
        parts.append(f'<text x="{left-10}" y="{y+3:.1f}" text-anchor="end" class="tick">{yv:.4f}</text>')
    parts.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#bdb8ad"/>')
    for x, y, row in pts:
        color = colors.get(row.get("evidence_class", ""), "#555")
        parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="5" fill="{color}" opacity="0.9"><title>{esc(row["case_key"])} {xfield}={x:.4g} mdot={y:.6f}</title></circle>')
    legend_x, legend_y = 505, 68
    for idx, (label, color) in enumerate(colors.items()):
        yy = legend_y + idx * 18
        parts.append(f'<circle cx="{legend_x}" cy="{yy}" r="5" fill="{color}"/>')
        parts.append(f'<text x="{legend_x+12}" y="{yy+4}" class="legend">{esc(label)}</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def draw_q_perturbation(path: Path) -> None:
    width, height = 840, 520
    left, top, bottom = 220, 50, 470
    max_val = 4.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<!-- generated_by={TASK}; source={rel(T3_NOTE)} -->",
        '<rect width="100%" height="100%" fill="#fcfcfb"/>',
        '<style>text{font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:#111}.title{font-size:19px;font-weight:700}.lbl{font-size:10px}.tick{font-size:10px;fill:#777}.legend{font-size:11px}</style>',
        '<text x="32" y="28" class="title">Q perturbation rows: expected vs observed mdot movement</text>',
    ]
    row_h = 27
    scale_w = 560
    for i in range(5):
        x = left + i * scale_w / 4
        v = i * max_val / 4
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}" stroke="#e5e2da"/>')
        parts.append(f'<text x="{x:.1f}" y="492" text-anchor="middle" class="tick">{v:.1f}%</text>')
    for idx, (case_key, _q, observed, expected, _verdict) in enumerate(FALSE_STEADY_Q_ROWS):
        y = top + idx * row_h
        obs = abs(f(observed) or 0.0)
        exp = f(expected) or 0.0
        parts.append(f'<text x="{left-8}" y="{y+13}" text-anchor="end" class="lbl">{esc(case_key)}</text>')
        parts.append(f'<rect x="{left}" y="{y+4}" width="{exp/max_val*scale_w:.1f}" height="8" fill="#d39b33"/>')
        parts.append(f'<rect x="{left}" y="{y+15}" width="{obs/max_val*scale_w:.1f}" height="8" fill="#b23838"/>')
    parts.append('<rect x="570" y="32" width="12" height="8" fill="#d39b33"/><text x="588" y="40" class="legend">expected |move|</text>')
    parts.append('<rect x="570" y="48" width="12" height="8" fill="#b23838"/><text x="588" y="56" class="legend">observed |move|</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def draw_heat_breakdown(path: Path, patch_rows: list[dict[str, Any]]) -> None:
    selected = [r for r in patch_rows if r["source_id"] in {
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "viscosity_screening_salt_test_4_jin_coarse_mesh",
    }]
    roles = ["heater", "cooler", "ambient_wall", "test_section", "junction_other"]
    colors = {"heater": "#12664f", "cooler": "#3267a8", "ambient_wall": "#b26a00", "test_section": "#8a5a9e", "junction_other": "#6d6a63"}
    by_case: dict[str, dict[str, float]] = defaultdict(dict)
    for row in selected:
        by_case[row["source_id"]][row["role"]] = f(row.get("realized_wallHeatFlux_W")) or 0.0
    width, height = 820, 390
    left, top = 230, 58
    max_abs = max([abs(v) for rolemap in by_case.values() for v in rolemap.values()] + [1.0])
    scale = 250 / max_abs
    zero = 500
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<!-- generated_by={TASK}; source={rel(PATCH_ROLE_TABLE)} -->",
        '<rect width="100%" height="100%" fill="#fcfcfb"/>',
        '<style>text{font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:#111}.title{font-size:19px;font-weight:700}.lbl{font-size:11px}.legend{font-size:11px}</style>',
        '<text x="32" y="28" class="title">Patch-role realized wallHeatFlux by mainline Salt case</text>',
        f'<line x1="{zero}" x2="{zero}" y1="{top-10}" y2="{height-55}" stroke="#bdb8ad"/>',
    ]
    y = top
    for case, rolemap in sorted(by_case.items()):
        parts.append(f'<text x="{left-10}" y="{y+16}" text-anchor="end" class="lbl">{esc(case.replace("viscosity_screening_", ""))}</text>')
        yy = y
        for role in roles:
            val = rolemap.get(role, 0.0)
            w = abs(val) * scale
            x = zero if val >= 0 else zero - w
            parts.append(f'<rect x="{x:.1f}" y="{yy}" width="{max(w, 0.5):.1f}" height="10" fill="{colors[role]}"><title>{esc(role)} {val:.3f} W</title></rect>')
            yy += 13
        y += 75
    lx, ly = 570, 68
    for i, role in enumerate(roles):
        parts.append(f'<rect x="{lx}" y="{ly+i*17}" width="12" height="9" fill="{colors[role]}"/>')
        parts.append(f'<text x="{lx+18}" y="{ly+8+i*17}" class="legend">{esc(role)}</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def write_figures(out: Path, case_rows: list[dict[str, Any]], patch_rows: list[dict[str, Any]]) -> None:
    fig = out / "figures"
    draw_scatter(fig / "mdot_vs_probe_temperature.svg", case_rows, "timeseries_probe_T_avg_K", "mdot_mean_abs_kg_s", "Flow rate vs probe temperature", "time-series probe average temperature [K]")
    draw_scatter(fig / "mdot_vs_initial_temperature.svg", case_rows, "T_init_K", "mdot_mean_abs_kg_s", "Flow rate vs initial temperature", "initial temperature [K]")
    draw_scatter(fig / "mdot_vs_heater_power.svg", case_rows, "heater_power_W", "mdot_mean_abs_kg_s", "Flow rate vs heater setup power", "heater power [W]")
    draw_scatter(fig / "mdot_vs_cooler_power.svg", case_rows, "cooling_power_W", "mdot_mean_abs_kg_s", "Flow rate vs cooler setup power", "cooler power [W]")
    draw_scatter(fig / "mdot_vs_area_weighted_external_h.svg", case_rows, "area_weighted_external_h_W_m2K", "mdot_mean_abs_kg_s", "Flow rate vs area-weighted external h", "area-weighted external h [W/m2-K]")
    draw_q_perturbation(fig / "q_perturbation_expected_vs_observed_mdot_move.svg")
    draw_heat_breakdown(fig / "bc_role_heat_breakdown_by_case.svg", patch_rows)


def trend_lookup(response_summary: list[dict[str, str]], scope: str, variable: str) -> dict[str, str]:
    for row in response_summary:
        if row["scope"] == scope and row["variable"] == variable:
            return row
    return {}


def paper_conclusion_rows(case_rows: list[dict[str, Any]], response_summary: list[dict[str, str]]) -> list[dict[str, str]]:
    admitted = [r for r in case_rows if r["case_key"] in {"salt2_jin", "salt3_jin", "salt4_jin"}]
    admitted = sorted(admitted, key=lambda r: f(r.get("timeseries_probe_T_avg_K")) or 0.0)
    mdots = [f(r.get("mdot_mean_abs_kg_s")) for r in admitted]
    temps = [f(r.get("timeseries_probe_T_avg_K")) for r in admitted]
    heater = trend_lookup(response_summary, "admitted_or_usable_with_mdot", "heater_power_W")
    probe = trend_lookup(response_summary, "admitted_or_usable_with_mdot", "timeseries_probe_T_avg_K")
    external_h = trend_lookup(response_summary, "all_rows_with_mdot", "area_weighted_external_h_W_m2K")
    pm5_rows = [r for r in case_rows if r.get("evidence_class") == "terminal_harvested_split_pending"]
    false_abs = [abs(f(row[2]) or 0.0) for row in FALSE_STEADY_Q_ROWS]
    false_exp = [f(row[3]) or 0.0 for row in FALSE_STEADY_Q_ROWS]
    return [
        {
            "conclusion_id": "C1_mainline_flow_temperature_ordering",
            "finding": (
                f"Across admitted Salt2/Salt3/Salt4 mainline rows, |mdot| rises from {fmt(min(mdots), 9)} to {fmt(max(mdots), 9)} kg/s "
                f"as time-series probe temperature rises from {fmt(min(temps), 3)} to {fmt(max(temps), 3)} K."
            ),
            "evidence": f"n=3; Pearson r={probe.get('pearson_r', '')}; slope={probe.get('slope_kg_s_per_unit', '')} kg/s/K",
            "paper_claim_strength": "observational monotonic trend; limited by n=3 and covarying boundary conditions",
            "limitation_or_blocker": "not a controlled flow-temperature law; Salt2 and Salt3 remain heat-drifting in steady labels",
        },
        {
            "conclusion_id": "C2_power_temperature_boundary_confounding",
            "finding": "Initial temperature, probe temperature, heater power, cooler power, and external-h settings co-vary with the Salt case design.",
            "evidence": f"heater trend n={heater.get('n', '')}, r={heater.get('pearson_r', '')}; all-row external-h r={external_h.get('pearson_r', '')}",
            "paper_claim_strength": "valid as design documentation and context",
            "limitation_or_blocker": "do not interpret scalar correlations as independent causal coefficients",
        },
        {
            "conclusion_id": "C3_boundary_heat_roles_scale_with_case",
            "finding": "Patch-role reductions show heater input, cooler removal, and passive heat losses increasing in magnitude from Salt2 to Salt4.",
            "evidence": "heater/cooler/ambient/test-section/junction wallHeatFlux roles are tabulated in patch_role_bc_summary.csv and plotted in bc_role_heat_breakdown_by_case.svg",
            "paper_claim_strength": "usable for boundary-condition audit and qualitative heat-path explanation",
            "limitation_or_blocker": "realized wallHeatFlux is a diagnostic outcome, not a predictive runtime input",
        },
        {
            "conclusion_id": "C4_old_q_perturbations_are_not_physical_response_rows",
            "finding": (
                f"Old Q perturbation rows are false-steady: observed mdot moves are {fmt(min(false_abs), 3)}-{fmt(max(false_abs), 3)}%, "
                f"well below expected {fmt(min(false_exp), 2)}-{fmt(max(false_exp), 2)}% movement."
            ),
            "evidence": "invalid_or_diagnostic_runs.csv and q_perturbation_expected_vs_observed_mdot_move.svg",
            "paper_claim_strength": "strong exclusion/admission claim",
            "limitation_or_blocker": "none for exclusion; these rows remain provenance only",
        },
        {
            "conclusion_id": "C5_corrected_pm5q_rows_are_sensitivity_evidence",
            "finding": f"{len(pm5_rows)} corrected +/-5Q rows are terminal-harvested and split-pending, with heat-role reductions now linked into this study.",
            "evidence": "corrected_q_pm5_response_overlay.csv; source AGENT-353 split-admission and heat-role tables",
            "paper_claim_strength": "usable as sensitivity/admission evidence, not independent fit rows",
            "limitation_or_blocker": "requires perturbation split policy, BC-role refresh, and operating-point/matched-plane gates before independent training or scoring use",
        },
        {
            "conclusion_id": "C6_radiation_semantics",
            "finding": "For current CFD rows, rcExternalTemperature includes radiation in total wallHeatFlux; no separate exported qr term exists.",
            "evidence": "bc_semantics_and_assumptions.csv; thermal-boundary-and-radiation map",
            "paper_claim_strength": "required methods statement",
            "limitation_or_blocker": "do not double-count radiation or present a separate CFD qr heat-loss budget",
        },
    ]


def pm5_overlay_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in case_rows if r.get("evidence_class") == "terminal_harvested_split_pending"]


def paper_ready_analysis(case_rows: list[dict[str, Any]], response_summary: list[dict[str, str]], conclusions: list[dict[str, str]]) -> str:
    admitted = sorted(
        [r for r in case_rows if r["case_key"] in {"salt2_jin", "salt3_jin", "salt4_jin"}],
        key=lambda r: f(r.get("timeseries_probe_T_avg_K")) or 0.0,
    )
    probe = trend_lookup(response_summary, "admitted_or_usable_with_mdot", "timeseries_probe_T_avg_K")
    heater = trend_lookup(response_summary, "admitted_or_usable_with_mdot", "heater_power_W")
    cooler = trend_lookup(response_summary, "admitted_or_usable_with_mdot", "cooling_power_W")
    pm5_count = sum(1 for r in case_rows if r.get("evidence_class") == "terminal_harvested_split_pending")
    admitted_lines = "\n".join(
        f"- `{r['case_key']}`: |mdot|={r.get('mdot_mean_abs_kg_s')} kg/s, probe T={r.get('timeseries_probe_T_avg_K')} K, "
        f"heater={r.get('heater_power_W')} W, cooler={r.get('cooling_power_W')} W, split/use=`{r.get('split_or_use_status')}`."
        for r in admitted
    )
    conclusion_lines = "\n".join(
        f"- **{row['conclusion_id']}**: {row['finding']} Claim strength: {row['paper_claim_strength']}. Limitation: {row['limitation_or_blocker']}."
        for row in conclusions
    )
    return f"""# Paper-Ready Flow-Rate, Temperature, and Boundary-Condition Analysis

Task: `{PAPER_TASK}` additive hardening of `{TASK}`
Date: `{DATE}`

## Scope And Data

This analysis joins case-level boundary-condition metadata, time-series
mdot/temperature aggregates, patch-role OpenFOAM boundary reductions, submitted
steady-state labels, false-steady perturbation provenance, and split-aware
corrected +/-5Q terminal-harvest evidence. It does not run OpenFOAM, mutate
native CFD solver outputs, modify registry/admission state, or edit external
`../cfd-modeling-tools`.

The study is suitable for paper methods/results text as an audited observational
dataset. It is not a controlled causal fit of flow rate against temperature
because the Salt2/Salt3/Salt4 design changes temperature, heater power, cooler
power, and boundary coefficients together.

## Admitted Mainline Rows

{admitted_lines}

The admitted/usable mainline rows show a monotonic increase in |mdot| with
temperature: for time-series probe temperature, n=`{probe.get('n', '')}`,
Pearson r=`{probe.get('pearson_r', '')}`, R2=`{probe.get('r_squared', '')}`, and
slope=`{probe.get('slope_kg_s_per_unit', '')}` kg/s/K. Heater power gives
n=`{heater.get('n', '')}`, r=`{heater.get('pearson_r', '')}`, and slope=`{heater.get('slope_kg_s_per_unit', '')}`
kg/s/W; cooler setup power gives n=`{cooler.get('n', '')}`, r=`{cooler.get('pearson_r', '')}`.
These values document the observed ordering, not an independent closure law.

## Boundary Conditions And Heat Roles

Case-level setup scalars document the intended initial temperature, heater
power, cooler setting, and external boundary coefficients. Patch-role reductions
document the realized OpenFOAM boundary roles and total `wallHeatFlux` by heater,
cooler, ambient wall, test section, and junction/other surfaces. Realized
`wallHeatFlux` is a diagnostic result and must not be used as a predictive
runtime input.

Radiation semantics are explicit: CFD `rcExternalTemperature` includes
emissivity and surroundings-temperature radiation in total `wallHeatFlux`, and
there is no separate exported `qr` term in the current CFD outputs. Paper text
should therefore describe radiation as embedded in the boundary heat flux, not
as a separately measured heat-loss channel.

## Perturbation Evidence

Old Q perturbation rows remain invalid false-steady provenance. Their observed
|mdot| movement is far smaller than the expected Q^(1/3)-type operating-point
movement, so they cannot support a flow-rate/temperature response conclusion.

The corrected +/-5Q rows are handled separately. This package includes
`{pm5_count}` terminal-harvested corrected-Q rows from the split-aware AGENT-353
tables and their heat-role reductions. They are sensitivity/admission evidence
only: they do not expand the training, validation, or holdout sets until the
perturbation split policy and required operating-point gates are explicitly
updated.

## Conclusions

{conclusion_lines}
"""


def readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(CASE_METADATA)}
  - {rel(STEADY_SUMMARY)}
  - {rel(PATCH_ROLE_TABLE)}
  - {rel(TRIAGE)}
  - {rel(CORRECTED_HARVEST_3295437)}
  - {rel(PM5_SPLIT_ADMISSION)}
  - {rel(PM5_HEAT_ROLE_REDUCTION)}
tags: [flow-rate, temperature, boundary-conditions, cfd-admission]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: {TASK}
date: {DATE}
role: BC-modeling/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Flow Rate, Temperature, and Boundary-Condition Response Study

## Purpose

This package consolidates existing CFD evidence into one chart-first study of
how loop flow rate varies with temperature and boundary-condition choices. It
does not run OpenFOAM, mutate solver outputs, edit registry/admission state, or
change external Fluid code.

## Current Result

- Case response rows: `{summary['case_rows']}`.
- Patch-role BC rows: `{summary['patch_role_rows']}`.
- Admitted/usable response rows with mdot: `{summary['admitted_rows_with_mdot']}`.
- Invalid false-steady Q perturbation rows tracked: `{summary['false_steady_rows']}`.
- Corrected-Q terminal harvested but split-pending rows: `{summary['terminal_harvested_split_pending_rows']}`.
- Paper conclusion rows: `{summary['paper_conclusion_rows']}`.

The strongest physically usable trend evidence today remains the mainline Salt
2/3/4 split rows. Diagnostic and historical rows are retained because they
explain which boundary conditions were attempted and why some apparent steady
results cannot be used as physical response data.

## Paper-Ready Interpretation

See `paper_ready_analysis.md` for methods/results prose, the admissible
observational trend statement, limitations, and paper-safe conclusions. The
mainline Salt2/Salt3/Salt4 trend is admissible as an observed monotonic ordering
only; it is not a controlled causal fit because temperature, heater power,
cooler power, and external boundary settings co-vary by case design.

## Boundary-Condition Semantics

Case-level setup fields come from the Ethan case metadata index. Patch-level
OpenFOAM boundary details come from the thermal boundary patch-role table.
Current CFD `rcExternalTemperature` includes emissivity/Tsur radiation inside
total `wallHeatFlux`; no separate exported `qr` term exists.

## Important Caveats

- Old Q perturbation rows are false-steady provenance only; their mdot did not
  move by the expected operating-point response.
- Corrected-Q +/-5 rows harvested by job `3295437` are terminal in that gate,
  and now linked to AGENT-353 heat-role reductions, but still need split-policy
  and operating-point gate updates before being treated as independent training
  or scoring rows.
- Rows with missing mdot or temperature aggregates stay in the tables with an
  explicit missing-result reason instead of being silently dropped.

## Files

- `case_bc_response_matrix.csv`
- `patch_role_bc_summary.csv`
- `flow_temperature_response_summary.csv`
- `trend_correlation_analysis.csv`
- `paper_conclusions.csv`
- `corrected_q_pm5_response_overlay.csv`
- `paper_ready_analysis.md`
- `invalid_or_diagnostic_runs.csv`
- `bc_semantics_and_assumptions.csv`
- `source_manifest.csv`
- `summary.json`
- `figures/*.svg`
"""


def source_manifest() -> list[dict[str, str]]:
    sources = [
        CASE_METADATA,
        STEADY_SUMMARY,
        TIME_CASE_INVENTORY,
        PATCH_ROLE_TABLE,
        PATCH_ROLE_SUMMARY,
        SUBMITTED_STEADY,
        SUBMITTED_COMPACT,
        SALT_INVENTORY,
        TRIAGE,
        CORRECTED_HARVEST_3295437,
        PM5_SPLIT_ADMISSION,
        PM5_HEAT_ROLE_REDUCTION,
        PM5_FORWARD_GATE_QUEUE,
        HIINS_LOINS_REVIEW,
        T2_NOTE,
        T3_NOTE,
        THERMAL_BOUNDARY_MAP,
    ]
    return [{"path": rel(path), "exists": "yes" if path.exists() else "no", "role": "read_only_input"} for path in sources]


CASE_FIELDS = [
    "case_key", "source_case_key", "canonical_case_key", "source_id", "case_id", "fluid", "variant_label", "evidence_class", "split_or_use_status",
    "steady_or_needs_continuation", "steady_state_detection_status", "bc_summary_status",
    "heater_power_W", "cooling_power_W", "T_init_K", "heater_h_W_m2K", "heater_Ta_K", "heater_emissivity",
    "cooler_h_W_m2K", "cooler_Ta_K", "test_section_h_W_m2K", "test_section_Ta_K", "insulated_h_W_m2K",
    "insulated_Ta_K", "two_d_radiation_on", "mdot_mean_abs_kg_s", "mdot_monitor_count",
    "metadata_probe_T_avg_K", "timeseries_probe_T_avg_K", "timeseries_probe_T_min_K",
    "timeseries_probe_T_max_K", "timeseries_wall_T_avg_K", "timeseries_heat_net_W",
    "final_total_wall_heat_abs_W", "heater_realized_wallHeatFlux_W", "cooler_realized_wallHeatFlux_W",
    "ambient_wall_realized_wallHeatFlux_W", "test_section_realized_wallHeatFlux_W",
    "area_weighted_external_h_W_m2K", "q_ratio", "current_split_family", "terminal_harvest_state",
    "closure_fit_admissible_terminal_gate", "can_expand_training_now", "can_score_validation_now",
    "can_score_holdout_now", "blocked_use", "next_required_gate", "pm5_final_window_start_s",
    "pm5_final_window_end_s", "pm5_final_window_row_count", "pm5_total_Q_postProc_mean_W",
    "pm5_ambient_proxy_mean_W", "pm5_cooling_branch_total_removal_mean_W",
    "pm5_section_heater_net_q_mean_W", "pm5_section_test_section_net_q_mean_W",
    "pm5_section_cooling_branch_net_q_mean_W", "pm5_section_downcomer_net_q_mean_W",
    "pm5_section_upcomer_net_q_mean_W", "pm5_section_junctions_net_q_mean_W",
    "pm5_radiation_semantics", "pm5_runtime_use_guardrail",
    "missing_result_reason", "source_root", "evidence_paths",
]

PATCH_FIELDS = [
    "source_id", "case_id", "role", "role_group", "patch_count", "area_m2", "imposed_Q_W",
    "realized_wallHeatFlux_W", "rcExternalTemperature_count", "externalTemperature_count",
    "zeroGradient_count", "area_weighted_h_W_m2K", "area_weighted_Ta_K", "area_weighted_Tsur_K",
    "area_weighted_emissivity", "source_table",
]

RESPONSE_FIELDS = [
    "scope", "variable", "label", "n", "x_min", "x_max", "mdot_min_kg_s", "mdot_max_kg_s",
    "pearson_r", "r_squared", "slope_kg_s_per_unit", "intercept_kg_s", "x_delta_observed_range",
    "mdot_delta_observed_range_kg_s", "trend_statement", "paper_use", "interpretation",
]

CONCLUSION_FIELDS = [
    "conclusion_id", "finding", "evidence", "paper_claim_strength", "limitation_or_blocker",
]


def build(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    case_rows, patch_rows, response_summary, invalid_rows = build_case_matrix()
    semantics = semantics_rows()
    conclusions = paper_conclusion_rows(case_rows, response_summary)
    pm5_rows = pm5_overlay_rows(case_rows)
    write_csv(out / "case_bc_response_matrix.csv", case_rows, CASE_FIELDS)
    write_csv(out / "patch_role_bc_summary.csv", patch_rows, PATCH_FIELDS)
    write_csv(out / "flow_temperature_response_summary.csv", response_summary, RESPONSE_FIELDS)
    write_csv(out / "trend_correlation_analysis.csv", response_summary, RESPONSE_FIELDS)
    write_csv(out / "paper_conclusions.csv", conclusions, CONCLUSION_FIELDS)
    write_csv(out / "corrected_q_pm5_response_overlay.csv", pm5_rows, CASE_FIELDS)
    invalid_fields = CASE_FIELDS + ["q_ratio", "observed_mdot_move_pct", "expected_mdot_move_pct"]
    write_csv(out / "invalid_or_diagnostic_runs.csv", invalid_rows, invalid_fields)
    write_csv(out / "bc_semantics_and_assumptions.csv", semantics, ["rule_id", "topic", "rule", "study_consequence", "source_path"])
    write_csv(out / "source_manifest.csv", source_manifest(), ["path", "exists", "role"])
    write_figures(out, case_rows, patch_rows)

    summary = {
        "task": TASK,
        "paper_hardened_by": PAPER_TASK,
        "date": DATE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "case_rows": len(case_rows),
        "patch_role_rows": len(patch_rows),
        "response_summary_rows": len(response_summary),
        "paper_conclusion_rows": len(conclusions),
        "corrected_pm5_overlay_rows": len(pm5_rows),
        "admitted_rows_with_mdot": sum(1 for r in case_rows if r["evidence_class"] == "admitted_or_usable" and r.get("mdot_mean_abs_kg_s")),
        "false_steady_rows": sum(1 for r in invalid_rows if r.get("evidence_class") == "invalid_false_steady"),
        "terminal_harvested_split_pending_rows": sum(1 for r in case_rows if r["evidence_class"] == "terminal_harvested_split_pending"),
        "figures": [f"figures/{name}" for name in FIGURES],
        "paper_outputs": [
            "paper_ready_analysis.md",
            "paper_conclusions.csv",
            "trend_correlation_analysis.csv",
            "corrected_q_pm5_response_overlay.csv",
        ],
        "native_cfd_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
    }
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(readme(summary), encoding="utf-8")
    (out / "paper_ready_analysis.md").write_text(paper_ready_analysis(case_rows, response_summary, conclusions), encoding="utf-8")

    if out.resolve() == OUT.resolve():
        status = ROOT / ".agent/status/2026-07-14_AGENT-351.md"
        paper_status = ROOT / ".agent/status/2026-07-14_AGENT-359.md"
        journal = ROOT / ".agent/journal/2026-07-14/flow-rate-temperature-bc-response-study.md"
        paper_journal = ROOT / ".agent/journal/2026-07-14/flow-rate-temperature-bc-response-paper-analysis.md"
        import_path = ROOT / "imports/2026-07-14_flow_rate_temperature_bc_response_study.json"
        paper_import_path = ROOT / "imports/2026-07-14_flow_rate_temperature_bc_response_paper_analysis.json"
        status.write_text(
            f"""# {TASK} Status

Status: COMPLETE

Built `{rel(out)}` with `{summary['case_rows']}` case response rows, `{summary['patch_role_rows']}` patch-role BC rows, `{len(FIGURES)}` SVG figures, strict admitted/diagnostic/pending/invalid classifications, and `{summary['paper_conclusion_rows']}` paper-ready conclusion rows.

No native CFD solver outputs, registry/admission state, scheduler state, generated indexes, or external `../cfd-modeling-tools` files were mutated.
""",
            encoding="utf-8",
        )
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_text(
            f"""# Flow Rate, Temperature, and Boundary-Condition Response Study

Task: `{TASK}`
Date: `{DATE}`

Implemented a chart-first study package joining case-level setup BCs, time-series
mdot/temperature aggregates, patch-role boundary reductions, submitted-run
steady labels, corrected-Q harvest status, and false-steady perturbation
provenance.

Key guardrails: old Q perturbation rows are invalid_false_steady provenance;
corrected-Q +/-5 rows harvested by job 3295437 are terminal but split/BC-role
pending; radiation is embedded in `rcExternalTemperature` wallHeatFlux with no
separate exported `qr`.

AGENT-359 hardening added paper-ready trend/regression descriptors, split-aware
corrected-Q +/-5 overlays from AGENT-353, conclusion rows, and a generated
paper narrative without changing solver outputs or admission state.
""",
            encoding="utf-8",
        )
        paper_status.write_text(
            f"""# {PAPER_TASK} Status

Status: COMPLETE

Hardened `{rel(out)}` for scientific-paper use. Added `paper_ready_analysis.md`, `paper_conclusions.csv`, `trend_correlation_analysis.csv`, and `corrected_q_pm5_response_overlay.csv`.

Main result: Salt2/Salt3/Salt4 show an observational monotonic |mdot|-temperature ordering, but not a controlled causal flow-temperature fit because temperature, heater power, cooler power, and external boundary settings co-vary. Corrected +/-5Q rows remain terminal-harvested sensitivity/admission evidence only, not independent fit rows.

No native CFD solver outputs, registry/admission state, scheduler state, generated indexes, or external `../cfd-modeling-tools` files were mutated.
""",
            encoding="utf-8",
        )
        paper_journal.write_text(
            f"""# Flow-Rate/Temperature/BC Response Paper Analysis

Task: `{PAPER_TASK}`
Date: `{DATE}`

Added a reproducible paper-facing analysis layer to the AGENT-351 study. The
builder now writes ordinary least-squares trend descriptors, paper-use labels,
conclusion rows, a generated paper narrative, and a canonical corrected +/-5Q
overlay sourced from AGENT-353 split-admission and heat-role tables.

Interpretation: admitted Salt2/Salt3/Salt4 rows support a paper-safe statement
that loop |mdot| increases monotonically with the observed temperature/power
case ordering. They do not support an independent causal fit because boundary
conditions co-vary. Old Q perturbations remain false-steady provenance, and
corrected +/-5Q rows remain sensitivity/admission evidence pending explicit
split-policy and operating-point gates.
""",
            encoding="utf-8",
        )
        write_json(
            import_path,
            {
                "task": TASK,
                "paper_hardened_by": PAPER_TASK,
                "date": DATE,
                "kind": "work_product_import",
                "work_product": rel(out),
                "summary": rel(out / "summary.json"),
                "status": rel(status),
                "journal": rel(journal),
                "native_cfd_outputs_mutated": False,
                "external_cfd_modeling_tools_mutated": False,
                "generated_index_refresh": "not_run_active_AGENT_344_owns_generated_index_scope",
            },
        )
        write_json(
            paper_import_path,
            {
                "task": PAPER_TASK,
                "base_task": TASK,
                "date": DATE,
                "kind": "work_product_import",
                "work_product": rel(out),
                "paper_ready_analysis": rel(out / "paper_ready_analysis.md"),
                "paper_conclusions": rel(out / "paper_conclusions.csv"),
                "trend_correlation_analysis": rel(out / "trend_correlation_analysis.csv"),
                "corrected_q_pm5_response_overlay": rel(out / "corrected_q_pm5_response_overlay.csv"),
                "summary": rel(out / "summary.json"),
                "status": rel(paper_status),
                "journal": rel(paper_journal),
                "native_cfd_outputs_mutated": False,
                "external_cfd_modeling_tools_mutated": False,
                "generated_index_refresh": "not_run_active_AGENT_344_owns_generated_index_scope",
            },
        )
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
