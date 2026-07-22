from __future__ import annotations

import unittest

from tools.analyze import build_s13_upcomer_exchange_qwall_neighbor_window_sampling as builder
from tools.extract import build_s13_upcomer_exchange_exact_pressure_qwall_compute as exact


class S13QwallNeighborWindowSamplingTests(unittest.TestCase):
    def test_neighbor_time_selection_finds_minus_and_missing_plus(self) -> None:
        rows = [builder.neighbor_times(case) for case in exact.case_rows()]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["target_minus_available"] == "true" for row in rows))
        self.assertTrue(all(row["target_plus_available"] == "false" for row in rows))
        self.assertEqual({row["target_minus_time_window_s"] for row in rows}, {"7914", "7617", "9999"})

    def test_vector_parser_handles_openfoam_vector_list(self) -> None:
        block = "internalField nonuniform List<vector> 2\n(\n(1 2 3)\n(-4.5 6e-1 7E+2)\n);"
        self.assertEqual(builder.parse_vector_list(block), [(1.0, 2.0, 3.0), (-4.5, 0.6, 700.0)])

    def test_qoi_labels_match_requested_set(self) -> None:
        self.assertEqual(
            builder.qoi_labels(),
            [
                "Q_wall_W",
                "mdot_exchange_positive_outward_proxy_kg_s",
                "tau_recirc_proxy_s",
                "wall_core_bulk_temperature_contrast_K",
            ],
        )


if __name__ == "__main__":
    unittest.main()
