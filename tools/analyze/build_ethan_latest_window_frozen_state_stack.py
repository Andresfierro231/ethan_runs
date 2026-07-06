#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_ethan_frozen_state_results_package as legacy  # noqa: E402
from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, finite_float, load_csv_rows, write_json  # noqa: E402
from tools.common import ensure_dir, iso_timestamp  # noqa: E402

CASE_SPECS: tuple[dict[str, str], ...] = (
    {
        "case_key": "salt1_jin",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "case_label": "Salt 1 Jin",
        "checkpoint_subdir": "salt1_jin",
    },
    {
        "case_key": "salt2_cont",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "case_label": "Salt 2 Jin",
        "checkpoint_subdir": "salt2_cont",
    },
    {
        "case_key": "salt3_cont",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "case_label": "Salt 3 Jin",
        "checkpoint_subdir": "salt3_cont",
    },
    {
        "case_key": "salt4_cont",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "case_label": "Salt 4 Jin",
        "checkpoint_subdir": "salt4_cont",
    },
)

BRANCH_FIT_STATUS = {
    "left_lower_leg": "fit_used",
    "left_upper_leg": "sensitivity_only",
    "test_section_span": "sensitivity_only",
    "upcomer": "sensitivity_only",
    "right_leg": "excluded",
    "lower_leg": "excluded",
    "upper_leg": "excluded",
}

DEFAULT_FREEZE_WINDOWS_CSV = ROOT / "reports" / "2026-06-23_ethan_cfd_freeze_checkpoint" / "freeze_case_windows.csv"
DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV = (
    ROOT / "reports" / "2026-06-23_ethan_cfd_freeze_checkpoint" / "representative_timesteps.csv"
)
DEFAULT_CHECKPOINT_ROOT = ROOT / "tmp" / "2026-06-23_salt_last20_checkpoint"
DEFAULT_CASE_ANALYSIS_ROOT = ROOT / "tmp" / "2026-06-23_ethan_latest_window_case_analysis_refresh"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_frozen_state_results_latest_window"
DEFAULT_IMPORT_MANIFEST_PATH = ROOT / "imports" / "2026-06-23_ethan_frozen_state_results_latest_window.json"
CASE_ANALYSIS_BUILDER = ROOT / "tools" / "analyze" / "build_ethan_case_analysis_package.py"
TARGET_REPRESENTATIVE_COUNT = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the nominal Salt Jin case-analysis packages from the June 23 "
            "checkpoint windows and publish a latest-window frozen-state package."
        )
    )
    parser.add_argument("--freeze-windows-csv", default=str(DEFAULT_FREEZE_WINDOWS_CSV))
    parser.add_argument("--representative-timesteps-csv", default=str(DEFAULT_REPRESENTATIVE_TIMESTEPS_CSV))
    parser.add_argument("--checkpoint-root", default=str(DEFAULT_CHECKPOINT_ROOT))
    parser.add_argument("--case-analysis-root", default=str(DEFAULT_CASE_ANALYSIS_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_MANIFEST_PATH))
    parser.add_argument(
        "--skip-case-refresh",
        action="store_true",
        help="Reuse existing refreshed case-analysis package roots if they already exist.",
    )
    return parser.parse_args()


def canonical_time_token(value: str) -> str:
    token = str(value).strip()
    if not token:
        return token
    if "." in token and "e" not in token.lower():
        return token.rstrip("0").rstrip(".")
    return token


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def normalized_delta(latest: float, mean_value: float) -> float:
    if not math.isfinite(latest) or not math.isfinite(mean_value) or mean_value == 0.0:
        return math.nan
    return abs(latest - mean_value) / abs(mean_value)


def load_freeze_windows(path: Path) -> dict[str, dict[str, str]]:
    rows = load_csv_rows(path)
    return {row["case_key"]: row for row in rows}


def load_representative_times(path: Path) -> dict[str, list[str]]:
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in load_csv_rows(path):
        grouped[row["case_key"]].append((int(row["representative_index"]), canonical_time_token(row["time_s"])))
    return {
        case_key: [time_token for _idx, time_token in sorted(items, key=lambda item: item[0])]
        for case_key, items in grouped.items()
    }


def build_case_refresh_manifest_rows(
    *,
    freeze_windows: dict[str, dict[str, str]],
    representative_times: dict[str, list[str]],
    checkpoint_root: Path,
    case_analysis_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        case_key = spec["case_key"]
        freeze_row = freeze_windows[case_key]
        times = representative_times[case_key]
        runtime_root = checkpoint_root / spec["checkpoint_subdir"]
        package_root = case_analysis_root / case_key
        rows.append(
            {
                "case_key": case_key,
                "source_id": spec["source_id"],
                "case_label": spec["case_label"],
                "runtime_root": str(runtime_root),
                "package_root": str(package_root),
                "time_selector": ",".join(times),
                "representative_time_count": len(times),
                "freeze_representative_time_count": int(float(freeze_row["representative_time_count"])),
                "latest_retained_time_s": finite_float(freeze_row.get("latest_retained_time_s")),
                "restart_time_s": finite_float(freeze_row.get("restart_time_s")),
            }
        )
    return rows


def refresh_case_package(row: dict[str, Any]) -> None:
    print(
        f"[latest-window] refreshing {row['case_key']} -> {row['source_id']} "
        f"with {row['representative_time_count']} representative times",
        flush=True,
    )
    command = [
        sys.executable,
        str(CASE_ANALYSIS_BUILDER),
        "--source-id",
        str(row["source_id"]),
        "--runtime-root",
        str(row["runtime_root"]),
        "--time-selector",
        str(row["time_selector"]),
        "--output-dir",
        str(row["package_root"]),
    ]
    subprocess.run(command, check=True, cwd=str(ROOT))
    print(f"[latest-window] completed {row['case_key']}", flush=True)


def branch_lookup(branch_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["branch_name"]: row for row in branch_rows}


def branch_mean_bulk_k(branch_rows: list[dict[str, str]], branch_name: str) -> float:
    return finite_float(branch_lookup(branch_rows).get(branch_name, {}).get("mean_bulk_temp_fluid_area_avg_k"))


def load_case_context(
    *,
    manifest_row: dict[str, Any],
    freeze_row: dict[str, str],
    package_root: Path,
) -> dict[str, Any]:
    heat_row = load_csv_rows(package_root / "heat_loss_summary.csv")[0]
    branch_rows = load_csv_rows(package_root / "branch_thermal_summary.csv")
    profile_rows = load_csv_rows(package_root / "branch_thermal_profiles.csv")
    summary_json = json.loads((package_root / "summary.json").read_text(encoding="utf-8"))
    retained_count = int(float(freeze_row["representative_time_count"]))
    window_status = "window_shortfall" if retained_count < TARGET_REPRESENTATIVE_COUNT else "target_window"
    return {
        "case_key": manifest_row["case_key"],
        "source_id": manifest_row["source_id"],
        "case_label": manifest_row["case_label"],
        "package_root": package_root,
        "runtime_root": Path(str(manifest_row["runtime_root"])),
        "time_selector": str(manifest_row["time_selector"]),
        "representative_time_count": retained_count,
        "late_window_time_start_s": finite_float(freeze_row.get("representative_start_s")),
        "late_window_time_end_s": finite_float(freeze_row.get("representative_end_s")),
        "latest_retained_time_s": finite_float(freeze_row.get("latest_retained_time_s")),
        "restart_time_s": finite_float(freeze_row.get("restart_time_s")),
        "advanced_since_restart_s": finite_float(freeze_row.get("advanced_since_restart_s")),
        "window_status": window_status,
        "window_status_note": (
            "Representative window retained only 18 exact checkpoint times; include as provisional today-freeze evidence."
            if window_status == "window_shortfall"
            else "Representative window retained the full 20 exact checkpoint times."
        ),
        "heat_row": heat_row,
        "branch_rows": branch_rows,
        "profile_rows": profile_rows,
        "profile_name": str(summary_json.get("profile_name", "")),
    }


def fit_status_for_branch(branch_name: str) -> str:
    return BRANCH_FIT_STATUS.get(branch_name, "excluded")


def support_fraction_for_branch(profile_rows: list[dict[str, str]], branch_name: str) -> float:
    branch_rows = [row for row in profile_rows if row.get("branch_name") == branch_name]
    if not branch_rows:
        return math.nan
    usable_count = sum(1 for row in branch_rows if str(row.get("thermal_support_status", "")).strip() == "usable")
    return usable_count / len(branch_rows)


def branch_behavior_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for context in case_contexts:
        for row in context["branch_rows"]:
            grouped[row["branch_name"]].append({"summary": row, "context": context})
    rows_out: list[dict[str, Any]] = []
    for branch_name, entries in sorted(grouped.items()):
        fit_status = fit_status_for_branch(branch_name)
        support_values = [
            support_fraction_for_branch(entry["context"]["profile_rows"], branch_name)
            for entry in entries
        ]
        time_count_shortfall = sum(1 for entry in entries if entry["context"]["window_status"] == "window_shortfall")
        domain_note = (
            "Latest-window means rebuilt directly from the June 23 checkpoint package roots."
            if time_count_shortfall == 0
            else "Latest-window means rebuilt directly from the June 23 checkpoint roots; includes Salt 1 short-window provisional evidence."
        )
        rows_out.append(
            {
                "branch_name": branch_name,
                "branch_alias": legacy.BRANCH_ALIAS.get(branch_name, branch_name),
                "case_count": len(entries),
                "fit_used_case_count": len(entries) if fit_status == "fit_used" else 0,
                "sensitivity_only_case_count": len(entries) if fit_status == "sensitivity_only" else 0,
                "excluded_case_count": len(entries) if fit_status == "excluded" else 0,
                "mean_re_effective": math.nan,
                "mean_nu_effective": math.nan,
                "mean_htc_effective_w_m2_k": safe_mean(
                    [finite_float(entry["summary"].get("mean_effective_htc_w_m2_k")) for entry in entries]
                ),
                "mean_support_fraction": safe_mean(support_values),
                "mean_residual_fraction_of_wall_heat": math.nan,
                "domain_note": domain_note,
                "dominant_fit_status": fit_status,
                "modeling_note": legacy.BRANCH_MODELING_NOTES.get(branch_name, ""),
            }
        )
    return rows_out


def branch_development_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        for row in context["branch_rows"]:
            branch_name = row["branch_name"]
            rows_out.append(
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "window_status": context["window_status"],
                    "representative_time_count": context["representative_time_count"],
                    "branch_name": branch_name,
                    "fit_lane": fit_status_for_branch(branch_name),
                    "mean_bulk_temp_k": finite_float(row.get("mean_bulk_temp_fluid_area_avg_k")),
                    "mean_wall_temp_k": finite_float(row.get("mean_t_wall_area_avg_k")),
                    "mean_bulk_minus_wall_temp_k": finite_float(row.get("mean_bulk_minus_wall_temp_k")),
                    "mean_effective_htc_w_m2_k": finite_float(row.get("mean_effective_htc_w_m2_k")),
                    "mean_effective_ua_per_m_w_m_k": finite_float(row.get("mean_effective_ua_per_m_w_m_k")),
                    "mean_mdot_kg_s": finite_float(row.get("mean_mdot_mean_abs_kg_s")),
                    "mean_wall_heat_per_length_w_m": finite_float(row.get("mean_wall_heat_per_length_w_m")),
                    "support_fraction": support_fraction_for_branch(context["profile_rows"], branch_name),
                    "thermal_warning_fraction": finite_float(row.get("thermal_warning_fraction")),
                    "modeling_note": legacy.BRANCH_MODELING_NOTES.get(branch_name, ""),
                }
            )
    return rows_out


def reduce_profile_rows_by_branch_and_time(profile_rows: list[dict[str, str]]) -> dict[tuple[str, float], dict[str, float]]:
    grouped: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
    for row in profile_rows:
        grouped[(row["branch_name"], finite_float(row.get("time_s")))].append(row)
    reduced: dict[tuple[str, float], dict[str, float]] = {}
    for key, rows in grouped.items():
        reduced[key] = {
            "bulk_temp_k": safe_mean([finite_float(row.get("bulk_temp_fluid_area_avg_k")) for row in rows]),
            "wall_temp_k": safe_mean([finite_float(row.get("t_wall_area_avg_k")) for row in rows]),
            "htc_w_m2_k": safe_mean([finite_float(row.get("effective_htc_w_m2_k")) for row in rows]),
            "wall_heat_per_length_w_m": safe_mean([finite_float(row.get("wall_heat_per_length_w_m")) for row in rows]),
            "mdot_kg_s": safe_mean([finite_float(row.get("mdot_mean_abs_kg_s")) for row in rows]),
        }
    return reduced


def branch_drift_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        reduced = reduce_profile_rows_by_branch_and_time(context["profile_rows"])
        branch_times: dict[str, list[tuple[float, dict[str, float]]]] = defaultdict(list)
        for (branch_name, time_s), payload in reduced.items():
            if math.isfinite(time_s):
                branch_times[branch_name].append((time_s, payload))
        for branch_name, entries in sorted(branch_times.items()):
            entries.sort(key=lambda item: item[0])
            latest_time, latest_payload = entries[-1]
            bulk_values = [item[1]["bulk_temp_k"] for item in entries]
            wall_values = [item[1]["wall_temp_k"] for item in entries]
            htc_values = [item[1]["htc_w_m2_k"] for item in entries]
            rows_out.append(
                {
                    "source_id": context["source_id"],
                    "case_label": context["case_label"],
                    "branch_name": branch_name,
                    "window_status": context["window_status"],
                    "latest_time_s": latest_time,
                    "time_row_count": len(entries),
                    "bulk_mean_k": safe_mean(bulk_values),
                    "bulk_latest_k": latest_payload["bulk_temp_k"],
                    "bulk_latest_vs_mean_fraction": normalized_delta(latest_payload["bulk_temp_k"], safe_mean(bulk_values)),
                    "wall_mean_k": safe_mean(wall_values),
                    "wall_latest_k": latest_payload["wall_temp_k"],
                    "wall_latest_vs_mean_fraction": normalized_delta(latest_payload["wall_temp_k"], safe_mean(wall_values)),
                    "htc_mean_w_m2_k": safe_mean(htc_values),
                    "htc_latest_w_m2_k": latest_payload["htc_w_m2_k"],
                    "htc_latest_vs_mean_fraction": normalized_delta(latest_payload["htc_w_m2_k"], safe_mean(htc_values)),
                    "wall_heat_per_length_mean_w_m": safe_mean([item[1]["wall_heat_per_length_w_m"] for item in entries]),
                    "wall_heat_per_length_latest_w_m": latest_payload["wall_heat_per_length_w_m"],
                    "mdot_mean_kg_s": safe_mean([item[1]["mdot_kg_s"] for item in entries]),
                    "mdot_latest_kg_s": latest_payload["mdot_kg_s"],
                }
            )
    return rows_out


def branch_drift_rollup(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["branch_name"]].append(row)
    rows_out: list[dict[str, Any]] = []
    for branch_name, rows in sorted(grouped.items()):
        rows_out.append(
            {
                "branch_name": branch_name,
                "case_count": len(rows),
                "mean_bulk_latest_vs_mean_fraction": safe_mean(
                    [finite_float(row.get("bulk_latest_vs_mean_fraction")) for row in rows]
                ),
                "mean_wall_latest_vs_mean_fraction": safe_mean(
                    [finite_float(row.get("wall_latest_vs_mean_fraction")) for row in rows]
                ),
                "mean_htc_latest_vs_mean_fraction": safe_mean(
                    [finite_float(row.get("htc_latest_vs_mean_fraction")) for row in rows]
                ),
                "max_htc_latest_vs_mean_fraction": max(
                    (finite_float(row.get("htc_latest_vs_mean_fraction")) for row in rows),
                    default=math.nan,
                ),
            }
        )
    return rows_out


def frozen_state_contract_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        branch_rows = context["branch_rows"]
        rows_out.append(
            {
                "source_id": context["source_id"],
                "case_label": context["case_label"],
                "run_status": "checkpoint_latest_window_frozen",
                "comparison_ready": "comparison_candidate",
                "late_window_time_start_s": context["late_window_time_start_s"],
                "late_window_time_end_s": context["late_window_time_end_s"],
                "late_window_time_count": context["representative_time_count"],
                "late_window_target_count": TARGET_REPRESENTATIVE_COUNT,
                "primary_frozen_state_basis": "late_window_mean",
                "sensitivity_snapshot_basis": "latest_retained_time",
                "latest_retained_time_s": context["latest_retained_time_s"],
                "window_status": context["window_status"],
                "window_status_note": context["window_status_note"],
                "package_root": str(context["package_root"]),
                "runtime_root": str(context["runtime_root"]),
                "profile_name": context["profile_name"],
                "downcomer_to_upcomer_bulk_delta_k": (
                    branch_mean_bulk_k(branch_rows, "right_leg") - branch_mean_bulk_k(branch_rows, "upcomer")
                ),
                "heater_to_cooler_bulk_delta_k": (
                    branch_mean_bulk_k(branch_rows, "lower_leg") - branch_mean_bulk_k(branch_rows, "upper_leg")
                ),
            }
        )
    return rows_out


def case_window_summary_rows(case_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for context in case_contexts:
        heat_row = context["heat_row"]
        rows_out.append(
            {
                "case_key": context["case_key"],
                "source_id": context["source_id"],
                "case_label": context["case_label"],
                "window_status": context["window_status"],
                "window_status_note": context["window_status_note"],
                "representative_time_count": context["representative_time_count"],
                "restart_time_s": context["restart_time_s"],
                "latest_retained_time_s": context["latest_retained_time_s"],
                "advanced_since_restart_s": context["advanced_since_restart_s"],
                "late_window_time_start_s": context["late_window_time_start_s"],
                "late_window_time_end_s": context["late_window_time_end_s"],
                "package_root": str(context["package_root"]),
                "runtime_root": str(context["runtime_root"]),
                "ambient_proxy_w": finite_float(heat_row.get("ambient_proxy_w")),
                "cooling_branch_total_removal_w": finite_float(heat_row.get("cooling_branch_total_removal_w")),
                "section_heater_net_q_w": finite_float(heat_row.get("section_heater_net_q_w")),
                "section_test_section_net_q_w": finite_float(heat_row.get("section_test_section_net_q_w")),
                "section_junctions_net_q_w": finite_float(heat_row.get("section_junctions_net_q_w")),
                "net_total_q_pct_of_heater": finite_float(heat_row.get("net_total_q_pct_of_heater")),
            }
        )
    return rows_out


def short_window_note(case_contexts: list[dict[str, Any]]) -> str:
    flagged = [context for context in case_contexts if context["window_status"] == "window_shortfall"]
    if not flagged:
        return "All nominal Salt Jin checkpoint freezes retained the full 20 exact representative times."
    labels = ", ".join(context["case_label"] for context in flagged)
    return (
        f"{labels} retained fewer than {TARGET_REPRESENTATIVE_COUNT} representative times in the June 23 checkpoint "
        "and should stay flagged as provisional short-window evidence."
    )


def build_readme(
    *,
    case_contexts: list[dict[str, Any]],
    branch_behavior: list[dict[str, Any]],
) -> str:
    best_one_d = legacy.best_one_d_rows(legacy.one_d_status_rows())
    best_one_d_note = "No readable external 1D diagnostics found."
    if best_one_d:
        example = best_one_d[0]
        best_one_d_note = (
            "Readable Fluid diagnostics still exist only as the older June 19 external bundle. "
            f"Example readable row: {example['case_label']} / {example['scenario']} with air-outlet error "
            f"{example['air_outlet_temperature_error_k']:.2f} K and mass-flow error "
            f"{example['mass_flow_relative_error_pct']:.2f}%."
        )
    fit_counts = Counter(row["dominant_fit_status"] for row in branch_behavior)
    return f"""# Ethan Latest-Window Frozen-State Results

Generated: `{iso_timestamp()}`

## Scope

- Nominal Salt Jin family only:
  `Salt 1 Jin`, `Salt 2 Jin`, `Salt 3 Jin`, `Salt 4 Jin`.
- These package roots were rebuilt from the June 23 checkpoint staging tree
  under `tmp/2026-06-23_salt_last20_checkpoint/`.
- Primary pseudo-steady basis: retained representative-window mean from the
  refreshed package roots.
- Sensitivity overlay: latest retained checkpoint time.

## Main findings

- Straight sections are **not** assumed fully developed by default. This stack
  preserves branchwise development behavior from the refreshed case-analysis
  packages instead of replacing those branches with fully developed defaults.
- `left_lower_leg` remains the best current direct internal HTC evidence lane.
- `upcomer` remains a separate sensitivity-only modeling branch and should not
  be collapsed into the direct straight-section law.
- `right_leg` / downcomer remains blocked for direct internal `Nu`; use it as a
  return-leg discrepancy indicator, not as a defended direct fit lane.
- Branch fit-status counts on this latest-window nominal Salt surface:
  `fit_used={fit_counts.get("fit_used", 0)}`,
  `sensitivity_only={fit_counts.get("sensitivity_only", 0)}`,
  `excluded={fit_counts.get("excluded", 0)}`.
- {short_window_note(case_contexts)}

## 1D boundary

- {best_one_d_note}
- This package intentionally supersedes the ambiguity of reusing the older
  June 15 live-analysis roots for today’s local pseudo-steady comparison work.
"""


def write_import_manifest(
    *,
    freeze_windows_csv: Path,
    representative_timesteps_csv: Path,
    output_dir: Path,
    case_refresh_rows: list[dict[str, Any]],
    import_manifest_path: Path,
) -> None:
    payload = {
        "generated_at": iso_timestamp(),
        "package": "2026-06-23_ethan_frozen_state_results_latest_window",
        "inputs": {
            "freeze_windows_csv": str(freeze_windows_csv.resolve()),
            "representative_timesteps_csv": str(representative_timesteps_csv.resolve()),
            "checkpoint_root": str(DEFAULT_CHECKPOINT_ROOT.resolve()),
            "legacy_closure_map_csv": str((legacy.BLOCKER_DIR / "one_d_closure_map.csv").resolve()),
            "legacy_feature_stability_csv": str((legacy.FEATURE_DIR / "feature_stability_summary.csv").resolve()),
        },
        "case_refresh_rows": case_refresh_rows,
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "frozen_state_contract_csv": str((output_dir / "frozen_state_contract.csv").resolve()),
            "case_window_summary_csv": str((output_dir / "case_window_summary.csv").resolve()),
            "branch_behavior_summary_csv": str((output_dir / "branch_behavior_summary.csv").resolve()),
            "branch_development_summary_csv": str((output_dir / "branch_development_summary.csv").resolve()),
            "branch_drift_by_case_csv": str((output_dir / "branch_drift_by_case.csv").resolve()),
            "one_d_readable_status_csv": str((output_dir / "one_d_readable_status.csv").resolve()),
        },
    }
    write_json(import_manifest_path, payload)


def main() -> int:
    args = parse_args()
    freeze_windows_csv = Path(args.freeze_windows_csv)
    representative_timesteps_csv = Path(args.representative_timesteps_csv)
    checkpoint_root = Path(args.checkpoint_root)
    case_analysis_root = ensure_dir(Path(args.case_analysis_root))
    output_dir = ensure_dir(Path(args.output_dir))
    import_manifest_path = Path(args.import_manifest_path)

    freeze_windows = load_freeze_windows(freeze_windows_csv)
    representative_times = load_representative_times(representative_timesteps_csv)
    case_refresh_rows = build_case_refresh_manifest_rows(
        freeze_windows=freeze_windows,
        representative_times=representative_times,
        checkpoint_root=checkpoint_root,
        case_analysis_root=case_analysis_root,
    )

    case_contexts: list[dict[str, Any]] = []
    for refresh_row in case_refresh_rows:
        package_root = Path(str(refresh_row["package_root"]))
        if not args.skip_case_refresh or not (package_root / "summary.json").exists():
            refresh_case_package(refresh_row)
        context = load_case_context(
            manifest_row=refresh_row,
            freeze_row=freeze_windows[str(refresh_row["case_key"])],
            package_root=package_root,
        )
        case_contexts.append(context)

    frozen_rows = frozen_state_contract_rows(case_contexts)
    case_window_rows = case_window_summary_rows(case_contexts)
    branch_behavior = branch_behavior_rows(case_contexts)
    branch_development = branch_development_rows(case_contexts)
    branch_drift = branch_drift_rows(case_contexts)
    branch_drift_rollup = branch_drift_rollup(branch_drift)
    feature_stability = load_csv_rows(legacy.FEATURE_DIR / "feature_stability_summary.csv")
    model_summary = legacy.load_json(legacy.MODEL_DIR / "summary.json")
    feature_fit = legacy.load_json(legacy.MODEL_DIR / "salt_feature_keff_fit_results.json")
    closure_rows = load_csv_rows(legacy.BLOCKER_DIR / "one_d_closure_map.csv")
    closure_map = legacy.refreshed_closure_map(closure_rows, model_summary, feature_fit)
    data_needs = legacy.data_needs_rows()
    phase_rows = legacy.phase_plan_rows()
    one_d_rows = legacy.one_d_status_rows()
    one_d_best = legacy.best_one_d_rows(one_d_rows)

    csv_dump_rows(output_dir / "case_package_refresh_manifest.csv", case_refresh_rows)
    csv_dump_rows(output_dir / "frozen_state_contract.csv", frozen_rows)
    csv_dump_rows(output_dir / "case_window_summary.csv", case_window_rows)
    csv_dump_rows(output_dir / "branch_behavior_summary.csv", branch_behavior)
    csv_dump_rows(output_dir / "branch_development_summary.csv", branch_development)
    csv_dump_rows(output_dir / "branch_drift_by_case.csv", branch_drift)
    csv_dump_rows(output_dir / "branch_drift_rollup.csv", branch_drift_rollup)
    csv_dump_rows(output_dir / "feature_stability_summary.csv", feature_stability)
    csv_dump_rows(output_dir / "closure_map_current.csv", closure_map)
    csv_dump_rows(output_dir / "data_needs.csv", data_needs)
    csv_dump_rows(output_dir / "phase_plan.csv", phase_rows)
    csv_dump_rows(output_dir / "one_d_readable_status.csv", one_d_rows)
    csv_dump_rows(output_dir / "one_d_best_readable_rows.csv", one_d_best)

    summary = {
        "generated_at": iso_timestamp(),
        "nominal_case_count": len(case_contexts),
        "short_window_case_count": sum(1 for context in case_contexts if context["window_status"] == "window_shortfall"),
        "branch_count": len(branch_behavior),
        "closure_feature_status": feature_fit.get("recommended_status", ""),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        build_readme(case_contexts=case_contexts, branch_behavior=branch_behavior),
        encoding="utf-8",
    )
    write_import_manifest(
        freeze_windows_csv=freeze_windows_csv,
        representative_timesteps_csv=representative_timesteps_csv,
        output_dir=output_dir,
        case_refresh_rows=case_refresh_rows,
        import_manifest_path=import_manifest_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
