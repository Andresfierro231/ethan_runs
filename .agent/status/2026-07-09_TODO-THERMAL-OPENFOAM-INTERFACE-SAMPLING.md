# TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING Status

Date: `2026-07-09`
Role: Coordinator / Implementer / Tester / Writer

## Task

Design, smoke-check, and submit a bounded compute-node OpenFOAM sampling job
that brackets heater interiors, cooler/reducer interiors, and junction control
volumes for Salt 2/3/4 Jin mainline thermal validation.

## Scope

Edited:

- `.agent/BOARD.md` own row
- `.agent/status/2026-07-09_TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING.md`
- `.agent/journal/2026-07-09/thermal-openfoam-interface-sampling.md`
- `imports/2026-07-09_thermal_openfoam_interface_sampling.json`
- `operational_notes/07-26/09/2026-07-09_thermal_openfoam_interface_sampling.md`
- `tools/extract/sample_physical_segment_interface_temperatures.py`
- `tools/extract/test_sample_physical_segment_interface_temperatures.py`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/**`
- `tmp/2026-07-09_thermal_openfoam_interface_sampling/**`

Read-only:

- Source Salt 2/3/4 mainline OpenFOAM case trees
- Existing reconstructed mirrors under `tmp/2026-06-30_claude_action_items/**`
- July 8 thermal boundary and mismatch packages
- Native solver outputs outside this task-local mirror

## Outputs

- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/sampling_plane_plan.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/sampling_targets.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/local_smoke_summary.json`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/local_smoke_existing_secmean_samples.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/job_completion_summary.json`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/scripts/run_thermal_openfoam_interface_sampling.sh`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/scripts/submit_overnight_thermal_sampling.sbatch`

## Sampling Plan

- Cases: Salt 2/3/4 Jin mainline.
- Retained times: Salt 2 `7915`, Salt 3 `7618`, Salt 4 `10000`.
- Planned planes: `16` per case, `48` total.
- Bracketed control volumes: `heater_interior`,
  `cooler_reducer_interior`, `lower_left_junction`, `lower_right_junction`,
  `upper_right_junction`, `upper_left_junction`,
  `test_section_lower_junction`, and `test_section_upper_junction`.
- Plane geometry source:
  `work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/**/mesh_stations.json`.

## Semantics Preserved

- The parser keeps signed mixing-cup temperature and dominant forward-flow bulk
  temperature as separate columns.
- Positive-normal and negative-normal directional bulk temperatures are kept
  separately.
- Backflow fraction is reported as the weaker directional flux divided by the
  dominant directional flux.
- `qr` is sampled only if a reconstructed `qr` field exists. Current generated
  rows are expected to report `absent_no_qr_output`.

## Smoke / Validation

- `python3 -m py_compile tools/extract/sample_physical_segment_interface_temperatures.py tools/extract/test_sample_physical_segment_interface_temperatures.py`
- `python3 -m unittest tools.extract.test_sample_physical_segment_interface_temperatures`
- `python3 tools/extract/sample_physical_segment_interface_temperatures.py build-openfoam-package`
- `bash work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/scripts/run_local_smoke_preflight.sh`
- `bash work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/scripts/run_thermal_openfoam_interface_sampling.sh preflight`
- `sacct -j 3287311 --format=JobID,JobName%20,State,ExitCode,Elapsed,AllocCPUS,NodeList%20`

Local smoke result: `5/5` existing reconstructed Salt 2 secmean parser rows
were OK; no OpenFOAM run was performed on the login shell.

## Submitted Job

- Job ID: `3287311`
- Name: `th_ofsamp`
- Submit host: `login3`
- Partition/account: `NuclearEnergy` / `ASC23046`
- Limit: `1` node, `1` task, `64` CPUs, `08:00:00`
- Initial state: `PD`, reason `Resources`
- Submit command:
  `ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch -t 08:00:00 work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/scripts/submit_overnight_thermal_sampling.sbatch"`

## Current State

Complete. Job `3287311` completed with `ExitCode=0:0` in `00:01:20`.

Final sampling result:

- Salt 2: `16/16` rows OK at `t=7915`
- Salt 3: `16/16` rows OK at `t=7618`
- Salt 4: `16/16` rows OK at `t=10000`
- Combined: `48/48` rows OK, `0` missing rows
- Radiation output terms: `absent_no_qr_output`

The first Slurm run emitted harmless `cp` warnings for missing `0/` directories
in the older reconstructed mirrors, then completed successfully using task-local
mirrors. The generator and current runner were updated so future runs fall back
to the source case `0/` directory without that warning.
