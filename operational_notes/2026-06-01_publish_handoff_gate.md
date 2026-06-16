# 2026-06-01 publish handoff gate

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
- The local extraction and campaign tables are complete, but the current join contract does not define how Jin/Kirst salt variants should map into the canonical cross-model comparison rows.
- Two Kirst salt cases remain in `incomplete` run status.
- The water `kOmegaSSTLM` family remains setup-only and intentionally excluded from result claims.

## Required before publish

- Define a variant-aware comparison contract for Jin/Kirst salt cases.
- Disposition incomplete salt cases explicitly.
- Resolve or formally waive the salt2 continuation requirement.
