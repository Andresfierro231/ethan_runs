#!/usr/bin/env python3
"""openfoam_timeseries.py — parse OpenFOAM postProcessing scalar time series.

Reusable, dependency-free (stdlib only) reader for the scalar functionObject
outputs written by the Ethan TAMU loop CFD cases. It handles continuation runs
(multiple `<startTime>` subdirectories per functionObject) by concatenating and
de-duplicating on the time column, and it never mutates the source tree.

Supported inputs
----------------
- mass flow    `postProcessing/mdot_<leg>/<startTime>/surfaceFieldValue.dat`
               column `sum(phi)` → one Series per leg (group "mdot").
- temperature  `postProcessing/temperature_probes/<startTime>/T`
               one Series per probe column (group "temperature").
- wall temp    `postProcessing/wall_temperature_probes/<startTime>/T`
               one Series per probe column (group "wall_temperature").
- heat         `postProcessing/total_Q.dat` (bare `time  Q`) → one Series
               (group "heat").

Units disclosure
----------------
`sum(phi)` is the surfaceFieldValue flux integral through an oriented faceZone;
for the compressible buoyant solver used here it is a mass flow in kg/s, and the
sign reflects the faceZone orientation (legs differ). Temperatures are K; Q is W.
These conventions are stated wherever a Series is produced and echoed in the
figure package's DATA_DISCLOSURE.md.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

# Friendly leg labels (fall back to the raw suffix if unknown).
MDOT_LEG_LABELS = {
    "mdot_pipeleg_lower_05_straight": "lower (heater)",
    "mdot_pipeleg_right_02_middle": "right (downcomer)",
    "mdot_pipeleg_left_04_test_section": "left (test section)",
    "mdot_pipeleg_upper_05_cooler": "upper (cooler)",
}

GROUP_UNITS = {
    "mdot": "kg/s",
    "temperature": "K",
    "wall_temperature": "K",
    "heat": "W",
}


@dataclass
class Series:
    name: str                      # unique label within a case
    group: str                     # mdot | temperature | wall_temperature | heat
    unit: str
    t: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.t)


@dataclass
class CaseInfo:
    case_root: Path
    slug: str
    postprocessing: Path
    fingerprint: str
    duplicate_of: str | None = None


# ---------------------------------------------------------------------------
# Low-level readers
# ---------------------------------------------------------------------------

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _numeric_rows(path: Path) -> list[list[float]]:
    """Yield numeric rows from a whitespace-delimited .dat, skipping # comments."""
    rows: list[list[float]] = []
    with path.open() as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            toks = s.replace("\t", " ").split()
            vals: list[float] = []
            ok = True
            for tok in toks:
                try:
                    vals.append(float(tok))
                except ValueError:
                    ok = False
                    break
            if ok and vals:
                rows.append(vals)
    return rows


def _startdirs(fo_dir: Path) -> list[Path]:
    """Time-start subdirectories of a functionObject dir, ascending by start time."""
    subs = [p for p in fo_dir.iterdir() if p.is_dir()]

    def keyf(p: Path) -> float:
        try:
            return float(p.name)
        except ValueError:
            return float("inf")

    return sorted(subs, key=keyf)


def _merge_by_time(pairs: list[tuple[float, float]]) -> tuple[list[float], list[float]]:
    """Merge (t, y) keeping the last-written value at duplicate times; sort by t."""
    d: dict[float, float] = {}
    for t, y in pairs:
        d[round(t, 6)] = y          # later (higher start dir) overwrites at overlaps
    ts = sorted(d)
    return ts, [d[t] for t in ts]


# ---------------------------------------------------------------------------
# Per-functionObject parsers
# ---------------------------------------------------------------------------

def parse_surface_field_value(fo_dir: Path, group: str = "mdot") -> Series:
    """mdot surfaceFieldValue.dat → Series (col 0 time, col 1 sum(phi))."""
    name = fo_dir.name
    label = MDOT_LEG_LABELS.get(name, name.replace("mdot_pipeleg_", ""))
    pairs: list[tuple[float, float]] = []
    src: list[str] = []
    for sd in _startdirs(fo_dir):
        dat = sd / "surfaceFieldValue.dat"
        if not dat.exists():
            continue
        src.append(str(dat))
        for row in _numeric_rows(dat):
            if len(row) >= 2:
                pairs.append((row[0], row[1]))
    t, y = _merge_by_time(pairs)
    return Series(name=label, group=group, unit=GROUP_UNITS[group], t=t, y=y,
                  source_files=src, meta={"functionobject": name, "column": "sum(phi)"})


def parse_probe_set(fo_dir: Path, group: str, field_file: str = "T") -> list[Series]:
    """Probe file (`# Probe N (x y z)` header + time + per-probe columns)."""
    unit = GROUP_UNITS[group]
    coords: dict[int, str] = {}
    # coordinates from any subdir header (assume stable layout)
    per_probe: dict[int, list[tuple[float, float]]] = {}
    src: list[str] = []
    for sd in _startdirs(fo_dir):
        f = sd / field_file
        if not f.exists():
            continue
        src.append(str(f))
        with f.open() as fh:
            for line in fh:
                m = re.match(r"#\s*Probe\s+(\d+)\s*\(([^)]*)\)", line)
                if m:
                    coords[int(m.group(1))] = m.group(2).strip()
        for row in _numeric_rows(f):
            t = row[0]
            for i, val in enumerate(row[1:]):
                per_probe.setdefault(i, []).append((t, val))
    series: list[Series] = []
    for i in sorted(per_probe):
        t, y = _merge_by_time(per_probe[i])
        loc = coords.get(i, "")
        name = f"probe {i}" + (f" ({loc})" if loc else "")
        series.append(Series(name=name, group=group, unit=unit, t=t, y=y,
                             source_files=src,
                             meta={"functionobject": fo_dir.name, "probe_index": i,
                                   "location": loc}))
    return series


def parse_total_q(path: Path) -> Series:
    """total_Q.dat → Series (col 0 time, col 1 Q [W])."""
    pairs = [(r[0], r[1]) for r in _numeric_rows(path) if len(r) >= 2]
    t, y = _merge_by_time(pairs)
    return Series(name="total_Q", group="heat", unit=GROUP_UNITS["heat"], t=t, y=y,
                  source_files=[str(path)], meta={"functionobject": "total_Q"})


# ---------------------------------------------------------------------------
# Case-level loading + discovery
# ---------------------------------------------------------------------------

def load_case_series(pp_dir: Path) -> list[Series]:
    """All available scalar Series for one postProcessing directory."""
    out: list[Series] = []
    for sub in sorted(pp_dir.iterdir()):
        if sub.is_dir() and sub.name.startswith("mdot_pipeleg_"):
            s = parse_surface_field_value(sub, "mdot")
            if len(s):
                out.append(s)
    tp = pp_dir / "temperature_probes"
    if tp.is_dir():
        out += [s for s in parse_probe_set(tp, "temperature") if len(s)]
    wt = pp_dir / "wall_temperature_probes"
    if wt.is_dir():
        out += [s for s in parse_probe_set(wt, "wall_temperature") if len(s)]
    tq = pp_dir / "total_Q.dat"
    if tq.exists():
        s = parse_total_q(tq)
        if len(s):
            out.append(s)
    return out


def _fingerprint(pp_dir: Path) -> str:
    """Content fingerprint for duplicate detection (cheap: sizes + a few tails)."""
    h = hashlib.md5()
    tq = pp_dir / "total_Q.dat"
    if tq.exists():
        h.update(tq.read_bytes())
    for name in sorted(p.name for p in pp_dir.glob("mdot_pipeleg_*")):
        fo = pp_dir / name
        for sd in _startdirs(fo):
            dat = sd / "surfaceFieldValue.dat"
            if dat.exists():
                h.update(f"{name}:{dat.stat().st_size}".encode())
                # include last line to distinguish continuations
                try:
                    h.update(dat.read_bytes()[-256:])
                except OSError:
                    pass
    return h.hexdigest()


def _slug(case_root: Path, repo_root: Path) -> str:
    try:
        rel = case_root.relative_to(repo_root)
    except ValueError:
        rel = case_root
    parts = str(rel).replace("jadyn_runs/", "").split("/")
    # keep informative parts, drop generic "case_stage"
    keep = [p for p in parts if p not in {"case_stage", "runs"}]
    slug = "__".join(keep)
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", slug)


def discover_cases(repo_root: Path, search_root: Path | None = None) -> list[CaseInfo]:
    """Find every postProcessing dir with scalar series; flag duplicates."""
    search_root = search_root or (repo_root / "jadyn_runs")
    pps = sorted(search_root.rglob("postProcessing"))
    seen: dict[str, str] = {}
    cases: list[CaseInfo] = []
    for pp in pps:
        if not pp.is_dir():
            continue
        # must have at least one scalar series worth analysing
        has = any((pp / "total_Q.dat").exists() for _ in [0]) or \
            any(p.name.startswith("mdot_pipeleg_") for p in pp.iterdir() if p.is_dir())
        if not has:
            continue
        case_root = pp.parent
        slug = _slug(case_root, repo_root)
        fp = _fingerprint(pp)
        dup = seen.get(fp)
        if dup is None:
            seen[fp] = slug
        cases.append(CaseInfo(case_root=case_root, slug=slug, postprocessing=pp,
                              fingerprint=fp, duplicate_of=dup))
    return cases
