# Journal: Staged Closure-QOI / Pressure sbatch

Date: 2026-07-15
Task: AGENT-440

## Work Performed

Created a new AGENT-440 board row to avoid overlapping active AGENT-438 and
AGENT-439 scopes. Built a package that follows the completed AGENT-409 staged
copy pattern but writes into a separate AGENT-440 scratch tree.

The generated runner samples `U`, `p`, `p_rgh`, and `rho` on the lower and
upper test-section tap planes for Salt2/Salt3/Salt4 coarse mainline cases. It
reports both pressure-drop signs and explicitly leaves the rows diagnostic.

## Local Validation

Confirmed locally before submission:

- package build succeeded;
- Python files compiled;
- generated shell scripts passed `bash -n`;
- preflight-only runner verified all three source cases, processor time
  directories, `constant/system/0`, and the OF13 environment script;
- focused package tests passed.

The local preflight intentionally did not run heavy OpenFOAM on the current
compute/login shell. Heavy postprocessing is in the submitted Slurm job.

## Submission

Direct `sbatch` from `c318-008` was rejected because sbatch is not available on
compute nodes. Submission through `login3.ls6.tacc.utexas.edu` first failed
because the account was unspecified. Added `#SBATCH -A ASC23046`, revalidated,
and resubmitted successfully.

Slurm job:

- `3297845` / `cqp_stage`
- partition/account: `NuclearEnergy` / `ASC23046`
- final checked state: `COMPLETED`, exit code `0:0`, elapsed `00:06:00`, node `c318-012`
- stdout: `work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch/logs/slurm-3297845.out`
- stderr: `work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch/logs/slurm-3297845.err`

## Harvest

After the job completed, refreshed the supported harvest with:

```bash
python3.11 tools/analyze/build_staged_closure_qoi_pressure_sbatch.py --harvest --record-job-id 3297845
```

The authoritative parsed table is
`work_products/2026-07/2026-07-15/2026-07-15_staged_closure_qoi_pressure_sbatch/raw_pressure_two_tap_harvest.csv`.
It contains three diagnostic rows for `salt2_mainline`, `salt3_mainline`, and
`salt4_mainline`. The submitted runner wrote surfaces under
`agent440ClosurePressureSurfaces`; the harvest script now accepts that actual
submitted function-object name as well as the prepared fallback name
`agent440RawPressureSurfaces`.

Do not promote rows beyond diagnostic until pressure definition, tap
orientation, straight-loss subtraction, recirculation, and mesh/GCI gates are
explicitly admitted.
