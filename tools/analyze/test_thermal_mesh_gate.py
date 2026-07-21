"""Tests for the Salt2 thermal/closure mesh gate refresh."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_thermal_mesh_gate import build_package, build_thermal_rows


class ThermalMeshGateTests(unittest.TestCase):
    def _write_segment_csv(self, path: Path, rows: list[str]) -> None:
        header = (
            "segment,status,htc_wm2k,uaprime_wmk,Nu,sign_consistent_heated_wall,"
            "nu_direct_admitted,q_sign,wall_duty_Q_w\n"
        )
        path.write_text(header + "".join(rows), encoding="utf-8")

    def test_sign_review_blocks_complete_triplet_rows(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            coarse = root / "coarse.csv"
            medium = root / "medium.csv"
            fine = root / "fine.csv"
            self._write_segment_csv(
                coarse,
                ["upcomer,computed,102,10.2,5.2,False,True,negative_into_fluid_heated,-25\n"],
            )
            self._write_segment_csv(
                medium,
                ["upcomer,computed,100,10.0,5.0,False,True,negative_into_fluid_heated,-24\n"],
            )
            self._write_segment_csv(
                fine,
                ["upcomer,computed,99,9.9,4.9,False,True,negative_into_fluid_heated,-23\n"],
            )

            rows = build_thermal_rows(coarse, medium, fine, 1.5, 1.5)
            htc = next(row for row in rows if row["quantity"] == "HTC")

            self.assertTrue(htc["complete_triplet"])
            self.assertEqual(htc["classification"], "blocked-sign-review")
            self.assertEqual(htc["fit_admissible"], "no")
            self.assertIn("coarse_sign_review_required", str(htc["blockers"]))
            self.assertEqual(htc["gci_status"], "not_publication_gci_sign_review_required")

    def test_downcomer_policy_blocks_noncomputed_segment(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            coarse = root / "coarse.csv"
            medium = root / "medium.csv"
            fine = root / "fine.csv"
            blocked = "downcomer,thermally_blocked_segment_right_leg,,,,False,False,,,-22\n"
            self._write_segment_csv(coarse, [blocked])
            self._write_segment_csv(medium, [blocked])
            self._write_segment_csv(fine, [blocked])

            rows = build_thermal_rows(coarse, medium, fine, 1.5, 1.5)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["classification"], "blocked-downcomer-policy")
            self.assertEqual(rows[0]["fit_admissible"], "no")

    def test_build_package_writes_unified_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            coarse = root / "coarse.csv"
            medium = root / "medium.csv"
            fine = root / "fine.csv"
            coarse_summary = root / "coarse_summary.json"
            medium_summary = root / "medium_summary.json"
            fine_summary = root / "fine_summary.json"
            closure = root / "closure"
            output = root / "out"
            closure.mkdir()

            self._write_segment_csv(
                coarse,
                ["upcomer,computed,102,10.2,5.2,False,True,negative_into_fluid_heated,-25\n"],
            )
            self._write_segment_csv(
                medium,
                ["upcomer,computed,100,10.0,5.0,False,True,negative_into_fluid_heated,-24\n"],
            )
            self._write_segment_csv(
                fine,
                ["upcomer,computed,99,9.9,4.9,False,True,negative_into_fluid_heated,-23\n"],
            )
            for level, path in [
                ("coarse", coarse_summary),
                ("medium", medium_summary),
                ("fine", fine_summary),
            ]:
                smoke = {
                    "decision": f"{level.capitalize()} repair smoke passed: clean reconstructed T.",
                    "section_temperature_sampling": [{"level": level, "gate_pass": True}],
                    "segment_thermal_extraction": [{"level": level, "gate_pass": True}],
                }
                path.write_text(json.dumps(smoke), encoding="utf-8")

            (closure / "closure_qoi_admission_decisions.csv").write_text(
                "case_id,qoi_id,lane,span,method,quantity,numeric_triplet_complete,source_gate,"
                "gci_verdict,gci_trustworthy,publication_ready,admission_decision,blocker,recommended_use\n"
                "salt_2,momentum_corrected_friction::upper_leg,momentum_corrected_friction,upper_leg,"
                "streamwise_momentum_budget_debuoyed,f_corrected,yes,medium_fine_source_rows_admitted,"
                "oscillatory,no,no,blocked_gci_not_trustworthy,computed GCI failed monotonic/asymptotic gate,"
                "treat as diagnostic\n",
                encoding="utf-8",
            )
            (closure / "closure_qoi_triplets.csv").write_text(
                "case_id,qoi_id,lane,span,method,quantity,units,coarse_value,medium_value,fine_value,r21,r32,"
                "numeric_triplet_complete,coarse_source_path,medium_source_path,fine_source_path,"
                "coarse_admission_status,medium_admission_status,fine_admission_status,source_gate,blocker\n"
                "salt_2,momentum_corrected_friction::upper_leg,momentum_corrected_friction,upper_leg,"
                "streamwise_momentum_budget_debuoyed,f_corrected,dimensionless,2.2,2.1,2.15,1.5,1.5,"
                "yes,coarse.csv,medium.csv,fine.csv,admitted,admitted,admitted,medium_fine_source_rows_admitted,\n",
                encoding="utf-8",
            )
            (closure / "closure_qoi_gci_results.csv").write_text(
                "case_id,qoi_id,lane,span,method,quantity,units,coarse,medium,fine,r21,r32,verdict,"
                "order_status,observed_order_p,f_exact_richardson,gci_fine_pct,gci_coarse_pct,"
                "asymptotic_range_ratio,gci_trustworthy,note\n"
                "salt_2,momentum_corrected_friction::upper_leg,momentum_corrected_friction,upper_leg,"
                "streamwise_momentum_budget_debuoyed,f_corrected,dimensionless,2.2,2.1,2.15,1.5,1.5,"
                "oscillatory,ok,1.0,,,,,no,note\n",
                encoding="utf-8",
            )

            summary = build_package(
                coarse,
                medium,
                fine,
                coarse_summary,
                medium_summary,
                fine_summary,
                closure,
                output,
            )

            self.assertEqual(summary["thermal_qoi_row_count"], 3)
            self.assertEqual(summary["closure_qoi_row_count"], 1)
            self.assertEqual(summary["publication_ready_count"], 0)
            self.assertEqual(summary["fit_admissible_admission_count"], 0)
            self.assertTrue((output / "refreshed_qoi_mesh_gate_status.csv").exists())
            self.assertTrue((output / "thermal_admission_table.csv").exists())
            self.assertTrue((output / "thermal_admission_memo.md").exists())
            self.assertIn("blocked-sign-review", (output / "thermal_mesh_gate_qois.csv").read_text())
            self.assertIn("non-monotone/oscillatory", (output / "refreshed_qoi_mesh_gate_status.csv").read_text())
            self.assertIn("internal_Nu_residual_absorption_forbidden", (output / "thermal_admission_table.csv").read_text())


if __name__ == "__main__":
    unittest.main()
