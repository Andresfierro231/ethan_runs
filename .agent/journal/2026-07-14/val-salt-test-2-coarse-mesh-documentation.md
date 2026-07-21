---
provenance:
  - imports/2026-05-29_val_salt_test_2_coarse_mesh_laminar_import.json
  - jadyn_runs/salt2/2026-06-01_continuation_candidate/README.md
  - jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/0/T
  - jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/summary.json
tags: [cfd-pp, salt2, val-lineage, boundary-conditions, documentation]
related:
  - .agent/status/2026-07-14_AGENT-354.md
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
task: AGENT-354
date: 2026-07-14
role: cfd-pp / Writer / Implementer
type: journal
status: complete
---
# val_salt_test_2_coarse_mesh Documentation

## Question

Produce a durable, reproducible documentation package for
`val_salt_test_2_coarse_mesh`, the user-requested canonical display label for
the existing `2026-06-01_continuation_candidate` /
`val_salt_test_2_coarse_mesh_laminar` lineage. Include source/path lineage,
BCs, material/property evidence, comparison against Salt2 Jin, manifest files,
and a focused test.

## Files Inspected

- Root coordination: `AGENTS.md`, `.agent/BOARD.md`,
  `.agent/FILE_OWNERSHIP.md`, `.agent/ROLES.md`,
  `.agent/DOC_FRONTMATTER_SCHEMA.md`.
- Local instructions: `tools/AGENTS.override.md`,
  `staging/AGENTS.override.md`, `jadyn_runs/AGENTS.override.md`,
  `.agent/status/README.md`, `.agent/journal/README.md`.
- Val lineage: `imports/2026-05-29_val_salt_test_2_coarse_mesh_laminar_import.json`,
  `registry/case_registry.csv`,
  `jadyn_runs/salt2/2026-06-01_continuation_candidate/README.md`,
  `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml`,
  `0/T`, `0/U`, `0/p_rgh`, and `constant/physicalProperties`.
- Salt2 Jin comparator:
  `imports/2026-06-02_viscosity_screening_salt_test_2_jin_coarse_mesh_import.json`,
  `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/README.md`,
  and comparator case dictionaries.
- Prior packages:
  `work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/`,
  `work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/`,
  `work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/`,
  `reports/2026-06/2026-06-04/2026-06-04_ethan_direct_validation/`,
  and `reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/`.

## Files Changed

- Added `tools/analyze/build_val_salt_test_2_coarse_mesh_documentation.py`
- Added `tools/analyze/test_val_salt_test_2_coarse_mesh_documentation.py`
- Added `imports/2026-07-14_val_salt_test_2_coarse_mesh_documentation.json`
- Added package files under
  `work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/`
- Added `.agent/status/2026-07-14_AGENT-354.md`
- Added this journal entry
- Updated only the AGENT-354 row in `.agent/BOARD.md` during closeout

## Observed

The val intake manifest records `source_id=val_salt_test_2_coarse_mesh_laminar`,
`source_owner=native_2d_cfd_external`, and source root
`/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar`.
The continuation README says the source stopped around `1724.714285714 s`, had
`endTime=10000`, and was staged under
`jadyn_runs/salt2/2026-06-01_continuation_candidate/`.

The display-label migration should therefore be additive: use
`val_salt_test_2_coarse_mesh` in new reports, but preserve all historical
source IDs and file paths. The source spelling is `coarse`, not `course`.

The val and Salt2 Jin cases share `mesh_group_id=7ab7fb2650596980`, `nprocs=64`,
`heater_power_W=265.7`, `cooling_power_W=56.34`, and the same fluid-property
coefficient forms. They differ in source family, fluid label, initial
temperature, and wall insulation thicknesses: val commonly uses `0.04191 m`,
while Salt2 Jin uses `0.03556 m` in comparable ambient-wall layer positions.

The thermal boundary dictionaries show:

- three lower heater patches with `Q=88.56666666666666 W` each;
- one test-section patch with `Q=37.0 W`;
- upper reducer/cooler/reducer fixed negative-Q patches totaling
  `-136.350740 W`;
- passive/junction/stub wall exchange using `rcExternalTemperature` and
  `externalTemperature`;
- `rcExternalTemperature` patches with `Ta=299.19 K`, `Tsur=299.19 K`, and
  `emissivity=0.95` where present.

The velocity and pressure dictionaries show a closed-loop setup: no named inlet
or outlet patch was found. `0/U` uses a no-slip wildcard plus 10 NCC slip
connector patches; `0/p_rgh` uses `fixedFluxPressure` on all patches.

Current comparison status: Salt2 Jin is current mainline nominal evidence and
paper inventory class `paper-grade`, but the July 14 steady table carries a
hydraulic-stationary/thermal-drift caveat. The val row is `blocked` in the June
29 paper inventory and diagnostic/historical in July 14 comparison context.

## Interpretation

The val case is useful for provenance, BC/property comparison, historical
validation context, and display-label cleanup. It should not be silently used as
current training or validation evidence without a future explicit admission row.

The radiation semantics follow the current thermal boundary map: emissivity and
Tsur are active in `rcExternalTemperature`; radiation is folded into total
OpenFOAM `wallHeatFlux`; no separate exported `qr` term is available.

## Commands Run

- `python3.11 tools/analyze/build_val_salt_test_2_coarse_mesh_documentation.py`
- `python3.11 -m unittest tools.analyze.test_val_salt_test_2_coarse_mesh_documentation`

Both passed.

## Incomplete Lines

No native case, registry, scheduler, generated index, or external Fluid edit was
attempted. A future admission task would need to decide whether the val row can
be re-admitted and under which split/use policy.

## Next Step

Use the generated package as the canonical source for prose or table text about
`val_salt_test_2_coarse_mesh`. If the row is needed for fitting or validation,
open a new admission task rather than changing this documentation package.
