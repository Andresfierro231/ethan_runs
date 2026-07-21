#!/usr/bin/env python3
"""Build the final PM10 recirculation promotion gate."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace


PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
DEFAULT_RECIRC_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_recirc_hybrid_residual_scorecard"
    / "pm10_recirc_model_form_scorecard.csv"
)
DEFAULT_COMPONENT_GATE = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_pressure_component_isolation"
    / "pm10_component_isolation_gate.csv"
)
DEFAULT_UQ_GATE = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_qoi_uq_preflight"
    / "pm10_uq_gate.csv"
)
DEFAULT_OUTPUT_DIR = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_pm10_recirc_promotion_gate"

PROMOTION_FIELDS = [
    "case_key",
    "recirculation_lane",
    "residual_target_status",
    "component_isolation_status",
    "same_qoi_uq_gate",
    "promotion_state",
    "recirculation_calibration_review_allowed",
    "recirculation_model_selection_review_allowed",
    "ordinary_pipe_fit_allowed",
    "component_K_admitted",
    "runtime_input_allowed_now",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "required_next_evidence",
    "source_paths",
]
MANIFEST_FIELDS = ["source_id", "path", "exists", "role"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def unique_join(values: Iterable[str]) -> str:
    seen: list[str] = []
    for value in values:
        for part in str(value).split(";"):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
    return ";".join(seen)


def first_by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        case_key = row.get("case_key", "")
        if case_key and case_key not in out:
            out[case_key] = row
    return out


def promotion_rows(
    recirc_score_rows: list[dict[str, str]],
    component_gate_rows: list[dict[str, str]],
    uq_gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    recirc = first_by_case(recirc_score_rows)
    component = first_by_case(component_gate_rows)
    uq = first_by_case(uq_gate_rows)
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        r = recirc.get(case_key, {})
        c = component.get(case_key, {})
        u = uq.get(case_key, {})
        target_ok = r.get("target_status") == "residual_target_available"
        component_ok = c.get("component_isolation_ready") == "true"
        uq_ok = u.get("same_qoi_uq_gate") == "same_qoi_uq_pass"
        required: list[str] = []
        if not target_ok:
            required.append("same_window_residual_target")
        if not component_ok:
            required.append(c.get("required_next_evidence") or "component_isolation")
        if not uq_ok:
            required.append("same_qoi_mesh_time_uq")
        if target_ok and component_ok and uq_ok:
            state = "conditional_model_selection_review_ready"
            calibration_review = "yes"
            model_selection_review = "yes"
        elif target_ok and not component_ok:
            state = "blocked_missing_component_isolation"
            calibration_review = "no"
            model_selection_review = "no"
        elif target_ok and not uq_ok:
            state = "blocked_missing_mesh_time_uq"
            calibration_review = "no"
            model_selection_review = "no"
        else:
            state = "diagnostic_residual_weighted_ranking_only"
            calibration_review = "no"
            model_selection_review = "no"
        rows.append(
            {
                "case_key": case_key,
                "recirculation_lane": "recirculating_upcomer_effective",
                "residual_target_status": r.get("target_status", "missing"),
                "component_isolation_status": c.get("component_isolation_status", "missing"),
                "same_qoi_uq_gate": u.get("same_qoi_uq_gate", "missing"),
                "promotion_state": state,
                "recirculation_calibration_review_allowed": calibration_review,
                "recirculation_model_selection_review_allowed": model_selection_review,
                "ordinary_pipe_fit_allowed": "no",
                "component_K_admitted": "false",
                "runtime_input_allowed_now": "no",
                "fit_allowed_now": "no",
                "model_selection_allowed_now": "no",
                "required_next_evidence": unique_join(required),
                "source_paths": unique_join([r.get("source_paths", ""), rel(DEFAULT_COMPONENT_GATE), rel(DEFAULT_UQ_GATE)]),
            }
        )
    return rows


def source_manifest(recirc_scorecard_path: Path, component_gate_path: Path, uq_gate_path: Path) -> list[dict[str, Any]]:
    return [
        {"source_id": "pm10_recirc_model_form_scorecard", "path": rel(recirc_scorecard_path), "exists": str(recirc_scorecard_path.exists()).lower(), "role": "residual-weighted recirculation ranking"},
        {"source_id": "pm10_component_isolation_gate", "path": rel(component_gate_path), "exists": str(component_gate_path.exists()).lower(), "role": "component isolation status"},
        {"source_id": "pm10_uq_gate", "path": rel(uq_gate_path), "exists": str(uq_gate_path.exists()).lower(), "role": "same-QOI mesh/time UQ status"},
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {summary["recirc_scorecard_path"]}
tags: [pm10, promotion-gate, recirculation, model-selection]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Recirculation Promotion Gate

This gate joins PM10 residual ranking, component isolation, and same-QOI UQ. It
only opens conditional recirculation-aware review when all three evidence gates
pass. It never admits ordinary pipe coefficients, component `K`, or runtime
inputs.
""",
        encoding="utf-8",
    )


def build_package(
    recirc_scorecard_path: Path = DEFAULT_RECIRC_SCORECARD,
    component_gate_path: Path = DEFAULT_COMPONENT_GATE,
    uq_gate_path: Path = DEFAULT_UQ_GATE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    rows = promotion_rows(read_csv(recirc_scorecard_path), read_csv(component_gate_path), read_csv(uq_gate_path))
    csv_dump(output_dir / "pm10_recirc_promotion_gate.csv", PROMOTION_FIELDS, rows)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, source_manifest(recirc_scorecard_path, component_gate_path, uq_gate_path))
    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(rows),
        "conditional_model_selection_review_ready_cases": sum(row["promotion_state"] == "conditional_model_selection_review_ready" for row in rows),
        "blocked_missing_component_isolation_cases": sum(row["promotion_state"] == "blocked_missing_component_isolation" for row in rows),
        "blocked_missing_mesh_time_uq_cases": sum(row["promotion_state"] == "blocked_missing_mesh_time_uq" for row in rows),
        "required_component_isolation_cases": sum("component" in row["required_next_evidence"] or "straight_development" in row["required_next_evidence"] for row in rows),
        "required_same_qoi_uq_cases": sum("same_qoi_mesh_time_uq" in row["required_next_evidence"] for row in rows),
        "fit_allowed_now": 0,
        "model_selection_allowed_now": 0,
        "runtime_input_allowed_now": 0,
        "recirc_scorecard_path": rel(recirc_scorecard_path),
        "output_dir": rel(output_dir),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recirc-scorecard", type=Path, default=DEFAULT_RECIRC_SCORECARD)
    parser.add_argument("--component-gate", type=Path, default=DEFAULT_COMPONENT_GATE)
    parser.add_argument("--uq-gate", type=Path, default=DEFAULT_UQ_GATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(build_package(args.recirc_scorecard, args.component_gate, args.uq_gate, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
