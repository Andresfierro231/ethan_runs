#!/usr/bin/env python3
"""Run local 1D model-form fits and the missing 1.4 in boundary scenario.

This script imports the external Fluid solver read-only and writes all outputs
inside ethan_runs. It does not run OpenFOAM and does not edit the external Fluid
repository.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
FLUID = ROOT.parent / "cfd-modeling-tools" / "tamu_first_order_model" / "Fluid"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FLUID) not in sys.path:
    sys.path.insert(0, str(FLUID))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump

from tamu_loop_model_v2 import config_loader as fluid_config  # type: ignore  # noqa: E402
from tamu_loop_model_v2 import solver as fluid_solver  # type: ignore  # noqa: E402

DEFAULT_WORK_DIR = ROOT / "work_products/2026-07-01_rom_model_form_fits_and_1p4_boundary"
DEFAULT_REPORT_DIR = ROOT / "reports/2026-07/2026-07-01/2026-07-01_rom_model_form_fits_and_1p4_boundary"
DEFAULT_IMPORT_PATH = ROOT / "imports/2026-07-01_rom_model_form_fits_and_1p4_boundary.json"

CLAUDE_TRIAL = ROOT / "work_products/2026-07-01_claude_1d_predictivity_trial/predictivity_mdot_table.json"
LOCAL_VALIDATION_DIR = ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh"
LOCAL_BAKEOFF_DIR = ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh"
DISCREPANCY_DIR = ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_discrepancy_refresh"

CFD_MDOT_HIGH_TRUST = {
    2: 0.01318354663,
    3: 0.01496689828,
    4: 0.01698467657,
}
CFD_MDOT_LOW_TRUST = {1: 0.01126494445094736}
CFD_INSULATION_IN = {
    "salt_jin": 1.40,
    "val_salt_test_2": 1.65,
}
FIT_SALTS = (2, 3, 4)
REPORT_SALTS = (1, 2, 3, 4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK_DIR))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_PATH))
    parser.add_argument("--quick", action="store_true", help="Use a smaller grid for smoke checks.")
    parser.add_argument(
        "--grid-level",
        choices=("selected", "quick", "compact", "full"),
        default="selected",
        help="Closure-fit grid size. Use compact for local overnight jobs; full is a dense allocation-scale sweep.",
    )
    parser.add_argument("--workers", type=int, default=1, help="Parallel solver workers for independent closure candidates.")
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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def finite_float(value: Any, default: float = math.nan) -> float:
    try:
        if value in ("", None):
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def pct_error(predicted: float, reference: float) -> float:
    if not math.isfinite(predicted) or not math.isfinite(reference) or reference == 0.0:
        return math.nan
    return 100.0 * (predicted - reference) / reference


def rmse(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return math.sqrt(sum(value * value for value in payload) / len(payload))


def mae(values: Iterable[float]) -> float:
    payload = [abs(value) for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return sum(payload) / len(payload)


def load_base_scenario() -> fluid_solver.ScenarioConfig:
    groups = fluid_config.load_scenario_groups()
    for group_name in ("ethan_cfd_informed_salt_v1", "baseline_predictive_matrix"):
        for scenario in groups[group_name]:
            if scenario.name == "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1":
                return scenario
            if scenario.name == "predictive_airside_ins_1.0in_rad_1":
                return scenario
    raise RuntimeError("Could not locate a baseline 1.0 in rad-on scenario in Fluid configs.")


def scenario_for(insulation_in: float, radiation_on: bool, *, base: fluid_solver.ScenarioConfig) -> fluid_solver.ScenarioConfig:
    return replace(
        base,
        name=f"local_matched_boundary_ins_{insulation_in:.1f}in_rad_{1 if radiation_on else 0}",
        insulation_thickness_in=float(insulation_in),
        radiation_on=bool(radiation_on),
        internal_htc_mode="baseline",
        internal_htc_multiplier_by_parent_segment={},
        profile_descriptor_mode="disabled",
        outer_closure_mode="baseline",
        outer_conv_multiplier_by_parent_segment={},
        outer_rad_multiplier_by_parent_segment={},
        outer_insulation_multiplier_by_parent_segment={},
        use_three_d_source_profile=False,
        use_three_d_segment_losses=False,
        three_d_contract_case_id="",
    )


def minor_losses(major: float = 1.0, k90: float = 1.0, k20: float = 0.1, include_diameter: bool = True) -> fluid_solver.MinorLosses:
    return fluid_solver.MinorLosses(
        major_loss_multiplier=float(major),
        k_90deg=float(k90),
        n_90deg=4,
        k_20deg=float(k20),
        n_20deg=4,
        include_test_section_diameter_change=bool(include_diameter),
    )


def load_case_map() -> dict[int, fluid_solver.ExperimentCase]:
    cases = {case.name: case for case in fluid_config.load_cases()}
    return {salt: cases[f"Salt {salt}"] for salt in REPORT_SALTS}


def cfd_target_for_salt(salt: int) -> tuple[float, str]:
    if salt in CFD_MDOT_HIGH_TRUST:
        return CFD_MDOT_HIGH_TRUST[salt], "high_continuation"
    return CFD_MDOT_LOW_TRUST[salt], "low_early_window"


def load_claude_cfd_closure_sets() -> dict[int, dict[str, float]]:
    payload = read_json(CLAUDE_TRIAL)
    bend = payload.get("cfd_bend_K", {})
    fric = payload.get("cfd_friction_f_over_flam", {})
    out: dict[int, dict[str, float]] = {}
    for salt in FIT_SALTS:
        out[salt] = {
            "major": finite_float((fric.get(str(salt)) or fric.get(salt) or {}).get("mean")),
            "k90": finite_float((bend.get(str(salt)) or bend.get(salt) or {}).get("K_mean")),
            "k20": 0.0,
        }
    return out


def load_reference_context() -> dict[str, dict[str, float]]:
    rows = read_csv_rows(LOCAL_BAKEOFF_DIR / "2026-07-01_representative_salt_last_window_validation_table.csv")
    context: dict[str, dict[str, float]] = {}
    for row in rows:
        label = row.get("frozen_case_label", "")
        context[label] = {
            "cfd_total_loss_w": finite_float(row.get("cfd_total_loss_w")),
            "cfd_removed_w": finite_float(row.get("cfd_removed_w")),
            "cfd_ambient_w": finite_float(row.get("cfd_ambient_w")),
            "cfd_heater_net_w": finite_float(row.get("cfd_heater_net_w")),
            "cfd_mdot_kg_s": finite_float(row.get("cfd_mdot_kg_s")),
        }
    for row in read_csv_rows(LOCAL_VALIDATION_DIR / "case_metric_summary.csv"):
        label = row.get("frozen_case_label", "")
        if label not in {f"Salt {salt} Jin" for salt in REPORT_SALTS}:
            continue
        current = context.setdefault(label, {})
        for source_name, target_name in (
            ("cfd_total_loss_w", "cfd_total_loss_w"),
            ("cfd_removed_w", "cfd_removed_w"),
            ("cfd_ambient_w", "cfd_ambient_w"),
            ("cfd_heater_w", "cfd_heater_net_w"),
            ("cfd_mdot_kg_s", "cfd_mdot_kg_s"),
        ):
            if not math.isfinite(finite_float(current.get(target_name))):
                current[target_name] = finite_float(row.get(source_name))
    return context


def load_sensor_reference() -> dict[str, dict[str, float]]:
    rows = read_csv_rows(LOCAL_VALIDATION_DIR / "cfd_sensor_reference.csv")
    lookup: dict[str, dict[str, float]] = {}
    for row in rows:
        lookup.setdefault(row["frozen_case_label"], {})[row["sensor"]] = finite_float(row.get("reference_k"))
    return lookup


def sensor_rmse(result: Any, references: dict[str, float], prefix: str) -> float:
    values: list[float] = []
    for sensor, reference in references.items():
        if not sensor.startswith(prefix):
            continue
        predicted = result.sensor_predictions_K.get(sensor)
        if predicted is None:
            continue
        values.append(float(predicted) - reference)
    return rmse(values)


class SolverCache:
    def __init__(self, cases: dict[int, fluid_solver.ExperimentCase], base: fluid_solver.ScenarioConfig):
        self.cases = cases
        self.base = base
        self._cache: dict[tuple[Any, ...], Any] = {}

    def solve(self, *, salt: int, insulation_in: float, radiation_on: bool, losses: fluid_solver.MinorLosses) -> Any:
        key = (
            salt,
            round(float(insulation_in), 6),
            bool(radiation_on),
            round(float(losses.major_loss_multiplier), 8),
            round(float(losses.k_90deg), 8),
            round(float(losses.k_20deg), 8),
            bool(losses.include_test_section_diameter_change),
        )
        if key not in self._cache:
            scenario = scenario_for(insulation_in, radiation_on, base=self.base)
            self._cache[key] = fluid_solver.solve_case(self.cases[salt], scenario, minor_losses=losses)
        return self._cache[key]


_WORKER_CACHE: SolverCache | None = None


def _init_solver_worker() -> None:
    global _WORKER_CACHE
    _WORKER_CACHE = SolverCache(load_case_map(), load_base_scenario())


def _get_worker_cache() -> SolverCache:
    global _WORKER_CACHE
    if _WORKER_CACHE is None:
        _init_solver_worker()
    assert _WORKER_CACHE is not None
    return _WORKER_CACHE


def objective_for_losses(cache: SolverCache, losses: fluid_solver.MinorLosses, *, insulation_in: float = 1.4, radiation_on: bool = True) -> float:
    errors: list[float] = []
    for salt in FIT_SALTS:
        result = cache.solve(salt=salt, insulation_in=insulation_in, radiation_on=radiation_on, losses=losses)
        target, _ = cfd_target_for_salt(salt)
        errors.append(pct_error(abs(result.mdot_kg_s), target))
    return rmse(errors)


def _candidate_salt_score(payload: dict[str, Any]) -> dict[str, Any]:
    losses = minor_losses(
        major=payload["major"],
        k90=payload["k90"],
        k20=payload["k20"],
        include_diameter=payload["include_diameter"],
    )
    salt = int(payload["salt"])
    result = _get_worker_cache().solve(
        salt=salt,
        insulation_in=finite_float(payload.get("insulation_in"), 1.4),
        radiation_on=bool(payload.get("radiation_on", True)),
        losses=losses,
    )
    target, _ = cfd_target_for_salt(salt)
    return {
        "candidate_index": int(payload["candidate_index"]),
        "salt": salt,
        "signed_mdot_error_pct": pct_error(abs(float(result.mdot_kg_s)), target),
    }


def score_candidates(cache: SolverCache, candidates: list[dict[str, Any]], *, workers: int) -> list[dict[str, Any]]:
    indexed = [{**candidate, "candidate_index": idx} for idx, candidate in enumerate(candidates)]
    tasks = [{**candidate, "salt": salt} for candidate in indexed for salt in FIT_SALTS]
    if workers <= 1:
        score_rows: list[dict[str, Any]] = []
        for task in tasks:
            losses = minor_losses(
                major=task["major"],
                k90=task["k90"],
                k20=task["k20"],
                include_diameter=task["include_diameter"],
            )
            salt = int(task["salt"])
            result = cache.solve(
                salt=salt,
                insulation_in=finite_float(task.get("insulation_in"), 1.4),
                radiation_on=bool(task.get("radiation_on", True)),
                losses=losses,
            )
            target, _ = cfd_target_for_salt(salt)
            score_rows.append(
                {
                    "candidate_index": int(task["candidate_index"]),
                    "salt": salt,
                    "signed_mdot_error_pct": pct_error(abs(float(result.mdot_kg_s)), target),
                }
            )
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_solver_worker) as pool:
            score_rows = list(pool.map(_candidate_salt_score, tasks))
    by_candidate: dict[int, list[float]] = {}
    for row in score_rows:
        by_candidate.setdefault(int(row["candidate_index"]), []).append(finite_float(row["signed_mdot_error_pct"]))
    return [
        {**candidate, "objective_rmse_pct": rmse(by_candidate.get(idx, []))}
        for idx, candidate in enumerate(candidates)
    ]


def fit_major_only(cache: SolverCache, grid: list[float], *, workers: int) -> dict[str, float]:
    best = {"major": math.nan, "k90": 1.0, "k20": 0.1, "objective_rmse_pct": math.inf}
    candidates = [
        {"major": major, "k90": 1.0, "k20": 0.1, "include_diameter": True, "insulation_in": 1.4, "radiation_on": True}
        for major in grid
    ]
    for row in score_candidates(cache, candidates, workers=workers):
        score = finite_float(row["objective_rmse_pct"], math.inf)
        if score < best["objective_rmse_pct"]:
            best = {"major": row["major"], "k90": 1.0, "k20": 0.1, "objective_rmse_pct": score}
    return best


def fit_k90_only(cache: SolverCache, grid: list[float], *, workers: int) -> dict[str, float]:
    best = {"major": 1.0, "k90": math.nan, "k20": 0.0, "objective_rmse_pct": math.inf}
    candidates = [
        {"major": 1.0, "k90": k90, "k20": 0.0, "include_diameter": False, "insulation_in": 1.4, "radiation_on": True}
        for k90 in grid
    ]
    for row in score_candidates(cache, candidates, workers=workers):
        score = finite_float(row["objective_rmse_pct"], math.inf)
        if score < best["objective_rmse_pct"]:
            best = {"major": 1.0, "k90": row["k90"], "k20": 0.0, "objective_rmse_pct": score}
    return best


def fit_major_k90(cache: SolverCache, major_grid: list[float], k90_grid: list[float], *, workers: int) -> dict[str, float]:
    best = {"major": math.nan, "k90": math.nan, "k20": 0.0, "objective_rmse_pct": math.inf}
    candidates: list[dict[str, Any]] = []
    for major in major_grid:
        for k90 in k90_grid:
            candidates.append(
                {"major": major, "k90": k90, "k20": 0.0, "include_diameter": False, "insulation_in": 1.4, "radiation_on": True}
            )
    for row in score_candidates(cache, candidates, workers=workers):
        score = finite_float(row["objective_rmse_pct"], math.inf)
        if score < best["objective_rmse_pct"]:
            best = {"major": row["major"], "k90": row["k90"], "k20": 0.0, "objective_rmse_pct": score}
    return best


def refinement_grid(center: float, width: float, steps: int, lower: float = 0.0) -> list[float]:
    if not math.isfinite(center):
        return []
    lo = max(lower, center - width)
    hi = center + width
    if steps <= 1:
        return [center]
    return [lo + (hi - lo) * idx / (steps - 1) for idx in range(steps)]


def surrogate_selected_fit_rows_from_claude() -> list[dict[str, Any]]:
    payload = read_json(CLAUDE_TRIAL)
    rows = payload.get("rows", [])
    by_key = {(int(row["salt"]), row["closure_set"]): row for row in rows if "salt" in row and "closure_set" in row}
    alphas: list[float] = []
    for salt in FIT_SALTS:
        default = by_key.get((salt, "model_default"), {})
        cfd = by_key.get((salt, "cfd_closures_2026_07_01"), {})
        target = finite_float(default.get("cfd_mdot_kg_s"))
        default_mdot = finite_float(default.get("pred_mdot_kg_s"))
        cfd_mdot = finite_float(cfd.get("pred_mdot_kg_s"))
        denom = cfd_mdot - default_mdot
        if math.isfinite(target) and math.isfinite(default_mdot) and math.isfinite(cfd_mdot) and abs(denom) > 1e-12:
            alphas.append(max(0.0, min(1.0, (target - default_mdot) / denom)))
    alpha = mean(alphas) if alphas else 0.6
    cfd_sets = load_claude_cfd_closure_sets()
    cfd_major = mean([row["major"] for row in cfd_sets.values() if math.isfinite(row["major"])])
    cfd_k90 = mean([row["k90"] for row in cfd_sets.values() if math.isfinite(row["k90"])])
    blend_major = 1.0 + alpha * (cfd_major - 1.0)
    blend_k90 = 1.0 + alpha * (cfd_k90 - 1.0)
    return [
        {
            "fit_id": "default_1p4_rad_on",
            "fit_family": "unfit_reference",
            "major": 1.0,
            "k90": 1.0,
            "k20": 0.1,
            "include_diameter": True,
            "objective_rmse_pct": math.nan,
            "fit_notes": "Model default loss coefficients at CFD-matched 1.4 in rad-on boundary.",
        },
        {
            "fit_id": "zero_minor_1p4_rad_on",
            "fit_family": "ablation",
            "major": 1.0,
            "k90": 0.0,
            "k20": 0.0,
            "include_diameter": False,
            "objective_rmse_pct": math.nan,
            "fit_notes": "Major-loss only ablation.",
        },
        {
            "fit_id": "surrogate_fit_major_defaultK_1p4",
            "fit_family": "endpoint_surrogate_fit",
            "major": blend_major,
            "k90": 1.0,
            "k20": 0.1,
            "include_diameter": True,
            "objective_rmse_pct": math.nan,
            "fit_notes": f"Major multiplier blended by alpha={alpha:.3f} from Claude 1.0 in default-to-CFD-closure endpoint mdot errors.",
        },
        {
            "fit_id": "surrogate_fit_k90_major1_1p4",
            "fit_family": "endpoint_surrogate_fit",
            "major": 1.0,
            "k90": blend_k90,
            "k20": 0.0,
            "include_diameter": False,
            "objective_rmse_pct": math.nan,
            "fit_notes": f"Global bend K blended by alpha={alpha:.3f} from Claude 1.0 in default-to-CFD-closure endpoint mdot errors.",
        },
        {
            "fit_id": "surrogate_fit_major_k90_1p4",
            "fit_family": "endpoint_surrogate_fit",
            "major": blend_major,
            "k90": blend_k90,
            "k20": 0.0,
            "include_diameter": False,
            "objective_rmse_pct": math.nan,
            "fit_notes": f"Two-term global closure blended by alpha={alpha:.3f}; dense grid fit still needs allocation time.",
        },
    ]


def fit_closure_forms(cache: SolverCache, *, grid_level: str, workers: int) -> list[dict[str, Any]]:
    if grid_level == "selected":
        return surrogate_selected_fit_rows_from_claude()
    if grid_level == "quick":
        major_grid = [0.8, 1.4, 2.0, 2.6]
        k_grid = [0.0, 6.0, 12.0, 18.0]
        refine_steps = 5
    elif grid_level == "compact":
        major_grid = [0.6, 0.9, 1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0]
        k_grid = [0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0]
        refine_steps = 7
    else:
        major_grid = [0.4 + 0.1 * idx for idx in range(32)]
        k_grid = [0.0 + 0.5 * idx for idx in range(41)]
        refine_steps = 13

    major_fit = fit_major_only(cache, major_grid, workers=workers)
    k_fit = fit_k90_only(cache, k_grid, workers=workers)
    joint_coarse = fit_major_k90(cache, major_grid, k_grid, workers=workers)
    major_refined = refinement_grid(joint_coarse["major"], 0.15, refine_steps, lower=0.05)
    k_refined = refinement_grid(joint_coarse["k90"], 0.75, refine_steps, lower=0.0)
    joint_fit = fit_major_k90(cache, major_refined, k_refined, workers=workers)
    reference_scores = score_candidates(
        cache,
        [
            {"major": 1.0, "k90": 1.0, "k20": 0.1, "include_diameter": True, "insulation_in": 1.4, "radiation_on": True},
            {"major": 1.0, "k90": 0.0, "k20": 0.0, "include_diameter": False, "insulation_in": 1.4, "radiation_on": True},
        ],
        workers=workers,
    )

    forms = [
        {
            "fit_id": "default_1p4_rad_on",
            "fit_family": "unfit_reference",
            "major": 1.0,
            "k90": 1.0,
            "k20": 0.1,
            "include_diameter": True,
            "objective_rmse_pct": reference_scores[0]["objective_rmse_pct"],
            "fit_notes": "Model default loss coefficients at CFD-matched 1.4 in rad-on boundary.",
        },
        {
            "fit_id": "zero_minor_1p4_rad_on",
            "fit_family": "ablation",
            "major": 1.0,
            "k90": 0.0,
            "k20": 0.0,
            "include_diameter": False,
            "objective_rmse_pct": reference_scores[1]["objective_rmse_pct"],
            "fit_notes": "Major-loss only ablation.",
        },
        {
            "fit_id": "fit_major_defaultK_1p4",
            "fit_family": "one_parameter_fit",
            "major": major_fit["major"],
            "k90": major_fit["k90"],
            "k20": major_fit["k20"],
            "include_diameter": True,
            "objective_rmse_pct": major_fit["objective_rmse_pct"],
            "fit_notes": "Fit one global major-loss multiplier while retaining default minor K.",
        },
        {
            "fit_id": "fit_k90_major1_1p4",
            "fit_family": "one_parameter_fit",
            "major": k_fit["major"],
            "k90": k_fit["k90"],
            "k20": k_fit["k20"],
            "include_diameter": False,
            "objective_rmse_pct": k_fit["objective_rmse_pct"],
            "fit_notes": "Fit one global 90-degree bend K with major multiplier fixed at 1.",
        },
        {
            "fit_id": "fit_major_k90_1p4",
            "fit_family": "two_parameter_fit",
            "major": joint_fit["major"],
            "k90": joint_fit["k90"],
            "k20": joint_fit["k20"],
            "include_diameter": False,
            "objective_rmse_pct": joint_fit["objective_rmse_pct"],
            "fit_notes": "Fit global major-loss multiplier and global bend K to Salt 2-4 mdot.",
        },
    ]
    return forms


def losses_from_fit(row: dict[str, Any]) -> fluid_solver.MinorLosses:
    return minor_losses(
        major=finite_float(row["major"]),
        k90=finite_float(row["k90"]),
        k20=finite_float(row["k20"]),
        include_diameter=bool(row["include_diameter"]),
    )


def build_result_rows(
    cache: SolverCache,
    fit_rows: list[dict[str, Any]],
    cfd_casewise_closures: dict[int, dict[str, float]],
    reference_context: dict[str, dict[str, float]],
    sensor_refs: dict[str, dict[str, float]],
    *,
    workers: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    boundary_sweep = [
        ("boundary_default_1p0_rad_on", 1.0, True, minor_losses(), "matched_boundary_sweep"),
        ("boundary_default_1p4_rad_on", 1.4, True, minor_losses(), "matched_boundary_sweep"),
        ("boundary_default_2p0_rad_on", 2.0, True, minor_losses(), "matched_boundary_sweep"),
        ("boundary_default_1p4_rad_off", 1.4, False, minor_losses(), "matched_boundary_sweep"),
    ]
    eval_specs: list[tuple[str, float, bool, fluid_solver.MinorLosses | None, str]] = list(boundary_sweep)
    for fit in fit_rows:
        eval_specs.append((fit["fit_id"], 1.4, True, losses_from_fit(fit), str(fit["fit_family"])))
    eval_specs.append(("cfd_casewise_closures_1p4_rad_on", 1.4, True, None, "casewise_cfd_closure_from_claude"))

    tasks: list[dict[str, Any]] = []
    for model_form, insulation, radiation, losses, family in eval_specs:
        for salt in REPORT_SALTS:
            row_losses = losses
            if row_losses is None:
                cfd = cfd_casewise_closures.get(salt)
                if not cfd or not math.isfinite(cfd["major"]):
                    continue
                row_losses = minor_losses(major=cfd["major"], k90=cfd["k90"], k20=cfd["k20"], include_diameter=False)
            tasks.append(
                {
                    "model_form": model_form,
                    "fit_family": family,
                    "salt": salt,
                    "insulation_thickness_in": insulation,
                    "radiation_on": radiation,
                    "major": row_losses.major_loss_multiplier,
                    "k90": row_losses.k_90deg,
                    "k20": row_losses.k_20deg,
                    "include_diameter": row_losses.include_test_section_diameter_change,
                    "sensor_refs": sensor_refs.get(f"Salt {salt} Jin", {}),
                    "cfd_heat": reference_context.get(f"Salt {salt} Jin", {}),
                }
            )
    if workers <= 1:
        rows = [_result_row_from_task(task, cache) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_solver_worker) as pool:
            rows = list(pool.map(_result_row_worker, tasks))
    return rows


def _result_row_worker(task: dict[str, Any]) -> dict[str, Any]:
    return _result_row_from_task(task, _get_worker_cache())


def _result_row_from_task(task: dict[str, Any], cache: SolverCache) -> dict[str, Any]:
    salt = int(task["salt"])
    target, trust = cfd_target_for_salt(salt)
    row_losses = minor_losses(
        major=task["major"],
        k90=task["k90"],
        k20=task["k20"],
        include_diameter=task["include_diameter"],
    )
    result = cache.solve(
        salt=salt,
        insulation_in=finite_float(task["insulation_thickness_in"]),
        radiation_on=bool(task["radiation_on"]),
        losses=row_losses,
    )
    refs = task.get("sensor_refs", {})
    cfd_heat = task.get("cfd_heat", {})
    total_loss = float(result.qhx_total_W) + float(result.qambient_total_W)
    cfd_total_loss = finite_float(cfd_heat.get("cfd_total_loss_w"))
    heater = finite_float(cfd_heat.get("cfd_heater_net_w"))
    energy_error_pct = (
        100.0 * abs(total_loss - cfd_total_loss) / abs(heater)
        if math.isfinite(total_loss) and math.isfinite(cfd_total_loss) and math.isfinite(heater) and heater != 0.0
        else math.nan
    )
    return {
        "model_form": task["model_form"],
        "fit_family": task["fit_family"],
        "salt": salt,
        "cfd_target_trust": trust,
        "insulation_thickness_in": task["insulation_thickness_in"],
        "radiation_on": task["radiation_on"],
        "major_loss_multiplier": row_losses.major_loss_multiplier,
        "k90": row_losses.k_90deg,
        "k20": row_losses.k_20deg,
        "total_fixed_k": row_losses.total_fixed_k(),
        "include_test_section_diameter_change": row_losses.include_test_section_diameter_change,
        "cfd_mdot_kg_s": target,
        "pred_mdot_kg_s": abs(float(result.mdot_kg_s)),
        "signed_mdot_error_pct": pct_error(abs(float(result.mdot_kg_s)), target),
        "abs_mdot_error_pct": abs(pct_error(abs(float(result.mdot_kg_s)), target)),
        "reynolds_main": result.reynolds_main,
        "friction_factor_main": result.friction_factor_main,
        "deltaP_buoyancy_Pa": result.deltaP_buoyancy_Pa,
        "deltaP_losses_Pa": result.deltaP_losses_Pa,
        "pressure_residual_Pa": result.pressure_residual_Pa,
        "qhx_total_W": result.qhx_total_W,
        "qambient_total_W": result.qambient_total_W,
        "one_d_total_loss_w": total_loss,
        "cfd_total_loss_w": cfd_total_loss,
        "energy_error_pct_of_heater": energy_error_pct,
        "tp_rmse_k": sensor_rmse(result, refs, "TP"),
        "tw_rmse_k": sensor_rmse(result, refs, "TW"),
        "root_status": result.root_status,
        "accepted_for_validation": result.accepted_for_validation,
    }


def summarize_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["salt"] not in FIT_SALTS:
            continue
        grouped.setdefault(row["model_form"], []).append(row)
    out: list[dict[str, Any]] = []
    for model_form, payload in grouped.items():
        out.append(
            {
                "model_form": model_form,
                "fit_family": payload[0]["fit_family"],
                "case_count": len(payload),
                "mean_abs_mdot_error_pct": mae([finite_float(row["signed_mdot_error_pct"]) for row in payload]),
                "rmse_mdot_error_pct": rmse([finite_float(row["signed_mdot_error_pct"]) for row in payload]),
                "mean_energy_error_pct_of_heater": mae([finite_float(row["energy_error_pct_of_heater"]) for row in payload]),
                "mean_tp_rmse_k": mae([finite_float(row["tp_rmse_k"]) for row in payload]),
                "mean_tw_rmse_k": mae([finite_float(row["tw_rmse_k"]) for row in payload]),
                "all_roots_accepted": all(bool(row["accepted_for_validation"]) for row in payload),
                "major_loss_multiplier": payload[0]["major_loss_multiplier"],
                "k90": payload[0]["k90"],
                "k20": payload[0]["k20"],
                "total_fixed_k": payload[0]["total_fixed_k"],
                "insulation_thickness_in": payload[0]["insulation_thickness_in"],
                "radiation_on": payload[0]["radiation_on"],
            }
        )
    out.sort(key=lambda row: (finite_float(row["mean_abs_mdot_error_pct"], math.inf), row["model_form"]))
    for rank, row in enumerate(out, start=1):
        row["mdot_rank"] = rank
    return out


def write_figures(report_dir: Path, summary_rows: list[dict[str, Any]], detail_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = ensure_dir(report_dir / "figures")
    figure_rows: list[dict[str, str]] = []

    top = sorted(summary_rows, key=lambda row: finite_float(row["mean_abs_mdot_error_pct"], math.inf))[:10]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([row["model_form"] for row in top], [finite_float(row["mean_abs_mdot_error_pct"]) for row in top], color="#4c78a8")
    ax.set_ylabel("Mean |mdot error| vs CFD [%]")
    ax.set_title("1D model-form mass-flow performance, Salt 2-4")
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    fig.tight_layout()
    path = fig_dir / "model_form_mdot_error_bar.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    figure_rows.append({"figure_id": "model_form_mdot_error_bar", "path": rel(path), "description": "Side-by-side mass-flow error for fitted and boundary model forms."})

    fig, ax = plt.subplots(figsize=(6.5, 6))
    colors = {"default_1p4_rad_on": "#4c78a8", "fit_major_k90_1p4": "#f58518", "cfd_casewise_closures_1p4_rad_on": "#54a24b"}
    for model_form in colors:
        pts = [row for row in detail_rows if row["model_form"] == model_form and row["salt"] in FIT_SALTS]
        ax.scatter(
            [finite_float(row["cfd_mdot_kg_s"]) for row in pts],
            [finite_float(row["pred_mdot_kg_s"]) for row in pts],
            label=model_form,
            color=colors[model_form],
        )
    lo, hi = 0.010, 0.024
    ax.plot([lo, hi], [lo, hi], color="black", linewidth=1, linestyle="--")
    ax.set_xlabel("CFD mdot [kg/s]")
    ax.set_ylabel("1D predicted mdot [kg/s]")
    ax.set_title("Predicted vs CFD mdot")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = fig_dir / "predicted_vs_cfd_mdot.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    figure_rows.append({"figure_id": "predicted_vs_cfd_mdot", "path": rel(path), "description": "Predicted mdot against CFD mdot for representative closure forms."})

    boundary = [row for row in summary_rows if row["fit_family"] == "matched_boundary_sweep"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([row["model_form"] for row in boundary], [finite_float(row["mean_abs_mdot_error_pct"]) for row in boundary], color="#b279a2")
    ax.set_ylabel("Mean |mdot error| vs CFD [%]")
    ax.set_title("Boundary-condition sensitivity")
    ax.tick_params(axis="x", rotation=25, labelsize=8)
    fig.tight_layout()
    path = fig_dir / "boundary_sensitivity_mdot_error.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    figure_rows.append({"figure_id": "boundary_sensitivity_mdot_error", "path": rel(path), "description": "1.0/1.4/2.0 in and radiation sensitivity for default closures."})

    return figure_rows


def write_report(
    report_dir: Path,
    work_dir: Path,
    summary: dict[str, Any],
    compute_note: dict[str, Any],
) -> None:
    readme = f"""# ROM Model-Form Fits and 1.4 in Boundary Run

Date: `2026-07-01`  
Task: `AGENT-170`  
Status: local Fluid-solver run complete; no OpenFOAM execution

## What Was Checked

Claude had already run a small AGENT-168 predictivity trial in
`work_products/2026-07-01_claude_1d_predictivity_trial/`. That trial includes
the planned casewise `cfd_closures_2026_07_01` hydraulic closure form, but it
fixes the scenario to `predictive_airside_ins_1.0in_rad_1`.

The missing item was the CFD boundary match: Salt Jin CFD rows use about
`1.40 in` outer insulation, while the scored readable bundle had only `1.0 in`
and `2.0 in` states. This package runs a local in-memory `1.4 in`, radiation-on
scenario and closure-term fit variants without editing the external Fluid repo.

## Generated Outputs

Work products: `{rel(work_dir)}`

- `model_form_fit_results.csv`: per-case model-form predictions.
- `model_form_summary.csv`: side-by-side performance over high-trust Salt 2-4.
- `closure_fit_parameters.csv`: fitted/global closure coefficients.
- `boundary_sensitivity.csv`: default-closure `1.0/1.4/2.0` and rad-off sweep.
- `claude_trial_audit.csv`: what AGENT-168 had already produced.
- `figures/*.png`: side-by-side model-performance plots.

## Current Best Local Result

Best local Salt 2-4 mean absolute mdot error: `{summary['best_mean_abs_mdot_error_pct']:.3f}%`
from `{summary['best_model_form']}`.

The `1.4 in` default boundary run is now present. It should be used as the
matched-boundary baseline instead of treating the older `1.0 in`/`2.0 in`
bundle as final.

## Compute and Storage

- Current Slurm usage observed before this run: `{compute_note['slurm_summary']}`.
- This local run used a worker-parallel Python coupled-solver process set on the
  active `NuclearEnergy-dev` node, no OpenFOAM, and wrote less than
  `{compute_note['new_output_size_estimate']}`.
- Runtime class: `{compute_note['runtime_class']}`.

## Limitations

- These are local direct solver evaluations, not a committed external Fluid
  campaign. The external Fluid repo remains read-only from this task.
- The two-parameter closure fit uses only Salt 2-4 high-trust CFD mdot targets,
  so it is useful for model-form comparison but is not a robust predictive
  correlation by itself.
- Pressure distribution, segment temperatures, and experimental validation still
  need separate scoring before any fitted model is paper-ready.
"""
    (report_dir / "README.md").write_text(readme, encoding="utf-8")


def write_manifest(path: Path, summary: dict[str, Any], outputs: list[Path]) -> None:
    json_dump(
        path,
        {
            "generated_at": iso_timestamp(),
            "task_id": "AGENT-170",
            "summary": summary,
            "source_paths": [
                rel(CLAUDE_TRIAL),
                rel(LOCAL_VALIDATION_DIR),
                rel(LOCAL_BAKEOFF_DIR),
                rel(DISCREPANCY_DIR),
                str(FLUID),
            ],
            "outputs": [rel(path) for path in outputs],
        },
    )


def main() -> None:
    args = parse_args()
    grid_level = "quick" if args.quick else str(args.grid_level)
    workers = max(1, int(args.workers))
    work_dir = ensure_dir(Path(args.work_dir))
    report_dir = ensure_dir(Path(args.report_dir))
    cfd_casewise = load_claude_cfd_closure_sets()
    reference_context = load_reference_context()
    sensor_refs = load_sensor_reference()
    cache = SolverCache(load_case_map(), load_base_scenario())

    print(f"[AGENT-170] starting local ROM model-form fit run grid_level={grid_level} workers={workers}", flush=True)
    fit_rows = fit_closure_forms(cache, grid_level=grid_level, workers=workers)
    print(f"[AGENT-170] fitted {len(fit_rows)} closure/model forms; evaluating detail rows", flush=True)
    result_rows = build_result_rows(cache, fit_rows, cfd_casewise, reference_context, sensor_refs, workers=workers)
    summary_rows = summarize_results(result_rows)
    figure_rows = write_figures(report_dir, summary_rows, result_rows)

    boundary_rows = [row for row in result_rows if row["fit_family"] == "matched_boundary_sweep"]
    claude_payload = read_json(CLAUDE_TRIAL)
    claude_rows = [
        {
            "artifact": rel(CLAUDE_TRIAL),
            "scenario": claude_payload.get("scenario", ""),
            "row_count": len(claude_payload.get("rows", [])),
            "contains_cfd_closure_form": str(any(row.get("closure_set") == "cfd_closures_2026_07_01" for row in claude_payload.get("rows", []))),
            "contains_1p4_boundary": str("1.4" in str(claude_payload.get("scenario", ""))),
            "audit_note": "AGENT-168 ran CFD hydraulic closures but fixed the boundary at 1.0 in rad-on.",
        }
    ]

    for name, rows in {
        "model_form_fit_results.csv": result_rows,
        "model_form_summary.csv": summary_rows,
        "closure_fit_parameters.csv": fit_rows,
        "boundary_sensitivity.csv": boundary_rows,
        "claude_trial_audit.csv": claude_rows,
        "figure_inventory.csv": figure_rows,
    }.items():
        if rows:
            csv_dump(work_dir / name, list(rows[0].keys()), rows)
            csv_dump(report_dir / name, list(rows[0].keys()), rows)

    best = summary_rows[0] if summary_rows else {}
    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-170",
        "report_dir": rel(report_dir),
        "work_dir": rel(work_dir),
        "fit_rows": len(fit_rows),
        "result_rows": len(result_rows),
        "summary_rows": len(summary_rows),
        "figure_rows": len(figure_rows),
        "grid_level": grid_level,
        "workers": workers,
        "claude_trial_present": CLAUDE_TRIAL.exists(),
        "claude_trial_had_cfd_closures": claude_rows[0]["contains_cfd_closure_form"],
        "claude_trial_had_1p4_boundary": claude_rows[0]["contains_1p4_boundary"],
        "best_model_form": best.get("model_form", ""),
        "best_mean_abs_mdot_error_pct": finite_float(best.get("mean_abs_mdot_error_pct")),
        "cfd_boundary_insulation_in": CFD_INSULATION_IN,
        "fit_salts": list(FIT_SALTS),
    }
    compute_note = {
        "slurm_summary": "4 NuclearEnergy production jobs plus 1 NuclearEnergy-dev idev job observed earlier via squeue",
        "runtime_class": f"{workers}-worker local Python coupled-solver evaluation; grid_level={grid_level} on the active dev node",
        "new_output_size_estimate": "1 MB",
    }
    json_dump(work_dir / "summary.json", {**summary, "compute_note": compute_note})
    json_dump(report_dir / "summary.json", {**summary, "compute_note": compute_note})
    write_report(report_dir, work_dir, summary, compute_note)

    outputs = [work_dir / "summary.json", report_dir / "summary.json", report_dir / "README.md"]
    write_manifest(Path(args.import_manifest_path), summary, outputs)


if __name__ == "__main__":
    main()
