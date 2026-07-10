"""Tests for openfoam_timeseries.py (AGENT-244)."""

from __future__ import annotations

import shutil
from pathlib import Path

import openfoam_timeseries as ot


def _make_case(root: Path) -> Path:
    """Build a tiny synthetic postProcessing tree with a continuation restart."""
    pp = root / "case_stage" / "cs" / "postProcessing"
    # mdot with two start dirs (0 and 5) overlapping at t=5
    d0 = pp / "mdot_pipeleg_lower_05_straight" / "0"
    d5 = pp / "mdot_pipeleg_lower_05_straight" / "5"
    d0.mkdir(parents=True)
    d5.mkdir(parents=True)
    (d0 / "surfaceFieldValue.dat").write_text(
        "# Selection : x\n# Time\tsum(phi)\n"
        "0\t-1.0\n1\t-1.1\n2\t-1.2\n3\t-1.3\n4\t-1.4\n5\t-9.9\n")  # t=5 stale
    (d5 / "surfaceFieldValue.dat").write_text(
        "# Time\tsum(phi)\n5\t-1.5\n6\t-1.6\n7\t-1.7\n")           # t=5 fresh wins
    # temperature probes, 2 probes
    tp = pp / "temperature_probes" / "0"
    tp.mkdir(parents=True)
    (tp / "T").write_text(
        "# Probe 0 (1 2 3)\n# Probe 1 (4 5 6)\n# Time 0 1\n"
        "0\t400\t500\n1\t401\t501\n2\t402\t502\n")
    # total_Q
    (pp / "total_Q.dat").write_text("1\t-9.5\n2\t-9.4\n3\t-9.3\n")
    return pp


def test_parse_mdot_merges_continuations(tmp_path: Path) -> None:
    pp = _make_case(tmp_path / "c1")
    s = ot.parse_surface_field_value(pp / "mdot_pipeleg_lower_05_straight")
    assert s.group == "mdot" and s.unit == "kg/s"
    assert s.name == "lower (heater)"
    assert s.t == [0, 1, 2, 3, 4, 5, 6, 7]
    # t=5 value comes from the later start dir (-1.5), not the stale -9.9
    assert s.y[s.t.index(5)] == -1.5


def test_parse_probes(tmp_path: Path) -> None:
    pp = _make_case(tmp_path / "c2")
    ser = ot.parse_probe_set(pp / "temperature_probes", "temperature")
    assert len(ser) == 2
    assert ser[0].unit == "K"
    assert "probe 0" in ser[0].name and "1 2 3" in ser[0].name
    assert ser[1].y == [500, 501, 502]


def test_parse_total_q(tmp_path: Path) -> None:
    pp = _make_case(tmp_path / "c3")
    s = ot.parse_total_q(pp / "total_Q.dat")
    assert s.group == "heat" and s.unit == "W"
    assert s.t == [1, 2, 3]
    assert s.y == [-9.5, -9.4, -9.3]


def test_load_case_series_groups(tmp_path: Path) -> None:
    pp = _make_case(tmp_path / "c4")
    ser = ot.load_case_series(pp)
    groups = sorted({s.group for s in ser})
    assert groups == ["heat", "mdot", "temperature"]


def test_discover_dedupes_identical_trees(tmp_path: Path) -> None:
    a = _make_case(tmp_path / "runA")
    # exact copy → same fingerprint → flagged as duplicate
    shutil.copytree(tmp_path / "runA", tmp_path / "runB")
    cases = ot.discover_cases(tmp_path, search_root=tmp_path)
    assert len(cases) == 2
    uniq = [c for c in cases if c.duplicate_of is None]
    dups = [c for c in cases if c.duplicate_of is not None]
    assert len(uniq) == 1
    assert len(dups) == 1
    assert dups[0].fingerprint == uniq[0].fingerprint


def test_merge_by_time_sorted_and_deduped() -> None:
    t, y = ot._merge_by_time([(3.0, 30.0), (1.0, 10.0), (2.0, 20.0), (2.0, 99.0)])
    assert t == [1.0, 2.0, 3.0]
    assert y[t.index(2.0)] == 99.0   # last write wins
