---
task: AGENT-435
date: 2026-07-15
role: Coordinator/Writer
type: operational_note
status: complete
tags: [branch-models, upcomer, recirculation, admission, forward-model]
related:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md
---
# Branch-Specific Model Forms and Upcomer Omission Plan

## Decision

Current Salt2-4 upcomer evidence is recirculating. Therefore the upcomer must
not be included in ordinary single-stream `Nu`, `f_D`, or `K` fits. This is not
a failure to analyze the loop; it is the admission rule that lets the rest of
the loop move forward without forcing one invalid model form everywhere.

The immediate analysis plan is:

1. Omit recirculating upcomer rows from ordinary-pipe coefficient fits and from
   ordinary-pipe aggregate fit-quality claims.
2. Perform ordinary single-stream analysis on the other branches where the local
   regime supports it.
3. Use different model forms per branch.
4. Keep the upcomer in a separate recirculation/hybrid/onset lane.

## Branch Policy

| Branch / region | Ordinary single-stream `Nu`, `f_D`, `K` fit? | Model-form lane |
| --- | --- | --- |
| Downcomer | Yes, if local gates pass | Ordinary pipe/developing-flow friction and internal heat-transfer forms |
| Heater / lower leg | Yes with source/entrance gates | Heater source model plus branch-local pressure/thermal development terms |
| Cooler / HX branch | Not as a simple pipe heat-loss fit | HX/UA or effectiveness model plus branch-local pressure loss |
| Test section | Conditional | Ordinary/developing form only if local regime gates pass; otherwise distributed setup-only heat-loss model |
| Junction / stub / connector regions | No | Named-loss, branch-apparent, mixing, or explicit boundary/source terms |
| Upcomer, current Salt2-4 rows | No | Omit from ordinary-pipe fits; model separately as throughflow plus recirculation-cell exchange |

## Upcomer Lane

The upcomer remains scientifically important, but it needs a different model
form:

```text
mdot_loop = mdot_through
Q_upcomer = Q_through_internal + Q_recirculation_cell + Q_mixing + Q_unresolved
dp_upcomer = dp_through + dp_development/reset + dp_cell_apparent + dp_junction
```

Candidate regime weights should come from reverse-flow area fraction,
reverse-flow mass fraction, secondary velocity fraction, `Ri`, `Gr`, `Ra`,
`Re`, `Pr`, `Gz`, and wall-bulk temperature drive. Ordinary/transition anchors
such as Re 150/200/250 are still needed before onset is calibrated.

## Scorecard Requirements

The branch-specific scorecard must publish:

- included/excluded branch masks,
- equations used per branch,
- nondimensional ranges for each included branch,
- admission status for each branch/coefficient row,
- train/validation/holdout score deltas,
- a separate list of recirculating upcomer rows handed to the hybrid/onset lane.

Do not report a single global `Nu`, `f_D`, or `K` claim for the loop. Report
branch-local forms and their gate status.

## Board Task

Created:

- `TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD`

This complements:

- `TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL`
- `TODO-PREDICT-SEGMENT-EQUATION-CONTRACT`
- `TODO-PREDICT-SEGMENT-PRESSURE-MODELS`
- `TODO-PREDICT-SEGMENT-THERMAL-MODELS`

## Guardrails

- Do not fit or label recirculating upcomer rows as single-stream `Nu`, `f_D`,
  or `K`.
- Do not hide branch differences inside a global multiplier.
- Do not use validation TP/TW temperatures as runtime inputs.
- Do not mutate native CFD solver outputs.
- Keep external `../cfd-modeling-tools/**` read-only unless a later board row
  explicitly claims it.
