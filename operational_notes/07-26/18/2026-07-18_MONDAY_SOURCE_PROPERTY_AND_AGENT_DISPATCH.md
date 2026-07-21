---
provenance:
  - .agent/STATE.md
  - .agent/BLOCKERS.md
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/source_property_enforced_fit_admission_rows.csv
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/literature-synthesis-and-gates.md
tags: [monday-handoff, coordination, source-property-labels, predictive-1d, task-dispatch]
related:
  - operational_notes/START_HERE_FOR_AGENTS.md
  - operational_notes/07-26/17/2026-07-17_MONDAY_MORNING_FRESH_AGENT_HANDOFF.md
  - operational_notes/07-26/17/2026-07-17_MONDAY_HYDRAULICS_CONTEXT_AND_NEXT_STEPS.md
  - .agent/status/2026-07-18_AGENT-546.md
  - .agent/status/2026-07-18_AGENT-549.md
task: AGENT-549
date: 2026-07-18
role: Coordinator/Writer
type: operational_note
status: complete
---
# Monday Source/Property And Agent Dispatch

Use this as the first Monday, 2026-07-20 coordination note after the standard
startup files. It assumes the generated state at `2026-07-18 15:50` plus later
board text are the current handoff surface.

## Open First

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/STATE.md`
4. `.agent/BLOCKERS.md`
5. `operational_notes/maps/forward-predictive-model.md`
6. `operational_notes/maps/literature-synthesis-and-gates.md`
7. `work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/README.md`
8. `work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/summary.json`

## Current Launch Decision

Do not launch a new weekend job from this handoff. The current read-only queue
snapshot from Saturday, 2026-07-18 showed:

| job | state | role |
| --- | --- | --- |
| `3293924` | RUNNING | corrected Salt2/Salt4 selected-Q continuation |
| `3295438` | PENDING dependency | selected-Q harvester waiting on continuation |
| `3299610` | RUNNING | Salt4 Q x insulation probe |
| `3299620` | RUNNING | Salt4 high-heat pack |
| `3302317` | RUNNING | dev/Fluid-side active work, likely tied to current external Fluid ownership |

There is no clean additional long-running launch to start before Monday. Leave
the running jobs alone. Let `AGENT-519` continue read-only scheduler monitoring
and let the active TSWFC2/external Fluid row finish or release its files before
any UMX1/TSWFC2/Fluid follow-on claims `solver.py` or launches a score grid.

## Current Open Blockers

- `two-tap-corner-lower-right-material-reverse-flow`: high. Raw endpoints are
  harvested, but all finite corner_lower_right pairs fail ordinary reverse-flow
  gates. Do not fit F6 or component K from these rows.
- `predictive-wall-test-section-submodels`: high. Wall/test-section/passive
  boundary remains the main forward-predictive blocker.
- `upcomer-onset-data-sparsity`: medium. Need near-onset/non-recirculating
  anchors and same-window pressure/thermal/UQ.
- `f6-friction-re-correction`: medium. Need non-recirculating pressure anchors
  or explicit recirculation-modeled closure, validated against `F3_shah_apparent`.

## Monday Task Packets

### 1. Source/Property Gate Infrastructure

Role: Implementer / Tester / Cleaner.

Objective: promote the AGENT-546 task-owned scanner into a reusable repo-level
gate without overlapping active broad `tools/analyze/**` TODO rows.

Inputs:

- `work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/build_source_property_label_enforcement.py`
- `work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/test_source_property_label_enforcement.py`
- `tools/agent/finish_task.py`
- `tools/agent/common.py`

Acceptance:

- One command can check a package path and fail if any fit/admission candidate
  row has blank `property_mode`, `property_sensitivity_label`,
  `source_validity_envelope_status`, `source_use_category`, or
  `provenance_author_title`.
- The command reports original gaps separately from enforced blocked rows.
- Tests include a positive labeled fixture and a failing unlabeled fixture.

Guardrails:

- Do not rewrite historical scorecards.
- Do not change scientific admission.
- Do not consume active TSWFC2 or Fluid files.

### 2. Scorecard Template / Writer Contract

Role: Implementer / Writer / Tester.

Objective: create a canonical scorecard schema or helper contract that every
future closure scorecard can reuse.

Acceptance:

- Template includes source/property labels, split legality, runtime-input audit,
  `source_paths`, `fit_allowed`, `model_selection_allowed`,
  `admission_status`, and `source_property_gate_status`.
- New package README pattern states whether it produced scorecard/admission CSVs
  and which label-gate command was run.

Guardrails:

- Keep it additive. Do not migrate every old scorecard.

### 3. Finish-Task Enforcement Hook

Role: Implementer / Tester.

Objective: make missing source/property labels hard to miss during closeout.

Acceptance:

- `finish_task.py` or a companion closeout checker detects task-owned
  scorecard/admission/fit/gate CSVs.
- If fit/admission candidate rows are present, closeout requires either a
  passing source/property label audit or an explicit `no_scorecard_outputs`
  declaration.

Guardrails:

- Avoid broad false positives on manifests and source inventories.
- Keep the error message actionable: name file, row number, missing labels.

### 4. Salt1 Source/Property Refresh

Role: Literature-synthesis / Implementer / Writer.

Objective: fill row-specific source/property coverage for Salt1 nominal before
any final Salt1-4 training/admission language.

Inputs:

- AGENT-538 source/property carryforward package.
- AGENT-546 original gap rows.
- Final predictive scorecard shell.
- Salt1 schema promotion/admission packages.

Acceptance:

- Salt1 final-training rows no longer require
  `source_property_refresh_required` in the source/property coverage audit.
- Labels are specific enough to support thesis language, not just generic
  provenance.

Guardrails:

- Do not promote Salt1 or any closure by label refresh alone.

### 5. Perturbation / External Row Label Refresh

Role: Literature-synthesis / Forward-pred / Writer.

Objective: extend source/property labels to Salt2 +/-5Q, `val_salt2`, PM10
future rows, and new-CFD placeholders.

Acceptance:

- Holdout/external rows carry complete labels but remain no-fit/no-selection.
- Scorecard rows distinguish `score_after_freeze` from `fit/model_selection`.

Guardrails:

- Do not turn holdout or external rows into training evidence.

### 6. Thesis Admission Framework Section

Role: Writer / Reviewer.

Objective: turn the source/property gate into thesis text that makes the
admission framework rigorous rather than ad hoc.

Acceptance:

- Thesis prose explains split legality, source-validity envelope,
  property-mode sensitivity, source-use category, provenance, and blocker
  labels.
- It cites AGENT-538/546 and the final scorecard shell.
- It states that blank labels are not allowed on fit/admission rows.

Guardrails:

- Avoid claiming admitted closures where AGENT-546 only produced an enforcement
  view.

### 7. TSWFC2 / Fluid Ownership Follow-Up

Role: Coordinator / Implementer / Tester.

Objective: wait for active `TODO-TSWFC2-DISTRIBUTED-WALL-FLUID` and the external
Fluid row to complete or release ownership, then decide whether to claim a
non-conflicting Fluid follow-on.

Acceptance:

- If TSWFC2 completes, read its status/journal/import and only then decide
  whether to run a bounded dry/smoke score.
- If it remains active, do not claim overlapping Fluid source files.

Guardrails:

- No UMX1 grid and no TSWFC2 grid until root/bracket and API contracts pass.

### 8. UMX1 Temperature-Periodicity / Stratification Follow-Up

Role: Forward-pred / Thermal-modeling / Implementer.

Objective: after TSWFC2/Fluid ownership clears, address the UMX1 Salt3/Salt4
temperature-periodicity bracket issue before any UMX1 score grid.

Inputs:

- AGENT-544 UMX1 dry/smoke scorer.
- AGENT-548 UMX1 stratified-reservoir blocked handoff.
- `TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR` package.

Acceptance:

- Fluid bracket expansion or equivalent root handling is implemented in a
  bounded, tested way.
- Existing rejected finite roots are not retroactively used for admission.

Guardrails:

- Do not relax accepted-root tolerances to force a pass.

### 9. Two-Tap / F6 Hydraulic Follow-Up

Role: Hydraulics / Implementer / Tester / Writer.

Objective: continue from the completed two-tap and F6 packages without fitting
from reverse-flow rows.

Acceptance:

- Either identify non-recirculating pressure anchors or publish an explicit
  recirculation-modeled apparent-cluster path.
- Any future F6 candidate must be compared against `F3_shah_apparent` and must
  pass source/property label enforcement.

Guardrails:

- No component-K admission from `corner_lower_right` reverse-flow rows.
- No hidden global multiplier.

## Structure Rule Going Forward

Every future scorecard/admission package should include this closeout sentence
in its status and README:

> Source/property label gate: passed/failed/not applicable. If applicable, no
> fit/admission candidate row has blank `property_mode`,
> `property_sensitivity_label`, `source_validity_envelope_status`,
> `source_use_category`, or `provenance_author_title`.

If the answer is failed, the row stays blocked/diagnostic. If the answer is not
applicable, the package must explain why it produced no fit/admission candidate
rows.

## Monday Coordinator Order

1. Check `squeue -u andresfierro231` and AGENT-519 status first.
2. Check whether `TODO-TSWFC2-DISTRIBUTED-WALL-FLUID` and external Fluid
   ownership completed.
3. Dispatch source/property infrastructure work before any new scorecard build.
4. Dispatch Salt1 and perturbation/external label refreshes in parallel.
5. Only after those gates exist, let predictive/F6/wall agents create new
   scorecards.
6. Refresh `.agent/STATE.md` / `.agent/BLOCKERS.md` at the end of Monday's
   first coordination pass.
