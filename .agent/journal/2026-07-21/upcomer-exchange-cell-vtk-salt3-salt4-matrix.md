---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/validation_report.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/scheduler_terminal_status.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/logs/stage_field_sanitization.log
tags: [journal, upcomer, exchange-cell, cell-vtk, salt3, salt4, scheduler]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix.json
task: TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Salt3/Salt4 Cell VTK Matrix

## Attempted

Extended the Salt2 whole-mesh cell VTK extraction path to Salt3 and Salt4.
Staged task-local reconstructed cases under `tmp/`, used OF13 reconstruction
and `foamToVTK`, copied only package-owned VTK outputs, and validated cell
count plus `U/T/rho` field presence.

## Observed

Job `3308495` failed after reconstructing Salt3 because `foamToVTK` could not
parse `-nan` tokens in the reconstructed Salt3 `T` boundaryField. The native
processor source was left read-only. The task-local reconstructed field showed
four non-finite boundary tokens and no non-finite internal-cell tokens.

The runner was repaired to verify the internal scalar list first, replace only
task-local boundary non-finite tokens, and exclude patch output during internal
cell export. Job `3308527` completed successfully. Salt3 and Salt4 both
validate with `2166996` cells and fields `T;U;cellID;rho`.

## Inferred

The whole-mesh cell-state input lane is now complete for Salt2/Salt3/Salt4.
The Salt3 boundary-field repair is acceptable only for internal cell VTK export;
it does not provide wall thermal evidence or justify any wall/core heat-flow
claim.

## Contradictions Or Caveats

`foamToVTK -excludePatches` still writes patch VTK files for some patches in
this OpenFOAM path, so downstream scripts must continue selecting the top-level
internal file explicitly. The generated package validator checks the copied
top-level internal files only.

## Next Useful Actions

1. Use the S13 geometry contract to decide whether interface/wall surface VTK
   extraction can proceed.
2. Do not launch exchange-cell harvest from the complete cell VTKs alone.
3. If a future row defines a recirculation volume, reuse these VTKs for
   internal cell state and regenerate separate wall/interface surfaces under a
   new task-owned package.
