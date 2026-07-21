---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - topology-forensics
  - journal
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/component_topology_forensics.csv
---

# S13 Upcomer Exchange Topology Forensics And Alternate CV Journal

Task: `TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21`

Observed: the completed topology-CV release package already showed the largest
reverse-flow face components at about `0.53` of the candidate masks with no
trusted right-leg wall face area and non-wall boundary escapes.

Observed: per-component forensics reviewed `56` face-connected components.
Salt2 has no component with trusted right-leg wall contact. Salt3 component
`12` has `10` cells, `6` trusted right-leg wall faces, and `10` escape faces on
`ncc_pipeleg_right_03_upper_end`. Salt4 component `12` has `84` cells, `15`
trusted wall faces, and `36` escape faces on `ncc_pipeleg_right_03_upper_end`.

Inferred: a conservative wall-adjacent alternate CV cannot release S13 under the
existing gates. The only wall-contact components are far too small relative to
the reverse-flow masks and still touch an unreleased nonconformal boundary.

Contradiction/caveat: positive internal interface face counts exist for many
components, but that is not enough. The release contract also requires a
dominant face-connected CV, trusted wall-band contact, and no unreleased
boundary escape for all three cases together.

Next useful actions: review the right-leg ROI and wall-patch alignment before
any surface or sampler work. If a new setup-only recirculation seed is proposed,
predeclare it and rerun topology release with the same dominance, wall, and
boundary-escape gates.
