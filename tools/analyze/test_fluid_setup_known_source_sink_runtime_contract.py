import csv
import json
import unittest

from tools.analyze import build_fluid_setup_known_source_sink_runtime_contract as builder


class SetupKnownSourceSinkContractTests(unittest.TestCase):
    def test_build_outputs_contract_without_admission(self) -> None:
        summary = builder.build()
        self.assertEqual(summary["runtime_admitted_rows"], 0)
        self.assertFalse(summary["external_fluid_mutation"])
        with (builder.PACKAGE / "setup_known_source_contract.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2"})
        self.assertEqual({row["scenario_value"] for row in rows}, {"tw4_to_tp3_three_span"})
        self.assertEqual({row["runtime_admitted_now"] for row in rows}, {"False"})

    def test_runtime_audit_keeps_forbidden_inputs_out(self) -> None:
        builder.build()
        with (builder.PACKAGE / "runtime_leakage_audit.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreaterEqual(len(rows), 6)
        self.assertEqual({row["status"] for row in rows}, {"forbidden"})
        summary = json.loads((builder.PACKAGE / "summary.json").read_text())
        self.assertEqual(summary["validation_rows_consumed"], 0)
        self.assertEqual(summary["holdout_rows_consumed"], 0)
        self.assertEqual(summary["external_test_rows_consumed"], 0)


if __name__ == "__main__":
    unittest.main()
