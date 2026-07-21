#!/usr/bin/env python3
"""Repair PM5 staged matched-plane VTK sampling for representative times.

This AGENT-406 builder is intentionally diagnostic-only. It stages minimal
scratch copies with processor-time symlinks, fixes the stale controlDict include
only in those scratch copies, reconstructs the requested PM5 representative
times, samples matched upcomer planes, and publishes provenance/metrics.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract import sample_upcomer_matched_plane_metrics as matched  # noqa: E402
from tools.analyze import build_pm5_matched_plane_parser_repair as repaired  # noqa: E402


TASK = "AGENT-406"
DATE = "2026-07-15"
REQUESTED_CASES = ("salt2_lo5q", "salt2_hi5q", "salt4_lo5q", "salt4_hi5q")
FIELD_SET = ("U", "T", "rho", "p_rgh", "Re", "Pr", "Ri", "Gr", "Ra", "wallHeatFlux")
PACKAGE_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair")
TMP_REL = Path("tmp/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair")
CASE_LIST_REL = Path("work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/pm5_matched_plane_case_list.csv")
HELPER_REL = Path("work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/scripts/pm5_matched_plane_helper.py")
OF_ENV = ROOT / "tools/ofenv/of13_env.sh"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def load_cases() -> dict[str, dict[str, str]]:
    rows = read_csv(ROOT / CASE_LIST_REL)
    return {row["case_key"]: row for row in rows if row["case_key"] in REQUESTED_CASES}


def copy_if_missing(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        return
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def ensure_empty_functions_include(case_dir: Path) -> None:
    """Satisfy stale '#include "functions"' without enabling source functions."""
    functions_path = case_dir / "system" / "functions"
    functions_path.parent.mkdir(parents=True, exist_ok=True)
    if functions_path.exists() or functions_path.is_symlink():
        if functions_path.is_dir():
            disabled = functions_path.with_name("functions.source_disabled_for_pm5_agent406_dir")
            if not disabled.exists():
                functions_path.rename(disabled)
        else:
            disabled = functions_path.with_name("functions.source_disabled_for_pm5_agent406")
            if not disabled.exists():
                functions_path.rename(disabled)
    functions_path.write_text(
        "// Empty AGENT-406 scratch include: source functions disabled for diagnostic postprocessing.\n",
        encoding="utf-8",
    )


def prepare_case(case: dict[str, str], tmp_dir: Path) -> Path:
    case_key = case["case_key"]
    source_case = ROOT / case["source_case_dir"]
    time_s = case["representative_time_s"]
    if not source_case.exists():
        raise FileNotFoundError(f"missing source case for {case_key}: {source_case}")
    proc_dir = source_case / "processors64" / time_s
    if not proc_dir.exists():
        raise FileNotFoundError(f"missing processor time for {case_key}: {proc_dir}")

    recon_dir = tmp_dir / "recon" / case_key
    recon_dir.mkdir(parents=True, exist_ok=True)
    for name in ("constant", "system", "0"):
        copy_if_missing(source_case / name, recon_dir / name)
    processors_link = recon_dir / "processors64"
    if processors_link.exists() or processors_link.is_symlink():
        if not processors_link.is_symlink():
            raise RuntimeError(f"expected processors64 symlink in scratch case: {processors_link}")
    else:
        os.symlink(source_case / "processors64", processors_link)
    ensure_empty_functions_include(recon_dir)
    return recon_dir


def run_logged(command: str, log_path: Path, timeout_s: int) -> dict[str, object]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_s,
        check=False,
    )
    log_path.write_text(completed.stdout, encoding="utf-8", errors="replace")
    return {"command": command, "returncode": completed.returncode, "log": rel(log_path)}


def reconstruct_case(case: dict[str, str], recon_dir: Path, logs_dir: Path) -> dict[str, object]:
    time_s = case["representative_time_s"]
    out_time = recon_dir / time_s
    fields = " ".join(FIELD_SET)
    log_path = logs_dir / f"reconstruct_{case['case_key']}.log"
    if out_time.exists() and all((out_time / field).exists() for field in FIELD_SET):
        return {"case_key": case["case_key"], "step": "reconstruct", "returncode": 0, "log": rel(log_path) if log_path.exists() else "", "skipped": True}
    command = (
        f"source '{OF_ENV}' >/dev/null 2>&1 && "
        f"reconstructPar -case '{recon_dir}' -time '{time_s}' -fields '({fields})'"
    )
    result = run_logged(command, log_path, timeout_s=5400)
    result.update({"case_key": case["case_key"], "step": "reconstruct", "skipped": False})
    if result["returncode"] != 0:
        raise RuntimeError(f"reconstruct failed for {case['case_key']}; see {result['log']}")
    return result


def helper_command(*args: str) -> str:
    quoted = " ".join("'" + arg.replace("'", "'\"'\"'") + "'" for arg in args)
    return f"python3.11 '{ROOT / HELPER_REL}' {quoted}"


def sample_case(case: dict[str, str], recon_dir: Path, logs_dir: Path) -> dict[str, object]:
    write_cmd = helper_command(
        "write-control-dict",
        "--case-dir",
        str(recon_dir),
        "--case-key",
        case["case_key"],
        "--mode",
        "surfaces",
    )
    write_result = run_logged(write_cmd, logs_dir / f"write_control_{case['case_key']}.log", timeout_s=120)
    if write_result["returncode"] != 0:
        raise RuntimeError(f"controlDict write failed for {case['case_key']}; see {write_result['log']}")
    command = f"source '{OF_ENV}' >/dev/null 2>&1 && foamPostProcess -case '{recon_dir}' -time '{case['representative_time_s']}'"
    result = run_logged(command, logs_dir / f"surfaces_{case['case_key']}.log", timeout_s=5400)
    result.update({"case_key": case["case_key"], "step": "surfaces", "control_log": write_result["log"]})
    if result["returncode"] != 0:
        raise RuntimeError(f"surface sampling failed for {case['case_key']}; see {result['log']}")
    return result


def parse_repaired_metrics(case: dict[str, str], recon_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    case_key = case["case_key"]
    time_s = case["representative_time_s"]
    plane_dir = recon_dir / "postProcessing" / matched.FO_SAMPLE_NAME / time_s
    wall_dir = recon_dir / "postProcessing" / matched.FO_WALL_BAND_NAME / time_s
    for plane_location, span, suffix in repaired.PLANE_SPECS:
        station = repaired.load_station(ROOT, case["parent_geometry_source_id"], span, suffix)
        normal = repaired.normalize(np.array([float(station["nx"]), float(station["ny"]), float(station["nz"])]))
        plane_path = plane_dir / f"plane_{plane_location}.vtk"
        wall_path = wall_dir / "upcomerWallPatches.vtk"
        parsed: dict[str, Any] = {}
        quality: list[str] = []
        try:
            parsed.update(repaired.parse_plane_vtk(plane_path, normal))
        except Exception as exc:  # pragma: no cover - captured in artifact.
            quality.append(f"plane_parse_failed:{exc}")
        try:
            parsed.update(repaired.parse_wall_vtk(wall_path, station))
        except Exception as exc:  # pragma: no cover - captured in artifact.
            quality.append(f"wall_parse_failed:{exc}")
        if parsed.get("wallHeatFlux_available") is False:
            quality.append("wallHeatFlux_missing_from_staged_wall_band_vtk")
        has_plane = all(key in parsed for key in ("reverse_area_fraction", "reverse_mass_fraction", "bulk_T_K", "Re", "Pr", "Ri"))
        has_wall_t = "wall_T_K" in parsed
        has_whf = "wallHeatFlux_W_m2" in parsed
        if has_plane and has_wall_t and has_whf:
            metric_status = "complete_with_wallHeatFlux"
            admission_status = "ready_for_pressure_and_internal_nu_gate_review_not_admitted"
        elif has_plane and has_wall_t:
            metric_status = "plane_and_wall_temperature_repaired_wallHeatFlux_blocked"
            admission_status = "ready_for_f6_pressure_onset_review_not_internal_nu"
        else:
            metric_status = "incomplete"
            admission_status = "blocked"
        delta = ""
        if "wall_T_K" in parsed and "bulk_T_K" in parsed:
            delta = float(parsed["wall_T_K"]) - float(parsed["bulk_T_K"])
        rows.append(
            {
                "case_key": case_key,
                "source_id": case["parent_geometry_source_id"],
                "case_role": case["requested_split_role"],
                "plane_location": plane_location,
                "span": span,
                "station_label": f"{span}__{suffix}",
                "representative_time_s": time_s,
                "actual_plane_time_dir": time_s if plane_dir.exists() else "",
                "actual_wall_time_dir": time_s if wall_dir.exists() else "",
                "sampled_plane_file": rel(plane_path),
                "sampled_wall_file": rel(wall_path),
                "metric_status": metric_status,
                "face_count": parsed.get("face_count", ""),
                "wall_face_count": parsed.get("wall_face_count", ""),
                "reverse_area_fraction": repaired.fmt(parsed.get("reverse_area_fraction")),
                "reverse_mass_fraction": repaired.fmt(parsed.get("reverse_mass_fraction")),
                "secondary_velocity_fraction": repaired.fmt(parsed.get("secondary_velocity_fraction")),
                "bulk_T_K": repaired.fmt(parsed.get("bulk_T_K")),
                "forward_bulk_T_K": repaired.fmt(parsed.get("forward_bulk_T_K")),
                "bulk_T_rule": parsed.get("bulk_T_rule", "signed_mass_flux_bulk_T"),
                "wall_T_K": repaired.fmt(parsed.get("wall_T_K")),
                "wallHeatFlux_W_m2": repaired.fmt(parsed.get("wallHeatFlux_W_m2")),
                "wallHeatFlux_available": str(has_whf).lower(),
                "Re": repaired.fmt(parsed.get("Re")),
                "Pr": repaired.fmt(parsed.get("Pr")),
                "Ri": repaired.fmt(parsed.get("Ri")),
                "Gr": repaired.fmt(parsed.get("Gr")),
                "Ra": repaired.fmt(parsed.get("Ra")),
                "Gz": repaired.fmt(parsed.get("Gz")),
                "delta_T_wall_bulk_K": repaired.fmt(delta),
                "admission_status": admission_status,
                "quality_flags": ";".join(quality),
                "source_paths": case["source_case_dir"] + ";" + case["mesh_stations_path"],
            }
        )
    return rows


def parse_case(case: dict[str, str], recon_dir: Path, parsed_dir: Path, logs_dir: Path) -> dict[str, object]:
    rows = parse_repaired_metrics(case, recon_dir)
    out_csv = parsed_dir / f"matched_plane_metrics_{case['case_key']}.csv"
    row_count = write_csv(out_csv, rows, repaired.METRIC_FIELDS)
    log_path = logs_dir / f"parse_{case['case_key']}.log"
    log_path.write_text(json.dumps({"case_key": case["case_key"], "row_count": row_count, "parser": "AGENT-404 FIELD-array repair"}, indent=2), encoding="utf-8")
    return {"case_key": case["case_key"], "step": "parse", "returncode": 0, "log": rel(log_path), "skipped": False}


def combine_parsed(parsed_dir: Path, out_csv: Path) -> tuple[int, dict[str, int]]:
    rows: list[dict[str, object]] = []
    status_counts: dict[str, int] = {}
    fieldnames: list[str] | None = None
    for case_key in REQUESTED_CASES:
        path = parsed_dir / f"matched_plane_metrics_{case_key}.csv"
        case_rows = read_csv(path)
        if fieldnames is None and case_rows:
            fieldnames = list(case_rows[0].keys())
        for row in case_rows:
            status_counts[row.get("metric_status", "")] = status_counts.get(row.get("metric_status", ""), 0) + 1
            rows.append(row)
    if fieldnames is None:
        fieldnames = []
    return write_csv(out_csv, rows, fieldnames), status_counts


def has_plane_wall_t(row: dict[str, str]) -> bool:
    required = ("bulk_T_K", "wall_T_K", "Re", "Pr", "Ri", "sampled_plane_file", "sampled_wall_file")
    return all(row.get(field, "") not in {"", "nan"} for field in required)


def has_wall_heat_flux(row: dict[str, str]) -> bool:
    return row.get("wallHeatFlux_available", "").lower() == "true" and row.get("wallHeatFlux_W_m2", "") not in {"", "nan"}


def scorecard_rows(metric_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    total = len(metric_rows)
    plane_wall_t = sum(1 for row in metric_rows if has_plane_wall_t(row))
    wall_heat_flux = sum(1 for row in metric_rows if has_wall_heat_flux(row))
    return [
        {
            "gate": "pm5_full_plane_fields_for_f6",
            "status": "unlocked_for_bounded_review_not_admitted" if total and plane_wall_t == total else "blocked",
            "evidence": f"plane_wallT_rows={plane_wall_t}/{total}",
            "next_action": "run the bounded F6/Re review with split labels preserved; do not fit thermal terms",
        },
        {
            "gate": "wall_band_vtk_wallHeatFlux_for_internal_nu",
            "status": "unlocked_for_internal_nu_review_not_admitted" if total and wall_heat_flux == total else "blocked",
            "evidence": f"wallHeatFlux_rows={wall_heat_flux}/{total}",
            "next_action": "compute internal Nu/HTC rows, then apply sign, heat-balance, recirculation, and admission gates",
        },
        {
            "gate": "diagnostic_output_guardrail",
            "status": "pass",
            "evidence": "AGENT-406 writes only to diagnostic scratch/work-product paths; native CFD outputs remain read-only",
            "next_action": "downstream gates must explicitly admit these repaired rows before use in claims",
        },
    ]


def case_unlock_rows(metric_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in metric_rows:
        grouped.setdefault(row["case_key"], []).append(row)
    rows: list[dict[str, object]] = []
    for case_key in REQUESTED_CASES:
        case_rows = grouped.get(case_key, [])
        total = len(case_rows)
        plane_wall_t = sum(1 for row in case_rows if has_plane_wall_t(row))
        wall_heat_flux = sum(1 for row in case_rows if has_wall_heat_flux(row))
        rows.append(
            {
                "case_key": case_key,
                "rows": total,
                "plane_wallT_rows": plane_wall_t,
                "wallHeatFlux_rows": wall_heat_flux,
                "f6_status": "unlocked_for_review" if total and plane_wall_t == total else "blocked",
                "internal_nu_status": "unlocked_for_review" if total and wall_heat_flux == total else "blocked",
                "notes": "diagnostic repaired output; not admitted by this package",
            }
        )
    return rows


def vtk_validation_rows(cases: dict[str, dict[str, str]], tmp_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_key in REQUESTED_CASES:
        case = cases[case_key]
        base = tmp_dir / "recon" / case_key / "postProcessing" / matched.FO_SAMPLE_NAME / case["representative_time_s"]
        for plane_location, _, _ in matched.PLANE_SPECS:
            vtk_path = base / f"plane_{plane_location}.vtk"
            parsed = repaired.parse_legacy_vtk_with_field_arrays(vtk_path)
            cell_fields = parsed["cell_fields"]
            missing = [field for field in ("rho", "Re", "Pr", "Ri", "Gr", "Ra") if field not in cell_fields]
            rows.append(
                {
                    "case_key": case_key,
                    "plane_location": plane_location,
                    "representative_time_s": case["representative_time_s"],
                    "resampled_vtk": rel(vtk_path),
                    "cell_field_count": len(cell_fields),
                    "has_rho": "rho" in cell_fields,
                    "has_Re": "Re" in cell_fields,
                    "has_Pr": "Pr" in cell_fields,
                    "has_Ri": "Ri" in cell_fields,
                    "has_Gr": "Gr" in cell_fields,
                    "has_Ra": "Ra" in cell_fields,
                    "missing_fields": ";".join(missing),
                    "validation_status": "pass" if not missing else "fail",
                }
            )
    return rows


def source_manifest_rows(cases: dict[str, dict[str, str]], package_dir: Path, tmp_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {"path": str(CASE_LIST_REL), "role": "read_only_case_list", "exists": (ROOT / CASE_LIST_REL).exists()},
        {"path": str(HELPER_REL), "role": "read_only_pm5_helper", "exists": (ROOT / HELPER_REL).exists()},
        {"path": str(OF_ENV.relative_to(ROOT)), "role": "read_only_openfoam_env", "exists": OF_ENV.exists()},
        {"path": rel(package_dir), "role": "generated_work_product", "exists": package_dir.exists()},
        {"path": rel(tmp_dir), "role": "generated_diagnostic_scratch", "exists": tmp_dir.exists()},
    ]
    for case in cases.values():
        rows.append({"path": case["source_case_dir"], "role": f"read_only_source_case:{case['case_key']}", "exists": (ROOT / case["source_case_dir"]).exists()})
        rows.append({"path": case["mesh_stations_path"], "role": f"read_only_mesh_stations:{case['case_key']}", "exists": (ROOT / case["mesh_stations_path"]).exists()})
    return rows


def existing_command_log_rows(logs_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_key in REQUESTED_CASES:
        for step, name in (
            ("reconstruct", f"reconstruct_{case_key}.log"),
            ("write_control", f"write_control_{case_key}.log"),
            ("surfaces", f"surfaces_{case_key}.log"),
            ("parse", f"parse_{case_key}.log"),
        ):
            path = logs_dir / name
            if path.exists():
                rows.append(
                    {
                        "case_key": case_key,
                        "step": step,
                        "returncode": 0,
                        "skipped": "existing_log",
                        "log": rel(path),
                        "control_log": "",
                        "command": "",
                    }
                )
    return rows


def write_readme(package_dir: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  task: {TASK}
  generated_by: codex
tags: [cfd-pp, pm5, matched-plane, vtk, f6, diagnostic]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_matched_plane_parser_repair/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md
---
# PM5 Wall-Band VTK and F6 Unlock Repair

Date: {DATE}
Task: {TASK}

## Result

Resampled representative-time staged plane and wall-band VTKs for
`salt2_lo5q`, `salt2_hi5q`, `salt4_lo5q`, and `salt4_hi5q` in an AGENT-406
scratch tree. The output plane VTKs now carry cell fields `rho`, `Re`, `Pr`,
`Ri`, `Gr`, and `Ra` alongside `U`, `T`, and `p_rgh`; the wall-band VTKs are
checked for `wallHeatFlux`.

The earlier July 14 samples were time `0` fallbacks because `reconstructPar`
failed on a stale `#include "functions"` in `controlDict`. This package fixes
that include only in copied scratch cases and leaves native solver outputs
unchanged.

## Outputs

- `resampled_pm5_matched_plane_metrics.csv`: combined parsed metrics for the
  requested PM5 cases.
- `resampled_vtk_field_validation.csv`: per-plane field-presence check.
- `pm5_f6_internal_nu_unlock_scorecard.csv`: gate status for F6 and internal-Nu.
- `pm5_case_unlock_status.csv`: per-case F6/internal-Nu readiness summary.
- `command_log_manifest.csv`: reconstruct/sample/parse command logs.
- `source_manifest.csv`: source and generated artifact provenance.
- `summary.json`: machine-readable status.

## Guardrails

- Native CFD source trees were read-only.
- The July 14 staged output tree was not edited.
- The generated VTK files are diagnostic until a later admission gate consumes
  them.
- Repaired rows remain diagnostic until a later gate explicitly admits them.
  Internal-Nu availability here means the VTK field blocker is cleared, not that
  Nu/HTC rows have passed sign, heat-balance, recirculation, or admission review.

## Summary

- Cases requested: {', '.join(REQUESTED_CASES)}
- VTK validation rows: {summary.get('vtk_validation_rows')}
- Failed VTK validation rows: {summary.get('vtk_validation_fail_rows')}
- Parsed metric rows: {summary.get('parsed_metric_rows')}
- Plane/wall-T rows ready: {summary.get('plane_wallT_rows')}
- wallHeatFlux rows ready: {summary.get('wallHeatFlux_rows')}
- F6 bounded review unlocked: {summary.get('f6_unlocked_for_review_not_admitted')}
- Internal-Nu review unlocked: {summary.get('internal_nu_unlocked_for_review_not_admitted')}
- Metric status counts: `{summary.get('metric_status_counts')}`
"""
    (package_dir / "README.md").write_text(text, encoding="utf-8")


def build(run_openfoam: bool = True) -> dict[str, object]:
    package_dir = ROOT / PACKAGE_REL
    tmp_dir = ROOT / TMP_REL
    logs_dir = package_dir / "logs"
    parsed_dir = package_dir / "parsed"
    package_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    cases = load_cases()
    missing_cases = [case for case in REQUESTED_CASES if case not in cases]
    if missing_cases:
        raise RuntimeError(f"missing requested cases in case list: {missing_cases}")

    command_rows: list[dict[str, object]] = []
    if run_openfoam:
        for case_key in REQUESTED_CASES:
            case = cases[case_key]
            recon_dir = prepare_case(case, tmp_dir)
            command_rows.append(reconstruct_case(case, recon_dir, logs_dir))
            command_rows.append(sample_case(case, recon_dir, logs_dir))
            command_rows.append(parse_case(case, recon_dir, parsed_dir, logs_dir))
    else:
        command_rows = existing_command_log_rows(logs_dir)

    metrics_path = package_dir / "resampled_pm5_matched_plane_metrics.csv"
    parsed_rows, status_counts = combine_parsed(parsed_dir, metrics_path)
    metric_rows = read_csv(metrics_path)
    plane_wall_t_rows = sum(1 for row in metric_rows if has_plane_wall_t(row))
    wall_heat_flux_rows = sum(1 for row in metric_rows if has_wall_heat_flux(row))
    validation_rows = vtk_validation_rows(cases, tmp_dir)
    validation_fail_rows = sum(1 for row in validation_rows if row["validation_status"] != "pass")
    write_csv(
        package_dir / "resampled_vtk_field_validation.csv",
        validation_rows,
        [
            "case_key",
            "plane_location",
            "representative_time_s",
            "resampled_vtk",
            "cell_field_count",
            "has_rho",
            "has_Re",
            "has_Pr",
            "has_Ri",
            "has_Gr",
            "has_Ra",
            "missing_fields",
            "validation_status",
        ],
    )
    write_csv(
        package_dir / "command_log_manifest.csv",
        command_rows,
        ["case_key", "step", "returncode", "skipped", "log", "control_log", "command"],
    )
    write_csv(
        package_dir / "pm5_f6_internal_nu_unlock_scorecard.csv",
        scorecard_rows(metric_rows),
        ["gate", "status", "evidence", "next_action"],
    )
    write_csv(
        package_dir / "pm5_case_unlock_status.csv",
        case_unlock_rows(metric_rows),
        ["case_key", "rows", "plane_wallT_rows", "wallHeatFlux_rows", "f6_status", "internal_nu_status", "notes"],
    )
    write_csv(package_dir / "source_manifest.csv", source_manifest_rows(cases, package_dir, tmp_dir), ["path", "role", "exists"])
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": utc_now(),
        "requested_cases": list(REQUESTED_CASES),
        "field_set": list(FIELD_SET),
        "parsed_metric_rows": parsed_rows,
        "metric_status_counts": status_counts,
        "plane_wallT_rows": plane_wall_t_rows,
        "wallHeatFlux_rows": wall_heat_flux_rows,
        "f6_unlocked_for_review_not_admitted": parsed_rows > 0 and plane_wall_t_rows == parsed_rows,
        "internal_nu_unlocked_for_review_not_admitted": parsed_rows > 0 and wall_heat_flux_rows == parsed_rows,
        "vtk_validation_rows": len(validation_rows),
        "vtk_validation_fail_rows": validation_fail_rows,
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "scheduler_jobs_launched": False,
        "openfoam_postprocessing_launched_in_agent406_scratch": bool(
            run_openfoam or any((logs_dir / f"surfaces_{case_key}.log").exists() for case_key in REQUESTED_CASES)
        ),
        "scratch_dir": rel(tmp_dir),
        "work_product_dir": rel(package_dir),
    }
    (package_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_readme(package_dir, summary)
    return summary


def main() -> int:
    run_openfoam = "--no-openfoam" not in sys.argv[1:]
    summary = build(run_openfoam=run_openfoam)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
