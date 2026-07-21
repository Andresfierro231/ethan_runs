#!/usr/bin/env python3
"""Tests for build_thermal_parity_resolution_gate.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_thermal_parity_resolution_gate as gate


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThermalParityResolutionGateTests(unittest.TestCase):
    def test_residual_owner_gate_requires_no_internal_nu_guardrail(self) -> None:
        rows = [
            {
                "residual_id": "heater_realized_fraction",
                "residual_owner": "heater/source",
                "internal_nu_guardrail": "Do not fit this residual into internal Nu.",
                "excluded_internal_nu_use": "Do not tune Nu to hide heater error.",
                "primary_runtime_setup_inputs": "heater power",
                "source_evidence": "source.md",
            }
        ]
        evaluated = gate.evaluate_residual_owners(rows)
        heater = next(row for row in evaluated if row["residual_id"] == "heater_realized_fraction")

        self.assertEqual(heater["resolution_gate"], "pass")
        missing = [row for row in evaluated if row["reason"] == "missing_required_residual_row"]
        self.assertGreaterEqual(len(missing), 1)

    def test_thermal_rows_fail_if_internal_nu_absorbs_residual(self) -> None:
        rows = [
            {
                "case_id": "salt_2",
                "segment": "lower_leg",
                "qoi": "Nu",
                "review_admission_class": "fit_admissible",
                "internal_nu_fit_allowed": "true",
                "guardrail": "fit_boundary_residual_into_Nu",
            }
        ]
        evaluated = gate.evaluate_thermal_rows(rows)

        self.assertEqual(evaluated[0]["residual_owner_gate"], "fail")
        self.assertEqual(evaluated[0]["parity_resolution_use"], "does_not_support_resolution")

    def test_continuation_gate_accepts_preferred_setup_only_hx(self) -> None:
        hx_rows = [
            {
                "candidate_id": gate.PREFERRED_HX,
                "validation_gate": "pass",
                "holdout_gate": "pass",
                "runtime_gate": "pass",
                "runtime_input_violation_count": "0",
                "validation_abs_error_W": "2.8",
                "holdout_abs_error_W": "7.5",
            }
        ]
        runtime_rows = [{"gate": "pass", "forbidden_runtime_inputs": "realized wallHeatFlux"}]
        fit_rows = [{"fit_row_id": "internal_nu_fit_admitted_rows", "admitted_row_count": "0"}]

        rows = gate.evaluate_continuation(hx_rows, runtime_rows, fit_rows)
        gates = {row["continuation_item"]: row["gate"] for row in rows}

        self.assertEqual(gates["setup_only_hx_cooler"], "pass")
        self.assertEqual(gates["runtime_input_legality"], "pass")
        self.assertEqual(gates["internal_nu_fit_rows"], "pass")

    def test_blocker_resolves_only_when_all_gates_pass(self) -> None:
        residuals = [
            {"resolution_gate": "pass"},
            {"resolution_gate": "pass"},
        ]
        thermal = [
            {"residual_owner_gate": "pass"},
            {"residual_owner_gate": "pass"},
        ]
        continuation = [
            {"gate": "pass"},
            {"gate": "pass"},
        ]

        resolved = gate.blocker_decision_rows(residuals, thermal, continuation)[0]
        self.assertEqual(resolved["decision"], "resolved")
        self.assertEqual(resolved["can_update_blocker_register"], "yes")

        continuation[0]["gate"] = "fail"
        not_resolved = gate.blocker_decision_rows(residuals, thermal, continuation)[0]
        self.assertEqual(not_resolved["decision"], "not_resolved")
        self.assertEqual(not_resolved["can_update_blocker_register"], "no")

    def test_build_package_writes_resolution_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = gate.build_package(out)

            self.assertEqual(summary["task"], "AGENT-452")
            self.assertEqual(summary["blocker_decision"], "resolved")
            self.assertEqual(summary["internal_nu_fit_allowed_rows"], 0)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertTrue((out / "blocker_resolution_decision.csv").exists())
            self.assertTrue((out / "litrev_methodology_crosswalk.csv").exists())

            decision = read_csv(out / "blocker_resolution_decision.csv")[0]
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(decision["decision"], "resolved")
            self.assertTrue(parsed["can_update_blocker_register"])


if __name__ == "__main__":
    unittest.main()
