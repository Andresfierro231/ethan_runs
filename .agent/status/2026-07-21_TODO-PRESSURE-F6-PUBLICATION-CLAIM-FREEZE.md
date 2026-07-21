---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/pressure_f6_publication_claim_freeze.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/pressure_corner_narrative_update.md
tags: [pressure, f6, publication, claim-freeze, no-admission]
related:
  - .agent/journal/2026-07-21/pressure-f6-publication-claim-freeze.md
  - imports/2026-07-21_pressure_f6_publication_claim_freeze.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/README.md
task: TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE
date: 2026-07-21
role: Writer / Reviewer / Hydraulics / cfd-pp
type: status
status: complete
---
# TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE

## Objective

Freeze publication-facing pressure/F6 claims after the static-pressure basis
audit and S14 F6 branch-use study, while keeping coefficient admission separate
from diagnostic pressure-corner interpretation.

## Outcome

Completed a publication claim package at
`work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/`.

The frozen result is:

- F6 may be used for diagnostic pressure-basis and branch-screening claims only.
- Coarse static-pressure differences may be reconstructed diagnostically with
  `p = p_rgh + rho * (g dot x)`, validated against Stage A pair deltas with max
  error `4.382729351630587 Pa`.
- Pressure rise around corners is hydrostatic/recovery/section-effective/
  diagnostic evidence, not negative loss.
- Current endpoint evidence remains blocked for coefficient scoring:
  `0/10` endpoint pairs pass RAF/RMF ordinary-flow gates.
- Future F6/component-K review requires ordinary-flow evidence, same-QOI
  mesh/time UQ, and F3 comparison in a separate task.

## Changes Made

- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/build_pressure_f6_publication_claim_freeze.py`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/test_pressure_f6_publication_claim_freeze.py`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/summary.json`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/pressure_f6_publication_claim_freeze.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/pressure_f6_claim_boundary_ledger.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/f6_static_basis_publication_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/f6_use_decision_publication_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/admission_blocker_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/ordinary_flow_next_steps.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/pressure_corner_narrative_update.md`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/source_manifest.csv`
- `.agent/status/2026-07-21_TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE.md`
- `.agent/journal/2026-07-21/pressure-f6-publication-claim-freeze.md`
- `imports/2026-07-21_pressure_f6_publication_claim_freeze.json`
- `.agent/BOARD.md` own row status only

## Validation

- `python3.11 tools/agent/preflight_task.py --task-id TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE`
  passed before edits.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/build_pressure_f6_publication_claim_freeze.py work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/test_pressure_f6_publication_claim_freeze.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/test_pressure_f6_publication_claim_freeze.py`
  passed: `Ran 5 tests in 0.293s OK`.

## Guardrails

No native solver output, registry/admission state, scheduler state, solver,
sampler, harvest output, Fluid source tree, external repo, blocker register,
generated docs index, or manuscript/report file was mutated. No fit, tuning,
model selection, clipped `K`, hidden multiplier, F6 coefficient, component `K`,
cluster `K`, or S11 release was produced.

## Remaining Blockers

The active admission blocker is ordinary-flow evidence. Current F6 endpoint
pairs are `0/10` passing RAF/RMF, so no coefficient admission can proceed until
a lower-recirculation source family or anchor is found. After an ordinary-flow
candidate exists, the next required gates are same-QOI mesh/time UQ and F3
comparison before any F6/component-K review.
