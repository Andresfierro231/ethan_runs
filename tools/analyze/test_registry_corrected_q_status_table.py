import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_registry_corrected_q_status_table as builder


class RegistryCorrectedQStatusTableTests(unittest.TestCase):
    def test_duration_format_matches_operator_table(self):
        self.assertEqual(builder.seconds_with_minsec("2621.279"), "2621.279 s = 43m 41s")
        self.assertEqual(builder.seconds_with_minsec("254.259"), "254.259 s = 4m 14s")

    def test_status_sentence_special_cases(self):
        gate = {
            "gate_operating_point_verdict": "too_short",
            "closure_fit_admissible": "no",
            "row_verdict": "partial_requires_extended_continuation",
            "action": "Needs extended continuation.",
        }
        rec = {"terminal_window_status": "terminal_window_stationary_but_under_advanced"}
        self.assertIn("closure-fit admissible", builder.status_sentence(gate, rec))

        rec = {"recommendation": "defer_second_wave"}
        self.assertIn("defer behind Salt2 +/-10Q first wave", builder.status_sentence(gate, rec))

        rec = {"recommendation": "investigate_before_resubmit", "reason": "convergenceMonitor path"}
        self.assertIn("early monitor/End path", builder.status_sentence(gate, rec))

    def test_latest_registered_timestep_and_log_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "processors64" / "10").mkdir(parents=True)
            (root / "processors64" / "12.5").mkdir(parents=True)
            (root / "logs").mkdir()
            (root / "logs" / "log.foamRun_corrected_q").write_text(
                "Time = 12.5s\nTime = 13.75s\n",
                encoding="utf-8",
            )

            latest_time, latest_path = builder.latest_registered_timestep(str(root))
            self.assertEqual(latest_time, "12.500 s")
            self.assertTrue(latest_path.endswith("processors64/12.5"))
            self.assertEqual(builder.latest_log_time(str(root)), "13.750 s")

    def test_display_case_key_removes_corrected_suffix(self):
        self.assertEqual(builder.display_case_key("salt2_jin_lo10q_corrected"), "salt2_lo10q")
        self.assertEqual(builder.display_case_key("salt4_jin_hi5q_corrected"), "salt4_hi5q")

    def test_registry_coverage_detects_missing_and_mismatch(self):
        registry = [
            {
                "source_id": "salt1_jin_lo10q_corrected",
                "source_owner": builder.CORRECTED_OWNER,
                "source_root": "/cases/a",
            },
            {
                "source_id": "salt1_jin_hi10q_corrected",
                "source_owner": builder.CORRECTED_OWNER,
                "source_root": "/cases/old",
            },
        ]
        manifest = [
            {"case_key": "salt1_jin_lo10q_corrected", "case_dir": "/cases/a"},
            {"case_key": "salt1_jin_hi10q_corrected", "case_dir": "/cases/b"},
            {"case_key": "salt4_jin_hi10q_corrected", "case_dir": "/cases/c"},
        ]
        rows = builder.registry_coverage_rows(registry, manifest)
        self.assertEqual([row["issue"] for row in rows], ["ok", "source_root_mismatch", "missing_from_registry"])

    def test_write_outputs_creates_selected_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.csv"
            manifest = root / "manifest.csv"
            gate = root / "gate.csv"
            recs = root / "recs.csv"
            out = root / "out"

            registry.write_text(
                "source_id,case_id,source_owner,source_root,local_link_path,registered_at,size_bytes,status\n"
                f"salt1_jin_lo10q_corrected,salt_test_1_jin_corrected_q_lo10q,{builder.CORRECTED_OWNER},{root / 'case_a'},,now,,registered\n",
                encoding="utf-8",
            )
            (root / "case_a" / "processors64" / "6377").mkdir(parents=True)
            manifest.write_text(
                f"case_key,case_dir\nsalt1_jin_lo10q_corrected,{root / 'case_a'}\n",
                encoding="utf-8",
            )
            gate.write_text(
                "case_key,label,gate_latest_time_s,gate_advance_s,gate_operating_point_verdict,closure_fit_admissible,row_verdict,action\n"
                "salt1_jin_lo10q_corrected,Salt1 -10Q,6377.610,2621.279,too_short,no,partial_requires_extended_continuation,Needs continuation.\n",
                encoding="utf-8",
            )
            recs.write_text(
                "case_key,terminal_window_status,recommendation,future_fit_label\n"
                "salt1_jin_lo10q_corrected,terminal_window_stationary_but_under_advanced,hold_policy_then_continue,sensitivity/correlation-support\n",
                encoding="utf-8",
            )

            args = type(
                "Args",
                (),
                {
                    "registry": str(registry),
                    "manifest": str(manifest),
                    "gate": str(gate),
                    "recommendations": str(recs),
                    "output_dir": str(out),
                    "case_key": ["salt1_jin_lo10q_corrected"],
                    "strict_registry": True,
                },
            )
            self.assertEqual(builder.write_outputs(args), 0)
            self.assertIn("Salt1 -10Q", (out / "selected_corrected_q_status_table.md").read_text(encoding="utf-8"))
            rows = builder.read_csv(out / "selected_corrected_q_status_table.csv")
            self.assertEqual(rows[0]["case_key"], "salt1_lo10q")
            self.assertEqual(rows[0]["source_case_key"], "salt1_jin_lo10q_corrected")
            self.assertEqual(rows[0]["closure_fit_admissible"], "yes")
            self.assertTrue((out / "corrected_q_latest_timesteps.csv").is_file())


if __name__ == "__main__":
    unittest.main()
