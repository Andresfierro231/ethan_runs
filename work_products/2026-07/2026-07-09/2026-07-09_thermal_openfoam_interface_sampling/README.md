# Thermal OpenFOAM Interface Sampling

Generated: `2026-07-09T16:45:18-05:00`
Task: `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`

## Scope

This package prepares and launches a bounded compute-node OpenFOAM sampling run
for admitted Salt 2/3/4 Jin mainline cases. Source case trees remain read-only.
Task-local reconstructed mirrors and postProcessing outputs live under
`tmp/2026-07-09_thermal_openfoam_interface_sampling` and `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling`.

## Sampling Targets

- heater interior: bracketed inside the lower leg around
  `pipeleg_lower_04_straight` through `pipeleg_lower_06_straight`
- cooler/reducer interior: bracketed inside the upper leg around
  `pipeleg_upper_06_reducer`, `pipeleg_upper_05_cooler`, and
  `pipeleg_upper_04_reducer`
- junction control volumes: lower-left, lower-right, upper-right, upper-left,
  and test-section lower/upper junction faces

## Outputs

- `sampling_plane_plan.csv`: generated OpenFOAM plane geometry and provenance.
- `sampling_targets.csv`: case roots, retained times, reconstructed mirrors,
  and output directories.
- `scripts/run_local_smoke_preflight.sh`: login-safe smoke/preflight.
- `scripts/run_thermal_openfoam_interface_sampling.sh`: compute-node driver.
- `scripts/submit_overnight_thermal_sampling.sbatch`: bounded overnight Slurm
  wrapper.
- `outputs/<source_id>/openfoam_interface_samples.csv`: written after the
  compute-node job samples and parses each case.

## Semantics

The parser preserves both signed mixing-cup and dominant forward-flow bulk
temperatures. Backflow is reported as a fraction of the dominant directional
flux at each plane. Radiation is not inferred from emissivity; `qr` is sampled
only if OpenFOAM exposes a reconstructed `qr` field, otherwise rows carry
`absent_no_qr_output`.

## Counts

- Cases: `3`
- Planes per case: `16`
- Total planned planes: `48`
