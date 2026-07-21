#!/usr/bin/env python3
"""Build PM10 pressure component-isolation status.

This keeps PM10 in the recirculating-upcomer lane. Existing same-window pressure
targets are treated as partial residuals until straight/development terms are
available with the same case/window/basis.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
DEFAULT_TARGETS = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets"
    / "pm10_same_window_residual_targets.csv"
)
DEFAULT_DEVELOPMENT_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard"
    / "development_toggle_scorecard.csv"
)
DEFAULT_COMPONENT_TERMS = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_pressure_component_isolation"
    / "pm10_same_window_component_terms.csv"
)
DEFAULT_OUTPUT_DIR = (
    ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pm10_pressure_component_isolation"
)

ISOLATION_FIELDS = [
    "case_key",
    "target_status",
    "pm10_pressure_partial_residual_pa",
    "straight_development_term_pa",
    "pm10_pressure_isolated_residual_pa",
    "abs_pm10_pressure_isolated_residual_pa",
    "available_development_evidence_rows",
    "straight_development_terms_status",
    "component_isolation_status",
    "component_K_admitted",
    "ordinary_f_D_admitted",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "blockers",
    "source_paths",
]

GATE_FIELDS = [
    "case_key",
    "component_isolation_status",
    "component_isolation_ready",
    "required_next_evidence",
    "admission_effect",
]

MANIFEST_FIELDS = ["source_id", "path", "exists", "role"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, precision: int = 10) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "" if value is None else str(value)
    return f"{parsed:.{precision}g}"


def unique_join(values: Iterable[str]) -> str:
    seen: list[str] = []
    for value in values:
        for part in str(value).split(";"):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
    return ";".join(seen)


def development_evidence_rows(rows: list[dict[str, str]]) -> int:
    wanted = {"hydraulic_reset_length", "developing_apparent_friction"}
    total = 0
    for row in rows:
        if row.get("loop_region") != "upcomer" or row.get("toggle_id") not in wanted:
            continue
        try:
            total += int(float(row.get("local_evidence_rows", "0")))
        except ValueError:
            pass
    return total


def component_terms_by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("case_key", ""): row for row in rows if row.get("case_key", "")}


def isolation_rows(
    targets: list[dict[str, str]],
    development_rows: list[dict[str, str]],
    component_terms: list[dict[str, str]],
) -> list[dict[str, Any]]:
    targets_by_case = {row.get("case_key", ""): row for row in targets}
    terms_by_case = component_terms_by_case(component_terms)
    evidence_rows = development_evidence_rows(development_rows)
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        target = targets_by_case.get(case_key, {})
        partial = parse_float(target.get("pm10_pressure_partial_residual_pa"))
        term_row = terms_by_case.get(case_key, {})
        term = parse_float(term_row.get("straight_development_term_pa"))
        term_status = term_row.get("component_term_status", "")
        blockers: list[str] = []
        if target.get("target_status") != "residual_target_available" or partial is None:
            status = "diagnostic_only"
            terms_status = "blocked_missing_pm10_pressure_target"
            blockers.append("pm10_pressure_residual_target_missing")
            isolated = None
        elif term is not None and term_status in {"available", "same_window_available", ""}:
            status = "component_isolation_ready"
            terms_status = "same_window_straight_development_terms_available"
            isolated = partial - term
        elif evidence_rows > 0:
            status = "component_isolation_partial"
            terms_status = "diagnostic_development_evidence_available_not_same_window"
            blockers.append("same_window_straight_development_terms_missing")
            isolated = None
        else:
            status = "diagnostic_only"
            terms_status = "straight_development_terms_missing"
            blockers.append("straight_development_evidence_missing")
            isolated = None
        if status != "component_isolation_ready":
            blockers.append("component_isolation_not_ready")
        rows.append(
            {
                "case_key": case_key,
                "target_status": target.get("target_status", "missing"),
                "pm10_pressure_partial_residual_pa": fmt(partial),
                "straight_development_term_pa": fmt(term),
                "pm10_pressure_isolated_residual_pa": fmt(isolated),
                "abs_pm10_pressure_isolated_residual_pa": fmt(abs(isolated) if isolated is not None else None),
                "available_development_evidence_rows": str(evidence_rows),
                "straight_development_terms_status": terms_status,
                "component_isolation_status": status,
                "component_K_admitted": "false",
                "ordinary_f_D_admitted": "false",
                "fit_allowed_now": "no",
                "model_selection_allowed_now": "no",
                "runtime_input_allowed_now": "no",
                "blockers": unique_join(blockers),
                "source_paths": unique_join(
                    [target.get("source_paths", ""), term_row.get("source_paths", ""), rel(DEFAULT_DEVELOPMENT_SCORECARD)]
                ),
            }
        )
    return rows


def gate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        ready = row["component_isolation_status"] == "component_isolation_ready"
        out.append(
            {
                "case_key": row["case_key"],
                "component_isolation_status": row["component_isolation_status"],
                "component_isolation_ready": str(ready).lower(),
                "required_next_evidence": "" if ready else "same_window_straight_development_terms",
                "admission_effect": (
                    "unblocks_component_isolation_for_policy_review"
                    if ready
                    else "keeps_pm10_residual_weighted_ranking_diagnostic_only"
                ),
            }
        )
    return out


def source_manifest(targets_path: Path, development_path: Path, component_terms_path: Path) -> list[dict[str, Any]]:
    return [
        {"source_id": "pm10_same_window_residual_targets", "path": rel(targets_path), "exists": str(targets_path.exists()).lower(), "role": "PM10 partial pressure residual target"},
        {"source_id": "boundary_layer_development_scorecard", "path": rel(development_path), "exists": str(development_path.exists()).lower(), "role": "diagnostic reset/development evidence"},
        {"source_id": "pm10_same_window_component_terms", "path": rel(component_terms_path), "exists": str(component_terms_path.exists()).lower(), "role": "optional same-window straight/development terms"},
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {summary["targets_path"]}
tags: [pm10, pressure, component-isolation, recirculation]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Pressure Component Isolation

This package separates the current PM10 same-window pressure target from the
remaining straight/development component-isolation blocker. It does not admit
ordinary `f_D`, component `K`, model-selection, or runtime use.
""",
        encoding="utf-8",
    )


def build_package(
    targets_path: Path = DEFAULT_TARGETS,
    development_scorecard_path: Path = DEFAULT_DEVELOPMENT_SCORECARD,
    component_terms_path: Path = DEFAULT_COMPONENT_TERMS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    rows = isolation_rows(read_csv(targets_path), read_csv(development_scorecard_path), read_csv(component_terms_path))
    gates = gate_rows(rows)
    manifest = source_manifest(targets_path, development_scorecard_path, component_terms_path)
    csv_dump(output_dir / "pm10_pressure_component_isolation.csv", ISOLATION_FIELDS, rows)
    csv_dump(output_dir / "pm10_component_isolation_gate.csv", GATE_FIELDS, gates)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(rows),
        "component_isolation_ready_cases": sum(row["component_isolation_status"] == "component_isolation_ready" for row in rows),
        "component_isolation_partial_cases": sum(row["component_isolation_status"] == "component_isolation_partial" for row in rows),
        "fit_allowed_now": 0,
        "model_selection_allowed_now": 0,
        "runtime_input_allowed_now": 0,
        "targets_path": rel(targets_path),
        "output_dir": rel(output_dir),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--development-scorecard", type=Path, default=DEFAULT_DEVELOPMENT_SCORECARD)
    parser.add_argument("--component-terms", type=Path, default=DEFAULT_COMPONENT_TERMS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(build_package(args.targets, args.development_scorecard, args.component_terms, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
