---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/adjacent_pressure_ladder.csv
  - work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/adjacent_pressure_ladder.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/summary.json
tags: [pressure-ladder, hydraulics, branch-orientation, straight-loss, recirculation-mask]
related:
  - .agent/status/2026-07-16_AGENT-449.md
  - operational_notes/07-26/16/2026-07-16_pressure_ladder_harvest_admission_handoff.md
task: AGENT-449
date: 2026-07-16
role: Hydraulics/Implementer/Tester/Writer
type: journal
status: complete
---
# Pressure Ladder Harvest Admission Table

## Observed Output

The July 15 pressure-ladder harvest outputs are present and parsed. AGENT-445
job `3297860` contributes `72` adjacent pair rows for Salt2/Salt3/Salt4
mainline rows. AGENT-447 job `3297863` contributes `192` adjacent pair rows for
Salt1 nominal/perturbed rows, Salt2 +/-5Q holdouts, Salt4 +/-5Q training
perturbations, and `val_salt2`.

AGENT-449 built:

- `branch_orientation_straight_loss_recirc_admission.csv`
- `adjacent_pair_recirc_screen.csv`
- `case_pressure_ladder_admission_summary.csv`

## Interpretation

All `66` case-branch rows remain diagnostic. The harvested ladders are useful
for orientation and straight-loss screening, but not for final coefficient
fitting. All branch rows are blocked by the reverse-area recirculation mask, and
`24` branch rows also carry static-`p` versus `p_rgh` net-sign conflicts.

The upcomer-related ladder branches (`left_lower_leg`, `test_section_span`, and
`left_upper_leg`) remain in the hybrid/onset lane. They are not ordinary
single-stream `Nu`, `f_D`, or `K` evidence.

## Next Suggested Actions

Use this table as the handoff point for pressure admission:

1. Do not submit duplicate pressure-ladder jobs for the rows covered by
   AGENT-445 and AGENT-447.
2. If coefficient fitting is still desired, first define pressure definition,
   tap orientation, station distance/geometry normalization, straight-loss
   subtraction, low-recirculation masks, mesh/GCI, and source-window gates in
   one package.
3. Keep any component `K` or distributed `f_D` claim out of final forward-v1
   until those gates pass together.

## Validation

- `python3.11 -m unittest tools.analyze.test_pressure_ladder_harvest_admission_table` passed `5/5`.
- `python3.11 tools/analyze/build_pressure_ladder_harvest_admission_table.py` regenerated the package.

Generated index refresh was intentionally skipped because another active board
row owned the generated `.agent` index files during this task.
