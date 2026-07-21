from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_heat_loss_builder(tmp_path: Path) -> None:
    out = tmp_path / "heat_loss"
    subprocess.run(
        [sys.executable, str(ROOT / "tools/analyze/build_litrev_heat_loss_calibration.py"), "--output-dir", str(out)],
        check=True,
    )
    ledger = list(csv.DictReader((out / "separated_heat_loss_ledger.csv").open()))
    admission = list(csv.DictReader((out / "heat_closure_admission.csv").open()))
    validation = json.load((out / "validation_report.json").open())
    assert ledger
    assert admission
    assert validation["new_openfoam_extraction_performed"] is False
    assert {"heat_path", "calibration_admission", "provenance_author_title"}.issubset(ledger[0])
    assert all(row["internal_Nu_admission"] == "blocked_from_absorbing_external_heat_loss" for row in admission)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_heat_loss_builder(Path(tmp))
