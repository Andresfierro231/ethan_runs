#!/usr/bin/env python3
"""Build a section-effective hybrid pressure scorecard for corner_lower_right."""
from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21"
DATE = "2026-07-21"
SLUG = "2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-21" / SLUG

RECIRC_TABLE = REPO_ROOT / (
    "work_products/2026-07/2026-07-20/"
    "2026-07-20_two_tap_recirc_section_effective_model/"
    "recirc_pressure_basis_table.csv"
)
CANONICAL_TABLE = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_publication_freeze/"
    "canonical_pressure_corner_result.csv"
)
RESIDUAL_CONTRACT = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_throughflow_recirc_exchange_cell/"
    "residual_equation_contract.md"
)


def dec(value: str | None) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"cannot parse decimal value {value!r}") from exc


def fmt(value: Decimal) -> str:
    return format(value.normalize(), "f")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def build_scorecard_rows() -> list[dict[str, str]]:
    recirc_rows = read_csv(RECIRC_TABLE)
    canonical_by_case = {row["case_id"]: row for row in read_csv(CANONICAL_TABLE)}
    rows: list[dict[str, str]] = []
    for row in recirc_rows:
        case_id = row["case_id"]
        canonical = canonical_by_case[case_id]
        gross = dec(canonical["gross_static_pressure_rise_pa"])
        residual = dec(canonical["available_residual_pa"])
        residual_pct = (abs(residual) / abs(gross) * Decimal("100")) if gross else Decimal("0")
        rows.append(
            {
                "case_id": case_id,
                "case_key": row["case_key"],
                "feature": row["feature"],
                "time_s": row["time_s"],
                "endpoint_pair": canonical["endpoint_pair"],
                "gross_static_pressure_rise_pa": canonical["gross_static_pressure_rise_pa"],
                "hydrostatic_term_pa": canonical["hydrostatic_term_pa"],
                "hydrostatic_fraction_of_gross": canonical["hydrostatic_fraction_of_gross"],
                "kinetic_term_pa": canonical["kinetic_term_pa"],
                "straight_developing_term_pa": "0",
                "straight_developing_status": canonical["straight_developing_status"],
                "available_signed_residual_pa": canonical["available_residual_pa"],
                "available_residual_percent_of_gross": fmt(residual_pct),
                "pressure_recovery_candidate_pa": canonical["pressure_recovery_candidate_pa"],
                "q_ref_pa": row["local_dynamic_pressure_mean_pa"],
                "K_eff_recirc_diagnostic": row["K_eff_recirc_diagnostic"],
                "reverse_area_fraction": canonical["reverse_area_fraction"],
                "reverse_mass_fraction": canonical["reverse_mass_fraction"],
                "secondary_velocity_fraction": canonical["secondary_velocity_fraction"],
                "component_isolation_label": canonical["component_isolation_label"],
                "component_isolation_gate": row["component_isolation_gate"],
                "same_qoi_uncertainty_gate": canonical["same_qoi_uncertainty_gate"],
                "ordinary_recirculation_gate": row["ordinary_recirculation_gate"],
                "final_label": canonical["final_label"],
                "admission_status": canonical["admission_status"],
                "allowed_thesis_use": canonical["publication_use"],
                "forbidden_use": "component_K;ordinary_single_stream_K;F6_fit;clipped_K;hidden_global_multiplier",
            }
        )
    return sorted(rows, key=lambda item: item["case_id"])


def build_hybrid_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "term_id": "HYBRID-PRESSURE-001",
            "term_name": "Delta_p_recirc_section",
            "model_lane": "throughflow_plus_recirc_section_effective_pressure",
            "formula": "Delta_p_recirc_section = q_ref * K_eff_recirc",
            "equivalent_direct_form": "Delta_p_recirc_section = Delta_p_rgh - Delta_p_kin - Delta_p_straight - Delta_p_dev",
            "normalization": "q_ref is same-window throughflow dynamic pressure from net positive mass flux",
            "allowed_use": "diagnostic_decomposition;thesis_section_effective_scorecard;future_split_safe_candidate_after_UQ",
            "forbidden_use": "component_K;F6_fit;global_multiplier;clipped_or_sign_flipped_K",
            "current_status": "diagnostic_section_effective_only",
        },
        {
            "term_id": "HYBRID-PRESSURE-002",
            "term_name": "Salt2_frozen_K_eff_recirc",
            "model_lane": "train_frozen_diagnostic_transfer_check",
            "formula": "Delta_p_recirc_section_pred = q_ref_case * K_eff_recirc_salt2",
            "equivalent_direct_form": "uses Salt2 K_eff_recirc without refitting Salt3/Salt4",
            "normalization": "case-local q_ref with Salt2 diagnostic coefficient",
            "allowed_use": "diagnostic_error_quantification_only",
            "forbidden_use": "validation_score;holdout_score;external_score;admission",
            "current_status": "not_a_frozen_predictive_candidate",
        },
        {
            "term_id": "HYBRID-PRESSURE-003",
            "term_name": "oracle_envelope",
            "model_lane": "nonpredictive_upper_bound",
            "formula": "Delta_p_recirc_section_oracle = q_ref_case * K_eff_recirc_case",
            "equivalent_direct_form": "row-specific observed residual",
            "normalization": "case-local q_ref and case-local diagnostic K",
            "allowed_use": "upper_bound_explainable_error_context",
            "forbidden_use": "predictive_evidence;admission;coefficient_transfer",
            "current_status": "oracle_nonpredictive",
        },
    ]


def build_three_level_rows(scorecard_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    salt2 = next(row for row in scorecard_rows if row["case_id"] == "salt_2")
    frozen_k = dec(salt2["K_eff_recirc_diagnostic"])
    out: list[dict[str, str]] = []
    for row in scorecard_rows:
        observed = dec(row["available_signed_residual_pa"])
        q_ref = dec(row["q_ref_pa"])
        gross = dec(row["gross_static_pressure_rise_pa"])
        case_k = dec(row["K_eff_recirc_diagnostic"])
        levels = [
            ("observed_decomposition", observed, "", "explanatory_observed_terms_only"),
            ("salt2_frozen_diagnostic", q_ref * frozen_k, fmt(frozen_k), "diagnostic_transfer_check_not_admitted"),
            ("oracle_envelope_nonpredictive", observed, fmt(case_k), "oracle_upper_bound_nonpredictive"),
        ]
        for level, predicted, k_used, status in levels:
            error = predicted - observed
            abs_error = abs(error)
            error_pct = (abs_error / abs(gross) * Decimal("100")) if gross else Decimal("0")
            out.append(
                {
                    "case_id": row["case_id"],
                    "case_key": row["case_key"],
                    "score_level": level,
                    "q_ref_pa": row["q_ref_pa"],
                    "K_eff_recirc_used": k_used,
                    "predicted_delta_p_recirc_section_pa": fmt(predicted),
                    "observed_available_residual_pa": row["available_signed_residual_pa"],
                    "prediction_error_pa": fmt(error),
                    "abs_error_pa": fmt(abs_error),
                    "abs_error_percent_gross_static": fmt(error_pct),
                    "score_status": status,
                    "admission_status": "not_admitted",
                    "protected_rows_consumed": "0",
                }
            )
    return out


def build_claim_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "CLAIM-001",
            "claim_status": "allowed",
            "claim": "corner_lower_right pressure evidence is section-effective under material reverse flow",
            "basis": "three Salt2/Salt3/Salt4 rows have high reverse-flow metrics and failed ordinary gates",
            "forbidden_extension": "do not call these rows ordinary component K",
        },
        {
            "claim_id": "CLAIM-002",
            "claim_status": "allowed",
            "claim": "hydrostatic head dominates gross static pressure rise",
            "basis": "hydrostatic fraction of gross is approximately one for all three rows",
            "forbidden_extension": "do not normalize gross static rise as local loss K",
        },
        {
            "claim_id": "CLAIM-003",
            "claim_status": "allowed",
            "claim": "a named throughflow-plus-recirculation pressure residual can be quantified diagnostically",
            "basis": "available signed residual and q_ref produce diagnostic K_eff_recirc rows",
            "forbidden_extension": "do not treat the diagnostic term as fitted F6 or admitted closure",
        },
        {
            "claim_id": "CLAIM-004",
            "claim_status": "forbidden",
            "claim": "component K or F6 is admitted from the current corner_lower_right rows",
            "basis": "component isolation, reverse-flow, and same-QOI UQ gates fail",
            "forbidden_extension": "no clipping, hidden multiplier, or protected-row scoring",
        },
    ]


def write_readme(out_dir: Path, summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - {RECIRC_TABLE.relative_to(REPO_ROOT)}
  - {CANONICAL_TABLE.relative_to(REPO_ROOT)}
  - {RESIDUAL_CONTRACT.relative_to(REPO_ROOT)}
tags: [pressure-ledger, two-tap, section-effective, hybrid-pressure, thesis]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
  - .agent/journal/2026-07-21/two-tap-section-effective-hybrid-pressure-scorecard.md
  - imports/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard.json
task: {TASK_ID}
date: {DATE}
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Section-Effective Hybrid Pressure Scorecard

## Result

This package converts the existing `corner_lower_right` pressure evidence into a
thesis-safe section-effective hybrid pressure scorecard. It does not admit a
component `K`, F6 correction, or predictive pressure closure.

Rows scored: `{summary["row_count"]}`. Component-K rows admitted: `0`. F6 fit
rows: `0`. Clipped-K rows: `0`. Hidden/global multiplier rows: `0`.

## Interpretation

The gross static pressure rise is hydrostatic dominated. After hydrostatic and
kinetic correction, the available signed residual is small and negative:
Salt2 `{summary["salt2_residual_pa"]} Pa`, Salt3 `{summary["salt3_residual_pa"]} Pa`,
and Salt4 `{summary["salt4_residual_pa"]} Pa`.

The named hybrid term is `Delta_p_recirc_section`. The Salt2-frozen diagnostic
transfer check applies Salt2 `K_eff_recirc` to Salt3/Salt4 without refitting.
This is useful thesis quantification, not model admission.

## Outputs

- `section_effective_pressure_scorecard.csv`
- `hybrid_pressure_term_contract.csv`
- `three_level_score.csv`
- `thesis_claim_ledger.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repo, validation/holdout/external scoring, fitting, model
selection, component-K/F6 admission, clipped K, hidden/global multiplier, S11,
S15, S6, blocker register, generated index, thesis current file, or internal-Nu
residual absorption is changed by this package.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def write_source_manifest(out_dir: Path) -> None:
    rows = [
        {
            "source_id": "recirc_section_effective_model",
            "path": str(RECIRC_TABLE.relative_to(REPO_ROOT)),
            "use": "diagnostic residual and K_eff basis",
            "mutation": "False",
        },
        {
            "source_id": "pressure_corner_publication_freeze",
            "path": str(CANONICAL_TABLE.relative_to(REPO_ROOT)),
            "use": "canonical section-effective result and publication labels",
            "mutation": "False",
        },
        {
            "source_id": "throughflow_recirc_exchange_cell_contract",
            "path": str(RESIDUAL_CONTRACT.relative_to(REPO_ROOT)),
            "use": "hybrid residual equation boundary",
            "mutation": "False",
        },
    ]
    write_csv(out_dir / "source_manifest.csv", rows, ["source_id", "path", "use", "mutation"])


def build(out_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard_rows = build_scorecard_rows()
    contract_rows = build_hybrid_contract_rows()
    three_level_rows = build_three_level_rows(scorecard_rows)
    claim_rows = build_claim_rows()

    write_csv(out_dir / "section_effective_pressure_scorecard.csv", scorecard_rows, [
        "case_id", "case_key", "feature", "time_s", "endpoint_pair",
        "gross_static_pressure_rise_pa", "hydrostatic_term_pa", "hydrostatic_fraction_of_gross",
        "kinetic_term_pa", "straight_developing_term_pa", "straight_developing_status",
        "available_signed_residual_pa", "available_residual_percent_of_gross",
        "pressure_recovery_candidate_pa", "q_ref_pa", "K_eff_recirc_diagnostic",
        "reverse_area_fraction", "reverse_mass_fraction", "secondary_velocity_fraction",
        "component_isolation_label", "component_isolation_gate", "same_qoi_uncertainty_gate",
        "ordinary_recirculation_gate", "final_label", "admission_status",
        "allowed_thesis_use", "forbidden_use",
    ])
    write_csv(out_dir / "hybrid_pressure_term_contract.csv", contract_rows, [
        "term_id", "term_name", "model_lane", "formula", "equivalent_direct_form",
        "normalization", "allowed_use", "forbidden_use", "current_status",
    ])
    write_csv(out_dir / "three_level_score.csv", three_level_rows, [
        "case_id", "case_key", "score_level", "q_ref_pa", "K_eff_recirc_used",
        "predicted_delta_p_recirc_section_pa", "observed_available_residual_pa",
        "prediction_error_pa", "abs_error_pa", "abs_error_percent_gross_static",
        "score_status", "admission_status", "protected_rows_consumed",
    ])
    write_csv(out_dir / "thesis_claim_ledger.csv", claim_rows, [
        "claim_id", "claim_status", "claim", "basis", "forbidden_extension",
    ])
    write_source_manifest(out_dir)

    frozen_rows = [row for row in three_level_rows if row["score_level"] == "salt2_frozen_diagnostic"]
    non_train_frozen = [row for row in frozen_rows if row["case_id"] != "salt_2"]
    summary: dict[str, object] = {
        "task": TASK_ID,
        "date": DATE,
        "row_count": len(scorecard_rows),
        "three_level_rows": len(three_level_rows),
        "component_k_admitted_rows": 0,
        "f6_fit_rows": 0,
        "clipped_k_rows": 0,
        "hidden_global_multiplier_rows": 0,
        "validation_rows_consumed": 0,
        "holdout_rows_consumed": 0,
        "external_test_rows_consumed": 0,
        "s11_s15_s6_trigger": False,
        "salt2_frozen_K_eff_recirc": next(row["K_eff_recirc_diagnostic"] for row in scorecard_rows if row["case_id"] == "salt_2"),
        "salt2_residual_pa": next(row["available_signed_residual_pa"] for row in scorecard_rows if row["case_id"] == "salt_2"),
        "salt3_residual_pa": next(row["available_signed_residual_pa"] for row in scorecard_rows if row["case_id"] == "salt_3"),
        "salt4_residual_pa": next(row["available_signed_residual_pa"] for row in scorecard_rows if row["case_id"] == "salt_4"),
        "salt2_frozen_all_case_max_abs_error_pa": max(dec(row["abs_error_pa"]) for row in frozen_rows).to_eng_string(),
        "salt2_frozen_transfer_max_abs_error_pa": max(dec(row["abs_error_pa"]) for row in non_train_frozen).to_eng_string(),
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "thesis_current_file_edit": False,
        "status": "complete",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(out_dir, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    summary = build(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
