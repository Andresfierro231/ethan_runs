---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/case_qoi_medium_fine_spread.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/qoi_mesh_disposition_summary.csv
tags: [journal, s13, recirculation, exchange-cell, medium-fine, mesh-gci]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22.md
  - imports/2026-07-22_s13_medium_fine_mesh_gci_disposition.json
task: TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Medium/Fine Mesh-GCI Disposition

## Attempted

Built a reusable package that consumes the completed S13 split-rerun aggregate
files and computes one medium/fine spread row per Salt2/Salt3/Salt4 case and
QOI. The builder also emits the formal-GCI blocker and production/admission
gate.

## Observed

The exact-label split rerun is complete enough to compute two-level mesh
sensitivity. `Q_wall_W` is close across medium/fine grids, with maximum spread
below one percent. The exchange-flow proxy, recirculation residence-time proxy,
and wall/core temperature contrast are much more mesh-sensitive, with maximum
relative spreads of about `95.5%`, `24.1%`, and `52.9%`, respectively.

## Inferred

The heat-flow side is the most promising diagnostic lane for matching work, but
this package still cannot release Qwall/source-property evidence or admit a
closure. The exchange-cell flow and contrast QOIs are not yet mesh-stable enough
to support coefficient fitting. Formal GCI is blocked independently because no
strict same-label coarse member exists in this medium/fine rerun family.

## Caveats

The previous same-QOI temporal UQ is useful context but is not a mesh substitute.
The medium/fine spread report is diagnostic only. It does not justify absorbing
recirculation residuals into ordinary one-stream internal Nu, and it does not
trigger S11, S13 admission, S15 freeze, or S6 scoring.

## Next Useful Actions

Either produce a strict same-label coarse companion for the four QOIs or
publish an explicit coarse-equivalence contract that can be audited. In
parallel, keep heat-flow matching work focused on source-side equivalence and
same-QOI UQ, since `Q_wall_W` is the only S13 QOI showing low medium/fine spread
in this diagnostic package.
