#!/bin/bash
set -euo pipefail

cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
jin_job=$(sbatch --parsable jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch)
kirst_job=$(sbatch --parsable jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/run_continuation_openfoam13.sbatch)
printf 'salt1_jin_job=%s
' "$jin_job"
printf 'salt1_kirst_job=%s
' "$kirst_job"
