#!/usr/bin/env python3
"""Build AGENT-487 F6 friction/Re-correction unblock package."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-487"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock")
OUT = ROOT / OUT_REL

AGENT425 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock"
AGENT464 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard"
AGENT467 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract"
AGENT478 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"

F6_SCORECARD = AGENT425 / "f6_onset_scorecard.csv"
F6_CANDIDATES = AGENT425 / "f6_fit_candidate_table.csv"
F6_STATUS = AGENT464 / "f6_status_scorecard.csv"
RECIRC_TABLE = AGENT467 / "recirculation_feature_admission_table.csv"
HYBRID_CONTRACT = AGENT467 / "hybrid_1d_model_contract.csv"
RECIRC_QUEUE = AGENT467 / "next_extraction_queue.csv"
CFD_MATRIX = AGENT478 / "proposed_cfd_run_matrix.csv"
CFD_OUTPUT_CONTRACT = AGENT478 / "required_output_contract.csv"

SOURCES = {
    "f6_onset_scorecard": F6_SCORECARD,
    "f6_fit_candidate_table": F6_CANDIDATES,
    "f6_status_scorecard": F6_STATUS,
    "recirculation_feature_admission_table": RECIRC_TABLE,
    "hybrid_1d_model_contract": HYBRID_CONTRACT,
    "recirculation_next_extraction_queue": RECIRC_QUEUE,
    "recirculation_cfd_run_matrix": CFD_MATRIX,
    "recirculation_required_output_contract": CFD_OUTPUT_CONTRACT,
}

LOW_REVERSE_LIMIT = 0.01
TRANSITION_REVERSE_LIMIT = 0.10
RECIRC_RI_LIMIT = 1.0

CANDIDATE_COLUMNS = [
    "candidate_id",
    "case_key",
    "case_role",
    "span",
    "Re",
    "Ri",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "primary_classification",
    "ordinary_f6_admission_status",
    "hybrid_lane_status",
    "fit_admissible_now",
    "allowed_use_now",
    "blocked_labels",
    "missing_for_admission",
    "reason",
    "source_path",
]

SCORE_COLUMNS = [
    "model_lane",
    "production_baseline",
    "candidate_rows",
    "scoreable_rows",
    "validation_holdout_status",
    "hidden_global_multiplier_status",
    "decision",
    "reason",
]

QUEUE_COLUMNS = [
    "queue_id",
    "blocker_id",
    "required_evidence",
    "minimum_acceptance",
    "current_status",
    "why_needed",
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


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def classify_row(row: dict[str, str]) -> dict[str, str]:
    raf = as_float(row.get("reverse_area_fraction"))
    rmf = as_float(row.get("reverse_mass_fraction"))
    ri = as_float(row.get("Ri"))
    fit_now = row.get("fit_admissible_now", "")

    max_reverse = max(value for value in [raf, rmf] if value is not None)
    material_recirc = max_reverse >= TRANSITION_REVERSE_LIMIT or (ri is not None and ri >= RECIRC_RI_LIMIT)
    low_reverse = max_reverse < LOW_REVERSE_LIMIT and (ri is None or ri < RECIRC_RI_LIMIT)

    if low_reverse and fit_now == "yes":
        primary = "ordinary_f6_candidate"
        ordinary_status = "admissible_pending_score_against_f3"
        hybrid_status = "not_applicable_low_reverse"
        missing = "validation_holdout_score_over_F3"
    elif material_recirc:
        primary = "recirculation_diagnostic"
        ordinary_status = "blocked_material_recirculation"
        hybrid_status = "future_hybrid_lane_candidate_not_admitted"
        missing = "pressure_residual_movement;wall_core_or_wall_bulk_deltaT;Gz;mesh_time_uncertainty;validation_holdout_score_over_F3"
    elif max_reverse < TRANSITION_REVERSE_LIMIT:
        primary = "hybrid_lane_candidate"
        ordinary_status = "blocked_transition_recirculation"
        hybrid_status = "transition_anchor_needed"
        missing = "paired_low_reverse_and_material_recirculation_anchors;mesh_time_uncertainty;validation_holdout_score_over_F3"
    else:
        primary = "needs_extraction"
        ordinary_status = "insufficient_reverse_flow_or_pressure_evidence"
        hybrid_status = "not_scoreable"
        missing = "same_window_reverse_flow_pressure_property_evidence"

    return {
        "primary_classification": primary,
        "ordinary_f6_admission_status": ordinary_status,
        "hybrid_lane_status": hybrid_status,
        "missing_for_admission": missing,
    }


def candidate_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(F6_SCORECARD):
        labels = "none" if row.get("fit_admissible_now") == "yes" else "single_stream_f_D; ordinary_F6"
        classified = classify_row(row)
        rows.append(
            {
                "candidate_id": f"pm5:{row.get('case_key', '')}:{row.get('span', '')}",
                "case_key": row.get("case_key", ""),
                "case_role": row.get("case_role", ""),
                "span": row.get("span", ""),
                "Re": row.get("Re", ""),
                "Ri": row.get("Ri", ""),
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "secondary_velocity_fraction": row.get("secondary_velocity_fraction", ""),
                "fit_admissible_now": row.get("fit_admissible_now", ""),
                "allowed_use_now": row.get("allowed_use_now", ""),
                "blocked_labels": labels,
                "reason": row.get("reason", ""),
                "source_path": row.get("source_metric_file", rel(F6_SCORECARD)),
                **classified,
            }
        )
    return rows


def score_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordinary_candidates = [row for row in candidates if row["primary_classification"] == "ordinary_f6_candidate"]
    hybrid_candidates = [
        row
        for row in candidates
        if row["primary_classification"] in {"recirculation_diagnostic", "hybrid_lane_candidate"}
    ]
    ordinary_scoreable = [row for row in ordinary_candidates if row["fit_admissible_now"] == "yes"]
    hybrid_scoreable: list[dict[str, Any]] = []
    return [
        {
            "model_lane": "ordinary_F6_single_stream",
            "production_baseline": "F3_shah_apparent",
            "candidate_rows": len(ordinary_candidates),
            "scoreable_rows": len(ordinary_scoreable),
            "validation_holdout_status": "not_scoreable_no_admitted_ordinary_rows",
            "hidden_global_multiplier_status": "not_used",
            "decision": "do_not_promote",
            "reason": "No non-recirculating fit-admissible pressure rows exist in the current PM5 evidence.",
        },
        {
            "model_lane": "recirculation_modeled_F6_onset",
            "production_baseline": "F3_shah_apparent",
            "candidate_rows": len(hybrid_candidates),
            "scoreable_rows": len(hybrid_scoreable),
            "validation_holdout_status": "not_scoreable_missing_hybrid_pressure_delta_uncertainty_and_split_scores",
            "hidden_global_multiplier_status": "forbidden_by_contract",
            "decision": "do_not_promote",
            "reason": "Material-recirculation rows support regime diagnostics and future hybrid design, but not an admitted predictive closure today.",
        },
    ]


def queue_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "queue_id": "f6:ordinary_nonrecirculating_pressure_rows",
            "blocker_id": "f6-friction-re-correction",
            "required_evidence": "Non-recirculating or low-reverse-flow pressure rows for upcomer/test-section-relevant spans.",
            "minimum_acceptance": "RAF < 0.01 and RMF < 0.01, valid same-window pressure loss, Re/Ri/property extraction, and split-safe scoring.",
            "current_status": "missing",
            "why_needed": "Only these rows can support ordinary single-stream F6/f_D admission.",
            "source_path": rel(F6_CANDIDATES),
        },
        {
            "queue_id": "f6:hybrid_pressure_residual_movement",
            "blocker_id": "f6-friction-re-correction",
            "required_evidence": "Explicit recirculation-modeled pressure residual movement against F3_shah_apparent.",
            "minimum_acceptance": "Validation/holdout improvement without realized CFD mdot, validation temperatures, or hidden global multiplier.",
            "current_status": "missing",
            "why_needed": "Material-recirculation rows can only promote a named hybrid/onset lane if they move predictive residuals.",
            "source_path": rel(HYBRID_CONTRACT),
        },
        {
            "queue_id": "f6:hybrid_thermal_geometry_features",
            "blocker_id": "f6-friction-re-correction",
            "required_evidence": "Same-window wall-core or wall-bulk Delta T, Gz, RAF/RMF/SVF, and pressure metrics.",
            "minimum_acceptance": "Features extracted on the same retained window and section definitions as the pressure/onset evidence.",
            "current_status": "partial",
            "why_needed": "Current PM5 rows include RAF/RMF/SVF but lack the full hybrid feature set needed for admission.",
            "source_path": rel(CFD_OUTPUT_CONTRACT),
        },
        {
            "queue_id": "f6:mesh_time_uncertainty",
            "blocker_id": "f6-friction-re-correction",
            "required_evidence": "Mesh/time uncertainty for reverse-flow, Ri, pressure residual, and any admitted hybrid metric.",
            "minimum_acceptance": "Coarse/medium/fine or documented time-window bounds before coefficient promotion.",
            "current_status": "missing",
            "why_needed": "Prevents fitting an onset/friction correction to one under-bounded recirculation realization.",
            "source_path": rel(CFD_OUTPUT_CONTRACT),
        },
        {
            "queue_id": "f6:cfd_anchor_follow_on",
            "blocker_id": "f6-friction-re-correction",
            "required_evidence": "Salt3 Q x insulation onset anchors from AGENT-478 after current Salt4 high-heat jobs are usable.",
            "minimum_acceptance": "At least one low-reverse/non-recirculating anchor or bounded transition pair with required output contract.",
            "current_status": "blocked_pending_3299610_3299620_harvest_status",
            "why_needed": "Current PM5 evidence is all material recirculation and cannot bracket onset alone.",
            "source_path": rel(CFD_MATRIX),
        },
    ]
    return rows


def manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "f6_onset_scorecard": "row-level PM5 F6/onset candidate evidence",
        "f6_fit_candidate_table": "prior fit-candidate conclusion",
        "f6_status_scorecard": "current blocker status input",
        "recirculation_feature_admission_table": "hybrid/recirculation lane row labels",
        "hybrid_1d_model_contract": "allowed and forbidden model labels",
        "recirculation_next_extraction_queue": "existing extraction queue to extend",
        "recirculation_cfd_run_matrix": "follow-on CFD anchor design",
        "recirculation_required_output_contract": "required extraction features for future anchors",
    }
    return [
        {
            "source_id": source_id,
            "path": rel(path),
            "exists": path.exists(),
            "role": roles[source_id],
        }
        for source_id, path in SOURCES.items()
    ]


def write_contract(path: Path) -> None:
    text = f"""---
provenance:
  - {rel(F6_SCORECARD)}
  - {rel(HYBRID_CONTRACT)}
  - {rel(CFD_OUTPUT_CONTRACT)}
tags: [f6, friction, recirculation, admission, blocker]
related:
  - {rel(RECIRC_TABLE)}
  - {rel(CFD_MATRIX)}
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: decision_contract
status: complete
---
# F6 Admission Contract

## Ordinary F6 Lane

Admit only rows with low reverse flow (`RAF < 0.01` and `RMF < 0.01`), valid
same-window pressure loss, documented Re/Ri/property extraction, and split-safe
validation/holdout improvement over `F3_shah_apparent`.

## Recirculation-Modeled Lane

Rows with material reverse flow may support a named `section_effective_loss`,
`mixing_penalty`, or `onset/transition_diagnostic` lane. They may not be
reported as ordinary `Nu`, `f_D`, or component `K`.

Admission requires same-window RAF/RMF/SVF, wall-core or wall-bulk Delta T, Gz,
pressure residual movement, mesh/time uncertainty, and validation/holdout
improvement over `F3_shah_apparent` without a hidden global multiplier.

## Current Decision

Current PM5 evidence does not clear either lane. Keep `F3_shah_apparent` as the
production closure and keep `f6-friction-re-correction` open with the narrowed
queue in `next_extraction_queue.csv`.
"""
    path.write_text(text, encoding="utf-8")


def write_decision(path: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - f6_candidate_inventory.csv
  - f6_vs_f3_scorecard.csv
  - next_extraction_queue.csv
tags: [f6, friction, blocker, decision]
related:
  - .agent/blockers.yml
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: blocker_decision
status: complete
---
# F6 Blocker Decision

Decision: `keep_open_narrowed`.

The current package reviews `{summary["candidate_rows"]}` PM5 F6/onset rows.
Ordinary single-stream F6 has `{summary["ordinary_f6_candidate_rows"]}` candidate
rows and `{summary["ordinary_f6_scoreable_rows"]}` scoreable rows. The
recirculation-modeled lane has `{summary["hybrid_candidate_rows"]}` diagnostic or
future-hybrid rows and `{summary["hybrid_scoreable_rows"]}` scoreable rows.

Production remains `F3_shah_apparent`. The blocker can clear only after
non-recirculating pressure evidence or a named recirculation/onset lane beats
`F3_shah_apparent` on validation/holdout without a hidden global multiplier.

Generated-index refresh was intentionally not run in this task because active
`AGENT-482` owns `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.json`,
and `.agent/catalog.csv`.
"""
    path.write_text(text, encoding="utf-8")


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(F6_SCORECARD)}
  - {rel(F6_STATUS)}
  - {rel(HYBRID_CONTRACT)}
  - {rel(CFD_MATRIX)}
tags: [f6, friction, recirculation, blocker]
related:
  - .agent/status/2026-07-17_AGENT-487.md
  - .agent/journal/2026-07-17/f6-friction-re-correction-unblock.md
task: {TASK}
date: {DATE}
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Friction/Re-Correction Unblock

Generated: `{summary["generated_at"]}`

## Decision

- `f6-friction-re-correction`: `keep_open_narrowed`.
- Production closure remains `F3_shah_apparent`.
- No current row admits ordinary single-stream F6.
- No current row admits a predictive recirculation-modeled F6/onset closure.

## Results

- Candidate rows reviewed: `{summary["candidate_rows"]}`.
- Ordinary F6 candidate rows: `{summary["ordinary_f6_candidate_rows"]}`.
- Ordinary F6 scoreable rows: `{summary["ordinary_f6_scoreable_rows"]}`.
- Recirculation/hybrid diagnostic rows: `{summary["hybrid_candidate_rows"]}`.
- Recirculation/hybrid scoreable rows: `{summary["hybrid_scoreable_rows"]}`.
- Next extraction rows: `{summary["queue_rows"]}`.

## Outputs

- `f6_candidate_inventory.csv`
- `f6_admission_contract.md`
- `f6_vs_f3_scorecard.csv`
- `f6_blocker_decision.md`
- `next_extraction_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, or generated index files were mutated. Generated indexes remain
pending because `AGENT-482` owns the generated index paths.
"""
    path.write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    candidates = candidate_inventory()
    scores = score_rows(candidates)
    queue = queue_rows()
    manifest = manifest_rows()

    ordinary = [row for row in candidates if row["primary_classification"] == "ordinary_f6_candidate"]
    hybrid = [row for row in candidates if row["primary_classification"] in {"recirculation_diagnostic", "hybrid_lane_candidate"}]
    ordinary_scoreable = sum(1 for row in ordinary if row["fit_admissible_now"] == "yes")
    hybrid_scoreable = 0
    classifications = Counter(row["primary_classification"] for row in candidates)

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at": utc_now(),
        "f6_blocker_decision": "keep_open_narrowed",
        "production_closure": "F3_shah_apparent",
        "candidate_rows": len(candidates),
        "ordinary_f6_candidate_rows": len(ordinary),
        "ordinary_f6_scoreable_rows": ordinary_scoreable,
        "hybrid_candidate_rows": len(hybrid),
        "hybrid_scoreable_rows": hybrid_scoreable,
        "queue_rows": len(queue),
        "classification_counts": dict(classifications),
        "generated_index_refresh": "not_run_active_AGENT_482_owns_generated_indexes",
    }

    write_csv(out / "f6_candidate_inventory.csv", candidates, CANDIDATE_COLUMNS)
    write_csv(out / "f6_vs_f3_scorecard.csv", scores, SCORE_COLUMNS)
    write_csv(out / "next_extraction_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    write_contract(out / "f6_admission_contract.md")
    write_decision(out / "f6_blocker_decision.md", summary)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT, help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
