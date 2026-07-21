#!/usr/bin/env python3
"""Reconcile claimed freeze-window times against on-disk CFD data (action #6).

WHY THIS EXISTS
---------------
The inspection found that freeze-window / representative-time CSVs reference
retained times (e.g. salt2 -> 5397 s, salt4 -> 8123 s via the *_cont / *_hiq /
*_loq continuation lanes) that DO NOT exist in the staged `processors64/` trees
present in this workspace (salt2_jin reaches 2431 s, salt4_jin 2082 s). That is a
reproducibility hazard: an analysis built on times that cannot be reopened here
can be neither verified nor re-sampled. This tool makes that gap explicit and
machine-checkable so nobody silently trusts unverifiable times.

WHAT IT DOES
------------
For each row of a freeze-window CSV it:
  * parses the claimed `latest_retained_time_s` and `representative_times_s`,
  * maps the case_key to candidate staged case dir(s) and reads the actual
    on-disk `processors64/` time directories,
  * classifies the row as
      - `verifiable_on_disk`     : every representative time is present on disk
      - `partially_verifiable`   : some representative times present
      - `unverifiable_here`      : claimed times exceed / are absent from disk
      - `no_staged_case_found`   : no staged dir resolved for the key
  * reports the max on-disk time vs the claimed latest time.

This is a provenance check, not a correctness judgement: an `unverifiable_here`
lane may be perfectly valid elsewhere; it simply cannot be confirmed from this
workspace, which is itself the finding to record.

Read-only. No OpenFOAM runtime needed.

USAGE
  python tools/analyze/reconcile_freeze_windows.py
  python tools/analyze/reconcile_freeze_windows.py --freeze-csv <path> --search-root <dir>
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
    safe_float,
)

DEFAULT_FREEZE_CSV = (
    WORKSPACE_ROOT
    / "reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint/freeze_case_windows.csv"
)
# Search BOTH the canonical staging tree AND jadyn_runs. The mainline CONTINUATION
# field data lives under jadyn_runs/.../case_stage/..._continuation/ (the original
# tool only searched staging/, which is why it wrongly reported continuation lanes
# as 'unverifiable'). We search both and report which tree satisfied each lane.
DEFAULT_SEARCH_ROOTS = [
    WORKSPACE_ROOT / "staging" / "modern_runs",
    WORKSPACE_ROOT / "jadyn_runs",
]
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_freeze_window_reconcile"
# Tolerance (s) for matching a claimed representative time to an on-disk dir.
MATCH_TOL_S = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--freeze-csv", default=str(DEFAULT_FREEZE_CSV))
    parser.add_argument("--search-root", action="append", default=None,
                        help="Search root for processors64 trees (repeatable). Defaults to staging/ + jadyn_runs/.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def index_staged_cases(search_roots: list[Path]) -> dict[str, list[Path]]:
    """Map each case dir name -> ALL its processors64 paths across the roots.

    Multiple trees can share a case name (e.g. the same continuation case staged
    in several jadyn_runs waves); we keep them all and let the caller pick the
    best (max-time) one, so we never silently hide a more-advanced run.
    """
    index: dict[str, list[Path]] = {}
    for root in search_roots:
        if not root.exists():
            continue
        for proc in root.rglob("processors64"):
            if proc.is_dir():
                index.setdefault(proc.parent.name, []).append(proc)
    return index


def on_disk_times(proc_dir: Path) -> list[float]:
    times: list[float] = []
    for child in proc_dir.iterdir():
        if child.is_dir():
            val = safe_float(child.name)
            if val is not None:
                times.append(val)
    return sorted(times)


def candidate_case_names(case_key: str) -> list[str]:
    """Map a freeze case_key (e.g. 'salt2_cont', 'salt4_hiq', 'salt1_jin') to the
    staged case dir names it could correspond to.

    The staged trees are named `viscosity_screening_salt_test_<n>_<jin|kirst>_
    coarse_mesh` and `val_water_test_<n>_coarse_mesh_laminar`. The freeze lanes
    (cont/hiq/loq) are continuation variants of the same physical case; the only
    staged representative we have is the *_jin (salt) / val (water) tree, so we
    point there and let the time comparison reveal the mismatch.
    """
    key = case_key.lower()
    salt = re.search(r"salt\s*_?(\d+)", key)
    water = re.search(r"water\s*_?(\d+)", key)
    names: list[str] = []
    if salt:
        n = salt.group(1)
        # continuation variants FIRST (mainline per the run-classification rule),
        # then the original parent-warmup names.
        names += [
            f"viscosity_screening_salt_test_{n}_jin_coarse_mesh_continuation",
            f"viscosity_screening_salt_test_{n}_kirst_coarse_mesh_continuation",
            f"viscosity_screening_salt_test_{n}_jin_coarse_mesh",
            f"viscosity_screening_salt_test_{n}_kirst_coarse_mesh",
        ]
    if water:
        n = water.group(1)
        names += [
            f"val_water_test_{n}_coarse_mesh_laminar_continuation",
            f"val_water_test_{n}_coarse_mesh_laminar",
        ]
    return names


def parse_representative_times(value: str) -> list[float]:
    out: list[float] = []
    for token in (value or "").split("|"):
        v = safe_float(token.strip())
        if v is not None:
            out.append(v)
    return out


def reconcile_row(row: dict[str, str], staged_index: dict[str, Path]) -> dict[str, Any]:
    case_key = row.get("case_key", "")
    claimed_latest = safe_float(row.get("latest_retained_time_s"))
    rep_times = parse_representative_times(row.get("representative_times_s", ""))
    candidates = candidate_case_names(case_key)
    # Across all candidate names and all trees indexed for each, pick the tree
    # with the MAX on-disk time (the most-advanced run for this case).
    best_name = None
    best_path = None
    best_times: list[float] = []
    for name in candidates:
        for proc in staged_index.get(name, []):
            times = on_disk_times(proc)
            if times and (not best_times or max(times) > max(best_times)):
                best_name, best_path, best_times = name, proc, times

    result: dict[str, Any] = {
        "case_key": case_key,
        "lane": row.get("lane", ""),
        "family": row.get("family", ""),
        "claimed_latest_time_s": claimed_latest,
        "claimed_representative_count": len(rep_times),
        "candidate_case_names": candidates,
        "resolved_staged_case": best_name,
        "resolved_tree": relative_to_workspace(best_path.parent) if best_path else None,
    }
    if best_path is None:
        result["classification"] = "no_staged_case_found"
        return result

    disk_times = best_times
    max_disk = max(disk_times) if disk_times else None
    result["on_disk_max_time_s"] = max_disk
    result["on_disk_time_count"] = len(disk_times)

    def present(t: float) -> bool:
        return any(abs(t - d) <= MATCH_TOL_S for d in disk_times)

    matched = [t for t in rep_times if present(t)]
    result["representative_times_present_on_disk"] = len(matched)
    result["representative_times_total"] = len(rep_times)

    if rep_times and len(matched) == len(rep_times):
        result["classification"] = "verifiable_on_disk"
    elif matched:
        result["classification"] = "partially_verifiable"
    else:
        result["classification"] = "unverifiable_here"
    if claimed_latest is not None and max_disk is not None and claimed_latest > max_disk + MATCH_TOL_S:
        result["claimed_exceeds_disk_by_s"] = claimed_latest - max_disk
    return result


def main() -> int:
    args = parse_args()
    freeze_csv = Path(args.freeze_csv)
    search_roots = [Path(r) for r in args.search_root] if args.search_root else list(DEFAULT_SEARCH_ROOTS)
    staged_index = index_staged_cases(search_roots)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    rows: list[dict[str, str]] = []
    if freeze_csv.exists():
        with freeze_csv.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

    results = [reconcile_row(row, staged_index) for row in rows]
    summary: dict[str, int] = {}
    for res in results:
        summary[res["classification"]] = summary.get(res["classification"], 0) + 1

    payload = {
        "generated_at": iso_timestamp(),
        "freeze_csv": relative_to_workspace(freeze_csv),
        "search_roots": [relative_to_workspace(r) for r in search_roots],
        "match_tolerance_s": MATCH_TOL_S,
        "staged_cases_indexed": sorted(staged_index.keys()),
        "classification_summary": summary,
        "rows": results,
    }
    json_dump(output_dir / "freeze_window_reconcile.json", payload)
    if results:
        keys = sorted({k for r in results for k in r.keys()})
        norm = [{k: r.get(k, "") for k in keys} for r in results]
        csv_dump(output_dir / "freeze_window_reconcile.csv", keys, norm)

    print(f"# Freeze-window reconciliation  ({iso_timestamp()})")
    print(f"# freeze_csv: {relative_to_workspace(freeze_csv)}")
    print(f"# summary: {summary}")
    for res in results:
        line = (
            f"   {res['case_key']:12s} {res['classification']:20s} "
            f"claimed_latest={res.get('claimed_latest_time_s')} "
            f"disk_max={res.get('on_disk_max_time_s')} "
            f"rep_on_disk={res.get('representative_times_present_on_disk','-')}/{res.get('representative_times_total','-')}"
        )
        if res.get("claimed_exceeds_disk_by_s"):
            line += f"  EXCEEDS_DISK_BY={res['claimed_exceeds_disk_by_s']:.0f}s"
        if res.get("resolved_tree"):
            line += f"\n        tree={res['resolved_tree']}"
        print(line)
    print(f"\nWrote {relative_to_workspace(output_dir / 'freeze_window_reconcile.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
