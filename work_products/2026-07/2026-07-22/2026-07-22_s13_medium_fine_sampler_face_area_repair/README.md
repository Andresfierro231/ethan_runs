---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/summary.json
tags: [s13, sampler-repair, face-area-vector, smoke-passed]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22.md
  - .agent/journal/2026-07-22/s13-medium-fine-sampler-face-area-repair.md
  - imports/2026-07-22_s13_medium_fine_sampler_face_area_repair.json
task: TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Scheduler
type: work_product_readme
status: complete
---
# S13 Medium/Fine Sampler Face-Area Repair

This package closes the face-area-vector blocker found in the S13 medium/fine
exact-label sampler. The failed prior package generated face rows without
`area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`, so all six
medium/fine reductions failed before exact-label QOI rows could be sampled.

The repaired sampler now emits and consumes those face-area-vector columns. A
clean one-case/window smoke, `salt_2`/`medium` with one terminal retained
window, completed as Slurm job `3311109` with exit code `0:0`.

## Key Results

- Smoke decision:
  `terminal_exact_label_rows_sampled_mesh_gci_fail_closed_time_equivalence_missing`
- Exact-label QOI rows: `4`
- Terminal-window reduction rows: `1`
- Sampling-error rows: `0`
- Native solver outputs mutated: `false`
- Production harvest allowed: `false`
- Admission allowed: `false`

## Important Files

- `preflight/`: no-heavy source and geometry preflight before smoke.
- `smoke_salt2_medium_one_window/`: clean terminal smoke package.
- `RUNNING.md`: terminal handoff, including scheduler and guardrail notes.
- `run_salt2_medium_one_window_smoke.sbatch`: wrapper used for the clean smoke.

## Claim Boundary

This package proves the face-area-vector repair at smoke scale only. It does
not provide a six-case production harvest, same-label mesh/GCI, Qwall or
source/property release, coefficient admission, final score, or S11/S12/S13/S15
/S6 trigger.

## Next Step

Claim a separate row for the full six-case medium/fine sampler rerun using this
smoke-passed contract. Only after that package has nonempty exact-label rows
for all required case/mesh labels should the same-label mesh/GCI gate be opened.
