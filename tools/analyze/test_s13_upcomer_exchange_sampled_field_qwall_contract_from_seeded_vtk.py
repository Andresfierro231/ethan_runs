from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SampledFieldQwallContractTests(unittest.TestCase):
    def test_source_files_and_geometry_mappings_are_ready(self) -> None:
        cases = builder.case_rows()
        sources = builder.build_source_file_availability(cases)
        mapping = builder.build_face_to_cell_mapping_preflight(cases)

        self.assertEqual(len(cases), 3)
        self.assertEqual(len(mapping), 6)
        self.assertTrue(all(row["contract_status"] == "ready_read_only" for row in sources))
        self.assertTrue(all(row["mapping_status"] == "ready_for_contract_extraction_not_run" for row in mapping))
        self.assertEqual({row["face_count"] for row in mapping}, {"38880"})

    def test_field_matrix_opens_only_limited_sampling(self) -> None:
        fields = builder.build_field_availability_matrix()
        by_field = {}
        for row in fields:
            by_field.setdefault(row["field_or_property"], set()).add(row["contract_status"])

        self.assertEqual(by_field["U"], {"geometry_ready_whole_mesh_field_present_surface_sampling_not_run"})
        self.assertIn("geometry_ready_whole_mesh_field_present_surface_sampling_not_run", by_field["T"])
        self.assertEqual(by_field["rho"], {"geometry_ready_whole_mesh_field_present_surface_sampling_not_run"})
        self.assertEqual(by_field["p_or_p_rgh"], {"blocked_missing_pressure_basis"})
        self.assertEqual(by_field["wallHeatFlux"], {"blocked_missing_wallHeatFlux_Q_wall"})
        self.assertEqual(by_field["mu_or_nu"], {"blocked_missing_mu_or_nu_basis"})
        self.assertEqual(by_field["cp_J_kg_K"], {"blocked_missing_cp_property_contract"})

    def test_qwall_and_cp_remain_blocked(self) -> None:
        cases = builder.case_rows()
        qwall = builder.build_wall_heat_integration_contract(cases)
        sign_cp = builder.build_sign_cp_convention_contract(cases)

        self.assertEqual(len(qwall), 3)
        self.assertTrue(all(row["contract_status"] == "blocked_missing_wallHeatFlux" for row in qwall))
        self.assertTrue(all(row["Q_wall_W_released"] == "false" for row in qwall))
        self.assertTrue(all(row["cp_released"] == "false" for row in sign_cp))
        self.assertTrue(all(row["default_cp_allowed"] == "false" for row in sign_cp))

    def test_scheduler_decision_is_per_case_limited_and_nonharvest(self) -> None:
        rows = builder.build_sampled_field_scheduler_decision(builder.case_rows())
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["decision"] for row in rows}, {"open_limited_nonharvest_field_sampling"})
        self.assertEqual({row["allowed"] for row in rows}, {"true"})
        for row in rows:
            self.assertIn("no Q_wall_W release", row["explicitly_forbidden_scope"])
            self.assertIn("no production harvest", row["explicitly_forbidden_scope"])
            self.assertIn("no coefficient admission", row["explicitly_forbidden_scope"])

    def test_s13_and_s12_impacts_are_per_case_and_trigger_closed(self) -> None:
        cases = builder.case_rows()
        s13 = builder.build_s13_unlock_impact(cases)
        s12 = builder.build_s12_unlock_impact(cases)
        combined = builder.build_unlock_impact(cases)

        self.assertEqual(len(s13), 3)
        self.assertEqual(len(s12), 3)
        self.assertEqual(len(combined), 6)
        self.assertEqual({row["s13_candidate_or_admission_trigger_allowed"] for row in s13}, {"false"})
        self.assertEqual({row["s12_trigger_allowed"] for row in s12}, {"false"})
        self.assertEqual({row["target"] for row in combined}, {"S13", "S12"})
        self.assertEqual({row["trigger_allowed"] for row in combined}, {"false"})

    def test_build_package_writes_contract_and_keeps_harvest_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            payload = builder.build_package(out)
            summary = payload["summary"]

            self.assertEqual(summary["case_count"], 3)
            self.assertEqual(summary["ready_source_file_rows"], summary["source_file_rows"])
            self.assertEqual(summary["ready_face_mapping_rows"], 6)
            self.assertEqual(summary["limited_sampled_field_lanes_open"], 12)
            self.assertEqual(summary["blocked_pressure_rows"], 3)
            self.assertEqual(summary["blocked_wallHeatFlux_rows"], 3)
            self.assertEqual(summary["blocked_mu_rows"], 3)
            self.assertEqual(summary["blocked_cp_rows"], 3)
            self.assertEqual(summary["Q_wall_W_released_rows"], 0)
            self.assertEqual(summary["scheduler_authorized_sampled_field_rows_open"], 3)
            self.assertEqual(summary["s13_unlock_rows"], 3)
            self.assertEqual(summary["s12_unlock_rows"], 3)
            self.assertTrue(summary["limited_scheduler_sampled_field_row_open"])
            self.assertFalse(summary["Q_wall_W_extraction_allowed"])
            self.assertFalse(summary["sampler_refresh_allowed"])
            self.assertFalse(summary["production_harvest_allowed"])
            self.assertFalse(summary["s11_s12_s15_s6_trigger"])

            for name in [
                "README.md",
                "summary.json",
                "source_file_availability.csv",
                "field_availability_matrix.csv",
                "face_to_cell_mapping_preflight.csv",
                "sign_cp_convention_contract.csv",
                "wall_heat_integration_contract.csv",
                "extraction_input_contract.csv",
                "sampler_refresh_gate.csv",
                "sampled_field_scheduler_decision.csv",
                "s13_unlock_impact.csv",
                "s12_unlock_impact.csv",
                "s13_s12_unlock_impact.csv",
                "downstream_gate.csv",
                "no_mutation_guardrails.csv",
                "source_manifest.csv",
            ]:
                self.assertTrue((out / name).exists(), name)

            gates = read_rows(out / "sampler_refresh_gate.csv")
            gate_by_name = {row["gate"]: row for row in gates}
            self.assertEqual(gate_by_name["limited_scheduler_sampled_field_extraction"]["allowed"], "true")
            self.assertEqual(gate_by_name["sampler_manifest_refresh"]["allowed"], "false")
            self.assertEqual(gate_by_name["production_harvest_or_same_qoi_uq"]["allowed"], "false")

            impacts = read_rows(out / "s13_s12_unlock_impact.csv")
            self.assertEqual({row["trigger_allowed"] for row in impacts}, {"false"})
            self.assertEqual(len(read_rows(out / "s13_unlock_impact.csv")), 3)
            self.assertEqual(len(read_rows(out / "s12_unlock_impact.csv")), 3)


if __name__ == "__main__":
    unittest.main()
