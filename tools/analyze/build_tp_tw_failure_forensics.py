#!/usr/bin/env python3
"""Build AGENT-536 TP/TW failure-forensics requirement matrices.

This is an existing-evidence package. It ranks wall/test-section TP/TW
failures and turns them into physics requirements before another Fluid grid is
launched.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-536"
DATE = "2026-07-18"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics")
OUT = ROOT / OUT_REL
STATUS = ROOT / f".agent/status/{DATE}_{TASK}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-18/tp-tw-failure-forensics.md"
IMPORT = ROOT / "imports/2026-07-18_tp_tw_failure_forensics.json"
MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"

AUDIT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit"
HANDOFF = ROOT / "operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md"
AGENT526 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate"

REQUIRED_AUDIT_FILES = [
    "probe_residual_atlas.csv",
    "role_segment_residual_atlas.csv",
    "invariant_failure_modes.csv",
    "admission_gate_sanity.csv",
    "cross_candidate_residual_matrix.csv",
    "next_lane_decision.csv",
    "README.md",
    "summary.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: Any) -> float | None:
    try:
        if value in ("", None, "nan", "NaN"):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: float | None, precision: int = 10) -> str:
    if value is None or not math.isfinite(value):
        return ""
    return f"{value:.{precision}g}"


def finite_max(values: Iterable[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    return max(finite) if finite else None


def require_sources() -> None:
    paths = [AUDIT / name for name in REQUIRED_AUDIT_FILES]
    paths.extend(
        [
            HANDOFF,
            AGENT526 / "coupled_delta_vs_m3.csv",
            AGENT526 / "candidate_admission_review.csv",
            AGENT526 / "README.md",
        ]
    )
    missing = [rel(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing TP/TW failure evidence: " + "; ".join(missing))


def split_values(value: str) -> list[str]:
    return [part for part in value.split(";") if part]


def infer_family(candidate_id: str, source_package: str = "") -> str:
    if "TSWFC1" in candidate_id:
        return "TSWFC1_bulk_to_ambient_series_resistance"
    if candidate_id.startswith("PB2"):
        return "PB2_local_passive_distribution"
    if candidate_id.startswith("PB3"):
        return "PB3_upcomer_test_section_attenuated"
    if candidate_id.startswith("WTD1"):
        return "WTD1_upcomer_test_section_pipe_wall_drive"
    if candidate_id.startswith("WTD2"):
        return "WTD2_upcomer_test_section_outer_surface_drive"
    if candidate_id.startswith("HS1"):
        return "HS1_heater_source_redistribution"
    if candidate_id.startswith("HIW1"):
        return "HIW1_heated_incline_pipe_wall_drive"
    if candidate_id.startswith("HIW2"):
        return "HIW2_heated_incline_outer_surface_drive"
    if candidate_id.startswith("TSC1"):
        return "TSC1_test_section_pipe_wall_drive"
    if candidate_id.startswith("TSC2"):
        return "TSC2_test_section_outer_surface_drive"
    return source_package or "unknown"


def rank_sensor_failures() -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "compared_rows": 0,
            "fail_rows": 0,
            "pass_rows": 0,
            "positive_deltas": [],
            "candidate_abs_errors": [],
            "m3_abs_errors": [],
            "candidate_families": set(),
            "cases": set(),
            "split_roles": set(),
            "worst": None,
            "source_paths": set(),
        }
    )
    for row in read_csv(AUDIT / "probe_residual_atlas.csv"):
        if row.get("comparison_status") != "compared":
            continue
        key = (row.get("sensor", ""), row.get("kind", ""), row.get("prediction_source_segment", ""))
        entry = grouped[key]
        entry["compared_rows"] += 1
        if row.get("probe_gate") == "fail":
            entry["fail_rows"] += 1
        elif row.get("probe_gate") == "pass":
            entry["pass_rows"] += 1
        candidate_family = row.get("candidate_family") or infer_family(row.get("candidate_id", ""), row.get("source_package", ""))
        entry["candidate_families"].add(candidate_family)
        entry["cases"].add(row.get("case_id", ""))
        entry["split_roles"].add(row.get("split_role", ""))
        entry["source_paths"].add(row.get("source_path", ""))
        delta = fnum(row.get("abs_error_delta_vs_m3_K"))
        if delta is not None:
            if delta > 0:
                entry["positive_deltas"].append(delta)
            worst = entry["worst"]
            if worst is None or delta > worst[0]:
                entry["worst"] = (delta, row)
        cand_abs = fnum(row.get("candidate_abs_error_K"))
        m3_abs = fnum(row.get("m3_abs_error_K"))
        if cand_abs is not None:
            entry["candidate_abs_errors"].append(cand_abs)
        if m3_abs is not None:
            entry["m3_abs_errors"].append(m3_abs)

    rows: list[dict[str, Any]] = []
    for (sensor, kind, segment), entry in grouped.items():
        compared = entry["compared_rows"]
        fail_rows = entry["fail_rows"]
        positive = entry["positive_deltas"]
        worst_delta, worst_row = entry["worst"] or (None, {})
        mean_positive = sum(positive) / len(positive) if positive else None
        mean_candidate_abs = (
            sum(entry["candidate_abs_errors"]) / len(entry["candidate_abs_errors"])
            if entry["candidate_abs_errors"]
            else None
        )
        mean_m3_abs = sum(entry["m3_abs_errors"]) / len(entry["m3_abs_errors"]) if entry["m3_abs_errors"] else None
        failure_score = (
            (fail_rows / compared if compared else 0.0) * 100.0
            + (worst_delta or 0.0)
            + (mean_positive or 0.0)
        )
        rows.append(
            {
                "rank": 0,
                "sensor": sensor,
                "kind": kind,
                "prediction_source_segment": segment,
                "compared_rows": compared,
                "fail_rows": fail_rows,
                "pass_rows": entry["pass_rows"],
                "fail_fraction": fmt(fail_rows / compared if compared else None),
                "candidate_families_failed": len(entry["candidate_families"]),
                "cases": ";".join(sorted(entry["cases"])),
                "split_roles": ";".join(sorted(entry["split_roles"])),
                "mean_candidate_abs_error_K": fmt(mean_candidate_abs),
                "mean_m3_abs_error_K": fmt(mean_m3_abs),
                "mean_positive_abs_error_delta_vs_m3_K": fmt(mean_positive),
                "worst_abs_error_delta_vs_m3_K": fmt(worst_delta),
                "worst_candidate_id": worst_row.get("candidate_id", ""),
                "worst_case_id": worst_row.get("case_id", ""),
                "evidence_read": evidence_read_for_sensor(kind, segment, sensor, fail_rows, compared),
                "required_physics": requirement_for_segment(kind, segment),
                "source_paths": ";".join(sorted(path for path in entry["source_paths"] if path)),
                "_score": failure_score,
            }
        )
    rows.sort(key=lambda row: (-float(row["_score"]), row["kind"], row["sensor"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
        row.pop("_score", None)
    return rows


def evidence_read_for_sensor(kind: str, segment: str, sensor: str, fail_rows: int, compared_rows: int) -> str:
    if segment == "heated_incline" and kind == "TW":
        return "scoreable heated-incline wall-temperature residual persists across tested wall/source families"
    if segment == "cooled_incline_pre_hx" and kind == "TW":
        return "cooled-incline pre-HX wall temperature regresses after upstream wall/source changes"
    if kind == "TP" and segment in {"left_upper_vertical", "test_section", "top_horizontal_exit"}:
        return "path-temperature shape failure in upper upcomer/test-section neighborhood"
    if compared_rows and fail_rows == compared_rows:
        return "all compared rows regress relative to M3"
    return "mixed or partial probe-level regression"


def requirement_for_segment(kind: str, segment: str) -> str:
    if segment == "heated_incline" and kind == "TW":
        return "energy-conserving upcomer/heated-incline stratification or exchange state; not another passive hA selector"
    if segment in {"left_upper_vertical", "test_section", "top_horizontal_exit"}:
        return "distributed upcomer/test-section axial energy state with finite TP outputs at scoreable probes"
    if segment.startswith("cooled_incline"):
        return "coupled upstream-to-HX thermal-shape preservation so cooler compensation does not create wall regressions"
    return "segment-local thermal-shape closure with TP/TW validation outputs"


def rank_role_segment_failures() -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "fail_rows": 0,
            "positive_deltas": [],
            "candidate_rmse": [],
            "m3_rmse": [],
            "candidate_families": set(),
            "cases": set(),
            "worst": None,
            "source_paths": set(),
        }
    )
    for row in read_csv(AUDIT / "role_segment_residual_atlas.csv"):
        key = (row.get("kind", ""), row.get("prediction_source_segment", ""))
        entry = grouped[key]
        entry["rows"] += 1
        family = row.get("candidate_family") or infer_family(row.get("candidate_id", ""), row.get("source_package", ""))
        entry["candidate_families"].add(family)
        entry["cases"].add(row.get("case_id", ""))
        entry["source_paths"].add(row.get("source_path", ""))
        delta = fnum(row.get("rmse_delta_vs_m3_K"))
        if delta is not None:
            if delta > 0:
                entry["fail_rows"] += 1
                entry["positive_deltas"].append(delta)
            worst = entry["worst"]
            if worst is None or delta > worst[0]:
                entry["worst"] = (delta, row)
        cand = fnum(row.get("candidate_rmse_K"))
        m3 = fnum(row.get("m3_rmse_K"))
        if cand is not None:
            entry["candidate_rmse"].append(cand)
        if m3 is not None:
            entry["m3_rmse"].append(m3)

    rows: list[dict[str, Any]] = []
    for (kind, segment), entry in grouped.items():
        positive = entry["positive_deltas"]
        mean_positive = sum(positive) / len(positive) if positive else None
        mean_candidate = sum(entry["candidate_rmse"]) / len(entry["candidate_rmse"]) if entry["candidate_rmse"] else None
        mean_m3 = sum(entry["m3_rmse"]) / len(entry["m3_rmse"]) if entry["m3_rmse"] else None
        worst_delta, worst_row = entry["worst"] or (None, {})
        score = (
            (entry["fail_rows"] / entry["rows"] if entry["rows"] else 0.0) * 100.0
            + (worst_delta or 0.0)
            + (mean_positive or 0.0)
        )
        rows.append(
            {
                "rank": 0,
                "kind": kind,
                "prediction_source_segment": segment,
                "role_segment_rows": entry["rows"],
                "fail_rows": entry["fail_rows"],
                "pass_rows": entry["rows"] - entry["fail_rows"],
                "fail_fraction": fmt(entry["fail_rows"] / entry["rows"] if entry["rows"] else None),
                "candidate_families_failed": len(entry["candidate_families"]),
                "cases": ";".join(sorted(entry["cases"])),
                "mean_candidate_rmse_K": fmt(mean_candidate),
                "mean_m3_rmse_K": fmt(mean_m3),
                "mean_positive_rmse_delta_vs_m3_K": fmt(mean_positive),
                "worst_rmse_delta_vs_m3_K": fmt(worst_delta),
                "worst_candidate_id": worst_row.get("candidate_id", ""),
                "worst_case_id": worst_row.get("case_id", ""),
                "evidence_read": evidence_read_for_sensor(kind, segment, "role_segment", entry["fail_rows"], entry["rows"]),
                "required_physics": requirement_for_segment(kind, segment),
                "source_paths": ";".join(sorted(path for path in entry["source_paths"] if path)),
                "_score": score,
            }
        )
    rows.sort(key=lambda row: (-float(row["_score"]), row["kind"], row["prediction_source_segment"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
        row.pop("_score", None)
    return rows


def combined_gate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(AUDIT / "cross_candidate_residual_matrix.csv"):
        item = dict(row)
        item["family_source"] = "AGENT-531_audit"
        rows.append(item)
    for row in read_csv(AGENT526 / "coupled_delta_vs_m3.csv"):
        item = {
            "source_package": "AGENT-526_test_section_wall_fluid_coupling",
            "candidate_id": row["candidate_id"],
            "candidate_family": infer_family(row["candidate_id"]),
            "case_id": row["case_id"],
            "split_role": row["split_role"],
            "mdot_delta_vs_m3_pct": row["mdot_delta_vs_m3_pct"],
            "tp_delta_vs_m3_K": row["tp_delta_vs_m3_K"],
            "tw_delta_vs_m3_K": row["tw_delta_vs_m3_K"],
            "all_probe_delta_vs_m3_K": row["all_probe_delta_vs_m3_K"],
            "score_gate": row["score_gate"],
            "gate_fail_dimensions": ";".join(gate_fail_dimensions_from_deltas(row)),
            "nearest_miss_dimension": nearest_positive_dimension(row),
            "failure_pattern": "mdot_improves_temperature_shape_fails",
            "source_path": rel(AGENT526 / "coupled_delta_vs_m3.csv"),
            "family_source": "AGENT-526_handoff_followthrough",
        }
        rows.append(item)
    return rows


def gate_fail_dimensions_from_deltas(row: dict[str, str]) -> list[str]:
    names = [
        ("mdot", "mdot_delta_vs_m3_pct"),
        ("tp", "tp_delta_vs_m3_K"),
        ("tw", "tw_delta_vs_m3_K"),
        ("all_probe", "all_probe_delta_vs_m3_K"),
    ]
    return [name for name, key in names if (fnum(row.get(key)) is not None and fnum(row.get(key)) > 0.0)]


def nearest_positive_dimension(row: dict[str, str]) -> str:
    values = []
    for name, key in [
        ("mdot", "mdot_delta_vs_m3_pct"),
        ("tp", "tp_delta_vs_m3_K"),
        ("tw", "tw_delta_vs_m3_K"),
        ("all_probe", "all_probe_delta_vs_m3_K"),
    ]:
        value = fnum(row.get(key))
        if value is not None and value > 0:
            values.append((value, name))
    return min(values)[1] if values else "all_available_dimensions_pass"


def candidate_family_gate_matrix() -> list[dict[str, Any]]:
    families: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": [],
            "candidate_ids": set(),
            "source_packages": set(),
            "source_paths": set(),
            "fail_dims": set(),
        }
    )
    for row in combined_gate_rows():
        family = row.get("candidate_family") or infer_family(row.get("candidate_id", ""), row.get("source_package", ""))
        entry = families[family]
        entry["rows"].append(row)
        entry["candidate_ids"].add(row.get("candidate_id", ""))
        entry["source_packages"].add(row.get("source_package", ""))
        entry["source_paths"].add(row.get("source_path", ""))
        entry["fail_dims"].update(split_values(row.get("gate_fail_dimensions", "")))

    rows: list[dict[str, Any]] = []
    for family, entry in families.items():
        matrix_rows = entry["rows"]
        score_fail_rows = sum(1 for row in matrix_rows if row.get("score_gate") == "fail")
        source_packages = sorted(package for package in entry["source_packages"] if package)
        worst = {
            "mdot": finite_max(fnum(row.get("mdot_delta_vs_m3_pct")) for row in matrix_rows),
            "tp": finite_max(fnum(row.get("tp_delta_vs_m3_K")) for row in matrix_rows),
            "tw": finite_max(fnum(row.get("tw_delta_vs_m3_K")) for row in matrix_rows),
            "all_probe": finite_max(fnum(row.get("all_probe_delta_vs_m3_K")) for row in matrix_rows),
        }
        rows.append(
            {
                "candidate_family": family,
                "source_packages": ";".join(source_packages),
                "candidate_count": len(entry["candidate_ids"]),
                "gate_rows": len(matrix_rows),
                "score_gate_pass_rows": len(matrix_rows) - score_fail_rows,
                "score_gate_fail_rows": score_fail_rows,
                "admission_status": "not_admitted",
                "worst_mdot_delta_vs_m3_pct": fmt(worst["mdot"]),
                "worst_tp_delta_vs_m3_K": fmt(worst["tp"]),
                "worst_tw_delta_vs_m3_K": fmt(worst["tw"]),
                "worst_all_probe_delta_vs_m3_K": fmt(worst["all_probe"]),
                "failed_dimensions": ";".join(sorted(entry["fail_dims"])),
                "family_gate": family_gate(family),
                "physics_implication": physics_implication(family),
                "do_not_repeat": do_not_repeat(family),
                "source_paths": ";".join(sorted(path for path in entry["source_paths"] if path)),
            }
        )
    rows.sort(key=lambda row: (row["family_gate"], row["candidate_family"]))
    return rows


def family_gate(family: str) -> str:
    if family == "TSWFC1_bulk_to_ambient_series_resistance":
        return "blocked_do_not_duplicate_single_node_wall_fluid_fallback"
    if family.startswith("PB") or family.startswith("WTD") or family.startswith("HIW") or family.startswith("TSC"):
        return "blocked_wall_state_or_passive_hA_retread"
    if family.startswith("HS1"):
        return "blocked_source_redistribution_insufficient"
    return "blocked_existing_family_not_admitted"


def physics_implication(family: str) -> str:
    if family == "TSWFC1_bulk_to_ambient_series_resistance":
        return "single bulk-to-ambient series resistance improves mdot but worsens TP/TW/all-probe; next wall/fluid model must be distributed and energy-conserving"
    if family.startswith("HS1"):
        return "source placement alone does not repair the persistent TP/TW shape failure"
    if family.startswith("PB"):
        return "passive heat-loss redistribution does not supply the missing axial/branch thermal state"
    if family.startswith("WTD") or family.startswith("HIW") or family.startswith("TSC"):
        return "wall-temperature drive selector changes are insufficient without a coupled axial/mixing state"
    return "existing family failed at least one coupled TP/TW/all-probe gate"


def do_not_repeat(family: str) -> str:
    if family == "TSWFC1_bulk_to_ambient_series_resistance":
        return "do not rerun AGENT-526 one-node bulk-to-ambient series-resistance model unchanged"
    if family.startswith("PB"):
        return "do not retry passive hA redistribution as the next Fluid grid"
    if family.startswith("HS1"):
        return "do not retune heater-source lambda against Salt3 or blind rows"
    return "do not launch another selector-only wall-state grid before the requirement contract is satisfied"


def physics_requirement_matrix(sensor_rows: list[dict[str, Any]], role_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top_sensor_paths = ";".join(sorted({path for row in sensor_rows[:6] for path in split_values(row.get("source_paths", ""))}))
    top_role_paths = ";".join(sorted({path for row in role_rows[:4] for path in split_values(row.get("source_paths", ""))}))
    return [
        {
            "requirement_id": "R1_upcomer_exchange_stratification",
            "priority": 1,
            "evidence_scope": "TW heated_incline plus TP upper-upcomer/test-section failures",
            "observed_failure": "TW5/TW6 and heated-incline role RMSE fail across passive wall distribution, wall-temperature drive, wall-circuit, and source families",
            "must_have_physics": "energy-conserving upcomer/heated-incline exchange or stratification state coupled to the main through-flow",
            "runtime_allowed_inputs": "setup geometry, segment lengths/elevations, material properties, ambient/radiation setup rows, heater and admitted cooler model inputs",
            "runtime_forbidden_inputs": "CFD mdot; realized CFD wallHeatFlux; imposed CFD cooler duty; validation TP/TW temperatures; Salt3/blind target leakage; finite rejected roots",
            "acceptance_gate": "accepted train roots and no worse than M3/best prior candidate on mdot, TP RMSE, TW RMSE, and all-probe RMSE for Salt3 plus declared blind/release gates",
            "matrix_consequence": "UMX1 is the first next-model lane; candidate grid must stay small until API/root contract passes",
            "source_paths": top_sensor_paths or top_role_paths,
        },
        {
            "requirement_id": "R2_distributed_wall_fluid_nodes",
            "priority": 2,
            "evidence_scope": "AGENT-526 TSWFC1 and AGENT-531 wall-state families",
            "observed_failure": "one-node test-section bulk-to-ambient series resistance completed but failed validation and holdout mdot/TP/TW/all-probe gates",
            "must_have_physics": "distributed axial wall/fluid nodes with inner wall, outer wall/surface, wall resistance, ambient/radiation ledgers, and energy conservation",
            "runtime_allowed_inputs": "setup-only wall dimensions/materials, hA/radiation/coverage rows, one predeclared global UA/contact multiplier if needed",
            "runtime_forbidden_inputs": "realized CFD test-section net heat, CFD wallHeatFlux, CFD mdot, imposed CFD cooler duty, validation temperatures",
            "acceptance_gate": "per-node heat ledger closes and TP/TW/all-probe gates do not regress on Salt3/holdout/blind rows",
            "matrix_consequence": "TSWFC2 is secondary; do not duplicate AGENT-526 single-node fallback",
            "source_paths": f"{rel(AGENT526 / 'coupled_delta_vs_m3.csv')};{rel(HANDOFF)}",
        },
        {
            "requirement_id": "R3_no_mdot_only_admission",
            "priority": 3,
            "evidence_scope": "candidate family gate matrix",
            "observed_failure": "many candidates improve mdot while TP, TW, and all-probe RMSE worsen",
            "must_have_physics": "model selection objective must include coupled thermal-shape gates, not only pressure-root mdot",
            "runtime_allowed_inputs": "predeclared train split metrics only for selection",
            "runtime_forbidden_inputs": "Salt3, perturbation, val_salt2, or new CFD rows for model form, lambda, root fallback, or sensor policy",
            "acceptance_gate": "zero admissions unless mdot, TP, TW, and all-probe gates all pass in the declared split contract",
            "matrix_consequence": "next grid must stop on accepted-root/runtime-audit failure and cannot expand from mdot-only improvement",
            "source_paths": f"{rel(AUDIT / 'admission_gate_sanity.csv')};{rel(AGENT526 / 'candidate_admission_review.csv')}",
        },
        {
            "requirement_id": "R4_sensor_policy_preservation",
            "priority": 4,
            "evidence_scope": "sensor failure rank and AGENT-531 sensor audit",
            "observed_failure": "TP2 and TW10 are policy/extraction exclusions, but TW5/TW6 are scoreable failures",
            "must_have_physics": "candidate must emit finite, scoreable TP/TW outputs at admitted sensor-map locations and may not hide failure by sensor exclusion",
            "runtime_allowed_inputs": "frozen sensor map/projection contract",
            "runtime_forbidden_inputs": "posthoc sensor correction, new exclusions chosen from candidate residuals, active-HX shell-state proxy for TW10",
            "acceptance_gate": "probe-localization table shows TW5/TW6 and upper-upcomer/test-section residuals move in the right direction without new compensation failures",
            "matrix_consequence": "sensor map is validation-only; the model must satisfy scoreable probes rather than changing policy",
            "source_paths": f"{rel(AUDIT / 'sensor_map_candidate_audit.csv')};{rel(AUDIT / 'invariant_failure_modes.csv')}",
        },
        {
            "requirement_id": "R5_salt_split_and_root_contract",
            "priority": 5,
            "evidence_scope": "weekend handoff blockers",
            "observed_failure": "AGENT-529 strict lane is blocked by Salt4 rejected roots, PB2 lacks Salt1 role rows, and blind adapters are missing",
            "must_have_physics": "pre-grid contract must define fit/selection rows, score-only rows, root acceptance, missing adapter handling, and no-go states",
            "runtime_allowed_inputs": "Salt1/Salt2/Salt4 nominal train rows only for selection under the handoff, with Salt3 and blind rows score-only",
            "runtime_forbidden_inputs": "finite rejected roots for admission; Salt3/blind rows for model selection; silent Salt1 omission",
            "acceptance_gate": "runtime audit passes, all train roots accepted, and missing Salt1/blind adapters become explicit release gates rather than implicit exclusions",
            "matrix_consequence": "build static UMX1 API/scenario contract before any full Fluid grid",
            "source_paths": rel(HANDOFF),
        },
    ]


def next_model_contract() -> list[dict[str, Any]]:
    return [
        {
            "contract_id": "UMX1_static_api_audit",
            "model_family": "UMX1_energy_conserving_upcomer_exchange",
            "sequence": 1,
            "action_before_grid": "audit Fluid for real upcomer/mixing/stratification/exchange hooks and emit scenario contracts",
            "fit_selection_rows": "Salt1/Salt2/Salt4 nominal only",
            "score_only_rows": "Salt3 nominal holdout; Salt2 +/-5Q; val_salt2; future admitted perturbation/external rows",
            "required_outputs": "case_split_contract.csv;candidate_definitions.csv;scenario_contracts.csv;runtime_input_audit.csv;training_objective_by_parameter.csv;nominal_coupled_scorecard.csv;salt3_holdout_delta_vs_m3.csv;probe_error_localization.csv;candidate_admission_review.csv",
            "hard_no_go": "missing Fluid hook; any forbidden runtime input; Salt4 rejected root; Salt3/blind leakage into model selection; mdot-only improvement",
            "admission_gate": "accepted roots plus mdot/TP/TW/all-probe no worse than M3 and best prior wall/source candidate",
            "why_now": "top ranked failures indicate axial/branch thermal-shape error rather than passive total heat-loss error",
            "source_paths": rel(HANDOFF),
        },
        {
            "contract_id": "UMX1_smoke_then_grid",
            "model_family": "UMX1_energy_conserving_upcomer_exchange",
            "sequence": 2,
            "action_before_grid": "run only one or two predeclared parameter values on compute resources after static API/root contract passes",
            "fit_selection_rows": "same as UMX1_static_api_audit",
            "score_only_rows": "Salt3 only after selected diagnostic parameter exists; blind rows only after adapters exist",
            "required_outputs": "runtime_request_audit.csv;root_status_by_case.csv;small_smoke_delta_vs_m3.csv;probe_error_localization.csv",
            "hard_no_go": "any rejected train root or missing scenario field stops expansion",
            "admission_gate": "smoke only cannot admit; it can only authorize bounded full-grid submission",
            "why_now": "prevents another expensive grid from discovering basic API/root failure late",
            "source_paths": rel(HANDOFF),
        },
        {
            "contract_id": "TSWFC2_distributed_wall_nodes",
            "model_family": "TSWFC2_distributed_test_section_wall_fluid_nodes",
            "sequence": 3,
            "action_before_grid": "use only if UMX1 API is unavailable or UMX1 fails cleanly; implement distributed nodes, not AGENT-526 single-node fallback",
            "fit_selection_rows": "Salt1/Salt2/Salt4 nominal only if Salt1 role rows exist; otherwise block explicitly",
            "score_only_rows": "Salt3 and blind/external rows",
            "required_outputs": "node_geometry_contract.csv;node_heat_ledger_contract.csv;runtime_input_audit.csv;candidate_admission_review.csv;probe_error_localization.csv",
            "hard_no_go": "missing Salt1 external-boundary role rows; realized heat use; no per-node energy ledger; duplicated one-node series resistance",
            "admission_gate": "per-node energy balance plus mdot/TP/TW/all-probe gates pass without new cooler/test-section compensation",
            "why_now": "AGENT-526 proved the single bulk-to-ambient series model is insufficient but a distributed wall/fluid model remains plausible",
            "source_paths": f"{rel(AGENT526 / 'README.md')};{rel(HANDOFF)}",
        },
        {
            "contract_id": "sensor_and_release_policy",
            "model_family": "all_next_wall_test_section_candidates",
            "sequence": 4,
            "action_before_grid": "freeze sensor policy and blind-row release gates before scorecard generation",
            "fit_selection_rows": "no sensor policy tuning from fit rows beyond existing frozen map",
            "score_only_rows": "TP2 restored only where finite scoreable output exists; TW10 excluded until active-HX shell-state exists",
            "required_outputs": "sensor_score_contract.csv;blind_perturbation_external_scorecard.csv;release_gate_decision.csv",
            "hard_no_go": "posthoc sensor exclusion or blind-row adapter omission without a release gate",
            "admission_gate": "scoreable TW5/TW6 and TP upper-upcomer/test-section probes improve or candidate remains non-admitted",
            "why_now": "the dominant residuals are scoreable sensors, not policy exclusions",
            "source_paths": f"{rel(AUDIT / 'sensor_map_candidate_audit.csv')};{rel(AUDIT / 'next_lane_decision.csv')}",
        },
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(AUDIT)}
  - {rel(HANDOFF)}
  - {rel(AGENT526 / 'coupled_delta_vs_m3.csv')}
tags: [forward-model, wall-test-section, tp-tw, failure-forensics, physics-requirements]
related:
  - .agent/status/{DATE}_{TASK}.md
  - .agent/journal/2026-07-18/tp-tw-failure-forensics.md
  - imports/2026-07-18_tp_tw_failure_forensics.json
  - operational_notes/maps/forward-predictive-model.md
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# TP/TW Failure Forensics

## Result

Decision for `predictive-wall-test-section-submodels`: `contract_first_no_grid`.

The package turns the wall/test-section failure evidence into a physics
requirement matrix before another Fluid grid is launched. It performs no
solver, scheduler, Fluid, fitting, tuning, registry, or scientific-admission
action.

## Counts

- Sensor failure rows: `{summary['sensor_failure_rows']}`.
- Role/segment failure rows: `{summary['role_segment_failure_rows']}`.
- Candidate family gate rows: `{summary['candidate_family_rows']}`.
- Physics requirements: `{summary['physics_requirement_rows']}`.
- Next-model contract rows: `{summary['next_model_contract_rows']}`.
- Admitted candidate families: `{summary['admitted_candidate_families']}`.

## Interpretation

The dominant scoreable failures are thermal-shape failures, not sensor-policy
artifacts. TP2 and TW10 remain policy/extraction exclusions, but TW5/TW6 and
heated-incline role RMSE are scoreable failures that persist across passive
wall redistribution, wall-temperature drive, wall-circuit, heater-source
redistribution, and the AGENT-526 single-node wall/fluid series fallback.

The next Fluid work should start with the `UMX1` static API/root/scenario
contract. A full grid is blocked until that contract shows accepted roots,
runtime legality, split discipline, and no mdot-only admission path. `TSWFC2`
distributed wall/fluid nodes are secondary and must not duplicate AGENT-526's
single bulk-to-ambient series-resistance model.

## Files

- `sensor_failure_rank.csv`
- `role_segment_failure_rank.csv`
- `candidate_family_gate_matrix.csv`
- `physics_requirement_matrix.csv`
- `next_model_contract.csv`
- `runtime_request_audit.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / 'summary.json')}
  - {rel(OUT / 'physics_requirement_matrix.csv')}
  - {rel(OUT / 'next_model_contract.csv')}
tags: [forward-model, wall-test-section, tp-tw, failure-forensics]
related:
  - {rel(OUT / 'README.md')}
  - .agent/journal/2026-07-18/tp-tw-failure-forensics.md
  - imports/2026-07-18_tp_tw_failure_forensics.json
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: status
status: complete
---
# {TASK} Status

## Objective

Turn TP/TW wall/test-section failure evidence into a physics requirement matrix
before another Fluid grid is launched.

## Outcome

Completed the static forensics package in `{rel(OUT)}`. The decision is
`contract_first_no_grid`: launch no new Fluid grid until UMX1 API/root/runtime
and split contracts pass.

## Changes Made

- `{rel(OUT / 'sensor_failure_rank.csv')}`
- `{rel(OUT / 'role_segment_failure_rank.csv')}`
- `{rel(OUT / 'candidate_family_gate_matrix.csv')}`
- `{rel(OUT / 'physics_requirement_matrix.csv')}`
- `{rel(OUT / 'next_model_contract.csv')}`
- `{rel(OUT / 'README.md')}`
- `{rel(STATUS)}`
- `{rel(JOURNAL)}`
- `{rel(IMPORT)}`
- `{rel(MAP)}` additive link/context update
- `.agent/STATE.md`, `.agent/catalog.json`, `.agent/catalog.csv`, `.agent/BLOCKERS.md`

## Validation

- `python3 -m unittest tools.analyze.test_tp_tw_failure_forensics`
- `python3 tools/docs/build_repo_index.py`
- `python3 tools/docs/build_repo_index.py --check`
- `python3.11 tools/agent/finish_task.py --task-id {TASK}`

## Guardrails

Native CFD/OpenFOAM outputs mutated: no. Registry/admission state mutated: no.
Scheduler action: no. Solver/postprocessing/Fluid launch: no. Fluid source edit:
no. Fitting/tuning/model selection: no. Scientific admission change:
`{summary['scientific_admission_change']}`.
"""
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(AUDIT / 'probe_residual_atlas.csv')}
  - {rel(AUDIT / 'role_segment_residual_atlas.csv')}
  - {rel(AUDIT / 'invariant_failure_modes.csv')}
  - {rel(HANDOFF)}
  - {rel(AGENT526 / 'coupled_delta_vs_m3.csv')}
tags: [forward-model, wall-test-section, tp-tw, failure-forensics]
related:
  - {rel(OUT / 'README.md')}
  - .agent/status/{DATE}_{TASK}.md
  - imports/2026-07-18_tp_tw_failure_forensics.json
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: journal
status: complete
---
# TP/TW Failure Forensics

## Attempted

Built an existing-evidence forensics package from AGENT-531 wall/test-section
blocker audit outputs and the AGENT-533 weekend handoff. Added the AGENT-526
single-node test-section wall/fluid fallback as a blocked candidate family,
because the handoff says it completed after the audit and must not be
duplicated unchanged.

## Observed

The sensor and role/segment ranks put heated-incline TW failures at the top of
the wall/test-section problem. Candidate families continue to improve mdot in
some rows while TP, TW, and all-probe errors worsen. AGENT-526 shows the same
pattern for the single-node wall/fluid series resistance.

## Inferred

The next requirement is an axial/branch thermal-shape mechanism, preferably an
energy-conserving upcomer exchange/stratification model. A distributed
test-section wall/fluid model remains plausible, but only as a second lane and
only if it is not the already-failed one-node bulk-to-ambient series model.

## Caveats

No new Fluid run was launched and no candidate was admitted. These matrices are
a pre-grid contract, not a replacement for coupled scorecards.

## Next Useful Actions

1. Audit Fluid for a real upcomer mixing/stratification/exchange hook.
2. Emit the UMX1 static API/scenario/root contract before any parameter grid.
3. Stop on missing hook, forbidden runtime input, Salt4 rejected root, or
   Salt3/blind leakage.

## Counts

Sensor rows: `{summary['sensor_failure_rows']}`. Role/segment rows:
`{summary['role_segment_failure_rows']}`. Candidate family rows:
`{summary['candidate_family_rows']}`. Physics requirement rows:
`{summary['physics_requirement_rows']}`. Next-model contract rows:
`{summary['next_model_contract_rows']}`.
"""
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(text, encoding="utf-8")


def write_manifest(summary: dict[str, Any], source_paths: list[str]) -> None:
    payload = {
        "task": TASK,
        "created_utc": utc_now(),
        "objective": "Turn TP/TW wall/test-section failure evidence into a physics requirement matrix before another Fluid grid.",
        "changed_files": [
            rel(OUT / "sensor_failure_rank.csv"),
            rel(OUT / "role_segment_failure_rank.csv"),
            rel(OUT / "candidate_family_gate_matrix.csv"),
            rel(OUT / "physics_requirement_matrix.csv"),
            rel(OUT / "next_model_contract.csv"),
            rel(OUT / "runtime_request_audit.csv"),
            rel(OUT / "source_manifest.csv"),
            rel(OUT / "summary.json"),
            rel(OUT / "README.md"),
            rel(STATUS),
            rel(JOURNAL),
            rel(IMPORT),
            "tools/analyze/build_tp_tw_failure_forensics.py",
            "tools/analyze/test_tp_tw_failure_forensics.py",
            rel(MAP),
            ".agent/STATE.md",
            ".agent/catalog.json",
            ".agent/catalog.csv",
            ".agent/BLOCKERS.md",
        ],
        "read_only_context": source_paths,
        "native_solver_outputs_mutated": False,
        "native_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "external_fluid_edit": False,
        "fluid_source_mutated": False,
        "fitting_or_model_selection_performed": False,
        "scientific_admission_change": summary["scientific_admission_change"],
        "summary": summary,
    }
    write_json(IMPORT, payload)


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [AUDIT / name for name in REQUIRED_AUDIT_FILES]
    paths.extend(
        [
            HANDOFF,
            AGENT526 / "coupled_delta_vs_m3.csv",
            AGENT526 / "candidate_admission_review.csv",
            AGENT526 / "README.md",
        ]
    )
    return [
        {
            "source_path": rel(path),
            "exists": str(path.exists()).lower(),
            "use": "read_only_evidence",
            "mutation": "none",
        }
        for path in paths
    ]


def runtime_request_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_item": "solver_or_postprocessing_launch",
            "status": "pass",
            "evidence": "builder reads existing CSV/markdown/json only",
        },
        {
            "audit_item": "scheduler_action",
            "status": "pass",
            "evidence": "no sbatch/srun/squeue/sacct action requested",
        },
        {
            "audit_item": "native_output_mutation",
            "status": "pass",
            "evidence": "all CFD/OpenFOAM/native outputs are read-only and untouched",
        },
        {
            "audit_item": "runtime_forbidden_inputs",
            "status": "pass",
            "evidence": "no candidate runtime was executed; matrix forbids CFD mdot, wallHeatFlux, imposed cooler duty, and validation temperatures",
        },
        {
            "audit_item": "scientific_admission_change",
            "status": "pass",
            "evidence": "all existing families remain not_admitted and blocker remains open",
        },
    ]


def build() -> dict[str, Any]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)

    sensor_rows = rank_sensor_failures()
    role_rows = rank_role_segment_failures()
    family_rows = candidate_family_gate_matrix()
    requirement_rows = physics_requirement_matrix(sensor_rows, role_rows)
    contract_rows = next_model_contract()
    runtime_rows = runtime_request_audit_rows()
    sources = source_manifest_rows()

    write_csv(
        OUT / "sensor_failure_rank.csv",
        sensor_rows,
        [
            "rank",
            "sensor",
            "kind",
            "prediction_source_segment",
            "compared_rows",
            "fail_rows",
            "pass_rows",
            "fail_fraction",
            "candidate_families_failed",
            "cases",
            "split_roles",
            "mean_candidate_abs_error_K",
            "mean_m3_abs_error_K",
            "mean_positive_abs_error_delta_vs_m3_K",
            "worst_abs_error_delta_vs_m3_K",
            "worst_candidate_id",
            "worst_case_id",
            "evidence_read",
            "required_physics",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "role_segment_failure_rank.csv",
        role_rows,
        [
            "rank",
            "kind",
            "prediction_source_segment",
            "role_segment_rows",
            "fail_rows",
            "pass_rows",
            "fail_fraction",
            "candidate_families_failed",
            "cases",
            "mean_candidate_rmse_K",
            "mean_m3_rmse_K",
            "mean_positive_rmse_delta_vs_m3_K",
            "worst_rmse_delta_vs_m3_K",
            "worst_candidate_id",
            "worst_case_id",
            "evidence_read",
            "required_physics",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "candidate_family_gate_matrix.csv",
        family_rows,
        [
            "candidate_family",
            "source_packages",
            "candidate_count",
            "gate_rows",
            "score_gate_pass_rows",
            "score_gate_fail_rows",
            "admission_status",
            "worst_mdot_delta_vs_m3_pct",
            "worst_tp_delta_vs_m3_K",
            "worst_tw_delta_vs_m3_K",
            "worst_all_probe_delta_vs_m3_K",
            "failed_dimensions",
            "family_gate",
            "physics_implication",
            "do_not_repeat",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "physics_requirement_matrix.csv",
        requirement_rows,
        [
            "requirement_id",
            "priority",
            "evidence_scope",
            "observed_failure",
            "must_have_physics",
            "runtime_allowed_inputs",
            "runtime_forbidden_inputs",
            "acceptance_gate",
            "matrix_consequence",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "next_model_contract.csv",
        contract_rows,
        [
            "contract_id",
            "model_family",
            "sequence",
            "action_before_grid",
            "fit_selection_rows",
            "score_only_rows",
            "required_outputs",
            "hard_no_go",
            "admission_gate",
            "why_now",
            "source_paths",
        ],
    )
    write_csv(OUT / "runtime_request_audit.csv", runtime_rows, ["audit_item", "status", "evidence"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_path", "exists", "use", "mutation"])

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "out_dir": rel(OUT),
        "decision": "contract_first_no_grid",
        "blocker_status": "open",
        "sensor_failure_rows": len(sensor_rows),
        "role_segment_failure_rows": len(role_rows),
        "candidate_family_rows": len(family_rows),
        "physics_requirement_rows": len(requirement_rows),
        "next_model_contract_rows": len(contract_rows),
        "admitted_candidate_families": 0,
        "top_sensor_failure": sensor_rows[0]["sensor"] if sensor_rows else "",
        "top_role_segment_failure": (
            f"{role_rows[0]['kind']}:{role_rows[0]['prediction_source_segment']}" if role_rows else ""
        ),
        "recommended_next_model": "UMX1_energy_conserving_upcomer_exchange",
        "secondary_model": "TSWFC2_distributed_test_section_wall_fluid_nodes",
        "scheduler_action": "none",
        "solver_or_postprocessing_launched": "none",
        "scientific_admission_change": "none",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status(summary)
    write_journal(summary)
    write_manifest(summary, [row["source_path"] for row in sources])
    return summary


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    main()
