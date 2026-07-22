#!/usr/bin/env python3
"""Build a no-fit bakeoff for the section-effective hybrid pressure route."""
from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path
from statistics import mean
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21"
DATE = "2026-07-21"
SLUG = "2026-07-21_hybrid_pressure_no_fit_performance_bakeoff"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-21" / SLUG

SCORECARD = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/"
    "section_effective_pressure_scorecard.csv"
)
THREE_LEVEL = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/"
    "three_level_score.csv"
)
NEGATIVE_DISPATCH = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_negative_k_section_effective_thesis_case_dispatch/"
    "summary.json"
)
F3_STATUS = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_f6_same_qoi_uq_and_admission_gate/"
    "f3_comparison_status.csv"
)
S10_F3_TABLE = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/"
    "f3_shah_apparent_comparison_table.csv"
)
S14_F3_TABLE = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/"
    "f3_vs_f6_comparison_readiness.csv"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def dec(value: str | int | float | Decimal | None) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def fmt(value: Decimal) -> str:
    return format(value.normalize(), "f")


def decimal_mean(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return Decimal(str(mean(values)))


def split_role_audit_rows(scorecard: list[dict[str, str]], three_level: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    score_levels_by_case: dict[str, set[str]] = {}
    for row in three_level:
        score_levels_by_case.setdefault(row["case_id"], set()).add(row["score_level"])
    for row in scorecard:
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "split_role_used": "final_training_nominal_context",
                "score_levels_present": ";".join(sorted(score_levels_by_case[row["case_id"]])),
                "validation_rows_consumed": "0",
                "holdout_rows_consumed": "0",
                "external_test_rows_consumed": "0",
                "fit_or_tuning_performed": "false",
                "model_selection_performed": "false",
                "runtime_leakage_status": "pass_no_runtime_inputs_changed",
                "protected_row_status": "pass_none_consumed",
            }
        )
    return rows


def performance_rows(three_level: list[dict[str, str]], f3_status: list[dict[str, str]], s14_f3: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    levels = {
        "observed_decomposition": "Observed residual decomposition; not a predictive model.",
        "salt2_frozen_diagnostic": "Salt2 K_eff_recirc applied without refitting to all train rows.",
        "oracle_envelope_nonpredictive": "Row-local residual upper bound; explicitly nonpredictive.",
    }
    for level, interpretation in levels.items():
        level_rows = [row for row in three_level if row["score_level"] == level]
        transfer_rows = [row for row in level_rows if row["case_id"] != "salt_2"]
        abs_errors = [dec(row["abs_error_pa"]) for row in level_rows]
        transfer_errors = [dec(row["abs_error_pa"]) for row in transfer_rows]
        pct_errors = [dec(row["abs_error_percent_gross_static"]) for row in level_rows]
        rows.append(
            {
                "comparison_id": f"HPB-{len(rows) + 1:03d}",
                "method": level,
                "cases": ";".join(row["case_id"] for row in level_rows),
                "coefficient_source": "salt2_only" if level == "salt2_frozen_diagnostic" else "observed_terms",
                "numeric_status": "evaluated_no_fit",
                "max_abs_error_pa": fmt(max(abs_errors) if abs_errors else Decimal("0")),
                "mean_abs_error_pa": fmt(decimal_mean(abs_errors)),
                "transfer_max_abs_error_pa": fmt(max(transfer_errors) if transfer_errors else Decimal("0")),
                "max_abs_error_percent_gross_static": fmt(max(pct_errors) if pct_errors else Decimal("0")),
                "validation_rows_consumed": "0",
                "holdout_rows_consumed": "0",
                "external_test_rows_consumed": "0",
                "fit_or_tuning_performed": "false",
                "admission_status": "not_admitted",
                "interpretation": interpretation,
            }
        )

    f3 = f3_status[0]
    s14 = s14_f3[0]
    rows.append(
        {
            "comparison_id": f"HPB-{len(rows) + 1:03d}",
            "method": "F3_shah_apparent_baseline_status",
            "cases": "not_row_numeric_for_current_corner",
            "coefficient_source": "production_baseline_status_only",
            "numeric_status": f3["status"],
            "max_abs_error_pa": "",
            "mean_abs_error_pa": "",
            "transfer_max_abs_error_pa": "",
            "max_abs_error_percent_gross_static": "",
            "validation_rows_consumed": "0",
            "holdout_rows_consumed": "0",
            "external_test_rows_consumed": "0",
            "fit_or_tuning_performed": "false",
            "admission_status": "not_admitted",
            "interpretation": (
                f"F3/Shah comparison withheld: {f3['reason']}. "
                f"S14 status is {s14['comparison_status']} because {s14['reason']}"
            ),
        }
    )
    return rows


def residual_ownership_rows(scorecard: list[dict[str, str]]) -> list[dict[str, str]]:
    residuals = [dec(row["available_signed_residual_pa"]) for row in scorecard]
    gross = [dec(row["gross_static_pressure_rise_pa"]) for row in scorecard]
    return [
        {
            "owner": "hydrostatic_head",
            "evidence": "hydrostatic_fraction_of_gross approximately 1.0 for all rows",
            "value_summary": ";".join(row["hydrostatic_fraction_of_gross"] for row in scorecard),
            "ownership_status": "dominant_gross_static_pressure_owner",
            "allowed_use": "basis_decomposition",
            "forbidden_use": "component_K_or_F6_fit",
        },
        {
            "owner": "kinetic_correction",
            "evidence": "finite same-endpoint kinetic term is retained separately",
            "value_summary": ";".join(row["kinetic_term_pa"] for row in scorecard),
            "ownership_status": "small_separate_basis_term",
            "allowed_use": "basis_decomposition",
            "forbidden_use": "hide_inside_K",
        },
        {
            "owner": "straight_developing_reference",
            "evidence": "same-basis straight/developing correction is missing",
            "value_summary": "blocked_missing_same_basis_reference",
            "ownership_status": "blocks_ordinary_component_K",
            "allowed_use": "admission_gate",
            "forbidden_use": "infer_irreversible_component_loss",
        },
        {
            "owner": "recirculating_section_residual",
            "evidence": "available signed residual after hydrostatic and kinetic correction",
            "value_summary": ";".join(fmt(value) for value in residuals),
            "ownership_status": "section_effective_diagnostic",
            "allowed_use": "Delta_p_recirc_section thesis evidence",
            "forbidden_use": "component_K;cluster_K;F6;clipped_K;hidden_multiplier",
        },
        {
            "owner": "gross_static_pressure_rise",
            "evidence": "gross static rise is about 3 kPa but not a loss coefficient target",
            "value_summary": ";".join(fmt(value) for value in gross),
            "ownership_status": "not_target_for_K",
            "allowed_use": "context_for_hydrostatic_dominance",
            "forbidden_use": "normalize_as_local_loss",
        },
    ]


def baseline_rows(f3_status: list[dict[str, str]], s10_f3: list[dict[str, str]], s14_f3: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "source_id": "f6_same_qoi_uq_f3_status",
            "path": str(F3_STATUS.relative_to(REPO_ROOT)),
            "baseline": "F3_shah_apparent",
            "numeric_comparison_available": "false",
            "status": f3_status[0]["status"],
            "reason": f3_status[0]["reason"],
            "required_unlock": f3_status[0]["required_unlock"],
        },
        {
            "source_id": "s10_figtable_f3_status",
            "path": str(S10_F3_TABLE.relative_to(REPO_ROOT)),
            "baseline": "F3_shah_apparent",
            "numeric_comparison_available": "false",
            "status": s10_f3[0]["status"],
            "reason": s10_f3[0]["reason"],
            "required_unlock": "ordinary-flow and same-QOI admissible F6 row",
        },
        {
            "source_id": "s14_f3_readiness",
            "path": str(S14_F3_TABLE.relative_to(REPO_ROOT)),
            "baseline": s14_f3[0]["baseline"],
            "numeric_comparison_available": "false",
            "status": s14_f3[0]["comparison_status"],
            "reason": s14_f3[0]["reason"],
            "required_unlock": "F6 row passing ordinary-flow, same-QOI UQ, source/property, and endpoint gates",
        },
    ]


def decision_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "HPB-DECISION-001",
            "question": "Can the current hybrid term be used as thesis evidence?",
            "decision": "yes_thesis_evidence",
            "reason": "No-fit scorecard quantifies a signed section-effective residual and Salt2-frozen diagnostic transfer without protected rows.",
        },
        {
            "decision_id": "HPB-DECISION-002",
            "question": "Is the current hybrid term candidate-reviewable for freeze/admission?",
            "decision": "no_thesis_evidence_only",
            "reason": "Current rows fail component isolation, reverse-flow, same-QOI UQ, and F3/Shah numeric comparison readiness gates.",
        },
        {
            "decision_id": "HPB-DECISION-003",
            "question": "Can F3/Shah be beaten numerically from current evidence?",
            "decision": "not_evaluated",
            "reason": "Existing F3/Shah artifacts explicitly withhold comparison until an ordinary admissible F6 candidate exists.",
        },
    ]


def write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - {SCORECARD.relative_to(REPO_ROOT)}
  - {THREE_LEVEL.relative_to(REPO_ROOT)}
  - {F3_STATUS.relative_to(REPO_ROOT)}
  - {S14_F3_TABLE.relative_to(REPO_ROOT)}
tags: [pressure-ledger, hybrid-pressure, no-fit, bakeoff, thesis]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
  - .agent/journal/2026-07-21/hybrid-pressure-no-fit-performance-bakeoff.md
  - imports/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff.json
task: {TASK_ID}
date: {DATE}
role: Hydraulics/cfd-pp/Tester/Writer
type: work_product
status: complete
---
# Hybrid Pressure No-Fit Performance Bakeoff

## Result

This package tests the section-effective hybrid pressure route without fitting,
tuning, protected split scoring, or model selection. It compares observed
decomposition, Salt2-frozen diagnostic transfer, oracle upper bound, and the
available F3/Shah apparent baseline status.

The Salt2-frozen diagnostic transfer remains the only numeric transfer check.
Its max all-row and Salt3/Salt4 transfer absolute error is
`{summary["salt2_frozen_transfer_max_abs_error_pa"]} Pa`.

F3/Shah apparent baseline comparison is not numeric here. The existing F3/F6
artifacts record `not_evaluated_no_ordinary_candidate`; no ordinary admissible
F6 row exists for a fair F3-vs-F6 comparison.

## Decision

The current hybrid pressure term is thesis evidence only. It is useful for
residual ownership and model-form motivation, but it is not candidate-reviewable
for freeze/admission from current rows.

## Outputs

- `no_fit_performance_table.csv`
- `residual_ownership_table.csv`
- `baseline_comparison_provenance.csv`
- `split_role_audit.csv`
- `candidate_reviewability_decision.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, validation/holdout/external score, fitting, tuning,
model selection, component-K/F6/cluster-K admission, clipped K, hidden/global
multiplier, S11/S15/S6 trigger, blocker register, generated index, mixed-basis
promotion, or thesis current file is changed by this package.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"path": str(SCORECARD.relative_to(REPO_ROOT)), "use": "section-effective residual inputs", "mutation": "False"},
        {"path": str(THREE_LEVEL.relative_to(REPO_ROOT)), "use": "no-fit score levels", "mutation": "False"},
        {"path": str(NEGATIVE_DISPATCH.relative_to(REPO_ROOT)), "use": "non-admission guardrails", "mutation": "False"},
        {"path": str(F3_STATUS.relative_to(REPO_ROOT)), "use": "F3/Shah baseline comparison status", "mutation": "False"},
        {"path": str(S10_F3_TABLE.relative_to(REPO_ROOT)), "use": "thesis figure/table F3 status", "mutation": "False"},
        {"path": str(S14_F3_TABLE.relative_to(REPO_ROOT)), "use": "S14 F3-vs-F6 readiness", "mutation": "False"},
    ]


def build(out_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard = read_csv(SCORECARD)
    three_level = read_csv(THREE_LEVEL)
    f3_status = read_csv(F3_STATUS)
    s10_f3 = read_csv(S10_F3_TABLE)
    s14_f3 = read_csv(S14_F3_TABLE)

    perf = performance_rows(three_level, f3_status, s14_f3)
    ownership = residual_ownership_rows(scorecard)
    baseline = baseline_rows(f3_status, s10_f3, s14_f3)
    split = split_role_audit_rows(scorecard, three_level)
    decisions = decision_rows()

    write_csv(out_dir / "no_fit_performance_table.csv", perf, [
        "comparison_id", "method", "cases", "coefficient_source", "numeric_status",
        "max_abs_error_pa", "mean_abs_error_pa", "transfer_max_abs_error_pa",
        "max_abs_error_percent_gross_static", "validation_rows_consumed",
        "holdout_rows_consumed", "external_test_rows_consumed",
        "fit_or_tuning_performed", "admission_status", "interpretation",
    ])
    write_csv(out_dir / "residual_ownership_table.csv", ownership, [
        "owner", "evidence", "value_summary", "ownership_status", "allowed_use", "forbidden_use",
    ])
    write_csv(out_dir / "baseline_comparison_provenance.csv", baseline, [
        "source_id", "path", "baseline", "numeric_comparison_available", "status", "reason", "required_unlock",
    ])
    write_csv(out_dir / "split_role_audit.csv", split, [
        "case_id", "case_key", "split_role_used", "score_levels_present",
        "validation_rows_consumed", "holdout_rows_consumed", "external_test_rows_consumed",
        "fit_or_tuning_performed", "model_selection_performed",
        "runtime_leakage_status", "protected_row_status",
    ])
    write_csv(out_dir / "candidate_reviewability_decision.csv", decisions, [
        "decision_id", "question", "decision", "reason",
    ])
    write_csv(out_dir / "source_manifest.csv", source_manifest_rows(), ["path", "use", "mutation"])

    salt2_frozen = next(row for row in perf if row["method"] == "salt2_frozen_diagnostic")
    summary: dict[str, object] = {
        "task": TASK_ID,
        "date": DATE,
        "status": "complete",
        "scorecard_rows": len(scorecard),
        "performance_rows": len(perf),
        "residual_owner_rows": len(ownership),
        "split_role_rows": len(split),
        "baseline_rows": len(baseline),
        "decision_rows": len(decisions),
        "salt2_frozen_transfer_max_abs_error_pa": salt2_frozen["transfer_max_abs_error_pa"],
        "f3_shah_numeric_comparison_available": False,
        "f3_shah_comparison_status": f3_status[0]["status"],
        "candidate_reviewability": "thesis_evidence_only_not_candidate_reviewable",
        "component_k_admitted_rows": 0,
        "cluster_k_admitted_rows": 0,
        "f6_fit_rows": 0,
        "clipped_k_rows": 0,
        "hidden_global_multiplier_rows": 0,
        "validation_rows_consumed": 0,
        "holdout_rows_consumed": 0,
        "external_test_rows_consumed": 0,
        "fit_or_tuning_performed": False,
        "model_selection_performed": False,
        "s11_s15_s6_trigger": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(out_dir, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    summary = build(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
