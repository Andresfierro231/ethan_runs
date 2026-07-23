---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_post_junction_source_property_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate/summary.json
tags: [PASSIVE-H2, handoff, forward-model, source-property, no-release]
related:
  - operational_notes/maps/forward-predictive-model.md
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-CONTEXT-HANDOFF-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_context_handoff/README.md
task: TODO-PASSIVE-H2-CONTEXT-HANDOFF-2026-07-22
date: 2026-07-22
role: Writer / Coordinator / Reviewer
type: operational_note
status: complete
---
# PASSIVE-H2 Context Handoff

## Start Here

Open these first:

1. `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_post_junction_source_property_gate/README.md`
2. `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background/README.md`
3. `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/README.md`
4. `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_r4_predeclared_source_envelope_uq_gate/README.md`

## Current State

PASSIVE-H2 runtime coverage is no longer the main blocker. The post-junction
gate records four-case diagnostic runtime evidence for Salt1/Salt2/Salt3/Salt4:
`4/4` runtime-complete, `4/4` accepted roots, and `4/4` nonzero radiation
heat-ledger response.

Salt1 junction recovery landed. Slurm `3312160` completed `0:0` in `00:04:00`
on `c302-005`. Terminal Fluid output used five train operator rows, accepted
all three roots, used no forbidden/protected runtime inputs, and produced
`radiation_on_heat_ledger_delta_W = 13.284890561953006`.

The no-junction candidate `PASSIVE-H2-R4-CAND001` is predeclared and
setup/runtime-ready across its four families, but it also remains fail-closed:
strict source-envelope rows `0`, same-QOI release-UQ rows `0`, release rows
`0`, freeze rows `0`, final score rows `0`.

The Salt1 mesh-area provenance repair preflight is now complete. It found all
`39/39` setup patches and backed four source families with setup mesh areas:
`cooling_branch`, `downcomer`, `lower_leg`, and `upcomer`. The five-family
operator remains fail-closed because `junction` failed area reconciliation. The
package emitted `4` mesh-area-backed diagnostic rows, source/property release
`False`, freeze `False`, and score values `0`.

## Blocker Shift

Before this handoff, the confusing H2 blocker was whether Salt1 lacked a
junction runtime row. That is now resolved at diagnostic runtime level.

The controlling blockers are now:

- release-grade source/property provenance
- junction-family area reconciliation and release-grade subspan provenance
- exact same-QOI release UQ
- freeze gate after exactly one release-ready candidate exists

Current post-junction gate result:

- strict source-envelope-ready rows: `0`
- source/property release-ready rows: `0`
- release-grade subspan rows: `0`
- release-ready same-QOI labels: `0`
- freeze-ready candidates: `0`
- final score values: `0`

## Completed Mesh-Area Row

`TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22` is
complete. It computed Salt1 family areas directly from
`constant/polyMesh/{boundary,faces,points}` and compared them against recovered
operator areas. Treat its four non-junction rows as diagnostic setup-mesh area
evidence only. Do not promote the four-family candidate or silently drop
`junction` from the five-family PASSIVE-H2 path.

## Next Task Sequence

1. Claim a narrow Salt1 `junction` area-reconciliation row. It should audit the
   exact junction/stub patch grouping, recovered-operator area source, and
   tolerance policy using setup-only mesh geometry.

2. If the junction mismatch is recoverable, rebuild a five-family area-backed
   diagnostic operator candidate. If not, record a hard no-go for five-family
   source/property release from Salt1 PASSIVE-H2.

3. Claim a PASSIVE-H2 release-grade source/property provenance repair row.
   It should produce one row per source family with source envelope, property
   labels, source-family provenance, subspan/area basis, split role, and
   release/fail reason.

4. Rerun same-QOI release UQ only after provenance repair.
   Existing Salt2 setup-UQ is diagnostic, not release-grade.

5. Rerun the freeze gate only if exactly one runtime-legal candidate has
   release-grade source/property provenance and same-QOI UQ.

6. Keep S15/S6 final scoring closed until freeze succeeds.

## Do Not Do

- Do not mutate native solver outputs.
- Do not use CFD `wallHeatFlux`, CFD `mdot`, imposed cooler duty, validation
  temperatures, or protected rows as runtime inputs.
- Do not score Salt3/Salt4 or holdout/external rows from diagnostic H2 runs.
- Do not release source/property, Qwall, numeric q-loss, coefficient admission,
  candidate freeze, or final score from the current evidence.
- Do not rerun broad schedulers or Fluid jobs before a new board row authorizes
  the exact command and output path.

## Useful Numbers

- Salt1 recovered junction patch coverage: `18/18`
- Salt1 recovered operator rows used by Fluid: `5`
- Salt1 replacement Slurm job: `3312160`, `COMPLETED`, `0:0`, `00:04:00`
- Salt1 H2 radiation heat-ledger delta: `13.284890561953006 W`
- Salt2 H2 radiation heat-ledger delta: `14.629985767350746 W`
- Salt3 H2 radiation heat-ledger delta: `15.36243689429574 W`
- Salt4 H2 radiation heat-ledger delta: `16.402272249451528 W`
- Salt1 mesh-area patches found: `39/39`
- Salt1 mesh-area family tolerance pass rows: `4/5`
- Salt1 failed mesh-area family: `junction`
- Salt1 mesh-area max area delta: `9.533941464717754e-06 m2`
- Salt1 mesh-area-backed diagnostic rows: `4`

## Continuation Question

The next agent should answer: is the Salt1 `junction` area mismatch a
recoverable setup-only patch grouping issue or a hard provenance break? If it
is recoverable, rebuild the five-family area-backed diagnostic candidate and
then proceed to source/property provenance repair. If it is not recoverable,
publish a clean fail-closed result that H2 is runtime-feasible but not
five-family release-grade.
