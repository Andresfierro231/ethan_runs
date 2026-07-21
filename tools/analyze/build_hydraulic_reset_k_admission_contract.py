#!/usr/bin/env python3
"""Build hydraulic reset/K admission contract tables from existing evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_reset_k_admission_contract"

RESET_MAP = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv"
NAMED_LOSSES = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv"
MINOR_TWO_TAP = REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv"
PRESSURE_LEDGER = REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv"
H1_GAP = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_h1_faithful_gap_and_f6_decision/h1_faithful_implementation_gap_table.csv"
F6_DECISION = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_h1_faithful_gap_and_f6_decision/f6_candidate_decision_table.csv"
CORRECTED_Q_SUMMARY = REPO_ROOT / "work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/summary.json"


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, fieldnames: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _boolish(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _has_flag(row: Dict[str, str], flag: str) -> bool:
    return flag in row.get("quality_flags", "")


def _reset_admission(row: Dict[str, str]) -> str:
    flags = row.get("quality_flags", "")
    status = row.get("hydraulic_reset_status", "")
    if "recirculation" in flags:
        return "diagnostic_only_recirculation_invalid"
    if "reset_flagged" in status or "feature_reset_assumed" in status:
        return "candidate_blocked_api_and_mesh_admission"
    if "not_flagged" in status:
        return "reference_not_reset_candidate"
    return "blocked_unclassified_reset_status"


def _reset_action(admission_status: str) -> str:
    if admission_status == "candidate_blocked_api_and_mesh_admission":
        return "Implement first-class reset/development term keyed by feature, downstream span, x/D, Re, and mesh-admitted pressure evidence."
    if admission_status == "diagnostic_only_recirculation_invalid":
        return "Keep as recirculation diagnostic; do not convert to single-stream universal f or K."
    if admission_status == "reference_not_reset_candidate":
        return "Retain as downstream reference span; no reset term admitted from current evidence."
    return "Audit hydraulic_reset_status before using this row."


def _k_admission(row: Dict[str, str]) -> str:
    flags = row.get("quality_flags", "")
    if "downstream_span_recirculation_invalid_single_stream" in flags or row.get("recirculation_adjacent_spans"):
        return "diagnostic_only_recirculation_adjacent"
    if "tap_length_proxy_abs_dz_not_centerline_length" in flags or "K_local_still_upper_bound" in flags:
        return "blocked_tap_length_upper_bound"
    if "coarse_no_gci" in flags:
        return "diagnostic_only_coarse_no_gci"
    if _boolish(row.get("fit_eligible", "")):
        return "candidate_fit_admissible"
    if _boolish(row.get("validation_eligible", "")):
        return "validation_only_not_fit"
    return "blocked_not_fit_or_validation_eligible"


def _k_action(admission_status: str) -> str:
    if admission_status == "candidate_fit_admissible":
        return "May enter bounded fit only after matching train/validation/holdout rules and no thermal fitting."
    if admission_status == "validation_only_not_fit":
        return "Use for no-refit diagnostics only."
    if admission_status == "diagnostic_only_recirculation_adjacent":
        return "Exclude from universal component K fitting; preserve as recirculation/branch diagnostic."
    if admission_status == "blocked_tap_length_upper_bound":
        return "Extract true centerline tap-to-tap length and recompute straight-loss subtraction before fitting."
    if admission_status == "diagnostic_only_coarse_no_gci":
        return "Require mesh-family/GCI pressure evidence before admission."
    return "Do not use until row status is audited."


def _tap_gap_type(row: Dict[str, str]) -> str:
    flags = row.get("quality_flags", "")
    gap_types: List[str] = []
    if "tap_length_proxy_abs_dz_not_centerline_length" in flags:
        gap_types.append("centerline_tap_length_missing")
    if "K_local_still_upper_bound" in flags:
        gap_types.append("K_local_upper_bound")
    if "coarse_no_gci" in flags:
        gap_types.append("mesh_gci_missing")
    if "recirculation" in flags or row.get("recirculation_adjacent_spans"):
        gap_types.append("recirculation_single_stream_invalid")
    return ";".join(gap_types) if gap_types else "none"


def _tap_priority(gap_type: str) -> str:
    if "recirculation_single_stream_invalid" in gap_type:
        return "P0_exclude_from_universal_fit"
    if "centerline_tap_length_missing" in gap_type or "K_local_upper_bound" in gap_type:
        return "P1_required_for_component_K"
    if "mesh_gci_missing" in gap_type:
        return "P2_required_for_publication_admission"
    return "P3_reference_only"


def _build_reset_contract(reset_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for index, row in enumerate(reset_rows, start=1):
        admission = _reset_admission(row)
        rows.append(
            {
                "contract_id": f"RESET-{index:03d}",
                "source_id": row.get("source_id", ""),
                "case_id": row.get("case_id", ""),
                "reset_feature": row.get("feature_or_span", ""),
                "reset_type": row.get("reset_type", ""),
                "downstream_span": row.get("downstream_span", ""),
                "orientation": row.get("orientation", ""),
                "x_from_reset_m": row.get("x_from_reset_m", ""),
                "L_over_D_from_reset": row.get("L_over_D_from_reset", ""),
                "thermal_reset_status": row.get("thermal_reset_status", ""),
                "hydraulic_reset_status": row.get("hydraulic_reset_status", ""),
                "recirculation_flag": "yes" if "recirculation" in row.get("quality_flags", "") else "no",
                "admission_status": admission,
                "fluid_api_requirement": "first_class_reset_development_term",
                "required_next_action": _reset_action(admission),
                "source_path": row.get("source_path", ""),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    return rows


def _build_component_k_table(minor_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for index, row in enumerate(minor_rows, start=1):
        admission = _k_admission(row)
        rows.append(
            {
                "k_row_id": f"K-{index:03d}",
                "join_key": row.get("join_key", ""),
                "source_id": row.get("source_id", ""),
                "case_id": row.get("case_id", ""),
                "feature": row.get("feature", ""),
                "feature_type": row.get("feature_type", ""),
                "downstream_span": row.get("downstream_span", ""),
                "adjacent_spans": row.get("adjacent_spans", ""),
                "K_apparent": row.get("K_apparent", ""),
                "K_local": row.get("K_local", ""),
                "q_ref_basis": row.get("q_ref_basis", ""),
                "tap_length_proxy_m": row.get("tap_length_proxy_m", ""),
                "downstream_span_fit_use_status": row.get("downstream_span_fit_use_status", ""),
                "fit_eligible": row.get("fit_eligible", ""),
                "validation_eligible": row.get("validation_eligible", ""),
                "admission_status": admission,
                "coefficient_name_allowed": "yes_component_K_candidate" if admission == "candidate_fit_admissible" else "no_universal_K_yet",
                "required_next_action": _k_action(admission),
                "quality_flags": row.get("quality_flags", ""),
                "source_bend_minor_loss_csv": row.get("source_bend_minor_loss_csv", ""),
            }
        )
    return rows


def _build_tap_gap_table(minor_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for index, row in enumerate(minor_rows, start=1):
        gap_type = _tap_gap_type(row)
        if gap_type == "none":
            continue
        rows.append(
            {
                "gap_id": f"TAP-GAP-{index:03d}",
                "case_id": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "feature": row.get("feature", ""),
                "feature_type": row.get("feature_type", ""),
                "start_patch": row.get("start_patch", ""),
                "end_patch": row.get("end_patch", ""),
                "downstream_span": row.get("downstream_span", ""),
                "current_tap_length_proxy_m": row.get("tap_length_proxy_m", ""),
                "current_basis": row.get("straight_loss_subtraction_status", ""),
                "gap_type": gap_type,
                "needed_input": "true centerline tap-to-tap length; mesh-family/GCI pressure terms; recirculation-aware exclusion labels where flagged",
                "blocks": "component_or_cluster_K_admission_for_fitting",
                "priority": _tap_priority(gap_type),
                "source_path": row.get("source_bend_minor_loss_csv", ""),
                "quality_flags": row.get("quality_flags", ""),
            }
        )
    return rows


def _build_f6_handoff(corrected_q_summary: Dict[str, object]) -> List[Dict[str, object]]:
    corrected_q_terminal = bool(corrected_q_summary.get("terminal", False))
    admitted_rows = int(corrected_q_summary.get("corrected_q_rows_admitted", 0))
    row_count = int(corrected_q_summary.get("row_count", 0))
    classification = str(corrected_q_summary.get("row_classification", "unknown"))
    return [
        {
            "candidate_id": "F6_phi_re",
            "current_status": "next_bounded_candidate_not_launchable_yet",
            "corrected_q_terminal": str(corrected_q_terminal).lower(),
            "corrected_q_admitted_rows": admitted_rows,
            "corrected_q_row_count": row_count,
            "corrected_q_classification": classification,
            "ready_for_bounded_test": "yes" if corrected_q_terminal and admitted_rows > 0 else "no",
            "primary_metric": "admitted non-recirculating pressure-loss validation versus F3_shah_apparent",
            "secondary_guardrail": "no-refit Salt3/Salt4 mdot must not worsen; no thermal fitting",
            "blocking_gap": "terminal/admitted corrected-Q Re-variation evidence is absent" if admitted_rows == 0 else "none",
            "next_action": "Harvest terminal corrected-Q rows and rerun F6 bounded pressure-loss screen only after admission gate passes.",
        }
    ]


def _write_readme(output_dir: Path, summary: Dict[str, object]) -> None:
    readme = f"""# Hydraulic Reset/K Admission Contract

Date: 2026-07-14

## Decision

The current H1 evidence remains a proxy, not a faithful hydraulic closure. This package creates the tables needed to make a faithful path executable: a reset/development contract, a component/cluster K admission table, tap-length gap rows, and an F6 readiness handoff. No thermal fitting, native CFD output mutation, or global friction/K multiplier is used.

## Outputs

- `hydraulic_reset_development_contract.csv` lists reset/development rows and requires a first-class Fluid reset/development term before H1 can be relaunched faithfully.
- `component_cluster_k_admission_table.csv` keeps component K, cluster/branch context, recirculation diagnostics, and fit/validation status separate.
- `tap_length_gap_table.csv` identifies the centerline tap-length, upper-bound K, coarse/no-GCI, and recirculation gaps blocking local-K admission.
- `f6_readiness_handoff.csv` keeps F6 as the next bounded candidate but blocks launch until admitted Re-variation evidence exists.
- `summary.json` records the guardrails and row counts.

## Recommended Next Hydraulic Run/Edit

1. Add a Fluid-side reset/development input contract that reports reset/development pressure separately from straight friction, component K, cluster K, branch-apparent diagnostics, and recirculation diagnostics.
2. Extract true centerline tap-to-tap lengths and mesh-family pressure terms for the two-tap minor-loss rows before fitting any component or cluster K.
3. Do not launch F6 until corrected-Q or equivalent Re-variation rows are terminal and admitted. When admitted, score F6 first on pressure-loss validation, then mdot as a secondary guardrail.

## Counts

- Reset contract rows: {summary['reset_contract_rows']}
- Reset candidate rows blocked on API/mesh admission: {summary['reset_candidate_blocked_rows']}
- Component/cluster K rows: {summary['component_k_rows']}
- Component/cluster K fit-admissible rows: {summary['component_fit_admissible_rows']}
- Tap-length/gap rows: {summary['tap_length_gap_rows']}
- F6 ready for bounded test: {str(summary['f6_ready_for_bounded_test']).lower()}
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(output_dir: Path = OUTPUT_DIR) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)

    reset_rows = _read_csv(RESET_MAP)
    named_rows = _read_csv(NAMED_LOSSES)
    minor_rows = _read_csv(MINOR_TWO_TAP)
    corrected_q_summary = _read_json(CORRECTED_Q_SUMMARY)

    reset_contract = _build_reset_contract(reset_rows)
    component_k = _build_component_k_table(minor_rows)
    tap_gaps = _build_tap_gap_table(minor_rows)
    f6_handoff = _build_f6_handoff(corrected_q_summary)

    reset_status_counts = Counter(row["admission_status"] for row in reset_contract)
    k_status_counts = Counter(row["admission_status"] for row in component_k)

    source_rows = [
        {"source_id": "reset_map", "path": _rel(RESET_MAP), "role": "reset/development row evidence"},
        {"source_id": "named_losses", "path": _rel(NAMED_LOSSES), "role": "branch/component/cluster loss context"},
        {"source_id": "minor_two_tap", "path": _rel(MINOR_TWO_TAP), "role": "component and cluster K admission source"},
        {"source_id": "pressure_ledger", "path": _rel(PRESSURE_LEDGER), "role": "pressure-term provenance for reset and minor-loss reductions"},
        {"source_id": "h1_gap", "path": _rel(H1_GAP), "role": "prior H1 faithful gap decision"},
        {"source_id": "f6_decision", "path": _rel(F6_DECISION), "role": "prior F6 bounded-candidate decision"},
        {"source_id": "corrected_q_gate", "path": _rel(CORRECTED_Q_SUMMARY), "role": "F6 Re-variation admission status"},
    ]

    _write_csv(
        output_dir / "hydraulic_reset_development_contract.csv",
        [
            "contract_id",
            "source_id",
            "case_id",
            "reset_feature",
            "reset_type",
            "downstream_span",
            "orientation",
            "x_from_reset_m",
            "L_over_D_from_reset",
            "thermal_reset_status",
            "hydraulic_reset_status",
            "recirculation_flag",
            "admission_status",
            "fluid_api_requirement",
            "required_next_action",
            "source_path",
            "quality_flags",
        ],
        reset_contract,
    )
    _write_csv(
        output_dir / "component_cluster_k_admission_table.csv",
        [
            "k_row_id",
            "join_key",
            "source_id",
            "case_id",
            "feature",
            "feature_type",
            "downstream_span",
            "adjacent_spans",
            "K_apparent",
            "K_local",
            "q_ref_basis",
            "tap_length_proxy_m",
            "downstream_span_fit_use_status",
            "fit_eligible",
            "validation_eligible",
            "admission_status",
            "coefficient_name_allowed",
            "required_next_action",
            "quality_flags",
            "source_bend_minor_loss_csv",
        ],
        component_k,
    )
    _write_csv(
        output_dir / "tap_length_gap_table.csv",
        [
            "gap_id",
            "case_id",
            "source_id",
            "feature",
            "feature_type",
            "start_patch",
            "end_patch",
            "downstream_span",
            "current_tap_length_proxy_m",
            "current_basis",
            "gap_type",
            "needed_input",
            "blocks",
            "priority",
            "source_path",
            "quality_flags",
        ],
        tap_gaps,
    )
    _write_csv(
        output_dir / "f6_readiness_handoff.csv",
        [
            "candidate_id",
            "current_status",
            "corrected_q_terminal",
            "corrected_q_admitted_rows",
            "corrected_q_row_count",
            "corrected_q_classification",
            "ready_for_bounded_test",
            "primary_metric",
            "secondary_guardrail",
            "blocking_gap",
            "next_action",
        ],
        f6_handoff,
    )
    _write_csv(output_dir / "source_manifest.csv", ["source_id", "path", "role"], source_rows)

    f6_ready = f6_handoff[0]["ready_for_bounded_test"] == "yes"
    summary: Dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reset_contract_rows": len(reset_contract),
        "reset_candidate_blocked_rows": int(reset_status_counts["candidate_blocked_api_and_mesh_admission"]),
        "reset_status_counts": dict(reset_status_counts),
        "named_loss_rows_available": len(named_rows),
        "component_k_rows": len(component_k),
        "component_fit_admissible_rows": int(k_status_counts["candidate_fit_admissible"]),
        "component_k_status_counts": dict(k_status_counts),
        "tap_length_gap_rows": len(tap_gaps),
        "f6_ready_for_bounded_test": f6_ready,
        "corrected_q_admitted_rows": int(f6_handoff[0]["corrected_q_admitted_rows"]),
        "native_solver_outputs_mutated": False,
        "thermal_fit_used": False,
        "global_multiplier_exported": False,
        "recommendation": "implement_reset_development_api_and_tap_length_extraction_before_faithful_h1; hold_f6_until_admitted_re_variation",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_readme(output_dir, summary)
    return summary


def main() -> None:
    summary = build_package()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
