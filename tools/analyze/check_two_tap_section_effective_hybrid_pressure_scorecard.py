#!/usr/bin/env python3
"""Validate the two-tap section-effective hybrid pressure scorecard package."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard"
)
EXPECTED_CASES = {"salt_2", "salt_3", "salt_4"}
EXPECTED_LEVELS = {"observed_decomposition", "salt2_frozen_diagnostic", "oracle_envelope_nonpredictive"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check(out_dir: Path = DEFAULT_OUTPUT_DIR) -> list[str]:
    findings: list[str] = []
    required = [
        "section_effective_pressure_scorecard.csv",
        "hybrid_pressure_term_contract.csv",
        "three_level_score.csv",
        "thesis_claim_ledger.csv",
        "source_manifest.csv",
        "summary.json",
        "README.md",
    ]
    for filename in required:
        if not (out_dir / filename).exists():
            findings.append(f"missing {filename}")
    if findings:
        return findings

    scorecard = read_csv(out_dir / "section_effective_pressure_scorecard.csv")
    three_level = read_csv(out_dir / "three_level_score.csv")
    contract = read_csv(out_dir / "hybrid_pressure_term_contract.csv")
    claims = read_csv(out_dir / "thesis_claim_ledger.csv")
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))

    if {row["case_id"] for row in scorecard} != EXPECTED_CASES:
        findings.append("scorecard does not contain exactly Salt2/Salt3/Salt4")
    if len(scorecard) != 3:
        findings.append(f"scorecard row count is {len(scorecard)}, expected 3")
    if len(three_level) != 9:
        findings.append(f"three_level row count is {len(three_level)}, expected 9")
    if {row["score_level"] for row in three_level} != EXPECTED_LEVELS:
        findings.append("three_level score levels are incomplete")
    if any(row["admission_status"] != "not_admitted" for row in three_level):
        findings.append("a three_level row is marked admitted")
    if any(row["protected_rows_consumed"] != "0" for row in three_level):
        findings.append("a three_level row consumed protected rows")
    if any("component_K" not in row["forbidden_use"] for row in scorecard):
        findings.append("scorecard forbidden_use does not preserve component_K guardrail")
    if not any(row["term_name"] == "Delta_p_recirc_section" for row in contract):
        findings.append("hybrid contract missing Delta_p_recirc_section")
    if not any(row["claim_status"] == "forbidden" and "component K" in row["claim"] for row in claims):
        findings.append("claim ledger missing forbidden component K claim")

    for key in [
        "component_k_admitted_rows",
        "f6_fit_rows",
        "clipped_k_rows",
        "hidden_global_multiplier_rows",
        "validation_rows_consumed",
        "holdout_rows_consumed",
        "external_test_rows_consumed",
    ]:
        if summary.get(key) != 0:
            findings.append(f"summary {key} is {summary.get(key)}, expected 0")
    if summary.get("s11_s15_s6_trigger") is not False:
        findings.append("summary indicates downstream trigger")
    if summary.get("status") != "complete":
        findings.append("summary status is not complete")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    findings = check(args.out_dir)
    if findings:
        print("\n".join(findings))
        return 1
    print("two_tap_section_effective_hybrid_pressure_scorecard: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
