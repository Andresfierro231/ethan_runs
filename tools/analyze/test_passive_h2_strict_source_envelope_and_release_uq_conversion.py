#!/usr/bin/env python3.11
"""Tests for the PASSIVE-H2 strict source-envelope + release-UQ conversion.

Invariants enforced (fail-closed, no-leakage audit):
- 16 conversion rows (4 salt cases x 4 retained R4 families; junction excluded).
- Strict pass rows exist and are wallHeatFlux-free with mesh/setup-backed area.
- Salt1 provenance was CONVERTED FROM a wallHeatFlux-traced recovery.
- No row flips source_property_release / candidate_freeze / final_score.
- Same-QOI release UQ is fail-closed (no ready label) with mesh-GCI named blocker.
- All no-mutation guardrails are False.
"""
from __future__ import annotations

import build_passive_h2_strict_source_envelope_and_release_uq_conversion as mod


def test_conversion_row_shape():
    r = mod.build()
    conv = r["conversion"]
    assert len(conv) == 16, "expected 4 cases x 4 retained families"
    assert all(row["source_family"] != "junction" for row in conv), "junction is R4-excluded"
    assert {row["case_id"] for row in conv} == {"salt_1", "salt_2", "salt_3", "salt_4"}


def test_strict_pass_is_wallheatflux_free_and_nonzero():
    r = mod.build()
    strict = [row for row in r["conversion"] if row["strict_source_envelope_pass"] == "True"]
    assert strict, "conversion must produce at least one strict source-envelope row"
    for row in strict:
        assert row["c1_wallHeatFlux_free"] == "True"
        assert row["c2_no_forbidden_runtime_inputs"] == "True"
        assert row["c4_area_mesh_backed"] == "True"
        assert row["property_mode"] == "salt_jin"


def test_salt1_converted_from_wallheatflux_trace():
    r = mod.build()
    salt1 = [row for row in r["conversion"] if row["case_id"] == "salt_1"]
    assert len(salt1) == 4
    for row in salt1:
        assert row["provenance_converted_from"] == "wallHeatFlux_traced_postProcessing_recovery"
        assert row["area_provenance"] == "salt1_mesh_area_verified_polyMesh_only"
        assert row["strict_source_envelope_pass"] == "True"


def test_train_release_eligibility_and_protected_rows():
    r = mod.build()
    conv = r["conversion"]
    train_eligible = [row for row in conv if row["release_eligible_pending_uq_and_review"] == "True"]
    # Salt1 (train) + Salt2 (train) x 4 families = 8
    assert len(train_eligible) == 8
    assert {row["case_id"] for row in train_eligible} == {"salt_1", "salt_2"}
    protected = [row for row in conv if row["split_role"] in ("validation", "holdout")]
    for row in protected:
        assert row["release_eligible_pending_uq_and_review"] == "False", "protected rows are score-only"


def test_strict_pass_is_exactly_the_eight_train_rows():
    r = mod.build()
    strict = [row for row in r["conversion"] if row["strict_source_envelope_pass"] == "True"]
    assert len(strict) == 8, "strict pass must be Salt1+Salt2 train x 4 retained families only"
    assert {row["case_id"] for row in strict} == {"salt_1", "salt_2"}
    # protected rows must NOT claim a strict pass without verified per-row props
    protected = [row for row in r["conversion"] if row["split_role"] in ("validation", "holdout")]
    assert all(row["strict_source_envelope_pass"] == "False" for row in protected)
    assert r["summary"]["strict_source_envelope_pass_rows"] == 8


def test_no_release_or_freeze_or_score_flipped():
    r = mod.build()
    for row in r["conversion"]:
        assert row["source_property_release"] == "False"
        assert row["candidate_freeze"] == "False"
        assert row["final_score"] == "0"
    assert r["decision"]["source_property_release"] is False
    assert r["decision"]["candidate_freeze"] is False
    assert r["decision"]["final_score_values"] == 0


def test_same_qoi_uq_fail_closed_with_named_blocker():
    r = mod.build()
    uq = r["uq_rows"]
    assert uq, "must enumerate R4 QOI labels"
    assert all(row["same_qoi_release_uq_ready"] == "False" for row in uq)
    assert all(row["source_gate"] == "pass_after_strict_conversion" for row in uq)
    assert all("mesh_gci" in row["mesh_gci_gate"] for row in uq)
    assert r["summary"]["same_qoi_release_uq_ready_labels"] == 0
    # the sole remaining freeze blocker must be the mesh-GCI triplet
    assert "mesh_gci_triplet" in r["decision"]["same_qoi_release_uq"]
    assert any("GCI triplet" in m["missing_item"] for m in r["missing_evidence"])


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
