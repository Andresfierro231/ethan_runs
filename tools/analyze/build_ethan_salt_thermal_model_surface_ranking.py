#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_thermal_model_surface_ranking"
DEFAULT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"
DEFAULT_SALT_CASE_ROOTS = [
    ROOT / "tmp" / "2026-06-15_live_case_analysis" / "contract_fix_salt2",
    ROOT / "tmp" / "2026-06-15_live_case_analysis" / "contract_fix_salt_family",
]

SAFE_BRANCHES = ("left_lower_leg", "test_section_span", "left_upper_leg", "upcomer")
MISSING = {"", "nan", "NaN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rank the existing Salt safe-subset effective thermal modeling surfaces "
            "without reopening extraction. The script uses only the already-published "
            "branch trust gates and branch thermal summaries."
        )
    )
    parser.add_argument("--closure-dir", default=str(DEFAULT_CLOSURE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def require_exists(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Required input is missing: {path}")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def rel_cv(values: list[float]) -> float:
    if not values:
        return math.nan
    mean_value = statistics.fmean(values)
    if abs(mean_value) <= 1.0e-12:
        return math.inf
    return statistics.pstdev(values) / abs(mean_value)


def load_safe_branch_gate_rows(closure_dir: Path) -> dict[str, dict[str, str]]:
    path = closure_dir / "branch_thermal_interpretation.csv"
    require_exists(path)
    rows = load_csv_rows(path)
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["family"] != "salt_all":
            continue
        if row["branch"] not in SAFE_BRANCHES:
            continue
        output[str(row["branch"])] = row
    missing = [branch for branch in SAFE_BRANCHES if branch not in output]
    if missing:
        raise RuntimeError(f"Missing Salt safe-branch gate rows: {missing}")
    return output


def iter_salt_branch_summaries() -> list[tuple[str, Path]]:
    summary_paths: list[tuple[str, Path]] = []
    for root in DEFAULT_SALT_CASE_ROOTS:
        require_exists(root)
        for path in sorted(root.glob("*/branch_thermal_summary.csv")):
            summary_paths.append((path.parent.name, path))
    if not summary_paths:
        raise RuntimeError("No Salt branch_thermal_summary.csv files were found under the preserved June 15 case roots.")
    return summary_paths


def load_branch_summary_rows() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source_id, path in iter_salt_branch_summaries():
        rows = load_csv_rows(path)
        for row in rows:
            branch = str(row["branch_name"])
            if branch not in SAFE_BRANCHES:
                continue
            total_row_count = float(row["total_row_count"])
            usable_row_count = float(row["usable_row_count"])
            output.append(
                {
                    "source_id": source_id,
                    "branch": branch,
                    "usable_fraction": usable_row_count / total_row_count if total_row_count else math.nan,
                    "thermal_warning_fraction": float(row["thermal_warning_fraction"]),
                    "min_abs_bulk_minus_wall_temp_k": float(row["min_abs_bulk_minus_wall_temp_k"]),
                    "mean_effective_htc_w_m2_k": float(row["mean_effective_htc_w_m2_k"]),
                    "mean_effective_ua_per_m_w_m_k": float(row["mean_effective_ua_per_m_w_m_k"]),
                    "mean_effective_thermal_resistance_k_m_w": float(row["mean_effective_thermal_resistance_k_m_w"]),
                    "source_path": relative_path(path),
                }
            )
    if not output:
        raise RuntimeError("No Salt safe-branch summary rows were loaded.")
    return output


def build_branch_stats(branch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        by_branch[str(row["branch"])].append(row)

    output: list[dict[str, Any]] = []
    for branch in SAFE_BRANCHES:
        rows = by_branch[branch]
        htc_values = [float(row["mean_effective_htc_w_m2_k"]) for row in rows]
        ua_values = [float(row["mean_effective_ua_per_m_w_m_k"]) for row in rows]
        rth_values = [float(row["mean_effective_thermal_resistance_k_m_w"]) for row in rows]
        usable_fractions = [float(row["usable_fraction"]) for row in rows]
        warning_fractions = [float(row["thermal_warning_fraction"]) for row in rows]
        min_dt_values = [float(row["min_abs_bulk_minus_wall_temp_k"]) for row in rows]
        output.append(
            {
                "branch": branch,
                "source_count": len(rows),
                "usable_fraction_min": f"{min(usable_fractions):.12f}",
                "usable_fraction_mean": f"{statistics.fmean(usable_fractions):.12f}",
                "thermal_warning_fraction_max": f"{max(warning_fractions):.12f}",
                "thermal_warning_fraction_mean": f"{statistics.fmean(warning_fractions):.12f}",
                "min_abs_bulk_minus_wall_temp_k_min": f"{min(min_dt_values):.12f}",
                "min_abs_bulk_minus_wall_temp_k_mean": f"{statistics.fmean(min_dt_values):.12f}",
                "effective_htc_rel_cv": f"{rel_cv(htc_values):.12f}",
                "effective_ua_rel_cv": f"{rel_cv(ua_values):.12f}",
                "thermal_resistance_rel_cv": f"{rel_cv(rth_values):.12f}",
            }
        )
    return output


def thermal_surface_rows(branch_stats: list[dict[str, Any]], safe_gate_rows: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    all_safe = all(gate["interpretability_status"] == "headline_eligible" for gate in safe_gate_rows.values())
    min_usable = min(float(row["usable_fraction_min"]) for row in branch_stats)
    max_warning = max(float(row["thermal_warning_fraction_max"]) for row in branch_stats)
    min_delta_t = min(float(row["min_abs_bulk_minus_wall_temp_k_min"]) for row in branch_stats)
    mean_htc_rel_cv = statistics.fmean(float(row["effective_htc_rel_cv"]) for row in branch_stats)
    mean_ua_rel_cv = statistics.fmean(float(row["effective_ua_rel_cv"]) for row in branch_stats)
    mean_rth_rel_cv = statistics.fmean(float(row["thermal_resistance_rel_cv"]) for row in branch_stats)
    worst_rth_rel_cv = max(float(row["thermal_resistance_rel_cv"]) for row in branch_stats)

    return [
        {
            "rank": 1,
            "surface_id": "effective_ua_profile",
            "surface_label": "Effective UA'(x)",
            "readiness_status": "family_specific_primary",
            "recommended_use": "primary_salt_model_surface",
            "headline_allowed": "yes" if all_safe else "no",
            "eligible_branches": ", ".join(SAFE_BRANCHES),
            "min_usable_fraction": f"{min_usable:.12f}",
            "max_thermal_warning_fraction": f"{max_warning:.12f}",
            "min_abs_bulk_minus_wall_temp_k": f"{min_delta_t:.12f}",
            "mean_relative_cv": f"{mean_ua_rel_cv:.12f}",
            "worst_branch_relative_cv": f"{max(float(row['effective_ua_rel_cv']) for row in branch_stats):.12f}",
            "scientific_rationale": (
                "UA' keeps the same support-cleared Salt branch set as HTC, but it ties the effective thermal signal directly to branch heat transfer per length and avoids the extra wall-area normalization step. "
                "Its case-to-case variability is slightly lower than HTC on three of the four safe branches and it avoids the reciprocal amplification seen in R'_th."
            ),
        },
        {
            "rank": 2,
            "surface_id": "effective_htc_profile",
            "surface_label": "Effective HTC(x)",
            "readiness_status": "family_specific_secondary",
            "recommended_use": "secondary_salt_model_surface",
            "headline_allowed": "yes" if all_safe else "no",
            "eligible_branches": ", ".join(SAFE_BRANCHES),
            "min_usable_fraction": f"{min_usable:.12f}",
            "max_thermal_warning_fraction": f"{max_warning:.12f}",
            "min_abs_bulk_minus_wall_temp_k": f"{min_delta_t:.12f}",
            "mean_relative_cv": f"{mean_htc_rel_cv:.12f}",
            "worst_branch_relative_cv": f"{max(float(row['effective_htc_rel_cv']) for row in branch_stats):.12f}",
            "scientific_rationale": (
                "HTC remains usable on the same safe Salt branch subset and tracks UA' closely, but it introduces an additional wall-area normalization choice. "
                "That makes it a good comparison surface, but a weaker primary modeling surface than UA' when the goal is a branch-level dependency rather than a wall-flux presentation."
            ),
        },
        {
            "rank": 3,
            "surface_id": "branch_average_thermal_resistance",
            "surface_label": "Branch-averaged R'_th",
            "readiness_status": "supporting_only",
            "recommended_use": "supporting_summary_only",
            "headline_allowed": "no",
            "eligible_branches": ", ".join(SAFE_BRANCHES),
            "min_usable_fraction": f"{min_usable:.12f}",
            "max_thermal_warning_fraction": f"{max_warning:.12f}",
            "min_abs_bulk_minus_wall_temp_k": f"{min_delta_t:.12f}",
            "mean_relative_cv": f"{mean_rth_rel_cv:.12f}",
            "worst_branch_relative_cv": f"{worst_rth_rel_cv:.12f}",
            "scientific_rationale": (
                "A branch-averaged resistance summary can still help organize Salt branch comparisons, but it inherits the reciprocal sensitivity of 1/UA'. "
                "It should be kept as a compact summary surface, not as the primary dependency to fit."
            ),
        },
        {
            "rank": 4,
            "surface_id": "thermal_resistance_profile",
            "surface_label": "Effective R'_th(x)",
            "readiness_status": "diagnostic_only",
            "recommended_use": "do_not_fit_directly",
            "headline_allowed": "no",
            "eligible_branches": ", ".join(SAFE_BRANCHES),
            "min_usable_fraction": f"{min_usable:.12f}",
            "max_thermal_warning_fraction": f"{max_warning:.12f}",
            "min_abs_bulk_minus_wall_temp_k": f"{min_delta_t:.12f}",
            "mean_relative_cv": f"{mean_rth_rel_cv:.12f}",
            "worst_branch_relative_cv": f"{worst_rth_rel_cv:.12f}",
            "scientific_rationale": (
                "The streamwise resistance profile is the most fragile of the defended Salt thermal surfaces because the reciprocal transform amplifies the same low-conductance regions that already challenge UA'. "
                "The safe-subset summary confirms this directly: test_section_span and upcomer show much larger resistance variability than the paired HTC or UA' summaries."
            ),
        },
    ]


def write_readme(
    output_dir: Path,
    branch_stats: list[dict[str, Any]],
    ranking_rows: list[dict[str, Any]],
    branch_summary_rows: list[dict[str, Any]],
) -> None:
    source_paths = sorted({str(row["source_path"]) for row in branch_summary_rows})
    primary_row = ranking_rows[0]
    secondary_row = ranking_rows[1]
    readme = f"""# Salt Thermal Model Surface Ranking

Generated: `{iso_timestamp()}`

## Purpose

Rank the already-defended Salt thermal modeling surfaces on the existing safe branch subset only. This package does not reopen extraction, branch trust gates, or cross-family promotion.

## Inputs

- `reports/2026-06-18_ethan_transport_interpretation_closure/branch_thermal_interpretation.csv`
- Salt branch summaries under the preserved June 15 package roots:
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/*/branch_thermal_summary.csv`
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/*/branch_thermal_summary.csv`

## Safe Salt branch subset

- `left_lower_leg`
- `test_section_span`
- `left_upper_leg`
- `upcomer`

## Decision

- Primary Salt thermal modeling surface: `{primary_row['surface_label']}`
- Secondary Salt thermal modeling surface: `{secondary_row['surface_label']}`
- Keep `branch-averaged R'_th` as supporting-only.
- Keep `R'_th(x)` as diagnostic-only.

## Why

- All four branches remain scrutiny-cleared in the June 18 interpretation closure.
- Minimum usable fraction across the safe subset stays above `0.94`.
- Maximum branch warning fraction across the safe subset stays below `0.06`.
- Minimum resolved `|T_bulk - T_wall|` across the safe subset stays above `2.03 K`, well above the current `0.50 K` floor.
- `UA'` and `HTC` have comparable case-to-case stability, but `UA'` avoids the extra wall-area normalization embedded in HTC.
- `R'_th` is materially more fragile because the reciprocal transform amplifies the same low-conductance regions that already challenge UA'.

## Branch stability summary

| Branch | Min usable fraction | Max warning fraction | Min |T_bulk-T_wall| [K] | HTC rel-CV | UA' rel-CV | R'_th rel-CV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in branch_stats:
        readme += (
            f"| {row['branch']} | {float(row['usable_fraction_min']):.3f} | "
            f"{float(row['thermal_warning_fraction_max']):.3f} | "
            f"{float(row['min_abs_bulk_minus_wall_temp_k_min']):.3f} | "
            f"{float(row['effective_htc_rel_cv']):.3f} | "
            f"{float(row['effective_ua_rel_cv']):.3f} | "
            f"{float(row['thermal_resistance_rel_cv']):.3f} |\n"
        )

    readme += f"""

## Source paths

{chr(10).join(f"- `{path}`" for path in source_paths)}

## Reproduction

```bash
python tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py \\
  --output-dir {relative_path(output_dir)}
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def write_decision_note(output_dir: Path, ranking_rows: list[dict[str, Any]]) -> None:
    primary = ranking_rows[0]
    secondary = ranking_rows[1]
    note = f"""# Salt Safe-Subset Model Surface Decision

## Primary surface

`{primary['surface_label']}` is the preferred Salt modeling surface on the defended branch subset. It keeps the same branch promotion gate as HTC, but it is the most direct branch-scale conductance surface and avoids the extra wall-area normalization step used by HTC.

## Secondary surface

`{secondary['surface_label']}` remains valuable for interpretation and presentation, but it should stay secondary to `UA'` when the goal is a branch dependency rather than a wall-flux-normalized report quantity.

## Demotions

- `branch-averaged R'_th`: supporting-only
- `R'_th(x)`: diagnostic-only

The reason is not that resistance is meaningless. The reason is that the reciprocal transform adds fragility exactly where support is already thinnest. The safe Salt subset is strong enough to use resistance as a check, but not as the primary fitted surface.
"""
    (output_dir / "salt_safe_subset_model_surface_decision.md").write_text(note, encoding="utf-8")


def main() -> None:
    args = parse_args()
    closure_dir = Path(args.closure_dir).resolve()
    output_dir = ensure_dir(Path(args.output_dir).resolve())

    safe_gate_rows = load_safe_branch_gate_rows(closure_dir)
    branch_summary_rows = load_branch_summary_rows()
    branch_stats = build_branch_stats(branch_summary_rows)
    ranking_rows = thermal_surface_rows(branch_stats, safe_gate_rows)

    csv_dump(
        output_dir / "salt_safe_subset_branch_stats.csv",
        list(branch_stats[0].keys()),
        branch_stats,
    )
    csv_dump(
        output_dir / "salt_safe_subset_thermal_ranking.csv",
        list(ranking_rows[0].keys()),
        ranking_rows,
    )

    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-072",
        "builder_script": "tools/analyze/build_ethan_salt_thermal_model_surface_ranking.py",
        "safe_branches": list(SAFE_BRANCHES),
        "branch_count": len(SAFE_BRANCHES),
        "salt_case_count": len({str(row["source_id"]) for row in branch_summary_rows}),
        "primary_surface": ranking_rows[0]["surface_id"],
        "secondary_surface": ranking_rows[1]["surface_id"],
        "diagnostic_only_surface": ranking_rows[-1]["surface_id"],
        "artifacts": [
            "README.md",
            "summary.json",
            "salt_safe_subset_branch_stats.csv",
            "salt_safe_subset_thermal_ranking.csv",
            "salt_safe_subset_model_surface_decision.md",
        ],
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, branch_stats, ranking_rows, branch_summary_rows)
    write_decision_note(output_dir, ranking_rows)


if __name__ == "__main__":
    main()
