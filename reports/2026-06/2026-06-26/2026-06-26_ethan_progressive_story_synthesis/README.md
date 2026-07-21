# Ethan Progressive Story Synthesis

Generated: `2026-06-26`

## What this package does

This package turns the Ethan journal trail and the analytical report stack into
one progressive story. It focuses on:

- what was tried
- how priorities shifted
- what became defended versus only provisional
- what was learned from failed or partial attempts
- what still needs more analysis before stronger claims are justified

Primary source groups:

- journals: `journals/2026-05/2026-05-29_ethan_runs.md`,
  `journals/2026-06/*.md`
- report pass anchors:
  `reports/2026-06/2026-06-10/2026-06-10_ethan_salt2_case_analysis_package`,
  `reports/2026-06/2026-06-18/2026-06-18_ethan_transport_analysis_package`,
  `reports/2026-06/2026-06-19/2026-06-19_ethan_closure_to_modeling_handoff`,
  `reports/2026-06/2026-06-22/2026-06-22_ethan_frozen_state_results`,
  `reports/2026-06/2026-06-22/2026-06-22_ethan_fluid_replay_against_frozen_state`,
  `reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff`,
  `reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation`

Package entry points:

- chronology first: `phase1_journal_synthesis.md`
- report-gap scan: `phase2_report_gap_scan.md`
- deeper technical read: `phase3_full_report_synthesis.md`
- next-work program: `open_analysis_queue.md`
- row-level follow-ups: `analysis_followups.csv`

## Progressive story

### 1. Intake and reality-check phase

The first phase was not yet about reduced-order closure. It was about proving
the workspace could intake Ethan cases, publish a usable contract, and answer a
basic question: which cases were even mature enough to analyze
(`2026-05-29` through `2026-06-05` journals; `2026-06-02_ethan_1d_model_discrepancy_report`;
`2026-06-04_ethan_direct_validation`; `2026-06-04_ethan_essential_steadiness_audit`;
`2026-06-05_ethan_convergence_and_salt1_campaign`).

The early priority was therefore:

- register and publish cases
- separate coded convergence from practical usability
- stop overstating Water readiness
- identify whether disagreement was mostly runtime immaturity or model-form
  mismatch

This phase already forced one durable correction: fully developed assumptions
could not be treated as defaults just because literature reference values
existed or the geometry looked long.

### 2. Salt 2 became the method-repair anchor

By `2026-06-09` through `2026-06-11`, the work narrowed onto Salt 2 because it
was the fastest route to repairing the method itself. The main focus shifted to:

- heat-accounting clarity
- streamwise friction extraction
- direct versus shear-based hydraulic comparison
- fixing streamwise registration and provenance bugs

This culminated in the June 10 Salt 2 package and the June 11 rigor note
(`2026-06-10_ethan_salt2_case_analysis_package`;
`2026-06-11_salt2_internal_technical_report_brief`;
`2026-06-11_salt2_rigor_repair_methods_note`;
`journals/2026-06/2026-06-10_ethan_runs.md`).

The important lesson here was procedural and scientific at the same time:
better geometry registration and better provenance discipline changed which
hydraulic spans were even interpretable. The workflow stopped pretending that a
stable-looking number was useful if the coordinate definition behind it was
wrong.

### 3. Transport expansion was followed immediately by trust gating

From `2026-06-12` through `2026-06-18`, the repo expanded from one repaired
Salt 2 case into a reusable transport workflow across Salt, then Water, and
then the cross-case campaign (`2026-06-15_ethan_representative_transport_comparison`;
`2026-06-15_ethan_field_transport_campaign`;
`2026-06-15_ethan_all_runs_field_transport_campaign`;
`2026-06-17_ethan_transport_scrutiny_package`;
`2026-06-18_ethan_transport_analysis_package`;
`2026-06-18_ethan_transport_interpretation_closure`).

Priority changed again at this point. The question stopped being
"can we extract more fields?" and became
"which extracted results are safe to promote?"

That shift produced the repo’s most mature interpretation pattern:

- publish the broad outputs
- gate them into `paper_safe`, `internal_only`, or excluded
- preserve contradictions explicitly
- define safe subsets instead of forcing full-family claims

This is where several enduring boundaries were fixed:

- Water `left_lower_leg` became an exclusion problem, not a mystery to gloss
  over
- Salt branch-thermal promotion narrowed to a safe subset
- cross-family hydraulic claims stayed blocked
- boundary-layer outputs remained contextual rather than promoted closure inputs

### 4. The work pivoted from 3D interpretation to 1D planning

On `2026-06-19`, the center of gravity moved from "what can the 3D reports
say?" to "what is the first defensible 1D modeling bundle?"
(`2026-06-19_ethan_closure_to_modeling_handoff`;
`2026-06-19_ethan_litrev_to_1d_modeling_handoff`;
`2026-06-19_ethan_salt_conclusions_package`;
`2026-06-19_ethan_blocker_report_and_followon_wave`).

The key change in priorities was explicit:

- stop trying to defend a universal closure set
- start building a bounded Salt-first model with exclusions stated up front
- use effective thermal state surfaces where direct closure is too narrow
- keep Water in readiness mode
- keep `feature K_eff` out of the first defended model

This phase also made the open questions more disciplined. Instead of a generic
"more CFD is needed" story, the reports identified specific missing observables:

- retained-time full-path hydro support for feature `K_eff`
- stronger late-window straight rows
- broader retained-time thermal support beyond `left_lower_leg`
- a durable development-coordinate contract for entry/reset effects

### 5. Frozen-state and continuation support became the active contract

From `2026-06-22` through `2026-06-25`, the main thread narrowed again around
the frozen-state contract, active queue triage, and replay boundaries
(`2026-06-22_ethan_frozen_state_results`;
`2026-06-22_ethan_frozen_state_roadmap`;
`2026-06-22_ethan_fluid_replay_against_frozen_state`;
`2026-06-23_ethan_frozen_state_1d_validation`;
`2026-06-23_ethan_1d_closure_bakeoff`;
`2026-06-23_ethan_cfd_freeze_checkpoint`;
`journals/2026-06/2026-06-22_ethan_runs.md`;
`journals/2026-06/2026-06-23_ethan_runs.md`).

This phase clarified two things at once:

- what the repo can currently defend from the preserved late windows
- what remains stale or under-supported in the external readable 1D bundle

The frozen-state package is therefore both a result and a boundary document.
It strengthened the current Salt closure picture, but it also made the limits
of the current replay surface impossible to hide.

## Priority shifts

1. `intake -> validation triage`
   The work began by proving local case reachability, publication, and first
   validation rather than closure fitting.

2. `broad validation -> Salt 2 method repair`
   Once it was clear that not all cases were equally mature, Salt 2 became the
   anchor for hydraulic registration, heat-accounting, and direct-vs-shear
   method repair.

3. `more outputs -> trust gating`
   The transport campaign produced a lot of data, but the more important move
   was the scrutiny and contradiction workflow that reduced the promotable
   subset.

4. `3D report writing -> 1D modeling bundle design`
   The repo then pivoted from paper-staging around field data to building a
   bounded closure bundle for reduced-order use.

5. `generic future work -> blocker-specific next actions`
   By June 19 onward, "needs more analysis" became specific missing
   observables, not a vague request for more runtime.

## Main findings

- `defended`: Salt straight friction is usable only on an explicit bounded
  subset and still carries caveats about late-window sensitivity and branch
  scope (`2026-06-19_ethan_salt_conclusions_package`;
  `2026-06-22_ethan_frozen_state_results`).
- `defended`: direct Salt thermal closure is strongest on `left_lower_leg`;
  broader direct Nu claims are still not supported
  (`2026-06-19_ethan_salt_conclusions_package`;
  `2026-06-23_ethan_frozen_state_1d_validation`).
- `defended`: `upcomer` should not be treated as a generic straight-branch Nu
  problem; it remains a separate modeling lane
  (`2026-06-22_ethan_frozen_state_results`;
  `2026-06-22_ethan_fluid_replay_against_frozen_state`).
- `provisional`: feature `K_eff` reopened only after the June 22 pathwise
  decomposition, and even then only on a patch-endpoint basis rather than a
  full retained-time path integral
  (`2026-06-22_ethan_feature_path_hydro_decomposition`;
  `2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2`;
  `2026-06-22_ethan_salt_model_dependency_package_v4`).
- `blocked`: Water still does not support a defended cross-family closure
  collapse. The repo’s own trust gates repeatedly keep Water in readiness or
  exclusion-heavy posture (`2026-06-18_ethan_transport_analysis_package`;
  `2026-06-19_ethan_water_readiness_handoff`).
- `blocked`: the readable external `Fluid` surface is still stale relative to
  the June 22 frozen-state closure contract
  (`2026-06-22_ethan_fluid_replay_against_frozen_state`;
  `2026-06-23_ethan_1d_closure_bakeoff`).

## Lessons learned

- A long section is not equivalent to a fully developed closure row. This was
  corrected early and stays central to the later 1D planning surface.
- Better geometry registration can change the scientific interpretation, not
  just the plot quality. The June 10 Salt 2 repair is the clearest example.
- More output is not the same as more admissible evidence. The June 17 and
  June 18 scrutiny packages were necessary because the raw transport expansion
  alone would have encouraged over-claiming.
- Queue and runtime decisions mattered scientifically. The continuation waves
  were not just operational work; they were the fastest route to the
  retained-time support the closure packages explicitly lacked.
- The repo got stronger when it named exclusions and support limits directly
  instead of smoothing them into the main story.

## Open questions

- What is the retained-time full-path hydro quantity needed to promote feature
  `K_eff` beyond patch-endpoint provisional status?
- Can the mature late-window continuation roots promote a stronger straight
  sensitivity package than the current case-mean defended set?
- Which branches beyond `left_lower_leg` can support retained-time thermal
  closure without collapsing into low-`ΔT` instability or support-limited
  ratios?
- Can Water reach a defended comparable branch subset, or should Salt and Water
  remain separate modeling families for the foreseeable future?
- What exact development/reset coordinate contract should the 1D model use for
  buoyancy and re-development effects?

## Highest-value next analyses

1. Refresh the external readable 1D replay against the frozen-state contract
   so the local bakeoff is no longer compared to a stale June 19 bundle.
2. Rebuild straight-section sensitivity on the matured late windows after the
   continuation lanes preserve stronger retained support.
3. Add retained-time branchwise thermal support on currently blocked branches,
   especially cooler-adjacent return behavior.
4. If feature closure rises in priority, open a dedicated retained-time
   feature-path extractor rather than assuming more runtime alone solves it.
5. Keep any future cross-family collapse test behind Water closure hardening on
   a comparable branch subset.

## Open-analysis queue

The recommended order is now documented explicitly in `open_analysis_queue.md`.
The queue is intentionally not "everything still missing." It is ranked by
which missing artifact most improves the current defended modeling posture.

Recommended order:

1. refresh the external replay bundle
2. rebuild straight sensitivity on the matured late window
3. expand retained-time branchwise thermal support
4. build the retained-time full-path feature extractor
5. harden Water before any cross-family collapse attempt
