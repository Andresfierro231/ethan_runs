---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/RUNNING.md
tags: [journal, s13, sampler-repair, face-area-vector, smoke-passed]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22.md
  - imports/2026-07-22_s13_medium_fine_sampler_face_area_repair.json
task: TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Scheduler
type: journal
status: complete
---
# S13 Medium/Fine Sampler Face-Area Repair

## Attempted

Picked up the active repair row after the post-sampler gate showed that the
medium/fine exact-label sampler failed because interface rows lacked face-area
vectors. Read the sampler source and tests, ran the local tests, ran a dry
preflight into the repair package, and checked scheduler state before any
submission.

After the smoke-first requirement was clarified, cancelled running full
six-case jobs `3310996` and `3311004`, patched the sampler to accept
`--case-id`, `--mesh-level`, and `--max-windows`, and submitted a clean
`salt_2`/`medium`/one-window smoke as job `3311109`.

After the smoke reached terminal completion, inspected its summary, face CSV,
QOI rows, sampling errors, and Slurm error log.

## Observed

The current sampler source includes `selected_face_area_vectors()` and writes
`area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2` for generated
interface, trusted-wall, and cap face rows. The unit tests include both a
positive area-vector contract check and a fail-closed missing-vector check.
The tests now also cover filtered one-case/window smoke mode. The existing
failed output package still has stale face CSV headers without vector columns.

The clean smoke job `3311109` completed `0:0` on `c318-018`. Its summary
reports `exact_label_qoi_rows=4`, `sampling_error_rows=0`,
`terminal_window_reduction_rows=1`, and
`native_solver_outputs_mutated=false`. The clean smoke exchange-interface CSV
contains `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`.

## Inferred

The code-level repair path is present, locally tested, and compute-smoked on
one case/window. The smoke proves the generated face-contract rows carry
owner-to-neighbor face area vectors before interface reduction and that one
terminal exact-label reduction path can complete without missing-vector errors.

## Caveats

The smoke was intentionally narrow: one case, one mesh level, and one window.
It does not itself satisfy same-label mesh/GCI or production harvest gates.

## Next Useful Actions

Claim a separate full six-case rerun row using the smoke-passed sampler
contract. After that rerun lands, inspect all six medium/fine rows before
opening the same-label mesh/GCI gate.
