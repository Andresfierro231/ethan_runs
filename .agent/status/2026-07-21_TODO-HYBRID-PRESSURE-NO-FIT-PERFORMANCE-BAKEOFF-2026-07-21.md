---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/README.md
tags: [pressure-ledger, hybrid-pressure, no-fit, bakeoff]
related:
  - .agent/journal/2026-07-21/hybrid-pressure-no-fit-performance-bakeoff.md
  - imports/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff.json
task: TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Tester/Writer
type: status
status: complete
---
# TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21

## Objective

Test the section-effective hybrid pressure route without coefficient tuning by
comparing observed decomposition, Salt2-frozen diagnostic transfer, oracle upper
bound, and available F3/Shah apparent baseline status on train-only evidence.

## Outcome

Published a no-fit bakeoff package. Result: the current hybrid pressure term is
thesis evidence only, not candidate-reviewable for freeze/admission. The
Salt2-frozen diagnostic transfer has max Salt3/Salt4 error
`0.47046606946166093438399 Pa`; F3/Shah numeric comparison remains unavailable
because existing artifacts report `not_evaluated_no_ordinary_candidate`.

## Changes Made

- Added `tools/analyze/build_hybrid_pressure_no_fit_performance_bakeoff.py`.
- Added `tools/analyze/check_hybrid_pressure_no_fit_performance_bakeoff.py`.
- Added `tools/analyze/test_hybrid_pressure_no_fit_performance_bakeoff.py`.
- Created `work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/**`.
- Updated `.agent/BOARD.md` to claim and close the row.

## Validation

- `python3.11 -m py_compile tools/analyze/build_hybrid_pressure_no_fit_performance_bakeoff.py tools/analyze/check_hybrid_pressure_no_fit_performance_bakeoff.py tools/analyze/test_hybrid_pressure_no_fit_performance_bakeoff.py` — pass.
- `python3.11 -m unittest tools.analyze.test_hybrid_pressure_no_fit_performance_bakeoff` — pass, 4 tests.
- `python3.11 tools/analyze/build_hybrid_pressure_no_fit_performance_bakeoff.py` — pass.
- `python3.11 tools/analyze/check_hybrid_pressure_no_fit_performance_bakeoff.py` — pass.
- `python3.11 tools/agent/finish_task.py --task-id TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21` — pass.

## Unresolved Blockers

- F3/Shah numeric comparison remains blocked until an ordinary admissible F6 row
  passes ordinary-flow, same-QOI UQ, source/property, and endpoint gates.
- Current lower-right rows remain blocked for component-K/F6 admission by
  reverse flow, component isolation, same-basis straight/developing reference,
  and same-QOI UQ.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, validation/holdout/external-test score, fitting,
tuning, model selection, component-K/F6/cluster-K admission, clipped K,
hidden/global multiplier, S11/S15/S6 trigger, blocker register, generated index,
mixed-basis promotion, or thesis current file was changed.
