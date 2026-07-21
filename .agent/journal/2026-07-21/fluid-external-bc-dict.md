---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/external_bc_dictionary_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/external_bc_segment_role_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/README.md
tags: [journal, thermal-modeling, external-boundary, fluid]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-DICT.md
  - imports/2026-07-21_fluid_external_bc_dict.json
task: TODO-FLUID-EXTERNAL-BC-DICT
date: 2026-07-21
role: Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Fluid External BC Dictionary

## Attempted

Built the repo-local external-boundary dictionary package from the completed
Phase 1 external-BC/radiation integration evidence. The task was limited to
contract, validation, and handoff artifacts; external Fluid source was not
edited.

## Observed

Phase 1 exposes `24` segment/role rows. Of these, `15` are predictive passive
external-boundary rows and `9` are document-only source/sink rows such as
heater, cooler, and test-section roles. The released schema already contains
the necessary setup fields: `h`, `Ta`, `Tsur`, emissivity, area, coverage,
layer-resistance status, and drive-temperature selector.

## Inferred

The immediate Fluid-facing interface should be a typed runtime dictionary with
explicit mode selectors. Predictive mode can compute external convection and
radiation from setup fields and solved states; replay mode can only consume a
diagnostic total boundary heat lane and cannot add separate radiation or
convection.

## Contradictions Or Caveats

This package does not prove a final heat-loss candidate. It removes one
runtime-interface blocker, but Phase 5 remains a negative freeze because
upcomer exchange state, same-QOI uncertainty, and ordinary internal-`Nu` gates
remain closed.

## Next Useful Actions

1. Open a separate exact-file Fluid row to implement the API/source changes.
2. Create the upcomer exchange evidence extraction row for `V_recirc`,
   `mdot_exchange`, `tau_recirc`, wall-core Delta T, pressure residual, and
   energy residual.
3. Publish same-QOI UQ before any final heat-loss candidate score.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repo files, staged-copy/postprocessing jobs,
fitting/tuning/model selection, blocker register, generated docs index, or
scientific admission state were changed.
