# Mainline Continuation Staging / Index Plan (AGENT-156 phase 2, task 1)

Date: `2026-06-30`
Owner: claude (AGENT-156)

## The finding (reproducibility gap was an INDEXING gap)

The 2026-06-30 inspection flagged that the published closures rest on continuation
("mainline") runs whose field data appeared absent. It is NOT absent — it is
staged locally, just not under the canonical `staging/`/`registry`. The nominal
mainline continuation trees are:

| case | continuation tree (under `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/`) | latest t (s) |
| --- | --- | --- |
| salt1_jin | `salt1_jin/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation` | 3756 (basecont 2026-06-25: 4026) |
| salt2_jin | `salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation` | 7915 |
| salt3_jin | `salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation` | 7618 |
| salt4_jin | `salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation` | 10000 |
| water1..4 | `water{1..4}/case_stage/val_water_test_{n}_coarse_mesh_laminar_continuation` | 5036–9609 |

`reconcile_freeze_windows.py` (now searching `jadyn_runs/` too) confirms 8/14
freeze lanes verifiable_on_disk — all the nominal continuation + water lanes. The
remaining unverifiable lanes are the hiq/loq PERTURBATION variants (separate
sensitivity group per the run-classification rule; different waves/times).

Upstream `/scratch/09807/ethanrozak/` is also readable as an ultimate source.

## What was done now (no shared-state mutation)

- Confirmed fields (U, p_rgh, rho, phi, wallHeatFlux, mdot monitors, faceZones)
  exist in the continuation trees.
- Ran convergence (#2) directly on the continuation postProcessing: Salt 2/3/4
  Jin stationary (heat closes <0.1%); Salt 1 weaker (-2.08%).
- Reconstructed salt2_jin continuation (t=7915) into
  `tmp/2026-06-30_claude_action_items/recon_salt2_jin_continuation/` (non-mutating
  scratch) and reran section-mean pressure (#1) — closure-grade, consistent with
  the parent-warmup state.

## Decision needed from the coordinator (shared files)

Registering the continuation runs into the canonical `registry/case_registry.csv`
and/or symlinking under `staging/` touches SHARED, coordinator-approval files
(`registry/`, `config/`). AGENT-156 did NOT edit them. Two options to choose:

- **Option A (index-only, low risk):** leave the data in `jadyn_runs/` and treat
  this note + the reconcile tool's `resolved_tree` output as the authoritative
  index. Pro: no shared-state churn, no duplication. Con: canonical registry still
  omits the mainline.
- **Option B (register, canonical):** add continuation rows to
  `registry/case_registry.csv` (source_id e.g. `..._jin_continuation`, source_root
  = the jadyn_runs tree) so the standard pipeline resolves the mainline directly.
  Requires coordinator approval and a registry entry per case.

Recommendation: **Option A now** (the reconcile tool already resolves trees), and
open a separate coordinated task for Option B if the canonical pipeline must run
on the mainline unattended.

## Remaining mechanical steps (data proven available)

1. Reconstruct salt3_jin and salt4_jin continuations (same recipe) and rerun #1.
2. Re-derive the closure-grade friction/Nu inputs from the continuation window
   (so #3 fits rest on mainline, not warmup) — coordinate with the closure-bundle
   owner since that feeds `ethan_cfd_informed_salt_v2`.

## Reconstruction note

The continuation reconstruction must be run to completion in ONE foreground
invocation (~5 min, 1 core); backgrounded runs were observed to be killed
mid-merge, leaving a truncated `constant/polyMesh/points`. If that happens, delete
`constant/polyMesh` and the partial time dir and retry.
