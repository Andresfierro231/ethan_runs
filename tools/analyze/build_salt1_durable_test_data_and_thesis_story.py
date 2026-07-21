#!/usr/bin/env python3
"""Publish durable Salt1 test-data rows and thesis-story scorecard split."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-16"
TASK = "AGENT-453"

SALT1_PACKAGE = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_salt1_primary_evidence_admission_and_scorecard"
THERMAL_PACKAGE = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate"
MESH_PACKAGE = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_punch_list"
PRESSURE_PACKAGE = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table"

OUT = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_salt1_durable_test_data_and_thesis_story"
FIXTURE = ROOT / "tools/analyze/test_data/salt1_primary_closure_cases.csv"
THESIS = ROOT / "reports/thesis_dossier/2026-07-16_salt1_confident_use_and_forward_scorecard_story.md"
JOURNAL = ROOT / ".agent/journal/2026-07-16/salt1-durable-test-data-and-thesis-story.md"
STATUS = ROOT / ".agent/status/2026-07-16_AGENT-453.md"
IMPORT = ROOT / "imports/2026-07-16_salt1_durable_test_data_and_thesis_story.json"

SALT1_Q_RATIO = {
    "salt1_nominal": "1.00",
    "salt1_lo10q": "0.90",
    "salt1_hi10q": "1.10",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def build_salt1_fixture_rows() -> list[dict[str, object]]:
    summaries = {row["case_id"]: row for row in read_csv(SALT1_PACKAGE / "salt1_terminal_summary.csv")}
    convergence = {row["case_id"]: row for row in read_csv(SALT1_PACKAGE / "salt1_convergence_audit.csv")}
    decisions = {row["case_id"]: row for row in read_csv(SALT1_PACKAGE / "salt1_primary_evidence_decision.csv")}
    scorecard = {row["case_key"]: row for row in read_csv(SALT1_PACKAGE / "final_admission_status_scorecard.csv")}

    rows: list[dict[str, object]] = []
    for case_id in ["salt1_nominal", "salt1_lo10q", "salt1_hi10q"]:
        summary = summaries[case_id]
        audit = convergence[case_id]
        decision = decisions[case_id]
        score = scorecard[case_id]
        is_nominal = case_id == "salt1_nominal"
        rows.append({
            "case_key": case_id,
            "run_key": summary["run_key"],
            "q_ratio": SALT1_Q_RATIO[case_id],
            "fixture_group": "salt1_primary_closure_cases",
            "test_dataset_role": "primary_nominal_anchor" if is_nominal else "primary_q_perturbation_anchor",
            "admission_status": score["admission_status"],
            "recommended_use": decision["recommended_use"],
            "confidence_label": "confident_with_operational_stop_provenance",
            "steady_state_verdict": score["steady_state_verdict"],
            "terminal_monitor_verdict": summary["all_monitor_verdicts"],
            "suspicious_monitor_flag": summary["suspicious_monitor_flag"],
            "total_Q_drift_W": summary["total_Q_drift_W"],
            "max_mdot_rel_drift": summary["max_mdot_rel_drift"],
            "max_tp_abs_drift_K": summary["max_tp_abs_drift_K"],
            "max_tw_abs_drift_K": summary["max_tw_abs_drift_K"],
            "has_stopAt_writeNow": audit["has_stopAt_writeNow"],
            "convergence_monitor_policy": "diagnostic_only_continue_to_configured_endTime",
            "foam_fatal_in_tail": audit["foam_fatal_in_tail"],
            "cancelled_in_tail": audit["cancelled_in_tail"],
            "latest_time_in_tail_s": audit["latest_time_in_tail_s"],
            "source_case_path": summary["source_case_path"],
            "required_future_assertion": (
                "must remain admitted primary closure evidence unless a later dated review records a new failed gate"
            ),
            "disallowed_future_claim": "do not call a clean endTime completion; preserve operational cancellation/stop provenance",
            "primary_evidence_source": rel(SALT1_PACKAGE / "README.md"),
        })
    return rows


def build_future_integration_rows() -> list[dict[str, str]]:
    return [
        {
            "integration_point": "final_admission_scorecard",
            "required_update": "include salt1_nominal, salt1_lo10q, and salt1_hi10q as admitted rows",
            "guardrail": "do not demote Salt1 to diagnostic/context-only unless a newer dated gate overturns AGENT-448",
            "evidence": rel(SALT1_PACKAGE / "final_admission_status_scorecard.csv"),
        },
        {
            "integration_point": "closure_regression_tests",
            "required_update": "load tools/analyze/test_data/salt1_primary_closure_cases.csv or assert equivalent rows",
            "guardrail": "tests must check admitted status, no suspicious drift, diagnostic-only convergence monitor, no FOAM FATAL",
            "evidence": rel(FIXTURE),
        },
        {
            "integration_point": "thesis_story",
            "required_update": "present Salt1 as confident primary evidence with provenance caveat",
            "guardrail": "separate admitted Salt1 evidence from still-diagnostic hydraulic/mesh/internal-Nu coefficient claims",
            "evidence": rel(THESIS),
        },
        {
            "integration_point": "future_test_split",
            "required_update": "keep Salt1 q-ratio labels visible: nominal 1.00, lo10q 0.90, hi10q 1.10",
            "guardrail": "do not merge perturbed-Q rows into nominal baselines or hide q-ratio labels",
            "evidence": rel(FIXTURE),
        },
    ]


def build_thesis_story_rows() -> list[dict[str, str]]:
    salt1_summary = load_json(SALT1_PACKAGE / "summary.json")
    thermal_summary = load_json(THERMAL_PACKAGE / "summary.json")
    mesh_summary = load_json(MESH_PACKAGE / "summary.json")
    pressure_summary = load_json(PRESSURE_PACKAGE / "summary.json")
    return [
        {
            "story_lane": "implemented_predictive_model",
            "defensible_claim": (
                "A setup-only predictive path is implemented far enough to continue scoring heater and HX/cooler submodels."
            ),
            "current_status": "implemented_but_final_forward_v1_partly_blocked",
            "scorecard_use": "Report model implementation and legal runtime-input gates separately from final prediction admission.",
            "evidence": rel(THERMAL_PACKAGE / "README.md"),
            "limitation": (
                f"Internal-Nu fit-admissible rows remain {thermal_summary['internal_nu_fit_allowed_rows']}; "
                "do not tune Nu to absorb residuals."
            ),
        },
        {
            "story_lane": "admitted_primary_evidence",
            "defensible_claim": "Salt1 nominal, -10Q, and +10Q are admitted primary closure evidence with terminal-window confidence.",
            "current_status": "admitted",
            "scorecard_use": "Use in final scorecards and regression fixtures as admitted evidence, not context-only diagnostics.",
            "evidence": rel(SALT1_PACKAGE / "README.md"),
            "limitation": (
                f"Suspicious Salt1 cases: {len(salt1_summary['salt1_suspicious_cases'])}; "
                "preserve operational stop/cancellation provenance."
            ),
        },
        {
            "story_lane": "diagnostic_evidence",
            "defensible_claim": "Pressure ladders and current PM5/F6/upcomer evidence are useful diagnostics, but not admitted coefficients.",
            "current_status": "diagnostic_only",
            "scorecard_use": "Use for blocker narrowing and next-step selection, not final f_D/K/Nu coefficient claims.",
            "evidence": rel(PRESSURE_PACKAGE / "README.md"),
            "limitation": f"Pressure true-fit rows: {pressure_summary['true_fit_rows']}; recirc-blocked branch rows: {pressure_summary['recirc_mask_blocked_branch_rows']}.",
        },
        {
            "story_lane": "admission_gates",
            "defensible_claim": "The thesis can be defended by showing which gates admit evidence and which gates prevent overclaiming.",
            "current_status": "gate_discipline_active",
            "scorecard_use": "Make admitted, validation-only, diagnostic-only, and blocked statuses first-class scorecard columns.",
            "evidence": rel(SALT1_PACKAGE / "final_admission_status_scorecard.csv"),
            "limitation": "Admission status is not ambition; diagnostic usefulness does not imply closure-fit admission.",
        },
        {
            "story_lane": "unresolved_blockers",
            "defensible_claim": "Remaining blockers are bounded and named rather than hidden: mesh/GCI, predictive submodel validation, upcomer onset, and F6 friction.",
            "current_status": "partly_blocked",
            "scorecard_use": "Keep final forward-v1 partly blocked while presenting implemented and diagnostic results honestly.",
            "evidence": rel(MESH_PACKAGE / "README.md"),
            "limitation": f"Closure-QOI admitted-only candidates now: {mesh_summary['admitted_only_candidate_count']}; extraction/reconciliation queue rows: {mesh_summary['extraction_queue_count']}.",
        },
    ]


def write_readme(fixture_rows: list[dict[str, object]], story_rows: list[dict[str, str]]) -> None:
    admitted = sum(1 for row in fixture_rows if row["admission_status"] == "admitted")
    lines = [
        "---",
        "provenance:",
        f"  - {rel(SALT1_PACKAGE / 'README.md')}",
        f"  - {rel(THERMAL_PACKAGE / 'README.md')}",
        f"  - {rel(MESH_PACKAGE / 'README.md')}",
        f"  - {rel(PRESSURE_PACKAGE / 'README.md')}",
        "tags: [salt1, test-data, thesis-story, final-scorecard, admission]",
        "related:",
        f"  - {rel(THESIS)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Coordinator/cfd-pp/Forward-pred/Writer/Tester",
        "type: work_product",
        "status: complete",
        "---",
        "# Salt1 Durable Test Data And Thesis Story",
        "",
        "## Decision",
        "",
        f"Salt1 durable test-data integration: `{admitted}/3` rows admitted.",
        "",
        "Future scorecards and regression tests should treat `salt1_nominal`, "
        "`salt1_lo10q`, and `salt1_hi10q` as admitted primary closure evidence "
        "unless a later dated review records a new failed gate. The confidence "
        "boundary is provenance, not drift: these remain operational stop/cancel "
        "terminal harvests, not clean endTime completions.",
        "",
        "## Thesis Use",
        "",
        "The thesis story remains defensible if final forward-v1 is partly blocked, "
        "provided every table separates implemented predictive model, admitted "
        "primary evidence, diagnostic evidence, admission gates, and unresolved "
        "blockers.",
        "",
        "## Files",
        "",
        "- `salt1_primary_closure_cases.csv`: canonical dated Salt1 admitted fixture rows.",
        "- `tools/analyze/test_data/salt1_primary_closure_cases.csv`: stable repo-local fixture copy.",
        "- `future_integration_contract.csv`: where future work must keep Salt1 visible.",
        "- `thesis_story_parallel_scorecard.csv`: thesis-story lanes parallel to final scorecard status.",
        "- `summary.json`: counts and guardrail flags.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_thesis_doc(story_rows: list[dict[str, str]]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'README.md')}",
        f"  - {rel(SALT1_PACKAGE / 'README.md')}",
        f"  - {rel(THERMAL_PACKAGE / 'README.md')}",
        f"  - {rel(PRESSURE_PACKAGE / 'README.md')}",
        f"  - {rel(MESH_PACKAGE / 'README.md')}",
        "tags: [thesis-dossier, salt1, final-scorecard, forward-v1, admission]",
        "related:",
        f"  - {rel(OUT / 'thesis_story_parallel_scorecard.csv')}",
        "  - reports/thesis_dossier/README.md",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Writer/Forward-pred/cfd-pp",
        "type: report",
        "status: complete",
        "---",
        "# Salt1 Confident Use And Forward Scorecard Story",
        "",
        "## Core Claim",
        "",
        "Salt1 is now part of the admitted primary closure evidence set. The reason "
        "to preserve caution is provenance, not lack of stationarity: Salt1 "
        "nominal, -10Q, and +10Q are operational terminal harvests with clean "
        "terminal drift checks and diagnostic-only convergence monitors.",
        "",
        "## Thesis Framing",
        "",
        "The thesis does not need to pretend final forward-v1 is fully unblocked. "
        "It can defend a rigorous workflow: implemented predictive pieces are "
        "reported as implemented, diagnostics are used to locate residuals and "
        "failure modes, admission gates prevent coefficient overclaiming, and "
        "remaining blockers are named explicitly.",
        "",
        "## Parallel Scorecard",
        "",
        "| lane | current status | thesis use | limitation |",
        "| --- | --- | --- | --- |",
    ]
    for row in story_rows:
        lines.append(
            f"| {row['story_lane']} | {row['current_status']} | "
            f"{row['scorecard_use']} | {row['limitation']} |"
        )
    lines.extend([
        "",
        "## Salt1 Rules For Future Tables",
        "",
        "- Include `salt1_nominal`, `salt1_lo10q`, and `salt1_hi10q` in closure test data.",
        "- Keep q-ratio and operational stop/cancel provenance visible.",
        "- Do not silently revert Salt1 to context-only wording unless a newer dated review supersedes AGENT-448/453.",
        "- Keep hydraulic F6, pressure-ladder, mesh/GCI, and internal-Nu coefficient claims separate from Salt1 evidence admission.",
    ])
    THESIS.write_text("\n".join(lines) + "\n")


def main() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    fixture_rows = build_salt1_fixture_rows()
    integration_rows = build_future_integration_rows()
    story_rows = build_thesis_story_rows()

    fixture_fields = [
        "case_key", "run_key", "q_ratio", "fixture_group", "test_dataset_role",
        "admission_status", "recommended_use", "confidence_label", "steady_state_verdict",
        "terminal_monitor_verdict", "suspicious_monitor_flag", "total_Q_drift_W",
        "max_mdot_rel_drift", "max_tp_abs_drift_K", "max_tw_abs_drift_K",
        "has_stopAt_writeNow", "convergence_monitor_policy", "foam_fatal_in_tail",
        "cancelled_in_tail", "latest_time_in_tail_s", "source_case_path",
        "required_future_assertion", "disallowed_future_claim", "primary_evidence_source",
    ]
    write_csv(OUT / "salt1_primary_closure_cases.csv", fixture_rows, fixture_fields)
    write_csv(FIXTURE, fixture_rows, fixture_fields)
    write_csv(OUT / "future_integration_contract.csv", integration_rows, [
        "integration_point", "required_update", "guardrail", "evidence",
    ])
    write_csv(OUT / "thesis_story_parallel_scorecard.csv", story_rows, [
        "story_lane", "defensible_claim", "current_status", "scorecard_use", "evidence", "limitation",
    ])
    write_readme(fixture_rows, story_rows)
    write_thesis_doc(story_rows)

    status_counts = Counter(row["admission_status"] for row in fixture_rows)
    summary = {
        "task": TASK,
        "salt1_fixture_rows": len(fixture_rows),
        "salt1_fixture_status_counts": dict(status_counts),
        "all_salt1_rows_admitted": status_counts == {"admitted": 3},
        "story_lanes": [row["story_lane"] for row in story_rows],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "outputs": [
            rel(OUT / "README.md"),
            rel(OUT / "salt1_primary_closure_cases.csv"),
            rel(FIXTURE),
            rel(OUT / "future_integration_contract.csv"),
            rel(OUT / "thesis_story_parallel_scorecard.csv"),
            rel(THESIS),
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "---\n"
        f"provenance:\n  - {rel(OUT / 'README.md')}\n  - {rel(THESIS)}\n"
        "tags: [salt1, test-data, thesis-story, final-scorecard]\n"
        f"related:\n  - {rel(OUT / 'summary.json')}\n"
        f"task: {TASK}\n"
        f"date: {DATE}\n"
        "role: Coordinator/cfd-pp/Forward-pred/Writer/Tester\n"
        "type: journal\n"
        "status: complete\n"
        "---\n"
        "# Salt1 Durable Test Data And Thesis Story\n\n"
        "Published stable Salt1 primary-closure fixture rows, a dated integration "
        "contract, and thesis wording that separates implemented predictive model, "
        "diagnostic evidence, admission gates, and unresolved blockers.\n"
    )
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "---\n"
        f"provenance:\n  - {rel(OUT / 'README.md')}\n  - {rel(FIXTURE)}\n"
        "tags: [salt1, test-data, thesis-story]\n"
        f"related:\n  - {rel(JOURNAL)}\n"
        f"task: {TASK}\n"
        f"date: {DATE}\n"
        "role: Coordinator/cfd-pp/Forward-pred/Writer/Tester\n"
        "type: status\n"
        "status: complete\n"
        "---\n"
        "# AGENT-453 Status\n\n"
        "STATUS: COMPLETE 2026-07-16.\n\n"
        "Salt1 fixture rows are admitted and copied to `tools/analyze/test_data/`. "
        "The thesis story has been updated to use Salt1 confidently while keeping "
        "diagnostic evidence, admission gates, and unresolved blockers separate.\n"
    )
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.write_text(json.dumps({
        "task": TASK,
        "date": DATE,
        "objective": "Make Salt1 durable in future test data and thesis scorecard story.",
        "outputs": summary["outputs"] + [rel(JOURNAL), rel(STATUS)],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
    }, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
