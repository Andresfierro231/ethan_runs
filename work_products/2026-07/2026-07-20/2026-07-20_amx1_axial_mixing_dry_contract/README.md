# AGENT-565 AMX1 Axial-Mixing Dry Contract

Date: 2026-07-20

Decision: `fluid_patch_required_before_smoke`.

This package implements the planned analysis for unlocking
`predictive-wall-test-section-submodels` by narrowing the next model form to
AMX1: conservative axial thermal exchange across the upcomer/test-section
bridge, optionally followed by the already-existing UMX1 reservoir exchange.
It does not run Fluid, does not edit Fluid, and does not create a score grid.

## Result

The current Fluid API can execute UMX1 exchange and TSWFC2 distributed
wall/fluid nodes, but it cannot represent AMX1 yet. The missing pieces are:

- `axial_mixing_mode`
- `axial_mixing_multiplier`
- `axial_mixing_parent_segments`
- conservative adjacent-pair axial exchange implementation
- segment ledgers proving nonzero action and near-zero energy residual
- config-loader round trip and focused contract tests

Therefore the next useful step is not another scorecard. It is a separate
external Fluid row that adds the disabled-by-default AMX1 API and ledgers, then
runs a Salt2 smoke only.

## Candidate Order

1. `AMX1a_axial_mixing_segment_diffusion_v1`: conservative adjacent-pair
   axial thermal exchange across `left_lower_vertical`, `test_section`, and
   `left_upper_vertical`.
2. `AMX1b_axial_mixing_plus_umx_exchange_v1`: AMX1a plus existing UMX1
   reservoir exchange, only after AMX1a smoke passes.
3. `AMX1c_junction_reset_plus_axial_mixing_v1`: deferred until AMX1a/AMX1b
   evidence justifies more complexity.
4. `TSWFC3_wall_axial_conduction_v1`: deferred wall-conduction extension,
   not a retread of failed four-node TSWFC2.

## Required Next Fluid Row

Claim the external Fluid board first. Then implement exactly the patch contract
in `fluid_patch_contract.csv`: disabled defaults, validator checks, conservative
pairwise exchange, ledgers, config-loader support, README docs, and focused
tests. Defaults must be a strict no-op.

After the patch, run only:

- `salt2_jin_nominal`
- disabled baseline
- one low bounded `AMX1a` multiplier

Required smoke gates: finite accepted roots, nonzero axial-mixing ledger,
near-zero axial-mixing residual, runtime-input lint pass, and split-policy lint
pass.

## Guardrails

No Salt1-4 nominal scorecard, no external/holdout scoring, no fit/model
selection, and no blocker-register change should happen until the AMX1 smoke
passes. TSWFC2 and UMX1 exchange-only paths are already documented as not
scorecard-ready, so repeating those without new physics does not unlock the
blocker.
