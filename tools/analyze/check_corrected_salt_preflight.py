#!/usr/bin/env python3
"""Read-only preflight audit for corrected Salt Q perturbation cases.

The corrected Salt campaign is usable for closure fitting only if the intended
thermal perturbation is present in both the visible root field and the collated
restart field read by ``foamRun``. This checker validates that contract without
modifying case directories.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    ROOT
    / "jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv"
)

HEATER_PATCHES = [
    "pipeleg_lower_04_straight",
    "pipeleg_lower_05_straight",
    "pipeleg_lower_06_straight",
]
COOLER_PATCHES = [
    "pipeleg_upper_04_reducer",
    "pipeleg_upper_05_cooler",
    "pipeleg_upper_06_reducer",
]
TARGET_PATCHES = HEATER_PATCHES + COOLER_PATCHES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--case-key", action="append", default=[], help="Limit to a case key; repeatable.")
    parser.add_argument("--audit-out", required=True, help="CSV audit output path.")
    parser.add_argument("--json-out", help="Optional JSON audit output path.")
    parser.add_argument("--expected-processors", type=int, default=64)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--rtol", type=float, default=1e-9)
    parser.add_argument(
        "--check-runtime-controls",
        action="store_true",
        help="Validate controlDict restart controls in addition to Q patch fields.",
    )
    parser.add_argument(
        "--min-time-precision",
        type=int,
        default=12,
        help="Minimum safe OpenFOAM timePrecision for large-time adaptive continuations.",
    )
    parser.add_argument(
        "--max-time-precision",
        type=int,
        help="Optional maximum OpenFOAM timePrecision; useful for general-format restart repairs.",
    )
    parser.add_argument(
        "--required-time-format",
        default="fixed",
        help="Required OpenFOAM timeFormat for checked adaptive continuations.",
    )
    parser.add_argument(
        "--restart-time",
        action="append",
        default=[],
        metavar="CASE_KEY=TIME",
        help="Expected restart time for a case key; repeatable.",
    )
    parser.add_argument(
        "--allow-missing-processors",
        action="store_true",
        help="Do not fail cases that lack processors64/latest/T. Root/config checks still run.",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def expected_patch_values(row: dict[str, str]) -> dict[str, float]:
    heater_patch_q = float(row["target_heater_power_W"]) / 3.0
    return {
        **{patch: heater_patch_q for patch in HEATER_PATCHES},
        "pipeleg_upper_04_reducer": float(row["target_cooler_q04_W"]),
        "pipeleg_upper_05_cooler": float(row["target_cooler_q05_W"]),
        "pipeleg_upper_06_reducer": float(row["target_cooler_q06_W"]),
    }


def close_enough(a: float, b: float, *, atol: float, rtol: float) -> bool:
    return math.isclose(a, b, abs_tol=atol, rel_tol=rtol)


def latest_time(processors64: Path) -> str | None:
    if not processors64.is_dir():
        return None
    times = []
    for child in processors64.iterdir():
        if not child.is_dir():
            continue
        try:
            times.append((float(child.name), child.name))
        except ValueError:
            continue
    if not times:
        return None
    return max(times, key=lambda item: item[0])[1]


def parse_restart_overrides(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"--restart-time must be CASE_KEY=TIME, got {value!r}")
        key, time_name = value.split("=", 1)
        if not key or not time_name:
            raise ValueError(f"--restart-time must be CASE_KEY=TIME, got {value!r}")
        out[key] = time_name
    return out


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.lower()
    if lowered in {"true", "yes", "on", "1"}:
        return True
    if lowered in {"false", "no", "off", "0"}:
        return False
    return None


def parse_control_dict(path: Path) -> dict[str, str | float | int | bool | None]:
    if not path.exists():
        return {
            "exists": False,
            "startFrom": None,
            "startTime": None,
            "endTime": None,
            "adjustTimeStep": None,
            "timeFormat": None,
            "timePrecision": None,
        }
    text = path.read_text(encoding="utf-8", errors="ignore")

    def token(name: str) -> str | None:
        match = re.search(rf"(?m)^\s*{re.escape(name)}\s+([^;]+)\s*;", text)
        return match.group(1).strip() if match else None

    def as_float(raw: str | None) -> float | None:
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def as_int(raw: str | None) -> int | None:
        if raw is None:
            return None
        try:
            return int(float(raw))
        except ValueError:
            return None

    adjust_raw = token("adjustTimeStep")
    return {
        "exists": True,
        "startFrom": token("startFrom"),
        "startTime": as_float(token("startTime")),
        "endTime": as_float(token("endTime")),
        "adjustTimeStep": parse_bool(adjust_raw),
        "timeFormat": token("timeFormat"),
        "timePrecision": as_int(token("timePrecision")),
    }


def runtime_control_audit(
    case_dir: Path,
    case_key: str,
    restart_time: str | None,
    args: argparse.Namespace,
) -> tuple[bool, dict[str, Any], list[str]]:
    control = parse_control_dict(case_dir / "system/controlDict")
    mismatches: list[str] = []
    notes: list[str] = []
    restart_overrides = getattr(args, "restart_times", {})
    expected_restart = restart_overrides.get(case_key)

    if not control["exists"]:
        mismatches.append("missing system/controlDict")
        return False, control, mismatches
    if restart_time is None:
        mismatches.append("missing restart time")
        return False, control, mismatches

    try:
        restart_float = float(restart_time)
    except ValueError:
        mismatches.append(f"restart time is not numeric: {restart_time}")
        return False, control, mismatches

    time_precision = control.get("timePrecision")
    if time_precision is None:
        mismatches.append("missing timePrecision")
    elif int(time_precision) < args.min_time_precision:
        mismatches.append(f"timePrecision {time_precision} < {args.min_time_precision}")
    elif args.max_time_precision is not None and int(time_precision) > args.max_time_precision:
        mismatches.append(f"timePrecision {time_precision} > {args.max_time_precision}")

    if control.get("endTime") is None:
        mismatches.append("missing endTime")
    elif float(control["endTime"]) <= restart_float:
        mismatches.append(f"endTime {control['endTime']} <= restart {restart_time}")

    if expected_restart:
        if expected_restart != restart_time:
            mismatches.append(f"selected restart {restart_time} != expected {expected_restart}")
        if control.get("startFrom") == "startTime":
            if control.get("startTime") is None:
                mismatches.append("missing startTime")
            elif not close_enough(float(control["startTime"]), restart_float, atol=args.atol, rtol=args.rtol):
                mismatches.append(f"startTime {control['startTime']:.12g} != restart {restart_time}")
        else:
            mismatches.append(f"startFrom {control.get('startFrom')} != startTime for explicit restart")
    elif control.get("startFrom") != "latestTime":
        mismatches.append(f"startFrom {control.get('startFrom')} != latestTime")

    if control.get("adjustTimeStep") is True:
        if control.get("timeFormat") != args.required_time_format:
            mismatches.append(
                f"timeFormat {control.get('timeFormat')} != {args.required_time_format} "
                "for adaptive continuation"
            )
        else:
            notes.append(
                f"adaptive timestep uses {args.required_time_format} time format with "
                f"timePrecision >= {args.min_time_precision}"
            )

    return not mismatches, control, mismatches + notes


def parse_case_config(path: Path) -> dict[str, float | None]:
    if not path.exists():
        return {"operating_point_heater_power_W": None, "bc_params_heater_Q": None}
    text = path.read_text(encoding="utf-8", errors="ignore")
    heater_power = None
    match = re.search(r"(?m)^\s*heater_power_W:\s*([-+0-9.eE]+)\s*$", text)
    if match:
        heater_power = float(match.group(1))

    heater_q = None
    match = re.search(r"(?ms)^\s*heater:\s*\n(?P<body>(?:\s{4,}.+\n)+)", text)
    if match:
        q_match = re.search(r"(?m)^\s*Q:\s*([-+0-9.eE]+)\s*$", match.group("body"))
        if q_match:
            heater_q = float(q_match.group(1))
    return {"operating_point_heater_power_W": heater_power, "bc_params_heater_Q": heater_q}


def q_values_from_text(text: str, patches: list[str]) -> dict[str, list[float]]:
    lines = text.splitlines()
    wanted = set(patches)
    out: dict[str, list[float]] = {patch: [] for patch in patches}
    i = 0
    while i < len(lines):
        patch = lines[i].strip().strip('"')
        if patch not in wanted:
            i += 1
            continue
        depth = 0
        j = i
        while j < len(lines):
            depth += lines[j].count("{") - lines[j].count("}")
            stripped = lines[j].strip()
            q_match = re.match(r"^Q\s+constant\s+([-+0-9.eE]+)\s*;", stripped)
            if q_match:
                out[patch].append(float(q_match.group(1)))
                break
            if stripped == "Q":
                for k in range(j + 1, min(j + 20, len(lines))):
                    value_match = re.match(r"^value\s+([-+0-9.eE]+)\s*;", lines[k].strip())
                    if value_match:
                        out[patch].append(float(value_match.group(1)))
                        break
                break
            if j > i and depth <= 0:
                break
            j += 1
        i = max(j + 1, i + 1)
    return out


def read_field(path: Path) -> tuple[dict[str, list[float]], dict[str, Any]]:
    raw = path.read_bytes()
    if b"class       decomposedBlockData" not in raw[:4096]:
        text = raw.decode("utf-8")
        return q_values_from_text(text, TARGET_PATCHES), {
            "field_format": "text",
            "processor_blocks": 0,
            "frame_error_count": 0,
        }
    values: dict[str, list[float]] = {patch: [] for patch in TARGET_PATCHES}
    frame_errors: list[str] = []
    block_count = 0
    header = re.compile(rb"// Processor(\d+)\n\n(\d+)\n\(")
    for match in header.finditer(raw):
        block_count += 1
        proc = match.group(1).decode("ascii", errors="replace")
        byte_count = int(match.group(2))
        block_start = match.end()
        block_end = block_start + byte_count
        if block_end >= len(raw) or raw[block_end:block_end + 1] != b")":
            frame_errors.append(f"processor {proc}: byte-count frame mismatch")
            continue
        text = raw[block_start:block_end].decode("latin-1")
        block_values = q_values_from_text(text, TARGET_PATCHES)
        for patch, patch_values in block_values.items():
            values[patch].extend(patch_values)
    if block_count == 0:
        frame_errors.append("no processor blocks found")
    return values, {
        "field_format": "decomposedBlockData",
        "processor_blocks": block_count,
        "frame_error_count": len(frame_errors),
        "frame_errors": frame_errors,
    }


def summarize_values(
    values: dict[str, list[float]],
    expected: dict[str, float],
    expected_count: int,
    *,
    atol: float,
    rtol: float,
) -> tuple[bool, dict[str, Any]]:
    counts = {patch: len(values.get(patch, [])) for patch in TARGET_PATCHES}
    mismatches: list[str] = []
    extrema: dict[str, dict[str, float | None]] = {}
    for patch in TARGET_PATCHES:
        vals = values.get(patch, [])
        if len(vals) != expected_count:
            mismatches.append(f"{patch}: count {len(vals)} != {expected_count}")
        if vals:
            extrema[patch] = {"min": min(vals), "max": max(vals), "expected": expected[patch]}
            if any(not close_enough(value, expected[patch], atol=atol, rtol=rtol) for value in vals):
                mismatches.append(
                    f"{patch}: value range {min(vals):.12g}..{max(vals):.12g} != {expected[patch]:.12g}"
                )
        else:
            extrema[patch] = {"min": None, "max": None, "expected": expected[patch]}
    return not mismatches, {"counts": counts, "extrema": extrema, "mismatches": mismatches}


def audit_case(row: dict[str, str], args: argparse.Namespace) -> dict[str, Any]:
    case_dir = Path(row["case_dir"])
    expected = expected_patch_values(row)
    notes: list[str] = []

    config_vals = parse_case_config(case_dir / "case_config.yaml")
    target_heater = float(row["target_heater_power_W"])
    config_mismatches = []
    for key, value in config_vals.items():
        if value is None:
            config_mismatches.append(f"{key}: missing")
        elif not close_enough(float(value), target_heater, atol=args.atol, rtol=args.rtol):
            config_mismatches.append(f"{key}: {value:.12g} != {target_heater:.12g}")
    config_ok = not config_mismatches

    root_ok = False
    root_summary: dict[str, Any] = {"mismatches": ["missing 0/T"]}
    root_path = case_dir / "0/T"
    if root_path.exists():
        root_values, root_meta = read_field(root_path)
        root_ok, root_summary = summarize_values(
            root_values, expected, 1, atol=args.atol, rtol=args.rtol
        )
        root_summary.update(root_meta)

    restart_overrides = getattr(args, "restart_times", {})
    restart_time = restart_overrides.get(row["case_key"]) or latest_time(case_dir / "processors64")
    processor_ok = False
    processor_summary: dict[str, Any] = {"mismatches": ["missing processors64/latest/T"]}
    if restart_time is not None:
        proc_path = case_dir / "processors64" / restart_time / "T"
        if proc_path.exists():
            proc_values, proc_meta = read_field(proc_path)
            frames_ok = (
                proc_meta.get("field_format") == "decomposedBlockData"
                and proc_meta.get("processor_blocks") == args.expected_processors
                and proc_meta.get("frame_error_count") == 0
            )
            processor_ok, processor_summary = summarize_values(
                proc_values, expected, args.expected_processors, atol=args.atol, rtol=args.rtol
            )
            processor_summary.update(proc_meta)
            if not frames_ok:
                processor_ok = False
                notes.append(
                    "processor frame check failed: "
                    f"format={proc_meta.get('field_format')} blocks={proc_meta.get('processor_blocks')} "
                    f"frame_errors={proc_meta.get('frame_error_count')}"
                )
        else:
            notes.append(f"missing restart T field at {rel(proc_path)}")
    elif args.allow_missing_processors:
        processor_ok = True
        notes.append("processors64 missing; allowed by --allow-missing-processors")

    runtime_ok = True
    runtime_summary: dict[str, Any] = {"mismatches": []}
    if getattr(args, "check_runtime_controls", False):
        runtime_ok, runtime_controls, runtime_notes = runtime_control_audit(
            case_dir, row["case_key"], restart_time, args
        )
        runtime_summary = {
            "controls": runtime_controls,
            "mismatches": [note for note in runtime_notes if not note.startswith("adaptive timestep uses")],
            "notes": [note for note in runtime_notes if note.startswith("adaptive timestep uses")],
        }

    overall_ok = config_ok and root_ok and processor_ok and runtime_ok
    return {
        "case_key": row["case_key"],
        "case_dir": rel(case_dir),
        "q_ratio": row.get("q_ratio", ""),
        "target_heater_power_W": target_heater,
        "target_heater_patch_Q_W": target_heater / 3.0,
        "restart_time_s": restart_time or "",
        "config_ok": config_ok,
        "root_field_ok": root_ok,
        "processor_field_ok": processor_ok,
        "runtime_controls_ok": runtime_ok,
        "overall_ok": overall_ok,
        "config_values": config_vals,
        "config_mismatches": config_mismatches,
        "root_summary": root_summary,
        "processor_summary": processor_summary,
        "runtime_summary": runtime_summary,
        "notes": notes,
    }


def flatten(row: dict[str, Any]) -> dict[str, str]:
    return {
        "case_key": str(row["case_key"]),
        "case_dir": str(row["case_dir"]),
        "q_ratio": str(row["q_ratio"]),
        "target_heater_power_W": f"{float(row['target_heater_power_W']):.12g}",
        "target_heater_patch_Q_W": f"{float(row['target_heater_patch_Q_W']):.12g}",
        "restart_time_s": str(row["restart_time_s"]),
        "config_ok": str(row["config_ok"]),
        "root_field_ok": str(row["root_field_ok"]),
        "processor_field_ok": str(row["processor_field_ok"]),
        "runtime_controls_ok": str(row["runtime_controls_ok"]),
        "overall_ok": str(row["overall_ok"]),
        "config_mismatches": "; ".join(row["config_mismatches"]),
        "root_mismatches": "; ".join(row["root_summary"].get("mismatches", [])),
        "processor_mismatches": "; ".join(row["processor_summary"].get("mismatches", [])),
        "runtime_mismatches": "; ".join(row["runtime_summary"].get("mismatches", [])),
        "processor_blocks": str(row["processor_summary"].get("processor_blocks", "")),
        "processor_frame_error_count": str(row["processor_summary"].get("frame_error_count", "")),
        "notes": "; ".join(row["notes"] + row["runtime_summary"].get("notes", [])),
    }


def main() -> int:
    args = parse_args()
    try:
        args.restart_times = parse_restart_overrides(args.restart_time)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    rows = read_manifest(Path(args.manifest))
    wanted = set(args.case_key)
    if wanted:
        rows = [row for row in rows if row["case_key"] in wanted]
    audits = [audit_case(row, args) for row in rows]

    out = Path(args.audit_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    flat_rows = [flatten(row) for row in audits]
    fields = list(flat_rows[0].keys()) if flat_rows else ["case_key"]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flat_rows)

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({"cases": audits}, indent=2), encoding="utf-8")

    bad = [row for row in audits if not row["overall_ok"]]
    print(f"Audited {len(audits)} corrected Salt cases; failures={len(bad)}")
    for row in bad:
        print(f"FAIL {row['case_key']}: {row['notes']}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
