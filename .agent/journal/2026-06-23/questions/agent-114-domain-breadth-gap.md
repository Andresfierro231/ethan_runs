# AGENT-114 Question: Hybrid Domain Breadth Gap

## Current question

- How much of the current "hybrid underperformance" is real, and how much is
  simply the result of only having `1` readable primary hybrid row against `3`
  primary frozen references?

## Why it matters

- The current bakeoff shows the best full-coverage winner is baseline, but the
  best mass-flow row is hybrid.
- Without Salt 2-4 hybrid breadth on the refreshed closure surface, the repo
  cannot honestly claim whether the hybrid lane is globally worse, globally
  better, or just differently tuned by observable.

## Immediate bounded answer

- Yes, the current frozen-state rows are still usable now as a provisional
  training and scoring surface.
- No, they are not enough to promote the hybrid lane as the global winner yet.

## Next data needed

- A reproducible external `Fluid` `v2` bundle build and Salt rerun that exposes
  the hybrid lane on the same primary case set as the baseline lane.
