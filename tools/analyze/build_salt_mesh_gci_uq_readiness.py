#!/usr/bin/env python3
"""Build Salt mesh-UQ readiness and screening GCI diagnostics.

This orchestrates the AGENT-231 read-only follow-on package:

1. coarse-source reconciliation,
2. full-history endpoint monitor reduction,
3. GCI/readiness tables and closure-observation handoff.

Numeric GCI is computed where complete triplet values exist, but rows are marked
publication-ready only when source reconciliation, admission gates, convergence
classification, and asymptotic checks all pass.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.build_salt_mesh_coarse_reconciliation import run as run_coarse  # noqa: E402
from tools.analyze.build_salt_mesh_full_history_monitor_reduction import run as run_monitors  # noqa: E402
from tools.analyze.compute_gci import compute_gci  # noqa: E402
from tools.common import WORKSPACE_ROOT, ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_CATALOG = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_case_catalog.csv"
)
DEFAULT_QUALITY = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_quality_gate.csv"
)
DEFAULT_SCENARIO = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv"
)
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_followon_readiness"
)

MESH_LEVELS = ("coarse", "medium", "fine")
ENDPOINT_CASES = ("salt_test_2_jin", "salt_test_4_jin")
TARGETS = {
    "mdot_abs_mean_kg_s": 2.0,
    "wall_gross_duty_w": 5.0,
    "wall_heat_in_w": 5.0,
    "wall_heat_out_w": 5.0,
    "wall_net_q_w": None,
    "yplus_global_max": None,
    "yplus_patch_average_mean": None,
    "temperature_probe_mean_K": None,
    "wall_temperature_probe_mean_K": None,
    "lower_leg_f_debuoyed": 2.0,
    "test_section_span_f_debuoyed": 2.0,
    "left_lower_leg_nu_or_htc": 5.0,
}

READINESS_FIELDS = [
    "case_id",
    "quantity",
    "units",
    "coarse_value",
    "medium_value",
    "fine_value",
    "r21",
    "r32",
    "coarse_source_status",
    "coarse_gate_verdict",
    "medium_gate_verdict",
    "fine_gate_verdict",
    "coarse_series_verdict",
    "medium_series_verdict",
    "fine_series_verdict",
    "numeric_triplet_complete",
    "gci_numeric_status",
    "mesh_uq_status",
    "target_gci_fine_pct",
    "blocker",
    "source_note",
]

GCI_FIELDS = [
    "case_id",
    "quantity",
    "units",
    "coarse",
    "medium",
    "fine",
    "r21",
    "r32",
    "verdict",
    "order_status",
    "observed_order_p",
    "f_exact_richardson",
    "gci_fine_pct",
    "gci_coarse_pct",
    "asymptotic_range_ratio",
    "gci_trustworthy",
    "mesh_uq_status",
    "publication_ready",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--quality", default=str(DEFAULT_QUALITY))
    parser.add_argument("--scenario-contract", default=str(DEFAULT_SCENARIO))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def numeric(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def quality_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_id"], row["mesh_level"]): row for row in rows}


def catalog_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["case_id"], row["mesh_level"]): row for row in rows}


def monitor_value_map(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    out: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if row.get("monitor") in {"mdot_monitor_mean", "wallHeatFlux", "yPlus", "temperature_probes", "wall_temperature_probes"}:
            out[(row["case_id"], row["mesh_level"], row["quantity"])] = row
    return out


def coarse_status_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def mesh_ratios(catalog: dict[tuple[str, str], dict[str, str]], case_id: str) -> tuple[float, float]:
    fine = numeric(catalog[(case_id, "fine")].get("bulk_cell_size"))
    medium = numeric(catalog[(case_id, "medium")].get("bulk_cell_size"))
    coarse = numeric(catalog[(case_id, "coarse")].get("bulk_cell_size"))
    if fine is None or medium is None or coarse is None or fine <= 0 or medium <= 0:
        return 1.5, 1.5
    return medium / fine, coarse / medium


def source_rows_for_quantity(
    case_id: str,
    quantity: str,
    monitors: dict[tuple[str, str, str], dict[str, str]],
) -> dict[str, dict[str, str]]:
    return {level: monitors.get((case_id, level, quantity), {}) for level in MESH_LEVELS}


def row_value(row: dict[str, str]) -> float | None:
    return numeric(row.get("mean_value"))


def gate_verdict(qmap: dict[tuple[str, str], dict[str, str]], case_id: str, level: str) -> str:
    return qmap.get((case_id, level), {}).get("gate_verdict", "missing")


def series_verdict(rows: dict[str, dict[str, str]], level: str) -> str:
    return rows.get(level, {}).get("series_verdict", "missing_monitor")


def status_for(
    *,
    complete: bool,
    coarse_reconciliation: str,
    gates: dict[str, str],
    series: dict[str, str],
    gci: dict[str, Any] | None,
    target: float | None,
    quantity: str,
) -> tuple[str, str, str]:
    if quantity in {"lower_leg_f_debuoyed", "test_section_span_f_debuoyed", "left_lower_leg_nu_or_htc"}:
        return "blocked_requires_mesh_level_extraction", "medium_fine_pressure_or_thermal_closure_qoi_not_extracted", "not_computed"
    if not complete:
        return "blocked_missing_triplet_qoi", "one_or_more_mesh_levels_missing_numeric_qoi", "not_computed"
    if coarse_reconciliation == "superseded_by_mainline":
        return (
            "blocked_coarse_superseded_by_mainline",
            "external_coarse_source_is_superseded_by_mainline_continuation",
            "screening_gci_only",
        )
    elif coarse_reconciliation in {"same_as_mainline", "compatible_but_not_identical"}:
        numeric_status = "candidate_gci_computed"
        status = "candidate_pending_admission"
        blocker = "none"
    else:
        return "blocked_coarse_not_reconciled", "coarse_source_not_reconciled", "screening_gci_only"
    if any(gates[level] != "admitted_for_gci_input" for level in ("medium", "fine")):
        return (
            "blocked_level_not_admitted",
            "medium_or_fine_level_not_admitted_for_gci_input",
            numeric_status,
        )
    if any(series[level] in {"drifting_or_oscillatory", "short_or_partial", "missing_monitor"} for level in MESH_LEVELS):
        status = "blocked_monitor_not_stationary"
        blocker = "one_or_more_mesh_levels_has_nonstationary_or_missing_monitor_summary"
    if gci is not None and gci.get("gci_trustworthy") is not True:
        status = "blocked_gci_not_trustworthy"
        blocker = "computed_gci_failed_monotonic_or_asymptotic_check"
    if gci is not None and target is not None and numeric(gci.get("gci_fine_pct")) is not None and gci["gci_fine_pct"] > target:
        status = "blocked_gci_exceeds_target"
        blocker = "fine_grid_gci_exceeds_protocol_target"
    if status == "candidate_pending_admission" and gci is not None and gci.get("gci_trustworthy") is True:
        status = "mesh_uq_ready"
        blocker = "none"
    return status, blocker, numeric_status


def build_readiness(
    catalog_rows: list[dict[str, str]],
    quality_rows: list[dict[str, str]],
    monitor_rows: list[dict[str, str]],
    coarse_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cmap = catalog_map(catalog_rows)
    qmap = quality_map(quality_rows)
    mmap = monitor_value_map(monitor_rows)
    coarse = coarse_status_map(coarse_rows)
    readiness: list[dict[str, Any]] = []
    gci_rows: list[dict[str, Any]] = []

    for case_id in ENDPOINT_CASES:
        r21, r32 = mesh_ratios(cmap, case_id)
        for quantity, target in TARGETS.items():
            units = "dimensionless"
            if quantity.endswith("_w"):
                units = "W"
            elif quantity == "mdot_abs_mean_kg_s":
                units = "kg/s"
            elif quantity.endswith("_K"):
                units = "K"
            rows = source_rows_for_quantity(case_id, quantity, mmap)
            values = {level: row_value(rows[level]) for level in MESH_LEVELS}
            complete = all(values[level] is not None for level in MESH_LEVELS)
            gates = {level: gate_verdict(qmap, case_id, level) for level in MESH_LEVELS}
            series = {level: series_verdict(rows, level) for level in MESH_LEVELS}
            coarse_verdict = coarse.get(case_id, {}).get("reconciliation_verdict", "missing")
            gci: dict[str, Any] | None = None
            if complete:
                gci = compute_gci(values["coarse"], values["medium"], values["fine"], r21, r32)
            status, blocker, numeric_status = status_for(
                complete=complete,
                coarse_reconciliation=coarse_verdict,
                gates=gates,
                series=series,
                gci=gci,
                target=target,
                quantity=quantity,
            )
            readiness.append(
                {
                    "case_id": case_id,
                    "quantity": quantity,
                    "units": units,
                    "coarse_value": values["coarse"] if values["coarse"] is not None else "",
                    "medium_value": values["medium"] if values["medium"] is not None else "",
                    "fine_value": values["fine"] if values["fine"] is not None else "",
                    "r21": r21,
                    "r32": r32,
                    "coarse_source_status": coarse_verdict,
                    "coarse_gate_verdict": gates["coarse"],
                    "medium_gate_verdict": gates["medium"],
                    "fine_gate_verdict": gates["fine"],
                    "coarse_series_verdict": series["coarse"],
                    "medium_series_verdict": series["medium"],
                    "fine_series_verdict": series["fine"],
                    "numeric_triplet_complete": "yes" if complete else "no",
                    "gci_numeric_status": numeric_status,
                    "mesh_uq_status": status,
                    "target_gci_fine_pct": "" if target is None else target,
                    "blocker": blocker,
                    "source_note": "full_history_monitor_reduction" if rows else "requires_dedicated_extraction",
                }
            )
            if gci is not None:
                gci_rows.append(
                    {
                        "case_id": case_id,
                        "quantity": quantity,
                        "units": units,
                        "coarse": values["coarse"],
                        "medium": values["medium"],
                        "fine": values["fine"],
                        "r21": r21,
                        "r32": r32,
                        "verdict": gci["verdict"],
                        "order_status": gci["order_status"],
                        "observed_order_p": gci["observed_order_p"],
                        "f_exact_richardson": gci["f_exact_richardson"],
                        "gci_fine_pct": gci["gci_fine_pct"],
                        "gci_coarse_pct": gci["gci_coarse_pct"],
                        "asymptotic_range_ratio": gci["asymptotic_range_ratio"],
                        "gci_trustworthy": gci["gci_trustworthy"],
                        "mesh_uq_status": status,
                        "publication_ready": "yes" if status == "mesh_uq_ready" else "no",
                        "note": gci["gci_note"],
                    }
                )
    return readiness, gci_rows


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Salt Mesh-Refinement Follow-On Readiness

Generated: `{summary['generated_at']}`

## Summary

This package implements the read-only follow-on plan after AGENT-228. It
reconciles external coarse endpoint sources, merges full-history endpoint
postProcessing monitors, and computes screening GCI diagnostics where complete
triplets exist. It does not stage, register, submit continuations, update
closure observations, or mutate native solver outputs.

## Outputs

- `coarse_reconciliation.csv`: external coarse Salt 2/4 Jin source status versus
  current mainline continuations.
- `endpoint_full_history_monitor_summary.csv`: merged restart-segment monitor
  summaries for Salt 2/4 Jin coarse/medium/fine.
- `endpoint_postprocessing_family_coverage.csv`: postProcessing coverage by
  family, including velocity-profile snapshot coverage.
- `mesh_uq_readiness.csv`: per-QoI readiness and blocker table.
- `gci_results.csv`: numeric screening GCI diagnostics for complete triplets,
  with publication readiness kept separate.
- `closure_observation_mesh_uq_handoff.md`: downstream observation-table update
  guidance.

## Observed Facts

- Coarse reconciliation verdict counts: `{summary['coarse_verdict_counts']}`.
- Monitor row count: `{summary['monitor_row_count']}`.
- Mesh-UQ readiness counts: `{summary['mesh_uq_status_counts']}`.
- Publication-ready GCI rows: `{summary['publication_ready_gci_rows']}`.

## Interpretation

The package intentionally keeps numeric screening GCI separate from admitted
mesh uncertainty. Salt 2 has complete endpoint monitor triplets, but its external
coarse source is marked as superseded by the repo's mainline continuation. Salt 4
has complete monitor triplets for some QoIs but medium/fine remain blocked by
the earlier quality gate. Pressure/thermal closure QoIs such as debuoyed
friction and Nu/HTC still require medium/fine extraction before GCI can be
computed.
"""
    path.write_text(text, encoding="utf-8")


def write_handoff(path: Path, readiness_rows: list[dict[str, Any]], gci_rows: list[dict[str, Any]]) -> None:
    ready = [row for row in readiness_rows if row["mesh_uq_status"] == "mesh_uq_ready"]
    text = f"""# Closure Observation Mesh-UQ Handoff

Do not update `closure_observations.csv` from this pass.

Observed result:

- Mesh-UQ-ready rows: `{len(ready)}`.
- Numeric GCI rows are screening diagnostics unless `publication_ready=yes`.
- Existing July 8 closure observations should remain `mesh_status=coarse_no_gci`
  and current `fit_use_status` values until a later task has admitted mesh-UQ
  bands.

Recommended next action:

1. Reconcile mainline coarse endpoint values with the external coarse mesh-family
   source before using Salt 2 GCI bands.
2. Decide whether Salt 4 medium/fine need continuation or can be admitted by a
   stronger full-history evidence gate.
3. Extract medium/fine pressure and thermal closure QoIs before attempting GCI
   for debuoyed friction, apparent friction, Nu, or HTC.
4. Only then update closure observations with explicit mesh uncertainty fields.
"""
    path.write_text(text, encoding="utf-8")


def run(catalog_path: Path, quality_path: Path, scenario_path: Path, output_dir: Path) -> dict[str, Any]:
    out = ensure_dir(output_dir)
    coarse_summary = run_coarse(catalog_path, quality_path, scenario_path, out)
    monitor_summary = run_monitors(catalog_path, out)
    catalog_rows = read_csv(catalog_path)
    quality_rows = read_csv(quality_path)
    coarse_rows = read_csv(out / "coarse_reconciliation.csv")
    monitor_rows = read_csv(out / "endpoint_full_history_monitor_summary.csv")
    readiness_rows, gci_rows = build_readiness(catalog_rows, quality_rows, monitor_rows, coarse_rows)
    write_csv(out / "mesh_uq_readiness.csv", readiness_rows, READINESS_FIELDS)
    write_csv(out / "gci_results.csv", gci_rows, GCI_FIELDS)
    status_counts: dict[str, int] = {}
    for row in readiness_rows:
        status_counts[row["mesh_uq_status"]] = status_counts.get(row["mesh_uq_status"], 0) + 1
    publication_ready = sum(1 for row in gci_rows if row["publication_ready"] == "yes")
    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-231",
        "input_catalog": rel(catalog_path),
        "input_quality": rel(quality_path),
        "input_scenario_contract": rel(scenario_path),
        "output_dir": rel(out),
        "coarse_verdict_counts": coarse_summary["verdict_counts"],
        "monitor_row_count": monitor_summary["monitor_row_count"],
        "coverage_row_count": monitor_summary["coverage_row_count"],
        "readiness_row_count": len(readiness_rows),
        "gci_row_count": len(gci_rows),
        "publication_ready_gci_rows": publication_ready,
        "mesh_uq_status_counts": dict(sorted(status_counts.items())),
        "source_tree_read_only": True,
        "registry_updated": False,
        "staging_updated": False,
        "closure_observations_updated": False,
        "continuation_jobs_submitted": False,
        "generated_files": [
            rel(out / "coarse_reconciliation.csv"),
            rel(out / "endpoint_full_history_monitor_summary.csv"),
            rel(out / "endpoint_postprocessing_family_coverage.csv"),
            rel(out / "mesh_uq_readiness.csv"),
            rel(out / "gci_results.csv"),
            rel(out / "closure_observation_mesh_uq_handoff.md"),
            rel(out / "README.md"),
            rel(out / "summary.json"),
        ],
    }
    write_handoff(out / "closure_observation_mesh_uq_handoff.md", readiness_rows, gci_rows)
    write_json(out / "summary.json", summary)
    write_readme(out / "README.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(Path(args.catalog), Path(args.quality), Path(args.scenario_contract), Path(args.output_dir))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
