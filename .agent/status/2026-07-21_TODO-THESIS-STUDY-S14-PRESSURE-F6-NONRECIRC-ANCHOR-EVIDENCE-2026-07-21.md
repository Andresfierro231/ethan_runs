---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f6_branch_use_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f6_branch_decision_table.csv
tags: [thesis-dossier, s14, pressure, f6, branch-use, no-admission]
related:
  - .agent/journal/2026-07-21/thesis-study-s14-pressure-f6-nonrecirc-anchor-evidence.md
  - imports/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/README.md
task: TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21 Status

## Objective

Score current F6-relevant pressure evidence and decide where F6 should be used,
where it should remain diagnostic, where it is a future candidate, and where it
must not be used.

## Outcome

Complete. The S14 package scores `53` rows:

- `0` admit
- `11` diagnostic-only
- `8` future-candidate
- `34` do-not-use

Current F6 evidence is suitable for diagnostic branch screening only. It is not
suitable for admitted F6/component-K scoring until ordinary-flow and same-QOI UQ
gates pass. Preferred future ordinary lanes remain `right_leg` and
`test_section_span`.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21.md`
- `.agent/journal/2026-07-21/thesis-study-s14-pressure-f6-nonrecirc-anchor-evidence.md`
- `imports/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence.json`
- `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/**`

## Validation

- `python3.11 tools/agent/preflight_task.py --task-id TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21` passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/build_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence.py work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/test_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/test_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence.py` passed with 6 tests.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. No scheduler action, solver/postprocessing/sampler launch, Fluid edit,
external repo edit, fitting/tuning/model selection, component-K admission, F6
fit, clipped K, hidden/global multiplier, mixed-basis promotion,
blocker-register edit, generated-index refresh, or S11 trigger was performed.

Next useful action: refresh terminal low-recirculation source readiness or run a
separately claimed sampler/UQ row before any F3-vs-F6 scoring release.
