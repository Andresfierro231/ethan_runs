#!/usr/bin/env python3
"""Build the thesis evidence packet CFD legal-use matrix."""

from __future__ import annotations

import csv
import json
from pathlib import Path


TASK_ID = "TODO-THESIS-EVIDENCE-PACKET-CFD-LEGAL-USE-MATRIX-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix"

SPLIT_TABLE = REPO / "work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/split_legal_case_table.csv"
PM10_TABLE = REPO / "work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/pm10_split_use_decision.csv"
PM10_SUMMARY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/summary.json"
M0_RUNTIME_AUDIT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard/runtime_input_audit.csv"
N1_RUNTIME_AUDIT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate/runtime_input_audit.csv"
CH3_CFD_DB = REPO / "reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md"
SPLIT_POLICY_NOTE = REPO / "reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md"
CLAIM_LEDGER = REPO / "reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def legal_use_rows() -> list[dict[str, object]]:
    return [
        {
            "evidence_class": "native OpenFOAM solver outputs",
            "allowed_thesis_use": "read-only provenance, convergence context, postprocessed diagnostic evidence",
            "forbidden_use": "direct mutation, final-score target edits, or runtime predictor injection",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "no",
            "protected_score_allowed_now": "no",
            "reason": "Native outputs are observed CFD results, not setup-only predictor inputs.",
        },
        {
            "evidence_class": "postprocessed CFD QoI ledgers",
            "allowed_thesis_use": "finite-QoI tables, residual attribution, closure blocker diagnosis",
            "forbidden_use": "turning realized mdot, wall heat flux, cooler duty, temperatures, or residuals into predictive runtime inputs",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "diagnostic only unless predeclared train-only release passes",
            "protected_score_allowed_now": "no",
            "reason": "QOI ledgers are evidence reductions from solved fields.",
        },
        {
            "evidence_class": "nominal Salt1-Salt4 final train rows",
            "allowed_thesis_use": "train-only fit or attribution only after candidate-specific legal and source/property gates",
            "forbidden_use": "validation, holdout, external-test scoring, or freeze by train-only agreement",
            "runtime_input_allowed": "setup-only inputs only",
            "fit_or_model_selection_allowed": "blocked by current source/property release",
            "protected_score_allowed_now": "no",
            "reason": "The split allows training in principle, but current source/property release is not ready.",
        },
        {
            "evidence_class": "training-support perturbation rows",
            "allowed_thesis_use": "diagnostic trend support and uncertainty context",
            "forbidden_use": "expanding the final train set without a new split policy",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "no",
            "protected_score_allowed_now": "no",
            "reason": "They are admitted as support diagnostics, not final-training rows.",
        },
        {
            "evidence_class": "PM5 holdout rows",
            "allowed_thesis_use": "future blind score only after independently frozen candidate",
            "forbidden_use": "fit, tuning, model selection, or current protected scoring",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "no",
            "protected_score_allowed_now": "no",
            "reason": "Holdout rows must remain blind until freeze.",
        },
        {
            "evidence_class": "PM10 terminal evidence rows",
            "allowed_thesis_use": "diagnostic terminal evidence and future holdout planning",
            "forbidden_use": "fit, model selection, runtime input, or current protected score",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "no",
            "protected_score_allowed_now": "no",
            "reason": "Terminal evidence exists but the rows remain future blind holdout evidence.",
        },
        {
            "evidence_class": "val_salt2 external-test row",
            "allowed_thesis_use": "external score only after independent freeze",
            "forbidden_use": "candidate tuning, runtime input, or current score",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "no",
            "protected_score_allowed_now": "no",
            "reason": "External-test data must not influence model construction.",
        },
        {
            "evidence_class": "negative and blocked results",
            "allowed_thesis_use": "scientific evidence for model-form limits, missing gates, and overclaim prevention",
            "forbidden_use": "renaming a failed diagnostic as a frozen predictive closure",
            "runtime_input_allowed": "no",
            "fit_or_model_selection_allowed": "no",
            "protected_score_allowed_now": "no",
            "reason": "A blocked path can support the thesis without becoming a prediction.",
        },
    ]


def case_rows(split_rows: list[dict[str, str]], pm10_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    pm10_by_key = {row["case_key"]: row for row in pm10_rows}
    rows: list[dict[str, object]] = []
    for row in split_rows:
        pm10 = pm10_by_key.get(row["case_key"])
        blind_now = pm10["blind_score_allowed_now"] if pm10 else row["blind_score_allowed_now"]
        use_now = pm10["use_now"] if pm10 else row["use_in_final_scorecard"]
        guardrail = pm10["guardrail"] if pm10 else row["guardrail"]
        rows.append(
            {
                "case_key": row["case_key"],
                "corrected_scorecard_role": row["corrected_scorecard_role"],
                "final_fit_allowed": row["final_fit_allowed"],
                "final_model_selection_allowed": row["final_model_selection_allowed"],
                "blind_score_allowed_now": blind_now,
                "use_now": use_now,
                "legal_disposition": guardrail,
                "terminal_update": pm10["terminal_admission_update"] if pm10 else "",
            }
        )
    return rows


def runtime_bans() -> list[dict[str, object]]:
    return [
        {
            "forbidden_input": "CFD_mdot",
            "runtime_use_allowed": "no",
            "source_basis": rel(M0_RUNTIME_AUDIT),
            "reason": "forbidden runtime input: mass flow from CFD is an observed result and would leak the target solution.",
        },
        {
            "forbidden_input": "realized_CFD_wallHeatFlux",
            "runtime_use_allowed": "no",
            "source_basis": rel(M0_RUNTIME_AUDIT),
            "reason": "forbidden runtime input: realized wall flux is post-solve evidence, not setup-known heat input.",
        },
        {
            "forbidden_input": "imposed_CFD_cooler_duty",
            "runtime_use_allowed": "no",
            "source_basis": rel(M0_RUNTIME_AUDIT),
            "reason": "forbidden runtime input: cooler duty is not a released setup-only predictor for candidate scoring.",
        },
        {
            "forbidden_input": "validation_holdout_external_temperatures",
            "runtime_use_allowed": "no",
            "source_basis": rel(M0_RUNTIME_AUDIT),
            "reason": "forbidden runtime input: target temperatures are score targets and cannot drive predictions.",
        },
        {
            "forbidden_input": "protected_holdout_or_external_residuals",
            "runtime_use_allowed": "no",
            "source_basis": rel(M0_RUNTIME_AUDIT),
            "reason": "forbidden runtime input: protected residuals cannot be used for tuning or hidden multipliers.",
        },
        {
            "forbidden_input": "exact_target_window_Q_wall_W",
            "runtime_use_allowed": "no",
            "source_basis": rel(N1_RUNTIME_AUDIT),
            "reason": "forbidden runtime input: target-window wall heat is diagnostic until same-QOI UQ and production gates pass.",
        },
    ]


def writer_claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim_type": "safe",
            "claim_text": "CFD evidence can be used to diagnose why candidate paths remain blocked.",
            "boundary": "Do not turn that evidence into runtime inputs or protected scores.",
        },
        {
            "claim_type": "safe",
            "claim_text": "PM10 terminal evidence is available for future blind-holdout planning.",
            "boundary": "It is not a current scorecard result.",
        },
        {
            "claim_type": "safe",
            "claim_text": "Negative S12/S13/pressure results strengthen the model-admission argument.",
            "boundary": "They are evidence of blocked gates, not admitted closures.",
        },
        {
            "claim_type": "unsafe",
            "claim_text": "A candidate is final because train rows match.",
            "boundary": "Train-only agreement cannot justify freeze, validation, holdout, or external scoring.",
        },
        {
            "claim_type": "unsafe",
            "claim_text": "Use CFD mdot or measured temperatures to improve runtime prediction.",
            "boundary": "forbidden: that would violate the runtime input contract.",
        },
    ]


def figure_table_targets() -> list[dict[str, object]]:
    return [
        {
            "target_id": "TABLE-CFD-LEGAL-USE-MATRIX",
            "chapter": "Ch3/Ch6",
            "purpose": "Define allowed and forbidden uses of CFD artifacts by evidence class.",
            "source_output": "cfd_legal_use_matrix.csv",
        },
        {
            "target_id": "TABLE-CASE-SPLIT-LEGAL-USE",
            "chapter": "Ch4/Ch6",
            "purpose": "Preserve train/support/holdout/external separation.",
            "source_output": "case_split_legal_use_table.csv",
        },
        {
            "target_id": "TABLE-RUNTIME-FORBIDDEN-INPUTS",
            "chapter": "Ch5/Ch6",
            "purpose": "Show runtime legality bans for predictive candidates.",
            "source_output": "runtime_forbidden_input_bans.csv",
        },
        {
            "target_id": "TABLE-WRITER-CLAIM-BOUNDARY",
            "chapter": "Ch7/Ch8",
            "purpose": "Provide exact safe/unsafe language for negative and blocked results.",
            "source_output": "writer_claim_boundary.csv",
        },
    ]


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    split_rows = read_csv(SPLIT_TABLE)
    pm10_rows = read_csv(PM10_TABLE)
    pm10_summary = read_json(PM10_SUMMARY)

    legal_rows = legal_use_rows()
    split_use_rows = case_rows(split_rows, pm10_rows)
    ban_rows = runtime_bans()
    claim_rows = writer_claim_rows()
    target_rows = figure_table_targets()
    source_manifest = [
        {"source_id": "split_legal_case_table", "path": rel(SPLIT_TABLE), "use": "case split legal-use basis", "mutation_status": "read_only"},
        {"source_id": "pm10_split_use_decision", "path": rel(PM10_TABLE), "use": "PM10 terminal update overlay", "mutation_status": "read_only"},
        {"source_id": "pm10_summary", "path": rel(PM10_SUMMARY), "use": "PM10 guardrail counts", "mutation_status": "read_only"},
        {"source_id": "m0_runtime_audit", "path": rel(M0_RUNTIME_AUDIT), "use": "runtime forbidden input basis", "mutation_status": "read_only"},
        {"source_id": "n1_runtime_audit", "path": rel(N1_RUNTIME_AUDIT), "use": "frozen-candidate gate runtime basis", "mutation_status": "read_only"},
        {"source_id": "ch3_cfd_database", "path": rel(CH3_CFD_DB), "use": "thesis evidence context", "mutation_status": "read_only"},
        {"source_id": "split_policy_note", "path": rel(SPLIT_POLICY_NOTE), "use": "split-policy prose context", "mutation_status": "read_only"},
        {"source_id": "claim_ledger", "path": rel(CLAIM_LEDGER), "use": "claim-boundary context", "mutation_status": "read_only"},
    ]
    no_mutation_rows = [
        {"guardrail": "native_output_mutation", "value": "False"},
        {"guardrail": "registry_or_admission_mutation", "value": "False"},
        {"guardrail": "scheduler_action", "value": "False"},
        {"guardrail": "fluid_or_external_edit", "value": "False"},
        {"guardrail": "validation_holdout_external_scoring", "value": "False"},
        {"guardrail": "final_score", "value": "not_performed"},
        {"guardrail": "source_property_release", "value": "False"},
        {"guardrail": "candidate_freeze", "value": "False"},
    ]

    write_csv(OUT / "cfd_legal_use_matrix.csv", legal_rows, ["evidence_class", "allowed_thesis_use", "forbidden_use", "runtime_input_allowed", "fit_or_model_selection_allowed", "protected_score_allowed_now", "reason"])
    write_csv(OUT / "case_split_legal_use_table.csv", split_use_rows, ["case_key", "corrected_scorecard_role", "final_fit_allowed", "final_model_selection_allowed", "blind_score_allowed_now", "use_now", "legal_disposition", "terminal_update"])
    write_csv(OUT / "runtime_forbidden_input_bans.csv", ban_rows, ["forbidden_input", "runtime_use_allowed", "source_basis", "reason"])
    write_csv(OUT / "writer_claim_boundary.csv", claim_rows, ["claim_type", "claim_text", "boundary"])
    write_csv(OUT / "figure_table_targets.csv", target_rows, ["target_id", "chapter", "purpose", "source_output"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "use", "mutation_status"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_rows, ["guardrail", "value"])

    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "cfd_evidence_legal_use_matrix_ready_no_scoring_no_runtime_leakage",
        "evidence_class_rows": len(legal_rows),
        "case_split_rows": len(split_use_rows),
        "runtime_forbidden_input_rows": len(ban_rows),
        "writer_claim_boundary_rows": len(claim_rows),
        "pm10_terminal_evidence_admitted_rows": pm10_summary.get("terminal_evidence_admitted_rows"),
        "pm10_protected_score_allowed_now_rows": pm10_summary.get("protected_score_allowed_now_rows"),
        "current_protected_score_allowed": False,
        "validation_holdout_external_scoring": False,
        "final_score": "not_performed",
        "source_property_release": False,
        "candidate_freeze": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "runtime_leakage_detected": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {rel(SPLIT_TABLE)}
  - {rel(PM10_TABLE)}
  - {rel(M0_RUNTIME_AUDIT)}
  - {rel(N1_RUNTIME_AUDIT)}
tags: [thesis, cfd, legal-use, runtime-contract, no-score]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thesis-evidence-packet-cfd-legal-use-matrix.md
  - imports/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix.json
task: {TASK_ID}
date: {DATE}
role: Writer/Reviewer/Tester
type: work_product
status: complete
---
# CFD Legal-Use Matrix

Decision: `{summary["decision"]}`.

This packet gives the external thesis writer and later model-admission agents a
single table set for legal CFD evidence use. It separates thesis evidence from
runtime prediction inputs and preserves the train/support/holdout/external-test
split.

Key outcomes:

- evidence classes: `{summary["evidence_class_rows"]}`
- case split rows: `{summary["case_split_rows"]}`
- explicitly forbidden runtime input rows: `{summary["runtime_forbidden_input_rows"]}`
- PM10 terminal evidence rows admitted for future planning: `{summary["pm10_terminal_evidence_admitted_rows"]}`
- current protected score allowed: `{summary["current_protected_score_allowed"]}`

Outputs:

- `cfd_legal_use_matrix.csv`
- `case_split_legal_use_table.csv`
- `runtime_forbidden_input_bans.csv`
- `writer_claim_boundary.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

Only the files listed above are canonical regenerated outputs for this packet.
Additional CSV/Markdown files in this directory came from a near-simultaneous
draft packet pass and are retained as supplemental, noncanonical material until
a later cleanup task explicitly reviews or removes them.

Guardrails: no native CFD/OpenFOAM output, registry/admission state, scheduler
state, Fluid source, external repository, validation/holdout/external-test
score, final score, source/property release, candidate freeze, or runtime input
contract was changed.
"""


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
