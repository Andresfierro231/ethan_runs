---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_window_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_exact_label_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery/endpoint_face_geometry_recovery_matrix.csv
tags: [journal, s13, scheduler, coarse, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/README.md
task: TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# TODO-S13-DIRECT-COARSE-EXTRACTION-GCI-UQ-CHAIN-2026-07-22

## Attempted

Built and executed a task-owned scheduler chain for S13 direct coarse sampled-field evidence. The chain used seeded coarse geometry and target-minus/target/target-plus native-field evidence for U, T, rho, and wallHeatFlux, then resolved the requested medium/fine equivalence, endpoint residual-basis, formal GCI, and same-QOI UQ gates.

## Observed

Slurm job `3311815` completed successfully with command `python3.11 tools/extract/build_s13_direct_coarse_extraction_gci_uq_chain.py --execute --job-id 3311815`.

The package wrote `36` direct sampled coarse rows across Salt2/Salt3/Salt4, four QOIs, and three window roles. It also wrote `12` diagnostic neighbor-spread rows.

Same-window medium/fine equivalence admitted `0/12` rows. Endpoint residual basis admitted `0/6` endpoint rows because area vectors, owner cells, normals, and positive mdot sign conventions remain absent from the endpoint mask evidence. Formal GCI ran `0/4` QOI rows, and formal same-QOI UQ reran `0/12` rows.

## Inferred

The requested coarse surface-field evidence is now present and auditable, but it cannot support formal GCI or admission-grade same-QOI UQ yet. The correct scientific state is a fail-closed chain with diagnostic neighbor-window spread only.

## Contradictions Or Caveats

The coarse rows are direct sampled-field rows from the current seeded geometry/evidence package, not a production harvest or model admission. Medium/fine rows currently carry exact labels but not admitted same physical coarse target windows. Endpoint residual masks are still geometry-incomplete for conservation residuals.

## Next Useful Actions

Recover or regenerate medium/fine samples at the same physical windows used by the coarse target-minus/target/target-plus rows, or publish an auditable terminal-to-target equivalence map that admits the same-window basis.

Enrich endpoint throughflow inlet/outlet masks with face area vectors, owner cells, normals, and the positive mdot convention. After both gates pass, rerun formal GCI and same-QOI UQ using the exact labels already defined here.

Keep Q_wall_W, exchange-cell residuals, production harvest, coefficient fitting, and candidate admission closed until those gates pass.
