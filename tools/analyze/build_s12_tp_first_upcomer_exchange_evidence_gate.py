#!/usr/bin/env python3.11
"""Build a TP-first S12 upcomer-exchange evidence gate from existing artifacts."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TASK_ID = "TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate"

S12_TRAIN = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/finite_train_metric_table.csv"
S12_DISPOSITION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/candidate_disposition_table.csv"
S13_TREND = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/s13_exchange_trend_table.csv"
S13_SAMPLE_GATES = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/s13_sampled_field_gate_matrix.csv"
S13_PRODUCTION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/production_readiness_gate.csv"
S13_SOURCE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/source_property_conservation_release.csv"
S13_UQ = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/same_qoi_uq_matrix.csv"
S13_EXACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/downstream_gate.csv"
SCORE_SHAPE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch/signed_error_shape_metrics.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    return float(value)


def boolish(value: str) -> bool:
    return value.strip().lower() == "true"


def build_tp_priority_context() -> list[dict[str, object]]:
    rows = [r for r in read_csv(SCORE_SHAPE) if r["model_form_id"] == "M3"]
    by_case: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], {})[row["sensor_kind"]] = row

    out: list[dict[str, object]] = []
    for case_id in sorted(by_case):
        tp = by_case[case_id]["TP"]
        tw = by_case[case_id]["TW"]
        tp_rmse = f(tp, "rmse_K")
        tw_rmse = f(tw, "rmse_K")
        out.append(
            {
                "case_id": case_id,
                "model_form_id": "M3",
                "tp_rmse_K": tp_rmse,
                "tw_rmse_K": tw_rmse,
                "tp_minus_tw_rmse_K": tp_rmse - tw_rmse,
                "tp_mean_signed_error_K": f(tp, "mean_signed_error_K"),
                "tw_mean_signed_error_K": f(tw, "mean_signed_error_K"),
                "tp_local_shape_rmse_after_bias_K": f(tp, "local_shape_rmse_after_bias_K"),
                "tw_local_shape_rmse_after_bias_K": f(tw, "local_shape_rmse_after_bias_K"),
                "priority_interpretation": "TP is lower RMSE than TW for current M3, but remains cold-biased and thesis-priority relevant.",
                "candidate_use": "context_only_not_final_locked_split",
            }
        )
    return out


def build_train_context() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in read_csv(S12_TRAIN):
        family = row["metric_family"]
        if family in {"TP", "TW", "all_probe"}:
            value = f(row, "rmse_K")
            unit = "K"
        elif family == "mdot":
            value = f(row, "residual_mdot_kg_s")
            unit = "kg/s residual"
        else:
            value = f(row, "pressure_residual_Pa")
            unit = "Pa residual"
        out.append(
            {
                "candidate_id": row["candidate_id"],
                "metric_family": family,
                "split_role": row["split_role"],
                "finite_count": row["finite_count"],
                "primary_value": value,
                "unit": unit,
                "use_class": "train_only_context_not_candidate_freeze",
                "tp_first_interpretation": "S12-HIAX1 has finite train metrics, but the TP error is too large and too under-gated for promotion." if family == "TP" else "supporting train-only context",
            }
        )
    return out


def build_exchange_evidence() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in read_csv(S13_TREND):
        out.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "mdot_exchange_net_proxy_kg_s": row["mdot_exchange_net_proxy_kg_s"],
                "mdot_exchange_positive_outward_proxy_kg_s": row["mdot_exchange_positive_outward_proxy_kg_s"],
                "mdot_exchange_negative_inward_proxy_kg_s": row["mdot_exchange_negative_inward_proxy_kg_s"],
                "tau_recirc_proxy_s": row["tau_recirc_proxy_s"],
                "interface_core_T_area_avg_K": row["interface_core_T_area_avg_K"],
                "seeded_cv_T_volume_avg_K": row["seeded_cv_T_volume_avg_K"],
                "trusted_wall_T_area_avg_K": row["trusted_wall_T_area_avg_K"],
                "delta_T_wall_minus_core_K": row["delta_T_wall_minus_core_K"],
                "source_side_q_net_W": row["source_side_q_net_W"],
                "hA_source_side_proxy_W_K": row["hA_source_side_proxy_W_K"],
                "tp_relevance": "directly relevant to TP through exchange residence time, bulk/core thermal state, and source-side energy balance",
                "release_status": "diagnostic_only_no_production_harvest_no_coefficient_admission",
            }
        )
    return out


def build_gate_matrix() -> list[dict[str, object]]:
    s12_train = read_csv(S12_TRAIN)
    s12_disp = read_csv(S12_DISPOSITION)
    s13_trend = read_csv(S13_TREND)
    sample_gates = read_csv(S13_SAMPLE_GATES)
    production = read_csv(S13_PRODUCTION)
    exact = read_csv(S13_EXACT)
    source_rows = read_csv(S13_SOURCE)
    uq_rows = read_csv(S13_UQ)

    exact_release = {r["gate"]: boolish(r["allowed"]) for r in exact}
    production_gate = {r["gate"]: r for r in production}

    return [
        {
            "gate": "tp_priority_declared",
            "status": "pass",
            "production_ready": False,
            "blocks_s12_freeze": False,
            "evidence": "User priority shifted from TW-dominant residual repair to TP-first thermal-level/exchange evidence.",
            "next_action": "Use TP as the primary S12 continuation QOI.",
        },
        {
            "gate": "finite_s12_hiax1_train_tp_context",
            "status": "pass_diagnostic",
            "production_ready": False,
            "blocks_s12_freeze": True,
            "evidence": f"TP train RMSE = {next(r['rmse_K'] for r in s12_train if r['metric_family'] == 'TP')} K; candidate disposition = {next(r['disposition'] for r in s12_disp if r['candidate_or_lane'] == 'S12-HIAX1')}.",
            "next_action": "Do not freeze; use only as train-only stress signal.",
        },
        {
            "gate": "finite_exchange_proxy_rows",
            "status": "pass_diagnostic",
            "production_ready": False,
            "blocks_s12_freeze": True,
            "evidence": f"{len(s13_trend)} retained-window rows have finite mdot_exchange proxy, tau proxy, wall/core T, and source-side q.",
            "next_action": "Convert proxies into production-harvested QOIs before promotion.",
        },
        {
            "gate": "exact_pressure_and_qwall_target_window",
            "status": "partial_release",
            "production_ready": False,
            "blocks_s12_freeze": True,
            "evidence": f"exact pressure released={exact_release.get('exact_pressure_basis', False)}; Q_wall_W released={exact_release.get('Q_wall_W', False)}; production sampler refresh remains separate.",
            "next_action": "Join exact pressure/Qwall to exchange rows without relabeling source-side Q as wall heat flux.",
        },
        {
            "gate": "source_property_conservation_release",
            "status": "fail",
            "production_ready": False,
            "blocks_s12_freeze": True,
            "evidence": f"{sum(boolish(r['source_property_release_allowed_now']) for r in source_rows)} source/property-release rows allowed out of {len(source_rows)}.",
            "next_action": "Release cp, property mode, source validity envelope, source use category, pressure/enthalpy basis, and energy residual equation.",
        },
        {
            "gate": "same_qoi_uq",
            "status": "fail",
            "production_ready": False,
            "blocks_s12_freeze": True,
            "evidence": f"{sum(boolish(r['same_qoi_uq_ready']) for r in uq_rows)} same-QOI UQ-ready rows out of {len(uq_rows)}.",
            "next_action": "Run same-label target-minus/target-plus and mesh/GCI UQ after exact QOI contract.",
        },
        {
            "gate": "production_harvest",
            "status": production_gate["production_harvest"]["status"],
            "production_ready": False,
            "blocks_s12_freeze": True,
            "evidence": production_gate["production_harvest"]["reason"],
            "next_action": "Claim a production-harvest row only after source/property and same-QOI UQ are ready.",
        },
        {
            "gate": "validation_holdout_external_scoring",
            "status": "not_consumed",
            "production_ready": False,
            "blocks_s12_freeze": False,
            "evidence": "This package consumes existing train/diagnostic evidence only and performs no protected split scoring.",
            "next_action": "Keep protected splits closed until a frozen runtime-legal S12 candidate exists.",
        },
    ]


def build_next_queue() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "task": "TP-first retained-window join",
            "objective": "Join S13 exchange proxies with exact pressure and Q_wall_W on the same retained windows.",
            "why_it_matters_for_tp": "TP is governed by bulk/core energy state, residence time, pressure-driven exchange, and heat input/removal balance.",
            "allowed_now": True,
            "forbidden": "do not use protected split scoring; do not use source-side Q as wallHeatFlux; do not fit a coefficient",
        },
        {
            "priority": 2,
            "task": "source/property release audit",
            "objective": "Attach cp, property mode, source validity envelope, source use category, pressure/enthalpy basis, and residual-equation sign.",
            "why_it_matters_for_tp": "TP-first exchange cannot become a physical energy closure without source/property legality.",
            "allowed_now": True,
            "forbidden": "no coefficient admission or empirical correction release",
        },
        {
            "priority": 3,
            "task": "same-QOI neighbor-window UQ",
            "objective": "Harvest exact same-label target-minus and target-plus windows for mdot_exchange, tau, wall/core T contrast, pressure, and energy residual.",
            "why_it_matters_for_tp": "TP evidence needs uncertainty on the same variables used to explain TP drift or bias.",
            "allowed_now": False,
            "forbidden": "no mesh/time uncertainty borrowing from unrelated QOIs",
        },
        {
            "priority": 4,
            "task": "freeze review only after upstream gates",
            "objective": "Revisit S12-HIAX1 only if production harvest, source/property release, and same-QOI UQ pass.",
            "why_it_matters_for_tp": "Prevents a large train-only TP residual from being mistaken for a validated model correction.",
            "allowed_now": False,
            "forbidden": "no final score, no protected split scoring, no residual absorption into internal Nu",
        },
    ]


def write_svg(tp_rows: list[dict[str, object]]) -> None:
    svg_dir = OUT / "figures/svg"
    svg_dir.mkdir(parents=True, exist_ok=True)
    max_rmse = max(max(float(r["tp_rmse_K"]), float(r["tw_rmse_K"])) for r in tp_rows)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360">',
        '<rect width="900" height="360" fill="#ffffff"/>',
        '<text x="40" y="42" font-family="Arial" font-size="24" fill="#111">S12 TP-first context: M3 TP vs TW RMSE</text>',
        '<text x="40" y="70" font-family="Arial" font-size="13" fill="#444">TP is the priority QOI; S12 remains diagnostic until exchange/source/UQ gates pass.</text>',
    ]
    y = 110
    scale = 560 / max_rmse
    for row in tp_rows:
        tp_w = float(row["tp_rmse_K"]) * scale
        tw_w = float(row["tw_rmse_K"]) * scale
        lines.extend(
            [
                f'<text x="40" y="{y + 18}" font-family="Arial" font-size="15" fill="#111">{row["case_id"]}</text>',
                f'<rect x="130" y="{y}" width="{tp_w:.2f}" height="20" fill="#2f6f9f"/>',
                f'<text x="{140 + tp_w:.2f}" y="{y + 15}" font-family="Arial" font-size="12" fill="#111">TP {float(row["tp_rmse_K"]):.2f} K</text>',
                f'<rect x="130" y="{y + 26}" width="{tw_w:.2f}" height="20" fill="#b25d2a"/>',
                f'<text x="{140 + tw_w:.2f}" y="{y + 41}" font-family="Arial" font-size="12" fill="#111">TW {float(row["tw_rmse_K"]):.2f} K</text>',
            ]
        )
        y += 72
    lines.extend(
        [
            '<text x="40" y="330" font-family="Arial" font-size="12" fill="#555">No freeze, final score, source/property release, protected split scoring, or residual absorption into internal Nu.</text>',
            "</svg>",
        ]
    )
    (svg_dir / "s12_tp_first_exchange_status.svg").write_text("\n".join(lines) + "\n")


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    tp_rows = build_tp_priority_context()
    train_rows = build_train_context()
    exchange_rows = build_exchange_evidence()
    gate_rows = build_gate_matrix()
    queue_rows = build_next_queue()

    write_csv(
        OUT / "s12_tp_priority_context.csv",
        tp_rows,
        [
            "case_id",
            "model_form_id",
            "tp_rmse_K",
            "tw_rmse_K",
            "tp_minus_tw_rmse_K",
            "tp_mean_signed_error_K",
            "tw_mean_signed_error_K",
            "tp_local_shape_rmse_after_bias_K",
            "tw_local_shape_rmse_after_bias_K",
            "priority_interpretation",
            "candidate_use",
        ],
    )
    write_csv(
        OUT / "s12_hiax1_train_only_context.csv",
        train_rows,
        ["candidate_id", "metric_family", "split_role", "finite_count", "primary_value", "unit", "use_class", "tp_first_interpretation"],
    )
    write_csv(
        OUT / "s12_tp_exchange_evidence_table.csv",
        exchange_rows,
        [
            "case_id",
            "time_window_s",
            "mdot_exchange_net_proxy_kg_s",
            "mdot_exchange_positive_outward_proxy_kg_s",
            "mdot_exchange_negative_inward_proxy_kg_s",
            "tau_recirc_proxy_s",
            "interface_core_T_area_avg_K",
            "seeded_cv_T_volume_avg_K",
            "trusted_wall_T_area_avg_K",
            "delta_T_wall_minus_core_K",
            "source_side_q_net_W",
            "hA_source_side_proxy_W_K",
            "tp_relevance",
            "release_status",
        ],
    )
    write_csv(
        OUT / "s12_tp_unlock_gate_matrix.csv",
        gate_rows,
        ["gate", "status", "production_ready", "blocks_s12_freeze", "evidence", "next_action"],
    )
    write_csv(
        OUT / "s12_tp_next_executable_queue.csv",
        queue_rows,
        ["priority", "task", "objective", "why_it_matters_for_tp", "allowed_now", "forbidden"],
    )
    claim_rows = [
        {
            "claim": "S12 continuation should be TP-first, not TW-only.",
            "status": "allowed",
            "basis": "User priority plus M3 signed-error scoreboard show TP remains cold-biased and thesis-relevant.",
        },
        {
            "claim": "S13 exchange proxies are useful upstream evidence for S12.",
            "status": "allowed_diagnostic_only",
            "basis": "Finite retained-window mdot_exchange proxy, tau proxy, wall/core T, and source-side q rows exist for Salt2/Salt3/Salt4.",
        },
        {
            "claim": "S12-HIAX1 can be frozen or scored as final.",
            "status": "forbidden",
            "basis": "Production harvest, same-QOI UQ, source/property release, and attribution freeze remain closed.",
        },
        {
            "claim": "Large TP can be absorbed into internal Nu.",
            "status": "forbidden",
            "basis": "Residual ownership must stay outside internal Nu until sign/heat-balance/source/UQ gates pass.",
        },
    ]
    write_csv(OUT / "s12_tp_claim_boundary.csv", claim_rows, ["claim", "status", "basis"])
    guardrails = [
        {"guardrail": "native_output_mutation", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "protected_split_scoring", "status": False},
        {"guardrail": "source_property_or_qwall_release", "status": False},
        {"guardrail": "candidate_freeze_or_final_score", "status": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "status": False},
    ]
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, ["guardrail", "status"])
    sources = [
        S12_TRAIN,
        S12_DISPOSITION,
        S13_TREND,
        S13_SAMPLE_GATES,
        S13_PRODUCTION,
        S13_SOURCE,
        S13_UQ,
        S13_EXACT,
        SCORE_SHAPE,
    ]
    write_csv(
        OUT / "source_manifest.csv",
        [{"source_path": str(p.relative_to(ROOT)), "used_read_only": True, "native_output": False} for p in sources],
        ["source_path", "used_read_only", "native_output"],
    )
    write_svg(tp_rows)

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),
        "decision": "tp_first_s12_exchange_continuation_diagnostic_only",
        "tp_priority_rows": len(tp_rows),
        "train_context_rows": len(train_rows),
        "exchange_evidence_rows": len(exchange_rows),
        "unlock_gate_rows": len(gate_rows),
        "next_queue_rows": len(queue_rows),
        "m3_tp_rmse_below_tw_rmse_all_cases": all(float(r["tp_rmse_K"]) < float(r["tw_rmse_K"]) for r in tp_rows),
        "production_ready_rows": sum(1 for r in gate_rows if r["production_ready"]),
        "s12_freeze_allowed": False,
        "source_property_or_qwall_release": False,
        "protected_split_scoring": False,
        "final_score_values": 0,
        "scheduler_action": False,
        "native_output_mutation": False,
        "fluid_or_external_repo_mutation": False,
        "residual_absorbed_into_internal_nu": False,
        "figure_svg": str((OUT / "figures/svg/s12_tp_first_exchange_status.svg").relative_to(ROOT)),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_readmes(summary)
    return summary


def write_readmes(summary: dict[str, object]) -> None:
    frontmatter = f"""---
provenance:
  - {S12_TRAIN.relative_to(ROOT)}
  - {S13_TREND.relative_to(ROOT)}
  - {S13_PRODUCTION.relative_to(ROOT)}
  - {SCORE_SHAPE.relative_to(ROOT)}
tags: [s12, tp-first, upcomer-exchange, diagnostic-only]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - operational_notes/07-26/22/2026-07-22_S12_TP_FIRST_UPCOMER_EXCHANGE_EVIDENCE_GATE.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Hydraulics / Tester / Writer / Reviewer
type: work_product
status: complete
---
"""
    readme = frontmatter + f"""# S12 TP-First Upcomer Exchange Evidence Gate

Decision: `{summary["decision"]}`.

This package continues S12 scientifically, but reframes the next useful work
around TP rather than TW-only residual ownership. The available evidence says:

- S12-HIAX1 has finite train-only TP/TW/mdot/pressure context, but remains not
  frozen.
- Current M3 TP RMSE is lower than TW RMSE across Salt2/Salt3/Salt4, but TP is
  still cold-biased and is a valid thesis-priority QOI.
- S13 retained-window exchange proxies are finite for Salt2/Salt3/Salt4 and
  are directly relevant to TP through residence time, core/bulk temperature,
  pressure, and source-side energy balance.
- Production harvest, same-QOI UQ, source/property release, final score, and
  freeze are still closed.

Primary files:

- `s12_tp_priority_context.csv`
- `s12_hiax1_train_only_context.csv`
- `s12_tp_exchange_evidence_table.csv`
- `s12_tp_unlock_gate_matrix.csv`
- `s12_tp_next_executable_queue.csv`
- `s12_tp_claim_boundary.csv`
- `figures/svg/s12_tp_first_exchange_status.svg`

Guardrails: no protected split scoring, no source/property or new
Qwall release, no candidate freeze, no final score, no scheduler action, no
native-output mutation, and no residual absorption into internal Nu.
"""
    (OUT / "README.md").write_text(readme)
    handoff = frontmatter.replace("type: work_product", "type: report") + """# Thesis Handoff: TP-First S12 Continuation

Use this as the S12 continuation note after the prior no-freeze disposition.
The key thesis statement is:

> S12 should continue, if at all, as a TP-first upcomer/exchange energy-state
> evidence path. The current evidence supports the mechanism diagnostically but
> not a frozen correction.

Recommended table set:

- `s12_tp_priority_context.csv`: why TP is the priority QOI even though TW is
  larger in some residual-owner views.
- `s12_tp_exchange_evidence_table.csv`: finite retained-window exchange
  proxies.
- `s12_tp_unlock_gate_matrix.csv`: exact blockers before S12 promotion.
- `s12_tp_next_executable_queue.csv`: next scientific tasks.

Do not claim protected split scoring, source/property
release, Qwall release by this package, coefficient admission, final score,
candidate freeze, or internal-Nu residual absorption.
"""
    (OUT / "thesis_tp_first_handoff.md").write_text(handoff)


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
