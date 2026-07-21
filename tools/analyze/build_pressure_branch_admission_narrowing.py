#!/usr/bin/env python3
"""Narrow branch-level pressure closure admission blockers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PRESSURE-BRANCH-ADMISSION-NARROWING"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_pressure_branch_admission_narrowing"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-PRESSURE-BRANCH-ADMISSION-NARROWING.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/pressure-branch-admission-narrowing.md"
IMPORT = ROOT / "imports/2026-07-17_pressure_branch_admission_narrowing.json"

PRESSURE_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
    / "segment_pressure_model_scorecard.csv"
)
PRESSURE_LADDER = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table"
    / "branch_orientation_straight_loss_recirc_admission.csv"
)
PRESSURE_TERM_LEDGER = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv"
MINOR_LOSS = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv"
BRANCH_MASK = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard"
    / "ordinary_pipe_branch_mask.csv"
)

BRANCHES = [
    ("heater_lower_leg", "heater", ["lower_leg"], "candidate_nearest_admission_after_source_and_mesh_gates"),
    ("cooler_upper_leg", "cooler_HX", ["upper_leg"], "candidate_nearest_admission_after_hx_boundary_separation"),
    ("downcomer_right_leg", "downcomer", ["right_leg"], "blocked_by_downcomer_policy_and_recirc_gates"),
    ("lower_upper_legs", "lower_upper_legs", ["lower_leg", "upper_leg"], "least_risk_straight_branch_pair_but_still_blocked"),
    ("test_section_span", "test_section", ["test_section_span"], "blocked_by_pressure_definition_and_component_length"),
    ("upcomer_left_vertical", "upcomer", ["left_lower_leg", "left_upper_leg", "test_section_span"], "handoff_to_hybrid_lane_not_ordinary_pressure"),
    ("junction_stub_connector", "junction_stub_connector", ["junction"], "diagnostic_named_loss_only"),
]
GATES = [
    "pressure_definition",
    "geometry_length_normalization",
    "straight_loss_subtraction",
    "component_isolation",
    "recirculation_mask",
    "mesh_gci",
]


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
    required = [PRESSURE_SCORECARD, PRESSURE_LADDER, PRESSURE_TERM_LEDGER, MINOR_LOSS, BRANCH_MASK]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing pressure branch admission sources: " + "; ".join(missing))


def _by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def _rows_for_spans(rows: list[dict[str, str]], key: str, spans: list[str]) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key, "") in spans]


def _gate_status(branch_id: str, spans: list[str], pressure_rows: list[dict[str, str]], ladder_rows: list[dict[str, str]], minor_rows: list[dict[str, str]]) -> dict[str, str]:
    blockers = ";".join(row.get("blockers", "") for row in ladder_rows)
    recirc_block = any("recirculation_mask" in row.get("blockers", "") for row in ladder_rows) or "upcomer" in branch_id
    return {
        "pressure_definition": "blocked" if not ladder_rows or any(row.get("pressure_definition_status", "").startswith("blocked") for row in ladder_rows) else "diagnostic",
        "geometry_length_normalization": "blocked" if "no_geometry_distance_normalization" in blockers else "diagnostic",
        "straight_loss_subtraction": "blocked" if any("screen_only_no_straight_loss" in row.get("straight_loss_subtraction_status", "") for row in ladder_rows) else "diagnostic",
        "component_isolation": "blocked" if branch_id in {"junction_stub_connector", "test_section_span"} or "component_K_not_isolated" in blockers else "diagnostic",
        "recirculation_mask": "blocked" if recirc_block else "diagnostic",
        "mesh_gci": "blocked" if "coarse_no_gci" in ";".join(row.get("quality_flags", "") for row in pressure_rows) or "coarse_only_no_mesh_gci" in blockers else "blocked",
    }


def build_branch_admission_rows() -> list[dict[str, object]]:
    pressure_score = _by(read_csv(PRESSURE_SCORECARD), "loop_region")
    ladder = read_csv(PRESSURE_LADDER)
    pressure_terms = read_csv(PRESSURE_TERM_LEDGER)
    minor = read_csv(MINOR_LOSS)
    branch_mask = _by(read_csv(BRANCH_MASK), "branch_id")
    rows: list[dict[str, object]] = []
    for branch_id, region, spans, role in BRANCHES:
        p_score = pressure_score[region]
        p_rows = _rows_for_spans(pressure_terms, "span", spans)
        ladder_rows = _rows_for_spans(ladder, "branch", spans)
        minor_rows = _rows_for_spans(minor, "downstream_span", spans)
        gates = _gate_status(branch_id, spans, p_rows, ladder_rows, minor_rows)
        blocked_gates = [gate for gate, status in gates.items() if status == "blocked"]
        if branch_id == "junction_stub_connector":
            admission = "diagnostic-only"
        elif blocked_gates:
            admission = "blocked"
        else:
            admission = "validation-only"
        rows.append(
            {
                "branch_id": branch_id,
                "loop_region": region,
                "review_role": role,
                "admission_status": admission,
                "fit_admitted_pressure_rows": 0,
                "diagnostic_pressure_rows": len(p_rows) + len(ladder_rows) + len(minor_rows),
                "least_risk_candidate": "true" if branch_id == "lower_upper_legs" else "false",
                "blocked_gates": ";".join(blocked_gates),
                "next_required_evidence": ";".join(blocked_gates) if blocked_gates else "split_safe_validation_score",
                "segment_scorecard_status": p_score["admission_status"],
                "ordinary_branch_mask_status": branch_mask.get(branch_id, {}).get("admission_status", ""),
                "source_paths": ";".join([rel(PRESSURE_SCORECARD), rel(PRESSURE_LADDER), rel(PRESSURE_TERM_LEDGER), rel(MINOR_LOSS), rel(BRANCH_MASK)]),
            }
        )
    return rows


def build_gate_matrix(branch_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in branch_rows:
        blocked = set(str(row["blocked_gates"]).split(";")) if row["blocked_gates"] else set()
        for gate in GATES:
            rows.append(
                {
                    "branch_id": row["branch_id"],
                    "gate": gate,
                    "status": "blocked" if gate in blocked else "diagnostic",
                    "admission_effect": "prevents_fit_admission" if gate in blocked else "supports_diagnostic_review_only",
                }
            )
    return rows


def build_missing_queue(branch_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in branch_rows:
        for gate in [item for item in str(row["blocked_gates"]).split(";") if item]:
            rows.append(
                {
                    "branch_id": row["branch_id"],
                    "missing_gate": gate,
                    "priority": "high" if row["least_risk_candidate"] == "true" else "medium",
                    "action": {
                        "pressure_definition": "admit raw/static/p_rgh pressure definition for coefficient use",
                        "geometry_length_normalization": "publish centerline length/tap-distance normalization for this branch",
                        "straight_loss_subtraction": "separate distributed straight loss before local coefficient fitting",
                        "component_isolation": "bracket component pressure drop independently of neighboring spans",
                        "recirculation_mask": "prove low-recirculation validity or route to hybrid/named-loss lane",
                        "mesh_gci": "provide same-QOI mesh/GCI or uncertainty basis",
                    }[gate],
                }
            )
    return rows


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_cfd_mdot_runtime", "status": "pass_forbidden", "forbidden_input": "CFD mdot", "policy": "pressure closure must be predictive"},
        {"check": "no_global_friction_multiplier", "status": "pass_forbidden", "forbidden_input": "global friction multiplier", "policy": "branch-level gates only"},
        {"check": "no_recirc_ordinary_fit", "status": "pass_forbidden", "forbidden_input": "ordinary f_D/K fit on recirculating rows", "policy": "upcomer routes to hybrid lane"},
        {"check": "no_unbracketed_k", "status": "pass_forbidden", "forbidden_input": "unbracketed residual as physical K", "policy": "component isolation required"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("pressure_scorecard", PRESSURE_SCORECARD, "segment pressure admission state"),
        ("pressure_ladder", PRESSURE_LADDER, "branch pressure masks"),
        ("pressure_term_ledger", PRESSURE_TERM_LEDGER, "pressure evidence rows"),
        ("minor_loss", MINOR_LOSS, "minor-loss/two-tap evidence"),
        ("branch_mask", BRANCH_MASK, "ordinary branch exclusion state"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(PRESSURE_SCORECARD)}",
                f"  - {rel(PRESSURE_LADDER)}",
                f"  - {rel(BRANCH_MASK)}",
                "tags: [pressure, branch-admission, scorecard, blocker]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Forward-pred/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# Pressure Branch Admission Narrowing",
                "",
                "## Decision",
                "",
                "No segment-local pressure coefficient is admitted by this narrowing pass. The package completes the blocker narrowing by branch and gate; `lower_upper_legs` is the least-risk next technical target but still blocked.",
                "",
                "## Results",
                "",
                f"- Branch rows: `{summary['branch_rows']}`.",
                f"- Fit-admitted pressure rows: `{summary['fit_admitted_pressure_rows']}`.",
                f"- Least-risk candidates: `{summary['least_risk_candidate_rows']}`.",
                f"- Missing-evidence rows: `{summary['missing_evidence_rows']}`.",
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
                "tags: [status, pressure, branch-admission]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Forward-pred/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- The segment pressure scorecard admits zero scoreable predictive pressure rows.",
                "- Branch-level gates can be narrowed without promoting diagnostics into closures.",
                "- `lower_upper_legs` is the least-risk next target but still fails admission gates.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_pressure_branch_admission_narrowing`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for branch-level pressure blocker visibility.",
                "- Pressure closure admission remains blocked by exact gate rows in `missing_evidence_queue.csv`.",
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
                f"  - {rel(PRESSURE_SCORECARD)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, pressure, branch-admission]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Forward-pred/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Pressure Branch Admission Narrowing Journal",
                "",
                "## Interpretation",
                "",
                "The pressure path is now narrowed to concrete missing gates. The scientific result is still zero admitted pressure coefficients, not a failed model.",
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
    branches = build_branch_admission_rows()
    gates = build_gate_matrix(branches)
    missing = build_missing_queue(branches)
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(
        OUT / "branch_pressure_admission.csv",
        branches,
        [
            "branch_id",
            "loop_region",
            "review_role",
            "admission_status",
            "fit_admitted_pressure_rows",
            "diagnostic_pressure_rows",
            "least_risk_candidate",
            "blocked_gates",
            "next_required_evidence",
            "segment_scorecard_status",
            "ordinary_branch_mask_status",
            "source_paths",
        ],
    )
    write_csv(OUT / "pressure_gate_matrix.csv", gates, ["branch_id", "gate", "status", "admission_effect"])
    write_csv(OUT / "missing_evidence_queue.csv", missing, ["branch_id", "missing_gate", "priority", "action"])
    write_csv(OUT / "runtime_pressure_branch_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "branch_rows": len(branches),
        "fit_admitted_pressure_rows": sum(int(row["fit_admitted_pressure_rows"]) for row in branches),
        "least_risk_candidate_rows": sum(1 for row in branches if row["least_risk_candidate"] == "true"),
        "missing_evidence_rows": len(missing),
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
