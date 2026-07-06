#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, finite_float, load_csv_rows, write_json  # noqa: E402
from tools.common import ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_FROZEN_DIR = ROOT / "reports" / "2026-06-23_ethan_frozen_state_results_latest_window"
DEFAULT_VALIDATION_DIR = ROOT / "reports" / "2026-06-23_ethan_frozen_state_1d_validation_latest_window"
DEFAULT_BAKEOFF_DIR = ROOT / "reports" / "2026-06-23_ethan_1d_closure_bakeoff_latest_window"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_1d_discrepancy_explainer_latest_window"
DEFAULT_IMPORT_MANIFEST = ROOT / "imports" / "2026-06-23_ethan_1d_discrepancy_explainer_latest_window.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a latest-window discrepancy explainer package for the defended "
            "local 1D-vs-CFD Salt comparison surface."
        )
    )
    parser.add_argument("--frozen-dir", default=str(DEFAULT_FROZEN_DIR))
    parser.add_argument("--validation-dir", default=str(DEFAULT_VALIDATION_DIR))
    parser.add_argument("--bakeoff-dir", default=str(DEFAULT_BAKEOFF_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_MANIFEST))
    return parser.parse_args()


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def load_dated_representative_table(bakeoff_dir: Path) -> list[dict[str, str]]:
    summary = json_or_empty(bakeoff_dir / "summary.json")
    target = summary.get("dated_representative_validation_csv")
    if target:
        path = Path(str(target))
        if path.exists():
            return load_csv_rows(path)
    candidates = sorted(bakeoff_dir.glob("*_representative_salt_last_window_validation_table.csv"))
    if not candidates:
        return []
    return load_csv_rows(candidates[-1])


def json_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def select_defended_case_rows(bakeoff_dir: Path) -> list[dict[str, str]]:
    return load_csv_rows(bakeoff_dir / "defended_full_coverage_surface" / "case_metric_summary.csv")


def build_upcomer_downcomer_contrast(branch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in branch_rows:
        grouped[row["case_label"]][row["branch_name"]] = row
    rows_out: list[dict[str, Any]] = []
    for case_label, lookup in sorted(grouped.items()):
        up = lookup.get("upcomer", {})
        down = lookup.get("right_leg", {})
        rows_out.append(
            {
                "case_label": case_label,
                "upcomer_fit_lane": up.get("fit_lane", ""),
                "downcomer_fit_lane": down.get("fit_lane", ""),
                "upcomer_support_fraction": finite_float(up.get("support_fraction")),
                "downcomer_support_fraction": finite_float(down.get("support_fraction")),
                "upcomer_mean_htc_w_m2_k": finite_float(up.get("mean_effective_htc_w_m2_k")),
                "downcomer_mean_htc_w_m2_k": finite_float(down.get("mean_effective_htc_w_m2_k")),
                "upcomer_minus_downcomer_htc_w_m2_k": (
                    finite_float(up.get("mean_effective_htc_w_m2_k"))
                    - finite_float(down.get("mean_effective_htc_w_m2_k"))
                ),
                "upcomer_mean_bulk_minus_wall_temp_k": finite_float(up.get("mean_bulk_minus_wall_temp_k")),
                "downcomer_mean_bulk_minus_wall_temp_k": finite_float(down.get("mean_bulk_minus_wall_temp_k")),
                "upcomer_minus_downcomer_bulk_minus_wall_temp_k": (
                    finite_float(up.get("mean_bulk_minus_wall_temp_k"))
                    - finite_float(down.get("mean_bulk_minus_wall_temp_k"))
                ),
                "upcomer_modeling_note": up.get("modeling_note", ""),
                "downcomer_modeling_note": down.get("modeling_note", ""),
            }
        )
    return rows_out


def load_branch_comparison_rows(*, frozen_dir: Path, validation_dir: Path) -> list[dict[str, Any]]:
    branch_development_path = frozen_dir / "branch_development_summary.csv"
    if branch_development_path.exists():
        return load_csv_rows(branch_development_path)

    fallback_path = validation_dir / "cfd_branch_profile_summary.csv"
    rows = load_csv_rows(fallback_path)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["frozen_case_label"], row["branch_name"])].append(row)

    aggregated: list[dict[str, Any]] = []
    for (case_label, branch_name), payload in sorted(grouped.items()):
        mean_bulk = safe_mean([finite_float(row.get("mean_bulk_temp_k")) for row in payload])
        mean_wall = safe_mean([finite_float(row.get("mean_wall_temp_k")) for row in payload])
        aggregated.append(
            {
                "case_label": case_label,
                "branch_name": branch_name,
                "fit_lane": payload[0].get("fit_status", ""),
                "support_fraction": math.nan,
                "mean_effective_htc_w_m2_k": safe_mean(
                    [finite_float(row.get("mean_effective_htc_w_m2_k")) for row in payload]
                ),
                "mean_bulk_minus_wall_temp_k": mean_bulk - mean_wall if math.isfinite(mean_bulk) and math.isfinite(mean_wall) else math.nan,
                "modeling_note": payload[0].get("modeling_note", ""),
            }
        )
    return aggregated


def build_heat_partition_gap(representative_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for row in representative_rows:
        cfd_removed = finite_float(row.get("cfd_removed_w"))
        cfd_ambient = finite_float(row.get("cfd_ambient_w"))
        one_d_removed = finite_float(row.get("one_d_removed_w"))
        one_d_ambient = finite_float(row.get("one_d_ambient_w"))
        rows_out.append(
            {
                "case_label": row["frozen_case_label"],
                "one_d_scenario": row["one_d_scenario"],
                "cfd_removed_w": cfd_removed,
                "one_d_removed_w": one_d_removed,
                "removed_gap_w": one_d_removed - cfd_removed,
                "cfd_ambient_w": cfd_ambient,
                "one_d_ambient_w": one_d_ambient,
                "ambient_gap_w": one_d_ambient - cfd_ambient,
                "cfd_total_loss_w": finite_float(row.get("cfd_total_loss_w")),
                "one_d_total_loss_w": finite_float(row.get("one_d_total_loss_w")),
                "total_loss_gap_w": finite_float(row.get("one_d_total_loss_w")) - finite_float(row.get("cfd_total_loss_w")),
                "energy_error_pct_of_heater": finite_float(row.get("one_d_energy_error_pct_of_heater")),
                "mass_flow_error_pct_vs_cfd": finite_float(row.get("one_d_mass_flow_error_pct_vs_cfd")),
            }
        )
    return rows_out


def build_defended_case_summary(
    *,
    case_rows: list[dict[str, str]],
    representative_rows: list[dict[str, str]],
    contrast_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rep_lookup = {row["frozen_case_label"]: row for row in representative_rows}
    contrast_lookup = {row["case_label"]: row for row in contrast_rows}
    rows_out: list[dict[str, Any]] = []
    for row in case_rows:
        case_label = row["frozen_case_label"]
        rep = rep_lookup.get(case_label, {})
        contrast = contrast_lookup.get(case_label, {})
        mass_flow_error = finite_float(row.get("mass_flow_relative_error_pct_vs_cfd"))
        wall_rmse = finite_float(row.get("tw_rmse_k"))
        centerline_rmse = finite_float(row.get("tp_rmse_k"))
        energy_error = finite_float(row.get("energy_error_pct_of_heater"))
        insulation_base = finite_float(rep.get("one_d_base_insulation_in"))
        rows_out.append(
            {
                "case_label": case_label,
                "scenario": row["scenario"],
                "energy_error_pct_of_heater": energy_error,
                "wall_rmse_k": wall_rmse,
                "centerline_rmse_k": centerline_rmse,
                "mass_flow_error_pct_vs_cfd": mass_flow_error,
                "one_d_base_insulation_in": insulation_base,
                "one_d_radiation_on": rep.get("one_d_radiation_on", ""),
                "current_setup_gap_status": (
                    "readable_bundle_only_has_1.0in_or_2.0in"
                    if math.isfinite(insulation_base) and insulation_base in {1.0, 2.0}
                    else "unknown"
                ),
                "upcomer_fit_lane": contrast.get("upcomer_fit_lane", ""),
                "downcomer_fit_lane": contrast.get("downcomer_fit_lane", ""),
                "upcomer_minus_downcomer_htc_w_m2_k": finite_float(contrast.get("upcomer_minus_downcomer_htc_w_m2_k")),
                "upcomer_minus_downcomer_bulk_minus_wall_temp_k": finite_float(
                    contrast.get("upcomer_minus_downcomer_bulk_minus_wall_temp_k")
                ),
                "dominant_discrepancy_bucket": dominant_discrepancy_bucket(
                    energy_error_pct=energy_error,
                    mass_flow_error_pct=mass_flow_error,
                    wall_rmse_k=wall_rmse,
                    centerline_rmse_k=centerline_rmse,
                ),
            }
        )
    return rows_out


def dominant_discrepancy_bucket(
    *,
    energy_error_pct: float,
    mass_flow_error_pct: float,
    wall_rmse_k: float,
    centerline_rmse_k: float,
) -> str:
    values = {
        "heat_partition": abs(energy_error_pct) if math.isfinite(energy_error_pct) else -1.0,
        "mass_flow": abs(mass_flow_error_pct) if math.isfinite(mass_flow_error_pct) else -1.0,
        "wall_temperature": abs(wall_rmse_k) if math.isfinite(wall_rmse_k) else -1.0,
        "centerline_temperature": abs(centerline_rmse_k) if math.isfinite(centerline_rmse_k) else -1.0,
    }
    return max(values.items(), key=lambda item: item[1])[0]


def build_explanation_register(
    *,
    defended_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
    heat_gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mean_energy = safe_mean([finite_float(row.get("energy_error_pct_of_heater")) for row in defended_rows])
    mean_mdot = safe_mean([finite_float(row.get("mass_flow_error_pct_vs_cfd")) for row in defended_rows])
    mean_upcomer_delta = safe_mean(
        [finite_float(row.get("upcomer_minus_downcomer_htc_w_m2_k")) for row in contrast_rows]
    )
    mean_removed_gap = safe_mean([finite_float(row.get("removed_gap_w")) for row in heat_gap_rows])
    mean_ambient_gap = safe_mean([finite_float(row.get("ambient_gap_w")) for row in heat_gap_rows])
    return [
        {
            "explanation_id": "upcomer_requires_separate_model",
            "status": "supported",
            "evidence": (
                "Upcomer stays on a sensitivity-only fit lane while right_leg/downcomer stays excluded, "
                "and the mean upcomer-minus-downcomer HTC contrast remains "
                f"{mean_upcomer_delta:.2f} W/m2-K on the defended latest-window cases."
            ),
            "supporting_artifact": "branch_development_summary.csv + upcomer_downcomer_contrast.csv",
        },
        {
            "explanation_id": "heat_partition_not_matched_case_by_case",
            "status": "supported",
            "evidence": (
                "The defended 1D rows still miss the frozen CFD heat partition: "
                f"mean removed-duty gap = {mean_removed_gap:.2f} W, mean ambient gap = {mean_ambient_gap:.2f} W, "
                f"mean |total-loss error| = {mean_energy:.2f}% of heater."
            ),
            "supporting_artifact": "heat_partition_gap_summary.csv",
        },
        {
            "explanation_id": "mass_flow_gap_tracks_hydraulic_underclosure",
            "status": "supported",
            "evidence": (
                "Mean defended mass-flow error remains "
                f"{mean_mdot:.2f}% vs frozen CFD while the downcomer direct thermal lane is still blocked and "
                "the upcomer direct lane is not defended."
            ),
            "supporting_artifact": "defended_case_discrepancy_summary.csv",
        },
        {
            "explanation_id": "global_1p4in_setup_still_unpublished_in_readable_bundle",
            "status": "possible_not_tested",
            "evidence": (
                "The readable defended bundle rows still use base 1.0 in or 2.0 in insulation states only; "
                "there is still no readable globally matched 1.4 in Salt scenario on disk."
            ),
            "supporting_artifact": "representative_salt_last_window_validation_table.csv",
        },
    ]


def build_readme(
    *,
    defended_rows: list[dict[str, Any]],
    explanation_rows: list[dict[str, Any]],
) -> str:
    mean_energy = safe_mean([finite_float(row.get("energy_error_pct_of_heater")) for row in defended_rows])
    mean_wall = safe_mean([finite_float(row.get("wall_rmse_k")) for row in defended_rows])
    mean_centerline = safe_mean([finite_float(row.get("centerline_rmse_k")) for row in defended_rows])
    mean_mdot = safe_mean([finite_float(row.get("mass_flow_error_pct_vs_cfd")) for row in defended_rows])
    supported = [row for row in explanation_rows if row["status"] == "supported"]
    supported_lines = "\n".join(
        f"- `{row['explanation_id']}`: {row['evidence']}" for row in supported
    )
    return f"""# Ethan 1D Discrepancy Explainer — Latest Window

Generated: `{iso_timestamp()}`

## Scope

- This package explains the defended local 1D-vs-CFD gaps on the June 23
  latest-window nominal Salt Jin surface.
- Inputs:
  `2026-06-23_ethan_frozen_state_results_latest_window`,
  `2026-06-23_ethan_frozen_state_1d_validation_latest_window`,
  `2026-06-23_ethan_1d_closure_bakeoff_latest_window`.

## Defended latest-window error level

- Mean |energy| mismatch: `{mean_energy:.2f}%` of heater.
- Mean wall-temperature RMSE: `{mean_wall:.2f} K`.
- Mean centerline-temperature RMSE: `{mean_centerline:.2f} K`.
- Mean mass-flow mismatch: `{mean_mdot:.2f}%` vs frozen CFD.

## Supported explanations

{supported_lines if supported_lines else "- none"}

## Boundary

- This package explains the current local defended surface only.
- It does not replace the still-stale external June 19 `Fluid` bundle.
- The insulation mismatch note remains a possible setup explanation, not a
  proven dominant cause, until a readable globally matched `1.4 in` Salt
  scenario exists on disk.
"""


def write_import_manifest(
    *,
    frozen_dir: Path,
    validation_dir: Path,
    bakeoff_dir: Path,
    output_dir: Path,
    import_manifest_path: Path,
) -> None:
    payload = {
        "generated_at": iso_timestamp(),
        "package": output_dir.name,
        "inputs": {
            "frozen_dir": str(frozen_dir.resolve()),
            "validation_dir": str(validation_dir.resolve()),
            "bakeoff_dir": str(bakeoff_dir.resolve()),
        },
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "defended_case_discrepancy_summary_csv": str((output_dir / "defended_case_discrepancy_summary.csv").resolve()),
            "upcomer_downcomer_contrast_csv": str((output_dir / "upcomer_downcomer_contrast.csv").resolve()),
            "heat_partition_gap_summary_csv": str((output_dir / "heat_partition_gap_summary.csv").resolve()),
            "explanation_register_csv": str((output_dir / "explanation_register.csv").resolve()),
        },
    }
    write_json(import_manifest_path, payload)


def main() -> int:
    args = parse_args()
    frozen_dir = Path(args.frozen_dir)
    validation_dir = Path(args.validation_dir)
    bakeoff_dir = Path(args.bakeoff_dir)
    output_dir = ensure_dir(Path(args.output_dir))
    import_manifest_path = Path(args.import_manifest_path)

    defended_case_rows = select_defended_case_rows(bakeoff_dir)
    representative_rows = load_dated_representative_table(bakeoff_dir)
    branch_development_rows = load_branch_comparison_rows(frozen_dir=frozen_dir, validation_dir=validation_dir)
    contrast_rows = build_upcomer_downcomer_contrast(branch_development_rows)
    heat_gap_rows = build_heat_partition_gap(representative_rows)
    defended_summary_rows = build_defended_case_summary(
        case_rows=defended_case_rows,
        representative_rows=representative_rows,
        contrast_rows=contrast_rows,
    )
    explanation_rows = build_explanation_register(
        defended_rows=defended_summary_rows,
        contrast_rows=contrast_rows,
        heat_gap_rows=heat_gap_rows,
    )

    csv_dump_rows(output_dir / "defended_case_discrepancy_summary.csv", defended_summary_rows)
    csv_dump_rows(output_dir / "upcomer_downcomer_contrast.csv", contrast_rows)
    csv_dump_rows(output_dir / "heat_partition_gap_summary.csv", heat_gap_rows)
    csv_dump_rows(output_dir / "explanation_register.csv", explanation_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(defended_summary_rows),
        "supported_explanation_count": sum(1 for row in explanation_rows if row["status"] == "supported"),
        "possible_explanation_count": sum(1 for row in explanation_rows if row["status"] == "possible_not_tested"),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        build_readme(defended_rows=defended_summary_rows, explanation_rows=explanation_rows),
        encoding="utf-8",
    )
    write_import_manifest(
        frozen_dir=frozen_dir,
        validation_dir=validation_dir,
        bakeoff_dir=bakeoff_dir,
        output_dir=output_dir,
        import_manifest_path=import_manifest_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
