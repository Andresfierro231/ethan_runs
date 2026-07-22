#!/usr/bin/env python3
"""Checks for the entrance/development/reset missing-physics gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_mf_entrance_development_reset_gate"
)


def read_csv(name: str) -> list[dict[str, str]]:
    with (OUT_DIR / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/analyze/build_mf_entrance_development_reset_gate.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )

    summary = json.loads((OUT_DIR / "summary.json").read_text())
    assert summary["decision"] == "entrance_development_reset_gate_diagnostic_only_no_admission"
    assert summary["single_stream_gate_rows"] == 90
    assert summary["single_stream_allowed_precheck_rows"] == 60
    assert summary["single_stream_admitted_rows"] == 0
    assert summary["branch_rows"] == 6
    assert summary["recirculation_invalid_spans"] == 2
    assert summary["same_qoi_uq_blocked_spans"] == 6
    assert summary["boundary_toggle_rows"] == 35
    assert summary["boundary_executable_ablation_rows"] == 0
    assert summary["source_property_release"] is False
    assert summary["coefficient_admission"] is False
    assert summary["s11_s12_s13_s15_s6_trigger"] is False
    assert summary["residual_absorbed_into_internal_nu"] is False

    branch_rows = read_csv("branch_development_admissibility.csv")
    assert len(branch_rows) == 6
    assert {row["admission_status"] for row in branch_rows} == {
        "no_coefficient_admission"
    }

    gate_rows = read_csv("development_model_form_gate_matrix.csv")
    assert any(row["toggle_id"] == "d2_bulk_to_tp_projection" for row in gate_rows)
    assert any(row["toggle_id"] == "d3_wall_shape_axial_mixing" for row in gate_rows)
    assert any(row["toggle_id"] == "d4_segment_source_placement" for row in gate_rows)
    assert all(row["executable_rows"] in {"0", ""} for row in gate_rows)

    queue_rows = read_csv("successor_implementation_queue.csv")
    assert [row["priority"] for row in queue_rows] == ["1", "2", "3"]

    manifest_rows = read_csv("source_manifest.csv")
    assert {row["mutation_status"] for row in manifest_rows} == {"read_only"}

    print("mf entrance/development/reset gate checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
