---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_m3ts_val_salt2_matched_plane_sbatch_submit/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_m3ts_val_salt2_matched_plane_sbatch_submit/local_validation_matrix.csv
  - work_products/2026-07/2026-07-15/2026-07-15_m3ts_val_salt2_matched_plane_sbatch_submit/submitted_jobs.csv
tags: [journal, sbatch, m3ts, val-salt2, matched-plane, onset]
related:
  - .agent/status/2026-07-15_AGENT-439.md
  - imports/2026-07-15_m3ts_val_salt2_matched_plane_sbatch_submit.json
task: AGENT-439
date: 2026-07-15
role: Coordinator/Scheduler/Forward-pred/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# M3+TS / val_salt2 / Matched-Plane sbatch Submit

User requested local validation followed by sbatch submission for:

1. M3+TS study and scorecard.
2. val_salt2 external test.
3. matched-plane/onset extraction after field-contract preflight.

Actions:

- Claimed AGENT-439.
- Built `tools/analyze/build_m3ts_val_salt2_sbatch_studies.py`.
- Added focused tests in `tools/analyze/test_m3ts_val_salt2_sbatch_studies.py`.
- Generated
  `work_products/2026-07/2026-07-15/2026-07-15_m3ts_val_salt2_matched_plane_sbatch_submit/`.
- Ran local/preflight checks.
- Submitted all three jobs through `ssh login3.ls6.tacc.utexas.edu` because
  direct `sbatch` on the compute node only returned the TACC "use a login node"
  notification.

Submitted jobs:

- `3297844`, `m3ts_score`, dependency `afterok:3295438`.
- `3297842`, `val_s2_ext`, dependency `afterok:3295438`.
- `3297843`, `pm5_onset`, dependency `afterok:3295438`.

Initial scheduler check:

- `squeue -j 3297844,3297842,3297843` showed all three `PD (Dependency)`.
- `sacct` showed all three `PENDING`, submitted `2026-07-15T17:43:46`, with no
  assigned node.

Important caveat:

- The M3+TS and val_salt2 jobs are lightweight scorecard/preflight rebuilds
  from existing evidence and setup-only contracts. They are not final
  forward-v1 admission.
- The PM5/onset job is the OpenFOAM postprocessing job; it reruns the existing
  PM5 matched-plane compute wrapper on a compute node after the dependency
  clears.

Guardrails preserved:

- No OpenFOAM on login node.
- No native CFD output mutation.
- No registry/admission mutation.
- No generated-index refresh.
- No external Fluid edit.
