# AGENT-565 Journal: AMX1 Axial-Mixing Dry Contract

Task: AGENT-565

Date: 2026-07-20

## Starting Context

The active blocker is `predictive-wall-test-section-submodels`: no setup-only
wall/test-section/passive-boundary candidate has passed coupled mdot, TP, TW,
all-probe, runtime, split, and source/property gates. Recent evidence narrowed
the viable next move:

- TSWFC2 four-node wall/fluid smoke ran, but the bounded nominal scorecard was
  not admitted.
- UMX1 exchange roots now pass smoke, but exchange-only score behavior is not
  scorecard-ready.
- Upcomer onset evidence remains sparse, with PM10/high-heat anchor evidence
  still needed before broad expansion.

## Work Performed

Claimed AGENT-565 and kept scope limited to repo-local documentation and
handoff artifacts. Inspected the external Fluid API read-only. The current
`ScenarioConfig` exposes `upcomer_mixing_mode`,
`upcomer_exchange_multiplier`, `upcomer_exchange_parent_segments`,
`upcomer_reservoir_heat_sources`, and TSWFC2 wall/fluid fields. It does not
expose `axial_mixing_mode`, `axial_mixing_multiplier`, or
`axial_mixing_parent_segments`, and validation accepts only the existing UMX1
exchange mode for upcomer mixing.

Created the package:

- `source_manifest.csv`
- `amx1_candidate_ladder.csv`
- `amx1_dry_contract.csv`
- `fluid_capability_audit.csv`
- `fluid_patch_contract.csv`
- `runtime_input_audit.csv`
- `source_property_release_plan.csv`
- `scenario_contract_stub.yaml`
- `smoke_readiness_decision.json`
- `summary.json`
- `README.md`

Updated the forward predictive map with the AMX1 decision and next sequence.

## Decision

AMX1 is the right next model family to try, but it cannot be smoked in the
current Fluid API. The next row must be an external Fluid implementer row that
adds disabled-by-default axial mixing fields, conservative adjacent-pair
exchange, ledgers, config round trip, docs, and focused tests.

After that patch, run Salt2 smoke only: disabled baseline plus one low bounded
AMX1a multiplier. Do not run a Salt1-4 scorecard, broad grid, external/holdout
score, fit/model selection, or blocker-register update before the smoke passes.

## Process Notes

The package intentionally records blocked statuses instead of positive
admission/fit statuses. This prevents source/property tooling from interpreting
the handoff as an admitted candidate. The runtime audit lists forbidden values
only in explicitly forbidden contexts.
