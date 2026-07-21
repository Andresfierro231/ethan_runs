#!/usr/bin/env python3
"""Rank low-dimensional hydraulic correction candidates from fit-safe evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DATE_DIR = ROOT / "work_products/2026-07/2026-07-13"
HYDRAULIC_GATE_DIR = DATE_DIR / "2026-07-13_predictive_hydraulic_gate"
PRESSURE_DIR = DATE_DIR / "2026-07-13_salt2_pressure_only_mesh_family_comparison"
RESET_NAMED_DIR = DATE_DIR / "2026-07-13_litrev_reset_named_losses"
OUT_DIR = DATE_DIR / "2026-07-13_predictive_hydraulic_correction_candidates"

RAW_COLUMNS = [
    "lane",
    "span",
    "fit_safety",
    "basis",
    "fine_value",
    "delta_pct",
    "gate_decision",
    "allowed_use",
    "fit_lane",
]
DIAGNOSTIC_COLUMNS = RAW_COLUMNS + ["diagnostic_reason"]
SCALING_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "variant_id",
    "mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_ratio_model_to_cfd",
    "required_resistance_multiplier",
    "additional_resistance_fraction",
    "deltaP_losses_Pa",
    "equivalent_added_loss_at_model_root_Pa",
    "pressure_residual_Pa",
    "thermal_fit_used",
    "hydraulic_only_interpretation",
]
CANDIDATE_COLUMNS = [
    "rank",
    "candidate_id",
    "candidate_name",
    "fit_lane",
    "parameter_count",
    "training_evidence",
    "diagnostic_evidence",
    "mean_required_resistance_multiplier",
    "mdot_improvement_without_thermal_fitting",
    "admission_status",
    "primary_blockers",
    "decision",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def mean(values: Iterable[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    if not finite:
        return None
    return sum(finite) / len(finite)


def split_fit_rows(fit_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw: list[dict[str, Any]] = []
    diagnostic: list[dict[str, Any]] = []
    for row in fit_rows:
        lane = row.get("lane", "")
        base = {
            "lane": lane,
            "span": row.get("span", ""),
            "fit_safety": row.get("fit_safety", ""),
            "basis": row.get("basis", ""),
            "fine_value": num(row.get("fine_value")),
            "delta_pct": num(row.get("delta_pct")),
            "gate_decision": row.get("gate_decision", ""),
            "allowed_use": row.get("allowed_use", ""),
        }
        if lane == "pressure_gradient_friction" and row.get("fit_safety") == "fit_safe_pressure_gradient":
            base["fit_lane"] = "fit_safe_raw_pressure_gradient"
            raw.append(base)
        elif lane == "momentum_corrected_friction" and row.get("fit_safety") == "fit_safe_momentum_corrected":
            base["fit_lane"] = "diagnostic_momentum_corrected"
            base["diagnostic_reason"] = (
                "debuoyed/profile evidence only; not a substitute for raw pressure-gradient fitting"
            )
            diagnostic.append(base)
    return raw, diagnostic


def resistance_scaling_rows(forward_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in forward_rows:
        mdot = num(row.get("mdot_kg_s"))
        cfd_mdot = num(row.get("cfd_mdot_kg_s"))
        losses = num(row.get("deltaP_losses_Pa"))
        pressure_residual = num(row.get("pressure_residual_Pa"))
        ratio = mdot / cfd_mdot if mdot is not None and cfd_mdot not in (None, 0.0) else None
        multiplier = ratio * ratio if ratio is not None else None
        additional = multiplier - 1.0 if multiplier is not None else None
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "fluid_case_name": row.get("fluid_case_name", ""),
                "variant_id": row.get("variant_id", ""),
                "mdot_kg_s": mdot,
                "cfd_mdot_kg_s": cfd_mdot,
                "mdot_ratio_model_to_cfd": ratio,
                "required_resistance_multiplier": multiplier,
                "additional_resistance_fraction": additional,
                "deltaP_losses_Pa": losses,
                "equivalent_added_loss_at_model_root_Pa": losses * additional
                if losses is not None and additional is not None
                else None,
                "pressure_residual_Pa": pressure_residual,
                "thermal_fit_used": "no",
                "hydraulic_only_interpretation": hydraulic_scaling_interpretation(multiplier),
            }
        )
    return rows


def hydraulic_scaling_interpretation(multiplier: float | None) -> str:
    if multiplier is None:
        return "not_quantified"
    if multiplier > 1.0:
        return "increasing_hydraulic_resistance_would_reduce_mdot_toward_cfd"
    if multiplier < 1.0:
        return "decreasing_hydraulic_resistance_would_raise_mdot_toward_cfd"
    return "current_resistance_matches_cfd_mdot"


def count_named(loss_rows: list[dict[str, str]], status: str | None = None) -> int:
    if status is None:
        return len(loss_rows)
    return sum(1 for row in loss_rows if row.get("fit_use_status") == status)


def candidate_rows(
    raw_rows: list[dict[str, Any]],
    diagnostic_rows: list[dict[str, Any]],
    named_loss_rows: list[dict[str, str]],
    reset_rows: list[dict[str, str]],
    scaling_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mean_multiplier = mean(num(row.get("required_resistance_multiplier")) for row in scaling_rows)
    raw_spans = ", ".join(row["span"] for row in raw_rows)
    diagnostic_spans = ", ".join(row["span"] for row in diagnostic_rows)
    fit_named = count_named(named_loss_rows, "fit_target")
    reset_flagged = sum(
        1 for row in reset_rows if row.get("hydraulic_reset_status") in {"reset_flagged", "feature_reset_assumed_for_downstream_development_sensitivity"}
    )
    return [
        {
            "rank": 1,
            "candidate_id": "H1_localized_named_loss_and_reset_bundle",
            "candidate_name": "localized named losses plus reset/development sensitivity",
            "fit_lane": "diagnostic_momentum_corrected_with_fit_safe_raw_guardrail",
            "parameter_count": 3,
            "training_evidence": f"{len(raw_rows)} raw fit-safe spans retained as guardrails: {raw_spans}",
            "diagnostic_evidence": f"{fit_named} named-loss fit-target rows; {reset_flagged} hydraulic reset/development rows; momentum spans: {diagnostic_spans}",
            "mean_required_resistance_multiplier": mean_multiplier,
            "mdot_improvement_without_thermal_fitting": "yes_expected_hydraulic_only",
            "admission_status": "best_candidate_for_next_hydraulic_rerun_not_publication_ready",
            "primary_blockers": "named losses are coarse/no-GCI; some K rows are upper bounds; full solve_case rerun still needed",
            "decision": "advance first because it can add resistance locally without hiding losses in one global multiplier",
        },
        {
            "rank": 2,
            "candidate_id": "H2_fit_safe_raw_two_span_friction_scale",
            "candidate_name": "single scalar on raw fit-safe pressure-gradient spans",
            "fit_lane": "fit_safe_raw_pressure_gradient",
            "parameter_count": 1,
            "training_evidence": f"{len(raw_rows)} raw fit-safe spans: {raw_spans}",
            "diagnostic_evidence": "uses no pressure-recovery spans for fitting; diagnostic rows may only sanity-check sign and scale",
            "mean_required_resistance_multiplier": mean_multiplier,
            "mdot_improvement_without_thermal_fitting": "yes_possible_but_underinformed",
            "admission_status": "screening_candidate_only",
            "primary_blockers": "only Salt2 pressure-gradient rows are fit-safe; Closure-QOI GCI publication readiness is false",
            "decision": "use as a conservative lower-dimensional screen, not as the preferred physical correction",
        },
        {
            "rank": 3,
            "candidate_id": "H3_momentum_corrected_profile_scale",
            "candidate_name": "debuoyed momentum/profile correction across all spans",
            "fit_lane": "diagnostic_momentum_corrected",
            "parameter_count": 2,
            "training_evidence": "no raw pressure-gradient training outside the two fit-safe spans",
            "diagnostic_evidence": f"{len(diagnostic_rows)} momentum-corrected positive, medium/fine-consistent spans: {diagnostic_spans}",
            "mean_required_resistance_multiplier": mean_multiplier,
            "mdot_improvement_without_thermal_fitting": "yes_diagnostic_only",
            "admission_status": "diagnostic_candidate_only",
            "primary_blockers": "strong buoyancy corrections on lower_leg and upper_leg; not raw pressure-gradient evidence",
            "decision": "use to design profile/debuoying terms after H1/H2, not as a standalone fit claim",
        },
        {
            "rank": 4,
            "candidate_id": "H4_global_loop_resistance_multiplier",
            "candidate_name": "one global loop resistance multiplier",
            "fit_lane": "rejected_global",
            "parameter_count": 1,
            "training_evidence": f"would numerically target mean multiplier {csv_value(mean_multiplier)}",
            "diagnostic_evidence": "contradicts named-loss package recommendation to preserve localized losses",
            "mean_required_resistance_multiplier": mean_multiplier,
            "mdot_improvement_without_thermal_fitting": "yes_numerically_but_rejected",
            "admission_status": "reject_except_as_math_baseline",
            "primary_blockers": "masks pressure recovery, resets, cluster losses, and recirculation invalidity",
            "decision": "do not export as model correction; keep only as a resistance-scaling baseline",
        },
        {
            "rank": 5,
            "candidate_id": "T0_thermal_parameter_fit",
            "candidate_name": "thermal UA/HTC/Nu adjustment to repair mdot",
            "fit_lane": "blocked_thermal",
            "parameter_count": "",
            "training_evidence": "none admitted by this task",
            "diagnostic_evidence": "hydraulic gate shows mdot failure before thermal fitting",
            "mean_required_resistance_multiplier": "",
            "mdot_improvement_without_thermal_fitting": "no_not_hydraulic",
            "admission_status": "blocked",
            "primary_blockers": "thermal closure remains blocked; per-case thermal hacks are disallowed",
            "decision": "reject for AGENT-300",
        },
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {summary['source_files']['hydraulic_fit_safety_gate']}
  - {summary['source_files']['forward_v0_hydraulic_residuals']}
  - {summary['source_files']['named_pressure_loss_table']}
  - {summary['source_files']['reset_distance_map']}
tags: [predictive-model, hydraulics, pressure-evidence, mdot]
related:
  - .agent/journal/2026-07-13/predictive-hydraulic-correction-candidates.md
  - .agent/status/2026-07-13_AGENT-300.md
task: AGENT-300
date: 2026-07-13
role: Implementer/Reviewer/Writer
type: work_product
status: complete
---

# Predictive Hydraulic Correction Candidates

Task: `AGENT-300`

This package ranks low-dimensional hydraulic correction candidates from existing pressure evidence. It does not mutate native CFD outputs, does not edit external Fluid, and does not fit thermal UA/HTC/Nu parameters.

## Start Here

Why this exists: TODO-PRED-HYDRAULIC-GATE showed that forward-v0 pressure roots converge at low residual but overpredict `mdot` for every Salt row. That means thermal-looking improvements cannot be claimed until a hydraulic resistance path is tested.

Files to open first:

- `candidate_rankings.csv` for the ranked correction candidates.
- `mdot_resistance_scaling.csv` for the hydraulic-only resistance factor needed to move current forward-v0 `mdot` toward CFD `mdot`.
- `fit_safe_raw_pressure_rows.csv` for raw pressure-gradient rows admitted as fit-safe.
- `diagnostic_momentum_corrected_rows.csv` for debuoyed/profile diagnostic rows.
- `decision_summary.json` for machine-readable counts and the package decision.

Trusted packages: TODO-PRED-HYDRAULIC-GATE, AGENT-262 Salt2 pressure-only mesh-family comparison, and TODO-LITREV-RESET-NAMED-LOSSES.

Active board row: `AGENT-300`.

Next task sequence: implement the `H1` localized named-loss/reset bundle in a bounded forward hydraulic rerun, keep `H2` as a raw-fit-safe scalar screen, then rerun forward scoring before reopening thermal closure.

Output contract: raw pressure-gradient fit rows and momentum-corrected diagnostic rows are separate files and separate candidate lanes.

Do-not-do guardrails: no native solver mutation, no per-case thermal hacks, no thermal fitting, no global resistance multiplier as the exported correction.

## Decision

- Best next candidate: `{summary['best_candidate_id']}`.
- Mean resistance multiplier needed to hit CFD `mdot` under the simple hydraulic scaling check: `{summary['mean_required_resistance_multiplier']:.3f}`.
- Hydraulic-only mdot improvement is plausible because every forward-v0 row overpredicts `mdot`; increasing hydraulic resistance moves the root in the needed direction.
- This is not publication-ready closure: named losses are coarse/no-GCI, raw fit-safe evidence is limited to two spans, and a full forward rerun is still required.
- Thermal closure remains blocked.

## Outputs

- `candidate_rankings.csv`
- `mdot_resistance_scaling.csv`
- `fit_safe_raw_pressure_rows.csv`
- `diagnostic_momentum_corrected_rows.csv`
- `decision_summary.json`

## Reproduce

```bash
python3 tools/analyze/build_predictive_hydraulic_correction_candidates.py
python3 -m unittest tools.analyze.test_predictive_hydraulic_correction_candidates
```
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(
    out_dir: Path = OUT_DIR,
    hydraulic_gate_dir: Path = HYDRAULIC_GATE_DIR,
    reset_named_dir: Path = RESET_NAMED_DIR,
) -> dict[str, Any]:
    fit_rows = read_csv(hydraulic_gate_dir / "hydraulic_fit_safety_gate.csv")
    forward_rows = read_csv(hydraulic_gate_dir / "forward_v0_hydraulic_residuals.csv")
    named_rows = read_csv(reset_named_dir / "named_pressure_loss_table.csv")
    reset_rows = read_csv(reset_named_dir / "reset_distance_map.csv")

    raw_rows, diagnostic_rows = split_fit_rows(fit_rows)
    scaling_rows = resistance_scaling_rows(forward_rows)
    candidates = candidate_rows(raw_rows, diagnostic_rows, named_rows, reset_rows, scaling_rows)

    write_csv(out_dir / "fit_safe_raw_pressure_rows.csv", raw_rows, RAW_COLUMNS)
    write_csv(out_dir / "diagnostic_momentum_corrected_rows.csv", diagnostic_rows, DIAGNOSTIC_COLUMNS)
    write_csv(out_dir / "mdot_resistance_scaling.csv", scaling_rows, SCALING_COLUMNS)
    write_csv(out_dir / "candidate_rankings.csv", candidates, CANDIDATE_COLUMNS)

    summary = {
        "task_id": "AGENT-300",
        "generated_utc": utc_now(),
        "output_dir": rel(out_dir),
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "thermal_fit_used": False,
        "thermal_closure_status": "blocked",
        "can_mdot_improve_without_thermal_fitting": "yes_hydraulic_resistance_increase_moves_mdot_toward_cfd_but_requires_forward_rerun",
        "best_candidate_id": candidates[0]["candidate_id"],
        "mean_required_resistance_multiplier": mean(
            num(row.get("required_resistance_multiplier")) for row in scaling_rows
        ),
        "raw_fit_safe_spans": [row["span"] for row in raw_rows],
        "diagnostic_momentum_corrected_spans": [row["span"] for row in diagnostic_rows],
        "n_named_loss_rows": len(named_rows),
        "n_named_fit_target_rows": count_named(named_rows, "fit_target"),
        "n_reset_rows": len(reset_rows),
        "outputs": [
            "candidate_rankings.csv",
            "mdot_resistance_scaling.csv",
            "fit_safe_raw_pressure_rows.csv",
            "diagnostic_momentum_corrected_rows.csv",
            "decision_summary.json",
            "README.md",
        ],
        "source_files": {
            "hydraulic_fit_safety_gate": rel(hydraulic_gate_dir / "hydraulic_fit_safety_gate.csv"),
            "forward_v0_hydraulic_residuals": rel(hydraulic_gate_dir / "forward_v0_hydraulic_residuals.csv"),
            "named_pressure_loss_table": rel(reset_named_dir / "named_pressure_loss_table.csv"),
            "reset_distance_map": rel(reset_named_dir / "reset_distance_map.csv"),
            "agent_262_pressure_package": rel(PRESSURE_DIR),
        },
    }
    write_json(out_dir / "decision_summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--hydraulic-gate-dir", type=Path, default=HYDRAULIC_GATE_DIR)
    parser.add_argument("--reset-named-dir", type=Path, default=RESET_NAMED_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_package(args.output_dir, args.hydraulic_gate_dir, args.reset_named_dir)


if __name__ == "__main__":
    main()
