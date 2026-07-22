#!/usr/bin/env python3
"""S13 medium/fine mesh-sensitivity disposition.

This builder consumes the completed exact-label medium/fine split rerun and
reports what can be claimed before any production harvest. It deliberately does
not run a formal Grid Convergence Index unless a same-label coarse/medium/fine
triplet exists.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_mesh_gci_disposition"
)
SPLIT_RERUN = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_exact_label_split_rerun"
)
TEMPORAL_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)

QOI_LABELS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]

QOI_COLUMN = {
    "Q_wall_W": "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s": "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s": "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K": "wall_core_bulk_temperature_contrast_K",
}

UNITS = {
    "Q_wall_W": "W",
    "mdot_exchange_positive_outward_proxy_kg_s": "kg/s",
    "tau_recirc_proxy_s": "s",
    "wall_core_bulk_temperature_contrast_K": "K",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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


def pct(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    value = 100.0 * abs(numerator) / abs(denominator)
    if not math.isfinite(value):
        return None
    return value


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite value: {text}")
    return value


def require_inputs() -> None:
    required = [
        SPLIT_RERUN / "summary.json",
        SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv",
        SPLIT_RERUN / "aggregated_terminal_window_reductions.csv",
        SPLIT_RERUN / "mesh_gci_unlock_gate.csv",
        TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 mesh/GCI disposition inputs: " + "; ".join(missing))


def rows_by_key(rows: list[dict[str, str]], *fields: str) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in fields)].append(row)
    return grouped


def classify_medium_fine_spread(qoi_label: str, max_relative_percent: float | None) -> str:
    if max_relative_percent is None:
        return "medium_fine_spread_unquantified_fail_closed"
    if qoi_label == "Q_wall_W" and max_relative_percent <= 1.0:
        return "medium_fine_spread_low_diagnostic_only_formal_gci_blocked"
    if max_relative_percent <= 5.0:
        return "medium_fine_spread_moderate_diagnostic_only_formal_gci_blocked"
    return "medium_fine_spread_large_fail_closed_formal_gci_blocked"


def build_case_qoi_spread(
    qoi_rows: list[dict[str, str]], terminal_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    qoi_by_case_mesh = rows_by_key(qoi_rows, "case_id", "mesh_level", "qoi_label")
    reductions_by_case_mesh = rows_by_key(terminal_rows, "case_id", "mesh_level")
    case_ids = sorted({row["case_id"] for row in qoi_rows})
    output: list[dict[str, Any]] = []

    for case_id in case_ids:
        for qoi_label in QOI_LABELS:
            medium_qoi = qoi_by_case_mesh[(case_id, "medium", qoi_label)]
            fine_qoi = qoi_by_case_mesh[(case_id, "fine", qoi_label)]
            medium_terminal = [row for row in medium_qoi if row["window_role"] == "terminal"]
            fine_terminal = [row for row in fine_qoi if row["window_role"] == "terminal"]
            if len(medium_terminal) != 1 or len(fine_terminal) != 1:
                raise ValueError(f"expected one terminal row for {case_id} {qoi_label}")

            medium_value = finite_float(medium_terminal[0]["value"])
            fine_value = finite_float(fine_terminal[0]["value"])
            delta = medium_value - fine_value
            relative_percent = pct(delta, fine_value)

            temporal_stats: dict[str, dict[str, Any]] = {}
            for mesh_level in ["medium", "fine"]:
                column = QOI_COLUMN[qoi_label]
                values = [finite_float(row[column]) for row in reductions_by_case_mesh[(case_id, mesh_level)]]
                if len(values) != 3:
                    raise ValueError(f"expected three terminal-window reductions for {case_id} {mesh_level}")
                span = max(values) - min(values)
                terminal_value = medium_value if mesh_level == "medium" else fine_value
                temporal_stats[mesh_level] = {
                    "mean": mean(values),
                    "span": span,
                    "half_range": 0.5 * span,
                    "half_range_percent": pct(0.5 * span, terminal_value),
                }

            temporal_half_range_max = max(
                temporal_stats["medium"]["half_range"], temporal_stats["fine"]["half_range"]
            )
            mesh_to_temporal_ratio = (
                abs(delta) / temporal_half_range_max if temporal_half_range_max != 0.0 else None
            )
            output.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi_label,
                    "unit": UNITS[qoi_label],
                    "medium_terminal_value": medium_value,
                    "fine_terminal_value": fine_value,
                    "medium_minus_fine": delta,
                    "medium_fine_relative_percent_vs_fine": relative_percent,
                    "medium_window_mean": temporal_stats["medium"]["mean"],
                    "fine_window_mean": temporal_stats["fine"]["mean"],
                    "medium_window_half_range": temporal_stats["medium"]["half_range"],
                    "fine_window_half_range": temporal_stats["fine"]["half_range"],
                    "medium_window_half_range_percent": temporal_stats["medium"]["half_range_percent"],
                    "fine_window_half_range_percent": temporal_stats["fine"]["half_range_percent"],
                    "mesh_delta_to_max_window_half_range_ratio": mesh_to_temporal_ratio,
                    "same_label_medium_fine_rows_exist": True,
                    "same_label_coarse_row_exists": False,
                    "formal_gci_status": "blocked_missing_same_label_coarse_member",
                    "admission_allowed": False,
                }
            )
    return output


def build_qoi_summary(
    case_rows: list[dict[str, Any]], temporal_uq_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    temporal_by_qoi = {row["qoi_label"]: row for row in temporal_uq_rows}
    output: list[dict[str, Any]] = []
    for qoi_label in QOI_LABELS:
        rows = [row for row in case_rows if row["qoi_label"] == qoi_label]
        relative_values = [
            float(row["medium_fine_relative_percent_vs_fine"])
            for row in rows
            if row["medium_fine_relative_percent_vs_fine"] is not None
        ]
        max_relative = max(relative_values) if relative_values else None
        mean_relative = mean(relative_values) if relative_values else None
        max_mesh_to_temporal = max(
            float(row["mesh_delta_to_max_window_half_range_ratio"])
            for row in rows
            if row["mesh_delta_to_max_window_half_range_ratio"] is not None
        )
        temporal = temporal_by_qoi[qoi_label]
        disposition = classify_medium_fine_spread(qoi_label, max_relative)
        output.append(
            {
                "qoi_label": qoi_label,
                "case_count": len(rows),
                "medium_fine_case_rows": len(rows),
                "max_medium_fine_relative_percent_vs_fine": max_relative,
                "mean_medium_fine_relative_percent_vs_fine": mean_relative,
                "max_mesh_delta_to_window_half_range_ratio": max_mesh_to_temporal,
                "same_qoi_temporal_uq_status": temporal["same_qoi_temporal_uq_status"],
                "same_qoi_temporal_max_relative_percent": temporal[
                    "max_relative_temporal_uncertainty_percent"
                ],
                "same_label_medium_fine_evidence": True,
                "same_label_coarse_evidence": False,
                "formal_gci_status": "blocked_missing_same_label_coarse_member",
                "diagnostic_disposition": disposition,
                "production_harvest_allowed": False,
                "admission_allowed": False,
                "coefficient_fit_allowed": False,
            }
        )
    return output


def build_blocker_table() -> list[dict[str, Any]]:
    return [
        {
            "blocker": "formal_three_grid_gci",
            "status": "blocked",
            "evidence": "medium/fine exact-label rows exist; same-label coarse member is absent from this family",
            "required_to_clear": "produce or admit strict same-label coarse/medium/fine triplets for each QOI, or document an explicit equivalence contract that survives review",
            "production_consequence": "no formal GCI, no production harvest, no S13 admission",
        },
        {
            "blocker": "source_property_qwall_release",
            "status": "blocked_out_of_scope",
            "evidence": "this package reads Q_wall_W diagnostic rows but does not prove source/property or Qwall release",
            "required_to_clear": "separate source/property and source-side heat-flow equivalence package with same-QOI UQ",
            "production_consequence": "do not use Q_wall_W as admitted closure target here",
        },
        {
            "blocker": "exchange_cell_coefficients",
            "status": "blocked",
            "evidence": "mesh sensitivity is diagnostic and formal GCI is blocked",
            "required_to_clear": "clear same-label mesh/GCI, same-window UQ, source/property release, and model-form gate",
            "production_consequence": "no exchange-cell coefficient fitting",
        },
    ]


def build_production_gate(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate": "split_rerun_exact_label_rows",
            "status": "pass",
            "pass": True,
            "evidence": f"aggregated_exact_label_qoi_rows={summary['aggregated_exact_label_qoi_rows']}; successful_case_mesh_pairs={summary['successful_case_mesh_pairs']}",
            "consequence": "diagnostic medium/fine spread can be computed",
        },
        {
            "gate": "same_label_medium_fine_mesh_sensitivity",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": "medium and fine rows exist for Salt2/Salt3/Salt4 and four exact labels",
            "consequence": "mesh sensitivity can be reported as two-level diagnostic evidence only",
        },
        {
            "gate": "same_label_three_grid_gci",
            "status": "fail_closed_missing_coarse",
            "pass": False,
            "evidence": "same_label_coarse_row_exists=false for all case/QOI rows",
            "consequence": "no formal Richardson/GCI admission",
        },
        {
            "gate": "production_harvest_or_admission",
            "status": "do_not_run",
            "pass": False,
            "evidence": "formal GCI, source/property release, and coefficient-prerequisite gates remain closed",
            "consequence": "no S11/S13/S15/S6 trigger and no coefficient fit",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {
            "artifact": "split_rerun_summary",
            "path": rel(SPLIT_RERUN / "summary.json"),
            "role": "controls successful exact-label medium/fine rerun counts",
            "mutation_status": "read_only",
        },
        {
            "artifact": "exact_label_qoi_rows",
            "path": rel(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv"),
            "role": "terminal and neighbor-window exact-label QOI values",
            "mutation_status": "read_only",
        },
        {
            "artifact": "terminal_window_reductions",
            "path": rel(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv"),
            "role": "three terminal-window reductions per case/mesh for within-window stability",
            "mutation_status": "read_only",
        },
        {
            "artifact": "temporal_uq_summary",
            "path": rel(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv"),
            "role": "prior same-QOI temporal UQ context; not a mesh substitute",
            "mutation_status": "read_only",
        },
    ]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SPLIT_RERUN / "summary.json")}
  - {rel(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")}
  - {rel(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv")}
  - {rel(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv")}
tags: [work-product, s13, recirculation, exchange-cell, mesh-gci, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-medium-fine-mesh-gci-disposition.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Medium/Fine Mesh-GCI Disposition

This package consumes the completed S13 exact-label split rerun and reports
medium/fine mesh sensitivity for the four exchange-cell QOIs. It does not run a
formal Grid Convergence Index because this evidence family has no strict
same-label coarse member.

## Decision

`{summary["decision"]}`

## What Is Defensible

- `case_qoi_medium_fine_spread.csv` quantifies Salt2/Salt3/Salt4 medium/fine
  spread for `Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
  `tau_recirc_proxy_s`, and `wall_core_bulk_temperature_contrast_K`.
- `qoi_mesh_disposition_summary.csv` separates low diagnostic spread from
  large fail-closed spread.
- `formal_gci_blocker_table.csv` records why formal Richardson/GCI remains
  blocked.

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid source,
external repo, thesis body, source/property release, Qwall release, coefficient
fit, validation/holdout/external score, production harvest, or generated docs
index was mutated.
"""


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    split_summary = read_json(SPLIT_RERUN / "summary.json")
    qoi_rows = read_csv(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")
    terminal_rows = read_csv(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv")
    temporal_uq_rows = read_csv(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv")

    case_spread = build_case_qoi_spread(qoi_rows, terminal_rows)
    qoi_summary = build_qoi_summary(case_spread, temporal_uq_rows)
    blockers = build_blocker_table()
    gate = build_production_gate(split_summary)
    manifest = build_source_manifest()

    max_qwall_spread = next(
        row["max_medium_fine_relative_percent_vs_fine"]
        for row in qoi_summary
        if row["qoi_label"] == "Q_wall_W"
    )
    max_proxy_spread = max(
        row["max_medium_fine_relative_percent_vs_fine"]
        for row in qoi_summary
        if row["qoi_label"] != "Q_wall_W"
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "medium_fine_mesh_disposition_complete_formal_gci_fail_closed_no_admission",
        "source_split_decision": split_summary["decision"],
        "case_qoi_spread_rows": len(case_spread),
        "qoi_summary_rows": len(qoi_summary),
        "qoi_labels": QOI_LABELS,
        "same_label_medium_fine_rows_exist": True,
        "same_label_coarse_rows_exist": False,
        "formal_gci_run": False,
        "formal_gci_status": "blocked_missing_same_label_coarse_member",
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "source_property_release": False,
        "Qwall_release": False,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "validation_holdout_external_scoring": False,
        "proxy_substitution": False,
        "max_Q_wall_medium_fine_relative_percent_vs_fine": max_qwall_spread,
        "max_proxy_medium_fine_relative_percent_vs_fine": max_proxy_spread,
    }

    write_csv(
        OUT / "case_qoi_medium_fine_spread.csv",
        case_spread,
        [
            "case_id",
            "qoi_label",
            "unit",
            "medium_terminal_value",
            "fine_terminal_value",
            "medium_minus_fine",
            "medium_fine_relative_percent_vs_fine",
            "medium_window_mean",
            "fine_window_mean",
            "medium_window_half_range",
            "fine_window_half_range",
            "medium_window_half_range_percent",
            "fine_window_half_range_percent",
            "mesh_delta_to_max_window_half_range_ratio",
            "same_label_medium_fine_rows_exist",
            "same_label_coarse_row_exists",
            "formal_gci_status",
            "admission_allowed",
        ],
    )
    write_csv(
        OUT / "qoi_mesh_disposition_summary.csv",
        qoi_summary,
        [
            "qoi_label",
            "case_count",
            "medium_fine_case_rows",
            "max_medium_fine_relative_percent_vs_fine",
            "mean_medium_fine_relative_percent_vs_fine",
            "max_mesh_delta_to_window_half_range_ratio",
            "same_qoi_temporal_uq_status",
            "same_qoi_temporal_max_relative_percent",
            "same_label_medium_fine_evidence",
            "same_label_coarse_evidence",
            "formal_gci_status",
            "diagnostic_disposition",
            "production_harvest_allowed",
            "admission_allowed",
            "coefficient_fit_allowed",
        ],
    )
    write_csv(
        OUT / "formal_gci_blocker_table.csv",
        blockers,
        ["blocker", "status", "evidence", "required_to_clear", "production_consequence"],
    )
    write_csv(
        OUT / "production_admission_gate.csv",
        gate,
        ["gate", "status", "pass", "evidence", "consequence"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        manifest,
        ["artifact", "path", "role", "mutation_status"],
    )
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    global OUT
    if args.output_dir is not None:
        OUT = args.output_dir
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
