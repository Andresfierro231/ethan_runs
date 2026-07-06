# AGENT-114 Question: Upcomer Versus Downcomer Modeling Split

## Current question

- What is the smallest defended modeling split that captures the observed
  difference between the `upcomer` and the blocked `right_leg` / downcomer?

## Why it matters

- The bakeoff keeps `upcomer` much better supported than `right_leg`:
  - `upcomer` support fraction `0.96`, mean `HTC` `120.7 W/m^2-K`
  - `right_leg` support fraction `0.73`, mean `HTC` `61.7 W/m^2-K`
- A single straight-pipe closure applied loop-wide would erase the very branch
  difference the current CFD evidence is showing.

## Immediate bounded answer

- Keep direct `Nu(Re)` restricted to `left_lower_leg`.
- Keep `upcomer` on a separate state-surface / sensitivity lane now.
- Keep `right_leg` / downcomer inside residual or lumped return-leg treatment
  until cooler-adjacent observables are preserved more directly.

## Next data or implementation needed

- Prototype an upcomer-specific hydraulic penalty or buoyancy-aware submodel
  using `Ri`, `Gr`, `Ra`, and development position as gating diagnostics.
