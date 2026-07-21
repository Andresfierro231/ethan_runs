# Salt Perturbation Quarantine and Corrected Relaunch

Date: `2026-07-04`

## Decision

The June 19/25 Salt Q perturbation runs are quarantined as invalid closure data.
Do not use them for friction-factor fits, HTC fits, closure-term regression,
Re-response curves, or 1D model validation.

They looked stationary because the intended perturbation was not reliably in the
restart fields read by `foamRun`. In audited cases, the decomposed
`processors64/<latest>/T` field remained nominal even when metadata/root files
advertised +/-Q. Some root `0/T` files also changed only one of the three lower
heater patches.

## Insulation

The inspected Jádyn Salt cases used baseline `insulated.h = 5.964`. Historical
`hiins`/`loins` labels should not be treated as validated insulation variants
for current analysis unless a later audit proves the live insulation boundary
condition actually changed.

`insulated.h` is a heat-transfer coefficient, not a resistance. It is also only
a summary/config value. The authoritative heat-transfer setup is the patchwise
OpenFOAM `T` boundary field:

- `rcExternalTemperature` layered wall patches carry `h`, `Ta`, `Tsur`,
  emissivity, `thicknessLayers`, material coefficients, and sometimes imposed
  heater `Q`.
- `externalTemperature` patches carry fixed heat-loss/source terms used by the
  cooler and nearby reducers.

Effective heat-transfer resistance is therefore patch-dependent: external
convection/radiation plus explicit conduction layers. Future insulation claims
must cite actual `0/T` and restart-field boundary values, not only
`case_config.yaml`.

## Replacement

Replacement campaign:
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`.

The replacement workflow patches:

- root `0/T`;
- copied `processors64/<latest>/T` immediately before `foamRun`;
- all three lower heater patches;
- the balanced upper cooling patches.

Admission rule: even corrected rows remain provisional until mdot moves from the
nominal baseline by the expected Q response and re-plateaus.

Restarting from a nominal continuation is acceptable and preferred for local Q
perturbations because it preserves the converged thermal inventory. The lesson
is not to avoid restarts; the lesson is to stage into a clean new directory and
audit the restart-time boundary field that `foamRun` actually reads.

Required future preflight:

- check `case_config.yaml`;
- check root `0/T`;
- check copied `processors64/<latest>/T`;
- check all intended patches, not only one heater patch;
- preserve collated `decomposedBlockData` framing when editing restart fields;
- require a launch-time `preflight_patch_audit_<job>.csv` before accepting a run
  as valid.
- Monday TODO: promote this into a reusable automated preflight checker that
  fails a case unless `case_config.yaml`, root `0/T`, and
  `processors64/<latest>/T` agree for every target thermal patch. The checker
  must validate all target patch counts, preserve/verify collated
  `decomposedBlockData` frames, and write a documented audit artifact.

## Current submissions

Current corrected jobs are listed in:
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv`.

Earlier attempts are documented and should not be interpreted as data:

- `3275388`-`3275391`: failed launcher bootstrap.
- `3275392`-`3275395`: canceled because comma-separated case arrays were split
  by Slurm export handling; one partial copied restart tree was removed.
- `3275400`-`3275403`: canceled because launch-time patching used a broken
  post-OpenFOAM `python` and the launcher did not enforce patcher failure before
  starting `foamRun`. The staged `runs/` tree was deleted and regenerated.
- `3275422`-`3275425`: canceled because the first launch-time patcher corrupted
  the collated `decomposedBlockData` restart `T` file by not preserving
  per-processor byte framing. The patcher now rewrites collated blocks
  frame-safely and was smoke-tested on a copied restart field.
- `3275433`-`3275436`: canceled because the staged roots omitted parent
  `dynamicCode/`, forcing fresh parallel coded-function compilation during
  launch. Staging now copies parent `dynamicCode/`.
- `3275448`-`3275451`: current corrected submission. At the last check, group 1
  had all four packed cases launched; groups 2 and 3 were also running; group 4
  was pending for resources.

Final closeout update: a later queue check showed all four corrected Salt Q
jobs `3275448`-`3275451` running, with visible `foamRun` steps active. Water
continuation `3265970` was still running, and dependent Water postprocess
`3275363` remained pending on `afterany:3265970`.

## Smoke checks

Local checks passed:

- launcher and submitter `bash -n`;
- patch/staging script `py_compile`;
- root patch audit for all 14 corrected cases;
- sampled restart-field smoke audit for all 14 corrected cases.

Next check: confirm each running job writes
`preflight_patch_audit_<job>.csv` and advances solver logs before any result is
treated as an admissible CFD perturbation.
