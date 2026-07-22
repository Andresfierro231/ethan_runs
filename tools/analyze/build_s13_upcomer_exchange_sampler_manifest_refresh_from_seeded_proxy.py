#!/usr/bin/env python3
"""Refresh S13 sampler manifest readiness from seeded diagnostic proxy evidence."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-REFRESH-FROM-SEEDED-PROXY-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy"
)
AVERAGE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
)
CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"
)
SURFACE_VTK = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv"
)
SAMPLER_PREFLIGHT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
)
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def contract_gate_map() -> dict[str, dict[str, str]]:
    return {row["gate"]: row for row in read_csv(CONTRACT / "sampler_refresh_gate.csv")}


def proxy_manifest_rows() -> list[dict[str, Any]]:
    metrics = by_case(read_csv(AVERAGE / "diagnostic_average_exchange_metrics.csv"))
    gates = contract_gate_map()
    limited_context_open = gates["limited_scheduler_sampled_field_extraction"]["allowed"] == "true"
    production_refresh_blocked = gates["sampler_manifest_refresh"]["allowed"] == "false"
    rows = []
    for case_id, metric in metrics.items():
        proxy_ready = (
            metric["release_status"] == "diagnostic_average_proxy_only"
            and limited_context_open
            and production_refresh_blocked
        )
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": metric["time_window_s"],
                "sampler_proxy_ready": str(proxy_ready).lower(),
                "production_sampler_ready": "false",
                "geometry_vtk_ready": "true",
                "average_U_T_rho_ready": "true",
                "source_sink_context_ready": "true",
                "Q_wall_W_ready": "false",
                "pressure_basis_ready": "false",
                "cp_ready": "false",
                "same_qoi_uq_ready": "false",
                "mdot_exchange_proxy_kg_s": metric["mdot_exchange_positive_outward_proxy_kg_s"],
                "tau_recirc_proxy_s": metric["tau_recirc_proxy_s"],
                "hA_source_side_proxy_W_K": metric["hA_source_side_proxy_W_K"],
                "release_status": "sampler_proxy_ready_nonproduction" if proxy_ready else "blocked",
                "blocking_reason": "production blocked by missing Q_wall_W, pressure basis, cp, sampled surface fields, and same-QOI UQ",
            }
        )
    return rows


def input_gate_rows() -> list[dict[str, Any]]:
    missing = read_csv(AVERAGE / "missing_gate_matrix.csv")
    rows = []
    for row in missing:
        rows.append(
            {
                "input_gate": row["gate"],
                "status": row["status"],
                "blocks_production_sampler": "true",
                "allows_proxy_context": row["diagnostic_average_proxy_allows_progress"],
                "blocking_reason": row["blocking_reason"],
            }
        )
    return rows


def downstream_rows() -> list[dict[str, str]]:
    return [
        {
            "gate": "production_harvest",
            "status": "blocked",
            "allowed": "false",
            "reason": "proxy-ready rows are nonproduction and same-QOI UQ/Q_wall/pressure/cp remain absent",
        },
        {
            "gate": "same_qoi_uq",
            "status": "blocked_pending_production_qois",
            "allowed": "false",
            "reason": "UQ must be run on exact production QOIs, not proxy-only rows",
        },
        {
            "gate": "s12_diagnostic_context",
            "status": "available",
            "allowed": "true",
            "reason": "proxy rows can support documented diagnostic/negative-result reasoning",
        },
        {
            "gate": "s11_s15_s6_or_coefficient_admission",
            "status": "blocked",
            "allowed": "false",
            "reason": "no production sampler harvest or same-QOI UQ exists",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only package inputs"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "sampler_or_harvest_launch", "changed": "false", "policy": "manifest refresh only; no sampler/harvest"},
        {"guard_id": "same_qoi_uq_or_admission", "changed": "false", "policy": "no UQ/admission/trigger"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "residual remains explicit and non-fitted"},
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        (AVERAGE / "diagnostic_average_exchange_metrics.csv", "read diagnostic average proxy metrics"),
        (AVERAGE / "missing_gate_matrix.csv", "read missing production gates"),
        (CONTRACT / "sampler_refresh_gate.csv", "read sampled-field/Qwall contract gate"),
        (SURFACE_VTK / "released_surface_vtk_manifest.csv", "read geometry VTK manifest"),
        (SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv", "read prior sampler preflight"),
        (UQ_DESIGN / "summary.json", "read UQ status"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(AVERAGE / "diagnostic_average_exchange_metrics.csv")}
  - {rel(CONTRACT / "sampler_refresh_gate.csv")}
tags: [s13, upcomer-exchange, sampler-manifest, proxy-ready, fail-closed]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Reviewer / Tester / Writer
type: work_product
status: complete
---
# S13 Sampler Manifest Refresh From Seeded Proxy

This package refreshes sampler readiness after the seeded diagnostic average
reduction. It separates proxy readiness from production sampler readiness.

Result: `{summary["decision"]}`.

- sampler proxy-ready rows: `{summary["sampler_proxy_ready_rows"]}`
- production sampler-ready rows: `{summary["production_sampler_ready_rows"]}`
- production harvest allowed: `false`
- same-QOI UQ allowed: `false`
- coefficient/admission trigger: `false`
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build(out_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(out_dir)
    proxy = proxy_manifest_rows()
    inputs = input_gate_rows()
    downstream = downstream_rows()
    guards = guardrail_rows()
    manifest = source_manifest_rows()
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "proxy_ready_rows_released_production_sampler_blocked",
        "case_count": len(proxy),
        "sampler_proxy_ready_rows": sum(1 for row in proxy if row["sampler_proxy_ready"] == "true"),
        "production_sampler_ready_rows": sum(1 for row in proxy if row["production_sampler_ready"] == "true"),
        "production_harvest_allowed": False,
        "same_qoi_uq_allowed": False,
        "coefficient_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "sampler_or_harvest_launched": False,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out_dir / "sampler_proxy_manifest.csv", list(proxy[0]), proxy)
    csv_dump(out_dir / "production_input_gate_matrix.csv", list(inputs[0]), inputs)
    csv_dump(out_dir / "downstream_gate.csv", list(downstream[0]), downstream)
    csv_dump(out_dir / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out_dir / "source_manifest.csv", list(manifest[0]), manifest)
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
