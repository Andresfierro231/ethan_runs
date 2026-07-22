from __future__ import annotations

import unittest

from tools.analyze import build_thesis_n2_upcomer_exchange_qwall_uq_paper_panels_refresh_after_neighbor_sampling as builder


class N2PanelRefreshAfterNeighborSamplingTests(unittest.TestCase):
    def test_qwall_time_drift_has_three_cases(self) -> None:
        rows = builder.read_csv(builder.SAMPLING / "same_qoi_neighbor_window_rows.csv")
        drift = builder.qwall_time_drift_rows(rows)
        self.assertEqual(len(drift), 3)
        self.assertEqual({row["case_id"] for row in drift}, {"salt_2", "salt_3", "salt_4"})

    def test_blocker_table_preserves_no_ready_uq(self) -> None:
        rows = builder.read_csv(builder.SAMPLING / "same_qoi_uq_matrix.csv")
        blockers = builder.qoi_blocker_rows(rows)
        self.assertEqual(len(blockers), 4)
        self.assertTrue(all(row["same_qoi_neighbor_uq_ready"] == "false" for row in blockers))
        self.assertTrue(all(row["target_plus_ready_rows"] == "0" for row in blockers))

    def test_claim_boundary_forbids_harvest_and_admission(self) -> None:
        summary = {"target_minus_ready_rows": 12, "target_plus_ready_rows": 0}
        claims = builder.claim_boundary_rows(summary)
        forbidden = [row for row in claims if row["allowed"] == "false"]
        self.assertGreaterEqual(len(forbidden), 2)
        self.assertTrue(any("production harvest" in row["claim"] for row in forbidden))
        self.assertTrue(any("coefficient" in row["claim"] for row in forbidden))


if __name__ == "__main__":
    unittest.main()
