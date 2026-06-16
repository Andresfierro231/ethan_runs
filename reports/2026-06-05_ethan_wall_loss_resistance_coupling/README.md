# Ethan Wall-Loss And Resistance Coupling

Generated: `2026-06-07T15:15:47-05:00`

## What the plots mean

- `figures/png/salt_mdot_vs_ambient_loss_error.png`: each point is one salt case. The x-axis is the CFD absolute error against the Ethan-linked ambient-loss proxy. The y-axis is the CFD absolute mass-flow error. If wall-loss were the only major problem, cases would move mostly left-right with little change in mdot. They do not.
- `figures/png/salt_section_pressure_drop_heatmap.png`: latest-time patch-averaged `|Δp_rgh|` by major branch. Larger values indicate where the hydrostatic-pressure-reduced loop resistance is concentrated. The absolute columns should be used for ranking.

## Scientific interpretation

- The salt cases do not support a single-cause story in which wall loss alone explains the mdot shortfall.
- Salt 2-4 cluster fairly tightly on ambient-loss proxy error, but mdot still changes materially between Jin and Kirst. That is stronger evidence for a coupled resistance problem than for a pure wall-loss problem.
- The upper leg is the dominant pressure-loss section in every salt row. The left leg is consistently the next major branch loss. The test-section branch is much smaller in absolute loss, but it still changes enough between Jin and Kirst to affect loop balance.
- Salt 1 is different from Salt 2-4. It is not just less converged. It sits on a much higher residual floor and much worse validation error simultaneously, which means runtime extension alone may not fully rescue it.

## How to bring the mass-flow error down

- First priority: fix the continuation/bootstrap path and extend Salt 4 Jin and Salt 1 so the pressure and heat-balance tails are no longer ambiguous.
- Second priority: build transient `p_rgh` histories for the upper leg, left leg, and test-section branch. That is the cheapest way to confirm whether the current hydraulic ranking is stable in time.
- Third priority: run a wall-loss sensitivity on the current representative Salt 2 validation row and Salt 4 Jin. Use that to test whether improved ambient exchange reduces temperature bias without worsening mdot further.
- Do not prioritize insulation thickening first. The existing data already show a shared ambient-loss bias, but the mdot spread is too variant-sensitive for insulation thickness to be the first explanatory lever.
- Cp sensitivity is lower priority than wall-loss and resistance-coupling checks because all salt rows currently share the same effectively constant Cp model.

## Recommended clarification work

- `Shared wall-loss boundary underpredicts ambient exchange`: Recompute report metrics after a wall-loss sensitivity centered on Salt 2 validation and Salt 4 Jin. Worth doing now: `yes`.
- `Hydraulic resistance is too high in the upper-left loop path`: Build transient p_rgh history extraction for the upper leg, left leg, and test-section branch before changing geometry. Worth doing now: `yes`.
- `Constant Cp is not the leading-order cause of the mdot mismatch`: Defer Cp sensitivity until after wall-loss and resistance-coupling checks, because those levers have stronger evidence today. Worth doing now: `no`.
- `Salt 1 is a coupled low-power regime problem, not just missing runtime`: Continue both Salt 1 Jin and Salt 1 Kirst with the repaired bootstrap before proposing lower-power wall-loss or cooler-h sensitivities. Worth doing now: `yes`.

## Output files

- `salt_model_assumption_summary.csv`: current 3D property and wall-loss assumption table.
- `salt_coupling_summary.csv`: validation and coupling summary for all salt rows.
- `salt_hydraulic_summary.csv`: section-wise pressure-loss summary in wide format.
- `hypothesis_matrix.csv`: modeling-hypothesis and next-test matrix.

