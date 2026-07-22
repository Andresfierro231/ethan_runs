---
task: TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed_alt_cv
tags: [s13, upcomer, exchange-cell, topology, forensics, alternate-cv, fail-closed]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release
---
# S13 Upcomer Exchange Topology Forensics and Alternate CV

This package diagnoses why the prior S13 topology CV release failed and tests
one conservative alternate selection from the same reverse-flow evidence. The
alternate selector prefers a reverse-flow face component with right-leg wall
contact if one exists, but it keeps the existing release gates: dominant
component fraction, positive interface area, positive right-leg wall area, and
zero unclassified boundary escapes.

## Decision

- cases processed: `3`
- component forensic rows: `56`
- selected alternate CV rows released: `0`
- surface extraction allowed: `false`
- scheduler action: `false`
- sampler/harvest launched: `false`

Result: `complete_fail_closed_alt_cv`. Reverse-flow evidence remains diagnostic unless
all three cases release together under the unchanged topology gates.

## Outputs

- `component_topology_forensics.csv`
- `alternate_cv_case_summary.csv`
- `alternate_cv_surface_contract.csv`
- `alternate_cv_boundary_escape_by_patch.csv`
- `reverse_occupancy_diagnostics.csv`
- `downstream_release_gate.csv`
- `masks/*_selected_alternate_cv_mask.csv`
- `no_mutation_guardrails.csv`, `source_manifest.csv`, and `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated documentation index,
surface VTK extraction, sampler/harvest, fit, score, model selection,
S11/S15/S6 trigger, threshold relaxation, proxy-interface admission, or
internal-Nu residual absorption is changed by this package.
