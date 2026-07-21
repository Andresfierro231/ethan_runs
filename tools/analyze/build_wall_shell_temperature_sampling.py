#!/usr/bin/env python3
"""Derive patch-internal wall-shell temperature proxies from reconstructed OF13 cases.

The proxy used here is the owner-cell temperature behind each boundary face:
``T_wall_shell_K = mean(T_internal[owner[boundary_face]])``.  This is not a new
OpenFOAM solve and it does not modify native solver outputs.
"""

from __future__ import annotations

import csv
import json
import math
import platform
import re
import socket
import subprocess
from array import array
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-PRED-WALL-SHELL-SAMPLE"
OUT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling"
PATCH_TABLE = (
    ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
)

CASES = {
    "salt_2": {
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "recon_dir": ROOT / "tmp/2026-06-30_claude_action_items/recon_salt2_of13",
        "time_s": "7915",
    },
    "salt_3": {
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "recon_dir": ROOT / "tmp/2026-06-30_claude_action_items/recon_salt3_of13",
        "time_s": "7618",
    },
    "salt_4": {
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "recon_dir": ROOT / "tmp/2026-06-30_claude_action_items/recon_salt4_of13",
        "time_s": "10000",
    },
}

PATCH_COLUMNS = [
    "source_id",
    "case_id",
    "patch_name",
    "role",
    "one_d_segment",
    "bc_type",
    "area_m2",
    "start_face",
    "n_boundary_faces",
    "n_owner_samples",
    "n_unique_owner_cells",
    "T_wall_shell_K",
    "T_wall_shell_min_K",
    "T_wall_shell_max_K",
    "T_wall_shell_std_K",
    "proxy_definition",
    "support_status",
    "recon_case_dir",
    "time_s",
    "owner_path",
    "boundary_path",
    "T_field_path",
]

SEGMENT_COLUMNS = [
    "source_id",
    "case_id",
    "one_d_segment",
    "role",
    "patch_count",
    "area_m2",
    "T_wall_shell_K",
    "T_wall_shell_min_K",
    "T_wall_shell_max_K",
    "area_weighting",
    "support_status",
    "proxy_definition",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fnum(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if text in {"", "nan", "NaN", "None"}:
        return default
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.9f}".rstrip("0").rstrip(".")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def parse_internal_scalar_field(path: Path) -> array:
    text = path.read_text(encoding="utf-8", errors="ignore")
    marker = "internalField"
    idx = text.find(marker)
    if idx < 0:
        raise ValueError(f"internalField not found in {path}")
    match = re.search(r"nonuniform\s+List<scalar>\s+(\d+)\s*\(", text[idx:])
    if not match:
        uniform = re.search(r"uniform\s+([-+0-9.eE]+)\s*;", text[idx:])
        if uniform:
            raise ValueError(f"uniform internal field is unsupported for owner-cell sampling: {path}")
        raise ValueError(f"nonuniform scalar internalField not found in {path}")
    start = idx + match.end()
    end = text.find("\n)\n", start)
    if end < 0:
        raise ValueError(f"internalField closing delimiter not found in {path}")
    values = array("d")
    values.fromlist([float(tok) for tok in text[start:end].split()])
    expected = int(match.group(1))
    if len(values) != expected:
        raise ValueError(f"{path}: expected {expected} T values, parsed {len(values)}")
    return values


def parse_label_list(path: Path) -> array:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"\n\s*(\d+)\s*\n\s*\(", text)
    if not match:
        raise ValueError(f"OpenFOAM label list not found in {path}")
    start = match.end()
    end = text.find("\n)\n", start)
    if end < 0:
        raise ValueError(f"label list closing delimiter not found in {path}")
    values = array("I")
    values.fromlist([int(tok) for tok in text[start:end].split()])
    expected = int(match.group(1))
    if len(values) != expected:
        raise ValueError(f"{path}: expected {expected} labels, parsed {len(values)}")
    return values


def parse_boundary(path: Path) -> dict[str, dict[str, int]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, dict[str, int]] = {}
    pattern = re.compile(
        r"\n\s*([A-Za-z0-9_.*|()]+)\s*\n\s*\{(?P<body>.*?)\n\s*\}",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        body = match.group("body")
        nf = re.search(r"\bnFaces\s+(\d+)\s*;", body)
        sf = re.search(r"\bstartFace\s+(\d+)\s*;", body)
        if nf and sf:
            out[match.group(1)] = {"nFaces": int(nf.group(1)), "startFace": int(sf.group(1))}
    return out


def stats(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {
            "mean": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "std": float("nan"),
        }
    mean = sum(values) / n
    var = sum((value - mean) ** 2 for value in values) / n
    return {"mean": mean, "min": min(values), "max": max(values), "std": math.sqrt(var)}


def eligible_patch_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        if row.get("bc_type") != "rcExternalTemperature":
            continue
        if row.get("role") == "zero_gradient_ncc_connector":
            continue
        if not row.get("one_d_segment"):
            continue
        out.append(row)
    return out


def sample_case(case_id: str, patch_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    case = CASES[case_id]
    recon_dir = case["recon_dir"]
    time_s = case["time_s"]
    owner_path = recon_dir / "constant/polyMesh/owner"
    boundary_path = recon_dir / "constant/polyMesh/boundary"
    t_path = recon_dir / time_s / "T"

    owner = parse_label_list(owner_path)
    temps = parse_internal_scalar_field(t_path)
    boundary = parse_boundary(boundary_path)

    rows: list[dict[str, Any]] = []
    for patch in patch_rows:
        patch_name = patch["patch_name"]
        binfo = boundary.get(patch_name)
        base = {
            "source_id": patch["source_id"],
            "case_id": patch["case_id"],
            "patch_name": patch_name,
            "role": patch.get("role", ""),
            "one_d_segment": patch.get("one_d_segment", ""),
            "bc_type": patch.get("bc_type", ""),
            "area_m2": patch.get("area_m2", ""),
            "proxy_definition": "boundary_face_owner_cell_temperature_mean",
            "recon_case_dir": rel(recon_dir),
            "time_s": time_s,
            "owner_path": rel(owner_path),
            "boundary_path": rel(boundary_path),
            "T_field_path": rel(t_path),
        }
        if binfo is None:
            rows.append({**base, "support_status": "blocked_patch_missing_from_boundary"})
            continue
        start = binfo["startFace"]
        n_faces = binfo["nFaces"]
        if start + n_faces > len(owner):
            rows.append(
                {
                    **base,
                    "start_face": start,
                    "n_boundary_faces": n_faces,
                    "support_status": "blocked_boundary_face_range_exceeds_owner_list",
                }
            )
            continue
        samples = [temps[owner[face_i]] for face_i in range(start, start + n_faces)]
        row_stats = stats(samples)
        rows.append(
            {
                **base,
                "start_face": start,
                "n_boundary_faces": n_faces,
                "n_owner_samples": len(samples),
                "n_unique_owner_cells": len(set(owner[face_i] for face_i in range(start, start + n_faces))),
                "T_wall_shell_K": row_stats["mean"],
                "T_wall_shell_min_K": row_stats["min"],
                "T_wall_shell_max_K": row_stats["max"],
                "T_wall_shell_std_K": row_stats["std"],
                "support_status": "ok_patch_internal_owner_cell_proxy",
            }
        )
    return rows


def reduce_segments(patch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in patch_rows:
        grouped[(row["source_id"], row["case_id"], row["one_d_segment"], row["role"])].append(row)
    out: list[dict[str, Any]] = []
    for (source_id, case_id, segment, role), rows in sorted(grouped.items()):
        ok = [row for row in rows if row.get("support_status") == "ok_patch_internal_owner_cell_proxy"]
        area_total = sum(fnum(row.get("area_m2"), 0.0) or 0.0 for row in ok)
        if area_total > 0:
            mean = sum((fnum(row.get("area_m2"), 0.0) or 0.0) * (fnum(row.get("T_wall_shell_K"), 0.0) or 0.0) for row in ok) / area_total
            tmins = [fnum(row.get("T_wall_shell_min_K")) for row in ok]
            tmaxs = [fnum(row.get("T_wall_shell_max_K")) for row in ok]
            status = "ok_area_weighted_patch_internal_owner_cell_proxy"
        else:
            mean = None
            tmins = []
            tmaxs = []
            status = "blocked_no_supported_patch_shell_samples"
        out.append(
            {
                "source_id": source_id,
                "case_id": case_id,
                "one_d_segment": segment,
                "role": role,
                "patch_count": len(rows),
                "area_m2": area_total if area_total > 0 else "",
                "T_wall_shell_K": mean,
                "T_wall_shell_min_K": min(t for t in tmins if t is not None) if any(t is not None for t in tmins) else None,
                "T_wall_shell_max_K": max(t for t in tmaxs if t is not None) if any(t is not None for t in tmaxs) else None,
                "area_weighting": "AGENT-263_patch_area_m2",
                "support_status": status,
                "proxy_definition": "boundary_face_owner_cell_temperature_mean_area_weighted_by_patch",
            }
        )
    return out


def git_rev() -> str:
    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""# Wall-Shell Temperature Sampling

Generated: `{summary['generated_at']}`
Task: `{TASK_ID}`

## Purpose

This package fills the main TODO-PRED-WALL-LAYER blocker by deriving a local
near-wall temperature proxy from reconstructed OpenFOAM 13 cases. The proxy is
not a new solver result. It is the internal owner-cell temperature immediately
behind each boundary face on an `rcExternalTemperature` patch.

## Proxy Definition

`T_wall_shell_K = mean(T_internal[owner[boundary_face]])`

Patch rows report boundary face count, owner sample count, unique owner-cell
count, min/max/std, and exact reconstructed field/mesh paths. Segment rows are
area-weighted with AGENT-263 patch areas. Treat this as a first-cell
patch-internal shell proxy, not as an independent wall-function or y-plus
resolved thermal profile.

## Outputs

- `patch_wall_shell_temperatures.csv`
- `segment_wall_shell_temperatures.csv`
- `run_metadata.json`

## Key Counts

- Patch rows: `{summary['patch_rows']}`
- Segment rows: `{summary['segment_rows']}`
- Blocked patch rows: `{summary['blocked_patch_rows']}`

## Use In Parity

These segment rows are intended to be consumed by
`tools/analyze/build_wall_layer_drive_mapping.py` so E1 wall-shell replay can be
computed. E2 blend fitting remains diagnostic unless a later package admits a
family-level beta with validation separation.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    patch_rows_all = eligible_patch_rows(read_csv(PATCH_TABLE))
    patch_rows: list[dict[str, Any]] = []
    for case_id in CASES:
        case_patch_rows = [row for row in patch_rows_all if row["case_id"] == case_id]
        patch_rows.extend(sample_case(case_id, case_patch_rows))
    segment_rows = reduce_segments(patch_rows)

    write_csv(OUT / "patch_wall_shell_temperatures.csv", patch_rows, PATCH_COLUMNS)
    write_csv(OUT / "segment_wall_shell_temperatures.csv", segment_rows, SEGMENT_COLUMNS)

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "git_rev": git_rev(),
        "source_paths": {
            "patch_table": rel(PATCH_TABLE),
            "reconstructed_cases": {case_id: rel(case["recon_dir"]) for case_id, case in CASES.items()},
        },
        "patch_rows": len(patch_rows),
        "segment_rows": len(segment_rows),
        "blocked_patch_rows": sum(1 for row in patch_rows if str(row.get("support_status", "")).startswith("blocked")),
        "proxy_definition": "boundary_face_owner_cell_temperature_mean",
        "native_solver_outputs_modified": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "run_metadata.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_readme(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
