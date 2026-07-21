from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_reset_named_losses_builder(tmp_path: Path) -> None:
    out = tmp_path / "reset"
    subprocess.run(
        [sys.executable, str(ROOT / "tools/analyze/build_litrev_reset_named_losses.py"), "--output-dir", str(out)],
        check=True,
    )
    resets = list(csv.DictReader((out / "reset_distance_map.csv").open()))
    losses = list(csv.DictReader((out / "named_pressure_loss_table.csv").open()))
    validation = json.load((out / "validation_report.json").open())
    assert resets
    assert losses
    assert validation["global_friction_multiplier_recommended"] is False
    assert {"straight_section", "branch_apparent", "component_K", "cluster_K"} & {row["loss_class"] for row in losses}
    assert {"pressure_basis", "velocity_basis", "provenance_author_title"}.issubset(losses[0])


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_reset_named_losses_builder(Path(tmp))
