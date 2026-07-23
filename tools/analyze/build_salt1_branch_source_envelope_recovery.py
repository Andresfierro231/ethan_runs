#!/usr/bin/env python3
"""Build a strict Salt1 branch source-envelope recovery package."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


TASK_ID = "TODO-SALT1-BRANCH-SOURCE-ENVELOPE-RECOVERY-2026-07-22"
DATE = "2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_salt1_branch_source_envelope_recovery"

PREVIOUS_RECOVERY = REPO / "work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate"
SALT1_RUNTIME = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_runtime_unblock_freeze_blind_predict"
SOURCE_PREFLIGHT = REPO / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
POSTPROC_INVENTORY = REPO / "work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package"
CASE_METADATA = REPO / "reports/2026-06/2026-06-02/2026-06-02_ethan_case_metadata_index/ethan_case_metadata_index.csv"

RECOVERY_ROWS = PREVIOUS_RECOVERY / "salt1_external_bc_recovery_rows.csv"
AUGMENTED_DICT = PREVIOUS_RECOVERY / "augmented_fluid_external_boundary_runtime_dictionary.csv"
PREVIOUS_RUNTIME_AUDIT = PREVIOUS_RECOVERY / "runtime_leakage_audit.csv"
PREVIOUS_FREEZE_GATE = PREVIOUS_RECOVERY / "candidate_freeze_gate.csv"
RUNTIME_OPERATOR = SALT1_RUNTIME / "salt1_recovered_operator_rows_for_fluid.csv"
RUNTIME_PROVENANCE_GATE = SALT1_RUNTIME / "salt1_recovery_provenance_gate.csv"
POST_RUNTIME_FREEZE_GATE = SALT1_RUNTIME / "post_runtime_freeze_gate.csv"
NOMINAL_PREFLIGHT = SOURCE_PREFLIGHT / "nominal_train_release_audit.csv"
POSTPROC_STATS = POSTPROC_INVENTORY / "salt14_postprocessing_window_stats.csv"

EXPECTED_FAMILIES = ["cooling_branch", "downcomer", "lower_leg", "upcomer", "junction"]
FORBIDDEN_SOURCE_TOKENS = ("wallHeatFlux", "postProcessing")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def yes(value: object) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass"}


def path_exists(path: Path) -> bool:
    return path.exists()


def contains_forbidden_source(*values: str) -> bool:
    text = " ".join(value or "" for value in values)
    return any(token in text for token in FORBIDDEN_SOURCE_TOKENS)


def source_class(row: dict[str, str]) -> str:
    if contains_forbidden_source(row.get("source_paths", ""), row.get("area_basis", "")):
        return "diagnostic_or_geometry_recovered_with_wallheatflux_trace"
    if row.get("boundary_field_availability_status") == "setup_convection_and_radiation_fields_present":
        return "setup_boundary_fields_only"
    return "missing_or_unknown"


def build_evidence_matrix(recovery_rows: list[dict[str, str]], runtime_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_family = {row["segment_id"]: row for row in recovery_rows if row.get("case_id") == "salt_1"}
    runtime_by_family = {row["source_family"]: row for row in runtime_rows if row.get("case_id") == "salt_1"}
    rows: list[dict[str, object]] = []
    for family in EXPECTED_FAMILIES:
        row = by_family.get(family, {})
        runtime = runtime_by_family.get(family, {})
        recovered = bool(row)
        setup_fields_present = (
            recovered
            and row.get("boundary_field_availability_status") == "setup_convection_and_radiation_fields_present"
            and all(row.get(field, "").strip() for field in ["h_W_m2_K", "Ta_K", "Tsur_K", "emissivity"])
        )
        area_present = recovered and bool(row.get("area_m2", "").strip())
        wall_layer_present = recovered and "available" in row.get("wall_layer_resistance_status", "")
        forbidden_trace = contains_forbidden_source(row.get("source_paths", ""), row.get("area_basis", ""), runtime.get("source_paths", ""))
        runtime_forbidden_flags_clear = all(
            not yes(runtime.get(field, "False"))
            for field in [
                "runtime_CFD_mdot_used",
                "runtime_Qwall_used",
                "runtime_validation_temperature_used",
                "runtime_wallHeatFlux_used",
            ]
        )
        diagnostic_operator_usable = recovered and setup_fields_present and runtime_forbidden_flags_clear
        strict_release_candidate = recovered and setup_fields_present and area_present and wall_layer_present and not forbidden_trace and family != "junction"
        if family == "junction":
            strict_release_candidate = False
        if not recovered:
            release_blocker = "missing Salt1 row-specific external-boundary/operator family"
        elif forbidden_trace:
            release_blocker = "source or area provenance still traces through wallHeatFlux/postProcessing"
        elif not wall_layer_present:
            release_blocker = "wall-layer basis unavailable"
        else:
            release_blocker = "source_use_category remains diagnostic/not-fit pending S11/S15"
        rows.append(
            {
                "case_key": "salt1_nominal",
                "case_id": "salt_1",
                "source_family": family,
                "recovered_row_present": recovered,
                "diagnostic_operator_usable": diagnostic_operator_usable,
                "setup_h_Ta_Tsur_emissivity_present": setup_fields_present,
                "area_present": area_present,
                "wall_layer_metadata_present": wall_layer_present,
                "forbidden_wallHeatFlux_or_postProcessing_trace": forbidden_trace,
                "strict_source_envelope_release_candidate": strict_release_candidate,
                "h_W_m2_K": row.get("h_W_m2_K", ""),
                "area_m2": row.get("area_m2", ""),
                "hA_W_K": row.get("hA_W_K", runtime.get("hA_W_K", "")),
                "Ta_K": row.get("Ta_K", runtime.get("Ta_K", "")),
                "Tsur_K": row.get("Tsur_K", runtime.get("Tsur_K", "")),
                "emissivity": row.get("emissivity", runtime.get("emissivity", "")),
                "patch_count": row.get("patch_count", ""),
                "patch_names": row.get("patch_names", ""),
                "source_class": source_class(row) if recovered else "missing",
                "release_blocker": "" if strict_release_candidate else release_blocker,
                "source_paths": row.get("source_paths", runtime.get("source_paths", "")),
            }
        )
    return rows


def build_postproc_junction_context(stats_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    junction_rows = [
        row
        for row in stats_rows
        if row.get("case_family") == "salt1"
        and row.get("quantity") == "Q_wall_patch_W"
        and "junction" in row.get("patch_or_surface", "")
    ]
    grouped = Counter(row.get("case_id", "") for row in junction_rows)
    context_rows: list[dict[str, object]] = []
    for case_id, count in sorted(grouped.items()):
        values = [float(row["mean"]) for row in junction_rows if row.get("case_id") == case_id and row.get("mean")]
        context_rows.append(
            {
                "case_id": case_id,
                "salt_family": "salt1",
                "junction_wallHeatFlux_rows": count,
                "diagnostic_qwall_sum_W": sum(values),
                "runtime_allowed": False,
                "release_use": "diagnostic_only_forbidden_runtime_input",
                "reason": "forbidden: postProcessing wallHeatFlux can show a missing junction heat family exists but cannot provide setup-only predictive source-envelope coefficients",
            }
        )
    if not context_rows:
        context_rows.append(
            {
                "case_id": "salt1_nominal",
                "salt_family": "salt1",
                "junction_wallHeatFlux_rows": 0,
                "diagnostic_qwall_sum_W": "",
                "runtime_allowed": False,
                "release_use": "not_available",
                "reason": "forbidden: no Salt1 junction wallHeatFlux rows found in reviewed postProcessing inventory",
            }
        )
    return context_rows


def build_metadata_context(metadata_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in metadata_rows:
        if row.get("source_id") != "viscosity_screening_salt_test_1_jin_coarse_mesh":
            continue
        rows.append(
            {
                "source_id": row["source_id"],
                "source_root": row["source_root"],
                "heater_power_W": row["heater_power_W"],
                "cooling_power_W": row["cooling_power_W"],
                "T_init_K": row["T_init_K"],
                "heater_Ta_K": row["heater_Ta_K"],
                "cooler_Ta_K": row["cooler_Ta_K"],
                "insulated_Ta_K": row["insulated_Ta_K"],
                "geometry_dir": row["geometry_dir"],
                "geometry_stl_count": row["geometry_stl_count"],
                "geometry_stl_examples": row["geometry_stl_examples"],
                "runtime_release_use": "setup_context_only",
                "limitation": "metadata confirms Salt1 setup and junction STL examples but does not provide a mapped junction hA/operator row",
            }
        )
    return rows


def build_gate_matrix(evidence_rows: list[dict[str, object]], preflight_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    salt1_preflight = next(row for row in preflight_rows if row["case_key"] == "salt1_nominal")
    recovered = sum(1 for row in evidence_rows if row["recovered_row_present"])
    diagnostic = sum(1 for row in evidence_rows if row["diagnostic_operator_usable"])
    strict_candidates = sum(1 for row in evidence_rows if row["strict_source_envelope_release_candidate"])
    forbidden_trace = sum(1 for row in evidence_rows if row["forbidden_wallHeatFlux_or_postProcessing_trace"])
    return [
        {
            "gate": "salt1_expected_passive_family_coverage",
            "status": "fail_closed",
            "count_or_value": f"{recovered}/5",
            "release_allowed": False,
            "reason": "junction family is still missing from Salt1 row-specific operator evidence",
        },
        {
            "gate": "salt1_diagnostic_operator_usability",
            "status": "pass_diagnostic",
            "count_or_value": f"{diagnostic}/5",
            "release_allowed": False,
            "reason": "four recovered rows are usable for train-only diagnostic smoke but not coefficient/source release",
        },
        {
            "gate": "wallHeatFlux_free_source_provenance",
            "status": "fail_closed",
            "count_or_value": f"{forbidden_trace} recovered rows with wallHeatFlux/postProcessing trace",
            "release_allowed": False,
            "reason": "forbidden: strict predictive source envelope cannot depend on realized wallHeatFlux or postProcessing-derived area recovery",
        },
        {
            "gate": "strict_source_envelope_candidate_rows",
            "status": "fail_closed",
            "count_or_value": strict_candidates,
            "release_allowed": False,
            "reason": "no Salt1 branch row currently satisfies complete coverage plus wallHeatFlux-free provenance",
        },
        {
            "gate": "nominal_train_source_property_preflight",
            "status": salt1_preflight["source_property_gate_status"],
            "count_or_value": salt1_preflight["source_validity_envelope_status"],
            "release_allowed": False,
            "reason": salt1_preflight["primary_blocker"],
        },
        {
            "gate": "validation_holdout_external_use",
            "status": "pass_closed",
            "count_or_value": 0,
            "release_allowed": False,
            "reason": "this recovery consumes no validation, holdout, or external-test scoring rows",
        },
        {
            "gate": "overall_salt1_branch_source_envelope",
            "status": "fail_closed_no_release",
            "count_or_value": "0 release-ready rows",
            "release_allowed": False,
            "reason": "recover setup-only junction geometry/operator and replace wallHeatFlux-traced area/source provenance before S11/S15",
        },
    ]


def build_unblock_queue() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "next_task": "Salt1 junction setup-only parser recovery",
            "why": "PASSIVE-H2 family coverage is 4/5 without junction.",
            "done_when": "Salt1 junction row has segment mapping, area, h/Ta/Tsur/emissivity, wall-layer status, and no wallHeatFlux/postProcessing source trace.",
            "forbidden_shortcut": "forbidden: copying Salt2 junction hA to Salt1 or using Salt1 wallHeatFlux q-loss as runtime coefficient",
        },
        {
            "priority": 2,
            "next_task": "Salt1 area provenance repair",
            "why": "Recovered non-junction families still cite wallHeatFlux Q/q geometry recovery.",
            "done_when": "area and coverage are computed from mesh/geometry/setup fields or a documented geometry invariant, not realized wallHeatFlux.",
            "forbidden_shortcut": "forbidden: labeling wallHeatFlux-derived area as setup-only without an independent check",
        },
        {
            "priority": 3,
            "next_task": "Candidate-specific S11 source/property rerun",
            "why": "Preflight labels are complete but release remains blocked.",
            "done_when": "candidate-specific strict source envelope and property sensitivity gates pass for Salt1-4 nominal train rows.",
            "forbidden_shortcut": "releasing validation/holdout/external rows or freezing coefficients before the source envelope passes",
        },
        {
            "priority": 4,
            "next_task": "One frozen Salt1-4 train-only candidate then blind prediction",
            "why": "Blind Salt2 +/-5Q and val_salt2 predictions need a frozen runtime-legal coefficient set.",
            "done_when": "one predeclared candidate is frozen on Salt1-4 only and evaluated on protected rows without coefficient changes.",
            "forbidden_shortcut": "using protected-row errors for model selection or post-hoc correction",
        },
    ]


def build_source_manifest() -> list[dict[str, object]]:
    sources = [
        ("previous_recovery_rows", RECOVERY_ROWS, "Salt1 recovered external-boundary/operator rows"),
        ("previous_augmented_dictionary", AUGMENTED_DICT, "Augmented Fluid external-boundary dictionary context"),
        ("previous_runtime_audit", PREVIOUS_RUNTIME_AUDIT, "Runtime leakage audit from recovery package"),
        ("previous_freeze_gate", PREVIOUS_FREEZE_GATE, "Prior freeze gate"),
        ("salt1_runtime_operator", RUNTIME_OPERATOR, "Salt1 operator rows used by diagnostic smoke"),
        ("salt1_runtime_provenance_gate", RUNTIME_PROVENANCE_GATE, "Salt1 runtime provenance gate"),
        ("post_runtime_freeze_gate", POST_RUNTIME_FREEZE_GATE, "Post-runtime freeze blockers"),
        ("source_property_preflight", NOMINAL_PREFLIGHT, "Salt1-4 nominal train source/property preflight"),
        ("postprocessing_inventory", POSTPROC_STATS, "Salt1 junction postProcessing diagnostic context"),
        ("case_metadata", CASE_METADATA, "Salt1 setup metadata and geometry/STL context"),
    ]
    return [
        {
            "source_id": source_id,
            "path": str(path.relative_to(REPO)),
            "exists": path_exists(path),
            "use": use,
            "mutation_status": "read_only",
        }
        for source_id, path, use in sources
    ]


def readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {RECOVERY_ROWS.relative_to(REPO)}
  - {RUNTIME_OPERATOR.relative_to(REPO)}
  - {NOMINAL_PREFLIGHT.relative_to(REPO)}
  - {POSTPROC_STATS.relative_to(REPO)}
tags: [salt1, source-property, source-envelope, passive-h2, no-release]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/salt1-branch-source-envelope-recovery.md
  - imports/2026-07-22_salt1_branch_source_envelope_recovery.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Salt1 Branch Source-Envelope Recovery

## Result

Decision: `{summary["decision"]}`.

This package turns the Salt1 PASSIVE-H2 diagnostic recovery into a strict
source-envelope release audit. It does not run Fluid, score, fit, admit,
release source/property rows, or freeze coefficients.

- expected Salt1 passive/source families: `{summary["expected_source_families"]}`
- recovered diagnostic families: `{summary["recovered_source_families"]}`
- missing families: `{summary["missing_source_families"]}`
- rows with wallHeatFlux/postProcessing provenance trace: `{summary["forbidden_trace_rows"]}`
- strict release-ready rows: `{summary["strict_release_ready_rows"]}`
- protected score values emitted: `{summary["score_values_emitted"]}`

## Interpretation

Salt1 is no longer blocked by total absence of external-boundary rows: four
ambient-wall families can drive a train-only diagnostic smoke path. It is still
blocked for final predictive release because the `junction` family is absent
and the recovered non-junction area/source provenance still carries a
wallHeatFlux/postProcessing trace. Those traces are acceptable as diagnostic
evidence but not as runtime/source-envelope release evidence.

The shortest rigorous unblock is therefore narrow: recover the Salt1 junction
and replace the wallHeatFlux-traced area/coverage basis with setup-only
mesh/geometry provenance, then rerun the candidate-specific S11/S15 gate.

## Outputs

- `salt1_branch_source_evidence_matrix.csv`
- `salt1_source_envelope_gate_matrix.csv`
- `salt1_junction_diagnostic_context.csv`
- `salt1_setup_metadata_context.csv`
- `s11_s15_unblock_queue.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, thesis current/LaTeX file, validation/holdout/
external-test score, fitting, tuning, model selection, source/property release,
protected-row release, candidate freeze, coefficient admission, blocker
register, runtime-leakage rule, hidden multiplier, or residual absorption into
internal Nu was changed.
"""


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    recovery_rows = read_csv(RECOVERY_ROWS)
    runtime_rows = read_csv(RUNTIME_OPERATOR)
    preflight_rows = read_csv(NOMINAL_PREFLIGHT)
    stats_rows = read_csv(POSTPROC_STATS)
    metadata_rows = read_csv(CASE_METADATA)

    evidence_rows = build_evidence_matrix(recovery_rows, runtime_rows)
    junction_context = build_postproc_junction_context(stats_rows)
    metadata_context = build_metadata_context(metadata_rows)
    gate_rows = build_gate_matrix(evidence_rows, preflight_rows)
    unblock_rows = build_unblock_queue()
    no_mutation_rows = [
        {"guardrail": "native_solver_outputs_mutated", "value": False},
        {"guardrail": "registry_or_admission_mutated", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "fluid_or_external_edit", "value": False},
        {"guardrail": "validation_holdout_external_scoring", "value": False},
        {"guardrail": "fitting_or_model_selection_performed", "value": False},
        {"guardrail": "source_property_release", "value": False},
        {"guardrail": "protected_row_release", "value": False},
        {"guardrail": "candidate_freeze", "value": False},
        {"guardrail": "coefficient_admission", "value": False},
        {"guardrail": "wallHeatFlux_runtime_leakage", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
        {"guardrail": "blocker_register_change", "value": False},
    ]
    source_manifest = build_source_manifest()

    write_csv(
        OUT / "salt1_branch_source_evidence_matrix.csv",
        evidence_rows,
        [
            "case_key",
            "case_id",
            "source_family",
            "recovered_row_present",
            "diagnostic_operator_usable",
            "setup_h_Ta_Tsur_emissivity_present",
            "area_present",
            "wall_layer_metadata_present",
            "forbidden_wallHeatFlux_or_postProcessing_trace",
            "strict_source_envelope_release_candidate",
            "h_W_m2_K",
            "area_m2",
            "hA_W_K",
            "Ta_K",
            "Tsur_K",
            "emissivity",
            "patch_count",
            "patch_names",
            "source_class",
            "release_blocker",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "salt1_source_envelope_gate_matrix.csv",
        gate_rows,
        ["gate", "status", "count_or_value", "release_allowed", "reason"],
    )
    write_csv(
        OUT / "salt1_junction_diagnostic_context.csv",
        junction_context,
        ["case_id", "salt_family", "junction_wallHeatFlux_rows", "diagnostic_qwall_sum_W", "runtime_allowed", "release_use", "reason"],
    )
    write_csv(
        OUT / "salt1_setup_metadata_context.csv",
        metadata_context,
        [
            "source_id",
            "source_root",
            "heater_power_W",
            "cooling_power_W",
            "T_init_K",
            "heater_Ta_K",
            "cooler_Ta_K",
            "insulated_Ta_K",
            "geometry_dir",
            "geometry_stl_count",
            "geometry_stl_examples",
            "runtime_release_use",
            "limitation",
        ],
    )
    write_csv(OUT / "s11_s15_unblock_queue.csv", unblock_rows, ["priority", "next_task", "why", "done_when", "forbidden_shortcut"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_rows, ["guardrail", "value"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "exists", "use", "mutation_status"])

    recovered = [row["source_family"] for row in evidence_rows if row["recovered_row_present"]]
    missing = [row["source_family"] for row in evidence_rows if not row["recovered_row_present"]]
    forbidden_trace_rows = sum(1 for row in evidence_rows if row["forbidden_wallHeatFlux_or_postProcessing_trace"])
    strict_ready = sum(1 for row in evidence_rows if row["strict_source_envelope_release_candidate"])
    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "salt1_branch_source_envelope_recovery_fail_closed_diagnostic_only",
        "expected_source_families": len(EXPECTED_FAMILIES),
        "recovered_source_families": len(recovered),
        "missing_source_families": ";".join(missing),
        "forbidden_trace_rows": forbidden_trace_rows,
        "strict_release_ready_rows": strict_ready,
        "diagnostic_operator_usable_rows": sum(1 for row in evidence_rows if row["diagnostic_operator_usable"]),
        "junction_diagnostic_context_rows": len(junction_context),
        "setup_metadata_rows": len(metadata_context),
        "release_allowed": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "score_values_emitted": 0,
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection_performed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "runtime_leakage_relaxation": False,
        "residual_absorbed_into_internal_nu": False,
        "blocker_register_change": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
