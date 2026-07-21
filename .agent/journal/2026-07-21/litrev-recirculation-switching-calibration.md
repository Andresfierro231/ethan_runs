---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration/switching_calibration_template.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration/unresolved_threshold_fields.csv
tags: [recirculation, switching-calibration, thermal-closure]
related:
  - .agent/status/2026-07-21_TODO-LITREV-RECIRCULATION-SWITCHING-CALIBRATION.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration/README.md
task: TODO-LITREV-RECIRCULATION-SWITCHING-CALIBRATION
date: 2026-07-21
role: Hydraulics / Thermal-modeling / Writer
type: journal
status: complete
---

# LitRev Recirculation Switching Calibration

## Attempted

I converted the LitRev recirculation and recovery requirements into a TAMU
calibration template. The row explicitly prohibited code, so the result is a
static package of evidence tables and a README rather than a generated builder.

## Observed

The LitRev extraction defines reverse area fraction, reverse mass fraction,
secondary-flow intensity, and recovery diagnostics as required CFD fields.
Current lower-right corner evidence has material reverse flow and is already
blocked from ordinary coefficient use. Upcomer evidence remains proxy,
parse-incomplete, or missing key mass/thermal/coherent-cell fields. Same-QOI
uncertainty remains missing for threshold families.

## Inferred

The current evidence is enough to define the switch variables and conservative
blocking posture, but not enough to select numeric `epsilon_*` thresholds. Any
future threshold must be learned from TAMU training/support rows with the exact
same definitions, then frozen before held-out/external use.

## Contradictions Or Caveats

Operational notes mention earlier heuristic thresholds such as ordinary
reverse-flow limits, but the LitRev row explicitly prohibits importing universal
thresholds. This package therefore records those as evidence of current blocking
logic, not as admitted final TAMU switching thresholds.

## Next Useful Actions

Harvest same-window `F_A`, `F_m`, transverse velocity components, wall/core
thermal stratification, and recovery-plane sweeps with same-QOI uncertainty.
Then run a separate calibration row that predeclares train/support, development,
holdout, and external-test rows before selecting any epsilon values.
