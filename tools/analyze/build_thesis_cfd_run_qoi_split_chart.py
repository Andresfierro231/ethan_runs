#!/usr/bin/env python3
"""Build thesis CSV charts of CFD split rows versus mdot, TP, and TW QoIs."""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-THESIS-CFD-RUN-QOI-SPLIT-CHART-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart"

WINDOW_STATS = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_salt14_postprocessing_inventory_model_form_package/"
    "salt14_postprocessing_window_stats.csv"
)
SALT1_STOPPED = ROOT / (
    "work_products/2026-07/2026-07-13/"
    "2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv"
)
SALT1_UNCERT = ROOT / (
    "work_products/2026-07/2026-07-13/"
    "2026-07-13_time_series_uncertainty_story/screened_out_not_steady_or_live.csv"
)
LEGAL_USE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix/case_split_legal_use_table.csv"
)
PM5_SPLIT = ROOT / (
    "work_products/2026-07/2026-07-14/"
    "2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv"
)
SENSOR_REFERENCE = ROOT / (
    "reports/2026-07/2026-07-01/"
    "2026-07-01_local_1d_closure_bakeoff_refresh/"
    "defended_full_coverage_surface/cfd_sensor_reference.csv"
)
TRAINING_ROSTER = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_model_form_scoreboard_training_roster/"
    "canonical_train_validation_holdout_plan.csv"
)


@dataclass(frozen=True)
class CaseSpec:
    case_key: str
    display_name: str
    source_id: str
    split_group: str
    split_subrole: str
    q_ratio: str
    source_basis: str
    score_allowed_after_freeze: bool
    coefficient_fit_allowed_now: bool = False
    model_selection_allowed_now: bool = False


CASE_SPECS = [
    CaseSpec(
        "salt1_nominal",
        "Salt 1 nominal",
        "salt1_jin_nominal_continuation_corrected",
        "train",
        "train_nominal",
        "1.00",
        "latest corrected Salt1 stopped-run final window plus uncertainty digest",
        False,
    ),
    CaseSpec(
        "salt2_jin_nominal",
        "Salt 2 nominal",
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "train",
        "train_nominal",
        "1.00",
        "Salt1-4 postprocessing inventory window stats",
        False,
    ),
    CaseSpec(
        "salt3_jin_nominal",
        "Salt 3 nominal",
        "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "train",
        "train_nominal",
        "1.00",
        "Salt1-4 postprocessing inventory window stats",
        False,
    ),
    CaseSpec(
        "salt4_nominal",
        "Salt 4 nominal",
        "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "train",
        "train_nominal",
        "1.00",
        "Salt1-4 postprocessing inventory window stats",
        False,
    ),
    CaseSpec(
        "salt2_lo5q",
        "Salt 2 -5Q",
        "salt2_jin_lo5q_corrected",
        "holdout_test",
        "holdout_pm5",
        "0.95",
        "Salt1-4 postprocessing inventory window stats",
        True,
    ),
    CaseSpec(
        "salt2_hi5q",
        "Salt 2 +5Q",
        "salt2_jin_hi5q_corrected",
        "holdout_test",
        "holdout_pm5",
        "1.05",
        "Salt1-4 postprocessing inventory window stats",
        True,
    ),
    CaseSpec(
        "val_salt2",
        "Salt 2 external validation",
        "val_salt_test_2_coarse_mesh_laminar",
        "holdout_test",
        "external_test",
        "external",
        "Salt1-4 postprocessing inventory window stats; external validation row",
        True,
    ),
]

TP_LABELS = [f"TP{i}" for i in range(1, 7)]
TW_LABELS = [f"TW{i}" for i in range(1, 12)]
WIDE_QOI_LABELS = ["mdot_abs_mean_kg_s", "mdot_signed_mean_kg_s", "TP_mean_K", "TW_mean_K"] + [
    f"{label}_K" for label in TP_LABELS + TW_LABELS
]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 12) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}g}"


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def load_window_stats_by_source() -> dict[str, list[dict[str, str]]]:
    rows = read_csv(WINDOW_STATS)
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_source.setdefault(row["source_id"], []).append(row)
    return by_source


def load_salt1_uncertainty_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(SALT1_UNCERT)
        if row.get("case_slug", "").endswith("salt1_jin_nominal_continuation_corrected__viscosity_screening_salt_test_1_jin_coarse_mesh_continuation")
    ]


def add_long_row(
    rows: list[dict[str, Any]],
    spec: CaseSpec,
    qoi_label: str,
    qoi_family: str,
    mean_value: float | None,
    unit: str,
    n: str = "",
    window_start_s: str = "",
    window_end_s: str = "",
    source_path: Path | None = None,
    source_quantity: str = "",
    coverage_status: str = "available",
) -> None:
    rows.append(
        {
            "case_key": spec.case_key,
            "display_name": spec.display_name,
            "source_id": spec.source_id,
            "split_group": spec.split_group,
            "split_subrole": spec.split_subrole,
            "q_ratio": spec.q_ratio,
            "qoi_family": qoi_family,
            "qoi_label": qoi_label,
            "mean_value": fmt(mean_value),
            "unit": unit,
            "n": n,
            "window_start_s": window_start_s,
            "window_end_s": window_end_s,
            "coverage_status": coverage_status,
            "source_quantity": source_quantity,
            "source_path": rel(source_path) if source_path is not None else "",
            "coefficient_fit_allowed_now": spec.coefficient_fit_allowed_now,
            "model_selection_allowed_now": spec.model_selection_allowed_now,
            "score_allowed_after_freeze": spec.score_allowed_after_freeze,
        }
    )


def extract_from_window_stats(spec: CaseSpec, rows: list[dict[str, str]], long_rows: list[dict[str, Any]]) -> dict[str, Any]:
    wide: dict[str, Any] = {}

    mdot_rows = [row for row in rows if row.get("quantity") == "mdot_kg_s" and row.get("function_object", "").startswith("mdot_pipeleg")]
    mdot_signed = mean([fnum(row.get("mean")) for row in mdot_rows if fnum(row.get("mean")) is not None])
    mdot_abs = abs(mdot_signed) if mdot_signed is not None else None
    if mdot_rows:
        wide.update(
            {
                "mdot_signed_mean_kg_s": fmt(mdot_signed),
                "mdot_abs_mean_kg_s": fmt(mdot_abs),
                "mdot_n": str(sum(int(float(row.get("n", "0") or 0)) for row in mdot_rows)),
                "mdot_window_start_s": min(row["window_start_s"] for row in mdot_rows),
                "mdot_window_end_s": max(row["window_end_s"] for row in mdot_rows),
            }
        )
    add_long_row(
        long_rows,
        spec,
        "mdot_abs_mean_kg_s",
        "mdot",
        mdot_abs,
        "kg/s",
        n=wide.get("mdot_n", ""),
        window_start_s=wide.get("mdot_window_start_s", ""),
        window_end_s=wide.get("mdot_window_end_s", ""),
        source_path=WINDOW_STATS,
        source_quantity="mean(abs(mdot_pipeleg_*_kg_s))",
        coverage_status="available" if mdot_abs is not None else "missing",
    )

    tp_values: list[float] = []
    tp_rows = [row for row in rows if row.get("function_object") == "temperature_probes" and row.get("quantity") == "temperature_K"]
    for label in TP_LABELS:
        match = next((row for row in tp_rows if row.get("patch_or_surface") == label), None)
        value = fnum(match.get("mean")) if match else None
        wide[f"{label}_K"] = fmt(value)
        if value is not None:
            tp_values.append(value)
        add_long_row(
            long_rows,
            spec,
            label,
            "TP",
            value,
            "K",
            n=match.get("n", "") if match else "",
            window_start_s=match.get("window_start_s", "") if match else "",
            window_end_s=match.get("window_end_s", "") if match else "",
            source_path=WINDOW_STATS,
            source_quantity="temperature_probes/temperature_K",
            coverage_status="available" if match else "missing",
        )
    wide["TP_mean_K"] = fmt(mean(tp_values))

    tw_component_values: dict[str, list[float]] = {label: [] for label in TW_LABELS}
    tw_rows = [row for row in rows if row.get("function_object") == "wall_temperature_probes" and row.get("quantity") == "temperature_K"]
    tw_pattern = re.compile(r"^(TW\d+)(?:_|$)")
    for row in tw_rows:
        match = tw_pattern.match(row.get("patch_or_surface", ""))
        if not match:
            continue
        label = match.group(1)
        if label in tw_component_values:
            value = fnum(row.get("mean"))
            if value is not None:
                tw_component_values[label].append(value)
    tw_values: list[float] = []
    for label in TW_LABELS:
        value = mean(tw_component_values[label])
        wide[f"{label}_K"] = fmt(value)
        if value is not None:
            tw_values.append(value)
        add_long_row(
            long_rows,
            spec,
            label,
            "TW",
            value,
            "K",
            n=str(len(tw_component_values[label])) if tw_component_values[label] else "",
            window_start_s=min([row["window_start_s"] for row in tw_rows if row.get("patch_or_surface", "").startswith(label + "_")], default=""),
            window_end_s=max([row["window_end_s"] for row in tw_rows if row.get("patch_or_surface", "").startswith(label + "_")], default=""),
            source_path=WINDOW_STATS,
            source_quantity="mean(wall_temperature_probes/temperature_K components)",
            coverage_status="available" if value is not None else "missing",
        )
    wide["TW_mean_K"] = fmt(mean(tw_values))
    wide["tw_individual_basis"] = "component_mean_from_wall_temperature_probes" if tw_values else "missing"
    wide["tp_sensor_count"] = str(len(tp_values))
    wide["tw_sensor_count"] = str(len(tw_values))
    return wide


def extract_salt1(long_rows: list[dict[str, Any]]) -> dict[str, Any]:
    spec = CASE_SPECS[0]
    rows = load_salt1_uncertainty_rows()
    wide: dict[str, Any] = {}
    mdot_row = next((row for row in rows if row.get("group") == "mdot"), None)
    mdot_signed = fnum(mdot_row.get("osc_mean")) if mdot_row else None
    mdot_abs = abs(mdot_signed) if mdot_signed is not None else None
    wide.update(
        {
            "mdot_signed_mean_kg_s": fmt(mdot_signed),
            "mdot_abs_mean_kg_s": fmt(mdot_abs),
            "mdot_n": "",
            "mdot_window_start_s": "7284",
            "mdot_window_end_s": "7884",
        }
    )
    add_long_row(
        long_rows,
        spec,
        "mdot_abs_mean_kg_s",
        "mdot",
        mdot_abs,
        "kg/s",
        window_start_s="7284",
        window_end_s="7884",
        source_path=SALT1_UNCERT,
        source_quantity="mdot/lower (heater)/osc_mean",
        coverage_status="available",
    )

    tp_values: list[float] = []
    probe_rows = [row for row in rows if row.get("group") == "temperature"]
    for idx, label in enumerate(TP_LABELS):
        match = probe_rows[idx] if idx < len(probe_rows) else None
        value = fnum(match.get("osc_mean")) if match else None
        wide[f"{label}_K"] = fmt(value)
        if value is not None:
            tp_values.append(value)
        add_long_row(
            long_rows,
            spec,
            label,
            "TP",
            value,
            "K",
            window_start_s="7284",
            window_end_s="7884",
            source_path=SALT1_UNCERT,
            source_quantity=match.get("series", "") if match else "temperature/probe",
            coverage_status="available_coordinate_probe_mapped_to_TP_order" if match else "missing",
        )
    wide["TP_mean_K"] = fmt(mean(tp_values))

    tw_mean_row = next((row for row in rows if row.get("group") == "wall_temperature"), None)
    tw_mean = fnum(tw_mean_row.get("osc_mean")) if tw_mean_row else None
    wide["TW_mean_K"] = fmt(tw_mean)
    for label in TW_LABELS:
        wide[f"{label}_K"] = ""
        add_long_row(
            long_rows,
            spec,
            label,
            "TW",
            None,
            "K",
            window_start_s="7284",
            window_end_s="7884",
            source_path=SALT1_UNCERT,
            source_quantity="individual TW unavailable in corrected Salt1 uncertainty digest",
            coverage_status="missing_individual_TW_corrected_salt1_has_wall_spatial_mean_only",
        )
    add_long_row(
        long_rows,
        spec,
        "TW_mean_K",
        "TW",
        tw_mean,
        "K",
        window_start_s="7284",
        window_end_s="7884",
        source_path=SALT1_UNCERT,
        source_quantity="wall_temperature/wall T spatial mean/osc_mean",
        coverage_status="available_spatial_mean_only",
    )
    wide["tw_individual_basis"] = "missing_individual_TW_corrected_salt1_has_wall_spatial_mean_only"
    wide["tp_sensor_count"] = str(len(tp_values))
    wide["tw_sensor_count"] = "0"
    return wide


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_source = load_window_stats_by_source()
    long_rows: list[dict[str, Any]] = []
    wide_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []

    for spec in CASE_SPECS:
        wide = extract_salt1(long_rows) if spec.case_key == "salt1_nominal" else extract_from_window_stats(spec, by_source.get(spec.source_id, []), long_rows)
        tp_count = int(wide.get("tp_sensor_count") or 0)
        tw_count = int(wide.get("tw_sensor_count") or 0)
        mdot_available = wide.get("mdot_abs_mean_kg_s", "") != ""
        coverage_status = "complete" if mdot_available and tp_count == 6 and tw_count == 11 else "partial"
        if spec.case_key == "salt1_nominal":
            coverage_status = "partial_latest_salt1_corrected_no_individual_TW"
        base = {
            "case_key": spec.case_key,
            "display_name": spec.display_name,
            "source_id": spec.source_id,
            "split_group": spec.split_group,
            "split_subrole": spec.split_subrole,
            "q_ratio": spec.q_ratio,
            "source_basis": spec.source_basis,
            "data_coverage_status": coverage_status,
            "coefficient_fit_allowed_now": spec.coefficient_fit_allowed_now,
            "model_selection_allowed_now": spec.model_selection_allowed_now,
            "score_allowed_after_freeze": spec.score_allowed_after_freeze,
            "runtime_use_warning": "CFD QoIs are score/diagnostic targets only; not runtime inputs to predictive 1D model",
        }
        row = {**base, **wide}
        wide_rows.append(row)
        coverage_rows.append(
            {
                "case_key": spec.case_key,
                "source_id": spec.source_id,
                "split_group": spec.split_group,
                "split_subrole": spec.split_subrole,
                "mdot_available": mdot_available,
                "tp_available_count": tp_count,
                "tw_available_count": tw_count,
                "coverage_status": coverage_status,
                "notes": "val_salt2 is grouped in holdout_test with external_test subtype"
                if spec.case_key == "val_salt2"
                else ("latest corrected Salt1 lacks individual TW labels in this source" if spec.case_key == "salt1_nominal" else ""),
            }
        )
    return wide_rows, long_rows, coverage_rows


def split_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "case_key": spec.case_key,
            "split_group": spec.split_group,
            "split_subrole": spec.split_subrole,
            "coefficient_fit_allowed_now": spec.coefficient_fit_allowed_now,
            "model_selection_allowed_now": spec.model_selection_allowed_now,
            "score_allowed_after_freeze": spec.score_allowed_after_freeze,
            "policy_note": "External validation is reported inside the holdout/test bucket, with subtype external_test."
            if spec.case_key == "val_salt2"
            else "",
        }
        for spec in CASE_SPECS
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [WINDOW_STATS, SALT1_STOPPED, SALT1_UNCERT, LEGAL_USE, PM5_SPLIT, SENSOR_REFERENCE, TRAINING_ROSTER]
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "use": "read_only_context",
            "mutation_allowed": False,
        }
        for path in paths
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs", "status": "not_mutated"},
        {"guardrail": "registry_or_admission_state", "status": "not_mutated"},
        {"guardrail": "scheduler_or_solver_launch", "status": "not_used"},
        {"guardrail": "validation_holdout_external_model_scoring", "status": "not_performed"},
        {"guardrail": "fitting_tuning_model_selection", "status": "not_performed"},
        {"guardrail": "source_property_or_Qwall_release", "status": "not_released"},
        {"guardrail": "coefficient_admission_or_candidate_freeze", "status": "not_performed"},
        {"guardrail": "CFD_QOIs_as_runtime_inputs", "status": "forbidden"},
    ]


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  task_id: {TASK_ID}
  generated_at: {summary["generated_at"]}
tags:
  - thesis
  - cfd-qoi-chart
  - train-holdout
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/README.md
---
# Thesis CFD Run QoI Split Chart

Decision: `{summary["decision"]}`.

This package creates thesis-facing CSV charts of CFD runs versus split role and
QoIs. It treats `val_salt2` as part of the `holdout_test` bucket while keeping
the subtype `external_test`, so the thesis can report one protected test set
without losing provenance.

Outputs:

- `cfd_run_qoi_split_chart_wide.csv`: one row per CFD run with mdot, TP1-TP6,
  TW1-TW11, TP mean, and TW mean columns.
- `cfd_run_qoi_split_chart_long.csv`: tidy QoI rows for plotting.
- `cfd_run_qoi_source_coverage.csv`: coverage and caveats.
- `holdout_test_policy_update.csv`: split grouping with no-fit/no-selection
  flags.

Salt1 nominal uses the latest corrected Salt1 stopped-run/uncertainty evidence.
That source has TP probe values and a wall-temperature spatial mean, but not
individual TW1-TW11 labels, so the TW columns are intentionally blank for that
row and the coverage status is partial.

No model training, fitting, scoring, source/property release, Qwall release,
coefficient admission, candidate freeze, solver launch, scheduler action,
native-output mutation, or registry/admission mutation was performed.
"""


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    wide_rows, long_rows, coverage_rows = build_rows()
    split_rows = split_policy_rows()
    manifest = source_manifest_rows()
    guardrails = guardrail_rows()

    wide_fields = [
        "case_key",
        "display_name",
        "source_id",
        "split_group",
        "split_subrole",
        "q_ratio",
        "source_basis",
        "data_coverage_status",
        "coefficient_fit_allowed_now",
        "model_selection_allowed_now",
        "score_allowed_after_freeze",
        "runtime_use_warning",
        "mdot_abs_mean_kg_s",
        "mdot_signed_mean_kg_s",
        "mdot_n",
        "mdot_window_start_s",
        "mdot_window_end_s",
        "TP_mean_K",
        *[f"{label}_K" for label in TP_LABELS],
        "TW_mean_K",
        *[f"{label}_K" for label in TW_LABELS],
        "tp_sensor_count",
        "tw_sensor_count",
        "tw_individual_basis",
    ]
    long_fields = [
        "case_key",
        "display_name",
        "source_id",
        "split_group",
        "split_subrole",
        "q_ratio",
        "qoi_family",
        "qoi_label",
        "mean_value",
        "unit",
        "n",
        "window_start_s",
        "window_end_s",
        "coverage_status",
        "source_quantity",
        "source_path",
        "coefficient_fit_allowed_now",
        "model_selection_allowed_now",
        "score_allowed_after_freeze",
    ]
    csv_dump(out / "cfd_run_qoi_split_chart_wide.csv", wide_fields, wide_rows)
    csv_dump(out / "cfd_run_qoi_split_chart_long.csv", long_fields, long_rows)
    csv_dump(
        out / "cfd_run_qoi_source_coverage.csv",
        ["case_key", "source_id", "split_group", "split_subrole", "mdot_available", "tp_available_count", "tw_available_count", "coverage_status", "notes"],
        coverage_rows,
    )
    csv_dump(
        out / "holdout_test_policy_update.csv",
        ["case_key", "split_group", "split_subrole", "coefficient_fit_allowed_now", "model_selection_allowed_now", "score_allowed_after_freeze", "policy_note"],
        split_rows,
    )
    csv_dump(out / "source_manifest.csv", ["source_path", "exists", "use", "mutation_allowed"], manifest)
    csv_dump(out / "no_mutation_guardrails.csv", ["guardrail", "status"], guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "cfd_run_qoi_split_chart_complete_no_model_scoring",
        "wide_rows": len(wide_rows),
        "long_rows": len(long_rows),
        "train_rows": sum(1 for row in wide_rows if row["split_group"] == "train"),
        "holdout_test_rows": sum(1 for row in wide_rows if row["split_group"] == "holdout_test"),
        "external_test_rows_grouped_as_holdout_test": sum(1 for row in wide_rows if row["split_subrole"] == "external_test"),
        "all_source_paths_exist": all(row["exists"] for row in manifest),
        "model_scoring_performed": False,
        "fitting_model_selection_performed": False,
        "source_property_release": False,
        "candidate_freeze": False,
    }
    json_dump(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
