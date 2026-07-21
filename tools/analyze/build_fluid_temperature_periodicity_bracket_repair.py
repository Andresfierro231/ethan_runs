#!/usr/bin/env python3
"""Audit finite rejected temperature-periodicity roots before a Fluid patch.

This package keeps the accepted-root gate strict. It replays the thermal
periodicity residual at the fixed UMX1 smoke mdot and expands only the starting
temperature scan window to determine whether Salt3/Salt4 are blocked by the
current Fluid scan ceiling.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FLUID_ROOT = (REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
if str(FLUID_ROOT) not in sys.path:
    sys.path.insert(0, str(FLUID_ROOT))

from tamu_loop_model_v2 import config_loader, solver as S  # noqa: E402
from tools.analyze import build_umx1_dry_smoke_scorer as umx1  # noqa: E402
from tools.analyze import run_predictive_forward_v0_imposed_cooler as forward_v0  # noqa: E402


TASK_ID = "TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR"
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair"
UMX1_PACKAGE = REPO_ROOT / "work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer"
AGENT529_PACKAGE = REPO_ROOT / "work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score"
FLUID_SOLVER = FLUID_ROOT / "tamu_loop_model_v2/solver.py"
TEMPERATURE_HARD_CEILING_K = 700.0
EXPANSION_DELTAS_K = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0, 89.0, 144.0)


AUDIT_COLUMNS = [
    "case_id",
    "candidate_id",
    "engine",
    "original_root_status",
    "original_accepted_for_validation",
    "original_pressure_residual_Pa",
    "original_temperature_periodicity_error_K",
    "mdot_kg_s",
    "original_start_temperature_K",
    "original_end_temperature_K",
    "initial_lower_K",
    "initial_upper_K",
    "initial_lower_residual_K",
    "initial_upper_residual_K",
    "expanded_lower_K",
    "expanded_upper_K",
    "bracket_found",
    "bracket_lower_K",
    "bracket_upper_K",
    "root_temperature_K",
    "root_residual_K",
    "required_upper_expansion_K",
    "repair_status",
    "fluid_patch_required",
    "next_action",
    "source_path",
]

SWEEP_COLUMNS = [
    "case_id",
    "candidate_id",
    "engine",
    "sample_index",
    "sample_role",
    "T0_K",
    "residual_K",
    "end_temperature_K",
    "qhx_total_W",
    "qambient_total_W",
    "predicted_air_outlet_temperature_K",
]

PRIOR_COLUMNS = [
    "source_task",
    "package",
    "artifact",
    "lane_id",
    "candidate_id",
    "case_id",
    "root_status",
    "accepted_case_count",
    "finite_case_count",
    "policy",
    "use_in_this_task",
]

DECISION_COLUMNS = [
    "gate_id",
    "status",
    "evidence",
    "decision",
    "next_action",
]
PATCH_CONTRACT_COLUMNS = [
    "patch_id",
    "target_repo",
    "target_file",
    "target_function",
    "current_behavior",
    "required_change",
    "invariants",
    "validation_command",
    "status",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def btext(value: Any) -> str:
    return "true" if bool(value) else "false"


def thermal_residual(
    case: S.ExperimentCase,
    scenario_segments: list[Any],
    sensors: list[Any],
    mdot_kg_s: float,
    scenario: S.ScenarioConfig,
    T0_K: float,
) -> dict[str, float]:
    segment_states, _sensor_preds, _sensor_prov, qamb, qhx, air_out = S.march_temperatures(
        case,
        scenario_segments,
        sensors,
        mdot_kg_s,
        float(T0_K),
        scenario,
        prescribed_segment_sources_W=None,
        prescribed_segment_losses_W=None,
    )
    residual = float(segment_states[-1].T_out_K) - float(T0_K)
    return {
        "T0_K": float(T0_K),
        "residual_K": residual,
        "end_temperature_K": float(segment_states[-1].T_out_K),
        "qhx_total_W": float(qhx),
        "qambient_total_W": float(qamb),
        "predicted_air_outlet_temperature_K": float(air_out),
    }


def bracket_from_samples(samples: Iterable[dict[str, float]]) -> tuple[dict[str, float], dict[str, float]] | None:
    ordered = sorted(samples, key=lambda row: row["T0_K"])
    for prev, curr in zip(ordered[:-1], ordered[1:]):
        r0 = float(prev["residual_K"])
        r1 = float(curr["residual_K"])
        if r0 == 0.0:
            return prev, prev
        if r0 * r1 <= 0.0:
            return prev, curr
    return None


def bisection_root(
    case: S.ExperimentCase,
    scenario_segments: list[Any],
    sensors: list[Any],
    mdot_kg_s: float,
    scenario: S.ScenarioConfig,
    lo: dict[str, float],
    hi: dict[str, float],
) -> dict[str, float]:
    T_lo = float(lo["T0_K"])
    T_hi = float(hi["T0_K"])
    r_lo = float(lo["residual_K"])
    if T_lo == T_hi:
        return dict(lo)
    best = dict(min((lo, hi), key=lambda row: abs(float(row["residual_K"]))))
    for _ in range(32):
        T_mid = 0.5 * (T_lo + T_hi)
        mid = thermal_residual(case, scenario_segments, sensors, mdot_kg_s, scenario, T_mid)
        best = mid
        r_mid = float(mid["residual_K"])
        if abs(r_mid) <= 1.0e-9:
            return mid
        if r_lo * r_mid <= 0.0:
            T_hi = T_mid
        else:
            T_lo = T_mid
            r_lo = r_mid
    return best


def classify_repair(initial_hi: float, bracket: tuple[dict[str, float], dict[str, float]] | None) -> tuple[str, bool, float | None]:
    if bracket is None:
        return "no_bracket_before_hard_ceiling", True, None
    upper = max(float(bracket[0]["T0_K"]), float(bracket[1]["T0_K"]))
    expansion = max(0.0, upper - initial_hi)
    if expansion > 1.0e-9:
        return "upper_bound_too_low_root_recovered", True, expansion
    return "already_bracketed_by_current_bounds", False, 0.0


def audit_one_row(
    smoke_row: dict[str, str],
    case_input: dict[str, str],
    candidate: dict[str, Any],
    case: S.ExperimentCase,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scenario = umx1.scenario_for(case_input, candidate)
    _geometry_segments, sensors, scenario_segments = forward_v0.build_solver_segments_and_sensors(case, scenario)
    mdot = fnum(smoke_row["mdot_kg_s"])
    if mdot is None:
        raise ValueError(f"missing mdot for {smoke_row['case_id']} {smoke_row['candidate_id']}")

    initial_lo, initial_hi = S._temperature_scan_bounds(case, scenario, mdot, prescribed_segment_sources_W=None)
    raw_samples: list[dict[str, float]] = [
        thermal_residual(case, scenario_segments, sensors, mdot, scenario, initial_lo),
        thermal_residual(case, scenario_segments, sensors, mdot, scenario, initial_hi),
    ]
    sample_roles = {initial_lo: "initial_lower", initial_hi: "initial_upper"}
    bracket = bracket_from_samples(raw_samples)

    if bracket is None:
        lo_res = float(raw_samples[0]["residual_K"])
        hi_res = float(raw_samples[1]["residual_K"])
        if lo_res > 0.0 and hi_res > 0.0:
            for delta in EXPANSION_DELTAS_K:
                T0 = min(TEMPERATURE_HARD_CEILING_K, initial_hi + delta)
                if T0 <= max(row["T0_K"] for row in raw_samples):
                    continue
                raw_samples.append(thermal_residual(case, scenario_segments, sensors, mdot, scenario, T0))
                sample_roles[T0] = "expanded_upper"
                bracket = bracket_from_samples(raw_samples)
                if bracket is not None or T0 >= TEMPERATURE_HARD_CEILING_K:
                    break
        elif lo_res < 0.0 and hi_res < 0.0:
            for delta in EXPANSION_DELTAS_K:
                T0 = max(250.0, initial_lo - delta)
                if T0 >= min(row["T0_K"] for row in raw_samples):
                    continue
                raw_samples.append(thermal_residual(case, scenario_segments, sensors, mdot, scenario, T0))
                sample_roles[T0] = "expanded_lower"
                bracket = bracket_from_samples(raw_samples)
                if bracket is not None or T0 <= 250.0:
                    break

    root = None
    if bracket is not None:
        root = bisection_root(case, scenario_segments, sensors, mdot, scenario, bracket[0], bracket[1])

    repair_status, patch_required, required_upper_expansion = classify_repair(initial_hi, bracket)
    ordered_samples = sorted(raw_samples, key=lambda row: row["T0_K"])
    sweep_rows = []
    for idx, sample in enumerate(ordered_samples):
        T0 = float(sample["T0_K"])
        sweep_rows.append(
            {
                "case_id": smoke_row["case_id"],
                "candidate_id": smoke_row["candidate_id"],
                "engine": smoke_row["engine"],
                "sample_index": idx,
                "sample_role": sample_roles.get(T0, "expanded"),
                **sample,
            }
        )

    initial_lower_residual = next(row["residual_K"] for row in ordered_samples if row["T0_K"] == initial_lo)
    initial_upper_residual = next(row["residual_K"] for row in ordered_samples if row["T0_K"] == initial_hi)
    audit = {
        "case_id": smoke_row["case_id"],
        "candidate_id": smoke_row["candidate_id"],
        "engine": smoke_row["engine"],
        "original_root_status": smoke_row["root_status"],
        "original_accepted_for_validation": smoke_row["accepted_for_validation"],
        "original_pressure_residual_Pa": smoke_row["pressure_residual_Pa"],
        "original_temperature_periodicity_error_K": smoke_row["temperature_periodicity_error_K"],
        "mdot_kg_s": mdot,
        "original_start_temperature_K": smoke_row["start_temperature_K"],
        "original_end_temperature_K": smoke_row["end_temperature_K"],
        "initial_lower_K": initial_lo,
        "initial_upper_K": initial_hi,
        "initial_lower_residual_K": initial_lower_residual,
        "initial_upper_residual_K": initial_upper_residual,
        "expanded_lower_K": min(row["T0_K"] for row in ordered_samples),
        "expanded_upper_K": max(row["T0_K"] for row in ordered_samples),
        "bracket_found": btext(bracket is not None),
        "bracket_lower_K": "" if bracket is None else min(bracket[0]["T0_K"], bracket[1]["T0_K"]),
        "bracket_upper_K": "" if bracket is None else max(bracket[0]["T0_K"], bracket[1]["T0_K"]),
        "root_temperature_K": "" if root is None else root["T0_K"],
        "root_residual_K": "" if root is None else root["residual_K"],
        "required_upper_expansion_K": required_upper_expansion,
        "repair_status": repair_status,
        "fluid_patch_required": btext(patch_required),
        "next_action": "patch Fluid thermal bracket expansion and rerun strict scorer"
        if patch_required and bracket is not None
        else "keep current strict root gate",
        "source_path": rel(UMX1_PACKAGE / "umx1_smoke_results.csv"),
    }
    return audit, sweep_rows


def prior_rejected_root_context() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    nominal_path = AGENT529_PACKAGE / "nominal_coupled_scorecard.csv"
    if nominal_path.exists():
        for row in read_csv(nominal_path):
            if row.get("case_id") == "salt_4" and row.get("root_status") == "rejected":
                rows.append(
                    {
                        "source_task": "AGENT-529",
                        "package": rel(AGENT529_PACKAGE),
                        "artifact": "nominal_coupled_scorecard.csv",
                        "lane_id": row.get("lane_id", ""),
                        "candidate_id": row.get("candidate_id", ""),
                        "case_id": row.get("case_id", ""),
                        "root_status": row.get("root_status", ""),
                        "accepted_case_count": "",
                        "finite_case_count": "",
                        "policy": "finite rejected roots were diagnostic only",
                        "use_in_this_task": "prior blocker context, not replayed admission evidence",
                    }
                )
    objective_path = AGENT529_PACKAGE / "training_objective_by_lambda.csv"
    if objective_path.exists():
        for row in read_csv(objective_path):
            if row.get("completed_accepted_case_count") != row.get("required_train_case_count"):
                rows.append(
                    {
                        "source_task": "AGENT-529",
                        "package": rel(AGENT529_PACKAGE),
                        "artifact": "training_objective_by_lambda.csv",
                        "lane_id": row.get("lane_id", ""),
                        "candidate_id": row.get("candidate_id", ""),
                        "case_id": "salt_1,salt_2,salt_4",
                        "root_status": "selection_blocked_by_rejected_train_root",
                        "accepted_case_count": row.get("completed_accepted_case_count", ""),
                        "finite_case_count": row.get("completed_finite_case_count", ""),
                        "policy": row.get("root_status_policy", ""),
                        "use_in_this_task": "confirms strict accepted-root policy was already documented",
                    }
                )
    return rows


def decision_rows(audit_rows: list[dict[str, Any]], prior_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failed_current = [row for row in audit_rows if row["repair_status"] == "upper_bound_too_low_root_recovered"]
    no_bracket = [row for row in audit_rows if row["repair_status"] == "no_bracket_before_hard_ceiling"]
    strict_prior = bool(prior_rows)
    rows = [
        {
            "gate_id": "runtime_legality",
            "status": "pass",
            "evidence": "UMX1 smoke package already passed runtime/split guardrails; this audit only changes thermal scan evidence.",
            "decision": "unchanged",
            "next_action": "do not add forbidden runtime inputs",
        },
        {
            "gate_id": "accepted_root_policy",
            "status": "pass" if strict_prior else "warn",
            "evidence": f"{len(prior_rows)} AGENT-529 context rows preserve finite rejected roots as diagnostic-only.",
            "decision": "do_not_relax_gate",
            "next_action": "rerun strict scorer after Fluid patch",
        },
        {
            "gate_id": "thermal_bracket_repair",
            "status": "pass" if failed_current and not no_bracket else "blocked",
            "evidence": f"{len(failed_current)} rows recover a thermal bracket above the current Fluid upper bound; {len(no_bracket)} rows do not.",
            "decision": "patch_required" if failed_current and not no_bracket else "needs_more_diagnosis",
            "next_action": "claim non-conflicting external Fluid row and add adaptive high-side temperature bracket expansion",
        },
        {
            "gate_id": "admission",
            "status": "not_admitted",
            "evidence": "Audit package produces no fitted candidate and no score-grid expansion.",
            "decision": "no_admission",
            "next_action": "full grid remains blocked until refreshed roots/conservation pass strict smoke",
        },
    ]
    return rows


def patch_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "patch_id": "fluid_temperature_periodicity_adaptive_upper_bracket_v1",
            "target_repo": str(FLUID_ROOT.parents[1]),
            "target_file": "tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py",
            "target_function": "solve_temperature_periodicity",
            "current_behavior": "_temperature_scan_bounds caps Salt3/Salt4 UMX1 smoke at about 550 K, returns no_bracketed_temperature_periodicity_root while residual remains positive.",
            "required_change": "After the initial scan finds no bracket and both endpoint residuals have the same sign, expand the relevant temperature bound in bounded increments until a sign change or hard ceiling, then use the existing bisection path.",
            "invariants": "Do not change ScenarioConfig API, TEMPERATURE_PERIODICITY_TOL_K, pressure-root acceptance, validity gates, UMX conservation, split discipline, or admission policy.",
            "validation_command": "cd tamu_first_order_model/Fluid && python -m pytest tests/test_solver_contracts.py -q -k 'temperature or scenario_config_defaults_match_active_solver_contract'; then rerun Ethan UMX1 smoke strict validation.",
            "status": "ready_deferred_until_external_solver_owner_clears",
        }
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_type": "umx1_smoke_results",
            "path": rel(UMX1_PACKAGE / "umx1_smoke_results.csv"),
            "used_for": "fixed-mdot thermal bracket replay",
            "mutation_status": "read_only_existing_evidence",
        },
        {
            "source_type": "agent529_root_policy",
            "path": rel(AGENT529_PACKAGE),
            "used_for": "prior finite rejected root policy context",
            "mutation_status": "read_only_existing_evidence",
        },
        {
            "source_type": "fluid_solver",
            "path": str(FLUID_SOLVER),
            "used_for": "read-only march_temperatures and current _temperature_scan_bounds audit",
            "mutation_status": "read_only_due_active_external_solver_owner",
        },
    ]


def build(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    smoke_path = UMX1_PACKAGE / "umx1_smoke_results.csv"
    if not smoke_path.exists():
        raise FileNotFoundError(f"missing UMX1 smoke results: {smoke_path}")

    smoke_rows = read_csv(smoke_path)
    case_inputs = {row["case_id"]: row for row in umx1.case_input_rows()}
    candidates = {row["candidate_id"]: row for row in umx1.candidate_rows()}
    cases = {case.name: case for case in config_loader.load_cases()}

    audit_rows: list[dict[str, Any]] = []
    sweep_rows: list[dict[str, Any]] = []
    for smoke_row in smoke_rows:
        case_id = smoke_row["case_id"]
        candidate_id = smoke_row["candidate_id"]
        if case_id not in case_inputs or candidate_id not in candidates:
            continue
        case_input = case_inputs[case_id]
        audit, sweep = audit_one_row(smoke_row, case_input, candidates[candidate_id], cases[case_input["fluid_case_name"]])
        audit_rows.append(audit)
        sweep_rows.extend(sweep)

    prior_rows = prior_rejected_root_context()
    decisions = decision_rows(audit_rows, prior_rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "audit_complete",
        "umx1_rows_audited": len(audit_rows),
        "current_bound_already_bracketed_rows": sum(row["repair_status"] == "already_bracketed_by_current_bounds" for row in audit_rows),
        "upper_bound_recovered_rows": sum(row["repair_status"] == "upper_bound_too_low_root_recovered" for row in audit_rows),
        "no_bracket_before_hard_ceiling_rows": sum(row["repair_status"] == "no_bracket_before_hard_ceiling" for row in audit_rows),
        "prior_context_rows": len(prior_rows),
        "fluid_source_edit_status": "deferred_active_external_solver_owner",
        "admission_status": "not_admitted_audit_only",
    }

    write_csv(out_dir / "temperature_root_bound_audit.csv", audit_rows, AUDIT_COLUMNS)
    write_csv(out_dir / "temperature_root_sweep.csv", sweep_rows, SWEEP_COLUMNS)
    write_csv(out_dir / "prior_rejected_root_context.csv", prior_rows, PRIOR_COLUMNS)
    write_csv(out_dir / "root_repair_decision.csv", decisions, DECISION_COLUMNS)
    write_csv(out_dir / "fluid_patch_contract.csv", patch_contract_rows(), PATCH_CONTRACT_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", source_manifest_rows(), ["source_type", "path", "used_for", "mutation_status"])
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def validate_existing(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    required = [
        out_dir / "temperature_root_bound_audit.csv",
        out_dir / "temperature_root_sweep.csv",
        out_dir / "prior_rejected_root_context.csv",
        out_dir / "root_repair_decision.csv",
        out_dir / "fluid_patch_contract.csv",
        out_dir / "source_manifest.csv",
        out_dir / "summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing audit outputs: " + ", ".join(rel(path) for path in missing))
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    audit_rows = read_csv(out_dir / "temperature_root_bound_audit.csv")
    if int(summary["umx1_rows_audited"]) != len(audit_rows):
        raise ValueError("summary row count does not match temperature_root_bound_audit.csv")
    recovered = [row for row in audit_rows if row["repair_status"] == "upper_bound_too_low_root_recovered"]
    if not recovered:
        raise ValueError("audit did not recover any above-ceiling Salt3/Salt4 thermal roots")
    if any(row["case_id"] in {"salt_3", "salt_4"} and row["bracket_found"] != "true" for row in audit_rows):
        raise ValueError("at least one Salt3/Salt4 row still lacks a recovered thermal bracket")
    return summary


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(UMX1_PACKAGE)}
  - {rel(AGENT529_PACKAGE)}
  - {str(FLUID_SOLVER)}
tags: [fluid, temperature-periodicity, root-bracket, umx1, no-admission]
related:
  - .agent/status/2026-07-18_TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR.md
  - .agent/journal/2026-07-18/fluid-temperature-periodicity-bracket-repair.md
task: {TASK_ID}
date: 2026-07-18
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: audit_complete
---

# Fluid Temperature Periodicity Bracket Repair Audit

Generated: `{summary['generated_at']}`

## Result

Status: `{summary['status']}`.

This package audits the finite but rejected Salt3/Salt4 temperature periodicity
rows from the UMX1 smoke scorer. It does not relax accepted-root policy, does
not fit or select a model, and does not admit any candidate.

## Key Counts

- UMX1 rows audited: `{summary['umx1_rows_audited']}`.
- Already bracketed by current Fluid bounds: `{summary['current_bound_already_bracketed_rows']}`.
- Roots recovered above current upper bound: `{summary['upper_bound_recovered_rows']}`.
- No bracket before hard ceiling: `{summary['no_bracket_before_hard_ceiling_rows']}`.
- Prior AGENT-529 root-policy context rows: `{summary['prior_context_rows']}`.
- Fluid source edit status: `{summary['fluid_source_edit_status']}`.
- Admission status: `{summary['admission_status']}`.

## Files

- `temperature_root_bound_audit.csv`
- `temperature_root_sweep.csv`
- `prior_rejected_root_context.csv`
- `root_repair_decision.csv`
- `fluid_patch_contract.csv`
- `source_manifest.csv`
- `summary.json`

## Interpretation

If Salt3/Salt4 rows recover brackets only above the current Fluid upper
temperature bound, the next non-conflicting external Fluid task should add
adaptive high-side expansion inside `solve_temperature_periodicity()`. The
strict accepted-root gate must remain unchanged and this package remains
audit-only.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--validate-existing", action="store_true")
    args = parser.parse_args()
    summary = validate_existing(args.output_dir) if args.validate_existing else build(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
