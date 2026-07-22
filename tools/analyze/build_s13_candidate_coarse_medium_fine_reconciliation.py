#!/usr/bin/env python3
"""Reconcile S13 current-coarse candidates with canonical medium/fine rows.

This is a diagnostic follow-on to the medium/fine split rerun. It deliberately
does not admit formal GCI when the completed coarse-equivalence contract keeps
the current-coarse rows as reference candidates only.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"
)
SPLIT_RERUN = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_exact_label_split_rerun"
)
MEDIUM_FINE_DISPOSITION = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_mesh_gci_disposition"
)
MESH_FAMILY = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
)
COARSE_CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract"
)
QWALL_GATE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
)

QOI_LABELS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def require_inputs() -> None:
    required = [
        SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv",
        SPLIT_RERUN / "aggregated_terminal_window_reductions.csv",
        SPLIT_RERUN / "summary.json",
        MEDIUM_FINE_DISPOSITION / "qoi_mesh_disposition_summary.csv",
        MESH_FAMILY / "same_label_mesh_family_generated_rows.csv",
        COARSE_CONTRACT / "coarse_basis_resolution.csv",
        COARSE_CONTRACT / "auditable_coarse_equivalence_contract.csv",
        QWALL_GATE / "summary.json",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 reconciliation inputs: " + "; ".join(missing))


def finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite value: {text}")
    return value


def pct(delta: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    value = 100.0 * abs(delta) / abs(denominator)
    return value if math.isfinite(value) else None


def convergence_ratio(coarse: float, medium: float, fine: float) -> float | None:
    coarse_medium = coarse - medium
    if coarse_medium == 0.0:
        return None
    return (medium - fine) / coarse_medium


def classify_convergence(ratio: float | None) -> str:
    if ratio is None:
        return "undefined_equal_coarse_medium"
    if ratio < 0.0:
        return "oscillatory"
    if ratio < 1.0:
        return "monotonic_convergence"
    if ratio == 1.0:
        return "neutral_no_reduction"
    return "monotonic_divergence"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def rows_by_key(rows: list[dict[str, str]], *fields: str) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in fields)].append(row)
    return grouped


def build_triplet_rows(
    coarse_rows: list[dict[str, str]],
    medium_fine_rows: list[dict[str, str]],
    coarse_resolution_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    coarse_by_key = {
        (row["case_id"], row["qoi_label"]): row
        for row in coarse_rows
        if row["mesh_level"] == "current_coarse_continuation"
        and row["row_generation_status"] == "generated_current_coarse_only_not_gci"
    }
    mf_by_key = rows_by_key(medium_fine_rows, "case_id", "mesh_level", "qoi_label", "window_role")
    resolution_by_key = {
        (row["case_id"], row["qoi_label"]): row for row in coarse_resolution_rows
    }
    output: list[dict[str, Any]] = []
    for case_id in ["salt_2", "salt_3", "salt_4"]:
        for qoi_label in QOI_LABELS:
            coarse = coarse_by_key[(case_id, qoi_label)]
            medium = mf_by_key[(case_id, "medium", qoi_label, "terminal")]
            fine = mf_by_key[(case_id, "fine", qoi_label, "terminal")]
            if len(medium) != 1 or len(fine) != 1:
                raise ValueError(f"expected one medium/fine terminal row for {case_id} {qoi_label}")
            coarse_value = finite_float(coarse["target_value"])
            medium_value = finite_float(medium[0]["value"])
            fine_value = finite_float(fine[0]["value"])
            ratio = convergence_ratio(coarse_value, medium_value, fine_value)
            resolution = resolution_by_key[(case_id, qoi_label)]
            coarse_admitted = resolution["coarse_equivalence_admitted"].lower() == "true"
            output.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi_label,
                    "unit": medium[0]["unit"],
                    "coarse_candidate_value": coarse_value,
                    "medium_value": medium_value,
                    "fine_value": fine_value,
                    "coarse_minus_medium": coarse_value - medium_value,
                    "medium_minus_fine": medium_value - fine_value,
                    "coarse_fine_span": coarse_value - fine_value,
                    "coarse_fine_relative_percent_vs_fine": pct(coarse_value - fine_value, fine_value),
                    "medium_fine_relative_percent_vs_fine": pct(medium_value - fine_value, fine_value),
                    "candidate_three_level_convergence_ratio": ratio,
                    "candidate_three_level_convergence_class": classify_convergence(ratio),
                    "current_coarse_candidate_exists": resolution["current_coarse_candidate_exists"],
                    "coarse_equivalence_admitted": coarse_admitted,
                    "direct_same_label_coarse_admitted": resolution["direct_same_label_coarse_admitted"],
                    "formal_gci_status": (
                        "not_run_coarse_equivalence_not_admitted"
                        if not coarse_admitted
                        else "requires_separate_formal_gci_review"
                    ),
                    "diagnostic_use_allowed": True,
                    "production_use_allowed": False,
                    "admission_allowed": False,
                    "source_paths": ";".join(
                        [
                            rel(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv"),
                            rel(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv"),
                            rel(COARSE_CONTRACT / "coarse_basis_resolution.csv"),
                        ]
                    ),
                }
            )
    return output


def build_qoi_summary(
    triplet_rows: list[dict[str, Any]],
    medium_fine_summary_rows: list[dict[str, str]],
    contract_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    mf_by_qoi = {row["qoi_label"]: row for row in medium_fine_summary_rows}
    required_contract_failures = [
        row["criterion"] for row in contract_rows if row["current_status"] != "admitted"
    ]
    output: list[dict[str, Any]] = []
    for qoi_label in QOI_LABELS:
        rows = [row for row in triplet_rows if row["qoi_label"] == qoi_label]
        max_cf = max(float(row["coarse_fine_relative_percent_vs_fine"]) for row in rows)
        max_mf = max(float(row["medium_fine_relative_percent_vs_fine"]) for row in rows)
        classes = sorted({row["candidate_three_level_convergence_class"] for row in rows})
        all_coarse_admitted = all(row["coarse_equivalence_admitted"] for row in rows)
        qwall_low_spread = (
            qoi_label == "Q_wall_W"
            and max_mf <= 1.0
            and mf_by_qoi[qoi_label]["diagnostic_disposition"]
            == "medium_fine_spread_low_diagnostic_only_formal_gci_blocked"
        )
        output.append(
            {
                "qoi_label": qoi_label,
                "case_count": len(rows),
                "current_coarse_candidate_rows": len(rows),
                "medium_fine_rows_available": True,
                "coarse_equivalence_admitted_all_cases": all_coarse_admitted,
                "max_coarse_fine_relative_percent_vs_fine": max_cf,
                "max_medium_fine_relative_percent_vs_fine": max_mf,
                "candidate_three_level_classes": ";".join(classes),
                "formal_gci_status": "blocked_coarse_equivalence_not_admitted",
                "diagnostic_disposition": (
                    "qwall_low_medium_fine_spread_but_coarse_not_admitted"
                    if qwall_low_spread
                    else "diagnostic_only_not_admissible"
                ),
                "production_harvest_allowed": False,
                "admission_allowed": False,
                "coefficient_fit_allowed": False,
                "blocking_contract_criteria": ";".join(required_contract_failures),
            }
        )
    return output


def build_gate() -> list[dict[str, Any]]:
    return [
        {
            "gate": "canonical_medium_fine_exact_label_rows",
            "status": "pass",
            "pass": True,
            "evidence": "canonical split rerun aggregate has medium/fine exact-label terminal rows",
            "consequence": "diagnostic medium/fine and candidate triplet reconciliation can be reported",
        },
        {
            "gate": "current_coarse_candidate_rows",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": "12 current-coarse candidate rows exist from completed mesh-family generation package",
            "consequence": "candidate coarse/medium/fine comparisons can be computed but not admitted",
        },
        {
            "gate": "coarse_equivalence_contract",
            "status": "fail_closed_not_admitted",
            "pass": False,
            "evidence": "completed coarse-equivalence contract admits 0 current-coarse rows",
            "consequence": "formal GCI and production/admission remain closed",
        },
        {
            "gate": "formal_gci",
            "status": "not_run",
            "pass": False,
            "evidence": "coarse member is a non-admitted reference candidate, not an accepted same-label mesh member",
            "consequence": "no GCI uncertainty bound, no S13 release, no coefficient fitting",
        },
        {
            "gate": "qwall_heat_flow_path",
            "status": "diagnostic_continue_only",
            "pass": False,
            "evidence": "Q_wall_W medium/fine spread is low, but source/property/Qwall release and accepted mesh family remain closed",
            "consequence": "use Q_wall_W in thesis as diagnostic evidence, not as an admitted closure target",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {"role": "canonical_medium_fine_qoi_rows", "path": rel(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")},
        {"role": "canonical_medium_fine_reductions", "path": rel(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv")},
        {"role": "medium_fine_disposition", "path": rel(MEDIUM_FINE_DISPOSITION / "qoi_mesh_disposition_summary.csv")},
        {"role": "current_coarse_candidates", "path": rel(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv")},
        {"role": "coarse_equivalence_contract", "path": rel(COARSE_CONTRACT / "coarse_basis_resolution.csv")},
        {"role": "qwall_mesh_gci_gate_context", "path": rel(QWALL_GATE / "summary.json")},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")}
  - {rel(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv")}
  - {rel(COARSE_CONTRACT / "coarse_basis_resolution.csv")}
tags: [work-product, s13, recirculation, exchange-cell, mesh-gci, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-candidate-coarse-medium-fine-reconciliation.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Candidate Coarse/Medium/Fine Reconciliation

Decision: `{summary["decision"]}`.

This package joins the canonical medium/fine exact-label split rerun with the
current-coarse candidate rows from the same-label mesh-family generation
package. It reports candidate three-level behavior, but it does not run or admit
formal GCI because the completed coarse-equivalence contract admits `0`
current-coarse rows as same-label coarse mesh evidence.

`Q_wall_W` remains the only low-spread medium/fine diagnostic lane. The exchange
flux, residence-time, and wall/core/bulk contrast proxies remain diagnostic and
not coefficient-admissible.

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid source,
external repo, thesis body, source/property release, Qwall release, coefficient
fit, validation/holdout/external score, production harvest, or formal GCI
admission was mutated.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    require_inputs()
    coarse_rows = read_csv(MESH_FAMILY / "same_label_mesh_family_generated_rows.csv")
    medium_fine_rows = read_csv(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")
    coarse_resolution_rows = read_csv(COARSE_CONTRACT / "coarse_basis_resolution.csv")
    medium_fine_summary_rows = read_csv(MEDIUM_FINE_DISPOSITION / "qoi_mesh_disposition_summary.csv")
    contract_rows = read_csv(COARSE_CONTRACT / "auditable_coarse_equivalence_contract.csv")

    triplet_rows = build_triplet_rows(coarse_rows, medium_fine_rows, coarse_resolution_rows)
    qoi_summary = build_qoi_summary(triplet_rows, medium_fine_summary_rows, contract_rows)
    gate_rows = build_gate()
    source_manifest = build_source_manifest()

    write_csv(
        OUT / "candidate_triplet_reconciliation.csv",
        triplet_rows,
        [
            "case_id",
            "qoi_label",
            "unit",
            "coarse_candidate_value",
            "medium_value",
            "fine_value",
            "coarse_minus_medium",
            "medium_minus_fine",
            "coarse_fine_span",
            "coarse_fine_relative_percent_vs_fine",
            "medium_fine_relative_percent_vs_fine",
            "candidate_three_level_convergence_ratio",
            "candidate_three_level_convergence_class",
            "current_coarse_candidate_exists",
            "coarse_equivalence_admitted",
            "direct_same_label_coarse_admitted",
            "formal_gci_status",
            "diagnostic_use_allowed",
            "production_use_allowed",
            "admission_allowed",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "qoi_reconciliation_summary.csv",
        qoi_summary,
        [
            "qoi_label",
            "case_count",
            "current_coarse_candidate_rows",
            "medium_fine_rows_available",
            "coarse_equivalence_admitted_all_cases",
            "max_coarse_fine_relative_percent_vs_fine",
            "max_medium_fine_relative_percent_vs_fine",
            "candidate_three_level_classes",
            "formal_gci_status",
            "diagnostic_disposition",
            "production_harvest_allowed",
            "admission_allowed",
            "coefficient_fit_allowed",
            "blocking_contract_criteria",
        ],
    )
    write_csv(
        OUT / "production_admission_gate.csv",
        gate_rows,
        ["gate", "status", "pass", "evidence", "consequence"],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest, ["role", "path"])

    max_qwall_cf = max(
        row["coarse_fine_relative_percent_vs_fine"]
        for row in triplet_rows
        if row["qoi_label"] == "Q_wall_W"
    )
    max_proxy_cf = max(
        row["coarse_fine_relative_percent_vs_fine"]
        for row in triplet_rows
        if row["qoi_label"] != "Q_wall_W"
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "candidate_triplets_quantified_formal_gci_fail_closed_coarse_equivalence_not_admitted",
        "candidate_triplet_rows": len(triplet_rows),
        "qoi_summary_rows": len(qoi_summary),
        "current_coarse_candidate_rows": sum(1 for row in triplet_rows if row["current_coarse_candidate_exists"] == "True"),
        "coarse_equivalence_admitted_rows": sum(1 for row in triplet_rows if row["coarse_equivalence_admitted"]),
        "formal_gci_run": False,
        "formal_gci_status": "blocked_coarse_equivalence_not_admitted",
        "max_Q_wall_candidate_coarse_fine_relative_percent_vs_fine": max_qwall_cf,
        "max_proxy_candidate_coarse_fine_relative_percent_vs_fine": max_proxy_cf,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "source_property_release": False,
        "Qwall_release": False,
        "coefficient_admission": False,
        "validation_holdout_external_scoring": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "proxy_substitution": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
