#!/usr/bin/env python3
"""Re-present the CFD-derived friction / Nusselt closures HONESTLY (action #3).

WHY THIS EXISTS
---------------
The inspection found the 1D closures are sold as correlations f(Re), Nu(Re,Pr)
but are actually calibrated from only ~3 physically-distinct LAMINAR salt cases,
over a narrow Re band that is itself partly an ARTIFACT of swapping the salt
viscosity model (Jin vs Kirst). This tool re-presents the same numbers so the
confidence boundary is explicit:

  1. Per-PHYSICAL-CASE table of apparent Darcy f and Nu with Re/Pr labelled.
  2. Separation of the two axes that the legacy fit conflates:
       * physical-case axis (Salt 2 vs 3 vs 4: genuinely different operating pts)
       * property-model axis (Jin vs Kirst: SAME physical case, different mu ->
         different Re). We quantify how much of the apparent "Re dependence" is
         really property-model disagreement.
  3. Context vs the fully-developed laminar reference f_lam = 64/Re: the apparent
     f is reported as a MULTIPLE of f_lam ("excess-loss factor"), making clear
     it lumps form/entrance/curvature losses and is NOT a wall-friction factor.
  4. Honesty metrics for each fit: #physical cases, #points, #free parameters,
     degrees of freedom, R^2, and the Re validity window.
  5. A reusable Re-domain guard so the 1D solver can flag extrapolation.
  6. A test of whether Pr is actually a meaningful Nu regressor (it is nominally
     consumed by the model) given the available Pr spread.

Scope (user decision 2026-06-30): paper-grade fits use Salt **Jin** only; Kirst
and val rows are carried as sensitivity context and reported but not used in the
paper fit. All choices are recorded in the output.

Read-only over existing fit-ready CSVs; no CFD runtime needed.

USAGE
  python tools/analyze/represent_closures_per_case.py
  python tools/analyze/represent_closures_per_case.py --hydraulic-csv ... --thermal-csv ...
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
    safe_float,
)

DEFAULT_HYDRAULIC_CSV = (
    WORKSPACE_ROOT
    / "reports/2026-06/2026-06-22/2026-06-22_ethan_salt_model_dependency_package_v4/hydraulic_fit_ready_rows.csv"
)
DEFAULT_THERMAL_CSV = (
    WORKSPACE_ROOT
    / "reports/2026-06/2026-06-22/2026-06-22_ethan_salt_model_dependency_package_v4/thermal_fit_ready_rows.csv"
)
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_closure_representation"

# Fully-developed laminar circular-pipe Darcy friction constant (f_D = 64/Re).
# Justification: the canonical reference for a fully-developed laminar duct; any
# apparent f far above 64/Re is dominated by non-fully-developed / form effects.
LAMINAR_DARCY_CONST = 64.0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def property_model(case_label: str, source_id: str) -> str:
    text = f"{case_label} {source_id}".lower()
    if "jin" in text:
        return "jin"
    if "kirst" in text:
        return "kirst"
    if "val" in text:
        return "val"
    return "unknown"


def physical_case(case_label: str) -> str:
    """Collapse Jin/Kirst/val labels to the physical case (e.g. 'Salt 2')."""
    import re

    match = re.search(r"salt\s*(\d+)", case_label.lower())
    return f"Salt {match.group(1)}" if match else case_label


def power_law_fit(re_values: list[float], y_values: list[float]) -> dict[str, Any]:
    """Fit y = a * Re^b (i.e. log y = log a + b log Re). Report honesty metrics."""
    re_arr = np.array(re_values, dtype=float)
    y_arr = np.array(y_values, dtype=float)
    good = (re_arr > 0) & (y_arr > 0) & np.isfinite(re_arr) & np.isfinite(y_arr)
    re_arr, y_arr = re_arr[good], y_arr[good]
    n = int(re_arr.size)
    if n < 2:
        return {"status": "insufficient_points", "n_points": n}
    log_re = np.log(re_arr)
    log_y = np.log(y_arr)
    coeffs = np.polyfit(log_re, log_y, 1)
    b, log_a = float(coeffs[0]), float(coeffs[1])
    pred = log_a + b * log_re
    ss_res = float(np.sum((log_y - pred) ** 2))
    ss_tot = float(np.sum((log_y - np.mean(log_y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    n_params = 2
    dof = n - n_params
    # Honesty flag: with dof<=1 the "fit" interpolates the points, so R^2~1 is an
    # ARTIFACT of saturation, not evidence of a validated correlation.
    if dof <= 0:
        overfit = "interpolation_not_fit_dof<=0"
    elif dof == 1:
        overfit = "saturated_fit_dof=1_R2_uninformative"
    else:
        overfit = "ok"
    return {
        "status": "fit",
        "form": "y = a * Re^b  (log-linear)",
        "a": math.exp(log_a),
        "b": b,
        "log_a": log_a,
        "r2_logspace": r2,
        "overfit_flag": overfit,
        "n_points": n,
        "n_free_params": n_params,
        "dof": dof,
        "re_min": float(np.min(re_arr)),
        "re_max": float(np.max(re_arr)),
        "re_span_ratio": float(np.max(re_arr) / np.min(re_arr)),
    }


def re_domain_guard(re_query: float, fit: dict[str, Any]) -> str:
    if fit.get("status") != "fit":
        return "no_fit"
    if re_query < fit["re_min"]:
        return "extrapolation_below"
    if re_query > fit["re_max"]:
        return "extrapolation_above"
    return "in_domain"


def build_friction_view(rows: list[dict[str, str]]) -> dict[str, Any]:
    per_case: list[dict[str, Any]] = []
    for row in rows:
        re_eff = safe_float(row.get("re_effective"))
        f_app = safe_float(row.get("target_value"))
        if re_eff is None or f_app is None:
            continue
        f_lam = LAMINAR_DARCY_CONST / re_eff if re_eff > 0 else float("nan")
        per_case.append(
            {
                "source_id": row.get("source_id", ""),
                "case_label": row.get("case_label", ""),
                "physical_case": physical_case(row.get("case_label", "")),
                "property_model": property_model(row.get("case_label", ""), row.get("source_id", "")),
                "segment": row.get("category_name", ""),
                "re_effective": re_eff,
                "apparent_darcy_f": f_app,
                "laminar_ref_darcy_f_64_over_Re": f_lam,
                "excess_loss_factor_fapp_over_flam": f_app / f_lam if math.isfinite(f_lam) and f_lam > 0 else float("nan"),
            }
        )
    return {"per_case": per_case}


def property_axis_spread(per_case: list[dict[str, Any]], value_key: str) -> list[dict[str, Any]]:
    """For each (physical_case, segment), quantify the Jin-vs-Kirst spread.

    This isolates how much apparent Re/value variation is property-model driven
    (i.e. NOT an independent physical operating point).
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entry in per_case:
        key = (entry["physical_case"], entry["segment"])
        groups.setdefault(key, []).append(entry)
    out: list[dict[str, Any]] = []
    for (phys, seg), entries in sorted(groups.items()):
        models = {e["property_model"]: e for e in entries}
        if "jin" in models and "kirst" in models:
            re_j, re_k = models["jin"]["re_effective"], models["kirst"]["re_effective"]
            v_j, v_k = models["jin"][value_key], models["kirst"][value_key]
            re_mid = 0.5 * (re_j + re_k)
            v_mid = 0.5 * (v_j + v_k)
            out.append(
                {
                    "physical_case": phys,
                    "segment": seg,
                    "value_key": value_key,
                    "re_jin": re_j,
                    "re_kirst": re_k,
                    "re_property_spread_pct": 100.0 * abs(re_j - re_k) / re_mid if re_mid else float("nan"),
                    "value_jin": v_j,
                    "value_kirst": v_k,
                    "value_property_spread_pct": 100.0 * abs(v_j - v_k) / v_mid if v_mid else float("nan"),
                }
            )
    return out


def build_thermal_view(rows: list[dict[str, str]]) -> dict[str, Any]:
    per_case: list[dict[str, Any]] = []
    for row in rows:
        re_eff = safe_float(row.get("re_effective"))
        pr_eff = safe_float(row.get("pr_effective"))
        nu_eff = safe_float(row.get("nu_effective"))
        htc = safe_float(row.get("htc_effective_w_m2_k"))
        if re_eff is None or nu_eff is None:
            continue
        per_case.append(
            {
                "source_id": row.get("source_id", ""),
                "case_label": row.get("case_label", ""),
                "physical_case": physical_case(row.get("case_label", "")),
                "property_model": property_model(row.get("case_label", ""), row.get("source_id", "")),
                "branch": row.get("branch_name", ""),
                "segment": row.get("branch_name", ""),
                "re_effective": re_eff,
                "pr_effective": pr_eff,
                "nu_effective": nu_eff,
                "htc_effective_w_m2_k": htc,
            }
        )
    return {"per_case": per_case}


def assess_pr_relevance(per_case: list[dict[str, Any]]) -> dict[str, Any]:
    """Does Pr actually matter for Nu given the available spread?

    The model nominally consumes Nu(Re,Pr) but the legacy fit is Nu(Re) only. We
    (a) report the Pr spread, and (b) correlate the Re-only fit residuals with Pr.
    With laminar molten salt, Pr and Re are strongly anti-correlated (both move
    with viscosity), so Pr and Re are nearly collinear -> Pr cannot be separately
    identified from this data. We MEASURE and report that collinearity instead of
    asserting it.
    """
    re = np.array([e["re_effective"] for e in per_case if e.get("pr_effective")], dtype=float)
    pr = np.array([e["pr_effective"] for e in per_case if e.get("pr_effective")], dtype=float)
    nu = np.array([e["nu_effective"] for e in per_case if e.get("pr_effective")], dtype=float)
    if re.size < 3:
        return {"status": "insufficient_points"}
    log_re, log_pr, log_nu = np.log(re), np.log(pr), np.log(nu)
    # collinearity of log Re and log Pr
    re_pr_corr = float(np.corrcoef(log_re, log_pr)[0, 1])
    # Re-only fit residuals vs log Pr
    b, log_a = np.polyfit(log_re, log_nu, 1)
    resid = log_nu - (log_a + b * log_re)
    resid_pr_corr = float(np.corrcoef(resid, log_pr)[0, 1]) if np.std(resid) > 0 else float("nan")
    return {
        "status": "assessed",
        "pr_min": float(np.min(pr)),
        "pr_max": float(np.max(pr)),
        "pr_spread_ratio": float(np.max(pr) / np.min(pr)),
        "logRe_logPr_correlation": re_pr_corr,
        "collinearity_note": (
            "log Re and log Pr are nearly collinear (|corr|~%.2f); with laminar "
            "salt, mu drives both, so Pr cannot be identified as an independent "
            "Nu regressor from this data. Nu(Re) and Nu(Re,Pr) are not "
            "distinguishable here." % abs(re_pr_corr)
        ),
        "reOnly_residual_vs_logPr_correlation": resid_pr_corr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hydraulic-csv", default=str(DEFAULT_HYDRAULIC_CSV))
    parser.add_argument("--thermal-csv", default=str(DEFAULT_THERMAL_CSV))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    fric = build_friction_view(read_csv_rows(Path(args.hydraulic_csv)))
    therm = build_thermal_view(read_csv_rows(Path(args.thermal_csv)))

    # Property-axis separation
    fric_spread = property_axis_spread(fric["per_case"], "apparent_darcy_f")
    therm_spread = property_axis_spread(therm["per_case"], "nu_effective")

    # Fits: paper-grade (Jin only) vs all-salt (context). Per friction segment.
    def fit_friction(model_filter, segment) -> dict[str, Any]:
        sel = [e for e in fric["per_case"] if e["segment"] == segment and (model_filter is None or e["property_model"] == model_filter)]
        n_phys = len({e["physical_case"] for e in sel})
        fit = power_law_fit([e["re_effective"] for e in sel], [e["apparent_darcy_f"] for e in sel])
        fit["n_physical_cases"] = n_phys
        fit["segment"] = segment
        return fit

    segments = sorted({e["segment"] for e in fric["per_case"]})
    friction_fits = {
        "jin_only": {seg: fit_friction("jin", seg) for seg in segments},
        "all_salt": {seg: fit_friction(None, seg) for seg in segments},
    }

    def fit_nu(model_filter) -> dict[str, Any]:
        sel = [e for e in therm["per_case"] if (model_filter is None or e["property_model"] == model_filter)]
        n_phys = len({e["physical_case"] for e in sel})
        fit = power_law_fit([e["re_effective"] for e in sel], [e["nu_effective"] for e in sel])
        fit["n_physical_cases"] = n_phys
        return fit

    nu_fits = {"jin_only": fit_nu("jin"), "all_salt": fit_nu(None)}
    pr_relevance = assess_pr_relevance(therm["per_case"])

    payload = {
        "generated_at": iso_timestamp(),
        "scope_note": "Paper fits use Salt Jin only; Kirst/val are sensitivity context.",
        "laminar_reference": "Darcy f_lam = 64/Re (fully-developed laminar circular pipe).",
        "friction_per_case": fric["per_case"],
        "friction_property_axis_spread": fric_spread,
        "friction_fits": friction_fits,
        "thermal_per_case": therm["per_case"],
        "thermal_property_axis_spread": therm_spread,
        "nusselt_fits": nu_fits,
        "pr_relevance": pr_relevance,
    }
    json_dump(output_dir / "closure_representation.json", payload)
    csv_dump(
        output_dir / "friction_per_case.csv",
        list(fric["per_case"][0].keys()) if fric["per_case"] else [],
        fric["per_case"],
    )
    csv_dump(
        output_dir / "thermal_per_case.csv",
        list(therm["per_case"][0].keys()) if therm["per_case"] else [],
        therm["per_case"],
    )
    if fric_spread:
        csv_dump(output_dir / "friction_property_axis_spread.csv", list(fric_spread[0].keys()), fric_spread)

    # ---- console headline ----
    print(f"# Closure re-presentation  ({iso_timestamp()})")
    print("\n## Apparent friction vs fully-developed laminar reference (64/Re)")
    print(f"{'case':14s} {'seg':18s} {'Re':>7s} {'f_app':>8s} {'f_lam':>7s} {'excess x':>9s}")
    for e in fric["per_case"]:
        print(f"{e['case_label']:14s} {e['segment']:18s} {e['re_effective']:7.1f} {e['apparent_darcy_f']:8.2f} {e['laminar_ref_darcy_f_64_over_Re']:7.3f} {e['excess_loss_factor_fapp_over_flam']:9.1f}")
    print("\n## Property-model (Jin vs Kirst) share of apparent Re/f spread")
    for s in fric_spread:
        print(f"   {s['physical_case']:8s} {s['segment']:18s} Re spread={s['re_property_spread_pct']:5.1f}%  f spread={s['value_property_spread_pct']:5.1f}%  (SAME physical case)")
    print("\n## Friction fits (Jin-only, paper scope)")
    for seg, fit in friction_fits["jin_only"].items():
        if fit.get("status") == "fit":
            print(f"   {seg:18s} f=a*Re^b a={fit['a']:.3g} b={fit['b']:.3f} R^2={fit['r2_logspace']:.3f} "
                  f"N={fit['n_points']} (phys cases={fit['n_physical_cases']}, dof={fit['dof']}) Re[{fit['re_min']:.0f},{fit['re_max']:.0f}] [{fit['overfit_flag']}]")
        else:
            print(f"   {seg:18s} {fit.get('status')} (N={fit.get('n_points')})")
    print("\n## Nusselt fit (Jin-only) + Pr identifiability")
    nf = nu_fits["jin_only"]
    if nf.get("status") == "fit":
        print(f"   Nu=a*Re^b a={nf['a']:.3g} b={nf['b']:.3f} R^2={nf['r2_logspace']:.3f} N={nf['n_points']} phys={nf['n_physical_cases']} dof={nf['dof']} Re[{nf['re_min']:.0f},{nf['re_max']:.0f}] [{nf['overfit_flag']}]")
    if pr_relevance.get("status") == "assessed":
        print(f"   Pr spread {pr_relevance['pr_min']:.1f}-{pr_relevance['pr_max']:.1f}; log Re/log Pr corr={pr_relevance['logRe_logPr_correlation']:+.2f}")
        print(f"   -> {pr_relevance['collinearity_note']}")
    print(f"\nWrote {relative_to_workspace(output_dir / 'closure_representation.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
