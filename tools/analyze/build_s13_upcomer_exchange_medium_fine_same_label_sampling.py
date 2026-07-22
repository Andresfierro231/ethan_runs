#!/usr/bin/env python3
"""Inventory medium/fine Salt runs for exact S13 same-label sampling.

This task is a read-only preflight. It does not run OpenFOAM, submit Slurm
jobs, sample fields, compute mesh/GCI, or admit production evidence.
"""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-SAME-LABEL-SAMPLING-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling"
)
MESH_GENERATION = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
)
CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_inventory_and_generation_contract"
)
TEMPORAL_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
REFINEMENT = ROOT / (
    "work_products/2026-07/2026-07-09/"
    "2026-07-09_salt_mesh_refinement_followon_readiness"
)
SOURCE_BASE = Path(
    "/home1/09748/andresfierro231/bubble_flow_loop/"
    "tamu_loop_box/ethan_data/modern_runs/salt"
)

CASES = {
    "salt_2": {"source_case_id": "salt_test_2_jin", "test_number": "2"},
    "salt_3": {"source_case_id": "salt_test_3_jin", "test_number": "3"},
    "salt_4": {"source_case_id": "salt_test_4_jin", "test_number": "4"},
}
MESHES = {
    "medium": {"processors": "processors64"},
    "fine": {"processors": "processors128"},
}
QOI_LABELS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]
REQUIRED_FIELDS = {
    "Q_wall_W": ["wallHeatFlux"],
    "mdot_exchange_positive_outward_proxy_kg_s": ["rho", "U"],
    "tau_recirc_proxy_s": ["rho", "U"],
    "wall_core_bulk_temperature_contrast_K": ["T", "rho"],
}


def rel(path: Path) -> str:
    if path.is_absolute() and not str(path).startswith(str(ROOT)):
        return str(path)
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric_name(path: Path) -> float | None:
    try:
        return float(path.name)
    except ValueError:
        return None


def format_time(value: float | None) -> str:
    if value is None:
        return ""
    if value.is_integer():
        return str(int(value))
    return f"{value:.12g}"


def source_root(case_id: str, mesh_level: str) -> Path:
    test_number = CASES[case_id]["test_number"]
    return (
        SOURCE_BASE
        / mesh_level
        / f"viscosity_screening_salt_test_{test_number}_jin_{mesh_level}_mesh"
    )


def processors_dir(case_id: str, mesh_level: str) -> Path:
    return source_root(case_id, mesh_level) / MESHES[mesh_level]["processors"]


def processor_times(case_id: str, mesh_level: str) -> list[float]:
    proc = processors_dir(case_id, mesh_level)
    if not proc.exists():
        return []
    times: list[float] = []
    for child in proc.iterdir():
        if not child.is_dir():
            continue
        value = numeric_name(child)
        if value is not None:
            times.append(value)
    return sorted(times)


def latest_nonzero_times(case_id: str, mesh_level: str, count: int = 3) -> list[float]:
    times = [time for time in processor_times(case_id, mesh_level) if time > 0]
    return times[-count:]


def fields_at_time(case_id: str, mesh_level: str, time_value: float) -> set[str]:
    path = processors_dir(case_id, mesh_level) / format_time(time_value)
    if not path.exists():
        return set()
    return {child.name for child in path.iterdir() if child.is_file()}


def contract_time_windows() -> dict[str, list[str]]:
    rows = read_csv(CONTRACT / "generation_contract.csv")
    window_text = rows[0]["required_time_windows_s"]
    windows: dict[str, list[str]] = {}
    for part in window_text.split(";"):
        case_id, values = part.strip().split(":", 1)
        windows[case_id.strip()] = [item.strip() for item in values.split(",")]
    return windows


def coverage_rows() -> list[dict[str, str]]:
    path = REFINEMENT / "endpoint_postprocessing_family_coverage.csv"
    return read_csv(path) if path.exists() else []


def coverage_by_case_mesh() -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in coverage_rows():
        key = (row["case_id"], row["mesh_level"])
        grouped.setdefault(key, []).append(row)
    return grouped


def postprocessing_family_summary(case_id: str, mesh_level: str) -> tuple[list[str], str]:
    post = source_root(case_id, mesh_level) / "postProcessing"
    if not post.exists():
        return [], ""
    families: list[str] = []
    latest_times: list[float] = []
    for family in sorted(child for child in post.iterdir() if child.is_dir()):
        families.append(family.name)
        family_times = [numeric_name(child) for child in family.iterdir() if child.is_dir()]
        latest_times.extend(time for time in family_times if time is not None)
    return families, format_time(max(latest_times) if latest_times else None)


def source_run_inventory_rows() -> list[dict[str, str]]:
    endpoint_coverage = coverage_by_case_mesh()
    rows: list[dict[str, str]] = []
    windows = contract_time_windows()
    for case_id in CASES:
        for mesh_level in MESHES:
            root = source_root(case_id, mesh_level)
            proc = processors_dir(case_id, mesh_level)
            times = processor_times(case_id, mesh_level)
            latest = latest_nonzero_times(case_id, mesh_level)
            latest_fields = fields_at_time(case_id, mesh_level, latest[-1]) if latest else set()
            families, post_latest = postprocessing_family_summary(case_id, mesh_level)
            source_case_id = CASES[case_id]["source_case_id"]
            cov = endpoint_coverage.get((source_case_id, mesh_level), [])
            required_windows = windows[case_id]
            required_dirs_present = [
                window for window in required_windows if (proc / window).exists()
            ]
            rows.append(
                {
                    "case_id": case_id,
                    "source_case_id": source_case_id,
                    "mesh_level": mesh_level,
                    "source_root": str(root),
                    "processors_dir": str(proc),
                    "source_root_exists": bool_text(root.exists()),
                    "processors_dir_exists": bool_text(proc.exists()),
                    "processor_time_count": str(len(times)),
                    "earliest_processor_time_s": format_time(times[0] if times else None),
                    "latest_processor_time_s": format_time(times[-1] if times else None),
                    "latest_three_nonzero_processor_times_s": ";".join(format_time(item) for item in latest),
                    "latest_time_fields_present": ";".join(sorted(latest_fields)),
                    "required_contract_windows_s": ";".join(required_windows),
                    "required_contract_window_dirs_present": ";".join(required_dirs_present),
                    "all_required_contract_windows_present": bool_text(
                        len(required_dirs_present) == len(required_windows)
                    ),
                    "postprocessing_dir_exists": bool_text((root / "postProcessing").exists()),
                    "postprocessing_families_present": ";".join(families),
                    "postprocessing_latest_time_s": post_latest,
                    "july9_endpoint_coverage_rows": str(len(cov)),
                    "registry_status": "external_readonly_not_registered_mainline",
                    "source_use_decision": (
                        "source_run_available_for_compute_node_terminal_sampling"
                        if root.exists() and proc.exists() and latest
                        else "source_run_missing_or_unreadable"
                    ),
                }
            )
    return rows


def existing_postprocessing_reuse_rows(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    reuse_specs = [
        (
            "wallHeatFlux",
            "Q_wall_W",
            "raw/support only",
            "Existing wallHeatFlux output can verify heat-flux field availability, but S13 still needs integration over the trusted wall mask with exact sign and area provenance.",
        ),
        (
            "mdot_pipeleg_*",
            "mdot_exchange_positive_outward_proxy_kg_s",
            "diagnostic only",
            "Pipeleg mass-flow surfaces are not the trusted recirculation exchange interface and cannot be relabeled as the S13 outward exchange flux.",
        ),
        (
            "velocity_profiles",
            "mdot_exchange_positive_outward_proxy_kg_s;tau_recirc_proxy_s",
            "raw/support only",
            "Velocity profiles help confirm field availability and flow character, but they are not a closed exchange-interface surface integral or CV inventory.",
        ),
        (
            "temperature_probes;wall_temperature_probes",
            "wall_core_bulk_temperature_contrast_K",
            "diagnostic only",
            "Probe means are not the same wall/core/bulk masks and weights used by the S13 temperature-contrast label.",
        ),
        (
            "July 9 endpoint GCI rows",
            "mesh/GCI support",
            "non-equivalent prior evidence",
            "Those rows use endpoint quantities such as wall gross/net duty, pipeleg mdot, and probe temperatures; they are useful precedent but not exact S13 labels.",
        ),
    ]
    by_mesh = {(row["case_id"], row["mesh_level"]): row for row in inventory}
    for case_id in CASES:
        for mesh_level in MESHES:
            inv = by_mesh[(case_id, mesh_level)]
            for family, qoi, use_status, reason in reuse_specs:
                rows.append(
                    {
                        "case_id": case_id,
                        "mesh_level": mesh_level,
                        "existing_evidence_family": family,
                        "related_s13_qoi_label": qoi,
                        "present_in_source_or_prior_package": bool_text(
                            family == "July 9 endpoint GCI rows"
                            and int(inv["july9_endpoint_coverage_rows"]) > 0
                            or family != "July 9 endpoint GCI rows"
                            and any(part.replace("*", "") in inv["postprocessing_families_present"] for part in family.split(";"))
                        ),
                        "reuse_status": use_status,
                        "production_row_allowed": "false",
                        "reason_not_directly_admissible": reason,
                    }
                )
    return rows


def sampling_need_rows(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    windows = contract_time_windows()
    inv_by_key = {(row["case_id"], row["mesh_level"]): row for row in inventory}
    contracts = {row["qoi_label"]: row for row in read_csv(CONTRACT / "generation_contract.csv")}
    for case_id in CASES:
        for mesh_level in MESHES:
            inv = inv_by_key[(case_id, mesh_level)]
            latest_times = [item for item in inv["latest_three_nonzero_processor_times_s"].split(";") if item]
            latest_fields = set(filter(None, inv["latest_time_fields_present"].split(";")))
            exact_windows_present = inv["all_required_contract_windows_present"] == "true"
            source_available = inv["source_use_decision"].startswith("source_run_available")
            for qoi_label in QOI_LABELS:
                needed_fields = REQUIRED_FIELDS[qoi_label]
                fields_ready = all(field in latest_fields for field in needed_fields)
                status = "blocked_missing_source_run"
                if source_available and exact_windows_present:
                    status = "ready_for_exact_contract_window_sampling"
                elif source_available and latest_times and fields_ready:
                    status = "ready_for_terminal_window_sampling_needs_mesh_time_equivalence_gate"
                elif source_available:
                    status = "source_run_present_missing_latest_required_fields"
                rows.append(
                    {
                        "case_id": case_id,
                        "mesh_level": mesh_level,
                        "qoi_label": qoi_label,
                        "exact_contract_windows_s": ";".join(windows[case_id]),
                        "exact_contract_windows_present": bool_text(exact_windows_present),
                        "terminal_candidate_windows_s": ";".join(latest_times),
                        "required_fields": ";".join(needed_fields),
                        "latest_required_fields_present": bool_text(fields_ready),
                        "geometry_mask_required": contracts[qoi_label]["geometry_inputs_required"],
                        "formula_sign_basis_required": contracts[qoi_label]["formula_sign_basis_required"],
                        "source_run_available": bool_text(source_available),
                        "existing_exact_s13_row_present": "false",
                        "sampling_status": status,
                        "production_use_allowed_now": "false",
                        "mesh_gci_use_allowed_now": "false",
                    }
                )
    return rows


def command_contract_rows(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    windows = contract_time_windows()
    inv_by_key = {(row["case_id"], row["mesh_level"]): row for row in inventory}
    for case_id in CASES:
        for mesh_level in MESHES:
            inv = inv_by_key[(case_id, mesh_level)]
            terminal = inv["latest_three_nonzero_processor_times_s"]
            rows.append(
                {
                    "case_id": case_id,
                    "mesh_level": mesh_level,
                    "source_root": inv["source_root"],
                    "processors_dir": inv["processors_dir"],
                    "strict_contract_windows_s": ";".join(windows[case_id]),
                    "strict_contract_windows_available": inv["all_required_contract_windows_present"],
                    "fallback_terminal_candidate_windows_s": terminal,
                    "field_inputs": "U;T;rho;wallHeatFlux",
                    "geometry_inputs": "mesh-level trusted wall mask; mesh-level exchange interface; normals; CV cell volume/mass inventory",
                    "outputs_to_generate": "four exact S13 labels for this case/mesh/window family",
                    "recommended_next_task": "compute-node S13 medium/fine exact-label sampler over mesh-level S13 masks",
                    "run_allowed_from_this_task": "false",
                    "reason": "This row is inventory/contract only; compute sampling needs a scheduler-authorized row.",
                }
            )
    return rows


def mesh_gci_readiness_rows(need_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for qoi_label in QOI_LABELS:
        qoi_rows = [row for row in need_rows if row["qoi_label"] == qoi_label]
        terminal_ready = sum(
            row["sampling_status"] == "ready_for_terminal_window_sampling_needs_mesh_time_equivalence_gate"
            for row in qoi_rows
        )
        exact_ready = sum(row["sampling_status"] == "ready_for_exact_contract_window_sampling" for row in qoi_rows)
        rows.append(
            {
                "qoi_label": qoi_label,
                "medium_fine_needed_rows": str(len(qoi_rows)),
                "existing_exact_s13_medium_fine_rows": "0",
                "exact_contract_window_sampling_ready_rows": str(exact_ready),
                "terminal_window_sampling_ready_rows": str(terminal_ready),
                "mesh_gci_ready_now": "false",
                "decision": (
                    "source_runs_available_sampling_required_before_mesh_gci"
                    if terminal_ready or exact_ready
                    else "source_or_field_gap_blocks_sampling"
                ),
                "next_gate": "execute_sampling_then_test_mesh_family_monotonicity_or_publish_mesh_spread",
            }
        )
    return rows


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "path": rel(MESH_GENERATION / "same_label_mesh_family_generated_rows.csv"),
            "use": "current-coarse exact S13 rows and prior fail-closed medium/fine gap",
            "mutation": "read-only",
        },
        {
            "path": rel(CONTRACT / "generation_contract.csv"),
            "use": "exact labels, sign convention, masks, required fields, and forbidden shortcuts",
            "mutation": "read-only",
        },
        {
            "path": rel(TEMPORAL_UQ / "same_qoi_temporal_uq_case_rows.csv"),
            "use": "target-minus/target/target-plus temporal UQ already completed for current coarse",
            "mutation": "read-only",
        },
        {
            "path": rel(REFINEMENT / "endpoint_postprocessing_family_coverage.csv"),
            "use": "prior endpoint postProcessing/GCI coverage for medium/fine where present",
            "mutation": "read-only",
        },
        {
            "path": str(SOURCE_BASE / "medium"),
            "use": "read-only medium mesh native source run inventory",
            "mutation": "read-only external source",
        },
        {
            "path": str(SOURCE_BASE / "fine"),
            "use": "read-only fine mesh native source run inventory",
            "mutation": "read-only external source",
        },
    ]


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(MESH_GENERATION / "same_label_mesh_family_generated_rows.csv")}
  - {rel(CONTRACT / "generation_contract.csv")}
  - {rel(TEMPORAL_UQ / "same_qoi_temporal_uq_case_rows.csv")}
  - {rel(REFINEMENT / "endpoint_postprocessing_family_coverage.csv")}
  - {SOURCE_BASE / "medium"}
  - {SOURCE_BASE / "fine"}
tags: [s13, upcomer-exchange, medium-fine, mesh-gci, same-label]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-upcomer-exchange-medium-fine-same-label-sampling.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# S13 Medium/Fine Same-Label Sampling Preflight

Decision: `{summary["decision"]}`.

The medium and fine Salt2/Salt3/Salt4 source runs are present and readable.
The missing item is narrower: exact S13 medium/fine rows have not yet been
sampled for the four labels, masks, formula/sign basis, and window policy used
by the current-coarse S13 evidence.

- Medium/fine source run rows inventoried: `{summary["source_run_inventory_rows"]}`
- Existing source runs available: `{summary["source_runs_available"]}`
- Medium/fine exact S13 sampling need rows: `{summary["sampling_need_rows"]}`
- Need rows with terminal primitive fields ready: `{summary["terminal_sampling_ready_rows"]}`
- Need rows with strict coarse-contract windows already present: `{summary["exact_contract_window_ready_rows"]}`
- Existing exact S13 medium/fine rows: `{summary["existing_exact_s13_medium_fine_rows"]}`
- Mesh/GCI ready now: `{str(summary["mesh_gci_ready_now"]).lower()}`
- Scheduler/sampler launched: `{str(summary["scheduler_or_sampler_launched"]).lower()}`

How to use the postprocessing already done:

1. Treat it as source/provenance and sanity-check evidence for available fields,
   stationarity, and endpoint behavior.
2. Do not relabel pipeleg mdot, velocity profiles, probe means, wall gross/net
   duty, or July 9 endpoint GCI rows as S13 exchange rows.
3. Use the medium/fine native fields at the listed terminal candidate windows
   to run the exact S13 sampler over mesh-level trusted wall, exchange
   interface, recirculation CV, and wall/core/bulk masks.

The next row should run compute-node sampling from `sampling_command_contract.csv`.
If exact target-window directories remain absent for medium/fine, that row must
either prove a terminal-window mesh-time equivalence gate or publish a
fail-closed mesh/GCI result with only temporal UQ accepted.
"""


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    inventory = source_run_inventory_rows()
    reuse = existing_postprocessing_reuse_rows(inventory)
    needs = sampling_need_rows(inventory)
    commands = command_contract_rows(inventory)
    mesh_gate = mesh_gci_readiness_rows(needs)
    manifest = source_manifest_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "medium_fine_runs_exist_exact_s13_rows_absent_sampling_contract_ready",
        "source_run_inventory_rows": len(inventory),
        "source_runs_available": sum(row["source_use_decision"].startswith("source_run_available") for row in inventory),
        "sampling_need_rows": len(needs),
        "terminal_sampling_ready_rows": sum(
            row["sampling_status"] == "ready_for_terminal_window_sampling_needs_mesh_time_equivalence_gate"
            for row in needs
        ),
        "exact_contract_window_ready_rows": sum(
            row["sampling_status"] == "ready_for_exact_contract_window_sampling" for row in needs
        ),
        "existing_exact_s13_medium_fine_rows": 0,
        "mesh_gci_ready_now": False,
        "scheduler_or_sampler_launched": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
    }
    csv_dump(out / "medium_fine_source_run_inventory.csv", list(inventory[0]), inventory)
    csv_dump(out / "existing_postprocessing_reuse_matrix.csv", list(reuse[0]), reuse)
    csv_dump(out / "s13_exact_label_sampling_need_matrix.csv", list(needs[0]), needs)
    csv_dump(out / "sampling_command_contract.csv", list(commands[0]), commands)
    csv_dump(out / "mesh_gci_readiness_after_medium_fine_inventory.csv", list(mesh_gate[0]), mesh_gate)
    csv_dump(out / "source_manifest.csv", list(manifest[0]), manifest)
    json_dump(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
