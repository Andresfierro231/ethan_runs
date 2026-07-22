---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/surface_input_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seeded_release_decision.csv
tags: [s13, upcomer-exchange, seeded-cv, surface-input-manifest, preflight]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SURFACE-INPUT-MANIFEST-FROM-SEEDED-CV-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/README.md
task: TODO-S13-UPCOMER-EXCHANGE-SURFACE-INPUT-MANIFEST-FROM-SEEDED-CV-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Upcomer Exchange Surface/Input Manifest From Seeded CV

## Attempted

Converted the released S13 seeded source-bounded CV package into a downstream
surface/input manifest package. The builder streams headers and line counts from
the large seeded CSVs and joins those release facts to existing cell VTK,
cell-volume, and static source/sink context.

The builder also regenerates task-owned per-case split inputs under `masks/`,
`faces/`, and `bands/`, plus the downstream manifest, existence-check, and gate
tables that a later surface extraction row can consume.

## Observed

- `seeded_recirc_cv_cells.csv`, `seeded_exchange_interface_faces.csv`, and
  `seeded_trusted_wall_faces.csv` each contain `116640` rows, split as `38880`
  rows for Salt2, Salt3, and Salt4.
- Required seeded columns were present for release decision, recirc cells,
  internal interface faces, trusted wall faces, wall/core band, normal
  convention, source/sink boundary ledger, and surface contract.
- Salt2/Salt3/Salt4 each have zero unclassified escape faces, released seeded
  wall/core band, released seeded normal convention, existing cell VTK, existing
  cell-volume CSV, and static source/sink summary context.
- `Q_wall_W` is not released. Raw sampled interface/wall VTK outputs and
  same-window sampler outputs are not present.

## Inferred

The seeded geometry/input lane is now strong enough to claim a separate
scheduler-authorized surface extraction row. That next row should generate or
fail-close raw sampled interface and wall outputs from the seeded face lists.

This package does not make S13 sampler-ready. It releases only a
surface-extraction input manifest, not a harvest manifest, same-QOI UQ package,
or coefficient/admission decision.

## Caveats

The seeded face lists are geometry/control-volume products. They are not raw
same-window sampled face-field outputs. Treating them as sampled VTK/field
outputs would collapse the scientific distinction between geometry readiness and
production QOI readiness.

## Next Useful Actions

1. Claim a scheduler-authorized seeded surface extraction row that writes only
   task-owned outputs and reads the seeded face lists as input geometry.
2. Produce or fail-close raw interface/wall sampled outputs, including the
   convention needed for `mdot_exchange`.
3. Release or fail-close `Q_wall_W` for the seeded wall/core band.
4. Refresh sampler manifest only after raw sampled interface/wall outputs,
   cell VTK, cell volumes, source/sink context, and sign conventions validate.
5. Run production harvest and same-QOI UQ only after the sampler manifest has
   `3/3` ready rows.

## Guardrails

No native outputs, registry/admission state, scheduler state, Fluid/external
code, blocker register, generated index, OpenFOAM run, surface extraction,
sampler, harvest, UQ execution, fitting, admission, S11/S12/S13/S15/S6 trigger,
or internal-Nu residual absorption changed.
