#!/usr/bin/env python3
"""Consolidate corner_lower_right two-tap admission repair evidence."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-TWO-TAP-CORNER-LOWER-RIGHT-ADMISSION-REPAIR"
FEATURE = "corner_lower_right"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_corner_lower_right_admission_repair"

ENDPOINT_DIR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler"
ENDPOINT_ROWS = ENDPOINT_DIR / "raw_endpoint_pressure_velocity.csv"
ISOLATION_DIR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision"
ISOLATION_AUDIT = ISOLATION_DIR / "component_isolation_audit.csv"
UQ_DIR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status"
UQ_AUDIT = UQ_DIR / "same_qoi_uncertainty_audit.csv"
SEPARATED_DIR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review"
FINAL_GATE = SEPARATED_DIR / "final_gate_review.csv"
STATUS = ROOT / ".agent/status/2026-07-20_TODO-TWO-TAP-CORNER-LOWER-RIGHT-ADMISSION-REPAIR.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/two-tap-corner-lower-right-admission-repair.md"
IMPORT = ROOT / "imports/2026-07-20_two_tap_corner_lower_right_admission_repair.json"

CASE_ORDER = ("salt_2", "salt_3", "salt_4")
RAF_THRESHOLD = 0.01
RMF_THRESHOLD = 0.01


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: str) -> float:
    if value == "":
        return float("nan")
    return float(value)


def require_sources() -> None:
    required = [ENDPOINT_ROWS, ISOLATION_AUDIT, UQ_AUDIT, FINAL_GATE]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing two-tap admission repair sources: " + "; ".join(missing))


def endpoint_rows_by_case() -> dict[str, list[dict[str, str]]]:
    rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(ENDPOINT_ROWS):
        if row["feature"] == FEATURE and row["case_id"] in CASE_ORDER:
            rows[row["case_id"]].append(row)
    return rows


def row_by_case(path: Path) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(path) if row.get("feature") == FEATURE}


def build_endpoint_reverse_flow_gate() -> list[dict[str, Any]]:
    grouped = endpoint_rows_by_case()
    rows: list[dict[str, Any]] = []
    for case_id in CASE_ORDER:
        endpoints = sorted(grouped[case_id], key=lambda row: row["tap_role"])
        if len(endpoints) != 2:
            raise ValueError(f"Expected two endpoint rows for {case_id}, found {len(endpoints)}")
        upstream = next(row for row in endpoints if row["tap_role"] == "upstream")
        downstream = next(row for row in endpoints if row["tap_role"] == "downstream")
        upstream_raf = fnum(upstream["reverse_area_fraction"])
        downstream_raf = fnum(downstream["reverse_area_fraction"])
        upstream_rmf = fnum(upstream["reverse_mass_fraction"])
        downstream_rmf = fnum(downstream["reverse_mass_fraction"])
        aggregate_raf = max(upstream_raf, downstream_raf)
        aggregate_rmf = max(upstream_rmf, downstream_rmf)
        gate_pass = aggregate_raf < RAF_THRESHOLD and aggregate_rmf < RMF_THRESHOLD
        rows.append(
            {
                "case_id": case_id,
                "case_key": upstream["case_key"],
                "feature": FEATURE,
                "upstream_station_label": upstream["station_label"],
                "downstream_station_label": downstream["station_label"],
                "upstream_sample_status": upstream["sample_status"],
                "downstream_sample_status": downstream["sample_status"],
                "upstream_reverse_area_fraction": upstream["reverse_area_fraction"],
                "downstream_reverse_area_fraction": downstream["reverse_area_fraction"],
                "aggregate_reverse_area_fraction": f"{aggregate_raf:.12g}",
                "upstream_reverse_mass_fraction": upstream["reverse_mass_fraction"],
                "downstream_reverse_mass_fraction": downstream["reverse_mass_fraction"],
                "aggregate_reverse_mass_fraction": f"{aggregate_rmf:.12g}",
                "reverse_flow_gate": "pass_low_reverse_flow" if gate_pass else "fail_material_reverse_flow",
                "ordinary_component_k_candidate": str(gate_pass).lower(),
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "guardrail": "ordinary component K requires aggregate RAF < 0.01 and RMF < 0.01 at both endpoints",
                "source_path": rel(ENDPOINT_ROWS),
            }
        )
    return rows


def build_component_isolation_ledger() -> list[dict[str, Any]]:
    isolation = row_by_case(ISOLATION_AUDIT)
    rows = []
    for case_id in CASE_ORDER:
        row = isolation[case_id]
        rows.append(
            {
                "case_id": case_id,
                "case_key": row["case_key"],
                "feature": row["feature"],
                "basis_status": row["basis_status"],
                "recirculation_gate": row["recirculation_gate"],
                "prior_centerline_K_local": row["prior_centerline_K_local"],
                "selected_component_isolation_label": row["selected_component_isolation_label"],
                "component_isolation_gate": row["component_isolation_gate"],
                "component_isolation_decision": row["decision"],
                "ordinary_component_k_candidate": "false",
                "component_k_admitted": row["component_k_admitted"],
                "f6_fit_performed": row["f6_fit_performed"],
                "next_action": row["next_action"],
                "guardrail": row["guardrail"],
                "source_path": rel(ISOLATION_AUDIT),
            }
        )
    return rows


def build_same_qoi_uq_family() -> list[dict[str, Any]]:
    uq = row_by_case(UQ_AUDIT)
    rows = []
    for case_id in CASE_ORDER:
        row = uq[case_id]
        rows.append(
            {
                "case_id": case_id,
                "case_key": row["case_key"],
                "feature": row["feature"],
                "qoi": row["qoi"],
                "same_endpoint_labels": row["same_endpoint_labels"],
                "same_formula_status": row["same_formula_status"],
                "time_uncertainty_status": row["time_uncertainty_status"],
                "mesh_uncertainty_status": row["mesh_uncertainty_status"],
                "same_qoi_uncertainty_gate": row["same_qoi_uncertainty_gate"],
                "decision": row["decision"],
                "component_k_admitted": row["component_k_admitted"],
                "f6_fit_performed": row["f6_fit_performed"],
                "guardrail": row["guardrail"],
                "source_path": rel(UQ_AUDIT),
            }
        )
    return rows


def build_split_decision(
    endpoint_gate: list[dict[str, Any]],
    isolation_ledger: list[dict[str, Any]],
    uq_family: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    final = row_by_case(FINAL_GATE)
    by_endpoint = {row["case_id"]: row for row in endpoint_gate}
    by_iso = {row["case_id"]: row for row in isolation_ledger}
    by_uq = {row["case_id"]: row for row in uq_family}
    rows = []
    for case_id in CASE_ORDER:
        final_row = final[case_id]
        endpoint = by_endpoint[case_id]
        iso = by_iso[case_id]
        uq = by_uq[case_id]
        failed = [
            gate
            for gate, value in [
                ("endpoint_reverse_flow_gate", endpoint["reverse_flow_gate"]),
                ("component_isolation_gate", iso["component_isolation_gate"]),
                ("same_qoi_uncertainty_gate", uq["same_qoi_uncertainty_gate"]),
            ]
            if str(value).startswith("fail")
        ]
        rows.append(
            {
                "case_id": case_id,
                "case_key": final_row["case_key"],
                "feature": FEATURE,
                "endpoint_reverse_flow_gate": endpoint["reverse_flow_gate"],
                "component_isolation_gate": iso["component_isolation_gate"],
                "same_qoi_uncertainty_gate": uq["same_qoi_uncertainty_gate"],
                "failed_gates": ";".join(failed),
                "ordinary_component_k_candidate": "false",
                "admission_decision": final_row["admission_decision"],
                "selected_label": iso["selected_component_isolation_label"],
                "split_use": "diagnostic_only_not_fit_or_model_selection",
                "component_k_admitted": final_row["component_k_admitted"],
                "f6_fit_performed": final_row["f6_fit_performed"],
                "next_action": "seek nonrecirculating anchor or keep section-effective diagnostic treatment",
                "guardrail": "material reverse-flow or missing same-QOI UQ forbids ordinary component-K/F6 admission",
                "source_path": rel(FINAL_GATE),
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (ENDPOINT_ROWS, "raw endpoint pressure/velocity/reverse-flow evidence"),
        (ISOLATION_AUDIT, "component-isolation decision"),
        (UQ_AUDIT, "same-QOI uncertainty audit"),
        (FINAL_GATE, "separated final admission gate"),
    ]
    return [
        {
            "source_id": path.stem,
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "source_role": role,
            "mutation": "read_only",
        }
        for path, role in sources
    ]


def write_status_files(summary: dict[str, Any]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        "\n".join(
            [
                f"# {TASK}",
                "",
                "- status: complete",
                f"- feature: {FEATURE}",
                f"- rows: {summary['case_count']}",
                f"- component_k_admitted_rows: {summary['component_k_admitted_rows']}",
                f"- output: {rel(OUT)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(
        "\n".join(
            [
                f"# {DATE} two-tap corner lower-right admission repair",
                "",
                "Consolidated endpoint reverse-flow, component-isolation, same-QOI UQ, and split decisions.",
                "Current Salt2/Salt3/Salt4 rows remain diagnostic-only.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        IMPORT,
        {
            "task": TASK,
            "date": DATE,
            "output_dir": rel(OUT),
            "native_solver_outputs_mutated": False,
            "generated_index_refreshed": False,
            "summary_path": rel(OUT / "summary.json"),
        },
    )


def write_readme(summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# Two-Tap Corner Lower-Right Admission Repair",
                "",
                "This package consolidates current Salt2/Salt3/Salt4 corner_lower_right two-tap evidence into the requested admission tables.",
                "It does not run new sampling and does not admit ordinary component K or F6 rows.",
                "",
                "Primary outputs:",
                "",
                "- `endpoint_reverse_flow_gate.csv`",
                "- `component_isolation_ledger.csv`",
                "- `same_qoi_uq_family.csv`",
                "- `split_decision.csv`",
                "- `summary.json`",
                "",
                f"Rows: {summary['case_count']}.",
                f"Reverse-flow pass rows: {summary['reverse_flow_pass_rows']}.",
                f"Same-QOI UQ pass rows: {summary['same_qoi_uq_pass_rows']}.",
                f"Component-K admitted rows: {summary['component_k_admitted_rows']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> dict[str, Any]:
    require_sources()
    endpoint_gate = build_endpoint_reverse_flow_gate()
    isolation_ledger = build_component_isolation_ledger()
    uq_family = build_same_qoi_uq_family()
    split_decision = build_split_decision(endpoint_gate, isolation_ledger, uq_family)
    source_manifest = build_source_manifest()

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "feature": FEATURE,
        "case_count": len(split_decision),
        "reverse_flow_pass_rows": sum(row["endpoint_reverse_flow_gate"] == "pass_low_reverse_flow" for row in split_decision),
        "component_isolation_pass_rows": sum(not row["component_isolation_gate"].startswith("fail") for row in split_decision),
        "same_qoi_uq_pass_rows": sum(not row["same_qoi_uncertainty_gate"].startswith("fail") for row in split_decision),
        "ordinary_component_k_candidates": sum(row["ordinary_component_k_candidate"] == "true" for row in split_decision),
        "component_k_admitted_rows": sum(row["component_k_admitted"] == "true" for row in split_decision),
        "f6_fit_performed": False,
        "split_decision": "diagnostic_only_apparent_cluster_recirculation_blocked_missing_UQ",
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "endpoint_reverse_flow_gate.csv", endpoint_gate)
    write_csv(OUT / "component_isolation_ledger.csv", isolation_ledger)
    write_csv(OUT / "same_qoi_uq_family.csv", uq_family)
    write_csv(OUT / "split_decision.csv", split_decision)
    write_csv(OUT / "source_manifest.csv", source_manifest)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
