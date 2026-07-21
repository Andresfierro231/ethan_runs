#!/usr/bin/env python3
"""Build AGENT-405 hydraulic node-run admission package.

The AGENT-373 diagnostic stages are executed directly on the compute node into
this package before this builder is run. This builder does not mutate native
CFD outputs or central registry/admission state; it records derived admission
decisions for the forward-v1 gate.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run"
HYD_OUT = OUT / "hydraulic_node_run_outputs"
PM5 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_matched_plane_parser_repair"
AG393 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_hydraulic_unblock_plan_execution"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def count_rows(path: Path) -> int:
    return len(read_csv(path))


def build_stage_rows() -> list[dict[str, Any]]:
    stage_files = [
        ("raw_two_tap", HYD_OUT / "test_section_complex_raw_two_tap_status.csv"),
        ("f6_gate", HYD_OUT / "f6_ready_to_run_gate.csv"),
        ("reset_k_sweep", HYD_OUT / "fluid_reset_k_diagnostic_sweep.csv"),
    ]
    rows = []
    for stage_id, path in stage_files:
        summary = read_json(HYD_OUT / f"{path.stem}_summary.json")
        rows.append(
            {
                "stage_id": stage_id,
                "path": rel(path),
                "exists": str(path.exists()).lower(),
                "row_count": count_rows(path),
                "stage_status": summary.get("status", "missing_summary"),
                "hostname": summary.get("hostname", ""),
                "admission_use": {
                    "raw_two_tap": "preflight_only_not_admitted",
                    "f6_gate": "gate_status_not_admitted",
                    "reset_k_sweep": "diagnostic_admitted_for_component_separation_only",
                }[stage_id],
            }
        )
    return rows


def build_admission_rows() -> list[dict[str, Any]]:
    pm5_summary = read_json(PM5 / "summary.json")
    pm5_rows = read_csv(PM5 / "repaired_pm5_matched_plane_metrics.csv")
    repaired_ready = [
        row
        for row in pm5_rows
        if row.get("admission_status") == "ready_for_f6_pressure_onset_review_not_internal_nu"
    ]
    raw_rows = read_csv(HYD_OUT / "test_section_complex_raw_two_tap_status.csv")
    reset_rows = read_csv(HYD_OUT / "fluid_reset_k_diagnostic_sweep.csv")
    reset_pass = bool(reset_rows) and all(row.get("component_separation") == "pass" for row in reset_rows)
    return [
        {
            "gate_item": "test_section_complex_raw_two_tap",
            "landed": bool(raw_rows),
            "admission_status": "blocked_not_admitted",
            "evidence": f"{len(raw_rows)} safe preflight rows landed, but no raw two-tap pressure extraction was run.",
            "why": "Available raw extractor mutates OpenFOAM controlDict/postProcessing in case trees; native CFD outputs are read-only.",
            "next_to_admit": "Run staged-copy raw two-tap extraction with all writes confined to scratch/work_products, then compare taps.",
        },
        {
            "gate_item": "f6_ready_to_run_gate",
            "landed": (HYD_OUT / "f6_ready_to_run_gate.csv").exists(),
            "admission_status": "blocked_not_admitted",
            "evidence": "F6 gate refresh landed, but matched-pressure/upcomer evidence is incomplete and no F6 row is fit-admitted.",
            "why": "Only partial PM5 evidence exists; corrected-Q/F6 split policy and full upcomer metrics are not ready.",
            "next_to_admit": "Repair PM5 resampling for missing fields and rerun F6 gate with admitted pressure/onset evidence.",
        },
        {
            "gate_item": "fluid_reset_k_diagnostic_sweep",
            "landed": bool(reset_rows),
            "admission_status": "diagnostic_admitted_component_separation_only" if reset_pass else "blocked",
            "evidence": f"{len(reset_rows)} reset-K/localized-K rows landed; component separation pass={reset_pass}.",
            "why": "Rows verify API separation and pressure-charge arithmetic only; they do not fit hydraulic K.",
            "next_to_admit": "Use as diagnostic support when raw pressure evidence lands; do not calibrate from it alone.",
        },
        {
            "gate_item": "pm5_matched_pressure_upcomer",
            "landed": bool(pm5_rows),
            "admission_status": "partial_not_final_admitted",
            "evidence": (
                f"{len(repaired_ready)}/{len(pm5_rows)} rows ready for F6 pressure/onset review; "
                f"wallHeatFlux rows={pm5_summary.get('wallHeatFlux_rows', 0)}."
            ),
            "why": "Salt2-lo5q rows are repaired, but Salt2-hi5q/Salt4 rows need resampling; wallHeatFlux is absent.",
            "next_to_admit": "Run scratch-case PM5 resampling after fixing disabled system/functions include and wallHeatFlux context.",
        },
        {
            "gate_item": "final_hydraulic_residual_attribution",
            "landed": True,
            "admission_status": "provisional_attribution_only",
            "evidence": "Attribution table generated from landed diagnostic evidence.",
            "why": "Raw two-tap and full PM5/F6 evidence are not admitted, so residual magnitudes cannot be final.",
            "next_to_admit": "Recompute after raw two-tap and PM5/F6 gates have admitted rows.",
        },
    ]


def build_residual_rows() -> list[dict[str, Any]]:
    pm5_rows = read_csv(PM5 / "repaired_pm5_matched_plane_metrics.csv")
    ready_rows = [
        row
        for row in pm5_rows
        if row.get("admission_status") == "ready_for_f6_pressure_onset_review_not_internal_nu"
    ]
    if ready_rows:
        reverse_area = "; ".join(
            f"{row['case_key']}:{row['plane_location']} reverse_area={row.get('reverse_area_fraction', '')}"
            for row in ready_rows
        )
        reverse_mass = "; ".join(
            f"{row['case_key']}:{row['plane_location']} reverse_mass={row.get('reverse_mass_fraction', '')}"
            for row in ready_rows
        )
    else:
        reverse_area = ""
        reverse_mass = ""

    return [
        {
            "residual_component": "test_section_complex_pressure_drop",
            "current_attribution": "unassigned_blocked",
            "admitted_input": "none",
            "evidence": "Raw two-tap stage landed preflight rows only.",
            "math_or_model": "Delta_p_two_tap = p_upstream - p_downstream over the staged test-section tap pair.",
            "limitation": "No raw tap pressures were extracted in a scratch-safe way.",
            "next_action": "Run staged-copy raw two-tap extractor.",
        },
        {
            "residual_component": "reset_development_vs_localized_k",
            "current_attribution": "diagnostic_component_separation_supported",
            "admitted_input": "reset-K diagnostic sweep only",
            "evidence": "128 rows separate localized_fixed_k and reset_development_k pressure charges.",
            "math_or_model": "Delta_p_named = (K_localized + K_reset) * q_dynamic with q_dynamic=0.2 Pa in the diagnostic sweep.",
            "limitation": "This proves implementation separation, not fitted K values.",
            "next_action": "Use after raw pressure evidence identifies which K lane is physically supported.",
        },
        {
            "residual_component": "pm5_upcomer_recirculation_pressure_onset",
            "current_attribution": "partial_salt2_lo5q_only",
            "admitted_input": "none_final; partial F6/onset review evidence",
            "evidence": reverse_area + " | " + reverse_mass,
            "math_or_model": "Reverse area/mass fractions and Ri/Re/Pr indicate recirculation/onset regime at matched planes.",
            "limitation": "Only 3/12 PM5 rows have full U/rho/T/Re/Pr/Ri/Gr/Ra; no wallHeatFlux.",
            "next_action": "Resample missing PM5 cases and repair wallHeatFlux before internal-Nu or final F6 admission.",
        },
        {
            "residual_component": "f6_re_variation_hydraulic_closure",
            "current_attribution": "blocked",
            "admitted_input": "none",
            "evidence": "F6 gate status remains blocked_or_unproven / blocked_or_pending.",
            "math_or_model": "F6 should score pressure residuals under bounded Re/phi perturbation without global K multiplier.",
            "limitation": "Perturbation rows are not admitted as independent training expansion.",
            "next_action": "Refresh F6 after corrected-Q/PM5 admitted rows land.",
        },
        {
            "residual_component": "final_hydraulic_residual",
            "current_attribution": "not_final",
            "admitted_input": "diagnostic reset-K component separation only",
            "evidence": "Raw two-tap and PM5/F6 gates remain not final admitted.",
            "math_or_model": "Final residual should decompose total pressure error into raw test-section, distributed/reset-K, PM5/onset, and remaining model-form terms.",
            "limitation": "Cannot assign final residual magnitudes without admitted pressure extractions.",
            "next_action": "Run scratch raw two-tap and PM5 resampling, then rebuild final attribution.",
        },
    ]


def build_pm5_run_rows() -> list[dict[str, Any]]:
    requirements = read_csv(PM5 / "pm5_resample_requirements.csv")
    rows = []
    for row in requirements:
        rows.append(
            {
                "case_key": row.get("case_key", ""),
                "current_status": (
                    "partial_repaired_pressure_onset_evidence"
                    if row.get("case_key") == "salt2_lo5q"
                    else "requires_resampling"
                ),
                "missing_plane_field_rows": row.get("missing_plane_field_rows", ""),
                "missing_wallHeatFlux_rows": row.get("missing_wallHeatFlux_rows", ""),
                "run_decision": (
                    "do_not_rerun_plane_now_wallHeatFlux_still_missing"
                    if row.get("case_key") == "salt2_lo5q"
                    else "rerun_scratch_resampling_after_controlDict_functions_fix"
                ),
                "reason": row.get("required_action", ""),
            }
        )
    return rows


def build_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "hydraulic_h1_f6",
            "opens_when": "raw two-tap pressure extraction lands from staged copies and PM5/F6 rows are complete enough for pressure/onset review",
            "current_status": "closed",
            "current_evidence": "AGENT-405 node diagnostics landed but raw two-tap is preflight-only and F6 is blocked.",
        },
        {
            "gate": "pm5_matched_pressure_upcomer",
            "opens_when": "all Salt2/Salt4 +/-5Q PM5 plane rows have U/rho/T/Re/Pr/Ri/Gr/Ra; wallHeatFlux is optional for pressure/onset but required for internal Nu",
            "current_status": "partial",
            "current_evidence": "3/12 rows ready for F6 pressure/onset review; 0 wallHeatFlux rows.",
        },
        {
            "gate": "internal_nu",
            "opens_when": "matched-plane onset candidates plus wall-band wallHeatFlux and wall/bulk temperature rows are complete and admitted",
            "current_status": "closed",
            "current_evidence": "wallHeatFlux missing in all PM5 rows.",
        },
        {
            "gate": "closure_qoi_mesh_gci",
            "opens_when": "same closure QOI is available on admitted coarse/medium/fine mesh family rows with uncertainty calculation",
            "current_status": "closed",
            "current_evidence": "No new GCI evidence generated by this node run.",
        },
        {
            "gate": "final_forward_v1_scorecard",
            "opens_when": "hydraulic, PM5/upcomer, HX/BC, sensor policy, and closure uncertainty gates all provide admitted rows",
            "current_status": "closed",
            "current_evidence": "Only diagnostic/component-separation rows newly admitted here.",
        },
    ]


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_rows = build_stage_rows()
    admission_rows = build_admission_rows()
    residual_rows = build_residual_rows()
    pm5_rows = build_pm5_run_rows()
    gate_rows = build_gate_rows()

    write_csv(
        output_dir / "hydraulic_node_stage_outputs.csv",
        stage_rows,
        ["stage_id", "path", "exists", "row_count", "stage_status", "hostname", "admission_use"],
    )
    write_csv(
        output_dir / "hydraulic_admission_decisions.csv",
        admission_rows,
        ["gate_item", "landed", "admission_status", "evidence", "why", "next_to_admit"],
    )
    write_csv(
        output_dir / "final_hydraulic_residual_attribution.csv",
        residual_rows,
        [
            "residual_component",
            "current_attribution",
            "admitted_input",
            "evidence",
            "math_or_model",
            "limitation",
            "next_action",
        ],
    )
    write_csv(
        output_dir / "pm5_matched_pressure_upcomer_run_decision.csv",
        pm5_rows,
        ["case_key", "current_status", "missing_plane_field_rows", "missing_wallHeatFlux_rows", "run_decision", "reason"],
    )
    write_csv(
        output_dir / "gate_opening_criteria.csv",
        gate_rows,
        ["gate", "opens_when", "current_status", "current_evidence"],
    )
    write_csv(
        output_dir / "source_manifest.csv",
        [
            {"source_id": "AGENT-373-script", "path": rel(ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_overnight_dependent_chain/hydraulic_overnight_chain.py"), "use": "direct local diagnostic stage execution"},
            {"source_id": "AGENT-405-hydraulic-node-outputs", "path": rel(HYD_OUT), "use": "landed raw/F6/reset-K outputs"},
            {"source_id": "AGENT-404-pm5", "path": rel(PM5), "use": "PM5 parser repair and resampling requirements"},
            {"source_id": "AGENT-393-sensor-hydraulic", "path": rel(AG393), "use": "prior hydraulic/sensor policy context"},
        ],
        ["source_id", "path", "use"],
    )

    reset_rows = count_rows(HYD_OUT / "fluid_reset_k_diagnostic_sweep.csv")
    raw_rows = count_rows(HYD_OUT / "test_section_complex_raw_two_tap_status.csv")
    pm5_summary = read_json(PM5 / "summary.json")
    summary = {
        "task": "AGENT-405",
        "date": "2026-07-15",
        "hostname": "c318-008.ls6.tacc.utexas.edu",
        "raw_two_tap_rows": raw_rows,
        "raw_two_tap_admission": "blocked_preflight_only",
        "f6_gate_admission": "blocked_not_admitted",
        "reset_k_rows": reset_rows,
        "reset_k_admission": "diagnostic_admitted_component_separation_only",
        "pm5_metric_rows": pm5_summary.get("metric_rows", 0),
        "pm5_wallHeatFlux_rows": pm5_summary.get("wallHeatFlux_rows", 0),
        "pm5_pressure_onset_status": "partial_not_final",
        "final_hydraulic_residual_attribution": "provisional_not_final",
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "native_solver_outputs_mutated": False,
        "registry_or_admission_state_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "scheduler_mutated": False,
        "openfoam_solver_launched": False,
        "local_openfoam_postprocessing_launched_by_agent405": False,
    }
    write_json(output_dir / "summary.json", summary)

    readme = """# Sensor Policy Gate Opening And Hydraulic Node Run

Date: 2026-07-15

Task: AGENT-405

## Result

The three safe AGENT-373 diagnostic stages were run directly on compute node
`c318-008` into this package:

- `test_section_complex_raw_two_tap`: 3 preflight rows landed.
- `f6_ready_to_run_gate`: 4 gate rows landed.
- `fluid_reset_k_diagnostic_sweep`: 128 diagnostic rows landed.

Only the reset-K/localized-K component-separation sweep is admitted, and only
as diagnostic implementation evidence. Raw two-tap pressure extraction is not
admitted because the available extractor would mutate OpenFOAM case state.
F6 is not admitted because PM5 matched-pressure/upcomer evidence is incomplete.

## PM5 Evidence

AGENT-404 repaired the parser and recovered 3/12 PM5 rows for Salt2-lo5q
pressure/onset review. The other 9 rows require scratch-case resampling with
`rho/Re/Pr/Ri/Gr/Ra`; all 12 rows lack wallHeatFlux, so internal-Nu remains
blocked.

The previous PM5 scratch run failed to reconstruct full fields for the
incomplete cases because `controlDict` still included a disabled/missing
`system/functions` file. Do not call final F6 or internal-Nu admission until
that scratch resampling path is repaired and rerun.

## Residual Attribution

`final_hydraulic_residual_attribution.csv` is provisional. It documents where
the hydraulic residual can currently be assigned and where it remains blocked:

- test-section complex pressure drop: blocked pending staged raw two-tap.
- reset/development K separation: diagnostic-supported, not fit-admitted.
- PM5 upcomer recirculation/onset: partial Salt2-lo5q evidence only.
- F6 Re/phi closure: blocked.
- final hydraulic residual: not final.

## Guardrails

No native CFD solver outputs, registry/admission state, generated indexes, or
external `../cfd-modeling-tools` files were mutated. AGENT-405 did not launch
OpenFOAM solver or postprocessing; it consumed AGENT-404 PM5 evidence and ran
repo-local diagnostics only.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    return summary


def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
