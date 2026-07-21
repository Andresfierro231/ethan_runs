# Thermal OpenFOAM Interface Sampling

Date: `2026-07-09`
Task: `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`
Role: Coordinator / Implementer / Tester / Writer

## Prompt

The user asked to claim the thermal OpenFOAM interface sampling TODO, run local
smokes, and submit a bounded overnight compute-node sampling job that brackets
heater, cooler/reducer, and junction control volumes.

## Work Performed

Extended `tools/extract/sample_physical_segment_interface_temperatures.py` so it
can now:

- generate mesh-derived OpenFOAM cut-plane plans for Salt 2/3/4;
- write an OpenFOAM `surfaces` controlDict for task-local reconstructed mirrors;
- parse raw plane dumps into signed mixing-cup, positive-normal,
  negative-normal, and dominant-forward bulk temperatures;
- preserve backflow fractions;
- sample `qr` only when a reconstructed `qr` field exists;
- generate login-safe smoke and Slurm submission scripts.

Updated tests in:

- `tools/extract/test_sample_physical_segment_interface_temperatures.py`

Generated package:

- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/**`

## Plane Plan

The generated package plans `48` total planes: `16` per Salt case. These include
heater-interior brackets, cooler/reducer-interior brackets, and junction
bracketing faces for lower-left, lower-right, upper-right, upper-left, and
test-section lower/upper junctions.

The geometry source is the existing mesh-centerline package, not schematic probe
coordinates.

## Smoke And Preflight

Validation completed:

- Python syntax check passed.
- Focused unittest suite passed: `6/6`.
- Package generator completed.
- Login-safe smoke parsed `5/5` existing Salt 2 reconstructed secmean rows.
- OF13 environment preflight passed.
- Compute-node runner preflight passed without mutating existing reconstructed
  mirrors.

No heavy OpenFOAM command was run on the login shell.

## Submission

Direct `sbatch` from the current shell reported that `sbatch` is unavailable on
compute nodes. The job was then submitted from `login3`.

Submitted:

- Job ID: `3287311`
- Job name: `th_ofsamp`
- Partition/account: `NuclearEnergy` / `ASC23046`
- Limit: `08:00:00`
- Initial state: pending, reason `Resources`
- Final state: `COMPLETED`, `ExitCode=0:0`, elapsed `00:01:20`

Final parsed outputs:

- Salt 2: `16/16` rows OK
- Salt 3: `16/16` rows OK
- Salt 4: `16/16` rows OK
- Combined: `48/48` rows OK
- Radiation output terms: `absent_no_qr_output`

After completion, the parser's raw-column resolver was corrected for the new
`fields (U T rho p_rgh)` controlDict order and all generated OpenFOAM plane
files were re-parsed without rerunning OpenFOAM. Focused tests now cover both
supported raw-column orders.

## Interpretation Boundary

This turn completes the OpenFOAM sampling job and prepares parsed interface
samples. It does not yet refresh the observation table or promote thermal rows
to fit evidence. That should happen in `TODO-OBSERVATION-TABLE-THERMAL-REFRESH`
after these rows are reviewed.
