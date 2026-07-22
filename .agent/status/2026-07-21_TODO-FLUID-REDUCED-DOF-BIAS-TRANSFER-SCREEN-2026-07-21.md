---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md
  - tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py
  - tools/analyze/test_fluid_reduced_dof_bias_transfer_screen.py
tags: [forward-model, empirical-bias, reduced-dof, frozen-transfer]
related:
  - .agent/journal/2026-07-21/fluid-reduced-dof-bias-transfer-screen.md
  - imports/2026-07-21_fluid_reduced_dof_bias_transfer_screen.json
  - operational_notes/maps/forward-predictive-model.md
task: TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21

## Objective

Reduce the empirical temperature correction degrees of freedom, predeclare
admissible diagnostic correction families, fit only train/support coefficients,
and test whether the same frozen correction structure transfers beyond the
fit partition without changing coefficients.

## Outcome

Published
`work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/`.

The package fits six predeclared reduced-DOF families on existing TSWFC2
Salt1/Salt2 train/support sensor rows (`32` usable rows) and applies frozen
coefficients to Salt3/Salt4 legacy validation/holdout-style stress rows (`32`
usable rows).

Headline metrics:

- Best train/support family: `F2_global_affine`, corrected MAE `8.501470 K`.
- Best frozen-transfer family: `F5_thermal_family_offset_shared_multiplier`,
  transfer MAE `106.121666 K -> 13.324483 K`.
- External-test rows scored: `0`.
- Coefficient refit after transfer scoring: `false`.
- Model selection from transfer rows: `false`.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21.md`
- `.agent/journal/2026-07-21/fluid-reduced-dof-bias-transfer-screen.md`
- `imports/2026-07-21_fluid_reduced_dof_bias_transfer_screen.json`
- `tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py`
- `tools/analyze/test_fluid_reduced_dof_bias_transfer_screen.py`
- `operational_notes/maps/forward-predictive-model.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/**`

## Validation

- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m py_compile tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py tools/analyze/test_fluid_reduced_dof_bias_transfer_screen.py` passed.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py` passed.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 tools/analyze/test_fluid_reduced_dof_bias_transfer_screen.py` passed with `Reduced-DOF bias transfer screen checks passed.`
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/fit_and_transfer_sensor_rows.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/model_family_dof_ledger.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/split_metric_scorecard.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/transfer_summary.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/split_runtime_leakage_audit.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/explanation_hypothesis_ledger.csv work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/source_manifest.csv --warn --todo-out work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/source_property_gate_todo.csv` completed with expected warning and wrote the blocker TODO CSV.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Fluid solve or postprocessing launch: no.
- External Fluid repository edit: no.
- External-test score claim: no.
- Final predictive admission: no.
- Source/property release: no.
- Blocker register changed: no.
- Generated docs index changed: no.
- Thesis files changed: no.
- Residual absorbed into internal Nu: no.

## Blockers

The screen uses existing TSWFC2 sensor rows, not a new Phase E/Fluid external-BC
multi-split solve. It therefore supports a frozen diagnostic transfer claim,
not a final corrected-split validation/holdout/external-test claim. A compatible
runtime-legal Fluid score artifact with train, validation/support, holdout, and
external-test rows is still required before admission language.

The source/property gate remains blocked from the TSWFC2 source package. These
rows are empirical diagnostic score rows only; they do not release a material
source/property model, fit-admitted closure, or final predictive candidate.
