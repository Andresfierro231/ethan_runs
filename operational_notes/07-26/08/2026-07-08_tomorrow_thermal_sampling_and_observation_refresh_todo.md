# Tomorrow TODO: Thermal Sampling And Observation Refresh

Date: `2026-07-08`
Task: `AGENT-220`

## Purpose

Capture the next thermal-ledger work for tomorrow after
`TODO-HEAT-ENTHALPY-INTERFACE-LEDGER` completed the first physical-interface
enthalpy package. The new package is useful for validation, but it still relies
on existing span/interface planes and does not yet isolate all physical
heat-source/sink control volumes.

## Tomorrow TODO List

1. Claim `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`.
2. Prepare a bounded compute-node OpenFOAM sampling run; do not run heavy
   OpenFOAM work on a login node.
3. Add or verify cut planes that separately bracket heater interiors, not only
   the whole lower-leg span.
4. Add or verify cut planes that separately bracket cooler and reducer
   interiors, not only the whole upper-leg cooling branch.
5. Add junction control-volume bracketing planes so junction rows can move from
   wall-flux-only diagnostics toward enthalpy-residual rows.
6. Improve fidelity at high-recirculation interfaces:
   - preserve reverse-flow/backflow fractions;
   - keep mixing-cup and forward-flow bulk temperatures separate;
   - do not promote recirculation-cell rows to fit targets without a
     defensible multi-stream control-volume method.
7. Preserve the heat-ledger radiation rule:
   - radiation remains absent unless OpenFOAM output exposes a `qr` term;
   - emissivity metadata alone must not be converted into a radiation heat term;
   - if `qr` appears, record source path, sign convention, and whether it is
     already included in `wallHeatFlux` to avoid double counting.
8. Document the sampling dictionaries, exact commands, Slurm job IDs, source
   paths, generated plane files, and any failed or missing samples.
9. After the sampling package is generated, claim
   `TODO-OBSERVATION-TABLE-THERMAL-REFRESH`.
10. Refresh the canonical observation table to consume
    `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/` and
    any improved sampling package, carrying physical-interface provenance,
    bracketing status, residual status, recirculation flags, and no-`qr`
    semantics.

## Observed Facts

- `TODO-HEAT-ENTHALPY-INTERFACE-LEDGER` generated
  `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/**`.
- That package has `24` patchwise rows, `15` segment residual rows, `60`
  interface samples, and `0` validation errors.
- The July 8 foundation heat ledger hash was unchanged by the follow-up package.
- Existing planes still do not separately bracket heater interiors,
  cooler/reducer interiors, or junction control volumes.
- High-recirculation interface rows remain diagnostic-only.
- Radiation remains absent as a heat-ledger term because no OpenFOAM `qr` output
  term is exposed in the current evidence.

## Inferred Interpretation

The next blocking work is not another ledger reshape; it is targeted OpenFOAM
sampling to create the missing physical control-volume boundaries. Once those
samples exist, the observation table should be refreshed so model-form bakeoff
and future 1D surrogate scoring use the same thermal validation contract as the
pressure and mdot rows.

## Blockers

- No dedicated sampling planes currently isolate heater interior heat gain.
- No dedicated sampling planes currently isolate cooler/reducer heat removal.
- Junction rows are not bracketed by inlet/outlet flow interfaces.
- Recirculation-contaminated interfaces need higher-fidelity treatment before
  any fit eligibility can be claimed.
- Mesh/GCI remains unresolved and still gates publication-strength claims.

## Exact Files Used

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_TODO-HEAT-ENTHALPY-INTERFACE-LEDGER.md`
- `.agent/journal/2026-07-08/heat-enthalpy-interface-ledger.md`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/README.md`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/summary.json`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/patchwise_heat_ledger_enthalpy_interfaces.csv`

## Recommended Next Action

Start with `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING` tomorrow. After the
sampling run is documented and validated, run
`TODO-OBSERVATION-TABLE-THERMAL-REFRESH` so
`closure_observations.csv` consumes the new thermal validation package before
any refreshed model-form bakeoff.
