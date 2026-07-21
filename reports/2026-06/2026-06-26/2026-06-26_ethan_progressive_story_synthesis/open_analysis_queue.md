# Open Analysis Queue

## Purpose

This queue translates the report stack’s unresolved questions into a recommended
order of work. It is not just a backlog. Each item is ranked by:

- scientific leverage
- dependency structure
- how much existing report language already points to the missing artifact

## Recommended execution order

### Queue 1: refresh the external replay against the frozen-state contract

- Main source packages:
  - `2026-06-22_ethan_fluid_replay_against_frozen_state`
  - `2026-06-23_ethan_frozen_state_1d_validation`
  - `2026-06-23_ethan_1d_closure_bakeoff`
- Why this is first:
  the repo already has a local ranking surface, but it is still anchored to a
  stale June 19 external bundle. That means every later modeling conclusion has
  a known ceiling until the replay surface is refreshed.
- Prerequisite:
  producer path in the external `Fluid` repo for a refreshed Ethan CFD-informed
  Salt bundle.
- Expected payoff:
  converts the current local shadow bakeoff into a current readable 1D-vs-CFD
  comparison surface.
- Success criteria:
  - a refreshed readable diagnostics bundle exists
  - the June 22 frozen-state contract is the comparison basis
  - the current best scenario and current under-coverage boundaries are
    recomputed on that refreshed bundle

### Queue 2: rebuild straight-section sensitivity on the matured late windows

- Main source packages:
  - `2026-06-19_ethan_salt_straight_hydraulic_sensitivity`
  - `2026-06-22_ethan_salt_straight_hydraulic_sensitivity_refresh`
  - `2026-06-22_ethan_frozen_state_results`
- Why this is second:
  straight friction is one of the most reusable defended closure lanes, and the
  report stack repeatedly says its main weakness is retained-time maturity, not
  missing conceptual framing.
- Prerequisite:
  stronger late-window continuation support on the defended Salt subset.
- Expected payoff:
  upgrades straight friction from "provisional with explicit caveats" toward a
  stronger late-window basis.
- Success criteria:
  - retained-time hydro-corrected straight rows are rebuilt on the late window
  - the defended subset and exclusions are restated from those rows, not only
    from older case means
  - the updated rows can be consumed by the next dependency package without
    silently widening scope

### Queue 3: expand retained-time branchwise thermal closure on blocked branches

- Main source packages:
  - `2026-06-19_ethan_salt_thermal_closure_hardening_v3`
  - `2026-06-19_ethan_salt_conclusions_package`
  - `2026-06-22_ethan_frozen_state_results/data_needs.csv`
- Why this is third:
  the repo’s current direct thermal story is too narrow. If broader direct
  closure is possible at all, this is the lane that tests it directly.
- Prerequisite:
  retained-time branchwise bulk temperature, wall temperature, and heat-flux
  support on the currently blocked or weak-support branches.
- Expected payoff:
  determines whether the direct domain can move beyond `left_lower_leg` or
  whether the present bounded thermal strategy is effectively the long-term
  limit.
- Success criteria:
  - right-leg and other blocked return-path rows are re-evaluated on retained
    support
  - low-`ΔT` instability and support masking are quantified explicitly
  - the result is either a widened defended domain or a cleaner permanent
    exclusion

### Queue 4: build the retained-time full-path feature extractor

- Main source packages:
  - `2026-06-19_ethan_blocker_report_and_followon_wave`
  - `2026-06-22_ethan_feature_path_hydro_decomposition`
  - `2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2`
- Why this is fourth:
  this is high-value but more upstream than the replay or straight refresh.
  The reports already show that more runtime alone is not the fix.
- Prerequisite:
  a dedicated implementation task for retained-time pathwise hydro extraction.
- Expected payoff:
  turns the current patch-endpoint provisional feature basis into the first
  candidate for defended feature-resolved `K_eff`.
- Success criteria:
  - retained-time full-path hydro quantities exist per defended feature path
  - pathwise support is reproducible across the late window
  - the next feature dependency package can distinguish endpoint proxy support
    from actual retained-time path support

### Queue 5: move Water from readiness into defended closure posture

- Main source packages:
  - `2026-06-18_ethan_transport_interpretation_closure`
  - `2026-06-19_ethan_water_readiness_handoff`
  - `2026-06-19_ethan_water_thermal_closure_readiness`
- Why this is fifth:
  the repo is already correct to keep Salt and Water separate for now. Water
  hardening should happen only after the higher-leverage Salt replay and
  closure-support upgrades land.
- Prerequisite:
  thermal rebuild on strongest direct Water spans, then feature hydraulic
  hardening, then a closure-gated Water dependency package.
- Expected payoff:
  allows a real test of whether any shared cross-family nondimensional collapse
  is justified.
- Success criteria:
  - a defended Water branch subset exists
  - Water direct exclusions remain explicit rather than being folded into a
    family average
  - any cross-family dashboard or collapse test uses same-definition rows only

### Queue 6: publish a durable development-coordinate contract

- Main source packages:
  - `2026-06-19_ethan_litrev_to_1d_modeling_handoff`
  - `2026-06-22_ethan_frozen_state_results/data_needs.csv`
- Why this is sixth:
  it is conceptually important but does not unlock as much immediate scoring
  value as the first five items.
- Prerequisite:
  explicit choice of what counts as hydraulic and thermal reset locations.
- Expected payoff:
  cleaner 1D implementation of development-aware friction and thermal closures.
- Success criteria:
  - one durable note or contract defines reset locations and development
    coordinate usage
  - the same contract can be reused in the replay and reduced-order lanes

### Queue 7: cooler-side provenance audit

- Main source packages:
  - `2026-06-15_ethan_boundary_modeling_report`
  - `2026-06-22_ethan_heat_balance_contract`
- Why this is later:
  it sharpens interpretation but does not currently block the bounded Salt-first
  replay path.
- Prerequisite:
  access to readable preprocessing or staging provenance that explains the
  cooler-side translation from nominal metadata to fixed sink `Q`.
- Expected payoff:
  cleaner explanation of cooler-side closure semantics and heat-balance
  bookkeeping.
- Success criteria:
  - the readable path from nominal cooler-side metadata to actual `0/T`
    implementation is documented
  - future reports can describe the cooler branch without ambiguous `h` versus
    fixed-sink language

## Queue summary

The queue is intentionally front-loaded toward analyses that improve the
current Salt-first closure and replay surface without reopening a broad new CFD
wave. The first three items are the highest-value near-term upgrades because
they sharpen current defended modeling results directly. The later items are
important, but they should follow the current Salt replay and retained-time
support upgrades rather than compete with them.
