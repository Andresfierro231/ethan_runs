# Salt Test 2 CFD Setup Dossier

Date: `2026-06-01`
Case: `val_salt_test_2_coarse_mesh_laminar`
Purpose: record the imported CFD setup in comparison-grade detail for later 1D-to-CFD mapping and continuation planning.

## Executive Status

- The source case is a decomposed full 3D OpenFOAM loop case, not an axisymmetric wedge surrogate.
- The run is not yet convergence-quality by the case's own stop rule.
- A writable continuation copy is staged under `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation`.
- Direct submission of the continuation is currently blocked by a missing readable runtime library: `libRCWallBC.so`.
- The prepared submission wrapper is `jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_openfoam13_template.sbatch`.

## Provenance

- Imported source root: `/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar`
- Source run path from solver log: `/scratch/09807/ethanrozak/foam_vv/runs/jin_viscosity_emissivity_testing_20260502_194913/cases/val_salt_test_2_coarse_mesh_laminar`
- Original solver executable from log: `/work/09807/ethanrozak/ls6/OpenFOAM_V13/OpenFOAM-13/platforms/linux64GccDPInt32Opt/bin/foamRun -parallel`
- Original job id: `3139458`
- Source run start: `2026-05-02 14:58:06`
- Source run termination: `2026-05-05 17:06:26`, `signal 15 (Terminated)`

## Geometry And Mesh

This case is organized as a loop with four named pipe legs plus connecting junctions.
Patch naming shows the main sections:
- lower leg: `pipeleg_lower_*`
- right leg: `pipeleg_right_*`
- upper leg: `pipeleg_upper_*`
- left leg: `pipeleg_left_*`
- junctions: `junction_*` and `ncc_*`

Concrete mesh facts from `constant/polyMesh`:
- estimated cell count from `cellProc`: `2,166,996`
- points: `2,268,735`
- faces: `6,598,756`
- internal faces: `6,403,220`
- boundary patches: `109`
- domain bounding box in meters:
  - x: `[-0.04493875, 0.9324581072]`
  - y: `[-0.3137833472, 1.11947325]`
  - z: `[-0.0127, 0.0127]`
- decomposition: `64` subdomains via `scotch`

Interpretation:
- the nonzero `z` thickness confirms this is a full 3D geometry with front/back extent, not a 2D wedge.
- the left test-section wall patch is `pipeleg_left_04_test_section`.
- the largest named wall sections include `pipeleg_left_01_upper`, `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, `pipeleg_right_03_upper`, `pipeleg_left_07_lower`, and `pipeleg_upper_05_cooler`.

## Solver And Numerics

Files used:
- `system/controlDict`
- `system/fvSolution`
- `system/fvSchemes`
- `system/decomposeParDict`

Active runtime settings:
- application: `foamRun`
- solver region: `fluid`
- restart mode: `startFrom latestTime`
- stop rule at file level: `stopAt endTime`, `endTime 10000`
- initial nominal `deltaT`: `0.01`
- adaptive stepping: `yes`
- `maxCo = 1`, `maxDeltaT = 1.0`
- write control: `adjustableRunTime`
- write interval: `1`
- purge writes: `5`
- file handler: `collated`
- processor decomposition: `64`, method `scotch`

Linear solvers and outer loop:
- `p_rgh`: `GAMG`
- `(U|h|...)`: `PBiCGStab` with `DILU`
- PIMPLE: `1` outer corrector, `2` correctors, `1` non-orthogonal corrector
- relaxation factors are effectively `1.0`

## Physics And Modeling Assumptions

Files used:
- `constant/physicalProperties`
- `constant/momentumTransport`
- `constant/thermophysicalTransport`
- `constant/g`
- `case_config.yaml`

Model form:
- OpenFOAM version from log: `13`
- single-region variable-property thermal-fluid model
- thermodynamics: `heRhoThermo / pureMixture / icoTabulated / hPolynomial / icoPolynomial / sensibleEnthalpy`
- momentum model: `laminar`
- heat transport model: `Fourier`
- gravity vector: `(0, -9.81, 0)` m/s^2

Fluid property setup for HITEC salt:
- `Cp = 1423.47 J/kg-K` constant from `CpCoeffs<8>`
- density law from `rhoCoeffs<8> = (2293.6, -0.7497, ...)`
- dynamic viscosity is tabulated in `constant/physicalProperties`, generated from the `expInvT` law recorded in `case_config.yaml`
- thermal conductivity is tabulated in `constant/physicalProperties`, generated from the quadratic law recorded in `case_config.yaml`
- molar mass: `84.25`

High-level operating point from `case_config.yaml`:
- fluid: `hitec_salt`
- turbulence model: `laminar`
- heater power: `265.7 W`
- cooling power: `56.34 W`
- initial temperature: `451.5 K`
- geometry scale factor: `0.001`

## Initial Conditions

Files used:
- `0/U`
- `0/T`
- `0/p_rgh`

Initial fields:
- `U internalField = uniform (0 0 0)`
- `T internalField = uniform 451.5`
- `p_rgh internalField = uniform 0`

Boundary-wide defaults:
- velocity: default `noSlip` on all walls, with `slip` only on the named NCC neighbour patches
- pressure: `fixedFluxPressure` everywhere

## Thermal Boundary Conditions

The thermal model is patch-specific and is the main thing to preserve for comparison work.
Most exterior wall segments use the custom boundary condition `rcExternalTemperature`, which is why the case requires `libRCWallBC.so` at runtime.

Common features across many `rcExternalTemperature` patches:
- ambient air temperature `Ta = 299.19 K`
- surrounding radiative temperature `Tsur = 299.19 K`
- emissivity `0.95`
- explicit multilayer wall conduction via `thicknessLayers`, `kappaLayerCoeffs`, `rhoLayerCoeffs`, and `CpLayerCoeffs`

Representative segment classes:
- junction exterior segments:
  - example `junction_lower_left`
  - `h = 4.1380 W/m^2-K`
  - `internalRadius = 0.011049 m`
  - steel plus insulation layers: thicknesses `(0.006096001, 0.04191) m`
- powered test section:
  - patch `pipeleg_left_04_test_section`
  - boundary type `rcExternalTemperature`
  - imposed `Q = +37.0 W`
  - `powerLayer = 0`
  - `h = 7.4822 W/m^2-K`
  - quartz wall layer thickness `0.0022 m`
  - quartz properties from the patch coefficients: `k = 1.4 W/m-K`, `rho = 2214.39 kg/m^3`, `Cp = 740 J/kg-K`
- cooler section:
  - patch `pipeleg_upper_05_cooler`
  - boundary type `externalTemperature`
  - imposed `Q = -104.0735 W`
  - comment says this combines air-side plus jacket-to-ambient loss
- upper reducers around the cooler:
  - `pipeleg_upper_04_reducer` and `pipeleg_upper_06_reducer`
  - each uses `externalTemperature` with `Q = -16.1386 W`
- stub fins and caps:
  - multiple patches use `externalTemperature` with calibrated fixed heat-loss surrogates
  - examples include comments such as `Q_loss = 4.959 W @ T_init` and corresponding calibrated `h_cal`

Important interpretation note:
- this case is not using one uniform external heat-transfer coefficient globally.
- instead, it mixes segment-wise `rcExternalTemperature` wall models, fixed heat-loss surrogates, and an explicitly powered quartz test section.

### 2026-07-04 clarification: insulation and restart BC audits

Do not interpret `case_config.yaml` values such as `insulated.h` as the complete
thermal resistance of the CFD model. `insulated.h` is a heat-transfer
coefficient summary for an insulation-related patch category. The actual thermal
resistance is patchwise and combines:

- external convection/radiation terms in `rcExternalTemperature`;
- explicit layer conduction through `thicknessLayers` and material coefficient
  lists;
- fixed-source/sink `externalTemperature` terms for cooler and reducer patches;
- imposed heater `Q` on powered `rcExternalTemperature` sections.

For any continuation or perturbation restart, the authoritative boundary field
is not only root `0/T`. `foamRun` restarts from the decomposed latest-time field
under `processors64/<latest>/T`. A valid perturbation workflow must audit
`case_config.yaml`, root `0/T`, and `processors64/<latest>/T` for every intended
thermal patch before launch.

The July 4 Salt perturbation quarantine was caused by violating this contract:
metadata/root files advertised Q perturbations, but audited decomposed restart
fields still carried nominal heater `Q` values. Future smoke tests must reject
that condition before any solver job is submitted.

## Measurement, Monitoring, And Comparison Hooks

Files used:
- `system/functions`
- `postProcessing/*`

Temperature probes:
- six centerline bulk probes `TP1` through `TP6`
- coordinates are recorded in `jadyn_runs/salt2/2026-06-01_continuation_candidate/tp_tw_probe_locations.csv`
- examples:
  - `TP1 = (0.887519, 0.704090, 0.0) m`
  - `TP2 = (0.887519, -0.245426, 0.0) m`
  - `TP3 = (0, 0, 0) m`
  - `TP6 = (0, 0.949515, 0) m`

Wall probes:
- `44` wall probes total
- organized as `TW1` through `TW11`
- each station has four azimuthal positions: `_back`, `_bottom`, `_front`, `_top`
- these are valuable for later 1D comparison because they let you distinguish bulk-fluid temperature targets from wall-skin temperatures.

PIV-matching diagnostic:
- a dedicated PIV slab cell zone is volume-averaged
- slab box in meters:
  - `(-0.001125, 0.356140, -0.010500)` to `(0.001125, 0.542140, 0.010500)`
- the case writes both vector `U` and `magU` for this slab

Mass-flow diagnostics:
- `mdot_pipeleg_right_02_middle`
- `mdot_pipeleg_lower_05_straight`
- `mdot_pipeleg_upper_05_cooler`
- `mdot_pipeleg_left_04_test_section`

Velocity profiles:
- line samples at `Y/H = 0.25`, `0.50`, and `0.75`
- sampled in both `X` and `Z` directions across the test-section area

## Convergence Logic

The case has its own coded function-object stop rule in `system/functions`.
That rule is more authoritative than a simple visual read of the final probe values.

Actual stop-rule logic:
- check interval: every `100` iterations
- minimum iteration count before testing: `500`
- window size: `100`
- relative tolerance: `1e-4`
- residual gates:
  - `p_rgh <= 1e-6`
  - `U <= 1e-5`
  - `h <= 1e-5`

The QoIs used by the coded convergence monitor are whole-domain volume-weighted:
- `Tmean`
- `Tsigma`
- `Umean = volume-weighted mean of |U|`

This matters for later comparison: the solver is not stopping on TP/TW probes directly. It is stopping on domain-wide thermal and velocity statistics.

## Current Run State And Runtime Estimate

Observed source-run endpoint:
- latest physical time in postprocessing: about `1724.714285714 s`
- latest convergence-monitor iteration from log: `296000`
- total observed wall clock in log: about `266900 s` or `74.1 h`

Throughput estimates from the source run:
- about `23.3 simulated seconds per wall-clock hour`
- about `3990` convergence-monitor iterations per wall-clock hour

Current coded stop-rule status at the last logged monitor check (`iter=296000`):
- `dTmean = 2.0235e-05` and already well below tolerance
- `dUmean = 8.13e-05` and currently below tolerance
- `dTsigma = 7.738e-03` and still far above `1e-4`

Interpretation:
- the case is mainly failing convergence on temperature-spread drift, not mean temperature drift.
- this is consistent with the postprocessing result that heat-loss-related quantities are still moving.

Walltime estimate:
- if the last-segment `dTsigma` decay is extrapolated exponentially, the case would need roughly `7.9` additional days of wall clock to bring `dTsigma` down to `1e-4`.
- at the same observed throughput, reaching the file-level `endTime = 10000` would take about `14.8` additional days from the current state if no earlier stop occurs.

Practical recommendation:
- do not expect one more short continuation to finish this case.
- a single additional `120 h` run is unlikely to be enough.
- the defensible plan is at least two restartable continuation chunks, each on the order of `96-120 h`, unless the partition allows a longer single job and you want to accept the larger failure/requeue risk.

## Submission Pattern Learned From `andres_2d`

The `andres_2d_axisymmetric_testing_heat_loss` repo is useful for scheduler pattern, not for physics parity.
Useful conventions adopted from that repo:
- submit from a login node with `sbatch`
- use tracked job scripts with explicit `#SBATCH -p NuclearEnergy` and `#SBATCH -A ASC23046`
- preserve restartability instead of forcing a fresh run
- keep run-specific notes and logs adjacent to the staged continuation folder

Important difference:
- `andres_2d` cases are wedge-axisymmetric steady cases launched through `automation/run_case.py`
- this `salt_test_2` case is a decomposed full 3D native OpenFOAM case run with `foamRun -parallel`
- so the continuation should preserve the native `srun foamRun -parallel` path, not be migrated into the wedge automation itself

## Submission Blocker

I retried this specifically through the `andres_2d` workflow runtime. On a compute node, the configured container path `/corral-secure/utexas/ASC23046/Images/openfoam-default_latest.sif` starts successfully and `/openfoam/bash.rc` exists, but it resolves to OpenFOAM `2512` and does not expose `rcExternalTemperature` or `libRCWallBC.so` in the container OpenFOAM tree.

I therefore did not submit the longer continuation job yet because the case still references:
- `libs ("libRCWallBC.so")`

and a readable copy of `libRCWallBC.so` was not found in your accessible scratch/home trees nor in the validated `andres_2d` container runtime.

That means:
- Slurm setup is ready
- case staging is ready
- runtime environment is not yet complete enough to launch safely under your account without changing the boundary-condition model

Needed to unblock submission:
1. a readable OpenFOAM 13 bashrc path for the continuation job
2. a readable directory containing `libRCWallBC.so`

Once a readable `libRCWallBC.so` path is known, the prepared container-based wrapper `run_continuation_andres2d_container_template.sbatch` is ready to submit through the `andres_2d` runtime pattern.
