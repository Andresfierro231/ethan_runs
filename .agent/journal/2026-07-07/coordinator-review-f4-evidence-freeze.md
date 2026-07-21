# Coordinator Review: F4 Evidence Freeze

Date: `2026-07-07`  
Task: `AGENT-189`  
Role: Coordinator / Reviewer / Writer

## Context

The requested attack plan was to freeze admitted evidence at mainline Salt 2/3/4
Jin, build a read-only F4 calibration table with Ri/Ra/Re audit, compare F1/F3/F4/F5,
and only then open a separate solver-edit task.

## Review Result

`AGENT-187` already completed a useful Salt 2/3/4 mainline F4 calibration table
and documented it. It also edited external `friction_closures.py` to add
`F4_leg_class` before the full Ri audit and model comparison were complete.

Current disposition:

- Treat `F4_leg_class` as provisional data-driven pressure-resistance evidence.
- Do not treat it as the final Ri-corrected F4 mixed-convection law.
- Do not open further solver edits until a read-only Ri/F4 table and F1/F3/F4/F5
  comparison are complete.

## Evidence Freeze

Admitted for the next read-only table:

- Salt 2 Jin mainline continuation.
- Salt 3 Jin mainline continuation.
- Salt 4 Jin mainline continuation.

Held:

- Salt 1: pending a dedicated qualification package.
- Corrected Salt Q: pending formal operating-point gate.
- Any row with `needs_special_gate_scrutiny=True`: no closure-fit admission
  without coordinator review.

## Outputs

- `work_products/2026-07-07_f4_evidence_freeze_review/README.md`
- `work_products/2026-07-07_f4_evidence_freeze_review/f4_evidence_freeze_review.json`
- `work_products/2026-07-07_f4_evidence_freeze_review/recent_related_changes.csv`
- `.agent/status/2026-07-07_AGENT-189.md`

## Next Action

Open a separate read-only Implementer task for the Ri/F4 calibration table. That
task should not edit `../cfd-modeling-tools/**`. Solver edits should wait until
the table and model comparison satisfy the acceptance criteria in the review
package.
