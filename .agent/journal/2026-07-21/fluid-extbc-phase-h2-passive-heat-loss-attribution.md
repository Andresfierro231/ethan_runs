---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/tw5_response_waterfall.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/source_sink_coupling_matrix.csv
tags: [journal, forward-model, phase-h2, heat-loss-attribution]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21.md
  - imports/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/README.md
task: TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Phase H2 Passive Heat-Loss Attribution

## Attempted

Built a reproducible post-processing package that consumes existing Phase E,
Phase H, source/sink provenance, and heated-incline audit evidence. No Fluid
solve was launched. The package implements the requested H2 audit plus three
follow-on studies as CSV outputs.

## Observed

The passive role ledger has `12` rows. All pass the h/area/hA recomputation
screen and all reviewed heat-ledger rows have sign-consistent ambient loss.

The TW5 response remains the dominant scientific signal:

- Phase E baseline TW5 absolute residual: `109.09380824932663 K`.
- Lower-leg hA half TW5 absolute residual: `104.50070134125099 K`.
- Global passive hA half TW5 absolute residual: `57.46011442285385 K`.

By direct Phase H evidence, lower-leg hA half explains only
`4.59310690807564 K` of the `51.63369382647278 K` global hA-half TW5
improvement. The H2 attribution package allocates the non-lower-leg remainder
by hA share only as a diagnostic heuristic, with the largest estimated family
shares in `junction`, `downcomer`, `upcomer`, and `cooling_branch`.

## Inferred

The thermal residual is passive-network responsive but not primarily
lower-leg-passive localized. The immediate uncertainty is not arithmetic
consistency. It is physical source basis: all passive role rows carry
wallHeatFlux provenance paths, and the train-optimal global `0.5x` hA response
cannot be admitted as a physical repair.

Setup-known source/sink coupling remains important. For Salt2, the recovered
lower-leg heater setup magnitude is `265.7 W`, compared with a Phase E passive
plus HX loss reference of `302.6917569849107 W`, but runtime use remains
blocked by the separate source/sink contract and source/property release gates.

## Contradictions Or Caveats

The row-family attribution outside lower-leg is not a one-at-a-time computed
sensitivity. It is an allocated remainder estimate based on hA share. Treat it
as a prioritization aid for follow-up audits, not as evidence that any one
family alone causes the residual.

The source/sink matrix reads validation and holdout metadata rows from the
provenance package, but does not score those rows or join protected residuals.

## Next Useful Actions

1. Finish or consume the active setup-known source/sink runtime contract and
   lower-leg heater residual decomposition rows before deciding whether source
   terms explain part of the thermal residual.
2. Build an independent passive hA/source-family basis from setup geometry,
   ambient conditions, insulation/state assumptions, and literature or
   engineering correlations.
3. Only after that basis exists, execute a single predeclared train-only
   candidate: `PASSIVE-H2-CAND001 passive_hA_source_basis_rebuild_v1`.
4. Keep validation, holdout, and external-test scoring blocked until a frozen
   candidate exists.
