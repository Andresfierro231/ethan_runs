from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_passive_h2_salt1_runtime_unblock_freeze_blind_predict as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PassiveH2Salt1RuntimeUnblockFreezeBlindPredictTests(unittest.TestCase):
    def test_recovers_four_salt1_operator_rows_without_forbidden_flags(self) -> None:
        rows = builder.recovered_operator_rows()
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["source_family"] for row in rows}, {"cooling_branch", "downcomer", "lower_leg", "upcomer"})
        self.assertTrue(all(row["case_id"] == "salt_1" for row in rows))
        self.assertTrue(all(row["external_bc_split_role"] == "train" for row in rows))
        self.assertTrue(all(float(row["hA_W_K"]) > 0.0 for row in rows))
        self.assertTrue(all(row["runtime_wallHeatFlux_used"] is False for row in rows))

    def test_recovery_gate_marks_partial_coverage(self) -> None:
        rows = {row["evidence_item"]: row for row in builder.recovery_provenance_rows()}
        self.assertEqual(rows["salt1_recovered_operator_rows"]["status"], "pass_diagnostic")
        self.assertEqual(rows["passive_source_family_coverage"]["count_or_value"], "4/5")
        self.assertEqual(rows["passive_source_family_coverage"]["release_ready"], False)

    def test_command_manifest_targets_salt1_smoke(self) -> None:
        command = builder.command_rows()[0]["command"]
        self.assertIn("--case-id salt_1", command)
        self.assertIn("passive_h2_radiation_runtime_smoke", command)
        self.assertIn("srun -n 1", command)

    def test_build_outputs_pre_or_post_run_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["salt1_operator_rows"], 4)
            self.assertEqual(summary["salt1_source_family_coverage"], "4/5")
            self.assertFalse(summary["diagnostic_runtime_lock_created"])
            self.assertFalse(summary["admitted_final_freeze_created"])
            self.assertEqual(summary["blind_numeric_prediction_rows_available"], 0)
            for filename in [
                "salt1_recovered_operator_rows_for_fluid.csv",
                "salt1_runtime_target_context.csv",
                "salt1_recovery_provenance_gate.csv",
                "command_manifest.csv",
                "run_salt1_runtime_smoke.sh",
                "salt1_runtime_smoke_status.csv",
                "four_case_runtime_evidence.csv",
                "post_runtime_freeze_gate.csv",
                "coefficient_lock_manifest.csv",
                "blind_prediction_artifact.csv",
                "split_leakage_audit.csv",
                "summary.json",
                "README.md",
            ]:
                self.assertTrue((out / filename).exists(), filename)
            blind = read_rows(out / "blind_prediction_artifact.csv")
            self.assertTrue(all(row["prediction_available"] == "False" for row in blind))


if __name__ == "__main__":
    unittest.main()
