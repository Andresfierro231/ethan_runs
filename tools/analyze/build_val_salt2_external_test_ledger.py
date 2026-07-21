#!/usr/bin/env python3
"""Build the val_salt2 external-test ledger from admitted July 17 evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "AGENT-486"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger")
OUT = ROOT / OUT_REL

AGENT483_DIR = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock"
PATCH_HEAT = AGENT483_DIR / "val_salt2_patch_heat_ledger.csv"
SECTION_HEAT = AGENT483_DIR / "val_salt2_section_reconciliation.csv"
JUNCTION_SPLIT = AGENT483_DIR / "val_salt2_junction_split_heat_ledger.csv"
TRAINING_GATE = AGENT483_DIR / "val_salt2_training_admission_gate.csv"
PRESSURE_MAP = AGENT483_DIR / "val_salt2_pressure_map.csv"
CORNER_K = AGENT483_DIR / "pressure_corner_k_admission_table.csv"
AGENT483_SUMMARY = AGENT483_DIR / "summary.json"

SENSOR_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_hydraulic_unblock_plan_execution/sensor_map_policy_refresh.csv"
)
SENSOR_POLICY_CLOSEOUT = (
    ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_plan_implementation_closeout/verified_artifacts.csv"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def add_external_policy(row: dict[str, str], target_family: str) -> dict[str, Any]:
    copied: dict[str, Any] = dict(row)
    copied["target_family"] = target_family
    copied["external_test_only"] = "yes"
    copied["training_input_allowed"] = "no"
    copied["fit_allowed"] = "no"
    copied["model_selection_allowed"] = "no"
    copied["runtime_input_allowed"] = "no"
    copied["runtime_wallHeatFlux_allowed"] = "no"
    copied["policy_status"] = "external_test_target_only_not_runtime_input"
    return copied


def external_patch_heat_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [add_external_policy(row, "patch_wall_heat") for row in rows if row.get("case_key") == "val_salt2"]


def external_section_heat_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("case_key") != "val_salt2":
            continue
        copied = add_external_policy(row, "section_heat")
        copied["ledger_value_W"] = row.get("latest_section_ledger_q_net_w", "")
        copied["residual_check_W"] = row.get("latest_residual_patch_minus_ledger_w", "")
        out.append(copied)
    return out


def external_junction_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("case_key") != "val_salt2":
            continue
        if row.get("physical_junction_bucket") == "case_total_check" or row.get("model_use") == "closure_check":
            continue
        copied = add_external_policy(row, "junction_stub_heat")
        copied["ledger_value_W"] = row.get("realized_wallHeatFlux_W", "")
        copied["loss_positive_W"] = row.get("realized_external_loss_positive_W", "")
        out.append(copied)
    return out


def external_pressure_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("case_key") != "val_salt2":
            continue
        out.append(
            {
                "case_key": "val_salt2",
                "target_type": "pressure_streamwise_map",
                "target_id": row.get("station_label", ""),
                "one_d_component_segments": row.get("one_d_component_segments", ""),
                "physical_location_label": row.get("physical_location_label", ""),
                "loop_order_index": row.get("loop_order_index", ""),
                "target_value": row.get("relative_p_from_case_loop_start_Pa", ""),
                "target_units": "Pa relative to case loop start",
                "secondary_value": row.get("relative_p_rgh_from_case_loop_start_Pa", ""),
                "secondary_units": "p_rgh Pa relative to case loop start",
                "mapping_status": row.get("mapping_status", ""),
                "external_test_only": "yes",
                "training_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "policy_status": "external_test_target_only_not_runtime_input",
                "source_path": row.get("source_path", rel(PRESSURE_MAP)),
            }
        )
    return out


def external_thermal_target_rows(
    section_rows: list[dict[str, Any]], junction_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in section_rows:
        out.append(
            {
                "case_key": "val_salt2",
                "target_type": "section_heat",
                "target_id": row.get("section_key", ""),
                "one_d_component_segments": row.get("section_key", ""),
                "physical_location_label": row.get("section_label", ""),
                "target_value": row.get("latest_section_ledger_q_net_w", ""),
                "target_units": "W, positive net into fluid",
                "secondary_value": row.get("latest_patch_sum_q_net_w", ""),
                "secondary_units": "W patch sum",
                "mapping_status": row.get("reconciliation_status", ""),
                "external_test_only": "yes",
                "training_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "policy_status": "external_test_target_only_not_runtime_input",
                "source_path": row.get("source_paths", rel(SECTION_HEAT)),
            }
        )
    for row in junction_rows:
        out.append(
            {
                "case_key": "val_salt2",
                "target_type": "junction_stub_heat",
                "target_id": row.get("physical_junction_bucket", ""),
                "one_d_component_segments": "junction_stub_connector_group",
                "physical_location_label": row.get("physical_junction_label", ""),
                "target_value": row.get("realized_wallHeatFlux_W", ""),
                "target_units": "W, positive net into fluid",
                "secondary_value": row.get("realized_external_loss_positive_W", ""),
                "secondary_units": "W external loss positive",
                "mapping_status": "junction_split_closes_to_case_junction_loss",
                "external_test_only": "yes",
                "training_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "policy_status": "external_test_target_only_not_runtime_input",
                "source_path": row.get("source_path", rel(JUNCTION_SPLIT)),
            }
        )
    return out


def external_sensor_target_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "case_key": "val_salt2",
                "target_type": "sensor_temperature_policy",
                "target_id": row.get("sensor", ""),
                "kind": row.get("kind", ""),
                "one_d_component_segments": row.get("source_segments", ""),
                "target_value": "",
                "target_units": "K",
                "mapping_status": row.get("policy", ""),
                "case_specific_numeric_target_available_here": "no",
                "external_test_only": "yes",
                "training_input_allowed": "no",
                "fit_allowed": "no",
                "model_selection_allowed": "no",
                "runtime_input_allowed": "no",
                "score_allowed": "yes" if row.get("policy") != "coordinate_upgrade_needed" else "no",
                "policy_status": "score_validation_policy_only_no_case_specific_temperature_join",
                "source_path": rel(SENSOR_POLICY),
            }
        )
    return out


def runtime_input_audit() -> list[dict[str, str]]:
    return [
        {
            "check": "val_salt2_used_for_training_fit",
            "status": "pass_forbidden",
            "policy": "val_salt2 remains external-test evidence unless a later explicit reclassification package changes the split.",
        },
        {
            "check": "wallHeatFlux_or_section_heat_as_runtime_input",
            "status": "pass_forbidden",
            "policy": "Patch, section, and junction heat are post-solve targets/diagnostics only.",
        },
        {
            "check": "pressure_map_as_runtime_input",
            "status": "pass_forbidden",
            "policy": "Streamwise pressure rows are external-test targets and mapping diagnostics, not runtime predictors.",
        },
        {
            "check": "sensor_temperature_as_runtime_input",
            "status": "pass_forbidden",
            "policy": "TP/TW sensor rows are validation/scorecard policy targets only.",
        },
        {
            "check": "model_selection_on_val_salt2",
            "status": "pass_forbidden",
            "policy": "Do not select model form or tune parameters against val_salt2 external-test errors.",
        },
        {
            "check": "native_solver_output_mutation",
            "status": "pass_no_mutation",
            "policy": "This ledger normalizes AGENT-483/AGENT-393 artifacts and does not touch native CFD outputs.",
        },
    ]


def admission_decision(summary: dict[str, Any], section_rows: list[dict[str, Any]], junction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_residual = max(abs(fnum(row.get("latest_residual_patch_minus_ledger_w"))) for row in section_rows)
    junction_loss = sum(fnum(row.get("realized_external_loss_positive_W")) for row in junction_rows)
    return [
        {
            "case_key": "val_salt2",
            "external_test_only": "yes",
            "training_input_allowed": "no",
            "fit_allowed": "no",
            "model_selection_allowed": "no",
            "runtime_wallHeatFlux_allowed": "no",
            "admission_status": "external_test_ledger_ready_training_forbidden",
            "patch_rows": summary.get("val_patch_rows", ""),
            "junction_patch_rows": summary.get("val_junction_patch_rows", ""),
            "junction_split_rows": len(junction_rows),
            "junction_loss_positive_W": f"{junction_loss:.10f}",
            "max_section_latest_residual_W": f"{max_residual:.12g}",
            "guardrail": "May be used as main external-test evidence and training-quality audit artifact, not as training input.",
            "source_paths": ";".join(
                [
                    rel(PATCH_HEAT),
                    rel(SECTION_HEAT),
                    rel(JUNCTION_SPLIT),
                    rel(TRAINING_GATE),
                    rel(PRESSURE_MAP),
                    rel(SENSOR_POLICY),
                ]
            ),
        }
    ]


def build_source_manifest() -> list[dict[str, str]]:
    return [
        {"artifact": "agent483_patch_heat_ledger", "path": rel(PATCH_HEAT), "use": "primary val_salt2 patch heat external targets"},
        {"artifact": "agent483_section_reconciliation", "path": rel(SECTION_HEAT), "use": "section heat and closure residuals"},
        {"artifact": "agent483_junction_split", "path": rel(JUNCTION_SPLIT), "use": "junction/stub heat split targets"},
        {"artifact": "agent483_training_gate", "path": rel(TRAINING_GATE), "use": "external-test policy guardrail"},
        {"artifact": "agent483_pressure_map", "path": rel(PRESSURE_MAP), "use": "streamwise pressure map target rows"},
        {"artifact": "agent483_corner_k_table", "path": rel(CORNER_K), "use": "pressure corner K remains diagnostic, not admitted"},
        {"artifact": "agent483_summary", "path": rel(AGENT483_SUMMARY), "use": "row counts and residual summary"},
        {"artifact": "agent393_sensor_policy", "path": rel(SENSOR_POLICY), "use": "TP/TW score/validation policy rows"},
        {"artifact": "agent393_closeout", "path": rel(SENSOR_POLICY_CLOSEOUT), "use": "sensor policy provenance verification"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(PATCH_HEAT)}
  - {rel(SECTION_HEAT)}
  - {rel(JUNCTION_SPLIT)}
  - {rel(PRESSURE_MAP)}
  - {rel(SENSOR_POLICY)}
tags: [val_salt2, external-test, ledger, heat-audit, pressure-map, sensors]
related:
  - tools/analyze/build_val_salt2_external_test_ledger.py
task: {TASK}
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 External-Test Ledger

This package normalizes AGENT-483 `val_salt2` heat and pressure evidence into a
single external-test ledger. It also carries AGENT-393 sensor policy rows so
TP/TW targets are visible to downstream scorecards without treating sensor
temperatures as runtime inputs.

## Result

- Patch heat rows: `{summary['patch_heat_rows']}`.
- Section heat rows: `{summary['section_heat_rows']}`.
- Junction split rows: `{summary['junction_split_rows']}`.
- Pressure target rows: `{summary['pressure_target_rows']}`.
- Sensor policy target rows: `{summary['sensor_policy_rows']}`.
- Fit-admitted rows: `{summary['fit_allowed_rows']}`.
- Runtime heat-input rows admitted: `{summary['runtime_heat_input_allowed_rows']}`.

`val_salt2` is main external-test evidence and a training-quality audit artifact.
It is not a training, fitting, model-selection, or runtime wall-heat input.
Sensor rows are policy targets only here; this package does not claim a
case-specific val_salt2 numeric sensor-temperature join.

## Files

- `val_salt2_external_patch_heat_ledger.csv`
- `val_salt2_external_section_heat_ledger.csv`
- `val_salt2_external_junction_split.csv`
- `val_salt2_external_pressure_thermal_sensor_targets.csv`
- `val_salt2_external_runtime_input_audit.csv`
- `val_salt2_external_admission_decision.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(readme)


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    agent483_summary = json.loads(AGENT483_SUMMARY.read_text())
    patch_rows = external_patch_heat_rows(read_csv(PATCH_HEAT))
    section_rows = external_section_heat_rows(read_csv(SECTION_HEAT))
    junction_rows = external_junction_rows(read_csv(JUNCTION_SPLIT))
    pressure_targets = external_pressure_rows(read_csv(PRESSURE_MAP))
    thermal_targets = external_thermal_target_rows(section_rows, junction_rows)
    sensor_targets = external_sensor_target_rows(read_csv(SENSOR_POLICY))
    all_targets = pressure_targets + thermal_targets + sensor_targets
    audit_rows = runtime_input_audit()
    decisions = admission_decision(agent483_summary, section_rows, junction_rows)

    write_csv(OUT / "val_salt2_external_patch_heat_ledger.csv", patch_rows)
    write_csv(OUT / "val_salt2_external_section_heat_ledger.csv", section_rows)
    write_csv(OUT / "val_salt2_external_junction_split.csv", junction_rows)
    write_csv(OUT / "val_salt2_external_pressure_thermal_sensor_targets.csv", all_targets)
    write_csv(OUT / "val_salt2_external_runtime_input_audit.csv", audit_rows)
    write_csv(OUT / "val_salt2_external_admission_decision.csv", decisions)
    write_csv(OUT / "source_manifest.csv", build_source_manifest())

    target_counts = Counter(row["target_type"] for row in all_targets)
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "output_dir": rel(OUT),
        "patch_heat_rows": len(patch_rows),
        "section_heat_rows": len(section_rows),
        "junction_split_rows": len(junction_rows),
        "pressure_target_rows": len(pressure_targets),
        "thermal_target_rows": len(thermal_targets),
        "sensor_policy_rows": len(sensor_targets),
        "all_target_rows": len(all_targets),
        "target_type_counts": dict(target_counts),
        "fit_allowed_rows": sum(row.get("fit_allowed") == "yes" for row in patch_rows + section_rows + junction_rows),
        "runtime_heat_input_allowed_rows": sum(
            row.get("runtime_wallHeatFlux_allowed") == "yes" for row in patch_rows + section_rows + junction_rows
        ),
        "junction_loss_positive_W": decisions[0]["junction_loss_positive_W"],
        "max_section_latest_residual_W": decisions[0]["max_section_latest_residual_W"],
        "val_salt2_external_test_ledger_ready": "yes",
        "val_salt2_training_input_allowed": "no",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
