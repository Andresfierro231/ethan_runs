# Heater/Test-Section Source Contract

Generated: `2026-07-13T21:43:44+00:00`

Task: `TODO-PRED-HEATER-TEST-CONTRACT`

## Purpose

This package turns the forward-v0 imposed-cooler finding into a small source
contract for the TAMU loop. It compares:

- current 37 W test-section source,
- heater-only setup source,
- heater transfer-efficiency calibration,
- test-section source/external-loss calibration,
- diagnostic realized CFD wallHeatFlux partitioning.

The contract equation is:

```text
Q_to_fluid = eta_heater * P_heater_setup
           + test_section_fluid_fraction * P_test_section_setup
           - test_section_external_loss
           - Q_cooler
           - Q_passive_external
```

`Q_cooler` and `Q_passive_external` stay separate. Realized CFD
`wallHeatFlux` is used only as diagnostic evidence and is not a forward runtime
input.

## Key Result

- `C0_current_37W_test_source`: mean abs CFD Tmean error `34.3736183211 K`.
- `C1_heater_only_predictive_setup`: mean abs CFD Tmean error `4.60896609261 K`.
- Linearized fitted rows require `mean -5.849; range -9.165..-2.736 W` relative to
  heater-only, i.e. negative added test-section heat on all current rows.

## Recommendation

Use `C1_heater_only_predictive_setup` as the next admissible unfitted model:
`eta_heater = 1`, `test_section_fluid_fraction = 0`, and
`test_section_external_loss_W = 0` until a validation split admits a calibrated
correction.

After `TODO-PRED-VALIDATION-SPLIT`, test either one global `eta_heater` or one
global `test_section_external_loss`, not both on the same small training set.
Do not use realized CFD `wallHeatFlux` as a runtime input, and do not hide this
source-contract issue inside passive external hA.

## Files

- `case_heat_ledger.csv`: heater, test-section, cooler, and passive external
  realized heat ledgers from the fixed-mdot diagnostic package.
- `case_contract_interpretation.csv`: per-case linearized source-contract
  interpretation from the F0/F1 forward-v0 contrast.
- `candidate_parameters.csv`: fit/validation-safe candidate parameter table.
- `recommended_model.csv`: next model and calibration-gate recommendation.
- `summary.json`: machine-readable summary.

## Evidence Boundary

Thermal closure claims remain provisional. The package uses existing
forward-v0 fast-scan outputs and diagnostic section heat balance outputs; it
does not rerun Fluid and does not stage or mutate native CFD solver outputs.
