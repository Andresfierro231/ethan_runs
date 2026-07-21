# Friction Correlation Math Reference

Date: 2026-07-09  
Task: AGENT-229  
Role: Coordinator / Writer  
Owner: codex

## Request

The user asked to make sure the math for the actual friction fitted
correlations is documented in this repo for later master's thesis use,
specifically including `F1`, the `F3` correlations, and the `F4` correlations.

## Context Read

- Root coordination instructions and active board state.
- `reports/AGENTS.override.md`, which identifies report package README/prose as
  the right place for thesis-facing interpretive documentation.
- Primary external implementation:
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
- July 7 literature and friction comparison packages:
  - `work_products/2026-07/2026-07-07/2026-07-07_f_lit_forms/README.md`
  - `work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/README.md`
  - `work_products/2026-07/2026-07-07/2026-07-07_f4_buoyancy_friction/README.md`
  - `work_products/2026-07/2026-07-07/2026-07-07_f4_ri_calibration_and_solver_gate/f4_candidate_fit_report.md`
- July 8 rigor review:
  `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md`

## Work Done

Created `reports/2026-07/2026-07-09/2026-07-09_friction_correlation_math_reference/`
with:

- `README.md`: thesis-facing equations, coefficient table, evidence status,
  limitations, source map, and recommended wording.
- `slide_equation_block.md`: compact equation block for slides.

Also created:

- `imports/2026-07-09_friction_correlation_math_reference.json`
- `.agent/status/2026-07-09_AGENT-229.md`

## Key Interpretation Preserved

- `F1` is analytic fully developed laminar friction.
- `F3_hagenbach` is a one-time asymptotic entry-defect correction.
- `F3_shah_apparent` is a literature correlation and currently the strongest
  baseline for presentation/thesis drafting.
- `F4_leg_class` is the actual implemented fitted form, with
  `f/f_lam = a + b/Re` by leg class, but remains provisional.
- The Ri-based F4 candidate is diagnostic only and should be cited as an
  insufficient/failed screen unless future work replaces it.

## No-Change Boundaries

- No native solver outputs were modified.
- No external `cfd-modeling-tools` files were modified.
- No new fit, solver replay, or CFD extraction was run.
