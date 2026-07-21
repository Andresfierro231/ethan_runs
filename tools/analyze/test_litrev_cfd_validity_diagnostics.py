from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_cfd_validity_builder(tmp_path: Path) -> None:
    out = tmp_path / "validity"
    subprocess.run(
        [sys.executable, str(ROOT / "tools/analyze/build_litrev_cfd_validity_diagnostics.py"), "--output-dir", str(out)],
        check=True,
    )
    rows = list(csv.DictReader((out / "cfd_single_stream_validity.csv").open()))
    limits = list(csv.DictReader((out / "coefficient_naming_limits.csv").open()))
    validation = json.load((out / "validation_report.json").open())
    assert rows
    assert limits
    assert validation["new_openfoam_extraction_performed"] is False
    assert {"single_stream_validity", "coefficient_naming_limit", "provenance_author_title"}.issubset(rows[0])
    assert {"f_D", "K", "Nu"}.issubset({row["coefficient_family"] for row in limits})


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_cfd_validity_builder(Path(tmp))
