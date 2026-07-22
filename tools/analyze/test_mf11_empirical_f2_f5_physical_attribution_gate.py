#!/usr/bin/env python3.11
"""Validate the MF11 empirical F2/F5 physical-attribution gate."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate"
TASK_ID = "TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True)
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["decision"] == "empirical_diagnostic_only"
    assert summary["empirical_model_rows"] >= 6
    assert summary["attribution_rows"] == 6
    assert summary["coefficient_plausibility_rows"] == 2
    assert summary["contradiction_rows"] == 5
    assert summary["physical_attribution_unique"] is False
    assert summary["physical_closure_admitted"] is False
    assert summary["source_property_release"] is False
    assert summary["coefficient_admission"] is False
    assert summary["final_score_claim"] is False
    assert summary["new_fitting_tuning_model_selection"] is False
    assert summary["validation_holdout_external_test_scoring"] is False
    assert summary["residual_internal_nu_absorption"] is False
    assert summary["f2_transfer_reduction_pct"] > 80.0
    assert summary["f5_transfer_reduction_pct"] > summary["f2_transfer_reduction_pct"]

    attribution = read_csv(OUT_DIR / "physical_attribution_matrix.csv")
    physics = {row["candidate_physics"] for row in attribution}
    assert {
        "MF07_entrance_development_reset",
        "MF08_signed_wall_flux_development",
        "MF09_recirculating_upcomer_exchange_stratification",
        "D3_wall_shape_axial_mixing",
        "D4_segment_source_placement",
        "sensor_QOI_projection",
    }.issubset(physics)
    assert all(row["admissible_as_physical_closure"] == "False" for row in attribution)

    plausibility = read_csv(OUT_DIR / "coefficient_to_physics_plausibility.csv")
    assert {row["empirical_model"] for row in plausibility} == {
        "F2_global_affine",
        "F5_thermal_family_offset_shared_multiplier",
    }
    assert all(row["gate"] == "empirical_diagnostic_only" for row in plausibility)
    assert any("hidden fit" in row["forbidden_interpretation"] for row in plausibility)

    guardrails = read_csv(OUT_DIR / "no_mutation_guardrails.csv")
    assert all(row["performed"] == "False" for row in guardrails)

    assert (OUT_DIR / "README.md").exists()
    assert (ROOT / f".agent/status/2026-07-22_{TASK_ID}.md").exists()
    assert (ROOT / ".agent/journal/2026-07-22/mf11-empirical-f2-f5-physical-attribution-gate.md").exists()
    assert (ROOT / "imports/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate.json").exists()
    print("MF11 empirical F2/F5 physical-attribution gate package passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
