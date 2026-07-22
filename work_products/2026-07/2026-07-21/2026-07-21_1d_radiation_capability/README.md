---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_split_junction_storage_radiation_extraction/README.md
tags: [thermal-modeling, radiation, heat-loss, one-d, no-admission]
related:
  - .agent/status/2026-07-21_TODO-1D-RADIATION-CAPABILITY.md
  - .agent/journal/2026-07-21/1d-radiation-capability.md
task: TODO-1D-RADIATION-CAPABILITY
date: 2026-07-21
role: Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# 1D Radiation Capability

## Decision

This package releases a repo-local 1D radiation capability and sensitivity
ledger. It computes radiative exchange from setup emissivity, surroundings
temperature, area, and declared surface-temperature offsets. It does not edit
Fluid/API code, consume solver output as a predictive input, fit a coefficient,
or admit a closure.

## Results

- Analytic tests: `5` rows, `0` failures.
- Predictive setup boundary rows: `15`.
- Radiation sensitivity rows: `75`.
- Case/scenario energy ledger rows: `15`.
- Fit/admission rows released: `0`.

## Outputs

- `radiation_analytic_tests.csv`
- `radiation_sensitivity_scenarios.csv`
- `radiation_energy_ledger.csv`
- `runtime_double_counting_audit.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Current 3D CFD includes radiative exchange through `rcExternalTemperature`, but
the cited sources expose no separate exported `qr` heat-loss term. Predictive 1D
may compute radiation from setup fields and solved states. Replay/diagnostic
use of total CFD heat disables a separate radiation term to prevent double
counting. No native CFD/OpenFOAM output, registry/admission state, scheduler
state, Fluid source, external repository, blocker register, generated index,
fit, tuning, model-selection, or admission state was changed.
