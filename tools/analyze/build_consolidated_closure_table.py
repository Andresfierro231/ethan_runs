#!/usr/bin/env python3
"""Build a consolidated CFD-to-1D closure table from existing work products.

The table is intentionally provenance-heavy. It joins already-generated
friction, thermal, recirculation, model-fit, and run-status products without
reading or mutating native OpenFOAM case directories.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

DEFAULT_OUTPUT_DIR = ROOT / "work_products/2026-07-04_consolidated_closure_and_model_jobs"
FRICTION_PATH = ROOT / "work_products/2026-07-01_claude_segment_friction/segment_friction.csv"
THERMAL_DIR = ROOT / "work_products/2026-06-30_claude_thermal_htc"
UPCOMER_DIR = ROOT / "work_products/2026-06-30_claude_upcomer_convection_cell"
DOWNCOMER_PATH = ROOT / "work_products/2026-06-30_claude_downcomer_recirculation/downcomer_recirculation.csv"
SEGMENT_DP_PATH = ROOT / "work_products/2026-07-01_claude_1d_predictivity_trial/segment_dp_compare.csv"
PERLEG_MODEL_PATH = ROOT / "work_products/2026-07-01_claude_1d_predictivity_trial/perleg_vs_global_mdot.csv"
RUN_STATUS_PATH = ROOT / "work_products/2026-07-04_postprocessing_run_status_and_next_steps/run_status_inventory.csv"
MODEL_LADDER_PATH = ROOT / "work_products/2026-07-04_incremental_model_form_comparison/incremental_model_form_ladder.csv"

SOURCE_FIELDS = [
    "source_id",
    "salt",
    "fluid",
    "case_family",
    "span",
    "pressure_method",
    "closure_fit_admissible",
    "data_quality",
    "quality_flags",
    "friction_available",
    "reynolds_number",
    "apparent_darcy_f",
    "laminar_ref_darcy_f_64_over_Re",
    "excess_loss_factor_fapp_over_flam",
    "dp_loss_ds_pa_per_m",
    "dp_signed_ds_pa_per_m",
    "hydraulic_diameter_m",
    "segment_temperature_k",
    "mu_pa_s_used",
    "flow_alignment_min",
    "thermal_available",
    "htc_wm2k",
    "uaprime_wmk",
    "nu",
    "pr_effective",
    "wall_duty_Q_w",
    "qprime_wall_wm",
    "thermal_status",
    "thermal_note",
    "recirculation_available",
    "backflow_area_fraction",
    "recirculation_intensity",
    "ri_section_median",
    "ri_streamwise_median",
    "ra_section_median",
    "re_section_median",
    "recirculation_status",
    "model_cfd_dp_pa",
    "model_dP_pa",
    "model_pct_err",
    "model_f_over_flam",
    "run_job_id",
    "run_job_state",
    "run_case_label",
    "run_family",
    "run_case_verdict",
    "run_operating_point_verdict",
    "run_recommendation",
    "source_files",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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


def source_to_salt(source_id: str) -> int | None:
    for salt in (1, 2, 3, 4):
        if f"salt_test_{salt}" in source_id or f"salt{salt}" in source_id:
            return salt
    return None


def infer_source_id_from_path(path: Path, prefix: str, suffix: str) -> str:
    name = path.name
    if name.startswith(prefix):
        name = name[len(prefix) :]
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name


def case_family(source_id: str) -> str:
    if "water" in source_id:
        return "water"
    if "salt" in source_id and "jin" in source_id:
        return "salt_jin"
    if "salt" in source_id and "kirst" in source_id:
        return "salt_kirst"
    if "val_salt" in source_id:
        return "salt_val"
    return "unknown"


def fluid(source_id: str) -> str:
    if "water" in source_id:
        return "water"
    if "salt" in source_id:
        return "salt"
    return ""


def table_key(source_id: str, span: str, pressure_method: str = "") -> tuple[str, str, str]:
    return (source_id, span, pressure_method)


def ensure_row(rows: dict[tuple[str, str, str], dict[str, Any]], source_id: str, span: str, pressure_method: str = "") -> dict[str, Any]:
    key = table_key(source_id, span, pressure_method)
    if key not in rows:
        salt = source_to_salt(source_id)
        rows[key] = {
            "source_id": source_id,
            "salt": salt if salt is not None else "",
            "fluid": fluid(source_id),
            "case_family": case_family(source_id),
            "span": span,
            "pressure_method": pressure_method,
            "closure_fit_admissible": "screen_only",
            "data_quality": "partial",
            "quality_flags": "",
            "friction_available": "no",
            "thermal_available": "no",
            "recirculation_available": "no",
            "source_files": "",
        }
    return rows[key]


def append_source(row: dict[str, Any], path: Path) -> None:
    rel = relative_to_workspace(path)
    existing = [item for item in str(row.get("source_files", "")).split(";") if item]
    if rel not in existing:
        existing.append(rel)
    row["source_files"] = ";".join(existing)


def add_quality_flag(row: dict[str, Any], flag: str) -> None:
    if not flag:
        return
    flags = [item for item in str(row.get("quality_flags", "")).split(";") if item]
    if flag not in flags:
        flags.append(flag)
    row["quality_flags"] = ";".join(flags)


def ingest_friction(rows: dict[tuple[str, str, str], dict[str, Any]], path: Path) -> None:
    for item in read_csv(path):
        source_id = item.get("source_id", "")
        span = item.get("span", "")
        method = item.get("method", "")
        row = ensure_row(rows, source_id, span, method)
        row.update(
            {
                "friction_available": "yes",
                "reynolds_number": ffloat(item.get("reynolds_number")),
                "apparent_darcy_f": ffloat(item.get("apparent_darcy_f")),
                "laminar_ref_darcy_f_64_over_Re": ffloat(item.get("laminar_ref_darcy_f_64_over_Re")),
                "excess_loss_factor_fapp_over_flam": ffloat(item.get("excess_loss_factor_fapp_over_flam")),
                "dp_loss_ds_pa_per_m": ffloat(item.get("dp_loss_ds_pa_per_m")),
                "dp_signed_ds_pa_per_m": ffloat(item.get("dp_signed_ds_pa_per_m")),
                "hydraulic_diameter_m": ffloat(item.get("hydraulic_diameter_m")),
                "segment_temperature_k": ffloat(item.get("segment_temperature_k")),
                "mu_pa_s_used": ffloat(item.get("mu_pa_s_used")),
                "flow_alignment_min": ffloat(item.get("flow_alignment_min")),
            }
        )
        flags = item.get("flags", "")
        if flags:
            add_quality_flag(row, flags)
        if ffloat(item.get("apparent_darcy_f")) <= 0 or "negative_f" in flags:
            row["closure_fit_admissible"] = "no"
            row["data_quality"] = "rejected_friction_sign"
        append_source(row, path)


def ingest_thermal(rows: dict[tuple[str, str, str], dict[str, Any]], directory: Path) -> None:
    for path in sorted(directory.glob("segment_htc_uaprime_*.csv")):
        source_id = infer_source_id_from_path(path, "segment_htc_uaprime_", ".csv")
        for item in read_csv(path):
            span = item.get("segment", "") or item.get("cfd_spans", "")
            row = ensure_row(rows, source_id, span, "")
            row.update(
                {
                    "thermal_available": "yes",
                    "htc_wm2k": ffloat(item.get("htc_wm2k")),
                    "uaprime_wmk": ffloat(item.get("uaprime_wmk")),
                    "nu": ffloat(item.get("Nu")),
                    "wall_duty_Q_w": ffloat(item.get("wall_duty_Q_w")),
                    "qprime_wall_wm": ffloat(item.get("qprime_wall_wm")),
                    "thermal_status": item.get("status", ""),
                    "thermal_note": item.get("nu_note", ""),
                }
            )
            if item.get("thermally_blocked") == "True":
                add_quality_flag(row, "thermal_blocked")
            append_source(row, path)


def ingest_upcomer(rows: dict[tuple[str, str, str], dict[str, Any]], directory: Path) -> None:
    for path in sorted(directory.glob("upcomer_convection_cell_*.csv")):
        source_id = infer_source_id_from_path(path, "upcomer_convection_cell_", ".csv")
        for item in read_csv(path):
            span = item.get("span", "")
            row = ensure_row(rows, source_id, span, "")
            row.update(
                {
                    "recirculation_available": "yes",
                    "backflow_area_fraction": ffloat(item.get("backflow_area_fraction")),
                    "recirculation_intensity": ffloat(item.get("recirculation_intensity")),
                    "ri_section_median": ffloat(item.get("Ri_section_median")),
                    "ri_streamwise_median": ffloat(item.get("Ri_streamwise_median")),
                    "ra_section_median": ffloat(item.get("Ra_section_median")),
                    "re_section_median": ffloat(item.get("Re_section_median")),
                    "recirculation_status": item.get("status", ""),
                }
            )
            append_source(row, path)


def ingest_downcomer(rows: dict[tuple[str, str, str], dict[str, Any]], path: Path) -> None:
    for item in read_csv(path):
        row = ensure_row(rows, item.get("source_id", ""), item.get("span", ""), "")
        row.update(
            {
                "recirculation_available": "yes",
                "backflow_area_fraction": ffloat(item.get("backflow_area_fraction")),
                "recirculation_intensity": ffloat(item.get("recirculation_intensity")),
                "recirculation_status": item.get("status", ""),
            }
        )
        append_source(row, path)


def ingest_segment_dp(rows: dict[tuple[str, str, str], dict[str, Any]], path: Path) -> None:
    for item in read_csv(path):
        salt = item.get("salt", "")
        source_id = f"viscosity_screening_salt_test_{salt}_jin_coarse_mesh"
        span = item.get("element", "")
        kind = item.get("kind", "")
        if kind != "friction":
            span = f"minor::{span}"
        row = ensure_row(rows, source_id, span, "")
        row.update(
            {
                "model_cfd_dp_pa": ffloat(item.get("cfd_dP_pa")),
                "model_dP_pa": ffloat(item.get("model_dP_pa")),
                "model_pct_err": ffloat(item.get("pct_err")),
                "model_f_over_flam": ffloat(item.get("cfd_f_over_flam")),
            }
        )
        append_source(row, path)


def ingest_run_status(rows: dict[tuple[str, str, str], dict[str, Any]], path: Path) -> None:
    for item in read_csv(path):
        label = item.get("case_label", "")
        case_dir = item.get("case_dir", "")
        run_family = item.get("run_family", "")
        if run_family == "salt_q_perturbation":
            row = ensure_row(rows, label, "case_status", "")
            row.update(
                {
                    "closure_fit_admissible": item.get("closure_fit_admissible", "no"),
                    "data_quality": item.get("operating_point_verdict", "false_steady"),
                    "run_job_id": item.get("job_id", ""),
                    "run_job_state": item.get("job_state", ""),
                    "run_case_label": label,
                    "run_family": run_family,
                    "run_case_verdict": item.get("case_verdict", ""),
                    "run_operating_point_verdict": item.get("operating_point_verdict", ""),
                    "run_recommendation": item.get("recommendation", ""),
                }
            )
            add_quality_flag(row, item.get("recommendation_reason", ""))
            append_source(row, path)
            continue
        source_id = Path(case_dir).name if case_dir else label
        for row in rows.values():
            if row["source_id"] == source_id or label in str(row["source_id"]):
                row.update(
                    {
                        "run_job_id": item.get("job_id", ""),
                        "run_job_state": item.get("job_state", ""),
                        "run_case_label": label,
                        "run_family": item.get("run_family", ""),
                        "run_case_verdict": item.get("case_verdict", ""),
                        "run_operating_point_verdict": item.get("operating_point_verdict", ""),
                        "run_recommendation": item.get("recommendation", ""),
                    }
                )
                if item.get("closure_fit_admissible") == "no":
                    row["closure_fit_admissible"] = "no"
                    add_quality_flag(row, "run_not_closure_fit_admissible")
                append_source(row, path)


def finalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        if row.get("closure_fit_admissible") == "no":
            pass
        elif row.get("fluid") == "salt" and row.get("case_family") == "salt_jin":
            row["closure_fit_admissible"] = "yes_nominal_or_screen"
        if not row.get("quality_flags"):
            row["quality_flags"] = "none"
        if row.get("data_quality") == "partial" and row.get("closure_fit_admissible") == "yes_nominal_or_screen":
            row["data_quality"] = "usable_with_span_flags"
    rows.sort(key=lambda item: (str(item.get("source_id")), str(item.get("span")), str(item.get("pressure_method"))))
    return rows


def build_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_id"))].append(row)
    out: list[dict[str, Any]] = []
    for source_id, items in sorted(grouped.items()):
        flags = Counter(str(item.get("closure_fit_admissible", "")) for item in items)
        out.append(
            {
                "source_id": source_id,
                "salt": items[0].get("salt", ""),
                "fluid": items[0].get("fluid", ""),
                "case_family": items[0].get("case_family", ""),
                "row_count": len(items),
                "friction_rows": sum(item.get("friction_available") == "yes" for item in items),
                "thermal_rows": sum(item.get("thermal_available") == "yes" for item in items),
                "recirculation_rows": sum(item.get("recirculation_available") == "yes" for item in items),
                "admissible_rows": flags.get("yes_nominal_or_screen", 0),
                "rejected_rows": flags.get("no", 0),
            }
        )
    return out


def write_readme(output_dir: Path, row_count: int, case_count: int) -> None:
    lines = [
        "# Consolidated Closure And Model Jobs",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "This package joins existing CFD-to-1D closure work products into one provenance-heavy table.",
        "It does not run OpenFOAM and does not mutate case directories.",
        "",
        "## Files",
        "",
        "- `consolidated_closure_table.csv`: joined friction, HTC/UA', recirculation, model-comparison, and run-status rows.",
        "- `consolidated_closure_summary_by_case.csv`: per-case row counts and admissibility counts.",
        "- `consolidated_closure_summary.json`: source inventory and package counts.",
        "- `next_1d_model_forms/`: lightweight 1D model-form screen generated from this table.",
        "",
        "## Current Counts",
        "",
        f"- Rows: `{row_count}`",
        f"- Cases / run labels: `{case_count}`",
        "",
        "## Admission Rules",
        "",
        "- Nominal Salt Jin closure rows are kept as existing closure evidence with span-level quality flags.",
        "- Salt perturbation runs are represented as `case_status` rows only; their false-steady status is not joined onto nominal closure rows.",
        "- Rows with negative apparent friction remain in the table for auditability but are marked non-admissible.",
        "- Water rows will become useful after job `3265970` exits and the dependent Water postprocess job reruns the inventory.",
    ]
    output_dir.joinpath("README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    ingest_friction(rows, FRICTION_PATH)
    ingest_thermal(rows, THERMAL_DIR)
    ingest_upcomer(rows, UPCOMER_DIR)
    ingest_downcomer(rows, DOWNCOMER_PATH)
    ingest_segment_dp(rows, SEGMENT_DP_PATH)
    ingest_run_status(rows, RUN_STATUS_PATH)
    final = finalize_rows(list(rows.values()))
    summary = build_summary(final)
    csv_dump(output_dir / "consolidated_closure_table.csv", SOURCE_FIELDS, final)
    csv_dump(output_dir / "consolidated_closure_summary_by_case.csv", list(summary[0].keys()) if summary else [], summary)
    payload = {
        "generated_at": iso_timestamp(),
        "row_count": len(final),
        "case_count": len(summary),
        "sources": {
            "friction": relative_to_workspace(FRICTION_PATH),
            "thermal_dir": relative_to_workspace(THERMAL_DIR),
            "upcomer_dir": relative_to_workspace(UPCOMER_DIR),
            "downcomer": relative_to_workspace(DOWNCOMER_PATH),
            "segment_dp": relative_to_workspace(SEGMENT_DP_PATH),
            "run_status": relative_to_workspace(RUN_STATUS_PATH),
            "model_ladder": relative_to_workspace(MODEL_LADDER_PATH),
        },
    }
    json_dump(output_dir / "consolidated_closure_summary.json", payload)
    write_readme(output_dir, len(final), len(summary))
    print(f"Wrote {relative_to_workspace(output_dir / 'consolidated_closure_table.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
