---
provenance:
  task: AGENT-363
  generated_by: tools/analyze/build_salt1_terminal_bc_and_pm5_upcomer_harvest.py
tags: [cfd-pp, salt1, boundary-conditions, corrected-q, upcomer]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/README.md
---
# Salt1 Terminal BC And PM5 Upcomer Harvest

## Salt1 Patch-Complete BC Labels

This package promotes Salt1 terminal BC labeling from partial case-level evidence
to a patch-complete table built from each actual terminal `0/T` dictionary and
`constant/polyMesh/boundary`.

Outputs:

- `salt1_terminal_patch_bc_role_table.csv`: every terminal patch for nominal,
  lo10q, and hi10q.
- `salt1_terminal_bc_role_summary.csv`: patch counts and imposed Q totals by
  role.
- `salt1_training_admission_update.csv`: current fit-use decision.

## Salt1 hi10q Resolution

The Salt1 hi10q conflict is resolved here. The older salt inventory used a stale
latest-time/failed gate. The later terminal harvest review plus this
patch-complete BC table now supersede that older row. `salt1_hi10q` can be used
as a training perturbation row, with the guardrail that it remains labeled
`hi10q` and must not be collapsed into nominal Salt1.

## PM5 Pressure/Upcomer Status

Job `3295901` is still not harvestable at package generation time:

- `squeue_state`: `PENDING`
- `squeue_reason`: `Priority`
- `sacct_state`: `PENDING`

The pressure/upcomer job has been submitted correctly, but parsed metrics cannot
be admitted until Slurm reaches terminal state and the expected parsed CSVs
exist.

## Next Steps

1. Monitor `3295901`.
2. When terminal, inspect `logs/reconstruct_*`, `logs/wallHeatFlux_*`,
   `logs/surfaces_*`, and `parsed/matched_plane_metrics_*.csv`.
3. Admit or block each pressure/upcomer metric row based on missing fields,
   recirculation, secondary-flow fraction, mixed-convection Ri, and wall-bulk
   Delta T.
4. Refresh the older Salt inventory so it no longer reports Salt1 hi10q as
   failed/not-admissible.
