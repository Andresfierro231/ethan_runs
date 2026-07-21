# CFD Radiative Boundary Correction

Date: 2026-07-13
Task: AGENT-287
Role: Coordinator / Implementer / Tester / Writer

## Decision

Do not describe the admitted Ethan Salt CFD thermal boundary as no-radiation.
The current evidence says the CFD includes radiative exchange through the
custom `rcExternalTemperature` boundary condition.

The key distinction is:

- `emissivity` and `Tsur` affect realized OpenFOAM `wallHeatFlux`.
- There is no separate exported `qr` or radiation heat-rate ledger in the
  current outputs.
- Therefore radiation is inseparable from total CFD `wallHeatFlux`.

## Authoritative Sources

- Human-readable CFD setup reference:
  `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- Per-run generated guidance:
  `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/README.md`
- Per-run emissivity/Tsur table:
  `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/cfd_emissivity_by_run.csv`
- Source patch table:
  `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`
- AGENT-277 microcase deltas:
  `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/wallHeatFlux_delta_summary.csv`
- Agent-facing policy:
  `.agent/DECISIONS.md`

## Per-Run Values

From the AGENT-263 patch table, each admitted Salt mainline row has 36
`rcExternalTemperature` patches spanning `ambient_wall`, `heater`,
`junction_other`, and `test_section` roles.

| Case | emissivity | Tsur K | Ta K |
| --- | ---: | ---: | ---: |
| Salt 2 | 0.95 | 299.19 | 299.19 |
| Salt 3 | 0.95 | 299.79 | 299.79 |
| Salt 4 | 0.95 | 299.97 | 299.97 |

AGENT-277 microcase evidence with the compiled custom boundary library:

| Perturbation | Final-time delta Q W |
| --- | ---: |
| emissivity `0.95 -> 0.10` | -658.64271204 |
| emissivity `0.95 -> 0.00` | -809.14474124 |
| `Tsur 299.19 K -> 350 K` | 1912.49758926 |

## Instructions For 1D Agents

- If using CFD `wallHeatFlux` as a CFD-informed replay input, do not add a
  separate 1D radiation term on top of that heat rate.
- If building a forward/predictive 1D model from physical setup inputs, include
  radiative external heat-loss capability using emissivity and surroundings, or
  explicitly label radiation disabled as a sensitivity.
- The AGENT-279 radiation-off package remains useful for sensitivity and
  debugging, but it is not CFD parity after AGENT-277/287.
- Do not use the older phrase "force radiation off to match CFD assumptions."

## Remaining Limitations

The actual custom `rcExternalTemperature` source has not been recovered. For
publication wording, cite the compiled-library evidence and the task-scoped
OF13 microcase response, not source-level proof. The radiative contribution is
not separable from total OpenFOAM `wallHeatFlux` with the current outputs.
