---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/stage_a_b_face_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/stage_a_b_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/blocker_delta.csv
tags: [f6, stage-b-qa, gate-refresh, pressure-basis, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH.md
  - imports/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh.json
task: TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: journal
status: complete
---

# F6 Stage B Harvest QA And Gate Refresh

## Attempted

I built a reproducible QA/gate-refresh package that normalizes Stage A and
Stage B F6 harvested outputs into one face table and one endpoint-pair table.
The package then refreshes the gate status and records which blockers changed
after coarse VTK sampling.

I also queued two future rows: one for static-pressure basis reconstruction
audit and one for publication claim freeze. Those rows are unclaimed and do not
change admission state.

## Observed

The Stage B sampler resolved the missing coarse VTK output blocker. Stage A+B
now contains 20 sampled endpoint faces and 10 endpoint pairs.

All endpoint pairs fail ordinary-flow by RAF/RMF. Stage A pairs are already
`recirc_diagnostic`; Stage B coarse pairs have material reverse-area fractions
and about half reverse mass fraction. Coarse static `p` is still absent, so
coarse static pressure deltas remain blank by design.

## Inferred

The new evidence strengthens the diagnostic result but does not unlock
coefficient admission. The refreshed state is:

- raw face sampling: pass
- ordinary-flow: fail
- static-pressure basis: blocked for coarse rows
- same-QOI mesh/UQ: blocked
- F3 comparison: not evaluated
- admission: closed

The correct next scientific choice is not to fit F6. It is to either audit
whether static `p` can be reconstructed under a validated pressure convention,
or search for a different low-recirculation anchor under the existing S10 row.

## Contradictions Or Caveats

Stage B adds coarse mesh evidence, but not same-QOI static-pressure evidence.
The coarse rows are useful for face area and recirculation diagnostics only
until static `p` is either recovered rigorously or declared unavailable.

No publication claim should describe these rows as component losses. They are
diagnostic evidence supporting the recirculation/pressure-basis gate story.

## Next Useful Actions

Claim `TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT` if the next goal is to test
whether `p_rgh` can become admissible static pressure. Claim
`TODO-THESIS-STUDY-S10-PRESSURE-F6-LOW-RECIRC-ANCHOR-UQ-2026-07-21` if the next
goal is to find a lower-recirculation pressure anchor. Defer
`TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE` until one of those paths has a
clear decision.
