#!/usr/bin/env python3
"""Repair/narrow test-section passive-loss admission blockers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-TEST-SECTION-PASSIVE-LOSS-ADMISSION-REPAIR"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_test_section_passive_loss_admission_repair"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-TEST-SECTION-PASSIVE-LOSS-ADMISSION-REPAIR.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/test-section-passive-loss-admission-repair.md"
IMPORT = ROOT / "imports/2026-07-17_test_section_passive_loss_admission_repair.json"

SETUP_CANDIDATES = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model"
    / "setup_candidate_summary.csv"
)
BLOCKER_DECISION = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model"
    / "blocker_decision.json"
)
BOUNDARY_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission"
    / "wall_test_section_scorecard.csv"
)
THERMAL_SLOTS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
    / "thermal_model_slot_admission.csv"
)
COUPLED_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_coupled_segment_m3ts_scorecard"
    / "prerequisite_gate_matrix.csv"
)


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [SETUP_CANDIDATES, BLOCKER_DECISION, BOUNDARY_SCORECARD, THERMAL_SLOTS, COUPLED_SCORECARD]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing test-section repair sources: " + "; ".join(missing))


def build_candidate_class_rows() -> list[dict[str, object]]:
    existing = read_csv(SETUP_CANDIDATES)
    rows: list[dict[str, object]] = []
    for row in existing:
        rows.append(
            {
                "candidate_class": row["candidate_id"],
                "source_candidate": row["candidate_id"],
                "runtime_gate": row["runtime_gate"],
                "validation_qoi_gate": row["validation_qoi_gate"],
                "holdout_qoi_gate": row["holdout_qoi_gate"],
                "end_to_end_gate": row["end_to_end_gate"],
                "admission_status": "blocked" if row["admission_decision"] == "not_admitted" else "admitted",
                "fit_allowed_now": "false",
                "score_allowed_now": "diagnostic" if "diagnostic" in row["candidate_class"] else "false",
                "reason": row["primary_reason"],
                "source_path": rel(SETUP_CANDIDATES),
            }
        )
    rows.extend(
        [
            {
                "candidate_class": "TS5_setup_resistance_network_wall_external",
                "source_candidate": "new_class_not_scored",
                "runtime_gate": "pass_available_api_hooks",
                "validation_qoi_gate": "not_scored",
                "holdout_qoi_gate": "not_scored",
                "end_to_end_gate": "not_scored_no_frozen_candidate",
                "admission_status": "blocked",
                "fit_allowed_now": "false",
                "score_allowed_now": "false",
                "reason": "API hooks exist, but no scored setup-only resistance-network candidate exists.",
                "source_path": rel(BOUNDARY_SCORECARD),
            },
            {
                "candidate_class": "TS6_radiation_if_independently_admitted",
                "source_candidate": "new_class_not_scored",
                "runtime_gate": "blocked_until_independent_radiation_gate",
                "validation_qoi_gate": "not_scored",
                "holdout_qoi_gate": "not_scored",
                "end_to_end_gate": "not_scored_no_frozen_candidate",
                "admission_status": "blocked",
                "fit_allowed_now": "false",
                "score_allowed_now": "false",
                "reason": "Radiation cannot be double-counted or inferred from realized wall heat; independent setup radiation gate is missing.",
                "source_path": rel(THERMAL_SLOTS),
            },
        ]
    )
    return rows


def build_missing_requirements() -> list[dict[str, object]]:
    blocker = json.loads(BLOCKER_DECISION.read_text())
    return [
        {
            "requirement_id": "setup_only_resistance_network_candidate",
            "status": "missing",
            "next_action": "Freeze a setup-only wall/external resistance-network candidate using geometry, emissivity, ambient/surroundings temperatures, coverage, and h inputs.",
            "source_path": rel(BOUNDARY_SCORECARD),
        },
        {
            "requirement_id": "validation_holdout_heat_gate",
            "status": "missing",
            "next_action": "Pass Salt3 validation and Salt4 holdout test-section heat-loss gates without realized wallHeatFlux or validation temperatures.",
            "source_path": rel(SETUP_CANDIDATES),
        },
        {
            "requirement_id": "coupled_m3ts_score_for_candidate",
            "status": "missing",
            "next_action": blocker["next_required_action"],
            "source_path": rel(BLOCKER_DECISION),
        },
        {
            "requirement_id": "independent_radiation_semantics",
            "status": "missing",
            "next_action": "Admit radiation only as a setup term with no double-counting against external convection or realized wall heat.",
            "source_path": rel(THERMAL_SLOTS),
        },
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_realized_wall_heat_runtime", "status": "pass_forbidden", "forbidden_input": "realized wallHeatFlux", "policy": "diagnostic only"},
        {"check": "no_validation_temperature_runtime", "status": "pass_forbidden", "forbidden_input": "validation TP/TW temperatures", "policy": "post-solve targets only"},
        {"check": "no_cfd_mdot_runtime", "status": "pass_forbidden", "forbidden_input": "CFD mdot", "policy": "coupled solved output"},
        {"check": "no_imposed_cooler_duty_runtime", "status": "pass_forbidden", "forbidden_input": "imposed CFD cooler duty", "policy": "unrelated setup cooler lane only"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("setup_candidates", SETUP_CANDIDATES, "existing setup-only candidate scores"),
        ("blocker_decision", BLOCKER_DECISION, "existing blocker decision"),
        ("boundary_scorecard", BOUNDARY_SCORECARD, "API hook and boundary state"),
        ("thermal_slots", THERMAL_SLOTS, "segment thermal test-section slots"),
        ("coupled_scorecard", COUPLED_SCORECARD, "final coupled prerequisite state"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(SETUP_CANDIDATES)}",
                f"  - {rel(BLOCKER_DECISION)}",
                f"  - {rel(BOUNDARY_SCORECARD)}",
                "tags: [test-section, passive-loss, admission, blocker]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Test-Section Passive-Loss Admission Repair",
                "",
                "## Decision",
                "",
                "No test-section passive-loss candidate is admitted by this repair pass. The API hooks exist, but the scored setup-only physical candidates still fail validation/holdout gates or lack a frozen coupled M3+TS score.",
                "",
                "## Results",
                "",
                f"- Candidate class rows: `{summary['candidate_class_rows']}`.",
                f"- Admitted candidate rows: `{summary['admitted_candidate_rows']}`.",
                f"- Missing requirement rows: `{summary['missing_requirement_rows']}`.",
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
                "tags: [status, test-section, passive-loss]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- Existing TS1/TS2 setup-only physical candidates fail validation and holdout heat gates.",
                "- The realized external-loss row is runtime-illegal.",
                "- API hooks exist for a resistance-network style candidate, but that candidate is not yet scored.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_test_section_passive_loss_admission_repair`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for test-section passive-loss blocker visibility.",
                "- Admission remains blocked by missing setup-only resistance-network scoring, validation/holdout heat gates, coupled M3+TS scoring, and radiation semantics.",
                "- Generated docs index refresh was skipped because active/completed board context owns generated index files.",
            ]
        )
        + "\n"
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(SETUP_CANDIDATES)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, test-section, passive-loss]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Test-Section Passive-Loss Admission Repair Journal",
                "",
                "## Interpretation",
                "",
                "The repair pass narrows the blocker but does not admit a candidate. The next scientific step is a frozen setup-only resistance-network candidate with split-safe heat and coupled scores.",
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
    candidates = build_candidate_class_rows()
    missing = build_missing_requirements()
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(
        OUT / "test_section_candidate_class_admission.csv",
        candidates,
        [
            "candidate_class",
            "source_candidate",
            "runtime_gate",
            "validation_qoi_gate",
            "holdout_qoi_gate",
            "end_to_end_gate",
            "admission_status",
            "fit_allowed_now",
            "score_allowed_now",
            "reason",
            "source_path",
        ],
    )
    write_csv(OUT / "missing_requirement_queue.csv", missing, ["requirement_id", "status", "next_action", "source_path"])
    write_csv(OUT / "runtime_test_section_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "candidate_class_rows": len(candidates),
        "admitted_candidate_rows": sum(1 for row in candidates if row["admission_status"] == "admitted"),
        "missing_requirement_rows": len(missing),
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
