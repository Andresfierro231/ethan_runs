#!/usr/bin/env python3
"""Validate the hybrid pressure no-fit performance bakeoff package."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_hybrid_pressure_no_fit_performance_bakeoff"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check(out_dir: Path = DEFAULT_OUTPUT_DIR) -> list[str]:
    findings: list[str] = []
    required = [
        "no_fit_performance_table.csv",
        "residual_ownership_table.csv",
        "baseline_comparison_provenance.csv",
        "split_role_audit.csv",
        "candidate_reviewability_decision.csv",
        "source_manifest.csv",
        "summary.json",
        "README.md",
    ]
    for filename in required:
        if not (out_dir / filename).exists():
            findings.append(f"missing {filename}")
    if findings:
        return findings

    perf = read_csv(out_dir / "no_fit_performance_table.csv")
    baseline = read_csv(out_dir / "baseline_comparison_provenance.csv")
    split = read_csv(out_dir / "split_role_audit.csv")
    decisions = read_csv(out_dir / "candidate_reviewability_decision.csv")
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))

    if len(perf) != 4:
        findings.append(f"performance row count is {len(perf)}, expected 4")
    if not any(row["method"] == "salt2_frozen_diagnostic" for row in perf):
        findings.append("missing salt2_frozen_diagnostic performance row")
    if not any(row["method"] == "F3_shah_apparent_baseline_status" for row in perf):
        findings.append("missing F3/Shah baseline status row")
    if any(row["validation_rows_consumed"] != "0" for row in perf):
        findings.append("performance consumed validation rows")
    if any(row["holdout_rows_consumed"] != "0" for row in perf):
        findings.append("performance consumed holdout rows")
    if any(row["external_test_rows_consumed"] != "0" for row in perf):
        findings.append("performance consumed external-test rows")
    if any(row["fit_or_tuning_performed"] != "false" for row in perf):
        findings.append("performance indicates fit/tuning")
    if any(row["admission_status"] != "not_admitted" for row in perf):
        findings.append("performance indicates admission")
    if not all(row["numeric_comparison_available"] == "false" for row in baseline):
        findings.append("baseline table should mark F3/Shah numeric comparison unavailable")
    if not any(row["status"] == "not_evaluated_no_ordinary_candidate" for row in baseline):
        findings.append("baseline table missing not_evaluated_no_ordinary_candidate status")
    if {row["case_id"] for row in split} != {"salt_2", "salt_3", "salt_4"}:
        findings.append("split audit must contain Salt2/Salt3/Salt4 only")
    if not any(row["decision"] == "no_thesis_evidence_only" for row in decisions):
        findings.append("decision table missing thesis-evidence-only decision")

    zero_keys = [
        "component_k_admitted_rows",
        "cluster_k_admitted_rows",
        "f6_fit_rows",
        "clipped_k_rows",
        "hidden_global_multiplier_rows",
        "validation_rows_consumed",
        "holdout_rows_consumed",
        "external_test_rows_consumed",
    ]
    for key in zero_keys:
        if summary.get(key) != 0:
            findings.append(f"summary {key} is {summary.get(key)}, expected 0")
    if summary.get("candidate_reviewability") != "thesis_evidence_only_not_candidate_reviewable":
        findings.append("summary candidate_reviewability is wrong")
    if summary.get("f3_shah_numeric_comparison_available") is not False:
        findings.append("summary should block F3/Shah numeric comparison")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    findings = check(args.out_dir)
    if findings:
        print("\n".join(findings))
        return 1
    print("hybrid_pressure_no_fit_performance_bakeoff: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
