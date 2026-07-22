from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_s13_upcomer_exchange_sampler_manifest_refresh_from_seeded_proxy as builder


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class S13SamplerManifestRefreshFromSeededProxyTests(unittest.TestCase):
    def test_proxy_rows_are_not_production_ready(self) -> None:
        rows = builder.proxy_manifest_rows()
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["sampler_proxy_ready"] == "true" for row in rows))
        self.assertTrue(all(row["production_sampler_ready"] == "false" for row in rows))
        self.assertTrue(all(row["Q_wall_W_ready"] == "false" for row in rows))

    def test_downstream_blocks_harvest_and_admission(self) -> None:
        gates = {row["gate"]: row for row in builder.downstream_rows()}
        self.assertEqual(gates["production_harvest"]["allowed"], "false")
        self.assertEqual(gates["same_qoi_uq"]["allowed"], "false")
        self.assertEqual(gates["s12_diagnostic_context"]["allowed"], "true")
        self.assertEqual(gates["s11_s15_s6_or_coefficient_admission"]["allowed"], "false")

    def test_build_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pkg"
            summary = builder.build(out)
            self.assertEqual(summary["sampler_proxy_ready_rows"], 3)
            self.assertEqual(summary["production_sampler_ready_rows"], 0)
            rows = read_rows(out / "sampler_proxy_manifest.csv")
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row["release_status"] == "sampler_proxy_ready_nonproduction" for row in rows))


if __name__ == "__main__":
    unittest.main()
