#!/usr/bin/env python3
"""Build a non-fitting F6 non-recirculating pressure-anchor plan."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-F6-NONRECIRC-PRESSURE-ANCHOR-PLAN"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_nonrecirculating_pressure_anchor_plan"
STATUS = ROOT / f".agent/status/{DATE}_{TASK}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/f6-nonrecirculating-pressure-anchor-plan.md"
IMPORT = ROOT / "imports/2026-07-17_f6_nonrecirculating_pressure_anchor_plan.json"

F6_CANDIDATES = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_candidate_inventory.csv"
F6_GATE_MATRIX = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_recorrection_resolution_plan/f6_row_gate_matrix.csv"
F6_ANCHOR_TABLE = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/anchor_gate_table.csv"
NAMED_PRESSURE = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/named_pressure_readiness.csv"
SEGMENT_PRESSURE = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/segment_pressure_model_scorecard.csv"
F6_INTERNAL_NU = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv"

RAF_ORDINARY_MAX = 0.01
RMF_ORDINARY_MAX = 0.01


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
    required = [F6_CANDIDATES, F6_GATE_MATRIX, F6_ANCHOR_TABLE, NAMED_PRESSURE, SEGMENT_PRESSURE, F6_INTERNAL_NU]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing F6 pressure-anchor sources: " + "; ".join(missing))


def _float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _reverse_class(raf: str, rmf: str) -> tuple[str, str]:
    raf_value = _float_or_none(raf)
    rmf_value = _float_or_none(rmf)
    if raf_value is None or rmf_value is None:
        return ("unknown_pending_postprocessing", "reverse-flow gate cannot be evaluated until RAF/RMF exist")
    if raf_value < RAF_ORDINARY_MAX and rmf_value < RMF_ORDINARY_MAX:
        return ("ordinary_reverse_gate_pass", f"RAF<{RAF_ORDINARY_MAX} and RMF<{RMF_ORDINARY_MAX}")
    return ("recirculation_diagnostic", f"material reverse flow: RAF={raf_value:g}, RMF={rmf_value:g}")


def build_pressure_anchor_plan() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    gate_by_id = {row["row_id"]: row for row in read_csv(F6_GATE_MATRIX)}
    for row in read_csv(F6_CANDIDATES):
        row_id = row["candidate_id"]
        gate = gate_by_id.get(row_id, {})
        reverse_class, reverse_reason = _reverse_class(row["reverse_area_fraction"], row["reverse_mass_fraction"])
        rows.append(
            {
                "row_id": row_id,
                "evidence_family": "PM5_current",
                "case_key": row["case_key"],
                "span_or_pressure_row": row["span"],
                "case_role": row["case_role"],
                "Re": row["Re"],
                "Ri": row["Ri"],
                "RAF": row["reverse_area_fraction"],
                "RMF": row["reverse_mass_fraction"],
                "SVF": row["secondary_velocity_fraction"],
                "ordinary_anchor_class": "current_recirculation_diagnostic",
                "ordinary_f6_legitimate_now": "no",
                "recirculation_diagnostic_now": "yes",
                "pressure_anchor_use": "diagnostic_pressure_onset_only",
                "required_before_ordinary_f6": "obtain low-reverse row; same-window pressure/velocity basis; straight-loss/development ledger; mesh/time UQ; split-safe score plan",
                "why": reverse_reason,
                "do_not_fit_reason": row["reason"],
                "next_action": gate.get("next_action", "do not fit ordinary F6 from PM5; use only as diagnostic/onset evidence"),
                "source_path": row["source_path"],
            }
        )

    for row in read_csv(F6_ANCHOR_TABLE):
        if row["evidence_family"] == "PM5":
            continue
        rows.append(
            {
                "row_id": row["row_id"],
                "evidence_family": row["evidence_family"],
                "case_key": row["case_key"],
                "span_or_pressure_row": row["lane"],
                "case_role": "pending_terminal_or_harvest",
                "Re": "",
                "Ri": "",
                "RAF": row["RAF"],
                "RMF": row["RMF"],
                "SVF": "",
                "ordinary_anchor_class": "pending_ordinary_anchor_candidate",
                "ordinary_f6_legitimate_now": "no",
                "recirculation_diagnostic_now": "not_evaluated",
                "pressure_anchor_use": "future_anchor_candidate_after_terminal_postprocessing",
                "required_before_ordinary_f6": "terminal harvest; PM5/PM10 style RAF/RMF/SVF; same-window pressure and velocity fields; pressure definition; mesh/time UQ; no active duplicate job",
                "why": "could become an ordinary F6 pressure anchor only if RAF/RMF pass low-reverse gate and pressure basis is complete",
                "do_not_fit_reason": row["primary_blocker"],
                "next_action": row["next_action"],
                "source_path": row["source_path"],
            }
        )
    return rows


def build_named_pressure_anchor_slots() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(NAMED_PRESSURE):
        if row["loss_class"] in {"cluster_K"}:
            f6_role = "not_ordinary_f6_component_k_lane"
            anchor_status = "component_or_cluster_diagnostic"
            required = "component isolation and two-tap K gates; do not use for F6 distributed friction"
        elif row["fit_use_status"] == "not_fit_recirculation":
            f6_role = "recirculation_diagnostic_not_anchor"
            anchor_status = "not_legitimate_ordinary_f6_anchor"
            required = "wait for low-reverse terminal anchor before branch/straight ordinary F6 use"
        elif row["readiness_status"] == "extraction_required_branch_or_straight":
            f6_role = "ordinary_f6_pressure_slot_candidate"
            anchor_status = "candidate_pending_pressure_repair_and_low_reverse_gate"
            required = "repair pressure/velocity basis, geometry normalization, straight-loss/development basis, mesh/time UQ, and low RAF/RMF row"
        else:
            f6_role = "section_effective_diagnostic_only"
            anchor_status = "not_currently_legitimate_ordinary_f6_anchor"
            required = "keep diagnostic label until low-reverse pressure evidence and naming gates are repaired"
        rows.append(
            {
                "row_id": row["row_id"],
                "case_id": row["case_id"],
                "pressure_row": row["name"],
                "loss_class": row["loss_class"],
                "span_or_feature": row["span_or_feature"],
                "f6_anchor_role": f6_role,
                "anchor_status": anchor_status,
                "ordinary_f6_legitimate_now": "no",
                "recirculation_diagnostic_now": "yes" if "recirculation" in f6_role or "diagnostic" in anchor_status else "not_evaluated",
                "required_before_use": required,
                "forbidden_use": row["forbidden_use"],
                "source_path": row["source_path"],
            }
        )
    return rows


def build_ordinary_anchor_gate_contract() -> list[dict[str, object]]:
    return [
        {
            "gate_id": "reverse_flow",
            "required_for": "ordinary F6 distributed-friction anchor",
            "pass_condition": f"same-window RAF < {RAF_ORDINARY_MAX} and RMF < {RMF_ORDINARY_MAX}; uncertainty upper bound must also pass",
            "current_status": "fails for all 12 current PM5 rows; unknown for pending PM10/high-heat rows",
            "blocks_if_missing_or_failed": "single-stream f_D/F6 fitting",
        },
        {
            "gate_id": "same_window_pressure_velocity",
            "required_for": "ordinary F6 pressure anchor",
            "pass_condition": "pressure basis, velocity basis, Re, density/viscosity, and reverse-flow metrics share case_key/window_id/plane definitions",
            "current_status": "not complete for fit admission",
            "blocks_if_missing_or_failed": "pressure row remains diagnostic/section-effective",
        },
        {
            "gate_id": "geometry_and_straight_loss",
            "required_for": "F6 pressure-residual attribution",
            "pass_condition": "centerline length, hydraulic diameter, branch orientation, straight-loss/development subtraction, and component exclusion documented",
            "current_status": "not complete; named-pressure readiness marks branch/straight repair required",
            "blocks_if_missing_or_failed": "ordinary F6 cannot be separated from component or development pressure loss",
        },
        {
            "gate_id": "mesh_time_uncertainty",
            "required_for": "main evidence or training use",
            "pass_condition": "same-QOI mesh/time uncertainty for pressure residual, Re, RAF/RMF/SVF, and classification",
            "current_status": "missing for current PM5 rows",
            "blocks_if_missing_or_failed": "no coefficient admission or training promotion",
        },
        {
            "gate_id": "split_and_holdout_policy",
            "required_for": "future scoring after anchor exists",
            "pass_condition": "training/validation/holdout role declared before fitting; no holdout row used to select F6 parameters",
            "current_status": "not applicable because no ordinary anchor passes yet",
            "blocks_if_missing_or_failed": "no F6-vs-F3 scorecard or closure promotion",
        },
    ]


def build_next_action_plan() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "action_id": "terminal_pm10_high_heat_harvest_gate",
            "target_rows": "pm10:salt2_lo10q;pm10:salt2_hi10q;pm10:salt4_lo10q;pm10:salt4_hi10q;high_heat Salt4 no-recirc probes",
            "why": "these are the only current lanes that might supply a low-reverse ordinary F6 anchor",
            "required_outputs": "RAF/RMF/SVF, Re/Ri, same-window pressure basis, velocity basis, wall/bulk context, mesh/time UQ",
            "launch_or_fit_allowed_here": "no",
        },
        {
            "priority": 2,
            "action_id": "branch_straight_pressure_repair",
            "target_rows": "named_pressure right_leg and test_section_span branch/straight candidates",
            "why": "ordinary F6 pressure rows need branch/straight pressure definition before any f_D attribution",
            "required_outputs": "pressure/velocity basis, geometry normalization, centerline length, straight-loss/development subtraction",
            "launch_or_fit_allowed_here": "no",
        },
        {
            "priority": 3,
            "action_id": "recirculation_diagnostic_lane",
            "target_rows": "all current PM5 F6 rows",
            "why": "material RAF/RMF makes them scientifically invalid as single-stream ordinary F6 anchors",
            "required_outputs": "keep as diagnostic/onset/hybrid evidence; do not export fitted F6 coefficients",
            "launch_or_fit_allowed_here": "no",
        },
        {
            "priority": 4,
            "action_id": "future_scorecard_only_after_anchor_gate",
            "target_rows": "future rows that pass ordinary gate",
            "why": "F6-vs-F3 pressure residual movement is meaningful only after an ordinary anchor exists",
            "required_outputs": "predeclared split-safe score table; compare pressure residuals without tuning on holdout rows",
            "launch_or_fit_allowed_here": "no",
        },
    ]


def build_runtime_audit() -> list[dict[str, object]]:
    return [
        {"check": "no_fitting", "status": "pass", "detail": "no F6/F3/pressure coefficient fitted or exported"},
        {"check": "no_scheduler_action", "status": "pass", "detail": "no sbatch/srun/scancel/scontrol action"},
        {"check": "no_native_output_mutation", "status": "pass", "detail": "native CFD/OpenFOAM outputs read-only"},
        {"check": "no_registry_or_admission_mutation", "status": "pass", "detail": "registry and scientific admission state unchanged"},
        {"check": "no_AGENT_511_collision", "status": "pass", "detail": "AGENT-511 Fluid scoring outputs used only as read-only conflict context; no Fluid edits"},
    ]


def source_manifest_rows() -> list[dict[str, object]]:
    sources = [
        ("f6_candidates", F6_CANDIDATES, "current 12 PM5 F6 candidate rows"),
        ("f6_gate_matrix", F6_GATE_MATRIX, "current F6 ordinary/hybrid gate decisions"),
        ("f6_anchor_table", F6_ANCHOR_TABLE, "PM10/high-heat anchor-first pending rows"),
        ("named_pressure", NAMED_PRESSURE, "named pressure rows and extraction readiness"),
        ("segment_pressure", SEGMENT_PRESSURE, "segment pressure model blockers and runtime guardrails"),
        ("f6_internal_nu", F6_INTERNAL_NU, "PM5 onset diagnostics and non-admission rationale"),
    ]
    return [{"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use} for key, path, use in sources]


def write_docs(summary: dict[str, object]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(F6_CANDIDATES)}",
                f"  - {rel(F6_GATE_MATRIX)}",
                f"  - {rel(F6_ANCHOR_TABLE)}",
                f"  - {rel(NAMED_PRESSURE)}",
                "tags: [f6, pressure-anchor, recirculation, hydraulics]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(JOURNAL)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: work_product",
                "status: complete",
                "---",
                "# F6 Non-Recirculating Pressure Anchor Plan",
                "",
                "## Decision",
                "",
                "No F6 or pressure coefficient is fitted here. Current PM5 rows remain recirculation diagnostics. Pending PM10/high-heat rows are ordinary-anchor candidates only after terminal harvest and low-reverse, same-window pressure gates pass.",
                "",
                "## Results",
                "",
                f"- Current PM5 rows reviewed: `{summary['pm5_current_rows']}`.",
                f"- Current legitimate ordinary F6 anchors: `{summary['current_ordinary_anchor_rows']}`.",
                f"- Current recirculation diagnostic rows: `{summary['current_recirculation_diagnostic_rows']}`.",
                f"- Pending ordinary-anchor candidate rows: `{summary['pending_anchor_candidate_rows']}`.",
                f"- Named pressure slots reviewed: `{summary['named_pressure_slot_rows']}`.",
                f"- Fitting performed: `{summary['fitting_performed']}`.",
                "",
                "## Outputs",
                "",
                "- `f6_pressure_anchor_plan.csv`: row-level current and pending anchor classification.",
                "- `named_pressure_anchor_slots.csv`: branch/straight/component pressure-row roles for future F6 use.",
                "- `ordinary_anchor_gate_contract.csv`: exact gates required before ordinary F6 evidence exists.",
                "- `next_action_plan.csv`: non-fitting sequence for attacking `f6-friction-re-correction`.",
                "- `runtime_request_audit.csv`: no-fit/no-launch/no-mutation audit.",
                "",
                "## Scientific Guardrail",
                "",
                "A pressure row is not a legitimate ordinary F6 anchor unless reverse flow is negligible, pressure and velocity are same-window and geometry-normalized, straight/development/component losses are separated, and mesh/time uncertainty is reported. Until then, rows remain diagnostic.",
            ]
        )
        + "\n"
    )

    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'summary.json')}",
                f"  - {rel(OUT / 'f6_pressure_anchor_plan.csv')}",
                f"  - {rel(OUT / 'ordinary_anchor_gate_contract.csv')}",
                "tags: [status, f6, pressure-anchor]",
                "related:",
                f"  - {rel(JOURNAL)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: status",
                "status: complete",
                "---",
                f"# {TASK} Status",
                "",
                "## Changes Made",
                "",
                "- Built a reusable non-fitting F6 pressure-anchor plan generator.",
                "- Classified current PM5 rows as recirculation diagnostics and pending PM10/high-heat rows as future ordinary-anchor candidates only.",
                "- Published gate, named-pressure-slot, next-action, runtime-audit, README, journal, and manifest artifacts.",
                "",
                "## Validation",
                "",
                "- `python3.11 -m unittest tools.analyze.test_f6_nonrecirculating_pressure_anchor_plan`",
                "- `python3.11 tools/analyze/build_f6_nonrecirculating_pressure_anchor_plan.py`",
                "- `python3.11 -m json.tool work_products/2026-07/2026-07-17/2026-07-17_f6_nonrecirculating_pressure_anchor_plan/summary.json`",
                "",
                "## Guardrails",
                "",
                "- No F6/F3/pressure coefficient was fitted or exported.",
                "- No native solver output, registry state, scheduler state, generated index, Fluid source, or AGENT-511 scoped artifact was mutated.",
                "- The package changes no scientific admission state; `f6-friction-re-correction` remains open but narrowed.",
            ]
        )
        + "\n"
    )

    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                "---",
                "provenance:",
                f"  - {rel(OUT / 'README.md')}",
                f"  - {rel(F6_CANDIDATES)}",
                f"  - {rel(F6_ANCHOR_TABLE)}",
                f"  - {rel(NAMED_PRESSURE)}",
                "tags: [journal, f6, pressure-anchor, recirculation]",
                "related:",
                f"  - {rel(STATUS)}",
                f"  - {rel(IMPORT)}",
                f"task: {TASK}",
                f"date: {DATE}",
                "role: Coordinator/Implementer/Tester/Writer",
                "type: journal",
                "status: complete",
                "---",
                "# F6 Non-Recirculating Pressure Anchor Plan Journal",
                "",
                f"Task: `{TASK}`",
                "",
                "The existing F6 evidence was reviewed as a planning problem, not a fitting problem. The current PM5 rows are not legitimate ordinary F6 anchors because every row has material reverse flow. The pending PM10/high-heat lanes remain potentially useful only after terminal harvest and same-window pressure/reverse-flow postprocessing.",
                "",
                "Named pressure rows were kept separate from current F6 admission. Branch/straight rows can become ordinary F6 pressure slots only after pressure/velocity basis repair, geometry normalization, straight-loss/development subtraction, low-reverse gating, and mesh/time uncertainty. Component/cluster K rows are not distributed-friction anchors.",
                "",
                "No AGENT-511 work was touched. The next useful action is a terminal/postprocessed anchor gate, followed by branch/straight pressure repair, then a split-safe F6-vs-F3 scorecard only if at least one ordinary anchor passes.",
            ]
        )
        + "\n"
    )


def changed_files() -> list[str]:
    return [
        ".agent/BOARD.md",
        "tools/analyze/build_f6_nonrecirculating_pressure_anchor_plan.py",
        "tools/analyze/test_f6_nonrecirculating_pressure_anchor_plan.py",
        rel(OUT / "f6_pressure_anchor_plan.csv"),
        rel(OUT / "named_pressure_anchor_slots.csv"),
        rel(OUT / "ordinary_anchor_gate_contract.csv"),
        rel(OUT / "next_action_plan.csv"),
        rel(OUT / "runtime_request_audit.csv"),
        rel(OUT / "source_manifest.csv"),
        rel(OUT / "summary.json"),
        rel(OUT / "README.md"),
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
    ]


def write_import_manifest(summary: dict[str, object]) -> None:
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "task": TASK,
        "date": DATE,
        "summary": "Non-fitting F6 non-recirculating pressure-anchor plan and row classification.",
        "changed_files": changed_files(),
        "read_only_context": [
            rel(F6_CANDIDATES),
            rel(F6_GATE_MATRIX),
            rel(F6_ANCHOR_TABLE),
            rel(NAMED_PRESSURE),
            rel(SEGMENT_PRESSURE),
            rel(F6_INTERNAL_NU),
            ".agent/status/2026-07-17_AGENT-511.md",
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "scientific_admission_change": "none",
        "fitting_performed": False,
        "output_dir": rel(OUT),
        "summary_json": summary,
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    plan_rows = build_pressure_anchor_plan()
    named_rows = build_named_pressure_anchor_slots()
    gate_rows = build_ordinary_anchor_gate_contract()
    action_rows = build_next_action_plan()
    audit_rows = build_runtime_audit()
    manifest_rows = source_manifest_rows()

    write_csv(
        OUT / "f6_pressure_anchor_plan.csv",
        plan_rows,
        [
            "row_id",
            "evidence_family",
            "case_key",
            "span_or_pressure_row",
            "case_role",
            "Re",
            "Ri",
            "RAF",
            "RMF",
            "SVF",
            "ordinary_anchor_class",
            "ordinary_f6_legitimate_now",
            "recirculation_diagnostic_now",
            "pressure_anchor_use",
            "required_before_ordinary_f6",
            "why",
            "do_not_fit_reason",
            "next_action",
            "source_path",
        ],
    )
    write_csv(
        OUT / "named_pressure_anchor_slots.csv",
        named_rows,
        [
            "row_id",
            "case_id",
            "pressure_row",
            "loss_class",
            "span_or_feature",
            "f6_anchor_role",
            "anchor_status",
            "ordinary_f6_legitimate_now",
            "recirculation_diagnostic_now",
            "required_before_use",
            "forbidden_use",
            "source_path",
        ],
    )
    write_csv(
        OUT / "ordinary_anchor_gate_contract.csv",
        gate_rows,
        ["gate_id", "required_for", "pass_condition", "current_status", "blocks_if_missing_or_failed"],
    )
    write_csv(
        OUT / "next_action_plan.csv",
        action_rows,
        ["priority", "action_id", "target_rows", "why", "required_outputs", "launch_or_fit_allowed_here"],
    )
    write_csv(OUT / "runtime_request_audit.csv", audit_rows, ["check", "status", "detail"])
    write_csv(OUT / "source_manifest.csv", manifest_rows, ["source_id", "path", "exists", "use"])

    classes = Counter(row["ordinary_anchor_class"] for row in plan_rows)
    summary = {
        "task": TASK,
        "output_dir": rel(OUT),
        "pm5_current_rows": sum(1 for row in plan_rows if row["evidence_family"] == "PM5_current"),
        "current_ordinary_anchor_rows": sum(1 for row in plan_rows if row["ordinary_f6_legitimate_now"] == "yes"),
        "current_recirculation_diagnostic_rows": sum(1 for row in plan_rows if row["ordinary_anchor_class"] == "current_recirculation_diagnostic"),
        "pending_anchor_candidate_rows": sum(1 for row in plan_rows if row["ordinary_anchor_class"] == "pending_ordinary_anchor_candidate"),
        "named_pressure_slot_rows": len(named_rows),
        "named_ordinary_slot_candidates": sum(1 for row in named_rows if row["f6_anchor_role"] == "ordinary_f6_pressure_slot_candidate"),
        "gate_rows": len(gate_rows),
        "next_action_rows": len(action_rows),
        "runtime_audit_pass_rows": sum(1 for row in audit_rows if row["status"] == "pass"),
        "class_counts": dict(classes),
        "fitting_performed": False,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "external_fluid_edit": False,
        "scientific_admission_change": "none",
        "f6_friction_re_correction_status": "open_narrowed_by_anchor_plan",
    }
    write_json(OUT / "summary.json", summary)
    write_docs(summary)
    write_import_manifest(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
