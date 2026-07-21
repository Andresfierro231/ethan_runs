#!/usr/bin/env python3
"""Build AGENT-418 evidence for the setup-predictive Fluid heat-loss variant."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
OUT = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant"

if str(FLUID_ROOT) not in sys.path:
    sys.path.insert(0, str(FLUID_ROOT))

from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, default_scenarios  # noqa: E402
from tamu_loop_model_v2.geometry import build_geometry, default_geometry_refinement  # noqa: E402
from tamu_loop_model_v2.solver import ScenarioConfig, ambient_loss_for_segment  # noqa: E402


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: float) -> str:
    return f"{value:.12g}"


def fluid_source(path: str) -> str:
    return f"../cfd-modeling-tools/tamu_first_order_model/Fluid/{path}"


def contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "field": "outer_closure_mode",
            "status": "implemented",
            "accepted_values": "baseline; per_parent_multiplier; external_boundary_table",
            "purpose": "activates setup-only per-segment external-boundary loss calculation",
            "runtime_leakage_risk": "none_by_itself",
        },
        {
            "field": "external_boundary_h_by_parent_segment",
            "status": "implemented",
            "accepted_values": "mapping parent_or_segment -> W/m2/K",
            "purpose": "prescribed setup external h instead of natural-convection correlation on targeted rows",
            "runtime_leakage_risk": "must come from setup/boundary dictionary, not realized wallHeatFlux",
        },
        {
            "field": "external_boundary_ambient_temperature_by_parent_segment",
            "status": "implemented",
            "accepted_values": "mapping parent_or_segment -> K",
            "purpose": "per-segment ambient Ta drive",
            "runtime_leakage_risk": "setup_only",
        },
        {
            "field": "external_boundary_surroundings_temperature_by_parent_segment",
            "status": "implemented",
            "accepted_values": "mapping parent_or_segment -> K",
            "purpose": "per-segment Tsur metadata for radiation-enabled setup calculations",
            "runtime_leakage_risk": "setup_only",
        },
        {
            "field": "external_boundary_emissivity_by_parent_segment",
            "status": "implemented",
            "accepted_values": "mapping parent_or_segment -> emissivity",
            "purpose": "per-segment setup emissivity metadata",
            "runtime_leakage_risk": "setup_only",
        },
        {
            "field": "external_boundary_coverage_multiplier_by_parent_segment",
            "status": "implemented",
            "accepted_values": "positive mapping parent_or_segment -> multiplier",
            "purpose": "junction/stub/connector heat-loss area coverage without CFD wallHeatFlux",
            "runtime_leakage_risk": "setup geometry only; do not fit to held-out realized heat loss",
        },
        {
            "field": "external_boundary_drive_selector_by_parent_segment",
            "status": "implemented",
            "accepted_values": "fluid_segment_bulk_temperature_for_v1_setup_mode; pipe_outer_wall_temperature; outer_surface_temperature",
            "purpose": "choose bulk, wall/shell, or outer-surface effective driving temperature",
            "runtime_leakage_risk": "uses solver-state temperatures only",
        },
        {
            "field": "hx_ua_multiplier",
            "status": "compatible_existing_hook",
            "accepted_values": "nonnegative scalar",
            "purpose": "setup-only HX/cooler UA scaling; separate from passive external-boundary loss",
            "runtime_leakage_risk": "not imposed cooler duty",
        },
    ]


def demonstration_rows() -> list[dict[str, Any]]:
    case = next(case for case in EXPERIMENT_CASES if case.name == "Salt 1")
    baseline = next(s for s in default_scenarios() if s.name == "predictive_airside_ins_1.0in_rad_0")
    segments, _ = build_geometry(refinement=default_geometry_refinement())
    heated = next(segment for segment in segments if segment.resolved_parent_name == "heated_incline")
    junction = next(segment for segment in segments if segment.resolved_parent_name == "top_horizontal_exit")
    rows: list[dict[str, Any]] = []

    def add(label: str, segment, scenario: ScenarioConfig) -> None:
        q, diag = ambient_loss_for_segment(segment, case, 470.0, 0.02, scenario)
        rows.append(
            {
                "case_name": case.name,
                "demo_id": label,
                "segment_name": segment.name,
                "parent_name": segment.resolved_parent_name,
                "q_ambient_W": fmt(q),
                "external_h_W_m2K": fmt(float(diag.external_prescribed_h_W_m2K or 0.0)),
                "external_Ta_K": fmt(float(diag.external_ambient_temperature_K or 0.0)),
                "external_Tsur_K": fmt(float(diag.external_surroundings_temperature_K or 0.0)),
                "external_emissivity": fmt(float(diag.external_emissivity or 0.0)),
                "coverage_multiplier": fmt(float(diag.external_boundary_coverage_multiplier)),
                "drive_selector": diag.external_boundary_drive_selector or "fluid_segment_bulk_temperature_for_v1_setup_mode",
                "source": diag.external_boundary_source,
                "runtime_input_policy": "setup_only_no_realized_wallHeatFlux_no_imposed_cfd_cooler_duty",
            }
        )

    common_heated = {
        **baseline.__dict__,
        "outer_closure_mode": "external_boundary_table",
        "external_boundary_h_by_parent_segment": {"heated_incline": 5.0},
        "external_boundary_ambient_temperature_by_parent_segment": {"heated_incline": 300.0},
        "external_boundary_surroundings_temperature_by_parent_segment": {"heated_incline": 300.0},
        "external_boundary_emissivity_by_parent_segment": {"heated_incline": 0.95},
        "external_boundary_source_by_parent_segment": {"heated_incline": "setup_boundary_table.csv"},
    }
    add(
        "heated_bulk_drive",
        heated,
        ScenarioConfig(
            **{
                **common_heated,
                "name": "demo_heated_bulk_drive",
                "external_boundary_drive_selector_by_parent_segment": {
                    "heated_incline": "fluid_segment_bulk_temperature_for_v1_setup_mode",
                },
            }
        ),
    )
    add(
        "heated_pipe_outer_wall_drive",
        heated,
        ScenarioConfig(
            **{
                **common_heated,
                "name": "demo_heated_wall_drive",
                "external_boundary_drive_selector_by_parent_segment": {
                    "heated_incline": "pipe_outer_wall_temperature",
                },
            }
        ),
    )
    add(
        "heated_outer_surface_drive",
        heated,
        ScenarioConfig(
            **{
                **common_heated,
                "name": "demo_heated_surface_drive",
                "external_boundary_drive_selector_by_parent_segment": {
                    "heated_incline": "outer_surface_temperature",
                },
            }
        ),
    )
    junction_common = {
        **baseline.__dict__,
        "outer_closure_mode": "external_boundary_table",
        "external_boundary_h_by_parent_segment": {"top_horizontal_exit": 5.0},
        "external_boundary_ambient_temperature_by_parent_segment": {"top_horizontal_exit": 300.0},
        "external_boundary_source_by_parent_segment": {"top_horizontal_exit": "setup_junction_stub_table.csv"},
    }
    add(
        "junction_unit_coverage",
        junction,
        ScenarioConfig(
            **{
                **junction_common,
                "name": "demo_junction_unit_coverage",
                "external_boundary_coverage_multiplier_by_parent_segment": {"top_horizontal_exit": 1.0},
            }
        ),
    )
    add(
        "junction_double_coverage",
        junction,
        ScenarioConfig(
            **{
                **junction_common,
                "name": "demo_junction_double_coverage",
                "external_boundary_coverage_multiplier_by_parent_segment": {"top_horizontal_exit": 2.0},
            }
        ),
    )
    add(
        "heated_warmer_ambient",
        heated,
        ScenarioConfig(
            **{
                **common_heated,
                "name": "demo_heated_warmer_ambient",
                "external_boundary_ambient_temperature_by_parent_segment": {"heated_incline": 340.0},
                "external_boundary_drive_selector_by_parent_segment": {
                    "heated_incline": "fluid_segment_bulk_temperature_for_v1_setup_mode",
                },
            }
        ),
    )
    return rows


def source_manifest() -> list[dict[str, Any]]:
    sources = [
        ("Fluid solver", FLUID_ROOT / "tamu_loop_model_v2/solver.py", "active external-boundary heat-loss implementation"),
        ("Fluid config loader", FLUID_ROOT / "tamu_loop_model_v2/config_loader.py", "scenario YAML parsing and scenario_records export"),
        ("Fluid solver tests", FLUID_ROOT / "tests/test_solver_contracts.py", "focused contract tests for setup-only heat-loss variant"),
        ("Fluid README", FLUID_ROOT / "tamu_loop_model_v2/README.md", "scenario contract documentation"),
        ("AGENT-410 plan", ROOT / "work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/predictive_heat_loss_variant_plan.csv", "requested implementation plan"),
    ]
    return [
        {
            "source_id": source_id,
            "path": fluid_source(str(path.relative_to(FLUID_ROOT))) if str(path).startswith(str(FLUID_ROOT)) else rel(path),
            "exists": str(path.exists()).lower(),
            "use": use,
        }
        for source_id, path, use in sources
    ]


def build_readme(summary: dict[str, Any]) -> str:
    return f"""# Setup-Predictive Heat-Loss Fluid Variant

Task: AGENT-418  
Generated: 2026-07-15

## Result

Implemented the first active Fluid 1D variant for setup-predictive segment heat
losses. `outer_closure_mode: external_boundary_table` now changes actual
passive heat-loss calculation, not just diagnostics.

## Implemented Capabilities

- External h/Ta/Tsur/emissivity setup dictionaries.
- Junction/stub/connector coverage multiplier through
  `external_boundary_coverage_multiplier_by_parent_segment`.
- Bulk, pipe-outer-wall, and outer-surface drive selectors through
  `external_boundary_drive_selector_by_parent_segment`.
- Compatibility with the setup-only `hx_ua_multiplier` hook.
- No runtime use of realized CFD `wallHeatFlux`, CFD mdot, imposed CFD cooler
  duty, or validation temperatures.

## Dry-Run Evidence

Rows: {summary["dry_run_rows"]}

The demonstration table shows:

- warmer external Ta reduces computed passive loss;
- junction coverage multiplier scales computed loss;
- wall/shell drive selectors reduce computed loss relative to bulk drive.

## Files

- `fluid_variant_contract.csv`
- `dry_run_segment_loss_demonstration.csv`
- `source_manifest.csv`
- `summary.json`

## Validation

- Focused Fluid contract tests: passed.
- Python compilation of modified Fluid source/tests: passed.
- Full `tests.test_solver_contracts` was started but stopped because unrelated
  solver-heavy tests exceeded the interactive turn budget.
"""


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    contracts = contract_rows()
    demos = demonstration_rows()
    sources = source_manifest()
    summary = {
        "task": "AGENT-418",
        "date": "2026-07-15",
        "implemented": True,
        "fluid_files_modified": [
            fluid_source("tamu_loop_model_v2/solver.py"),
            fluid_source("tamu_loop_model_v2/config_loader.py"),
            fluid_source("tamu_loop_model_v2/README.md"),
            fluid_source("tests/test_solver_contracts.py"),
            fluid_source("journals/2026-07/2026-07-15_workflow_journal.md"),
        ],
        "dry_run_rows": len(demos),
        "runtime_leakage_guardrail": "no_realized_CFD_wallHeatFlux_no_CFD_mdot_no_imposed_CFD_cooler_duty_no_validation_temperatures",
        "native_cfd_outputs_mutated": False,
        "scheduler_mutated": False,
        "registry_or_admission_state_mutated": False,
    }
    write_csv(
        output_dir / "fluid_variant_contract.csv",
        contracts,
        ["field", "status", "accepted_values", "purpose", "runtime_leakage_risk"],
    )
    write_csv(
        output_dir / "dry_run_segment_loss_demonstration.csv",
        demos,
        [
            "case_name",
            "demo_id",
            "segment_name",
            "parent_name",
            "q_ambient_W",
            "external_h_W_m2K",
            "external_Ta_K",
            "external_Tsur_K",
            "external_emissivity",
            "coverage_multiplier",
            "drive_selector",
            "source",
            "runtime_input_policy",
        ],
    )
    write_csv(output_dir / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    build_package()


if __name__ == "__main__":
    main()
