# 2026-06-30 Paper Package Readiness Index

## Purpose

This note identifies which existing report packages are most useful for paper
work after the June 30 run-classification update. It does not modify generated
reports. It gives a current reading order and trust boundary so Claude's closure
work can proceed separately.

## Current Paper-Facing Anchors

- `reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/`
  - Status: current scope anchor.
  - Use: defines the present paper subset as `paper-grade = Salt 1-4 Jin`.
  - Boundary: records `Salt 2 Kirst` as exploratory and `Salt 1 Kirst` as
    blocked under the older surface; June 30 policy demotes all Kirst rows to
    historical/provenance unless re-admitted later.
- `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/`
  - Status: current provenance anchor.
  - Use: station map, branch map, reduction choices, and mixed provenance for
    Salt 1 Jin latest-window root versus Salt 2-4 June 15 roots.
  - Boundary: should be refreshed after the latest-window Salt 2-4
    continuation package is republished.
- `reports/2026-06/2026-06-29/2026-06-29_ethan_closure_status_gate/`
  - Status: current claim-gate anchor.
  - Use: labels closure families as `defended`, `support-gated`,
    `diagnostic-only`, `residual-only`, or `blocked`.
  - Boundary: intentionally not post-latest-window; refresh only if
    continuation results change admitted/blocked labels.
- `reports/2026-06/2026-06-29/2026-06-29_ethan_salt_pressure_drop_predictivity/`
  - Status: useful hydraulic replay package, but status file still says
    `in_progress`.
  - Use: 9-case frozen-reference pressure-budget and local hydraulic replay.
  - Boundary: board/status should be reconciled before citing as final.
- `reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/`
  - Status: completed additive evidence package.
  - Use: upcomer recirculation evidence for the paper-grade Salt Jin subset.
  - Boundary: mixed Salt 1 latest-window versus Salt 2-4 June 15 provenance.
- `reports/2026-06/2026-06-26/2026-06-26_ethan_progressive_story_synthesis/`
  - Status: best narrative/progression index.
  - Use: explains how priorities shifted and which claims became defended,
    provisional, or blocked.
  - Boundary: predates the June 30 Kirst exclusion and latest-window repair.

## Stale Or Refresh-Gated Packages

- `reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff/`
  - Treat as stale support until the continuation/latest-window chain lands.
  - Kirst rows inside this package are not current mainline evidence.
- `reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation/`
  - Useful for old validation surfaces, but not the current final authority.
  - Refresh-gated on the latest-window chain and external Fluid replay work.
- `reports/2026-06/2026-06-23/2026-06-23_presentation/`
  - Do not use as a current deck without refresh. It still promotes Kirst
    representative rows and Salt 2 Kirst figure labels.
- `reports/2026-06/2026-06-18/*closure*` and
  `reports/2026-06/2026-06-19/*closure*`
  - Valuable method-development history.
  - Use only with the June 29/30 claim gate in front of it.

## Current Reading Order

1. `2026-06-30_run_classification_policy.md`
2. `2026-06-29_ethan_paper_case_inventory/README.md`
3. `2026-06-29_ethan_reduction_contract_audit/README.md`
4. `2026-06-29_ethan_closure_status_gate/README.md`
5. `2026-06-30_kirst_reference_cleanup.md`
6. Claude's AGENT-156 outputs after they finish

## Next Useful Package Work

- Refresh the June 23 presentation package so its representative rows follow
  the continuation/Jin mainline policy.
- Rebuild the latest-window validation/bakeoff/discrepancy packages once the
  local chain finishes.
- Refresh the June 29 reduction-contract audit if Salt 2-4 all move from June
  15 roots to a consistent latest-window package root.
