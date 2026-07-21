# AGENT-287 CFD Radiative Boundary Correction

Timestamp: 2026-07-13T15:37:07-0500
Role: Coordinator / Implementer / Tester / Writer

## Observed Output

Built
`work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/`.

Primary files:

- `README.md`
- `cfd_emissivity_by_run.csv`
- `radiation_guidance_decision.json`
- `source_index.csv`
- `run_metadata.json`

Also updated:

- `.agent/DECISIONS.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `tools/analyze/run_cfd_bc_no_radiation_1d_parity.py`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/run_metadata.json`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/cfd_boundary_condition_contract_no_radiation.csv`
- `imports/2026-07-13_cfd_bc_no_radiation_1d_parity.json`
- `operational_notes/07-26/13/2026-07-13_cfd_radiative_boundary_correction.md`

## Evidence

AGENT-263 provides the authoritative patch-level boundary table for admitted
Salt 2/3/4 Jin mainline rows. Summarized from that table:

| Case | rcExternalTemperature patches | emissivity | Tsur K | Ta K |
| --- | ---: | ---: | ---: | ---: |
| Salt 2 | 36 | 0.95 | 299.19 | 299.19 |
| Salt 3 | 36 | 0.95 | 299.79 | 299.79 |
| Salt 4 | 36 | 0.95 | 299.97 | 299.97 |

AGENT-277 provides the publication-support microcase evidence that
`emissivity` and `Tsur` affect realized `wallHeatFlux`. The final-time
microcase deltas are:

- emissivity `0.95 -> 0.10`: `-658.64271204 W`
- emissivity `0.95 -> 0.00`: `-809.14474124 W`
- `Tsur 299.19 K -> 350 K`: `+1912.49758926 W`

## Interpretation

Ethan CFD should not be described as no-radiation. The supported wording is:
`rcExternalTemperature` includes radiative exchange through emissivity/Tsur, but
current outputs expose only total `wallHeatFlux`; no separate `qr` or radiation
heat-rate ledger is available.

For 1D agents:

- Do not add a separate radiation term on top of CFD `wallHeatFlux`.
- Do not call AGENT-279 radiation-off replay CFD parity.
- Predictive 1D runs from physical setup inputs need a radiation-capable
  external-loss model, or radiation disabled must be labeled as sensitivity.

## Commands

```bash
python tools/analyze/build_cfd_radiative_boundary_guidance.py
pytest -q tools/analyze/test_cfd_radiative_boundary_guidance.py
python -m py_compile tools/analyze/run_cfd_bc_no_radiation_1d_parity.py tools/analyze/test_cfd_bc_no_radiation_1d_parity.py tools/analyze/build_cfd_radiative_boundary_guidance.py tools/analyze/test_cfd_radiative_boundary_guidance.py
python tools/analyze/test_cfd_bc_no_radiation_1d_parity.py
python tools/analyze/run_cfd_bc_no_radiation_1d_parity.py --strict
python -m json.tool imports/2026-07-13_cfd_bc_no_radiation_1d_parity.json
python -m json.tool work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/radiation_guidance_decision.json
```

Focused tests passed: 7/7.

## Boundaries

No native CFD solver outputs, registry rows, scheduler state, or external Fluid
source files were modified. The AGENT-279 rerun used Fluid read-only and only
regenerated repo-local work-product files.
