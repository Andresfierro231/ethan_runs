#!/usr/bin/env python3.11
"""Tests for the S13 stationary-window Q_wall mesh GCI.

Invariants:
- 12 GCI rows (3 cases x 4 QOIs); refinement ratios ~1.46-1.48.
- Q_wall is mesh-UQ admitted for all 3 cases with a small, trustworthy GCI and
  an in-range asymptotic ratio; Salt3/Salt4 recover near second-order.
- The recirculation-exchange proxies are NOT admitted (mesh-unconverged).
- All three windows feeding an admitted Q_wall GCI are stationary.
- Nothing is released / frozen / scored; all guardrails are False.
"""
from __future__ import annotations

import build_s13_stationary_window_qwall_mesh_gci as mod


def test_grid_ratios_and_row_count():
    r = mod.build()
    assert len(r["gci"]) == 12
    s = r["summary"]
    assert 1.40 < s["r21"] < 1.55
    assert 1.40 < s["r32"] < 1.55


def test_qwall_mesh_uq_admitted_all_cases():
    r = mod.build()
    qw = [row for row in r["gci"] if row["qoi_label"] == "Q_wall_W"]
    assert len(qw) == 3
    for row in qw:
        assert row["mesh_uq_admitted"] == "True"
        assert row["gci_trustworthy"] == "True"
        assert row["verdict"] == "monotonic_convergence"
        assert row["gci_fine_pct"] is not None and row["gci_fine_pct"] < 1.0
        assert abs(row["asymptotic_range_ratio"] - 1.0) <= 0.15
        assert row["all_windows_stationary"] == "True"


def test_salt3_salt4_recover_second_order():
    r = mod.build()
    for case in ("salt_3", "salt_4"):
        row = next(x for x in r["gci"] if x["case_id"] == case and x["qoi_label"] == "Q_wall_W")
        assert 1.5 <= row["observed_order_p"] <= 2.5, f"{case} p={row['observed_order_p']}"


def test_exchange_proxies_fail_closed():
    r = mod.build()
    proxies = [row for row in r["gci"] if row["qoi_label"] != "Q_wall_W"]
    assert len(proxies) == 9
    assert all(row["mesh_uq_admitted"] == "False" for row in proxies)
    assert r["summary"]["exchange_proxy_cases_mesh_uq_admitted"] == 0


def test_gate_and_no_release():
    r = mod.build()
    assert r["decision"]["same_qoi_mesh_gci_gate"] == "pass_for_Q_wall_only"
    assert r["decision"]["source_property_release"] is False
    assert r["decision"]["candidate_freeze"] is False
    assert r["decision"]["final_score_values"] == 0


def test_guardrails_all_false():
    r = mod.build()
    for key, value in r["guardrails"]:
        assert value is False, f"guardrail {key} must be False"


if __name__ == "__main__":
    import sys

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:  # pragma: no cover
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    sys.exit(1 if failed else 0)
