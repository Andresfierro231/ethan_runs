# Hydraulic Overnight Dependent Chain

2026-07-14T19:08:00-05:00 - Claimed AGENT-373 to submit the user-requested overnight hydraulics chain on `c318-008` after current node job `3295120`.

Initial scheduler context:
- `3295120` is running on `c318-008` in `NuclearEnergy-dev`; this is treated as the "already running job" on this node.
- `3293924` is a separate long-running job on `c318-016`.
- `3295438` is pending on dependency.

Planned dependency chain:
1. `test_section_complex_raw_two_tap` afterany:`3295120:3295438`
2. `f6_ready_to_run_gate` afterok:stage1
3. `fluid_reset_k_diagnostic_sweep` afterok:stage2

Safety decision:
- The existing raw OpenFOAM tap extractor writes into case `system/controlDict` and `postProcessing`; therefore this chain will not mutate native CFD solver outputs. The first stage records a safe raw-two-tap preflight/staging decision unless a staged-copy extraction path is explicitly available.

2026-07-14T17:57:00-05:00 - Submitted corrected dependency tail through
`login3`:

- `3295989` for `test_section_complex_raw_two_tap`, dependency
  `afterany:3295120` and `afterany:3295438`.
- `3295990` for `f6_ready_to_run_gate`, dependency `afterok:3295989`.
- `3295991` for `fluid_reset_k_diagnostic_sweep`, dependency `afterok:3295990`.

Cancelled older jobs `3295985`, `3295986`, and `3295987` because they only
waited for `3295120` and did not respect the requested ordering after the
existing corrected-Q dependency harvester.
