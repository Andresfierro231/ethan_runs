# Modeling Guardrails

- Do not use this package to claim cross-family hydraulic readiness.
- Do not re-admit `left_lower_leg` through overlap reasoning; it remains excluded on the Water side.
- If a future redesign is attempted, start from branch-level cumulative direct branch-end drop and keep the analysis on `right_leg`, `test_section_span`, and `upper_leg` only.
- If `timeseries_fallback_publication_used = yes`, treat the branch-end direct-drop publication path as repaired from preserved retained-time cumulative data rather than from the older per-case summary field alone.

## Branch Notes

- `right_leg`: bounded_cumulative_redesign_candidate -> Both families prefer cumulative direct branch-end drop more often than branch-mean direct gradient on this shared overlap branch. If future cross-family hydraulic redesign work is attempted, start here.
- `test_section_span`: no_clear_redesign_priority -> This shared overlap branch is sign-clean in both families, but the retained-time stability comparison does not show a decisive advantage for cumulative direct branch-end drop over the current branch-mean direct gradient.
- `upper_leg`: no_clear_redesign_priority -> The raw per-case summary terminal direct drop is missing in one or both families, but the publication path can be repaired from preserved retained-time cumulative direct-drop data. After using that repaired publication value, the retained-time stability comparison still does not show a decisive cross-family reason to switch to cumulative end drop over the current branch-mean direct gradient path.
