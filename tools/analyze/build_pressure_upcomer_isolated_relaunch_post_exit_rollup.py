#!/usr/bin/env python3
"""Roll up post-exit pressure/upcomer isolated relaunch parse status."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-PRESSURE-UPCOMER-ISOLATED-RELAUNCH-POST-EXIT-ROLLUP"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_isolated_relaunch_post_exit_rollup"
RELAUNCH = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_isolated_relaunch_submission_package"
PARSED_ROOT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/parsed"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-PRESSURE-UPCOMER-ISOLATED-RELAUNCH-POST-EXIT-ROLLUP.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/pressure-upcomer-isolated-relaunch-post-exit-rollup.md"
IMPORT = ROOT / "imports/2026-07-20_pressure_upcomer_isolated_relaunch_post_exit_rollup.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_sources() -> None:
    required = [RELAUNCH / "post_exit_parse_rollup_contract.csv", RELAUNCH / "summary.json"]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing pressure/upcomer post-exit rollup sources: " + "; ".join(missing))


def safe_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def classify_parsed_rows(rows: list[dict[str, str]]) -> tuple[str, str]:
    if not rows:
        return "failed_relaunch", "missing_parse_rows"
    for row in rows:
        if row.get("metric_status") == "incomplete" or row.get("admission_status", "").startswith("blocked"):
            return "blocked_missing_field", row.get("quality_flags", "incomplete_or_blocked")
        if row.get("quality_flags", "") not in {"", "none"}:
            return "blocked_missing_field", row.get("quality_flags", "")
        raf = safe_float(row.get("reverse_area_fraction", ""))
        rmf = safe_float(row.get("reverse_mass_fraction", ""))
        if raf is not None and raf >= 0.01:
            return "diagnostic_only_recirculating", "reverse_area_fraction_ge_0.01"
        if rmf is not None and rmf >= 0.01:
            return "diagnostic_only_recirculating", "reverse_mass_fraction_ge_0.01"
        required = ("sampled_plane_file", "sampled_wall_file", "bulk_T_K", "wall_T_K", "wallHeatFlux_W_m2", "Re", "Pr")
        missing = [field for field in required if not row.get(field, "")]
        if missing:
            return "blocked_missing_field", "missing_" + ";missing_".join(missing)
    return "admission_grade_candidate", "all_required_gates_passed"


def build_isolated_relaunch_parse_inventory() -> list[dict[str, Any]]:
    rows = []
    for contract in read_csv(RELAUNCH / "post_exit_parse_rollup_contract.csv"):
        path = ROOT / contract["expected_parsed_csv"]
        parsed = read_csv(path) if path.exists() else []
        classification, reason = classify_parsed_rows(parsed)
        rows.append(
            {
                "case_key": contract["case_key"],
                "parsed_csv": contract["expected_parsed_csv"],
                "exists": "yes" if path.exists() else "no",
                "row_count": len(parsed),
                "classification": classification,
                "reason": reason,
            }
        )
    return rows


def build_pressure_upcomer_admission_rollup(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in inventory:
        rows.append(
            {
                "case_key": item["case_key"],
                "parse_classification": item["classification"],
                "admission_status": "candidate_pending_final_review" if item["classification"] == "admission_grade_candidate" else item["classification"],
                "fit_candidate_now": "false",
                "reason": item["reason"],
            }
        )
    return rows


def build_fit_release_decision(rollup: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [row for row in rollup if row["admission_status"] == "candidate_pending_final_review"]
    release = bool(candidates) and len(candidates) == len(rollup)
    return [
        {
            "decision_id": "pressure_upcomer_fit_release_after_isolated_relaunch",
            "decision": "fit_release_admitted" if release else "blocked_no_fit_release",
            "candidate_rows": len(candidates),
            "total_rows": len(rollup),
            "fit_rows_released_now": len(candidates) if release else 0,
            "reason": "all rows admission-grade" if release else "one or more rows missing, blocked, diagnostic, or not terminal",
        }
    ]


def build_blocked_or_diagnostic_rows(rollup: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rollup if row["admission_status"] != "candidate_pending_final_review"]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [(RELAUNCH / "post_exit_parse_rollup_contract.csv", "expected parse contract"), (PARSED_ROOT, "parsed output directory")]
    return [{"source_path": rel(path), "exists": "yes" if path.exists() else "no", "source_role": role, "mutation": "read_only"} for path, role in sources]


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(f"# Pressure/Upcomer Isolated Relaunch Post-Exit Rollup\n\nFit rows released now: {summary['fit_rows_released_now']}.\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(f"# {TASK}\n\n- status: complete\n- fit_rows_released_now: {summary['fit_rows_released_now']}\n- output: {rel(OUT)}\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(f"# {DATE} pressure/upcomer isolated relaunch post-exit rollup\n\nRolled up parsed pressure/upcomer rows without fit release.\n", encoding="utf-8")
    write_json(IMPORT, {"task": TASK, "date": DATE, "output_dir": rel(OUT), "native_solver_outputs_mutated": False, "summary_path": rel(OUT / "summary.json")})


def main() -> dict[str, Any]:
    require_sources()
    inventory = build_isolated_relaunch_parse_inventory()
    rollup = build_pressure_upcomer_admission_rollup(inventory)
    decision = build_fit_release_decision(rollup)
    blocked = build_blocked_or_diagnostic_rows(rollup)
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "inventory_rows": len(inventory),
        "admission_grade_candidate_rows": sum(row["classification"] == "admission_grade_candidate" for row in inventory),
        "blocked_or_diagnostic_rows": len(blocked),
        "fit_rows_released_now": decision[0]["fit_rows_released_now"],
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }
    write_csv(OUT / "isolated_relaunch_parse_inventory.csv", inventory)
    write_csv(OUT / "pressure_upcomer_admission_rollup.csv", rollup)
    write_csv(OUT / "fit_release_decision.csv", decision)
    write_csv(OUT / "blocked_or_diagnostic_rows.csv", blocked)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
