import csv

from tools.analyze import build_thesis_study_recirculation_fraction_onset_evidence_packet as builder


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_recirculation_onset_builder_fail_closes_admission_paths(tmp_path):
    summary = builder.build(tmp_path)

    assert summary["status"] == "complete"
    assert summary["closed_recirc_fraction_admitted"] is False
    assert summary["ri_admitted"] is False
    assert summary["ordinary_upcomer_closure_admitted"] is False
    assert summary["exchange_cell_coefficient_admitted"] is False
    assert summary["native_output_mutation"] is False
    assert summary["registry_mutation"] is False
    assert summary["scheduler_launch_by_this_packet"] is False

    claims = read_csv(tmp_path / "claim_boundary_table.csv")
    assert claims
    forbidden_claims = [row for row in claims if row["claim_type"] == "forbidden"]
    assert any("closed recirculation fraction" in row["claim_text"] for row in forbidden_claims)
    assert any("Ordinary upcomer Nu" in row["claim_text"] for row in forbidden_claims)

    gates = read_csv(tmp_path / "evidence_availability_gate.csv")
    blocked = {row["evidence_item"]: row for row in gates}
    assert blocked["closed recirculation fraction"]["status"] == "blocked"
    assert blocked["closed recirculation fraction"]["use_allowed"] == "false"
    assert blocked["Richardson number for S13 onset packet"]["status"] == "blocked"
    assert blocked["Richardson number for S13 onset packet"]["use_allowed"] == "false"
    assert blocked["medium/fine exact-label rows"]["use_allowed"] == "false"


def test_recirculation_onset_builder_writes_writer_packet_files(tmp_path):
    builder.build(tmp_path)

    expected = {
        "recirculation_onset_metric_table.csv",
        "velocity_figure_evidence.csv",
        "reverse_flow_topology_proxy.csv",
        "onset_recirculation_proxy_table.csv",
        "s13_exchange_tau_proxy_table.csv",
        "same_qoi_temporal_uq_boundary.csv",
        "evidence_availability_gate.csv",
        "figure_table_targets.csv",
        "claim_boundary_table.csv",
        "source_manifest.csv",
        "no_mutation_guardrails.csv",
        "summary.json",
        "README.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
