#!/usr/bin/env python3
"""Run a task-scoped reconstructed-T repair trial for Salt2 refined cases.

This deliberately avoids editing native solver outputs. It stages fresh mirrors,
tests OpenFOAM reconstruction modes, scans reconstructed T before use, and only
attempts thermal sampling when field-quality gates pass.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PKG = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial"
PKG = DEFAULT_PKG
LOGS = PKG / "logs"
OUTPUTS = PKG / "outputs"
RECON = PKG / "recon"
SCRIPTS = PKG / "scripts"
TASK_ID = "AGENT-267"

OF_ENV = ROOT / "tools/ofenv/of13_env.sh"
PROFILE = "viscosity_screening_salt_test_2_jin_coarse_mesh"
MESH_STATIONS = (
    ROOT
    / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
    / PROFILE
    / "mesh_stations.json"
)
BASE = Path("/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt")

PURE_FLOAT_RE = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?|nan|inf)$",
    re.IGNORECASE,
)
TARGET_LIST_RE = re.compile(r"^\s*(internalField|value)\s+nonuniform\s+List<scalar>\s*$")


@dataclass(frozen=True)
class Case:
    level: str
    source: Path
    time: str
    proc: str


CASES = [
    Case("medium", BASE / "medium/viscosity_screening_salt_test_2_jin_medium_mesh", "518", "processors64"),
    Case("fine", BASE / "fine/viscosity_screening_salt_test_2_jin_fine_mesh", "399", "processors128"),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_bash(command: str, *, cwd: Path, log_path: Path, timeout_s: int = 240) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    inner = f"source '{OF_ENV}' >/dev/null 2>&1 && of13_assert_ready && {command}"
    with log_path.open("w", encoding="utf-8") as log:
        try:
            proc = subprocess.run(
                ["bash", "-lc", inner],
                cwd=str(cwd),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout_s,
            )
            return int(proc.returncode)
        except subprocess.TimeoutExpired:
            log.write(f"\nTIMEOUT after {timeout_s} seconds\n")
            return 124


def prepare_stage(case: Case, stage: Path) -> None:
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for name in ("constant", "system", "0"):
        shutil.copytree(case.source / name, stage / name, symlinks=True)
    shutil.copy2(case.source / "case_config.yaml", stage / "case_config.yaml")
    (stage / "system" / "functions").write_text(
        "FoamFile { version 2.0; format ascii; class dictionary; object functions; }\n",
        encoding="utf-8",
    )
    control = stage / "system" / "controlDict"
    text = control.read_text(encoding="utf-8")
    if "maxThreadFileBufferSize" not in text:
        text = text.replace(
            "OptimisationSwitches\n{\n    fileHandler     collated;\n}",
            "OptimisationSwitches\n{\n    fileHandler     collated;\n    maxThreadFileBufferSize 0;\n}",
        )
    control.write_text(text, encoding="utf-8")
    (stage / case.proc).symlink_to(case.source / case.proc)
    (stage / "postProcessing").mkdir()
    (stage / "PROVENANCE.txt").write_text(
        "\n".join(
            [
                f"task={TASK_ID}",
                f"level={case.level}",
                f"source_case_root={case.source}",
                f"time={case.time}",
                f"processor_dir={case.proc}",
                f"created_at={now()}",
                "native_solver_outputs_mutated=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def scan_reconstructed_t(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "line_count": 0,
        "all_numeric_scalar_line_count": 0,
        "all_finite_count": 0,
        "all_nonfinite_count": 0,
        "all_min_finite": None,
        "all_max_finite": None,
        "first_all_nonfinite": None,
        "temperature_value_count": 0,
        "temperature_list_count": 0,
        "temperature_outside_250_1500K_count": 0,
        "temperature_min_K": None,
        "temperature_max_K": None,
        "first_temperature_outside_250_1500K": None,
        "temperature_lists": [],
        "examples": [],
        "gate_pass": False,
    }
    if not path.exists():
        return payload
    all_min_v = float("inf")
    all_max_v = float("-inf")
    temp_min_v = float("inf")
    temp_max_v = float("-inf")
    pending_kind: str | None = None
    active_kind: str | None = None
    active_expected: int | None = None
    active_count = 0
    active_min = float("inf")
    active_max = float("-inf")
    active_outside = 0
    active_start_line: int | None = None

    def close_active(end_line: int) -> None:
        nonlocal active_kind, active_expected, active_count, active_min, active_max, active_outside, active_start_line
        if active_kind is None:
            return
        payload["temperature_lists"].append(
            {
                "kind": active_kind,
                "start_line": active_start_line,
                "end_line": end_line,
                "expected_count": active_expected,
                "parsed_count": active_count,
                "min_K": active_min if active_count else None,
                "max_K": active_max if active_count else None,
                "outside_250_1500K_count": active_outside,
                "count_matches_header": active_expected == active_count if active_expected is not None else None,
            }
        )
        active_kind = None
        active_expected = None
        active_count = 0
        active_min = float("inf")
        active_max = float("-inf")
        active_outside = 0
        active_start_line = None

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            payload["line_count"] = line_no
            token = line.strip()
            if active_kind is not None:
                if token == ")":
                    close_active(line_no)
                    continue
                if PURE_FLOAT_RE.match(token):
                    value = float(token)
                    active_count += 1
                    payload["temperature_value_count"] += 1
                    if math.isfinite(value):
                        active_min = min(active_min, value)
                        active_max = max(active_max, value)
                        temp_min_v = min(temp_min_v, value)
                        temp_max_v = max(temp_max_v, value)
                    if not math.isfinite(value) or not (250.0 <= value <= 1500.0):
                        active_outside += 1
                        payload["temperature_outside_250_1500K_count"] += 1
                        payload["first_temperature_outside_250_1500K"] = payload[
                            "first_temperature_outside_250_1500K"
                        ] or {"line": line_no, "token": token, "value": value, "kind": active_kind}
                        if len(payload["examples"]) < 12:
                            payload["examples"].append(
                                {"kind": f"{active_kind}_outside_250_1500K", "line": line_no, "token": token}
                            )
                continue
            if pending_kind is not None:
                if token.isdigit():
                    active_expected = int(token)
                    continue
                if token == "(":
                    active_kind = pending_kind
                    pending_kind = None
                    active_start_line = line_no
                    payload["temperature_list_count"] += 1
                    continue
                continue
            match = TARGET_LIST_RE.match(line)
            if match:
                pending_kind = match.group(1)
                continue
            if PURE_FLOAT_RE.match(token):
                payload["all_numeric_scalar_line_count"] += 1
                value = float(token)
                if not math.isfinite(value):
                    payload["all_nonfinite_count"] += 1
                    payload["first_all_nonfinite"] = payload["first_all_nonfinite"] or {
                        "line": line_no,
                        "token": token,
                    }
                    if len(payload["examples"]) < 12:
                        payload["examples"].append({"kind": "all_nonfinite", "line": line_no, "token": token})
                    continue
                payload["all_finite_count"] += 1
                all_min_v = min(all_min_v, value)
                all_max_v = max(all_max_v, value)
    if active_kind is not None:
        close_active(payload["line_count"])
    if payload["all_finite_count"]:
        payload["all_min_finite"] = all_min_v
        payload["all_max_finite"] = all_max_v
    if payload["temperature_value_count"]:
        payload["temperature_min_K"] = temp_min_v
        payload["temperature_max_K"] = temp_max_v
    list_count_mismatches = [
        item for item in payload["temperature_lists"] if item.get("count_matches_header") is False
    ]
    payload["gate_pass"] = (
        payload["exists"]
        and payload["all_numeric_scalar_line_count"] > 1000
        and payload["all_nonfinite_count"] == 0
        and payload["temperature_value_count"] > 1000
        and payload["temperature_outside_250_1500K_count"] == 0
        and not list_count_mismatches
    )
    return payload


def extract_foam_io(log_path: Path) -> str:
    if not log_path.exists():
        return ""
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("I/O"):
            return line.strip()
    return ""


def reconstruct(
    case: Case,
    method: str,
    fields: str,
    *,
    full: bool = False,
    command_timeout_s: int = 180,
) -> dict[str, Any]:
    stage = RECON / f"{case.level}_{method}{'_full' if full else ''}"
    prepare_stage(case, stage)
    log_path = LOGS / f"reconstruct_{case.level}_{method}{'_full' if full else ''}.log"
    if method == "default_case_arg":
        command = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -case '{stage}' "
            f"-time '{case.time}' -fields '{fields}' -noFunctionObjects"
        )
        cwd = ROOT
    elif method == "cwd_controlDict_collated":
        command = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -time '{case.time}' "
            f"-fields '{fields}' -noFunctionObjects"
        )
        cwd = stage
    elif method == "explicit_fileHandler_collated":
        command = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -case '{stage}' "
            f"-time '{case.time}' -fields '{fields}' "
            "-fileHandler collated -noFunctionObjects"
        )
        cwd = ROOT
    else:
        raise ValueError(method)
    rc = run_bash(command, cwd=cwd, log_path=log_path, timeout_s=command_timeout_s + 90)
    scan = scan_reconstructed_t(stage / case.time / "T")
    return {
        "level": case.level,
        "method": method,
        "full_fields": full,
        "split_full_fields": False,
        "fields": fields,
        "stage": rel(stage),
        "log": rel(log_path),
        "returncode": rc,
        "foam_io": extract_foam_io(log_path),
        "scan": scan,
        "clean_T": rc == 0 and scan["gate_pass"],
    }


def reconstruct_split_full(case: Case, method: str, *, command_timeout_s: int = 180) -> dict[str, Any]:
    """Reconstruct T first, then non-T fields, preserving a clean T gate.

    Full-field reconstruction has reproduced auxiliary boundary scalar NaNs in
    T even when T-only reconstruction is clean. This split test verifies whether
    a final analysis stage can keep the clean T file while adding the remaining
    fields needed by pressure and thermal samplers.
    """
    stage = RECON / f"{case.level}_{method}_split_full"
    prepare_stage(case, stage)
    log_t = LOGS / f"reconstruct_{case.level}_{method}_split_T.log"
    log_other = LOGS / f"reconstruct_{case.level}_{method}_split_nonT.log"
    if method == "cwd_controlDict_collated":
        cmd_t = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -time '{case.time}' "
            "-fields '(T)' -noFunctionObjects"
        )
        cmd_other = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -time '{case.time}' "
            "-fields '(p_rgh U rho wallHeatFlux wallShearStress yPlus)' -noFunctionObjects"
        )
        cwd = stage
    elif method == "default_case_arg":
        cmd_t = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -case '{stage}' "
            f"-time '{case.time}' -fields '(T)' -noFunctionObjects"
        )
        cmd_other = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -case '{stage}' -time '{case.time}' "
            "-fields '(p_rgh U rho wallHeatFlux wallShearStress yPlus)' -noFunctionObjects"
        )
        cwd = ROOT
    elif method == "explicit_fileHandler_collated":
        cmd_t = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -case '{stage}' "
            f"-time '{case.time}' -fields '(T)' "
            "-fileHandler collated -noFunctionObjects"
        )
        cmd_other = (
            f"timeout --kill-after=30s {command_timeout_s}s reconstructPar -case '{stage}' -time '{case.time}' "
            "-fields '(p_rgh U rho wallHeatFlux wallShearStress yPlus)' -fileHandler collated -noFunctionObjects"
        )
        cwd = ROOT
    else:
        raise ValueError(method)
    rc_t = run_bash(cmd_t, cwd=cwd, log_path=log_t, timeout_s=command_timeout_s + 90)
    scan_after_t = scan_reconstructed_t(stage / case.time / "T")
    rc_other = 99
    scan_after_other = scan_after_t
    if rc_t == 0 and scan_after_t["gate_pass"]:
        rc_other = run_bash(cmd_other, cwd=cwd, log_path=log_other, timeout_s=command_timeout_s + 90)
        scan_after_other = scan_reconstructed_t(stage / case.time / "T")
    rc = rc_other if rc_t == 0 else rc_t
    return {
        "level": case.level,
        "method": method,
        "full_fields": True,
        "split_full_fields": True,
        "fields": "(T) then (p_rgh U rho wallHeatFlux wallShearStress yPlus)",
        "stage": rel(stage),
        "log": f"{rel(log_t)}; {rel(log_other)}",
        "returncode": rc,
        "returncode_T": rc_t,
        "returncode_nonT": rc_other,
        "foam_io": extract_foam_io(log_t),
        "scan_after_T_only": scan_after_t,
        "scan": scan_after_other,
        "clean_T": rc_t == 0 and rc_other == 0 and scan_after_t["gate_pass"] and scan_after_other["gate_pass"],
    }


def run_section_temperature_sampling(case: Case, stage_rel: str, *, timeout_s: int = 900) -> dict[str, Any]:
    stage = ROOT / stage_rel
    out = OUTPUTS / case.level
    out.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"section_temperature_{case.level}.log"
    functions_file = stage / "system" / "functions"
    if functions_file.exists() or functions_file.is_symlink():
        functions_file.unlink()
    command = (
        f"python3 '{ROOT / 'tools/extract/sample_section_mean_pressure.py'}' "
        f"--case-dir '{stage}' --time '{case.time}' --source-id '{PROFILE}' --output-dir '{out}' "
        f"--of-env-script tools/ofenv/of13_env.sh --centerline-source mesh "
        f"--mesh-stations '{MESH_STATIONS}' --dump-temperature"
    )
    with log.open("w", encoding="utf-8") as handle:
        try:
            rc = subprocess.run(
                ["bash", "-lc", command],
                cwd=str(ROOT),
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout_s,
            ).returncode
        except subprocess.TimeoutExpired:
            handle.write(f"\nTIMEOUT after {timeout_s} seconds\n")
            rc = 124
    section_json = out / f"section_mean_pressure_{PROFILE}.json"
    sampled = 0
    by_span: dict[str, int] = {}
    if section_json.exists():
        data = json.loads(section_json.read_text(encoding="utf-8"))
        rows = data.get("stations") or data.get("rows") or []
        for row in rows:
            if row.get("status") == "sampled":
                sampled += 1
                span = str(row.get("span"))
                by_span[span] = by_span.get(span, 0) + 1
    foam_log = out / f"foampostprocess_{PROFILE}.log"
    text = foam_log.read_text(encoding="utf-8", errors="replace") if foam_log.exists() else ""
    return {
        "level": case.level,
        "step": "section_temperature_sampling",
        "returncode": rc,
        "log": rel(log),
        "foam_log": rel(foam_log),
        "section_json": rel(section_json),
        "sampled_rows": sampled,
        "sampled_by_span": by_span,
        "foam_fatal": "FOAM FATAL" in text,
        "gate_pass": rc == 0 and sampled >= 30 and "FOAM FATAL" not in text,
    }


def run_segment_thermal(case: Case, stage_rel: str, *, timeout_s: int = 900) -> dict[str, Any]:
    stage = ROOT / stage_rel
    out = OUTPUTS / case.level
    (stage / "postProcessing").mkdir(exist_ok=True)
    functions_file = stage / "system" / "functions"
    if functions_file.exists() or functions_file.is_symlink():
        functions_file.unlink()
    whf_link = stage / "postProcessing" / "wallHeatFlux"
    if whf_link.exists() or whf_link.is_symlink():
        whf_link.unlink()
    whf_link.symlink_to(case.source / "postProcessing" / "wallHeatFlux")
    log = LOGS / f"segment_thermal_{case.level}.log"
    base_command = (
        f"python3 '{ROOT / 'tools/extract/sample_segment_htc_uaprime.py'}' "
        f"--case-dir '{stage}' --time '{case.time}' --source-id '{PROFILE}' --output-dir '{out}' "
        f"--mesh-length --mesh-stations '{MESH_STATIONS}'"
    )
    with log.open("w", encoding="utf-8") as handle:
        try:
            rc = subprocess.run(
                ["bash", "-lc", base_command],
                cwd=str(ROOT),
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout_s,
            ).returncode
        except subprocess.TimeoutExpired:
            handle.write(f"\nTIMEOUT after {timeout_s} seconds\n")
            rc = 124

    def parse_segment_csv(csv_path: Path) -> tuple[list[dict[str, str]], dict[str, int], int]:
        parsed_rows = []
        parsed_statuses: dict[str, int] = {}
        parsed_computed_finite_rows = 0
        if csv_path.exists():
            with csv_path.open(encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    parsed_rows.append(row)
                    status = row.get("status", "")
                    parsed_statuses[status] = parsed_statuses.get(status, 0) + 1
                    numeric_values = [
                        row.get("T_bulk_k", ""),
                        row.get("T_wall_k", ""),
                        row.get("htc_wm2k", ""),
                        row.get("uaprime_wmk", ""),
                    ]
                    try:
                        if status.startswith("computed") and all(math.isfinite(float(v)) for v in numeric_values):
                            parsed_computed_finite_rows += 1
                    except ValueError:
                        pass
        return parsed_rows, parsed_statuses, parsed_computed_finite_rows

    csv_path = out / f"segment_htc_uaprime_{PROFILE}.csv"
    rows, statuses, computed_finite_rows = parse_segment_csv(csv_path)
    if rc != 0 or (rows and computed_finite_rows == 0 and statuses.get("no_cutplane_output", 0) > 0):
        # sample_segment_htc_uaprime.py currently hard-codes the OF12 env for
        # foamPostProcess. For OF13-reconstructed T with rcExternalTemperature,
        # rerun only the generated segthermSurfaces controlDict under OF13 and
        # then parse with --skip-run.
        of13_log = LOGS / f"segment_thermal_{case.level}_of13_foampostprocess.log"
        of13_rc = run_bash(
            f"foamPostProcess -case '{stage}' -time '{case.time}'",
            cwd=stage,
            log_path=of13_log,
            timeout_s=timeout_s,
        )
        skip_log = LOGS / f"segment_thermal_{case.level}_skip_run.log"
        skip_command = f"{base_command} --skip-run"
        with skip_log.open("w", encoding="utf-8") as handle:
            try:
                skip_rc = subprocess.run(
                    ["bash", "-lc", skip_command],
                    cwd=str(ROOT),
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_s,
                ).returncode
            except subprocess.TimeoutExpired:
                handle.write(f"\nTIMEOUT after {timeout_s} seconds\n")
                skip_rc = 124
        rc = skip_rc if of13_rc == 0 else rc
        log = skip_log
        rows, statuses, computed_finite_rows = parse_segment_csv(csv_path)
    return {
        "level": case.level,
        "step": "segment_thermal_extraction",
        "returncode": rc,
        "log": rel(log),
        "csv": rel(csv_path),
        "row_count": len(rows),
        "statuses": statuses,
        "computed_finite_rows": computed_finite_rows,
        "gate_pass": rc == 0 and computed_finite_rows > 0,
    }


def write_summary(results: dict[str, Any]) -> None:
    write_json(PKG / "summary.json", results)
    with (OUTPUTS / "reconstruction_trials.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "level",
            "method",
            "full_fields",
            "split_full_fields",
            "returncode",
            "foam_io",
            "all_numeric_scalar_line_count",
            "all_nonfinite_count",
            "all_min_finite",
            "all_max_finite",
            "temperature_value_count",
            "temperature_list_count",
            "temperature_outside_250_1500K_count",
            "temperature_min_K",
            "temperature_max_K",
            "clean_T",
            "stage",
            "log",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in results["reconstruction_trials"]:
            scan = row["scan"]
            writer.writerow(
                {
                    "level": row["level"],
                    "method": row["method"],
                    "full_fields": row["full_fields"],
                    "split_full_fields": row.get("split_full_fields", False),
                    "returncode": row["returncode"],
                    "foam_io": row["foam_io"],
                    "all_numeric_scalar_line_count": scan["all_numeric_scalar_line_count"],
                    "all_nonfinite_count": scan["all_nonfinite_count"],
                    "all_min_finite": scan["all_min_finite"],
                    "all_max_finite": scan["all_max_finite"],
                    "temperature_value_count": scan["temperature_value_count"],
                    "temperature_list_count": scan["temperature_list_count"],
                    "temperature_outside_250_1500K_count": scan["temperature_outside_250_1500K_count"],
                    "temperature_min_K": scan["temperature_min_K"],
                    "temperature_max_K": scan["temperature_max_K"],
                    "clean_T": row["clean_T"],
                    "stage": row["stage"],
                    "log": row["log"],
                }
            )
    (PKG / "README.md").write_text(
        f"""# Reconstructed T Repair Trial

Task: `{results['task_id']}`

Generated: `{results['generated_at']}`

This package tests fresh reconstructed-`T` paths for Salt2 refined thermal
sampling without mutating native solver outputs. The `T` scan separates
whole-file scalar syntax/nonfinite checks from Kelvin plausibility checks,
because OpenFOAM boundary dictionaries can store auxiliary non-temperature
scalars such as `qConv`, `refGradient`, `valueFraction`, `h`, and `Q` in the
same `T` file.

## Decision

{results['decision']}

## Key Outputs

- `summary.json`
- `outputs/reconstruction_trials.csv`
- `outputs/<level>/section_mean_pressure_{PROFILE}.csv`
- `outputs/<level>/segment_htc_uaprime_{PROFILE}.csv` when the thermal smoke ran

## Boundary

These are repair-trial outputs. They are not closure-fit admissions by
themselves; the next step is review against heat-balance, sign, and mesh-family
admission gates.
""",
        encoding="utf-8",
    )


def main() -> int:
    global PKG, LOGS, OUTPUTS, RECON, SCRIPTS, TASK_ID
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--medium-only", action="store_true", help="Run only medium trials.")
    parser.add_argument("--fine-only", action="store_true", help="Run only the fine split-reconstruction workflow.")
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=DEFAULT_PKG,
        help="Output package root. Defaults to the original AGENT-267 repair-trial package.",
    )
    parser.add_argument("--task-id", default=TASK_ID, help="Task ID recorded in provenance and summaries.")
    parser.add_argument(
        "--reconstruct-timeout-s",
        type=int,
        default=180,
        help="Per reconstructPar command timeout in seconds.",
    )
    parser.add_argument(
        "--foam-timeout-s",
        type=int,
        default=900,
        help="Per section/segment OpenFOAM sampling command timeout in seconds.",
    )
    args = parser.parse_args()
    if args.medium_only and args.fine_only:
        parser.error("--medium-only and --fine-only are mutually exclusive")

    PKG = args.package_dir if args.package_dir.is_absolute() else ROOT / args.package_dir
    LOGS = PKG / "logs"
    OUTPUTS = PKG / "outputs"
    RECON = PKG / "recon"
    SCRIPTS = PKG / "scripts"
    TASK_ID = args.task_id

    for path in (PKG, LOGS, OUTPUTS, RECON, SCRIPTS):
        path.mkdir(parents=True, exist_ok=True)

    if args.medium_only:
        cases = CASES[:1]
    elif args.fine_only:
        cases = CASES[1:]
    else:
        cases = CASES
    results: dict[str, Any] = {
        "generated_at": now(),
        "task_id": TASK_ID,
        "host": subprocess.check_output(["hostname"], text=True).strip(),
        "profile": PROFILE,
        "mesh_stations": rel(MESH_STATIONS),
        "package": rel(PKG),
        "medium_only": args.medium_only,
        "fine_only": args.fine_only,
        "reconstruct_timeout_s": args.reconstruct_timeout_s,
        "foam_timeout_s": args.foam_timeout_s,
        "native_solver_outputs_mutated": False,
        "reconstruction_trials": [],
        "section_temperature_sampling": [],
        "segment_thermal_extraction": [],
        "decision": "",
    }

    if args.fine_only:
        # AGENT-267 established this as the preferred medium method. Fine-only
        # mode intentionally avoids rerunning the medium method matrix.
        chosen = "cwd_controlDict_collated"
        results["chosen_method_basis"] = "AGENT-267 medium smoke selected staged cwd collated reconstruction."
    else:
        medium = CASES[0]
        for method in ("default_case_arg", "cwd_controlDict_collated", "explicit_fileHandler_collated"):
            results["reconstruction_trials"].append(
                reconstruct(medium, method, "(T)", command_timeout_s=args.reconstruct_timeout_s)
            )

        clean_methods = [
            r["method"] for r in results["reconstruction_trials"] if r["level"] == "medium" and r["clean_T"]
        ]
        if not clean_methods:
            results["decision"] = "No clean medium reconstructed-T path found; thermal UA/HTC/Nu remains blocked."
            write_summary(results)
            return 1

        # Prefer the staged-case cwd path because it honors the local collated
        # OptimisationSwitches, including maxThreadFileBufferSize 0. The explicit
        # collated path can reconstruct T-only cleanly but has shown auxiliary
        # boundary-field corruption during full-field reconstruction.
        preferred_methods = ("cwd_controlDict_collated", "default_case_arg", "explicit_fileHandler_collated")
        chosen = next(method for method in preferred_methods if method in clean_methods)
    results["chosen_method"] = chosen

    for case in cases:
        full = reconstruct_split_full(case, chosen, command_timeout_s=args.reconstruct_timeout_s)
        results["reconstruction_trials"].append(full)
        if not full["clean_T"]:
            continue
        section = run_section_temperature_sampling(case, full["stage"], timeout_s=args.foam_timeout_s)
        results["section_temperature_sampling"].append(section)
        if not section["gate_pass"]:
            continue
        segment = run_segment_thermal(case, full["stage"], timeout_s=args.foam_timeout_s)
        results["segment_thermal_extraction"].append(segment)

    full_clean = [r for r in results["reconstruction_trials"] if r.get("full_fields") and r["clean_T"]]
    section_pass = [r for r in results["section_temperature_sampling"] if r["gate_pass"]]
    thermal_pass = [r for r in results["segment_thermal_extraction"] if r["gate_pass"]]
    if len(full_clean) == len(cases) and len(section_pass) == len(cases) and len(thermal_pass) == len(cases):
        results["decision"] = (
            "Repair smoke passed for requested cases: clean reconstructed T, successful temperature section "
            "sampling, and segment thermal extraction completed. Closure admission still requires review gates."
        )
        rc = 0
    else:
        results["decision"] = (
            "Partial repair progress only: at least one clean reconstruction or thermal sampling gate failed. "
            "Thermal UA/HTC/Nu remains blocked for failed levels."
        )
        rc = 2
    write_summary(results)
    print(results["decision"])
    print(f"wrote {rel(PKG / 'summary.json')}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
