---
provenance:
  - tools/analyze/build_1d_setup_only_bc_uq_propagation.py
  - tools/analyze/test_1d_setup_only_bc_uq_propagation.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/summary.json
task: TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22
date: 2026-07-22
role: Uncertainty / Forward-pred / Thermal-modeling / Hydraulics / Tester / Writer
type: status
status: complete
tags: [status, predictive-1d, uncertainty, setup-only, runtime-leakage]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation
  - .agent/journal/2026-07-22/1d-setup-only-bc-uq-propagation.md
  - imports/2026-07-22_1d_setup_only_bc_uq_propagation.json
---
# TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22

## Objective

Define how setup-input uncertainty should propagate through the 1D model before
any final scorecard: heater source fraction, cooler/HX strength, ambient and
radiation fields, external convection, wall/layer materials, property modes,
pressure-loss terms, and sensor projection.

## Outcome

Decision: `setup_only_uq_contract_ready_no_compute_no_publication_interval`.

The package was published at
`work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/`.
It contains `9` UQ source rows, `5` propagation-plan stages, `9` lightweight
sensitivity rows, `9` protected-row guardrails, and `6` readiness gates.

This is a UQ runbook and screening-prior contract. It is not a completed UQ
calculation and does not provide publication uncertainty intervals.

## What Worked

- The new conservative thermal ledger and completed sensor projection operator
  gave clean boundaries for setup-only UQ.
- The package converts the runtime leakage rules into protected-row guardrails:
  CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty, realized
  test-section heat, validation temperatures, holdout temperatures, and residual
  heat closure are all blocked.
- The plan separates train-only screening, low-order interaction screens,
  candidate-specific UQ after release, and protected-row propagation after
  freeze.

## What Did Not Work

- No numerical UQ was run. The row did not have authority to launch Fluid,
  solvers, samplers, or scheduler jobs.
- The proposed ranges are screening priors, not admitted final intervals. They
  still need setup-log review, material manifests, radiation capability, and a
  frozen runtime-legal candidate before publication intervals are possible.
- No source/property release or candidate admission occurred.

## Analysis

The useful scientific progress is a disciplined UQ boundary: propagate
uncertainty in setup fields first, report sensitivity structure, and only later
score validation/holdout/external rows after the runtime input set is frozen.
This prevents the current residual-owner evidence from being converted into
validation-tuned multipliers.

The most important first screens are heater source fraction, cooler/HX strength,
external hA, pressure-loss terms through `mdot_model`, and sensor projection.
Radiation and wall/layer material uncertainty are important but currently
blocked from final interval status by missing setup/capability fields.

## Changes Made

- `tools/analyze/build_1d_setup_only_bc_uq_propagation.py`
- `tools/analyze/test_1d_setup_only_bc_uq_propagation.py`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/`
- `.agent/status/2026-07-22_TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22.md`
- `.agent/journal/2026-07-22/1d-setup-only-bc-uq-propagation.md`
- `imports/2026-07-22_1d_setup_only_bc_uq_propagation.json`
- `.agent/BOARD.md` own row only

## Validation

- `python3.11 -m py_compile tools/analyze/build_1d_setup_only_bc_uq_propagation.py tools/analyze/test_1d_setup_only_bc_uq_propagation.py`: passed.
- `python3.11 tools/analyze/test_1d_setup_only_bc_uq_propagation.py`: passed.
- `python3.11 tools/analyze/build_1d_setup_only_bc_uq_propagation.py`: passed.

## Guardrails

- Native CFD/OpenFOAM output mutation: false.
- Scheduler, solver, sampler, harvest, or UQ execution launch: false.
- Fluid/external repository mutation: false.
- Registry/admission/blocker-register mutation: false.
- Source/property release, candidate admission, protected scoring, fitting, and
  model selection: false.
- Runtime use of forbidden CFD/validation/holdout fields: false.

## Next Useful Actions

Use the package as the runbook for a separately claimed train-only one-at-a-time
UQ smoke row. In parallel, the model-hierarchy/ablation ladder row can consume
the conservative ledger, sensor operator, and UQ contract as documentation
evidence.
