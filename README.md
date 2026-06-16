# ethan_runs

`ethan_runs/` is the local intake and preprocessing workspace for Ethan's
large high-fidelity CFD cases. It is not the canonical publication home for
cross-model comparison results.

## Role

- Stage or reference large local case folders without mutating native outputs.
- Build explicit import manifests and local provenance records.
- Extract inventory, quantities of interest, and first-pass validation inputs.
- Generate field-visualization artifacts through PyVista/VTK or ParaView
  `pvpython` when the local runtime supports them.
- Publish canonical comparison-ready artifacts into
  `../cfd-modeling-tools/cross_model_comparison`.

## Workflow

1. Make the source case reachable on the local machine.
2. If the source lives elsewhere, sync it into `staging/`.
3. Register the case into `registry/case_registry.csv`.
4. Build an import manifest in `imports/`.
5. Extract inventory and QoI tables into `work_products/`.
6. Prepare a render input under `staging/render_inputs/`.
7. Attempt PyVista/VTK or ParaView field figures into `figures_rendered/`.
8. Write a reusable Slurm render job into `staging/render_jobs/` when direct rendering skips.
9. Join the case against the canonical 1D reference contract.
10. Publish a campaign package into
   `../cfd-modeling-tools/cross_model_comparison`.

## Local-first intake rule

- Symlinks in `linked_cases/` are convenience handles only.
- Provenance lives in manifests, journals, checkpoints, and published reports.
- Remote paths are not treated as analysis-ready until staged locally.

## Milestone-one case

The initial scaffold targets
`/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar`
for `salt_test_2`.

## Primary entrypoints

- `python tools/intake/register_case.py --source-path <case-dir>`
- `python tools/intake/build_import_manifest.py --source-id <source-id>`
- `python tools/extract/extract_case_inventory.py --source-id <source-id>`
- `python tools/extract/extract_qoi_table.py --source-id <source-id>`
- `python tools/extract/prepare_render_input.py --source-id <source-id> --format auto`
- `python tools/extract/render_field_figures.py --source-id <source-id> --backend auto`
- `python tools/extract/write_render_job.py --source-id <source-id>`
- `python tools/publish/build_cross_model_join.py --source-id <source-id>`
- `python tools/publish/publish_cross_model_campaign.py --source-id <source-id>`
- `python tools/run_registered_pipeline.py --source-id <source-id>`

## Codex Batch Job Submission

Use `tools/analyze/submit_codex_board_queue_sbatch.sh` when you want to launch
the bounded Codex queue-resume harness on Slurm.

Requirements:

- Run the submission from a login node, not a compute node.
- Make sure `codex` and `sbatch` are both on `PATH`, or pass `--codex-bin`.
- Review the live queue state in `.agent/BOARD.md` first; by default the script
  asserts the expected bounded-slice board state before it submits anything.

Typical flow:

1. Dry run first:
   `bash tools/analyze/submit_codex_board_queue_sbatch.sh --dry-run`
2. Inspect the emitted job directory under `tmp/slurm_codex_board_jobs/`.
3. Submit for real:
   `bash tools/analyze/submit_codex_board_queue_sbatch.sh`
4. Monitor the job:
   `squeue -j <jobid>` and `sacct -j <jobid>`
5. Inspect the emitted logs after completion:
   `tmp/slurm_codex_board_jobs/<timestamp>_codex_ethan_queue_resume/`

Key emitted artifacts:

- `prompt.md`: exact bounded prompt sent to Codex
- `codex_ethan_queue_resume.sbatch`: generated Slurm script
- `board-snapshot.txt`: board snapshot captured at submit time
- `board-assertion.txt`: pre-submit assertion result
- `slurm-<jobid>.out` and `slurm-<jobid>.err`: scheduler stdout/stderr
- `codex-events.jsonl` and `codex-last-message.txt`: Codex execution logs

Important flags:

- `--dry-run`: emit prompt and sbatch script without submitting
- `--allow-stale-board`: bypass the default board-state assertion
- `--job-dir PATH`: force a specific output directory for emitted artifacts
- `--model MODEL`: override the default Codex model for the batch run

## Current status

- `val_salt_test_2_coarse_mesh_laminar` is registered, extracted, joined to the
  canonical 1D contract, and published.
- Validation metrics are derived from solver logs plus `postProcessing/` outputs.
- Decomposed-case rendering still requires a compatible runtime or a reconstructed
  staging copy, but the workspace now emits a reusable Slurm render job.
- Only one accessible Ethan case was found under the readable project scratch tree
  on 2026-05-29, so multi-case execution remains externally blocked by source
  availability rather than missing workflow code.
