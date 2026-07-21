import unittest

from tools.analyze.build_val_salt2_training_readiness_and_corner_k_unlock import (
    CORNER_EVIDENCE,
    CORNER_RECOMPUTED,
    PRESSURE_BRANCH_ADMISSION,
    TAP_LENGTHS,
    VAL_BC_SUMMARY,
    VAL_SECTION_LEDGER,
    build_corner_k_rows,
    build_junction_split,
    build_section_reconciliation,
    build_val_training_gate,
    junction_bucket,
    load_wall_heat_rows,
    read_csv,
    section_for_patch,
)


class ValSalt2TrainingReadinessAndCornerKUnlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_rows = load_wall_heat_rows()
        cls.section_rows = build_section_reconciliation(cls.patch_rows, read_csv(VAL_SECTION_LEDGER))
        cls.junction_rows = build_junction_split(cls.patch_rows, read_csv(VAL_SECTION_LEDGER))
        cls.gate_rows = build_val_training_gate(
            cls.patch_rows,
            cls.section_rows,
            cls.junction_rows,
            read_csv(VAL_BC_SUMMARY),
        )
        cls.corner_rows = build_corner_k_rows(
            read_csv(CORNER_EVIDENCE),
            read_csv(CORNER_RECOMPUTED),
            read_csv(TAP_LENGTHS),
            read_csv(PRESSURE_BRANCH_ADMISSION),
        )

    def test_patch_mapping(self):
        self.assertEqual(section_for_patch("pipeleg_lower_05_straight")[0], "heater")
        self.assertEqual(section_for_patch("pipeleg_upper_05_cooler")[0], "cooling_branch")
        self.assertEqual(section_for_patch("junction_upper_right_upper_stub")[0], "junctions")
        self.assertEqual(junction_bucket("junction_lower_left_left_stub"), "lower_left")

    def test_val_patch_ledger_has_expected_entities(self):
        self.assertEqual(len(self.patch_rows), 69)
        junction_rows = [row for row in self.patch_rows if row["section_key"] == "junctions"]
        self.assertEqual(len(junction_rows), 21)
        self.assertTrue(any(row["entity_name"] == "pipeleg_left_04_test_section" for row in self.patch_rows))

    def test_patch_sums_reconcile_to_section_ledger(self):
        residuals = [abs(float(row["latest_residual_patch_minus_ledger_w"])) for row in self.section_rows]
        self.assertLess(max(residuals), 1e-6)

    def test_junction_split_closes_to_aggregate_loss(self):
        total = next(row for row in self.junction_rows if row["physical_junction_bucket"] == "case_total_check")
        split_loss = float(total["realized_external_loss_positive_W"])
        aggregate_loss = float(total["source_aggregate_junction_loss_positive_W"])
        self.assertAlmostEqual(split_loss, aggregate_loss, places=9)

    def test_val_salt2_external_policy_blocks_training_use(self):
        gate = {row["gate"]: row["status"] for row in self.gate_rows}
        self.assertEqual(gate["patch_level_wall_heat_flux_available"], "pass")
        self.assertEqual(gate["training_use_without_reclassification"], "fail_policy")

    def test_corner_k_remains_not_fit_admitted(self):
        self.assertEqual(len(self.corner_rows), 12)
        self.assertEqual({row["fit_admitted"] for row in self.corner_rows}, {"no"})
        self.assertTrue(all("component_K_not_isolated" in row["why_diagnostic"] for row in self.corner_rows))
        self.assertTrue(any(float(row["K_local_centerline"]) < 0 for row in self.corner_rows))


if __name__ == "__main__":
    unittest.main()
