import unittest

from tools.analyze import build_heater_fluid_fraction_model as hff


class HeaterFluidFractionModelTests(unittest.TestCase):
    def test_salt2_wallflux_eta_is_training_ratio(self):
        rows = hff.read_csv(hff.CASE_HEAT_LEDGER)
        eta = hff.train_eta_from_wallflux(rows)
        train = next(row for row in rows if row["case_id"] == "salt_2")
        self.assertAlmostEqual(
            eta,
            float(train["heater_realized_wallHeatFlux_source_W"]) / float(train["heater_setup_power_W"]),
            places=12,
        )

    def test_wallflux_eta_candidate_passes_heldout_gates(self):
        summaries = hff.summary_rows(hff.candidate_rows())
        hf2 = next(row for row in summaries if row["candidate_id"] == "HF2_eta_wallflux_salt2")
        self.assertEqual(hf2["validation_gate"], "pass")
        self.assertEqual(hf2["holdout_gate"], "pass")
        self.assertEqual(hf2["admission_status"], "candidate_passes_wallflux_score_not_final_forward_v1")

    def test_realized_eta_upper_bound_is_rejected(self):
        rows = [row for row in hff.candidate_rows() if row["candidate_id"] == "HF3_case_realized_eta_upper_bound"]
        self.assertTrue(all(row["runtime_gate"] == "fail_for_admission" for row in rows))
        self.assertTrue(all(float(row["abs_error_W"]) == 0.0 for row in rows))


if __name__ == "__main__":
    unittest.main()
