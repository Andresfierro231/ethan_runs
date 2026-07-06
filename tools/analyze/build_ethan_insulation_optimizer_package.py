#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_ethan_runs")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    save_matplotlib_figure,
)

ETHAN_MODEL_FILE = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools"
    / "tamu_first_order_model"
    / "Ethan_wall_and_heat_losses"
    / "first_order_model_tamu_loop.py"
)
SALT_DASHBOARD = WORKSPACE_ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package" / "salt_dashboard.csv"
WATER_DASHBOARD = WORKSPACE_ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package" / "water_dashboard.csv"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-19_ethan_insulation_optimizer_package"

SALT_TRACE_THICKNESSES_IN = [0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40, 1.65, 1.80, 2.00, 2.40, 2.80]
WATER_TRACE_THICKNESSES_IN = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00, 1.20]
DEFAULT_BISECTION_ITERS = 6
EPS = 1.0e-9


def meters_to_inches(value_m: float) -> float:
    return value_m / 0.0254


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return math.nan
    return parsed if math.isfinite(parsed) else math.nan


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return sum(payload) / len(payload)


def safe_std(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if len(payload) < 2:
        return 0.0
    mu = sum(payload) / len(payload)
    return math.sqrt(sum((value - mu) ** 2 for value in payload) / (len(payload) - 1))


def fmt(value: float, digits: int = 3) -> str:
    if not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def rounded_recommendation_in(value: float) -> float:
    if not math.isfinite(value):
        return math.nan
    return round(value * 20.0) / 20.0


def case_name_from_base_case_id(base_case_id: str) -> str:
    family = "Salt" if base_case_id.startswith("salt") else "Water"
    suffix = base_case_id.split("_")[-1]
    return f"{family} {suffix}"


def case_sort_key(case_name: str) -> tuple[int, int]:
    family_rank = 0 if case_name.startswith("Salt") else 1
    number = int(case_name.split()[-1])
    return family_rank, number


def load_ethan_namespace() -> dict[str, Any]:
    text = ETHAN_MODEL_FILE.read_text(encoding="utf-8")
    start = text.index("import math")
    end = text.index("\n# Main output")
    namespace: dict[str, Any] = {"__file__": str(ETHAN_MODEL_FILE)}
    exec(text[start:end], namespace)
    return namespace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the additive Ethan insulation optimizer package from the wall-loss model and known 3D dashboard metadata."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild using one or more known CFD source IDs.",
    )
    parser.add_argument(
        "--case-name",
        action="append",
        dest="case_names",
        help="Optional explicit Ethan experimental case names such as 'Salt 2' or 'Water 3'.",
    )
    return parser.parse_args()


class EthanEvaluator:
    def __init__(self, namespace: dict[str, Any]) -> None:
        self.ns = namespace
        self.cache: dict[tuple[str, float, float], dict[str, Any]] = {}

    def _insulation_settings(self, case_name: str) -> tuple[Any, float]:
        if case_name.startswith("Salt"):
            return self.ns["insulation_salt"], meters_to_inches(float(self.ns["insulation_thickness_salt"]))
        return self.ns["insulation_water"], meters_to_inches(float(self.ns["insulation_thickness_water"]))

    def evaluate(self, case_name: str, thickness_in: float, temperature_offset_c: float = 0.0) -> dict[str, Any]:
        key = (case_name, round(thickness_in, 6), round(temperature_offset_c, 6))
        if key in self.cache:
            return self.cache[key]

        case_data = self.ns["EXPERIMENTAL_CASES"][case_name]
        family = "salt" if case_name.startswith("Salt") else "water"
        ins_mat, _ = self._insulation_settings(case_name)
        thickness_m = float(self.ns["inches_to_meters"](thickness_in))
        ambient_k = float(case_data["air_T_inlet_C"]) + 273.15

        loop = self.ns["solve_case"](
            case_data,
            T_offset_C=temperature_offset_c,
            ins_mat=ins_mat,
            ins_t=thickness_m,
            T_ambient_K=ambient_k,
        )
        shifted_temps = {
            key_name: float(value) + temperature_offset_c for key_name, value in case_data["temps_C"].items()
        }
        fin_results = self.ns["solve_all_fins"](
            shifted_temps,
            ins_mat,
            thickness_m,
            T_ambient_K=ambient_k,
        )

        q_passive = float(self.ns["total_Q_outward_outer"](loop))
        q_fins = sum(float(result["Q"]) for result in fin_results.values())
        q_total_loss = q_passive + q_fins
        q_cooler, mdot = self.ns["compute_Q_cooler"](case_data)
        q_heater = float(case_data["heater_power_W"])
        q_test_section = float(case_data["test_section_power_W"])
        q_expected = q_heater + q_test_section - float(q_cooler)
        q_unaccounted = q_expected - q_total_loss

        payload = {
            "case_name": case_name,
            "family": family,
            "thickness_in": thickness_in,
            "temperature_offset_c": temperature_offset_c,
            "q_heater_w": q_heater,
            "q_test_section_w": q_test_section,
            "q_cooler_w": float(q_cooler),
            "mdot_air_kg_s": float(mdot),
            "q_expected_loss_w": q_expected,
            "q_passive_w": q_passive,
            "q_fins_w": q_fins,
            "q_total_loss_w": q_total_loss,
            "q_unaccounted_w": q_unaccounted,
            "air_inlet_c": float(case_data["air_T_inlet_C"]),
            "air_outlet_c": float(case_data["air_T_outlet_C"]),
            "heater_power_w": q_heater,
            "cooler_power_reported_w": float(case_data["cooler_power_W"]),
        }
        self.cache[key] = payload
        return payload


def trace_points_for_case(case_name: str) -> list[float]:
    return SALT_TRACE_THICKNESSES_IN[:] if case_name.startswith("Salt") else WATER_TRACE_THICKNESSES_IN[:]


def build_trace_rows(evaluator: EthanEvaluator, case_name: str) -> list[dict[str, Any]]:
    rows = [evaluator.evaluate(case_name, thickness_in) for thickness_in in trace_points_for_case(case_name)]
    return sorted(rows, key=lambda row: row["thickness_in"])


def find_sign_change_bounds(trace_rows: list[dict[str, Any]]) -> tuple[float, float] | None:
    for left, right in zip(trace_rows, trace_rows[1:]):
        y_left = left["q_unaccounted_w"]
        y_right = right["q_unaccounted_w"]
        if abs(y_left) <= EPS:
            return left["thickness_in"], left["thickness_in"]
        if y_left * y_right < 0.0 or abs(y_right) <= EPS:
            return left["thickness_in"], right["thickness_in"]
    return None


def interpolate_zero_crossing(x0: float, y0: float, x1: float, y1: float) -> float:
    if abs(y1 - y0) <= EPS:
        return 0.5 * (x0 + x1)
    return x0 + (0.0 - y0) * (x1 - x0) / (y1 - y0)


def refine_case_optimum(
    evaluator: EthanEvaluator,
    case_name: str,
    trace_rows: list[dict[str, Any]],
    max_iters: int = DEFAULT_BISECTION_ITERS,
) -> tuple[dict[str, Any], str]:
    best_row = min(trace_rows, key=lambda row: abs(row["q_unaccounted_w"]))
    bounds = find_sign_change_bounds(trace_rows)
    if bounds is None:
        return best_row, "coarse_grid_min_abs_q_unaccounted"

    low_in, high_in = bounds
    if abs(high_in - low_in) <= EPS:
        return evaluator.evaluate(case_name, low_in), "exact_trace_zero"

    low_row = evaluator.evaluate(case_name, low_in)
    high_row = evaluator.evaluate(case_name, high_in)

    for _ in range(max_iters):
        mid_in = 0.5 * (low_in + high_in)
        mid_row = evaluator.evaluate(case_name, mid_in)
        if abs(mid_row["q_unaccounted_w"]) < abs(best_row["q_unaccounted_w"]):
            best_row = mid_row
        if low_row["q_unaccounted_w"] * mid_row["q_unaccounted_w"] <= 0.0:
            high_in = mid_in
            high_row = mid_row
        else:
            low_in = mid_in
            low_row = mid_row

    root_guess_in = interpolate_zero_crossing(
        low_in,
        low_row["q_unaccounted_w"],
        high_in,
        high_row["q_unaccounted_w"],
    )
    root_row = evaluator.evaluate(case_name, root_guess_in)
    if abs(root_row["q_unaccounted_w"]) < abs(best_row["q_unaccounted_w"]):
        best_row = root_row
    return best_row, "trace_bracket_plus_bisection"


def estimate_optimum_uncertainty(
    evaluator: EthanEvaluator,
    namespace: dict[str, Any],
    optimum_row: dict[str, Any],
) -> dict[str, float]:
    case_name = optimum_row["case_name"]
    thickness_in = optimum_row["thickness_in"]
    high_row = evaluator.evaluate(case_name, thickness_in, temperature_offset_c=float(namespace["TC_UNCERTAINTY_C"]))
    low_row = evaluator.evaluate(case_name, thickness_in, temperature_offset_c=-float(namespace["TC_UNCERTAINTY_C"]))

    d_q_heater = float(namespace["compute_power_uncertainty"](optimum_row["q_heater_w"]))
    d_q_test_section = float(namespace["compute_power_uncertainty"](optimum_row["q_test_section_w"]))
    d_q_cooler = float(namespace["compute_Q_cooler_uncertainty"](namespace["EXPERIMENTAL_CASES"][case_name]))
    d_q_passive = abs(high_row["q_passive_w"] - low_row["q_passive_w"]) / 2.0
    d_q_fins = abs(high_row["q_fins_w"] - low_row["q_fins_w"]) / 2.0
    d_q_model = math.sqrt(d_q_passive ** 2 + d_q_fins ** 2)
    d_q_unaccounted = math.sqrt(d_q_heater ** 2 + d_q_test_section ** 2 + d_q_cooler ** 2 + d_q_model ** 2)

    return {
        "d_q_heater_w": d_q_heater,
        "d_q_test_section_w": d_q_test_section,
        "d_q_cooler_w": d_q_cooler,
        "d_q_passive_w": d_q_passive,
        "d_q_fins_w": d_q_fins,
        "d_q_model_w": d_q_model,
        "d_q_unaccounted_w": d_q_unaccounted,
    }


def append_unique_trace_row(rows: list[dict[str, Any]], row: dict[str, Any]) -> list[dict[str, Any]]:
    thickness = row["thickness_in"]
    if any(abs(existing["thickness_in"] - thickness) <= 1.0e-6 for existing in rows):
        return rows
    rows.append(row)
    return sorted(rows, key=lambda item: item["thickness_in"])


def level_crossing(rows: list[dict[str, Any]], target: float) -> float:
    for left, right in zip(rows, rows[1:]):
        y_left = left["q_unaccounted_w"] - target
        y_right = right["q_unaccounted_w"] - target
        if abs(y_left) <= EPS:
            return left["thickness_in"]
        if y_left * y_right < 0.0 or abs(y_right) <= EPS:
            return interpolate_zero_crossing(left["thickness_in"], y_left, right["thickness_in"], y_right)
    return math.nan


def summarize_case(
    evaluator: EthanEvaluator,
    namespace: dict[str, Any],
    case_name: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    trace_rows = build_trace_rows(evaluator, case_name)
    optimum_row, method = refine_case_optimum(evaluator, case_name, trace_rows)
    uncertainty = estimate_optimum_uncertainty(evaluator, namespace, optimum_row)
    trace_rows = append_unique_trace_row(trace_rows, optimum_row)
    d_q_unaccounted = uncertainty["d_q_unaccounted_w"]
    feasible_min_in = level_crossing(trace_rows, -d_q_unaccounted)
    feasible_max_in = level_crossing(trace_rows, +d_q_unaccounted)

    case_data = namespace["EXPERIMENTAL_CASES"][case_name]
    default_thickness_in = (
        meters_to_inches(float(namespace["insulation_thickness_salt"]))
        if case_name.startswith("Salt")
        else meters_to_inches(float(namespace["insulation_thickness_water"]))
    )
    default_row = evaluator.evaluate(case_name, default_thickness_in)

    summary_row = {
        "case_name": case_name,
        "family": optimum_row["family"],
        "heater_power_w": optimum_row["q_heater_w"],
        "test_section_power_w": optimum_row["q_test_section_w"],
        "cooler_power_reported_w": optimum_row["cooler_power_reported_w"],
        "q_cooler_airside_w": optimum_row["q_cooler_w"],
        "q_expected_loss_w": optimum_row["q_expected_loss_w"],
        "default_thickness_in": default_thickness_in,
        "default_q_unaccounted_w": default_row["q_unaccounted_w"],
        "optimal_thickness_in": optimum_row["thickness_in"],
        "optimal_q_unaccounted_w": optimum_row["q_unaccounted_w"],
        "optimal_q_passive_w": optimum_row["q_passive_w"],
        "optimal_q_fins_w": optimum_row["q_fins_w"],
        "optimal_q_total_loss_w": optimum_row["q_total_loss_w"],
        "optimal_feasible_min_in": feasible_min_in,
        "optimal_feasible_max_in": feasible_max_in,
        "delta_opt_minus_default_in": optimum_row["thickness_in"] - default_thickness_in,
        "d_q_unaccounted_w": d_q_unaccounted,
        "d_q_model_w": uncertainty["d_q_model_w"],
        "d_q_passive_w": uncertainty["d_q_passive_w"],
        "d_q_fins_w": uncertainty["d_q_fins_w"],
        "d_q_cooler_w": uncertainty["d_q_cooler_w"],
        "within_uncertainty": abs(optimum_row["q_unaccounted_w"]) <= d_q_unaccounted,
        "air_inlet_c": optimum_row["air_inlet_c"],
        "air_outlet_c": optimum_row["air_outlet_c"],
        "measured_cooler_power_w": float(case_data["cooler_power_W"]),
        "search_method": method,
    }

    trace_output_rows = []
    for row in trace_rows:
        trace_output_rows.append(
            {
                "case_name": row["case_name"],
                "family": row["family"],
                "thickness_in": row["thickness_in"],
                "q_unaccounted_w": row["q_unaccounted_w"],
                "q_expected_loss_w": row["q_expected_loss_w"],
                "q_total_loss_w": row["q_total_loss_w"],
                "q_passive_w": row["q_passive_w"],
                "q_fins_w": row["q_fins_w"],
                "temperature_offset_c": row["temperature_offset_c"],
            }
        )
    return summary_row, trace_output_rows


def build_family_summary_rows(
    case_rows: list[dict[str, Any]],
    dashboard_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for family in ("salt", "water"):
        family_case_rows = [row for row in case_rows if row["family"] == family]
        family_dashboard_rows = [row for row in dashboard_rows if row["fluid_family"] == family]
        optimums = [float(row["optimal_thickness_in"]) for row in family_case_rows]
        known_three_d = [finite_float(row["three_d_outer_insulation_thickness_in"]) for row in family_dashboard_rows]
        known_three_d = [value for value in known_three_d if math.isfinite(value)]
        mean_optimum = safe_mean(optimums)
        row = {
            "family": family,
            "experimental_case_count": len(family_case_rows),
            "known_three_d_case_count": len(known_three_d),
            "mean_optimum_thickness_in": mean_optimum,
            "median_optimum_thickness_in": median(optimums) if optimums else math.nan,
            "std_optimum_thickness_in": safe_std(optimums),
            "min_optimum_thickness_in": min(optimums) if optimums else math.nan,
            "max_optimum_thickness_in": max(optimums) if optimums else math.nan,
            "recommended_uniform_thickness_in": rounded_recommendation_in(mean_optimum),
            "known_three_d_mean_thickness_in": safe_mean(known_three_d),
            "known_three_d_min_thickness_in": min(known_three_d) if known_three_d else math.nan,
            "known_three_d_max_thickness_in": max(known_three_d) if known_three_d else math.nan,
            "delta_known_three_d_mean_minus_optimum_in": safe_mean(known_three_d) - mean_optimum,
        }
        rows_out.append(row)
    return rows_out


def build_cfd_comparison_rows(
    dashboard_rows: list[dict[str, str]],
    case_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    case_lookup = {row["case_name"]: row for row in case_rows}
    family_lookup = {row["family"]: row for row in family_rows}
    rows_out: list[dict[str, Any]] = []
    for row in dashboard_rows:
        case_name = case_name_from_base_case_id(row["base_case_id"])
        case_summary = case_lookup[case_name]
        family_summary = family_lookup[row["fluid_family"]]
        three_d_thickness_in = finite_float(row["three_d_outer_insulation_thickness_in"])
        variant_label = row.get("variant_label", "")
        if row["fluid_family"] == "salt" and variant_label in {"jin", "kirst"}:
            case_group = "salt_screening"
        elif row["fluid_family"] == "salt":
            case_group = "salt_validation"
        else:
            case_group = "water_validation"
        rows_out.append(
            {
                "source_id": row["source_id"],
                "display_label": row["display_label"],
                "fluid_family": row["fluid_family"],
                "case_group": case_group,
                "base_case_id": row["base_case_id"],
                "variant_label": variant_label,
                "three_d_outer_insulation_thickness_in": three_d_thickness_in,
                "matched_experimental_case_name": case_name,
                "matched_optimal_thickness_in": case_summary["optimal_thickness_in"],
                "matched_feasible_min_in": case_summary["optimal_feasible_min_in"],
                "matched_feasible_max_in": case_summary["optimal_feasible_max_in"],
                "delta_three_d_minus_matched_optimum_in": three_d_thickness_in - case_summary["optimal_thickness_in"],
                "family_recommended_uniform_thickness_in": family_summary["recommended_uniform_thickness_in"],
                "delta_three_d_minus_family_recommended_in": three_d_thickness_in - family_summary["recommended_uniform_thickness_in"],
                "cooler_h_w_m2_k": finite_float(row["cooler_h_W_m2K"]),
                "heater_power_w": finite_float(row["heater_power_W"]),
                "package_root": row["package_root"],
            }
        )
    return rows_out


def plot_q_unaccounted_traces(trace_rows: list[dict[str, Any]], family: str, output_dir: Path) -> None:
    family_rows = [row for row in trace_rows if row["family"] == family]
    if not family_rows:
        return

    ordered_cases = sorted({row["case_name"] for row in family_rows}, key=case_sort_key)
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    for case_name in ordered_cases:
        case_trace = sorted(
            [row for row in family_rows if row["case_name"] == case_name and abs(row["temperature_offset_c"]) <= EPS],
            key=lambda row: row["thickness_in"],
        )
        ax.plot(
            [row["thickness_in"] for row in case_trace],
            [row["q_unaccounted_w"] for row in case_trace],
            marker="o",
            linewidth=1.8,
            markersize=4.0,
            label=case_name,
        )
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Insulation thickness [in]")
    ax.set_ylabel("Q_unaccounted [W]")
    ax.set_title(f"{family.capitalize()} case closure versus insulation thickness")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    save_matplotlib_figure(fig, output_dir, f"{family}_q_unaccounted_vs_thickness")
    plt.close(fig)


def plot_three_d_vs_effective_thickness(cfd_rows: list[dict[str, Any]], output_dir: Path) -> None:
    if not cfd_rows:
        return
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    styles = {
        "salt": {"marker": "o", "color": "#b35c1e"},
        "water": {"marker": "s", "color": "#1f77b4"},
    }
    for family in ("salt", "water"):
        family_rows = [row for row in cfd_rows if row["fluid_family"] == family]
        if not family_rows:
            continue
        ax.scatter(
            [row["matched_optimal_thickness_in"] for row in family_rows],
            [row["three_d_outer_insulation_thickness_in"] for row in family_rows],
            label=family.capitalize(),
            s=38,
            alpha=0.85,
            **styles[family],
        )
    max_extent = max(
        max(row["matched_optimal_thickness_in"] for row in cfd_rows),
        max(row["three_d_outer_insulation_thickness_in"] for row in cfd_rows),
    )
    ax.plot([0.0, max_extent], [0.0, max_extent], linestyle="--", color="black", linewidth=1.0)
    ax.set_xlabel("Matched effective optimum thickness [in]")
    ax.set_ylabel("Known 3D outer insulation thickness [in]")
    ax.set_title("Known 3D thickness versus inferred effective optimum")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    save_matplotlib_figure(fig, output_dir, "three_d_vs_effective_thickness")
    plt.close(fig)


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def build_case_table_rows(case_rows: list[dict[str, Any]], cfd_rows: list[dict[str, Any]]) -> list[list[str]]:
    rows_out: list[list[str]] = []
    for case_row in sorted(case_rows, key=lambda row: case_sort_key(row["case_name"])):
        matched_cfd_rows = [row for row in cfd_rows if row["matched_experimental_case_name"] == case_row["case_name"]]
        matched_cfd_rows = sorted(matched_cfd_rows, key=lambda row: (row["fluid_family"], row["display_label"]))
        current_thickness_payload = [
            f"{row['display_label']} ({fmt(row['three_d_outer_insulation_thickness_in'], 3)} in)"
            for row in matched_cfd_rows
        ]
        rows_out.append(
            [
                case_row["case_name"],
                fmt(case_row["optimal_thickness_in"], 4),
                fmt(case_row["default_thickness_in"], 3),
                "yes" if case_row["within_uncertainty"] else "no",
                "; ".join(current_thickness_payload) if current_thickness_payload else "none",
            ]
        )
    return rows_out


def build_cfd_table_rows(cfd_rows: list[dict[str, Any]]) -> list[list[str]]:
    rows_out: list[list[str]] = []
    ordered_rows = sorted(
        cfd_rows,
        key=lambda row: (
            0 if row["fluid_family"] == "salt" else 1,
            row["matched_experimental_case_name"],
            row["display_label"],
        ),
    )
    for row in ordered_rows:
        rows_out.append(
            [
                row["display_label"],
                row["matched_experimental_case_name"],
                fmt(row["three_d_outer_insulation_thickness_in"], 3),
                fmt(row["matched_optimal_thickness_in"], 4),
                fmt(row["delta_three_d_minus_matched_optimum_in"], 4),
            ]
        )
    return rows_out


def write_case_thickness_tables(
    output_dir: Path,
    case_rows: list[dict[str, Any]],
    cfd_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Case Thickness Tables",
        "",
        "## Solver-optimum thickness by experimental case",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Experimental case", "Solver optimum [in]", "Legacy solver default [in]", "Within uncertainty?", "Current CFD thicknesses"],
            build_case_table_rows(case_rows, cfd_rows),
        )
    )
    lines.extend(["", "## Current CFD thickness by run", ""])
    lines.extend(
        markdown_table(
            ["CFD case", "Matched experimental case", "Current CFD thickness [in]", "Solver optimum [in]", "CFD - optimum [in]"],
            build_cfd_table_rows(cfd_rows),
        )
    )
    (output_dir / "case_thickness_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(
    output_dir: Path,
    case_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    cfd_rows: list[dict[str, Any]],
) -> None:
    salt_family = next(row for row in family_rows if row["family"] == "salt")
    water_family = next(row for row in family_rows if row["family"] == "water")
    salt_screening_count = sum(1 for row in cfd_rows if row["case_group"] == "salt_screening")
    salt_validation_count = sum(1 for row in cfd_rows if row["case_group"] == "salt_validation")
    water_validation_count = sum(1 for row in cfd_rows if row["case_group"] == "water_validation")

    lines = [
        "# Ethan Insulation Optimizer Package",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Purpose",
        "",
        "This package uses the read-only Ethan wall-loss model to infer the effective insulation thickness that drives",
        "`Q_unaccounted = Q_heater + Q_test_section - Q_cooler(air-side) - Q_total_loss` toward zero for each experimental",
        "Salt and Water case. It then compares those inferred effective thicknesses against the known outer insulation",
        "thicknesses already recorded for the 3D CFD cases in the June 17 nondimensional dashboard package.",
        "",
        "## Method boundary",
        "",
        "- The optimizer reuses `../cfd-modeling-tools/tamu_first_order_model/Ethan_wall_and_heat_losses/first_order_model_tamu_loop.py` as-is.",
        "- The cooler term is still the measured air-side enthalpy balance from Ethan's model, not a predictive cooler HTC closure.",
        "- The reported optimum is an effective thickness for the measured-state heat-loss model. It is not, by itself, a validated redesign recommendation for a new geometry or a new ambient closure model.",
        "",
        "## Current state",
        "",
        f"- experimental cases optimized: `{len(case_rows)}`",
        f"- known salt screening CFD cases quantified: `{salt_screening_count}`",
        f"- known salt validation CFD cases compared: `{salt_validation_count}`",
        f"- known water CFD cases compared: `{water_validation_count}`",
        "",
        "## Family summary",
        "",
        f"- Salt effective mean optimum: `{fmt(salt_family['mean_optimum_thickness_in'], 3)}` in",
        f"- Salt recommended uniform thickness: `{fmt(salt_family['recommended_uniform_thickness_in'], 2)}` in",
        f"- Salt known 3D mean thickness: `{fmt(salt_family['known_three_d_mean_thickness_in'], 3)}` in",
        f"- Water effective mean optimum: `{fmt(water_family['mean_optimum_thickness_in'], 3)}` in",
        f"- Water recommended uniform thickness: `{fmt(water_family['recommended_uniform_thickness_in'], 2)}` in",
        f"- Water known 3D mean thickness: `{fmt(water_family['known_three_d_mean_thickness_in'], 3)}` in",
        "",
        "## Case-by-case thickness tables",
        "",
        "The report now includes explicit case tables in `case_thickness_tables.md`.",
        "",
        "### Solver optimum by experimental case",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Experimental case", "Solver optimum [in]", "Legacy solver default [in]", "Within uncertainty?", "Current CFD thicknesses"],
            build_case_table_rows(case_rows, cfd_rows),
        )
    )
    lines.extend(
        [
            "",
            "### Current CFD thickness by run",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["CFD case", "Matched experimental case", "Current CFD thickness [in]", "Solver optimum [in]", "CFD - optimum [in]"],
            build_cfd_table_rows(cfd_rows),
        )
    )
    lines.extend(
        [
            "",
        "## Interpretation boundary",
        "",
        "Read `thickness_scientific_analysis.md` before using these numbers in a redesign or paper claim. That note explains",
        "which conclusions are directly supported by the effective-thickness fit, which conclusions only compare against the",
        "current 3D setup choices, and which questions still belong to the coupled 1D fluid model or to new CFD runs.",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_scientific_analysis(
    output_dir: Path,
    case_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    cfd_rows: list[dict[str, Any]],
) -> None:
    salt_family = next(row for row in family_rows if row["family"] == "salt")
    water_family = next(row for row in family_rows if row["family"] == "water")
    salt_1_row = next(row for row in case_rows if row["case_name"] == "Salt 1")
    salt_screening_rows = [row for row in cfd_rows if row["case_group"] == "salt_screening"]
    salt_validation_rows = [row for row in cfd_rows if row["case_group"] == "salt_validation"]
    water_rows = [row for row in cfd_rows if row["case_group"] == "water_validation"]

    salt_deltas = [row["delta_three_d_minus_matched_optimum_in"] for row in salt_screening_rows]
    water_deltas = [row["delta_three_d_minus_matched_optimum_in"] for row in water_rows]

    lines = [
        "# Scientific Analysis",
        "",
        "## Observed result",
        "",
        f"The Salt-family mean effective optimum is `{fmt(salt_family['mean_optimum_thickness_in'], 3)}` in, with a rounded",
        f"uniform target of `{fmt(salt_family['recommended_uniform_thickness_in'], 2)}` in. The Water-family mean effective",
        f"optimum is `{fmt(water_family['mean_optimum_thickness_in'], 3)}` in, with a rounded uniform target of",
        f"`{fmt(water_family['recommended_uniform_thickness_in'], 2)}` in.",
        "",
        "## Comparison to known 3D cases",
        "",
        f"The known Salt screening CFD runs currently cluster at `{fmt(safe_mean([row['three_d_outer_insulation_thickness_in'] for row in salt_screening_rows]), 3)}` in,",
        f"while the lone Salt validation CFD row sits at `{fmt(safe_mean([row['three_d_outer_insulation_thickness_in'] for row in salt_validation_rows]), 3)}` in. The Water CFD rows",
        f"cluster at `{fmt(safe_mean([row['three_d_outer_insulation_thickness_in'] for row in water_rows]), 3)}` in.",
        "",
        f"Relative to the matched experimental optima, the Salt screening rows differ by a mean of `{fmt(safe_mean(salt_deltas), 3)}` in",
        f"and the Water rows differ by a mean of `{fmt(safe_mean(water_deltas), 3)}` in.",
        "",
        "## Important exception",
        "",
        f"`Salt 1` does not actually close to zero within the scanned thickness band. Its best scanned fit is",
        f"`{fmt(salt_1_row['optimal_thickness_in'], 3)}` in with residual `Q_unaccounted = {fmt(salt_1_row['optimal_q_unaccounted_w'], 2)}` W,",
        "and that residual still sits outside the propagated uncertainty band. This means the family-level Salt target should be read as",
        "a useful effective trend, not as proof that thickness alone explains every Salt thermal-loss mismatch.",
        "",
        "## Interpretation",
        "",
        "The effective-thickness fit is closing a measured-state energy balance, so it should be read as a lumped thermal",
        "surrogate. If the fitted thickness differs from the physical 3D wall setup, the discrepancy can stand in for multiple",
        "unmodeled effects at once: installation compression, contact resistances, fixture leakage, ambient/radiative closure",
        "error, or simplifications in the fin-loss treatment. It is therefore strong evidence about the thermal-loss budget,",
        "but weaker evidence about literal wrap thickness alone.",
        "",
        "## Scope limits",
        "",
        "- This package does not infer a predictive cooler HTC.",
        "- This package does not overwrite the current 3D case setups or claim that a new 3D optimum is proven without reruns.",
        "- The most defensible near-term use is to rank whether the current 3D thickness assumptions are likely low, high, or roughly aligned relative to the wall-loss closure fit.",
    ]
    (output_dir / "thickness_scientific_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_summary_payload(
    output_dir: Path,
    case_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    cfd_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "generated_at": iso_timestamp(),
        "builder_script": "tools/analyze/build_ethan_insulation_optimizer_package.py",
        "ethan_model_file": str(ETHAN_MODEL_FILE),
        "output_dir": str(output_dir),
        "summary": {
            "experimental_case_count": len(case_rows),
            "salt_experimental_case_count": sum(1 for row in case_rows if row["family"] == "salt"),
            "water_experimental_case_count": sum(1 for row in case_rows if row["family"] == "water"),
            "known_cfd_case_count": len(cfd_rows),
            "known_salt_screening_case_count": sum(1 for row in cfd_rows if row["case_group"] == "salt_screening"),
            "known_salt_validation_case_count": sum(1 for row in cfd_rows if row["case_group"] == "salt_validation"),
            "known_water_case_count": sum(1 for row in cfd_rows if row["case_group"] == "water_validation"),
        },
        "family_results": family_rows,
        "artifacts": [
            "README.md",
            "summary.json",
            "case_thickness_tables.md",
            "experimental_case_optima.csv",
            "experimental_thickness_trace.csv",
            "family_optima.csv",
            "all_known_case_thickness_comparison.csv",
            "salt_screening_thickness_quantification.csv",
            "thickness_scientific_analysis.md",
            "figures/png/salt_q_unaccounted_vs_thickness.png",
            "figures/png/water_q_unaccounted_vs_thickness.png",
            "figures/png/three_d_vs_effective_thickness.png",
        ],
    }


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    print(f"[insulation_optimizer] output_dir={output_dir}", flush=True)

    namespace = load_ethan_namespace()
    experimental_case_names = sorted(namespace["EXPERIMENTAL_CASES"].keys(), key=case_sort_key)

    dashboard_rows = load_csv_rows(SALT_DASHBOARD) + load_csv_rows(WATER_DASHBOARD)
    selected_case_names = set(args.case_names or [])
    if args.source_ids:
        source_ids = set(args.source_ids)
        for row in dashboard_rows:
            if row["source_id"] in source_ids:
                selected_case_names.add(case_name_from_base_case_id(row["base_case_id"]))
    if selected_case_names:
        experimental_case_names = [name for name in experimental_case_names if name in selected_case_names]
        dashboard_rows = [
            row for row in dashboard_rows if case_name_from_base_case_id(row["base_case_id"]) in selected_case_names
        ]

    evaluator = EthanEvaluator(namespace)
    case_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    for case_name in experimental_case_names:
        print(f"[insulation_optimizer] solving {case_name}", flush=True)
        case_row, case_trace = summarize_case(evaluator, namespace, case_name)
        print(
            "[insulation_optimizer] solved"
            f" case={case_name}"
            f" optimum_in={case_row['optimal_thickness_in']:.4f}"
            f" q_unaccounted_w={case_row['optimal_q_unaccounted_w']:.4f}",
            flush=True,
        )
        case_rows.append(case_row)
        trace_rows.extend(case_trace)

    family_rows = build_family_summary_rows(case_rows, dashboard_rows)
    cfd_rows = build_cfd_comparison_rows(dashboard_rows, case_rows, family_rows)
    salt_screening_rows = [row for row in cfd_rows if row["case_group"] == "salt_screening"]

    csv_dump(
        output_dir / "experimental_case_optima.csv",
        [
            "case_name",
            "family",
            "heater_power_w",
            "test_section_power_w",
            "cooler_power_reported_w",
            "q_cooler_airside_w",
            "q_expected_loss_w",
            "default_thickness_in",
            "default_q_unaccounted_w",
            "optimal_thickness_in",
            "optimal_q_unaccounted_w",
            "optimal_q_passive_w",
            "optimal_q_fins_w",
            "optimal_q_total_loss_w",
            "optimal_feasible_min_in",
            "optimal_feasible_max_in",
            "delta_opt_minus_default_in",
            "d_q_unaccounted_w",
            "d_q_model_w",
            "d_q_passive_w",
            "d_q_fins_w",
            "d_q_cooler_w",
            "within_uncertainty",
            "air_inlet_c",
            "air_outlet_c",
            "measured_cooler_power_w",
            "search_method",
        ],
        case_rows,
    )
    csv_dump(
        output_dir / "experimental_thickness_trace.csv",
        [
            "case_name",
            "family",
            "thickness_in",
            "q_unaccounted_w",
            "q_expected_loss_w",
            "q_total_loss_w",
            "q_passive_w",
            "q_fins_w",
            "temperature_offset_c",
        ],
        trace_rows,
    )
    csv_dump(
        output_dir / "family_optima.csv",
        [
            "family",
            "experimental_case_count",
            "known_three_d_case_count",
            "mean_optimum_thickness_in",
            "median_optimum_thickness_in",
            "std_optimum_thickness_in",
            "min_optimum_thickness_in",
            "max_optimum_thickness_in",
            "recommended_uniform_thickness_in",
            "known_three_d_mean_thickness_in",
            "known_three_d_min_thickness_in",
            "known_three_d_max_thickness_in",
            "delta_known_three_d_mean_minus_optimum_in",
        ],
        family_rows,
    )
    csv_dump(
        output_dir / "all_known_case_thickness_comparison.csv",
        [
            "source_id",
            "display_label",
            "fluid_family",
            "case_group",
            "base_case_id",
            "variant_label",
            "three_d_outer_insulation_thickness_in",
            "matched_experimental_case_name",
            "matched_optimal_thickness_in",
            "matched_feasible_min_in",
            "matched_feasible_max_in",
            "delta_three_d_minus_matched_optimum_in",
            "family_recommended_uniform_thickness_in",
            "delta_three_d_minus_family_recommended_in",
            "cooler_h_w_m2_k",
            "heater_power_w",
            "package_root",
        ],
        cfd_rows,
    )
    csv_dump(
        output_dir / "salt_screening_thickness_quantification.csv",
        [
            "source_id",
            "display_label",
            "fluid_family",
            "case_group",
            "base_case_id",
            "variant_label",
            "three_d_outer_insulation_thickness_in",
            "matched_experimental_case_name",
            "matched_optimal_thickness_in",
            "matched_feasible_min_in",
            "matched_feasible_max_in",
            "delta_three_d_minus_matched_optimum_in",
            "family_recommended_uniform_thickness_in",
            "delta_three_d_minus_family_recommended_in",
            "cooler_h_w_m2_k",
            "heater_power_w",
            "package_root",
        ],
        salt_screening_rows,
    )

    plot_q_unaccounted_traces(trace_rows, "salt", output_dir)
    plot_q_unaccounted_traces(trace_rows, "water", output_dir)
    plot_three_d_vs_effective_thickness(cfd_rows, output_dir)

    write_case_thickness_tables(output_dir, case_rows, cfd_rows)
    write_readme(output_dir, case_rows, family_rows, cfd_rows)
    write_scientific_analysis(output_dir, case_rows, family_rows, cfd_rows)

    json_dump(output_dir / "summary.json", build_summary_payload(output_dir, case_rows, family_rows, cfd_rows))
    print(f"[insulation_optimizer] complete output_dir={output_dir}", flush=True)


if __name__ == "__main__":
    main()
