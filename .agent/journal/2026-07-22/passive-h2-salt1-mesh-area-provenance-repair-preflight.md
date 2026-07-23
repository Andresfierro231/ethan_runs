---
provenance:
  generated_by: codex
  task_id: TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22
  date: 2026-07-22
tags:
  - passive-h2
  - salt1
  - mesh-area
  - junction
  - source-property
related:
  - .agent/status/2026-07-22_TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight
  - operational_notes/07-26/22/2026-07-22_PASSIVE_H2_SALT1_MESH_AREA_PROVENANCE_REPAIR_PREFLIGHT.md
task: TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---

# Passive-H2 Salt1 Mesh-Area Provenance Repair Preflight

## Attempted

Validated the Salt1 PASSIVE-H2 mesh-area provenance package. The package reads
setup mesh geometry from `constant/polyMesh/points`, `faces`, and `boundary`,
maps 39 source-family patches, and compares the resulting mesh-derived areas
against recovered operator rows from the Salt1 junction setup-row recovery
package.

No scheduler action, native-field edit, Fluid edit, registry/admission mutation,
or thesis edit was performed.

## Observed

- All `39/39` requested boundary patches were present.
- The mesh parser read `2268735` setup points.
- Four families passed area reconciliation:
  `cooling_branch`, `downcomer`, `lower_leg`, and `upcomer`.
- `junction` did not pass the family-area tolerance gate.
- The maximum family area mismatch was `9.533941464717754e-06 m2`, with maximum
  relative mismatch `0.00022444002113082377`.
- The package emitted four mesh-area-backed diagnostic operator rows and zero
  release/freeze/score values.

## Inferred

The old wallHeatFlux-derived area concern is narrower now: most Salt1 PASSIVE-H2
families can be backed by setup mesh geometry alone. The remaining blocker is
not patch discovery, because no patches are missing. It is the exact
junction-family area reconciliation between setup mesh geometry and the
recovered operator row.

This is progress, but it is not enough for source/property release. A complete
five-family operator is still fail-closed, and the four-family diagnostic
candidate must not be promoted without a separately claimed release/UQ/freeze
row.

## Contradictions Or Caveats

- The package proves setup-mesh area provenance for four families, but does not
  prove physical source/property validity.
- A four-family diagnostic operator exists, but excluding `junction` changes the
  candidate definition and cannot be silently substituted for the five-family
  PASSIVE-H2 path.
- Area provenance does not remove the need for same-QOI release UQ.

## Next Useful Actions

1. Open a narrow `junction` reconciliation row that audits the recovered
   junction row against exact junction/stub patch grouping and tolerance policy.
2. If the junction mismatch is explainable from setup-only patch coverage, emit
   a corrected five-family area-backed operator candidate.
3. Only after the five-family area gate and source/property/UQ gates pass,
   consider opening S11/S15 release/freeze work.
