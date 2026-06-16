#!/bin/bash
#SBATCH -J modern_stage1
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/slurm/stage_first_batch_%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/slurm/stage_first_batch_%j.err
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 06:00:00

set -euo pipefail
bash /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/scripts/stage_first_batch.sh
