# Open Questions

## Still blocked

1. Feature `K_eff`
   - The current artifact stack still lacks retained-time full-path hydro
     integrals.
   - More runtime alone does not solve this.
   - A new extractor is required before defended feature-path closure exists.

2. Straight-friction late-window hardening
   - The current straight fit is useful and admitted provisionally.
   - The stronger desired support remains retained-time defended straight rows
     over the preferred late window.

3. Broader direct `Nu` admission
   - Only `left_lower_leg` is currently defended for a direct fitted `Nu(Re)`.
   - The right leg and other unsupported return-path regions remain outside the
     defended direct thermal fit boundary.

4. Quartz / transition redevelopment contract
   - The literature review supports a separate redevelopment framework.
   - The repo still needs one durable reset-location and development-coordinate
     contract before that can be implemented cleanly.

5. Cooler-side closure semantics
   - The readable cases expose fixed sink `Q`, not a directly readable cooler
     `h`.
   - If a future model wants a live cooler-side closure, the preprocessing path
     from metadata to final boundary condition must be reconstructed or
     published.

## Still separate by design

1. Salt vs Water
   - The current repo evidence still supports a Salt-first defended fit surface
     and a Water readiness-only lane.
   - A shared collapse remains a future audit question, not a current result.

2. State surfaces vs direct closures
   - `UA'(x)` and `HTC(x)` are currently safer than wider direct `Nu` fits.
   - This package deliberately keeps that asymmetry explicit.

## Future update trigger

Refresh this package after either of these happens:

- a new retained-time feature-path hydraulic extractor lands
- the current continuation, repaired Salt 4 relaunches, and repaired optimum
  wave preserve enough late-window support to rerun the straight and thermal
  hardening packages on stronger retained-time evidence

Runtime note:

- the June 22 Salt 4 relaunches and optimum-wave relaunch repair workflow
  failures, not closure logic
- the June 22 Water timeouts matter operationally, but they do not by
  themselves change what this package admits or blocks scientifically

## Implementation boundary

1. Code workspace separation
   - This package now defines the dual-path implementation brief.
   - Actual solver edits still belong in the 1D code workspace, not in
     `ethan_runs`.

2. Shared-bundle discipline
   - The `Fluid` path and `salt_cfd_rom` path should consume one identical
     closure bundle.
   - If the two paths drift onto different bundle contents, cross-path ROM
     comparison loses meaning.
