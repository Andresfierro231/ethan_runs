---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/salt1_junction_recovery_gate.csv
tags: [PASSIVE-H2, Salt1, junction, background-smoke]
related:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-SALT1-JUNCTION-SETUP-ROW-RECOVERY-BACKGROUND-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/README.md
task: TODO-PASSIVE-H2-SALT1-JUNCTION-SETUP-ROW-RECOVERY-BACKGROUND-2026-07-22
date: 2026-07-22
role: Implementer / Tester / Writer / Monitor
type: journal
status: complete
---
# PASSIVE-H2 Salt1 Junction Setup-Row Recovery

Attempted: recover the missing Salt1 junction setup row from native setup
boundary dictionaries and patch area accounting, then prepare the background
runtime smoke path.

Observed: Salt1 contains the junction/stub setup patches needed for a grouped
junction row. The recovered row is diagnostic and setup-only; it does not repair
strict source-envelope, release-UQ, or source/property release gates.

Scheduler: direct compute-node `sbatch` was refused by the TACC wrapper; the
first login-node submission lacked an account directive; after adding
`#SBATCH -A ASC23046`, the first submitted job failed on a package-side target
CSV schema mismatch. The target context was repaired with explicit `nan`
placeholders for the runner's optional target columns, and replacement Slurm
job `3312160` completed. The terminal runtime summary
used five train rows, accepted all three roots, used no forbidden/protected
runtime inputs, and produced a nonzero radiation heat-ledger response.

Observed runtime output: the failed prior execution wrote runtime summary rows
for current/no-role radiation-off, PASSIVE-H2 radiation-off, and PASSIVE-H2
radiation-on before the Fluid runner's post-summary heat-ledger comparison
failed. The retained diagnostic deltas are in
`work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/partial_heat_delta_from_runtime_summary.csv`. They are not
score values and do not use protected targets.

Inferred: this removes the mechanical Salt1 4/5 coverage issue if the background
smoke lands, but H2 still cannot freeze until source-envelope and release-UQ
are admitted.
