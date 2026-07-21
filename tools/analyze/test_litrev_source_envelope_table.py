from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_source_envelope_builder_outputs_required_tables(tmp_path: Path) -> None:
    out = tmp_path / "source_envelope"
    subprocess.run(
        [sys.executable, str(ROOT / "tools/analyze/build_litrev_source_envelope_table.py"), "--output-dir", str(out)],
        check=True,
    )
    rows = list(csv.DictReader((out / "branch_source_envelope.csv").open()))
    flags = list(csv.DictReader((out / "source_overlap_flags.csv").open()))
    validation = json.load((out / "validation_report.json").open())
    assert rows
    assert flags
    assert validation["branch_rows"] == len(rows)
    required = {"Re", "Pr", "Gr", "Ri", "Ra", "Gz", "L_over_D", "provenance_author_title"}
    assert {"Re", "Pr", "Gr", "Ri", "Ra", "Gz", "L_over_D"}.issubset(rows[0])
    assert required - set(flags[0]) == {"Re", "Pr", "Gr", "Ri", "Ra", "Gz", "L_over_D"}
    assert any(row["candidate_source"].startswith("chen_2017") for row in flags)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_source_envelope_builder_outputs_required_tables(Path(tmp))
