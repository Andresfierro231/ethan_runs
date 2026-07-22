from __future__ import annotations

import unittest

from tools.analyze import build_s13_upcomer_exchange_target_plus_same_qoi_harvest as builder


class S13TargetPlusSameQoiHarvestTests(unittest.TestCase):
    def test_target_plus_times_are_expected(self) -> None:
        self.assertEqual(builder.TARGET_PLUS_TIMES, {"salt_2": "7916", "salt_3": "7619", "salt_4": "10001"})

    def test_field_status_rows_cover_three_cases(self) -> None:
        rows = builder.target_plus_field_status_rows()
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["case_id"] for row in rows}, {"salt_2", "salt_3", "salt_4"})
        self.assertTrue(all(row["required_fields_present"] == "true" for row in rows))

    def test_triplet_matrix_ready_when_all_windows_sampled(self) -> None:
        rows = []
        for qoi in ["Q_wall_W", "mdot_exchange_positive_outward_proxy_kg_s"]:
            for case_id in ["salt_2", "salt_3", "salt_4"]:
                rows.append(
                    {
                        "case_id": case_id,
                        "qoi_label": qoi,
                        "target_status": "ready",
                        "target_minus_status": "sampled_from_existing_native_processors64",
                        "target_plus_status": "sampled_from_staged_target_plus_processors64",
                    }
                )
        matrix = builder.same_qoi_triplet_matrix(rows)
        selected = [row for row in matrix if row["qoi_label"] == "Q_wall_W"][0]
        self.assertEqual(selected["same_qoi_neighbor_triplet_ready"], "true")
        self.assertEqual(selected["same_qoi_neighbor_uq_execution_status"], "ready_not_executed")


if __name__ == "__main__":
    unittest.main()
