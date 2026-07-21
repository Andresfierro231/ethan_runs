# Phase 3 Full Report Synthesis

## Purpose

This pass goes beyond chronology and package triage. It asks what the full
report stack now says when read as one technical argument rather than as a set
of dated packages.

## Executive synthesis

The repo’s work matured by narrowing the claim surface faster than it expanded
the artifact surface.

At the start, the workspace was trying to prove it could stage cases, publish
them, and compare CFD against experiment. By the end of the current stack, the
repo had become much more selective:

- it defended only the closure rows with durable retained-time support
- it kept `upcomer` and `right_leg` explicitly outside a generic direct-Nu
  story
- it moved Water into a readiness lane rather than forcing it into the same
  model family as Salt
- it treated feature `K_eff` as a blocker-specific extraction problem instead
  of as something more runtime would automatically fix

That selectivity is the strongest sign of progress in the package history.

## Technical lane synthesis

### 1. Hydraulic evidence lane

The hydraulic lane moved through three distinct stages.

First, the repo built basic friction and pressure summaries
(`2026-06-09_ethan_streamwise_friction_package`;
`2026-06-09_ethan_dense_streamwise_friction_package`).
These packages were method prototypes. Their own implementation notes show that
they were still discovering the right streamwise coordinate and face coverage.

Second, the Salt 2 case-analysis package repaired the streamwise registration
problem (`2026-06-10_ethan_salt2_case_analysis_package`). This is the moment
the repo became comfortable using direct-vs-shear hydraulic comparisons as part
of the scientific story rather than only as debugging views.

Third, the transport scrutiny and interpretation packages converted the
hydraulic outputs into an evidence gate
(`2026-06-17_ethan_transport_scrutiny_package`;
`2026-06-18_ethan_transport_analysis_package`;
`2026-06-18_ethan_transport_interpretation_closure`).

What is defended now:

- bounded Salt straight-section hydraulic evidence
- exclusion of Water `left_lower_leg` from any strong cross-family claim
- explicit caution around Salt upper-leg direct-vs-shear magnitude mismatch

What is still only provisional:

- any Salt upper-leg story stronger than "same sign, materially different
  magnitude"
- any Water-to-Salt shared hydraulic collapse

### 2. Thermal closure lane

The thermal lane became more disciplined over time.

Early heat-flow and direct-validation packages established that the repo could
close sectionwise energy balances and compare against experiment, but they did
not yet support broad direct closure claims
(`2026-06-04_ethan_direct_validation`;
`2026-06-09_ethan_steady_state_heat_flow_audit`).

The June 15 through June 18 transport wave introduced richer thermal summaries:

- effective HTC and `UA'`
- parasitic and intended heat-loss separation
- azimuthal wall transport
- first-pass boundary-layer landmarks

The critical move happened on June 19, when the repo stopped treating these as
"more thermal outputs" and instead ranked them by admissibility
(`2026-06-19_ethan_salt_thermal_closure_hardening_v3`;
`2026-06-19_ethan_salt_conclusions_package`).

What is defended now:

- direct thermal closure remains strongest on `left_lower_leg`
- effective `UA'(x)` is the leading bounded Salt thermal surface
- residual remains reported explicitly rather than hidden in fitted `Nu`

What remains blocked:

- `right_leg` direct thermal closure
- broader direct developing-flow `Nu` beyond the safe domain
- any Water direct dependency package

### 3. Feature-path closure lane

This lane is the cleanest example of the repo learning to separate
"scientifically interesting" from "currently defensible."

The June 17 pressure package and the June 19 feature hardening passes showed
that feature behavior was visible, but the evidence was still a residual-style
proxy (`2026-06-17_ethan_pressure_htc_boundarylayer_package`;
`2026-06-19_ethan_salt_feature_hydraulic_hardening`;
`2026-06-19_ethan_salt_feature_path_hydraulic_hardening`).

The June 22 decomposition changed the status materially:

- the path-to-proxy provenance matched exactly
- the repo could defend a patch-endpoint pathwise basis
- `corner_upper_right` and `test_section_complex` reopened

But the June 22 v4 dependency package keeps the right boundary:
the reopened basis is still not a full retained-time feature-path integral
(`2026-06-22_ethan_feature_path_hydro_decomposition`;
`2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2`;
`2026-06-22_ethan_salt_model_dependency_package_v4`).

The full report story here is not "feature closure is solved." It is
"the blocker is now much sharper and more upstream than it was before."

### 4. 1D replay and reduced-order modeling lane

This lane became coherent only after the repo had already limited the 3D claim
surface.

The early discrepancy report correctly identified that the 1D and 3D stacks
were misaligned in assumptions, but it did not yet have the later closure gate
to define what a defensible import bundle should be
(`2026-06-02_ethan_1d_model_discrepancy_report`).

The real modeling lane appears on June 19:

- `2026-06-19_ethan_closure_to_modeling_handoff`
- `2026-06-19_ethan_litrev_to_1d_modeling_handoff`
- `2026-06-19_ethan_blocker_report_and_followon_wave`

The frozen-state and replay packages then convert that plan into a bounded
comparison contract:

- `2026-06-22_ethan_frozen_state_results`
- `2026-06-22_ethan_fluid_replay_against_frozen_state`
- `2026-06-23_ethan_frozen_state_1d_validation`
- `2026-06-23_ethan_1d_closure_bakeoff`

What is defended now:

- the first useful model should be Salt-first
- direct closures should be branch-bounded
- effective state surfaces should carry the broader thermal load
- the local replay surface is good enough for ranking and filtering

What remains blocked:

- the readable external replay bundle is stale
- no defended broad direct-Nu surface exists
- no justified shared Salt/Water closure family exists

### 5. Operational and continuation lane

The operational lane is part of the science story, not just cluster management.

The continuation diagnosis, blocker wave, weekend triage, corrected relaunch,
balanced Salt scenario wave, checkpoint freeze, and normal-queue relaunches all
feed directly into what rows can later be defended
(`2026-06-05_ethan_continuation_diagnosis`;
`2026-06-19_ethan_blocker_report_and_followon_wave`;
`2026-06-22_ethan_weekend_run_triage`;
`2026-06-22_ethan_corrected_continuation_relaunch`;
`2026-06-23_ethan_cfd_freeze_checkpoint`;
`journals/2026-06/2026-06-23_ethan_runs.md`).

The lesson is consistent:

- continuations were not busywork
- queue changes altered retained-time support quality
- the meaning of "freeze" had to be clarified because it directly affected the
  validity of the bounded analysis contract

## What the full stack now argues

The full stack argues for a conservative but actionable posture:

- The repo has enough evidence to support a bounded Salt-first 1D import path.
- The repo does not yet have enough evidence to flatten branch distinctions or
  combine Salt and Water into a shared closure family.
- The highest-value missing work is not a giant new scenario sweep. It is a
  small number of precise evidence upgrades:
  - refreshed external replay
  - stronger late-window straight rows
  - broader retained-time branchwise thermal support
  - retained-time full-path feature hydro support

## Interpretation boundaries that should remain explicit

- Do not rewrite provisional rows as defended because later packages look more
  polished.
- Do not treat Water readiness tables as equivalent to defended Water closure
  rows.
- Do not promote boundary-layer landmarks into closure inputs until a retained
  profile contract exists.
- Do not describe the reopened feature `K_eff` basis as a full feature-volume
  integral closure.
