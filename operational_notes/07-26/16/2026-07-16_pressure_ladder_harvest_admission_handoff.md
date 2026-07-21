---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/case_pressure_ladder_admission_summary.csv
tags: [handoff, pressure-ladder, hydraulics, no-duplicate-jobs]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch/README.md
  - .agent/status/2026-07-16_AGENT-449.md
task: AGENT-449
date: 2026-07-16
role: Coordinator/Hydraulics/Writer
type: operational_note
status: complete
---
# Pressure Ladder Harvest Admission Handoff

## Start Here

Open
`work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/README.md`
first, then inspect
`branch_orientation_straight_loss_recirc_admission.csv`.

## Current State

Pressure ladder outputs are available. AGENT-445 and AGENT-447 harvests have
already been integrated into a branch orientation, straight-loss subtraction,
and recirculation-mask admission table.

No duplicate jobs should be submitted for:

- AGENT-445 pressure ladder job `3297860`
- AGENT-447 expanded pressure ladder job `3297863`

## Output Contract

The current table is an admission screen, not a coefficient table. It admits
`0` true `f_D` or component `K` rows. Any later coefficient package must carry
the pressure-definition, tap-orientation, station-distance, straight-loss,
recirculation, mesh/GCI, and source-window gates explicitly.

## Do Not Do

- Do not treat the harvested reverse-area proxy rows as low-recirculation
  single-stream evidence.
- Do not promote upcomer-lane branches into ordinary-pipe coefficient fits.
- Do not use these pressure rows as predictive-model runtime inputs.
- Do not submit more pressure-ladder jobs for the same rows without a new
  failure or coverage gap documented in a board row.
