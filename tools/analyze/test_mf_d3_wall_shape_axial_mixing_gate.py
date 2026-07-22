#!/usr/bin/env python3
"""Validate the D3 wall-shape / axial-mixing gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_mf_d3_wall_shape_axial_mixing_gate.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    subprocess.run([sys.executable, str(BUILDER)], check=True)

    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "d3_wall_shape_signal_supported_diagnostic_only_same_qoi_triplets_ready_uq_not_executed"
    assert summary["wall_rows"] == 30
    assert summary["transfer_wall_rows"] == 20
    assert summary["candidate_rows"] == 3
    assert summary["candidate_ready_rows"] == 0
    assert summary["same_qoi_triplet_ready_qois"] == 4
    assert summary["same_qoi_uq_executed"] is False
    assert summary["admission_status"] == "diagnostic_not_admitted"

    wall = read_csv(OUT / "wall_index_residual_shape_decomposition.csv")
    assert len(wall) == 30
    assert all(row["sensor"].startswith("TW") for row in wall)

    crosswalk = read_csv(OUT / "s12_s13_evidence_crosswalk.csv")
    assert len(crosswalk) == 4
    assert any(row["status"] == "triplets_ready_uq_not_executed" for row in crosswalk)
    assert all(row["blocks_candidate"] == "True" for row in crosswalk)

    uq = read_csv(OUT / "same_qoi_uq_requirement_table.csv")
    assert len(uq) == 4
    assert all(row["triplet_ready"] == "true" for row in uq)
    assert all(row["same_qoi_uq_execution_status"] == "ready_not_executed" for row in uq)

    gate = read_csv(OUT / "candidate_gate.csv")
    assert len(gate) == 3
    assert all(row["candidate_ready"] == "False" for row in gate)

    for rel in ["README.md", "source_manifest.csv", "no_mutation_guardrails.csv", "publication_claim_boundary.csv"]:
        path = OUT / rel
        assert path.exists() and path.stat().st_size > 200


if __name__ == "__main__":
    main()
