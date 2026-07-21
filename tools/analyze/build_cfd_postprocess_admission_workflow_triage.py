#!/usr/bin/env python3
"""Build CFD postprocessing/admission workflow triage artifacts.

This package answers the July 14 cfd-pp workflow questions without mutating
native CFD outputs. It composes existing steady-state, BC-role, split, registry,
and corrected-Q harvest evidence into a compact set of workflow decisions.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage"

STEADY_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv"
COMPACT_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_compact_lineage_table.csv"
SALT_INVENTORY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv"
ADMISSION_MATRIX = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/steady_state_admission_matrix.csv"
BC_INVENTORY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/bc_role_label_inventory.csv"
SPLIT_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/recommended_salt_split.csv"
TIMESERIES_METHODOLOGY = REPO_ROOT / "work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/METHODOLOGY.md"
HARVEST_ROOT = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission"
HARVEST_MANIFEST = HARVEST_ROOT / "stopped_salt2_salt4_pm5q/harvest_job_manifest.csv"
HARVEST_STATUS = HARVEST_ROOT / "stopped_salt2_salt4_pm5q/status_table/selected_corrected_q_status_table.csv"
HARVEST_LOG = HARVEST_ROOT / "stopped_salt2_salt4_pm5q/aggregate_registered_postprocessing.log"
REGISTRY_INDEX = REPO_ROOT / "registry/_all_postprocessing_runs.csv"
JUNE19_MANIFEST = REPO_ROOT / "jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/campaign_manifest.csv"
SALT2_VAL_README = REPO_ROOT / "jadyn_runs/salt2/2026-06-01_continuation_candidate/README.md"
ROLLUP_TABLE = REPO_ROOT / "work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/all_timeseries_case_rollup.csv"

TRIAGE_CASES = [
    "salt1_jin_hi10q_corrected",
    "salt1_jin_lo10q_corrected",
    "salt1_jin_nominal_continuation_corrected",
    "salt4_jin",
    "salt4_jin_hi5q_balq",
    "salt4_jin_hiq_hiins",
    "salt4_jin_lo5q_balq",
]

TRIAGE_FIELDNAMES = [
    "case_key",
    "lineage_or_alias",
    "detector_label",
    "steady_detection_status",
    "admission_overlay",
    "current_admission_or_split_verdict",
    "postprocessing_status",
    "bc_label_status",
    "split_discipline_status",
    "why_not_admitted_as_training_now",
    "good_reason_not_to_run_workflow",
    "workflow_action_now",
    "can_expand_training_now_after_correct_postprocessing",
    "evidence_paths",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _display(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def _find_by_source(rows: list[dict[str, str]], source_id: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("source_id") == source_id:
            return row
    return None


def _case_inventory_for(case_key: str, rows: list[dict[str, str]]) -> dict[str, str] | None:
    aliases = {
        "salt1_jin_lo10q_corrected": "salt1_jin_lo10q_corrected",
        "salt1_jin_hi10q_corrected": "salt1_jin_hi10q_corrected",
        "salt1_jin_nominal_continuation_corrected": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "salt4_jin": "viscosity_screening_salt_test_4_jin_coarse_mesh",
    }
    source = aliases.get(case_key)
    if source:
        found = _find_by_source(rows, source)
        if found:
            return found
    for row in rows:
        if case_key in {row.get("case_key"), row.get("source_id")}:
            return row
    return None


def _bc_status(case_key: str, bc_rows: list[dict[str, str]]) -> str:
    source_map = {
        "salt4_jin": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "salt1_jin_lo10q_corrected": "salt1_jin_lo10q_corrected",
        "salt1_jin_hi10q_corrected": "salt1_jin_hi10q_corrected",
    }
    source_id = source_map.get(case_key, case_key)
    matches = [row for row in bc_rows if row.get("source_id") == source_id or row.get("case_key") == source_id]
    if matches:
        roles = sorted({row.get("patch_or_role", "") for row in matches if row.get("patch_or_role")})
        return f"available for {len(matches)} grouped roles: {';'.join(roles)}"
    if case_key.startswith("salt4_jin_") and case_key.endswith("_balq"):
        return "not promoted; legacy perturbation needs row-level BC reduction before any fit use"
    if case_key == "salt4_jin_hiq_hiins":
        return "not promoted; hiins label is construction-risk and needs BC dictionary audit"
    if case_key == "salt1_jin_nominal_continuation_corrected":
        return "not promoted; Salt1 terminal row needs Salt1-specific BC/admission reduction"
    return "not found in current BC role inventory"


def _triage_row(case_key: str, steady: dict[str, dict[str, str]], compact: dict[str, dict[str, str]],
                inventory_rows: list[dict[str, str]], split_rows: list[dict[str, str]],
                bc_rows: list[dict[str, str]]) -> dict[str, object]:
    steady_row = steady.get(case_key, {})
    detector_label = steady_row.get("steady_or_needs_continuation", "")
    admission_overlay = steady_row.get("admission_overlay", "")
    evidence_paths = [p for p in [steady_row.get("steady_evidence_path"), steady_row.get("submission_evidence_path")] if p]

    inv = _case_inventory_for(case_key, inventory_rows) or {}
    split = _find_by_source(split_rows, inv.get("source_id", "")) if inv else None
    split = split or {}

    lineage = case_key
    for row in compact.values():
        if row.get("latest_run_key") == case_key:
            lineage = row.get("lineage_group", case_key)
            break

    if case_key.startswith("salt1_jin"):
        current = inv.get("admission_verdict") or admission_overlay or "diagnostic/pending"
        reason = (
            "Salt1 steady detector is not enough: Salt1 remains context-only until a dated Salt1 "
            "admission/split policy and post-run gate admit it."
        )
        no_reason = "yes; do not admit as training before Salt1 policy is defined"
        action = "prepare Salt1-specific admission package; do not train yet"
        can_train = "no"
    elif case_key == "salt4_jin":
        current = split.get("recommended_split") or inv.get("admission_verdict") or "holdout"
        reason = "It is already admitted as current mainline evidence, but split discipline preserves Salt4 as holdout."
        no_reason = "yes; keep as holdout to avoid leaking the high-power endpoint into fitting"
        action = "use for holdout scoring, not training"
        can_train = "no"
    else:
        current = admission_overlay or inv.get("admission_verdict") or "not_assessed"
        reason = (
            "This is a historical/legacy perturbation row, not a current corrected-Q training row; "
            "it needs provenance, BC-role, and operating-point admission re-opened before use."
        )
        no_reason = "yes; do not use historical/diagnostic perturbations as training without a reopened evidence contract"
        action = "leave diagnostic unless coordinator explicitly reopens legacy perturbation admission"
        can_train = "no"

    if inv.get("steady_state_admission_evidence_path"):
        evidence_paths.append(inv["steady_state_admission_evidence_path"])
    if inv.get("terminal_status_evidence_path"):
        evidence_paths.append(inv["terminal_status_evidence_path"])

    return {
        "case_key": case_key,
        "lineage_or_alias": lineage,
        "detector_label": detector_label,
        "steady_detection_status": steady_row.get("steady_state_detection_status", ""),
        "admission_overlay": admission_overlay,
        "current_admission_or_split_verdict": current,
        "postprocessing_status": inv.get("postprocessing_availability", "not shown in current salt inventory"),
        "bc_label_status": _bc_status(case_key, bc_rows),
        "split_discipline_status": split.get("recommended_split", "not training split candidate"),
        "why_not_admitted_as_training_now": reason,
        "good_reason_not_to_run_workflow": no_reason,
        "workflow_action_now": action,
        "can_expand_training_now_after_correct_postprocessing": can_train,
        "evidence_paths": "; ".join(dict.fromkeys(evidence_paths)),
    }


def _workflow_steps() -> list[dict[str, object]]:
    return [
        {
            "step_order": 1,
            "stage": "terminal_state_harvest",
            "automatable": "yes",
            "inputs": "Slurm stdout/stderr, solver logs, latest time directories, submitted job ledgers",
            "outputs": "terminal_status table with run_state, latest solver/log time, restart advance, and exact evidence paths",
            "admission_gate": "do not proceed to fit labels if job is still running or terminal evidence is missing",
        },
        {
            "step_order": 2,
            "stage": "registered_postprocessing",
            "automatable": "yes",
            "inputs": "case postProcessing trees and registry aggregation scripts",
            "outputs": "postprocessing_case_long.csv, wall_heat_flux_grouped.csv, case_summary.csv/json/sqlite, registry index row",
            "admission_gate": "diagnostic until aggregation exists and source manifest records native paths",
        },
        {
            "step_order": 3,
            "stage": "bc_role_labeling",
            "automatable": "mostly",
            "inputs": "0/T, constant/radiationProperties, system/functions, wallHeatFlux aggregates",
            "outputs": "heater/cooler/passive/rcExternalTemperature/inlet/outlet role table with emissivity and Tsur",
            "admission_gate": "reject rows with unlabeled thermal roles or ambiguous radiation/wallHeatFlux semantics",
        },
        {
            "step_order": 4,
            "stage": "steady_state_and_operating_point_gate",
            "automatable": "yes",
            "inputs": "last-window mdot, heat, temperature, post-restart advance, case-specific monitor rows",
            "outputs": "steady/quasi/needs-continuation plus operating-point/admission verdict",
            "admission_gate": "steady detector is advisory; admission also requires operating-point and terminal context",
        },
        {
            "step_order": 5,
            "stage": "split_discipline",
            "automatable": "policy-driven",
            "inputs": "case lineage, q perturbation relation, mainline split policy, validation/holdout reservations",
            "outputs": "training/validation/holdout/sensitivity-only/excluded labels",
            "admission_gate": "perturbations of a baseline are not independent training rows unless a dated policy allows it",
        },
    ]


def _harvest_status() -> list[dict[str, object]]:
    manifest = _read_csv(HARVEST_MANIFEST)
    status = _read_csv(HARVEST_STATUS)
    registry = _read_csv(REGISTRY_INDEX)
    registry_by_source = _index(registry, "source_id")
    job = manifest[0] if manifest else {}
    rows: list[dict[str, object]] = []
    for row in status:
        source = row["source_case_key"]
        reg = registry_by_source.get(source, {})
        rows.append({
            "job_id": job.get("job_id", "3295437"),
            "job_name": job.get("job_name", "saltq_s24_done_harv"),
            "scheduler_state_observed": "COMPLETED 00:12:55 exit 0:0",
            "case_key": row["case_key"],
            "source_case_key": source,
            "terminal_window_status": row["status"],
            "closure_fit_admissible_in_terminal_gate": row["closure_fit_admissible"],
            "registry_aggregate_available": "yes" if reg.get("normalized_csv") else "no",
            "normalized_csv": reg.get("normalized_csv", ""),
            "wall_heat_flux_grouped_csv": reg.get("heat_grouped_csv", ""),
            "case_summary_csv": reg.get("summary_csv", ""),
            "next_workflow_action": (
                "run BC role reduction, admission-matrix refresh, and split-policy labeling; "
                "do not silently add as independent training rows until perturbation split policy is explicit"
            ),
        })
    return rows


def _hiins_review() -> list[dict[str, object]]:
    rows = [row for row in _read_csv(JUNE19_MANIFEST) if row.get("case_key") in {"salt3_jin_hiq_hiins", "salt3_jin_loq_loins"}]
    out: list[dict[str, object]] = []
    for row in rows:
        out.append({
            "case_key": row["case_key"],
            "source_id": row["source_id"],
            "mutation_profile": row["mutation_profile"],
            "heater_scale": row["heater_scale"],
            "insulation_delta_in": row["insulation_delta_in"],
            "stage_case_dir": row["stage_case_dir"],
            "job_id": row["job_id"],
            "construction_status": (
                "misnamed for true hiins/loins: manifest says baseline insulation restored "
                "and insulation_delta_in=0.00; treat as balanced-Q/baseline-insulation historical row"
            ),
            "report_exists": "yes: June 19 campaign manifest and July 1/July 4 operational notes",
            "admission_status": "historical/diagnostic; not current corrected-Q fit evidence",
            "evidence_paths": f"{_display(JUNE19_MANIFEST)}; operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md; operational_notes/maps/cfd-runs-and-admission.md",
        })
    return out


def _salt2_comparison() -> list[dict[str, object]]:
    steady = _index(_read_csv(STEADY_TABLE), "run_key")
    registry = _index(_read_csv(REGISTRY_INDEX), "source_id")
    return [
        {
            "comparison_axis": "canonical_display_label",
            "salt2_jin": "salt2_jin / viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
            "salt2_val": "val_salt_test_2_coarse_mesh_laminar_continuation (recommended display alias for 2026-06-01_continuation_candidate)",
            "interpretation": "Use the alias in new reports; preserve original paths for provenance. The source spelling is coarse, not course.",
        },
        {
            "comparison_axis": "lineage",
            "salt2_jin": "Modern Jin Salt2 continuation from the June 18 convergence/Jin envelope wave.",
            "salt2_val": "Continuation of older external/native val_salt_test_2_coarse_mesh_laminar source under jadyn_runs/salt2/2026-06-01_continuation_candidate.",
            "interpretation": "The 2026-06-01 continuation is not a mislabeled continuation of salt2_jin; it is a distinct historical Salt2 validation/coarse-mesh lineage.",
        },
        {
            "comparison_axis": "current_steady_status",
            "salt2_jin": steady.get("salt2_jin", {}).get("steady_state_detection_status", ""),
            "salt2_val": steady.get("2026-06-01_continuation_candidate", {}).get("steady_state_detection_status", ""),
            "interpretation": "Both have steady mdot but drifting heat in the last-window rollup; neither should be treated as newly steady thermal training evidence from detector label alone.",
        },
        {
            "comparison_axis": "admission_or_use",
            "salt2_jin": "Current mainline nominal evidence; fit-admissible training row in the existing split, with thermal drift caveat.",
            "salt2_val": "Historical/diagnostic comparison candidate; needs explicit re-admission before validation or training use.",
            "interpretation": "salt2_jin is the current training anchor; salt2_val is useful as context only until re-admitted.",
        },
        {
            "comparison_axis": "registry_postprocessing",
            "salt2_jin": registry.get("viscosity_screening_salt_test_2_jin_coarse_mesh", {}).get("normalized_csv", ""),
            "salt2_val": registry.get("val_salt_test_2_coarse_mesh_laminar", {}).get("normalized_csv", ""),
            "interpretation": "Both have registry aggregates, but aggregation is not admission.",
        },
        {
            "comparison_axis": "evidence_paths",
            "salt2_jin": "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
            "salt2_val": f"{_display(SALT2_VAL_README)}; jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation",
            "interpretation": "These are separate file roots and should not be collapsed.",
        },
    ]


def _source_manifest() -> list[dict[str, object]]:
    sources = [
        STEADY_TABLE, COMPACT_TABLE, SALT_INVENTORY, ADMISSION_MATRIX, BC_INVENTORY,
        SPLIT_TABLE, TIMESERIES_METHODOLOGY, HARVEST_MANIFEST, HARVEST_STATUS,
        HARVEST_LOG, REGISTRY_INDEX, JUNE19_MANIFEST, SALT2_VAL_README, ROLLUP_TABLE,
    ]
    return [{"source_path": _display(path), "exists": path.exists(), "role": "input evidence"} for path in sources]


def _write_markdown(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {_display(STEADY_TABLE)}
  - {_display(SALT_INVENTORY)}
  - {_display(HARVEST_STATUS)}
  - {_display(JUNE19_MANIFEST)}
tags: [cfd-pp, salt-cfd, postprocessing, admission, split-discipline]
related:
  - {_display(HARVEST_ROOT / "README.md")}
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/README.md
task: AGENT-347
date: 2026-07-14
role: cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# CFD Postprocessing Admission Workflow Triage

## Observed Facts

- A workflow can be automated as a staged gate: terminal harvest, registered postprocessing, BC role labeling, steady/operating-point admission, then split discipline.
- The seven user-named rows are steady only in the detector sense where the steady table says `steady`; that is not the same as training admission.
- `salt4_jin` is already admitted current mainline evidence but is reserved as holdout, not training.
- The legacy `salt4_jin_hi5q_balq`, `salt4_jin_hiq_hiins`, and `salt4_jin_lo5q_balq` rows are historical/diagnostic unless a future row reopens their evidence contract.
- Corrected Salt2/Salt4 +/-5Q harvest job `3295437` completed and produced registry aggregates plus a terminal status table marking the four +/-5Q corrected rows closure-fit admissible under current coordinator policy.

## Inferred Interpretation

The immediate useful progress is not to train on the historical `balq`/`hiins` names. It is to process the newly harvested corrected-Q +/-5Q rows through BC role reduction, admission-matrix refresh, and split-aware labeling. Perturbations should remain grouped with their baseline unless a dated split policy allows them to expand training.

## Why The Named Rows Are Not Training-Admitted

See `steady_candidate_admission_triage.csv`. In short:

- Salt1 rows need a Salt1-specific admission/split policy before training use.
- `salt4_jin` is holdout by design.
- The Salt4 `balq`/`hiins` rows are legacy/historical and need a reopened evidence contract.

## Hiins/Loins Construction

See `hiins_loins_construction_review.csv`. The June 19 manifest records `salt3_jin_hiq_hiins` as `hiQ_balQ_baselineIns` with `insulation_delta_in=0.00`; that means it should not be treated as a true high-insulation case. There is a report trail, and it supports diagnostic/historical use rather than current fit use.

## Drift Ratio

See `drift_ratio_definition.md`. Ratio means `|a * W| / RMSE_about_trend`: the trend's change across the window measured in units of detrended oscillation amplitude.

## Salt2 Jin Versus Salt2 Val

See `salt2_jin_vs_val_comparison.csv`. `2026-06-01_continuation_candidate` is best displayed in new reports as `val_salt_test_2_coarse_mesh_laminar_continuation`. It is a distinct historical validation/coarse-mesh lineage, not the current `salt2_jin` continuation. The source spelling is `coarse`, not `course`; historical paths are preserved as provenance.

## Process Completed Harvest 3295437

This means: consume the completed postprocessing harvest outputs for Salt2/Salt4 corrected +/-5Q, verify the registry aggregates, run BC labeling/admission/split workflow, and then decide downstream use. It does not mean launch duplicate harvest jobs.

## Outputs

- `workflow_automation_steps.csv`
- `steady_candidate_admission_triage.csv`
- `corrected_q_harvest_3295437_processing_status.csv`
- `hiins_loins_construction_review.csv`
- `salt2_jin_vs_val_comparison.csv`
- `drift_ratio_definition.md`
- `source_manifest.csv`
- `summary.json`

## Summary

- Named triage rows: {summary["named_case_count"]}
- Harvested corrected +/-5Q rows ready for workflow processing: {summary["harvest_rows"]}
- Rows that can expand training immediately without split-policy change: {summary["immediate_training_expansion_rows"]}
"""


def _drift_ratio_doc() -> str:
    return f"""---
provenance:
  - {_display(TIMESERIES_METHODOLOGY)}
tags: [cfd-pp, steady-state, drift-ratio]
related:
  - {_display(STEADY_TABLE)}
task: AGENT-347
date: 2026-07-14
role: cfd-pp / Writer
type: work_product
status: complete
---
# Drift Ratio Definition

`ratio` in the drift-severity context refers to:

```text
drift_ratio = |a * W| / RMSE_about_trend
```

where `a` is the ordinary-least-squares slope over the analysis window, `W` is
the window duration, and `RMSE_about_trend` is the detrended oscillation
amplitude.

Interpretation: it measures how much the fitted trend changes across the window
in units of the case's own oscillation amplitude. The detector uses it mainly
when the mean is near zero and relative drift against the mean would be
misleading. In the July 9 methodology, `drift_ratio < 1` is steady,
`drift_ratio > 3` is not steady, and intermediate values are quasi-steady for
near-zero-mean series.
"""


def build_workflow_triage(out_dir: Path = OUT_DIR) -> dict[str, object]:
    steady_rows = _read_csv(STEADY_TABLE)
    compact_rows = _read_csv(COMPACT_TABLE)
    inventory_rows = _read_csv(SALT_INVENTORY)
    split_rows = _read_csv(SPLIT_TABLE)
    bc_rows = _read_csv(BC_INVENTORY)

    steady_by_key = _index(steady_rows, "run_key")
    compact_by_group = _index(compact_rows, "lineage_group")

    triage_rows = [
        _triage_row(case, steady_by_key, compact_by_group, inventory_rows, split_rows, bc_rows)
        for case in TRIAGE_CASES
    ]
    workflow_rows = _workflow_steps()
    harvest_rows = _harvest_status()
    hiins_rows = _hiins_review()
    salt2_rows = _salt2_comparison()
    source_rows = _source_manifest()

    _write_csv(out_dir / "workflow_automation_steps.csv", workflow_rows, [
        "step_order", "stage", "automatable", "inputs", "outputs", "admission_gate",
    ])
    _write_csv(out_dir / "steady_candidate_admission_triage.csv", triage_rows, TRIAGE_FIELDNAMES)
    _write_csv(out_dir / "corrected_q_harvest_3295437_processing_status.csv", harvest_rows, [
        "job_id", "job_name", "scheduler_state_observed", "case_key", "source_case_key",
        "terminal_window_status", "closure_fit_admissible_in_terminal_gate",
        "registry_aggregate_available", "normalized_csv", "wall_heat_flux_grouped_csv",
        "case_summary_csv", "next_workflow_action",
    ])
    _write_csv(out_dir / "hiins_loins_construction_review.csv", hiins_rows, [
        "case_key", "source_id", "mutation_profile", "heater_scale", "insulation_delta_in",
        "stage_case_dir", "job_id", "construction_status", "report_exists",
        "admission_status", "evidence_paths",
    ])
    _write_csv(out_dir / "salt2_jin_vs_val_comparison.csv", salt2_rows, [
        "comparison_axis", "salt2_jin", "salt2_val", "interpretation",
    ])
    _write_csv(out_dir / "source_manifest.csv", source_rows, ["source_path", "exists", "role"])

    summary = {
        "task": "AGENT-347",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "named_case_count": len(triage_rows),
        "harvest_rows": len(harvest_rows),
        "hiins_review_rows": len(hiins_rows),
        "immediate_training_expansion_rows": sum(
            1 for row in triage_rows
            if row["can_expand_training_now_after_correct_postprocessing"] == "yes"
        ),
        "named_case_training_flags": dict(Counter(row["can_expand_training_now_after_correct_postprocessing"] for row in triage_rows)),
        "harvest_closure_fit_admissible_rows": sum(
            1 for row in harvest_rows if row["closure_fit_admissible_in_terminal_gate"] == "yes"
        ),
        "outputs": {
            "readme": _display(out_dir / "README.md"),
            "workflow_steps": _display(out_dir / "workflow_automation_steps.csv"),
            "triage": _display(out_dir / "steady_candidate_admission_triage.csv"),
            "harvest_status": _display(out_dir / "corrected_q_harvest_3295437_processing_status.csv"),
            "hiins_review": _display(out_dir / "hiins_loins_construction_review.csv"),
            "salt2_comparison": _display(out_dir / "salt2_jin_vs_val_comparison.csv"),
            "drift_ratio": _display(out_dir / "drift_ratio_definition.md"),
            "source_manifest": _display(out_dir / "source_manifest.csv"),
        },
    }

    _write_markdown(out_dir / "drift_ratio_definition.md", _drift_ratio_doc())
    _write_markdown(out_dir / "README.md", _readme(summary))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    summary = build_workflow_triage()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
