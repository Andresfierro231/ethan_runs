---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv
  - work_products/2026-07/2026-07-17/2026-07-17_high_heat_harvest_readiness_and_live_monitor/harvest_readiness_queue.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/proposed_cfd_run_matrix.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_admission_contract.md
tags: [f6, cfd-study-design, recirculation, uncertainty]
related:
  - .agent/status/2026-07-17_AGENT-501.md
task: AGENT-501
date: 2026-07-17
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# Recommended Further Studies

Generated: `2026-07-17T20:04:44+00:00`

## Special Section: Studies That Add Clarity

1. Immediate terminal harvest: wait for PM10 and high-heat jobs to become
terminal, then run PM5-style scratch-copy postprocessing. Required outputs are
`U`, `T`, `wallHeatFlux`, Re/Pr/Ri/Gr/Ra/Gz, wall-core Delta T, reverse
area/mass fraction, secondary velocity, steady-window status, and mesh/time
uncertainty.

2. Non-recirculating F6 anchor: use a high-Re/high-insulation or high-Q case
to deliberately seek `RAF < 0.01` and `RMF < 0.01`. This is the cleanest route
to an ordinary F6 friction row.

3. Onset-bracketing Q x insulation matrix: if terminal high-heat evidence does
not provide a clean non-recirculating anchor, run the small Q x insulation
matrix to bracket transition between low-reverse and material-recirculation
regimes.

4. Low-Q/low-insulation cell-max sentinel: keep this case because it stresses
the opposite regime, where buoyancy and loss sensitivity should be strongest.
It is useful for a recirculation-modeled lane, not ordinary F6, unless the
reverse-flow gate unexpectedly passes.

5. Hybrid closure residual test: after features and uncertainty exist, score a
named section-effective/onset/mixing penalty against `F3_shah_apparent` on
validation/holdout. Do not use realized CFD mass flow, validation temperatures,
or a hidden global multiplier.

6. Uncertainty sequence: start with time-window uncertainty for RAF/RMF/SVF,
pressure residuals, and wall-core Delta T. Add mesh/GCI only after a candidate
lane shows meaningful residual movement.

## Next Steps For Today

- Keep F6 blocked for production and cite the gate matrix instead of trying to
fit ordinary friction from PM5.
- Monitor PM10 and high-heat terminal status in their owning packages; do not
harvest from this package.
- When a run becomes terminal, claim a separate extraction task and rerun the
PM5-style scratch-copy workflow with the full output contract above.
- If no terminal case reaches the low-reverse gate, prioritize the Q x
insulation onset-bracketing matrix before adding more nominal perturbations.
