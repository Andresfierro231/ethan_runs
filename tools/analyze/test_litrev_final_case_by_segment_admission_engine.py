import unittest

from tools.analyze import build_litrev_final_case_by_segment_admission_engine as engine


class LitRevFinalCaseBySegmentAdmissionEngineTests(unittest.TestCase):
    def test_case_segment_matrix_has_current_regime_rows(self):
        rows = engine.case_segment_rows()
        self.assertEqual(len(rows), 18)
        self.assertEqual({row["closure_status"] for row in rows}, {"unresolved"})

    def test_no_closure_family_admitted(self):
        rows = engine.closure_family_rows()
        self.assertTrue(rows)
        self.assertEqual(sum(int(row["admitted_rows"]) for row in rows), 0)

    def test_litrev_sources_are_recorded(self):
        rows = engine.litrev_source_rows()
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(row["exists"] == "true" for row in rows))

    def test_missing_required_fields_are_explicit(self):
        missing = {row["field"]: row for row in engine.missing_field_rows(engine.case_segment_rows())}
        self.assertEqual(missing["Bo_range"]["status"], "missing")
        self.assertEqual(missing["same_QOI_UQ"]["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
