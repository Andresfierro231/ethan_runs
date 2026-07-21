---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv
tags: [thermal-parity, external-boundary, heat-loss, radiation, forward-model]
related:
  - .agent/status/2026-07-14_AGENT-365.md
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/README.md
task: AGENT-365
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# External-BC Thermal-Profile Parity Study

## Why This Exists

The user asked for a thesis-ready study comparing where the 3D model releases
heat and where the 1D model releases heat, starting from Ethan's boundary and
source assumptions. Prior packages started the comparison, but the method needed
one findable package that ties together the external-boundary contract,
radiation policy, leg-level discrepancy, and thermal-profile drive diagnosis.

## Observed Facts

- CFD `rcExternalTemperature` includes emissivity/Tsur effects; radiation is
  inseparable from total exported `wallHeatFlux`.
- Fluid now has external-boundary table support documented by AGENT-318, but
  AGENT-365 did not rerun Fluid or edit external source.
- The best executable predictive-style baseline is still `F1_heater_only`,
  which uses imposed cooler duty and is therefore not final predictive-HX
  validation.
- Existing wall-layer drive rows show wall/shell proxies are cooler than bulk in
  Salt2/Salt3 upcomer and downcomer rows, consistent with bulk-drive over-loss
  being plausible there.

## Inferred Interpretation

The next 1D refinement should not tune one global heat-loss coefficient. It
should separately address:

- junction/stub/horizontal connector heat-loss area or segments;
- heater realization versus lower-leg passive wall loss;
- active HX/cooler duty versus passive cooling-branch wall loss;
- external-boundary h/Ta/Tsur/emissivity/layer contract;
- wall-adjacent or mixed thermal drive, trained on Salt2 and validated on
  Salt3/Salt4 without refit.

## Files Changed

- Added `tools/analyze/build_external_bc_thermal_profile_parity_study.py`.
- Added `tools/analyze/test_external_bc_thermal_profile_parity_study.py`.
- Added `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/**`.
- Added this journal and the AGENT-365 status/import closeout.
- Added links to the thermal-boundary map, forward-predictive map, and thesis
  dossier.

## Next Action

Run a new setup-only Fluid scenario that consumes the external-boundary table
and compares bulk-drive versus wall-adjacent/mixing-factor drive. Keep Salt2 as
training, Salt3 as validation, and Salt4 as holdout. Do not promote the run to
predictive-HX evidence until cooler removal is modeled from setup inputs instead
of imposed duty.
