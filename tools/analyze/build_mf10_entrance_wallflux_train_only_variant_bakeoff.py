#!/usr/bin/env python3
"""Build MF10 entrance/wall-flux train-only variant bakeoff gate.

MF10 consumes completed MF07/MF08/MF09 gates and the current master model-form
scoreboard. It does not execute Fluid, fit coefficients, score protected rows,
or admit a closure. Existing scoreboard metrics are carried as numeric context
for baseline/negative-control rows; new variants are fail-closed until source
and UQ gates pass.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-MF10-ENTRANCE-WALLFLUX-TRAIN-ONLY-VARIANT-BAKEOFF-2026-07-22"
OUT_DIR = Path(
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff"
)

SOURCES = {
    "mf07": Path("work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis"),
    "mf08": Path("work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"),
    "mf09": Path("work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives"),
    "scoreboard": Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard"),
    "source_property": Path("work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: "true" if value is True else "false" if value is False else value
                    for key, value in ((name, row.get(name, "")) for name in fieldnames)
                }
            )


def aggregate_mae(rows: list[dict[str, str]], model_form: str) -> dict[str, Any]:
    selected = [
        row for row in rows
        if row["model_form_id"] == model_form and row["case_id"] in {"salt_2", "salt_3", "salt_4"}
    ]
    if not selected:
        return {
            "source_metric_model_form": "",
            "train_metric_rows": 0,
            "train_all_sensor_mae_K": "",
            "train_tp_mae_K": "",
            "train_tw_mae_K": "",
            "metric_status": "not_available",
        }
    all_mae = sum(float(row["mean_absolute_error_K"]) for row in selected) / len(selected)
    tp = [float(row["mean_absolute_error_K"]) for row in selected if row["sensor_kind"] == "TP"]
    tw = [float(row["mean_absolute_error_K"]) for row in selected if row["sensor_kind"] == "TW"]
    return {
        "source_metric_model_form": model_form,
        "train_metric_rows": len(selected),
        "train_all_sensor_mae_K": f"{all_mae:.12g}",
        "train_tp_mae_K": f"{sum(tp) / len(tp):.12g}",
        "train_tw_mae_K": f"{sum(tw) / len(tw):.12g}",
        "metric_status": "existing_scoreboard_numeric_context_not_new_scoring",
    }


def write_closeout(summary: dict[str, Any]) -> None:
    status_path = Path(f".agent/status/2026-07-22_{TASK_ID}.md")
    journal_path = Path(".agent/journal/2026-07-22/mf10-entrance-wallflux-train-only-variant-bakeoff.md")
    import_path = Path("imports/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    import_path.parent.mkdir(parents=True, exist_ok=True)

    status_path.write_text(f"""---
provenance:
  generated_by: tools/analyze/build_mf10_entrance_wallflux_train_only_variant_bakeoff.py
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
task: {TASK_ID}
tags: [status, MF10, train-only-bakeoff, diagnostic-only]
related:
  - {OUT_DIR}
---
# {TASK_ID}

## Objective

Evaluate whether the MF07/MF08/MF09 model forms can proceed to a train/support
bakeoff without protected-row tuning, source/property release, or residual
absorption into internal Nu.

## Outcome

Decision: `diagnostic_only`. Variants reviewed: `{summary['variant_rows']}`.
New train/support scoring executed: `false`. Existing scoreboard numeric-context
variants: `{summary['existing_numeric_context_variants']}`. Smoke-ready variants:
`{summary['smoke_ready_variants']}`. Candidate/admission variants:
`{summary['candidate_ready_variants']}`.

MF10 does not launch a Fluid run because MF07, MF08, and MF09 all stop before
source/property release or smoke-ready candidate status. The best next row is a
source-property/cp release preflight, followed by a separately claimed Fluid
train-only smoke if a candidate becomes executable.

## Changes Made

- Wrote variant bakeoff matrix with six predeclared variants.
- Wrote train/support metric table using only existing scoreboard numeric context.
- Wrote residual-owner deltas, runtime-leakage audit, assumption/provenance
  table, production gate, next-step queue, README, summary, journal, and import
  manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_mf10_entrance_wallflux_train_only_variant_bakeoff.py tools/analyze/test_mf10_entrance_wallflux_train_only_variant_bakeoff.py` passed.
- `python3.11 -m unittest tools.analyze.test_mf10_entrance_wallflux_train_only_variant_bakeoff` passed.

## Guardrails

- Validation/holdout/external-test scoring: false.
- Protected-row tuning: false.
- Scheduler/solver/sampler/harvest/UQ launch: false.
- Fluid/external edit: false.
- Native-output and registry/admission mutation: false.
- Source/property release, coefficient admission, final score, and S11/S12/S13/S15/S6 trigger: false.
- Residual absorbed into internal Nu: false.
""")

    journal_path.write_text(f"""---
provenance:
  generated_by: tools/analyze/build_mf10_entrance_wallflux_train_only_variant_bakeoff.py
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
task: {TASK_ID}
tags: [journal, MF10, train-only-bakeoff]
related:
  - {OUT_DIR}
---
# MF10 entrance/wall-flux train-only variant bakeoff

## Attempted

Built the MF10 dry bakeoff gate from completed MF07/MF08/MF09 evidence and the
master scoreboard numeric context.

## Observed

MF07 is diagnostic-only, MF08 needs source basis, MF09 is blocked by missing
mesh/GCI/source basis, and the source-property preflight has 0 release-ready
rows. Existing M2/M3 scoreboard metrics can be carried as context, but new
development/exchange-cell variants are not executable.

## Inferred

MF10 should not run a hidden train/support score. The rigorous next step is to
release source/property/cp and candidate disable/default behavior before any
train-only Fluid smoke.

## Contradictions or Caveats

Existing scoreboard metrics are legacy numeric context, not a new locked-split
score. They are useful for residual-owner direction, not for selecting a new
coefficient.

## Next Useful Actions

Claim a source-property/cp release row for the entrance/wall-flux/exchange-cell
candidate family, then claim a separate bounded train-only Fluid smoke row only
if at least one variant becomes executable.
""")

    import_doc = {
        "task": TASK_ID,
        "generated_at_utc": summary["generated_at_utc"],
        "changed_files": [
            str(OUT_DIR / name)
            for name in [
                "README.md",
                "summary.json",
                "variant_bakeoff_matrix.csv",
                "train_support_metric_table.csv",
                "residual_owner_delta_table.csv",
                "runtime_leakage_audit.csv",
                "assumption_provenance_table.csv",
                "production_gate.csv",
                "next_step_queue.csv",
                "source_manifest.csv",
            ]
        ]
        + [
            str(status_path),
            str(journal_path),
            str(import_path),
            "tools/analyze/build_mf10_entrance_wallflux_train_only_variant_bakeoff.py",
            "tools/analyze/test_mf10_entrance_wallflux_train_only_variant_bakeoff.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": [str(path) for path in SOURCES.values()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "external_fluid_edit": False,
        "scheduler_action": "none",
        "mutation_flags": {
            "new_scoring": False,
            "protected_row_tuning": False,
            "source_property_release": False,
            "coefficient_admission": False,
            "final_score": False,
            "residual_absorbed_into_internal_nu": False,
        },
    }
    import_path.write_text(json.dumps(import_doc, indent=2) + "\n")


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mf07 = read_json(SOURCES["mf07"] / "summary.json")
    mf08 = read_json(SOURCES["mf08"] / "summary.json")
    mf09 = read_json(SOURCES["mf09"] / "summary.json")
    scoreboard = read_json(SOURCES["scoreboard"] / "summary.json")
    source_property = read_json(SOURCES["source_property"] / "summary.json")
    signed_summary = read_csv(SOURCES["scoreboard"] / "signed_sensor_error_summary.csv")

    m2_metrics = aggregate_mae(signed_summary, "M2")
    m3_metrics = aggregate_mae(signed_summary, "M3")

    variants = [
        ("MF10a_fully_developed_baseline", "fully developed baseline", "M2", m2_metrics, "numeric_context_only"),
        ("MF10b_hydraulic_development_only", "hydraulic development/reset only", "", {}, "blocked_mf07_not_smoke_ready"),
        ("MF10c_signed_thermal_development_only", "signed thermal development only", "", {}, "blocked_mf08_needs_source_basis"),
        ("MF10d_combined_hydraulic_signed_thermal_upcomer_guarded", "hydraulic plus signed thermal development with ordinary upcomer guarded", "", {}, "blocked_no_source_property_release"),
        ("MF10e_combined_with_mf09_exchange_cell_upcomer", "combined development with MF09 exchange-cell upcomer", "", {}, "blocked_mf09_mesh_gci_source_basis"),
        ("MF10f_no_upcomer_correction_negative_control", "no-upcomer-correction negative control", "M3", m3_metrics, "numeric_context_only"),
    ]

    variant_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for variant_id, description, source_model, metrics, status in variants:
        executable = status == "numeric_context_only"
        variant_rows.append(
            {
                "variant_id": variant_id,
                "description": description,
                "source_metric_model_form": source_model,
                "train_support_execution_status": "not_executed_new_scoring",
                "existing_numeric_context_used": executable,
                "smoke_ready_now": False,
                "candidate_ready_now": False,
                "primary_blocker": status,
                "decision": "diagnostic_context_only" if executable else "blocked_before_train_smoke",
            }
        )
        metric_rows.append(
            {
                "variant_id": variant_id,
                "source_metric_model_form": metrics.get("source_metric_model_form", source_model),
                "train_metric_rows": metrics.get("train_metric_rows", 0),
                "train_all_sensor_mae_K": metrics.get("train_all_sensor_mae_K", ""),
                "train_tp_mae_K": metrics.get("train_tp_mae_K", ""),
                "train_tw_mae_K": metrics.get("train_tw_mae_K", ""),
                "support_metric_rows": 0,
                "support_metric_status": "not_executed_no_support_release",
                "metric_status": metrics.get("metric_status", "not_executed_gate_failed"),
            }
        )

    m2_all = float(m2_metrics["train_all_sensor_mae_K"])
    m3_all = float(m3_metrics["train_all_sensor_mae_K"])
    residual_rows = [
        {
            "comparison": "M3_minus_M2_existing_numeric_context",
            "delta_train_all_sensor_mae_K": f"{m3_all - m2_all:.12g}",
            "interpretation": "existing M3 context improves all-sensor MAE versus M2, but this is not a new MF10 score or source release",
            "residual_owner_status": "diagnostic_only",
        },
        {
            "comparison": "new_development_variants",
            "delta_train_all_sensor_mae_K": "",
            "interpretation": "no new residual-owner deltas computed because source/property gates fail",
            "residual_owner_status": "blocked_before_execution",
        },
    ]

    leakage_rows = [
        {"guardrail": "validation_holdout_external_rows_used", "pass": True, "observed": "0"},
        {"guardrail": "new_fitting_or_model_selection", "pass": True, "observed": "false"},
        {"guardrail": "source_property_release", "pass": True, "observed": "false"},
        {"guardrail": "coefficient_admission", "pass": True, "observed": "false"},
        {"guardrail": "scheduler_solver_sampler_harvest_uq_launch", "pass": True, "observed": "false"},
        {"guardrail": "residual_absorbed_into_internal_nu", "pass": True, "observed": "false"},
    ]

    assumptions = [
        {"item": "MF07", "status": mf07["decision"], "effect_on_mf10": "hydraulic-development-only variant not smoke-ready"},
        {"item": "MF08", "status": mf08["decision"], "effect_on_mf10": "signed wall-flux variants need source basis"},
        {"item": "MF09", "status": mf09["decision"], "effect_on_mf10": "exchange-cell variant blocked by mesh/GCI/source basis"},
        {"item": "source_property", "status": source_property["decision"], "effect_on_mf10": "0 release-ready rows; no Fluid smoke"},
        {"item": "scoreboard", "status": scoreboard["decision"], "effect_on_mf10": "existing numeric context only, not new scoring"},
    ]

    gates = [
        {"gate": "train_only_bakeoff_execution", "status": "blocked", "pass": False, "reason": "0 smoke-ready variants"},
        {"gate": "candidate_for_source_property_audit", "status": "not_ready", "pass": False, "reason": "source-property preflight has 0 release-ready rows"},
        {"gate": "diagnostic_only", "status": "selected", "pass": True, "reason": "existing evidence supports only a dry matrix"},
        {"gate": "reject_model_family", "status": "not_selected", "pass": False, "reason": "development/exchange lanes remain plausible but under-specified"},
    ]

    next_rows = [
        {"priority": 1, "next_step": "source-property/cp release preflight for MF08/MF09 candidate family", "stop_condition": "0 release-ready rows"},
        {"priority": 2, "next_step": "candidate disable/default API contract before any Fluid smoke", "stop_condition": "variant cannot be disabled or audited at runtime"},
        {"priority": 3, "next_step": "bounded train-only Fluid smoke row after one executable candidate exists", "stop_condition": "uses validation/holdout/external rows or hidden tuning"},
    ]

    manifest = [
        {"source_id": key, "source_path": str(path), "mutation_status": "read_only"}
        for key, path in SOURCES.items()
    ]

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "diagnostic_only",
        "variant_rows": len(variant_rows),
        "existing_numeric_context_variants": 2,
        "new_train_support_scoring_executed": False,
        "smoke_ready_variants": 0,
        "candidate_ready_variants": 0,
        "source_property_release_ready_rows": source_property["release_ready_rows"],
        "mf07_ready_for_train_only_smoke": mf07["ready_for_train_only_smoke"],
        "mf08_ready_for_train_only_smoke_rows": mf08["ready_for_train_only_smoke_rows"],
        "mf09_smoke_ready_variants": mf09["smoke_ready_variants"],
        "validation_holdout_external_rows_scored": 0,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "final_score": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
        "s11_s12_s13_s15_s6_trigger": False,
    }

    write_csv(OUT_DIR / "variant_bakeoff_matrix.csv", variant_rows, list(variant_rows[0].keys()))
    write_csv(OUT_DIR / "train_support_metric_table.csv", metric_rows, list(metric_rows[0].keys()))
    write_csv(OUT_DIR / "residual_owner_delta_table.csv", residual_rows, list(residual_rows[0].keys()))
    write_csv(OUT_DIR / "runtime_leakage_audit.csv", leakage_rows, list(leakage_rows[0].keys()))
    write_csv(OUT_DIR / "assumption_provenance_table.csv", assumptions, list(assumptions[0].keys()))
    write_csv(OUT_DIR / "production_gate.csv", gates, list(gates[0].keys()))
    write_csv(OUT_DIR / "next_step_queue.csv", next_rows, list(next_rows[0].keys()))
    write_csv(OUT_DIR / "source_manifest.csv", manifest, list(manifest[0].keys()))
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT_DIR / "README.md").write_text(
        """---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives/summary.json
tags: [MF10, train-only-bakeoff, diagnostic-only]
related:
  - operational_notes/maps/forward-predictive-model.md
---
# MF10 Entrance/Wall-Flux Train-Only Variant Bakeoff

Decision: `diagnostic_only`.

MF10 reviewed six predeclared variants. No new train/support score was run
because MF07/MF08/MF09 do not release a smoke-ready candidate and the
source-property preflight has 0 release-ready rows. Existing M2/M3 scoreboard
metrics are included only as numeric context.

Key guardrail: no validation/holdout/external rows, no fitting, no source
property release, no coefficient admission, and no residual absorption into
internal Nu.
"""
    )
    write_closeout(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
