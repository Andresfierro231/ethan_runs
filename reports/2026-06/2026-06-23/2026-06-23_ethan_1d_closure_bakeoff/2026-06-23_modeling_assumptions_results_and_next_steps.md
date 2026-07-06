# 1D Closure Status, Assumptions, And Next Steps

Generated: `2026-06-23`

## Purpose

This note turns the June 23 bakeoff tables into a presentation-ready status
write-up. It is intentionally scoped to what is currently defended from local
evidence while the continuation runs and external `Fluid` refresh work are
still underway.

## Modeling assumptions in the current bakeoff

- Comparison basis:
  1D predictions are compared against CFD frozen-state last-window means, not
  against experiment. The current dated comparison table is
  `2026-06-23_representative_salt_last_window_validation_table.csv`.
- Active 1D solver:
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2` in
  `predictive_airside_hx` mode.
- Current defended scored scenario:
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
- Insulation interpretation:
  the defended winner is a baseline `1.0 in` radiation-on case. Hybrid rows in
  the same readable family can apply branchwise outer-loss multipliers, but no
  readable global `1.4 in` Salt scenario is published yet.
- Heat-input contract:
  the current Salt cases use tracked heater power plus a separate `37 W`
  quartz test-section source. The heater-partition table quantifies how much
  of the heater input appears to reach the fluid in CFD.
- Straight-section treatment:
  the bakeoff does not assume a single globally fully developed internal
  closure. Direct `Nu(Re)` is defended only on `left_lower_leg`. Other branches
  are carried as UA'/HTC state surfaces, sensitivity-only lanes, or residual
  buckets depending on support.

Primary branch recommendations from
`closure_term_recommendations.csv` and
`branch_development_summary.csv` are:

- Straight friction:
  `straight_friction_class_aware_re_power_law` on
  `lower_leg|test_section_span`.
- Direct internal thermal closure:
  `left_lower_leg_nu_branch_aware_re_power_law` only on `left_lower_leg`.
- Primary thermal lane:
  UA' profile/state-surface closure on
  `left_lower_leg|test_section_span|left_upper_leg|upcomer`.
- Blocked direct thermal lane:
  `right_leg` / downcomer remains excluded from direct `Nu`.

## Current results

### Defended 1D-vs-CFD status

From `README.md`, `family_metric_summary.csv`, and
`best_full_coverage_case_metrics.csv`:

- The defended full-coverage readable scenario is still
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
- On the current readable surface, the baseline family outranks the hybrid
  family on temperature and energy metrics:
  best baseline mean heater-relative energy error `11.27%`,
  best baseline mean mass-flow error vs CFD `26.69%`,
  best baseline `T_w` RMSE `62.79 K`,
  best baseline `T_p` RMSE `62.69 K`.
- The hybrid family shows a potentially better best mass-flow error
  (`19.55%`) but does not have full readable breadth across the Salt family and
  is therefore not defended as the current top predictive choice.

### Strict comparison subset

The current dated validation table is intentionally narrower than the full Salt
family. The strict comparison-candidate subset currently includes:

- `Salt 1 Kirst`
- `Salt 2 Kirst`
- `Salt 2 Val`

Representative errors from
`2026-06-23_representative_salt_last_window_validation_table.csv` are:

- `Salt 1 Kirst`:
  energy error `16.01%` of heater,
  `T_w` RMSE `65.31 K`,
  `T_p` RMSE `65.24 K`,
  mass-flow error vs CFD `25.45%`.
- `Salt 2 Kirst`:
  energy error `8.92%`,
  `T_w` RMSE `64.65 K`,
  `T_p` RMSE `64.78 K`,
  mass-flow error vs CFD `34.41%`.
- `Salt 2 Val`:
  energy error `8.89%`,
  `T_w` RMSE `58.40 K`,
  `T_p` RMSE `58.05 K`,
  mass-flow error vs CFD `20.21%`.

These numbers show that the present defended 1D lane is directionally useful
but still not strongly predictive in absolute temperature or mass flow.

### Heater partition and heat-loss interpretation

From `2026-06-23_representative_salt_heater_partition.csv`:

- `Salt 1 Kirst`:
  heater config `232.3 W`,
  CFD heater net to fluid `213.09 W`,
  about `19.21 W` of heater power does not appear to reach the fluid.
- `Salt 2 Kirst`:
  heater config `265.7 W`,
  CFD heater net to fluid `243.66 W`,
  about `22.04 W` of heater power does not appear to reach the fluid.
- The current CFD heat-loss contract remains
  `Q_lost = Q_removed + Q_ambient`, where `Q_ambient` is the current CFD-side
  bookkeeping proxy used consistently in the frozen package.

This is useful immediately because it gives a first practical correction target
for the reduced-order heat-input contract even before the external `Fluid`
bundle is refreshed.

### Branch-development findings that already matter

From `branch_development_summary.csv` and
`upcomer_downcomer_contrast.csv`:

- `left_lower_leg` is the best current direct developing-flow thermal evidence
  lane and is the only place where direct `Nu(Re)` is presently defended.
- `test_section_span` and `left_upper_leg` should be treated as state-surface
  branches, not as globally defended direct-`Nu` branches.
- `upcomer` is explicitly sensitivity-only and should be modeled separately
  from the straight direct branches; the current modeling note already points
  toward a convection-cell-style or buoyancy-aware submodel.
- `right_leg` / downcomer remains blocked for direct `Nu`, with missing
  cooler-adjacent return observables and large residual fractions.

## Work underway

Current in-flight work relevant to this package:

- External `Fluid` refresh remains active under `AGENT-102`.
  The local bakeoff is current against the June 22 frozen CFD contract, but the
  readable external `Fluid` campaign is still the June 19
  `ethan_cfd_informed_salt_v1` bundle.
- Continuation runs are still maturing.
  For now, the frozen last-window contract is the right working surface for
  quantitative closure scoring.
- Feature-path hydraulic closure remains additive but incomplete.
  The pathwise endpoint decomposition has been reopened, but the continuous
  retained-time hydro integral / defended `p` vs `p_rgh` subtraction path is
  still not finished.

## Analysis still needed

The highest-value remaining analysis is:

- Refresh the external `Fluid` bundle to a reproducible v2 path so hybrid and
  other CFD-informed closures can be rescored on the June 22 frozen contract.
- Resolve the insulation mismatch explicitly:
  either publish a true global `1.4 in` Salt scenario or document that the
  intended correction is branchwise rather than global.
- Build and test a separate upcomer submodel.
  The current evidence does not support treating the upcomer as just another
  straight developing branch.
- Keep the downcomer on residual / lumped closure for now, but collect the
  missing cooler-adjacent return observables needed to tighten that branch.
- Finish the retained-time feature extractor:
  hydro integral, defended `p` vs `p_rgh` split, straight-reference
  subtraction, and stable feature-loss quantity.
- Re-score Salt 3 and Salt 4 once they clear the stricter convergence-audit
  boundary rather than borrowing the current narrower comparison subset.

## What we can do now to get a better feel

Without waiting for the continuation jobs to finish, useful immediate analysis
still available on the current frozen package is:

- Treat the frozen CFD rows as a provisional training and scoring surface.
  This is already justified in `stale_and_data_needs.csv`.
- Use the heater-partition rows to test a corrected 1D input contract:
  instead of only the nominal heater power, compare against an effective
  heater-to-fluid delivery model.
- Rank sensitivity to closure class separately by observable:
  energy balance, `T_w`, `T_p`, and mass flow should not be collapsed too early
  into one score.
- Compare baseline versus hybrid only where readable support actually exists,
  instead of overgeneralizing the currently under-supported hybrid rows.
- Use the branch-development tables to split the loop into defended direct,
  state-surface, and residual-only regions before attempting any new global
  correlation fit.

## Practical next steps

If the goal is to improve predictive confidence as quickly as possible, the
next bounded sequence should be:

1. Keep using the frozen June 22 CFD contract as the working truth surface.
2. Add a heater-to-fluid correction test to the current 1D interpretation.
3. Prototype an upcomer-specific penalty or buoyancy-aware submodel.
4. Publish or rerun a true `1.4 in`-matched external `Fluid` scenario.
5. Refresh the external Salt bundle and rerank the closure families.
6. Only after that, reopen stronger claims about defended feature `K_eff` or a
   globally predictive Salt 1D closure.
