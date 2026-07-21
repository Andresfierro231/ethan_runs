import unittest

from tools.analyze.build_junction_split_heat_ledger_and_model_gate import (
    AGENT462_COVERAGE,
    AGENT462_HEAT_AUDIT,
    EXTERNAL_BC_PATCH_CONTRACT,
    HEAT_LEDGER_STATUS,
    PRESSURE_ADMISSION_BRANCH,
    PRESSURE_ADMISSION_SUMMARY,
    WALL_SHELL_TEMPS,
    aggregate_patch_ledger,
    build_case_admission_rows,
    build_model_gate_rows,
    build_patch_ledger,
    physical_bucket,
    read_csv,
)


class JunctionSplitHeatLedgerAndModelGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.heat_audit = read_csv(AGENT462_HEAT_AUDIT)
        cls.patch_rows = build_patch_ledger(read_csv(EXTERNAL_BC_PATCH_CONTRACT), read_csv(WALL_SHELL_TEMPS))
        cls.aggregate_rows = aggregate_patch_ledger(cls.patch_rows, cls.heat_audit)
        cls.case_rows = build_case_admission_rows(
            read_csv(AGENT462_COVERAGE),
            cls.heat_audit,
            read_csv(HEAT_LEDGER_STATUS),
            read_csv(PRESSURE_ADMISSION_SUMMARY),
            {row["case_key"] for row in cls.patch_rows},
        )
        cls.gate_rows = build_model_gate_rows(cls.aggregate_rows, cls.case_rows, read_csv(PRESSURE_ADMISSION_BRANCH))

    def test_physical_bucket_parser(self):
        self.assertEqual(physical_bucket("junction_lower_left_left_stub"), "lower_left")
        self.assertEqual(physical_bucket("ncc_junction_upper_right_lower_start"), "upper_right")

    def test_patch_split_has_salt2_4_cases(self):
        keys = {row["case_key"] for row in self.patch_rows}
        self.assertEqual(keys, {"salt2_mainline", "salt3_mainline", "salt4_mainline"})
        self.assertEqual(len(self.patch_rows), 87)

    def test_split_totals_close_to_agent462_aggregate(self):
        total_rows = [row for row in self.aggregate_rows if row["physical_junction_bucket"] == "case_total_check"]
        self.assertEqual(len(total_rows), 3)
        for row in total_rows:
            split = float(row["realized_external_loss_positive_W"])
            source = float(row["source_aggregate_junction_loss_positive_W"])
            self.assertAlmostEqual(split, source, places=9)

    def test_every_pressure_case_has_heat_admission_row(self):
        keys = {row["case_key"] for row in self.case_rows}
        self.assertEqual(len(keys), 11)
        self.assertIn("val_salt2", keys)
        self.assertIn("salt1_nominal", keys)

    def test_model_gate_blocks_fluid_edit(self):
        gate = {row["gate"]: row["status"] for row in self.gate_rows}
        self.assertEqual(gate["salt2_4_junction_patch_split_available"], "pass")
        self.assertEqual(gate["split_rows_close_to_agent462_aggregate"], "pass")
        self.assertEqual(gate["overall_ready_for_fluid_model_edit"], "fail")


if __name__ == "__main__":
    unittest.main()
