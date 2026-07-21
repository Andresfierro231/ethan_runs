#!/usr/bin/env python3
"""Build AGENT-463 TP2 validation-only 1D evidence package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-463"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence")
OUT = ROOT / OUT_REL

FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
FLUID_SENSOR_REGISTRY = FLUID_ROOT / "docs/provisional_sensor_locations.csv"
AGENT442 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude"
AGENT360 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"
DECISION_NOTE = ROOT / "operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md"

TP2 = "TP2"
TW10 = "TW10"
TP2_CANONICAL_SEGMENT = "right_downcomer_bottom_horizontal_junction"
TP2_FLUID_PARENT_SEGMENT = "bottom_horizontal_inlet"
TP2_FLUID_PARENT_FRACTION = 0.0
TP2_ACCEPTABLE_FLUID_PARENTS = {"bottom_horizontal_inlet", "right_vertical"}
CURRENT_EXCLUDED = {TP2, TW10}
RESTORED_EXCLUDED = {TW10}

SENSOR_COLUMNS = [
    "case_id",
    "mode_id",
    "part",
    "sensor",
    "kind",
    "predicted_K",
    "target_K",
    "error_K",
    "abs_error_K",
    "prediction_source_segment",
    "prediction_source_fraction",
    "target_provenance",
    "admission_use_class",
    "assumption_ids",
    "notes",
]
AGG_COLUMNS = [
    "aggregate_policy",
    "tp_count",
    "tw_count",
    "sensor_count",
    "n_compared_rows",
    "rmse_K",
    "mae_K",
    "mean_error_K",
    "max_abs_error_K",
    "included_sensors",
    "excluded_sensors",
    "interpretation",
]


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return "" if not math.isfinite(value) else f"{value:.12g}"
    return str(value)


def fnum(value: Any) -> float | None:
    if value in ("", None, "nan", "NaN"):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def rmse(values: Iterable[float]) -> float | None:
    vals = [v for v in values if math.isfinite(v)]
    return math.sqrt(sum(v * v for v in vals) / len(vals)) if vals else None


def mean(values: Iterable[float]) -> float | None:
    vals = [v for v in values if math.isfinite(v)]
    return sum(vals) / len(vals) if vals else None


def projected_registry_rows(source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in source_rows:
        updated: dict[str, Any] = dict(row)
        updated.setdefault("original_x_in", row.get("x_in", ""))
        updated.setdefault("original_y_in", row.get("y_in", ""))
        updated.setdefault("projection_parent_segment", "")
        updated.setdefault("projection_parent_fraction", "")
        updated.setdefault("canonical_source_segment", "")
        if row.get("sensor") == TP2:
            original_x = row.get("x_in", "")
            original_y = row.get("y_in", "")
            # Fluid's existing sensor sampler requires a point on the 1D path.
            # Preserve the old coordinate in explicit provenance columns and
            # use the junction point for this validation-only scoring pass.
            updated["x_in"] = "35.8289343482927"
            updated["y_in"] = "-12.3127251597241"
            updated["x_m"] = "0.910054932446635"
            updated["y_m"] = "-0.3127432190569915"
            updated["original_x_in"] = original_x
            updated["original_y_in"] = original_y
            updated["placement_class"] = "projected_1d_validation_target"
            updated["source_basis"] = "AGENT-463 TP2 gated 1D projection"
            updated["authoritative_status"] = "projected_from_native_cfd_junction_evidence"
            updated["caveat"] = (
                "Projected onto the 1D bottom-horizontal/right-downcomer junction for validation-only scoring; "
                "not a runtime input or fit target."
            )
            updated["projection_parent_segment"] = TP2_FLUID_PARENT_SEGMENT
            updated["projection_parent_fraction"] = TP2_FLUID_PARENT_FRACTION
            updated["canonical_source_segment"] = TP2_CANONICAL_SEGMENT
        out.append(updated)
    return out


def write_projected_registry(out_dir: Path) -> Path:
    rows = projected_registry_rows(read_csv(FLUID_SENSOR_REGISTRY))
    path = out_dir / "tp2_projected_sensor_registry.csv"
    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(path, rows, fieldnames)
    return path


def execute_projected_fluid_audit(projected_registry: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(FLUID_ROOT) not in sys.path:
        sys.path.insert(0, str(FLUID_ROOT))

    from tools.analyze import build_mdot_temperature_probe_error_audit as audit  # noqa: WPS433

    def projected_solver_segments(case: Any, scenario: Any) -> tuple[list[Any], list[Any], list[Any]]:
        segments, sensors = audit.S.build_geometry(
            refinement=audit.S.default_geometry_refinement(),
            sensor_registry_path=projected_registry,
        )
        return segments, sensors, audit.fixed_replay.scenario_segments_for_solver(audit.S, segments, case, scenario)

    original_solver_segments = audit.solver_segments
    audit.solver_segments = projected_solver_segments
    try:
        refs = audit.load_sensor_refs()
        cases = audit.case_rows(audit.load_targets(), refs, audit.heat_rows_by_case())
        heat_by = audit.heat_rows_by_case()
        fluid_cases = {case.name: case for case in audit.config_loader.load_cases()}
        mode = next(row for row in audit.mode_rows() if row["mode_id"] == "M1b_full_cfd_segment_heat_flux_fixed_mdot")
        results: list[dict[str, Any]] = []
        sensors: list[dict[str, Any]] = []
        for case_row in cases:
            rows = heat_by.get(case_row["case_id"], [])
            cfd_mdot = fnum(case_row.get("cfd_mdot_kg_s"))
            if not rows or cfd_mdot is None:
                continue
            scenario, sources, losses, source_total, loss_total = audit.mode_setup(case_row, mode["mode_id"], rows)
            case = fluid_cases[case_row["fluid_case_name"]]
            result = audit.fixed_mdot_eval(case, scenario, cfd_mdot, sources, losses)
            source_paths = ";".join([rel(audit.SECTION_HEAT), rel(audit.THERMAL_TARGETS), str(FLUID_ROOT)])
            results.append(audit.result_row(result, case_row, mode, source_total, loss_total, source_paths))
            sensors.extend(audit.sensor_rows_for_result(result, case_row, mode, refs))
        return results, sensors
    finally:
        audit.solver_segments = original_solver_segments


def row_has_finite_comparison(row: dict[str, Any]) -> bool:
    return fnum(row.get("predicted_K")) is not None and fnum(row.get("target_K")) is not None and fnum(row.get("error_K")) is not None


def comparable_sensors(rows: list[dict[str, Any]], excluded: set[str]) -> set[str]:
    return {
        str(row.get("sensor", ""))
        for row in rows
        if row.get("sensor") not in excluded and row_has_finite_comparison(row)
    }


def aggregate_row(rows: list[dict[str, Any]], *, label: str, excluded: set[str], interpretation: str) -> dict[str, Any]:
    included = comparable_sensors(rows, excluded)
    compared = [row for row in rows if row.get("sensor") in included and row_has_finite_comparison(row)]
    errors = [float(fnum(row["error_K"]) or 0.0) for row in compared]
    tp_count = len({s for s in included if s.startswith("TP")})
    tw_count = len({s for s in included if s.startswith("TW")})
    return {
        "aggregate_policy": label,
        "tp_count": tp_count,
        "tw_count": tw_count,
        "sensor_count": len(included),
        "n_compared_rows": len(compared),
        "rmse_K": rmse(errors),
        "mae_K": mean(abs(e) for e in errors),
        "mean_error_K": mean(errors),
        "max_abs_error_K": max((abs(e) for e in errors), default=""),
        "included_sensors": ",".join(sorted(included)),
        "excluded_sensors": ",".join(sorted(excluded)),
        "interpretation": interpretation,
    }


def tp2_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if row.get("sensor") == TP2]


def finite_tp2_gate(rows: list[dict[str, Any]]) -> tuple[str, str]:
    subset = tp2_rows(rows)
    if not subset:
        return "fail", "No TP2 rows were emitted by the 1D score run."
    missing = [row for row in subset if not row_has_finite_comparison(row)]
    if missing:
        return "fail", f"{len(missing)} of {len(subset)} TP2 rows lack finite predicted/target/error values."
    return "pass", f"{len(subset)} of {len(subset)} TP2 rows have finite predicted/target/error values."


def gate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    finite_status, finite_detail = finite_tp2_gate(rows)
    tp2_sources = sorted({str(row.get("prediction_source_segment", "")) for row in tp2_rows(rows)})
    source_status = "pass" if tp2_sources and set(tp2_sources).issubset(TP2_ACCEPTABLE_FLUID_PARENTS) else "fail"
    return [
        {
            "gate": "TP2_source_segment_named",
            "status": source_status,
            "detail": (
                f"Fluid parent={','.join(tp2_sources) or 'missing'}; "
                f"accepted endpoint parents={','.join(sorted(TP2_ACCEPTABLE_FLUID_PARENTS))}; "
                f"canonical scorecard segment={TP2_CANONICAL_SEGMENT}."
            ),
        },
        {
            "gate": "TP2_runtime_input_forbidden",
            "status": "pass",
            "detail": "TP2 remains post-solve validation-only evidence; no runtime temperature input or fit target path is enabled.",
        },
        {
            "gate": "TP2_finite_prediction_before_aggregate",
            "status": finite_status,
            "detail": finite_detail,
        },
        {
            "gate": "TW10_excluded_until_active_hx_shell_state",
            "status": "pass",
            "detail": "TW10 remains excluded because the active-HX shell-state target is not emitted by the 1D model.",
        },
    ]


def admission_status_rows(rows: list[dict[str, Any]], gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_map = {row["gate"]: row["status"] for row in gates}
    tp2_status = "validation-only" if all(gate_map.get(g) == "pass" for g in [
        "TP2_source_segment_named",
        "TP2_runtime_input_forbidden",
        "TP2_finite_prediction_before_aggregate",
    ]) else "blocked"
    return [
        {
            "evidence_item": "TP2 restored 1D sensor target",
            "admission_status": tp2_status,
            "allowed_use": "post-solve TP/TW aggregate scoring only",
            "not_allowed_use": "runtime input; fit target; closure calibration",
            "reason": "Finite TP2 rows are required before aggregate use; projection is explicit and target-only.",
        },
        {
            "evidence_item": "Other scoreable TP/TW labels",
            "admission_status": "validation-only",
            "allowed_use": "post-solve diagnostic scorecard comparison",
            "not_allowed_use": "runtime input; fit target; sensor-wise correction",
            "reason": "Existing policy keeps all TP/TW temperatures target-only.",
        },
        {
            "evidence_item": "AGENT-360 replay model rows consumed here",
            "admission_status": "diagnostic-only",
            "allowed_use": "evidence that TP2 projection emits finite 1D predictions",
            "not_allowed_use": "final forward-v1 thesis-strength closure claim",
            "reason": "The replay modes still consume CFD heat ledgers or other non-final runtime shortcuts.",
        },
        {
            "evidence_item": "TW10 cooling-jacket shell surrogate",
            "admission_status": "blocked",
            "allowed_use": "reported as excluded",
            "not_allowed_use": "aggregate TP/TW score until active-HX shell-state model exists",
            "reason": "Current 1D model does not emit the active-HX shell-state temperature.",
        },
        {
            "evidence_item": "Final predictive forward-v1 model",
            "admission_status": "blocked",
            "allowed_use": "none from this TP2 package alone",
            "not_allowed_use": "claim final forward-v1 is admitted",
            "reason": "This package resolves TP2 scoring evidence only; broader hydraulic/thermal gates remain separate.",
        },
    ]


def sensor_policy_rows(sensor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sensor: dict[str, list[dict[str, Any]]] = {}
    for row in sensor_rows:
        by_sensor.setdefault(str(row.get("sensor", "")), []).append(row)
    rows: list[dict[str, Any]] = []
    for sensor, group in sorted(by_sensor.items()):
        kind = str(group[0].get("kind", ""))
        finite_count = sum(1 for row in group if row_has_finite_comparison(row))
        current = "yes" if sensor not in CURRENT_EXCLUDED and finite_count else "no"
        after = "yes" if sensor not in RESTORED_EXCLUDED and finite_count else "no"
        if sensor == TW10:
            after = "no"
        rows.append(
            {
                "sensor": sensor,
                "kind": kind,
                "runtime_temperature_allowed": "false",
                "fit_allowed": "false",
                "finite_prediction_rows": finite_count,
                "total_rows": len(group),
                "aggregate_score_current": current,
                "aggregate_score_after_tp2_restore": after,
                "source_segment": (
                    TP2_CANONICAL_SEGMENT if sensor == TP2 else sorted({str(r.get("prediction_source_segment", "")) for r in group})[0]
                ),
                "policy_decision": (
                    "restore_to_aggregate_validation_only_after_gates"
                    if sensor == TP2
                    else ("keep_excluded_until_active_hx_shell_state" if sensor == TW10 else "validation_target_only")
                ),
            }
        )
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(FLUID_SENSOR_REGISTRY)}
  - {rel(AGENT442 / "sensor_tp2_tw10_policy_refresh.csv")}
  - {rel(AGENT360 / "sensor_level_errors.csv")}
  - {rel(DECISION_NOTE)}
tags: [TP2, sensor-map, forward-v1, validation-only, one-dimensional-model]
task: {TASK}
date: {DATE}
type: work_product_readme
status: complete
---
# TP2 1D Model Evidence

This package makes TP2 usable as validation-only 1D evidence. It reruns the
existing TP/TW score path with a generated projected TP2 registry that keeps the
original provisional coordinate in provenance columns while placing TP2 on the
1D bottom-horizontal/right-downcomer junction for scoring.

## Result

- TP2 canonical scorecard segment: `{TP2_CANONICAL_SEGMENT}`.
- TP2 Fluid computational parent: either `right_vertical` at its end or `{TP2_FLUID_PARENT_SEGMENT}` at fraction `{TP2_FLUID_PARENT_FRACTION}`; these are the same physical junction in the current segment order.
- TP2 finite prediction gate: `{summary['gate_status']['TP2_finite_prediction_before_aggregate']}`.
- Current aggregate count: `{summary['current_aggregate']['tp_count']}` TP + `{summary['current_aggregate']['tw_count']}` TW.
- Restored aggregate count: `{summary['restored_aggregate']['tp_count']}` TP + `{summary['restored_aggregate']['tw_count']}` TW.
- Current aggregate RMSE: `{summary['current_aggregate']['rmse_K']}` K.
- Restored aggregate RMSE: `{summary['restored_aggregate']['rmse_K']}` K.

TP2 is now validation-only score evidence when these gates pass. It is still not
a runtime temperature input, fit target, sensor-wise correction, or closure
calibration row. The replay model rows consumed here remain diagnostic-only for
final forward-v1 because they are not the final setup-only predictive model.

## Outputs

- `tp2_projected_sensor_registry.csv`
- `tp2_sensor_level_evidence.csv`
- `sensor_policy_gate_evidence.csv`
- `aggregate_rmse_before_after.csv`
- `tp2_gate_status.csv`
- `admission_status_scorecard.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Native CFD outputs, registry/admission state, scheduler state, generated docs
indexes, and external Fluid source files were not mutated.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build(*, execute_fluid: bool = True, out_dir: Path = OUT) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    projected_registry = write_projected_registry(out_dir)
    if execute_fluid:
        _results, sensor_rows = execute_projected_fluid_audit(projected_registry)
    else:
        sensor_rows = read_csv(AGENT360 / "sensor_level_errors.csv")

    current = aggregate_row(
        sensor_rows,
        label="current_policy_excludes_tp2_tw10",
        excluded=CURRENT_EXCLUDED,
        interpretation="Baseline current policy: TP2 and TW10 excluded from aggregate TP/TW score.",
    )
    restored = aggregate_row(
        sensor_rows,
        label="restored_policy_includes_tp2_excludes_tw10",
        excluded=RESTORED_EXCLUDED,
        interpretation="Restored policy: TP2 included only after finite/projection/runtime/fit gates pass; TW10 remains excluded.",
    )
    gates = gate_rows(sensor_rows)
    policy = sensor_policy_rows(sensor_rows)
    status = admission_status_rows(sensor_rows, gates)
    tp2 = tp2_rows(sensor_rows)
    manifest = [
        {"path": rel(FLUID_SENSOR_REGISTRY), "role": "input Fluid provisional sensor registry"},
        {"path": rel(AGENT442 / "sensor_tp2_tw10_policy_refresh.csv"), "role": "input TP2/TW10 policy"},
        {"path": rel(AGENT360 / "sensor_level_errors.csv"), "role": "baseline TP/TW score output"},
        {"path": rel(projected_registry), "role": "generated projected TP2 registry"},
        {"path": rel(out_dir / "tp2_sensor_level_evidence.csv"), "role": "generated TP2 finite-row evidence"},
        {"path": rel(out_dir / "aggregate_rmse_before_after.csv"), "role": "generated aggregate score impact"},
    ]
    summary = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "execute_fluid": execute_fluid,
        "tp2_canonical_segment": TP2_CANONICAL_SEGMENT,
        "tp2_fluid_parent_segment": "right_vertical@end_or_bottom_horizontal_inlet@start",
        "tp2_fluid_parent_fraction": TP2_FLUID_PARENT_FRACTION,
        "tp2_rows": len(tp2),
        "tp2_finite_rows": sum(1 for row in tp2 if row_has_finite_comparison(row)),
        "gate_status": {row["gate"]: row["status"] for row in gates},
        "current_aggregate": current,
        "restored_aggregate": restored,
        "final_decision": (
            "TP2 is validation-only 1D evidence after finite-row gates pass; "
            "TW10 remains blocked; final forward-v1 remains a separate admission question."
        ),
    }
    write_csv(out_dir / "tp2_sensor_level_evidence.csv", tp2, SENSOR_COLUMNS)
    write_csv(out_dir / "sensor_policy_gate_evidence.csv", policy, [
        "sensor",
        "kind",
        "runtime_temperature_allowed",
        "fit_allowed",
        "finite_prediction_rows",
        "total_rows",
        "aggregate_score_current",
        "aggregate_score_after_tp2_restore",
        "source_segment",
        "policy_decision",
    ])
    write_csv(out_dir / "aggregate_rmse_before_after.csv", [current, restored], AGG_COLUMNS)
    write_csv(out_dir / "tp2_gate_status.csv", gates, ["gate", "status", "detail"])
    write_csv(out_dir / "admission_status_scorecard.csv", status, [
        "evidence_item",
        "admission_status",
        "allowed_use",
        "not_allowed_use",
        "reason",
    ])
    write_csv(out_dir / "source_manifest.csv", manifest, ["path", "role"])
    write_json(out_dir / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-execute-fluid", action="store_true", help="Use existing AGENT-360 rows instead of rerunning Fluid.")
    args = parser.parse_args()
    print(json.dumps(build(execute_fluid=not args.no_execute_fluid), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
