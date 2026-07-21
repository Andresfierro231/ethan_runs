from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_property_sensitivity_builder(tmp_path: Path) -> None:
    out = tmp_path / "property"
    subprocess.run(
        [sys.executable, str(ROOT / "tools/analyze/build_litrev_property_sensitivity.py"), "--output-dir", str(out)],
        check=True,
    )
    rows = list(csv.DictReader((out / "property_mode_matrix.csv").open()))
    summaries = list(csv.DictReader((out / "property_sensitivity_summary.csv").open()))
    validation = json.load((out / "validation_report.json").open())
    assert rows
    assert summaries
    assert validation["full_1d_rerun_performed"] is False
    assert {"Re_ratio_to_replication", "Pr_ratio_to_replication", "model_form_admission_flag"}.issubset(rows[0])
    assert any(row["property_mode"] == "jin_viscosity_parida_cp_santini_k" for row in rows)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_property_sensitivity_builder(Path(tmp))
