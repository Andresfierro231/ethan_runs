#!/usr/bin/env python3
"""Tests for AGENT-414 downstream PM5 final-state refresh."""

from __future__ import annotations

import unittest

from tools.analyze import build_downstream_pm5_final_state_refresh as refresh


class DownstreamPm5FinalStateRefreshTests(unittest.TestCase):
    def test_f6_recirculation_blocks_fit(self) -> None:
        row = {
            "Re": "100",
            "Pr": "10",
            "Ri": "0.1",
            "rho": "1000",
            "bulk_T_K": "500",
            "wall_T_K": "501",
            "reverse_mass_fraction": "0.5",
            "reverse_area_fraction": "0.2",
            "secondary_velocity_fraction": "0.01",
        }

        status, _ = refresh.f6_row_status(row)

        self.assertEqual(status, "diagnostic_onset_only_recirculating_not_f6_fit")

    def test_internal_nu_sign_review(self) -> None:
        row = {
            "wallHeatFlux_W_m2": "-100",
            "delta_T_wall_bulk_K": "5",
            "reverse_mass_fraction": "0",
            "reverse_area_fraction": "0",
        }

        status, _, h_proxy = refresh.internal_nu_row_status(row)

        self.assertEqual(status, "diagnostic_sign_review_required")
        self.assertEqual(h_proxy, -20)

    def test_refresh_matrix_flags_stale_dependency(self) -> None:
        rows = refresh.downstream_refresh_rows(
            {
                "parsed_metric_rows": 12,
                "wallHeatFlux_rows": 12,
                "f6_unlocked_for_review_not_admitted": True,
                "internal_nu_unlocked_for_review_not_admitted": True,
            }
        )

        stale = [row for row in rows if "internal_nu_fit_rows.csv" in row["downstream_artifact"]]

        self.assertEqual(stale[0]["refresh_status"], "dependency_narrowed_not_resolved")


if __name__ == "__main__":
    unittest.main()
