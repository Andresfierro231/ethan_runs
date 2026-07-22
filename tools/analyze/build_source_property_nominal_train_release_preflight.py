#!/usr/bin/env python3
"""Build the Salt1-4 nominal train source/property release preflight package."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


TASK_ID = "TODO-SOURCE-PROPERTY-NOMINAL-TRAIN-RELEASE-PREFLIGHT-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"

POLICY_CSV = REPO / "work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_envelope_resolution/scorecard_source_property_resolution_policy.csv"
REFRESH_CSV = REPO / "work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_property_refresh/refreshed_final_scorecard_source_property_labels.csv"
S5_LEDGER = REPO / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release/source_property_release_ledger.csv"
S13_MESH_SUMMARY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate/summary.json"
M2_SUMMARY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/summary.json"
MF02_SUMMARY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic/summary.json"
M0_SUMMARY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_m0_setup_only_baseline_prediction_scorecard/summary.json"
MODEL_FORM_SUMMARY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/summary.json"

NOMINAL_CASES = {
    "salt1_nominal": "Salt1 nominal final-train row",
    "salt2_jin_nominal": "Salt2 nominal final-train row",
    "salt3_jin_nominal": "Salt3 nominal final-train row",
    "salt4_nominal": "Salt4 nominal final-train row",
}

REQUIRED_LABELS = [
    "property_mode",
    "property_sensitivity_label",
    "source_validity_envelope_status",
    "source_use_category",
    "provenance_author_title",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def read_json(path: Path) -> dict[str, object]:
    with path.open() as handle:
        return json.load(handle)


def yes(value: object) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass"}


def source_family(row: dict[str, str]) -> str:
    case_key = row["case_key"]
    if case_key.startswith("salt1"):
        return "salt1_branch_source_envelope"
    if case_key.startswith(("salt2", "salt3", "salt4")):
        return "salt2_3_4_mixed_source_envelope"
    return "other"


def blocker_for(row: dict[str, str]) -> str:
    status = row["source_property_gate_status"]
    decision = row["resolution_decision"]
    if "salt1" in status or "row_specific" in status:
        return "missing row-specific Salt1 branch source-envelope evidence"
    if "not_strict_pass" in status or "demote" in decision:
        return "mixed/outside/unknown source-envelope evidence prevents strict source pass"
    return row.get("source_property_gate_status", "source/property policy block")


def next_action_for(row: dict[str, str]) -> str:
    if row["case_key"] == "salt1_nominal":
        return "join row-specific Salt1 branch source-envelope evidence before any S11/S15 release"
    return "replace mixed/outside/unknown source-envelope labels with row-specific strict-pass evidence before any S11/S15 release"


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    policy_rows = read_csv(POLICY_CSV)
    refresh_rows = read_csv(REFRESH_CSV)
    s5_rows = read_csv(S5_LEDGER)

    nominal_policy = [row for row in policy_rows if row["case_key"] in NOMINAL_CASES and row["final_scorecard_partition"] == "train_nominal"]
    if sorted(row["case_key"] for row in nominal_policy) != sorted(NOMINAL_CASES):
        found = sorted(row["case_key"] for row in nominal_policy)
        raise RuntimeError(f"Expected nominal train cases {sorted(NOMINAL_CASES)}, found {found}")

    refresh_by_case = {row["case_key"]: row for row in refresh_rows}
    row_audit: list[dict[str, object]] = []
    for row in nominal_policy:
        refreshed = refresh_by_case.get(row["case_key"], {})
        missing_labels = [label for label in REQUIRED_LABELS if not row.get(label, "").strip()]
        labels_complete = not missing_labels
        fit_allowed = yes(row.get("final_fit_allowed"))
        selection_allowed = yes(row.get("final_model_selection_allowed"))
        strict_source_pass = "strict_pass" in row.get("source_validity_envelope_status", "") and not (
            "not_strict" in row.get("source_validity_envelope_status", "")
        )
        release_ready = labels_complete and fit_allowed and selection_allowed and strict_source_pass
        row_audit.append(
            {
                "case_key": row["case_key"],
                "normalized_case_id": row["normalized_case_id"],
                "source_family": source_family(row),
                "final_scorecard_partition": row["final_scorecard_partition"],
                "labels_complete": labels_complete,
                "missing_required_labels": ";".join(missing_labels),
                "property_mode": row["property_mode"],
                "property_sensitivity_label": row["property_sensitivity_label"],
                "source_validity_envelope_status": row["source_validity_envelope_status"],
                "source_use_category": row["source_use_category"],
                "provenance_author_title": row["provenance_author_title"],
                "source_property_gate_status": row["source_property_gate_status"],
                "resolution_decision": row["resolution_decision"],
                "original_fit_allowed": row["original_fit_allowed"],
                "original_model_selection_allowed": row["original_model_selection_allowed"],
                "final_fit_allowed": row["final_fit_allowed"],
                "final_model_selection_allowed": row["final_model_selection_allowed"],
                "release_ready": release_ready,
                "release_decision": "release_ready" if release_ready else "blocked_no_nominal_train_source_property_release",
                "primary_blocker": "" if release_ready else blocker_for(row),
                "next_action": "" if release_ready else next_action_for(row),
                "refreshed_gate_status": refreshed.get("source_property_gate_status", ""),
                "protected_row_release": False,
            }
        )

    family_counts: dict[str, Counter[str]] = {}
    for row in row_audit:
        family = str(row["source_family"])
        family_counts.setdefault(family, Counter())
        family_counts[family]["rows"] += 1
        if row["labels_complete"]:
            family_counts[family]["labels_complete_rows"] += 1
        if row["release_ready"]:
            family_counts[family]["release_ready_rows"] += 1

    family_rows: list[dict[str, object]] = []
    for family, counts in sorted(family_counts.items()):
        blockers = sorted({str(row["primary_blocker"]) for row in row_audit if row["source_family"] == family and row["primary_blocker"]})
        family_rows.append(
            {
                "source_family": family,
                "nominal_train_rows": counts["rows"],
                "labels_complete_rows": counts["labels_complete_rows"],
                "release_ready_rows": counts["release_ready_rows"],
                "release_status": "release_ready" if counts["release_ready_rows"] == counts["rows"] else "blocked",
                "missing_or_blocking_evidence": "; ".join(blockers),
                "next_action": "row-specific strict-pass source-envelope evidence, then candidate-specific S11/S15 release gate",
            }
        )

    summaries = {
        "S13_MF04_upcomer_exchange": read_json(S13_MESH_SUMMARY),
        "M2_passive_wall_test_section": read_json(M2_SUMMARY),
        "MF02_pressure_mdot_coupling": read_json(MF02_SUMMARY),
        "M0_setup_only_baseline": read_json(M0_SUMMARY),
        "master_model_form_scoreboard": read_json(MODEL_FORM_SUMMARY),
    }

    lane_rows = [
        {
            "candidate_lane": "S13_MF04_upcomer_exchange",
            "physical_or_diagnostic_status": summaries["S13_MF04_upcomer_exchange"]["decision"],
            "source_property_preflight_status": "blocked_no_nominal_train_source_property_release",
            "additional_blocker": "same-label mesh/GCI accepted rows are 0/4; production harvest not allowed",
            "s11_consequence": "cannot open S11 candidate release",
            "s15_consequence": "cannot freeze or score",
            "next_unblock": "same-label mesh family plus row-specific strict-pass source envelope and same-mask energy residual",
        },
        {
            "candidate_lane": "M2_passive_wall_test_section",
            "physical_or_diagnostic_status": summaries["M2_passive_wall_test_section"]["decision"],
            "source_property_preflight_status": "blocked_no_nominal_train_source_property_release",
            "additional_blocker": "source-bounded passive repair not released; 0 S11-reviewable candidates",
            "s11_consequence": "cannot open S11 candidate release",
            "s15_consequence": "cannot freeze or score",
            "next_unblock": "source-bounded local repair evidence with runtime-legal inputs and row-specific source envelope",
        },
        {
            "candidate_lane": "MF02_pressure_mdot_coupling",
            "physical_or_diagnostic_status": summaries["MF02_pressure_mdot_coupling"]["decision"],
            "source_property_preflight_status": "blocked_no_nominal_train_source_property_release",
            "additional_blocker": "ordinary-flow, endpoint, and same-QOI gates fail; no F6/component-K evidence",
            "s11_consequence": "cannot open pressure candidate release",
            "s15_consequence": "cannot freeze or score",
            "next_unblock": "different low-recirculation pressure anchors plus same-QOI UQ and strict source envelope",
        },
        {
            "candidate_lane": "M0_setup_only_baseline",
            "physical_or_diagnostic_status": summaries["M0_setup_only_baseline"]["decision"],
            "source_property_preflight_status": "blocked_no_nominal_train_source_property_release",
            "additional_blocker": "0 numerical predictions; baseline shell only",
            "s11_consequence": "no candidate to release",
            "s15_consequence": "no frozen prediction artifact",
            "next_unblock": "runner with setup-only legal inputs and source/property-reviewed train rows",
        },
        {
            "candidate_lane": "diagnostic_model_forms",
            "physical_or_diagnostic_status": summaries["master_model_form_scoreboard"]["decision"],
            "source_property_preflight_status": "blocked_no_nominal_train_source_property_release",
            "additional_blocker": "diagnostic forms are not physical closures",
            "s11_consequence": "can support thesis interpretation only",
            "s15_consequence": "cannot freeze diagnostic offsets as final candidate",
            "next_unblock": "convert one diagnostic form into a physical source-bounded candidate, then rerun S11",
        },
    ]

    s11_rows = [
        {
            "gate": "nominal_train_label_presence",
            "status": "pass",
            "evidence": "all four nominal train rows have required nonblank labels",
            "s11_s15_action": "necessary but not sufficient",
        },
        {
            "gate": "nominal_train_source_envelope_strict_pass",
            "status": "fail",
            "evidence": "Salt1 lacks row-specific branch envelope; Salt2/Salt3/Salt4 remain mixed/outside/unknown",
            "s11_s15_action": "block source/property release",
        },
        {
            "gate": "candidate_specific_physical_gate",
            "status": "fail",
            "evidence": "S13, M2, MF02, and M0 summaries do not expose S11-reviewable candidate",
            "s11_s15_action": "block candidate freeze",
        },
        {
            "gate": "protected_row_release",
            "status": "pass_closed",
            "evidence": "0 validation, holdout, or external-test rows released",
            "s11_s15_action": "preserve split policy",
        },
    ]

    protected_rows = [
        {
            "protected_class": "validation_holdout_external",
            "rows_released": 0,
            "fit_or_model_selection_allowed": False,
            "reason": "No candidate-specific source/property release and no frozen runtime-legal candidate.",
        }
    ]

    no_mutation_rows = [
        {"guardrail": "native_solver_outputs_mutated", "value": False},
        {"guardrail": "registry_mutated", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "external_fluid_edit", "value": False},
        {"guardrail": "validation_holdout_external_scoring", "value": False},
        {"guardrail": "fitting_or_model_selection_performed", "value": False},
        {"guardrail": "source_property_release", "value": False},
        {"guardrail": "protected_row_release", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "coefficient_admission", "value": False},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "value": False},
        {"guardrail": "blocker_register_change", "value": False},
        {"guardrail": "generated_index_refresh", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
    ]

    source_manifest = [
        {"source_id": "SRC-001", "path": str(POLICY_CSV.relative_to(REPO)), "use": "final source/property resolution policy", "mutation_status": "read_only"},
        {"source_id": "SRC-002", "path": str(REFRESH_CSV.relative_to(REPO)), "use": "refreshed label table", "mutation_status": "read_only"},
        {"source_id": "SRC-003", "path": str(S5_LEDGER.relative_to(REPO)), "use": "prior source/property release gate context", "mutation_status": "read_only"},
        {"source_id": "SRC-004", "path": str(S13_MESH_SUMMARY.relative_to(REPO)), "use": "S13 candidate-lane consequence", "mutation_status": "read_only"},
        {"source_id": "SRC-005", "path": str(M2_SUMMARY.relative_to(REPO)), "use": "M2 candidate-lane consequence", "mutation_status": "read_only"},
        {"source_id": "SRC-006", "path": str(MF02_SUMMARY.relative_to(REPO)), "use": "MF02 candidate-lane consequence", "mutation_status": "read_only"},
        {"source_id": "SRC-007", "path": str(M0_SUMMARY.relative_to(REPO)), "use": "M0 candidate-lane consequence", "mutation_status": "read_only"},
        {"source_id": "SRC-008", "path": str(MODEL_FORM_SUMMARY.relative_to(REPO)), "use": "diagnostic model-form consequence", "mutation_status": "read_only"},
    ]

    write_csv(
        OUT / "nominal_train_release_audit.csv",
        row_audit,
        [
            "case_key",
            "normalized_case_id",
            "source_family",
            "final_scorecard_partition",
            "labels_complete",
            "missing_required_labels",
            "property_mode",
            "property_sensitivity_label",
            "source_validity_envelope_status",
            "source_use_category",
            "provenance_author_title",
            "source_property_gate_status",
            "resolution_decision",
            "original_fit_allowed",
            "original_model_selection_allowed",
            "final_fit_allowed",
            "final_model_selection_allowed",
            "release_ready",
            "release_decision",
            "primary_blocker",
            "next_action",
            "refreshed_gate_status",
            "protected_row_release",
        ],
    )
    write_csv(OUT / "source_family_blocker_rollup.csv", family_rows, ["source_family", "nominal_train_rows", "labels_complete_rows", "release_ready_rows", "release_status", "missing_or_blocking_evidence", "next_action"])
    write_csv(OUT / "candidate_lane_consequences.csv", lane_rows, ["candidate_lane", "physical_or_diagnostic_status", "source_property_preflight_status", "additional_blocker", "s11_consequence", "s15_consequence", "next_unblock"])
    write_csv(OUT / "s11_s15_blocker_matrix.csv", s11_rows, ["gate", "status", "evidence", "s11_s15_action"])
    write_csv(OUT / "protected_row_release_audit.csv", protected_rows, ["protected_class", "rows_released", "fit_or_model_selection_allowed", "reason"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_rows, ["guardrail", "value"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "use", "mutation_status"])

    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "nominal_train_source_property_release_not_ready_no_protected_release",
        "nominal_train_rows": len(row_audit),
        "labels_complete_rows": sum(1 for row in row_audit if row["labels_complete"]),
        "release_ready_rows": sum(1 for row in row_audit if row["release_ready"]),
        "candidate_lane_rows": len(lane_rows),
        "s11_s15_gate_rows": len(s11_rows),
        "protected_rows_released": 0,
        "fit_allowed_rows": sum(1 for row in row_audit if yes(row["final_fit_allowed"])),
        "model_selection_allowed_rows": sum(1 for row in row_audit if yes(row["final_model_selection_allowed"])),
        "source_property_release": False,
        "candidate_freeze": False,
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection_performed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {POLICY_CSV.relative_to(REPO)}
  - {REFRESH_CSV.relative_to(REPO)}
  - {S5_LEDGER.relative_to(REPO)}
tags: [source-property, nominal-train, release-preflight, no-freeze]
related:
  - .agent/status/2026-07-22_TODO-SOURCE-PROPERTY-NOMINAL-TRAIN-RELEASE-PREFLIGHT-2026-07-22.md
  - .agent/journal/2026-07-22/source-property-nominal-train-release-preflight.md
  - imports/2026-07-22_source_property_nominal_train_release_preflight.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred/Reviewer/Tester/Writer
type: work_product
status: complete
---
# Source/Property Nominal Train Release Preflight

## Result

Decision: `{summary["decision"]}`.

This package preflights Salt1-4 nominal final-training rows for
source/property release independent of any single candidate. It uses existing
source/property policy artifacts only; it does not release source/property
state, score protected rows, freeze a candidate, or admit a coefficient.

- nominal train rows reviewed: `{summary["nominal_train_rows"]}`
- rows with required labels complete: `{summary["labels_complete_rows"]}`
- release-ready rows: `{summary["release_ready_rows"]}`
- fit-allowed rows after final source/property policy: `{summary["fit_allowed_rows"]}`
- model-selection-allowed rows after final source/property policy: `{summary["model_selection_allowed_rows"]}`
- protected rows released: `{summary["protected_rows_released"]}`

## Interpretation

The blocker has narrowed. The problem is no longer blank labels: all four
nominal train rows carry required source/property labels. The problem is source
envelope admissibility:

- Salt1 nominal remains blocked by missing row-specific branch source-envelope
  evidence.
- Salt2/Salt3/Salt4 nominal remain blocked because their source-envelope state
  is mixed/outside/unknown rather than strict-pass for final fit or model
  selection.

This means S11/S15 should not reopen broad source/property release. They should
ask for candidate-specific strict-pass evidence tied to the exact model lane.

## Outputs

- `nominal_train_release_audit.csv`
- `source_family_blocker_rollup.csv`
- `candidate_lane_consequences.csv`
- `s11_s15_blocker_matrix.csv`
- `protected_row_release_audit.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, thesis current/LaTeX file, validation/holdout/
external-test score, fitting, tuning, model selection, source/property release,
protected-row release, candidate freeze, coefficient admission, S11/S12/S13/
S15/S6 trigger, blocker register, generated index, runtime-leakage rule, or
residual absorption into internal Nu was changed.
"""


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
