#!/usr/bin/env python3
"""Build the upcomer onset CFD anchor matrix package without launching CFD."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-UPCOMER-ONSET-CFD-ANCHOR-MATRIX"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-UPCOMER-ONSET-CFD-ANCHOR-MATRIX.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/upcomer-onset-cfd-anchor-matrix.md"
IMPORT = ROOT / "imports/2026-07-17_upcomer_onset_cfd_anchor_matrix.json"

SOURCE_MATRIX = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"
    / "proposed_cfd_run_matrix.csv"
)
OUTPUT_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"
    / "required_output_contract.csv"
)
ACTIVE_HIGH_HEAT = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design"
    / "active_high_heat_context.csv"
)
HYBRID_GAPS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "onset_anchor_gap.csv"
)
ONSET_CLASS = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard"
    / "upcomer_onset_classification.csv"
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
    required = [SOURCE_MATRIX, OUTPUT_CONTRACT, ACTIVE_HIGH_HEAT, HYBRID_GAPS, ONSET_CLASS]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing upcomer onset matrix sources: " + "; ".join(missing))


def build_anchor_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(SOURCE_MATRIX):
        if row["study_group"] == "sentinel_cell_off":
            readiness = "after_high_heat_preflight"
        elif row["study_group"] == "sentinel_cell_max":
            readiness = "after_high_heat_preflight"
        elif row["study_group"] == "small_q_x_insulation_matrix":
            readiness = "future_compute_heavy"
        else:
            readiness = "future_feasibility"
        rows.append(
            {
                "case_key": row["case_key"],
                "study_group": row["study_group"],
                "salt_anchor": row["salt_anchor"],
                "target_heater_power_W": row["target_heater_power_W"],
                "q_ratio_vs_salt3_nominal": row["q_ratio_vs_salt3_nominal"],
                "insulation_mode": row["insulation_mode"],
                "target_regime": row["target_regime"],
                "priority": row["priority"],
                "readiness_class": readiness,
                "launch_allowed_in_this_row": "false",
                "scientific_use": row["scientific_use"],
                "rationale": row["rationale"],
            }
        )
    rows.append(
        {
            "case_key": "forced_flow_decoupled_re_feasibility",
            "study_group": "optional_forced_flow_feasibility",
            "salt_anchor": "representative_salt_case",
            "target_heater_power_W": "TBD",
            "q_ratio_vs_salt3_nominal": "TBD",
            "insulation_mode": "TBD",
            "target_regime": "decouple_Re_from_buoyancy_if_solver_supports",
            "priority": 3,
            "readiness_class": "future_feasibility",
            "launch_allowed_in_this_row": "false",
            "scientific_use": "feasibility only; not an ordinary upcomer coefficient fit",
            "rationale": "Useful only if boundary conditions can decouple flow rate from buoyancy without invalidating the natural-circulation comparison.",
        }
    )
    return rows


def build_required_output_rows() -> list[dict[str, object]]:
    return [
        {
            **row,
            "admission_role": "required_before_hybrid_fit_admission" if row["required_for_acceptance"] == "yes" else "supporting",
        }
        for row in read_csv(OUTPUT_CONTRACT)
    ]


def build_decision_rows(anchor_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups = sorted({row["study_group"] for row in anchor_rows})
    return [
        {
            "decision_id": group,
            "case_count": sum(1 for row in anchor_rows if row["study_group"] == group),
            "admission_status": "design_only_not_launched",
            "next_action": "claim separate scheduler/staging row before any case launch",
            "runtime_guardrail": "no expensive CFD launched in this planning row",
        }
        for group in groups
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_scheduler_action", "status": "pass_forbidden", "forbidden_input": "sbatch/srun/scancel", "policy": "planning row only"},
        {"check": "no_native_output_mutation", "status": "pass_forbidden", "forbidden_input": "native CFD case outputs", "policy": "read-only sources"},
        {"check": "no_registry_mutation", "status": "pass_forbidden", "forbidden_input": "registry/admission state", "policy": "future row decides launch/admission"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("source_matrix", SOURCE_MATRIX, "proposed CFD anchor cases"),
        ("output_contract", OUTPUT_CONTRACT, "required outputs"),
        ("active_high_heat", ACTIVE_HIGH_HEAT, "readiness context"),
        ("hybrid_gaps", HYBRID_GAPS, "hybrid missing evidence"),
        ("onset_class", ONSET_CLASS, "current onset classifications"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(SOURCE_MATRIX)}",
                f"  - {rel(OUTPUT_CONTRACT)}",
                f"  - {rel(HYBRID_GAPS)}",
                "tags: [upcomer, onset, cfd-anchor, design]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Scheduler/Hydraulics/Thermal-modeling/Upcomer-onset/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Upcomer Onset CFD Anchor Matrix",
                "",
                "## Decision",
                "",
                "The onset anchor study is designed but not launched. A future scheduler/staging row must claim any expensive CFD execution.",
                "",
                "## Results",
                "",
                f"- Anchor rows: `{summary['anchor_rows']}`.",
                f"- Immediate/after-preflight rows: `{summary['after_high_heat_preflight_rows']}`.",
                f"- Future compute-heavy rows: `{summary['future_compute_heavy_rows']}`.",
                f"- Required output rows: `{summary['required_output_rows']}`.",
                f"- Scheduler action: `{summary['scheduler_action']}`.",
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
                "tags: [status, upcomer, onset]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Scheduler/Hydraulics/Thermal-modeling/Upcomer-onset/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- Existing design evidence already defines high-Re cell-off, low-Q cell-max, and Q x insulation matrix cases.",
                "- Required outputs cover U/T/wallHeatFlux/Re/Pr/Ri/Gr/Ra/Gz, wall-core Delta T, RAF/RMF/SVF, steady window, and mesh/time uncertainty.",
                "- This row launched no CFD and made no scheduler action.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_upcomer_onset_cfd_anchor_matrix`",
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
                f"  - {rel(SOURCE_MATRIX)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, upcomer, onset]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Scheduler/Hydraulics/Thermal-modeling/Upcomer-onset/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Upcomer Onset CFD Anchor Matrix Journal",
                "",
                "The matrix is complete as a design artifact. Any launch requires a separate board row with scheduler/staging scope.",
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
    anchors = build_anchor_matrix()
    outputs = build_required_output_rows()
    decisions = build_decision_rows(anchors)
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(
        OUT / "upcomer_onset_anchor_matrix.csv",
        anchors,
        [
            "case_key",
            "study_group",
            "salt_anchor",
            "target_heater_power_W",
            "q_ratio_vs_salt3_nominal",
            "insulation_mode",
            "target_regime",
            "priority",
            "readiness_class",
            "launch_allowed_in_this_row",
            "scientific_use",
            "rationale",
        ],
    )
    write_csv(
        OUT / "required_output_contract.csv",
        outputs,
        [
            "required_output",
            "source_type",
            "extraction_location_or_method",
            "why_required",
            "required_for_acceptance",
            "admission_role",
        ],
    )
    write_csv(OUT / "anchor_group_decisions.csv", decisions, ["decision_id", "case_count", "admission_status", "next_action", "runtime_guardrail"])
    write_csv(OUT / "runtime_onset_anchor_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "anchor_rows": len(anchors),
        "after_high_heat_preflight_rows": sum(1 for row in anchors if row["readiness_class"] == "after_high_heat_preflight"),
        "future_compute_heavy_rows": sum(1 for row in anchors if row["readiness_class"] == "future_compute_heavy"),
        "future_feasibility_rows": sum(1 for row in anchors if row["readiness_class"] == "future_feasibility"),
        "required_output_rows": len(outputs),
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
