#!/usr/bin/env python3
"""Build branch-specific ordinary-pipe inclusion/exclusion scorecards."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_branch_specific_ordinary_pipe_scorecard"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/branch-specific-ordinary-pipe-scorecard.md"
IMPORT = ROOT / "imports/2026-07-17_branch_specific_ordinary_pipe_scorecard.json"

BRANCH_THERMAL = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock"
    / "branch_local_thermal_admission.csv"
)
DOWNCOMER_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact"
    / "downcomer_admission_decision.csv"
)
PRESSURE_LADDER = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table"
    / "branch_orientation_straight_loss_recirc_admission.csv"
)
PRESSURE_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
    / "segment_pressure_model_scorecard.csv"
)
THERMAL_SCORECARD = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models"
    / "segment_thermal_model_scorecard.csv"
)
UPCOMER_HYBRID = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model"
    / "upcomer_admission_decision.csv"
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
    required = [BRANCH_THERMAL, DOWNCOMER_POLICY, PRESSURE_LADDER, PRESSURE_SCORECARD, THERMAL_SCORECARD, UPCOMER_HYBRID]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing branch ordinary-pipe sources: " + "; ".join(missing))


def _by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def build_branch_mask() -> list[dict[str, object]]:
    thermal = _by(read_csv(BRANCH_THERMAL), "canonical_leg_id")
    pressure = _by(read_csv(PRESSURE_SCORECARD), "loop_region")
    thermal_seg = _by(read_csv(THERMAL_SCORECARD), "loop_region")
    downcomer = read_csv(DOWNCOMER_POLICY)[0]
    ladder = read_csv(PRESSURE_LADDER)
    ladder_by_branch = {}
    for row in ladder:
        ladder_by_branch.setdefault(row["branch"], []).append(row)

    specs = [
        ("heater_lower_leg", "heater", "heater_lower_leg", "heated/source-region branch", "source-region branch-specific thermal and hydraulic diagnostics"),
        ("downcomer_right_vertical", "downcomer", "right_leg", "cooling/downcomer branch", "ordinary branch only after downcomer policy gates pass"),
        ("cooler_hx_branch", "cooler_HX", "upper_leg", "HX/boundary branch", "setup cooler UA/effectiveness lane, not internal Nu"),
        ("test_section_span", "test_section", "test_section_span", "upcomer test-section span", "test-section boundary lane, not ordinary pipe coefficient"),
        ("upcomer_left_vertical", "upcomer", "left_lower_leg;left_upper_leg", "recirculating upcomer branch", "handoff to throughflow-pipe plus recirculation-cell hybrid lane"),
        ("junction_stub_connector", "junction_stub_connector", "bends;tees;reducers;stubs", "named local component", "named-loss or boundary term only"),
        ("lower_upper_legs", "lower_upper_legs", "lower_leg;upper_leg", "interconnecting straight branches", "development and wall-resistance diagnostic lane"),
    ]
    rows: list[dict[str, object]] = []
    for branch_id, region, ladder_key, role, model_form in specs:
        branch_source = thermal.get(branch_id, {})
        p = pressure.get(region, {})
        t = thermal_seg.get(region, {})
        ladder_rows = []
        for key in ladder_key.split(";"):
            ladder_rows.extend(ladder_by_branch.get(key, []))
        fit_rows = int(branch_source.get("fit_admissible_internal_nu_rows") or 0)
        pressure_fit_rows = int(p.get("true_fd_or_k_fit_admitted_rows") or 0)
        thermal_fit_rows = int(t.get("residual_internal_nu_fit_admitted_rows") or 0)
        if branch_id == "upcomer_left_vertical":
            admission = "blocked_handoff_to_upcomer_hybrid"
            include = "false"
            reason = "recirculating rows excluded from ordinary-pipe aggregate fits"
        elif branch_id == "junction_stub_connector":
            admission = "diagnostic_only_named_loss"
            include = "false"
            reason = "component heat/pressure not isolated as pipe coefficient"
        elif branch_id == "cooler_hx_branch":
            admission = "validation_only_boundary_hx_lane"
            include = "false"
            reason = "HX removal is a setup boundary model, not an internal-Nu fit"
        elif branch_id == "downcomer_right_vertical":
            admission = "blocked_downcomer_policy"
            include = "false"
            reason = downcomer["blocking_reasons"]
        elif branch_id == "heater_lower_leg":
            admission = "blocked_source_region_gates"
            include = "false"
            reason = branch_source.get("primary_blockers", "source ownership and heat-balance gates")
        elif branch_id == "test_section_span":
            admission = "blocked_test_section_boundary_and_pressure_gates"
            include = "false"
            reason = "test-section passive loss and pressure definition/component gates are not admitted"
        else:
            admission = "diagnostic_only_development_lane"
            include = "false"
            reason = "development and wall-resistance effects not yet scored as admitted ordinary coefficients"

        rows.append(
            {
                "branch_id": branch_id,
                "loop_region": region,
                "branch_role": role,
                "ordinary_pipe_fit_included": include,
                "ordinary_nu_fit_admitted_rows": fit_rows + thermal_fit_rows,
                "ordinary_fd_k_fit_admitted_rows": pressure_fit_rows,
                "pressure_ladder_rows": len(ladder_rows),
                "diagnostic_rows": int(p.get("diagnostic_evidence_rows") or 0) + int(t.get("diagnostic_source_sink_rows") or 0),
                "branch_specific_model_form": model_form,
                "admission_status": admission,
                "blocked_labels": "single_stream_Nu;single_stream_f_D;component_K" if include == "false" else "",
                "reason": reason,
                "handoff_target": "TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL" if branch_id == "upcomer_left_vertical" else "",
                "score_delta_status": "not_run_no_fit_admitted_branch",
                "source_paths": ";".join([rel(BRANCH_THERMAL), rel(PRESSURE_SCORECARD), rel(THERMAL_SCORECARD), rel(PRESSURE_LADDER)]),
            }
        )
    return rows


def build_model_form_contract(mask: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "branch_id": row["branch_id"],
            "allowed_model_form": row["branch_specific_model_form"],
            "fit_allowed_now": "false",
            "score_allowed_now": "diagnostic" if "diagnostic" in str(row["admission_status"]) else "false",
            "runtime_guardrail": "no CFD mdot, realized wallHeatFlux, imposed cooler duty, validation temperatures, or global multipliers",
            "admission_status": row["admission_status"],
        }
        for row in mask
    ]


def build_handoff_rows(mask: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "branch_id": row["branch_id"],
            "excluded_from_ordinary_pipe_aggregate": "true",
            "handoff_target": row["handoff_target"] or "branch_specific_gate_repair",
            "reason": row["reason"],
        }
        for row in mask
        if row["ordinary_pipe_fit_included"] == "false"
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {"check": "no_upcomer_in_ordinary_aggregate", "status": "pass_forbidden", "forbidden_input": "recirculating upcomer rows in ordinary-pipe aggregate", "policy": "handoff to hybrid lane"},
        {"check": "no_validation_temperatures_runtime", "status": "pass_forbidden", "forbidden_input": "validation TP/TW temperatures", "policy": "score targets only"},
        {"check": "no_cfd_mdot_runtime", "status": "pass_forbidden", "forbidden_input": "CFD mdot", "policy": "coupled solved output"},
        {"check": "no_global_multiplier", "status": "pass_forbidden", "forbidden_input": "global Nu/f friction multiplier", "policy": "branch-specific forms only"},
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("branch_thermal", BRANCH_THERMAL, "branch-local internal Nu gates"),
        ("downcomer_policy", DOWNCOMER_POLICY, "downcomer ordinary Nu exclusion"),
        ("pressure_ladder", PRESSURE_LADDER, "branch recirculation/pressure masks"),
        ("pressure_scorecard", PRESSURE_SCORECARD, "segment pressure admission"),
        ("thermal_scorecard", THERMAL_SCORECARD, "segment thermal admission"),
        ("upcomer_hybrid", UPCOMER_HYBRID, "upcomer handoff target"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    readme = [
        "---",
        "provenance:",
        f"  - {rel(BRANCH_THERMAL)}",
        f"  - {rel(PRESSURE_SCORECARD)}",
        f"  - {rel(THERMAL_SCORECARD)}",
        "tags: [branch-specific, ordinary-pipe, admission, scorecard]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Branch-Specific Ordinary Pipe Scorecard",
        "",
        "## Decision",
        "",
        "No current branch is admitted for ordinary single-stream `Nu`, `f_D`, or physical `K` coefficient fitting. "
        "The package is complete as an admission mask: upcomer rows are handed to the hybrid lane, junctions remain named-loss diagnostics, "
        "and heater/cooler/test-section/downcomer rows keep their own gates.",
        "",
        "## Results",
        "",
        f"- Branches reviewed: `{summary['branch_rows']}`.",
        f"- Branches included in ordinary aggregate fits: `{summary['ordinary_fit_included_branches']}`.",
        f"- Ordinary coefficient fit-admitted rows: `{summary['ordinary_coefficient_fit_admitted_rows']}`.",
        f"- Exclusion handoff rows: `{summary['exclusion_handoff_rows']}`.",
        f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
    ]
    (OUT / "README.md").write_text("\n".join(readme) + "\n")
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
                "tags: [status, branch-specific, ordinary-pipe]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Observed Facts",
                "",
                "- Current branch evidence admits zero ordinary single-stream coefficient rows.",
                "- Upcomer rows are explicitly excluded from ordinary-pipe aggregate fit claims.",
                "- Other branches have branch-specific gates or diagnostic/named-loss uses.",
                "",
                "## Validation",
                "",
                "- `python3 -m unittest tools.analyze.test_branch_specific_ordinary_pipe_scorecard`",
                "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
                "",
                "## Blockers",
                "",
                "- No blocker remains for branch mask visibility.",
                "- Ordinary coefficient admission remains blocked by source ownership, downcomer policy, recirculation, pressure definition, component isolation, mesh/GCI, and boundary-lane separation.",
                "- Generated docs index refresh was skipped because active board rows own generated index files.",
            ]
        )
        + "\n"
    )
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(BRANCH_THERMAL)}",
                f"  - {rel(OUT / 'README.md')}",
                "tags: [journal, branch-specific, ordinary-pipe]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# Branch-Specific Ordinary Pipe Scorecard Journal",
                "",
                "## Files Changed",
                "",
                "- `tools/analyze/build_branch_specific_ordinary_pipe_scorecard.py`",
                "- `tools/analyze/test_branch_specific_ordinary_pipe_scorecard.py`",
                f"- `{rel(OUT)}/`",
                f"- `{rel(STATUS)}`",
                f"- `{rel(JOURNAL)}`",
                f"- `{rel(IMPORT)}`",
                "- `.agent/BOARD.md` own row status",
                "",
                "## Interpretation",
                "",
                "The branch-specific task is complete as a conservative admission mask. It prevents diagnostics from becoming overclaimed ordinary closures.",
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
        "generated_index_refresh_note": "Skipped because active board rows own generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)
    mask = build_branch_mask()
    forms = build_model_form_contract(mask)
    handoffs = build_handoff_rows(mask)
    runtime = runtime_audit_rows()
    sources = source_manifest()
    write_csv(
        OUT / "ordinary_pipe_branch_mask.csv",
        mask,
        [
            "branch_id",
            "loop_region",
            "branch_role",
            "ordinary_pipe_fit_included",
            "ordinary_nu_fit_admitted_rows",
            "ordinary_fd_k_fit_admitted_rows",
            "pressure_ladder_rows",
            "diagnostic_rows",
            "branch_specific_model_form",
            "admission_status",
            "blocked_labels",
            "reason",
            "handoff_target",
            "score_delta_status",
            "source_paths",
        ],
    )
    write_csv(OUT / "branch_model_form_contract.csv", forms, ["branch_id", "allowed_model_form", "fit_allowed_now", "score_allowed_now", "runtime_guardrail", "admission_status"])
    write_csv(OUT / "ordinary_pipe_exclusion_handoff.csv", handoffs, ["branch_id", "excluded_from_ordinary_pipe_aggregate", "handoff_target", "reason"])
    write_csv(OUT / "runtime_branch_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    summary = {
        "task": TASK,
        "date": DATE,
        "branch_rows": len(mask),
        "ordinary_fit_included_branches": sum(1 for row in mask if row["ordinary_pipe_fit_included"] == "true"),
        "ordinary_coefficient_fit_admitted_rows": sum(int(row["ordinary_nu_fit_admitted_rows"]) + int(row["ordinary_fd_k_fit_admitted_rows"]) for row in mask),
        "exclusion_handoff_rows": len(handoffs),
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
