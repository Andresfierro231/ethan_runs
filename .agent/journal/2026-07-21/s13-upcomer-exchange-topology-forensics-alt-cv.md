---
provenance:
  - tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/component_topology_forensics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/alternate_cv_case_summary.csv
tags: [s13, upcomer, exchange-cell, topology, forensics, alternate-cv, journal]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv.json
task: TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Upcomer Exchange Topology Forensics and Alternate CV

## Attempted

Built a task-owned forensic package that reuses the completed reverse-flow
masks, cell-volume CSVs, and native Salt2/Salt3/Salt4 `polyMesh` topology. The
builder computes per-component wall contact, internal exchange-interface area,
boundary escapes, reverse-component volume, and a conservative alternate-CV
selection.

The alternate selector did not relax the prior gates. It prefers a right-leg
wall-adjacent reverse-flow component when one exists, but release still requires
dominant component fraction, positive interface area, positive right-leg wall
area, and zero unclassified boundary escapes in all three cases.

## Observed

- Salt2 has `17` reverse-flow face components and `0` wall-adjacent reverse
  components. The selected alternate is therefore the largest component, which
  has `71775` cells, `0` wall faces, and `5694` boundary escape faces.
- Salt3 has `20` reverse-flow face components and `1` wall-adjacent reverse
  component. The selected alternate is component `12`, with `10` cells, `6`
  wall faces, and `10` boundary escape faces.
- Salt4 has `19` reverse-flow face components and `1` wall-adjacent reverse
  component. The selected alternate is component `12`, with `84` cells, `15`
  wall faces, and `36` boundary escape faces.
- `0/3` alternate CV rows release; downstream surface extraction remains
  blocked.

## Inferred

Reverse-flow components alone cannot define the S13 upcomer exchange heat-loss
CV. Salt2 has no wall-attached reverse component, while Salt3/Salt4 only expose
small wall-attached fragments that do not form dominant closed CVs. The next
rigorous path is a physical geometry-defined CV with cap/interface/wall lanes,
using reverse-flow occupancy only as a diagnostic field inside the physical CV.

## Contradictions and Caveats

- The prior largest-component result was not just missing a wall patch label:
  the per-component pass confirms there is no Salt2 wall-adjacent reverse
  component under the current mask.
- Salt3/Salt4 wall contact exists, but it is not sufficient evidence because
  the selected fragments are tiny and have boundary escapes.
- No low-throughflow scalar was released as a trusted selection input in the
  current packages; this row therefore used the existing reverse-flow evidence
  and did not invent a low-throughflow threshold.

## Next Useful Actions

1. Claim a separate physical-CV definition row that is not restricted to
   reverse-flow components.
2. Define inlet/outlet cap, wall, and exchange-interface lanes from geometry
   and topology.
3. Treat `V_reverse/V_CV` as diagnostic occupancy after the physical CV is
   released.
4. Keep surface extraction, sampler refresh, harvest, UQ, and S11/S15/S6
   blocked until the physical CV releases `3/3` cases.
