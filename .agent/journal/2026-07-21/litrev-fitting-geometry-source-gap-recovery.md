---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_inventory_source_envelope/fitting_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/cfd_postprocessing_schema_gap_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/model_interface_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
  - reference/geometry_reference.md
tags: [litrev-synthesis, minor-loss, source-envelope, geometry, pressure-ledger]
related:
  - .agent/status/2026-07-21_TODO-LITREV-FITTING-GEOMETRY-SOURCE-GAP-RECOVERY.md
  - imports/2026-07-21_litrev_fitting_geometry_source_gap_recovery.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_fitting_geometry_source_gap_recovery/README.md
task: TODO-LITREV-FITTING-GEOMETRY-SOURCE-GAP-RECOVERY
date: 2026-07-21
role: Implementer/Writer
type: journal
status: complete
---
# LitRev Fitting Geometry Source-Gap Recovery

Task: TODO-LITREV-FITTING-GEOMETRY-SOURCE-GAP-RECOVERY

## Attempted

Implemented the second continuation step after the source-envelope inventory:
convert each fitting and cluster row into a geometry/source-gap recovery table
that names what evidence is still missing before a source-bounded pressure-loss
term could be considered.

The package deliberately stays on the evidence/recovery side. It does not
select, tune, import, or admit any local fitting coefficient.

## Observed

The inventory package already covers the required loop features: four loop
corners, lower and upper quartz transitions, the composite test-section
complex, a facility-reported heat-exchanger reducer, a facility-reported
tee/corner fitting, and the unresolved `junction_other` cluster. The schema-gap
audit requires plane geometry, pressure basis, velocity basis, hydrostatic and
kinetic treatment, source-family validity, same-QOI uncertainty, and
recirculation metrics before any local-loss row can be admitted.

The pressure-corner basis/recovery package resolves the current status of
`corner_lower_right`: Salt2-Salt4 endpoint rows are section-effective evidence
under recirculation, not isolated component-K evidence. The other corner rows
remain ordinary component or cluster prechecks only after bend geometry,
component boundaries, tap sweeps, pressure/velocity basis, and recirculation
classification are recovered.

The quartz transitions have useful diameter evidence from the geometry
reference, but their source-page path still needs transition length, half-angle,
edge radius, pressure bracketing, recovery length where applicable, and a
straight reference. The heat-exchanger reducer and tee/corner fitting remain
facility/source-gap rows because the current geometry reference and pressure
products do not locate pressure-isolated members. `junction_other` is still a
thermal patch group rather than a pressure fitting map.

## Inferred

The next productive work is not to choose K values; it is to recover geometry
and source-page fields. Source families are useful now as audit queues:
NIST/VDI/Idelchik/Crane/Miller style sources can define reducer/bend/area-change
requirements only after TAMU geometry and pressure basis match; Patino-Jaramillo
can only be evaluated after a discrete tee topology, branch numbering, and
reduced-static basis exist; recirculation exchange-cell sources are architectural
guidance for the test-section complex, not scalar fitting terms.

This leaves two usable modeling lanes today: an ordinary component/cluster
precheck lane for rows whose geometry and low-recirculation evidence may later
be recovered, and a recirculating section-effective or exchange-cell lane for
the current lower-right/test-section evidence.

## Caveats

The first builder run failed because the package-local repo-root calculation
walked one directory too high. The builder was corrected to use the actual
`ethan_runs/` root from this work-product depth, then regenerated and passed
the package test. No source evidence or native data were edited while correcting
that path.

No CAD, manufacturer page, native OpenFOAM field, scheduler job, Fluid source,
registry/admission state, or external repository was read-write touched. Current
source-family names are candidate audit labels, not coefficient sources.

## Next Useful Actions

Use `geometry_source_gap_recovery.csv` and
`source_page_audit_queue.csv` as the handoff. Highest leverage next tasks are:
recover facility/CAD dimensions and part mappings for quartz, heat-exchanger
reducer, and tee rows; standardize pressure-plane metadata and pressure basis
for component bracketing; and keep `corner_lower_right` in the recirculating
section-effective lane unless a same-topology, low-reverse-flow anchor with
same-QOI uncertainty lands.
