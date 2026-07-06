#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, finite_float, load_csv_rows, write_json
from tools.analyze.build_ethan_frozen_state_results_package import best_one_d_rows

FROZEN_DIR = ROOT / "reports" / "2026-06-22_ethan_frozen_state_results"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-22_ethan_fluid_replay_against_frozen_state"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a report package that compares the current readable Fluid "
            "Salt replay against the June 22 frozen-state CFD contract."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def scenario_family(scenario: str) -> str:
    if "_hybrid_" in scenario:
        return "hybrid"
    if "_baseline_" in scenario:
        return "baseline"
    return "other"


def scenario_condition(scenario: str) -> str:
    parts = scenario.split("_")
    if len(parts) < 2:
        return scenario
    try:
        ins_index = parts.index("ins")
    except ValueError:
        return scenario
    if ins_index + 3 >= len(parts):
        return scenario
    return f"ins_{parts[ins_index + 1]}_rad_{parts[ins_index + 3]}"


def scenario_rollup_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["scenario"]].append(row)
    out: list[dict[str, Any]] = []
    for scenario, group in sorted(grouped.items()):
        temp_abs = [abs(finite_float(row.get("air_outlet_temperature_error_k"))) for row in group]
        flow_abs = [abs(finite_float(row.get("mass_flow_relative_error_pct"))) for row in group]
        valid_count = sum(
            1
            for row in group
            if str(row.get("accepted_for_validation", "")).lower() == "true"
            and row.get("validity_status") == "valid"
        )
        out.append(
            {
                "scenario": scenario,
                "scenario_family": scenario_family(scenario),
                "condition_label": scenario_condition(scenario),
                "case_count": len(group),
                "valid_case_count": valid_count,
                "mean_abs_air_outlet_temperature_error_k": sum(temp_abs) / len(temp_abs) if temp_abs else None,
                "max_abs_air_outlet_temperature_error_k": max(temp_abs) if temp_abs else None,
                "mean_abs_mass_flow_relative_error_pct": sum(flow_abs) / len(flow_abs) if flow_abs else None,
                "max_abs_mass_flow_relative_error_pct": max(flow_abs) if flow_abs else None,
                "descriptor_modes": "|".join(sorted({row.get("profile_descriptor_mode", "") for row in group})),
                "internal_htc_modes": "|".join(sorted({row.get("internal_htc_mode", "") for row in group})),
            }
        )
    return out


def hybrid_coverage_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in rows:
        grouped[scenario_condition(row["scenario"])][scenario_family(row["scenario"])].add(row["case_label"])
    out: list[dict[str, Any]] = []
    for condition, family_map in sorted(grouped.items()):
        baseline_cases = sorted(family_map.get("baseline", set()))
        hybrid_cases = sorted(family_map.get("hybrid", set()))
        missing_hybrid = sorted(set(baseline_cases) - set(hybrid_cases))
        out.append(
            {
                "condition_label": condition,
                "baseline_case_count": len(baseline_cases),
                "hybrid_case_count": len(hybrid_cases),
                "baseline_cases": "|".join(baseline_cases),
                "hybrid_cases": "|".join(hybrid_cases),
                "missing_hybrid_cases": "|".join(missing_hybrid),
                "coverage_status": "partial" if missing_hybrid else "matched",
            }
        )
    return out


def branch_boundary_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "branch_name": row["branch_name"],
                "branch_alias": row["branch_alias"],
                "dominant_fit_status": row["dominant_fit_status"],
                "domain_note": row["domain_note"],
                "modeling_note": row["modeling_note"],
            }
        )
    return out


def data_need_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "blocked_closure": row["blocked_closure"],
            "missing_observable": row["missing_observable"],
            "preferred_extractor_or_package": row["preferred_extractor_or_package"],
            "would_unlock": row["would_unlock"],
        }
        for row in rows
    ]


def readme_text(
    *,
    scenario_rows: list[dict[str, Any]],
    best_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
) -> str:
    best_note = "No readable Fluid replay rows found."
    if best_rows:
        case_bits = [
            f"{row['case_label']}: {row['scenario']} (|dT_air|={abs(finite_float(row['air_outlet_temperature_error_k'])):.2f} K, "
            f"|dm_dot|={abs(finite_float(row['mass_flow_relative_error_pct'])):.2f}%)"
            for row in best_rows
        ]
        best_note = "; ".join(case_bits)
    partial_conditions = [row["condition_label"] for row in coverage_rows if row["coverage_status"] == "partial"]
    downcomer_row = next((row for row in branch_rows if row["branch_name"] == "right_leg"), None)
    upcomer_row = next((row for row in branch_rows if row["branch_name"] == "upcomer"), None)
    hybrid_scenarios = [row for row in scenario_rows if row["scenario_family"] == "hybrid"]
    hybrid_note = "No hybrid scenarios were readable."
    if hybrid_scenarios:
        hybrid_note = (
            f"Readable hybrid scenarios: {len(hybrid_scenarios)} condition rows, "
            f"but only {sum(int(row['case_count']) for row in hybrid_scenarios)} total case rows."
        )
    return f"""# Ethan Fluid Replay Against Frozen State

Generated: `2026-06-22`

## Scope

- This package compares the current readable `Fluid` Salt replay against the
  June 22 frozen-state CFD contract.
- It does **not** assume straight sections are automatically fully developed.
- It keeps the current branch boundary explicit:
  - direct internal `Nu` is defended only on `left_lower_leg`
  - `upcomer` remains sensitivity-only
  - `right_leg` or downcomer remains blocked for direct `Nu`

## Best current readable 1D rows

{best_note}

## Coverage boundary

- {hybrid_note}
- Conditions with incomplete baseline-vs-hybrid case coverage:
  `{", ".join(partial_conditions) if partial_conditions else "none"}`.
- This is the practical meaning of the current domain-breadth gap:
  the hybrid closure family is not yet readable across the same Salt case set as
  the baseline family, so broad closure conclusions remain under-supported.

## Branch modeling boundary

- Upcomer:
  {upcomer_row['modeling_note'] if upcomer_row else 'not available'}
- Downcomer:
  {downcomer_row['modeling_note'] if downcomer_row else 'not available'}

## Current interpretation

- The present readable `Fluid` campaign is still a pre-refresh reference
  surface rather than a new June 22 rerun.
- It is already useful for quantifying current 1D error trends and showing
  which closure family currently helps.
- It is not broad enough yet to defend one shared direct internal HTC closure
  over all Salt branches or cases.
"""


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))

    one_d_rows = load_csv_rows(FROZEN_DIR / "one_d_readable_status.csv")
    best_rows = best_one_d_rows(one_d_rows)
    scenario_rows = scenario_rollup_rows(one_d_rows)
    coverage_rows = hybrid_coverage_rows(one_d_rows)
    branch_rows = branch_boundary_rows(load_csv_rows(FROZEN_DIR / "branch_behavior_summary.csv"))
    need_rows = data_need_rows(load_csv_rows(FROZEN_DIR / "data_needs.csv"))

    csv_dump_rows(output_dir / "fluid_replay_status.csv", one_d_rows)
    csv_dump_rows(output_dir / "fluid_best_case_rows.csv", best_rows)
    csv_dump_rows(output_dir / "scenario_rollup.csv", scenario_rows)
    csv_dump_rows(output_dir / "hybrid_coverage.csv", coverage_rows)
    csv_dump_rows(output_dir / "branch_modeling_boundary.csv", branch_rows)
    csv_dump_rows(output_dir / "data_needs_for_replay.csv", need_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "readable_row_count": len(one_d_rows),
        "best_case_count": len(best_rows),
        "scenario_count": len(scenario_rows),
        "partial_coverage_condition_count": sum(1 for row in coverage_rows if row["coverage_status"] == "partial"),
        "hybrid_case_count": sum(int(row["hybrid_case_count"]) for row in coverage_rows),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        readme_text(
            scenario_rows=scenario_rows,
            best_rows=best_rows,
            coverage_rows=coverage_rows,
            branch_rows=branch_rows,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
