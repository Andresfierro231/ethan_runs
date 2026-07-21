import csv
import json

from tools.analyze import build_fluid_walls_readiness_ledger as ledger


def test_ledger_rows_use_allowed_statuses_and_required_fields():
    ledger.validate_rows()
    assert len(ledger.LEDGER_ROWS) == 7
    assert {row["segment_id"] for row in ledger.LEDGER_ROWS} == {
        "lower_leg_heater",
        "left_lower_leg_upcomer",
        "test_section_span",
        "left_upper_leg_upcomer",
        "upper_leg_cooler_hx",
        "right_leg_downcomer",
        "junction_stub_connector_group",
    }
    for row in ledger.LEDGER_ROWS:
        for field in ledger.LEDGER_FIELDS:
            assert field in row
        for field in ledger.STATUS_FIELDS:
            assert row[field] in ledger.ALLOWED_STATUSES


def test_build_outputs_machine_readable_tables(tmp_path):
    summary = ledger.build(tmp_path)
    assert summary["segment_rows"] == 7
    assert summary["blocker_rows"] >= 7
    assert summary["path_rows"] >= 5
    assert summary["acceptance"]["runtime_leakage_introduced"] is False
    assert summary["acceptance"]["native_outputs_mutated"] is False
    assert summary["acceptance"]["scheduler_action"] is False

    with (tmp_path / "fluid_walls_segment_readiness_ledger.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 7
    assert rows[0]["geometry_status"] in ledger.ALLOWED_STATUSES
    assert any(row["segment_id"] == "test_section_span" and row["material_stack_status"] == "admitted" for row in rows)
    assert any(row["segment_id"] == "junction_stub_connector_group" and row["uncertainty_status"] == "missing" for row in rows)

    with (tmp_path / "summary.json").open() as handle:
        written_summary = json.load(handle)
    assert written_summary["outputs"] == summary["outputs"]
    assert "pressure_model_status" in written_summary["status_counts"]


def test_shortest_path_keeps_m3ts_and_paper_claims_separate(tmp_path):
    ledger.build(tmp_path)
    with (tmp_path / "fluid_walls_shortest_missing_data_path.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    targets = {row["target"] for row in rows}
    assert {"M3+TS", "paper_ready_documentation", "paper_ready_coefficients"} <= targets
    assert any("upcomer recirculation guardrail" in row["reason"] for row in rows)
