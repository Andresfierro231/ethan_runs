# Ethan Lit Review To 1D Modeling Handoff

Generated: `2026-06-19`

## Purpose

This package converts the source-audited closure menu in the literature-review
repo into a repo-local 1D modeling guide for future Ethan reduced-order work.
It is intentionally narrower than the literature review and more explicit than
the current closure-to-modeling handoff: it maps literature forms onto the
current Ethan CFD artifact stack and states which closures are admitted,
comparison-only, calibration-only, or blocked.

## Immediate answer

Yes, the work can start now.

Nothing foundational blocks the analysis and reporting lane for the next Salt
ROM pass. What is blocked is narrower:

- defended feature `K_eff`
- broader direct `Nu` promotion outside the current safe branch/domain
- any claim that the readable 3D cooler boundary is a live direct `h` closure

This package now includes an execution layer for two implementation paths:

- current solver path in `Fluid`
- new clean Salt ROM path named `salt_cfd_rom`

## Core correction to the earlier assumption

The literature review correctly identifies fully developed laminar circular-pipe
friction and fully developed laminar Nusselt limits as important baselines, but
this repo should not assume that every long section behaves as pressure-drop
developed or thermally developed.

The main reasons are already visible in the audited source stack:

- the literature review itself keeps hydrodynamic redevelopment and apparent
  friction separate from fully developed friction in
  `../papers/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/chapters/04_friction_apparent_friction.tex`
- the same review treats fully developed `Nu = 3.657` or `Nu = 4.364` as
  limiting references rather than default truth for the TAMU loop in
  `../papers/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/chapters/14_Jun18_bigger_lit_rev_pot_overlap.tex`
- the current repo handoff admits only a narrow defended subset for direct
  hydraulic and thermal closure use:
  `reports/2026-06-19_ethan_closure_to_modeling_handoff/README.md`
- the blocker package already fixes the first defended 1D model as hybrid, not
  fully closed:
  `reports/2026-06-19_ethan_blocker_report_and_followon_wave/one_d_implementation_spec.md`

Practical rule:

- fully developed values are baseline references
- developing-flow terms are allowed only where they are justified and scoped
- unresolved features and return-path behavior stay as explicit residual buckets

## Current v1 modeling boundary

The best current defended boundary stays aligned with the June 19 blocker and
closure packages.

Admit now:

- Salt family only
- straight-section hydraulic closure on `lower_leg` and `test_section_span`
- primary thermal surface `UA'(x)` on:
  - `left_lower_leg`
  - `test_section_span`
  - `left_upper_leg`
  - `upcomer`
- secondary thermal surface `HTC(x)` on the same safe Salt subset
- direct fitted `Nu(Re)` only on `left_lower_leg`
- visible 3D boundary-condition inputs:
  - heater `Q`
  - fixed cooler `Q`
  - ambient temperature
  - insulation selection / thickness
  - explicit salt material branch

Do not admit yet:

- feature-resolved `K_eff`
- Water-family dependency fits
- direct fitted `Nu` on `right_leg`
- direct fitted `Nu` on derived `upcomer`
- live cooler-side `h` control

These boundaries are grounded in:

- `reports/2026-06-19_ethan_salt_model_dependency_package_v3/README.md`
- `reports/2026-06-19_ethan_blocker_report_and_followon_wave/one_d_closure_map.csv`
- `reports/2026-06-18_ethan_salt_thermal_model_surface_ranking/README.md`
- `reports/2026-06-15_ethan_boundary_modeling_report/README.md`

## Hydraulic closure policy

### 1. Distributed friction

Use local-property laminar Darcy friction as the baseline distributed-friction
 law in straight smooth sections:

- literature baseline:
  - Fanning `f_F = 16 / Re`
  - Darcy `f_D = 64 / Re`
- repo rule:
  - keep Fanning/Darcy conventions separate everywhere
  - compare directly to Reis wall-shear work only in Fanning convention
  - use Darcy convention in the 1D pressure-drop balance unless the source is
    explicitly Fanning

### 2. Redevelopment and apparent friction

Use Shah-style apparent-friction thinking only where a profile reset or short
redeveloping section is physically justified. In this repo, that is a
comparison or sensitivity tool, not a loop-wide default closure. The best
candidate region remains the quartz / test-section transition family described
in the literature review friction chapter.

### 3. Local losses

Keep contractions, expansions, elbows, reducers, and fittings separate from
distributed friction. If a section may carry both a local loss and downstream
redevelopment, those remain separate terms unless an explicitly empirical
effective coefficient is being used.

### 4. Current blocker

Feature `K_eff` remains blocked because the current readable additive artifact
stack does not preserve the retained-time full-path hydro integral needed for a
defended feature-loss closure. The current repo evidence only supports a
positive residual bucket, not a defended feature-resolved `K_eff`.

## Thermal / HTC / Nusselt closure policy

### 1. Fully developed limits

Treat fully developed laminar `Nu` limits as lower-order comparison surfaces:

- constant wall temperature circular baseline: `Nu ≈ 3.657`
- uniform heat-flux circular baseline: `Nu ≈ 4.364`

These are useful reference values, not default truth for all current Ethan
sections.

### 2. Developing thermal closure

The literature review supports using developing-flow and high-`Pr` thermal
diagnostics, especially Graetz-style logic and Muzychka/Yovanovich combined
entry forms, but the repo does not yet have a defended direct implementation of
those models across the current branch inventory. For the first defended model:

- use `UA'(x)` as the primary thermal state surface
- carry `HTC(x)` as the secondary surface
- use direct fitted `Nu(Re)` only on `left_lower_leg`
- treat broader entry-correlation use as sensitivity-only until the needed CFD
  observables are preserved more directly

### 3. Mixed convection and buoyancy flags

The literature review supports using buoyancy-aware diagnostics for vertical and
heated segments, but those should be gating flags rather than automatic closure
switches. Use `Gr`, `Ra`, `Ri = Gr / Re^2`, and `Gz` as interpretation aids
before promoting a new thermal law.

## Heat-loss and boundary-condition policy

The readable 3D boundary model is essential context for any 1D closure choice.
The local boundary-model report shows that:

- the cooler branch is a fixed negative `Q` sink in readable `0/T`, not a live
  cooler-side convective `h` control
- heater power is readable and directly imposed
- insulation thickness is readable and directly imposed
- external losses are wall-surrogate boundary conditions rather than a resolved
  external-fluid domain

Therefore:

- use fixed cooler `Q`, not a hidden cooler `h`, in the first defended 1D
  forcing contract
- keep external-loss effects explicit instead of hiding them inside internal
  `Nu`
- retain one thermal residual bucket for unsupported walls and cooler-vicinity
  behavior until broader direct closure support exists

## Nondimensional priorities

The most useful immediate nondimensional quantities are listed in
`nondimensional_group_spec.csv`. The short version is:

- `Re` and `Pr` remain first-line state descriptors
- `Gz` is the main entry-development diagnostic
- `Gr`, `Ra`, and `Ri` are mixed-convection / buoyancy flags
- `Nu` stays branch-specific and support-gated
- boundary-layer thickness ratios are diagnostic-only for now

Do not force a shared Salt/Water collapse yet. The June 17 nondimensional
dashboard explicitly keeps the families separate pending a later defended audit:
`reports/2026-06-17_ethan_nondimensional_dashboard_package/README.md`

## Package contents

- `closure_crosswalk.csv`
  - literature and repo closure map with admitted vs blocked status
- `segment_closure_policy.csv`
  - per-segment or per-family closure policy
- `nondimensional_group_spec.csv`
  - nondimensional and diagnostic quantity spec
- `required_future_cfd_observables.csv`
  - exact missing observables needed for future closure upgrades
- `dual_path_execution_report.md`
  - implementation brief for `Fluid` and `salt_cfd_rom`
- `correlation_registry.csv`
  - narrowed correlation and closure registry for the dual-path ROM work
- `shared_closure_bundle_contract.csv`
  - machine-readable contract for the shared CFD closure bundle both paths
    should consume
- `rom_test_matrix.csv`
  - CFD-only ROM replay and acceptance test matrix
- `dual_path_workstreams.csv`
  - prioritized work packages and exit criteria
- `development_aware_closure_plan.md`
  - concrete next-step plan for development-aware nondimensional friction and
    thermal closures plus Monday handoff notes
- `report_outline.md`
  - section skeleton for a later deeper write pass
- `writing_checklist.md`
  - completion and review gate
- `open_questions.md`
  - unresolved items that must remain explicit
- `summary.json`
  - package metadata and row counts

## Queue refresh on 2026-06-22

No additional CFD submission is justified from this report package on
`2026-06-22`.

The closure authority in this handoff is unchanged. What changed is the known
runtime state of the June 18 and June 19 jobs:

- running:
  - `3244950` `ethan_s3j_cont`
  - `3244951` `ethan_s2j_cont`
  - `3244954` `ethan_s4j_cont`
  - `3244957` `ethan_w2_cont`
  - `3246561` `ethan_s2j_hiqins`
  - `3246564` `ethan_s2j_loqins`
  - `3250524` `ethan_s4j_hiqins_r2`
  - `3250525` `ethan_s4j_loqins_r2`
- pending:
  - `3250526` `ethan_salt_optpack`
- failed:
  - `3246562` `ethan_s4j_hiqins`
  - `3246563` `ethan_s4j_loqins`
  - `3246927` `ethan_salt_optpack`
- timed out:
  - `3244952` `ethan_w3_cont`
  - `3244953` `ethan_w1_cont`
  - `3244956` `ethan_w4_cont`
- completed:
  - `3244955` `ethan_s1j_cont`

Interpretation boundary:

- the Salt 4 relaunches and the repaired optimum-wave relaunch are workflow
  repairs, not new closure evidence
- the Water timeouts reinforce the existing bounded Water-readiness stance, but
  they do not revoke the admitted Salt-only modeling boundary
- the deferred Salt 3 Jin midpoint bracket should still stay deferred until the
  active bracket wave and repaired optimum wave show acceptable health

## Recommended next use

1. Use `dual_path_execution_report.md` as the start-here implementation brief
   for the Salt CFD-informed ROM push.
2. Use `development_aware_closure_plan.md` as the concrete next-step fitting
   plan for development-aware nondimensional closures.
3. Use `shared_closure_bundle_contract.csv`,
   `correlation_registry.csv`, and `rom_test_matrix.csv` as the machine-readable
   handoff into the actual 1D code workspace.
4. Keep the current `AGENT-087` and `AGENT-089` report roots as the source of
   truth for admitted v1 closures.
5. Open a separate follow-on task when the work shifts from report planning in
   `ethan_runs` into actual 1D code implementation in the solver workspace.
