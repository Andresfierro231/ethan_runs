# Sponsor Salt Status Deck

Generated: `2026-06-08T10:08:00-05:00`

## Purpose

This package is a sponsor-facing, salt-first presentation scaffold built from the current Ethan CFD reporting stack plus a live June 8 continuation snapshot. It is meant to accelerate a same-day status deck, not to replace the underlying scientific report packages.

## Audience convention

- Emphasize what is usable now, what is provisional, and what is not yet supported.
- Keep decisions, blockers, and next-run priorities explicit.
- Avoid manuscript-grade claims for Salt 1 or the water cases.

## Current sponsor-safe headline

- `Salt 2` remains the best-supported validation-style salt case and is already usable for steady-state interpretation with caveats.
- `Salt 4 Jin` is the live improvement target; as of `2026-06-08T10:08:00-05:00`, continuation `3210231` is still running and advancing stably through about `3896.935643564 s`.
- `Salt 1` is no longer blocked by the broad runtime/bootstrap question, but it is still not a clean steady-state result and the current Kirst retry path is blocked on a missing root-level `T`.
- The strongest current mechanism story is coupled wall-loss plus hydraulic-resistance mismatch, not a wall-loss-only explanation.

## Package contents

- `slide_outline.md`: sponsor-facing 8-slide outline with exact figure paths and confidence framing.
- `live_status_summary.csv`: compact June 8 status table for Salt 1-4 and the current actions.
- `summary.json`: machine-readable deck summary, source references, and live runtime snapshot.

## Figure sources to use

- `reports/2026-06-05_ethan_convergence_and_salt1_campaign/figures/png/eight_case_convergence_dashboard.png`
- `reports/2026-06-04_salt2_behavior_package/figures/png/salt2_mdot_compare.png`
- `reports/2026-06-04_salt2_behavior_package/figures/png/salt2_tp_compare.png`
- `reports/2026-06-05_ethan_wall_loss_resistance_coupling/figures/png/salt_mdot_vs_ambient_loss_error.png`
- `reports/2026-06-05_ethan_wall_loss_resistance_coupling/figures/png/salt_section_pressure_drop_heatmap.png`

## Source packages

- `reports/2026-06-04_all_salt_behavior_package/`
- `reports/2026-06-04_salt2_behavior_package/`
- `reports/2026-06-05_ethan_continuation_diagnosis/`
- `reports/2026-06-05_ethan_convergence_and_salt1_campaign/`
- `reports/2026-06-05_ethan_wall_loss_resistance_coupling/`
- `reports/2026-06-04_ethan_essential_steadiness_audit/`

## Important caveats

- Most narrative report packages were last regenerated on June 7, 2026 or earlier. This package adds a live June 8 status overlay for the continuation jobs rather than claiming full report-package refresh.
- `Salt 4 Jin` should be described as a live operational update, not as a completed scientific outcome.
- Water rows remain useful only as validation context and should not headline the sponsor deck.
