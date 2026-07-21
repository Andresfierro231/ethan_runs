# Ethan Reduction-Contract Audit

Generated: `2026-06-29T15:01:20-05:00`

## Scope

- Paper-grade Salt subset only: `Salt 1 Jin`, `Salt 2 Jin`, `Salt 3 Jin`, `Salt 4 Jin`.
- This package is additive and provenance-first: it reuses existing reduced package roots instead of reopening the older June 10-26 builders.
- Source package roots:
- `Salt 1 Jin` -> `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/salt1_jin`
- `Salt 2 Jin` -> `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh`
- `Salt 3 Jin` -> `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_3_jin_coarse_mesh`
- `Salt 4 Jin` -> `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/viscosity_screening_salt_test_4_jin_coarse_mesh`

## Main findings

- Station contract shared across all paper-grade cases: `True`.
- Branch geometry contract shared across all paper-grade cases: `True`.
- Branch map rows published: `7`.
- Reduction-choice audit rows published: `79`.
- Salt 1 Jin currently points at the latest-window refresh root that AGENT-121 is rebuilding; this audit records the latest readable package snapshot rather than waiting for the full republish chain.

## Boundaries

- Salt 2-4 currently reuse the June 15 reduced package roots; this audit makes that mixed provenance explicit rather than pretending every case already passed through the live June 29 rerun.
- Flow direction remains a manual profile assumption encoded in the per-case analysis manifests.
- Deferred terms still include the unsampled profile-level `dp` term and inferred feature wall `dp` term where the manifest says so.
