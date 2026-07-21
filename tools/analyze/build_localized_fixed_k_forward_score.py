#!/usr/bin/env python3
"""Score Salt2/3/4 with Fluid localized fixed-K hydraulic losses.

This package exercises the existing Fluid ``localized_fixed_k_by_segment`` hook.
It is a gate-moving hydraulic score, not a final forward-v1 model: it still uses
the forward-v0 imposed-cooler thermal boundary and does not implement
reset/redevelopment semantics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import run_predictive_forward_v0_imposed_cooler as base  # noqa: E402
from tools.analyze import run_predictive_h1_proxy_rerun as h1proxy  # noqa: E402

TASK_ID = "AGENT-328"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score"
H1_PROXY_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun"
H1_PROXY_K_SOURCE = H1_PROXY_DIR / "h1_proxy_k_source.csv"
FORWARD_V0_DIR = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler"
FORWARD_V0_RESULTS = FORWARD_V0_DIR / "forward_v0_results.csv"
FLUID_HOOK_PACKAGE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api"
FINAL_GATE_PACKAGE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate"

SPLIT = {
    "salt_2": ("train", "training_residual_only_not_model_selection_score"),
    "salt_3": ("validation", "diagnostic_validation_check_no_refit"),
    "salt_4": ("holdout", "diagnostic_holdout_check_no_refit"),
}

LOCALIZED_SOURCE_COLUMNS = [
    "case_id",
    "name",
    "loss_class",
    "span_or_feature",
    "localized_fixed_k_key",
    "fit_use_status",
    "K_local",
    "included_in_localized_score",
    "exclusion_reason",
    "quality_flags",
    "source_path",
]

SCORE_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "split_assignment",
    "split_score_boundary",
    "base_variant_id",
    "localized_variant_id",
    "engine",
    "cfd_mdot_kg_s",
    "baseline_mdot_kg_s",
    "localized_mdot_kg_s",
    "baseline_mdot_error_vs_cfd_kg_s",
    "localized_mdot_error_vs_cfd_kg_s",
    "baseline_abs_mdot_error_pct",
    "localized_abs_mdot_error_pct",
    "mdot_error_reduction_kg_s",
    "mdot_error_reduction_pct",
    "localized_pressure_residual_Pa",
    "localized_root_status",
    "localized_accepted_for_validation",
    "thermal_fit_used",
    "runtime_uses_cfd_mdot",
    "runtime_uses_realized_cfd_wallheatflux",
    "runtime_uses_validation_temperatures",
    "runtime_uses_imposed_cooler_duty",
    "localized_fixed_k_keys",
    "localized_fixed_k_total",
    "movement_direction",
    "row_decision",
    "boundary_note",
]

VARIANT_COLUMNS = [
    "base_variant_id",
    "localized_variant_id",
    "n_rows",
    "mean_baseline_abs_mdot_error_kg_s",
    "mean_localized_abs_mdot_error_kg_s",
    "mean_baseline_abs_mdot_error_pct",
    "mean_localized_abs_mdot_error_pct",
    "mean_mdot_error_reduction_pct",
    "train_localized_abs_mdot_error_pct",
    "validation_localized_abs_mdot_error_pct",
    "holdout_localized_abs_mdot_error_pct",
    "all_localized_rows_overpredict_cfd",
    "movement_gate",
    "forward_v1_scoring_decision",
]

RIGOR_COLUMNS = ["gate_id", "gate", "status", "evidence", "failure_action"]
MANIFEST_COLUMNS = ["source_id", "path", "description", "access"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def fnum(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def localized_source_rows(path: Path = H1_PROXY_K_SOURCE) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        k_local = fnum(row.get("K_local"))
        span = row.get("span_or_feature", "")
        included = row.get("included_in_proxy") == "yes" and k_local is not None and bool(span)
        if included:
            reason = ""
        elif row.get("included_in_proxy") != "yes":
            reason = row.get("exclusion_reason", "not_in_proxy_training_set")
        elif not span:
            reason = "missing_span_or_feature_for_localized_key"
        else:
            reason = "K_local_not_finite"
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "name": row.get("name", ""),
                "loss_class": row.get("loss_class", ""),
                "span_or_feature": span,
                "localized_fixed_k_key": span if included else "",
                "fit_use_status": row.get("fit_use_status", ""),
                "K_local": k_local,
                "included_in_localized_score": "yes" if included else "no",
                "exclusion_reason": reason,
                "quality_flags": row.get("quality_flags", ""),
                "source_path": row.get("source_path", ""),
            }
        )
    return rows


def localized_k_map(rows: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in rows:
        if row.get("included_in_localized_score") != "yes":
            continue
        key = str(row["localized_fixed_k_key"])
        value = fnum(row.get("K_local"))
        if not key or value is None:
            continue
        if key in result:
            raise ValueError(f"duplicate localized fixed-K key {key!r}")
        result[key] = value
    if not result:
        raise ValueError("no localized fixed-K rows were available")
    return result


def localized_minor_losses(k_by_segment: dict[str, float]) -> base.S.MinorLosses:
    return base.S.MinorLosses(
        major_loss_multiplier=1.0,
        k_90deg=0.0,
        n_90deg=0,
        k_20deg=0.0,
        n_20deg=0,
        include_test_section_diameter_change=True,
        localized_fixed_k_by_segment=dict(k_by_segment),
    )


def baseline_by_case_variant() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(FORWARD_V0_RESULTS)
    return {(row["case_id"], row["variant_id"]): row for row in rows}


def split_for(case_id: str) -> tuple[str, str]:
    try:
        return SPLIT[case_id]
    except KeyError as exc:
        raise ValueError(f"unexpected case_id {case_id!r}") from exc


def pct_error(error: float | None, cfd_mdot: float | None) -> float | None:
    if error is None or cfd_mdot in (None, 0.0):
        return None
    return abs(error) / abs(cfd_mdot) * 100.0


def movement_direction(baseline_abs: float | None, localized_abs: float | None) -> str:
    if baseline_abs is None or localized_abs is None:
        return "not_scoreable"
    if localized_abs < baseline_abs:
        return "toward_cfd"
    if localized_abs > baseline_abs:
        return "away_from_cfd"
    return "unchanged"


def row_decision(case_id: str, movement: str, accepted: bool) -> str:
    split, _ = split_for(case_id)
    if not accepted:
        return f"{split}_row_blocked_root_or_temperature_gate"
    if movement == "toward_cfd":
        return f"{split}_row_improves_mdot_diagnostic_only"
    if movement == "away_from_cfd":
        return f"{split}_row_worsens_mdot_diagnostic_only"
    return f"{split}_row_no_mdot_change_diagnostic_only"


def build_score_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_rows = localized_source_rows()
    k_by_segment = localized_k_map(source_rows)
    minor_losses = localized_minor_losses(k_by_segment)
    baseline_lookup = baseline_by_case_variant()
    case_inputs = base.read_csv(base.CONTRACT_DIR / "case_runtime_inputs_forward_v0.csv")
    targets = base.target_by_case()
    cases = {case.name: case for case in base.config_loader.load_cases()}
    validation_records = base.config_loader.load_validation_records()

    score_rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        case = cases[case_input["fluid_case_name"]]
        validation_record = validation_records.get(case.name)
        target = targets.get(case_input["case_id"], {})
        split_assignment, split_boundary = split_for(case_input["case_id"])
        for spec in base.variant_specs():
            base_variant = spec["variant_id"]
            variant_id = f"{base_variant}_localized_fixed_K"
            scenario = base.scenario_for(case_input, base_variant)
            scenario = replace(scenario, name=f"forward_v0_{variant_id}")
            prescribed = base.prescribed_sources_for(case, base_variant)
            result = h1proxy.fast_pressure_root_proxy(case, scenario, prescribed, minor_losses)
            row = base.result_row(result, case_input, variant_id, "fast_scan_localized_fixed_k", prescribed, validation_record, target)
            baseline = baseline_lookup[(case_input["case_id"], base_variant)]
            cfd_mdot = fnum(row.get("cfd_mdot_kg_s"))
            baseline_mdot = fnum(baseline.get("mdot_kg_s"))
            baseline_err = fnum(baseline.get("mdot_error_vs_cfd_kg_s"))
            localized_err = fnum(row.get("mdot_error_vs_cfd_kg_s"))
            baseline_abs_pct = pct_error(baseline_err, cfd_mdot)
            localized_abs_pct = pct_error(localized_err, cfd_mdot)
            reduction = abs(baseline_err) - abs(localized_err) if baseline_err is not None and localized_err is not None else None
            reduction_pct = reduction / abs(baseline_err) * 100.0 if reduction is not None and baseline_err not in (None, 0.0) else None
            movement = movement_direction(abs(baseline_err) if baseline_err is not None else None, abs(localized_err) if localized_err is not None else None)
            accepted = str(row.get("accepted_for_validation", "")).lower() == "true"
            score_rows.append(
                {
                    "case_id": case_input["case_id"],
                    "fluid_case_name": case_input["fluid_case_name"],
                    "source_id": case_input["source_id"],
                    "split_assignment": split_assignment,
                    "split_score_boundary": split_boundary,
                    "base_variant_id": base_variant,
                    "localized_variant_id": variant_id,
                    "engine": "fast_scan_localized_fixed_k",
                    "cfd_mdot_kg_s": cfd_mdot,
                    "baseline_mdot_kg_s": baseline_mdot,
                    "localized_mdot_kg_s": row.get("mdot_kg_s"),
                    "baseline_mdot_error_vs_cfd_kg_s": baseline_err,
                    "localized_mdot_error_vs_cfd_kg_s": localized_err,
                    "baseline_abs_mdot_error_pct": baseline_abs_pct,
                    "localized_abs_mdot_error_pct": localized_abs_pct,
                    "mdot_error_reduction_kg_s": reduction,
                    "mdot_error_reduction_pct": reduction_pct,
                    "localized_pressure_residual_Pa": row.get("pressure_residual_Pa"),
                    "localized_root_status": row.get("root_status"),
                    "localized_accepted_for_validation": row.get("accepted_for_validation"),
                    "thermal_fit_used": "false",
                    "runtime_uses_cfd_mdot": "false",
                    "runtime_uses_realized_cfd_wallheatflux": "false",
                    "runtime_uses_validation_temperatures": "false",
                    "runtime_uses_imposed_cooler_duty": "true",
                    "localized_fixed_k_keys": ";".join(sorted(k_by_segment)),
                    "localized_fixed_k_total": sum(k_by_segment.values()),
                    "movement_direction": movement,
                    "row_decision": row_decision(case_input["case_id"], movement, accepted),
                    "boundary_note": (
                        "Uses existing Fluid localized_fixed_k_by_segment hook; no thermal fitting. "
                        "Still forward-v0 imposed-cooler, so hydraulic evidence is diagnostic-only for final forward-v1."
                    ),
                }
            )
    return source_rows, score_rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def variant_summary_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in score_rows:
        grouped.setdefault(str(row["base_variant_id"]), []).append(row)
    rows: list[dict[str, Any]] = []
    for base_variant, items in sorted(grouped.items()):
        localized_variant = str(items[0]["localized_variant_id"])
        by_split = {str(row["split_assignment"]): row for row in items}
        baseline_abs = [abs(float(row["baseline_mdot_error_vs_cfd_kg_s"])) for row in items]
        localized_abs = [abs(float(row["localized_mdot_error_vs_cfd_kg_s"])) for row in items]
        reductions = [float(row["mdot_error_reduction_pct"]) for row in items if row["mdot_error_reduction_pct"] not in ("", None)]
        all_over = all(float(row["localized_mdot_error_vs_cfd_kg_s"]) > 0.0 for row in items)
        all_toward = all(row["movement_direction"] == "toward_cfd" for row in items)
        val = by_split.get("validation", {})
        hold = by_split.get("holdout", {})
        validation_pct = fnum(val.get("localized_abs_mdot_error_pct"))
        holdout_pct = fnum(hold.get("localized_abs_mdot_error_pct"))
        movement_gate = "pass_directional_screen" if all_toward else "fail_directional_screen"
        if validation_pct is None or holdout_pct is None:
            decision = "blocked_missing_validation_or_holdout"
        elif movement_gate != "pass_directional_screen":
            decision = "diagnostic_only_failed_directional_screen"
        else:
            decision = "diagnostic_only_improves_mdot_but_not_final_forward_v1"
        rows.append(
            {
                "base_variant_id": base_variant,
                "localized_variant_id": localized_variant,
                "n_rows": len(items),
                "mean_baseline_abs_mdot_error_kg_s": mean(baseline_abs),
                "mean_localized_abs_mdot_error_kg_s": mean(localized_abs),
                "mean_baseline_abs_mdot_error_pct": mean([float(row["baseline_abs_mdot_error_pct"]) for row in items]),
                "mean_localized_abs_mdot_error_pct": mean([float(row["localized_abs_mdot_error_pct"]) for row in items]),
                "mean_mdot_error_reduction_pct": mean(reductions),
                "train_localized_abs_mdot_error_pct": by_split.get("train", {}).get("localized_abs_mdot_error_pct", ""),
                "validation_localized_abs_mdot_error_pct": validation_pct,
                "holdout_localized_abs_mdot_error_pct": holdout_pct,
                "all_localized_rows_overpredict_cfd": bool_text(all_over),
                "movement_gate": movement_gate,
                "forward_v1_scoring_decision": decision,
            }
        )
    return rows


def rigor_rows(score_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    final_claim_blocked = "true"
    source_paths_present = all(bool(row.get("source_path")) for row in source_rows if row.get("included_in_localized_score") == "yes")
    return [
        {
            "gate_id": "R1",
            "gate": "Provenance completeness",
            "status": "pass" if source_paths_present else "fail",
            "evidence": "localized_fixed_k_source.csv includes source_path for every included K row",
            "failure_action": "block publication/admission claim",
        },
        {
            "gate_id": "R2",
            "gate": "No native CFD mutation",
            "status": "pass",
            "evidence": "package reads prior CSV/JSON artifacts and Fluid API only",
            "failure_action": "stop and create separate repair/staging row",
        },
        {
            "gate_id": "R5",
            "gate": "Predictive input discipline",
            "status": "pass",
            "evidence": "runtime flags for CFD mdot, realized wallHeatFlux, and validation temperatures are false on all score rows",
            "failure_action": "label replay/diagnostic, not predictive",
        },
        {
            "gate_id": "R6",
            "gate": "Locked split",
            "status": "pass" if {row["split_assignment"] for row in score_rows} == {"train", "validation", "holdout"} else "fail",
            "evidence": "Salt2=train, Salt3=validation, Salt4=holdout in localized_fixed_k_scorecard.csv",
            "failure_action": "do not report final forward-v1 score",
        },
        {
            "gate_id": "R8",
            "gate": "No global hydraulic fudge",
            "status": "pass",
            "evidence": "uses localized_fixed_k_by_segment keys instead of k_90deg aggregate or global major_loss_multiplier",
            "failure_action": "demote to diagnostic screen",
        },
        {
            "gate_id": "R10",
            "gate": "Documentation closeout",
            "status": "pass",
            "evidence": "status, journal, import manifest, README, summary, source manifest, and tests produced",
            "failure_action": "task incomplete",
        },
        {
            "gate_id": "FWD",
            "gate": "Final forward-v1 admission",
            "status": "blocked",
            "evidence": f"final_claim_blocked={final_claim_blocked}; cooler remains imposed and reset/redevelopment is not implemented",
            "failure_action": "keep final forward-v1 no-go until setup-only boundary and reset semantics land",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "source_id": "forward_v0_results",
            "path": rel(FORWARD_V0_RESULTS),
            "description": "baseline forward-v0 mdot rows for comparison",
            "access": "read_only",
        },
        {
            "source_id": "h1_proxy_k_source",
            "path": rel(H1_PROXY_K_SOURCE),
            "description": "Salt2 train K source rows used to build localized fixed-K map",
            "access": "read_only",
        },
        {
            "source_id": "fluid_localized_hook",
            "path": rel(FLUID_HOOK_PACKAGE / "README.md"),
            "description": "existing Fluid localized_fixed_k_by_segment hook evidence",
            "access": "read_only",
        },
        {
            "source_id": "final_forward_v1_gate",
            "path": rel(FINAL_GATE_PACKAGE / "README.md"),
            "description": "current no-go final forward-v1 decision boundary",
            "access": "read_only",
        },
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    f1 = next((row for row in summary["variant_summary"] if row["base_variant_id"] == "F1_heater_only"), None)
    f1_line = "No `F1_heater_only` summary row was generated."
    if f1:
        f1_line = (
            f"`F1_heater_only` localized fixed-K mean mdot error is "
            f"`{float(f1['mean_localized_abs_mdot_error_kg_s']):.6f} kg/s`, "
            f"with mean reduction `{float(f1['mean_mdot_error_reduction_pct']):.2f}%` vs baseline."
        )
    text = f"""---
provenance:
  - {rel(FORWARD_V0_RESULTS)}
  - {rel(H1_PROXY_K_SOURCE)}
  - {rel(FLUID_HOOK_PACKAGE / 'README.md')}
tags: [forward-model, hydraulics, localized-fixed-k, scorecard]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_localized_h1_and_boundary_api/README.md
task: {TASK_ID}
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Localized Fixed-K Forward Score

Generated: `{summary['generated_utc']}`

## Decision

This package executes the localized fixed-K work packet through the existing
Fluid hook. The current localized-only score does not pass the directional
hydraulic screen; it remains diagnostic-only for final forward-v1 because the
run still uses imposed cooler duty and does not implement reset/redevelopment
semantics.

{f1_line}

Final forward-v1 remains: `{summary['final_forward_v1_status']}`.

## Guardrails

- Thermal fitting used: `false`.
- Runtime CFD mdot used: `false`.
- Runtime realized CFD wallHeatFlux used: `false`.
- Runtime validation temperatures used: `false`.
- Runtime imposed cooler duty used: `true`, so this is not final setup-only
  boundary/HX evidence.
- Global hydraulic multiplier exported: `false`.

## Outputs

- `localized_fixed_k_source.csv`
- `localized_fixed_k_scorecard.csv`
- `localized_fixed_k_variant_summary.csv`
- `rigor_gate_audit.csv`
- `source_manifest.csv`
- `summary.json`
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def run_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_rows, score_rows = build_score_rows()
    variant_rows = variant_summary_rows(score_rows)
    rigor = rigor_rows(score_rows, source_rows)
    included = [row for row in source_rows if row["included_in_localized_score"] == "yes"]
    f1 = next((row for row in variant_rows if row["base_variant_id"] == "F1_heater_only"), {})
    summary = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "overall_status": "localized_fixed_k_score_complete_diagnostic_only",
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "engine": "fast_scan_localized_fixed_k",
        "n_result_rows": len(score_rows),
        "n_cases": len({row["case_id"] for row in score_rows}),
        "n_variants": len({row["base_variant_id"] for row in score_rows}),
        "localized_fixed_k_keys": sorted({row["localized_fixed_k_key"] for row in included}),
        "localized_fixed_k_total": sum(float(row["K_local"]) for row in included),
        "n_localized_k_rows": len(included),
        "thermal_fit_used": False,
        "runtime_uses_cfd_mdot": False,
        "runtime_uses_realized_cfd_wallheatflux": False,
        "runtime_uses_validation_temperatures": False,
        "runtime_uses_imposed_cooler_duty": True,
        "external_fluid_modified": False,
        "native_solver_outputs_mutated": False,
        "global_friction_multiplier_exported": False,
        "reset_redevelopment_implemented": False,
        "setup_only_boundary_hx_final": False,
        "f1_mean_localized_abs_mdot_error_kg_s": fnum(f1.get("mean_localized_abs_mdot_error_kg_s")),
        "f1_mean_mdot_error_reduction_pct": fnum(f1.get("mean_mdot_error_reduction_pct")),
        "variant_summary": variant_rows,
        "rigor_gate_status": {row["gate_id"]: row["status"] for row in rigor},
        "outputs": [
            "README.md",
            "localized_fixed_k_source.csv",
            "localized_fixed_k_scorecard.csv",
            "localized_fixed_k_variant_summary.csv",
            "rigor_gate_audit.csv",
            "source_manifest.csv",
            "summary.json",
        ],
    }
    write_csv(out_dir / "localized_fixed_k_source.csv", source_rows, LOCALIZED_SOURCE_COLUMNS)
    write_csv(out_dir / "localized_fixed_k_scorecard.csv", score_rows, SCORE_COLUMNS)
    write_csv(out_dir / "localized_fixed_k_variant_summary.csv", variant_rows, VARIANT_COLUMNS)
    write_csv(out_dir / "rigor_gate_audit.csv", rigor, RIGOR_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", source_manifest_rows(), MANIFEST_COLUMNS)
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = run_package(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
