from __future__ import annotations

import csv
import unittest
from pathlib import Path

from tools.analyze.build_upcomer_internal_nu_extraction_contract import OUT, build


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class UpcomerInternalNuExtractionContractTests(unittest.TestCase):
    def test_builds_expected_outputs(self) -> None:
        summary = build()
        self.assertEqual(summary["task"], "AGENT-339")
        self.assertEqual(summary["decision"], "contract_only_current_fit_admissible_upcomer_Nu_rows_remain_zero")
        for name in summary["outputs"]:
            self.assertTrue((OUT / name).exists(), name)

    def test_extraction_contract_has_all_required_metrics_and_planes(self) -> None:
        build()
        rows = read_csv(OUT / "upcomer_extraction_contract.csv")
        required_metrics = {
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "mass_flux_weighted_bulk_T",
            "area_weighted_wall_T",
            "wallHeatFlux",
            "Re",
            "Pr",
            "Ri",
            "Gr",
            "Ra",
            "Gz",
            "plane_location",
            "exact_time_window",
        }
        seen = {row["metric_id"] for row in rows}
        self.assertTrue(required_metrics.issubset(seen))
        for metric in required_metrics:
            planes = {row["plane_location"] for row in rows if row["metric_id"] == metric}
            self.assertEqual(planes, {"upcomer_inlet", "upcomer_mid", "upcomer_outlet"}, metric)

    def test_formulas_include_required_definitions(self) -> None:
        build()
        rows = {row["metric_id"]: row for row in read_csv(OUT / "upcomer_extraction_contract.csv") if row["plane_location"] == "upcomer_mid"}
        self.assertIn("sum(A_i for u_n_i < 0) / sum(A_i)", rows["reverse_area_fraction"]["formula"])
        self.assertIn("sum(max(-rho_i*u_n_i, 0)*A_i)", rows["reverse_mass_fraction"]["formula"])
        self.assertIn("rms(|U_i - u_n_i*n|)", rows["secondary_velocity_fraction"]["formula"])
        self.assertIn("sum(rho_i*u_n_i*T_i*A_i)", rows["mass_flux_weighted_bulk_T"]["formula"])
        self.assertIn("sum(T_wall_j*A_j)", rows["area_weighted_wall_T"]["formula"])
        self.assertIn("Re*Pr*D_h/L_from_upcomer_inlet_to_plane", rows["Gz"]["formula"])
        self.assertIn("includes radiation", rows["wallHeatFlux"]["notes"])

    def test_admission_criteria_are_decision_complete(self) -> None:
        build()
        rows = read_csv(OUT / "upcomer_nu_admission_criteria.csv")
        classes = {row["classification"] for row in rows}
        self.assertEqual(classes, {"diagnostic_only", "validation_only", "fit_admissible_Nu", "invalid_single_stream_coefficient"})
        fit = next(row for row in rows if row["classification"] == "fit_admissible_Nu")
        self.assertIn("reverse_area_fraction<0.02", fit["pass_criteria"])
        self.assertIn("wallHeatFlux/enthalpy residual<=10%", fit["pass_criteria"])
        self.assertIn("Nu_fit_admissible_upcomer_single_stream", fit["allowed_label"])
        invalid = next(row for row in rows if row["classification"] == "invalid_single_stream_coefficient")
        self.assertIn("reverse_area_fraction>=0.10", invalid["pass_criteria"])
        self.assertIn("universal_Nu", invalid["forbidden_label"])

    def test_naming_policy_separates_diagnostic_and_fit_nu(self) -> None:
        build()
        text = (OUT / "coefficient_naming_policy.md").read_text(encoding="utf-8")
        self.assertIn("Nu_section_effective_upcomer_diagnostic", text)
        self.assertIn("It is not a true fit Nu row", text)
        self.assertIn("Nu_fit_admissible_upcomer_single_stream", text)
        self.assertIn("Internal-Nu fitting may reopen only", text)

    def test_readme_states_reopen_evidence(self) -> None:
        build()
        text = (OUT / "README.md").read_text(encoding="utf-8")
        self.assertIn("at least three admitted upcomer rows", text)
        self.assertIn("ordinary-pipe non-recirculating anchor", text)
        self.assertIn("Current fit-admissible upcomer Nu rows remain `0`", text)


if __name__ == "__main__":
    unittest.main()
