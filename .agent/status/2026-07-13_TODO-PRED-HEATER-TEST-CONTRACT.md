# TODO-PRED-HEATER-TEST-CONTRACT Status

Date: 2026-07-13
Role: Implementer / Writer
Owner: codex
Status: complete, awaiting review

## Objective

Implement and document a low-dimensional heater/test-section source contract
that compares current 37 W test-section source, heater-only, heater efficiency,
and test-section source/external-loss interpretations while keeping heater,
test-section, cooler, and passive external residuals separate.

## Delivered

- Added `tools/analyze/build_heater_test_section_contract.py`.
- Added focused tests in `tools/analyze/test_heater_test_section_contract.py`.
- Built `work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/`.
- Wrote provenance manifest `imports/2026-07-13_heater_test_section_contract.json`.
- Wrote journal entry `.agent/journal/2026-07-13/heater-test-section-contract.md`.

## Key Findings

- Current 37 W test-section source (`C0`) mean abs CFD Tmean error: `34.374 K`.
- Heater-only predictive setup (`C1`) mean abs CFD Tmean error: `4.609 K`.
- Linearized F0/F1 contrast requires negative added heat relative to heater-only
  on all three rows: mean `-5.849 W`, range `-9.165..-2.736 W`.
- Direct positive test-section fluid fraction is rejected for current rows
  because the fitted fraction is negative.
- Candidate calibrated forms are either global `eta_heater` or global
  `test_section_external_loss`, but both require a train/heldout split before
  runtime use.
- Diagnostic realized CFD wallHeatFlux suggests heater transfer efficiency near
  `0.918` and test-section external loss near `11.0 W`, but this remains
  diagnostic-only evidence and is not a forward runtime input.

## Validation

```text
python3.11 -m unittest tools.analyze.test_heater_test_section_contract
python3.11 tools/analyze/build_heater_test_section_contract.py
```

Both commands completed successfully on the login node; no native CFD outputs
were mutated and no long-running solver job was launched.

## Recommendation

Use `C1_heater_only_predictive_setup` as the next admissible unfitted
imposed-cooler source contract:

```text
eta_heater = 1
test_section_fluid_fraction = 0
test_section_external_loss_W = 0
```

Thermal closure claims remain provisional pending validation split, HX fit,
hydraulic gate, wall-layer mapping, and thermal mesh uncertainty work.
