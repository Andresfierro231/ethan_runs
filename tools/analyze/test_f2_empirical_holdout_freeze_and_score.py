#!/usr/bin/env python3.11
"""Tests for the F2 empirical freeze + score-once harness.

Invariants:
- Frozen F2 coefficients match the committed source exactly.
- The affine harness is correct: T_corr = a*predicted + b (identity check).
- The dry-run runs on nominal data only and reduces error vs raw.
- No protected holdout row is scored; readiness is blocked with named inputs.
- No physical-closure claim; all guardrails False.
"""
from __future__ import annotations

import build_f2_empirical_holdout_freeze_and_score as mod


def test_frozen_coefficients_exact():
    f2 = mod.frozen_f2()
    assert abs(f2["a_multiplier"] - 0.3729829182408737) < 1e-15
    assert abs(f2["b_offset_K"] - 246.55192842685844) < 1e-12
    assert f2["n_fit_rows"] == 32
    assert f2["coefficient_source"] == "Salt1_Salt2_train_support_fit_only"


def test_affine_harness_math():
    a, b = 0.5, 100.0
    assert mod.apply_f2(400.0, a, b) == 300.0
    rows = [
        {"sensor": "TP1", "kind": "TP", "predicted_K": "400.0", "measured_K": "300.0", "validation_excluded": "False"},
        {"sensor": "X", "kind": "OTHER", "predicted_K": "1", "measured_K": "1", "validation_excluded": "False"},
        {"sensor": "TW1", "kind": "TW", "predicted_K": "", "measured_K": "1", "validation_excluded": "False"},
        {"sensor": "TP2", "kind": "TP", "predicted_K": "200.0", "measured_K": "150.0", "validation_excluded": "True"},
    ]
    out = mod.score_rows(rows, a, b)
    assert out["n_rows"] == 1, "only the one usable TP row counts"
    assert abs(out["rows"][0]["corrected_K"] - 300.0) < 1e-9
    assert abs(out["corrected_error_K"] if "corrected_error_K" in out else out["rows"][0]["corrected_error_K"]) < 1e-9


def test_freeze_manifest_and_hash():
    r = mod.build()
    fm = r["freeze_manifest"]
    assert fm["immutable"] is True
    assert fm["physical_closure_claim_allowed"] is False
    assert fm["refit_after_freeze"] is False
    assert len(fm["content_sha256"]) == 64  # sha256 hex


def test_dry_run_is_nominal_only_and_improves():
    r = mod.build()
    d = r["dryrun"][0]
    assert "NOT_a_holdout_score" in d["role"]
    assert d["affine_identity_check_passed"] == "True"
    assert d["n_rows"] > 0
    # F2 correction must beat the raw 1D bias on the nominal set
    assert d["corrected_rmse_K"] < d["raw_rmse_K"]


def test_no_protected_row_scored():
    r = mod.build()
    assert r["decision"]["protected_rows_scored"] == 0
    assert r["decision"]["final_protected_score_values"] == 0
    for row in r["readiness"]:
        assert row["score_computable_now"] == "False"
        assert row["score_value"] == "blocked_pending_inputs"
        assert row["missing_inputs"]


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
