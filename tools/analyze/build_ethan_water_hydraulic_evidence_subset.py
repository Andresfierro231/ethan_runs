#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_water_hydraulic_evidence_subset"
DEFAULT_PACKAGE_ROOT = ROOT / "tmp" / "2026-06-15_live_case_analysis" / "contract_fix_water_family"
DEFAULT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"

WATER_CASES = (
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
)
CASE_LABELS = {
    "val_water_test_1_coarse_mesh_laminar": "Water 1",
    "val_water_test_2_coarse_mesh_laminar": "Water 2",
    "val_water_test_3_coarse_mesh_laminar": "Water 3",
    "val_water_test_4_coarse_mesh_laminar": "Water 4",
}
EXCLUDED_LEFT_LOWER = {"val_water_test_1_coarse_mesh_laminar", "val_water_test_2_coarse_mesh_laminar"}
MISSING = {"", "nan", "NaN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Screen the finished Water-family branch hydraulic outputs into a conservative "
            "evidence subset without reopening extraction or campaign generation."
        )
    )
    parser.add_argument("--package-root", default=str(DEFAULT_PACKAGE_ROOT))
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


def is_missing(value: str) -> bool:
    return str(value).strip() in MISSING


def classify_branch(
    branch: str,
    rows: list[dict[str, Any]],
) -> tuple[str, str, str]:
    agree_all = all(int(row["agree_time_count"]) == int(row["time_count"]) for row in rows)
    cum_all = all(int(row["positive_cumulative_time_count"]) == int(row["time_count"]) for row in rows)
    per_case_alignment_clean = all("," not in row["branch_alignment_signature"] for row in rows)
    cases_with_any_negative_mean = sum(int(row["negative_mean_direct_time_count"]) > 0 for row in rows)
    cases_with_any_nonpositive_cum = sum(int(row["nonpositive_cumulative_time_count"]) > 0 for row in rows)

    if branch == "left_lower_leg":
        return (
            "excluded",
            "water_left_lower_leg_resolved_exclusion",
            "Water left_lower_leg remains excluded from usable hydraulic evidence because the direct branch path was closed as exclusion rather than promotion.",
        )
    # Candidate-grade Water hydraulic branches need per-case sign agreement and
    # positive cumulative direct drop throughout the retained window. They do
    # not need one universal loop-orientation sign across different branches;
    # they only need each case to stay internally consistent.
    if branch in {"right_leg", "test_section_span", "upper_leg"} and agree_all and cum_all and per_case_alignment_clean:
        return (
            "water_family_candidate",
            "stable_branch_sign_and_cumulative_drop",
            "This branch is the cleanest Water-family candidate for future family-specific branch pressure interpretation because direct-vs-shear sign agreement and cumulative direct drop stay stable across the screened Water cases.",
        )
    if branch == "lower_leg":
        return (
            "contextual_only",
            "weak_signal_mean_gradient_instability",
            "Lower-leg direct branch means stay positive at the summary level, but one retained-time sign failure in Water 4 indicates weak-signal mean-gradient instability. Keep it contextual unless a cumulative-drop-based reduction is adopted.",
        )
    if branch == "left_upper_leg":
        return (
            "contextual_only",
            "one_case_nonpositive_cumulative_direct_drop",
            "Left-upper-leg branch means are sign-consistent, but Water 2 carries one retained time with non-positive cumulative direct p_rgh end drop. Keep it contextual rather than candidate-grade.",
        )
    if not cum_all:
        return (
            "contextual_only",
            "nonpositive_cumulative_direct_drop_present",
            f"{cases_with_any_nonpositive_cum} Water case(s) carry a non-positive cumulative direct branch-end drop in this branch.",
        )
    if cases_with_any_negative_mean > 0:
        return (
            "contextual_only",
            "negative_mean_direct_time_present",
            f"{cases_with_any_negative_mean} Water case(s) carry at least one retained time with a negative mean direct branch gradient.",
        )
    return (
        "excluded",
        "not_stable_enough_for_water_subset",
        "The current Water branch screening does not support promoting this branch into the candidate hydraulic evidence subset.",
    )


def build_case_branch_screen(package_root: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for case_id in WATER_CASES:
        package_dir = package_root / case_id
        summary_path = package_dir / "major_loss_summary.csv"
        timeseries_path = package_dir / "major_loss_cumulative_timeseries.csv"
        require_exists(summary_path)
        require_exists(timeseries_path)
        summary_rows = load_csv_rows(summary_path)
        timeseries_rows = load_csv_rows(timeseries_path)

        by_span_time: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for row in timeseries_rows:
            direct = row.get("dp_major_gradient_direct_prgh_pa_per_m", "")
            shear = row.get("dp_major_gradient_pa_per_m", "")
            if direct in {"", "nan", "NaN"} or shear in {"", "nan", "NaN"}:
                continue
            by_span_time[(row["span_name"], row["time_s"])].append(row)

        for summary in summary_rows:
            span = summary["span_name"]
            time_keys = sorted({time_s for (span_name, time_s) in by_span_time if span_name == span}, key=float)
            if not time_keys:
                continue
            agree_time_count = 0
            positive_cumulative_time_count = 0
            negative_mean_direct_time_count = 0
            nonpositive_cumulative_time_count = 0
            branch_alignment_modes: list[str] = []
            direct_to_shear_ratios: list[float] = []
            terminal_direct_values: list[float] = []
            for time_s in time_keys:
                rows = sorted(by_span_time[(span, time_s)], key=lambda row: int(row["bin_index"]))
                mean_direct = sum(float(row["dp_major_gradient_direct_prgh_pa_per_m"]) for row in rows) / len(rows)
                mean_shear = sum(float(row["dp_major_gradient_pa_per_m"]) for row in rows) / len(rows)
                cumulative_end = float(rows[-1]["cumulative_dp_major_direct_prgh_pa"])
                direct_to_shear_ratios.append(abs(mean_direct) / max(abs(mean_shear), 1.0e-12))
                terminal_direct_values.append(cumulative_end)
                if mean_direct * mean_shear > 0.0:
                    agree_time_count += 1
                if mean_direct < 0.0:
                    negative_mean_direct_time_count += 1
                if cumulative_end > 0.0:
                    positive_cumulative_time_count += 1
                else:
                    nonpositive_cumulative_time_count += 1
                branch_alignment_modes.append(",".join(sorted({row["flow_alignment_sign"] for row in rows})))

            raw_summary_terminal_direct = str(summary["mean_terminal_dp_major_direct_prgh_pa"])
            if is_missing(raw_summary_terminal_direct):
                published_terminal_direct = f"{sum(terminal_direct_values) / len(terminal_direct_values):.12f}"
                terminal_direct_source = "timeseries_mean_fallback"
            else:
                published_terminal_direct = raw_summary_terminal_direct
                terminal_direct_source = "summary_mean"

            output.append(
                {
                    "family": "water",
                    "case_id": case_id,
                    "case_label": CASE_LABELS[case_id],
                    "branch": span,
                    "time_count": len(time_keys),
                    "agree_time_count": agree_time_count,
                    "negative_mean_direct_time_count": negative_mean_direct_time_count,
                    "positive_cumulative_time_count": positive_cumulative_time_count,
                    "nonpositive_cumulative_time_count": nonpositive_cumulative_time_count,
                    "branch_alignment_signature": ";".join(sorted(set(branch_alignment_modes))),
                    "mean_shear_gradient_pa_per_m": summary["mean_dp_major_gradient_pa_per_m"],
                    "mean_direct_prgh_gradient_pa_per_m": summary["mean_dp_major_gradient_direct_prgh_pa_per_m"],
                    "direct_to_shear_ratio_mean": f"{sum(direct_to_shear_ratios) / len(direct_to_shear_ratios):.12f}",
                    "terminal_direct_prgh_drop_pa": published_terminal_direct,
                    "raw_summary_terminal_direct_prgh_drop_pa": raw_summary_terminal_direct,
                    "terminal_direct_prgh_drop_source": terminal_direct_source,
                    "terminal_shear_drop_pa": summary["mean_terminal_dp_major_pa"],
                    "direct_support_fraction": f"{int(summary['direct_prgh_valid_bin_count']) / max(int(summary['valid_bin_count']), 1):.12f}",
                    "source_summary_path": relative_path(summary_path),
                    "source_timeseries_path": relative_path(timeseries_path),
                }
            )
    return output


def build_family_subset(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        by_branch[row["branch"]].append(row)

    output: list[dict[str, Any]] = []
    for branch, rows in sorted(by_branch.items()):
        classification, reason_code, explanation = classify_branch(branch, rows)
        output.append(
            {
                "family": "water",
                "branch": branch,
                "classification": classification,
                "reason_code": reason_code,
                "recommended_use": (
                    "family_specific_candidate"
                    if classification == "water_family_candidate"
                    else ("contextual_only" if classification == "contextual_only" else "excluded")
                ),
                "case_count": len(rows),
                "case_labels": ", ".join(row["case_label"] for row in rows),
                "agree_time_fraction_min": f"{min(int(row['agree_time_count']) / max(int(row['time_count']), 1) for row in rows):.12f}",
                "positive_cumulative_fraction_min": f"{min(int(row['positive_cumulative_time_count']) / max(int(row['time_count']), 1) for row in rows):.12f}",
                "direct_support_fraction_min": f"{min(float(row['direct_support_fraction']) for row in rows):.12f}",
                "source_summary_paths": " | ".join(row["source_summary_path"] for row in rows),
                "source_timeseries_paths": " | ".join(row["source_timeseries_path"] for row in rows),
                "explanation": explanation,
            }
        )
    return output


def build_cross_family_guardrails(family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in family_rows:
        branch = row["branch"]
        classification = row["classification"]
        if classification == "water_family_candidate":
            status = "water_only_candidate"
            caveat = "Candidate for Water-family hydraulic interpretation only; do not assume Salt cross-family promotion without a separate Salt-side branch screen."
        elif classification == "contextual_only":
            status = "contextual_only"
            caveat = "Not stable enough for Water-family branch-pressure dependency work."
        else:
            status = "excluded"
            caveat = "Excluded from Water-family hydraulic evidence."
        rows.append(
            {
                "branch": branch,
                "status": status,
                "required_caveat": caveat,
                "cross_family_ready": "no",
            }
        )
    return rows


def build_readme(
    args: argparse.Namespace,
    case_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> str:
    candidates = [row["branch"] for row in family_rows if row["classification"] == "water_family_candidate"]
    contextual = [row["branch"] for row in family_rows if row["classification"] == "contextual_only"]
    excluded = [row["branch"] for row in family_rows if row["classification"] == "excluded"]
    return f"""# Water Hydraulic Evidence Subset

Generated: `{iso_timestamp()}`

## Purpose

This package defines a conservative Water-family hydraulic evidence subset
using only existing June 15 and June 18 transport outputs. It does not reopen
extraction, rebuild campaign figures, or try to rescue excluded left-lower-leg
rows. Its job is to identify which non-excluded Water branches are stable
enough for future family-specific branch-pressure interpretation.

## Inputs Used

- Water case packages under `{relative_path(Path(args.package_root))}`
- Interpretation closure package `{relative_path(Path(args.closure_dir))}`

## Candidate Water Hydraulic Branches

- `{", ".join(candidates) if candidates else "none"}`

These branches keep positive shear/direct branch means, positive branch-end
cumulative direct `p_rgh` drop, and stable per-case alignment signatures
through the current Water retained windows.

## Contextual-Only Water Hydraulic Branches

- `{", ".join(contextual) if contextual else "none"}`

These branches are not excluded because of the same failure mode as
`left_lower_leg`, but they are still not stable enough for Water-family branch
pressure dependencies.

## Excluded Water Hydraulic Branches

- `{", ".join(excluded) if excluded else "none"}`

`left_lower_leg` remains excluded by the June 18 interpretation closure.

## Cross-Family Boundary

No branch in this package is promoted directly to cross-family hydraulic use.
The point of this subset is to move future Water-family hydraulic work off the
excluded `left_lower_leg` branch and onto a cleaner Water-only evidence set.

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_water_hydraulic_evidence_subset.py`
- `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir tmp/2026-06-18_ethan_water_hydraulic_evidence_subset_smoke`
- `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir reports/2026-06-18_ethan_water_hydraulic_evidence_subset`
"""


def validate_outputs(
    output_dir: Path,
    family_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> None:
    required = (
        output_dir / "README.md",
        output_dir / "summary.json",
        output_dir / "water_hydraulic_case_branch_screen.csv",
        output_dir / "water_hydraulic_family_subset.csv",
        output_dir / "water_hydraulic_cross_family_guardrails.csv",
    )
    for path in required:
        require_exists(path)
        if path.suffix in {".md", ".json"} and path.stat().st_size == 0:
            raise RuntimeError(f"Unexpected empty output file: {path}")

    family_lookup = {row["branch"]: row for row in family_rows}
    if family_lookup["left_lower_leg"]["classification"] != "excluded":
        raise RuntimeError("left_lower_leg must stay excluded in the Water hydraulic subset package.")
    if family_lookup["right_leg"]["classification"] != "water_family_candidate":
        raise RuntimeError("right_leg should be a Water-family hydraulic candidate in the current screen.")
    if family_lookup["test_section_span"]["classification"] != "water_family_candidate":
        raise RuntimeError("test_section_span should be a Water-family hydraulic candidate in the current screen.")
    if any(row["cross_family_ready"] != "no" for row in guardrail_rows):
        raise RuntimeError("No Water hydraulic subset branch should be promoted directly to cross-family readiness.")


def main() -> None:
    args = parse_args()
    package_root = Path(args.package_root).resolve()
    closure_dir = Path(args.closure_dir).resolve()
    require_exists(package_root)
    require_exists(closure_dir / "contradiction_resolution_rows.csv")

    output_dir = ensure_dir(Path(args.output_dir).resolve())
    case_rows = build_case_branch_screen(package_root)
    family_rows = build_family_subset(case_rows)
    guardrail_rows = build_cross_family_guardrails(family_rows)

    csv_dump(
        output_dir / "water_hydraulic_case_branch_screen.csv",
        [
            "family",
            "case_id",
            "case_label",
            "branch",
            "time_count",
            "agree_time_count",
            "negative_mean_direct_time_count",
            "positive_cumulative_time_count",
            "nonpositive_cumulative_time_count",
            "branch_alignment_signature",
            "mean_shear_gradient_pa_per_m",
            "mean_direct_prgh_gradient_pa_per_m",
            "direct_to_shear_ratio_mean",
            "terminal_direct_prgh_drop_pa",
            "raw_summary_terminal_direct_prgh_drop_pa",
            "terminal_direct_prgh_drop_source",
            "terminal_shear_drop_pa",
            "direct_support_fraction",
            "source_summary_path",
            "source_timeseries_path",
        ],
        case_rows,
    )
    csv_dump(
        output_dir / "water_hydraulic_family_subset.csv",
        [
            "family",
            "branch",
            "classification",
            "reason_code",
            "recommended_use",
            "case_count",
            "case_labels",
            "agree_time_fraction_min",
            "positive_cumulative_fraction_min",
            "direct_support_fraction_min",
            "source_summary_paths",
            "source_timeseries_paths",
            "explanation",
        ],
        family_rows,
    )
    csv_dump(
        output_dir / "water_hydraulic_cross_family_guardrails.csv",
        ["branch", "status", "required_caveat", "cross_family_ready"],
        guardrail_rows,
    )

    summary = {
        "generated_at": iso_timestamp(),
        "package_name": output_dir.name,
        "case_count": len(WATER_CASES),
        "candidate_branch_count": sum(1 for row in family_rows if row["classification"] == "water_family_candidate"),
        "contextual_branch_count": sum(1 for row in family_rows if row["classification"] == "contextual_only"),
        "excluded_branch_count": sum(1 for row in family_rows if row["classification"] == "excluded"),
        "candidate_branches": [row["branch"] for row in family_rows if row["classification"] == "water_family_candidate"],
        "cross_family_ready_branch_count": 0,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(build_readme(args, case_rows, family_rows, guardrail_rows), encoding="utf-8")

    validate_outputs(output_dir, family_rows, guardrail_rows)


if __name__ == "__main__":
    main()
