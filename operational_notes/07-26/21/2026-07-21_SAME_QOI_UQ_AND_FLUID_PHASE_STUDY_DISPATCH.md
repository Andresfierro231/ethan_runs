---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_same_qoi_scientific_synthesis/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_terminal_source_readiness/summary.json
tags: [same-qoi-uq, cfd-postprocessing, fluid-external-boundary, thesis, uncertainty]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_and_fluid_phase_study_dispatch/README.md
  - .agent/status/2026-07-21_TODO-SAME-QOI-UQ-AND-FLUID-PHASE-STUDY-DISPATCH-2026-07-21.md
task: TODO-SAME-QOI-UQ-AND-FLUID-PHASE-STUDY-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: operational_note
status: complete
supersedes: []
superseded_by:
---

# Same-QOI UQ and External Fluid Phase Study Dispatch

## Why This Exists

The current same-QOI uncertainty package is a useful negative result: retained-time evidence exists in places, but the evidence does not yet include a complete neighboring-window check or accepted same-QOI mesh/GCI for the paper-facing pressure, recirculation, thermal, and heat-loss quantities. That means the thesis can describe the uncertainty discipline, but it cannot yet claim accepted same-QOI uncertainty intervals for final predictive closure admission.

The external-boundary thread is in a similar handoff state. The repo-local external BC contract exists, but the next true implementation blocker is not another CFD package. It is an exact-file Fluid row in `../cfd-modeling-tools/**` that parses external boundary dictionaries and computes external convection, radiation, and layer terms from setup/runtime inputs while keeping forbidden realized `wallHeatFlux` out of predictive runtime.

## Open First

- `.agent/BOARD.md`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/same_qoi_uq_admission_table.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_same_qoi_uq_execution/uq_gap_queue.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict/fluid_external_boundary_runtime_dictionary.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_terminal_source_readiness/README.md`

## Phase Sequence

Phase A is the retained-window inventory. It should answer, for each paper-facing QOI, whether the retained time exists, what neighboring windows are available, whether the window drift is small enough to continue, and which exact source paths support the claim. This is a read-only study; it must not launch samplers or postprocessing.

Phase B is the same-QOI mesh/GCI evidence matrix. It should join the retained-window inventory to existing mesh/GCI packages and mark each pressure, recirculation, thermal, and heat-loss QOI as accepted, blocked, diagnostic-only, or not applicable. It must not invent GCI from two-level or non-monotone evidence.

Phase C is the same-QOI admission table. It should combine Phase A and Phase B, then publish thesis-ready uncertainty rows. The correct outcome may still be a blocked table with `0` admitted rows; that is valuable if it clearly names the missing window, missing mesh/GCI, source-readiness, or policy blocker.

Phase D is the external Fluid exact-file preflight. It should inspect `../cfd-modeling-tools/**` read-only, identify the exact parser/API/test files to edit, and update or create a later implementation row with exact external paths before any external edit.

Phase E is the external Fluid implementation. It is trigger-gated on Phase D. Its job is to parse external boundary dictionaries and compute external convection, radiation, and layer terms from allowed setup/runtime inputs. It must reject forbidden realized `wallHeatFlux`, CFD mass flow, validation temperatures, hidden residual fills, and imposed cooler duty as predictive runtime inputs.

Phase F is the smoke scorecard and runtime-leakage audit. It should exercise the new Fluid path on a small train/support smoke only, not heldout or external-test scoring, and document energy-path accounting without final admission.

Phase G is thesis incorporation. It should write an incorporation addendum or update thesis chapters only after active thesis rows release those files. Until then, the study packages should carry chapter-ready tables, captions, and claim boundaries.

## Output Contract

Each study phase should publish a work-product `README.md`, at least one CSV with stable row IDs, a source manifest, summary JSON, status file, journal entry, and import manifest. Paper-facing rows need these columns wherever applicable: `qoi_family`, `case_or_source_family`, `qoi_name`, `retained_time_source`, `neighbor_window_status`, `mesh_gci_status`, `admission_readiness`, `thesis_destination`, `source_paths`, `next_task`.

## Guardrails

- Do not mutate native CFD/OpenFOAM outputs.
- Do not launch solver, sampler, postprocessing, harvest, or scheduler jobs from these planning rows.
- Do not change registry/admission state from documentation-only studies.
- Do not edit external `../cfd-modeling-tools/**` until Phase D names exact files and the Phase E board row claims them.
- Do not use forbidden realized `wallHeatFlux`, CFD mass flow, validation temperatures, hidden residual fills, or imposed cooler duty as predictive runtime inputs.
- Do not write into active thesis current files unless the board row explicitly owns them and no active thesis writer owns the same files.

## Board Rows

This dispatch created successor rows for:

- `TODO-SAME-QOI-UQ-PHASE-A-RETAINED-WINDOW-INVENTORY-2026-07-21`
- `TODO-SAME-QOI-UQ-PHASE-B-MESH-GCI-EVIDENCE-MATRIX-2026-07-21`
- `TODO-SAME-QOI-UQ-PHASE-C-ADMISSION-TABLE-2026-07-21`
- `TODO-FLUID-EXTERNAL-BC-PHASE-B-EXACT-FILE-PREFLIGHT-2026-07-21`
- `TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21`
- `TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21`
- `TODO-THESIS-CSEM-UQ-FLUID-READINESS-INTEGRATION-2026-07-21`

The best path forward is to execute Phase A first. Phase A produces the missing-window ledger that lets Phase B avoid wasting time on QOIs whose temporal evidence is already insufficient.
