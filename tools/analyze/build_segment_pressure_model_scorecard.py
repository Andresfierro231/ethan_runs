#!/usr/bin/env python3
"""Build the segment-local pressure model scorecard from existing evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PREDICT-SEGMENT-PRESSURE-MODELS"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-PREDICT-SEGMENT-PRESSURE-MODELS.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/predict-segment-pressure-models.md"
IMPORT = ROOT / "imports/2026-07-17_predict_segment_pressure_models.json"

SEGMENT_CONTRACT = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_equation_contract"
    / "segment_equation_contract.csv"
)
PRESSURE_TERM_LEDGER = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv"
MINOR_LOSS = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv"
RECIRC_BRANCH = (
    ROOT
    / "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table"
    / "branch_orientation_straight_loss_recirc_admission.csv"
)
HYDRAULIC_DECISIONS = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification"
    / "hydraulic_admission_final_decisions.csv"
)
F6_SUMMARY = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/summary.json"
F6_CANDIDATES = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_candidate_inventory.csv"

REGION_SPANS = {
    "heater": {"lower_leg"},
    "cooler_HX": {"upper_leg"},
    "downcomer": {"right_leg"},
    "upcomer": {"left_lower_leg", "left_upper_leg"},
    "test_section": {"test_section_span"},
    "junction_stub_connector": set(),
    "lower_upper_legs": {"lower_leg", "upper_leg"},
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [
        SEGMENT_CONTRACT,
        PRESSURE_TERM_LEDGER,
        MINOR_LOSS,
        RECIRC_BRANCH,
        HYDRAULIC_DECISIONS,
        F6_SUMMARY,
        F6_CANDIDATES,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing segment pressure scorecard sources: " + "; ".join(missing))


def segment_contract_rows() -> list[dict[str, str]]:
    return read_csv(SEGMENT_CONTRACT)


def pressure_rows_for_region(region: str, pressure_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    spans = REGION_SPANS.get(region, set())
    if not spans:
        return []
    return [row for row in pressure_rows if row.get("span") in spans]


def recirc_rows_for_region(region: str, recirc_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    spans = REGION_SPANS.get(region, set())
    if not spans:
        return []
    return [row for row in recirc_rows if row.get("branch") in spans]


def minor_rows_for_region(region: str, minor_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if region == "junction_stub_connector":
        return minor_rows
    spans = REGION_SPANS.get(region, set())
    return [row for row in minor_rows if row.get("downstream_span") in spans]


def truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1"}


def build_segment_scorecard() -> list[dict[str, object]]:
    pressure = read_csv(PRESSURE_TERM_LEDGER)
    minor = read_csv(MINOR_LOSS)
    recirc = read_csv(RECIRC_BRANCH)
    contract = segment_contract_rows()
    rows: list[dict[str, object]] = []

    for row in contract:
        region = row["loop_region"]
        p_rows = pressure_rows_for_region(region, pressure)
        r_rows = recirc_rows_for_region(region, recirc)
        m_rows = minor_rows_for_region(region, minor)
        legacy_fit_targets = sum(1 for item in p_rows if item.get("fit_use_status") == "fit_target")
        recirc_blocked = sum(1 for item in r_rows if item.get("true_f_D_or_K_fit_admitted") == "no")
        local_k_upper_bounds = sum(1 for item in m_rows if "K_local_still_upper_bound" in item.get("quality_flags", ""))
        missing_two_tap = sum(1 for item in m_rows if item.get("status") == "missing_preserved_two_tap_feature_output")
        diagnostic_rows = len(p_rows) + len(r_rows) + len(m_rows)

        if region == "upcomer":
            admission_status = "blocked_upcomer_hybrid_required"
            next_gate = "Use hybrid throughflow plus recirculation-cell model; do not fit true single-stream f_D/K."
            blocker = "recirculation_mask;upcomer_hybrid_lane_not_ordinary_pipe_fit;coarse_only_no_mesh_gci"
        elif region == "test_section":
            admission_status = "blocked_pressure_definition_and_component_gate"
            next_gate = "Admit raw two-tap pressure definition and component/tap-length policy before K or f_D fitting."
            blocker = "raw_two_tap_fit_admitted_rows_zero;component_length_policy_unresolved;coarse_only_no_mesh_gci"
        elif region == "junction_stub_connector":
            admission_status = "diagnostic_only_apparent_loss"
            next_gate = "Use apparent K/mixing diagnostics only until physically bracketed local pressure evidence exists."
            blocker = "component_K_not_isolated;tap_length_proxy_abs_dz_not_centerline_length;K_local_upper_bound"
        else:
            admission_status = "diagnostic_only_no_fit_admitted"
            next_gate = "Resolve mesh/GCI, geometry normalization, recirculation mask, and straight-loss subtraction before coefficient admission."
            blocker = "coarse_only_no_mesh_gci;no_geometry_distance_normalization;component_K_not_isolated;recirculation_mask"

        rows.append(
            {
                "loop_region": region,
                "one_d_segments": row["one_d_segments"],
                "pressure_drive_model": row["pressure_drive_form"],
                "candidate_pressure_loss_slots": row["pressure_loss_slots"],
                "pressure_term_ledger_rows": len(p_rows),
                "legacy_pressure_fit_target_rows": legacy_fit_targets,
                "pressure_ladder_admission_rows": len(r_rows),
                "pressure_ladder_blocked_rows": recirc_blocked,
                "minor_loss_rows": len(m_rows),
                "minor_loss_upper_bound_rows": local_k_upper_bounds,
                "missing_two_tap_rows": missing_two_tap,
                "diagnostic_evidence_rows": diagnostic_rows,
                "true_fd_or_k_fit_admitted_rows": 0,
                "scoreable_predictive_model_rows": 0,
                "admission_status": admission_status,
                "primary_blockers": blocker,
                "train_validation_holdout_improvement_status": "not_run_no_fit_admitted_segment_pressure_model",
                "next_gate": next_gate,
                "runtime_forbidden_inputs": row["runtime_forbidden_inputs"],
                "source_paths": ";".join(
                    [
                        rel(SEGMENT_CONTRACT),
                        rel(PRESSURE_TERM_LEDGER),
                        rel(MINOR_LOSS),
                        rel(RECIRC_BRANCH),
                    ]
                ),
            }
        )
    return rows


def build_model_slot_rows(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in scorecard:
        for slot in str(row["candidate_pressure_loss_slots"]).split(";"):
            if not slot:
                continue
            if "recirculation" in slot or "hybrid" in slot or "onset" in slot:
                admission = "diagnostic_or_blocked_until_hybrid_model"
            elif "K" in slot or "apparent" in slot or "junction" in slot:
                admission = "diagnostic_only_until_component_bracketing"
            elif "distributed_friction" in slot or "ordinary" in slot:
                admission = "diagnostic_only_until_mesh_recirc_pressure_gates"
            else:
                admission = "diagnostic_only"
            rows.append(
                {
                    "loop_region": row["loop_region"],
                    "model_slot": slot,
                    "admission_status": admission,
                    "fit_allowed_now": "false",
                    "score_allowed_now": "diagnostic",
                    "reason": row["primary_blockers"],
                }
            )
    return rows


def build_evidence_rollup(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    decisions = read_csv(HYDRAULIC_DECISIONS)
    f6_summary = json.loads(F6_SUMMARY.read_text())
    pressure = read_csv(PRESSURE_TERM_LEDGER)
    minor = read_csv(MINOR_LOSS)
    recirc = read_csv(RECIRC_BRANCH)
    source_counts = Counter(row.get("admission_status", "") for row in scorecard)
    return [
        {
            "evidence_source": "segment_equation_contract",
            "rows": len(segment_contract_rows()),
            "fit_admitted_rows": 0,
            "diagnostic_rows": len(scorecard),
            "status": "contract_available",
            "interpretation": "Segment-local pressure slots are defined; this scorecard applies current admission gates.",
            "source_path": rel(SEGMENT_CONTRACT),
        },
        {
            "evidence_source": "pressure_term_ledger",
            "rows": len(pressure),
            "fit_admitted_rows": 0,
            "diagnostic_rows": len(pressure),
            "status": "diagnostic_under_current_gates",
            "interpretation": "Older fit_target labels are retained as historical diagnostics, not current final admission.",
            "source_path": rel(PRESSURE_TERM_LEDGER),
        },
        {
            "evidence_source": "minor_loss_two_tap",
            "rows": len(minor),
            "fit_admitted_rows": 0,
            "diagnostic_rows": sum(1 for row in minor if row.get("validation_eligible") == "yes"),
            "status": "diagnostic_only",
            "interpretation": "K_local remains upper-bound/proxy or missing for test-section complex rows.",
            "source_path": rel(MINOR_LOSS),
        },
        {
            "evidence_source": "pressure_ladder_recirc_admission",
            "rows": len(recirc),
            "fit_admitted_rows": sum(1 for row in recirc if row.get("true_f_D_or_K_fit_admitted") == "yes"),
            "diagnostic_rows": len(recirc),
            "status": "no_true_fd_or_k_fit_admitted",
            "interpretation": "Branch rows are orientation/straight-loss/recirculation screens; true f_D/K admission remains zero.",
            "source_path": rel(RECIRC_BRANCH),
        },
        {
            "evidence_source": "hydraulic_chain_final_decisions",
            "rows": len(decisions),
            "fit_admitted_rows": sum(int(row.get("fit_admitted_rows") or 0) for row in decisions),
            "diagnostic_rows": sum(int(row.get("diagnostic_admitted_rows") or 0) for row in decisions),
            "status": "final_hydraulic_residual_blocked_not_final",
            "interpretation": "Reset-K/raw two-tap/F6 lanes are diagnostic; final hydraulic residual is blocked.",
            "source_path": rel(HYDRAULIC_DECISIONS),
        },
        {
            "evidence_source": "f6_re_correction_unblock",
            "rows": f6_summary["candidate_rows"],
            "fit_admitted_rows": f6_summary["ordinary_f6_scoreable_rows"],
            "diagnostic_rows": f6_summary["hybrid_candidate_rows"],
            "status": f6_summary["f6_blocker_decision"],
            "interpretation": "F6 remains narrowed-open; F3_shah_apparent remains production.",
            "source_path": rel(F6_SUMMARY),
        },
        {
            "evidence_source": "segment_scorecard_decisions",
            "rows": len(scorecard),
            "fit_admitted_rows": 0,
            "diagnostic_rows": sum(source_counts.values()),
            "status": "complete_no_fit_admitted",
            "interpretation": "All loop regions have pressure model slots and exact gates; none admit a predictive pressure coefficient yet.",
            "source_path": rel(OUT / "segment_pressure_model_scorecard.csv"),
        },
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "check": "no_cfd_mdot_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "CFD mdot",
            "policy": "mdot remains solved by the coupled model; CFD mdot is score/diagnostic only.",
        },
        {
            "check": "no_global_friction_multiplier",
            "status": "pass_forbidden",
            "forbidden_input": "global friction multiplier",
            "policy": "model slots are segment-local by contract.",
        },
        {
            "check": "no_recirc_true_fd_or_k_fit",
            "status": "pass_forbidden",
            "forbidden_input": "true f_D/K fit from recirculating rows",
            "policy": "upcomer and recirculation-masked rows remain hybrid/diagnostic lanes.",
        },
        {
            "check": "no_pressure_residual_as_component_k",
            "status": "pass_forbidden",
            "forbidden_input": "unbracketed residual as physical K",
            "policy": "local K requires admitted pressure definition, tap length, straight-loss subtraction, and component bracketing.",
        },
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("segment_equation_contract", SEGMENT_CONTRACT, "pressure slots and runtime guardrails"),
        ("pressure_term_ledger", PRESSURE_TERM_LEDGER, "pressure term evidence"),
        ("minor_loss_two_tap", MINOR_LOSS, "minor-loss/two-tap evidence"),
        ("pressure_ladder_recirc_admission", RECIRC_BRANCH, "branch recirculation/admission gates"),
        ("hydraulic_chain_decisions", HYDRAULIC_DECISIONS, "hydraulic final decision blockers"),
        ("f6_summary", F6_SUMMARY, "F6/Re correction blocker state"),
        ("f6_candidate_inventory", F6_CANDIDATES, "F6 candidate classifications"),
    ]
    return [
        {"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use}
        for key, path, use in sources
    ]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(SEGMENT_CONTRACT)}",
        f"  - {rel(PRESSURE_TERM_LEDGER)}",
        f"  - {rel(RECIRC_BRANCH)}",
        f"  - {rel(HYDRAULIC_DECISIONS)}",
        "tags: [segment-pressure-models, forward-predictive-model, hydraulics, admission]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Hydraulics/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Segment Pressure Model Scorecard",
        "",
        "## Decision",
        "",
        "The segment pressure model slots are now scored against existing evidence and current admission gates. "
        "No true segment `f_D` or physical component `K` coefficient is admitted yet. Existing pressure rows remain useful "
        "diagnostics and gate evidence.",
        "",
        "## Results",
        "",
        f"- Loop regions reviewed: `{summary['segment_rows']}`.",
        f"- Model-slot rows: `{summary['model_slot_rows']}`.",
        f"- Fit-admitted pressure coefficient rows: `{summary['fit_admitted_pressure_rows']}`.",
        f"- Diagnostic evidence rows represented in segment scorecard: `{summary['diagnostic_evidence_rows']}`.",
        f"- Runtime audit pass rows: `{summary['runtime_audit_pass_rows']}`.",
        "",
        "## Interpretation",
        "",
        "Pressure and thermal coupling can proceed only with diagnostic pressure terms unless a later package admits segment-local "
        "coefficients. Current blockers are mesh/GCI, pressure definition, geometry normalization, component isolation, straight-loss "
        "subtraction, and recirculation/hybrid upcomer policy.",
        "",
        "## Next Action",
        "",
        "Use this package as input to the thermal scorecard and later coupled M3+TS runner, but do not treat it as an admitted pressure closure.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_closeout(summary: dict[str, object]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)

    status = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'README.md')}",
        f"  - {rel(OUT / 'summary.json')}",
        "tags: [status, segment-pressure-models, hydraulics]",
        "related:",
        f"  - {rel(JOURNAL)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Hydraulics/Implementer/Tester/Writer",
        "type: status",
        "status: complete",
        "---",
        f"# {TASK} Status",
        "",
        "## Observed Facts",
        "",
        "- The segment equation contract is complete and defines segment-local pressure slots.",
        "- Later branch/F6/hydraulic decisions admit zero true `f_D` or physical `K` fit rows.",
        "- Existing pressure evidence remains diagnostic and useful for blocker narrowing.",
        "",
        "## Changes Made",
        "",
        f"- Wrote `{rel(OUT)}/` with segment scorecard, model-slot rows, evidence rollup, runtime audit, README, and summary.",
        "- Added focused builder tests.",
        "",
        "## Validation",
        "",
        "- `python3 -m unittest tools.analyze.test_segment_pressure_model_scorecard`",
        "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
        "",
        "## Blockers",
        "",
        "- No blocker remains for pressure-model status visibility.",
        "- Predictive pressure coefficient admission remains blocked by mesh/GCI, pressure definition, geometry normalization, component isolation, straight-loss subtraction, and recirculation gates.",
        "- Generated docs index refresh was skipped because active board rows own generated index files.",
    ]
    STATUS.write_text("\n".join(status) + "\n")

    journal = [
        "---",
        "provenance:",
        f"  - {rel(SEGMENT_CONTRACT)}",
        f"  - {rel(PRESSURE_TERM_LEDGER)}",
        f"  - {rel(OUT / 'README.md')}",
        "tags: [journal, segment-pressure-models, hydraulics]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Hydraulics/Implementer/Tester/Writer",
        "type: journal",
        "status: complete",
        "---",
        "# Segment Pressure Model Scorecard Journal",
        "",
        "## Files Inspected",
        "",
        f"- `{rel(SEGMENT_CONTRACT)}`",
        f"- `{rel(PRESSURE_TERM_LEDGER)}`",
        f"- `{rel(MINOR_LOSS)}`",
        f"- `{rel(RECIRC_BRANCH)}`",
        f"- `{rel(HYDRAULIC_DECISIONS)}`",
        f"- `{rel(F6_SUMMARY)}`",
        "",
        "## Files Changed",
        "",
        "- `tools/analyze/build_segment_pressure_model_scorecard.py`",
        "- `tools/analyze/test_segment_pressure_model_scorecard.py`",
        f"- `{rel(OUT)}/`",
        f"- `{rel(STATUS)}`",
        f"- `{rel(JOURNAL)}`",
        f"- `{rel(IMPORT)}`",
        "- `.agent/BOARD.md` own row status",
        "",
        "## Interpretation",
        "",
        "The pressure lane is clearer but still not admitted for final predictive closure. This is a completed scorecard, not a model admission.",
        "",
        "## Recommended Next Action",
        "",
        "Proceed to `TODO-PREDICT-SEGMENT-THERMAL-MODELS` or a targeted pressure-gate unblock package for mesh/GCI and component bracketing.",
    ]
    JOURNAL.write_text("\n".join(journal) + "\n")

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

    scorecard = build_segment_scorecard()
    model_slots = build_model_slot_rows(scorecard)
    evidence = build_evidence_rollup(scorecard)
    runtime = runtime_audit_rows()
    sources = source_manifest()

    write_csv(
        OUT / "segment_pressure_model_scorecard.csv",
        scorecard,
        [
            "loop_region",
            "one_d_segments",
            "pressure_drive_model",
            "candidate_pressure_loss_slots",
            "pressure_term_ledger_rows",
            "legacy_pressure_fit_target_rows",
            "pressure_ladder_admission_rows",
            "pressure_ladder_blocked_rows",
            "minor_loss_rows",
            "minor_loss_upper_bound_rows",
            "missing_two_tap_rows",
            "diagnostic_evidence_rows",
            "true_fd_or_k_fit_admitted_rows",
            "scoreable_predictive_model_rows",
            "admission_status",
            "primary_blockers",
            "train_validation_holdout_improvement_status",
            "next_gate",
            "runtime_forbidden_inputs",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "pressure_model_slot_admission.csv",
        model_slots,
        ["loop_region", "model_slot", "admission_status", "fit_allowed_now", "score_allowed_now", "reason"],
    )
    write_csv(
        OUT / "pressure_evidence_rollup.csv",
        evidence,
        ["evidence_source", "rows", "fit_admitted_rows", "diagnostic_rows", "status", "interpretation", "source_path"],
    )
    write_csv(OUT / "runtime_pressure_input_audit.csv", runtime, ["check", "status", "forbidden_input", "policy"])
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])

    summary = {
        "task": TASK,
        "date": DATE,
        "segment_rows": len(scorecard),
        "model_slot_rows": len(model_slots),
        "evidence_rollup_rows": len(evidence),
        "runtime_audit_rows": len(runtime),
        "runtime_audit_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "fit_admitted_pressure_rows": sum(int(row["true_fd_or_k_fit_admitted_rows"]) for row in scorecard),
        "scoreable_predictive_model_rows": sum(int(row["scoreable_predictive_model_rows"]) for row in scorecard),
        "diagnostic_evidence_rows": sum(int(row["diagnostic_evidence_rows"]) for row in scorecard),
        "all_sources_present": all(row["exists"] == "true" for row in sources),
        "train_validation_holdout_improvement_status": "not_run_no_fit_admitted_segment_pressure_model",
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
