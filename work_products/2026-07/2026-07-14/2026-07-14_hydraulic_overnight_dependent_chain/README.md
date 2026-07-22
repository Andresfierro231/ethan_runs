# Hydraulic Overnight Dependent Chain

Date: 2026-07-14

Purpose: submit the requested overnight hydraulics stages as a dependent Slurm chain on `c318-008`, beginning after both current node job `3295120` and the existing corrected-Q dependency harvester `3295438`.

Stages:
1. `test_section_complex_raw_two_tap`
2. `f6_ready_to_run_gate`
3. `fluid_reset_k_diagnostic_sweep`

Guardrails:
- Native CFD solver outputs remain read-only.
- External `../cfd-modeling-tools` remains read-only.
- No thermal fitting is performed.
- The raw two-tap stage does not run the mutating OpenFOAM extractor on native case directories. It records the safe preflight/staging status and the remaining requirement for staged-copy raw extraction.

Expected outputs after the chain runs:
- `test_section_complex_raw_two_tap_status.csv`
- `f6_ready_to_run_gate.csv`
- `fluid_reset_k_diagnostic_sweep.csv`
- One `*_summary.json` per stage
- Slurm stdout logs under `logs/`
- `slurm_dependency_tail_manifest.csv` records the submitted dependency tail.

Submission:
- The first job should depend on `afterany:3295120:3295438`.
- The second job should depend on `afterok:<stage1_job_id>`.
- The third job should depend on `afterok:<stage2_job_id>`.

Submitted chain:

- `3295989` `test_section_complex_raw_two_tap`: `afterany:3295120` and `afterany:3295438`.
- `3295990` `f6_ready_to_run_gate`: `afterok:3295989`.
- `3295991` `fluid_reset_k_diagnostic_sweep`: `afterok:3295990`.

Older jobs `3295985`, `3295986`, and `3295987` were cancelled because they only
waited for `3295120` and did not wait for the existing corrected-Q harvester
`3295438`.
