from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_umx1_dry_smoke_scorer as mod


class UMX1DrySmokeScorerTests(unittest.TestCase):
    def rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def build_tmp(self) -> Path:
        tmp = tempfile.TemporaryDirectory(prefix="umx1-smoke-")
        self.addCleanup(tmp.cleanup)
        out_dir = Path(tmp.name)
        mod.build_dry(out_dir)
        return out_dir

    def test_candidate_grid_is_fixed_and_no_admission(self) -> None:
        out_dir = self.build_tmp()
        rows = self.rows(out_dir / "umx1_candidate_definitions.csv")

        self.assertEqual(
            [row["candidate_id"] for row in rows],
            ["UMX1_disabled_baseline", "UMX1_exchange_0p01", "UMX1_exchange_0p05"],
        )
        self.assertTrue(all(row["fit_allowed"] == "false" for row in rows))
        self.assertTrue(all(row["model_selection_allowed"] == "false" for row in rows))
        self.assertTrue(all(row["admission_status"] == "not_admitted_smoke_only" for row in rows))

    def test_split_contract_executes_salt234_and_blocks_salt1(self) -> None:
        out_dir = self.build_tmp()
        rows = self.rows(out_dir / "umx1_case_split_contract.csv")
        executable = [row for row in rows if row["executable_in_smoke"] == "true"]
        salt1 = [row for row in rows if row["case_key"] == "salt1_nominal"]

        self.assertEqual({row["case_id"] for row in executable}, {"salt_2", "salt_3", "salt_4"})
        self.assertEqual(len(executable), 3)
        self.assertEqual(salt1[0]["executable_status"], "blocked_schema_promotion_missing")
        self.assertTrue(all(row["fit_allowed"] == "false" for row in rows))
        self.assertTrue(all(row["model_selection_allowed"] == "false" for row in rows))

    def test_runtime_audit_forbids_target_and_cfd_runtime_inputs(self) -> None:
        out_dir = self.build_tmp()
        rows = self.rows(out_dir / "umx1_runtime_input_audit.csv")
        forbidden = [row for row in rows if row["runtime_field"] in mod.FORBIDDEN_RUNTIME_FIELDS]

        self.assertGreater(len(forbidden), 0)
        self.assertTrue(all(row["runtime_allowed"] == "false" for row in forbidden))
        self.assertTrue(all(row["audit_status"] == "pass_absent" for row in forbidden))
        self.assertFalse(any(row["runtime_field"] == "imposed_qhx_W" and row["runtime_value"] for row in rows))

    def test_scenario_contract_uses_predictive_hx_and_umx_fields(self) -> None:
        out_dir = self.build_tmp()
        rows = self.rows(out_dir / "umx1_scenario_contracts.csv")

        self.assertEqual(len(rows), 9)
        self.assertTrue(all(row["model_mode"] == "predictive_airside_hx" for row in rows))
        self.assertTrue(all(row["imposed_qhx_W"] == "" for row in rows))
        self.assertEqual(
            {row["upcomer_mixing_mode"] for row in rows},
            {"disabled", "energy_conserving_exchange_v1"},
        )

    def test_validate_existing_accepts_dry_package(self) -> None:
        out_dir = self.build_tmp()
        summary = mod.validate_existing(out_dir)

        self.assertEqual(summary["status"], "dry_contract_ready")
        self.assertEqual(summary["planned_smoke_rows"], 9)
        self.assertEqual(summary["admission_status"], "not_admitted_smoke_only")

    def test_validate_existing_rejects_stale_smoke_summary(self) -> None:
        out_dir = self.build_tmp()
        smoke_row = {
            "case_id": "salt_2",
            "fluid_case_name": "salt_test_2_jin",
            "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "candidate_id": "UMX1_disabled_baseline",
            "scenario_name": "salt_2__UMX1_disabled_baseline",
            "engine": "fast_scan",
            "root_status": "fast_scan_bracketed_pressure_root",
            "accepted_for_validation": "true",
            "mdot_kg_s": "0.1",
            "pressure_residual_Pa": "0",
            "temperature_periodicity_error_K": "0",
            "admission_status": "not_admitted_smoke_only",
        }
        root_row = {
            "case_id": "salt_2",
            "candidate_id": "UMX1_disabled_baseline",
            "engine": "fast_scan",
            "root_status": "fast_scan_bracketed_pressure_root",
            "accepted_for_validation": "true",
            "pressure_residual_Pa": "0",
            "temperature_periodicity_error_K": "0",
            "root_gate_status": "pass",
            "notes": "synthetic validation fixture",
        }
        conservation_row = {
            "case_id": "salt_2",
            "candidate_id": "UMX1_disabled_baseline",
            "engine": "fast_scan",
            "active_umx_segment_count": "0",
            "finite_temperature_count": "0",
            "max_abs_reservoir_energy_residual_W": "0",
            "net_exchange_residual_W": "0",
            "conservation_gate_status": "pass_noop",
            "notes": "synthetic validation fixture",
        }
        mod.write_csv(out_dir / "umx1_smoke_results.csv", [smoke_row], mod.RESULT_COLUMNS)
        mod.write_csv(out_dir / "umx1_root_status_by_case.csv", [root_row], mod.ROOT_COLUMNS)
        mod.write_csv(out_dir / "umx1_conservation_ledger.csv", [conservation_row], mod.CONSERVATION_COLUMNS)

        with self.assertRaisesRegex(ValueError, "summary.json is stale"):
            mod.validate_existing(out_dir)

        refreshed = mod.refresh_summary(out_dir)
        self.assertEqual(refreshed["smoke_result_rows"], 1)
        self.assertEqual(mod.validate_existing(out_dir)["status"], "fast_scan_smoke_complete")

    def test_summary_json_is_valid(self) -> None:
        out_dir = self.build_tmp()
        payload = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["task_id"], "AGENT-544")
        self.assertEqual(payload["salt1_status"], "blocked_schema_promotion_missing")


if __name__ == "__main__":
    unittest.main()
