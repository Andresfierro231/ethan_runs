# CFD Radiative Boundary Guidance

Generated: `2026-07-13T20:31:09+00:00`
Task: `AGENT-287`

## Decision

Ethan CFD should not be described as no-radiation. The admitted Salt CFD
`rcExternalTemperature` patches carry `emissivity` and `Tsur`, and AGENT-277's
OF13 microcase evidence shows those fields affect realized `wallHeatFlux`.

AGENT-277 decision: `yes`
with evidence class `microcase_confirmed`.

There is still no separate exported `qr`/radiation heat ledger. Radiation is
therefore inseparable from total OpenFOAM `wallHeatFlux` in the available CFD
outputs.

## Per-Run Values

| Case | rcExternalTemperature patches | Roles | emissivity | Tsur K | Ta K |
| --- | ---: | --- | --- | --- | --- |
| salt_2 | 36 | ambient_wall;heater;junction_other;test_section | 0.95 | 299.19 | 299.19 |
| salt_3 | 36 | ambient_wall;heater;junction_other;test_section | 0.95 | 299.79 | 299.79 |
| salt_4 | 36 | ambient_wall;heater;junction_other;test_section | 0.95 | 299.97 | 299.97 |

## Microcase Evidence

- `baseline_vs_emissivity_low`: `delta_Q = -658.64271204 W`, `effect_detected = True`
- `baseline_vs_emissivity_zero`: `delta_Q = -809.1447412399999 W`, `effect_detected = True`
- `baseline_vs_tsur_high`: `delta_Q = 1912.4975892599998 W`, `effect_detected = True`

## Instructions For 1D Agents

- For CFD-informed replay that consumes CFD `wallHeatFlux`, do not add a
  separate 1D radiation term on top of that heat rate.
- For forward/predictive 1D modeling from physical setup inputs, the external
  loss model must be radiation-capable, or the run must be labeled explicitly
  as a radiation-disabled sensitivity rather than CFD parity.
- The old AGENT-279 no-radiation replay remains useful as a diagnostic
  sensitivity. It is superseded as a statement of what the CFD did.

## Authoritative Sources

- `cfd_emissivity_by_run.csv` in this package.
- AGENT-263 patch table:
  `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`.
- AGENT-277 publication evidence:
  `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/publication_evidence_decision.json` and `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/wallHeatFlux_delta_summary.csv`.
- Human-readable CFD setup reference:
  `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`.
- Agent-facing policy:
  `.agent/DECISIONS.md`.
