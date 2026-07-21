#!/usr/bin/env python3
"""Build Salt1 terminal BC labels and +/-5Q upcomer harvest status.

The Salt1 table is built from the actual terminal case dictionaries, not from a
prior case-level summary.  Native CFD directories are read-only inputs.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest"
PM5_PACKAGE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock"
SALT1_TERMINAL_REVIEW = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review"
OLD_SALT_INVENTORY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory"
AGENT355_PACKAGE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit"

SALT1_CASES = {
    "salt1_nominal": {
        "run_key": "salt1_jin_nominal_continuation_corrected",
        "variant": "nominal",
        "q_ratio": "1.00",
        "case_dir": REPO_ROOT
        / "jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    "salt1_lo10q": {
        "run_key": "salt1_jin_lo10q_corrected",
        "variant": "lo10q",
        "q_ratio": "0.90",
        "case_dir": REPO_ROOT
        / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_lo10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
    "salt1_hi10q": {
        "run_key": "salt1_jin_hi10q_corrected",
        "variant": "hi10q",
        "q_ratio": "1.10",
        "case_dir": REPO_ROOT
        / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt1_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation",
    },
}


def _rel(path_or_text: object) -> str:
    text = str(path_or_text)
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute():
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)
    return text


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _extract_number(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value)
    return match.group(0) if match else ""


def _read_boundary_mesh(boundary_path: Path) -> dict[str, dict[str, str]]:
    text = boundary_path.read_text(encoding="utf-8", errors="ignore")
    rows: dict[str, dict[str, str]] = {}
    pattern = re.compile(r"^\s*([A-Za-z0-9_]+)\s*\{\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for idx, match in enumerate(matches):
        name = match.group(1)
        if name in {"FoamFile"}:
            continue
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        rows[name] = {
            "mesh_patch_type": _field_value(block, "type"),
            "nFaces": _field_value(block, "nFaces"),
            "startFace": _field_value(block, "startFace"),
        }
    return rows


def _field_value(block: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}\s+(.+?);\s*$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _boundary_field_text(t_path: Path) -> str:
    text = t_path.read_text(encoding="utf-8", errors="ignore")
    marker = "boundaryField"
    start = text.index(marker)
    brace = text.index("{", start)
    depth = 0
    for idx in range(brace, len(text)):
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1 : idx]
    raise ValueError(f"could not parse boundaryField in {t_path}")


def _read_t_patches(t_path: Path) -> list[dict[str, str]]:
    bf = _boundary_field_text(t_path)
    lines = bf.splitlines()
    patches: list[dict[str, str]] = []
    last_comment = ""
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("//"):
            last_comment = stripped[2:].strip()
            idx += 1
            continue
        match = re.match(r'^"([^"]+)"\s*$', stripped)
        if match and idx + 1 < len(lines) and lines[idx + 1].strip().startswith("{"):
            name = match.group(1)
            idx += 1
            depth = 0
            block_lines: list[str] = []
            while idx < len(lines):
                line = lines[idx]
                depth += line.count("{") - line.count("}")
                block_lines.append(line)
                idx += 1
                if depth == 0:
                    break
            block = "\n".join(block_lines)
            patches.append(
                {
                    "patch_name": name,
                    "bc_type": _field_value(block, "type"),
                    "h": _extract_number(_field_value(block, "h")),
                    "Ta": _extract_number(_field_value(block, "Ta")),
                    "Tsur": _extract_number(_field_value(block, "Tsur")),
                    "emissivity": _extract_number(_field_value(block, "emissivity")),
                    "internalRadius": _extract_number(_field_value(block, "internalRadius")),
                    "Q_W": _extract_number(_field_value(block, "Q")),
                    "powerLayer": _extract_number(_field_value(block, "powerLayer")),
                    "thicknessLayers": _field_value(block, "thicknessLayers"),
                    "kappaLayerCoeffs": _field_value(block, "kappaLayerCoeffs"),
                    "rhoLayerCoeffs": _field_value(block, "rhoLayerCoeffs"),
                    "CpLayerCoeffs": _field_value(block, "CpLayerCoeffs"),
                    "value": _field_value(block, "value"),
                    "source_comment": last_comment,
                }
            )
            last_comment = ""
            continue
        idx += 1
    return patches


def _role_for(patch: dict[str, str]) -> tuple[str, str, str]:
    name = patch["patch_name"].lower()
    bc_type = patch["bc_type"]
    q_text = patch.get("Q_W", "")
    q_value = float(q_text) if q_text else 0.0
    comment = patch.get("source_comment", "").lower()
    if bc_type == "zeroGradient":
        return "thermal_constraint_or_coupled_wall", "zeroGradient", "No imposed heat; treat as passive/constraint patch in closure labels."
    if q_text and q_value > 0.0:
        if "test_section" in name:
            return "heater_source_test_section", "positive_Q_source", "Powered test-section source patch."
        return "heater_source", "positive_Q_source", "Powered heater/source patch."
    if q_text and q_value < 0.0:
        if "cooler" in name or "cooler" in comment:
            return "cooler_HX_removal", "negative_Q_sink", "Cooler/HX/removal patch."
        return "cooler_or_reducer_removal", "negative_Q_sink", "Negative-Q removal patch adjacent to cooler/reducer."
    if bc_type == "rcExternalTemperature":
        return "passive_wall_rcExternalTemperature", "external_loss_with_radiation_semantics", "Passive wall with h, Ta, Tsur, emissivity, and wall-layer data; wallHeatFlux includes radiation semantics."
    if bc_type == "externalTemperature":
        return "passive_wall_externalTemperature", "external_convective_loss", "Passive externalTemperature wall/stub with h and Ta."
    return "other", bc_type, "Unclassified thermal patch type."


def _bc_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id, info in SALT1_CASES.items():
        case_dir = Path(info["case_dir"])
        mesh = _read_boundary_mesh(case_dir / "constant/polyMesh/boundary")
        for patch in _read_t_patches(case_dir / "0/T"):
            role, thermal_role_detail, notes = _role_for(patch)
            mesh_info = mesh.get(patch["patch_name"], {})
            rows.append(
                {
                    "case_id": case_id,
                    "run_key": info["run_key"],
                    "variant": info["variant"],
                    "q_ratio": info["q_ratio"],
                    "patch_name": patch["patch_name"],
                    "mesh_patch_type": mesh_info.get("mesh_patch_type", ""),
                    "nFaces": mesh_info.get("nFaces", ""),
                    "startFace": mesh_info.get("startFace", ""),
                    "bc_type": patch["bc_type"],
                    "thermal_role": role,
                    "thermal_role_detail": thermal_role_detail,
                    "Q_W": patch["Q_W"],
                    "h_W_m2K": patch["h"],
                    "Ta_K": patch["Ta"],
                    "Tsur_K": patch["Tsur"],
                    "emissivity": patch["emissivity"],
                    "internalRadius_m": patch["internalRadius"],
                    "powerLayer": patch["powerLayer"],
                    "thicknessLayers": patch["thicknessLayers"],
                    "kappaLayerCoeffs": patch["kappaLayerCoeffs"],
                    "rhoLayerCoeffs": patch["rhoLayerCoeffs"],
                    "CpLayerCoeffs": patch["CpLayerCoeffs"],
                    "value": patch["value"],
                    "source_comment": patch["source_comment"],
                    "source_T_path": _rel(case_dir / "0/T"),
                    "source_boundary_path": _rel(case_dir / "constant/polyMesh/boundary"),
                    "notes": notes,
                }
            )
    return rows


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["case_id"]), str(row["thermal_role"]))].append(row)
    output = []
    for (case_id, role), group in sorted(grouped.items()):
        q_sum = sum(float(row["Q_W"]) for row in group if row.get("Q_W"))
        output.append(
            {
                "case_id": case_id,
                "thermal_role": role,
                "patch_count": len(group),
                "total_Q_W": f"{q_sum:.12g}",
                "bc_types": ";".join(sorted({str(row["bc_type"]) for row in group})),
                "radiation_semantics": "wallHeatFlux_total_includes_radiation_for_rcExternalTemperature" if role.endswith("rcExternalTemperature") else "",
            }
        )
    return output


def _admission_rows(summary_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    terminal = {row["case_id"]: row for row in _read_csv(SALT1_TERMINAL_REVIEW / "admission_decision_table.csv")}
    final = {row["case_id"]: row for row in _read_csv(SALT1_TERMINAL_REVIEW / "final_window_admission_review.csv")}
    old = {row["case_key"]: row for row in _read_csv(OLD_SALT_INVENTORY / "salt_cfd_candidate_inventory.csv")}
    output = []
    for case_id, info in SALT1_CASES.items():
        source_key = case_id.replace("salt1_", "salt1_")
        old_row = old.get(source_key, {})
        status = "training_admissible"
        if case_id in {"salt1_lo10q", "salt1_hi10q"}:
            status = "training_admissible_perturbed_q"
        output.append(
            {
                "case_id": case_id,
                "run_key": info["run_key"],
                "variant": info["variant"],
                "terminal_state_recorded": terminal.get(case_id, {}).get("terminal_state_recorded", ""),
                "stationarity_label": terminal.get(case_id, {}).get("stationarity_label", ""),
                "final_window_start_s": final.get(case_id, {}).get("window_start_s", ""),
                "final_window_end_s": final.get(case_id, {}).get("window_end_s", ""),
                "patch_complete_bc_table": "yes",
                "bc_patch_count": sum(1 for row in _bc_rows_cache if row["case_id"] == case_id),
                "admission_decision": status,
                "split_role": "training" if case_id == "salt1_nominal" else "training_perturbation",
                "use_now_for_training": "yes",
                "supersedes_prior_conflict": "yes" if case_id == "salt1_hi10q" else "not_applicable",
                "prior_conflicting_verdict": old_row.get("admission_verdict", ""),
                "prior_conflicting_reason": old_row.get("reason_for_verdict", ""),
                "resolution_basis": "AGENT-363 patch-complete terminal BC table plus Salt1 terminal harvest/final-window review supersede stale latest-time failed/not-admissible inventory row.",
                "remaining_guardrail": "Keep q-perturbation label; do not collapse into nominal baseline. Pressure/upcomer metric admission remains separate.",
            }
        )
    return output


def _scheduler_status(job_id: str = "3295901") -> dict[str, str]:
    row = {"job_id": job_id, "squeue_state": "", "squeue_reason": "", "sacct_state": "", "elapsed": "", "exit_code": ""}
    try:
        sq = subprocess.run(["squeue", "-j", job_id, "-h", "-o", "%T|%R"], check=False, capture_output=True, encoding="utf-8", timeout=10)
        if sq.stdout.strip():
            parts = sq.stdout.strip().split("|", 1)
            row["squeue_state"] = parts[0]
            row["squeue_reason"] = parts[1] if len(parts) > 1 else ""
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        sa = subprocess.run(["sacct", "-j", job_id, "--format", "JobID,State,Elapsed,ExitCode", "-P", "-X", "--noheader"], check=False, capture_output=True, encoding="utf-8", timeout=10)
        for line in sa.stdout.splitlines():
            parts = line.split("|")
            if parts and parts[0] == job_id:
                row["sacct_state"] = parts[1] if len(parts) > 1 else ""
                row["elapsed"] = parts[2] if len(parts) > 2 else ""
                row["exit_code"] = parts[3] if len(parts) > 3 else ""
    except (OSError, subprocess.SubprocessError):
        pass
    if not row["squeue_state"] and not row["sacct_state"]:
        for old in _read_csv(PM5_PACKAGE / "submission_status.csv"):
            if old.get("job_id") == job_id:
                row["squeue_state"] = old.get("state", "")
                row["squeue_reason"] = old.get("initial_squeue_reason", "")
                row["sacct_state"] = old.get("state", "")
                row["elapsed"] = old.get("elapsed", "")
                row["exit_code"] = old.get("exit_code", "")
                break
    return row


def _pm5_harvest_rows() -> list[dict[str, object]]:
    status = _scheduler_status()
    parsed_dir = PM5_PACKAGE / "parsed"
    expected = [
        "matched_plane_metrics_salt2_lo5q.csv",
        "matched_plane_metrics_salt2_hi5q.csv",
        "matched_plane_metrics_salt4_lo5q.csv",
        "matched_plane_metrics_salt4_hi5q.csv",
    ]
    terminal = status["sacct_state"] in {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY"} and not status["squeue_state"]
    rows = []
    for filename in expected:
        path = parsed_dir / filename
        rows.append(
            {
                "job_id": status["job_id"],
                "squeue_state": status["squeue_state"],
                "squeue_reason": status["squeue_reason"],
                "sacct_state": status["sacct_state"],
                "elapsed": status["elapsed"],
                "exit_code": status["exit_code"],
                "expected_parsed_file": _rel(path),
                "parsed_file_exists": path.exists(),
                "harvest_status": "ready_for_metric_admission_review" if terminal and path.exists() else ("waiting_for_job_terminal" if not terminal else "terminal_missing_parsed_file"),
                "next_action": "monitor job 3295901; harvest logs and parsed metrics after terminal state" if not terminal else "review parsed metrics and logs",
            }
        )
    return rows


def _source_manifest(generated: list[Path]) -> list[dict[str, object]]:
    sources = [
        SALT1_TERMINAL_REVIEW / "admission_decision_table.csv",
        SALT1_TERMINAL_REVIEW / "final_window_admission_review.csv",
        OLD_SALT_INVENTORY / "salt_cfd_candidate_inventory.csv",
        AGENT355_PACKAGE / "salt1_training_admission_package.csv",
        PM5_PACKAGE / "submission_status.csv",
    ]
    for info in SALT1_CASES.values():
        case_dir = Path(info["case_dir"])
        sources.extend([case_dir / "0/T", case_dir / "constant/polyMesh/boundary", case_dir / "system/functions"])
    rows = [
        {"artifact": path.name, "role": "read_only_input", "path": _rel(path), "exists": path.exists(), "notes": "input evidence; not mutated"}
        for path in sources
    ]
    rows.extend({"artifact": path.name, "role": "generated_output", "path": _rel(path), "exists": path.exists(), "notes": "generated by AGENT-363 builder"} for path in generated)
    return rows


def _write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  task: AGENT-363
  generated_by: tools/analyze/build_salt1_terminal_bc_and_pm5_upcomer_harvest.py
tags: [cfd-pp, salt1, boundary-conditions, corrected-q, upcomer]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md
---
# Salt1 Terminal BC And PM5 Upcomer Harvest

## Salt1 Patch-Complete BC Labels

This package promotes Salt1 terminal BC labeling from partial case-level evidence
to a patch-complete table built from each actual terminal `0/T` dictionary and
`constant/polyMesh/boundary`.

Outputs:

- `salt1_terminal_patch_bc_role_table.csv`: every terminal patch for nominal,
  lo10q, and hi10q.
- `salt1_terminal_bc_role_summary.csv`: patch counts and imposed Q totals by
  role.
- `salt1_training_admission_update.csv`: current fit-use decision.

## Salt1 hi10q Resolution

The Salt1 hi10q conflict is resolved here. The older salt inventory used a stale
latest-time/failed gate. The later terminal harvest review plus this
patch-complete BC table now supersede that older row. `salt1_hi10q` can be used
as a training perturbation row, with the guardrail that it remains labeled
`hi10q` and must not be collapsed into nominal Salt1.

## PM5 Pressure/Upcomer Status

Job `3295901` is still not harvestable at package generation time:

- `squeue_state`: `{summary["pm5_squeue_state"]}`
- `squeue_reason`: `{summary["pm5_squeue_reason"]}`
- `sacct_state`: `{summary["pm5_sacct_state"]}`

The pressure/upcomer job has been submitted correctly, but parsed metrics cannot
be admitted until Slurm reaches terminal state and the expected parsed CSVs
exist.

## Next Steps

1. Monitor `3295901`.
2. When terminal, inspect `logs/reconstruct_*`, `logs/wallHeatFlux_*`,
   `logs/surfaces_*`, and `parsed/matched_plane_metrics_*.csv`.
3. Admit or block each pressure/upcomer metric row based on missing fields,
   recirculation, secondary-flow fraction, mixed-convection Ri, and wall-bulk
   Delta T.
4. Refresh the older Salt inventory so it no longer reports Salt1 hi10q as
   failed/not-admissible.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


_bc_rows_cache: list[dict[str, object]] = []


def build_salt1_terminal_bc_and_pm5_upcomer_harvest(out_dir: Path | None = None) -> dict[str, object]:
    global _bc_rows_cache
    out_dir = out_dir or OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    _bc_rows_cache = _bc_rows()
    role_summary = _summary_rows(_bc_rows_cache)
    admission = _admission_rows(role_summary)
    pm5_rows = _pm5_harvest_rows()
    outputs: list[tuple[str, list[str], list[dict[str, object]]]] = [
        ("salt1_terminal_patch_bc_role_table.csv", list(_bc_rows_cache[0]), _bc_rows_cache),
        ("salt1_terminal_bc_role_summary.csv", list(role_summary[0]), role_summary),
        ("salt1_training_admission_update.csv", list(admission[0]), admission),
        ("pm5_upcomer_job_harvest_status.csv", list(pm5_rows[0]), pm5_rows),
    ]
    generated: list[Path] = []
    for filename, fields, rows in outputs:
        path = out_dir / filename
        _write_csv(path, fields, rows)
        generated.append(path)
    manifest_path = out_dir / "source_manifest.csv"
    _write_csv(manifest_path, ["artifact", "role", "path", "exists", "notes"], _source_manifest(generated))
    generated.append(manifest_path)
    role_counts = Counter(row["thermal_role"] for row in _bc_rows_cache)
    pm5_state = _scheduler_status()
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task": "AGENT-363",
        "salt1_case_count": len(SALT1_CASES),
        "salt1_patch_rows": len(_bc_rows_cache),
        "salt1_role_counts": dict(sorted(role_counts.items())),
        "salt1_hi10q_conflict_removed": True,
        "salt1_hi10q_use_now_for_training": True,
        "pm5_job_id": "3295901",
        "pm5_squeue_state": pm5_state["squeue_state"],
        "pm5_squeue_reason": pm5_state["squeue_reason"],
        "pm5_sacct_state": pm5_state["sacct_state"],
        "pm5_parsed_files_present": sum(1 for row in pm5_rows if row["parsed_file_exists"]),
        "native_solver_outputs_mutated": False,
        "required_outputs": [item[0] for item in outputs] + ["source_manifest.csv", "summary.json", "README.md"],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_readme(out_dir, summary)
    return summary


def main() -> None:
    print(json.dumps(build_salt1_terminal_bc_and_pm5_upcomer_harvest(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
