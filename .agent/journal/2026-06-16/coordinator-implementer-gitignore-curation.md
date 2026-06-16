# AGENT-081 Journal

Date: `2026-06-16T00:00:00-05:00`
Role: `Coordinator / Implementer`
Task: `AGENT-081`

## Intent

Make the root `.gitignore` safe for `git add .` in this workspace by keeping
notes, manifests, configs, and code trackable while excluding generated figure
trees, heavy local mirrors, and scheduler/runtime output.

## Observed state at start

- The existing `.gitignore` only covered Python bytecode plus a few top-level
  scratch directories.
- Top-level `figures/` content, report-package figure subtrees, and `*.out`
  scheduler logs were still eligible for staging.
- The workspace contains both durable notes/code and large generated areas, so
  a path-blind `git add .` was too noisy.

## Planned action

- Keep the ignore rules path-based where possible so report markdown, JSON,
  CSV, and scripts remain visible.
- Ignore figure outputs separately from report prose/data so the reports stay
  addable without their rendered assets.
- Ignore the heavy local staging mirrors rather than broad `jadyn_runs/**`
  content so README/TODO/script files remain trackable.

## Outcome

- Expanded `.gitignore` to cover:
  - local Codex state and Python bytecode
  - `*.out` and `*.err` runtime/scheduler logs
  - top-level generated `figures/` outputs
  - `reports/**/figures/**` and `reports/**/figures_rendered/**`
  - `staging/modern_runs/**`, `staging/render_inputs/**`,
    `staging/render_jobs/**`
  - `jadyn_runs/**/case_stage/**`
  - existing heavy scratch trees such as `cache/`, `tmp/`, `tmp_extract/`,
    `linked_cases/`, and `work_products/`
- Left markdown notes, manifests, configs, helper scripts, and coordination
  files unignored.

## Validation

- Verified ignored examples with `git check-ignore -v`:
  - `slurm-3199773.out`
  - `figures/png/val_salt_test_2_coarse_mesh_laminar.png`
  - `reports/2026-06-09_ethan_steady_state_heat_flow_audit/figures/png/cross_case_heat_partition_comparison.png`
  - `staging/render_jobs/2026-06-15_paraview_cell_association_refresh.sbatch`
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml`
- Verified non-ignored examples with `git check-ignore -v --non-matching`:
  - `staging/AGENTS.override.md`
  - `jadyn_runs/salt2/2026-06-01_continuation_candidate/README.md`
  - `journals/2026-06/2026-06-16_ethan_runs.md`
  - `tools/analyze/build_ethan_case_analysis_package.py`
  - `.agent/BOARD.md`
- Ran `git add -n .` to confirm the dry-run staging set now favors notes,
  configs, manifests, scripts, and report text/data rather than figures and
  `.out` logs.
