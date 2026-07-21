---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/candidate_terminal_preflight.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/source_case_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/sampler_or_no_launch_decision.json
tags: [pressure-corner, low-recirculation-anchor, journal]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-CORNER-LOW-RECIRC-ANCHOR-HARVEST.md
  - imports/2026-07-21_pressure_corner_low_recirc_anchor_harvest.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/README.md
task: TODO-PRESSURE-CORNER-LOW-RECIRC-ANCHOR-HARVEST
date: 2026-07-21
role: cfd-pp/Hydraulics/Tester/Writer
type: journal
status: complete
---
# Pressure-Corner Low-Recirculation Anchor Harvest Journal

## Attempted

I implemented the preflight portion of the low-recirculation anchor harvest from
existing artifacts. The package consumes the scientific synthesis, pressure
corner freeze, same-QOI UQ table, nonrecirculating anchor plan, F6/two-tap
staging handoff, high-heat readiness monitor, F6 anchor terminal refresh, and
matched-plane recirculation inventory.

## Observed

`CAND-001` remains the best source family because it preserves the
`corner_lower_right` topology and targets Salt4 high-heat/no-recirculation probe
cases. The cited readiness artifacts still report scheduler/terminal state as
not checked or not ready, and the candidate endpoint raw fields have not been
sampled. Therefore terminal-ready cases are zero.

`CAND-002` remains a fallback only after a terminal-admission refresh. `CAND-003`
is deferred because exact alternate labels and low-reverse evidence are absent.
Current Salt2/Salt3/Salt4 rows are explicitly rejected as ordinary anchors
because their reverse-flow metrics already fail.

## Inferred

The blocker is not scientific ambiguity about the current corner rows; it is
source readiness for the proposed low-reverse source family. A future sampler
should not launch until a terminal-refresh or latest-CFD schema-promotion row
confirms terminal success and exact staged-copy scope.

## Contradictions Or Caveats

This task did not query live scheduler state, launch a sampler, or inspect
native fields directly. It intentionally preserves the terminal-gated state from
the cited artifacts. If newer terminal evidence exists, it should be promoted
through a separate claimed row before sampling.

## Next Useful Actions

Run `TODO-LITREV-LATEST-CFD-SCHEMA-PROMOTION` or a narrower high-heat terminal
refresh row. If high-heat `CAND-001` is terminal successful, claim an exact
staged-copy sampler row for `lower_leg__s04;right_leg__s00`. Only if same-window
`RAF < 0.01` and `RMF < 0.01` pass should ordinary component-K review be queued.
