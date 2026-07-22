# Ethan CFD Closure Bundle

Generated: `2026-06-26T09:51:41-05:00`

## Purpose

This bundle packages the current defended Salt CFD-derived closure terms into a
single local machine-readable contract for downstream 1D modeling work.

## Current admitted terms

- straight distributed friction: `straight_friction_class_aware_re_power_law` on `lower_leg, test_section_span` with defended Reynolds window `80.35` to `173.74`
- primary thermal conductance surface: `primary_ua_profile_library` on `left_lower_leg, test_section_span, left_upper_leg, upcomer`
- limited direct `Nu`: `left_lower_leg_nu_branch_aware_re_power_law` on `left_lower_leg` with defended Reynolds window `76.10` to `165.23`

## Explicitly not promoted

- blocked or incomplete topics carried through from the source handoff: `feature_keff_full_path_closure, water_dependency_package`
- direct downcomer or cooler-side internal `Nu`
- feature-resolved defended `K_eff`

## Artifacts

- `salt_closure_bundle.json`: machine-readable closure contract
- `closure_term_contract.csv`: normalized closure-term table
- `branch_state_surface_policy.csv`: branchwise `UA'` / HTC / direct-`Nu` policy rows
- `reference_curve_samples.csv`: sampled friction and direct-`Nu` values across the defended Reynolds windows
- `blocked_term_followons.csv`: exact blocked or missing follow-on requirements
