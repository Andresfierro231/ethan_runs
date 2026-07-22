# rcExternalTemperature Publication Evidence

Generated: `2026-07-13T18:17:07+00:00`
Task: `AGENT-277`

## Purpose

This package strengthens AGENT-264 by searching for the actual custom
`rcExternalTemperature` source and, when source is unavailable, attempting an
isolated OpenFOAM 13 microcase that varies only `emissivity` or `Tsur`.

## Outputs

- `source_probe.csv`
- `binary_probe_refresh.csv`
- `microcase_matrix.csv`
- `microcase_run_results.csv`
- `wallHeatFlux_delta_summary.csv`
- `publication_evidence_decision.json`
- `run_metadata.json`

## Decision

- Evidence class: `microcase_confirmed`
- Source confirmed: `False`
- Microcase confirmed: `True`
- Microcase statuses: `['success']`

## Final-Time Microcase Deltas

The microcase parser aggregates only the latest written `wallHeatFlux.dat` time
and combines the `glass+roof` rcExternalTemperature patches. Mean heat flux is
reported as total Q divided by inferred combined patch area.

- `baseline_vs_emissivity_low` (emissivity): `delta_Q = -658.64271204 W`, `delta_q = -21.513354567708234 W/m2`, `effect_detected = True`
- `baseline_vs_emissivity_zero` (emissivity): `delta_Q = -809.1447412399999 W`, `delta_q = -26.429226953318217 W/m2`, `effect_detected = True`
- `baseline_vs_tsur_high` (Tsur): `delta_Q = 1912.4975892599998 W`, `delta_q = 62.46822140808613 W/m2`, `effect_detected = True`

## Interpretation Boundary

This package does not mutate native Ethan solver outputs. Microcases, if run,
are generated under this package directory from an OF13 tutorial base. A
positive microcase result supports the publication statement that changing
`emissivity` or `Tsur` changes `wallHeatFlux`; it does not expose a separable
radiation heat-flux output. Until such a separate output exists, 1D parity
should continue to treat radiation in `rcExternalTemperature` as inseparable
from total OpenFOAM `wallHeatFlux`.
