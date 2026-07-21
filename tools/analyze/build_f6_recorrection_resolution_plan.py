#!/usr/bin/env python3
"""Build AGENT-501 F6 re-correction resolution package."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-501"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_recorrection_resolution_plan"

F6_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock"
PM10_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness"
HIGH_HEAT_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor"
ANCHOR_DIR = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"

F6_CANDIDATES = F6_DIR / "f6_candidate_inventory.csv"
F6_QUEUE = F6_DIR / "next_extraction_queue.csv"
F6_CONTRACT = F6_DIR / "f6_admission_contract.md"
F6_SUMMARY = F6_DIR / "summary.json"
PM10_CASES = PM10_DIR / "pm10_case_readiness.csv"
PM10_SUMMARY = PM10_DIR / "summary.json"
HIGH_HEAT_QUEUE = HIGH_HEAT_DIR / "harvest_readiness_queue.csv"
ANCHOR_MATRIX = ANCHOR_DIR / "proposed_cfd_run_matrix.csv"

SOURCES = {
    "f6_candidate_inventory": (F6_CANDIDATES, "canonical current F6 PM5 candidate rows"),
    "f6_next_extraction_queue": (F6_QUEUE, "current narrowed F6 evidence queue"),
    "f6_admission_contract": (F6_CONTRACT, "ordinary and recirculation-modeled lane rules"),
    "f6_summary": (F6_SUMMARY, "current F6 decision counts"),
    "pm10_case_readiness": (PM10_CASES, "future PM10 terminal admission readiness"),
    "pm10_summary": (PM10_SUMMARY, "PM10 blocked/live count summary"),
    "high_heat_harvest_queue": (HIGH_HEAT_QUEUE, "high-heat terminal harvest readiness"),
    "recirculation_anchor_matrix": (ANCHOR_MATRIX, "proposed onset-bracketing CFD studies"),
}

LOW_REVERSE_LIMIT = 0.01

GATE_COLUMNS = [
    "row_id",
    "evidence_family",
    "case_key",
    "span",
    "case_role",
    "Re",
    "Ri",
    "RAF",
    "RMF",
    "SVF",
    "ordinary_gate",
    "hybrid_gate",
    "pressure_status",
    "thermal_feature_status",
    "uncertainty_status",
    "lane_classification",
    "scoreable_now",
    "promotion_allowed",
    "primary_blocker",
    "next_action",
    "source_path",
]

SCORECARD_COLUMNS = [
    "resolution_item",
    "evidence_family",
    "candidate_rows",
    "scoreable_rows",
    "required_gate",
    "current_status",
    "production_baseline",
    "promotion_allowed",
    "decision",
    "reason",
]

QUEUE_COLUMNS = [
    "priority",
    "action_id",
    "evidence_lane",
    "dependency",
    "current_status",
    "next_step",
    "minimum_acceptance",
    "source_path",
]

MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({key: "" if row.get(key) is None else str(row.get(key, "")) for key in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def as_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def require_sources() -> None:
    missing = [rel(path) for path, _role in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required AGENT-501 source files: " + ", ".join(missing))


def build_gate_matrix(pm5_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in pm5_rows:
        raf = as_float(row.get("reverse_area_fraction"))
        rmf = as_float(row.get("reverse_mass_fraction"))
        low_reverse = (
            raf is not None
            and rmf is not None
            and raf < LOW_REVERSE_LIMIT
            and rmf < LOW_REVERSE_LIMIT
        )
        material_reverse = not low_reverse
        if material_reverse:
            ordinary_gate = "fail_material_reverse_flow"
            lane = "diagnostic_recirculation"
            blocker = "material_recirculation_blocks_ordinary_f6; missing_hybrid_admission_evidence"
        else:
            ordinary_gate = "pass_low_reverse_pending_pressure_split_score"
            lane = "ordinary_f6_candidate"
            blocker = "pending_same_window_pressure_loss_and_split_score"

        rows.append(
            {
                "row_id": row.get("candidate_id", ""),
                "evidence_family": "PM5",
                "case_key": row.get("case_key", ""),
                "span": row.get("span", ""),
                "case_role": row.get("case_role", ""),
                "Re": row.get("Re", ""),
                "Ri": row.get("Ri", ""),
                "RAF": row.get("reverse_area_fraction", ""),
                "RMF": row.get("reverse_mass_fraction", ""),
                "SVF": row.get("secondary_velocity_fraction", ""),
                "ordinary_gate": ordinary_gate,
                "hybrid_gate": "diagnostic_only_missing_pressure_residual_deltaT_Gz_uncertainty_split_score",
                "pressure_status": "no_admitted_hybrid_pressure_residual_movement",
                "thermal_feature_status": "partial_RAF_RMF_SVF_present_deltaT_and_Gz_missing",
                "uncertainty_status": "missing_mesh_time_uncertainty",
                "lane_classification": lane,
                "scoreable_now": "no",
                "promotion_allowed": "no",
                "primary_blocker": blocker,
                "next_action": "harvest terminal PM10/high-heat evidence or run onset-bracketing CFD before scoring",
                "source_path": row.get("source_path", rel(F6_CANDIDATES)),
            }
        )
    return rows


def build_scorecard(
    gate_rows: list[dict[str, Any]],
    pm10_rows: list[dict[str, str]],
    high_heat_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    lane_counts = Counter(row["lane_classification"] for row in gate_rows)
    pm10_blocked = sum(1 for row in pm10_rows if row.get("readiness_state") != "ready_for_terminal_admission")
    high_heat_blocked = sum(1 for row in high_heat_rows if row.get("harvest_readiness") != "harvest_ready")
    return [
        {
            "resolution_item": "production_baseline",
            "evidence_family": "current_1d_model",
            "candidate_rows": "",
            "scoreable_rows": "",
            "required_gate": "only replace after split-safe evidence beats baseline",
            "current_status": "keep_current",
            "production_baseline": "F3_shah_apparent",
            "promotion_allowed": "not_applicable",
            "decision": "keep",
            "reason": "No F6 lane currently passes admission.",
        },
        {
            "resolution_item": "ordinary_F6_single_stream",
            "evidence_family": "PM5",
            "candidate_rows": lane_counts.get("ordinary_f6_candidate", 0),
            "scoreable_rows": 0,
            "required_gate": "RAF < 0.01, RMF < 0.01, same-window pressure loss, Re/Ri/properties, split score",
            "current_status": "blocked_zero_ordinary_rows",
            "production_baseline": "F3_shah_apparent",
            "promotion_allowed": "no",
            "decision": "do_not_promote",
            "reason": "All PM5 rows fail the low-reverse-flow gate, so there are 0 ordinary F6 scoreable rows.",
        },
        {
            "resolution_item": "recirculation_modeled_F6_onset",
            "evidence_family": "PM5",
            "candidate_rows": lane_counts.get("diagnostic_recirculation", 0),
            "scoreable_rows": 0,
            "required_gate": "same-window RAF/RMF/SVF, Delta T, Gz, pressure residual movement, UQ, split improvement",
            "current_status": "diagnostic_only",
            "production_baseline": "F3_shah_apparent",
            "promotion_allowed": "no",
            "decision": "do_not_promote",
            "reason": "PM5 has regime diagnostics, but not the pressure movement, thermal features, uncertainty, or validation/holdout score needed for a named hybrid closure.",
        },
        {
            "resolution_item": "PM10_terminal_follow_on",
            "evidence_family": "PM10",
            "candidate_rows": len(pm10_rows),
            "scoreable_rows": 0,
            "required_gate": "terminal jobs plus PM5-style scratch-copy postprocessing and admission",
            "current_status": f"blocked_live_or_nonterminal_cases={pm10_blocked}",
            "production_baseline": "F3_shah_apparent",
            "promotion_allowed": "no",
            "decision": "wait_for_terminal_harvest",
            "reason": "PM10 rows are future-holdout evidence; no terminal admission has been performed.",
        },
        {
            "resolution_item": "high_heat_no_recirc_follow_on",
            "evidence_family": "high_heat",
            "candidate_rows": len(high_heat_rows),
            "scoreable_rows": 0,
            "required_gate": "terminal high-heat harvest with reverse-flow and pressure/thermal/UQ contract",
            "current_status": f"blocked_running_or_not_harvest_ready_cases={high_heat_blocked}",
            "production_baseline": "F3_shah_apparent",
            "promotion_allowed": "no",
            "decision": "wait_for_terminal_harvest",
            "reason": "High-heat rows are intended as low-reverse or non-recirculating anchors, but the cited monitor marks them not terminal.",
        },
    ]


def build_action_queue(
    f6_queue: list[dict[str, str]],
    pm10_rows: list[dict[str, str]],
    high_heat_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    priority = 10
    for row in f6_queue:
        rows.append(
            {
                "priority": priority,
                "action_id": row.get("queue_id", ""),
                "evidence_lane": "ordinary_or_hybrid_f6",
                "dependency": row.get("blocker_id", "f6-friction-re-correction"),
                "current_status": row.get("current_status", ""),
                "next_step": row.get("required_evidence", ""),
                "minimum_acceptance": row.get("minimum_acceptance", ""),
                "source_path": row.get("source_path", rel(F6_QUEUE)),
            }
        )
        priority += 10

    rows.extend(
        [
            {
                "priority": 60,
                "action_id": "pm10:terminal_harvest_and_pm5_style_postprocess",
                "evidence_lane": "future_holdout_recirc_or_transition",
                "dependency": "jobs 3293924 and 3295438 terminal",
                "current_status": f"{sum(1 for row in pm10_rows if row.get('readiness_state') != 'ready_for_terminal_admission')} blocked cases",
                "next_step": "After terminal completion, run PM5-style scratch-copy matched-plane/wall-band postprocessing and terminal admission.",
                "minimum_acceptance": "U, T, wallHeatFlux, Re/Pr/Ri/Gr/Ra/Gz, wall-core Delta T, RAF/RMF/SVF, pressure residuals, steady-window status, UQ.",
                "source_path": rel(PM10_CASES),
            },
            {
                "priority": 70,
                "action_id": "high_heat:terminal_harvest_nonrecirc_anchor",
                "evidence_lane": "ordinary_f6_anchor_or_onset_bracket",
                "dependency": "jobs 3299610 and 3299620 terminal",
                "current_status": f"{sum(1 for row in high_heat_rows if row.get('harvest_readiness') != 'harvest_ready')} blocked cases",
                "next_step": "When terminal, harvest the high-heat cases and test whether RAF/RMF falls below 0.01.",
                "minimum_acceptance": "At least one low-reverse/non-recirculating anchor or a bounded transition pair with same-window pressure/thermal/UQ.",
                "source_path": rel(HIGH_HEAT_QUEUE),
            },
            {
                "priority": 80,
                "action_id": "study:onset_bracketing_q_x_insulation_matrix",
                "evidence_lane": "transition_classifier",
                "dependency": "after high-heat harvest shows remaining gap",
                "current_status": "proposed_not_staged_here",
                "next_step": "Use the Salt3 Q x insulation matrix to bracket the recirculation onset boundary.",
                "minimum_acceptance": "Each case emits U, T, wallHeatFlux, dimensionless groups, wall-core Delta T, RAF/RMF/SVF, secondary velocity, steady status, and UQ.",
                "source_path": rel(ANCHOR_MATRIX),
            },
            {
                "priority": 90,
                "action_id": "study:nonrecirculating_f6_anchor",
                "evidence_lane": "ordinary_f6_single_stream",
                "dependency": "choose high-Re/high-insulation or high-Q case after terminal high-heat evidence",
                "current_status": "needed_if_no_existing_low_reverse_anchor",
                "next_step": "Design one CFD case expressly to achieve RAF < 0.01 and RMF < 0.01.",
                "minimum_acceptance": "Low reverse-flow gate plus same-window pressure loss, properties, time window, and mesh/time bounds.",
                "source_path": rel(ANCHOR_MATRIX),
            },
            {
                "priority": 100,
                "action_id": "study:hybrid_closure_residual_test",
                "evidence_lane": "recirculation_modeled_f6_onset",
                "dependency": "only after features and uncertainty exist",
                "current_status": "not_scoreable_today",
                "next_step": "Score named section-effective or onset/mixing penalty against F3 on validation/holdout.",
                "minimum_acceptance": "Improves pressure residuals without hidden global multiplier or split leakage.",
                "source_path": rel(F6_CONTRACT),
            },
        ]
    )
    return rows


def write_decision_tree(path: Path, generated_at: str) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(F6_CANDIDATES)}
  - {rel(F6_CONTRACT)}
tags: [f6, friction, recirculation, decision-tree]
related:
  - .agent/status/2026-07-17_AGENT-501.md
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Re-Correction Decision Tree

Generated: `{generated_at}`

## Gate 1: Ordinary F6

A row can enter ordinary single-stream F6 only when `RAF < 0.01` and
`RMF < 0.01`, and when same-window pressure loss, Re/Ri/properties, and
split-safe validation/holdout scoring exist. Any material reverse flow blocks
ordinary `f_D`, ordinary F6, and component `K` fitting.

Current PM5 result: fail. The PM5 inventory has 12 rows and all 12 have
material reverse flow, so ordinary F6 has 0 scoreable rows.

## Gate 2: Recirculation-Modeled Lane

Material-recirculation rows may support a named section-effective loss,
mixing penalty, or onset/transition diagnostic. They cannot be reported as
ordinary friction. Promotion requires same-window RAF/RMF/SVF, wall-core or
wall-bulk Delta T, Gz, pressure residual movement, mesh/time uncertainty, and
validation/holdout improvement over `F3_shah_apparent` without a hidden global
multiplier.

Current PM5 result: diagnostic only. PM5 has RAF/RMF/SVF evidence, but it does
not have the full pressure, thermal, uncertainty, and split-score package.

## Gate 3: Follow-On Evidence

PM10 and high-heat runs should be harvested only after terminal completion.
If they produce low-reverse anchors, ordinary F6 can be revisited. If they
remain recirculating, use them only in the named recirculation/onset lane and
score against `F3_shah_apparent`.

## Current Production Decision

Keep `F3_shah_apparent` as production. Do not promote F6 or a recirculation
hybrid until one of the explicit lanes passes its full gate.
""",
        encoding="utf-8",
    )


def write_recommended_studies(path: Path, generated_at: str) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(PM10_CASES)}
  - {rel(HIGH_HEAT_QUEUE)}
  - {rel(ANCHOR_MATRIX)}
  - {rel(F6_CONTRACT)}
tags: [f6, cfd-study-design, recirculation, uncertainty]
related:
  - .agent/status/2026-07-17_AGENT-501.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# Recommended Further Studies

Generated: `{generated_at}`

## Special Section: Studies That Add Clarity

1. Immediate terminal harvest: wait for PM10 and high-heat jobs to become
terminal, then run PM5-style scratch-copy postprocessing. Required outputs are
`U`, `T`, `wallHeatFlux`, Re/Pr/Ri/Gr/Ra/Gz, wall-core Delta T, reverse
area/mass fraction, secondary velocity, steady-window status, and mesh/time
uncertainty.

2. Non-recirculating F6 anchor: use a high-Re/high-insulation or high-Q case
to deliberately seek `RAF < 0.01` and `RMF < 0.01`. This is the cleanest route
to an ordinary F6 friction row.

3. Onset-bracketing Q x insulation matrix: if terminal high-heat evidence does
not provide a clean non-recirculating anchor, run the small Q x insulation
matrix to bracket transition between low-reverse and material-recirculation
regimes.

4. Low-Q/low-insulation cell-max sentinel: keep this case because it stresses
the opposite regime, where buoyancy and loss sensitivity should be strongest.
It is useful for a recirculation-modeled lane, not ordinary F6, unless the
reverse-flow gate unexpectedly passes.

5. Hybrid closure residual test: after features and uncertainty exist, score a
named section-effective/onset/mixing penalty against `F3_shah_apparent` on
validation/holdout. Do not use realized CFD mass flow, validation temperatures,
or a hidden global multiplier.

6. Uncertainty sequence: start with time-window uncertainty for RAF/RMF/SVF,
pressure residuals, and wall-core Delta T. Add mesh/GCI only after a candidate
lane shows meaningful residual movement.

## Next Steps For Today

- Keep F6 blocked for production and cite the gate matrix instead of trying to
fit ordinary friction from PM5.
- Monitor PM10 and high-heat terminal status in their owning packages; do not
harvest from this package.
- When a run becomes terminal, claim a separate extraction task and rerun the
PM5-style scratch-copy workflow with the full output contract above.
- If no terminal case reaches the low-reverse gate, prioritize the Q x
insulation onset-bracketing matrix before adding more nominal perturbations.
""",
        encoding="utf-8",
    )


def write_readme(path: Path, generated_at: str, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(F6_CANDIDATES)}
  - {rel(F6_CONTRACT)}
  - {rel(PM10_CASES)}
  - {rel(HIGH_HEAT_QUEUE)}
tags: [f6, friction, recirculation, blocker]
related:
  - .agent/status/2026-07-17_AGENT-501.md
  - .agent/journal/2026-07-17/f6-recorrection-resolution-plan.md
task: {TASK}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Re-Correction Resolution Plan

Generated: `{generated_at}`

## Answer

PM5 rows classify as recirculation diagnostics because all PM5 candidate rows
fail the low-reverse-flow gate for ordinary F6. The gate is `RAF < 0.01` and
`RMF < 0.01`; the current PM5 rows have material reverse flow, so they cannot
be used as ordinary single-stream `f_D`, F6, or component `K` rows.

## Current Counts

- PM5 rows reviewed: `{summary["pm5_rows"]}`.
- Ordinary F6 scoreable rows: `{summary["ordinary_scoreable_rows"]}`.
- Recirculation diagnostic rows: `{summary["recirculation_diagnostic_rows"]}`.
- Hybrid/recirculation scoreable rows: `{summary["hybrid_scoreable_rows"]}`.
- Production closure: `{summary["production_closure"]}`.
- Promotion allowed now: `{summary["promotion_allowed"]}`.

## Outputs

- `f6_row_gate_matrix.csv`
- `f6_decision_tree.md`
- `f6_resolution_scorecard.csv`
- `f6_next_action_queue.csv`
- `recommended_further_studies.md`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, blocker register, generated index files, or active-agent scopes
were mutated. This package performs no terminal harvest and makes no
scientific admission change.
""",
        encoding="utf-8",
    )


def build_manifest() -> list[dict[str, Any]]:
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "role": role,
        }
        for source_id, (path, role) in SOURCES.items()
    ]


def build_package(out_dir: Path = OUT) -> dict[str, Any]:
    require_sources()
    generated_at = utc_now()
    out_dir.mkdir(parents=True, exist_ok=True)

    pm5_rows = read_csv(F6_CANDIDATES)
    pm10_rows = read_csv(PM10_CASES)
    high_heat_rows = read_csv(HIGH_HEAT_QUEUE)
    f6_queue = read_csv(F6_QUEUE)
    f6_summary = read_json(F6_SUMMARY)
    pm10_summary = read_json(PM10_SUMMARY)

    gate_rows = build_gate_matrix(pm5_rows)
    scorecard_rows = build_scorecard(gate_rows, pm10_rows, high_heat_rows)
    action_rows = build_action_queue(f6_queue, pm10_rows, high_heat_rows)
    manifest_rows = build_manifest()

    write_csv(out_dir / "f6_row_gate_matrix.csv", gate_rows, GATE_COLUMNS)
    write_csv(out_dir / "f6_resolution_scorecard.csv", scorecard_rows, SCORECARD_COLUMNS)
    write_csv(out_dir / "f6_next_action_queue.csv", action_rows, QUEUE_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", manifest_rows, MANIFEST_COLUMNS)

    lane_counts = Counter(row["lane_classification"] for row in gate_rows)
    ordinary_scoreable = sum(1 for row in gate_rows if row["lane_classification"] == "ordinary_f6_candidate" and row["scoreable_now"] == "yes")
    hybrid_scoreable = sum(1 for row in gate_rows if row["lane_classification"] == "diagnostic_recirculation" and row["scoreable_now"] == "yes")
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": generated_at,
        "output_dir": rel(out_dir),
        "pm5_rows": len(pm5_rows),
        "ordinary_scoreable_rows": ordinary_scoreable,
        "ordinary_f6_candidate_rows": lane_counts.get("ordinary_f6_candidate", 0),
        "recirculation_diagnostic_rows": lane_counts.get("diagnostic_recirculation", 0),
        "hybrid_scoreable_rows": hybrid_scoreable,
        "pm10_cases": len(pm10_rows),
        "pm10_ready_cases": pm10_summary.get("ready_for_terminal_admission_count", 0),
        "high_heat_cases": len(high_heat_rows),
        "high_heat_harvest_ready_cases": sum(1 for row in high_heat_rows if row.get("harvest_readiness") == "harvest_ready"),
        "production_closure": "F3_shah_apparent",
        "promotion_allowed": "no",
        "f6_blocker_decision": f6_summary.get("f6_blocker_decision", "keep_open_narrowed"),
        "recommended_studies_count": 6,
        "next_action_rows": len(action_rows),
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "generated_index_refresh": "not_run_active_agents_own_generated_index_paths",
    }
    write_json(out_dir / "summary.json", summary)
    write_decision_tree(out_dir / "f6_decision_tree.md", generated_at)
    write_recommended_studies(out_dir / "recommended_further_studies.md", generated_at)
    write_readme(out_dir / "README.md", generated_at, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
