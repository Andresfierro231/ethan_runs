#!/usr/bin/env python3
"""Build the next lightweight 1D model-form screen from consolidated closures.

Workflow role:
    This is a low-cost model-form triage script. It consumes consolidated CFD
    closure observations and prior per-leg/model-ladder comparisons, then emits
    candidate model forms and scores that can guide a more formal external
    Fluid bakeoff.

Inputs:
    - Consolidated closure tables from `--input-dir`.
    - Prior local per-leg and model-ladder products referenced by constants in
      this module.

Outputs:
    Candidate-form CSV/JSON artifacts under `--output-dir`.

CLI modifiers:
    - `--input-dir` retargets the consolidated closure source package.
    - `--output-dir` redirects the next-form screen.

Boundaries:
    This is a screening tool, not a publication-grade calibration by itself. It
    should consume a canonical observation table once that contract exists, and
    it should keep fitted rows separate from validation rows.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

DEFAULT_INPUT_DIR = ROOT / "work_products/2026-07-04_consolidated_closure_and_model_jobs"
DEFAULT_OUTPUT_DIR = ROOT / "work_products/2026-07-04_consolidated_closure_and_model_jobs/next_1d_model_forms"
PERLEG_PRIOR = ROOT / "work_products/2026-07-01_claude_1d_predictivity_trial/perleg_vs_global_mdot.csv"
LADDER_PRIOR = ROOT / "work_products/2026-07-04_incremental_model_form_comparison/incremental_model_form_ladder.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def ffloat(value: Any, default: float = math.nan) -> float:
    try:
        if value in ("", None):
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def mean_abs(values: list[float]) -> float:
    values = [abs(value) for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def rmse(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else math.nan


def summarize_prior_perleg(path: Path) -> list[dict[str, Any]]:
    rows = read_csv(path)
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row.get("form", "")].append(ffloat(row.get("pct_err")))
    out = []
    for form, errors in sorted(grouped.items()):
        out.append(
            {
                "model_form": form,
                "source": relative_to_workspace(path),
                "case_count": len([value for value in errors if math.isfinite(value)]),
                "mean_abs_mdot_error_pct": mean_abs(errors),
                "rmse_mdot_error_pct": rmse(errors),
                "status": "evaluated_prior",
                "interpretation": "Prior Claude trial score; useful comparison but not a new external Fluid run.",
            }
        )
    return out


def fit_power_law(points: list[dict[str, str]]) -> dict[str, Any]:
    usable = [
        row for row in points
        if row.get("closure_fit_admissible") != "no"
        and ffloat(row.get("reynolds_number")) > 0
        and ffloat(row.get("apparent_darcy_f")) > 0
        and "negative_f" not in row.get("quality_flags", "")
    ]
    if len(usable) < 2:
        return {"point_count": len(usable), "fit_status": "insufficient_true_steady_points"}
    xs = [math.log(ffloat(row["reynolds_number"])) for row in usable]
    ys = [math.log(ffloat(row["apparent_darcy_f"])) for row in usable]
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom <= 0:
        return {"point_count": len(usable), "fit_status": "singular"}
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    intercept = ybar - slope * xbar
    preds = [intercept + slope * x for x in xs]
    ss_res = sum((y - pred) ** 2 for y, pred in zip(ys, preds))
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    return {
        "point_count": len(usable),
        "fit_status": "screen_only_needs_more_true_steady_cfd",
        "a_prefactor": math.exp(intercept),
        "b_exponent": slope,
        "r2_log_space": 1.0 - ss_res / ss_tot if ss_tot > 0 else math.nan,
        "re_min": min(ffloat(row["reynolds_number"]) for row in usable),
        "re_max": max(ffloat(row["reynolds_number"]) for row in usable),
    }


def build_re_fit_screen(closure_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in closure_rows:
        if row.get("fluid") != "salt" or row.get("case_family") != "salt_jin":
            continue
        if row.get("friction_available") != "yes":
            continue
        grouped[(row.get("span", ""), row.get("pressure_method", ""))].append(row)
    out = []
    for (span, method), points in sorted(grouped.items()):
        out.append({"model_form": "per_leg_f_of_Re_power_law", "span": span, "pressure_method": method, **fit_power_law(points)})
    return out


def build_candidate_backlog(re_screen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fitted_spans = sum(row.get("fit_status") == "screen_only_needs_more_true_steady_cfd" for row in re_screen)
    return [
        {
            "candidate_id": "N1",
            "model_form": "per_leg_friction_multiplier",
            "job_action": "evaluate_from_existing_prior_perleg_trial",
            "ready_state": "ready_now_from_existing_salt_nominal",
            "blocker": "needs integration into canonical model-form runner before becoming the default fit.",
        },
        {
            "candidate_id": "N2",
            "model_form": "per_leg_f_of_Re_power_law",
            "job_action": "screen_loglog_f_vs_Re_by_span",
            "ready_state": "screen_only",
            "blocker": f"Only {fitted_spans} span/method groups have enough positive Salt nominal points; false-steady perturbations excluded.",
        },
        {
            "candidate_id": "N3",
            "model_form": "thermal_UA_prime_term",
            "job_action": "stage_for_next_external_or_local_rom_fit",
            "ready_state": "partial_ready",
            "blocker": "Salt nominal UA'/HTC exists; Water and uncertainty treatment still pending.",
        },
        {
            "candidate_id": "N4",
            "model_form": "water_family_validation_axis",
            "job_action": "wait_for_dependent_water_postprocess",
            "ready_state": "blocked_on_3265970",
            "blocker": "Water continuation job must exit and be frozen before admission.",
        },
    ]


def write_readme(output_dir: Path, scores: list[dict[str, Any]], re_screen: list[dict[str, Any]]) -> None:
    best = min(
        [row for row in scores if math.isfinite(ffloat(row.get("mean_abs_mdot_error_pct")))],
        key=lambda row: ffloat(row.get("mean_abs_mdot_error_pct")),
        default={},
    )
    lines = [
        "# Next 1D Model-Form Job Output",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "This is a lightweight local/Slurm-safe screen built from existing consolidated CFD closure tables.",
        "It does not run OpenFOAM and does not edit external Fluid repositories.",
        "",
        "## Current Result",
        "",
    ]
    if best:
        lines.append(f"- Best prior per-leg/global trial row here: `{best['model_form']}` with mean |mdot error| `{ffloat(best['mean_abs_mdot_error_pct']):.3f}%`.")
    lines.extend(
        [
            f"- f(Re) span/method groups screened: `{len(re_screen)}`.",
            "- f(Re) rows remain screen-only because the canceled perturbation runs are false-steady and excluded.",
            "",
            "## Files",
            "",
            "- `next_1d_model_form_scores.csv`",
            "- `per_leg_re_power_law_screen.csv`",
            "- `next_model_form_backlog.csv`",
            "- `summary.json`",
        ]
    )
    output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = ensure_dir(Path(args.output_dir))
    closure_rows = read_csv(input_dir / "consolidated_closure_table.csv")
    scores = summarize_prior_perleg(PERLEG_PRIOR)
    re_screen = build_re_fit_screen(closure_rows)
    backlog = build_candidate_backlog(re_screen)
    csv_dump(output_dir / "next_1d_model_form_scores.csv", list(scores[0].keys()) if scores else [], scores)
    csv_dump(output_dir / "per_leg_re_power_law_screen.csv", list(re_screen[0].keys()) if re_screen else [], re_screen)
    csv_dump(output_dir / "next_model_form_backlog.csv", list(backlog[0].keys()), backlog)
    json_dump(
        output_dir / "summary.json",
        {
            "generated_at": iso_timestamp(),
            "inputs": {
                "closure_table": relative_to_workspace(input_dir / "consolidated_closure_table.csv"),
                "prior_perleg": relative_to_workspace(PERLEG_PRIOR),
                "prior_ladder": relative_to_workspace(LADDER_PRIOR),
            },
            "scores": scores,
            "re_screen": re_screen,
            "backlog": backlog,
        },
    )
    write_readme(output_dir, scores, re_screen)
    print(f"Wrote {relative_to_workspace(output_dir / 'summary.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
