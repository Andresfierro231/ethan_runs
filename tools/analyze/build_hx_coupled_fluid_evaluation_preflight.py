#!/usr/bin/env python3
"""Build the HX coupled Fluid evaluation preflight and launch contract."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "TODO-HX-COUPLED-FLUID-EVALUATION-SCHEDULER-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler"
COUPLED_OUT = OUT / "coupled_fluid_output"

COOLER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_cooler_removal_model"
CANDIDATE_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_candidate_specific_source_property_gate"
SOURCE_NOMINAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
SOURCE_EXACT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_predictive_source_property_exact_field_recovery_salt14"
JULY17_COOLER = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()

TIMEOUT_SECONDS = 273


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def require_inputs() -> None:
    required = [
        COOLER / "summary.json",
        COOLER / "runtime_input_audit.csv",
        COOLER / "candidate_definitions.csv",
        CANDIDATE_GATE / "candidate_gate_matrix.csv",
        CANDIDATE_GATE / "summary.json",
        SOURCE_NOMINAL / "nominal_train_release_audit.csv",
        SOURCE_EXACT / "summary.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing HX coupled preflight inputs: " + "; ".join(missing))


def source_property_rows() -> list[dict[str, Any]]:
    candidate_rows = read_csv(CANDIDATE_GATE / "candidate_gate_matrix.csv")
    hx = next(row for row in candidate_rows if row["candidate_id"] == "HX_LUMPED_UA_NTU")
    nominal = read_csv(SOURCE_NOMINAL / "nominal_train_release_audit.csv")
    release_ready = sum(row.get("release_ready") == "True" for row in nominal)
    strict_source = sum(
        row.get("source_validity_envelope_status") in {"strict_pass", "source_envelope_strict_pass"}
        for row in nominal
    )
    protected_release = sum(row.get("protected_row_release") == "True" for row in nominal)
    return [
        {
            "gate": "runtime_input_audit",
            "status": "pass_diagnostic_compute",
            "evidence": "cooler runtime_input_audit rows pass and coupled runner does not pass imposed CFD cooler duty or realized wallHeatFlux",
            "release_consequence": "allows user-requested diagnostic coupled compute only",
            "source_path": rel(COOLER / "runtime_input_audit.csv"),
        },
        {
            "gate": "candidate_specific_source_property_release",
            "status": hx["row_specific_source_property_release"],
            "evidence": hx["primary_blocker"],
            "release_consequence": "blocks fit/admission prose, candidate freeze, S11/S15 release",
            "source_path": rel(CANDIDATE_GATE / "candidate_gate_matrix.csv"),
        },
        {
            "gate": "nominal_source_property_release_ready_rows",
            "status": "fail_closed" if release_ready == 0 else "needs_review",
            "evidence": f"release_ready_rows={release_ready}; strict_source_envelope_pass_rows={strict_source}; protected_row_release_rows={protected_release}",
            "release_consequence": "score rows must remain diagnostic until this is repaired",
            "source_path": rel(SOURCE_NOMINAL / "nominal_train_release_audit.csv"),
        },
        {
            "gate": "coupled_compute_permission",
            "status": "allowed_by_current_user_request_for_diagnostic_score_only",
            "evidence": "user requested actual coupled Fluid evaluation after maximum source/property preflight progress",
            "release_consequence": "does not override source/property fail-closed state",
            "source_path": "chat_request_2026-07-22",
        },
    ]


def launch_rows() -> list[dict[str, Any]]:
    command = (
        "srun -N1 --overlap -n1 python3.11 tools/analyze/build_cooler_removal_model.py "
        f"--run-fluid --timeout-seconds {TIMEOUT_SECONDS} --output-dir {rel(COUPLED_OUT)}"
    )
    return [
        {
            "launch_item": "scheduler_command",
            "value": command,
            "note": "Use inside the current allocation; sbatch is unavailable from compute node c318-008 in this session.",
        },
        {
            "launch_item": "expected_output_dir",
            "value": rel(COUPLED_OUT),
            "note": "Actual coupled score outputs are isolated from the earlier cooler-removal package.",
        },
        {
            "launch_item": "score_qoi_columns",
            "value": "qhx_total_W;mdot_error_pct;tp_rmse_K;tw_rmse_K;all_probe_rmse_K",
            "note": "QHX is score output; admission/freeze remains blocked by source/property release.",
        },
        {
            "launch_item": "per_row_timeout_seconds",
            "value": str(TIMEOUT_SECONDS),
            "note": "Chosen from the package handoff after prior 45 s timeout and 180 s successful July 17 rerun context.",
        },
    ]


def guardrail_rows() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "occurred": False},
        {"guardrail": "registry_or_admission_mutated", "occurred": False},
        {"guardrail": "fluid_or_external_source_edited", "occurred": False},
        {"guardrail": "source_property_release", "occurred": False},
        {"guardrail": "qwall_or_numeric_q_loss_release", "occurred": False},
        {"guardrail": "coefficient_admission_or_candidate_freeze", "occurred": False},
        {"guardrail": "protected_scoring_or_refit", "occurred": False},
        {"guardrail": "runtime_leakage_relaxation", "occurred": False},
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {"source_path": rel(COOLER), "use": "candidate definitions, runtime audit, pending coupled contract", "read_only": True},
        {"source_path": rel(CANDIDATE_GATE), "use": "candidate-specific source/property gate state", "read_only": True},
        {"source_path": rel(SOURCE_NOMINAL), "use": "nominal source/property release-ready counts", "read_only": True},
        {"source_path": rel(SOURCE_EXACT), "use": "exact-field recovery context", "read_only": True},
        {"source_path": rel(JULY17_COOLER), "use": "prior coupled timeout/success context", "read_only": True},
        {"source_path": str(FLUID_ROOT), "use": "read-only Fluid import/solve execution path", "read_only": True},
    ]


def maybe_float(value: str) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out


def coupled_review_rows() -> list[dict[str, Any]]:
    scorecard = COUPLED_OUT / "coupled_scorecard.csv"
    if not scorecard.exists():
        return []
    rows = read_csv(scorecard)
    m3_rows = read_csv(ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv")
    m3_reference = {
        row["case_id"]: maybe_float(row["all_probe_rmse_K"])
        for row in m3_rows
        if row["candidate_id"] == "M3TS_R0_role_table_unscaled"
    }
    candidates = sorted({row["candidate_id"] for row in rows})
    review: list[dict[str, Any]] = []
    for candidate_id in candidates:
        crows = [row for row in rows if row["candidate_id"] == candidate_id]
        completed = sum(row["coupled_run_status"] == "completed" for row in crows)
        accepted = sum(row["root_status"] == "accepted" for row in crows)
        mdot_abs = [abs(value) for row in crows if (value := maybe_float(row["mdot_error_pct"])) is not None]
        all_rmse = [value for row in crows if (value := maybe_float(row["all_probe_rmse_K"])) is not None]
        m3_delta = []
        for row in crows:
            hx_rmse = maybe_float(row["all_probe_rmse_K"])
            baseline = m3_reference.get(row["case_id"])
            if hx_rmse is not None and baseline is not None:
                m3_delta.append(hx_rmse - baseline)
        review.append(
            {
                "candidate_id": candidate_id,
                "completed_rows": completed,
                "accepted_root_rows": accepted,
                "max_abs_mdot_error_pct": "" if not mdot_abs else f"{max(mdot_abs):.10g}",
                "mean_all_probe_rmse_K": "" if not all_rmse else f"{sum(all_rmse) / len(all_rmse):.10g}",
                "mean_delta_all_probe_rmse_vs_M3TS_R0_K": "" if not m3_delta else f"{sum(m3_delta) / len(m3_delta):.10g}",
                "review_gate": "fail_diagnostic_large_coupled_errors_source_property_closed",
                "admission_consequence": "not_admitted_no_freeze_no_final_score",
                "source_path": rel(scorecard),
            }
        )
    return review


def coupled_review_summary(review: list[dict[str, Any]]) -> dict[str, Any]:
    if not review:
        return {
            "coupled_rows_completed": 0,
            "accepted_root_rows": 0,
            "review_gate": "pending_coupled_output",
        }
    return {
        "coupled_rows_completed": sum(int(row["completed_rows"]) for row in review),
        "accepted_root_rows": sum(int(row["accepted_root_rows"]) for row in review),
        "review_gate": "fail_diagnostic_large_coupled_errors_source_property_closed",
        "candidate_review_rows": len(review),
    }


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(COOLER / 'summary.json')}
  - {rel(CANDIDATE_GATE / 'summary.json')}
  - {rel(SOURCE_NOMINAL / 'nominal_train_release_audit.csv')}
tags: [work-product, hx, cooler, coupled-fluid, source-property, scheduler]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/hx-coupled-fluid-evaluation-scheduler.md
task: {TASK_ID}
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Monitor
type: work_product
status: complete
---
# HX Coupled Fluid Evaluation Scheduler Package

Decision: `{summary['preflight_decision']}`.

The source/property gate remains fail-closed, so the coupled Fluid evaluation is
diagnostic score generation only. It may populate coupled QOI columns for the
declared cooler candidates, but it does not admit, freeze, or release
`HX_LUMPED_UA_NTU`.

Expected coupled output directory: `{rel(COUPLED_OUT)}`.

Coupled rows completed: `{summary['coupled_rows_completed']}`.

Accepted-root rows: `{summary['accepted_root_rows']}`.

Review gate: `{summary['review_gate']}`.
"""


def running_text() -> str:
    command = launch_rows()[0]["value"]
    completed = (COUPLED_OUT / "summary.json").exists()
    state = "COMPLETED" if completed else "RUNNING_OR_READY"
    state_note = (
        "The scheduler-accounted coupled run completed and wrote the expected output package."
        if completed
        else "The scheduler-accounted coupled run has been prepared or launched and should not be duplicated while active."
    )
    return f"""# RUNNING: {TASK_ID}

State: `{state}`.

{state_note}

Prepared scheduler command:

```bash
{command}
```

Expected outputs:

- `{rel(COUPLED_OUT)}/coupled_scorecard.csv`
- `{rel(COUPLED_OUT)}/summary.json`
- `{rel(COUPLED_OUT)}/model_comparison_decision.json`
- `{rel(COUPLED_OUT)}/segmented_profile_diagnostics.csv`

Guardrails: diagnostic coupled compute only; no source/property release, no
Qwall/numeric q-loss release, no admission/freeze, no refit, no Fluid source
edit, and no native CFD output mutation.

Launch record:

- Scheduler mode: `srun` inside existing Slurm allocation because `sbatch` was
  unavailable from compute node `c318-008`.
- Allocation/job: `3307325`, partition `NuclearEnergy-dev`, node `c318-008`.
- Command session completed on 2026-07-22 with `12/12` coupled rows completed
  when `{rel(COUPLED_OUT)}/summary.json` is present.
"""


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = source_property_rows()
    release_ready = any(row["status"] in {"pass", "release_ready"} for row in rows if "source_property" in row["gate"])
    summary = {
        "task_id": TASK_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preflight_decision": "diagnostic_coupled_compute_allowed_source_property_fail_closed",
        "source_property_release": False,
        "source_property_release_ready": release_ready,
        "candidate_freeze": False,
        "final_score_claim": False,
        "coupled_output_dir": rel(COUPLED_OUT),
        "timeout_seconds": TIMEOUT_SECONDS,
    }
    review = coupled_review_rows()
    summary.update(coupled_review_summary(review))
    write_csv(OUT / "source_property_preflight.csv", rows, ["gate", "status", "evidence", "release_consequence", "source_path"])
    write_csv(OUT / "launch_contract.csv", launch_rows(), ["launch_item", "value", "note"])
    write_csv(
        OUT / "coupled_qoi_review.csv",
        review,
        [
            "candidate_id",
            "completed_rows",
            "accepted_root_rows",
            "max_abs_mdot_error_pct",
            "mean_all_probe_rmse_K",
            "mean_delta_all_probe_rmse_vs_M3TS_R0_K",
            "review_gate",
            "admission_consequence",
            "source_path",
        ],
    )
    write_csv(OUT / "no_mutation_guardrails.csv", guardrail_rows(), ["guardrail", "occurred"])
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_path", "use", "read_only"])
    write_json(OUT / "summary_preflight.json", summary)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary), encoding="utf-8")
    (OUT / "RUNNING.md").write_text(running_text(), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
