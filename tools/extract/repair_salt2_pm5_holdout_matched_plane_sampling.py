#!/usr/bin/env python3
"""Validate and package repaired Salt2 +/-5Q PM5 matched-plane evidence.

This is intentionally validation-first. AGENT-406 already repaired the broken
July 14 PM5 sampling contract in staged copies, so this tool reuses those
artifacts unless required fields are absent.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-486"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair")
OUT = ROOT / OUT_REL

AGENT406_DIR = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
AGENT406_METRICS = AGENT406_DIR / "resampled_pm5_matched_plane_metrics.csv"
AGENT406_VALIDATION = AGENT406_DIR / "resampled_vtk_field_validation.csv"
AGENT406_COMMANDS = AGENT406_DIR / "command_log_manifest.csv"
AGENT406_SUMMARY = AGENT406_DIR / "summary.json"
JULY14_BROKEN = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md"

SALT2_CASES = ("salt2_lo5q", "salt2_hi5q")
PLANE_LOCATIONS = ("upcomer_inlet", "upcomer_mid", "upcomer_outlet")
REQUIRED_METRIC_FIELDS = (
    "sampled_plane_file",
    "sampled_wall_file",
    "face_count",
    "wall_face_count",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "bulk_T_K",
    "wall_T_K",
    "wallHeatFlux_W_m2",
    "Re",
    "Pr",
    "Ri",
    "Gr",
    "Ra",
    "Gz",
    "delta_T_wall_bulk_K",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def missing_required_fields(row: dict[str, str]) -> list[str]:
    missing = [field for field in REQUIRED_METRIC_FIELDS if row.get(field, "") in ("", "nan", "None")]
    if row.get("wallHeatFlux_available", "").lower() != "true":
        missing.append("wallHeatFlux_available")
    if row.get("metric_status") != "complete_with_wallHeatFlux":
        missing.append("metric_status_complete_with_wallHeatFlux")
    return missing


def salt2_metric_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("case_key") not in SALT2_CASES:
            continue
        missing = missing_required_fields(row)
        copied = dict(row)
        copied["case_role"] = "holdout"
        copied["holdout_only"] = "yes"
        copied["fit_forbidden"] = "yes"
        copied["model_selection_forbidden"] = "yes"
        copied["field_validation_status"] = "pass" if not missing else "fail"
        copied["missing_required_fields"] = ";".join(missing)
        copied["repair_source"] = "AGENT-406_resampled_staged_copy"
        out.append(copied)
    out.sort(key=lambda r: (r["case_key"], PLANE_LOCATIONS.index(r["plane_location"])))
    return out


def salt2_validation_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("case_key") not in SALT2_CASES:
            continue
        copied = dict(row)
        copied["holdout_only"] = "yes"
        copied["repair_source"] = "AGENT-406_resampled_staged_copy"
        out.append(copied)
    out.sort(key=lambda r: (r["case_key"], PLANE_LOCATIONS.index(r["plane_location"])))
    return out


def build_repair_decision(metric_rows: list[dict[str, Any]], validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_case = defaultdict(list)
    for row in metric_rows:
        rows_by_case[row["case_key"]].append(row)
    validation_by_case = defaultdict(list)
    for row in validation_rows:
        validation_by_case[row["case_key"]].append(row)
    decisions: list[dict[str, Any]] = []
    for case_key in SALT2_CASES:
        metrics = rows_by_case[case_key]
        validations = validation_by_case[case_key]
        missing = sorted({field for row in metrics for field in row["missing_required_fields"].split(";") if field})
        plane_set = {row["plane_location"] for row in metrics}
        validation_failures = [row for row in validations if row.get("validation_status") != "pass"]
        complete = (
            len(metrics) == 3
            and plane_set == set(PLANE_LOCATIONS)
            and not missing
            and len(validations) == 3
            and not validation_failures
        )
        decisions.append(
            {
                "case_key": case_key,
                "requested_plane_count": 3,
                "observed_metric_rows": len(metrics),
                "observed_validation_rows": len(validations),
                "plane_locations": ";".join(sorted(plane_set)),
                "missing_required_fields": ";".join(missing),
                "validation_failure_count": len(validation_failures),
                "repair_decision": "reuse_agent406_repaired_artifacts" if complete else "staged_copy_repair_required",
                "staged_copy_postprocessing_needed": "no" if complete else "yes",
                "do_not_run_old_broken_script": "yes",
                "source_paths": f"{rel(AGENT406_METRICS)};{rel(AGENT406_VALIDATION)};{rel(JULY14_BROKEN)}",
            }
        )
    return decisions


def build_source_manifest() -> list[dict[str, str]]:
    return [
        {"artifact": "agent406_repaired_metrics", "path": rel(AGENT406_METRICS), "use": "primary Salt2 PM5 metric rows"},
        {"artifact": "agent406_field_validation", "path": rel(AGENT406_VALIDATION), "use": "required VTK field validation"},
        {"artifact": "agent406_command_manifest", "path": rel(AGENT406_COMMANDS), "use": "repaired staged-copy command provenance"},
        {"artifact": "agent406_summary", "path": rel(AGENT406_SUMMARY), "use": "repaired package summary"},
        {"artifact": "july14_broken_contract", "path": rel(JULY14_BROKEN), "use": "known failure mode not to rerun unchanged"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(AGENT406_METRICS)}
  - {rel(AGENT406_VALIDATION)}
  - {rel(JULY14_BROKEN)}
tags: [salt2, pm5, holdout, matched-plane, extraction-repair]
related:
  - tools/extract/repair_salt2_pm5_holdout_matched_plane_sampling.py
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt2 PM5 Holdout Extraction Repair

This package validates and repackages the repaired AGENT-406 PM5 matched-plane
outputs for `salt2_lo5q` and `salt2_hi5q`.

## Result

- Salt2 holdout metric rows: `{summary['salt2_metric_rows']}`.
- Field-validation rows: `{summary['salt2_validation_rows']}`.
- Required-field failures: `{summary['required_field_failure_rows']}`.
- Staged-copy postprocessing needed now: `{summary['staged_copy_postprocessing_needed']}`.

The repair decision is to reuse AGENT-406 repaired staged-copy artifacts. The
old July 14 PM5 script is not relaunched unchanged.

## Files

- `salt2_pm5_holdout_metrics.csv`
- `salt2_pm5_field_validation.csv`
- `salt2_pm5_repair_decision.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(readme)


def build(out_dir: Path = OUT) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = salt2_metric_rows(read_csv(AGENT406_METRICS))
    validation = salt2_validation_rows(read_csv(AGENT406_VALIDATION))
    decisions = build_repair_decision(metrics, validation)
    write_csv(out_dir / "salt2_pm5_holdout_metrics.csv", metrics)
    write_csv(out_dir / "salt2_pm5_field_validation.csv", validation)
    write_csv(out_dir / "salt2_pm5_repair_decision.csv", decisions)
    write_csv(out_dir / "source_manifest.csv", build_source_manifest())
    status_counts = Counter(row["field_validation_status"] for row in metrics)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out_dir),
        "salt2_metric_rows": len(metrics),
        "salt2_validation_rows": len(validation),
        "case_keys": list(SALT2_CASES),
        "required_field_failure_rows": status_counts.get("fail", 0),
        "staged_copy_postprocessing_needed": "yes"
        if any(row["staged_copy_postprocessing_needed"] == "yes" for row in decisions)
        else "no",
        "old_broken_pm5_script_relaunched": "no",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
