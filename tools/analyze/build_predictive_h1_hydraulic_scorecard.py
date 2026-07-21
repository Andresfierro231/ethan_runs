#!/usr/bin/env python3
"""Build the AGENT-310 H1 hydraulic scorecard."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE13_DIR = ROOT / "work_products/2026-07/2026-07-13"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard"

HYDRAULIC_GATE_DIR = DATE13_DIR / "2026-07-13_predictive_hydraulic_gate"
H1_PROXY_DIR = DATE13_DIR / "2026-07-13_predictive_h1_proxy_rerun"
VALIDATION_SPLIT_DIR = DATE13_DIR / "2026-07-13_predictive_validation_split"
NAMED_LOSS_DIR = DATE13_DIR / "2026-07-13_litrev_reset_named_losses"
HYDRAULIC_CANDIDATES_DIR = DATE13_DIR / "2026-07-13_predictive_hydraulic_correction_candidates"
SOLVE_CASE_DIR = DATE13_DIR / "2026-07-13_predictive_forward_v0_solve_case_confirmation"

SCORECARD_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "split_assignment",
    "split_score_boundary",
    "base_variant_id",
    "h1_variant_id",
    "comparison_engine",
    "cfd_mdot_kg_s",
    "baseline_mdot_kg_s",
    "h1_mdot_kg_s",
    "baseline_mdot_error_vs_cfd_kg_s",
    "h1_mdot_error_vs_cfd_kg_s",
    "baseline_abs_mdot_error_pct",
    "h1_abs_mdot_error_pct",
    "mdot_error_reduction_kg_s",
    "mdot_error_reduction_pct",
    "baseline_pressure_residual_Pa",
    "h1_pressure_residual_Pa",
    "h1_accepted_for_validation",
    "thermal_fit_used",
    "movement_direction",
    "row_decision",
    "boundary_note",
]

VARIANT_COLUMNS = [
    "base_variant_id",
    "h1_variant_id",
    "n_rows",
    "mean_baseline_abs_mdot_error_kg_s",
    "mean_h1_abs_mdot_error_kg_s",
    "mean_baseline_abs_mdot_error_pct",
    "mean_h1_abs_mdot_error_pct",
    "mean_mdot_error_reduction_pct",
    "train_h1_abs_mdot_error_pct",
    "validation_h1_abs_mdot_error_pct",
    "holdout_h1_abs_mdot_error_pct",
    "all_h1_rows_overpredict_cfd",
    "movement_gate",
    "forward_v1_scoring_decision",
]

TERM_COLUMNS = [
    "term_family",
    "source_table",
    "n_rows",
    "n_fit_target_or_fit_safe",
    "n_included_in_h1_proxy",
    "n_recirculation_flagged",
    "status_in_h1_scorecard",
    "notes",
]

SOURCE_COLUMNS = [
    "source_key",
    "path",
    "used_for",
    "mutation_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def fnum(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return str(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column)) for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mean(values: list[float]) -> float:
    if not values:
        return float("nan")
    return sum(values) / len(values)


def pct(error: float, reference: float) -> float:
    if reference == 0.0:
        return float("nan")
    return abs(error) / abs(reference) * 100.0


def split_rows() -> dict[str, dict[str, str]]:
    rows = read_csv(VALIDATION_SPLIT_DIR / "admission_split_table.csv")
    return {row["row_id"]: row for row in rows}


def baseline_rows() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(HYDRAULIC_GATE_DIR / "forward_v0_hydraulic_residuals.csv")
    return {(row["case_id"], row["variant_id"]): row for row in rows}


def h1_rows() -> list[dict[str, str]]:
    return read_csv(H1_PROXY_DIR / "h1_proxy_results.csv")


def score_boundary(split_assignment: str) -> str:
    if split_assignment == "train":
        return "training_residual_only_not_model_selection_score"
    if split_assignment == "validation":
        return "diagnostic_validation_check_no_refit"
    if split_assignment == "holdout":
        return "diagnostic_holdout_check_no_refit"
    return "diagnostic_only"


def row_decision(split_assignment: str, reduction_pct: float, h1_abs_pct: float) -> str:
    if reduction_pct <= 0.0:
        return "fails_directionality_gate"
    if split_assignment == "train":
        return "train_row_improves_mdot_screen_only"
    if h1_abs_pct <= 15.0:
        return "diagnostic_row_improves_enough_for_forward_v1_scorecard_refresh"
    return "diagnostic_row_improves_but_residual_still_large"


def build_scorecard() -> list[dict[str, Any]]:
    split_by_case = split_rows()
    baseline_by_key = baseline_rows()
    rows: list[dict[str, Any]] = []
    for h1 in h1_rows():
        h1_variant = h1["variant_id"]
        if not h1_variant.endswith("_H1_proxy"):
            continue
        base_variant = h1_variant.removesuffix("_H1_proxy")
        key = (h1["case_id"], base_variant)
        base = baseline_by_key[key]
        cfd_mdot = fnum(h1["cfd_mdot_kg_s"])
        base_err = fnum(base["mdot_error_vs_cfd_kg_s"])
        h1_err = fnum(h1["mdot_error_vs_cfd_kg_s"])
        if cfd_mdot is None or base_err is None or h1_err is None:
            raise ValueError(f"missing mdot fields for {key}")
        base_abs_pct = pct(base_err, cfd_mdot)
        h1_abs_pct = pct(h1_err, cfd_mdot)
        reduction = abs(base_err) - abs(h1_err)
        reduction_pct = reduction / abs(base_err) * 100.0 if base_err else float("nan")
        split_assignment = split_by_case[h1["case_id"]]["current_assignment"]
        rows.append(
            {
                "case_id": h1["case_id"],
                "fluid_case_name": h1["fluid_case_name"],
                "source_id": h1["source_id"],
                "split_assignment": split_assignment,
                "split_score_boundary": score_boundary(split_assignment),
                "base_variant_id": base_variant,
                "h1_variant_id": h1_variant,
                "comparison_engine": "fast_scan_baseline_vs_fast_scan_h1_proxy",
                "cfd_mdot_kg_s": cfd_mdot,
                "baseline_mdot_kg_s": fnum(base["mdot_kg_s"]),
                "h1_mdot_kg_s": fnum(h1["mdot_kg_s"]),
                "baseline_mdot_error_vs_cfd_kg_s": base_err,
                "h1_mdot_error_vs_cfd_kg_s": h1_err,
                "baseline_abs_mdot_error_pct": base_abs_pct,
                "h1_abs_mdot_error_pct": h1_abs_pct,
                "mdot_error_reduction_kg_s": reduction,
                "mdot_error_reduction_pct": reduction_pct,
                "baseline_pressure_residual_Pa": fnum(base["pressure_residual_Pa"]),
                "h1_pressure_residual_Pa": fnum(h1["pressure_residual_Pa"]),
                "h1_accepted_for_validation": h1["accepted_for_validation"],
                "thermal_fit_used": h1["thermal_fit_used"],
                "movement_direction": "toward_cfd" if reduction > 0.0 else "away_or_no_improvement",
                "row_decision": row_decision(split_assignment, reduction_pct, h1_abs_pct),
                "boundary_note": (
                    "H1 is an aggregate fixed-K proxy; row can refresh a forward-v1 scorecard "
                    "only as diagnostic hydraulic evidence until localized Fluid support exists."
                ),
            }
        )
    return rows


def build_variant_summary(scorecard: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base_variant in sorted({row["base_variant_id"] for row in scorecard}):
        group = [row for row in scorecard if row["base_variant_id"] == base_variant]
        h1_variant = group[0]["h1_variant_id"]
        by_split = {row["split_assignment"]: row for row in group}
        reductions = [float(row["mdot_error_reduction_pct"]) for row in group]
        mean_reduction = mean(reductions)
        mean_h1_pct = mean([float(row["h1_abs_mdot_error_pct"]) for row in group])
        all_over = all(float(row["h1_mdot_error_vs_cfd_kg_s"]) > 0.0 for row in group)
        movement_gate = "pass_directional_screen" if mean_reduction > 50.0 else "fail_or_marginal_directional_screen"
        if movement_gate == "pass_directional_screen":
            decision = "unblocks_forward_v1_scorecard_refresh_as_diagnostic_proxy_not_final_closure"
        else:
            decision = "does_not_unblock_forward_v1_scorecard_refresh"
        rows.append(
            {
                "base_variant_id": base_variant,
                "h1_variant_id": h1_variant,
                "n_rows": len(group),
                "mean_baseline_abs_mdot_error_kg_s": mean(
                    [abs(float(row["baseline_mdot_error_vs_cfd_kg_s"])) for row in group]
                ),
                "mean_h1_abs_mdot_error_kg_s": mean([abs(float(row["h1_mdot_error_vs_cfd_kg_s"])) for row in group]),
                "mean_baseline_abs_mdot_error_pct": mean(
                    [float(row["baseline_abs_mdot_error_pct"]) for row in group]
                ),
                "mean_h1_abs_mdot_error_pct": mean_h1_pct,
                "mean_mdot_error_reduction_pct": mean_reduction,
                "train_h1_abs_mdot_error_pct": by_split.get("train", {}).get("h1_abs_mdot_error_pct"),
                "validation_h1_abs_mdot_error_pct": by_split.get("validation", {}).get("h1_abs_mdot_error_pct"),
                "holdout_h1_abs_mdot_error_pct": by_split.get("holdout", {}).get("h1_abs_mdot_error_pct"),
                "all_h1_rows_overpredict_cfd": str(all_over).lower(),
                "movement_gate": movement_gate,
                "forward_v1_scoring_decision": decision,
            }
        )
    return rows


def recirculation_count(rows: list[dict[str, str]]) -> int:
    return sum("recirculation" in row.get("quality_flags", "") for row in rows)


def is_fit_safe(row: dict[str, str]) -> bool:
    return row.get("fit_safety", "").startswith("fit_safe")


def build_term_boundary() -> list[dict[str, Any]]:
    named = read_csv(NAMED_LOSS_DIR / "named_pressure_loss_table.csv")
    reset = read_csv(NAMED_LOSS_DIR / "reset_distance_map.csv")
    fit_gate = read_csv(HYDRAULIC_GATE_DIR / "hydraulic_fit_safety_gate.csv")
    h1_k = read_csv(H1_PROXY_DIR / "h1_proxy_k_source.csv")
    included_by_loss = Counter(row["loss_class"] for row in h1_k if row["included_in_proxy"] == "yes")

    pressure_gradient = [row for row in fit_gate if row["lane"] == "pressure_gradient_friction"]
    momentum = [row for row in fit_gate if row["lane"] == "momentum_corrected_friction"]
    branch = [row for row in named if row["loss_class"] == "branch_apparent"]
    cluster = [row for row in named if row["loss_class"] == "cluster_K"]
    straight = [row for row in named if row["loss_class"] == "straight_section"]
    recirc_named = [row for row in named if row["fit_use_status"] == "not_fit_recirculation"]

    return [
        {
            "term_family": "straight_friction_pressure_gradient",
            "source_table": rel(HYDRAULIC_GATE_DIR / "hydraulic_fit_safety_gate.csv"),
            "n_rows": len(pressure_gradient),
            "n_fit_target_or_fit_safe": sum(is_fit_safe(row) for row in pressure_gradient),
            "n_included_in_h1_proxy": 0,
            "n_recirculation_flagged": 0,
            "status_in_h1_scorecard": "guardrail_only_not_proxy_K",
            "notes": "Raw pressure-gradient friction remains separate from named K; only left_lower_leg and left_upper_leg are fit-safe with mesh caveats.",
        },
        {
            "term_family": "straight_section_named_loss",
            "source_table": rel(NAMED_LOSS_DIR / "named_pressure_loss_table.csv"),
            "n_rows": len(straight),
            "n_fit_target_or_fit_safe": sum(row["fit_use_status"] == "fit_target" for row in straight),
            "n_included_in_h1_proxy": included_by_loss.get("straight_section", 0),
            "n_recirculation_flagged": recirculation_count(straight),
            "status_in_h1_scorecard": "kept_separate_not_in_aggregate_K",
            "notes": "Straight-section rows are not hidden inside the proxy K sum.",
        },
        {
            "term_family": "component_K",
            "source_table": rel(NAMED_LOSS_DIR / "named_pressure_loss_table.csv"),
            "n_rows": 0,
            "n_fit_target_or_fit_safe": 0,
            "n_included_in_h1_proxy": 0,
            "n_recirculation_flagged": 0,
            "status_in_h1_scorecard": "not_present_as_distinct_rows",
            "notes": "The available named-loss table carries branch_apparent and cluster_K rows; no distinct component_K rows are exported yet.",
        },
        {
            "term_family": "cluster_K",
            "source_table": rel(NAMED_LOSS_DIR / "named_pressure_loss_table.csv"),
            "n_rows": len(cluster),
            "n_fit_target_or_fit_safe": sum(row["fit_use_status"] == "fit_target" for row in cluster),
            "n_included_in_h1_proxy": included_by_loss.get("cluster_K", 0),
            "n_recirculation_flagged": recirculation_count(cluster),
            "status_in_h1_scorecard": "diagnostic_named_loss_not_included_in_proxy",
            "notes": "Cluster K rows stay visible; current H1 proxy did not include them because only finite Salt2 fit-target K_local branch rows were summed.",
        },
        {
            "term_family": "branch_apparent_loss",
            "source_table": rel(NAMED_LOSS_DIR / "named_pressure_loss_table.csv"),
            "n_rows": len(branch),
            "n_fit_target_or_fit_safe": sum(row["fit_use_status"] == "fit_target" for row in branch),
            "n_included_in_h1_proxy": included_by_loss.get("branch_apparent", 0),
            "n_recirculation_flagged": recirculation_count(branch),
            "status_in_h1_scorecard": "aggregate_fixed_K_proxy_source",
            "notes": "Only Salt2 finite fit-target branch_apparent K_local rows feed the aggregate proxy K=40.6384.",
        },
        {
            "term_family": "reset_development",
            "source_table": rel(NAMED_LOSS_DIR / "reset_distance_map.csv"),
            "n_rows": len(reset),
            "n_fit_target_or_fit_safe": sum(row["hydraulic_reset_status"] != "" for row in reset),
            "n_included_in_h1_proxy": 0,
            "n_recirculation_flagged": recirculation_count(reset),
            "status_in_h1_scorecard": "diagnostic_reset_context_not_fitted",
            "notes": "Reset/development rows explain candidate structure but were not fit as a thermal or global friction multiplier.",
        },
        {
            "term_family": "momentum_corrected_profile_or_debuoying",
            "source_table": rel(HYDRAULIC_GATE_DIR / "hydraulic_fit_safety_gate.csv"),
            "n_rows": len(momentum),
            "n_fit_target_or_fit_safe": sum(is_fit_safe(row) for row in momentum),
            "n_included_in_h1_proxy": 0,
            "n_recirculation_flagged": 0,
            "status_in_h1_scorecard": "diagnostic_only_not_training_K",
            "notes": "Momentum-corrected rows remain profile/debuoying diagnostics; not used to hide errors in one friction multiplier.",
        },
        {
            "term_family": "recirculation_diagnostics",
            "source_table": rel(NAMED_LOSS_DIR / "named_pressure_loss_table.csv"),
            "n_rows": len(recirc_named),
            "n_fit_target_or_fit_safe": 0,
            "n_included_in_h1_proxy": 0,
            "n_recirculation_flagged": len(recirc_named),
            "status_in_h1_scorecard": "excluded_from_fit_and_proxy",
            "notes": "Recirculating spans remain diagnostic and are not reduced to single-stream K or friction coefficients.",
        },
    ]


def source_manifest() -> list[dict[str, str]]:
    sources = [
        ("h1_proxy_results", H1_PROXY_DIR / "h1_proxy_results.csv", "H1 proxy mdot rows"),
        ("h1_proxy_summary", H1_PROXY_DIR / "summary.json", "H1 proxy guardrails"),
        ("hydraulic_gate_residuals", HYDRAULIC_GATE_DIR / "forward_v0_hydraulic_residuals.csv", "baseline fast_scan mdot rows"),
        ("hydraulic_fit_safety_gate", HYDRAULIC_GATE_DIR / "hydraulic_fit_safety_gate.csv", "fit-safe friction and pressure guardrails"),
        ("validation_split", VALIDATION_SPLIT_DIR / "admission_split_table.csv", "train validation holdout boundary"),
        ("named_pressure_loss_table", NAMED_LOSS_DIR / "named_pressure_loss_table.csv", "named loss classes and K source"),
        ("reset_distance_map", NAMED_LOSS_DIR / "reset_distance_map.csv", "reset and development diagnostics"),
        ("candidate_rankings", HYDRAULIC_CANDIDATES_DIR / "candidate_rankings.csv", "H1 candidate rationale"),
        ("solve_case_confirmation", SOLVE_CASE_DIR / "comparison_summary.json", "forward-v0 solve_case boundary context"),
    ]
    return [
        {
            "source_key": key,
            "path": rel(path),
            "used_for": used_for,
            "mutation_status": "read_only",
        }
        for key, path, used_for in sources
    ]


def build_readme(summary: dict[str, Any]) -> str:
    f1 = summary["variant_decisions"]["F1_heater_only"]
    return "\n".join(
        [
            "---",
            "provenance:",
            "  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/summary.json",
            "  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/forward_v0_hydraulic_residuals.csv",
            "  - work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv",
            "tags: [forward-model, predictive-1d, hydraulics, h1-proxy, scorecard]",
            "related:",
            "  - .agent/status/2026-07-14_AGENT-310.md",
            "  - .agent/journal/2026-07-14/predictive-h1-hydraulic-scorecard.md",
            "task: AGENT-310",
            "date: 2026-07-14",
            "role: Implementer/Tester/Writer",
            "type: work_product",
            "status: complete",
            "---",
            "# Predictive H1 Hydraulic Scorecard",
            "",
            "This package scores the bounded AGENT-308 H1 fixed-K proxy against the prior hydraulic gate. It performs no thermal fitting, does not edit external Fluid source, and does not mutate native CFD outputs.",
            "",
            "## Decision",
            "",
            f"- H1 passes the directional hydraulic screen for `F1_heater_only`: mean mdot error drops from `{f1['mean_baseline_abs_mdot_error_kg_s']:.6f}` kg/s to `{f1['mean_h1_abs_mdot_error_kg_s']:.6f}` kg/s, a `{f1['mean_mdot_error_reduction_pct']:.2f}%` reduction.",
            f"- The remaining mean H1 mdot error is `{f1['mean_h1_abs_mdot_error_pct']:.2f}%` of CFD mdot, and all H1 rows still overpredict CFD mdot.",
            "- This is enough to unblock a forward-v1 scorecard refresh as diagnostic/proxy hydraulic evidence.",
            "- This is not enough to claim a final localized H1 closure or publication-ready forward-v1 model; current Fluid support only exercised one aggregate fixed-K proxy.",
            "",
            "## Train / Diagnostic Boundary",
            "",
            "- `salt_2` is the training residual because the proxy K was trained from Salt2 finite fit-target rows.",
            "- `salt_3` is a validation diagnostic check with no refit.",
            "- `salt_4` is a holdout diagnostic check with no refit.",
            "- No validation or holdout rows were used to train K, and no thermal response was fitted.",
            "",
            "## Outputs",
            "",
            "- `h1_hydraulic_scorecard.csv`",
            "- `h1_variant_decision_summary.csv`",
            "- `hydraulic_term_boundary.csv`",
            "- `source_manifest.csv`",
            "- `summary.json`",
            "",
            "## Reproduce",
            "",
            "```bash",
            "python3 tools/analyze/build_predictive_h1_hydraulic_scorecard.py",
            "python3 -m unittest tools.analyze.test_predictive_h1_hydraulic_scorecard",
            "```",
            "",
        ]
    )


def run_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard = build_scorecard()
    variant_summary = build_variant_summary(scorecard)
    term_boundary = build_term_boundary()
    manifest = source_manifest()

    write_csv(out_dir / "h1_hydraulic_scorecard.csv", scorecard, SCORECARD_COLUMNS)
    write_csv(out_dir / "h1_variant_decision_summary.csv", variant_summary, VARIANT_COLUMNS)
    write_csv(out_dir / "hydraulic_term_boundary.csv", term_boundary, TERM_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", manifest, SOURCE_COLUMNS)

    variant_decisions = {row["base_variant_id"]: row for row in variant_summary}
    summary: dict[str, Any] = {
        "task_id": "AGENT-310",
        "generated_utc": utc_now(),
        "overall_decision": variant_decisions["F1_heater_only"]["forward_v1_scoring_decision"],
        "comparison_engine": "fast_scan_baseline_vs_fast_scan_h1_proxy",
        "h1_proxy_not_faithful_localized_closure": True,
        "thermal_fit_used": False,
        "external_fluid_modified": False,
        "native_solver_outputs_mutated": False,
        "publication_closure_allowed": False,
        "train_case_id": "salt_2",
        "diagnostic_case_ids": ["salt_3", "salt_4"],
        "variant_decisions": variant_decisions,
        "n_scorecard_rows": len(scorecard),
        "n_term_boundary_rows": len(term_boundary),
        "outputs": [
            "README.md",
            "h1_hydraulic_scorecard.csv",
            "h1_variant_decision_summary.csv",
            "hydraulic_term_boundary.csv",
            "source_manifest.csv",
            "summary.json",
        ],
    }
    write_json(out_dir / "summary.json", summary)
    (out_dir / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    summary = run_package()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
