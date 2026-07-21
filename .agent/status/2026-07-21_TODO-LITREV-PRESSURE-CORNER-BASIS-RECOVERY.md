---
task: TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: status
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/README.md
tags: [pressure-ledger, pressure-corner, two-tap, section-effective, litrev-synthesis]
related:
  - .agent/journal/2026-07-21/litrev-pressure-corner-basis-recovery.md
  - imports/2026-07-21_litrev_pressure_corner_basis_recovery.json
  - operational_notes/maps/pressure-and-momentum-budget.md
---
# TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY Status

## Objective

Audit pressure-increasing corner candidates by decomposing gross static pressure into hydrostatic, kinetic, straight/developing, pressure-recovery, and residual terms without clipping negative diagnostic values or turning them into negative loss.

## Outcome

Complete. Published `pressure_corner_basis_recovery_audit.csv` for the three current `corner_lower_right` Salt2/Salt3/Salt4 endpoint pairs. Each row is labeled `section_effective` with a reason. The audit preserves signed terms:

- gross static rise: about `3035-3069 Pa` downstream-minus-upstream;
- hydrostatic term: about `3037-3070 Pa`, slightly larger than gross static rise;
- kinetic term: about `-0.057` to `-0.098 Pa`;
- straight/developing correction: missing same-basis reference, explicitly blank/blocked;
- available residual: about `-1.25` to `-1.85 Pa`, preserved as unadmitted pressure-recovery/section-effective diagnostic evidence.

No row is labeled `component_K`, `cluster_K`, `pressure_recovery` as an admitted class, or ordinary one-stream K because material recirculation, component isolation, same-QOI UQ, and same-basis straight/developing gates fail.

## Changes Made

- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/build_litrev_pressure_corner_basis_recovery.py`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/test_litrev_pressure_corner_basis_recovery.py`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/summary.json`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/README.md`
- `operational_notes/maps/pressure-and-momentum-budget.md`
- `.agent/BOARD.md`
- `.agent/journal/2026-07-21/litrev-pressure-corner-basis-recovery.md`
- `imports/2026-07-21_litrev_pressure_corner_basis_recovery.json`

## Validation

Passed:

```bash
python3.11 -m unittest work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/test_litrev_pressure_corner_basis_recovery.py
```

Result: `Ran 3 tests ... OK`.

## Guardrails

- Native CFD/OpenFOAM outputs: read-only, not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not touched; no solver or postprocessing launch.
- Fluid/external repo: not touched.
- Generated docs index: not refreshed in this task scope.
- F6 fit: not performed.
- Component-K admission: not performed.
- Clipped K/global multiplier: not introduced.

## Unresolved Blockers

The current rows still need same-basis straight/developing reference, recovery diagnostics, material reverse-flow resolution or a calibrated recirculating model, and same-QOI mesh/time uncertainty before any coefficient admission review.
