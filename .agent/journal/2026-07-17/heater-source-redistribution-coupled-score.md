---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/coupled_delta_vs_m3.csv
  - tools/analyze/build_heater_source_redistribution_coupled_score.py
tags: [forward-model, heater-source, heat-placement, wall-circuit, handoff]
related:
  - .agent/status/2026-07-17_AGENT-511.md
  - imports/2026-07-17_heater_source_redistribution_coupled_score.json
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-511
date: 2026-07-17
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Heater Source Redistribution Coupled Score

## Why This Exists

AGENT-507 narrowed the remaining wall/test-section blocker to local thermal-field
physics. The first executable model was heater/source redistribution because the
current Fluid solver already supports `heater_source_mode="tw4_to_tp3_three_span"`
without an external source edit.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/selected_heater_source_weights.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/coupled_delta_vs_m3.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/candidate_admission_review.csv`

## Observed Output

- A bounded compute-node `srun` pass completed/reused `27/27` Fluid rows with accepted roots.
- Salt2-only lambda selection chose `lambda=0.00`.
- The selected source vector is upstream weighted:
  `tw4_to_tw5=0.60`, `tw5_to_tw6=0.30`, `tw6_to_tp3=0.10`.
- Runtime audit passed.
- Validation and holdout both fail the M3 comparison gate for both cooler forms.
- The best rows improve mdot versus M3 but make TP/TW/all-probe temperatures much
  worse.

## Inference

Moving the heater source within the existing TW4-to-TP3 span is not enough to
repair the temperature-shape error created by the current wall/passive/test-section
model. The optimum pushed to the upstream endpoint, so the predeclared source
redistribution family does not expose an interior physically useful correction.

This shifts priority to the Fluid features the user expects in the next pass:
upcomer mixing/stratification and explicit test-section wall/fluid coupling.

## Caveats

- This task intentionally keeps the older Salt2-train, Salt3-validation,
  Salt4-holdout blocker-removal split. Final thesis scoring still needs the
  AGENT-481 canonical split once a candidate is actually admissible.
- The result is crossed with PB2 wall distribution and admitted cooler mechanics;
  it is not a standalone statement about all possible heater physics.
- No external Fluid source was edited.

## Next Useful Actions

1. Implement the updated Fluid upcomer mixing model and score a one-scalar
   recirculation/exchange candidate.
2. Implement explicit test-section wall/fluid coupling with a local wall node and
   setup-only wall-to-ambient resistance.
3. Add incremental/checkpoint writes to any future long coupled grid campaign so
   partial completed rows survive job-level interruption.

## Do Not Do

- Do not admit `HS1` from mdot improvement alone.
- Do not rerun the same 27-row campaign unless the Fluid solver or candidate
  contract changes.
- Do not fit heater-source lambda on Salt3/Salt4, perturbation rows, or external
  validation rows.
