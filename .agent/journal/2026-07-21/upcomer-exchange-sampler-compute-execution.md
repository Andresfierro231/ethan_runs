---
provenance:
  - tools/extract/build_upcomer_exchange_sampler_compute_execution.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/source_case_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/required_field_gap.csv
tags: [journal, upcomer, recirculation, exchange-cell, sampler, compute-gate]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-SAMPLER-COMPUTE-EXECUTION-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_sampler_compute_execution.json
task: TODO-UPCOMER-EXCHANGE-SAMPLER-COMPUTE-EXECUTION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Sampler Compute Execution

## Attempted

Implemented the next gate after the dry exchange-cell sampler design. The row
checked the Salt2/Salt3/Salt4 queued source windows and generated a future
compute-node scaffold, but only after deciding whether the extraction was ready
to submit.

## Observed

The queued windows are Salt2 at `7915` s, Salt3 at `7618` s, and Salt4 at
`10000` s. Each reconstructed time directory has the primary fields `U`, `T`,
`rho`, `p_rgh`, `Re`, `Pr`, `Ri`, `Gr`, and `Ra`. The same directories do not
have `cellVolume`, `mu`, `recircMask`, or wall heat-flux diagnostics as ordinary
time fields.

## Inferred

The extraction should not be submitted yet. The dry parser requires a same-cell
`cellVolume` basis for `V_recirc`, residence time, and volume-weighted
recirculation/main thermal states. `mu` can be missing without blocking the
sample because `R_mu` already has an unavailable-field policy. `recircMask` can
fall back to reverse `U dot n`. Wall heat-flux evidence can be generated in a
task-owned staged case on a compute node, but it remains diagnostic/support-only
and cannot become a predictive shortcut.

## Contradictions Or Caveats

The source windows are not generally missing data; they are missing one derived
diagnostic that the exchange-cell model needs to make a physically meaningful
volume claim. The generated sbatch script is therefore not a launch artifact. It
is an intentionally failing scaffold that records the queue and stops before
OpenFOAM work.

## Next Useful Actions

1. Implement a trusted cell-volume source: either export `cellVolume` into the
   same VTK cell sample or add a tested mesh-volume parser.
2. Update the compute scaffold to stage the cases, generate diagnostic wall
   heat flux where needed, sample cell/interface/wall VTK, and call
   `sample_upcomer_exchange_cell.py`.
3. Submit only from a scheduler-authorized row and record job IDs, commands,
   logs, and expected VTK/output paths.
4. Harvest rows into same-window exchange QOIs, then run same-QOI UQ before any
   Phase 4B/5/S6 claim.
