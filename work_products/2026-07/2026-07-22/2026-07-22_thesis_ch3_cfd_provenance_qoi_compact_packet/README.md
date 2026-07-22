---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package/salt14_inventory_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix/cfd_legal_use_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix/case_split_legal_use_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_cfd_extraction_methodology_thesis_study/README.md
tags: [thesis, chapter-3, cfd-extraction, qoi-dictionary, provenance, legal-use]
related:
  - .agent/status/2026-07-22_TODO-THESIS-CH3-CFD-PROVENANCE-QOI-COMPACT-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-ch3-cfd-provenance-qoi-compact-packet.md
  - imports/2026-07-22_thesis_ch3_cfd_provenance_qoi_compact_packet.json
task: TODO-THESIS-CH3-CFD-PROVENANCE-QOI-COMPACT-PACKET-2026-07-22
date: 2026-07-22
role: cfd-pp / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Ch3 CFD Provenance and QoI Compact Packet

Decision: `chapter3_cfd_database_packet_ready_diagnostic_only_no_runtime_release`.

This packet condenses the CFD extraction evidence needed for a thesis Chapter 3
methods/database section. It is a writer-facing appendix package: it states
what CFD data are retained, how QoIs are reduced, which cases are fit/support/
holdout/external rows, and which uses are forbidden. It does not copy native
OpenFOAM output trees, run solvers, launch the scheduler, mutate registry or
admission state, release source/property inputs, or admit any predictive
coefficient.

## Chapter 3 Statement

The CFD database is a reference simulation database, not an experimental
validation database. Its native OpenFOAM fields and postprocessed QoI ledgers
are observed CFD results. They can support provenance, method description,
diagnostic model-form reasoning, residual attribution, and uncertainty/run
planning. They cannot be passed into the predictive runtime model as realized
mass flow, realized wall heat flux, realized cooler duty, realized validation
temperature, or realized residual.

The Salt1-4 postprocessing inventory contains 23 registered sources, all parsed,
with 1,405,596 tidy QoI rows and 16,353 retained-window statistic rows. Velocity
profiles were parsed in `latest` mode, with the full available profile
directory/file coverage retained in the source manifest.

## Exact Data Package

- `case_provenance_table.csv`: compact case/family split labels and legal-use
  permissions.
- `retained_window_table.csv`: retained-window and inventory statistics.
- `qoi_dictionary.csv`: extracted CFD QoI lanes, source artifacts, reduction
  definitions, and allowed/forbidden uses.
- `postprocessing_method_table.csv`: reproducible extraction sequence from
  source inventory through split/admission metadata join.
- `claim_boundary_table.csv`: statements that are safe for Chapter 3 and
  statements that must not be made.
- `figure_table_targets.csv`: suggested Chapter 3 tables/figures derived from
  the compact packet.
- `native_source_path_manifest.csv`: source packages used as read-only evidence.
- `no_mutation_guardrails.csv`: native-output, registry, scheduler, and external
  repository mutation status.
- `summary.json`: machine-readable outcome and guardrails.

## Methodology Contract

The extraction method is contract-first. A case/time window and source path are
recorded first. Geometry masks and reduction domains are fixed before field
values are sampled. Pressure, velocity, density, temperature, and wall heat-flow
QoIs are reduced on that fixed basis. Source/property permissions and split
roles are joined after physical reduction, then same-QOI uncertainty gates are
checked before any production/admission use.

The same reduction may therefore have different permitted uses depending on its
split role. For example, a realized CFD `mdot` value can quantify mass-flow
drift or diagnose model-form error, but it remains a forbidden predictive
runtime input. A realized `wallHeatFlux` integral can support heat-path
diagnosis, but it cannot be used as a heat-loss closure or hidden in internal
Nu.

## Heat-Loss Alignment Guardrail

Chapter 3 should preserve the heat-path ownership introduced in the thermal
accounting work: heater/source, internal Nu, wall conduction, insulation/quartz,
external convection, radiation, jacket/cooler, storage, and residual are
separate lanes. Missing heat residual remains a residual or a named candidate
owner until a setup-known source/property and same-QOI uncertainty gate admits a
runtime-legal path. It is not assigned to internal Nu by convenience.

## Current Blockers

This package is complete for Chapter 3 documentation, but it does not unblock
predictive model admission. Current blockers that remain outside this packet:

- row-level `cp_J_kg_K`, viscosity, pressure-basis, and source/sink property
  release remain fail-closed unless a separate source/property packet admits
  them;
- S13 target-window pressure and `Q_wall_W` reductions still need same-QOI
  neighbor-window and mesh/UQ support before production harvest/admission;
- pressure component-K/F6 closure remains blocked until a defensible low-
  recirculation or nonrecirculating anchor basis exists;
- validation, holdout, and external-test temperatures remain score-only after
  an independently frozen candidate.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid/external repository, thesis LaTeX/manuscript body, source/property
release state, blocker register, or generated index was changed by this
package.
