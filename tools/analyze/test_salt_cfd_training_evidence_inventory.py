from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_salt_cfd_training_evidence_inventory import build_salt_cfd_training_evidence_inventory


class SaltCFDTrainingEvidenceInventoryTests(unittest.TestCase):
    def test_salt_only_split_and_corrected_q_guardrails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-cfd-inventory-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt_cfd_training_evidence_inventory(out_dir, query_scheduler=False)

            self.assertEqual(summary["water_rows_included"], 0)
            self.assertEqual(summary["corrected_q_rows"], 14)
            self.assertEqual(summary["corrected_q_rows_admitted_now"], 0)
            self.assertEqual(summary["usable_training_now"], ["salt2_jin_nominal_continuation"])
            self.assertEqual(summary["usable_validation_now"], ["salt3_jin_nominal_continuation"])
            self.assertEqual(summary["usable_holdout_now"], ["salt4_jin_nominal_continuation"])

            rows = self._rows_by_key(out_dir / "salt_cfd_candidate_inventory.csv")
            self.assertEqual(rows["salt2_jin_nominal_continuation"]["admission_verdict"], "fit-admissible")
            self.assertEqual(rows["salt2_jin_nominal_continuation"]["candidate_onset_role"], "recirculating_reference")
            self.assertEqual(rows["salt2_jin_nominal_continuation"]["recirculation_evidence_available"], "yes")
            self.assertEqual(rows["salt2_lo10q"]["admission_verdict"], "pending-terminal-harvest")
            self.assertEqual(rows["salt3_hi10q"]["admission_verdict"], "not-admissible")
            self.assertEqual(rows["salt2_mesh_refinement_family_coarse_medium_fine"]["admission_verdict"], "diagnostic-only")

    def test_bc_roles_preserve_radiation_and_pending_status(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-cfd-inventory-") as tmpdir:
            out_dir = Path(tmpdir)
            build_salt_cfd_training_evidence_inventory(out_dir, query_scheduler=False)

            with (out_dir / "bc_role_label_inventory.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            salt2_heater = [
                row for row in rows
                if row["case_key"] == "salt2_jin_nominal_continuation" and row["patch_or_role"] == "heater"
            ]
            self.assertEqual(len(salt2_heater), 1)
            self.assertEqual(salt2_heater[0]["heater_source"], "yes")
            self.assertIn("wallHeatFlux is the total", salt2_heater[0]["radiation_wallHeatFlux_semantics"])

            corrected_roles = [row for row in rows if row["case_key"] == "salt2_lo10q"]
            self.assertTrue(corrected_roles)
            self.assertTrue(all("not admitted" in row["admission_use"] for row in corrected_roles))

    def test_required_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-cfd-inventory-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt_cfd_training_evidence_inventory(out_dir, query_scheduler=False)

            for filename in summary["required_outputs"]:
                self.assertTrue((out_dir / filename).exists(), filename)

            with (out_dir / "source_manifest.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            read_only_inputs = [row for row in rows if row["role"] == "read_only_input"]
            self.assertTrue(read_only_inputs)
            self.assertTrue(all(row["exists"] == "True" for row in read_only_inputs))

    def test_upcomer_onset_candidates_preserve_availability_vs_admission(self) -> None:
        with tempfile.TemporaryDirectory(prefix="salt-cfd-inventory-") as tmpdir:
            out_dir = Path(tmpdir)
            summary = build_salt_cfd_training_evidence_inventory(out_dir, query_scheduler=False)

            self.assertFalse(summary["onset_existing_bracket_available"])
            self.assertEqual(summary["onset_current_re_max"], "134.883")

            rows = self._rows_by_key(out_dir / "upcomer_onset_candidate_cases.csv")
            salt4 = rows["salt4_jin_nominal_continuation"]
            self.assertEqual(salt4["availability_status"], "available now")
            self.assertEqual(salt4["candidate_onset_role"], "recirculating_reference")
            self.assertEqual(salt4["recirculation_observed"], "yes")
            self.assertEqual(salt4["Re_target_bucket"], "highest_available_below_150")

            self.assertEqual(rows["salt4_hi10q"]["availability_status"], "running")
            self.assertEqual(rows["salt4_hi10q"]["candidate_onset_role"], "transition_candidate")
            self.assertEqual(rows["salt4_hi10q"]["recirculation_evidence_available"], "no")

            self.assertEqual(rows["new_targeted_re250"]["availability_status"], "would require a new run")
            self.assertEqual(rows["new_targeted_re250"]["candidate_onset_role"], "ordinary_pipe_anchor")

    @staticmethod
    def _rows_by_key(path: Path) -> dict[str, dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["case_key"]: row for row in csv.DictReader(handle)}


if __name__ == "__main__":
    unittest.main()
