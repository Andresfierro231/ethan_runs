# Cross-Family Hydraulic Redesign Screen

Generated: `2026-06-22T09:48:09-05:00`

## Purpose

This package does one bounded follow-on analysis on the current shared
Salt/Water hydraulic overlap branches. It does not fit a cross-family model
and it does not reopen extraction. Its only question is whether future direct
branch reduction work should prefer cumulative direct `p_rgh` branch-end drop
over the current branch-mean direct gradient path.

## Shared Overlap Branches Screened

- `right_leg, test_section_span, upper_leg`

- Current closure guardrail: `reports/2026-06-18_ethan_transport_interpretation_closure/cross_family_claims_audit.csv`

## Observed Outcome

- `right_leg` -> `bounded_cumulative_redesign_candidate`: Both families prefer cumulative direct branch-end drop more often than branch-mean direct gradient on this shared overlap branch. If future cross-family hydraulic redesign work is attempted, start here.
- `test_section_span` -> `no_clear_redesign_priority`: This shared overlap branch is sign-clean in both families, but the retained-time stability comparison does not show a decisive advantage for cumulative direct branch-end drop over the current branch-mean direct gradient.
- `upper_leg` -> `no_clear_redesign_priority`: The raw per-case summary terminal direct drop is missing in one or both families, but the publication path can be repaired from preserved retained-time cumulative direct-drop data. After using that repaired publication value, the retained-time stability comparison still does not show a decisive cross-family reason to switch to cumulative end drop over the current branch-mean direct gradient path.

## Interpretation Boundary

- This screen does not make any branch cross-family-ready by itself.
- It only identifies where a future redesign of the direct hydraulic observable would have the best evidence base.
- The current closure guardrail still applies even on the shared clean overlap branches.

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py`
- `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir tmp/2026-06-18_ethan_cross_family_hydraulic_redesign_screen_smoke`
- `python tools/analyze/build_ethan_cross_family_hydraulic_redesign_screen.py --output-dir reports/2026-06-18_ethan_cross_family_hydraulic_redesign_screen`
