#!/usr/bin/env python3
"""Validate thesis main-text write-up and table polish package."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_maintext_writeup_table_polish_pack"


REQUIRED = [
    "README.md",
    "main_text_table_s6_gate_flow.csv",
    "main_text_table_s7_sensor_policy.csv",
    "main_text_table_s9_exchange_requirements.csv",
    "main_text_table_s10_pressure_gate_waterfall.csv",
    "main_text_table_s13_exchange_scaffold.csv",
    "main_text_table_s14_branch_use_summary.csv",
    "main_text_table_h2_passive_heat_response.csv",
    "runtime_input_methods_table.csv",
    "latex_import_manifest.csv",
    "negative_results_scientific_contribution.md",
    "upcomer_physics_subsection.md",
    "pressure_f6_sidebar.md",
    "thermal_attribution_subsection.md",
    "runtime_leakage_methods_box.md",
    "blocked_scorecard_and_future_work_figure.md",
    "caption_bank.md",
    "source_manifest.csv",
    "summary.json",
]


def rows(name: str) -> list[dict[str, str]]:
    with (PKG / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    require(PKG.exists(), f"missing package {PKG}")
    for name in REQUIRED:
        require((PKG / name).exists(), f"missing {name}")

    summary = json.loads((PKG / "summary.json").read_text(encoding="utf-8"))
    require(summary["main_text_tables"] == 8, "main text table count mismatch")
    require(summary["writeup_sections"] == 6, "writeup section count mismatch")
    require(summary["closure_admission"] is False, "closure admission unexpectedly true")
    require(summary["final_score_claim"] is False, "final score unexpectedly true")
    require(summary["runtime_leakage_relaxed"] is False, "runtime leakage unexpectedly relaxed")

    s7 = rows("main_text_table_s7_sensor_policy.csv")
    policy = {row["policy_row"]: row["value"] for row in s7}
    require(policy["sensor_count"] == "17", "sensor count changed")
    require(policy["runtime_permissions"] == "0", "runtime permission leak")
    require(policy["fit_permissions"] == "0", "fit permission leak")
    require(policy["model_selection_permissions"] == "0", "model-selection permission leak")

    s14 = rows("main_text_table_s14_branch_use_summary.csv")
    s14_values = {row["summary_row"]: row["value"] for row in s14}
    require(s14_values["admitted_rows"] == "0", "S14 admitted rows unexpectedly nonzero")
    require("right_leg" in s14_values["preferred_future_lanes"], "right_leg future lane missing")
    require("test_section_span" in s14_values["preferred_future_lanes"], "test_section_span future lane missing")

    source_rows = rows("source_manifest.csv")
    for row in source_rows:
        path = ROOT / row["path"]
        require(path.exists(), f"missing source path {row['path']}")
        require(row["mutation_status"] == "read_only", f"unexpected mutation status {row['source_id']}")

    combined = "\n".join((PKG / name).read_text(encoding="utf-8") for name in REQUIRED if name.endswith(".md"))
    forbidden = [
        "SAM validation",
        "final predictive accuracy is available",
        "admitted passive wall/test-section closure",
        "admitted ordinary component K",
    ]
    for phrase in forbidden:
        require(phrase not in combined, f"forbidden phrase present: {phrase}")

    print("thesis main-text polish package checks passed")


if __name__ == "__main__":
    main()
