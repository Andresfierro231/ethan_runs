from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.analyze import build_fluid_temperature_periodicity_bracket_repair as mod


class FluidTemperaturePeriodicityBracketRepairTests(unittest.TestCase):
    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_bracket_from_samples_finds_sign_change(self) -> None:
        samples = [
            {"T0_K": 550.0, "residual_K": 2.0},
            {"T0_K": 553.0, "residual_K": -0.5},
            {"T0_K": 560.0, "residual_K": -2.0},
        ]

        bracket = mod.bracket_from_samples(samples)

        self.assertIsNotNone(bracket)
        assert bracket is not None
        self.assertEqual(bracket[0]["T0_K"], 550.0)
        self.assertEqual(bracket[1]["T0_K"], 553.0)

    def test_classify_repair_marks_upper_bound_recovery(self) -> None:
        bracket = ({"T0_K": 550.0, "residual_K": 1.0}, {"T0_K": 552.0, "residual_K": -0.1})

        status, patch_required, expansion = mod.classify_repair(550.0, bracket)

        self.assertEqual(status, "upper_bound_too_low_root_recovered")
        self.assertTrue(patch_required)
        self.assertEqual(expansion, 2.0)

    def test_classify_repair_keeps_current_bracket(self) -> None:
        bracket = ({"T0_K": 545.0, "residual_K": 1.0}, {"T0_K": 548.0, "residual_K": -0.1})

        status, patch_required, expansion = mod.classify_repair(550.0, bracket)

        self.assertEqual(status, "already_bracketed_by_current_bounds")
        self.assertFalse(patch_required)
        self.assertEqual(expansion, 0.0)

    def test_validate_existing_rejects_missing_recovered_rows(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="temp-bracket-audit-")
        self.addCleanup(tmp.cleanup)
        out_dir = Path(tmp.name)
        out_dir.mkdir(parents=True, exist_ok=True)
        mod.write_csv(
            out_dir / "temperature_root_bound_audit.csv",
            [
                {
                    "case_id": "salt_2",
                    "candidate_id": "UMX1_disabled_baseline",
                    "repair_status": "already_bracketed_by_current_bounds",
                    "bracket_found": "true",
                }
            ],
            mod.AUDIT_COLUMNS,
        )
        for filename, columns in [
            ("temperature_root_sweep.csv", mod.SWEEP_COLUMNS),
            ("prior_rejected_root_context.csv", mod.PRIOR_COLUMNS),
            ("root_repair_decision.csv", mod.DECISION_COLUMNS),
            ("fluid_patch_contract.csv", mod.PATCH_CONTRACT_COLUMNS),
            ("source_manifest.csv", ["source_type", "path", "used_for", "mutation_status"]),
        ]:
            mod.write_csv(out_dir / filename, [], columns)
        (out_dir / "summary.json").write_text(
            json.dumps({"umx1_rows_audited": 1}) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "did not recover"):
            mod.validate_existing(out_dir)


if __name__ == "__main__":
    unittest.main()
