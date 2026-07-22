---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/setup_known_source_contract.csv
tags: [status, fluid, setup-known-source, heater-source]
related:
  - .agent/journal/2026-07-21/fluid-setup-known-source-sink-runtime-contract.md
  - imports/2026-07-21_fluid_setup_known_source_sink_runtime_contract.json
task: TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21

## Objective

Publish a setup-known lower-leg heater source/sink runtime contract using
existing Fluid source-distribution capability and recovered setup Q provenance.

## Outcome

Complete. The package records that Fluid already exposes
`heater_source_mode=tw4_to_tp3_three_span` and that Salt2 lower-leg setup
heater power can be represented as three predeclared train-only span rows:
`119.565 W`, `92.995 W`, and `53.14 W`.

Runtime-admitted source rows remain `0`; source/property release remains `0`.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-FLUID-SETUP-KNOWN-SOURCE-SINK-RUNTIME-CONTRACT-2026-07-21.md`
- `.agent/journal/2026-07-21/fluid-setup-known-source-sink-runtime-contract.md`
- `imports/2026-07-21_fluid_setup_known_source_sink_runtime_contract.json`
- `tools/analyze/build_fluid_setup_known_source_sink_runtime_contract.py`
- `tools/analyze/test_fluid_setup_known_source_sink_runtime_contract.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/**`

## Validation

- `python3.11 -m py_compile tools/analyze/build_fluid_setup_known_source_sink_runtime_contract.py tools/analyze/test_fluid_setup_known_source_sink_runtime_contract.py` passed.
- `python3.11 tools/analyze/build_fluid_setup_known_source_sink_runtime_contract.py` passed.
- `python3.11 -m unittest tools.analyze.test_fluid_setup_known_source_sink_runtime_contract` passed: `Ran 2 tests`.

## Unresolved Blockers

Train-only residual effect testing, source/property release, candidate freeze,
and validation/holdout/external scoring remain blocked.

## Guardrails

No external Fluid edit, native-output mutation, registry/admission mutation,
scheduler action, solver/postprocessing/sampler/harvest launch,
validation/holdout/external-test scoring, fit/model selection, source/property
release, freeze/admission, blocker-register change, generated-index refresh,
or thesis edit.
