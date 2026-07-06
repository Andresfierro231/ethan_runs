#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_hydraulic_evidence_subset"
DEFAULT_SALT_FAMILY_ROOT = ROOT / "tmp" / "2026-06-15_live_case_analysis" / "contract_fix_salt_family"
DEFAULT_SALT2_ROOT = ROOT / "tmp" / "2026-06-15_live_case_analysis" / "contract_fix_salt2"
DEFAULT_WATER_SUBSET_DIR = ROOT / "reports" / "2026-06-18_ethan_water_hydraulic_evidence_subset"
DEFAULT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"

SALT_CASES = (
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
)
CASE_LABELS = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "Salt 1 Jin",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": "Salt 1 Kirst",
    "val_salt_test_2_coarse_mesh_laminar": "Salt 2 val",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "Salt 2 Jin",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": "Salt 2 Kirst",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "Salt 3 Jin",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": "Salt 3 Kirst",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "Salt 4 Jin",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": "Salt 4 Kirst",
}
MISSING = {"", "nan", "NaN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Screen the finished Salt-family branch hydraulic outputs into a conservative "
            "Salt-only evidence subset and identify overlap with the current Water subset "
            "without reopening extraction or campaign generation."
        )
    )
    parser.add_argument("--salt-family-root", default=str(DEFAULT_SALT_FAMILY_ROOT))
    parser.add_argument("--salt2-root", default=str(DEFAULT_SALT2_ROOT))
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


def load_case_package_dirs(salt_family_root: Path, salt2_root: Path) -> list[Path]:
    case_dirs: list[Path] = []
    for case_id in SALT_CASES:
        root = salt2_root if "salt_test_2" in case_id or case_id.startswith("val_salt_test_2") else salt_family_root
        case_dir = root / case_id
        require_exists(case_dir / "major_loss_summary.csv")
        require_exists(case_dir / "major_loss_cumulative_timeseries.csv")
        case_dirs.append(case_dir)
    return case_dirs


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def is_missing(value: str) -> bool:
    return str(value).strip() in MISSING


def classify_branch(rows: list[dict[str, Any]]) -> tuple[str, str, str]:
    agree_all = all(int(row["agree_time_count"]) == int(row["time_count"]) for row in rows)
    cum_all = all(int(row["positive_cumulative_time_count"]) == int(row["time_count"]) for row in rows)
    alignment_clean = all("," not in row["branch_alignment_signature"] for row in rows)
    if agree_all and cum_all and alignment_clean:
        return (
            "salt_family_candidate",
            "stable_sign_and_cumulative_drop",
            "All Salt cases keep direct-vs-shear sign agreement, positive cumulative direct p_rgh branch-end drop, and stable branch alignment signatures through the retained windows.",
        )
    if cum_all:
        return (
            "contextual_only",
            "positive_cumulative_drop_but_incomplete_sign_agreement",
            "Salt branch-end cumulative direct drop stays positive, but one or more cases fail full direct-vs-shear sign agreement or stable alignment registration.",
        )
    return (
        "excluded",
        "nonpositive_cumulative_drop_present",
        "At least one Salt case carries a non-positive cumulative direct branch-end drop in this branch, so the branch should not be promoted for Salt-family hydraulic interpretation.",
    )


def build_case_branch_screen(case_dirs: list[Path]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        case_id = case_dir.name
        summary_rows = load_csv_rows(case_dir / "major_loss_summary.csv")
        timeseries_rows = load_csv_rows(case_dir / "major_loss_cumulative_timeseries.csv")

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
            negative_mean_direct_time_count = 0
            positive_cumulative_time_count = 0
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
                    "family": "salt",
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
                    "source_summary_path": relative_path(case_dir / "major_loss_summary.csv"),
                    "source_timeseries_path": relative_path(case_dir / "major_loss_cumulative_timeseries.csv"),
                }
            )
    return output


def build_family_subset(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        by_branch[row["branch"]].append(row)

    output: list[dict[str, Any]] = []
    for branch, rows in sorted(by_branch.items()):
        classification, reason_code, explanation = classify_branch(rows)
        output.append(
            {
                "family": "salt",
                "branch": branch,
                "classification": classification,
                "reason_code": reason_code,
                "recommended_use": (
                    "family_specific_candidate"
                    if classification == "salt_family_candidate"
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


def build_overlap_with_water(
    salt_rows: list[dict[str, Any]],
    water_rows: list[dict[str, Any]],
    closure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    water_by_branch = {row["branch"]: row for row in water_rows}
    closure_by_claim = {row["claim_id"]: row for row in closure_rows}
    cross_family_status = closure_by_claim.get("X01", {}).get("status", "unknown")

    output: list[dict[str, Any]] = []
    for row in salt_rows:
        water_row = water_by_branch.get(row["branch"], {})
        water_classification = str(water_row.get("classification", "not_screened"))
        if water_classification == "water_family_candidate":
            overlap_status = "shared_clean_branch_but_cross_family_guarded"
            recommended_use = "shared_candidate_not_cross_family_ready"
            explanation = (
                "This branch is clean in both Salt and Water branch screens, but the June 18 "
                "closure package still blocks direct cross-family hydraulic promotion."
            )
        elif water_classification == "contextual_only":
            overlap_status = "salt_clean_water_contextual"
            recommended_use = "salt_only_candidate"
            explanation = (
                "Salt branch behavior is clean, but the current Water screen only supports "
                "contextual use for the same branch."
            )
        else:
            overlap_status = "salt_clean_water_excluded_or_unavailable"
            recommended_use = "salt_only_candidate"
            explanation = (
                "Salt branch behavior is clean, but the current Water evidence subset excludes "
                "or does not promote the same branch."
            )
        output.append(
            {
                "branch": row["branch"],
                "salt_classification": row["classification"],
                "water_classification": water_classification,
                "overlap_status": overlap_status,
                "recommended_use": recommended_use,
                "cross_family_ready": "no",
                "cross_family_guardrail": cross_family_status,
                "required_caveat": "Do not use this overlap row alone to justify cross-family hydraulic fitting.",
                "explanation": explanation,
            }
        )
    return output


def build_readme(
    case_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    overlap_rows: list[dict[str, Any]],
    closure_dir: Path,
    water_subset_dir: Path,
) -> str:
    candidates = [row["branch"] for row in family_rows if row["classification"] == "salt_family_candidate"]
    contextual = [row["branch"] for row in family_rows if row["classification"] == "contextual_only"]
    excluded = [row["branch"] for row in family_rows if row["classification"] == "excluded"]
    overlap_candidates = [row["branch"] for row in overlap_rows if row["overlap_status"] == "shared_clean_branch_but_cross_family_guarded"]

    lines = [
        "# Salt Hydraulic Evidence Subset",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Purpose",
        "",
        "This package defines a conservative Salt-family hydraulic evidence subset",
        "using only existing June 15 and June 18 transport outputs. It does not",
        "reopen extraction, rebuild campaign figures, or loosen the cross-family",
        "closure gate. Its job is to identify which Salt branches are clean enough",
        "for Salt-family branch-pressure interpretation and which of those branches",
        "overlap with the current Water candidate subset without overclaiming",
        "cross-family readiness.",
        "",
        "## Inputs Used",
        "",
        f"- Salt case packages under `{relative_path(DEFAULT_SALT_FAMILY_ROOT)}` and `{relative_path(DEFAULT_SALT2_ROOT)}`",
        f"- Water hydraulic subset `{relative_path(water_subset_dir / 'README.md')}`",
        f"- Interpretation closure package `{relative_path(closure_dir / 'README.md')}`",
        "",
        "## Candidate Salt Hydraulic Branches",
        "",
        f"- `{', '.join(candidates)}`" if candidates else "- none",
        "",
        "These branches keep positive shear/direct branch means, positive branch-end",
        "cumulative direct `p_rgh` drop, and stable per-case alignment signatures",
        "through the current Salt retained windows.",
        "",
        "## Shared Salt/Water Candidate Overlap",
        "",
        f"- `{', '.join(overlap_candidates)}`" if overlap_candidates else "- none",
        "",
        "These overlap branches are clean in both family screens, but they remain",
        "guarded from direct cross-family hydraulic fitting by the June 18 closure",
        "package.",
        "",
        "## Contextual-Only Salt Hydraulic Branches",
        "",
        f"- `{', '.join(contextual)}`" if contextual else "- none",
        "",
        "## Excluded Salt Hydraulic Branches",
        "",
        f"- `{', '.join(excluded)}`" if excluded else "- none",
        "",
        "## Cross-Family Boundary",
        "",
        "No branch in this package is promoted directly to cross-family hydraulic use.",
        "The overlap screen is meant to show where future cross-family work could start",
        "once the closure gate changes, not to claim that it already has.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    salt_family_root = Path(args.salt_family_root).resolve()
    salt2_root = Path(args.salt2_root).resolve()
    water_subset_dir = Path(args.water_subset_dir).resolve()
    closure_dir = Path(args.closure_dir).resolve()
    output_dir = ensure_dir(Path(args.output_dir).resolve())

    require_exists(water_subset_dir / "water_hydraulic_family_subset.csv")
    require_exists(closure_dir / "cross_family_claims_audit.csv")
    case_dirs = load_case_package_dirs(salt_family_root, salt2_root)
    case_rows = build_case_branch_screen(case_dirs)
    family_rows = build_family_subset(case_rows)
    water_rows = load_csv_rows(water_subset_dir / "water_hydraulic_family_subset.csv")
    closure_rows = load_csv_rows(closure_dir / "cross_family_claims_audit.csv")
    overlap_rows = build_overlap_with_water(family_rows, water_rows, closure_rows)

    csv_dump(
        output_dir / "salt_hydraulic_case_branch_screen.csv",
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
        output_dir / "salt_hydraulic_family_subset.csv",
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
        output_dir / "salt_hydraulic_overlap_with_water.csv",
        [
            "branch",
            "salt_classification",
            "water_classification",
            "overlap_status",
            "recommended_use",
            "cross_family_ready",
            "cross_family_guardrail",
            "required_caveat",
            "explanation",
        ],
        overlap_rows,
    )
    (output_dir / "README.md").write_text(
        build_readme(case_rows, family_rows, overlap_rows, closure_dir, water_subset_dir),
        encoding="utf-8",
    )

    candidate_branches = [row["branch"] for row in family_rows if row["classification"] == "salt_family_candidate"]
    overlap_branches = [row["branch"] for row in overlap_rows if row["overlap_status"] == "shared_clean_branch_but_cross_family_guarded"]
    summary = {
        "generated_at": iso_timestamp(),
        "inputs": {
            "salt_family_root": relative_path(salt_family_root),
            "salt2_root": relative_path(salt2_root),
            "water_subset_dir": relative_path(water_subset_dir),
            "closure_dir": relative_path(closure_dir),
        },
        "candidate_branch_count": len(candidate_branches),
        "contextual_branch_count": sum(1 for row in family_rows if row["classification"] == "contextual_only"),
        "excluded_branch_count": sum(1 for row in family_rows if row["classification"] == "excluded"),
        "shared_overlap_branch_count": len(overlap_branches),
        "candidate_branches": candidate_branches,
        "shared_overlap_branches": overlap_branches,
        "artifacts": {
            "salt_hydraulic_case_branch_screen_csv": str(output_dir / "salt_hydraulic_case_branch_screen.csv"),
            "salt_hydraulic_family_subset_csv": str(output_dir / "salt_hydraulic_family_subset.csv"),
            "salt_hydraulic_overlap_with_water_csv": str(output_dir / "salt_hydraulic_overlap_with_water.csv"),
        },
        "remaining_boundary": [
            "No Salt branch is blocked at the current family-only screen, but overlap with Water does not by itself authorize cross-family hydraulic fitting.",
            "Shared clean branches are limited to the intersection with the Water candidate subset: right_leg, test_section_span, and upper_leg.",
            "Cross-family hydraulics remain guarded by the June 18 interpretation closure package.",
        ],
    }
    json_dump(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
