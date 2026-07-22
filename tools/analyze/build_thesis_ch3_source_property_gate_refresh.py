#!/usr/bin/env python3
"""Resolve the Ch3 CFD database source/property warning without admission."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-THESIS-CH3-SOURCE-PROPERTY-GATE-REFRESH-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_ch3_source_property_gate_refresh"

CH3_PACKET = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_ch3_cfd_database"
CASE_PROVENANCE = CH3_PACKET / "case_provenance_table.csv"
TODO_CSV = CH3_PACKET / "source_property_gate_todo.csv"
NOMINAL_PREFLIGHT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight/nominal_train_release_audit.csv"
SOURCE_UNBLOCK = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_source_property_unblock/release_unblock_matrix.csv"

CASE_NAME_TO_KEY = {
    "Salt1 nominal": "salt1_nominal",
    "Salt2 Jin nominal": "salt2_jin_nominal",
    "Salt3 Jin nominal": "salt3_jin_nominal",
    "Salt4 nominal": "salt4_nominal",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fieldnames:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass"}


def build_resolution_rows() -> list[dict[str, object]]:
    provenance_rows = read_csv(CASE_PROVENANCE)
    todo_rows = read_csv(TODO_CSV)
    nominal_rows = {row["case_key"]: row for row in read_csv(NOMINAL_PREFLIGHT)}

    out: list[dict[str, object]] = []
    for todo in todo_rows:
        row_number = int(todo["row_number"])
        provenance = provenance_rows[row_number - 1]
        case_key = CASE_NAME_TO_KEY[provenance["case_or_family"]]
        nominal = nominal_rows[case_key]

        release_ready = truthy(nominal["release_ready"])
        final_fit_allowed = truthy(nominal["final_fit_allowed"])
        final_model_selection_allowed = truthy(nominal["final_model_selection_allowed"])
        labels_complete = truthy(nominal["labels_complete"])
        resolution = "resolved_by_label_refresh_and_no_fit_demotion"
        writer_use_now = "database_provenance_and_diagnostic_context_only"
        if release_ready and final_fit_allowed and final_model_selection_allowed:
            resolution = "release_ready_recheck_required_before_use"
            writer_use_now = "candidate_specific_release_review_required"

        out.append(
            {
                "artifact": todo["artifact"],
                "row_number": row_number,
                "case_or_family": provenance["case_or_family"],
                "case_key": case_key,
                "split_role": provenance["split_role"],
                "ch3_fit_allowed_stale": provenance["fit_allowed"],
                "ch3_model_selection_allowed_stale": provenance["model_selection_allowed"],
                "ch3_failure_modes": todo["failure_modes"],
                "labels_complete_after_refresh": str(labels_complete).lower(),
                "property_mode": nominal["property_mode"],
                "property_sensitivity_label": nominal["property_sensitivity_label"],
                "source_validity_envelope_status": nominal["source_validity_envelope_status"],
                "source_use_category": nominal["source_use_category"],
                "source_property_gate_status": nominal["source_property_gate_status"],
                "release_ready_after_refresh": str(release_ready).lower(),
                "final_fit_allowed_after_refresh": str(final_fit_allowed).lower(),
                "final_model_selection_allowed_after_refresh": str(final_model_selection_allowed).lower(),
                "resolution": resolution,
                "writer_use_now": writer_use_now,
                "why_no_fit_or_admission_prose": (
                    "Split-role fit permission is insufficient without a source/property release gate. "
                    f"{nominal['primary_blocker']}; release_ready is false, so using the row for a fitted "
                    "coefficient or admission claim would silently bypass the source-envelope/provenance guard."
                ),
                "next_unblock_task": nominal["next_action"],
                "source_evidence": rel(NOMINAL_PREFLIGHT),
            }
        )
    return out


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = build_resolution_rows()

    write_csv(
        OUT / "ch3_source_property_gate_resolution.csv",
        rows,
        [
            "artifact",
            "row_number",
            "case_or_family",
            "case_key",
            "split_role",
            "ch3_fit_allowed_stale",
            "ch3_model_selection_allowed_stale",
            "ch3_failure_modes",
            "labels_complete_after_refresh",
            "property_mode",
            "property_sensitivity_label",
            "source_validity_envelope_status",
            "source_use_category",
            "source_property_gate_status",
            "release_ready_after_refresh",
            "final_fit_allowed_after_refresh",
            "final_model_selection_allowed_after_refresh",
            "resolution",
            "writer_use_now",
            "why_no_fit_or_admission_prose",
            "next_unblock_task",
            "source_evidence",
        ],
    )

    decision_rows = [
        {
            "decision": "ch3_source_property_warning_resolved_by_demote_no_release",
            "stale_warning_rows": len(rows),
            "labels_complete_after_refresh_rows": sum(row["labels_complete_after_refresh"] == "true" for row in rows),
            "release_ready_rows": sum(row["release_ready_after_refresh"] == "true" for row in rows),
            "final_fit_allowed_rows": sum(row["final_fit_allowed_after_refresh"] == "true" for row in rows),
            "final_model_selection_allowed_rows": sum(row["final_model_selection_allowed_after_refresh"] == "true" for row in rows),
            "writer_action": "use rows for Ch3 database provenance only; do not use for fit/admission prose",
            "next_unblock": "row-specific strict-pass source-envelope evidence followed by candidate-specific S11/S15 release gate",
        }
    ]
    write_csv(OUT / "warning_resolution_decision.csv", decision_rows)

    claim_rows = [
        {
            "claim_type": "allowed",
            "claim": "The four Ch3 nominal rows now have source/property labels available from the nominal-train preflight.",
            "source": rel(NOMINAL_PREFLIGHT),
        },
        {
            "claim_type": "allowed",
            "claim": "The four Ch3 nominal rows remain database/provenance evidence and must be treated as no-fit/no-admission rows for current thesis prose.",
            "source": rel(OUT / "ch3_source_property_gate_resolution.csv"),
        },
        {
            "claim_type": "forbidden",
            "claim": "Do not state these rows support coefficient fitting, candidate admission, model selection, protected scoring, or a final score.",
            "source": rel(SOURCE_UNBLOCK),
        },
    ]
    write_csv(OUT / "allowed_forbidden_claim_table.csv", claim_rows)

    guardrails = [
        {"guardrail": "native_output_mutation", "performed": False},
        {"guardrail": "registry_or_admission_mutation", "performed": False},
        {"guardrail": "scheduler_action", "performed": False},
        {"guardrail": "solver_or_postprocessing_launch", "performed": False},
        {"guardrail": "fluid_or_external_edit", "performed": False},
        {"guardrail": "thesis_latex_edit", "performed": False},
        {"guardrail": "source_property_release", "performed": False},
        {"guardrail": "candidate_freeze", "performed": False},
        {"guardrail": "protected_scoring", "performed": False},
        {"guardrail": "final_score", "performed": False},
    ]
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails)

    source_manifest = [
        {"path": rel(CASE_PROVENANCE), "role": "read_only_stale_ch3_case_table"},
        {"path": rel(TODO_CSV), "role": "read_only_warning_handoff"},
        {"path": rel(NOMINAL_PREFLIGHT), "role": "read_only_label_refresh_and_demotion_source"},
        {"path": rel(SOURCE_UNBLOCK), "role": "read_only_allowed_forbidden_claim_context"},
    ]
    write_csv(OUT / "source_manifest.csv", source_manifest)

    summary = {
        "task": TASK_ID,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "ch3_source_property_warning_resolved_by_demote_no_release",
        "warning_rows": len(rows),
        "labels_complete_after_refresh_rows": sum(row["labels_complete_after_refresh"] == "true" for row in rows),
        "release_ready_rows": sum(row["release_ready_after_refresh"] == "true" for row in rows),
        "final_fit_allowed_rows": sum(row["final_fit_allowed_after_refresh"] == "true" for row in rows),
        "final_model_selection_allowed_rows": sum(row["final_model_selection_allowed_after_refresh"] == "true" for row in rows),
        "source_property_release": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_score": False,
        "output_dir": rel(OUT),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    (OUT / "README.md").write_text(
        f"""---
provenance:
  - {rel(TODO_CSV)}
  - {rel(NOMINAL_PREFLIGHT)}
tags: [thesis, ch3, cfd-database, source-property, no-release]
related:
  - {rel(SOURCE_UNBLOCK)}
task: {TASK_ID}
date: {DATE}
status: complete
---
# Ch3 Source/Property Gate Refresh

Decision: `ch3_source_property_warning_resolved_by_demote_no_release`.

This packet resolves the Ch3 CFD database source/property warning by joining the
four stale nominal training rows in `source_property_gate_todo.csv` to the
completed nominal-train source/property preflight.

The result is a label refresh, not a source/property release:

- warning rows reviewed: `{summary['warning_rows']}`
- rows with labels complete after refresh: `{summary['labels_complete_after_refresh_rows']}`
- release-ready rows: `{summary['release_ready_rows']}`
- final fit-allowed rows after refresh: `{summary['final_fit_allowed_rows']}`
- final model-selection-allowed rows after refresh: `{summary['final_model_selection_allowed_rows']}`

## Writer Instruction

Use the affected Salt1-4 nominal rows only as Ch3 CFD database provenance and
diagnostic context. Do not use them as fit, model-selection, candidate
admission, protected-score, or final-score evidence until a future row provides
row-specific strict-pass source-envelope evidence and reruns the candidate
release gate.

The reason is methodological: split-role permission alone does not authorize a
fit/admission claim. The source/property gate must also establish that the row's
property mode, source envelope, provenance, and runtime legality are complete
for the exact candidate lane. Current evidence completes the labels but still
sets release-ready rows to zero.

## Outputs

- `ch3_source_property_gate_resolution.csv`
- `warning_resolution_decision.csv`
- `allowed_forbidden_claim_table.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`
""",
        encoding="utf-8",
    )

    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
