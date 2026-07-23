#!/usr/bin/env python3
"""Print a bounded preview of selected CSV columns and rows."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def _split_cols(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--cols", help="Comma-separated columns to print.")
    parser.add_argument("--rows", type=int, default=20, help="Maximum data rows to print.")
    parser.add_argument("--grep", help="Only print rows whose full row text contains this substring.")
    parser.add_argument("--delimiter", default=",")
    args = parser.parse_args()

    if args.rows < 0:
        print("ERROR: --rows must be nonnegative", file=sys.stderr)
        return 2

    wanted = _split_cols(args.cols)
    printed = 0
    matched = 0
    with args.csv_path.open(newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh, delimiter=args.delimiter)
        if reader.fieldnames is None:
            print(f"ERROR: {args.csv_path}: missing header", file=sys.stderr)
            return 1
        fields = wanted or reader.fieldnames
        missing = [field for field in fields if field not in reader.fieldnames]
        if missing:
            print(f"ERROR: {args.csv_path}: missing columns: {', '.join(missing)}", file=sys.stderr)
            print(f"available: {', '.join(reader.fieldnames)}", file=sys.stderr)
            return 1

        writer = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in reader:
            row_text = " ".join(str(row.get(name, "")) for name in reader.fieldnames)
            if args.grep and args.grep not in row_text:
                continue
            matched += 1
            if printed >= args.rows:
                continue
            writer.writerow({field: row.get(field, "") for field in fields})
            printed += 1

    print(f"# preview_csv: printed={printed} matched={matched} limit={args.rows}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
