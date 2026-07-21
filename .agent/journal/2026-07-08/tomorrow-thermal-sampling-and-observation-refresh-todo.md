# Tomorrow Thermal Sampling And Observation Refresh TODO

Date: `2026-07-08`
Task: `AGENT-220`
Role: Coordinator / Writer

## TODO

- Run a bounded compute-node OpenFOAM sampling pass for the missing thermal
  control-volume interfaces.
- Separately bracket heater interiors with physical inlet/outlet planes.
- Separately bracket cooler and reducer interiors with physical inlet/outlet
  planes.
- Bracket junction rows so grouped junction heat losses can be tested against
  enthalpy-flow changes.
- Improve high-recirculation interface fidelity; keep recirculation rows
  diagnostic until a defensible multi-stream control-volume treatment exists.
- Keep radiation absent unless OpenFOAM exposes a `qr` output term; do not infer
  radiation from emissivity metadata alone.
- Refresh the canonical observation table to consume
  `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/**`.

## Observed Facts

- The physical-interface heat package exists and validates with zero errors.
- Current sampling uses existing `secmeanSurfaces` planes.
- Existing planes do not isolate heater interior, cooler/reducer interior, or
  junction control volumes.
- Radiation is still no-`qr` in the current evidence.

## Inferred Interpretation

Tomorrow's thermal work should prioritize missing OpenFOAM sampling geometry
before further model-form claims. The observation table refresh is the next
technical step after sampling because downstream model bakeoff should consume a
single canonical thermal validation contract.

## Blockers

- Missing heater/cooler/junction bracketing planes.
- Recirculation-contaminated interfaces.
- No `qr` output term for radiation heat accounting.
- Mesh uncertainty remains separate and unresolved.

## Exact Files Used

- `.agent/BOARD.md`
- `operational_notes/07-26/08/2026-07-08_tomorrow_thermal_sampling_and_observation_refresh_todo.md`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/summary.json`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/README.md`

## Recommended Next Action

Claim `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`, then claim
`TODO-OBSERVATION-TABLE-THERMAL-REFRESH` once the sampling package is available.
