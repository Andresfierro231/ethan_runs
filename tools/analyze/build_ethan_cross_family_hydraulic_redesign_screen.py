#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_cross_family_hydraulic_redesign_screen"
DEFAULT_SALT_SUBSET_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_hydraulic_evidence_subset"
DEFAULT_WATER_SUBSET_DIR = ROOT / "reports" / "2026-06-18_ethan_water_hydraulic_evidence_subset"
DEFAULT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"

MISSING = {"", "nan", "NaN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the shared clean Salt/Water hydraulic overlap branches and decide whether "
            "future direct branch reduction work should prefer cumulative direct p_rgh branch-end "
            "drop over the current branch-mean direct gradient path."
        )
    )
    parser.add_argument("--salt-subset-dir", default=str(DEFAULT_SALT_SUBSET_DIR))
    parser.add_argument("--water-subset-dir", default=str(DEFAULT_WATER_SUBSET_DIR))
    parser.add_argument("--closure-dir", default=str(DEFAULT_CLOSURE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def require_exists(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Required input is missing: {path}")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def rel_cv(values: list[float]) -> float:
    if not values:
        return math.nan
    mean_value = statistics.fmean(values)
    if abs(mean_value) <= 1.0e-12:
        return math.inf
    return statistics.pstdev(values) / abs(mean_value)


def preferred_observable(
    gradient_positive_fraction: float,
    cumulative_positive_fraction: float,
    gradient_cv: float,
    cumulative_cv: float,
) -> tuple[str, str]:
    if cumulative_positive_fraction < 1.0:
        return (
            "not_ready_for_direct_redesign",
            "Cumulative direct branch-end drop is not strictly positive across retained times, so it cannot be promoted as the preferred future direct observable.",
        )
    if gradient_positive_fraction < 1.0:
        return (
            "cumulative_end_drop_preferred",
            "Cumulative direct branch-end drop stays positive while the branch-mean direct gradient changes sign across retained times.",
        )
    if math.isfinite(cumulative_cv) and math.isfinite(gradient_cv):
        if cumulative_cv <= 0.90 * gradient_cv:
            return (
                "cumulative_end_drop_preferred",
                "Cumulative direct branch-end drop is materially less noisy than the branch-mean direct gradient on this case/branch pair.",
            )
        if gradient_cv <= 0.90 * cumulative_cv:
            return (
                "mean_direct_gradient_preferred",
                "The branch-mean direct gradient is materially less noisy than the cumulative branch-end direct drop on this case/branch pair.",
            )
    return (
        "no_clear_advantage",
        "Both direct observables are sign-clean on this case/branch pair, but neither has a decisive retained-time stability advantage.",
    )


def load_shared_overlap_branches(salt_subset_dir: Path) -> list[str]:
    rows = load_csv_rows(salt_subset_dir / "salt_hydraulic_overlap_with_water.csv")
    return [
        str(row["branch"])
        for row in rows
        if str(row["overlap_status"]) == "shared_clean_branch_but_cross_family_guarded"
    ]


def compute_case_time_rows(
    family: str,
    case_rows: list[dict[str, str]],
    shared_branches: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_time_rows: list[dict[str, Any]] = []
    per_case_rows: list[dict[str, Any]] = []
    for summary_row in case_rows:
        branch = str(summary_row["branch"])
        if branch not in shared_branches:
            continue
        timeseries_path = ROOT / str(summary_row["source_timeseries_path"])
        require_exists(timeseries_path)
        timeseries_rows = load_csv_rows(timeseries_path)
        by_time: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in timeseries_rows:
            if str(row["span_name"]) != branch:
                continue
            direct = row.get("dp_major_gradient_direct_prgh_pa_per_m", "")
            shear = row.get("dp_major_gradient_pa_per_m", "")
            cumulative_direct = row.get("cumulative_dp_major_direct_prgh_pa", "")
            cumulative_shear = row.get("cumulative_dp_major_pa", "")
            if direct in MISSING or shear in MISSING or cumulative_direct in MISSING or cumulative_shear in MISSING:
                continue
            by_time[str(row["time_s"])].append(row)

        mean_direct_values: list[float] = []
        terminal_direct_values: list[float] = []
        gradient_positive_count = 0
        cumulative_positive_count = 0
        for time_s, rows in sorted(by_time.items(), key=lambda item: float(item[0])):
            rows = sorted(rows, key=lambda row: int(row["bin_index"]))
            mean_direct = sum(float(row["dp_major_gradient_direct_prgh_pa_per_m"]) for row in rows) / len(rows)
            mean_shear = sum(float(row["dp_major_gradient_pa_per_m"]) for row in rows) / len(rows)
            terminal_direct = float(rows[-1]["cumulative_dp_major_direct_prgh_pa"])
            terminal_shear = float(rows[-1]["cumulative_dp_major_pa"])
            mean_direct_values.append(mean_direct)
            terminal_direct_values.append(terminal_direct)
            if mean_direct > 0.0:
                gradient_positive_count += 1
            if terminal_direct > 0.0:
                cumulative_positive_count += 1
            per_time_rows.append(
                {
                    "family": family,
                    "case_id": summary_row["case_id"],
                    "case_label": summary_row["case_label"],
                    "branch": branch,
                    "time_s": time_s,
                    "mean_direct_gradient_pa_per_m": f"{mean_direct:.12f}",
                    "mean_shear_gradient_pa_per_m": f"{mean_shear:.12f}",
                    "terminal_direct_drop_pa": f"{terminal_direct:.12f}",
                    "terminal_shear_drop_pa": f"{terminal_shear:.12f}",
                    "gradient_positive": "yes" if mean_direct > 0.0 else "no",
                    "cumulative_positive": "yes" if terminal_direct > 0.0 else "no",
                    "flow_alignment_signature": ",".join(sorted({str(row["flow_alignment_sign"]) for row in rows})),
                    "source_timeseries_path": summary_row["source_timeseries_path"],
                }
            )

        gradient_positive_fraction = gradient_positive_count / max(len(mean_direct_values), 1)
        cumulative_positive_fraction = cumulative_positive_count / max(len(terminal_direct_values), 1)
        gradient_cv = rel_cv(mean_direct_values)
        cumulative_cv = rel_cv(terminal_direct_values)
        preference, explanation = preferred_observable(
            gradient_positive_fraction,
            cumulative_positive_fraction,
            gradient_cv,
            cumulative_cv,
        )
        terminal_direct_summary = str(summary_row["terminal_direct_prgh_drop_pa"])
        terminal_direct_raw_summary = str(summary_row.get("raw_summary_terminal_direct_prgh_drop_pa", terminal_direct_summary))
        terminal_direct_source = str(summary_row.get("terminal_direct_prgh_drop_source", "summary_mean"))
        per_case_rows.append(
            {
                "family": family,
                "case_id": summary_row["case_id"],
                "case_label": summary_row["case_label"],
                "branch": branch,
                "time_count": len(mean_direct_values),
                "gradient_positive_fraction": f"{gradient_positive_fraction:.12f}",
                "cumulative_positive_fraction": f"{cumulative_positive_fraction:.12f}",
                "gradient_rel_cv": f"{gradient_cv:.12f}" if math.isfinite(gradient_cv) else "inf",
                "cumulative_rel_cv": f"{cumulative_cv:.12f}" if math.isfinite(cumulative_cv) else "inf",
                "mean_direct_gradient_pa_per_m": f"{statistics.fmean(mean_direct_values):.12f}",
                "mean_terminal_direct_drop_pa": f"{statistics.fmean(terminal_direct_values):.12f}",
                "summary_terminal_direct_drop_pa": terminal_direct_summary,
                "raw_summary_terminal_direct_drop_pa": terminal_direct_raw_summary,
                "summary_terminal_direct_drop_missing": "yes" if terminal_direct_raw_summary in MISSING else "no",
                "terminal_direct_drop_publication_source": terminal_direct_source,
                "preferred_direct_observable": preference,
                "recommended_status": "context_only_redesign_input",
                "explanation": explanation,
                "source_summary_path": summary_row["source_summary_path"],
                "source_timeseries_path": summary_row["source_timeseries_path"],
            }
        )
    return per_time_rows, per_case_rows


def aggregate_family_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family_branch: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        by_family_branch[(str(row["family"]), str(row["branch"]))].append(row)

    output: list[dict[str, Any]] = []
    for (family, branch), rows in sorted(by_family_branch.items()):
        preferences = [str(row["preferred_direct_observable"]) for row in rows]
        output.append(
            {
                "family": family,
                "branch": branch,
                "case_count": len(rows),
                "gradient_positive_fraction_min": f"{min(float(row['gradient_positive_fraction']) for row in rows):.12f}",
                "cumulative_positive_fraction_min": f"{min(float(row['cumulative_positive_fraction']) for row in rows):.12f}",
                "median_gradient_rel_cv": f"{statistics.median(float(row['gradient_rel_cv']) for row in rows):.12f}",
                "median_cumulative_rel_cv": f"{statistics.median(float(row['cumulative_rel_cv']) for row in rows):.12f}",
                "cases_preferring_cumulative": sum(pref == "cumulative_end_drop_preferred" for pref in preferences),
                "cases_preferring_gradient": sum(pref == "mean_direct_gradient_preferred" for pref in preferences),
                "cases_no_clear_advantage": sum(pref == "no_clear_advantage" for pref in preferences),
                "summary_terminal_direct_drop_missing_case_count": sum(str(row["summary_terminal_direct_drop_missing"]) == "yes" for row in rows),
                "timeseries_fallback_case_count": sum(
                    str(row["terminal_direct_drop_publication_source"]) == "timeseries_mean_fallback"
                    for row in rows
                ),
                "source_timeseries_paths": " | ".join(str(row["source_timeseries_path"]) for row in rows),
            }
        )
    return output


def branch_recommendations(
    family_rows: list[dict[str, Any]],
    closure_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_branch: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in family_rows:
        by_branch[str(row["branch"])][str(row["family"])] = row
    cross_family_status = next(
        (
            str(row["status"])
            for row in closure_rows
            if str(row["claim_id"]) == "X01"
        ),
        "unknown",
    )
    output: list[dict[str, Any]] = []
    for branch, family_map in sorted(by_branch.items()):
        salt = family_map.get("salt")
        water = family_map.get("water")
        if not salt or not water:
            continue
        salt_cum = int(salt["cases_preferring_cumulative"])
        salt_grad = int(salt["cases_preferring_gradient"])
        water_cum = int(water["cases_preferring_cumulative"])
        water_grad = int(water["cases_preferring_gradient"])
        raw_summary_gap_present = (
            int(salt["summary_terminal_direct_drop_missing_case_count"]) > 0
            or int(water["summary_terminal_direct_drop_missing_case_count"]) > 0
        )
        timeseries_fallback_present = (
            int(salt["timeseries_fallback_case_count"]) > 0
            or int(water["timeseries_fallback_case_count"]) > 0
        )

        if salt_cum > salt_grad and water_cum > water_grad:
            recommendation = "bounded_cumulative_redesign_candidate"
            explanation = (
                "Both families prefer cumulative direct branch-end drop more often than branch-mean direct gradient on this shared overlap branch. "
                "If future cross-family hydraulic redesign work is attempted, start here."
            )
        elif raw_summary_gap_present and not timeseries_fallback_present:
            recommendation = "timeseries_only_do_not_use_summary_terminal_drop"
            explanation = (
                "The per-time cumulative direct branch-end drop is finite in the timeseries, but the current per-case summary terminal direct drop is missing in one or both families. "
                "Any redesign study on this branch must use the cumulative timeseries directly."
            )
        elif raw_summary_gap_present and timeseries_fallback_present:
            recommendation = "no_clear_redesign_priority"
            explanation = (
                "The raw per-case summary terminal direct drop is missing in one or both families, but the publication path can be repaired from preserved retained-time cumulative direct-drop data. "
                "After using that repaired publication value, the retained-time stability comparison still does not show a decisive cross-family reason to switch to cumulative end drop over the current branch-mean direct gradient path."
            )
        else:
            recommendation = "no_clear_redesign_priority"
            explanation = (
                "This shared overlap branch is sign-clean in both families, but the retained-time stability comparison does not show a decisive advantage for cumulative direct branch-end drop over the current branch-mean direct gradient."
            )

        output.append(
            {
                "branch": branch,
                "salt_cases_preferring_cumulative": salt_cum,
                "salt_cases_preferring_gradient": salt_grad,
                "water_cases_preferring_cumulative": water_cum,
                "water_cases_preferring_gradient": water_grad,
                "salt_median_gradient_rel_cv": salt["median_gradient_rel_cv"],
                "salt_median_cumulative_rel_cv": salt["median_cumulative_rel_cv"],
                "water_median_gradient_rel_cv": water["median_gradient_rel_cv"],
                "water_median_cumulative_rel_cv": water["median_cumulative_rel_cv"],
                "raw_summary_terminal_direct_drop_gap_present": "yes" if raw_summary_gap_present else "no",
                "timeseries_fallback_publication_used": "yes" if timeseries_fallback_present else "no",
                "cross_family_guardrail": cross_family_status,
                "recommendation": recommendation,
                "recommended_use": "guarded_internal_design_note",
                "explanation": explanation,
            }
        )
    return output


def build_readme(
    overlap_branches: list[str],
    family_rows: list[dict[str, Any]],
    recommendation_rows: list[dict[str, Any]],
    closure_dir: Path,
) -> str:
    lines = [
        "# Cross-Family Hydraulic Redesign Screen",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Purpose",
        "",
        "This package does one bounded follow-on analysis on the current shared",
        "Salt/Water hydraulic overlap branches. It does not fit a cross-family model",
        "and it does not reopen extraction. Its only question is whether future direct",
        "branch reduction work should prefer cumulative direct `p_rgh` branch-end drop",
        "over the current branch-mean direct gradient path.",
        "",
        "## Shared Overlap Branches Screened",
        "",
        f"- `{', '.join(overlap_branches)}`" if overlap_branches else "- none",
        "",
        f"- Current closure guardrail: `{relative_path(closure_dir / 'cross_family_claims_audit.csv')}`",
        "",
        "## Observed Outcome",
        "",
    ]
    for row in recommendation_rows:
        lines.append(
            f"- `{row['branch']}` -> `{row['recommendation']}`: {row['explanation']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- This screen does not make any branch cross-family-ready by itself.",
            "- It only identifies where a future redesign of the direct hydraulic observable would have the best evidence base.",
            "- The current closure guardrail still applies even on the shared clean overlap branches.",
            "",
            "## Reproduction Commands",
            "",
            "- `python -m py_compile tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py`",
            "- `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir tmp/2026-06-18_ethan_cross_family_hydraulic_redesign_screen_smoke`",
            "- `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir reports/2026-06-18_ethan_cross_family_hydraulic_redesign_screen`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_guardrails_md(recommendation_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Modeling Guardrails",
        "",
        "- Do not use this package to claim cross-family hydraulic readiness.",
        "- Do not re-admit `left_lower_leg` through overlap reasoning; it remains excluded on the Water side.",
        "- If a future redesign is attempted, start from branch-level cumulative direct branch-end drop and keep the analysis on `right_leg`, `test_section_span`, and `upper_leg` only.",
        "- If `timeseries_fallback_publication_used = yes`, treat the branch-end direct-drop publication path as repaired from preserved retained-time cumulative data rather than from the older per-case summary field alone.",
        "",
        "## Branch Notes",
        "",
    ]
    for row in recommendation_rows:
        lines.append(f"- `{row['branch']}`: {row['recommendation']} -> {row['explanation']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    salt_subset_dir = Path(args.salt_subset_dir).resolve()
    water_subset_dir = Path(args.water_subset_dir).resolve()
    closure_dir = Path(args.closure_dir).resolve()
    output_dir = ensure_dir(Path(args.output_dir).resolve())

    require_exists(salt_subset_dir / "salt_hydraulic_case_branch_screen.csv")
    require_exists(salt_subset_dir / "salt_hydraulic_overlap_with_water.csv")
    require_exists(water_subset_dir / "water_hydraulic_case_branch_screen.csv")
    require_exists(closure_dir / "cross_family_claims_audit.csv")

    overlap_branches = load_shared_overlap_branches(salt_subset_dir)
    shared_branches = set(overlap_branches)
    salt_case_rows = load_csv_rows(salt_subset_dir / "salt_hydraulic_case_branch_screen.csv")
    water_case_rows = load_csv_rows(water_subset_dir / "water_hydraulic_case_branch_screen.csv")
    closure_rows = load_csv_rows(closure_dir / "cross_family_claims_audit.csv")

    salt_time_rows, salt_case_audit_rows = compute_case_time_rows("salt", salt_case_rows, shared_branches)
    water_time_rows, water_case_audit_rows = compute_case_time_rows("water", water_case_rows, shared_branches)
    case_audit_rows = salt_case_audit_rows + water_case_audit_rows
    family_summary_rows = aggregate_family_rows(case_audit_rows)
    recommendation_rows = branch_recommendations(family_summary_rows, closure_rows)

    csv_dump(
        output_dir / "overlap_case_time_audit.csv",
        [
            "family",
            "case_id",
            "case_label",
            "branch",
            "time_s",
            "mean_direct_gradient_pa_per_m",
            "mean_shear_gradient_pa_per_m",
            "terminal_direct_drop_pa",
            "terminal_shear_drop_pa",
            "gradient_positive",
            "cumulative_positive",
            "flow_alignment_signature",
            "source_timeseries_path",
        ],
        salt_time_rows + water_time_rows,
    )
    csv_dump(
        output_dir / "overlap_case_summary.csv",
        [
            "family",
            "case_id",
            "case_label",
            "branch",
            "time_count",
            "gradient_positive_fraction",
            "cumulative_positive_fraction",
            "gradient_rel_cv",
            "cumulative_rel_cv",
            "mean_direct_gradient_pa_per_m",
            "mean_terminal_direct_drop_pa",
            "summary_terminal_direct_drop_pa",
            "raw_summary_terminal_direct_drop_pa",
            "summary_terminal_direct_drop_missing",
            "terminal_direct_drop_publication_source",
            "preferred_direct_observable",
            "recommended_status",
            "explanation",
            "source_summary_path",
            "source_timeseries_path",
        ],
        case_audit_rows,
    )
    csv_dump(
        output_dir / "overlap_family_summary.csv",
        [
            "family",
            "branch",
            "case_count",
            "gradient_positive_fraction_min",
            "cumulative_positive_fraction_min",
            "median_gradient_rel_cv",
            "median_cumulative_rel_cv",
            "cases_preferring_cumulative",
            "cases_preferring_gradient",
            "cases_no_clear_advantage",
            "summary_terminal_direct_drop_missing_case_count",
            "timeseries_fallback_case_count",
            "source_timeseries_paths",
        ],
        family_summary_rows,
    )
    csv_dump(
        output_dir / "direct_reduction_recommendations.csv",
        [
            "branch",
            "salt_cases_preferring_cumulative",
            "salt_cases_preferring_gradient",
            "water_cases_preferring_cumulative",
            "water_cases_preferring_gradient",
            "salt_median_gradient_rel_cv",
            "salt_median_cumulative_rel_cv",
            "water_median_gradient_rel_cv",
            "water_median_cumulative_rel_cv",
            "raw_summary_terminal_direct_drop_gap_present",
            "timeseries_fallback_publication_used",
            "cross_family_guardrail",
            "recommendation",
            "recommended_use",
            "explanation",
        ],
        recommendation_rows,
    )

    (output_dir / "README.md").write_text(
        build_readme(overlap_branches, family_summary_rows, recommendation_rows, closure_dir),
        encoding="utf-8",
    )
    (output_dir / "modeling_guardrails.md").write_text(
        build_guardrails_md(recommendation_rows),
        encoding="utf-8",
    )

    summary = {
        "generated_at": iso_timestamp(),
        "inputs": {
            "salt_subset_dir": relative_path(salt_subset_dir),
            "water_subset_dir": relative_path(water_subset_dir),
            "closure_dir": relative_path(closure_dir),
        },
        "shared_overlap_branches": overlap_branches,
        "branch_count": len(overlap_branches),
        "bounded_cumulative_redesign_candidate_count": sum(
            str(row["recommendation"]) == "bounded_cumulative_redesign_candidate"
            for row in recommendation_rows
        ),
        "timeseries_only_gap_count": sum(
            str(row["raw_summary_terminal_direct_drop_gap_present"]) == "yes"
            for row in recommendation_rows
        ),
        "artifacts": {
            "overlap_case_time_audit_csv": str(output_dir / "overlap_case_time_audit.csv"),
            "overlap_case_summary_csv": str(output_dir / "overlap_case_summary.csv"),
            "overlap_family_summary_csv": str(output_dir / "overlap_family_summary.csv"),
            "direct_reduction_recommendations_csv": str(output_dir / "direct_reduction_recommendations.csv"),
            "modeling_guardrails_md": str(output_dir / "modeling_guardrails.md"),
        },
        "remaining_boundary": [
            "This package does not promote any branch to cross-family hydraulic readiness.",
            "The current closure guardrail still blocks cross-family hydraulic fitting even on shared clean overlap branches.",
            "Any future redesign should start from cumulative direct branch-end drop on the shared overlap branches only.",
        ],
    }
    json_dump(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
