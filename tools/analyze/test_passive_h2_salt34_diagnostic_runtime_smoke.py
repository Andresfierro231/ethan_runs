from __future__ import annotations

import csv
import unittest
from pathlib import Path

from tools.analyze import build_passive_h2_salt34_diagnostic_runtime_smoke as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt34DiagnosticRuntimeSmokeTests(unittest.TestCase):
    def test_inputs_preserve_diagnostic_scope(self) -> None:
        builder.build()
        rows = read_rows(builder.OPERATOR_INPUT)
        self.assertEqual(len(rows), 10)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_3", "salt_4"})
        self.assertEqual({row["external_bc_split_role"] for row in rows}, {"train"})
        self.assertEqual({row["source_property_release"] for row in rows}, {"False"})

    def test_case_outputs_complete_after_srun(self) -> None:
        summary = builder.build()
        self.assertEqual(
            summary["decision"],
            "passive_h2_salt34_diagnostic_runtime_smoke_complete_no_release_no_score",
        )
        self.assertEqual(summary["completed_case_rows"], 2)
        self.assertEqual(summary["accepted_root_case_rows"], 2)
        self.assertEqual(summary["nonzero_radiation_case_rows"], 2)
        self.assertFalse(summary["protected_scoring"])
        self.assertFalse(summary["candidate_freeze"])

    def test_release_gates_keep_scoring_closed(self) -> None:
        builder.build()
        gates = read_rows(builder.OUT / "release_gate_matrix.csv")
        by_gate = {row["gate"]: row for row in gates}
        self.assertEqual(by_gate["Salt3_Salt4_diagnostic_runtime_outputs"]["ready_now"], "true")
        self.assertEqual(by_gate["accepted_runtime_roots"]["ready_now"], "true")
        self.assertEqual(by_gate["nonzero_radiation_movement"]["ready_now"], "true")
        self.assertEqual(by_gate["protected_scoring"]["ready_now"], "false")
        self.assertEqual(by_gate["source_property_release"]["ready_now"], "false")


if __name__ == "__main__":
    unittest.main()
