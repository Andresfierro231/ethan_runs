# Data Disclosure — Postprocessor Time-Series Analysis (AGENT-244)

## Sources (READ-ONLY; never mutated)

Native OpenFOAM `postProcessing` outputs under `jadyn_runs/**`:

| Quantity group | Path pattern | Column used | Unit |
|---|---|---|---|
| mdot | `postProcessing/mdot_<leg>/<startTime>/surfaceFieldValue.dat` | `sum(phi)` | kg/s |
| temperature | `postProcessing/temperature_probes/<startTime>/T` | per-probe columns | K |
| wall_temperature | `postProcessing/wall_temperature_probes/<startTime>/T` | per-probe columns | K |
| heat | `postProcessing/total_Q.dat` | column 2 | W |

## Handling

- **Continuations**: each functionObject may have several `<startTime>`
  subdirectories; they are concatenated and de-duplicated on the time column
  (later/higher start wins at overlaps).
- **Duplicates**: 52 postProcessing dirs found; byte-identical copies
  (e.g. `failed_stage_preserved` and staging mirrors) are detected by content
  fingerprint and excluded from analysis, leaving 47 unique cases.
  All are listed with their fingerprint in `case_inventory.csv`.
- **Representatives** (for the windowed trend + CLT): loop `mdot` uses the heater
  leg (all legs carry the same mass flow by continuity); `wall_temperature` uses
  the spatial mean across probes; `temperature` keeps all probes; `heat` uses
  `total_Q`. Every *individual* series still gets a full stats row in the
  per-case `stats.csv`.

## Units / sign conventions

- `sum(phi)` is the surfaceFieldValue flux integral through an oriented faceZone;
  for this compressible buoyant solver it is a mass flow in kg/s and its sign
  reflects the faceZone orientation (legs may differ in sign; magnitudes agree).
- Temperatures are in kelvin; `total_Q` is in watts (sign per the solver's
  convention — net loop heat).

## What is NOT done here

- No mesh/GCI convergence (all cases `coarse_no_gci`).
- No field-sample (velocity/PIV/wallHeatFlux field) processing — only scalar time
  series. Per-patch heat accounting lives in the patchwise heat ledger.
- A "steady" verdict describes time-series stationarity only; it does not certify
  the operating point (see the false-steady Q-perturbation caveat in README).

Window = last 300 s of simulated time. Every plotted value is
reproducible from the sources above via the reusable modules
`openfoam_timeseries.py`, `timeseries_stats.py`, `svg_timeseries_chart.py`.
