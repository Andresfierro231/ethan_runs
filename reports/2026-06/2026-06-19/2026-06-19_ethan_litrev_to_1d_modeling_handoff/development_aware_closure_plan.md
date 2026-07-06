# Development-Aware Closure Plan

Generated: `2026-06-19`

## Purpose

Turn the current June 19 Salt closure evidence into a concrete next-step plan
for development-aware 1D closures that do not assume long sections are fully
developed by default.

This plan narrows the first fitting pass to low-order nondimensional families
that can be tested against the current defended Salt CFD subset before any
measured-loop calibration or broader Water collapse is attempted.

## Queue refresh on 2026-06-22

No additional CFD submission is justified from this report scope on
`2026-06-22`.

Reason:

- the June 18 continuation wave is still the highest-priority CFD action for
  straight retained-time hardening and Water readiness
- the June 19 blocker package already records the first justified bracket wave
  as the submitted Salt 2 / Salt 4 heater-plus-insulation children
- the June 22 Salt 4 relaunches repaired runtime workflow defects, but they do
  not widen the scientific closure boundary
- no new Water DOE and no dedicated feature `K_eff` DOE are justified yet

Observed queue state on `2026-06-22` from `sacct`:

- running:
  - `3244950` Salt 3 Jin continuation
  - `3244951` Salt 2 Jin continuation
  - `3244954` Salt 4 Jin continuation
  - `3244957` Water 2 continuation
  - `3246561` Salt 2 high-Q / high-insulation bracket child
  - `3246564` Salt 2 low-Q / low-insulation bracket child
  - `3250524` repaired Salt 4 high-Q / high-insulation bracket child
  - `3250525` repaired Salt 4 low-Q / low-insulation bracket child
- pending:
  - `3250526` repaired packed optimum-thickness wave
- failed:
  - `3246562` initial Salt 4 high-Q / high-insulation bracket child
  - `3246563` initial Salt 4 low-Q / low-insulation bracket child
  - `3246927` initial packed optimum-thickness wave
- timed out:
  - `3244952` Water 3 continuation
  - `3244953` Water 1 continuation
  - `3244956` Water 4 continuation
- completed:
  - `3244955` Salt 1 Jin continuation

Action is therefore:

- monitor the active continuation wave
- keep the submitted Salt 2 / Salt 4 bracket wave as the bounded out-of-sample
  stress test
- watch whether the repaired packed optimum wave starts cleanly
- do not submit the deferred Salt 3 Jin midpoint bracket yet

## Modeling stance

Use normalized closure residuals rather than raw closure values as the fit
targets.

Recommended response variables:

- hydraulic:
  - `phi_f = f_D / f_D_fd`
  - where `f_D_fd = 64 / Re`
- thermal:
  - `phi_nu = Nu / Nu_ref`
  - where `Nu_ref` is one of:
    - admitted direct branch baseline for `left_lower_leg`
    - or a branchwise state-surface reference when direct `Nu` is not defended

Why this is the right first form:

- it preserves the fully developed references as asymptotes instead of
  replacing them
- it makes development effects an additive or multiplicative correction
  rather than a hidden redefinition of the baseline law
- it fits the current June 19 handoff boundary where direct closures are only
  partially admitted

## Candidate nondimensional inputs

Start with the smallest defended feature set that still represents
development, buoyancy, and branch context.

Primary inputs:

- `Re`
- `Pr`
- `Ri = Gr / Re^2`
- `Gz = Re * Pr * D_h / x_dev`
- `x_dev_over_D = x_dev / D_h`
- branch or segment class

Secondary inputs for sensitivity-only or later promotion:

- `Ra`
- local heater or cooler forcing flag
- profile-descriptor amplitudes already preserved in the current bundle
- branchwise residual-bucket class

Definitions that must stay explicit:

- `x_dev` is distance from the last hydraulic or thermal reset, not just raw
  loop arc length
- use separate reset coordinates for:
  - hydraulic development
  - thermal development
- vertical heated segments should always carry `Ri` as the preferred
  buoyancy-to-inertia flag instead of raw `Gr` alone

## First closure families to test

### Family F1: decaying hydraulic development multiplier

Use a direct correction on the fully developed Darcy baseline:

`phi_f = 1 + A_f * Re^a * Pr^b * Ri^c * g_f(x_dev_over_D)`

Recommended first decay shapes:

- rational: `g_f(x) = 1 / (1 + B_f * x^m_f)`
- exponential: `g_f(x) = exp(-B_f * x)`

Use this family first on admitted straight hydraulic rows only.

### Family T1: direct thermal correction with explicit development

For direct thermal fits on the defended branch only:

`phi_nu = 1 + A_nu * Re^d * Pr^e * Ri^g * g_nu(x_dev_over_D)`

This is the cleanest first thermal family for:

- `left_lower_leg` direct `Nu` rows

### Family T2: thermal closure conditioned on hydraulic state

For the next pass, allow hydraulic state to inform thermal closure:

`phi_nu = 1 + A_nu * Re^d * Pr^e * Ri^g * phi_f^h * g_nu(x_dev_over_D)`

This family matches the user-proposed coupling and is physically reasonable,
but it should be fit only after Family F1 is stable.

### Family LT1: shared latent development amplitude

Fit one hidden development state `z_dev` and map it separately into hydraulic
and thermal corrections:

- `phi_f = 1 + alpha_f * z_dev`
- `phi_nu = 1 + alpha_nu * z_dev`
- `z_dev = A * Re^a * Pr^b * Ri^c * g(x_dev_over_D)`

This is the best candidate if the separate `f` and `Nu` fits appear too noisy
or too coupled for stable low-order regression.

## Fit order

Do not fit everything at once.

Recommended order:

1. fit `phi_f` on the admitted straight Salt rows
2. test whether `x_dev_over_D` or `Gz` carries clearer development signal
3. fit direct `phi_nu` on defended `left_lower_leg` rows only
4. compare:
   - uncoupled thermal family `T1`
   - hydraulically informed thermal family `T2`
   - shared-latent family `LT1`
5. only after one family is stable, decide whether the same architecture can
   drive state-surface corrections for `UA'` or `HTC`

## Data products needed from the current repo stack

Use existing defended or support-gated artifacts first.

Immediate reusable inputs:

- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_candidate_correlation_inputs.csv`
- `reports/2026-06-19_ethan_blocker_report_and_followon_wave/one_d_state_vector.csv`
- `reports/2026-06-19_ethan_blocker_report_and_followon_wave/one_d_closure_map.csv`
- `reports/2026-06-19_ethan_salt_model_dependency_package_v3/README.md`
- `reports/2026-06-19_ethan_salt_straight_hydraulic_sensitivity/`
- `reports/2026-06-19_ethan_salt_thermal_closure_hardening_v3/`
- `reports/2026-06-19_ethan_closure_to_modeling_handoff/`

Derived columns to add in the next implementation lane:

- `x_hyd_dev_m`
- `x_therm_dev_m`
- `x_hyd_dev_over_D`
- `x_therm_dev_over_D`
- `Gz_h`
- `Gz_t`
- `phi_f`
- `phi_nu`
- branch reset class
- support gate flags carried through from the current hardening packages

## Testing plan

### Path A: current `Fluid` solver

Goal:

- import the shared bundle
- replay the seven defended Salt cases
- compare casewise and branchwise errors using the same imported closure family

First checks:

- bundle contract validation
- direct `Nu` range guard on `left_lower_leg`
- residual-bucket visibility in outputs
- no hidden promotion of feature `K_eff`

### Path B: `salt_cfd_rom`

Goal:

- build the clean Salt-first seven-element skeleton
- use the same bundle as Path A
- reproduce the same CFD-only replay scorecard

First checks:

- same imported bundle manifest as Path A
- same closure-authority boundary
- same branch gating
- same residual accounting

## Monday pickup list

1. Freeze the exact feature table for the first development-aware fit:
   - decide whether the first implementation lane uses `x_dev_over_D`,
     `Gz`, or both
2. Write the explicit branch/reset-coordinate contract:
   - hydraulic reset
   - thermal reset
   - which branch transitions count as a reset
3. Decide the first response variable pair:
   - `phi_f`
   - `phi_nu`
4. Open the separate code-workspace task:
   - current `Fluid` import/replay lane
   - clean `salt_cfd_rom` skeleton
5. Build a small fit harness that can compare:
   - `F1 + T1`
   - `F1 + T2`
   - `LT1`
6. Keep Water out of the first fitting pass.
7. Keep feature `K_eff` out of the first fitted bundle.

## Monday presentation prep implications

Prepare the presentation around these points:

- why fully developed references remain useful but are not default truth
- why development-aware nondimensional closure is the right next abstraction
- what is already admitted today:
  - straight friction
  - `UA'`
  - `HTC`
  - narrow direct Salt `Nu`
- what remains blocked:
  - feature `K_eff`
  - right-leg direct thermal closure
  - Water dependency fitting
- why the current June 22 queue is already the right CFD action
- what the next code implementation split is:
  - `Fluid`
  - `salt_cfd_rom`
