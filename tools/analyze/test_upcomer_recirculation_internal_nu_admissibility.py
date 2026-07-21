from __future__ import annotations

import csv
import unittest
from pathlib import Path

from tools.analyze.build_upcomer_recirculation_internal_nu_admissibility import OUT, build


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class UpcomerRecirculationInternalNuAdmissibilityTests(unittest.TestCase):
    def test_builds_expected_outputs(self) -> None:
        summary = build()
        self.assertEqual(summary["task"], "AGENT-330")
        self.assertEqual(summary["decision"], "no_internal_Nu_fit_admissible_today")
        self.assertEqual(summary["fit_admissible_internal_nu_rows"], 0)
        for name in summary["outputs"]:
            self.assertTrue((OUT / name).exists(), name)

    def test_onset_rows_are_recirculating_and_not_fit_admitted(self) -> None:
        build()
        rows = read_csv(OUT / "upcomer_recirculation_onset_conditions.csv")
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["recirculation_observed"] for row in rows}, {"yes"})
        self.assertEqual({row["internal_nu_fit_admissible"] for row in rows}, {"no"})
        self.assertEqual({row["admissibility_decision"] for row in rows}, {"validation_only_diagnostic_not_fit"})
        self.assertTrue(all(float(row["backflow_fraction"]) >= 0.10 for row in rows))
        self.assertTrue(all(float(row["Ri_median"]) >= 1.0 for row in rows))

    def test_missing_thermal_development_metrics_stay_blocked(self) -> None:
        build()
        rows = read_csv(OUT / "upcomer_recirculation_onset_conditions.csv")
        self.assertEqual({row["Gz_available"] for row in rows}, {"no"})
        self.assertEqual({row["wall_bulk_delta_T_status"] for row in rows}, {"missing_direct_wall_core_delta_T"})
        for row in rows:
            blockers = row["blocked_missing_metrics"].split(";")
            self.assertIn("Gz", blockers)
            self.assertIn("direct_wall_bulk_delta_T", blockers)
            self.assertIn("mesh_GCI", blockers)

    def test_coefficient_naming_rejects_universal_names(self) -> None:
        build()
        rows = read_csv(OUT / "coefficient_naming_rules_for_recirculation.csv")
        general = [row for row in rows if row["scope"] == "general_upcomer_recirculation_rule"]
        self.assertEqual({row["coefficient_family"] for row in general}, {"Nu", "f_D", "K"})
        self.assertEqual({row["rule_status"] for row in general}, {"reject_universal_name"})
        self.assertTrue(all("universal_" in row["rejected_labels"] for row in general))
        self.assertTrue(any(row["coefficient_family"] == "Nu" and row["section"] == "left_upper_leg" for row in rows))

    def test_readme_states_no_internal_nu_fit(self) -> None:
        build()
        readme = (OUT / "README.md").read_text(encoding="utf-8")
        self.assertIn("No internal Nu row is fit-admissible today", readme)
        self.assertIn("Upcomer recirculation is now an admission rule", readme)
        self.assertIn("rcExternalTemperature wallHeatFlux includes radiation", readme)


if __name__ == "__main__":
    unittest.main()
