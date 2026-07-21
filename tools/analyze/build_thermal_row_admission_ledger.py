#!/usr/bin/env python3
"""Build AGENT-391/392 thermal row admission/use ledger."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger"

AG391 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run"
AG392 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue"
AG319 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate"
AG330 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"


INPUTS = {
    "ag392_hx_primary": AG392 / "results/predictive_hx_fit_setup_only_refresh/hx_primary_forward_scores.csv",
    "ag392_hx_violations": AG392 / "results/predictive_hx_fit_setup_only_refresh/violations.csv",
    "ag391_cooler_summary": AG391 / "setup_only_cooler_closure_bakeoff/cooler_rmse_summary_with_leakage_policy.csv",
    "ag391_test_section": AG391 / "test_section_boundary_form_bakeoff/test_section_model_result_ledger.csv",
    "ag392_source_sink": AG392 / "results/external_bc_thermal_profile_parity_refresh/source_sink_parity_contract.csv",
    "ag392_external_decisions": AG392 / "results/external_bc_thermal_profile_parity_refresh/admission_decision_table.csv",
    "ag319_internal_nu_gate": AG319 / "thermal_admission_internal_nu_final_gate.csv",
    "ag319_segment_summary": AG319 / "segment_thermal_fit_summary.csv",
    "ag319_summary": AG319 / "summary.json",
    "ag330_upcomer_admissibility": AG330 / "README.md",
}


LEDGER_FIELDS = [
    "row_id",
    "row_family",
    "source_agent",
    "source_artifact",
    "case_id",
    "split_role",
    "model_form",
    "mode_or_role",
    "admission_class",
    "forward_v1_use",
    "runtime_inputs_allowed",
    "runtime_inputs_forbidden",
    "fit_source",
    "score_source",
    "key_metric_1",
    "key_metric_2",
    "key_metric_3",
    "blocker",
    "next_action",
    "source_path",
]


FAMILY_FILES = {
    "final_predictive_hx_closure": "final_predictive_hx_closure_rows.csv",
    "fitted_internal_nu": "fitted_internal_nu_rows.csv",
    "realized_wallheatflux_replay": "realized_wallheatflux_replay_rows.csv",
    "imposed_cooler_duty": "imposed_cooler_duty_rows.csv",
    "diagnostic_test_section_negative_source": "diagnostic_test_section_negative_source_rows.csv",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str] = LEDGER_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row(**kwargs: str) -> dict[str, str]:
    out = {field: "" for field in LEDGER_FIELDS}
    out.update(kwargs)
    return out


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def build_final_hx_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    hx_path = INPUTS["ag392_hx_primary"]
    for src in read_csv(hx_path):
        rows.append(
            row(
                row_id=f"AG392_HX1_{src['variant_id']}_{src['case_id']}",
                row_family="final_predictive_hx_closure",
                source_agent="AGENT-392",
                source_artifact="predictive_hx_fit_setup_only_refresh/hx_primary_forward_scores.csv",
                case_id=src["case_id"],
                split_role=src["fit_role"],
                model_form=f"{src['variant_id']}::{src['model_form_id']}",
                mode_or_role=src["root_status"],
                admission_class="predictive_candidate_pending_final_gate",
                forward_v1_use="candidate_scorecard_input_after_hydraulic_cfd_pp_runtime_audit_gates",
                runtime_inputs_allowed="setup-only HX scalar fitted on declared training row; model-predicted cooler duty",
                runtime_inputs_forbidden="held-out CFD cooler duty; realized wallHeatFlux; validation or holdout temperatures at runtime",
                fit_source="Salt2 train row only under declared Salt2/Salt3/Salt4 split",
                score_source=f"{src['fit_role']} score row; target cooler used for scoring only",
                key_metric_1=f"qhx_error_W={src['qhx_error_W']}",
                key_metric_2=f"Tmean_error_K={src['Tmean_error_vs_cfd_K']}",
                key_metric_3=f"mdot_error_kg_s={src['mdot_error_vs_cfd_kg_s']}",
                blocker="final forward-v1 still waits on hydraulic, cfd-pp, PM5/upcomer, and admission gates",
                next_action="use as candidate only in next final-scorecard gate package; do not label final",
                source_path=rel(hx_path),
            )
        )

    cooler_path = INPUTS["ag391_cooler_summary"]
    setup_legal_forms = {"current_fluid_airside_hx_fixed_mdot", "salt2_fit_constant_UA_bulk_drive"}
    for src in read_csv(cooler_path):
        if src["model_form"] not in setup_legal_forms:
            continue
        rows.append(
            row(
                row_id=f"AG391_COOLER_SETUP_{src['model_form']}_{src['scope']}",
                row_family="final_predictive_hx_closure",
                source_agent="AGENT-391",
                source_artifact="setup_only_cooler_closure_bakeoff/cooler_rmse_summary_with_leakage_policy.csv",
                case_id=src["scope"],
                split_role=src["scope"],
                model_form=src["model_form"],
                mode_or_role=src["fit_policy"],
                admission_class="setup_legal_candidate_pending_final_gate",
                forward_v1_use="candidate_comparison_row_for_hx_lane_selection",
                runtime_inputs_allowed="setup/current Fluid model inputs; Salt2-only scalar fit for salt2_fit_constant_UA_bulk_drive",
                runtime_inputs_forbidden="realized CFD cooler duty at predictive runtime; validation or holdout refit",
                fit_source=src["fit_policy"],
                score_source=src["scope"],
                key_metric_1=f"rmse_W={src['rmse_W']}",
                key_metric_2=f"mae_W={src['mae_W']}",
                key_metric_3=f"mean_error_W={src['mean_error_W']}",
                blocker="candidate screen only; final forward-v1 gates not complete",
                next_action="compare against AGENT-392 HX1 and select one setup-legal lane",
                source_path=rel(cooler_path),
            )
        )
    return rows


def build_internal_nu_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    summary_path = INPUTS["ag319_segment_summary"]
    for src in read_csv(summary_path):
        rows.append(
            row(
                row_id=f"INTERNAL_NU_ZERO_FIT_{src['segment']}",
                row_family="fitted_internal_nu",
                source_agent="AGENT-319/AGENT-330",
                source_artifact="thermal_admission_internal_nu_final_gate + upcomer_recirculation_internal_nu_admissibility",
                case_id=src["segment"],
                split_role="not_applicable_zero_fit_set",
                model_form="internal_Nu_fit",
                mode_or_role=src["segment_decision"],
                admission_class="blocked_empty_fit_set",
                forward_v1_use="no_internal_nu_fit_use_baseline_or_literature_only",
                runtime_inputs_allowed="baseline/literature/default internal Nu only",
                runtime_inputs_forbidden="fitted internal Nu; Nu absorbing heater/cooler/passive/radiation/recirculation residuals",
                fit_source=f"fit_eligible_qoi_count={src['fit_eligible_qoi_count']}",
                score_source=f"validation_only_qoi_count={src['validation_only_qoi_count']}; blocked_qoi_count={src['blocked_qoi_count']}",
                key_metric_1=f"segment_decision={src['segment_decision']}",
                key_metric_2=f"fit_allowed={src['forward_v1_internal_nu_fit_allowed']}",
                key_metric_3="current_fit_admissible_rows=0",
                blocker=src["dominant_blockers"],
                next_action="reopen only after matched-plane thermal/vector extraction, onset anchors, and mesh/time uncertainty",
                source_path=f"{rel(summary_path)};{rel(INPUTS['ag330_upcomer_admissibility'])}",
            )
        )
    return rows


def build_wallheatflux_replay_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = INPUTS["ag392_source_sink"]
    for src in read_csv(path):
        rows.append(
            row(
                row_id=f"WALLHEATFLUX_REPLAY_{src['case_id']}_{src['one_d_segment']}_{src['role']}",
                row_family="realized_wallheatflux_replay",
                source_agent="AGENT-392",
                source_artifact="external_bc_thermal_profile_parity_refresh/source_sink_parity_contract.csv",
                case_id=src["case_id"],
                split_role="diagnostic_replay",
                model_form="realized_CFD_wallHeatFlux_replay",
                mode_or_role=f"{src['one_d_segment']}::{src['role']}",
                admission_class="diagnostic_replay_not_predictive",
                forward_v1_use="residual_attribution_and_sign_radiation_policy_only",
                runtime_inputs_allowed="realized wallHeatFlux only in explicitly labeled diagnostic replay",
                runtime_inputs_forbidden="predictive runtime wallHeatFlux replay; separate radiation add-on",
                fit_source="not_fit_row",
                score_source="CFD realized wallHeatFlux readback",
                key_metric_1=f"imposed_Q_W={src['imposed_Q_W']}",
                key_metric_2=f"realized_wallHeatFlux_W={src['realized_wallHeatFlux_W']}",
                key_metric_3=f"realized_minus_imposed_W={src['realized_minus_imposed_W']}",
                blocker="realized CFD wallHeatFlux contains inseparable rcExternalTemperature radiation; replay is leakage if used predictively",
                next_action="use to localize residuals and verify sign policy; keep out of final predictive runtime",
                source_path=rel(path),
            )
        )
    return rows


def build_imposed_cooler_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = INPUTS["ag391_cooler_summary"]
    leakage_forms = {"imposed_cfd_cooler_upper_bound", "salt2_fit_cooler_imposed_ratio"}
    for src in read_csv(path):
        if src["model_form"] not in leakage_forms:
            continue
        rows.append(
            row(
                row_id=f"IMPOSED_COOLER_{src['model_form']}_{src['scope']}",
                row_family="imposed_cooler_duty",
                source_agent="AGENT-391",
                source_artifact="setup_only_cooler_closure_bakeoff/cooler_rmse_summary_with_leakage_policy.csv",
                case_id=src["scope"],
                split_role=src["scope"],
                model_form=src["model_form"],
                mode_or_role=src["fit_policy"],
                admission_class="diagnostic_upper_bound_or_leakage_warning",
                forward_v1_use="upper_bound_or_leakage_warning_only",
                runtime_inputs_allowed="none for final predictive runtime",
                runtime_inputs_forbidden="imposed CFD cooler duty; realized CFD cooler duty; cooler-duty ratio derived from imposed/CFD evidence",
                fit_source=src["fit_policy"],
                score_source=src["scope"],
                key_metric_1=f"rmse_W={src['rmse_W']}",
                key_metric_2=f"mae_W={src['mae_W']}",
                key_metric_3=f"runtime_leakage_class={src['runtime_leakage_class']}",
                blocker="uses imposed or CFD cooler information and is not setup-predictive",
                next_action="retain as diagnostic bound; exclude from final predictive HX closure",
                source_path=rel(path),
            )
        )
    return rows


def build_negative_source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path = INPUTS["ag391_test_section"]
    for src in read_csv(path):
        if src["mode_id"] != "negative_source_compatibility":
            continue
        rows.append(
            row(
                row_id=f"TEST_SECTION_NEG_SOURCE_{src['case_id']}",
                row_family="diagnostic_test_section_negative_source",
                source_agent="AGENT-391",
                source_artifact="test_section_boundary_form_bakeoff/test_section_model_result_ledger.csv",
                case_id=src["case_id"],
                split_role=src["split"],
                model_form=src["mode_id"],
                mode_or_role=src["admission_use_class"],
                admission_class="diagnostic_boundary_form_screen",
                forward_v1_use="residual_localization_only",
                runtime_inputs_allowed="explicitly labeled diagnostic compatibility source only",
                runtime_inputs_forbidden="physical test-section boundary proof; final predictive source/sink closure",
                fit_source="not_fit_row",
                score_source=src["split"],
                key_metric_1=f"Tmean_error_K={src['Tmean_error_K']}",
                key_metric_2=f"mdot_error_pct={src['mdot_error_pct']}",
                key_metric_3=f"qambient_total_W={src['qambient_total_W']}",
                blocker="negative source is mathematical compatibility evidence, not a physical boundary condition",
                next_action="BC-modeling must admit a physical test-section boundary form before predictive use",
                source_path=rel(path),
            )
        )
    return rows


def build_all() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(build_final_hx_rows())
    rows.extend(build_internal_nu_rows())
    rows.extend(build_wallheatflux_replay_rows())
    rows.extend(build_imposed_cooler_rows())
    rows.extend(build_negative_source_rows())
    return rows


def write_summary(out_dir: Path, rows: list[dict[str, str]]) -> None:
    families = Counter(r["row_family"] for r in rows)
    classes = Counter(r["admission_class"] for r in rows)
    summary = {
        "task": "AGENT-423",
        "row_count": len(rows),
        "family_counts": dict(sorted(families.items())),
        "admission_class_counts": dict(sorted(classes.items())),
        "final_predictive_rows_admitted": 0,
        "fitted_internal_nu_rows_admitted": 0,
        "runtime_cfd_duty_leakage_rows_admitted": 0,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_state_mutated": False,
        "generated_index_refreshed": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def write_family_summary(out_dir: Path, rows: list[dict[str, str]]) -> None:
    grouped: dict[tuple[str, str], int] = Counter((r["row_family"], r["admission_class"]) for r in rows)
    out_rows = [
        {
            "row_family": family,
            "admission_class": admission_class,
            "row_count": count,
        }
        for (family, admission_class), count in sorted(grouped.items())
    ]
    write_csv(out_dir / "row_family_summary.csv", out_rows, ["row_family", "admission_class", "row_count"])


def write_source_manifest(out_dir: Path) -> None:
    rows = []
    for name, path in INPUTS.items():
        rows.append(
            {
                "source_id": name,
                "path": rel(path),
                "exists": str(path.exists()).lower(),
                "role": "read_only_input",
            }
        )
    write_csv(out_dir / "source_manifest.csv", rows, ["source_id", "path", "exists", "role"])


def write_readme(out_dir: Path, rows: list[dict[str, str]]) -> None:
    family_counts = Counter(r["row_family"] for r in rows)
    text = f"""---
provenance:
  task: AGENT-423
  generated_by: codex
tags: [forward-pred, thermal-rows, hx, internal-nu, wallheatflux, diagnostics]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_overnight_compute_node_rescue/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
---
# Thermal Row Admission Ledger

Date: 2026-07-15

Task: AGENT-423

## Result

This package implements the requested AGENT-391/AGENT-392 thermal row plan as
a canonical row ledger. It separates setup-legal predictive candidates from
diagnostic replay/leakage rows and from currently blocked fitted internal-Nu
rows.

No row is newly promoted to final forward-v1 admission in this package.

## Counts

- Canonical ledger rows: {len(rows)}
- Final predictive HX candidate rows: {family_counts['final_predictive_hx_closure']}
- Fitted internal-Nu rows: {family_counts['fitted_internal_nu']} blocker rows, `0` admitted fits
- Realized wallHeatFlux replay rows: {family_counts['realized_wallheatflux_replay']}
- Imposed cooler duty rows: {family_counts['imposed_cooler_duty']}
- Diagnostic test-section negative-source rows: {family_counts['diagnostic_test_section_negative_source']}

## Files

- `thermal_row_admission_ledger.csv`: canonical row ledger.
- `final_predictive_hx_closure_rows.csv`: setup-legal HX/cooler candidates, still pending final gates.
- `fitted_internal_nu_rows.csv`: explicit zero-fit internal-Nu blocker rows.
- `realized_wallheatflux_replay_rows.csv`: diagnostic replay rows only.
- `imposed_cooler_duty_rows.csv`: diagnostic upper-bound/leakage rows only.
- `diagnostic_test_section_negative_source_rows.csv`: test-section compatibility rows only.
- `row_family_summary.csv`, `source_manifest.csv`, `summary.json`.

## Guardrails

- Realized CFD wallHeatFlux and imposed/CFD cooler duty are never predictive runtime inputs.
- Internal Nu remains closed for fitting: current fit-admissible rows are zero.
- Negative test-section source rows are mathematical residual probes, not physical boundary-condition proof.
- Final predictive HX rows remain candidates until hydraulic, cfd-pp, runtime-input, and final scorecard gates admit them.
"""
    (out_dir / "README.md").write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = [str(path) for path in INPUTS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing inputs: " + ", ".join(missing))

    rows = build_all()
    write_csv(out_dir / "thermal_row_admission_ledger.csv", rows)
    for family, filename in FAMILY_FILES.items():
        write_csv(out_dir / filename, [r for r in rows if r["row_family"] == family])
    write_family_summary(out_dir, rows)
    write_source_manifest(out_dir)
    write_summary(out_dir, rows)
    write_readme(out_dir, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
