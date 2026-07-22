import csv
import json

from tools.analyze import build_1d_model_hierarchy_ablation_ladder_packet as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_hierarchy_ladder_reports_no_current_score_or_freeze(tmp_path):
    summary = builder.build(tmp_path)

    assert summary["decision"] == "hierarchy_ablation_ladder_ready_no_freeze_no_score"
    assert summary["hierarchy_rows"] == 7
    assert summary["ablation_rows"] == 6
    assert summary["final_predictive_score_values"] == 0
    assert summary["candidate_freeze_allowed"] is False
    assert summary["fit_or_model_selection"] is False
    assert summary["validation_holdout_external_scoring"] is False
    assert summary["source_property_release"] is False

    ladder = read_csv(tmp_path / "model_hierarchy_ladder.csv")
    assert len(ladder) == 7
    assert {row["train_fit_allowed"] for row in ladder} == {"no"}
    assert {row["validation_holdout_external_score_allowed_now"] for row in ladder} == {"no"}
    assert {row["final_predictive_score_values"] for row in ladder} == {"0"}


def test_freeze_and_score_guardrails_are_closed(tmp_path):
    builder.build(tmp_path)

    gates = read_csv(tmp_path / "freeze_prerequisite_gate_table.csv")
    assert gates
    assert {row["release_allowed_now"] for row in gates} == {"no"}

    scores = read_csv(tmp_path / "final_score_guardrail_table.csv")
    assert scores
    assert {row["score_values_reported"] for row in scores} == {"0"}
    assert {row["allowed_now"] for row in scores} == {"no"}


def test_hierarchy_packet_writes_expected_files(tmp_path):
    builder.build(tmp_path)

    expected = {
        "model_hierarchy_ladder.csv",
        "ablation_evidence_matrix.csv",
        "freeze_prerequisite_gate_table.csv",
        "final_score_guardrail_table.csv",
        "figure_caption_targets.csv",
        "source_manifest.csv",
        "no_mutation_guardrails.csv",
        "summary.json",
        "README.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["native_output_mutation"] is False
    assert summary["registry_or_admission_mutation"] is False
    assert summary["scheduler_action"] is False
    assert summary["fluid_or_external_edit"] is False
