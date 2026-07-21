---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/local_test_section_behavior.csv
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/candidate_admission_review.csv
  - tools/analyze/build_test_section_wall_fluid_coupling_candidate.py
tags: [forward-model, wall-fluid-coupling, test-section, handoff]
related:
  - .agent/status/2026-07-17_AGENT-526.md
  - imports/2026-07-17_test_section_wall_fluid_coupling_candidate.json
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/
  - work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study/
task: AGENT-526
date: 2026-07-17
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Test-Section Wall/Fluid Coupling Candidate

## Why This Exists

AGENT-511 showed that source redistribution alone improves mdot but worsens the
temperature field. AGENT-522 showed that changing wall-drive selectors without
an explicit series wall/fluid coupling also fails admission. The remaining
planned fallback was to test whether a local test-section bulk-to-ambient series
resistance could improve the test-section/upcomer temperature shape without
using validation/holdout data as inputs.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/coupled_delta_vs_m3.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/local_test_section_behavior.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/candidate_admission_review.csv`

## Methodology

- Used AGENT-511's completed Salt2-only source selection, `lambda=0.00`.
- Used PB2 wall/test-section distribution as the base external-boundary table.
- Crossed with the two existing cooler candidates:
  `HX_LUMPED_UA_NTU` and `HX_SEGMENTED_UA_NTU_N16`.
- Applied the new model only to the `left_upper_vertical` role row named
  `test_section`.
- Computed that row's heat loss using a series path:
  bulk fluid to ambient through `R_i_prime + R_wall_prime` and setup external
  `hA`; other role rows retained the existing direct external hA behavior.
- Installed the behavior through a process-local Fluid adapter during scoring
  and restored the original function after each solve.

## Observed Output

- Runtime audit passed.
- `6/6` coupled rows completed with accepted roots.
- `102` full probe rows and `18` local test-section/upcomer-bracket rows were
  emitted.
- `0/2` candidates admitted.
- Both cooler forms improved mdot relative to M3 on validation and holdout.
- Both cooler forms failed TP, TW, and all-probe RMSE gates by large margins.

## Inference

The explicit local series resistance is not the missing mechanism by itself.
The result is scientifically useful because it separates the scalar wall/source
thermal-circuit hypothesis from the remaining blocker: the model can get flow
rate close while still placing the thermal field incorrectly. The next
candidate must change the upcomer/test-section thermal state itself, most likely
through a mixing, stratification, or recirculation-aware exchange term.

## Assumptions

- Salt2 remains the only fit/select row for this candidate family.
- Salt3 and Salt4 are validation/holdout rows only.
- The current M3 comparator remains the admission baseline for this blocker.
- Local TP5/TP6/TW8 behavior is diagnostic only; it does not override the
  global mdot, TP, TW, and all-probe admission gates.

## Do Not Do

- Do not admit this candidate from mdot improvement alone.
- Do not tune the series resistance on Salt3/Salt4.
- Do not persistently edit Fluid source from this package.
- Do not reinterpret the local TP5 improvement question as permission to ignore
  TW or all-probe gates.

## Next Useful Actions

1. Build a one-parameter upcomer/test-section mixing or stratification candidate
   with Salt2-only selection and the same Salt3/Salt4 gates.
2. Add a residual table comparing AGENT-511, AGENT-522, and AGENT-526 at TP5,
   TP6, TW8, and TW10 to quantify which failure is common across all scalar
   wall/source variants.
3. If a mixing candidate still fails TW10/HX-active wall behavior, split the
   cooler-adjacent wall thermal state from the test-section/upcomer state before
   trying another global external hA change.
