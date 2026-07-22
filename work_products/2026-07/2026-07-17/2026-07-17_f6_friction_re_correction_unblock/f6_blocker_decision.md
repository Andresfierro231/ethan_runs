---
provenance:
  - f6_candidate_inventory.csv
  - f6_vs_f3_scorecard.csv
  - next_extraction_queue.csv
tags: [f6, friction, blocker, decision]
related:
  - .agent/blockers.yml
task: AGENT-487
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: blocker_decision
status: complete
---
# F6 Blocker Decision

Decision: `keep_open_narrowed`.

The current package reviews `12` PM5 F6/onset rows.
Ordinary single-stream F6 has `0` candidate
rows and `0` scoreable rows. The
recirculation-modeled lane has `12` diagnostic or
future-hybrid rows and `0` scoreable rows.

Production remains `F3_shah_apparent`. The blocker can clear only after
non-recirculating pressure evidence or a named recirculation/onset lane beats
`F3_shah_apparent` on validation/holdout without a hidden global multiplier.

Generated-index refresh was intentionally not run in this task because active
`AGENT-482` owns `.agent/STATE.md`, `.agent/BLOCKERS.md`, `.agent/catalog.json`,
and `.agent/catalog.csv`.
