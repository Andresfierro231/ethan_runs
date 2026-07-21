"""Tests for remaining two-tap gate and anchor request packages."""

from __future__ import annotations

import csv
import json
import unittest

from tools.analyze import build_two_tap_remaining_gates_and_anchor_request as build


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TwoTapRemainingGatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = build.build_all()

    def test_component_isolation_routes_all_rows_to_apparent_cluster(self) -> None:
        audit = rows(build.ISOLATION_OUT / "component_isolation_audit.csv")
        self.assertEqual(len(audit), 3)
        self.assertEqual({row["case_id"] for row in audit}, {"salt_2", "salt_3", "salt_4"})
        for row in audit:
            self.assertEqual(row["selected_component_isolation_label"], "apparent_cluster_only")
            self.assertEqual(row["decision"], "diagnostic_apparent_cluster_only")
            self.assertEqual(row["component_k_admitted"], "false")
            self.assertEqual(row["f6_fit_performed"], "false")
        decision = json.loads((build.ISOLATION_OUT / "apparent_cluster_decision.json").read_text(encoding="utf-8"))
        self.assertEqual(decision["decision"], "apparent_cluster_only")

    def test_straight_reference_options_reject_clipping_and_mixed_basis(self) -> None:
        options = rows(build.ISOLATION_OUT / "straight_reference_options.csv")
        self.assertEqual(len(options), 12)
        by_status = {row["option_status"] for row in options}
        self.assertIn("reject_negative_or_old_proxy_basis", by_status)
        self.assertIn("reject_mixed_basis_and_recirculation", by_status)
        self.assertIn("reject_negative_and_recirculation", by_status)
        self.assertIn("select_apparent_cluster_only", by_status)

    def test_same_qoi_uq_is_missing_no_gci_for_all_rows(self) -> None:
        uq = rows(build.UQ_OUT / "same_qoi_uncertainty_audit.csv")
        self.assertEqual(len(uq), 3)
        for row in uq:
            self.assertEqual(row["same_qoi_uncertainty_gate"], "fail_missing_same_qoi_UQ")
            self.assertEqual(row["decision"], "missing_no_GCI_diagnostic_only")
            self.assertEqual(row["component_k_admitted"], "false")
        inventory = rows(build.UQ_OUT / "available_family_inventory.csv")
        self.assertEqual(len(inventory), 6)
        self.assertTrue(all(row["eligible_for_same_qoi_UQ"] == "false" for row in inventory))

    def test_separated_review_admits_nothing_and_preserves_f6_guardrail(self) -> None:
        final = rows(build.REVIEW_OUT / "final_gate_review.csv")
        self.assertEqual(len(final), 3)
        for row in final:
            self.assertEqual(row["raw_endpoint_surface_availability"], "pass")
            self.assertEqual(row["pressure_velocity_basis_gate"], "pass")
            self.assertEqual(row["recirculation_gate"], "fail_material_reverse_flow")
            self.assertEqual(row["ordinary_component_k_candidate"], "false")
            self.assertEqual(row["component_k_admitted"], "false")
            self.assertEqual(row["f6_fit_performed"], "false")
        f6 = rows(build.REVIEW_OUT / "f6_separation_guardrail.csv")
        self.assertEqual({row["status"] for row in f6}, {"enforced"})

    def test_anchor_request_is_request_only(self) -> None:
        request = rows(build.ANCHOR_OUT / "nonrecirculating_anchor_request.csv")
        self.assertEqual(len(request), 2)
        self.assertTrue(all("do not launch" in row["guardrail"] or "do not substitute" in row["guardrail"] for row in request))
        gates = rows(build.ANCHOR_OUT / "launch_gate_contract.csv")
        self.assertEqual({row["status"] for row in gates}, {"required_future"})
        summary = json.loads((build.ANCHOR_OUT / "summary.json").read_text(encoding="utf-8"))
        self.assertFalse(summary["component_k_admitted"])
        self.assertFalse(summary["f6_fit_performed"])

    def test_top_level_summary_guardrails(self) -> None:
        self.assertEqual(self.summary["case_count"], 3)
        self.assertEqual(self.summary["component_isolation_decision"], "apparent_cluster_only")
        self.assertEqual(self.summary["same_qoi_uq_missing_rows"], 3)
        self.assertEqual(self.summary["final_admission_decision"], "diagnostic_only_apparent_cluster_recirculation_blocked_missing_UQ")
        self.assertFalse(self.summary["component_k_admitted"])
        self.assertFalse(self.summary["f6_fit_performed"])


if __name__ == "__main__":
    unittest.main()
