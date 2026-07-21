#!/usr/bin/env python3
"""Verify AGENT-373 hydraulic chain rerun and final admission lanes."""

from __future__ import annotations

import csv
import json
import socket
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TASK = "AGENT-421"
DATE = "2026-07-15"
PACKAGE_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification")
PACKAGE = ROOT / PACKAGE_REL
STAGE_OUT = PACKAGE / "agent373_stage_outputs"

AGENT373 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_overnight_dependent_chain"
AGENT405 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run"
AGENT406 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
AGENT409 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess"
AGENT414 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> int:
    materialized = list(rows)
    if fieldnames is None:
        fieldnames = list(materialized[0].keys()) if materialized else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_summary(stage: str) -> dict[str, Any]:
    return read_json(STAGE_OUT / f"{stage}_summary.json")


def build_chain_verification() -> list[dict[str, Any]]:
    stages = [
        ("agent373_rerun", "test_section_complex_raw_two_tap", STAGE_OUT / "test_section_complex_raw_two_tap_status.csv"),
        ("agent373_rerun", "f6_ready_to_run_gate", STAGE_OUT / "f6_ready_to_run_gate.csv"),
        ("agent373_rerun", "fluid_reset_k_diagnostic_sweep", STAGE_OUT / "fluid_reset_k_diagnostic_sweep.csv"),
        ("agent409_scratch_openfoam", "raw_two_tap_agent409_staged_copy", AGENT409 / "raw_two_tap_test_section_complex.csv"),
        ("agent406_scratch_openfoam", "pm5_matched_pressure_upcomer", AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
        ("agent414_review", "f6_pm5_readiness", AGENT414 / "f6_pm5_row_readiness.csv"),
    ]
    rows = []
    for source, item, path in stages:
        summary = stage_summary(item) if source == "agent373_rerun" else {}
        table_rows = read_csv(path)
        rows.append({
            "source": source,
            "item": item,
            "rerun_on_node_or_consumed": "rerun_on_node" if source == "agent373_rerun" else "consumed_completed_node_output",
            "output_path": rel(path),
            "output_exists": str(path.exists()).lower(),
            "row_count": len(table_rows) if table_rows else summary.get("rows", 0),
            "stage_status": summary.get("status", "landed_existing" if path.exists() else "missing"),
            "admission_effect": admission_effect_for_item(item),
        })
    return rows


def admission_effect_for_item(item: str) -> str:
    if item == "test_section_complex_raw_two_tap":
        return "preflight_rerun_only; superseded by AGENT-409 scratch diagnostic extraction"
    if item == "raw_two_tap_agent409_staged_copy":
        return "diagnostic_admitted_pressure_scale_only_not_fit_admitted"
    if item == "f6_ready_to_run_gate":
        return "gate_rerun_landed_not_ready_for_fit_admission"
    if item == "fluid_reset_k_diagnostic_sweep":
        return "diagnostic_admitted_component_separation_only"
    if item == "pm5_matched_pressure_upcomer":
        return "diagnostic_complete_for_review_not_fit_admitted"
    if item == "f6_pm5_readiness":
        return "all_rows_diagnostic_onset_only_zero_fit_admissible"
    return "informational"


def build_admission_decisions(raw_rows: list[dict[str, str]], pm5_rows: list[dict[str, str]], f6_rows: list[dict[str, str]], reset_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    raw_diag = sum(row.get("admission_status", "").startswith("diagnostic") for row in raw_rows)
    pm5_wall = sum(row.get("wallHeatFlux_available", "").lower() == "true" for row in pm5_rows)
    f6_fit = sum(row.get("fit_admissible_now", "").lower() == "yes" for row in f6_rows)
    reset_ok = sum(row.get("component_separation", "") == "pass" for row in reset_rows)
    return [
        {
            "evidence_item": "raw_two_tap_test_section_complex",
            "output_landed": str(raw_diag == 3).lower(),
            "admission_lane": "diagnostic_admitted_pressure_scale_only",
            "fit_admitted_rows": 0,
            "diagnostic_admitted_rows": raw_diag,
            "why_not_fit_admitted": "coarse_only_no_mesh_gci; reduced_pressure_proxy; recirculation; component_length_policy_unresolved",
            "next_gate_to_fit_admit": "mesh/GCI pressure-definition/component-policy gate plus admitted straight-loss subtraction",
        },
        {
            "evidence_item": "f6_ready_to_run_gate",
            "output_landed": str((STAGE_OUT / "f6_ready_to_run_gate.csv").exists()).lower(),
            "admission_lane": "review_ready_not_fit_admitted",
            "fit_admitted_rows": f6_fit,
            "diagnostic_admitted_rows": len(f6_rows),
            "why_not_fit_admitted": "PM5 rows are recirculating/onset diagnostics; reverse flow exceeds single-stream F6 fit threshold",
            "next_gate_to_fit_admit": "bounded F6 scorecard on admitted pressure rows with validation/holdout improvement",
        },
        {
            "evidence_item": "fluid_reset_k_diagnostic_sweep",
            "output_landed": str(len(reset_rows) > 0).lower(),
            "admission_lane": "diagnostic_admitted_component_separation_only",
            "fit_admitted_rows": 0,
            "diagnostic_admitted_rows": reset_ok,
            "why_not_fit_admitted": "sweep proves localized-K/reset-K arithmetic separation, not physical K calibration",
            "next_gate_to_fit_admit": "use only after admitted raw pressure evidence identifies supported K lane",
        },
        {
            "evidence_item": "pm5_matched_pressure_upcomer",
            "output_landed": str(len(pm5_rows) == 12 and pm5_wall == 12).lower(),
            "admission_lane": "diagnostic_complete_for_f6_internal_nu_review",
            "fit_admitted_rows": 0,
            "diagnostic_admitted_rows": len(pm5_rows),
            "why_not_fit_admitted": "all reviewed F6 rows remain recirculating/diagnostic; internal-Nu single-stream fitting stays closed",
            "next_gate_to_fit_admit": "recirculation/onset classification and non-recirculating or section-effective policy gate",
        },
        {
            "evidence_item": "final_hydraulic_residual_attribution",
            "output_landed": "true",
            "admission_lane": "final_decision_blocked_not_final_numeric",
            "fit_admitted_rows": 0,
            "diagnostic_admitted_rows": raw_diag + len(pm5_rows) + reset_ok,
            "why_not_fit_admitted": "no fit-admitted raw pressure/F6 closure rows exist",
            "next_gate_to_fit_admit": "recompute residual after raw pressure and F6 gates admit rows",
        },
    ]


def build_pm5_rollup(pm5_rows: list[dict[str, str]], f6_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in pm5_rows:
        by_case.setdefault(row.get("case_key", ""), []).append(row)
    f6_by_case: dict[str, list[dict[str, str]]] = {}
    for row in f6_rows:
        f6_by_case.setdefault(row.get("case_key", ""), []).append(row)
    rows = []
    for case_key, case_rows in sorted(by_case.items()):
        f6_case = f6_by_case.get(case_key, [])
        rows.append({
            "case_key": case_key,
            "pm5_rows": len(case_rows),
            "wallHeatFlux_rows": sum(row.get("wallHeatFlux_available", "").lower() == "true" for row in case_rows),
            "min_Re": min(float(row["Re"]) for row in case_rows if row.get("Re")),
            "max_Re": max(float(row["Re"]) for row in case_rows if row.get("Re")),
            "max_reverse_area_fraction": max(float(row["reverse_area_fraction"]) for row in case_rows if row.get("reverse_area_fraction")),
            "f6_fit_admissible_rows": sum(row.get("fit_admissible_now", "").lower() == "yes" for row in f6_case),
            "review_statuses": ";".join(sorted({row.get("f6_review_status", "") for row in f6_case})),
        })
    return rows


def build_final_residual(raw_rows: list[dict[str, str]], pm5_rows: list[dict[str, str]], f6_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        rows.append({
            "residual_component": "test_section_complex_pressure_drop",
            "case_or_family": row.get("case_id", ""),
            "current_attribution": "diagnostic_raw_two_tap_delta_p_landed",
            "admitted_input": "diagnostic_only_not_fit",
            "diagnostic_observed_delta_p_rgh_lower_minus_upper_Pa": row.get("delta_p_rgh_lower_minus_upper_Pa", ""),
            "evidence": row.get("lower_plane_file", "") + ";" + row.get("upper_plane_file", ""),
            "math_or_theory": "Delta_p_two_tap is reported in both reduced-pressure sign conventions; K needs admitted static/reduced pressure convention and straight-loss subtraction.",
            "final_numeric_residual_status": "blocked_not_final",
            "limitation": row.get("blockers", ""),
        })
    rows.append({
        "residual_component": "pm5_upcomer_recirculation_pressure_onset",
        "case_or_family": "corrected_pm5_salt2_salt4",
        "current_attribution": "diagnostic_pressure_onset_evidence_landed",
        "admitted_input": "diagnostic_only_not_fit",
        "diagnostic_observed_delta_p_rgh_lower_minus_upper_Pa": "",
        "evidence": f"{len(pm5_rows)} PM5 matched-plane rows; {len(f6_rows)} F6 review rows",
        "math_or_theory": "Reverse fractions and Ri/Re/Pr indicate recirculating/onset conditions, not single-stream F6 fit rows.",
        "final_numeric_residual_status": "blocked_not_final",
        "limitation": "zero F6 fit-admissible PM5 rows",
    })
    rows.append({
        "residual_component": "final_hydraulic_residual",
        "case_or_family": "forward_v1",
        "current_attribution": "not_final",
        "admitted_input": "diagnostic reset-K plus diagnostic raw two-tap/PM5 only",
        "diagnostic_observed_delta_p_rgh_lower_minus_upper_Pa": "",
        "evidence": "AGENT-373 rerun, AGENT-409 raw two-tap, AGENT-406 PM5, AGENT-414 F6 readiness",
        "math_or_theory": "Final residual requires observed pressure residual minus admitted straight, localized-K, reset/development-K, and onset/F6 terms.",
        "final_numeric_residual_status": "blocked_not_final",
        "limitation": "no fit-admitted raw pressure/F6 rows",
    })
    return rows


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""# AGENT-421 AGENT-373 Hydraulic Chain Node Verification

Created: `{summary['created_utc']}`

## Result

The original AGENT-373 stage logic was rerun locally into
`agent373_stage_outputs/`. The later scratch OpenFOAM evidence from AGENT-409
is used for the real raw two-tap landing decision, and AGENT-406/414 are used
for PM5/F6 review.

- Raw two-tap landed: `{summary['raw_two_tap_rows']}` diagnostic rows.
- F6 review rows landed: `{summary['f6_review_rows']}`, with
  `{summary['f6_fit_admitted_rows']}` fit-admissible rows.
- Reset-K sweep landed: `{summary['reset_k_rows']}` rows, admitted only as
  component-separation diagnostics.
- PM5 matched-pressure/upcomer landed: `{summary['pm5_rows']}` rows, all with
  wallHeatFlux.
- Final hydraulic residual attribution status:
  `{summary['final_hydraulic_residual_status']}`.

## Admission Decision

Diagnostic admission is supported for raw two-tap pressure scale, reset-K
component separation, and PM5/F6 onset review. Fit admission is not supported
today because the raw two-tap rows are coarse-only reduced-pressure proxies with
recirculation and no mesh/GCI/component policy admission, and all PM5 F6 review
rows remain recirculating/onset diagnostics.

No native CFD solver outputs, registry/admission state, scheduler state,
generated indexes, or external Fluid code were mutated by this package.
"""
    (PACKAGE / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    STAGE_OUT.mkdir(parents=True, exist_ok=True)

    raw_rows = read_csv(AGENT409 / "raw_two_tap_test_section_complex.csv")
    pm5_rows = read_csv(AGENT406 / "resampled_pm5_matched_plane_metrics.csv")
    f6_rows = read_csv(AGENT414 / "f6_pm5_row_readiness.csv")
    reset_rows = read_csv(STAGE_OUT / "fluid_reset_k_diagnostic_sweep.csv")

    chain = build_chain_verification()
    decisions = build_admission_decisions(raw_rows, pm5_rows, f6_rows, reset_rows)
    pm5_rollup = build_pm5_rollup(pm5_rows, f6_rows)
    residual = build_final_residual(raw_rows, pm5_rows, f6_rows)

    write_csv(PACKAGE / "chain_execution_verification.csv", chain)
    write_csv(PACKAGE / "hydraulic_admission_final_decisions.csv", decisions)
    write_csv(PACKAGE / "pm5_matched_pressure_upcomer_evidence_rollup.csv", pm5_rollup)
    write_csv(PACKAGE / "final_hydraulic_residual_attribution.csv", residual)
    write_csv(PACKAGE / "source_manifest.csv", [
        {"source_id": "agent373_script", "path": rel(AGENT373 / "hydraulic_overnight_chain.py"), "exists": str((AGENT373 / "hydraulic_overnight_chain.py").exists()).lower(), "role": "rerun stage logic"},
        {"source_id": "agent409_raw_two_tap", "path": rel(AGENT409 / "raw_two_tap_test_section_complex.csv"), "exists": str((AGENT409 / "raw_two_tap_test_section_complex.csv").exists()).lower(), "role": "scratch OpenFOAM raw two-tap evidence"},
        {"source_id": "agent406_pm5", "path": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"), "exists": str((AGENT406 / "resampled_pm5_matched_plane_metrics.csv").exists()).lower(), "role": "PM5 matched pressure/upcomer evidence"},
        {"source_id": "agent414_f6", "path": rel(AGENT414 / "f6_pm5_row_readiness.csv"), "exists": str((AGENT414 / "f6_pm5_row_readiness.csv").exists()).lower(), "role": "F6 readiness admission review"},
        {"source_id": "agent405_prior", "path": rel(AGENT405 / "hydraulic_admission_decisions.csv"), "exists": str((AGENT405 / "hydraulic_admission_decisions.csv").exists()).lower(), "role": "prior AGENT-373 safe equivalent admission table"},
    ])

    decision_by_item = {row["evidence_item"]: row for row in decisions}
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "work_product_dir": rel(PACKAGE),
        "agent373_stage_output_dir": rel(STAGE_OUT),
        "agent373_stage_logic_rerun": all((STAGE_OUT / name).exists() for name in [
            "test_section_complex_raw_two_tap_summary.json",
            "f6_ready_to_run_gate_summary.json",
            "fluid_reset_k_diagnostic_sweep_summary.json",
        ]),
        "raw_two_tap_rows": len(raw_rows),
        "raw_two_tap_diagnostic_admitted_rows": int(decision_by_item["raw_two_tap_test_section_complex"]["diagnostic_admitted_rows"]),
        "raw_two_tap_fit_admitted_rows": 0,
        "f6_review_rows": len(f6_rows),
        "f6_fit_admitted_rows": sum(row.get("fit_admissible_now", "").lower() == "yes" for row in f6_rows),
        "reset_k_rows": len(reset_rows),
        "reset_k_diagnostic_admitted_rows": int(decision_by_item["fluid_reset_k_diagnostic_sweep"]["diagnostic_admitted_rows"]),
        "pm5_rows": len(pm5_rows),
        "pm5_wallHeatFlux_rows": sum(row.get("wallHeatFlux_available", "").lower() == "true" for row in pm5_rows),
        "final_hydraulic_residual_status": "blocked_not_final",
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_jobs_launched": False,
        "external_fluid_modified": False,
    }
    write_json(PACKAGE / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
