#!/usr/bin/env python3.11
"""Build the integrated signed wall-flux thermal-development gate.

The package synthesizes completed MF07/MF08/MF09/MF10 plus D2/D3/D4 evidence.
It does not fit, score protected rows, release source/property terms, or admit
any coefficient.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-MF-SIGNED-WALL-FLUX-THERMAL-DEVELOPMENT-GATE-2026-07-22"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_signed_wall_flux_thermal_development_gate"

MF07 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis"
MF08 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches"
MF09 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives"
MF10 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff"
MF11 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate"
D2 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
D3 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
D4 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate"
S12 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fnum(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_decomposition(
    mf07_summary: dict[str, object],
    mf08_summary: dict[str, object],
    mf09_summary: dict[str, object],
    mf10_summary: dict[str, object],
    d2_summary: dict[str, object],
    d3_summary: dict[str, object],
    d4_summary: dict[str, object],
) -> list[dict[str, object]]:
    return [
        {
            "owner_layer": "bulk_to_TP_projection_thermal_development",
            "evidence_package": str(MF07.relative_to(ROOT)),
            "support_level": "promising_diagnostic",
            "key_evidence": f"{mf07_summary['thermal_development_indicated_rows']} rows indicate thermal development; train M3 TP rows are cold; max S13 wall/core over D2 TP offset is {mf07_summary['max_abs_wall_core_over_D2_train_TP_offset']}.",
            "primary_blocker": "same-QOI TP projection UQ, released formula, and source/property labels missing",
            "candidate_review_status": "not_reviewable",
            "next_action": "do not correct TW until this TP layer is source-bounded or fail-closed",
        },
        {
            "owner_layer": "signed_wall_or_source_heat_path",
            "evidence_package": str(MF08.relative_to(ROOT)),
            "support_level": "sign_convention_established_diagnostic",
            "key_evidence": f"{mf08_summary['required_variant_rows']} signed variants reviewed; {mf08_summary['ready_for_train_only_smoke_rows']} smoke-ready; realized wallHeatFlux fit forbidden.",
            "primary_blocker": "4/4 variants need source basis and no source/property release exists",
            "candidate_review_status": "not_reviewable",
            "next_action": "source-bounded heat-path release table before any train-only smoke",
        },
        {
            "owner_layer": "recirculating_upcomer_exchange",
            "evidence_package": str(MF09.relative_to(ROOT)),
            "support_level": "best_next_science_lane_but_blocked",
            "key_evidence": f"best lane is {mf09_summary['best_next_science_lane']}; smoke-ready variants {mf09_summary['smoke_ready_variants']}; accepted same-label mesh/GCI QOIs {mf09_summary['accepted_same_label_mesh_gci_qois']}.",
            "primary_blocker": "same-label mesh/GCI, source-property conservation, production harvest, and onset anchors missing",
            "candidate_review_status": "not_reviewable",
            "next_action": "same-label mesh-family generation and source-property conservation gate",
        },
        {
            "owner_layer": "TP_to_TW_wall_shape_axial_mixing",
            "evidence_package": str(D3.relative_to(ROOT)),
            "support_level": "strong_diagnostic_shape_signal",
            "key_evidence": f"D3 transfer RMSE {d3_summary['d3_transfer_rmse_K']} K and local-shape RMSE after bias {d3_summary['d3_transfer_local_shape_rmse_after_bias_K']} K; production use false.",
            "primary_blocker": "same-QOI UQ/source basis not admitted; TP projection layer still unresolved",
            "candidate_review_status": "not_reviewable",
            "next_action": "analyze TW only after defended TP projection",
        },
        {
            "owner_layer": "segment_source_placement",
            "evidence_package": str(D4.relative_to(ROOT)),
            "support_level": "diagnostic_upper_bound",
            "key_evidence": f"D4 transfer RMSE {d4_summary['d4_transfer_rmse_K']} K with {d4_summary['source_bounded_candidate_ready_rows']} source-bounded ready rows.",
            "primary_blocker": "source-bounded candidate count is zero; D4 is empirical source-placement priority only",
            "candidate_review_status": "not_reviewable",
            "next_action": "independent heat-path/source release before segment source placement smoke",
        },
        {
            "owner_layer": "dry_variant_bakeoff",
            "evidence_package": str(MF10.relative_to(ROOT)),
            "support_level": "blocked_before_execution",
            "key_evidence": f"MF10 decision {mf10_summary['decision']}; zero new train/support scoring rows executed.",
            "primary_blocker": "MF07/MF08/MF09 source-basis gates did not release a smoke-ready variant",
            "candidate_review_status": "not_reviewable",
            "next_action": "do not run another bakeoff until a source-basis gate opens",
        },
        {
            "owner_layer": "empirical_bias_or_hidden_fit",
            "evidence_package": str(MF11.relative_to(ROOT)),
            "support_level": "forbidden_as_closure",
            "key_evidence": "F2/F5 empirical performance is useful attribution context but not a physical release.",
            "primary_blocker": "hidden empirical fit would violate runtime legality and source/property gates",
            "candidate_review_status": "forbidden",
            "next_action": "use only as contradiction/attribution context",
        },
    ]


def build_release_gate(decomp: list[dict[str, object]]) -> list[dict[str, object]]:
    gates = [
        ("bulk_to_TP_formula_released", False, "MF07 stayed diagnostic-only."),
        ("signed_source_property_release", False, "MF08 has 0 smoke-ready variants and 4/4 need source basis."),
        ("recirculating_upcomer_exchange_release", False, "MF09 has 0 smoke-ready variants and no same-label mesh/GCI."),
        ("TP_to_TW_wall_shape_release", False, "D3 is diagnostic and should wait until TP projection is defended."),
        ("segment_source_placement_release", False, "D4 has 0 source-bounded candidate-ready rows."),
        ("train_only_smoke_authorized", False, "MF10 did not run new scores because upstream gates failed."),
        ("candidate_reviewable_now", False, "All owner layers are not reviewable or forbidden."),
    ]
    return [
        {
            "gate": gate,
            "passed": passed,
            "release_allowed": False,
            "reason": reason,
        }
        for gate, passed, reason in gates
    ]


def build_runtime_legality() -> list[dict[str, object]]:
    return [
        {
            "item": "setup-side signed heat-source labels",
            "runtime_allowed": "conditional_after_source_property_release",
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "MF08 documents signs but does not release source/property terms.",
        },
        {
            "item": "realized CFD wallHeatFlux",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "realized wallHeatFlux is post-solve evidence only.",
        },
        {
            "item": "TP/TW target temperatures",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "post-solve targets support residual-owner diagnosis only.",
        },
        {
            "item": "S13 exchange proxy values",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "temporal UQ exists but production/source/mesh gates remain closed.",
        },
        {
            "item": "empirical bias offsets",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "use only as attribution context, not closure.",
        },
    ]


def build_next_sequence() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "next_analysis": "same-label S13 mesh-family generation/GCI or explicit fail-close",
            "why": "MF09 exchange-cell path is blocked by same-label mesh/GCI and production harvest readiness.",
            "exit_condition": "accepted same-label mesh/GCI rows or documented impossibility",
        },
        {
            "priority": 2,
            "next_analysis": "signed source/property heat-path release preflight",
            "why": "MF08 sign convention exists, but no source/property release exists for any signed branch.",
            "exit_condition": "branch-level source/property release table with no runtime leakage",
        },
        {
            "priority": 3,
            "next_analysis": "bulk-to-TP formula gate",
            "why": "MF07 shows TP projection promise, but no formula and same-QOI TP UQ exist.",
            "exit_condition": "released diagnostic formula or fail-closed missing-input table",
        },
        {
            "priority": 4,
            "next_analysis": "TW-after-TP residual-owner table",
            "why": "D3/D4 support wall-shape/source-placement only after TP is not carrying bulk residual.",
            "exit_condition": "TW owner table with no internal-Nu absorption",
        },
    ]


def build_claim_boundary() -> list[dict[str, object]]:
    return [
        {"claim": "signed thermal-development is worth pursuing", "allowed": True, "basis": "MF07/MF08 diagnostic support"},
        {"claim": "a bulk-to-TP correction is released", "allowed": False, "basis": "MF07 release gates failed"},
        {"claim": "wallHeatFlux can be a runtime input", "allowed": False, "basis": "MF08 explicit forbidden gate"},
        {"claim": "upcomer exchange candidate is reviewable", "allowed": False, "basis": "MF09 same-label mesh/GCI and source gates fail"},
        {"claim": "TW should be corrected before TP", "allowed": False, "basis": "D2/MF07 support TP-first ordering"},
        {"claim": "internal Nu may absorb the residual", "allowed": False, "basis": "all source packages preserve this guardrail"},
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - {MF07.relative_to(ROOT)}/README.md
  - {MF08.relative_to(ROOT)}/README.md
  - {MF09.relative_to(ROOT)}/README.md
  - {MF10.relative_to(ROOT)}/README.md
tags: [signed-wall-flux, thermal-development, residual-ownership, bulk-to-tp]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Signed Wall-Flux Thermal-Development Gate

Decision: `{summary["decision"]}`.

This package synthesizes MF07/MF08/MF09/MF10 with D2/D3/D4. It separates the
residual-owner layers and keeps every release/admission gate closed.

Main result:

- Residual-owner layers: `{summary["residual_owner_rows"]}`.
- Candidate-reviewable layers: `{summary["candidate_reviewable_rows"]}`.
- Release gates passed: `{summary["release_gates_passed"]}`.
- Recommended next analysis rows: `{summary["next_sequence_rows"]}`.

The science signal remains useful: signed thermal development and TP-first
projection are worth pursuing. The candidate state is not useful yet: no branch
has source/property release, same-QOI TP release, exchange-cell mesh/GCI release,
or train-only smoke authorization.
"""
    (OUT / "README.md").write_text(text)


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    mf07_summary = read_json(MF07 / "summary.json")
    mf08_summary = read_json(MF08 / "summary.json")
    mf09_summary = read_json(MF09 / "summary.json")
    mf10_summary = read_json(MF10 / "summary.json")
    d2_summary = read_json(D2 / "summary.json")
    d3_summary = read_json(D3 / "summary.json")
    d4_summary = read_json(D4 / "summary.json")

    decomp = build_decomposition(mf07_summary, mf08_summary, mf09_summary, mf10_summary, d2_summary, d3_summary, d4_summary)
    release_gate = build_release_gate(decomp)
    runtime = build_runtime_legality()
    next_sequence = build_next_sequence()
    claims = build_claim_boundary()
    candidate_decision = [
        {
            "decision": "diagnostic_only_no_candidate_reviewable",
            "candidate_reviewable_rows": 0,
            "reason": "all physical owner layers are missing source/property, same-QOI, mesh/GCI, or formula release; empirical layer is forbidden",
            "s11_s12_s13_s15_s6_trigger": False,
        }
    ]
    guardrails = [
        {"guardrail": "native_output_mutation", "value": False},
        {"guardrail": "registry_or_admission_mutation", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "solver_sampler_harvest_uq_launch", "value": False},
        {"guardrail": "fluid_or_external_repo_mutation", "value": False},
        {"guardrail": "thesis_current_file_mutation", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "source_property_release", "value": False},
        {"guardrail": "coefficient_admission", "value": False},
        {"guardrail": "final_score", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
    ]
    source_manifest = [
        {"source_path": str(path.relative_to(ROOT)), "role": role, "mutation": "read_only"}
        for path, role in [
            (MF07 / "summary.json", "bulk-to-TP and reset/Graetz gate"),
            (MF08 / "summary.json", "signed heat-path gate"),
            (MF09 / "summary.json", "recirculating upcomer alternatives"),
            (MF10 / "summary.json", "dry bakeoff gate"),
            (MF11 / "summary.json", "empirical attribution boundary"),
            (D2 / "summary.json", "TP-first projection signal"),
            (D3 / "summary.json", "wall-shape axial-mixing signal"),
            (D4 / "summary.json", "segment source-placement signal"),
            (S12 / "summary.json", "candidate disposition context"),
        ]
    ]

    write_csv(OUT / "residual_owner_decomposition_table.csv", decomp, list(decomp[0].keys()))
    write_csv(OUT / "source_property_release_gate.csv", release_gate, list(release_gate[0].keys()))
    write_csv(OUT / "runtime_legality_audit.csv", runtime, list(runtime[0].keys()))
    write_csv(OUT / "next_analysis_sequence.csv", next_sequence, list(next_sequence[0].keys()))
    write_csv(OUT / "publication_claim_boundary.csv", claims, list(claims[0].keys()))
    write_csv(OUT / "candidate_review_decision.csv", candidate_decision, list(candidate_decision[0].keys()))
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, list(guardrails[0].keys()))
    write_csv(OUT / "source_manifest.csv", source_manifest, list(source_manifest[0].keys()))

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),
        "decision": "diagnostic_only_no_candidate_reviewable",
        "residual_owner_rows": len(decomp),
        "candidate_reviewable_rows": sum(1 for row in decomp if row["candidate_review_status"] == "reviewable"),
        "forbidden_owner_rows": sum(1 for row in decomp if row["candidate_review_status"] == "forbidden"),
        "release_gate_rows": len(release_gate),
        "release_gates_passed": sum(1 for row in release_gate if row["passed"] is True),
        "next_sequence_rows": len(next_sequence),
        "runtime_temperature_release": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "final_score": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "fluid_or_external_repo_mutation": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
