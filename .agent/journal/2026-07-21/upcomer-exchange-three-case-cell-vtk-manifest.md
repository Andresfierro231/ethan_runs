---
provenance:
  - tools/extract/build_upcomer_exchange_three_case_cell_vtk_manifest.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest/three_case_cell_vtk_validation_join.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest/remaining_sampler_blockers.csv
tags: [upcomer, exchange-cell, cell-vtk, sampler-blocked]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest.json
task: TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Three-Case Cell VTK Manifest

## Attempted

Built a task-owned manifest package that consumes the completed Salt2 smoke
and Salt3/Salt4 matrix validation reports, joins their whole-mesh `cell_vtk`
paths to the sampler template, and records the remaining non-cell blockers.

## Observed

All three cases have existing validated cell VTKs with `2166996` observed
cells and required fields `U`, `T`, and `rho`. The prior writers also emitted
`cellID`, which is useful for same-order checks. The generated sampler manifest
copy now points at those three VTK files but leaves the exchange-interface,
wall, and normal-vector columns blocked.

The source/sink package has static `0/T` source and sink terms for all three
cases, but each row explicitly says wall loss is still blocked. The manifest
therefore treats those rows as context rather than as a sampler-release ledger.

## Inferred

The exchange-cell sequence has advanced from missing whole-mesh cell VTKs to a
geometry/source blocker. The next progress should not rerun cell extraction
unless provenance is lost; it should define an exchange interface, define a
wall/core band, and release a heat-flow sign convention.

## Contradictions Or Caveats

The existing reusable scaffold contract still labels `cell_vtk` as blocked
because it was written before the Salt2/Salt3/Salt4 VTK extraction rows
completed. This package does not edit that scaffold in place; it publishes a
task-owned manifest copy that supersedes only the cell-lane placeholders.

This package does not make S13 production-ready and does not run the sampler.
It also does not move source/sink rows into a released runtime heat ledger,
because `Q_wall_W` and the sign convention remain absent.

## Next Useful Actions

1. Claim an exchange-interface source-definition package and either publish a
   conservative interface geometry or fail-closed with a narrow candidate list.
2. Claim a wall/core band package for wall VTK and `Q_wall_W` integration.
3. Publish a source/sink/sign-convention release only after wall loss is
   included.
4. Run the sampler preflight against the cell-populated manifest only after
   the interface, wall, normal, and source lanes are populated.
