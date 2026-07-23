#!/usr/bin/env python3.11
"""Tests for the CFD-basis all-4 affine fit + Salt2 +/-5Q holdout score."""
from __future__ import annotations

import build_salt2_pm5_holdout_inputs_and_f2_score as mod


def test_all4_nominal_paired():
    r = mod.build()
    cov = {c["case"]: c for c in r["nominal_coverage"]}
    assert set(cov) == {"salt_1", "salt_2", "salt_3", "salt_4"}
    assert all(cov[c]["status"] == "ok" and cov[c]["paired_sensors"] >= 10 for c in cov)


def test_cfd_affine_fit_finite_and_positive_slope():
    r = mod.build()
    f = r["freeze"]
    assert 0.0 < f["a_multiplier"] < 2.0
    assert f["n_fit_pairs"] >= 40
    assert f["target_reference"].startswith("CFD reference_k")
    assert f["physical_closure_claim_allowed"] is False


def test_holdout_scored_on_full_tp_tw_and_big_reduction():
    r = mod.build()
    combined = r["holdout_combined"]["new_cfd_affine"]
    assert combined["n"] == 30, "15 TP/TW sensors x 2 pm5 cases"
    # corrected error must be a large reduction vs raw 1D
    assert combined["corrected_mae_K"] < 0.2 * combined["raw_mae_K"]
    assert combined["corrected_mae_K"] < 15.0


def test_external_val_salt2_scored_cfd_basis():
    r = mod.build()
    ext = r["external_scores"]
    assert ext["status"] == "scored_cfd_basis_salt_jin"
    assert "same_pipeline" in ext["cfd_target_vintage"], "must use method-consistent 2026-07-23 extraction"
    s = ext["new_cfd_affine"]
    assert s["n"] == 15
    assert s["corrected_mae_K"] < 0.2 * s["raw_mae_K"]  # large reduction vs raw
    assert s["corrected_mae_K"] < 15.0


def test_no_physical_release_or_closure():
    r = mod.build()
    assert r["decision"]["physical_closure_claim"] is False
    for k, v in r["guardrails"]:
        assert v is False, f"guardrail {k} must be False"


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except AssertionError as exc:  # pragma: no cover
            failed += 1; print(f"FAIL {fn.__name__}: {exc}")
    sys.exit(1 if failed else 0)
