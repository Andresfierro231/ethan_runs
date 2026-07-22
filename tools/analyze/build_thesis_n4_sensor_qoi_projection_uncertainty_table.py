#!/usr/bin/env python3
"""Build thesis N4 sensor/QOI projection uncertainty table package."""

from build_thesis_n1_frozen_runtime_legal_candidate_gate import build, out_dir, ROOT


def main() -> int:
    build("N4")
    print(f"wrote {out_dir('N4').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
