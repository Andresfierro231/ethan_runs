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

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_pressure_feature_support_note"
DEFAULT_PRESSURE_PACKAGE_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
DEFAULT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reuse the existing pressure/HTC/boundary-layer package to close the remaining "
            "feature-loss and Water supporting-evidence interpretation gaps without rebuilding "
            "the additive analysis stack."
        )
    )
    parser.add_argument("--pressure-package-dir", default=str(DEFAULT_PRESSURE_PACKAGE_DIR))
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


def build_feature_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["family"]), str(row["feature_kind"]))].append(row)

    output: list[dict[str, Any]] = []
    for (family, feature_kind), group_rows in sorted(grouped.items()):
        keff_values = [float(row["mean_keff_reference"]) for row in group_rows]
        warning_fractions = [float(row["warning_fraction"]) for row in group_rows]
        residual_values = [abs(float(row["mean_feature_residual_dp_pa"])) for row in group_rows]
        output.append(
            {
                "family": family,
                "feature_kind": feature_kind,
                "row_count": len(group_rows),
                "mean_keff_reference": f"{statistics.fmean(keff_values):.12f}",
                "keff_relative_cv": f"{rel_cv(keff_values):.12f}",
                "warning_fraction_mean": f"{statistics.fmean(warning_fractions):.12f}",
                "warning_fraction_max": f"{max(warning_fractions):.12f}",
                "mean_abs_feature_residual_dp_pa": f"{statistics.fmean(residual_values):.12f}",
                "readiness_status": "not_ready",
                "explanation": (
                    "K_eff stays not ready because the June 17 package still uses the preserved p_rgh residual closure without a dedicated feature-path density integral, "
                    "and the warning fractions remain too high for defended dependency construction."
                ),
            }
        )
    return output


def build_water_test_section_metrics(
    htc_rows: list[dict[str, str]],
    closure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    selected = [row for row in htc_rows if row["family"] == "water" and row["span_name"] == "test_section_span"]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        grouped[str(row["source_id"])].append(row)

    closure_lookup = {
        str(row["family"]): row
        for row in closure_rows
        if row["family"] == "water_all" and row["branch"] == "test_section_span" and row["variable"] == "effective_ua"
    }
    closure_row = closure_lookup["water_all"]

    output: list[dict[str, Any]] = []
    for source_id, rows in sorted(grouped.items()):
        h_values = [float(row["h_area_ratio_signed_w_m2_k"]) for row in rows]
        nu_values = [float(row["nu_area_ratio_signed"]) for row in rows]
        delta_values = [abs(float(row["delta_t_wall_minus_bulk_integral_k_m2"])) for row in rows]
        output.append(
            {
                "source_id": source_id,
                "time_count": len(rows),
                "mean_h_area_ratio_signed_w_m2_k": f"{statistics.fmean(h_values):.12f}",
                "h_area_ratio_signed_relative_cv": f"{rel_cv(h_values):.12f}",
                "mean_nu_area_ratio_signed": f"{statistics.fmean(nu_values):.12f}",
                "nu_area_ratio_signed_relative_cv": f"{rel_cv(nu_values):.12f}",
                "min_abs_delta_t_wall_minus_bulk_integral_k_m2": f"{min(delta_values):.12f}",
                "max_abs_delta_t_wall_minus_bulk_integral_k_m2": f"{max(delta_values):.12f}",
                "recommended_use": "supporting_only",
                "closure_gate": closure_row["interpretability_status"],
            }
        )
    return output


def build_pressure_readiness_rows(case_rows: list[dict[str, str]], section_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    straight_rows = [row for row in section_rows if row["straight_section_flag"] == "yes"]
    straight_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in straight_rows:
        straight_by_family[str(row["family"])].append(row)

    output: list[dict[str, Any]] = []
    for family, rows in sorted(straight_by_family.items()):
        endpoint_residuals = [abs(float(row["mean_pressure_closure_residual_vs_prgh_endpoint_pa"])) for row in rows]
        direct_darcy = [abs(float(row["mean_direct_prgh_darcy_existing"])) for row in rows]
        case_subset = [row for row in case_rows if row["family"] == family]
        loop_prgh = [abs(float(row["loop_total_pressure_loss_prgh_pa"])) for row in case_subset]
        hydro_proxy = [abs(float(row["max_hydro_head_proxy_range_pa"])) for row in case_subset]
        output.append(
            {
                "family": family,
                "mean_abs_pressure_closure_residual_vs_endpoint_pa": f"{statistics.fmean(endpoint_residuals):.12f}",
                "mean_abs_direct_prgh_darcy_existing": f"{statistics.fmean(direct_darcy):.12f}",
                "mean_abs_loop_total_pressure_loss_prgh_pa": f"{statistics.fmean(loop_prgh):.12f}",
                "mean_abs_max_hydro_head_proxy_range_pa": f"{statistics.fmean(hydro_proxy):.12f}",
                "readiness_status": "diagnostic_only",
                "recommended_use": "narrative_context_only",
                "explanation": (
                    "Hydro-corrected straight-section pressure metrics help explain why p and p_rgh diverge, but the remaining closure residuals are still too large for defended direct dependency fitting."
                ),
            }
        )
    return output


def build_support_conclusions(
    feature_rows: list[dict[str, Any]],
    water_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "conclusion_id": "PF01",
            "topic": "feature_keff",
            "status": "not_ready",
            "scope": "all_families",
            "recommended_use": "do_not_fit",
            "explanation": (
                "Feature K_eff remains not ready for defended dependency construction. The June 17 package still depends on the stored p_rgh residual closure without a dedicated feature-path density integral, "
                "and the feature warning fractions remain too high for both Salt and Water."
            ),
        },
        {
            "conclusion_id": "PF02",
            "topic": "water_test_section_span",
            "status": "supporting_only",
            "scope": "water",
            "recommended_use": "internal_comparison_only",
            "explanation": (
                "Water test_section_span is the strongest Water thermal branch, but it remains supporting-only because the closure package still flags it as contextual_only and the resolved driving-temperature support remains below the defended Salt threshold."
            ),
        },
        {
            "conclusion_id": "PF03",
            "topic": "hydro_corrected_pressure",
            "status": "diagnostic_only",
            "scope": "all_families",
            "recommended_use": "methods_context_only",
            "explanation": (
                "Hydro-corrected straight-section pressure rows are still valuable for methods interpretation because they quantify how strongly p - p_rgh dominates the raw wall-pressure range, but the remaining straight-section residuals prevent them from becoming closure-quality direct observables."
            ),
        },
    ]


def write_readme(
    output_dir: Path,
    pressure_package_dir: Path,
    closure_dir: Path,
    feature_rows: list[dict[str, Any]],
    water_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, Any]],
) -> None:
    salt_feature = next(row for row in feature_rows if row["family"] == "salt" and row["feature_kind"] == "corner")
    water_feature = next(row for row in feature_rows if row["family"] == "water" and row["feature_kind"] == "corner")
    water_test = water_rows[0]
    water_test_mean = statistics.fmean(float(row["mean_h_area_ratio_signed_w_m2_k"]) for row in water_rows)
    pressure_water = next(row for row in pressure_rows if row["family"] == "water")
    pressure_salt = next(row for row in pressure_rows if row["family"] == "salt")

    readme = f"""# Pressure / Feature / Water Support Note

Generated: `{iso_timestamp()}`

## Purpose

Reuse the existing June 17 pressure / HTC / boundary-layer package to close three remaining interpretation gaps without rebuilding any additive analysis package:

1. confirm whether feature `K_eff` is ready for any family-specific use;
2. tighten the Water `test_section_span` supporting-only interpretation;
3. describe how far the hydro-corrected straight-section pressure rows can be used without changing readiness status.

## Inputs

- `{relative_path(pressure_package_dir / 'README.md')}`
- `{relative_path(pressure_package_dir / 'MATH_COMPANION.md')}`
- `{relative_path(closure_dir / 'README.md')}`
- `{relative_path(closure_dir / 'branch_thermal_interpretation.csv')}`

## Decisions

- Feature `K_eff`: **not ready**
- Water `test_section_span`: **supporting-only**
- Hydro-corrected straight-section pressure rows: **diagnostic-only**

## Why feature `K_eff` stays blocked

- Salt corner `K_eff` still shows mean warning fraction `{float(salt_feature['warning_fraction_mean']):.3f}` with relative variation `{float(salt_feature['keff_relative_cv']):.3f}`.
- Water corner `K_eff` still shows mean warning fraction `{float(water_feature['warning_fraction_mean']):.3f}`.
- The June 17 package explicitly states that the raw package does not retain a dedicated feature-path density integral, so the residual `p_rgh` closure should not be over-read as a defended feature-loss dependency.

## Why Water `test_section_span` is stronger than the rest of Water but still not headline-safe

- Mean signed effective area-ratio HTC across the retained windows is `{water_test_mean:.3f} W/m^2/K`.
- The per-case retained-window series remains stable enough for internal comparison, but the closure package still classifies Water `test_section_span` as `contextual_only` rather than `headline_eligible`.
- The current defended reason remains the resolved driving-temperature floor, not random plotting noise.

## Pressure / hydro narrative

- Mean straight-section endpoint closure residual by family:
  - Salt: `{float(pressure_salt['mean_abs_pressure_closure_residual_vs_endpoint_pa']):.3f} Pa`
  - Water: `{float(pressure_water['mean_abs_pressure_closure_residual_vs_endpoint_pa']):.3f} Pa`
- Mean absolute `p_rgh` loop loss by family stays much smaller than the hydro-head proxy range, especially in Water.
- That means the hydro-corrected pressure rows are useful for methods context and sign interpretation, but not yet strong enough to promote as defended direct fitting observables.

## Reproduction

```bash
python tools/analyze/build_ethan_pressure_feature_support_note.py \\
  --output-dir {relative_path(output_dir)}
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def write_water_support_note(output_dir: Path, water_rows: list[dict[str, Any]]) -> None:
    note = """# Water Test Section Supporting Note

Water `test_section_span` remains the only Water thermal branch that is consistently strong enough to keep in the conversation. That still does not make it headline-safe.

The defended use is narrower:

- use it as the Water-family branch for internal comparison and trend description;
- do not use it as a cross-family fitting anchor;
- do not use it to override the broader Water thermal support collapse on the left-side branches.

The important distinction is that Water `test_section_span` is support-limited, not random. Its signed area-ratio HTC and signed Nusselt levels are reasonably stable across retained windows, but the closure package still blocks headline promotion because the resolved driving-temperature support stays below the defended Salt threshold.
"""
    (output_dir / "water_test_section_support_note.md").write_text(note, encoding="utf-8")


def write_pressure_readiness_note(output_dir: Path) -> None:
    note = """# Pressure Support Readiness

## Feature K_eff

Keep feature `K_eff` at `not_ready`. The current residual closure is still based on stored `p_rgh` feature loss relative to adjacent major-span reference pressure drops. Without a dedicated feature-path density integral, even a clean-looking case trend is not enough to defend direct model fitting.

## Hydro-corrected straight-section pressure rows

Keep the hydro-corrected straight-section rows at `diagnostic_only`. They are useful because they quantify how strongly `p - p_rgh` dominates the raw wall-pressure range, especially in Water, but the remaining straight-section closure residuals are too large to claim closure-quality direct observables.
"""
    (output_dir / "pressure_support_readiness.md").write_text(note, encoding="utf-8")


def main() -> None:
    args = parse_args()
    pressure_package_dir = Path(args.pressure_package_dir).resolve()
    closure_dir = Path(args.closure_dir).resolve()
    output_dir = ensure_dir(Path(args.output_dir).resolve())

    feature_path = pressure_package_dir / "feature_keff_by_case.csv"
    pressure_case_path = pressure_package_dir / "pressure_closure_by_case.csv"
    pressure_section_path = pressure_package_dir / "pressure_closure_by_section.csv"
    water_htc_path = pressure_package_dir / "fluid_side_htc_nu_section_summary.csv"
    closure_path = closure_dir / "branch_thermal_interpretation.csv"
    for path in [feature_path, pressure_case_path, pressure_section_path, water_htc_path, closure_path]:
        require_exists(path)

    feature_rows = build_feature_summary(load_csv_rows(feature_path))
    water_rows = build_water_test_section_metrics(load_csv_rows(water_htc_path), load_csv_rows(closure_path))
    pressure_rows = build_pressure_readiness_rows(load_csv_rows(pressure_case_path), load_csv_rows(pressure_section_path))
    conclusions = build_support_conclusions(feature_rows, water_rows, pressure_rows)

    csv_dump(output_dir / "feature_keff_family_summary.csv", list(feature_rows[0].keys()), feature_rows)
    csv_dump(output_dir / "water_test_section_support_metrics.csv", list(water_rows[0].keys()), water_rows)
    csv_dump(output_dir / "pressure_support_readiness.csv", list(pressure_rows[0].keys()), pressure_rows)
    csv_dump(output_dir / "feature_support_conclusions.csv", list(conclusions[0].keys()), conclusions)

    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-072",
        "builder_script": "tools/analyze/build_ethan_pressure_feature_support_note.py",
        "pressure_package_dir": relative_path(pressure_package_dir),
        "closure_dir": relative_path(closure_dir),
        "feature_keff_status": "not_ready",
        "water_test_section_status": "supporting_only",
        "hydro_corrected_pressure_status": "diagnostic_only",
        "artifacts": [
            "README.md",
            "summary.json",
            "feature_keff_family_summary.csv",
            "water_test_section_support_metrics.csv",
            "pressure_support_readiness.csv",
            "feature_support_conclusions.csv",
            "water_test_section_support_note.md",
            "pressure_support_readiness.md",
        ],
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, pressure_package_dir, closure_dir, feature_rows, water_rows, pressure_rows)
    write_water_support_note(output_dir, water_rows)
    write_pressure_readiness_note(output_dir)


if __name__ == "__main__":
    main()
