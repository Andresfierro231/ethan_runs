#!/usr/bin/env python3
"""Regression checks for thesis N2 upcomer exchange/Qwall/UQ panels."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, "tools/analyze/build_thesis_n2_upcomer_exchange_qwall_uq_paper_panels.py"], cwd=ROOT, check=True)
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["decision"] == "paper_panels_ready_diagnostic_only_no_single_stream_closure"
    assert summary["exact_Q_wall_W_released_rows"] == 3
    assert summary["same_qoi_uq_ready_rows"] == 0
    assert summary["ordinary_upcomer_closure_admitted"] is False
    assert summary["coefficient_admission_allowed"] is False
    assert len(rows("sampled_interface_summary_table.csv")) == 3
    assert len(rows("wall_core_temperature_contrast_table.csv")) == 3
    assert any(row["case_id"] == "source_side_equivalent" and row["Q_wall_W_released"] == "false" for row in rows("qwall_source_side_status_table.csv"))
    print("thesis N2 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
