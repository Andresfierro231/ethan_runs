#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, finite_float, load_csv_rows, write_json
from tools.analyze.build_ethan_frozen_state_results_package import best_one_d_rows

REPORT_DAY_DIR = ROOT / "reports" / "2026-06" / "2026-06-22"
FROZEN_DIR = REPORT_DAY_DIR / "2026-06-22_ethan_frozen_state_results"
DEFAULT_OUTPUT_DIR = REPORT_DAY_DIR / "2026-06-22_ethan_fluid_replay_against_frozen_state"
FLUID_ROOT = ROOT.parent / "cfd-modeling-tools" / "tamu_first_order_model" / "Fluid"
FLUID_VALIDATION_ROOTS = {
    "ethan_cfd_informed_salt_v1": FLUID_ROOT / "validation_data" / "ethan_cfd_informed_salt_v1",
    "ethan_cfd_informed_salt_v2": FLUID_ROOT / "validation_data" / "ethan_cfd_informed_salt_v2",
}
FLUID_TRACKED_MODE = "ethan_cfd_informed_salt_v2"
FLUID_RESULTS_ROOT_BY_MODE = {
    "ethan_cfd_informed_salt_v1": FLUID_ROOT / "results" / "diagnostics" / "ethan_cfd_informed_salt_v1",
    "ethan_cfd_informed_salt_v2": FLUID_ROOT / "results" / "diagnostics" / "ethan_cfd_informed_salt_v2",
}
FLUID_V2_BUNDLE_PRODUCER_PATH = FLUID_ROOT / "tools" / "build_ethan_cfd_informed_salt_v2_bundle.py"
FLUID_REFERENCE_PATHS = (
    FLUID_ROOT / "tamu_loop_model_v2" / "ethan_cfd_informed_salt.py",
    FLUID_ROOT / "tamu_loop_model_v2" / "profile_descriptor_closure.py",
    FLUID_ROOT / "tamu_loop_model_v2" / "solver.py",
    FLUID_ROOT / "configs" / "campaigns.yaml",
    FLUID_ROOT / "configs" / "scenarios.yaml",
    FLUID_ROOT / "tests" / "test_ethan_cfd_informed_salt.py",
    FLUID_V2_BUNDLE_PRODUCER_PATH,
)
FLUID_MODE_TOKENS = ("ethan_cfd_informed_salt_v1", "ethan_cfd_informed_salt_v2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a report package that compares the current readable Fluid "
            "Salt replay against the June 22 frozen-state CFD contract."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def scenario_family(scenario: str) -> str:
    if "_hybrid_" in scenario:
        return "hybrid"
    if "_baseline_" in scenario:
        return "baseline"
    return "other"


def scenario_condition(scenario: str) -> str:
    parts = scenario.split("_")
    if len(parts) < 2:
        return scenario
    try:
        ins_index = parts.index("ins")
    except ValueError:
        return scenario
    if ins_index + 3 >= len(parts):
        return scenario
    return f"ins_{parts[ins_index + 1]}_rad_{parts[ins_index + 3]}"


def scenario_rollup_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["scenario"]].append(row)
    out: list[dict[str, Any]] = []
    for scenario, group in sorted(grouped.items()):
        temp_abs = [abs(finite_float(row.get("air_outlet_temperature_error_k"))) for row in group]
        flow_abs = [abs(finite_float(row.get("mass_flow_relative_error_pct"))) for row in group]
        valid_count = sum(
            1
            for row in group
            if str(row.get("accepted_for_validation", "")).lower() == "true"
            and row.get("validity_status") == "valid"
        )
        out.append(
            {
                "scenario": scenario,
                "scenario_family": scenario_family(scenario),
                "condition_label": scenario_condition(scenario),
                "case_count": len(group),
                "valid_case_count": valid_count,
                "mean_abs_air_outlet_temperature_error_k": sum(temp_abs) / len(temp_abs) if temp_abs else None,
                "max_abs_air_outlet_temperature_error_k": max(temp_abs) if temp_abs else None,
                "mean_abs_mass_flow_relative_error_pct": sum(flow_abs) / len(flow_abs) if flow_abs else None,
                "max_abs_mass_flow_relative_error_pct": max(flow_abs) if flow_abs else None,
                "descriptor_modes": "|".join(sorted({row.get("profile_descriptor_mode", "") for row in group})),
                "internal_htc_modes": "|".join(sorted({row.get("internal_htc_mode", "") for row in group})),
            }
        )
    return out


def hybrid_coverage_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in rows:
        grouped[scenario_condition(row["scenario"])][scenario_family(row["scenario"])].add(row["case_label"])
    out: list[dict[str, Any]] = []
    for condition, family_map in sorted(grouped.items()):
        baseline_cases = sorted(family_map.get("baseline", set()))
        hybrid_cases = sorted(family_map.get("hybrid", set()))
        missing_hybrid = sorted(set(baseline_cases) - set(hybrid_cases))
        out.append(
            {
                "condition_label": condition,
                "baseline_case_count": len(baseline_cases),
                "hybrid_case_count": len(hybrid_cases),
                "baseline_cases": "|".join(baseline_cases),
                "hybrid_cases": "|".join(hybrid_cases),
                "missing_hybrid_cases": "|".join(missing_hybrid),
                "coverage_status": "partial" if missing_hybrid else "matched",
            }
        )
    return out


def branch_boundary_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "branch_name": row["branch_name"],
                "branch_alias": row["branch_alias"],
                "dominant_fit_status": row["dominant_fit_status"],
                "domain_note": row["domain_note"],
                "modeling_note": row["modeling_note"],
            }
        )
    return out


def data_need_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "blocked_closure": row["blocked_closure"],
            "missing_observable": row["missing_observable"],
            "preferred_extractor_or_package": row["preferred_extractor_or_package"],
            "would_unlock": row["would_unlock"],
        }
        for row in rows
    ]


def count_text_occurrences(text: str, needle: str) -> int:
    if not needle:
        return 0
    return text.count(needle)


def tracked_bundle_root() -> Path:
    tracked_root = FLUID_VALIDATION_ROOTS[FLUID_TRACKED_MODE]
    if tracked_root.exists():
        return tracked_root
    return FLUID_VALIDATION_ROOTS["ethan_cfd_informed_salt_v1"]


def load_external_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_external_snapshot() -> dict[str, Any]:
    return load_external_json(tracked_bundle_root() / "closure_snapshot.json")


def load_external_manifest() -> dict[str, Any]:
    return load_external_json(tracked_bundle_root() / "bundle_manifest.json")


def readable_results_present(results_root: Path) -> bool:
    return (results_root / "run_manifest.csv").exists()


def external_refresh_reference_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in FLUID_REFERENCE_PATHS:
        exists = path.exists()
        counts = {f"{mode}_occurrence_count": 0 for mode in FLUID_MODE_TOKENS}
        if exists:
            text = path.read_text(encoding="utf-8")
            for mode in FLUID_MODE_TOKENS:
                counts[f"{mode}_occurrence_count"] = count_text_occurrences(text, mode)
        row = {"path": str(path), "exists": exists}
        row.update(counts)
        rows.append(row)
    return rows


def external_refresh_blocker_rows(reference_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snapshot = load_external_snapshot()
    manifest = load_external_manifest()
    tracked_root = tracked_bundle_root()
    v2_reference_count = sum(int(row["ethan_cfd_informed_salt_v2_occurrence_count"]) for row in reference_rows if row["exists"])
    readable_v2_results_root = FLUID_RESULTS_ROOT_BY_MODE["ethan_cfd_informed_salt_v2"]
    readable_v2_results_present = readable_results_present(readable_v2_results_root)
    refresh_notes = [str(note) for note in snapshot.get("refresh_notes", [])]
    limits = [str(note) for note in manifest.get("limits", [])]
    carry_forward_note_present = any("carried forward unchanged from v1" in note for note in refresh_notes + limits)
    return [
        {
            "blocker_id": "parallel_v2_bundle_published",
            "status": "resolved" if tracked_root.name == "ethan_cfd_informed_salt_v2" else "open",
            "evidence": f"bundle_root={tracked_root.name}; generated_on={snapshot.get('generated_on', 'missing')}",
            "required_follow_on": "keep the v2 snapshot as the tracked parallel contract until a later replacement is intentionally published",
        },
        {
            "blocker_id": "v2_loader_config_test_wiring_present",
            "status": "resolved" if v2_reference_count > 0 else "open",
            "evidence": f"tracked v2 token occurrences across audited files={v2_reference_count}",
            "required_follow_on": "preserve the parallel v1 path but keep new tracked Ethan CFD-informed runs pointed at the v2 mode",
        },
        {
            "blocker_id": "reproducible_v2_bundle_producer_present",
            "status": "resolved" if FLUID_V2_BUNDLE_PRODUCER_PATH.exists() else "open",
            "evidence": f"producer_path={FLUID_V2_BUNDLE_PRODUCER_PATH}",
            "required_follow_on": "use the producer script to rebuild the tracked static bundle whenever the local Ethan closure contract changes",
        },
        {
            "blocker_id": "readable_v2_diagnostics_present",
            "status": "resolved" if readable_v2_results_present else "open",
            "evidence": (
                f"results_root_exists={readable_v2_results_root.exists()}; "
                f"readable_results_present={readable_v2_results_present}; "
                f"results_root={readable_v2_results_root}"
            ),
            "required_follow_on": "run the bounded ethan_cfd_informed_salt_v2 campaign and publish readable status rows under results/diagnostics",
        },
        {
            "blocker_id": "refreshed_surface_tables_still_carried_from_v1",
            "status": "open" if carry_forward_note_present else "resolved",
            "evidence": (
                "tracked v2 snapshot still carries descriptor and safe-subset surface tables forward unchanged from v1"
                if carry_forward_note_present
                else "tracked v2 snapshot no longer advertises v1 surface-table carry-forward"
            ),
            "required_follow_on": "land the dedicated refreshed surface-table producer before claiming a fully regenerated v2 closure surface",
        },
    ]


def external_refresh_summary(reference_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot = load_external_snapshot()
    tracked_root = tracked_bundle_root()
    tracked_results_root = FLUID_RESULTS_ROOT_BY_MODE.get(snapshot.get("profile_descriptor_mode"), FLUID_RESULTS_ROOT_BY_MODE[FLUID_TRACKED_MODE])
    return {
        "fluid_repo_present": FLUID_ROOT.exists(),
        "tracked_bundle_root": str(tracked_root),
        "tracked_bundle_name": tracked_root.name,
        "tracked_bundle_generated_on": snapshot.get("generated_on"),
        "tracked_profile_descriptor_mode": snapshot.get("profile_descriptor_mode"),
        "tracked_results_root": str(tracked_results_root),
        "tracked_results_present": readable_results_present(tracked_results_root),
        "audited_reference_file_count": len(reference_rows),
        "audited_v1_occurrence_count": sum(int(row["ethan_cfd_informed_salt_v1_occurrence_count"]) for row in reference_rows if row["exists"]),
        "audited_v2_occurrence_count": sum(int(row["ethan_cfd_informed_salt_v2_occurrence_count"]) for row in reference_rows if row["exists"]),
        "open_blocker_count": sum(1 for row in blocker_rows if row["status"] == "open"),
    }


def readme_text(
    *,
    scenario_rows: list[dict[str, Any]],
    best_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    external_blocker_rows: list[dict[str, Any]],
    external_summary: dict[str, Any],
) -> str:
    best_note = "No readable Fluid replay rows found."
    if best_rows:
        case_bits = [
            f"{row['case_label']}: {row['scenario']} (|dT_air|={abs(finite_float(row['air_outlet_temperature_error_k'])):.2f} K, "
            f"|dm_dot|={abs(finite_float(row['mass_flow_relative_error_pct'])):.2f}%)"
            for row in best_rows
        ]
        best_note = "; ".join(case_bits)
    partial_conditions = [row["condition_label"] for row in coverage_rows if row["coverage_status"] == "partial"]
    downcomer_row = next((row for row in branch_rows if row["branch_name"] == "right_leg"), None)
    upcomer_row = next((row for row in branch_rows if row["branch_name"] == "upcomer"), None)
    hybrid_scenarios = [row for row in scenario_rows if row["scenario_family"] == "hybrid"]
    hybrid_note = "No hybrid scenarios were readable."
    if hybrid_scenarios:
        hybrid_note = (
            f"Readable hybrid scenarios: {len(hybrid_scenarios)} condition rows, "
            f"but only {sum(int(row['case_count']) for row in hybrid_scenarios)} total case rows."
        )
    blocker_note = "\n".join(
        f"- `{row['blocker_id']}` [{row['status']}]: {row['evidence']}. Next: {row['required_follow_on']}."
        for row in external_blocker_rows
    )
    return f"""# Ethan Fluid Replay Against Frozen State

Generated: `2026-06-22`

## Scope

- This package compares the current readable `Fluid` Salt replay against the
  June 22 frozen-state CFD contract.
- It does **not** assume straight sections are automatically fully developed.
- It keeps the current branch boundary explicit:
  - direct internal `Nu` is defended only on `left_lower_leg`
  - `upcomer` remains sensitivity-only
  - `right_leg` or downcomer remains blocked for direct `Nu`

## Best current readable 1D rows

{best_note}

## Coverage boundary

- {hybrid_note}
- Conditions with incomplete baseline-vs-hybrid case coverage:
  `{", ".join(partial_conditions) if partial_conditions else "none"}`.
- This is the practical meaning of the current domain-breadth gap:
  the hybrid closure family is not yet readable across the same Salt case set as
  the baseline family, so broad closure conclusions remain under-supported.

## Branch modeling boundary

- Upcomer:
  {upcomer_row['modeling_note'] if upcomer_row else 'not available'}
- Downcomer:
  {downcomer_row['modeling_note'] if downcomer_row else 'not available'}

## Current interpretation

- The present readable `Fluid` campaign is still the legacy readable surface
  rather than a new `v2` rerun.
- The external `Fluid` repo now carries a parallel `v2` bundle, campaign, and
  test path, but there are not yet readable `v2` diagnostics on disk.
- It is already useful for quantifying current 1D error trends and showing
  which closure family currently helps.
- It is not broad enough yet to defend one shared direct internal HTC closure
  over all Salt branches or cases.

## External refresh status

- Tracked bundle root:
  `{external_summary.get('tracked_bundle_name', 'missing')}`
- Tracked bundle generated on:
  `{external_summary.get('tracked_bundle_generated_on', 'missing')}`
- Audited `v1` token occurrences across the loader/config/test surface:
  `{external_summary.get('audited_v1_occurrence_count', 'missing')}`
- Audited `v2` token occurrences across the loader/config/test surface:
  `{external_summary.get('audited_v2_occurrence_count', 'missing')}`
- Tracked `v2` readable-results root present:
  `{external_summary.get('tracked_results_present', 'missing')}`
- Refresh status rows:
{blocker_note}
"""


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))

    one_d_rows = load_csv_rows(FROZEN_DIR / "one_d_readable_status.csv")
    best_rows = best_one_d_rows(one_d_rows)
    scenario_rows = scenario_rollup_rows(one_d_rows)
    coverage_rows = hybrid_coverage_rows(one_d_rows)
    branch_rows = branch_boundary_rows(load_csv_rows(FROZEN_DIR / "branch_behavior_summary.csv"))
    need_rows = data_need_rows(load_csv_rows(FROZEN_DIR / "data_needs.csv"))
    external_reference_rows = external_refresh_reference_rows()
    external_blocker_rows = external_refresh_blocker_rows(external_reference_rows)
    external_summary = external_refresh_summary(external_reference_rows, external_blocker_rows)

    csv_dump_rows(output_dir / "fluid_replay_status.csv", one_d_rows)
    csv_dump_rows(output_dir / "fluid_best_case_rows.csv", best_rows)
    csv_dump_rows(output_dir / "scenario_rollup.csv", scenario_rows)
    csv_dump_rows(output_dir / "hybrid_coverage.csv", coverage_rows)
    csv_dump_rows(output_dir / "branch_modeling_boundary.csv", branch_rows)
    csv_dump_rows(output_dir / "data_needs_for_replay.csv", need_rows)
    csv_dump_rows(output_dir / "external_refresh_references.csv", external_reference_rows)
    csv_dump_rows(output_dir / "external_refresh_blockers.csv", external_blocker_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "readable_row_count": len(one_d_rows),
        "best_case_count": len(best_rows),
        "scenario_count": len(scenario_rows),
        "partial_coverage_condition_count": sum(1 for row in coverage_rows if row["coverage_status"] == "partial"),
        "hybrid_case_count": sum(int(row["hybrid_case_count"]) for row in coverage_rows),
        "external_refresh": external_summary,
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        readme_text(
            scenario_rows=scenario_rows,
            best_rows=best_rows,
            coverage_rows=coverage_rows,
            branch_rows=branch_rows,
            external_blocker_rows=external_blocker_rows,
            external_summary=external_summary,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
