# Ethan Closure-Status Gate

Generated: `2026-06-29T17:53:18-05:00`

## Scope

- Write the current paper-facing closure gate as one dated package rather than
  leaving it split across the June 19 closure stack, the June 26 queue, and
  the June 29 paper-inventory / reduction-audit follow-ons.
- Label each current branch or closure family as `defended`,
  `support-gated`, `diagnostic-only`, `residual-only`, or `blocked`.
- Preserve concrete failure examples for every non-defended lane.

## Current basis

- The authority for this package is the current June 26 local closure bundle
  plus the June 22 published local validation/bakeoff surface.
- The June 29 paper subset and reduction-contract audit are used to freeze the
  paper-facing Salt scope and to make the mixed reduction provenance explicit.
- This package is intentionally **not** post-overnight latest-window:
  `AGENT-121`, `AGENT-122`, and `AGENT-123` still have the refreshed
  latest-window frozen, validation, bakeoff, and discrepancy packages queued.

## Current gate summary

- `defended`
  - straight friction on admitted `lower_leg` / `test_section_span`
  - direct `Nu(Re)` on `left_lower_leg` only
- `support-gated`
  - `UA'` on `left_lower_leg`, `left_upper_leg`, and `test_section_span`
- `diagnostic-only`
  - `upcomer` thermal state surface
  - secondary `HTC` surface on the safe Salt subset
- `residual-only`
  - `lower_leg` and `upper_leg` direct thermal closure
  - hydraulic and thermal residual buckets for unsupported losses
- `blocked`
  - `right_leg` direct thermal closure
  - feature `K_eff`
  - Water thermal and feature dependency fits

## Output tables

- `work_products/2026-06-29_ethan_closure_status_gate/closure_status_by_branch_and_family.csv`
- `work_products/2026-06-29_ethan_closure_status_gate/blocked_questions.csv`
- `work_products/2026-06-29_ethan_closure_status_gate/source_surface_status.csv`

## Main boundary

- The honest current story is still narrow:
  - the direct Salt thermal lane is `left_lower_leg` only
  - the broader Salt thermal story still runs through bounded `UA'` surfaces
    and explicit residual buckets
  - `upcomer` and `right_leg` remain different closure problems
  - Water remains readiness-only
- The readable external `Fluid` replay remains stale relative to the current
  June 22 closure surface, so this package does not treat the readable replay
  as the current final validation authority.

## Ranked next actions

1. Let the overnight latest-window chain land, then refresh this package only
   if the admitted or blocked labels actually change.
2. Refresh the readable external replay against the June 22 closure surface.
3. Quantify `upcomer` recirculation before widening any derived-branch thermal
   claim.
4. Rebuild retained-time branchwise thermal support on the blocked return-path
   branches if broader direct thermal closure is still desired.
