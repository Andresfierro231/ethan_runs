from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from tools.analyze.build_internal_nu_blocker_progress_integration import OUT, build


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class InternalNuBlockerProgressIntegrationTests(unittest.TestCase):
    def test_builds_expected_outputs(self) -> None:
        summary = build()
        self.assertEqual(summary["task"], "AGENT-345")
        self.assertEqual(summary["fit_admissible_internal_nu_rows"], 0)
        for name in summary["outputs"]:
            self.assertTrue((OUT / name).exists(), name)

    def test_covers_all_current_open_blockers(self) -> None:
        build()
        rows = read_csv(OUT / "blocker_progress_matrix.csv")
        blocker_ids = {row["blocker_id"] for row in rows}
        self.assertEqual(
            blocker_ids,
            {
                "closure-qoi-mesh-gci",
                "thermal-cfd-1d-parity",
                "predictive-heater-cooler-wall-submodels",
                "upcomer-onset-data-sparsity",
                "fluid-external-boundary-api-gap",
                "f6-friction-re-correction",
            },
        )
        self.assertTrue(all(row["status"].startswith("open") for row in rows))

    def test_assumptions_capture_guardrails(self) -> None:
        build()
        rows = read_csv(OUT / "assumptions_methods_process.csv")
        assumptions = {row["assumption_id"]: row for row in rows}
        for assumption_id in {
            "zero_fit_internal_nu",
            "radiation_embedded_no_qr",
            "geometric_plane_normal",
            "residual_ownership_before_nu_fit",
        }:
            self.assertIn(assumption_id, assumptions)
        self.assertIn("no separate exported qr", assumptions["radiation_embedded_no_qr"]["assumption"])
        self.assertIn("not mean-velocity", assumptions["geometric_plane_normal"]["assumption"])

    def test_admission_decisions_keep_diagnostic_nu_out_of_fit(self) -> None:
        build()
        rows = read_csv(OUT / "admission_decision_table.csv")
        diagnostic = next(row for row in rows if row["decision_id"] == "nu_section_effective_upcomer_diagnostic")
        self.assertIn("diagnostic_only", diagnostic["current_classification"])
        self.assertIn("fit_admissible_Nu", diagnostic["forbidden_use"])
        forward = next(row for row in rows if row["decision_id"] == "forward_v1_internal_nu_consumption")
        self.assertIn("blocked_no_go", forward["current_classification"])

    def test_next_actions_are_executable_and_prioritized(self) -> None:
        build()
        rows = read_csv(OUT / "next_workstream_actions.csv")
        actions = {row["action_id"]: row for row in rows}
        self.assertIn("run_compute_node_matched_plane_sampling", actions)
        self.assertIn("harvest_corrected_q_terminal_rows", actions)
        self.assertEqual(actions["run_compute_node_matched_plane_sampling"]["priority"], "P1")
        self.assertEqual(actions["harvest_corrected_q_terminal_rows"]["priority"], "P2")
        self.assertIn("active AGENT-344", actions["run_compute_node_matched_plane_sampling"]["blocked_by"])

    def test_readme_documents_zero_fit_and_stale_blocker_policy(self) -> None:
        build()
        text = (OUT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Current fit-admissible internal-Nu rows remain `0`", text)
        self.assertIn("does not reopen stale blockers", text)
        self.assertIn("OF13 reconstruction works, mesh families exist", text)
        self.assertIn("Generated index refresh is intentionally left untouched", text)

    def test_import_records_no_native_or_external_mutation(self) -> None:
        build()
        payload = json.loads(
            Path("imports/2026-07-14_internal_nu_blocker_progress_integration.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(payload["native_cfd_outputs_mutated"])
        self.assertFalse(payload["external_cfd_modeling_tools_mutated"])
        self.assertEqual(payload["fit_admissible_internal_nu_rows"], 0)


if __name__ == "__main__":
    unittest.main()
