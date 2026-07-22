#!/usr/bin/env python3
"""Validate the D4 segment source-placement evidence gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_mf_d4_segment_source_placement_evidence_gate.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    subprocess.run([sys.executable, str(BUILDER)], check=True)

    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "d4_segment_signal_explained_as_empirical_upper_bound_no_source_bounded_candidate"
    assert summary["target_segments"] == 4
    assert summary["candidate_rows"] == 4
    assert summary["source_bounded_candidate_ready_rows"] == 0
    assert summary["admission_status"] == "fail_closed_not_admitted"

    residual = read_csv(OUT / "segment_residual_map.csv")
    assert len(residual) >= 4
    target_segments = {row["prediction_source_segment"] for row in residual if row["target_gate_segment"] == "True"}
    assert target_segments == {"heated_incline", "left_lower_vertical", "left_upper_vertical", "right_vertical"}

    evidence = read_csv(OUT / "independent_source_heat_path_evidence.csv")
    assert len(evidence) == 4
    assert all(row["evidence_status"] == "fail_closed_source_property_not_released" for row in evidence)
    assert all(row["blocking_reason"] for row in evidence)

    gate = read_csv(OUT / "source_bounded_candidate_gate.csv")
    assert len(gate) == 4
    assert all(row["source_bounded_candidate_ready"] == "False" for row in gate)
    assert all(row["gate_status"] == "fail_closed_empirical_upper_bound_only" for row in gate)

    runtime = read_csv(OUT / "runtime_legality_matrix.csv")
    assert len(runtime) == 4
    assert all(row["runtime_legal_now"] == "False" for row in runtime)
    assert all(row["uses_validation_holdout_targets"] == "False" for row in runtime)

    for rel in ["README.md", "source_manifest.csv", "no_mutation_guardrails.csv", "publication_claim_boundary.csv"]:
        path = OUT / rel
        assert path.exists() and path.stat().st_size > 200


if __name__ == "__main__":
    main()
