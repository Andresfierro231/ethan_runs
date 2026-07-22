# Salt2 Fine Reconstructed-T Repair Plan And Sbatch

Task: `AGENT-291`
Date: `2026-07-13`

## Overarching Idea

Thermal UA/HTC/Nu is blocked until the reconstructed temperature field is
shown to be scientifically usable on the refined mesh family. AGENT-265
diagnosed the original OpenFOAM failure as corrupted serial reconstructed `T`,
not as proven native decomposed-source corruption. AGENT-267 then repaired the
medium Salt2 refined path at smoke level by using a split reconstruction:

1. stage a task-local mirror without mutating native solver outputs,
2. reconstruct `T` alone,
3. scan reconstructed `T` for whole-file nonfinite tokens and Kelvin-valued
   `internalField`/boundary `value` lists,
4. reconstruct non-`T` fields into the same stage,
5. rescan `T`,
6. remove staged `system/functions` before sampling,
7. run section temperature sampling,
8. use OF13 for segment thermal postprocessing before parsing HTC/UA/Nu.

The next scientific step is to run the same sequence on the Salt2 fine refined
case. This is required before any mesh-family thermal GCI or closure admission
can interpret medium/fine UA, HTC, or Nu.

## Runtime Estimate

Expected runtime: `3-6 hours`.

Basis:

- Medium AGENT-267 smoke completed the full reconstruction plus scan plus
  section/segment thermal workflow interactively at manageable scale.
- The fine reconstructed `T` payload is approximately three times the medium
  payload, and the workflow performs two reconstruction phases plus two full
  `T` scans before sampling.
- OpenFOAM postprocessing also has to read the larger fine reconstructed field
  and can fail slowly if the field dictionary or function-object path is wrong.

Because the conservative estimate exceeds the user-provided `2 hour` threshold,
the fine run should be submitted through Slurm, not run on a login node.

## Submitted Workflow

Script:

- `scripts/run_salt2_fine_reconstructed_t_repair.sbatch`

Submitted Slurm job: `3293768`

Initial state: `PENDING` for `(Resources)` with `12:00:00` walltime.

Latest pre-handoff state: `RUNNING` on `c318-016`.

Command executed by the batch script:

```bash
python3.11 tools/analyze/build_reconstructed_t_repair_trial.py \
  --fine-only \
  --task-id AGENT-291 \
  --package-dir work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output \
  --reconstruct-timeout-s 14400 \
  --foam-timeout-s 14400
```

Output package:

- `repair_trial_output/summary.json`
- `repair_trial_output/outputs/reconstruction_trials.csv`
- `repair_trial_output/outputs/fine/section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `repair_trial_output/outputs/fine/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`
- `repair_trial_output/logs/`
- `repair_trial_output/recon/fine_cwd_controlDict_collated_split_full/`

## Scientific Gates

The fine run can be treated as a repair success only if all of these are true:

- final reconstructed fine `399/T` exists;
- whole-file numeric scalar scan has `0` nonfinite tokens;
- temperature-list scan has `0` entries outside `250..1500 K`;
- parsed temperature-list counts match OpenFOAM list headers;
- section temperature sampling returns all expected stations without
  `FOAM FATAL`;
- segment thermal extraction returns at least one finite computed row.

Even if these gates pass, the generated UA/HTC/Nu values remain repair-trial
evidence. They are not closure-fit admissions until a follow-up review checks
sign conventions, heat-balance consistency, downcomer/right-leg policy, and
medium/fine/coarse mesh-family reconciliation.

## Continuity Notes

Do not overwrite the AGENT-267 medium package. AGENT-291 writes the fine run
under this package through `--package-dir`.

Downstream order after job exit:

1. harvest Slurm state and `repair_trial_output/summary.json`;
2. if clean, rerun or extend the Salt2 Closure-QOI mesh/GCI package using the
   fine thermal output;
3. keep downcomer thermal blocked unless a separate task changes the
   right-leg/downcomer policy;
4. document any partial failure as a field-quality blocker, not as a closure
   result.
