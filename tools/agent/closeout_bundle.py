#!/usr/bin/env python3
"""Compatibility alias for closeout_stub.py."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.closeout_stub import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
