#!/usr/bin/env python3
"""Validate thesis scoreboard signed-error shape package."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_thesis_scoreboard_signed_error_shape_and_model_form_dispatch.py"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    subprocess.run([sys.executable, str(BUILDER)], check=True)

    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "signed_error_shape_executed_model_form_dispatch_updated_no_scoring_or_admission"
    assert summary["shape_metric_rows"] == 24
    assert summary["finite_sensor_rows"] == 180
    assert summary["model_level_rows"] == 4
    assert summary["board_dispatch_rows"] == 5
    assert summary["best_current_legacy_numeric_model"] == "M3"
    assert summary["m0_can_score_now"] is False
    assert summary["s13_same_qoi_uq_ready"] is False
    assert summary["pressure_component_k_or_f6_admitted"] is False

    metrics = read_csv(OUT / "signed_error_shape_metrics.csv")
    assert len(metrics) == 24
    assert {r["model_form_id"] for r in metrics} == {"M1", "M1b", "M2", "M3"}
    assert all(r["shape_class"] for r in metrics)

    enriched = read_csv(OUT / "signed_error_shape_by_sensor.csv")
    assert len(enriched) == 180
    assert all("bias_removed_error_K" in r for r in enriched)

    board = read_csv(OUT / "model_form_board_dispatch_matrix.csv")
    assert "TODO-M0-SETUP-ONLY-BASELINE-PREDICTION-SCORECARD-2026-07-22" in {r["task_id"] for r in board}
    assert "TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22" in {r["task_id"] for r in board}
    assert "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22" in {r["task_id"] for r in board}

    for rel in [
        "figures/svg/signed_error_shape_by_sensor.svg",
        "figures/svg/bias_vs_shape_residual.svg",
        "README.md",
    ]:
        p = OUT / rel
        assert p.exists() and p.stat().st_size > 200


if __name__ == "__main__":
    main()
