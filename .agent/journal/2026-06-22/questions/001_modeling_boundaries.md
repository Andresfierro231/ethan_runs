# Modeling Boundaries

Date: `2026-06-22`

1. How should the upcomer be modeled once the direct `left_lower_leg` Nu branch
   ends?
   Current evidence supports direct Nu only on `left_lower_leg`, while
   `upcomer` stays sensitivity-only and may need a convection-cell or
   loop-coupled closure rather than a generic straight-tube correlation.

2. What exact branchwise reset coordinates should the 1D model use?
   Current packages identify likely redevelopment zones, but there is still no
   durable reset-coordinate contract for quartz transitions, fittings, or the
   cooling-jacket onset.

3. What does “domain breadth” mean in the current closure context?
   It means the defended direct data cover too few branches and too narrow a
   range of retained-time states to justify one broad internal HTC closure over
   the whole loop. The current defended direct lane is strongest on
   `left_lower_leg`; other branches rely on state surfaces or residual buckets.

4. Can temporary frozen data be used while continuations finish?
   Yes for interim pseudo-steady training, diagnostics, and report generation,
   but it should stay labeled as a frozen late-window contract rather than a
   converged final-state closure.

5. What additional data are most valuable next?
   - retained-time hydro-corrected straight rows over a longer late window
   - retained-time branchwise wall/bulk/heat-flux support on right-leg and
     cooler-adjacent branches
   - a durable reset-coordinate contract
   - stronger paper-side mixed-convection evidence promotion for branch policy
