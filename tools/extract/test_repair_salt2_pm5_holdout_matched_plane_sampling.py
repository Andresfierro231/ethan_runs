import unittest

from tools.extract.repair_salt2_pm5_holdout_matched_plane_sampling import (
    AGENT406_METRICS,
    AGENT406_VALIDATION,
    PLANE_LOCATIONS,
    SALT2_CASES,
    build_repair_decision,
    read_csv,
    salt2_metric_rows,
    salt2_validation_rows,
)


class Salt2Pm5HoldoutMatchedPlaneRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = salt2_metric_rows(read_csv(AGENT406_METRICS))
        cls.validation = salt2_validation_rows(read_csv(AGENT406_VALIDATION))
        cls.decisions = build_repair_decision(cls.metrics, cls.validation)

    def test_only_salt2_holdout_rows(self):
        self.assertEqual({row["case_key"] for row in self.metrics}, set(SALT2_CASES))
        self.assertEqual(len(self.metrics), 6)

    def test_three_planes_per_case(self):
        for case_key in SALT2_CASES:
            rows = [row for row in self.metrics if row["case_key"] == case_key]
            self.assertEqual({row["plane_location"] for row in rows}, set(PLANE_LOCATIONS))

    def test_required_fields_complete(self):
        self.assertEqual({row["field_validation_status"] for row in self.metrics}, {"pass"})
        self.assertTrue(all(row["wallHeatFlux_available"].lower() == "true" for row in self.metrics))

    def test_validation_rows_pass(self):
        self.assertEqual(len(self.validation), 6)
        self.assertEqual({row["validation_status"] for row in self.validation}, {"pass"})

    def test_reuse_agent406_no_new_postprocessing_needed(self):
        self.assertEqual({row["repair_decision"] for row in self.decisions}, {"reuse_agent406_repaired_artifacts"})
        self.assertEqual({row["staged_copy_postprocessing_needed"] for row in self.decisions}, {"no"})


if __name__ == "__main__":
    unittest.main()
