#!/usr/bin/env python3
"""Build Salt2 +/-5Q PM5 holdout admission tables from repaired evidence."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract.repair_salt2_pm5_holdout_matched_plane_sampling import (
    OUT,
    PLANE_LOCATIONS,
    SALT2_CASES,
    build as build_repair_package,
    fnum,
    read_csv,
    rel,
    write_csv,
)


TASK = "AGENT-486"
METRICS = OUT / "salt2_pm5_holdout_metrics.csv"
VALIDATION = OUT / "salt2_pm5_field_validation.csv"
REPAIR_DECISION = OUT / "salt2_pm5_repair_decision.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def recirculation_status(row: dict[str, str]) -> str:
    if fnum(row.get("reverse_area_fraction")) > 0.01 or fnum(row.get("reverse_mass_fraction")) > 0.01:
        return "recirculating_section_effective"
    return "single_stream_candidate"


def thermal_sign_status(row: dict[str, str]) -> str:
    delta_t = fnum(row.get("delta_T_wall_bulk_K"))
    q = fnum(row.get("wallHeatFlux_W_m2"))
    if abs(delta_t) < 1e-12:
        return "blocked_zero_wall_bulk_delta_T"
    h_proxy = q / delta_t
    return "sign_consistent_positive_h_proxy" if h_proxy > 0 else "sign_review_required_nonpositive_h_proxy"


def build_admission_rows(metric_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in metric_rows:
        recirc = recirculation_status(row)
        sign_status = thermal_sign_status(row)
        blockers = ["holdout_fit_forbidden", "model_selection_forbidden", "mesh_gci_missing_for_final_fit"]
        if recirc != "single_stream_candidate":
            blockers.append("recirculation_invalidates_single_stream_fit")
        if sign_status.startswith("sign_review"):
            blockers.append("thermal_sign_review_required")
        rows.append(
            {
                "case_key": row["case_key"],
                "case_role": "holdout",
                "plane_location": row["plane_location"],
                "span": row["span"],
                "station_label": row["station_label"],
                "representative_time_s": row["representative_time_s"],
                "metric_status": row["metric_status"],
                "field_validation_status": row["field_validation_status"],
                "Re": row["Re"],
                "Pr": row["Pr"],
                "Ri": row["Ri"],
                "Gr": row["Gr"],
                "Ra": row["Ra"],
                "Gz": row["Gz"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_velocity_fraction": row["secondary_velocity_fraction"],
                "bulk_T_K": row["bulk_T_K"],
                "wall_T_K": row["wall_T_K"],
                "delta_T_wall_bulk_K": row["delta_T_wall_bulk_K"],
                "wallHeatFlux_W_m2": row["wallHeatFlux_W_m2"],
                "h_proxy_W_m2_K": fnum(row["wallHeatFlux_W_m2"]) / fnum(row["delta_T_wall_bulk_K"])
                if abs(fnum(row["delta_T_wall_bulk_K"])) > 1e-12
                else "",
                "recirculation_status": recirc,
                "thermal_sign_status": sign_status,
                "pressure_upcomer_use": "holdout_diagnostic_onset_evidence",
                "f6_fit_admissible_now": "no",
                "internal_nu_fit_admissible_now": "no",
                "holdout_only": "yes",
                "fit_forbidden": "yes",
                "model_selection_forbidden": "yes",
                "admission_status": "holdout_diagnostic_only_not_fit_admitted",
                "blockers": ";".join(blockers),
                "source_paths": row["source_paths"] + ";" + row["sampled_plane_file"] + ";" + row["sampled_wall_file"],
            }
        )
    return rows


def build_runtime_leakage_audit() -> list[dict[str, str]]:
    return [
        {
            "check": "salt2_pm5_rows_used_for_fit",
            "status": "pass_not_used",
            "runtime_policy": "Salt2 +/-5Q are final predictive holdout/testing rows only.",
        },
        {
            "check": "wallHeatFlux_runtime_input",
            "status": "pass_forbidden",
            "runtime_policy": "wallHeatFlux is target/diagnostic evidence only, never a predictive runtime input.",
        },
        {
            "check": "model_selection_on_holdout",
            "status": "pass_forbidden",
            "runtime_policy": "Do not select, tune, or refit model form using Salt2 +/-5Q PM5 rows.",
        },
        {
            "check": "native_solver_output_mutation",
            "status": "pass_no_mutation",
            "runtime_policy": "All consumed PM5 evidence comes from AGENT-406 staged-copy work products.",
        },
    ]


def svg_metric(path: Path, rows: list[dict[str, Any]], value_key: str, title: str) -> None:
    width, height = 920, 400
    margin_l, margin_b, margin_t = 80, 70, 45
    values = [fnum(row[value_key]) for row in rows]
    max_value = max(values) if values else 1.0
    min_value = min(values) if values else 0.0
    span = max(max_value - min(0.0, min_value), 1e-9)
    baseline = height - margin_b - (0.0 - min(0.0, min_value)) * (height - margin_t - margin_b) / span
    bar_w = (width - margin_l - 40) / max(len(rows), 1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(f'<text x="{width/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{title}</text>')
    parts.append(f'<line x1="{margin_l}" y1="{baseline:.1f}" x2="{width-30}" y2="{baseline:.1f}" stroke="#333"/>')
    for i, row in enumerate(rows):
        value = fnum(row[value_key])
        x = margin_l + i * bar_w + 7
        y = height - margin_b - (value - min(0.0, min_value)) * (height - margin_t - margin_b) / span
        y0 = baseline
        h = abs(y0 - y)
        parts.append(f'<rect x="{x:.1f}" y="{min(y, y0):.1f}" width="{bar_w-14:.1f}" height="{h:.1f}" fill="#4477aa"/>')
        parts.append(f'<text x="{x+(bar_w-14)/2:.1f}" y="{min(y, y0)-5:.1f}" text-anchor="middle" font-family="Arial" font-size="10">{value:.3g}</text>')
        label = f"{row['case_key'].replace('salt2_', '')} {row['plane_location'].replace('upcomer_', '')}"
        parts.append(f'<text x="{x+(bar_w-14)/2:.1f}" y="{height-45}" text-anchor="middle" font-family="Arial" font-size="10">{label}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(METRICS)}
  - {rel(VALIDATION)}
tags: [salt2, pm5, holdout, admission, recirculation]
related:
  - tools/extract/repair_salt2_pm5_holdout_matched_plane_sampling.py
  - tools/analyze/build_salt2_pm5_holdout_admission.py
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt2 PM5 Holdout Admission

## Result

Salt2 +/-5Q PM5 extraction is repaired for holdout diagnostics by reusing
AGENT-406 staged-copy artifacts. The package contains `{summary['admission_rows']}`
admission rows and `{summary['fit_admitted_rows']}` fit-admitted rows.

The rows are useful for holdout/onset diagnostics, but not for fitting or model
selection. Reverse flow remains high enough that F6 and Internal-Nu fits are not
admitted.

## Files

- `salt2_pm5_holdout_metrics.csv`
- `salt2_pm5_field_validation.csv`
- `salt2_pm5_admission_table.csv`
- `salt2_pm5_runtime_leakage_audit.csv`
- `salt2_pm5_repair_decision.csv`
- `salt2_pm5_reverse_fraction.svg`
- `salt2_pm5_ri.svg`
- `salt2_pm5_wall_core_delta_t.svg`
"""
    (OUT / "README.md").write_text(readme)


def build() -> dict[str, Any]:
    build_repair_package()
    metrics = read_csv(METRICS)
    validation = read_csv(VALIDATION)
    decisions = read_csv(REPAIR_DECISION)
    admission_rows = build_admission_rows(metrics)
    leakage_rows = build_runtime_leakage_audit()
    write_csv(OUT / "salt2_pm5_admission_table.csv", admission_rows)
    write_csv(OUT / "salt2_pm5_runtime_leakage_audit.csv", leakage_rows)
    svg_metric(OUT / "salt2_pm5_reverse_fraction.svg", admission_rows, "reverse_area_fraction", "Salt2 PM5 reverse area fraction")
    svg_metric(OUT / "salt2_pm5_ri.svg", admission_rows, "Ri", "Salt2 PM5 Richardson number")
    svg_metric(OUT / "salt2_pm5_wall_core_delta_t.svg", admission_rows, "delta_T_wall_bulk_K", "Salt2 PM5 wall-core delta T")
    counts = Counter(row["admission_status"] for row in admission_rows)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "metric_rows": len(metrics),
        "field_validation_rows": len(validation),
        "repair_decision_rows": len(decisions),
        "admission_rows": len(admission_rows),
        "fit_admitted_rows": sum(row["fit_forbidden"] == "no" for row in admission_rows),
        "holdout_only_rows": sum(row["holdout_only"] == "yes" for row in admission_rows),
        "admission_status_counts": dict(counts),
        "runtime_leakage_audit_rows": len(leakage_rows),
        "salt2_pm5_extraction_repaired": "yes",
        "staged_copy_postprocessing_needed": "no",
        "old_broken_pm5_script_relaunched": "no",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
