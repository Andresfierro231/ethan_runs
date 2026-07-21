#!/usr/bin/env python3
"""Build a model-form bakeoff package from the canonical observation table.

This is a lightweight starter bakeoff. It does not rerun the external Fluid
solver; it consumes admitted observation rows plus existing July 7/8 model and
ledger products, then scores mdot, pressure distribution, and thermal mismatch
as separate axes.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_model_form_bakeoff_thermal_refresh"

OBS = ROOT / "work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv"
FRICTION = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/mdot_comparison.csv"
F5 = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv"
PRESSURE = ROOT / "work_products/2026-07/2026-07-07/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv"

SPAN_TO_DP_COL = {
    "lower_leg": "dp_heater_pa",
    "upper_leg": "dp_cooler_pa",
    "right_leg": "dp_downcomer_pa",
    "upcomer": "dp_upcomer_pa",
}

FORM_COMPLEXITY = {
    "F1": (0, "fully_developed_baseline"),
    "F3_hagenbach": (0, "developing_flow_correction"),
    "F3_shah_apparent": (0, "literature_developing_flow_apparent"),
    "F4_leg_class": (4, "leg_class_multiplier_candidate"),
    "F5_ri_corrected": (1, "ri_multiplier_failed_screen_currently_equals_F3"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fnum(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "na"}:
        return default
    return float(text)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def case_id_from_source(source_id: str) -> str:
    if "salt_test_2" in source_id:
        return "salt_2"
    if "salt_test_3" in source_id:
        return "salt_3"
    if "salt_test_4" in source_id:
        return "salt_4"
    if "salt_test_1" in source_id:
        return "salt_1"
    return source_id


def observation_use_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str, str]] = Counter()
    for row in rows:
        counts[
            (
                row["observable_family"],
                row["fit_use_status"],
                row["validation_use_status"],
                row["mesh_status"],
            )
        ] += 1
    return [
        {
            "observable_family": family,
            "fit_use_status": fit,
            "validation_use_status": validation,
            "mesh_status": mesh,
            "row_count": count,
        }
        for (family, fit, validation, mesh), count in sorted(counts.items())
    ]


def observation_quality_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in rows:
        counts[
            (
                row["observable_family"],
                row.get("recirculation_flag", "no"),
                row.get("radiation_present", "no"),
                row.get("physical_interface_bracket_status", "not_applicable"),
                row.get("fit_use_status", ""),
            )
        ] += 1
    return [
        {
            "observable_family": family,
            "recirculation_flag": recirc,
            "radiation_present": radiation,
            "physical_interface_bracket_status": bracket,
            "fit_use_status": fit_status,
            "row_count": count,
        }
        for (family, recirc, radiation, bracket, fit_status), count in sorted(counts.items())
    ]


def pressure_targets(rows: list[dict[str, str]]) -> dict[tuple[str, str], float]:
    targets: dict[tuple[str, str], float] = {}
    for row in rows:
        span = row.get("span", "")
        if span not in SPAN_TO_DP_COL:
            continue
        case = row.get("case_id") or case_id_from_source(row.get("source_id", ""))
        mechanical = (
            abs(fnum(row.get("distributed_friction_pa")))
            + abs(fnum(row.get("development_loss_pa")))
            + abs(fnum(row.get("minor_loss_pa")))
        )
        targets[(case, span)] = mechanical
    return targets


def thermal_metrics_by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    residual_w: dict[str, list[float]] = defaultdict(list)
    residual_fraction: dict[str, list[float]] = defaultdict(list)
    thermal_row_count: Counter[str] = Counter()
    sampled_interface_count: Counter[str] = Counter()
    residual_row_count: Counter[str] = Counter()
    recirc_row_count: Counter[str] = Counter()
    bracket_counts: dict[str, Counter[str]] = defaultdict(Counter)
    radiation_present_count: Counter[str] = Counter()

    for row in rows:
        if row.get("observable_family") != "thermal":
            continue
        case = row["case_id"]
        thermal_row_count[case] += 1
        bracket = row.get("physical_interface_bracket_status", "not_applicable")
        bracket_counts[case][bracket] += 1
        if row.get("recirculation_flag") == "yes":
            recirc_row_count[case] += 1
        if row.get("radiation_present") == "yes":
            radiation_present_count[case] += 1
        if row.get("source_path", "").endswith("combined_openfoam_interface_samples.csv"):
            sampled_interface_count[case] += 1
        if row.get("source_path", "").endswith("patchwise_heat_ledger_enthalpy_interfaces.csv"):
            residual_row_count[case] += 1
        if row.get("quantity") == "wallHeatFlux_vs_enthalpy_residual_W":
            residual_w[case].append(abs(fnum(row["value"])))
        if row.get("quantity") == "residual_fraction":
            residual_fraction[case].append(abs(fnum(row["value"])))

    metrics: dict[str, dict[str, Any]] = {}
    for case in sorted(thermal_row_count):
        residuals = residual_w.get(case, [])
        fractions = residual_fraction.get(case, [])
        metrics[case] = {
            "thermal_observation_rows": thermal_row_count[case],
            "openfoam_interface_observation_rows": sampled_interface_count[case],
            "physical_interface_residual_observation_rows": residual_row_count[case],
            "mean_abs_thermal_residual_W": sum(residuals) / len(residuals) if residuals else "",
            "max_abs_thermal_residual_fraction": max(fractions) if fractions else "",
            "recirculation_contaminated_thermal_rows": recirc_row_count[case],
            "radiation_present_rows": radiation_present_count[case],
            "thermal_bracket_status_counts": ";".join(
                f"{status}={count}" for status, count in sorted(bracket_counts[case].items())
            ),
        }
    return metrics


def model_rows() -> list[dict[str, str]]:
    rows = read_csv(FRICTION)
    rows.extend(row for row in read_csv(F5) if row["friction_form"] == "F5_ri_corrected")
    return rows


def build_case_scores() -> list[dict[str, Any]]:
    obs_rows = read_csv(OBS)
    pressure = pressure_targets(read_csv(PRESSURE))
    thermal = thermal_metrics_by_case(obs_rows)
    f3_pressure_rows = {
        row["salt_label"]: row
        for row in read_csv(FRICTION)
        if row["friction_form"] == "F3_shah_apparent"
    }
    out: list[dict[str, Any]] = []
    for row in model_rows():
        case = row["salt_label"]
        form = row["friction_form"]
        pressure_source = f3_pressure_rows[case] if form == "F5_ri_corrected" else row
        pressure_errors = []
        for span, dp_col in SPAN_TO_DP_COL.items():
            target = pressure.get((case, span))
            if target is None or target <= 0:
                continue
            predicted = abs(fnum(pressure_source.get(dp_col)))
            pressure_errors.append(abs(predicted - target) / target * 100.0)
        out.append(
            {
                "model_form": form,
                "case_id": case,
                "mdot_error_pct": fnum(row["mdot_err_pct"]),
                "abs_mdot_error_pct": abs(fnum(row["mdot_err_pct"])),
                "pressure_distribution_mape_pct": sum(pressure_errors) / len(pressure_errors) if pressure_errors else "",
                "thermal_state_mismatch_W": thermal.get(case, {}).get("mean_abs_thermal_residual_W", ""),
                "max_abs_thermal_residual_fraction": thermal.get(case, {}).get("max_abs_thermal_residual_fraction", ""),
                "thermal_observation_rows": thermal.get(case, {}).get("thermal_observation_rows", ""),
                "openfoam_interface_observation_rows": thermal.get(case, {}).get("openfoam_interface_observation_rows", ""),
                "physical_interface_residual_observation_rows": thermal.get(case, {}).get("physical_interface_residual_observation_rows", ""),
                "recirculation_contaminated_thermal_rows": thermal.get(case, {}).get("recirculation_contaminated_thermal_rows", ""),
                "radiation_present_rows": thermal.get(case, {}).get("radiation_present_rows", ""),
                "thermal_bracket_status_counts": thermal.get(case, {}).get("thermal_bracket_status_counts", ""),
                "thermal_score_status": "canonical_validation_axis_not_model_specific_no_fit_promotion",
                "source_rows": f"{rel(FRICTION)};{rel(F5)};{rel(PRESSURE)};{rel(OBS)}",
            }
        )
    out.sort(key=lambda item: (item["model_form"], item["case_id"]))
    return out


def summarize_models(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["model_form"]].append(row)
    out: list[dict[str, Any]] = []
    for form, rows in sorted(grouped.items()):
        complexity, family = FORM_COMPLEXITY.get(form, ("", "unknown"))
        mdot = [fnum(row["abs_mdot_error_pct"]) for row in rows]
        pressure = [fnum(row["pressure_distribution_mape_pct"]) for row in rows if row["pressure_distribution_mape_pct"] != ""]
        thermal = [fnum(row["thermal_state_mismatch_W"]) for row in rows if row["thermal_state_mismatch_W"] != ""]
        overfit = "low_fixed_form" if complexity == 0 else "high_three_case_dataset" if complexity and complexity >= 3 else "screen_only"
        out.append(
            {
                "model_form": form,
                "form_family": family,
                "fit_parameter_count": complexity,
                "case_count": len(rows),
                "mean_abs_mdot_error_pct": sum(mdot) / len(mdot),
                "max_abs_mdot_error_pct": max(mdot),
                "mean_pressure_distribution_mape_pct": sum(pressure) / len(pressure) if pressure else "",
                "mean_thermal_state_mismatch_W": sum(thermal) / len(thermal) if thermal else "",
                "thermal_score_status": "same_cfd_validation_axis_for_all_current_forms_from_july9_canonical_table",
                "fit_validation_split": "fit rows from closure_observations; mdot/thermal scored as validation diagnostics",
                "complexity_overfit_warning": overfit,
            }
        )
    out.sort(key=lambda row: (fnum(row["mean_abs_mdot_error_pct"]), row["model_form"]))
    return out


def write_readme(summary_rows: list[dict[str, Any]], case_rows: list[dict[str, Any]], obs_rows: list[dict[str, str]]) -> None:
    best = summary_rows[0]
    recirc_rows = sum(1 for row in obs_rows if row.get("recirculation_flag") == "yes")
    radiation_rows = sum(1 for row in obs_rows if row.get("radiation_present") == "yes")
    text = f"""# Model-Form Bakeoff From Observations

Generated: `{datetime.now().isoformat(timespec='seconds')}`

## Scope

Refresh bakeoff for `AGENT-247`. This package consumes the canonical July 9
observation table and existing 1D model-form outputs. It does not rerun or edit
the external Fluid model.

## Observed Facts

- Observation rows consumed: `{len(obs_rows)}` from `{rel(OBS)}`.
- Model/case score rows: `{len(case_rows)}`.
- Best current mdot form: `{best['model_form']}` with mean absolute mdot error
  `{float(best['mean_abs_mdot_error_pct']):.3f}%`.
- Recirculation-flagged observation rows consumed: `{recirc_rows}`; validator
  policy keeps these out of fit targets.
- Radiation-present observation rows consumed: `{radiation_rows}`; current
  table carries explicit no-`qr` semantics.
- Thermal residuals and sampled interface rows are scored separately from mdot
  and pressure; they are not used to fit model coefficients.

## Inferred Interpretation

The current admitted Salt 2/3/4 dataset still favors `F3_shah_apparent` / the
currently-degenerate `F5_ri_corrected` on mdot. `F4_leg_class` over-stiffens the
loop in the existing run. Pressure-distribution and thermal-residual axes expose
why mdot alone is not a sufficient closure score.

## Blockers

- This is a bakeoff refresh from existing outputs, not a fresh Fluid rerun.
- Thermal scores are model-form-independent until each model emits comparable
  per-segment heat predictions.
- All rows remain coarse mesh without GCI.
- Corrected Salt perturbations remain work in progress and are excluded.

## Recommended Next Action

Rerun the external Fluid model only after deciding which candidate forms should
emit per-segment pressure and heat predictions in a common schema. Keep pressure
distribution, mdot, and thermal-state mismatch as separate objective columns.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    obs = read_csv(OBS)
    case_scores = build_case_scores()
    summary_rows = summarize_models(case_scores)
    obs_summary = observation_use_summary(obs)
    quality_summary = observation_quality_summary(obs)
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUT / "model_form_case_scores.csv",
        case_scores,
        [
            "model_form",
            "case_id",
            "mdot_error_pct",
            "abs_mdot_error_pct",
            "pressure_distribution_mape_pct",
            "thermal_state_mismatch_W",
            "max_abs_thermal_residual_fraction",
            "thermal_observation_rows",
            "openfoam_interface_observation_rows",
            "physical_interface_residual_observation_rows",
            "recirculation_contaminated_thermal_rows",
            "radiation_present_rows",
            "thermal_bracket_status_counts",
            "thermal_score_status",
            "source_rows",
        ],
    )
    write_csv(
        OUT / "model_form_summary.csv",
        summary_rows,
        [
            "model_form",
            "form_family",
            "fit_parameter_count",
            "case_count",
            "mean_abs_mdot_error_pct",
            "max_abs_mdot_error_pct",
            "mean_pressure_distribution_mape_pct",
            "mean_thermal_state_mismatch_W",
            "thermal_score_status",
            "fit_validation_split",
            "complexity_overfit_warning",
        ],
    )
    write_csv(
        OUT / "observation_use_summary.csv",
        obs_summary,
        ["observable_family", "fit_use_status", "validation_use_status", "mesh_status", "row_count"],
    )
    write_csv(
        OUT / "observation_quality_summary.csv",
        quality_summary,
        [
            "observable_family",
            "recirculation_flag",
            "radiation_present",
            "physical_interface_bracket_status",
            "fit_use_status",
            "row_count",
        ],
    )
    write_readme(summary_rows, case_scores, obs)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "AGENT-247",
        "observation_rows": len(obs),
        "case_score_rows": len(case_scores),
        "model_forms": [row["model_form"] for row in summary_rows],
        "best_mdot_model_form": summary_rows[0]["model_form"],
        "recirculation_flagged_observation_rows": sum(1 for row in obs if row.get("recirculation_flag") == "yes"),
        "radiation_present_observation_rows": sum(1 for row in obs if row.get("radiation_present") == "yes"),
        "inputs": [rel(path) for path in [OBS, FRICTION, F5, PRESSURE]],
        "outputs": [
            "model_form_summary.csv",
            "model_form_case_scores.csv",
            "observation_use_summary.csv",
            "observation_quality_summary.csv",
            "README.md",
            "summary.json",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    summary = build()
    print(json.dumps({"output_dir": rel(OUT), "model_forms": summary["model_forms"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
