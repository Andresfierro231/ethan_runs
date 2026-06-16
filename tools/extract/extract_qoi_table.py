#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from statistics import mean
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    get_registry_row,
    json_dump,
    load_case_metadata,
    load_yaml,
    parse_log_summary,
    parse_probe_series,
    parse_scalar_series,
    parse_vol_field_series,
    path_lookup,
    safe_float,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a normalized QoI row for a registered case.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    row = get_registry_row(registry_path, args.source_id)
    source_root = Path(row["source_root"]).resolve()
    metadata = load_case_metadata(source_root)
    qoi_definitions = load_yaml(WORKSPACE_ROOT / "config" / "qoi_definitions.yaml")
    post_root = source_root / "postProcessing"
    log_summary = parse_log_summary(source_root / "logs" / "log.foamRun")
    convergence = log_summary.get("convergence", {})

    output_row: dict[str, object] = {}
    for field in qoi_definitions["fields"]:
        name = field["name"]
        if field.get("source") == "registry":
            output_row[name] = row.get(field["key"], field.get("default", ""))
        elif "path" in field:
            output_row[name] = path_lookup(metadata, field["path"], field.get("default", ""))
        else:
            output_row[name] = field.get("default", "")

    mdot_paths = sorted(post_root.glob("mdot_*/0/surfaceFieldValue.dat"))
    mdot_samples: dict[str, float] = {}
    mdot_abs_values: list[float] = []
    final_time = safe_float(output_row.get("final_time"))
    for path in mdot_paths:
        rows = parse_scalar_series(path)
        if not rows:
            continue
        final = rows[-1]
        mdot_samples[path.parent.parent.name] = final["value"]
        mdot_abs_values.append(abs(final["value"]))
        final_time = final["time"]

    total_q_rows = parse_scalar_series(post_root / "total_Q.dat")
    total_q_final = total_q_rows[-1] if total_q_rows else None
    if total_q_final is not None:
        final_time = total_q_final["time"]

    piv_rows = parse_vol_field_series(post_root / "piv_slab_velocity" / "0" / "volFieldValue.dat")
    piv_final = piv_rows[-1] if piv_rows else None
    if piv_final is not None:
        final_time = piv_final["time"]

    probe_payload = parse_probe_series(post_root / "temperature_probes" / "0" / "T")
    probe_rows = probe_payload["rows"]
    probe_final = probe_rows[-1] if probe_rows else None
    if probe_final is not None:
        final_time = probe_final["time"]

    probe_values = probe_final["values"] if probe_final else []
    total_q_value = total_q_final["value"] if total_q_final else None
    render_status_path = WORKSPACE_ROOT / "figures_rendered" / row["source_id"] / "status.json"
    render_status = ""
    if render_status_path.exists():
        with render_status_path.open("r", encoding="utf-8") as handle:
            render_status = json.load(handle).get("status", "")
    render_job_path = WORKSPACE_ROOT / "staging" / "render_jobs" / f"{row['source_id']}_render.sbatch"

    output_row.update(
        {
            "final_time": "" if final_time is None else final_time,
            "mdot_monitor_count": len(mdot_samples),
            "mdot_mean_abs_kg_s": "" if not mdot_abs_values else mean(mdot_abs_values),
            "mdot_abs_spread_kg_s": "" if not mdot_abs_values else max(mdot_abs_values) - min(mdot_abs_values),
            "mdot_right_02_middle_kg_s": mdot_samples.get("mdot_pipeleg_right_02_middle", ""),
            "mdot_lower_05_straight_kg_s": mdot_samples.get("mdot_pipeleg_lower_05_straight", ""),
            "mdot_upper_05_cooler_kg_s": mdot_samples.get("mdot_pipeleg_upper_05_cooler", ""),
            "mdot_left_04_test_section_kg_s": mdot_samples.get("mdot_pipeleg_left_04_test_section", ""),
            "final_total_wall_heat_w": "" if total_q_value is None else total_q_value,
            "final_total_wall_heat_abs_w": "" if total_q_value is None else abs(total_q_value),
            "piv_slab_Ux_m_s": "" if piv_final is None else piv_final["Ux"],
            "piv_slab_Uy_m_s": "" if piv_final is None else piv_final["Uy"],
            "piv_slab_Uz_m_s": "" if piv_final is None else piv_final["Uz"],
            "piv_slab_magU_m_s": "" if piv_final is None else piv_final["magU"],
            "piv_slab_T_K": "" if piv_final is None else piv_final["T"],
            "probe_count": len(probe_payload["probe_positions"]),
            "probe_T_avg_K": "" if not probe_values else mean(probe_values),
            "probe_T_min_K": "" if not probe_values else min(probe_values),
            "probe_T_max_K": "" if not probe_values else max(probe_values),
            "run_status": log_summary["status"],
            "run_termination_reason": log_summary["termination_reason"],
            "source_job_id": log_summary["job_id"],
            "source_case_path": log_summary["source_case_path"],
            "convergence_reached": convergence.get("reached", False),
            "convergence_iteration": convergence.get("iteration", ""),
            "convergence_dTmean": convergence.get("dTmean", ""),
            "convergence_dTsigma": convergence.get("dTsigma", ""),
            "convergence_dUmean": convergence.get("dUmean", ""),
            "convergence_tol": convergence.get("tol", ""),
            "render_status": render_status,
            "render_job_path": str(render_job_path) if render_job_path.exists() else "",
        }
    )

    if mdot_abs_values and total_q_value is not None:
        output_row["validation_status"] = "derived_postprocessing_available"
        output_row["validation_note"] = (
            "Derived from postProcessing outputs and solver log; source run ended with "
            + (log_summary["termination_reason"] or "unknown termination")
        )
    else:
        output_row["validation_status"] = "partial_postprocessing_only"
        output_row["validation_note"] = "Expected postProcessing metrics were incomplete."

    output_root = WORKSPACE_ROOT / "work_products" / row["source_id"]
    fieldnames = [field["name"] for field in qoi_definitions["fields"]]
    fieldnames.extend(
        [
            "final_time",
            "mdot_monitor_count",
            "mdot_mean_abs_kg_s",
            "mdot_abs_spread_kg_s",
            "mdot_right_02_middle_kg_s",
            "mdot_lower_05_straight_kg_s",
            "mdot_upper_05_cooler_kg_s",
            "mdot_left_04_test_section_kg_s",
            "final_total_wall_heat_w",
            "final_total_wall_heat_abs_w",
            "piv_slab_Ux_m_s",
            "piv_slab_Uy_m_s",
            "piv_slab_Uz_m_s",
            "piv_slab_magU_m_s",
            "piv_slab_T_K",
            "probe_count",
            "probe_T_avg_K",
            "probe_T_min_K",
            "probe_T_max_K",
            "run_status",
            "run_termination_reason",
            "source_job_id",
            "source_case_path",
            "convergence_reached",
            "convergence_iteration",
            "convergence_dTmean",
            "convergence_dTsigma",
            "convergence_dUmean",
            "convergence_tol",
            "render_status",
            "render_job_path",
        ]
    )
    csv_dump(output_root / "qoi_summary.csv", fieldnames, [output_row])
    json_dump(output_root / "qoi_summary.json", output_row)
    json_dump(
        output_root / "validation_summary.json",
        {
            "source_id": row["source_id"],
            "mdot_samples": mdot_samples,
            "total_wall_heat_series_final": total_q_final,
            "piv_slab_final": piv_final,
            "temperature_probe_final": probe_final,
            "log_summary": log_summary,
        },
    )
    print(json.dumps({"source_id": row["source_id"], "fields": fieldnames}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
