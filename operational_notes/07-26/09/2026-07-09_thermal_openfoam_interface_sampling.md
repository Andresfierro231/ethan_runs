# Thermal OpenFOAM Interface Sampling

Date: `2026-07-09`
Task: `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`

## Purpose

Create the missing physical-interface sampling needed to move thermal rows from
wall-flux-only diagnostics toward defensible thesis validation rows.

## Package

- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/`

## What Is Sampled

The sampling plan adds planes for:

- heater interior brackets inside the lower leg;
- cooler/reducer interior brackets inside the upper leg;
- junction control-volume faces at lower-left, lower-right, upper-right,
  upper-left, and the lower/upper test-section junctions.

The plan uses mesh-centerline geometry from:

- `work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/**/mesh_stations.json`

## Flow/Thermal Semantics

The parser keeps these quantities separate:

- signed mixing-cup bulk temperature;
- positive-normal bulk temperature;
- negative-normal bulk temperature;
- dominant-forward bulk temperature;
- backflow fraction;
- signed, positive, and negative flux proxies.

This preserves reverse-flow/backflow information instead of hiding it in one
temperature.

## Radiation Rule

Do not infer radiation from emissivity metadata. The generated OpenFOAM
controlDict includes `qr` only when a reconstructed `qr` field exists. Otherwise
rows report `absent_no_qr_output`.

## Submitted Job

- Job ID: `3287311`
- Job name: `th_ofsamp`
- Partition/account: `NuclearEnergy` / `ASC23046`
- Wall limit: `08:00:00`
- Initial state: `PD (Resources)`
- Final state: `COMPLETED`, `ExitCode=0:0`, elapsed `00:01:20`
- Slurm wrapper:
  `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/scripts/submit_overnight_thermal_sampling.sbatch`

## Completion Output

- Combined samples:
  `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv`
- Completion summary:
  `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/job_completion_summary.json`

All `48/48` planned rows parsed successfully. No `qr` field was exposed, so the
radiation output term remains `absent_no_qr_output`.

## Next Step After Completion

Review the combined sample rows, then claim
`TODO-OBSERVATION-TABLE-THERMAL-REFRESH` so the observation table can consume
these physical-interface rows with the correct recirculation and no-`qr`
semantics.
