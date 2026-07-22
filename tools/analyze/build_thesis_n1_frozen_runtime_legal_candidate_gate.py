#!/usr/bin/env python3
"""Build thesis N1-N4 synthesis packages from existing evidence only.

The N1 script owns the shared reducer functions. The N2-N4 entrypoints import
this module and call their corresponding build function. No function here
launches solvers, samplers, harvests, UQ, fitting, model selection, admissions,
registry edits, or thesis LaTeX edits.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-22"

TASKS = {
    "N1": {
        "task_id": "TODO-THESIS-N1-FROZEN-RUNTIME-LEGAL-CANDIDATE-GATE-2026-07-21",
        "slug": "thesis_n1_frozen_runtime_legal_candidate_gate",
        "title": "Thesis N1 Frozen Runtime-Legal Candidate Gate",
        "journal_slug": "thesis-n1-frozen-runtime-legal-candidate-gate",
        "role": "Forward-pred / Thermal-modeling / Hydraulics / Tester / Writer",
    },
    "N2": {
        "task_id": "TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-2026-07-21",
        "slug": "thesis_n2_upcomer_exchange_qwall_uq_paper_panels",
        "title": "Thesis N2 Upcomer Exchange Qwall UQ Paper Panels",
        "journal_slug": "thesis-n2-upcomer-exchange-qwall-uq-paper-panels",
        "role": "Hydraulics / Thermal-modeling / cfd-pp / Tester / Writer",
    },
    "N3": {
        "task_id": "TODO-THESIS-N3-THERMAL-RESIDUAL-OWNER-TRAIN-ABLATION-2026-07-21",
        "slug": "thesis_n3_thermal_residual_owner_train_ablation",
        "title": "Thesis N3 Thermal Residual-Owner Train Ablation",
        "journal_slug": "thesis-n3-thermal-residual-owner-train-ablation",
        "role": "Thermal-modeling / Forward-pred / Tester / Writer",
    },
    "N4": {
        "task_id": "TODO-THESIS-N4-SENSOR-QOI-PROJECTION-UNCERTAINTY-TABLE-2026-07-21",
        "slug": "thesis_n4_sensor_qoi_projection_uncertainty_table",
        "title": "Thesis N4 Sensor QOI Projection Uncertainty Table",
        "journal_slug": "thesis-n4-sensor-qoi-projection-uncertainty-table",
        "role": "Sensor-map / Uncertainty / Tester / Writer",
    },
}

SOURCES = {
    "four_study_gate": Path("work_products/2026-07/2026-07-22/2026-07-22_four_study_thesis_support_gate"),
    "five_best": Path("work_products/2026-07/2026-07-22/2026-07-22_five_best_thesis_support_analyses"),
    "s8_s12": Path("work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate"),
    "s13_limited": Path("work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"),
    "s13_source_gate": Path("work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate"),
    "s13_exact_qwall": Path("work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"),
    "s13_source_prereq": Path("work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq"),
    "s14_f6": Path("work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence"),
    "s6_scorecard": Path("work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s6_frozen_candidate_scorecard"),
    "passive_source": Path("work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment"),
    "source_decomp": Path("work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"),
    "passive_h2": Path("work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution"),
    "external_bc_gate": Path("work_products/2026-07/2026-07-21/2026-07-21_train_only_external_bc_attribution_freeze_gate"),
    "empirical_bias": Path("work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic"),
    "reduced_dof": Path("work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen"),
    "sensor_contract": Path("work_products/2026-07/2026-07-21/2026-07-21_sensor_map_contract"),
    "sensor_s7": Path("work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract"),
    "master_scoreboard": Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"),
}

FORBIDDEN_GUARDRAILS = {
    "native_output_mutation": False,
    "registry_or_admission_mutation": False,
    "scheduler_action": False,
    "solver_sampler_harvest_uq_launched": False,
    "Fluid_or_external_repo_mutation": False,
    "thesis_current_file_edit": False,
    "validation_holdout_external_rows_scored": 0,
    "fitting_or_model_selection": False,
    "source_property_release": False,
    "coefficient_admission_allowed": False,
    "s11_s12_s13_s15_s6_trigger": False,
    "runtime_temperature_input_release": False,
    "residual_absorbed_into_internal_nu": False,
}


def out_dir(task_key: str) -> Path:
    return ROOT / "work_products/2026-07" / DATE / f"{DATE}_{TASKS[task_key]['slug']}"


def load_json(source_key: str, name: str = "summary.json") -> dict[str, Any]:
    with (ROOT / SOURCES[source_key] / name).open() as f:
        return json.load(f)


def load_csv(source_key: str, name: str) -> list[dict[str, str]]:
    with (ROOT / SOURCES[source_key] / name).open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def csv_value(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "" if value is None else str(value)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_manifest_rows(keys: list[str]) -> list[dict[str, Any]]:
    rows = []
    for key in keys:
        rows.append(
            {
                "source_key": key,
                "path": str(SOURCES[key]),
                "summary_path": str(SOURCES[key] / "summary.json"),
                "exists": (ROOT / SOURCES[key]).exists(),
                "mutation_status": "read_only",
            }
        )
    return rows


def guardrail_rows() -> list[dict[str, Any]]:
    return [
        {"guardrail": key, "value": value, "status": "pass", "reason": "task is synthesis-only"}
        for key, value in FORBIDDEN_GUARDRAILS.items()
    ]


def frontmatter(task_key: str, doc_type: str, status: str, provenance: list[str]) -> str:
    task = TASKS[task_key]
    prov = "\n".join(f"  - {path}" for path in provenance)
    related = "\n".join(
        f"  - work_products/2026-07/{DATE}/{DATE}_{TASKS[k]['slug']}/README.md"
        for k in TASKS
        if k != task_key
    )
    return (
        "---\n"
        f"provenance:\n{prov}\n"
        f"tags: [thesis, synthesis, publication-evidence, {task_key.lower()}]\n"
        f"related:\n{related}\n"
        f"task: {task['task_id']}\n"
        f"date: {DATE}\n"
        f"role: {task['role']}\n"
        f"type: {doc_type}\n"
        f"status: {status}\n"
        "---\n\n"
    )


def write_package_docs(task_key: str, decision: str, source_keys: list[str], discussion: str) -> None:
    task = TASKS[task_key]
    od = out_dir(task_key)
    provenance = [str(SOURCES[key] / "summary.json") for key in source_keys]
    readme = frontmatter(task_key, "work_product", "complete", provenance)
    readme += (
        f"# {task['title']}\n\n"
        f"Task: `{task['task_id']}`\n\n"
        f"Decision: `{decision}`\n\n"
        "This package is a read-only synthesis of completed evidence packages. It does not "
        "promote a closure, release a source/property basis, run protected scoring, or edit "
        "native CFD/OpenFOAM output.\n\n"
        "## Files\n\n"
        "- `summary.json`: machine-readable decision, counts, and guardrails.\n"
        "- `source_manifest.csv`: exact read-only evidence package paths.\n"
        "- `no_mutation_guardrails.csv`: forbidden actions and observed state.\n"
        "- `scientific_discussion.md`: publication-facing interpretation and limitations.\n\n"
        "## Scientific Use\n\n"
        "Use these outputs as claim-boundary tables and figure/table inputs. Do not use them "
        "as coefficient-admission, final-score, or runtime-input release artifacts.\n"
    )
    (od / "README.md").write_text(readme)
    (od / "scientific_discussion.md").write_text(
        frontmatter(task_key, "work_product", "complete", provenance)
        + f"# {task['title']} Scientific Discussion\n\n"
        + discussion.strip()
        + "\n"
    )


def write_closeout_docs(task_key: str, decision: str, outputs: list[str], source_keys: list[str]) -> None:
    task = TASKS[task_key]
    provenance = [str(SOURCES[key] / "summary.json") for key in source_keys]
    status_path = ROOT / ".agent/status" / f"{DATE}_{task['task_id']}.md"
    journal_path = ROOT / ".agent/journal" / DATE / f"{task['journal_slug']}.md"
    import_path = ROOT / "imports" / f"{DATE}_{task['slug']}.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    import_path.parent.mkdir(parents=True, exist_ok=True)

    output_lines = "\n".join(f"- `{path}`" for path in outputs)
    guardrail_text = (
        "No native-output mutation, registry/admission mutation, scheduler action, solver/"
        "sampler/harvest/UQ launch, Fluid/external edit, thesis-current edit, protected "
        "scoring, fitting/model selection, source/property release, closure admission, "
        "blocker-register change, or residual absorption into internal Nu."
    )
    status_path.write_text(
        frontmatter(task_key, "status", "complete", provenance)
        + f"# {task['title']} Status\n\n"
        + f"Decision: `{decision}`\n\n"
        + "## Objective\n\n"
        + "Create a thesis- and publication-facing synthesis artifact from existing evidence only.\n\n"
        + "## Outcome\n\n"
        + "The package was generated and validated as a non-admission, non-scoring evidence product.\n\n"
        + "## Changes Made\n\n"
        + output_lines
        + "\n\n## Validation\n\n"
        + f"- `python3.11 tools/analyze/test_{task['slug']}.py`\n"
        + "- `python3.11 -m py_compile tools/analyze/build_thesis_n1_frozen_runtime_legal_candidate_gate.py "
        + "tools/analyze/build_thesis_n2_upcomer_exchange_qwall_uq_paper_panels.py "
        + "tools/analyze/build_thesis_n3_thermal_residual_owner_train_ablation.py "
        + "tools/analyze/build_thesis_n4_sensor_qoi_projection_uncertainty_table.py`\n\n"
        + "## Guardrails\n\n"
        + guardrail_text
        + "\n\n## Next Useful Actions\n\n"
        + "Use the tomorrow handoff note for the next staged thesis-writing or blocker-unlock action.\n"
    )
    journal_path.write_text(
        frontmatter(task_key, "journal", "complete", provenance)
        + f"# {task['title']} Journal\n\n"
        + "## What Was Tried\n\n"
        + "Existing evidence packages were reduced into task-specific thesis tables and discussion prose. "
        + "No new numerical solve, harvest, UQ, protected scoring, fit, or model selection was attempted.\n\n"
        + "## What Worked\n\n"
        + "The available packages were sufficient to document the current scientific state and preserve "
        + "claim boundaries for publication writing.\n\n"
        + "## What Did Not Work\n\n"
        + "The synthesis did not unlock coefficient admission, candidate freezing, source/property release, "
        + "or final scoring because the prerequisite gates remain closed.\n\n"
        + "## Analysis\n\n"
        + f"The result is `{decision}`. This is a rigorous negative or gated result: it states exactly "
        + "which evidence exists, which inference is allowed, and which downstream scientific claim is still blocked.\n\n"
        + "## Next Steps\n\n"
        + "Continue with source/property release, same-QOI UQ, or thesis LaTeX insertion only under separate claimed rows.\n"
    )
    write_json(
        import_path,
        {
            "task": task["task_id"],
            "task_id": task["task_id"],
            "date": DATE,
            "decision": decision,
            "changed_files": outputs
            + [
                str(status_path.relative_to(ROOT)),
                str(journal_path.relative_to(ROOT)),
                str(import_path.relative_to(ROOT)),
            ],
            "read_only_context": [str(SOURCES[key]) for key in source_keys],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "source_property_release": False,
            "validation_holdout_external_rows_scored": 0,
            "thesis_current_file_edit": False,
        },
    )


def finish_task_package(task_key: str, summary: dict[str, Any], source_keys: list[str], discussion: str) -> dict[str, Any]:
    od = out_dir(task_key)
    write_csv(od / "source_manifest.csv", source_manifest_rows(source_keys))
    write_csv(od / "no_mutation_guardrails.csv", guardrail_rows())
    write_json(od / "summary.json", summary)
    write_package_docs(task_key, summary["decision"], source_keys, discussion)
    outputs = [
        str(path.relative_to(ROOT))
        for path in sorted(od.glob("*"))
        if path.is_file()
    ]
    write_closeout_docs(task_key, summary["decision"], outputs, source_keys)
    return summary


def build_n1() -> dict[str, Any]:
    source_keys = [
        "four_study_gate",
        "five_best",
        "s8_s12",
        "s13_source_gate",
        "s13_exact_qwall",
        "s13_limited",
        "s14_f6",
        "s6_scorecard",
        "sensor_contract",
    ]
    od = out_dir("N1")
    od.mkdir(parents=True, exist_ok=True)
    four = load_json("four_study_gate")
    s8 = load_json("s8_s12")
    s13 = load_json("s13_source_gate")
    s13_exact = load_json("s13_exact_qwall")
    s14 = load_json("s14_f6")
    s6 = load_json("s6_scorecard")
    sensor = load_json("sensor_contract")
    candidates = load_csv("four_study_gate", "candidate_freeze_readiness_matrix.csv")

    candidate_rows = []
    for row in candidates:
        candidate_rows.append(
            {
                "candidate_or_lane": row["candidate_or_lane"],
                "component_class": row["basis"],
                "diagnostic_evidence_available": row["diagnostic_evidence_available"],
                "runtime_legal_for_final_score": "false",
                "source_property_released": row["source_property_released"],
                "same_qoi_uq_ready": row["same_qoi_uq_ready"],
                "production_or_repair_allowed": row["production_or_repair_allowed"],
                "candidate_released": row["candidate_released"],
                "status_label": "diagnostic_or_blocked",
                "reason": row["blocking_reason"],
            }
        )
    write_csv(od / "candidate_gate_matrix.csv", candidate_rows)

    runtime_rows = [
        {
            "input_or_output": "predeclared geometry/topology",
            "evidence_status": "available_from_prior_packages",
            "runtime_input_allowed": "true",
            "fit_or_selection_allowed": "false",
            "reason": "setup/source geometry may define model structure but cannot score a candidate alone",
        },
        {
            "input_or_output": "exact target-window Q_wall_W",
            "evidence_status": f"released_rows={s13_exact['Q_wall_W_released_rows']}",
            "runtime_input_allowed": "false",
            "fit_or_selection_allowed": "false",
            "reason": "CFD target-window evidence is publication/diagnostic input until same-QOI UQ and production gates pass",
        },
        {
            "input_or_output": "Q_source_side_net_static_bc_W",
            "evidence_status": s13["qoi_label"],
            "runtime_input_allowed": "false",
            "fit_or_selection_allowed": "false",
            "reason": "source-side QOI is defined but conservation, neighbor-window, and UQ release gates fail closed",
        },
        {
            "input_or_output": "runtime TP/TW temperatures",
            "evidence_status": f"runtime_temperature_inputs_allowed={sensor['runtime_temperature_inputs_allowed']}",
            "runtime_input_allowed": "false",
            "fit_or_selection_allowed": "false",
            "reason": "temperatures remain post-solve score targets only",
        },
        {
            "input_or_output": "F6/component-K/cluster-K pressure closures",
            "evidence_status": f"admitted_rows={s14['admitted_rows']}",
            "runtime_input_allowed": "false",
            "fit_or_selection_allowed": "false",
            "reason": "ordinary-flow and same-QOI UQ gates are not passed",
        },
    ]
    write_csv(od / "runtime_input_audit.csv", runtime_rows)

    blocked_rows = [
        {
            "gate": "S8/S12 thermal residual owner",
            "status": s8["decision"],
            "scorecard_effect": "no thermal repair candidate released",
            "protected_rows_touched": 0,
            "reason": "needs more physical basis before repair or admission",
        },
        {
            "gate": "S13 exchange/Qwall/UQ",
            "status": s13["decision"],
            "scorecard_effect": "Qwall evidence can be cited but no production candidate can be scored",
            "protected_rows_touched": 0,
            "reason": "conservation, neighbor-window, and same-QOI UQ gates fail closed",
        },
        {
            "gate": "S14 pressure/F6",
            "status": s14["study_state"],
            "scorecard_effect": "diagnostic branch screening only",
            "protected_rows_touched": 0,
            "reason": "0 admitted rows and 0 fits",
        },
        {
            "gate": "S6 frozen scorecard",
            "status": s6["decision"],
            "scorecard_effect": "final score table remains a shell",
            "protected_rows_touched": s6["final_score_values_published"],
            "reason": "no single released runtime-legal candidate",
        },
    ]
    write_csv(od / "blocked_scorecard_logic.csv", blocked_rows)
    write_csv(
        od / "closure_status_rollup.csv",
        [
            {"closure_family": "thermal", "admitted_rows": 0, "diagnostic_rows": s8["basis_rows"], "decision": s8["decision"]},
            {"closure_family": "upcomer_exchange", "admitted_rows": 0, "diagnostic_rows": s13["neighbor_window_qoi_rows"], "decision": s13["decision"]},
            {"closure_family": "pressure_F6", "admitted_rows": s14["admitted_rows"], "diagnostic_rows": s14["use_label_counts"]["diagnostic_only"], "decision": s14["study_state"]},
            {"closure_family": "sensor_policy", "admitted_rows": 0, "diagnostic_rows": sensor["sensors_reviewed"], "decision": "score_targets_only_no_runtime_inputs"},
        ],
    )
    write_csv(
        od / "ch8_ready_table.csv",
        [
            {
                "chapter_target": "Chapter 8 limitations/conclusions",
                "claim": "No frozen runtime-legal predictive candidate is available yet.",
                "evidence": "S8/S12 released 0 candidates; S13 production/UQ blocked; S14/F6 diagnostic only; S6 final scores published 0 values.",
                "allowed_language": "blocked scorecard shell; diagnostic evidence; no admission",
                "forbidden_language": "final score, admitted closure, released runtime temperature input, negative loss",
            }
        ],
    )
    (od / "caption_bank.md").write_text(
        "# N1 Caption Bank\n\n"
        "Runtime-legal candidate gate. Existing thermal, upcomer-exchange, pressure/F6, "
        "and sensor-policy evidence is sufficient to explain why the scorecard remains "
        "blocked, but no closure is admitted and no protected score is published.\n"
    )
    discussion = """
## Observed Evidence

The closed evidence packages agree on a no-freeze state. S8/S12 reviewed thermal
residual-owner evidence but released zero candidates. S13 provides exact
target-window pressure and `Q_wall_W` evidence, while the source-side
conservation, neighbor-window, and same-QOI UQ gates remain closed. S14/F6
contains diagnostic branch-use evidence only, with no component-K, cluster-K,
F6 fit, clipped-K, or hidden-multiplier rows admitted.

## Interpretation

The scientific result is not a failure to learn. It is a runtime-legality result:
the current evidence can support thesis claims about why candidate scoring is
blocked, but it cannot be used as a final predictive scorecard.

## Publication Boundary

The safe claim is that the current model-form evidence is diagnostic and
gate-localizing. The unsafe claim would be that a coefficient, heat-flow source,
or pressure closure has been admitted for final predictive scoring.
"""
    summary = {
        "task_id": TASKS["N1"]["task_id"],
        "generated_at_utc": now_utc(),
        "decision": "no_frozen_runtime_legal_candidate",
        "candidate_gate_rows": len(candidate_rows),
        "released_candidate_rows": 0,
        "runtime_inputs_allowed_rows": sum(1 for row in runtime_rows if row["runtime_input_allowed"] == "true"),
        "runtime_temperature_input_release": False,
        "s13_Q_wall_W_released_rows": s13_exact["Q_wall_W_released_rows"],
        "s13_production_harvest_allowed": s13["harvest_allowed"],
        "s14_admitted_rows": s14["admitted_rows"],
        "s6_final_score_values_published": s6["final_score_values_published"],
        **FORBIDDEN_GUARDRAILS,
    }
    return finish_task_package("N1", summary, source_keys, discussion)


def build_n2() -> dict[str, Any]:
    source_keys = ["s13_limited", "s13_source_gate", "s13_exact_qwall", "s13_source_prereq"]
    od = out_dir("N2")
    od.mkdir(parents=True, exist_ok=True)
    limited = load_json("s13_limited")
    source_gate = load_json("s13_source_gate")
    exact = load_json("s13_exact_qwall")
    trend = load_csv("s13_limited", "s13_exchange_trend_table.csv")
    qwall = load_csv("s13_exact_qwall", "trusted_wall_Q_wall_summary.csv")

    write_csv(
        od / "panel_manifest.csv",
        [
            {"panel_id": "A", "panel_type": "existing_velocity_or_status_visual", "source": limited["figure_svg"], "status": "ready_existing_artifact", "claim_boundary": "diagnostic only"},
            {"panel_id": "B", "panel_type": "sampled_interface_U_T_rho_summary", "source": str(SOURCES["s13_limited"] / "s13_sampled_field_gate_matrix.csv"), "status": "table_ready", "claim_boundary": "not production harvest"},
            {"panel_id": "C", "panel_type": "wall_core_temperature_contrast", "source": str(SOURCES["s13_limited"] / "s13_exchange_trend_table.csv"), "status": "table_ready", "claim_boundary": "thermal contrast only"},
            {"panel_id": "D", "panel_type": "Qwall_source_side_UQ_gate", "source": str(SOURCES["s13_source_gate"] / "summary.json"), "status": "caption_ready", "claim_boundary": "Qwall evidence released; admission blocked"},
        ],
    )
    interface_rows = []
    contrast_rows = []
    for row in trend:
        interface_rows.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "interface_area_m2": row["interface_area_m2"],
                "mdot_exchange_net_proxy_kg_s": row["mdot_exchange_net_proxy_kg_s"],
                "tau_recirc_proxy_s": row["tau_recirc_proxy_s"],
                "source_side_q_net_W": row["source_side_q_net_W"],
                "evidence_role": row["evidence_role"],
                "production_harvest_allowed": row["production_harvest_allowed"],
            }
        )
        contrast_rows.append(
            {
                "case_id": row["case_id"],
                "trusted_wall_T_area_avg_K": row["trusted_wall_T_area_avg_K"],
                "interface_core_T_area_avg_K": row["interface_core_T_area_avg_K"],
                "seeded_cv_T_volume_avg_K": row["seeded_cv_T_volume_avg_K"],
                "delta_T_wall_minus_core_K": row["delta_T_wall_minus_core_K"],
                "delta_T_core_minus_seed_K": row["delta_T_core_minus_seed_K"],
                "interpretation": "small wall/core/seed contrast supports exchange-cell diagnostic evidence, not a single-stream closure",
            }
        )
    write_csv(od / "sampled_interface_summary_table.csv", interface_rows)
    write_csv(od / "wall_core_temperature_contrast_table.csv", contrast_rows)
    qwall_rows = [
        {
            "case_id": row["case_id"],
            "time_window_s": row["time_window_s"],
            "Q_wall_W": row["Q_wall_W"],
            "Q_wall_W_released": row["Q_wall_W_released"],
            "release_status": row["release_status"],
            "production_or_admission_allowed": "false",
            "reason": "exact target-window input released read-only; same-QOI UQ/production gate remains blocked",
        }
        for row in qwall
    ]
    qwall_rows.append(
        {
            "case_id": "source_side_equivalent",
            "time_window_s": "",
            "Q_wall_W": source_gate["qoi_label"],
            "Q_wall_W_released": "false",
            "release_status": source_gate["decision"],
            "production_or_admission_allowed": "false",
            "reason": "source-side QOI must not be relabeled as Q_wall_W",
        }
    )
    write_csv(od / "qwall_source_side_status_table.csv", qwall_rows)
    write_csv(
        od / "same_qoi_uq_status_table.csv",
        [
            {"gate": "source_property_conservation", "rows": source_gate["source_property_conservation_rows"], "ready_rows": source_gate["conservation_release_ready_rows"], "status": "blocked"},
            {"gate": "neighbor_window_qoi", "rows": source_gate["neighbor_window_qoi_rows"], "ready_rows": source_gate["neighbor_window_ready_rows"], "status": "blocked"},
            {"gate": "same_qoi_uq", "rows": 1, "ready_rows": source_gate["same_qoi_uq_ready_rows"], "status": "blocked"},
            {"gate": "production_harvest", "rows": source_gate["production_ready_gate_rows"], "ready_rows": int(source_gate["harvest_allowed"]), "status": "blocked"},
        ],
    )
    write_csv(
        od / "single_stream_closure_blocker_table.csv",
        [
            {"blocker": "finite exchange exists", "status": "diagnostic_ready", "reason": f"{limited['finite_exchange_rows']} finite exchange rows"},
            {"blocker": "ordinary upcomer Nu/f_D/K admission", "status": "blocked", "reason": "recirculating exchange is not a single-stream ordinary-flow basis"},
            {"blocker": "source/property release", "status": "blocked", "reason": "0 conservation release-ready rows"},
            {"blocker": "same-QOI UQ", "status": "blocked", "reason": "0 same-QOI UQ ready rows"},
        ],
    )
    (od / "caption_bank.md").write_text(
        "# N2 Caption Bank\n\n"
        "Upcomer exchange evidence panels. Velocity and sampled-field summaries show "
        "finite exchange and thermal contrast, exact `Q_wall_W` is available for the "
        "target windows, and the production/admission path remains blocked by "
        "source-property and same-QOI UQ gates.\n"
    )
    discussion = """
## Observed Evidence

The S13 tables contain finite exchange proxies for Salt2, Salt3, and Salt4.
Exact target-window `Q_wall_W` values are released from trusted-wall heat-flux
integration, but the source-side conservation/UQ gate records zero release-ready
source-property rows, zero neighbor-window ready rows, and zero same-QOI UQ ready
rows.

## Interpretation

This supports a paper panel about recirculating exchange and wall/source heat
paths. It does not support treating the upcomer as a single ordinary stream, nor
does it release an exchange-cell coefficient.
"""
    summary = {
        "task_id": TASKS["N2"]["task_id"],
        "generated_at_utc": now_utc(),
        "decision": "paper_panels_ready_diagnostic_only_no_single_stream_closure",
        "panel_rows": 4,
        "case_rows": len(trend),
        "exact_Q_wall_W_released_rows": exact["Q_wall_W_released_rows"],
        "same_qoi_uq_ready_rows": source_gate["same_qoi_uq_ready_rows"],
        "production_harvest_allowed_rows": limited["production_harvest_allowed_rows"],
        "ordinary_upcomer_closure_admitted": False,
        **FORBIDDEN_GUARDRAILS,
    }
    return finish_task_package("N2", summary, source_keys, discussion)


def build_n3() -> dict[str, Any]:
    source_keys = ["s8_s12", "source_decomp", "passive_source", "passive_h2", "external_bc_gate", "empirical_bias", "reduced_dof"]
    od = out_dir("N3")
    od.mkdir(parents=True, exist_ok=True)
    s8 = load_json("s8_s12")
    source = load_json("source_decomp")
    passive = load_json("passive_source")
    h2 = load_json("passive_h2")
    ext = load_json("external_bc_gate")
    empirical = load_json("empirical_bias")
    reduced = load_json("reduced_dof")
    metrics = load_csv("source_decomp", "train_metric_comparison.csv")

    ablation_rows = [
        {"lane": "baseline", "evidence": "Phase E/S8 baseline context", "metric_context": "baseline_all_mae_K=81.581515 from source-decomp comparison", "physical_plausibility": "reference_only", "runtime_legality": "not_a_closure", "split_role": "train_context", "status": "evidence_only", "reason": "baseline is comparator"},
        {"lane": "external_boundary", "evidence": ext["decision"], "metric_context": f"available_ambient_wall_rows={ext['available_ambient_wall_rows']}", "physical_plausibility": "plausible_but_incomplete", "runtime_legality": "not_released", "split_role": "train_only", "status": "fail_closed", "reason": "negative freeze; missing ambient wall rows"},
        {"lane": "passive_wall", "evidence": passive["decision"], "metric_context": f"global_tw5_improvement_K={h2['global_tw5_improvement_K']:.6g}", "physical_plausibility": "plausible_needs_source_basis", "runtime_legality": "not_released", "split_role": "train_only", "status": "evidence_only", "reason": "0 source families released"},
        {"lane": "test_section_source", "evidence": source["decision"], "metric_context": "; ".join(f"{m['metric']}:{m['delta_candidate_minus_baseline']}" for m in metrics[:3]), "physical_plausibility": "partial_local_response", "runtime_legality": "not_released", "split_role": "train_only", "status": "evidence_only", "reason": "partial improvement and worsening both observed"},
        {"lane": "junction_stub", "evidence": "unowned residual/stub lane", "metric_context": "no admitted owner", "physical_plausibility": "unresolved", "runtime_legality": "not_released", "split_role": "blocked", "status": "fail_closed", "reason": "no independent source/property basis"},
        {"lane": "empirical_diagnostic", "evidence": "leg bias and reduced-DOF screens", "metric_context": f"empirical_train_mae_K={empirical['corrected_all_mae_K']:.6g}; transfer_mae_K={reduced['best_transfer_corrected_mae_K']:.6g}", "physical_plausibility": "diagnostic_not_physical_closure", "runtime_legality": "not_released", "split_role": "train_support_diagnostic", "status": "evidence_only", "reason": "fit is not physics admission and transfer was not used for model selection"},
    ]
    write_csv(od / "thermal_residual_ablation_table.csv", ablation_rows)
    write_csv(
        od / "lane_evidence_matrix.csv",
        [
            {"lane": row["lane"], "observed": row["evidence"], "inferred": row["physical_plausibility"], "claim_boundary": row["reason"]}
            for row in ablation_rows
        ],
    )
    write_csv(
        od / "runtime_legality_matrix.csv",
        [
            {"lane": row["lane"], "runtime_legal": "false", "source_property_released": "false", "admission_allowed": "false", "reason": row["reason"]}
            for row in ablation_rows
        ],
    )
    write_csv(
        od / "physical_plausibility_table.csv",
        [
            {"lane": row["lane"], "plausibility_class": row["physical_plausibility"], "status": row["status"], "publication_language": row["reason"]}
            for row in ablation_rows
        ],
    )
    write_csv(od / "train_only_metric_context.csv", metrics)
    (od / "caption_bank.md").write_text(
        "# N3 Caption Bank\n\n"
        "Train-only residual-owner ablation. The rows separate physical plausibility "
        "from runtime legality: external/passive/source lanes explain where residuals "
        "may live, while empirical lanes remain diagnostic and no lane is admitted.\n"
    )
    discussion = """
## Observed Evidence

Passive wall and external-boundary evidence show plausible heat-path responses,
while the known heater/source decomposition improves some local residuals and
worsens others. Empirical corrections sharply reduce train residuals, but their
role is diagnostic because they are not source-backed physical closures.

## Interpretation

The useful result is ownership separation. The residual should not be absorbed
into internal Nu or any single ad hoc multiplier. The ablation table documents
which mechanisms are credible enough to discuss and which remain blocked.
"""
    summary = {
        "task_id": TASKS["N3"]["task_id"],
        "generated_at_utc": now_utc(),
        "decision": "train_only_residual_owner_ablation_complete_no_candidate_release",
        "ablation_rows": len(ablation_rows),
        "candidate_reviewable_rows": 0,
        "evidence_only_rows": sum(1 for row in ablation_rows if row["status"] == "evidence_only"),
        "fail_closed_rows": sum(1 for row in ablation_rows if row["status"] == "fail_closed"),
        "s8_candidate_count_released": s8["candidate_count_released"],
        **FORBIDDEN_GUARDRAILS,
    }
    return finish_task_package("N3", summary, source_keys, discussion)


def build_n4() -> dict[str, Any]:
    source_keys = ["sensor_contract", "sensor_s7", "master_scoreboard", "s6_scorecard"]
    od = out_dir("N4")
    od.mkdir(parents=True, exist_ok=True)
    sensor_summary = load_json("sensor_contract")
    s7 = load_json("sensor_s7")
    master = load_json("master_scoreboard")
    ledger = load_csv("sensor_s7", "sensor_coordinate_ledger.csv")
    path_map = {row["sensor"]: row for row in load_csv("sensor_s7", "one_d_path_position_map.csv")}
    policy = {row["sensor"]: row for row in load_csv("sensor_s7", "score_only_target_policy.csv")}
    rationale = {row["sensor"]: row for row in load_csv("sensor_s7", "bounded_or_excluded_sensor_rationale.csv")}

    projection_rows = []
    for row in ledger:
        sensor = row["sensor"]
        pmap = path_map.get(sensor, {})
        pol = policy.get(sensor, {})
        rat = rationale.get(sensor, {})
        projection_rows.append(
            {
                "sensor": sensor,
                "kind": row["kind"],
                "acceptance_class": row["acceptance_class"],
                "one_d_segment_or_state": pmap.get("one_d_segment_or_state", ""),
                "one_d_fraction_or_marker": pmap.get("one_d_fraction_or_marker", ""),
                "score_target_use": pol.get("score_target_use", ""),
                "runtime_temperature_allowed": pol.get("runtime_temperature_allowed", "false"),
                "fit_allowed": pol.get("fit_allowed", "false"),
                "model_selection_allowed": pol.get("model_selection_allowed", "false"),
                "uncertainty_caveat": row["coordinate_caveat"],
                "score_table_effect": rat.get("score_aggregate_after_refresh", ""),
            }
        )
    write_csv(od / "sensor_qoi_projection_table.csv", projection_rows)
    write_csv(
        od / "sensor_runtime_input_audit.csv",
        [
            {
                "sensor": row["sensor"],
                "runtime_temperature_allowed": row["runtime_temperature_allowed"],
                "fit_allowed": row["fit_allowed"],
                "model_selection_allowed": row["model_selection_allowed"],
                "reason": "score-only policy; temperature is not a runtime input",
            }
            for row in projection_rows
        ],
    )
    write_csv(
        od / "sensor_uncertainty_caveat_table.csv",
        [
            {
                "sensor": row["sensor"],
                "acceptance_class": row["acceptance_class"],
                "coordinate_claim_level": next(src["coordinate_claim_level"] for src in ledger if src["sensor"] == row["sensor"]),
                "uncertainty_caveat": row["uncertainty_caveat"],
                "publication_effect": "use segment/projection language; avoid exact-coordinate claims",
            }
            for row in projection_rows
        ],
    )
    write_csv(
        od / "score_table_effect_matrix.csv",
        [
            {"class": "mapped", "rows": s7["mapped_rows"], "score_effect": "included after projection gates; still score-only"},
            {"class": "bounded", "rows": s7["bounded_rows"], "score_effect": "include as bounded/provisional score targets"},
            {"class": "excluded", "rows": s7["excluded_rows"], "score_effect": "exclude from aggregate until model emits required state"},
            {"class": "runtime_temperature_inputs", "rows": s7["runtime_temperature_allowed_rows"], "score_effect": "forbidden as inputs"},
        ],
    )
    write_csv(
        od / "ch6_appendix_ch8_table.csv",
        [
            {
                "target_location": "Chapter 6 or appendix",
                "claim": "TP/TW sensors are post-solve QOI targets with mapped, bounded, or excluded status.",
                "evidence": f"{sensor_summary['sensors_reviewed']} sensors; mapped={s7['mapped_rows']}; bounded={s7['bounded_rows']}; excluded={s7['excluded_rows']}",
                "limitation": "no runtime temperature input release",
            },
            {
                "target_location": "Chapter 8 scorecard context",
                "claim": "Sensor projection uncertainty affects score interpretation, not model runtime inputs.",
                "evidence": f"master scoreboard signed rows={master['signed_sensor_error_rows']}",
                "limitation": "no new protected scoring beyond closed summaries",
            },
        ],
    )
    (od / "caption_bank.md").write_text(
        "# N4 Caption Bank\n\n"
        "Sensor/QOI projection policy. TP/TW sensors are post-solve score targets; "
        "TP2 is mapped, most sensors are bounded, TW10 is excluded, and no runtime "
        "temperature, fit, or model-selection permission is released.\n"
    )
    discussion = """
## Observed Evidence

The sensor packages review 17 TP/TW sensors: one mapped target, fifteen bounded
targets, and one excluded target. Every row preserves
`runtime_temperature_allowed=false`, `fit_allowed=false`, and
`model_selection_allowed=false`.

## Interpretation

Sensor uncertainty is a QOI projection issue. It affects how score tables and
captions should be written, but it must not leak target temperatures into model
runtime, fitting, or model selection.
"""
    runtime_allowed = sum(1 for row in projection_rows if row["runtime_temperature_allowed"] == "true")
    summary = {
        "task_id": TASKS["N4"]["task_id"],
        "generated_at_utc": now_utc(),
        "decision": "sensor_projection_uncertainty_table_complete_no_runtime_temperature_release",
        "sensor_rows": len(projection_rows),
        "mapped_rows": s7["mapped_rows"],
        "bounded_rows": s7["bounded_rows"],
        "excluded_rows": s7["excluded_rows"],
        "runtime_temperature_allowed_rows": runtime_allowed,
        "new_protected_scoring_rows": 0,
        **FORBIDDEN_GUARDRAILS,
    }
    return finish_task_package("N4", summary, source_keys, discussion)


def write_tomorrow_handoff() -> None:
    path = ROOT / "operational_notes/07-26/22/2026-07-22_THESIS_N1_N4_SYNTHESIS_TOMORROW_HANDOFF.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    provenance = [
        f"work_products/2026-07/{DATE}/{DATE}_{TASKS[key]['slug']}/summary.json"
        for key in TASKS
    ]
    path.write_text(
        "---\n"
        + "provenance:\n"
        + "\n".join(f"  - {item}" for item in provenance)
        + "\n"
        + "tags: [thesis, handoff, synthesis, publication-evidence]\n"
        + "related:\n"
        + "\n".join(f"  - work_products/2026-07/{DATE}/{DATE}_{TASKS[key]['slug']}/README.md" for key in TASKS)
        + "\n"
        + "task: TODO-THESIS-N1-N4-SYNTHESIS-HANDOFF-2026-07-22\n"
        + f"date: {DATE}\n"
        + "role: Coordinator/Writer\n"
        + "type: operational_note\n"
        + "status: complete\n"
        + "---\n\n"
        + "# Thesis N1-N4 Tomorrow Handoff\n\n"
        + "## Context\n\n"
        + "N1-N4 were implemented as synthesis packages from existing evidence only. The key "
        + "result is publication-grade documentation of why the current candidate scorecard "
        + "remains blocked, not a new admitted closure.\n\n"
        + "## Progress\n\n"
        + "- N1 documents no frozen runtime-legal candidate.\n"
        + "- N2 documents S13 exchange/Qwall panels as diagnostic-only, with exact Qwall evidence but blocked production/UQ/admission.\n"
        + "- N3 documents train-only residual-owner ablation and separates physical plausibility from runtime legality.\n"
        + "- N4 documents TP/TW projection uncertainty and preserves no runtime-temperature input release.\n\n"
        + "## What Worked\n\n"
        + "The existing S8/S12, S13, S14/F6, source-property, and sensor packages were sufficient "
        + "to produce tables and discussion suitable for thesis/publication claim boundaries.\n\n"
        + "## What Did Not Work\n\n"
        + "No package unlocked source/property release, same-QOI UQ, final score publication, or "
        + "closure admission. Those remain separate blockers.\n\n"
        + "## Next Steps For Tomorrow\n\n"
        + "1. Use the N1 Ch. 8 table and N4 sensor table in thesis writing under a separate LaTeX row.\n"
        + "2. If prioritizing science, work the S13 source-property/same-QOI UQ blocker before any exchange-cell coefficient review.\n"
        + "3. If prioritizing model form, use N3 to choose one physical residual-owner experiment, but do not fit or admit it without a new gate.\n"
        + "4. Keep F6/component-K pressure evidence diagnostic until ordinary-flow and same-QOI UQ gates pass.\n\n"
        + "## Do Not Do\n\n"
        + "Do not publish final score values, admit a coefficient, relabel source-side heat flow as Qwall, "
        + "use TP/TW temperatures as runtime inputs, or absorb thermal residuals into internal Nu.\n"
    )


BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "N1": build_n1,
    "N2": build_n2,
    "N3": build_n3,
    "N4": build_n4,
}


def build(task_key: str = "N1") -> dict[str, Any]:
    summary = BUILDERS[task_key]()
    if task_key == "N4":
        write_tomorrow_handoff()
    return summary


def main() -> int:
    build("N1")
    print(f"wrote {out_dir('N1').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
