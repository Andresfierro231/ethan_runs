"""Tests for build_math_theory_results_register.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_math_theory_results_register as register


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class MathTheoryResultsRegisterTests(unittest.TestCase):
    def build_tmp(self) -> Path:
        out = Path(tempfile.mkdtemp(prefix="math_theory_register_"))
        register.build_package(out)
        return out

    def test_core_equation_ids_exist(self) -> None:
        out = self.build_tmp()
        equations = {row["equation_id"]: row for row in read_csv(out / "equation_register.csv")}
        for equation_id in {
            "loop_pressure_root",
            "distributed_pressure_loss",
            "minor_or_component_loss",
            "segment_heat_balance",
            "internal_convection",
            "radiation_boundary",
            "hx_ua_or_epsilon_ntu",
            "gci_admission_formula",
            "post_solve_score_residual",
        }:
            self.assertIn(equation_id, equations)

    def test_predictive_runtime_hygiene_is_explicit(self) -> None:
        out = self.build_tmp()
        assumptions = {row["assumption_id"]: row for row in read_csv(out / "assumption_register.csv")}
        hygiene = assumptions["predictive_runtime_hygiene"]
        self.assertIn("CFD mdot", hygiene["assumption"])
        self.assertIn("realized CFD wallHeatFlux", hygiene["assumption"])
        self.assertIn("Targets join only after solve", hygiene["default_policy"])

    def test_result_contract_requires_admission_split_and_sources(self) -> None:
        out = self.build_tmp()
        fields = {row["field_name"]: row for row in read_csv(out / "result_intake_contract.csv")}
        for field in {
            "split_role",
            "model_mode",
            "forbidden_runtime_inputs_used",
            "property_mode",
            "equation_ids",
            "fit_source_rows",
            "admission_status",
            "source_paths",
            "do_not_claim",
        }:
            self.assertEqual(fields[field]["required"], "yes")

    def test_current_hooks_keep_proxy_and_blocked_boundaries(self) -> None:
        out = self.build_tmp()
        hooks = {row["area"]: row for row in read_csv(out / "current_evidence_hooks.csv")}
        self.assertEqual(hooks["h1_hydraulic_proxy"]["current_status"], "diagnostic_proxy")
        self.assertEqual(hooks["thermal_mesh_admission"]["current_status"], "blocked")
        self.assertIn("0 fit-admissible thermal rows", hooks["thermal_mesh_admission"]["current_result"])

    def test_summary_and_readme_are_consistent(self) -> None:
        out = self.build_tmp()
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["task_id"], "AGENT-322")
        self.assertGreaterEqual(summary["n_equations"], 12)
        self.assertFalse(summary["native_solver_outputs_mutated"])
        self.assertFalse(summary["external_fluid_modified"])
        readme = (out / "README.md").read_text(encoding="utf-8")
        self.assertIn("not progress by tuning one global coefficient", readme)
        self.assertIn("Sensor temperatures are validation targets only", readme)


if __name__ == "__main__":
    unittest.main()
