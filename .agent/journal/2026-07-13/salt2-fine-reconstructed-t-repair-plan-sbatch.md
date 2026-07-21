# Salt2 Fine Reconstructed-T Repair Plan And Sbatch

Task: `AGENT-291`
Date: `2026-07-13`

## Context Read

I read the active coordination files and the relevant thermal blocker chain:

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `.agent/journal/2026-07-13/reconstructed-t-repair-trial.md`
- `.agent/journal/2026-07-13/salt2-closure-qoi-mesh-gci.md`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/summary.json`

## Observed

AGENT-267 showed the medium Salt2 refined reconstructed-`T` failure is
repairable with a split reconstruction and strict scan gates. AGENT-284 then
kept thermal Closure-QOI GCI blocked because fine thermal extraction is still
missing. Therefore the next step is a fine-only compute run, not a new
interpretive closure claim.

## Plan

1. Reuse the AGENT-267 split reconstruction method selected on medium:
   `cwd_controlDict_collated`.
2. Stage the fine case under AGENT-291 work products and leave native solver
   outputs read-only.
3. Reconstruct fine `T` alone at time `399`.
4. Scan final fine `399/T` for nonfinite tokens and Kelvin-valued list sanity.
5. Reconstruct non-`T` fields into the same staged case.
6. Rescan `T` after non-`T` reconstruction.
7. Run section temperature sampling.
8. Run segment thermal sampling with the OF13 fallback path.
9. Admit no closure result until the output is harvested and reviewed.

## Runtime Estimate

The fine case is expected to run `3-6 hours`. The estimate is intentionally
conservative because fine reconstructed fields are about three times the medium
payload, the workflow scans the field twice, and postprocessing has to read the
larger field dictionaries. Since this exceeds the requested `2 hour` threshold,
the run belongs in Slurm.

## Implementation

Focused script changes:

- `tools/analyze/build_reconstructed_t_repair_trial.py`
  - added `--fine-only`;
  - added `--package-dir`;
  - added `--task-id`;
  - added `--reconstruct-timeout-s`;
  - added `--foam-timeout-s`;
  - kept existing scan and sampling gates intact.

Sbatch package:

- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/scripts/run_salt2_fine_reconstructed_t_repair.sbatch`

## Validation

- `python3.11 -m py_compile tools/analyze/build_reconstructed_t_repair_trial.py`
- `bash -n work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/scripts/run_salt2_fine_reconstructed_t_repair.sbatch`
- `python3.11 -m json.tool imports/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch.json`

## Submission

Direct `sbatch` from the current compute-node shell was refused with:

```text
sbatch not available on compute nodes. Use a login node.
```

The same prepared script was then submitted from `login3`:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/scripts/run_salt2_fine_reconstructed_t_repair.sbatch"
```

Submitted Slurm job: `3293768`.

Initial scheduler snapshot:

```text
3293768 s2_fine_Tfix PENDING 0:00 12:00:00 1 (Resources)
```

Subsequent scheduler snapshot before handoff:

```text
3293768 s2_fine_Tfix RUNNING 1:03 12:00:00 1 c318-016
```

## Next Harvest

After the job exits, harvest:

- `sacct -j 3293768 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList%30`
- `repair_trial_output/summary.json`
- `repair_trial_output/outputs/reconstruction_trials.csv`
- fine section and segment CSVs if gates pass
- Slurm stdout/stderr and `logs/fine_repair_<jobid>.log`

Only then should a follow-up task update the Salt2 Closure-QOI mesh/GCI package
or thermal admission interpretation.

## Terminal Harvest

The job reached terminal state:

```text
3293768      s2_fine_T+  COMPLETED      0:0   00:22:33        c318-016
3293768.bat+      batch  COMPLETED      0:0   00:22:33        c318-016
3293768.0    python3.11  COMPLETED      0:0   00:22:32        c318-016
```

Harvested fine repair output:

- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/summary.json`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/outputs/fine/segment_htc_uaprime_viscosity_screening_salt_test_2_jin_coarse_mesh.csv`

The fine smoke passed clean reconstructed `T`, section temperature sampling,
and segment thermal extraction. The subsequent thermal mesh gate is documented
in `.agent/journal/2026-07-13/thermal-mesh-gate.md`.
