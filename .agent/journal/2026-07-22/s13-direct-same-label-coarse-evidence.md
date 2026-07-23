---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/direct_coarse_evidence_lane_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/case_qoi_direct_coarse_admission_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
tags: [journal, s13, recirculation, coarse-equivalence, mesh-gci]
related:
  - .agent/status/2026-07-22_TODO-S13-DIRECT-SAME-LABEL-COARSE-EVIDENCE-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/README.md
  - imports/2026-07-22_s13_direct_same_label_coarse_evidence.json
task: TODO-S13-DIRECT-SAME-LABEL-COARSE-EVIDENCE-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Direct Same-Label Coarse Evidence

## Attempted

I attempted to resolve the direct same-label coarse evidence lane from existing
topology-derived artifacts. The pass consumed seeded CV/surface manifests,
geometry-only surface VTKs, current-coarse same-QOI triplets, medium/fine
exact-label rows, strict coarse no-go context, and endpoint recovery evidence.

## Observed

The seeded geometry basis is useful and should be preserved:
Salt2/Salt3/Salt4 all have seeded coarse CV masks, cell VTKs, cell volumes,
exchange-interface faces, trusted-wall faces, wall/core bands, and
geometry-only VTKs. The current-coarse triplets also exist for all four QOIs and
all three cases.

The evidence is still not direct-admission grade. Geometry-only VTKs lack
sampled fields. `Q_wall_W`/source-property release remains false. The coarse
target-window family is not admitted as the same window role as the medium/fine
terminal exact-label family. Endpoint masks remain candidate face IDs without
released area vectors, owner cells, endpoint normals, or throughflow sign
convention.

## Inferred

Formal GCI and same-QOI UQ should not be rerun yet. The next high-value compute
row is not GCI; it is direct sampled coarse surface-field extraction using the
seeded interface/trusted-wall geometry and exact target-minus/target/target-plus
native fields, followed by a same-window equivalence decision.

## Caveats

This row did not run a scheduler job or sample new fields. It is an admission
audit and compute-ready contract over existing evidence. The broad trigger-gated
S11 `tools/analyze` conflict remains a coordination caveat; this work stayed in
fresh S13-specific files and did not touch the S11 candidate/source-property
lane.

## Next Useful Actions

1. Claim a scheduler-authorized extraction row to generate direct sampled
   coarse surface-field rows from the seeded geometry for exact S13 QOIs.
2. Resolve same-window equivalence by either documenting a terminal-equivalence
   map or regenerating medium/fine rows on the same physical window role.
3. Release endpoint residual basis if pressure/energy residual support is to be
   claimed.
4. Rerun formal GCI and same-QOI UQ only after direct same-label coarse rows are
   admitted.
