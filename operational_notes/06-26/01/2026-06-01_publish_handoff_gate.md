# 2026-06-01 publish handoff gate

## 2026-06-30 supersession note

This handoff gate is retained as historical context. The current policy is that
Kirst runs are not mainline evidence or default publish inputs; continuation
Jin artifacts are the mainline path when present.

## Salt2 continuation case

### Decision
- Defer publish handoff updates for `val_salt_test_2_coarse_mesh_laminar`.

### Reasons
- No successful continuation checkpoint has been written.
- The runtime path is still blocked after the corrected container resubmission.
- The current physical interpretation remains conditional on unresolved continuation evidence.

## modern_runs first batch

### Decision
- Defer publish handoff for `work_products/campaigns/2026-06-01_modern_runs_first_batch/`.

### Reasons
- The local extraction and campaign tables are complete, but the current join contract does not define any bounded re-admitted use of historical Kirst rows.
- Kirst rows are now excluded from current mainline publish handoff.
- The water `kOmegaSSTLM` family remains setup-only and intentionally excluded from result claims.

## Required before publish

- Publish mainline continuation/Jin artifacts first.
- If Kirst rows are ever reintroduced for a bounded sensitivity question,
  define a variant-aware comparison contract and dated re-admission note first.
- Resolve or formally waive the salt2 continuation requirement.
