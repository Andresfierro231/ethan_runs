#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import iso_timestamp, json_dump  # noqa: E402
from tools.extract.postprocessing_registry_common import (  # noqa: E402
    build_case_aggregation,
    default_source_ids,
    refresh_indexes,
    write_case_aggregation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate registered OpenFOAM postProcessing outputs into registry-local CSV and SQLite products."
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Repeat to restrict aggregation to selected registered source ids. Default: all registered cases.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or default_source_ids()
    written_runs: list[dict[str, str]] = []
    index_rows: list[dict[str, object]] = []
    total = len(source_ids)

    for index, source_id in enumerate(source_ids, start=1):
        print(f"[{index}/{total}] aggregating {source_id}", flush=True)
        payload = build_case_aggregation(source_id)
        outputs = write_case_aggregation(payload)
        written_runs.append({"source_id": source_id, **outputs})
        index_rows.append(payload["index_row"])
        print(f"[{index}/{total}] wrote {source_id} -> {outputs['normalized_csv']}", flush=True)

    index_outputs = refresh_indexes(index_rows)
    import_manifest = {
        "generated_at": iso_timestamp(),
        "task": "AGENT-130",
        "kind": "ethan_postprocessing_registry_pipeline",
        "storage_format_fast": "sqlite",
        "storage_format_tabular": "csv",
        "source_ids": source_ids,
        "run_outputs": written_runs,
        "index_outputs": index_outputs,
        "note": "SQLite was used instead of Parquet because the current environment does not have pyarrow/pandas installed.",
    }
    import_path = ROOT / "imports" / "2026-06-25_ethan_postprocessing_registry_pipeline.json"
    json_dump(import_path, import_manifest)
    print(json.dumps(import_manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
