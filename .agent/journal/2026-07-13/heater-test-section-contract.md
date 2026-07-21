# Heater/Test-Section Contract

Date: 2026-07-13
Task: `TODO-PRED-HEATER-TEST-CONTRACT`
Role: Implementer / Writer

## Why This Avenue Exists

The forward-v0 imposed-cooler package found that the current Fluid source
contract, which includes heater power plus a configured 37 W test-section
source, overpredicts CFD mean temperature much more than a heater-only variant.
This points to the heater/test-section source contract as a first-order issue
before fitting passive external heat loss or claiming thermal closure.

## Files To Open First

- `work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/candidate_parameters.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_contract_interpretation.csv`
- `tools/analyze/build_heater_test_section_contract.py`

## Trusted Inputs

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/forward_v0_results.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/forward_v0_variant_summary.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/README.md`

## Observed Output

The generated contract package compares six candidates:

- `C0_current_37W_test_source`: full heater plus full 37 W test-section source.
- `C1_heater_only_predictive_setup`: heater setup power only.
- `C2_calibrated_eta_heater_equivalent`: one fitted heater efficiency.
- `C3_calibrated_test_section_external_loss`: one fitted test-section loss.
- `C4_test_section_fluid_fraction_fit`: direct fitted test-section source fraction.
- `C5_realized_wallHeatFlux_partition_diagnostic`: diagnostic CFD partition only.

Forward-v0 fast-scan evidence gives `34.374 K` mean abs CFD Tmean error for the
current 37 W source and `4.609 K` for heater-only. The F0/F1 contrast implies
that all three current rows need negative added heat relative to heater-only:
Salt 2 `-2.736 W`, Salt 3 `-5.647 W`, and Salt 4 `-9.165 W`.

Diagnostic fixed-mdot CFD wallHeatFlux evidence reports realized heater
efficiency near `0.918` and test-section external loss near `11.0 W` mean, but
that evidence is explicitly not a forward runtime input.

## Inferred Interpretation

The current 37 W test-section source is not a safe default for the next
predictive run. A direct positive test-section fluid fraction has the wrong
sign on current rows. The next admissible unfitted model is heater-only:

```text
Q_to_fluid = eta_heater * P_heater_setup
           + test_section_fluid_fraction * P_test_section_setup
           - test_section_external_loss
           - Q_cooler
           - Q_passive_external
```

with `eta_heater = 1`, `test_section_fluid_fraction = 0`, and
`test_section_external_loss_W = 0` until a validation split admits calibration.

## Contradictions And Boundaries

The diagnostic CFD wallHeatFlux partition points toward less than full heater
transfer and a lossy test section, but realized wallHeatFlux must not be
consumed by forward runtime. It is sign and magnitude evidence only.

The calibrated `eta_heater` and `test_section_external_loss` interpretations
fit the current rows by construction. They are not held-out scores and cannot
be used for validation claims until `TODO-PRED-VALIDATION-SPLIT` defines
training and held-out rows.

Cooler duty and passive external residuals remain separate ledgers. This work
does not tune passive external hA to absorb a heater/test-section source error.

## Next Task Sequence

1. Use `C1_heater_only_predictive_setup` for the next unfitted forward-v0 source
   contract.
2. Run `TODO-PRED-VALIDATION-SPLIT` before any calibrated heater/test-section
   parameter is used for scoring.
3. After the split, test one global `eta_heater` or one global
   `test_section_external_loss`, not both on the same small training set.
4. Keep the HX fit, hydraulic gate, wall-layer drive mapping, and thermal mesh
   gate separate from this source-contract calibration.

## Output Contract

The package output is CSV/JSON/Markdown only. It does not launch Fluid, does
not stage native solver outputs, and does not mutate native CFD solver outputs.

## Do-Not-Do Guardrails

- Do not use realized CFD `wallHeatFlux` as a forward runtime input.
- Do not combine heater efficiency, test-section loss, cooler duty, and passive
  external hA into one scalar correction.
- Do not claim thermal closure from the current three-row fast-scan contrast.
- Do not fit both `eta_heater` and `test_section_external_loss` without enough
  independent training rows.
