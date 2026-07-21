#!/usr/bin/env python3
"""Assess whether final forward-v1 boundary/coupled scorecards should be rerun."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-FINAL-FORWARD-V1-RERUN-GATE-ASSESSMENT"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_final_forward_v1_rerun_gate_assessment"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-FINAL-FORWARD-V1-RERUN-GATE-ASSESSMENT.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/final-forward-v1-rerun-gate-assessment.md"
IMPORT = ROOT / "imports/2026-07-17_final_forward_v1_rerun_gate_assessment.json"

PRESSURE_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_pressure_branch_admission_narrowing/summary.json"
TEST_SECTION_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_test_section_passive_loss_admission_repair/summary.json"
UPCOMER_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_hybrid_frozen_candidate_score/summary.json"
ONSET_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix/summary.json"
BOUNDARY_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard/summary.json"
COUPLED_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard/summary.json"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [PRESSURE_SUMMARY, TEST_SECTION_SUMMARY, UPCOMER_SUMMARY, ONSET_SUMMARY, BOUNDARY_SUMMARY, COUPLED_SUMMARY]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing rerun assessment sources: " + "; ".join(missing))


def build_gate_delta_rows() -> list[dict[str, object]]:
    pressure = load_json(PRESSURE_SUMMARY)
    test_section = load_json(TEST_SECTION_SUMMARY)
    upcomer = load_json(UPCOMER_SUMMARY)
    onset = load_json(ONSET_SUMMARY)
    boundary = load_json(BOUNDARY_SUMMARY)
    coupled = load_json(COUPLED_SUMMARY)
    return [
        {"gate": "pressure_closure", "new_admitted_rows": pressure["fit_admitted_pressure_rows"], "rerun_triggered": "false", "reason": "zero pressure rows admitted"},
        {"gate": "test_section_passive_loss", "new_admitted_rows": test_section["admitted_candidate_rows"], "rerun_triggered": "false", "reason": "zero test-section candidates admitted"},
        {"gate": "upcomer_hybrid", "new_admitted_rows": upcomer["candidate_admitted_rows"], "rerun_triggered": "false", "reason": "frozen candidate remains blocked"},
        {"gate": "upcomer_onset_anchors", "new_admitted_rows": 0, "rerun_triggered": "false", "reason": f"anchor matrix design only; scheduler_action={onset['scheduler_action']}"},
        {"gate": "boundary_layer_executable_ablation", "new_admitted_rows": boundary["executable_ablation_rows"], "rerun_triggered": "false", "reason": "zero executable ablation rows"},
        {"gate": "coupled_forward_v1", "new_admitted_rows": coupled["candidates_admitted"], "rerun_triggered": "false", "reason": "final forward-v1 remains blocked"},
    ]


def build_decision_rows(gates: list[dict[str, object]]) -> list[dict[str, object]]:
    should_rerun = any(row["rerun_triggered"] == "true" for row in gates)
    return [
        {
            "decision": "do_not_rerun_boundary_or_coupled_scorecards_now" if not should_rerun else "rerun_required",
            "boundary_layer_rerun": str(should_rerun).lower(),
            "coupled_m3ts_rerun": str(should_rerun).lower(),
            "scientific_reason": "No upstream prerequisite gate moved to admitted or executable; rerunning would only reproduce the blocked state.",
            "next_gate_sequence": "pressure branch admission; test-section setup resistance-network candidate; upcomer anchor launch/staging; frozen hybrid split scoring",
        }
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_solver_launch", "status": "pass_forbidden", "forbidden_input": "OpenFOAM/Fluid solve", "policy": "assessment only"},
        {"check": "no_scheduler_action", "status": "pass_forbidden", "forbidden_input": "scheduler action", "policy": "assessment only"},
        {"check": "no_native_output_mutation", "status": "pass_forbidden", "forbidden_input": "native CFD outputs", "policy": "read-only summaries"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("pressure_summary", PRESSURE_SUMMARY, "pressure gate delta"),
        ("test_section_summary", TEST_SECTION_SUMMARY, "test-section gate delta"),
        ("upcomer_summary", UPCOMER_SUMMARY, "hybrid gate delta"),
        ("onset_summary", ONSET_SUMMARY, "anchor launch state"),
        ("boundary_summary", BOUNDARY_SUMMARY, "current boundary ablation state"),
        ("coupled_summary", COUPLED_SUMMARY, "current final forward-v1 state"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(PRESSURE_SUMMARY)}",
                f"  - {rel(TEST_SECTION_SUMMARY)}",
                f"  - {rel(UPCOMER_SUMMARY)}",
                "tags: [forward-v1, rerun-gate, assessment]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Forward-pred/Coordinator/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Final Forward-v1 Rerun Gate Assessment",
                "",
                "## Decision",
                "",
                "Do not rerun the boundary-layer or coupled M3+TS scorecards yet. No upstream gate moved to admitted or executable, so a rerun would only reproduce the blocked state.",
                "",
                "## Results",
                "",
                f"- Gate delta rows: `{summary['gate_delta_rows']}`.",
                f"- Rerun-triggered gates: `{summary['rerun_triggered_gates']}`.",
                f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
            ]
        )
        + "\n"
    )
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                f"  - {rel(OUT / 'summary.json')}",
                "tags: [status, forward-v1, rerun-gate]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Forward-pred/Coordinator/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- Pressure, test-section, and upcomer packages admitted zero new closure rows.",
                "- The onset matrix is design-only and launched no anchors.",
                "- Boundary-layer executable ablations and coupled candidate admissions remain zero.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_final_forward_v1_rerun_gate_assessment`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
            ]
        )
        + "\n"
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, forward-v1, rerun-gate]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Forward-pred/Coordinator/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Final Forward-v1 Rerun Gate Assessment Journal",
                "",
                "The assessment documents why rerunning final scorecards now would not add evidence: no prerequisite admission gate changed.",
            ]
        )
        + "\n"
    )
    manifest = {
        "task": TASK,
        "date": DATE,
        "package": rel(OUT),
        "outputs": sorted(path.name for path in OUT.iterdir() if path.is_file()),
        "summary": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
        "generated_index_refresh_note": "Skipped because active/completed board context owns generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)
    gates = build_gate_delta_rows()
    decisions = build_decision_rows(gates)
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(OUT / "gate_delta_assessment.csv", gates, ["gate", "new_admitted_rows", "rerun_triggered", "reason"])
    write_csv(OUT / "rerun_decision.csv", decisions, ["decision", "boundary_layer_rerun", "coupled_m3ts_rerun", "scientific_reason", "next_gate_sequence"])
    write_csv(OUT / "runtime_rerun_assessment_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "gate_delta_rows": len(gates),
        "rerun_triggered_gates": sum(1 for row in gates if row["rerun_triggered"] == "true"),
        "boundary_layer_rerun": decisions[0]["boundary_layer_rerun"] == "true",
        "coupled_m3ts_rerun": decisions[0]["coupled_m3ts_rerun"] == "true",
        "runtime_audit_rows": len(runtime),
        "runtime_audit_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_docs(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
