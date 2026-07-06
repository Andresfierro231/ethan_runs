# Salt Jin Optimum Insulation Wave

## Purpose

This subcampaign stages and submits one packed 256-rank node that runs the
four Salt Jin base cases at the per-case effective insulation thicknesses
reported in `reports/2026-06-19_ethan_insulation_optimizer_package/`.

The wave is intentionally narrow:

- no heater-power mutation;
- no cooler-side mutation;
- one Salt 1 / 2 / 3 / 4 Jin continuation each;
- one 256-core node with four independent 64-rank OpenFOAM steps.

## Scientific scope

- The target thicknesses come from the read-only effective wall-loss solver,
  not from a fully coupled redesigned closure model.
- The run objective is therefore comparative CFD evidence at the solver-suggested
  thicknesses, not proof that the inferred effective thickness is uniquely
  physical.
- The Jin Salt cases currently use a uniform outer insulation layer across the
  whole loop. This wave preserves that pattern and only changes the single
  outer layer value in `0/T` for each case.

## Packed-node rationale

- Each Salt case decomposes to `64` MPI ranks.
- The current LS6 nodes expose `256` physical CPUs, so four cases can fit on
  one node without CPU oversubscription.
- The packed launcher uses four concurrent `srun` steps with:
  - `--exclusive`
  - `--exact`
  - `--cpu-bind=cores`
  - `--distribution=block:block`
- This keeps each case on a disjoint 64-core slice of the same node instead of
  paying for four half-empty nodes.

## Cases

| Case key | Parent source | Stable parent latest time [s] | Target thickness [in] | Target thickness [m] |
| --- | --- | --- | --- | --- |
| `salt1_jin_optins` | `jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation` | `3617.6625` | `2.4000` | `0.060960000000` |
| `salt2_jin_optins` | `staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_2_jin_coarse_mesh` | `2431` | `1.7291` | `0.043919140000` |
| `salt3_jin_optins` | `staging/modern_runs/2026-06-01_full_extractable_batch/salt/viscosity_screening_salt_test_3_jin_coarse_mesh` | `2514` | `1.6696` | `0.042407840000` |
| `salt4_jin_optins` | `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation` | `5776` | `1.8277` | `0.046423580000` |

## June 22 runtime refresh

### Diagnosed June 19 failure

- initial packed job:
  - `3246927` `ethan_salt_optpack`
- state:
  - failed after `00:36:33`
- failure mode:
  - the compute-node self-staging launcher depended on `rg`, which was not
    available on the runtime path
- preserved evidence:
  - `failed_stage_preserved/2026-06-19_job3246927_selfstage_failed_rg_missing`

### Repair actions

- replaced `rg` checks with `grep -Eq` in
  `scripts/stage_optimum_insulation_cases.sh` and
  `scripts/run_packed_optimum_insulation_wave_selfstage.sbatch`
- kept the original self-staging launcher for provenance, but used the simpler
  local pre-staged launcher for the repaired submission because the four local
  staged case roots already existed under `runs/`
- resubmitted the repaired packed wave on `2026-06-22` as:
  - `3250526` `ethan_salt_optpack`
- after the capped-window stop and continuation repack, resubmitted again on
  `2026-06-22` as:
  - `3250784` `ethan_salt_optpack`

### Current queue state after the June 22 heat-balance gate

- the repacked optimum job `3250784` was canceled on `2026-06-22`
- reason:
  - the insulation-only wave has no defensible `< 2 W` 3D reference-state
    residual guarantee under the current fixed-`Q` cooling contract
  - changing insulation without a matched 3D ambient-loss predictor leaves no
    rigorous way to promise `Q_in - Q_lost ≈ 0` before the run starts
- result:
  - the wave is now out of queue
  - the staged roots remain preserved for later reinterpretation or rebuild
  - any future insulation-only relaunch must first add a defensible 3D
    ambient-loss or residual-solve contract rather than relying on the
    measured-state wall-loss optimizer alone

## Guardrails

- Do not stage from the currently running June 18 continuation roots. Copying a
  live case risks a partial tree or an inconsistent restart snapshot.
- The earlier June 19 Salt 4 child failure came from an incomplete staged copy
  that was missing `system/controlDict`; the staging and continuation launch
  paths now reject that before solver startup.
- The repaired June 22 pending job `3250526` was later canceled during the
  capped-window stop, and the repacked follow-on `3250784` was then canceled
  again by the stricter heat-balance gate.

## Reproduction

- manifest: `campaign_manifest.csv`
- staging script: `scripts/stage_optimum_insulation_cases.sh`
- packed sbatch launcher: `scripts/run_packed_optimum_insulation_wave.sbatch`
- self-staging packed sbatch launcher:
  `scripts/run_packed_optimum_insulation_wave_selfstage.sbatch`

The self-staging launcher exists as a preserved fallback path, but the repaired
June 22 submission had used the already staged case roots under:

- `runs/salt1_jin_optins/`
- `runs/salt2_jin_optins/`
- `runs/salt3_jin_optins/`
- `runs/salt4_jin_optins/`
