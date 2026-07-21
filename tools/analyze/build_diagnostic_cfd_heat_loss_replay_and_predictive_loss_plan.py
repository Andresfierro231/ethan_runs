#!/usr/bin/env python3
"""Build the AGENT-410 CFD-realized heat-loss replay addendum.

This package makes the existing forced-realized-wallHeatFlux diagnostic easy
to cite in reports. It also records the current train/test data sufficiency and
the implementation plan for a setup-predictive heat-loss variant.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan"

AG350 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment"
ALIGNMENT = AG350 / "heat_loss_alignment_by_segment.csv"
AG392 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/results"
BEST_DISCREPANCY = AG392 / "best_predictive_heat_loss_discrepancy_refresh/presentation_brief.md"
MODEL_CHANGES = AG392 / "best_predictive_heat_loss_discrepancy_refresh/model_change_recommendations.csv"
SOURCE_SINK = AG392 / "external_bc_thermal_profile_parity_refresh/source_sink_parity_contract.csv"
AG402 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_salt_forward_v1_unblock"
TRAIN_TABLE = AG402 / "salt_training_fit_input_table.csv"
AG354 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation"
VAL_README = AG354 / "README.md"
VAL_COMPARISON = AG354 / "salt2_jin_comparison.csv"
VAL_SUMMARY = AG354 / "summary.json"
PRESSURE_REPORT = ROOT / "reports/2026-06/2026-06-29/2026-06-29_ethan_salt_pressure_drop_predictivity/cfd_pressure_budget_elements.csv"

FORCED_FIELDS = [
    "case_id",
    "source_id",
    "one_d_segment",
    "fluid_parent_segment",
    "model_source_W",
    "model_cooler_loss_W",
    "model_external_loss_W",
    "model_total_loss_W",
    "model_net_to_fluid_W",
    "cfd_realized_source_W",
    "cfd_realized_loss_W",
    "cfd_realized_net_to_fluid_W",
    "model_minus_cfd_realized_net_W",
    "evidence_class",
    "admissibility_status",
    "source_paths",
    "notes",
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: str | int | float | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def fmt(value: float) -> str:
    return f"{value:.12g}"


def build_forced_replay_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(ALIGNMENT):
        if row.get("path_id") != "B2_realized_wallflux_roles":
            continue
        out = {field: row.get(field, "") for field in FORCED_FIELDS}
        out["diagnostic_runtime_input"] = "realized_CFD_wallHeatFlux"
        out["predictive_status"] = "not_predictive_runtime_leakage_diagnostic"
        rows.append(out)
    return rows


def build_forced_replay_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_id"]].append(row)

    summaries: list[dict[str, Any]] = []
    for case_id, case_rows in sorted(grouped.items()):
        residuals = [fnum(row["model_minus_cfd_realized_net_W"]) for row in case_rows]
        summaries.append(
            {
                "case_id": case_id,
                "forced_replay_rows": len(case_rows),
                "segment_count": len({row["one_d_segment"] for row in case_rows}),
                "model_net_to_fluid_sum_W": fmt(sum(fnum(row["model_net_to_fluid_W"]) for row in case_rows)),
                "cfd_realized_net_to_fluid_sum_W": fmt(sum(fnum(row["cfd_realized_net_to_fluid_W"]) for row in case_rows)),
                "model_minus_cfd_realized_net_sum_W": fmt(sum(residuals)),
                "max_abs_segment_net_residual_W": fmt(max((abs(value) for value in residuals), default=0.0)),
                "diagnostic_result": "exact_net_heat_path_replay_by_construction",
                "admissibility_status": "diagnostic_only_not_predictive",
                "why_not_predictive": "uses realized CFD wallHeatFlux, which is a target/output rather than a setup runtime input",
                "source_path": rel(ALIGNMENT),
            }
        )
    return summaries


def build_train_test_sufficiency() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(TRAIN_TABLE):
        case_key = row["case_key"]
        can_train = row["use_for_thermal_fit"] == "yes"
        can_test = row["use_for_holdout_or_test"] == "yes"
        if can_train and not can_test:
            conclusion = "usable_for_user_policy_training"
        elif can_test and not can_train:
            conclusion = "usable_for_user_policy_holdout_screen_after_row_specific_gates"
        else:
            conclusion = "check_row_policy_before_use"
        rows.append(
            {
                "case_key": case_key,
                "display_label": row["display_label"],
                "split_policy": "2026-07-15_user_policy_salt1_salt4_train_salt2_pm5_holdout",
                "split_role": row["split_role"],
                "can_fit_heat_loss_variant": str(can_train).lower(),
                "can_score_heat_loss_variant": str(can_test).lower(),
                "admission_status": row["admission_status"],
                "data_sufficiency_conclusion": conclusion,
                "guardrail": row["guardrail"],
                "source_path": row["primary_evidence"],
            }
        )

    rows.extend(
        [
            {
                "case_key": "salt2_salt3_salt4_mainline_split",
                "display_label": "Salt2 train / Salt3 validation / Salt4 holdout",
                "split_policy": "earlier_forward_model_split",
                "split_role": "training_validation_holdout_reference",
                "can_fit_heat_loss_variant": "yes_if_this_split_is_declared_before_fit",
                "can_score_heat_loss_variant": "yes_for_salt3_salt4_under_this_split",
                "admission_status": "reference_policy_not_to_mix_with_user_policy",
                "data_sufficiency_conclusion": "sufficient_for_three-row_model-form_screen_not_thesis_strength_generalization",
                "guardrail": "Do not train Salt1-4 and also claim Salt3/Salt4 are untouched holdouts.",
                "source_path": "operational_notes/maps/forward-predictive-model.md",
            },
            {
                "case_key": "val_salt_test_2_coarse_mesh",
                "display_label": "val_salt_test_2_coarse_mesh",
                "split_policy": "candidate_future_external_test",
                "split_role": "historical_diagnostic_or_blocked_context",
                "can_fit_heat_loss_variant": "no",
                "can_score_heat_loss_variant": "not_yet_for_section_heat_loss",
                "admission_status": "blocked_or_diagnostic_until_explicitly_re_admitted",
                "data_sufficiency_conclusion": "lineage_and_sensor_pressure_evidence_exist_but_current_section_heat_loss_replay_package_not_found",
                "guardrail": "Can become a useful val_salt2 test only after AGENT-350-style thermal heat-loss extraction and admission.",
                "source_path": rel(VAL_README),
            },
            {
                "case_key": "other_cfd_runs",
                "display_label": "other CFD runs",
                "split_policy": "future_external_test_pool",
                "split_role": "not_currently_admitted_as_independent_heat_loss_test_set",
                "can_fit_heat_loss_variant": "no",
                "can_score_heat_loss_variant": "not_until_same_ledgers_exist",
                "admission_status": "insufficient_currently",
                "data_sufficiency_conclusion": "not sufficient for robust train on Salt1-4 and test elsewhere without matched heat-loss ledgers, boundary contracts, and split labels",
                "guardrail": "Require setup/source/sink/section heat-loss ledgers and runtime-input leakage audit before scoring.",
                "source_path": rel(TRAIN_TABLE),
            },
        ]
    )
    return rows


def build_jin_val_report_status() -> list[dict[str, Any]]:
    return [
        {
            "evidence_item": "val_salt2_lineage_and_bc_report",
            "exists": str(VAL_README.exists()).lower(),
            "status": "produced",
            "answer": "Yes, AGENT-354 documents that val_salt_test_2_coarse_mesh is distinct from salt2_jin and remains diagnostic/blocked unless re-admitted.",
            "source_path": rel(VAL_README),
        },
        {
            "evidence_item": "salt2_jin_vs_val_comparison_table",
            "exists": str(VAL_COMPARISON.exists()).lower(),
            "status": "produced",
            "answer": "Yes, the comparison table records lineage, T_init, mesh group, heater/cooler inputs, insulation thickness, mdot consensus, and admission/use differences.",
            "source_path": rel(VAL_COMPARISON),
        },
        {
            "evidence_item": "hydraulic_pressure_comparison_rows",
            "exists": str(PRESSURE_REPORT.exists()).lower(),
            "status": "produced_for_pressure_context",
            "answer": "Pressure/sensor comparison evidence exists, but it is not a section heat-loss replay.",
            "source_path": rel(PRESSURE_REPORT),
        },
        {
            "evidence_item": "val_salt2_section_heat_loss_replay",
            "exists": "false",
            "status": "not_found_as_current_report_package",
            "answer": "No current AGENT-350/365-style section heat-loss replay package for val_salt2 was found in the scoped evidence read for this addendum.",
            "source_path": rel(VAL_README),
        },
    ]


def build_predictive_variant_plan() -> list[dict[str, Any]]:
    guardrail = (
        "No realized CFD wallHeatFlux, CFD mdot, imposed CFD cooler duty, or validation "
        "temperatures as runtime inputs; fit only declared training rows and score held-out rows without refit."
    )
    return [
        {
            "step_id": "P1",
            "work_packet": "segment_and_patch_data_contract",
            "implementation_target": "Create one setup-only external-boundary table keyed by 1D segment and CFD patch role.",
            "required_inputs": "patch role, area, one_d_segment, source/sink role, junction/stub/horizontal connector coverage",
            "outputs": "loss_surface_coverage_table.csv and Fluid-ready external_boundary_table fixture",
            "rigor_gate": "coverage sums match CFD patch-role areas; junction/stub patches are first-class rows",
            "source_paths": rel(SOURCE_SINK),
            "guardrail": guardrail,
        },
        {
            "step_id": "P2",
            "work_packet": "external_circuit_physics",
            "implementation_target": "Represent h, Ta, Tsur, emissivity, wall and insulation layers from setup dictionaries.",
            "required_inputs": "external h, ambient Ta, surrounding Tsur, emissivity, layer thickness/k/coefficients",
            "outputs": "per-segment equivalent thermal resistance and optional radiative exchange from setup metadata",
            "rigor_gate": "do not add separate radiation when replaying realized wallHeatFlux; for prediction use setup metadata only",
            "source_paths": rel(SOURCE_SINK),
            "guardrail": guardrail,
        },
        {
            "step_id": "P3",
            "work_packet": "wall_shell_temperature_drive",
            "implementation_target": "Replace bulk-temperature ambient loss with a wall/shell or wall-adjacent driving temperature model.",
            "required_inputs": "bulk T, candidate wall/shell estimator, geometry, external circuit, train-only calibration if needed",
            "outputs": "wall_drive_model.py or Fluid API hook plus unit tests",
            "rigor_gate": "fit on declared training rows only; report sensitivity to bulk-drive versus wall/shell-drive",
            "source_paths": rel(MODEL_CHANGES),
            "guardrail": guardrail,
        },
        {
            "step_id": "P4",
            "work_packet": "setup_only_hx_cooler",
            "implementation_target": "Replace imposed CFD cooler duty with a setup-only HX/cooler UA/effectiveness model or selected setup-legal HX closure.",
            "required_inputs": "cooler geometry, air/fluid-side setup quantities, declared train rows",
            "outputs": "setup_only_hx_model and runtime leakage audit",
            "rigor_gate": "runtime-input audit violations = 0; score validation/holdout without refit",
            "source_paths": "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/README.md",
            "guardrail": guardrail,
        },
        {
            "step_id": "P5",
            "work_packet": "heater_and_test_section_contract",
            "implementation_target": "Separate heater realization, lower-leg passive loss, and test-section source/sink behavior.",
            "required_inputs": "heater setup power, test-section setup power, patch roles, train-only efficiency model if admitted",
            "outputs": "source_contract_table.csv and Fluid source-lane inputs",
            "rigor_gate": "heater efficiency cannot absorb passive wall, cooler, radiation, storage, or Nu residuals",
            "source_paths": rel(SOURCE_SINK),
            "guardrail": guardrail,
        },
        {
            "step_id": "P6",
            "work_packet": "split_and_validation_gate",
            "implementation_target": "Choose exactly one split policy before fitting.",
            "required_inputs": "Salt1/Salt4 user-policy table or Salt2/Salt3/Salt4 legacy split, not both simultaneously",
            "outputs": "declared_split_policy.md and train/validation/holdout score table",
            "rigor_gate": "no row changes role after seeing scores; perturbations are labeled as perturbations",
            "source_paths": rel(TRAIN_TABLE),
            "guardrail": guardrail,
        },
        {
            "step_id": "P7",
            "work_packet": "val_salt2_and_external_tests",
            "implementation_target": "Make val_salt2 a future test only after thermal section heat-loss extraction/admission.",
            "required_inputs": "val_salt2 section wallHeatFlux ledger, source/sink contract, boundary dictionary, sensor/pressure context",
            "outputs": "val_salt2_heat_loss_replay.csv and admission memo",
            "rigor_gate": "val_salt2 remains diagnostic/blocked until this package exists",
            "source_paths": rel(VAL_README),
            "guardrail": guardrail,
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        ("AGENT-350 heat-loss alignment", ALIGNMENT, "forced realized wallHeatFlux B2 diagnostic replay rows"),
        ("AGENT-350 README", AG350 / "README.md", "method and diagnostic/predictive distinction"),
        ("AGENT-392 best-discrepancy brief", BEST_DISCREPANCY, "presentation-ready current model discrepancy"),
        ("AGENT-392 model changes", MODEL_CHANGES, "physical refinement recommendations"),
        ("AGENT-392 source/sink contract", SOURCE_SINK, "setup versus realized source/sink runtime policy"),
        ("AGENT-402 train table", TRAIN_TABLE, "Salt train/holdout sufficiency under user policy"),
        ("AGENT-354 val README", VAL_README, "Jin/val lineage and admission status"),
        ("AGENT-354 val comparison", VAL_COMPARISON, "Jin Salt2 versus val Salt2 differences"),
        ("AGENT-354 val summary", VAL_SUMMARY, "val package machine-readable status"),
        ("June 29 pressure report", PRESSURE_REPORT, "pressure/sensor context for val_salt2"),
    ]
    return [
        {"source_id": source_id, "path": rel(path), "exists": str(path.exists()).lower(), "use": use}
        for source_id, path, use in sources
    ]


def build_report_addendum(summary: dict[str, Any]) -> str:
    return f"""# Diagnostic CFD-Realized Heat-Loss Replay And Predictive Loss Plan

Task: AGENT-410  
Generated: 2026-07-15

## Direct Answers

**Did we try running the 1D model with heat losses placed exactly where the CFD
model realizes them?** Yes. The prior heat-loss alignment package contains the
`B2_realized_wallflux_roles` lane, and this addendum extracts it into
`diagnostic_forced_cfd_heat_loss_replay.csv`. It forces each 1D section net heat
path to match the CFD-realized `wallHeatFlux` location for Salt2, Salt3, and
Salt4.

**Can we present it as predictive?** No. It is valuable as a leakage diagnostic
and physical limit case, but it consumes realized CFD `wallHeatFlux`, which is a
target/output. The proper label is `diagnostic_only_not_predictive`.

**Can we train on Salt1, Salt2, Salt3, Salt4 and test on other CFD runs?** Not
yet as a thesis-strength generalization claim. A user-policy training table
exists for Salt1/Salt4-family rows with Salt2 +/-5Q as holdout screening, but
that policy must not be mixed with the older Salt2 train / Salt3 validation /
Salt4 holdout split. Other CFD runs need matching heat-loss ledgers, source/sink
contracts, boundary dictionaries, and admission labels before they become an
independent test set.

**Can we test on val_salt2?** Not yet for the section heat-loss variant. The
val_salt2 lineage and Jin-vs-val comparison report exists, but a current
AGENT-350-style thermal section heat-loss replay/admission package for val_salt2
was not found in this addendum's scoped evidence. It is a good future test after
that extraction lands.

**Did we produce a Jin Salt2 versus val Salt2 report?** Yes. AGENT-354 produced
`work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/`,
including `salt2_jin_comparison.csv`.

## Forced-Replay Result

- Forced replay rows: {summary["forced_replay_rows"]}
- Cases covered: {summary["case_count"]}
- Segments per case: lower leg, upcomer, cooling branch, downcomer, junction.
- Maximum segment net residual after forcing: {summary["max_forced_replay_abs_segment_net_residual_W"]} W.
- Predictive rows admitted from this replay: 0.

The forced replay proves that exact location matching is possible if we use CFD
outputs. The scientific task is now to predict those losses from setup
quantities: junction/stub coverage, wall/shell drive, external h/Ta/Tsur/
emissivity/layers, and setup-only HX/cooler behavior.

## Files

- `diagnostic_forced_cfd_heat_loss_replay.csv`
- `diagnostic_forced_replay_case_summary.csv`
- `train_test_data_sufficiency.csv`
- `jin_vs_val_salt2_report_status.csv`
- `predictive_heat_loss_variant_plan.csv`
- `source_manifest.csv`
- `summary.json`
"""


def build_readme(summary: dict[str, Any]) -> str:
    return build_report_addendum(summary) + """
## Method

1. Read only existing work products; no OpenFOAM, scheduler, registry, native
   CFD output, or external Fluid files were mutated.
2. Filter the AGENT-350 heat-loss alignment table to the exact
   `B2_realized_wallflux_roles` path.
3. Summarize net-to-fluid residuals by case to verify the forced replay is
   exact by construction.
4. Separate data sufficiency under the July 15 user-policy split from the older
   Salt2/Salt3/Salt4 split.
5. Record val_salt2 as a future heat-loss test dependency rather than silently
   treating it as already admitted.
6. Convert the observed discrepancy into setup-only implementation work packets
   with explicit rigor gates.

## Guardrails

- Realized CFD `wallHeatFlux` remains a diagnostic target/output, not a runtime
  input for forward prediction.
- Imposed CFD cooler duty remains a diagnostic upper bound unless replaced by a
  setup-only HX/cooler model.
- Radiation in CFD `rcExternalTemperature` is embedded in total
  `wallHeatFlux`; do not double-count it during realized-wallFlux replay.
- Do not mix split policies after seeing scores.
"""


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    forced_rows = build_forced_replay_rows()
    forced_summary = build_forced_replay_summary(forced_rows)
    train_rows = build_train_test_sufficiency()
    val_status = build_jin_val_report_status()
    plan_rows = build_predictive_variant_plan()
    sources = build_source_manifest()

    residuals = [abs(fnum(row["model_minus_cfd_realized_net_W"])) for row in forced_rows]
    status_counts = Counter(row["admissibility_status"] for row in forced_rows)
    summary = {
        "task": "AGENT-410",
        "date": "2026-07-15",
        "forced_replay_rows": len(forced_rows),
        "case_count": len({row["case_id"] for row in forced_rows}),
        "forced_replay_path_id": "B2_realized_wallflux_roles",
        "forced_replay_status_counts": dict(status_counts),
        "max_forced_replay_abs_segment_net_residual_W": fmt(max(residuals, default=0.0)),
        "predictive_rows_admitted_from_forced_replay": 0,
        "can_train_salt1_to_salt4_and_test_other_cfd_now": "not_as_thesis_strength_generalization_without_more_admitted_external_tests",
        "val_salt2_current_heat_loss_test_status": "not_yet_section_heat_loss_admitted",
        "jin_vs_val_salt2_report_exists": VAL_README.exists() and VAL_COMPARISON.exists(),
        "predictive_variant_plan_steps": len(plan_rows),
        "native_cfd_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "scheduler_mutated": False,
        "registry_or_admission_state_mutated": False,
    }

    write_csv(output_dir / "diagnostic_forced_cfd_heat_loss_replay.csv", forced_rows, FORCED_FIELDS + ["diagnostic_runtime_input", "predictive_status"])
    write_csv(
        output_dir / "diagnostic_forced_replay_case_summary.csv",
        forced_summary,
        [
            "case_id",
            "forced_replay_rows",
            "segment_count",
            "model_net_to_fluid_sum_W",
            "cfd_realized_net_to_fluid_sum_W",
            "model_minus_cfd_realized_net_sum_W",
            "max_abs_segment_net_residual_W",
            "diagnostic_result",
            "admissibility_status",
            "why_not_predictive",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "train_test_data_sufficiency.csv",
        train_rows,
        [
            "case_key",
            "display_label",
            "split_policy",
            "split_role",
            "can_fit_heat_loss_variant",
            "can_score_heat_loss_variant",
            "admission_status",
            "data_sufficiency_conclusion",
            "guardrail",
            "source_path",
        ],
    )
    write_csv(
        output_dir / "jin_vs_val_salt2_report_status.csv",
        val_status,
        ["evidence_item", "exists", "status", "answer", "source_path"],
    )
    write_csv(
        output_dir / "predictive_heat_loss_variant_plan.csv",
        plan_rows,
        [
            "step_id",
            "work_packet",
            "implementation_target",
            "required_inputs",
            "outputs",
            "rigor_gate",
            "source_paths",
            "guardrail",
        ],
    )
    write_csv(output_dir / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    write_json(output_dir / "summary.json", summary)
    (output_dir / "report_addendum.md").write_text(build_report_addendum(summary), encoding="utf-8")
    (output_dir / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
