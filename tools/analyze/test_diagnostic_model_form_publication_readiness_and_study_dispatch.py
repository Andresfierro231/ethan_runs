#!/usr/bin/env python3
"""Validate diagnostic model-form publication-readiness dispatch package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_diagnostic_model_form_publication_readiness_and_study_dispatch.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_diagnostic_model_form_publication_readiness_and_study_dispatch"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    subprocess.run([sys.executable, str(BUILDER)], check=True)
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "study_rows_listed_publication_readiness_pass_with_fail_closed_admission"
    assert summary["study_rows"] == 7
    assert summary["board_rows_listed"] == 7
    assert summary["publication_ready_for_diagnostic_claims"] is True
    assert summary["ready_for_admitted_closure_claims"] is False
    assert summary["best_diagnostic"] == "D4_M3_segment_offsets_min2_train"

    studies = read_csv(OUT / "study_dispatch_from_findings.csv")
    assert len(studies) == 7
    assert studies[0]["board_task"] == "TODO-MF-D4-SEGMENT-SOURCE-PLACEMENT-EVIDENCE-GATE-2026-07-22"
    assert all(row["admission_boundary"] for row in studies)

    crosswalk = read_csv(OUT / "board_row_crosswalk.csv")
    assert len(crosswalk) == 7
    assert all(row["listed_on_board"] == "True" for row in crosswalk)

    readiness = read_csv(OUT / "publication_readiness_audit.csv")
    assert len(readiness) == 6
    statuses = {row["status"] for row in readiness}
    assert "fail_closed" in statuses
    assert "pass_with_guardrail" in statuses

    claims = read_csv(OUT / "diagnostic_form_publication_claims.csv")
    assert len(claims) == 6
    assert all("diagnostic" in row["claim_allowed"] for row in claims)
    assert all("admitted" in row["claim_forbidden"] for row in claims)

    for rel in ["README.md", "source_manifest.csv", "no_mutation_guardrails.csv"]:
        path = OUT / rel
        assert path.exists() and path.stat().st_size > 200


if __name__ == "__main__":
    main()
