---
provenance:
  - tools/analyze/build_thesis_model_form_scoreboard_training_roster.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/summary.json
tags: [journal, thesis, model-form-scoreboard, training-roster]
related:
  - .agent/status/2026-07-22_TODO-THESIS-MODEL-FORM-SCOREBOARD-TRAINING-ROSTER-2026-07-22.md
task: TODO-THESIS-MODEL-FORM-SCOREBOARD-TRAINING-ROSTER-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Thesis Model-Form Scoreboard Training Roster

## Attempted

Audited the master model-form scoreboard, recent diagnostic model-form
appendices, and current July 22 source-property/UQ/development/recirculation
packages to enumerate the model forms that should be tried next.

## Observed

The master scoreboard already covers M0, M3, M5/MF-04, MF-02/two-tap, MF-01,
and M6/S6. Newer working families needed an additive training roster:
MF12 signed source-memory bulk-to-TP projection, MF15 wall/core exchange, MF15
axial mixing, MF07/MF08/MF10 development/reset/signed wall-flux variants, and
the D1-D4 empirical bias-shape diagnostics.

The canonical next split can train on Salt1-4 nominal rows, but support,
holdout, and external-test rows must remain locked until a single candidate is
frozen. Older Salt3/Salt4 transfer packages cannot be used as validation if
Salt1-4 nominal rows are used for training.

## Inferred

The immediate path is not "try every correction and look at holdout." It is:
close the active train-only setup-UQ run, repair source/property exact-field
release if possible, predeclare a small set of candidate families, train only
on Salt1-4 nominal rows, freeze exactly one runtime-legal candidate, and then
score validation/holdout/external rows once.

## Contradictions Or Caveats

The D1-D4 bias corrections showed useful diagnostic error reductions in legacy
Salt2-train/Salt3-Salt4-transfer context, but those coefficients are not a
physical predictive closure. They should inform MF12/MF15 mechanism design, not
serve as final thesis corrections unless replaced by source-bounded runtime
operators.

## Next Useful Actions

Close and interpret the active 1D train-only setup-UQ smoke execution. Then run
strict source-property recovery. If that gate opens, select 3-5 forms from the
roster and train them on Salt1-4 nominal rows without reading protected
validation, holdout, or external-test targets.

## Guardrails

No protected scoring, fitting, model selection, source/property release,
coefficient admission, candidate freeze, solver/scheduler action,
native-output mutation, registry/admission mutation, or Fluid/external edit
occurred.
