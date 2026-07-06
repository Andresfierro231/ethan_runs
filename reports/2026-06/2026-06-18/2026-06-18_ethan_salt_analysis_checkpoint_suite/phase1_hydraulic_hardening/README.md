# Phase 1 Hydraulic Hardening

Generated: `2026-06-18`

This checkpoint hardens the Salt hydraulic interpretation using the June 18
Salt closure package outputs. It does not recompute extraction. It instead
repackages the current straight-section and feature results into a more explicit
fit gate and blocker summary.

## Main findings

- Straight-section candidate rows: `12` of `54`
- Buoyancy-aided/net-gain straight sections: `18`
- Candidate feature rows: `19` of `45`

## Key outputs

- `hydraulic_case_checkpoint.csv`
- `hydraulic_screening_matrix.csv`
- `hydraulic_fit_candidates.csv`
- `hydraulic_span_fit_summary.csv`
- `feature_keff_status.csv`
- `feature_keff_summary_by_kind.csv`
- `buoyancy_aided_sections.csv`

## Interpretation checkpoint

This phase confirms that the current Salt hydraulic story is usable for
screening and partial fitting, but not yet fully closure-clean. In particular,
negative or net-gain section losses are preserved as physical outcomes, and the
feature `K_eff` family still inherits the residual `p_rgh` feature path from the
June 17 additive pressure package.
