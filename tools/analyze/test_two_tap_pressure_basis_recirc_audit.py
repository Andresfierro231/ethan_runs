"""Focused tests for the two-tap pressure/basis recirculation audit."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_two_tap_pressure_basis_recirc_audit as audit


OUT = audit.OUT


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TwoTapPressureBasisRecircAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        audit.build_package()

    def test_harvested_rows_pair_into_three_feature_rows(self) -> None:
        basis = rows("pressure_velocity_basis_audit.csv")
        self.assertEqual(len(basis), 3)
        self.assertEqual({row["case_id"] for row in basis}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["feature"] == "corner_lower_right" for row in basis))
        self.assertTrue(all(row["basis_status"] == "basis_resolved_raw_endpoint_diagnostic" for row in basis))

    def test_pressure_and_velocity_basis_formulas(self) -> None:
        basis = {row["case_id"]: row for row in rows("pressure_velocity_basis_audit.csv")}
        salt2 = basis["salt_2"]
        p_up = float(salt2["p_upstream_pa"])
        p_down = float(salt2["p_downstream_pa"])
        p_rgh_up = float(salt2["p_rgh_upstream_pa"])
        p_rgh_down = float(salt2["p_rgh_downstream_pa"])
        q_up = float(salt2["dynamic_pressure_upstream_pa"])
        q_down = float(salt2["dynamic_pressure_downstream_pa"])
        self.assertAlmostEqual(float(salt2["delta_p_down_minus_up_pa"]), p_down - p_up, places=8)
        self.assertAlmostEqual(float(salt2["delta_p_rgh_down_minus_up_pa"]), p_rgh_down - p_rgh_up, places=8)
        self.assertAlmostEqual(
            float(salt2["hydrostatic_correction_pa"]),
            (p_down - p_up) - (p_rgh_down - p_rgh_up),
            places=8,
        )
        self.assertAlmostEqual(float(salt2["kinetic_correction_pa"]), q_down - q_up, places=8)
        self.assertGreater(float(salt2["local_dynamic_pressure_mean_pa"]), 0.0)

    def test_recirculation_gate_blocks_all_three_rows(self) -> None:
        recirc = rows("endpoint_recirculation_metrics.csv")
        self.assertEqual(len(recirc), 3)
        for row in recirc:
            self.assertGreaterEqual(float(row["aggregate_RAF"]), audit.RECIRC_LIMIT)
            self.assertGreaterEqual(float(row["aggregate_RMF"]), audit.RECIRC_LIMIT)
            self.assertEqual(row["ordinary_recirculation_gate"], "fail_material_reverse_flow")
            self.assertEqual(row["recirculation_decision"], "diagnostic_or_section_effective_only")

    def test_gate_decisions_do_not_admit_or_fit(self) -> None:
        gates = rows("gate_decision_table.csv")
        self.assertEqual(len(gates), 3)
        for row in gates:
            self.assertEqual(row["raw_endpoint_surface_availability"], "pass_six_raw_surfaces_harvested")
            self.assertEqual(row["pressure_velocity_basis_gate"], "pass_basis_resolved")
            self.assertEqual(row["recirculation_gate"], "fail_material_reverse_flow")
            self.assertEqual(row["ordinary_component_k_candidate"], "false")
            self.assertEqual(row["component_k_admitted"], "false")
            self.assertEqual(row["f6_fit_performed"], "false")
            self.assertEqual(row["admission_decision"], "diagnostic_only_recirculation_blocked")

    def test_summary_guardrails(self) -> None:
        summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task"], audit.TASK)
        self.assertEqual(summary["feature_pairs"], 3)
        self.assertEqual(summary["basis_resolved_pairs"], 3)
        self.assertEqual(summary["recirculation_pass_pairs"], 0)
        self.assertEqual(summary["recirculation_fail_pairs"], 3)
        self.assertEqual(summary["ordinary_component_k_candidates"], 0)
        self.assertFalse(summary["f6_fit_performed"])
        self.assertFalse(summary["component_k_admitted"])
        self.assertFalse(summary["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
