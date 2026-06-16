# Staging Override

Read this after the repo-root `AGENTS.md` when working anywhere under
`staging/`.

## Scope

`staging/` contains local staged case copies, render inputs, reconstructed
latest-time mirrors, and Slurm job scripts for rendering or extraction support.

## Local rules

- Assume staged material may be expensive to recreate. Do not clean or rewrite
  broadly.
- Read the nearest status JSON, sbatch script, or render-input status file
  before changing a staging subtree.
- Prefer creating new dated status artifacts or job scripts rather than
  overwriting ambiguous older ones.
- Reconstruction-first rendering is the trusted pattern here. Avoid reviving
  direct-reader shortcuts unless the task is explicitly about validating them.
- Do not submit long or expensive jobs from a login node; prepare scripts and
  leave execution to Slurm or approved compute-node workflows.
- If a change affects provenance or expected outputs, record the associated
  import manifest or journal entry in the same task.

## Common subareas

- `render_inputs/`: case-specific readiness and reconstruction status
- `render_jobs/`: dated Slurm wrappers for smoke tests and full render batches
- `modern_runs/`: local staged copies of the campaign intake batch
