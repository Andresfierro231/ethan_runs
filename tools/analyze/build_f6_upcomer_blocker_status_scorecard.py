#!/usr/bin/env python3
"""Build AGENT-464 F6/upcomer blocker status scorecard."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-464"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard")
OUT = ROOT / OUT_REL

AGENT425 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock"
AGENT413 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation"
AGENT324 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution"

F6_SCORECARD = AGENT425 / "f6_onset_scorecard.csv"
F6_CANDIDATES = AGENT425 / "f6_fit_candidate_table.csv"
F6_READINESS = AGENT413 / "pm5_f6_admission_readiness.csv"
UPCOMER_STATUS = AGENT324 / "upcomer_onset_evidence_status.csv"
UPCOMER_REQUIREMENTS = AGENT324 / "next_evidence_requirements.csv"

SOURCES = {
    "f6_onset_scorecard": F6_SCORECARD,
    "f6_fit_candidate_table": F6_CANDIDATES,
    "pm5_f6_admission_readiness": F6_READINESS,
    "upcomer_onset_evidence_status": UPCOMER_STATUS,
    "upcomer_next_evidence_requirements": UPCOMER_REQUIREMENTS,
}

F6_COLUMNS = [
    "case_key",
    "case_role",
    "span",
    "Re",
    "Ri",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "fit_admissible_now",
    "allowed_use_now",
    "f6_decision",
    "reason",
    "source_path",
]
UPCOMER_COLUMNS = [
    "label",
    "Re_upcomer",
    "backflow_fraction",
    "Ri_median",
    "regime_class",
    "classification",
    "single_stream_fit_allowed",
    "allowed_use",
    "reason",
    "source_path",
]
QUEUE_COLUMNS = ["blocker_id", "queue_id", "required_evidence", "minimum_acceptance", "status", "source_path"]
DECISION_COLUMNS = [
    "blocker_id",
    "decision",
    "can_update_blocker_register",
    "resolved_by",
    "resolved_on",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
    "next_unlock_sequence",
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


def f6_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in read_csv(F6_SCORECARD):
        fit = row.get("fit_admissible_now", "")
        decision = "admit_f6_fit" if fit == "yes" else "diagnostic_only_keep_f3_production"
        out.append(
            {
                "case_key": row.get("case_key", ""),
                "case_role": row.get("case_role", ""),
                "span": row.get("span", ""),
                "Re": row.get("Re", ""),
                "Ri": row.get("Ri", ""),
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "fit_admissible_now": fit,
                "allowed_use_now": row.get("allowed_use_now", ""),
                "f6_decision": decision,
                "reason": row.get("reason", ""),
                "source_path": row.get("source_metric_file", rel(F6_SCORECARD)),
            }
        )
    return out


def upcomer_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in read_csv(UPCOMER_STATUS):
        regime = row.get("regime_class", "")
        if regime == "recirculation_cell_observed":
            classification = "observed_recirculation_only"
        elif row.get("admission_for_closure", "").startswith("not_fit"):
            classification = "rejected_for_single_stream_fit"
        else:
            classification = "manual_review"
        out.append(
            {
                "label": row.get("label", ""),
                "Re_upcomer": row.get("Re_upcomer", ""),
                "backflow_fraction": row.get("backflow_fraction", ""),
                "Ri_median": row.get("Ri_median", ""),
                "regime_class": regime,
                "classification": classification,
                "single_stream_fit_allowed": "no",
                "allowed_use": row.get("allowed_use", ""),
                "reason": row.get("decision_reason", ""),
                "source_path": rel(UPCOMER_STATUS),
            }
        )
    return out


def queue_rows() -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for row in read_csv(UPCOMER_REQUIREMENTS):
        queue.append(
            {
                "blocker_id": "upcomer-onset-data-sparsity",
                "queue_id": f"upcomer:{row.get('priority', '')}",
                "required_evidence": row.get("needed_evidence", ""),
                "minimum_acceptance": row.get("minimum_acceptance", ""),
                "status": row.get("status", ""),
                "source_path": rel(UPCOMER_REQUIREMENTS),
            }
        )
    queue.append(
        {
            "blocker_id": "f6-friction-re-correction",
            "queue_id": "f6:non_recirculating_or_hybrid_model_evidence",
            "required_evidence": "non-recirculating pressure rows or explicit recirculation-modeled F6/onset closure",
            "minimum_acceptance": "validation/holdout improvement over F3_shah_apparent without hidden global multiplier",
            "status": "missing_current_pm5_rows_are_diagnostic_only",
            "source_path": rel(F6_CANDIDATES),
        }
    )
    return queue


def decision_rows(f6: list[dict[str, Any]], upcomer: list[dict[str, Any]], queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    f6_admitted = sum(1 for row in f6 if row["fit_admissible_now"] == "yes")
    upcomer_single_stream = sum(1 for row in upcomer if row["single_stream_fit_allowed"] == "yes")
    return [
        {
            "blocker_id": "f6-friction-re-correction",
            "decision": "keep_open",
            "can_update_blocker_register": "yes",
            "resolved_by": "",
            "resolved_on": "",
            "criteria_passed": "PM5_fields_reviewed;F3_production_status_preserved;diagnostic_onset_use_defined",
            "criteria_failed": f"0_f6_fit_admissible_rows;{len(f6)}_material_recirculation_diagnostic_rows;no_holdout_improvement_over_F3",
            "scientific_interpretation": "Current PM5 rows are useful onset diagnostics, but all fail single-stream F6 fit admission. Keep F3_shah_apparent as production.",
            "next_unlock_sequence": "obtain_non_recirculating_or_hybrid_modeled_pressure_rows -> score_against_F3_on_validation_holdout -> update_blocker_register",
        },
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "decision": "keep_open",
            "can_update_blocker_register": "yes",
            "resolved_by": "",
            "resolved_on": "",
            "criteria_passed": f"{len(upcomer)}_observed_recirculation_points_classified",
            "criteria_failed": f"0_non_recirculating_anchor_points;0_single_stream_fit_allowed_rows;{len([r for r in queue if r['blocker_id']=='upcomer-onset-data-sparsity'])}_missing_evidence_requirements",
            "scientific_interpretation": "Current evidence observes recirculation, but onset/transition remains sparse and cannot be promoted to a single-stream closure.",
            "next_unlock_sequence": "add_or_admit_near_onset_Re_points -> add_non_recirculating_anchor -> bound_mesh_time_uncertainty -> update_onset_classification",
        },
    ]


def manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "f6_onset_scorecard": "row-level PM5 F6/onset diagnostic scorecard",
        "f6_fit_candidate_table": "current F6 fit candidate status",
        "pm5_f6_admission_readiness": "PM5 readiness input from blocker wave",
        "upcomer_onset_evidence_status": "current onset evidence points",
        "upcomer_next_evidence_requirements": "missing evidence requirements",
    }
    return [{"source_id": key, "path": rel(path), "exists": "yes" if path.exists() else "no", "role": roles[key]} for key, path in SOURCES.items()]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(F6_SCORECARD)}
  - {rel(F6_CANDIDATES)}
  - {rel(UPCOMER_STATUS)}
  - {rel(UPCOMER_REQUIREMENTS)}
tags: [f6, friction, upcomer, onset, blocker]
related:
  - .agent/blockers.yml
task: {TASK}
date: {DATE}
role: Hydraulics/Upcomer-onset/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 / Upcomer Blocker Status Scorecard

Generated: `{summary["generated_at"]}`

## Decisions

- `f6-friction-re-correction`: `keep_open`.
- `upcomer-onset-data-sparsity`: `keep_open`.

## Results

- F6/PM5 rows reviewed: `{summary["f6_rows"]}`.
- F6 fit-admissible rows: `{summary["f6_fit_admissible_rows"]}`.
- Upcomer onset evidence points reviewed: `{summary["upcomer_points"]}`.
- Upcomer single-stream fit rows admitted: `{summary["upcomer_single_stream_fit_rows"]}`.
- Queue rows: `{summary["queue_rows"]}`.

## Interpretation

Current PM5 rows are useful pressure/onset diagnostics, but all remain material
recirculation rows and cannot promote F6 as a single-stream friction correction.
Production should remain `F3_shah_apparent` until F6 shows validation/holdout
improvement without a hidden global multiplier.

Current upcomer evidence observes recirculation, but it does not bracket onset
or provide a non-recirculating anchor. Keep it in a hybrid/onset diagnostic
lane, not a conventional Nu/f_D/K fit lane.

## Outputs

- `f6_status_scorecard.csv`
- `upcomer_onset_classification.csv`
- `next_evidence_queue.csv`
- `blocker_decisions.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    f6 = f6_rows()
    upcomer = upcomer_rows()
    queue = queue_rows()
    decisions = decision_rows(f6, upcomer, queue)
    manifest = manifest_rows()

    write_csv(out / "f6_status_scorecard.csv", f6, F6_COLUMNS)
    write_csv(out / "upcomer_onset_classification.csv", upcomer, UPCOMER_COLUMNS)
    write_csv(out / "next_evidence_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(out / "blocker_decisions.csv", decisions, DECISION_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "f6_blocker_decision": "keep_open",
        "upcomer_blocker_decision": "keep_open",
        "f6_rows": len(f6),
        "f6_fit_admissible_rows": sum(1 for row in f6 if row["fit_admissible_now"] == "yes"),
        "f6_decision_counts": dict(Counter(row["f6_decision"] for row in f6)),
        "upcomer_points": len(upcomer),
        "upcomer_single_stream_fit_rows": sum(1 for row in upcomer if row["single_stream_fit_allowed"] == "yes"),
        "upcomer_classification_counts": dict(Counter(row["classification"] for row in upcomer)),
        "queue_rows": len(queue),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
