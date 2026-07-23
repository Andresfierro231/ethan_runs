---
provenance:
  task_id: TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22
  generated_on: 2026-07-22
task: TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22
tags: [thermal, passive-h2, fluid-runtime, radiation, no-score]
related:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation/README.md
---

# PASSIVE-H2 Outer-Insulation Radiation Runtime Implementation

## What Was Attempted

I claimed the local PASSIVE-H2 runtime implementation row and audited the
external Fluid board before editing. The external board had stale/older active
Fluid rows that still own shared campaign config files. To avoid conflicting
ownership, I claimed a separate external row limited to solver source, a
task-owned smoke runner, tests, docs, status/journal, and one diagnostics output
package.

I then inspected the Fluid role-local external-boundary path. The relevant
function applied only convection from role rows even though the external
boundary dictionary and role rows already carried setup radiation fields. This
matched the prior observation that `radiation_on` produced zero output delta.

## What Worked

Adding role-row radiation in the runtime path worked. The solver now evaluates
the radiation term when:

- `scenario.radiation_on` is true;
- the role row supplies `area_m2`, `emissivity`, and `Tsur_K`;
- the drive selector resolves to model state, with PASSIVE-H2 using
  `outer_surface_temperature`.

The targeted Fluid tests pass, and the Salt2 train-only smoke accepted roots for
all three states. The H2 radiation-on minus radiation-off ambient heat delta is
`14.629985767350746 W`, compared with the corrected outer-insulation radiation
target of `22.405251648168736 W`.

## What Did Not Work Or Remains Incomplete

This did not make H2 admissible. It only made the runtime implementation
scientifically usable for the next pre-admission studies.

The run was train-only Salt2. Salt3 and Salt4 remain blocked by split conflicts
and were not used for protected scoring. No source/property release or Qwall
release occurred. No model-form coefficient was admitted, frozen, or scored.

The external config ownership is still unresolved: shared Fluid
`configs/scenarios.yaml` and `configs/campaigns.yaml` are claimed by an older
active external row, so this work deliberately avoided campaign-preset edits.

## Analysis

The previous zero radiation delta was an implementation omission, not a
physical finding that H2 radiation is irrelevant. The corrected runtime result
is nonzero and order-consistent with the source-backed outer-insulation target.
The runtime delta is smaller than the diagnostic target because the Fluid solve
responds to the added heat-loss lane: temperatures, qhx, and mdot move
together, rather than holding the prior diagnostic wall state fixed.

This makes H2 worth pursuing as a possible predictive model-form component, but
only through a disciplined admission path. It cannot be used as thesis final
score evidence yet.

## Next Useful Actions

1. Resolve the external Fluid config ownership row or claim a separate config
   handoff before registering a shared campaign preset.
2. Run an H2 source-mapping preflight: verify each source family to Fluid
   parent/subspan mapping is source-backed enough for admission.
3. Resolve Salt3/Salt4 split conflicts or explicitly keep them out of the
   train/support admission path.
4. Run same-QOI setup-only UQ after source mapping and split gates pass.
5. Only after a frozen candidate exists should protected scoring/admission rows
   open.
