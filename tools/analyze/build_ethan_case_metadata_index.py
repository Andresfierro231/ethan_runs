#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    base_case_id,
    case_variant_label,
    csv_dump,
    ensure_dir,
    get_registry_row,
    iso_timestamp,
    json_dump,
    load_case_metadata,
    parse_log_summary,
    path_lookup,
    relative_to_workspace,
)


DEFAULT_SOURCE_IDS = [
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
]

DEFAULT_CONTRACT = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools"
    / "cross_model_comparison"
    / "campaigns"
    / "2026-06-02_ethan_modern_runs_first_batch_v1"
    / "data"
    / "cross_model_case_contract.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normalized Ethan case metadata index.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Registered source identifier. Repeat to override the default list.",
    )
    parser.add_argument(
        "--contract-csv",
        default=str(DEFAULT_CONTRACT),
        help="Optional published contract CSV used to enrich insulation/reference metadata.",
    )
    return parser.parse_args()


def load_contract_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {row["ethan_source_id"]: row for row in reader if row.get("ethan_source_id")}


def maybe_log_summary(source_root: Path) -> dict[str, object]:
    log_path = source_root / "logs" / "log.foamRun"
    if not log_path.exists():
        return {}
    return parse_log_summary(log_path)


def maybe_qoi_summary(source_id: str) -> dict[str, object]:
    qoi_path = WORKSPACE_ROOT / "work_products" / source_id / "qoi_summary.json"
    if not qoi_path.exists():
        return {}
    with qoi_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def geometry_inventory(source_root: Path) -> tuple[str, int, list[str]]:
    geometry_dir = source_root / "constant" / "geometry"
    if not geometry_dir.exists():
        return "", 0, []
    stls = sorted(path.name for path in geometry_dir.glob("*.stl"))
    return relative_to_workspace(geometry_dir), len(stls), stls[:8]


def build_row(source_id: str, contract_rows: dict[str, dict[str, str]]) -> dict[str, object]:
    registry_path = WORKSPACE_ROOT / "registry" / "case_registry.csv"
    registry_row = get_registry_row(registry_path, source_id)
    source_root = Path(registry_row["source_root"]).resolve()
    metadata = load_case_metadata(source_root)
    qoi = maybe_qoi_summary(source_id)
    log_summary = {} if qoi else maybe_log_summary(source_root)
    contract = contract_rows.get(source_id, {})
    geometry_rel, geometry_stl_count, geometry_examples = geometry_inventory(source_root)

    fluid = path_lookup(metadata, "fluid", "")
    turbulence_model = path_lookup(metadata, "turbulence_model", "")
    case_id = registry_row["case_id"]

    row: dict[str, object] = {
        "source_id": source_id,
        "case_id": case_id,
        "base_case_id": base_case_id(case_id),
        "variant_label": case_variant_label(case_id),
        "source_owner": registry_row["source_owner"],
        "source_root": str(source_root),
        "fluid": fluid,
        "turbulence_model": turbulence_model,
        "heater_power_W": path_lookup(metadata, "operating_point.heater_power_W", ""),
        "cooling_power_W": path_lookup(metadata, "operating_point.cooling_power_W", ""),
        "T_init_K": path_lookup(metadata, "operating_point.T_init_K", ""),
        "nprocs": path_lookup(metadata, "nprocs", ""),
        "scale_to_meters": path_lookup(metadata, "scale_to_meters", ""),
        "mesh_group_id": path_lookup(metadata, "mesh_group_id", ""),
        "ncc_couples": path_lookup(metadata, "ncc_couples", ""),
        "geometry_dir": geometry_rel,
        "geometry_stl_count": geometry_stl_count,
        "geometry_stl_examples": ";".join(geometry_examples),
        "heater_h_W_m2K": path_lookup(metadata, "bc_params.heater.h", ""),
        "heater_Ta_K": path_lookup(metadata, "bc_params.heater.Ta", ""),
        "heater_emissivity": path_lookup(metadata, "bc_params.heater.emissivity", ""),
        "cooler_h_W_m2K": path_lookup(metadata, "bc_params.cooler.h", ""),
        "cooler_Ta_K": path_lookup(metadata, "bc_params.cooler.Ta", ""),
        "test_section_h_W_m2K": path_lookup(metadata, "bc_params.test_section.h", ""),
        "test_section_Ta_K": path_lookup(metadata, "bc_params.test_section.Ta", ""),
        "insulated_h_W_m2K": path_lookup(metadata, "bc_params.insulated.h", ""),
        "insulated_Ta_K": path_lookup(metadata, "bc_params.insulated.Ta", ""),
        "mesh_kernel_factor": path_lookup(metadata, "mesh_settings.kernel_factor", ""),
        "mesh_kernel_blend": path_lookup(metadata, "mesh_settings.kernel_blend", ""),
        "mesh_core_ratio": path_lookup(metadata, "mesh_settings.core_ratio", ""),
        "inflation_first_cell_size": path_lookup(metadata, "mesh_settings.inflation.first_cell_size", ""),
        "inflation_bulk_cell_size": path_lookup(metadata, "mesh_settings.inflation.bulk_cell_size", ""),
        "inflation_c2c_expansion": path_lookup(metadata, "mesh_settings.inflation.c2c_expansion", ""),
        "convergence_enabled": path_lookup(metadata, "convergence.enabled", ""),
        "convergence_check_interval": path_lookup(metadata, "convergence.check_interval", ""),
        "convergence_min_iterations": path_lookup(metadata, "convergence.min_iterations", ""),
        "convergence_qoi_rtol": path_lookup(metadata, "convergence.qoi.rtol", ""),
        "convergence_qoi_window": path_lookup(metadata, "convergence.qoi.window", ""),
        "mu_spec_type": path_lookup(metadata, "fluid_properties.mu_spec.type", ""),
        "kappa_spec_type": path_lookup(metadata, "fluid_properties.kappa_spec.type", ""),
        "cp_coeff_count": len(path_lookup(metadata, "fluid_properties.Cp_coeffs", []) or []),
        "rho_coeff_count": len(path_lookup(metadata, "fluid_properties.rho_coeffs", []) or []),
        "walltime": path_lookup(metadata, "walltime", ""),
        "run_status": qoi.get("run_status", log_summary.get("status", "")),
        "run_termination_reason": qoi.get("run_termination_reason", log_summary.get("termination_reason", "")),
        "final_time": qoi.get("final_time", ""),
        "convergence_reached": qoi.get("convergence_reached", ""),
        "convergence_dTsigma": qoi.get("convergence_dTsigma", ""),
        "mdot_mean_abs_kg_s": qoi.get("mdot_mean_abs_kg_s", ""),
        "final_total_wall_heat_abs_w": qoi.get("final_total_wall_heat_abs_w", ""),
        "probe_T_avg_K": qoi.get("probe_T_avg_K", ""),
        "two_d_ins_s1_thickness_in": contract.get("two_d_ins_s1_thickness_in", ""),
        "two_d_ins_s2_thickness_in": contract.get("two_d_ins_s2_thickness_in", ""),
        "two_d_radiation_on": contract.get("two_d_radiation_on", ""),
        "one_d_stage1_scenario": contract.get("one_d_stage1_scenario", ""),
        "one_d_stage2_scenario": contract.get("one_d_stage2_scenario", ""),
        "comparison_ready": contract.get("comparison_ready", ""),
        "disposition_note": contract.get("disposition_note", ""),
    }

    row["assumption_note"] = (
        f"{fluid} / {turbulence_model} case on mesh group "
        f"{row['mesh_group_id']} with heater {row['heater_power_W']} W and cooler {row['cooling_power_W']} W."
    )
    return row


def write_summary(output_dir: Path, rows: list[dict[str, object]], contract_path: Path) -> None:
    converged = sum(1 for row in rows if row.get("convergence_reached") is True)
    geometry_cases = sum(1 for row in rows if row.get("geometry_stl_count"))
    source_ids = [str(row["source_id"]) for row in rows]

    lines = [
        "# Ethan Case Metadata Index",
        "",
        "- Generated for the active salt2 continuation case plus the first staged modern-runs batch.",
        f"- Source count: `{len(rows)}`",
        f"- Cases with recorded geometry STL inventory: `{geometry_cases}`",
        f"- Cases already marked converged in local QoI summaries: `{converged}`",
        "",
        "## Notes",
        "",
        "- `two_d_ins_s1_thickness_in`, `two_d_ins_s2_thickness_in`, and related 1D/2D fields come from the current published comparison-contract CSV when available.",
        "- Water laminar rows currently have direct-intake metadata but no canonical insulation/reference join in the published contract.",
        "- This index is intended as the durable assumptions/geometry handoff for later 1D, 2D, closure-term, and visualization work.",
        "",
        "## Inputs",
        "",
        f"- Contract enrichment CSV: `{contract_path}`" if contract_path.exists() else "- Contract enrichment CSV: unavailable",
        f"- Source IDs: `{', '.join(source_ids)}`",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or DEFAULT_SOURCE_IDS
    contract_path = Path(args.contract_csv).resolve()
    contract_rows = load_contract_rows(contract_path)

    rows = [build_row(source_id, contract_rows) for source_id in source_ids]
    fieldnames = list(rows[0].keys()) if rows else []

    output_dir = WORKSPACE_ROOT / "reports" / "2026-06-02_ethan_case_metadata_index"
    csv_dump(output_dir / "ethan_case_metadata_index.csv", fieldnames, rows)
    json_dump(
        output_dir / "ethan_case_metadata_index.json",
        {
            "generated_at": iso_timestamp(),
            "source_ids": source_ids,
            "rows": rows,
        },
    )
    write_summary(output_dir, rows, contract_path)
    print(json.dumps({"output_dir": str(output_dir), "row_count": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
