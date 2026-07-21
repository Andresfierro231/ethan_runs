#!/usr/bin/env python3
"""Advance corner_lower_right two-tap isolation and same-QOI UQ status."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-20"
TASK = "TODO-TWO-TAP-CORNER-LOWER-RIGHT-ISOLATION-UQ-PROGRESS"
FEATURE = "corner_lower_right"
OUT = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_corner_lower_right_isolation_uq_progress"

ENDPOINT_DIR = ROOT / "work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler"
ENDPOINT_ROWS = ENDPOINT_DIR / "raw_endpoint_pressure_velocity.csv"
CASE_SAMPLING_PLAN = ENDPOINT_DIR / "case_sampling_plan.csv"
REPAIR_DIR = ROOT / "work_products/2026-07/2026-07-20/2026-07-20_two_tap_corner_lower_right_admission_repair"
REVERSE_GATE = REPAIR_DIR / "endpoint_reverse_flow_gate.csv"
ISOLATION_LEDGER = REPAIR_DIR / "component_isolation_ledger.csv"
UQ_FAMILY = REPAIR_DIR / "same_qoi_uq_family.csv"
REPAIR_SPLIT = REPAIR_DIR / "split_decision.csv"
REFINED_PRESSURE_CANDIDATES = [
    ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight/outputs/medium/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv",
    ROOT / "work_products/2026-07/2026-07-09/2026-07-09_salt2_fine_closure_qoi_smoke_and_overnight/outputs/fine/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv",
    ROOT / "work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/outputs/medium/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv",
    ROOT / "work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/outputs/fine/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv",
]
STATUS = ROOT / ".agent/status/2026-07-20_TODO-TWO-TAP-CORNER-LOWER-RIGHT-ISOLATION-UQ-PROGRESS.md"
JOURNAL = ROOT / ".agent/journal/2026-07-20/two-tap-corner-lower-right-isolation-uq-progress.md"
IMPORT = ROOT / "imports/2026-07-20_two_tap_corner_lower_right_isolation_uq_progress.json"

CASE_ORDER = ("salt_2", "salt_3", "salt_4")
UPSTREAM_LABEL = "lower_leg__s04"
DOWNSTREAM_LABEL = "right_leg__s00"


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
    return float(value) if value != "" else float("nan")


def require_sources() -> None:
    required = [ENDPOINT_ROWS, CASE_SAMPLING_PLAN, REVERSE_GATE, ISOLATION_LEDGER, UQ_FAMILY, REPAIR_SPLIT]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing two-tap isolation/UQ sources: " + "; ".join(missing))


def endpoint_rows_by_case() -> dict[str, dict[str, dict[str, str]]]:
    grouped: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in read_csv(ENDPOINT_ROWS):
        if row["feature"] == FEATURE and row["case_id"] in CASE_ORDER:
            grouped[row["case_id"]][row["tap_role"]] = row
    for case_id in CASE_ORDER:
        if set(grouped[case_id]) != {"upstream", "downstream"}:
            raise ValueError(f"Expected upstream/downstream endpoint rows for {case_id}")
    return grouped


def table_by_case(path: Path) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(path) if row.get("feature") == FEATURE}


def sampling_plan_by_case() -> dict[str, list[dict[str, str]]]:
    rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CASE_SAMPLING_PLAN):
        if row["feature"] == FEATURE and row["case_id"] in CASE_ORDER:
            rows[row["case_id"]].append(row)
    return rows


def endpoint_time_dirs(case_key: str) -> list[str]:
    root = ROOT / "tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed" / case_key
    pp = root / "postProcessing/agentCTwoTapRawEndpointSurfaces"
    if not pp.exists():
        return []
    return sorted(path.name for path in pp.iterdir() if path.is_dir())


def candidate_pressure_columns(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return set(next(reader, []))


def build_component_isolation_basis() -> list[dict[str, Any]]:
    grouped = endpoint_rows_by_case()
    reverse = table_by_case(REVERSE_GATE)
    rows = []
    for case_id in CASE_ORDER:
        up = grouped[case_id]["upstream"]
        down = grouped[case_id]["downstream"]
        delta_p = fnum(up["p_pa"]) - fnum(down["p_pa"])
        delta_p_rgh = fnum(up["p_rgh_pa"]) - fnum(down["p_rgh_pa"])
        mean_rho = 0.5 * (fnum(up["rho_kg_m3"]) + fnum(down["rho_kg_m3"]))
        rows.append(
            {
                "case_id": case_id,
                "case_key": up["case_key"],
                "feature": FEATURE,
                "endpoint_pair": f"{UPSTREAM_LABEL}->{DOWNSTREAM_LABEL}",
                "pressure_basis_primary": "static_p_pa",
                "upstream_p_pa": up["p_pa"],
                "downstream_p_pa": down["p_pa"],
                "delta_p_static_Pa": f"{delta_p:.12g}",
                "delta_p_sign_convention": "p_upstream_minus_p_downstream",
                "upstream_p_rgh_pa": up["p_rgh_pa"],
                "downstream_p_rgh_pa": down["p_rgh_pa"],
                "delta_p_rgh_Pa": f"{delta_p_rgh:.12g}",
                "p_rgh_conversion_status": "not_reconstructed_missing_exact_hydrostatic_term",
                "mean_endpoint_rho_kg_m3": f"{mean_rho:.12g}",
                "same_window_rho_status": "available_endpoint_mean",
                "same_window_re_status": "missing_not_in_endpoint_sampler",
                "same_window_mu_status": "missing_not_in_endpoint_sampler",
                "reverse_flow_gate": reverse[case_id]["reverse_flow_gate"],
                "basis_decision": "basis_resolved_for_apparent_cluster_static_delta_only",
                "component_k_basis_status": "blocked_reverse_flow_and_missing_same_basis_straight_reference",
                "source_path": rel(ENDPOINT_ROWS),
            }
        )
    return rows


def build_straight_development_subtraction_ledger() -> list[dict[str, Any]]:
    basis = {row["case_id"]: row for row in build_component_isolation_basis()}
    rows = []
    for case_id in CASE_ORDER:
        row = basis[case_id]
        rows.append(
            {
                "case_id": case_id,
                "case_key": row["case_key"],
                "feature": FEATURE,
                "endpoint_pair": row["endpoint_pair"],
                "same_window_re_status": row["same_window_re_status"],
                "same_window_rho_status": row["same_window_rho_status"],
                "same_window_mu_status": row["same_window_mu_status"],
                "straight_reference_status": "blocked_missing_same_basis_reference",
                "development_loss_status": "blocked_missing_same_basis_reference",
                "subtraction_status": "blocked_missing_same_basis_reference",
                "isolated_residual_status": "not_computed_no_same_basis_subtraction",
                "clipping_policy": "no_clipping_no_make_positive_correction",
                "component_k_status": "blocked",
                "guardrail": "straight/development loss must use same endpoint labels, pressure basis, sign convention, retained window, Re/rho/mu",
                "source_path": rel(ENDPOINT_ROWS),
            }
        )
    return rows


def build_apparent_cluster_loss() -> list[dict[str, Any]]:
    basis = build_component_isolation_basis()
    rows = []
    for row in basis:
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "feature": FEATURE,
                "label": "apparent_cluster_loss",
                "endpoint_pair": row["endpoint_pair"],
                "delta_p_static_Pa": row["delta_p_static_Pa"],
                "delta_p_rgh_Pa": row["delta_p_rgh_Pa"],
                "reverse_flow_gate": row["reverse_flow_gate"],
                "diagnostic_use": "allowed_for_residual_accounting_only",
                "fit_use": "not_fit_not_model_selection",
                "decision": "apparent_cluster_loss_diagnostic",
                "guardrail": "do_not_export_as_component_K_or_F6_anchor",
                "source_path": rel(REVERSE_GATE),
            }
        )
    return rows


def build_component_k_decision() -> list[dict[str, Any]]:
    repair = table_by_case(REPAIR_SPLIT)
    subtraction = {row["case_id"]: row for row in build_straight_development_subtraction_ledger()}
    rows = []
    for case_id in CASE_ORDER:
        split = repair[case_id]
        sub = subtraction[case_id]
        failed = [
            split["endpoint_reverse_flow_gate"],
            split["component_isolation_gate"],
            split["same_qoi_uncertainty_gate"],
            sub["subtraction_status"],
        ]
        rows.append(
            {
                "case_id": case_id,
                "case_key": split["case_key"],
                "feature": FEATURE,
                "component_output": "component_K",
                "component_k_status": "component_K_blocked_apparent_cluster_only",
                "selected_diagnostic_output": "apparent_cluster_loss",
                "failed_reasons": ";".join(failed),
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "nonphysical_k_policy": "reject_no_clipping_no_hidden_multiplier",
                "next_action": "seek nonrecirculating same-QOI anchor or keep diagnostic residual accounting",
                "source_path": rel(REPAIR_SPLIT),
            }
        )
    return rows


def build_same_qoi_time_uq() -> list[dict[str, Any]]:
    grouped = endpoint_rows_by_case()
    rows = []
    for case_id in CASE_ORDER:
        up = grouped[case_id]["upstream"]
        dirs = endpoint_time_dirs(up["case_key"])
        same_time_count = len(dirs)
        rows.append(
            {
                "case_id": case_id,
                "case_key": up["case_key"],
                "feature": FEATURE,
                "endpoint_pair": f"{UPSTREAM_LABEL}->{DOWNSTREAM_LABEL}",
                "same_endpoint_labels": "true",
                "same_formula": "delta_p_static_and_K_app_RAF_RMF_same_sign",
                "available_time_dirs": ";".join(dirs),
                "time_family_member_count": same_time_count,
                "time_uq_status": (
                    "available_same_window_neighbors"
                    if same_time_count > 1
                    else "missing_no_same_window_neighbors"
                ),
                "component_k_admitted": "false",
                "source_path": rel(ENDPOINT_ROWS),
            }
        )
    return rows


def build_same_qoi_mesh_uq() -> list[dict[str, Any]]:
    candidates = []
    for path in REFINED_PRESSURE_CANDIDATES:
        columns = candidate_pressure_columns(path)
        has_endpoint_labels = {UPSTREAM_LABEL, DOWNSTREAM_LABEL}.issubset(columns)
        candidates.append(
            {
                "candidate_path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "same_endpoint_labels": str(has_endpoint_labels).lower(),
                "same_formula": "false",
                "same_sign_convention": "false",
                "eligible_for_same_qoi_mesh_uq": "false",
                "reason": "section_mean_pressure_table_not_exact_endpoint_pair_formula",
            }
        )
    rows = []
    for case_id in CASE_ORDER:
        case_key = {
            row["case_id"]: row["case_key"]
            for row in read_csv(REVERSE_GATE)
            if row.get("feature") == FEATURE
        }[case_id]
        rows.append(
            {
                "case_id": case_id,
                "case_key": case_key,
                "feature": FEATURE,
                "endpoint_pair": f"{UPSTREAM_LABEL}->{DOWNSTREAM_LABEL}",
                "mesh_family_status": "candidate_pressure_tables_scanned",
                "eligible_same_qoi_mesh_members": 0,
                "mesh_uq_status": "missing_no_GCI_not_same_qoi",
                "component_k_admitted": "false",
                "candidate_sources_scanned": ";".join(item["candidate_path"] for item in candidates),
                "rejection_reason": "no refined pressure table matched exact endpoint labels, formula, and sign convention",
            }
        )
    return rows


def build_split_decision() -> list[dict[str, Any]]:
    apparent = {row["case_id"]: row for row in build_apparent_cluster_loss()}
    component = {row["case_id"]: row for row in build_component_k_decision()}
    time_uq = {row["case_id"]: row for row in build_same_qoi_time_uq()}
    mesh_uq = {row["case_id"]: row for row in build_same_qoi_mesh_uq()}
    rows = []
    for case_id in CASE_ORDER:
        rows.append(
            {
                "case_id": case_id,
                "case_key": apparent[case_id]["case_key"],
                "feature": FEATURE,
                "apparent_cluster_loss_status": apparent[case_id]["decision"],
                "component_k_status": component[case_id]["component_k_status"],
                "time_uq_status": time_uq[case_id]["time_uq_status"],
                "mesh_uq_status": mesh_uq[case_id]["mesh_uq_status"],
                "split_decision": "diagnostic_only_apparent_cluster_component_K_blocked_missing_UQ",
                "fit_use": "not_fit_not_model_selection",
                "component_k_admitted": "false",
                "f6_fit_performed": "false",
                "next_action": "nonrecirculating_or_same_QOI_mesh_time_anchor_required_for_admission",
            }
        )
    return rows


def build_source_manifest() -> list[dict[str, Any]]:
    sources = [
        (ENDPOINT_ROWS, "raw endpoint pressure/velocity"),
        (CASE_SAMPLING_PLAN, "exact endpoint plane definitions"),
        (REVERSE_GATE, "reverse-flow gate"),
        (ISOLATION_LEDGER, "component isolation prior decision"),
        (UQ_FAMILY, "same-QOI UQ prior decision"),
        (REPAIR_SPLIT, "split/admission decision"),
    ]
    sources.extend((path, "refined pressure candidate checked for same-QOI mesh UQ") for path in REFINED_PRESSURE_CANDIDATES)
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
                f"- case_count: {summary['case_count']}",
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
                f"# {DATE} two-tap lower-right isolation/UQ progress",
                "",
                "Separated apparent cluster-loss diagnostics from blocked component-K admission and audited same-QOI time/mesh UQ.",
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
                "# Two-Tap Corner Lower-Right Isolation And UQ Progress",
                "",
                "This package advances the lower-right two-tap blocker by keeping apparent cluster loss diagnostic and component K blocked.",
                "It also records that same-QOI time and mesh UQ remain unavailable for current evidence.",
                "",
                "Primary outputs:",
                "",
                "- `component_isolation_basis.csv`",
                "- `straight_development_subtraction_ledger.csv`",
                "- `apparent_cluster_loss.csv`",
                "- `component_k_decision.csv`",
                "- `same_qoi_time_uq.csv`",
                "- `same_qoi_mesh_uq.csv`",
                "- `split_decision.csv`",
                "",
                f"Rows: {summary['case_count']}.",
                f"Component-K admitted rows: {summary['component_k_admitted_rows']}.",
                f"Same-QOI mesh UQ pass rows: {summary['same_qoi_mesh_uq_pass_rows']}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> dict[str, Any]:
    require_sources()
    basis = build_component_isolation_basis()
    subtraction = build_straight_development_subtraction_ledger()
    apparent = build_apparent_cluster_loss()
    component = build_component_k_decision()
    time_uq = build_same_qoi_time_uq()
    mesh_uq = build_same_qoi_mesh_uq()
    split = build_split_decision()
    sources = build_source_manifest()
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "feature": FEATURE,
        "case_count": len(split),
        "apparent_cluster_loss_rows": len(apparent),
        "component_k_admitted_rows": sum(row["component_k_admitted"] == "true" for row in split),
        "same_qoi_time_uq_pass_rows": sum(row["time_uq_status"] == "available_same_window_neighbors" for row in split),
        "same_qoi_mesh_uq_pass_rows": sum(row["mesh_uq_status"] != "missing_no_GCI_not_same_qoi" for row in split),
        "f6_fit_performed": False,
        "native_solver_outputs_mutated": False,
        "registry_mutation": "none",
    }

    write_csv(OUT / "component_isolation_basis.csv", basis)
    write_csv(OUT / "straight_development_subtraction_ledger.csv", subtraction)
    write_csv(OUT / "apparent_cluster_loss.csv", apparent)
    write_csv(OUT / "component_k_decision.csv", component)
    write_csv(OUT / "same_qoi_time_uq.csv", time_uq)
    write_csv(OUT / "same_qoi_mesh_uq.csv", mesh_uq)
    write_csv(OUT / "split_decision.csv", split)
    write_csv(OUT / "source_manifest.csv", sources)
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_status_files(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
