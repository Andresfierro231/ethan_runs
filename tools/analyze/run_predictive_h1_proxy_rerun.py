#!/usr/bin/env python3
"""Run a bounded H1-like hydraulic proxy screen.

This is not a faithful localized H1 implementation. Current Fluid only exposes
aggregate MinorLosses, so this runner uses Salt2 train finite fit-target
`K_local` rows as a single fixed-K proxy and labels all outputs accordingly.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import run_predictive_forward_v0_imposed_cooler as base  # noqa: E402

DATE_DIR = ROOT / "work_products/2026-07/2026-07-13"
OUT_DIR = DATE_DIR / "2026-07-13_predictive_h1_proxy_rerun"
NAMED_LOSS_TABLE = DATE_DIR / "2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv"
AGENT_299_DIR = DATE_DIR / "2026-07-13_predictive_parallel_execution_coordination"

PROXY_RESULT_COLUMNS = base.RESULT_COLUMNS + [
    "hydraulic_variant",
    "h1_proxy_label",
    "minor_loss_total_fixed_K",
    "minor_loss_source_policy",
    "thermal_fit_used",
    "publication_closure_allowed",
]
K_SOURCE_COLUMNS = [
    "case_id",
    "name",
    "loss_class",
    "span_or_feature",
    "fit_use_status",
    "K_local",
    "included_in_proxy",
    "exclusion_reason",
    "quality_flags",
    "source_path",
]
PLAN_COLUMNS = [
    "case_id",
    "variant_id",
    "base_variant_id",
    "engine",
    "minor_loss_total_fixed_K",
    "h1_proxy_label",
    "runtime_policy",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def fnum(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def k_source_rows(path: Path = NAMED_LOSS_TABLE) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        k_local = fnum(row.get("K_local"))
        included = (
            row.get("case_id") == "salt_2"
            and row.get("fit_use_status") == "fit_target"
            and k_local is not None
        )
        if included:
            reason = ""
        elif row.get("case_id") != "salt_2":
            reason = "validation_or_holdout_rows_not_used_for_proxy_training"
        elif row.get("fit_use_status") != "fit_target":
            reason = "not_fit_target"
        else:
            reason = "K_local_not_finite"
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "name": row.get("name", ""),
                "loss_class": row.get("loss_class", ""),
                "span_or_feature": row.get("span_or_feature", ""),
                "fit_use_status": row.get("fit_use_status", ""),
                "K_local": k_local,
                "included_in_proxy": "yes" if included else "no",
                "exclusion_reason": reason,
                "quality_flags": row.get("quality_flags", ""),
                "source_path": row.get("source_path", ""),
            }
        )
    return rows


def proxy_k_total(rows: list[dict[str, Any]]) -> float:
    values = [float(row["K_local"]) for row in rows if row.get("included_in_proxy") == "yes"]
    if not values:
        raise ValueError("no finite Salt2 fit-target K_local rows for H1 proxy")
    return sum(values)


def proxy_minor_losses(total_fixed_k: float) -> base.S.MinorLosses:
    return base.S.MinorLosses(
        major_loss_multiplier=1.0,
        k_90deg=float(total_fixed_k),
        n_90deg=1,
        k_20deg=0.0,
        n_20deg=0,
        include_test_section_diameter_change=True,
    )


def fast_pressure_root_proxy(
    case: base.S.ExperimentCase,
    scenario: base.S.ScenarioConfig,
    prescribed_sources: dict[str, float] | None,
    minor_losses: base.S.MinorLosses,
    *,
    bisection_iterations: int = 4,
) -> Any:
    geometry_segments, geometry_sensors, scenario_segments = base.build_solver_segments_and_sensors(case, scenario)
    grid = [
        value
        for value in base.FAST_MDOT_GRID
        if scenario.mdot_search_lower_kg_s <= value <= scenario.mdot_search_upper_kg_s
    ]
    if scenario.mdot_search_lower_kg_s not in grid:
        grid.insert(0, scenario.mdot_search_lower_kg_s)
    if scenario.mdot_search_upper_kg_s not in grid:
        grid.append(scenario.mdot_search_upper_kg_s)
    grid = sorted(set(grid))

    evaluations: list[dict[str, Any]] = []
    for mdot in grid:
        evaluations.append(
            base.S.pressure_residual(
                float(mdot),
                case,
                scenario_segments,
                geometry_sensors,
                scenario,
                minor_losses,
                prescribed_segment_sources_W=prescribed_sources,
            )
        )
    finite = [row for row in evaluations if math.isfinite(float(row["pressure_residual_Pa"]))]
    if not finite:
        raise ValueError(f"No finite pressure residuals for {case.name} {scenario.name}")

    bracket: tuple[dict[str, Any], dict[str, Any]] | None = None
    for prev, curr in zip(finite[:-1], finite[1:]):
        r0 = float(prev["pressure_residual_Pa"])
        r1 = float(curr["pressure_residual_Pa"])
        if r0 == 0.0 or r0 * r1 <= 0.0:
            bracket = (prev, curr)
            break

    selected = min(finite, key=lambda row: abs(float(row["pressure_residual_Pa"])))
    root_status = "fast_scan_best_residual_no_pressure_bracket"
    root_rejection_reason = "no_bracketed_pressure_root"
    pressure_root_bracketed = False
    if bracket is not None:
        pressure_root_bracketed = True
        lo, hi = bracket
        mdot_lo = float(lo["mdot_kg_s"])
        mdot_hi = float(hi["mdot_kg_s"])
        r_lo = float(lo["pressure_residual_Pa"])
        selected = min((lo, hi), key=lambda row: abs(float(row["pressure_residual_Pa"])))
        for _ in range(bisection_iterations):
            mdot_mid = 0.5 * (mdot_lo + mdot_hi)
            mid = base.S.pressure_residual(
                mdot_mid,
                case,
                scenario_segments,
                geometry_sensors,
                scenario,
                minor_losses,
                warm_start_temperature_K=float(selected["thermal"].start_temperature_K),
                prescribed_segment_sources_W=prescribed_sources,
            )
            r_mid = float(mid["pressure_residual_Pa"])
            selected = mid
            if r_lo * r_mid <= 0.0:
                mdot_hi = mdot_mid
            else:
                mdot_lo = mdot_mid
                r_lo = r_mid
        root_status = "fast_scan_bracketed_pressure_root"
        root_rejection_reason = ""

    thermal = selected["thermal"]
    dp_b = float(selected["deltaP_buoyancy_Pa"])
    dp_l = float(selected["deltaP_losses_Pa"])
    pressure_residual_pa = float(selected["pressure_residual_Pa"])
    pressure_tol = base.legacy_replay.pressure_tolerance(base.S, dp_b, dp_l)
    accepted = (
        pressure_root_bracketed
        and abs(pressure_residual_pa) <= pressure_tol
        and bool(thermal.root_found)
        and abs(float(thermal.temperature_periodicity_error_K)) <= float(base.S.TEMPERATURE_PERIODICITY_TOL_K)
    )
    return SimpleNamespace(
        scenario=scenario,
        case=case,
        mdot_kg_s=float(selected["mdot_kg_s"]),
        velocity_main_m_s=float(selected["velocity_main_m_s"]),
        reynolds_main=float(selected["reynolds_main"]),
        friction_factor_main=float(selected["friction_factor_main"]),
        deltaP_buoyancy_Pa=dp_b,
        deltaP_losses_Pa=dp_l,
        pressure_residual_Pa=pressure_residual_pa,
        qhx_total_W=float(thermal.qhx_total_W),
        qambient_total_W=float(thermal.qambient_total_W),
        predicted_air_outlet_temperature_K=float(thermal.predicted_air_outlet_temperature_K),
        start_temperature_K=float(thermal.start_temperature_K),
        end_temperature_K=float(thermal.end_temperature_K),
        temperature_periodicity_error_K=float(thermal.temperature_periodicity_error_K),
        sensor_predictions_K=thermal.sensor_predictions_K,
        sensor_prediction_provenance=thermal.sensor_prediction_provenance,
        segment_states=thermal.segment_states,
        geometry_segments=geometry_segments,
        geometry_sensors=geometry_sensors,
        root_status=root_status,
        root_rejection_reason=root_rejection_reason,
        accepted_for_validation=accepted,
        validity_status="not_evaluated_fast_scan_h1_proxy",
        validity_rejection_reason="screen_only_not_publication_closure",
        imported_source_total_W=0.0,
        imported_segment_loss_total_W=0.0,
    )


def run_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    contract_summary = base.load_or_build_contract(base.CONTRACT_DIR, strict=True)
    case_inputs = base.read_csv(base.CONTRACT_DIR / "case_runtime_inputs_forward_v0.csv")
    targets = base.target_by_case()
    cases = {case.name: case for case in base.config_loader.load_cases()}
    validation_records = base.config_loader.load_validation_records()
    k_rows = k_source_rows()
    total_k = proxy_k_total(k_rows)
    minor_losses = proxy_minor_losses(total_k)

    results: list[dict[str, Any]] = []
    plan: list[dict[str, Any]] = []
    for case_input in case_inputs:
        case = cases[case_input["fluid_case_name"]]
        validation_record = validation_records.get(case.name)
        target = targets.get(case_input["case_id"], {})
        for spec in base.variant_specs():
            base_variant = spec["variant_id"]
            variant_id = f"{base_variant}_H1_proxy"
            scenario = base.scenario_for(case_input, base_variant)
            scenario = replace(scenario, name=f"forward_v0_{variant_id}")
            prescribed = base.prescribed_sources_for(case, base_variant)
            result = fast_pressure_root_proxy(case, scenario, prescribed, minor_losses)
            row = base.result_row(result, case_input, variant_id, "fast_scan_h1_proxy", prescribed, validation_record, target)
            row.update(
                {
                    "hydraulic_variant": "H1_aggregate_fixed_K_proxy",
                    "h1_proxy_label": "screen_only_not_publication_closure",
                    "minor_loss_total_fixed_K": total_k,
                    "minor_loss_source_policy": "salt2_train_finite_fit_target_K_local_sum",
                    "thermal_fit_used": "false",
                    "publication_closure_allowed": "false",
                }
            )
            results.append(row)
            plan.append(
                {
                    "case_id": case_input["case_id"],
                    "variant_id": variant_id,
                    "base_variant_id": base_variant,
                    "engine": "fast_scan_h1_proxy",
                    "minor_loss_total_fixed_K": total_k,
                    "h1_proxy_label": "screen_only_not_publication_closure",
                    "runtime_policy": "no CFD mdot, no sensor targets, no thermal fitting; K trained from Salt2 named-loss table only",
                }
            )

    variant_summary = base.variant_summary_rows(results)
    write_csv(out_dir / "h1_proxy_run_plan.csv", plan, PLAN_COLUMNS)
    write_csv(out_dir / "h1_proxy_results.csv", results, PROXY_RESULT_COLUMNS)
    write_csv(out_dir / "h1_proxy_variant_summary.csv", variant_summary, base.VARIANT_SUMMARY_COLUMNS)
    write_csv(out_dir / "h1_proxy_k_source.csv", k_rows, K_SOURCE_COLUMNS)

    accepted = sum(1 for row in results if str(row.get("accepted_for_validation", "")).lower() == "true")
    summary = {
        "task_id": "AGENT-308",
        "generated_utc": utc_now(),
        "overall_status": "h1_proxy_screen_complete_not_publication_closure",
        "engine": "fast_scan_h1_proxy",
        "minor_loss_total_fixed_K": total_k,
        "k_source_policy": "salt2_train_finite_fit_target_K_local_sum",
        "n_k_source_rows": len(k_rows),
        "n_k_included_rows": sum(1 for row in k_rows if row["included_in_proxy"] == "yes"),
        "n_result_rows": len(results),
        "n_accepted_rows": accepted,
        "n_cases": len(case_inputs),
        "n_variants": len(base.variant_specs()),
        "variant_summary": variant_summary,
        "thermal_fit_used": False,
        "external_fluid_modified": False,
        "native_solver_outputs_mutated": False,
        "publication_closure_allowed": False,
        "contract_summary": contract_summary,
        "source_files": {
            "named_pressure_loss_table": rel(NAMED_LOSS_TABLE),
            "agent_299_h1_feasibility": rel(AGENT_299_DIR / "h1_feasibility_notes.csv"),
            "forward_v0_runner": "tools/analyze/run_predictive_forward_v0_imposed_cooler.py",
        },
        "outputs": [
            "README.md",
            "h1_proxy_run_plan.csv",
            "h1_proxy_results.csv",
            "h1_proxy_variant_summary.csv",
            "h1_proxy_k_source.csv",
            "summary.json",
        ],
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(NAMED_LOSS_TABLE)}",
        f"  - {rel(AGENT_299_DIR / 'h1_feasibility_notes.csv')}",
        "tags: [forward-model, predictive-1d, hydraulics, h1-proxy]",
        "related:",
        "  - .agent/status/2026-07-13_AGENT-308.md",
        "  - .agent/journal/2026-07-13/predictive-h1-proxy-rerun.md",
        "task: AGENT-308",
        "date: 2026-07-13",
        "role: Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Predictive H1 Proxy Rerun",
        "",
        f"Generated: `{summary['generated_utc']}`",
        "",
        "This package runs an `ethan_runs`-only H1-like hydraulic screen. It is not",
        "a faithful localized H1 implementation because current Fluid only accepts",
        "aggregate `MinorLosses` fixed-K controls.",
        "",
        "## Result",
        "",
        f"- Aggregate Salt2 train finite fit-target `K_local` sum: `{summary['minor_loss_total_fixed_K']:.6g}`.",
        f"- Accepted rows: `{summary['n_accepted_rows']}` of `{summary['n_result_rows']}`.",
        "- Thermal fitting used: `false`.",
        "- Publication closure allowed: `false`.",
        "",
        "## Outputs",
        "",
        "- `h1_proxy_run_plan.csv`",
        "- `h1_proxy_results.csv`",
        "- `h1_proxy_variant_summary.csv`",
        "- `h1_proxy_k_source.csv`",
        "- `summary.json`",
        "",
        "## Guardrail",
        "",
        "Use this only as a directionality screen. Faithful localized H1 still needs",
        "Fluid-side named/localized hydraulic-loss and reset metadata support.",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = run_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
