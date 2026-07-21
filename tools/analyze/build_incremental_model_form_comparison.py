#!/usr/bin/env python3
"""Build an incremental 1D model-form comparison from existing CFD/ROM outputs.

This package answers two immediate questions without running new OpenFOAM:

* How do currently evaluated 1D model forms perform when arranged as an
  incremental ladder where each row adds or swaps one term?
* What friction-vs-Re evidence exists today from mesh-corrected CFD extraction,
  and where are the gaps for the next model forms?

The script is intentionally additive. It reads existing July 1 work products and
writes a new July 4 package. It does not edit the external Fluid repository and
does not mutate case directories.
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

DEFAULT_OUTPUT_DIR = ROOT / "work_products/2026-07-04_incremental_model_form_comparison"
MODEL_FORM_DIR = ROOT / "work_products/2026-07-01_rom_model_form_fits_and_1p4_boundary"
PRESENTATION_DIR = ROOT / "work_products/2026-07-01_presentation_readiness_and_rom_agenda"
FRICTION_PATH = ROOT / "work_products/2026-07-01_claude_segment_friction/segment_friction.csv"
RUN_STATUS_PATH = ROOT / "work_products/2026-07-04_postprocessing_run_status_and_next_steps/run_status_inventory.csv"

FIT_SALTS = {2, 3, 4}

INCREMENTAL_FORMS = [
    {
        "step_id": "H0",
        "model_form": "zero_minor_1p4_rad_on",
        "comparison_type": "baseline",
        "incremental_change": "f(Re) major-friction only; no explicit minor losses or test-section diameter-change term",
        "new_term_count": 0,
        "interpretation": "Closest evaluated proxy for friction as a function of Re only in the current 1D model.",
    },
    {
        "step_id": "H1",
        "model_form": "boundary_default_1p4_rad_on",
        "comparison_type": "additive",
        "incremental_change": "add default fixed minor-loss K and test-section diameter-change term",
        "new_term_count": 1,
        "interpretation": "Default compact-loop loss model at CFD-matched 1.4 in boundary.",
    },
    {
        "step_id": "H2a",
        "model_form": "fit_major_defaultK_1p4",
        "comparison_type": "one_parameter_fit",
        "incremental_change": "fit one global major-friction multiplier while retaining default minor K",
        "new_term_count": 1,
        "interpretation": "Tests whether Re-only friction needs a global correction before adding richer terms.",
    },
    {
        "step_id": "H2b",
        "model_form": "fit_k90_major1_1p4",
        "comparison_type": "one_parameter_alternative",
        "incremental_change": "fit one global bend/minor-loss K with major multiplier fixed at 1",
        "new_term_count": 1,
        "interpretation": "Alternative one-term explanation: compact-loop losses instead of friction multiplier.",
    },
    {
        "step_id": "H3",
        "model_form": "fit_major_k90_1p4",
        "comparison_type": "two_parameter_fit",
        "incremental_change": "fit global major-friction multiplier plus global bend K",
        "new_term_count": 2,
        "interpretation": "Best current compact hydraulic fit, but still mdot-only and globally parameterized.",
    },
    {
        "step_id": "H4",
        "model_form": "cfd_casewise_closures_1p4_rad_on",
        "comparison_type": "casewise_cfd_closure",
        "incremental_change": "replace global coefficients with casewise CFD-derived friction and bend K closures",
        "new_term_count": 2,
        "interpretation": "Diagnostic injection of CFD closures; not a transferable predictive law yet.",
    },
]

MISSING_FORMS = [
    {
        "candidate_id": "M1",
        "model_form": "per_leg_friction_multiplier",
        "single_new_term": "replace one global major multiplier with per-leg friction multipliers",
        "data_needed": "mesh-corrected de-buoyed friction by leg for Salt 2-4 and later Water",
        "current_blocker": "needs consolidated closure table and uncertainty flags",
        "can_start_now": "yes_from_existing_salt_nominal_outputs",
        "suggested_owner_lane": "model_form_python",
    },
    {
        "candidate_id": "M2",
        "model_form": "per_leg_f_of_Re_power_law",
        "single_new_term": "fit f_D = a_l Re^b_l per leg instead of constants",
        "data_needed": "more true-steady operating points; current Salt 2-4 gives only three coupled points",
        "current_blocker": "false-steady perturbations cannot be admitted",
        "can_start_now": "screen_only",
        "suggested_owner_lane": "needs_new_cfd",
    },
    {
        "candidate_id": "M3",
        "model_form": "bend_K_Re_term",
        "single_new_term": "replace fixed bend K with K(Re) or K/Re family",
        "data_needed": "bend_minor_loss tables plus true-steady perturbation spread",
        "current_blocker": "bend K exists for nominal Salt only; perturbation spread is invalid",
        "can_start_now": "screen_only",
        "suggested_owner_lane": "closure_extraction_then_model_form",
    },
    {
        "candidate_id": "M4",
        "model_form": "thermal_UA_prime_term",
        "single_new_term": "replace default thermal boundary with segment UA' or HTC closure",
        "data_needed": "Salt nominal UA'/HTC/Nu tables, Water final window, uncertainty treatment",
        "current_blocker": "external Fluid campaign integration not yet committed",
        "can_start_now": "yes_local_python",
        "suggested_owner_lane": "model_form_python",
    },
    {
        "candidate_id": "M5",
        "model_form": "upcomer_recirculation_cell_term",
        "single_new_term": "replace ordinary upcomer friction/thermal closure with recirculation-cell state variable",
        "data_needed": "backflow fraction, Ri_streamwise, true-steady onset/limit CFD",
        "current_blocker": "needs T2/T13 data; current perturbations false-steady",
        "can_start_now": "no",
        "suggested_owner_lane": "new_cfd_design",
    },
    {
        "candidate_id": "M6",
        "model_form": "water_family_validation_axis",
        "single_new_term": "add Water-family validation/scaling axis to fitted Salt closures",
        "data_needed": "Water 1-4 final frozen windows after job 3265970 exits",
        "current_blocker": "Water job still running",
        "can_start_now": "prepare_sbatch_only",
        "suggested_owner_lane": "water_postprocess",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--model-form-dir", default=str(MODEL_FORM_DIR))
    parser.add_argument("--presentation-dir", default=str(PRESENTATION_DIR))
    parser.add_argument("--friction-path", default=str(FRICTION_PATH))
    parser.add_argument("--run-status-path", default=str(RUN_STATUS_PATH))
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ffloat(value: Any, default: float = math.nan) -> float:
    try:
        if value in ("", None):
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def source_to_salt(source_id: str) -> int | None:
    for salt in (1, 2, 3, 4):
        if f"salt_test_{salt}" in source_id or f"salt{salt}" in source_id:
            return salt
    return None


def by_model_summary(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["model_form"]: row for row in rows if row.get("model_form")}


def build_ladder(summary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    summary = by_model_summary(summary_rows)
    out: list[dict[str, Any]] = []
    previous_error = math.nan
    best_prior_error = math.nan
    for form in INCREMENTAL_FORMS:
        row = summary.get(form["model_form"], {})
        error = ffloat(row.get("mean_abs_mdot_error_pct"))
        delta = previous_error - error if math.isfinite(previous_error) and math.isfinite(error) else math.nan
        delta_vs_best_prior = (
            best_prior_error - error
            if math.isfinite(best_prior_error) and math.isfinite(error)
            else math.nan
        )
        out.append(
            {
                **form,
                "evaluated": "yes" if row else "no",
                "case_count": row.get("case_count", ""),
                "mean_abs_mdot_error_pct": error,
                "rmse_mdot_error_pct": ffloat(row.get("rmse_mdot_error_pct")),
                "mean_energy_error_pct_of_heater": ffloat(row.get("mean_energy_error_pct_of_heater")),
                "mean_tp_rmse_k": ffloat(row.get("mean_tp_rmse_k")),
                "mean_tw_rmse_k": ffloat(row.get("mean_tw_rmse_k")),
                "major_loss_multiplier": ffloat(row.get("major_loss_multiplier")),
                "k90": ffloat(row.get("k90")),
                "k20": ffloat(row.get("k20")),
                "total_fixed_k": ffloat(row.get("total_fixed_k")),
                "delta_mean_abs_mdot_error_pct_vs_previous_step": delta,
                "delta_mean_abs_mdot_error_pct_vs_best_prior": delta_vs_best_prior,
            }
        )
        if math.isfinite(error):
            previous_error = error
            best_prior_error = min(best_prior_error, error) if math.isfinite(best_prior_error) else error
    return out


def build_case_scores(detail_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    wanted = {item["model_form"] for item in INCREMENTAL_FORMS}
    out: list[dict[str, Any]] = []
    for row in detail_rows:
        if row.get("model_form") not in wanted:
            continue
        salt = int(ffloat(row.get("salt"), -1))
        if salt not in FIT_SALTS:
            continue
        out.append(
            {
                "model_form": row.get("model_form"),
                "salt": salt,
                "cfd_mdot_kg_s": ffloat(row.get("cfd_mdot_kg_s")),
                "pred_mdot_kg_s": ffloat(row.get("pred_mdot_kg_s")),
                "signed_mdot_error_pct": ffloat(row.get("signed_mdot_error_pct")),
                "abs_mdot_error_pct": ffloat(row.get("abs_mdot_error_pct")),
                "energy_error_pct_of_heater": ffloat(row.get("energy_error_pct_of_heater")),
                "tp_rmse_k": ffloat(row.get("tp_rmse_k")),
                "tw_rmse_k": ffloat(row.get("tw_rmse_k")),
                "root_status": row.get("root_status"),
                "accepted_for_validation": row.get("accepted_for_validation"),
            }
        )
    out.sort(key=lambda item: (item["model_form"], item["salt"]))
    return out


def build_boundary_sensitivity(summary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in summary_rows:
        if row.get("fit_family") != "matched_boundary_sweep":
            continue
        out.append(
            {
                "model_form": row.get("model_form"),
                "insulation_thickness_in": ffloat(row.get("insulation_thickness_in")),
                "radiation_on": row.get("radiation_on"),
                "mean_abs_mdot_error_pct": ffloat(row.get("mean_abs_mdot_error_pct")),
                "mean_energy_error_pct_of_heater": ffloat(row.get("mean_energy_error_pct_of_heater")),
                "interpretation": "boundary/surface-loss sensitivity, not a new hydraulic closure form",
            }
        )
    out.sort(key=lambda item: (str(item["radiation_on"]), item["insulation_thickness_in"]))
    return out


def build_friction_re_table(friction_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in friction_rows:
        salt = source_to_salt(row.get("source_id", ""))
        re_val = ffloat(row.get("reynolds_number"))
        f_app = ffloat(row.get("apparent_darcy_f"))
        f_lam = ffloat(row.get("laminar_ref_darcy_f_64_over_Re"))
        factor = ffloat(row.get("excess_loss_factor_fapp_over_flam"))
        flags = row.get("flags", "")
        usable = (
            salt in FIT_SALTS
            and math.isfinite(re_val)
            and math.isfinite(f_app)
            and f_app > 0.0
            and "negative_f" not in flags
        )
        out.append(
            {
                "source_id": row.get("source_id"),
                "salt": salt if salt is not None else "",
                "span": row.get("span"),
                "method": row.get("method"),
                "reynolds_number": re_val,
                "apparent_darcy_f": f_app,
                "laminar_ref_darcy_f_64_over_Re": f_lam,
                "excess_loss_factor_fapp_over_flam": factor,
                "flow_alignment_min": ffloat(row.get("flow_alignment_min")),
                "usable_for_re_only_screen": "yes" if usable else "no",
                "flags": flags,
            }
        )
    out.sort(key=lambda item: (str(item["span"]), str(item["method"]), ffloat(item["reynolds_number"], math.inf)))
    return out


def fit_power_law(points: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [
        point for point in points
        if point.get("usable_for_re_only_screen") == "yes"
        and math.isfinite(ffloat(point.get("reynolds_number")))
        and math.isfinite(ffloat(point.get("apparent_darcy_f")))
        and ffloat(point.get("reynolds_number")) > 0
        and ffloat(point.get("apparent_darcy_f")) > 0
    ]
    if len(usable) < 2:
        return {"point_count": len(usable), "fit_status": "insufficient_points"}
    xs = [math.log(ffloat(point["reynolds_number"])) for point in usable]
    ys = [math.log(ffloat(point["apparent_darcy_f"])) for point in usable]
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom <= 0:
        return {"point_count": len(usable), "fit_status": "singular"}
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    intercept = ybar - slope * xbar
    preds = [intercept + slope * x for x in xs]
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, preds))
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else math.nan
    return {
        "point_count": len(usable),
        "fit_status": "screen_only_not_publication_fit",
        "a_prefactor": math.exp(intercept),
        "b_exponent": slope,
        "r2_log_space": r2,
        "re_min": min(ffloat(point["reynolds_number"]) for point in usable),
        "re_max": max(ffloat(point["reynolds_number"]) for point in usable),
        "note": "Fit is a screen only; Salt 2-4 nominal points are too few for a defended law.",
    }


def build_friction_fit_summary(friction_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in friction_table:
        grouped[(str(row.get("span")), str(row.get("method")))].append(row)
    out: list[dict[str, Any]] = []
    for (span, method), points in sorted(grouped.items()):
        fit = fit_power_law(points)
        out.append({"span": span, "method": method, **fit})
    return out


def build_missing_backlog(existing_future: list[dict[str, str]], run_status_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts = defaultdict(int)
    for row in run_status_rows:
        counts[row.get("recommendation", "")] += 1
    out = []
    for row in MISSING_FORMS:
        out.append(
            {
                **row,
                "current_run_status_context": (
                    f"false_steady_rows={counts.get('document_only_false_steady', 0)}; "
                    f"water_wait_rows={counts.get('wait_for_job_exit_then_freeze', 0)}"
                ),
            }
        )
    existing_ids = {row.get("candidate_id") for row in out}
    for row in existing_future:
        if row.get("candidate_id") in existing_ids:
            continue
        out.append(
            {
                "candidate_id": row.get("candidate_id"),
                "model_form": row.get("model_form"),
                "single_new_term": row.get("purpose"),
                "data_needed": row.get("data_needed"),
                "current_blocker": row.get("uncertainty_plan"),
                "can_start_now": "see_prior_inventory",
                "suggested_owner_lane": "unassigned",
                "current_run_status_context": "",
            }
        )
    return out


def write_readme(output_dir: Path, ladder: list[dict[str, Any]], missing: list[dict[str, Any]]) -> None:
    best = min(
        [row for row in ladder if math.isfinite(ffloat(row.get("mean_abs_mdot_error_pct")))],
        key=lambda row: ffloat(row["mean_abs_mdot_error_pct"]),
    )
    lines = [
        "# Incremental Model-Form Comparison",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## What This Package Does",
        "",
        "This package reorganizes existing July 1 1D-vs-CFD model-form outputs into an incremental ladder.",
        "It does not run OpenFOAM and does not mutate case data.",
        "",
        "## Current Best Evaluated Form",
        "",
        f"- Best current Salt 2-4 mean |mdot error|: `{ffloat(best['mean_abs_mdot_error_pct']):.3f}%` from `{best['model_form']}`.",
        "- This is an mdot-focused compact fit, not a final physical closure law.",
        "",
        "## Files",
        "",
        "- `incremental_model_form_ladder.csv`: evaluated forms ordered as a one-term-at-a-time ladder.",
        "- `model_form_case_scores.csv`: per-Salt scores for the ladder forms.",
        "- `boundary_sensitivity_ladder.csv`: insulation/radiation sensitivity separated from hydraulic closure form changes.",
        "- `friction_re_only_candidates.csv`: mesh-corrected friction rows for Re-only screening.",
        "- `friction_re_fit_summary.csv`: screen-only log-log f(Re) fits by span/method.",
        "- `missing_model_form_backlog.csv`: model forms not yet fit or not yet supported by data.",
        "",
        "## Immediate Interpretation",
        "",
        "- The current Re-only/major-only proxy is weak by itself.",
        "- A single global major-loss multiplier explains most current mdot improvement, but it is not yet a defended friction law.",
        "- The joint major-plus-bend fit is the best compact mdot score, but improves only marginally over the best one-parameter major-loss fit and is fitted on only Salt 2-4.",
        "- Per-leg friction, thermal UA', and upcomer-cell terms remain the highest-value next model forms.",
        "",
        "## Missing High-Value Forms",
        "",
    ]
    for row in missing[:6]:
        lines.append(f"- `{row['candidate_id']}` `{row['model_form']}`: {row['current_blocker']}")
    output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    model_dir = Path(args.model_form_dir)
    presentation_dir = Path(args.presentation_dir)
    detail_rows = read_csv_rows(model_dir / "model_form_fit_results.csv")
    summary_rows = read_csv_rows(model_dir / "model_form_summary.csv")
    future_rows = read_csv_rows(presentation_dir / "future_model_forms.csv")
    friction_rows = read_csv_rows(Path(args.friction_path))
    run_status_rows = read_csv_rows(Path(args.run_status_path))

    ladder = build_ladder(summary_rows)
    case_scores = build_case_scores(detail_rows)
    boundary = build_boundary_sensitivity(summary_rows)
    friction_table = build_friction_re_table(friction_rows)
    friction_fits = build_friction_fit_summary(friction_table)
    missing = build_missing_backlog(future_rows, run_status_rows)

    csv_dump(output_dir / "incremental_model_form_ladder.csv", list(ladder[0].keys()), ladder)
    csv_dump(output_dir / "model_form_case_scores.csv", list(case_scores[0].keys()), case_scores)
    csv_dump(output_dir / "boundary_sensitivity_ladder.csv", list(boundary[0].keys()), boundary)
    csv_dump(output_dir / "friction_re_only_candidates.csv", list(friction_table[0].keys()), friction_table)
    csv_dump(output_dir / "friction_re_fit_summary.csv", list(friction_fits[0].keys()), friction_fits)
    csv_dump(output_dir / "missing_model_form_backlog.csv", list(missing[0].keys()), missing)
    payload = {
        "generated_at": iso_timestamp(),
        "sources": {
            "model_form_dir": relative_to_workspace(model_dir),
            "presentation_dir": relative_to_workspace(presentation_dir),
            "friction_path": relative_to_workspace(Path(args.friction_path)),
            "run_status_path": relative_to_workspace(Path(args.run_status_path)),
        },
        "best_ladder_form": min(
            [row for row in ladder if math.isfinite(ffloat(row.get("mean_abs_mdot_error_pct")))],
            key=lambda row: ffloat(row["mean_abs_mdot_error_pct"]),
        ),
        "ladder": ladder,
        "missing": missing,
    }
    json_dump(output_dir / "summary.json", payload)
    write_readme(output_dir, ladder, missing)
    print(f"Wrote {relative_to_workspace(output_dir / 'incremental_model_form_ladder.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
