---
provenance:
  - tools/analyze/build_1d_regime_map_nondimensional_closure_eligibility.py
  - tools/analyze/test_1d_regime_map_nondimensional_closure_eligibility.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/summary.json
task: TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22
date: 2026-07-22
role: Forward-pred / Hydraulics / Thermal-modeling / LitRev / Writer / Reviewer
type: status
status: complete
tags: [status, predictive-1d, regime-map, nondimensional, closure-eligibility]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility
  - .agent/journal/2026-07-22/1d-regime-map-nondimensional-closure-eligibility.md
  - imports/2026-07-22_1d_regime_map_nondimensional_closure_eligibility.json
---
# TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22

## Objective

Build a nondimensional regime map by case and segment using Re, Pr, Gr, Ra, Ri,
Graetz/development length, and recirculation/onset proxies to decide which
literature closure families are eligible for the current TAMU 1D model.

## Outcome

Decision: `regime_map_ready_fail_closed_no_closure_admission`.

The package was published at
`work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/`.
It contains `8` formula/provenance rows, `18` case/span regime rows, `7`
TAMU/source overlap rows, `5` closure-family decisions, and an SVG eligibility
map.

All closure families remain fail-closed for fitting:

- ordinary single-stream developing `f_D`/`Nu`: `0` fit rows;
- internal `Nu`: `0` fit rows;
- component `K` or F6: `0` fit rows;
- throughflow/recirculation exchange-cell: `0` admitted rows;
- source/property release rows: `0`.

## What Worked

- Existing LitRev and gated single-stream artifacts already carried the needed
  nondimensional rows, source titles, and source-use categories.
- The builder could aggregate the existing `90` property/case/span precheck rows
  into `18` case/span regime rows without touching native CFD outputs.
- The package produces both machine-readable tables and a compact SVG map for
  publication planning.

## What Did Not Work

- The current evidence does not admit any ordinary single-stream closure. Some
  spans are only precheck-only, and many are blocked by recirculation evidence.
- Literature formulas provide coordinates and eligibility checks, not TAMU
  source thresholds or coefficients.
- No final closure interval, coefficient, F6/component-K, or internal-`Nu` row
  was released.

## Analysis

The regime map reinforces the current scientific boundary: nondimensional
numbers are useful for model-form triage, but closure promotion still requires
source/property labels, same-QOI UQ, recirculation validity, pressure/thermal
residual ownership, and split discipline. The appropriate use is to decide which
future row to run, not to fit the present model.

The most defensible interpretation is:

- use ordinary single-stream developing forms only as prechecks where
  recirculation is not directly flagged;
- use throughflow-plus-recirculation exchange as the architecture for persistent
  local reverse mass/area, but keep coefficients blocked;
- use pressure section/cluster labels until component isolation, recovery, and
  low-recirculation source evidence exist;
- keep internal `Nu` closed to residual absorption.

## Changes Made

- `tools/analyze/build_1d_regime_map_nondimensional_closure_eligibility.py`
- `tools/analyze/test_1d_regime_map_nondimensional_closure_eligibility.py`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/`
- `.agent/status/2026-07-22_TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22.md`
- `.agent/journal/2026-07-22/1d-regime-map-nondimensional-closure-eligibility.md`
- `imports/2026-07-22_1d_regime_map_nondimensional_closure_eligibility.json`
- `.agent/BOARD.md` own row only

## Validation

- `python3.11 -m py_compile tools/analyze/build_1d_regime_map_nondimensional_closure_eligibility.py tools/analyze/test_1d_regime_map_nondimensional_closure_eligibility.py`: passed.
- `python3.11 tools/analyze/test_1d_regime_map_nondimensional_closure_eligibility.py`: passed.
- `python3.11 tools/analyze/build_1d_regime_map_nondimensional_closure_eligibility.py`: passed.

## Guardrails

- Native CFD/OpenFOAM output mutation: false.
- Scheduler, solver, sampler launch: false.
- Fluid/external repository mutation: false.
- Registry/admission/blocker-register mutation: false.
- Fit, model selection, source/property release, coefficient admission: false.
- Component `K`, F6, internal `Nu`, and exchange-cell coefficient admission:
  all remain `0`.

## Next Useful Actions

Use this package as input to thesis evidence packets and to the next
source/property release atlas. For new science, wait for the exact-label S13
sampler/post-sampler GCI row or a separate low-recirculation pressure anchor
before reopening coefficient review.
