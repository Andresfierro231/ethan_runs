---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [friction, closure-ledger, momentum-budget]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/literature-synthesis-and-gates.md
---
# Friction Closures — Map of Content

Tags: #friction #closure-ledger #momentum-budget

## What this covers
The friction-factor closure hierarchy (F1 → F3 → F4 → F5 → F6) for the TAMU 1D
molten-salt loop model: which forms are implemented, which is the production
baseline, what has been tried and failed, and where the CFD-derived friction
evidence comes from. Companion threads: the pressure/momentum-budget map (where
the de-buoyed f numbers originate) and the literature-synthesis map (candidate
forms and gates).

## Current status (one paragraph)
Production baseline is **F3_shah_apparent** (developing-length apparent friction),
the current best literature-backed form. F1 (64/Re) is reference/diagnostic only.
F4 (leg-class multiplier) and F5 (Ri correction) were both tried and did not
validate; F5 is kept as negative evidence. AGENT-310 shows the H1 aggregate
fixed-K proxy improves forward-v0 mdot enough to refresh a forward-v1 scorecard
as diagnostic evidence, but not enough to claim a final localized closure. The
open next step is still a faithful localized named-loss/reset implementation or
**F6 = 1+a/Re^b** (φ vs Re rather than φ vs Ri), tracked as blocker
`f6-friction-re-correction`. Cross-cutting lesson from lit review: a single
global friction factor is not literature-supported, and fully-developed 64/Re is
a reference, not a default.

## Trusted results
- **F3_shah_apparent = production baseline.** Salt2/3/4 mdot error
  −0.93 / +3.33 / +3.75 %. → `reports/2026-07/2026-07-09/2026-07-09_friction_correlation_math_reference/`
  (mdot table at README.md:229).
- **De-buoyed momentum-budget f** is positive/mesh-consistent only on the
  fit-safe spans (left_lower_leg, left_upper_leg) / isothermal upcomer (~2–2.7);
  single-leg heated/cooled p_rgh gradients give unphysical negative f. →
  `work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/`
- Closure library (F1, F3_hagenbach, F3_shah_apparent, F4_leg_class) is
  implemented and solver-wired. → `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  (external repo, read-only).

## Open / in-progress / blocked
- **F6 = 1+a/Re^b** (φ vs Re) — OPEN, the recommended next avenue after F5 failed.
  Blocker `f6-friction-re-correction` in `.agent/BLOCKERS.md` (line 16/34). →
  `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`
- **Per-leg vs single-global friction multiplier** — implemented in solver
  (AGENT-171), identified as the highest-value hydraulic lever, but NOT yet
  calibrated/validated. → `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/`,
  `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/`
- **F-lit laminar forms (Shah, Baehr-Stephan)** — candidate screens built, not
  promoted; constants need primary-source check (TODO-TARGETED-LITREV-FORMS). →
  `work_products/2026-07/2026-07-07/2026-07-07_f_lit_forms/`

## Research avenues tried (outcome + provenance)
- **F1 (64/Re laminar)** — reference/diagnostic only; flagged
  failed_as_predictive_form. Under-predicts the 2–3× de-buoyed CFD friction.
- **F3_hagenbach** — F1 + one-time asymptotic entrance pressure defect;
  implemented, superseded by F3_shah_apparent as baseline.
- **F4 buoyancy-modified (`F4_leg_class`)** — PARTIAL/FAILED. Leg-class multiplier
  over-stiffens the loop (~−23…−25% mdot); upcomer class fit R²=0.02
  (README.md:45,95). Provisional/training-set diagnostic only. →
  `work_products/2026-07/2026-07-07/2026-07-07_f4_buoyancy_friction/`
- **F5 Ri-corrected (φ=1+c·Ri)** — FAILED, kept as negative evidence. All leg
  fits R²<0, c≈0; only 3 points, Ri/Re collinear, ~2× offset not Ri-driven. →
  `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`,
  `work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/`
- **H1 aggregate fixed-K proxy** — SUCCESS as bounded diagnostic screen, not a
  publication closure. For `F1_heater_only`, mean mdot error drops from
  0.0054775 kg/s to 0.0021442 kg/s without thermal fitting; Salt2 is training
  residual, Salt3/Salt4 are diagnostic no-refit checks. →
  `work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/`
- **Cross-cutting (lit review)** — literature does NOT support a single global
  friction factor; 64/Re is a reference, not a default. →
  `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/`

## Key artifacts (canonical)
- Math reference / baseline choice: `reports/2026-07/2026-07-09/2026-07-09_friction_correlation_math_reference/`
- Closure library (external): `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
- CFD de-buoyed f (momentum budget): `work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/`
- F4 calibration: `work_products/2026-07/2026-07-07/2026-07-07_f4_buoyancy_friction/`
- F5 Ri screen (negative evidence): `work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/`
- F-lit candidate forms: `work_products/2026-07/2026-07-07/2026-07-07_f_lit_forms/`
- H1 hydraulic scorecard: `work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/`
- Path-forward + F6 rationale: `operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md`
- Lit-review lessons: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/`

## Related
- `operational_notes/maps/README.md` — MOC index
- `operational_notes/maps/pressure-and-momentum-budget.md` — source of de-buoyed f
- `operational_notes/maps/literature-synthesis-and-gates.md` — candidate forms & gates
- `.agent/BLOCKERS.md` — `f6-friction-re-correction`
