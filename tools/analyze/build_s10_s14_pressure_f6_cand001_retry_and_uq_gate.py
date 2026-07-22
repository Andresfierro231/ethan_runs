#!/usr/bin/env python3
"""Build the S10/S14 CAND-001 pressure/F6 retry and UQ gate.

This is a read-only synthesis gate. It decides whether the current CAND-001
state justifies a future scheduler-safe retry row, and it records why the
current lower-right pressure result remains a negative/section-effective result
rather than component-K or F6 evidence.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-22"
TASK_ID = "TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21"
SLUG = "s10_s14_pressure_f6_cand001_retry_and_uq_gate"
OUT_DIR = ROOT / "work_products/2026-07" / DATE / f"{DATE}_{SLUG}"

SOURCES = {
    "cand001_timeout": Path("work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition"),
    "low_recirc_readiness": Path("work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness"),
    "same_qoi_gate": Path("work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate"),
    "s14_anchor": Path("work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence"),
    "section_effective": Path("work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard"),
    "pressure_corner_freeze": Path("work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze"),
    "negative_insert": Path("work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert"),
    "stage_b_qa": Path("work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh"),
    "static_basis": Path("work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit"),
    "s5_source_split": Path("work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release"),
}

GUARDRAILS = {
    "native_output_mutation": False,
    "registry_or_admission_mutation": False,
    "scheduler_action": False,
    "solver_or_postprocessing_or_sampler_launched": False,
    "validation_holdout_external_rows_scored": 0,
    "fitting_or_model_selection": False,
    "f6_fit_performed": False,
    "component_k_admitted": False,
    "cluster_k_admitted": False,
    "clipped_k": False,
    "hidden_global_multiplier": False,
    "s11_s15_s6_trigger": False,
    "fluid_or_external_repo_edited": False,
    "thesis_current_file_edit": False,
    "blocker_register_change": False,
    "mixed_basis_promotion": False,
}


def load_json(key: str) -> dict[str, Any]:
    with (ROOT / SOURCES[key] / "summary.json").open() as f:
        return json.load(f)


def load_csv(key: str, name: str) -> list[dict[str, str]]:
    with (ROOT / SOURCES[key] / name).open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: value(row.get(field, "")) for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def value(item: Any) -> str:
    if item is True:
        return "true"
    if item is False:
        return "false"
    if item is None:
        return ""
    return str(item)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_key": key,
            "path": str(path),
            "summary_path": str(path / "summary.json"),
            "exists": (ROOT / path).exists(),
            "mutation_status": "read_only",
        }
        for key, path in SOURCES.items()
    ]


def frontmatter(doc_type: str, status: str, provenance: list[str]) -> str:
    prov = "\n".join(f"  - {item}" for item in provenance)
    return (
        "---\n"
        f"provenance:\n{prov}\n"
        "tags: [pressure, f6, cand001, same-qoi-uq, thesis, publication-evidence]\n"
        "related:\n"
        f"  - work_products/2026-07/{DATE}/{DATE}_{SLUG}/README.md\n"
        f"  - work_products/2026-07/{DATE}/{DATE}_{SLUG}/scheduler_safe_retry_runbook.md\n"
        f"task: {TASK_ID}\n"
        f"date: {DATE}\n"
        "role: Hydraulics / cfd-pp / Scheduler / Tester / Writer / Reviewer\n"
        f"type: {doc_type}\n"
        f"status: {status}\n"
        "---\n\n"
    )


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timeout = load_json("cand001_timeout")
    readiness = load_json("low_recirc_readiness")
    same_qoi = load_json("same_qoi_gate")
    s14 = load_json("s14_anchor")
    section = load_json("section_effective")
    source_split = load_json("s5_source_split")

    timeout_gate = load_csv("cand001_timeout", "endpoint_gate_after_timeout.csv")
    low_go = load_csv("low_recirc_readiness", "sampler_go_no_go.csv")
    s14_gate = load_csv("s14_anchor", "f6_gate_scoring_matrix.csv")
    f3 = load_csv("s14_anchor", "f3_vs_f6_comparison_readiness.csv")
    lower_right = load_csv("pressure_corner_freeze", "canonical_pressure_corner_result.csv")
    negative_claims = load_csv("negative_insert", "pressure_claim_boundary_table.csv")

    gate_rows = [
        {
            "gate": "CAND001_terminal_success",
            "status": "fail",
            "observed": f"terminal_success_cases={timeout['terminal_success_cases']}; timeout_jobs={timeout['timeout_jobs']}",
            "blocks": "raw endpoint evidence and sampler release",
            "next_action": "future scheduler-safe retry row may recover terminal source cases",
            "source": str(SOURCES["cand001_timeout"] / "summary.json"),
        },
        {
            "gate": "endpoint_fields",
            "status": "fail",
            "observed": f"endpoint_fields_ready={timeout['endpoint_fields_ready']}; required_rows={len(timeout_gate)}",
            "blocks": "F6/component-K/cluster-K evidence",
            "next_action": "after terminal success, sample finite p, p_rgh, U, rho, T, face area, normals, and derived RAF/RMF/SVF",
            "source": str(SOURCES["cand001_timeout"] / "endpoint_gate_after_timeout.csv"),
        },
        {
            "gate": "ordinary_flow",
            "status": "fail",
            "observed": f"ordinary_candidate_pairs={readiness['ordinary_candidate_pairs']}; S14 admitted_rows={s14['admitted_rows']}",
            "blocks": "ordinary F6 and component-K labels",
            "next_action": "require RAF < 0.01 and RMF < 0.01 for any ordinary F6 row",
            "source": str(SOURCES["low_recirc_readiness"] / "summary.json"),
        },
        {
            "gate": "same_qoi_mesh_time_uq",
            "status": "fail",
            "observed": f"same_qoi_mesh_uq_admissible_rows={same_qoi['same_qoi_mesh_uq_admissible_rows']}",
            "blocks": "F6 review release and F3-vs-F6 comparison",
            "next_action": "same-label, same-formula, same-sign mesh/time UQ after endpoint rows exist",
            "source": str(SOURCES["same_qoi_gate"] / "summary.json"),
        },
        {
            "gate": "lower_right_component_interpretation",
            "status": "negative_result",
            "observed": f"section_effective_rows={section['row_count']}; component_k_admitted_rows={section['component_k_admitted_rows']}",
            "blocks": "using lower-right result as component-K/F6 evidence",
            "next_action": "cite lower-right only as section-effective residual / recovery diagnostic",
            "source": str(SOURCES["pressure_corner_freeze"] / "canonical_pressure_corner_result.csv"),
        },
        {
            "gate": "source_property_split_refresh",
            "status": "blocked",
            "observed": f"fit_allowed_rows={source_split.get('fit_allowed_rows', 0)}",
            "blocks": "S11/S15/S6 trigger",
            "next_action": "only after exactly one pressure candidate is admission-worthy",
            "source": str(SOURCES["s5_source_split"] / "summary.json"),
        },
    ]
    write_csv(OUT_DIR / "timeout_source_ordinary_uq_gate_matrix.csv", gate_rows)

    retry_decision = [
        {
            "candidate_id": "CAND-001",
            "decision": "write_scheduler_safe_retry_runbook_no_launch",
            "retry_row_recommended": True,
            "launch_allowed_in_this_task": False,
            "sampler_allowed_now": False,
            "f6_scoring_allowed_now": False,
            "reason": "prior high-heat/no-recirculation attempts timed out before terminal source evidence; current endpoint/source/UQ gates remain closed",
            "alternative": "CAND-002 corrected +/-10Q fallback terminal-readiness audit if CAND-001 compute is deferred",
        }
    ]
    write_csv(OUT_DIR / "retry_decision.csv", retry_decision)

    endpoint_rows = []
    for row in timeout_gate:
        endpoint_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "field_name": row["field_name"],
                "field_class": row["field_class"],
                "current_status": row["current_status_after_timeout"],
                "required_before_use": row["required_before_use"],
                "admission_effect_now": row["admission_effect"],
            }
        )
    write_csv(OUT_DIR / "endpoint_field_requirement_table.csv", endpoint_rows)

    comparison_rows = []
    for row in f3:
        comparison_rows.append(
            {
                "comparison_id": row["comparison_id"],
                "baseline": row["baseline"],
                "candidate": row["candidate"],
                "status_now": row["comparison_status"],
                "admitted_f6_rows": row["admitted_f6_rows"],
                "required_before_comparison": "ordinary-flow pass; finite endpoint fields; same-QOI UQ; source/property labels; frozen split-safe candidate",
                "fit_performed": row["fit_performed"],
                "reason": row["reason"],
            }
        )
    write_csv(OUT_DIR / "f3_vs_f6_comparison_prerequisites.csv", comparison_rows)

    s11_rows = [
        {
            "decision_id": "S10-S14-S11-001",
            "s11_unblocked": False,
            "s15_or_s6_trigger": False,
            "candidate_released": False,
            "reason": "CAND-001 has retryable terminal-source failure, but no ordinary-flow, same-QOI UQ, or source/property-admitted pressure candidate",
            "next_allowed_row": "separate CAND-001 scheduler retry row or CAND-002 terminal-readiness audit",
        }
    ]
    write_csv(OUT_DIR / "s11_decision.csv", s11_rows)

    lower_right_rows = [
        {
            "case_id": row["case_id"],
            "feature": row["feature"],
            "gross_static_pressure_rise_pa": row["gross_static_pressure_rise_pa"],
            "hydrostatic_term_pa": row["hydrostatic_term_pa"],
            "available_residual_pa": row["available_residual_pa"],
            "reverse_area_fraction": row["reverse_area_fraction"],
            "reverse_mass_fraction": row["reverse_mass_fraction"],
            "same_qoi_uncertainty_gate": row["same_qoi_uncertainty_gate"],
            "final_label": row["final_label"],
            "admission_status": row["admission_status"],
            "use_in_this_gate": "negative_section_effective_context_only",
            "not_component_k_or_f6_reason": "pressure rise is hydrostatic-dominated; ordinary-flow, component isolation, same-basis straight reference, and same-QOI UQ gates fail",
        }
        for row in lower_right
    ]
    write_csv(OUT_DIR / "lower_right_negative_result_classification.csv", lower_right_rows)

    write_csv(
        OUT_DIR / "scheduler_retry_preflight_checklist.csv",
        [
            {"order": 1, "check": "duplicate_job_guard", "required_state": "no active duplicate CAND-001 retry job", "how_to_verify": "squeue/sacct in future scheduler row", "launch_block_if_missing": True},
            {"order": 2, "check": "source_case_selection", "required_state": "exact CAND-001 source cases and restart points named", "how_to_verify": "source readiness table and prior timeout logs", "launch_block_if_missing": True},
            {"order": 3, "check": "walltime_resource_plan", "required_state": "walltime exceeds prior 5-day timeouts or scope is reduced", "how_to_verify": "runbook records expected runtime and resources", "launch_block_if_missing": True},
            {"order": 4, "check": "terminal_success_definition", "required_state": "OpenFOAM terminal completion and readable retained time windows", "how_to_verify": "future row writes terminal/source-field readiness table", "launch_block_if_missing": True},
            {"order": 5, "check": "post_terminal_sampler_gate", "required_state": "finite endpoint fields plus RAF/RMF/SVF before sampler/admission", "how_to_verify": "endpoint field requirement table", "launch_block_if_missing": True},
        ],
    )

    no_mutation_rows = [
        {"guardrail": key, "value": val, "status": "pass", "reason": "gate/runbook only; no launch or admission"}
        for key, val in GUARDRAILS.items()
    ]
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", no_mutation_rows)
    write_csv(OUT_DIR / "source_manifest.csv", source_manifest_rows())

    runbook_text = frontmatter("work_product", "complete", [str(path / "summary.json") for path in SOURCES.values()])
    runbook_text += (
        "# Scheduler-Safe CAND-001 Retry Runbook\n\n"
        "## Decision\n\n"
        "Create a future, separately claimed scheduler retry row for CAND-001 only if the scientific owner still wants the high-heat/no-recirculation source family. Do not launch from this gate.\n\n"
        "## Why Retry Is Warranted\n\n"
        "The previous CAND-001 jobs ended in Slurm `TIMEOUT`, not a physics rejection. The timeout evidence means terminal source cases are missing; it does not prove the candidate cannot become a low-recirculation anchor.\n\n"
        "## Why Scoring Is Not Warranted\n\n"
        "Current CAND-001 endpoint fields are not terminal-ready, ordinary-flow candidate pairs are zero, same-QOI mesh/time UQ has zero admissible rows, and F3-vs-F6 comparison is not evaluated. Therefore there is no F6 fit, no component K, no cluster K, no clipped K, and no hidden multiplier.\n\n"
        "## Future Retry Row Must Do\n\n"
        "1. Verify no duplicate CAND-001 retry job is active.\n"
        "2. Name exact source cases, restart times, processor layout, walltime, allocation, logs, and expected terminal condition.\n"
        "3. Run only under scheduler control, not as a detached login-node process.\n"
        "4. After terminal success, emit endpoint field readiness for `p`, `p_rgh`, `U`, `rho`, `T`, face area, face normal, static and p_rgh deltas, hydrostatic and kinetic corrections, local dynamic pressure, RAF, RMF, and SVF.\n"
        "5. Stop before F6 scoring unless ordinary-flow and same-QOI UQ gates pass in a later row.\n\n"
        "## Fallback\n\n"
        "If CAND-001 compute is deferred, audit CAND-002 corrected +/-10Q terminal readiness before any new CAND-001 submission.\n"
    )
    (OUT_DIR / "scheduler_safe_retry_runbook.md").write_text(runbook_text)

    discussion = frontmatter("work_product", "complete", [str(path / "summary.json") for path in SOURCES.values()])
    discussion += (
        "# Scientific Discussion\n\n"
        "## Observed Result\n\n"
        "The lower-right pressure-corner result is a negative pressure-admission result. The gross static pressure rise is hydrostatic dominated, the available signed residual is small and negative, and the rows fail ordinary-flow, component-isolation, same-basis straight-reference, and same-QOI UQ gates.\n\n"
        "## Interpretation\n\n"
        "The lower-right rows may be cited as section-effective pressure residual and pressure-recovery diagnostic evidence. They must not be renamed as negative loss coefficients, component-K evidence, cluster-K evidence, or F6 evidence.\n\n"
        "## CAND-001 Decision\n\n"
        "CAND-001 deserves a future scheduler-safe retry row because its current failure is timeout/source-terminal failure rather than a completed no-go physics result. That retry is only source recovery. It does not authorize endpoint sampling, F6 scoring, F3-vs-F6 comparison, S11 release, or S15/S6 trigger.\n\n"
        "## Publication Boundary\n\n"
        "The pressure path remains scientifically useful as a rigorous blocked gate. A publication can state exactly why pressure rose around the corner and why that rise is not a negative loss. It cannot claim an admitted pressure closure.\n"
    )
    (OUT_DIR / "scientific_discussion.md").write_text(discussion)

    claim_boundary_rows = [
        {
            "claim_id": row["claim_id"],
            "status": row["status"],
            "allowed_wording": row["allowed_wording"],
            "forbidden_wording": row["forbidden_wording"],
            "use_in_this_package": "preserved",
        }
        for row in negative_claims
    ]
    write_csv(OUT_DIR / "pressure_claim_boundary_table.csv", claim_boundary_rows)

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": now(),
        "decision": "cand001_retry_runbook_recommended_no_launch_no_f6_scoring",
        "candidate_id": "CAND-001",
        "retry_row_recommended": True,
        "launch_allowed_in_this_task": False,
        "sampler_allowed_now": False,
        "f6_scoring_allowed_now": False,
        "terminal_success_cases": timeout["terminal_success_cases"],
        "timeout_jobs": timeout["timeout_jobs"],
        "endpoint_fields_ready": timeout["endpoint_fields_ready"],
        "ordinary_candidate_pairs": readiness["ordinary_candidate_pairs"],
        "same_qoi_mesh_uq_admissible_rows": same_qoi["same_qoi_mesh_uq_admissible_rows"],
        "s14_admitted_rows": s14["admitted_rows"],
        "lower_right_section_effective_rows": len(lower_right_rows),
        "lower_right_component_k_or_f6_rows": 0,
        "f3_comparison_status": f3[0]["comparison_status"],
        "s11_unblocked": False,
        **GUARDRAILS,
    }
    write_json(OUT_DIR / "summary.json", summary)

    readme = frontmatter("work_product", "complete", [str(path / "summary.json") for path in SOURCES.values()])
    readme += (
        "# S10/S14 Pressure F6 CAND-001 Retry And UQ Gate\n\n"
        f"Task: `{TASK_ID}`\n\n"
        f"Decision: `{summary['decision']}`\n\n"
        "This package decides retry/no-retry for CAND-001 and writes a scheduler-safe future runbook. It does not launch compute, harvest endpoints, fit F6, admit component K, or compare F3 against F6.\n\n"
        "## Outputs\n\n"
        "- `timeout_source_ordinary_uq_gate_matrix.csv`: terminal/source/ordinary-flow/UQ gates.\n"
        "- `retry_decision.csv`: retry/no-retry decision and claim boundary.\n"
        "- `scheduler_safe_retry_runbook.md`: future scheduler row requirements.\n"
        "- `endpoint_field_requirement_table.csv`: fields required before endpoint use.\n"
        "- `f3_vs_f6_comparison_prerequisites.csv`: comparison is blocked until an admissible F6 row exists.\n"
        "- `lower_right_negative_result_classification.csv`: lower-right result is section-effective/diagnostic only.\n"
        "- `s11_decision.csv`: S11/S15/S6 remain blocked.\n\n"
        "## Core Scientific Boundary\n\n"
        "The lower-right pressure rise is hydrostatic/recovery/section-effective diagnostic evidence, not negative loss and not component-K/F6 evidence. CAND-001 is retryable as source recovery only; the current pressure closure path remains unadmitted.\n"
    )
    (OUT_DIR / "README.md").write_text(readme)

    output_files = [str(p.relative_to(ROOT)) for p in sorted(OUT_DIR.glob("*")) if p.is_file()]
    write_closeout(summary, output_files)
    return summary


def write_closeout(summary: dict[str, Any], output_files: list[str]) -> None:
    provenance = [str(path / "summary.json") for path in SOURCES.values()]
    status_path = ROOT / ".agent/status" / f"{DATE}_{TASK_ID}.md"
    journal_path = ROOT / ".agent/journal" / DATE / "s10-s14-pressure-f6-cand001-retry-and-uq-gate.md"
    import_path = ROOT / "imports" / f"{DATE}_{SLUG}.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    import_path.parent.mkdir(parents=True, exist_ok=True)

    changed = output_files + [
        str(status_path.relative_to(ROOT)),
        str(journal_path.relative_to(ROOT)),
        str(import_path.relative_to(ROOT)),
        "tools/analyze/build_s10_s14_pressure_f6_cand001_retry_and_uq_gate.py",
        "tools/analyze/test_s10_s14_pressure_f6_cand001_retry_and_uq_gate.py",
    ]
    outputs = "\n".join(f"- `{item}`" for item in changed)
    guardrail = (
        "No native-output mutation, registry/admission mutation, scheduler action, solver/"
        "postprocessing/sampler launch, Fluid/external edit, protected scoring, fitting/model "
        "selection, F6 fit, component K, cluster K, clipped K, hidden/global multiplier, "
        "S11/S15/S6 trigger, blocker-register change, thesis edit, or mixed-basis promotion."
    )
    status_path.write_text(
        frontmatter("status", "complete", provenance)
        + "# S10/S14 Pressure F6 CAND-001 Retry And UQ Gate Status\n\n"
        + f"Decision: `{summary['decision']}`\n\n"
        + "## Objective\n\n"
        + "Decide whether CAND-001 should proceed to a future scheduler-safe retry row, while preserving the lower-right pressure result as negative/section-effective evidence rather than component-K/F6 evidence.\n\n"
        + "## Outcome\n\n"
        + "CAND-001 is recommended for a future scheduler-safe retry runbook only. It is not current F6 evidence and does not unblock S11, S15, or S6.\n\n"
        + "## Changes Made\n\n"
        + outputs
        + "\n\n## Validation\n\n"
        + "- `python3.11 -m py_compile tools/analyze/build_s10_s14_pressure_f6_cand001_retry_and_uq_gate.py tools/analyze/test_s10_s14_pressure_f6_cand001_retry_and_uq_gate.py`\n"
        + "- `python3.11 tools/analyze/test_s10_s14_pressure_f6_cand001_retry_and_uq_gate.py`\n"
        + "- `python3.11 tools/agent/finish_task.py --task-id TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21`\n\n"
        + "## Guardrails\n\n"
        + guardrail
        + "\n\n## Unresolved Blockers\n\n"
        + "- CAND-001 has zero terminal-success cases and zero endpoint fields ready.\n"
        + "- Ordinary candidate pairs remain zero.\n"
        + "- Same-QOI mesh/time UQ admissible rows remain zero.\n"
        + "- F3-vs-F6 comparison remains not evaluated because no ordinary/admitted F6 candidate exists.\n"
    )
    journal_path.write_text(
        frontmatter("journal", "complete", provenance)
        + "# S10/S14 Pressure F6 CAND-001 Retry And UQ Gate Journal\n\n"
        + "## What Was Tried\n\n"
        + "Existing pressure/F6 timeout, source-readiness, ordinary-flow, same-QOI UQ, S14 branch-use, and lower-right section-effective packages were reduced into a gate matrix and scheduler-safe retry runbook.\n\n"
        + "## What Worked\n\n"
        + "The evidence cleanly separates a retryable scheduler/source-terminal problem from pressure-admission evidence. The package identifies the exact endpoint fields and flow/UQ gates needed before any future F6 review.\n\n"
        + "## What Did Not Work\n\n"
        + "The current evidence does not support endpoint sampler release, F6 scoring, component-K admission, cluster-K admission, F3-vs-F6 comparison, or S11/S15/S6 trigger.\n\n"
        + "## Analysis\n\n"
        + "The lower-right pressure rise is hydrostatic dominated and its small negative residual remains section-effective/pressure-recovery diagnostic evidence. Calling it negative loss or component-K/F6 evidence would violate ordinary-flow, component-isolation, same-basis straight-reference, and same-QOI UQ gates.\n\n"
        + "## Next Useful Actions\n\n"
        + "Open a separate scheduler row if CAND-001 is still worth compute. Otherwise audit CAND-002 corrected +/-10Q terminal readiness before more CAND-001 compute. In either branch, stop before F6 scoring until endpoint fields, RAF/RMF, source/property, and same-QOI UQ pass.\n"
    )
    write_json(
        import_path,
        {
            "task": TASK_ID,
            "task_id": TASK_ID,
            "date": DATE,
            "decision": summary["decision"],
            "changed_files": changed,
            "read_only_context": [str(path) for path in SOURCES.values()],
            "native_solver_outputs_mutated": False,
            "registry_mutated": False,
            "registry_or_admission_mutated": False,
            "scheduler_action": False,
            "external_fluid_edit": False,
            "fluid_or_external_repo_edited": False,
            "validation_holdout_external_rows_scored": 0,
            "fitting_or_model_selection": False,
            "f6_fit_performed": False,
            "component_k_admitted": False,
            "cluster_k_admitted": False,
            "clipped_k": False,
            "hidden_global_multiplier": False,
            "s11_s15_s6_trigger": False,
        },
    )


def main() -> int:
    summary = build()
    print(f"wrote {OUT_DIR.relative_to(ROOT)}")
    print(summary["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
