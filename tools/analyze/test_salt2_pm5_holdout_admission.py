import unittest

from tools.analyze.build_salt2_pm5_holdout_admission import build_admission_rows, build_runtime_leakage_audit
from tools.extract.repair_salt2_pm5_holdout_matched_plane_sampling import (
    AGENT406_METRICS,
    SALT2_CASES,
    read_csv,
    salt2_metric_rows,
)


class Salt2Pm5HoldoutAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = salt2_metric_rows(read_csv(AGENT406_METRICS))
        cls.admission = build_admission_rows(cls.metrics)

    def test_admission_rows_cover_salt2_pm5(self):
        self.assertEqual(len(self.admission), 6)
        self.assertEqual({row["case_key"] for row in self.admission}, set(SALT2_CASES))

    def test_holdout_rows_are_fit_forbidden(self):
        self.assertEqual({row["holdout_only"] for row in self.admission}, {"yes"})
        self.assertEqual({row["fit_forbidden"] for row in self.admission}, {"yes"})
        self.assertEqual({row["model_selection_forbidden"] for row in self.admission}, {"yes"})
        self.assertEqual({row["f6_fit_admissible_now"] for row in self.admission}, {"no"})
        self.assertEqual({row["internal_nu_fit_admissible_now"] for row in self.admission}, {"no"})

    def test_recirculation_blocks_single_stream_fits(self):
        self.assertTrue(all("recirculation_invalidates_single_stream_fit" in row["blockers"] for row in self.admission))
        self.assertEqual({row["admission_status"] for row in self.admission}, {"holdout_diagnostic_only_not_fit_admitted"})

    def test_runtime_leakage_audit_forbids_wallheatflux_runtime_input(self):
        audit = {row["check"]: row["status"] for row in build_runtime_leakage_audit()}
        self.assertEqual(audit["wallHeatFlux_runtime_input"], "pass_forbidden")
        self.assertEqual(audit["model_selection_on_holdout"], "pass_forbidden")


if __name__ == "__main__":
    unittest.main()
