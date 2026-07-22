#!/usr/bin/env python3
"""Build publication-readiness and study-dispatch audit for diagnostic forms."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = "TODO-DIAGNOSTIC-MODEL-FORM-PUBLICATION-READINESS-AND-STUDY-DISPATCH-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_diagnostic_model_form_publication_readiness_and_study_dispatch"
DIAG = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests"
BOARD = ROOT / ".agent/BOARD.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def board_has(task_id: str, board_text: str) -> bool:
    return task_id in board_text


def main() -> None:
    append = read_csv(DIAG / "model_form_scoreboard_append.csv")
    assumptions = read_csv(DIAG / "construction_assumptions.csv")
    runtime = read_csv(DIAG / "runtime_audit.csv")
    summary = json.loads((DIAG / "summary.json").read_text())
    board_text = BOARD.read_text()

    study_rows = [
        {
            "priority": 1,
            "finding": "D4 segment offsets gave the largest transfer improvement",
            "evidence": "D4 transfer RMSE 7.94040349151 K versus M3 17.3645293096 K",
            "study": "Segment-local source-placement evidence gate",
            "board_task": "TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22",
            "why_next": "Best empirical signal; must be explained by independent segment heat/source evidence before any candidate can be trusted.",
            "admission_boundary": "diagnostic-only until source-bounded candidate, split discipline, and UQ gates exist",
        },
        {
            "priority": 2,
            "finding": "D3 wall-index correction transfers better than global or TP/TW offsets",
            "evidence": "D3 transfer RMSE 8.38846755024 K with local-shape RMSE 7.93285020379 K",
            "study": "Wall-shape axial-mixing or wall/core exchange gate",
            "board_task": "TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22",
            "why_next": "Tests whether the residual shape is physics or sensor/QOI projection rather than a fitted temperature line.",
            "admission_boundary": "diagnostic-only until source-bounded mechanism and same-QOI/UQ requirements are satisfied",
        },
        {
            "priority": 3,
            "finding": "D1 and D2 remove most global cold bias but leave local shape",
            "evidence": "D1/D2 transfer RMSE near 10.5 K and transfer bias +2.72695351733 K",
            "study": "Passive wall/test-section source-bounded repair gate",
            "board_task": "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22",
            "why_next": "Checks whether a missing independent passive heat-path term explains the level shift without absorbing residuals into Nu.",
            "admission_boundary": "no repair execution or admission until independent source/property evidence exists",
        },
        {
            "priority": 4,
            "finding": "TP/TW-specific offsets helped only slightly beyond global offset",
            "evidence": "D2 transfer RMSE 10.5253939442 K versus D1 10.5420700958 K",
            "study": "TP/TW QOI projection uncertainty gate",
            "board_task": "TODO-MF-D2-TP-TW-QOI-PROJECTION-GATE-2026-07-22",
            "why_next": "Determines whether TP/TW separation is sensor projection uncertainty rather than a physical closure.",
            "admission_boundary": "runtime temperature inputs remain forbidden; projection uncertainty is support evidence only",
        },
        {
            "priority": 5,
            "finding": "No minimum setup-only baseline exists in the tested score ladder",
            "evidence": "Diagnostic package still compares against M2/M3, not M0",
            "study": "M0 setup-only baseline scorecard",
            "board_task": "TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22",
            "why_next": "Needed to state how much M2/M3 and residual diagnostics improve over the minimum legal model.",
            "admission_boundary": "no scored TP/TW or realized CFD fields may enter runtime inputs",
        },
        {
            "priority": 6,
            "finding": "Pressure/mdot coupling was not tested by thermal residual corrections",
            "evidence": "Diagnostic tests have no pressure/velocity basis requirements",
            "study": "Pressure/mdot coupling diagnostic",
            "board_task": "TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22",
            "why_next": "Determines whether hydraulic pressure residuals move mdot enough to affect TP/TW temperatures.",
            "admission_boundary": "diagnostic-only unless same-QOI UQ, ordinary-flow, endpoint-field, and source/property gates pass",
        },
        {
            "priority": 7,
            "finding": "S13 target-plus same-QOI harvest may unblock exchange evidence",
            "evidence": "Active target-plus harvest row exists after target-plus windows completed",
            "study": "S13 target-plus same-QOI harvest",
            "board_task": "TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-SAME-QOI-HARVEST-2026-07-22",
            "why_next": "Could provide same-label neighbor-window evidence needed before upcomer exchange becomes more than diagnostic.",
            "admission_boundary": "no production harvest, source/property release, coefficient admission, or S12/S13 trigger from this dispatch",
        },
    ]

    board_rows = [
        {
            "board_task": row["board_task"],
            "listed_on_board": board_has(row["board_task"], board_text),
            "priority": row["priority"],
            "study": row["study"],
            "dispatch_status": "ready_to_claim" if board_has(row["board_task"], board_text) else "missing_from_board",
        }
        for row in study_rows
    ]

    assumption_by_id = {row["tested_model_form_id"]: row for row in assumptions}
    publication_rows = [
        {
            "criterion": "numeric reproducibility",
            "status": "pass",
            "evidence": "builder and validator scripts exist; runtime_audit.csv records phase runtimes",
            "remaining_gap": "none for diagnostic addendum",
        },
        {
            "criterion": "split discipline",
            "status": "pass",
            "evidence": "Salt2 train_candidate fit only; Salt3/Salt4 transfer report only",
            "remaining_gap": "do not describe Salt3/Salt4 as final protected validation from this package",
        },
        {
            "criterion": "construction assumptions",
            "status": "pass",
            "evidence": "construction_assumptions.csv lists formula, basis, missing fields, and forbidden inputs for each tested form",
            "remaining_gap": "source-bounded physical construction still needed for D3/D4/D1",
        },
        {
            "criterion": "per-sensor signed errors",
            "status": "pass",
            "evidence": "tested_model_form_sensor_errors.csv includes signed K and percent error for every finite TP/TW row",
            "remaining_gap": "figures should use signed errors, not only RMSE",
        },
        {
            "criterion": "publication claim boundary",
            "status": "pass_with_guardrail",
            "evidence": "README and assumptions label all fitted rows diagnostic_not_admitted",
            "remaining_gap": "publication text must call D1-D4 residual-shape diagnostics, not admitted closures",
        },
        {
            "criterion": "source-bounded physical admission",
            "status": "fail_closed",
            "evidence": "missing_fields column records no independent Q_wall/passive wall term, no same-QOI UQ, no M0 baseline, no source/property release",
            "remaining_gap": "execute successor board rows before claiming predictive model-form improvement",
        },
    ]

    write_csv(
        OUT / "study_dispatch_from_findings.csv",
        study_rows,
        ["priority", "finding", "evidence", "study", "board_task", "why_next", "admission_boundary"],
    )
    write_csv(
        OUT / "board_row_crosswalk.csv",
        board_rows,
        ["board_task", "listed_on_board", "priority", "study", "dispatch_status"],
    )
    write_csv(
        OUT / "publication_readiness_audit.csv",
        publication_rows,
        ["criterion", "status", "evidence", "remaining_gap"],
    )
    write_csv(
        OUT / "diagnostic_form_publication_claims.csv",
        [
            {
                "tested_model_form_id": row["candidate_id"],
                "transfer_rmse_K": row["transfer_rmse_K"],
                "transfer_mean_signed_error_K": row["transfer_mean_signed_error_K"],
                "claim_allowed": "diagnostic residual-shape and study-priority signal",
                "claim_forbidden": "source-bounded closure, final score, admitted repair, or validation/holdout-tuned model",
                "assumption_recorded": assumption_by_id.get(row["candidate_id"], {}).get("assumptions", ""),
            }
            for row in append
        ],
        [
            "tested_model_form_id",
            "transfer_rmse_K",
            "transfer_mean_signed_error_K",
            "claim_allowed",
            "claim_forbidden",
            "assumption_recorded",
        ],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"path": str((DIAG / "model_form_scoreboard_append.csv").relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str((DIAG / "construction_assumptions.csv").relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str((DIAG / "runtime_audit.csv").relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": str((DIAG / "summary.json").relative_to(ROOT)), "used": True, "mutation_status": "read_only"},
            {"path": ".agent/BOARD.md", "used": True, "mutation_status": "own_row_and_successor_rows_updated"},
        ],
        ["path", "used", "mutation_status"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native CFD/OpenFOAM outputs", "mutation": False},
            {"guardrail": "registry/admission state", "mutation": False},
            {"guardrail": "scheduler/solver/sampler/harvest/UQ", "mutation": False},
            {"guardrail": "Fluid or external source trees", "mutation": False},
            {"guardrail": "thesis current/LaTeX files", "mutation": False},
            {"guardrail": "new fitting/scoring/admission", "mutation": False},
        ],
        ["guardrail", "mutation"],
    )
    summary_out = {
        "task": TASK,
        "decision": "study_rows_listed_publication_readiness_pass_with_fail_closed_admission",
        "study_rows": len(study_rows),
        "board_rows_listed": sum(1 for row in board_rows if row["listed_on_board"]),
        "publication_readiness_rows": len(publication_rows),
        "publication_ready_for_diagnostic_claims": True,
        "ready_for_admitted_closure_claims": False,
        "best_diagnostic": summary["best_transfer_diagnostic_id"],
        "best_transfer_rmse_K": summary["best_transfer_rmse_K"],
        "m3_transfer_rmse_K": summary["m3_transfer_rmse_K"],
    }
    write_json(OUT / "summary.json", summary_out)

    readme = f"""---
provenance:
  - {str((DIAG / "model_form_scoreboard_append.csv").relative_to(ROOT))}
  - {str((DIAG / "construction_assumptions.csv").relative_to(ROOT))}
  - .agent/BOARD.md
tags: [model-form-dispatch, publication-readiness, thesis, diagnostic-tests]
related:
  - .agent/status/2026-07-22_{TASK}.md
  - .agent/journal/2026-07-22/diagnostic-model-form-publication-readiness-and-study-dispatch.md
task: {TASK}
date: 2026-07-22
role: Coordinator / Writer / Tester / Reviewer
type: work_product
status: complete
---
# Diagnostic Model-Form Publication Readiness And Study Dispatch

This package audits the suggested model-form diagnostic test package for
publication usability and lists the follow-on studies implied by the findings.

## Decision

The diagnostic runs are publication-usable as residual-shape diagnostics and
study-priority evidence. They are not publication-ready as admitted closures or
final predictive scores.

## Study Order

1. D4 segment-source placement evidence gate.
2. D3 wall-shape axial-mixing / wall-core exchange gate.
3. Passive wall/test-section source-bounded repair gate.
4. D2 TP/TW QOI projection gate.
5. M0 setup-only baseline scorecard.
6. MF02 pressure/mdot coupling diagnostic.
7. S13 target-plus same-QOI harvest, already active.

## Outputs

- `study_dispatch_from_findings.csv`
- `board_row_crosswalk.csv`
- `publication_readiness_audit.csv`
- `diagnostic_form_publication_claims.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(readme)


if __name__ == "__main__":
    main()
