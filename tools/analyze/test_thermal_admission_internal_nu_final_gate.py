"""Tests for the thermal admission/internal-Nu final gate."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_thermal_admission_internal_nu_final_gate import build_package


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ThermalAdmissionInternalNuFinalGateTests(unittest.TestCase):
    def test_package_blocks_internal_nu_fit_and_keeps_validation_rows(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            input_csv = root / "thermal_admission_table.csv"
            sign_csv = root / "sign_convention_table.csv"
            out = root / "out"
            input_csv.write_text(
                "case_id,source_id,segment,qoi,units,admission_class,fit_eligible,validation_use,blockers\n"
                "salt_2,src,lower_leg,wallHeatFlux,W,validation_only,no,yes_diagnostic_only,sign_review\n"
                "salt_2,src,lower_leg,Nu,dimensionless,blocked,no,no,internal_Nu_residual_absorption_forbidden\n"
                "salt_2,src,upcomer,Nu,dimensionless,validation_only,no,yes_diagnostic_only,recirculation_cell_diagnostic_only\n",
                encoding="utf-8",
            )
            sign_csv.write_text(
                "quantity,positive_direction,fit_use,guardrail,source\n"
                "wallHeatFlux_W,heat enters fluid,diagnostic,no qr,source.csv\n",
                encoding="utf-8",
            )

            summary = build_package(input_csv, sign_csv, out)

            self.assertEqual(summary["fit_eligible_row_count"], 0)
            self.assertFalse(summary["forward_v1_internal_nu_fit_allowed"])
            self.assertFalse(summary["radiation_double_count_allowed"])
            rows = read_csv(out / "thermal_admission_internal_nu_final_gate.csv")
            nu_rows = [row for row in rows if row["qoi"] == "Nu"]
            self.assertTrue(all(row["final_fit_eligible"] == "no" for row in nu_rows))
            self.assertEqual(
                {row["forward_v1_use"] for row in nu_rows},
                {"no_internal_nu_fit_use_baseline_or_literature_only"},
            )
            readme = (out / "README.md").read_text(encoding="utf-8")
            self.assertIn("Internal Nu fitting for forward-v1: `no`", readme)

    def test_real_package_counts_match_agent_309_gate(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            summary = build_package(output_dir=Path(tmp))

            self.assertEqual(summary["fit_eligible_row_count"], 0)
            self.assertEqual(summary["validation_only_row_count"], 11)
            self.assertEqual(summary["blocked_row_count"], 5)
            segments = {row["segment"]: row for row in summary["segment_summary"]}
            self.assertEqual(segments["lower_leg"]["validation_only_qoi_count"], 5)
            self.assertEqual(segments["upcomer"]["validation_only_qoi_count"], 6)
            self.assertEqual(segments["downcomer"]["blocked_qoi_count"], 4)

            parsed = json.loads((Path(tmp) / "summary.json").read_text(encoding="utf-8"))
            self.assertFalse(parsed["native_solver_outputs_mutated"])


if __name__ == "__main__":
    unittest.main()
