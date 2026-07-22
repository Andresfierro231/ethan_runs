---
provenance:
  - tools/analyze/build_pressure_alternate_low_reverse_anchor_screen.py
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_alternate_low_reverse_anchor_screen/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_alternate_low_reverse_anchor_screen/alternate_anchor_screen.csv
tags: [status, pressure, f6, low-reverse-anchor, no-launch, no-admission]
related:
  - .agent/journal/2026-07-22/pressure-alternate-low-reverse-anchor-screen.md
  - imports/2026-07-22_pressure_alternate_low_reverse_anchor_screen.json
  - work_products/2026-07/2026-07-22/2026-07-22_pressure_alternate_low_reverse_anchor_screen/README.md
task: TODO-PRESSURE-ALTERNATE-LOW-REVERSE-ANCHOR-SCREEN-2026-07-22
date: 2026-07-22
role: Hydraulics / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-PRESSURE-ALTERNATE-LOW-REVERSE-ANCHOR-SCREEN-2026-07-22

## Objective

Screen existing non-scheduler pressure evidence for alternate low-reverse
anchors after right-leg/test-section endpoint gates failed, while avoiding the
failed lower-right component-K path.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-22/2026-07-22_pressure_alternate_low_reverse_anchor_screen/`.

Decision: `pressure_alternate_anchor_screen_complete_existing_replacement_not_found`.

Key results:

- screen rows: `40`
- existing evidence rows: `29`
- future design rows: `11`
- existing replacement-ready rows: `0`
- component-K/F6 release rows: `0`
- admissible comparison rows: `0`
- PM5 material reverse-flow rows: `12`
- PM10 strong-recirculation rows: `4`
- same-QOI UQ-ready rows: `0`

## Changes Made

- Added `tools/analyze/build_pressure_alternate_low_reverse_anchor_screen.py`.
- Added `tools/analyze/test_pressure_alternate_low_reverse_anchor_screen.py`.
- Generated package outputs:
  `alternate_anchor_screen.csv`, `disqualification_matrix.csv`,
  `no_launch_shortlist.csv`, `source_manifest.csv`,
  `no_mutation_guardrails.csv`, `summary.json`, and `README.md`.

## Validation

- `python3.11 -m py_compile tools/analyze/build_pressure_alternate_low_reverse_anchor_screen.py tools/analyze/test_pressure_alternate_low_reverse_anchor_screen.py`:
  passed.
- `python3.11 tools/analyze/test_pressure_alternate_low_reverse_anchor_screen.py`:
  passed, `3` tests.
- `python3.11 tools/analyze/build_pressure_alternate_low_reverse_anchor_screen.py`:
  passed; regenerated the pressure package.
- `python3.11 -m json.tool imports/2026-07-22_pressure_alternate_low_reverse_anchor_screen.json`:
  passed.
- `git -C . diff --check -- <pressure alternate-anchor task-owned paths>`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-PRESSURE-ALTERNATE-LOW-REVERSE-ANCHOR-SCREEN-2026-07-22`:
  passed after adding the validator-required manifest key `scheduler_action`.

## Unresolved Blockers

No existing PM5, PM10, branch-scorecard, or prior inventory row can replace
`CAND001` now. The pressure path remains blocked by material reverse flow,
missing same-QOI pressure UQ, endpoint/source/admission gaps, and CAND001
terminal evidence ownership by an active scheduler monitor row.

## Guardrails

- Native CFD/OpenFOAM outputs: read-only, not mutated.
- Registry/admission state: not mutated.
- Scheduler query/action: none.
- Solver/postprocessing/sampler/harvest/UQ launch: none.
- Fluid/external repositories and thesis current/LaTeX files: not edited.
- Validation, holdout, and external-test rows: not scored or released.
- Fitting, tuning, model selection, component-K/F6/cluster-K/clipped-K/global
  multiplier admission, source/property release, candidate freeze, and
  S11/S12/S13/S15/S6 triggers: not performed.
- Blocker register and generated docs index files: not edited.
- Lower-right two-tap pressure remains section-effective residual evidence.
