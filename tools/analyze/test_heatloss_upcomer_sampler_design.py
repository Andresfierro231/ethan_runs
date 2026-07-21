#!/usr/bin/env python3
"""Tests for the heat-loss upcomer sampler design package."""

from __future__ import annotations

import csv
import unittest

from tools.analyze import build_heatloss_upcomer_sampler_design as design


class HeatlossUpcomerSamplerDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = design.build()
        cls.schema = cls.read_csv("sampler_output_schema.csv")
        cls.algorithm = cls.read_csv("algorithm_contract.csv")
        cls.dry_run = cls.read_csv("dry_run_emission_matrix.csv")
        cls.execution = cls.read_csv("execution_preflight_cases.csv")
        cls.validation = cls.read_csv("validation_cases.csv")

    @classmethod
    def read_csv(cls, name: str) -> list[dict[str, str]]:
        with (design.OUT / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_required_output_fields_are_present(self) -> None:
        fields = {row["output_field"] for row in self.schema}
        for required in {
            "V_recirc_m3",
            "mdot_exchange_kg_s",
            "tau_recirc_s",
            "T_main_K",
            "T_recirc_K",
            "wall_core_delta_T_K",
            "pressure_residual_Pa",
            "energy_residual_W",
            "same_qoi_uq_status",
        }:
            self.assertIn(required, fields)

    def test_schema_preserves_runtime_and_residual_guards(self) -> None:
        self.assertTrue(all(row["predictive_runtime_input"] == "false" for row in self.schema))
        self.assertTrue(all(row["admission_use_now"] == "diagnostic_only" for row in self.schema))
        self.assertTrue(
            all(row["residual_policy"] == "do_not_hide_heat_residual_in_internal_Nu" for row in self.schema)
        )

    def test_algorithm_contract_has_fail_closed_stages(self) -> None:
        stages = {row["stage"] for row in self.algorithm}
        for stage in {
            "case_window_lock",
            "recirculation_mask_and_volume",
            "exchange_rate_and_residence_time",
            "thermal_state",
            "pressure_residual_basis",
            "wall_source_and_energy_residual",
            "same_qoi_uq_hook",
            "runtime_and_admission_guard",
        }:
            self.assertIn(stage, stages)
        self.assertTrue(all(row["blocked_behavior"] for row in self.algorithm))

    def test_dry_run_matrix_covers_three_cases_without_launch(self) -> None:
        self.assertEqual({row["case_id"] for row in self.dry_run}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(len(self.dry_run), 3 * len(self.schema))
        self.assertTrue(all(row["launch_allowed_from_this_package"] == "false" for row in self.dry_run))
        self.assertTrue(all(row["dry_run_status"] == "schema_defined_no_value_emitted" for row in self.dry_run))

    def test_execution_preflight_keeps_compute_for_later_row(self) -> None:
        self.assertEqual({row["time_window_s"] for row in self.execution}, {"7915", "7618", "10000"})
        self.assertTrue(all(row["launch_allowed_from_this_package"] == "false" for row in self.execution))
        self.assertTrue(all("sbatch_or_srun" in row["scheduler_policy"] for row in self.execution))

    def test_validation_cases_cover_residual_and_uq_guards(self) -> None:
        test_ids = {row["test_id"] for row in self.validation}
        self.assertIn("residual_lane_guard", test_ids)
        self.assertIn("same_qoi_uq_guard", test_ids)

    def test_summary_reports_no_side_effects(self) -> None:
        self.assertFalse(self.summary["any_fit_or_score_allowed_now"])
        self.assertFalse(self.summary["residual_absorbed_into_internal_Nu"])
        for key in (
            "native_output_mutation",
            "registry_mutation",
            "scheduler_mutation",
            "solver_or_postprocessing_or_sampler_launched",
            "tools_extract_edit",
            "fluid_edit",
            "external_repo_edit",
            "fitting_or_model_selection",
            "closure_admission_change",
            "blocker_register_change",
            "generated_index_refresh",
        ):
            self.assertFalse(self.summary[key])


if __name__ == "__main__":
    unittest.main()
