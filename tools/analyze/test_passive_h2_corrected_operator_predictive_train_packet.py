#!/usr/bin/env python3
"""Validate the PASSIVE-H2 corrected-operator predictive train packet."""
from __future__ import annotations

import csv
import json
from pathlib import Path


TASK_ID = "TODO-PASSIVE-H2-CORRECTED-OPERATOR-PREDICTIVE-TRAIN-PACKET-2026-07-22"
RUNTIME_ROW = "TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    summary = json.loads((OUT_DIR / "summary.json").read_text(encoding="utf-8"))
    assert summary["task_id"] == TASK_ID
    assert summary["runtime_implementation_row"] == RUNTIME_ROW
    assert summary["runtime_implementation_worth_launching"] is True
    assert 20.0 < summary["corrected_radiation_min_W"] < summary["corrected_radiation_max_W"] < 30.0
    assert 35.0 < summary["corrected_total_min_W"] < summary["corrected_total_max_W"] < 50.0
    assert summary["current_radiation_on_noop_cases"] == 3
    for key in [
        "source_property_release",
        "numeric_q_loss_release",
        "qwall_release",
        "coefficient_admission",
        "candidate_freeze",
        "protected_scoring",
        "final_score_claim",
        "fitting_or_model_selection",
        "native_solver_outputs_mutated",
        "registry_mutated",
        "scheduler_action",
        "solver_or_sampler_launch",
        "fluid_or_external_edit",
        "runtime_leakage_relaxation",
    ]:
        assert summary[key] is False

    candidates = read_csv(OUT_DIR / "candidate_manifest.csv")
    assert len(candidates) == 1
    assert candidates[0]["development_decision"] == "worth_runtime_implementation_smoke_not_admission"

    split = read_csv(OUT_DIR / "split_reconciliation.csv")
    assert len(split) == 3
    assert sum(row["allowed_use_here"] == "False" for row in split) == 2
    assert all(row["protected_scoring_allowed"] == "False" for row in split)

    ledger = read_csv(OUT_DIR / "corrected_operator_injection_ledger.csv")
    assert len(ledger) == 3
    assert all(float(row["radiation_on_expected_heat_ledger_delta_W"]) > 20.0 for row in ledger)
    assert all(row["protected_scoring"] == "False" for row in ledger)

    contract = read_csv(OUT_DIR / "implementation_handoff_contract.csv")
    assert len(contract) == 4
    assert any(row["requirement"] == "radiation_on changes heat ledger" for row in contract)
    assert all(row["required_for_runtime_row"] == "True" for row in contract)

    sensitivity = read_csv(OUT_DIR / "sensitivity_interpolation_check.csv")
    assert len(sensitivity) == 3
    assert all(row["current_radiation_on_is_noop"] == "True" for row in sensitivity)
    assert all(row["interpolation_usable_for_scoring"] == "False" for row in sensitivity)

    audit = read_csv(OUT_DIR / "runtime_input_audit.csv")
    assert audit
    assert all(row["pass"] == "True" for row in audit)

    source = read_csv(OUT_DIR / "source_manifest.csv")
    assert source
    assert all(row["exists"] == "True" for row in source)
    print("PASS: PASSIVE-H2 corrected-operator predictive train packet is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
