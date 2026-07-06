# AGENT-102 Questions

Date: `2026-06-23`

## External Fluid refresh

- Should the refreshed Ethan CFD-informed Salt replay replace
  `ethan_cfd_informed_salt_v1`, or should it land as a parallel `v2` bundle
  until the old campaign is retired?
- If a full producer script cannot be landed quickly, what is the minimum
  static bundle contract that still keeps the external replay reproducible
  enough for review?

## Data breadth

- Hybrid coverage is still effectively readable only for Salt 1. Can the next
  external replay be presentation-useful with that asymmetry, or should it be
  labeled strictly as a partial closure-family trend surface until more Salt
  cases are rerun?
