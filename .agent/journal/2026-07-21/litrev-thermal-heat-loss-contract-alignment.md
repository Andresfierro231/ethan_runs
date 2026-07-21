---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
tags: [journal, litrev-synthesis, thermal-modeling, heat-loss, internal-nu]
related:
  - .agent/status/2026-07-21_TODO-LITREV-THERMAL-HEAT-LOSS-CONTRACT-ALIGNMENT.md
  - imports/2026-07-21_litrev_thermal_heat_loss_contract_alignment.json
task: TODO-LITREV-THERMAL-HEAT-LOSS-CONTRACT-ALIGNMENT
date: 2026-07-21
role: Thermal-modeling/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# LitRev Thermal Heat-Loss Contract Alignment

## Attempted

Read the thermal maps, `TODO-FLUID-EXTERNAL-BC-DICT` board row, the current
`fluid+walls` thesis section, LitRev CFD rows `CFD-13` to `CFD-15`, and MF-01 /
MF-04 model-form rows. Cross-checked the July 13 heat-loss calibration, July 16
thermal parity gate, predictive boundary admission package, test-section
passive-loss package, segment thermal scorecard, wall-circuit study, and
patchwise heat ledgers.

## Observed

The current repo evidence already separates residual owners. Heater and
cooler/HX have setup-only predictive boundary lanes. Test-section passive loss
is not admitted. Radiation is active in CFD `rcExternalTemperature` metadata and
embedded in total `wallHeatFlux`, but no separate `qr` output exists. Internal
`Nu` has zero fit-admissible rows and is repeatedly guarded from absorbing
external, source, storage, recirculation, or residual terms.

## Inferred

The LitRev heat-transfer contract is compatible with the current
`fluid+walls` model if the contract is phrased as a multi-lane heat-path
ledger, not as one effective thermal coefficient. `CFD-13` and `CFD-14` define
the bulk/wall quantities needed to diagnose internal heat transfer. `CFD-15`
controls the decisive separation: heat-loss-network terms and residual owners
must stay named.

## Caveats

This is not a new calibration or admission package. It does not prove any wall,
quartz, radiation, or internal-Nu coefficient. It only fixes the model contract
and identifies the current blocker for each heat path.

## Next Useful Actions

- Implement `TODO-FLUID-EXTERNAL-BC-DICT` so predictive runs can consume setup
  external boundary dictionaries without realized `wallHeatFlux`.
- Implement or verify `TODO-1D-RADIATION-CAPABILITY` with no double counting in
  replay mode.
- Reopen test-section passive loss only with setup-only candidates that pass
  validation and holdout gates.
- Keep internal `Nu` diagnostic until row-level sign/heat-balance,
  recirculation, and same-QOI mesh/GCI gates pass.
