# AGENT-277 rcExternalTemperature Publication Evidence

Timestamp: 2026-07-13T13:14:44-0500
Role: Coordinator / Implementer / Tester / Writer

## Observed Output

Built
`work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/`.

Primary files:

- `source_probe.csv`
- `binary_probe_refresh.csv`
- `microcase_matrix.csv`
- `microcase_run_results.csv`
- `wallHeatFlux_delta_summary.csv`
- `publication_evidence_decision.json`
- `run_metadata.json`
- `README.md`

The decision file reports:

- `emissivity_Tsur_affect_heat_flux = yes`
- `evidence_class = microcase_confirmed`
- `source_confirmed = false`
- `microcase_confirmed = true`
- `separable_radiation_output_available = no_separate_output_observed`

## Evidence

The custom C++ source was not found in targeted accessible locations:
`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/RCWallBC/`,
the adjacent Ethan data directory, or the current runtime-library locations.
The readable custom library
`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so`
has SHA256
`34f4c7c2acb62d9b7b817efd5abd8b229313c2d19f8f12b21da5852d54f81f09` and exposes
`Foam::rcExternalTemperatureFvPatchScalarField::updateCoeffs()` plus radial and
areal thermal symbols in `nm -C`/`objdump -T` output.

The script created a task-scoped OF13 `roomHeating` copy for each variant,
loaded `libRCWallBC.so`, applied `rcExternalTemperature` to `glass` and inherited
it on `roof`, and ran `blockMesh`, `createZones`, and `foamRun`. The parser uses
the latest written time only and reports the combined `glass+roof` heat rate and
area-weighted mean heat flux.

Final-time `glass+roof` results:

| Variant | Changed parameter | Q [W] | q [W/m2] |
| --- | --- | ---: | ---: |
| baseline | none | 7.49863434 | 0.244929119 |
| emissivity_low | emissivity `0.95 -> 0.10` | -651.14407770 | -21.268425448 |
| emissivity_zero | emissivity `0.95 -> 0.00` | -801.64610690 | -26.184297834 |
| tsur_high | `Tsur 299.19 K -> 350 K` | 1919.99622360 | 62.713150527 |

Relative to baseline:

- emissivity `0.95 -> 0.10`: `delta_Q = -658.64271204 W`
- emissivity `0.95 -> 0.00`: `delta_Q = -809.14474124 W`
- `Tsur 299.19 K -> 350 K`: `delta_Q = +1912.49758926 W`

## Interpretation

This is stronger than the prior binary-only AGENT-264 workflow evidence because
it demonstrates an executable OpenFOAM response when only `emissivity` or only
`Tsur` is changed. It is still not source-level proof of the custom
implementation because the actual `rcExternalTemperature` source was not
recovered.

For thesis or paper language, cite this as an OF13 microcase response using the
same compiled custom boundary library. The result supports that `emissivity` and
`Tsur` affect realized `wallHeatFlux`. It does not expose a separate radiation
heat-flux channel, so 1D parity should continue treating radiation as
inseparable from the total OpenFOAM `wallHeatFlux` unless a later source audit
or solver output provides a separate `qr`/radiation term.

## Commands

```bash
python tools/analyze/build_rc_external_temperature_publication_evidence.py --strict
pytest -q tools/analyze/test_rc_external_temperature_publication_evidence.py
python -m py_compile tools/analyze/build_rc_external_temperature_publication_evidence.py tools/analyze/test_rc_external_temperature_publication_evidence.py
```

## Boundaries

No native Ethan solver outputs were mutated. No staged mainline case, external
Fluid file, registry entry, or scheduler job was changed. Solver execution was
limited to generated AGENT-277 microcases under the work product directory.
