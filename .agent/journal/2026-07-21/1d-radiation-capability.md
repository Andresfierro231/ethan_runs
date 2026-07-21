---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_1d_radiation_capability/README.md
tags: [journal, thermal-modeling, radiation, one-d]
related:
  - .agent/status/2026-07-21_TODO-1D-RADIATION-CAPABILITY.md
  - imports/2026-07-21_1d_radiation_capability.json
task: TODO-1D-RADIATION-CAPABILITY
date: 2026-07-21
role: Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# 1D Radiation Capability

## Attempted

Built a reproducible 1D radiation capability package from the Fluid
external-boundary dictionary, Phase 1 radiation contract, LitRev split
junction/storage/radiation extraction, and radiative-boundary guidance.

## Observed

The Fluid external-boundary dictionary provides `15` predictive rows with setup
radiation fields. Expanding five declared surface-temperature scenarios
produces `75` sensitivity rows and `15` case/scenario energy-ledger rows.
Analytic tests cover zero emissivity, zero temperature difference, positive
loss, negative gain, and the linearized radiation coefficient.

## Inferred

Radiation can now be represented as a separate predictive 1D loss lane from
setup evidence. This does not mean current CFD outputs provide a separable `qr`
target; radiation remains embedded in total heat evidence and cannot be added
again in replay mode.

## Contradictions Or Caveats

The package uses declared sensitivity offsets from setup `Tsur`, not validation
temperatures or a solved wall-state model. It therefore quantifies capability
and scale, not final predictive accuracy.

## Next Useful Actions

1. Use this package as the radiation lane input for a future runtime-legal
   frozen candidate.
2. Keep external Fluid/API implementation under a separate claimed row.
3. Keep `qr` absence and storage/contact blockers separated from internal `Nu`.

## Guardrails

No native-output, registry/admission, scheduler, solver/postprocessing,
staged-copy, Fluid, external repo, fitting/tuning/model-selection,
blocker-register, or generated-index state was changed.
