import csv
import json

from tools.analyze import build_salt_pm10_terminal_admission as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_pm10_terminal_packet_preserves_split_and_runtime_guardrails(tmp_path):
    summary = builder.build(tmp_path)

    assert summary["case_count"] == 4
    assert summary["scheduler_terminal"] == "yes"
    assert summary["solver_job_state"] == "TIMEOUT"
    assert summary["harvest_job_state"] == "COMPLETED"
    assert summary["terminal_evidence_admitted_rows"] == 4
    assert summary["fit_allowed_now_rows"] == 0
    assert summary["model_selection_allowed_now_rows"] == 0
    assert summary["protected_score_allowed_now_rows"] == 0
    assert summary["runtime_input_allowed_now_rows"] == 0
    assert summary["ordinary_upcomer_closure_allowed_rows"] == 0
    assert summary["native_output_mutation"] == "none"
    assert summary["registry_mutation"] == "none"
    assert summary["scheduler_action"] == "none"

    gate_rows = read_csv(tmp_path / "pm10_case_terminal_gate.csv")
    assert {row["case_key"] for row in gate_rows} == set(builder.CASE_KEYS)
    assert {row["terminal_evidence_admitted"] for row in gate_rows} == {"yes"}
    assert {row["fit_allowed_now"] for row in gate_rows} == {"no"}
    assert {row["model_selection_allowed_now"] for row in gate_rows} == {"no"}
    assert {row["protected_score_allowed_now"] for row in gate_rows} == {"no"}
    assert {row["runtime_input_allowed_now"] for row in gate_rows} == {"no"}
    assert {row["ordinary_upcomer_closure_allowed"] for row in gate_rows} == {"no"}
    assert {row["source_property_release_allowed"] for row in gate_rows} == {"no"}


def test_pm10_recirc_packet_does_not_promote_ordinary_upcomer_closures(tmp_path):
    builder.build(tmp_path)

    recirc_rows = read_csv(tmp_path / "pm10_recirc_onset_summary.csv")
    assert len(recirc_rows) == 4
    assert {row["upcomer_admission_classification"] for row in recirc_rows} == {
        "recirculation_diagnostic"
    }
    assert {row["recirculation_severity_class"] for row in recirc_rows} == {
        "strong_recirculation"
    }
    assert {row["ordinary_pipe_fit_allowed"] for row in recirc_rows} == {"no"}
    assert {row["ordinary_pipe_model_selection_allowed"] for row in recirc_rows} == {"no"}
    assert {row["fit_allowed_now"] for row in recirc_rows} == {"no"}
    assert {row["model_selection_allowed_now"] for row in recirc_rows} == {"no"}
    assert {row["runtime_input_allowed_now"] for row in recirc_rows} == {"no"}


def test_pm10_packet_writes_expected_closeout_files(tmp_path):
    builder.build(tmp_path)

    expected = {
        "scheduler_terminal_evidence.csv",
        "pm10_case_terminal_gate.csv",
        "pm10_steadiness_metric_context.csv",
        "pm10_split_use_decision.csv",
        "pm10_recirc_onset_summary.csv",
        "pm10_heat_pressure_evidence_inventory.csv",
        "no_mutation_guardrails.csv",
        "source_manifest.csv",
        "summary.json",
        "README.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["final_score"] == "not_performed"

    guardrails = read_csv(tmp_path / "no_mutation_guardrails.csv")
    assert {row["status"] for row in guardrails} == {"none"}
