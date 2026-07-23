---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/endpoint_geometry_enriched_face_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/same_window_medium_fine_equivalence_gate.csv
tags: [journal, s13, same-window, endpoint-geometry, scheduler, mesh-gci, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_same_window_endpoint_gci_uq_admission_chain/README.md
task: TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Scheduler / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# TODO-S13-SAME-WINDOW-ENDPOINT-GCI-UQ-ADMISSION-CHAIN-2026-07-22

## Attempted

Claimed a new S13 continuation row and built a reusable task-owned chain for same-window medium/fine mapping, endpoint geometry enrichment, and downstream GCI/UQ disposition.

The first Slurm submit attempt failed before job creation because no allocation was specified. The prior S13 job used account `ASC23046`, so the wrapper was patched to include `#SBATCH -A ASC23046` and resubmitted.

## Observed

Slurm job `3312020` completed successfully. The package enriched all six Salt2/Salt3/Salt4 endpoint candidate masks from read-only coarse polyMesh files. Each released endpoint mask has `48` faces, owner cells, area magnitudes, area-vector components, centers, OpenFOAM boundary-normal convention, endpoint-specific positive mdot convention, target time label, and source polyMesh provenance.

The medium/fine mapping attempt found role-equivalent terminal rows for all requested QOIs, but the medium/fine processor directories do not contain the coarse physical target labels. For example, Salt2 medium has processor time labels including `516/517/518`, Salt2 fine has `397/398/399`, while coarse direct rows use `7914/7915/7916`.

## Inferred

Endpoint residual support can now use the enriched endpoint masks instead of candidate face IDs. This resolves the endpoint-geometry part of the previous blocker.

Formal GCI and same-QOI UQ still cannot be admitted because role-equivalent terminal rows are not same physical-window rows. Treating terminal-minus/terminal/terminal-plus as a substitute for target-minus/target/target-plus would be proxy substitution.

## Caveats

No field resampling was launched for medium/fine target labels because the target directories were absent. No formal GCI, formal UQ, production harvest, source/property/Qwall release, coefficient fit, admission, final score, or candidate freeze was performed.

## Next Useful Actions

Regenerate medium/fine native outputs or sampled rows at the same physical target-minus/target/target-plus labels as the coarse chain, or publish an auditable physical-time equivalence proof. Once that gate passes, rerun this same chain; endpoint geometry should already pass.
