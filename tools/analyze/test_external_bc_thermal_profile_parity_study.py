#!/usr/bin/env python3
"""Tests for build_external_bc_thermal_profile_parity_study.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_external_bc_thermal_profile_parity_study as study


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ExternalBcThermalProfileParityStudyTests(unittest.TestCase):
    def test_patch_contract_preserves_all_salt_mainline_patch_rows(self) -> None:
        rows = study.patch_contract_rows()
        self.assertEqual(len(rows), 207)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(
            {sum(1 for row in rows if row["case_id"] == case_id) for case_id in {"salt_2", "salt_3", "salt_4"}},
            {69},
        )

    def test_segment_contract_and_source_sink_counts(self) -> None:
        segment_rows = study.segment_equivalent_rows()
        source_sink_rows = study.source_sink_contract_rows()
        self.assertEqual(len(segment_rows), 24)
        self.assertEqual(len(source_sink_rows), 12)
        self.assertIn("include_rcExternalTemperature", " ".join(row["setup_radiation_policy"] for row in segment_rows))
        self.assertTrue(
            all(
                "do_not_add_radiation" in row["realized_flux_replay_policy"]
                for row in segment_rows
            )
        )

    def test_heat_loss_comparison_covers_five_legs_per_case(self) -> None:
        rows = study.heat_loss_comparison_rows()
        self.assertEqual(len(rows), 15)
        for case_id in {"salt_2", "salt_3", "salt_4"}:
            legs = {row["leg"] for row in rows if row["case_id"] == case_id}
            self.assertEqual(legs, {"lower_leg", "upcomer", "cooling_branch", "downcomer", "junction"})
        junction_rows = [row for row in rows if row["leg"] == "junction"]
        self.assertTrue(all(row["heat_loss_bias"] == "model_under_loses_heat" for row in junction_rows))
        self.assertTrue(all("junction_stub" in row["likely_root_cause"] for row in junction_rows))

    def test_drive_rows_are_diagnostic_and_split_aware(self) -> None:
        rows = study.drive_comparison_rows()
        self.assertEqual(len(rows), 15)
        self.assertEqual({row["validation_split_role"] for row in rows}, {"train", "validation", "holdout"})
        self.assertTrue(all(row["admission_status"].startswith(("diagnostic_only", "blocked")) for row in rows))
        self.assertTrue(any("wall_adjacent" in row["recommended_next_model"] for row in rows))

    def test_build_package_outputs_docs_and_summary_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = study.build_package(out)
            self.assertEqual(summary["task"], "AGENT-365")
            self.assertFalse(summary["predictive_hx_admitted"])
            self.assertFalse(summary["internal_nu_closure_admitted"])
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["heavy_openfoam_run"])
            self.assertFalse(summary["external_fluid_modified"])

            expected = {
                "README.md",
                "methodology_and_assumptions.md",
                "equations_and_sign_conventions.md",
                "presentation_brief.md",
                "repeatability_and_refinement_guide.md",
                "thesis_reuse_index.md",
                "external_bc_patch_contract.csv",
                "external_bc_segment_equivalents.csv",
                "source_sink_parity_contract.csv",
                "section_heat_loss_comparison.csv",
                "thermal_profile_drive_comparison.csv",
                "case_summary.csv",
                "model_change_recommendations.csv",
                "admission_decision_table.csv",
                "source_manifest.csv",
                "summary.json",
            }
            for name in expected:
                self.assertTrue((out / name).exists(), name)

            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["publication_ready_predictive_heat_loss_rows"], 0)

    def test_docs_carry_stale_radiation_correction_and_refinement_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            study.build_package(out)
            readme = (out / "README.md").read_text(encoding="utf-8")
            guide = (out / "repeatability_and_refinement_guide.md").read_text(encoding="utf-8")
            thesis = (out / "thesis_reuse_index.md").read_text(encoding="utf-8")

            self.assertIn("old assumption that CFD has no radiation is superseded", readme)
            self.assertIn("do not add separate 1D radiation", readme)
            self.assertIn("python3.11 tools/analyze/build_external_bc_thermal_profile_parity_study.py", guide)
            self.assertIn("Do not use realized CFD wallHeatFlux", guide)
            self.assertIn("not final predictive-HX scoring", thesis)

    def test_output_csv_row_counts(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            study.build_package(out)
            self.assertEqual(len(read_csv(out / "external_bc_patch_contract.csv")), 207)
            self.assertEqual(len(read_csv(out / "external_bc_segment_equivalents.csv")), 24)
            self.assertEqual(len(read_csv(out / "source_sink_parity_contract.csv")), 12)
            self.assertEqual(len(read_csv(out / "section_heat_loss_comparison.csv")), 15)
            self.assertEqual(len(read_csv(out / "thermal_profile_drive_comparison.csv")), 15)
            self.assertEqual(len(read_csv(out / "case_summary.csv")), 3)
            self.assertEqual(len(read_csv(out / "admission_decision_table.csv")), 5)


if __name__ == "__main__":
    unittest.main()
