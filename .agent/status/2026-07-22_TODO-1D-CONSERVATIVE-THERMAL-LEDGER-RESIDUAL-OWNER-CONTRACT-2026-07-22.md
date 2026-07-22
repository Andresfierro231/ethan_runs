---
provenance:
  - tools/analyze/build_1d_conservative_thermal_ledger_residual_owner_contract.py
  - tools/analyze/test_1d_conservative_thermal_ledger_residual_owner_contract.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/summary.json
task: TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Writer / Reviewer / Tester
type: status
status: complete
tags: [status, predictive-1d, thermal-ledger, residual-owner, runtime-leakage]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract
  - .agent/journal/2026-07-22/1d-conservative-thermal-ledger-residual-owner-contract.md
  - imports/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract.json
---
# TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22

## Objective

Produce a model-facing 1D heat ledger contract that separates heater input,
cooler/HX removal, passive wall exchange, test-section/quartz paths, wall/layer
resistance, radiation, storage, recirculation/exchange, internal `Nu`, and final
residual ownership before any fitting or final scoring.

## Outcome

Decision: `contract_ready_no_candidate_release_no_runtime_leakage`.

The package was published at
`work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/`.
It contains `12` conservative ledger rows, `10` runtime allowed-input rows, `8`
runtime-forbidden audit rows, `7` missing setup-field rows, `5` next-task
handoffs, and `8` residual-owner families.

The key equation is:

`R_s = sum(Q_known_s) - mdot_model * cp * (T_out_s - T_in_s)`.

`R_s` is a reported residual and owner label. It is not a heat closure, tuning
term, or source/property release.

## What Worked

- Existing heat-loss, source/sink, S12, N3, and patchwise ledger packages were
  sufficient to define the conservative accounting contract without new compute.
- The runtime leakage policy is now machine-readable: all forbidden inputs are
  explicitly marked `runtime_allowed=false`.
- The ledger cleanly separates diagnostic CFD evidence from predictive runtime
  inputs, preserving realized `wallHeatFlux` and CFD enthalpy fields as audit
  evidence only.

## What Did Not Work

- No heat-path candidate was released. Heater/source, passive wall, test-section,
  and S13 exchange rows still lack the required source/property or same-QOI UQ
  evidence.
- Storage could not be promoted to a model term because no same-time solid-energy
  or transient audit is admitted for this steady 1D contract.
- Internal `Nu` remains baseline/literature/diagnostic only; current evidence
  still has `0` fit-admissible internal-`Nu` rows.

## Analysis

The scientifically useful move is to make the residual impossible to misuse.
The ledger allows a residual to be measured and assigned an owner family, but it
does not let the residual become an unobserved source term or a hidden global
multiplier. This matters because the strongest current thermal signals are
diagnostic: broad passive hA movement, partial test-section response, and
recirculating upcomer exchange evidence. Those signals can guide the next
source-bounded studies, but they do not yet justify coefficient admission.

The contract also keeps the pressure/thermal split clean for the 1D model:
`mdot_model` is a model output coupled back into enthalpy transport, while CFD
`mdot` remains post-solve comparison evidence only.

## Changes Made

- `tools/analyze/build_1d_conservative_thermal_ledger_residual_owner_contract.py`
- `tools/analyze/test_1d_conservative_thermal_ledger_residual_owner_contract.py`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/`
- `.agent/status/2026-07-22_TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22.md`
- `.agent/journal/2026-07-22/1d-conservative-thermal-ledger-residual-owner-contract.md`
- `imports/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract.json`
- `.agent/BOARD.md` own row only

## Validation

- `python3.11 -m py_compile tools/analyze/build_1d_conservative_thermal_ledger_residual_owner_contract.py tools/analyze/test_1d_conservative_thermal_ledger_residual_owner_contract.py`: passed.
- `python3.11 tools/analyze/test_1d_conservative_thermal_ledger_residual_owner_contract.py`: passed.
- `python3.11 tools/analyze/build_1d_conservative_thermal_ledger_residual_owner_contract.py`: passed.

## Guardrails

- Native CFD/OpenFOAM output mutation: false.
- Scheduler, solver, sampler launch: false.
- Fluid/external repository mutation: false.
- Registry/admission/blocker-register mutation: false.
- Source/property release, fitting, model selection, final scoring: false.
- Runtime use of realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler
  duty, realized test-section heat, validation temperatures, holdout
  temperatures, hidden global multiplier, or final residual closure: false.

## Next Useful Actions

Run `TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22` next. Then
run `TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22` before any final
scorecard or source/property release attempt.
