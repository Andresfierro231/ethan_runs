#!/usr/bin/env python3
"""Close out S13 production-harvest/UQ readiness from existing evidence only."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21"
DATE = "2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s13_upcomer_exchange_production_harvest_uq"

S13_LIMITED = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
S13_TEMPORAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
S13_MESH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
S13_QWALL_MESH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
MF09 = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives"
SOURCE_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight"
S12_TP_FIRST = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate"

QOIS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "pass"}


def build_exchange_qoi_table(generated_rows: list[dict[str, str]], temporal_rows: list[dict[str, str]], gap_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    generated_by_qoi = defaultdict(list)
    temporal_by_qoi = defaultdict(list)
    gaps_by_qoi = defaultdict(list)
    for row in generated_rows:
        generated_by_qoi[row["qoi_label"]].append(row)
    for row in temporal_rows:
        temporal_by_qoi[row["qoi_label"]].append(row)
    for row in gap_rows:
        gaps_by_qoi[row["qoi_label"]].append(row)

    rows: list[dict[str, Any]] = []
    for qoi in QOIS:
        generated = generated_by_qoi[qoi]
        temporal = temporal_by_qoi[qoi]
        gaps = gaps_by_qoi[qoi]
        current_coarse = [row for row in generated if row["mesh_level"] == "current_coarse_continuation"]
        missing_medium_fine = [
            row for row in gaps if row["mesh_level"] in {"medium", "fine"} and not is_true(row["same_label_row_present"])
        ]
        target_values = [row.get("target_value", "") for row in current_coarse]
        rows.append(
            {
                "qoi_label": qoi,
                "current_coarse_case_rows": len(current_coarse),
                "finite_current_coarse_values": sum(1 for value in target_values if str(value).strip()),
                "same_qoi_temporal_uq_case_rows": len(temporal),
                "same_qoi_temporal_uq_complete": len(temporal) == 3,
                "same_label_medium_fine_missing_rows": len(missing_medium_fine),
                "same_label_mesh_gci_ready": False,
                "production_harvest_allowed": False,
                "scientific_use_now": "diagnostic_current_coarse_temporal_context_only",
                "primary_blocker": "missing medium/fine same-label mesh-family rows for accepted GCI",
                "value_context": "; ".join(target_values),
            }
        )
    return rows


def build_mesh_blocker_table(gap_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in gap_rows:
        rows.append(
            {
                "case_id": row["case_id"],
                "qoi_label": row["qoi_label"],
                "mesh_level": row["mesh_level"],
                "same_label_row_present": is_true(row["same_label_row_present"]),
                "same_window_triplet_present": is_true(row["same_window_triplet_present"]),
                "formula_sign_basis_matched": is_true(row["formula_sign_basis_matched"]),
                "source_property_basis_matched": is_true(row["source_property_basis_matched"]),
                "geometry_mask_basis_matched": is_true(row["geometry_mask_basis_matched"]),
                "mesh_level_status": row["mesh_level_status"],
                "missing_or_blocking_reason": row["missing_or_blocking_reason"],
                "production_use_allowed_now": False,
            }
        )
    return rows


def build_gate_rows(mf09_summary: dict[str, Any], temporal_summary: dict[str, Any], source_summary: dict[str, Any], generated_rows: list[dict[str, str]], gap_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    missing_medium_fine = [
        row for row in gap_rows if row["mesh_level"] in {"medium", "fine"} and not is_true(row["same_label_row_present"])
    ]
    return [
        {
            "gate": "current_coarse_exchange_qois",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": f"{len(generated_rows)} current-coarse rows generated for 3 cases x 4 QOIs",
            "consequence": "usable as trend/evidence context only",
        },
        {
            "gate": "same_qoi_temporal_uq",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": f"{temporal_summary.get('same_qoi_temporal_uq_executed_qois', 0)} QOIs have same-window neighbor UQ",
            "consequence": "temporal readiness exists, but not mesh/GCI readiness",
        },
        {
            "gate": "same_label_mesh_gci",
            "status": "blocked",
            "pass": False,
            "evidence": f"{len(missing_medium_fine)} medium/fine rows missing; accepted same-label mesh/GCI QOIs = {mf09_summary.get('accepted_same_label_mesh_gci_qois', 0)}",
            "consequence": "production harvest remains forbidden",
        },
        {
            "gate": "source_property_release",
            "status": "blocked",
            "pass": False,
            "evidence": f"nominal train source/property release-ready rows = {source_summary.get('release_ready_rows', 0)}",
            "consequence": "no candidate-specific S11 or S15 release",
        },
        {
            "gate": "pressure_energy_residual_same_window",
            "status": "partial_diagnostic",
            "pass": False,
            "evidence": f"MF09 energy residual contracts = {mf09_summary.get('energy_residual_contract_rows', 0)}, production-ready sampled rows = {mf09_summary.get('limited_sampled_production_ready_rows', 0)}",
            "consequence": "same-window pressure/energy support is not production complete",
        },
        {
            "gate": "near_onset_nonrecirculating_anchor",
            "status": "blocked",
            "pass": False,
            "evidence": f"onset anchor candidate rows = {mf09_summary.get('onset_anchor_candidate_rows', 0)}",
            "consequence": "ordinary upcomer closure remains disabled",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "pass": False,
            "evidence": "mesh/GCI, source/property, and anchor gates are blocked",
            "consequence": "do not launch sampler/harvest/UQ under this row",
        },
        {
            "gate": "s11_decision",
            "status": "closed",
            "pass": False,
            "evidence": "0 exchange-cell fit-ready rows and 0 ordinary internal-Nu fit rows",
            "consequence": "S11/S15/S6 remain closed",
        },
    ]


def build_s11_rows(mf09_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "pathway": "exchange_cell_candidate",
            "candidate_status": "not_s11_reviewable",
            "supporting_evidence": f"exchange-cell fit-ready rows = {mf09_summary.get('exchange_cell_fit_ready_rows', 0)}",
            "blocking_evidence": "same-label mesh/GCI and source/property release are not complete",
            "next_action": "generate medium/fine same-label mesh rows before any production harvest",
        },
        {
            "pathway": "ordinary_upcomer_Nu_fD_K",
            "candidate_status": "disabled",
            "supporting_evidence": f"ordinary internal-Nu fit rows = {mf09_summary.get('ordinary_internal_nu_fit_rows', 0)}",
            "blocking_evidence": "near-onset/nonrecirculating anchors are absent",
            "next_action": "produce independent low-recirculation/onset anchors before reopening ordinary closure",
        },
        {
            "pathway": "S11_candidate_source_property_refresh",
            "candidate_status": "closed",
            "supporting_evidence": "0 named admission-worthy physical candidates",
            "blocking_evidence": "source/property nominal train preflight releases 0 rows",
            "next_action": "rerun only after one physical candidate clears mesh/UQ/source gates",
        },
        {
            "pathway": "S15_freeze_score_release",
            "candidate_status": "closed",
            "supporting_evidence": "0 frozen runtime-legal candidates",
            "blocking_evidence": "S12/S13/S14 have not released exactly one candidate",
            "next_action": "do not score validation/holdout/external rows",
        },
    ]


def build_onset_rows(mf09_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "regime_or_anchor": "current Salt2/Salt3/Salt4 recirculating target windows",
            "available_rows": 3,
            "status": "diagnostic_recirc_only",
            "use_allowed": "trend_context_only",
            "reason": "recirculating rows cannot identify ordinary upcomer Nu/f_D/K independently",
        },
        {
            "regime_or_anchor": "near_onset_transition",
            "available_rows": mf09_summary.get("onset_anchor_candidate_rows", 0),
            "status": "missing",
            "use_allowed": "false",
            "reason": "no same-window near-onset anchor package is admitted",
        },
        {
            "regime_or_anchor": "nonrecirculating_low_recirculation_anchor",
            "available_rows": mf09_summary.get("onset_ordinary_fit_rows", 0),
            "status": "missing",
            "use_allowed": "false",
            "reason": "ordinary throughflow basis is not independently anchored",
        },
    ]


def build_handoff_rows() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "next_row": "TODO-S13-UPCOMER-EXCHANGE-SAME-LABEL-MEDIUM-FINE-MESH-SAMPLING-2026-07-22",
            "goal": "sample/generate medium and fine same-label QOI rows for Salt2/Salt3/Salt4 and four exchange QOIs",
            "must_preserve": "exact label, same time windows, same masks, same sign convention, same source family",
            "forbidden": "production harvest, coefficient admission, ordinary Nu/f_D/K fit",
        },
        {
            "priority": 2,
            "next_row": "TODO-S13-UPCOMER-EXCHANGE-SAME-LABEL-MESH-GCI-UQ-2026-07-22",
            "goal": "compute accepted mesh/GCI UQ only after coarse/medium/fine exact-label rows exist",
            "must_preserve": "same-QOI temporal and mesh uncertainty separation",
            "forbidden": "substitute Salt2-only refined smoke or matched-plane diagnostics for same-label mesh family",
        },
        {
            "priority": 3,
            "next_row": "TODO-S13-UPCOMER-EXCHANGE-SOURCE-PROPERTY-RELEASE-2026-07-22",
            "goal": "independent source/property release for the exact exchange-cell candidate lane",
            "must_preserve": "Q_wall_W/source-side separation and row-specific source envelope",
            "forbidden": "source-side relabel as Q_wall_W or residual absorption into internal Nu",
        },
    ]


def write_svg(gate_rows: list[dict[str, Any]]) -> None:
    path = OUT / "figures/svg/s13_production_harvest_readiness_status.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = {"diagnostic_pass": "#2d7f5e", "partial_diagnostic": "#c28720", "blocked": "#b34040", "do_not_run": "#6d4c8d", "closed": "#555555"}
    width = 1040
    height = 90 + 70 * len(gate_rows)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="32" y="42" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#1d2329">S13 Production Harvest Readiness</text>',
        '<text x="32" y="68" font-family="Arial, sans-serif" font-size="14" fill="#46515c">Existing evidence supports diagnostic current-coarse trends only; production/admission gates remain closed.</text>',
    ]
    for idx, row in enumerate(gate_rows):
        y = 100 + idx * 70
        color = colors.get(str(row["status"]), "#777777")
        parts.extend(
            [
                f'<rect x="32" y="{y}" width="976" height="48" rx="4" fill="#f7f8f9" stroke="#d5dadd"/>',
                f'<circle cx="58" cy="{y + 24}" r="10" fill="{color}"/>',
                f'<text x="82" y="{y + 20}" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#1d2329">{row["gate"]}</text>',
                f'<text x="82" y="{y + 39}" font-family="Arial, sans-serif" font-size="13" fill="#46515c">{row["status"]}: {str(row["consequence"])[:120]}</text>',
            ]
        )
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    generated_rows = read_csv(S13_MESH / "same_label_mesh_family_generated_rows.csv")
    gap_rows = read_csv(S13_MESH / "required_mesh_level_gap_matrix.csv")
    temporal_rows = read_csv(S13_TEMPORAL / "same_qoi_temporal_uq_case_rows.csv")
    mf09_summary = read_json(MF09 / "summary.json")
    temporal_summary = read_json(S13_TEMPORAL / "summary.json")
    source_summary = read_json(SOURCE_PREFLIGHT / "summary.json")
    limited_summary = read_json(S13_LIMITED / "summary.json")

    qoi_rows = build_exchange_qoi_table(generated_rows, temporal_rows, gap_rows)
    mesh_rows = build_mesh_blocker_table(gap_rows)
    gate_rows = build_gate_rows(mf09_summary, temporal_summary, source_summary, generated_rows, gap_rows)
    s11_rows = build_s11_rows(mf09_summary)
    onset_rows = build_onset_rows(mf09_summary)
    handoff_rows = build_handoff_rows()

    disabled_rows = read_csv(MF09 / "ordinary_upcomer_disabled_reasons.csv")
    source_manifest = [
        {"artifact": "limited sampled-field synthesis", "path": rel(S13_LIMITED), "use": "finite diagnostic sampled-field and thesis-status context"},
        {"artifact": "same-QOI temporal UQ", "path": rel(S13_TEMPORAL), "use": "neighbor-window UQ status"},
        {"artifact": "same-label mesh-family generation", "path": rel(S13_MESH), "use": "current-coarse rows and medium/fine blocker matrix"},
        {"artifact": "S13 Qwall mesh/GCI gate", "path": rel(S13_QWALL_MESH), "use": "prior production harvest consequence"},
        {"artifact": "MF09 recirculating-upcomer alternatives", "path": rel(MF09), "use": "ordinary closure disable and S11/S15 gate status"},
        {"artifact": "source/property nominal train preflight", "path": rel(SOURCE_PREFLIGHT), "use": "source release blocker status"},
        {"artifact": "S12 TP-first evidence gate", "path": rel(S12_TP_FIRST), "use": "TP-first upstream interpretation context"},
    ]

    no_mutation = [
        {"guardrail": "native_output_mutation", "status": False},
        {"guardrail": "registry_or_admission_mutation", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_sampler_harvest_uq_launch", "status": False},
        {"guardrail": "Fluid_or_external_repo_mutation", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "source_property_release", "status": False},
        {"guardrail": "Qwall_release", "status": False},
        {"guardrail": "coefficient_admission", "status": False},
        {"guardrail": "S11_S12_S13_S15_S6_trigger", "status": False},
        {"guardrail": "residual_absorbed_into_internal_Nu", "status": False},
    ]

    write_csv(
        OUT / "exchange_qoi_availability_uq_table.csv",
        qoi_rows,
        [
            "qoi_label",
            "current_coarse_case_rows",
            "finite_current_coarse_values",
            "same_qoi_temporal_uq_case_rows",
            "same_qoi_temporal_uq_complete",
            "same_label_medium_fine_missing_rows",
            "same_label_mesh_gci_ready",
            "production_harvest_allowed",
            "scientific_use_now",
            "primary_blocker",
            "value_context",
        ],
    )
    write_csv(
        OUT / "same_label_mesh_gci_blocker_table.csv",
        mesh_rows,
        [
            "case_id",
            "qoi_label",
            "mesh_level",
            "same_label_row_present",
            "same_window_triplet_present",
            "formula_sign_basis_matched",
            "source_property_basis_matched",
            "geometry_mask_basis_matched",
            "mesh_level_status",
            "missing_or_blocking_reason",
            "production_use_allowed_now",
        ],
    )
    write_csv(OUT / "production_harvest_readiness_gate.csv", gate_rows, ["gate", "status", "pass", "evidence", "consequence"])
    write_csv(OUT / "ordinary_closure_disabled_map.csv", disabled_rows, list(disabled_rows[0]))
    write_csv(OUT / "s11_decision_table.csv", s11_rows, ["pathway", "candidate_status", "supporting_evidence", "blocking_evidence", "next_action"])
    write_csv(OUT / "onset_regime_map_status.csv", onset_rows, ["regime_or_anchor", "available_rows", "status", "use_allowed", "reason"])
    write_csv(OUT / "next_compute_handoff.csv", handoff_rows, ["priority", "next_row", "goal", "must_preserve", "forbidden"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["artifact", "path", "use"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation, ["guardrail", "status"])
    write_svg(gate_rows)

    gate_counts = Counter(str(row["status"]) for row in gate_rows)
    missing_medium_fine = [
        row for row in gap_rows if row["mesh_level"] in {"medium", "fine"} and not is_true(row["same_label_row_present"])
    ]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "fail_closed_ordinary_upcomer_disabled_no_s11_reviewable_candidate",
        "limited_sampled_finite_exchange_rows": limited_summary.get("finite_exchange_rows", 0),
        "current_coarse_exchange_qoi_rows": len(generated_rows),
        "same_qoi_temporal_uq_complete_qois": temporal_summary.get("same_qoi_temporal_uq_executed_qois", 0),
        "same_label_gap_rows": len(gap_rows),
        "missing_medium_fine_same_label_rows": len(missing_medium_fine),
        "accepted_same_label_mesh_gci_qois": mf09_summary.get("accepted_same_label_mesh_gci_qois", 0),
        "source_property_release_ready_rows": source_summary.get("release_ready_rows", 0),
        "exchange_cell_fit_ready_rows": mf09_summary.get("exchange_cell_fit_ready_rows", 0),
        "ordinary_internal_nu_fit_rows": mf09_summary.get("ordinary_internal_nu_fit_rows", 0),
        "onset_anchor_candidate_rows": mf09_summary.get("onset_anchor_candidate_rows", 0),
        "production_harvest_allowed": False,
        "s11_reviewable_candidate": False,
        "s15_freeze_allowed": False,
        "validation_holdout_external_scoring": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "source_property_release": False,
        "Qwall_release": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "residual_absorbed_into_internal_nu": False,
        "gate_status_counts": dict(gate_counts),
        "next_required_action": "compute-node medium/fine exact same-label mesh sampling before production harvest",
    }
    dump_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
tags:
  - s13
  - upcomer-exchange
  - production-harvest
  - fail-closed
related:
  - {rel(S13_MESH)}
  - {rel(S13_TEMPORAL)}
  - {rel(MF09)}
---

# S13 Upcomer Exchange Production-Harvest/UQ Closeout

This package closes the open S13 production-harvest row from existing evidence only.
It does not launch a scheduler job, sampler, solver, harvest, UQ job, Fluid solve,
source/property release, or admission action.

## Outcome

Decision: `{summary['decision']}`.

The current-coarse exchange evidence is finite and useful as diagnostic thesis
evidence, but production harvest remains blocked. The decisive blocker is missing
medium/fine same-label mesh-family evidence: `{summary['missing_medium_fine_same_label_rows']}`
medium/fine rows are absent, accepted same-label mesh/GCI QOIs are
`{summary['accepted_same_label_mesh_gci_qois']}`, and source/property release-ready
rows are `{summary['source_property_release_ready_rows']}`.

## Open First

- `production_harvest_readiness_gate.csv`
- `exchange_qoi_availability_uq_table.csv`
- `same_label_mesh_gci_blocker_table.csv`
- `s11_decision_table.csv`
- `figures/svg/s13_production_harvest_readiness_status.svg`

## Guardrails

No validation, holdout, or external-test rows were scored. No source/property or
Qwall release was made. No residual was absorbed into internal `Nu`, and ordinary
upcomer `Nu/f_D/K` remains disabled.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
