import csv
import json

from tools.analyze import build_salt2_pm5q_val_salt2_readiness_ledger as ledger


def test_build_outputs_required_ledgers(tmp_path):
    summary = ledger.build(tmp_path)

    assert summary["case_rows"] == 3
    assert summary["readiness_rows"] == 21
    assert summary["pressure_rows"] == 18
    assert summary["pm5_rows"] == 7
    assert summary["fit_admitted_pressure_rows"] == 0
    assert summary["guardrails"]["scheduler_action"] is False
    assert summary["guardrails"]["native_outputs_mutated"] is False
    assert summary["guardrails"]["salt2_pm5q_fit_or_tune_allowed"] is False
    assert summary["guardrails"]["val_salt2_training_input_allowed"] is False

    for name in summary["outputs"]:
        assert (tmp_path / name).exists(), name


def test_readiness_schema_and_status_vocabulary(tmp_path):
    ledger.build(tmp_path)

    with (tmp_path / "fluid_walls_readiness_ledger.csv").open() as handle:
        rows = list(csv.DictReader(handle))

    assert {row["case_key"] for row in rows} == {"salt2_lo5q", "salt2_hi5q", "val_salt2"}
    assert {row["segment_or_branch"] for row in rows} == {row["segment_or_branch"] for row in ledger.SEGMENTS}

    for row in rows:
        for field in ledger.STATUS_FIELDS:
            assert row[field] in ledger.ALLOWED_STATUSES
        assert row["primary_source_paths"]
        assert row["next_action"]
        assert "training_fit" in row["do_not_use_for"]
        assert "model_tuning" in row["do_not_use_for"]


def test_val_salt2_pm5_is_explicitly_missing_not_inferred(tmp_path):
    ledger.build(tmp_path)

    with (tmp_path / "pm5_recirc_readiness_ledger.csv").open() as handle:
        rows = list(csv.DictReader(handle))

    val_rows = [row for row in rows if row["case_key"] == "val_salt2"]
    assert len(val_rows) == 1
    assert val_rows[0]["pm5_internal_nu_gate_status"] == "missing"
    assert val_rows[0]["metric_status"] == "missing_in_current_evidence_set"
    assert "Optional follow-on" in val_rows[0]["next_action"]

    salt2_rows = [row for row in rows if row["case_key"] in {"salt2_lo5q", "salt2_hi5q"}]
    assert len(salt2_rows) == 6
    assert all(row["pm5_internal_nu_gate_status"] == "diagnostic" for row in salt2_rows)
    assert all(row["wallHeatFlux_available"] == "true" for row in salt2_rows)


def test_pressure_rows_remain_diagnostic_and_not_fit_admitted(tmp_path):
    ledger.build(tmp_path)

    with (tmp_path / "pressure_readiness_ledger.csv").open() as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 18
    assert all(row["pressure_model_status"] == "diagnostic" for row in rows)
    assert all(row["true_f_D_or_K_fit_admitted"] == "no" for row in rows)
    assert any("pressure_definition_conflict" in row["blockers"] for row in rows)
    assert all("do_not_submit_duplicate_pressure_ladder_jobs" in row["next_use"] for row in rows)


def test_summary_matches_written_status_counts(tmp_path):
    summary = ledger.build(tmp_path)
    with (tmp_path / "summary.json").open() as handle:
        written = json.load(handle)

    assert written["outputs"] == summary["outputs"]
    assert written["status_counts"] == summary["status_counts"]
    assert written["status_counts"]["pressure_model_status"]["diagnostic"] == 18
    assert written["status_counts"]["pressure_model_status"]["missing"] == 3
