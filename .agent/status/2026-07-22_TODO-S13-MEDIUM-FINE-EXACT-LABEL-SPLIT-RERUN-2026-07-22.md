---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_exact_label_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/mesh_gci_unlock_gate.csv
tags: [status, s13, medium-fine, exact-label, split-rerun]
related:
  - .agent/journal/2026-07-22/s13-medium-fine-exact-label-split-rerun.md
  - imports/2026-07-22_s13_medium_fine_exact_label_split_rerun.json
task: TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-S13-MEDIUM-FINE-EXACT-LABEL-SPLIT-RERUN-2026-07-22

## Objective

After the Salt2/medium smoke passed, run the repaired sampler as six isolated
case/mesh jobs with unique output paths, aggregate completed exact-label QOI
rows, and report whether mesh/GCI disposition is unlocked.

## Outcome

Complete. Slurm array `3311146[0-5]` completed successfully:

- `3311146_0`: Salt2 medium, completed `0:0`
- `3311146_1`: Salt2 fine, completed `0:0`
- `3311146_2`: Salt3 medium, completed `0:0`
- `3311146_3`: Salt3 fine, completed `0:0`
- `3311146_4`: Salt4 medium, completed `0:0`
- `3311146_5`: Salt4 fine, completed `0:0`

Aggregate decision:
`split_exact_label_rows_complete_mesh_gci_disposition_unlocked_no_admission`.

Key counts:

- successful case/mesh pairs: `6/6`
- aggregated exact-label QOI rows: `72`
- aggregated terminal-window reduction rows: `18`
- sampling error rows in successful outputs: `0`
- mesh/GCI disposition unlocked: `true`
- mesh/GCI disposition run here: `false`
- production harvest/admission/coefficient admission: `false`

Duplicate array `3311175` was canceled after canonical array `3311146` was
found running. Its `split_runs/` output is partial/noncanonical and must not be
used for mesh/GCI, production harvest, or admission evidence.

## Changes Made

- Added split Slurm array wrapper:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/run_split_exact_label_sampler.sbatch`
- Added aggregation script:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregate_split_outputs.py`
- Generated per-case/per-mesh outputs under `outputs/`.
- Generated aggregate CSV/JSON gate files in the split rerun package.
- Wrote this status, matching journal, import manifest, README/RUNNING, and updated own board row.
- Updated handoff records to mark duplicate `3311175`/`split_runs/` as
  noncanonical.

## Validation

- `bash -n work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/run_split_exact_label_sampler.sbatch`:
  passed.
- `python3.11 -m pytest tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`:
  passed, `9` tests.
- `python3.11 work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregate_split_outputs.py`:
  passed; aggregate decision above.
- `python3.11 -m py_compile work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregate_split_outputs.py`:
  passed.
- `python3 tools/docs/build_repo_index.py`:
  regenerated `.agent/STATE.md`, `.agent/catalog.json`, `.agent/catalog.csv`,
  and `.agent/BLOCKERS.md`.
- `git diff --check`:
  passed after stripping trailing whitespace from generated `.agent/catalog.csv`.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: `false`.
- Registry/admission state mutated: `false`.
- Solver/OpenFOAM postProcess launched: `false`.
- Scheduler action: Slurm array `3311146[0-5]` submitted and completed.
- Mesh/GCI disposition: `not run`.
- Source/property or Qwall release: `false`.
- Coefficient fitting/admission: `false`.
- S11/S12/S13/S15/S6 trigger: `false`.

## Next Useful Action

Open a separate mesh/GCI disposition row using
`aggregated_exact_label_qoi_rows.csv` and
`aggregated_terminal_window_reductions.csv`. That row should compute
same-label medium/fine disposition per QOI and still avoid coefficient fitting
unless same-window UQ and source/property gates also pass.
