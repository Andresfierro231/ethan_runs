#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from tools.analyze.build_ethan_case_analysis_package import main as shared_main
from tools.common import WORKSPACE_ROOT


LEGACY_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_legwise_hydraulic_budget_package"


if __name__ == "__main__":
    raise SystemExit(shared_main(default_output_dir=Path(LEGACY_OUTPUT_DIR)))
