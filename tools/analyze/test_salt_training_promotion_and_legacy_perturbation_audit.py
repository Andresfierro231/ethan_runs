from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_salt_training_promotion_and_legacy_perturbation_audit import (
    build_salt_training_promotion_and_legacy_perturbation_audit,
)


class SaltTrainingPromotionAuditTests(unittest.TestCase):
    def test_pm5_split_override_matches_user_policy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-training-audit-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt_training_promotion_and_legacy_perturbation_audit(out_dir)

            self.assertFalse(summary["matched_pressure_upcomer_pm5_submitted"])
            rows = self._rows_by(out_dir / "pm5_perturbed_q_split_override.csv", "source_case_key")
            self.assertEqual(rows["salt2_jin_lo5q_corrected"]["requested_split_role"], "holdout")
            self.assertEqual(rows["salt2_jin_hi5q_corrected"]["requested_split_role"], "holdout")
            self.assertEqual(rows["salt4_jin_lo5q_corrected"]["requested_split_role"], "training")
            self.assertEqual(rows["salt4_jin_hi5q_corrected"]["requested_split_role"], "training")
            self.assertEqual(rows["salt4_jin_hi5q_corrected"]["training_or_holdout_admission"], "admitted_for_requested_split_role")

    def test_legacy_hiins_is_not_labeled_high_insulation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-training-audit-") as tmpdir:
            out_dir = Path(tmpdir)
            build_salt_training_promotion_and_legacy_perturbation_audit(out_dir)

            rows = self._rows_by(out_dir / "legacy_perturbation_label_audit.csv", "case_key")
            salt4 = rows["salt4_jin_hiq_hiins"]
            self.assertIn("baseline-insulation", salt4["trusted_physics_label"])
            self.assertEqual(salt4["insulation_delta_in"], "0.00")
            self.assertEqual(salt4["split_decision"], "sensitivity_only_until_operating_point_gate_override")

            salt3 = rows["salt3_jin_hiq_hiins"]
            self.assertEqual(salt3["split_decision"], "not_training_needs_continuation")
            self.assertIn("heat still drifting", salt3["training_use_decision"])

    def test_outputs_and_manifest_exist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-training-audit-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt_training_promotion_and_legacy_perturbation_audit(out_dir)
            for filename in summary["required_outputs"]:
                self.assertTrue((out_dir / filename).exists(), filename)

            manifest = self._read_rows(out_dir / "source_manifest.csv")
            inputs = [row for row in manifest if row["role"] == "read_only_input"]
            self.assertTrue(inputs)
            self.assertTrue(all(row["exists"] == "True" for row in inputs), inputs)

    @staticmethod
    def _read_rows(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    @classmethod
    def _rows_by(cls, path: Path, key: str) -> dict[str, dict[str, str]]:
        return {row[key]: row for row in cls._read_rows(path)}


if __name__ == "__main__":
    unittest.main()
