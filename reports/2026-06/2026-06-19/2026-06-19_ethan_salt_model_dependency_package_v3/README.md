# Ethan Salt Model Dependency Package v3

Generated: `2026-06-19`

## Purpose

This package rebuilds the Salt model-dependency layer after the new v3 thermal
hardening pass and the stricter feature-path blocker audit.

## Current status

- straight-section friction: `provisional_defended`
- feature `K_eff`: `not_defensible_yet`
- Salt Nu: `provisional_defended`

## Row counts

- hydraulic fit-used rows: `12`
- thermal fit-used rows: `7`
- proxy-positive but non-defended feature rows: `21`

## Important boundary

Feature `K_eff` is intentionally refused here until a real full-path hydraulic
closure exists. Salt Nu may be admitted only on the limited direct-branch
domain documented in `salt_nu_fit_results.json`.
